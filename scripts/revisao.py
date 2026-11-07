#!/usr/bin/env python3
"""Painel do AVALIADOR HUMANO.

    python3 scripts/revisao.py PROJETO

Gera PROJETO/revisao/painel.html, um arquivo único que abre em qualquer navegador (também no
painel lateral do Cowork). No topo, o teste do deck fantasma (só os títulos, em ordem) e os
avisos do deck. Para cada slide, primeiro só a captura limpa. As marcas (vazio em vermelho, texto
pequeno, sem contraste ou enfeite em laranja), os números e as caixas aparecem depois que o
avaliador escreve o que viu (pelo menos 10 palavras), para ele não se ancorar nos números.
No fim, o bloco Manter, Corrigir, Ganhos rápidos e o parecer.json que a trava exige.

Slide reprovado pela medição automática não pode ser aprovado no painel: corrija e verifique de novo.
Também gera PROJETO/revisao/pendencias.md com o que falta, para quem revisa pela conversa.
"""
from __future__ import annotations

import argparse
import base64
import html as H
import io
import json
import re
import sys
from pathlib import Path


def jpg64(p: Path, largura=1280, q=80):
    from PIL import Image
    im = Image.open(p).convert("RGB")
    if im.width > largura:
        im = im.resize((largura, int(im.height * largura / im.width)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=q)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


CSS = """
:root{--bg:#F3EFE6;--card:#FFFDF8;--ink:#1D232B;--mut:#535B66;--ok:#1F7A45;--bad:#B3261E;--warn:#9A5B00;--line:#D9D1C1}
@media (prefers-color-scheme:dark){:root{--bg:#14171A;--card:#1D2125;--ink:#ECE8DF;--mut:#A9B0B8;--ok:#5CC48A;--bad:#FF8A80;--warn:#F2B35B;--line:#343A40}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:18px/1.45 'Segoe UI',system-ui,sans-serif}
header{padding:28px 4vw 18px;border-bottom:1px solid var(--line);position:sticky;top:0;background:var(--bg);z-index:3}
h1{font-size:30px;margin:0 0 6px}h2{font-size:24px;margin:0}
.sum{display:flex;flex-wrap:wrap;gap:10px 22px;color:var(--mut);font-size:17px}
.pill{display:inline-block;padding:2px 12px;border-radius:99px;font-weight:700;font-size:15px}
.ok{background:color-mix(in srgb,var(--ok) 16%,transparent);color:var(--ok)}.bad{background:color-mix(in srgb,var(--bad) 16%,transparent);color:var(--bad)}
main{padding:24px 4vw 120px;display:grid;gap:28px}
.inst{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:20px 24px;max-width:1100px}
.slide{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:20px;display:grid;grid-template-columns:minmax(0,1.7fr) minmax(320px,1fr);gap:24px}
@media (max-width:1100px){.slide{grid-template-columns:1fr}}
.slide.reprovado{border-color:var(--bad);box-shadow:0 0 0 2px color-mix(in srgb,var(--bad) 30%,transparent)}
.img{position:relative;border-radius:10px;overflow:hidden;background:#000;aspect-ratio:16/9}
.img img{width:100%;height:100%;object-fit:contain;display:block}
.img img.marcas{position:absolute;inset:0;opacity:0;transition:opacity .2s}
.img.ver-marcas img.marcas{opacity:1}
.ctrl{display:flex;gap:10px;margin-top:10px;flex-wrap:wrap}
button{font:inherit;padding:8px 16px;border-radius:10px;border:1px solid var(--line);background:var(--bg);color:var(--ink);cursor:pointer}
button.prim{background:var(--ink);color:var(--bg);border-color:var(--ink);font-weight:700}
table{border-collapse:collapse;width:100%;font-size:16px}td{padding:5px 6px;border-bottom:1px solid var(--line)}td:last-child{text-align:right;font-variant-numeric:tabular-nums}
.chk{display:grid;gap:10px;margin-top:14px}
label{display:flex;gap:12px;align-items:flex-start;font-size:18px;cursor:pointer}
label input{width:24px;height:24px;margin-top:2px;accent-color:var(--ok)}
textarea,input[type=text]{width:100%;font:inherit;padding:10px;border-radius:10px;border:1px solid var(--line);background:var(--bg);color:var(--ink)}
.prob{color:var(--bad);font-size:16px;margin:8px 0 0}.av{color:var(--warn);font-size:16px;margin:6px 0 0}
.depois{display:none}.slide.liberado .depois{display:block}.slide.liberado .falta{display:none}.falta{color:var(--mut);font-size:15px}
.fantasma{margin:10px 0 0;padding-left:1.6em;font-size:19px}.fantasma li{margin:3px 0}
footer{position:fixed;left:0;right:0;bottom:0;background:var(--card);border-top:1px solid var(--line);padding:14px 4vw;display:flex;gap:18px;align-items:center;z-index:4;flex-wrap:wrap}
#estado{font-weight:700}
"""

JS = r"""
const R = window.REL;
function coletar(){
  const slides = R.slides.map(s => {
    const g = (k) => { const el = document.getElementById(k + s.slide); return el ? el.checked : false; };
    return {slide:s.slide, fontes_ok:g('f'), tela_ocupada:g('t'), sem_defeitos:g('d'), visual_ok:g('v'),
            nota:(document.getElementById('n'+s.slide)||{}).value||'', evidencia:(document.getElementById('e'+s.slide)||{}).value||''};
  });
  const glob = {argumento:document.getElementById('ga').checked, variacao:document.getElementById('gv').checked, conteudo_real:document.getElementById('gr').checked, movimento:document.getElementById('gm').checked};
  const sintese = {manter:document.getElementById('xm').value.trim(), corrigir:document.getElementById('xc').value.trim(), ganhos_rapidos:document.getElementById('xg').value.trim()};
  const quem = document.getElementById('quem').value.trim(), tipo = document.getElementById('tipo').value;
  const tudo = slides.every(s => s.fontes_ok && s.tela_ocupada && s.sem_defeitos && s.visual_ok) && Object.values(glob).every(Boolean);
  const sep = tipo==='agente' ? document.getElementById('sep').checked : null;
  return {hash:R.hash, arquivo:R.arquivo, data:new Date().toISOString(), origem:'painel', estado: tipo==='agente' && !sep ? 'degradado' : 'normal',
          avaliador:{nome:quem, tipo:tipo, contexto_separado: sep}, slides:slides, globais:glob, sintese:sintese,
          automatico_ok:R.automatico_ok, aprovado: !!(tudo && R.automatico_ok && quem && !(tipo==='agente' && !sep))};
}
function atualizar(){
  const p = coletar();
  const pend = p.slides.filter(s => !(s.fontes_ok && s.tela_ocupada && s.sem_defeitos && s.visual_ok)).map(s => s.slide);
  const e = document.getElementById('estado');
  if (!R.automatico_ok) e.textContent = 'TRAVADO: a medição automática reprovou. Corrija, construa e verifique de novo.';
  else if (!p.avaliador.nome) e.textContent = 'Informe quem está avaliando.';
  else if (pend.length) e.textContent = 'TRAVADO: faltam ' + pend.length + ' slide(s): ' + pend.join(', ');
  else if (!Object.values(p.globais).every(Boolean)) e.textContent = 'TRAVADO: faltam as condições gerais (inclusive o teste do deck fantasma, no topo).';
  else if (p.estado === 'degradado') e.textContent = 'DEGRADADO: avaliador agente sem contexto separado não libera.';
  else e.textContent = 'Tudo satisfeito. Gere o parecer e salve em revisao/parecer.json.';
  e.style.color = p.aprovado ? 'var(--ok)' : 'var(--bad)';
}
function gerar(){
  const p = coletar(); const txt = JSON.stringify(p, null, 1);
  document.getElementById('saida').value = txt;
  const a = document.getElementById('baixar'); a.href = URL.createObjectURL(new Blob([txt], {type:'application/json'})); a.download = 'parecer.json'; a.style.display='inline-block';
}
function liberar(){ R.slides.forEach(s => { const el = document.getElementById('e' + s.slide); const n = (el.value.match(/[\p{L}\p{N}]+/gu) || []).length;
  const card = document.getElementById('s' + s.slide); if (n >= 10) card.classList.add('liberado');
  const f = card.querySelector('.falta'); if (f) f.textContent = 'Escreva o que você vê neste slide antes de ver as medições (faltam ' + Math.max(0, 10 - n) + ' palavras).'; }); }
document.addEventListener('change', atualizar); document.addEventListener('input', () => { liberar(); atualizar(); });
document.querySelectorAll('.alternar').forEach(b => b.onclick = () => b.closest('.slide').querySelector('.img').classList.toggle('ver-marcas'));
window.onload = () => { liberar(); atualizar(); };
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("projeto")
    a = ap.parse_args()
    proj = Path(a.projeto).resolve()
    relp = proj / "verificacao" / "relatorio.json"
    if not relp.is_file():
        print("ERRO rode antes: python3 scripts/verificar.py PROJETO")
        return 1
    rel = json.loads(relp.read_text(encoding="utf8"))
    build = json.loads((proj / "dist" / "build.json").read_text(encoding="utf8"))
    if build["hash"] != rel["hash"]:
        print("ERRO a verificação é de uma versão anterior do deck. Rode scripts/verificar.py de novo.")
        return 1
    d = rel["deck"]
    deck = json.loads((proj / "deck.json").read_text(encoding="utf8"))
    titulos = []
    for k, s in enumerate(deck.get("slides", [])):
        tt = re.sub(r"<[^>]+>|\*\*", "", s.get("titulo") or "").strip()
        if not tt and s.get("citacao"):
            tt = f"(citação de {(s['citacao'].get('autor') or 'autor sem nome')})"
        titulos.append(tt or f"(sem título, layout {s.get('layout')})")
    cards = []
    pend = []
    for s in rel["slides"]:
        n = s["slide"]
        auto = s["automatico_ok"]
        falhas = [nome for nome, ok in (("fonte abaixo do piso", s["fontes_ok"]), ("área morta", s["tela_ocupada"]),
                                        ("texto não coube", s["encaixe_ok"]), ("contraste baixo", s["contraste_ok"]),
                                        ("enfeite", s.get("enfeites_ok", True)), ("animação inacabada", s.get("estado_final_ok", True))) if not ok]
        if not auto:
            pend.append(f"- Slide {n} ({s['layout']}): reprovado na medição ({', '.join(falhas)}).")
        probs = "".join(f"<p class='prob'>Texto pequeno: “{p['trecho'][:60]}” com {p['px']} px (piso {p['piso']} px).</p>" for p in s["problemas_fonte"][:4])
        probs += "".join(f"<p class='prob'>Contraste {c['razao']}:1 em “{c['trecho'][:50]}”.</p>" for c in s["problemas_contraste"][:3])
        probs += "".join(f"<p class='prob'>REPROVA {H.escape(x['tipo'])}: {H.escape(x['msg'])}</p>" for x in s.get("enfeites", []) + s.get("estado_final", []))
        probs += "".join(f"<p class='av'>Aviso, {H.escape(x['tipo'])}: {H.escape(x['msg'])}</p>" for x in s.get("avisos", [])[:5])
        dis = "" if auto else " disabled"
        aviso = "" if auto else "<p class='prob'><b>Reprovado pela medição.</b> Não pode ser aprovado aqui. Corrija o deck.</p>"
        tabela = "".join(f"<tr><td>{k}</td><td>{v}</td></tr>" for k, v in [
            ("Layout", s["layout"]), ("Menor texto", f"{s['menor_fonte_px']} px ({round((s['menor_fonte_px'] or 0) / 2, 1)} pt)"),
            ("Corpo do slide", f"{s['corpo_px']} px ({s['corpo_px'] / 2:.0f} pt)"), ("Título", f"{s['titulo_px']} px"),
            ("Área morta", f"{int(s['fracao_vazia'] * 100)}% (limite {int(rel['limites']['max_fracao_vazia'] * 100)}%)"),
            ("Maior vazio contínuo", f"{int(s['maior_vazio'] * 100)}% (limite {int(rel['limites']['max_maior_vazio'] * 100)}%)"),
            ("Extensão do conteúdo", f"{int(s['extensao_x'] * 100)}% × {int(s['extensao_y'] * 100)}%"),
            ("Imagem real", "sim" if s["imagem_real"] else ("gráfico ou diagrama" if s["visual"] else "não")), ("Palavras", s["palavras"])])
        cards.append(f"""
<section class="slide" id="s{n}">
 <div><div class="img"><img src="{jpg64(proj / 'verificacao' / 'slides' / f's{n:03d}.png')}" alt="Slide {n}"><img class="marcas depois" src="{jpg64(proj / 'verificacao' / 'slides' / f's{n:03d}_marcas.jpg')}" alt="Marcas do slide {n}"></div>
 <div class="ctrl depois"><button class="alternar">Mostrar ou esconder as marcas</button></div></div>
 <div><h2>Slide {n} · {H.escape(titulos[n - 1] if n <= len(titulos) else s['layout'])}</h2>
 <textarea id="e{n}" rows="3" placeholder="O que você vê neste slide: imagem, posição do título, tamanho do texto, onde sobra espaço (pelo menos 10 palavras)"></textarea>
 <p class="falta"></p>
 <div class="depois"><p><span class="pill {'ok' if auto else 'bad'}">{'medição ok' if auto else 'reprovado'}</span></p>
 <table>{tabela}</table>{aviso}{probs}
 <div class="chk">
  <label><input type="checkbox" id="f{n}"{dis}> Fontes grandes e legíveis em todo o slide, inclusive legendas, rótulos e fontes</label>
  <label><input type="checkbox" id="t{n}"{dis}> A tela inteira está ocupada, sem área morta</label>
  <label><input type="checkbox" id="d{n}"{dis}> Nada cortado, sobreposto ou sem contraste</label>
  <label><input type="checkbox" id="v{n}"{dis}> Imagem ou visual pertinente ao conteúdo</label>
  <input type="text" id="n{n}" placeholder="Correção pedida (se houver)">
 </div></div></div>
</section>""")
    resumo = (f"<span class='pill {'ok' if rel['automatico_ok'] else 'bad'}'>medição {'ok' if rel['automatico_ok'] else 'reprovada'}</span>"
              f"<span>{d['slides']} slides</span><span>{d['com_imagem_real']} com imagem real</span><span>{d['layouts_distintos']} layouts distintos</span>"
              f"<span>sem internet: {'ok' if d['offline']['ok'] else 'falha'}</span><span>versão {rel['hash']}</span>")
    av_deck = d.get("avisos") or []
    avisos_html = ("<h2 style='margin-top:18px'>Avisos do deck (não travam)</h2>" + "".join(f"<p class='av'>{H.escape(x)}</p>" for x in av_deck)) if av_deck else ""
    pagina = f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Avaliação humana</title><style>{CSS}</style></head><body>
<header><h1>Avaliação humana · {rel['arquivo']}</h1><div class="sum">{resumo}</div></header>
<main>
<div class="inst"><h2>Como avaliar</h2>
<p>Olhe cada captura como alguém sentado no fundo da sala e escreva primeiro o que vê, com palavras do slide (imagem, título, tamanho, espaço). Só então aparecem as marcas, os números e as caixas. Evite palavras vazias como moderno, limpo, elegante ou bonito, que a trava recusa. As marcas vermelhas mostram área morta, as laranjas mostram texto abaixo do piso, pouco contraste ou enfeite. Slide reprovado pela medição não pode ser aprovado aqui, peça a correção. Qualquer mudança no deck exige nova avaliação.</p>
<p>Avaliador: <input type="text" id="quem" placeholder="Seu nome" style="max-width:340px"> <select id="tipo"><option value="pessoa">pessoa</option><option value="agente">agente em contexto separado</option></select>
<label style="display:inline-flex;margin-left:12px"><input type="checkbox" id="sep"> o agente avaliador não construiu o deck</label></p></div>
<div class="inst"><h2>Teste do deck fantasma</h2><p>Leia só os títulos, em ordem. Eles contam o argumento sozinhos, sem as imagens e sem o corpo?</p>
<ol class="fantasma">{''.join(f"<li>{H.escape(x)}</li>" for x in titulos)}</ol>
<div class="chk"><label><input type="checkbox" id="ga"> Só os títulos contam o argumento</label></div>
{avisos_html}</div>
{''.join(cards)}
<section class="inst"><h2>Condições gerais</h2><div class="chk">
<label><input type="checkbox" id="gv"> Há variação real entre os slides (layouts, composição, ritmo)</label>
<label><input type="checkbox" id="gr"> Informações, números e imagens são reais e têm fonte ou crédito (tecla I no deck)</label>
<label><input type="checkbox" id="gm"> Movimento e animações foram vistos no navegador e servem ao tema</label></div>
<h2 style="margin-top:22px">Manter, Corrigir, Ganhos rápidos</h2>
<p>Manter. O que funciona e não pode se perder na correção.</p><textarea id="xm" rows="2"></textarea>
<p>Corrigir. Os problemas que pesam mais, em ordem.</p><textarea id="xc" rows="3"></textarea>
<p>Ganhos rápidos. Ajustes pequenos que melhoram muito (trocar lado, recortar imagem, cortar um item).</p><textarea id="xg" rows="2"></textarea>
<p style="margin-top:18px"><button class="prim" onclick="gerar()">Gerar parecer</button> <a id="baixar" style="display:none;margin-left:12px">Baixar parecer.json</a></p>
<textarea id="saida" rows="8" placeholder="O parecer aparece aqui. Salve como revisao/parecer.json no projeto."></textarea></section>
</main><footer><span id="estado"></span></footer>
<script>window.REL={json.dumps({'hash': rel['hash'], 'arquivo': rel['arquivo'], 'automatico_ok': rel['automatico_ok'], 'slides': [{'slide': s['slide']} for s in rel['slides']]})};</script>
<script>{JS}</script></body></html>"""
    rv = proj / "revisao"
    rv.mkdir(exist_ok=True)
    (rv / "painel.html").write_text(pagina, encoding="utf8")
    linhas = [f"# Pendências para o avaliador humano · versão {rel['hash']}", ""]
    if not rel["automatico_ok"]:
        linhas += ["A medição automática reprovou. Nada pode ser aprovado antes da correção.", ""] + pend
        if not d["variacao_ok"]:
            linhas.append(f"- Variação: três iguais seguidos {d['tres_iguais_seguidos']}, quase idênticos {d['quase_iguais']}.")
        if not d["tecnico_ok"]:
            linhas.append(f"- Técnico: sem internet {d['offline']}, console {d['console'][:3]}.")
    else:
        linhas += ["A medição automática passou em todos os slides. Falta o olhar do avaliador:",
                   "1. Abra revisao/painel.html (ou as folhas em verificacao/folhas).",
                   "2. Para cada slide, confirme fontes grandes e legíveis em todo o slide e tela inteira ocupada.",
                   "3. Leia só os títulos abaixo (teste do deck fantasma) e confirme se eles contam o argumento. Confirme variação, conteúdo real e movimento visto no navegador.",
                   "4. Salve o parecer em revisao/parecer.json, ou responda na conversa e o agente registra suas palavras com scripts/trava.py --registrar."]
    linhas += ["", "Títulos em ordem (teste do deck fantasma)", ""] + [f"{i}. {x}" for i, x in enumerate(titulos, 1)]
    if d.get("avisos"):
        linhas += ["", "Avisos do deck (não travam)", ""] + [f"- {x}" for x in d["avisos"]]
    (rv / "pendencias.md").write_text("\n".join(linhas), encoding="utf8")
    print(f"painel: {rv / 'painel.html'}\npendências: {rv / 'pendencias.md'}")
    print("\n".join(linhas))
    return 0


if __name__ == "__main__":
    sys.exit(main())
