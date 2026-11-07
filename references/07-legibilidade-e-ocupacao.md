# 07. Legibilidade e ocupação

Duas exigências do pedido original são medidas em cada slide, no render real, e travam a entrega. Fontes grandes e legíveis em todo o slide. Tela inteira ocupada.

## Unidade

Tudo é medido em px do palco de 1920x1080, já descontada a escala que ajusta o palco à janela. Na lâmina padrão do PowerPoint (13,33 x 7,5 polegadas), 2 px do palco equivalem a 1 pt.

Projetado numa tela de 3 m de largura, 1 px do palco mede cerca de 1,6 mm. O corpo de 28 px tem então cerca de 4,4 cm, o de 44 px cerca de 6,9 cm e o de 64 px cerca de 10 cm.

## Pisos por papel

| Papel (`data-role`) | O que é | Piso | Alvo |
|---|---|---|---|
| `titulo` | título do slide | 64 px (32 pt) | 64 a 88 px, abertura de seção até 150 px, capa até 170 px. Título grande demais disputa com o texto |
| `numero` | número em destaque | 64 px | 200 a 300 px |
| `corpo` | itens, frases, citação, texto de cartão e de evento | 44 px (22 pt) | 48 a 60 px |
| `celula` | célula de tabela | 36 px (18 pt) | 40 a 50 px |
| `referencia` | referência bibliográfica | 32 px (16 pt) | 36 a 44 px |
| `legenda`, `rotulo`, `fonte`, `credito` | legenda de imagem, rótulo de gráfico, fonte de dado, ano, nome de seção | 28 px (14 pt) | 30 a 36 px |

Qualquer trecho com 25 caracteres ou mais, fora de legenda, rótulo, fonte ou crédito, é tratado como corpo. Isso impede que um parágrafo passe como "legenda" para escapar do piso.

Os pisos não descem. Em `deck.json > limites` dá para subi-los (por exemplo `"piso_corpo": 52` para um auditório grande), nunca baixar. A trava recusa relatório feito com limite mais frouxo.

## Como o motor ajusta o texto

Cada layout tem um tamanho máximo, mínimo e teto para o título e para o corpo (`ESPEC` em `sk.js`).

1. O título diminui até caber em poucas linhas.
2. Se o conteúdo transborda, o corpo diminui primeiro, depois o título, até os pisos.
3. Se sobra espaço, o corpo cresce até a zona de texto ficar cerca de 70% preenchida ou até o teto do layout.
4. Se o texto continua curto, nos layouts `dividido`, `lista`, `fechamento` e `referencias` a coluna de texto estreita e o visual ganha largura.
5. Título com uma palavra sozinha na última linha é reduzido um pouco, sem passar do piso, até a palavra subir.
6. Hierarquia nos dois sentidos. O corpo fica em no máximo 90% do título, e o título fica em no máximo 1,7 vez o corpo (fora capa, seção, afirmação, número e citação).

Se mesmo no piso o texto não cabe, o slide é reprovado em "encaixe". Nunca resolva isso cortando texto ou baixando o piso. Reduza o texto (modo autoral), troque o layout (`lista` e `faixa` comportam mais) ou divida o slide. Em modo verbatim, quem decide a divisão é a pessoa, e ela é feita no arquivo de origem.

## Como a ocupação é medida

`verificar.py` tira a captura de cada slide no estado final e faz o seguinte.

1. Recorta a área útil (margens de 96 px nas laterais e 64 px em cima e embaixo).
2. Divide em células de 40 px.
3. Marca como lisa a célula sem variação visível (desvio de luminância abaixo de 6 e diferença entre os percentis 3 e 97 abaixo de 22). Fundo liso e campo de cor vazio são lisos.
4. Toda célula lisa conta como vazia, exceto as que estão sobre imagem, vídeo, canvas ou desenho SVG (céu de uma foto não é área morta).
5. Um fechamento morfológico absorve o espaço entre linhas e entre itens, para contar só o vazio que o olho percebe.
6. Calcula a fração vazia, o maior retângulo vazio contínuo e a extensão do conteúdo na horizontal e na vertical.

| Medida | Limite |
|---|---|
| fração vazia da área útil | no máximo 33% |
| maior retângulo vazio | no máximo 16% da área útil |
| extensão horizontal do conteúdo | pelo menos 86% |
| extensão vertical do conteúdo | pelo menos 80% |

## Outras medidas por slide

- **Encaixe.** Nenhuma caixa de texto transborda, nenhum título passa do número de linhas do layout e nenhum texto fica em cima de outro texto.
- **Contraste.** A cor de cada trecho é comparada com a cor dominante do fundo dentro da caixa dele. Mínimo de 4,5 para 1.
- **Quase iguais.** Slides vizinhos com capturas quase idênticas (hash perceptivo) reprovam a variação.

## Enfeites e estado final (REPROVA)

`verificar.py` lê os estilos computados de cada slide no render e reprova o que é marca de gerador.

| Achado | Como é lido |
|---|---|
| texto em degradê | `background-clip: text` com degradê, ou texto SVG preenchido com degradê |
| sombra dura | `box-shadow` ou `text-shadow` sem desfoque e deslocada 2 px ou mais |
| vidro fosco | `backdrop-filter` com `blur` |
| borda lateral | borda esquerda ou direita colorida de mais de 1 px num bloco de texto (células de tabela ficam fora) |
| rótulo acima do título | texto em caixa alta, espaçado (0,05 em ou mais), com até metade da fonte do título e a menos de 1,5 título acima dele |
| quique | curva `cubic-bezier` com y fora de 0 a 1, ou `linear()` que passa de 1, lida com o movimento ligado |
| emoji ou símbolo | emoji no texto, ou elemento cujo texto é só seta, estrela, bolinha ou outro símbolo |
| numeração decorativa | número isolado do tipo 01, 02, 03 com 56 px ou mais |
| texto inacabado | texto com opacidade efetiva abaixo de 0,95 ou oculto no estado final (rótulo e legenda só abaixo de 0,6) |
| imagem apagada | imagem com opacidade abaixo de 0,3 no estado final |

O conserto é tirar o enfeite. Animação inacabada se resolve no CSS da animação, nunca baixando o limite.

## Avisos (não travam)

Aparecem no fim de `relatorio.md` e no painel do avaliador. Olhe cada um e decida.

- **Linha longa.** Linha de corpo com mais de 65 caracteres.
- **Entrelinha apertada.** Corpo de várias linhas com entrelinha abaixo de 1,15.
- **Caixa alta longa.** Trecho de 25 caracteres ou mais em caixa alta fora do título.
- **Palavra sozinha.** Última linha de um item de corpo com uma palavra só.
- **Respiro curto.** Título colado no corpo (menos de 0,6 vez a fonte do corpo) enquanto sobra uma faixa vazia maior embaixo.
- **Texto esmaecido.** Rótulo com opacidade entre 0,6 e 0,95. Prefira uma cor mais clara.
- **Ritmo.** Cinco ou mais slides seguidos sem um momento forte (`capa`, `secao`, `afirmacao`, `imagem-total`, `numero`, `numeros`, `citacao`, `pergunta`).
- **Movimento repetido.** Slides vizinhos com a mesma sequência de entradas (`data-a`).
- **Tempo.** A soma dos campos `minutos` dos slides passa de 90% de `contrato.duracao_min`.

Slides com `"apendice": true` ficam fora da regra de variação, da contagem de imagens e do ritmo, mas são medidos como os outros.

## Ler o resultado

`verificacao/relatorio.md` tem uma linha por slide com a menor fonte, o corpo mediano, a fração vazia, o maior vazio, se há imagem e o veredito. `verificacao/slides/sNNN_marcas.jpg` mostra a captura com o vazio em vermelho e os trechos pequenos ou sem contraste em laranja. `verificacao/folhas/` junta nove slides por folha, para você olhar o conjunto.

No navegador, a tecla **M** liga o medidor no próprio deck. Ele marca cada texto com o tamanho em px e pinta de laranja o que está abaixo do piso. Serve também em máquinas sem Python (ver `11-portabilidade.md`).

## Consertos por sintoma

| Sintoma | Conserto |
|---|---|
| legenda ou rótulo abaixo de 28 px em HTML livre | `data-role` certo e `font-size` de pelo menos 28 px no palco |
| corpo abaixo de 44 px | menos texto, layout mais largo, ou divisão do slide |
| faixa vazia embaixo do texto | layout com visual maior (`imagem-total`, `afirmacao`), mais um item real, ou `cmax` maior para o texto crescer |
| metade do slide vazia | falta o visual. Acrescente imagem, gráfico ou diagrama |
| campo de cor vazio | o campo precisa de conteúdo ou de arte. Em HTML livre, aumente o texto ou ponha uma imagem |
| contraste baixo | troque o campo da seção (`secoes[].campo`) ou ajuste `--sobre-campo` |
| quase iguais | troque o layout de um dos dois ou inverta o `lado` |

## O que a medição não vê

Beleza, pertinência da imagem, hierarquia e a qualidade do movimento (ritmo e repetição viram apenas avisos). Ela também não sabe se o texto diz algo verdadeiro. Por isso existe o avaliador humano (`09-avaliador-humano.md`). Verde na medição é condição necessária, não suficiente.
