"""ANOVA de um fator, dados em colunas separadas ou resposta/fator."""
import math
import statistics
from core import numeric_column
from inference import scientific_stats, summarize


def prepare_groups(headers, rows, columns=None, response=None, factor=None):
    def valid(index):
        return type(index) is int and 0 <= index < len(headers)
    groups, excluded = [], 0
    if columns is not None:
        if len(columns) < 2 or len(set(columns)) != len(columns) or not all(valid(i) for i in columns):
            raise ValueError('Selecione pelo menos duas colunas diferentes.')
        for index in columns:
            try:
                values, missing = numeric_column(rows, index)
            except ValueError as error:
                raise ValueError(f'{headers[index]}: {error}') from error
            groups.append(dict(label=headers[index], values=values, missing=missing))
            excluded += missing
    else:
        if not valid(response) or not valid(factor) or response == factor:
            raise ValueError('Selecione colunas diferentes para resposta e fator.')
        levels = {}
        for line, row in enumerate(rows, 2):
            label, raw = str(row[factor]).strip(), str(row[response]).strip()
            if label in ('', '*'):
                excluded += 1
                continue
            group = levels.setdefault(label, dict(label=label, values=[], missing=0))
            if raw in ('', '*'):
                group['missing'] += 1
                excluded += 1
                continue
            try:
                value = float(raw.replace(',', '.'))
            except ValueError:
                raise ValueError(f'Linha {line}, {headers[response]}: número inválido {raw!r}.') from None
            if not math.isfinite(value):
                raise ValueError(f'Linha {line}: número não finito.')
            group['values'].append(value)
        groups = list(levels.values())
    if len(groups) < 2:
        raise ValueError('São necessários pelo menos dois grupos.')
    for group in groups:
        if len(group['values']) < 2:
            raise ValueError(f"Grupo {group['label']}: são necessárias pelo menos duas observações válidas.")
    return groups, excluded


def one_way(groups, equal_var=True, confidence=95, comparisons=False):
    if not math.isfinite(confidence) or not 0 < confidence < 100:
        raise ValueError('O nível de confiança deve estar entre 0 e 100, sem os extremos.')
    if len(groups) < 2:
        raise ValueError('São necessários pelo menos dois grupos.')
    try:
        summaries = [dict(summarize(g['values']), label=g['label']) for g in groups]
        k = len(groups)
        count = sum(g['n'] for g in summaries)
        overall = statistics.mean(v for g in groups for v in g['values'])
        within = math.fsum((g['n'] - 1) * g['sd'] ** 2 for g in summaries)
        between = math.fsum(g['n'] * (g['mean'] - overall) ** 2 for g in summaries)
        total = within + between
        df1, df_error = k - 1, count - k
        mse = within / df_error
        if not all(math.isfinite(v) for v in (within, between, total, mse)):
            raise ValueError('Magnitude dos dados excede a precisão numérica suportada.')
        if mse <= 0:
            raise ValueError('Variação dentro dos grupos nula: ANOVA não calculável nesta implementação.')
        stats = scientific_stats()
        if equal_var:
            df2 = df_error
            statistic = (between / df1) / mse
        else:
            if any(g['sd'] <= 0 for g in summaries):
                raise ValueError('ANOVA de Welch exige variância positiva em todos os grupos.')
            weights = [g['n'] / g['sd'] ** 2 for g in summaries]
            weight_sum = math.fsum(weights)
            if not math.isfinite(weight_sum) or weight_sum <= 0:
                raise ValueError('Escala de variâncias fora da precisão numérica suportada.')
            mean_w = math.fsum(w * g['mean'] for w, g in zip(weights, summaries)) / weight_sum
            correction = math.fsum((1 - w / weight_sum) ** 2 / (g['n'] - 1)
                                   for w, g in zip(weights, summaries))
            df2 = (k * k - 1) / (3 * correction)
            numerator = math.fsum(w * (g['mean'] - mean_w) ** 2 for w, g in zip(weights, summaries)) / df1
            statistic = numerator / (1 + 2 * (k - 2) * correction / (k * k - 1))
        p = float(stats.f.sf(statistic, df1, df2))
        if not all(math.isfinite(v) for v in (statistic, p, df2)):
            raise ValueError('Resultado fora da precisão numérica suportada.')
        # ICs individuais: desvio combinado no modelo clássico; EP próprio
        # e n-1 graus de liberdade para cada grupo no modelo de Welch.
        for group in summaries:
            se = math.sqrt(mse / group['n']) if equal_var else group['se']
            df = df_error if equal_var else group['n'] - 1
            margin = float(stats.t.isf((1 - confidence / 100) / 2, df)) * se
            group.update(low=group['mean'] - margin, high=group['mean'] + margin)
            if not all(math.isfinite(group[key]) for key in ('low', 'high')):
                raise ValueError('Não foi possível calcular os intervalos com este nível de confiança.')
        pairs = []
        if comparisons:
            comparison = stats.tukey_hsd(*(g['values'] for g in groups), equal_var=equal_var)
            intervals = comparison.confidence_interval(confidence / 100)
            for i in range(k):
                for j in range(i + 1, k):
                    pair = dict(first=groups[i]['label'], second=groups[j]['label'],
                                difference=float(comparison.statistic[i, j]), p=float(comparison.pvalue[i, j]),
                                low=float(intervals.low[i, j]), high=float(intervals.high[i, j]))
                    if not all(math.isfinite(pair[key]) for key in ('difference', 'p', 'low', 'high')):
                        raise ValueError('Não foi possível calcular todas as comparações entre os grupos.')
                    pairs.append(pair)
    except (ArithmeticError, OverflowError) as error:
        raise ValueError('Escala numérica dos dados não suportada para esta ANOVA.') from error
    return dict(groups=summaries, n=count, overall=overall, equal_var=equal_var,
                ss_between=between, ss_within=within, ss_total=total, mse=mse,
                df1=df1, df2=df2, df_error=df_error, f=statistic, p=p,
                s=math.sqrt(mse) if equal_var else None,
                r_squared=(between / total) * 100 if equal_var else None,
                confidence=confidence, comparisons=pairs,
                comparison_method='Tukey-Kramer' if equal_var else 'Games-Howell')


def format_anova_report(result, excluded=0):
    def number(value):
        return f'{value:.9g}'
    def probability(value):
        return '< 0,000001' if value < 1e-6 else '= ' + number(value)
    lines = ['ANOVA DE UM FATOR' + (' — variâncias iguais' if result['equal_var'] else ' — Welch'), '',
             'H0: todas as médias populacionais são iguais.',
             'H1: pelo menos uma média populacional difere.',
             f"Observações válidas: {result['n']}    Excluídas: {excluded}", '']
    if result['equal_var']:
        lines += [f"{'Fonte':<18} {'GL':>7} {'SQ':>15} {'QM':>15}",
                  f"{'Fator':<18} {result['df1']:>7} {number(result['ss_between']):>15} {number(result['ss_between'] / result['df1']):>15}",
                  f"{'Erro':<18} {result['df_error']:>7} {number(result['ss_within']):>15} {number(result['mse']):>15}",
                  f"{'Total':<18} {result['n'] - 1:>7} {number(result['ss_total']):>15}", '',
                  f"S = {number(result['s'])}    R² = {number(result['r_squared'])}%"]
    lines += [f"F = {number(result['f'])}    GL1 = {number(result['df1'])}    GL2 = {number(result['df2'])}    Valor-p {('<' if result['p'] < 1e-6 else '=')} {('0,000001' if result['p'] < 1e-6 else number(result['p']))}", '',
              f"{'Grupo':<25} {'N':>5} {'Média':>13} {'DesvPad':>13} {'IC individual ' + str(result['confidence']) + '%':>28}"]
    for group in result['groups']:
        label = group['label'] if len(group['label']) <= 24 else group['label'][:21] + '…'
        interval = f"({number(group['low'])}; {number(group['high'])})"
        lines.append(f"{label:<25} {group['n']:>5} {number(group['mean']):>13} {number(group['sd']):>13} {interval:>28}")
    lines += ['', 'Grupos: ' + ' | '.join(g['label'] for g in result['groups']),
              'Os intervalos das médias são individuais, não simultâneos.']
    if result['comparisons']:
        lines += ['', f"Comparações múltiplas: {result['comparison_method']}",
                  f"Confiança familiar: {result['confidence']:g}%. Diferença = primeiro grupo − segundo grupo."]
        for pair in result['comparisons']:
            lines += [f"{pair['first']} − {pair['second']}: diferença = {number(pair['difference'])}; "
                      f"IC = ({number(pair['low'])}; {number(pair['high'])}); p ajustado {probability(pair['p'])}"]
    return '\n'.join(lines) + '\n'
