#!/usr/bin/env python3
"""Exporta o deck para PDF: uma página 1920x1080 por slide, no estado final das animações.

    python3 scripts/exportar_pdf.py PROJETO              # versão final: exige a trava liberada
    python3 scripts/exportar_pdf.py PROJETO --rascunho   # para revisão: cada página leva a tarja RASCUNHO

Confere que o PDF tem tantas páginas quanto slides.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import trava  # noqa: E402


def paginas(pdf: Path):
    try:
        out = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True, timeout=60).stdout
        m = re.search(r"Pages:\s+(\d+)", out)
        if m:
            return int(m.group(1))
    except Exception:  # noqa: BLE001
        pass
    return len(re.findall(rb"/Type\s*/Page[^s]", pdf.read_bytes()))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("projeto")
    ap.add_argument("--rascunho", action="store_true")
    a = ap.parse_args()
    proj = Path(a.projeto).resolve()
    if not a.rascunho:
        ok, motivos = trava.checar(proj)
        if not ok:
            print("TRAVADO. O PDF final só sai com uma aprovação registrada para esta versão (rode scripts/fazer.py):")
            for m in motivos:
                print(" -", m)
            print("Para revisão, use --rascunho (as páginas saem marcadas).")
            return 2
    from playwright.sync_api import sync_playwright

    build = json.loads((proj / "dist" / "build.json").read_text(encoding="utf8"))
    html = proj / "dist" / build["arquivo"]
    saida = html.with_name(html.stem + ("-RASCUNHO" if a.rascunho else "") + ".pdf")
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1920, "height": 1080})
        pg.goto(html.as_uri() + "?final")
        pg.wait_for_function("window.SK && window.SK.pronto === true", timeout=60000)
        pg.evaluate("window.SK.final(true)")
        if a.rascunho:
            pg.evaluate("document.documentElement.classList.add('sk-rascunho')")
        # WebP vira JPEG antes de imprimir: o Chromium embute JPEG sem recomprimir (PDF muito menor)
        pg.evaluate("""async () => {
          const imgs = Array.from(document.querySelectorAll('img'));
          for (const im of imgs) {
            if (!im.src.startsWith('data:image/webp')) continue;
            await im.decode().catch(() => {});
            const c = document.createElement('canvas'); c.width = im.naturalWidth; c.height = im.naturalHeight;
            c.getContext('2d').drawImage(im, 0, 0);
            im.src = c.toDataURL('image/jpeg', 0.86);
            await im.decode().catch(() => {});
          }
        }""")
        pg.emulate_media(media="print")
        pg.wait_for_timeout(300)
        pg.pdf(path=str(saida), width="1920px", height="1080px", print_background=True, prefer_css_page_size=True,
               margin={"top": "0", "right": "0", "bottom": "0", "left": "0"})
        total = pg.evaluate("window.SK.total")
        b.close()
    n = paginas(saida)
    if n != total:
        print(f"ERRO o PDF tem {n} páginas e o deck tem {total} slides. Não entregue este PDF; rode scripts/verificar.py.")
        return 1
    print(f"OK {saida} ({n} páginas, {saida.stat().st_size / 1e6:.1f} MB){' [RASCUNHO]' if a.rascunho else ''}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
