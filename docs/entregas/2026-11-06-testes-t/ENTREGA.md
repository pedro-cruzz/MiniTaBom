# MiniTaBom 0.4.0 — histórico dos testes t

Continuação autorizada da entrega 0.3.0, seguindo a auditoria de 05/11/2026. A referência funcional continua sendo Minitab 16.2.4.0. Esta entrega integra capacidades existentes à plataforma; não declara equivalência numérica ou de opções com a referência.

## Mudanças

O serviço `analysis_service.py` agora atende aos sete formatos disponíveis no programa: uma amostra em coluna/resumo; pareado em colunas/resumo das diferenças; duas amostras em colunas/empilhadas/resumos. Cada execução persiste método, parâmetros efetivos, versão, origem, ausentes, tabelas, valores sem arredondamento e relatório. Os cálculos numéricos existentes foram reaproveitados.

`t_analysis_contract.py` define IDs e validação dos parâmetros por formato. `workspace_model.py` valida os novos registros antes de gravar/instalar um documento. O ID e o contrato anterior de uma amostra em coluna foram preservados; projetos/registros 0.3.0 sem fingerprint específico das entradas continuam abrindo e reexecutando. O formato do projeto permanece statlab v2.

As entradas resumidas preservam N/média/desvio e não dependem das células da folha. No pareado resumido, o resumo é o das diferenças; não se constroem pares artificiais. Para duas amostras, a suposição de variâncias iguais e a opção Welch GL inteiro/fracionário permanecem nos parâmetros.

Nas amostras empilhadas, a ordem dos dois grupos é estabelecida na primeira execução e persistida. A reexecução reutiliza essa ordem, mesmo após reordenar linhas. Trocar/desaparecer um grupo recusa a execução em vez de inverter silenciosamente a hipótese. O leitor compartilhado de amostras ganhou ordem explícita opcional; sem essa opção, os demais fluxos mantêm a primeira aparição como antes.

Novos registros incluem fingerprint apenas das colunas de entrada e dos seus valores/linhas, além da revisão/fingerprint geral já existente. Renomear ou editar outra coluna não acusa mudança dos valores de entrada. Alterar/remover uma coluna usada ou mudar a sequência das linhas é detectado. O fingerprint não é autenticação de arquivo; a validação da origem continua dependendo das evidências.

O armazenamento pareado é reexecutável. Os cálculos e a preparação da nova coluna são validados antes da alteração da tabela. Cada execução cria uma coluna nova, preservando as anteriores e registrando os IDs de destino. Quando a folha de origem está inativa, o armazenamento ocorre nela sem trocar a folha ativa. O histórico de desfazer daquela folha recebe a transformação.

`history.py` passa a guardar também IDs/metadados das colunas em snapshots paralelos aos estados já existentes. Desfazer/refazer restaura a identidade, de modo que uma análise de uma coluna gerada volta a encontrá-la após refazer. Os snapshots permanecem em memória e não são serializados como histórico de desfazer no projeto.

A tela Janela > Histórico de análises usa nomes legíveis e relatório em português; o contrato completo continua disponível na exportação JSON. Entradas resumidas são identificadas como resumo informado, separadas do indicador de dados alterados.

## Verificação e evidências

- **287 testes aprovados**, contra 273 na entrega anterior. Saída original em `unittest.log`; ambiente e comandos em `verification.json`.
- **19 exemplos válidos**. Novo `exemplo_historico_testes_t.statlab` contém os sete formatos para consulta/reexecução.
- Os testes novos verificam ida/volta e reexecução dos formatos, caso analítico t com dois GL, GL Welch racional/fracionário ou truncado, resumos independentes, ordem de grupos após reordenação, referências/grupos removidos, ausência de mutação parcial e contrato inválido.
- Integração verifica armazenamento em folha inativa, IDs após desfazer/refazer, análise de coluna gerada após restaurá-la, preservação de resultados e reabertura de resumo em folha vazia.
- `benchmark.json`: 20000 linhas × 10 colunas, seis snapshots com IDs/metadados; edições/sincronização/snapshot em cerca de 0,41–0,42 s, pico tracemalloc de 28,4 MB. A medição inclui overhead de instrumentação e não inclui grade/cálculo estatístico.
- O smoke test do executável foi ampliado para pareado com armazenamento, resumos, empilhadas e ordem persistida, além do projeto v2 já verificado. Executável 0.4.0, smoke test, CRC do ZIP e SHA256 aprovados; evidência em `package-verification.json`.

Nenhuma fixture nova executada no Minitab 16 foi adicionada. O executável dessa referência continua indisponível neste PC; não se substituiu a validação por resultados do 22. O novo teste analítico verifica o núcleo e a persistência, não todos os padrões do fabricante. Não houve execução de CI remoto ou verificação em Windows limpo.

## Registro e sequência

`CAPACIDADES.json` foi atualizado com persistência dos formatos t e identidade no undo/redo; o texto histórico da auditoria foi preservado em proveniência. Opções padrão do MiniTaBom foram separadas do que está documentalmente confirmado no 16. As exportações de cobertura foram regeneradas a partir da fonte única, sem porcentagem de funções.

Seguem pendentes: integrar as demais análises, modelos e cenas; recuperação, tarefas longas/cancelamento, tipos/metadados efetivos e demais opções de plataforma; depois completar fundamentos e famílias restantes conforme a auditoria. Não houve publicação no GitHub nem alteração de instalação Minitab. As alterações anteriores do usuário e da entrega 0.3.0 foram preservadas.
