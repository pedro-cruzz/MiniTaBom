# MiniTaBom 0.6.0 — previsões e ANOVA persistentes

Duas integrações da plataforma foram concluídas nesta continuação autorizada. Os métodos numéricos existentes foram reaproveitados; a referência alvo continua Minitab 16.2.4.0 e a equivalência integral não foi declarada.

## Previsões vinculadas

`prediction_service.py` e `prediction_contract.py` introduzem registros de previsão com vínculo explícito ao ID de uma regressão já salva. Preservam casos/numeração, mapeamento das colunas por ID, confiança efetiva, direção dos intervalos, valores sem arredondamento, IC/IP, extrapolação, alavancagem, ausentes e proveniência. A validação exige que o modelo exista antes da previsão e confira dimensões/formatos compatíveis.

O histórico distingue duas ações. Recalcular casos salvos usa os casos digitados originais. Recalcular colunas atuais relê o mapeamento salvo e conserva a política de ausentes. Ambas usam o ajuste original, sem novo ajuste e sem substituir silenciosamente por um modelo posterior. Cada execução preserva o resultado anterior e registra seu vínculo.

Uma previsão histórica pode ser recalculada mesmo após mudar a amostra de treinamento: o modelo salvo é um snapshot imutável. Isso é explicitado no relatório e nos nomes dos botões. Uma previsão nova pelo menu Regressão mantém a regra 0.5.0 de exigir modelo compatível com a origem atual. Os casos podem vir de outra planilha pelo serviço; a UI atual usa a planilha ativa do modelo.

Modelos/casos fixos não são marcados como dependentes dos dados atuais. Para previsões por colunas, o fingerprint acompanha apenas essas entradas. Colunas renomeadas/reordenadas mantêm a identidade; removê-las recusa a reexecução. Os valores originais continuam consultáveis. Limites infinitos unilaterais usam as etiquetas JSON já estabelecidas, sem NaN/Infinity literais.

## ANOVA de um fator

`anova_service.py` e `anova_contract.py` persistem ANOVA clássica/Welch nos dois formatos existentes: grupos em colunas e resposta/fator. O registro inclui parâmetros, grupos/ausentes, estatísticas, comparações, revisão/fingerprint e snapshot dos dados para boxplots. Os nomes/ajustes de Tukey–Kramer, Fisher LSD e Games–Howell continuam os do núcleo existente; não foram acrescentadas novas famílias estatísticas.

A ordem dos grupos em resposta/fator é fixada na primeira execução e preservada na reexecução, evitando inverter os contrastes ao reordenar as linhas. Adicionar/remover/substituir um nível exige iniciar outra análise. O leitor compartilhado de grupos aceita essa ordem opcional e conserva o comportamento anterior quando ela não é fornecida.

Ver gráficos reconstrói os boxplots dos valores guardados na execução, mesmo após mudar a tabela atual. Reexecutar usa as variáveis atuais resolvidas pelos IDs e preserva o relatório/gráfico antigos. Edição geral de cenas e layout continua pendente.

## Integração, validação e distribuição

O roteador comum de reexecução e a tela do histórico atendem aos novos métodos. A leitura/gravação de projeto valida parâmetros, origem, vínculos, intervalos, grupos, contagens e comparações antes de instalar ou salvar o documento. O formato permanece statlab v2; registros anteriores continuam válidos. Nenhum parâmetro foi inventado para textos legados.

**314 testes aprovados e 22 exemplos válidos.** Logs originais e ambiente estão em `unittest.log`, `examples.log` e `verification.json`.

Nove testes novos de previsão cobrem round-trip, vínculo imutável, ausência de refit, limites unilaterais, casos/numeração, mapeamento por IDs, outra folha, ausentes, referências removidas, formato corrompido, exportação e recálculo após alterar o treinamento. O caso analítico verifica previsão 5,5, EP=√0,525, IC e IP usando o quantil fechado de t com dois GL.

Sete testes novos de ANOVA cobrem round-trip/reexecução, F=27 e p=0,001, três métodos de comparação existentes, ordem dos níveis após reordenar, mudanças de grupos, ausentes, imutabilidade dos snapshots, contratos inválidos, boxplot histórico e ausência de alteração parcial em uma execução recusada.

Os exemplos sintéticos `exemplo_previsoes_historico.statlab` e `exemplo_anova_historico.statlab` acompanham o pacote. Nenhum material original da faculdade foi incluído. O registro CAPACIDADES.json foi atualizado sem alterar os IDs anteriores ou apagar a proveniência da auditoria.

O smoke test portátil foi ampliado para previsão vinculada a modelo anterior, ANOVA/comparações, boxplots e salvar/reabrir/reexecutar os dois métodos. Executável 0.6.0, smoke test, CRC do ZIP e SHA256 aprovados; evidência em `package-verification.json`. Não houve CI remoto nem teste em Windows limpo.

Nenhuma fixture foi executada no Minitab 16. Os testes analíticos e de fluxo não são comprovação de paridade com essa versão. Não houve push, publicação de Release ou alteração de instalação Minitab.

## Próximos requisitos

Integrar demais análises ao histórico, completar opções dos fundamentos, cenas editáveis/exportação comum, tarefas longas/cancelamento e recuperação. ANOVA de dois fatores/GLM e demais modelos, qualidade/medição, DOE, confiabilidade, multivariada, séries e automação continuam no escopo da auditoria. O inventário ainda precisa ser decomposto e confirmado por função/opção na instalação 16.
