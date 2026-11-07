/* slides-impecaveis · extensão de layouts
   numeros (3 a 6 números com contagem, torres opcionais), evidencia (título-afirmação e gráfico grande)
   e linha-do-tempo vertical (orientacao: "vertical"; sem ela, o layout nativo). */
(function () {
  'use strict';
  const X = window.SK_EXT = window.SK_EXT || {};
  const L = X.layouts = X.layouts || {};
  const E = X.espec = X.espec || {};
  // [título máx, título mín, corpo máx, corpo mín, corpo teto, título teto]
  E.numeros = [72, 64, 48, 44, 56, 80];
  E.evidencia = [76, 64, 48, 44, 52, 84];
  const valorDe = (v) => parseFloat(String(v).replace(/[^\d,.-]/g, '').replace(/\.(?=\d{3})/g, '').replace(',', '.'));

  L.numeros = function (s, i, aj) {
    const ns = (s.numeros || []).slice(0, 6), n = ns.length, torres = !!s.torres;
    // sem torres: fileiras (número à esquerda, frase à direita), em uma coluna até 4 números e em duas com 5 ou 6
    const cols = torres ? n : n <= 4 ? 1 : 2, linhas = Math.ceil(n / cols);
    const tl = String(s.titulo || '').length > 48 ? 150 : 80, altL = (1080 - 88 - 96 - tl - 52 - (linhas - 1) * 36) / linhas;
    const nch = Math.max.apply(null, ns.map((x) => String(x.valor).length).concat([1]));
    const fonteN = Math.min(altL * 0.74, (cols === 1 ? 760 : 460) / (nch * 0.6), 250);
    const kn = torres ? { 3: 0.6, 4: 0.5, 5: 0.42, 6: 0.36 }[n] || 0.5 : fonteN / 300;
    const vs = ns.map((x) => valorDe(x.valor)), mx = Math.max.apply(null, vs.filter(isFinite).concat([1e-9]));
    const cel = ns.map((x, j) => {
      const h = isFinite(vs[j]) ? Math.max(2, (100 * vs[j]) / mx) : 0;
      const torre = torres ? '<div class="sk-torre"><svg viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">' +
        '<rect x="0" y="0" width="100" height="100" fill="var(--tinta)" opacity=".07"/>' +
        '<rect x="0" y="' + (100 - h).toFixed(2) + '" width="100" height="' + h.toFixed(2) + '" fill="' + (j === s.destaque ? 'var(--acento)' : 'var(--acento2)') + '" data-a="cresce-y" style="--d:' + (500 + j * 140) + 'ms"/></svg></div>' : '';
      return '<div class="sk-nums-cel sk-caixa' + (j === s.destaque ? ' sk-aqui' : '') + '"' + aj.A('sobe', 250 + j * 140) + '>' +
        '<p class="sk-num" data-role="numero" data-txt data-conta="' + aj.esc(x.valor) + '">' + aj.esc(x.valor) + (x.unidade ? '<small data-role="rotulo">' + aj.esc(x.unidade) + '</small>' : '') + '</p>' +
        (x.texto ? '<p class="sk-texto" data-role="corpo" data-txt>' + aj.md(x.texto) + '</p>' : '') + torre + '</div>';
    }).join('');
    return '<div class="sk-l sk-l-numeros' + (torres ? ' sk-com-torres' : ' sk-fileiras') + '" style="--cols:' + cols + ';--kn:' + kn.toFixed(3) + ';--nch:' + nch + '">' +
      (s.titulo ? '<div class="sk-cab">' + aj.titulo(s) + '</div>' : '') + '<div class="sk-nums sk-caixa sk-zona">' + cel + '</div>' + aj.fonte(s) + '</div>';
  };

  L.evidencia = function (s, i, aj) {
    // o gráfico é desenhado na proporção da área que sobra: título de uma linha ou de duas
    // e numa escala de 1,2 (rótulos de 30 unidades viram 36 px no palco)
    const W = 1366, H = String(s.titulo || '').length > 44 ? 572 : 633;
    const vis = s.grafico ? aj.grafico(s.grafico, W, H) : aj.diagrama(s.diagrama || {}, W, H);
    return '<div class="sk-l sk-l-evidencia"><div class="sk-cab">' + aj.titulo(s) + '</div>' +
      '<div class="sk-ev-graf"' + aj.A('foco', 150) + '>' + vis + '</div>' + aj.fonte(s) + '</div>';
  };

  L['linha-do-tempo'] = function (s, i, aj) {
    if (s.orientacao !== 'vertical') return aj.core['linha-do-tempo'](s, i);
    const ev = (s.eventos || []).slice(0, 6), temValor = ev.some((e) => e.valor != null && e.valor !== '');
    const anoW = Math.max(4, Math.max.apply(null, ev.map((e) => String(e.ano).length)));
    return '<div class="sk-l sk-l-ltv' + (temValor ? ' sk-com-valor' : '') + '" style="--ano-ch:' + anoW + '">' +
      '<div class="sk-ltv-vis">' + (s.imagem ? aj.img(s.imagem, { d: 0, a: 'revela-baixo' }) : aj.arte(650, 1080, i + 2, { letra: s.titulo })) + '</div>' +
      '<div class="sk-ltv-dir">' + (s.titulo ? '<div class="sk-cab">' + aj.titulo(s) + '</div>' : '') +
      '<div class="sk-ltv sk-caixa sk-zona">' + ev.map((e, j) => '<div class="sk-ltv-ev"' + aj.A('sobe', 400 + j * 160) + '>' +
        '<span class="sk-ano" data-role="rotulo" data-txt>' + aj.esc(e.ano) + '</span><p class="sk-texto" data-role="corpo" data-txt>' + aj.md(e.texto || '') + '</p>' +
        (temValor ? '<span class="sk-ltv-valor" data-role="rotulo" data-txt>' + aj.esc(e.valor == null ? '' : e.valor) + '</span>' : '') + '</div>').join('') +
      '</div>' + aj.fonte(s) + '</div></div>';
  };
})();
