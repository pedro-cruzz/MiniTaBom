"""Contrato JSON de previsões vinculadas a um modelo imutável."""
import math

PREDICTION_METHOD='regression.prediction.v1'


def validate_prediction_parameters(parameters,width):
    expected={'model_analysis_id','input_kind','cases','case_numbers','input_column_ids','omit_missing','confidence','alternative'}
    finite=lambda v:type(v) in (int,float) and math.isfinite(v)
    if (not isinstance(parameters,dict) or set(parameters)!=expected
            or not isinstance(parameters['model_analysis_id'],str) or not parameters['model_analysis_id']
            or parameters['input_kind'] not in ('cases','columns') or type(parameters['omit_missing']) is not bool
            or not finite(parameters['confidence']) or not 0<parameters['confidence']<100
            or parameters['alternative'] not in ('two-sided','lower','upper')):
        raise ValueError('Parâmetros de previsão inválidos.')
    columns=parameters['input_column_ids']
    if not isinstance(columns,list) or any(not isinstance(c,str) or not c for c in columns):
        raise ValueError('Mapeamento da previsão inválido.')
    if parameters['input_kind']=='cases':
        cases,numbers=parameters['cases'],parameters['case_numbers']
        if (columns or not isinstance(cases,list) or not cases
                or any(not isinstance(row,list) or len(row)!=width or any(not finite(v) for v in row) for row in cases)
                or not isinstance(numbers,list) or len(numbers)!=len(cases)
                or any(type(n) is not int or n<1 for n in numbers) or len(set(numbers))!=len(numbers)):
            raise ValueError('Casos de previsão inválidos.')
    elif len(columns)!=width or parameters['cases'] is not None or parameters['case_numbers'] is not None:
        raise ValueError('Formato de previsão por colunas inválido.')


def validate_prediction_values(values,parameters,model):
    try:
        finite=lambda v:type(v) in (float,int) and math.isfinite(v)
        width=len(model['predictors'])
        if (values['n']!=model['n'] or type(values['n']) is not int
                or values['response']!=model['response'] or values['predictors']!=model['predictors']
                or values['confidence']!=parameters['confidence'] or values['alternative']!=parameters['alternative']
                or type(values['perfect']) is not bool or values['perfect']!=model['perfect']
                or not isinstance(values['source'],str) or not isinstance(values['cases'],list) or not values['cases']):
            raise ValueError('Resultado de previsão incompatível com o modelo.')
        numbers=[]
        for case in values['cases']:
            if type(case['case']) is not int or case['case']<1:raise ValueError('Número de caso inválido.')
            numbers.append(case['case'])
            if (not isinstance(case['values'],list) or len(case['values'])!=width or any(not finite(v) for v in case['values'])
                    or any(not finite(case[k]) for k in ('fit','se_fit','leverage')) or case['se_fit']<0 or case['leverage']<0
                    or type(case['high_leverage']) is not bool or not isinstance(case['outside'],list)
                    or any(v not in model['predictors'] for v in case['outside'])):
                raise ValueError('Valores de previsão inválidos.')
            for key in ('ci','pi'):
                bounds=case[key]
                if not isinstance(bounds,(list,tuple)) or len(bounds)!=2:raise ValueError('Intervalo de previsão inválido.')
                low,high=bounds
                if not finite(low) and not (parameters['alternative']=='upper' and low==-math.inf):raise ValueError('Limite inferior inválido.')
                if not finite(high) and not (parameters['alternative']=='lower' and high==math.inf):raise ValueError('Limite superior inválido.')
                if low>case['fit'] or high<case['fit']:raise ValueError('Intervalo não contém a estimativa.')
        omitted=values['omitted']
        if (len(set(numbers))!=len(numbers) or not isinstance(omitted,list)
                or any(type(n) is not int or n<1 for n in omitted) or len(set(omitted))!=len(omitted)
                or set(numbers)&set(omitted)):
            raise ValueError('Linhas/casos de previsão inválidos.')
        if parameters['input_kind']=='cases':
            if omitted or numbers!=parameters['case_numbers'] or [c['values'] for c in values['cases']]!=parameters['cases']:
                raise ValueError('Os casos calculados não correspondem aos parâmetros.')
    except (KeyError,TypeError,AttributeError,OverflowError) as error:
        raise ValueError('Resultado de previsão incompleto.') from error

