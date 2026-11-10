"""Projeto statlab v2: identidade, revisões e resultados JSON, sem widgets."""
from copy import deepcopy
import hashlib
import json
import math
import uuid
from t_analysis_contract import T_ONE_METHOD, T_METHODS, validate_t_parameters
from regression_contract import REGRESSION_METHOD, validate_regression_parameters, validate_linear_model
from prediction_contract import PREDICTION_METHOD, validate_prediction_parameters, validate_prediction_values
from anova_contract import ANOVA_METHOD, validate_anova_parameters, validate_anova_result
from diagnostic_contract import NORMALITY_METHOD,STUDY_METHODS,validate_diagnostic_parameters,validate_diagnostic_result
from two_poisson_contract import TWO_POISSON_METHOD,validate_two_poisson_parameters,validate_two_poisson_result


def identifier(prefix):
    return prefix + '-' + uuid.uuid4().hex


def validate_table(headers, rows):
    if (not isinstance(headers, list) or not headers
            or any(not isinstance(h, str) or not h.strip() for h in headers)
            or len(set(headers)) != len(headers)):
        raise ValueError('Cabeçalhos devem ser únicos e não vazios.')
    if (not isinstance(rows, list)
            or any(not isinstance(row, list) or len(row) != len(headers)
                   or any(not isinstance(v, str) for v in row) for row in rows)):
        raise ValueError('Dados de tabela inválidos.')


def fingerprint(sheet):
    payload = [[(c['id'], c['name']) for c in sheet['columns']], sheet['rows']]
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, separators=(',', ':')).encode('utf-8')).hexdigest()


def new_sheet(name='Worksheet 1', headers=None, rows=None):
    headers = ['Coluna 1', 'Coluna 2', 'Coluna 3'] if headers is None else headers
    rows = [] if rows is None else rows
    validate_table(headers, rows)
    sheet = dict(id=identifier('ws'), name=name, revision=0,
                 columns=[dict(id=identifier('col'), name=h, type='text', format={}, metadata={}) for h in headers],
                 rows=deepcopy(rows), metadata={})
    sheet['fingerprint'] = fingerprint(sheet)
    return sheet


def new_document(headers=None, rows=None, output=''):
    sheet = new_sheet(headers=headers, rows=rows)
    return dict(format='statlab', version=2, project_id=identifier('project'),
                active_worksheet_id=sheet['id'], worksheets=[sheet], analyses=[], output=output,
                metadata={})


def active_sheet(document):
    return next(s for s in document['worksheets'] if s['id'] == document['active_worksheet_id'])


def sync_sheet(sheet, headers, rows):
    """Preserva IDs por nome nas reordenações e por posição em renomeações.

    Transformações que criam/excluem variáveis devem fornecer novos IDs em
    contratos futuros. Não tenta inferir identidade pelo conteúdo numérico.
    """
    validate_table(headers, rows)
    old = sheet['columns']
    by_name = {c['name']: c for c in old}
    used = {by_name[h]['id'] for h in headers if h in by_name}
    columns = []
    for index, name in enumerate(headers):
        if name in by_name:
            column = deepcopy(by_name[name])
        elif len(headers) == len(old) and old[index]['id'] not in used:
            column = deepcopy(old[index])
            used.add(column['id'])
        else:
            column = dict(id=identifier('col'), type='text', format={}, metadata={})
        column['name'] = name
        columns.append(column)
    candidate = dict(sheet, columns=columns, rows=rows)
    current = fingerprint(candidate)
    changed = current != sheet['fingerprint']
    if changed:
        sheet.update(columns=columns, rows=deepcopy(rows), fingerprint=current,
                     revision=sheet['revision'] + 1)
    return changed


def pack_numbers(value):
    """JSON não admite infinito: etiqueta explícita só nos payloads numéricos."""
    if isinstance(value, float) and not math.isfinite(value):
        if math.isnan(value):
            raise ValueError('Resultado contém NaN não permitido.')
        return {'$statlab_number': '+inf' if value > 0 else '-inf'}
    if isinstance(value, dict):
        if '$statlab_number' in value:
            raise ValueError('Chave reservada no resultado.')
        return {k: pack_numbers(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [pack_numbers(v) for v in value]
    return value


def unpack_numbers(value):
    if isinstance(value, dict):
        if '$statlab_number' in value:
            if len(value) != 1 or value['$statlab_number'] not in ('+inf', '-inf'):
                raise ValueError('Etiqueta numérica inválida.')
            return math.inf if value['$statlab_number'] == '+inf' else -math.inf
        return {k: unpack_numbers(v) for k, v in value.items()}
    if isinstance(value, list):
        return [unpack_numbers(v) for v in value]
    return value


def is_stale(result, sheet):
    if result['source'].get('kind') == 'fixed_prediction':
        return False
    if result['source'].get('kind') == 'summary':
        return False
    if 'input_fingerprint' in result['source']:
        try:
            return result['source']['input_fingerprint'] != input_fingerprint(sheet, result['source']['column_ids'])
        except ValueError:
            return True
    return (result['source']['revision'] != sheet['revision']
            or result['source']['fingerprint'] != sheet['fingerprint'])


def input_fingerprint(sheet, column_ids):
    indices=[]
    for column_id in column_ids:
        matches=[i for i,c in enumerate(sheet['columns']) if c['id']==column_id]
        if len(matches)!=1:raise ValueError('Coluna de origem não encontrada.')
        indices.append(matches[0])
    payload=[column_ids,[[row[i] for i in indices] for row in sheet['rows']]]
    return hashlib.sha256(json.dumps(payload,ensure_ascii=False,separators=(',',':')).encode('utf-8')).hexdigest()


def validate_document(document):
    """Valida o documento inteiro antes de o instalar ou gravar."""
    try:
        if not isinstance(document, dict) or document.get('format') != 'statlab' or type(document.get('version')) is not int or document['version'] != 2:
            raise ValueError('Formato ou versão de projeto não suportado.')
        # Também rejeita NaN/Infinity literais e metadados não JSON.
        json.dumps(document, allow_nan=False)
        ids = set()

        def unique(value):
            if not isinstance(value, str) or not value.strip() or len(value) > 128 or value in ids:
                raise ValueError('Identificador vazio, duplicado ou inválido.')
            ids.add(value)

        unique(document['project_id'])
        if not isinstance(document['output'], str) or not isinstance(document['metadata'], dict):
            raise ValueError('Sessão ou metadados inválidos.')
        sheets = document['worksheets']
        if not isinstance(sheets, list) or not 1 <= len(sheets) <= 100:
            raise ValueError('Use entre 1 e 100 planilhas por projeto.')
        names = set()
        for sheet in sheets:
            unique(sheet['id'])
            if not isinstance(sheet['name'], str) or not sheet['name'].strip() or sheet['name'] in names:
                raise ValueError('Nomes de planilha devem ser únicos e não vazios.')
            names.add(sheet['name'])
            if type(sheet['revision']) is not int or sheet['revision'] < 0 or not isinstance(sheet['metadata'], dict):
                raise ValueError('Revisão ou metadados de planilha inválidos.')
            for column in sheet['columns']:
                unique(column['id'])
                if column['type'] not in ('text', 'numeric', 'datetime') or not isinstance(column['format'], dict) or not isinstance(column['metadata'], dict):
                    raise ValueError('Tipo, formato ou metadados de coluna inválidos.')
            validate_table([c['name'] for c in sheet['columns']], sheet['rows'])
            if sheet['fingerprint'] != fingerprint(sheet):
                raise ValueError('Fingerprint da planilha não corresponde aos dados.')
        if document['active_worksheet_id'] not in {s['id'] for s in sheets}:
            raise ValueError('Planilha ativa inexistente.')
        analyses = document['analyses']
        if not isinstance(analyses, list) or len(analyses) > 10000:
            raise ValueError('Histórico inválido ou acima de 10000 análises.')
        selection=document['metadata'].get('active_regression_by_sheet',{})
        if not isinstance(selection,dict):raise ValueError('Seleção de modelos inválida.')
        for sheet_id,analysis_id in selection.items():
            if not isinstance(sheet_id,str) or not isinstance(analysis_id,str) or not any(
                r['analysis_id']==analysis_id and r['method_id']==REGRESSION_METHOD and r['source']['worksheet_id']==sheet_id for r in analyses):
                raise ValueError('Modelo selecionado não corresponde à planilha.')
        analysis_ids = set()
        for result in analyses:
            unique(result['analysis_id'])
            for field in ('method_id', 'created_at', 'report'):
                if not isinstance(result[field], str) or not result[field]:
                    raise ValueError('Registro de análise incompleto.')
            for field in ('parameters', 'source', 'versions', 'missing', 'provenance'):
                if not isinstance(result[field], dict):
                    raise ValueError('Contrato de resultado inválido.')
            if result.get('parent_analysis_id') is not None and result['parent_analysis_id'] not in analysis_ids:
                raise ValueError('Execução anterior não encontrada.')
            analysis_ids.add(result['analysis_id'])
            source = result['source']
            if source['worksheet_id'] not in {s['id'] for s in sheets} or type(source['revision']) is not int or source['revision'] < 0:
                raise ValueError('Origem de análise inválida.')
            if (not isinstance(source['column_ids'], list) or any(not isinstance(c, str) for c in source['column_ids'])
                    or len(set(source['column_ids'])) != len(source['column_ids'])):
                raise ValueError('Referências de colunas inválidas.')
            if not isinstance(source['fingerprint'], str) or len(source['fingerprint']) != 64:
                raise ValueError('Fingerprint de análise inválido.')
            if (result['status'] != 'completed' or not isinstance(result['warnings'], list)
                    or any(not isinstance(w, str) for w in result['warnings']) or not isinstance(result['tables'], list)):
                raise ValueError('Estado ou tabelas de análise inválidos.')
            if not isinstance(result['values'], dict):
                raise ValueError('Valores de análise inválidos.')
            unpack_numbers(result['values'])
            unpack_numbers(result['tables'])
            if result['method_id']==TWO_POISSON_METHOD:
                validate_two_poisson_parameters(result['parameters'],len(source['column_ids']))
                validate_two_poisson_result(dict(result,values=unpack_numbers(result['values'])))
                if result['parameters']['input_kind']!='summary' and 'input_fingerprint' not in source:
                    raise ValueError('Origem de duas taxas Poisson incompleta.')
            if result['method_id']==NORMALITY_METHOD or result['method_id'] in STUDY_METHODS:
                validate_diagnostic_parameters(result['method_id'],result['parameters'],len(source['column_ids']))
                validate_diagnostic_result(result)
                if source.get('kind')!='columns' or 'input_fingerprint' not in source:
                    raise ValueError('Origem do diagnóstico incompleta.')
            if result['method_id']==REGRESSION_METHOD:
                validate_regression_parameters(result['parameters'],len(source['column_ids']))
                validate_linear_model(unpack_numbers(result['values']),len(source['column_ids']))
                if source.get('kind')!='columns' or 'input_fingerprint' not in source:
                    raise ValueError('Origem do modelo linear incompleta.')
                if result.get('scenes')!=[dict(kind='regression_diagnostics',version=1)]:
                    raise ValueError('Especificação gráfica do modelo inválida.')
            if result['method_id']==PREDICTION_METHOD:
                model_id=result['parameters'].get('model_analysis_id')
                model_record=next((r for r in analyses if r['analysis_id']==model_id and r['method_id']==REGRESSION_METHOD),None)
                if model_id not in analysis_ids or model_record is None:raise ValueError('Modelo de previsão inexistente ou posterior à previsão.')
                model=unpack_numbers(model_record['values'])
                validate_prediction_parameters(result['parameters'],len(model['predictors']))
                validate_prediction_values(unpack_numbers(result['values']),result['parameters'],model)
                kind=result['parameters']['input_kind']
                if (source.get('kind')!=('fixed_prediction' if kind=='cases' else 'prediction_columns')
                        or source['column_ids']!=list(dict.fromkeys(result['parameters']['input_column_ids']))
                        or (kind=='columns' and 'input_fingerprint' not in source)):
                    raise ValueError('Origem da previsão incompatível com os parâmetros.')
                if (result['provenance'].get('model_analysis_id')!=model_id
                        or result['missing'].get('rows')!=unpack_numbers(result['values'])['omitted']):
                    raise ValueError('Proveniência/ausentes da previsão inconsistentes.')
            if result['method_id']==ANOVA_METHOD:
                validate_anova_parameters(result['parameters'],len(source['column_ids']))
                validate_anova_result(result)
                if source.get('kind')!='columns' or 'input_fingerprint' not in source:
                    raise ValueError('Origem da ANOVA incompleta.')
            if 'input_fingerprint' in source and (not isinstance(source['input_fingerprint'],str)
                                                   or len(source['input_fingerprint'])!=64):
                raise ValueError('Fingerprint de entrada inválido.')
            if result['method_id'] in T_METHODS:
                _,kind=validate_t_parameters(result['method_id'],result['parameters'],len(source['column_ids']))
                if source.get('kind',kind) != kind:
                    raise ValueError('Origem incompatível com os parâmetros do teste t.')
                if result['method_id'] != T_ONE_METHOD:
                    if source.get('kind') != kind or (kind != 'summary' and 'input_fingerprint' not in source):
                        raise ValueError('Identificação da entrada do teste t incompleta.')
    except (KeyError, TypeError, AttributeError, OverflowError, StopIteration) as error:
        raise ValueError('Estrutura de projeto inválida.') from error
    return document
