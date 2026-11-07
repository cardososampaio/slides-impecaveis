/* slides-impecaveis · motor
   Lê window.SK_DECK (gerado por scripts/construir.py), monta os slides, ajusta as fontes
   sem descer dos pisos, anima o slide ativo e cuida da navegação.
   API para scripts: window.SK = { total, ir(i), final(bool), info(), pronto } */
(function () {
  'use strict';
  const D = window.SK_DECK;
  const doc = document.documentElement;
  const PISO = Object.assign({ titulo: 64, corpo: 44, qualquer: 28 }, D.pisos || {});
  const Q = new URLSearchParams(location.search);
  let FINAL = Q.has('final') || Q.has('sk-final');

  // ------------------------------------------------------------------ utilidades
  const esc = (s) => String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  function md(s) { // **negrito** e *itálico*, sem mexer no texto
    return esc(s).replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>').replace(/(^|[^*])\*(?!\s)(.+?)\*(?!\*)/g, '$1<em>$2</em>');
  }
  function marcar(html, frases) {
    (frases || []).forEach((f) => {
      const e = esc(f);
      const i = html.indexOf(e);
      if (i >= 0) html = html.slice(0, i) + '<mark>' + e + '</mark>' + html.slice(i + e.length);
    });
    return html;
  }
  function rng(seed) { let s = (seed || 7) >>> 0; return () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296); }
  const f1 = (n) => Math.round(n * 10) / 10;
  function lum(hex) {
    const h = hex.replace('#', '');
    const c = [0, 2, 4].map((i) => parseInt(h.substr(i, 2), 16) / 255).map((v) => (v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4)));
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2];
  }
  function contraste(a, b) { const x = lum(a), y = lum(b); return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05); }
  function cssVar(n) { return getComputedStyle(doc).getPropertyValue(n).trim(); }
  function quebra(txt, n) { // quebra rótulos de SVG em linhas de até n caracteres
    const w = String(txt).split(/\s+/); const l = []; let a = '';
    w.forEach((p) => { if ((a + ' ' + p).trim().length > n && a) { l.push(a); a = p; } else a = (a + ' ' + p).trim(); });
    if (a) l.push(a); return l;
  }
  function svgTexto(x, y, txt, tam, opt) {
    opt = opt || {}; const linhas = opt.n ? quebra(txt, opt.n) : [String(txt)]; const lh = tam * (opt.lh || 1.15);
    const y0 = opt.meio ? y - ((linhas.length - 1) * lh) / 2 : y;
    return '<text data-role="' + (opt.papel || 'rotulo') + '" data-txt x="' + f1(x) + '" y="' + f1(y0) + '" font-size="' + tam + '" text-anchor="' + (opt.a || 'start') + '" fill="' + (opt.cor || 'currentColor') +
      '" font-weight="' + (opt.w || 400) + '" font-family="' + (opt.f || 'var(--f-corpo)') + '"' + (opt.anim ? ' data-a="aparece" style="--d:' + opt.anim + 'ms"' : '') + '>' +
      linhas.map((ln, i) => '<tspan x="' + f1(x) + '" dy="' + (i ? lh : 0) + '">' + esc(ln) + '</tspan>').join('') + '</text>';
  }

  // ------------------------------------------------------------------ tema, seções, campos
  doc.dataset.tema = D.tema || 'tabuleiro';
  // intensidade do movimento: sobrio, padrao ou vivo (o estado final não muda)
  const INTENS = ['sobrio', 'padrao', 'vivo'];
  doc.dataset.intensidade = INTENS.includes(D.intensidade) ? D.intensidade : 'padrao';
  doc.lang = D.idioma || 'pt-BR';
  const SLIDES = D.slides || [];
  const SECOES = (D.secoes && D.secoes.length) ? D.secoes.slice().sort((a, b) => a.inicio - b.inicio) : [{ nome: D.titulo || '', inicio: 1 }];
  function secaoDe(i) { let k = 0; SECOES.forEach((s, j) => { if (i + 1 >= s.inicio) k = j; }); return k; }
  let CAMPOS = [];
  function campos() {
    CAMPOS = cssVar('--campos').split(',').map((s) => s.trim()).filter(Boolean);
    if (!CAMPOS.length) CAMPOS = ['#2A4D71'];
  }
  function corCampo(k) { return (SECOES[k] && SECOES[k].campo) || CAMPOS[k % CAMPOS.length]; }
  function sobre(campo) {
    const claro = '#F6F1E7', escuro = cssVar('--tinta') || '#1C2632';
    const c1 = contraste(campo, claro), c2 = contraste(campo, escuro.startsWith('#') ? escuro : '#1C2632');
    return c1 >= c2 ? [claro, 'rgba(246,241,231,.86)'] : [escuro, escuro];
  }

  // ------------------------------------------------------------------ imagens e artes
  let SLIDE_ATUAL = null;
  // morph: "morph": "id" liga a imagem principal ao slide vizinho com o mesmo id; true liga à do slide seguinte com a mesma imagem
  function morphId(k) {
    const s = SLIDE_ATUAL; if (!s || s.imagem !== k) return '';
    if (typeof s.morph === 'string') return s.morph;
    const a = SLIDES[SLIDES.indexOf(s) - 1];
    return s.morph === true || (a && a.morph === true && a.imagem === k) ? 'img-' + k : '';
  }
  function img(chave, opt) {
    opt = opt || {};
    const im = (D.imagens || {})[chave];
    if (!im) return '';
    // legenda sobre a imagem só quando a pessoa pede (deck, slide ou imagem). O crédito vai sempre para a tecla I.
    const pede = D.legendas_nas_imagens === true || (SLIDE_ATUAL && SLIDE_ATUAL.legendas === true) || im.mostrar_legenda === true;
    const leg = opt.semLegenda || !pede ? '' : (im.legenda ? '<figcaption data-role="legenda" data-txt>' + im.legenda + '</figcaption>' : '');
    const mid = morphId(chave);
    // retrato (pessoa: true, marcado pelo construtor): sem foco declarado, o recorte guarda o terço de cima, onde fica o rosto
    return '<figure class="sk-fig' + (im.conter || opt.conter ? ' sk-conter' : '') + (opt.cls ? ' ' + opt.cls : '') + '"' + (mid ? ' data-morph="' + esc(mid) + '"' : '') + (im.pessoa ? ' data-pessoa="' + esc(chave) + '"' : '') + ' data-a="' + (opt.a || 'foco') + '" style="--d:' + (opt.d || 150) + 'ms;--foco:' + ((SLIDE_ATUAL && SLIDE_ATUAL.imagem === chave && SLIDE_ATUAL.foco_imagem) || opt.foco || im.foco || (im.pessoa ? '50% 22%' : '50% 50%')) + '">' +
      '<img src="' + (im.dados || im.arquivo) + '" alt="' + esc(im.alt || im.legenda_texto || '') + '">' + leg + '</figure>';
  }
  const ARTES = {
    tabuleiro(W, H, r) {
      let s = ''; const cel = 120; const cols = Math.ceil(W / cel), rows = Math.ceil(H / cel);
      for (let y = 0; y < rows; y++) for (let x = 0; x < cols; x++) {
        const v = r(); const op = v < 0.18 ? 0.34 : v < 0.5 ? 0.16 : 0.07;
        s += '<rect x="' + (x * cel + 8) + '" y="' + (y * cel + 8) + '" width="' + (cel - 16) + '" height="' + (cel - 16) + '" rx="14" fill="var(--sobre-campo)" opacity="' + op + '" data-a="aparece" style="--d:' + Math.round(r() * 700) + 'ms"/>';
      }
      for (let k = 0; k < 6; k++) {
        const x = (Math.floor(r() * cols) + 0.5) * cel, y = (Math.floor(r() * rows) + 0.85) * cel, h = 74;
        s += '<g data-a="pousa" style="--d:' + (500 + k * 140) + 'ms"><path d="M' + (x - 26) + ' ' + y + 'h52l-9-12h-6l-8-30a15 15 0 1 0-6 0l-8 30h-6z" fill="' + (k % 2 ? 'var(--marca)' : 'var(--sobre-campo)') + '" transform="translate(0,' + (-h * 0.0) + ')"/></g>';
      }
      return s;
    },
    gravura(W, H, r) {
      const cx = W * (0.35 + r() * 0.3), cy = H * (0.4 + r() * 0.2); let s = '';
      for (let k = 1; k < 14; k++) s += '<circle cx="' + f1(cx) + '" cy="' + f1(cy) + '" r="' + (k * 46) + '" fill="none" stroke="var(--sobre-campo)" stroke-width="' + (k % 4 ? 1.2 : 3) + '" opacity="' + (k % 4 ? 0.35 : 0.6) + '" data-a="traco" style="--comp:' + Math.round(2 * Math.PI * k * 46) + ';--d:' + (k * 60) + 'ms"/>';
      for (let a = 0; a < 48; a++) { const t = (a / 48) * Math.PI * 2; s += '<line x1="' + f1(cx) + '" y1="' + f1(cy) + '" x2="' + f1(cx + Math.cos(t) * 2400) + '" y2="' + f1(cy + Math.sin(t) * 2400) + '" stroke="var(--sobre-campo)" stroke-width="' + (a % 6 ? 0.8 : 2) + '" opacity="' + (a % 6 ? 0.22 : 0.4) + '"/>'; }
      for (let y = 0; y < H; y += 9) s += '<line x1="0" y1="' + y + '" x2="' + W + '" y2="' + (y + W * 0.18) + '" stroke="var(--sobre-campo)" stroke-width=".7" opacity=".09"/>';
      return s;
    },
    editorial(W, H, r, ctx) {
      const letra = esc(((ctx && ctx.letra) || 'A').charAt(0).toUpperCase());
      const tam = Math.round(Math.min(H * 0.92, W * 1.15)), base = H * 0.5 + tam * 0.36;
      let s = '';
      for (let y = 18; y < H; y += 26) s += '<line x1="0" y1="' + y + '" x2="' + W + '" y2="' + y + '" stroke="var(--sobre-campo)" stroke-width="1.2" opacity=".10"/>';
      s += '<rect x="0" y="' + f1(H * 0.78) + '" width="' + W + '" height="' + Math.max(10, Math.round(H * 0.022)) + '" fill="var(--acento)" data-a="cresce-x" style="--d:300ms"/>';
      s += '<text x="' + f1(W * 0.5) + '" y="' + f1(base) + '" font-family="var(--f-titulo)" font-weight="700" font-size="' + tam + '" text-anchor="middle" fill="none" stroke="var(--sobre-campo)" stroke-width="' + Math.max(3, Math.round(tam / 120)) + '" opacity=".6" data-sk-ignore data-a="aparece" style="--d:100ms">' + letra + '</text>';
      return s;
    },
    noturno(W, H, r) {
      let s = ''; const pts = [];
      for (let k = 0; k < 260; k++) {
        const x = r() * W, y = r() * H, rr = r() < 0.08 ? 3.4 : r() < 0.3 ? 2 : 1.2; pts.push([x, y]);
        s += '<circle class="sk-particula" cx="' + f1(x) + '" cy="' + f1(y) + '" r="' + rr + '" fill="' + (r() < 0.12 ? 'var(--acento)' : 'var(--tinta)') + '" opacity=".75" style="--dx:' + f1((r() - 0.5) * 18) + 'px;--dy:' + f1((r() - 0.5) * 18) + 'px;--t-der:' + f1(5 + r() * 6) + 's;--t-pul:' + f1(3 + r() * 4) + 's"/>';
      }
      for (let k = 0; k < 22; k++) { const a = pts[Math.floor(r() * pts.length)], b = pts[Math.floor(r() * pts.length)]; if (Math.hypot(a[0] - b[0], a[1] - b[1]) < 260) s += '<line x1="' + f1(a[0]) + '" y1="' + f1(a[1]) + '" x2="' + f1(b[0]) + '" y2="' + f1(b[1]) + '" stroke="var(--acento)" stroke-width="1.4" opacity=".45" data-a="traco" style="--comp:300;--d:' + (300 + k * 50) + 'ms"/>'; }
      const cx = W * 0.5, cy = H * 0.5;
      for (let k = 0; k < 90; k++) { const t = (k / 90) * Math.PI * 2; s += '<circle cx="' + f1(cx + Math.cos(t) * W * 0.32) + '" cy="' + f1(cy + Math.sin(t) * H * 0.2) + '" r="3" fill="var(--acento)" opacity=".9" data-a="aparece" style="--d:' + (k * 14) + 'ms"/>'; }
      return s;
    },
    datilografo(W, H, r) {
      let s = '';
      for (let k = 0; k < 3; k++) {
        const w = W * 0.72, h = H * 0.42, x = W * 0.14 + (r() - 0.5) * 40, y = H * 0.12 + k * H * 0.24, g = (r() - 0.5) * 7;
        s += '<g transform="rotate(' + f1(g) + ' ' + f1(x + w / 2) + ' ' + f1(y + h / 2) + ')" data-a="pousa" style="--d:' + (k * 180) + 'ms"><rect x="' + f1(x) + '" y="' + f1(y) + '" width="' + f1(w) + '" height="' + f1(h) + '" fill="#FBF8F1" stroke="rgba(31,42,68,.18)"/>' +
          '<line x1="' + f1(x) + '" y1="' + f1(y + 70) + '" x2="' + f1(x + w) + '" y2="' + f1(y + 70) + '" stroke="#B23A2B" stroke-width="3" opacity=".7"/>';
        for (let l = 1; l < 6; l++) s += '<line x1="' + f1(x + 30) + '" y1="' + f1(y + 70 + l * 52) + '" x2="' + f1(x + w - 30 - r() * 160) + '" y2="' + f1(y + 70 + l * 52) + '" stroke="#4F7CAC" stroke-width="2" opacity=".45"/>';
        s += '</g>';
      }
      s += '<circle cx="' + f1(W * 0.74) + '" cy="' + f1(H * 0.8) + '" r="96" fill="none" stroke="#B23A2B" stroke-width="10" opacity=".75" data-a="aparece" style="--d:900ms"/>';
      return s;
    },
    cartografico(W, H, r) {
      let s = ''; const SC = 'stroke="var(--sobre-campo)"';
      for (let k = 0; k <= 12; k++) { const x = W * k / 12; s += '<path d="M' + f1(x) + ' 0Q' + f1(x + (k - 6) * W * 0.014) + ' ' + f1(H / 2) + ' ' + f1(x) + ' ' + H + '" fill="none" ' + SC + ' stroke-width="1.2" opacity=".18"/>'; }
      for (let k = 0; k <= 8; k++) { const y = H * k / 8; s += '<path d="M0 ' + f1(y) + 'Q' + f1(W / 2) + ' ' + f1(y - H * 0.05) + ' ' + W + ' ' + f1(y) + '" fill="none" ' + SC + ' stroke-width="1.2" opacity=".18"/>'; }
      for (let k = 0; k < 3; k++) {
        const a = [W * (0.05 + r() * 0.3), H * (0.25 + r() * 0.6)], b = [W * (0.5 + r() * 0.42), H * (0.2 + r() * 0.7)];
        const topo = Math.min(a[1], b[1]) - H * (0.1 + r() * 0.2), comp = Math.round(Math.hypot(b[0] - a[0], b[1] - a[1]) * 1.5);
        s += '<path d="M' + f1(a[0]) + ' ' + f1(a[1]) + 'C' + f1(a[0] + (b[0] - a[0]) * 0.3) + ' ' + f1(topo) + ' ' + f1(a[0] + (b[0] - a[0]) * 0.7) + ' ' + f1(topo + H * 0.1) + ' ' + f1(b[0]) + ' ' + f1(b[1]) + '" fill="none" ' + SC + ' stroke-width="3" stroke-linecap="round" opacity=".7" data-a="traco" style="--comp:' + comp + ';--d:' + (200 + k * 300) + 'ms"/>';
        for (const p of [a, b]) s += '<circle cx="' + f1(p[0]) + '" cy="' + f1(p[1]) + '" r="9" fill="var(--sobre-campo)" opacity=".85" data-a="aparece" style="--d:' + (k * 300) + 'ms"/>';
      }
      const cx = W * 0.74, cy = H * 0.34, R = Math.min(W, H) * 0.26;
      s += '<g data-a="aparece" style="--d:300ms"><circle cx="' + f1(cx) + '" cy="' + f1(cy) + '" r="' + f1(R) + '" fill="none" ' + SC + ' stroke-width="2" opacity=".5"/><circle cx="' + f1(cx) + '" cy="' + f1(cy) + '" r="' + f1(R * 0.84) + '" fill="none" ' + SC + ' stroke-width="1.2" opacity=".4"/>';
      for (let i = 0; i < 32; i++) { const t = i / 32 * Math.PI * 2, r0 = i % 4 ? R * 0.92 : R * 0.84; s += '<line x1="' + f1(cx + Math.cos(t) * r0) + '" y1="' + f1(cy + Math.sin(t) * r0) + '" x2="' + f1(cx + Math.cos(t) * R) + '" y2="' + f1(cy + Math.sin(t) * R) + '" ' + SC + ' stroke-width="1.5" opacity=".5"/>'; }
      for (let i = 0; i < 8; i++) {
        const t = i * Math.PI / 4 - Math.PI / 2, L = i % 2 ? R * 0.5 : R * 0.98, w = i % 2 ? R * 0.06 : R * 0.1;
        const tip = [cx + Math.cos(t) * L, cy + Math.sin(t) * L], l = [cx + Math.cos(t - Math.PI / 2) * w, cy + Math.sin(t - Math.PI / 2) * w], d = [cx + Math.cos(t + Math.PI / 2) * w, cy + Math.sin(t + Math.PI / 2) * w];
        s += '<path d="M' + f1(cx) + ' ' + f1(cy) + 'L' + f1(l[0]) + ' ' + f1(l[1]) + 'L' + f1(tip[0]) + ' ' + f1(tip[1]) + 'Z" fill="var(--sobre-campo)" opacity=".8"/><path d="M' + f1(cx) + ' ' + f1(cy) + 'L' + f1(d[0]) + ' ' + f1(d[1]) + 'L' + f1(tip[0]) + ' ' + f1(tip[1]) + 'Z" fill="var(--sobre-campo)" opacity=".32"/>';
      }
      return s + '</g>';
    },
    floresta(W, H, r) {
      let s = ''; const M = Math.max(W, H);
      [[W * (0.25 + r() * 0.15), H * (0.5 + r() * 0.2)], [W * (0.68 + r() * 0.15), H * (0.3 + r() * 0.2)]].forEach((c, ci) => {
        const p1 = r() * 6, p2 = r() * 6;
        for (let k = 1; k <= 13; k++) {
          const R = k * M * 0.032; let d = '';
          for (let j = 0; j <= 72; j++) { const t = j / 72 * Math.PI * 2, rr = R * (1 + 0.14 * Math.sin(3 * t + p1 + k * 0.18) + 0.07 * Math.sin(5 * t + p2)); d += (j ? 'L' : 'M') + f1(c[0] + Math.cos(t) * rr * 1.25) + ' ' + f1(c[1] + Math.sin(t) * rr); }
          s += '<path d="' + d + 'Z" fill="none" stroke="var(--sobre-campo)" stroke-width="' + (k % 5 ? 1.5 : 3) + '" opacity="' + (k % 5 ? 0.32 : 0.6) + '" data-a="traco" style="--comp:' + Math.round(R * 8.5) + ';--d:' + (ci * 250 + k * 70) + 'ms"/>';
        }
      });
      return s;
    },
    risografia(W, H, r) {
      let s = ''; const st = 28, cx = W * (0.55 + r() * 0.2), cy = H * (0.45 + r() * 0.15), m = Math.min(W, H);
      s += '<circle cx="' + f1(cx + 16) + '" cy="' + f1(cy - 12) + '" r="' + f1(m * 0.34) + '" fill="var(--sobre-campo)" opacity=".13" data-a="aparece"/>';
      for (let y = st / 2, j = 0; y < H; y += st, j++) {
        let row = '';
        for (let x = st / 2 + (j % 2) * st / 2; x < W; x += st) {
          const i = Math.max(0, 1 - Math.hypot(x - cx, y - cy) / (m * 0.6)), dg = Math.max(0, (x / W + 1 - y / H) / 2 - 0.3);
          const rad = st * 0.47 * Math.min(1, Math.max(i, dg * 0.9));
          if (rad > 1.4) row += '<circle cx="' + f1(x) + '" cy="' + f1(y) + '" r="' + f1(rad) + '"/>';
        }
        if (row) s += '<g fill="var(--sobre-campo)" opacity=".55" data-a="aparece" style="--d:' + Math.min(900, j * 30) + 'ms">' + row + '</g>';
      }
      return s;
    },
    prancheta(W, H, r) {
      let s = ''; const SC = 'stroke="var(--sobre-campo)" fill="none"';
      for (let x = 48; x < W; x += 48) s += '<line x1="' + x + '" y1="0" x2="' + x + '" y2="' + H + '" ' + SC + ' stroke-width="1" opacity=".1"/>';
      for (let y = 48; y < H; y += 48) s += '<line x1="0" y1="' + y + '" x2="' + W + '" y2="' + y + '" ' + SC + ' stroke-width="1" opacity=".1"/>';
      const cs = [[W * (0.26 + r() * 0.1), H * 0.64], [W * (0.66 + r() * 0.1), H * 0.4]], m = Math.min(W, H);
      s += '<line x1="0" y1="' + f1(cs[0][1] + (cs[0][1] - cs[1][1]) / (cs[1][0] - cs[0][0]) * cs[0][0]) + '" x2="' + W + '" y2="' + f1(cs[0][1] - (cs[0][1] - cs[1][1]) / (cs[1][0] - cs[0][0]) * (W - cs[0][0])) + '" ' + SC + ' stroke-width="1.5" stroke-dasharray="22 8 4 8" opacity=".45"/>';
      cs.forEach((c, ci) => {
        [0.3, 0.46, 0.62].forEach((f, k) => {
          const R = m * f, a0 = (ci ? 2.3 : -0.9) + r() * 0.4, a1 = a0 + 2.1;
          s += '<path d="M' + f1(c[0] + Math.cos(a0) * R) + ' ' + f1(c[1] + Math.sin(a0) * R) + 'A' + f1(R) + ' ' + f1(R) + ' 0 0 1 ' + f1(c[0] + Math.cos(a1) * R) + ' ' + f1(c[1] + Math.sin(a1) * R) + '" ' + SC + ' stroke-width="' + (k === 1 ? 3 : 1.6) + '" opacity="' + (k === 1 ? 0.75 : 0.45) + '" data-a="traco" style="--comp:' + Math.round(R * 2.2) + ';--d:' + (ci * 300 + k * 160) + 'ms"/>';
        });
        s += '<circle cx="' + f1(c[0]) + '" cy="' + f1(c[1]) + '" r="10" ' + SC + ' stroke-width="2.5" opacity=".8"/><path d="M' + f1(c[0] - 26) + ' ' + f1(c[1]) + 'h52M' + f1(c[0]) + ' ' + f1(c[1] - 26) + 'v52" ' + SC + ' stroke-width="2" opacity=".8"/>';
      });
      const y = H * 0.88, x0 = W * 0.1, x1 = W * 0.9;
      s += '<g data-a="aparece" style="--d:700ms"><path d="M' + f1(x0) + ' ' + f1(y) + 'H' + f1(x1) + 'M' + f1(x0) + ' ' + f1(y - 22) + 'v44M' + f1(x1) + ' ' + f1(y - 22) + 'v44" ' + SC + ' stroke-width="2" opacity=".7"/>' +
        '<path d="M' + f1(x0) + ' ' + f1(y) + 'l26 -9v18zM' + f1(x1) + ' ' + f1(y) + 'l-26 -9v18z" fill="var(--sobre-campo)" opacity=".7"/></g>';
      return s;
    },
    porcelana(W, H) {
      let s = ''; const R = 64;
      for (let j = 0, y = 0; y < H + R * 2; j++, y += R / 2) {
        let row = '';
        for (let x = (j % 2) * R - R; x < W + R; x += 2 * R) row += '<circle cx="' + x + '" cy="' + y + '" r="' + R + '" fill="var(--campo)"/><circle cx="' + x + '" cy="' + y + '" r="' + R * 0.7 + '" fill="none"/><circle cx="' + x + '" cy="' + y + '" r="' + R * 0.4 + '" fill="none"/>';
        s += '<g stroke="var(--sobre-campo)" stroke-width="1.6" stroke-opacity=".3" data-a="aparece" style="--d:' + Math.min(900, j * 28) + 'ms">' + row + '</g>';
      }
      return s;
    },
    kraft(W, H, r) {
      let s = '<rect x="28" y="28" width="' + (W - 56) + '" height="' + (H - 56) + '" fill="none" stroke="var(--sobre-campo)" stroke-width="3" stroke-dasharray="18 12" opacity=".4"/>';
      for (let k = 0; k < 2; k++) {
        const w = W * 0.3, h = H * 0.3, x = W * (0.1 + k * 0.38) + r() * 30, y = H * (0.45 - k * 0.22) + r() * 30, g = (k ? 7 : -6), n = Math.min(w, h) * 0.2;
        s += '<g transform="rotate(' + g + ' ' + f1(x + w / 2) + ' ' + f1(y + h / 2) + ')" data-a="pousa" style="--d:' + (200 + k * 200) + 'ms"><path d="M' + f1(x + n) + ' ' + f1(y) + 'H' + f1(x + w) + 'V' + f1(y + h) + 'H' + f1(x + n) + 'L' + f1(x) + ' ' + f1(y + h - n) + 'V' + f1(y + n) + 'Z" fill="var(--sobre-campo)" fill-opacity=".12" stroke="var(--sobre-campo)" stroke-width="3" opacity=".7"/>' +
          '<circle cx="' + f1(x + n * 0.9) + '" cy="' + f1(y + h / 2) + '" r="' + f1(n * 0.28) + '" fill="none" stroke="var(--sobre-campo)" stroke-width="3" opacity=".7"/></g>';
      }
      for (let k = 0; k < 2; k++) {
        const y0 = H * (0.2 + r() * 0.2), y1 = H * (0.6 + r() * 0.25), d = 'M-20 ' + f1(y0) + 'C' + f1(W * 0.35) + ' ' + f1(y0 + H * 0.3) + ' ' + f1(W * 0.6) + ' ' + f1(y1 - H * 0.35) + ' ' + (W + 20) + ' ' + f1(y1);
        s += '<path d="' + d + '" fill="none" stroke="var(--sobre-campo)" stroke-width="4" opacity=".55" data-a="traco" style="--comp:' + Math.round(W * 1.5) + ';--d:' + (k * 250) + 'ms"/><path d="' + d + '" transform="translate(0,7)" fill="none" stroke="var(--sobre-campo)" stroke-width="2" opacity=".3"/>';
      }
      const cx = W * 0.78, cy = H * 0.26, R = Math.min(W, H) * 0.14;
      s += '<g data-a="aparece" style="--d:700ms" fill="none" stroke="var(--sobre-campo)" opacity=".6"><circle cx="' + f1(cx) + '" cy="' + f1(cy) + '" r="' + f1(R) + '" stroke-width="5"/><circle cx="' + f1(cx) + '" cy="' + f1(cy) + '" r="' + f1(R * 0.8) + '" stroke-width="2"/>';
      for (let k = -2; k <= 2; k++) { let d = ''; for (let x = 0; x <= R * 2.6; x += 10) d += (x ? 'L' : 'M') + f1(cx - R * 2.9 + x) + ' ' + f1(cy + k * R * 0.32 + Math.sin(x / 18) * 6); s += '<path d="' + d + '" stroke-width="3"/>'; }
      return s + '</g>';
    },
    lousa(W, H, r) {
      let s = ''; const giz = (pts, cor, sw, op, d, comp) => '<path d="' + pts.map((p, j) => (j ? 'L' : 'M') + f1(p[0] + (r() - 0.5) * 3) + ' ' + f1(p[1] + (r() - 0.5) * 3)).join('') + '" fill="none" stroke="' + cor + '" stroke-width="' + sw + '" stroke-linecap="round" stroke-linejoin="round" opacity="' + op + '" data-a="traco" style="--comp:' + comp + ';--d:' + d + 'ms"/>';
      for (let k = 0; k < 120; k++) s += '<circle cx="' + f1(r() * W) + '" cy="' + f1(r() * H) + '" r="' + f1(1 + r() * 2.2) + '" fill="var(--sobre-campo)" opacity="' + f1(0.12 + r() * 0.2) + '"/>';
      for (let k = 0; k < 3; k++) { const y = H * (0.22 + k * 0.14), x0 = W * 0.08, x1 = W * (0.5 - k * 0.08), pts = []; for (let x = x0; x <= x1; x += 24) pts.push([x, y + Math.sin(x / 90 + k) * 4]); s += giz(pts, 'var(--sobre-campo)', 7, 0.5, k * 200, Math.round(x1 - x0 + 60)); }
      const cx = W * 0.68, cy = H * 0.42, rx = W * 0.18, ry = H * 0.24, ring = [];
      for (let j = 0; j <= 80; j++) { const t = j / 70 * Math.PI * 2 - 0.4; ring.push([cx + Math.cos(t) * rx * (1 + j * 0.0012), cy + Math.sin(t) * ry * (1 - j * 0.0016)]); }
      s += giz(ring, 'var(--acento)', 8, 0.85, 600, Math.round((rx + ry) * 4));
      const a = [W * 0.2, H * 0.82], b = [W * 0.47, H * 0.64], arco = [];
      for (let j = 0; j <= 20; j++) { const t = j / 20; arco.push([a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t - Math.sin(t * Math.PI) * H * 0.08]); }
      s += giz(arco, 'var(--acento2)', 7, 0.85, 1000, Math.round(W * 0.4)) + giz([[b[0] - 34, b[1] - 6], b, [b[0] - 18, b[1] + 28]], 'var(--acento2)', 7, 0.85, 1300, 120);
      for (let k = 0; k < 4; k++) s += giz([[W * 0.66 + k * 26, H * 0.8], [W * 0.66 + k * 26 + 4, H * 0.92]], 'var(--sobre-campo)', 6, 0.6, 1400 + k * 80, 160);
      return s + giz([[W * 0.65, H * 0.9], [W * 0.66 + 4 * 26, H * 0.81]], 'var(--sobre-campo)', 6, 0.6, 1800, 200);
    },
    velino(W, H, r) {
      let s = '<rect x="36" y="36" width="' + (W - 72) + '" height="' + (H - 72) + '" fill="none" stroke="var(--acento)" stroke-width="2" opacity=".55"/><rect x="50" y="50" width="' + (W - 100) + '" height="' + (H - 100) + '" fill="none" stroke="var(--acento)" stroke-width="1" opacity=".4"/>';
      const ph = r() * 6;
      for (let k = 0; k < 24; k++) {
        let d = '';
        for (let x = 0; x <= W; x += 12) { const u = x / W; d += (x ? 'L' : 'M') + x + ' ' + f1(H * 0.5 + H * 0.27 * Math.sin(u * Math.PI * 3 + k * 0.26 + ph) * Math.cos(u * Math.PI * 0.8 - 0.4) + H * 0.05 * Math.sin(u * Math.PI * 14 + k * 0.5)); }
        s += '<path d="' + d + '" fill="none" stroke="' + (k % 6 ? 'var(--sobre-campo)' : 'var(--acento)') + '" stroke-width="' + (k % 6 ? 1.2 : 2) + '" opacity="' + (k % 6 ? 0.24 : 0.6) + '" data-a="traco" style="--comp:' + Math.round(W * 1.6) + ';--d:' + (k * 50) + 'ms"/>';
      }
      return s;
    },
    revista(W, H, r) {
      let s = '';
      for (let k = 1; k < 6; k++) s += '<line x1="' + f1(W * k / 6) + '" y1="0" x2="' + f1(W * k / 6) + '" y2="' + H + '" stroke="var(--sobre-campo)" stroke-width="1.5" opacity=".18"/>';
      const m = Math.min(W, H);
      s += '<circle cx="' + f1(W * (0.62 + r() * 0.1)) + '" cy="' + f1(H * 0.58) + '" r="' + f1(m * 0.44) + '" fill="var(--sobre-campo)" opacity=".13" data-a="aparece"/>';
      [0.85, 0.5, 0.3].forEach((op, k) => { s += '<rect x="' + f1(W * 0.08) + '" y="' + f1(H * (0.16 + k * 0.09)) + '" width="' + f1(W * (0.34 - k * 0.08)) + '" height="' + f1(Math.max(8, H * 0.032)) + '" fill="var(--sobre-campo)" opacity="' + op + '" data-a="cresce-x" style="--d:' + (200 + k * 150) + 'ms"/>'; });
      return s;
    },
    duna(W, H, r) {
      let s = '<circle cx="' + f1(W * 0.78) + '" cy="' + f1(H * 0.2) + '" r="' + f1(Math.min(W, H) * 0.09) + '" fill="var(--sobre-campo)" opacity=".5" data-a="aparece"/>';
      for (let k = 0; k < 7; k++) {
        const base = H * (0.3 + k * 0.11), f = 1.1 + k * 0.17, p = r() * 6, p2 = r() * 6; let d = '';
        for (let x = 0; x <= W + 24; x += 24) { const u = x / W; d += 'L' + x + ' ' + f1(base + H * 0.06 * Math.sin(u * Math.PI * f + p) + H * 0.02 * Math.sin(u * Math.PI * 4.3 + p2)); }
        s += '<g data-a="sobe" style="--d:' + (k * 110) + 'ms"><path d="M0 ' + H + d + 'L' + (W + 24) + ' ' + H + 'Z" fill="var(--sobre-campo)" opacity="' + f1(0.06 + k * 0.025) + '"/><path d="M' + d.slice(1) + '" fill="none" stroke="var(--sobre-campo)" stroke-width="2" opacity=".45"/></g>';
      }
      return s;
    },
    civico(W, H, r) {
      let s = ''; const g = 22, ops = [0.07, 0.11, 0.16, 0.22];
      for (let y = g, j = 0; y < H; j++) {
        const h = 110 + r() * 90;
        for (let x = g; x < W;) {
          const w = 140 + r() * 130, v = r();
          s += '<rect x="' + f1(x) + '" y="' + f1(y) + '" width="' + f1(Math.min(w, W - x)) + '" height="' + f1(h) + '" rx="6" fill="' + (v < 0.1 ? 'var(--marca)' : 'var(--sobre-campo)') + '" opacity="' + (v < 0.1 ? 0.7 : ops[Math.floor(r() * 4)]) + '" data-a="aparece" style="--d:' + Math.round(Math.min(900, (x / W + y / H) * 450)) + 'ms"/>';
          if (v > 0.93) s += '<circle cx="' + f1(x + w / 2) + '" cy="' + f1(y + h / 2) + '" r="' + f1(Math.min(w, h) * 0.3) + '" fill="none" stroke="var(--sobre-campo)" stroke-width="3" opacity=".6"/>';
          x += w + g;
        }
        y += h + g;
      }
      s += '<path d="M' + f1(-W * 0.05) + ' ' + f1(H * 0.9) + 'L' + f1(W * 1.05) + ' ' + f1(H * 0.15) + '" stroke="var(--campo)" stroke-width="34"/><path d="M' + f1(-W * 0.05) + ' ' + f1(H * 0.9) + 'L' + f1(W * 1.05) + ' ' + f1(H * 0.15) + '" stroke="var(--sobre-campo)" stroke-width="3" stroke-dasharray="20 14" opacity=".5"/>';
      return s;
    },
    ardosia(W, H, r) {
      let s = ''; const tw = 150, th = 130, cv = 34;
      for (let j = 0, y = -th * 0.6; y < H; j++, y += th * 0.55) {
        let row = '';
        for (let x = (j % 2) * tw / 2 - tw; x < W + tw; x += tw) {
          const dest = r() < 0.06;
          row += '<path d="M' + f1(x + 3) + ' ' + f1(y) + 'h' + (tw - 6) + 'v' + (th - cv) + 'q0 ' + cv + ' ' + (-cv) + ' ' + cv + 'h' + (-(tw - 6 - 2 * cv)) + 'q' + (-cv) + ' 0 ' + (-cv) + ' ' + (-cv) + 'Z" fill="var(--campo)" stroke="' + (dest ? 'var(--acento)' : 'var(--sobre-campo)') + '" stroke-width="' + (dest ? 4 : 2) + '" stroke-opacity="' + (dest ? 0.85 : 0.26) + '"/>';
        }
        s += '<g data-a="aparece" style="--d:' + Math.min(900, j * 45) + 'ms">' + row + '</g>';
      }
      return s;
    },
  };
  function arte(W, H, seed, ctx) {
    const t = D.arte_tema || doc.dataset.tema; const f = ARTES[t] || ARTES.tabuleiro;
    return '<div class="sk-arte-box sk-campo" aria-hidden="true"><svg viewBox="0 0 ' + W + ' ' + H + '" preserveAspectRatio="xMidYMid slice">' + f(W, H, rng(seed), ctx) + '</svg></div>';
  }

  // ------------------------------------------------------------------ gráficos (dados reais, sempre com fonte)
  // extensões (templates/runtime/sk-ext-*.js) registram tipos e layouts em window.SK_EXT e recebem os auxiliares em aj()
  const EXT = () => window.SK_EXT || {};
  // etapas: cada peça de gráfico ou diagrama vira um grupo que entra numa tecla (só quando o slide pede "etapas")
  const et = (n) => (SLIDE_ATUAL && SLIDE_ATUAL.etapas ? ' data-etapa="b' + String(n).padStart(3, '0') + '"' : '');
  function aj() {
    return { f1, svgTexto, esc, md, marcar, img, arte, A, titulo, sub, texto, itens, fonte, visual, grafico, diagrama, D, core: L, juntar, et,
      loc: (v) => (typeof v === 'number' ? v.toLocaleString(D.idioma || 'pt-BR') : v), slide: () => SLIDE_ATUAL };
  }
  function grafico(g, W, H) {
    const tipo = g.tipo || 'barras'; let s = '';
    if ((EXT().graficos || {})[tipo]) return EXT().graficos[tipo](g, W, H, aj());
    const loc = (v) => (typeof v === 'number' ? v.toLocaleString(D.idioma || 'pt-BR') : v);
    const val = (v) => (g.formato ? g.formato.replace('{v}', loc(v)) : loc(v) + (g.unidade || ''));
    const corA = 'var(--acento)', corB = 'var(--acento2)', tinta = 'var(--tinta)';
    if (tipo === 'barras') {
      const v = g.valores, n = v.length, max = g.max || Math.max.apply(null, v) * 1.12, base = H - 120, topo = 70;
      const larg = (W - 40) / n, bw = Math.min(larg * 0.62, 190);
      v.forEach((vv, i) => {
        const h = (base - topo) * (vv / max), x = 20 + i * larg + (larg - bw) / 2, d = (g.destaque || []).indexOf(i) >= 0;
        s += '<g' + et(i) + '><rect x="' + f1(x) + '" y="' + f1(base - h) + '" width="' + f1(bw) + '" height="' + f1(h) + '" rx="6" fill="' + (d ? corA : corB) + '" data-a="cresce-y" style="--d:' + (200 + i * 110) + 'ms"/>';
        s += svgTexto(x + bw / 2, base - h - 18, val(vv), 40, { a: 'middle', w: 700, f: 'var(--f-num)', anim: 700 + i * 110 });
        s += svgTexto(x + bw / 2, base + 44, g.rotulos[i], 30, { a: 'middle', n: 12, w: d ? 700 : 400 }) + '</g>';
      });
      s += '<line x1="10" y1="' + base + '" x2="' + (W - 10) + '" y2="' + base + '" stroke="' + tinta + '" stroke-width="3"/>';
    } else if (tipo === 'barras-h') {
      const v = g.valores, n = v.length, max = g.max || Math.max.apply(null, v) * 1.08, rot = Math.min(W * 0.34, Math.max(W * 0.16, Math.max.apply(null, g.rotulos.map((x) => String(x).length)) * 19 + 40)), alt = (H - 20) / n, bh = Math.min(alt * 0.64, 78);
      v.forEach((vv, i) => {
        const y = 10 + i * alt + (alt - bh) / 2, w = (W - rot - 110) * (vv / max), d = (g.destaque || []).indexOf(i) >= 0;
        s += '<g' + et(i) + '>' + svgTexto(rot - 22, y + bh / 2 + 12, g.rotulos[i], 34, { a: 'end', w: d ? 700 : 400 });
        s += '<rect x="' + rot + '" y="' + f1(y) + '" width="' + f1(w) + '" height="' + f1(bh) + '" rx="6" fill="' + (d ? corA : corB) + '" data-a="cresce-x" style="--d:' + (200 + i * 100) + 'ms"/>';
        s += svgTexto(rot + w + 16, y + bh / 2 + 13, val(vv), 38, { w: 700, f: 'var(--f-num)', anim: 650 + i * 100 }) + '</g>';
      });
    } else if (tipo === 'linha') {
      const xs = g.rotulos, ser = g.series || [{ nome: '', valores: g.valores }], all = [].concat.apply([], ser.map((x) => x.valores));
      const max = g.max || Math.max.apply(null, all) * 1.1, min = g.min != null ? g.min : 0, x0 = 30, x1 = W - 170, y0 = H - 90, y1 = 50;
      const X = (i) => x0 + ((x1 - x0) * i) / (xs.length - 1), Y = (v) => y0 - ((y0 - y1) * (v - min)) / (max - min);
      s += '<line x1="' + x0 + '" y1="' + y0 + '" x2="' + x1 + '" y2="' + y0 + '" stroke="' + tinta + '" stroke-width="3"/>';
      xs.forEach((t, i) => { if (xs.length <= 8 || i % Math.ceil(xs.length / 8) === 0 || i === xs.length - 1) s += svgTexto(X(i), y0 + 44, t, 30, { a: 'middle' }); });
      ser.forEach((sr, k) => {
        s += '<g' + et(k) + '>';
        const cor = k === 0 ? corA : corB; const d = sr.valores.map((v, i) => (i ? 'L' : 'M') + f1(X(i)) + ' ' + f1(Y(v))).join(' ');
        s += '<path d="' + d + '" fill="none" stroke="' + cor + '" stroke-width="8" stroke-linejoin="round" stroke-linecap="round" pathLength="1" data-a="traco" style="--d:' + (200 + k * 300) + 'ms"/>';
        sr.valores.forEach((v, i) => { s += '<circle cx="' + f1(X(i)) + '" cy="' + f1(Y(v)) + '" r="9" fill="' + cor + '" data-a="aparece" style="--d:' + (900 + i * 60) + 'ms"/>'; });
        const li = sr.valores.length - 1;
        s += svgTexto(X(li) + 18, Y(sr.valores[li]) + 12, val(sr.valores[li]), 40, { w: 700, f: 'var(--f-num)', cor: cor, anim: 1300 });
        if (sr.nome) s += svgTexto(X(li) + 18, Y(sr.valores[li]) + 50, sr.nome, 30, { cor: cor, anim: 1400 });
        s += '</g>';
      });
    } else if (tipo === 'proporcao') {
      const n = g.n || 10, k = g.k || 3, cols = g.colunas || Math.min(n, 10), rows = Math.ceil(n / cols);
      const cel = Math.min((W - 40) / cols, (H - 170) / rows), r = cel * 0.3;
      for (let i = 0; i < n; i++) {
        const x = 20 + (i % cols) * cel + cel / 2, y = 20 + Math.floor(i / cols) * cel + cel / 2, on = i < k;
        s += '<g data-a="pousa" style="--d:' + (i * 40) + 'ms"><circle cx="' + f1(x) + '" cy="' + f1(y - r * 0.9) + '" r="' + f1(r * 0.55) + '" fill="' + (on ? corA : 'none') + '" stroke="' + (on ? corA : tinta) + '" stroke-width="4"/>' +
          '<path d="M' + f1(x - r) + ' ' + f1(y + r * 1.1) + 'Q' + f1(x) + ' ' + f1(y - r * 0.6) + ' ' + f1(x + r) + ' ' + f1(y + r * 1.1) + 'Z" fill="' + (on ? corA : 'none') + '" stroke="' + (on ? corA : tinta) + '" stroke-width="4"/></g>';
      }
      s += svgTexto(20, H - 40, g.texto || (k + ' de ' + n), 64, { w: 700, f: 'var(--f-num)', cor: corA, anim: 600 });
    }
    return '<svg viewBox="0 0 ' + W + ' ' + H + '" preserveAspectRatio="xMidYMid meet" style="color:var(--tinta)">' + s + '</svg>';
  }

  // ------------------------------------------------------------------ diagramas
  let NDIAG = 0;
  function diagrama(g, W, H) {
    const tipo = g.tipo || 'cadeia', nos = g.nos || [], n = nos.length; let s = '';
    if ((EXT().diagramas || {})[tipo]) return EXT().diagramas[tipo](g, W, H, aj());
    const cor = 'var(--acento)', tinta = 'var(--tinta)', papel = 'var(--papel)';
    // um marcador de seta por diagrama: o Chromium herda a visibilidade do <svg> onde o marcador mora, e o slide escondido apagaria as setas dos outros
    const MK = 'skp' + (++NDIAG);
    const caixa = (x, y, w, h, t, i, destaque) => '<g' + et(i * 2) + ' data-a="sobe" style="--d:' + (150 + i * 160) + 'ms"><rect x="' + f1(x - w / 2) + '" y="' + f1(y - h / 2) + '" width="' + f1(w) + '" height="' + f1(h) + '" rx="18" fill="' + (destaque ? cor : papel) + '" stroke="' + (destaque ? cor : tinta) + '" stroke-width="4"/>' +
      svgTexto(x, y + 16, t, Math.min(56, Math.max(40, h / 4)), { a: 'middle', n: Math.max(8, Math.floor(w / 28)), meio: true, w: 600, f: 'var(--f-titulo)', cor: destaque ? 'var(--sobre-acento)' : tinta }) + '</g>';
    const seta = (x1, y1, x2, y2, i) => '<path' + et(i * 2 + 1) + ' d="M' + f1(x1) + ' ' + f1(y1) + 'L' + f1(x2) + ' ' + f1(y2) + '" stroke="' + tinta + '" stroke-width="5" fill="none" marker-end="url(#' + MK + ')" pathLength="1" data-a="traco" style="--d:' + (300 + i * 160) + 'ms"/>';
    const defs = '<defs><marker id="' + MK + '" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto"><path d="M0 0L10 5L0 10z" fill="' + tinta + '"/></marker></defs>';
    if (tipo === 'cadeia') {
      const vertical = H > W * 0.9, gap = 90;
      const bw = vertical ? Math.min(W * 0.86, 780) : Math.min((W - (n - 1) * gap) / n, 420);
      const bh = vertical ? Math.min((H - (n - 1) * gap) / n, 250) : Math.min(H * 0.5, 280);
      const tot = vertical ? n * bh + (n - 1) * gap : n * bw + (n - 1) * gap;
      const ini = vertical ? (H - tot) / 2 : (W - tot) / 2;
      nos.forEach((t, i) => {
        const x = vertical ? W / 2 : ini + bw / 2 + i * (bw + gap), y = vertical ? ini + bh / 2 + i * (bh + gap) : H / 2;
        s += caixa(x, y, bw, bh, t, i, (g.destaque || []).indexOf(i) >= 0);
        if (i < n - 1) s += vertical ? seta(x, y + bh / 2 + 10, x, y + bh / 2 + gap - 12, i) : seta(x + bw / 2 + 10, y, x + bw / 2 + gap - 12, y, i);
      });
    } else if (tipo === 'ciclo' && n >= 5) {
      // cinco ou mais etapas: duas fileiras. Em cima da esquerda para a direita, embaixo de volta, com curvas nas pontas
      const k = Math.ceil(n / 2), gx = 96, bw = Math.min(400, (W - 120 - (k - 1) * gx) / k), bh = Math.min(170, H * 0.3);
      const x0 = (W - (k * bw + (k - 1) * gx)) / 2 + bw / 2, yA = H * 0.27, yB = H * 0.73;
      const pos = nos.map((_, i) => (i < k ? [x0 + i * (bw + gx), yA] : [x0 + (k - 1 - (i - k) - (n % 2 ? 0.5 : 0)) * (bw + gx), yB]));
      const curva = (a, b, lado, i) => { const dx = lado * (bw / 2 + 60); return '<path' + et(i * 2 + 1) + ' d="M' + f1(a[0] + lado * (bw / 2 + 8)) + ' ' + f1(a[1]) + 'C' + f1(a[0] + dx) + ' ' + f1(a[1]) + ' ' + f1(b[0] + dx) + ' ' + f1(b[1]) + ' ' + f1(b[0] + lado * (bw / 2 + 12)) + ' ' + f1(b[1]) + '" stroke="' + tinta + '" stroke-width="5" fill="none" marker-end="url(#' + MK + ')" pathLength="1" data-a="traco" style="--d:' + (300 + i * 160) + 'ms"/>'; };
      nos.forEach((t, i) => {
        s += caixa(pos[i][0], pos[i][1], bw, bh, t, i, (g.destaque || []).indexOf(i) >= 0);
        const j = (i + 1) % n, a = pos[i], b = pos[j];
        if (i < k - 1) s += seta(a[0] + bw / 2 + 8, a[1], b[0] - bw / 2 - 12, b[1], i);
        else if (i === k - 1) s += curva(a, b, 1, i);
        else if (i < n - 1) s += seta(a[0] - bw / 2 - 8, a[1], b[0] + bw / 2 + 12, b[1], i);
        else s += curva(a, b, -1, i);
      });
    } else if (tipo === 'ciclo' || tipo === 'centro') {
      const cx = W / 2, cy = H / 2, R = Math.min(W, H) * 0.36, bw = Math.min(360, W * 0.34), bh = 150;
      if (tipo === 'centro') s += caixa(cx, cy, bw * 1.05, bh * 1.2, g.centro || '', 0, true);
      nos.forEach((t, i) => {
        const a = -Math.PI / 2 + (i / n) * Math.PI * 2, x = cx + Math.cos(a) * R * 1.12, y = cy + Math.sin(a) * R;
        if (tipo === 'centro') s += seta(cx + Math.cos(a) * 130, cy + Math.sin(a) * 100, x - Math.cos(a) * (bw / 2.2), y - Math.sin(a) * (bh / 1.6), i);
        else { const b = -Math.PI / 2 + ((i + 0.5) / n) * Math.PI * 2; s += '<path' + et((i + 1) * 2 + 1) + ' d="M' + f1(cx + Math.cos(a + 0.32) * R * 1.12) + ' ' + f1(cy + Math.sin(a + 0.32) * R) + 'Q' + f1(cx + Math.cos(b) * R * 1.45) + ' ' + f1(cy + Math.sin(b) * R * 1.3) + ' ' + f1(cx + Math.cos(a + (2 * Math.PI) / n - 0.32) * R * 1.12) + ' ' + f1(cy + Math.sin(a + (2 * Math.PI) / n - 0.32) * R) + '" fill="none" stroke="' + tinta + '" stroke-width="5" marker-end="url(#' + MK + ')" pathLength="1" data-a="traco" style="--d:' + (400 + i * 160) + 'ms"/>'; }
        s += caixa(x, y, bw, bh, t, i + 1, (g.destaque || []).indexOf(i) >= 0);
      });
    } else if (tipo === 'camadas') {
      const cx = W / 2, cy = H / 2 + 20;
      nos.forEach((t, i) => {
        const k = (n - i) / n, rx = (W / 2 - 10) * k, ry = (H / 2 - 20) * k, last = i === n - 1;
        s += '<g' + et(i) + '><ellipse cx="' + f1(cx) + '" cy="' + f1(cy) + '" rx="' + f1(rx) + '" ry="' + f1(ry) + '" fill="' + (last ? cor : 'var(--camada-' + (i % 3) + ',var(--papel))') + '" stroke="' + tinta + '" stroke-width="4" opacity="' + (last ? 1 : 0.94) + '" data-a="foco" style="--d:' + (i * 220) + 'ms"/>';
        s += svgTexto(cx, last ? cy + 14 : cy - ry + 62, t, last ? 44 : 38, { a: 'middle', w: 700, f: 'var(--f-titulo)', n: last ? 14 : 30, meio: last, cor: last ? 'var(--sobre-acento)' : tinta, anim: 300 + i * 220 }).replace('<text ', last ? '<text ' : '<text paint-order="stroke" stroke="var(--papel)" stroke-width="10" stroke-linejoin="round" ') + '</g>';
      });
    } else if (tipo === 'balanca') {
      const cx = W / 2, top = H * 0.3, braco = W * 0.4;
      s += '<path d="M' + f1(cx) + ' ' + f1(top) + 'L' + f1(cx - 70) + ' ' + f1(H - 60) + 'H' + f1(cx + 70) + 'Z" fill="' + tinta + '" opacity=".9"/>';
      s += '<line x1="' + f1(cx - braco) + '" y1="' + f1(top) + '" x2="' + f1(cx + braco) + '" y2="' + f1(top) + '" stroke="' + tinta + '" stroke-width="10" stroke-linecap="round" data-a="cresce-x" style="--d:200ms"/>';
      [0, 1].forEach((j) => { const x = cx + (j ? 1 : -1) * braco; s += '<line x1="' + f1(x) + '" y1="' + f1(top) + '" x2="' + f1(x) + '" y2="' + f1(top + 90) + '" stroke="' + tinta + '" stroke-width="4"/>' + caixa(x, top + 190, Math.min(380, W * 0.36), 190, nos[j] || '', j + 1, j === (g.lado_forte || 0)); });
      if (g.centro) s += '<g' + et(9) + '>' + svgTexto(cx, H - 10, g.centro, 34, { a: 'middle', w: 600 }) + '</g>';
    }
    return '<svg viewBox="0 0 ' + W + ' ' + H + '" preserveAspectRatio="xMidYMid meet">' + defs + s + '</svg>';
  }

  // ------------------------------------------------------------------ peças comuns dos layouts
  const ESPEC = { // [título máx, título mín, corpo máx, corpo mín, corpo teto, título teto] em px do palco
    'capa': [160, 72, 60, 44, 72, 168], 'secao': [136, 80, 58, 44, 72, 152], 'imagem-total': [80, 64, 56, 44, 70, 88], 'dividido': [80, 64, 58, 44, 72, 84],
    'faixa': [72, 64, 62, 44, 70, 80], 'numero': [64, 64, 64, 44, 72, 72], 'citacao': [64, 64, 92, 44, 104, 64], 'comparacao': [68, 64, 52, 44, 68, 76],
    'linha-do-tempo': [68, 64, 56, 44, 66, 76], 'processo': [68, 64, 50, 44, 68, 76], 'galeria': [72, 64, 50, 44, 50, 80], 'cartoes': [68, 64, 48, 44, 64, 76],
    'grafico': [72, 64, 58, 44, 72, 80], 'tabela': [68, 64, 60, 44, 70, 76], 'pergunta': [80, 64, 60, 44, 74, 88], 'afirmacao': [88, 64, 56, 44, 68, 100],
    'lista': [76, 64, 58, 44, 72, 80], 'diagrama': [72, 64, 54, 44, 68, 80], 'fechamento': [76, 64, 58, 44, 72, 80], 'referencias': [68, 64, 54, 44, 80, 80], 'livre': [72, 64, 52, 44, 52, 72],
  };
  let ordemAnim = 0;
  const A = (tipo, extra) => { const d = (extra != null ? extra : (ordemAnim += 110)); return ' data-a="' + tipo + '" style="--d:' + d + 'ms"'; };
  // nomes que não se partem no título: "~" vira espaço fixo, e o trecho curto antes da primeira vírgula
  // fica inteiro ("ESTADOS UNIDOS, / 1787" e nunca "ESTADOS / UNIDOS, 1787")
  function juntar(x) {
    x = String(x).replace(/~/g, '\u00a0');
    const v = x.indexOf(', '); if (v > 0) { const a = x.slice(0, v); if (a.split(' ').length <= 3) x = a.replace(/ /g, '\u00a0') + x.slice(v); }
    return x;
  }
  function titulo(s, tag) { if (!s.titulo) return ''; return '<' + (tag || 'h2') + ' class="sk-titulo" data-role="titulo" data-txt' + (doc.dataset.tema === 'datilografo' && String(s.titulo).length <= 34 ? ' data-dat' : '') + A('sobe', 80) + '>' + marcar(md(juntar(s.titulo)), (s.destaques || {}).titulo) + '</' + (tag || 'h2') + '>'; }
  function sub(s) { return s.subtitulo ? '<p class="sk-sub" data-role="corpo" data-txt' + A('sobe') + '>' + md(s.subtitulo) + '</p>' : ''; }
  function itens(s, cls, anim) {
    const it = s.itens || []; if (!it.length) return '';
    const h = (s.destaques || {});
    return '<ul class="sk-itens ' + (cls || '') + '">' + it.map((t, i) => '<li data-role="corpo" data-txt' + (s.etapas ? ' data-etapa="a' + String(i).padStart(3, '0') + '"' : '') + A(anim || 'sobe') + '>' + marcar(md(t), h[String(i)]) + '</li>').join('') + '</ul>';
  }
  function texto(s) { return s.texto ? '<p class="sk-texto" data-role="corpo" data-txt' + A('sobe') + '>' + marcar(md(s.texto), (s.destaques || {}).texto) + '</p>' : ''; }
  // a fonte fica registrada no deck, na tecla I e nas notas. Na tela, só quando a pessoa pede.
  const fonteVisivel = (s) => s.fonte && (D.fontes_no_slide === true || s.fonte_visivel === true);
  function fonte(s) { return fonteVisivel(s) ? '<p class="sk-fonte" data-role="legenda" data-txt' + A('aparece') + '>' + md(s.fonte) + '</p>' : ''; }
  function visual(s, W, H, i, opt) {
    opt = opt || {};
    if (s.grafico) return '<div class="sk-campo" style="display:flex;flex-direction:column;padding:60px 56px 56px;gap:18px"><div style="flex:1;position:relative;background:var(--papel);border-radius:var(--raio,14px);color:var(--tinta)">' +
      '<div style="position:absolute;inset:30px 34px 26px">' + grafico(s.grafico, W - 180, H - 230) + '</div></div>' + (s.fonte ? '' : '') + '</div>';
    if (s.diagrama) return '<div class="sk-campo" style="padding:50px 40px">' + '<div style="position:absolute;inset:50px 40px;color:var(--sobre-campo)">' + diagrama(s.diagrama, W - 80, H - 100).replace(/var\(--tinta\)/g, 'var(--sobre-campo)').replace(/var\(--papel\)/g, 'var(--campo)') + '</div></div>';
    if (s.imagem) return img(s.imagem, { d: 120, a: opt.a });
    return arte(W, H, i * 7 + 3, { letra: s.titulo || D.titulo });
  }

  // ------------------------------------------------------------------ layouts
  const L = {
    'capa'(s, i) {
      const meta = [s.autor || D.autor, s.instituicao || D.instituicao, s.data || D.data].filter(Boolean).join(' · ');
      return '<div class="sk-l sk-l-capa"><div class="sk-lado-texto sk-campo sk-caixa sk-zona"' + A('cortina', 0) + '>' + titulo(Object.assign({ titulo: D.titulo }, s), 'h1') + sub(s) + itens(s) +
        (meta ? '<p class="sk-meta" data-role="legenda" data-txt' + A('aparece') + '>' + esc(meta) + '</p>' : '') + '</div>' +
        '<div class="sk-im">' + (s.imagem ? img(s.imagem, { d: 0 }) : arte(960, 1080, 11, { letra: s.titulo || D.titulo })) + '</div></div>';
    },
    'secao'(s, i) {
      const k = secaoDe(i);
      const mapa = SECOES.length > 1 ? '<div class="sk-mapa" data-role="rotulo">' + SECOES.map((x, j) => '<span data-txt data-role="rotulo" class="' + (j === k ? 'sk-aqui' : '') + '"' + A('aparece', 500 + j * 70) + '>' + esc(x.nome) + '</span>').join('') + '</div>' : '';
      return '<div class="sk-l sk-l-secao sk-campo"><div class="sk-lado-texto sk-caixa sk-zona">' + titulo(Object.assign({ titulo: SECOES[k].nome }, s)) + sub(s) + texto(s) + itens(s) + '</div>' + mapa +
        (s.imagem ? img(s.imagem, { d: 100, a: 'revela' }) : arte(845, 1080, i + 5, { letra: s.titulo || SECOES[k].nome })) + '</div>';
    },
    'imagem-total'(s, i) {
      const lado = s.lado || 'esquerda';
      return '<div class="sk-l sk-l-imagem-total" data-lado="' + lado + '">' + img(s.imagem, { d: 0 }) + '<div class="sk-painel sk-caixa sk-zona"' + A('revela', 200) + '>' + titulo(s) + sub(s) + texto(s) + itens(s) + fonte(s) + '</div></div>';
    },
    'dividido'(s, i) {
      const lado = s.lado || 'direita';
      const dir = lado === 'esquerda'; // cada lado entra pela sua borda
      return '<div class="sk-l sk-l-dividido" data-lado="' + lado + '"><div class="sk-lado-texto sk-caixa sk-zona">' + titulo(s) + sub(s) + texto(s) + itens(s, '', dir ? 'entra-dir' : 'entra-esq') + fonte(s) + '</div><div class="sk-visual"' + A(dir ? 'entra-esq' : 'entra-dir', 60) + '>' + visual(s, 883, 1080, i, { a: 'aparece' }) + '</div></div>';
    },
    'faixa'(s, i) {
      const corpo = '<div class="sk-caixa sk-zona" style="display:flex;flex-direction:column;gap:34px">' + texto(s) + itens(s) + fonte(s) + '</div>';
      return '<div class="sk-l sk-l-faixa"><div class="sk-im">' + (s.imagem ? img(s.imagem, { d: 0, a: 'revela' }) : arte(1920, 430, i, { letra: s.titulo })) + '</div>' +
        '<div class="sk-baixo' + (s.titulo ? '' : ' sk-sem-titulo') + '">' + (s.titulo ? '<div class="sk-cab">' + titulo(s) + '</div>' : '') + corpo + '</div></div>';
    },
    'numero'(s, i) {
      const n = s.numero || {};
      return '<div class="sk-l sk-l-numero"><div class="sk-lado-texto sk-caixa sk-zona">' + titulo(s) +
        '<p class="sk-num" data-role="numero" data-txt data-conta="' + esc(n.valor) + '"' + A('sobe') + '>' + esc(n.valor) + (n.unidade ? '<small>' + esc(n.unidade) + '</small>' : '') + '</p>' +
        (n.texto ? '<p class="sk-texto" data-role="corpo" data-txt' + A('sobe') + '>' + md(n.texto) + '</p>' : '') + texto(s) + itens(s) + fonte(s) + '</div><div class="sk-visual">' + visual(s, 806, 1080, i) + '</div></div>';
    },
    'citacao'(s, i) {
      const c = s.citacao || {};
      return '<div class="sk-l sk-l-citacao' + (s.campo === false ? '' : ' sk-campo') + '"><div class="sk-lado-texto sk-caixa sk-zona">' +
        '<svg class="sk-aspas" viewBox="0 0 200 170" aria-hidden="true"' + A('aparece', 0) + '><path fill="currentColor" d="M0 170V96C0 40 30 6 86 0l8 22C62 32 48 54 46 86h40v84zm112 0V96c0-56 30-90 86-96l8 22c-32 10-46 32-48 64h40v84z"/></svg>' +
        '<blockquote data-role="corpo" data-txt' + A('foco', 200) + '>' + marcar(md(c.texto || s.texto || ''), (s.destaques || {}).citacao) + '</blockquote>' +
        '<p class="sk-autor" data-role="legenda" data-txt' + A('aparece', 900) + '>' + md(c.autor || '') + (c.obra ? '<br><span style="font-weight:400">' + md(c.obra) + '</span>' : '') + '</p></div>' +
        '<div class="sk-im">' + (s.imagem ? img(s.imagem, { d: 0 }) : arte(730, 1080, i, { letra: c.autor })) + '</div></div>';
    },
    'comparacao'(s, i) {
      const col = (c, j) => '<div class="sk-col' + (c.imagem ? '' : ' sk-sem-img') + '">' + (c.imagem ? '<div class="sk-im">' + img(c.imagem, { d: 150 + j * 200, a: 'revela' }) + '</div>' : '') +
        '<h3 data-role="corpo" data-txt' + A(j ? 'entra-dir' : 'entra-esq', 400 + j * 200) + '>' + md(c.titulo || '') + '</h3>' +
        '<div class="sk-caixa">' + itens({ itens: c.itens, destaques: c.destaques }, '', j ? 'entra-dir' : 'entra-esq') + '</div></div>';
      const cs = s.colunas || [];
      return '<div class="sk-l sk-l-comparacao"><div class="sk-cab">' + titulo(s) + '</div><div class="sk-cols sk-zona"><div class="sk-versus" aria-hidden="true"></div>' + cs.slice(0, 2).map(col).join('') + '</div></div>';
    },
    'linha-do-tempo'(s, i) {
      const ev = s.eventos || [];
      return '<div class="sk-l sk-l-linha-do-tempo">' + (s.imagem ? '<div class="sk-faixa-img">' + img(s.imagem, { d: 0, a: 'revela', semLegenda: false }) + '</div>' : '<div class="sk-faixa-img">' + arte(1920, 250, i, { letra: s.titulo }) + '</div>') +
        '<div class="sk-cab">' + titulo(s) + '</div><div class="sk-eventos sk-caixa sk-zona">' +
        ev.map((e, j) => '<div class="sk-evento"' + A('sobe', 500 + j * 160) + '><span class="sk-ano" data-role="rotulo" data-txt>' + esc(e.ano) + '</span><p class="sk-texto" data-role="corpo" data-txt>' + md(e.texto) + '</p></div>').join('') + '</div></div>';
    },
    'processo'(s, i) {
      const ps = s.passos || [];
      return '<div class="sk-l sk-l-processo"><div class="sk-faixa-img">' + (s.imagem ? img(s.imagem, { d: 0, a: 'revela' }) : arte(1920, 220, i + 3, { letra: s.titulo })) + '</div><div class="sk-cab">' + titulo(s) + '</div><div class="sk-passos sk-caixa sk-zona">' +
        ps.map((p, j) => '<div class="sk-passo"' + A('sobe', 300 + j * 180) + '><span class="sk-marca" data-role="rotulo" data-txt>' + (j + 1) + '</span><h3 data-role="corpo" data-txt>' + md(p.titulo || '') + '</h3>' + (p.texto ? '<p class="sk-texto" data-role="corpo" data-txt>' + md(p.texto) + '</p>' : '') + '</div>').join('') + '</div></div>';
    },
    'galeria'(s, i) {
      const ims = s.imagens || [];
      return '<div class="sk-l sk-l-galeria"><div class="sk-cab">' + titulo(s) + '</div><div class="sk-grade">' + ims.map((k, j) => '<div class="sk-im">' + img(k, { d: 200 + j * 180, a: 'revela-baixo' }) + '</div>').join('') + '</div></div>';
    },
    'cartoes'(s, i) {
      const cs = s.cartoes || [];
      return '<div class="sk-l sk-l-cartoes"><div class="sk-cab">' + titulo(s) + '</div><div class="sk-cartoes sk-zona">' +
        cs.map((c, j) => '<div class="sk-cartao"' + A('sobe', 300 + j * 150) + '>' + '<div class="sk-im">' + (c.imagem ? img(c.imagem, { d: 0, semLegenda: true }) : arte(420, 400, i * 5 + j * 3 + 1, { letra: c.titulo })) + '</div>' +
          '<h3 data-role="corpo" data-txt>' + md(c.titulo || '') + '</h3><div class="sk-caixa"><p class="sk-texto" data-role="corpo" data-txt>' + md(c.texto || '') + '</p></div></div>').join('') + '</div></div>';
    },
    'grafico'(s, i) {
      return '<div class="sk-l sk-l-grafico"><div class="sk-lado-texto sk-caixa sk-zona">' + titulo(s) + texto(s) + itens(s) + '</div>' +
        '<div class="sk-area sk-campo"><div class="sk-cartao-graf"' + A('foco', 100) + '>' + grafico(s.grafico || {}, 950, 790) + '</div>' + fonte(s) + '</div></div>';
    },
    'tabela'(s, i) {
      const t = s.tabela || { cabecalho: [], linhas: [] };
      return '<div class="sk-l sk-l-tabela"><div class="sk-cab">' + titulo(s) + '</div><div class="sk-caixa sk-zona"><table class="sk-tab"' + A('foco', 250) + '><thead><tr>' + t.cabecalho.map((h) => '<th data-role="celula" data-txt>' + md(h) + '</th>').join('') + '</tr></thead><tbody>' +
        t.linhas.map((l) => '<tr>' + l.map((c) => '<td data-role="celula" data-txt>' + md(c) + '</td>').join('') + '</tr>').join('') + '</tbody></table>' + (fonteVisivel(s) ? '<div style="margin-top:24px">' + fonte(s) + '</div>' : '') + '</div></div>';
    },
    'pergunta'(s, i) {
      return '<div class="sk-l sk-l-pergunta sk-campo"><div class="sk-lado-texto sk-caixa sk-zona">' + titulo(s) + texto(s) + itens(s) + '</div><div class="sk-visual">' + visual(s, 768, 1080, i, { a: 'iris' }) + '</div></div>';
    },
    'afirmacao'(s, i) {
      const tem = !!s.imagem;
      return '<div class="sk-l sk-l-afirmacao' + (tem ? ' sk-com-img' : ' sk-campo') + '">' + (tem ? img(s.imagem, { d: 0 }) : arte(1920, 1080, i, { letra: s.titulo })) +
        '<div class="sk-bloco sk-caixa sk-zona"' + (tem ? A('revela', 200) : '') + '>' + titulo(s) + texto(s) + itens(s) + fonte(s) + '</div></div>';
    },
    'lista'(s, i) {
      const lado = s.lado || 'direita';
      return '<div class="sk-l sk-l-lista" data-lado="' + (lado === 'direita' ? 'direita' : 'esquerda') + '"><div class="sk-lado-texto sk-caixa sk-zona">' + titulo(s) + texto(s) + itens(s) + fonte(s) + '</div><div class="sk-visual">' + visual(s, 576, 1080, i) + '</div></div>';
    },
    'diagrama'(s, i) {
      return '<div class="sk-l sk-l-diagrama"><div class="sk-lado-texto sk-caixa sk-zona">' + titulo(s) + texto(s) + itens(s) + fonte(s) + '</div><div class="sk-area-diag sk-papel">' + diagrama(s.diagrama || {}, 1056, 960) + '</div></div>';
    },
    'fechamento'(s, i) {
      return '<div class="sk-l sk-l-fechamento"><div class="sk-lado-texto sk-caixa sk-zona">' + titulo(s) + '<ul class="sk-ideias">' + (s.itens || []).map((t, j) => '<li data-role="corpo" data-txt' + A('sobe', 300 + j * 180) + '>' + md(t) + '</li>').join('') + '</ul></div>' +
        '<div class="sk-visual">' + visual(s, 691, 1080, i) + '</div></div>';
    },
    'referencias'(s, i) {
      return '<div class="sk-l sk-l-referencias"><div class="sk-lado-texto sk-caixa sk-zona">' + titulo(s) + '<ol class="sk-refs">' + (s.referencias || s.itens || []).map((t) => '<li data-role="referencia" data-txt' + A('aparece') + '>' + md(t) + '</li>').join('') + '</ol></div>' +
        '<div class="sk-visual">' + visual(s, 461, 1080, i) + '</div></div>';
    },
    'livre'(s, i) { // {{img:nome}} vira a figura da imagem declarada em "imagens", com legenda e foco
      const h = (s.html || '').replace(/\{\{img:([\w-]+)\}\}/g, (_, k) => img(k, { d: 150, cls: 'sk-fig-livre' }));
      const semFonte = fonteVisivel(s) && h.indexOf(s.fonte.slice(0, 24)) < 0; // a fonte declarada aparece no pé, se o HTML não a trouxer
      return '<div class="sk-l sk-l-livre' + (semFonte ? ' sk-com-fonte' : '') + '">' + h + (semFonte ? '<p class="sk-fonte sk-fonte-livre" data-role="legenda" data-txt' + A('aparece', 900) + '>' + md(s.fonte) + '</p>' : '') + '</div>';
    },
  };

  // ------------------------------------------------------------------ viúvas
  // a última palavra curta de um texto de corpo fica presa à anterior, para nenhuma linha terminar com uma palavra só.
  // Custa zero rodada de correção e tira o aviso "palavra sozinha" da verificação.
  function ligarFins(raiz) {
    raiz.querySelectorAll('[data-role="corpo"], [data-role="legenda"], .sk-itens li').forEach((el) => {
      if ((el.textContent || '').trim().split(/\s+/).length < 4) return;
      const w = document.createTreeWalker(el, NodeFilter.SHOW_TEXT); let ult = null, n;
      while ((n = w.nextNode())) if (n.nodeValue.trim()) ult = n;
      if (!ult) return;
      const m = ult.nodeValue.match(/^([\s\S]*\S)[ \t]+(\S{1,14})(\s*)$/);
      if (m) { LIGADOS.push([ult, ult.nodeValue, el]); ult.nodeValue = m[1] + '\u00a0' + m[2] + m[3]; }
      else if (/^\S{1,14}\s*$/.test(ult.nodeValue)) { // a última palavra está noutro nó (negrito, destaque): prende o espaço anterior
        const w2 = document.createTreeWalker(el, NodeFilter.SHOW_TEXT); let ant = null, x;
        while ((x = w2.nextNode()) && x !== ult) if (x.nodeValue.trim()) ant = x;
        if (ant && / $/.test(ant.nodeValue)) { LIGADOS.push([ant, ant.nodeValue, el]); ant.nodeValue = ant.nodeValue.replace(/ $/, '\u00a0'); }
      }
    });
  }
  // depois do ajuste: se o par preso não cabe na coluna (palavra passando da borda), desfaz e deixa a quebra normal
  const LIGADOS = [];
  function conferirLigados() {
    let mudou = false;
    LIGADOS.forEach((x) => {
      const [no, orig, el] = x; if (!no.parentNode || no.nodeValue === orig) return;
      const r = document.createRange(); r.selectNodeContents(el); const b = el.getBoundingClientRect();
      const passa = Array.from(r.getClientRects()).some((q) => q.width > 1 && q.right > b.right + 1);
      if (passa || el.scrollWidth > el.clientWidth + 1) { no.nodeValue = orig; mudou = true; }
    });
    return mudou;
  }

  // ------------------------------------------------------------------ montagem
  const palco = document.getElementById('sk-palco');
  function montar() {
    campos();
    const html = SLIDES.map((s, i) => {
      ordemAnim = 150; SLIDE_ATUAL = s;
      const LX = EXT().layouts || {};
      const lay = (LX[s.layout] || L[s.layout]) ? s.layout : 'dividido';
      const k = secaoDe(i), cc = corCampo(k), sc = sobre(cc), e = ESPEC[lay] || (EXT().espec || {})[lay] || ESPEC.dividido;
      let corpo = '';
      try { corpo = LX[lay] ? LX[lay](s, i, aj()) : L[lay](s, i); } catch (err) { corpo = '<div class="sk-l" style="padding:120px;font-size:44px">Erro no slide ' + (i + 1) + ': ' + esc(err.message) + '</div>'; console.error(err); }
      const trilha = '<div class="sk-trilha" aria-hidden="true">' + SLIDES.map((_, j) => '<span class="' + (j < i ? 'sk-feito' : j === i ? 'sk-aqui' : '') + '" style="background:' + corCampo(secaoDe(j)) + '"></span>').join('') + '</div>';
      return '<section class="sk-slide" data-i="' + i + '" data-layout="' + lay + '" data-secao="' + k + '"' + (s.etapas ? ' data-etapas' : '') + (INTENS.includes(s.intensidade) ? ' data-intensidade="' + s.intensidade + '"' : '') +
        ' data-tmax="' + (s.tmax || e[0]) + '" data-tmin="' + Math.max(PISO.titulo, s.tmin || e[1]) + '" data-cmax="' + (s.cmax || e[2]) + '" data-cmin="' + Math.max(PISO.corpo, s.cmin || e[3]) + '"' +
        ' data-cteto="' + (s.cteto || e[4]) + '" data-tteto="' + (s.tteto || e[5]) + '" data-tlinhas="' + ({ 'pergunta': 4.4, 'afirmacao': 4.4, 'secao': 3.4, 'grafico': 4.4 }[lay] || 3.4) + '"' +
        ' style="--campo:' + cc + ';--sobre-campo:' + sc[0] + ';--sobre-campo-2:' + sc[1] + '" aria-label="' + esc(s.titulo || ('Slide ' + (i + 1))) + '">' + corpo + trilha + '</section>';
    }).join('');
    palco.innerHTML = html;
    ligarFins(palco);
  }

  // ------------------------------------------------------------------ ajuste de fontes (nunca abaixo do piso)
  function transborda(sec) {
    const out = [];
    sec.querySelectorAll('.sk-caixa').forEach((el) => { if (el.scrollHeight > el.clientHeight + 2 || el.scrollWidth > el.clientWidth + 2) out.push(el); });
    sec.querySelectorAll('.sk-titulo').forEach((el) => { const lh = parseFloat(getComputedStyle(el).lineHeight) || 1; if (el.getBoundingClientRect().height / lh > (+sec.dataset.tlinhas || 3.4)) out.push(el); });
    return out;
  }
  function preenchimento(sec) { // fração da altura da zona de texto que o texto ocupa
    let pior = 1;
    sec.querySelectorAll('.sk-zona').forEach((z) => {
      const zr = z.getBoundingClientRect(); if (zr.height < 50) return;
      let y0 = Infinity, y1 = -Infinity;
      z.querySelectorAll('[data-txt]').forEach((t) => { const r = t.getBoundingClientRect(); if (r.height > 0) { y0 = Math.min(y0, r.top); y1 = Math.max(y1, r.bottom); } });
      if (y1 > y0) pior = Math.min(pior, (y1 - y0) / zr.height);
    });
    return pior;
  }
  const COMPACTO = { 'dividido': ['--col-texto', '42%'], 'lista': ['--col-tira', '42%'], 'referencias': ['--col-vis', '40%'], 'fechamento': ['--col-vis', '46%'] };
  function caber(sec) {
    const comp0 = COMPACTO[sec.dataset.layout]; if (comp0) { sec.style.removeProperty(comp0[0]); delete sec.dataset.compacto; }
    let t = +sec.dataset.tmax, c = +sec.dataset.cmax; const tmin = +sec.dataset.tmin, cmin = +sec.dataset.cmin;
    const cteto = Math.max(c, +sec.dataset.cteto || c), tteto = Math.max(t, +sec.dataset.tteto || t);
    const num = sec.querySelector('.sk-num'); let n = num ? 300 : 0;
    const set = () => { sec.style.setProperty('--t', t); sec.style.setProperty('--c', c); if (num) sec.style.setProperty('--n', n); };
    set();
    let encolheu = false;
    const linhasTitulo = () => { let m = 0; sec.querySelectorAll('.sk-titulo').forEach((el) => { const lh = parseFloat(getComputedStyle(el).lineHeight) || 1; m = Math.max(m, el.getBoundingClientRect().height / lh); }); return m; };
    const tituloLargo = () => Array.from(sec.querySelectorAll('.sk-titulo')).some((el) => el.scrollWidth > el.clientWidth + 2);
    // última linha do título curta demais (uma palavra sozinha embaixo)
    const ultimaCurta = () => Array.from(sec.querySelectorAll('.sk-titulo')).some((el) => {
      // depois de vírgula, uma linha curta é escolha de diagramação ("ESTADOS UNIDOS, / 1787"), não viúva
      if (/,\s*\S+(\s\S+)?\s*$/.test(el.textContent.replace(/\u00a0/g, ' '))) return false;
      const r = document.createRange(); r.selectNodeContents(el);
      const lin = {}; Array.from(r.getClientRects()).filter((q) => q.width > 2).forEach((q) => { const k = Math.round(q.top / 6); lin[k] = (lin[k] || 0) + q.width; });
      const ks = Object.keys(lin).map(Number).sort((x, y) => x - y); if (ks.length < 2) return false;
      return lin[ks[ks.length - 1]] < 0.34 * Math.max.apply(null, ks.map((k) => lin[k]));
    });
    while ((linhasTitulo() > (+sec.dataset.tlinhas || 3.4) || tituloLargo()) && t > tmin) { t -= 4; set(); } // título encolhido não impede o corpo de crescer
    for (let k = 0; k < 140; k++) {
      const ov = transborda(sec).filter((el) => !el.classList.contains('sk-titulo')); if (!ov.length) { sec.dataset.transborda = '0'; break; }
      encolheu = true;
      if (num && n > 160) n -= 12;
      else if (c > cmin) c -= 2;
      else if (t > tmin) t -= 4;
      else { sec.dataset.transborda = '1'; console.warn('[slides-impecaveis] slide ' + (+sec.dataset.i + 1) + ': o texto não cabe nem no piso. Divida o slide ou troque o layout.'); break; }
      set();
    }
    // crescer: texto curto ganha corpo até ocupar a zona, sem passar do teto do layout
    const crescer = () => {
      let tituloParado = false; // quando o título não pode crescer, o corpo ainda pode
      const ruim = () => transborda(sec).length || linhasTitulo() > (+sec.dataset.tlinhas || 3.4) || tituloLargo();
      for (let k = 0; k < 60 && preenchimento(sec) < 0.7; k++) {
        const c0 = c, t0 = t;
        if (c < cteto) c += 2;
        if (!tituloParado && t < tteto && k % 2 === 0) t += 4;
        if (c === c0 && t === t0) break;
        set();
        if (ruim() || (t !== t0 && ultimaCurta())) {
          if (t !== t0) { t = t0; tituloParado = true; set(); if (!ruim()) continue; }
          c = c0; t = t0; set(); break;
        }
      }
    };
    if (!encolheu && sec.dataset.transborda === '0') {
      crescer();
      // texto que continua curto demais cede largura ao visual (imagem, arte ou gráfico maior, menos área morta)
      const comp = COMPACTO[sec.dataset.layout];
      if (comp && preenchimento(sec) < 0.55) {
        sec.style.setProperty(comp[0], comp[1]); sec.dataset.compacto = '1';
        if (transborda(sec).length) { sec.style.removeProperty(comp[0]); delete sec.dataset.compacto; } else crescer();
      }
    }
    // bom senso com o espaço: se reduzir o título em até 12% tira uma linha inteira, reduz
    // ("ESTADOS UNIDOS, / 1787" em vez de "ESTADOS / UNIDOS, 1787")
    { const n0 = Math.round(linhasTitulo()), t0 = t; let melhor = 0;
      if (n0 >= 3) { for (let tt = t - 2; tt >= Math.max(tmin, t0 * 0.88); tt -= 2) { t = tt; set(); if (Math.round(linhasTitulo()) < n0 && !transborda(sec).length) { melhor = tt; break; } } }
      t = melhor || t0; set(); }
    // título com palavra sozinha na última linha: tenta reduzir um pouco, sem passar do piso
    if (ultimaCurta()) {
      const t0 = t;
      for (let k = 0; k < 8 && t - 4 >= tmin && ultimaCurta(); k++) { t -= 4; set(); }
      if (ultimaCurta()) { t = t0; set(); }
    }
    // hierarquia nos dois sentidos: título no máximo 1,7 vez o corpo (fora capa, seção e afirmação)
    if (!/^(capa|secao|afirmacao|numero|citacao)$/.test(sec.dataset.layout) && sec.querySelector('.sk-titulo') && sec.querySelector('.sk-zona [data-role="corpo"]') && t > Math.max(tmin, Math.round(c * 1.7 / 4) * 4)) { t = Math.max(tmin, Math.round(c * 1.7 / 4) * 4); set(); }
    // hierarquia: com título, o corpo fica no máximo em 90% dele (título de 64 px pede corpo de até 56 px)
    if (sec.querySelector('.sk-titulo') && c > Math.max(cmin, Math.floor(t * 0.9 / 2) * 2)) { c = Math.max(cmin, Math.floor(t * 0.9 / 2) * 2); set(); }
    sec.dataset.c = c; sec.dataset.t = t;
  }

  // ------------------------------------------------------------------ escala, navegação, etapas
  function escalar() {
    if (document.body.classList.contains('sk-grade')) return;
    const W = window.innerWidth, H = window.innerHeight, s = Math.min(W / 1920, H / 1080);
    palco.style.transform = 'translate(' + (W - 1920 * s) / 2 + 'px,' + (H - 1080 * s) / 2 + 'px) scale(' + s + ')';
  }
  let atual = 0; const total = SLIDES.length; const PREVIA = Q.has('sk-previa');
  const canal = (!PREVIA && 'BroadcastChannel' in window) ? new BroadcastChannel('slides-impecaveis') : null;
  const REDUZ = !!(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches);
  const TRANS = ['dissolve', 'sobe', 'assenta', 'floresce', 'respiro'];
  let limpa = 0;
  function secs() { return palco.querySelectorAll('.sk-slide'); }
  // etapas por grupo: as peças com a mesma chave data-etapa entram juntas (texto "a000...", gráfico e diagrama "b000...")
  const chave = (e) => e.dataset.etapa || '';
  function grupos(sec, sel) { const m = new Map(); if (sec) sec.querySelectorAll(sel).forEach((e) => { const k = chave(e); if (!m.has(k)) m.set(k, []); m.get(k).push(e); }); return Array.from(m.keys()).sort().map((k) => m.get(k)); }
  function etapasPendentes(sec) { return grupos(sec, '[data-etapa].sk-oculta'); }
  // ao revelar, a animação da peça recomeça do zero, com os atrasos internos preservados (barra antes do número)
  const animados = (els) => { const v = []; els.forEach((e) => { if (e.hasAttribute('data-a')) v.push(e); e.querySelectorAll('[data-a]').forEach((x) => v.push(x)); }); return v; };
  // peça escondida fica sem animação (uma animação em curso no compositor pintaria a peça por cima do opacity:0)
  function esconder(els, sim) { els.forEach((e) => e.classList.toggle('sk-oculta', sim)); animados(els).forEach((e) => { if (e.dataset.d0 != null) e.style.setProperty('--d', e.dataset.d0 + 'ms'); e.style.animation = sim ? 'none' : ''; }); }
  function replay(els) {
    const vivos = animados(els);
    const dd = vivos.map((e) => { if (e.dataset.d0 == null) e.dataset.d0 = parseFloat(e.style.getPropertyValue('--d')) || 0; return +e.dataset.d0; });
    const m = dd.length ? Math.min.apply(null, dd) : 0;
    vivos.forEach((e, j) => { e.style.setProperty('--d', (dd[j] - m) + 'ms'); e.style.animation = 'none'; });
    void palco.offsetWidth; vivos.forEach((e) => { e.style.animation = ''; });
  }
  const movendo = () => !FINAL && doc.classList.contains('sk-mov');
  // troca de slide: o que sai fica parado e opaco embaixo, o que entra aparece por cima (o fundo nunca aparece entre os dois)
  function trocar(ss, i, de) {
    ss.forEach((s, j) => { s.classList.toggle('sk-ativo', j === i); s.classList.remove('sk-sai', 'sk-entra'); if (j !== i) s.querySelectorAll('.sk-morfando').forEach((e) => e.classList.remove('sk-morfando')); });
    if (de == null || de === i || !movendo()) return;
    const t = SLIDES[i].transicao || D.transicao || 'dissolve';
    palco.dataset.tr = TRANS.includes(t) ? t : 'dissolve';
    ss[de].classList.add('sk-sai'); ss[i].classList.add('sk-entra');
    clearTimeout(limpa); limpa = setTimeout(() => { ss[de].classList.remove('sk-sai'); ss[i].classList.remove('sk-entra'); }, 700);
  }
  function pares(a, b) { return Array.from(b.querySelectorAll('[data-morph]')).map((n) => [a.querySelector('[data-morph="' + CSS.escape(n.dataset.morph) + '"]'), n]).filter((p) => p[0]); }
  // morph: o mesmo objeto em dois slides vizinhos desliza e muda de tamanho do lugar antigo ao novo
  function morfar(ss, i, de, ps) {
    ps.forEach((p) => p[1].classList.add('sk-morfando'));
    if (document.startViewTransition) {
      ps.forEach((p, k) => { p[0].style.viewTransitionName = 'sk-m' + k; });
      const vt = document.startViewTransition(() => { ps.forEach((p, k) => { p[0].style.viewTransitionName = ''; if (atual === i) p[1].style.viewTransitionName = 'sk-m' + k; }); trocar(ss, atual); });
      vt.finished.finally(() => ps.forEach((p) => { p[1].style.viewTransitionName = ''; }));
      return;
    }
    const P = palco.getBoundingClientRect(), k = P.width / 1920;
    const caixa = (e) => { const r = e.getBoundingClientRect(); return [(r.left - P.left) / k, (r.top - P.top) / k, r.width / k, r.height / k]; };
    const antes = ps.map((p) => caixa(p[0])); trocar(ss, i, de);
    ps.forEach(([o, n], j) => { // FLIP com uma cópia por cima dos dois slides
      const a = antes[j], b = caixa(n), c = n.cloneNode(true);
      c.style.cssText += ';position:absolute;margin:0;z-index:8;transform-origin:0 0;left:' + b[0] + 'px;top:' + b[1] + 'px;width:' + b[2] + 'px;height:' + b[3] + 'px';
      palco.appendChild(c); o.style.visibility = n.style.visibility = 'hidden';
      c.animate([{ transform: 'translate(' + (a[0] - b[0]) + 'px,' + (a[1] - b[1]) + 'px) scale(' + a[2] / b[2] + ',' + a[3] / b[3] + ')' }, { transform: 'none' }], { duration: 700, easing: 'cubic-bezier(.4,0,.2,1)' })
        .finished.finally(() => { c.remove(); o.style.visibility = n.style.visibility = ''; });
    });
  }
  function ir(i, opt) {
    opt = opt || {};
    i = Math.max(0, Math.min(total - 1, i)); const ss = secs(), de = atual;
    const sec = ss[i];
    if (sec && sec.hasAttribute('data-etapas')) esconder(Array.from(sec.querySelectorAll('[data-etapa]')), !(FINAL || opt.fim));
    const ps = movendo() && !REDUZ && Math.abs(i - de) === 1 ? pares(ss[de], sec) : [];
    atual = i;
    if (ps.length) morfar(ss, i, de, ps); else trocar(ss, i, de);
    if (de !== i) contar(sec);
    if (ss[i + 1]) ss[i + 1].querySelectorAll('img').forEach((im) => { if (im.decode) im.decode().catch(() => {}); }); // pré-carga do próximo
    const md0 = document.getElementById('sk-medidor'); if (md0) md0.remove();
    if (!opt.semHash) history.replaceState(null, '', '#' + (i + 1));
    if (canal && !opt.remoto) canal.postMessage({ tipo: 'ir', i: i });
    const nt = document.getElementById('sk-notas'); if (nt && nt.classList.contains('sk-ver')) notas(true);
  }
  function proximo() { const p = etapasPendentes(secs()[atual]); if (p.length && !FINAL) { esconder(p[0], false); if (movendo()) replay(p[0]); return; } if (atual < total - 1) ir(atual + 1); }
  function anterior() { // desfaz a última etapa revelada antes de voltar de slide
    const s = secs()[atual], feitas = s && !FINAL && s.hasAttribute('data-etapas') ? grupos(s, '[data-etapa]:not(.sk-oculta)') : [];
    if (feitas.length) { esconder(feitas[feitas.length - 1], true); return; }
    if (atual > 0) ir(atual - 1, { fim: true });
  }

  // contagem de números (estado final já está no HTML)
  function contar(sec) {
    if (FINAL || !doc.classList.contains('sk-mov')) return;
    sec.querySelectorAll('[data-conta]').forEach((el) => {
      const alvo = el.dataset.conta; const m = String(alvo).match(/^([^\d]*)([\d.,]+)(.*)$/); if (!m) return;
      const num = parseFloat(m[2].replace(/\./g, '').replace(',', '.')); if (!isFinite(num)) return;
      const casas = (m[2].split(',')[1] || '').length, unidade = el.querySelector('small') ? el.querySelector('small').outerHTML : '';
      const fmt = (v) => m[1] + v.toLocaleString(doc.lang, { minimumFractionDigits: casas, maximumFractionDigits: casas }) + m[3];
      const t0 = performance.now(), dur = 1400;
      const step = (t) => { const k = Math.min(1, (t - t0) / dur), e = 1 - Math.pow(1 - k, 4); el.innerHTML = esc(fmt(num * e)) + unidade; if (k < 1) requestAnimationFrame(step); else el.innerHTML = esc(alvo) + unidade; };
      requestAnimationFrame(step);
    });
  }

  // ------------------------------------------------------------------ sobreposições: créditos, notas, apresentador, grade
  function ui() {
    const div = document.createElement('div');
    div.innerHTML = '<div id="sk-ajuda" class="sk-ui" data-ui>setas ou clique para navegar · número e Enter salta · F tela cheia · G visão geral · B tela preta · W tela branca · L ponteiro · I créditos · N notas · P apresentador (R zera o tempo) · M medidor de fontes e vazios</div>' +
      '<div id="sk-tela" class="sk-ui" data-ui></div><div id="sk-laser" class="sk-ui" data-ui></div>' +
      '<div id="sk-creditos" class="sk-ui" data-ui><h2>Imagens, dados e fontes</h2><ol>' + (D.creditos || []).map((c) => '<li>' + c + '</li>').join('') + '</ol></div>' +
      '<div id="sk-notas" class="sk-ui" data-ui></div>';
    while (div.firstChild) document.body.appendChild(div.firstChild);
  }
  function alternar(id) { const el = document.getElementById(id); el.classList.toggle('sk-ver'); return el.classList.contains('sk-ver'); }
  function notas(forcar) {
    const el = document.getElementById('sk-notas'); const s = SLIDES[atual] || {};
    el.innerHTML = '<h2>' + esc(s.titulo || ('Slide ' + (atual + 1))) + '</h2><p>' + md(s.notas || '(sem notas)') + '</p>' + (s.fontes_notas ? '<p style="font-size:26px;opacity:.8">' + md(s.fontes_notas) + '</p>' : '');
    if (!forcar) alternar('sk-notas');
  }
  const BASE = location.href.split(/[?#]/)[0];
  function apresentador() { window.open(BASE + '?apresentador#' + (atual + 1), 'sk-apresentador', 'width=1280,height=800'); }
  // janela do apresentador: o mesmo arquivo com ?apresentador. Notas, próximo slide (?final), cronômetro e tempo previsto
  function paginaApresentador() {
    doc.classList.add('sk-ap'); document.title = 'Apresentador · ' + (D.titulo || '');
    document.body.innerHTML = '<div id="ap"><p id="ap-tempo"></p><div id="ap-atual"><h1 id="ap-h"></h1><p id="ap-tags"></p><div id="ap-n"></div></div>' +
      '<div id="ap-prox"><p>A seguir</p><iframe id="ap-f" tabindex="-1" title="Próximo slide"></iframe><p id="ap-pt"></p></div></div>';
    const $ = (id) => document.getElementById(id), soma = []; let i = Math.max(0, (parseInt(location.hash.slice(1), 10) || 1) - 1), t0 = Date.now(), m = 0;
    SLIDES.forEach((s) => { m += +s.minutos || 0; soma.push(m); });
    const mmss = (x) => Math.floor(x / 60) + ':' + String(x % 60).padStart(2, '0');
    const tique = () => { $('ap-tempo').textContent = mmss(Math.floor((Date.now() - t0) / 1000)) + (m ? '   ·   previsto ' + soma[i] + ' de ' + m + ' min' : ''); };
    const r = () => {
      const a = SLIDES[i] || {}, b = SLIDES[i + 1];
      $('ap-h').textContent = (i + 1) + ' / ' + total + '   ' + (a.titulo || '');
      $('ap-tags').textContent = [a.cortavel && 'cortável', a.apendice && 'apêndice', a.minutos && a.minutos + ' min'].filter(Boolean).join('   ·   ');
      $('ap-n').innerHTML = md(a.notas || '(sem notas)');
      $('ap-f').style.visibility = b ? 'visible' : 'hidden'; if (b) $('ap-f').src = BASE + '?final&sk-previa#' + (i + 2);
      $('ap-pt').textContent = b ? (b.titulo || '') + (b.cortavel ? '   (cortável)' : '') : 'Fim';
      tique();
    };
    if (canal) { canal.onmessage = (e) => { if (e.data.tipo === 'ir') { i = e.data.i; r(); } }; canal.postMessage({ tipo: 'quem' }); }
    document.addEventListener('keydown', (e) => { if (e.key === 'r' || e.key === 'R') { t0 = Date.now(); tique(); } else if (canal) { e.preventDefault(); canal.postMessage({ tipo: 'tecla', k: e.key }); } });
    setInterval(tique, 500); r(); window.SK.pronto = true;
  }
  function grade() {
    const on = document.body.classList.toggle('sk-grade');
    if (on) { palco.style.transform = 'none'; secs()[atual].scrollIntoView({ block: 'center' }); } else escalar();
  }


  // ------------------------------------------------------------------ medidor (tecla M): o avaliador humano vê pisos e vazios no próprio navegador
  function medidor() {
    const velho = document.getElementById('sk-medidor'); if (velho) { velho.remove(); return; }
    const sec = secs()[atual]; if (!sec) return;
    const R = palco.getBoundingClientRect(), k = R.width / 1920;
    const pos = (r) => ({ x: (r.left - R.left) / k, y: (r.top - R.top) / k, w: r.width / k, h: r.height / k });
    const textos = []; let menor = 999;
    const w = document.createTreeWalker(sec, NodeFilter.SHOW_TEXT); let n;
    while ((n = w.nextNode())) {
      const t = (n.nodeValue || '').trim(); if (!t) continue;
      const el = n.parentElement; if (!el || el.closest('[data-sk-ignore],[data-ui]')) continue;
      const rg = document.createRange(); rg.selectNodeContents(n);
      const rr = Array.from(rg.getClientRects()).filter((r) => r.width > 1); if (!rr.length) continue;
      const papelEl = el.closest('[data-role]'); const papel = papelEl ? papelEl.getAttribute('data-role') : (t.length >= 25 ? 'corpo' : 'curto');
      const piso = papel === 'titulo' || papel === 'numero' ? PISO.titulo : papel === 'corpo' ? PISO.corpo : papel === 'referencia' ? 32 : papel === 'celula' ? 36 : PISO.qualquer;
      const escala = (el instanceof SVGElement) ? ((el.getScreenCTM() || { a: 1 }).a / k) : (el.getBoundingClientRect().width / (el.offsetWidth || el.getBoundingClientRect().width) / k) * k / k;
      const px = parseFloat(getComputedStyle(el).fontSize) * ((el instanceof SVGElement) ? ((el.getScreenCTM() || { a: k }).a / k) : 1);
      menor = Math.min(menor, px);
      rr.forEach((r) => textos.push(Object.assign(pos(r), { ruim: px + 0.5 < piso, px: Math.round(px), piso: piso })));
    }
    const vis = []; sec.querySelectorAll('img,svg,canvas,video').forEach((el) => { if (el.closest('[data-sk-ignore]') || (el instanceof SVGElement && el.ownerSVGElement)) return; const r = el.getBoundingClientRect(); if (r.width * r.height > 6400 * k * k) vis.push(pos(r)); });
    const cel = 40, mx = 96, my = 64, cols = Math.floor((1920 - 2 * mx) / cel), rows = Math.floor((1080 - 2 * my) / cel);
    const ocup = []; for (let r = 0; r < rows; r++) { ocup.push([]); for (let c = 0; c < cols; c++) {
      const x = mx + c * cel, y = my + r * cel; const bate = (b) => b.x < x + cel && b.x + b.w > x && b.y < y + cel && b.y + b.h > y;
      ocup[r].push(textos.some(bate) || vis.some(bate)); } }
    const fech = ocup.map((l, r) => l.map((v, c) => v || [[0, 1], [0, -1], [1, 0], [-1, 0]].filter(([dr, dc]) => (ocup[r + dr] || [])[c + dc]).length >= 2));
    let vaz = 0, svg = '';
    fech.forEach((l, r) => l.forEach((v, c) => { if (!v) { vaz++; svg += '<rect x="' + (mx + c * cel) + '" y="' + (my + r * cel) + '" width="' + (cel - 1) + '" height="' + (cel - 1) + '" fill="rgba(220,40,40,.28)"/>'; } }));
    textos.filter((t) => t.ruim).forEach((t) => { svg += '<rect x="' + t.x + '" y="' + t.y + '" width="' + t.w + '" height="' + t.h + '" fill="none" stroke="#FF9F1C" stroke-width="5"/><text x="' + t.x + '" y="' + (t.y - 6) + '" font-size="26" fill="#FF9F1C" font-family="system-ui">' + t.px + ' px (piso ' + t.piso + ')</text>'; });
    const frac = vaz / (rows * cols), corpo = +sec.dataset.c;
    const ok = !textos.some((t) => t.ruim) && frac <= 0.33 && sec.dataset.transborda !== '1';
    svg += '<rect x="1300" y="24" width="596" height="150" rx="14" fill="rgba(10,10,10,.86)"/><text x="1326" y="72" font-size="30" font-family="system-ui" fill="' + (ok ? '#6BD68F' : '#FF8A80') + '">' + (ok ? 'Medição ok' : 'Medição reprovada') + '</text>' +
      '<text x="1326" y="112" font-size="26" font-family="system-ui" fill="#fff">menor texto ' + Math.round(menor) + ' px · corpo ' + corpo + ' px</text><text x="1326" y="150" font-size="26" font-family="system-ui" fill="#fff">área lisa sem conteúdo ' + Math.round(frac * 100) + '% (limite 33%)</text>';
    const ov = document.createElement('div'); ov.id = 'sk-medidor'; ov.setAttribute('data-ui', ''); ov.style.cssText = 'position:absolute;inset:0;z-index:60;pointer-events:none';
    ov.innerHTML = '<svg viewBox="0 0 1920 1080" width="1920" height="1080" style="position:absolute;inset:0">' + svg + '</svg>';
    palco.appendChild(ov);
  }

  let digitos = '', tmDig = 0;
  function tela(cor) { const el = document.getElementById('sk-tela'), on = el.dataset.cor !== cor; el.dataset.cor = on ? cor : ''; el.classList.toggle('sk-ver', on); }
  function teclas(e) {
    const k = e.key;
    if (/^[0-9]$/.test(k)) { digitos += k; clearTimeout(tmDig); tmDig = setTimeout(() => { digitos = ''; }, 3000); return; } // número + Enter salta
    if (k === 'Enter' && digitos) { e.preventDefault(); const n = +digitos; digitos = ''; if (n > 0) ir(n - 1); return; }
    if (k === 'b' || k === 'B' || k === '.') tela('preta');
    else if (k === 'w' || k === 'W') tela('branca');
    else if (k === 'l' || k === 'L') doc.classList.toggle('sk-laser');
    else if (['ArrowRight', 'ArrowDown', 'PageDown', ' ', 'Enter'].includes(k)) { e.preventDefault(); if (document.body.classList.contains('sk-grade')) { grade(); return; } proximo(); }
    else if (['ArrowLeft', 'ArrowUp', 'PageUp', 'Backspace'].includes(k)) { e.preventDefault(); anterior(); }
    else if (k === 'Home') ir(0); else if (k === 'End') ir(total - 1);
    else if (k === 'f' || k === 'F') { if (!document.fullscreenElement) doc.requestFullscreen && doc.requestFullscreen(); else document.exitFullscreen(); }
    else if (k === 'g' || k === 'G') grade();
    else if (k === 'i' || k === 'I') alternar('sk-creditos');
    else if (k === 'n' || k === 'N') notas();
    else if (k === 'p' || k === 'P') apresentador();
    else if (k === 'm' || k === 'M') medidor();
    else if (k === '?' || k === 'h' || k === 'H') alternar('sk-ajuda');
    else if (k === 'Escape') { doc.classList.remove('sk-laser'); ['sk-creditos', 'sk-notas', 'sk-ajuda', 'sk-tela'].forEach((id) => document.getElementById(id).classList.remove('sk-ver')); if (document.body.classList.contains('sk-grade')) grade(); }
  }

  // ------------------------------------------------------------------ início
  async function iniciar() {
    if (Q.has('apresentador')) { paginaApresentador(); return; }
    if (FINAL) doc.classList.add('sk-final');
    montar(); ui(); escalar();
    if (document.fonts && document.fonts.ready) { try { await document.fonts.ready; } catch (e) { /* segue */ } }
    secs().forEach(caber);
    if (conferirLigados()) secs().forEach(caber);
    palco.querySelectorAll('[data-dat]').forEach((el) => { // datilografa só em título de uma linha
      const lh = parseFloat(getComputedStyle(el).lineHeight) || 1, n = el.textContent.length;
      if (el.offsetHeight > 0 && el.offsetHeight / lh < 1.5) { el.dataset.a = 'datilografa'; el.style.setProperty('--passos', n); el.style.setProperty('--dur', Math.min(1.4, n * 0.05).toFixed(2) + 's'); }
    });
    const h = parseInt((location.hash || '#1').slice(1), 10);
    ir(isFinite(h) && h > 0 ? h - 1 : 0, { semHash: true });
    // com movimento reduzido no sistema, o CSS deixa só a opacidade
    if (!FINAL) requestAnimationFrame(() => { doc.classList.add('sk-mov'); contar(secs()[atual]); });
    window.addEventListener('hashchange', () => { const n = parseInt(location.hash.slice(1), 10); if (n > 0 && n - 1 !== atual) ir(n - 1, { semHash: true, fim: true }); });
    window.addEventListener('resize', escalar);
    document.addEventListener('keydown', teclas);
    palco.addEventListener('click', (e) => {
      if (document.body.classList.contains('sk-grade')) { const s = e.target.closest('.sk-slide'); if (s) { ir(+s.dataset.i); grade(); } return; }
      if (e.clientX > window.innerWidth * 0.3) proximo(); else anterior();
    });
    let x0 = null; window.addEventListener('touchstart', (e) => { x0 = e.touches[0].clientX; }, { passive: true });
    window.addEventListener('touchend', (e) => { if (x0 == null) return; const dx = e.changedTouches[0].clientX - x0; if (Math.abs(dx) > 40) (dx < 0 ? proximo : anterior)(); x0 = null; });
    if (canal) canal.onmessage = (e) => { if (e.data.tipo === 'tecla') teclas({ key: e.data.k, preventDefault() {} }); else if (e.data.tipo === 'quem') canal.postMessage({ tipo: 'ir', i: atual }); };
    const laser = document.getElementById('sk-laser');
    let tm; window.addEventListener('mousemove', (e) => { laser.style.transform = 'translate(' + e.clientX + 'px,' + e.clientY + 'px)'; doc.classList.remove('sk-sem-cursor'); clearTimeout(tm); tm = setTimeout(() => doc.classList.add('sk-sem-cursor'), 2500); });
    window.SK.pronto = true;
  }
  window.SK = {
    total: total, pronto: false,
    ir: (i) => ir(i, { semHash: true, fim: true }),
    final: (on) => { FINAL = !!on; doc.classList.toggle('sk-mov', !on); doc.classList.toggle('sk-final', !!on); secs().forEach((s) => esconder(Array.from(s.querySelectorAll('[data-etapa]')), !on && s.classList.contains('sk-ativo'))); },
    info: () => Array.from(secs()).map((s) => ({ i: +s.dataset.i, layout: s.dataset.layout, secao: +s.dataset.secao, transborda: s.dataset.transborda === '1', corpo: +s.dataset.c, titulo_px: +s.dataset.t,
      imagens: s.querySelectorAll('figure.sk-fig img').length, arte: s.querySelectorAll('.sk-arte-box').length, grafico: !!SLIDES[+s.dataset.i].grafico, diagrama: !!SLIDES[+s.dataset.i].diagrama })),
    reajustar: () => secs().forEach(caber),
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', iniciar); else iniciar();
})();
