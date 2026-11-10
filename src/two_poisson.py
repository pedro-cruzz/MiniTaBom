"""Duas taxas/médias Poisson: Z, IC normal e teste condicional binomial.

Referências: ajuda 16.2.4 (2-Sample Poisson Rate) e fórmulas oficiais atuais.
O exato bilateral duplica a menor cauda inclusiva; não usa ordenação por PMF.
"""
import math

from basic_inference import _count,_options,_normal_p,parse_count
from inference import scientific_stats,p_statement
from sample_inputs import independent_samples

TITLE='Duas taxas de Poisson'


def two_poisson(events1,n1,events2,n2,length1=1.,length2=1.,null=0.,confidence=95.,
                alternative='two-sided',pooled=False,measure='rate',perform_test=True):
    for count,n in ((events1,n1),(events2,n2)):
        _count(count,0,'Total de ocorrências');_count(n,1,'Número de observações')
    if any(type(v) not in (int,float) or not math.isfinite(v) or v<=0 for v in (length1,length2)):
        raise ValueError('As exposições por observação devem ser positivas e finitas.')
    if any(type(v) not in (int,float) for v in (null,confidence)) or type(pooled) is not bool or type(perform_test) is not bool:
        raise ValueError('Opções de Poisson inválidas.')
    _,tail=_options(null,confidence,alternative)
    if measure not in ('rate','mean'):raise ValueError('Selecione taxas por unidade ou médias por observação.')
    if pooled and null!=0:raise ValueError('A estimativa combinada requer diferença hipotética zero.')
    samples=[]
    for i,(count,n,length) in enumerate(((events1,n1,length1),(events2,n2,length2)),1):
        exposure=n*length
        if not math.isfinite(exposure) or exposure<=0:raise ValueError('Exposição total fora da precisão suportada.')
        samples.append(dict(name=f'Amostra {i}',events=count,n=n,length=length,exposure=exposure,
                            rate=count/exposure,mean=count/n,missing=0))
    exposures=[s['exposure'] if measure=='rate' else s['n'] for s in samples]
    rates=[s[measure] for s in samples]
    estimate=rates[0]-rates[1]
    se=math.hypot(math.sqrt(events1)/exposures[0],math.sqrt(events2)/exposures[1])
    scale=max(exposures);scaled=[e/scale for e in exposures];denominator=math.fsum(scaled)
    conditional_p=scaled[0]/denominator
    if not 0<conditional_p<1:raise ValueError('Razão das exposições fora da precisão numérica suportada.')
    common=((events1+events2)/scale)/denominator
    se_test=math.sqrt(common)*math.hypot(1/math.sqrt(exposures[0]),1/math.sqrt(exposures[1])) if pooled else se
    critical=float(scientific_stats().norm.isf(tail));margin=critical*se
    low=-math.inf if alternative=='less' else estimate-margin
    high=math.inf if alternative=='greater' else estimate+margin
    statistic=p=exact=None
    if perform_test:
        if se_test>0:
            statistic=(estimate-null)/se_test;p=_normal_p(statistic,alternative)
        if null==0:
            distribution=scientific_stats().binom(events1+events2,conditional_p)
            lower,upper=float(distribution.cdf(events1)),float(distribution.sf(events1-1))
            exact=min(1.,2*min(lower,upper)) if alternative=='two-sided' else lower if alternative=='less' else upper
    numbers=[estimate,se,se_test,margin,common,*rates,*[s[k] for s in samples for k in ('rate','mean')]]
    if alternative!='less':numbers.append(low)
    if alternative!='greater':numbers.append(high)
    numbers += [v for v in (statistic,p,exact) if v is not None]
    if not all(math.isfinite(v) for v in numbers) or low>high:
        raise ValueError('Taxas, teste ou intervalo fora da precisão numérica suportada.')
    warnings=[]
    if min(events1,events2)<=10:warnings.append('Contagens pequenas: a aproximação normal e o IC podem ser inadequados.')
    if se==0:warnings.append('IC normal degenerado: não há ocorrências; o teste Z é indisponível. O exato para diferença zero permanece disponível.')
    if perform_test and null!=0:warnings.append('O teste exato condicional só é calculado para diferença hipotética zero.')
    return dict(samples=samples,estimate=estimate,se=se,se_test=se_test,statistic=statistic,p=p,exact_p=exact,
                conditional_probability=conditional_p,low=low,high=high,null=null,confidence=confidence,
                alternative=alternative,pooled=pooled,measure=measure,perform_test=perform_test,
                warnings=warnings,source='Dados resumidos',excluded_groups=0)


def analyze_two_poisson(headers,rows,columns,source='columns',group=None,group_order=None,**options):
    if (source=='columns' and len(columns)!=2) or (source=='stacked' and len(columns)!=1):
        raise ValueError('Selecione as amostras ou resposta/grupo.')
    samples,excluded=independent_samples(headers,rows,columns,source,group,numeric=False,levels=group_order)
    summaries=[]
    for sample in samples:
        summaries.extend((sum(parse_count(v,'Contagem de '+sample['name']) for v in sample['values']),len(sample['values'])))
    result=two_poisson(*summaries,**options)
    for calculated,sample in zip(result['samples'],samples):
        calculated.update(name=sample['name'],missing=sample['missing'])
    result.update(source='Colunas separadas' if source=='columns' else 'Amostras empilhadas',excluded_groups=excluded,
                  group_order=[s['level'] for s in samples] if source=='stacked' else None)
    return result


def format_two_poisson(result):
    number=lambda v:'+∞' if v==math.inf else '−∞' if v==-math.inf else f'{v:.9g}'
    measure='taxa por unidade' if result['measure']=='rate' else 'média por observação'
    lines=['DUAS TAXAS DE POISSON — '+result['source'],'','Comparação de '+measure+'. Diferença = primeira − segunda.']
    for s in result['samples']:
        missing='não informados' if s['missing'] is None else str(s['missing'])
        lines += [f"{s['name']}: N={s['n']}; ocorrências={s['events']}; exposição por observação={number(s['length'])}; ausentes={missing}.",
                  f"  Taxa={number(s['rate'])}; média={number(s['mean'])}."]
    lines += [f"Diferença estimada = {number(result['estimate'])}",
              f"IC normal de {result['confidence']:g}%: ({number(result['low'])}; {number(result['high'])})"]
    if result['perform_test']:
        symbol={'two-sided':'≠','less':'<','greater':'>'}[result['alternative']]
        lines += [f"H0: diferença = {number(result['null'])}; H1: diferença {symbol} {number(result['null'])}.",
                  'Teste normal: taxa combinada.' if result['pooled'] else 'Teste normal: estimativas separadas.',
                  'Z = '+(number(result['statistic']) if result['statistic'] is not None else 'indisponível'),
                  p_statement(result['p'],'Valor-p normal')]
        if result['exact_p'] is not None:
            lines += [p_statement(result['exact_p'],'Valor-p exato condicional'),
                      'Exato bilateral: duas vezes a menor cauda binomial inclusiva, limitado a 1.']
    lines += ['Linhas excluídas por grupo ausente: '+str(result['excluded_groups']),
              'O IC usa aproximação normal com estimativas separadas, inclusive quando o teste usa taxa combinada ou exato.',
              'Modelo: processos Poisson independentes, taxa constante e mesma exposição dentro de cada amostra.']
    return '\n'.join(lines+result['warnings'])+'\n'
