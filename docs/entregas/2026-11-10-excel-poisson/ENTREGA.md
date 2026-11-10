# MiniTaBom 0.8.0 — abertura de Excel e duas taxas Poisson

O pedido rápido de usabilidade foi priorizado e a continuação autorizada avançou na lacuna de duas taxas Poisson. O alvo continua Minitab 16.2.4.0, sem declaração de paridade integral.

## Excel sem seleção de células

Arquivo > Abrir Excel… agora pede somente o arquivo `.xlsx`. A tela de intervalo deixou de participar desse fluxo. O leitor determina a área com valores, abre as abas e preserva a posição desde A1, incluindo títulos, vazios e primeira linha. A aba ativa é respeitada quando válida; todas as abas de células, inclusive vazias/ocultas, ficam no seletor. Uma nota identifica abas originalmente ocultas.

Os nomes A/B/C evitam descartar títulos ou falhar com nomes repetidos na primeira linha. Para tabelas comuns, Dados > Usar primeira linha como nomes das colunas é opcional e reversível. A transformação preserva os IDs por posição, inclusive se os novos nomes trocarem letras A/B; undo restaura nomes e dados anteriores.

Fórmulas com resultado salvo usam esse valor; sem resultado, são mostradas como texto, sem execução. Isso permite abrir o arquivo sem exigir recálculo prévio, mantendo a limitação clara no relatório. Estilos/mesclagens e cálculo de fórmulas não são reproduzidos. O arquivo original não é alterado; salvar usa o projeto `.statlab`.

O parser de intervalo continua disponível para ferramentas legadas, com a mesma validação estrita de cabeçalhos e fórmulas sem cache. Limites de abertura automática: 100 abas, 200000 linhas/512 colunas por área e dois milhões de células entre as abas. Células apenas formatadas e dimensionamentos inflados não expandem a área de valores. O projeto inteiro é preparado/validado antes da confirmação de substituição, preservando a sessão aberta em cancelamento ou erro.

## Duas taxas Poisson

Estat > Estatísticas básicas > Duas taxas de Poisson compara taxas por exposição ou médias por observação. A entrada aceita colunas separadas, contagens/grupo e eventos/N resumidos, com exposição positiva por amostra. O teste normal permite estimativas separadas ou combinadas sob diferença zero. O teste condicional usa a binomial com proporção das exposições; o bilateral duplica a menor cauda inclusiva. O IC é normal e usa estimativas separadas, inclusive com teste exato. Métodos conferidos na [documentação oficial](https://support.minitab.com/en-us/minitab/help-and-how-to/statistics/basic-statistics/how-to/2-sample-poisson-rate/methods-and-formulas/methods-and-formulas/).

A opção de médias usa N como exposição estatística e mantém descritivas das taxas. Hipóteses não nulas têm apenas teste normal. Contagens zero geram IC normal degenerado e Z indisponível, com aviso; o exato para diferença zero permanece calculável. Os resumos são congelados no histórico; colunas usam IDs e ordem de grupos preservada. A UI aceita confiança 95 ou 0,95, armazenando a porcentagem efetiva para não reconverter na reexecução.

O contrato valida entradas/saídas e limites; a gravação usa etiquetas explícitas para limites infinitos. Resultados antigos são preservados ao reexecutar. Frequências opcionais do 16 e demais opções não foram declaradas completas.

## Evidências

**342 testes aprovados e 24 exemplos válidos.** Logs/ambiente em `unittest.log`, `examples.log` e `verification.json`.

Cinco testes novos de Excel verificam abertura sem diálogo de intervalo, todas as abas/aba ativa, posições/títulos/nomes repetidos, vazio/oculto, dimensão de formatação ignorada, fórmulas em cache/texto, cancelamento/corrupção sem alteração e promoção de nomes com IDs/undo.

Nove testes novos de Poisson verificam caudas binomiais por enumeração, Z e erro padrão analíticos, taxa combinada sem modificar o IC, conversão de unidade, médias, zeros, hipótese não nula, entradas inválidas, resumos/intervalos unilaterais, exclusões/ordem de grupos, round-trip, diálogo e atomicidade. Há conferência com o exemplo TVDEFECT da ajuda extraída da instalação 16.2.4.0: 713 ocorrências em 40 observações de duração 3 e 515 em 20 de duração 6. O caso documental confere diferença 1,65, IC e Z somente na precisão exibida.

`tests/fixtures/two_poisson_documentation16/metadata.json` identifica explicitamente **executed_reference=false** e o hash do texto. Valores-p publicados como 0,000 são comparados como menores que 0,0005, não como zero matemático. Isso não é uma fixture executada no Minitab 16. As fórmulas atuais e a ajuda histórica foram usadas separadamente; o escopo ainda requer validação diferencial.

O smoke test portátil foi ampliado para Excel automático, coordenadas, duas taxas e persistência/reexecução. Executável 0.8.0, smoke test, CRC e SHA256 aprovados; evidência em `package-verification.json`. Não houve CI remoto ou teste em Windows limpo, push ou publicação de Release.

## Arquivos e continuidade

- `excel_import.py`, `app.py`: abertura automática e promoção de cabeçalhos; API antiga mantida.
- `two_poisson.py`, `two_poisson_contract.py`, `two_poisson_service.py`, `two_poisson_dialog.py`: nova análise e histórico.
- Registro/visões atualizados, com presença documental e validação executada separadas.
- Exemplo sintético novo: `exemplo_duas_taxas_poisson.statlab`. Nenhum material original da faculdade no pacote.

Permanecem no escopo as opções restantes dos fundamentos, persistência dos demais métodos, tarefas longas/cancelamento, recuperação e famílias avançadas da auditoria. O inventário ainda não é exaustivo e nenhuma área foi declarada equivalente integralmente ao 16.
