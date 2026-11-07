"""Checagens baratas que o construtor roda antes de montar o HTML (milissegundos, sem navegador).

Cobrem o que um modelo sem visão não percebe sozinho.
  campos_desconhecidos   campo com nome errado ("title", "titlo") que sumiria em silêncio
  estilo_texto           pontuação e palavras proibidas pelo "estilo_texto" do deck
  imagens_repetidas      a mesma obra usada em mais de dois slides, mesmo com nomes e recortes diferentes
  texto_em_imagem        captura de tela, figura de livro, anúncio ou ficha com texto dentro
  marcar_pessoas         retrato de pessoa (para o motor não cortar o rosto numa faixa)

Os resultados de imagem ficam guardados no .json de proveniência de cada arquivo, então o custo
de OCR acontece uma vez por imagem.
"""
from __future__ import annotations

import difflib
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
RUNTIME = SKILL / "templates" / "runtime"

# ---------------------------------------------------------------- campos
_EXTRA_SLIDE = {"layout", "apendice", "cortavel", "minutos", "notas", "etapas", "intensidade", "transicao", "morph",
                "foco_imagem", "legendas", "fontes_notas", "fonte", "fonte_visivel", "rascunho_layout", "destaques",
                "destaque", "tmax", "tmin", "cmax", "cmin", "cteto", "tteto", "porque"}
_EXTRA_DECK = {"titulo", "autor", "instituicao", "data", "idioma", "tema", "paleta", "estilo", "ajustes_tema", "contrato",
               "secoes", "slides", "imagens", "slug", "modo_texto", "creditos", "creditos_extra", "legendas_nas_imagens",
               "fontes_no_slide", "pisos", "arte_tema", "transicao", "intensidade", "limites", "capa", "estilo_texto",
               "perfil", "duracao", "publico", "$schema", "_comentario"}
_METODOS_JS = {"dataset", "query", "class", "has", "trim", "length", "map", "forEach", "filter", "split", "join"}


def _chaves_do_motor():
    txt = "\n".join(p.read_text(encoding="utf8") for p in RUNTIME.glob("*.js"))
    s = set(re.findall(r"\b(?:s|SLIDE_ATUAL)\.([a-z_][a-z0-9_]*)", txt)) - _METODOS_JS
    d = set(re.findall(r"\bD\.([a-z_][a-z0-9_]*)", txt)) - _METODOS_JS
    return s | _EXTRA_SLIDE, d | _EXTRA_DECK


def campos_desconhecidos(deck):
    """Lista de (onde, campo, sugestão, é_slide)."""
    ks, kd = _chaves_do_motor()
    out = []
    for k in deck:
        if k not in kd and not k.startswith("_"):
            out.append(("deck.json", k, (difflib.get_close_matches(k, kd, 1, 0.7) or [""])[0], False))
    for n, s in enumerate(deck.get("slides") or [], 1):
        for k in s:
            if k not in ks and not k.startswith("_"):
                out.append((f"slide {n}", k, (difflib.get_close_matches(k, ks, 1, 0.7) or [""])[0], True))
    return out


# ---------------------------------------------------------------- estilo do texto
_CAMPOS_TEXTO = ("titulo", "subtitulo", "texto", "itens", "citacao", "cartoes", "colunas", "passos", "eventos", "numeros", "pergunta")
_SINAIS = {":": re.compile(r"(?<!\d):(?=\s)|:$"), ";": re.compile(r";"), "—": re.compile(r"\s—|—\s|–\s|\s–")}


def _textos(v, acc):
    if isinstance(v, str):
        if not re.match(r"https?://", v):
            acc.append(v)
    elif isinstance(v, dict):
        for k, x in v.items():
            if k not in ("imagem", "fonte", "url", "autor", "obra"):
                _textos(x, acc)
    elif isinstance(v, list):
        for x in v:
            _textos(x, acc)
    return acc


def estilo_texto(deck):
    """O deck pode pedir, por exemplo, {"sem": [":", ";", "—"], "vetadas": ["crucial", "sinergia"]}."""
    est = deck.get("estilo_texto") or {}
    if not est:
        return []
    sem = [x for x in est.get("sem", []) if x in _SINAIS]
    vet = [re.compile(r"\b" + re.escape(w.lower()) + r"\b") for w in est.get("vetadas", []) if w.strip()]
    out = []
    for n, s in enumerate(deck.get("slides") or [], 1):
        if s.get("layout") == "referencias":
            continue
        for campo in _CAMPOS_TEXTO:
            for t in _textos(s.get(campo), []):
                limpo = re.sub(r"<[^>]+>", "", t)
                for x in sem:
                    if _SINAIS[x].search(limpo):
                        out.append(f'slide {n}, {campo}: o estilo do deck proíbe "{x}" ("{limpo[:60]}"). Reescreva com ponto ou vírgula.')
                for r in vet:
                    m = r.search(limpo.lower())
                    if m:
                        out.append(f'slide {n}, {campo}: palavra vetada "{m.group(0)}" ("{limpo[:60]}").')
    return out


# ---------------------------------------------------------------- imagens
def _meta(p: Path):
    j = Path(str(p) + ".json")
    try:
        return json.loads(j.read_text(encoding="utf8")) if j.is_file() else {}
    except (OSError, ValueError):
        return {}


def _salvar_meta(p: Path, meta):
    j = Path(str(p) + ".json")
    if j.is_file():
        j.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf8")


def _md5(p: Path):
    return hashlib.md5(p.read_bytes()).hexdigest()[:12]


def _dhash(p: Path):
    from PIL import Image
    im = Image.open(p).convert("L").resize((9, 8))
    px = list(im.getdata())
    return sum(1 << i for i in range(64) if px[(i // 8) * 9 + i % 8] > px[(i // 8) * 9 + i % 8 + 1])


def usos_por_slide(deck):
    """{chave_da_imagem: [slides]} contando qualquer campo do slide que cite a chave."""
    imgs = deck.get("imagens") or {}
    uso = {k: [] for k in imgs}

    def varrer(v, n):
        if isinstance(v, str):
            if v in imgs:
                uso[v].append(n)
            for m in re.findall(r"\{\{img:([^}]+)\}\}", v):
                if m in imgs:
                    uso[m].append(n)
        elif isinstance(v, dict):
            for x in v.values():
                varrer(x, n)
        elif isinstance(v, list):
            for x in v:
                varrer(x, n)
    for n, s in enumerate(deck.get("slides") or [], 1):
        varrer(s, n)
    return {k: sorted(set(v)) for k, v in uso.items()}


def imagens_repetidas(deck, proj: Path, limite=2):
    """Agrupa as imagens pela origem (URL ou arquivo bruto) e pelo desenho (dhash). Erro se um grupo aparece em mais de `limite` slides."""
    imgs = deck.get("imagens") or {}
    uso = usos_por_slide(deck)
    chaves, origem, dh = list(imgs), {}, {}
    for k in chaves:
        p = proj / imgs[k].get("arquivo", "")
        if not p.is_file():
            continue
        m = _meta(p)
        origem[k] = m.get("url_arquivo") or m.get("url_pagina") or m.get("origem_local") or m.get("arquivo_local") or ""
        try:
            dh[k] = _dhash(p)
        except Exception:  # noqa: BLE001
            pass
    pai = {k: k for k in chaves}

    def raiz(k):
        while pai[k] != k:
            pai[k] = pai[pai[k]]
            k = pai[k]
        return k
    for i, a in enumerate(chaves):
        for b in chaves[i + 1:]:
            mesma = origem.get(a) and origem.get(a) == origem.get(b)
            if not mesma and a in dh and b in dh:
                mesma = bin(dh[a] ^ dh[b]).count("1") <= 8
            if mesma:
                pai[raiz(a)] = raiz(b)
    grupos = {}
    for k in chaves:
        grupos.setdefault(raiz(k), []).append(k)
    out = []
    for ks in grupos.values():
        sl = sorted({n for k in ks for n in uso.get(k, [])})
        if len(sl) > limite:
            nomes = ", ".join(f'"{k}"' for k in ks)
            out.append(f"a mesma obra ({nomes}) está em {len(sl)} slides ({', '.join(map(str, sl))}), o limite é {limite}. "
                       "Nos outros use número, gráfico, diagrama, arte do tema ou outra obra.")
    return out


def _tesseract():
    for c in (shutil.which("tesseract"), r"C:\Program Files\Tesseract-OCR\tesseract.exe", r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"):
        if c and Path(c).is_file():
            return c
    return None


def _palavras_ocr(p: Path, exe):
    from PIL import Image
    im = Image.open(p).convert("L")
    im.thumbnail((1600, 1600))
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "o.png"
        im.save(f)
        r = subprocess.run([exe, str(f), "-", "--psm", "11", "tsv"], capture_output=True, text=True, timeout=60)
    n = 0
    for ln in r.stdout.splitlines()[1:]:
        c = ln.split("\t")
        if len(c) < 12:
            continue
        try:
            conf = float(c[10])
        except ValueError:
            continue
        letras = re.sub(r"[^A-Za-zÀ-ú]", "", c[11])
        if conf >= 70 and len(letras) >= 3 and re.search(r"[aeiouAEIOUà-úÀ-Ú]", letras) and len(set(letras.lower())) > 1:
            n += 1
    return n


def _indice_figura(p: Path, T=24):
    """Fração de blocos com fundo liso e traços finos de alto contraste. Telas, figuras e diagramas passam de 0,12. Fotos ficam abaixo de 0,10."""
    import numpy as np
    from PIL import Image
    im = Image.open(p).convert("L")
    w, h = im.size
    k = 1000 / max(w, h)
    a = np.asarray(im.resize((max(1, int(w * k)), max(1, int(h * k)))), dtype=np.int16)
    H, W = a.shape
    n = tx = 0
    for y in range(0, H - T + 1, T):
        for x in range(0, W - T + 1, T):
            t = a[y:y + T, x:x + T]
            med = np.median(t)
            n += 1
            if (np.abs(t - med) < 14).mean() > 0.55 and 0.04 < (np.abs(t - med) > 70).mean() < 0.4 and (np.abs(np.diff(t, axis=1)) > 60).mean() > 0.04:
                tx += 1
    return tx / max(n, 1)


def texto_em_imagem(deck, proj: Path):
    """(erros, metodo). Com Tesseract instalado lê as palavras. Sem ele, reconhece telas, figuras e diagramas com texto."""
    imgs = deck.get("imagens") or {}
    uso = usos_por_slide(deck)
    exe = _tesseract()
    metodo = "ocr" if exe else "heuristica"
    erros = []
    alvo = [(k, im, proj / im.get("arquivo", "")) for k, im in imgs.items()
            if uso.get(k) and not im.get("documento") and not im.get("texto_ok") and (proj / im.get("arquivo", "")).is_file()]

    def medir(item):
        k, im, p = item
        meta = _meta(p)
        h = _md5(p)
        cache = meta.get("texto_na_imagem") or {}
        if cache.get("md5") != h or cache.get("metodo") != metodo:
            try:
                cache = {"md5": h, "metodo": metodo}
                if exe:
                    cache["palavras"] = _palavras_ocr(p, exe)
                cache["indice_figura"] = round(_indice_figura(p), 3)
            except Exception as e:  # noqa: BLE001
                cache = {"md5": h, "metodo": "falhou", "erro": str(e)[:80]}
            meta["texto_na_imagem"] = cache
            _salvar_meta(p, meta)
        return cache
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(4) as ex:
        caches = list(ex.map(medir, alvo))
    for (k, im, p), cache in zip(alvo, caches):
        pal, fig = cache.get("palavras", 0), cache.get("indice_figura", 0)
        if pal >= 4 or fig >= 0.12:
            o_que = f"{pal} palavras" if pal >= 4 else "tela, figura ou diagrama"
            erros.append(f'imagem "{k}" (slide {", ".join(map(str, uso[k]))}): texto dentro da imagem ({o_que}).')
    if erros:
        erros.append('Texto em imagem fica miúdo e não se mede. Refaça como "grafico", "diagrama", "tabela" ou texto do slide, '
                     'ou troque a imagem. Se a página do documento é o assunto, marque "documento": true nela.')
    return erros, metodo


_PESSOA = re.compile(r"\b(retrato de [A-ZÀ-Ú]|portrait of|portrait|photograph of [A-Z]|retratad[oa]|busto|bust of|head and shoulders|"
                     r"self-portrait|autorretrato|pessoa|homem|mulher|operador[a]?|estudante|criança|menin[oa]|senhor[a]?|"
                     r"mr\.|mrs\.|miss [A-Z]|at (?:his|her|a) desk|at desk|seated|sentad[oa]|de perfil)", re.I)


def marcar_pessoas(deck, proj: Path):
    """Marca "pessoa": true nas imagens que parecem retrato (metadados ou rosto detectado pelo OpenCV, se houver). Não sobrescreve false."""
    imgs = deck.get("imagens") or {}
    cascata = None
    try:
        import cv2  # opcional: sem OpenCV ficam só os metadados
        xml = Path(cv2.data.haarcascades) / "haarcascade_frontalface_default.xml"
        if xml.is_file():
            cascata = cv2.CascadeClassifier(str(xml))
            if cascata.empty():
                cascata = None
    except Exception:  # noqa: BLE001
        cascata = None
    marcadas = []
    for k, im in imgs.items():
        if "pessoa" in im:
            continue
        p = proj / im.get("arquivo", "")
        meta = _meta(p) if p.is_file() else {}
        texto = " ".join(str(x) for x in (k, im.get("alt"), im.get("legenda"), meta.get("titulo")) if x)
        sim = bool(_PESSOA.search(texto.replace("-", " ").replace("_", " ")))
        if not sim and cascata is not None and p.is_file():
            cache = meta.get("rosto") or {}
            h = _md5(p)
            if cache.get("md5") != h:
                try:
                    from PIL import Image
                    import numpy as np
                    g = Image.open(p).convert("L")
                    g.thumbnail((900, 900))
                    a = np.asarray(g)
                    fs = cascata.detectMultiScale(a, scaleFactor=1.1, minNeighbors=6, minSize=(int(min(a.shape) * 0.12),) * 2)
                    cache = {"md5": h, "rostos": int(len(fs))}
                except Exception:  # noqa: BLE001
                    cache = {"md5": h, "rostos": 0}
                meta["rosto"] = cache
                _salvar_meta(p, meta)
            sim = cache.get("rostos", 0) >= 1
        if sim:
            im["pessoa"] = True
            marcadas.append(k)
    return marcadas
