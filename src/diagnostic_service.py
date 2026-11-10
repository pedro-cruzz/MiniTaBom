"""Diagnósticos persistentes; cálculos existentes e fontes por IDs."""
from datetime import datetime,timezone
import platform

from core import numeric_column
from normality import analyze_normality,format_normality
from study_tests import analyze_study,format_study
from workspace_model import identifier,fingerprint,input_fingerprint,pack_numbers
from diagnostic_contract import NORMALITY_METHOD,STUDY_METHODS,validate_diagnostic_parameters,validate_diagnostic_result
from updates import load_metadata


def _indices(sheet,column_ids):
    if sheet['fingerprint']!=fingerprint(sheet):raise ValueError('Sincronize a planilha antes do diagnóstico.')
    if len(set(column_ids))!=len(column_ids):raise ValueError('Selecione colunas distintas.')
    indices=[]
    for key in column_ids:
        found=[i for i,c in enumerate(sheet['columns']) if c['id']==key]
        if len(found)!=1:raise ValueError('Coluna original removida; inicie outra análise.')
        indices.append(found[0])
    return indices


def _record(sheet,column_ids,method_id,parameters,values,report,missing,scenes,parent_analysis_id):
    import scipy
    result=dict(analysis_id=identifier('analysis'),parent_analysis_id=parent_analysis_id,method_id=method_id,
                created_at=datetime.now(timezone.utc).isoformat(),parameters=parameters,
                source=dict(worksheet_id=sheet['id'],column_ids=list(column_ids),revision=sheet['revision'],fingerprint=sheet['fingerprint'],
                            input_fingerprint=input_fingerprint(sheet,column_ids),kind='columns'),
                versions=dict(application=load_metadata()['version'],method=1,python=platform.python_version(),scipy=scipy.__version__),
                missing=missing,values=pack_numbers(values),tables=[dict(name='diagnostico',rows=pack_numbers(values.get('summaries',[values])))],
                scenes=scenes,warnings=['Validação diferencial Minitab 16 pendente.'],status='completed',
                provenance=dict(origin='MiniTaBom',reference16='pending'),report=report)
    validate_diagnostic_result(result)
    return result


def execute_normality(sheet,column_ids,method='ad',show_graph=False,parent_analysis_id=None):
    parameters=dict(method=method,show_graph=show_graph)
    validate_diagnostic_parameters(NORMALITY_METHOD,parameters,len(column_ids))
    indices=_indices(sheet,column_ids);headers=[c['name'] for c in sheet['columns']]
    values=analyze_normality(headers,sheet['rows'],indices[0],method=method)
    sample,_=numeric_column(sheet['rows'],indices[0])
    return _record(sheet,column_ids,NORMALITY_METHOD,parameters,values,format_normality(values),
                   dict(policy='omit_empty_or_star',count=values['missing']),
                   [dict(kind='normal_probability',version=1,sample=sample)],parent_analysis_id)


def execute_study(sheet,column_ids,mode,input_kind='columns',group_order=None,alternative='two-sided',method='auto',
                  correction=True,zero_method='wilcox',center='median',parent_analysis_id=None):
    method_id=next((key for key,value in STUDY_METHODS.items() if value==mode),None)
    indices=_indices(sheet,column_ids)
    if input_kind=='stacked' and group_order is None and len(indices)==2:
        group_order=list(dict.fromkeys(str(row[indices[1]]).strip() for row in sheet['rows'] if str(row[indices[1]]).strip() not in ('','*')))
    if isinstance(group_order,list):group_order=list(group_order)
    parameters=dict(mode=mode,input_kind=input_kind,group_order=group_order,alternative=alternative,method=method,
                    correction=correction,zero_method=zero_method,center=center)
    validate_diagnostic_parameters(method_id,parameters,len(column_ids))
    selection=dict(columns=indices) if input_kind=='columns' else dict(response=indices[0],factor=indices[1],group_order=group_order)
    values=analyze_study([c['name'] for c in sheet['columns']],sheet['rows'],mode,**selection,
                         alternative=alternative,method=method,correction=correction,zero_method=zero_method,center=center)
    return _record(sheet,column_ids,method_id,parameters,values,format_study(values),
                   dict(policy='pairwise' if mode=='wilcoxon' else 'per_group',count=values['excluded']),[],parent_analysis_id)
