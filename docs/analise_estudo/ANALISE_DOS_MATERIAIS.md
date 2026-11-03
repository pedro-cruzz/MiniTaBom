# MiniTaBom: cobertura dos materiais de estudo

Data: 03/11/2026. Aplicativo avaliado: MiniTaBom 0.1.0, código atual em `src/`.

## Atualização: MiniTaBom 0.2.0

Os procedimentos computacionais identificados como faltantes na avaliação inicial abaixo foram acrescentados: Mann–Whitney, Wilcoxon, Kruskal–Wallis, Levene/Bartlett com vários grupos, Ryan–Joiner/KS/Shapiro–Wilk/D’Agostino–Pearson e gráfico de probabilidade, calculadora de colunas, armazenamento das diferenças/resíduos, frequências configuráveis, Pareto/setores/barras, percentis/decis, dispersão populacional e distinção de outliers extremos. Fisher LSD e um diagnóstico bivariado complementar de Mardia também estão acessíveis.

**Verificação com a lista original:** os nove blocos foram importados diretamente do Excel e processados pelos métodos novos e existentes na interface Tk oculta. A conferência inclui todos os cinco métodos de normalidade, Mann–Whitney/Student/Welch nos independentes, Wilcoxon e diferenças armazenadas nos pareados, Levene/Bartlett/Kruskal/Tukey/LSD nos três cenários ANOVA, correlação com diagnóstico bivariado e regressão com resíduos armazenados. Resultado: nove fluxos aprovados em `verificacao_novos_fluxos.json`.

É possível estudar os procedimentos da lista com a versão 0.2.0, mantendo a decisão de método/pressupostos e a interpretação como parte do exercício. Isso não significa que todas as opções, intervalos robustos, valores padrão, aspectos visuais e casos extremos do Minitab 16 foram reproduzidos. O leitor Excel importa valores e caches de fórmulas; não reproduz a formatação nem calcula fórmulas do arquivo. Alguns exatos têm limites e não aceitam empates/zeros; nesses casos há aproximação explicitamente selecionada. O relatório inicial a seguir fica preservado como histórico de onde vieram as prioridades.

## Avaliação inicial (0.1.0)

**O MiniTaBom atual permite calcular os testes principais da lista, mas ainda não resolve integralmente todos os procedimentos e alternativas descritos nos materiais.** Ele já serve para estudar testes t, ANOVA/Tukey, correlação e regressão. As lacunas mais importantes para esta lista são alternativas não paramétricas, Ryan–Joiner, gráfico de probabilidade na normalidade, igualdade de variâncias para mais de dois grupos e preparação automática de diferenças/resíduos.

Conseguir produzir um valor-p não basta para concluir que o procedimento é adequado aos dados. A avaliação abaixo distingue o cálculo disponível da análise dos pré-requisitos. Não foi calculado um percentual de cobertura.

## Material e verificação

- Excel: `C:/Users/pedro/Downloads/exercícios sistemas 2b.xlsx`, aba `Plan1`, A1:O96. Uma aba, 5 comandos numerados e 9 conjuntos de dados; as questões 1 e 2 usam os mesmos dois conjuntos.
- PDF: `C:/Users/pedro/Downloads/material de estatística 1 (1).pdf`, 22 páginas. Texto extraído das 22 páginas e conferência visual das páginas, incluindo figuras e exemplos.
- Os dois arquivos originais foram usados somente para leitura. As instruções de exercícios foram tratadas como conteúdo a avaliar, sem alterar os materiais ou implementar novos testes no aplicativo.
- Os dados originais de cada conjunto foram executados com as funções atuais do MiniTaBom. O resultado detalhado está em `resultados_nucleo.json`; a extração registra as células de origem. Isso é teste do núcleo com os dados da lista, não comparação diferencial com uma execução do Minitab 16.
- Para os diagnósticos numéricos abaixo, adotou-se α=0,05, confiança de 95%, hipóteses bilaterais e dados originais, sem exclusão de observações. Normalidade: Anderson–Darling com valor-p aproximado, o método atualmente acessível no programa.

## Lista do Excel, conjunto por conjunto

| Exercício e dados | Origem em Plan1 | N | O que já pode ser feito | Limite para concluir tudo |
| --- | --- | --- | --- | --- |
| 1/2a — Tempo | A4:B20 | 16 e 15 | Boxplots, AD em cada grupo, F de duas variâncias, t combinado e Welch | G2 tem 80 como outlier extremo e AD p≈0,000195. F p≈0,003112 também indica diferença de variâncias sob a hipótese de normalidade. O F é sensível à não normalidade. Se for necessária a alternativa do PDF, Mann–Whitney ainda falta. |
| 1/2b — Produtividade | D4:E19 | 15 e 15 | Os mesmos procedimentos de 1/2a | G2 tem AD p≈0,025325 e dois pontos além de 1,5 IQR: 128 e 165. F p≈0,961965 não resolve a questão da normalidade. Falta a rota de Mann–Whitney e, para reproduzir outra escolha do professor, Ryan–Joiner. |
| 3a — Custo antes/depois | A23:B42 | 19 pares | Boxplots, normalidade das duas colunas e teste t pareado | O cálculo principal está disponível. Para avaliar a distribuição das diferenças e seus outliers, é preciso preparar uma coluna Antes−Depois fora do cálculo automático: ainda não há calculadora de colunas ou armazenamento das diferenças. AD das diferenças≈0,601351. |
| 3b — Colesterol antes/depois | D23:E35 | 12 pares | Os mesmos procedimentos de 3a | AD das diferenças≈0,132795. Exige o mesmo preparo de diferenças. Se o professor exigir Ryan–Joiner ou uma alternativa de Wilcoxon, esses métodos ainda faltam. |
| 4a — Provedores | A47:C62 | 15 por grupo | Boxplots, AD por grupo, ANOVA clássica/Tukey ou Welch/Games–Howell | G2 tem AD p≈0,028554 e outlier suave 3,8. A razão maior/menor variância≈13,817 ultrapassa inclusive a regra de 9 do PDF. Kruskal–Wallis, citado no material, ainda falta; também não há teste global de igualdade de três variâncias. |
| 4b — Resistência dos lotes | E47:G82 | 35 por grupo | ANOVA/Tukey, alternativa Welch/Games–Howell, AD e boxplots | AD rejeita nos lotes 1 e 2 (p≈0,016114 e 0,029523); lote 3 p≈0,053098. O PDF admite a rota paramétrica por N≥30, mas essa regra não é uma garantia universal. Razão maior/menor variância≈3,676. O F disponível compara somente dois grupos; a comparação simultânea e robusta das três variâncias não está pronta. |
| 4c — Qualidade de vida e profissões | I47:K61 | 14 por grupo | ANOVA/Tukey, AD e boxplots | Professor tem AD p≈0,021698, sem outliers pelo boxplot. Pode exigir a rota de Kruskal–Wallis, que falta. O aplicativo ainda não testa globalmente as três variâncias. |
| 5a — Prints e tempo | A87:B96 | 9 pares X/Y | Pearson/Spearman, regressão simples, dispersão e gráficos de resíduos | Cálculo principal disponível. O exame dos pré-requisitos requer interpretação dos gráficos; não há Ryan–Joiner ou teste formal de normalidade bivariada. Para testar numericamente os resíduos, copie/preencha esses valores em uma coluna. |
| 5b — Pessoas e prazo | E87:F95 | 8 pares X/Y | Os mesmos procedimentos de 5a | Mesmas ressalvas, com apenas oito observações. Não confundir uma correlação negativa com prova de causalidade. |

### Resultados principais que o núcleo conseguiu calcular

Os números abaixo são conferências da execução; não substituem a decisão sobre pré-requisitos ou o desenvolvimento das respostas.

| Dados | Resultado, com observações mantidas |
| --- | --- |
| Tempo | Student combinado: T≈−3,972931; GL=29; p≈0,000431. Welch com GL truncado: p≈0,001087. |
| Produtividade | Student combinado: T≈−2,650514; GL=28; p≈0,013072. |
| Custo | Diferença Antes−Depois≈−396,421; T≈−11,659876; GL=18; p≈8,01×10⁻¹⁰. |
| Colesterol | Diferença Antes−Depois≈108,833; T≈6,855478; GL=11; p≈0,0000274422. |
| Provedores | ANOVA clássica: F≈41,415584; p≈1,16×10⁻¹⁰. |
| Lotes | ANOVA clássica: F≈471,482139; p≈2,91×10⁻⁵². |
| Qualidade de vida | ANOVA clássica: F≈49,796846; p≈1,83×10⁻¹¹. |
| Prints e tempo | r≈0,990500; p≈2,73×10⁻⁷; Tempo≈0,862543 + 0,321392×Prints; R²≈98,109%. |
| Pessoas e prazo | r≈−0,978160; p≈0,0000256204; Prazo≈92,140449 − 5,421348×Pessoas; R²≈95,680%. |

O tempo G1 tem uma observação a mais que G2: não a elimine para igualar tamanhos. O teste independente aceita tamanhos diferentes. No pareado, preserve rigorosamente os pares da mesma linha.

### Exclusão do 80: cenário condicional

Apenas como análise de sensibilidade, foi recalculado Tempo sem o 80: N=16/14, AD de G2≈0,606806, F p≈0,903242 e Student p≈0,000009312. Nesse cenário o núcleo executa o fluxo paramétrico. Isso **não autoriza excluir o 80 automaticamente**: a decisão precisa de justificativa e orientação compatível com o exercício, não deve ser tomada para obter normalidade ou um resultado desejado. Os arquivos originais e a análise principal mantiveram o valor.

## Cobertura do PDF

| Conteúdo | Páginas do PDF | Situação no MiniTaBom |
| --- | --- | --- |
| População/amostra, tipos de dados, delineamento e amostragem | 1–3 | Conteúdo teórico: o aluno precisa justificar. O programa não deduz aleatoriedade ou desenho do estudo só pelos números. |
| Tabela de frequências por classes, frequência relativa e acumulada | 3–5 | Falta um procedimento dedicado com a regra de classes e arredondamento do material. As porcentagens de tabelas de contingência não substituem esse fluxo. |
| Histograma | 6 | Existe, mas usa Sturges e no máximo 30 classes; ainda não oferece a configuração de classes/eixos ensinada no PDF. |
| Pareto e setores/pizza | 6–7 | Ainda não implementados. |
| Média, mediana, moda, desvio/variância amostrais, CV e quartis | 7–10 | Disponíveis nas descritivas. Para a moda, são mostrados os valores mais frequentes e sua frequência. |
| Desvio populacional, decis e percentis de dados observados | 9 | Sem opção direta para desvio populacional ou percentis arbitrários. O quantil de uma distribuição teórica no menu Calc é outra operação. |
| Boxplot e classificação de outliers suaves/extremos | 9–10 | Boxplot disponível, com pontos além de 1,5 IQR. A distinção automática por 3 IQR e símbolos/rótulos diferentes ainda falta; pode ser calculada a partir de Q1/Q3. |
| Correlação e regressão | 10–13 | Pearson/Spearman e regressão disponíveis; há gráficos de ajuste/resíduos. Normalidade bivariada não é comprovada por testar X e Y separadamente. |
| Normalidade e gráficos de probabilidade | 13–14, 18–20 | AD disponível em relatório textual. Faltam Ryan–Joiner, KS, Shapiro–Wilk, D’Agostino–Pearson e o gráfico de probabilidade como resultado da normalidade. O Q–Q de resíduos da regressão não substitui todos esses recursos. |
| Duas variâncias | 14–16, 20–21 | Teste F e IC sob normalidade disponíveis. Levene e os intervalos contínuos/robustos mostrados no PDF não estão completos; igualdade global de três ou mais variâncias não implementada. |
| t independente e pareado | 16–17 | Disponíveis, com hipóteses unilateral/bilateral, intervalos, Welch/variâncias iguais e resumos. |
| Mann–Whitney e Wilcoxon | 17 | Ainda não implementados na interface ou no núcleo próprio do aplicativo. |
| ANOVA e pós-teste | 17–21 | ANOVA de um fator e Tukey-Kramer disponíveis; também Welch/Games–Howell. Fisher LSD e vários diagnósticos/opções ainda faltam. |
| Kruskal–Wallis | 21 | Ainda não implementado. Empilhar dados já é possível, mas isso sozinho não executa o teste. |
| Proporções/binomial e Fisher | 21–22 | Uma e duas proporções e Fisher 2×2 disponíveis com métodos/limites explícitos. Não há dados binários específicos desses testes no Excel enviado. |

## Como usar a lista na versão atual

1. Trabalhe um conjunto por vez. O aplicativo ainda não importa `.xlsx` diretamente.
2. Copie apenas o bloco numérico do exercício para a planilha do MiniTaBom e renomeie os cabeçalhos. Também é possível preparar um CSV com cabeçalho. Não cole os enunciados como dados numéricos.
3. Para boxplots conjuntos: Gráfico > Boxplots comparativos. Para AD e F: Estat > Estatísticas básicas > Teste de normalidade / Teste de duas variâncias.
4. Para t: Estat > Estatísticas básicas > Teste t de duas amostras / Teste t pareado. Marque variâncias iguais somente quando esse for o modelo a estudar.
5. Para ANOVA: Estat > ANOVA > Um fator. As comparações opcionais usam Tukey-Kramer quando se assume variância igual, ou Games–Howell na alternativa sem variância igual.
6. Para a questão 5: Estat > Estatísticas básicas > Correlação; depois Estat > Regressão > Ajustar modelo linear. Y é tempo/prazo, X é quantidade de prints/pessoas. Exiba gráficos e tabela de observações para inspecionar resíduos.
7. Prepare as diferenças pareadas ou copie os resíduos para uma coluna adicional quando precisar rodar AD nesses valores. Não há cálculo automático dessas colunas.

## Cuidados de interpretação para estudar

- p>0,05 em um teste de normalidade não prova que a população é normal; significa que o teste não forneceu evidência suficiente contra esse modelo.
- No pareado, a distribuição relevante para a inferência é a das diferenças. Não é obrigatório que os dois lados, isoladamente, tenham variâncias iguais.
- No exemplo do PDF, página 17, aparece a divisão de um valor-p bilateral por 2. Não faça essa divisão automaticamente: uma hipótese unilateral deve ser escolhida de acordo com a pergunta e a direção. O MiniTaBom já calcula o valor-p para a alternativa selecionada.
- A regra de razão de variâncias até 9 e o atalho N≥30 constam do material; não são garantias gerais de validade. A robustez depende também de forma das distribuições, valores extremos, balanceamento e objetivo da análise.
- Welch ajusta a comparação para variâncias diferentes; não transforma dados em normais nem substitui uma análise de outliers ou uma alternativa não paramétrica por si só.

Fontes complementares oficiais, consultadas em 03/11/2026: [normalidade e distinção dos métodos](https://support.minitab.com/en-us/minitab/help-and-how-to/statistics/basic-statistics/how-to/normality-test/methods-and-formulas/methods-and-formulas/), [interpretação do teste de normalidade](https://support.minitab.com/en-us/minitab/help-and-how-to/statistics/basic-statistics/how-to/normality-test/interpret-the-results/key-results/), [t pareado e diferenças](https://support.minitab.com/en-us/minitab/help-and-how-to/statistics/basic-statistics/how-to/paired-t/interpret-the-results/all-statistics-and-graphs/), [considerações para duas amostras](https://support.minitab.com/en-us/minitab/help-and-how-to/statistics/basic-statistics/how-to/2-sample-t/before-you-start/data-considerations/). Documentação atual não comprova paridade integral com Minitab 16.

## Prioridades para cobrir esses materiais

1. **Para a lista de exercícios:** Mann–Whitney e Kruskal–Wallis; igualdade de variâncias para mais de dois grupos/Levene; Ryan–Joiner e gráfico de probabilidade; criação e armazenamento das diferenças/resíduos.
2. **Para completar a rota não paramétrica do PDF:** Wilcoxon pareado, com tratamento explícito de zeros e empates.
3. **Para a parte descritiva do PDF:** tabela de frequências configurável, frequências relativas/acumuladas, Pareto, setores, percentis/decis e distinção de outliers extremos.
4. **Para facilitar o uso do material:** importação direta Excel e um roteiro de análise que reúna pré-requisitos sem substituir a interpretação do aluno.

Nenhum desses recursos novos foi implementado nesta avaliação. A lista serve para orientar a próxima etapa do desenvolvimento, mantendo o alvo do Minitab 16.
