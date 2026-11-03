"""Verificação do pacote distribuível; executada somente por opção explícita."""
import json
import math
from pathlib import Path
import sys
import traceback
from app_resources import resource_path


def run(app_class, report_path):
    report = dict(ok=False, frozen=bool(getattr(sys, 'frozen', False)), checks=[])
    app = None
    try:
        app = app_class()
        app.withdraw()
        app.update_idletasks()
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
        report['ok'] = True
    except Exception:
        report['error'] = traceback.format_exc()
    finally:
        if app is not None:
            app.destroy()
        Path(report_path).write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return 0 if report['ok'] else 1
