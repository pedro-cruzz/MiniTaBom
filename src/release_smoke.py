"""Verificação do pacote distribuível; executada somente por opção explícita."""
import json
import math
from pathlib import Path
import sys
import traceback
import time
from app_resources import resource_path


def run(app_class, report_path):
    report = dict(ok=False, frozen=bool(getattr(sys, 'frozen', False)), checks=[])
    app = None
    try:
        app = app_class()
        app.withdraw()
        app.update_idletasks()
        def drain_task():
            deadline = time.monotonic() + 30
            while app._task_window is not None:
                app.update()
                if time.monotonic() > deadline:raise RuntimeError('Tarefa em segundo plano não concluiu no pacote.')
                time.sleep(.005)
        if 'MiniTaBom' not in app.title() or not app.icons:
            raise RuntimeError('Interface ou ícones indisponíveis.')
        if app.rows or app.output.get('1.0', 'end-1c') or app.dirty:
            raise RuntimeError('O programa deve iniciar com planilha e sessão vazias.')
        report['checks'].append('inicialização com planilha e sessão vazias')
        report['checks'].append('Tk, interface e ícones')
        inventory = json.loads(resource_path('INVENTARIO_FUNCIONAL.json').read_text(encoding='utf-8'))
        if len(inventory['areas']) != 23:
            raise RuntimeError('Inventário de cobertura ausente ou inválido.')
        report['checks'].append('recurso JSON de cobertura')
        from updates import load_metadata
        if not load_metadata()['version']:
            raise RuntimeError('Versão do aplicativo ausente.')
        dialog = app.update_dialog()
        dialog.withdraw()
        if str(dialog.check_button.cget('state')) != 'normal':
            raise RuntimeError('Botão de atualizações indisponível.')
        dialog.destroy()
        report['checks'].append('diálogo de atualizações e versão (sem acesso à rede)')
        from inference import one_sample, scientific_stats
        if not math.isclose(one_sample([0, 2])['p'], .5, abs_tol=1e-12):
            raise RuntimeError('Resultado do teste t inconsistente.')
        stats = scientific_stats()
        probability = float(stats.studentized_range.cdf(3, 3, 10))
        if not math.isfinite(probability) or not 0 < probability < 1:
            raise RuntimeError('Distribuição das comparações múltiplas indisponível.')
        report['checks'].append('SciPy: teste t e distribuição de comparações')
        from linear_models import linear_regression
        model = linear_regression(['X', 'Y'], [['0', '1'], ['1', '2'], ['2', '4'], ['3', '4']], 1, [0])
        if not math.isclose(model['terms'][1]['coefficient'], 1.1, abs_tol=1e-12):
            raise RuntimeError('Regressão NumPy/SciPy inconsistente.')
        report['checks'].append('regressão NumPy/SciPy')
        from study_tests import analyze_study
        rank=analyze_study(['A','B'],[['1','4'],['2','5'],['3','6']],'mannwhitney',columns=[0,1],method='exact')
        if not math.isclose(rank['p'],.1,abs_tol=1e-12):raise RuntimeError('Mann–Whitney indisponível no pacote.')
        from normality import normality_test
        if normality_test([1,2,3,4,5,7,9,11],'rj')['method_key']!='rj':raise RuntimeError('Ryan–Joiner indisponível.')
        from study_descriptives import frequency_table
        if frequency_table(['X'],[['A'],['B'],['B']],0)['n']!=3:raise RuntimeError('Tabela de frequências indisponível.')
        from column_calculator import calculate_column
        if calculate_column(['A','B'],[['0.3','0.2']],'C1-C2')[1][0][-1]!='0.1':raise RuntimeError('Calculadora indisponível.')
        from probability_graph import ProbabilityGraph
        from frequency_graph import FrequencyGraph
        probability=ProbabilityGraph(app,[1,2,3,4,5,7,9,11],dict(normality_test([1,2,3,4,5,7,9,11],'rj'),source='Teste'))
        probability.withdraw();probability.draw();probability.destroy()
        chart=FrequencyGraph(app,frequency_table(['X'],[['A'],['B'],['B']],0),'pareto')
        chart.withdraw();chart.draw();chart.destroy()
        report['checks'].append('postos, Ryan–Joiner, frequências, calculadora e novos gráficos')
        registry = json.loads(resource_path('CAPACIDADES.json').read_text(encoding='utf-8'))
        if not registry['requirements'] or registry['parity_validated']:
            raise RuntimeError('Registro de capacidades ausente ou com estado inesperado.')
        import tempfile
        from project import load_document
        from analysis_service import rerun_analysis
        app.headers=['X'];app.rows=[['0'],['2'],['*']];app.refresh()
        if not app.run_ttest('one',0):
            raise RuntimeError('Serviço estruturado do teste t indisponível.')
        if not app.add_worksheet('Segunda'):
            raise RuntimeError('Coleção de planilhas indisponível.')
        app.headers=['Y'];app.rows=[['4'],['6']];app.refresh()
        if not app.run_ttest('one',0,null=5):
            raise RuntimeError('Análise na segunda planilha indisponível.')
        with tempfile.TemporaryDirectory() as directory:
            app.project_path=str(Path(directory)/'smoke.statlab')
            if not app.save_project():
                raise RuntimeError('Gravação de projeto v2 indisponível.')
            document=load_document(app.project_path)
            if len(document['worksheets'])!=2 or len(document['analyses'])!=2:
                raise RuntimeError('Planilhas ou resultados não persistidos.')
            rerun=rerun_analysis(document,document['analyses'][0]['analysis_id'])
            if not math.isclose(rerun['values']['p'],.5,abs_tol=1e-12):
                raise RuntimeError('Reexecução após reabrir o projeto inconsistente.')
        history=app.analysis_history_dialog();history.withdraw();history.destroy()
        report['checks'].append('registro, projeto v2, duas planilhas, resultado persistente e reexecução')
        app.headers=['A','B','Resposta','Grupo']
        app.rows=[['0','0','0','A'],['2','0','2','A'],['*','1','2','B'],['','*','4','B']]
        app.refresh()
        if not app.run_ttest('paired',0,1,store=True):
            raise RuntimeError('Histórico/armazenamento pareado indisponível.')
        if not app.run_ttest('two',2,3,source='stacked',legacy_df=False):
            raise RuntimeError('Histórico de amostras empilhadas indisponível.')
        stacked=app.document['analyses'][-1]
        if not app.run_ttest('two',source='summary',summaries=[dict(n=2,mean=1.,sd=2.),dict(n=3,mean=4.,sd=3.)]):
            raise RuntimeError('Histórico de resumos indisponível.')
        with tempfile.TemporaryDirectory() as directory:
            app.project_path=str(Path(directory)/'formats.statlab')
            if not app.save_project():raise RuntimeError('Gravação dos formatos t indisponível.')
            document=load_document(app.project_path)
            summary=rerun_analysis(document,document['analyses'][-1]['analysis_id'])
            repeated=rerun_analysis(document,stacked['analysis_id'])
            if summary['parameters']['summaries'] is None or repeated['parameters']['group_order']!=['A','B']:
                raise RuntimeError('Parâmetros efetivos dos testes t não preservados.')
        report['checks'].append('testes t pareado, resumos, empilhadas e ordem persistida dos grupos')
        from workspace_model import active_sheet
        app.headers=['X','Y'];app.rows=[['0','1'],['1','2'],['2','4'],['3','4']];app.refresh()
        if not app.run_regression(1,[0],show_graph=False,store=True):
            raise RuntimeError('Regressão persistente indisponível.')
        regression_id=app.last_regression_id
        with tempfile.TemporaryDirectory() as directory:
            app.project_path=str(Path(directory)/'regression.statlab')
            if not app.save_project():raise RuntimeError('Gravação de modelo indisponível.')
            document=load_document(app.project_path)
            app.document=document;sheet=active_sheet(document)
            app.headers=[c['name'] for c in sheet['columns']];app.rows=sheet['rows']
            app.clear_regression();app.refresh()
            if app.last_regression_id!=regression_id or not app.run_prediction(text='4'):
                raise RuntimeError('Restauração do modelo/previsão indisponível.')
            if 'Previsão = 5.5' not in app.output.get('1.0','end'):
                raise RuntimeError('Previsão do modelo persistido inconsistente.')
            forecast_id=app.document['analyses'][-1]['analysis_id']
            graph=app.show_saved_regression_graph(regression_id)
            if graph is None:raise RuntimeError('Gráfico histórico indisponível.')
            graph.withdraw();graph.draw();graph.destroy()
            if not app.rerun_saved_analysis(regression_id):
                raise RuntimeError('Reexecução do modelo indisponível.')
            if not app.rerun_saved_analysis(forecast_id) or app.document['analyses'][-1]['parameters']['model_analysis_id']!=regression_id:
                raise RuntimeError('A previsão perdeu o vínculo com o modelo original.')
        report['checks'].append('modelo linear salvo, restauração, previsão sem novo ajuste e gráfico histórico')
        app.headers=['A','B','C'];app.rows=[['1','4','7'],['2','5','8'],['3','6','9']];app.refresh()
        if not app.run_anova(columns=[0,1,2],comparisons=True,comparison_method='lsd'):
            raise RuntimeError('ANOVA persistente indisponível.')
        anova_id=app.document['analyses'][-1]['analysis_id']
        graph=app.show_saved_anova_graph(anova_id)
        if graph is None:raise RuntimeError('Boxplot histórico de ANOVA indisponível.')
        graph.withdraw();graph.draw();graph.destroy()
        with tempfile.TemporaryDirectory() as directory:
            app.project_path=str(Path(directory)/'prediction-anova.statlab')
            if not app.save_project():raise RuntimeError('Gravação de previsão/ANOVA indisponível.')
            document=load_document(app.project_path)
            prediction=rerun_analysis(document,forecast_id)
            anova=rerun_analysis(document,anova_id)
            if not math.isclose(prediction['values']['cases'][0]['fit'],5.5,abs_tol=1e-12) or not math.isclose(anova['values']['p'],.001,abs_tol=1e-12):
                raise RuntimeError('Reexecução de previsão/ANOVA inconsistente.')
        report['checks'].append('previsões vinculadas, ANOVA/comparações persistentes e boxplots históricos')
        app.headers=['A','B','C'];app.rows=[[str(i+1),str(20+2*i),str(2+3*i)] for i in range(8)];app.refresh()
        if not app.run_normality(0,method='rj'):raise RuntimeError('Normalidade persistente indisponível.')
        normality_id=app.document['analyses'][-1]['analysis_id']
        for mode,options in [('mannwhitney',dict(columns=[0,1],method='exact')),('wilcoxon',dict(columns=[0,1],method='exact')),
                             ('kruskal',dict(columns=[0,1,2])),('variances',dict(columns=[0,1,2],center='bartlett'))]:
            if not app.run_study(mode,**options):raise RuntimeError('Teste persistente indisponível: '+mode)
        graph=app.show_saved_normality_graph(normality_id)
        if graph is None:raise RuntimeError('Gráfico histórico de normalidade indisponível.')
        graph.withdraw();graph.draw();graph.destroy()
        with tempfile.TemporaryDirectory() as directory:
            app.project_path=str(Path(directory)/'diagnostics.statlab')
            if not app.save_project():raise RuntimeError('Gravação dos diagnósticos indisponível.')
            document=load_document(app.project_path)
            normality=rerun_analysis(document,normality_id)
            variance=rerun_analysis(document,document['analyses'][-1]['analysis_id'])
            if normality['values']['method_key']!='rj' or variance['parameters']['center']!='bartlett':
                raise RuntimeError('Opções dos diagnósticos não preservadas.')
        report['checks'].append('normalidade/gráfico histórico, postos, variâncias e reexecução persistente')
        if not app.run_two_poisson(input_kind='summary',summaries=[dict(events=713,n=40),dict(events=515,n=20)],lengths=[3.,6.]):
            raise RuntimeError('Duas taxas Poisson indisponíveis.')
        poisson_id=app.document['analyses'][-1]['analysis_id']
        if not math.isclose(app.document['analyses'][-1]['values']['estimate'],1.65,abs_tol=1e-12):
            raise RuntimeError('Comparação de taxas inconsistente.')
        with tempfile.TemporaryDirectory() as directory:
            app.project_path=str(Path(directory)/'two-poisson.statlab')
            if not app.save_project():raise RuntimeError('Gravação das taxas indisponível.')
            document=load_document(app.project_path)
            if not math.isclose(rerun_analysis(document,poisson_id)['values']['estimate'],1.65,abs_tol=1e-12):
                raise RuntimeError('Reexecução de taxas inconsistente.')
        import zipfile
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'automatic.xlsx'
            ns='http://schemas.openxmlformats.org/spreadsheetml/2006/main'
            with zipfile.ZipFile(path,'w') as archive:
                archive.writestr('xl/workbook.xml',f'<workbook xmlns="{ns}" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Dados" sheetId="1" r:id="r1"/></sheets></workbook>')
                archive.writestr('xl/_rels/workbook.xml.rels','<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="r1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>')
                archive.writestr('xl/worksheets/sheet1.xml',f'<worksheet xmlns="{ns}"><sheetData><row r="2"><c r="B2"><v>12</v></c></row></sheetData></worksheet>')
            app.dirty=False
            if not app.start_excel_import(path):raise RuntimeError('Tarefa de abertura Excel indisponível.')
            drain_task()
            if app.rows!=[['',''],['','12']]:
                raise RuntimeError('Abertura automática do Excel indisponível.')
        report['checks'].append('Excel sem intervalo e duas taxas Poisson com persistência')
        random_dialog = app.random_dialog()
        random_dialog.withdraw(); random_dialog.destroy()
        if not app.run_random('Normal', {'mean': 0., 'sd': 1.}, row_count=6, column_count=2, seed=123):
            raise RuntimeError('Geração aleatória indisponível no pacote.')
        random_id = app.document['analyses'][-1]['analysis_id']
        generated = [row[-2:] for row in app.rows]
        with tempfile.TemporaryDirectory() as directory:
            app.project_path = str(Path(directory) / 'random.statlab')
            if not app.save_project(): raise RuntimeError('Gravação dos valores aleatórios indisponível.')
            document = load_document(app.project_path)
            replay = rerun_analysis(document, random_id)
            if replay['values'] != document['analyses'][-1]['values']:
                raise RuntimeError('Valores aleatórios não preservados após reabrir.')
        if not app.rerun_saved_analysis(random_id) or [row[-2:] for row in app.rows] != generated:
            raise RuntimeError('Reprodução aleatória não preservou as células.')
        width = len(app.headers)
        app.undo_data()
        if len(app.headers) != width - 2: raise RuntimeError('Desfazer geração indisponível.')
        app.redo_data()
        if len(app.headers) != width: raise RuntimeError('Refazer geração indisponível.')
        if not app.run_random('Inteiros', {'lower': 7, 'upper': 7}, row_count=6, seed=0):
            raise RuntimeError('Geração de inteiros indisponível.')
        if any(row[-1] != '7' for row in app.rows): raise RuntimeError('Valores inteiros inconsistentes.')
        report['checks'].append('geração PCG64, semente, persistência, reprodução exata e undo/redo')
        if not app.start_random('Normal', {'mean': 0., 'sd': 1.}, row_count=5000, column_count=2, seed=2718):
            raise RuntimeError('Tarefa de geração aleatória indisponível.')
        drain_task()
        if len(app.rows) != 5000 or app.document['analyses'][-1]['parameters']['seed'] != 2718:
            raise RuntimeError('Resultado da geração em segundo plano inconsistente.')
        before_headers=list(app.headers);before_rows=[list(row) for row in app.rows]
        before_analyses=len(app.document['analyses'])
        def cancelled_work(context):
            while True:
                context.cancelled.wait(.005);context.checkpoint()
        def must_not_apply(value):raise RuntimeError('Tarefa cancelada aplicou dados.')
        if not app.start_background_task('Verificação de cancelamento',cancelled_work,must_not_apply):
            raise RuntimeError('Serviço de tarefas indisponível.')
        app._task_window.cancel();drain_task()
        if app.headers!=before_headers or app.rows!=before_rows or len(app.document['analyses'])!=before_analyses:
            raise RuntimeError('Cancelar alterou a planilha ou o histórico.')
        report['checks'].append('tarefas em segundo plano: Excel, geração e cancelamento sem alteração')
        report['ok'] = True
    except Exception:
        report['error'] = traceback.format_exc()
    finally:
        if app is not None:
            app.destroy()
        Path(report_path).write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return 0 if report['ok'] else 1
