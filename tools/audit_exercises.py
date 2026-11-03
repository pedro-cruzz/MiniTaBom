"""Executa o núcleo atual do MiniTaBom nos dados extraídos da lista."""
import json
from pathlib import Path
import statistics
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from core import boxplot
from normality import normality_test
from inference import analyze_columns, two_sample, format_t_report
from extended_inference import analyze_extended
from anova import prepare_groups, one_way
from linear_models import correlations, linear_regression

OUTPUT = ROOT / 'docs' / 'analise_estudo'


def main():
    source = json.loads((OUTPUT / 'excel_celulas.json').read_text(encoding='utf-8'))[0]
    cells = {c['cell']: c['value'] for c in source['cells']}
    scenarios = [('1/2a', 'Tempo', 'A4:B20', ['A', 'B'], 4, 5, 20, 'independent'),
                 ('1/2b', 'Produtividade', 'D4:E19', ['D', 'E'], 4, 5, 19, 'independent'),
                 ('3a', 'Custo antes/depois', 'A23:B42', ['A', 'B'], 23, 24, 42, 'paired'),
                 ('3b', 'Colesterol antes/depois', 'D23:E35', ['D', 'E'], 23, 24, 35, 'paired'),
                 ('4a', 'Provedores', 'A47:C62', ['A', 'B', 'C'], 47, 48, 62, 'anova'),
                 ('4b', 'Lotes', 'E47:G82', ['E', 'F', 'G'], 47, 48, 82, 'anova'),
                 ('4c', 'Qualidade de vida', 'I47:K61', ['I', 'J', 'K'], 47, 48, 61, 'anova'),
                 ('5a', 'Prints e tempo', 'A87:B96', ['A', 'B'], 87, 88, 96, 'regression'),
                 ('5b', 'Pessoas e prazo', 'E87:F95', ['E', 'F'], 87, 88, 95, 'regression')]
    results = []
    for identifier, title, source_range, columns, header, start, end, mode in scenarios:
        headers = [cells[f'{col}{header}'] for col in columns]
        rows = [[str(cells.get(f'{col}{r}', '')) for col in columns] for r in range(start, end + 1)]
        groups = [[float(cells[f'{col}{r}']) for r in range(start, end + 1) if f'{col}{r}' in cells] for col in columns]
        normality = [normality_test(g) for g in groups]
        boxes = [boxplot(g) for g in groups]
        details = dict(id=identifier, name=title, source_range=source_range, headers=headers,
                       n=[len(g) for g in groups], normality=normality, boxplots=boxes,
                       severe_outliers=[[x for x in g if x < b['q1'] - 3 * (b['q3']-b['q1'])
                                         or x > b['q3'] + 3 * (b['q3']-b['q1'])] for g, b in zip(groups, boxes)])
        if mode == 'independent':
            details['variances'] = analyze_extended(headers, rows, 'two_variances', [0, 1], measure='variance')
            details['student'] = analyze_columns(headers, rows, 'two', 0, 1, equal_var=True)
            details['welch'] = analyze_columns(headers, rows, 'two', 0, 1)
        elif mode == 'paired':
            differences = [a-b for a, b in zip(*groups)]
            details['differences_normality'] = normality_test(differences)
            details['differences_boxplot'] = boxplot(differences)
            details['paired'] = analyze_columns(headers, rows, 'paired', 0, 1)
        elif mode == 'anova':
            prepared, excluded = prepare_groups(headers, rows, columns=list(range(len(columns))))
            details['anova'] = one_way(prepared, comparisons=True)
            details['welch_anova'] = one_way(prepared, equal_var=False, comparisons=True)
            variances = [statistics.variance(g) for g in groups]
            details['variance_ratio_max_min'] = max(variances) / min(variances)
            details['variance_pairs'] = [dict(pair=[i, j], result=analyze_extended(headers, rows, 'two_variances', [i, j], measure='variance'))
                                         for i in range(len(groups)) for j in range(i+1, len(groups))]
        else:
            details['correlation'] = correlations(headers, rows, [0, 1])
            details['regression'] = linear_regression(headers, rows, 1, [0])
            details['residual_normality'] = normality_test(details['regression']['residuals'])
        results.append(details)
    (OUTPUT / 'resultados_nucleo.json').write_text(json.dumps(results, ensure_ascii=False, indent=2,
                                                           default=lambda value: value.item()), encoding='utf-8')
    for result in results:
        print(result['id'], result['name'], result['source_range'], 'N=',result['n'])
        print('AD p=', [round(n['p'], 7) if n['p'] is not None else '<limite' for n in result['normality']],
              'outliers=', [b['outliers'] for b in result['boxplots']], 'extremos=',result['severe_outliers'])
        for key in ['variances','student','welch','paired','anova','welch_anova']:
            if key in result:
                item=result[key]
                print(key, {k: item[k] for k in ['estimate','statistic','t','f','p','df','low','high'] if k in item})
        if 'differences_normality' in result:
            print('AD diferenças:',result['differences_normality']['p'], 'outliers dif=',result['differences_boxplot']['outliers'])
        if 'variance_ratio_max_min' in result:
            print('Razão max/min:',result['variance_ratio_max_min'])
        if 'correlation' in result:
            pair = result['correlation']['pairs'][0]
            model = result['regression']
            print('r=',pair['r'],'p=',pair['p'],'coef=',[t['coefficient'] for t in model['terms']],
                  'R2=',model['r2'],'AD resíduos=',result['residual_normality']['p'])


if __name__ == '__main__':
    main()
