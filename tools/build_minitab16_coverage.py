"""Exporta visões do registro único. Nunca deriva IDs de textos ou do 22."""
from collections import Counter
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def build():
    registry = json.loads((ROOT/'CAPACIDADES.json').read_text(encoding='utf-8'))
    requirements = registry['requirements']
    if len({r['id'] for r in requirements}) != len(requirements):
        raise ValueError('IDs duplicados no registro de capacidades.')
    return dict(formato='statlab-fila-cobertura-minitab16',versao=2,gerado_de='CAPACIDADES.json',
                alvo=registry['target'],escopo_integral_concluido=registry['inventory_exhaustive'],
                paridade_validada=registry['parity_validated'],requisitos=requirements,
                contagens=dict(registros=len(requirements),por_tipo=dict(Counter(r['kind'] for r in requirements))),
                limites=['Visão gerada; editar estados somente em CAPACIDADES.json.',
                         'Pacotes, requisitos e tópicos não são denominador de porcentagem de funções.',
                         'O backlog do 22 permanece separado; não prova presença no 16.'])


def main():
    result=build()
    path=ROOT/'docs/analise_instalacao/cobertura_minitab16.json'
    path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with (ROOT/'docs/coverage.csv').open('w',encoding='utf-8-sig',newline='') as stream:
        writer=csv.writer(stream)
        writer.writerow(['id','tipo','area','nome','implementacao','interface','validacao16','persistencia','prioridade'])
        for r in result['requisitos']:
            writer.writerow([r['id'],r['kind'],r['area'],r['name'],r['states']['implementation'],
                             r['states']['ui'],r['states']['validation16'],r['states']['persistence'],r['priority']])
    print(json.dumps(result['contagens'],ensure_ascii=False))


if __name__=='__main__':main()
