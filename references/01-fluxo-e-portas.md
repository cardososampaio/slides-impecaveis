# 01. Fluxo e portas

As portas valem para o **modo acompanhado**, quando a pessoa quer decidir junto. No modo automático (o padrão, descrito no `SKILL.md`) não há pausas e o `fazer.py` cuida da verificação, da aprovação e da exportação. Aqui está o que acontece em cada porta, o que perguntar à pessoa e o que nunca fazer.

## Regras das pausas

- Cada pausa entrega um artefato que a pessoa pode olhar (o contrato, o roteiro, a folha de temas, o painel de avaliação). Não descreva em texto o que você pode mostrar.
- Pergunte uma coisa de cada vez, com a sua recomendação primeiro.
- Silêncio, demora ou "depois eu vejo" não autorizam seguir. Se a pessoa não estiver presente, registre a pendência em `decisoes.md` e pare na porta.
- Sem pedido da pessoa para acompanhar, use o modo automático do `SKILL.md`. As decisões viram registros curtos em `decisoes.md`.

## G0 · Ambiente

`python3 scripts/verificar_ambiente.py`. Sem Playwright e Chromium não há render, e sem render não há verificação. Instale antes de começar.

## G1 · Contrato

Preencha `deck.json > contrato` com a pessoa. Os campos obrigatórios são `tese`, `mundo`, `historia`, `primeira_tela`, `publico` e `sala`, e `forma` registra o tema escolhido. Acrescente `duracao_min` e `perfil`. Pergunte também o formato de saída (HTML sempre, PDF e PPTX quando pedidos), o modo de texto (`verbatim` ou `autoral`) e o que não pode mudar.

O `perfil` define densidade, títulos e roteiro.

| `perfil` | Quando | O que muda |
|---|---|---|
| `aula` (padrão) | turma, curso, oficina | 3 a 4 itens, títulos que afirmam |
| `congresso` | sessão com tempo fixo | títulos-ação, cerca de 1 slide por minuto, roteiro de `references/14-apresentacao-de-pesquisa.md`, apêndice |
| `banca` | defesa de dissertação ou tese | como `congresso`, com mais peso em método, limitações e apêndice |
| `palestra` | público amplo | menos texto, mais imagem, uma ideia por slide |
| `gestores` | servidores públicos | linguagem da administração pública brasileira, leis e políticas nacionais citadas pelo número, 1 ideia e 2 ou 3 itens por slide |

Um contrato bom é específico. "Design moderno e limpo" não serve. "Revista de história impressa, creme e grafite, gravuras de acervo em tamanho grande, sangrando até a borda" serve.

## G2 · Conteúdo

- **Texto pronto (verbatim).** `python3 scripts/extrair_texto.py ORIGEM PROJETO --verbatim`. O script preserva o texto e lista anomalias (citações sem espaço, slides com mais de 4 itens, itens longos, marcações). Mostre a lista à pessoa. Nada é corrigido sem ela.
- **Texto a construir (autoral).** Leia a fonte inteira. Faça um mapa de afirmações e de onde cada uma vem. Redija seguindo `references/02-texto.md`. Mostre o roteiro (título e ideia de cada slide) antes de montar.
- **Densidade.** Segue o `perfil` (tabela em `references/02-texto.md`). No padrão, 3 a 4 itens por slide e cerca de 30 palavras visíveis. Texto longo vai para as notas.
- **Congresso e banca.** Faça o teste do deck fantasma (só os títulos, em sequência) antes de montar. Ver `references/14-apresentacao-de-pesquisa.md`.

## G3 · Direção visual

`python3 scripts/amostra_temas.py PROJETO --slides 1,3,7` mostra os mesmos slides em três temas sugeridos pelo contrato (um seguro, um ousado e um curinga). Com `--todos`, mostra os dezessete temas, seis por folha (`amostra-temas/temas_1.jpg`, `temas_2.jpg`, `temas_3.jpg`). Mostre as folhas e espere a escolha. Registre em `contrato.forma` e em `decisoes.md`.

## G4 · Imagens e dados

Siga `references/05-imagens-reais.md`. Gere a folha de candidatas com `imagens.py olhar` e escolha olhando. Guarde cada número com a fonte no campo `fonte` do slide. Ela vai para a tecla I e para as notas, não para a tela.

## G5 · Montagem

Para cada slide, diga a ideia em uma frase, escolha o layout pela tabela do `SKILL.md`, escolha o visual, escreva as notas (`notas`, com tempo estimado) e a fonte (`fonte`) quando houver número. Construa a cada 5 a 8 slides e confira o lote com `verificar.py PROJETO --slides 1-8`. O lote vai para `verificacao/lote/` e não vale para a trava. No fim, verifique o deck inteiro.

## G6 · Verificação

`python3 scripts/verificar.py PROJETO`. Corrija até PASSOU. Depois olhe todas as folhas em `verificacao/folhas/` e abra o HTML para ver o movimento. Verde não demonstra beleza. Pergunte a si mesmo, slide a slide, se ele poderia estar em qualquer outro deck sem mudar nada. Se sim, ele é genérico e precisa de uma ideia visual própria.

## G7 · Avaliador

Com a pessoa presente, `python3 scripts/revisao.py PROJETO` e entregue `revisao/painel.html` (ou as folhas). Corrija o que ela pedir e repita até `python3 scripts/trava.py PROJETO` dizer LIBERADO. Sem a pessoa, o `fazer.py` decide entre o avaliador com visão e o caminho automático. Ver `references/09-avaliador-humano.md`.

## G8 · Exportação e entrega

`python3 scripts/exportar_pdf.py PROJETO` e `python3 scripts/exportar_pptx.py PROJETO --conferir`. Entregue o HTML, o PDF e o PPTX. Diga quantos slides, o tema, como navegar (setas, F, G, I, N, P, M), onde estão os créditos e o que ficou pendente.

## Modelo de `decisoes.md`

```
- 2026-10-21 · G1 · contrato aprovado pela pessoa ("pode seguir").
- 2026-10-21 · G2 · modo verbatim; pessoa pediu para dividir o slide 14 em dois.
- 2026-10-21 · G3 · tema editorial escolhido entre os cinco.
- 2026-10-21 · G4 · suposição: usar gravura de 1846 na capa (domínio público, LoC).
- 2026-10-22 · G7 · avaliadora pediu fonte maior no slide 9; corrigido; aprovado na versão 6715c740.
```
