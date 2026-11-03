# MiniTaBom

Projeto independente para **fins educativos e estudo de estatística**, em português, com referência funcional pretendida no Minitab 16.2.4.0. Sem vínculo, patrocínio ou endosso da Minitab. A cobertura integral e a equivalência numérica com a versão 16 ainda estão em desenvolvimento.

## Abrir o programa

No computador em que o pacote foi gerado, abra **`Aplicativo/MiniTaBom.exe`**. Também é possível dar dois cliques em **`MiniTaBom.bat`**, na raiz desta pasta.

O programa inicia com a planilha e a sessão vazias. Para estudar com dados de demonstração, abra um projeto da pasta `Exemplos` pelo menu Arquivo.

Para outras pessoas, disponibilize **`dist/MiniTaBom-Windows-x64.zip`** nas [Releases do repositório](https://github.com/pedro-cruzz/MiniTaBom/releases). Quem baixar deve extrair a pasta inteira e abrir `MiniTaBom.exe`. Não é necessário instalar Python nem Minitab. Mantenha `_internal` junto do executável.

O download do código-fonte pelo GitHub não inclui o executável; ele é distribuído separadamente nas Releases.

## Organização

| Pasta ou arquivo | Conteúdo |
| --- | --- |
| `Aplicativo/` | Programa pronto: **MiniTaBom.exe**, dependências, exemplos e licenças. Gerado localmente. |
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

Versão atual: **0.2.0**. Para uma atualização local, aumente `version` em `app_metadata.json`, gere o ZIP e publique uma Release com a mesma tag, por exemplo `v0.2.0`. No GitHub Actions, a versão da tag e o repositório são incluídos automaticamente. Uma alteração no código ou uma tag sem Release não aparece como atualização nesse botão.

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
