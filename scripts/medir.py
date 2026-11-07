#!/usr/bin/env python3
"""Medições objetivas que o avaliador humano usa como evidência.

Duas medidas, as mesmas para qualquer HTML (do motor desta skill ou feito à mão):

1. Tamanho real das fontes: percorre todos os nós de texto visíveis no slide atual
   (HTML e SVG), calcula o tamanho efetivo em px no palco de 1920x1080 (já considerando
   transformações de escala) e devolve uma lista de trechos com papel, tamanho e posição.

2. Ocupação da tela: lê a captura do slide (o que o olho vê), divide a área útil em
   células e marca como VAZIA a célula lisa (fundo ou campo de cor sem nada dentro),
   exceto onde há imagem ou desenho. Devolve a fração vazia, o maior retângulo vazio
   e a extensão do conteúdo.

Este módulo não decide sozinho. Ele produz números que o avaliador humano lê ao
olhar as capturas. Os limites ficam em LIMITES. deck.json > limites só pode endurecê-los.
"""
from __future__ import annotations

import math

LIMITES = {
    # tamanhos em px no palco 1920x1080 (1 px = 0,5 pt numa lâmina de 13,33 pol)
    "piso_qualquer_texto": 28,   # legenda, crédito, rótulo de gráfico, fonte
    "piso_corpo": 44,            # bullets, parágrafos, frases do slide
    "piso_titulo": 64,           # título do slide
    "piso_referencia": 32,       # lista de referências bibliográficas
    "piso_celula": 36,           # célula de tabela
    "caracteres_para_ser_corpo": 25,  # trecho com 25+ caracteres fora de legenda conta como corpo
    # ocupação da área útil
    "margem_x": 96, "margem_y": 64, "celula": 40,
    "max_fracao_vazia": 0.33,
    "max_maior_vazio": 0.16,
    "min_extensao_x": 0.86,
    "min_extensao_y": 0.80,
}



def limites_do_deck(extra):
    """deck.json > limites só pode deixar a regra mais exigente, nunca mais frouxa."""
    lim = dict(LIMITES)
    for k, v in (extra or {}).items():
        if k not in lim or not isinstance(v, (int, float)):
            continue
        if k.startswith(("piso_", "min_")):
            lim[k] = max(lim[k], v)
        elif k.startswith("max_"):
            lim[k] = min(lim[k], v)
    return lim


def limites_frouxos(lim):
    """Lista os limites de um relatório que estão abaixo do padrão da skill (usado pela trava)."""
    ruins = []
    for k, padrao in LIMITES.items():
        v = lim.get(k, padrao)
        if (k.startswith(("piso_", "min_")) and v < padrao) or (k.startswith("max_") and v > padrao):
            ruins.append(f"{k}={v} (padrão {padrao})")
    return ruins


# JavaScript executado na página. Recebe o elemento-raiz do slide (ou document.body).
JS_TEXTO = r"""
(root) => {
  root = root || document.body;
  const W = window.innerWidth, H = window.innerHeight;
  const out = [];
  const skip = (el) => el.closest('[data-ui],[data-sk-ignore],script,style,noscript,template,.notes,aside.notes,.sk-notes');
  const opacityChain = (el) => {
    let o = 1, e = el;
    while (e && e.nodeType === 1) {
      const cs = getComputedStyle(e);
      if (cs.display === 'none' || cs.visibility === 'hidden') return 0;
      o *= parseFloat(cs.opacity || '1');
      e = e.parentElement || (e.parentNode && e.parentNode.host) || null;
    }
    return o;
  };
  const scaleOf = (el) => {
    if (el instanceof SVGElement) {
      const m = el.getScreenCTM ? el.getScreenCTM() : null;
      if (m) return Math.sqrt(m.a * m.a + m.b * m.b);
      return 1;
    }
    let e = el;
    while (e && e.nodeType === 1) {
      if (e.offsetWidth > 0) {
        const r = e.getBoundingClientRect();
        return r.width / e.offsetWidth;
      }
      e = e.parentElement;
    }
    return 1;
  };
  const roleOf = (el) => {
    const r = el.closest('[data-role]');
    if (r) return r.getAttribute('data-role');
    if (el.closest('h1,h2,.sk-titulo,.sk-title')) return 'titulo';
    if (el.closest('.sk-itens,.sk-texto,.sk-sub,blockquote,.sk-ideias,li,p')) return 'corpo';
    if (el.closest('figcaption,.caption,.legenda,.cap,.src,cite,small,.credito,.fonte')) return 'legenda';
    if (el instanceof SVGElement) return 'rotulo';
    return '';
  };
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
  const blocos = new Map();
  const blocoDe = (e) => {
    let b = e;
    while (b && b !== root && b.parentElement) {
      const d = getComputedStyle(b).display;
      if (d !== 'inline' && d !== 'contents' && !(b instanceof SVGElement && b.tagName.toLowerCase() !== 'svg')) break;
      b = b.parentElement;
    }
    if (!blocos.has(b)) blocos.set(b, blocos.size);
    return blocos.get(b);
  };
  let n;
  while ((n = walker.nextNode())) {
    const txt = (n.nodeValue || '').replace(/\s+/g, ' ').trim();
    if (!txt) continue;
    const el = n.parentElement;
    if (!el || skip(el)) continue;
    const op = opacityChain(el);
    if (op < 0.2) continue;
    const range = document.createRange();
    range.selectNodeContents(n);
    const rects = Array.from(range.getClientRects()).filter(r => r.width > 1 && r.height > 1 && r.right > 0 && r.bottom > 0 && r.left < W && r.top < H);
    if (!rects.length) continue;
    const cs = getComputedStyle(el);
    const fs = parseFloat(cs.fontSize) * scaleOf(el);
    let x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9;
    rects.forEach(r => { x0 = Math.min(x0, r.left); y0 = Math.min(y0, r.top); x1 = Math.max(x1, r.right); y1 = Math.max(y1, r.bottom); });
    out.push({ t: txt.slice(0, 80), n: txt.length, px: Math.round(fs * 10) / 10, role: roleOf(el),
               x: Math.round(x0), y: Math.round(y0), w: Math.round(x1 - x0), h: Math.round(y1 - y0),
               op: Math.round(op * 100) / 100, color: (el instanceof SVGElement) ? cs.fill : cs.color,
               b: blocoDe(el), ls: rects.map(r => [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)]) });
  }
  // retângulos de conteúdo visual (imagens, vídeos, canvas e o desenho real de cada SVG)
  const vis = [];
  root.querySelectorAll('img,video,canvas,svg').forEach((el) => {
    if (el.closest('[data-ui],[data-sk-ignore]')) return;
    if (el instanceof SVGElement && el.ownerSVGElement) return;
    if (opacityChain(el) < 0.2) return;
    let r = el.getBoundingClientRect();
    if (el.tagName.toLowerCase() === 'svg') {
      try {
        const b = el.getBBox(), m = el.getScreenCTM();
        if (m && b.width > 0) {
          const xs = [b.x, b.x + b.width].map((x) => m.a * x + m.e), ys = [b.y, b.y + b.height].map((y) => m.d * y + m.f);
          const x0 = Math.max(Math.min(...xs), r.left), x1 = Math.min(Math.max(...xs), r.right), y0 = Math.max(Math.min(...ys), r.top), y1 = Math.min(Math.max(...ys), r.bottom);
          r = { left: x0, top: y0, width: x1 - x0, height: y1 - y0 };
        }
      } catch (e) { /* sem bbox */ }
    }
    // Desenho (svg, canvas) que cobre mais de metade da tela é fundo: quem decide é a captura.
    // Sem isso, um canvas decorativo em tela cheia faria qualquer slide parecer ocupado.
    const tag = el.tagName.toLowerCase();
    if ((tag === 'svg' || tag === 'canvas') && r.width * r.height > 0.5 * W * H) return;
    if (r.width * r.height > 6400) vis.push([Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)]);
  });
  return { W, H, items: out, visuais: vis };
}
"""


# Enfeites de gerador, estado final e avisos tipográficos, lidos nos estilos computados do slide.
# Ideias adaptadas de pbakaus/impeccable (Apache 2.0, antipatterns.json e crates/core/src/checks)
# e de alchaincyf/huashu-design (MIT, scripts/design_lint.py). Ver LICENSE-NOTES.md.
# Devolve {reprova: [...], final: [...], avisos: [...], anim: "seq"}; cada achado tem tipo, msg, trecho e caixa.
JS_ENFEITES = r"""
(root) => {
  root = root || document.body;
  const W = innerWidth, H = innerHeight, doc = document.documentElement;
  const ign = (el) => el.closest('[data-ui],[data-sk-ignore],script,style,noscript,template,.notes,.sk-notes');
  const caixa = (r) => ({ x: Math.round(r.left), y: Math.round(r.top), w: Math.round(r.width), h: Math.round(r.height) });
  const naTela = (r) => r.width > 1 && r.height > 1 && r.right > 0 && r.bottom > 0 && r.left < W && r.top < H;
  const escala = (el) => { if (el instanceof SVGElement) { const m = el.getScreenCTM && el.getScreenCTM(); return m ? Math.hypot(m.a, m.b) : 1; }
    let e = el; while (e && e.nodeType === 1) { if (e.offsetWidth > 0) return e.getBoundingClientRect().width / e.offsetWidth; e = e.parentElement; } return 1; };
  const fsOf = (el) => parseFloat(getComputedStyle(el).fontSize) * escala(el);
  const opac = (el) => { let o = 1, e = el, oculto = false;
    while (e && e.nodeType === 1) { const cs = getComputedStyle(e); if (cs.display === 'none') return { o: -1 };
      if (cs.visibility === 'hidden') oculto = true; o *= parseFloat(cs.opacity || '1'); e = e.parentElement; }
    return { o, oculto }; };
  const txt = (el) => (el.textContent || '').replace(/\s+/g, ' ').trim();
  const proprio = (el) => Array.from(el.childNodes).filter((n) => n.nodeType === 3).map((n) => n.nodeValue).join('').replace(/\s+/g, ' ').trim();
  const alfa = (c) => { const m = /rgba?\(([^)]+)\)/.exec(c || ''); if (!m) return c && c !== 'transparent' ? 1 : 0; const p = m[1].split(/[ ,/]+/).filter(Boolean); return p.length > 3 ? parseFloat(p[3]) : 1; };
  const R = [], F = [], A = [];
  const add = (lista, tipo, el, msg, r) => { const mesmos = lista.filter((x) => x.tipo === tipo); if (mesmos.length >= 3 || mesmos.some((x) => x.trecho === txt(el).slice(0, 50))) return;
    lista.push({ tipo, msg, trecho: txt(el).slice(0, 50), ...caixa(r || el.getBoundingClientRect()) }); };
  const els = Array.from(root.querySelectorAll('*')).filter((el) => !ign(el));
  const vis = els.filter((el) => naTela(el.getBoundingClientRect()));

  // ---- 1. enfeites ----
  const sombraDura = (v) => (v && v !== 'none') ? v.split(/,(?![^(]*\))/).some((s) => {
    const cor = (/rgba?\([^)]*\)/.exec(s) || ['rgb(0,0,0)'])[0]; const n = (s.replace(/rgba?\([^)]*\)/, '').match(/-?[\d.]+px/g) || []).map(parseFloat);
    return n.length >= 3 && n[2] === 0 && Math.max(Math.abs(n[0]), Math.abs(n[1])) >= 2 && alfa(cor) > 0.15 && !/inset/.test(s); }) : false;
  let titulo = null, tfs = 0;
  const tits = vis.filter((e) => e.getAttribute('data-role') === 'titulo');  // HTML de fora da skill: h1 e h2
  (tits.length ? tits : vis.filter((e) => /^h[12]$/i.test(e.tagName))).forEach((e) => { const f = fsOf(e); if (f > tfs) { tfs = f; titulo = e; } });
  const tr = titulo ? titulo.getBoundingClientRect() : null;
  for (const el of vis) {
    const cs = getComputedStyle(el), temTxt = txt(el).length > 0;
    if (temTxt && (/text/.test(cs.backgroundClip + cs.webkitBackgroundClip) && /gradient/.test(cs.backgroundImage)))
      add(R, 'texto em degradê', el, 'texto pintado com degradê (background-clip: text). Use cor chapada.');
    if (temTxt && el instanceof SVGElement && /^url\(/.test(cs.fill)) { const g = document.querySelector((/#[^")]+/.exec(cs.fill) || [''])[0] || 'x-nada');
      if (g && /gradient/i.test(g.tagName)) add(R, 'texto em degradê', el, 'texto SVG preenchido com degradê. Use cor chapada.'); }
    for (const pse of [null, '::before', '::after']) {
      const c2 = pse ? getComputedStyle(el, pse) : cs; if (pse && (c2.content === 'none' || c2.content === 'normal')) continue;
      if (sombraDura(c2.boxShadow) || sombraDura(c2.textShadow)) add(R, 'sombra dura', el, 'sombra sem desfoque e deslocada. Tire a sombra ou use uma sombra difusa e discreta.');
      if (/blur/.test((c2.backdropFilter || '') + (c2.webkitBackdropFilter || ''))) add(R, 'vidro fosco', el, 'backdrop-filter com blur (vidro fosco). Use campo de cor sólido.');
    }
    if (temTxt && !/table/.test(cs.display)) for (const [l, o] of [['Left', 'Right'], ['Right', 'Left']]) {
      const w = parseFloat(cs['border' + l + 'Width']) || 0;
      if (w > 1 && cs['border' + l + 'Style'] !== 'none' && alfa(cs['border' + l + 'Color']) > 0.15 && (parseFloat(cs['border' + o + 'Width']) || 0) <= 1
          && (parseFloat(cs.borderTopWidth) || 0) <= 1 && (parseFloat(cs.borderBottomWidth) || 0) <= 1)
        add(R, 'borda lateral', el, 'borda lateral colorida de ' + w + ' px num bloco de texto. Tire a faixa.');
    }
    const p = proprio(el), fs = fsOf(el);
    if (titulo && p.length >= 2 && !titulo.contains(el) && !el.contains(titulo)) {
      const lat = p.replace(/[^A-Za-zÀ-ÿ]/g, ''), caps = cs.textTransform === 'uppercase' || (lat.length >= 3 && lat === lat.toUpperCase());
      const ls = cs.letterSpacing === 'normal' ? 0 : parseFloat(cs.letterSpacing) / parseFloat(cs.fontSize);
      const r = el.getBoundingClientRect();
      if (caps && ls >= 0.05 && fs <= 0.5 * tfs && r.bottom <= tr.top + 0.25 * tfs && tr.top - r.bottom < 1.5 * tfs && r.right > tr.left && r.left < tr.right)
        add(R, 'rótulo acima do título', el, 'rótulo pequeno em caixa alta e espaçado logo acima do título. Tire o rótulo.');
    }
    if (/^0\d[.):]?$/.test(p) && fs >= 56) add(R, 'numeração decorativa', el, 'numeração grande do tipo 01, 02, 03. Tire o número.');
    if (p && /^[←-⇿■-◿•☀-➿⬀-⯿\u{1F000}-\u{1FAFF}️\s]{1,4}$/u.test(p)) add(R, 'emoji ou símbolo', el, 'caractere usado como ícone. Use imagem, desenho ou nada.');
  }
  const tw = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
  for (let n; (n = tw.nextNode());) {
    const el = n.parentElement; if (!el || ign(el)) continue;
    if (/[☀-➿\u{1F000}-\u{1FAFF}]/u.test(n.nodeValue)) { const rg = document.createRange(); rg.selectNodeContents(n); const r = rg.getBoundingClientRect();
      if (naTela(r)) add(R, 'emoji ou símbolo', el, 'emoji ou símbolo pictográfico no texto. Tire.', r); }
  }
  // ---- 2. estado final ----
  const tw2 = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
  for (let n; (n = tw2.nextNode());) {
    const el = n.parentElement; if (!el || ign(el) || !(n.nodeValue || '').trim()) continue;
    const rg = document.createRange(); rg.selectNodeContents(n); const r = rg.getBoundingClientRect(); if (!naTela(r)) continue;
    const o = opac(el); if (o.o < 0) continue;
    // rótulo e legenda esmaecidos de propósito (mapa de seções) só reprovam abaixo de 0,6. Entre 0,6 e 0,95 viram aviso.
    const sec = /^(rotulo|legenda)$/.test((el.closest('[data-role]') || el).getAttribute('data-role') || '');
    if (o.oculto || o.o < (sec ? 0.6 : 0.95)) add(F, 'texto inacabado', el, 'texto com opacidade ' + (o.oculto ? 'oculta' : o.o.toFixed(2)) + ' no estado final. A animação precisa terminar com o texto inteiro.', r);
    else if (o.o < 0.95) add(A, 'texto esmaecido', el, 'rótulo com opacidade ' + o.o.toFixed(2) + '. Prefira cor mais clara a opacidade.', r);
  }
  root.querySelectorAll('img,video,canvas').forEach((el) => { if (ign(el)) return; const r = el.getBoundingClientRect(); if (!naTela(r) || r.width * r.height < 6400) return;
    const o = opac(el); if (o.o >= 0 && (o.oculto || o.o < 0.3)) add(F, 'imagem apagada', el, 'imagem com opacidade ' + (o.oculto ? 'oculta' : o.o.toFixed(2)) + ' no estado final.'); });

  // ---- 3. avisos tipográficos ----
  const linhasDe = (el) => { const ls = []; const w = document.createTreeWalker(el, NodeFilter.SHOW_TEXT); const f = fsOf(el);
    for (let n; (n = w.nextNode());) { const re = /\S+/g; let m; while ((m = re.exec(n.nodeValue))) {
      const rg = document.createRange(); rg.setStart(n, m.index); rg.setEnd(n, m.index + m[0].length); const r = rg.getClientRects()[0]; if (!r || r.width < 1) continue;
      let L = ls.find((x) => Math.abs(x.top - r.top) < 0.5 * f); if (!L) { L = { top: r.top, bot: r.bottom, x0: r.left, x1: r.right, pal: 0, car: -1 }; ls.push(L); }
      L.pal++; L.car += m[0].length + 1; L.bot = Math.max(L.bot, r.bottom); L.x0 = Math.min(L.x0, r.left); L.x1 = Math.max(L.x1, r.right); } }
    return ls.sort((a, b) => a.top - b.top); };
  let corpos = vis.filter((e) => e.getAttribute('data-role') === 'corpo' && !e.querySelector('[data-role]') && txt(e));
  if (!corpos.length && !root.querySelector('[data-role]')) corpos = vis.filter((e) => /^(p|li)$/i.test(e.tagName) && !e.querySelector('p,li') && txt(e));
  const blocos = corpos.map((e) => ({ e, fs: fsOf(e), ls: linhasDe(e) })).filter((b) => b.ls.length);
  for (const b of blocos) {
    const cs = getComputedStyle(b.e), longa = Math.max(...b.ls.map((l) => l.car));
    if (longa > 65) add(A, 'linha longa', b.e, 'linha com ' + longa + ' caracteres (o olho se perde acima de cerca de 60).');
    const lh = parseFloat(cs.lineHeight) / parseFloat(cs.fontSize);
    const pal = b.ls.reduce((s, l) => s + l.pal, 0);
    if (b.ls.length >= 2 && pal >= 6 && lh < 1.15) add(A, 'entrelinha apertada', b.e, 'entrelinha de ' + lh.toFixed(2) + ' no corpo (mínimo 1,15).');
    if (b.ls.length >= 2 && pal >= 4 && b.ls[b.ls.length - 1].pal === 1) add(A, 'palavra sozinha', b.e, 'a última linha do item tem uma palavra só.');
  }
  for (const el of vis) { const p = proprio(el), role = (el.closest('[data-role]') || el).getAttribute('data-role');
    if (p.length < 25 || role === 'titulo' || role === 'numero') continue;
    const lat = p.replace(/[^A-Za-zÀ-ÿ]/g, '');
    if (lat.length >= 15 && (getComputedStyle(el).textTransform === 'uppercase' || lat === lat.toUpperCase())) add(A, 'caixa alta longa', el, 'trecho de ' + p.length + ' caracteres em caixa alta. Caixa alta longa cansa a leitura.'); }
  if (titulo && blocos.length) {
    const tl = linhasDe(titulo); const tb = tl.length ? Math.max(...tl.map((l) => l.bot)) : tr.bottom;
    const abaixo = blocos.filter((b) => b.ls[0].top >= tb - 4 && b.ls[0].x1 > tr.left && b.ls[0].x0 < tr.right).sort((a, b) => a.ls[0].top - b.ls[0].top);
    if (abaixo.length) { const c = abaixo[0], gap = c.ls[0].top - tb;
      const x0 = Math.min(tr.left, c.ls[0].x0), x1 = Math.max(tr.right, ...abaixo.map((b) => Math.max(...b.ls.map((l) => l.x1))));
      let fundo = tb; vis.forEach((e) => { if (e === root) return; const r = e.getBoundingClientRect(), t = e.tagName.toLowerCase();
        const conta = ['img', 'video', 'canvas', 'svg'].includes(t) ? !(r.width * r.height > 0.5 * W * H) : proprio(e).length > 0;
        if (conta && r.right > x0 && r.left < x1 && r.top >= tr.top - 2) fundo = Math.max(fundo, Math.min(r.bottom, H)); });
      const faixa = H - 64 - fundo;
      if (gap < 0.6 * c.fs && faixa > Math.max(1.5 * c.fs, 2 * gap)) add(A, 'respiro curto', c.e, 'título colado no corpo (' + Math.round(gap) + ' px) e faixa vazia de ' + Math.round(faixa) + ' px embaixo. Distribua o espaço.'); }
  }
  // quique: lê as curvas com o movimento ligado (html.sk-mov) e volta ao estado final em seguida
  const tinhaMov = doc.classList.contains('sk-mov'), tinhaFinal = doc.classList.contains('sk-final');
  doc.classList.add('sk-mov'); doc.classList.remove('sk-final');
  const quica = (v) => { let m; const re = /cubic-bezier\(([^)]+)\)/g;
    while ((m = re.exec(v || ''))) { const q = m[1].split(',').map(parseFloat); if (q[1] < 0 || q[1] > 1 || q[3] < 0 || q[3] > 1) return m[0]; }
    const l = /linear\(([^)]+)\)/.exec(v || ''); if (l && l[1].split(',').some((t) => { const x = parseFloat(t); return !/%/.test(t.trim().split(/\s+/)[0]) && (x > 1.001 || x < -0.001); })) return 'linear(...)';
    return null; };
  for (const el of els) { const cs = getComputedStyle(el), b = quica(cs.animationTimingFunction) || quica(cs.transitionTimingFunction);
    if (b) { add(R, 'quique', el, 'curva ' + b + ' passa do alvo e volta (quique). Use uma curva que só desacelera.'); } }
  if (!tinhaMov) doc.classList.remove('sk-mov'); if (tinhaFinal) doc.classList.add('sk-final');

  const seq = Array.from(root.querySelectorAll('[data-a]')).filter((e) => !e.ownerSVGElement).map((e) => e.getAttribute('data-a'))
    .filter((v, i, a) => i === 0 || v !== a[i - 1]).join('>');
  return { reprova: R, final: F, avisos: A, anim: seq };
}
"""


def sobreposicoes(items, escala=1.0):
    """Linhas de texto de blocos diferentes que se sobrepõem (texto em cima de texto)."""
    linhas = []
    for it in items:
        px = it.get("px") or 0
        for (x, y, w, h) in it.get("ls") or []:
            # a caixa da linha inclui o espaço reservado a acentos e descendentes, que é grande em fontes
            # enormes. Compara só a faixa central, onde ficam os traços das letras (70% do corpo da fonte).
            hb = min(h, 0.7 * px) if px else h
            linhas.append((it.get("b"), it["t"], x / escala, (y + (h - hb) / 2) / escala, w / escala, hb / escala, px / escala))
    achados = []
    for i in range(len(linhas)):
        bi, ti, xi, yi, wi, hi, pi = linhas[i]
        for j in range(i + 1, len(linhas)):
            bj, tj, xj, yj, wj, hj, pj = linhas[j]
            if bi == bj:
                continue
            ix = min(xi + wi, xj + wj) - max(xi, xj)
            iy = min(yi + hi, yj + hj) - max(yi, yj)
            if iy <= 0:
                continue
            if ix > 0 and iy > 0.3 * min(hi, hj) and ix * iy > 0.25 * min(wi * hi, wj * hj):
                achados.append({"a": ti[:40], "b": tj[:40], "x": round(max(xi, xj)), "y": round(max(yi, yj))})
            elif iy > 0.5 * min(hi, hj) and ix > -0.2 * min(pi or 40, pj or 40):
                # lado a lado na mesma altura, encostados ou quase (“AUTOVERIFICARREVISAR”): para o leitor vira uma palavra só
                achados.append({"a": ti[:40], "b": tj[:40], "x": round(max(xi, xj)), "y": round(max(yi, yj)), "tipo": "encostado"})
            if len(achados) >= 6:
                return achados
    return achados


def classificar_textos(items, lim=None, escala=1.0):
    """Aplica os pisos. escala converte px medidos para o palco de 1920 (W/1920)."""
    lim = {**LIMITES, **(lim or {})}
    problemas = []
    tot_chars = 0
    abaixo_corpo = 0
    min_px = None
    for it in items:
        px = it["px"] / escala
        it["px1920"] = round(px, 1)
        role = it.get("role") or ""
        if role in ("titulo", "numero"):
            piso = lim["piso_titulo"]
        elif role in ("legenda", "rotulo", "fonte", "credito", "nota-visual"):
            piso = lim["piso_qualquer_texto"]
        elif role == "referencia":
            piso = lim["piso_referencia"]
        elif role == "celula":
            piso = lim["piso_celula"]
        elif role == "corpo":
            piso = lim["piso_corpo"]
        elif it["n"] >= lim["caracteres_para_ser_corpo"]:
            piso = lim["piso_corpo"]
            role = role or "corpo"
        else:
            piso = lim["piso_qualquer_texto"]
            role = role or "curto"
        it["papel"] = role
        it["piso"] = piso
        tot_chars += it["n"]
        if role == "corpo" and px < lim["piso_corpo"]:
            abaixo_corpo += it["n"]
        if min_px is None or px < min_px:
            min_px = px
        if px + 0.5 < piso:
            problemas.append({"trecho": it["t"], "papel": role, "px": round(px, 1), "piso": piso,
                              "x": it["x"], "y": it["y"], "w": it["w"], "h": it["h"]})
    corpo = sorted([it["px1920"] for it in items if it["papel"] == "corpo"])
    mediana_corpo = corpo[len(corpo) // 2] if corpo else None
    titulos = [it["px1920"] for it in items if it["papel"] == "titulo"]
    return {
        "min_px": round(min_px, 1) if min_px is not None else None,
        "mediana_corpo_px": mediana_corpo,
        "titulo_px": max(titulos) if titulos else None,
        "fracao_texto_abaixo_do_corpo": round(abaixo_corpo / tot_chars, 3) if tot_chars else 0.0,
        "palavras": sum(len(it["t"].split()) for it in items if it["papel"] not in ("legenda", "rotulo", "credito", "fonte")),
        "problemas_fonte": problemas,
        "fontes_ok": not problemas,
    }


def _maior_retangulo(mat):
    """Maior retângulo de 1s numa matriz binária (lista de listas). Devolve (area, r0, c0, r1, c1)."""
    if not mat:
        return (0, 0, 0, 0, 0)
    cols = len(mat[0])
    alt = [0] * cols
    best = (0, 0, 0, 0, 0)
    for r, row in enumerate(mat):
        for c in range(cols):
            alt[c] = alt[c] + 1 if row[c] else 0
        stack = []
        for c in range(cols + 1):
            h = alt[c] if c < cols else 0
            start = c
            while stack and stack[-1][1] >= h:
                s, hh = stack.pop()
                area = hh * (c - s)
                if area > best[0]:
                    best = (area, r - hh + 1, s, r, c - 1)
                start = s
            stack.append((start, h))
    return best


def ocupacao(png_path, lim=None, visuais=None):
    """Mede a ocupação a partir da captura (o que o olho vê).

    visuais: retângulos [x, y, w, h] de imagens e desenhos. Céu liso de uma fotografia é imagem,
    não área morta, então essas células contam como ocupadas."""
    import numpy as np
    from PIL import Image

    lim = {**LIMITES, **(lim or {})}
    im = Image.open(png_path).convert("RGB")
    if im.size != (1920, 1080):
        im = im.resize((1920, 1080), Image.BILINEAR)
    a = np.asarray(im).astype(np.float32)
    mx, my, cs = lim["margem_x"], lim["margem_y"], lim["celula"]
    area = a[my:1080 - my, mx:1920 - mx]
    rows = area.shape[0] // cs
    cols = area.shape[1] // cs
    area = area[: rows * cs, : cols * cs]
    cells = area.reshape(rows, cs, cols, cs, 3).transpose(0, 2, 1, 3, 4).reshape(rows, cols, cs * cs, 3)
    lum = cells @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
    std = lum.std(axis=2)
    p95 = np.percentile(lum, 97, axis=2) - np.percentile(lum, 3, axis=2)
    mean = cells.mean(axis=2)
    lisa = (std < 6.0) & (p95 < 22)
    # cor de fundo = cor mais frequente entre as células lisas (quantizada)
    if lisa.any():
        q = (mean[lisa] / 12).round().astype(int)
        keys, counts = np.unique(q, axis=0, return_counts=True)
        bg = keys[counts.argmax()] * 12.0
    else:
        bg = np.array([0, 0, 0], dtype=np.float32)
    dist = np.sqrt(((mean - bg) ** 2).sum(axis=2))
    # Toda área lisa conta como vazia, seja da cor do fundo ou de um campo chapado sem nada dentro.
    # Imagens e desenhos (retângulos em "visuais") nunca contam como vazios.
    vazia_bruta = lisa.copy()
    for (vx, vy, vw, vh) in (visuais or []):
        c0 = max(0, int((vx - mx) // cs)); c1 = min(cols - 1, int((vx + vw - mx - 1) // cs))
        r0 = max(0, int((vy - my) // cs)); r1 = min(rows - 1, int((vy + vh - my - 1) // cs))
        if c1 >= c0 and r1 >= r0:
            vazia_bruta[r0:r1 + 1, c0:c1 + 1] = False
    superficie = lisa & (dist >= 22)
    # Fechamento morfológico: o espaço entre linhas e entre bullets (até ~2 células)
    # faz parte do bloco de texto e não conta como tela vazia.
    occ = ~vazia_bruta

    def _dil(m):
        o = m.copy()
        o[1:, :] |= m[:-1, :]; o[:-1, :] |= m[1:, :]
        o[:, 1:] |= m[:, :-1]; o[:, :-1] |= m[:, 1:]
        return o

    def _ero(m):
        o = m.copy()
        o[1:, :] &= m[:-1, :]; o[:-1, :] &= m[1:, :]
        o[:, 1:] &= m[:, :-1]; o[:, :-1] &= m[:, 1:]
        return o

    fechado = _ero(_dil(occ))
    vazia = ~(fechado | occ)
    frac_vazia = float(vazia.mean())
    area_r, r0, c0, r1, c1 = _maior_retangulo(vazia.tolist())
    maior = area_r / float(rows * cols)
    ocup = ~vazia
    if ocup.any():
        rr = np.where(ocup.any(axis=1))[0]
        cc = np.where(ocup.any(axis=0))[0]
        ext_x = (cc.max() - cc.min() + 1) / cols
        ext_y = (rr.max() - rr.min() + 1) / rows
    else:
        ext_x = ext_y = 0.0
    ok = (frac_vazia <= lim["max_fracao_vazia"] and maior <= lim["max_maior_vazio"]
          and ext_x >= lim["min_extensao_x"] and ext_y >= lim["min_extensao_y"])
    return {
        "fracao_vazia": round(frac_vazia, 3),
        "maior_vazio": round(maior, 3),
        "maior_vazio_px": [int(mx + c0 * cs), int(my + r0 * cs), int((c1 - c0 + 1) * cs), int((r1 - r0 + 1) * cs)] if area_r else None,
        "extensao_x": round(float(ext_x), 3),
        "extensao_y": round(float(ext_y), 3),
        "fracao_superficie_lisa": round(float(superficie.mean()), 3),
        "tela_ocupada": bool(ok),
        "grade_vazia": vazia.astype(int).tolist(),
        "grade": {"mx": mx, "my": my, "cel": cs, "linhas": int(rows), "colunas": int(cols)},
    }


def sobrepor(png_path, out_path, medida_oc, problemas_fonte=None):
    """Gera uma imagem com o vazio em vermelho e os textos pequenos destacados."""
    from PIL import Image, ImageDraw

    im = Image.open(png_path).convert("RGB")
    if im.size != (1920, 1080):
        im = im.resize((1920, 1080))
    ov = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    g = medida_oc["grade"]
    for r, row in enumerate(medida_oc["grade_vazia"]):
        for c, v in enumerate(row):
            if v:
                x = g["mx"] + c * g["cel"]
                y = g["my"] + r * g["cel"]
                d.rectangle([x, y, x + g["cel"] - 1, y + g["cel"] - 1], fill=(220, 40, 40, 70))
    if medida_oc.get("maior_vazio_px"):
        x, y, w, h = medida_oc["maior_vazio_px"]
        d.rectangle([x, y, x + w, y + h], outline=(220, 30, 30, 255), width=6)
    for p in problemas_fonte or []:
        d.rectangle([p["x"] - 4, p["y"] - 4, p["x"] + p["w"] + 4, p["y"] + p["h"] + 4], outline=(255, 170, 0, 255), width=5)
    d.rectangle([0, 0, 1919, 1079], outline=(0, 0, 0, 0))
    out = Image.alpha_composite(im.convert("RGBA"), ov).convert("RGB")
    out.save(out_path, quality=88)
    return out_path


def px_para_pt(px):
    return round(px / 2.0, 1)
