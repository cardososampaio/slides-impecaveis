# 09. Avaliador, aprovação e trava

Nada sai como versão final sem uma aprovação registrada para a versão atual do deck. A skill funciona sem intervenção humana, então há três caminhos de aprovação, e este arquivo diz quando vale cada um e como a trava confere.

## Três caminhos de aprovação

| Caminho | Quando | Quem registra | Nota no registro |
|---|---|---|---|
| automático | padrão. Ninguém com visão vai olhar, ou o modelo não enxerga imagens | `fazer.py` (ou `trava.py --automatico`) | "aprovado pelas verificações automáticas, sem revisão visual" |
| avaliador com visão | a sessão passou no teste de visão (`teste_visao.py`) | o subagente de `agents/avaliador-humano.md`, com a lista de defeitos | sem defeitos, aprovado. Com defeitos, uma correção e a nota "revisado por avaliador com visão" |
| pessoa | a pessoa quer olhar (modo acompanhado) | `trava.py --registrar --tipo pessoa`, pelo painel ou pela conversa | as palavras dela |

O caminho da pessoa vence os outros. O avaliador agente só existe com visão comprovada. Um modelo que só lê texto não consegue acertar o teste de visão, cuja resposta é sorteada e guardada como hash lento. Sem visão, a avaliação visual é pulada, porque um parecer feito a partir do código da página descreve a página sem ter visto os defeitos. Foi o que aconteceu num teste com um modelo sem visão, que aprovou títulos encostados e um rosto cortado.

O avaliador com visão olha só as folhas de contato e devolve no máximo dez defeitos concretos. Não escreve evidência slide a slide, para gastar pouco. O deck é corrigido uma vez e o `fazer.py` aprova a correção pelo caminho automático, sem chamar o avaliador de novo.

Quem construiu o deck nunca se aprova. Silêncio, "depois eu vejo" ou "parece bom" sobre outra versão não contam.

## Caminho da pessoa

Os itens abaixo valem para quando a pessoa avalia.

## O que o avaliador recebe

`python3 scripts/revisao.py PROJETO` gera dois arquivos.

- `revisao/painel.html`, arquivo único que abre em qualquer navegador. No topo fica o **teste do deck fantasma**, a lista só com os títulos em ordem, e os avisos do deck. Cada slide aparece primeiro só com a captura limpa e o campo de evidência. Depois que o avaliador escreve pelo menos 10 palavras sobre o que vê, o painel libera as marcas (vazio em vermelho, texto pequeno, sem contraste ou enfeite em laranja), os números medidos, os avisos e as quatro caixas. Ver os números antes ancora o olhar, e a ordem existe para evitar isso. No fim há o bloco **Manter, Corrigir, Ganhos rápidos**.
- `revisao/pendencias.md`, a mesma lista em texto, para revisão pela conversa.

O avaliador também pode abrir o próprio HTML do deck e apertar **M**, que desenha os tamanhos e os vazios no navegador, e passar os slides para ver o movimento.

## O que ele confirma

Para cada slide.

| Caixa | Pergunta |
|---|---|
| Fontes grandes e legíveis em todo o slide | Do fundo da sala, consigo ler tudo, inclusive legenda, rótulo e fonte? |
| Tela inteira ocupada | Há área morta, faixa vazia, campo de cor sem nada? |
| Sem defeitos | Algo cortado, sobreposto, borrado, sem contraste, desalinhado? O espaço livre está bem distribuído (título com o mínimo de linhas, nomes compostos inteiros, respiro entre blocos)? |
| Visual pertinente | A imagem, o gráfico ou o diagrama mostram o assunto do slide? A imagem é real e tem crédito? |

Os campos são **evidência** (o que ele viu) e **nota** (o que precisa mudar). A trava recusa evidência genérica, isto é, com menos de 10 palavras, repetida em outro slide ou sem nenhuma palavra do título do slide nem do nome, legenda ou descrição da imagem. Recusa também palavras vazias (moderno, limpo, elegante, profissional, impactante, bonito, clean, sofisticado) na evidência, nas notas, na síntese e em `revisao/diretor.md`. Isso vale para agente sempre e para pessoa quando o parecer vem do painel. A declaração literal de uma pessoa registrada pela conversa fica como ela disse.

Para o deck inteiro.

| Caixa | Pergunta |
|---|---|
| Argumento | Lendo só os títulos em ordem (deck fantasma), o argumento se sustenta? |
| Variação | Os slides variam em layout, lado, escala e ritmo? |
| Conteúdo real | Os números têm fonte, as citações existem, as imagens são o que dizem ser? |
| Movimento visto | Passei o deck no navegador e as entradas fazem sentido? |

O painel não deixa marcar aprovado num slide que a medição automática reprovou. A medição é a régua, o avaliador é quem confirma que a régua e os olhos concordam.

## Como o parecer chega à trava

Há dois caminhos.

**Pelo painel.** O avaliador marca as caixas, escreve nome e tipo e clica em "Gerar parecer". O painel mostra o JSON e oferece o download de `parecer.json`. Salve em `PROJETO/revisao/parecer.json`. No Cowork, se o download não funcionar dentro do painel lateral, a pessoa copia o texto da caixa e cola na conversa, e o agente grava o arquivo sem mudar nada.

**Pela conversa.** Mostre as folhas de contato (`verificacao/folhas/`) e as marcas dos slides com problema. Peça que a pessoa responda por slide ou em bloco. Registre as palavras literais dela.

```
python3 scripts/trava.py PROJETO --registrar --avaliador "Rafael" --tipo pessoa \
  --declaracao "Vi as três folhas. Fontes boas, tela cheia. Aprovo."
```

Se ela reprovar slides, registre também.

```
python3 scripts/trava.py PROJETO --registrar --avaliador "Rafael" --tipo pessoa \
  --declaracao "O 7 está com a legenda colada na borda" --reprovar 7 --motivo "legenda colada na borda"
```

Antes de registrar pela conversa, mostre à pessoa a lista de títulos de `revisao/pendencias.md` e pergunte se eles contam o argumento. A aprovação registrada confirma também essa condição.

Nunca escreva uma declaração que a pessoa não fez. A declaração é copiada da mensagem dela, com as palavras dela.

## A trava

`python3 scripts/trava.py PROJETO` responde LIBERADO ou TRAVADO, com os motivos. Em todos os caminhos ela exige o HTML exatamente como `construir.py` gerou (hash conferido), construído sem `--rascunho`, e a verificação automática desta versão aprovada com os limites da skill.

- **Automático.** Basta o registro desta versão.
- **Agente.** Teste de visão aprovado nas últimas 24 horas, contexto separado e lista de defeitos vazia. Com defeitos, a trava manda corrigir e rodar `fazer.py`.
- **Pessoa.** O parecer desta versão identifica quem avaliou, tem as quatro confirmações em cada slide e as quatro condições gerais, sem palavras vazias (moderno, limpo, elegante, profissional, impactante, bonito, clean, sofisticado), e está marcado como aprovado.

`exportar_pdf.py` e `exportar_pptx.py` chamam a trava e se recusam a gerar a versão final quando ela diz TRAVADO. Com `--rascunho` eles exportam sem a aprovação, com a tarja RASCUNHO em cada página. O `fazer.py` usa o rascunho quando bate no limite de rodadas.

Qualquer mudança no `deck.json`, nas imagens ou no motor muda o hash do HTML, e a aprovação antiga deixa de valer. O `fazer.py` registra de novo pelo caminho certo.

## Ciclo de correção (caminho da pessoa)

1. O avaliador reprova slides com notas.
2. Você corrige no `deck.json`, constrói, verifica até PASSOU.
3. Gera o painel de novo e devolve ao avaliador, dizendo o que mudou em cada slide reprovado.
4. Repete até LIBERADO.

Se a pessoa não estiver presente, pare na porta G7, registre a pendência em `decisoes.md` e entregue o HTML e os rascunhos dizendo com clareza que a versão final aguarda o avaliador.
