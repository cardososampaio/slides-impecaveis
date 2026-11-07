# 11. Portabilidade

A skill é uma pasta com instruções em Markdown, scripts em Python e um motor em HTML, CSS e JavaScript sem dependências externas. Funciona em qualquer agente que leia arquivos e rode comandos.

## Requisitos

| Item | Para quê | Obrigatório |
|---|---|---|
| Python 3.9+ | todos os scripts | sim |
| Pillow, numpy | imagens e medição | sim |
| Playwright com Chromium | render, verificação, painel, PDF e PPTX | sim para verificar e exportar |
| python-pptx | PPTX | sim para PPTX |
| python-docx | ler origem em `.docx` | não |
| LibreOffice | `exportar_pptx.py --conferir` | não |
| poppler (`pdfinfo`) | contar páginas do PDF | não |
| Tesseract | ler texto dentro das imagens | não (sem ele, a skill reconhece telas e figuras pelo desenho) |
| OpenCV (`opencv-python-headless`) | achar rostos para não cortá-los | não (sem ele, vale o `alt` da imagem) |

`python3 scripts/verificar_ambiente.py` confere tudo e imprime o comando de instalação do que faltar. A lista está em `requirements.txt`.

```
python3 -m pip install -r requirements.txt
python3 -m playwright install chromium
```

Em Linux gerenciado pelo sistema, acrescente `--break-system-packages` ao pip ou use um ambiente virtual.

## Distribuir

Nunca compacte a pasta de trabalho inteira. Projetos de teste, capturas, amostras de tema e exportações crescem rápido (um deck com 17 temas de amostra chegou a 600 MB). Use `python3 scripts/empacotar.py`, que monta `slides-impecaveis.zip` só com instruções, scripts, motor, fontes e exemplos leves, lista as pastas que ficaram de fora e avisa acima de 50 MB. Mantenha decks de teste fora da pasta da skill.

## Onde instalar a pasta

| Agente | Onde |
|---|---|
| Claude Code | `~/.claude/skills/slides-impecaveis/` (para todos os projetos) ou `.claude/skills/slides-impecaveis/` no projeto |
| Cowork (app Claude) | envie a pasta compactada em .zip nas configurações de skills, ou peça ao Claude para propor a skill a partir desta pasta |
| Codex, Cursor, Gemini CLI, Aider, outros | copie a pasta para o projeto e aponte o agente para `AGENTS.md`, que manda ler `SKILL.md` |
| agente sem suporte a skills | cole o conteúdo de `SKILL.md` nas instruções do agente e deixe a pasta acessível |

Os scripts localizam o motor e as fontes pela própria posição, então a pasta pode morar em qualquer lugar. Rode os comandos a partir da raiz da skill ou use o caminho completo de cada script.

## Windows

- Troque `python3` por `py` (ou `python`).
- Caminhos com espaço vão entre aspas (`py scripts\construir.py "C:\Aulas\Federalismo"`).
- Os scripts não usam bash, `sed` nem links simbólicos obrigatórios. Funcionam no PowerShell e no Prompt de Comando.
- O LibreOffice fica em `C:\Program Files\LibreOffice\program\soffice.exe`. Se `--conferir` não o encontrar, ponha essa pasta no PATH.

## Cowork

- O trabalho acontece na nuvem. Os arquivos da pessoa chegam por pasta conectada ou anexo. Ao final, entregue HTML, PDF e PPTX na pasta conectada.
- Para a porta G3 e para o avaliador, envie as folhas `amostra-temas/temas_N.jpg`, as folhas de contato e `revisao/painel.html` como arquivos que abrem no painel lateral.
- Se o botão de baixar do painel não funcionar, a pessoa copia o JSON do parecer e cola na conversa. Grave sem alterar.
- A rede da nuvem pode bloquear algum acervo. Tente outro (`loc`, `met`, `nasa`, `ia`, `commons`) ou peça à pessoa imagens que ela tenha. Nunca troque imagem real por imagem inventada.

## Claude Code e terminais

- A pessoa costuma estar no mesmo computador. Abra o HTML com o navegador padrão para ela ver o movimento e o medidor (tecla M).
- O avaliador agente em contexto separado é um subagente. Passe a ele só o caminho do painel ou das folhas e o arquivo `agents/avaliador-humano.md`, nunca o histórico da construção.

## Sem Chromium

Sem render não existe verificação, e sem verificação a trava não libera. Nesse caso.
1. Construa o HTML com `construir.py` (não precisa de navegador).
2. Entregue o HTML como rascunho e peça à pessoa que abra no navegador dela, passe os slides e aperte **M** em cada um. O medidor mostra cada texto com o tamanho em px e pinta de laranja o que está abaixo do piso e de vermelho as áreas vazias. É uma aproximação feita pelo DOM, menos precisa que a medição pela captura.
3. Para PDF, a pessoa pode imprimir pelo navegador (Ctrl+P, sem margens, paisagem). O CSS de impressão põe um slide por página.
4. Diga com clareza que a medição automática não rodou e que o PPTX depende de instalar o Chromium.

## Independência de modelo

A qualidade não depende só de quem escreve o deck. As regras que mais pesam estão no motor e nos scripts.
- O motor ajusta as fontes sem descer dos pisos e compõe os vinte layouts.
- O construtor recusa conteúdo sem fonte, imagem sem crédito e repetição de layout.
- A verificação mede cada slide pela captura.
- A trava impede a entrega sem o avaliador.

Para um modelo menor ou com pouco contexto, o caminho mais seguro é copiar o exemplo (`novo_projeto.py PROJETO --exemplo`), trocar o conteúdo slide a slide mantendo os layouts, rodar `construir.py` e `verificar.py` a cada lote e seguir a tabela de consertos de `07-legibilidade-e-ocupacao.md`. Ler `SKILL.md` e o arquivo de referência da porta atual basta. Os outros servem quando surgir a dúvida.
