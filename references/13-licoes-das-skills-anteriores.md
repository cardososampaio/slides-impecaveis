# 13. Lições das skills anteriores e dos decks de referência

Esta skill nasceu da comparação entre duas skills de slides (`aula-html-slides` e `skill-slides-rafael`), três decks de referência escolhidos como "bons slides" e cinco avaliações feitas por IAs diferentes. A avaliação completa está em `opus55.md`, na pasta original. Aqui fica só o que mudou o desenho desta skill. As imagens citadas estão em `exemplos/referencias/`.

## Medições que orientaram os limites

Todas feitas com `scripts/auditar_html.py` (decks HTML) ou com a medição de ocupação sobre a página rasterizada (PDFs), em 1920x1080 e com a mesma régua de `verificar.py`.

| Deck | Telas | Corpo mediano | Menor texto | Telas com corpo abaixo de 44 px | Telas com área morta acima do limite |
|---|---|---|---|---|---|
| aula-html-slides, exemplo de amostragem | 101 | 44 px | 13 px | 32 | 20 (vazio mediano de 27%) |
| Rousseau (HTML de referência) | 90 passos | 24 px | 12 px | 71 | 83 (vazio mediano de 59%) |
| Federalismo (PDF de referência) | 12 | texto dentro da imagem | não mensurável | não mensurável | 0 (vazio mediano de 10%) |
| Locke e Montesquieu (PDF de referência) | 30 | texto dentro da imagem | não mensurável | não mensurável | 1 (vazio mediano de 10%) |
| slides-rafael, modelo Swiss | 2 | 30 px | 14 px | 2 | 1 |

Os limites de ocupação (33% de vazio, 16% de maior vazio) separam os PDFs, que passam, do Rousseau, que falha, e reprovam cerca de uma em cada cinco telas da aula-html-slides. Os pisos de fonte (28, 44 e 64 px) vêm da exigência de leitura no fundo da sala e da conversão para pontos do PowerPoint (14, 22 e 32 pt).

## O que veio de cada fonte

**aula-html-slides.** Motor próprio em HTML com cenas, temas como mundos visuais completos, verificação sobre o render, folhas de contato, modo que preserva o texto da pessoa, imagens de acervo com crédito. A skill nova mantém a ideia de motor e de verificação, mas passa a medir o que a antiga só avisava (fonte abaixo de 30 px gerava aviso, não bloqueio) e a medir a ocupação, que a antiga não media. Defeitos que não podem voltar são legendas, chips e trilha abaixo de 28 px em todos os slides, etiquetas de citação copiadas com erro da origem ("Simetal,2018") e rótulo de gráfico sobre a linha.

**skill-slides-rafael.** O melhor método escrito (contrato antes do design, roteiro antes dos slides, pausas para a pessoa, tipografia para projeção). Faltavam motor e exemplos de saída. Os dois modelos HTML que ela traz falham quando renderizados (`exemplos/referencias/templates-slides-rafael.jpg`). Um abre como tela preta, o outro tem marcadores em chinês e rótulos de 10 a 14 px. A skill nova adota o contrato e as portas e põe um motor que os executa.

**PDFs de referência (Federalismo, Locke).** Explicam o que agrada. Tela sempre cheia, imagem em quase todo slide, títulos grandes e condensados, paleta creme, grafite e um acento, composição que muda a cada slide (`federalismo-pdf.jpg`, `locke-pdf.jpg`). Também mostram o que não pode ser copiado. Cada slide é uma imagem só, gerada por modelo de imagem, com o texto dentro, o que impede editar, buscar, ler em voz alta e medir. As imagens trazem rótulos inventados ("Pai da Nação 1", "Representante 2", um diagrama "CENTRALIZED (UNITARY) MODEL" em inglês) e anotações miúdas. Daí as regras de imagem real, sem texto dentro, e de piso de fonte em todo texto.

**Rousseau (HTML de referência).** O melhor movimento e a melhor direção de arte do conjunto (`rousseau.jpg`). Obras reais com legenda de museu, partículas que significam algo (maioria e minoria, o povo como corpo), argumento revelado em etapas, notas com tempo. O defeito é exatamente o que esta skill proíbe, texto pequeno e metade da tela vazia (`marcas-rousseau.jpg`). Daí o tema `noturno`, as etapas e o movimento com sentido, junto com a trava de fonte e de ocupação.

**As cinco avaliações.** Todas pediram dois modos de texto, folhas de contato, nenhum avanço por silêncio e aprovação final fora das mãos de quem construiu. Nenhuma propôs medir a fonte de todo texto visível nem a ocupação da tela. A DeepSeek leu "espectador humano" como o olhar de alguém no fundo da sala, leitura que o pedido final confirmou e que virou o avaliador desta skill.

## Regras que nasceram dessas lições

1. Fonte medida em todo texto visível, por papel, com piso que não desce.
2. Ocupação medida na captura, com o vazio marcado em vermelho para o avaliador ver.
3. Desenho ou canvas decorativo em tela cheia não conta como conteúdo. Sem essa regra, o Rousseau parecia ocupado em todas as telas.
4. Texto nunca dentro de imagem. Imagem sempre real, com origem e licença.
5. Avaliador humano que vê cada slide e trava a entrega, ligado à versão exata do HTML.
6. HTML como original, PDF e PPTX derivados, PPTX com texto editável.
7. Modelos e exemplos que passam na própria régua. Um exemplo que falha ensina o defeito.
