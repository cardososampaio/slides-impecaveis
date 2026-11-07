# 02. Texto

## Formato de entrada (`&&&`)

Funciona igual para `.md`, `.txt` e `.docx`.

```
&&&
**Título do slide**
- primeiro item
- segundo item
&&&
- slide sem título, só itens
&&&
```

Linha inteira em negrito é título. Linha que começa com `- `, `* `, `• ` ou número é item. `&&&` sozinho na linha separa slides e nunca aparece na tela.

## Dois modos

**verbatim.** O texto da pessoa entra exatamente como está. `construir.py` confere se cada título e cada item de `texto_origem.json` aparece inteiro em algum campo visível do slide (itens, cartões, passos, colunas, nós de diagrama ou HTML livre) e se nada foi acrescentado, e recusa qualquer diferença. Mudar o layout é permitido, reescrever não. Se um slide não couber no piso de fonte, você propõe a divisão e a pessoa decide. A divisão é feita na origem (o arquivo dela) e o texto é extraído de novo. Erros de digitação e citações coladas ("Simetal,2018") são mostrados à pessoa, nunca corrigidos por conta própria.

**autoral.** Você redige. Regras abaixo.

## Como redigir (modo autoral)

Para cada slide, nesta ordem.

1. **Ideia visível.** O que a plateia precisa entender. Vira o título, de preferência como afirmação ("Municípios também são federação") e não como rótulo ("Municípios").
2. **Evidência.** Caso, número, data, documento ou mecanismo que sustenta a ideia. Quando a referência precisa aparecer, ela entra curta no fim da frase, como "(Riker, 1964)". Nunca como linha separada de "Fonte" ou "Definição baseada em".
3. **Limite.** Quando a afirmação tiver condição ou incerteza, diga.
4. **Notas.** O que você diria em voz alta, com tempo estimado. O slide carrega pouco texto, as notas carregam o resto.

Comece pelo concreto. Uma data, um nome, um número com fonte, uma decisão, um documento.

## Proibições (reescreva se aparecer)

- Frase de anúncio que promete uma ideia em vez de apresentá-la.
- "Não apenas X, mas também Y" e "não se trata de X, trata-se de Y" sem necessidade.
- Trio de adjetivos genéricos.
- Palavras de efeito usadas para soar importantes ("cenário", "jornada", "panorama", "inovador", "robusto").
- "É importante notar", "vale destacar", "neste contexto".
- Gerúndio conclusivo ("garantindo", "promovendo", "contribuindo para").
- Travessão ou ponto e vírgula como enfeite, emoji, caixa alta como grito.
- Título que só nomeia o assunto quando dá para afirmar algo.

Citações, nomes oficiais e termos técnicos ficam literais. A pessoa pode ter uma lista própria de palavras e pontuação a evitar. Pergunte e respeite.

## Densidade

| Situação | Limite |
|---|---|
| capa | até 10 palavras no título, subtítulo de uma linha |
| abertura de seção | até 8 palavras no título |
| apresentação falada | 3 a 4 itens, cerca de 30 palavras visíveis |
| leitura autônoma (documento) | até 5 itens e 75 palavras, ainda com fonte de 44 px |

### Por perfil (`contrato.perfil`)

| Perfil | Itens por slide | Palavras visíveis | Título | Slides |
|---|---|---|---|---|
| `aula` (padrão) | 3 a 4 | cerca de 30 | afirmação curta | 20 a 30 |
| `congresso` | 2 a 4 | até 40 | título-ação (frase completa com a conclusão) | cerca de 1 por minuto, mais 3 a 5 de apêndice |
| `banca` | 2 a 4 | até 40 | título-ação | cerca de 1 por minuto, mais 3 a 5 de apêndice |
| `palestra` | 1 a 3 | até 20 | afirmação curta | livre |
| `gestores` | 2 a 3, uma ideia | até 25 | afirmação na linguagem da administração pública | livre |

No perfil `gestores`, cite a norma pelo número e pelo nome curto, como "Lei 13.709/2018 (LGPD)" ou "Lei 12.527/2011 (Acesso à Informação)", e prefira o vocabulário do serviço público (órgão, gestor, processo, controle, prestação de contas). Confira cada norma na fonte oficial antes de usar.

Nos perfis `congresso` e `banca`, títulos lidos em sequência contam o argumento (deck fantasma), e o construtor avisa quando o título de um slide de conteúdo tem menos de 4 palavras ou não tem verbo aparente. Roteiro completo em `references/14-apresentacao-de-pesquisa.md`.

Se dois itens têm o mesmo peso e não cabem, divida o slide. Reduza texto antes de reduzir fonte, e nunca reduza abaixo do piso.

## Notas do apresentador

Campo `notas` de cada slide. Comece pelo tempo ("2 min."), diga o que fazer (perguntar, mostrar, ler) e acrescente o que não coube no slide. As notas aparecem na tecla N, na janela do apresentador (tecla P) e nas notas do PPTX.

O tempo também pode ir no campo `minutos`, e os campos `cortavel` e `apendice` organizam a fala (ver a tabela de campos comuns em `references/04-layouts.md`).
