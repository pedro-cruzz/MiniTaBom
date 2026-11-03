"""Duas proporções e inferência normal para uma/duas variâncias.

Métodos explícitos. Não presume equivalência com padrões do Minitab 16.
"""
import math
import statistics

from basic_inference import _count, _options, _normal_p
from inference import scientific_stats, p_statement
from sample_inputs import independent_samples
from exact_tables import fisher_probability, FISHER_MAX_TOTAL


EXTENDED_TITLES = {'two_proportions': 'Teste de duas proporções',
                   'one_variance': 'Teste de uma variância', 'two_variances': 'Teste de duas variâncias'}


def _positive(value, label):
    if not math.isfinite(value) or value <= 0:
        raise ValueError(label + ': informe um número finito maior que zero.')
    return value


def two_proportions(events1, n1, events2, n2, null=0, confidence=95,
                    alternative='two-sided', pooled=False):
    for events, n in ((events1, n1), (events2, n2)):
        _count(n, 1, 'Número de ensaios')
        _count(events, 0, 'Número de eventos')
        if events > n:
            raise ValueError('Eventos não podem exceder o número de ensaios.')
    _, tail = _options(null, confidence, alternative)
    if not -1 <= null <= 1:
        raise ValueError('A diferença hipotética p1−p2 deve estar entre −1 e 1.')
    if pooled and null != 0:
        raise ValueError('A estimativa combinada exige diferença hipotética igual a zero.')
    p1, p2 = events1 / n1, events2 / n2
    estimate = p1 - p2
    se = math.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)
    common = (events1 + events2) / (n1 + n2)
    se_test = math.sqrt(common * (1 - common) * (1 / n1 + 1 / n2)) if pooled else se
    critical = float(scientific_stats().norm.isf(tail))
    margin = critical * se
    z = (estimate - null) / se_test if se_test > 0 else None
    p = _normal_p(z, alternative) if z is not None else None
    fisher = (fisher_probability(
        [[events1, n1 - events1], [events2, n2 - events2]], alternative=alternative)
        if null == 0 else None)
    warnings = []
    if min(events1, n1 - events1, events2, n2 - events2) < 5:
        warnings.append('Há contagens de eventos ou não eventos menores que 5; a aproximação normal pode ser inadequada.')
    if se == 0:
        warnings.append('IC Wald degenerado: erro padrão estimado igual a zero.')
    if z is None:
        warnings.append('Teste Z indisponível: erro padrão do teste igual a zero.')
    low = -1. if alternative == 'less' else estimate - margin
    high = 1. if alternative == 'greater' else estimate + margin
    if not all(math.isfinite(v) for v in (low, high)) or low > high:
        raise ValueError('Não foi possível calcular o intervalo com esta confiança.')
    return dict(mode='two_proportions', samples=[dict(n=n1, events=events1, estimate=p1, missing=0, name='Amostra 1'),
                dict(n=n2, events=events2, estimate=p2, missing=0, name='Amostra 2')],
                estimate=estimate, se=se, statistic=z, p=p, fisher=fisher, pooled=pooled,
                low=low, high=high,
                null=null, confidence=confidence, alternative=alternative, warnings=warnings,
                source='Dados resumidos', excluded_groups=0)


def _variance(value, measure):
    if measure not in ('sd', 'variance'):
        raise ValueError('Selecione desvio padrão ou variância.')
    _positive(value, 'Dispersão amostral ou hipótese')
    return _positive(value * value if measure == 'sd' else value,
                     'Variância fora da precisão numérica suportada')


def _tail_p(distribution, value, alternative):
    lower, upper = float(distribution.cdf(value)), float(distribution.sf(value))
    return min(1., 2 * min(lower, upper)) if alternative == 'two-sided' else (
        lower if alternative == 'less' else upper)


def _variance_interval(estimate, distribution, tail, alternative, multiplier=1):
    low = 0. if alternative == 'less' else estimate * (multiplier / _positive(float(distribution.isf(tail)), 'Quantil'))
    high = math.inf if alternative == 'greater' else estimate * (multiplier / _positive(float(distribution.ppf(tail)), 'Quantil'))
    for value, open_bound in ((low, alternative == 'less'), (high, alternative == 'greater')):
        if not open_bound:
            _positive(value, 'Limite fora da precisão numérica suportada')
    if low > high:
        raise ValueError('O intervalo não pôde ser calculado com esta precisão.')
    return low, high


def one_variance(n, value, null=1, confidence=95, alternative='two-sided', measure='sd'):
    _count(n, 2, 'Tamanho amostral')
    _, tail = _options(null, confidence, alternative)
    variance, null_variance = _variance(value, measure), _variance(null, measure)
    statistic = _positive((variance / null_variance) * (n - 1), 'Estatística qui-quadrado')
    distribution = scientific_stats().chi2(n - 1)
    # GL/quantil primeiro evita formar GL*s², que pode transbordar.
    low, high = _variance_interval(variance, distribution, tail, alternative, multiplier=n - 1)
    if measure == 'sd':
        low, high = math.sqrt(low), math.sqrt(high)
    return dict(mode='one_variance', samples=[dict(n=n, variance=variance, sd=math.sqrt(variance),
                missing=0, name='Amostra')], measure=measure, estimate=value, low=low, high=high,
                statistic=statistic, df=[n - 1], p=_tail_p(distribution, statistic, alternative),
                null=null, confidence=confidence, alternative=alternative, source='Dados resumidos', excluded_groups=0)


def two_variances(n1, value1, n2, value2, null=1, confidence=95, alternative='two-sided', measure='sd'):
    _count(n1, 2, 'Tamanho da primeira amostra')
    _count(n2, 2, 'Tamanho da segunda amostra')
    _, tail = _options(null, confidence, alternative)
    v1, v2, null_ratio = _variance(value1, measure), _variance(value2, measure), _variance(null, measure)
    ratio = _positive(v1 / v2, 'Razão de variâncias')
    statistic = _positive(ratio / null_ratio, 'Estatística F')
    distribution = scientific_stats().f(n1 - 1, n2 - 1)
    low, high = _variance_interval(ratio, distribution, tail, alternative)
    if measure == 'sd':
        low, high = math.sqrt(low), math.sqrt(high)
    return dict(mode='two_variances', samples=[dict(n=n1, variance=v1, sd=math.sqrt(v1), missing=0, name='Amostra 1'),
                dict(n=n2, variance=v2, sd=math.sqrt(v2), missing=0, name='Amostra 2')],
                measure=measure, estimate=value1 / value2, statistic=statistic, df=[n1 - 1, n2 - 1],
                p=_tail_p(distribution, statistic, alternative), low=low, high=high, null=null,
                confidence=confidence, alternative=alternative, source='Dados resumidos', excluded_groups=0)


def analyze_extended(headers, rows, mode, columns, source='columns', group=None, events=None, **options):
    if mode not in EXTENDED_TITLES:
        raise ValueError('Análise inválida.')
    expected = 1 if mode == 'one_variance' else 2
    if (source == 'columns' and len(columns) != expected) or (source == 'stacked' and expected == 1):
        raise ValueError('Quantidade de colunas ou formato inválido para a análise.')
    samples, excluded = independent_samples(headers, rows, columns, source, group, numeric=mode != 'two_proportions')
    if mode == 'two_proportions':
        if not events or len(events) != 2 or any(str(e).strip() in ('', '*') for e in events):
            raise ValueError('Defina o evento de cada amostra; vazio e * representam ausentes.')
        counts = []
        for sample, event in zip(samples, events):
            event = str(event).strip()
            levels = set(sample['values'])
            if len(levels) > 2 or (len(levels) == 2 and event not in levels):
                raise ValueError(f"{sample['name']}: use até duas categorias e um evento correspondente.")
            sample['event'] = event
            counts.extend((sample['values'].count(event), len(sample['values'])))
        result = two_proportions(*counts, **options)
    else:
        measure = options.get('measure', 'sd')
        summaries = []
        for sample in samples:
            if len(sample['values']) < 2:
                raise ValueError(f"{sample['name']}: são necessárias pelo menos duas observações válidas.")
            try:
                value = statistics.stdev(sample['values']) if measure == 'sd' else statistics.variance(sample['values'])
                _positive(value, 'Dispersão amostral')
            except (ArithmeticError, ValueError) as error:
                raise ValueError(f"{sample['name']}: dispersão nula ou fora da precisão suportada.") from error
            summaries.extend((len(sample['values']), value))
        result = (one_variance if expected == 1 else two_variances)(*summaries, **options)
    for calculated, sample in zip(result['samples'], samples):
        calculated.update({key: value for key, value in sample.items() if key != 'values'})
    result.update(source='Colunas separadas' if source == 'columns' else 'Amostras empilhadas (ordem de aparição dos grupos)',
                  excluded_groups=excluded)
    return result


def format_extended(result, perform_test=True):
    def number(value):
        return 'indisponível' if value is None else '+∞' if value == math.inf else f'{value:.9g}'
    proportion = result['mode'] == 'two_proportions'
    title = {'two_proportions': 'TESTE DE DUAS PROPORÇÕES', 'one_variance': 'TESTE DE UMA VARIÂNCIA',
             'two_variances': 'TESTE DE DUAS VARIÂNCIAS'}[result['mode']]
    lines = [title + ' — ' + result['source'], '']
    if proportion:
        lines += ['IC Wald com estimativas separadas; sem correção de continuidade.']
        if perform_test:
            lines += ['Teste Z: estimativa ' + ('combinada sob H0.' if result['pooled'] else 'separada em cada amostra.')]
        parameter = 'p1 − p2'
    else:
        parameter = ('σ' if result['measure'] == 'sd' else 'σ²') if result['mode'] == 'one_variance' else (
            'σ1 / σ2' if result['measure'] == 'sd' else 'σ1² / σ2²')
        lines += ['Método: qui-quadrado para uma amostra.' if result['mode'] == 'one_variance' else
                  'Método: F para duas amostras independentes; bilateral por duas vezes a menor cauda.',
                  'Pressuposto: populações normais; teste e IC são sensíveis à falta de normalidade.']
    for index, sample in enumerate(result['samples'], 1):
        line = f"Amostra {index}: {sample['name']}    N = {sample['n']}    Ausentes = {sample['missing']}"
        if proportion:
            line += f"    Eventos = {sample['events']}    p = {number(sample['estimate'])}"
            if 'event' in sample:
                line += f"    Evento = {sample['event']!r}"
        else:
            line += f"    Desvio = {number(sample['sd'])}    Variância = {number(sample['variance'])}"
        lines.append(line)
    lines += [f"Linhas excluídas por grupo ausente: {result['excluded_groups']}",
              f"Estimativa ({parameter}) = {number(result['estimate'])}",
              f"IC de {result['confidence']:g}%: ({number(result['low'])}; {number(result['high'])})"]
    if perform_test:
        symbol = {'two-sided': '≠', 'less': '<', 'greater': '>'}[result['alternative']]
        lines += ['', f"H0: {parameter} = {number(result['null'])}", f"H1: {parameter} {symbol} {number(result['null'])}",
                  ('Z' if proportion else 'Qui-quadrado' if result['mode'] == 'one_variance' else 'F') +
                  ' = ' + number(result['statistic'])]
        if not proportion:
            lines.append('GL = ' + ', '.join(map(str, result['df'])))
        lines.append(p_statement(result['p'], 'Valor-p normal' if proportion else 'Valor-p'))
        if proportion:
            if result['fisher'] is not None:
                lines.append(p_statement(result['fisher'], 'Fisher exato (SciPy, ordenação por probabilidade): valor-p'))
            elif result['null'] != 0:
                lines.append('Fisher não calculado: requer H0: p1−p2 = 0.')
            else:
                lines.append(f'Fisher não calculado: limite operacional de {FISHER_MAX_TOTAL} ensaios no total.')
    for warning in result.get('warnings', []):
        if perform_test or not warning.startswith('Teste Z'):
            lines.append('Atenção: ' + warning)
    if proportion:
        lines.append('O IC Wald pode ultrapassar [−1; 1] e degenerar nos extremos.')
    return '\n'.join(lines) + '\n'
