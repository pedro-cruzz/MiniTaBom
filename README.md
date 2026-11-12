# MiniTaBom

Projeto independente para **fins educativos e estudo de estatística**, em português, com referência funcional pretendida no Minitab 16.2.4.0. Sem vínculo, patrocínio ou endosso da Minitab. A cobertura integral e a equivalência numérica com a versão 16 ainda estão em desenvolvimento.

## Abrir o programa

No computador em que o pacote foi gerado, dê dois cliques em **`MiniTaBom.bat`**, na raiz desta pasta, ou em **`Aplicativo/Abrir.bat`**. Os dois abrem a compilação mais recente. O `.exe` local fica em uma pasta de `Aplicativo/versoes/`, indicada em `Aplicativo/atual.json`.

Cada compilação usa uma pasta nova para permitir gerar uma atualização com o programa aberto. A sessão já aberta continua na sua versão; o atalho abre a nova. Projetos e arquivos pessoais são preservados.

**Para abrir um Excel:** Arquivo > Abrir Excel…, escolha o `.xlsx` e pronto. As abas aparecem no seletor acima da grade; não precisa informar células ou intervalo.

O programa inicia com a planilha e a sessão vazias. Para estudar com dados de demonstração, abra um projeto da pasta `Exemplos` pelo menu Arquivo.

Para outras pessoas, disponibilize **`dist/MiniTaBom-Windows-x64.zip`** nas [Releases do repositório](https://github.com/pedro-cruzz/MiniTaBom/releases). Quem baixar deve extrair a pasta inteira e abrir `MiniTaBom.exe`. Não é necessário instalar Python nem Minitab. Mantenha `_internal` junto do executável.

O download do código-fonte pelo GitHub não inclui o executável; ele é distribuído separadamente nas Releases.

## Organização

| Pasta ou arquivo | Conteúdo |
| --- | --- |
| `Aplicativo/` | Atalho **Abrir.bat**, seleção em `atual.json` e programa pronto em `versoes/`, com dependências, exemplos e licenças. Gerado localmente. |
| `src/` | Código-fonte do programa. |
| `tests/` | Testes automatizados e dados de referência em `fixtures/`. |
| `exemplos/` | Projetos sintéticos `.statlab` para estudar. |
| `docs/` | Manual, relatório de continuidade, inventário da instalação e diagnósticos. |
| `desenvolvimento/` | Scripts para instalar dependências ou gerar o executável; uso de desenvolvimento. |
| `tools/` | Ferramentas de empacotamento, inspeção e validação. |
| `dist/` | ZIP portátil, checksum e relatório do teste do executável. |
| `.github/workflows/` | Geração do pacote Windows pelo GitHub Actions. |
| `app_metadata.json` | Versão do aplicativo e repositório das atualizações. |
| `INVENTARIO_FUNCIONAL.json` | Cobertura funcional e pendências do Minitab 16. |

`Aplicativo/`, `dist/`, `.deps/`, `.build/` e `.build-tools/` são arquivos gerados ou dependências locais e ficam fora do Git. Salve seus projetos de estudo em uma pasta pessoal, separada do aplicativo.

## Atualizações

No programa, abra **Ajuda > Verificar atualizações…**. O repositório padrão já é `pedro-cruzz/MiniTaBom`. Clique em **Verificar** para consultar a última Release estável pública e em **Abrir página da versão** para baixar o pacote. A consulta não instala nem substitui arquivos automaticamente.

Versão atual: **0.10.0**. Para uma atualização local, aumente `version` em `app_metadata.json`, gere o ZIP e publique uma Release com a mesma tag, por exemplo `v0.10.0`. No GitHub Actions, a versão da tag e o repositório são incluídos automaticamente. Uma alteração no código ou uma tag sem Release não aparece como atualização nesse botão.

## Executar pelo código-fonte

Requer Python com Tkinter, pip e as dependências científicas do projeto. No Windows, execute `desenvolvimento/instalar_dependencias.bat` uma vez e depois:

```powershell
python src/app.py
```

Para verificar cálculos, interface e exemplos:

```powershell
python -B -m unittest -q
python -B tools/check_study_examples.py
```

## Gerar o executável

Execute **`desenvolvimento/gerar_executavel.bat`** no Windows x64 com Python x64. Ele instala as ferramentas de construção, gera o executável, faz a verificação local e prepara `Aplicativo/` e o ZIP em `dist/`.

No GitHub: **Actions > Pacote Windows > Run workflow**. Tags iniciadas em `v` também disparam a construção. O artefato da execução contém o ZIP; anexe esse ZIP às Releases para disponibilizá-lo aos usuários. O fluxo não publica Releases automaticamente.

## Recursos e documentação

Há planilha editável, importação CSV/Excel, calculadora de colunas, descritivas, percentis/decis, tabelas de frequência, testes t/Z, proporções, Levene/Bartlett, cinco métodos de normalidade, Mann–Whitney/Wilcoxon/Kruskal–Wallis, ANOVA com Tukey/Fisher LSD, correlação, regressão com armazenamento de resíduos e gráficos de probabilidade, barras, Pareto e setores. Consulte o [manual técnico](docs/MANUAL.md), o [relatório de continuidade](docs/ANALISE_E_CONTINUIDADE.md) e a [fila de cobertura do Minitab 16](docs/analise_instalacao/cobertura_minitab16.json) para opções, testes e limitações.


## Novidades 0.2.0: materiais da faculdade

A prioridade é cobrir os procedimentos da lista de exercícios e do PDF; depois completar funções e usabilidade do Minitab 16.2.4.0. Recursos exclusivos do 22 ficam para o futuro. A [avaliação dos materiais](docs/analise_estudo/ANALISE_DOS_MATERIAIS.md) registra a situação anterior e a validação dos novos fluxos.

- **Arquivo > Importar Excel**: escolha aba e intervalo, por exemplo `A4:B20`, confira a prévia e importe só aquele bloco. Primeira linha pode ser cabeçalho. O leitor aceita `.xlsx` com valores, texto e resultados de fórmulas salvos; não executa fórmulas, macros ou links. Datas numéricas permanecem seriais. Formatos, mesclagens e tipos avançados ainda não são reproduzidos.
- **Estat > Não paramétricos**: Mann–Whitney, Wilcoxon pareado e Kruskal–Wallis. Os dois primeiros oferecem alternativas unilaterais/bilateral e exato ou aproximação. A regra e as limitações são descritas no manual. Exatos com empates/zeros não são apresentados como se fossem a distribuição sem empates.
- **Estat > Estatísticas básicas > Igualdade de variâncias**: Levene centrado na mediana (Brown–Forsythe), Levene na média ou Bartlett, para dois ou mais grupos. O teste F de duas variâncias continua disponível separadamente.
- **Teste de normalidade**: Anderson–Darling, Ryan–Joiner, KS com normal estimada, Shapiro–Wilk ou D’Agostino–Pearson, com gráfico de probabilidade opcional. Os métodos têm limites de N e probabilidades aproximadas/limitadas explicitamente identificadas.
- **Teste t pareado**: marque Armazenar diferenças. **Regressão**: marque Armazenar ajustados, resíduos e diagnósticos. As novas colunas preservam as posições de linhas omitidas e entram no histórico de desfazer. Podem ser usadas diretamente em normalidade e gráficos.
- **Calc > Calculadora**: `C1-C2`, `(C1+C2)/2`, `sqrt(C1)` e outras operações permitidas, sem executar código arbitrário. Não é uma fórmula com recálculo permanente: execute de novo após mudar as fontes.
- **Estat > Tabelas > Tabela de frequências** e menus de gráficos: classes, frequências relativas/acumuladas, barras, Pareto e setores. O histograma agora abre configuração de classes. A regra do material usa precisão decimal e acrescenta classe se o passo for exato.
- **Descritivas**: desvio/variância populacionais. **Percentis e decis**: posições exclusivas, inclusivas ou extremos limitados. Boxplots distinguem pontos suaves e cruzes para extremos, sem remover observações automaticamente.
- **ANOVA**: Fisher LSD é uma opção individual sem ajuste; Tukey-Kramer permanece a opção simultânea. Games–Howell fica na alternativa sem variâncias iguais.
- **Correlação**: diagnóstico bivariado complementar de Mardia opcional para duas variáveis. É aproximação assintótica, com correção da assimetria para N<20; não é apresentado como uma função do Minitab 16 já validada.

Os fluxos foram exercitados nos nove conjuntos da sua lista, pela interface Tk oculta. As novas rotas computacionais estão disponíveis; a interpretação do delineamento, amostragem, escolha de hipótese e adequação aos dados continua sendo parte da resolução. A equivalência integral com os resultados e todas as opções do Minitab 16 ainda não foi estabelecida.

Exemplos adicionais: `exemplo_postos_variancias.statlab` e `exemplo_frequencias_graficos.statlab`, na pasta `exemplos/` ou em `Aplicativo/Exemplos/` no pacote gerado. São dados sintéticos, sem incluir os materiais originais da faculdade no executável.


## Novidades 0.3.0: projetos e histórico

- **Dados > Nova planilha** cria uma planilha no mesmo projeto. Alterne pelo seletor acima da grade; cada planilha mantém seu histórico de desfazer em memória.
- Salvar grava o formato **statlab v2**, com IDs de planilhas/colunas, revisão, fingerprint e metadados. Projetos v1 abrem sem alterar o original; ao salvar, são migrados para v2. A versão 0.2.0 não abre arquivos v2: use Salvar como para conservar o arquivo original v1.
- **Teste t de uma amostra em coluna** agora conserva parâmetros, valores sem arredondamento, ausentes, versões e origem. Em **Janela > Histórico de análises**, confira os detalhes, exporte JSON e reexecute com os dados atuais. O resultado anterior permanece no projeto; a tela sinaliza dados de origem alterados.
- O histórico estruturado começa por esse fluxo. Os demais métodos continuam na sessão textual; modelos de regressão, gráficos persistentes, tarefas longas e recuperação ainda precisam ser integrados.
- [CAPACIDADES.json](CAPACIDADES.json) é o registro atual com IDs estáveis. Ajuda > Cobertura do projeto e as exportações de cobertura usam esse registro. Os estados de implementação e validação no Minitab 16 são separados.

Veja a [entrega técnica de 06/11/2026](docs/entregas/2026-11-06/ENTREGA.md) e o exemplo `exemplo_projeto_v2.statlab`. A prioridade permanece nas funções e experiência do Minitab 16; a cobertura integral ainda não foi demonstrada.


## Novidades 0.4.0: histórico dos testes t

O histórico estruturado agora inclui t de uma amostra, pareado e de duas amostras, em todos os formatos disponíveis: colunas, dados resumidos e duas amostras empilhadas. Em **Janela > Histórico de análises**, selecione o resultado para consultar, exportar ou reexecutar. Os resultados anteriores permanecem no projeto.

- Nos dados resumidos, N/média/desvio ficam salvos; alterar as células não altera o resumo informado.
- Nas amostras empilhadas, a ordem original dos grupos fica salva. Reordenar linhas não inverte a diferença; substituir um grupo exige iniciar outra análise.
- O armazenamento das diferenças pareadas é preservado como opção: cada reexecução cria uma nova coluna na planilha de origem, inclusive quando outra planilha está ativa. As anteriores permanecem.
- Desfazer/refazer preserva IDs e metadados das colunas, mantendo os vínculos das análises. O histórico de desfazer continua em memória por planilha.
- Novos registros identificam alterações nas colunas de entrada; mudar uma coluna alheia ao teste não marca o resultado como desatualizado. Registros antigos 0.3.0 continuam abrindo.

Validação desta entrega: **287 testes e 19 exemplos**. Exemplo novo: `exemplo_historico_testes_t.statlab`. Consulte o [relatório 0.4.0](docs/entregas/2026-11-06-testes-t/ENTREGA.md). As demais análises/modelos/gráficos ainda precisam ser integrados ao histórico estruturado; a validação diferencial no Minitab 16 permanece pendente.


## Novidades 0.5.0: modelos de regressão salvos

A regressão linear numérica agora conserva o modelo completo no projeto: coeficientes, diagnósticos, parâmetros, variáveis por ID e estado necessário para previsão. Ao reabrir o projeto, **Estat > Regressão > Prever novos casos** volta a ficar disponível quando as variáveis de origem não mudaram. Não há novo ajuste automático.

Em **Janela > Histórico de análises**, selecione uma regressão:

- **Usar modelo** seleciona aquele ajuste e sua planilha para prever; a seleção é salva por planilha.
- **Ver gráficos** reconstrói ajuste/resíduos do resultado histórico, inclusive se os dados atuais já mudaram.
- **Reexecutar com dados atuais** ajusta novamente com os parâmetros salvos, preservando o resultado anterior. Se o armazenamento estava marcado, cria novas colunas de diagnósticos na origem.

Editar uma variável usada no ajuste desabilita a previsão até reexecutar; desfazer pode restaurar a compatibilidade. Editar uma coluna alheia, renomear ou reordenar colunas sem mudar seus valores não perde o vínculo. Modelos numéricos simples/múltiplos com intercepto são os suportados nesta entrega.

**298 testes e 20 exemplos aprovados.** Abra `exemplo_modelo_regressao_salvo.statlab` e preveja X=4: o resultado esperado é 5,5. Consulte a [entrega 0.5.0](docs/entregas/2026-11-09-regressao/ENTREGA.md). Resultados de previsão continuam na sessão textual; registros próprios de previsão, edição/persistência geral de cenas e os demais modelos permanecem pendentes.


## Novidades 0.6.0: previsões e ANOVA no histórico

**Previsões** agora salvam os casos, a confiança, o tipo de intervalo, os ausentes e o ajuste original utilizado. Em Janela > Histórico de análises:

- **Recalcular casos salvos** conserva os valores digitados e o modelo daquele resultado.
- **Recalcular colunas atuais** relê as colunas mapeadas por ID, conservando o mesmo modelo. Renomear/mover mantém o vínculo; remover a coluna recusa a reexecução.

Recalcular uma previsão histórica não refaz a regressão nem escolhe automaticamente um modelo mais recente. Os casos/modelos salvos podem ser recalculados mesmo se o conjunto de treinamento atual mudou. Para uma previsão nova pelo menu Regressão, continua sendo necessário um modelo compatível com os dados atuais. Intervalos unilaterais preservam seus limites infinitos no arquivo.

**ANOVA de um fator** agora salva parâmetros, resultados, comparações e o snapshot dos grupos. Os dois formatos (colunas e resposta/fator) permitem salvar/reabrir/reexecutar, com ordem de grupos preservada. Tukey–Kramer, Fisher LSD e Games–Howell conservam as opções existentes. Em **Ver gráficos**, o boxplot usa os valores da execução histórica, mesmo após editar a planilha.

Verificação: **314 testes e 22 exemplos**. Novos projetos sintéticos: `exemplo_previsoes_historico.statlab` e `exemplo_anova_historico.statlab`. Veja a [entrega 0.6.0](docs/entregas/2026-11-09-previsao-anova/ENTREGA.md). Paridade com o Minitab 16 e demais funções/opções permanecem em desenvolvimento.


## Novidades 0.7.0: diagnósticos e postos no histórico

O histórico agora preserva **normalidade**, **Mann–Whitney**, **Wilcoxon pareado**, **Kruskal–Wallis** e **igualdade de variâncias** (Levene mediana/média e Bartlett), nos formatos já disponíveis. Parâmetros, método efetivo, ausentes e resultados podem ser salvos, reabertos, exportados e reexecutados com os dados atuais.

- A normalidade conserva os cinco métodos existentes e seus limites de valor-p. Em **Ver gráficos**, o gráfico de probabilidade usa os valores daquela execução, mesmo após editar a planilha.
- Exato, aproximado e automático permanecem distintos. Opções de continuidade/zeros são preservadas; uma reexecução exata que passou a ter empates/zeros incompatíveis é recusada, sem substituir o resultado anterior.
- Em dados empilhados, a ordem dos grupos é preservada; mudar os grupos exige uma nova análise.
- O histórico libera os gráficos abertos após reexecutar. Salvar recusa projetos acima do limite de leitura de 256 MiB sem substituir o arquivo anterior.

Verificação: **328 testes e 23 exemplos**. Abra `exemplo_diagnosticos_historico.statlab` para praticar. Veja a [entrega 0.7.0](docs/entregas/2026-11-10-diagnosticos/ENTREGA.md). Os cálculos existentes foram integrados à persistência; a equivalência com o Minitab 16 e as demais funções continuam pendentes.


## Novidades 0.8.0: Excel direto e duas taxas de Poisson

**Arquivo > Abrir Excel…** abre as abas automaticamente. Mantém as posições das células a partir de A1, títulos, linhas vazias e a primeira linha, usando colunas A/B/C. A aba ativa do arquivo é respeitada quando possível; abas vazias/ocultas também são mantidas. A abertura não altera o `.xlsx` original. A importação específica por intervalo permanece apenas como API legada.

Para uma tabela em que a primeira linha contém os nomes, há uma ação opcional: **Dados > Usar primeira linha como nomes das colunas**. Ela aceita nomes únicos/não vazios e pode ser desfeita com Ctrl+Z. Não é necessário usá-la para abrir o arquivo.

Fórmulas usam resultados salvos no Excel; quando não há resultado, aparecem como texto, sem cálculo. A grade não reproduz estilos/mesclagens. Limites: 100 abas, até 200000 linhas/512 colunas por área e 2000000 células no conjunto de abas.

**Estat > Estatísticas básicas > Duas taxas de Poisson…** compara taxas por exposição ou médias por observação. Aceita duas colunas, resposta/grupo e resumos; exposições diferentes; hipóteses unilateral/bilateral; Z separado/combinado e exato condicional para diferença zero. O IC usa aproximação normal com estimativas separadas, inclusive quando há teste exato. As opções e resultados ficam no histórico. Frequências opcionais do Minitab e demais opções continuam pendentes.

Verificação: **342 testes e 24 exemplos**, incluindo o novo `exemplo_duas_taxas_poisson.statlab`. O exemplo da ajuda 16 foi conferido somente na precisão dos números publicados, sem execução no programa original. Veja a [entrega 0.8.0](docs/entregas/2026-11-10-excel-poisson/ENTREGA.md).

## Novidades 0.9.0: dados aleatórios com semente

Abra **Calc > Dados aleatórios…**, escolha a distribuição, os parâmetros e quantas linhas/colunas gerar. Os dados entram em novas colunas da planilha ativa, com Ctrl+Z/Ctrl+Y para desfazer/refazer. Dados existentes são preservados; nomes repetidos ganham sufixos.

São 14 distribuições: normal, t, qui-quadrado, F, binomial, Poisson, exponencial, uniforme, Weibull, lognormal, gama, beta, Bernoulli e inteiros com limites inclusivos. A semente é opcional: se ficar vazia, o programa cria uma e registra na sessão.

O projeto salva parâmetros, semente, versões do gerador e os valores originais. No **Histórico de análises**, **Reproduzir valores salvos** acrescenta uma cópia exata dos dados, mesmo depois de reabrir o projeto. A semente é aplicada por operação; não reproduz o estado global nem as sequências do Minitab 16. Novos sorteios podem mudar com versões do NumPy/SciPy; a reprodução pelo histórico usa o snapshot salvo.

Verificação: **363 testes e 25 exemplos válidos**, além do teste do executável instalado. Exemplo sintético: `exemplo_dados_aleatorios.statlab`. Detalhes, validação e limites na [entrega 0.9.0](docs/entregas/2026-11-10-aleatorios/ENTREGA.md).

## Novidades 0.10.0: progresso e cancelamento

**Arquivo > Abrir Excel…** e **Calc > Dados aleatórios… > Gerar** agora exibem uma janela de progresso. Use **Cancelar**, **Esc** ou o **X dessa janela** para interromper a operação e manter os dados atuais. O Excel continua abrindo normalmente, sem seleção de células.

Enquanto a tarefa roda, os menus e a edição ficam bloqueados; a janela de progresso continua respondendo. Os dados são preparados separadamente e aplicados ao concluir. Se o projeto mudar durante a preparação, o programa descarta o resultado antigo para preservar as alterações atuais. A geração concluída continua com Ctrl+Z/Ctrl+Y e histórico persistente.

Cancelar pode levar alguns instantes até a etapa em curso terminar. A aplicação final dos dados e os demais procedimentos ainda são síncronos. Esta entrega inicia o serviço comum de tarefas, com migração das outras rotas ainda pendente.

Verificação: **386 testes e 25 exemplos válidos**, com executável instalado e ZIP aprovados. Detalhes, medições e limites na [entrega 0.10.0](docs/entregas/2026-11-10-tarefas/ENTREGA.md).
