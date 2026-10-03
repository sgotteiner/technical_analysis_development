// Side-panel lists: the algorithm's result per level, and the owner's drawings (editable).
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

export function renderAnnotations(root, items, selected, setups, { onSelect, onPatch, onDelete, onAssign }) {
  root.innerHTML = '';
  if (!items.length) { root.innerHTML = '<div class="hint">none yet: pick Line or Box, then click twice on the chart</div>'; return; }
  items.forEach(a => {
    const row = document.createElement('div');
    row.className = 'ann' + (a.id === selected ? ' sel' : '');
    const icon = { box: '▭', freehand: '✎' }[a.kind] || '╱';
    const asked = a.purpose === 'ask';          // only shown to explain something; clearable
    if (asked) row.className += ' asked';
    row.innerHTML = `<span title="${asked ? 'sketch you were only showing me' : a.kind}">${icon}</span><input class="lab" title="label"><input class="note" placeholder="note">
      <span class="d">${day(a.points[0].time)}</span><button title="Delete">×</button>
      <select title="setup"><option value="">no setup</option>${setups.map(s => `<option value="${s.id}">${esc(s.name)}</option>`).join('')}</select>`;
    const [lab, note] = row.querySelectorAll('input');
    lab.value = a.label; note.value = a.note || '';
    const pick = row.querySelector('select'), mine = setups.find(s => s.members.includes(a.id));
    pick.value = mine ? mine.id : '';
    pick.onchange = () => onAssign(a, pick.value || null);
    row.onclick = e => { if (!['INPUT', 'BUTTON', 'SELECT', 'OPTION'].includes(e.target.tagName)) onSelect(a); };
    lab.onchange = () => lab.value.trim() && onPatch(a, { label: lab.value.trim() });
    note.onchange = () => onPatch(a, { note: note.value });
    row.querySelector('button').onclick = () => onDelete(a);
    root.appendChild(row);
  });
}
