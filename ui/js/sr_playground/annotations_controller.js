// The owner's drawings: the list, and everything that changes one. Saving, labelling, deleting and
// assigning a drawing to a setup all live here, not in main.js - the page wires the parts together,
// it should not also BE the drawings editor.
import { api } from './api.js';

const day = t => new Date(t * 1000).toISOString().slice(0, 10);
const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

function render(root, items, selected, setups, { onSelect, onPatch, onDelete, onAssign }) {
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

export function createAnnotations({ root, count, drawings, status, saved,
                                    getSetups, onAssign, onReload, centerOn }) {
  let items = saved, selected = null;

  function refresh() {
    drawings.setItems(items); drawings.select(selected);
    count.textContent = items.length ? `(${items.length})` : '';
    render(root, items, selected, getSetups(), {
      onSelect: a => { selected = selected === a.id ? null : a.id; refresh(); centerOn(a); },
      onPatch: async (a, patch) => {
        try {
          const b = await api.patchAnnotation(a.id, patch);
          items = items.map(x => x.id === b.id ? b : x);
          onReload();
        } catch (e) { status(`not saved: ${e.message}`, 'err'); }
      },
      onDelete: async a => {
        if (!confirm(`Delete ${a.kind} "${a.label}"?`)) return;
        try { await api.deleteAnnotation(a.id); items = items.filter(x => x.id !== a.id); onReload(); }
        catch (e) { status(`not deleted: ${e.message}`, 'err'); }
      },
      onAssign });
  }

  return {
    refresh,
    all: () => items,
    select(id) { selected = id; refresh(); },
    add(ann) { items = [...items, ann]; refresh(); },
    async reloadFromServer() { items = await api.annotations(); refresh(); },
  };
}
