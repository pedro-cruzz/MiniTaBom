from copy import deepcopy
from datetime import datetime,timezone
import platform

from two_poisson import two_poisson,analyze_two_poisson,format_two_poisson
from two_poisson_contract import TWO_POISSON_METHOD,validate_two_poisson_parameters,validate_two_poisson_result
from workspace_model import identifier,fingerprint,input_fingerprint,pack_numbers
from updates import load_metadata


def execute_two_poisson(sheet,column_ids=None,input_kind='columns',summaries=None,group_order=None,lengths=None,
                        null=0.,confidence=95.,alternative='two-sided',pooled=False,measure='rate',perform_test=True,parent_analysis_id=None):
    if sheet['fingerprint']!=fingerprint(sheet):raise ValueError('Sincronize a planilha antes do teste.')
    column_ids=list(column_ids or []);lengths=[1.,1.] if lengths is None else list(lengths)
    if len(set(column_ids))!=len(column_ids):raise ValueError('Use colunas distintas.')
    indices=[]
    for key in column_ids:
        found=[i for i,c in enumerate(sheet['columns']) if c['id']==key]
        if len(found)!=1:raise ValueError('Coluna original de Poisson removida; inicie outra análise.')
        indices.append(found[0])
    if input_kind=='stacked' and group_order is None and len(indices)==2:
        group_order=list(dict.fromkeys(str(r[indices[1]]).strip() for r in sheet['rows'] if str(r[indices[1]]).strip() not in ('','*')))
    parameters=dict(input_kind=input_kind,summaries=deepcopy(summaries),group_order=deepcopy(group_order),lengths=lengths,
                    null=null,confidence=confidence,alternative=alternative,pooled=pooled,measure=measure,perform_test=perform_test)
    validate_two_poisson_parameters(parameters,len(column_ids))
    options=dict(length1=lengths[0],length2=lengths[1],null=null,confidence=confidence,alternative=alternative,
                 pooled=pooled,measure=measure,perform_test=perform_test)
    if input_kind=='summary':
        values=two_poisson(summaries[0]['events'],summaries[0]['n'],summaries[1]['events'],summaries[1]['n'],**options)
        for sample in values['samples']:sample['missing']=None
    else:
        values=analyze_two_poisson([c['name'] for c in sheet['columns']],sheet['rows'],indices if input_kind=='columns' else indices[:1],
                                   source=input_kind,group=indices[1] if input_kind=='stacked' else None,group_order=group_order,**options)
    source=dict(worksheet_id=sheet['id'],column_ids=column_ids,revision=sheet['revision'],fingerprint=sheet['fingerprint'],
                kind='summary' if input_kind=='summary' else 'columns')
    if input_kind!='summary':source['input_fingerprint']=input_fingerprint(sheet,column_ids)
    import scipy
    result=dict(analysis_id=identifier('analysis'),parent_analysis_id=parent_analysis_id,method_id=TWO_POISSON_METHOD,
                created_at=datetime.now(timezone.utc).isoformat(),parameters=parameters,source=source,
                versions=dict(application=load_metadata()['version'],method=1,python=platform.python_version(),scipy=scipy.__version__),
                missing=dict(policy='unknown_summary' if input_kind=='summary' else 'omit_per_sample',counts=[s['missing'] for s in values['samples']],excluded_groups=values['excluded_groups']),
                values=pack_numbers(values),tables=[dict(name='amostras',rows=pack_numbers(values['samples']))],
                warnings=values['warnings']+['Validação diferencial Minitab 16 pendente.'],status='completed',
                provenance=dict(origin='MiniTaBom',reference16='pending'),report=format_two_poisson(values))
    # Validation consumes decoded numbers, while persistence uses explicit infinity tags.
    from workspace_model import unpack_numbers
    validate_two_poisson_result(dict(result,values=unpack_numbers(result['values'])))
    return result
