# 12. Solução de problemas

## Construção

| Mensagem ou sintoma | Causa | O que fazer |
|---|---|---|
| `o contrato está incompleto` | campos do contrato vazios ou com PREENCHER | preencha com a pessoa (porta G1) |
| `layout "?"` | o extrator deixou a escolha para você | escolha pelo significado (tabela do `SKILL.md`) |
| `falta a proveniência ... .json` | imagem copiada à mão | baixe e trate com `imagens.py`, ou `baixar local` para arquivo da pessoa |
| `licença marcada VERIFICAR` | o acervo não informou a licença | leia a página do item e registre a decisão no `.json` |
| `destaque não aparece literalmente` | expressão de `destaques` diferente do texto | copie a expressão exata do item |
| `três slides seguidos com o layout` | repetição | troque o do meio ou reordene |
| aviso de layout fora do que ele comporta | citação longa, poucas datas, passos, imagens ou cartões fora de faixa, tabela grande, `torres` com unidades diferentes, documento em tela cheia | troque o layout ou ajuste o conteúdo. A tabela de "não use quando" está em `04-layouts.md` |
| `o texto difere da origem (modo verbatim)` | o texto foi reescrito | volte ao texto da pessoa. Correções só com ela, na origem |
| `emoji ou símbolo no texto` | emoji ou ícone de caractere | tire. Use imagem, diagrama ou nada |
| `o campo "x" não existe` | nome errado ou campo inventado | use o nome sugerido. A lista está em `04-layouts.md` |
| `texto dentro da imagem` | captura, figura, anúncio, ficha | refaça como gráfico, diagrama, tabela ou texto. Se a página é o assunto, `"documento": true` |
| `a mesma obra ... está em N slides` | recortes da mesma imagem com nomes diferentes | no máximo dois slides. Nos outros, número, diagrama, arte ou outra obra |
| `o estilo do deck proíbe` | pontuação ou palavra vetada em `estilo_texto` | reescreva a frase com ponto ou vírgula |
| HTML muito pesado (acima de 40 MB) | imagens grandes | `tratar --max 2000 --qualidade 80`, e não use a mesma imagem em versões diferentes |

## Verificação

| Reprovação | O que fazer |
|---|---|
| `encosta em` | uma palavra longa passa da coluna (títulos de passos, colunas estreitas). Encurte a palavra, use menos passos ou outro layout |
| `o retrato ... numa faixa` | retrato em faixa estreita corta o rosto. Use `dividido`, `imagem-total` ou `numero`, ou outra imagem na faixa |
| fontes, um trecho de legenda ou rótulo abaixo de 28 px | em HTML livre, `data-role` e `font-size` corretos. Em gráfico, menos categorias |
| fontes, corpo abaixo de 44 px | menos texto, `lista` ou `faixa` no lugar de `dividido`, ou divisão do slide |
| encaixe | o texto não cabe nem no piso. Mesmo conserto acima |
| tela, fração vazia alta | falta visual ou o texto está curto demais para o layout. Ver tabela em `07-legibilidade-e-ocupacao.md` |
| tela, maior vazio alto | uma faixa ou um bloco inteiro sem nada. Em geral embaixo do texto ou num campo de cor. Troque o layout ou deixe o corpo crescer (`cmax`) |
| tela, extensão baixa | o conteúdo está espremido num canto. Use um layout que vá de margem a margem |
| contraste | campo de cor claro com texto claro, ou o contrário. Troque `secoes[].campo` ou use `ajustes_tema` |
| quase iguais | dois vizinhos com a mesma composição. Troque o layout ou inverta o `lado` |
| variação, poucos layouts | o deck repete três ou quatro layouts. Reveja a tabela de escolha |
| sem internet falhou | algo no HTML pede a rede (fonte, imagem ou script externo em HTML livre) |
| erro de console | olhe a mensagem no relatório. Em geral, HTML livre malformado |

## Imagens

| Sintoma | O que fazer |
|---|---|
| `buscar` não acha nada | termos em inglês, objeto concreto, nome próprio, data. Tente outro acervo |
| 403 ou 429 | espere um minuto e baixe uma por vez. Commons limita muito, prefira os outros. Pelo `openverse`, a imagem da Commons pode vir com 1280 ou 960 px (o script avisa) |
| `RECUSADA a licença` | NC, ND, direitos reservados ou licença desconhecida. Procure outra imagem, leia a página e use `--licenca "TEXTO"`, ou `--aceitar-nc` só em aula sem fins comerciais |
| imagem pequena (abaixo de 1600 px) | procure a versão de maior resolução (TIFF na LoC, `~orig` na NASA) ou use em área menor |
| a primeira página do livro é a capa ou uma carta de cores | `--pagina N` com a página certa (olhe a folha de candidatas) |
| moldura, cartão de catálogo ou carimbo na borda | `tratar --cortar` |
| rosto cortado | `foco` ou `foco_imagem` |

## Exportação

| Sintoma | O que fazer |
|---|---|
| `TRAVADO` | leia os motivos. Construa, verifique, gere o painel e espere o avaliador |
| PDF com página a mais ou a menos | rode de novo. Se persistir, há slide com altura maior que 1080 em HTML livre |
| PPTX com fonte trocada | `python3 scripts/instalar_fontes.py` na máquina que abre o PPTX, depois feche e abra o PowerPoint. Ou gere com `--fontes-seguras` |
| PPTX com texto deslocado no LibreOffice | diferença de métrica de fonte. Confira no PowerPoint. Se precisar de fidelidade total, `--modo imagem` |
| PPTX grande demais para e-mail | `--max-mb 20`. Se não couber, `imagens.py tratar --max 1600` nas imagens do deck |
| gráfico ou tabela não ficou editável | só `barras`, `barras-h`, `linha` e `tabela` viram objetos nativos, e só com `--dados-nativos`. Os outros ficam no fundo |
| `--conferir` acusa fonte não instalada | rode `instalar_fontes.py` na máquina que vai abrir o PPTX, ou gere com `--fontes-seguras` |
| `--conferir` acusa texto abaixo de 14 pt | caixa de texto de HTML livre com fonte pequena. Corrija no `deck.json` e construa de novo |
| `--conferir` não acha o LibreOffice | instale ou ponha `soffice` no PATH. O PPTX é gerado mesmo sem a conferência |

## Texto de PPTX ou PDF

| Sintoma | O que fazer |
|---|---|
| `extrair_texto.py` lê PDF em modo autoral mesmo com `--verbatim` | o PDF não marca slides. Use o texto como insumo ou peça a origem em .md ou .docx com `&&&` |
| itens de PDF partidos ou colados | quebras do PDF. Redija o slide a partir do texto, sem copiar a quebra |
| aviso de imagens no PPTX de origem | as imagens não são extraídas. Pergunte a origem e a licença e registre com `imagens.py baixar local` |

## Ambiente

| Sintoma | O que fazer |
|---|---|
| `Executable doesn't exist` do Playwright | `python3 -m playwright install chromium` |
| Chromium não abre em contêiner | rode como está (os scripts já usam o modo sem janela). Se faltar biblioteca do sistema, `python3 -m playwright install-deps chromium` |
| `ModuleNotFoundError` | `python3 -m pip install -r requirements.txt` |
| sem permissão para criar link em `amostra_temas.py` (Windows) | o script copia as imagens no lugar do link |

## Quando o problema é de direção, não técnico

Tudo verde e o deck ainda parece genérico. Volte a `03-direcao-de-arte.md`. Os sinais mais comuns são a mesma composição repetida com conteúdo diferente, imagens que só ilustram o tema geral, títulos que nomeiam em vez de afirmar e ausência de um momento forte (uma imagem em tela cheia, um número enorme, uma pergunta) a cada quatro ou cinco slides.

## `fazer.py`

| Saída | O que significa |
|---|---|
| CORRIJA (rodada N de 3) | mude só os slides citados e rode de novo |
| PASSOU nas verificações, chame o avaliador | a sessão tem visão e ainda não houve avaliação. Siga `agents/avaliador-humano.md` em contexto separado |
| O avaliador apontou defeitos | corrija e rode de novo. A correção sai aprovada com nota de revisão |
| LIMITE DE RODADAS | três rodadas com erro. Entregue o rascunho e diga o que ficou. Para recomeçar a contagem depois de uma mudança grande, apague `dist/rodadas.json` |
