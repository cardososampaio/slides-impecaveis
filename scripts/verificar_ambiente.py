#!/usr/bin/env python3
"""Confere se a máquina tem o que a skill precisa e diz como instalar o que faltar.

    python3 scripts/verificar_ambiente.py

Obrigatório: Python 3.9+, Pillow, numpy, Playwright com Chromium (render, verificação, PDF e PPTX), python-pptx.
Opcional: python-docx (ler .docx), pypdf ou pdftotext (ler .pdf), LibreOffice (conferir o PPTX renderizado),
pdfinfo e pdftoppm (contar páginas, ler PDF de referência em extrair_estilo.py), fc-list (fontes instaladas).
"""
import importlib
import shutil
from pathlib import Path
import sys

ok = True


def linha(nome, bom, dica=""):
    global ok
    print(f"[{'ok' if bom else 'FALTA'}] {nome}" + ("" if bom else f"  ->  {dica}"))


def tem(mod):
    try:
        importlib.import_module(mod)
        return True
    except Exception:  # noqa: BLE001
        return False


py = sys.version_info >= (3, 9)
linha(f"Python {sys.version.split()[0]}", py, "instale Python 3.9 ou mais novo")
ok &= py
pip = f"{sys.executable} -m pip install"
for mod, pacote in (("PIL", "pillow"), ("numpy", "numpy"), ("pptx", "python-pptx"), ("playwright", "playwright")):
    b = tem(mod)
    linha(pacote, b, f"{pip} {pacote}   (em Linux gerenciado, acrescente --break-system-packages)")
    ok &= b
if tem("playwright"):
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            b = p.chromium.launch()
            b.close()
        linha("Chromium do Playwright", True)
    except Exception as e:  # noqa: BLE001
        linha("Chromium do Playwright", False, f"{sys.executable} -m playwright install chromium   ({str(e).splitlines()[0][:80]})")
        ok = False
linha("python-docx (opcional, para ler .docx)", tem("docx"), f"{pip} python-docx")
linha("pypdf ou pdftotext (opcional, para ler .pdf)", tem("pypdf") or bool(shutil.which("pdftotext")), f"{pip} pypdf   (ou instale poppler-utils)")
lo = shutil.which("soffice") or shutil.which("libreoffice")
linha("LibreOffice (opcional, para --conferir o PPTX)", bool(lo), "instale o LibreOffice se quiser conferir o PPTX renderizado")
linha("pdfinfo e pdftoppm (opcional)", bool(shutil.which("pdfinfo") and shutil.which("pdftoppm")), "poppler-utils; sem ele a contagem de páginas usa um método interno e extrair_estilo.py não lê PDF")
sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from checagens import _tesseract
    tess = bool(_tesseract())
except Exception:  # noqa: BLE001
    tess = bool(shutil.which("tesseract"))
linha("Tesseract (opcional, lê texto dentro das imagens)", tess, "Windows: instalador do UB Mannheim (github.com/UB-Mannheim/tesseract). Linux: apt install tesseract-ocr. macOS: brew install tesseract. Sem ele, a skill ainda reconhece telas e figuras com texto")
linha("OpenCV (opcional, acha rostos para não cortá-los)", tem("cv2"), f"{pip} opencv-python-headless")
linha("fc-list (opcional, para --conferir as fontes do PPTX)", bool(shutil.which("fc-list")), "fontconfig; no Windows e no macOS confira as fontes à mão")
print()
print("ambiente OK" if ok else "Faltam itens obrigatórios. Instale e rode de novo. Sem render não há verificação, e sem verificação nada é aprovado.")
sys.exit(0 if ok else 1)
