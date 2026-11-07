#!/usr/bin/env python3
"""Teste de visão do avaliador. Descobre, em segundos e poucas centenas de tokens, se o modelo enxerga imagens.

    python3 scripts/teste_visao.py PROJETO                     # gera revisao/visao.png e mostra a pergunta
    python3 scripts/teste_visao.py PROJETO --resposta "4 BAMIRO"
    python3 scripts/teste_visao.py PROJETO --sem-visao         # o modelo não consegue abrir ou ver a imagem
    python3 scripts/teste_visao.py PROJETO --estado            # imprime com_visao, sem_visao ou nao_testado

A imagem tem círculos de três cores e dois quadrados com palavras inventadas. A pergunta é quantos círculos
vermelhos há e qual palavra está no quadrado azul. A resposta certa é sorteada na hora e guardada só como
hash lento (PBKDF2), então não dá para acertar por sorte, por leitura de arquivo nem por força bruta.
Um modelo que só lê texto erra ou declara --sem-visao, e a skill segue no modo automático, sem avaliador.
Uma tentativa por desafio. Para tentar de novo, gere outro.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import secrets
import sys
import time
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
ITER = 300_000
CONS, VOG = "BCDFGLMNPRSTVZ", "AEIOU"


def _palavra(r):
    return "".join(r.choice(CONS) + r.choice(VOG) for _ in range(3))


def _norm(t):
    t = "".join(ch for ch in str(t).upper() if ch.isalnum() or ch == " ")
    num = "".join(ch for ch in t if ch.isdigit())
    pal = "".join(ch for ch in t if ch.isalpha())
    return f"{num}-{pal}"


def _hash(resp, sal):
    return hashlib.pbkdf2_hmac("sha256", _norm(resp).encode(), bytes.fromhex(sal), ITER).hex()


def gerar(proj: Path):
    from PIL import Image, ImageDraw, ImageFont
    r = random.Random(secrets.randbits(64))
    k = r.randint(2, 6)
    alvo, isca = _palavra(r), _palavra(r)
    W, H = 1000, 560
    im = Image.new("RGB", (W, H), (244, 240, 230))
    d = ImageDraw.Draw(im)
    try:
        f = ImageFont.truetype(str(SKILL / "assets" / "fontes-ttf" / "AtkinsonHyperlegibleNext-700.ttf"), 58)
    except OSError:
        f = ImageFont.load_default()
    caixas = []

    def livre(x, y, w, h):
        return all(x + w < a or a + c < x or y + h < b or b + e < y for a, b, c, e in caixas)
    # dois quadrados com palavra, um azul e um vermelho (a isca), em posições sorteadas
    for cor, pal in (((40, 90, 170), alvo), ((180, 40, 40), isca)):
        for _ in range(200):
            x, y = r.randint(30, W - 330), r.randint(30, H - 150)
            if livre(x - 20, y - 20, 340, 150):
                break
        d.rectangle([x, y, x + 300, y + 110], outline=cor, width=8)
        d.text((x + 150, y + 55), pal, fill=(30, 30, 30), font=f, anchor="mm")
        caixas.append((x - 20, y - 20, 340, 150))
    # círculos: k vermelhos e algumas iscas azuis e verdes
    cores = [(196, 38, 38)] * k + [(40, 90, 170)] * r.randint(1, 4) + [(60, 140, 70)] * r.randint(1, 4)
    r.shuffle(cores)
    for c in cores:
        for _ in range(400):
            rad = r.randint(26, 40)
            x, y = r.randint(10, W - 2 * rad - 10), r.randint(10, H - 2 * rad - 10)
            if livre(x - 6, y - 6, 2 * rad + 12, 2 * rad + 12):
                break
        d.ellipse([x, y, x + 2 * rad, y + 2 * rad], fill=c)
        caixas.append((x - 6, y - 6, 2 * rad + 12, 2 * rad + 12))
    rev = proj / "revisao"
    rev.mkdir(parents=True, exist_ok=True)
    im.save(rev / "visao.png")
    sal = secrets.token_hex(16)
    (rev / "visao_desafio.json").write_text(json.dumps({"sal": sal, "hash": _hash(f"{k} {alvo}", sal), "criado": time.time(),
                                                        "usado": False}), encoding="utf8")
    print(f"Abra {rev / 'visao.png'} e responda: quantos círculos VERMELHOS há e qual palavra está no quadrado AZUL.\n"
          f'Depois rode: python3 scripts/teste_visao.py {proj} --resposta "NUMERO PALAVRA"\n'
          "Se você não consegue ver a imagem, não adivinhe. Rode com --sem-visao.")


def responder(proj: Path, resp):
    rev = proj / "revisao"
    dp = rev / "visao_desafio.json"
    if not dp.is_file():
        raise SystemExit("ERRO gere o desafio antes (sem --resposta).")
    des = json.loads(dp.read_text(encoding="utf8"))
    if des.get("usado"):
        raise SystemExit("ERRO este desafio já foi respondido. Gere outro.")
    ok = _hash(resp, des["sal"]) == des["hash"]
    des["usado"] = True
    dp.write_text(json.dumps(des), encoding="utf8")
    (rev / "visao.json").write_text(json.dumps({"visao": ok, "quando": time.time(), "desafio": des["hash"][:12]}), encoding="utf8")
    print("COM VISÃO. Siga a avaliação visual (agents/avaliador-humano.md)." if ok else
          "SEM VISÃO (resposta errada). Pare a avaliação visual. A skill segue no modo automático.")
    return 0 if ok else 3


def estado(proj: Path, horas=24):
    """com_visao, sem_visao ou nao_testado. O teste vale por 24 horas."""
    vp = proj / "revisao" / "visao.json"
    dp = proj / "revisao" / "visao_desafio.json"
    if not vp.is_file():
        return "nao_testado"
    try:
        v = json.loads(vp.read_text(encoding="utf8"))
        des = json.loads(dp.read_text(encoding="utf8")) if dp.is_file() else {}
    except ValueError:
        return "nao_testado"
    if time.time() - v.get("quando", 0) > horas * 3600:
        return "nao_testado"
    if v.get("visao") and des.get("hash", "")[:12] == v.get("desafio") and des.get("usado"):
        return "com_visao"
    return "sem_visao"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("projeto")
    ap.add_argument("--resposta")
    ap.add_argument("--sem-visao", action="store_true")
    ap.add_argument("--estado", action="store_true")
    a = ap.parse_args()
    proj = Path(a.projeto).resolve()
    if a.estado:
        print(estado(proj))
        return 0
    if a.sem_visao:
        (proj / "revisao").mkdir(parents=True, exist_ok=True)
        (proj / "revisao" / "visao.json").write_text(json.dumps({"visao": False, "quando": time.time(), "declarado": True}), encoding="utf8")
        print("SEM VISÃO registrado. A skill segue no modo automático, sem avaliador visual.")
        return 0
    if a.resposta is not None:
        return responder(proj, a.resposta)
    gerar(proj)
    return 0


if __name__ == "__main__":
    sys.exit(main())
