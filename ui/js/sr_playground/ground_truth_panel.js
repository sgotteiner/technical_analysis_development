// The ground truth, as he thinks of it (owner, 2026-10-04: "a setup draw is not a single sketch
// its a collection of them with a note that i explain" / "read add remove edit easily").
//
// Grouped by the date he DREW at - his unit of work - with the setups of that date, the drawings
// each one holds, the loose drawings, and the verdicts he recorded there. Every row says what the
// system does with it, and carries the four verbs: go to it, edit it, redraw it, remove it.
// Rendering only; the data is shaped in ground_truth_controller.js.
const esc = s => String(s == null ? '' : s).replace(/[&<>"]/g, c =>
  ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const ICON = { box: '▭', freehand: '✎', line: '╱' };
const money = p => Math.round(p).toLocaleString();

function row(r, setupOptions = []) {
  const strokes = r.strokes > 1 ? ` <span class="hint">· ${r.strokes} strokes</span>` : '';
  const fix = r.kind === 'freehand' ? '' : `<button data-act="redraw" title="Draw it again in place: keeps its label, note, setup and any verdict pointing at it">✎ redraw</button>`;
  // EVERY row carries its collection and can be moved to another or out of all of them: a drawing
  // that could only leave a collection by deleting the collection was stuck in it
  const move = !setupOptions.length ? '' : `<select data-act="assignrow" title="Which collection it belongs to">
      <option value=""${r.setup ? '' : ' selected'}>no collection</option>${setupOptions
        .map(o => `<option value="${o.id}"${o.id === r.setup ? ' selected' : ''}>${esc(o.name)}</option>`).join('')}</select>`;
  // the note is his memory of why he drew it, so it shows when there IS one and stays out of the
  // way when there is not: eleven empty note boxes are what made the old list unreadable
  const note = r.note
    ? `<input class="note" value="${esc(r.note)}" title="why you drew it">`
    : `<button class="addnote" title="Say what it means - you will not remember">＋ note</button>`;
  return `<div class="gt-row${r.scored ? ' scored' : ''}${r.asked ? ' asked' : ''}${r.redrawing ? ' redrawing' : ''}" data-id="${r.id}">
    <span class="k" title="${r.asked ? 'a sketch you were only showing me' : esc(r.kind)}">${ICON[r.kind] || '•'}</span>
    <input class="lab" value="${esc(r.label)}" title="label">${strokes}
    <span class="uses" title="${esc(r.why.join(' · '))}">${r.redrawing
      ? 'draw it again on the chart — Esc cancels' : esc(r.uses.join(' · '))}</span>
    ${move}
    <span class="acts">${note}<button data-act="see" title="Show it on the chart">see</button>${fix}
      <button data-act="del" title="${r.strokes > 1 ? 'Remove all its strokes' : 'Remove it'}">×</button></span>
  </div>`;
}

function verdict(v) {
  const instead = v.replacement ? `<button data-act="instead" title="Show the line you drew instead">drew instead ⤴</button>` : '';
  return `<div class="gt-row verdict ${v.verdict}" data-jid="${v.id}">
    <span class="k">${v.verdict === 'good' ? '✓' : '✗'}</span>
    <span class="lab">${money(v.price)}${v.kind === 'trend' ? ' <span class="hint">(trend)</span>' : ''}</span>
    <span class="uses">your verdict on the code's line</span>
    <span class="acts">${instead}<button data-act="unjudge" title="Take the verdict back">×</button></span>
    <input class="jnote" value="${esc(v.note)}" placeholder="why${v.verdict === 'bad' ? ' not' : ''}?">
  </div>`;
}

function setupBlock(s, setupOptions = []) {
  return `<div class="gt-setup${s.onChart ? ' on-chart' : ''}" data-sid="${s.id}">
    <div class="row"><span class="k">■</span><input class="sname" value="${esc(s.name)}" title="setup name">
      <button data-act="focus" title="Show only this collection on the chart">${s.onChart ? 'on the chart ✓' : 'show alone'}</button>
      <button data-act="delsetup" title="Delete the setup (its drawings stay)">×</button></div>
    <textarea class="snote" rows="2" placeholder="how would you trade it?">${esc(s.note)}</textarea>
    <div class="m ${s.detector.cls}">${esc(s.detector.text)}</div>
    ${s.rows.map(r => row(r, setupOptions)).join('')
      || '<div class="hint">no drawings in it: pick this collection on any row below, or use "+ setup from these"</div>'}
  </div>`;
}

function dayBlock(d, setupOptions) {
  return `<div class="gt-day" data-ts="${d.ts}">
    <div class="row head">
      <button data-act="goday" title="Put &quot;now&quot; back on this date and compute the setup as it was">⤒ ${d.day}</button>
      <span class="hint">${esc(d.summary)}</span>
      <button data-act="newsetup" title="Make a setup from this date's drawings that are in none">+ setup from these</button>
    </div>
    ${d.setups.map(s => setupBlock(s, setupOptions)).join('')}
    ${d.loose.length ? `<div class="gt-loose">${d.loose.map(r => row(r, setupOptions)).join('')}</div>` : ''}
    ${d.verdicts.length ? `<div class="gt-verdicts">${d.verdicts.map(verdict).join('')}</div>` : ''}
  </div>`;
}

export function renderGroundTruth(root, model, h) {
  const { counts: c } = model;
  root.innerHTML = `
    <div class="row">
      <select id="gt-jump" title="Pick a setup or a date and the page goes there">
        <option value="">go to a setup or a date…</option>
        ${model.index.map(i => `<option value="${esc(i.key)}">${esc(i.label)}</option>`).join('')}
      </select>
      <button data-act="newempty" title="Make an empty collection and put drawings in it one by one, whatever else is loose">+ new collection</button>
    </div>
    ${model.usageError ? `<div class="row warn" title="${esc(model.usageError)}">
      <b>Restart <code>scripts/sr_playground.py</code></b> — it is running older code than this page,
      so it cannot say what each drawing is used for and the badges show "?". Everything else here
      is fine.</div>` : ''}
    <div class="row">
      <span class="hint">${c.drawings} drawings · ${c.setups} setups · ${c.verdicts} verdicts</span>
      <label title="Off: only the drawings of the date you are standing on are painted, so dates do not pile up on each other">
        <input type="checkbox" id="gt-all" ${model.showAllDates ? 'checked' : ''}> every date on the chart</label>
      ${model.focusSetup ? '<span class="hint">· one collection is on the chart</span>' : ''}
    </div>
    ${model.empty.length ? `<div class="gt-day empty"><div class="row head">
        <span class="hint">setups with no drawings yet — put drawings in them from the rows below</span></div>
      ${model.empty.map(s => setupBlock(s, model.setupOptions)).join('')}</div>` : ''}
    ${model.days.map(d => dayBlock(d, model.setupOptions)).join('')
      || '<div class="hint">nothing yet: pick Line or Box and click twice on the chart</div>'}`;

  const find = (el, sel) => el.closest(sel);
  const rowOf = el => model.byId[find(el, '.gt-row').dataset.id];
  root.querySelector('#gt-all').onchange = e => h.onShowAllDates(e.target.checked);
  root.querySelector('#gt-jump').onchange = e => { if (e.target.value) h.onJump(e.target.value); };
  root.querySelectorAll('[data-act]').forEach(el => {
    const act = el.dataset.act;
    if (act === 'assignrow') {
      el.onchange = () => h.onAssignRow(rowOf(el), el.value || null);
      return;
    }
    el.onclick = () => (({
      goday: () => h.onGoToDate(+find(el, '.gt-day').dataset.ts),
      newsetup: () => h.onNewSetupFrom(+find(el, '.gt-day').dataset.ts),
      newempty: () => h.onNewSetup(),
      delsetup: () => h.onDeleteSetup(find(el, '.gt-setup').dataset.sid),
      focus: () => h.onFocusSetup(find(el, '.gt-setup').dataset.sid),
      see: () => h.onSee(rowOf(el)),
      redraw: () => h.onRedraw(rowOf(el)),
      del: () => h.onDelete(rowOf(el)),
      unjudge: () => h.onUnjudge(find(el, '.gt-row').dataset.jid),
      instead: () => h.onShowReplacement(find(el, '.gt-row').dataset.jid),
    }[act] || (() => {}))());
  });
  root.querySelectorAll('.gt-row .lab').forEach(i => {
    i.onchange = () => i.value.trim() && h.onPatch(rowOf(i), { label: i.value.trim() });
  });
  root.querySelectorAll('.gt-row .note').forEach(i => {
    i.onchange = () => h.onPatch(rowOf(i), { note: i.value });
  });
  root.querySelectorAll('.gt-row .addnote').forEach(b => {       // ＋ note becomes the box itself
    b.onclick = () => {
      const i = document.createElement('input');
      i.className = 'note';
      i.placeholder = 'what it means';
      i.onchange = () => i.value.trim() && h.onPatch(rowOf(i), { note: i.value });
      b.replaceWith(i);
      i.focus();
    };
  });
  root.querySelectorAll('.gt-row .jnote').forEach(i => {
    i.onchange = () => h.onVerdictNote(find(i, '.gt-row').dataset.jid, i.value);
  });
  root.querySelectorAll('.gt-setup').forEach(el => {
    const sid = el.dataset.sid, name = el.querySelector('.sname'), note = el.querySelector('.snote');
    name.onchange = () => name.value.trim() && h.onPatchSetup(sid, { name: name.value.trim() });
    note.onchange = () => h.onPatchSetup(sid, { note: note.value });
  });
}
