"""Contrato JSON para modelos lineares numéricos com intercepto."""
import math

REGRESSION_METHOD='regression.linear.numeric.v1'


def validate_regression_parameters(parameters, column_count):
    if (not isinstance(parameters,dict) or set(parameters)!={'confidence','observations','store','show_graph'}
            or type(parameters['confidence']) not in (int,float)
            or not math.isfinite(parameters['confidence']) or not 0<parameters['confidence']<100
            or any(type(parameters[k]) is not bool for k in ('observations','store','show_graph'))
            or column_count<2):
        raise ValueError('Parâmetros da regressão inválidos.')


def validate_linear_model(model, column_count):
    try:
        width=column_count-1;k=width+1;n=model['n']
        if type(n) is not int or n<=k or type(model['perfect']) is not bool:
            raise ValueError('Tamanho/estado do modelo linear inválido.')
        if (not isinstance(model['response'],str) or not model['response'].strip()
                or not isinstance(model['predictors'],list) or len(model['predictors'])!=width
                or any(not isinstance(v,str) or not v.strip() for v in model['predictors'])):
            raise ValueError('Variáveis do modelo linear inválidas.')
        finite=lambda value:type(value) in (int,float) and math.isfinite(value)

        def vector(values,size,nullable=False):
            if not isinstance(values,list) or len(values)!=size or any(not finite(v) and not (nullable and v is None) for v in values):
                raise ValueError('Vetor do modelo linear inválido.')

        for key in ('fitted','residuals','observed','leverage'):
            vector(model[key],n)
        for key in ('standardized','cooks'):vector(model[key],n,True)
        for key in ('ss_model','ss_error','ss_total','ms_error','s','condition','confidence'):
            if not finite(model[key]) or model[key]<0:raise ValueError('Escala do modelo linear inválida.')
        if not 0<model['confidence']<100:raise ValueError('Confiança do modelo inválida.')
        for key in ('f','p','r2','adjusted','press','predicted'):
            if model[key] is not None and not finite(model[key]):raise ValueError('Estatística do modelo inválida.')
        if (any(type(model[key]) is not int for key in ('df_model','df_error','df_total','excluded'))
                or model['df_model']!=width or model['df_error']!=n-k or model['df_total']!=n-1 or model['excluded']<0):
            raise ValueError('Graus de liberdade do modelo inválidos.')
        positions=model['row_numbers']
        if (not isinstance(positions,list) or len(positions)!=n
                or any(type(v) is not int or v<1 for v in positions)
                or positions!=sorted(set(positions))):raise ValueError('Linhas do ajuste inválidas.')
        if any(not 0<=v<=1 for v in model['leverage']):raise ValueError('Alavancagem inválida.')
        if not isinstance(model['x'],list) or len(model['x'])!=n:raise ValueError('Matriz do modelo inválida.')
        for row in model['x']:vector(row,width)
        if not isinstance(model['terms'],list) or len(model['terms'])!=k:raise ValueError('Termos do modelo inválidos.')
        for term in model['terms']:
            if not isinstance(term['label'],str):raise ValueError('Rótulo de termo inválido.')
            for key in ('coefficient','se','low','high'):
                if not finite(term[key]):raise ValueError('Coeficiente do modelo inválido.')
            if term['se']<0 or term['low']>term['high']:raise ValueError('Intervalo de coeficiente inválido.')
            for key in ('t','p','vif'):
                if term[key] is not None and not finite(term[key]):raise ValueError('Diagnóstico de coeficiente inválido.')
        state=model['prediction_state']
        for key in ('x_mean','x_scale'):vector(state[key],width)
        vector(state['coefficients'],k)
        if any(v<=0 for v in state['x_scale']) or not finite(state['y_mean']) or not finite(state['y_scale']) or state['y_scale']<=0:
            raise ValueError('Normalização da previsão inválida.')
        if not isinstance(state['inverse_factor'],list) or len(state['inverse_factor'])!=k:
            raise ValueError('Fator de previsão inválido.')
        for row in state['inverse_factor']:vector(row,k)
    except (KeyError,TypeError,AttributeError,OverflowError) as error:
        raise ValueError('Contrato de modelo linear incompleto.') from error
    return model
