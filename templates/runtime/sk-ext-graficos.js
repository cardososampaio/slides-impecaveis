/* slides-impecaveis · extensão de gráficos e diagramas
   Gráficos: pontos, halteres, empilhadas, dispersao, linha (com anotacoes e trecho_final), barras (com anotacao).
   Diagramas: funil, iceberg, matriz, venn.
   Fontes de 30 a 44 nas unidades do viewBox, que o motor desenha perto da escala 1 (piso de 28 px no palco). */
(function () {
  'use strict';
  const X = window.SK_EXT = window.SK_EXT || {};
  const G = X.graficos = X.graficos || {};
  const DG = X.diagramas = X.diagramas || {};
  const A = 'var(--acento)', B = 'var(--acento2)', TINTA = 'var(--tinta)', PAPEL = 'var(--papel)';

  // ---------------------------------------------------------------- auxiliares
  const num = (v) => (typeof v === 'number' ? v : parseFloat(String(v).replace(/[^\d,.-]/g, '').replace(/\.(?=\d{3})/g, '').replace(',', '.')));
  const f1 = (n) => Math.round(n * 10) / 10;
  const larg = (t, tam) => String(t).length * tam * 0.55; // largura aproximada do texto
  const lim = (v, a, b) => Math.max(a, Math.min(b, v));
  const caixa = (W, H, s) => '<svg viewBox="0 0 ' + W + ' ' + H + '" preserveAspectRatio="xMidYMid meet" style="color:var(--tinta)">' + s + '</svg>';
  const halo = (t) => t.replace('<text ', '<text paint-order="stroke" stroke="var(--papel)" stroke-width="10" stroke-linejoin="round" ');
  function fmt(g, aj) {
    const casas = g.casas;
    const loc = (v) => (casas != null ? Number(v).toLocaleString((aj.D && aj.D.idioma) || 'pt-BR', { minimumFractionDigits: casas, maximumFractionDigits: casas }) : aj.loc(v));
    return (v) => (g.formato ? g.formato.replace('{v}', loc(v)) : loc(v) + (g.unidade || ''));
  }
  function marcas(min, max, n) {
    const p0 = (max - min) / (n || 5), p = Math.pow(10, Math.floor(Math.log10(p0))), m = p0 / p;
    const passo = (m < 1.5 ? 1 : m < 3 ? 2 : m < 7 ? 5 : 10) * p, out = [];
    for (let v = Math.ceil(min / passo - 1e-9) * passo; v <= max + passo * 1e-6; v += passo) out.push(+v.toFixed(8));
    return out;
  }
  // cores reais do tema, para escolher texto claro ou escuro sobre cada cor (contraste medido de verdade)
  function rgb(c) {
    c = String(c || '').trim(); let m;
    if ((m = c.match(/^#([0-9a-f]{3})$/i))) return m[1].split('').map((x) => parseInt(x + x, 16));
    if ((m = c.match(/^#([0-9a-f]{6})/i))) return [0, 2, 4].map((i) => parseInt(m[1].substr(i, 2), 16));
    if ((m = c.match(/rgba?\(([^)]+)\)/))) return m[1].split(',').slice(0, 3).map((x) => parseFloat(x));
    return null;
  }
  const hex = (c) => '#' + c.map((v) => Math.round(lim(v, 0, 255)).toString(16).padStart(2, '0')).join('');
  const mistura = (a, b, k) => hex(a.map((v, i) => v * (1 - k) + b[i] * k));
  function lum(c) { const x = c.map((v) => v / 255).map((v) => (v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4))); return 0.2126 * x[0] + 0.7152 * x[1] + 0.0722 * x[2]; }
  const contraste = (a, b) => { const x = lum(a), y = lum(b); return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05); };
  const tok = (n) => rgb(getComputedStyle(document.documentElement).getPropertyValue(n));
  function sobre(cor) { // texto que contrasta mais com a cor (claro do tema ou tinta)
    const c = rgb(cor), claro = tok('--sobre-acento') || [251, 246, 236], escuro = tok('--tinta') || [28, 38, 50];
    if (!c) return 'var(--sobre-acento)';
    const l = lum(claro) > lum(escuro) ? claro : escuro, d = l === claro ? escuro : claro;
    return contraste(c, l) >= contraste(c, d) ? hex(l) : hex(d);
  }
  function paleta(n) { // até 6 cores do tema, em hex
    const a = tok('--acento'), b = tok('--acento2'), p = tok('--papel'), t2 = tok('--tinta2'), t = tok('--tinta');
    if (!a || !b || !p) return [A, B, 'var(--tinta2)', 'var(--linha)', TINTA, A].slice(0, n);
    return [hex(b), hex(a), mistura(b, p, 0.5), mistura(a, p, 0.5), hex(t2 || t), mistura(t2 || t, p, 0.6)].slice(0, n);
  }
  // etapas: abre um grupo que entra numa tecla quando o slide tem "etapas" (sem etapas, o grupo é neutro)
  const gA = (aj, n) => '<g' + (aj.et ? aj.et(n) : '') + '>';
  const cel = (cor) => (cor.charAt(0) === '#' ? sobre(cor) : 'var(--sobre-acento)');
  // coluna de rótulos à esquerda (barras horizontais, pontos, halteres, empilhadas)
  function colunaRotulos(R, W, tam) {
    const maior = Math.max.apply(null, R.map((x) => String(x).length).concat([4]));
    const w = lim(maior * tam * 0.55 + 36, W * 0.16, W * 0.32), n = Math.max(8, Math.floor((w - 36) / (tam * 0.55)));
    return { w: w, n: n };
  }
  function rotulo(aj, x, y, t, tam, n, forte) { return aj.svgTexto(x, y, t, tam, { a: 'end', n: n, meio: true, w: forte ? 700 : 400 }); }
  // anotação curta presa a um ponto (x, y): texto com halo do papel e um fio até o ponto
  function anotar(aj, x, y, texto, W, H, opt) {
    opt = opt || {}; const tam = opt.tam || 32, lh = tam * 1.15;
    const linhas = String(texto).length > (opt.n || 22) ? Math.ceil(String(texto).length / (opt.n || 22)) : 1;
    const hw = Math.min(String(texto).length, opt.n || 22) * tam * 0.55 / 2;
    const cx = lim(x, hw + 6, W - hw - 6);
    let acima = opt.lado !== 'abaixo', y0;
    if (acima && y - 46 - (linhas - 1) * lh - tam < 0) acima = false;
    if (!acima && y + 54 + (linhas - 1) * lh > H) acima = true;
    if (acima) y0 = y - 46 - (linhas - 1) * lh; else y0 = y + 54 + tam * 0.3;
    const fio = acima ? [y - 14, y - 40] : [y + 14, y + 22];
    return '<line x1="' + f1(x) + '" y1="' + f1(fio[0]) + '" x2="' + f1(cx) + '" y2="' + f1(fio[1]) + '" stroke="var(--tinta)" stroke-width="3" data-a="aparece" style="--d:' + (opt.d || 1500) + 'ms"/>' +
      halo(aj.svgTexto(cx, y0, texto, tam, { a: 'middle', n: opt.n || 22, w: 600, anim: (opt.d || 1500) + 100 }));
  }

  // ---------------------------------------------------------------- pontos (estimativa com intervalo)
  G.pontos = function (g, W, H, aj) {
    const R = g.rotulos || [], v = (g.valores || []).map(num), n = R.length, val = fmt(g, aj);
    const lo = (g.inferior || v).map(num), hi = (g.superior || v).map(num);
    const ref = g.referencia == null || g.referencia === false ? null : num(g.referencia === true ? 0 : g.referencia);
    const col = colunaRotulos(R, W, 34), dz = g.destaque || [];
    let mn = Math.min.apply(null, lo.concat(ref == null ? [] : [ref])), mx = Math.max.apply(null, hi.concat(ref == null ? [] : [ref]));
    const pad = (mx - mn || 1) * 0.08; mn = g.min != null ? g.min : mn - pad; mx = g.max != null ? g.max : mx + pad;
    const x0 = col.w + 20, x1 = W - 30, base = H - 66, topo = 6, alt = (base - topo) / Math.max(1, n);
    const Xs = (u) => x0 + ((x1 - x0) * (u - mn)) / (mx - mn);
    let s = '';
    marcas(mn, mx, 5).forEach((t) => {
      s += '<line x1="' + f1(Xs(t)) + '" y1="' + topo + '" x2="' + f1(Xs(t)) + '" y2="' + base + '" stroke="var(--linha)" stroke-width="2"/>';
      s += aj.svgTexto(Xs(t), base + 44, val(t), 30, { a: 'middle' });
    });
    s += '<line x1="' + x0 + '" y1="' + base + '" x2="' + x1 + '" y2="' + base + '" stroke="' + TINTA + '" stroke-width="3"/>';
    if (g.eixo) s += aj.svgTexto(col.w - 22, base + 44, g.eixo, 30, { a: 'end', w: 600 });
    if (ref != null) s += '<line x1="' + f1(Xs(ref)) + '" y1="' + topo + '" x2="' + f1(Xs(ref)) + '" y2="' + base + '" stroke="' + TINTA + '" stroke-width="4" stroke-dasharray="14 10" data-a="aparece" style="--d:150ms"/>';
    R.forEach((r, i) => {
      const y = topo + alt * (i + 0.5), d = dz.indexOf(i) >= 0, cor = d ? A : B, a = Xs(lo[i]), b = Xs(hi[i]), p = Xs(v[i]);
      s += gA(aj, i) + rotulo(aj, col.w - 22, y + 12, r, 34, col.n, d);
      if (b - a > 2) {
        s += '<rect x="' + f1(a) + '" y="' + f1(y - 6) + '" width="' + f1(b - a) + '" height="12" rx="6" fill="' + cor + '" opacity=".75" data-a="cresce-x" style="--d:' + (250 + i * 110) + 'ms"/>';
        [a, b].forEach((xx) => { s += '<line x1="' + f1(xx) + '" y1="' + f1(y - 20) + '" x2="' + f1(xx) + '" y2="' + f1(y + 20) + '" stroke="' + cor + '" stroke-width="5" stroke-linecap="round" data-a="aparece" style="--d:' + (500 + i * 110) + 'ms"/>'; });
      }
      s += '<circle cx="' + f1(p) + '" cy="' + f1(y) + '" r="15" fill="' + cor + '" stroke="' + PAPEL + '" stroke-width="5" data-a="aparece" style="--d:' + (650 + i * 110) + 'ms"/>';
      const tv = val(v[i]), wv = larg(tv, 34);
      const dir = b + 22 + wv <= W - 4, xl = dir ? Math.max(b, p + 16) + 22 : Math.min(a, p - 16) - 22;
      s += aj.svgTexto(xl, y + 12, tv, 34, { a: dir ? 'start' : 'end', w: 700, f: 'var(--f-num)', anim: 800 + i * 110 }) + '</g>';
    });
    return caixa(W, H, s);
  };

  // ---------------------------------------------------------------- halteres (antes e depois)
  G.halteres = function (g, W, H, aj) {
    const R = g.rotulos || [], a = (g.antes || []).map(num), d = (g.depois || []).map(num), n = R.length, val = fmt(g, aj);
    const nomes = g.nomes || ['antes', 'depois'], col = colunaRotulos(R, W, 34), dz = g.destaque || [];
    const todos = a.concat(d), mn = g.min != null ? g.min : Math.min(0, Math.min.apply(null, todos)), mx = g.max != null ? g.max : Math.max.apply(null, todos) * 1.04;
    const wv = Math.max.apply(null, todos.map((x) => larg(val(x), 34))) + 30;
    const x0 = col.w + wv, x1 = W - wv, topo = 76, alt = (H - topo - 6) / Math.max(1, n);
    const Xs = (u) => x0 + ((x1 - x0) * (u - mn)) / (mx - mn);
    let s = '';
    R.forEach((r, i) => {
      const y = topo + alt * (i + 0.5), xa = Xs(a[i]), xd = Xs(d[i]), cresce = xd >= xa, forte = dz.indexOf(i) >= 0;
      s += '<line x1="' + x0 + '" y1="' + f1(y) + '" x2="' + x1 + '" y2="' + f1(y) + '" stroke="var(--linha)" stroke-width="2"/>';
      s += gA(aj, i) + rotulo(aj, col.w - 22, y + 12, r, 34, col.n, forte);
      s += '<rect x="' + f1(Math.min(xa, xd)) + '" y="' + f1(y - 7) + '" width="' + f1(Math.abs(xd - xa)) + '" height="14" rx="7" fill="' + (forte ? A : 'var(--tinta2)') + '" opacity="' + (forte ? 0.9 : 0.45) + '" data-a="cresce-x" style="--d:' + (400 + i * 110) + 'ms"/>';
      s += '<circle cx="' + f1(xa) + '" cy="' + f1(y) + '" r="17" fill="' + PAPEL + '" stroke="' + B + '" stroke-width="7" data-a="aparece" style="--d:' + (200 + i * 110) + 'ms"/>';
      s += '<circle cx="' + f1(xd) + '" cy="' + f1(y) + '" r="19" fill="' + A + '" data-a="aparece" style="--d:' + (700 + i * 110) + 'ms"/>';
      s += aj.svgTexto(cresce ? xa - 32 : xa + 32, y + 12, val(a[i]), 32, { a: cresce ? 'end' : 'start', anim: 300 + i * 110 });
      s += aj.svgTexto(cresce ? xd + 34 : xd - 34, y + 12, val(d[i]), 34, { a: cresce ? 'start' : 'end', w: 700, f: 'var(--f-num)', anim: 800 + i * 110 });
      if (i === 0) { // nomes das séries escritos no próprio gráfico, sobre a primeira linha
        s += aj.svgTexto(xa + (cresce ? 8 : -8), topo - 30, nomes[0], 32, { a: cresce ? 'end' : 'start', w: 700, anim: 200 });
        s += aj.svgTexto(xd + (cresce ? -8 : 8), topo - 30, nomes[1], 32, { a: cresce ? 'start' : 'end', w: 700, anim: 700 });
        s += '<line x1="' + f1(xa) + '" y1="' + (topo - 22) + '" x2="' + f1(xa) + '" y2="' + f1(y - 22) + '" stroke="' + B + '" stroke-width="3"/>' +
          '<line x1="' + f1(xd) + '" y1="' + (topo - 22) + '" x2="' + f1(xd) + '" y2="' + f1(y - 24) + '" stroke="' + A + '" stroke-width="3"/>';
      }
      s += '</g>';
    });
    return caixa(W, H, s);
  };

  // ---------------------------------------------------------------- empilhadas (100% ou absolutas)
  G.empilhadas = function (g, W, H, aj) {
    const R = g.rotulos || [], S = (g.series || []).slice(0, 6), n = R.length, pc = g.percentual !== false;
    const cores = paleta(S.length), col = colunaRotulos(R, W, 34), val = fmt(pc ? Object.assign({}, g, { unidade: g.unidade != null ? g.unidade : '%', casas: g.casas != null ? g.casas : 0 }) : g, aj);
    const tot = R.map((_, i) => S.reduce((t, sr) => t + num(sr.valores[i] || 0), 0)), mx = pc ? 1 : Math.max.apply(null, tot) * (g.total === false ? 1 : 1.14);
    const x0 = col.w, x1 = W - 10;
    // nomes das séries sobre a primeira barra: uma ou duas fileiras, sem caixa de legenda
    const meio = [], w0 = [];
    let acc = 0; S.forEach((sr) => { const v = num(sr.valores[0] || 0) / (pc ? tot[0] : 1); const a = x0 + (x1 - x0) * acc / mx; acc += v; meio.push((a + x0 + (x1 - x0) * acc / mx) / 2); w0.push(larg(sr.nome, 30)); });
    const coloca = (idx) => { let fim = -1e9; return idx.map((k) => { let x = Math.max(meio[k] - w0[k] / 2, fim + 26); x = Math.min(x, W - w0[k]); fim = x + w0[k]; return [k, x]; }); };
    let fil = [coloca(S.map((_, k) => k))];
    const sobra = (f) => f.some(([k, x], j) => j && x < f[j - 1][1] + w0[f[j - 1][0]] + 20) || f.some(([k, x]) => Math.abs(x + w0[k] / 2 - meio[k]) > 140);
    if (sobra(fil[0])) fil = [coloca(S.map((_, k) => k).filter((k) => k % 2 === 0)), coloca(S.map((_, k) => k).filter((k) => k % 2 === 1))];
    const topo = fil.length * 50 + 34, alt = (H - topo) / Math.max(1, n), bh = Math.min(alt * 0.72, 240), tn = bh >= 120 ? 40 : 32;
    let s = '';
    fil.forEach((f, r) => f.forEach(([k, x]) => {
      const yt = 34 + r * 50, yb = topo + (alt - bh) / 2 - 6;
      s += aj.svgTexto(x, yt, S[k].nome, 30, { w: 700, anim: 300 + k * 90 });
      s += '<path d="M' + f1(x + w0[k] / 2) + ' ' + (yt + 10) + 'L' + f1(meio[k]) + ' ' + f1(yb) + '" stroke="' + cores[k] + '" stroke-width="4" fill="none" data-a="aparece" style="--d:' + (500 + k * 90) + 'ms"/>';
    }));
    R.forEach((r, i) => {
      const y = topo + alt * i + (alt - bh) / 2; let ac = 0;
      s += gA(aj, i) + rotulo(aj, x0 - 22, y + bh / 2 + 12, r, 34, col.n, (g.destaque || []).indexOf(i) >= 0);
      S.forEach((sr, k) => {
        const v = num(sr.valores[i] || 0), fr = pc ? v / tot[i] : v, xa = x0 + (x1 - x0) * ac / mx, w = (x1 - x0) * fr / mx; ac += fr;
        s += '<rect x="' + f1(xa) + '" y="' + f1(y) + '" width="' + f1(Math.max(0, w - 3)) + '" height="' + f1(bh) + '" fill="' + cores[k] + '" data-a="cresce-x" style="--d:' + (200 + i * 140 + k * 60) + 'ms"/>';
        const tv = val(pc ? fr * 100 : v);
        if (w > larg(tv, tn) + 18) s += aj.svgTexto(xa + w / 2, y + bh / 2 + tn * 0.36, tv, tn, { a: 'middle', w: 700, f: 'var(--f-num)', cor: cel(cores[k]), anim: 900 + i * 140 });
      });
      if (!pc && g.total !== false) s += aj.svgTexto(x0 + (x1 - x0) * ac / mx + 14, y + bh / 2 + 12, val(tot[i]), 34, { w: 700, f: 'var(--f-num)', anim: 1200 });
      s += '</g>';
    });
    return caixa(W, H, s);
  };

  // ---------------------------------------------------------------- dispersão
  G.dispersao = function (g, W, H, aj) {
    const P = (g.pontos || []).map((p) => ({ x: num(p.x), y: num(p.y), r: p.rotulo })), vx = fmt({ unidade: g.unidade_x, formato: g.formato_x }, aj), vy = fmt({ unidade: g.unidade_y, formato: g.formato_y }, aj);
    const xs = P.map((p) => p.x), ys = P.map((p) => p.y);
    const mnx = g.min_x != null ? g.min_x : Math.min(0, Math.min.apply(null, xs)), mxx = g.max_x != null ? g.max_x : Math.max.apply(null, xs) * 1.06;
    const mny = g.min_y != null ? g.min_y : Math.min(0, Math.min.apply(null, ys)), mxy = g.max_y != null ? g.max_y : Math.max.apply(null, ys) * 1.1;
    const ty = marcas(mny, mxy, 5), tx = marcas(mnx, mxx, 6);
    const x0 = Math.max.apply(null, ty.map((t) => larg(vy(t), 30))) + 26, x1 = W - 16, y0 = H - 104, y1 = 64;
    const Xs = (u) => x0 + ((x1 - x0) * (u - mnx)) / (mxx - mnx), Ys = (u) => y0 - ((y0 - y1) * (u - mny)) / (mxy - mny);
    let s = '';
    ty.forEach((t) => { s += '<line x1="' + x0 + '" y1="' + f1(Ys(t)) + '" x2="' + x1 + '" y2="' + f1(Ys(t)) + '" stroke="var(--linha)" stroke-width="2"/>' + aj.svgTexto(x0 - 14, Ys(t) + 11, vy(t), 30, { a: 'end' }); });
    tx.forEach((t) => { s += aj.svgTexto(Xs(t), y0 + 42, vx(t), 30, { a: 'middle' }); });
    s += '<line x1="' + x0 + '" y1="' + y0 + '" x2="' + x1 + '" y2="' + y0 + '" stroke="' + TINTA + '" stroke-width="3"/><line x1="' + x0 + '" y1="' + y0 + '" x2="' + x0 + '" y2="' + y1 + '" stroke="' + TINTA + '" stroke-width="3"/>';
    if (g.eixo_x) s += aj.svgTexto(x1, H - 8, g.eixo_x, 32, { a: 'end', w: 600 });
    if (g.eixo_y) s += aj.svgTexto(x0 - 14 - (x0 - 26 > 0 ? 0 : 0), 34, g.eixo_y, 32, { a: 'start', w: 600 });
    P.forEach((p, i) => { if (!p.r) s += '<circle cx="' + f1(Xs(p.x)) + '" cy="' + f1(Ys(p.y)) + '" r="11" fill="' + B + '" opacity=".7" data-a="aparece" style="--d:' + (200 + i * 30) + 'ms"/>'; });
    const caixas = [];
    P.filter((p) => p.r).slice(0, 6).forEach((p, j) => {
      const cx = Xs(p.x), cy = Ys(p.y), w = larg(p.r, 32), esq = cx + 26 + w > W - 4;
      let ly = cy + 11; const bx = esq ? cx - 26 - w : cx + 26;
      for (let k = 0; k < 8 && caixas.some((c) => bx < c[0] + c[2] && bx + w > c[0] && Math.abs(ly - c[1]) < 38); k++) ly += (k % 2 ? -1 : 1) * 40 * (k + 1);
      ly = lim(ly, y1 - 20, y0 - 10); caixas.push([bx, ly, w]);
      s += gA(aj, j) + '<circle cx="' + f1(cx) + '" cy="' + f1(cy) + '" r="15" fill="' + A + '" stroke="' + PAPEL + '" stroke-width="4" data-a="aparece" style="--d:' + (900 + j * 120) + 'ms"/>';
      s += halo(aj.svgTexto(esq ? cx - 26 : cx + 26, ly, p.r, 32, { a: esq ? 'end' : 'start', w: 700, anim: 1000 + j * 120 })) + '</g>';
    });
    return caixa(W, H, s);
  };

  // ---------------------------------------------------------------- linha (sobrepõe a nativa): anotacoes e trecho_final
  G.linha = function (g, W, H, aj) {
    const xs = g.rotulos || [], ser = g.series || [{ nome: '', valores: g.valores || [] }], all = [].concat.apply([], ser.map((x) => x.valores.map(num))), val = fmt(g, aj);
    const max = g.max || Math.max.apply(null, all) * 1.1, min = g.min != null ? g.min : 0, x0 = 30, x1 = W - 170, y0 = H - 90, y1 = 50;
    const Xs = (i) => x0 + ((x1 - x0) * i) / Math.max(1, xs.length - 1), Ys = (v) => y0 - ((y0 - y1) * (num(v) - min)) / (max - min);
    const tf = ser.length === 1 ? Math.max(0, Math.min(xs.length - 1, g.trecho_final || 0)) : 0;
    let s = '<line x1="' + x0 + '" y1="' + y0 + '" x2="' + x1 + '" y2="' + y0 + '" stroke="' + TINTA + '" stroke-width="3"/>';
    xs.forEach((t, i) => { if (xs.length <= 8 || i % Math.ceil(xs.length / 8) === 0 || i === xs.length - 1) s += aj.svgTexto(Xs(i), y0 + 44, t, 30, { a: 'middle' }); });
    ser.forEach((sr, k) => {
      const v = sr.valores.map(num), cor = tf ? B : k === 0 ? A : B, li = v.length - 1, ini = v.length - 1 - tf;
      s += gA(aj, k);
      const caminho = (a, b) => v.slice(a, b + 1).map((vv, j) => (j ? 'L' : 'M') + f1(Xs(a + j)) + ' ' + f1(Ys(vv))).join(' ');
      s += '<path d="' + caminho(0, li) + '" fill="none" stroke="' + cor + '" stroke-width="8" stroke-linejoin="round" stroke-linecap="round" data-a="traco" style="--comp:4000;--d:' + (200 + k * 300) + 'ms"/>';
      if (tf) s += '<path d="' + caminho(ini, li) + '" fill="none" stroke="' + A + '" stroke-width="12" stroke-linejoin="round" stroke-linecap="round" data-a="traco" style="--comp:2400;--d:1100ms"/>';
      v.forEach((vv, i) => { s += '<circle cx="' + f1(Xs(i)) + '" cy="' + f1(Ys(vv)) + '" r="' + (tf && i >= ini ? 12 : 9) + '" fill="' + (tf && i >= ini ? A : cor) + '" data-a="aparece" style="--d:' + (900 + i * 60) + 'ms"/>'; });
      const cf = tf ? A : cor;
      s += aj.svgTexto(Xs(li) + 18, Ys(v[li]) + 12, val(v[li]), 40, { w: 700, f: 'var(--f-num)', cor: cf, anim: 1300 });
      if (sr.nome) s += aj.svgTexto(Xs(li) + 18, Ys(v[li]) + 50, sr.nome, 30, { cor: cf, anim: 1400 });
      s += '</g>';
    });
    (g.anotacoes || []).forEach((an, j) => {
      const sr = ser[an.serie || 0] || ser[0], i = lim(an.i | 0, 0, sr.valores.length - 1);
      s += gA(aj, 50 + j) + anotar(aj, Xs(i), Ys(sr.valores[i]), an.texto, x1 + 120, H - 70, { lado: an.lado, d: 1500 + j * 200 }) + '</g>';
    });
    return caixa(W, H, s);
  };

  // ---------------------------------------------------------------- barras com anotação presa ao destaque (sem anotação, a nativa)
  G.barras = function (g, W, H, aj) {
    const nativa = () => { const f = G.barras; delete G.barras; try { return aj.grafico(g, W, H); } finally { G.barras = f; } };
    if (!g.anotacao) return nativa();
    const an = typeof g.anotacao === 'string' ? { texto: g.anotacao } : g.anotacao, v = (g.valores || []).map(num), nB = v.length;
    const i = an.i != null ? an.i : (g.destaque || [])[0] != null ? g.destaque[0] : v.indexOf(Math.max.apply(null, v));
    const tam = 32, lh = tam * 1.15, ncar = 24, linhas = Math.ceil(String(an.texto).length / ncar) + 0.3, fundo = 14 + linhas * lh;
    const base = H - 120, topo = 70, vmax = Math.max.apply(null, v), livre = base - (fundo + 34 + 58);
    const max = Math.max(g.max || 0, vmax * 1.12, (vmax * (base - topo)) / Math.max(80, livre));
    const larg0 = (W - 40) / nB, bw = Math.min(larg0 * 0.62, 190), cx = 20 + i * larg0 + larg0 / 2, h = (base - topo) * (v[i] / max);
    const g2 = Object.assign({}, g, { max: max }); delete g2.anotacao;
    const f = G.barras; delete G.barras; let svg; try { svg = aj.grafico(g2, W, H); } finally { G.barras = f; }
    const hw = Math.min(String(an.texto).length, ncar) * tam * 0.55 / 2, ax = lim(cx, hw + 6, W - hw - 6);
    const extra = gA(aj, 90) + halo(aj.svgTexto(ax, tam + 6, an.texto, tam, { a: 'middle', n: ncar, w: 600, anim: 1500 })) +
      '<line x1="' + f1(ax) + '" y1="' + f1(fundo + 4) + '" x2="' + f1(cx) + '" y2="' + f1(base - h - 66) + '" stroke="var(--tinta)" stroke-width="3" data-a="aparece" style="--d:1400ms"/></g>';
    void bw;
    return svg.replace(/<\/svg>$/, extra + '</svg>');
  };

  // ---------------------------------------------------------------- diagramas
  const nos = (g) => (g.etapas || g.nos || []).map((x) => (typeof x === 'string' ? { rotulo: x } : x));
  const svgD = (W, H, s) => '<svg viewBox="0 0 ' + W + ' ' + H + '" preserveAspectRatio="xMidYMid meet">' + s + '</svg>';

  DG.funil = function (g, W, H, aj) {
    const E = nos(g).slice(0, 5), n = E.length, gap = 16, bh = (H - gap * (n - 1)) / Math.max(1, n), cx = W / 2;
    const wTop = W * 0.98, wBot = W * (n > 3 ? 0.44 : 0.52), cores = paleta(2), dz = g.destaque || [n - 1];
    const larguraEm = (y) => wTop - (wTop - wBot) * (y / H);
    let s = '';
    E.forEach((e, i) => {
      const ya = i * (bh + gap), yb = ya + bh, la = larguraEm(ya) / 2, lb = larguraEm(yb) / 2, d = dz.indexOf(i) >= 0;
      const cor = d ? (cores[1] || A) : (cores[0] || B), tc = cel(cor);
      s += '<g' + (aj.et ? aj.et(i) : '') + ' data-a="sobe" style="--d:' + (150 + i * 170) + 'ms"><path d="M' + f1(cx - la) + ' ' + f1(ya) + 'H' + f1(cx + la) + 'L' + f1(cx + lb) + ' ' + f1(yb) + 'H' + f1(cx - lb) + 'Z" fill="' + cor + '"/>';
      const temV = e.valor != null && e.valor !== '';
      const nmax = Math.max(10, Math.floor((lb * 2 - 60) / (36 * 0.55)));
      if (temV) {
        s += aj.svgTexto(cx, ya + bh / 2 - 4, String(e.valor), Math.min(64, bh * 0.36), { a: 'middle', w: 700, f: 'var(--f-num)', cor: tc });
        s += aj.svgTexto(cx, ya + bh / 2 + Math.min(44, bh * 0.26), e.rotulo || '', 34, { a: 'middle', n: nmax, cor: tc, w: 600 });
      } else s += aj.svgTexto(cx, ya + bh / 2 + 14, e.rotulo || '', 42, { a: 'middle', n: nmax, meio: true, w: 700, f: 'var(--f-titulo)', cor: tc });
      s += '</g>';
    });
    return svgD(W, H, s);
  };

  DG.iceberg = function (g, W, H, aj) {
    const ac = (g.acima || []).slice(0, 2), ab = (g.abaixo || []).slice(0, 3), agua = H * 0.34, cx = W / 2;
    let s = '<rect x="0" y="' + f1(agua) + '" width="' + W + '" height="' + f1(H - agua) + '" fill="' + B + '" opacity=".16" data-a="aparece" style="--d:0ms"/>';
    // massa submersa e ponta
    s += '<path d="M' + f1(cx - W * 0.14) + ' ' + f1(agua) + 'L' + f1(W * 0.06) + ' ' + f1(H * 0.6) + 'L' + f1(W * 0.16) + ' ' + f1(H * 0.9) + 'L' + f1(cx) + ' ' + f1(H * 0.995) + 'L' + f1(W * 0.86) + ' ' + f1(H * 0.88) + 'L' + f1(W * 0.95) + ' ' + f1(H * 0.56) + 'L' + f1(cx + W * 0.15) + ' ' + f1(agua) + 'Z" fill="' + PAPEL + '" stroke="' + TINTA + '" stroke-width="4" stroke-linejoin="round" data-a="revela-baixo" style="--d:200ms"/>';
    s += '<path d="M' + f1(cx - W * 0.14) + ' ' + f1(agua) + 'L' + f1(cx - W * 0.04) + ' ' + f1(H * 0.05) + 'L' + f1(cx + W * 0.03) + ' ' + f1(H * 0.12) + 'L' + f1(cx + W * 0.15) + ' ' + f1(agua) + 'Z" fill="' + A + '" stroke="' + TINTA + '" stroke-width="4" stroke-linejoin="round" data-a="sobe" style="--d:100ms"/>';
    // linha d'água ondulada que se desenha
    let onda = 'M0 ' + f1(agua); for (let x = 0; x < W; x += 60) onda += 'q15 -12 30 0t30 0';
    s += '<path d="' + onda + '" fill="none" stroke="' + TINTA + '" stroke-width="5" stroke-linecap="round" data-a="traco" style="--comp:' + Math.round(W * 1.3) + ';--d:400ms"/>';
    const wl = cx - W * 0.14 - 30, nl = Math.max(10, Math.floor(wl / (40 * 0.55)));
    ac.forEach((t, j) => { s += gA(aj, 0) + aj.svgTexto(j ? W - 4 : 4, agua * 0.5 + 14, t, 40, { a: j ? 'end' : 'start', n: nl, meio: true, w: 700, f: 'var(--f-titulo)', anim: 500 + j * 150 }) + '</g>'; });
    const zona0 = agua + (H - agua) * 0.14, zona1 = H * 0.86, passo = (zona1 - zona0) / Math.max(1, ab.length);
    ab.forEach((t, j) => { s += gA(aj, 1 + j) + aj.svgTexto(cx, zona0 + passo * (j + 0.5) + 14, t, 40, { a: 'middle', n: 30, meio: true, w: 600, anim: 900 + j * 180 }) + '</g>'; });
    return svgD(W, H, s);
  };

  DG.matriz = function (g, W, H, aj) {
    const ex = g.eixo_x || ['baixo', 'alto'], ey = g.eixo_y || ['baixo', 'alto'], Q = g.quadrantes || [], dz = g.destaque;
    const ly = Math.min(W * 0.2, Math.max.apply(null, ey.map((t) => Math.min(String(t).length, 10))) * 32 * 0.55 + 40);
    const x0 = ly + 10, y1 = H - 112, gap = 18, qw = (W - x0 - gap) / 2, qh = (y1 - gap) / 2;
    let s = '';
    // eixos com seta, extremos escritos nas pontas
    s += '<path d="M' + (x0 - 6) + ' ' + (y1 + 12) + 'H' + (W - 4) + 'M' + (x0 - 6) + ' ' + (y1 + 12) + 'V4" stroke="' + TINTA + '" stroke-width="4" fill="none" data-a="traco" style="--comp:3000;--d:100ms"/>';
    s += aj.svgTexto(x0, y1 + 56, ex[0], 32, { anim: 300 }) + aj.svgTexto(W - 4, y1 + 56, ex[1], 32, { a: 'end', w: 700, anim: 300 });
    s += aj.svgTexto(x0 - 22, y1 - 4, ey[0], 32, { a: 'end', n: 10, anim: 300 }) + aj.svgTexto(x0 - 22, 40, ey[1], 32, { a: 'end', n: 10, w: 700, anim: 300 });
    if (g.nome_x) s += aj.svgTexto(x0 + (W - x0) / 2, H - 8, g.nome_x, 34, { a: 'middle', w: 700, anim: 400 });
    if (g.nome_y) s += '<g transform="rotate(-90 26 ' + f1(y1 / 2) + ')">' + aj.svgTexto(26, y1 / 2 + 12, g.nome_y, 34, { a: 'middle', w: 700, anim: 400 }) + '</g>';
    Q.slice(0, 4).forEach((t, k) => {
      const x = x0 + (k % 2) * (qw + gap), y = Math.floor(k / 2) * (qh + gap), d = k === dz;
      s += '<g' + (aj.et ? aj.et(k) : '') + ' data-a="sobe" style="--d:' + (300 + k * 150) + 'ms"><rect x="' + f1(x) + '" y="' + f1(y) + '" width="' + f1(qw) + '" height="' + f1(qh) + '" rx="16" fill="' + (d ? A : PAPEL) + '" stroke="' + (d ? A : TINTA) + '" stroke-width="3"/>' +
        aj.svgTexto(x + qw / 2, y + qh / 2 + 14, t, 42, { a: 'middle', n: Math.max(8, Math.floor((qw - 50) / (42 * 0.55))), meio: true, w: 600, f: 'var(--f-titulo)', cor: d ? 'var(--sobre-acento)' : TINTA }) + '</g>';
    });
    return svgD(W, H, s);
  };

  DG.venn = function (g, W, H, aj) {
    const C = nos({ nos: g.conjuntos || g.nos }).slice(0, 3), n = C.length, cores = [A, B, 'var(--tinta2)'];
    let s = '', R, centros, rot;
    if (n <= 2) {
      R = Math.min(H * 0.48, W / 3.2); const d = R * 0.58;
      centros = [[W / 2 - d, H / 2], [W / 2 + d, H / 2]]; rot = [[W / 2 - d - R * 0.5, H / 2], [W / 2 + d + R * 0.5, H / 2]];
    } else {
      R = Math.min(H / 3, W / 3.15); const d = R * 0.62, cy = H / 2 + d * 0.2;
      centros = [0, 1, 2].map((k) => { const a = -Math.PI / 2 + k * 2 * Math.PI / 3; return [W / 2 + Math.cos(a) * d, cy + Math.sin(a) * d]; });
      rot = [0, 1, 2].map((k) => { const a = -Math.PI / 2 + k * 2 * Math.PI / 3; return [W / 2 + Math.cos(a) * d * 2.05, cy + Math.sin(a) * d * 2.05]; });
    }
    const vg = centros.map(() => '');
    centros.forEach((c, k) => { vg[k] += '<circle cx="' + f1(c[0]) + '" cy="' + f1(c[1]) + '" r="' + f1(R) + '" fill="' + cores[k] + '" fill-opacity=".12" stroke="' + cores[k] + '" stroke-width="6" data-a="foco" style="--d:' + (k * 220) + 'ms"/>'; });
    C.forEach((c, k) => { vg[k] += aj.svgTexto(rot[k][0], rot[k][1] + 14, c.rotulo || '', 42, { a: 'middle', n: n <= 2 ? 11 : 12, meio: true, w: 700, f: 'var(--f-titulo)', anim: 500 + k * 200 }); });
    vg.forEach((x, k) => { s += gA(aj, k) + x + '</g>'; });
    if (g.intersecao) {
      const cx = centros.reduce((t, c) => t + c[0], 0) / n, cy = centros.reduce((t, c) => t + c[1], 0) / n;
      s += gA(aj, 9) + halo(aj.svgTexto(cx, cy + 12, g.intersecao, n <= 2 ? 36 : 32, { a: 'middle', n: n <= 2 ? 12 : 10, meio: true, w: 700, anim: 1100 })) + '</g>';
    }
    return svgD(W, H, s);
  };
})();
