// Shaping the ground truth into what he asked to see: his work grouped by the DATE HE DREW AT,
// and inside a date, the setups, then the drawings in none of them, then the verdicts he recorded
// (owner, 2026-10-04: "how do i even know where i drew after a couple of setups in different
// times"). Pure: no DOM, no network, so the grouping can be tested on its own.
export const day = t => new Date(t * 1000).toISOString().slice(0, 10);
export const drawnAt = a => a.drawn_at || a.points[0].time;

/** Several strokes that explain one thing are ONE row: he drew them as one picture with one note.
 *  Which setup a row belongs to is read from the SETUPS themselves, never from the usage answer:
 *  usage says what reads a drawing, and when it cannot be fetched (an older server, a failed call)
 *  the collections must still be the collections (2026-10-04: "i dont see any of them"). */
export function strokeRows(items, usage, setups = []) {
  const memberOf = {};
  for (const s of setups) for (const id of s.members) memberOf[id] = s.id;
  const groups = new Map();
  for (const a of items) {
    const k = a.group || a.id;
    if (!groups.has(k)) groups.set(k, []);
    groups.get(k).push(a);
  }
  return [...groups.values()].map(group => {
    const a = group[0], u = usage[a.id] || { uses: ['?'], why: ['not asked yet'], scored: false };
    return { id: a.id, kind: a.kind, label: a.label, note: a.note || '',
             uses: u.uses, why: u.why || u.uses,
             scored: u.scored, strokes: group.length, group: a.group || null,
             asked: a.purpose === 'ask', ids: group.map(g => g.id), ts: drawnAt(a),
             setup: group.map(g => memberOf[g.id]).find(Boolean) || null };
  });
}

function detector(ev) {
  if (!ev) return { cls: 'hint', text: 'detector: none for this kind of setup yet' };
  if (ev.found) return { cls: 'ok', text: `detector finds it on ${ev.date}` };
  return { cls: 'err',
           text: `detector misses it on ${ev.date}: ${ev.detected ? 'the shapes do not line up' : ev.reason}` };
}

export function groundTruthModel({ items, usage, setups, evaluation, verdicts, showAllDates,
                                   usageError = null, focusSetup = null, redrawingId = null }) {
  const rows = strokeRows(items, usage, setups);
  const byId = Object.fromEntries(rows.map(r => [r.id, r]));
  const days = [...new Set(rows.map(r => day(r.ts)))].sort().reverse().map(d => {
    const mine = rows.filter(r => day(r.ts) === d);
    const here = verdicts.filter(v => day(v.at) === d);
    return {
      day: d, ts: Math.max(...mine.map(r => r.ts)),
      setups: setups.filter(s => mine.some(r => r.setup === s.id)).map(s => ({
        id: s.id, name: s.name, note: s.note || '', detector: detector(evaluation[s.id]),
        onChart: s.id === focusSetup, rows: mine.filter(r => r.setup === s.id) })),
      loose: mine.filter(r => !r.setup),
      verdicts: here,
      // drawings, not rows: the 8 strokes of one sketch are one row but eight drawings
      summary: `${mine.reduce((n, r) => n + r.strokes, 0)} drawings`
        + (here.length ? ` · ${here.length} verdict${here.length === 1 ? '' : 's'}` : '')
        + ` · ${mine.filter(r => r.scored).length} scored`,
    };
  });
  // a setup holding no drawings has no date to sit under, and must still be visible: his own
  // "BTC flat resistance + bull flag" was exactly that, and a card that hides it cannot be filled
  const held = new Set(rows.map(r => r.setup));
  const empty = setups.filter(s => !held.has(s.id)).map(s => ({
    id: s.id, name: s.name, note: s.note || '', detector: detector(evaluation[s.id]),
    onChart: false, rows: [] }));
  // one list of everything he has drawn, to pick from and be taken to: every setup under the date
  // it was drawn at, and every date that has drawings in no setup ("how do i know which dates and
  // setups i drew without such a thing")
  const index = days.flatMap(d => [
    ...d.setups.map(s => ({ key: `setup:${s.id}`, ts: d.ts,
      label: `${d.day} · ${s.name} (${s.rows.reduce((n, r) => n + r.strokes, 0)} drawings)` })),
    ...(d.loose.length ? [{ key: `date:${d.ts}`, ts: d.ts,
      label: `${d.day} · in no setup (${d.loose.reduce((n, r) => n + r.strokes, 0)} drawings)` }] : []),
  ]).concat(empty.map(s => ({ key: `setup:${s.id}`, ts: null, label: `${s.name} (no drawings yet)` })));
  for (const r of rows) r.redrawing = r.id === redrawingId;
  return { byId, days, empty, index, showAllDates, usageError, focusSetup, redrawingId,
    setupOptions: setups.map(s => ({ id: s.id, name: s.name })),
    counts: { drawings: items.length, setups: setups.length, verdicts: verdicts.length } };
}
