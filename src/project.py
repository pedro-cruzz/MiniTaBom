"""Formato de projeto próprio do MiniTaBom; não é um arquivo MPJ/MTW."""
import json
import os
from pathlib import Path
import tempfile


def validate_project(data):
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
    try:
        data = json.loads(Path(path).read_text(encoding='utf-8-sig'))
    except (json.JSONDecodeError, UnicodeError) as error:
        raise ValueError('Arquivo de projeto inválido.') from error
    return validate_project(data)


def save_project(path, headers, rows, output):
    data = dict(format='statlab', version=1, headers=headers, rows=rows, output=output)
    validate_project(data)
    target = Path(path)
    # Grava ao lado do destino e substitui só depois da escrita completa.
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8',
                dir=target.parent, prefix='.statlab-', suffix='.tmp', delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(data, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
