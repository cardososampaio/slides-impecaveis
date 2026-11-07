#!/usr/bin/env python3
"""Um comando para o deck inteiro. Constrói, verifica, aprova e exporta, e imprime só o que exige ação.

    python3 scripts/fazer.py PROJETO                  # modo automático (padrão)
    python3 scripts/fazer.py PROJETO --sem-avaliador  # nunca para para o avaliador visual
    python3 scripts/fazer.py PROJETO --sem-exportar   # para depois da aprovação (sem PDF e PPTX)

Como decide.
  1. Tema vazio ou "auto" vira a sugestão do contrato, gravada no deck.json. Sem amostra de temas.
  2. Constrói e verifica. Se algo bloqueia, imprime cada problema com a correção e conta uma rodada.
     Avisos não contam e não pedem correção.
  3. Depois de três rodadas com erro (a primeira e duas correções) ele para de tentar, exporta com a tarja
     RASCUNHO e lista o que ficou para a pessoa. Isso impede voltas sem fim.
  4. Com tudo certo, aprova. Se esta sessão passou no teste de visão (scripts/teste_visao.py) e ainda não
     houve avaliação, ele para e pede o avaliador (agents/avaliador-humano.md). Se o avaliador apontou
     defeitos e o deck mudou depois disso, a correção é aprovada pelo caminho automático, com a nota de
     que houve revisão visual. Sem visão, aprova direto, com a nota de que não houve revisão visual.
  5. Exporta PDF e PPTX.

Saídas (código de retorno): 0 pronto, 1 corrigir e rodar de novo, 4 corrigir os defeitos do avaliador,
5 chamar o avaliador, 6 limite de rodadas (entregue o rascunho).
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
MAX_RODADAS = 3


def rodar(script, *args):
    r = subprocess.run([sys.executable, str(AQUI / script), *map(str, args)], capture_output=True, text=True, encoding="utf8", errors="replace")
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def estado(proj: Path):
    p = proj / "dist" / "rodadas.json"
    try:
        return json.loads(p.read_text(encoding="utf8")) if p.is_file() else {"falhas": 0}
    except ValueError:
        return {"falhas": 0}


def salvar_estado(proj: Path, st):
    (proj / "dist").mkdir(parents=True, exist_ok=True)
    (proj / "dist" / "rodadas.json").write_text(json.dumps(st), encoding="utf8")


def corte(t, n=60):
    t = " ".join(str(t).split())
    return t if len(t) <= n else t[: n - 1] + "…"


def problemas_da_verificacao(rel):
    """Lista curta de problemas que bloqueiam, cada um com a correção."""
    out = []
    for s in rel.get("slides", []):
        n = f"slide {s['slide']} ({s['layout']})"
        if not s.get("fontes_ok"):
            p = (s.get("problemas_fonte") or [{}])[0]
            out.append(f"{n}: texto de {p.get('px', '?')} px, abaixo do piso de {p.get('piso', '?')} (\"{corte(p.get('trecho', ''), 40)}\"). "
                       "Encurte o texto, tire itens ou divida o slide.")
        if not s.get("tela_ocupada"):
            dica = ("O espaço sobra entre blocos de texto. Escreva um pouco mais em cada item, use menos colunas ou passos, ou troque o layout."
                    if s.get("visual") else "Ponha imagem, gráfico ou diagrama, ou troque para um layout com visual maior.")
            out.append(f"{n}: {int(s.get('fracao_vazia', 0) * 100)}% da tela vazia (maior vazio {int(s.get('maior_vazio', 0) * 100)}%). {dica}")
        if not s.get("encaixe_ok"):
            sob = s.get("texto_sobreposto") or []
            enc = [x for x in sob if x.get("tipo") == "encostado"]
            if enc:
                x = enc[0]
                out.append(f"{n}: \"{corte(x['a'], 30)}\" encosta em \"{corte(x['b'], 30)}\". Encurte a palavra longa, reduza o número de "
                           "colunas ou passos, ou troque o layout.")
            elif sob:
                x = sob[0]
                out.append(f"{n}: \"{corte(x['a'], 30)}\" está por cima de \"{corte(x['b'], 30)}\". Encurte o texto ou troque o layout.")
            else:
                out.append(f"{n}: o texto não cabe nem no tamanho mínimo. Corte texto ou divida em dois slides.")
        if not s.get("contraste_ok"):
            c = (s.get("problemas_contraste") or [{}])[0]
            out.append(f"{n}: contraste {c.get('razao', '?')} em \"{corte(c.get('trecho', ''), 30)}\" (mínimo 4,5). Tire o texto de cima da imagem "
                       "ou use o lado do campo de cor.")
        if not s.get("retrato_ok", True):
            r = (s.get("retrato_em_faixa") or [{}])[0]
            out.append(f"{n}: o retrato \"{r.get('k', '')}\" aparece numa faixa de {r.get('w')}x{r.get('h')} px e o rosto sai cortado. "
                       "Use \"dividido\", \"imagem-total\" ou \"numero\" para retratos, ou outra imagem na faixa.")
        for x in (s.get("enfeites") or []) + (s.get("estado_final") or []):
            out.append(f"{n}: {x.get('msg', x.get('tipo', ''))}")
    d = rel.get("deck") or {}
    if d.get("tres_iguais_seguidos"):
        out.append(f"três layouts iguais seguidos nos slides {d['tres_iguais_seguidos']}. Troque o layout do slide do meio.")
    if d.get("quase_iguais"):
        out.append(f"slides vizinhos quase idênticos: {d['quase_iguais']}. Mude layout, lado ou visual de um deles.")
    if d.get("layouts_distintos", 99) < d.get("minimo_layouts", 0):
        out.append(f"só {d['layouts_distintos']} layouts diferentes (mínimo {d['minimo_layouts']}). Varie mais.")
    if not (d.get("offline") or {}).get("ok", True):
        out.append("o HTML tenta usar a internet: " + "; ".join((d.get("offline") or {}).get("detalhe", [])[:2]))
    erros = [c for c in d.get("console", []) if c.startswith(("error", "pageerror"))]
    if erros:
        out.append("erro de JavaScript: " + corte(erros[0], 120))
    return out


def exportar(proj: Path, rascunho=False):
    linhas = []
    extra = ["--rascunho"] if rascunho else []
    for script in ("exportar_pdf.py", "exportar_pptx.py"):
        rc, out = rodar(script, proj, *extra)
        ok = [ln for ln in out.splitlines() if ln.startswith("OK ")]
        linhas += ok if rc == 0 and ok else [f"{script} falhou: " + corte(out.strip().splitlines()[-1] if out.strip() else "?", 160)]
    return linhas


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("projeto")
    ap.add_argument("--sem-avaliador", action="store_true", help="aprova pelo caminho automático mesmo com visão")
    ap.add_argument("--sem-exportar", action="store_true")
    a = ap.parse_args()
    proj = Path(a.projeto).resolve()
    dj = proj / "deck.json"
    if not dj.is_file():
        print(f"ERRO {dj} não existe. Crie com scripts/novo_projeto.py.")
        return 1
    try:
        deck = json.loads(dj.read_text(encoding="utf8"))
    except json.JSONDecodeError as e:
        print(f"ERRO deck.json não é JSON válido: linha {e.lineno}, coluna {e.colno}: {e.msg}")
        return 1

    # 1. tema automático, gravado para não mudar entre rodadas
    if deck.get("tema") in (None, "", "auto"):
        import construir
        deck["tema"] = construir.tema_automatico(deck)
        dj.write_text(json.dumps(deck, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
        print(f"tema: {deck['tema']} (escolhido pelo contrato e gravado no deck.json)")

    st = estado(proj)

    def falhou(problemas, origem):
        st["falhas"] = st.get("falhas", 0) + 1
        salvar_estado(proj, st)
        if st["falhas"] >= MAX_RODADAS:
            print(f"LIMITE DE RODADAS ({MAX_RODADAS}). Pare de corrigir. Problemas que ficaram:")
            for p in problemas[:12]:
                print(" -", p)
            if origem == "verificacao":
                for ln in exportar(proj, rascunho=True):
                    print(ln)
                print("Entregue o HTML e as exportações com a tarja RASCUNHO e diga à pessoa quais problemas ficaram.")
            else:
                print("O deck não constrói. Diga à pessoa quais erros ficaram.")
            return 6
        print(f"CORRIJA (rodada {st['falhas']} de {MAX_RODADAS}). Mude só os slides citados, sem reler o deck inteiro:")
        for p in problemas[:15]:
            print(" -", p)
        if len(problemas) > 15:
            print(f" - e mais {len(problemas) - 15}.")
        return 1

    # 2. construir
    rc, out = rodar("construir.py", proj, "--curto")
    if rc != 0:
        erros = [ln[6:].strip() for ln in out.splitlines() if ln.startswith("ERRO")]
        return falhou(erros or [corte(out, 300)], "construcao")

    # 3. verificar
    rc, out = rodar("verificar.py", proj, "--curto")
    rp = proj / "verificacao" / "relatorio.json"
    if not rp.is_file():
        print("ERRO a verificação não rodou: " + corte(out, 300))
        return 1
    rel = json.loads(rp.read_text(encoding="utf8"))
    if not rel.get("automatico_ok"):
        return falhou(problemas_da_verificacao(rel) or ["verificação reprovada. Veja verificacao/relatorio.md."], "verificacao")
    st["falhas"] = 0
    salvar_estado(proj, st)
    n_av = sum(len(s.get("avisos") or []) for s in rel.get("slides", [])) + len((rel.get("deck") or {}).get("avisos") or [])

    # 4. aprovação
    import teste_visao
    import trava
    build = json.loads((proj / "dist" / "build.json").read_text(encoding="utf8"))
    par = trava.parecer_atual(proj)
    tipo = (par.get("avaliador") or {}).get("tipo")
    mesma = par.get("hash") == build["hash"]
    if tipo == "pessoa" and mesma and par.get("aprovado"):
        caminho = "aprovado pela pessoa"
    elif tipo == "agente" and mesma and par.get("aprovado"):
        caminho = "aprovado pelo avaliador com visão, sem defeitos"
    elif tipo == "agente" and mesma and par.get("defeitos"):
        print(f"O avaliador apontou {len(par['defeitos'])} defeito(s). Corrija e rode fazer.py de novo:")
        for d in par["defeitos"][:12]:
            print(f" - slide {d.get('slide')}: {str(d.get('defeito', '')).rstrip('.')}." + (f" Correção: {d['correcao']}" if d.get("correcao") else ""))
        return 4
    elif tipo == "agente" and not mesma and par.get("defeitos"):
        nota = f"revisado por avaliador com visão. {len(par['defeitos'])} defeito(s) apontado(s) e corrigido(s) numa rodada"
        trava.registrar_automatico(proj, nota)
        caminho = nota
    elif not a.sem_avaliador and teste_visao.estado(proj) == "com_visao" and tipo not in ("agente", "automatico"):
        print("PASSOU nas verificações. Esta sessão tem visão. Chame o avaliador em contexto separado com agents/avaliador-humano.md "
              "(ele olha só as folhas em verificacao/folhas/) e depois rode fazer.py de novo.")
        return 5
    else:
        trava.registrar_automatico(proj)
        caminho = "aprovado pelas verificações automáticas, sem revisão visual"
    ok, motivos = trava.checar(proj)
    if not ok:
        print("TRAVADO: " + " ".join(motivos[:3]))
        return 1

    # 5. exportar
    print(f"PASSOU ({len(rel.get('slides', []))} slides, {n_av} aviso(s) que não bloqueiam). {caminho[0].upper() + caminho[1:]}.")
    print(f"HTML: {proj / 'dist' / build['arquivo']}")
    if not a.sem_exportar:
        for ln in exportar(proj):
            print(ln)
    return 0


if __name__ == "__main__":
    sys.exit(main())
