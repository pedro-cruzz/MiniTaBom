import csv, io, math, statistics
from collections import Counter
from itertools import product

def read_table(text):
    try:
        dialect = csv.Sniffer().sniff(text[:8192], delimiters=';,\t')
    except csv.Error:
        try:
            dialect = csv.Sniffer().sniff(text.splitlines()[0], delimiters=';,\t')
        except (csv.Error, IndexError):
            dialect = csv.excel
    rows = list(csv.reader(io.StringIO(text), dialect))
    if not rows:
        raise ValueError('Arquivo vazio.')
    headers = [h.strip() for h in rows[0]]
    if any(not h for h in headers) or len(set(headers)) != len(headers):
        raise ValueError('Cabeçalhos devem ser únicos e não vazios.')
    body = [r for r in rows[1:] if r]
    if any(len(r) != len(headers) for r in body):
        raise ValueError('Quantidade de campos inconsistente.')
    return headers, body

def _numeric_value(raw, line):
    raw = str(raw).strip()
    if raw in ('', '*'):
        return None
    try:
        value = float(raw.replace(',', '.'))
    except ValueError:
        raise ValueError(f'Linha {line}: número inválido {raw!r}.') from None
    if not math.isfinite(value):
        raise ValueError(f'Linha {line}: valor não finito.')
    return value


def numeric_column(rows, index):
    values, missing = [], 0
    for line, row in enumerate(rows, 2):
        value = _numeric_value(row[index], line)
        if value is None:
            missing += 1
            continue
        values.append(value)
    return values, missing

def _quartile(ordered, probability):
    """Posição (n+1)p, interpolação linear e limites nos extremos.

    A convenção nos extremos para n pequeno é do MiniTaBom; falta comparação
    experimental com Minitab 16.
    """
    position = (len(ordered) + 1) * probability
    if position <= 1:
        return ordered[0]
    if position >= len(ordered):
        return ordered[-1]
    lower = math.floor(position)
    fraction = position - lower
    return (1 - fraction) * ordered[lower - 1] + fraction * ordered[lower]


def describe(values, missing=0):
    try:
        result = _describe(values, missing)
    except (OverflowError, ArithmeticError) as error:
        raise ValueError('Magnitude dos dados excede a precisão numérica suportada.') from error
    numeric_results = (item for value in result.values()
                       for item in (value if isinstance(value, tuple) else (value,)))
    if any(value is not None and not math.isfinite(value) for value in numeric_results):
        raise ValueError('Magnitude dos dados excede a precisão numérica suportada.')
    return result


def _describe(values, missing=0):
    if not values or not all(math.isfinite(v) for v in values):
        raise ValueError('A coluna precisa conter números finitos.')
    n = len(values)
    if type(missing) is not int or missing < 0:
        raise ValueError('A quantidade de ausentes deve ser um inteiro não negativo.')
    ordered = sorted(values)
    mean = statistics.mean(values)
    sd = statistics.stdev(values) if n > 1 else None
    q1, q3 = _quartile(ordered, .25), _quartile(ordered, .75)
    # 5% por ponta; meios inteiros arredondados para cima (convenção
    # ainda pendente de comparação experimental com a versão 16).
    trim = (n + 10) // 20
    frequencies = Counter(values)
    frequency = max(frequencies.values())
    modes = tuple(sorted(v for v, count in frequencies.items() if count == frequency))
    # Razões padronizadas evitam elevar diretamente dados grandes a 3/4.
    standardized = [(v - mean) / sd for v in values] if sd else []
    skewness = (n / ((n - 1) * (n - 2)) * math.fsum(z ** 3 for z in standardized)
                if n > 2 and sd else None)
    kurtosis = (n * (n + 1) / ((n - 1) * (n - 2) * (n - 3))
                * math.fsum(z ** 4 for z in standardized)
                - 3 * (n - 1) ** 2 / ((n - 2) * (n - 3))
                if n > 3 and sd else None)
    mssd = (math.fsum((b - a) ** 2 / 2 for a, b in zip(values, values[1:])) / (n - 1)
            if n > 1 else None)
    return {'N': n, 'Ausentes': missing, 'N total': n + missing, 'Média': mean,
            'Erro padrão': sd / math.sqrt(n) if n > 1 else None,
            'Desvio padrão amostral': sd,
            'Variância amostral': statistics.variance(values) if n > 1 else None,
            'Coeficiente de variação (%)': 100 * (sd / mean) if sd is not None and mean != 0 else None,
            'Mínimo': ordered[0], 'Q1': q1, 'Mediana': statistics.median(values),
            'Q3': q3, 'Máximo': ordered[-1],
            'Amplitude': ordered[-1] - ordered[0], 'Intervalo interquartil': q3 - q1,
            'Soma': math.fsum(values), 'Soma dos quadrados': math.fsum(v * v for v in values),
            'Média aparada (5% por ponta)': statistics.mean(ordered[trim:n - trim]),
            'Moda': modes if frequency > 1 else None,
            'Frequência da moda': frequency if frequency > 1 else None,
            'Assimetria': skewness, 'Curtose (excesso)': kurtosis, 'MSSD': mssd}


DESCRIPTIVE_STATISTICS = (
    'N', 'Ausentes', 'N total', 'Média', 'Erro padrão',
    'Desvio padrão amostral', 'Variância amostral', 'Coeficiente de variação (%)',
    'Mínimo', 'Q1', 'Mediana', 'Q3', 'Máximo', 'Amplitude',
    'Intervalo interquartil', 'Soma', 'Soma dos quadrados',
    'Média aparada (5% por ponta)', 'Moda', 'Frequência da moda',
    'Assimetria', 'Curtose (excesso)', 'MSSD',
)


def grouped_describe(headers, rows, columns, by, include_missing=False, include_empty=False):
    """Grupos textuais na ordem de aparição; exclusão independente por resposta."""
    if (not columns or not by or len(set(by)) != len(by) or len(set(columns)) != len(columns)
            or any(type(i) is not int or not 0 <= i < len(headers) for i in [*columns, *by])):
        raise ValueError('Selecione variáveis e colunas de agrupamento válidas, sem repetir os grupos.')
    if set(columns) & set(by):
        raise ValueError('Use colunas diferentes para as respostas e os grupos.')
    groups, levels, excluded = {}, [[] for _ in by], 0
    for line, row in enumerate(rows, 2):
        key = tuple(None if str(row[i]).strip() in ('', '*') else str(row[i]).strip() for i in by)
        if None in key and not include_missing:
            excluded += 1
            continue
        for known, value in zip(levels, key):
            if value not in known:
                known.append(value)
        if key not in groups:
            if len(groups) >= 10000:
                raise ValueError('A análise está limitada a 10.000 grupos.')
            groups[key] = {index: [[], 0] for index in columns}
        for index in columns:
            try:
                value = _numeric_value(row[index], line)
            except ValueError as error:
                raise ValueError(f'{headers[index]}: {error}') from error
            if value is None:
                groups[key][index][1] += 1
            else:
                groups[key][index][0].append(value)
    if not groups:
        raise ValueError('Nenhum grupo disponível. Confira as colunas e a opção de incluir grupos ausentes.')
    count = math.prod(map(len, levels)) if include_empty else len(groups)
    if count > 10000:
        raise ValueError('A análise está limitada a 10.000 grupos. Reduza as variáveis de agrupamento ou as combinações vazias.')
    keys = list(product(*levels)) if include_empty else list(groups)
    records = []
    for index in columns:
        for key in keys:
            values, missing = groups[key][index] if key in groups else ([], 0)
            if values:
                result = describe(values, missing)
            else:
                result = dict.fromkeys(DESCRIPTIVE_STATISTICS)
                result.update({'N': 0, 'Ausentes': missing, 'N total': missing})
            records.append({'column': index, 'levels': key, 'statistics': result})
    return records, excluded


def _statistics_lines(result, selected):
    lines = []
    for key in selected:
        value = result[key]
        if isinstance(value, tuple):
            lines.append(f'{key}: ' + '; '.join(f'{item:.10g}' for item in value))
        else:
            lines.append(f'{key}: {value:.10g}' if value is not None else f'{key}: indefinido')
    return lines


def descriptive_report(headers, rows, columns, statistics_selected, by=None, include_missing=False, include_empty=False):
    """Calcula todas as colunas antes de produzir o texto, sem saída parcial."""
    if not columns or any(type(i) is not int or not 0 <= i < len(headers) for i in columns):
        raise ValueError('Selecione pelo menos uma variável válida.')
    if not statistics_selected or any(key not in DESCRIPTIVE_STATISTICS for key in statistics_selected):
        raise ValueError('Selecione pelo menos uma estatística válida.')
    if by:
        records, excluded = grouped_describe(headers, rows, columns, by, include_missing, include_empty)
        sections = []
        for index in columns:
            lines = ['Estatísticas descritivas: ' + headers[index] + ' (por ' + ', '.join(headers[i] for i in by) + ')',
                     f'Linhas excluídas por grupo ausente: {excluded}']
            for record in records:
                if record['column'] != index:
                    continue
                labels = [f'{headers[i]} = ' + ('[ausente]' if value is None else repr(value))
                          for i, value in zip(by, record['levels'])]
                lines.extend(['', 'Grupo: ' + '; '.join(labels)])
                lines.extend(_statistics_lines(record['statistics'], statistics_selected))
            sections.append('\n'.join(lines))
        return '\n\n'.join(sections) + '\n'
    sections = []
    for index in columns:
        try:
            values, missing = numeric_column(rows, index)
            result = describe(values, missing)
        except ValueError as error:
            raise ValueError(f'{headers[index]}: {error}') from error
        lines = ['Estatísticas descritivas: ' + headers[index]]
        lines.extend(_statistics_lines(result, statistics_selected))
        sections.append('\n'.join(lines))
    return '\n\n'.join(sections) + '\n'

def histogram(values):
    if not values or not all(math.isfinite(v) for v in values):
        raise ValueError('Histograma requer números finitos.')
    lo, hi = min(values), max(values)
    if lo == hi:
        return [lo, hi], [len(values)]
    count = min(30, math.ceil(math.log2(len(values)) + 1))
    width = (hi-lo)/count
    bins = [0]*count
    for v in values:
        bins[min(int((v-lo)/width), count-1)] += 1
    return [lo + width*i for i in range(count+1)], bins


def boxplot(values):
    """Quartis interpolados, bigodes nos valores adjacentes e cercas 1,5 IQR."""
    if not values or not all(math.isfinite(v) for v in values):
        raise ValueError('Boxplot requer números finitos.')
    ordered = sorted(values)
    q1, q3 = _quartile(ordered, .25), _quartile(ordered, .75)
    iqr = q3 - q1
    lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    if not all(math.isfinite(v) for v in (iqr, lower, upper)):
        raise ValueError('Magnitude dos dados excede a precisão numérica suportada.')
    adjacent = [v for v in ordered if lower <= v <= upper]
    return dict(q1=q1, median=statistics.median(values), q3=q3,
                low=adjacent[0], high=adjacent[-1],
                outliers=[v for v in ordered if v < lower or v > upper])
