"""Leitura de amostras independentes sem alterar a planilha."""
from core import _numeric_value


def independent_samples(headers, rows, columns, source='columns', group=None, numeric=False):
    if source not in ('columns', 'stacked'):
        raise ValueError('Formato de amostras inválido.')
    if not columns or any(type(c) is not int or not 0 <= c < len(headers) for c in columns):
        raise ValueError('Selecione as colunas das amostras.')
    if len(set(columns)) != len(columns):
        raise ValueError('As amostras devem estar em colunas diferentes.')
    excluded = 0
    if source == 'columns':
        samples = [dict(name=headers[c], raw=[row[c] for row in rows]) for c in columns]
    else:
        if (len(columns) != 1 or type(group) is not int or not 0 <= group < len(headers)
                or group == columns[0]):
            raise ValueError('Selecione resposta e grupo em colunas diferentes.')
        groups = {}
        for row in rows:
            level = str(row[group]).strip()
            if level in ('', '*'):
                excluded += 1
                continue
            groups.setdefault(level, []).append(row[columns[0]])
            if len(groups) > 2:
                raise ValueError('A coluna de grupo deve conter exatamente dois grupos não ausentes.')
        if len(groups) != 2:
            raise ValueError('A coluna de grupo deve conter exatamente dois grupos não ausentes.')
        samples = [dict(name=f'{headers[columns[0]]} [grupo {level!r}]', raw=values)
                   for level, values in groups.items()]
    for sample in samples:
        values, missing = [], 0
        for index, raw in enumerate(sample.pop('raw'), 1):
            text = str(raw).strip()
            if text in ('', '*'):
                missing += 1
                continue
            try:
                values.append(_numeric_value(text, index) if numeric else text)
            except ValueError as error:
                raise ValueError(f"{sample['name']}, observação {index}: {error}") from error
        sample.update(values=values, missing=missing)
    return samples, excluded
