"""Amostras independentes por operação; reprodução histórica usa o snapshot."""
from copy import deepcopy
from datetime import datetime, timezone
import platform
import secrets
import warnings

from data_operations import _append_columns, unique_name
from distributions import frozen_distribution
from inference import scientific_stats
from random_contract import (RANDOM_METHOD, RANDOM_DISTRIBUTIONS, DISCRETE,
                             validate_random_parameters, validate_random_capacity, validate_random_result)
from updates import load_metadata
from workspace_model import identifier, fingerprint
from background_tasks import TaskContext

RANDOM_CHUNK_SIZE = 4096


def format_random(result):
    p = result['parameters']
    labels = RANDOM_DISTRIBUTIONS[p['distribution']]
    original = result['provenance']['generation']
    replay = result['provenance']['execution'] == 'replay_saved_values'
    lines = ['DADOS ALEATÓRIOS — ' + p['distribution'], '',
             'Parâmetros: ' + '; '.join(f'{label}={p["distribution_parameters"][key]}' for key, label, _ in labels),
             f"Linhas por coluna: {p['row_count']}; colunas: {p['column_count']}",
             'Semente: ' + str(p['seed']),
             f"Gerador original: PCG64; NumPy {original['numpy']}; SciPy {original['scipy']}",
             'Valores salvos reproduzidos, sem novo sorteio.' if replay else 'Valores gerados em novas colunas. Ctrl+Z desfaz a inclusão.',
             'A semente é aplicada a cada geração; o histórico conserva os valores exatos.']
    return '\n'.join(lines) + '\n'


def prepare_random(sheet, distribution, distribution_parameters, row_count=100, column_count=1,
                   seed=None, base_name='Aleatorio'):
    """Captura só opções e identidade: o sorteio não lê células da interface."""
    if sheet['fingerprint'] != fingerprint(sheet):
        raise ValueError('Sincronize a planilha antes de gerar dados.')
    p = dict(distribution=distribution, distribution_parameters=deepcopy(distribution_parameters),
             row_count=row_count, column_count=column_count, seed=0 if seed is None else seed,
             base_name=base_name.strip() if isinstance(base_name, str) else base_name)
    validate_random_parameters(p)
    validate_random_capacity([c['name'] for c in sheet['columns']], sheet['rows'], p)
    if seed is None:
        p['seed'] = secrets.randbits(128)
    return dict(parameters=p, source=dict(worksheet_id=sheet['id'], column_ids=[], revision=sheet['revision'],
                                         fingerprint=sheet['fingerprint'], kind='fixed_generation'))


def generate_random(request, context=None):
    context = context or TaskContext()
    context.report(0., 'Preparando motor estatístico…')
    p = deepcopy(request['parameters'])
    validate_random_parameters(p)
    distribution = p['distribution']
    row_count, column_count = p['row_count'], p['column_count']
    scientific_stats()
    import numpy as np
    import scipy
    rng = np.random.Generator(np.random.PCG64(p['seed']))
    context.checkpoint()
    if distribution not in ('Inteiros', 'Bernoulli'):
        dist, _, _ = frozen_distribution(distribution, p['distribution_parameters'])
    columns = []
    total = row_count * column_count
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error', RuntimeWarning)
            for column_index in range(column_count):
                column = []
                for offset in range(0, row_count, RANDOM_CHUNK_SIZE):
                    context.checkpoint()
                    size = min(RANDOM_CHUNK_SIZE, row_count - offset)
                    if distribution == 'Inteiros':
                        bounds = p['distribution_parameters']
                        sample = rng.integers(int(bounds['lower']), int(bounds['upper']) + 1, size=size)
                    elif distribution == 'Bernoulli':
                        sample = rng.binomial(1, p['distribution_parameters']['p'], size=size)
                    else:
                        sample = dist.rvs(size=size, random_state=rng)
                    if sample.shape != (size,) or not np.all(np.isfinite(sample)):
                        raise ValueError('O sorteio excede a precisão suportada; ajuste os parâmetros.')
                    column.extend(sample.tolist())
                    count = column_index * row_count + len(column)
                    context.report(count / total, f'Gerando coluna {column_index + 1} de {column_count}: {count} de {total} valores')
                columns.append(column)
    except (ValueError, ArithmeticError, RuntimeWarning) as error:
        raise ValueError('Não foi possível gerar valores finitos com estes parâmetros. ' + str(error)) from error
    version = load_metadata()['version']
    result = dict(analysis_id=identifier('analysis'), parent_analysis_id=None, method_id=RANDOM_METHOD,
                  created_at=datetime.now(timezone.utc).isoformat(), parameters=p,
                  source=deepcopy(request['source']),
                  versions=dict(application=version, method=1, python=platform.python_version(),
                                numpy=np.__version__, scipy=scipy.__version__),
                  missing=dict(policy='generated_no_missing'), values=dict(columns=columns, discrete=distribution in DISCRETE),
                  tables=[], warnings=['Validação diferencial Minitab 16 pendente; sequência aleatória própria do MiniTaBom.'],
                  status='completed', provenance=dict(origin='MiniTaBom', reference16='pending', execution='generate',
                      generation=dict(engine='PCG64', layout='columns_then_rows', chunk_size=RANDOM_CHUNK_SIZE, application=version,
                                      python=platform.python_version(), numpy=np.__version__, scipy=scipy.__version__)))
    result['report'] = format_random(result)
    validate_random_result(result)
    context.checkpoint()
    return result


def execute_random(sheet, distribution, distribution_parameters, row_count=100, column_count=1,
                   seed=None, base_name='Aleatorio', context=None):
    context = context or TaskContext()
    context.checkpoint()
    request = prepare_random(sheet, distribution, distribution_parameters, row_count, column_count, seed, base_name)
    return generate_random(request, context)


def random_columns(headers, rows, result, context=None):
    context = context or TaskContext()
    context.report(0., 'Preparando as colunas de destino…')
    validate_random_result(result)
    p = result['parameters']
    validate_random_capacity(headers, rows, p)
    names, used = [], set(headers)
    for i in range(p['column_count']):
        proposed = p['base_name'] if p['column_count'] == 1 else f"{p['base_name']} {i + 1}"
        name = unique_name(proposed, used)
        names.append(name)
        used.add(name)
    columns = []
    for index, col in enumerate(result['values']['columns']):
        text = []
        for offset in range(0, len(col), RANDOM_CHUNK_SIZE):
            context.checkpoint()
            text.extend(str(value) for value in col[offset:offset + RANDOM_CHUNK_SIZE])
        columns.append(text)
        context.report(.5 * (index + 1) / len(names), 'Preparando coluna ' + names[index])
    new_headers, new_rows = _append_columns(headers, rows, names, columns, context.phase(.5, 1.))
    return new_headers, new_rows, names


def replay_random(document, result):
    validate_random_result(result)
    sheet = next((s for s in document['worksheets'] if s['id'] == result['source']['worksheet_id']), None)
    if sheet is None:
        raise ValueError('Planilha de destino não encontrada.')
    validate_random_capacity([c['name'] for c in sheet['columns']], sheet['rows'], result['parameters'])
    replay = deepcopy(result)
    replay.pop('storage', None)
    replay.update(analysis_id=identifier('analysis'), parent_analysis_id=result['analysis_id'],
                  created_at=datetime.now(timezone.utc).isoformat())
    replay['versions']['application'] = load_metadata()['version']
    replay['source'].update(revision=sheet['revision'], fingerprint=sheet['fingerprint'])
    replay['provenance'].update(execution='replay_saved_values', replay_of=result['analysis_id'])
    replay['report'] = format_random(replay)
    validate_random_result(replay)
    return replay
