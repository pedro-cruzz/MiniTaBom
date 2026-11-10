# MiniTaBom 0.7.0 — diagnósticos e testes de postos

Continuação autorizada das entregas de plataforma, mantendo o alvo Minitab 16.2.4.0. Métodos numéricos existentes foram integrados ao contrato de resultados; nenhuma paridade integral foi declarada.

## Recursos entregues

Normalidade Anderson–Darling, Ryan–Joiner, KS com normal estimada, Shapiro–Wilk e D’Agostino–Pearson agora conservam método, opções, ausentes, estatística, valor-p ou limite de probabilidade, versões e revisão/fingerprint por coluna. Os métodos adicionais não são apresentados como confirmação de presença no Minitab 16.

O snapshot dos valores permite reconstruir o gráfico de probabilidade da execução histórica, mesmo após editar a planilha. Ver gráficos usa o resultado salvo; reexecutar calcula novamente com os valores atuais resolvidos pelo ID da coluna. Os limites de N, os valores-p aproximados e as ressalvas numéricas anteriores permanecem. A divergência documental Ryan–Joiner já registrada em METODOS_ESTUDO.md não foi resolvida por uma execução diferencial nesta entrega.

Mann–Whitney, Wilcoxon pareado, Kruskal–Wallis e igualdade de variâncias (Levene centrado na mediana/média ou Bartlett) passam a preservar seus parâmetros e resultados no histórico. Automático/exato/aproximado são guardados como solicitação; o resultado guarda o método efetivo. Correção de continuidade, regra de zeros, hipótese alternativa, centro de Levene/Bartlett, exclusões, resumos e GL são preservados. O núcleo passou a expor contagens de exclusões/zeros e indicação de empates como campos estruturados, sem mudar o cálculo.

Nos dados empilhados, a ordem dos grupos é estabelecida na primeira execução e reutilizada, evitando inverter uma hipótese unilateral após ordenar as linhas. Trocar/adicionar/remover um nível exige iniciar outra análise. O fluxo Wilcoxon continua pareado em duas colunas. Exatos com novos empates/zeros incompatíveis recusam a reexecução e conservam resultado/sessão/tabela anteriores.

## Código e persistência

- `diagnostic_service.py`: execução independente de Tk, registros completos e snapshots de normalidade.
- `diagnostic_contract.py`: valida parâmetros, fontes, grupos/contagens, estatísticas/GL e probabilidades limitadas antes de instalar/gravar um projeto.
- `study_tests.py`: ordem explícita opcional e metadados de exclusões/zeros/empates; os algoritmos e seus limites anteriores foram preservados.
- `workspace_model.py`, `analysis_service.py`, `app.py` e histórico: roteamento, salvar/reabrir/exportar/reexecutar e gráficos históricos.
- `project.py`: o mesmo limite de 256 MiB vale para leitura e gravação. Uma gravação excessiva recusa a substituição e limpa o temporário, preservando o arquivo anterior.
- Histórico: a janela libera seu grab modal quando a reexecução abre gráficos, permitindo interagir com eles.

O esquema do projeto continua statlab v2; registros anteriores abrem sem inventar parâmetros para relatórios textuais legados. CAPACIDADES.json foi atualizado com IDs novos, preservando os anteriores e a proveniência da auditoria. Implementação e validação16 continuam em campos separados.

## Verificação

**328 testes aprovados e 23 exemplos válidos.** Saídas originais e ambiente em `unittest.log`, `examples.log` e `verification.json`.

Quatorze testes novos cobrem ida/volta e reexecução dos cinco métodos de normalidade; RJ com p>0,1 preservado como limite e não transformado em p=0,1; cauda exata de Mann–Whitney por combinação e de Wilcoxon por sinais; zeros/empates e as três regras de zeros; caso de diferenças todas zero; Kruskal com H=7,2 e cauda qui-quadrado fechada; Levene/Bartlett e GL; ordem dos grupos após reordenação; contratos inválidos; gráfico histórico; erro exato após novos empates; fonte removida; liberação dos gráficos; gravação acima do limite sem sobrescrever o original.

O exemplo sintético `exemplo_diagnosticos_historico.statlab` contém as novas rotas de histórico. Nenhum material original da faculdade foi incluído.

O teste portátil do executável foi ampliado para normalidade/RJ, gráfico histórico, testes de postos, Bartlett e salvar/reabrir/reexecutar. Executável 0.7.0, smoke test, CRC e SHA256 aprovados; evidência em `package-verification.json`. Não houve CI remoto ou teste em Windows limpo.

Não foi executada comparação nova no Minitab 16; o caminho da referência instalada continua indisponível neste computador. Testes analíticos/internos não comprovam todos os padrões e opções da versão 16. Não houve push, publicação de Release ou alteração da instalação Minitab.

## Pendências e sequência

Completar os fundamentos ainda ausentes e opções históricas (incluindo duas taxas de Poisson), integrar os demais métodos/resultados, tarefas longas/cancelamento, recuperação, tipos/metadados efetivos e editor/exportação geral de gráficos. Depois avançar nas famílias restantes da auditoria, sem excluir modelos, qualidade/medição, DOE, confiabilidade, multivariada, séries e automação. Inventário completo por função/opção e validação diferencial no 16 permanecem necessários.
