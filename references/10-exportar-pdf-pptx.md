# 10. Exportar para PDF e PPTX

O HTML é a obra principal. PDF e PPTX saem dele, no estado final das animações, e só como versão final depois que a trava libera.

## PDF

```
python3 scripts/exportar_pdf.py PROJETO              # versão final, exige LIBERADO
python3 scripts/exportar_pdf.py PROJETO --rascunho   # revisão, cada página leva a tarja RASCUNHO
```

- Uma página de 1920x1080 px por slide, com texto vetorial e fontes embutidas pelo Chromium. O texto pode ser selecionado e buscado.
- As imagens WebP são convertidas para JPEG antes da impressão, o que mantém o arquivo pequeno (o exemplo de 19 slides fica perto de 6 MB).
- Etapas aparecem todas, partículas e animações ficam paradas no estado final.
- O script confere se o número de páginas é igual ao de slides.

Saída em `dist/NOME.pdf` (ou `dist/NOME-RASCUNHO.pdf`).

## PPTX

```
python3 scripts/exportar_pptx.py PROJETO                     # híbrido, exige LIBERADO
python3 scripts/exportar_pptx.py PROJETO --conferir          # e compara com o HTML pelo LibreOffice
python3 scripts/exportar_pptx.py PROJETO --modo imagem       # cada slide vira uma imagem fiel
python3 scripts/exportar_pptx.py PROJETO --fontes-seguras    # Arial, Georgia e Courier New no lugar das fontes do tema
python3 scripts/exportar_pptx.py PROJETO --rascunho          # revisão, sem a trava
python3 scripts/exportar_pptx.py PROJETO --dados-nativos     # gráficos e tabelas editáveis no PowerPoint
python3 scripts/exportar_pptx.py PROJETO --max-mb 25         # reduz a qualidade dos fundos até caber
python3 scripts/exportar_pptx.py PROJETO --sem-transicao     # sem o esmaecimento entre slides
```

### Modo híbrido (padrão)

Cada slide é fotografado sem o texto. Imagens, campos de cor, gráficos, diagramas, marcadores e ornamentos ficam numa imagem de fundo. Todo texto marcado com `data-txt` volta como caixa de texto nativa do PowerPoint, na mesma posição, tamanho, peso, cor, alinhamento e quebra de linha do HTML.

- 1 px do palco vira 6350 EMU, então a lâmina tem 13,33 x 7,5 polegadas e 2 px equivalem a 1 pt.
- O título vai no espaço reservado de título, o que ajuda leitores de tela e o modo de estrutura.
- As quebras de linha do HTML viram quebras explícitas, para o texto não refluir diferente.
- As notas do apresentador e os créditos das imagens entram nas notas de cada slide.
- A imagem de fundo leva texto alternativo.
- Rótulos dentro de gráficos e diagramas SVG ficam na imagem de fundo e não são editáveis, salvo com `--dados-nativos` (abaixo).
- Cada slide entra com esmaecimento nativo de 0,5 s. `--sem-transicao` tira.

### Gráficos e tabelas nativos

Com `--dados-nativos`, os slides `grafico` dos tipos `barras`, `barras-h` e `linha` viram gráficos do PowerPoint e os slides `tabela` viram tabelas do PowerPoint, com os dados do `deck.json`, as cores do tema e rótulos de 14 pt ou mais. Eles ocupam a posição do elemento no HTML, que some da imagem de fundo. A pessoa pode editar os números e o PowerPoint redesenha. Os outros tipos (proporção, pontos, halteres, empilhadas, dispersão) e os slides `evidencia` continuam no fundo, e o script lista quais. O desenho fica um pouco diferente do HTML (fonte dos eixos, espaçamento das barras). Olhe a folha do `--conferir`.

### Tamanho do arquivo

Os fundos vão em JPEG de qualidade 90. Com `--max-mb N`, o script baixa a qualidade em degraus (90, 80, 70, 60, 50) e depois reduz a resolução até o arquivo caber. Se nem o último degrau couber, ele avisa. A saída então é tratar as imagens do deck com `imagens.py tratar --max 1600`.

O que se perde é o movimento (o PowerPoint recebe o estado final) e a fidelidade exata das quebras quando a máquina não tem as fontes do tema.

### Fontes no PPTX

python-pptx não embute fontes. Há três saídas.
1. Instalar as fontes na máquina de quem vai apresentar com `python3 scripts/instalar_fontes.py` (ou `--tema NOME` para só as do tema). O script instala para o usuário atual, sem pedir administrador, no Windows, no macOS e no Linux. É a opção mais fiel. Para quem vai receber só o PPTX, mande junto a pasta `assets/fontes-ttf/` com as licenças.
2. Gerar com `--fontes-seguras`, que troca as famílias por Arial, Georgia e Courier New. O texto pode ocupar um pouco mais ou menos espaço.
3. Gerar com `--modo imagem`, que preserva tudo e não deixa nada editável.

Diga à pessoa qual das três você usou.

### Conferir

`--conferir` primeiro confere o arquivo. O zip precisa estar íntegro, o número de slides igual ao do deck, as notas presentes onde o deck tem notas ou fontes e nenhuma caixa abaixo de 14 pt. Ele lista as fontes usadas e quais não estão instaladas nesta máquina (pelo `fc-list`), o número de gráficos, tabelas e transições e o tamanho em MB. Depois converte o PPTX em PDF com o LibreOffice (quando instalado), rasteriza as páginas e monta `verificacao/pptx/html_x_pptx.jpg`, com o HTML à esquerda e o PPTX à direita, slide a slide. Olhe essa folha antes de entregar. Diferenças pequenas de espaçamento são esperadas. Texto fora do lugar, fonte trocada ou caixa cortada não são.

## Converter um deck HTML de fora

Para HTML que não foi construído com esta skill (um deck antigo, um modelo de outra ferramenta).

```
python3 scripts/converter_html.py deck.html --saida convertido/ [--medir]
```

O script avança com a seta, fotografa cada passo e gera um PDF e um PPTX em que cada slide é uma imagem, com o texto visível copiado para as notas. `--medir` mede fontes e ocupação com a mesma régua de `verificar.py`. Diga à pessoa que nesse caso o texto não é editável e que a trava do avaliador não se aplica, porque o deck não foi construído aqui. Para ter tudo (texto editável, medição, trava), refaça o deck em `deck.json`.

## Entrega

Entregue juntos o HTML, o PDF e o PPTX. Diga quantos slides, qual tema, como navegar (setas, F tela cheia, G visão geral, I créditos, N notas, P apresentador, M medidor), qual opção de fonte o PPTX usou e o que ficou pendente. Se a trava não liberou, entregue somente os rascunhos e diga isso com todas as letras.
