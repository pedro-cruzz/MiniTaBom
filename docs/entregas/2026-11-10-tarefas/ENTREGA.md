# MiniTaBom 0.10.0 — tarefas, progresso e cancelamento

A continuação avançou no pacote P0 GAP-004 da auditoria: um serviço comum de execução com progresso e cancelamento, integrado verticalmente à abertura automática de Excel e à geração aleatória. O alvo permanece Minitab 16.2.4.0. O pacote continua parcial, pois os demais procedimentos ainda não foram migrados.

## Comportamento disponível

**Arquivo > Abrir Excel…** pede somente o `.xlsx`, mantém a abertura automática das abas e exibe progresso durante leitura e preparação do projeto. **Calc > Dados aleatórios… > Gerar** prepara o sorteio e a nova tabela em segundo plano. Os menus e a edição ficam temporariamente bloqueados; a janela de progresso continua recebendo eventos.

**Cancelar**, **Esc** e o **X da janela de progresso** solicitam interrupção. Cancelamento ou erro descartam a preparação sem incluir colunas, análises ou estados no histórico de desfazer, e sem substituir o projeto aberto. Um resultado pronto ainda pode ser descartado antes de a interface o recolher. Conclusão bem-sucedida mantém o armazenamento, Ctrl+Z/Ctrl+Y e persistência existentes.

Antes da aplicação, a geração confere a identidade e a revisão da planilha original. O Excel confere o estado do projeto, incluindo planilhas, análises, sessão e metadados. Uma origem alterada impede aplicar uma preparação antiga. A confirmação de salvar o projeto atual permanece no final da abertura do Excel, antes da substituição. Cancelar a confirmação mantém o projeto anterior.

Pedir o fechamento do programa solicita cancelamento primeiro e mantém o fluxo existente de salvar alterações. Destruição direta da janela remove o polling e descarta a entrega pendente. Nenhuma tarefa escreve arquivos do usuário ou altera a planilha dentro da thread de trabalho.

## Arquitetura e limites

`background_tasks.py` fornece contexto de cancelamento por Event, fases de progresso, uma thread por tarefa e entrega consumível uma vez. O progresso usa um único slot atualizado, sem uma fila que cresça com a quantidade de células. Uma tarefa por janela é aceita; pedidos sobrepostos são recusados.

`task_dialog.py` consulta o estado por `after`, aplica callbacks somente na thread Tk, restaura menus e a janela modal anterior e cancela callbacks ao destruir. Trabalho longo fora dos handlers segue o [modelo de eventos do Tkinter](https://docs.python.org/3.14/library/tkinter.html#threading-model). O cancelamento por sinalização utiliza [Event do Python](https://docs.python.org/3.14/library/threading.html#event-objects).

O gerador usa blocos de até 4096 valores por coluna, preservando a ordem coluna/linha e registrando o tamanho do bloco na proveniência. A leitura XML do Excel recebe pontos de interrupção a cada bloco de 64 KiB; interpretação de células/textos, montagem das linhas e preparação do projeto têm checkpoints adicionais. Arquivos abertos pelo leitor são liberados ao cancelar.

O cancelamento é cooperativo: a chamada nativa em curso, uma importação de biblioteca ou uma validação precisam retornar antes do próximo checkpoint. Não há interrupção forçada de threads. A preparação usa snapshots; a aplicação final no modelo/Tk permanece síncrona e não aceita cancelamento parcial. O diálogo de salvamento já existente também é síncrono.

Demais análises, reexecução histórica, salvar/exportar e a API direta continuam síncronos. Não há fila persistente, retomada após fechar, várias tarefas simultâneas nem migração universal de métodos nesta entrega. Os limites de leitura/tabela e o limite de projeto de 256 MiB continuam os mesmos.

## Verificação

**386 testes aprovados e 25 exemplos válidos.** Logs e ambiente em `unittest.log`, `examples.log` e `verification.json`: Python 3.14.2, NumPy 2.5.4 e SciPy 1.18.1. Não houve avisos Tcl/Tk na regressão registrada.

Os 23 testes novos cobrem:

- Trabalho fora da thread chamadora, entrega única e progresso coalescido; cancelamento durante a execução e após a preparação, antes da entrega; erros sem exceção solta na thread.
- Interrupção da leitura/montagem de Excel, liberação do arquivo e reabertura; cancelamento entre blocos de sorteio sem alterar a planilha.
- Pulso Tk e aplicação na thread principal; menu Excel efetivamente usando o worker; bloqueio de pedidos sobrepostos; restauração de menus e grab anterior ao falhar a criação da thread.
- Cancelamento sem alterar dados/histórico; planilha ou metadados alterados impedindo sobrescrita; geração na planilha original inativa; erro de leitura e confirmação de substituição recusada preservando o projeto.
- Fechamento/cancelamento, remoção do polling e integração Excel → geração → teste t → undo/redo → salvar/reabrir → exportar JSON.

Uma regressão compara os sorteios em blocos com a chamada matricial usada na 0.9.0: as 14 famílias, parâmetros padrão, semente 2718 e duas colunas de 4097 linhas produziram valores exatamente iguais neste backend. Isso não é uma garantia geral entre versões/parametrizações, nem uma comparação com Minitab 16. Projetos antigos continuam válidos; a reprodução histórica usa seus valores salvos.

O smoke test portátil foi ampliado para Excel em tarefa, geração em tarefa e cancelamento sem alteração. O bundle e a cópia instalada 0.10.0 passaram nos 15 grupos de checagens, com PYTHONPATH/PYTHONHOME removidos. Evidências em `installed-smoke.json` e `package-verification.json`.

CRC e SHA256 do ZIP aprovados; versão, 114 entradas do registro e 25 exemplos conferidos dentro do pacote. ZIP com 85407109 bytes, SHA256 `4449c4ced4eaae613f16c4066584bb8722013d859ab228b1990196bff9bc78d1`. Material de ajuda da referência não foi incluído.

O atalho `MiniTaBom.bat` aponta para a compilação instalada nova. Os executáveis 0.8.0 e 0.9.0 foram conferidos como preservados; a sessão aberta não foi encerrada. Não houve push, publicação de Release, CI remoto ou teste em Windows limpo nesta entrega.

## Medições locais

`tools/benchmark_background_tasks.py` usa somente dados sintéticos, Tk oculto, bibliotecas aquecidas e tracemalloc. Inclui a aplicação final no tempo total e nos intervalos do pulso Tk. Valores completos em `performance.json`.

| Operação | Entrada | Tempo total | Pulsos Tk | Maior intervalo do pulso | Pico Python rastreado |
| --- | --- | --- | --- | --- | --- |
| Gerar normal | 10000 linhas × 3 colunas novas | 0,457 s | 6 | 234 ms | 7,78 MiB |
| Cancelar geração | 100000 linhas × 4 colunas; pedido 20 ms após iniciar | 0,192 s desde a chamada | 3 | 150 ms | 2,30 MiB |
| Abrir Excel | 2 abas × 10000 linhas × 3 colunas | 2,126 s | 37 | 177 ms | 27,94 MiB |

O cancelamento preservou o documento integral. Esses resultados incluem overhead da instrumentação e não medem toda a memória nativa; não demonstram responsividade nos tamanhos máximos nem equivalência de desempenho ao Minitab.

## Evidência 16 e continuidade

A ajuda histórica documenta Ctrl+Break para interromper saída e macros, com término do comando corrente na macro. Localizadores e hashes dos dois tópicos estão em `reference-metadata.json`. Essa evidência não valida a implementação dos novos diálogos, seus padrões ou seu cancelamento; não foram criados comandos/macros compatíveis nesta entrega.

O executável 16 continua ausente no caminho de referência. **executed_reference=false; nenhuma fixture executada 16 nova.** A validação diferencial permanece pendente, sem substituir resultados do 16 por números inventados ou por resultados do 22.

O registro canônico tem 114 entradas (80 pacotes e 34 requisitos atômicos), com implementação/UI/persistência separadas de validação 16. O estado antigo do pacote de distribuição foi reconciliado com os builds/smoke tests locais, mantendo pendentes Windows limpo, CI remoto e lockfile completo. Contagens não representam percentual de funções.

Próximos requisitos continuam incluindo migração dos demais métodos para tarefas, progresso/cancelamento da aplicação quando viável, recuperação de projeto, operações de dados e demais famílias da auditoria. A prioridade continua sendo a versão 16.
