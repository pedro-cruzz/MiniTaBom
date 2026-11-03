"""Consulta manual de Releases públicas; não baixa nem instala executáveis."""
import json
import os
from pathlib import Path
import re
import socket
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit
from urllib.request import Request, urlopen
from app_resources import resource_path

METADATA_PATH = resource_path('app_metadata.json')


def normalize_repository(value):
    text = value.strip().rstrip('/')
    if text.startswith('https://'):
        parsed = urlsplit(text)
        if parsed.netloc.lower() != 'github.com' or parsed.query or parsed.fragment:
            raise ValueError('Informe o link do repositório em https://github.com/usuario/repositorio.')
        text = parsed.path.strip('/')
    if text.endswith('.git'):
        text = text[:-4]
    if not re.fullmatch(r'[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})/[A-Za-z0-9_.-]{1,100}', text):
        raise ValueError('Informe usuario/repositorio ou o link completo do repositório no GitHub.')
    if text.split('/')[1] in ('.', '..'):
        raise ValueError('Nome de repositório inválido.')
    return text


def version_key(version):
    match = re.fullmatch(r'[vV]?(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)'
                         r'(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?'
                         r'(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?', version)
    if not match:
        raise ValueError('Use versões no formato v0.1.0, v0.2.0 etc. na tag da Release.')
    major, minor, patch, pre, _ = match.groups()
    identifiers = []
    for item in pre.split('.') if pre else []:
        if item.isdigit() and len(item) > 1 and item.startswith('0'):
            raise ValueError('Identificador numérico de pré-versão inválido.')
        identifiers.append((0, int(item)) if item.isdigit() else (1, item))
    return (int(major), int(minor), int(patch), 1 if pre is None else 0, tuple(identifiers))


def load_metadata():
    data = json.loads(METADATA_PATH.read_text(encoding='utf-8'))
    version_key(data['version'])
    return data


def preferences_path():
    base = Path(os.environ['APPDATA']) if os.environ.get('APPDATA') else Path.home() / '.config'
    return base / 'MiniTaBom' / 'updates.json'


def configured_repository():
    path = preferences_path()
    if path.exists():
        return normalize_repository(json.loads(path.read_text(encoding='utf-8'))['repository'])
    bundled = load_metadata().get('repository', '')
    return normalize_repository(bundled) if bundled else ''


def save_repository(repository):
    repository = normalize_repository(repository)
    path = preferences_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(repository=repository), ensure_ascii=False, indent=2), encoding='utf-8')
    return repository


def check_latest(repository, current_version):
    repository = normalize_repository(repository)
    current = version_key(current_version)
    request = Request(f'https://api.github.com/repos/{repository}/releases/latest',
                      headers={'Accept': 'application/vnd.github+json',
                               'User-Agent': f'MiniTaBom/{current_version}',
                               'X-GitHub-Api-Version': '2026-03-10'})
    try:
        with urlopen(request, timeout=10) as response:
            raw = response.read(512 * 1024 + 1)
        if len(raw) > 512 * 1024:
            raise ValueError('A resposta do GitHub excedeu o tamanho esperado.')
        release = json.loads(raw)
    except HTTPError as error:
        if error.code == 404:
            raise ValueError('Repositório não encontrado ou ainda sem uma Release estável pública. Confira o endereço.') from error
        if error.code in (403, 429):
            raise ValueError('O GitHub limitou as consultas. Tente novamente mais tarde.') from error
        raise ValueError(f'O GitHub retornou erro HTTP {error.code}. Tente novamente mais tarde.') from error
    except (URLError, TimeoutError, socket.timeout, OSError) as error:
        raise ValueError('Não foi possível acessar o GitHub. Confira a internet e tente novamente.') from error
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise ValueError('O GitHub retornou uma resposta inválida.') from error
    if not isinstance(release, dict) or not isinstance(release.get('tag_name'), str):
        raise ValueError('Não foi possível identificar a versão publicada no GitHub.')
    if release.get('draft') or release.get('prerelease'):
        raise ValueError('Não há uma Release estável disponível nesta resposta.')
    tag = release['tag_name']
    latest = version_key(tag)
    return dict(current=current_version, latest=tag, newer=latest > current,
                url=f'https://github.com/{repository}/releases/tag/{quote(tag, safe="")}',
                repository=repository)
