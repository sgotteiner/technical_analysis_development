// The events at "now": asks /api/events with the line switches and the event switches, puts ONE dot
// on each day that has events, and draws an event's line, box and pattern only once he opens it -
// by clicking its dot (events_popup.js) or its row in the card. "too messy. i want a dot that i can
// click and it opens a card and explains" (owner, 2026-10-08). Previous / next jumps across history.
import { api } from './api.js';
import { LETTER, renderEvents } from './events_panel.js';
import { createEventsPopup } from './events_popup.js';

const KEY = 'sr_playground_events_v2';
// shown or hidden from the layer bar above the chart ("events"), like every other layer: hiding them
// by default with the switch tucked in this card made them look deleted (owner, 2026-10-08: "where
// are my events. you cant just remove stuff. at least leave a checkbox. think im a new person")
const DEFAULTS = { recent: 15, closes: 1, fakeoutWithin: 5, retestWithin: 20, candle: 'off',
  types: ['breakout', 'fakeout', 'sweep', 'retest', 'bounce', 'trend_change'],
  patterns: ['double_top', 'double_bottom', 'head_shoulders', 'inverse_head_shoulders', 'cup_handle', 'bull_flag', 'bear_flag'] };

export function createEventsController({ root, srChart, drawings, card, getCandles, getNow, setNow,
                                         getConcepts, status }) {
  let state = { ...DEFAULTS }, info = null, busy = false, error = null, focus = null, inflight = null;
  let opened = [], visible = true;                 // the events of the day he opened: the only ones drawn in full
  const popup = createEventsPopup({ card, series: srChart.series, getCandles,
    onOpen: events => { opened = events || []; focus = opened.length ? opened[0].bar : null; paint(); draw(); } });
  try { Object.assign(state, JSON.parse(localStorage.getItem(KEY)) || {}); } catch (e) {}
  const save = () => { try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (e) {} };

  async function refresh() {
    if (inflight) inflight.abort();
    if (!visible) { info = null; popup.close(); paint(); draw(); return; }
    const ctrl = new AbortController(); inflight = ctrl;
    busy = true; error = null; draw();
    try {
      info = await api.events({ end: getNow(), concepts: getConcepts(), events: {
        types: state.types, patterns: state.patterns, closes: +state.closes,
        fakeout_within: +state.fakeoutWithin, retest_within: +state.retestWithin, candle: state.candle } }, ctrl.signal);
      if (focus !== null && !info.events.some(e => e.bar === focus)) popup.close();   // not known at this "now"
    } catch (e) {
      if (e.name === 'AbortError') return;
      info = null; error = e.message; status(`events: ${e.message}`, 'err');
    }
    busy = false; inflight = null;
    paint(); draw();
  }

  function paint() {
    const days = popup.setEvents(info ? info.events : []);
    srChart.setEventMarkers(days.map(evs => ({ time: evs[0].time, direction: evs[0].direction,
      mixed: evs.some(e => e.direction !== evs[0].direction) })));
    drawings.setEvents(opened.map(e => ({ ...e, letter: LETTER[e.type], detail: true })));
  }

  function draw() {
    const nav = renderEvents(root, { state, info, now: getNow(), busy, focus, error });
    const on = (sel, f) => { const el = root.querySelector(sel); if (el) el.onclick = f; };
    on('#ev-prev', () => nav.prev !== undefined && setNow(nav.prev));
    on('#ev-next', () => nav.next !== undefined && setNow(nav.next));
    on('#ev-all', e => { e.preventDefault(); popup.close(); });
    root.querySelectorAll('[data-ek]').forEach(el => el.onchange = () => {
      const key = el.dataset.ek;
      state[key] = el.checked ? [...state[key], el.value] : state[key].filter(v => v !== el.value);
      save(); refresh();
    });
    root.querySelectorAll('[data-en]').forEach(el => el.onchange = () => {
      state[el.dataset.en] = el.value; save(); refresh();
    });
    root.querySelectorAll('.ev-row').forEach(row => row.onclick = () => {
      const bar = +row.dataset.k;
      opened = focus === bar ? [] : info.events.filter(e => e.bar === bar);
      focus = opened.length ? bar : null; paint(); draw();
    });
  }

  draw();
  return { refresh, setVisible(on) { if (on !== visible) { visible = on; refresh(); } } };
}
