"""Verificação do pacote distribuível; executada somente por opção explícita."""
import json
import math
from pathlib import Path
import sys
import traceback


def run(app_class, report_path):
    report = dict(ok=False, frozen=bool(getattr(sys, 'frozen', False)), checks=[])
    app = None
    try:
        app = app_class()
        app.withdraw()
        app.update_idletasks()
        if 'MiniTaBom' not in app.title() or not app.icons:
            raise RuntimeError('Interface ou ícones indisponíveis.')
        report['checks'].append('Tk, interface e ícones')
        inventory = json.loads(Path(__file__).with_name('INVENTARIO_FUNCIONAL.json').read_text(encoding='utf-8'))
        if len(inventory['areas']) != 23:
            raise RuntimeError('Inventário de cobertura ausente ou inválido.')
        report['checks'].append('recurso JSON de cobertura')
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
        report['ok'] = True
    except Exception:
        report['error'] = traceback.format_exc()
    finally:
        if app is not None:
            app.destroy()
        Path(report_path).write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return 0 if report['ok'] else 1
