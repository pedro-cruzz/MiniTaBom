# MiniTaBom — relatório técnico de investigação e continuidade

## Atualização de continuidade — 03/11/2026

Esta seção atualiza o estado do pacote; o relato original abaixo é histórico.

### Vigésima etapa — 03/11/2026: verificação manual de atualizações

- Adicionados updates.py, update_dialog.py e app_metadata.json (versão inicial 0.1.0). Ajuda > Verificar atualizações abre diálogo com versão instalada, repositório, botão de consulta e link para a Release. Rede executada em thread; retorno à interface via fila/after, sem acessar Tk no worker. Fechar cancela o callback; respostas tardias não acessam a janela destruída.
- Consulta manual da API oficial GitHub releases/latest com timeout de 10 segundos, limite de resposta, comparação semântica de versões e mensagens de erro. Endereço limitado ao GitHub; link da Release construído a partir do repositório/tag, sem aceitar URLs arbitrárias do JSON. Sem token, consulta automática na inicialização, download ou instalação automática.
- Usuário informou que ainda está criando o repositório. Campo aceita link ou usuario/repositorio e salva a preferência em APPDATA/MiniTaBom/updates.json (fallback ~/.config). Nenhum endereço de repositório foi inventado e não houve consulta de ponta a ponta contra o projeto ainda inexistente.
- Build inclui metadados; GitHub Actions preenche o repositório e a versão da tag no pacote. Construção local lê app_metadata.json. README explica versões/tags e necessidade de Release estável pública com ZIP anexado.
- Verificação: 212 testes aprovados (11 novos), incluindo comparação de versões, igualdade/versão mais antiga, JSON inválido, limite de resposta, 404/403/500/offline/timeout, preferências e fluxo do diálogo. Respostas HTTP simuladas nos testes; não representam consulta real do repositório.

### Décima nona etapa — 03/11/2026: distribuição portátil MiniTaBom

- Nome MiniTaBom aplicado à interface, documentação e classe principal; formato .statlab preservado. Finalidade educativa e independência em relação ao Minitab indicadas no README e na tela Sobre.
- Criados requirements-build.txt, gerar_executavel.bat e tools/build_windows.py. PyInstaller 6.22.3 gera um pacote Windows x64 em pasta, com dependências, inventário, 15 exemplos, instruções e licenças dos pacotes científicos/Python. Nenhum arquivo da instalação Minitab é incorporado.
- Criada .github/workflows/windows.yml: construção manual ou por tags v*, testes e artefato para download. Requer .github na raiz do repositório. Não publica Releases automaticamente; o responsável anexa o ZIP à Release.
- Gerado dist/MiniTaBom-Windows-x64.zip (~81 MB), checksum SHA256 e smoke-test.json. Pastas .build-tools, .build e dist ignoradas pelo Git.
- Verificação: 201 testes aprovados. Executável gerado executado em modo de diagnóstico, com interface oculta e sem PYTHONPATH/PYTHONHOME; aprovados Tk/ícones, inventário, teste t analítico, integração da distribuição de comparações e regressão NumPy/SciPy. CRC do ZIP aprovado. Verificação ocorreu neste computador, não em uma máquina Windows limpa.
- Artefato apenas local: nenhum upload ou publicação no GitHub realizado.

### Décima oitava etapa — 03/11/2026: prioridade integral do 16 e formatos dos testes t

- Instrução atual do usuário: todos os recursos do 16 têm prioridade; exercício de prova será enviado depois para avaliação de disponibilidade e fluxo de estudo. Nenhum conteúdo de prova foi presumido.
- Reaproveitado o estado recente do pacote: 191 testes aprovados antes das alterações. Repetida a inspeção estática local 22.6 (209 arquivos, 612 recursos de tradução, 183 blocos legados e 24 recursos gráficos), sem alterar a instalação nem executar uma análise no Minitab.
- Criada fila reproduzível em analise_instalacao/cobertura_minitab16.json e tools/build_minitab16_coverage.py, com as 23 áreas e 247 requisitos de trabalho do inventário (88 capacidades parciais a auditar e 159 pendências). Recursos do 22 têm triagem separada. Contagens não representam funções distintas, cobertura percentual ou comprovação histórica; todas as áreas do 16 permanecem no escopo.
- Adicionados formatos resumidos aos testes t de uma/duas amostras e pareado (somente resumo das diferenças), e duas amostras t empilhadas. Cálculo compartilhado com a entrada bruta, sem reconstrução artificial de observações. Relatório distingue ausentes desconhecidos e explicita grupos/ordem. N e desvios têm validação; casos extremos não implicam paridade com o 16.
- Fontes atuais de entrada t vinculadas no README. Localizado o PDF do fabricante Meet Minitab 16.1 na UPC; identificação Release 16.1.0/copyright 2010 e sumário foram lidos. Catálogo histórico atualizado; nenhuma confirmação automática de todas as funções do 16 a partir desse manual introdutório.
- Verificação: 201 testes aprovados e 15 exemplos conferidos. Dez testes novos cobrem formatos, resultado analítico Cauchy, alternativas/GL, hipóteses não nulas, grupos/ausentes, N grande, erros atômicos e diálogos Tk ocultos. Exemplo sintético exemplo_formatos_t.statlab adicionado. Não houve comparação executada nova com o 16/22 nem inspeção visual nativa.
- Próximos blocos: auditar funções/opções históricas restantes; completar inferência (igualdade de variâncias/Poisson e opções de normalidade), não paramétricos e fundamentos; prosseguir por todas as áreas da fila. Questões da prova, quando recebidas, orientarão a ordem dentro do escopo integral do 16.

### Décima sétima etapa — 24/10/2026: referências documentais da família 16

- Pesquisa específica da versão 16 a pedido do usuário. Criado analise_instalacao/referencias_minitab16.json com cinco fontes, autoria/hospedagem, versão identificada, localizadores, grau de conferência e limites. Fontes e usos resumidos no README; inventário funcional aponta para o catálogo. Nenhuma alteração de cálculo/interface nesta etapa.
- Manual Meet Minitab identifica Release 16.1.0 e Copyright 2010 no corpo da transcrição consultada; há também espelho no DirectIndustry. Brochura Minitab16 WhatsNew tem seção Features List na página 11. Manual introdutório e novidades não equivalem ao Help completo. Slides Minitab de 2010, hospedados na ADDITIVE, corroboram opções históricas; foram lidos como texto PDF e a tentativa de captura visual falhou por cache miss.
- Histórico ADDITIVE e reprodução textual de ReadMe separam lançamento/16.2 e correções posteriores. Para o alvo 16.2.4.0, não confundir documentação do lançamento 16.1.0 com todas as opções 16.2 nem com a revisão distinta 16.2.4.4. Índices dos portais, datas de espelhos e resumos automáticos não foram tratados como prova do conteúdo original.
- Presença documentada continua separada de implementação e equivalência numérica. Ainda faltam auditoria integral da lista de funções, Help/StatGuide/Session Command Help/Methods and Formulas específicos do 16 e execução diferencial. Os indicadores de inventário exaustivo e paridade permanecem falsos. Não houve download de instalador, mudança na instalação original ou teste executado no Minitab nesta etapa.

### Décima sexta etapa — 24/10/2026: duas proporções, variâncias, contingência e normalidade

- Adicionados extended_inference.py/extended_inference_dialog.py, sample_inputs.py e exact_tables.py. Estat > Estatísticas básicas contém duas proporções, uma e duas variâncias. Diálogos com abas/ícones, entrada resumida ou colunas; duas amostras também aceitam resposta/grupo, na ordem de primeira aparição dos dois grupos. Ausentes de amostras independentes são omitidos separadamente; grupo ausente exclui a linha. Relatórios nomeiam amostras/eventos e entram no navegador de resultados.
- Duas proporções: diferença p1−p2, teste Z separado ou combinado (apenas H0 zero), IC Wald separado, alternativas e intervalo sem teste. Fisher condicional SciPy é adicional para H0 zero, com ordenação por probabilidade no bilateral; empates não têm paridade presumida com Minitab. IC fora da faixa física/degenerado e teste Z com erro zero são informados explicitamente. Resumo permite N até 2.147.483.647 por amostra; Fisher tem limite operacional de 1.000.000 ensaios totais, omitindo só esse cálculo acima do limite.
- Uma/duas variâncias usam qui-quadrado/F para populações normais, com hipóteses, ICs e limites em desvio/variância ou razões correspondentes, conforme opção explícita. N≥2, dispersões/hipótese positivas; constantes e magnitudes não representáveis são recusadas. Bilateral usa duas vezes a menor cauda, limitado a 1. Bonett, Levene, mais grupos, gráficos e comparação com versão alvo permanecem pendentes.
- Adicionados contingency.py/contingency_dialog.py em Estat > Tabelas. Categorias com frequência opcional ou matriz de contagens com rótulos; Pearson e razão de verossimilhanças sem Yates, esperadas, resíduos brutos/padronizados/ajustados, contribuições e percentuais. Frequência zero não introduz categorias; matriz com ausência parcial é recusada, ausência total na linha é omitida. Limites: 50×50 categorias e total até 2⁵³−1; margens zero recusadas. Esperada <1 suprime valores-p assintóticos; <5 é identificado. Fisher adicional 2×2 segue o mesmo limite/convenção acima. Razão de verossimilhanças usa termos equivalentes estáveis próximos da independência e trata O=0.
- Adicionados normality.py/normality_dialog.py: Anderson-Darling com média/desvio amostral, logCDF/logSF, correção A²(1+0,75/N+2,25/N²) e valor-p aproximado das equações documentadas. A² ajustado >13 é apresentado como limite de valor-p. Aceita 3 a 200.000 números, omite vazio/*, recusa constantes/não finitos, identifica repetições e informa pouco poder com N<20. Sem gráfico, Ryan-Joiner/KS ou múltiplas respostas nesta etapa. Não usa statsmodels como dependência; documentação confirmou a correção.
- Verificação: 191 testes aprovados na suíte completa, incluindo 27 novos. Casos independentes por combinações hipergeométricas, CDFs fechadas X²(2)/F(2,2)/qui-quadrado GL2, caudas, reciprocidade, contagens grandes, ausência/grupos, conversões de medidas, extremos/constantes e erros atômicos. A² também comparado com SciPy. Diálogos exercitados em Tk oculto; não houve inspeção visual nativa nem comparação executada desses novos comandos no Minitab 16/22.
- Exemplos sintéticos: exemplo_proporcoes_variancias.statlab, exemplo_contingencia.statlab e exemplo_normalidade.statlab. tools/check_study_examples.py validou os 14 exemplos e conferiu os resultados demonstrados pelos novos dados (incluindo equivalência colunas/empilhadas e categorias/matriz), além dos inventários JSON. README e inventários atuais descrevem fórmulas/pressupostos, limites e pendências. As fontes oficiais atuais estão vinculadas no README; não comprovam padrões da versão 16. Paridade e inventário exaustivo continuam falsos.

### Décima quinta etapa — 24/10/2026: operações de dados e posicionamento

- Dados > Ordenar linhas: até três chaves, direção/tipo por chave, comparações numéricas com Decimal, texto por Unicode com opção casefold, ausência no início/final independente da direção e estabilidade nos empates. Ordena linhas completas, preservando os textos e a relação entre colunas. Automático só usa números quando todos os valores não ausentes da chave são decimais finitos. Sem alteração efetiva não cria entrada no histórico.
- Empilhar colunas adiciona valores e origem, preservando fontes, com omissão opcional de vazios/*. Desempilhar por grupo adiciona uma coluna por categoria, preservando ordem de aparição, ordem interna e textos de célula. Oferece políticas separadas para valores e grupos ausentes; nomes distinguem grupo ausente de rótulos literais e evitam colisões com sufixos. Os comprimentos das fontes seguem o retângulo da tabela atual, sem comprimentos independentes por coluna.
- Transformações constroem e validam o resultado antes de atribuir a nova tabela. Acrescentar colunas preserva fontes e preenche a área adicional com vazios. Limites de saída do empilhar/desempilhar: 200.000 linhas, 512 colunas e 2.000.000 células. Uma transformação constitui uma entrada no histórico; desfazer/refazer e invalidação do modelo de regressão são integrados. A nota da operação permanece na sessão após desfazer.
- Verificação do bloco: 157 testes aprovados na suíte completa. Casos novos incluem inteiros acima de 2⁵³, múltiplas chaves/direções, estabilidade, posição de ausentes, manutenção de linhas completas, preservação de textos, fontes e categorias, colisões, ida e volta empilhar/desempilhar, limites e erros sem alteração parcial, diálogos e uma etapa de desfazer/refazer.
- Na inspeção nativa dos gráficos, menus/abas e o desenho da série foram conferidos. Foi observado deslocamento da janela de gráfico para (7,0). A instrumentação de desenvolvimento registrou centro calculado (368,386) e geometria solicitada correspondente, apesar da posição capturada posteriormente. O ajuste atual usa tamanho inicial explícito dos gráficos, área útil do monitor da janela principal e reaplicação após 80 ms, com cancelamento ao destruir a janela. O cálculo de monitores à direita/esquerda e o ciclo de cancelamento têm testes; a última reaplicação ainda precisa de nova conferência nativa. Não confundir aprovação dos testes com confirmação visual dessa última alteração.
- APIs de leitura da área útil: MonitorFromWindow e GetMonitorInfoW, sem alteração de configurações do sistema. Fontes oficiais: https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-monitorfromwindow e https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getmonitorinfow . O fallback conserva o centro relativo à janela principal. tools/preview_geometry_probe.py é uma prévia manual de desenvolvimento, sem automação de entradas; grava somente medidas em diagnosticos/geometry_probe.json quando executada explicitamente.
- Verificação final, incluindo ajuste de posicionamento, marcas inteiras no eixo de séries e guardas numéricas da proporção: 164 testes aprovados. Criados exemplos exemplo_z_proporcao.statlab, exemplo_graficos_xy.statlab e exemplo_operacoes_dados.statlab; os 11 exemplos do projeto foram abertos pelo validador sem erros. README, inventário funcional e mapa de lacunas atualizados. Os novos blocos não têm comparação executada com Minitab 16/22; a instalação original não estava aberta nesta conferência. A execução diferencial registrada continua sendo o caso Welch anterior.

### Décima quarta etapa — 24/10/2026: dispersão, séries e exportação vetorial

- Adicionados xy_graphs.py e xy_graph_dialog.py, com comandos independentes no menu Gráfico e ícones. Aceitam X/Y numéricos (dispersão) ou Y na ordem original das linhas (séries) e grupo opcional. A dispersão pode conectar pontos, sempre na ordem da planilha, sem agregação ou ordenação implícita por X.
- Abas Variáveis e Escalas e títulos. Escalas linear/log₁₀, títulos personalizados, identificação de N/omissões e detalhes por ponto sob o cursor. Pares incompletos e grupos ausentes são omitidos. Conexões interrompem o respectivo grupo em X/Y ausente e todos os grupos iniciados em grupo ausente; conectar através de ausentes é uma opção explícita. Grupos intercalados se conectam na sequência própria.
- Canvas e exportador SVG compartilham uma cena vetorial. SVG independente preserva textos, cores, linhas e títulos dos pontos; XML é escapado. Gráfico guarda cópia dos dados e não entra no .statlab. Limites: 20.000 pontos e 20 grupos. Faltam calendário/frequência, várias respostas, painéis, agregação, estilos completos e formatos raster/PDF.
- Suíte completa ao fechar esse bloco: 144 testes aprovados. Verificados pares/grupos/linhas, lacunas e conexões, ordem sem agregação, escala logarítmica, coordenadas finitas com extremos/constantes/subnormais, XML/acentos/caracteres especiais, rejeições, diálogos, snapshot e exportação pela janela. A conferência nativa posterior verificou os ícones do menu, ambas as abas e o desenho de uma série de 10 observações sintéticas.

### Décima terceira etapa — 24/10/2026: Z e uma proporção

- Estat > Estatísticas básicas oferece Teste Z de uma amostra e Teste de uma proporção, com abas e ícones, coluna ou resumo, confiança, alternativas e opção de intervalo sem teste. Novos relatórios são indexados no navegador e preservados como texto no projeto.
- Z usa sigma populacional conhecido positivo, N≥2 e distribuição normal para teste/intervalos. Resumo aceita N/média/sigma; coluna omite ausentes. Números finitos e limites de precisão são verificados; dados constantes são permitidos com sigma informado.
- Proporção recebe eventos/ensaios inteiros ou coluna com até duas categorias aparadas. Evento é texto exato com distinção de maiúsculas; uma categoria observada permite zero eventos de outra categoria especificada. Há teste binomial exato por caudas inclusivas e IC Clopper–Pearson, teste score com IC Wilson, ou teste score com IC Wald sem corte em [0;1]. Não há correção de continuidade nem Blaker ajustado. Métodos são explícitos no diálogo/relatório; não presumem os padrões do 16/22. Aproximações normais exigem hipótese estritamente entre 0 e 1 e variância sob H0 representável. Intervalos invertidos por opções extremas são recusados.
- Recursos locais oneSampleZForTheMean.json e oneSampleProportion.json orientaram os campos; fórmulas foram conferidas na documentação atual Minitab/SciPy vinculada no README. O catálogo local tem rótulos e validações, não os algoritmos. Ainda faltam duas proporções, várias colunas, correção, gráficos e armazenamento.
- Suíte completa do bloco: 134 testes aprovados. Casos novos cobrem Z analítico e caudas, intervalos unilaterais, constantes/ausentes, enumeração independente binomial, extremos de eventos, fórmulas fechadas de IC, inversão do teste exato, aninhamento, Wilson contra referência independente, limites Wald, categorias/eventos, contagens/domínio e submissão/erros sem saída parcial. Guardas posteriores de subfluxo e relatórios foram incluídas na verificação final da etapa 15.

### Décima segunda etapa — 23/10/2026: análise estática da instalação original

- Raiz lida: `C:\Program Files\Minitab\Minitab 22`. Versão 22.6.0.0 confirmada por metadados de Mtb.exe e pelo SWID da instalação. Encontrados 209 arquivos, 793.122.481 bytes (aproximadamente 793 MB decimais), 58 DLLs e quatro executáveis. Nenhuma alteração na instalação ou execução de componentes foi necessária para a análise estática.
- Os quatro arquivos `.data` são ZIPs: Dialogs.data (428 arquivos), mss-graphs.data (204), mss-graph-editing.data (4) e minitab-treeviewer.data (6). Contagens excluem diretórios. Contêm HTML, JavaScript e recursos gráficos; não foi feita extração de executáveis ou incorporação desses pacotes ao MiniTaBom.
- No pacote principal de Dialogs.data, o mapa Webpack relaciona 612 recursos `./pt-BR/*.json` a módulos de tradução. Todos os 612 foram localizados e lidos estaticamente, usando somente literais e JSON. O catálogo guarda títulos, chaves, ID de módulo, membro do ZIP e offset em caracteres. Esses recursos incluem opções, galerias, componentes compartilhados e variantes antigas: não correspondem a 612 funções distintas ou confirmadas no menu. Chunks podem incorporar outro aplicativo com mapa próprio; por isso, não se misturam seus IDs com os do pacote principal.
- mss-graphs.data tem 24 recursos JSON pt-BR. Foram identificados nomes de gráficos e chaves para grupos, painéis, escala logarítmica, rótulos, medidas, dados ausentes, datas/horas e outras opções ainda não implementadas. O material ajuda a decompor o contrato de interface; não fornece por si só algoritmos ou valores padrão efetivos.
- Em Resources/1046, o arquivo mtb.inx tem 502 entradas. Os comprimentos observados permitem percorrer 183 blocos de mtb.dlg, cobrindo seus 1.126.120 bytes; seus offsets coincidem com as entradas diretas válidas do índice. Duas entradas brutas, nos slots base zero 399/400, excedem o tamanho de mtb.dlg e foram registradas como não resolvidas. Não se pressupõe que o formato esteja completamente decodificado. As sequências UTF-16LE são amostras heurísticas, sem atribuição garantida a títulos/controles.
- Há exemplos C# MyMenu (56 arquivos .cs distribuídos por oito pastas de idioma), com formulários e uso de Mtb.Application/IMinitabAddin. Demonstram acesso a worksheets/colunas, GetData/SetData, ExecuteCommand e montagem de DESCRIBE com subcomandos. Isso é código de exemplo de um complemento, não o fonte completo de Mtb.exe/MtbCore.dll. As 16 macros instaladas correspondem a Userfunc.mac e Simproc.mac distribuídas pelos oito idiomas.
- Não foram encontrados MTW/MPJ/MWX/MPX nem manuais PDF/CHM dentro desta raiz. A constatação não abrange pastas de exemplos/documentos externas à instalação.
- Artefatos: `analise_instalacao/inventario_instalacao.json`, `dialogos_pt_br.json`, `dialogos_legados_pt_br.json`, `graficos_pt_br.json` e `lacunas_priorizadas.json`. O último cruza recursos encontrados com as lacunas do MiniTaBom, mantendo prioridade para inferência básica, operações de dados e gráficos independentes. O inventário funcional permanece parcial e sem paridade validada.
- Reprodução: `python -X utf8 -B tools/inspect_minitab_installation.py`. O script lê a instalação, registra hashes dos pacotes/binários selecionados e só grava relatórios dentro deste projeto. Não carrega DLLs nem executa JavaScript, macros ou exemplos C#. A inspeção concluiu com 612/612 recursos de tradução lidos; as referências de recursos do mapa de lacunas foram verificadas contra esse catálogo. O código do aplicativo não foi alterado nesta etapa; sua última suíte completa teve 121 testes aprovados.

### Décima primeira etapa — 23/10/2026: previsão, distribuições e ícones

- Previsão linear reutiliza a base escalada/SVD do último ajuste, com casos digitados (TSV/ponto e vírgula) ou colunas mapeadas. Mostra EP da média, IC da média e IP de uma observação, com confiança e limites bilaterais/unilaterais. Números originais das linhas e omissões preservados. Valores além das faixas marginais ou com alavancagem acima do treino são sinalizados, sem alegar checagem completa do domínio multivariado.
- O modelo em memória é invalidado por mudanças na planilha/refresh, incluindo undo/redo, importação, novo e abertura. O menu Prever novos casos fica desabilitado até novo ajuste. O .statlab continua guardando texto, sem persistência do objeto de regressão. Adicionado exemplo_previsao.statlab com casos analíticos X=2 e X=5.
- Calc > Distribuições de probabilidade: 12 famílias com PDF/PMF, CDF, SF, intervalo inclusivo e PPF/ISF. Parâmetros e semântica discreta explicitados no README. Probabilidades de cauda e intervalos superiores evitam calcular 1−CDF quando possível. Sem geração aleatória, gráficos ou armazenamento em colunas.
- Ícones próprios em icons.py, feitos com PhotoImage e operações de pixel da biblioteca padrão, aplicados a comandos de menus, toolbar e abas. Referência visual enviada pelo usuário. Corrigida a decoração para ignorar a entrada tearoff especial de menus Tk. Mantidos comandos e estados de habilitação. Não foram adicionados itens vazios para famílias ainda não implementadas.
- Suíte completa com 121 testes aprovados. Inclui previsões analíticas simples/múltiplas, reprodução de valores ajustados/alavancagens, limites unilaterais, variação de confiança, parsing/ausentes, erro nulo, invalidação do modelo e relatórios; 12 distribuições com casos fechados, relações entre famílias, quantis, caudas extremas e domínio; comandos dos menus e ícones.
- Inspeção no Windows da toolbar com ícones, menu Gráfico com ícones e calculador de distribuições; executada Normal(0,1), P(X≤0)=0,5. Primeira captura do menu retornou unknown screenshotId; atualizada a referência da janela e a captura, a conferência foi concluída. Previsão foi conferida por integração Tk sem captura separada nesta etapa. Fontes oficiais atuais Minitab/SciPy vinculadas no README; paridade com o 16 continua pendente.
- Tentativa posterior de retomar a comparação no Minitab instalado: localizada a janela Minitab - Sem título e lidos os menus/atalhos pela acessibilidade. A captura após ativação falhou com `encode latest capture frame failed: window crop is outside captured monitor`; a leitura sem imagem funcionou, mas a tentativa de abrir Linha de Comando/Histórico retornou `window bounds changed; call get_window_state before using this window`. Não houve nova execução de regressão nem registro de novos valores do original. A conferência diferencial executada permanece o caso Welch em fixtures/welch_minitab_22_6/observed.json. A suíte foi novamente executada: 121 testes aprovados.


### Décima etapa — 23/10/2026: correlação e regressão linear

- Adicionados linear_models.py, linear_dialog.py e regression_graph.py. Menus Estat > Estatísticas básicas > Correlação e Estat > Regressão > Ajustar modelo linear, com abas Dados / Opções e resultados e indexação dos relatórios no gerenciador do projeto.
- Correlação Pearson/Spearman em várias colunas, exclusão por par ou por linha completa, N e teste t bilateral contra correlação zero. Spearman usa postos médios. IC de Fisher para Pearson com N>3; IC de Spearman continua pendente, com campo desabilitado. Pares com N<3 ou constantes são relatados como indefinidos. Valores-p não têm ajuste de multiplicidade.
- Exemplo numérico arredondado de Spearman da documentação oficial atual registrado em fixtures/spearman_documentation/observed.json, com fonte e tolerâncias de 0,0005 para r/p. Isso não é execução nem validação da versão 16.
- Regressão simples/múltipla com intercepto e preditores numéricos. Cálculo por SVD após escala/centralização; coeficientes e matriz de covariância voltam à escala original. Inclui ICs/testes t, VIF, ANOVA global, S, R²/ajustado/predito, PRESS, ajustados/resíduos, resíduos padronizados internos, alavancagens e Cook.
- R² ajustado/predito negativos limitados a zero conforme documentação atual. Preditores constantes e matrizes com condicionamento escalado >10¹⁰ são recusados. Erro residual nulo na tolerância descrita no README deixa t/F e resíduos padronizados indefinidos. Alavancagem próxima de 1 torna PRESS e diagnósticos associados indefinidos. Esses casos extremos requerem execução na versão alvo.
- Quatro gráficos redimensionáveis com cópia dos resultados: reta ou observados × ajustados, resíduos × ajustados, Q–Q normal e resíduos × linha original. Quantis normais pré-calculados. Sem exportação/persistência gráfica.
- Exemplos adicionados: exemplo_regressao_simples.statlab (intercepto=0,6; inclinação=0,9; SQ Erro=3,1; F=243/31) e exemplo_regressao_multipla.statlab (coeficientes 2/3/−2; SQ Erro=1; F=26; VIF=1; PRESS=16). Documentação e inventário atualizados, mantendo paridade_validada=false.
- Verificação: suíte completa com 101 testes aprovados. Casos novos cobrem Pearson ortogonal/Fisher, Spearman com empates/referência documental, exclusão por par/linha e ordem, entradas inválidas, regressão simples e múltipla analíticas, scipy.stats.linregress, invariância, ICs, PRESS por reajustes leave-one-out, ajustes perfeitos, resposta constante, alavancagem unitária, condicionamento, relatórios, submissão dos diálogos e snapshots/desenho dos gráficos.
- Inspeção no Windows: aberto o exemplo simples, conferidos menu e ambas as abas do diálogo, executado o modelo e visualizados os quatro gráficos. Um índice de acessibilidade do seletor de arquivos retornou indisponível; o estado foi atualizado e a abertura concluída pelo campo Nome observado. A correlação foi conferida por testes de integração Tk, sem captura visual separada nesta etapa. A prévia ficou aberta com os resultados, sem salvar sobre o exemplo original.
- Pendências: IC de Spearman, matriz/armazenamento de correlação; predição, categorias/interações, seleção de variáveis, falta de ajuste, pesos, demais diagnósticos/modelos e validação diferencial integral no Minitab 16.

### Nona etapa — 23/10/2026: interação da planilha e descritivas por grupo

- Planilha: seleção retangular por arraste, Shift+clique e Shift+setas; seleção de linhas/colunas pelos cabeçalhos; Ctrl+A, Ctrl+Home e Ctrl+End. Ctrl+C copia a seleção em TSV com aspas para preservar conteúdo com tabulação/quebras de linha. A colagem começa no canto superior esquerdo da seleção e mantém a validação integral do bloco antes de modificar dados.
- Delete limpa as células selecionadas sem remover linhas/colunas; a ação inteira é desfeita em uma etapa. Linhas virtuais não são materializadas pela seleção ou limpeza vazia. Menu Editar oferece cópia, colagem, limpeza e seleção dos dados.
- Largura individual de coluna por arraste e ajuste ao conteúdo por duplo clique na separação do cabeçalho. Limites atuais de 60–600 pixels lógicos. Larguras são apenas preferências temporárias de visualização; não alteram observações, estado salvo ou formato do projeto. SheetGrid usa limites acumulados e busca binária para manter rolagem, identificação e editor alinhados.
- Descritivas: agrupamento por uma ou mais variáveis, várias respostas com exclusão independente por resposta, contagens por grupo e relatório sem escrita parcial em caso de erro. Grupos são textos aparados, em ordem de aparição. Vazio/asterisco são níveis ausentes, excluídos por padrão e incluídos opcionalmente como um nível próprio.
- Combinações vazias opcionais para múltiplos grupos: produto dos níveis observados nas linhas incluídas, limitado a 10.000 grupos. Grupos com respostas só ausentes mostram N=0 e contagens; demais medidas ficam indefinidas. Combinações sem linhas mostram as três contagens iguais a zero. Essas convenções ainda não foram executadas contra o Minitab 16.
- Novo descriptive_dialog.py com abas Dados e grupos / Estatísticas. Referências complementares oficiais atuais de Display e Store Descriptive Statistics estão no README. As opções de Store servem como referência de agrupamento; armazenamento em novas colunas não foi implementado.
- Adicionado exemplo_descritivas_grupos.statlab com duas respostas, dois grupos, ausentes, instruções e resultados analíticos. Mantidas as ampliações anteriores das descritivas (oitava etapa).
- Verificação: 80 testes aprovados. Novos casos cobrem TSV com aspas/quebras, seleção reversa e por arraste, limpeza/desfazer de bloco, largura/coordenadas, agrupamentos cruzados, respostas com ausentes independentes, grupos vazios, rótulo literal distinto de ausente, ordem/MSSD, erros com linha original, limite de combinações, submissão do diálogo e ausência de saída parcial.
- Inspeção visual no Windows: seleção C1:C2 em quatro linhas, arraste da largura de C1, ambas as abas e execução de Medição por Grupo com os dados fictícios iniciais. Observados N=10 e média=13 no grupo A. A prévia ficou aberta com o resultado, sem salvar sobre arquivos existentes. Não houve inspeção adicional do Minitab original nesta etapa.
- Pendências próximas: percentuais/contagens acumuladas, armazenamento e resumo gráfico; correlação/regressão; propriedades e tipos de coluna, persistência de preferências e gerenciamento de múltiplas planilhas. A lista de 23 áreas continua parcial, sem percentual de completude nem paridade validada.

### Oitava etapa — 23/10/2026: descritivas adicionais

- Retomado o pacote local com a suíte anterior aprovada (58 testes). Adicionadas média aparada de 5% por ponta, todas as modas repetidas e frequência por moda, assimetria ajustada, curtose de excesso corrigida e MSSD com fator 1/2.
- Convenções explicitadas no README: poda com arredondamento de meios para cima; ausência de moda quando não há repetição; momentos indefinidos com N insuficiente ou desvio zero; MSSD sobre sequência de válidos após remover ausentes. São decisões ainda pendentes de comparação com a versão 16.
- Fórmulas de momentos implementadas com valores padronizados. Nenhuma dependência adicional. Relatório suporta várias modas e o diálogo mantém duas colunas de opções.
- Fontes atuais oficiais Minitab e SciPy vinculadas no README. Não houve execução no Minitab nesta etapa nem comparação visual. Inventário atualizado preservando a ausência de paridade validada.
- Verificação: 64 testes aprovados, incluindo cinco casos novos de núcleo e um fluxo Tk real que seleciona todas as medidas e submete o diálogo. Cobertura: resultados analíticos, limites de arredondamento, empates, constantes, amostras pequenas, invariância e ordem do MSSD.
- Próximos passos: agrupamentos, percentuais/contagens acumuladas e armazenamento; validação diferencial dos contratos, especialmente moda e MSSD com ausentes.

### Sétima etapa — 23/10/2026: revisão da interface clássica

- Substituída a Treeview da planilha por SheetGrid em sheet_grid.py, um Canvas com grade contínua, células brancas, números de linha, cabeçalhos fixos em duas faixas (C1/C2 e nomes) e destaque da célula ativa. Desenho limitado ao trecho visível; os dados permanecem nas mesmas listas usadas pelos cálculos e projetos.
- Preservados edição por Entry, Enter/Tab/Esc, colagem tabulada validada, salvamento de edição pendente e histórico. Rolagem com roda e Shift+roda; a navegação revela a célula selecionada também horizontalmente. Colunas adicionais continuam sendo criadas explicitamente por + Coluna.
- Tema nativo vista no Windows com alternativa clam; barras mais compactas, títulos de sessão/planilha com indicação do foco, fonte monoespaçada na sessão e gerenciador de projeto recolhível, inicialmente oculto. Removido o painel permanente de instruções. Ctrl+M e Ctrl+D mudam o foco entre sessão e dados.
- Referências documentais consultadas: guia Minitab 16 da NYU e instruções de laboratório da UQ, com links no README. A fonte oficial antiga EN16_MeetMinitab.pdf retornou 404; a captura do PDF da NYU também falhou. Não foi realizada comparação de pixels com uma instalação da versão 16. A aproximação segue a disposição documentada, não comprova reprodução exata.
- Conferência visual no Windows: grade, cabeçalhos, seleção, editor dentro da célula e abertura do gerenciador. Identificado e corrigido o destaque de foco que confundia os caminhos Tk de frames irmãos; a correção possui teste específico.
- Verificação: 58 testes aprovados, incluindo edição/navegação em 5.000 linhas e 50 colunas com desenho limitado à área visível, preservação do navegador ao ocultá-lo e foco das áreas. A suíte anterior de cálculos, projetos e diálogos segue aprovada. Janelas internas livres, redimensionamento individual de colunas, seleção de intervalos e equivalência visual completa permanecem pendentes.

### Sexta etapa — 23/10/2026: ANOVA de um fator e grupos

- Adicionados anova.py e group_dialog.py: ANOVA clássica e Welch, com grupos em colunas separadas ou resposta/fator. A tabela clássica apresenta GL/SQ/QM, F, p, S e R². Os ICs individuais usam erro combinado no modelo clássico e EP/GL próprios em Welch.
- Comparações múltiplas opcionais: Tukey-Kramer no modelo clássico e Games-Howell sem assumir variâncias iguais, com p ajustado e intervalos simultâneos. Probabilidades F/t e comparações vêm do SciPy. Fontes complementares atuais constam no README; as opções não foram reexecutadas no Minitab 16.
- GroupSelector compartilhado entre análise e gráfico, com Ctrl/Shift, selecionar todas e limpar seleção, além de campos de resposta/fator. Fatores são textos aparados, na ordem de primeira aparição; não há inferência automática de tipo numérico/data.
- Boxplots comparativos em escala comum, N por grupo, cores distintas e rolagem para muitos grupos. Dados copiados na criação; exportação/persistência gráfica seguem pendentes. Janelas gráficas agora são transitórias da janela principal.
- Menus Estat > ANOVA > Um fator e Gráfico > Boxplots comparativos. Resultados entram na sessão e no navegador de análises. Abas receberam ajuste de cores.
- Exemplos sintéticos adicionados: exemplo_anova.statlab e exemplo_anova_empilhada.statlab. Ambos representam o caso analítico com SQ Fator=54, SQ Erro=6, F=27, p=0,001, S=1 e R²=90%. Não são exportações do Minitab.
- Validação: 55 testes aprovados. Incluem caso F(2,6) com probabilidade analítica, relação F=t² em dois grupos, modelos desbalanceados contra scipy.stats.f_oneway, invariância a escala/translação/ordem, equivalência dos dois formatos de dados, comparações múltiplas, casos inválidos, submissão do diálogo e isolamento dos dados no gráfico.
- Conferência visual no Windows do carregamento do exemplo, seleção dos três grupos, aba de opções e relatório com Tukey. A captura isolada do gráfico comparativo não foi concluída: o controle retornou `user input was detected in this window; call get_window_state before continuing` e, após atualização, `window is minimized; call activate_window, refresh with get_window, then retry get_window_state`; a recuperação voltou a detectar interação. A automação foi interrompida, preservando as janelas. O desenho do gráfico foi verificado com Canvas nos testes.
- Pendências: grupos com uma observação, casos com erro nulo e variâncias zero em Welch conforme o original; modelos de vários fatores/efeitos; Fisher/Dunnett/Hsu, letras de agrupamento, resíduos e diagnósticos; armazenamento e validação diferencial na versão 16. INVENTARIO_FUNCIONAL.json atualizado sem marcar paridade integral.

### Quinta etapa: testes t, interface e primeira referência executada

- Implementados testes t de uma amostra, pareado e duas amostras (Welch e variâncias iguais), com hipóteses bilateral e unilaterais, confiança configurável, valor nulo configurável e opção de exibir só estimativa/intervalo.
- Distribuição t, probabilidades e quantis calculados por SciPy. Adicionados requirements.txt e instalar_dependencias.bat para dependências locais em .deps. Ambiente testado: Python 3.14.2, SciPy 1.18.1 e NumPy 2.5.4. A instalação inicialmente gerou diretórios sem herança de permissões; a herança foi habilitada somente em .deps, após aprovação, e a importação passou a funcionar no ambiente restrito.
- No pareado, exclusão por linha preserva os pares. Duas amostras usam exclusão independente por coluna. Erro padrão zero é recusado; equivalência desse tratamento com a versão 16 permanece pendente.
- Diferença documental identificada: Minitab desktop anterior a 22.6 trunca graus de liberdade de Welch; 22.6 usa GL fracionário. O MiniTaBom usa truncamento por padrão e permite desmarcá-lo. Corrigidos resíduos de arredondamento (até 64 ULPs) muito próximos de GL inteiros para evitar perder um grau indevidamente. Referência: https://support.minitab.com/en-us/minitab/help-and-how-to/statistics/basic-statistics/how-to/2-sample-t/methods-and-formulas/methods-and-formulas/ . O comportamento do 16 foi documentado, ainda não confirmado por execução na versão 16.
- Minitab 22.6 inspecionado diretamente: criada Worksheet 2 separada para dados sintéticos, sem substituir a Worksheet 1 preexistente. Dados C1=[2,4,5,9,15,*], C2=[1,2,4,6,7,8]. Executado teste bilateral, confiança 95%, hipótese 0, sem assumir variâncias iguais. Saída observada: estimativa 2,33; IC=(-3,98;8,64); T=0,91; GL=5,93; p=0,400.
- Criada fixture fixtures/welch_minitab_22_6/observed.json com entradas, opções, proveniência, valores observados e tolerâncias de meia unidade do último decimal. O MiniTaBom com GL fracionário passa nessa conferência. Isso valida somente a saída arredondada desse caso, não a precisão completa nem compatibilidade com o 16. A Worksheet 2 e o resultado foram deixados no Minitab, sem salvar o projeto original em disco.
- Interface com cabeçalhos mais claros, botão principal azul, diálogos com abas Dados/Opções, títulos de resultados destacados e lista de análises no navegador. A lista é reconstruída a partir do texto ao abrir projeto. Relatórios em texto incluem N, média, desvio, erro padrão, IC, T, GL e p; valores-p muito pequenos são exibidos como limite.
- Conferência visual realizada no MiniTaBom com o diálogo de uma amostra, ambas as abas, execução e navegação de volta ao título do relatório. A prévia contém apenas os dados sintéticos iniciais.
- Verificação: 45 testes aprovados, incluindo caso analítico Cauchy, hipóteses unilaterais, pares ausentes, graus de liberdade, comparação com API independente de testes do SciPy, erro numérico, submissão do diálogo e fixture arredondada da referência. Testes que compartilham SciPy verificam a integração/fórmulas, não independência da biblioteca numérica.
- Pendências deste bloco: entradas resumidas/empilhadas, gráficos anexos, armazenamento estruturado e validação integral na versão 16. Adicionado exemplo_inferencia.statlab para estudo reproduzível.

### Quarta etapa: escopo integral, histórico e gráficos

- O usuário solicitou cobertura integral, sem lacunas. Alvo mantido em Minitab 16.2.4.0 conforme contexto da faculdade. Criado `INVENTARIO_FUNCIONAL.json`, com 23 áreas e critérios de aceite por função. É um mapa inicial e não um inventário exaustivo; não há percentual defensável nem paridade validada.
- Histórico de até 50 alterações da planilha em memória, com desfazer/refazer de células, colagens, linhas, adição e renomeação de colunas. A edição pendente é confirmada antes de desfazer. O histórico é reiniciado ao abrir/importar/criar projeto; resultados da sessão não são recalculados nem desfeitos por esse histórico.
- Borda de célula ativa e cancelamento das tarefas de redesenho ao destruir a planilha. Corrigida proteção de duplo clique em áreas sem cabeçalho de coluna.
- Histograma redimensionável com eixos e frequências; boxplot simples com quartis, mediana, bigodes e outliers. Ambos usam cópia dos dados na criação. Não há exportação ou persistência gráfica.
- Modelo de boxplot usa cercas de 1,5IQR e valores adjacentes observados, inclusive bigodes que podem entrar na caixa, conforme documentação oficial atual. Caso documental 1200,1443,1490,1528,1563,2479 conferido analiticamente em teste; não foi reexecutado no Minitab 16.
- Verificação automatizada: 33 testes aprovados, incluindo bifurcação do histórico, isolamento dos snapshots, limite do histórico, desfazer/refazer integrado e desenho dos dois gráficos em Canvas Tk. Comparação visual e numérica diferencial com a versão 16 continua pendente.
- Conferência visual adicional no Windows: célula ativa com borda e novo boxplot exibidos corretamente com os dados sintéticos iniciais. A janela gráfica foi deixada aberta. O inventário também pode ser consultado por Ajuda > Cobertura do projeto. Nenhum dado do Minitab foi usado como fixture nesta etapa.

### Terceira etapa: interface de estudos

- Aparência reorganizada com navegador lateral, cabeçalhos de sessão e planilha, barras de rolagem nos dois eixos, barra de estado e divisórias ajustáveis. Menus Arquivo, Dados, Estat, Gráfico, Janela e Ajuda expõem as ações implementadas.
- Novo módulo `worksheet.py`: edição diretamente na célula, F2, digitação, confirmação/avanço com Enter/Tab, cancelamento com Esc, numeração de linhas e identificação da célula ativa. As linhas adicionais de digitação não contam como observações até receber conteúdo.
- Ctrl+C copia uma célula; Ctrl+V cola blocos tabulados, acrescentando linhas. Blocos com excesso de colunas são recusados antes de qualquer alteração. Não há desfazer da planilha nem seleção retangular para copiar blocos.
- Novo projeto vazio e renomeação de colunas; Ctrl+N/O/S e ajuda F1. A edição pendente é confirmada antes de salvar/analisar/fechar/substituir. Uma mudança de dados avisa na barra inferior que as análises precisam ser executadas novamente.
- Diálogo de descritivas mais compacto, com seleção/desmarcação de todas as medidas e posição centralizada. Nomes de coluna permanecem no cabeçalho, ao lado de C1/C2.
- Verificação: 26 testes aprovados em Python 3.14.2, incluindo integração com widgets Tk reais em janela oculta. Cobertura nova: cancelar edição, salvar edição pendente, analisar edição pendente, linhas virtuais, navegação, troca de coluna com edição pendente, renomeação e colagem sem alteração parcial.
- Conferência visual realizada no Windows com a janela principal e o diálogo de descritivas. Corrigidos o corte do nome no cabeçalho e o deslocamento inicial do diálogo. Não foi realizada comparação visual lado a lado com Minitab 16 nem inspeção exaustiva em todas as resoluções/DPI.
- A interface permanece uma implementação independente inspirada no fluxo clássico. Não representa cobertura integral dos menus nem equivalência estatística com o Minitab.

### Segunda etapa: descritivas e fluxo clássico

- Decisão do usuário: preservar Minitab 16 como alvo para acompanhar a faculdade. A instalação local consultada é 22.6.0.0 em `C:/Program Files/Minitab/Minitab 22`. A versão 22 serve como referência complementar; não comprova comportamento da 16.
- Interface reorganizada com sessão acima da planilha, divisória ajustável, identificação C1/C2 e menus Arquivo, Estat e Gráfico. O diálogo de descritivas aceita várias colunas e seleção de medidas. O botão anterior continua disponível.
- Núcleo ampliado: N total, Q1/Q3, IQR, amplitude, CV e soma dos quadrados não centrada. Contratos e convenções nos extremos constam no README; n pequeno e média negativa ainda precisam de comparação experimental com a versão 16.
- Relatórios de várias colunas só são inseridos após todas as colunas serem calculadas. Erros identificam a coluna; estouro numérico gera mensagem controlada.
- Adicionado exemplo sintético `exemplo_descritivas.statlab` com resultados analíticos esperados. Não é uma saída do Minitab.
- Validação: 15 testes aprovados (`python -B -m unittest -v`), incluindo interpolação, casos pequenos, média zero/negativa, invariância por translação/escala e seleção de colunas/medidas. A nova interface ainda não foi verificada visualmente.
- Ainda pendentes: moda, média aparada, assimetria/curtose, MSSD, agrupamentos e acumulados. Portanto DESCRIBE permanece parcial.

- Implementado `project.py`: persistência própria `.statlab` em JSON, versão 1, com cabeçalhos, células textuais e resultados em texto. Não lê MPJ/MTW.
- Implementado menu Projeto para abrir, salvar e salvar como; indicador de alterações e confirmação ao fechar/substituir. Cancelamento ou falha ao salvar impede a substituição.
- Importar CSV limpa resultados anteriores e inicia projeto sem caminho associado. Exportar CSV/texto mantém o indicador de alterações do projeto.
- Salvamento escreve em arquivo temporário no diretório do destino e usa substituição ao final. Um teste simula falha de substituição e verifica que o arquivo anterior permanece intacto.
- Verificação: `python -B -m unittest -v`, 10 testes aprovados em Python 3.14.2. Inclui os cinco testes originais e cinco de persistência/decisão de salvamento. Não foi realizada inspeção visual da interface nesta etapa; o teste da confirmação usa diálogos simulados.
- Próximos itens: validar manualmente os fluxos na interface, endurecer entrada e casos numéricos extremos e completar contratos de DESCRIBE antes de implementar opções adicionais. Resultados estruturados, histórico e compatibilidade Minitab continuam pendentes.

Data: 22/10/2026
Referência encontrada: Minitab 16.2.4.0 para Windows.
Projeto: C:/Users/00022021/statlab

## 1. O que este documento entrega

Este é o relatório integral do trabalho realizado nesta conversa, acrescido de uma especificação proposta para continuar o desenvolvimento. Não é uma análise completa de todos os recursos internos do Minitab.

O trabalho realizado foi uma inspeção de instalação, leitura de artefatos locais, investigação documental inicial de DESCRIBE e construção de um protótipo independente. Não houve descompilação, depuração do executável, reconstrução do código-fonte, análise de todas as DLLs, inventário exaustivo dos menus ou validação numérica contra uma nova execução do Minitab.

Não há percentual defensável de equivalência: o denominador, isto é, o inventário completo por função e opção, ainda não foi levantado.

Convenções deste relatório:
- OBSERVADO: confirmado nos arquivos lidos ou nos testes executados.
- DOCUMENTADO: descrito na ajuda local; ainda pode exigir confirmação experimental.
- PROPOSTO: decisão de arquitetura ou método para implementação futura.
- PENDENTE: informação ou trabalho ainda não concluído.

## 2. Evidências e rastreabilidade

### E01 — instalação

OBSERVADO: executável encontrado em:
C:/Program Files (x86)/Minitab/Minitab 16/Mtb.exe
Versão do arquivo: 16.2.4.0.

A pasta contém bibliotecas com nomes como MtbMath.dll, MtbStatUtil.dll, MtbIO.dll, MtbGraphics.dll, MtbOLE.dll e MtbCmndFramework.dll. Esses nomes não comprovam contratos, algoritmos, arquitetura interna ou interfaces utilizáveis. Não foram inspecionados seus símbolos nem seus corpos de código.

### E02 — projeto criado

Arquivos:
- app.py: interface Tkinter.
- core.py: importação textual e cálculos.
- test_core.py: cinco testes automatizados.
- iniciar.bat: inicializador local.
- README.md: instruções e limitações.
- coverage.csv: matriz preliminar por famílias.

Requisitos observados no computador: Python 3.11 e Tkinter disponíveis. NumPy, SciPy, pandas, statsmodels, matplotlib e openpyxl não foram encontrados na checagem inicial desse interpretador. O protótipo não depende deles.

### E03 — comandos existentes

C:/Users/00022021/minitab_analysis/01_descriptive.MTB:

```text
DESCRIBE C1 C2 C5 C6.
```

C:/Users/00022021/minitab_analysis/02_inferential.MTB:

```text
AOVONEWAY C5 C6;
  GINDPLOT;
  GBOXPLOT.
VARTEST C5 C6;
  UNSTACKED.
PAIR C1 C2;
  GHISTOGRAM;
  GBOXPLOT.
```

São comandos encontrados em arquivos locais. Não foram reexecutados nesta investigação.

### E04 — sessão anterior

C:/Users/00022021/minitab_analysis/minitab_session.txt

Contém saída anterior de descritivas, ANOVA de um fator, comparação de variâncias e teste t pareado. A sessão menciona entrada em:
C:/Users/00022021/Documents/EXEMPLO TESTE T.XLSX

A existência e o conteúdo atual dessa planilha não foram verificados neste trabalho. Os resultados abaixo são transcrições resumidas da sessão, não cálculos feitos pelo MiniTaBom:

| Resultado | Valor exibido na sessão |
|---|---|
| Tempo antes: N, média, desvio padrão | 15; 2637,4; 77,9 |
| Tempo depois: N, média, desvio padrão | 15; 1084,8; 236,0 |
| APF G1: N, média, desvio padrão | 7; 121,86; 19,74 |
| APF G2: N, média, desvio padrão | 7; 211,14; 22,31 |
| ANOVA: F e graus de liberdade | 62,87; 1 e 12 |
| Teste F de variâncias: estatística e p | 0,78; 0,774 |
| Levene: estatística e p | 0,07; 0,799 |
| Pareado: média da diferença | 1552,6 |
| Pareado: IC de 95% | 1400,2 a 1705,0 |
| Pareado: estatística t | 21,85 |

A saída mostra p = 0,000 em algumas análises. Isso é formatação arredondada, não prova de probabilidade exatamente zero. Não usar esses valores arredondados como única referência de precisão.

### E05 — ajuda local

Pasta: C:/Users/00022021/minitab_auto_help

Arquivos encontrados:
- stbasics_sc/DESCRIBE_Session.htm
- stbasics_sc/PAIR.htm
- stbasics_sc/TWOVARIANCE.htm
- stanovar_sc/VARTEST.htm
- stanovar_sc/ONEWAY_Session.htm
- stanovar_sc/GLM_Session.htm
- stanovar_sc/AOVONEWAY_Session.htm
- stanovar_sc/ANOVA_Session.htm
- GR_Graph_Menu/BOXPLOT_Session_Pro.htm

DESCRIBE_Session.htm foi lido para extrair os comportamentos da seção seguinte. A lista dos demais arquivos não significa que seus contratos tenham sido analisados. A ajuda contém metadados antigos e links relativos; sua correspondência integral com a versão instalada ainda deve ser confirmada. Não foi realizada pesquisa externa para este relatório.

## 3. Descobertas documentais de DESCRIBE

Origem de todos os itens desta seção: E05, DESCRIBE_Session.htm. São paráfrases e especificações técnicas derivadas da ajuda local.

### 3.1 Entrada e agrupamento

DOCUMENTADO:
- Comando principal DESCRIBE aceita uma ou mais colunas.
- BY identifica variáveis de agrupamento.
- Agrupadores podem ser numéricos ou textuais.
- O texto descreve níveis textuais em ordem de primeira aparição.
- Colunas devem ter comprimentos iguais para BY.
- Valores ausentes são omitidos de várias estatísticas básicas.

PENDENTE: ordem dos níveis numéricos, ordenação de múltiplos agrupadores, representação de ausentes por tipo, comportamento de colunas vazias e detalhes de MISSING.

### 3.2 Estatísticas expostas

A ajuda lista:
MEAN, SEMEAN, STDEVIATION, VARIANCE, CVARIATION, QONE, MEDIAN,
QTHREE, IQRANGE, MODE, TRMEAN, SUMS, MINIMUM, MAXIMUM, RANGE,
SSQ, SKEWNESS, KURTOSIS, MSSD, N, NMISSING, COUNT, CUMN,
PERCENT, CUMPERCENT.

Em partes explicativas aparecem formas abreviadas ou nomes diferentes, como STDEV, SUM e NMISS. Não assumir que todos sejam aliases aceitos: confirmar no interpretador da versão instalada.

| Item | Comportamento documental | Situação no MiniTaBom |
|---|---|---|
| Média | Média aritmética, ignorando ausentes | Implementado, sem comparação Minitab |
| Erro padrão | Desvio padrão dividido por raiz de N | Implementado, sem comparação Minitab |
| Desvio/variância | Estatísticas amostrais | Implementado, sem comparação Minitab |
| CV | 100 vezes desvio padrão dividido pela média | Pendente |
| Quartis | Posições (n+1)/4 e 3(n+1)/4 com interpolação | Pendente |
| Mediana | Centro ou média dos dois centrais | Implementado, sem comparação Minitab |
| IQR | Q3 menos Q1 | Pendente |
| Moda | Exibição de até quatro menores modas | Pendente |
| Média aparada | Retirada de 5% de cada ponta, quantidade arredondada | Pendente |
| Soma, mínimo, máximo | Operações sobre valores válidos | Implementado, sem comparação Minitab |
| Amplitude | Máximo menos mínimo | Pendente |
| SSQ | Soma dos quadrados não centrados | Pendente |
| Assimetria/curtose | Medidas disponíveis; fórmula completa não extraída | Pendente |
| MSSD | Metade da média dos quadrados das diferenças sucessivas | Pendente |
| N e ausentes | Contagens separadas | Implementado parcialmente |
| COUNT | Total de observações | Pendente |
| CUMN | Contagem acumulada por grupos | Pendente |
| PERCENT/CUMPERCENT | Percentuais por grupos e acumulados | Pendente |

Cuidados para implementação:
1. Quartis: não substituir automaticamente pelo padrão de outra biblioteca. Para valores 1 a 10, a regra documental produz Q1=2,75 e Q3=8,25. Falta confirmar N muito pequeno e posições nos extremos.
2. Média aparada: definir experimentalmente o desempate do arredondamento. O arredondamento padrão do Python não deve ser presumido equivalente.
3. Moda: falta determinar o comportamento quando todos os valores têm frequência um.
4. SSQ: o corpo da ajuda indica soma não centrada, mas há uma nota com redação inconsistente. Registrar e testar a divergência.
5. MSSD: para 1, 2, 4, 10, a regra descrita dá (1+4+36)/(2*3)=6,833333... . Falta definir o efeito de ausentes entre observações e a dependência de ordem.
6. CV: falta definir média zero e negativa.
7. Assimetria e curtose: identificar correção de viés, normalização, mínimo N e tratamento de variância zero.

### 3.3 Gráficos associados

DOCUMENTADO: GHISTOGRAM, GNHISTOGRAM, GINDPLOT e GBOXPLOT. O corpo também menciona GSUMMARY.
- Histograma normal usa média e desvio padrão amostrais para a curva.
- Com grupos, a ajuda descreve histogramas separados e mesma escala para comparação.
- Gráficos de valores individuais e boxplots podem mostrar grupos lado a lado.

PENDENTE: algoritmos de classes, limites, inclusão nas bordas, quartis usados no boxplot, bigodes, outliers, escalas, exportação e padrões visuais.

O histograma do protótipo usa uma regra própria e não deve ser apresentado como réplica.

## 4. Contrato atual do MiniTaBom

### 4.1 Dados

headers: lista de nomes únicos e não vazios.
rows: lista de linhas, cada uma uma lista de strings.
A análise converte somente a coluna selecionada.

CSV:
- Leitura UTF-8 com BOM opcional.
- Detecção entre vírgula, ponto e vírgula e tabulação.
- Se detecção geral falha, tentativa com o cabeçalho.
- Cabeçalho obrigatório.
- Linhas totalmente vazias são descartadas.
- Quantidade de campos inconsistente gera erro.
- Exportação com ponto e vírgula e UTF-8 com BOM.

Conversão numérica:
- Espaços externos removidos.
- Vazio ou asterisco representam ausente.
- Vírgula decimal é convertida em ponto.
- Texto não numérico, NaN e infinito são rejeitados.
- Separadores de milhar não são suportados.

### 4.2 Cálculos presentes

Para n valores válidos:
- média = soma(x)/n;
- variância amostral = soma((x−média)^2)/(n−1);
- desvio padrão = raiz(variância);
- erro padrão = desvio padrão/raiz(n);
- mediana = centro dos valores ordenados;
- mínimo, máximo e soma.

A implementação usa statistics e math.fsum da biblioteca padrão. As fórmulas indicam a semântica matemática, não uma promessa sobre o algoritmo interno dessas bibliotecas.
Com n=1, variância, desvio e erro padrão retornam None.
Sem números válidos, a análise é recusada.

Histograma:
- k = mínimo(30, teto(log2(n)+1)).
- Classes de largura igual entre mínimo e máximo.
- Máximo entra na última classe.
- Série constante resulta em uma classe cujo intervalo tem extremos iguais.
- Barras exibem contagens absolutas.

### 4.3 Interface

Tkinter/ttk, uma planilha em memória e uma coluna selecionada por análise.
Duplo clique edita célula. Há inclusão de linhas e colunas.
Resultados são texto editável, sem um objeto estruturado persistido.
Gráfico é desenhado em Canvas e não possui exportação própria.

### 4.4 Testes executados

Cinco testes passaram:
1. Amostra analítica 2,4,4,4,5,5,7,9: média 5; mediana 4,5; variância 32/7; erro padrão raiz(4/7).
2. Entrada vazia e amostra de tamanho um.
3. CSV com vírgula decimal e ausentes.
4. Rejeição de texto, NaN, infinito, cabeçalho duplicado e linhas inconsistentes.
5. Conservação da contagem em histograma e série constante.

Um teste detectou que a detecção de delimitador podia aceitar arquivo malformado. Foi adicionada a tentativa com o cabeçalho; a suíte passou após a correção.

Não foram executados testes diferenciais contra o Minitab. A interface não recebeu validação visual/manual nesta sessão. Esses cinco testes não cobrem todo o espaço de entradas.

## 5. Limitações e problemas a resolver primeiro

Constatados no código ou inferidos diretamente da implementação:
- Abrir outro arquivo ou fechar a janela pode perder alterações sem aviso.
- Não há desfazer/refazer, exclusão de linhas/colunas ou colagem de intervalos.
- Não há projeto persistente com planilhas, análises e gráficos.
- Texto dos resultados é editável e não serve como registro imutável.
- A numeração de linha em erros pode divergir do arquivo original se houver linhas vazias descartadas.
- Detecção automática de CSV permanece ambígua; falta escolha explícita de delimitador e prévia de importação.
- Não há suporte a encodings legados, arquivos Excel ou projetos Minitab.
- Nomes exibidos são usados para identificar colunas; faltam identificadores estáveis.
- Não há datas, categorias tipadas, unidades, pesos ou metadados.
- Atualizar a tabela reconstrói todas as linhas; volumes grandes não foram medidos.
- Cálculos rodam na thread da interface.
- Valores finitos extremos podem provocar overflow ou perda numérica em operações subsequentes; o histograma precisa de tratamento adicional para amplitude extrema.
- Não há distribuição instalável independente de Python.
- Nenhum parser de comandos Minitab foi implementado.
- coverage.csv é uma lista de famílias, não um inventário de todas as funções.

## 6. Arquitetura proposta para a continuação

PROPOSTO; não descreve a arquitetura interna do Minitab.

Separar em camadas:
1. Dados: projeto, planilhas, colunas tipadas, máscaras de ausentes e identificadores.
2. Métodos: funções estatísticas sem interface gráfica.
3. Aplicação: validação de parâmetros, execução, cancelamento e registro.
4. Resultados: estatísticas, tabelas, modelos, gráficos e diagnósticos estruturados.
5. Interface: apresenta e edita dados; não implementa fórmulas.
6. Persistência e importação: leitura/escrita com versão de esquema.
7. Compatibilidade: traduz um subconjunto documentado de comandos para a mesma camada de aplicação.
8. Verificação: fixtures, comparações e relatórios de cobertura.

Estrutura sugerida, a criar gradualmente:

```text
statlab/
  app.py
  domain/
    project.py
    worksheet.py
    results.py
  methods/
    descriptive.py
    distributions.py
    hypothesis.py
    regression.py
    anova.py
    quality.py
    doe.py
    reliability.py
  services/
    analysis_runner.py
    history.py
  io/
    csv_import.py
    project_store.py
  compatibility/
    parser.py
    commands.py
  ui/
  tests/
    unit/
    differential/
    fixtures/
  docs/
```

Contrato proposto para uma execução:
- analysis_id e method_id estáveis.
- Versão do método e do aplicativo.
- IDs das colunas e impressão digital dos dados usados.
- Parâmetros explícitos, inclusive os que antes eram padrões.
- Política de ausentes.
- Estatísticas numéricas não arredondadas.
- Tabelas, gráficos e dados necessários à sua reconstrução.
- Diagnósticos, avisos de convergência e status.
- Proveniência da referência quando usada em validação.

Separar cálculo e apresentação: arredondamento ocorre ao renderizar; não reutilizar números arredondados em cálculos posteriores.

Persistência proposta: formato próprio versionado, com manifesto e dados. Definir primeiro o esquema; não afirmar compatibilidade MPJ/MTW antes de estudar esses formatos. Evitar formatos que executem código ao abrir projetos.

Bibliotecas numéricas futuras devem ser avaliadas contra os contratos escolhidos. A presença de um método com o mesmo nome em uma biblioteca não garante os mesmos padrões, estimadores ou resultados. Versões e APIs deverão ser verificadas quando forem selecionadas.

## 7. Especificação mínima para cada nova função

Criar uma ficha com:
- ID e família.
- Nome na interface e comando de referência.
- Caminho de menu confirmado.
- Fonte documental, versão e trechos relevantes.
- Tipos, formato e restrições das entradas.
- Parâmetros obrigatórios, opcionais e valores padrão.
- Tratamento de ausentes e agrupamentos.
- Fórmulas e convenções.
- Algoritmo numérico, tolerâncias e convergência.
- Resultados e diagnósticos.
- Erros esperados.
- Casos de teste e resultados de referência.
- Limitações conhecidas.
- Estado: identificado / especificado / implementado / testado analiticamente / comparado com referência / aceito.

Implementado e validado são estados diferentes. Gráfico e cálculo também devem poder ter estados diferentes.

## 8. Próximos métodos: base matemática e decisões pendentes

As fórmulas abaixo são bases estatísticas usuais para implementação futura. Não foram verificadas como especificação completa da versão de referência.

### Teste t de uma amostra

t = (média−mu0)/(s/raiz(n)), graus de liberdade n−1.
IC bilateral: média ± quantil_t(1−alpha/2,n−1)*s/raiz(n).

Decidir: alternativas unilateral/bilateral, nível de confiança, dados resumidos, N mínimo, variância zero, ausentes e precisão das caudas.

### Teste t pareado

Preservar alinhamento por linha; formar d_i = x_i−y_i somente para pares válidos, conforme política confirmada.
Aplicar teste de uma amostra às diferenças.

Nunca remover ausentes separadamente nas duas colunas antes de formar pares. Confirmar a ordem da subtração, n efetivo e gráficos das diferenças.

### Duas médias independentes

Especificar separadamente método de variâncias iguais e método de Welch.
Welch usa erro padrão raiz(s1²/n1+s2²/n2) e graus de liberdade aproximados de Welch–Satterthwaite.
A versão agrupada usa variância combinada com graus de liberdade n1+n2−2.

Não presumir qual é o padrão do Minitab; confirmar na ajuda e em execuções.

### ANOVA de um fator

SQ entre grupos = soma_j n_j*(média_j−média_global)^2.
SQ dentro = soma_j soma_i (x_ij−média_j)^2.
F = [SQ entre/(k−1)]/[SQ dentro/(N−k)].

Faltam: entradas empilhadas/não empilhadas, grupos vazios, variância zero, ICs, comparações múltiplas, diagnósticos e métodos para heterocedasticidade.

### Regressão linear

Especificar matriz de desenho, intercepto, codificação de fatores, interações, pesos e predição.
Usar solução numericamente estável; evitar inversão explícita como implementação padrão.
Testar posto deficiente, colinearidade, resíduos, medidas de influência e intervalos.

### Qualidade e capabilidade

Definir subgrupos, estimador de sigma, fases, constantes, regras de sinais e transformação.
Não confundir dispersão global com dispersão dentro dos subgrupos.
Antes de implementar índices, fixar como sigma é estimado em cada procedimento.

### DOE, confiabilidade e modelos avançados

Exigem especificações próprias. Não são simples extensões das descritivas.
DOE inclui geração do planejamento, aleatorização, blocos, alias e análise.
Confiabilidade inclui censura, parametrização, otimização e intervalos.
Não marcar famílias como concluídas por disponibilizar apenas uma função central.

## 9. Matriz macro de cobertura

O arquivo coverage.csv acompanha este relatório. Complemento das frentes de investigação:

| Família | O que deve ser inventariado |
|---|---|
| Dados | Tipos, fórmulas, ordenar, filtrar, empilhar, transpor, unir, agregar |
| Descritivas | Todas as opções de DESCRIBE, estatísticas por linha e por grupo |
| Distribuições | Densidades/massas, CDF, inversas, parâmetros, geração aleatória |
| Inferência | Médias, proporções, variâncias, equivalência se presente, poder |
| ANOVA | Modelos, fatores, interações, efeitos, comparações e diagnósticos |
| Regressão | Linear, logística, não linear e procedimentos confirmados na versão |
| DOE | Planejamentos, análise, gráficos e otimização |
| CEP | Cartas, subgrupos, estimadores, fases, sinais e limites |
| Medição | Repetibilidade, reprodutibilidade, concordância e desenhos |
| Capabilidade | Normal, não normal, transformações, ICs e índices |
| Confiabilidade | Censura, distribuições, modelos e planos de teste |
| Multivariada | Componentes, fatores, agrupamento e métodos confirmados |
| Séries temporais | Tendência, decomposição, suavização, ARIMA e diagnósticos |
| Não paramétricos | Testes, empates, métodos exatos e aproximações |
| Tabelas | Frequências, contingência, associação e testes |
| Gráficos | Tipos, agrupamentos, edição, escalas, rótulos e exportação |
| Automação | Comandos, macros, constantes, matrizes e interfaces verificadas |
| Projetos | Persistência, recuperação, formatos e compatibilidade |
| Assistentes | Fluxos guiados e relatórios efetivamente presentes |

A presença nesta tabela é uma tarefa de investigação, não confirmação de todas as funções na versão 16.2.4.0. Também não prova que nenhuma família esteja faltando.

## 10. Processo de engenharia reversa funcional

1. Congelar a referência: versão, idioma, configurações e opções.
2. Capturar menus, diálogos e ajuda; cadastrar cada função e opção.
3. Escolher dados sintéticos que distingam convenções concorrentes.
4. Executar no Minitab e guardar dados, comando exato, opções e resultados.
5. Preferir comandos e interfaces nativas documentadas; não inventar sintaxe.
6. Implementar o mesmo contrato na camada de métodos.
7. Comparar resultados estruturados, não apenas texto ou imagens.
8. Investigar divergências: dados, padrões, estimador, algoritmo, arredondamento.
9. Registrar decisões e atualizar o estado de cobertura.
10. Repetir para opções, limites e interações.

O Minitab não foi lançado novamente nesta etapa. A automação COM foi apenas identificada como possibilidade pela skill; interfaces e versões não foram verificadas. Antes de usar COM, consultar a ajuda de automação instalada e a biblioteca de tipos correspondente.

## 11. Plano de validação

### Dados obrigatórios

Por método, incluir:
- Exemplo analítico pequeno.
- Conjunto comum de tamanho moderado.
- Zero, um e poucos valores válidos.
- Constantes e variância quase zero.
- Ausentes nas extremidades e no meio.
- Valores negativos e escalas muito distintas.
- Empates, grupos desbalanceados e categorias ausentes.
- Entradas inválidas.
- Casos específicos: colinearidade, separação, censura, não convergência.

### Comparações

Para valor numérico, usar critério:
abs(obtido−referência) <= atol + rtol*abs(referência)

atol e rtol devem ser definidos por método e campo. Não adotar um valor único para todas as análises.
Contagens e graus de liberdade inteiros geralmente pedem comparação exata quando o contrato assim exigir.
Probabilidades muito pequenas exigem atenção a caudas e subfluxo.
Validar categorias, nomes e diagnósticos além dos números.

Resultados arredondados da sessão anterior só permitem verificar a precisão exibida. Para maior precisão, obter saídas armazenadas ou exportadas com a precisão disponível na ferramenta.

### Fixture proposta

Uma pasta por caso:
- input.csv
- reference_command.mtb
- reference_output.txt
- expected.json
- metadata.json

Metadata: versão Minitab, idioma, data, opções, parâmetros, origem, tolerâncias e justificativas.
Não versionar dados pessoais desnecessários: casos sintéticos facilitam reprodução e compartilhamento.

### Critério de aceite

Uma função é aceita quando:
- contrato e parâmetros estão documentados;
- entradas inválidas têm tratamento definido;
- testes analíticos passam;
- comparações de referência passam nas tolerâncias justificadas;
- interface permite reproduzir o caso;
- resultados preservam proveniência;
- limitações estão registradas.

“Todas as funções” só poderá ser afirmado com inventário completo da versão alvo e cada item aceito ou explicitamente excluído por decisão de escopo.

## 12. Roteiro de implementação por entregas

Entrega A — estabilizar o protótipo:
avisos de alterações não salvas, importação explícita, IDs de coluna, testes de integração, erros numéricos e persistência básica.

Entrega B — concluir descritivas:
quartis documentados, CV, moda, aparada, amplitude, SSQ, MSSD, assimetria/curtose e agrupamento; validar cada opção contra referência.

Entrega C — inferência:
distribuições necessárias, teste t de uma amostra, pareado, duas amostras, variâncias e ANOVA de um fator; recuperar dados associados à sessão anterior.

Entrega D — plataforma de análise:
resultados estruturados, histórico reprodutível, múltiplas planilhas, modelos e gráficos exportáveis.

Entrega E — módulos avançados:
regressão, ANOVA expandida, qualidade/medição, DOE, confiabilidade, multivariada, séries e não paramétricos, guiados pelo inventário.

Entrega F — compatibilidade e distribuição:
subconjunto de comandos documentado, importadores avaliados individualmente, instalador, migrações, testes integrados e documentação.

Não há estimativa confiável de prazo sem inventário, critérios de equivalência, equipe e plataforma final definidos.

## 13. Como retomar imediatamente

1. Extrair o pacote e manter os arquivos juntos.
2. Executar iniciar.bat em um ambiente com Python e Tkinter.
3. Executar: python -B -m unittest -v
4. Ler README.md e coverage.csv.
5. Criar controle de versão do projeto, ainda não configurado nesta conversa.
6. Começar pela Entrega A e pela ficha completa de DESCRIBE.
7. Abrir as referências E03–E05 no computador original.
8. Montar fixtures verificáveis antes de anunciar compatibilidade.

Os arquivos de ajuda, dados e sessão originais não são necessários para abrir o protótipo. Eles não estão incluídos automaticamente no pacote de código e documentação; os caminhos acima identificam onde foram encontrados. Para continuar em outro computador, reunir as referências necessárias e revisar quais dados podem ser compartilhados.

## 14. Instrução sugerida para outro desenvolvedor ou agente

“Continue o projeto MiniTaBom a partir do código e deste relatório. O alvo pretendido é equivalência funcional com Minitab 16.2.4.0, ainda não demonstrada. Não trate coverage.csv como inventário completo. Preserve os dados originais. Primeiro estabilize importação, persistência e resultados estruturados. Depois especifique e valide DESCRIBE com a ajuda local e casos diferenciais. Não invente comandos nem marque funções como equivalentes sem evidência. Separe fórmulas, interface e apresentação; mantenha registro das lacunas.”

## 15. Estado de encerramento desta documentação

Entregue: protótipo inicial, cinco testes aprovados, matriz preliminar e este relatório.
Documentado adicionalmente: comportamento de opções de DESCRIBE encontrado na ajuda local.
Pendente: inventário completo, implementação avançada, validação diferencial, interface testada visualmente, instalador e compatibilidade de arquivos/comandos.

Este documento permite continuar o trabalho com rastreabilidade, sem atribuir ao protótipo uma completude que ele ainda não tem.
