# 03. Direção de arte

A diretiva do autor pede o mais alto nível de apresentação. Na prática isso significa um deck com mundo próprio, em que cada slide tem uma ideia visual e o conjunto tem ritmo. Este arquivo diz como chegar lá com os recursos da skill.

## Comece pelo mundo, não pelo tema

Antes de escolher o tema, escreva `contrato.mundo` em uma frase concreta. Diga o objeto de referência (revista, museu, mesa de trabalho, sala escura), o papel, a tinta e o tipo de imagem.

Bom exemplo.
> Revista de história impressa, papel creme, grafite e bordô, títulos condensados em caixa alta, gravuras e fotografias de acervo em tamanho grande, imagens sem nada escrito por cima.

Mau exemplo.
> Visual moderno, limpo e profissional.

O segundo serve para qualquer deck, então não orienta nenhuma decisão. Depois escreva `contrato.primeira_tela`, descrevendo o que a plateia vê no primeiro segundo. Se você não consegue descrever a capa, ainda não tem direção.

## Os temas

Dezessete temas, todos com índice em `templates/temas.json` (fontes, arte, tom, perfis indicados e evitados). Os tokens de cor ficam em `templates/runtime/temas.css` e a arte que entra quando falta imagem fica em `ARTES` de `sk.js`.

| Tema | Títulos e corpo | Papel, tinta e acentos | Arte quando falta imagem |
|---|---|---|---|
| `tabuleiro` | Jost e Atkinson Hyperlegible Next | osso, azul-tinta, terracota, musgo, ocre | casas de tabuleiro e peões que pousam |
| `gravura` | Libre Caslon Text e Source Serif 4 | vergé, sépia, vermelho óxido, azul-ardósia | círculos concêntricos e hachuras |
| `editorial` | Oswald em caixa alta e Atkinson | creme, grafite, bordô | filetes e letra gigante vazada |
| `noturno` | Newsreader e Atkinson | verde-negro, marfim, ouro, garança | constelações que derivam |
| `datilografo` | Courier Prime e Atkinson | papel de fichário, azul-negro, carimbo vermelho | fichas sobrepostas e carimbo |
| `cartografico` | Spectral e Source Serif 4 | pergaminho, sépia, verde-floresta, marinho | meridianos, rotas e rosa dos ventos |
| `floresta` | Bricolage Grotesque e Public Sans | aveia, verde-escuro, terracota | curvas de nível |
| `risografia` | Archivo 800 e Archivo | creme e uma tinta ferrugem | pontos de meio-tom |
| `prancheta` | Barlow Condensed em caixa alta e Public Sans | pedra quente, grafite, azul de cópia | arcos de compasso, eixos e cotas |
| `porcelana` | Instrument Serif e Schibsted Grotesk | papel frio branco-azulado, marinho, azul suave | escamas de porcelana |
| `kraft` | Zilla Slab | papel pardo, marrom, vinho, azul-petróleo | etiquetas, barbante e carimbo postal |
| `lousa` | Bricolage Grotesque e Atkinson | verde-ardósia, giz creme, amarelo, azul claro | traços de giz, círculo e seta |
| `velino` | Spectral | pervinca escuro, amarelo pálido, ouro | linhas de guilhoché e filete duplo |
| `revista` | Newsreader (opsz 72) e Public Sans | branco, preto, vermelhão | colunas, disco e barras |
| `duna` | Source Serif 4 e Archivo | areia, ocre, terracota | dunas em camadas e sol |
| `civico` | Public Sans | cinza frio, azul institucional, verde musgo | quadras e avenida |
| `ardosia` | Schibsted Grotesk | cinza-azulado escuro, marfim, ocre | telhas de pedra sobrepostas |

Tinta sobre fundo, papel e cada campo passa de 4,5 para 1. Citações saem em redondo. `porcelana` é a variação sem creme e tem outra capa, com a imagem sangrando nos 60% de cima e título e subtítulo numa faixa embaixo. `civico` foi pensado para gestores públicos. `noturno`, `lousa`, `velino` e `ardosia` são escuros e pedem sala com pouca luz.

Nunca escolha sozinho. `amostra_temas.py PROJETO` lê `contrato.perfil`, `contrato.mundo`, o público e a sala, sugere três temas (um seguro, um ousado e um curinga) e gera a folha com três slides do próprio deck em cada um. `--temas a,b,c` mostra outros e `--todos` mostra todos, em folhas de seis temas (`temas_1.jpg`, `temas_2.jpg`). Mostre à pessoa e espere a escolha.

## Paletas e estilos

`"paleta": "nome"` no `deck.json` troca todas as cores de qualquer tema por um conjunto pronto de `templates/temas.json` (`terra`, `kraft`, `ardosia`, `porcelana`, `floresta`, `oceano`, `vinho`, `grafite`). As fontes e a arte continuam as do tema.

`"estilo": "nome"` carrega `PROJETO/estilos/NOME.json` ou `~/.slides-impecaveis/estilos/NOME.json`, um arquivo pequeno com `tema`, `paleta` e `ajustes_tema` que a pessoa reaproveita entre decks. O que estiver no próprio deck vence o estilo, e `ajustes_tema` vence a paleta.

## Ajustar um tema ao projeto

Quando a pessoa tem identidade própria (cores da instituição, um acento específico), use `ajustes_tema` no `deck.json`. Cada nome vira uma variável CSS do tema.

```json
"ajustes_tema": {
  "acento": "#7A1F2B",
  "acento2": "#3B6593",
  "campos": "#1F2A44,#7A1F2B,#3B6593,#5F7254"
}
```

Variáveis úteis são `fundo`, `papel`, `tinta`, `tinta2`, `acento`, `acento2`, `sobre-acento`, `campos`, `marca`, `raio` e `raio-img`. O `verificar.py` mede o contraste de novo em cada slide. Não troque famílias de fonte por aqui, porque só as fontes do tema vão embutidas.

## Uma ideia visual por slide

Para cada slide, complete a frase "a plateia vê ___ e entende ___". Se a primeira lacuna for "uma lista", procure outra resposta. Quase todo conteúdo tem uma forma visual própria.

| Se o conteúdo é | Mostre |
|---|---|
| um lugar | o mapa ou a fotografia aérea daquele lugar, em tamanho grande |
| uma pessoa | o retrato dela, ou a obra dela, ao lado da citação |
| um documento | a folha de rosto ou a página original, recortada no trecho que importa |
| uma mudança no tempo | linha do tempo com a imagem da época em faixa |
| uma quantidade | o número sozinho, enorme, com a fonte embaixo |
| uma comparação de valores | barras com o caso em discussão destacado no acento |
| uma parte de um todo | proporção com figuras (3 de 10) |
| uma relação causal | cadeia, ciclo ou balança |
| dois modelos | comparação com uma imagem por coluna |

Imagem decorativa, sem relação com a ideia, piora o slide. Se não existe imagem real pertinente, use gráfico, diagrama ou a arte do tema, que foi desenhada para não competir com o texto.

## Composição

- **Sangria.** Imagens encostam na borda do slide. Moldura fina em volta de foto pequena parece documento de escritório.
- **Escala com contraste.** Um elemento domina cada slide. Título enorme com imagem média, ou imagem enorme com texto em painel. Dois elementos do mesmo tamanho disputam o olhar.
- **Grade.** O palco tem margens de 96 px nas laterais e 64 px em cima e embaixo. Texto nunca encosta na margem, imagem pode atravessá-la.
- **Campos de cor.** Cada seção do deck tem um campo de cor (lista `--campos`). A capa, a abertura de seção, a pergunta e a citação usam o campo inteiro. Isso dá identidade ao bloco e mostra à plateia onde ela está.
- **Trilha.** A faixa de 12 px no pé do slide mostra o andamento com as cores das seções. Ela substitui o número do slide, que não aparece na tela.
- **Destaques.** Use `destaques` para marcar no máximo duas expressões por slide. Marca demais vira ruído.

## Bom senso com o espaço

Medir fonte e ocupação não basta. O avaliador e quem constrói olham também como o espaço livre foi distribuído. A folha `exemplos/referencias/espaco-antes-depois.jpg` mostra quatro casos reais, com o slide como saiu e como o avaliador faria.

1. **Menos linhas no título, usando a largura que existe.** Se o título cabe em duas linhas ocupando a coluna inteira, ele não deve ir para três. "A DUPLA SEGURANÇA / DE MADISON" é melhor que "A DUPLA / SEGURANÇA / DE MADISON". O motor reduz o título de três ou mais linhas em até 12% quando isso tira uma linha inteira.
2. **Nomes compostos não se partem.** "ESTADOS UNIDOS, / 1787" é melhor que "ESTADOS / UNIDOS, 1787". Vale para nomes de países, instituições, leis e pessoas.
3. **Respiro entre título e texto.** Quando sobra altura, o espaço vai para o intervalo entre os blocos, e não para uma faixa vazia embaixo. O título se destaca melhor e o slide fica mais leve.
4. **Blocos distribuídos na altura.** Na capa, título no alto, subtítulo no meio e autoria embaixo, em vez de título e subtítulo amontoados no centro com um buraco antes da autoria.
5. **Margens com propósito.** O título pode usar a largura da coluna até perto do visual. Folga grande à direita do título, com linhas quebrando antes da hora, é desperdício.

## Ritmo do deck

Pense o deck como uma sequência de cenas.

1. A capa e a primeira pergunta abrem com imagem em tela cheia ou campo de cor.
2. Cada bloco começa com `secao`, que mostra o mapa do deck e o lugar atual.
3. Dentro do bloco, alterne um slide denso (tabela, gráfico, processo) com um slide de respiro (citação, número, imagem-total, afirmação).
4. Alterne o lado do texto (`lado` direita e esquerda) entre slides vizinhos do mesmo tipo.
5. Perto do fim, uma `afirmacao` com a tese, depois `fechamento` e `referencias`.

`construir.py` recusa três layouts iguais em sequência e `verificar.py` recusa slides vizinhos quase idênticos na captura. Variação mínima de 10 layouts num deck de 20 ou mais slides.

## Tipografia

- Títulos usam a família de título do tema, com peso alto e entrelinha curta. Títulos são afirmações, não rótulos.
- Corpo usa a família de corpo do tema, sempre com peso 400 ou mais, escolhida para leitura a distância.
- Números grandes usam a família de título, com algarismos tabulares quando há comparação.
- Itálico só em títulos de obras e termos estrangeiros. Citações ficam em redondo.
- Caixa alta só nos temas `editorial` e `prancheta`, e só nos títulos.
- Nada abaixo de 28 px. Ver `07-legibilidade-e-ocupacao.md`.

## O que nunca fazer

- Rótulo pequeno em caixa alta acima do título ("CAPÍTULO 2", "INTRODUÇÃO").
- Número do slide na tela.
- Texto em degradê, brilho, sombra dura deslocada, vidro fosco.
- Três cartões iguais com ícone em cima, sem motivo de conteúdo.
- Ícones feitos de caractere ou emoji.
- Foto de banco de imagens com gente sorrindo para a câmera.
- Robô, cérebro, circuito, holograma, lâmpada, aperto de mão, alvo com flecha, "IA" como elemento visual.
- Imagem gerada por IA no lugar de documento ou fotografia, ou com texto dentro.
- Animação com quique, giro ou elasticidade.
- Fundo com padrão que compete com o texto.

## Teste final de direção

Olhe as folhas de contato em `verificacao/folhas/`. Para cada slide, pergunte se ele poderia estar em outro deck sem mudar nada. Se poderia, ele ainda não tem ideia visual própria. Depois olhe as folhas em conjunto e pergunte se dá para reconhecer o deck pela miniatura. Se não dá, o mundo do contrato não chegou à tela.
