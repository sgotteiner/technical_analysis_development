// His ground truth, with CRUD over all of it (owner, 2026-10-04: "read add remove edit easily.
// crud principles"). This file owns the DRAWINGS; the setups live in setups_controller.js and the
// verdicts in verdicts.js and are passed in, so no two surfaces can disagree about them. What the
// system actually reads is asked of the server (/api/ground-truth/usage), never decided here.
//
// The model is ground_truth_model.js, the rendering ground_truth_panel.js.
import { api } from './api.js';
import { groundTruthModel, day, drawnAt } from './ground_truth_model.js';
import { renderGroundTruth } from './ground_truth_panel.js';

const KEY = 'sr_playground_gt_v1';

export function createGroundTruth({ root, drawings, status, saved, candles, setNow, getNow,
                                    centerOn, armTool, setups, getVerdicts, verdictHandlers }) {
  let items = saved, usage = {}, usageError = null;
  let selected = null, redrawing = null, showAllDates = false, focusSetup = null;
  try { showAllDates = !!(JSON.parse(localStorage.getItem(KEY)) || {}).showAllDates; } catch (e) {}

  const fail = (what, e) => status(`${what}: ${e.message}`, 'err');
  // a failed usage call must SAY so in the card: swallowing it once made every collection look
  // empty against an older server, and the only clue was a 404 in the network tab
  const reloadUsage = () => api.usage().then(
    u => { usage = u; usageError = null; },
    e => { usage = {}; usageError = e.message; });
  const loose = ts => items.filter(a => drawnAt(a) === ts && !(usage[a.id] || {}).setup);

  function paint() {
    // one collection at a time when he picks one - two collections can share a date, so filtering
    // by date alone still "shows everything" (owner, 2026-10-04). Otherwise: this date's drawings,
    // unless he asked for every date at once.
    const here = candles[getNow()].time;
    const focused = focusSetup && (setups.setups().find(s => s.id === focusSetup) || {}).members;
    drawings.setItems(focused ? items.filter(a => focused.includes(a.id))
      : showAllDates ? items
      : items.filter(a => drawnAt(a) === here || a.id === selected));
    drawings.select(selected);
  }

  let lastModel = {};

  function refresh() {
    paint();
    lastModel = groundTruthModel({ items, usage, setups: setups.setups(),
      evaluation: setups.evaluation(), verdicts: getVerdicts(), showAllDates, usageError,
      focusSetup, redrawingId: redrawing ? redrawing.row.id : null });
    renderGroundTruth(root, lastModel, handlers);
  }

  const after = async () => { await Promise.all([reloadUsage(), setups.reload()]); refresh(); };

  const handlers = {
    onShowAllDates(on) {
      showAllDates = on;
      focusSetup = null;                 // "every date" and "one collection" cannot both be true
      try { localStorage.setItem(KEY, JSON.stringify({ showAllDates })); } catch (e) {}
      refresh();
    },
    /** Click a collection's header to show only it on the chart; click it again for everything. */
    onFocusSetup(id) {
      focusSetup = focusSetup === id ? null : id;
      refresh();
      status(focusSetup ? 'showing that collection alone — click its name again for the rest'
                        : 'showing everything drawn on this date');
    },
    onGoToDate(ts) {
      const i = candles.findIndex(c => c.time >= ts);
      if (i >= 0) { setNow(i); status(`"now" is back on ${day(ts)}`); }
    },
    /** Pick a setup or a date and be taken to it: "now" goes to its date and the card scrolls to
     *  it, so finding one of many is a choice from a list, not a scroll (owner, 2026-10-04). */
    onJump(key) {
      const [what, id] = [key.slice(0, key.indexOf(':')), key.slice(key.indexOf(':') + 1)];
      const entry = (lastModel.index || []).find(i => i.key === key);
      focusSetup = what === 'setup' ? id : null;     // picking a collection SHOWS that collection
      if (entry && entry.ts) handlers.onGoToDate(entry.ts);
      else status('that setup has no drawings yet, so it has no date to go to', 'warn');
      refresh();
      setTimeout(() => {
        const el = what === 'setup' ? root.querySelector(`.gt-setup[data-sid="${id}"]`)
                                    : root.querySelector(`.gt-day[data-ts="${id}"]`);
        if (!el) return;
        el.scrollIntoView({ block: 'center' });
        el.classList.add('found');
        setTimeout(() => el.classList.remove('found'), 1600);
      }, 60);
    },
    onSee(r) {
      selected = selected === r.id ? null : r.id;
      refresh();
      const a = items.find(x => x.id === r.id);
      if (a && selected) centerOn(a);
    },
    async onPatch(r, patch) {
      // a sketch he drew as one picture IS one thing: its name and its note land on every stroke,
      // or renaming it would rename one of eight (owner, 2026-10-04: "i wanna name them too")
      const ids = r.strokes > 1 ? r.ids : [r.id];
      try {
        for (const id of ids) {
          const b = await api.patchAnnotation(id, patch);
          items = items.map(x => x.id === b.id ? b : x);
        }
        refresh();
      } catch (e) { fail('not saved', e); }
    },
    async onDelete(r) {
      const what = r.strokes > 1 ? `the ${r.strokes} strokes of "${r.label}"` : `the ${r.kind} "${r.label}"`;
      if (!confirm(`Delete ${what}?`)) return;
      try {
        if (r.group && r.strokes > 1) await api.deleteAnnotationGroup(r.group);
        else await api.deleteAnnotation(r.id);
        items = items.filter(x => !r.ids.includes(x.id));
        await after();
      } catch (e) { fail('not deleted', e); }
    },
    onRedraw(r) {
      // armed for THIS drawing at THIS date. Leaving the date disarms it: an arming that outlives
      // the moment ate the next line drawn elsewhere and silently rewrote the old one instead
      // (measured 2026-10-04: 19 drawings before, 19 after, and the new line never existed).
      redrawing = { row: r, at: candles[getNow()].time };
      armTool(r.kind);
      refresh();
      status(`redrawing "${r.label}": click its ${r.kind === 'box' ? 'two corners' : 'two points'} again (Esc cancels)`);
    },
    /** An empty collection, named, to put drawings into one at a time - the only way to start a
     *  SECOND collection at a date whose drawings are already in one. */
    async onNewSetup() {
      const name = prompt('Name the new collection');
      if (!name || !name.trim()) return;
      try {
        await api.addSetup({ name: name.trim(), members: [] });
        await after();
        status(`"${name.trim()}" is empty — pick it on a drawing's row to put that drawing in it`);
      } catch (e) { fail('collection not created', e); }
    },
    async onNewSetupFrom(ts) {
      const mine = loose(ts);
      if (!mine.length) return status(`every drawing of ${day(ts)} is already in a setup`, 'warn');
      const name = prompt(`Name this setup (${mine.length} drawing${mine.length === 1 ? '' : 's'} of ${day(ts)})`);
      if (!name || !name.trim()) return;
      try {
        await api.addSetup({ name: name.trim(), members: mine.map(a => a.id) });
        await after();
        status(`setup "${name.trim()}" holds ${mine.length} drawing${mine.length === 1 ? '' : 's'}`);
      } catch (e) { fail('setup not created', e); }
    },
    async onAssignRow(r, setupId) {
      // all of its strokes, not just the first: a setup is made of lines and boxes OR of sketches
      // (owner, 2026-10-04), and half a sketch in a setup is not a thing he drew
      for (const id of r.ids) {
        const a = items.find(x => x.id === id);
        if (a) await setups.assign(a, setupId);     // it owns "a drawing is in at most one setup"
      }
      await reloadUsage();
      refresh();
    },
    async onPatchSetup(id, patch) {
      try { await api.patchSetup(id, patch); await after(); } catch (e) { fail('setup not saved', e); }
    },
    async onDeleteSetup(id) {
      const s = setups.setups().find(x => x.id === id);
      if (!confirm(`Delete setup "${s ? s.name : id}"? Its drawings stay.`)) return;
      try { await api.deleteSetup(id); await after(); } catch (e) { fail('setup not deleted', e); }
    },
    onUnjudge: id => verdictHandlers.onUnjudge(id),
    onVerdictNote: (id, note) => verdictHandlers.onNote(id, note),
    onShowReplacement: id => verdictHandlers.onShowReplacement(id),
  };

  return {
    refresh,
    paint,
    all: () => items,
    select(id) { selected = id; refresh(); },
    cancelRedraw() { if (redrawing) { redrawing = null; refresh(); status('redraw cancelled'); } },
    /** "now" moved. Two things belong to the date they were started at and must not outlive it:
     *  an armed redraw, and a collection being shown alone - carrying that one to another date
     *  painted the old date's drawings over the new one ("when i go back i still see the original
     *  drawings", 2026-10-04). */
    onNowMoved() {
      const here = candles[getNow()].time;
      let said = null;
      if (redrawing && redrawing.at !== here) {
        said = `redraw of "${redrawing.row.label}" cancelled — you left the date it was drawn at`;
        redrawing = null;
      }
      const shown = focusSetup && setups.setups().find(s => s.id === focusSetup);
      if (shown && !items.some(a => shown.members.includes(a.id) && drawnAt(a) === here)) {
        focusSetup = null;
        said = said || `"${shown.name}" is not drawn on this date — showing this date instead`;
      }
      if (!said) return paint();
      refresh();
      status(said, 'warn');
    },
    /** A shape just drawn: if a redraw was armed it REPLACES that drawing and keeps everything
     *  hanging off it (its note, its setup, the verdict that points at it). */
    async replaced(shape) {
      if (!redrawing || redrawing.row.kind !== shape.kind) return false;
      const target = redrawing.row;
      redrawing = null;
      try {
        const b = await api.patchAnnotation(target.id, { points: shape.points });
        items = items.map(x => x.id === b.id ? b : x);
        refresh();
        status(`"${b.label}" redrawn — its note, its setup and its verdict kept`);
      } catch (e) { fail('not redrawn', e); }
      return true;
    },
    add(ann) { items = [...items, ann]; reloadUsage().then(refresh); },
    async reloadFromServer() { items = await api.annotations(); await after(); },
    async start() { await reloadUsage(); refresh(); },
  };
}
