# MiniTaBom

Projeto independente para **fins educativos e estudo de estatística**, em português, com referência funcional pretendida no Minitab 16.2.4.0. Sem vínculo, patrocínio ou endosso da Minitab. A cobertura integral e a equivalência numérica com a versão 16 ainda estão em desenvolvimento.

## Abrir o programa

No computador em que o pacote foi gerado, abra **`Aplicativo/MiniTaBom.exe`**. Também é possível dar dois cliques em **`MiniTaBom.bat`**, na raiz desta pasta.

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
| `tools/` | Ferramentas de empacotamento, inspeção e validação. |
| `dist/` | ZIP portátil, checksum e relatório do teste do executável. |
| `.github/workflows/` | Geração do pacote Windows pelo GitHub Actions. |
| `app_metadata.json` | Versão do aplicativo e repositório das atualizações. |
| `INVENTARIO_FUNCIONAL.json` | Cobertura funcional e pendências do Minitab 16. |

`Aplicativo/`, `dist/`, `.deps/`, `.build/` e `.build-tools/` são arquivos gerados ou dependências locais e ficam fora do Git. Salve seus projetos de estudo em uma pasta pessoal, separada do aplicativo.

## Atualizações

No programa, abra **Ajuda > Verificar atualizações…**. O repositório padrão já é `pedro-cruzz/MiniTaBom`. Clique em **Verificar** para consultar a última Release estável pública e em **Abrir página da versão** para baixar o pacote. A consulta não instala nem substitui arquivos automaticamente.

Versão inicial: **0.1.0**. Para uma atualização local, aumente `version` em `app_metadata.json`, gere o ZIP e publique uma Release com a mesma tag, por exemplo `v0.2.0`. No GitHub Actions, a versão da tag e o repositório são incluídos automaticamente. Uma alteração no código ou uma tag sem Release não aparece como atualização nesse botão.

## Executar pelo código-fonte

Requer Python com Tkinter, pip e as dependências científicas do projeto. No Windows, execute `instalar_dependencias.bat` uma vez e depois:

```powershell
python src/app.py
```

Para verificar cálculos, interface e exemplos:

```powershell
python -B -m unittest -q
python -B tools/check_study_examples.py
```

## Gerar o executável

Execute **`gerar_executavel.bat`** no Windows x64 com Python x64. Ele instala as ferramentas de construção, gera o executável, faz a verificação local e prepara `Aplicativo/` e o ZIP em `dist/`.

No GitHub: **Actions > Pacote Windows > Run workflow**. Tags iniciadas em `v` também disparam a construção. O artefato da execução contém o ZIP; anexe esse ZIP às Releases para disponibilizá-lo aos usuários. O fluxo não publica Releases automaticamente.

## Recursos e documentação

Há planilha editável, CSV/projetos, descritivas, testes t/Z, proporções, variâncias, normalidade, contingência, ANOVA de um fator, correlação, regressão, distribuições e gráficos. Consulte o [manual técnico](docs/MANUAL.md), o [relatório de continuidade](docs/ANALISE_E_CONTINUIDADE.md) e a [fila de cobertura do Minitab 16](docs/analise_instalacao/cobertura_minitab16.json) para opções, testes e limitações.
