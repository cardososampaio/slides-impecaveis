#!/usr/bin/env python3
"""Cria um projeto de apresentação.

    python3 scripts/novo_projeto.py PROJETO                          # esqueleto vazio para preencher
    python3 scripts/novo_projeto.py PROJETO --texto aula.docx        # extrai os slides separados por &&&
    python3 scripts/novo_projeto.py PROJETO --texto aula.md --verbatim   # texto intocável
    python3 scripts/novo_projeto.py PROJETO --exemplo                # cópia do exemplo federalismo, para estudar
    python3 scripts/novo_projeto.py PROJETO --perfil banca           # aula (padrão), congresso, banca, palestra, gestores

Estrutura criada:
  PROJETO/deck.json        conteúdo, contrato, seções, imagens e slides (o único arquivo que você edita)
  PROJETO/assets/brutas/   imagens baixadas, com proveniência
  PROJETO/assets/          imagens tratadas que entram no deck
  PROJETO/decisoes.md      registro das decisões da pessoa e das suas suposições
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

AQUI = Path(__file__).resolve().parent
SKILL = AQUI.parent
PERFIS = ("aula", "congresso", "banca", "palestra", "gestores")


def gravar_perfil(proj: Path, perfil: str):
    dj = proj / "deck.json"
    if not dj.is_file():
        return
    deck = json.loads(dj.read_text(encoding="utf8"))
    con = deck.setdefault("contrato", {})
    con["perfil"] = perfil
    con.pop("perfil_opcoes", None)
    dj.write_text(json.dumps(deck, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    if perfil in ("congresso", "banca"):
        print("perfil de pesquisa: siga references/14-apresentacao-de-pesquisa.md (títulos-ação, 1 slide por minuto, apêndice no fim).")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("projeto")
    ap.add_argument("--texto")
    ap.add_argument("--verbatim", action="store_true")
    ap.add_argument("--exemplo", action="store_true")
    ap.add_argument("--perfil", choices=PERFIS, help="perfil da apresentação (vai para contrato.perfil)")
    a = ap.parse_args()
    proj = Path(a.projeto)
    if proj.exists() and any(proj.iterdir()):
        print(f"ERRO {proj} já existe e não está vazio. Escolha outro nome.")
        return 1
    if a.exemplo:
        ex = SKILL / "exemplos" / "federalismo"
        shutil.copytree(ex, proj, ignore=shutil.ignore_patterns("dist", "verificacao", "revisao", "amostra-temas", "brutas"))
        if a.perfil:
            gravar_perfil(proj, a.perfil)
        print(f"cópia do exemplo em {proj}. Rode: python3 scripts/construir.py {proj}")
        return 0
    (proj / "assets" / "brutas").mkdir(parents=True)
    (proj / "decisoes.md").write_text(
        f"# Decisões e suposições\n\nRegistre aqui, com a porta (G1 a G8) e a data, cada decisão da pessoa e cada suposição sua.\n\n"
        f"- {date.today().isoformat()} · G0 · projeto criado.\n", encoding="utf8")
    if a.texto:
        cmd = [sys.executable, str(AQUI / "extrair_texto.py"), a.texto, str(proj)]
        if a.verbatim:
            cmd.append("--verbatim")
        r = subprocess.run(cmd)
        if r.returncode:
            return r.returncode
    else:
        shutil.copy(SKILL / "templates" / "projeto-modelo" / "deck.json", proj / "deck.json")
    if a.perfil:
        gravar_perfil(proj, a.perfil)
    print(f"projeto criado em {proj}.\nPróximos passos: scripts/teste_visao.py {proj} (uma vez), contrato e slides no deck.json"
          f" (tema \"auto\"), imagens com scripts/imagens.py e, por fim, scripts/fazer.py {proj}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
