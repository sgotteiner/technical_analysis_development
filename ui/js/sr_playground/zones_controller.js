// Price zones: bands on the chart and the ladder read from the current price -
// what am I standing on, what is next up, what is next down.
import { api } from './api.js';

const KEY = 'sr_playground_zones_v1';
const DEFAULTS = { sizePct: 20, bandPct: '', minVisits: 2, nEach: 3, show: false };
const COLOR = { on: '#ffb74d', resistance: '#f23645', support: '#089981' };

export function createZonesController({ root, drawings, getNow, status, onRedraw, getTrends }) {
  let state = { ...DEFAULTS }, view = null, score = null, seq = 0, visible = true;
  try { Object.assign(state, JSON.parse(localStorage.getItem(KEY)) || {}); } catch (e) {}
  const save = () => { try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (e) {} };
  const money = v => Math.round(v).toLocaleString();

  async function refresh() {
    render();
    if (!state.show) { view = null; paint(); render(++seq); return; }
    const mine = ++seq;
    try {
      const got = await api.zones({ end: getNow(), size: +state.sizePct / 100,
        band_pct: state.bandPct === '' ? null : +state.bandPct,
        min_visits: +state.minVisits, n_each: +state.nEach });
      if (mine !== seq) return;
      view = got;
      paint();
      render(mine);
      score = await api.score({ end: getNow(), size: +state.sizePct / 100,
        band_pct: state.bandPct === '' ? null : +state.bandPct, min_visits: +state.minVisits,
        n_each: +state.nEach, trends: getTrends ? getTrends() : [], tol_pct: 3 });
      if (mine === seq) render(mine);
    } catch (e) { if (mine === seq) { status(`zones: ${e.message}`, 'err'); view = null; render(mine); } }
  }

  function paint() {
    const bands = (visible && view ? view.zones : []).map(z => ({
      color: z.at_price_now ? COLOR.on : COLOR[z.label] || COLOR.resistance,
      label: `${money(z.price)} · ${z.visits} visits`,
      visits: z.visit_times,                       // one tick per touch, so the cluster is visible
      points: [{ time: z.first_time, price: z.low }, { time: z.now_time, price: z.high }],
    }));
    drawings.setZones(bands);
    if (onRedraw) onRedraw();
  }

  function ladderRows() {
    if (!view) return '';
    const row = (z, tag) => `<div class="m" style="color:${z.at_price_now ? COLOR.on : COLOR[z.label]}">
      ${tag} <b>${money(z.price)}</b> · ${z.label} · ${z.visits} visits · last ${new Date(z.last_time * 1000).toISOString().slice(0, 10)}
      · ${((z.price / view.price_now - 1) * 100).toFixed(0)}%</div>`;
    const here = view.on ? row(view.on, 'ON') : `<div class="m">between ${money(view.below[0] ? view.below[0].price : 0)} and ${money(view.above[0] ? view.above[0].price : 0)}</div>`;
    return `<div class="m"><b>price ${money(view.price_now)}</b></div>${here}
      ${view.above.map((z, i) => row(z, i === 0 ? 'next up' : 'then')).join('')}
      ${view.below.map((z, i) => row(z, i === 0 ? 'next down' : 'then')).join('')}`;
  }

  // the scoreboard: what the code finds against what the owner drew
  function scoreRows() {
    if (!score || !score.total) return '';
    const rows = score.lines.map(l => `<div class="m" style="color:${l.found ? '#089981' : '#f23645'}">
      ${l.found ? '✓' : '✗'} ${l.label} ${money(l.drawn)}${l.found ? ` — found by ${money(l.by)} (${l.kind})` : ' — missed'}</div>`).join('');
    return `<div class="m"><b>vs my drawings: ${score.found}/${score.total} found, ${score.extra.length} extra</b></div>${rows}
      ${score.extra.length ? `<div class="m hint">extra: ${score.extra.map(e => money(e.price)).join(', ')}</div>` : ''}`;
  }

  function render(answered) {
    if (answered) root.dataset.rev = String(answered);
    root.innerHTML = `<div class="row">
        <label><input type="checkbox" id="zn-show" ${state.show ? 'checked' : ''}> zones</label>
        <label>swing <input id="zn-size" type="number" min="1" max="100" step="1" value="${state.sizePct}">%</label>
        <label>band <input id="zn-band" type="number" min="0.5" step="0.5" value="${state.bandPct}" placeholder="half">%</label>
        <label>min visits <input id="zn-visits" type="number" min="1" max="20" value="${state.minVisits}"></label>
        <label>each way <input id="zn-each" type="number" min="1" max="10" value="${state.nEach}"></label>
      </div>${ladderRows()}${scoreRows()}`;
    const bind = (id, key, isCheck) => {
      const el = root.querySelector(id);
      if (el) el.onchange = e => { state[key] = isCheck ? e.target.checked : e.target.value; save(); refresh(); };
    };
    bind('#zn-show', 'show', true);
    [['#zn-size', 'sizePct'], ['#zn-band', 'bandPct'], ['#zn-visits', 'minVisits'], ['#zn-each', 'nEach']]
      .forEach(([id, key]) => bind(id, key));
  }

  render();
  return { refresh, setVisible(v) { visible = v; paint(); }, count: () => (view ? view.zones.length : 0) };
}
