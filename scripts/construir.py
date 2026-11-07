#!/usr/bin/env python3
"""Constrói o deck: PROJETO/deck.json -> PROJETO/dist/<slug>.html (um arquivo só, offline).

    python3 scripts/construir.py PROJETO [--rascunho]

Valida tudo antes de escrever e imprime cada problema com o número do slide e a correção.
Código de saída 1 quando há ERRO. AVISO não bloqueia a construção, mas o avaliador humano vai ver.
Nunca edite o HTML gerado. Edite deck.json e construa de novo.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import html
import json
import mimetypes
import re
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
SKILL = AQUI.parent
RUNTIME = SKILL / "templates" / "runtime"
FONTES = SKILL / "assets" / "fontes"

LAYOUTS = {
    "capa": [], "secao": [], "imagem-total": ["imagem"], "dividido": [], "faixa": [], "numero": ["numero"],
    "citacao": ["citacao"], "comparacao": ["colunas"], "linha-do-tempo": ["eventos"], "processo": ["passos"],
    "galeria": ["imagens"], "cartoes": ["cartoes"], "grafico": ["grafico"], "tabela": ["tabela"], "pergunta": ["titulo"],
    "afirmacao": ["titulo"], "lista": ["itens"], "diagrama": ["diagrama"], "fechamento": ["itens"], "referencias": [], "livre": ["html"],
    "numeros": ["numeros"], "evidencia": ["grafico"],
}
# layouts em que a imagem é esperada (ou um gráfico/diagrama que faça o papel visual)
PEDEM_VISUAL = {"capa", "secao", "imagem-total", "dividido", "faixa", "numero", "citacao", "pergunta", "afirmacao", "lista", "fechamento", "galeria"}
INDICE = json.loads((SKILL / "templates" / "temas.json").read_text(encoding="utf8"))  # temas, famílias de fonte e paletas
TEMAS = INDICE["temas"]


def faces_do_tema(tema):
    """(família, estilo, peso, woff2) do tema. O itálico só vai para a fonte de corpo, que é onde aparece."""
    t = TEMAS[tema]
    out = []
    for papel in ("titulo", "corpo"):
        fam = t[papel]
        if papel == "corpo" and fam == t["titulo"]:
            out = [x for x in out if x[0] != fam]
        for est, peso, arq in INDICE["familias"][fam]["woff2"]:
            if (est == "normal" or papel == "corpo") and (fam, est, peso, arq) not in out:
                out.append((fam, est, peso, arq))
    return out


def estilo_e_paleta(deck, proj: Path):
    """Aplica "estilo" (biblioteca pessoal) e "paleta" (temas.json) ao deck. O próprio deck sempre vence."""
    nome = deck.get("estilo")
    if nome:
        achou = [p for p in (proj / "estilos" / f"{nome}.json", Path.home() / ".slides-impecaveis" / "estilos" / f"{nome}.json") if p.is_file()]
        if not achou:
            erro(f'deck.json: estilo "{nome}" não encontrado em PROJETO/estilos/ nem em ~/.slides-impecaveis/estilos/.')
        else:
            est = json.loads(achou[0].read_text(encoding="utf8"))
            for k in ("tema", "paleta"):
                if est.get(k) and not deck.get(k):
                    deck[k] = est[k]
            deck["ajustes_tema"] = {**(est.get("ajustes_tema") or {}), **(deck.get("ajustes_tema") or {})}
    pal = deck.get("paleta")
    if pal:
        if pal not in INDICE["paletas"]:
            erro(f'deck.json: paleta "{pal}" não existe. Use uma de {", ".join(INDICE["paletas"])}.')
        else:
            deck["ajustes_tema"] = {**INDICE["paletas"][pal], **(deck.get("ajustes_tema") or {})}
    return deck
CONTRATO = ["tese", "mundo", "historia", "primeira_tela", "publico", "sala"]

ERROS: list[str] = []
AVISOS: list[str] = []


def erro(m):
    ERROS.append(m)


def aviso(m):
    AVISOS.append(m)


def b64(p: Path, mime=None):
    mime = mime or mimetypes.guess_type(str(p))[0] or "application/octet-stream"
    if p.suffix.lower() == ".webp":
        mime = "image/webp"
    if p.suffix.lower() == ".woff2":
        mime = "font/woff2"
    return f"data:{mime};base64," + base64.b64encode(p.read_bytes()).decode()


def textos_do_slide(s):
    """Todos os textos visíveis de um slide, para checagens de fidelidade e de pontuação."""
    if s.get("layout") == "livre" and s.get("html"):  # no livre, só o HTML aparece na tela
        return [x.strip() for x in re.findall(r">([^<>]+)<", re.sub(r"\{\{img:[\w-]+\}\}", "", s["html"])) if x.strip()]
    out = []
    for k in ("titulo", "subtitulo", "texto"):
        if s.get(k):
            out.append(s[k])
    out += s.get("itens") or []
    out += s.get("referencias") or []
    for c in s.get("colunas") or []:
        out += [c.get("titulo", "")] + (c.get("itens") or [])
    for e in s.get("eventos") or []:
        out.append(e.get("texto", ""))
    for p in s.get("passos") or []:
        out += [p.get("titulo", ""), p.get("texto", "")]
    for c in s.get("cartoes") or []:
        out += [c.get("titulo", ""), c.get("texto", "")]
    if s.get("diagrama"):
        out += [str(x) for x in s["diagrama"].get("nos") or []] + ([s["diagrama"]["centro"]] if s["diagrama"].get("centro") else [])
    if s.get("citacao"):
        out.append(s["citacao"].get("texto", ""))
    if s.get("numero"):
        out.append(s["numero"].get("texto", ""))
    return [t for t in out if t]


def validar_ext(s, n, lay):
    """Validações dos tipos de gráfico, diagramas e layouts das extensões (sk-ext-*.js). Use erro() e aviso()."""
    # BLOCO-EXT-INICIO (mantido pela extensão de gráficos e layouts)
    def pal(t, m, onde):  # rótulo curto, para caber a 28 px ou mais
        if len(str(t).split()) > m:
            aviso(f'slide {n}: "{str(t)[:40]}" tem mais de {m} palavras ({onde}). Encurte para caber grande.')

    def num(v):
        try:
            return float(v) if isinstance(v, (int, float)) else float(str(v).replace(".", "").replace(",", "."))
        except ValueError:
            return None
    g, d = s.get("grafico") or {}, s.get("diagrama") or {}
    tg, td = g.get("tipo"), d.get("tipo")
    rot = g.get("rotulos") or []
    for r in rot if tg in ("pontos", "halteres", "empilhadas") else []:
        pal(r, 4, "rótulo do gráfico")
    if tg == "pontos":
        v, lo, hi = g.get("valores") or [], g.get("inferior") or g.get("valores") or [], g.get("superior") or g.get("valores") or []
        if not rot or not (len(rot) == len(v) == len(lo) == len(hi)):
            erro(f"slide {n}: pontos pede rotulos, valores, inferior e superior do mesmo tamanho.")
        elif any(num(a) is None or num(b) is None or num(c) is None or not num(a) <= num(b) <= num(c) for a, b, c in zip(lo, v, hi)):
            erro(f"slide {n}: em pontos, cada valor precisa ficar entre inferior e superior.")
        if len(rot) > 8:
            aviso(f"slide {n}: {len(rot)} estimativas. Até 8 ficam legíveis.")
    elif tg == "halteres":
        if not rot or not (len(rot) == len(g.get("antes") or []) == len(g.get("depois") or [])):
            erro(f"slide {n}: halteres pede rotulos, antes e depois do mesmo tamanho.")
        if len(g.get("nomes") or []) != 2:
            erro(f'slide {n}: halteres pede "nomes" com dois textos, por exemplo ["2010", "2022"].')
        for x in g.get("nomes") or []:
            pal(x, 2, "nome da série")
        if len(rot) > 7:
            aviso(f"slide {n}: {len(rot)} categorias em halteres. Até 7 ficam legíveis.")
    elif tg == "empilhadas":
        se = g.get("series") or []
        if not rot or not 2 <= len(se) <= 6 or any(len(x.get("valores") or []) != len(rot) or not x.get("nome") for x in se):
            erro(f"slide {n}: empilhadas pede rotulos e de 2 a 6 series com nome e um valor por rótulo.")
        for x in se:
            pal(x.get("nome", ""), 2, "nome da série")
        if len(rot) > 6:
            aviso(f"slide {n}: {len(rot)} barras empilhadas. Até 6 ficam legíveis.")
    elif tg == "dispersao":
        pts = g.get("pontos") or []
        if len(pts) < 3 or any(num(p.get("x")) is None or num(p.get("y")) is None for p in pts):
            erro(f"slide {n}: dispersao pede pelo menos 3 pontos, cada um com x e y numéricos.")
        com = [p["rotulo"] for p in pts if p.get("rotulo")]
        if len(com) > 6:
            aviso(f"slide {n}: {len(com)} pontos com rótulo. Só os 6 primeiros aparecem.")
        for r in com:
            pal(r, 3, "rótulo de ponto")
    elif tg == "linha":
        tam = len(rot)
        for a in g.get("anotacoes") or []:
            if not isinstance(a.get("i"), int) or not 0 <= a["i"] < tam:
                erro(f"slide {n}: anotação com índice i fora da série (0 a {tam - 1}).")
            pal(a.get("texto", ""), 8, "anotação")
        if g.get("trecho_final") and (len(g.get("series") or [1]) > 1 or not 0 < g["trecho_final"] < tam):
            erro(f"slide {n}: trecho_final vale só para uma série e precisa ser menor que o número de pontos.")
    elif tg == "barras" and g.get("anotacao"):
        a = g["anotacao"]
        pal(a if isinstance(a, str) else a.get("texto", ""), 8, "anotação")
    if td == "funil":
        et = d.get("etapas") or d.get("nos") or []
        if not 3 <= len(et) <= 5:
            erro(f"slide {n}: funil pede de 3 a 5 etapas.")
        for e in et:
            pal(e if isinstance(e, str) else e.get("rotulo", ""), 4, "etapa do funil")
    elif td == "iceberg":
        if not d.get("acima") or not d.get("abaixo") or len(d["acima"]) > 2 or len(d["abaixo"]) > 3:
            erro(f"slide {n}: iceberg pede acima (1 ou 2 textos) e abaixo (1 a 3 textos).")
        for t in (d.get("acima") or []) + (d.get("abaixo") or []):
            pal(t, 7, "iceberg")
    elif td == "matriz":
        if len(d.get("quadrantes") or []) != 4 or len(d.get("eixo_x") or []) != 2 or len(d.get("eixo_y") or []) != 2:
            erro(f"slide {n}: matriz pede quadrantes (4 textos), eixo_x e eixo_y (2 textos cada).")
        for t in d.get("quadrantes") or []:
            pal(t, 5, "quadrante")
        if d.get("destaque") is not None and d["destaque"] not in (0, 1, 2, 3):
            erro(f"slide {n}: destaque da matriz é o índice do quadrante, de 0 a 3.")
    elif td == "venn":
        cj = d.get("conjuntos") or d.get("nos") or []
        if not 2 <= len(cj) <= 3:
            erro(f"slide {n}: venn pede 2 ou 3 conjuntos.")
        for t in cj:
            pal(t, 2, "conjunto")
        pal(d.get("intersecao", ""), 3, "interseção")
    if lay == "numeros":
        ns = s.get("numeros") or []
        if not 3 <= len(ns) <= 6 or any(not str(x.get("valor", "")).strip() for x in ns):
            erro(f'slide {n} (numeros): de 3 a 6 itens em "numeros", cada um com "valor".')
        if not s.get("fonte"):
            erro(f'slide {n} (numeros): falta "fonte". Todo número precisa de origem real.')
        for x in ns:
            if len(str(x.get("valor", ""))) > 6:
                aviso(f'slide {n}: o valor "{x.get("valor")}" é longo. Use unidade ("156,5" e "mi") para o número ficar grande.')
            pal(x.get("texto", ""), 9, "texto do número")
    elif lay == "evidencia":
        if not s.get("titulo"):
            erro(f"slide {n} (evidencia): o título é a afirmação que o gráfico sustenta.")
        elif len(s["titulo"]) > 90:
            aviso(f"slide {n} (evidencia): título longo. A afirmação cabe em duas linhas (até 90 caracteres).")
        if s.get("itens") or s.get("texto"):
            aviso(f"slide {n} (evidencia): itens e texto não aparecem neste layout. A anotação vai no gráfico.")
    elif lay == "linha-do-tempo" and s.get("orientacao") not in (None, "horizontal", "vertical"):
        erro(f'slide {n}: orientacao é "vertical" ou "horizontal".')
    elif lay == "linha-do-tempo" and s.get("orientacao") == "vertical" and not 3 <= len(s.get("eventos") or []) <= 6:
        erro(f"slide {n}: a linha do tempo vertical pede de 3 a 6 eventos.")
    # BLOCO-EXT-FIM


def contraindicacoes(s, n, lay, imgs):
    """Avisos de layout usado fora do que ele comporta (tabela em references/04-layouts.md). Não bloqueiam."""
    def palavras(t):
        return len(re.findall(r"\S+", t or ""))

    if lay == "citacao":
        k = palavras((s.get("citacao") or {}).get("texto") or s.get("texto"))
        if k > 40:
            aviso(f"slide {n} (citacao): {k} palavras. Acima de 40 a citação desce até o piso e perde o tamanho de citação. Recorte o trecho que importa.")
    elif lay == "linha-do-tempo" and s.get("orientacao") != "vertical":
        k = len(s.get("eventos") or [])
        if k < 3:
            aviso(f'slide {n} (linha-do-tempo): {k} eventos. Com duas datas o slide é uma comparação; use "comparacao".')
    elif lay == "processo":
        k = len(s.get("passos") or [])
        if k < 3:
            aviso(f'slide {n} (processo): {k} passos. O layout pede de 3 a 5; com dois use "comparacao".')
        elif k > 5:
            aviso(f'slide {n} (processo): {k} passos. O layout pede de 3 a 5; divida em dois slides ou use "diagrama".')
    elif lay == "galeria":
        k = len(s.get("imagens") or [])
        if k < 2:
            aviso(f'slide {n} (galeria): {k} imagem. O layout pede de 2 a 4; com uma use "imagem-total".')
        elif k > 4:
            aviso(f"slide {n} (galeria): {k} imagens. O layout pede de 2 a 4; divida em duas galerias.")
    elif lay == "cartoes":
        k = len(s.get("cartoes") or [])
        if k < 3:
            aviso(f'slide {n} (cartoes): {k} cartões. O layout pede 3 ou 4; com dois use "comparacao".')
        elif k > 4:
            aviso(f'slide {n} (cartoes): {k} cartões. O layout pede 3 ou 4; com cinco ou mais use "lista".')
    elif lay == "tabela":
        t = s.get("tabela") or {}
        col, lin = len(t.get("cabecalho") or []), len(t.get("linhas") or [])
        if col > 4 or lin > 5:
            aviso(f"slide {n} (tabela): {col} colunas e {lin} linhas. O limite é 4 e 5; acima disso a célula encosta no piso. Divida em duas tabelas ou resuma as linhas.")
    elif lay == "numeros" and s.get("torres"):
        un = {str(x.get("unidade") or "").strip().lower() for x in s.get("numeros") or []}
        if len(un) > 1:
            aviso(f'slide {n} (numeros): "torres" compara alturas, mas as unidades são diferentes ({", ".join(sorted(x or "sem unidade" for x in un))}). Use a mesma unidade ou tire "torres".')
    elif lay == "imagem-total":
        k = s.get("imagem")
        im = imgs.get(k) or {}
        if im.get("documento") and not im.get("conter"):
            aviso(f'slide {n} (imagem-total): "{k}" é documento e a tela cheia corta a página. Use "dividido" ou marque "conter": true.')


def tema_automatico(deck):
    """Tema escolhido pelo contrato (perfil, mundo, público, sala), sem construir amostras."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from amostra_temas import sugerir
    return sugerir(deck)[0][0]


def validar(deck, proj: Path):
    if deck.get("tema") in (None, "", "auto"):
        deck["tema"] = tema_automatico(deck)
        aviso(f'tema escolhido automaticamente pelo contrato: "{deck["tema"]}". Grave "tema" no deck.json para fixar.')
    tema = deck.get("tema")
    if tema not in TEMAS:
        erro(f'deck.json: "tema" precisa ser um de {", ".join(TEMAS)} (recebido: {tema!r}).')
    aj = deck.get("ajustes_tema")
    if aj is not None:
        if not isinstance(aj, dict):
            erro('deck.json: "ajustes_tema" precisa ser um objeto, por exemplo {"acento": "#7A1F2B"}.')
        else:
            for k in aj:
                if k.lstrip("-").startswith("f-"):
                    aviso(f'ajustes_tema: "{k}" troca a família de fonte, mas só as fontes do tema vão embutidas. O HTML pode cair numa fonte do sistema.')
    con = deck.get("contrato") or {}
    falta = [k for k in CONTRATO if not str(con.get(k, "")).strip() or "PREENCHER" in str(con.get(k, ""))]
    if falta:
        erro("deck.json: o contrato está incompleto (" + ", ".join(falta) + "). Preencha antes de construir. Exemplo em exemplos/federalismo/deck.json.")
    slides = deck.get("slides") or []
    if not slides:
        erro("deck.json: nenhum slide em \"slides\".")
    imgs = deck.get("imagens") or {}
    for k, im in imgs.items():
        p = proj / im.get("arquivo", "")
        if not p.is_file():
            erro(f'imagem "{k}": arquivo não encontrado ({im.get("arquivo")}).')
            continue
        if not (Path(str(p) + ".json")).is_file():
            erro(f'imagem "{k}": falta a proveniência {im.get("arquivo")}.json (use scripts/imagens.py baixar e tratar).')
        elif str(json.loads(Path(str(p) + ".json").read_text(encoding="utf8")).get("licenca", "")).upper().startswith("VERIFICAR"):
            aviso(f'imagem "{k}": a licença está marcada VERIFICAR. Leia os direitos na página do item e registre a decisão no .json.')
        if not im.get("credito"):
            erro(f'imagem "{k}": falta "credito" (aparece na tecla I).')
        if not im.get("legenda") and (deck.get("legendas_nas_imagens") or im.get("mostrar_legenda")):
            aviso(f'imagem "{k}": a pessoa pediu legendas, mas esta imagem não tem "legenda".')
        if not im.get("alt"):
            aviso(f'imagem "{k}": sem "alt" (texto alternativo para leitor de tela).')
        if re.search(r"<(?!/?i>|/?em>|br>)", im.get("legenda", "")):
            erro(f'imagem "{k}": a legenda só aceita <i>, <em> e <br>.')
        try:
            from PIL import Image
            w, h = Image.open(p).size
            if w < 1200 and h < 1200:
                aviso(f'imagem "{k}": só {w}x{h} px. Em tela cheia vai parecer borrada. Prefira lado maior >= 1600 px.')
        except Exception:  # noqa: BLE001
            pass
    # checagens baratas que substituem o olhar quando o modelo não vê imagem (scripts/checagens.py)
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import checagens
    for onde, k, sug, de_slide in checagens.campos_desconhecidos(deck):
        msg = f'{onde}: o campo "{k}" não existe e seria ignorado em silêncio.' + (f' Quis dizer "{sug}"?' if sug else " Veja references/04-layouts.md.")
        (erro if de_slide else aviso)(msg)
    for m in checagens.estilo_texto(deck):
        erro(m)
    for m in checagens.imagens_repetidas(deck, proj):
        erro(m)
    if imgs:
        ruins, _metodo = checagens.texto_em_imagem(deck, proj)
        for m in ruins:
            erro(m)
        checagens.marcar_pessoas(deck, proj)
    # transições e morph (references/08-movimento.md)
    for n, s in [(0, deck)] + list(enumerate(slides, 1)):
        t, onde = s.get("transicao"), f"slide {n}" if n else "deck.json"
        if t is not None and t not in ("dissolve", "sobe", "assenta", "floresce", "respiro"):
            erro(f'{onde}: "transicao" {t!r} não existe. Use dissolve, sobe, assenta, floresce ou respiro.')
        if t == "respiro" and s.get("layout") != "secao":
            aviso(f'{onde}: "respiro" passa pelo fundo e serve só para entrar num slide de seção.')
        it = s.get("intensidade")
        if it is not None and it not in ("sobrio", "padrao", "vivo"):
            erro(f'{onde}: "intensidade" {it!r} não existe. Use sobrio, padrao ou vivo.')
        if n and s.get("etapas") and not (s.get("itens") or s.get("grafico") or s.get("diagrama")):
            aviso(f'slide {n}: "etapas" revela itens, peças de gráfico ou caixas de diagrama, e este slide não tem nenhum deles.')
        if s.get("morph") and n and not s.get("imagem"):
            aviso(f'slide {n}: "morph" liga a imagem principal, mas o slide não tem "imagem".')
    usados = set()
    seq = []
    sem_visual = 0
    for n, s in enumerate(slides, 1):
        lay = s.get("layout")
        if lay == "?":
            erro(f"slide {n}: escolha o layout (\"?\" é o marcador do esqueleto). Veja references/04-layouts.md.")
            continue
        if lay not in LAYOUTS:
            erro(f'slide {n}: layout {lay!r} não existe. Use um de: {", ".join(LAYOUTS)}.')
            continue
        if s.get("rascunho_layout"):
            aviso(f"slide {n}: layout sugerido automaticamente. Escolha pelo significado da ideia e apague \"rascunho_layout\".")
        for campo in LAYOUTS[lay]:
            if not s.get(campo):
                erro(f'slide {n} ({lay}): falta o campo "{campo}".')
        refs = [s.get("imagem")] + list(s.get("imagens") or []) + [c.get("imagem") for c in (s.get("colunas") or []) + (s.get("cartoes") or [])]
        refs += re.findall(r"\{\{img:([\w-]+)\}\}", s.get("html") or "")
        for r in [x for x in refs if x]:
            usados.add(r)
            if r not in imgs:
                erro(f'slide {n}: imagem "{r}" não declarada em "imagens".')
        if lay in PEDEM_VISUAL and not (s.get("imagem") or s.get("imagens") or s.get("grafico") or s.get("diagrama")):
            sem_visual += 1
            aviso(f"slide {n} ({lay}): sem imagem, gráfico ou diagrama. O motor desenha uma arte do tema, mas imagem real é a regra sempre que possível.")
        if s.get("grafico"):
            g = s["grafico"]
            if not s.get("fonte"):
                erro(f'slide {n}: gráfico sem "fonte". Todo número precisa de origem real.')
            if g.get("tipo", "barras") in ("barras", "barras-h") and len(g.get("rotulos", [])) != len(g.get("valores", [])):
                erro(f"slide {n}: o gráfico tem {len(g.get('rotulos', []))} rótulos e {len(g.get('valores', []))} valores.")
        if lay == "numero" and not s.get("fonte"):
            erro(f'slide {n}: número em destaque sem "fonte".')
        for chave, frases in (s.get("destaques") or {}).items():
            alvo = s.get("titulo") if chave == "titulo" else (s.get("citacao") or {}).get("texto") if chave == "citacao" else s.get("texto") if chave == "texto" else ((s.get("itens") or [])[int(chave)] if chave.isdigit() and int(chave) < len(s.get("itens") or []) else None)
            for f in frases:
                if not alvo or f not in alvo:
                    erro(f'slide {n}: destaque "{f}" não aparece literalmente em {chave!r}.')
        if len(s.get("itens") or []) > 5:
            aviso(f"slide {n}: {len(s['itens'])} itens. Acima de 5 a fonte encosta no piso. Divida o slide.")
        if s.get("notas") is None:
            aviso(f"slide {n}: sem notas do apresentador.")
        if lay == "livre":
            if re.search(r"https?://", s.get("html", "")):
                erro(f"slide {n}: o HTML livre aponta para a rede. Tudo precisa estar embutido.")
            aviso(f"slide {n}: layout livre. Os pisos de fonte e a ocupação serão medidos como em qualquer outro.")
        validar_ext(s, n, lay)
        contraindicacoes(s, n, lay, imgs)
        if not s.get("apendice"):  # apêndice fica fora da regra dos três layouts iguais
            seq.append((n, lay))
        for t in textos_do_slide(s):
            if re.search(r"[\U0001F300-\U0001FAFF☀-➿]", t):
                erro(f"slide {n}: emoji ou símbolo no texto ({t[:40]}...). Use glifos desenhados ou nada.")
    contagem = {}
    for s in slides:
        for r in set([s.get("imagem")] + list(s.get("imagens") or []) + [c.get("imagem") for c in (s.get("colunas") or []) + (s.get("cartoes") or [])]
                     + re.findall(r"\{\{img:([\w-]+)\}\}", s.get("html") or "")):
            if r:
                contagem[r] = contagem.get(r, 0) + 1
    for k, v in contagem.items():
        if v > 2:
            aviso(f'imagem "{k}" aparece em {v} slides. Repetição cansa. Uma volta no fechamento basta.')
    for k in imgs:
        if k not in usados and k != (deck.get("capa") or {}).get("imagem"):
            aviso(f'imagem "{k}" declarada e não usada.')
    for i in range(2, len(seq)):
        if seq[i][1] == seq[i - 1][1] == seq[i - 2][1] and seq[i][1] not in ("livre",):
            erro(f"slides {seq[i - 2][0]} a {seq[i][0]}: três slides seguidos com o layout {seq[i][1]!r}. Varie.")
    # perfil, apêndice e tempo (references/14-apresentacao-de-pesquisa.md)
    perfil = con.get("perfil") or "aula"
    if perfil not in ("aula", "congresso", "banca", "palestra", "gestores"):
        erro(f'contrato.perfil {perfil!r} não existe. Use aula, congresso, banca, palestra ou gestores.')
    ap = [n for n, s in enumerate(slides, 1) if s.get("apendice")]
    if ap:
        depois = [n for n, s in enumerate(slides, 1) if not s.get("apendice") and n > ap[0]]
        if depois:
            erro(f"slide {ap[0]}: apêndice antes do slide {depois[0]} ({slides[depois[0] - 1].get('layout')}). "
                 "Os apêndices vêm no fim, depois de fechamento e referencias.")
        if not any(s.get("layout") == "fechamento" for s in slides):
            aviso("há apêndice mas nenhum slide fechamento. A conclusão fica na tela durante as perguntas, antes do apêndice.")
    corpo = [s for s in slides if not s.get("apendice")]
    dur = con.get("duracao_min")
    mins = sum(s["minutos"] for s in corpo if isinstance(s.get("minutos"), (int, float)))
    if isinstance(dur, (int, float)) and mins > dur:
        aviso(f'a soma de "minutos" dos slides ({mins:g}) passa de duracao_min ({dur}). Marque slides "cortavel" ou corte.')
    if perfil in ("congresso", "banca"):
        if isinstance(dur, (int, float)) and len(corpo) > 1.1 * dur:
            aviso(f"perfil {perfil}: {len(corpo)} slides fora do apêndice para {dur} min. A regra é cerca de 1 por minuto. "
                  'Mova detalhes para o apêndice ("apendice": true).')
        if not ap:
            aviso(f'perfil {perfil}: nenhum slide de apêndice. Prepare de 3 a 5 para as perguntas prováveis ("apendice": true).')
        verbo = re.compile(r"(?:ar|er|ir|am|em|ou|eu|iu|aram|eram|iram|ava|avam|ará|erá|irá|ando|endo|indo)$")
        comuns = {"é", "são", "foi", "foram", "era", "há", "tem", "têm", "está", "estão", "pode", "podem", "deve", "devem", "vai",
                  "faz", "dá", "cai", "sobe", "cresce", "muda", "aumenta", "reduz", "explica", "mostra", "indica", "sugere",
                  "persiste", "depende", "afeta", "existe", "resiste", "concentra", "decide", "define", "importa", "falha"}
        nao_verbo = {"em", "sem", "nem", "quem", "bem", "também", "porém", "além", "ou", "eu", "seu", "meu", "teu", "por", "mar", "lugar"}
        for n, s in enumerate(slides, 1):
            if s.get("apendice") or s.get("layout") in ("capa", "secao", "referencias", "fechamento", "pergunta", "citacao"):
                continue
            pal = re.findall(r"[\wÀ-ÿ]+", re.sub(r"[*~]", " ", s.get("titulo") or "").lower())
            tem_verbo = any(p in comuns or (p not in nao_verbo and verbo.search(p)) for p in pal)
            if len(pal) < 4 or not tem_verbo:
                aviso(f'slide {n} ({s.get("layout")}): título-ação esperado no perfil {perfil}. "{s.get("titulo", "")}" '
                      'parece rótulo. Escreva a conclusão em frase completa ("O efeito persiste após controlar seleção").')
    if slides:
        com_img = sum(1 for s in slides if s.get("imagem") or s.get("imagens") or "{{img:" in (s.get("html") or "")
                      or any(c.get("imagem") for c in (s.get("colunas") or []) + (s.get("cartoes") or [])))
        frac = com_img / len(slides)
        if frac < 0.5:
            aviso(f"só {com_img} de {len(slides)} slides têm imagem real ({frac:.0%}). A meta é pelo menos metade, sempre que houver imagem pertinente.")
    if (deck.get("modo_texto") or "autoral") == "verbatim":
        origem = proj / "texto_origem.json"
        if not origem.is_file():
            erro("modo_texto verbatim exige texto_origem.json (gerado por scripts/extrair_texto.py).")
        else:
            src = json.loads(origem.read_text(encoding="utf8"))
            norm = lambda xs: sorted(re.sub(r"\s+", " ", x).strip() for x in xs if x and x.strip())  # noqa: E731
            for n, (a, b) in enumerate(zip(src, slides), 1):
                # cada título e item da origem precisa aparecer inteiro em algum campo visível do slide
                # (itens, cartões, passos, colunas, HTML livre...), e nada além deles.
                ta = norm([a.get("titulo") or ""] + list(a.get("itens") or []))
                tb = norm(dict.fromkeys(textos_do_slide(b)))
                if ta != tb:
                    falta = [x for x in ta if x not in tb]
                    sobra = [x for x in tb if x not in ta]
                    erro(f"slide {n}: o texto difere da origem (modo verbatim). Não reescreva."
                         + (f" Falta: {falta[:2]}." if falta else "") + (f" Sobra: {sobra[:2]}." if sobra else ""))
            if len(src) != len(slides):
                erro(f"modo verbatim: a origem tem {len(src)} slides e o deck tem {len(slides)}.")


def montar(deck, proj: Path, rascunho=False):
    tema = deck.get("tema", "tabuleiro")
    css = "\n".join(f.read_text(encoding="utf8") for f in [RUNTIME / "sk.css", RUNTIME / "temas.css", *sorted(RUNTIME.glob("sk-ext-*.css"))])
    aj = deck.get("ajustes_tema") or {}
    if aj:  # tokens do tema trocados pelo projeto (cores, campos, raio). O contraste é medido de novo em verificar.py.
        decl = ";".join(f"--{re.sub(r'[^a-z0-9-]', '', k.lstrip('-'))}:{re.sub(r'[;{}<>]', '', str(v))}" for k, v in aj.items())
        css += f'\nhtml[data-tema="{tema}"]{{{decl}}}\n'
    faces = []
    for fam, est, peso, arq in faces_do_tema(tema):
        faces.append(f"@font-face{{font-family:'{fam}';font-style:{est};font-weight:{peso};font-display:block;src:url({b64(FONTES / arq)}) format('woff2')}}")
    dados = json.loads(json.dumps(deck))
    dados["arte_tema"] = TEMAS[tema]["arte"]
    creditos = list(deck.get("creditos_extra") or [])
    for k, im in (dados.get("imagens") or {}).items():
        im["dados"] = b64(proj / im["arquivo"])
        im["legenda_texto"] = re.sub("<[^>]+>", "", im.get("legenda", ""))
        if im.get("credito") and im["credito"] not in creditos:
            creditos.append(im["credito"])
    for n, s in enumerate(dados.get("slides", []), 1):
        if s.get("fonte"):  # a fonte de cada slide sai da tela e vai para a tecla I e para as notas
            c = f"Slide {n}. " + re.sub(r"^Fonte:\s*", "", s["fonte"])
            if c not in creditos:
                creditos.append(c)
    dados["creditos"] = creditos
    js_deck = json.dumps(dados, ensure_ascii=False).replace("</", "<\\/")
    con = deck.get("contrato") or {}
    comentario = "\n".join(f"  {k.upper()}: {html.escape(str(v))}" for k, v in con.items())
    titulo = html.escape(deck.get("titulo", "Apresentação"))
    # extensões opcionais (tipos de gráfico, diagramas, layouts) entram antes do motor
    corpo = "\n".join(f.read_text(encoding="utf8") for f in sorted(RUNTIME.glob("sk-ext-*.js"))) + "\n" + (RUNTIME / "sk.js").read_text(encoding="utf8")
    return f"""<!doctype html>
<html lang="{html.escape(deck.get('idioma', 'pt-BR'))}" data-tema="{tema}"{' class="sk-rascunho"' if rascunho else ''}>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{titulo}</title>
<meta name="generator" content="slides-impecaveis">
<!-- CONTRATO DE DESIGN
{comentario}
-->
<style>
{chr(10).join(faces)}
{css}
</style>
</head>
<body>
<main id="sk-palco" aria-live="polite"></main>
<script>window.SK_DECK={js_deck};</script>
<script>
{corpo}
</script>
</body>
</html>
"""


def slug(s):
    s = re.sub(r"[^\w\s-]", "", s.lower(), flags=re.U)
    s = re.sub(r"[\s_]+", "-", s).strip("-")
    import unicodedata
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode() or "deck"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("projeto")
    ap.add_argument("--rascunho", action="store_true", help="marca todos os slides como RASCUNHO")
    ap.add_argument("--slug", action="store_true", help="só imprime o nome do arquivo de saída")
    ap.add_argument("--curto", action="store_true", help="imprime só os erros e o número de avisos (para economizar leitura)")
    a = ap.parse_args()
    proj = Path(a.projeto).resolve()
    dj = proj / "deck.json"
    if not dj.is_file():
        print(f"ERRO {dj} não existe. Crie com scripts/novo_projeto.py.")
        return 1
    try:
        deck = json.loads(dj.read_text(encoding="utf8"))
    except json.JSONDecodeError as e:
        print(f"ERRO deck.json não é JSON válido: linha {e.lineno}, coluna {e.colno}: {e.msg}")
        return 1
    nome = deck.get("slug") or slug(deck.get("titulo", "deck"))
    if a.slug:
        print(nome)
        return 0
    deck = estilo_e_paleta(deck, proj)
    validar(deck, proj)
    if a.curto:
        if AVISOS:
            print(f"{len(AVISOS)} aviso(s), que não bloqueiam. Lista completa sem --curto.")
    else:
        for m in AVISOS:
            print("AVISO", m)
    for m in ERROS:
        print("ERRO ", m)
    if ERROS:
        print(f"\n{len(ERROS)} erro(s). Corrija e rode de novo.")
        return 1
    saida = proj / "dist" / f"{nome}.html"
    saida.parent.mkdir(parents=True, exist_ok=True)
    pagina = montar(deck, proj, a.rascunho)
    saida.write_text(pagina, encoding="utf8", newline="")  # sem newline="" o Windows grava CRLF e o hash da trava nunca confere
    h = hashlib.sha256(pagina.encode("utf8")).hexdigest()[:16]
    (proj / "dist" / "build.json").write_text(json.dumps({"arquivo": saida.name, "hash": h, "slides": len(deck.get("slides", [])),
                                                           "rascunho": a.rascunho}, indent=1), encoding="utf8")
    mb = saida.stat().st_size / 1e6
    print(f"OK {saida} ({len(deck.get('slides', []))} slides, {mb:.1f} MB, hash {h}){' [RASCUNHO]' if a.rascunho else ''}")
    if mb > 25:
        print("AVISO arquivo grande. Reduza imagens com scripts/imagens.py tratar --max 1800 --qualidade 78.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
