"""Regressão persistente, restauração e reexecução sem dependência de Tk."""
from copy import deepcopy
from datetime import datetime, timezone
import platform

from linear_models import linear_regression, format_regression
from workspace_model import identifier, fingerprint, input_fingerprint, pack_numbers, unpack_numbers, is_stale
from regression_contract import REGRESSION_METHOD, validate_regression_parameters, validate_linear_model
from updates import load_metadata


def execute_regression(sheet,column_ids,confidence=95.,observations=False,store=False,show_graph=True,parent_analysis_id=None):
    parameters=dict(confidence=confidence,observations=observations,store=store,show_graph=show_graph)
    validate_regression_parameters(parameters,len(column_ids))
    if sheet['fingerprint']!=fingerprint(sheet):raise ValueError('Sincronize a planilha antes de ajustar.')
    if len(set(column_ids))!=len(column_ids):raise ValueError('Use resposta e preditores distintos.')
    indices=[]
    for key in column_ids:
        found=[i for i,c in enumerate(sheet['columns']) if c['id']==key]
        if len(found)!=1:raise ValueError('Uma variável original foi removida; inicie outro ajuste.')
        indices.append(found[0])
    model=linear_regression([c['name'] for c in sheet['columns']],sheet['rows'],indices[0],indices[1:],confidence=confidence)
    validate_linear_model(model,len(column_ids))
    import scipy,numpy
    return dict(analysis_id=identifier('analysis'),parent_analysis_id=parent_analysis_id,
                method_id=REGRESSION_METHOD,created_at=datetime.now(timezone.utc).isoformat(),parameters=parameters,
                source=dict(worksheet_id=sheet['id'],column_ids=list(column_ids),revision=sheet['revision'],
                            fingerprint=sheet['fingerprint'],input_fingerprint=input_fingerprint(sheet,column_ids),kind='columns'),
                versions=dict(application=load_metadata()['version'],method=1,python=platform.python_version(),scipy=scipy.__version__,numpy=numpy.__version__),
                missing=dict(policy='complete_rows_response_and_predictors',count=model['excluded'],retained_rows=model['row_numbers']),
                values=pack_numbers(model),tables=[dict(name='coeficientes',rows=pack_numbers(model['terms']))],
                scenes=[dict(kind='regression_diagnostics',version=1)],
                warnings=['Validação diferencial Minitab 16 pendente.'],status='completed',
                provenance=dict(origin='MiniTaBom',reference16='pending'),report=format_regression(model,observations))


def archived_model(result):
    if result['method_id']!=REGRESSION_METHOD:raise ValueError('Selecione um modelo linear no histórico.')
    validate_regression_parameters(result['parameters'],len(result['source']['column_ids']))
    model=deepcopy(unpack_numbers(result['values']))
    return validate_linear_model(model,len(result['source']['column_ids']))


def model_for_prediction(result,sheet):
    model=archived_model(result)
    if result['source']['worksheet_id']!=sheet['id'] or is_stale(result,sheet):
        raise ValueError('As variáveis de origem mudaram ou foram removidas. Reexecute o ajuste antes de prever.')
    labels={c['id']:c['name'] for c in sheet['columns']}
    names=[labels[key] for key in result['source']['column_ids']]
    model['response'],model['predictors']=names[0],names[1:]
    for term,label in zip(model['terms'],['Constante',*names[1:]]):term['label']=label
    return model
