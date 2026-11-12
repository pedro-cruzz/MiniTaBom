"""Serviços de testes t reexecutáveis; sem dependência de Tk."""
from copy import deepcopy
from datetime import datetime, timezone
import platform

from inference import analyze_t_inputs, format_t_report
from updates import load_metadata
from workspace_model import identifier, pack_numbers, fingerprint, input_fingerprint
from t_analysis_contract import T_ONE_METHOD, T_METHODS, validate_t_parameters


def execute_t_one(sheet, column_id, null=0., confidence=95., alternative='two-sided',
                  perform_test=True, parent_analysis_id=None):
    return execute_t(sheet,'one',[column_id],null=null,confidence=confidence,
                     alternative=alternative,perform_test=perform_test,parent_analysis_id=parent_analysis_id)


def execute_t(sheet, mode, column_ids=None, source='columns', summaries=None, null=0.,
              confidence=95., alternative='two-sided', perform_test=True, equal_var=False,
              legacy_df=True, group_order=None, store_differences=False, parent_analysis_id=None):
    methods=[key for key,value in T_METHODS.items() if value==(mode,source)]
    if len(methods)!=1:raise ValueError('Formato de teste t não suportado.')
    method_id=methods[0]
    if sheet['fingerprint'] != fingerprint(sheet):
        raise ValueError('Sincronize a revisão da planilha antes de calcular.')
    column_ids=[] if column_ids is None else list(column_ids)
    if len(set(column_ids))!=len(column_ids):raise ValueError('Use colunas distintas.')
    indices=[]
    for column_id in column_ids:
        matches=[i for i,c in enumerate(sheet['columns']) if c['id']==column_id]
        if len(matches)!=1:raise ValueError('A coluna original não está mais disponível; inicie uma nova análise.')
        indices.append(matches[0])
    if source=='stacked' and group_order is None and len(indices)==2:
        group_order=list(dict.fromkeys(str(row[indices[1]]).strip() for row in sheet['rows']
                                       if str(row[indices[1]]).strip() not in ('','*')))
    parameters=dict(null=null,confidence=confidence,alternative=alternative,perform_test=perform_test)
    if method_id!=T_ONE_METHOD:
        parameters.update(equal_var=equal_var,legacy_df=legacy_df,summaries=deepcopy(summaries),
                          group_order=deepcopy(group_order),store_differences=store_differences)
    elif store_differences:raise ValueError('Armazenar diferenças exige colunas pareadas.')
    validate_t_parameters(method_id,parameters,len(column_ids))
    headers=[c['name'] for c in sheet['columns']]
    values=analyze_t_inputs(headers,sheet['rows'],mode,*(indices+[None,None])[:2],source=source,
                            summaries=summaries,null=null,confidence=confidence,alternative=alternative,
                            equal_var=equal_var,legacy_df=legacy_df,group_order=group_order)
    report=format_t_report(values,perform_test=perform_test)
    import scipy
    origin=dict(worksheet_id=sheet['id'],column_ids=column_ids,revision=sheet['revision'],
                fingerprint=sheet['fingerprint'],kind=source)
    if source!='summary':origin['input_fingerprint']=input_fingerprint(sheet,column_ids)
    policy=('summary_missing_unknown' if source=='summary' else 'omit_pair_if_either_missing' if mode=='paired'
            else 'omit_group_then_sample' if source=='stacked' else 'omit_empty_or_star' if mode=='one' else 'omit_each_sample')
    missing=dict(policy=policy,counts=values['missing'])
    if source=='stacked':missing['excluded_groups']=values['excluded_groups']
    return dict(analysis_id=identifier('analysis'),parent_analysis_id=parent_analysis_id,
                method_id=method_id,created_at=datetime.now(timezone.utc).isoformat(),
                parameters=parameters,source=origin,
                versions=dict(application=load_metadata()['version'],method=1,
                              python=platform.python_version(),scipy=scipy.__version__),
                missing=missing,
                values=pack_numbers(values),tables=[dict(name='amostras',rows=pack_numbers(values['samples']))],
                warnings=['Validação diferencial Minitab 16 pendente.'],status='completed',
                provenance=dict(origin='MiniTaBom',reference16='pending'),report=report)


def rerun_analysis(document, analysis_id):
    results=[r for r in document['analyses'] if r['analysis_id']==analysis_id]
    if len(results)!=1:raise ValueError('Análise não encontrada.')
    result=results[0]
    from random_contract import RANDOM_METHOD
    if result['method_id'] == RANDOM_METHOD:
        from random_service import replay_random
        return replay_random(document, result)
    from two_poisson_contract import TWO_POISSON_METHOD
    if result['method_id']==TWO_POISSON_METHOD:
        from two_poisson_service import execute_two_poisson
        sheet=next((s for s in document['worksheets'] if s['id']==result['source']['worksheet_id']),None)
        if sheet is None:raise ValueError('Planilha de Poisson não encontrada.')
        return execute_two_poisson(sheet,result['source']['column_ids'],**result['parameters'],parent_analysis_id=analysis_id)
    from diagnostic_contract import NORMALITY_METHOD,STUDY_METHODS
    if result['method_id']==NORMALITY_METHOD or result['method_id'] in STUDY_METHODS:
        from diagnostic_service import execute_normality,execute_study
        sheet=next((s for s in document['worksheets'] if s['id']==result['source']['worksheet_id']),None)
        if sheet is None:raise ValueError('Planilha do diagnóstico não encontrada.')
        function=execute_normality if result['method_id']==NORMALITY_METHOD else execute_study
        return function(sheet,result['source']['column_ids'],**result['parameters'],parent_analysis_id=analysis_id)
    from anova_contract import ANOVA_METHOD
    if result['method_id']==ANOVA_METHOD:
        from anova_service import execute_anova
        sheet=next((s for s in document['worksheets'] if s['id']==result['source']['worksheet_id']),None)
        if sheet is None:raise ValueError('Planilha da ANOVA não encontrada.')
        return execute_anova(sheet,result['source']['column_ids'],**result['parameters'],parent_analysis_id=analysis_id)
    from prediction_contract import PREDICTION_METHOD
    if result['method_id']==PREDICTION_METHOD:
        from prediction_service import execute_prediction
        return execute_prediction(document,worksheet_id=result['source']['worksheet_id'],
                                  **result['parameters'],parent_analysis_id=analysis_id)
    from regression_contract import REGRESSION_METHOD
    if result['method_id']==REGRESSION_METHOD:
        from regression_service import execute_regression
        sheets=[s for s in document['worksheets'] if s['id']==result['source']['worksheet_id']]
        if len(sheets)!=1:raise ValueError('Planilha original não encontrada.')
        return execute_regression(sheets[0],result['source']['column_ids'],**result['parameters'],parent_analysis_id=analysis_id)
    if result['method_id'] not in T_METHODS:
        raise ValueError('Este método ainda não possui reexecução estruturada.')
    mode,source=T_METHODS[result['method_id']]
    sheets=[s for s in document['worksheets'] if s['id']==result['source']['worksheet_id']]
    if len(sheets)!=1:raise ValueError('Planilha original não encontrada.')
    validate_t_parameters(result['method_id'],result['parameters'],len(result['source']['column_ids']))
    return execute_t(sheets[0],mode,result['source']['column_ids'],source=source,
                     **result['parameters'],parent_analysis_id=analysis_id)
