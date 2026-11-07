---
name: slides-impecaveis
description: Cria apresentações impecáveis em HTML (arquivo único, offline, 16x9, animado) e as converte para PDF e PPTX, com fontes grandes em todo o slide, tela inteira ocupada, imagens reais e variação de layout, conferidas por verificações automáticas e, quando o modelo enxerga imagens, por um avaliador visual. Funciona sem intervenção humana. Use quando pedirem slides, apresentação, aula, palestra, deck, banca, keynote, "slides bonitos", ou conversão de deck HTML para PDF ou PowerPoint. Funciona no Cowork, no Claude Code e em qualquer agente que rode Python.
---

# slides-impecaveis

Transforma um conteúdo (texto com slides separados por `&&&`, artigo, roteiro ou pedido) em um HTML de arquivo único, offline e animado, e dele tira um PDF e um PPTX com texto editável. O padrão é o **modo automático**, que entrega sem pedir nada à pessoa. As regras de qualidade estão nos scripts, e não na sua memória, então siga o que eles imprimem.

> Diretiva do autor. "use sua capacidade máxima de criação, deixando o HTML no mais alto nível de apresentacao possivel, como movimentos, artes, desing e animações perfeitas dentro do tema. Busque somente informacoes reais, imagens e tudo que for pertinente para uma apresentacao impecável"

Ambição visual máxima e nada inventado. As regras abaixo fazem as duas coisas conviverem.

## Regras inegociáveis

1. **Fontes grandes.** No palco de 1920x1080, nada abaixo de 28 px, corpo a partir de 44 px, título a partir de 64 px. O motor ajusta sem descer do piso. Se não couber, corte texto ou divida o slide.
2. **Tela ocupada.** No máximo 33% de área vazia e nenhum vazio contínuo acima de 16%, medidos na captura.
3. **Só informação real.** Número e afirmação de terceiros com `fonte` no slide. Imagem com origem, licença e crédito no `.webp.json`. Nada de dado, citação, autor, lei, data ou imagem inventados.
4. **Imagem pertinente ou nenhuma.** Foto só quando o slide fala de algo concreto (lugar, pessoa, documento, objeto, época). Ideia abstrata (número, risco, custo, método) vira `numero`, gráfico, diagrama ou a arte do tema. A mesma obra aparece em no máximo dois slides.
5. **Sem texto dentro da imagem.** Nada de captura de tela, figura de livro, anúncio, ficha ou diagrama pronto em imagem. Refaça como `grafico`, `diagrama`, `tabela` ou texto. A exceção é o documento que é o próprio assunto (folha de rosto, mapa histórico), marcado `"documento": true`.
6. **Sem texto sobre a imagem.** Sem legenda e sem linha de fonte na tela, salvo pedido da pessoa. Referência curta entra no texto, como "(Riker, 1964)".
7. **Variação.** Nunca três layouts iguais seguidos. Deck de 20 slides usa pelo menos 10 layouts.
8. **Sem clichês e sem enfeites.** Nada de robô, cérebro, circuito, holograma, lâmpada, "IA" como imagem, foto de banco, rótulo pequeno acima do título, degradê no texto, emoji, número de slide na tela, quique.
9. **Densidade.** De 3 a 4 itens por slide e de 20 a 30 slides, salvo pedido diferente. Títulos são afirmações.
10. **Nunca edite o HTML gerado.** Edite `deck.json` e rode de novo.
11. **Ninguém se aprova.** A aprovação vem das verificações automáticas, de um avaliador com visão comprovada em contexto separado ou da própria pessoa. Diga sempre qual dos três aprovou.

## Modo automático (padrão)

1. **Projeto.** `python3 scripts/novo_projeto.py PROJETO [--texto ORIGEM] [--verbatim] [--perfil aula|congresso|banca|palestra|gestores]`. Com texto de origem, o script extrai tudo para `texto_origem.json`.
2. **Teste de visão, uma vez.** `python3 scripts/teste_visao.py PROJETO`. Abra a imagem e responda com `--resposta "N PALAVRA"`. Se você não consegue ver imagens, rode `--sem-visao` e não adivinhe. O resultado decide se as imagens serão escolhidas olhando ou pelos metadados e se haverá avaliador visual.
3. **Roteiro no deck.** Leia a fonte uma vez. Escreva no `deck.json` o contrato (perfil, público, sala, duração, objetivo, mundo) e todos os slides, cada um com layout escolhido pela tabela abaixo. Deixe `"tema": "auto"`, salvo pedido da pessoa. O tema sai do contrato, sem amostra.
4. **Imagens.** `python3 scripts/imagens.py buscar loc "objeto concreto"` (também `met`, `nasa`, `ia`, `commons`, `openverse`), depois `baixar` e `tratar --proporcao 16:9`. Com visão, gere a folha com `olhar` e escolha olhando. Sem visão, escolha pelo título e pela descrição do acervo, prefira de 6 a 10 fotos boas a 20 duvidosas, e escreva um `alt` que diga quem ou o que aparece. Retrato de pessoa nunca vai para faixa estreita.
5. **Um comando.** `python3 scripts/fazer.py PROJETO`. Ele constrói, verifica, aprova e exporta, e imprime só o que exige ação.

| Saída do fazer.py | O que fazer |
|---|---|
| 0, PASSOU | Entregue HTML, PDF e PPTX. Diga qual caminho aprovou e quantos avisos ficaram |
| 1, CORRIJA | Mude só os slides citados, com edições pequenas no `deck.json`, e rode de novo |
| 5, chame o avaliador | Sessão com visão. Abra um subagente com `agents/avaliador-humano.md` e o caminho do projeto, nada mais. Depois rode `fazer.py` de novo |
| 4, defeitos do avaliador | Corrija os slides apontados e rode `fazer.py`. A correção sai aprovada com a nota de que houve revisão |
| 6, limite de rodadas | Pare. Entregue o rascunho e liste à pessoa o que ficou |

O `fazer.py` permite três rodadas com erro (a primeira e duas correções). Avisos não bloqueiam e não pedem correção.

### Para gastar menos

- Não leia as referências de antemão. Abra uma só quando um erro apontar para ela.
- Não releia nem imprima o `deck.json` inteiro. Edite o slide citado.
- Não escreva scripts auxiliares, não rode verificação por lote e não gere painel. O `fazer.py` já faz o necessário.
- Não use `amostra_temas.py`, `revisao.py` nem o diretor de arte no modo automático. Eles servem ao modo acompanhado.
- Relato final em poucas linhas.

## Modo acompanhado (quando a pessoa quer decidir)

Mesmos scripts, com pausas. A pessoa aprova o contrato e o roteiro, escolhe o tema numa amostra (`amostra_temas.py PROJETO --slides 1,3,7 [--todos]`), olha o painel (`revisao.py PROJETO`) e aprova por `trava.py --registrar --tipo pessoa`. Detalhes em `references/01-fluxo-e-portas.md` e `references/09-avaliador-humano.md`. Em congresso e banca, siga também `references/14-apresentacao-de-pesquisa.md`.

## Escolher o layout de cada slide

Responda em uma frase o que a plateia precisa ver e escolha.

| A ideia é | Layout | Visual |
|---|---|---|
| abertura | `capa` | imagem forte do tema |
| início de bloco | `secao` | imagem ou arte, com mapa das seções |
| uma imagem que fala por si, com 1 a 3 frases | `imagem-total` | imagem em tela cheia e painel sólido |
| conceito com explicação | `dividido` (`lado` direita ou esquerda) | imagem, gráfico ou diagrama |
| contexto com imagem larga | `faixa` | imagem panorâmica no topo (nunca retrato) |
| um número que importa | `numero` | imagem, com fonte registrada |
| de 3 a 6 números que se explicam juntos | `numeros` | contagem, torres opcionais |
| frase de um autor | `citacao` | retrato ou obra do autor |
| duas coisas lado a lado | `comparacao` | uma imagem por coluna |
| datas em sequência | `linha-do-tempo` (`orientacao: "vertical"` para datas com valor) | imagem em faixa (nunca retrato) |
| etapas em ordem | `processo` | faixa de imagem ou arte, no máximo 5 passos de títulos curtos |
| várias imagens do mesmo assunto | `galeria` | 2 a 4 imagens |
| 3 ou 4 itens paralelos | `cartoes` | imagem ou arte em cada cartão |
| comparação de valores reais | `grafico` | barras, barras-h, linha, proporção, pontos, halteres, empilhadas, dispersão |
| afirmação que um gráfico sustenta | `evidencia` | gráfico grande com anotações |
| cruzamento de categorias | `tabela` | até 4 colunas e 5 linhas curtas |
| pergunta à plateia | `pergunta` | imagem vertical |
| tese forte | `afirmacao` | imagem em tela cheia |
| lista que precisa de largura | `lista` | tira vertical de imagem |
| relação entre partes | `diagrama` | cadeia, ciclo, centro, camadas, balança, funil, iceberg, matriz, venn |
| síntese final | `fechamento` | imagem de retorno à capa |
| referências | `referencias` | arte do tema |
| algo que nenhum layout resolve | `livre` | HTML seu, medido como qualquer outro |

Campos de cada layout em `references/04-layouts.md`. Exemplo completo em `exemplos/federalismo/deck.json`. Todos os layouts em `exemplos/catalogo-layouts/`. Campo com nome errado é recusado com a sugestão do nome certo.

## Temas, paletas e estilo do texto

Dezessete temas (`tabuleiro`, `gravura`, `editorial`, `noturno`, `datilografo`, `cartografico`, `floresta`, `risografia`, `prancheta`, `porcelana`, `kraft`, `lousa`, `velino`, `revista`, `duna`, `civico`, `ardosia`), descritos em `templates/temas.json` e `references/03-direcao-de-arte.md`. `"paleta"` troca as cores, `"estilo"` reaproveita um estilo salvo e `ajustes_tema` aplica as cores da instituição. `"estilo_texto": {"sem": [":", ";", "—"], "vetadas": ["palavra"]}` faz o construtor recusar pontuação e palavras que a pessoa não usa.

Movimento. `"etapas": true` monta gráfico e diagrama peça a peça e `"intensidade"` (`sobrio`, `padrao`, `vivo`) regula o quanto tudo se mexe (`references/08-movimento.md`).

## O que os scripts conferem sozinhos

| Onde | O quê |
|---|---|
| `construir.py` | campos com nome errado, contrato, imagens sem crédito, mesma obra em mais de dois slides, texto dentro de imagem (OCR com Tesseract, se instalado, ou reconhecimento de telas e figuras), retratos, estilo do texto, limites de cada layout, variação |
| `verificar.py` | fontes, vazio, contraste, texto sobreposto ou encostado, retrato em faixa, estado final, enfeites, internet |
| motor | tamanho das fontes, última palavra presa à anterior, foco de retrato no rosto, setas dos diagramas |
| `trava.py` | só libera a versão verificada, com aprovação automática, de avaliador com visão ou da pessoa |

## Comandos

```
python3 scripts/verificar_ambiente.py
python3 scripts/novo_projeto.py PROJETO --texto aula.docx
python3 scripts/teste_visao.py PROJETO
python3 scripts/imagens.py buscar loc "termo"
python3 scripts/imagens.py baixar loc ID --saida PROJETO/assets/brutas
python3 scripts/imagens.py tratar BRUTA.jpg PROJETO/assets/nome.webp --proporcao 16:9
python3 scripts/fazer.py PROJETO
python3 scripts/empacotar.py
```

Avulsos, para o modo acompanhado ou para depurar. `construir.py`, `verificar.py`, `amostra_temas.py`, `revisao.py`, `trava.py`, `exportar_pdf.py`, `exportar_pptx.py --dados-nativos --max-mb 20`, `extrair_estilo.py`, `instalar_fontes.py`, `auditar_html.py` e `converter_html.py` (deck HTML feito fora da skill, sem texto editável e sem trava). No Windows, troque `python3` por `py`.

## Agentes auxiliares

- `agents/avaliador-humano.md`. Avaliador visual em contexto separado. Faz o teste de visão, olha só as folhas de contato e lista defeitos. Sem visão, encerra na hora.
- `agents/diretor-de-arte.md` e `agents/revisor-de-texto.md`. Consultivos, para o modo acompanhado.

## Onde ler mais

`references/01-fluxo-e-portas.md` · `02-texto.md` · `03-direcao-de-arte.md` · `04-layouts.md` · `05-imagens-reais.md` · `06-graficos-e-diagramas.md` · `07-legibilidade-e-ocupacao.md` · `08-movimento.md` · `09-avaliador-humano.md` · `10-exportar-pdf-pptx.md` · `11-portabilidade.md` · `12-solucao-de-problemas.md` · `13-licoes-das-skills-anteriores.md` · `14-apresentacao-de-pesquisa.md` · `exemplos/README.md`
