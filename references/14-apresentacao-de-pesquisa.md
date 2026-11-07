# 14. Apresentação de pesquisa (congresso e banca)

Vale quando `contrato.perfil` é `congresso` ou `banca`. A plateia avalia raciocínio e evidência, e por isso a ordem é argumento, dados, layout e só depois estética. Adaptado de academic-pptx-skill (Gabberflast, MIT) e do estilo academic-research do ppt-master (Hugo He, MIT).

## Antes de montar

- **Um argumento.** Não apresente o artigo inteiro. Escolha a afirmação que cabe no tempo e mande o resto para o apêndice.
- **Orçamento.** Cerca de 1 slide por minuto, contando todos os slides que não são apêndice. Em 15 minutos, de 12 a 15 slides. O construtor avisa acima de 1,1 x `duracao_min`. Ensaie para terminar 1 ou 2 minutos antes.
- **Deck fantasma.** Leia só os títulos, em sequência. Eles precisam contar o argumento inteiro, da pergunta à conclusão. Se não contam, conserte o roteiro antes de construir.

## Títulos-ação

Todo slide de conteúdo tem como título uma frase completa com a conclusão dele. "O efeito persiste após controlar seleção" e não "Resultados". "Municípios pequenos dependem do FPM" e não "Dados". O construtor avisa quando o título tem menos de 4 palavras ou não tem verbo aparente (capa, seção, pergunta, citação, fechamento, referências e apêndice ficam de fora).

## Roteiro e layouts

| Papel | Quantos | Layout | O que precisa aparecer |
|---|---|---|---|
| Capa | 1 | `capa` | título da pesquisa, autoria, instituição, evento |
| Motivação | 1 ou 2 | `numero`, `numeros`, `faixa` | o problema com caso ou número real, com `fonte` |
| Pergunta | 1, até o 3º slide | `pergunta` | a pergunta sozinha na tela |
| Posição na literatura | 1 ou 2 | `comparacao`, `tabela`, `diagrama` (balança) | o que já se sabe e a lacuna, organizado pela relação com este trabalho, com "(Autor, ano)" no texto |
| Contribuição | 1 | `afirmacao` | o que o trabalho acrescenta, no tamanho que os resultados sustentam |
| Dados | 0 ou 1 | `numeros`, `dividido` | origem, N, período, critério de inclusão e viés conhecido |
| Método | 1 ou 2 | `processo`, `diagrama` (cadeia) | desenho, variáveis e escolhas que afetam o resultado |
| Achado | 1 por achado | `evidencia`, `grafico` | um gráfico, a leitura dele em uma frase ao lado, a incerteza |
| Interpretação | 1 ou 2 | `dividido`, `lista` | o que decorre dos dados separado do que os autores acreditam |
| Limitações | 1, slide próprio | `lista`, `tabela` | ameaças reais à validade e a direção de cada uma |
| Conclusão | 1 | `fechamento` | resposta à pergunta, espelhando o slide da pergunta, e contato |
| Referências | 1 | `referencias` | todas as obras citadas, no padrão da área |
| Apêndice | 3 a 5 | `tabela`, `grafico`, `lista`, `evidencia` | respostas preparadas para as perguntas prováveis |

Seções (`secao`) só a partir de 15 slides. No congresso elas costumam sobrar.

## Evidência

- **Um achado por slide.** Um gráfico, com a comparação decisiva marcada em `destaques` e a leitura escrita na tela. O achado nunca existe só na fala.
- **Incerteza visível.** Mostre intervalo, erro padrão ou tamanho da amostra junto da estimativa e diga nas notas o que o intervalo representa. Efeito com incerteza vale mais que significância sozinha.
- **Três registros separados.** Observação ("a taxa caiu 12 pontos"), inferência ("o programa explica parte da queda") e especulação ("talvez o efeito dure"). Use verbos diferentes para cada um e nunca deixe um virar outro ao longo da fala. Correlação não é causa, e o slide diz isso quando for o caso.
- **Resultado nulo ou negativo** aparece sem amaciar.
- **Referência curta no texto**, como "(Riker, 1964)", e completa no slide de referências.

## Fechamento

O slide de conclusão é o último que não é apêndice e fica na tela durante as perguntas. Nunca termine com "Obrigado", "Perguntas?" ou tela vazia. Ao convidar o debate, prefira "Comentários e perguntas são bem-vindos" dito em voz alta.

A ordem final é `fechamento`, `referencias` e os slides com `"apendice": true`. O construtor recusa apêndice antes do fechamento. Prepare de 3 a 5 apêndices a partir das perguntas mais prováveis (por que não outro método, comparação com outro estudo, endogeneidade, representatividade da amostra, robustez). Apêndice pode ser denso, desde que respeite os pisos de fonte, e não entra na regra dos três layouts iguais.

## Tempo

Cada slide pode ter `"minutos"` (tempo previsto). Marque com `"cortavel": true` os slides que podem ser pulados se o tempo apertar, em geral contexto e detalhes de método, nunca pergunta, achado principal ou conclusão. A marca nunca aparece na tela, só na janela do apresentador.

## Banca

Na banca o tempo costuma ser de 20 a 40 minutos e a plateia leu o texto. Reduza motivação, dê mais espaço a método, limitações e contribuição, e prepare apêndices para cada capítulo que a banca pode questionar.
