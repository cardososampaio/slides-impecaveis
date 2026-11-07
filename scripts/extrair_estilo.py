#!/usr/bin/env python3
"""Extrai a paleta de um material de referência e sugere tema e ajustes_tema para o deck.json.

    python3 scripts/extrair_estilo.py referencia.pdf [--nome instituto] [--paginas 1-6]
    python3 scripts/extrair_estilo.py modelo.pptx | marca.png | pagina.html

Renderiza a referência (PDF por pdftoppm, PPTX pelo LibreOffice, HTML pelo Playwright, imagem direta),
agrupa os pixels em 5 a 8 cores dominantes (k-means em numpy) e escolhe fundo, tinta, acento e campos.
A tinta sempre passa de 4,5:1 sobre o fundo (se a referência não tiver, ela é escurecida ou clareada).
O tema base é o de fundo e tinta mais próximos em templates/runtime/temas.css.

Grava ~/.slides-impecaveis/estilos/NOME.json ({"tema", "ajustes_tema", "origem", "data"}) e NOME.png
(amostra das cores para OLHAR), e imprime o trecho para colar no deck.json. Fontes não são extraídas.
Sem LibreOffice, um PPTX usa as cores do tema do próprio arquivo (ppt/theme).
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path

import numpy as np
from PIL import Image

RAIZ = Path(__file__).resolve().parent.parent


def hexa(c):
    return "#%02X%02X%02X" % tuple(int(round(v)) for v in c)


def rgb(h):
    h = h.strip().lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], float)


def lum(c):
    v = np.asarray(c, float) / 255
    v = np.where(v <= 0.03928, v / 12.92, ((v + 0.055) / 1.055) ** 2.4)
    return 0.2126 * v[0] + 0.7152 * v[1] + 0.0722 * v[2]


def contraste(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def croma(c):
    return float(np.max(c) - np.min(c))


def paginas(arg):
    a, _, b = arg.partition("-")
    return int(a), int(b or a)


def imagens(origem: Path, pags, tmp: Path):
    suf = origem.suffix.lower()
    if suf in (".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tif", ".tiff"):
        return [Image.open(origem)]
    if suf in (".html", ".htm"):
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            b = p.chromium.launch()
            pg = b.new_page(viewport={"width": 1920, "height": 1080})
            pg.goto(origem.resolve().as_uri() + ("?final" if "sk" in origem.read_text(encoding="utf8", errors="ignore")[:4000] else ""))
            pg.wait_for_timeout(1500)
            out = tmp / "html.png"
            pg.screenshot(path=str(out))
            b.close()
        return [Image.open(out)]
    if suf == ".pptx":
        exe = shutil.which("soffice") or shutil.which("libreoffice")
        if not exe:
            return None  # usa as cores do tema do arquivo
        subprocess.run([exe, f"-env:UserInstallation=file://{tmp / 'perfil'}", "--headless", "--convert-to", "pdf", "--outdir", str(tmp), str(origem)],
                       capture_output=True, timeout=300)
        origem = tmp / (origem.stem + ".pdf")
        if not origem.exists():
            raise SystemExit("ERRO o LibreOffice não converteu o PPTX.")
        suf = ".pdf"
    if suf == ".pdf":
        if not shutil.which("pdftoppm"):
            raise SystemExit("ERRO para ler PDF instale poppler-utils (pdftoppm) ou exporte uma página como imagem.")
        subprocess.run(["pdftoppm", "-f", str(pags[0]), "-l", str(pags[1]), "-r", "40", "-png", str(origem), str(tmp / "pg")], timeout=300)
        return [Image.open(f) for f in sorted(tmp.glob("pg*.png"))]
    raise SystemExit(f"ERRO formato não suportado: {suf}")


def cores_tema_pptx(origem: Path):
    """Sem LibreOffice: cores do esquema do tema (dk1, lt1, accent1 a accent6), com pesos fixos."""
    with zipfile.ZipFile(origem) as z:
        nomes = sorted(n for n in z.namelist() if re.fullmatch(r"ppt/theme/theme\d+\.xml", n))
        xml = z.read(nomes[0]).decode("utf8", "ignore")
    pesos = {"lt1": 50, "dk1": 20, "lt2": 6, "dk2": 6, "accent1": 6, "accent2": 4, "accent3": 3, "accent4": 2, "accent5": 2, "accent6": 1}
    out = []
    for nome, peso in pesos.items():
        m = re.search(rf"<a:{nome}>.*?(?:srgbClr val|lastClr)=\"([0-9A-Fa-f]{{6}})\"", xml, re.S)
        if m:
            out.append((rgb(m.group(1)), peso / 100))
    return out


def kmeans(px, k=8, voltas=15):
    rng = np.random.default_rng(7)
    ordem = np.argsort(px @ np.array([0.299, 0.587, 0.114]))
    cent = px[ordem[np.linspace(0, len(px) - 1, k).astype(int)]].copy()  # começa espalhado em luminância
    for _ in range(voltas):
        d = ((px[:, None, :] - cent[None]) ** 2).sum(2)
        lab = d.argmin(1)
        for j in range(k):
            sel = px[lab == j]
            cent[j] = sel.mean(0) if len(sel) else px[rng.integers(len(px))]
    pesos = np.bincount(lab, minlength=k) / len(px)
    grupos = sorted(zip(cent, pesos), key=lambda t: -t[1])
    juntos = []  # funde cores quase iguais
    for c, w in grupos:
        for g in juntos:
            if np.linalg.norm(g[0] - c) < 22:
                g[0] = (g[0] * g[1] + c * w) / (g[1] + w)
                g[1] += w
                break
        else:
            juntos.append([c, w])
    juntos.sort(key=lambda g: -g[1])
    return [(c, w) for c, w in juntos if w >= 0.004][:8]


def temas_base():
    """Fundo e tinta de cada tema, lidos agora de temas.css (outros temas podem ter entrado)."""
    css = (RAIZ / "templates" / "runtime" / "temas.css").read_text(encoding="utf8")
    hx = r"\s*(#[0-9A-Fa-f]{6}|#[0-9A-Fa-f]{3})\b"
    out = {}
    for nome, corpo in re.findall(r'html\[data-tema="([\w-]+)"\]\s*\{([^}]*)\}', css):
        f, t = re.search(r"--fundo:" + hx, corpo), re.search(r"--tinta:" + hx, corpo)
        if f and t and nome not in out:
            out[nome] = (rgb(f.group(1)), rgb(t.group(1)))
    try:  # só temas que o construtor aceita (índice templates/temas.json)
        validos = json.loads((RAIZ / "templates" / "temas.json").read_text(encoding="utf8"))["temas"]
        out = {k: v for k, v in out.items() if k in validos} or out
    except (OSError, KeyError, ValueError):
        pass
    return out


def ajustar(tinta, fundo, alvo=4.6):
    """Escurece ou clareia a tinta até passar de 4,5:1 sobre o fundo."""
    destino = np.zeros(3) if lum(fundo) > 0.18 else np.full(3, 255.0)
    t = np.array(tinta, float)
    for _ in range(40):
        if contraste(t, fundo) >= alvo:
            break
        t = t + (destino - t) * 0.12
    return t


def escolher(paleta):
    fundo = paleta[0][0]
    claro = lum(fundo) > 0.18
    papel = np.clip(fundo + (12 if claro else 10), 0, 255)
    le = lambda c: min(contraste(c, fundo), contraste(c, papel))  # noqa: E731  texto fica sobre o fundo e sobre o papel
    firme = lambda c, alvo=4.6: ajustar(ajustar(c, papel, alvo), fundo, alvo)  # noqa: E731
    resto = [c for c, _ in paleta[1:]]
    fortes = [c for c in resto if le(c) >= 7]  # a mais frequente entre as de contraste alto
    tinta = fortes[0] if fortes else max(resto, key=le) if resto else (np.zeros(3) if claro else np.full(3, 255.0))
    tinta = firme(tinta)
    # acentos também viram texto (rótulos de gráfico, destaques): 4,5:1 sobre fundo e papel
    cand = sorted([c for c in resto if np.linalg.norm(c - tinta) > 45], key=croma, reverse=True)
    acento = firme(next((c for c in cand if le(c) >= 4.5), cand[0] if cand else tinta))
    acento2 = next((c for c in cand if np.linalg.norm(c - acento) > 60 and croma(c) >= 25 and le(c) >= 4.5), None)
    acento2 = firme(acento2 if acento2 is not None else (acento + tinta) / 2)  # sem segunda cor forte: entre acento e tinta
    sobre = next((c for c in (papel, fundo, tinta) if contraste(acento, c) >= 4.5),
                 np.zeros(3) if contraste(acento, np.zeros(3)) > contraste(acento, np.full(3, 255.0)) else np.full(3, 255.0))
    # o motor escreve sobre o campo em #F6F1E7 ou na tinta, o que contrastar mais
    claro_motor = rgb("F6F1E7")
    campos = []
    for c in [tinta, acento, acento2] + resto:
        if max(contraste(c, claro_motor), contraste(c, tinta)) >= 4.5 and contraste(c, fundo) >= 1.6 and all(np.linalg.norm(c - x) > 45 for x in campos):
            campos.append(c)
    campos = campos or [ajustar(acento, claro_motor)]
    aj = {"fundo": hexa(fundo), "papel": hexa(papel), "tinta": hexa(tinta), "acento": hexa(acento), "acento2": hexa(acento2),
          "sobre-acento": hexa(sobre), "campos": ",".join(hexa(c) for c in campos[:6])}
    return aj


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("origem")
    ap.add_argument("--nome", help="nome do estilo (padrão: nome do arquivo)")
    ap.add_argument("--paginas", default="1-6", help="PDF e PPTX: páginas usadas, ex. 1-6")
    ap.add_argument("--pasta", default=str(Path.home() / ".slides-impecaveis" / "estilos"))
    a = ap.parse_args()
    origem = Path(a.origem)
    if not origem.is_file():
        raise SystemExit(f"ERRO arquivo não encontrado: {origem}")
    nome = re.sub(r"[^\w-]+", "-", a.nome or origem.stem).strip("-").lower()
    with tempfile.TemporaryDirectory() as t:
        ims = imagens(origem, paginas(a.paginas), Path(t))
        if ims is None:
            paleta = cores_tema_pptx(origem)
            print("AVISO LibreOffice indisponível: usei as cores do tema do PPTX, não as dos slides.")
        else:
            px = []
            for im in ims:
                im = im.convert("RGB")
                im.thumbnail((240, 240))
                px.append(np.asarray(im, float).reshape(-1, 3))
            paleta = kmeans(np.concatenate(px))
    if not paleta:
        raise SystemExit("ERRO nenhuma cor encontrada.")
    aj = escolher(paleta)
    base = temas_base()
    f, tt = rgb(aj["fundo"]), rgb(aj["tinta"])
    tema = min(base, key=lambda n: np.linalg.norm(base[n][0] - f) + 0.6 * np.linalg.norm(base[n][1] - tt))
    pasta = Path(a.pasta).expanduser()
    pasta.mkdir(parents=True, exist_ok=True)
    dados = {"tema": tema, "ajustes_tema": aj, "origem": str(origem.resolve()), "data": datetime.now().strftime("%Y-%m-%d")}
    (pasta / f"{nome}.json").write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf8")
    amostra = Image.new("RGB", (120 * len(paleta), 160), (255, 255, 255))
    for i, (c, w) in enumerate(paleta):
        amostra.paste(tuple(int(v) for v in c), (i * 120, 0, (i + 1) * 120, 160))
    amostra.save(pasta / f"{nome}.png")
    print("cores dominantes:", ", ".join(f"{hexa(c)} {w:.0%}" for c, w in paleta))
    print(f"contraste tinta/fundo {contraste(tt, f):.1f}:1, acento/fundo {contraste(rgb(aj['acento']), f):.1f}:1, "
          f"sobre-acento/acento {contraste(rgb(aj['sobre-acento']), rgb(aj['acento'])):.1f}:1")
    print(f"estilo salvo em {pasta / (nome + '.json')} (amostra em {nome}.png, OLHE antes de usar)")
    print(f'\nNo deck.json, use o estilo salvo com  "estilo": "{nome}"  ou cole o trecho abaixo (o deck sempre vence o estilo).\n')
    print(f'  "tema": "{tema}",\n  "ajustes_tema": ' + json.dumps(aj, ensure_ascii=False, indent=4).replace("\n", "\n  ") + ",")
    print("\nO verificar.py mede o contraste de novo em cada slide. Mostre a amostra à pessoa (porta G3).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
