"""Expressões aritméticas por linha; AST permitido, sem eval/exec."""
import ast
from decimal import Decimal, localcontext
import math
import operator
from data_operations import _validate, _append_columns, unique_name

OPERATORS={ast.Add:operator.add,ast.Sub:operator.sub,ast.Mult:operator.mul,ast.Div:operator.truediv,
           ast.Mod:operator.mod,ast.Pow:operator.pow}
FUNCTIONS={'abs':abs,'sqrt':math.sqrt,'log':math.log,'log10':math.log10,'exp':math.exp,'round':round}


def append_generated(headers,rows,names,columns):
    _validate(headers,rows)
    used=set(headers);created=[]
    for name in names:
        if not name.strip():raise ValueError('Informe nome não vazio para o destino.')
        resolved=unique_name(name.strip(),used);used.add(resolved);created.append(resolved)
    if len(names)!=len(columns) or any(len(c)!=len(rows) for c in columns):
        raise ValueError('As colunas geradas devem preservar as linhas da planilha.')
    new_headers,new_rows=_append_columns(headers,rows,created,columns)
    return new_headers,new_rows,created


def calculate_column(headers,rows,expression,name='Calculado'):
    _validate(headers,rows)
    try:tree=ast.parse(expression,mode='eval')
    except (SyntaxError,ValueError):raise ValueError('Expressão inválida. Use C1, C2, operações e funções permitidas.') from None
    nodes=list(ast.walk(tree))
    if len(nodes)>100:raise ValueError('Use expressão com até 100 elementos.')
    valid=(ast.Expression,ast.BinOp,ast.UnaryOp,ast.Call,ast.Name,ast.Load,ast.Constant,ast.UAdd,ast.USub,*OPERATORS.keys())
    if any(not isinstance(n,valid) for n in nodes):raise ValueError('Esta operação não é permitida na calculadora.')
    for node in nodes:
        if isinstance(node,ast.Name) and node.id not in FUNCTIONS:
            if not node.id.startswith('C') or not node.id[1:].isdigit() or not 1<=int(node.id[1:])<=len(headers):
                raise ValueError('Use identificadores de coluna C1, C2 etc.')
        if isinstance(node,ast.Call) and (not isinstance(node.func,ast.Name) or node.func.id not in FUNCTIONS
                                       or node.keywords or not 1<=len(node.args)<=2):
            raise ValueError('Função não permitida ou quantidade de argumentos inválida.')
        if isinstance(node,ast.Constant) and (type(node.value) not in (int,float) or abs(node.value)>1e308 or not math.isfinite(node.value)):
            raise ValueError('Use somente constantes numéricas finitas.')
    def evaluate(node,row):
        if isinstance(node,ast.Expression):return evaluate(node.body,row)
        if isinstance(node,ast.Constant):return Decimal(str(node.value))
        if isinstance(node,ast.Name):
            raw=row[int(node.id[1:])-1].strip()
            if raw in ('','*'):return None
            value=Decimal(raw.replace(',','.'))
            if not value.is_finite():raise ValueError('Valor não finito na coluna.')
            return value
        if isinstance(node,ast.UnaryOp):
            value=evaluate(node.operand,row)
            return None if value is None else -value if isinstance(node.op,ast.USub) else value
        if isinstance(node,ast.BinOp):
            a,b=evaluate(node.left,row),evaluate(node.right,row)
            if a is None or b is None:return None
            if isinstance(node.op,ast.Pow) and abs(b)>1000:raise ValueError('Expoente fora do limite de 1000.')
            return OPERATORS[type(node.op)](a,b)
        args=[evaluate(arg,row) for arg in node.args]
        if any(a is None for a in args):return None
        if node.func.id=='round' and len(args)==2:
            if args[1]!=int(args[1]) or not -15<=int(args[1])<=15:raise ValueError('Casas decimais entre −15 e 15.')
            result=round(args[0],int(args[1]))
        else:result=FUNCTIONS[node.func.id](*args)
        return Decimal(str(result))
    output=[]
    for line,row in enumerate(rows,1):
        try:
            with localcontext() as context:
                context.prec=40
                value=evaluate(tree,row)
            if value is not None and not math.isfinite(float(value)):raise ValueError('Resultado não finito.')
        except (ValueError,ArithmeticError,TypeError,OverflowError) as error:
            raise ValueError(f'Linha {line}: {error}') from error
        output.append('' if value is None else str(value))
    return append_generated(headers,rows,[name],[output])


def regression_columns(headers,rows,result):
    columns=[]
    for key in ('fitted','residuals','standardized','leverage','cooks'):
        values=['']*len(rows)
        for line,value in zip(result['row_numbers'],result[key]):
            values[line-1]='' if value is None else format(value,'.17g')
        columns.append(values)
    return append_generated(headers,rows,['Ajustados','Resíduos','Resíduos padronizados','Alavancagem','Cook'],columns)
