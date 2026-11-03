"""Tabelas de contingência: Pearson e razão de verossimilhanças."""
import math

from basic_inference import parse_count
from inference import scientific_stats, p_statement
from exact_tables import fisher_probability, FISHER_MAX_TOTAL


MAX_LEVELS = 50
MAX_TOTAL = 2**53 - 1


def _columns(headers, columns):
    if (not columns or len(set(columns)) != len(columns)
            or any(type(c) is not int or not 0 <= c < len(headers) for c in columns)):
        raise ValueError('Selecione colunas válidas e diferentes.')


def _levels(levels, size):
    if levels is None:
        return [str(i + 1) for i in range(size)]
    levels = [str(level).strip() for level in levels]
    if len(levels) != size or any(not label or label == '*' for label in levels) or len(set(levels)) != size:
        raise ValueError('Os rótulos de cada dimensão devem ser únicos e não ausentes.')
    return levels


def chi_square_table(observed, row_labels=None, column_labels=None):
    if (not 2 <= len(observed) <= MAX_LEVELS or not observed
            or not 2 <= len(observed[0]) <= MAX_LEVELS
            or any(len(row) != len(observed[0]) for row in observed)):
        raise ValueError(f'A tabela deve ser retangular, com 2 a {MAX_LEVELS} linhas e colunas.')
    if any(type(x) is not int or x < 0 for row in observed for x in row):
        raise ValueError('A tabela aceita apenas contagens inteiras não negativas.')
    nr, nc = len(observed), len(observed[0])
    row_labels, column_labels = _levels(row_labels, nr), _levels(column_labels, nc)
    row_totals = [sum(row) for row in observed]
    column_totals = [sum(row[j] for row in observed) for j in range(nc)]
    total = sum(row_totals)
    if any(x == 0 for x in row_totals + column_totals):
        raise ValueError('Há linha ou coluna com total zero. Remova essa categoria antes do teste.')
    if total > MAX_TOTAL:
        raise ValueError('O total excede o limite de precisão de contagens suportado.')
    expected = [[ri * cj / total for cj in column_totals] for ri in row_totals]
    residuals = [[x - e for x, e in zip(row, erow)] for row, erow in zip(observed, expected)]
    contributions = [[d * d / e for d, e in zip(row, erow)] for row, erow in zip(residuals, expected)]
    standardized = [[d / math.sqrt(e) for d, e in zip(row, erow)] for row, erow in zip(residuals, expected)]
    adjusted = [[residuals[i][j] / math.sqrt(expected[i][j] * (1 - row_totals[i] / total) *
                 (1 - column_totals[j] / total)) for j in range(nc)] for i in range(nr)]
    pearson = math.fsum(x for row in contributions for x in row)

    def deviance(x, e):
        if x == 0:
            return 2 * e
        r = (x - e) / e
        # A soma dos termos lineares é zero; esta forma evita cancelamento
        # no total, inclusive para contagens grandes quase independentes.
        if abs(r) < 1e-4:
            return 2 * e * (r*r / 2 - r**3 / 6 + r**4 / 12 - r**5 / 20)
        return 2 * (x * math.log(x / e) - (x - e))

    likelihood = max(0., math.fsum(deviance(x, e) for row, erow in zip(observed, expected) for x, e in zip(row, erow)))
    df = (nr - 1) * (nc - 1)
    stats = scientific_stats()
    below_one = sum(e < 1 for row in expected for e in row)
    below_five = sum(e < 5 for row in expected for e in row)
    fisher = fisher_probability(observed) if nr == nc == 2 else None
    return dict(observed=[list(row) for row in observed], expected=expected, residuals=residuals,
                contributions=contributions, standardized=standardized, adjusted=adjusted,
                row_labels=row_labels, column_labels=column_labels, row_totals=row_totals,
                column_totals=column_totals, total=total, df=df, pearson=pearson, likelihood=likelihood,
                p=None if below_one else float(stats.chi2.sf(pearson, df)),
                likelihood_p=None if below_one else float(stats.chi2.sf(likelihood, df)), fisher=fisher,
                below_one=below_one, below_five=below_five, fisher_limited=nr == nc == 2 and total > FISHER_MAX_TOTAL,
                missing_rows=0, zero_rows=0, source='Tabela de contagens')


def categorical_table(headers, rows, row_column, column_column, count_column=None):
    columns = [row_column, column_column] + ([] if count_column is None else [count_column])
    _columns(headers, columns)
    row_levels, column_levels, counts = {}, {}, {}
    missing_rows = zero_rows = 0
    for line, row in enumerate(rows, 2):
        a, b = str(row[row_column]).strip(), str(row[column_column]).strip()
        count_text = '1' if count_column is None else str(row[count_column]).strip()
        if a in ('', '*') or b in ('', '*') or count_text in ('', '*'):
            missing_rows += 1
            continue
        n = parse_count(count_text, f'Linha {line}, frequência')
        if n == 0:
            zero_rows += 1
            continue
        row_levels.setdefault(a, len(row_levels))
        column_levels.setdefault(b, len(column_levels))
        if max(len(row_levels), len(column_levels)) > MAX_LEVELS:
            raise ValueError(f'A tabela aceita até {MAX_LEVELS} categorias em cada dimensão.')
        counts[a, b] = counts.get((a, b), 0) + n
    observed = [[counts.get((a, b), 0) for b in column_levels] for a in row_levels]
    result = chi_square_table(observed, list(row_levels), list(column_levels))
    result.update(source=f'{headers[row_column]} × {headers[column_column]}',
                  missing_rows=missing_rows, zero_rows=zero_rows,
                  weighted=count_column is not None)
    return result


def matrix_table(headers, rows, columns, label_column=None):
    _columns(headers, list(columns) + ([] if label_column is None else [label_column]))
    if not 2 <= len(columns) <= MAX_LEVELS:
        raise ValueError(f'Selecione de 2 a {MAX_LEVELS} colunas de contagens.')
    observed, labels = [], []
    missing_rows = 0
    for line, row in enumerate(rows, 2):
        raw = [str(row[c]).strip() for c in columns]
        if all(x in ('', '*') for x in raw):
            missing_rows += 1
            continue
        if any(x in ('', '*') for x in raw):
            raise ValueError(f'Linha {line}: contagem ausente. Informe 0 onde não houve ocorrências.')
        observed.append([parse_count(x, f'Linha {line}, contagem') for x in raw])
        labels.append(str(len(labels) + 1) if label_column is None else str(row[label_column]).strip())
        if len(observed) > MAX_LEVELS:
            raise ValueError(f'A tabela aceita até {MAX_LEVELS} linhas de contagens.')
    result = chi_square_table(observed, labels, [headers[c] for c in columns])
    result.update(missing_rows=missing_rows)
    return result


def format_contingency(result, show_expected=True, show_residuals=False, show_contributions=False,
                       show_percentages=False):
    def number(value):
        return 'não exibido' if value is None else f'{value:.9g}'
    lines = ['QUI-QUADRADO DE ASSOCIAÇÃO — ' + result['source'], '',
             'H0: as variáveis de linha e coluna são independentes.',
             'H1: existe associação entre as variáveis. Sem correção de Yates.', '']
    lines += [f'C{j + 1} = {label!r}' for j, label in enumerate(result['column_labels'])]
    width = max(12, len(str(result['total'])) + 2)
    lines += ['', ' ' * 10 + ''.join(f'{"C" + str(j + 1):>{width}}' for j in range(len(result['column_labels']))) + f'{"Total":>{width}}']
    for i, row in enumerate(result['observed']):
        lines.append(f'{"R" + str(i + 1):<10}' + ''.join(f'{x:{width}d}' for x in row) + f"{result['row_totals'][i]:{width}d}")
    lines += ['Total     ' + ''.join(f'{x:{width}d}' for x in result['column_totals']) + f"{result['total']:{width}d}", '']
    for i, label in enumerate(result['row_labels']):
        lines.append(f'R{i + 1} = {label!r}')
        details = []
        if show_expected:
            details.append(('Esperadas', result['expected'][i]))
        if show_residuals:
            details += [('Resíduos brutos', result['residuals'][i]), ('Resíduos padronizados', result['standardized'][i]),
                        ('Resíduos ajustados', result['adjusted'][i])]
        if show_contributions:
            details.append(('Contribuições Pearson', result['contributions'][i]))
        if show_percentages:
            details += [('% da linha', [100 * x / result['row_totals'][i] for x in result['observed'][i]]),
                        ('% da coluna', [100 * x / total for x, total in zip(result['observed'][i], result['column_totals'])]),
                        ('% do total', [100 * x / result['total'] for x in result['observed'][i]])]
        lines += ['  ' + name + ': ' + '; '.join(number(x) for x in values) for name, values in details]
    lines += ['', f"N = {result['total']}    GL = {result['df']}",
              f"Pearson = {number(result['pearson'])}    " + p_statement(result['p'], unavailable='não exibido'),
              f"Razão de verossimilhanças = {number(result['likelihood'])}    " + p_statement(result['likelihood_p'], unavailable='não exibido'),
              f"Linhas omitidas por ausentes: {result['missing_rows']}; linhas de frequência zero ignoradas: {result['zero_rows']}"]
    if result['below_one']:
        lines.append('Há frequências esperadas menores que 1; valores-p assintóticos não são exibidos.')
    if result['below_five']:
        lines.append(f"Atenção: {result['below_five']} células têm frequência esperada menor que 5; a aproximação pode ser inadequada.")
    if result['fisher'] is not None:
        lines.append(p_statement(result['fisher'], 'Fisher bilateral 2×2 (SciPy, ordenação por probabilidade): valor-p'))
    elif result['fisher_limited']:
        lines.append(f'Fisher não calculado: limite operacional de {FISHER_MAX_TOTAL} observações no total.')
    return '\n'.join(lines) + '\n'
