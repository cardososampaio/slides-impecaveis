#!/usr/bin/env python3
"""Lê o texto dos slides (.md, .txt, .docx, .pptx ou .pdf) e prepara o projeto.

    python3 scripts/extrair_texto.py aula.docx PROJETO [--verbatim] [--sugerir]

Formato da origem (igual para .md, .txt e .docx):
    &&&
    **Título do slide**          linha inteira em negrito = título
    - primeiro bullet            item de lista, "- ", "* " ou "• " = bullet
    - segundo bullet
    &&&

Gera:
  PROJETO/texto_origem.json   o texto exatamente como veio (só espaços repetidos são colapsados)
  PROJETO/deck.json           se ainda não existir: esqueleto com os slides, layout "?" para você escolher
                              (com --sugerir, um rascunho de layouts variados marcado "rascunho_layout")
.pptx  cada slide vira um bloco (título do espaço de título, demais parágrafos como itens). As notas do
       apresentador vão para "notas" no deck.json. Imagens não são extraídas, só listadas (peça a proveniência).
.pdf   cada página vira um bloco, sempre em modo autoral: o texto é insumo, não verbatim (pypdf ou pdftotext).

Com --verbatim o deck fica em modo_texto "verbatim": o construtor recusa qualquer diferença em relação à origem.
Ao final, lista avisos para o avaliador humano: slides com mais de 4 bullets, bullets longos,
slides sem título, marcas estranhas e possíveis erros de digitação em citações (ex.: "Simetal,2018").
Nada é corrigido automaticamente: a pessoa decide.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

BULLET = re.compile(r"^\s*(?:[-*•–]\s+|\d+[.)]\s+)")


def linhas_docx(p: Path):
    from docx import Document
    doc = Document(str(p))
    out = []
    for par in doc.paragraphs:
        txt = par.text.replace(" ", " ")
        if not txt.strip():
            out.append("")
            continue
        runs = [r for r in par.runs if r.text.strip()]
        negrito = bool(runs) and all(r.bold or (r.style is not None and r.style.font.bold) for r in runs)
        estilo = (par.style.name or "").lower() if par.style is not None else ""
        lista = "list" in estilo or "lista" in estilo or par._p.pPr is not None and par._p.pPr.numPr is not None
        if txt.strip() == "&&&":
            out.append("&&&")
        elif negrito:
            out.append("**" + txt.strip() + "**")
        elif lista:
            out.append("- " + txt.strip())
        else:
            out.append(txt.strip())
    return out


def limpo(t):
    return re.sub(r"\s+", " ", (t or "").replace("\u000b", " ")).strip()


def slides_pptx(p: Path):
    """Um bloco por slide. Devolve (slides, notas, avisos)."""
    from pptx import Presentation
    from pptx.enum.shapes import MSO_SHAPE_TYPE, PP_PLACEHOLDER
    prs = Presentation(str(p))
    slides, notas, avisos, com_img = [], [], [], []
    tit_tipos = {PP_PLACEHOLDER.TITLE, PP_PLACEHOLDER.CENTER_TITLE}

    def formas(shs):
        for sh in shs:
            if sh.shape_type == MSO_SHAPE_TYPE.GROUP:
                yield from formas(sh.shapes)
            else:
                yield sh
    for n, sl in enumerate(prs.slides, 1):
        titulo, itens, imgs = None, [], 0
        for sh in sorted(formas(sl.shapes), key=lambda s: ((s.top or 0), (s.left or 0))):
            if sh.shape_type == MSO_SHAPE_TYPE.PICTURE or type(sh).__name__ == "PlaceholderPicture":
                imgs += 1
                continue
            if sh.is_placeholder and sh.placeholder_format.type in tit_tipos and sh.has_text_frame and titulo is None:
                titulo = limpo(sh.text_frame.text) or None
                continue
            if sh.has_text_frame:
                itens += [limpo(pa.text) for pa in sh.text_frame.paragraphs if limpo(pa.text)]
            elif getattr(sh, "has_table", False) and sh.has_table:
                itens += [" | ".join(limpo(c.text) for c in r.cells) for r in sh.table.rows]
        if imgs:
            com_img.append(str(n))
        nt = limpo(sl.notes_slide.notes_text_frame.text) if sl.has_notes_slide else ""
        if titulo or itens:
            slides.append({"titulo": titulo, "itens": itens})
            notas.append(nt)
    if com_img:
        avisos.append(f"slides {', '.join(com_img)} do PPTX original têm imagens. Elas não foram extraídas. Pergunte a origem e a licença de cada uma e registre com imagens.py baixar local.")
    return slides, notas, avisos


LIGA = re.compile(r"\b(?:a|o|as|os|um|uma|de|da|do|das|dos|e|em|na|no|nas|nos|pela|pelo|pelas|pelos|para|por|com|que|sem|sobre|entre|ao|à|the|of|and|to|in)$", re.I)


def slides_pdf(p: Path):
    """Um bloco por página. A primeira linha curta vira título, os parágrafos viram itens."""
    import shutil
    import subprocess
    if shutil.which("pdftotext"):  # mais fiel que pypdf em PDFs com espaçamento de letras
        out = subprocess.run(["pdftotext", str(p), "-"], capture_output=True, text=True, timeout=300).stdout
        paginas = out.split("\f")
    else:
        try:
            from pypdf import PdfReader
        except ImportError:
            raise SystemExit("ERRO para ler PDF instale pypdf (pip install pypdf) ou poppler-utils (pdftotext).")
        paginas = [pg.extract_text() or "" for pg in PdfReader(str(p)).pages]
    slides = []
    for pg in paginas:
        blocos, solta = [], True
        for ln in pg.splitlines():
            t = limpo(ln)
            if t.startswith("RASCUNHO · NÃO APROVADO"):
                continue
            if not t:
                solta = True  # linha em branco separa blocos
                continue
            ant = blocos[-1] if blocos and not solta else ""
            # continua a frase anterior: começa em minúscula ou parêntese, ou a anterior termina em palavra de ligação
            if ant and not re.search(r"[.!?:]$", ant) and (t[0].islower() or t[0] in "(,;" or LIGA.search(ant)):
                blocos[-1] += " " + t
            else:
                blocos.append(t)
            solta = False
        if not blocos:
            continue
        tit = blocos[0] if len(blocos[0].split()) <= 14 else None
        slides.append({"titulo": tit, "itens": [BULLET.sub("", b, count=1) for b in (blocos[1:] if tit else blocos)]})
    return slides


def ler(p: Path):
    if p.suffix.lower() == ".docx":
        return linhas_docx(p)
    return p.read_text(encoding="utf8").splitlines()


def extrair(linhas):
    slides = []
    atual = None
    for ln in linhas + ["&&&"]:
        s = ln.rstrip()
        if s.strip() == "&&&":
            if atual and (atual["titulo"] or atual["itens"]):
                slides.append(atual)
            atual = {"titulo": None, "itens": []}
            continue
        if atual is None:
            atual = {"titulo": None, "itens": []}
        if not s.strip():
            continue
        m = re.fullmatch(r"\s*\*\*(.+?)\*\*\s*", s)
        if m and atual["titulo"] is None and not atual["itens"]:
            atual["titulo"] = re.sub(r"\s+", " ", m.group(1)).strip()
            continue
        if s.lstrip().startswith("#") and atual["titulo"] is None and not atual["itens"]:
            atual["titulo"] = re.sub(r"\s+", " ", s.lstrip("# ")).strip()
            continue
        t = BULLET.sub("", s, count=1)
        t = re.sub(r"\*\*(.+?)\*\*", r"\1", t)
        atual["itens"].append(re.sub(r"\s+", " ", t).strip())
    return slides


SUGESTAO = [("dividido", "direita"), ("lista", "direita"), ("dividido", "esquerda"), ("faixa", None), ("dividido", "direita"), ("lista", "esquerda")]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("origem")
    ap.add_argument("projeto")
    ap.add_argument("--verbatim", action="store_true")
    ap.add_argument("--sugerir", action="store_true")
    a = ap.parse_args()
    src = Path(a.origem)
    proj = Path(a.projeto)
    proj.mkdir(parents=True, exist_ok=True)
    suf = src.suffix.lower()
    notas, avisos = [], []
    if suf == ".pptx":
        slides, notas, avisos = slides_pptx(src)
    elif suf == ".pdf":
        slides = slides_pdf(src)
        avisos.append("PDF lido como insumo: o texto vem sem marcação de slides e o deck fica em modo autoral. Redija cada slide com base nele.")
        if a.verbatim:
            avisos.append("--verbatim ignorado para PDF. Para verbatim, peça o texto em .md ou .docx separado por &&&.")
            a.verbatim = False
    else:
        slides = extrair(ler(src))
    if not slides:
        print("ERRO nenhum slide encontrado. Os slides precisam estar separados por uma linha com &&&.")
        return 1
    (proj / "texto_origem.json").write_text(json.dumps(slides, ensure_ascii=False, indent=1), encoding="utf8")
    for n, s in enumerate(slides, 1):
        if len(s["itens"]) > 4:
            avisos.append(f"slide {n}: {len(s['itens'])} bullets (o padrão é 3 a 4). Proponha dividir; a pessoa decide.")
        for b in s["itens"]:
            if len(b.split()) > 28:
                avisos.append(f"slide {n}: bullet com {len(b.split())} palavras. Vai pedir layout largo ou divisão.")
            if re.search(r"\b[A-ZÁ-Ú][a-zá-ú]+(?:et ?al)?,[A-ZÁ-Ú0-9]", b) or re.search(r"[a-z]{3,}etal\b", b, re.I):
                avisos.append(f"slide {n}: possível citação sem espaço ({re.search(r'[^ ]*,[^ ]*', b).group(0)}). Mostre à pessoa antes de construir.")
            if re.search(r"\*\*|&&&|#", b):
                avisos.append(f"slide {n}: marcação dentro do texto: {b[:50]}")
        if not s["titulo"] and n == 1:
            avisos.append("slide 1 sem título. A capa precisa de um título.")
        if not s["itens"] and not s["titulo"]:
            avisos.append(f"slide {n} vazio.")
    dj = proj / "deck.json"
    if not dj.exists():
        deck = {
            "titulo": slides[0]["titulo"] or "PREENCHER",
            "idioma": "pt-BR", "tema": "auto",
            "modo_texto": "verbatim" if a.verbatim else "autoral",
            "autor": "", "instituicao": "", "data": "",
            "contrato": {k: "PREENCHER" for k in ("tese", "mundo", "historia", "primeira_tela", "forma", "publico", "sala")},
            "secoes": [{"nome": slides[0]["titulo"] or "Abertura", "inicio": 1}],
            "imagens": {},
            "slides": [],
        }
        for n, s in enumerate(slides, 1):
            item = {"layout": "?", "titulo": s["titulo"], "itens": s["itens"], "notas": notas[n - 1] if n <= len(notas) else ""}
            if a.sugerir:
                if n == 1:
                    item["layout"] = "capa"
                else:
                    lay, lado = SUGESTAO[(n - 2) % len(SUGESTAO)]
                    item["layout"] = lay
                    if lado:
                        item["lado"] = lado
                item["rascunho_layout"] = True
            if item["titulo"] is None:
                item.pop("titulo")
            deck["slides"].append(item)
        dj.write_text(json.dumps(deck, ensure_ascii=False, indent=2), encoding="utf8")
        print(f"deck.json criado com {len(slides)} slides. Escolha layout, imagem e notas de cada slide.")
    else:
        print("deck.json já existe: só texto_origem.json foi atualizado.")
    print(f"{len(slides)} slides lidos de {src.name}.")
    for m in avisos:
        print("AVISO", m)
    return 0


if __name__ == "__main__":
    sys.exit(main())
