#!/usr/bin/env python3
"""Busca, baixa e trata imagens REAIS com proveniência registrada.

Acervos suportados (todos abertos, sem chave de API):
  loc      Library of Congress (fotografias, gravuras, mapas, cartazes). Leia o campo de direitos.
  met      The Metropolitan Museum of Art, Open Access (somente objetos marcados como domínio público).
  nasa     NASA Image and Video Library (imagens da NASA são, em regra, de domínio público nos EUA).
  ia       Internet Archive (livros de pranchas, atlas). Confirme o domínio público.
  commons  Wikimedia Commons (licença por arquivo, CC ou domínio público). Pode limitar requisições (429).
  openverse Openverse (índice de imagens abertas de Flickr, museus e Commons). A busca só lista CC0, PDM, CC BY e CC BY-SA.

Uso:
  python3 scripts/imagens.py buscar loc "independence hall" [--n 12]
  python3 scripts/imagens.py buscar met "engraving constitution" [--n 12]
  python3 scripts/imagens.py baixar loc https://www.loc.gov/item/2024692639/ --saida PROJETO/assets/brutas
  python3 scripts/imagens.py baixar loc 09021562 --pagina 11 --saida PROJETO/assets/brutas   (página de um livro)
  python3 scripts/imagens.py baixar met 712017 --saida PROJETO/assets/brutas
  python3 scripts/imagens.py baixar nasa PIA13045 --saida PROJETO/assets/brutas
  python3 scripts/imagens.py baixar commons "File:Nome do arquivo.jpg" --saida PROJETO/assets/brutas
  python3 scripts/imagens.py buscar openverse "taipa de pilão"
  python3 scripts/imagens.py baixar openverse ID --saida PROJETO/assets/brutas [--aceitar-nc]
  python3 scripts/imagens.py baixar url https://exemplo.org/foto.jpg --saida ... --licenca "CC BY 4.0" --autor "..." --origem URL
  python3 scripts/imagens.py baixar local minha-foto.jpg --saida ... --licenca "cedida pela autora" --autor "..." --titulo "..."
  python3 scripts/imagens.py tratar BRUTA.jpg PROJETO/assets/nome.webp --proporcao 16:9 [--foco 0.5,0.4] [--max 2200]
          [--duotom "#1C2632,#F2EBDD"] [--cinza] [--cortar 0.05,0.08,0.95,0.92]
  python3 scripts/imagens.py olhar PROJETO/assets/brutas   (gera uma folha com todas as candidatas para você OLHAR)

Cada imagem baixada ganha IMAGEM.json com fonte, página, arquivo, autor, data, licença,
direitos, data de acesso, transformações e classe_licenca, que vale para todos os acervos:
  livre     domínio público, CC0, PDM, sem restrições conhecidas
  credito   CC BY, CC BY-SA, cedida ou autorizada (o crédito é obrigatório)
  recusada  NC, ND, todos os direitos reservados ou licença desconhecida (VERIFICAR)
baixar recusa a classe "recusada" e apaga o arquivo. Licença desconhecida: leia a página do item e baixe
de novo com --licenca "TEXTO" (fica registrado que foi declarada por você). --aceitar-nc libera NC só
para aula sem fins comerciais e registra isso no .json. Sem esse arquivo a imagem não entra no deck.
Baixe uma imagem por vez (museus respondem 403 a downloads paralelos).
"""
from __future__ import annotations

import argparse
import json
import re
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36 slides-impecaveis"


def get(url, tentativas=4, pausa=2.0, timeout=60, ua=UA):
    ult = None
    for i in range(tentativas):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": ua})
            return urllib.request.urlopen(req, timeout=timeout).read()
        except Exception as e:  # noqa: BLE001
            ult = e
            if "429" in str(e):
                time.sleep(pausa * (i + 2) * 3)
            else:
                time.sleep(pausa * (i + 1))
    raise SystemExit(f"ERRO download falhou depois de {tentativas} tentativas: {url} ({ult})")


def get_json(url, **kw):
    return json.loads(get(url, **kw))


OPCOES = {"aceitar_nc": False, "licenca": None}  # preenchido por main() a partir de baixar


def nc(texto):
    t = " " + str(texto or "").lower().replace("_", "-") + " "
    return bool(re.search(r"[-\s/]nc[-\s/]|noncommercial|non-commercial|não comercial|nao comercial", t))


def classe_licenca(texto):
    """livre, credito ou recusada, a partir do texto da licença (vale para todos os acervos)."""
    t = " " + str(texto or "").lower().replace("_", "-") + " "
    if not t.strip() or "verificar" in t or t.strip() in ("?", "none"):
        return "recusada"
    if nc(t) or re.search(r"[-\s/]nd[-\s/]|noderiv|no deriv|sem deriva|all rights reserved|todos os direitos reservados", t):
        return "recusada"
    if re.search(r"public domain|publicdomain|domínio público|dominio publico|cc0|\bpdm\b|no known (copyright )?restrictions|sem restrições conhecidas", t):
        return "livre"
    if re.search(r"cc[- ]by|by-sa|creativecommons\.org/licenses/by|attribution|atribuição|autoriza|permit|permiss|cedid|fornecid|própri|propri|licença d[oa] autor|gfdl|copyrighted free use", t):
        return "credito"
    return "recusada"


def gravar_proveniencia(img: Path, dados: dict):
    if OPCOES["licenca"]:
        dados = {**dados, "licenca_do_acervo": dados.get("licenca"), "licenca": OPCOES["licenca"], "licenca_declarada_por": "pessoa (--licenca)"}
    lic = dados.get("licenca")
    classe = classe_licenca(lic)
    if classe == "recusada" and nc(lic) and OPCOES["aceitar_nc"] and classe_licenca(re.sub(r"(?i)-?nc\b|noncommercial|non-commercial", "", str(lic))) != "recusada":
        classe = "credito"
        dados["nao_comercial"] = True
        dados["aceite_nc"] = "licença não comercial aceita com --aceitar-nc, só para aula sem fins comerciais"
    if classe == "recusada":
        img.unlink(missing_ok=True)
        if nc(lic):
            motivo = "é não comercial (NC). Para aula sem fins comerciais, baixe de novo com --aceitar-nc"
        elif str(lic or "").upper().startswith("VERIFICAR") or not lic:
            motivo = ("é desconhecida. Leia os direitos na página do item" + (f" ({dados.get('url_pagina')})" if dados.get("url_pagina") else "")
                      + ". Se for domínio público ou CC BY, baixe de novo com --licenca \"TEXTO\"")
        else:
            motivo = "não permite uso em slides (ND, todos os direitos reservados ou termo não reconhecido). Procure outra imagem"
        raise SystemExit(f"RECUSADA a licença \"{lic}\" {motivo}. Direitos informados pelo acervo: {str(dados.get('direitos') or '(nenhum)')[:160]}")
    dados = {**dados, "classe_licenca": classe, "arquivo_local": img.name, "acesso_em": datetime.now(timezone.utc).strftime("%Y-%m-%d")}
    dados.setdefault("transformacoes", [])
    Path(str(img) + ".json").write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf8")


# ---------------------------------------------------------------- buscar

def buscar_loc(q, n):
    url = "https://www.loc.gov/search/?" + urllib.parse.urlencode({"q": q, "fa": "online-format:image", "fo": "json", "c": n})
    d = get_json(url)
    for r in d.get("results", [])[:n]:
        img = (r.get("image_url") or [""])[-1]
        dim = re.search(r"#h=(\d+)&w=(\d+)", img or "")
        print(f"  {r.get('id')} | {(r.get('title') or '')[:70]} | {r.get('date') or ''} | prévia {dim.group(2) + 'x' + dim.group(1) if dim else '?'}")


def buscar_met(q, n):
    ids = None
    for base in ("https://collectionapi.metmuseum.org/public/collection/v1.1/search?",
                 "https://collectionapi.metmuseum.org/public/collection/v1/search?"):
        try:
            ids = get_json(base + urllib.parse.urlencode({"q": q, "hasImages": "true", "isPublicDomain": "true"}), tentativas=2).get("objectIDs") or []
            break
        except SystemExit:
            continue
    if ids is None:
        print("  (busca do Met indisponível agora)")
        return
    achados = 0
    for oid in ids[: n * 3]:
        try:
            o = get_json(f"https://collectionapi.metmuseum.org/public/collection/v1/objects/{oid}", tentativas=2)
        except SystemExit:
            continue
        if not (o.get("isPublicDomain") and o.get("primaryImage")):
            continue
        print(f"  {oid} | {o.get('title', '')[:60]} | {(o.get('artistDisplayName') or '')[:30]} | {o.get('objectDate')} | {(o.get('medium') or '')[:30]}")
        achados += 1
        time.sleep(0.4)
        if achados >= n:
            break


def buscar_nasa(q, n):
    d = get_json("https://images-api.nasa.gov/search?" + urllib.parse.urlencode({"q": q, "media_type": "image"}))
    for it in d["collection"]["items"][:n]:
        m = it["data"][0]
        print(f"  {m.get('nasa_id')} | {m.get('title', '')[:70]} | {m.get('center')} | {str(m.get('date_created', ''))[:10]}")


def buscar_ia(q, n):
    d = get_json("https://archive.org/advancedsearch.php?" + urllib.parse.urlencode(
        {"q": q + " AND mediatype:(image OR texts)", "fl[]": ["identifier", "title", "date", "licenseurl"], "rows": n, "output": "json"}, doseq=True))
    for r in d["response"]["docs"]:
        print(f"  {r.get('identifier')} | {str(r.get('title'))[:70]} | {r.get('date', '')} | {r.get('licenseurl', '')}")


def buscar_commons(q, n):
    d = get_json("https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(
        {"action": "query", "format": "json", "generator": "search", "gsrsearch": q, "gsrnamespace": 6, "gsrlimit": n,
         "prop": "imageinfo", "iiprop": "url|size|extmetadata"}))
    for p in (d.get("query", {}).get("pages", {}) or {}).values():
        ii = (p.get("imageinfo") or [{}])[0]
        lic = ii.get("extmetadata", {}).get("LicenseShortName", {}).get("value", "?")
        print(f"  {p.get('title')} | {ii.get('width')}x{ii.get('height')} | {lic} ({classe_licenca(lic)})")


# Openverse: ideia e parâmetros adaptados de hugohe3/ppt-master (provider_openverse.py, MIT, (c) 2025-2026 Hugo He)
OPENVERSE = "https://api.openverse.org/v1/images/"


def licenca_openverse(it):
    lic, ver = (it.get("license") or "").lower(), it.get("license_version") or ""
    if lic == "cc0":
        return "CC0 " + ver
    if lic == "pdm":
        return "Public Domain Mark " + ver
    return f"CC {lic.upper()} {ver}".strip()


def buscar_openverse(q, n):
    d = get_json(OPENVERSE + "?" + urllib.parse.urlencode({"q": q, "page_size": n, "license": "cc0,pdm,by,by-sa"}))
    for it in d.get("results", [])[:n]:
        lic = licenca_openverse(it)
        print(f"  {it.get('id')} | {(it.get('title') or '')[:55]} | {(it.get('creator') or '')[:25]} | {it.get('width')}x{it.get('height')} | {lic} ({classe_licenca(lic)}) | {it.get('source')}")


def baixar_openverse(oid, saida: Path):
    it = get_json(OPENVERSE + urllib.parse.quote(oid) + "/")
    lic = licenca_openverse(it)
    url = it.get("url")
    if not url:
        raise SystemExit("ERRO o registro não traz o endereço do arquivo")
    ext = Path(urllib.parse.urlparse(url).path).suffix.lower() or ".jpg"
    dst = saida / f"openverse_{nome_seguro(oid)[:40]}{ext if ext in ('.jpg', '.jpeg', '.png', '.webp', '.tif', '.tiff') else '.jpg'}"
    if urllib.parse.urlparse(url).netloc == "upload.wikimedia.org":
        # a Commons limita originais e larguras fora da lista padrão (HTTP 429): tenta as larguras padrão, da maior para a menor
        base = "https://commons.wikimedia.org/wiki/Special:Redirect/file/" + urllib.parse.quote(urllib.parse.unquote(url.rsplit("/", 1)[-1]))
        for larg in (1920, 1280, 960):
            try:
                dst.write_bytes(get(f"{base}?width={larg}", tentativas=2))
                url = f"{base}?width={larg}"
                break
            except SystemExit as e:
                print(f"   {larg} px recusado pela Commons ({str(e)[-60:]}), tentando menor")
        else:
            raise SystemExit("ERRO a Commons recusou todas as larguras. Espere alguns minutos e tente de novo.")
        if larg < 1920:
            print(f"AVISO baixada com {larg} px de largura (a Commons limitou). Para tela cheia, tente de novo mais tarde.")
    else:
        dst.write_bytes(get(url))
    autor = it.get("creator") or ""
    gravar_proveniencia(dst, {
        "fonte": f"Openverse ({it.get('source') or it.get('provider')})", "titulo": it.get("title"), "autor": autor,
        "url_pagina": it.get("foreign_landing_url"), "url_arquivo": url, "licenca": lic, "url_licenca": it.get("license_url"),
        "direitos": it.get("attribution"),
        "credito_sugerido": f"{autor + ', ' if autor else ''}{it.get('title')}. {lic}, via {it.get('source') or 'Openverse'}.",
    })
    print(f"salvo {dst} ({dst.stat().st_size // 1024} KB) | {lic} | {autor[:60]}")


# ---------------------------------------------------------------- baixar

def nome_seguro(s):
    return re.sub(r"[^\w.-]+", "_", s)[:80]


def baixar_loc(ref, saida: Path, pagina=None, volume=1):
    url = ref if ref.startswith("http") else f"https://www.loc.gov/item/{ref}/"
    d = get_json(url.rstrip("/") + "/?fo=json")
    if pagina:  # livros e álbuns: uma página específica, em resolução real pelo serviço IIIF
        import io
        from PIL import Image
        res = d.get("resources", [])[volume - 1]
        grupo = res["files"][pagina - 1]
        jp = [f for f in grupo if f.get("mimetype") == "image/jpeg"]
        u = re.sub(r"/full/pct:[\d.]+/", "/full/pct:100/", jp[-1]["url"])
        im = Image.open(io.BytesIO(get(u, timeout=180))).convert("RGB")
        if max(im.size) > 3200:
            im.thumbnail((3200, 3200), Image.LANCZOS)
        it = d.get("item", {})
        dst = saida / f"loc_{nome_seguro(url.rstrip('/').split('/')[-1])}_v{volume}p{pagina}.jpg"
        im.save(dst, quality=90)
        direitos = it.get("rights_advisory") or it.get("rights_information") or "(não informado)"
        if isinstance(direitos, list):
            direitos = " ".join(direitos)
        gravar_proveniencia(dst, {"fonte": "Library of Congress", "titulo": it.get("title"), "data": it.get("date"), "url_pagina": url,
                                  "url_arquivo": u, "pagina": pagina, "volume": volume, "direitos": direitos,
                                  "licenca": "VERIFICAR (leia 'direitos'; obras anteriores a 1900 costumam ser de domínio público)",
                                  "credito_sugerido": f"{it.get('title')}. Library of Congress."})
        print(f"salvo {dst} {im.size[0]}x{im.size[1]}  direitos: {str(direitos)[:120]}")
        return
    it = d.get("item", {})
    direitos = it.get("rights_advisory") or it.get("rights_information") or "(não informado)"
    if isinstance(direitos, list):
        direitos = " ".join(direitos)
    melhor = None
    tiff = None
    for res in d.get("resources", []):
        for grupo in res.get("files", []):
            for f in grupo:
                if f.get("mimetype") == "image/jpeg":
                    w = f.get("width") or 0
                    if melhor is None or w > (melhor.get("width") or 0):
                        melhor = f
                if f.get("mimetype") == "image/tiff" and (tiff is None or (f.get("size") or 0) < (tiff.get("size") or 1e12)):
                    tiff = f
    if not melhor and not tiff:
        raise SystemExit("ERRO nenhuma imagem no registro do item")
    dst = saida / f"loc_{nome_seguro(url.rstrip('/').split('/')[-1])}.jpg"
    if (not melhor or (melhor.get("width") or 0) < 1800) and tiff and (tiff.get("size") or 0) < 150e6:
        # o JPEG de serviço é pequeno; baixa a matriz TIFF e converte (resolução real, sem ampliar)
        import io
        from PIL import Image
        Image.MAX_IMAGE_PIXELS = None
        im = Image.open(io.BytesIO(get(tiff["url"], timeout=300)))
        im = im.convert("RGB")
        if max(im.size) > 3200:
            im.thumbnail((3200, 3200), Image.LANCZOS)
        im.save(dst, quality=90)
        melhor = {"url": tiff["url"], "width": im.size[0], "height": im.size[1]}
    else:
        dst.write_bytes(get(melhor["url"]))
    autor = ", ".join(it.get("contributor_names") or it.get("creators") or []) if isinstance(it.get("contributor_names") or it.get("creators"), list) else ""
    gravar_proveniencia(dst, {
        "fonte": "Library of Congress", "titulo": it.get("title"), "autor": autor, "data": it.get("date"),
        "url_pagina": url, "url_arquivo": melhor["url"], "direitos": direitos,
        "licenca": "sem restrições conhecidas" if "no known restrictions" in direitos.lower() else "VERIFICAR (leia 'direitos')",
        "credito_sugerido": f"{it.get('title')}. Library of Congress.",
    })
    print(f"salvo {dst} ({dst.stat().st_size // 1024} KB, {melhor.get('width')}x{melhor.get('height')})\n  direitos: {direitos[:160]}")


def baixar_met(oid, saida: Path):
    o = get_json(f"https://collectionapi.metmuseum.org/public/collection/v1/objects/{oid}")
    if not o.get("isPublicDomain"):
        raise SystemExit(f"ERRO objeto {oid} NÃO é domínio público. Não use.")
    dst = saida / f"met_{oid}.jpg"
    dst.write_bytes(get(o["primaryImage"]))
    artista = o.get("artistDisplayName") or ""
    gravar_proveniencia(dst, {
        "fonte": "The Metropolitan Museum of Art (Open Access)", "titulo": o.get("title"), "autor": artista,
        "data": o.get("objectDate"), "tecnica": o.get("medium"), "url_pagina": o.get("objectURL"), "url_arquivo": o["primaryImage"],
        "licenca": "CC0 (domínio público)", "direitos": o.get("creditLine"),
        "credito_sugerido": f"{(artista + ', ') if artista else ''}{o.get('title')}, {o.get('objectDate')}. The Met, domínio público.",
    })
    print(f"salvo {dst} ({dst.stat().st_size // 1024} KB) | {o.get('title')} | {artista} | {o.get('objectDate')}")


def baixar_nasa(nid, saida: Path):
    meta = get_json("https://images-api.nasa.gov/search?" + urllib.parse.urlencode({"nasa_id": nid}))
    m = meta["collection"]["items"][0]["data"][0]
    arquivos = get_json(f"https://images-assets.nasa.gov/image/{nid}/collection.json")
    pref = [a for a in arquivos if a.endswith("~large.jpg")] or [a for a in arquivos if a.endswith("~orig.jpg")] or [a for a in arquivos if a.lower().endswith(".jpg")]
    url = pref[0].replace("http://", "https://")
    dst = saida / f"nasa_{nome_seguro(nid)}.jpg"
    dst.write_bytes(get(url))
    gravar_proveniencia(dst, {
        "fonte": "NASA Image and Video Library", "titulo": m.get("title"), "autor": m.get("photographer") or m.get("center"),
        "data": str(m.get("date_created", ""))[:10], "url_pagina": f"https://images.nasa.gov/details/{nid}", "url_arquivo": url,
        "licenca": "domínio público (imagens da NASA, salvo indicação em contrário)", "direitos": "Ver https://www.nasa.gov/nasa-brand-center/images-and-media/",
        "credito_sugerido": f"{m.get('title')}. NASA.",
    })
    print(f"salvo {dst} ({dst.stat().st_size // 1024} KB) | {m.get('title')}")


def baixar_commons(titulo, saida: Path):
    if not titulo.startswith("File:"):
        titulo = "File:" + titulo
    d = get_json("https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode(
        {"action": "query", "format": "json", "titles": titulo, "prop": "imageinfo", "iiprop": "url|extmetadata|size", "iiurlwidth": 1920}))
    p = next(iter(d["query"]["pages"].values()))
    ii = p["imageinfo"][0]
    em = ii.get("extmetadata", {})
    lic = em.get("LicenseShortName", {}).get("value", "?")
    autor = re.sub("<[^>]+>", "", em.get("Artist", {}).get("value", ""))
    url = ii.get("thumburl") or ii["url"]
    dst = saida / f"commons_{nome_seguro(titulo[5:])}"
    if not dst.suffix:
        dst = dst.with_suffix(".jpg")
    dst.write_bytes(get(url))
    gravar_proveniencia(dst, {
        "fonte": "Wikimedia Commons", "titulo": titulo[5:], "autor": autor, "url_pagina": ii.get("descriptionurl"),
        "url_arquivo": url, "licenca": lic, "direitos": re.sub("<[^>]+>", "", em.get("UsageTerms", {}).get("value", "")),
        "credito_sugerido": f"{autor}, {titulo[5:]}, Wikimedia Commons, {lic}.",
    })
    print(f"salvo {dst} ({dst.stat().st_size // 1024} KB) | licença {lic} | {autor[:60]}")


def baixar_ia(ref, saida: Path, arquivo=None):
    meta = get_json("https://archive.org/metadata/" + ref)
    md = meta.get("metadata", {})
    if not arquivo:
        for f in meta.get("files", []):
            if f["name"].lower().endswith((".jpg", ".jpeg", ".png")) and "thumb" not in f["name"]:
                print("  ", f["name"], int(f.get("size", 0)) // 1024, "KB")
        print("Escolha um arquivo e rode de novo com --arquivo NOME")
        return
    dst = saida / ("ia_" + nome_seguro(arquivo))
    dst.write_bytes(get(f"https://archive.org/download/{ref}/{urllib.parse.quote(arquivo)}"))
    gravar_proveniencia(dst, {
        "fonte": "Internet Archive", "titulo": md.get("title"), "autor": md.get("creator"), "data": md.get("date"),
        "url_pagina": f"https://archive.org/details/{ref}", "url_arquivo": f"https://archive.org/download/{ref}/{arquivo}",
        "licenca": md.get("licenseurl") or "VERIFICAR domínio público", "direitos": md.get("rights") or md.get("possible-copyright-status"),
        "credito_sugerido": f"{md.get('creator') or ''}, {md.get('title')}. Internet Archive.",
    })
    print(f"salvo {dst}")


def baixar_url(url, saida: Path, licenca, autor, pagina, titulo):
    if not licenca:
        raise SystemExit("ERRO informe --licenca (e confira na página de origem). Sem licença a imagem não entra.")
    dst = saida / ("web_" + nome_seguro(urllib.parse.urlparse(url).path.split("/")[-1] or "imagem.jpg"))
    dst.write_bytes(get(url))
    gravar_proveniencia(dst, {"fonte": urllib.parse.urlparse(url).netloc, "titulo": titulo, "autor": autor, "url_pagina": pagina or url,
                              "url_arquivo": url, "licenca": licenca, "credito_sugerido": f"{autor}, {titulo}. {licenca}."})
    print(f"salvo {dst}")


def baixar_local(caminho, saida: Path, licenca, autor, titulo):
    """Imagem que a pessoa forneceu (foto própria, figura de artigo dela, captura autorizada)."""
    import shutil
    if not licenca:
        raise SystemExit('ERRO informe --licenca (por exemplo "foto da autora, uso autorizado"). Sem licença a imagem não entra.')
    src = Path(caminho)
    if not src.is_file():
        raise SystemExit(f"ERRO arquivo não encontrado: {src}")
    dst = saida / ("local_" + nome_seguro(src.name))
    shutil.copyfile(src, dst)
    gravar_proveniencia(dst, {"fonte": "fornecida pela pessoa", "titulo": titulo, "autor": autor, "arquivo_original": src.name,
                              "licenca": licenca, "credito_sugerido": ", ".join(x for x in (autor, titulo) if x) + f". {licenca}."})
    print(f"salvo {dst}")


# ---------------------------------------------------------------- tratar

def tratar(origem, destino, proporcao=None, foco="0.5,0.5", maximo=2200, qualidade=84, duotom=None, cinza=False, cortar=None):
    from PIL import Image, ImageOps

    src = Path(origem)
    im = Image.open(src)
    im = ImageOps.exif_transpose(im).convert("RGB")
    ops = []
    if cortar:
        x0, y0, x1, y1 = [float(v) for v in cortar.split(",")]
        W, H = im.size
        if max(x0, y0, x1, y1) <= 1.0:
            x0, x1, y0, y1 = x0 * W, x1 * W, y0 * H, y1 * H
        im = im.crop((int(x0), int(y0), int(x1), int(y1)))
        ops.append(f"recorte {cortar}")
    if proporcao:
        a, b = [float(v) for v in proporcao.split(":")]
        fx, fy = [float(v) for v in foco.split(",")]
        W, H = im.size
        alvo = a / b
        if W / H > alvo:
            nw = int(H * alvo)
            x = int(min(max(fx * W - nw / 2, 0), W - nw))
            im = im.crop((x, 0, x + nw, H))
        else:
            nh = int(W / alvo)
            y = int(min(max(fy * H - nh / 2, 0), H - nh))
            im = im.crop((0, y, W, y + nh))
        ops.append(f"proporção {proporcao} foco {foco}")
    if max(im.size) > maximo:
        im.thumbnail((maximo, maximo), Image.LANCZOS)
        ops.append(f"redução para lado maior {maximo}px")
    if cinza or duotom:
        g = ImageOps.grayscale(im)
        if duotom:
            esc, cla = [c.strip() for c in duotom.split(",")]
            im = ImageOps.colorize(ImageOps.autocontrast(g, cutoff=1), black=esc, white=cla)
            ops.append(f"duotom {duotom}")
        else:
            im = g.convert("RGB")
            ops.append("tons de cinza")
    dst = Path(destino)
    dst.parent.mkdir(parents=True, exist_ok=True)
    im.save(dst, quality=qualidade, method=6) if dst.suffix.lower() == ".webp" else im.save(dst, quality=qualidade)
    prov = {}
    pj = Path(str(src) + ".json")
    if pj.exists():
        prov = json.loads(pj.read_text(encoding="utf8"))
    prov.setdefault("transformacoes", [])
    prov["transformacoes"] += ops + [f"salvo como {dst.suffix[1:]} q{qualidade}, {im.size[0]}x{im.size[1]}px"]
    prov["origem_local"] = src.name
    prov["largura"], prov["altura"] = im.size
    Path(str(dst) + ".json").write_text(json.dumps(prov, ensure_ascii=False, indent=2), encoding="utf8")
    aviso = ""
    if im.size[0] < 1600:
        aviso = "  AVISO imagem com menos de 1600 px de largura: serve para painel, não para tela cheia."
    print(f"salvo {dst} {im.size[0]}x{im.size[1]} ({dst.stat().st_size // 1024} KB){aviso}")


def olhar(pasta, saida=None):
    """Folha de contato das imagens brutas, para escolher com os olhos."""
    from PIL import Image, ImageDraw

    fs = [f for f in sorted(Path(pasta).iterdir()) if f.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp")]
    if not fs:
        raise SystemExit("nenhuma imagem na pasta")
    tw, th, cols = 480, 360, 4
    rows = (len(fs) + cols - 1) // cols
    S = Image.new("RGB", (cols * (tw + 12) + 12, rows * (th + 52) + 12), (24, 24, 24))
    d = ImageDraw.Draw(S)
    for i, f in enumerate(fs):
        im = Image.open(f).convert("RGB")
        w, h = im.size
        im.thumbnail((tw, th))
        x = 12 + (i % cols) * (tw + 12)
        y = 12 + (i // cols) * (th + 52)
        S.paste(im, (x, y))
        d.text((x, y + th + 6), f"{f.name[:52]}  {w}x{h}", fill=(230, 230, 230))
    out = saida or str(Path(pasta) / "_candidatas.jpg")
    S.save(out, quality=85)
    print("folha salva em", out, "  ABRA e OLHE antes de escolher.")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("buscar")
    b.add_argument("acervo", choices=["loc", "met", "nasa", "ia", "commons", "openverse"])
    b.add_argument("termos")
    b.add_argument("--n", type=int, default=12)
    g = sub.add_parser("baixar")
    g.add_argument("acervo", choices=["loc", "met", "nasa", "ia", "commons", "openverse", "url", "local"])
    g.add_argument("ref")
    g.add_argument("--saida", required=True)
    g.add_argument("--arquivo")
    g.add_argument("--licenca", help="url e local: obrigatória. Nos acervos: licença lida por você na página do item")
    g.add_argument("--aceitar-nc", action="store_true", help="aceita licença não comercial (só aula sem fins comerciais)")
    g.add_argument("--autor", default="")
    g.add_argument("--origem", help="url: página onde a imagem e a licença aparecem")
    g.add_argument("--titulo", default="")
    g.add_argument("--pagina", type=int, help="loc: página de um livro ou álbum (1 = primeira)")
    g.add_argument("--volume", type=int, default=1, help="loc: volume do livro (padrão 1)")
    t = sub.add_parser("tratar")
    t.add_argument("origem")
    t.add_argument("destino")
    t.add_argument("--proporcao")
    t.add_argument("--foco", default="0.5,0.5")
    t.add_argument("--max", type=int, default=2200)
    t.add_argument("--qualidade", type=int, default=84)
    t.add_argument("--duotom")
    t.add_argument("--cinza", action="store_true")
    t.add_argument("--cortar")
    o = sub.add_parser("olhar")
    o.add_argument("pasta")
    o.add_argument("--saida")
    a = ap.parse_args()
    if a.cmd == "buscar":
        {"loc": buscar_loc, "met": buscar_met, "nasa": buscar_nasa, "ia": buscar_ia, "commons": buscar_commons,
         "openverse": buscar_openverse}[a.acervo](a.termos, a.n)
    elif a.cmd == "baixar":
        s = Path(a.saida)
        s.mkdir(parents=True, exist_ok=True)
        OPCOES.update(aceitar_nc=a.aceitar_nc, licenca=a.licenca if a.acervo not in ("url", "local") else None)
        if a.acervo == "loc":
            baixar_loc(a.ref, s, a.pagina, a.volume)
        elif a.acervo == "met":
            baixar_met(a.ref, s)
        elif a.acervo == "nasa":
            baixar_nasa(a.ref, s)
        elif a.acervo == "commons":
            baixar_commons(a.ref, s)
        elif a.acervo == "openverse":
            baixar_openverse(a.ref, s)
        elif a.acervo == "ia":
            baixar_ia(a.ref, s, a.arquivo)
        elif a.acervo == "local":
            baixar_local(a.ref, s, a.licenca, a.autor, a.titulo)
        else:
            baixar_url(a.ref, s, a.licenca, a.autor, a.origem, a.titulo)
    elif a.cmd == "tratar":
        tratar(a.origem, a.destino, a.proporcao, a.foco, a.max, a.qualidade, a.duotom, a.cinza, a.cortar)
    else:
        olhar(a.pasta, a.saida)


if __name__ == "__main__":
    main()
