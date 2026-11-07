# 06. Gráficos e diagramas

Gráficos e diagramas são desenhados em SVG pelo motor, nas cores e fontes do tema, com animação de entrada e rótulos que passam no piso de 28 px. Você só escreve os dados.

## Antes de fazer um gráfico

- O dado existe e tem fonte que você leu. Escreva a fonte em `fonte`. Ela vai para a tecla I e para as notas, e só aparece no slide se a pessoa pedir (`fonte_visivel`). Sem fonte o construtor recusa.
- O gráfico responde a uma pergunta que está no título. "Quantas unidades formam cada federação" pede barras. "Como a receita mudou desde 1988" pede linha.
- Um destaque por gráfico, no caso que você discute (`destaque`). O resto fica na segunda cor do tema.
- Poucas categorias. Até 8 barras, até 12 pontos por linha, até 2 séries.
- Se o número é um só, use o layout `numero`. Se é uma parte de um todo pequeno, use `proporcao`.

Nunca invente, arredonde para impressionar ou complete série faltante. Se o dado tem limite (ano, recorte, método), diga na fonte.

## Tipos de gráfico

Os gráficos entram no layout `grafico` (com texto ao lado) ou como visual de `dividido`.

### Barras verticais
```json
"grafico": {"tipo": "barras", "rotulos": ["2000", "2010", "2022"], "valores": [5507, 5565, 5570], "destaque": [2]},
"fonte": "IBGE, Censos Demográficos de 2000, 2010 e 2022."
```

### Barras horizontais
Melhor quando os rótulos são nomes longos.
```json
"grafico": {"tipo": "barras-h", "rotulos": ["Estados Unidos", "México", "Índia", "Brasil"], "valores": [50, 31, 28, 26], "destaque": [3]},
"fonte": "Constituições nacionais (2025). Só unidades de primeiro nível."
```

### Linha
Uma ou duas séries ao longo do tempo. O último valor de cada série aparece escrito. Para duas séries, use `series` com `{nome, valores}` em cada uma.
```json
"grafico": {"tipo": "linha", "rotulos": ["1970", "1980", "1991", "2000", "2010", "2022"], "valores": [93.1, 119.0, 146.8, 169.8, 190.8, 203.1], "unidade": " mi"},
"fonte": "IBGE, Censos Demográficos. População residente em milhões."
```

### Proporção
Figuras de pessoas, k de n preenchidas. Para "3 em cada 10".
```json
"grafico": {"tipo": "proporcao", "n": 10, "k": 3, "texto": "3 em cada 10"}
```
Use somente quando a proporção real for essa. Os valores acima mostram o formato.

| Campo | Uso |
|---|---|
| `tipo` | `barras`, `barras-h`, `linha`, `proporcao` |
| `rotulos`, `valores` | listas do mesmo tamanho |
| `series` | só em `linha`. Lista de `{nome, valores}` |
| `destaque` | índices em destaque, na cor de acento |
| `unidade` | sufixo do valor (`%`, ` mi`, ` km`) |
| `formato` | molde do valor, com `{v}` no lugar do número (`"R$ {v} bi"`) |
| `max`, `min` | fixam a escala, para comparar gráficos vizinhos |
| `n`, `k`, `colunas`, `texto` | só em `proporcao` |

### Tipos da extensão (`templates/runtime/sk-ext-graficos.js`)

Os nomes das séries são escritos no próprio gráfico, nunca numa caixa de legenda. Todos aceitam `unidade`, `formato`, `casas` (decimais fixos) e `destaque`, e entram em `grafico`, `dividido` e `evidencia`.

| Tipo | Para mostrar | Campos |
|---|---|---|
| `pontos` | estimativas com intervalo de confiança, na horizontal | `rotulos`, `valores`, `inferior`, `superior`, `referencia` (linha tracejada, `true` para o zero), `eixo`, `min`, `max`. Até 8 |
| `halteres` | antes e depois por categoria | `rotulos`, `antes`, `depois`, `nomes` (`["2010", "2022"]`), `min`, `max`. Até 7 |
| `empilhadas` | composição de cada barra | `rotulos`, `series` (de 2 a 6 `{nome, valores}`), `percentual` (padrão `true`, cada barra soma 100). Com `false`, valores absolutos e total no fim. Até 6 barras |
| `dispersao` | relação entre duas medidas | `pontos` (`{x, y, rotulo}`, até 6 com rótulo, que ganham destaque), `eixo_x`, `eixo_y`, `unidade_x`, `unidade_y`, `min_x`, `max_x`, `min_y`, `max_y` |
| `linha` | a nativa, mais `anotacoes` e `trecho_final` | `anotacoes` (`{i, texto, lado}`, frase de até 8 palavras presa ao ponto `i`, `lado` `acima` ou `abaixo`). `trecho_final: n` pinta no acento os últimos n segmentos (só com uma série) |
| `barras` | a nativa, mais `anotacao` | `anotacao` (texto ou `{i, texto}`) presa à barra em destaque. A escala abre espaço para ela no alto |

```json
"grafico": {"tipo": "pontos", "rotulos": ["Lula, pesquisa", "Lula, urnas"], "valores": [52, 50.9], "inferior": [50, 50.9], "superior": [54, 50.9], "referencia": 50, "unidade": "%"},
"fonte": "Datafolha, 28 e 29/10/2022, registro BR-08297/2022. TSE, 2º turno de 2022."
```
```json
"grafico": {"tipo": "halteres", "rotulos": ["Norte", "Sudeste"], "antes": [8.5, 41.8], "depois": [25.9, 14.8], "nomes": ["população", "Senado"], "unidade": "%", "casas": 1}
```
```json
"grafico": {"tipo": "empilhadas", "rotulos": ["1º turno", "2º turno"], "casas": 1,
            "series": [{"nome": "Lula", "valores": [57259504, 60345999]}, {"nome": "Bolsonaro", "valores": [51072345, 58206354]}]}
```
```json
"grafico": {"tipo": "dispersao", "eixo_x": "habitantes (milhões)", "eixo_y": "deputados",
            "pontos": [{"x": 44.4, "y": 70, "rotulo": "São Paulo"}, {"x": 0.6, "y": 8, "rotulo": "Roraima"}, {"x": 20.5, "y": 53}]}
```

## Diagramas

Diagrama mostra relação, não decoração. Use quando a ideia é uma sequência causal, um ciclo, um centro com partes, camadas ou um equilíbrio entre dois lados. Os nós são curtos (até 4 palavras).

```json
"diagrama": {"tipo": "cadeia", "nos": ["Povo", "União e estados", "Três poderes em cada um"], "destaque": [0]}
```

| Tipo | Ideia | Nós |
|---|---|---|
| `cadeia` | A leva a B, que leva a C. Fica vertical quando a área é alta | 2 a 4 |
| `ciclo` | etapas que voltam ao começo | 3 a 6 |
| `centro` | um conceito no meio (`centro`) e partes ao redor | 3 a 6 |
| `camadas` | níveis contidos uns nos outros, do maior para o menor | 2 a 4 |
| `balanca` | dois lados em tensão. `lado_forte` (0 ou 1) inclina o destaque, `centro` escreve o critério embaixo | 2 |
| `funil` | etapas que estreitam. `etapas` com `{rotulo, valor}` ou `nos`. A largura é simbólica, não proporcional | 3 a 5 |
| `iceberg` | o visível e o que sustenta. `acima` (até 2) e `abaixo` (até 3), com a linha d'água que se desenha | 1 a 5 |
| `matriz` | 2x2. `eixo_x` e `eixo_y` com `[baixo, alto]`, `nome_x`, `nome_y`, `quadrantes` na ordem de leitura (alto à esquerda, alto à direita, baixo à esquerda, baixo à direita), `destaque` (0 a 3) | 4 |
| `venn` | conjuntos que se cruzam. `conjuntos` (até 2 palavras cada) e `intersecao` (até 3). Com 3 conjuntos fica mais alto e enche melhor a área | 2 ou 3 |

```json
"diagrama": {"tipo": "matriz", "nome_x": "quem executa", "nome_y": "quem regula", "eixo_x": ["União", "local"], "eixo_y": ["local", "União"],
             "quadrantes": ["Previdência social", "SUS e educação básica", "Combinação rara", "Transporte urbano"], "destaque": 1}
```

Os diagramas entram no layout `diagrama` (texto à esquerda, diagrama grande à direita) ou como visual de `dividido`, onde ganham o campo de cor da seção.

## Quando nenhum tipo serve

Use o layout `livre` e escreva o SVG você mesmo. Marque cada texto com `data-txt` e `data-role="rotulo"` e use tamanho de fonte que resulte em pelo menos 28 px no palco. A verificação mede texto SVG pela escala real (`getScreenCTM`), então um rótulo de 40 unidades num SVG reduzido à metade aparece como 20 px e reprova.

## Checagem

- `verificar.py` mede os rótulos dos gráficos como qualquer texto.
- Olhe a folha de contato. Barra com rótulo encostado no valor, linha com rótulo sobre o ponto, nó com texto quebrado em três linhas são defeitos que o avaliador vai marcar.
- Abra o HTML e veja a animação. As barras crescem do eixo, a linha se desenha da esquerda para a direita, os nós entram em ordem.
