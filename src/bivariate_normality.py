"""Diagnóstico conjunto de assimetria/curtose de Mardia (1970/1974)."""
import math
from core import numeric_column,_numeric_value
from inference import scientific_stats,p_statement


def bivariate_normality(headers,rows,columns):
    if len(columns)!=2 or len(set(columns))!=2 or any(type(c) is not int or not 0<=c<len(headers) for c in columns):
        raise ValueError('O diagnóstico bivariado requer exatamente duas colunas diferentes.')
    stats=scientific_stats()
    import numpy as np
    pairs=[]
    for line,row in enumerate(rows,1):
        pair=[_numeric_value(row[c],line) for c in columns]
        if all(v is not None for v in pair):pairs.append(pair)
    n=len(pairs)
    if not 4<=n<=200000:raise ValueError('Use entre 4 e 200000 pares completos.')
    with np.errstate(over='raise',invalid='raise',divide='raise'):
        data=np.asarray(pairs,dtype=float)
        scale=np.max(np.abs(data),axis=0)
        if np.any(scale==0):raise ValueError('Covariância singular: uma variável é constante.')
        centered=data/scale;centered-=centered.mean(axis=0)
        u,s,_=np.linalg.svd(centered,full_matrices=False)
        if s[-1]<=np.finfo(float).eps*max(centered.shape)*s[0]:
            raise ValueError('Covariância singular: não é possível avaliar normalidade bivariada com relação linear perfeita.')
        z=u*math.sqrt(n)
        third=np.einsum('ni,nj,nk->ijk',z,z,z)/n
        skew=max(0.,float(np.sum(third**2)))
        kurt=float(np.mean(np.sum(z*z,axis=1)**2))
        factor=3*(n+1)*(n+3)/(3*n*(n+1)-6) if n<20 else 1.
        skew_stat=n*factor*skew/6
        kurt_stat=(kurt-8)/math.sqrt(64/n)
    if not all(math.isfinite(v) for v in (skew,kurt,skew_stat,kurt_stat)):
        raise ValueError('Diagnóstico bivariado fora da precisão numérica suportada.')
    return dict(n=n,excluded=len(rows)-n,skew=skew,kurtosis=kurt,skew_statistic=skew_stat,
                skew_p=float(stats.chi2.sf(skew_stat,4)),kurtosis_z=kurt_stat,
                kurtosis_p=float(2*stats.norm.sf(abs(kurt_stat))),small_sample_factor=factor)


def format_bivariate(result):
    return '\n'.join(['NORMALIDADE BIVARIADA — diagnóstico de Mardia',
        f"N={result['n']}; pares excluídos={result['excluded']}",
        f"Assimetria b1,2={result['skew']:.9g}; qui-quadrado (GL=4)={result['skew_statistic']:.9g}; "+p_statement(result['skew_p']),
        f"Curtose b2,2={result['kurtosis']:.9g}; Z={result['kurtosis_z']:.9g}; "+p_statement(result['kurtosis_p']),
        f"Correção da assimetria para N<20: fator={result['small_sample_factor']:.9g}.",
        'Probabilidades aproximadas, especialmente limitadas em amostras pequenas. Dois diagnósticos separados, sem ajuste conjunto.',
        'Um resultado não significativo não comprova normalidade conjunta; avalie também dispersão e resíduos.',
        'Diagnóstico complementar para os estudos; equivalência com uma opção da versão 16 não foi estabelecida.'])+'\n'
