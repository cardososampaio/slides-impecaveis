#!/usr/bin/env python3
"""Converte o deck HTML em PowerPoint (.pptx) 16:9, com notas do apresentador.

    python3 scripts/exportar_pptx.py PROJETO                      # híbrido (padrão): fundo renderizado + texto editável
    python3 scripts/exportar_pptx.py PROJETO --modo imagem        # cada slide é uma imagem fiel (nada editável)
    python3 scripts/exportar_pptx.py PROJETO --fontes-seguras     # troca as fontes do tema por Arial, Georgia e Courier New
    python3 scripts/exportar_pptx.py PROJETO --rascunho           # para revisão, sem a trava (slides marcados)
    python3 scripts/exportar_pptx.py PROJETO --conferir           # confere o arquivo e compara com o HTML pelo LibreOffice
    python3 scripts/exportar_pptx.py PROJETO --dados-nativos      # gráficos (barras, barras-h, linha) e tabelas editáveis
    python3 scripts/exportar_pptx.py PROJETO --max-mb 25          # baixa a qualidade dos fundos até caber
    python3 scripts/exportar_pptx.py PROJETO --sem-transicao      # sem o esmaecimento de 0,5 s entre slides

Modo híbrido: cada slide é fotografado SEM o texto (imagens, campos de cor, gráficos, marcadores e
ornamentos ficam no fundo) e todo texto volta como caixa de texto nativa, na mesma posição, tamanho,
peso, cor e quebra de linha do HTML. O título vai no espaço reservado de título (bom para leitores de
tela e para o modo de estrutura do PowerPoint). Rótulos dentro de gráficos SVG ficam no fundo, salvo
com --dados-nativos, que refaz barras, barras-h, linha e tabelas como objetos do PowerPoint, com os
dados do deck.json e as cores do tema. Cada slide entra com esmaecimento de 0,5 s (--sem-transicao desliga).
O que se perde: animações (o PowerPoint recebe o estado final) e a fidelidade exata das quebras se a
máquina não tiver as fontes do tema. Rode scripts/instalar_fontes.py nessa máquina ou use --fontes-seguras.
"""
from __future__ import annotations

import argparse
import io
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import trava  # noqa: E402

EMU_PX = 6350  # 12.192.000 EMU / 1920 px
SEGURAS = {"Jost": "Arial", "Atkinson Hyperlegible Next": "Arial", "Oswald": "Arial Narrow", "Fraunces": "Georgia",
           "Source Serif 4": "Georgia", "Courier Prime": "Courier New"}

JS_TEXTOS = r"""
(raiz) => {
  const out = [];
  const els = Array.from(raiz.querySelectorAll('[data-txt]')).filter(e => !(e instanceof SVGElement));
  for (const el of els) {
    if (el.parentElement && el.parentElement.closest('[data-txt]')) continue; // só o mais externo
    const r = el.getBoundingClientRect();
    if (r.width < 2 || r.height < 2) continue;
    const cs = getComputedStyle(el);
    if (cs.visibility === 'hidden' || parseFloat(cs.opacity) < 0.05) continue;
    const runs = [];
    let ultimoTopo = null;
    const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
    let n;
    while ((n = walker.nextNode())) {
      const p = n.parentElement; const pcs = getComputedStyle(p);
      const txt = n.nodeValue; if (!txt) continue;
      const re = /\S+\s*/g; let m;
      while ((m = re.exec(txt))) {
        const rg = document.createRange(); rg.setStart(n, m.index); rg.setEnd(n, m.index + m[0].replace(/\s+$/, '').length || m.index + 1);
        const rr = rg.getClientRects()[0];
        let quebra = false;
        if (rr) { if (ultimoTopo !== null && rr.top > ultimoTopo + parseFloat(pcs.fontSize) * 0.5) quebra = true; ultimoTopo = rr.top; }
        runs.push({ t: m[0], q: quebra, w: parseInt(pcs.fontWeight) || 400, i: pcs.fontStyle === 'italic', c: pcs.color,
                    u: pcs.textTransform === 'uppercase', fs: parseFloat(pcs.fontSize), ff: pcs.fontFamily });
      }
    }
    if (!runs.length) continue;
    const rgT = document.createRange(); rgT.selectNodeContents(el); const tr = rgT.getBoundingClientRect();
    out.push({ x: r.left, y: r.top, w: r.width, h: r.height, tx: tr.left, tw: tr.width, fs: parseFloat(cs.fontSize), lh: parseFloat(cs.lineHeight) || parseFloat(cs.fontSize) * 1.2,
               ff: cs.fontFamily, al: cs.textAlign, tag: el.tagName.toLowerCase(), role: el.getAttribute('data-role') || '', runs: runs,
               pl: parseFloat(cs.paddingLeft) || 0, pt: parseFloat(cs.paddingTop) || 0, pr: parseFloat(cs.paddingRight) || 0, ti: parseFloat(cs.textIndent) || 0 });
  }
  return out;
}
"""


def cor(rgb):
    import re
    from pptx.dml.color import RGBColor
    m = re.match(r"rgba?\(([\d.]+),\s*([\d.]+),\s*([\d.]+)", rgb or "")
    if not m:
        return RGBColor(0, 0, 0)
    return RGBColor(*(int(float(m.group(i))) for i in (1, 2, 3)))


_FAM = json.loads((Path(__file__).resolve().parent.parent / "templates" / "temas.json").read_text(encoding="utf8"))["familias"]
SEGURAS.update({f: m["segura"] for f, m in _FAM.items()})  # troca de --fontes-seguras, lida de templates/temas.json
SEMINEGRITO = {f for f, m in _FAM.items() if any(a.endswith("-600.ttf") for a in m["ttf"])}  # famílias com arquivo SemiBold


def familia(ff, seguras):
    f = (ff or "Arial").split(",")[0].strip().strip("'\"")
    return SEGURAS.get(f, "Arial") if seguras else f


def face(ff, peso, seguras):
    """Nome da fonte e negrito do jeito que o PowerPoint entende (nome de família legado por peso)."""
    f = familia(ff, seguras)
    if seguras:
        return f, peso >= 600
    if 550 <= peso < 650 and f in SEMINEGRITO:
        return f + " SemiBold", False
    return f, peso >= 600


NATIVOS = {"barras", "barras-h", "linha"}

JS_NATIVO = r"""
([k, sel]) => {
  const raiz = document.querySelector(`.sk-slide[data-i="${k}"]`);
  const el = raiz && raiz.querySelector(sel);
  if (!el) return null;
  const r = el.getBoundingClientRect();
  const sonda = (v) => { const e = document.createElement('span'); e.style.color = `var(${v})`; el.parentElement.appendChild(e);
    const c = getComputedStyle(e).color; e.remove(); return c; };
  const cs = (q) => { const x = el.querySelector(q) || el; const c = getComputedStyle(x);
    return { fs: parseFloat(c.fontSize), ff: c.fontFamily, w: parseInt(c.fontWeight) || 400, u: c.textTransform === 'uppercase',
             pl: parseFloat(c.paddingLeft) || 0, pt: parseFloat(c.paddingTop) || 0 }; };
  const out = { x: r.left, y: r.top, w: r.width, h: r.height,
    cores: { acento: sonda('--acento'), acento2: sonda('--acento2'), tinta: sonda('--tinta'), papel: sonda('--papel'),
             sobre: sonda('--sobre-acento'), linha: sonda('--linha') },
    th: cs('th'), td: cs('td:not(:first-child)'), td1: cs('td'), corpo: getComputedStyle(el.parentElement).fontFamily,
    cols: Array.from(el.querySelectorAll('thead th')).map((t) => t.getBoundingClientRect().width) };
  el.classList.add('sk-pptx-nativo');  // some do fundo e das caixas de texto (visibility herda)
  return out;
}
"""


def nativo_de(s):
    """Seletor do elemento que vira objeto nativo, ou None se o slide não tem gráfico ou tabela suportados."""
    if s.get("layout") == "grafico" and (s.get("grafico") or {}).get("tipo", "barras") in NATIVOS and (s["grafico"].get("valores") or s["grafico"].get("series")):
        return ".sk-cartao-graf svg"
    if s.get("layout") == "tabela" and (s.get("tabela") or {}).get("cabecalho"):
        return "table.sk-tab"
    return None


def sem_md(t):
    return re.sub(r"<[^>]+>|\*\*|__|\*", "", str(t))


def grafico_nativo(sl, g, n, seguras):
    from pptx.chart.data import CategoryChartData
    from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION, XL_LABEL_POSITION
    from pptx.util import Pt
    tipo = g.get("tipo", "barras")
    c = {k: cor(v) for k, v in n["cores"].items()}
    dados = CategoryChartData()
    dados.categories = [sem_md(r) for r in g["rotulos"]]
    series = g.get("series") or [{"nome": g.get("nome", ""), "valores": g["valores"]}]
    for sr in series:
        dados.add_series(sr.get("nome") or "Valores", sr["valores"])
    xl = {"barras": XL_CHART_TYPE.COLUMN_CLUSTERED, "barras-h": XL_CHART_TYPE.BAR_CLUSTERED, "linha": XL_CHART_TYPE.LINE_MARKERS}[tipo]
    gf = sl.shapes.add_chart(xl, int(n["x"] * EMU_PX), int(n["y"] * EMU_PX), int(n["w"] * EMU_PX), int(n["h"] * EMU_PX), dados)
    gf.name = "Gráfico " + tipo
    ch = gf.chart
    ch.has_title = False
    ch.font.size = Pt(16)
    ch.font.name = familia(n["corpo"], seguras)
    ch.font.color.rgb = c["tinta"]
    ch.has_legend = len(series) > 1
    if ch.has_legend:
        ch.legend.position, ch.legend.include_in_layout = XL_LEGEND_POSITION.BOTTOM, False
        ch.legend.font.size = Pt(16)
    pre, _, suf = (g.get("formato") or "{v}" + (g.get("unidade") or "")).partition("{v}")
    fmt = (f'"{pre}"' if pre else "") + "General" + (f'"{suf}"' if suf else "")
    fmt = fmt.replace('""', "")
    va, ca = ch.value_axis, ch.category_axis
    ca.tick_labels.font.size = Pt(16)
    ca.format.line.color.rgb = c["tinta"]
    ca.has_major_gridlines = False
    from pptx.enum.chart import XL_TICK_MARK
    ca.major_tick_mark = ca.minor_tick_mark = XL_TICK_MARK.NONE
    if g.get("max"):
        va.maximum_scale = g["max"]
    if tipo == "linha":
        if g.get("min") is not None:
            va.minimum_scale = g["min"]
        va.tick_labels.font.size = Pt(14)
        va.tick_labels.number_format, va.tick_labels.number_format_is_linked = fmt, False
        va.major_gridlines.format.line.color.rgb = c["linha"]
        va.format.line.fill.background()
        for k, sr in enumerate(ch.plots[0].series):
            tom = c["acento"] if k == 0 else c["acento2"]
            sr.format.line.color.rgb, sr.format.line.width, sr.smooth = tom, Pt(4), False
            from pptx.enum.chart import XL_MARKER_STYLE
            sr.marker.style, sr.marker.size = XL_MARKER_STYLE.CIRCLE, 9
            sr.marker.format.fill.solid()
            sr.marker.format.fill.fore_color.rgb = tom
            sr.marker.format.line.color.rgb = tom
            ponto = sr.points[len(series[k]["valores"]) - 1].data_label  # valor só no último ponto, como no HTML
            ponto.has_text_frame = False
            ponto.position = XL_LABEL_POSITION.RIGHT
            ponto.font.size, ponto.font.bold, ponto.font.color.rgb = Pt(18), True, tom
            from lxml import etree
            from pptx.oxml.ns import qn
            nf = etree.Element(qn("c:numFmt"), formatCode=fmt, sourceLinked="0")
            ponto._dLbl.find(qn("c:spPr")).addprevious(nf)  # mesmo formato do HTML (prefixo e unidade)
        return gf
    va.visible = False
    va.has_major_gridlines = False
    if tipo == "barras-h":
        ca.reverse_order = True  # primeira categoria no topo, como no HTML
    pl = ch.plots[0]
    pl.gap_width = 55
    pl.has_data_labels = True
    dl = pl.data_labels
    dl.number_format, dl.number_format_is_linked = fmt, False
    dl.position = XL_LABEL_POSITION.OUTSIDE_END
    dl.font.size, dl.font.bold, dl.font.color.rgb = Pt(18), True, c["tinta"]
    dest = set(g.get("destaque") or [])
    for i in range(len(g["rotulos"])):
        pt = pl.series[0].points[i]
        pt.format.fill.solid()
        pt.format.fill.fore_color.rgb = c["acento"] if i in dest else c["acento2"]
    return gf


def tabela_nativa(sl, t, n, seguras):
    from pptx.util import Emu, Pt
    c = {k: cor(v) for k, v in n["cores"].items()}
    cab, linhas = t["cabecalho"], t["linhas"]
    nl, nc = len(linhas) + 1, len(cab)
    gf = sl.shapes.add_table(nl, nc, int(n["x"] * EMU_PX), int(n["y"] * EMU_PX), int(n["w"] * EMU_PX), int(n["h"] * EMU_PX))
    gf.name = "Tabela"
    tb = gf.table
    tb.horz_banding = False
    tb.first_row = True
    for j, w in enumerate(n["cols"][:nc]):
        tb.columns[j].width = int(w * EMU_PX)
    for i in range(nl):
        tb.rows[i].height = int(n["h"] / nl * EMU_PX)
    for i, lin in enumerate([cab] + linhas):
        for j in range(nc):
            cel = tb.cell(i, j)
            st = n["th"] if i == 0 else n["td"]
            txt = sem_md(lin[j] if j < len(lin) else "")
            cel.margin_left = cel.margin_right = Emu(int(st["pl"] * EMU_PX))
            cel.margin_top = cel.margin_bottom = Emu(int(st["pt"] * EMU_PX * 0.6))
            if i == 0 and not txt:
                cel.fill.background()
            else:
                cel.fill.solid()
                cel.fill.fore_color.rgb = c["acento"] if i == 0 else c["papel"]
            cel.text = txt.upper() if (i == 0 and st["u"]) else txt
            for par in cel.text_frame.paragraphs:
                for r in par.runs:
                    st2 = n["td1"] if (j == 0 and i > 0) else st  # primeira coluna com peso e família próprios
                    nome, negrito = face(st2["ff"], st2["w"], seguras)
                    r.font.name, r.font.bold = nome, negrito
                    r.font.size = Pt(max(14, round(st["fs"] * 0.5)))
                    r.font.color.rgb = c["sobre"] if i == 0 else c["tinta"]
    return gf


def transicao(sl):
    """Esmaecimento nativo de 0,5 s (spd="fast") ao entrar no slide."""
    from lxml import etree
    from pptx.oxml.ns import qn
    raiz = sl._element
    for velho in raiz.findall(qn("p:transition")):
        raiz.remove(velho)
    tr = etree.SubElement(raiz, qn("p:transition"), spd="fast")
    etree.SubElement(tr, qn("p:fade"))
    ref = raiz.find(qn("p:clrMapOvr"))
    if ref is None:
        ref = raiz.find(qn("p:cSld"))
    ref.addnext(tr)  # ordem do esquema: cSld, clrMapOvr, transition, timing


def checar_arquivo(pptx: Path, deck: dict):
    """Confere o arquivo entregue e devolve linhas de resumo."""
    import zipfile
    out = []
    try:
        with zipfile.ZipFile(pptx) as z:
            ruim = z.testzip()
            nomes = z.namelist()
            xml = {n: z.read(n).decode("utf8", "ignore") for n in nomes if n.endswith(".xml") and ("slides/" in n or "charts/" in n or "notesSlides/" in n)}
    except zipfile.BadZipFile:
        return ["[FALHA] o arquivo não é um zip válido"]
    out.append(("[ok] zip íntegro" if ruim is None else f"[FALHA] zip com membro corrompido: {ruim}"))
    slides = [n for n in nomes if re.fullmatch(r"ppt/slides/slide\d+\.xml", n)]
    esp = len(deck.get("slides", []))
    out.append(f"[{'ok' if len(slides) == esp else 'FALHA'}] {len(slides)} slides no PPTX, {esp} no deck")
    com_notas = sum(1 for n, x in xml.items() if "notesSlides/" in n and re.search(r"<a:t>[^<]{3,}", x))
    pedem = sum(1 for s in deck.get("slides", []) if s.get("notas") or s.get("fonte"))
    out.append(f"[{'ok' if com_notas >= pedem else 'FALHA'}] notas em {com_notas} slides ({pedem} têm notas ou fontes no deck)")
    pequenos = sorted({int(m) for n, x in xml.items() if "notesSlides/" not in n for m in re.findall(r"<a:(?:rPr|defRPr)[^>]*\ssz=\"(\d+)\"", x) if int(m) < 1400})
    out.append("[ok] nenhum texto abaixo de 14 pt" if not pequenos else f"[FALHA] texto abaixo de 14 pt: {', '.join(str(p / 100) + ' pt' for p in pequenos)}")
    usadas = sorted({f for n, x in xml.items() if "notesSlides/" not in n for f in re.findall(r'<a:latin typeface="([^"+][^"]*)"', x)})
    if shutil.which("fc-list"):
        inst = set()
        for ln in subprocess.run(["fc-list", ":", "family"], capture_output=True, text=True).stdout.splitlines():
            inst.update(x.strip().lower() for x in ln.split(","))
        falta = [f for f in usadas if f.lower() not in inst]
        out.append(f"[{'ok' if not falta else 'AVISO'}] fontes usadas: {', '.join(usadas) or 'nenhuma explícita'}" + (f". Não instaladas aqui: {', '.join(falta)} (rode instalar_fontes.py na máquina que vai abrir)" if falta else ". Todas instaladas aqui"))
    else:
        out.append(f"[--] fontes usadas: {', '.join(usadas)} (sem fc-list para comparar com as instaladas)")
    graf = sum(1 for n in nomes if re.fullmatch(r"ppt/charts/chart\d+\.xml", n))
    tabs = sum(x.count("<a:tbl>") for n, x in xml.items() if "slides/" in n and "notesSlides/" not in n)
    trans = sum(1 for n, x in xml.items() if re.fullmatch(r"ppt/slides/slide\d+\.xml", n) and "<p:transition" in x)
    out.append(f"[--] {graf} gráfico(s) e {tabs} tabela(s) nativos, transição em {trans} slides")
    out.append(f"[--] tamanho {pptx.stat().st_size / 1e6:.1f} MB")
    return out


def soffice_pdf(pptx: Path, destino: Path):
    exe = shutil.which("soffice") or shutil.which("libreoffice")
    if not exe:
        return None
    with tempfile.TemporaryDirectory() as perfil:
        try:
            subprocess.run([exe, f"-env:UserInstallation=file://{perfil}", "--headless", "--norestore", "--nolockcheck",
                            "--convert-to", "pdf", "--outdir", str(destino), str(pptx)], capture_output=True, timeout=300)
        except subprocess.TimeoutExpired:
            return None
    pdf = destino / (pptx.stem + ".pdf")
    return pdf if pdf.exists() else None


def coletar(html: Path, deck: dict, a):
    """Fotografa cada slide (PNG, sem perdas) e lê textos e objetos nativos."""
    from playwright.sync_api import sync_playwright
    dados = []
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1920, "height": 1080}, device_scale_factor=a.escala)
        pg.goto(html.as_uri() + "?final")
        pg.wait_for_function("window.SK && window.SK.pronto === true", timeout=60000)
        pg.evaluate("window.SK.final(true)")
        pg.add_style_tag(content=".sk-pptx-nativo{visibility:hidden!important}")
        if a.rascunho:
            pg.evaluate("document.documentElement.classList.add('sk-rascunho')")
        total = pg.evaluate("window.SK.total")
        for k in range(total):
            pg.evaluate(f"window.SK.ir({k})")
            pg.wait_for_timeout(120)
            s_info = deck["slides"][k]
            sel = nativo_de(s_info) if a.dados_nativos else None
            nat = pg.evaluate(JS_NATIVO, [k, sel]) if sel else None
            raiz = pg.query_selector(f'.sk-slide[data-i="{k}"]')
            textos = [] if a.modo == "imagem" else pg.evaluate(JS_TEXTOS, raiz)
            if a.modo == "hibrido":
                pg.evaluate("document.documentElement.classList.add('sk-pptx-fundo')")
                pg.wait_for_timeout(60)
            png = pg.screenshot(type="png")
            pg.evaluate("document.documentElement.classList.remove('sk-pptx-fundo')")
            dados.append({"textos": textos, "png": png, "s": s_info, "nativo": nat})
        b.close()
    return dados


def montar(dados, deck, a, qualidade=90, reduzir=1.0):
    from PIL import Image
    from pptx import Presentation
    from pptx.enum.text import MSO_ANCHOR, MSO_AUTO_SIZE, PP_ALIGN
    from pptx.util import Emu, Pt

    prs = Presentation()
    prs.slide_width, prs.slide_height = Emu(12192000), Emu(6858000)
    lay_titulo = prs.slide_layouts[5]
    lay_branco = prs.slide_layouts[6]
    prs.core_properties.title = deck.get("titulo", "")
    prs.core_properties.author = deck.get("autor", "")
    for k, d in enumerate(dados):
        textos, s_info, nat = d["textos"], d["s"], d["nativo"]
        im = Image.open(io.BytesIO(d["png"])).convert("RGB")
        if reduzir < 1:
            im = im.resize((int(im.width * reduzir), int(im.height * reduzir)), Image.LANCZOS)
        jpg = io.BytesIO()
        im.save(jpg, "JPEG", quality=qualidade, optimize=True)
        titulo_txt = next((t for t in textos if t["role"] == "titulo"), None)
        sl = prs.slides.add_slide(lay_titulo if titulo_txt else lay_branco)
        pic = sl.shapes.add_picture(jpg, 0, 0, prs.slide_width, prs.slide_height)
        pic.name = "Fundo do slide"
        pic._element.nvPicPr.cNvPr.set("descr", "Fundo do slide " + str(k + 1) + ": imagens, campos de cor e gráficos" + (" (" + s_info.get("titulo", "") + ")" if s_info.get("titulo") else ""))
        sp = sl.shapes._spTree
        sp.remove(pic._element)
        sp.insert(2, pic._element)  # fundo atrás de tudo
        if nat:
            if s_info.get("layout") == "grafico":
                grafico_nativo(sl, s_info["grafico"], nat, a.fontes_seguras)
            else:
                tabela_nativa(sl, s_info["tabela"], nat, a.fontes_seguras)
        for t in textos:
            # posição horizontal pela extensão real do texto (ignora marcadores e colunas de grade)
            x = t["tx"] * EMU_PX
            y = (t["y"] + t["pt"]) * EMU_PX
            w = max(t["tw"], 20) * 1.07 * EMU_PX
            h = (t["h"] - t["pt"]) * EMU_PX
            if t is titulo_txt and sl.shapes.title is not None:
                caixa = sl.shapes.title
                caixa.left, caixa.top, caixa.width, caixa.height = int(x), int(y), int(w), int(h)
            else:
                caixa = sl.shapes.add_textbox(int(x), int(y), int(w), int(h))
            tf = caixa.text_frame
            tf.clear()
            tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
            tf.vertical_anchor = MSO_ANCHOR.TOP
            tf.word_wrap = True  # as quebras do HTML já vêm explícitas; a caixa é um pouco mais larga
            tf.auto_size = MSO_AUTO_SIZE.NONE
            par = tf.paragraphs[0]
            par.alignment = {"center": PP_ALIGN.CENTER, "right": PP_ALIGN.RIGHT, "end": PP_ALIGN.RIGHT, "justify": PP_ALIGN.JUSTIFY}.get(t["al"], PP_ALIGN.LEFT)
            par.line_spacing = Pt(t["lh"] * 0.5)
            primeiro = True
            for r in t["runs"]:
                texto = r["t"].upper() if r["u"] else r["t"]
                if r["q"] and not primeiro:
                    # remove o espaço que ficou no fim da linha anterior e quebra a linha
                    if par.runs and par.runs[-1].text.endswith(" "):
                        par.runs[-1].text = par.runs[-1].text.rstrip(" ")
                    par.add_line_break()
                run = par.add_run()
                run.text = texto
                f = run.font
                f.size = Pt(r["fs"] * 0.5)
                nome, negrito = face(r["ff"], r["w"], a.fontes_seguras)
                f.bold = negrito
                f.italic = r["i"]
                f.name = nome
                f.color.rgb = cor(r["c"])
                primeiro = False
        if not a.sem_transicao:
            transicao(sl)
        notas = s_info.get("notas") or ""
        if s_info.get("fonte"):
            notas += ("\n\n[Fontes] " + s_info["fonte"])
        nomes = [s_info.get("imagem")] + list(s_info.get("imagens") or []) + [c.get("imagem") for c in (s_info.get("colunas") or []) + (s_info.get("cartoes") or [])]
        nomes += re.findall(r"\{\{img:([\w-]+)\}\}", s_info.get("html") or "")
        creds = []
        for nm in [x for x in nomes if x]:
            c = re.sub("<[^>]+>", "", ((deck.get("imagens") or {}).get(nm) or {}).get("credito", ""))
            if c and c not in creds:
                creds.append(c)
        if creds:
            notas += "\n\n[Imagens] " + " | ".join(creds)
        if notas:
            sl.notes_slide.notes_text_frame.text = notas
    return prs


DEGRAUS = [(90, 1.0), (80, 1.0), (70, 1.0), (60, 1.0), (50, 1.0), (60, 0.67), (45, 0.67), (35, 0.67)]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("projeto")
    ap.add_argument("--modo", choices=["hibrido", "imagem"], default="hibrido")
    ap.add_argument("--fontes-seguras", action="store_true")
    ap.add_argument("--rascunho", action="store_true")
    ap.add_argument("--conferir", action="store_true")
    ap.add_argument("--dados-nativos", action="store_true", help="gráficos (barras, barras-h, linha) e tabelas como objetos editáveis")
    ap.add_argument("--sem-transicao", action="store_true", help="sem o esmaecimento de 0,5 s entre slides")
    ap.add_argument("--max-mb", type=float, help="reduz a qualidade dos fundos em degraus até o arquivo caber")
    ap.add_argument("--escala", type=float, default=1.5, help="nitidez do fundo (1.5 = 2880x1620)")
    a = ap.parse_args()
    proj = Path(a.projeto).resolve()
    if not a.rascunho:
        ok, motivos = trava.checar(proj)
        if not ok:
            print("TRAVADO. O PPTX final só sai com uma aprovação registrada para esta versão (rode scripts/fazer.py):")
            for m in motivos:
                print(" -", m)
            print("Para revisão, use --rascunho.")
            return 2

    build = json.loads((proj / "dist" / "build.json").read_text(encoding="utf8"))
    deck = json.loads((proj / "deck.json").read_text(encoding="utf8"))
    html = proj / "dist" / build["arquivo"]
    saida = html.with_name(html.stem + ("-RASCUNHO" if a.rascunho else "") + ".pptx")

    dados = coletar(html, deck, a)
    degraus = DEGRAUS if a.max_mb else DEGRAUS[:1]
    for q, red in degraus:
        montar(dados, deck, a, q, red).save(saida)
        mb = saida.stat().st_size / 1e6
        if not a.max_mb or mb <= a.max_mb:
            break
        print(f"   {mb:.1f} MB com JPEG q{q} e escala {red:g}: acima de {a.max_mb:g} MB, reduzindo")
    total = len(dados)
    nat = sum(1 for d in dados if d["nativo"])
    print(f"OK {saida} ({total} slides, modo {a.modo}, {mb:.1f} MB, fundos JPEG q{q}{'' if red == 1 else f' escala {red:g}'}"
          f"{f', {nat} gráfico(s) ou tabela(s) nativos' if a.dados_nativos else ''}){' [RASCUNHO]' if a.rascunho else ''}")
    if a.max_mb and mb > a.max_mb:
        print(f"AVISO não coube em {a.max_mb:g} MB nem no último degrau. Use imagens menores no deck (imagens.py tratar --max 1600).")
    if a.dados_nativos:
        sem = [str(k + 1) for k, d in enumerate(dados) if d["s"].get("layout") in ("grafico", "tabela") and not d["nativo"]]
        if sem:
            print(f"   slides {', '.join(sem)}: tipo de gráfico sem versão nativa, ficou no fundo renderizado.")
    if a.modo == "hibrido" and not a.fontes_seguras:
        print("   As fontes do tema precisam estar instaladas no computador que vai abrir o PPTX. Rode scripts/instalar_fontes.py nele (licença OFL).")

    if a.conferir:
        print("Conferência do arquivo")
        for ln in checar_arquivo(saida, deck):
            print("  ", ln)
        conf = proj / "verificacao" / "pptx"
        conf.mkdir(parents=True, exist_ok=True)
        pdf = soffice_pdf(saida, conf)
        if not pdf:
            print("AVISO LibreOffice indisponível: não foi possível conferir o PPTX renderizado.")
            return 0
        for velho in conf.glob("pp-*.png"):
            velho.unlink()
        subprocess.run(["pdftoppm", "-r", "48", "-png", str(pdf), str(conf / "pp")], timeout=300)
        from PIL import Image, ImageDraw
        pps = sorted(conf.glob("pp-*.png"))
        linhas = []
        for j, pp in enumerate(pps):
            orig = proj / "verificacao" / "slides" / f"s{j + 1:03d}.png"
            if not orig.exists():
                continue
            A = Image.open(orig).convert("RGB").resize((640, 360))
            B = Image.open(pp).convert("RGB").resize((640, 360))
            L = Image.new("RGB", (1300, 380), (20, 20, 20))
            L.paste(A, (6, 10))
            L.paste(B, (654, 10))
            ImageDraw.Draw(L).text((10, 2), f"{j + 1}  HTML | PPTX (LibreOffice)", fill=(240, 240, 240))
            linhas.append(L)
        if linhas:
            S = Image.new("RGB", (1300, 380 * len(linhas)), (20, 20, 20))
            for j, L in enumerate(linhas):
                S.paste(L, (0, j * 380))
            S.save(conf / "html_x_pptx.jpg", quality=82)
            print(f"   comparação lado a lado: {conf / 'html_x_pptx.jpg'} (o LibreOffice substitui fontes ausentes; o PowerPoint com as fontes instaladas fica mais fiel)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
