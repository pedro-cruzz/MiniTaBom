"""Testes t: métodos documentados, distribuição t calculada pelo SciPy."""
from functools import lru_cache
import math
from pathlib import Path
import statistics
import sys
from core import numeric_column
from app_resources import resource_path


def p_statement(value, label='Valor-p', unavailable='indisponível'):
    if value is None:
        return f'{label} = {unavailable}'
    return f'{label} < 0,000001' if value < 1e-6 else f'{label} = {value:.9g}'


@lru_cache(maxsize=1)
def scientific_stats():
    local = resource_path('.deps')
    if local.is_dir() and str(local) not in sys.path:
        sys.path.insert(0, str(local))
    try:
        from scipy import stats
    except ImportError as error:
        raise ValueError('Instale as dependências com desenvolvimento/instalar_dependencias.bat para usar estas análises.') from error
    return stats


def summarize(values):
    if len(values) < 2 or not all(math.isfinite(v) for v in values):
        raise ValueError('Cada amostra analisada precisa de pelo menos dois números finitos.')
    sd = statistics.stdev(values)
    return dict(n=len(values), mean=statistics.mean(values), sd=sd, se=sd / math.sqrt(len(values)))


def t_result(estimate, se, df, null=0, confidence=95, alternative='two-sided'):
    if not math.isfinite(null) or not math.isfinite(confidence) or not 0 < confidence < 100:
        raise ValueError('Use hipótese finita e nível de confiança entre 0 e 100, sem os extremos.')
    if alternative not in ('two-sided', 'less', 'greater'):
        raise ValueError('Hipótese alternativa inválida.')
    if not all(math.isfinite(v) for v in (estimate, se, df)) or df <= 0:
        raise ValueError('Magnitude dos dados excede a precisão numérica suportada.')
    if se <= 0:
        raise ValueError('Erro padrão zero: não é possível calcular este teste t com dados constantes.')
    statistic = (estimate - null) / se
    if not math.isfinite(statistic):
        raise ValueError('Magnitude dos dados excede a precisão numérica suportada.')
    stats = scientific_stats()
    alpha = 1 - confidence / 100
    p = float(2 * stats.t.sf(abs(statistic), df) if alternative == 'two-sided'
              else stats.t.cdf(statistic, df) if alternative == 'less'
              else stats.t.sf(statistic, df))
    critical = float(stats.t.isf(alpha / 2 if alternative == 'two-sided' else alpha, df))
    margin = critical * se
    if not math.isfinite(margin) or not all(math.isfinite(v) for v in (estimate - margin, estimate + margin)):
        raise ValueError('Não foi possível calcular o intervalo com esta precisão ou nível de confiança.')
    low = -math.inf if alternative == 'less' else estimate - margin
    high = math.inf if alternative == 'greater' else estimate + margin
    return dict(estimate=estimate, se=se, df=df, t=statistic, p=p, low=low, high=high,
                null=null, confidence=confidence, alternative=alternative)


def one_sample(values, **options):
    sample = summarize(values)
    result = t_result(sample['mean'], sample['se'], sample['n'] - 1, **options)
    result.update(samples=[sample], mode='one', method='t de uma amostra')
    return result


def summary_sample(n, mean, sd):
    """Valida estatísticas suficientes sem construir observações fictícias."""
    if type(n) is not int or not 2 <= n <= 2_147_483_647:
        raise ValueError('Tamanho amostral: use inteiro entre 2 e 2147483647.')
    if (isinstance(mean, bool) or isinstance(sd, bool)
            or not isinstance(mean, (int, float)) or not isinstance(sd, (int, float))
            or not math.isfinite(mean) or not math.isfinite(sd) or sd < 0):
        raise ValueError('Use média finita e desvio padrão amostral finito não negativo.')
    return dict(n=n, mean=mean, sd=sd, se=sd / math.sqrt(n))


def one_sample_summary(n, mean, sd, **options):
    sample = summary_sample(n, mean, sd)
    result = t_result(sample['mean'], sample['se'], n - 1, **options)
    result.update(samples=[sample], mode='one', method='t de uma amostra')
    return result


def two_sample(first, second, equal_var=False, legacy_df=True, **options):
    a, b = summarize(first), summarize(second)
    return _two_summaries(a, b, equal_var=equal_var, legacy_df=legacy_df, **options)


def two_sample_summary(first, second, equal_var=False, legacy_df=True, **options):
    a, b = (summary_sample(**sample) for sample in (first, second))
    return _two_summaries(a, b, equal_var=equal_var, legacy_df=legacy_df, **options)


def _two_summaries(a, b, equal_var=False, legacy_df=True, **options):
    if equal_var:
        df_raw = df = a['n'] + b['n'] - 2
        pooled = math.hypot(a['sd'] * math.sqrt((a['n'] - 1) / df),
                            b['sd'] * math.sqrt((b['n'] - 1) / df))
        se = pooled * math.sqrt(1 / a['n'] + 1 / b['n'])
        method = 't de duas amostras · variâncias iguais (combinadas)'
    else:
        se = math.hypot(a['se'], b['se'])
        if not math.isfinite(se) or se == 0:
            raise ValueError('Erro padrão nulo ou fora da precisão numérica suportada.')
        wa, wb = (a['se'] / se) ** 2, (b['se'] / se) ** 2
        df_raw = 1 / (wa ** 2 / (a['n'] - 1) + wb ** 2 / (b['n'] - 1))
        # Corrige só resíduos de arredondamento em torno de GL inteiros:
        # 3,999999999999998 não deve perder um grau de liberdade.
        nearest = round(df_raw)
        stable_df = nearest if abs(df_raw - nearest) <= 64 * math.ulp(df_raw) else df_raw
        df = math.floor(stable_df) if legacy_df else df_raw
        method = 't de Welch · GL inteiro (referência 16)' if legacy_df else 't de Welch · GL fracionário'
    result = t_result(a['mean'] - b['mean'], se, df, **options)
    result.update(samples=[a, b], mode='two', method=method, df_raw=df_raw)
    return result


def analyze_t_inputs(headers, rows, mode, first=None, second=None,
                     source='columns', summaries=None, equal_var=False, legacy_df=True, group_order=None, **options):
    if mode not in ('one', 'paired', 'two'):
        raise ValueError('Tipo de teste inválido.')
    if source == 'columns':
        return analyze_columns(headers, rows, mode, first, second,
                               equal_var=equal_var, legacy_df=legacy_df, **options)
    try:
        if source == 'summary':
            count = 2 if mode == 'two' else 1
            if not isinstance(summaries, (list, tuple)) or len(summaries) != count:
                raise ValueError(f'Informe {count} resumo(s) com N, média e desvio padrão amostral.')
            if any(not isinstance(s, dict) or set(s) != {'n', 'mean', 'sd'} for s in summaries):
                raise ValueError('Cada resumo deve conter somente n, mean e sd.')
            result = (two_sample_summary(*summaries, equal_var=equal_var, legacy_df=legacy_df, **options)
                      if mode == 'two' else one_sample_summary(**summaries[0], **options))
            labels = ['Amostra 1', 'Amostra 2'] if mode == 'two' else ['Amostra']
            if mode == 'paired':
                result.update(mode='paired', method='t pareado · resumo das diferenças (primeira − segunda)')
                labels = ['Diferença']
            result.update(labels=labels, missing=[None] * count, source='summary')
            return result
        if source == 'stacked' and mode == 'two':
            from sample_inputs import independent_samples
            samples, excluded = independent_samples(headers, rows, [first], source='stacked',
                                                     group=second, numeric=True, levels=group_order)
            result = two_sample(*(s['values'] for s in samples), equal_var=equal_var,
                                legacy_df=legacy_df, **options)
            result.update(labels=[s['name'] for s in samples], missing=[s['missing'] for s in samples],
                          excluded_groups=excluded, source='stacked', group_order=[s['level'] for s in samples],
                          group_order_policy='fixed' if group_order is not None else 'first_appearance')
            return result
    except (OverflowError, ArithmeticError) as error:
        raise ValueError('Magnitude dos dados excede a precisão numérica suportada.') from error
    raise ValueError('Formato de entrada inválido para este teste t.')


def analyze_columns(headers, rows, mode, first, second=None, equal_var=False, legacy_df=True, **options):
    if mode not in ('one', 'paired', 'two'):
        raise ValueError('Tipo de teste inválido.')
    indices = [first] if mode == 'one' else [first, second]
    if any(type(index) is not int or not 0 <= index < len(headers) for index in indices):
        raise ValueError('Selecione as colunas das amostras.')
    if mode != 'one' and first == second:
        raise ValueError('Selecione duas colunas diferentes.')
    try:
        if mode == 'paired':
            valid = [[], []]
            missing = 0
            for line, row in enumerate(rows, 2):
                pair = []
                for index in indices:
                    raw = str(row[index]).strip()
                    if raw in ('', '*'):
                        pair.append(None)
                    else:
                        try:
                            value = float(raw.replace(',', '.'))
                        except ValueError:
                            raise ValueError(f'Linha {line}, {headers[index]}: número inválido {raw!r}.') from None
                        if not math.isfinite(value):
                            raise ValueError(f'Linha {line}, {headers[index]}: número não finito.')
                        pair.append(value)
                if any(value is None for value in pair):
                    missing += 1
                else:
                    for target, value in zip(valid, pair):
                        target.append(value)
            differences = [a - b for a, b in zip(*valid)]
            result = one_sample(differences, **options)
            result.update(mode='paired', method='t pareado · diferença = primeira − segunda',
                          samples=[summarize(valid[0]), summarize(valid[1]), summarize(differences)],
                          missing=[missing], labels=[headers[first], headers[second], 'Diferença'])
        else:
            data, missing = [], []
            for index in indices:
                try:
                    values, absent = numeric_column(rows, index)
                except ValueError as error:
                    raise ValueError(f'{headers[index]}: {error}') from error
                data.append(values)
                missing.append(absent)
            result = (one_sample(data[0], **options) if mode == 'one'
                      else two_sample(*data, equal_var=equal_var, legacy_df=legacy_df, **options))
            result.update(missing=missing, labels=[headers[index] for index in indices])
    except (OverflowError, ArithmeticError) as error:
        raise ValueError('Magnitude dos dados excede a precisão numérica suportada.') from error
    return result


def format_t_report(result, perform_test=True):
    def number(value):
        if value == math.inf:
            return '+∞'
        if value == -math.inf:
            return '−∞'
        return f'{value:.9g}'
    lines = [result['method'].upper(), '', f"{'Amostra':<26} {'N':>6} {'Média':>14} {'DesvPad':>14} {'EP Média':>14}"]
    for label, sample in zip(result['labels'], result['samples']):
        # Nomes longos têm sua versão integral registrada abaixo da tabela.
        short = label if len(label) <= 25 else label[:22] + '…'
        lines.append(f"{short:<26} {sample['n']:>6} {number(sample['mean']):>14} {number(sample['sd']):>14} {number(sample['se']):>14}")
    if any(len(label) > 25 for label in result['labels']):
        lines += ['', 'Variáveis: ' + ' | '.join(result['labels'])]
    missing_note = ('Entrada: dados resumidos; ausentes não informados.' if result.get('source') == 'summary'
                    else 'Pares excluídos: ' + str(result['missing'][0]) if result['mode'] == 'paired'
                    else 'Ausentes por amostra: ' + ', '.join(map(str, result['missing'])))
    if result.get('source') == 'stacked':
        missing_note += '\nLinhas excluídas por grupo ausente: ' + str(result['excluded_groups'])
        missing_note += ('\nOrdem das amostras: ordem dos grupos preservada nos parâmetros.'
                         if result.get('group_order_policy') == 'fixed' else
                         '\nOrdem das amostras: primeira aparição dos grupos na planilha.')
    lines += ['', missing_note,
              'Estimativa: ' + number(result['estimate']),
              f"IC de {result['confidence']:g}%: ({number(result['low'])}; {number(result['high'])})"]
    if result['mode'] != 'one':
        lines.append('Diferença definida como: primeira amostra − segunda amostra.')
    if perform_test:
        symbol = {'two-sided': '≠', 'less': '<', 'greater': '>'}[result['alternative']]
        p = 'Valor-p < 0,000001' if result['p'] < 1e-6 else 'Valor-p = ' + number(result['p'])
        lines += ['', f"H0: parâmetro = {number(result['null'])}",
                  f"H1: parâmetro {symbol} {number(result['null'])}",
                  f"T = {number(result['t'])}    GL = {number(result['df'])}    {p}"]
    return '\n'.join(lines) + '\n'
