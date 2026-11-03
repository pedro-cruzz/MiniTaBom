"""Correlação e mínimos quadrados com intercepto e preditores contínuos."""
import math
from itertools import combinations
from core import _numeric_value
from inference import scientific_stats


def _validate(headers, columns, minimum=1):
    if (len(columns) < minimum or any(type(i) is not int or not 0 <= i < len(headers) for i in columns)
            or len(set(columns)) != len(columns)):
        raise ValueError(f'Selecione pelo menos {minimum} coluna(s) válida(s), sem repetir.')


def _confidence(value):
    if not math.isfinite(value) or not 0 < value < 100:
        raise ValueError('O nível de confiança deve estar entre 0 e 100, sem os extremos.')


def _columns(headers, rows, columns):
    parsed = []
    for line, row in enumerate(rows, 2):
        values = []
        for index in columns:
            try:
                values.append(_numeric_value(row[index], line))
            except ValueError as error:
                raise ValueError(f'{headers[index]}: {error}') from error
        parsed.append(values)
    return parsed


def _pearson(x, y, np):
    # Escalar antes de centrar evita transbordar a soma/média dos dados brutos.
    a, b = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    a = a / max(1e-300, float(np.max(np.abs(a))))
    b = b / max(1e-300, float(np.max(np.abs(b))))
    a, b = a - a.mean(), b - b.mean()
    na, nb = float(np.linalg.norm(a)), float(np.linalg.norm(b))
    if not na or not nb:
        return None
    return max(-1., min(1., float(np.dot(a / na, b / nb))))


def correlations(headers, rows, columns, method='pearson', missing='pairwise', confidence=95):
    _validate(headers, columns, 2)
    _confidence(confidence)
    if method not in ('pearson', 'spearman') or missing not in ('pairwise', 'listwise'):
        raise ValueError('Método de correlação ou tratamento de ausentes inválido.')
    stats = scientific_stats()
    import numpy as np
    parsed = _columns(headers, rows, columns)
    complete = [row for row in parsed if all(value is not None for value in row)]
    pairs = []
    for i, j in combinations(range(len(columns)), 2):
        valid = [(row[i], row[j]) for row in (complete if missing == 'listwise' else parsed)
                 if row[i] is not None and row[j] is not None]
        n, r, p, ci, reason = len(valid), None, None, None, ''
        if n < 3:
            reason = 'Pelo menos três pares válidos são necessários nesta implementação.'
        else:
            x, y = zip(*valid)
            if method == 'spearman':
                x, y = stats.rankdata(x, method='average'), stats.rankdata(y, method='average')
            r = _pearson(x, y, np)
            if r is None:
                reason = 'Uma das variáveis é constante nos pares analisados.'
            else:
                if 1 - abs(r) <= 8 * np.finfo(float).eps:
                    r = math.copysign(1., r)
                    p = 0.
                else:
                    t = r * math.sqrt((n - 2) / ((1 - r) * (1 + r)))
                    p = float(2 * stats.t.sf(abs(t), n - 2))
                if method == 'pearson' and n > 3:
                    if abs(r) == 1:
                        ci = (r, r)
                    else:
                        z = math.atanh(r)
                        margin = float(stats.norm.isf((1 - confidence / 100) / 2)) / math.sqrt(n - 3)
                        ci = (math.tanh(z - margin), math.tanh(z + margin))
        pairs.append(dict(first=i, second=j, n=n, excluded=len(rows) - n, r=r, p=p, ci=ci, reason=reason))
    return dict(labels=[headers[i] for i in columns], method=method, missing=missing,
                confidence=confidence, pairs=pairs)


def linear_regression(headers, rows, response, predictors, confidence=95):
    _validate(headers, [response, *predictors], 2)
    _confidence(confidence)
    stats = scientific_stats()
    import numpy as np
    parsed = _columns(headers, rows, [response, *predictors])
    retained = [(i + 1, row) for i, row in enumerate(parsed) if all(v is not None for v in row)]
    n, k = len(retained), len(predictors) + 1
    if n <= k:
        raise ValueError(f'O modelo precisa de mais de {k} linhas completas para estimar o erro.')
    try:
        with np.errstate(over='raise', invalid='raise', divide='raise'):
            data = np.asarray([row for _, row in retained], dtype=float)
            y, x = data[:, 0], data[:, 1:]
            ym, xm = float(y.mean()), x.mean(axis=0)
            yc, xc = y - ym, x - xm
            xs = np.linalg.norm(xc, axis=0)
            if np.any(xs == 0):
                raise ValueError('Remova preditores constantes nas linhas completas do modelo.')
            ys = float(np.max(np.abs(yc))) or 1.
            z, yt = xc / xs, yc / ys
            design = np.column_stack((np.ones(n), z))
            u, singular, vt = np.linalg.svd(design, full_matrices=False)
            condition = float(singular[0] / singular[-1]) if singular[-1] else math.inf
            if not math.isfinite(condition) or condition > 1e10:
                raise ValueError('Preditores dependentes ou quase colineares: remova colunas redundantes.')
            b = vt.T @ ((u.T @ yt) / singular)
            residual_scaled = yt - design @ b
            tolerance = 32 * np.finfo(float).eps * max(n, k) * float(np.linalg.norm(yt))
            perfect = float(np.linalg.norm(residual_scaled)) <= tolerance
            if perfect:
                residual_scaled = np.zeros(n)
            residual = ys * residual_scaled
            fitted = y - residual
            df = n - k
            sse = float(np.dot(residual, residual))
            sst = float(np.dot(yc, yc))
            if (not np.isfinite([sse, sst]).all() or (np.any(yc != 0) and sst == 0)
                    or (not perfect and sse == 0)):
                raise ValueError('Magnitude dos dados excede a precisão numérica suportada.')
            mse, ssr = sse / df, max(0., sst - sse)
            slopes = b[1:] * ys / xs
            intercept = ym + ys * b[0] - float(xm @ slopes)
            coefficients = np.r_[intercept, slopes]
            inverse = (vt.T / singular ** 2) @ vt
            transform = np.zeros((k, k))
            transform[0, 0], transform[0, 1:] = ys, -ys * xm / xs
            transform[np.arange(1, k), np.arange(1, k)] = ys / xs
            covariance = transform @ inverse @ transform.T * float(np.dot(residual_scaled, residual_scaled) / df)
            se = np.sqrt(np.maximum(0., covariance.diagonal()))
            leverage = np.minimum(1., np.sum(u * u, axis=1))
            critical = float(stats.t.isf((1 - confidence / 100) / 2, df))
            if not np.isfinite(np.r_[coefficients, se, critical, fitted, residual, leverage, mse]).all():
                raise ValueError('Magnitude dos dados excede a precisão numérica suportada.')
            terms = []
            for i, (coef, error) in enumerate(zip(coefficients, se)):
                t = float(coef / error) if error else None
                p = float(2 * stats.t.sf(abs(t), df)) if t is not None else None
                if t is not None and not math.isfinite(t):
                    raise ValueError('Magnitude dos coeficientes excede a precisão numérica suportada.')
                terms.append(dict(label='Constante' if i == 0 else headers[predictors[i - 1]],
                                  coefficient=float(coef), se=float(error), t=t, p=p,
                                  low=float(coef - critical * error), high=float(coef + critical * error),
                                  vif=None if i == 0 else max(1., float(inverse[i, i]))))
            r2 = max(0., min(100., 100 * (1 - sse / sst))) if sst else None
            adjusted = max(0., 100 * (1 - mse / (sst / (n - 1)))) if sst else None
            f = (ssr / (k - 1)) / mse if mse else None
            p = float(stats.f.sf(f, k - 1, df)) if f is not None else None
            press = None
            if np.all(1 - leverage > 128 * np.finfo(float).eps):
                deleted = residual / (1 - leverage)
                press = float(np.dot(deleted, deleted))
            predicted = max(0., 100 * (1 - press / sst)) if press is not None and sst else None
            s = math.sqrt(mse)
            standardized, cooks = [], []
            for e, h in zip(residual, leverage):
                value = float(e / (s * math.sqrt(1 - h))) if s and 1 - h > 128 * np.finfo(float).eps else None
                standardized.append(value)
                cooks.append(float(value * value * h / (k * (1 - h))) if value is not None else None)
            numeric = [v for v in [f, press, predicted, adjusted, *standardized, *cooks] if v is not None]
            if not all(math.isfinite(v) for v in numeric):
                raise ValueError('Magnitude dos diagnósticos excede a precisão numérica suportada.')
    except (ArithmeticError, np.linalg.LinAlgError) as error:
        raise ValueError('Não foi possível ajustar o modelo com esta precisão numérica.') from error
    return dict(response=headers[response], predictors=[headers[i] for i in predictors],
                n=n, excluded=len(rows) - n, row_numbers=[i for i, _ in retained], terms=terms,
                confidence=confidence, df_model=k - 1, df_error=df, df_total=n - 1,
                ss_model=ssr, ss_error=sse, ss_total=sst, ms_error=mse, f=f, p=p,
                s=s, r2=r2, adjusted=adjusted, press=press, predicted=predicted,
                fitted=fitted.tolist(), residuals=residual.tolist(), observed=y.tolist(),
                x=x.tolist(), leverage=leverage.tolist(), standardized=standardized,
                cooks=cooks, perfect=perfect, condition=condition,
                prediction_state=dict(x_mean=xm.tolist(), x_scale=xs.tolist(),
                    y_mean=ym, y_scale=ys, coefficients=b.tolist(),
                    inverse_factor=(vt.T / singular).tolist()))


def number(value):
    if value is None:
        return 'indefinido'
    if math.isinf(value):
        return '+∞' if value > 0 else '−∞'
    return f'{value:.9g}'


def pvalue(value):
    return 'indefinido' if value is None else '<0,000001' if value < 1e-6 else f'{value:.6g}'


def format_correlation(result):
    lines = ['CORRELAÇÃO DE ' + result['method'].upper(), '',
             'Ausentes: ' + ('exclusão por par' if result['missing'] == 'pairwise' else 'somente linhas completas em todas as variáveis'),
             'H0: correlação = 0; H1: correlação ≠ 0. Valores-p sem ajuste para comparações múltiplas.', '']
    for i, label in enumerate(result['labels'], 1):
        lines.append(f'V{i}: {label}')
    lines += ['', f"{'Par':<12} {'N':>6} {'Coeficiente':>14} {'Valor-p':>14}"]
    for pair in result['pairs']:
        label = f"V{pair['first'] + 1} × V{pair['second'] + 1}"
        lines.append(f"{label:<12} {pair['n']:>6} {number(pair['r']):>14} {pvalue(pair['p']):>14}")
        if pair['reason']:
            lines.append('  ' + pair['reason'])
        if pair['ci'] is not None:
            lines.append(f"  IC individual de {result['confidence']:g}% (Fisher): ({number(pair['ci'][0])}; {number(pair['ci'][1])})")
    lines += ['', 'IC de Pearson disponível com mais de três pares; IC de Spearman ainda não implementado.']
    return '\n'.join(lines) + '\n'


def format_regression(result, observations=False):
    terms = result['terms']
    equation = number(terms[0]['coefficient'])
    for term in terms[1:]:
        equation += (' − ' if term['coefficient'] < 0 else ' + ') + number(abs(term['coefficient'])) + ' × ' + term['label']
    lines = ['REGRESSÃO LINEAR — ' + result['response'], '', result['response'] + ' = ' + equation,
             f"N = {result['n']}    Linhas excluídas por ausentes = {result['excluded']}",
             'Mínimos quadrados com intercepto; preditores numéricos.', '',
             f"{'Termo':<24} {'Coef':>14} {'EP Coef':>14} {'T':>12} {'Valor-p':>12} {'VIF':>10}"]
    for term in terms:
        label = term['label'] if len(term['label']) <= 23 else term['label'][:20] + '…'
        lines.append(f"{label:<24} {number(term['coefficient']):>14} {number(term['se']):>14} {number(term['t']):>12} {pvalue(term['p']):>12} {number(term['vif']) if term['vif'] is not None else '—':>10}")
        lines.append(f"  {term['label']} — IC de {result['confidence']:g}%: ({number(term['low'])}; {number(term['high'])})")
    lines += ['', 'Resumo do modelo',
              f"S = {number(result['s'])}    R² = {number(result['r2'])}%    R² ajustado = {number(result['adjusted'])}%",
              f"PRESS = {number(result['press'])}    R² predito = {number(result['predicted'])}%", '',
              'Análise de variância', f"{'Fonte':<18} {'GL':>6} {'SQ':>16} {'QM':>16} {'F':>12} {'Valor-p':>12}",
              f"{'Regressão':<18} {result['df_model']:>6} {number(result['ss_model']):>16} {number(result['ss_model'] / result['df_model']):>16} {number(result['f']):>12} {pvalue(result['p']):>12}",
              f"{'Erro':<18} {result['df_error']:>6} {number(result['ss_error']):>16} {number(result['ms_error']):>16}",
              f"{'Total':<18} {result['df_total']:>6} {number(result['ss_total']):>16}"]
    if result['perfect']:
        lines += ['', 'Ajuste com erro residual nulo na precisão do cálculo; testes t/F e resíduos padronizados indefinidos.']
    if result['ss_total'] == 0:
        lines.append('Resposta constante: os coeficientes de determinação são indefinidos.')
    if observations:
        lines += ['', f"{'Linha':>7} {'Y':>14} {'Ajustado':>14} {'Resíduo':>14} {'ResPad':>14} {'Alavancagem':>14} {'Cook':>14}"]
        for values in zip(result['row_numbers'], result['observed'], result['fitted'], result['residuals'],
                          result['standardized'], result['leverage'], result['cooks']):
            lines.append(f'{values[0]:>7}' + ''.join(f'{number(v):>14}' for v in values[1:]))
    return '\n'.join(lines) + '\n'
