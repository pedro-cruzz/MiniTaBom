"""Densidades, probabilidades e quantis; parametrização explícita por família."""
import math
from inference import scientific_stats
from linear_models import number


DISTRIBUTIONS = {
    'Normal': [('mean', 'Média μ', 0), ('sd', 'Desvio padrão σ', 1)],
    't de Student': [('df', 'Graus de liberdade', 10)],
    'Qui-quadrado': [('df', 'Graus de liberdade', 10)],
    'F': [('df1', 'GL do numerador', 5), ('df2', 'GL do denominador', 10)],
    'Binomial': [('n', 'Número de ensaios n', 10), ('p', 'Probabilidade de sucesso p', .5)],
    'Poisson': [('mean', 'Média λ', 3)],
    'Exponencial': [('scale', 'Média / escala', 1)],
    'Uniforme': [('lower', 'Mínimo a', 0), ('upper', 'Máximo b', 1)],
    'Weibull': [('shape', 'Forma', 2), ('scale', 'Escala', 1)],
    'Lognormal': [('meanlog', 'Média de ln(X)', 0), ('sdlog', 'Desvio padrão de ln(X)', 1)],
    'Gama': [('shape', 'Forma', 2), ('scale', 'Escala (não taxa)', 1)],
    'Beta': [('alpha', 'Forma α', 2), ('beta', 'Forma β', 2)],
}
OPERATIONS = {
    'density': 'Densidade / probabilidade pontual',
    'cdf': 'Probabilidade acumulada P(X ≤ x)',
    'sf': 'Cauda superior P(X > x)',
    'interval': 'Probabilidade P(a ≤ X ≤ b)',
    'quantile': 'Quantil pela probabilidade acumulada',
    'isf': 'Quantil pela cauda superior',
}


def frozen_distribution(name, parameters):
    if name not in DISTRIBUTIONS:
        raise ValueError('Distribuição não suportada.')
    expected = {key for key, _, _ in DISTRIBUTIONS[name]}
    if set(parameters) != expected:
        raise ValueError('Informe exatamente os parâmetros da distribuição selecionada.')
    try:
        p = {key: float(value) for key, value in parameters.items()}
    except (TypeError, ValueError) as error:
        raise ValueError('Os parâmetros devem ser numéricos.') from error
    if not all(math.isfinite(v) for v in p.values()):
        raise ValueError('Use parâmetros finitos.')
    for key in expected & {'sd', 'df', 'df1', 'df2', 'scale', 'shape', 'sdlog', 'alpha', 'beta'}:
        if p[key] <= 0:
            raise ValueError('Desvios, escalas, formas e graus de liberdade devem ser positivos.')
    if name == 'Binomial' and (not 0 <= p['n'] <= 2 ** 53 - 1 or not p['n'].is_integer() or not 0 <= p['p'] <= 1):
        raise ValueError('Use n inteiro entre 0 e 2⁵³−1 e probabilidade p entre 0 e 1.')
    if name == 'Poisson' and p['mean'] < 0:
        raise ValueError('A média de Poisson não pode ser negativa.')
    if name == 'Uniforme' and p['lower'] >= p['upper']:
        raise ValueError('O mínimo da uniforme deve ser menor que o máximo.')
    stats = scientific_stats()
    try:
        if name == 'Normal':
            dist = stats.norm(loc=p['mean'], scale=p['sd'])
        elif name == 't de Student':
            dist = stats.t(df=p['df'])
        elif name == 'Qui-quadrado':
            dist = stats.chi2(df=p['df'])
        elif name == 'F':
            dist = stats.f(dfn=p['df1'], dfd=p['df2'])
        elif name == 'Binomial':
            dist = stats.binom(n=int(p['n']), p=p['p'])
        elif name == 'Poisson':
            dist = stats.poisson(mu=p['mean'])
        elif name == 'Exponencial':
            dist = stats.expon(scale=p['scale'])
        elif name == 'Uniforme':
            scale = p['upper'] - p['lower']
            if not math.isfinite(scale):
                raise ValueError('A amplitude da uniforme excede a precisão suportada.')
            dist = stats.uniform(loc=p['lower'], scale=scale)
        elif name == 'Weibull':
            dist = stats.weibull_min(c=p['shape'], scale=p['scale'])
        elif name == 'Lognormal':
            scale = math.exp(p['meanlog'])
            if not scale:
                raise ValueError('A escala da lognormal excede a precisão suportada.')
            dist = stats.lognorm(s=p['sdlog'], scale=scale)
        elif name == 'Gama':
            dist = stats.gamma(a=p['shape'], scale=p['scale'])
        else:
            dist = stats.beta(a=p['alpha'], b=p['beta'])
    except (ArithmeticError, OverflowError) as error:
        raise ValueError('Os parâmetros excedem a precisão suportada.') from error
    return dist, name in ('Binomial', 'Poisson'), p


def distribution_calculation(name, parameters, operation, value, upper=None):
    if operation not in OPERATIONS:
        raise ValueError('Operação de distribuição inválida.')
    if not math.isfinite(value) or (upper is not None and not math.isfinite(upper)):
        raise ValueError('Informe limites ou probabilidades finitos.')
    dist, discrete, parsed = frozen_distribution(name, parameters)
    if operation in ('quantile', 'isf') and not 0 < value < 1:
        raise ValueError('A probabilidade do quantil deve estar entre 0 e 1, sem os extremos.')
    if operation == 'interval' and (upper is None or value > upper):
        raise ValueError('Informe os dois limites em ordem crescente.')
    try:
        if operation == 'density':
            result = float(dist.pmf(value) if discrete else dist.pdf(value))
        elif operation == 'cdf':
            result = float(dist.cdf(value))
        elif operation == 'sf':
            result = float(dist.sf(value))
        elif operation == 'quantile':
            result = float(dist.ppf(value))
        elif operation == 'isf':
            result = float(dist.isf(value))
        else:
            left, right = (math.ceil(value) - 1, math.floor(upper)) if discrete else (value, upper)
            if discrete and right <= left:
                result = 0.
            elif float(dist.cdf(left)) + float(dist.cdf(right)) <= 1:
                result = float(dist.cdf(right) - dist.cdf(left))
            else:
                result = float(dist.sf(left) - dist.sf(right))
    except (ArithmeticError, ValueError) as error:
        raise ValueError('Não foi possível calcular com esta precisão.') from error
    if math.isnan(result) or math.isinf(result) and operation != 'density':
        raise ValueError('O resultado excede a precisão suportada.')
    if operation in ('cdf', 'sf', 'interval'):
        result = min(1., max(0., result))
    return dict(distribution=name, parameters=parsed, operation=operation, value=value,
                upper=upper, result=result, discrete=discrete)


def format_distribution(result):
    lines = ['DISTRIBUIÇÃO — ' + result['distribution'], '',
             'Parâmetros: ' + '; '.join(label + '=' + number(result['parameters'][key]) for key, label, _ in DISTRIBUTIONS[result['distribution']])]
    op, x, answer = result['operation'], number(result['value']), number(result['result'])
    if op == 'density':
        lines.append(('P(X=' + x + ')' if result['discrete'] else 'f(' + x + ')') + ' = ' + answer)
        if not result['discrete']:
            lines.append('f(x) é densidade, não probabilidade em um ponto.')
    elif op == 'interval':
        lines.append(f"P({x} ≤ X ≤ {number(result['upper'])}) = {answer}")
    elif op in ('cdf', 'sf'):
        lines.append(f"P(X {'≤' if op == 'cdf' else '>'} {x}) = {answer}")
    else:
        lines.append(('Quantil acumulado' if op == 'quantile' else 'Quantil da cauda superior') + f' para p={x}: {answer}')
        if result['discrete']:
            lines.append('Distribuição discreta: o quantil é inteiro; a probabilidade alcançada pode diferir de p.')
    return '\n'.join(lines) + '\n'
