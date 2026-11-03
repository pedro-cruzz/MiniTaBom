"""Z com sigma conhecido e inferência de uma proporção binomial.

Métodos explícitos; não pressupõe os padrões de uma versão do Minitab.
"""
from decimal import Decimal, InvalidOperation
import math
import statistics

from core import numeric_column
from inference import scientific_stats


MAX_N = 2_147_483_647
PROPORTION_METHODS = {
    'exact': 'Exato por caudas / IC Clopper–Pearson',
    'score': 'Aproximação normal / IC Wilson',
    'wald': 'Aproximação normal / IC Wald',
}


def parse_count(text, label='Contagem', minimum=0):
    try:
        value = Decimal(str(text).strip().replace(',', '.'))
        if not value.is_finite() or value != value.to_integral_value() or not minimum <= value <= MAX_N:
            raise ValueError
    except (ValueError, InvalidOperation):
        raise ValueError(f'{label}: use um inteiro entre {minimum} e {MAX_N}.') from None
    return int(value)


def _count(value, minimum, label):
    if type(value) is not int or not minimum <= value <= MAX_N:
        raise ValueError(f'{label}: use um inteiro entre {minimum} e {MAX_N}.')


def _options(null, confidence, alternative):
    if not all(math.isfinite(v) for v in (null, confidence)) or not 0 < confidence < 100:
        raise ValueError('Use hipótese finita e confiança entre 0 e 100, sem os extremos.')
    if alternative not in ('two-sided', 'less', 'greater'):
        raise ValueError('Hipótese alternativa inválida.')
    alpha = 1 - confidence / 100
    if not 0 < alpha < 1:
        raise ValueError('Nível de confiança fora da precisão numérica suportada.')
    return alpha, alpha / 2 if alternative == 'two-sided' else alpha


def _normal_p(z, alternative):
    normal = scientific_stats().norm
    return float(2 * normal.sf(abs(z)) if alternative == 'two-sided'
                 else normal.cdf(z) if alternative == 'less' else normal.sf(z))


def z_mean(n, mean, sigma, null=0, confidence=95, alternative='two-sided'):
    _count(n, 2, 'Tamanho amostral')
    _, tail = _options(null, confidence, alternative)
    if not all(math.isfinite(v) for v in (mean, sigma)) or sigma <= 0:
        raise ValueError('Informe média finita e desvio padrão populacional conhecido maior que zero.')
    se = sigma / math.sqrt(n)
    if se <= 0 or not math.isfinite(se):
        raise ValueError('Erro padrão fora da precisão numérica suportada.')
    z = (mean - null) / se
    margin = float(scientific_stats().norm.isf(tail)) * se
    if not all(math.isfinite(v) for v in (z, margin, mean - margin, mean + margin)):
        raise ValueError('Magnitude dos dados ou confiança excede a precisão numérica suportada.')
    return dict(mode='z', n=n, estimate=mean, sigma=sigma, se=se, statistic=z,
                p=_normal_p(z, alternative), null=null, confidence=confidence, alternative=alternative,
                low=-math.inf if alternative == 'less' else mean - margin,
                high=math.inf if alternative == 'greater' else mean + margin,
                source='Dados resumidos', missing=0)


def one_proportion(events, n, null=.5, confidence=95, alternative='two-sided', method='exact'):
    _count(n, 1, 'Número de ensaios')
    _count(events, 0, 'Número de eventos')
    if events > n:
        raise ValueError('O número de eventos deve ser menor ou igual ao número de ensaios.')
    _, tail = _options(null, confidence, alternative)
    if not 0 <= null <= 1:
        raise ValueError('A proporção hipotética deve estar entre 0 e 1.')
    if method not in PROPORTION_METHODS:
        raise ValueError('Método de proporção inválido.')
    stats = scientific_stats()
    estimate = events / n
    z = None
    if method == 'exact':
        lower_p = float(stats.binom.cdf(events, n, null))
        upper_p = float(stats.binom.sf(events - 1, n, null))
        p = min(1., 2 * min(lower_p, upper_p)) if alternative == 'two-sided' else (
            lower_p if alternative == 'less' else upper_p)
        low = 0. if events == 0 or alternative == 'less' else float(stats.beta.ppf(tail, events, n - events + 1))
        high = 1. if events == n or alternative == 'greater' else float(stats.beta.isf(tail, events + 1, n - events))
    else:
        if not 0 < null < 1:
            raise ValueError('A aproximação normal requer proporção hipotética estritamente entre 0 e 1.')
        se_null = math.sqrt(null * (1 - null) / n)
        if se_null <= 0:
            raise ValueError('A variância sob H0 está fora da precisão numérica suportada; use o método exato.')
        z = (estimate - null) / se_null
        p = _normal_p(z, alternative)
        critical = float(stats.norm.isf(tail))
        if method == 'score':
            q = critical * critical / n
            center = (estimate + q / 2) / (1 + q)
            margin = critical * math.sqrt(estimate * (1 - estimate) / n + q / (4 * n)) / (1 + q)
            low = max(0., center - margin) if events else 0.
            high = min(1., center + margin) if events < n else 1.
        else:
            margin = critical * math.sqrt(estimate * (1 - estimate) / n)
            low, high = estimate - margin, estimate + margin
        if alternative == 'less':
            low = 0.
        elif alternative == 'greater':
            high = 1.
    if not all(math.isfinite(v) for v in (p, low, high)) or low > high:
        raise ValueError('Não foi possível calcular o intervalo com esta precisão.')
    return dict(mode='proportion', n=n, events=events, estimate=estimate, statistic=z, p=p,
                low=low, high=high, null=null, confidence=confidence, alternative=alternative,
                method=method, source='Dados resumidos', missing=0)


def analyze_basic(headers, rows, mode, column, event=None, **options):
    if type(column) is not int or not 0 <= column < len(headers):
        raise ValueError('Selecione uma coluna da amostra.')
    if mode == 'z':
        try:
            values, missing = numeric_column(rows, column)
            mean = statistics.mean(values) if values else 0.
            result = z_mean(len(values), mean, **options)
        except (ArithmeticError, ValueError) as error:
            raise ValueError(f'{headers[column]}: {error}') from error
    elif mode == 'proportion':
        event = str(event).strip() if event is not None else ''
        if event in ('', '*'):
            raise ValueError('Defina o evento; vazio e * representam ausentes.')
        values = [str(row[column]).strip() for row in rows]
        missing = sum(v in ('', '*') for v in values)
        values = [v for v in values if v not in ('', '*')]
        levels = list(dict.fromkeys(values))
        if len(levels) > 2:
            raise ValueError('A coluna de proporção deve ter no máximo duas categorias não ausentes.')
        if len(levels) == 2 and event not in levels:
            raise ValueError('O evento deve corresponder a uma das duas categorias da coluna.')
        result = one_proportion(values.count(event), len(values), **options)
        result.update(event=event, levels=levels)
    else:
        raise ValueError('Tipo de análise inválido.')
    result.update(source=headers[column], missing=missing)
    return result


def format_basic(result, perform_test=True):
    def number(value):
        return '+∞' if value == math.inf else '−∞' if value == -math.inf else f'{value:.9g}'
    is_z = result['mode'] == 'z'
    lines = [('Z DE UMA AMOSTRA' if is_z else 'TESTE DE UMA PROPORÇÃO') + ' — ' + result['source'], '']
    if is_z:
        lines += ['Método: Z com desvio padrão populacional conhecido.',
                  f"N = {result['n']}    Média = {number(result['estimate'])}",
                  f"Sigma conhecido = {number(result['sigma'])}    EP Média = {number(result['se'])}"]
    else:
        lines += ['Método: ' + PROPORTION_METHODS[result['method']],
                  f"Eventos = {result['events']}    Ensaios = {result['n']}    Proporção = {number(result['estimate'])}"]
        if 'event' in result:
            lines.append(f"Evento: {result['event']!r}; categorias observadas: {', '.join(map(repr, result['levels']))}")
        if result['method'] == 'exact' and perform_test:
            lines.append('Teste binomial bilateral: mínimo entre 1 e duas vezes a menor cauda inclusiva.'
                         if result['alternative'] == 'two-sided' else 'Teste binomial unilateral com cauda inclusiva.')
        elif result['method'] != 'exact':
            if perform_test:
                lines.append('Teste score com variância sob H0; sem correção de continuidade.')
            if perform_test and min(result['n'] * result['null'], result['n'] * (1 - result['null'])) < 5:
                lines.append('Aproximação normal: há contagens esperadas sob H0 menores que 5.')
            if result['method'] == 'wald':
                lines.append('IC Wald: pode ultrapassar [0; 1] e degenerar com zero ou todos os eventos.')
    lines += [f"Ausentes omitidos: {result['missing']}",
              f"IC de {result['confidence']:g}%: ({number(result['low'])}; {number(result['high'])})"]
    if perform_test:
        parameter = 'média' if is_z else 'proporção'
        symbol = {'two-sided': '≠', 'less': '<', 'greater': '>'}[result['alternative']]
        p = 'Valor-p < 0,000001' if result['p'] < 1e-6 else 'Valor-p = ' + number(result['p'])
        lines += ['', f"H0: {parameter} = {number(result['null'])}",
                  f"H1: {parameter} {symbol} {number(result['null'])}"]
        if result['statistic'] is not None:
            lines.append('Z = ' + number(result['statistic']))
        lines.append(p)
    return '\n'.join(lines) + '\n'
