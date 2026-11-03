"""Gera e verifica um ZIP portátil Windows x64; não publica arquivos."""
from datetime import datetime
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    if sys.platform != 'win32' or platform.machine().lower() not in ('amd64', 'x86_64'):
        raise SystemExit('Gere este pacote no Windows x64 com Python x64.')
    os.chdir(ROOT)
    for directory in (ROOT / '.deps', ROOT / '.build-tools'):
        if directory.is_dir():
            sys.path.insert(0, str(directory))
    try:
        import PyInstaller.__main__
        import numpy
        import scipy
    except ImportError as error:
        raise SystemExit('Instale requirements-build.txt antes de gerar o pacote: ' + str(error))
    stamp = datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    build = ROOT / '.build' / stamp
    build.mkdir(parents=True)
    os.environ['PYINSTALLER_CONFIG_DIR'] = str(build / 'cache')
    # Diretório próprio por compilação: nenhuma limpeza de arquivos anteriores.
    output = build / 'output'
    args = [str(ROOT / 'app.py'), '--name', 'MiniTaBom', '--windowed', '--onedir',
            '--noupx', '--distpath', str(output), '--workpath', str(build / 'work'),
            '--specpath', str(build), '--paths', str(ROOT),
            '--hidden-import', 'scipy.stats', '--hidden-import', 'numpy',
            '--exclude-module', 'pytest', '--exclude-module', 'scipy.tests',
            '--exclude-module', 'numpy.tests',
            '--add-data', str(ROOT / 'INVENTARIO_FUNCIONAL.json') + os.pathsep + '.',
            '--log-level', 'WARN']
    for scientific_path in dict.fromkeys(str(Path(package.__file__).resolve().parent.parent)
                                         for package in (numpy, scipy)):
        args += ['--paths', scientific_path]
    PyInstaller.__main__.run(args)
    bundle = output / 'MiniTaBom'
    examples = bundle / 'Exemplos'
    examples.mkdir()
    for example in sorted(ROOT.glob('exemplo_*.statlab')):
        shutil.copy2(example, examples / example.name)
    (bundle / 'LEIA-ME.txt').write_text(
        'MiniTaBom - projeto independente para fins educativos e estudo de estatística.\n\n'
        '1. Extraia a pasta MiniTaBom inteira para uma pasta do seu computador.\n'
        '2. Abra MiniTaBom.exe. Não precisa instalar Python ou Minitab.\n'
        '3. Em Arquivo > Abrir projeto, escolha um arquivo da pasta Exemplos.\n\n'
        'Mantenha a pasta _internal junto do executável. Ela contém as dependências.\n'
        'Os projetos podem ser salvos em qualquer pasta com permissão de escrita.\n'
        'Sem vínculo, patrocínio ou endosso da Minitab.\n'
        'Compatibilidade integral com Minitab 16 ainda não validada.\n', encoding='utf-8')
    licenses = bundle / 'Licencas'
    licenses.mkdir()
    # Preserva as licenças fornecidas pelos pacotes científicos distribuídos.
    for name in ('numpy', 'scipy', 'pyinstaller'):
        distribution = importlib.metadata.distribution(name)
        for entry in distribution.files or []:
            if any(part.lower().startswith(('license', 'copying', 'notice')) for part in entry.parts):
                source = Path(distribution.locate_file(entry))
                if source.is_file():
                    target = licenses / name / Path(*entry.parts)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, target)
    python_license = Path(sys.base_prefix) / 'LICENSE.txt'
    if python_license.is_file():
        shutil.copy2(python_license, licenses / 'Python-LICENSE.txt')
    manifest = dict(name='MiniTaBom', platform='Windows x64', python=platform.python_version(),
                    numpy=numpy.__version__, scipy=scipy.__version__,
                    pyinstaller=importlib.metadata.version('pyinstaller'),
                    purpose='Fins educativos e estudo de estatística',
                    built_at=datetime.now().astimezone().isoformat())
    (bundle / 'versao.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    report_path = build / 'smoke-test.json'
    # Retira os caminhos do ambiente de desenvolvimento antes de abrir o pacote.
    env = {k: v for k, v in os.environ.items() if k not in ('PYTHONPATH', 'PYTHONHOME')}
    completed = subprocess.run([str(bundle / 'MiniTaBom.exe'), '--smoke-test', str(report_path)],
                               cwd=build, env=env, timeout=120, check=False)
    report = json.loads(report_path.read_text(encoding='utf-8')) if report_path.exists() else {}
    if completed.returncode != 0 or not report.get('ok') or not report.get('frozen'):
        raise SystemExit('Pacote reprovado no teste: ' + json.dumps(report, ensure_ascii=True))
    print('Teste do executável aprovado: ' + ', '.join(report['checks']), flush=True)
    dist = ROOT / 'dist'
    dist.mkdir(exist_ok=True)
    archive = dist / 'MiniTaBom-Windows-x64.zip'
    # Só distribui os arquivos desta compilação, sem material da instalação Minitab.
    temporary = build / archive.name
    with zipfile.ZipFile(temporary, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as stream:
        for path in sorted(bundle.rglob('*')):
            if path.is_file():
                stream.write(path, path.relative_to(output))
    shutil.copy2(temporary, archive)
    with archive.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    checksum = archive.with_suffix('.zip.sha256')
    checksum.write_text(f'{digest}  {archive.name}\n', encoding='ascii')
    shutil.copy2(report_path, dist / 'smoke-test.json')
    print(f'Pacote: {archive}\nTamanho: {archive.stat().st_size / 1024**2:.1f} MB\nSHA256: {digest}', flush=True)


if __name__ == '__main__':
    main()
