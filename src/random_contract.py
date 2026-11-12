"""Contrato persistente de geração aleatória, independente de Tk e do sampler."""
import math

from data_operations import MAX_ROWS, MAX_COLUMNS, MAX_CELLS
from distributions import DISTRIBUTIONS, parse_distribution_parameters

RANDOM_METHOD = 'calc.random.generate.v1'
MAX_SEED = 2 ** 128 - 1
MAX_INTEGER = 2 ** 53 - 1
RANDOM_DISTRIBUTIONS = dict(DISTRIBUTIONS, **{
    'Bernoulli': [('p', 'Probabilidade de evento p', .5)],
    'Inteiros': [('lower', 'Inteiro mínimo (inclusivo)', 1),
                 ('upper', 'Inteiro máximo (inclusivo)', 6)],
})
DISCRETE = {'Binomial', 'Poisson', 'Bernoulli', 'Inteiros'}


def validate_random_parameters(parameters):
    try:
        if (set(parameters) != {'distribution', 'distribution_parameters', 'row_count', 'column_count', 'seed', 'base_name'}
                or parameters['distribution'] not in RANDOM_DISTRIBUTIONS
                or type(parameters['row_count']) is not int or not 1 <= parameters['row_count'] <= MAX_ROWS
                or type(parameters['column_count']) is not int or not 1 <= parameters['column_count'] <= MAX_COLUMNS
                or parameters['row_count'] * parameters['column_count'] > MAX_CELLS
                or type(parameters['seed']) is not int or not 0 <= parameters['seed'] <= MAX_SEED
                or not isinstance(parameters['base_name'], str) or not parameters['base_name'].strip()
                or parameters['base_name'] != parameters['base_name'].strip()):
            raise ValueError('Confira a distribuição, as quantidades, o nome e a semente (inteiro entre 0 e 2¹²⁸−1).')
        name = parameters['distribution']
        p = parameters['distribution_parameters']
        if (not isinstance(p, dict) or set(p) != {key for key, _, _ in RANDOM_DISTRIBUTIONS[name]}
                or any(type(v) not in (int, float) or not math.isfinite(v) for v in p.values())):
            raise ValueError('Informe exatamente os parâmetros numéricos finitos da distribuição.')
        if name in DISTRIBUTIONS:
            parse_distribution_parameters(name, p)
        elif name == 'Bernoulli':
            if not 0 <= p['p'] <= 1:
                raise ValueError('A probabilidade de evento deve estar entre 0 e 1.')
        elif (any(v != int(v) or abs(v) > MAX_INTEGER for v in p.values()) or p['lower'] > p['upper']):
            raise ValueError('Use limites inteiros em ordem crescente, entre −(2⁵³−1) e 2⁵³−1.')
    except (KeyError, TypeError, AttributeError, OverflowError) as error:
        raise ValueError('Parâmetros de geração aleatória inválidos.') from error


def validate_random_capacity(headers, rows, parameters):
    height = max(len(rows), parameters['row_count'])
    width = len(headers) + parameters['column_count']
    if height > MAX_ROWS or width > MAX_COLUMNS or height * width > MAX_CELLS:
        raise ValueError(f'O resultado excede {MAX_ROWS} linhas, {MAX_COLUMNS} colunas ou {MAX_CELLS} células. Reduza as quantidades.')


def validate_random_result(result):
    try:
        p = result['parameters']
        validate_random_parameters(p)
        source = result['source']
        if source.get('kind') != 'fixed_generation' or source['column_ids'] != []:
            raise ValueError('Origem da geração aleatória inválida.')
        v = result['values']
        if set(v) != {'columns', 'discrete'} or type(v['discrete']) is not bool or v['discrete'] != (p['distribution'] in DISCRETE):
            raise ValueError('Formato dos valores aleatórios inválido.')
        if not isinstance(v['columns'], list) or len(v['columns']) != p['column_count']:
            raise ValueError('Quantidade de colunas aleatórias inválida.')
        bounds = p['distribution_parameters']
        name = p['distribution']
        for column in v['columns']:
            if not isinstance(column, list) or len(column) != p['row_count']:
                raise ValueError('Quantidade de linhas aleatórias inválida.')
            for value in column:
                if type(value) not in (int, float) or not math.isfinite(value) or (v['discrete'] and type(value) is not int):
                    raise ValueError('Valores aleatórios devem ser finitos; distribuições discretas exigem inteiros.')
                if (name in ('Binomial', 'Poisson', 'Bernoulli', 'Exponencial', 'Weibull', 'Lognormal', 'Gama', 'Qui-quadrado', 'F') and value < 0
                        or name == 'Binomial' and value > bounds['n']
                        or name in ('Bernoulli', 'Beta') and not 0 <= value <= 1
                        or name in ('Uniforme', 'Inteiros') and not bounds['lower'] <= value <= bounds['upper']):
                    raise ValueError('Valor fora do suporte da distribuição.')
        generation = result['provenance']['generation']
        if 'chunk_size' in generation and (type(generation['chunk_size']) is not int or not 1 <= generation['chunk_size'] <= MAX_ROWS):
            raise ValueError('Tamanho de bloco do gerador inválido.')
        if (generation['engine'] != 'PCG64' or generation['layout'] != 'columns_then_rows'
                or any(not isinstance(generation[k], str) or not generation[k] for k in ('numpy', 'scipy', 'python', 'application'))
                or result['provenance']['execution'] not in ('generate', 'replay_saved_values')):
            raise ValueError('Proveniência do gerador incompleta.')
        if 'storage' in result:
            storage = result['storage']
            if (storage['policy'] != 'append_new_column_per_execution' or storage['worksheet_id'] != source['worksheet_id']
                    or any(not isinstance(storage[k], list) or len(storage[k]) != p['column_count']
                           or len(set(storage[k])) != len(storage[k])
                           or any(not isinstance(x, str) or not x.strip() for x in storage[k]) for k in ('names', 'column_ids'))):
                raise ValueError('Destino da geração aleatória inválido.')
    except (KeyError, TypeError, AttributeError, OverflowError) as error:
        raise ValueError('Registro de geração aleatória incompleto.') from error
