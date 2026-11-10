# MiniTaBom 0.5.0 — regressão persistente

Continuação autorizada da auditoria e das entregas 0.3/0.4. O alvo permanece Minitab 16.2.4.0. A implementação reutiliza o ajuste linear por SVD já existente; esta entrega acrescenta persistência, restauração, UI e verificação do fluxo. Não declara paridade de opções, padrões ou números com a referência.

## Comportamento entregue

O resultado de regressão agora preserva o modelo numérico completo, parâmetros efetivos, versões, IDs/revisão/fingerprint da fonte, exclusão por linhas completas, tabela de coeficientes e relatório. O estado normalizado e o fator usados para previsão são salvos sem arredondamento. O esquema do projeto continua statlab v2; projetos antigos abrem, mas seus relatórios textuais de regressão não são convertidos artificialmente em modelos.

Ao reabrir o projeto, o modelo selecionado da planilha ativa é restaurado quando seus dados de entrada ainda correspondem à origem. Nenhum ajuste numérico é reexecutado nesse processo. Editar resposta/preditores ou removê-los bloqueia a previsão; mudar colunas alheias mantém o modelo. Renomear/reordenar preserva IDs, e os rótulos exibidos para novas previsões acompanham os nomes atuais sem reescrever o resultado histórico. Desfazer pode restaurar a compatibilidade.

Cada planilha mantém sua seleção de modelo no projeto. Em Janela > Histórico de análises, Usar modelo valida a origem, ativa a planilha e seleciona o ajuste. Um modelo desatualizado precisa de novo ajuste antes de prever; os dados não são alterados em uma tentativa recusada.

Ver gráficos reconstrói ajuste e diagnósticos usando o snapshot salvo, mesmo quando a origem atual está diferente. A janela é identificada pela data da execução histórica. Persiste uma especificação versionada de gráfico de diagnósticos; não é ainda um editor/persistência geral de cenas ou do layout das janelas.

Reexecutar preserva o resultado anterior e registra o vínculo com a nova execução. Se o armazenamento de diagnósticos estava habilitado, novas colunas são criadas sem substituir as anteriores. A planilha de origem recebe o armazenamento mesmo se estiver inativa; seu undo/redo inclui a transformação e os IDs de destino.

## Código e contratos

- `regression_service.py`: ajuste estruturado, snapshot, restauração sem refit e rótulos atuais por IDs.
- `regression_contract.py`: valida parâmetros, tamanhos, graus de liberdade, vetores/matrizes, escalas, finitude, termos e estado de previsão. O documento inteiro é validado antes de abrir/salvar; seleções de modelo precisam apontar para uma regressão da planilha correta.
- `analysis_service.py`: roteamento de reexecução para regressão, mantendo os contratos t anteriores.
- `app.py` e `analysis_history_dialog.py`: restauração, seleção por planilha, gráficos históricos e armazenamento/reexecução. A previsão existente usa o modelo restaurado.
- `linear_models.py`: normalização explícita do indicador de ajuste perfeito para bool Python. O valor lógico podia ser um escalar NumPy, inadequado ao contrato JSON; a expressão numérica não mudou.
- `CAPACIDADES.json`: persistência/reexecução/gráficos da regressão atualizados; opções e validação16 seguem separadas e pendentes. Não se declarou a família inteira pronta.

A validação do formato não autentica o arquivo nem comprova numericamente um modelo editado por terceiros. Os arquivos continuam JSON, sem execução de código, eval ou pickle. Modelos inválidos não substituem o documento/cache abertos. A gravação do projeto continua atômica.

## Verificação

**298 testes aprovados e 20 exemplos válidos.** Logs originais e ambiente em `unittest.log`, `examples.log` e `verification.json`.

Onze testes novos verificam: round-trip e previsão sem chamar o ajustador; caso analítico Y=1,1+1,1X, com previsão 5,5 e EP=√0,525 em X=4; modelo múltiplo de ajuste perfeito; IDs após renomear/reordenar; alteração relevante versus coluna alheia; modelo/seleção corrompidos; seleção por planilha após reabrir; invalidação/desfazer; gráfico histórico com dados antigos; armazenamento repetido em planilha inativa e preservação após abertura inválida. A regressão de interface que antes exigia apagar o cache em todo refresh foi atualizada para exigir a restauração do modelo compatível.

O exemplo sintético `exemplo_modelo_regressao_salvo.statlab` permite abrir e prever sem ajustar. Nenhum material original da faculdade foi incluído.

O smoke test portátil foi ampliado para salvar/restaurar modelo, prever, reconstruir gráfico e reexecutar com armazenamento. Pacote 0.5.0 concluído: smoke test, CRC e SHA256 aprovados; evidência em `package-verification.json`. Não foi executado CI remoto nem teste em uma máquina Windows limpa.

Nenhuma fixture nova foi executada no Minitab 16, indisponível neste computador. Os testes analíticos e de persistência não substituem a comparação diferencial. Não houve publicação no GitHub nem alteração da instalação Minitab.

## Pendências

Resultados de previsão ainda são texto de sessão, sem registro independente de casos/modelo/intervalos no histórico estruturado. Outros métodos, modelos categóricos/sem intercepto/ponderados/especializados, editor geral de cenas, tarefas longas e recuperação continuam na fila. O histórico de desfazer permanece em memória por planilha. A auditoria integral de funções/opções e a validação na versão 16 seguem necessárias.
