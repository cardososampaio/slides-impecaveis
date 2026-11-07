# Licenças e proveniência

## Fontes

Todas as fontes estão sob a SIL Open Font License 1.1, que permite usar, embutir e redistribuir, inclusive em trabalhos comerciais, desde que a licença acompanhe as fontes e elas não sejam vendidas sozinhas. Os textos completos estão em `assets/fontes/licencas/`.

| Família | Autores | Arquivos |
|---|---|---|
| Atkinson Hyperlegible Next | The Atkinson Hyperlegible Next Project Authors (Braille Institute) | `AtkinsonNext*.woff2`, `AtkinsonHyperlegibleNext-*.ttf` |
| Courier Prime | The Courier Prime Project Authors | `CourierPrime*.woff2`, `CourierPrime-*.ttf` |
| Jost | The Jost Project Authors (indestructible type) | `Jost.woff2`, `Jost-*.ttf` |
| Oswald | The Oswald Project Authors | `Oswald.woff2`, `Oswald-*.ttf` |
| Source Serif 4 | The Source Serif 4 Project Authors (Adobe) | `SourceSerif4*.woff2`, `SourceSerif4-*.ttf` |
| Archivo | The Archivo Project Authors (Omnibus-Type) | `Archivo*.woff2`, `Archivo-*.ttf` |
| Barlow Condensed | The Barlow Project Authors (Jeremy Tribby) | `BarlowCondensed*.woff2`, `BarlowCondensed-*.ttf` |
| Bricolage Grotesque | The Bricolage Grotesque Project Authors (Mathieu Triay) | `BricolageGrotesque.woff2`, `BricolageGrotesque-*.ttf` |
| Instrument Serif | The Instrument Serif Project Authors (Instrument) | `InstrumentSerif*.woff2`, `InstrumentSerif-*.ttf` |
| Libre Caslon Text | The Libre Caslon Project Authors (Impallari Type) | `LibreCaslonText*.woff2`, `LibreCaslonText-*.ttf` |
| Newsreader | The Newsreader Project Authors (Production Type) | `Newsreader*.woff2`, `Newsreader-*.ttf` |
| Public Sans | The Public Sans Project Authors (USWDS) | `PublicSans*.woff2`, `PublicSans-*.ttf` |
| Schibsted Grotesk | The Schibsted Grotesk Project Authors | `SchibstedGrotesk*.woff2`, `SchibstedGrotesk-*.ttf` |
| Spectral | The Spectral Project Authors (Production Type) | `Spectral*.woff2`, `Spectral-*.ttf` |
| Zilla Slab | The Zilla Slab Project Authors (Typotheque para Mozilla) | `ZillaSlab*.woff2`, `ZillaSlab-*.ttf` |

As famílias novas foram baixadas de `github.com/google/fonts` (pasta `ofl/`), recortadas para o alfabeto latino e convertidas para woff2. Os TTF do PPTX são instâncias estáticas 400, 600, 700 e itálico 400 das fontes variáveis, com o nome da família ajustado para o PowerPoint (por exemplo, "Spectral SemiBold" para o peso 600). A OFL permite essas modificações, e nenhuma dessas famílias declara nome reservado (Reserved Font Name) na licença, o que permite manter o nome original nas versões recortadas.

Os decks gerados levam as fontes embutidas em base64, o que a licença permite.

## Imagens dos exemplos

Cada imagem em `exemplos/federalismo/assets/` tem um `.webp.json` com acervo, página do item, arquivo de origem, data de acesso, direitos declarados pelo acervo, decisão sobre a licença e transformações feitas.

- Library of Congress. Itens marcados "No known restrictions on publication" e obras impressas antes de 1900 sem restrição registrada no item.
- NASA Image and Video Library. Imagens produzidas pela NASA, em regra de domínio público nos Estados Unidos. As diretrizes de uso de mídia da NASA proíbem sugerir endosso e usar as insígnias da agência, o que os exemplos não fazem.

Antes de reutilizar uma imagem fora destes exemplos, leia de novo a página do item. Acervos mudam a informação de direitos.

## Código e textos

O motor (`templates/runtime/`), os scripts e as instruções foram escritos para esta skill. Nenhum código foi copiado das skills `aula-html-slides` e `skill-slides-rafael` nem dos decks da pasta de exemplos. As lições tiradas deles estão descritas em `references/13-licoes-das-skills-anteriores.md`.

- `references/14-apresentacao-de-pesquisa.md` adapta ideias e regras de academic-pptx-skill (Copyright (c) 2026 Gabberflast, licença MIT) e do estilo academic-research do ppt-master (Copyright (c) 2025-2026 Hugo He, licença MIT), reescritas em português.
- O acervo `openverse` de `scripts/imagens.py` segue a ideia e os parâmetros de busca de `skills/ppt-master/scripts/image_sources/provider_openverse.py` do ppt-master (Copyright (c) 2025-2026 Hugo He, licença MIT), reescritos para esta skill.

O detector de enfeites e os avisos tipográficos de `scripts/medir.py` (`JS_ENFEITES`) foram escritos para esta skill a partir das ideias da lista de antipadrões e das verificações de [pbakaus/impeccable](https://github.com/pbakaus/impeccable) (Apache 2.0, `crates/live/assets/antipatterns.json` e `crates/core/src/checks`) e do `scripts/design_lint.py` de [alchaincyf/huashu-design](https://github.com/alchaincyf/huashu-design) (MIT, Copyright (c) 2026 alchaincyf). Nenhum trecho de código foi copiado literalmente.

As transições de slide e o morph (`templates/runtime/sk.css` e `sk.js`, `references/08-movimento.md`) adaptam o contrato e a família de transições de `packages/core/skills/slide-authoring/references/transitions.md` e `morph.md` do [open-slide](https://github.com/open-slide/open-slide) (MIT, Copyright (c) 2026 Yiwei Ho), reescritos para esta skill.

Defina a licença do código antes de distribuir a skill publicamente.
