"""Formato de projeto próprio do MiniTaBom; não é um arquivo MPJ/MTW."""
import json
import os
from pathlib import Path
import tempfile
from copy import deepcopy
from workspace_model import new_document, validate_document, active_sheet

MAX_PROJECT_BYTES=256*1024*1024


def validate_project(data):
    if isinstance(data, dict) and type(data.get('version')) is int and data['version'] == 2:
        validate_document(data)
        sheet = active_sheet(data)
        return [c['name'] for c in sheet['columns']], sheet['rows'], data['output']
    if not isinstance(data, dict) or data.get('format') != 'statlab' or type(data.get('version')) is not int or data['version'] != 1:
        raise ValueError('Formato ou versão de projeto não suportado.')
    headers, rows, output = data.get('headers'), data.get('rows'), data.get('output')
    if (not isinstance(headers, list) or not headers
            or any(not isinstance(h, str) or not h.strip() for h in headers)
            or len(set(headers)) != len(headers)):
        raise ValueError('Cabeçalhos devem ser únicos e não vazios.')
    if (not isinstance(rows, list) or any(not isinstance(row, list)
            or len(row) != len(headers) or any(not isinstance(v, str) for v in row)
            for row in rows)):
        raise ValueError('Dados de projeto inválidos.')
    if not isinstance(output, str):
        raise ValueError('Resultados de projeto inválidos.')
    return headers, rows, output


def load_project(path):
    document = load_document(path)
    sheet = active_sheet(document)
    return [c['name'] for c in sheet['columns']], sheet['rows'], document['output']


def load_document(path):
    try:
        if Path(path).stat().st_size > MAX_PROJECT_BYTES:
            raise ValueError('Projeto excede o limite de leitura de 256 MiB.')
        data = json.loads(Path(path).read_text(encoding='utf-8-sig'),
                          parse_constant=_invalid_constant, object_pairs_hook=_unique_keys)
    except (json.JSONDecodeError, UnicodeError, RecursionError) as error:
        raise ValueError('Arquivo de projeto inválido.') from error
    if isinstance(data, dict) and type(data.get('version')) is int and data['version'] == 1:
        headers, rows, output = validate_project(data)
        migrated = new_document(headers, rows, output)
        migrated['metadata']['migration'] = dict(from_version=1, source_format='statlab',
                                                note='Sessão textual preservada; parâmetros antigos não são inferidos.')
        return migrated
    validate_document(data)
    return data


def _invalid_constant(value):
    raise ValueError('Número JSON inválido: ' + value)


def _unique_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Chave repetida no projeto: ' + key)
        result[key] = value
    return result


def save_project(path, headers, rows, output):
    """Adaptador legado para ferramentas que escrevem explicitamente statlab v1."""
    data = dict(format='statlab', version=1, headers=headers, rows=rows, output=output)
    validate_project(data)
    _atomic_save(path, data)


def save_document(path, document):
    data = deepcopy(document)
    validate_document(data)
    _atomic_save(path, data)


def _atomic_save(path, data):
    target = Path(path)
    # Grava ao lado do destino e substitui só depois da escrita completa.
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8',
                dir=target.parent, prefix='.statlab-', suffix='.tmp', delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(data, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.flush()
            if os.fstat(stream.fileno()).st_size>MAX_PROJECT_BYTES:
                raise ValueError('Projeto excede o limite de gravação de 256 MiB.')
            os.fsync(stream.fileno())
        os.replace(temporary, target)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
