"""Confere formatos de todos os exemplos e resultados dos exemplos novos."""
from pathlib import Path
import json
import math
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from project import load_project
from extended_inference import analyze_extended
from contingency import categorical_table, matrix_table
from normality import analyze_normality
from inference import analyze_t_inputs


def main():
    examples = {path.name: load_project(path) for path in ROOT.glob('exemplo_*.statlab')}
    for name in ('INVENTARIO_FUNCIONAL.json', 'analise_instalacao/lacunas_priorizadas.json',
                 'analise_instalacao/cobertura_minitab16.json', 'analise_instalacao/referencias_minitab16.json'):
        json.loads((ROOT / name).read_text(encoding='utf-8'))
    headers, rows, _ = examples['exemplo_proporcoes_variancias.statlab']
    result = analyze_extended(headers, rows, 'two_proportions', [2, 3], events=['Sim', 'Sim'])
    assert [s['events'] for s in result['samples']] == [4, 2]
    assert [s['n'] for s in result['samples']] == [6, 6]
    one = analyze_extended(headers, rows, 'one_variance', [0], measure='variance')
    assert one['estimate'] == 3.5
    separate = analyze_extended(headers, rows, 'two_variances', [0, 1], measure='variance')
    stacked = analyze_extended(headers, rows, 'two_variances', [4], source='stacked', group=5, measure='variance')
    assert separate['statistic'] == stacked['statistic'] == .25
    assert separate['p'] == stacked['p']
    headers, rows, _ = examples['exemplo_contingencia.statlab']
    categorical = categorical_table(headers, rows, 0, 1, 2)
    matrix = matrix_table(headers, rows, [3, 4], 5)
    assert categorical['observed'] == matrix['observed'] == [[30, 10], [10, 30]]
    assert categorical['pearson'] == matrix['pearson'] == 20
    assert math.isclose(categorical['p'], math.erfc(math.sqrt(10)), rel_tol=1e-12)
    headers, rows, _ = examples['exemplo_normalidade.statlab']
    normal, skew = [analyze_normality(headers, rows, column) for column in (0, 1)]
    assert normal['n'] == skew['n'] == 21
    assert normal['missing'] == skew['missing'] == 2
    assert normal['statistic'] < skew['statistic']
    headers, rows, _ = examples['exemplo_formatos_t.statlab']
    raw = analyze_t_inputs(headers, rows, 'two', 0, 1)
    stacked = analyze_t_inputs(headers, rows, 'two', 2, 3, source='stacked')
    summary = analyze_t_inputs(headers, rows, 'two', source='summary',
                              summaries=[dict(n=3, mean=2, sd=2), dict(n=3, mean=3, sd=2)])
    assert raw['estimate'] == stacked['estimate'] == summary['estimate'] == -1
    assert raw['p'] == stacked['p'] == summary['p']
    print(f'{len(examples)} exemplos válidos; novos cálculos e inventários conferidos.')


if __name__ == '__main__':
    main()
