"""Gera o .zip da skill para distribuir, só com o que a skill precisa para funcionar.

    python3 scripts/empacotar.py [--saida slides-impecaveis.zip] [--limite-mb 50]

Entra: SKILL.md, AGENTS.md, README.md, LICENSE-NOTES.md, requirements.txt, agents/, references/,
scripts/, templates/, assets/ e exemplos/ (HTML, deck.json, imagens tratadas, folhas e marcas).
Fica de fora: qualquer outra pasta na raiz (projetos de teste, decks da pessoa), __pycache__,
imagens brutas, cópias da amostra de temas, capturas PNG, PDF, PPTX e painéis de revisão.
O pacote passa do limite e o script avisa, para ninguém distribuir 700 MB por engano.
"""
from __future__ import annotations

import argparse
import fnmatch
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
ARQUIVOS = ["SKILL.md", "AGENTS.md", "README.md", "LICENSE-NOTES.md", "requirements.txt"]
PASTAS = ["agents", "references", "scripts", "templates", "assets", "exemplos"]
FORA = ["*/__pycache__/*", "*.pyc", "*/brutas/*", "*/amostra-temas/*/*", "*.png", "*.pdf", "*.pptx",
        "*/revisao/painel.html", "*/verificacao/pptx/pp-*", "*/.DS_Store", "*/Thumbs.db", "*/_*.py", "*/_*.json"]
PNG_OK = ["templates/*", "assets/*"]  # PNG dentro do motor ou dos ativos da skill continua


def entra(rel: str) -> bool:
    if any(fnmatch.fnmatch(rel, p) for p in FORA):
        return rel.endswith(".png") and any(fnmatch.fnmatch(rel, p) for p in PNG_OK)
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--saida", default=str(RAIZ.parent / "slides-impecaveis.zip"))
    ap.add_argument("--limite-mb", type=float, default=50)
    a = ap.parse_args()
    lista = [RAIZ / f for f in ARQUIVOS if (RAIZ / f).exists()]
    for p in PASTAS:
        lista += sorted(x for x in (RAIZ / p).rglob("*") if x.is_file())
    fora_raiz = sorted(x.name for x in RAIZ.iterdir() if x.is_dir() and x.name not in PASTAS and not x.name.startswith("."))
    total, n = 0, 0
    saida = Path(a.saida).resolve()
    with zipfile.ZipFile(saida, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for f in lista:
            rel = f.relative_to(RAIZ).as_posix()
            if not entra(rel):
                continue
            z.write(f, "slides-impecaveis/" + rel)
            total += f.stat().st_size
            n += 1
    mb = saida.stat().st_size / 1e6
    print(f"OK {saida} ({n} arquivos, {total / 1e6:.1f} MB descompactado, {mb:.1f} MB no zip)")
    if fora_raiz:
        print("Pastas da raiz deixadas de fora (projetos ou testes): " + ", ".join(fora_raiz))
    if mb > a.limite_mb:
        print(f"AVISO o zip passou de {a.limite_mb:.0f} MB. Veja o que cresceu em exemplos/ antes de distribuir.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
