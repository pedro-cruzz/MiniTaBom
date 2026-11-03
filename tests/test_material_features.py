import itertools
import json
import math
from pathlib import Path
import statistics
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from study_tests import analyze_study, paired_values
from normality import normality_test, rj_critical, format_normality
from study_descriptives import frequency_table,sample_percentiles
from column_calculator import calculate_column,regression_columns
from core import describe,boxplot
from linear_models import linear_regression
from excel_import import read_excel,excel_sheets
from app import MiniTaBom
from history import WorksheetHistory


def group_rows(groups):
    return [[str(g[i]) if i<len(g) else '' for g in groups] for i in range(max(map(len,groups)))]


class RankTestTests(unittest.TestCase):
    def test_fisher_lsd_two_groups_equals_pooled_t_and_labels_individual_intervals(self):
        from anova import prepare_groups,one_way,format_anova_report
        from inference import two_sample
        first,second=[1,2,4,5],[3,5,7,8]
        groups,_=prepare_groups(['A','B'],group_rows([first,second]),columns=[0,1])
        result=one_way(groups,comparisons=True,comparison_method='lsd')
        pair=result['comparisons'][0];expected=two_sample(first,second,equal_var=True)
        self.assertAlmostEqual(pair['p'],expected['p'])
        self.assertAlmostEqual(pair['low'],expected['low'])
        self.assertAlmostEqual(pair['high'],expected['high'])
        report=format_anova_report(result)
        self.assertIn('Confiança individual',report);self.assertIn('p sem ajuste',report)
        with self.assertRaises(ValueError):one_way(groups,equal_var=False,comparisons=True,comparison_method='lsd')

    def test_mann_exact_probability_from_all_rank_allocations(self):
        rows=group_rows([[1,2,3],[4,5,6]])
        r=analyze_study(['A','B'],rows,'mannwhitney',columns=[0,1],method='exact')
        self.assertEqual(r['statistic'],0)
        self.assertAlmostEqual(r['p'],2/math.comb(6,3))
        left=analyze_study(['A','B'],rows,'mannwhitney',columns=[0,1],method='exact',alternative='less')
        self.assertAlmostEqual(left['p'],1/math.comb(6,3))

    def test_mann_ties_auto_symmetry_and_exact_rejection(self):
        rows=group_rows([[1,1,2,4],[2,3,3,5]])
        a=analyze_study(['A','B'],rows,'mannwhitney',columns=[0,1])
        b=analyze_study(['A','B'],rows,'mannwhitney',columns=[1,0])
        self.assertEqual(a['method'],'asymptotic')
        self.assertAlmostEqual(a['p'],b['p'])
        self.assertAlmostEqual(a['statistic']+b['statistic'],16)
        with self.assertRaises(ValueError):analyze_study(['A','B'],rows,'mannwhitney',columns=[0,1],method='exact')

    def test_wilcoxon_exact_sign_allocations_and_paired_omission(self):
        rows=[[str(i),'0'] for i in range(1,6)]+[['*','2']]
        r=analyze_study(['A','B'],rows,'wilcoxon',columns=[0,1],method='exact')
        self.assertEqual(r['statistic'],0)
        self.assertAlmostEqual(r['p'],2/2**5)
        self.assertEqual(r['summaries'][0]['n'],5)
        self.assertIn('Pares excluídos: 1',r['details'][0])

    def test_decimal_paired_ties_and_zero_conventions(self):
        values,stored,excluded=paired_values(['A','B'],[['0.3','0.2'],['0.2','0.1'],['*','1']],0,1)
        self.assertEqual(values,[.1,.1]);self.assertEqual(stored,['0.10000000000000001']*2+[''])
        for method in ['wilcox','pratt','zsplit']:
            r=analyze_study(['A','B'],[['1','1'],['2','2']],'wilcoxon',columns=[0,1],zero_method=method)
            self.assertEqual(r['p'],1)
        with self.assertRaises(ValueError):analyze_study(['A','B'],[['1','1'],['2','1']],'wilcoxon',columns=[0,1],method='exact')

    def test_kruskal_statistic_and_closed_chi_square_tail(self):
        rows=group_rows([[1,2,3],[4,5,6],[7,8,9]])
        r=analyze_study(['A','B','C'],rows,'kruskal',columns=[0,1,2])
        self.assertAlmostEqual(r['statistic'],7.2)
        self.assertAlmostEqual(r['p'],math.exp(-3.6))
        with self.assertRaises(ValueError):analyze_study(['A','B'],[['1','1'],['1','1']],'kruskal',columns=[0,1])

    def test_levene_matches_anova_of_absolute_deviations_and_closed_f_tail(self):
        groups=[[1,2,3],[2,4,8],[1,5,9]]
        deviations=[[abs(x-statistics.median(g)) for x in g] for g in groups]
        means=[statistics.mean(g) for g in deviations]
        overall=statistics.mean(x for g in deviations for x in g)
        between=sum(3*(m-overall)**2 for m in means)
        within=sum((x-m)**2 for g,m in zip(deviations,means) for x in g)
        expected=(between/2)/(within/6)
        r=analyze_study(['A','B','C'],group_rows(groups),'variances',columns=[0,1,2])
        self.assertAlmostEqual(r['statistic'],expected)
        self.assertAlmostEqual(r['p'],(6/(6+2*expected))**3)

    def test_bartlett_affine_invariance_and_positive_variances(self):
        groups=[[1,2,4,6],[3,6,9,10],[0,1,2,4]]
        a=analyze_study(['A','B','C'],group_rows(groups),'variances',columns=[0,1,2],center='bartlett')
        b=analyze_study(['A','B','C'],group_rows([[100+3*x for x in g] for g in groups]),'variances',columns=[0,1,2],center='bartlett')
        self.assertAlmostEqual(a['statistic'],b['statistic'])
        self.assertAlmostEqual(a['p'],math.exp(-a['statistic']/2))
        with self.assertRaises(ValueError):analyze_study(['A','B'],group_rows([[1,1],[1,2]]),'variances',columns=[0,1],center='bartlett')

    def test_stacked_and_separate_rank_tests_agree(self):
        separate=analyze_study(['A','B'],group_rows([[1,2,3],[5,6,7]]),'mannwhitney',columns=[0,1])
        stacked=analyze_study(['X','G'],[['1','A'],['5','B'],['2','A'],['6','B'],['3','A'],['7','B'],['bad','*']],
                              'mannwhitney',response=0,factor=1)
        self.assertEqual(separate['p'],stacked['p'])


class NewNormalityTests(unittest.TestCase):
    def test_bivariate_mardia_symmetric_corners_and_affine_transform(self):
        from bivariate_normality import bivariate_normality
        corners=[[-1,-1],[-1,1],[1,-1],[1,1]]*3
        rows=[[str(x),str(y)] for x,y in corners]
        r=bivariate_normality(['X','Y'],rows,[0,1])
        self.assertAlmostEqual(r['skew'],0,places=13)
        self.assertAlmostEqual(r['kurtosis'],4)
        self.assertAlmostEqual(r['skew_p'],1)
        changed=[[str(100+2*x+y),str(-200+x-3*y)] for x,y in corners]
        shifted=bivariate_normality(['X','Y'],changed,[0,1])
        self.assertAlmostEqual(shifted['kurtosis'],r['kurtosis'])
        self.assertAlmostEqual(shifted['kurtosis_p'],r['kurtosis_p'])
        with self.assertRaises(ValueError):bivariate_normality(['X','Y'],[['1','2'],['2','4'],['3','6'],['4','8']],[0,1])

    def test_rj_rejects_degenerate_two_level_correlation(self):
        with self.assertRaisesRegex(ValueError,'três valores distintos'):normality_test([0,0,1,1],'rj')

    def test_rj_critical_values_match_published_author_table(self):
        # Tabela de Ryan/Joiner, nota de Ryan (1990), não ajuda com faixas invertidas.
        for n,c05 in [(4,.8734),(5,.8804),(10,.9180),(20,.9503),(50,.9764),(60,.9799),(1000,.9984)]:
            self.assertAlmostEqual(rj_critical(n)[1],c05,delta=.0003)

    def test_rj_perfect_blom_scores_and_affine_invariance(self):
        from inference import scientific_stats
        n=20;values=[float(scientific_stats().norm.ppf((i-.375)/(n+.25))) for i in range(1,n+1)]
        r=normality_test(values,'rj')
        self.assertAlmostEqual(r['statistic'],1)
        self.assertIsNone(r['p']);self.assertEqual(r['p_lower'],.1)
        self.assertIn('> 0.1',format_normality(r))
        shifted=normality_test([100+3*x for x in values],'rj')
        self.assertAlmostEqual(r['statistic'],shifted['statistic'])

    def test_ks_closed_three_point_statistic_and_bounds(self):
        r=normality_test([-1,0,1],'ks')
        expected=1/3-.5*math.erfc(1/math.sqrt(2))
        self.assertAlmostEqual(r['statistic'],expected)
        self.assertEqual(r['p_lower'],.15)
        skew=normality_test([0]*99+[10],'ks')
        self.assertEqual(skew['p_upper'],.01)

    def test_methods_ranges_and_invariance(self):
        values=[1,2,2.5,3,4,5,6,7,9,12,15,19]
        for method in ('rj','ks','shapiro','dagostino'):
            r=normality_test(values,method)
            transformed=normality_test([2+3*x for x in values],method)
            self.assertAlmostEqual(r['statistic'],transformed['statistic'],places=10)
        for method,values in [('rj',[1,2,3]),('dagostino',list(range(7))),('shapiro',list(range(5001))),('rj',list(range(1001)))]:
            with self.assertRaises(ValueError):normality_test(values,method)


class DescriptiveMaterialTests(unittest.TestCase):
    def test_pdf_height_frequency_example(self):
        values=['1.55','1.56','1.58','1.59','1.60','1.61','1.62','1.64','1.67','1.68','1.71','1.74','1.78','1.80','1.82','1.83','1.84']
        r=frequency_table(['Altura'],[[v] for v in values],0,numeric=True,classes=4)
        self.assertEqual(r['width'],'0.08')
        self.assertEqual([x['count'] for x in r['table']],[7,3,3,4])
        self.assertEqual(r['table'][-1]['cumulative'],17)
        self.assertEqual(r['table'][-1]['cumulative_percent'],100)

    def test_exact_step_extra_class_and_decimal_precision(self):
        r=frequency_table(['X'],[[str(i)] for i in range(1,6)],0,numeric=True,classes=2)
        self.assertTrue(r['exact_step']);self.assertEqual(r['classes'],3)
        self.assertEqual([x['count'] for x in r['table']],[2,2,1])
        with self.assertRaises(ValueError):frequency_table(['X'],[['1.25'],['2.5']],0,numeric=True,decimals=1)

    def test_weighted_categories_and_cumulative_order(self):
        r=frequency_table(['Categoria','N'],[['B','3'],['A','2'],['B','1'],['*','1']],0,frequency_column=1,order='descending')
        self.assertEqual(r['n'],6);self.assertEqual(r['missing'],1)
        self.assertEqual([v['label'] for v in r['table']],['B','A'])
        self.assertEqual([v['cumulative'] for v in r['table']],[4,6])
        self.assertAlmostEqual(r['table'][0]['relative'],2/3)
        with self.assertRaises(ValueError):frequency_table(['X','N'],[['A','-1']],0,frequency_column=1)

    def test_exclusive_inclusive_percentiles_and_population_variance(self):
        result=sample_percentiles(list(range(1,10)),[0,25,50,75,100])
        self.assertEqual([r['value'] for r in result],[None,2.5,5,7.5,None])
        self.assertEqual(sample_percentiles(list(range(1,10)),[25],'inclusive')[0]['value'],3)
        self.assertEqual(sample_percentiles([7],[0,100],'clamped')[0]['value'],7)
        self.assertEqual(describe([0,2])['Variância populacional'],1)
        self.assertEqual(describe([0,2])['Desvio padrão populacional'],1)
        with self.assertRaises(ValueError):sample_percentiles([1,2],[101])

    def test_outlier_classes_match_material_fences(self):
        r=boxplot([25,28,26,29,30,32,35,38,36,39,27,28,22,25,29,25])
        self.assertEqual(r['outliers'],[])
        r=boxplot([31,32,38,36,39,35,38,41,42,42,46,48,42,80,42])
        self.assertEqual(r['extreme_outliers'],[80]);self.assertEqual(r['mild_outliers'],[])


class GeneratedColumnsTests(unittest.TestCase):
    def test_decimal_difference_and_missing_rows_preserved(self):
        headers,rows=['A','B'],[['0.3','0.2'],['*','1'],['2','1']]
        new_headers,new_rows,names=calculate_column(headers,rows,'C1-C2','Diferença')
        self.assertEqual([r[-1] for r in new_rows],['0.1','','1'])
        self.assertEqual(rows,[['0.3','0.2'],['*','1'],['2','1']])
        self.assertEqual(names,['Diferença'])

    def test_functions_and_reject_code_execution_or_invalid_arithmetic(self):
        _,rows,_=calculate_column(['A'],[['4'],['9']],'sqrt(C1)+round(1.234,2)','R')
        self.assertEqual([float(r[-1]) for r in rows],[3.23,4.23])
        for expression in ['__import__("os")','C1.__class__','[C1]','C1/0','sqrt(-C1)','C0','C1**1001']:
            with self.subTest(expression=expression),self.assertRaises(ValueError):calculate_column(['A'],[['1']],expression)

    def test_regression_storage_preserves_excluded_original_rows(self):
        headers=['X','Y'];rows=[['1','2'],['2','4'],['','9'],['4','7'],['5','11']]
        model=linear_regression(headers,rows,1,[0])
        new_headers,new_rows,names=regression_columns(headers,rows,model)
        self.assertEqual(new_rows[2],['','9']+['']*5)
        for original,computed in zip(model['row_numbers'],model['residuals']):
            self.assertAlmostEqual(float(new_rows[original-1][3]),computed)
        self.assertEqual(names[1],'Resíduos')


class ExcelReadTests(unittest.TestCase):
    def make_book(self,path,formula=False):
        workbook='<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Dados" sheetId="1" r:id="rId1"/></sheets></workbook>'
        rels='<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>'
        sheet='<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData><row r="4"><c r="A4" t="inlineStr"><is><t>X</t></is></c><c r="B4" t="inlineStr"><is><t>Y</t></is></c></row><row r="5"><c r="A5"><v>1.5</v></c><c r="B5"><v>3</v></c></row><row r="6"><c r="A6"><v>2.5</v></c><c r="B6">'+('<f>2+3</f>' if formula else '<v>5</v>')+'</c></row></sheetData></worksheet>'
        with zipfile.ZipFile(path,'w') as z:
            for name,text in [('xl/workbook.xml',workbook),('xl/_rels/workbook.xml.rels',rels),('xl/worksheets/sheet1.xml',sheet)]:z.writestr(name,text)

    def test_select_sheet_range_headers_and_missing_formula_cache(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'input.xlsx';self.make_book(path)
            self.assertEqual(excel_sheets(path)[0]['name'],'Dados')
            headers,rows,meta=read_excel(path,'Dados','A4:B6')
            self.assertEqual(headers,['X','Y']);self.assertEqual(rows,[['1.5','3'],['2.5','5']])
            self.assertEqual(read_excel(path,'Dados','A5:B6',False)[0],['C1','C2'])
            with self.assertRaises(ValueError):read_excel(path,'Dados','A6:A5')
            self.make_book(path,True)
            with self.assertRaisesRegex(ValueError,'fórmula sem resultado'):read_excel(path,'Dados','A4:B6')


class MaterialInterfaceTests(unittest.TestCase):
    def setUp(self):
        self.app=MiniTaBom();self.app.withdraw();self.addCleanup(self.app.destroy)
        self.app.headers=['A','B','C'];self.app.rows=[['1','3','2'],['2','5','4'],['4','8','6'],['7','9','8'],['8','11','10']]
        self.app.history=WorksheetHistory(self.app.headers,self.app.rows)
        self.app.refresh()

    def test_rank_dialog_submit_and_result_navigation(self):
        for mode in ('mannwhitney','wilcoxon','kruskal','variances'):
            d=self.app.study_dialog(mode)
            if d.selector:
                d.selector.columns.selection_clear(0,'end');d.selector.columns.selection_set(0,1)
            d.submit();self.assertFalse(d.winfo_exists())
        self.assertEqual(len(self.app.navigator.get_children('results')),4)

    def test_calculator_one_history_step_and_failed_operation_atomic(self):
        before=[r[:] for r in self.app.rows]
        self.assertTrue(self.app.run_calculator('C2-C1','Diferenças'))
        self.assertEqual(self.app.headers[-1],'Diferenças')
        self.app.undo_data();self.assertEqual(self.app.rows,before)
        with patch('app.messagebox.showerror'):
            self.assertFalse(self.app.run_calculator('C1/0','Falha'))
        self.assertEqual(self.app.rows,before)

    def test_paired_difference_and_regression_storage(self):
        self.assertTrue(self.app.run_ttest('paired',0,1,store=True))
        self.assertIn('Diferenças',self.app.headers)
        self.assertTrue(self.app.run_regression(1,[0],show_graph=False,store=True))
        self.assertIn('Resíduos',self.app.headers)
        self.assertIsNotNone(self.app.last_regression)
        self.assertTrue(self.app.run_normality(self.app.headers.index('Resíduos'),method='rj'))

    def test_frequency_and_percentile_dialog_submit(self):
        d=self.app.frequency_dialog();d.submit();self.assertFalse(d.winfo_exists())
        d=self.app.percentile_dialog();d.deciles();d.submit();self.assertFalse(d.winfo_exists())
        self.assertIn('TABELA DE FREQUÊNCIAS',self.app.output.get('1.0','end'))
        self.assertIn('PERCENTIS DA AMOSTRA',self.app.output.get('1.0','end'))

    def test_new_graphs_draw_and_keep_snapshots(self):
        from probability_graph import ProbabilityGraph
        from frequency_graph import FrequencyGraph
        sample=[1,2,3,4,5,7,9,11]
        graph=ProbabilityGraph(self.app,sample,dict(normality_test(sample,'rj'),source='A'))
        graph.withdraw();graph.draw();self.assertGreater(len(graph.canvas.find_all()),25);graph.destroy()
        r=frequency_table(['X'],[['A'],['B'],['B'],['C'],['C'],['C']],0)
        for kind in ('bar','pareto','pie'):
            graph=FrequencyGraph(self.app,r,kind);graph.withdraw();graph.draw()
            self.assertGreater(len(graph.canvas.find_all()),3);self.assertIsNot(graph.result,r);graph.destroy()

    def test_excel_import_cancel_preserves_project(self):
        before=self.app.rows
        with patch.object(self.app,'confirm_replace',return_value=False):
            self.assertFalse(self.app.import_excel_data(['X'],[['1']],dict(sheet='A',range='A1',note=''),'source.xlsx'))
        self.assertIs(self.app.rows,before)
