"""ANOVA persistente: grupos, opções, comparações e boxplots históricos."""
from datetime import datetime,timezone
import platform

from anova import prepare_groups,one_way,format_anova_report
from anova_contract import ANOVA_METHOD,validate_anova_parameters,validate_anova_result
from workspace_model import identifier,fingerprint,input_fingerprint,pack_numbers
from updates import load_metadata


def execute_anova(sheet,column_ids,input_kind='columns',group_order=None,equal_var=True,confidence=95.,
                  comparisons=False,comparison_method='tukey',show_graph=False,parent_analysis_id=None):
    if sheet['fingerprint']!=fingerprint(sheet):raise ValueError('Sincronize a planilha antes da ANOVA.')
    if len(set(column_ids))!=len(column_ids):raise ValueError('Use colunas distintas na ANOVA.')
    indices=[]
    for key in column_ids:
        found=[i for i,c in enumerate(sheet['columns']) if c['id']==key]
        if len(found)!=1:raise ValueError('Coluna original da ANOVA removida; inicie nova análise.')
        indices.append(found[0])
    if input_kind=='stacked' and group_order is None and len(indices)==2:
        group_order=list(dict.fromkeys(str(row[indices[1]]).strip() for row in sheet['rows'] if str(row[indices[1]]).strip() not in ('','*')))
    if isinstance(group_order,list):group_order=list(group_order)
    parameters=dict(input_kind=input_kind,group_order=group_order,equal_var=equal_var,confidence=confidence,
                    comparisons=comparisons,comparison_method=comparison_method,show_graph=show_graph)
    validate_anova_parameters(parameters,len(column_ids))
    headers=[c['name'] for c in sheet['columns']]
    groups,excluded=(prepare_groups(headers,sheet['rows'],columns=indices) if input_kind=='columns' else
                     prepare_groups(headers,sheet['rows'],response=indices[0],factor=indices[1],group_order=group_order))
    values=one_way(groups,equal_var=equal_var,confidence=confidence,comparisons=comparisons,comparison_method=comparison_method)
    import scipy
    result=dict(analysis_id=identifier('analysis'),parent_analysis_id=parent_analysis_id,method_id=ANOVA_METHOD,
                created_at=datetime.now(timezone.utc).isoformat(),parameters=parameters,
                source=dict(worksheet_id=sheet['id'],column_ids=list(column_ids),revision=sheet['revision'],fingerprint=sheet['fingerprint'],
                            input_fingerprint=input_fingerprint(sheet,column_ids),kind='columns'),
                versions=dict(application=load_metadata()['version'],method=1,python=platform.python_version(),scipy=scipy.__version__),
                missing=dict(policy='per_group' if input_kind=='columns' else 'omit_missing_factor_then_response',count=excluded),
                values=pack_numbers(values),tables=[dict(name='grupos',rows=pack_numbers(values['groups'])),dict(name='comparacoes',rows=pack_numbers(values['comparisons']))],
                scenes=[dict(kind='group_boxplot',version=1,groups=pack_numbers(groups),response_label=headers[indices[0]] if input_kind=='stacked' else 'Valores')],
                warnings=['Validação diferencial Minitab 16 pendente.'],status='completed',
                provenance=dict(origin='MiniTaBom',reference16='pending'),report=format_anova_report(values,excluded))
    validate_anova_result(result)
    return result
