# slides-impecaveis

Skill para agentes de IA que cria apresentações em HTML de um arquivo só, animadas e offline, e as converte para PDF e PPTX com texto editável. Ela foi feita para que o resultado seja bom independentemente do modelo que a usa. As regras mais importantes estão no motor e nos scripts, não só nas instruções.

## O que ela garante

- **Fontes grandes em todo o slide.** Nada abaixo de 28 px, corpo a partir de 44 px e título a partir de 64 px num palco de 1920x1080 (14, 22 e 32 pt no PowerPoint). Medido em cada slide, no render real.
- **Tela inteira ocupada.** No máximo 33% de área vazia e nenhum vazio contínuo acima de 16%, medidos na captura.
- **Imagens reais.** Busca em acervos abertos (Library of Congress, Metropolitan Museum, NASA, Internet Archive, Wikimedia Commons), com origem, licença e crédito registrados.
- **Variação.** Vinte layouts e um modo livre, nunca três iguais seguidos.
- **Funciona sozinha.** Um comando (`fazer.py`) constrói, verifica, aprova e exporta, com no máximo três rodadas de correção. Verificações automáticas cobrem o que um modelo sem visão não percebe (texto dentro de imagem, a mesma obra repetida, títulos encostados, retrato cortado, campo com nome errado).
- **Avaliador visual só quando há olhos.** Um teste de visão sorteado decide se o modelo enxerga. Se enxerga, um avaliador em contexto separado olha as folhas de contato e lista defeitos. Se não, a etapa é pulada e o registro diz que não houve revisão visual. A pessoa pode sempre avaliar pelo painel.

## Instalar

```
python3 -m pip install -r requirements.txt
python3 -m playwright install chromium
python3 scripts/verificar_ambiente.py
```

Depois coloque a pasta onde o seu agente procura skills. Para distribuir, gere o pacote com `python3 scripts/empacotar.py`, que deixa de fora projetos, capturas e exportações e avisa se o zip passar de 50 MB. Detalhes para Claude Code, Cowork, Codex, Cursor, Gemini CLI e Windows em `references/11-portabilidade.md`.

## Usar

Peça ao agente uma apresentação ("faça slides sobre federalismo para uma turma de graduação, 30 minutos") ou entregue um texto com os slides separados por `&&&`. Por padrão o agente segue o modo automático do `SKILL.md` e entrega HTML, PDF e PPTX sem pedir nada. Se quiser decidir junto (contrato, tema, cada slide), diga que quer acompanhar.

Comandos principais, se quiser rodar à mão.

```
python3 scripts/novo_projeto.py aula --texto aula.docx
python3 scripts/teste_visao.py aula
python3 scripts/fazer.py aula
```

Avulsos. `construir.py`, `verificar.py`, `amostra_temas.py`, `revisao.py`, `trava.py`, `exportar_pdf.py`, `exportar_pptx.py --conferir`.

Para converter um deck HTML feito em outro lugar, `python3 scripts/converter_html.py deck.html --saida convertido/`. Para o PPTX abrir com as fontes do tema, rode `python3 scripts/instalar_fontes.py` na máquina de quem apresenta.

## No navegador

Setas ou clique navegam (a seta para trás desfaz a última etapa). Número e Enter saltam para o slide. F tela cheia. G visão geral. B tela preta. W tela branca. L ponteiro. I créditos das imagens e dados. N notas. P janela do apresentador, com o próximo slide, o tempo previsto e R para zerar o cronômetro. M medidor de fontes e vazios. ? ajuda.

## Estrutura

```
SKILL.md                 instruções para o agente (comece aqui)
AGENTS.md                ponte para agentes que não leem SKILL.md
references/              um arquivo por assunto (fluxo, texto, direção de arte, layouts, imagens, ...)
agents/                  avaliador humano (bloqueante), diretor de arte e revisor de texto
scripts/                 construir, verificar, revisar, travar, exportar, imagens, auditar, converter
templates/runtime/       motor do deck (sk.css, temas.css, sk.js)
templates/projeto-modelo deck.json vazio
assets/fontes            fontes livres embutidas no HTML (woff2) e licenças
assets/fontes-ttf        as mesmas fontes para instalar e usar no PowerPoint
exemplos/                deck de exemplo, catálogo de layouts e referências comentadas
```

## Exemplos

`exemplos/federalismo/` é um deck completo de 19 slides com imagens de acervo, verificado em todas as medições. O painel do avaliador e as exportações de rascunho saem com `revisao.py` e os exportadores. `exemplos/catalogo-layouts/` mostra os 21 layouts. `exemplos/README.md` traz as folhas de contato e o que copiar ou evitar em decks de referência.

Os exemplos vêm sem HTML, sem folhas, sem aprovação registrada e sem PDF e PPTX, para o pacote ficar leve. `python3 scripts/fazer.py exemplos/federalismo` constrói, aprova e exporta.

Licenças das fontes e das imagens em `LICENSE-NOTES.md`.
