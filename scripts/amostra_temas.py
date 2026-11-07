#!/usr/bin/env python3
"""Mostra os mesmos slides em vários temas, para a pessoa escolher a direção visual (porta G2).

    python3 scripts/amostra_temas.py PROJETO                     # sugere 3 temas pelo contrato
    python3 scripts/amostra_temas.py PROJETO --temas civico,porcelana,gravura
    python3 scripts/amostra_temas.py PROJETO --todos [--completo] [--slides 1,3,7]

Sem --temas nem --todos, lê contrato.perfil, contrato.mundo, publico e sala no deck.json e escolhe
pelo índice templates/temas.json uma opção segura, uma ousada e uma curinga. Gera
PROJETO/amostra-temas/temas.jpg (ou temas_1.jpg, temas_2.jpg... com seis temas por folha). As cópias
do deck em cada tema são apagadas no fim (--manter guarda o HTML de cada tema). Não altera o projeto. Mostre as folhas à pessoa e espere a escolha.
--completo roda a verificação de todos os slides em cada tema.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import unicodedata
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

AQUI = Path(__file__).resolve().parent
INDICE = json.loads((AQUI.parent / "templates" / "temas.json").read_text(encoding="utf8"))
TEMAS = INDICE["temas"]
POR_FOLHA = 6


def _n(s):
    return unicodedata.normalize("NFKD", str(s).lower()).encode("ascii", "ignore").decode()


def sugerir(deck):
    """Três temas (segura, ousada, curinga) a partir do contrato. Devolve [(tema, papel, motivo)]."""
    con = deck.get("contrato") or {}
    perfil = con.get("perfil") or "aula"
    texto = _n(" ".join(str(con.get(k, "")) for k in ("perfil", "mundo", "publico", "sala", "tese", "forma")))
    escura = "escur" in _n(con.get("sala", ""))
    nota = {}
    for t, m in TEMAS.items():
        p = sum(2 for w in m["bom_para"] if _n(w) in texto) - sum(3 for w in m["evitar_para"] if _n(w) in texto)
        p += 3 if perfil in m["bom_para"] else 0
        p -= 6 if perfil in m["evitar_para"] else 0
        p += (2 if not m["claro"] else -1) if escura else (0 if m["claro"] else -2)
        nota[t] = p
    ordem = sorted(TEMAS, key=lambda t: (-nota[t], t))
    segura = next(t for t in ordem if TEMAS[t]["ousadia"] <= 2 and TEMAS[t]["formalidade"] != "baixa")
    ousada = next((t for t in ordem if TEMAS[t]["ousadia"] == 3 and t != segura and nota[t] >= 0), next(t for t in ordem if t != segura))
    resto = [t for t in ordem if t not in (segura, ousada) and nota[t] >= 0 and TEMAS[t]["arte"] != TEMAS[segura]["arte"]] or [t for t in ordem if t not in (segura, ousada)]
    semente = int(hashlib.sha1(str(con.get("tese", "")).encode()).hexdigest(), 16)
    curinga = resto[semente % min(len(resto), 5)]
    return [(segura, "segura", TEMAS[segura]["tom"]), (ousada, "ousada", TEMAS[ousada]["tom"]), (curinga, "curinga", TEMAS[curinga]["tom"])]


def construir_tema(proj, deck, base, tema, completo):
    alvo = base / tema
    if alvo.exists():
        shutil.rmtree(alvo)
    alvo.mkdir(parents=True)
    d = dict(deck)
    d["tema"] = tema
    d.pop("paleta", None)  # a amostra mostra o tema puro
    d.pop("estilo", None)
    (alvo / "deck.json").write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf8")
    try:
        (alvo / "assets").symlink_to(proj / "assets", target_is_directory=True)
    except OSError:  # Windows sem permissão para links: copia as imagens tratadas
        shutil.copytree(proj / "assets", alvo / "assets", ignore=shutil.ignore_patterns("brutas"))
    if (proj / "texto_origem.json").exists():
        shutil.copy(proj / "texto_origem.json", alvo / "texto_origem.json")
    r = subprocess.run([sys.executable, "-I", str(AQUI / "construir.py"), str(alvo)], capture_output=True, text=True)
    if r.returncode:
        return f"construção falhou:\n{r.stdout[-800:]}"
    if not completo:
        return "construído"
    v = subprocess.run([sys.executable, "-I", str(AQUI / "verificar.py"), str(alvo)], capture_output=True, text=True)
    if v.returncode == 0:
        return "PASSOU na verificação"
    try:
        rel = json.loads((alvo / "verificacao" / "relatorio.json").read_text(encoding="utf8"))
        ruins = [s["slide"] for s in rel.get("slides", []) if not s.get("automatico_ok")]
    except (OSError, ValueError):
        ruins = []
    return f"FALHOU na verificação (slides {ruins or 'condições gerais'}). Veja {alvo / 'verificacao' / 'relatorio.md'}"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("projeto")
    ap.add_argument("--slides", default="1,3,7")
    ap.add_argument("--temas", help="lista separada por vírgulas")
    ap.add_argument("--todos", action="store_true", help="todos os temas do índice")
    ap.add_argument("--completo", action="store_true", help="verifica e gera folhas de todos os slides em cada tema")
    ap.add_argument("--processos", type=int, default=3, help="temas construídos ao mesmo tempo (padrão 3)")
    ap.add_argument("--manter", action="store_true", help="guarda o deck construído de cada tema (por padrão só ficam as folhas, para o projeto não crescer)")
    a = ap.parse_args()
    from PIL import Image, ImageDraw, ImageFont
    from playwright.sync_api import sync_playwright

    proj = Path(a.projeto).resolve()
    deck = json.loads((proj / "deck.json").read_text(encoding="utf8"))
    nums = [int(x) for x in a.slides.split(",") if x.strip()]
    papeis = {}
    if a.todos:
        temas = list(TEMAS)
    elif a.temas:
        temas = [t.strip() for t in a.temas.split(",") if t.strip()]
        fora = [t for t in temas if t not in TEMAS]
        if fora:
            print(f"ERRO tema(s) inexistente(s): {', '.join(fora)}. Temas: {', '.join(TEMAS)}")
            return 1
    else:
        sug = sugerir(deck)
        temas = [t for t, _, _ in sug]
        for t, p, m in sug:
            papeis[t] = p
            print(f"sugestão {p}: {t} ({m})")
        print("Para ver outros, use --temas a,b,c ou --todos.")
    base = proj / "amostra-temas"
    base.mkdir(exist_ok=True)
    with ThreadPoolExecutor(max(1, a.processos)) as ex:
        estados = dict(zip(temas, ex.map(lambda t: construir_tema(proj, deck, base, t, a.completo), temas)))
    linhas = []
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1920, "height": 1080})
        for tema in temas:
            print(f"[{tema}] {estados[tema]}")
            if estados[tema].startswith("construção falhou"):
                continue
            alvo = base / tema
            build = json.loads((alvo / "dist" / "build.json").read_text(encoding="utf8"))
            pg.goto((alvo / "dist" / build["arquivo"]).as_uri() + "?final")
            pg.wait_for_function("window.SK && window.SK.pronto === true", timeout=60000)
            pg.evaluate("window.SK.final(true)")
            caps = []
            for n in nums:
                pg.evaluate(f"window.SK.ir({n - 1})")
                pg.wait_for_timeout(120)
                out = alvo / f"amostra_{n:02d}.png"
                pg.screenshot(path=str(out))
                caps.append(out)
            linhas.append((tema, caps))
        b.close()
    for velha in list(base.glob("temas.jpg")) + list(base.glob("temas_*.jpg")):
        velha.unlink()
    tw, th, rot = 720, 405, 250
    try:
        f = ImageFont.truetype(str(AQUI.parent / "assets" / "fontes-ttf" / "AtkinsonHyperlegibleNext-700.ttf"), 34)
        f2 = ImageFont.truetype(str(AQUI.parent / "assets" / "fontes-ttf" / "AtkinsonHyperlegibleNext-400.ttf"), 26)
    except Exception:  # noqa: BLE001
        f = f2 = None
    grupos = [linhas[i:i + POR_FOLHA] for i in range(0, len(linhas), POR_FOLHA)]
    for gi, grupo in enumerate(grupos, 1):
        S = Image.new("RGB", (rot + len(nums) * (tw + 14) + 14, len(grupo) * (th + 14) + 14), (22, 22, 22))
        dr = ImageDraw.Draw(S)
        for i, (tema, caps) in enumerate(grupo):
            y = 14 + i * (th + 14)
            dr.text((18, y + th // 2 - 24), tema, fill=(240, 236, 228), font=f)
            if tema in papeis:
                dr.text((18, y + th // 2 + 18), papeis[tema], fill=(200, 192, 178), font=f2)
            for j, c in enumerate(caps):
                S.paste(Image.open(c).convert("RGB").resize((tw, th), Image.LANCZOS), (rot + 14 + j * (tw + 14), y))
        nome = "temas.jpg" if len(grupos) == 1 else f"temas_{gi}.jpg"
        S.save(base / nome, quality=86)
        print(f"folha de comparação: {base / nome}")
    if not a.manter:  # cada tema é uma cópia do deck com imagens e fontes embutidas (5 a 35 MB). Ficam só as folhas
        for tema in temas:
            alvo = base / tema
            if not alvo.exists():
                continue
            guardar = []
            if a.completo:
                guardar = [alvo / "verificacao" / "relatorio.md"] + sorted((alvo / "verificacao" / "folhas").glob("*.jpg"))
            if guardar:
                tmp = base / f".{tema}-guardar"
                tmp.mkdir(exist_ok=True)
                for g in guardar:
                    if g.exists():
                        shutil.move(str(g), tmp / g.name)
                shutil.rmtree(alvo, ignore_errors=True)
                tmp.rename(alvo)
            else:
                shutil.rmtree(alvo, ignore_errors=True)
        print("Cópias por tema apagadas (use --manter para guardá-las).")
    print("Mostre as folhas à pessoa e espere a escolha do tema.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
