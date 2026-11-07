#!/usr/bin/env python3
"""Audita QUALQUER deck HTML (inclusive feito fora desta skill) pelo que aparece na tela.

Abre o arquivo em 1920x1080, avança com a seta para a direita até o fim (ou até --max
passos) e, a cada passo, mede o tamanho efetivo das fontes visíveis e a ocupação da
tela pela captura, e procura enfeites de gerador (degradê no texto, sombra dura, vidro fosco,
borda lateral, rótulo acima do título, quique, emoji, numeração 01/02) e avisos tipográficos.
Texto apagado no estado final aparece só como informação, porque decks de fora empilham slides ocultos.
Útil para avaliar decks de referência e decks escritos à mão.

    python3 scripts/auditar_html.py deck.html --out auditoria/ [--max 200] [--espera 900]

Saída: auditoria/passoNNN.png, auditoria/passoNNN_sobreposto.jpg, auditoria/relatorio.json
"""
import argparse
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import medir  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("html")
    ap.add_argument("--out", required=True)
    ap.add_argument("--max", type=int, default=200)
    ap.add_argument("--espera", type=int, default=900, help="ms entre passos")
    ap.add_argument("--movimento", action="store_true", help="não emular movimento reduzido")
    a = ap.parse_args()
    from playwright.sync_api import sync_playwright

    os.makedirs(a.out, exist_ok=True)
    passos = []
    with sync_playwright() as p:
        b = p.chromium.launch()
        ctx = b.new_context(viewport={"width": 1920, "height": 1080},
                            reduced_motion=None if a.movimento else "reduce")
        pg = ctx.new_page()
        pg.goto("file://" + os.path.abspath(a.html))
        pg.wait_for_timeout(1500)
        iguais = 0
        ultimo = None
        for i in range(a.max):
            pg.wait_for_timeout(a.espera)
            png = os.path.join(a.out, f"passo{i + 1:03d}.png")
            pg.screenshot(path=png)
            h = hashlib.md5(open(png, "rb").read()).hexdigest()
            if h == ultimo:
                iguais += 1
                os.remove(png)
                if iguais >= 2:
                    break
                pg.keyboard.press("ArrowRight")
                continue
            iguais = 0
            ultimo = h
            res = pg.evaluate(medir.JS_TEXTO, None)
            en = pg.evaluate(medir.JS_ENFEITES, None)
            esc = res["W"] / 1920.0
            ft = medir.classificar_textos(res["items"], escala=esc)
            oc = medir.ocupacao(png, None, res.get("visuais"))
            medir.sobrepor(png, png.replace(".png", "_sobreposto.jpg"), oc, ft["problemas_fonte"] + en["reprova"])
            oc.pop("grade_vazia", None)
            passos.append({"passo": i + 1, "png": os.path.basename(png), **{k: v for k, v in ft.items() if k != "problemas_fonte"},
                           "n_problemas_fonte": len(ft["problemas_fonte"]),
                           "exemplos_fonte_pequena": ft["problemas_fonte"][:4], **oc,
                           "enfeites": en["reprova"], "avisos": en["avisos"], "estado_final_info": en["final"]})
            pg.keyboard.press("ArrowRight")
        b.close()
    resumo = {
        "passos": len(passos),
        "passos_com_fonte_abaixo_do_piso": sum(1 for s in passos if not s["fontes_ok"]),
        "passos_com_tela_nao_ocupada": sum(1 for s in passos if not s["tela_ocupada"]),
        "menor_fonte_px": min((s["min_px"] for s in passos if s["min_px"]), default=None),
        "mediana_corpo_px": sorted([s["mediana_corpo_px"] for s in passos if s["mediana_corpo_px"]])[len([1 for s in passos if s["mediana_corpo_px"]]) // 2] if any(s["mediana_corpo_px"] for s in passos) else None,
        "passos_com_enfeite": [s["passo"] for s in passos if s["enfeites"]],
        "enfeites": sorted({e["tipo"] for s in passos for e in s["enfeites"]}),
        "avisos": sum(len(s["avisos"]) for s in passos),
        "fracao_vazia_media": round(sum(s["fracao_vazia"] for s in passos) / max(1, len(passos)), 3),
    }
    json.dump({"resumo": resumo, "passos": passos}, open(os.path.join(a.out, "relatorio.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps(resumo, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
