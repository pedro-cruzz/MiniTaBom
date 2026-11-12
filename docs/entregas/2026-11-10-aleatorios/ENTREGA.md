# MiniTaBom 0.9.0 — geração aleatória e semente

A continuação autorizada avançou na geração de dados dos fundamentos da versão 16. O alvo permanece Minitab 16.2.4.0; o pacote de trabalho GAP-017 continua parcial, com requisitos atômicos separados para geração em colunas, semente por operação e reprodução histórica.

## Usar

**Calc > Dados aleatórios…** aceita distribuição, parâmetros, linhas por coluna, quantidade de colunas, nome e semente opcional. São as 12 famílias do calculador existente (normal, t, qui-quadrado, F, binomial, Poisson, exponencial, uniforme, Weibull, lognormal, gama, beta), mais Bernoulli e inteiros inclusivos. Defaults próprios do aplicativo: normal com média 0/desvio 1, 100 linhas, uma coluna e nome Aleatorio. Defaults do diálogo 16 não foram validados.

A semente vazia cria um inteiro de 128 bits e o registra. Uma semente explícita entre 0 e 2¹²⁸−1 é lida como inteiro, sem perda por conversão float. Cada operação recebe um gerador PCG64 próprio, sem alterar o gerador global NumPy. A matriz é sorteada na ordem coluna, depois linha. O SciPy aceita esse gerador explícito em [rvs](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.rv_continuous.rvs.html). Inteiros/Bernoulli usam os métodos correspondentes do gerador.

Os resultados acrescentam colunas com nomes únicos, sem sobrescrever dados. A tabela cresce ou recebe vazios de preenchimento conforme a quantidade de linhas. Ctrl+Z/Ctrl+Y desfaz/refaz a transformação em uma etapa, preservando os IDs das colunas. Parâmetros inválidos, falta de capacidade e resultados não finitos são recusados antes da instalação das colunas.

## Persistência e reprodução

O registro guarda parâmetros efetivos, semente, todas as observações sem arredondamento, versões Python/NumPy/SciPy/aplicativo, motor e ordem de geração. A saída de célula usa representação decimal que permite recuperar o valor float original. O projeto `.statlab` e a exportação JSON incluem esse snapshot.

**Histórico de análises > Reproduzir valores salvos** acrescenta os valores arquivados, sem chamar o sampler. Cria registro novo ligado ao anterior, mantém a proveniência original e preserva o resultado antigo. Funciona na planilha original mesmo quando outra está ativa, com histórico de desfazer independente. Editar/desfazer as colunas não torna o snapshot histórico inválido.

A reprodução pelo snapshot evita depender da estabilidade futura do sampler. Novos sorteios com os mesmos parâmetros/semente são reproduzíveis nas versões verificadas; o [Generator do NumPy](https://numpy.org/doc/stable/reference/random/generator) não garante compatibilidade irrestrita entre versões. A sequência não foi comparada nem declarada idêntica à do Minitab 16.

## Referência 16 e limites

Os tópicos Normal Random, Bernoulli Random, Integer Random e Set Base da ajuda histórica confirmam documentalmente geração em colunas, suporte e finalidade da semente. Seus localizadores e hashes estão em `reference-metadata.json`. O texto da ajuda não é distribuído no pacote.

O executável 16 não existe no caminho de referência desta máquina; **executed_reference=false**, nenhuma fixture executada 16 adicionada. A ajuda descreve estado global que avança entre operações. Esta entrega oferece semente independente por operação; estado global Set Base, amostragem de colunas, matrizes, demais famílias e comparação diferencial seguem pendentes.

A tabela resultante aceita até 200000 linhas, 512 colunas e 2000000 células, incluindo as existentes. O projeto mantém o limite de 256 MiB; histórico e células duplicam parte dos dados. Execução síncrona, sem progresso/cancelamento. Esses limites não são garantia de responsividade no tamanho máximo.

## Verificação

17 testes novos cobrem as 14 famílias, repetição de semente, limites inclusivos, casos degenerados exatos, semente de 128 bits, criação de semente, independência do estado global, validação antes de sorteio, capacidade incluindo dados existentes, erro não finito sem alteração, nomes/preenchimento, round-trip e replay sem sampler, rejeição de histórico corrompido sem substituir arquivo/sessão, diálogo decimal, navegador/menu, exportação JSON, undo/redo com IDs e reprodução em aba inativa.

O exemplo sintético `exemplo_dados_aleatorios.statlab` tem 30 ensaios e quatro registros de geração: duas normais, Poisson, inteiros e Bernoulli. O verificador dos exemplos compara o snapshot com as células e com a reprodução. Nenhum material original da faculdade foi incluído.

Medição local com bibliotecas aquecidas, Tk oculto e tracemalloc: 10000 linhas, três colunas novas e 60000 células totais; geração 0,310 s, undo 0,006 s e redo 0,162 s, pico Python rastreado de 7,61 MiB. Escopo e valores completos em `performance.json`; não mede toda a memória nativa nem extrapola para o limite máximo.

**363 testes aprovados e 25 exemplos válidos.** Logs em `unittest.log` e `examples.log`; ambiente e comandos em `verification.json` (Python 3.14.2, NumPy 2.5.4, SciPy 1.18.1). O smoke test portátil foi ampliado para diálogo, semente, geração, persistência, reprodução exata, inteiros e undo/redo.

O executável 0.9.0 instalado passou nos 14 grupos de checagens do smoke test com PYTHONPATH/PYTHONHOME removidos. CRC e SHA256 do ZIP aprovados; 25 exemplos e registro de 111 requisitos conferidos dentro do arquivo. Evidências em `installed-smoke.json` e `package-verification.json`. ZIP de 85387904 bytes, SHA256 `8ae8a3df0b11453b1dc3bcdb6b2a68e1e3e7d74e97ac22786880b65d488aab30`. Sem CI remoto, Windows limpo, push ou publicação de Release nesta entrega.

## Código e continuidade

O teste do executável congelado passou, mas a cópia sobre `Aplicativo/` encontrou WinError 32: a versão 0.8.0 estava aberta. Os arquivos que a tentativa havia substituído foram restaurados a partir do bundle 0.8.0, somente quando o hash correspondia à cópia feita nesta entrega. A sessão aberta foi preservada.

O empacotador agora instala cada compilação em `Aplicativo/versoes/<versao>-<compilacao>/`, sem sobrescrever arquivos da versão aberta. Depois da cópia completa, ativa `Aplicativo/Abrir.bat` para a versão nova; `MiniTaBom.bat` da raiz chama esse atalho. `Aplicativo/atual.json` registra o caminho. O ZIP para outras pessoas mantém `MiniTaBom/MiniTaBom.exe` e suas dependências juntos.

Quatro testes adicionais do empacotador cobrem preservação do executável antigo/arquivos pessoais, falha de cópia sem mudar o atalho, recusa de destino reutilizado ou fora da pasta e recusa de bundle sem aprovação congelada.

- `random_contract.py`: esquemas, suporte, capacidades e validação de histórico.
- `random_service.py`: sorteio com gerador local, formatação, armazenamento e reprodução de snapshot.
- `random_dialog.py`, `app.py`, `analysis_history_dialog.py`: acesso pela interface, undo/redo e histórico.
- `distributions.py`: validação de parâmetros compartilhada sem carregar o sampler.
- `workspace_model.py`, `analysis_service.py`: validação de projeto e roteamento da reprodução.
- `CAPACIDADES.json`: fonte canônica com 111 registros (80 pacotes e 31 requisitos atômicos); visões derivadas atualizadas. Contagem de registros não indica percentual de funções.

Permanecem no escopo as opções restantes dos fundamentos, tarefas longas/cancelamento, recuperação, operações de dados, persistência dos demais métodos e famílias avançadas da auditoria. A prioridade continua sendo a versão 16.
