> Atualização 0.2.0: os recursos de estudo acrescentados estão descritos no README da raiz e em METODOS_ESTUDO.md. As seções antigas deste manual preservam o histórico; pendências citadas antes dessa atualização podem já ter implementação parcial.

# Manual técnico do MiniTaBom

Este manual preserva o detalhamento e o histórico do projeto. Execute os comandos a partir da raiz do repositório. O código está em `src/`, os testes em `tests/`, os exemplos em `exemplos/` e a documentação em `docs/`. Para abrir o programa pronto, use `Aplicativo/MiniTaBom.exe` ou `MiniTaBom.bat` na raiz. Consulte o README da raiz para o início rápido.

# MiniTaBom

**Projeto independente desenvolvido para fins educativos e estudo de estatística.** O MiniTaBom permite praticar análises, explorar métodos estatísticos e aprender sobre o desenvolvimento de software científico.

Implementação independente inicial para Windows em português. Referência pretendida: Minitab 16.2.4.0. Não é um equivalente completo. Compatibilidade numérica ainda não validada.

O projeto não possui vínculo, patrocínio ou endosso da Minitab. As referências ao software Minitab têm finalidade de estudo e comparação funcional. Minitab é marca de seus respectivos titulares.

## Usar sem instalar Python (Windows x64)

Na página de **Releases** do repositório, baixe `MiniTaBom-Windows-x64.zip` quando o pacote estiver publicado. Extraia a pasta inteira e abra **MiniTaBom.exe**. Mantenha a pasta `_internal` junto do executável. Não é necessário instalar Python, dependências ou Minitab, e o programa funciona offline após o download.

A pasta `Exemplos` acompanha o pacote. Abra um exemplo pelo menu Arquivo > Abrir projeto e salve seus próprios arquivos em uma pasta com permissão de escrita.

O ZIP portátil precisa ser enviado às Releases pelo responsável pelo repositório. O download do código-fonte do GitHub não inclui automaticamente o executável.

## Executar a partir do código

Abra MiniTaBom.bat (ou iniciar.bat) ou execute python src/app.py nesta pasta. Requer Python 3.11 ou superior com Tkinter. Planilha, descritivas e gráficos básicos usam a biblioteca padrão. Testes t, ANOVA, correlação e regressão usam SciPy/NumPy: execute instalar_dependencias.bat uma vez para instalar as dependências dentro de .deps, nesta pasta. A instalação atual já possui SciPy 1.18.1 e NumPy 2.5.4, testados com Python 3.14.2. Dados iniciais fictícios.

## Disponível

Planilha editável na própria célula, novas linhas/colunas, desfazer/refazer, ordenação, empilhamento/desempilhamento, projetos .statlab, CSV UTF-8 com cabeçalho (vírgula, ponto e vírgula ou tabulação), exportações CSV/texto, descritivas por grupo, testes t/Z, uma/duas proporções, uma/duas variâncias, normalidade Anderson–Darling, tabelas de contingência e qui-quadrado, ANOVA de um fator, correlação, regressão linear com previsão e calculador de 12 distribuições. Gráficos disponíveis: histograma, boxplot, boxplots comparativos, dispersão, séries na ordem da planilha e diagnósticos de regressão. Dispersão/séries permitem exportar SVG. As seções abaixo descrevem opções e limitações. Números aceitam ponto ou vírgula decimal sem separadores de milhar. Ausentes são vazios ou asteriscos. Desvio padrão e variância usam n−1; com N=1 são indefinidos.

## Interface e atalhos

Menus Arquivo, Editar, Dados, Calc, Estat, Gráfico, Janela e Ajuda; sessão acima da planilha, barras compactas e controles nativos do Windows. A grade usa Canvas, com linhas entre células, identificação C1/C2 separada dos nomes das variáveis e cabeçalhos fixos durante a rolagem. Uma borda azul identifica a célula ativa. A barra inferior informa o estado e o tamanho real dos dados. Arraste a divisória para ajustar as áreas.

O gerenciador de projeto fica recolhido inicialmente. Mostre-o pelo controle Projeto na barra ou por Janela > Gerenciador de projeto; a lista de análises continua disponível nele. Ctrl+M ativa a sessão; Ctrl+D ativa a planilha. A barra de título azul identifica a área com foco. A roda do mouse rola linhas, e Shift+roda rola horizontalmente. Somente as colunas existentes têm cabeçalhos e aceitam edição; use + Coluna para ampliar os dados. A grade desenha somente o trecho visível, inclusive em planilhas extensas.

Referências de organização da interface clássica: [guia do Minitab 16 da NYU](https://pages.stern.nyu.edu/~gsimon/QuickIntroMinitab16_2010SEP02.pdf), seções Minitab’s Windows e Managing the Minitab Screen, e [instruções de laboratório da UQ](https://courses.smp.uq.edu.au/STAT2201/2016a/minitab_guide.pdf), página 2. A organização foi aproximada; reprodução visual exata, janelas internas livres e paridade completa continuam pendentes.

- Duplo clique ou F2 edita a célula selecionada; digitar na planilha começa uma edição substituindo seu conteúdo.
- Enter confirma e edita a próxima linha; Tab confirma e edita a próxima célula; Esc cancela a edição atual. Fora da edição, as setas mudam a célula selecionada.
- Arraste entre células ou use Shift+clique/Shift+setas para selecionar um retângulo. Clique nos números de linha ou cabeçalhos de coluna para selecionar linhas/colunas; Ctrl+A seleciona o retângulo de dados. Ctrl+Home e Ctrl+End vão ao início e à última célula do retângulo de dados.
- Ctrl+C copia a seleção como bloco TSV, com aspas para preservar tabulações, quebras de linha e aspas dentro das células. Ctrl+V cola a partir do canto superior esquerdo da seleção, preservando texto e vírgula decimal e adicionando linhas se necessário. Adicione antes as colunas necessárias: um bloco mais largo que a área disponível é recusado integralmente. O menu Editar também oferece essas ações.
- Delete limpa o conteúdo da seleção sem remover linhas/colunas. A limpeza de um bloco constitui uma alteração no histórico e pode ser desfeita com Ctrl+Z. Selecionar ou limpar apenas linhas virtuais vazias não cria observações.
- As linhas vazias exibidas no final são espaço para digitação e só entram nos dados ao receber conteúdo. O nome da célula ativa e seu valor aparecem acima da grade.
- Duplo clique no cabeçalho renomeia a coluna. Arraste a separação entre cabeçalhos para alterar a largura; duplo clique na separação ajusta a largura ao conteúdo (entre 60 e 600 pixels lógicos). As larguras são preferências temporárias da janela, não alteram os dados nem são salvas no projeto. O menu Dados também permite renomear, adicionar linha e adicionar coluna.
- Ctrl+N cria um projeto vazio; Ctrl+O abre projeto; Ctrl+S salva; F1 mostra instruções. Arquivo também oferece importação CSV e exportações.
- A edição em andamento é confirmada antes de salvar, analisar ou substituir o projeto. A sessão permite desfazer texto. O menu Editar oferece desfazer/refazer da planilha; Ctrl+Z/Ctrl+Y funcionam quando a grade tem foco. O histórico da planilha mantém até 50 alterações em memória, incluindo células, blocos colados, adição e renomeação de colunas e adição de linhas. Ele é reiniciado ao abrir/importar/criar projeto, e não é gravado no .statlab. Desfazer não altera os resultados já escritos na sessão.

O botão Descritivas abre abas Dados e grupos e Estatísticas. O diálogo oferece selecionar/desmarcar todas as medidas e confirma com Enter ou cancela com Esc. Os resultados permanecem na sessão após editar os dados: execute a análise novamente para atualizá-los.

### Descritivas por grupo

Na aba Dados e grupos, selecione uma ou mais respostas numéricas à esquerda e, opcionalmente, colunas de grupo em Por variáveis à direita. As colunas de grupo devem ser distintas das respostas. Cada combinação observada recebe um resumo próprio; ausentes em uma resposta não excluem valores de outra resposta. O relatório informa quantas linhas foram excluídas por grupo ausente e permanece no projeto junto à sessão.

As categorias são textos aparados e seguem a ordem de primeira aparição; por exemplo, os textos 1 e 1,0 constituem grupos distintos. Vazio e asterisco são grupos ausentes. Por padrão, linhas com qualquer grupo ausente são excluídas. A opção Incluir valores de grupo ausentes reúne esses valores em um nível separado, sem confundir com um rótulo literal de mesmo nome. Com dois ou mais grupos, Incluir combinações sem observações gera o produto dos níveis observados nas linhas incluídas. O padrão do MiniTaBom exibe apenas combinações observadas. Há limite de 10.000 grupos.

Grupos sem respostas válidas mostram N=0, a contagem de ausentes e as demais medidas como indefinidas. Combinações sem linhas mostram também Ausentes=0 e N total=0. A sequência dentro de cada grupo segue a ordem das linhas, inclusive para o MSSD. Tipos de coluna, ordenação numérica, padrões e convenções em grupos vazios ainda precisam de comparação com a versão 16.

Abra exemplo_descritivas_grupos.statlab para conferir um caso com duas respostas, dois grupos e ausentes. Fontes complementares atuais: [entrada de dados de Display Descriptive Statistics](https://support.minitab.com/en-us/minitab/help-and-how-to/statistics/basic-statistics/how-to/display-descriptive-statistics/perform-the-analysis/enter-your-data/) e [opções de grupos de Store Descriptive Statistics](https://support.minitab.com/en-us/minitab/help-and-how-to/statistics/basic-statistics/how-to/store-descriptive-statistics/perform-the-analysis/select-the-analysis-options/). A segunda referência descreve armazenamento no Minitab; o MiniTaBom implementa aqui a exibição agrupada, ainda sem armazenar os resultados em novas colunas.

No menu Arquivo, use Salvar projeto ou Salvar projeto como para guardar a planilha e o texto dos resultados em um arquivo .statlab. Abrir projeto restaura esses dados. O asterisco no título indica alterações não salvas; fechar, abrir outro projeto ou importar CSV oferece salvar, descartar ou cancelar. Importar CSV inicia um novo projeto e limpa os resultados anteriores. Exportar CSV ou texto não equivale a salvar o projeto completo.

A gravação de projeto usa um arquivo temporário e substitui o destino após terminar a escrita. O formato .statlab é próprio, em JSON versionado, e não é compatível com MPJ/MTW. Gráficos abertos não são armazenados; podem ser gerados novamente com os dados.

CSV não preserva resultados: exporte-os separadamente ou salve um projeto. Não há salvamento automático, recuperação após falha, importação direta de Excel ou MPJ/MTW. A inferência está parcialmente implementada nos testes descritos abaixo. O histograma usa Sturges com até 30 classes, sem compromisso de reproduzir as regras gráficas do Minitab.

Os gráficos Histograma e Boxplot estão no menu Gráfico, usam a coluna atual e se redesenham ao redimensionar a janela. O histograma mostra escalas, frequências e N. O boxplot usa quartis interpolados, mediana, valores adjacentes às cercas Q1−1,5IQR e Q3+1,5IQR e símbolos para observações fora dessas cercas. Referência complementar: https://support.minitab.com/en-us/minitab/help-and-how-to/graphs/boxplot/interpret-the-results/ingrown-or-inverted-whiskers/ . A regra permite bigodes voltados para dentro em certas amostras pequenas. A comparação diferencial com Minitab 16 permanece pendente. Gráficos usam uma cópia dos dados do momento da criação; mudanças posteriores não os atualizam. Exportação destes dois gráficos ainda não implementada.

## Dispersão e séries temporais

Gráfico > Gráfico de dispersão aceita uma variável X e uma Y numéricas e, opcionalmente, uma coluna de grupo. É possível conectar os pontos na ordem das linhas: não há ordenação automática por X, agregação ou ajuste de regressão nesse comando. Gráfico > Gráfico de séries temporais usa os números originais das linhas como X; ainda não recebe datas, frequências ou várias respostas.

As duas análises permitem títulos personalizados e escalas logarítmicas (somente valores positivos nos pontos incluídos). Pares incompletos e grupos vazios/* são omitidos. Sem Conectar através de valores ausentes, um valor ausente interrompe a linha do respectivo grupo; um grupo ausente interrompe todas as séries já iniciadas, porque não é possível atribuir a lacuna. Grupos intercalados se conectam pela sequência de observações daquele grupo. O eixo das séries conserva os números de linha, inclusive lacunas, e usa marcas inteiras na escala linear.

A janela mostra N, omissões e detalhes do ponto sob o cursor. Exportar SVG salva uma imagem vetorial independente com textos, linhas, cores e detalhes dos pontos. O exportador e o Canvas usam a mesma cena de desenho; texto XML é escapado. O gráfico aceita até 20.000 pontos e 20 grupos. Continua fora do .statlab. Estilos, painéis, múltiplas respostas, datas, exportação raster/PDF e validação visual/numérica contra o Minitab 16 permanecem pendentes. Abra exemplo_graficos_xy.statlab para conferir grupos, lacunas e escalas.

## Operações de dados

Dados > Ordenar linhas oferece até três chaves, com direção e tipo individuais. A ordenação é estável e move todas as colunas juntas. Numérico usa Decimal para não confundir inteiros acima de 2⁵³; a célula mantém o texto original. Automático escolhe números somente se todos os valores não ausentes da chave forem decimais finitos. Texto compara valores aparados, opcionalmente sem distinguir maiúsculas/minúsculas, por ordem Unicode. A opção de ausentes no início/final vale também para a direção decrescente; não depende da direção da chave.

Dados > Empilhar colunas adiciona duas novas colunas: valores e nomes das fontes. Empilha uma coluna completa de cada vez, na ordem da seleção; a origem permanece intacta. O usuário pode omitir vazios/*. As colunas de destino devem ter nomes novos. O tamanho de cada fonte é o número total de linhas da tabela, inclusive vazios ao final, pois o formato atual não guarda comprimentos independentes de coluna.

Dados > Desempilhar por grupo adiciona uma coluna por categoria, em ordem de aparição, mantendo a ordem dos valores dentro do grupo. Categorias são textos aparados, sem unificação numérica. Grupos vazios/* são excluídos ou reunidos em uma coluna própria; valores ausentes podem ser mantidos ou omitidos separadamente. Um grupo só com valores ausentes ainda recebe coluna quando a omissão está ligada. Os nomes gerados distinguem grupos ausentes de rótulos literais e recebem sufixos em colisões com colunas existentes.

O resultado inteiro é validado antes de substituir a tabela. Empilhar/desempilhar preservam as fontes e preenchem com vazios o espaço necessário nas outras colunas. Há limite de 200.000 linhas, 512 colunas e 2.000.000 células no resultado dessas duas operações. Cada transformação constitui uma etapa de desfazer/refazer, invalida o modelo de regressão em memória e registra uma nota na sessão. Desfazer restaura a planilha; a nota e análises anteriores continuam na sessão. Ordenação sem mudança não altera o histórico. Os padrões e convenções ainda precisam de comparação com o Minitab. Abra exemplo_operacoes_dados.statlab para praticar.

## Continuidade para estudos com a versão 16

Uma análise estática da instalação 22.6 está em docs/analise_instalacao/. O catálogo relaciona 612 recursos de tradução pt-BR do pacote principal, 24 recursos de gráficos e 183 blocos do arquivo de diálogos legado, com origem e limites da interpretação. Esses números incluem componentes compartilhados e não contam funções distintas. lacunas_priorizadas.json cruza os achados com o que falta no MiniTaBom. O script tools/inspect_minitab_installation.py reproduz a leitura sem carregar DLLs ou executar os pacotes; a instalação original é usada somente para leitura. O relatório técnico detalha os resultados.

O alvo funcional continua sendo o Minitab 16.2.4.0. A instalação disponível é o Minitab 22.6.0.0; um caso Welch foi comparado com os valores arredondados da interface dessa versão, conforme fixtures/welch_minitab_22_6/observed.json. Não há validação integral nem comparação executada contra a versão 16.

A janela usa sessão acima da planilha, com divisória ajustável e colunas identificadas por C1, C2 etc. A organização aproxima o fluxo clássico; não é uma cópia visual validada do Minitab 16. Acesse Estat > Estatísticas básicas > Exibir estatísticas descritivas para selecionar várias variáveis e as medidas desejadas.

Novas medidas: N total, Q1, Q3, intervalo interquartil, amplitude, coeficiente de variação e soma dos quadrados. Quartis usam posições (n+1)p com interpolação linear. Para posições fora da amostra, o MiniTaBom limita ao mínimo/máximo; essa convenção em amostras pequenas ainda exige confirmação no Minitab 16. CV usa 100s/média, é indefinido com média zero ou n=1 e conserva o sinal da média negativa. Soma dos quadrados é não centrada. As medidas continuam sem validação diferencial; testes analíticos não demonstram equivalência com o Minitab.

Referência documental complementar: https://support.minitab.com/en-us/minitab/help-and-how-to/statistics/basic-statistics/how-to/store-descriptive-statistics/methods-and-formulas/methods-and-formulas/ (consultada em 22/10/2026). É documentação atual, não um manual da versão 16. O relatório antigo registra a mesma regra central dos quartis; casos extremos permanecem pendentes.

Ainda faltam percentuais e contagens acumuladas, armazenamento e resumo gráfico para completar o contrato de DESCRIBE. Os agrupamentos estão implementados com as convenções descritas acima. A compatibilidade integral com a versão 16 não está estabelecida.

## Testes t e intervalos

Em Estat > Estatísticas básicas, escolha Teste t de uma amostra, Teste t pareado ou Teste t de duas amostras. O diálogo tem abas Dados e Opções, com colunas, hipótese, nível de confiança e alternativas bilateral, menor ou maior. Desmarque Realizar teste de hipótese para exibir apenas estimativas e intervalo/limite de confiança.

O teste de duas amostras aceita colunas separadas, dados resumidos ou resposta/grupo e oferece Welch (padrão) ou variâncias iguais combinadas. A opção de truncar os graus de liberdade de Welch fica marcada para reproduzir o comportamento documental das versões anteriores à 22.6; desmarcar usa GL fracionário. A documentação atual da Minitab registra explicitamente essa mudança: https://support.minitab.com/en-us/minitab/help-and-how-to/statistics/basic-statistics/how-to/2-sample-t/methods-and-formulas/methods-and-formulas/ . A instalação do Minitab 16 não foi usada para confirmação experimental desse padrão.

No pareado, a diferença é primeira coluna menos segunda; linhas com um ou ambos os valores ausentes são excluídas como pares. Em amostras independentes, ausentes são omitidos separadamente. Cada amostra analisada requer pelo menos duas observações válidas. Erro padrão zero é recusado com mensagem; equivalência do comportamento de erro com o 16 não está estabelecida. As pressuposições de amostragem, independência e distribuição precisam ser avaliadas pelo usuário.

Probabilidades e quantis vêm de scipy.stats.t. Os resultados mostram N, média, desvio amostral, erro padrão, estimativa, intervalo/limite, T, GL e valor-p. Valores-p menores que 0,000001 são exibidos por limite, sem arredondar para zero exato. Ainda faltam gráficos anexos, análises simultâneas e armazenamento estruturado dos resultados. Entradas resumidas e duas amostras empilhadas estão disponíveis, conforme descrito abaixo. O arquivo .statlab preserva o texto da sessão.

O navegador lateral lista as análises identificadas na sessão e permite voltar ao trecho correspondente. A lista é reconstruída ao abrir o projeto; alterações manuais nos títulos podem removê-las da lista. Títulos de relatório recebem destaque e o corpo usa fonte monoespaçada.

## Teste Z e teste de uma proporção

Estat > Estatísticas básicas oferece Teste Z de uma amostra e Teste de uma proporção. Ambos aceitam coluna ou dados resumidos, confiança, alternativas bilateral/unilaterais e a opção de mostrar apenas o intervalo. Ausentes são vazio e *. Os novos diálogos têm abas com ícones e os relatórios entram no navegador de resultados.

Z exige N≥2, média e sigma populacional conhecido positivo; EP=σ/√N e Z=(média−hipótese)/EP. Usa quantis/caudas normais. Dados constantes são permitidos porque sigma é informado. Fonte complementar: [métodos do teste Z do Minitab](https://support.minitab.com/en-us/minitab/help-and-how-to/statistics/basic-statistics/how-to/1-sample-z/methods-and-formulas/methods-and-formulas/).

Proporção aceita eventos/ensaios inteiros ou coluna com até duas categorias textuais aparadas. O evento distingue maiúsculas/minúsculas. Com uma categoria observada, é possível informar um evento não observado (zero eventos); com duas, o evento deve ser uma delas. Os limites resumidos são 0≤eventos≤N e 1≤N≤2.147.483.647.

Métodos disponíveis: exato por caudas inclusivas, com valor-p bilateral min(1; 2min(P(X≤k);P(X≥k))) e IC Clopper–Pearson; aproximação normal com teste score e IC Wilson sem correção; ou teste score e IC Wald. As aproximações exigem hipótese entre 0 e 1, sem extremos. O IC Wald não é cortado em [0;1] e pode degenerar nas bordas; o relatório explica essa limitação. Referências: [métodos de proporção do Minitab](https://support.minitab.com/en-us/minitab/help-and-how-to/statistics/basic-statistics/how-to/1-proportion/methods-and-formulas/methods-and-formulas/) e [intervalos binomiais do SciPy](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats._result_classes.BinomTestResult.proportion_ci.html).

O exato por caudas não implementa o método Blaker ajustado da documentação atual. A comparação executada nas versões 16/22 continua pendente para este bloco. Faltam várias amostras simultâneas, correção de continuidade, gráficos e armazenamento em colunas. Duas proporções são descritas na seção seguinte. Abra exemplo_z_proporcao.statlab para um caso sintético guiado.

## Duas proporções, variâncias, tabelas e normalidade — 24/10/2026

Novos comandos em Estat > Estatísticas básicas: Teste de duas proporções, Teste de uma variância, Teste de duas variâncias e Teste de normalidade. Estat > Tabelas oferece Qui-quadrado de associação. Diálogos têm abas/ícones e os relatórios são indexados no navegador e preservados no texto do projeto. Entradas inválidas mantêm o diálogo e não acrescentam relatórios parciais. Não há comparação executada desses métodos com as versões 16/22; os padrões e limites abaixo são contratos explícitos do MiniTaBom.

### Duas proporções

Aceita duas colunas, uma coluna binária empilhada com grupo, ou eventos/ensaios resumidos de cada amostra. Em colunas separadas os eventos podem usar codificações diferentes, informadas individualmente; empilhadas usam o mesmo evento. As categorias são textos aparados, distinguindo maiúsculas. Cada amostra aceita até duas categorias; com duas categorias o evento deve ser observado; com uma é permitido especificar um evento não observado. Em colunas separadas ausentes são omitidos independentemente. No formato empilhado são necessários exatamente dois grupos: amostra 1 é o primeiro observado e amostra 2 o segundo; o relatório identifica ambos. Grupo ausente exclui a linha antes da leitura da resposta.

Estima p1−p2 e usa IC Wald com erro padrão separado √(p1(1−p1)/n1+p2(1−p2)/n2). O teste Z permite esse mesmo erro ou estimativa combinada sob hipótese zero; combinada com hipótese diferente de zero é recusada. Oferece alternativas bilateral/unilaterais, confiança e relatório sem teste. O intervalo bilateral não é cortado em [−1;1]; unilaterais usam a fronteira física −1 ou 1 no lado aberto. IC degenerado, erro do teste zero e contagens menores que 5 são identificados. Erro do teste zero produz Z/valor-p normal indisponíveis, conservando o IC e Fisher quando aplicável. Resumos exigem inteiros 0≤eventos≤N e 1≤N≤2.147.483.647 por amostra.

Fisher adicional é condicional às margens para H0: p1−p2=0; bilateral soma probabilidades de tabelas tão ou menos prováveis que a observada, conforme scipy.stats.fisher_exact, incluindo empates numéricos. As caudas unilaterais seguem a alternativa selecionada. Não se presume igualdade dos empates/valores padrão com Minitab 16. Há limite operacional explícito de 1.000.000 ensaios somados para Fisher; acima disso o relatório explica a omissão e conserva os cálculos normais. Não há intervalo exato para a diferença, correção de continuidade, outras aproximações, gráficos ou armazenamento em colunas. Veja exemplo_proporcoes_variancias.statlab. Fontes: [duas proporções Minitab](https://support.minitab.com/en-us/minitab/help-and-how-to/statistics/basic-statistics/how-to/2-proportions/methods-and-formulas/methods-and-formulas/) e [Fisher SciPy](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.fisher_exact.html).

### Uma e duas variâncias

Aceitam coluna (uma amostra), colunas separadas ou resposta/grupo (duas), e resumos N/dispersão. Em Opções escolha Desvio padrão ou Variância: essa escolha define a medida dos resumos, hipótese, estimativa e IC; na comparação, a razão é sempre amostra 1 dividida pela 2. Ao trocar a medida, confira os valores numéricos que digitou: eles não são convertidos automaticamente. Relatórios mostram N, ausentes, desvio e variância de cada amostra. Exigem N≥2, dispersões/hipótese positivas e representáveis; amostras constantes são recusadas explicitamente.

Uma amostra usa X²=(N−1)s²/σ0² com N−1 GL e limites derivados dos quantis qui-quadrado. Duas usam F=(s1²/s2²)/razão0² para razão de desvios, ou F=(s1²/s2²)/razão0 para razão de variâncias, com GL=(n1−1,n2−1). IC da razão de variâncias é (razão/F superior, razão/F inferior); desvio e razão de desvios usam raízes dos limites. Ambos oferecem alternativas/limites unilaterais, confiança e intervalo sem teste. Valores-p bilaterais usam min(1,2min(CDF,SF)); caudas/quantis vêm de SciPy. São métodos para populações normais e amostras independentes, sensíveis a não normalidade. Bonett, Levene, mais de duas variâncias, gráficos e validação dos padrões do 16 permanecem pendentes. Referências: [uma variância Minitab](https://support.minitab.com/en-us/minitab/help-and-how-to/statistics/basic-statistics/how-to/1-variance/methods-and-formulas/methods-and-formulas/) e [duas variâncias Minitab](https://support.minitab.com/en-us/minitab/help-and-how-to/statistics/basic-statistics/how-to/2-variances/methods-and-formulas/methods-and-formulas/).

### Contingência e qui-quadrado de associação

Entrada por duas colunas categóricas com frequência opcional, ou matriz em colunas selecionadas com rótulos opcionais. Não inclua os totais marginais na seleção. Frequências são inteiros não negativos, até 2.147.483.647 por célula/linha de entrada, com total até 2⁵³−1. No formato categórico, linhas com variável/frequência ausente são excluídas; frequência zero não cria categorias. Categorias seguem a primeira aparição. Na matriz, linhas com todas as contagens vazias/* são omitidas; ausências parciais são recusadas, exigindo 0 quando não houve ocorrência. Rótulos opcionais devem ser únicos e não ausentes. Limite de 50 categorias em cada dimensão. Margens zero são recusadas para que o usuário remova explicitamente a categoria.

Pearson soma (O−E)²/E, razão de verossimilhanças soma 2O ln(O/E), com termo zero em O=0; a implementação usa uma forma equivalente estável perto da independência. E=total da linha × total da coluna/N e GL=(linhas−1)(colunas−1). Sem correção de Yates. Se alguma esperada <1, não exibe os valores-p assintóticos; identifica células com esperadas <5. Fisher bilateral adicional em 2×2 segue a convenção SciPy e o mesmo limite operacional de 1.000.000 observações. A aba Exibição oferece esperadas, resíduos brutos/padronizados/ajustados, contribuições e percentuais por linha/coluna/total. Não há teste de aderência de uma variável, estratificação, testes exatos RxC, gráficos ou armazenamento estruturado. Veja exemplo_contingencia.statlab. Fonte: [métodos de associação Minitab](https://support.minitab.com/en-us/minitab/help-and-how-to/statistics/tables/how-to/chi-square-test-for-association/methods-and-formulas/methods-and-formulas/).

### Normalidade Anderson–Darling

Aceita uma coluna numérica, de 3 a 200.000 números válidos, omitindo vazio/*. Recusa constantes e valores não finitos. Estima média e desvio amostral (N−1), ordena e calcula A² com logCDF/logSF normal para evitar perda nas caudas. A estatística usada no valor-p é A²(1+0,75/N+2,25/N²), com aproximações polinomiais/exponenciais publicadas; A² ajustado acima de 13 é informado por limite aproximado de valor-p, sem exibir zero exato. Os limites de faixas são [0;0,2), [0,2;0,34), [0,34;0,6) e [0,6;13]. Relatório mostra N, ausentes, média, desvio, A² original/ajustado e repetições, alertando para pouco poder com N<20. Não há Ryan–Joiner, Kolmogorov–Smirnov, gráfico de probabilidade, seleção de múltiplas respostas ou armazenamento em colunas. Veja exemplo_normalidade.statlab. Fontes: [normalidade Minitab](https://support.minitab.com/en-us/minitab/help-and-how-to/statistics/basic-statistics/how-to/normality-test/methods-and-formulas/methods-and-formulas/), [considerações de amostragem](https://support.minitab.com/en-us/minitab/help-and-how-to/statistics/basic-statistics/how-to/normality-test/before-you-start/data-considerations/) e [fórmulas/correção statsmodels](https://www.statsmodels.org/stable/_modules/statsmodels/stats/_adnorm.html). A implementação usa SciPy para caudas, sem adicionar dependência de statsmodels.

## ANOVA de um fator e gráficos por grupo

Em Estat > ANOVA > Um fator, selecione grupos em colunas separadas ou uma coluna de resposta com outra de fator. A seleção pode ser feita com Ctrl/Shift ou Selecionar todas. Cada grupo precisa de pelo menos duas observações válidas nesta implementação. Ausentes são vazios ou *; em dados empilhados, fator ausente exclui a linha. Os níveis do fator são tratados como texto aparado e preservam a ordem de primeira aparição; rótulos numéricos textuais como 1 e 1,0 não são unificados.

O padrão é ANOVA clássica, assumindo variâncias iguais, com SQ/GL/QM, F, p, S, R² e ICs individuais das médias com desvio combinado. Desmarcar variâncias iguais calcula Welch com GL fracionário. Com comparações múltiplas marcadas, usam-se Tukey-Kramer no modelo clássico e Games-Howell em Welch, com valores-p ajustados e intervalos simultâneos no nível familiar selecionado. Os ICs das médias são individuais e não substituem essas comparações. Pressuposições de independência, normalidade e variâncias precisam ser avaliadas conforme o método.

Gráfico > Boxplots comparativos oferece os mesmos dois formatos de dados, escala comum, N por grupo e rolagem para muitos grupos. Também é possível abrir o gráfico a partir das opções da ANOVA. Assim como os outros gráficos, ele usa uma cópia dos dados do momento da criação e não é salvo no projeto.

Abra exemplo_anova.statlab ou exemplo_anova_empilhada.statlab para estudar o mesmo caso nos dois formatos. São exemplos sintéticos com F=27 e p=0,001 conhecidos analiticamente; não são resultados exportados do Minitab.

Limites atuais: grupos com menos de duas observações são recusados; erro dentro dos grupos igual a zero é recusado; Welch exige variância positiva em cada grupo. Ainda faltam modelos com vários fatores, blocos e efeitos aleatórios, métodos Fisher/Dunnett/Hsu, letras de agrupamento, resíduos e diagnósticos, armazenamento e validação diferencial do conjunto de opções com o Minitab 16. Não presumir compatibilidade do comportamento em casos extremos.

Referências complementares de métodos atuais: https://support.minitab.com/en-us/minitab/help-and-how-to/statistical-modeling/anova/how-to/one-way-anova/methods-and-formulas/analysis-of-variance/ e https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.tukey_hsd.html . O uso de SciPy para probabilidades/comparações não demonstra equivalência integral com a versão 16.

## Correlação

Acesse Estat > Estatísticas básicas > Correlação. Selecione duas ou mais colunas numéricas com Ctrl/Shift. A aba Opções e resultados permite escolher Pearson ou Spearman e excluir ausentes por par (padrão) ou usar somente linhas completas em todas as colunas selecionadas. O relatório lista cada par com N, coeficiente e valor-p bilateral para H0: correlação=0, sem ajuste por comparações múltiplas.

Pearson recebe IC individual pela transformação de Fisher com N>3. Spearman usa postos médios nos empates e a mesma transformação t para o valor-p, com N−2 graus de liberdade. O IC de Spearman ainda não está implementado; o campo de confiança fica desabilitado nesse método. Pares com menos de três observações ou variável constante mostram resultado indefinido, com motivo. Correlações perfeitas, na precisão de arredondamento, mostram coeficiente ±1, valor-p por limite e IC de Pearson degenerado quando N>3.

Fonte complementar atual: [métodos de correlação do Minitab](https://support.minitab.com/en-us/minitab/help-and-how-to/statistics/basic-statistics/how-to/correlation/methods-and-formulas/methods-and-formulas/). O exemplo Spearman dessa página foi registrado em fixtures/spearman_documentation/observed.json; os dois valores arredondados conferem, com tolerância de meia unidade do último decimal. Isso é uma referência documental, sem execução no Minitab 16. Matriz gráfica, armazenamento e opções restantes continuam pendentes.

## Regressão linear

Acesse Estat > Regressão > Ajustar modelo linear. Selecione a resposta e um ou mais preditores numéricos distintos. O ajuste atual é de mínimos quadrados com intercepto e efeitos lineares. Linhas com qualquer ausente nas variáveis do modelo são omitidas, preservando a numeração original da planilha nos diagnósticos. É necessário ter mais linhas completas que coeficientes.

O relatório apresenta a equação, coeficientes, erros padrão, testes t bilaterais contra zero, ICs individuais configuráveis, VIF, ANOVA global, S, R², R² ajustado, PRESS e R² predito. Como na documentação atual, R² ajustado e predito negativos são exibidos como zero. A tabela opcional de observações inclui valores observados/ajustados, resíduos, resíduos padronizados internamente, alavancagem e distância de Cook. Se a alavancagem for praticamente 1, diagnósticos que dividem por 1−h e PRESS ficam indefinidos.

O ajuste usa centralização/escala e decomposição em valores singulares. Preditores constantes ou dependentes são recusados; o limite atual de condicionamento da matriz escalada é 10¹⁰. Ajustes com norma dos resíduos abaixo da tolerância numérica (32×epsilon×máximo(N, número de coeficientes)×norma da resposta escalada) são tratados como erro zero. Nesses casos, testes t/F e resíduos padronizados ficam indefinidos. Uma resposta constante também torna R² indefinido. Esses tratamentos não foram comparados com a versão 16.

A opção gráfica abre quatro painéis: reta ajustada na regressão simples (ou observados × ajustados na múltipla), resíduos × ajustados, Q–Q normal dos resíduos e resíduos na ordem dos dados. O Q–Q usa posições (i−0,375)/(N+0,25), com i de 1 a N. Os gráficos são snapshots e não constituem um teste de normalidade. Permanecem fora do projeto salvo; o texto dos resultados é preservado no .statlab.

Exemplos de estudo: exemplo_regressao_simples.statlab e exemplo_regressao_multipla.statlab, com entradas e resultados analíticos. A validação inclui fórmulas fechadas, comparação com scipy.stats.linregress e PRESS por reajustes explícitos deixando uma observação de fora. Não houve comparação executada com o Minitab 16 neste módulo.

Fontes complementares atuais do Minitab: [coeficientes e testes](https://support.minitab.com/en-us/minitab/help-and-how-to/statistical-modeling/regression/how-to/fit-regression-model/methods-and-formulas/coefficients/), [resumo do ajuste e PRESS](https://support.minitab.com/en-us/minitab/help-and-how-to/statistical-modeling/regression/how-to/fit-regression-model/methods-and-formulas/goodness-of-fit-statistics/) e [diagnósticos e VIF](https://support.minitab.com/en-us/minitab/help-and-how-to/statistical-modeling/regression/how-to/fit-regression-model/methods-and-formulas/diagnostic-measures/).

Ainda faltam preditores categóricos, termos/interações, modelos sem intercepto, pesos, transformações, seleção automática, falta de ajuste, SQ por termo, armazenamento em colunas e os modelos logísticos/não lineares. A previsão para novos casos está descrita na próxima seção. A implementação cobre o modelo linear numérico descrito acima; a família de regressão permanece parcial.

## Previsão após a regressão

Depois de ajustar um modelo linear, use Estat > Regressão > Prever novos casos. O comando usa o último modelo bem-sucedido dos dados atuais. Alterações na planilha, desfazer/refazer, abertura/importação de projeto ou criação de projeto limpam esse modelo em memória; é necessário ajustar novamente. Salvar apenas o texto do relatório não preserva um modelo reutilizável.

A aba Digitar casos aceita um caso por linha, com preditores na ordem indicada, separados por tabulação ou ponto e vírgula; vírgula decimal é aceita. A aba Colunas da planilha mapeia uma coluna para cada preditor, preservando as linhas originais e oferecendo omitir/rejeitar ausentes. A aba Intervalos conserva a última fonte de casos selecionada e permite confiança configurável e intervalos bilaterais ou limites inferiores/superiores.

Para cada caso, o relatório mostra previsão, EP da média, IC da média e IP de uma observação. Para s²=MSE e h₀=x₀'(X'X)⁻¹x₀, EP da média=s√h₀ e EP de predição=s√(1+h₀). Os quantis t usam os graus de liberdade do erro do ajuste. Os intervalos são individuais; não são bandas simultâneas. O cálculo usa a base escalada do ajuste para reduzir perda de precisão.

O relatório sinaliza preditores além do mínimo/máximo observados e alavancagem do novo caso acima da máxima no treino. Essa checagem não verifica todo o domínio multivariado nem garante segurança de extrapolação. Com erro residual nulo, os intervalos colapsam; isso é relatado explicitamente. Abra exemplo_previsao.statlab para conferir os casos X=2 e X=5 com fórmulas analíticas.

Fontes complementares atuais: [métodos de Predict no Minitab](https://support.minitab.com/en-us/minitab/help-and-how-to/statistical-modeling/using-fitted-models/how-to/predict/methods-and-formulas/methods-and-formulas/) e [tipos de intervalo](https://support.minitab.com/en-us/minitab/help-and-how-to/statistical-modeling/using-fitted-models/how-to/predict/perform-the-analysis/specify-the-confidence-and-prediction-intervals/). Sem validação diferencial no Minitab 16. Ainda faltam armazenamento das previsões em colunas, persistência do modelo, gráficos de intervalos e demais modelos.

## Calculador de distribuições

Em Calc > Distribuições de probabilidade, escolha Normal, t, qui-quadrado, F, binomial, Poisson, exponencial, uniforme, Weibull, lognormal, gama ou beta. As seis operações são densidade/massa pontual, acumulada P(X≤x), cauda P(X>x), probabilidade inclusiva entre limites e quantis pela acumulada ou cauda superior. O resultado entra na sessão e no navegador.

Parâmetros: normal (média/desvio); t/qui-quadrado (GL); F (GL numerador/denominador); binomial (n,p); Poisson (média); exponencial (média/escala); uniforme (mínimo/máximo); Weibull (forma/escala); lognormal (média e desvio de ln(X)); gama (forma/escala, não taxa); beta (formas α,β e suporte 0–1). Não há deslocamento adicional nas famílias positivas. Binomial usa n inteiro de 0 a 2⁵³−1. Nas discretas, intervalos incluem os inteiros entre ceil(a) e floor(b); P(X>x) usa cauda estrita. Quantis requerem 0<p<1. Densidades podem exceder 1 e ser infinitas em singularidades dos limites; não representam probabilidade em um ponto.

Fonte técnica: [distribuições e métodos do SciPy](https://docs.scipy.org/doc/scipy/tutorial/stats/probability_distributions.html). Testes analíticos cobrem relações normal/Cauchy/exponencial, somas binomiais/Poisson, parametrizações e inversões. A cauda superior usa SF diretamente, e intervalos na cauda usam diferença de SF para reduzir cancelamento. Ainda faltam cálculo em lote/armazenamento, geração aleatória, gráficos, outras distribuições/parametrizações e comparação com o 16.

## Ícones da interface

Comandos dos menus, barra de ferramentas e abas dos diálogos receberam ícones próprios de 18 px, inspirados na organização da referência visual fornecida pelo usuário. Não usam imagens ou bibliotecas externas. Texto, comandos e estados habilitado/desabilitado continuam associados aos controles. O menu Gráfico mostra os gráficos já implementados; demais famílias seguem no inventário de pendências.

## Verificação automatizada

python -m unittest -v

Testes analíticos e de casos extremos não demonstram equivalência com Minitab. Inspeção visual/manual ainda necessária.

Verificação de 24/10/2026: 191 testes aprovados. Execute também python tools/check_study_examples.py para validar o formato dos 14 exemplos, os cálculos demonstrados pelos exemplos novos e os inventários JSON. Diálogos novos foram exercitados em Tk oculto; a conferência visual nativa e a comparação executada com Minitab 16 continuam pendentes.

## Cobertura e continuidade

### Referências históricas específicas da versão 16 — 24/10/2026

Fontes catalogadas com identificação, links, localizadores e limites em docs/analise_instalacao/referencias_minitab16.json:

- [Meet Minitab 16, documento Minitab em transcrição de terceiro](https://manualzz.com/doc/11354467/minitab-minitab-16-statistical-software-user-guide): identifica Copyright 2010 e Release 16.1.0. Serve para fluxos, janelas, comandos, gráficos, planilha e exemplos; é introdutório, não exaustivo. [Espelho alternativo do catálogo](https://pdf.directindustry.com/pdf/minitab-ltd/meet-minitab/13108-155215.html).
- [Catálogo Minitab16 WhatsNew](https://pdf.directindustry.com/pdf/minitab-ltd/minitab16-whatsnew/13108-469601.html): documento de 12 páginas do fabricante, com novidades e seção Minitab 16 Features List na página 11. Os trechos/índice foram conferidos; todas as páginas dessa lista ainda não foram auditadas.
- [Histórico 16/16.2 da ADDITIVE](https://www.additive-net.de/en/software/produkte/minitab/minitab/versionshistorie/neu-in-minitab-16): diferencia novidades do lançamento das cartas Laney P'/U' e G/T adicionadas no 16.2. Considerar apenas as seções históricas, não os produtos atuais no menu lateral.
- [Slides Minitab de 2010 em alemão, 31 páginas](https://www.additive-net.de/images/software/minitab/downloads/MTB16_Whatsnew_DE.pdf): página 20 corrobora o método Bonett para uma variância. Texto conferido; captura visual indisponível nesta consulta.
- [Notas históricas Minitab 16, espelho não oficial](https://fliphtml5.com/ejsz/mric/Minitab_16_Statistical_Software/): seções separadas 16.2, 16.2.3, 16.2.4 e 16.2.4.4. A seção 16.2.3 registra correção de variâncias empilhadas com ausentes; serve para levantar casos de validação. Ainda requer corroboração do arquivo original.

Essas fontes permitem confirmar funcionalidades da época, mantendo separadas presença documentada, implementação parcial e validação executada. Para a cobertura integral, ainda precisamos auditar comando por comando e complementar com Minitab Help/StatGuide/Session Command Help/Methods and Formulas específicos do 16. O link antigo do manual no domínio Minitab retornou 404; os espelhos têm limitações de acesso/procedência registradas no catálogo. Nenhuma nova equivalência numérica foi estabelecida nesta pesquisa.

INVENTARIO_FUNCIONAL.json é o mapa atualizado de áreas implementadas e pendentes e dos critérios de aceite. Acesse Ajuda > Cobertura do projeto para consultar as 23 áreas e suas pendências dentro do aplicativo. O objetivo solicitado é cobertura funcional integral do Minitab 16.2.4.0, incluindo opções e possibilidades, sem exclusões implícitas. O mapa atual ainda não é um inventário exaustivo dos comandos e subcomandos da versão 16; não permite calcular percentual de completude. coverage.csv é a matriz preliminar histórica e pode conter pendências já implementadas. Decompor cada família em funções, subcomandos, opções, padrões e casos extremos da versão de referência. Validar cada função com dados de referência, métodos documentados e tolerâncias específicas. Relatórios arredondados não bastam para provar equivalência.

Sequência proposta: inventário detalhado; descritivas/distribuições; inferência/regressão; ANOVA/DOE; qualidade/confiabilidade; demais módulos; automação/formatos; validação integrada.

Referências históricas citadas no pacote original: ../minitab_auto_help/ e ../minitab_analysis/minitab_session.txt. Elas não foram encontradas neste pacote. A sessão ainda precisa ser associada aos dados originais antes de servir de referência para testes.


## Descritivas adicionais — 23/10/2026

O diálogo oferece média aparada de 5% por ponta, moda e frequência, assimetria ajustada de Fisher-Pearson, curtose de excesso corrigida e MSSD. As medidas usam a biblioteca padrão; não exigem SciPy. A seleção foi redistribuída em duas colunas.

Contratos atuais do MiniTaBom (casos extremos ainda sem comparação executada com o 16):
- Média aparada: ordena os valores válidos e remove floor(N/20 + 0,5) de cada ponta. Empates de arredondamento sobem; com N < 10 não remove observações.
- Moda: retorna todos os valores empatados na frequência máxima, em ordem crescente, separados por ponto e vírgula no relatório. A frequência é por moda. Sem repetição, moda e frequência aparecem como indefinidas, inclusive N=1.
- Assimetria: N/((N−1)(N−2)) vezes a soma de ((x−média)/s)^3. Indefinida com N<3 ou desvio zero.
- Curtose: N(N+1)/((N−1)(N−2)(N−3)) vezes a soma de ((x−média)/s)^4, menos 3(N−1)^2/((N−2)(N−3)). Indefinida com N<4 ou desvio zero.
- MSSD: soma dos quadrados das diferenças sucessivas dividida por 2(N−1), preservando a ordem dos valores válidos. Os ausentes são removidos antes das diferenças: 1,*,4,2 resulta em 3,25. Indefinido com N=1. A regra de ausentes ainda precisa ser confrontada com a referência.

Documentação complementar consultada em 23/10/2026: [fórmulas Minitab](https://support.minitab.com/en-us/minitab/help-and-how-to/statistics/basic-statistics/how-to/store-descriptive-statistics/methods-and-formulas/methods-and-formulas/), [moda e interpretações](https://support.minitab.com/en-us/minitab/help-and-how-to/statistics/basic-statistics/how-to/display-descriptive-statistics/interpret-the-results/all-statistics-and-graphs/), [assimetria ajustada](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.skew.html) e [curtose corrigida](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.kurtosis.html). As fontes são atuais, sem comprovação de paridade com Minitab 16. Testes analíticos cobrem momentos, arredondamento, empates, casos pequenos, invariância e ordem; o teste Tk submete todas as medidas pelo diálogo. Não foi realizada inspeção visual nesta etapa.


## Prioridade Minitab 16 e novos formatos t — 03/11/2026

O escopo solicitado continua sendo **todos os recursos do Minitab 16.2.4.0**, incluindo dados, análises, gráficos, DOE, qualidade, confiabilidade, séries, multivariada, poder, macros e relatórios. Recursos exclusivos de versões posteriores ficam depois desse alvo. A ordem interna de implementação segue as dependências: fundamentos e fluxos iniciados primeiro, demais áreas depois, sem exclusões.

A fila reproduzível está em `docs/analise_instalacao/cobertura_minitab16.json`. Execute `python -B tools/build_minitab16_coverage.py` após mudar o inventário funcional. Ela decompõe o mapa atual em 247 requisitos de trabalho de 23 áreas (88 capacidades parciais para auditar e 159 pendências), separando os 612 recursos locais do 22 que ainda exigem triagem histórica. **Essas contagens não são quantidade de funções do 16 nem porcentagem de completude.** Presença histórica e paridade numérica permanecem verificações separadas. O inventário completo por comando/opção ainda não foi concluído.

A inspeção estática foi repetida na instalação 22.6: 209 arquivos, 612 recursos de tradução, 183 blocos legados e 24 recursos gráficos. Somente leitura dos arquivos instalados; nenhuma execução diferencial nova foi feita. Foi localizado o [PDF Meet Minitab, Release 16.1.0, do fabricante e hospedado na UPC](https://eio.upc.edu/ca/qui-som/laboratori-de-calcul/manuals-del-sistema/EN16_MeetMinitab.pdf), com 122 páginas. Identificação e sumário foram conferidos como texto; ainda falta auditoria integral dos comandos/opções. O manual não substitui as alterações da versão 16.2.4.

Em **Estat > Estatísticas básicas > Teste t**, a aba Dados agora oferece:
- Uma amostra: coluna ou N/média/desvio padrão amostral resumidos.
- Duas amostras: colunas separadas, resumos de cada amostra ou resposta/grupo.
- Pareado: colunas pareadas ou N/média/desvio das **diferenças**. Resumos independentes dos dois lados não determinam o desvio das diferenças.

Resumos exigem N inteiro entre 2 e 2.147.483.647, média finita e desvio amostral finito não negativo. Não se geram dados artificiais para efetuar os cálculos. O erro padrão deve ser positivo; uma amostra constante pode participar do teste de duas amostras quando o erro combinado é positivo. Com resumos, o relatório informa que os ausentes não foram fornecidos; não afirma ausência de exclusões. As opções de hipóteses, confiança, Welch/variâncias iguais e GL truncado/fracionário são compartilhadas com os dados brutos.

Em dados empilhados, são necessários exatamente dois grupos; os níveis são textos aparados na ordem de primeira aparição. Grupo ausente exclui a linha antes de ler a resposta. Ausentes na resposta são omitidos dentro de cada grupo. O relatório explicita os nomes e a ordem da diferença. Essa ordem e os demais casos extremos continuam pendentes de comparação com a versão 16.

Abra `exemplo_formatos_t.statlab` para comparar os formatos. É exemplo sintético, com A: N=3, média=2, desvio=2; B: N=3, média=3, desvio=2. O pareado por resumo tem instruções separadas. Fontes complementares atuais: [uma amostra](https://support.minitab.com/en-us/minitab/help-and-how-to/statistics/basic-statistics/how-to/1-sample-t/perform-the-analysis/enter-your-data/), [duas amostras](https://support.minitab.com/en-us/minitab/help-and-how-to/statistics/basic-statistics/how-to/2-sample-t/perform-the-analysis/enter-your-data/) e [pareado](https://support.minitab.com/en-us/minitab/help-and-how-to/statistics/basic-statistics/how-to/paired-t/perform-the-analysis/enter-your-data/). Elas descrevem as entradas atuais; não comprovam isoladamente todos os padrões do 16.

Validação desta etapa: **201 testes aprovados**, incluindo 10 novos testes de núcleo/interface; **15 exemplos** conferidos. Casos analíticos, equivalência de formatos, alternativas, hipóteses não nulas, políticas de GL, N grande, desvios zero, grupos/ausentes e falhas sem saída parcial foram exercitados. Interface testada com Tk oculto; não houve inspeção visual nativa nesta etapa.

Quando o exercício da prova for fornecido, cada questão será associada ao método, às opções e ao caminho de menu do Minitab 16 e à capacidade efetiva do MiniTaBom. Ainda não foi feita avaliação de questões específicas.


## Nome do projeto — 03/11/2026

O projeto passou a se chamar **MiniTaBom**, sem acento. O formato e a extensão `.statlab` dos projetos existentes continuam compatíveis.


## Gerar o pacote portátil

Para quem desenvolve: execute `desenvolvimento/gerar_executavel.bat` no Windows x64 com Python x64. A primeira etapa precisa de internet e instala as ferramentas de construção em `.build-tools`. O script `tools/build_windows.py` empacota o aplicativo e suas dependências com PyInstaller, acrescenta os 15 exemplos e avisos de licenças, e testa o executável gerado antes de disponibilizar o ZIP.

Saídas: `dist/MiniTaBom-Windows-x64.zip`, checksum `.zip.sha256` e `dist/smoke-test.json`. Os arquivos intermediários ficam em `.build`; `.build-tools`, `.build` e `dist` são ignorados pelo Git. O pacote não inclui arquivos da instalação Minitab nem exige acesso a ela. A identificação de versão/dependências fica em `versao.json` dentro do pacote.

A verificação do pacote roda o executável com sua interface oculta, sem PYTHONPATH/PYTHONHOME do ambiente de desenvolvimento. Confere Tk/ícones, o JSON de cobertura, um teste t com probabilidade analítica, a distribuição utilizada nas comparações e uma regressão NumPy/SciPy. Esse teste local não substitui uma conferência em outro computador Windows.

### GitHub Actions

Publique **o conteúdo desta pasta como raiz do repositório**, incluindo `.github/workflows/windows.yml`. Em Actions > Pacote Windows > Run workflow, o GitHub instala as dependências, executa a suíte e gera o pacote no Windows. Tags iniciadas em `v` também disparam a construção. Baixe o artefato da execução; ele contém o ZIP portátil, checksum e relatório. Nas Releases do GitHub, anexe o arquivo **MiniTaBom-Windows-x64.zip** para que as outras pessoas encontrem o download. O fluxo não publica uma Release automaticamente.

Para reproduzir em um ambiente de construção já preparado: `python -m pip install -r requirements-build.txt`, seguido de `python tools/build_windows.py`. O empacotamento usa PyInstaller 6.22.3; fórmulas e testes estatísticos são os mesmos da versão em código-fonte.

Pacote gerado em 03/11/2026: aproximadamente 81 MB, com 15 exemplos. O teste do executável congelado foi aprovado neste computador, e os 201 testes da versão em código-fonte passaram. A integridade CRC do ZIP foi conferida; a validação em um segundo computador permanece pendente.


## Verificar atualizações

Abra **Ajuda > Verificar atualizações…**. A janela informa a versão instalada e tem os botões **Verificar** e **Abrir página da versão**. A consulta só ocorre ao clicar em Verificar, sem interromper o uso da interface. Ela compara a versão instalada com a última Release estável pública do repositório. O aplicativo informa uma versão nova, confirma que já está atualizado em relação à Release publicada ou explica falhas de rede/repositório/limite de consultas.

Se o endereço ainda não estiver preenchido, informe `usuario/repositorio` ou `https://github.com/usuario/repositorio`. O endereço é salvo no perfil do usuário, em `%APPDATA%/MiniTaBom/updates.json`, sem alterar projetos de estudo. Em máquinas sem APPDATA, usa `~/.config/MiniTaBom/updates.json`. O link da versão só abre no navegador quando você clicar no botão correspondente. Esta etapa não baixa, instala ou substitui arquivos do aplicativo.

### Preparar suas Releases

A identificação inicial do aplicativo é **0.1.0**, em `app_metadata.json`. Nesse arquivo, `repository` pode receber o endereço real do seu repositório antes da geração local do ZIP. No GitHub Actions, o endereço do repositório é preenchido automaticamente no pacote; quando a construção parte de uma tag, a versão também vem dessa tag. Use tags como `v0.1.0`, `v0.2.0` e `v1.0.0`; uma versão maior é comparada numericamente (por exemplo, 0.10.0 é maior que 0.9.0).

Ao gerar localmente uma atualização, aumente `version` em `app_metadata.json` antes de executar `desenvolvimento/gerar_executavel.bat`. Publique a Release estável com a tag correspondente e anexe o novo ZIP. Apenas subir alterações no código ou criar uma tag sem Release não disponibiliza uma atualização para esse botão. Repositórios privados não são suportados pela consulta sem autenticação.

A consulta usa a [API oficial de Releases do GitHub](https://docs.github.com/en/rest/releases/releases#get-the-latest-release). Os testes simulam as respostas do serviço para verificar versões, erros e interface sem depender da rede. Enquanto o repositório do projeto não for criado e a primeira Release publicada, não há consulta real de ponta a ponta contra ele.
