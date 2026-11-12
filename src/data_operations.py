"""Transformações que constroem uma nova tabela antes de alterar a planilha."""
from decimal import Decimal, InvalidOperation


MAX_ROWS, MAX_COLUMNS, MAX_CELLS = 200_000, 512, 2_000_000


def _validate(headers, rows):
    if not headers or len(set(headers)) != len(headers) or any(not isinstance(h, str) or not h.strip() for h in headers):
        raise ValueError('Cabeçalhos devem ser únicos e não vazios.')
    if any(len(row) != len(headers) or any(not isinstance(v, str) for v in row) for row in rows):
        raise ValueError('A tabela deve ser retangular e conter textos de célula.')


def _columns(headers, indices):
    if not indices or len(set(indices)) != len(indices) or any(type(i) is not int or not 0 <= i < len(headers) for i in indices):
        raise ValueError('Selecione colunas diferentes e válidas.')


def _decimal(raw, line, label):
    try:
        value = Decimal(raw.replace(',', '.'))
        if not value.is_finite():
            raise ValueError
    except (InvalidOperation, ValueError):
        raise ValueError(f'Linha {line}, {label}: número finito inválido {raw!r}.') from None
    return value


def sort_rows(headers, rows, keys, types=None, descending=None, missing_last=True, case_sensitive=True):
    _validate(headers, rows)
    _columns(headers, keys)
    types = ['auto'] * len(keys) if types is None else list(types)
    descending = [False] * len(keys) if descending is None else list(descending)
    if len(types) != len(keys) or len(descending) != len(keys) or any(t not in ('auto', 'numeric', 'text') for t in types):
        raise ValueError('Informe tipo e direção para cada chave de ordenação.')
    if any(type(v) is not bool for v in descending):
        raise ValueError('Direções de ordenação inválidas.')
    caches, resolved = [], []
    for column, mode in zip(keys, types):
        raw = [row[column].strip() for row in rows]
        if mode == 'auto':
            try:
                values = [None if v in ('', '*') else _decimal(v, line, headers[column]) for line, v in enumerate(raw, 1)]
                mode = 'numeric'
            except ValueError:
                mode = 'text'
        if mode == 'numeric':
            values = [None if v in ('', '*') else _decimal(v, line, headers[column]) for line, v in enumerate(raw, 1)]
        else:
            values = [None if v in ('', '*') else v if case_sensitive else v.casefold() for v in raw]
        caches.append(values)
        resolved.append(mode)
    order = list(range(len(rows)))
    # Ordenações estáveis da chave menos importante à mais importante.
    # Ausentes são particionados para não inverter sua posição no descendente.
    for values, reverse in reversed(list(zip(caches, descending))):
        present, absent = [], []
        for index in order:
            (absent if values[index] is None else present).append(index)
        present.sort(key=values.__getitem__, reverse=reverse)
        order = present + absent if missing_last else absent + present
    result = [list(rows[i]) for i in order]
    details = [f"{headers[key]} ({'numérico' if mode == 'numeric' else 'texto'}, {'decrescente' if reverse else 'crescente'})"
               for key, mode, reverse in zip(keys, resolved, descending)]
    return list(headers), result, dict(operation='Ordenar linhas', rows=len(rows),
                                      details=details, changed=result != rows,
                                      missing_position='final' if missing_last else 'início')


def unique_name(name, used):
    base, index = name, 2
    while name in used:
        name = f'{base} ({index})'
        index += 1
    return name


def _append_columns(headers, rows, names, columns, context=None):
    height, width = max([len(rows)] + [len(c) for c in columns]), len(headers) + len(names)
    if height > MAX_ROWS or width > MAX_COLUMNS or height * width > MAX_CELLS:
        raise ValueError(f'O resultado excede os limites desta operação: {MAX_ROWS} linhas, {MAX_COLUMNS} colunas e {MAX_CELLS} células.')
    result = []
    for i in range(height):
        if context is not None and i % 4096 == 0:
            context.report(i / height, 'Preparando a tabela de destino…')
        result.append((list(rows[i]) if i < len(rows) else [''] * len(headers)) +
                      [column[i] if i < len(column) else '' for column in columns])
    if context is not None:
        context.report(1., 'Tabela de destino preparada')
    return list(headers) + names, result


def stack_columns(headers, rows, columns, value_name='Valor', label_name='Origem', omit_missing=False):
    _validate(headers, rows)
    _columns(headers, columns)
    names = [value_name.strip(), label_name.strip()]
    if any(not n or n in headers for n in names) or names[0] == names[1]:
        raise ValueError('Use nomes novos, diferentes e não vazios para as duas colunas de destino.')
    values, labels, omitted = [], [], 0
    if len(rows) * len(columns) > MAX_ROWS:
        # Mesmo com omissão, evite uma lista intermediária ilimitada.
        valid_count = sum(not omit_missing or row[c].strip() not in ('', '*') for c in columns for row in rows)
        if valid_count > MAX_ROWS:
            raise ValueError(f'O empilhamento aceita até {MAX_ROWS} valores de destino.')
    for column in columns:
        for row in rows:
            value = row[column]
            if omit_missing and value.strip() in ('', '*'):
                omitted += 1
                continue
            values.append(value)
            labels.append(headers[column])
    if not values:
        raise ValueError('Não há valores para empilhar com estas opções.')
    new_headers, new_rows = _append_columns(headers, rows, names, [values, labels])
    return new_headers, new_rows, dict(operation='Empilhar colunas', changed=True, rows=len(values),
                                      created=names, omitted=omitted,
                                      details=['Ordem das fontes: ' + ', '.join(headers[i] for i in columns)])


def unstack_column(headers, rows, value_column, group_column, prefix='Separado',
                   omit_missing=False, include_missing_groups=False):
    _validate(headers, rows)
    _columns(headers, [value_column, group_column])
    prefix = prefix.strip()
    if not prefix:
        raise ValueError('Informe um prefixo não vazio para as colunas de destino.')
    groups, omitted, missing_groups = {}, 0, 0
    for row in rows:
        label = row[group_column].strip()
        key = None if label in ('', '*') else label
        if key is None and not include_missing_groups:
            missing_groups += 1
            continue
        values = groups.setdefault(key, [])
        if omit_missing and row[value_column].strip() in ('', '*'):
            omitted += 1
        else:
            values.append(row[value_column])
    if not groups:
        raise ValueError('Não há grupos para desempilhar com estas opções.')
    if len(groups) + len(headers) > MAX_COLUMNS:
        raise ValueError(f'O resultado pode ter no máximo {MAX_COLUMNS} colunas.')
    names, used = [], set(headers)
    for label in groups:
        name = unique_name(prefix + (' [ausente]' if label is None else f' [{label!r}]'), used)
        used.add(name)
        names.append(name)
    new_headers, new_rows = _append_columns(headers, rows, names, list(groups.values()))
    return new_headers, new_rows, dict(operation='Desempilhar por grupo', changed=True, rows=len(rows),
                                      created=names, omitted=omitted, missing_groups=missing_groups,
                                      details=[f'Valores: {headers[value_column]}; por: {headers[group_column]}'])


def format_operation(meta):
    lines = ['OPERAÇÃO DE DADOS — ' + meta['operation'], '', *meta['details']]
    if 'created' in meta:
        lines.append('Colunas adicionadas: ' + ', '.join(meta['created']))
    if 'missing_position' in meta:
        lines.append('Ausentes no ' + meta['missing_position'])
    lines.append(f"Linhas/valores processados: {meta['rows']}")
    if 'omitted' in meta:
        lines.append(f"Valores ausentes omitidos: {meta['omitted']}")
    if 'missing_groups' in meta:
        lines.append(f"Linhas com grupo ausente omitidas: {meta['missing_groups']}")
    lines.append('Execute novamente as análises para usar os dados atuais.')
    return '\n'.join(lines) + '\n'
