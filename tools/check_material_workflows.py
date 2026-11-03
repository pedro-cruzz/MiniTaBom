"""Conferência dos novos fluxos com o Excel da lista, sem alterar o original."""
import json
from pathlib import Path
import sys
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from app import MiniTaBom
from excel_import import read_excel
from normality import METHODS


def main():
    path=Path('C:/Users/pedro/Downloads/exercícios sistemas 2b.xlsx')
    if not path.is_file():raise SystemExit('Material original não encontrado neste computador.')
    cases=[('1/2a','A4:B20','independent'),('1/2b','D4:E19','independent'),('3a','A23:B42','paired'),
           ('3b','D23:E35','paired'),('4a','A47:C62','anova'),('4b','E47:G82','anova'),
           ('4c','I47:K61','anova'),('5a','A87:B96','linear'),('5b','E87:F95','linear')]
    app=MiniTaBom();app.withdraw();completed=[]
    try:
        with patch.object(app,'confirm_replace',return_value=True),patch('app.messagebox.showerror',side_effect=lambda *a,**k: (_ for _ in ()).throw(AssertionError(str(a)))):
            for name,cell_range,kind in cases:
                headers,rows,meta=read_excel(path,'Plan1',cell_range)
                assert app.import_excel_data(headers,rows,meta,path)
                for column in range(len(headers)):
                    for method in METHODS:
                        assert app.run_normality(column,method=method,show_graph=False)
                if kind=='independent':
                    assert app.run_study('variances',columns=[0,1])
                    assert app.run_study('mannwhitney',columns=[0,1])
                    assert app.run_ttest('two',0,1,equal_var=True)
                    assert app.run_ttest('two',0,1,equal_var=False)
                elif kind=='paired':
                    assert app.run_ttest('paired',0,1,store=True)
                    assert app.run_normality(len(app.headers)-1,method='rj')
                    assert app.run_study('wilcoxon',columns=[0,1])
                elif kind=='anova':
                    assert app.run_study('variances',columns=[0,1,2])
                    assert app.run_study('variances',columns=[0,1,2],center='bartlett')
                    assert app.run_study('kruskal',columns=[0,1,2])
                    assert app.run_anova(columns=[0,1,2],comparisons=True)
                    assert app.run_anova(columns=[0,1,2],comparisons=True,comparison_method='lsd')
                else:
                    assert app.run_correlation([0,1],check_bivariate=True)
                    assert app.run_regression(1,[0],show_graph=False,store=True)
                    assert app.run_normality(app.headers.index('Resíduos'),method='rj')
                completed.append(dict(exercise=name,range=cell_range,rows=len(rows),columns=len(headers),
                                      results=len(app.navigator.get_children('results')),ok=True))
                print(name,'OK',flush=True)
    finally:app.destroy()
    out=ROOT/'docs/analise_estudo/verificacao_novos_fluxos.json'
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(completed,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Nove conjuntos verificados pela interface Tk oculta, incluindo as novas alternativas.')


if __name__=='__main__':main()
