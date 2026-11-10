"""Importação única do relatório autorizado; não executa código do ZIP.

A ajuda do fabricante permanece no ZIP/cache local e não é redistribuída.
O registro criado é mantido diretamente, sem IDs derivados de descrições.
"""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('archive', type=Path)
    args = parser.parse_args()
    target = ROOT / 'CAPACIDADES.json'
    if target.exists():
        raise SystemExit('Registro existente: atualize-o preservando os IDs; não repetir bootstrap.')
    with zipfile.ZipFile(args.archive) as archive:
        prefix = 'Analise_MiniTaBom_2026-11-05/'
        read = lambda name: json.loads(archive.read(prefix + name).decode('utf-8-sig'))
        checksums = read('checksums.json')
        for name, digest in checksums.items():
            if hashlib.sha256(archive.read(prefix + name)).hexdigest() != digest:
                raise ValueError('Checksum da auditoria diverge: ' + name)
        matrix, help_index, code_index = map(read, ('matriz_lacunas.json', 'indice_ajuda.json', 'indice_codigo.json'))
        topics = archive.read(prefix + 'catalogo_topicos_16.csv')
    legacy = json.loads((ROOT/'docs/analise_instalacao/cobertura_minitab16.json').read_text(encoding='utf-8'))
    requirements = []
    for row in matrix:
        requirements.append(dict(
            id='audit.' + row['id'], kind='work_package', area=row['area'], name=row['recurso'],
            menu_command16=None, options_defaults={},
            evidence16=[dict(source='audit:2026-11-05', locator=row['ajuda'], status='documentary_pointer_not_runtime_confirmation')],
            states=dict(specification='partial', implementation='partial' if row['estado']=='Parcial' else 'pending',
                        ui='partial' if row['estado']=='Parcial' else 'pending', validation16='pending', persistence='to_audit'),
            dependencies=[], files=[p.strip() for p in row['codigo'].split(';')], tests=[],
            limitations=[row['falta']], acceptance=row['aceite'], priority=row['prioridade'],
            provenance=[dict(source='matriz_lacunas.json', legacy_id=row['id'], original=row)]))

    def atomic(key, area, name, parent, files, tests, state='implemented', persisted=False, topic=None, options=None):
        evidence = [dict(source='audit:2026-11-05', locator=i['caminho'], sha256=None,
                         status='documented_in_extracted_help_not_executed') for i in help_index
                    if topic and topic in i['caminho']][:3]
        requirements.append(dict(id=key, kind='requirement', parent_id='audit.'+parent, area=area, name=name,
            menu_command16='Stat > Basic Statistics > 1-Sample t' if key=='basic.t.one.column' else None,
            options_defaults=options or {}, evidence16=evidence,
            states=dict(specification='partial', implementation=state, ui=state,
                        validation16='pending', persistence='implemented' if persisted else 'pending'),
            dependencies=[], files=files, tests=tests,
            limitations=['Sem execução diferencial no Minitab 16 neste computador.',
                         'Este requisito não encerra o pacote de trabalho nem suas demais opções.'],
            priority='P0' if area=='Plataforma' else 'P1', provenance=[dict(source='code_audit:2026-11-06')]))

    atomic('platform.project.v2','Plataforma','Projeto v2 com migração explícita de v1','GAP-002',
           ['src/project.py','src/workspace_model.py'],['tests/test_workspace_v2.py'],persisted=True)
    atomic('platform.worksheets.collection','Plataforma','Criar e alternar planilhas com IDs','GAP-001',
           ['src/app.py','src/workspace_model.py'],['tests/test_workspace_v2.py'],persisted=True,topic='/WorksheetsCollection/')
    atomic('platform.columns.identity','Plataforma','IDs de coluna, revisão e fingerprint','GAP-006',
           ['src/workspace_model.py'],['tests/test_workspace_v2.py'],persisted=True)
    atomic('platform.analysis.result','Plataforma','Resultado estruturado de t de uma amostra','GAP-002',
           ['src/analysis_service.py'],['tests/test_workspace_v2.py'],persisted=True)
    atomic('platform.analysis.rerun','Plataforma','Salvar/reabrir/reexecutar t de uma amostra','GAP-003',
           ['src/analysis_service.py','src/analysis_history_dialog.py'],['tests/test_workspace_v2.py'],persisted=True)
    atomic('basic.t.one.column','Inferência','t de uma amostra em coluna','GAP-021',
           ['src/inference.py','src/analysis_service.py'],['tests/test_inference.py','tests/test_workspace_v2.py'],
           persisted=True,topic='/ST_Basic_Statistics/1_Sample_t/',options=dict(confidence=95,alternative='two-sided',null=0,perform_test=True))
    for key,name,parent,files,tests,topic in [
        ('basic.t.summary','t com estatísticas resumidas','GAP-021',['src/inference.py'],['tests/test_inference.py'],'/1_Sample_t/'),
        ('basic.t.stacked','t de duas amostras empilhadas','GAP-021',['src/inference.py'],['tests/test_inference.py'],'/2_Sample_t/'),
        ('basic.poisson.one','Taxa de Poisson de uma amostra','GAP-023',['src/poisson_inference.py'],['tests/test_poisson_inference.py'],'/1_Sample_Poisson_Rate/'),
        ('basic.normality.rj','Normalidade Ryan–Joiner','GAP-025',['src/normality.py'],['tests/test_material_features.py'],'/Normality_Test/'),
        ('basic.normality.ks','KS com normal estimada','GAP-025',['src/normality.py'],['tests/test_material_features.py'],'/Normality_Test/'),
        ('basic.normality.plot','Gráfico de probabilidade normal','GAP-025',['src/probability_graph.py'],['tests/test_material_features.py'],'/Normality_Test/'),
        ('basic.variances.groups','Levene/Bartlett com vários grupos','GAP-024',['src/study_tests.py'],['tests/test_material_features.py'],'/Test_for_Equal_Variances/'),
        ('descriptive.frequency.cumulative','Frequências relativas e acumuladas','GAP-020',['src/study_descriptives.py'],['tests/test_material_features.py'],None),
        ('regression.store.diagnostics','Armazenar ajustados e resíduos','GAP-031',['src/column_calculator.py'],['tests/test_material_features.py'],None),
    ]:
        area='Descritivas' if key.startswith('descriptive') else 'Regressão' if key.startswith('regression') else 'Inferência'
        atomic(key,area,name,parent,files,tests,topic=topic)
    atomic('basic.poisson.two','Inferência','Duas taxas de Poisson','GAP-023',[],[],state='pending',topic='/2_Sample_Poisson_Rate/')
    # Ponte histórica: os IDs antigos ficam preservados, não são funções novas.
    result=dict(format='minitabom-capability-registry',version=1,updated='2026-11-06',target='Minitab 16.2.4.0 / English 1033',
                inventory_exhaustive=False,parity_validated=False,requirements=requirements,
                sources=[dict(id='audit:2026-11-05',archive=args.archive.name,
                              sha256=hashlib.sha256(args.archive.read_bytes()).hexdigest(),checksums=checksums,
                              help_pages=len(help_index),code_modules=len(code_index),
                              topic_catalog_sha256=hashlib.sha256(topics).hexdigest(),
                              reference_runtime_available_here=False)],
                historical_scope=dict(source='INVENTARIO_FUNCIONAL.json',areas=legacy['areas']),
                legacy_requirements=legacy['requisitos'],
                policy=['IDs permanentes independentes de descrições; decompor pacotes em requisitos atômicos.',
                        'Implementação, interface, persistência e validação16 são estados independentes.',
                        'Tópicos de ajuda são evidência documental; acesso/edição/licença devem ser conferidos em execução.',
                        'Sem porcentagem por arquivos, tópicos ou pacotes; 22 fica em backlog separado.'])
    if len({r['id'] for r in requirements}) != len(requirements):
        raise ValueError('IDs repetidos.')
    # Não copia conteúdo da ajuda nem o código da auditoria para o produto.
    target.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (ROOT/'docs/analise_instalacao/backlog22_historico.json').write_text(json.dumps(
        dict(status='historical_not_evidence16',candidates=legacy.get('candidatos_22',[])),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(len(requirements),'registros iniciais; pacotes e requisitos não são contagem de funções.')


if __name__=='__main__':main()
