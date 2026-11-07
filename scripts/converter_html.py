#!/usr/bin/env python3
"""Converte QUALQUER deck HTML (feito fora desta skill) em PDF e PPTX, pelo que aparece na tela.

    python3 scripts/converter_html.py deck.html --saida convertido/ [--pdf] [--pptx] [--max 300] [--espera 900]
                                       [--movimento] [--medir]

Abre o arquivo em 1920x1080, avança com a seta para a direita até a tela parar de mudar e
fotografa cada passo. Passos idênticos em sequência são descartados. Sem --pdf nem --pptx, gera os dois.

Saída: convertido/<nome>.pdf (uma página por passo), convertido/<nome>.pptx (uma imagem por slide,
16:9, com o texto visível copiado para as notas), convertido/passos/*.png e, com --medir,
convertido/relatorio.json com fontes e ocupação de cada passo (mesma régua de verificar.py).

Limite honesto: num deck de fora, o texto vira imagem. Para PPTX com texto editável, fontes medidas
e trava do avaliador, refaça o deck nesta skill (deck.json) e use exportar_pptx.py.
Esta conversão não passa pela trava porque o deck não foi construído aqui. Avise isso à pessoa.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

JS_TEXTO_VISIVEL = r"""
() => {
  const out = []; const W = innerWidth, H = innerHeight;
  const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT); let n;
  while ((n = w.nextNode())) {
    const t = (n.nodeValue || '').replace(/\s+/g, ' ').trim(); if (!t) continue;
    const el = n.parentElement; if (!el || el.closest('script,style,noscript,template,aside.notes,.notes')) continue;
    const cs = getComputedStyle(el); if (cs.visibility === 'hidden' || +cs.opacity === 0) continue;
    const r = document.createRange(); r.selectNodeContents(n);
    const b = Array.from(r.getClientRects()).find((q) => q.width > 1 && q.right > 0 && q.bottom > 0 && q.left < W && q.top < H);
    if (b) out.push(t);
  }
  return out.join('\n');
}
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("html")
    ap.add_argument("--saida", required=True)
    ap.add_argument("--pdf", action="store_true")
    ap.add_argument("--pptx", action="store_true")
    ap.add_argument("--max", type=int, default=300)
    ap.add_argument("--espera", type=int, default=900, help="ms entre passos (aumente se as animações forem longas)")
    ap.add_argument("--movimento", action="store_true", help="não emular movimento reduzido")
    ap.add_argument("--medir", action="store_true", help="mede fontes e ocupação de cada passo")
    a = ap.parse_args()
    if not (a.pdf or a.pptx):
        a.pdf = a.pptx = True
    from playwright.sync_api import sync_playwright

    src = Path(a.html).resolve()
    out = Path(a.saida)
    pasta = out / "passos"
    pasta.mkdir(parents=True, exist_ok=True)
    for f in pasta.glob("*.png"):
        f.unlink()
    nome = src.stem
    capturas, textos, medidas = [], [], []
    if a.medir:
        import medir
    with sync_playwright() as p:
        b = p.chromium.launch()
        ctx = b.new_context(viewport={"width": 1920, "height": 1080}, reduced_motion=None if a.movimento else "reduce")
        pg = ctx.new_page()
        pg.goto(src.as_uri())
        pg.wait_for_timeout(1500)
        ultimo, iguais = None, 0
        for i in range(a.max):
            pg.wait_for_timeout(a.espera)
            dado = pg.screenshot(type="png")
            h = hashlib.md5(dado).hexdigest()
            if h == ultimo:
                iguais += 1
                if iguais >= 2:
                    break
                pg.keyboard.press("ArrowRight")
                continue
            iguais, ultimo = 0, h
            png = pasta / f"p{len(capturas) + 1:03d}.png"
            png.write_bytes(dado)
            capturas.append(png)
            textos.append(pg.evaluate(JS_TEXTO_VISIVEL))
            if a.medir:
                res = pg.evaluate(medir.JS_TEXTO, None)
                ft = medir.classificar_textos(res["items"], escala=res["W"] / 1920.0)
                oc = medir.ocupacao(str(png), None, res.get("visuais"))
                oc.pop("grade_vazia", None)
                medidas.append({"passo": len(capturas), "fontes_ok": ft["fontes_ok"], "min_px": ft["min_px"],
                                "mediana_corpo_px": ft["mediana_corpo_px"], **oc})
            pg.keyboard.press("ArrowRight")
        b.close()
    if not capturas:
        raise SystemExit("ERRO nenhuma tela capturada.")
    print(f"{len(capturas)} passos capturados de {src.name}")

    from PIL import Image
    if a.pdf:
        ims = [Image.open(c).convert("RGB") for c in capturas]
        pdf = out / f"{nome}.pdf"
        ims[0].save(pdf, save_all=True, append_images=ims[1:], resolution=144, quality=88)
        print(f"PDF {pdf} ({len(ims)} páginas, {pdf.stat().st_size / 1e6:.1f} MB)")
    if a.pptx:
        from pptx import Presentation
        from pptx.util import Emu
        prs = Presentation()
        prs.slide_width, prs.slide_height = Emu(12192000), Emu(6858000)
        branco = prs.slide_layouts[6]
        for c, t in zip(capturas, textos):
            jpg = c.with_suffix(".jpg")
            Image.open(c).convert("RGB").save(jpg, quality=88)
            sl = prs.slides.add_slide(branco)
            pic = sl.shapes.add_picture(str(jpg), 0, 0, prs.slide_width, prs.slide_height)
            pic._element.nvPicPr.cNvPr.set("descr", (t or "")[:1500])
            sl.notes_slide.notes_text_frame.text = "Texto visível neste slide (o slide é uma imagem):\n" + (t or "")
        px = out / f"{nome}.pptx"
        prs.save(px)
        for c in capturas:
            c.with_suffix(".jpg").unlink(missing_ok=True)
        print(f"PPTX {px} ({len(capturas)} slides, texto como imagem, texto copiado para as notas)")
    if a.medir:
        ruins_f = [m["passo"] for m in medidas if not m["fontes_ok"]]
        ruins_o = [m["passo"] for m in medidas if not m["tela_ocupada"]]
        (out / "relatorio.json").write_text(json.dumps({"passos": medidas}, ensure_ascii=False, indent=1), encoding="utf8")
        print(f"fonte abaixo do piso em {len(ruins_f)} de {len(medidas)} passos. Tela não ocupada em {len(ruins_o)}.")
    print("AVISO conversão de deck externo. O texto não é editável e a trava do avaliador não se aplica.")


if __name__ == "__main__":
    main()
