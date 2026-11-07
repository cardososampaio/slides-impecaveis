# 05. Imagens reais

A diretiva pede "somente informações reais, imagens e tudo que for pertinente". Toda imagem do deck é um objeto que existe (fotografia, gravura, mapa, documento, pintura, imagem científica) e carrega origem, licença e crédito.

## Ordem de preferência

1. **Imagem fornecida pela pessoa** (foto própria, figura de um artigo dela, material da instituição). `imagens.py baixar local ARQUIVO --licenca "..." --autor "..." --titulo "..."`.
2. **Acervos abertos com interface de busca**, já suportados pelo script.
   - `loc` Library of Congress. Fotografias, gravuras, mapas, cartazes, livros de pranchas. Ótima para história política, cidades e América.
   - `met` Metropolitan Museum, só objetos marcados como domínio público. Pinturas, gravuras, objetos.
   - `nasa` NASA Image and Video Library. Terra vista do espaço, cidades à noite, ciência.
   - `ia` Internet Archive. Atlas e livros ilustrados escaneados.
   - `commons` Wikimedia Commons. Licença por arquivo. Pode responder 429 a muitas requisições seguidas.
   - `openverse` Openverse, índice de imagens abertas (Flickr, Commons, museus). A busca só lista CC0, Public Domain Mark, CC BY e CC BY-SA. Fotos do Flickr chegam em geral com 1024 px, boas para painel e coluna.
3. **Acervos sem interface no script**, baixados com `baixar url` informando licença, autor e página de origem. Exemplos úteis para o Brasil são Brasiliana Fotográfica, Biblioteca Nacional Digital, Arquivo Nacional, IBGE (mapas e fotos históricas), Agência Brasil (licença Creative Commons indicada na página) e Portal da Câmara e do Senado. Leia a licença na página de cada item.
4. **Imagem gerada por IA**, somente como ilustração declarada, nunca como documento, retrato ou fotografia de algo real, e nunca com texto dentro. O crédito diz "ilustração gerada por IA". Prefira a arte do tema a isso.

## Como buscar

Busque o objeto concreto, não a categoria. "Capitol 1846 engraving" encontra algo que "government building" nunca encontra. Pense no que a plateia reconheceria (o prédio, o documento, o mapa, o rosto) e use os termos do acervo, que em geral estão em inglês.

```
python3 scripts/imagens.py buscar loc "federalist papers 1788" --n 12
python3 scripts/imagens.py buscar nasa "rio de janeiro" --n 12
python3 scripts/imagens.py buscar met "engraving washington" --n 12
```

A busca lista identificador, título, data e um resumo dos direitos. Baixe uma por vez.

```
python3 scripts/imagens.py baixar loc https://www.loc.gov/item/2013646770/ --saida PROJETO/assets/brutas
python3 scripts/imagens.py baixar loc 09021562 --pagina 11 --saida PROJETO/assets/brutas
python3 scripts/imagens.py baixar nasa STS065-88-001 --saida PROJETO/assets/brutas
```

Na Library of Congress, quando o maior JPEG tem menos de 1800 px, o script baixa o TIFF mestre (até 150 MB) e converte. Para livros e álbuns use `--pagina`, porque a primeira imagem costuma ser a capa, a lombada ou uma carta de cores.

## Olhe antes de escolher

```
python3 scripts/imagens.py olhar PROJETO/assets/brutas
```

Gera `_candidatas.jpg` com todas as brutas, nome e tamanho. Abra a folha e olhe de verdade. O título no acervo engana com frequência (uma "vista da cidade" que é um mapa, um "retrato" que é a página de rosto com o retrato pequeno). Descarte o que estiver borrado, manchado, cortado ou com carimbo de biblioteca em cima do assunto.

## Direitos

Leia o campo `direitos` de cada `.json`.

| O acervo diz | O que fazer |
|---|---|
| "No known restrictions on publication", domínio público, CC0, Public Domain Mark | usar com crédito |
| CC BY, CC BY-SA | usar com crédito completo (autor, título, licença) |
| "Rights status not evaluated", "publication may be restricted", "all rights reserved" | não usar |
| sem informação | não usar, a não ser que a pessoa garanta o direito por escrito |

Ao baixar, o script classifica a licença em `classe_licenca` no `.json`, para todos os acervos.

| Classe | Licenças | O que acontece |
|---|---|---|
| `livre` | domínio público, CC0, Public Domain Mark, sem restrições conhecidas | baixa |
| `credito` | CC BY, CC BY-SA, cedida ou autorizada pela pessoa | baixa, e o crédito completo é obrigatório |
| `recusada` | NC, ND, todos os direitos reservados, licença desconhecida | apaga o arquivo e explica o motivo |

Licença desconhecida se resolve lendo a página do item e baixando de novo com `--licenca "TEXTO"`, que registra a licença como declarada por você. `--aceitar-nc` libera licença não comercial só para aula sem fins comerciais e grava `aceite_nc` no `.json`. Diga isso à pessoa.

Quando o script não consegue ler a licença, ele grava `VERIFICAR` no campo `licenca`, e o construtor avisa até você registrar a decisão no `.json` (veja os exemplos em `exemplos/federalismo/assets/`). Obras anteriores a 1900 costumam ser de domínio público, mas a fotografia de uma pintura pode ter direitos próprios em alguns países. Na dúvida, prefira o acervo que declara domínio público.

## Tratar

```
python3 scripts/imagens.py tratar BRUTA.jpg PROJETO/assets/nome.webp --proporcao 16:9 --foco 0.5,0.4
```

| Opção | Uso |
|---|---|
| `--proporcao` | recorta na proporção da área do layout (ver `04-layouts.md`). Sem ela, a imagem fica inteira e o `foco` do deck faz o recorte na tela |
| `--foco x,y` | ponto que fica no recorte, de 0 a 1 |
| `--cortar x0,y0,x1,y1` | tira bordas, molduras, cartões de catálogo, legendas impressas e carimbos antes de tudo |
| `--max` | lado maior em px (padrão 2200) |
| `--cinza`, `--duotom "#1C2632,#F2EBDD"` | uniformiza fotos de origens diferentes no mesmo tom do tema |

O script grava `nome.webp.json` com a proveniência da bruta e a lista de transformações. Sem esse arquivo o construtor recusa a imagem. Imagem com menos de 1600 px de largura recebe aviso. Ela serve para painel e coluna, não para tela cheia.

## Declarar no deck

```json
"capitolio-1846": {
  "arquivo": "assets/capitolio-1846.webp",
  "foco": "72% 62%",
  "legenda": "<i>Capitol of the United States</i>, gravura, 1846 · Library of Congress",
  "credito": "Capitol of the United States, Washington, gravura, 1846. Library of Congress, Prints and Photographs Division. Sem restrições conhecidas de publicação.",
  "alt": "Gravura do Capitólio dos Estados Unidos em 1846, com a cúpula antiga e árvores à frente."
}
```

- `legenda` fica guardada e só aparece sobre a imagem quando a pessoa pede (`"legendas": true` no slide). Por padrão a imagem fica limpa. Escreva curta, no formato de museu (título, técnica, data, acervo).
- `credito` vai completo para a tela de créditos (tecla I) e para as notas do PPTX.
- `alt` descreve o que se vê, para leitor de tela e para o PPTX.

## Quando o modelo não enxerga imagens

O `teste_visao.py` diz se a sessão vê imagens. Sem visão, a escolha é feita pelos metadados do acervo, e as regras ficam mais estreitas.

- **Foto só para assunto concreto.** Um lugar, uma pessoa nomeada, um documento, um objeto, uma época. Número, risco, custo, método e conceito vão para `numero`, gráfico, diagrama ou a arte do tema. Biblioteca, estante e sala de leitura não ilustram ideia nenhuma.
- **Poucas e boas.** De 6 a 10 fotos num deck de 25 slides. O resto em gráfico, diagrama e arte.
- **Desconfie do título.** Títulos com "advertisement", "poster", "card", "page", "letter", "catalog", "screenshot" quase sempre trazem texto dentro. Evite.
- **`alt` diz quem ou o que aparece.** É dele que o construtor tira a marca de retrato.

## O que o construtor confere nas imagens

- **Texto dentro.** Com Tesseract instalado, lê as palavras. Sem ele, reconhece telas, figuras e diagramas pelo desenho. Quatro palavras legíveis ou cara de figura recusam a imagem. O resultado fica guardado no `.webp.json`, então a leitura acontece uma vez por arquivo. Quando a página é o próprio assunto (folha de rosto, mapa histórico, cartaz de época), marque `"documento": true` na imagem.
- **Mesma obra repetida.** Imagens com a mesma origem (URL ou arquivo bruto) ou o mesmo desenho contam como uma só, mesmo com nomes e recortes diferentes. No máximo dois slides.
- **Retrato.** Imagens cujo `alt`, legenda ou título indicam pessoa (retrato, homem, mulher, operadora, sentado, portrait), ou em que o OpenCV acha um rosto, ganham `"pessoa": true`. O motor centra o recorte no terço de cima e a verificação recusa retrato em faixa estreita (proporção acima de 3 por 1), onde o rosto sai cortado. Para desligar numa imagem, declare `"pessoa": false`.

## Erros comuns

- Imagem bonita sem relação com o slide. Troque por uma que mostre o assunto, ou use a arte do tema.
- A mesma imagem em muitos slides. Uma imagem pode voltar no fechamento, para amarrar com a capa. O construtor recusa a terceira vez.
- Fotos de origens muito diferentes lado a lado (uma colorida e saturada, outra sépia). Use `--cinza` ou `--duotom` para unificar.
- Rosto ou assunto principal cortado pelo painel de texto. Ajuste `foco` ou `foco_imagem`, ou troque o `lado`.
- Mapa ou documento recortado como se fosse foto. Use `"conter": true` para mostrar inteiro.

## Paleta a partir de uma referência

Quando a pessoa traz um modelo da instituição (PDF, PPTX, uma imagem ou um HTML), extraia as cores dele.

```
python3 scripts/extrair_estilo.py modelo.pdf --nome instituto
```

O script agrupa as cores dominantes, escolhe fundo, tinta, acentos e campos com contraste de 4,5:1 conferido, propõe o tema mais próximo e grava `~/.slides-impecaveis/estilos/instituto.json` e uma amostra `instituto.png`. No `deck.json`, use `"estilo": "instituto"` ou cole o trecho que ele imprime. Mostre a amostra à pessoa antes. Fontes não são extraídas.
