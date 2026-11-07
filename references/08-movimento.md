# 08. Movimento

Movimento bom mostra a ordem de leitura do slide, combina com o tema e nunca se mexe sem motivo.

## Princípios

1. **O estado final é o padrão.** O slide completo existe sem animação. Tudo que se move depende da classe `sk-mov`, ligada só no navegador. PDF, PPTX, impressão e verificação usam `?final` ou `SK.final(true)` e recebem o slide pronto, sem transição nem morph.
2. **A entrada conta a ordem de leitura.** Visual ou título primeiro, corpo depois. Intervalos de 110 a 180 ms entre peças.
3. **Uma ideia de movimento por slide.** Não empilhe efeitos.
4. **Curvas que só desaceleram.** Nada de quique, elástico ou giro. A verificação reprova curva que passa do alvo.
5. **Movimento reduzido.** Quem pede menos movimento no sistema continua vendo as entradas, mas só com opacidade. Sem deslocamento, zoom, desfoque ou morph.

## Vocabulário de entrada (`data-a`)

Cada elemento leva `data-a="nome"` e um atraso `style="--d:300ms"`.

| Nome | O que faz | Uso típico |
|---|---|---|
| `sobe` | aparece subindo 42 px (muda com a intensidade) | títulos, itens, cartões |
| `aparece` | só opacidade | legendas, rótulos |
| `entra-esq`, `entra-dir` | chega de lado (42 px) com opacidade | colunas da `comparacao`, lados do `dividido` |
| `revela`, `revela-baixo`, `cortina` | descobre da esquerda, de baixo, de cima | imagem de seção, galeria, campo da capa |
| `iris` | abre um círculo a partir de `--ox`/`--oy` (padrão 50% 50%) | imagem da `pergunta` |
| `foco` | sai do desfoque | citação, tabela, cartão de gráfico |
| `cresce-y`, `cresce-x` | cresce da base ou da esquerda | barras, linha do tempo |
| `traco` | desenha o contorno | linhas de gráfico, setas, ciclos |
| `pousa` | desce e pousa | peças do tabuleiro, fichas |
| `datilografa` | o título aparece letra a letra | ligado sozinho no tema `datilografo`, em título de uma linha só |

Para `traco`, use `pathLength="1"` no SVG e nada mais. O motor faz isso nos gráficos e diagramas. SVG antigo com `--comp` continua funcionando.

Imagens animadas ganham uma aproximação lenta (de 1,12 para 1). Números do layout `numero` contam até o valor.

## Troca de slide (`transicao`)

O slide que sai fica parado e opaco embaixo. O que entra aparece por cima em 0,32 s. O fundo da página nunca aparece entre os dois. Escolha uma para o deck inteiro e troque só em pontos marcados.

| Valor | O que faz | Quando |
|---|---|---|
| `dissolve` | só opacidade (padrão) | qualquer deck |
| `sobe` | opacidade e 6 px de subida | aulas, ritmo de "próxima ideia" |
| `assenta` | 12 px e desfoque de 4 px | capa |
| `floresce` | escala de 0,97 para 1 | imagem que domina o slide |
| `respiro` | o anterior some, o fundo do tema aparece e a seção entra | só antes de um slide `secao`, uma ou duas vezes por deck |

```json
{ "transicao": "sobe",
  "slides": [ { "layout": "capa", "transicao": "assenta" },
              { "layout": "secao", "transicao": "respiro" } ] }
```

A transição de um slide vale ao entrar nele, para frente e para trás. `construir.py` recusa valores fora da lista e avisa quando `respiro` não está numa seção.

## Morph

Quando o mesmo objeto aparece em dois slides vizinhos, ele desliza e muda de tamanho do lugar antigo ao novo, em vez de sumir e voltar. Use para continuidade real (a mesma gravura que sai do lado e vira faixa, o mesmo mapa que cresce). Um ou dois por bloco bastam.

```json
{ "layout": "secao", "imagem": "plano-washington-1792", "morph": true },
{ "layout": "linha-do-tempo", "imagem": "plano-washington-1792", "titulo": "Da liga à União" }
```

`"morph": true` liga a imagem principal à do slide seguinte que usar a mesma imagem. Para ligar imagens principais diferentes (um detalhe e a obra inteira), ponha o mesmo texto nos dois slides, como `"morph": "mapa"`. No layout `livre`, ponha `data-morph="id"` em qualquer elemento dos dois slides (uma figura, um número).

O motor usa `document.startViewTransition` quando o navegador tem. Sem ele, faz FLIP com Web Animations. Com movimento reduzido vira `dissolve`. Em `?final` nada acontece.

## Etapas

`"etapas": true` faz o slide se montar diante da plateia, uma peça a cada seta. Primeiro os itens de texto, depois as peças do gráfico ou do diagrama. A seta para trás esconde a última peça revelada antes de voltar de slide. No PDF, no PPTX e na verificação tudo aparece de uma vez.

| Visual | Uma etapa é |
|---|---|
| `barras`, `barras-h`, `pontos`, `halteres`, `empilhadas` | uma barra ou linha com seu rótulo e seu valor |
| `linha` | uma série inteira, depois cada anotação |
| `barras` com `anotacao` | todas as barras e, por último, a anotação |
| `dispersao` | cada ponto com nome (os pontos sem nome ficam desde o início) |
| `cadeia`, `ciclo`, `centro` | uma caixa, depois a seta que sai dela |
| `camadas`, `funil`, `matriz` | uma camada, uma faixa, um quadrante |
| `balanca` | um prato, o outro e a frase do centro |
| `iceberg` | o que está acima da água, depois cada item submerso |
| `venn` | cada conjunto com seu nome e, no fim, a interseção |

Eixos, grades e títulos ficam desde o início, para a plateia saber onde as peças vão cair. Cada peça revelada refaz a própria animação (a barra cresce, depois o número aparece). Use em slides de argumento, em que a ordem importa (a comparação que vira, o ciclo que fecha). Deixe de fora quando o visual é só ilustração, porque cada etapa custa um clique de quem apresenta.

```json
{ "layout": "diagrama", "titulo": "Como a federação se fecha", "etapas": true,
  "diagrama": { "tipo": "ciclo", "nos": ["União cobra", "Estados executam", "Municípios cobram", "União repassa"] } }
```

Em HTML livre, ponha `data-etapa="b000"`, `"b001"`, `"b002"` nas peças, na ordem em que devem entrar. Peças com o mesmo valor entram juntas.

## Intensidade

`"intensidade"` regula o quanto as coisas se mexem, sem trocar o vocabulário. Vale para o deck e pode mudar num slide.

| Valor | Deslocamento | Duração | Atrasos | Zoom das imagens | Quando |
|---|---|---|---|---|---|
| `sobrio` | 16 px | 70% | 55% | 1,03 | banca, gestores, sala grande com muita leitura |
| `padrao` | 42 px | 100% | 100% | 1,12 | aula e palestra (o padrão) |
| `vivo` | 72 px | 115% | 130% | 1,20 | abertura, público jovem, slide de impacto |

```json
{ "intensidade": "sobrio",
  "slides": [ { "layout": "capa", "intensidade": "vivo" } ] }
```

O estado final é o mesmo nas três. `construir.py` recusa outro valor. Quem pede menos movimento no sistema continua só com opacidade, em qualquer intensidade. Combine com o perfil (`banca` e `gestores` pedem `sobrio`) e evite `vivo` no deck inteiro, porque o efeito se gasta.

## Teclas de palco

| Tecla | Ação |
|---|---|
| setas, espaço, clique | avança ou volta (etapas primeiro) |
| número e Enter | salta para o slide |
| B (ou ponto) / W | tela preta / tela branca |
| L | ponteiro laser na cor de acento |
| P | janela do apresentador |
| ? | ajuda |

A janela do apresentador abre o mesmo arquivo com `?apresentador`. Mostra notas, o próximo slide em miniatura, o cronômetro (R zera), o tempo previsto somado pelos campos `minutos` e as marcas `cortável` e `apêndice`. As teclas da janela comandam o deck. As imagens do slide seguinte são decodificadas antes da troca.

## HTML livre

Use o mesmo vocabulário.

```html
<h2 class="sk-titulo" data-role="titulo" data-txt data-a="sobe" style="--d:80ms">Quem cuida de quê</h2>
<div style="height:640px" data-morph="planta">{{img:plano-washington-1792}}</div>
```

## O que não fazer

- Seis transições diferentes num deck. Uma da casa, no máximo outra para capa e o `respiro` nas seções.
- Transição longa. Acima de 0,35 s parece vídeo.
- Saída que some (fora do `respiro`). O fundo aparece e o corte pisca.
- `@keyframes` próprios sem necessidade. Se escrever, o estado sem animação precisa ser o completo.
- Morph de enfeite ou entre slides que não são vizinhos.
- Movimento contínuo competindo com texto (só as partículas do `noturno`, devagar).

## Conferir

A verificação usa o estado final e não vê o movimento. Abra o HTML, passe slide por slide e confira a ordem de entrada, se nada pisca, se o morph cai no lugar e se a última peça entra antes de 2 s. O avaliador humano confirma isso na condição "movimento visto no navegador".
