# 04. Layouts e o formato do `deck.json`

`deck.json` é o único arquivo que você edita. O HTML é gerado a partir dele por `scripts/construir.py`. Exemplo completo em `exemplos/federalismo/deck.json` e catálogo com todos os layouts em `exemplos/catalogo-layouts/deck.json`.

## Campos do deck

```json
{
  "titulo": "Federalismo",
  "slug": "federalismo",
  "idioma": "pt-BR",
  "tema": "editorial",
  "modo_texto": "autoral",
  "autor": "Nome de quem apresenta",
  "instituicao": "Curso ou instituição",
  "data": "2026",
  "contrato": {
    "tese": "a frase que o deck defende",
    "mundo": "o mundo visual em uma frase concreta",
    "historia": "o caminho da plateia do primeiro ao último slide",
    "primeira_tela": "o que a plateia vê no primeiro segundo",
    "forma": "tema escolhido e por quê",
    "publico": "quem assiste",
    "sala": "tamanho da sala, projetor, distância da última fila",
    "duracao_min": 30
  },
  "ajustes_tema": { "acento": "#7A1F2B" },
  "secoes": [
    { "nome": "O conceito", "inicio": 1 },
    { "nome": "Brasil", "inicio": 9, "campo": "#2E3A44" }
  ],
  "imagens": {
    "capitolio-1846": {
      "arquivo": "assets/capitolio-1846.webp",
      "foco": "72% 62%",
      "legenda": "<i>Capitol of the United States</i>, gravura, 1846 · Library of Congress",
      "credito": "Capitol of the United States, gravura, 1846. Library of Congress. Sem restrições conhecidas.",
      "alt": "Gravura do Capitólio em 1846, com a cúpula antiga e árvores à frente."
    }
  },
  "creditos_extra": ["Dados do gráfico 13 compilados pelo autor."],
  "slides": []
}
```

| Campo | Obrigatório | O que faz |
|---|---|---|
| `tema` | sim | `tabuleiro`, `gravura`, `editorial`, `noturno` ou `datilografo` |
| `modo_texto` | sim | `verbatim` (compara cada texto com `texto_origem.json`) ou `autoral` |
| `contrato` | sim | `tese`, `mundo`, `historia`, `primeira_tela`, `publico` e `sala` precisam estar preenchidos. O construtor recusa `PREENCHER` |
| `secoes` | recomendado | blocos do deck. `inicio` é o número do primeiro slide do bloco (contando a partir de 1). `campo` troca a cor do bloco |
| `imagens` | quando houver | cada imagem tem um nome curto, usado nos slides. `arquivo`, `credito` e `alt` são obrigatórios, e `legenda` é usada só quando a pessoa pede legenda, e o arquivo precisa do `.json` de proveniência ao lado |
| `ajustes_tema` | não | troca variáveis do tema (ver `03-direcao-de-arte.md`) |
| `creditos_extra` | não | linhas extras na tela de créditos (tecla I) |
| `legendas_nas_imagens`, `fontes_no_slide` | não | `true` liga legendas ou linhas de fonte em todo o deck. Use só a pedido da pessoa |

Na imagem, `foco` diz qual ponto fica visível quando o recorte corta a imagem (`"50% 50%"` é o centro, `"72% 62%"` puxa para a direita e para baixo). `conter: true` mostra a imagem inteira sobre o papel, sem recorte, o que serve para mapas e documentos. A legenda aceita somente `<i>`, `<em>` e `<br>`.

Outros campos do deck. `"tema": "auto"` escolhe o tema pelo contrato. `"estilo_texto": {"sem": [":", ";", "—"], "vetadas": ["crucial"]}` recusa pontuação e palavras que a pessoa não usa. Nas imagens, `"documento": true` libera texto dentro quando a página é o assunto e `"pessoa": true` ou `false` corrige a marca de retrato.

## Campos comuns a todos os slides

| Campo | Uso |
|---|---|
| `layout` | um dos 23 nomes abaixo. `"?"` é recusado, porque a escolha é sua |
| `titulo` | uma afirmação curta. Aceita `*itálico*` e `**negrito**`. Use `~` no lugar do espaço para um nome não se partir entre linhas (`Rio~de~Janeiro`). O trecho curto antes da primeira vírgula já fica inteiro sozinho |
| `subtitulo`, `texto` | uma frase cada |
| `itens` | de 3 a 4, no máximo 5 (acima disso o construtor avisa) |
| `destaques` | marca expressões literais. Use `titulo`, `texto`, `citacao` ou o índice do item (`"0"`, `"1"`). Ex. `{"1": ["garantidas pela Constituição"]}` |
| `fonte` | obrigatória em `numero` e em todo slide com `grafico`. Fica na tecla I e nas notas, fora da tela |
| `fonte_visivel` | `true` mostra a fonte no pé do slide. Só quando a pessoa pedir |
| `legendas` | `true` mostra a legenda sobre as imagens deste slide. Só quando a pessoa pedir |
| `notas` | o que você diria, com tempo estimado. Sai na tecla N, na janela do apresentador e no PPTX |
| `imagem` | nome de uma imagem de `imagens` |
| `foco_imagem` | troca o `foco` só neste slide |
| `lado` | `direita` ou `esquerda`, nos layouts que têm lado |
| `etapas` | `true` revela os itens e depois as peças do gráfico ou do diagrama, uma por seta. No PDF, no PPTX e no modo final tudo aparece |
| `intensidade` | `sobrio`, `padrao` ou `vivo` só neste slide (ver `08-movimento.md`) |
| `tmax`, `cmax`, `cteto`, `tteto` | ajuste fino do título e do corpo em px. Os pisos (64 e 44) nunca descem |
| `rascunho_layout` | marcado pelo extrator quando ele sugeriu o layout. Revise e apague |
| `minutos` | tempo previsto do slide. Se a soma passar de `duracao_min`, o construtor avisa |
| `cortavel` | `true` marca o slide que pode ser pulado se faltar tempo. Nunca aparece na tela, só na janela do apresentador |
| `apendice` | `true` marca slide de reserva para perguntas. Fica depois de `fechamento` e `referencias` (o construtor recusa antes) e não conta na regra dos três layouts iguais nem no orçamento de tempo |

## Os 23 layouts

Para cada layout, a proporção indicada é a da área que a imagem ocupa. Prepare a imagem perto dessa proporção com `imagens.py tratar --proporcao` ou ajuste o `foco`.

A coluna do meio diz quando o layout parece certo e não é. O construtor avisa, sem bloquear, nos casos que consegue medir.

| Layout | Não use quando | Melhor |
|---|---|---|
| `capa` | a única imagem disponível é fraca ou só ilustra o tema | troque a imagem: na capa o defeito ocupa metade da tela |
| `secao` | o deck não declara `secoes` | declare `secoes`; sem mapa, a abertura vira só campo e título |
| `imagem-total` | a imagem é documento ou tem texto | `dividido` com `conter: true` |
| `dividido` | o visual precisa de largura (série longa, nomes compridos) | `evidencia`, `grafico` ou `tabela` inteiros |
| `faixa` | o assunto é vertical (retrato, torre, página) | `dividido` ou `imagem-total` |
| `numero` | o valor só significa algo depois de uma explicação longa, ou há três ou mais que se explicam juntos | `numeros` para três ou mais; `dividido` para explicar |
| `citacao` | a frase passa de 40 palavras, ou não tem autor e obra | recorte o trecho; sem autor, use `afirmacao` |
| `comparacao` | há mais de dois modelos, ou as colunas não têm o mesmo peso | `cartoes` ou `tabela` |
| `linha-do-tempo` | há menos de três datas, ou elas não estão na mesma escala | `comparacao` para duas datas; `lista` para escalas diferentes |
| `processo` | as etapas voltam atrás ou dependem umas das outras | `diagrama` (cadeia, ciclo) |
| `galeria` | as imagens não são do mesmo assunto, ou são cinco ou mais | `imagem-total` para uma; duas galerias para cinco ou mais |
| `cartoes` | os itens não são paralelos, são só dois, ou passam de quatro | `comparacao` para dois; `lista` para cinco ou mais |
| `grafico` | não há valores reais comparáveis, ou o dado é categórico sem ordem | `tabela` ou `diagrama` |
| `tabela` | as células precisam de frases, ou passam de 4 colunas e 5 linhas | divida em duas tabelas ou resuma as linhas |
| `pergunta` | a pergunta é retórica, ou o deck termina nela | `afirmacao` no fecho |
| `afirmacao` | a tese não cabe em duas linhas ou precisa de ressalva | `dividido` com o texto |
| `lista` | os itens são curtos, ou a imagem não rende uma tira vertical | `cartoes` ou `dividido` |
| `diagrama` | a relação é só uma sequência, ou as partes não cabem nomeadas em letra grande | `processo` para a sequência; dois diagramas para o resto |
| `fechamento` | não há três ideias para levar, ou o deck não tem tese | `afirmacao` ou `citacao` |
| `referencias` | no meio do deck, ou quando a lista não couber em um slide | deixe no fim; divida em dois slides |
| `numeros` | `torres` com unidades diferentes, ou menos de três números | mesma unidade ou tire `torres`; com dois, `comparacao` |
| `evidencia` | o gráfico precisa de um parágrafo de explicação, ou o título não é uma afirmação | `grafico` com texto |
| `livre` | um layout existente resolve | o layout existente: o livre é medido igual e perde a manutenção do motor |

### `capa`
Título enorme num campo de cor à esquerda e imagem sangrando à direita. Autor, instituição e data saem do deck.
Campos `titulo`, `subtitulo`, `itens` (raro), `imagem`. Imagem 8:9.
```json
{"layout": "capa", "titulo": "Federalismo", "subtitulo": "Dividir o poder sem partir o país", "imagem": "capitolio-1846"}
```

### `secao`
Abre um bloco. Campo de cor, título, uma frase e o mapa das seções com a atual marcada. Sem `titulo`, usa o nome da seção.
Campos `titulo`, `texto`, `itens`, `imagem`. Imagem 4:5.
```json
{"layout": "secao", "titulo": "Brasil, 1889", "texto": "Aqui a federação nasceu de um Estado unitário que se dividiu.", "imagem": "pao-de-acucar-1862"}
```

### `imagem-total`
Imagem em tela cheia e painel sólido com o texto. Use quando a imagem fala sozinha.
Campos `imagem` (obrigatória), `lado` (do painel, padrão `esquerda`), `titulo`, `texto`, `itens`, `fonte`. Imagem 16:9.

### `dividido`
O layout mais versátil. Texto de um lado, visual do outro. O visual pode ser `imagem`, `grafico` ou `diagrama`.
Campos `titulo`, `texto`, `itens`, `destaques`, `fonte`, `lado` (do visual, padrão `direita`). Imagem 4:5.

### `faixa`
Imagem panorâmica no topo, título e texto embaixo, lado a lado.
Campos `imagem`, `titulo`, `texto`, `itens`, `fonte`. Imagem 9:2. Panoramas, paisagens e plantas funcionam bem.

### `numero`
Um número real, enorme, que conta até o valor na entrada.
Campos `numero` (`valor`, `unidade`, `texto`), `titulo`, `fonte` (obrigatória), `imagem`. Imagem 3:4.
```json
{"layout": "numero", "titulo": "Municípios também são federação", "numero": {"valor": "5.570", "texto": "Desde 1988 eles têm autonomia política, administrativa e financeira."}, "imagem": "rio-orbita-1994", "fonte": "IBGE. Constituição Federal, art. 18."}
```

### `citacao`
Frase de um autor em letra grande, com aspas desenhadas e o retrato ou a obra ao lado. Cite somente o que existe, com obra e data.
Campos `citacao` (`texto`, `autor`, `obra`), `imagem`, `destaques.citacao`, `campo: false` para tirar o campo de cor. Imagem 2:3.

### `comparacao`
Duas colunas com uma imagem, um título e itens cada.
Campos `titulo`, `colunas` (2 objetos com `titulo`, `imagem`, `itens`, `destaques`). Imagem de coluna 12:5.

### `linha-do-tempo`
Imagem da época numa faixa, título e de 3 a 6 eventos com ano grande.
Campos `titulo`, `eventos` (`ano`, `texto`), `imagem`. Imagem 6:1.

Com `"orientacao": "vertical"` os eventos descem numa coluna, com a imagem numa tira à esquerda (2:3), e cada evento aceita `valor`, escrito à direita (o total depois da mudança, um preço, uma contagem). De 3 a 6 eventos.
```json
{"layout": "linha-do-tempo", "orientacao": "vertical", "titulo": "Como o Brasil chegou a 26 estados",
 "eventos": [{"ano": "1891", "texto": "As 20 províncias viram estados", "valor": "20"}, {"ano": "1988", "texto": "Tocantins é criado, Roraima e Amapá viram estados", "valor": "26"}],
 "fonte": "Constituição de 1891, art. 2º. Constituição de 1988, ADCT, arts. 13 e 14."}
```

### `processo`
Etapas em ordem, numeradas, porque aqui a ordem é informação.
Campos `titulo`, `passos` (`titulo`, `texto`), `imagem` (faixa estreita), `fonte`. Imagem 9:1. De 3 a 5 passos.

### `galeria`
De 2 a 4 imagens do mesmo assunto. Como cada imagem precisa ser identificada, é o layout em que a pessoa mais costuma pedir legenda (`"legendas": true`).
Campos `titulo`, `imagens` (lista de nomes). Imagem 1:1 com duas, 3:4 com três, 1:2 com quatro.

### `cartoes`
Três ou quatro itens paralelos, cada um com imagem (ou a arte do tema), título e uma frase.
Campos `titulo`, `cartoes` (`titulo`, `texto`, `imagem`). Imagem quase quadrada.

### `grafico`
Valores reais em barras, barras horizontais, linha ou proporção. Ver `06-graficos-e-diagramas.md`.
Campos `titulo`, `texto`, `itens`, `grafico`, `fonte` (obrigatória).

### `tabela`
Cruzamento de categorias. No máximo 4 colunas e 5 linhas, células curtas, a partir de 36 px.
Campos `titulo`, `tabela` (`cabecalho`, `linhas`), `fonte`.

### `pergunta`
Pergunta à plateia em letra muito grande, num campo de cor, com imagem vertical.
Campos `titulo` (a pergunta), `texto`, `imagem`. Imagem 2:3.

### `afirmacao`
A tese, grande, sobre imagem em tela cheia ou sobre o campo com a arte do tema.
Campos `titulo`, `texto`, `imagem`. Imagem 16:9 com área calma onde o bloco de texto pousa.

### `lista`
Texto largo e uma tira vertical de imagem. Para itens mais longos.
Campos `titulo`, `texto`, `itens`, `fonte`, `imagem`, `lado`. Imagem 1:2.

### `diagrama`
Relação entre partes. Ver `06-graficos-e-diagramas.md`.
Campos `titulo`, `texto`, `itens`, `diagrama`, `fonte`.

### `fechamento`
Três ideias para levar, com marcadores grandes e a imagem da capa de volta.
Campos `titulo`, `itens` (obrigatório), `imagem`. Imagem 2:3.

### `referencias`
Lista de referências a partir de 32 px. Se não couberem, divida em dois slides.
Campos `titulo`, `referencias` (ou `itens`).

### `numeros`
De 3 a 6 números reais que contam até o valor na entrada, como no layout `numero`. Até 4 números ficam em fileiras (número grande à esquerda, frase à direita). Com 5 ou 6, em duas colunas. Com `"torres": true`, os números ficam lado a lado e cada um ganha uma torre com altura proporcional ao valor, o que só faz sentido quando todos estão na mesma unidade.
Campos `titulo`, `numeros` (`valor`, `unidade`, `texto`), `torres`, `destaque` (índice com a cor de acento), `fonte` (obrigatória, fica fora da tela). Valor curto, até 6 caracteres. Para números grandes use a unidade (`"156,5"` e `"mi"`).
```json
{"layout": "numeros", "titulo": "Bancadas na Câmara, do teto ao piso", "torres": true, "destaque": 0,
 "numeros": [{"valor": "70", "texto": "São Paulo"}, {"valor": "53", "texto": "Minas Gerais"}, {"valor": "8", "texto": "Roraima"}],
 "fonte": "Lei Complementar 78/1993."}
```

### `evidencia`
Uma afirmação no título, em uma ou duas linhas, e o gráfico que a sustenta ocupando cerca de três quartos da tela. Sem itens. O que precisa ser dito vai no próprio gráfico, com `anotacoes` (linha) ou `anotacao` (barras). O gráfico é desenhado numa escala um pouco maior, então os rótulos ficam acima de 35 px.
Campos `titulo` (a afirmação, até 90 caracteres), `grafico`, `fonte` (obrigatória).
```json
{"layout": "evidencia", "titulo": "O país ganhou mil municípios nos anos 1990 e quase parou depois de 1996",
 "grafico": {"tipo": "linha", "rotulos": ["1980", "1991", "2000", "2010"], "valores": [3974, 4491, 5507, 5565],
             "anotacoes": [{"i": 2, "texto": "EC 15/1996 exige lei federal e plebiscito"}]},
 "fonte": "IBGE, Atlas Nacional do Brasil 2010, p. 37. IBGE, Censo 2010."}
```

### `livre`
HTML seu, para o que nenhum layout resolve (um mapa anotado, uma montagem de documentos, uma tabela especial). Ele é medido como qualquer outro slide.
Campos `html` (obrigatório), `titulo` (para a trilha e para a navegação), `fonte`, `notas`. Se o HTML não trouxer a `fonte`, o motor a escreve no pé do slide e reserva espaço para ela.

Regras do HTML livre.
- Todo texto precisa de `data-txt` e de `data-role` (`titulo`, `corpo`, `legenda`, `rotulo`, `celula`, `numero`, `referencia`). Sem isso ele não é medido nem vai editável para o PPTX.
- Use as classes do motor quando servirem (`sk-titulo`, `sk-itens`, `sk-campo`, `sk-fig`, `sk-texto`).
- Num campo de cor seu, declare `--campo`, `--sobre-campo` e `--sobre-campo-2` no próprio elemento, para o contraste ficar certo.
- Nenhum endereço `http`. Para pôr uma imagem declarada em `imagens`, escreva `{{img:nome}}` dentro de um elemento com altura definida. O motor troca pela figura, com foco e animação.
- Animações por `data-a="sobe"` (ou outro nome de `08-movimento.md`) e `style="--d:300ms"`.

## Validações do construtor

`construir.py` para com erro quando um campo do slide tem nome errado (e sugere o certo), quando o texto usa pontuação ou palavra proibida por `estilo_texto`, quando a mesma obra aparece em mais de dois slides, quando uma imagem tem texto dentro sem `"documento": true`, quando falta campo obrigatório de layout, quando uma imagem não tem arquivo, proveniência, crédito ou alt, quando um gráfico ou número não tem fonte, quando um destaque não aparece literalmente no texto, quando há três layouts iguais seguidos, quando o HTML livre tem `http` e quando o modo verbatim encontra texto diferente da origem. Avisa quando falta nota, quando há mais de 5 itens, quando menos da metade dos slides tem imagem e quando um layout que pede visual ficou sem ele. Avisa também quando o layout é usado fora do que comporta: citação acima de 40 palavras, menos de 3 datas, `processo` fora de 3 a 5 passos, `galeria` fora de 2 a 4 imagens, `cartoes` fora de 3 ou 4, `tabela` acima de 4 colunas e 5 linhas, `numeros` com `torres` em unidades diferentes e `imagem-total` com documento.
