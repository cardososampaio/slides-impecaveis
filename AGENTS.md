# Instruções para agentes de IA (Codex, Cursor, Gemini CLI, Aider e outros)

Esta pasta é a skill **slides-impecaveis**. Ela cria apresentações em HTML e as converte para PDF e PPTX.

1. Leia `SKILL.md` inteiro antes de começar. Ele é a fonte das regras e do fluxo.
2. Rode `python3 scripts/verificar_ambiente.py` (no Windows, `py scripts/verificar_ambiente.py`) e instale o que faltar.
3. Siga as portas G0 a G8 do `SKILL.md`, na ordem. Leia o arquivo de `references/` da porta em que estiver.
4. Edite somente `PROJETO/deck.json` e as imagens do projeto. Nunca edite o HTML gerado.
5. A porta G7 exige um avaliador humano (a pessoa, ou um agente em contexto separado seguindo `agents/avaliador-humano.md`). PDF e PPTX finais só saem quando `scripts/trava.py PROJETO` disser LIBERADO.

Diretiva do autor, válida para todo deck.

> "use sua capacidade máxima de criação, deixando o HTML no mais alto nível de apresentacao possivel, como movimentos, artes, desing e animações perfeitas dentro do tema. Busque somente informacoes reais, imagens e tudo que for pertinente para uma apresentacao impecável"

Regras que não se negociam. Fontes grandes em todo o slide (nada abaixo de 28 px, corpo a partir de 44 px, título a partir de 64 px no palco de 1920x1080). Tela inteira ocupada. Imagem real sempre que possível. Variação de layout. Somente informação real, com fonte. O avaliador humano trava a entrega até tudo estar satisfeito.
