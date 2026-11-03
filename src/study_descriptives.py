"""Frequências por classes/categorias e percentis de observações."""
from collections import Counter
from decimal import Decimal, InvalidOperation, ROUND_CEILING
import math
from core import numeric_column


def sample_percentiles(values, percentages, method='exclusive'):
    if not values or not all(math.isfinite(v) for v in values):raise ValueError('Use uma amostra numérica finita.')
    if method not in ('exclusive','inclusive','clamped'):raise ValueError('Método de percentil inválido.')
    if not percentages or len(percentages)>100:raise ValueError('Informe entre 1 e 100 percentis.')
    ordered=sorted(values);n=len(ordered);result=[]
    for percentage in percentages:
        if not math.isfinite(percentage) or not 0<=percentage<=100:raise ValueError('Percentis devem estar entre 0 e 100.')
        position=(n-1)*percentage/100+1 if method=='inclusive' else (n+1)*percentage/100
        if method=='exclusive' and not 1<=position<=n:
            value=None
        elif position<=1:value=ordered[0]
        elif position>=n:value=ordered[-1]
        else:
            index=math.floor(position);fraction=position-index
            value=(1-fraction)*ordered[index-1]+fraction*ordered[index]
        result.append(dict(percentile=percentage,position=position,value=value))
    return result


def frequency_table(headers,rows,column,numeric=False,classes=4,decimals=None,frequency_column=None,order='first'):
    if type(column) is not int or not 0<=column<len(headers):raise ValueError('Selecione uma variável válida.')
    if frequency_column is not None and (type(frequency_column) is not int or not 0<=frequency_column<len(headers) or frequency_column==column):
        raise ValueError('Selecione coluna de contagens distinta da variável.')
    if order not in ('first','sorted','descending'):raise ValueError('Ordenação inválida.')
    records=[];missing=0
    for line,row in enumerate(rows,1):
        raw=row[column].strip()
        if raw in ('','*'):
            missing+=1;continue
        weight=1
        try:
            if frequency_column is not None:
                raw_weight=row[frequency_column].strip()
                if raw_weight in ('','*'):
                    missing+=1;continue
                weight_dec=Decimal(raw_weight.replace(',','.'))
                if not weight_dec.is_finite() or weight_dec!=weight_dec.to_integral_value() or weight_dec<0:raise InvalidOperation
                weight=int(weight_dec)
            if weight==0:continue
            value=Decimal(raw.replace(',','.')) if numeric else raw
            if numeric and not value.is_finite():raise InvalidOperation
        except (InvalidOperation,ValueError):raise ValueError(f'Linha {line}: confira os valores e as contagens inteiras não negativas.') from None
        records.append((value,weight))
    if not records:raise ValueError('Não há observações válidas com frequência positiva.')
    total=sum(weight for _,weight in records)
    if total>2**53-1:raise ValueError('A soma das frequências excede a precisão suportada.')
    meta={}
    if numeric:
        if type(classes) is not int or not 1<=classes<=200:raise ValueError('Use de 1 a 200 classes desejadas.')
        if decimals is None:decimals=max(0,max(-v.as_tuple().exponent for v,_ in records))
        if type(decimals) is not int or not 0<=decimals<=12:raise ValueError('Use entre 0 e 12 casas decimais.')
        quantum=Decimal(1).scaleb(-decimals)
        if any(v!=v.quantize(quantum) for v,_ in records):raise ValueError('As casas decimais escolhidas perdem precisão dos dados.')
        lo,hi=min(v for v,_ in records),max(v for v,_ in records)
        raw_width=(hi-lo)/classes
        width=raw_width.quantize(quantum,rounding=ROUND_CEILING) if raw_width else quantum
        count=classes+1 if raw_width and raw_width==width else classes
        counts=[0]*count
        for value,weight in records:
            index=int((value-lo)//width)
            if not 0<=index<count:raise ValueError('Os limites de classes não abrangem os dados.')
            counts[index]+=weight
        labels=[f'{lo+i*width:f} – {lo+(i+1)*width-quantum:f}' for i in range(count)]
        meta=dict(width=str(width),classes=count,desired_classes=classes,decimals=decimals,
                  exact_step=bool(raw_width and raw_width==width),lower=float(lo),
                  rule='Passo exato acrescenta classe; passo não exato arredonda para cima na precisão escolhida.')
        items=list(zip(labels,counts))
    else:
        counted=Counter()
        for value,weight in records:counted[value]+=weight
        if len(counted)>200:raise ValueError('Use até 200 categorias por tabela.')
        items=list(counted.items())
        if order=='sorted':items.sort(key=lambda item:item[0])
        elif order=='descending':items.sort(key=lambda item:-item[1])
    cumulative=0;table=[]
    for label,count in items:
        cumulative+=count
        table.append(dict(label=label,count=count,relative=count/total,percent=100*count/total,
                          cumulative=cumulative,cumulative_percent=100*cumulative/total))
    return dict(source=headers[column],numeric=numeric,n=total,missing=missing,table=table,**meta)


def format_frequency(result):
    lines=['TABELA DE FREQUÊNCIAS — '+result['source'],'',f"N = {result['n']}; linhas omitidas = {result['missing']}"]
    if result['numeric']:lines += [f"Classes = {result['classes']}; passo = {result['width']}",result['rule']]
    lines+=['',f"{'Classe/categoria':<28} {'f':>9} {'Fr':>12} {'%':>10} {'Fa':>10} {'Fa %':>10}"]
    for r in result['table']:
        lines.append(f"{r['label']:<28} {r['count']:>9} {r['relative']:>12.6g} {r['percent']:>10.6g} {r['cumulative']:>10} {r['cumulative_percent']:>10.6g}")
    return '\n'.join(lines)+'\n'
