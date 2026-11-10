"""Previsões persistentes: modelo fixo e casos salvos ou colunas atuais."""
from copy import deepcopy
from datetime import datetime,timezone
import platform

from prediction import predict_linear,predict_columns,format_predictions
from prediction_contract import PREDICTION_METHOD,validate_prediction_parameters,validate_prediction_values
from regression_service import archived_model
from workspace_model import identifier,pack_numbers,fingerprint,input_fingerprint
from updates import load_metadata


def execute_prediction(document,model_analysis_id,worksheet_id,input_kind='cases',cases=None,case_numbers=None,
                       input_column_ids=None,omit_missing=True,confidence=None,alternative='two-sided',parent_analysis_id=None):
    records=[r for r in document['analyses'] if r['analysis_id']==model_analysis_id]
    sheets=[s for s in document['worksheets'] if s['id']==worksheet_id]
    if len(records)!=1 or len(sheets)!=1:raise ValueError('Modelo ou planilha de previsão não encontrado.')
    record,sheet=records[0],sheets[0];model=archived_model(record)
    if sheet['fingerprint']!=fingerprint(sheet):raise ValueError('Sincronize a planilha antes de prever.')
    cases=deepcopy(cases)
    if input_kind=='cases' and case_numbers is None and isinstance(cases,list):case_numbers=list(range(1,len(cases)+1))
    parameters=dict(model_analysis_id=model_analysis_id,input_kind=input_kind,cases=cases,case_numbers=deepcopy(case_numbers),
                    input_column_ids=list(input_column_ids or []),omit_missing=omit_missing,
                    confidence=model['confidence'] if confidence is None else confidence,alternative=alternative)
    validate_prediction_parameters(parameters,len(model['predictors']))
    columns=[]
    if input_kind=='columns':
        for key in parameters['input_column_ids']:
            matches=[i for i,c in enumerate(sheet['columns']) if c['id']==key]
            if len(matches)!=1:raise ValueError('Coluna de previsão removida; inicie uma nova previsão.')
            columns.append(matches[0])
        values=predict_columns(model,[c['name'] for c in sheet['columns']],sheet['rows'],columns,
                               omit_missing=omit_missing,confidence=parameters['confidence'],alternative=alternative)
    else:
        values=predict_linear(model,cases,confidence=parameters['confidence'],alternative=alternative,case_numbers=parameters['case_numbers'])
    validate_prediction_values(values,parameters,model)
    column_ids=list(dict.fromkeys(parameters['input_column_ids']))
    source=dict(worksheet_id=worksheet_id,column_ids=column_ids,revision=sheet['revision'],fingerprint=sheet['fingerprint'],
                kind='fixed_prediction' if input_kind=='cases' else 'prediction_columns')
    if input_kind=='columns':source['input_fingerprint']=input_fingerprint(sheet,column_ids)
    import scipy,numpy
    report=format_predictions(values)+'\nModelo fixado ao ajuste de '+record['created_at']+'.\nRecalcular esta previsão mantém esse modelo, sem novo ajuste.\n'
    return dict(analysis_id=identifier('analysis'),parent_analysis_id=parent_analysis_id,method_id=PREDICTION_METHOD,
                created_at=datetime.now(timezone.utc).isoformat(),parameters=parameters,source=source,
                versions=dict(application=load_metadata()['version'],method=1,python=platform.python_version(),scipy=scipy.__version__,numpy=numpy.__version__),
                missing=dict(policy='omit_incomplete_cases' if omit_missing else 'reject_incomplete_cases',rows=values['omitted']),
                values=pack_numbers(values),tables=[dict(name='previsoes',rows=pack_numbers(values['cases']))],
                warnings=['Validação diferencial Minitab 16 pendente.'],status='completed',
                provenance=dict(origin='MiniTaBom',reference16='pending',model_analysis_id=model_analysis_id),report=report)
