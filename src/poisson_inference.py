"""Inferência de uma taxa Poisson; exposição comum por observação.

Exato bilateral ordenado pela razão de verossimilhanças, não por PMF.
Referência: suporte Minitab, 1-Sample Poisson Rate, methods and formulas.
"""
import math

from basic_inference import _count, _options, _normal_p, parse_count
from inference import scientific_stats, p_statement


METHODS = {'exact': 'Exato: razão de verossimilhanças / IC Garwood',
           'normal': 'Aproximação normal: variância estimada / IC Wald'}
TITLE = 'Taxa de Poisson de uma amostra'
MAX_EXPECTED = 1e12


def _deviance(k, mean):
    if k == 0:
        return mean
    relative = (k - mean) / mean
    if abs(relative) < .125:
        # Série evita cancelamento perto da média: (1+r)log(1+r)-r.
        term = relative * relative
        total = 0.
        for j in range(2, 32):
            total += term / (j * (j - 1))
            term *= -relative
        return max(0., mean * total)
    return max(0., k * (math.log(k) - math.log(mean)) - k + mean)


def poisson_exact_p(events, mean, alternative='two-sided'):
    """Caudas inclusivas, bilateral pela deviance >= observada.

Busca binária dos cortes inteiros: O(log(mean)), sem somar milhões
de probabilidades. Tolerância 1e-12 na escala da deviance para empates.
"""
    if mean == 0:
        return float(events == 0 or alternative == 'less')
    distribution = scientific_stats().poisson(mean)
    if alternative == 'less':
        return float(distribution.cdf(events))
    if alternative == 'greater':
        return float(distribution.sf(events - 1))
    target = _deviance(events, mean)
    tolerance = 1e-12 * max(1., target)
    if target <= tolerance:
        return 1.
    threshold = target - tolerance
    if events < mean:
        low, high = math.floor(mean), math.ceil(math.e * mean) + 1
        while high - low > 1:
            middle = (low + high) // 2
            if _deviance(middle, mean) >= threshold:
                high = middle
            else:
                low = middle
        return min(1., float(distribution.cdf(events) + distribution.sf(high - 1)))
    if _deviance(0, mean) < threshold:
        return float(distribution.sf(events - 1))
    low, high = 0, math.ceil(mean)
    while high - low > 1:
        middle = (low + high) // 2
        if _deviance(middle, mean) >= threshold:
            low = middle
        else:
            high = middle
    return min(1., float(distribution.cdf(low) + distribution.sf(events - 1)))


def one_poisson(events, n, length=1., null=1., confidence=95., alternative='two-sided', method='exact'):
    _count(events, 0, 'Total de ocorrências')
    _count(n, 1, 'Número de observações')
    _, tail = _options(null, confidence, alternative)
    if method not in METHODS:
        raise ValueError('Método de Poisson inválido.')
    if not math.isfinite(length) or length <= 0 or null < 0:
        raise ValueError('Use duração/exposição positiva e taxa hipotética não negativa.')
    exposure = n * length
    if not math.isfinite(exposure) or exposure <= 0:
        raise ValueError('Exposição total fora da precisão suportada.')
    mean = exposure * null
    if not math.isfinite(mean) or mean > MAX_EXPECTED or (null > 0 and mean == 0):
        raise ValueError('Total esperado sob H0 deve ser representável e não exceder 10^12.')
    estimate = events / exposure
    se = math.sqrt(events) / exposure
    stats = scientific_stats()
    statistic = None
    warnings = []
    if method == 'exact':
        low = 0. if events == 0 or alternative == 'less' else float(stats.chi2.ppf(tail, 2 * events)) / 2 / exposure
        high = math.inf if alternative == 'greater' else float(stats.chi2.isf(tail, 2 * (events + 1))) / 2 / exposure
        p = poisson_exact_p(events, mean, alternative)
    else:
        margin = float(stats.norm.isf(tail)) * se
        low = 0. if alternative == 'less' else estimate - margin
        high = math.inf if alternative == 'greater' else estimate + margin
        if se > 0:
            statistic = (estimate - null) / se
            p = _normal_p(statistic, alternative)
        else:
            p = None
            warnings.append('Sem ocorrências: teste Z indisponível e IC Wald degenerado; prefira o método exato.')
        if events <= 10:
            warnings.append('Total de ocorrências ≤10: a aproximação normal pode ser inadequada.')
        if low < 0:
            warnings.append('O limite Wald negativo não foi truncado; a taxa populacional é não negativa.')
    numbers = [estimate, se]
    if alternative != 'greater':
        numbers.append(high)
    numbers.append(low)
    if statistic is not None:
        numbers.append(statistic)
    if not all(math.isfinite(value) for value in numbers) or low > high:
        raise ValueError('Taxa ou intervalo fora da precisão numérica suportada.')
    return dict(events=events, n=n, length=length, exposure=exposure, estimate=estimate,
                se=se, mean=events / n, null=null, confidence=confidence,
                alternative=alternative, method=method, statistic=statistic, p=p,
                low=low, high=high, missing=0, source='Dados resumidos', warnings=warnings)


def analyze_poisson(headers, rows, column, **options):
    if type(column) is not int or not 0 <= column < len(headers):
        raise ValueError('Selecione uma coluna de contagens.')
    events = n = missing = 0
    for position, row in enumerate(rows, 1):
        text = str(row[column]).strip()
        if text in ('', '*'):
            missing += 1
            continue
        events += parse_count(text, f'Linha {position}: contagem')
        n += 1
    result = one_poisson(events, n, **options)
    result.update(source=f'C{column + 1} {headers[column]}', missing=missing)
    return result


def format_poisson(result, perform_test=True):
    def number(value):
        return '+∞' if value == math.inf else f'{value:.9g}'
    lines = ['TAXA DE POISSON DE UMA AMOSTRA — ' + result['source'], '',
             'Método: ' + METHODS[result['method']],
             f"Observações = {result['n']}    Ocorrências = {result['events']}    Ausentes = {result['missing']}",
             f"Exposição por observação = {number(result['length'])}    Exposição total = {number(result['exposure'])}",
             f"Taxa por unidade = {number(result['estimate'])}    Média por observação = {number(result['mean'])}",
             f"IC de {result['confidence']:g}% da taxa: ({number(result['low'])}; {number(result['high'])})"]
    if perform_test:
        symbol = {'two-sided': '≠', 'less': '<', 'greater': '>'}[result['alternative']]
        lines += [f"H0: taxa = {number(result['null'])}; H1: taxa {symbol} {number(result['null'])}."]
        if result['method'] == 'exact':
            lines.append('Bilateral por razão de verossimilhanças; unilaterais por caudas inclusivas.')
        elif result['statistic'] is not None:
            lines.append('Z = ' + number(result['statistic']))
        lines.append(p_statement(result['p']))
    lines += result['warnings']
    lines.append('Modelo: ocorrências independentes, taxa constante e igual exposição em cada observação.')
    lines.append('O IC exato usa caudas iguais; não é inversão do teste bilateral por verossimilhanças.')
    return '\n'.join(lines) + '\n'
