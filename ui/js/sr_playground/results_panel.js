// The pipe view's result, per level: the ranked pipes, the single lines, and the swing sizes the
// width rules were judged against.
const pct = v => v === null || v === undefined ? '—' : `${((Math.exp(v) - 1) * 100).toFixed(0)}%`;
const day = t => new Date(t * 1000).toISOString().slice(0, 10);
const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

function lineText(ln, candles) {
  const slope = (Math.exp(ln.slope) - 1) * 100;
  return `${ln.touches} touches · ${slope >= 0 ? '+' : ''}${slope.toFixed(2)}%/day · ${day(candles[ln.x1].time)} → ${day(candles[ln.last_touch].time)}`;
}

export function renderResults(root, view, request, candles) {
  if (!view) { root.innerHTML = ''; return; }
  root.innerHTML = Object.entries(view.levels).map(([name, lvl]) => {
    const cfg = request.levels[name];
    const warn = lvl.complete ? '' : `<div class="m warn">search stopped early (budget): only pipes with ≥ ${lvl.checked_down_to} total touches were checked</div>`;
    const pipes = lvl.pipes.length ? lvl.pipes.map((p, i) => `<div class="m"><b>Pipe ${i + 1}</b> · width ${pct(p.width)}<br>
        &nbsp;support: ${lineText(p.support, candles)}<br>&nbsp;resistance: ${lineText(p.resistance, candles)}</div>`).join('')
      : (request.pairs ? '<div class="m">no pipe passes the rules</div>' : '');
    const lines = lvl.lines.map((l, i) => `<div class="m">Line ${i + 1}: ${lineText(l, candles)}</div>`).join('');
    return `<div class="card"><div class="t">${esc(name)} · ${cfg.period}d · ${+(cfg.magnitude * 100).toFixed(2)}%</div>
      <div class="m">${lvl.candidates} candidate lines · swings: largest ${pct(lvl.largest_swing)}, median ${pct(lvl.median_swing)}</div>
      ${warn}${pipes}${lines}</div>`;
  }).join('') || '<div class="hint">no level shown</div>';
}
