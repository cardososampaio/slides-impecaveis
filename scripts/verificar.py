#!/usr/bin/env python3
"""Verificação objetiva de TODOS os slides, no render real (Chromium, 1920x1080, estado final).

    python3 scripts/verificar.py PROJETO

Mede em cada slide:
  fontes    tamanho efetivo de todo texto visível (piso 28 px qualquer texto, 44 px corpo, 64 px título)
  ocupação  área morta na captura (vazio total, maior retângulo vazio, extensão do conteúdo)
  encaixe   texto que não coube nem no piso (o motor marca o slide) ou texto em cima de texto
  contraste razão entre a cor do texto e o fundo real atrás dele (mínimo 4,5)
  imagem    se há imagem real, gráfico ou diagrama
  variação  layouts repetidos e slides vizinhos quase idênticos
  rede      o deck abre e carrega as fontes com a internet bloqueada
  console   erros de JavaScript
  enfeites  degradê no texto, sombra dura, vidro fosco, borda lateral, rótulo acima do título,
            quique, emoji ou símbolo como ícone, numeração 01/02 (REPROVA)
  final     texto ou imagem que não terminou de aparecer no estado final (REPROVA)
  avisos    linha longa, entrelinha, caixa alta, palavra sozinha, respiro, ritmo, movimento
            repetido, tempo (AVISO, não trava)

Saídas em PROJETO/verificacao/: relatorio.json, relatorio.md, slides/sNNN.png, slides/sNNN_marcas.jpg, folhas/folha_NN.jpg
Código de saída 1 se qualquer condição automática falhar. A aprovação vem depois (scripts/fazer.py).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import medir  # noqa: E402


def dhash(png, n=16):
    from PIL import Image
    im = Image.open(png).convert("L").resize((n + 1, n))
    px = list(im.getdata())
    bits = 0
    for r in range(n):
        for c in range(n):
            bits = (bits << 1) | (px[r * (n + 1) + c] > px[r * (n + 1) + c + 1])
    return bits


def ham(a, b):
    return bin(a ^ b).count("1")


def contraste_hex(c1, c2):
    def lum(rgb):
        out = []
        for v in rgb:
            v = v / 255
            out.append(v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4)
        return 0.2126 * out[0] + 0.7152 * out[1] + 0.0722 * out[2]
    a, b = lum(c1), lum(c2)
    return (max(a, b) + 0.05) / (min(a, b) + 0.05)


def parse_cor(s):
    import re
    m = re.match(r"rgba?\(([\d.]+),\s*([\d.]+),\s*([\d.]+)", s or "")
    return tuple(int(float(m.group(i))) for i in (1, 2, 3)) if m else None


def checar_contraste(png, itens):
    """Para cada trecho, compara a cor do texto com a cor dominante do fundo dentro da caixa do trecho."""
    import numpy as np
    from PIL import Image
    a = np.asarray(Image.open(png).convert("RGB")).astype(np.int32)
    ruins = []
    for it in itens:
        cor = parse_cor(it.get("color"))
        if not cor or it["w"] < 4 or it["h"] < 4:
            continue
        x0, y0 = max(0, it["x"]), max(0, it["y"])
        x1, y1 = min(1920, it["x"] + it["w"]), min(1080, it["y"] + it["h"])
        if x1 <= x0 or y1 <= y0:
            continue
        reg = a[y0:y1, x0:x1].reshape(-1, 3)
        d = np.abs(reg - np.array(cor)).sum(axis=1)
        fundo = reg[d > 90]
        if len(fundo) < 20:
            continue
        bg = tuple(int(v) for v in np.median(fundo, axis=0))
        r = contraste_hex(cor, bg)
        if r < 4.5:
            ruins.append({"trecho": it["t"][:50], "razao": round(r, 2), "texto": cor, "fundo": bg, "x": it["x"], "y": it["y"], "w": it["w"], "h": it["h"]})
    return ruins


FORTES = {"capa", "secao", "afirmacao", "imagem-total", "numero", "numeros", "citacao", "pergunta"}


def avisos_deck(pr, deck):
    """Avisos do deck inteiro (não travam). pr = slides medidos, sem os de apêndice."""
    av, seq = [], []
    for s in pr + [None]:
        if s and s["layout"] not in FORTES:
            seq.append(s["slide"])
            continue
        if len(seq) >= 5:
            av.append(f"ritmo: slides {seq[0]} a {seq[-1]} ({len(seq)} seguidos) sem momento forte (capa, seção, afirmação, imagem total, número, citação, pergunta).")
        seq = []
    for a, b in zip(pr, pr[1:]):
        if b["slide"] == a["slide"] + 1 and a["anim"] and a["anim"] == b["anim"]:
            av.append(f"movimento: slides {a['slide']} e {b['slide']} entram com a mesma sequência ({a['anim']}).")
    mins = [x.get("minutos") for x in deck["slides"] if isinstance(x.get("minutos"), (int, float))]
    dur = (deck.get("contrato") or {}).get("duracao_min")
    if mins and isinstance(dur, (int, float)) and sum(mins) > 0.9 * dur:
        av.append(f"tempo: os slides somam {sum(mins):g} min e o contrato prevê {dur:g} min. Deixe pelo menos 10% de folga.")
    return av


def folhas(pngs, rotulos, pasta, cols=3, rows=3):
    from PIL import Image, ImageDraw, ImageFont
    pasta.mkdir(parents=True, exist_ok=True)
    tw, th = 760, 428
    try:
        fonte = ImageFont.truetype(str(Path(__file__).resolve().parent.parent / "assets" / "fontes-ttf" / "AtkinsonHyperlegibleNext-700.ttf"), 26)
    except Exception:  # noqa: BLE001
        fonte = None
    saidas = []
    por = cols * rows
    for k in range(0, len(pngs), por):
        lote = pngs[k:k + por]
        S = Image.new("RGB", (cols * (tw + 16) + 16, ((len(lote) + cols - 1) // cols) * (th + 58) + 16), (22, 22, 22))
        d = ImageDraw.Draw(S)
        for j, p in enumerate(lote):
            im = Image.open(p).convert("RGB").resize((tw, th), Image.LANCZOS)
            x = 16 + (j % cols) * (tw + 16)
            y = 16 + (j // cols) * (th + 58)
            S.paste(im, (x, y))
            ok, txt = rotulos[k + j]
            d.rectangle([x, y + th + 6, x + 18, y + th + 24], fill=(60, 170, 90) if ok else (210, 50, 40))
            d.text((x + 28, y + th + 4), txt, fill=(235, 235, 235), font=fonte)
        out = pasta / f"folha_{k // por + 1:02d}.jpg"
        S.save(out, quality=86)
        saidas.append(out)
    return saidas


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("projeto")
    ap.add_argument("--slides", help="só estes slides, ex.: 1-5,9 (para conferir um lote)")
    ap.add_argument("--curto", action="store_true", help="imprime uma linha só (o relatório completo continua em verificacao/)")
    a = ap.parse_args()
    from playwright.sync_api import sync_playwright

    proj = Path(a.projeto).resolve()
    build = json.loads((proj / "dist" / "build.json").read_text(encoding="utf8"))
    html = proj / "dist" / build["arquivo"]
    deck = json.loads((proj / "deck.json").read_text(encoding="utf8"))
    lim = medir.limites_do_deck(deck.get("limites"))
    out = proj / "verificacao"
    sel = None
    if a.slides:
        sel = set()
        for part in a.slides.split(","):
            if "-" in part:
                x, y = part.split("-")
                sel.update(range(int(x), int(y) + 1))
            else:
                sel.add(int(part))
        out = out / "lote"  # lote parcial não substitui a verificação completa que a trava lê
    (out / "slides").mkdir(parents=True, exist_ok=True)

    resultado = {"arquivo": build["arquivo"], "hash": build["hash"], "quando": time.strftime("%Y-%m-%d %H:%M"), "limites": lim, "slides": []}
    console = []
    rede = []
    with sync_playwright() as p:
        b = p.chromium.launch()
        ctx = b.new_context(viewport={"width": 1920, "height": 1080}, reduced_motion="reduce", device_scale_factor=1)
        pg = ctx.new_page()
        pg.on("console", lambda m: console.append(f"{m.type}: {m.text}") if m.type in ("error", "warning") else None)
        pg.on("pageerror", lambda e: console.append(f"pageerror: {e}"))
        pg.on("request", lambda r: rede.append(r.url) if r.url.startswith("http") else None)
        pg.goto(html.as_uri() + "?final")
        pg.wait_for_function("window.SK && window.SK.pronto === true", timeout=60000)
        pg.evaluate("window.SK.final(true)")
        info = pg.evaluate("window.SK.info()")
        hashes = []
        for k, inf in enumerate(info):
            n = k + 1
            if sel and n not in sel:
                continue
            pg.evaluate(f"window.SK.ir({k})")
            pg.wait_for_timeout(120)
            png = out / "slides" / f"s{n:03d}.png"
            pg.screenshot(path=str(png))
            raiz = pg.query_selector(f'.sk-slide[data-i="{k}"]')
            res = pg.evaluate(medir.JS_TEXTO, raiz)
            ft = medir.classificar_textos(res["items"], lim)
            oc = medir.ocupacao(str(png), lim, res.get("visuais"))
            ct = checar_contraste(str(png), res["items"])
            sob = medir.sobreposicoes(res["items"])
            # retrato numa faixa estreita sempre corta o rosto (olhos, queixo). Vale para imagens marcadas "pessoa"
            faixas = pg.evaluate("""(r) => Array.from(r.querySelectorAll('figure[data-pessoa]')).map((f) => { const b = f.getBoundingClientRect();
                return { k: f.dataset.pessoa, w: Math.round(b.width), h: Math.round(b.height) }; }).filter((b) => b.w > 40 && b.h > 10 && (b.w / b.h > 3 || b.h / b.w > 4))""", raiz)
            en = pg.evaluate(medir.JS_ENFEITES, raiz)
            medir.sobrepor(str(png), str(out / "slides" / f"s{n:03d}_marcas.jpg"), oc, ft["problemas_fonte"] + [{**c, "papel": "contraste"} for c in ct] + en["reprova"] + en["final"])
            oc.pop("grade_vazia", None)
            tem_visual = inf["imagens"] > 0 or inf["grafico"] or inf["diagrama"]
            h = dhash(str(png))
            quase = bool(hashes) and ham(h, hashes[-1]) <= 10
            hashes.append(h)
            s = {
                "slide": n, "layout": inf["layout"], "titulo": (deck["slides"][k].get("titulo") or "")[:90],
                "fontes_ok": ft["fontes_ok"], "menor_fonte_px": ft["min_px"], "corpo_px": inf["corpo"], "titulo_px": inf["titulo_px"],
                "mediana_corpo_medida_px": ft["mediana_corpo_px"], "palavras": ft["palavras"],
                "problemas_fonte": ft["problemas_fonte"][:12],
                "tela_ocupada": oc["tela_ocupada"], **{k2: v for k2, v in oc.items() if k2 not in ("tela_ocupada", "grade")},
                "encaixe_ok": not inf["transborda"] and not sob, "texto_sobreposto": sob,
                "retrato_ok": not faixas, "retrato_em_faixa": faixas, "contraste_ok": not ct, "problemas_contraste": ct[:8],
                "imagem_real": inf["imagens"] > 0, "visual": bool(tem_visual), "arte_de_preenchimento": inf["arte"] > 0,
                "quase_igual_ao_anterior": bool(quase),
                "enfeites": en["reprova"], "enfeites_ok": not en["reprova"], "estado_final": en["final"], "estado_final_ok": not en["final"],
                "avisos": en["avisos"], "anim": en["anim"], "apendice": bool(deck["slides"][k].get("apendice")),
            }
            s["automatico_ok"] = s["fontes_ok"] and s["tela_ocupada"] and s["encaixe_ok"] and s["contraste_ok"] and s["enfeites_ok"] and s["estado_final_ok"] and s["retrato_ok"]
            resultado["slides"].append(s)
        b.close()

    # teste com a internet bloqueada
    offline = {"ok": True, "detalhe": []}
    with sync_playwright() as p:
        b = p.chromium.launch()
        ctx = b.new_context(viewport={"width": 1920, "height": 1080}, offline=True)
        pg = ctx.new_page()
        bloq = []
        pg.route("**/*", lambda r: (bloq.append(r.request.url), r.abort()) if r.request.url.startswith("http") else r.continue_())
        pg.goto(html.as_uri() + "?final")
        try:
            pg.wait_for_function("window.SK && window.SK.pronto === true", timeout=30000)
            fam = pg.evaluate("Array.from(document.fonts).filter(f=>f.status==='loaded').map(f=>f.family)")
            if not fam:
                offline["ok"] = False
                offline["detalhe"].append("nenhuma fonte embutida carregou")
        except Exception as e:  # noqa: BLE001
            offline["ok"] = False
            offline["detalhe"].append(f"não abriu sem rede: {e}")
        if bloq:
            offline["ok"] = False
            offline["detalhe"].append(f"pedidos à rede: {bloq[:5]}")
        b.close()

    ss = resultado["slides"]
    pr = [s for s in ss if not s["apendice"]]  # apêndice fica fora da variação e da contagem de imagens
    layouts = [s["layout"] for s in pr]
    repet = [pr[i]["slide"] for i in range(2, len(pr)) if layouts[i] == layouts[i - 1] == layouts[i - 2]]
    com_img = sum(1 for s in pr if s["imagem_real"])
    resultado["deck"] = {
        "slides": len(ss), "apendice": len(ss) - len(pr), "com_imagem_real": com_img, "com_visual": sum(1 for s in pr if s["visual"]),
        "layouts_distintos": len(set(layouts)), "tres_iguais_seguidos": repet,
        "quase_iguais": [pr[i]["slide"] for i in range(1, len(pr)) if pr[i]["quase_igual_ao_anterior"] and pr[i - 1]["slide"] == pr[i]["slide"] - 1],
        "offline": offline, "console": console[:20], "rede_durante_teste": rede[:10],
    }
    d = resultado["deck"]
    d["minimo_layouts"] = min(10, max(3, len(pr) // 2))
    d["variacao_ok"] = not repet and not d["quase_iguais"] and d["layouts_distintos"] >= d["minimo_layouts"]
    d["imagens_ok"] = com_img >= max(1, round(0.5 * len(pr)))
    d["avisos"] = avisos_deck(pr, deck)
    d["tecnico_ok"] = offline["ok"] and not [c for c in console if c.startswith(("error", "pageerror"))]
    if sel:
        resultado["parcial"] = True
        resultado["automatico_ok"] = all(s["automatico_ok"] for s in ss) and d["tecnico_ok"]
    else:
        resultado["automatico_ok"] = all(s["automatico_ok"] for s in ss) and d["variacao_ok"] and d["tecnico_ok"]
    (out / "relatorio.json").write_text(json.dumps(resultado, ensure_ascii=False, indent=1), encoding="utf8")

    rot = []
    for s in ss:
        falhas = [n for n, ok in (("fonte", s["fontes_ok"]), ("tela", s["tela_ocupada"]), ("encaixe", s["encaixe_ok"]), ("contraste", s["contraste_ok"]), ("enfeite", s["enfeites_ok"]), ("inacabado", s["estado_final_ok"]), ("retrato", s["retrato_ok"])) if not ok]
        rot.append((not falhas, f"{s['slide']:>3} {s['layout']}  corpo {s['corpo_px']}px  vazio {int(s['fracao_vazia'] * 100)}%" + (("  FALHA " + ",".join(falhas)) if falhas else "")))
    fs = folhas([out / "slides" / f"s{s['slide']:03d}.png" for s in ss], rot, out / "folhas")

    linhas = [f"# Verificação automática · {build['arquivo']} · {resultado['quando']}", "",
              (f"Lote {a.slides}: {'PASSOU' if resultado['automatico_ok'] else 'FALHOU'} nos slides do lote. Verificação parcial, que não vale para a trava. "
               "No fim, rode sem --slides." if sel else
               f"Resultado: {'PASSOU' if resultado['automatico_ok'] else 'FALHOU'}."), "",
              "| Slide | Layout | Fonte mínima | Corpo | Vazio | Maior vazio | Imagem | Situação |", "|---|---|---|---|---|---|---|---|"]
    for s in ss:
        falhas = [n for n, ok in (("fonte", s["fontes_ok"]), ("tela", s["tela_ocupada"]), ("encaixe", s["encaixe_ok"]), ("contraste", s["contraste_ok"]), ("enfeite", s["enfeites_ok"]), ("inacabado", s["estado_final_ok"]), ("retrato", s["retrato_ok"])) if not ok]
        linhas.append(f"| {s['slide']} | {s['layout']} | {s['menor_fonte_px']} px | {s['corpo_px']} px | {int(s['fracao_vazia'] * 100)}% | {int(s['maior_vazio'] * 100)}% | {'sim' if s['imagem_real'] else 'não'} | {'ok' if not falhas else 'FALHA ' + ', '.join(falhas)} |")
    ruins = [(s["slide"], x) for s in ss for x in s["enfeites"] + s["estado_final"]]
    if ruins:
        linhas += ["", "## Enfeites e estado final (REPROVA)", ""] + [f"- Slide {n}, {x['tipo']}: {x['msg']}" + (f" (“{x['trecho'][:40]}”)" if x["trecho"] else "") for n, x in ruins]
    av = [f"- {a}" for a in d["avisos"]]
    for s in ss:
        tipos = {}
        for x in s["avisos"]:
            tipos.setdefault(x["tipo"], []).append(x)
        av += [f"- Slide {s['slide']}, {tp}: {xs[0]['msg']}" + (f" ({len(xs)} trechos, como “{xs[0]['trecho'][:40]}”)" if len(xs) > 1 else (f" (“{xs[0]['trecho'][:40]}”)" if xs[0]["trecho"] else "")) for tp, xs in tipos.items()]
    if av:
        linhas += ["", f"## Avisos ({len(av)}, não travam, mas olhe cada um)", ""] + av
    linhas += ["", f"Slides com imagem real: {com_img} de {len(pr)}" + (f" (fora {d['apendice']} de apêndice)" if d["apendice"] else "") + f". Layouts distintos: {d['layouts_distintos']}.",
               f"Três layouts iguais seguidos: {repet or 'nenhum'}. Vizinhos quase idênticos: {d['quase_iguais'] or 'nenhum'}. Layouts distintos: {d['layouts_distintos']} (mínimo {d['minimo_layouts']}).",
               f"Sem internet: {'ok' if offline['ok'] else 'FALHA ' + '; '.join(offline['detalhe'])}. Erros de console: {len([c for c in console if c.startswith(('error', 'pageerror'))])}.",
               "", "Folhas de contato: " + ", ".join(str(f.relative_to(proj)) for f in fs)]
    (out / "relatorio.md").write_text("\n".join(linhas), encoding="utf8")
    if a.curto:
        print(f"{'PASSOU' if resultado['automatico_ok'] else 'FALHOU'} ({len(ss)} slides). Detalhes em verificacao/relatorio.md")
    else:
        print("\n".join(linhas))
    return 0 if resultado["automatico_ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
