"""Inventário estático: lê a instalação, sem carregar DLLs ou executar JavaScript.

Os relatórios contêm metadados e referências de interface, não cópias dos
executáveis, imagens ou algoritmos estatísticos do produto.
"""
from __future__ import annotations

import argparse
import ast
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import struct
import zipfile
import xml.etree.ElementTree as ET


PROJECT = Path(__file__).resolve().parents[1]
MAX_MEMBER = 64 * 1024 * 1024
MAX_ARCHIVE = 128 * 1024 * 1024


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def save_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def flatten(value, prefix=''):
    if isinstance(value, dict):
        for key, child in value.items():
            yield from flatten(child, f'{prefix}.{key}' if prefix else key)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from flatten(child, f'{prefix}[{index}]')
    elif isinstance(value, str):
        yield prefix, value


def js_string_end(text, start):
    """Localiza a aspa final sem interpretar nem executar o pacote."""
    quote = text[start]
    if quote not in ('\"', "'"):
        raise ValueError('JSON.parse sem literal de string.')
    cursor = start + 1
    while cursor < len(text):
        if text[cursor] == '\\':
            cursor += 2
        elif text[cursor] == quote:
            return cursor + 1
        else:
            cursor += 1
    raise ValueError('String não terminada no pacote.')


def archive_inventory(path):
    with zipfile.ZipFile(path) as archive:
        infos = archive.infolist()
        files = [entry for entry in infos if not entry.is_dir()]
        total = sum(entry.file_size for entry in files)
        if total > MAX_ARCHIVE or any(entry.file_size > MAX_MEMBER for entry in files):
            raise ValueError(f'Pacote excede o limite de inspeção: {path.name}')
        return dict(
            arquivo=path.name, sha256=sha256(path), entradas=len(infos),
            arquivos=len(files), bytes_descompactados=total,
            extensoes=dict(sorted(Counter(Path(i.filename).suffix.lower() for i in files).items())),
            membros=[dict(caminho=i.filename, bytes=i.file_size,
                          bytes_comprimidos=i.compress_size, crc32=f'{i.CRC:08x}') for i in files],
        )


def dialog_catalog(path):
    # O mapa de recursos relaciona ./pt-BR/*.json com IDs de módulos Webpack.
    # Os módulos de tradução exportam JSON.parse('...'). Somente literais são
    # lidos com ast.literal_eval e json.loads; nenhum código do pacote é executado.
    mapping = {}
    scripts = []
    with zipfile.ZipFile(path) as archive:
        for info in archive.infolist():
            # Chunks podem incorporar outros aplicativos com seus próprios
            # IDs Webpack. Não misturar os mapas desses espaços de módulos.
            if Path(info.filename).name.startswith('main.') and info.filename.endswith('.js'):
                text = archive.read(info).decode('utf-8')
                scripts.append((info.filename, text))
                for name, module_id in re.findall(r'"(\./pt-BR/[^"\n]+\.json)":(\d+)', text):
                    if name in mapping and mapping[name] != module_id:
                        raise ValueError(f'Mapeamento ambíguo: {name}')
                    mapping[name] = module_id
    if len(scripts) != 1 or not mapping:
        raise ValueError('Não foi encontrado um único pacote principal com mapa pt-BR.')
    wanted = set(mapping.values())
    modules = {}
    for name, text in scripts:
        for match in re.finditer(r'JSON\.parse\(', text):
            prefix = text[max(0, match.start() - 150):match.start()]
            module = re.search(r'(\d+)\([^)]*\)\{[^{}]{0,100}\.exports=$', prefix)
            if module is None or module[1] not in wanted:
                continue
            start = match.end()
            end = js_string_end(text, start)
            value = json.loads(ast.literal_eval(text[start:end]))
            if not isinstance(value, dict):
                raise ValueError(f'Tradução não é objeto: {name}, módulo {module[1]}')
            strings = list(flatten(value))
            titles = {key: label for key, label in strings
                      if any(word in key.lower() for word in ('title', 'header'))}
            entry = dict(modulo=module[1], membro=name, offset_caracteres=start,
                         numero_textos=len(strings), titulos=titles,
                         chaves=[key for key, _ in strings])
            if module[1] in modules and modules[module[1]] != entry:
                raise ValueError(f'Módulo duplicado divergente: {module[1]}')
            modules[module[1]] = entry
    missing = [name for name, module_id in mapping.items() if module_id not in modules]
    return dict(
        fonte=path.name, sha256=sha256(path), idioma='pt-BR',
        metodo='Mapa de módulos e JSON estático; amostras de títulos e chaves, sem executar JS',
        observacao='Recursos de tradução incluem componentes compartilhados, galerias e funções antigas. Não são uma contagem de funções ou prova de disponibilidade no menu.',
        recursos_mapeados=len(mapping), recursos_lidos=len(mapping) - len(missing),
        nao_lidos=missing,
        recursos=[dict(recurso=name, **modules[module_id]) for name, module_id in sorted(mapping.items())
                  if module_id in modules],
    )


def legacy_catalog(directory):
    data = (directory / 'mtb.dlg').read_bytes()
    index_data = (directory / 'mtb.inx').read_bytes()
    if len(index_data) % 4:
        raise ValueError('Índice de diálogos fora do alinhamento observado.')
    index = struct.unpack('<' + 'i' * (len(index_data) // 4), index_data)
    if index[0] != len(index) - 1:
        raise ValueError('Contagem inicial do índice diverge do tamanho do arquivo.')
    slots = defaultdict(list)
    unresolved = []
    for slot, offset in enumerate(index[1:]):
        if offset != -1:
            if not 0 <= offset < len(data):
                unresolved.append(dict(slot_base_zero=slot, valor_bruto=offset))
            else:
                slots[offset].append(slot)
    # Verificação empírica desta versão: primeiro uint32 de cada bloco é seu
    # tamanho; percorrer esses comprimentos deve cobrir o arquivo e o índice.
    records = []
    cursor = 0
    while cursor < len(data):
        size = struct.unpack_from('<I', data, cursor)[0]
        if size < 4 or cursor + size > len(data):
            raise ValueError('Tamanho de bloco inválido; layout não reconhecido.')
        strings = [(cursor + m.start(), m.group().decode('utf-16le'))
                   for m in re.finditer(rb'(?:[\x20-\xff]\x00){4,}', data[cursor:cursor + size])]
        records.append(dict(offset=cursor, bytes=size, slots_indice_base_zero=slots.get(cursor, []),
                            numero_sequencias_textuais=len(strings),
                            amostra=[dict(offset=offset, texto=text) for offset, text in strings[:8]]))
        cursor += size
    offsets = {r['offset'] for r in records}
    return dict(
        fonte=str(directory), sha256_dlg=sha256(directory / 'mtb.dlg'),
        sha256_inx=sha256(directory / 'mtb.inx'), entradas_indice=index[0],
        blocos=len(records), bytes_cobertos=cursor,
        entradas_indice_nao_resolvidas=unresolved,
        offsets_indice_sem_bloco=sorted(set(slots) - offsets),
        blocos_sem_entrada_direta=sorted(offsets - set(slots)),
        metodo='Offsets int32 e comprimentos uint32 observados e cruzados nesta instalação',
        observacao='Blocos podem incluir subdiálogos. Sequências UTF-16LE são heurísticas, não análise completa de campos, hierarquia, tipos ou padrões; amostras podem começar por valores padrão.',
        registros=records,
    )


def graph_catalog(path):
    records = []
    with zipfile.ZipFile(path) as archive:
        for name in archive.namelist():
            if name.startswith('locales/pt-BR/') and name.endswith('.json'):
                strings = list(flatten(json.loads(archive.read(name))))
                records.append(dict(membro=name, numero_textos=len(strings),
                                    nomes_graficos={k: v for k, v in strings if k.endswith('GraphName')},
                                    chaves=[k for k, _ in strings]))
    return dict(fonte=path.name, sha256=sha256(path), idioma='pt-BR', recursos=records,
                observacao='Catálogo de textos de componentes gráficos; não lista exaustiva do menu Gráfico.')


def inventory(root):
    files = sorted(p for p in root.rglob('*') if p.is_file())
    swid = next(root.glob('*.swidtag'))
    software = ET.parse(swid).getroot()
    product = software.get('name') or software.findtext('{*}product_title')
    version = software.get('version') or software.findtext('{*}product_version/{*}name')
    if not product or not version:
        raise ValueError('Produto/versão não identificados no SWID da instalação.')
    archives = [archive_inventory(p) for p in sorted(root.glob('*.data'))]
    known = {'Mtb.exe', 'MtbCore.dll', 'MtbDlg.dll', 'MtbObjectiveGrid.dll'}
    return dict(
        formato='statlab-inspecao-instalacao', versao=1,
        data_utc=datetime.now(timezone.utc).isoformat(), raiz=str(root),
        operacao='Leitura estática; nenhum arquivo da instalação foi alterado ou executado',
        produto=product, versao_produto=version, fonte_versao=swid.name,
        arquivos=len(files), bytes=sum(p.stat().st_size for p in files),
        extensoes=dict(sorted(Counter(p.suffix.lower() for p in files).items())),
        inventario=[dict(caminho=p.relative_to(root).as_posix(), bytes=p.stat().st_size,
                         **({'sha256': sha256(p)} if p.name in known else {})) for p in files],
        pacotes=archives,
        dados_e_ajuda_locais=[p.relative_to(root).as_posix() for p in files
                             if p.suffix.lower() in ('.mtw', '.mpj', '.mwx', '.mpx', '.pdf', '.chm')],
        limites=['Não recupera o código-fonte completo ou os algoritmos dos binários.',
                 'Recursos presentes não provam que um comando está disponível na interface ou na licença.',
                 'Esta é a instalação 22; não valida presença, padrões ou resultados na versão 16.',
                 'A busca de arquivos de dados/ajuda abrange somente a raiz indicada.'],
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path('C:/Program Files/Minitab/Minitab 22'))
    parser.add_argument('--output', type=Path, default=PROJECT / 'analise_instalacao')
    args = parser.parse_args()
    root, output = args.root.resolve(), args.output.resolve()
    if not output.is_relative_to(PROJECT) or output.is_relative_to(root):
        raise ValueError('Os relatórios devem ficar no projeto, fora da pasta de instalação.')
    result = inventory(root)
    dialogs = dialog_catalog(root / 'Dialogs.data')
    legacy = legacy_catalog(root / 'Resources' / '1046')
    graphs = graph_catalog(root / 'mss-graphs.data')
    output.mkdir(parents=True, exist_ok=True)
    for filename, value in [('inventario_instalacao.json', result), ('dialogos_pt_br.json', dialogs),
                            ('dialogos_legados_pt_br.json', legacy), ('graficos_pt_br.json', graphs)]:
        save_json(output / filename, value)
    print(json.dumps(dict(arquivos=result['arquivos'], bytes=result['bytes'],
                          versao=result['versao_produto'], recursos_pt_br=dialogs['recursos_mapeados'],
                          lidos=dialogs['recursos_lidos'], nao_lidos=dialogs['nao_lidos'],
                          blocos_legados=legacy['blocos'], recursos_graficos=len(graphs['recursos']),
                          destino=str(output)), ensure_ascii=True, indent=2))


if __name__ == '__main__':
    main()
