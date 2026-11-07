#!/usr/bin/env python3
"""Instala na máquina as fontes do tema, para o PPTX abrir no PowerPoint com a tipografia do HTML.

    python3 scripts/instalar_fontes.py              # todas as famílias (Windows, macOS e Linux)
    python3 scripts/instalar_fontes.py --tema gravura
    python3 scripts/instalar_fontes.py --listar     # só mostra o que seria instalado

A instalação é só para o usuário atual e não pede administrador.
  Windows  copia para %LOCALAPPDATA%\\Microsoft\\Windows\\Fonts e registra em HKCU\\...\\Fonts
  macOS    copia para ~/Library/Fonts
  Linux    copia para ~/.local/share/fonts e roda fc-cache

Todas as fontes são livres (SIL Open Font License 1.1, licenças em assets/fontes/licencas/).
Feche e abra de novo o PowerPoint depois de instalar.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
TTF = SKILL / "assets" / "fontes-ttf"
INDICE = json.loads((SKILL / "templates" / "temas.json").read_text(encoding="utf8"))


def arquivos(tema=None):
    """TTFs das famílias do tema (ou de todos os temas), lidos de templates/temas.json."""
    temas = [tema] if tema else list(INDICE["temas"])
    fams = {INDICE["temas"][t][k] for t in temas for k in ("titulo", "corpo")}
    return sorted({TTF / a for f in fams for a in INDICE["familias"][f]["ttf"]})


def nome_da_fonte(p: Path) -> str:
    try:
        from fontTools.ttLib import TTFont
        n = TTFont(str(p))["name"]
        return f"{n.getDebugName(4) or p.stem} (TrueType)"
    except Exception:  # noqa: BLE001
        return f"{p.stem} (TrueType)"


def destino() -> Path:
    s = platform.system()
    if s == "Windows":
        return Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local"))) / "Microsoft" / "Windows" / "Fonts"
    if s == "Darwin":
        return Path.home() / "Library" / "Fonts"
    return Path.home() / ".local" / "share" / "fonts" / "slides-impecaveis"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tema", choices=sorted(INDICE["temas"]))
    ap.add_argument("--listar", action="store_true")
    a = ap.parse_args()
    arqs = [p for p in arquivos(a.tema) if p.is_file()]
    if not arqs:
        print(f"ERRO nenhuma fonte encontrada em {TTF}")
        return 1
    dst = destino()
    print(f"{len(arqs)} arquivos para {dst}")
    if a.listar:
        for p in arqs:
            print("  ", p.name)
        return 0
    dst.mkdir(parents=True, exist_ok=True)
    win = platform.system() == "Windows"
    if win:
        import winreg  # noqa: PLC0415
        chave = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows NT\CurrentVersion\Fonts")
    for p in arqs:
        alvo = dst / p.name
        shutil.copyfile(p, alvo)
        if win:
            winreg.SetValueEx(chave, nome_da_fonte(p), 0, winreg.REG_SZ, str(alvo))
        print("  instalada", p.name)
    if platform.system() == "Linux" and shutil.which("fc-cache"):
        subprocess.run(["fc-cache", "-f", str(dst)], check=False)
    print("Pronto. Feche e abra de novo o PowerPoint (ou o LibreOffice) para ver as fontes.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
