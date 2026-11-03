"""Anderson–Darling normal, média/desvio estimados e valor-p aproximado.

Equações publicadas na documentação Minitab, com correção de tamanho
amostral confirmada na documentação statsmodels (ver README).
"""
import math
import statistics

from core import numeric_column
from inference import scientific_stats, p_statement


MAX_NORMALITY_N = 200_000
METHODS = {'ad': 'Anderson–Darling', 'rj': 'Ryan–Joiner', 'ks': 'Kolmogorov–Smirnov (normal estimada)',
           'shapiro': 'Shapiro–Wilk', 'dagostino': 'D’Agostino–Pearson'}


def ad_probability(adjusted):
    if not math.isfinite(adjusted) or adjusted < 0:
        raise ValueError('Estatística Anderson–Darling inválida.')
    if adjusted > 13:
        return None, math.exp(1.2937 - 5.709 * 13 + .0186 * 13**2)
    if adjusted < .2:
        p = -math.expm1(-13.436 + 101.14 * adjusted - 223.73 * adjusted**2)
    elif adjusted < .34:
        p = -math.expm1(-8.318 + 42.796 * adjusted - 59.938 * adjusted**2)
    elif adjusted < .6:
        p = math.exp(.9177 - 4.279 * adjusted - 1.38 * adjusted**2)
    else:
        p = math.exp(1.2937 - 5.709 * adjusted + .0186 * adjusted**2)
    return min(1., max(0., p)), None


def _ad_test(values):
    n = len(values)
    if not 3 <= n <= MAX_NORMALITY_N or not all(math.isfinite(x) for x in values):
        raise ValueError(f'Anderson–Darling requer entre 3 e {MAX_NORMALITY_N} números finitos nesta implementação.')
    try:
        mean, sd = statistics.mean(values), statistics.stdev(values)
        if not math.isfinite(sd) or sd <= 0:
            raise ValueError('A amostra deve ter desvio padrão positivo e finito.')
        scale = max(abs(x) for x in values)
        ordered = sorted(values)
        standardized = [(x - mean) / sd if math.isfinite(x - mean) else
                        (x / scale - mean / scale) / (sd / scale) for x in ordered]
        if not all(math.isfinite(x) for x in standardized):
            raise ValueError('Magnitude dos dados excede a precisão numérica suportada.')
        normal = scientific_stats().norm
        left, right = normal.logcdf(standardized), normal.logsf(standardized)
        statistic = -n - math.fsum((2 * i - 1) / n * (float(left[i - 1]) + float(right[n - i]))
                                   for i in range(1, n + 1))
        if not math.isfinite(statistic) or statistic < -1e-9:
            raise ValueError('Estatística fora da precisão numérica suportada.')
        statistic = max(0., statistic)
        adjusted = statistic * (1 + .75 / n + 2.25 / n**2)
        p, upper = ad_probability(adjusted)
    except ArithmeticError as error:
        raise ValueError('Magnitude dos dados excede a precisão numérica suportada.') from error
    return dict(n=n, mean=mean, sd=sd, statistic=statistic, adjusted=adjusted, p=p, p_upper=upper,
                repeated=n - len(set(values)), missing=0, source='Amostra')


def rj_critical(n):
    """Faixas conferidas com a tabela de Ryan/Joiner e nota de Ryan (1990).

    A página atual de ajuda inverte as legendas das duas faixas; a atribuição
    abaixo reproduz a tabela dos autores (n=4,5,10,...,1000), não a inversão.
    """
    if n <= 50:
        return (1.0071-.1371/math.sqrt(n)-.3682/n+.7780/n**2,
                1.0063-.1288/math.sqrt(n)-.6118/n+1.3505/n**2,
                .9963-.0211/math.sqrt(n)-1.4106/n+3.1791/n**2)
    return (.999878-.0009991/math.sqrt(n)-1.26149/n+2.22173/n**1.5,
            .999494+.0177805/math.sqrt(n)-1.77265/n+3.55823/n**1.5,
            .999040+.0362180/math.sqrt(n)-2.52631/n+4.36612/n**1.5)


def normality_test(values, method='ad'):
    if method not in METHODS:
        raise ValueError('Método de normalidade inválido.')
    if method == 'ad':
        result = _ad_test(values)
        result.update(method_key=method, method=METHODS[method], stat_label='A²')
        return result
    minimum = 4 if method == 'rj' else 8 if method == 'dagostino' else 3
    maximum = 1000 if method == 'rj' else 5000 if method == 'shapiro' else MAX_NORMALITY_N
    if not minimum <= len(values) <= maximum or not all(math.isfinite(v) for v in values):
        raise ValueError(f'{METHODS[method]}: use entre {minimum} e {maximum} números finitos.')
    sd, mean = statistics.stdev(values), statistics.mean(values)
    if not math.isfinite(sd) or sd <= 0:
        raise ValueError('A amostra deve ter desvio padrão positivo e finito.')
    stats, n = scientific_stats(), len(values)
    scale = max(abs(v) for v in values)
    ordered = sorted(values)
    normalized = [v/scale for v in ordered]
    result = dict(n=n, mean=mean, sd=sd, missing=0, source='Amostra', repeated=n-len(set(values)),
                  method_key=method, method=METHODS[method], p_upper=None, p_lower=None)
    if method == 'rj':
        if len(set(values)) < 3:
            raise ValueError('Ryan–Joiner requer pelo menos três valores distintos; a correlação de postos pode degenerar com somente dois níveis.')
        ranks = stats.rankdata(ordered, method='average')
        scores = stats.norm.ppf((ranks-.375)/(n+.25))
        statistic = float(stats.pearsonr(normalized, scores).statistic)
        c10, c05, c01 = rj_critical(n)
        result['critical'] = {'0.10': c10, '0.05': c05, '0.01': c01}
        if statistic > c10:
            p, result['p_lower'] = None, .1
        elif statistic <= c01:
            p, result['p_upper'] = None, .01
        elif statistic > c05:
            p = .05 + (statistic-c05)/(c10-c05)*.05
        else:
            p = .01 + (statistic-c01)/(c05-c01)*.04
        result['stat_label'] = 'RJ'
    elif method == 'ks':
        z = [(v-mean)/sd for v in ordered]
        probabilities = stats.norm.cdf(z)
        statistic = max(max((i+1)/n-float(p) for i,p in enumerate(probabilities)),
                        max(float(p)-i/n for i,p in enumerate(probabilities)))
        adjusted = statistic*(math.sqrt(n)-.01+.85/math.sqrt(n))
        result['adjusted'] = adjusted
        if adjusted < .775:
            p, result['p_lower'] = None, .15
        elif adjusted >= 1.035:
            p, result['p_upper'] = None, .01
        else:
            for upper, low_p, width, delta in [(.819,.1,.044,.05),(.895,.05,.076,.05),(.995,.025,.1,.025),(1.035,.01,.04,.015)]:
                if adjusted < upper:
                    p=low_p+(upper-adjusted)/width*delta
                    break
        result['stat_label'] = 'D'
    else:
        test = stats.shapiro(normalized) if method == 'shapiro' else stats.normaltest(normalized)
        statistic, p = float(test.statistic), float(test.pvalue)
        result['stat_label'] = 'W' if method == 'shapiro' else 'K²'
    if not math.isfinite(statistic) or (p is not None and (not math.isfinite(p) or not 0 <= p <= 1)):
        raise ValueError('Não foi possível calcular a normalidade com esta precisão.')
    result.update(statistic=statistic, p=p)
    return result


def analyze_normality(headers, rows, column, method='ad'):
    if type(column) is not int or not 0 <= column < len(headers):
        raise ValueError('Selecione a coluna da amostra.')
    values, missing = numeric_column(rows, column)
    result = normality_test(values, method=method)
    result.update(source=headers[column], missing=missing)
    return result


def format_normality(result):
    lines = ['TESTE DE NORMALIDADE — ' + result['source'], '',
             'Método: ' + result.get('method', 'Anderson–Darling') + '. Média e desvio estimados dos dados.',
             'H0: a população segue uma distribuição normal.', 'H1: a população não segue uma distribuição normal.',
             f"N = {result['n']}    Ausentes omitidos = {result['missing']}",
             f"Média = {result['mean']:.9g}    Desvio padrão = {result['sd']:.9g}",
             f"{result.get('stat_label','A²')} = {result['statistic']:.9g}"]
    if 'adjusted' in result:
        lines.append(f"Estatística ajustada = {result['adjusted']:.9g}")
    lines.append(f"Valor-p aproximado > {result['p_lower']:.9g}" if result.get('p_lower') is not None else
                 f"Valor-p aproximado < {result['p_upper']:.9g}" if result['p'] is None else
                 p_statement(result['p'], 'Valor-p aproximado'))
    lines.append(f"Observações repetidas além da primeira ocorrência: {result['repeated']}")
    if result['n'] < 20:
        lines.append('Amostra pequena: o teste pode ter pouco poder para detectar desvios de normalidade.')
    if result.get('method_key')=='dagostino' and result['n']<20:
        lines.append('D’Agostino–Pearson: a aproximação da curtose pode ser pouco precisa com N<20.')
    lines.append('Um valor-p alto não comprova normalidade; avalie também a amostragem e o padrão dos dados.')
    return '\n'.join(lines) + '\n'
