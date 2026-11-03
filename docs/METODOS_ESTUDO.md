# Métodos para os materiais de estudo — 0.2.0

Os procedimentos abaixo foram implementados para os materiais da faculdade. Os nove conjuntos do Excel foram importados e percorridos em testes da interface Tk oculta. Isso verifica execução, seleção de dados e armazenamento; não estabelece equivalência integral com o Minitab 16 nem substitui a interpretação dos exercícios.

## Normalidade e gráficos

Anderson–Darling usa parâmetros normais estimados e ajuste de tamanho amostral. Ryan–Joiner usa correlação com escores normais de Blom, postos médios em empates e críticos aproximados para 4 a 1000 observações; exige pelo menos três valores distintos. Probabilidades fora da faixa tabelada são reportadas como limites abaixo de 0,01 ou acima de 0,10.

Os coeficientes Ryan–Joiner foram conferidos com a tabela dos autores: a expressão de amostras pequenas é aplicada até N=50 e a outra acima de 50. A página atual do suporte Minitab associa os rótulos de tamanho aos dois conjuntos de coeficientes de forma inversa à tabela de Ryan (1990). A implementação segue a tabela dos autores; isso está registrado também no código e em testes dos críticos. Essa divergência exige comparação futura com saídas reais da versão 16.

KS usa normal com média e desvio estimados, estatística D ajustada por tamanho e probabilidades interpoladas, limitadas por 0,01 e 0,15; não é o teste KS com parâmetros conhecidos. Shapiro–Wilk aceita N de 3 a 5000; D’Agostino–Pearson, de 8 a 200000, com ressalva para amostras pequenas. Um valor-p alto não prova normalidade.

O gráfico de probabilidade normal usa observações ordenadas e posições de Blom, escala percentual normal e reta pela média/desvio. Exibe até 3000 pontos; os testes usam todos os dados válidos. Bandas de confiança e todas as opções gráficas do Minitab ainda estão pendentes.

## Postos e variâncias

Mann–Whitney: teste exato somente sem empates; escolha automática para amostra menor até oito, conforme SciPy. Exato solicitado aceita tamanho menor até 20 e produto dos tamanhos até 10000. A aproximação usa ajuste de empates e correção de continuidade opcional. O teste compara distribuições; interpretar como diferença de medianas requer hipóteses adicionais de forma.

Wilcoxon pareado: exclusão por par, diferenças decimais para evitar empates falsos de ponto flutuante. Exato automático até 25 pares, explícito até 50, sem zeros nem empates nas diferenças absolutas. Na aproximação, zeros podem seguir Wilcox, Pratt ou divisão de postos. Todas as diferenças zero produzem p=1 na escolha automática; exato sem zeros não é aplicado nesse caso.

Kruskal–Wallis: aproximação qui-quadrado com correção de empates; dados todos iguais são recusados. O teste global não identifica sozinho quais grupos diferem. Grupos com menos de cinco observações geram ressalva.

Igualdade de variâncias: Levene na mediana (Brown–Forsythe), Levene na média ou Bartlett. Bartlett pressupõe normalidade; dispersões nulas não são aceitas por esse método. Nenhum resultado provoca remoção automática de observações.

## Descritivas, frequências e comparações

Desvio/variância populacionais usam divisor N; medidas amostrais usam N−1. Percentis oferecem posição exclusiva (N+1)p, inclusiva 1+(N−1)p, ou exclusiva com extremos limitados. Na exclusiva, posições fora das observações são indisponíveis. A escolha deve acompanhar a convenção do exercício.

A regra de classes do PDF usa precisão decimal, amplitude e largura arredondada para cima; acrescenta uma classe quando o passo é exato. A tabela oferece frequência absoluta, relativa, percentual e acumuladas, com contagem opcional inteira. Limites operacionais: 200 categorias/classes e total de contagens até 2^53−1; gráficos até 50 grupos. Pareto ordena frequências e acumula percentuais.

Boxplots distinguem pontos além de 1,5 IQR e extremos além de 3 IQR. Tukey–Kramer tem comparações simultâneas; Fisher LSD usa erro residual combinado, valores-p sem ajuste e intervalos individuais. Games–Howell permanece na alternativa sem variâncias iguais.

Mardia é diagnóstico bivariado complementar para exatamente duas variáveis, com exclusão por linha completa e correção da assimetria para N<20. Usa covariância com divisor N e aproximações assintóticas; covariância singular é recusada. Não é uma declaração de paridade de um comando do Minitab 16.

## Planilha e armazenamento

Importação Excel lê `.xlsx`, permitindo aba, intervalo e cabeçalho. Não executa fórmulas, macros ou links; usa resultados de fórmulas já salvos e recusa fórmulas sem resultado em cache no intervalo escolhido. Datas permanecem seriais numéricos. Formatação e mesclagens não são reproduzidas. Limites: 64 MB por entrada ZIP, 256 MB descompactados, 10000 entradas, 200000 linhas, 512 colunas e dois milhões de células no intervalo.

A calculadora aceita aritmética, identificadores C1/C2 e abs, sqrt, log, log10, exp e round. Não usa eval. Valores ausentes se propagam; erros abortam a operação inteira. Máximo de 100 nós de expressão e expoentes absolutos até 1000. A coluna é resultado armazenado, sem recálculo permanente.

Diferenças pareadas, ajustados, resíduos, resíduos padronizados, alavancagem e distância de Cook preservam a posição das linhas excluídas. Inserções entram no histórico de desfazer e usam nomes de coluna disponíveis. O relatório identifica a origem e a regra de exclusão.

## Referências e limites de validação

- [Minitab: métodos de normalidade](https://support.minitab.com/en-us/minitab/help-and-how-to/statistics/basic-statistics/how-to/normality-test/methods-and-formulas/methods-and-formulas/).
- [Ryan e Joiner: relatório e nota de críticos, hospedados pela ADDITIVE](https://www.additive-net.de/en/component/jdownloads/send/70-support/236-normal-probability-plots-and-tests-for-normality-thomas-a-ryan-jr-bryan-l-joiner).
- Documentação oficial SciPy: [Mann–Whitney](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.mannwhitneyu.html), [Wilcoxon](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.wilcoxon.html), [Kruskal–Wallis](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.kruskal.html) e [Levene](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.levene.html).
- [Minitab: comparações de ANOVA](https://support.minitab.com/en-us/minitab/help-and-how-to/statistical-modeling/anova/how-to/one-way-anova/methods-and-formulas/multiple-comparisons/).
- [Artigo MVN, R Journal 2014: Mardia e correção de amostras pequenas](https://journal.r-project.org/articles/RJ-2014-031/index.html).

As páginas atuais do suporte fundamentam métodos, sem comprovar todos os padrões históricos da versão 16. Os testes usam casos analíticos e invariâncias, além dos materiais originais somente para leitura. Faltam comparações diferenciais abrangentes no Minitab 16 e avaliação visual integral da interface nativa.
