#!/usr/bin/env python3
"""TRAVA. Nada sai como versão final sem uma aprovação registrada para a versão atual do deck.

Três caminhos de aprovação, do mais comum ao mais exigente.
  automático   a verificação automática passou. É o padrão quando ninguém com visão vai olhar.
               Registro: python3 scripts/trava.py PROJETO --automatico  (o fazer.py faz isso sozinho)
  agente       um avaliador com visão comprovada (scripts/teste_visao.py) olhou as folhas de contato
               em contexto separado e listou os defeitos. Sem defeito, aprova. Com defeito, o deck é
               corrigido uma vez e sai pelo caminho automático, com a nota de que houve revisão.
               Registro: python3 scripts/trava.py PROJETO --registrar --tipo agente --avaliador "nome" \
                         --contexto-separado --defeitos revisao/defeitos.json
  pessoa       a própria pessoa aprovou pelo painel (scripts/revisao.py) ou na conversa.
               Registro: python3 scripts/trava.py PROJETO --registrar --tipo pessoa --avaliador "Nome" \
                         --declaracao "palavras literais" [--reprovar 3,7 --motivo "..."]

    python3 scripts/trava.py PROJETO      # diz LIBERADO ou TRAVADO e o motivo

No caminho da pessoa, libera somente quando TODAS as condições valem para a versão atual do deck:
  1. a verificação automática foi feita sobre esta versão (mesmo hash) e passou em tudo;
  2. existe revisao/parecer.json para esta versão;
  3. em cada slide o avaliador confirmou: fontes grandes e legíveis em todo o slide,
     tela inteira ocupada, nada cortado ou sem contraste, visual pertinente;
  4. as condições gerais (argumento nos títulos, variação, conteúdo real, movimento visto) foram confirmadas;
  5. o avaliador está identificado. Se for um agente, ele trabalhou em contexto separado
     de quem construiu o deck (sem isso o parecer é DEGRADADO e não libera);
  6. a evidência de cada slide é concreta (agente, ou pessoa pelo painel). Pelo menos 10 palavras,
     não repetida entre slides e com alguma palavra do título do slide ou do nome, legenda ou
     descrição da imagem;
  7. parecer e notas do diretor de arte (revisao/diretor.md) sem palavras vazias como "moderno",
     "limpo", "elegante", "profissional", "impactante", "bonito", "clean", "sofisticado".
     A declaração literal de uma pessoa fica como ela disse.

Qualquer mudança no deck muda o hash e trava de novo. O agente que constrói o deck NUNCA
preenche o parecer por conta própria e nunca trata silêncio como aprovação.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import medir  # noqa: E402


VAZIAS = re.compile(r"\b(modern[oa]s?|limp[oa]s?|elegantes?|profissiona(?:l|is)|impactantes?|bonit[oa]s?|clean|sofisticad[oa]s?)\b")
COMUNS = set("para como entre pela pelo pelos pelas mais cada onde quem deve sobre isso esta este essa esse "
             "slide imagem texto titulo foto with from that this".split())


def _norm(s):
    s = re.sub(r"<[^>]+>", " ", str(s or ""))
    return unicodedata.normalize("NFKD", s.lower()).encode("ascii", "ignore").decode()


def _palavras(s):
    return [w for w in re.findall(r"[a-z0-9]+", _norm(s)) if len(w) >= 4 and w not in COMUNS]


def referencias_do_slide(deck, k):
    """Palavras do título do slide e do nome, legenda e descrição das imagens que ele usa."""
    s = (deck.get("slides") or [])[k] if k < len(deck.get("slides") or []) else {}
    imgs, refs = deck.get("imagens") or {}, []
    for c in ("titulo", "subtitulo"):
        refs += _palavras(s.get(c))
    refs += _palavras((s.get("citacao") or {}).get("autor"))

    def varrer(v):
        if isinstance(v, str) and v in imgs:
            refs.extend(_palavras(v.replace("-", " ")) + _palavras(imgs[v].get("legenda")) + _palavras(imgs[v].get("alt")))
        elif isinstance(v, dict):
            for x in v.values():
                varrer(x)
        elif isinstance(v, list):
            for x in v:
                varrer(x)
    varrer(s)
    return set(refs)


def evidencia_generica(ev, refs, repetidas):
    """Devolve o motivo pelo qual a evidência não serve, ou None."""
    pal = re.findall(r"\w+", ev)
    if len(pal) < 10:
        return f"evidência com {len(pal)} palavras (mínimo 10). Descreva o que está no slide"
    if _norm(ev).strip() in repetidas:
        return "evidência repetida em outro slide"
    ws = _palavras(ev)
    if refs and not any(w[:5] == r[:5] if min(len(w), len(r)) >= 5 else w == r for w in ws for r in refs):
        return "evidência sem nenhuma palavra do título do slide nem do nome ou da legenda da imagem"
    return None


def checar(proj: Path):
    motivos = []
    bj = proj / "dist" / "build.json"
    if not bj.is_file():
        return False, ["o deck ainda não foi construído (scripts/construir.py)."]
    build = json.loads(bj.read_text(encoding="utf8"))
    html = proj / "dist" / build.get("arquivo", "")
    if not html.is_file():
        return False, [f"o HTML {build.get('arquivo')} não está em dist/. Construa de novo."]
    if hashlib.sha256(html.read_bytes()).hexdigest()[:16] != build["hash"]:
        motivos.append("o HTML em dist/ foi alterado depois de construído. Nunca edite o HTML. Edite deck.json e construa de novo.")
    if build.get("rascunho"):
        motivos.append("o HTML atual foi construído com --rascunho. Construa sem a opção e verifique de novo.")
    rp = proj / "verificacao" / "relatorio.json"
    if not rp.is_file():
        return False, motivos + ["falta a verificação automática (scripts/verificar.py)."]
    rel = json.loads(rp.read_text(encoding="utf8"))
    if rel.get("hash") != build["hash"]:
        motivos.append("a verificação é de outra versão do deck. Rode scripts/verificar.py de novo.")
    frouxos = medir.limites_frouxos(rel.get("limites") or {})
    if frouxos:
        motivos.append("a verificação usou limites mais frouxos que os da skill: " + ", ".join(frouxos) + ".")
    if not rel.get("automatico_ok"):
        ruins = [s["slide"] for s in rel.get("slides", []) if not s.get("automatico_ok")]
        motivos.append(f"a medição automática reprovou os slides {ruins or '(condições gerais)'}.")
    pp = proj / "revisao" / "parecer.json"
    if not pp.is_file():
        motivos.append("falta a aprovação desta versão. Rode scripts/fazer.py (ou, com a pessoa, scripts/revisao.py).")
        return False, motivos
    par = json.loads(pp.read_text(encoding="utf8"))
    if par.get("hash") != build["hash"]:
        motivos.append("o parecer é de outra versão do deck. Qualquer mudança exige nova avaliação.")
    av = par.get("avaliador") or {}
    if av.get("tipo") == "automatico":
        if par.get("hash") != build["hash"]:
            motivos.append("a aprovação automática é de outra versão do deck. Rode scripts/fazer.py de novo.")
        if not par.get("aprovado"):
            motivos.append("a aprovação automática não está marcada como aprovada.")
        return not motivos, motivos
    if av.get("tipo") == "agente":
        if par.get("hash") != build["hash"]:
            motivos.append("o parecer do avaliador é de outra versão do deck. Rode scripts/fazer.py, que registra a correção.")
        if par.get("visao") != "com_visao":
            motivos.append("avaliador agente sem visão comprovada (scripts/teste_visao.py). Use o caminho automático.")
        if not av.get("contexto_separado"):
            motivos.append("parecer DEGRADADO. Avaliador agente sem contexto separado não libera.")
        if par.get("defeitos"):
            motivos.append(f"o avaliador apontou {len(par['defeitos'])} defeito(s) em revisao/defeitos.json. Corrija e rode scripts/fazer.py.")
        elif not par.get("aprovado"):
            motivos.append("o parecer do avaliador não está marcado como aprovado.")
        return not motivos, motivos
    if not str(av.get("nome", "")).strip():
        motivos.append("o parecer não identifica o avaliador.")
    if av.get("tipo") != "pessoa":
        motivos.append("o tipo de avaliador precisa ser 'automatico', 'agente' ou 'pessoa'.")
    if av.get("tipo") == "agente" and not av.get("contexto_separado"):
        motivos.append("parecer DEGRADADO. Avaliador agente sem contexto separado não libera, porque quem construiu o deck não pode se aprovar.")
    n_rel = len(rel.get("slides", []))
    ps = par.get("slides") or []
    if len(ps) != n_rel:
        motivos.append(f"o parecer cobre {len(ps)} slides e o deck tem {n_rel}.")
    deck = json.loads((proj / "deck.json").read_text(encoding="utf8")) if (proj / "deck.json").is_file() else {}
    exige_ev = av.get("tipo") == "agente" or par.get("origem") == "painel"
    vistas = [_norm(s.get("evidencia", "")).strip() for s in ps]
    vazias = []
    for s in ps:
        falta = [k for k in ("fontes_ok", "tela_ocupada", "sem_defeitos", "visual_ok") if not s.get(k)]
        if falta:
            motivos.append(f"slide {s.get('slide')}: avaliador não confirmou {', '.join(falta)}" + (f" ({s.get('nota')})" if s.get("nota") else "") + ".")
        ev = str(s.get("evidencia", "")).strip()
        if exige_ev:
            rep_ = {v for v in vistas if v and vistas.count(v) > 1}
            ruim = evidencia_generica(ev, referencias_do_slide(deck, int(s.get("slide", 0)) - 1), rep_)
            if ruim:
                motivos.append(f"slide {s.get('slide')}: {ruim}.")
            vazias += [(s.get("slide"), m) for m in VAZIAS.findall(_norm(ev + " " + str(s.get("nota", ""))))]
    vazias += [("síntese", m) for m in VAZIAS.findall(_norm(" ".join(str(v) for v in (par.get("sintese") or {}).values())))]
    if av.get("tipo") == "agente":
        vazias += [("declaração", m) for m in VAZIAS.findall(_norm(par.get("declaracao_literal")))]
    if vazias:
        motivos.append("o parecer usa palavras vazias (" + ", ".join(f"{m} em {o}" for o, m in vazias[:6]) + "). Diga o que se vê, por exemplo tamanho, cor, posição, imagem.")
    dp = proj / "revisao" / "diretor.md"
    if dp.is_file():
        dv = sorted(set(VAZIAS.findall(_norm(dp.read_text(encoding="utf8")))))
        if dv:
            motivos.append(f"as notas do diretor de arte (revisao/diretor.md) usam palavras vazias ({', '.join(dv)}). Troque por apontamentos concretos.")
    g = par.get("globais") or {}
    for k, nome in (("argumento", "só os títulos contam o argumento (teste do deck fantasma)"), ("variacao", "variação"),
                    ("conteudo_real", "conteúdo real"), ("movimento", "movimento visto no navegador")):
        if not g.get(k):
            motivos.append(f"condição geral não confirmada: {nome}.")
    if not par.get("aprovado"):
        motivos.append("o parecer não está marcado como aprovado.")
    return not motivos, motivos


def _base(proj: Path):
    build = json.loads((proj / "dist" / "build.json").read_text(encoding="utf8"))
    rel = json.loads((proj / "verificacao" / "relatorio.json").read_text(encoding="utf8"))
    if rel.get("hash") != build["hash"]:
        raise SystemExit("ERRO verifique esta versão antes de registrar (scripts/verificar.py).")
    return build, rel


def _gravar(proj: Path, par):
    (proj / "revisao").mkdir(exist_ok=True)
    (proj / "revisao" / "parecer.json").write_text(json.dumps(par, ensure_ascii=False, indent=1), encoding="utf8")


def parecer_atual(proj: Path):
    pp = proj / "revisao" / "parecer.json"
    try:
        return json.loads(pp.read_text(encoding="utf8")) if pp.is_file() else {}
    except ValueError:
        return {}


def registrar_automatico(proj: Path, nota=""):
    """Aprovação pelas verificações automáticas. Diz com franqueza se houve ou não revisão visual."""
    build, rel = _base(proj)
    if not rel.get("automatico_ok"):
        raise SystemExit("ERRO a verificação automática não passou. Corrija antes de aprovar.")
    _gravar(proj, {"hash": build["hash"], "arquivo": build["arquivo"], "data": datetime.now(timezone.utc).isoformat(),
                   "avaliador": {"nome": "verificações automáticas", "tipo": "automatico"},
                   "revisao_visual": bool(nota), "nota": nota or "aprovado pelas verificações automáticas, sem revisão visual",
                   "automatico_ok": True, "aprovado": True})


def registrar_agente(proj: Path, avaliador, defeitos_arq, separado):
    """Avaliador com visão comprovada. Só aceita a lista de defeitos que ele viu nas folhas de contato."""
    build, rel = _base(proj)
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import teste_visao
    vis = teste_visao.estado(proj)
    if vis != "com_visao":
        raise SystemExit("ERRO o avaliador não passou no teste de visão (scripts/teste_visao.py). Sem visão não há avaliação visual. "
                         "Siga pelo caminho automático (scripts/fazer.py).")
    bruto = json.loads(Path(defeitos_arq).read_text(encoding="utf8")) if defeitos_arq else {"defeitos": []}
    defs = bruto.get("defeitos", bruto) if isinstance(bruto, dict) else bruto
    defs = [d for d in (defs or []) if isinstance(d, dict) and d.get("slide")]
    _gravar(proj, {"hash": build["hash"], "arquivo": build["arquivo"], "data": datetime.now(timezone.utc).isoformat(),
                   "avaliador": {"nome": avaliador, "tipo": "agente", "contexto_separado": separado},
                   "visao": vis, "defeitos": defs, "automatico_ok": rel.get("automatico_ok"),
                   "aprovado": not defs and bool(rel.get("automatico_ok")) and separado})


def registrar(proj: Path, avaliador, tipo, declaracao, reprovar, motivo, separado, evidencias=None):
    build, rel = _base(proj)
    if not declaracao or len(declaracao.strip()) < 8:
        raise SystemExit("ERRO registre as palavras literais do avaliador em --declaracao.")
    ev, globais_agente = {}, None
    ruins = set()
    if reprovar:
        for p in reprovar.split(","):
            if "-" in p:
                x, y = p.split("-")
                ruins.update(range(int(x), int(y) + 1))
            elif p.strip():
                ruins.add(int(p))
    slides = []
    for s in rel["slides"]:
        ok = s["slide"] not in ruins and s["automatico_ok"]
        slides.append({"slide": s["slide"], "fontes_ok": ok, "tela_ocupada": ok, "sem_defeitos": ok, "visual_ok": ok,
                       "nota": (motivo or "") if s["slide"] in ruins else "",
                       "evidencia": ev.get(str(s["slide"]), "") if tipo == "agente" else declaracao})
    aprovado = not ruins and rel.get("automatico_ok", False)
    par = {"hash": build["hash"], "arquivo": build["arquivo"], "data": datetime.now(timezone.utc).isoformat(),
           "avaliador": {"nome": avaliador, "tipo": tipo, "contexto_separado": separado if tipo == "agente" else None},
           "declaracao_literal": declaracao, "slides": slides,
           "origem": "conversa", "estado": "degradado" if tipo == "agente" and not separado else "normal",
           "globais": {k: aprovado and (globais_agente is None or bool(globais_agente.get(k))) for k in ("argumento", "variacao", "conteudo_real", "movimento")},
           "automatico_ok": rel.get("automatico_ok"), "aprovado": aprovado}
    _gravar(proj, par)
    print("parecer registrado em revisao/parecer.json")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("projeto")
    ap.add_argument("--registrar", action="store_true")
    ap.add_argument("--avaliador")
    ap.add_argument("--tipo", choices=["pessoa", "agente"], default="pessoa")
    ap.add_argument("--automatico", action="store_true", help="aprova pela verificação automática (sem revisão visual)")
    ap.add_argument("--defeitos", help="agente com visão: JSON com a lista de defeitos que ele viu")
    ap.add_argument("--declaracao")
    ap.add_argument("--reprovar")
    ap.add_argument("--motivo")
    ap.add_argument("--contexto-separado", action="store_true")
    a = ap.parse_args()
    proj = Path(a.projeto).resolve()
    if a.automatico:
        registrar_automatico(proj)
    elif a.registrar:
        if not a.avaliador:
            raise SystemExit("ERRO informe --avaliador")
        if a.tipo == "agente":
            registrar_agente(proj, a.avaliador, a.defeitos, a.contexto_separado)
        else:
            registrar(proj, a.avaliador, a.tipo, a.declaracao, a.reprovar, a.motivo, a.contexto_separado)
    ok, motivos = checar(proj)
    if ok:
        par = parecer_atual(proj)
        print(f"LIBERADO ({(par.get('avaliador') or {}).get('tipo', '?')}). Pode exportar PDF e PPTX finais.")
        return 0
    print("TRAVADO" + (" (parecer degradado)" if any("DEGRADADO" in m for m in motivos) else "") + ". Condições pendentes:")
    for m in motivos:
        print(" -", m)
    return 2


if __name__ == "__main__":
    sys.exit(main())
