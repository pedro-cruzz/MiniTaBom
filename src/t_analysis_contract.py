"""IDs e parâmetros persistidos; independente de Tk, IO e cálculo."""
import math

T_ONE_METHOD='basic.t_one.column.v1'
T_METHODS={T_ONE_METHOD:('one','columns'),
           'basic.t_one.summary.v1':('one','summary'),
           'basic.t_paired.columns.v1':('paired','columns'),
           'basic.t_paired.summary.v1':('paired','summary'),
           'basic.t_two.columns.v1':('two','columns'),
           'basic.t_two.stacked.v1':('two','stacked'),
           'basic.t_two.summary.v1':('two','summary')}


def validate_t_parameters(method_id, parameters, column_count):
    if method_id not in T_METHODS:
        raise ValueError('Método t não suportado.')
    mode,source=T_METHODS[method_id]
    basic={'null','confidence','alternative','perform_test'}
    expected=basic if method_id==T_ONE_METHOD else basic|{'equal_var','legacy_df','summaries','group_order','store_differences'}
    if not isinstance(parameters,dict) or set(parameters)!=expected:
        raise ValueError('Parâmetros do teste t incompletos.')
    if (type(parameters['null']) not in (int,float) or not math.isfinite(parameters['null'])
            or type(parameters['confidence']) not in (int,float) or not math.isfinite(parameters['confidence'])
            or not 0<parameters['confidence']<100 or type(parameters['perform_test']) is not bool
            or parameters['alternative'] not in ('two-sided','less','greater')):
        raise ValueError('Parâmetros do teste t inválidos.')
    expected_count=0 if source=='summary' else 1 if mode=='one' else 2
    if column_count!=expected_count:
        raise ValueError('Referências de colunas incompatíveis com o teste t.')
    if method_id==T_ONE_METHOD:return mode,source
    if any(type(parameters[k]) is not bool for k in ('equal_var','legacy_df','store_differences')):
        raise ValueError('Opções booleanas do teste t inválidas.')
    if parameters['store_differences'] and (mode!='paired' or source!='columns'):
        raise ValueError('Armazenar diferenças exige colunas pareadas.')
    summaries=parameters['summaries']
    if source=='summary':
        if not isinstance(summaries,list) or len(summaries)!=(2 if mode=='two' else 1):
            raise ValueError('Resumos incompatíveis com o teste t.')
        for summary in summaries:
            if (not isinstance(summary,dict) or set(summary)!={'n','mean','sd'}
                    or type(summary['n']) is not int or not 2<=summary['n']<=2147483647
                    or any(type(summary[k]) not in (float,int) or not math.isfinite(summary[k]) for k in ('mean','sd'))
                    or summary['sd']<0):
                raise ValueError('Resumo amostral inválido.')
    elif summaries is not None:raise ValueError('Resumo inesperado para entrada em colunas.')
    order=parameters['group_order']
    if source=='stacked':
        if (not isinstance(order,list) or len(order)!=2
                or any(not isinstance(v,str) or v.strip() in ('','*') for v in order) or order[0]==order[1]):
            raise ValueError('Ordem dos grupos inválida.')
    elif order is not None:raise ValueError('Grupos inesperados neste teste t.')
    return mode,source
