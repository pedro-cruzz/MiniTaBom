"""Gera uma fila auditável a partir do mapa de escopo e dos recursos locais.

Cada item é um requisito de trabalho, não uma função do Minitab comprovada.
Nenhuma presença histórica ou equivalência é inferida dos recursos do 22.
"""
from collections import Counter
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def build():
    inventory = json.loads((ROOT / 'INVENTARIO_FUNCIONAL.json').read_text(encoding='utf-8'))
    dialogs = json.loads((ROOT / 'docs/analise_instalacao/dialogos_pt_br.json').read_text(encoding='utf-8'))
    requirements = []
    # O primeiro bloco serve aos fluxos básicos; todas as outras áreas do 16
    # continuam no escopo, sem redução por prioridade ou pelo exercício futuro.
    foundation = {'planilha', 'arquivos', 'calculo', 'descritivas', 'graficos',
                  'distribuicoes', 'inferencia', 'anova', 'regressao', 'tabelas',
                  'nao_parametricos', 'poder_e_tamanho_amostral'}
    for area in inventory['areas']:
        for key, state in [('existente', 'implementacao_parcial_a_auditar'), ('pendente', 'pendente')]:
            for text in area[key]:
                identifier = hashlib.sha256((area['id'] + '\0' + text).encode('utf-8')).hexdigest()[:12]
                requirements.append(dict(
                    id=f"M16-{identifier}", area=area['id'], requisito=text,
                    prioridade=1 if area['id'] in foundation else 2,
                    implementacao=state, presenca_no_16='a_confirmar_por_funcao_e_opcao',
                    validacao_numerica_16='pendente',
                    origem=f"INVENTARIO_FUNCIONAL.json:areas[{area['id']}].{key}",
                    falta_conferir=['menu/comando e opções do 16.2.4.0',
                                    'padrões, entradas, ausentes e casos extremos',
                                    'comparação executada e tolerâncias específicas']))
    candidates = [dict(recurso_22=r['recurso'], titulos=r.get('titulos', {}),
                       estado='triagem_historica_pendente', prioridade=3,
                       evidencia='docs/analise_instalacao/dialogos_pt_br.json',
                       presenca_no_16='nao_estabelecida') for r in dialogs['recursos']]
    result = dict(
        formato='statlab-fila-cobertura-minitab16', versao=1,
        data_revisao_escopo='2026-11-03', alvo=inventory['alvo'],
        decisao_usuario='Todos os recursos do Minitab 16 são prioridade sobre expansões exclusivas do 22.',
        escopo_integral_concluido=False, paridade_validada=False,
        politica=['Prioridade 1: completar os fluxos de dados e análises já iniciados e os fundamentos de estudo.',
                  'Prioridade 2: todas as demais áreas do 16; não são exclusões de escopo.',
                  'Prioridade 3: apenas triagem de recursos do 22 sem confirmação histórica; componentes compartilhados não são funções.',
                  'Exercícios futuros serão associados aos requisitos e aos menus do 16 quando forem recebidos.',
                  'Implementação parcial, presença histórica e paridade numérica são verificações distintas.',
                  'As referências históricas disponíveis são consultadas por item; nenhum item recebe confirmação automática.'],
        referencia_historica='docs/analise_instalacao/referencias_minitab16.json',
        areas=[dict(id=a['id'], estado=a['estado']) for a in inventory['areas']],
        requisitos=requirements, candidatos_22=candidates,
        contagens=dict(areas=len(inventory['areas']), requisitos_de_trabalho=len(requirements),
                       por_estado=dict(Counter(r['implementacao'] for r in requirements)),
                       recursos_22_para_triagem=len(candidates)),
        limites=['Não é inventário exaustivo comando a comando do 16.',
                 'Um requisito pode abranger várias funções e opções; as contagens não medem porcentagem de cobertura.',
                 'A origem existente indica capacidade relatada no pacote, não paridade integral.',
                 'Itens devem ser decompostos e associados a evidências do 16 antes do aceite final.'])
    if len({r['id'] for r in requirements}) != len(requirements):
        raise ValueError('Requisitos duplicados no mapa de escopo.')
    return result


def main():
    result = build()
    path = ROOT / 'docs/analise_instalacao/cobertura_minitab16.json'
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result['contagens'], ensure_ascii=True))


if __name__ == '__main__':
    main()
