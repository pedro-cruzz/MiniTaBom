"""Contratos JSON: normalidade, testes de postos e igualdade de variâncias."""
import math

NORMALITY_METHOD='diagnostic.normality.v1'
NORMALITY_KEYS={'ad','rj','ks','shapiro','dagostino'}
STUDY_METHODS={f'study.{mode}.v1':mode for mode in ('mannwhitney','wilcoxon','kruskal','variances')}


def finite(value):return type(value) in (float,int) and math.isfinite(value)


def validate_diagnostic_parameters(method_id,parameters,column_count):
    if method_id==NORMALITY_METHOD:
        if (set(parameters)!={'method','show_graph'} or parameters['method'] not in NORMALITY_KEYS
                or type(parameters['show_graph']) is not bool or column_count!=1):
            raise ValueError('Parâmetros de normalidade inválidos.')
        return
    if (method_id not in STUDY_METHODS or set(parameters)!={'mode','input_kind','group_order','alternative','method','correction','zero_method','center'}
            or parameters['mode']!=STUDY_METHODS[method_id] or parameters['input_kind'] not in ('columns','stacked')
            or parameters['alternative'] not in ('two-sided','less','greater') or parameters['method'] not in ('auto','exact','asymptotic')
            or type(parameters['correction']) is not bool or parameters['zero_method'] not in ('wilcox','pratt','zsplit')
            or parameters['center'] not in ('median','mean','bartlett') or column_count<2):
        raise ValueError('Parâmetros do teste de estudo inválidos.')
    mode=parameters['mode'];order=parameters['group_order']
    if parameters['input_kind']=='columns':
        if order is not None or (mode in ('wilcoxon','mannwhitney') and column_count!=2):
            raise ValueError('Colunas ou ordem incompatíveis com o teste.')
    elif (mode=='wilcoxon' or column_count!=2 or not isinstance(order,list) or not 2<=len(order)<=50
          or any(not isinstance(v,str) or v.strip() in ('','*') for v in order)
          or len(set(order))!=len(order) or (mode=='mannwhitney' and len(order)!=2)):
        raise ValueError('Ordem de grupos inválida para o teste.')


def validate_diagnostic_result(result):
    try:
        method_id=result['method_id'];p=result['parameters'];values=result['values']
        if not finite(values['statistic']):raise ValueError('Estatística inválida.')
        if method_id==NORMALITY_METHOD:
            sample=result['scenes'][0]['sample'];scene=result['scenes'][0]
            minimum=4 if p['method']=='rj' else 8 if p['method']=='dagostino' else 3
            maximum=1000 if p['method']=='rj' else 5000 if p['method']=='shapiro' else 200000
            if (len(result['scenes'])!=1 or scene['kind']!='normal_probability' or type(scene['version']) is not int or scene['version']!=1
                    or not isinstance(sample,list) or not minimum<=len(sample)<=maximum or any(not finite(v) for v in sample)
                    or type(values['n']) is not int or values['n']!=len(sample) or values['method_key']!=p['method']
                    or not finite(values['mean']) or not finite(values['sd']) or values['sd']<=0
                    or type(values['missing']) is not int or values['missing']<0 or result['missing'].get('count')!=values['missing']
                    or type(values['repeated']) is not int or values['repeated']!=len(sample)-len(set(sample))
                    or any(not isinstance(values[k],str) or not values[k] for k in ('source','method','stat_label'))):
                raise ValueError('Snapshot de normalidade inválido.')
            bounds=[values.get('p_lower'),values.get('p_upper')]
            if values['p'] is None:
                if sum(v is not None for v in bounds)!=1 or any(v is not None and (not finite(v) or not 0<v<1) for v in bounds):
                    raise ValueError('Limite do valor-p inválido.')
            elif not finite(values['p']) or not 0<=values['p']<=1 or any(v is not None for v in bounds):
                raise ValueError('Valor-p de normalidade inválido.')
            return
        mode=p['mode'];summaries=values['summaries']
        if (values['mode']!=mode or not finite(values['p']) or not 0<=values['p']<=1
                or not isinstance(values['title'],str) or not values['title'] or not isinstance(values['method'],str) or not values['method']
                or values['alternative']!=p['alternative'] or values['correction']!=p['correction'] or type(values['correction']) is not bool
                or type(values['excluded']) is not int or values['excluded']<0 or result['missing'].get('count')!=values['excluded']
                or not isinstance(summaries,list) or len(summaries)!=(1 if mode=='wilcoxon' else len(p['group_order']) if p['input_kind']=='stacked' else len(result['source']['column_ids']))):
            raise ValueError('Resultado de teste de estudo inválido.')
        for s in summaries:
            if (not isinstance(s['label'],str) or not s['label'] or type(s['n']) is not int or s['n']<2 or not finite(s['median'])
                    or (mode!='wilcoxon' and (not finite(s['sd']) or s['sd']<0))):raise ValueError('Resumo amostral inválido.')
        if p['input_kind']=='stacked' and [s['label'] for s in summaries]!=p['group_order']:
            raise ValueError('Ordem dos grupos inconsistente.')
        for key in ('details','notes'):
            if not isinstance(values[key],list) or any(not isinstance(v,str) for v in values[key]):raise ValueError('Notas do teste inválidas.')
        df=values['df'];k=len(summaries)
        if mode in ('mannwhitney','wilcoxon'):
            if df is not None:raise ValueError('GL inesperados neste teste.')
        elif mode=='kruskal' or p['center']=='bartlett':
            if type(df) is not int or df!=k-1:raise ValueError('GL do teste inválidos.')
        elif not isinstance(df,list) or df!=[k-1,sum(s['n'] for s in summaries)-k] or any(type(n) is not int for n in df):
            raise ValueError('GL de Levene inválidos.')
        if result.get('scenes')!=[]:raise ValueError('Cena inesperada no teste de postos/variâncias.')
    except (KeyError,IndexError,TypeError,AttributeError,OverflowError) as error:
        raise ValueError('Registro de diagnóstico incompleto.') from error
