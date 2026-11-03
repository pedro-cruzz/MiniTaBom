"""Previsões condicionais ao último modelo linear ajustado."""
import csv
import io
import math
from core import _numeric_value
from inference import scientific_stats
from linear_models import _confidence, _columns, number


def parse_cases(text, width):
    delimiter = '\t' if '\t' in text else ';'
    cases, numbers = [], []
    reader = csv.reader(io.StringIO(text), delimiter=delimiter, strict=True)
    try:
        for row in reader:
            line = reader.line_num
            if not row or all(not v.strip() for v in row):
                continue
            if len(row) != width:
                raise ValueError(f'Linha {line}: informe {width} valor(es), separados por tabulação ou ponto e vírgula.')
            values = [_numeric_value(value, line) for value in row]
            if any(value is None for value in values):
                raise ValueError(f'Linha {line}: informe todos os preditores; ausentes não são aceitos na digitação.')
            cases.append(values)
            numbers.append(line)
    except csv.Error as error:
        raise ValueError('Confira as aspas e os separadores dos novos casos.') from error
    if not cases:
        raise ValueError('Informe pelo menos um novo caso.')
    return cases, numbers


def predict_linear(model, cases, confidence=None, alternative='two-sided', case_numbers=None):
    if not model or 'prediction_state' not in model:
        raise ValueError('Ajuste novamente a regressão antes de prever novos casos.')
    confidence = model['confidence'] if confidence is None else confidence
    _confidence(confidence)
    if alternative not in ('two-sided', 'lower', 'upper'):
        raise ValueError('Tipo de intervalo inválido.')
    width = len(model['predictors'])
    if not cases or any(len(row) != width for row in cases):
        raise ValueError(f'Cada caso precisa de {width} valor(es), na ordem dos preditores do modelo.')
    case_numbers = list(range(1, len(cases) + 1)) if case_numbers is None else case_numbers
    if len(case_numbers) != len(cases):
        raise ValueError('A numeração dos casos não corresponde aos dados.')
    stats = scientific_stats()
    import numpy as np
    state = model['prediction_state']
    try:
        with np.errstate(over='raise', invalid='raise', divide='raise'):
            values = np.asarray(cases, dtype=float)
            if not np.isfinite(values).all():
                raise ValueError('Os novos casos precisam conter somente números finitos.')
            normalized = (values - np.asarray(state['x_mean'])) / np.asarray(state['x_scale'])
            design = np.column_stack((np.ones(len(cases)), normalized))
            fits = state['y_mean'] + state['y_scale'] * (design @ np.asarray(state['coefficients']))
            factor = design @ np.asarray(state['inverse_factor'])
            h = np.sum(factor * factor, axis=1)
            se = model['s'] * np.sqrt(h)
            se_prediction = np.hypot(model['s'], se)
            tail = (1 - confidence / 100) / (2 if alternative == 'two-sided' else 1)
            critical = float(stats.t.isf(tail, model['df_error']))
            if not math.isfinite(critical) or not np.isfinite(np.r_[fits, h, se, se_prediction]).all():
                raise ValueError('Não é possível prever com esses valores e essa precisão.')
            margins = critical * se
            prediction_margins = critical * se_prediction
            ci_low, ci_high = fits - margins, fits + margins
            pi_low, pi_high = fits - prediction_margins, fits + prediction_margins
            if not np.isfinite(np.r_[ci_low, ci_high, pi_low, pi_high]).all():
                raise ValueError('Os limites excedem a precisão numérica suportada.')
    except (ArithmeticError, TypeError, ValueError) as error:
        if isinstance(error, ValueError):
            raise
        raise ValueError('Não é possível prever com esses valores e essa precisão.') from error
    lower = [min(row[j] for row in model['x']) for j in range(width)]
    upper = [max(row[j] for row in model['x']) for j in range(width)]
    max_h = max(model['leverage'])
    records = []
    for i, row in enumerate(values):
        outside = [label for j, label in enumerate(model['predictors']) if not lower[j] <= row[j] <= upper[j]]
        records.append(dict(case=case_numbers[i], values=row.tolist(), fit=float(fits[i]), se_fit=float(se[i]),
            leverage=float(h[i]), ci=(float(ci_low[i]) if alternative != 'upper' else -math.inf,
                                     float(ci_high[i]) if alternative != 'lower' else math.inf),
            pi=(float(pi_low[i]) if alternative != 'upper' else -math.inf,
                float(pi_high[i]) if alternative != 'lower' else math.inf),
            outside=outside, high_leverage=bool(h[i] > max_h + 128 * math.ulp(max(1., max_h)))))
    return dict(response=model['response'], predictors=model['predictors'][:], n=model['n'], confidence=confidence,
                alternative=alternative, cases=records, omitted=[], source='digitados', perfect=model['perfect'])


def predict_columns(model, headers, rows, columns, omit_missing=True, **options):
    if (not model or len(columns) != len(model['predictors'])
            or any(type(i) is not int or not 0 <= i < len(headers) for i in columns)):
        raise ValueError('Mapeie uma coluna para cada preditor do modelo.')
    parsed = _columns(headers, rows, columns)
    cases, numbers, omitted = [], [], []
    for line, values in enumerate(parsed, 1):
        if any(value is None for value in values):
            if not omit_missing:
                raise ValueError(f'Linha da planilha {line}: há preditor ausente.')
            omitted.append(line)
        else:
            cases.append(values)
            numbers.append(line)
    result = predict_linear(model, cases, case_numbers=numbers, **options)
    result.update(source='colunas: ' + ', '.join(headers[i] for i in columns), omitted=omitted)
    return result


def format_predictions(result):
    kind = {'two-sided': 'bilaterais', 'lower': 'limites inferiores', 'upper': 'limites superiores'}[result['alternative']]
    lines = ['PREVISÃO LINEAR — ' + result['response'], '',
             f"Modelo com N={result['n']}; casos de {result['source']}.",
             f"Confiança de {result['confidence']:g}%; intervalos individuais, {kind}.",
             'IC: média da resposta. IP: uma nova observação.',
             'Ordem dos preditores: ' + ', '.join(result['predictors']), '']
    for case in result['cases']:
        lines += [f"Caso {case['case']}: " + '; '.join(f'{label}={number(value)}' for label, value in zip(result['predictors'], case['values'])),
                  '  Previsão = ' + number(case['fit']) + '    EP da média = ' + number(case['se_fit']),
                  '  IC da média: (' + '; '.join(map(number, case['ci'])) + ')',
                  '  IP da observação: (' + '; '.join(map(number, case['pi'])) + ')']
        if case['outside']:
            lines.append('  Fora da faixa observada: ' + ', '.join(case['outside']) + '.')
        if case['high_leverage']:
            lines.append('  Alavancagem maior que a máxima das observações usadas no ajuste.')
        lines.append('')
    lines.append('Linhas omitidas por ausentes: ' + str(len(result['omitted'])))
    if result['perfect']:
        lines.append('Erro residual nulo na precisão do ajuste: os intervalos colapsam na previsão.')
    lines += ['A checagem de faixa é por preditor; não verifica todo o domínio multivariado do modelo.']
    return '\n'.join(lines) + '\n'
