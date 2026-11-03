"""Testes de postos e igualdade de variâncias com métodos explícitos."""
from collections import Counter
from decimal import Decimal, InvalidOperation
import math
import statistics
import warnings

from anova import prepare_groups
from inference import scientific_stats, p_statement

TITLES = {'mannwhitney': 'Mann–Whitney', 'wilcoxon': 'Wilcoxon pareado',
          'kruskal': 'Kruskal–Wallis', 'variances': 'Igualdade de variâncias'}


def paired_values(headers, rows, first, second):
    if (type(first) is not int or type(second) is not int or first == second
            or not 0 <= first < len(headers) or not 0 <= second < len(headers)):
        raise ValueError('Selecione duas colunas diferentes para os pares.')
    differences, line_values, excluded = [], [], 0
    for line, row in enumerate(rows, 1):
        values = []
        for index in (first, second):
            raw = str(row[index]).strip()
            if raw in ('', '*'):
                values.append(None)
            else:
                try:
                    value = Decimal(raw.replace(',', '.'))
                    if not value.is_finite():
                        raise InvalidOperation
                except InvalidOperation:
                    raise ValueError(f'Linha {line}, {headers[index]}: número inválido.') from None
                values.append(value)
        if None in values:
            line_values.append('')
            excluded += 1
            continue
        difference = float(values[0] - values[1])
        if not math.isfinite(difference):
            raise ValueError('Diferença fora da precisão numérica suportada.')
        differences.append(difference)
        line_values.append(format(difference, '.17g'))
    if len(differences) < 2:
        raise ValueError('São necessários pelo menos dois pares válidos.')
    return differences, line_values, excluded


def _mann(first, second, alternative, method, correction):
    stats = scientific_stats()
    ties = len(set(first + second)) < len(first) + len(second)
    selected = ('exact' if not ties and min(len(first), len(second)) <= 8 else 'asymptotic') if method == 'auto' else method
    if selected == 'exact' and (ties or len(first) * len(second) > 10000 or min(len(first), len(second)) > 20):
        raise ValueError('Exato de Mann–Whitney: requer ausência de empates, menor N≤20 e produto dos N≤10000. Use aproximação com empates.')
    if len(set(first + second)) == 1:
        return len(first) * len(second) / 2, 1., selected, ties
    result = stats.mannwhitneyu(first, second, alternative=alternative, method=selected, use_continuity=correction)
    return float(result.statistic), float(result.pvalue), selected, ties


def analyze_study(headers, rows, mode, columns=None, response=None, factor=None,
                  alternative='two-sided', method='auto', correction=True, zero_method='wilcox', center='median'):
    if mode not in TITLES or alternative not in ('two-sided', 'less', 'greater'):
        raise ValueError('Teste ou hipótese alternativa inválida.')
    if method not in ('auto', 'exact', 'asymptotic') or zero_method not in ('wilcox', 'pratt', 'zsplit'):
        raise ValueError('Método de cálculo inválido.')
    stats = scientific_stats()
    notes, details = [], []
    if mode == 'wilcoxon':
        if columns is None or len(columns) != 2:
            raise ValueError('Selecione as duas colunas pareadas.')
        differences, _, excluded = paired_values(headers, rows, *columns)
        zeros = differences.count(0.)
        nonzero = [v for v in differences if v != 0]
        ties = len({abs(v) for v in nonzero}) < len(nonzero)
        selected = ('exact' if len(nonzero) <= 25 and not zeros and not ties else 'asymptotic') if method == 'auto' else method
        if selected == 'exact' and (zeros or ties or len(nonzero) > 50):
            raise ValueError('Exato de Wilcoxon: requer até 50 diferenças, sem zeros ou empates absolutos. Use aproximação.')
        if not nonzero:
            statistic, p = 0., 1.
            selected = 'todas as diferenças são zero'
        else:
            result = stats.wilcoxon(differences, zero_method=zero_method, correction=correction,
                                    alternative=alternative, method=selected)
            statistic, p = float(result.statistic), float(result.pvalue)
        summaries = [dict(label='Diferença: ' + headers[columns[0]] + ' − ' + headers[columns[1]],
                          n=len(differences), median=statistics.median(differences))]
        details += [f'Pares excluídos: {excluded}; diferenças zero: {zeros}; regra de zeros: {zero_method}.',
                    'Diferenças calculadas a partir dos textos decimais; postos médios nos empates.',
                    'H0: distribuição das diferenças simétrica em torno de zero.']
        df = None
    else:
        groups, excluded = prepare_groups(headers, rows, columns=columns, response=response, factor=factor)
        values = [g['values'] for g in groups]
        count = sum(map(len, values))
        if count > 200000 or len(groups) > 50:
            raise ValueError('Use até 200000 observações e 50 grupos por análise.')
        summaries = [dict(label=g['label'], n=len(g['values']), median=statistics.median(g['values']),
                          sd=statistics.stdev(g['values'])) for g in groups]
        if mode == 'mannwhitney':
            if len(groups) != 2:
                raise ValueError('Mann–Whitney requer exatamente dois grupos.')
            statistic, p, selected, ties = _mann(*values, alternative, method, correction)
            details += ['Estatística U da primeira amostra.', 'H0: as distribuições das duas populações são iguais.',
                        'A interpretação como diferença de localização requer formas de distribuição comparáveis.']
            df = None
        elif mode == 'kruskal':
            if len(set(v for g in values for v in g)) == 1:
                raise ValueError('Todos os valores são iguais: não há variação de postos para este teste.')
            result = stats.kruskal(*values)
            statistic, p = float(result.statistic), float(result.pvalue)
            selected, df = 'qui-quadrado aproximado, correção de empates', len(groups) - 1
            details += ['H0: distribuições com mesma localização (interpretação em medianas sob formas comparáveis).',
                        'O teste global não identifica quais pares diferem.']
            if any(len(g) < 5 for g in values):
                notes.append('Há grupo com N<5; a aproximação qui-quadrado pode ser inadequada.')
        else:
            if center not in ('median', 'mean', 'bartlett'):
                raise ValueError('Método de comparação de variâncias inválido.')
            scale = max(abs(v) for g in values for v in g)
            if not scale:
                raise ValueError('Os grupos não possuem dispersão.')
            scaled = [[v / scale for v in g] for g in values]
            if center == 'bartlett' and any(s['sd'] == 0 for s in summaries):
                raise ValueError('Bartlett exige desvio padrão positivo em todos os grupos.')
            with warnings.catch_warnings():
                warnings.simplefilter('ignore', RuntimeWarning)
                result = stats.bartlett(*scaled) if center == 'bartlett' else stats.levene(*scaled, center=center)
            statistic, p = float(result.statistic), float(result.pvalue)
            selected = ('Bartlett — pressupõe normalidade' if center == 'bartlett' else
                        'Levene centrado na mediana (Brown–Forsythe)' if center == 'median' else 'Levene centrado na média')
            df = [len(groups)-1, count-len(groups)] if center != 'bartlett' else len(groups)-1
            positive = [s['sd'] for s in summaries if s['sd'] > 0]
            ratio = (max(positive) / min(positive)) ** 2 if len(positive) == len(summaries) else None
            details += ['H0: todas as variâncias populacionais são iguais.',
                        f'Razão maior/menor variância: {ratio:.9g}' if ratio is not None else 'Razão maior/menor: indefinida por grupo constante.']
        details.append(f'Observações/linhas excluídas: {excluded}.')
    if not all(math.isfinite(v) for v in (statistic, p)) or not 0 <= p <= 1:
        raise ValueError('O teste é indefinido para estas dispersões ou não pode ser calculado com esta precisão.')
    return dict(mode=mode, title=TITLES[mode], statistic=statistic, p=p, method=selected, df=df,
                summaries=summaries, alternative=alternative, correction=correction, details=details, notes=notes)


def format_study(result):
    lines = [result['title'].upper(), '', 'Método: ' + result['method']]
    for s in result['summaries']:
        lines.append(f"{s['label']}: N={s['n']}; mediana={s['median']:.9g}" +
                     (f"; desvio amostral={s['sd']:.9g}" if 'sd' in s else ''))
    lines += ['', f"Estatística = {result['statistic']:.9g}", p_statement(result['p'])]
    if result['df'] is not None:
        lines.append('GL = ' + str(result['df']))
    if result['mode'] in ('mannwhitney', 'wilcoxon'):
        lines += ['Alternativa: ' + {'two-sided':'bilateral', 'less':'primeira menor que segunda', 'greater':'primeira maior que segunda'}[result['alternative']],
                  'Correção de continuidade na aproximação: ' + ('sim' if result['correction'] else 'não')]
    return '\n'.join(lines + result['details'] + result['notes']) + '\n'
