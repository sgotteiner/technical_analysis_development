// Setup groups: name, how to trade it (note), member drawings, and whether the detector finds it.
const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const pct = v => `${((Math.exp(v) - 1) * 100).toFixed(1)}%`;

function verdict(ev) {
  if (!ev) return '<div class="m hint">detector: no detector for this kind of setup yet</div>';
  if (ev.found) return `<div class="m ok">detector finds it on ${ev.date} (line ${pct(ev.line_gap)} from yours, flag overlap ${(ev.flag_overlap * 100).toFixed(0)}%)</div>`;
  const why = ev.detected ? `line ${pct(ev.line_gap)} from yours, flag overlap ${(ev.flag_overlap * 100).toFixed(0)}%` : ev.reason;
  return `<div class="m err">detector misses it on ${ev.date}: ${esc(why)}</div>`;
}

export function renderSetups(root, setups, drawings, evaluation, { onCreate, onPatch, onDelete }) {
  root.innerHTML = '';
  const byId = Object.fromEntries(drawings.map(d => [d.id, d]));
  setups.forEach(s => {
    const card = document.createElement('div');
    card.className = 'card setup';
    card.innerHTML = `<div class="row"><input class="name"><button title="Delete setup (drawings stay)">×</button></div>
      <textarea class="trade" rows="3" placeholder="how would you trade it?"></textarea>
      <div class="m">${s.members.map(m => byId[m] ? `${byId[m].kind === 'box' ? '▭' : '╱'} ${esc(byId[m].label)}` : '').join(' · ') || 'no drawings: assign them in the list below'}</div>
      ${verdict(evaluation[s.id])}`;
    const name = card.querySelector('.name'), note = card.querySelector('.trade');
    name.value = s.name; note.value = s.note || '';
    name.onchange = () => name.value.trim() && onPatch(s, { name: name.value.trim() });
    note.onchange = () => onPatch(s, { note: note.value });
    card.querySelector('button').onclick = () => onDelete(s);
    root.appendChild(card);
  });
  const add = document.createElement('button');
  add.textContent = '+ New setup';
  add.onclick = () => { const n = prompt('Setup name'); if (n && n.trim()) onCreate(n.trim()); };
  root.appendChild(add);
}
