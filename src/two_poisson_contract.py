"""Contrato de duas taxas Poisson, independente do cálculo/Tk."""
import math

TWO_POISSON_METHOD='basic.poisson.two.v1'


def validate_two_poisson_parameters(parameters,column_count):
    try:
        if (set(parameters)!={'input_kind','summaries','group_order','lengths','null','confidence','alternative','pooled','measure','perform_test'}
                or parameters['input_kind'] not in ('columns','stacked','summary')
                or parameters['alternative'] not in ('two-sided','less','greater') or parameters['measure'] not in ('rate','mean')
                or any(type(parameters[k]) is not bool for k in ('pooled','perform_test'))
                or any(type(parameters[k]) not in (int,float) or not math.isfinite(parameters[k]) for k in ('null','confidence'))
                or not 0<parameters['confidence']<100 or (parameters['pooled'] and parameters['null']!=0)):
            raise ValueError('Parâmetros de duas taxas Poisson inválidos.')
        lengths=parameters['lengths']
        if not isinstance(lengths,list) or len(lengths)!=2 or any(type(v) not in (int,float) or not math.isfinite(v) or v<=0 for v in lengths):
            raise ValueError('Exposições inválidas.')
        kind=parameters['input_kind'];summaries=parameters['summaries'];order=parameters['group_order']
        if column_count!=(0 if kind=='summary' else 2):raise ValueError('Colunas incompatíveis com o formato.')
        if kind=='summary':
            if not isinstance(summaries,list) or len(summaries)!=2:raise ValueError('Informe dois resumos.')
            for s in summaries:
                if (not isinstance(s,dict) or set(s)!={'events','n'} or type(s['events']) is not int or type(s['n']) is not int
                        or not 0<=s['events']<=2147483647 or not 1<=s['n']<=2147483647):raise ValueError('Resumo Poisson inválido.')
        elif summaries is not None:raise ValueError('Resumo inesperado neste formato.')
        if kind=='stacked':
            if not isinstance(order,list) or len(order)!=2 or any(not isinstance(v,str) or v.strip() in ('','*') for v in order) or order[0]==order[1]:
                raise ValueError('Ordem dos grupos inválida.')
        elif order is not None:raise ValueError('Grupos inesperados neste formato.')
    except (KeyError,TypeError,OverflowError) as error:raise ValueError('Parâmetros Poisson incompletos.') from error


def validate_two_poisson_result(result):
    try:
        p=result['parameters'];v=result['values'];samples=v['samples']
        finite=lambda x:type(x) in (int,float) and math.isfinite(x)
        if not isinstance(samples,list) or len(samples)!=2:raise ValueError('Amostras Poisson inválidas.')
        for i,s in enumerate(samples):
            if (type(s['n']) is not int or not 1<=s['n']<=2147483647 or type(s['events']) is not int or not 0<=s['events']<=2147483647
                    or not isinstance(s['name'],str) or not s['name'] or s['length']!=p['lengths'][i]
                    or any(not finite(s[k]) or s[k]<0 for k in ('rate','mean','exposure')) or s['exposure']<=0
                    or (s['missing'] is not None and (type(s['missing']) is not int or s['missing']<0))):
                raise ValueError('Resumo de amostra Poisson inválido.')
            if p['input_kind']=='summary' and (s['n']!=p['summaries'][i]['n'] or s['events']!=p['summaries'][i]['events'] or s['missing'] is not None):
                raise ValueError('Resumo armazenado inconsistente.')
        for key in ('null','confidence','alternative','pooled','measure','perform_test'):
            if v[key]!=p[key]:raise ValueError('Resultado incompatível com os parâmetros.')
        if (not finite(v['estimate']) or any(not finite(v[k]) or v[k]<0 for k in ('se','se_test'))
                or not finite(v['conditional_probability']) or not 0<v['conditional_probability']<1):raise ValueError('Estimativa Poisson inválida.')
        if not finite(v['low']) and not (p['alternative']=='less' and v['low']==-math.inf):raise ValueError('Limite inferior inválido.')
        if not finite(v['high']) and not (p['alternative']=='greater' and v['high']==math.inf):raise ValueError('Limite superior inválido.')
        if v['low']>v['estimate'] or v['high']<v['estimate']:raise ValueError('Intervalo Poisson inválido.')
        for key in ('p','exact_p'):
            if v[key] is not None and (not finite(v[key]) or not 0<=v[key]<=1):raise ValueError('Valor-p inválido.')
        if v['statistic'] is not None and not finite(v['statistic']):raise ValueError('Estatística inválida.')
        if not p['perform_test'] and any(v[k] is not None for k in ('statistic','p','exact_p')):raise ValueError('Teste inesperado.')
        if p['null']!=0 and v['exact_p'] is not None:raise ValueError('Exato indisponível para diferença não nula.')
        if p['perform_test'] and p['null']==0 and v['exact_p'] is None:raise ValueError('Teste exato ausente.')
        if result['source']['kind']!=('summary' if p['input_kind']=='summary' else 'columns'):raise ValueError('Origem Poisson inválida.')
    except (KeyError,TypeError,AttributeError,OverflowError) as error:raise ValueError('Resultado Poisson incompleto.') from error
