"""Contrato da ANOVA de um fator e do snapshot de boxplots."""
import math

ANOVA_METHOD='anova.one_way.v1'


def validate_anova_parameters(parameters,column_count):
    if (not isinstance(parameters,dict) or set(parameters)!={'input_kind','group_order','equal_var','confidence','comparisons','comparison_method','show_graph'}
            or parameters['input_kind'] not in ('columns','stacked') or column_count<2
            or type(parameters['confidence']) not in (int,float) or not math.isfinite(parameters['confidence']) or not 0<parameters['confidence']<100
            or any(type(parameters[k]) is not bool for k in ('equal_var','comparisons','show_graph'))
            or parameters['comparison_method'] not in ('tukey','lsd')
            or (parameters['comparisons'] and parameters['comparison_method']=='lsd' and not parameters['equal_var'])):
        raise ValueError('Parâmetros da ANOVA inválidos.')
    order=parameters['group_order']
    if parameters['input_kind']=='columns':
        if order is not None:raise ValueError('Ordem de níveis inesperada.')
    elif (column_count!=2 or not isinstance(order,list) or len(order)<2
          or any(not isinstance(v,str) or not v.strip() or v in ('','*') for v in order) or len(set(order))!=len(order)):
        raise ValueError('Ordem de grupos da ANOVA inválida.')


def validate_anova_result(result):
    try:
        parameters=result['parameters'];values=result['values'];scenes=result['scenes']
        finite=lambda v:type(v) in (int,float) and math.isfinite(v)
        if not isinstance(scenes,list) or len(scenes)!=1:raise ValueError('Snapshot de ANOVA inválido.')
        scene=scenes[0];groups=scene['groups'];summaries=values['groups']
        if (scene['kind']!='group_boxplot' or type(scene['version']) is not int or scene['version']!=1
                or not isinstance(scene['response_label'],str) or not isinstance(groups,list) or len(groups)<2
                or not isinstance(summaries,list) or len(summaries)!=len(groups)):
            raise ValueError('Grupos/gráficos de ANOVA inválidos.')
        labels=[];n=0;excluded=0
        for group,summary in zip(groups,summaries):
            labels.append(group['label']);numbers=group['values']
            if (not isinstance(group['label'],str) or not group['label'] or not isinstance(numbers,list) or len(numbers)<2
                    or any(not finite(v) for v in numbers) or type(group['missing']) is not int or group['missing']<0
                    or summary['label']!=group['label'] or type(summary['n']) is not int or summary['n']!=len(numbers)
                    or any(not finite(summary[k]) for k in ('mean','sd','se','low','high'))
                    or summary['sd']<0 or summary['se']<0 or summary['low']>summary['high']):
                raise ValueError('Grupo de ANOVA inválido.')
            n+=len(numbers);excluded+=group['missing']
        if len(set(labels))!=len(labels):raise ValueError('Grupos repetidos na ANOVA.')
        if parameters['input_kind']=='stacked' and labels!=parameters['group_order']:raise ValueError('Ordem de grupos inconsistente.')
        if (type(values['n']) is not int or values['n']!=n or values['equal_var']!=parameters['equal_var']
                or type(values['equal_var']) is not bool or values['confidence']!=parameters['confidence']
                or values['df1']!=len(groups)-1 or values['df_error']!=n-len(groups)
                or any(not finite(values[k]) for k in ('overall','ss_between','ss_within','ss_total','mse','df2','f','p'))
                or values['df2']<=0 or values['mse']<=0 or values['f']<0 or not 0<=values['p']<=1):
            raise ValueError('Estatísticas de ANOVA inválidas.')
        pairs=values['comparisons']
        expected=len(groups)*(len(groups)-1)//2 if parameters['comparisons'] else 0
        if not isinstance(pairs,list) or len(pairs)!=expected:raise ValueError('Comparações de ANOVA incompletas.')
        seen=set()
        for pair in pairs:
            key=(pair['first'],pair['second'])
            if (pair['first'] not in labels or pair['second'] not in labels or labels.index(pair['first'])>=labels.index(pair['second'])
                    or key in seen or any(not finite(pair[k]) for k in ('difference','p','low','high'))
                    or not 0<=pair['p']<=1 or pair['low']>pair['high']):raise ValueError('Comparação de ANOVA inválida.')
            seen.add(key)
        missing=result['missing']
        if type(missing['count']) is not int or missing['count']<excluded:raise ValueError('Contagem de ausentes da ANOVA inválida.')
    except (KeyError,TypeError,AttributeError,OverflowError) as error:
        raise ValueError('Contrato de ANOVA incompleto.') from error
