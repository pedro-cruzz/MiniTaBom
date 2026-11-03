"""Anderson–Darling normal, média/desvio estimados e valor-p aproximado.

Equações publicadas na documentação Minitab, com correção de tamanho
amostral confirmada na documentação statsmodels (ver README).
"""
import math
import statistics

from core import numeric_column
from inference import scientific_stats, p_statement


MAX_NORMALITY_N = 200_000


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


def normality_test(values):
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


def analyze_normality(headers, rows, column):
    if type(column) is not int or not 0 <= column < len(headers):
        raise ValueError('Selecione a coluna da amostra.')
    values, missing = numeric_column(rows, column)
    result = normality_test(values)
    result.update(source=headers[column], missing=missing)
    return result


def format_normality(result):
    lines = ['TESTE DE NORMALIDADE — ' + result['source'], '',
             'Método: Anderson–Darling, média e desvio amostral estimados dos dados.',
             'H0: a população segue uma distribuição normal.', 'H1: a população não segue uma distribuição normal.',
             f"N = {result['n']}    Ausentes omitidos = {result['missing']}",
             f"Média = {result['mean']:.9g}    Desvio padrão = {result['sd']:.9g}",
             f"A² = {result['statistic']:.9g}    A² ajustado = {result['adjusted']:.9g}"]
    lines.append(f"Valor-p aproximado < {result['p_upper']:.9g}" if result['p'] is None else
                 p_statement(result['p'], 'Valor-p aproximado'))
    lines.append(f"Observações repetidas além da primeira ocorrência: {result['repeated']}")
    if result['n'] < 20:
        lines.append('Amostra pequena: o teste pode ter pouco poder para detectar desvios de normalidade.')
    lines.append('Um valor-p alto não comprova normalidade; avalie também a amostragem e o padrão dos dados.')
    return '\n'.join(lines) + '\n'
