// The events card: the switches, the arrows that jump from one event to the next across history, and
// the events known at "now", newest first, each saying what decided it (owner, 2026-10-08: "in
// contrast to lines events are not every candle so thats a question how i would see them").

import { meaning, NAMES, sketch } from './event_sketches.js';

export const LETTER = { breakout: 'B', fakeout: 'F', sweep: 'S', retest: 'R', bounce: 'T', trend_change: 'C',
  double_top: 'DT', double_bottom: 'DB', head_shoulders: 'HS', inverse_head_shoulders: 'iHS',
  cup_handle: 'CH', bull_flag: 'BF', bear_flag: 'bF' };
const TYPES = [['breakout', 'breakout'], ['fakeout', 'fakeout'], ['sweep', 'sweep (wick)'], ['retest', 'retest'],
  ['bounce', 'bounce'], ['trend_change', 'trend change']];
const PATTERNS = [['double_top', 'double top'], ['double_bottom', 'double bottom'], ['head_shoulders', 'head & shoulders'],
  ['inverse_head_shoulders', 'inverse H&S'], ['cup_handle', 'cup & handle'], ['bull_flag', 'bull flag'], ['bear_flag', 'bear flag']];
const esc = s => String(s == null ? '' : s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

function switches(state) {
  const boxes = (list, key) => list.map(([v, t]) => `<label><input type="checkbox" data-ek="${key}" value="${v}"`
    + `${state[key].includes(v) ? ' checked' : ''}> ${t}</label>`).join('');
  const num = (key, label, min, max) => `<label>${label} <input data-en="${key}" type="number" min="${min}" max="${max}" value="${state[key]}"></label>`;
  // what the names mean, as pictures (owner, 2026-10-08: "i dont know the names")
  const legend = '<details><summary>what the names mean</summary>' + NAMES.map(n =>
    `<div style="display:flex;gap:8px;align-items:center;margin:4px 0">${sketch(n)}`
    + `<div><b>${n.replace(/_/g, ' ')}</b><div class="hint">${meaning(n)}</div></div></div>`).join('') + '</details>';
  return legend + `<div class="row hint">show or hide them with "events" in the bar above the chart</div>
    <div class="row">events: ${boxes(TYPES, 'types')}</div>
    <div class="row">patterns: ${boxes(PATTERNS, 'patterns')}</div>
    <div class="row">${num('closes', 'breakout closes', 1, 5)}${num('fakeoutWithin', 'fakeout within', 1, 30)} bars
      ${num('retestWithin', 'retest within', 1, 90)} bars
      <label>candle <select data-en="candle">${['off', 'pin', 'engulfing', 'piercing', 'any'].map(v =>
        `<option${state.candle === v ? ' selected' : ''}>${v}</option>`).join('')}</select></label></div>`;
}

export function renderEvents(root, { state, info, now, busy, focus, error }) {
  const list = info ? info.events.slice().reverse() : [];
  const prev = info ? [...info.steps].reverse().find(b => b < now) : undefined;
  const next = info ? info.steps.find(b => b > now) : undefined;
  const rows = list.slice(0, state.recent).map(e => `<div class="m ev-row${focus === e.bar ? ' on' : ''}"`
    + ` data-k="${e.bar}" style="color:${e.direction === 'up' ? '#26a69a' : '#ef5350'}" title="click to see this day's events on the chart">`
    + `<b>${LETTER[e.type]}</b> ${e.date} · ${esc(e.type.replace(/_/g, ' '))} ${e.direction}`
    + `<div class="how">${esc(e.why)}</div></div>`).join('');
  root.innerHTML = switches(state)
    + `<div class="row"><button id="ev-prev"${prev === undefined ? ' disabled' : ''}>◀ previous event</button>`
    + `<button id="ev-next"${next === undefined ? ' disabled' : ''}>next event ▶</button>`
    + (busy ? ' <span class="warn">computing the events… (the first time for these line switches takes ~2 min)</span>' : '')
    + (error ? ` <span class="err">${esc(error)}</span>` : '') + '</div>'
    + (info ? `<div class="m">${info.events.length} events up to now · events on ${info.steps.length} days of history (the arrows jump between them)`
      + (focus ? ' · <a href="#" id="ev-all">show all</a>' : '') + '</div>' : '')
    + rows;
  return { prev, next };
}
