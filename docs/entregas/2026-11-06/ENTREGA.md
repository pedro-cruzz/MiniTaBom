# MiniTaBom 0.3.0 — primeira entrega após a auditoria

O ZIP de 05/11/2026 foi lido como evidência e o `PROMPT_PARA_AGENTE.txt` foi seguido por solicitação do usuário. Não existe Markdown de prompt no pacote. O relatório, a matriz de 80 pacotes, o índice de código, os índices de ajuda e o catálogo documental foram inspecionados. Scripts do ZIP não foram executados. A referência descrita é o Minitab 16.2.4.0, English/1033; seu executável não está disponível neste computador. A instalação histórica do 22 não foi usada como prova de presença no 16.

## Registro atual e proveniência

`CAPACIDADES.json` é a fonte atual dos estados, IDs, arquivos, testes, prioridades e limitações. A tela Ajuda > Cobertura do projeto e `tools/build_minitab16_coverage.py` usam esse registro. O CSV e a fila JSON são visões geradas; não editar estados neles. Há 80 pacotes históricos e 16 requisitos iniciais decompostos, com naturezas explícitas; não são contagem de funções nem denominador de porcentagem. A decomposição integral continua pendente.

Foram preservados os IDs GAP da auditoria e os IDs/textos anteriores de M16 em uma ponte histórica. As descrições originais e as lacunas de origem permanecem em provenance; as limitações atuais dos pacotes alterados foram atualizadas. T resumido/empilhado, uma taxa Poisson, RJ/KS/gráfico, Levene/Bartlett de vários grupos, frequências acumuladas e armazenamento de regressão não são classificados como ausentes. A validação 16 e opções ainda faltantes permanecem abertas.

O índice de 13930 páginas e o catálogo de tópicos foram usados para localizar evidência documental, sem transformar cada tópico em função. O contrato inicial do t de uma amostra foi conferido na ajuda extraída: caminho Stat > Basic Statistics > 1-Sample t, colunas/resumo, hipótese opcional, confiança padrão 95 e alternativas. As páginas e seus hashes estão vinculados no registro. O exemplo de comando ONET é documental, não uma execução desta entrega. Edição, licença e opções acessíveis ainda precisam de confirmação em execução.

O bootstrap `tools/import_audit_registry.py` verifica os checksums internos e recusa sobrescrever registro existente. Recursos do 22 ficam em backlog histórico separado. A ajuda do fabricante permanece no ZIP/cache `.reference/`, ignorado pelo Git; não foi incorporada ao executável nem redistribuída como documentação própria.

## Projeto v2 e primeira integração vertical

- `workspace_model.py`: projeto e coleção de planilhas com IDs; colunas com ID, tipo, formato e metadados; revisão e fingerprint de identidade/nome/células; validação do documento antes de instalação/gravação.
- `project.py`: leitura de v1 e v2, migração explícita em memória, preservação da sessão e de todas as células; gravação v2 pelo aplicativo com arquivo temporário, fsync e substituição atômica. JSON com chaves duplicadas ou NaN/Infinity literais é recusado. Limite de leitura declarado de 256 MiB. O adaptador de escrita v1 permanece para ferramentas legadas.
- `analysis_service.py`: serviço sem Tk para t de uma amostra em coluna. Persiste ID de análise/método, parâmetros efetivos, versões, IDs da fonte, revisão/fingerprint, ausentes, valores sem arredondamento, tabela amostral, avisos, relatório e proveniência. Limites infinitos são etiquetas explícitas JSON, sem pickle/eval.
- `app.py`: Dados > Nova planilha e seletor acima da grade; undo/redo independente em memória por planilha. Salvar/reabrir conserva a coleção e os resultados estruturados. A inicialização permanece vazia.
- `analysis_history_dialog.py`: Janela > Histórico de análises mostra origem/revisão, resultado completo, exportação JSON e reexecução com dados atuais. Renomear/reordenar colunas preserva a identidade no contrato inicial. Ausência da coluna original recusa a reexecução. O resultado anterior é preservado e vinculado pela nova execução.

As demais análises continuam funcionando na sessão textual; seus parâmetros/modelos/cenas ainda não estão integrados ao novo contrato. Não foram inventados parâmetros para relatórios antigos migrados. A versão 0.2.0 não abre v2: Salvar como conserva o arquivo original v1. Criar/importar um projeto continua substituindo o projeto aberto, com a confirmação já existente; importar para outra folha é uma opção futura.

## Verificação

O baseline `baseline.json` registra commit, hashes de 83 fontes/testes/ferramentas, Python e hash do ZIP. Baseline observado: 257 testes OK e 17 exemplos válidos. O ambiente atual é Python 3.14.2 com dependências locais próprias; os binários Python 3.11 da máquina da auditoria não foram reutilizados.

Os testes novos verificam migração/round-trip v1→v2, IDs e metadados, múltiplas planilhas, reexecução após renomear/reordenar/editar, resultado anterior intacto, referência removida, limites infinitos, parâmetros inválidos, fingerprint incompatível, atomicidade e exportação. A integração percorre editar → analisar duas folhas → salvar → reabrir → reexecutar → exportar; undo/redo é conferido separadamente por folha. Resultado: 273 testes aprovados e 18 exemplos válidos. As saídas originais da regressão e versões efetivas ficam em `unittest.log`, `examples.log` e `verification.json`.

Nenhuma fixture executada no Minitab 16 foi adicionada. As fixtures históricas de Welch 22.6 e documentação Spearman mantêm sua origem. Os avisos Tcl/Tk ThemeChanged relatados na auditoria não foram reproduzidos no baseline desta máquina; não foi aplicada uma correção especulativa. Os testes Tk são ocultos e não constituem inspeção visual integral do produto.

`benchmark.json`: 20000 linhas × 10 colunas, seis snapshots contando o inicial; cinco edições/sincronizações/históricos em aproximadamente 0,38–0,42 s cada, pico tracemalloc de 28,4 MB. Não mede a grade nem garante desempenho para todos os tamanhos ou 50 snapshots. Os snapshots continuam completos; compressão/deltas e tarefas longas continuam pendentes.

O build Windows inclui o registro e verifica, no executável com PYTHONPATH/PYTHONHOME removidos, o projeto v2, duas planilhas, análise persistida, reexecução e abertura do histórico. A conclusão efetiva do empacotamento é registrada no `dist/smoke-test.json` e no manifesto local. Pacote local 0.3.0 concluído com smoke test, CRC e SHA256 aprovados; evidência em `package-verification.json`. Não foi executado CI remoto nem teste em Windows limpo.

## Limitações e próxima sequência

Esta entrega implementa o primeiro corte de plataforma solicitado. Ainda faltam tipos/conversões efetivas e editor de metadados, excluir/renomear folhas, vínculos entre folhas, recuperação, tarefas longas com cancelamento, modelos/cenas persistentes e propagação do contrato a todos os métodos. O histórico de desfazer é em memória, não é salvo entre sessões. O fingerprint permite rastrear alterações, não autentica a origem de um arquivo.

Prosseguir na plataforma e nos fundamentos já iniciados, com fixtures16 quando houver referência disponível; depois modelos, qualidade, DOE, confiabilidade e compatibilidade conforme o registro. Todas as famílias da auditoria continuam no escopo. Nenhuma área foi declarada equivalente ou concluída. Não houve push, publicação de Release nem alteração de instalação Minitab.
