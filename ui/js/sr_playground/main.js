// S/R playground: settings -> live view at "now"; the owner's drawings -> ground truth.
import { api } from './api.js';
import { initialState, renderSettings, toRequest } from './settings_panel.js';
import { createSrChart } from './sr_chart.js';
import { createDrawings } from './drawings.js';
import { renderResults, renderAnnotations } from './panels.js';
import { createSetupsController } from './setups_controller.js';
import { createPointsController } from './points_controller.js';
import { createLayers } from './layers.js';
import { createZonesController } from './zones_controller.js';

const $ = id => document.getElementById(id);
const [candles, defaults, saved] = await Promise.all([api.candles(), api.defaults(), api.annotations()]);
const state = initialState(defaults);
let now = candles.length - 1, view = null, request = null, seq = 0, timer = null;
let annotations = saved, selected = null;

const srChart = createSrChart($('chart'));
const status = (text, cls = 'hint') => { $('status').textContent = text; $('status').className = cls; };

const drawings = createDrawings({ chart: srChart.chart, series: srChart.series, svg: $('overlay'), container: $('chart'),
  onCreate: async shape => {
    try {
      const ann = await api.addAnnotation({ ...shape, label: $('label').value.trim() || 'unlabelled',
        chart: defaults.chart, drawn_at: candles[now].time });
      annotations = [...annotations, ann];
      refreshAnnotations(); setups.reload();
      status(`saved ${ann.kind} "${ann.label}"`);
    } catch (e) { status(`not saved: ${e.message}`, 'err'); }
  } });
const setups = createSetupsController({ drawings, getAnnotations: () => annotations, setNow: i => setNow(i), status,
  onChange: () => refreshAnnotations() });
const points = createPointsController({ root: $('points'), srChart, status,
  getCandles: () => candles, getNow: () => now });
const zones = createZonesController({ root: $('zones'), drawings, getNow: () => now, status,
  getTrends: () => points.trends() });
const layers = createLayers({ root: $('layers'), onChange: applyLayers });

function applyLayers(show) {
  drawings.setVisible({ drawings: show.drawings, detections: show.detections });
  points.setVisible({ dots: show.dots, lines: show.lines });
  zones.setVisible(show.zones);
  srChart.drawView(show.pipes ? view : null, candles, now);
}

function refreshAnnotations() {
  drawings.setItems(annotations); drawings.select(selected);
  $('gt-count').textContent = annotations.length ? `(${annotations.length})` : '';
  renderAnnotations($('annotations'), annotations, selected, setups.setups(), {
    onSelect: a => { selected = selected === a.id ? null : a.id; refreshAnnotations(); centerOn(a); },
    onPatch: async (a, patch) => {
      try { const b = await api.patchAnnotation(a.id, patch); annotations = annotations.map(x => x.id === b.id ? b : x); setups.reload(); }
      catch (e) { status(`not saved: ${e.message}`, 'err'); }
    },
    onDelete: async a => {
      if (!confirm(`Delete ${a.kind} "${a.label}"?`)) return;
      try { await api.deleteAnnotation(a.id); annotations = annotations.filter(x => x.id !== a.id); setups.reload(); }
      catch (e) { status(`not deleted: ${e.message}`, 'err'); }
    },
    onAssign: (a, setupId) => setups.assign(a, setupId) });
}

function centerOn(a) {
  const idx = t => candles.findIndex(c => c.time >= t);
  const i0 = idx(a.points[0].time), i1 = idx(a.points[1].time), pad = Math.max(20, (i1 - i0) / 2);
  srChart.chart.timeScale().setVisibleRange({ from: candles[Math.max(0, Math.round(i0 - pad))].time,
    to: candles[Math.min(candles.length - 1, Math.round(i1 + pad))].time });
}

function compute() {
  clearTimeout(timer);
  status('computing…');
  const mine = ++seq;
  timer = setTimeout(async () => {
    const req = toRequest(state, now), t0 = performance.now();
    try {
      const v = await api.view(req);
      if (mine !== seq) return;                       // a newer request is on its way
      view = v; request = req;
      srChart.drawView(layers.state().pipes ? view : null, candles, now);
      renderResults($('results'), view, request, candles);
      const partial = Object.values(view.levels).some(l => !l.complete);
      status(`${((performance.now() - t0) / 1000).toFixed(2)} s${partial ? ' · search incomplete, see results' : ''}`, partial ? 'warn' : 'hint');
    } catch (e) { if (mine === seq) status(e.message, 'err'); }
  }, 120);
}

function setNow(i, refocus = true) {
  now = Math.max(0, Math.min(candles.length - 1, i));
  $('date').value = new Date(candles[now].time * 1000).toISOString().slice(0, 10);
  srChart.setNow(candles, now);
  srChart.drawView(null, candles, now);             // old lines belong to the old "now"
  if (refocus) srChart.focus(candles, now);
  history.replaceState(null, '', '#' + $('date').value);
  compute();
  points.refresh();
  zones.refresh();
}

function setTool(t) {
  drawings.setTool(t);
  document.querySelectorAll('[data-tool]').forEach(b => b.classList.toggle('on', b.dataset.tool === t));
}

['back7', 'back1', 'fwd1', 'fwd7'].forEach((id, i) => $(id).onclick = () => setNow(now + [-7, -1, 1, 7][i]));
document.querySelectorAll('[data-tool]').forEach(b => b.onclick = () => setTool(b.dataset.tool));
$('date').onchange = e => {
  const ts = Date.parse(e.target.value + 'T00:00:00Z') / 1000, i = candles.findIndex(c => c.time >= ts);
  if (i >= 0) setNow(i);
};
document.addEventListener('keydown', e => {
  if (e.target.tagName === 'INPUT' && e.target.type !== 'checkbox') return;   // arrows edit text / number fields
  if (e.key === 'ArrowLeft') setNow(now - (e.shiftKey ? 7 : 1));
  else if (e.key === 'ArrowRight') setNow(now + (e.shiftKey ? 7 : 1));
  else if (e.key === 'Escape') { drawings.cancel(); setTool('pan'); }
  else if (e.key === 'l' || e.key === 'L') setTool('line');
  else if (e.key === 'b' || e.key === 'B') setTool('box');
});
$('labels').innerHTML = defaults.labels.map(l => `<option value="${l}">`).join('');

renderSettings($('settings'), state, defaults, compute);
refreshAnnotations();
setups.reload();
const hash = location.hash.slice(1);
const start = /^\d{4}-\d{2}-\d{2}$/.test(hash) ? candles.findIndex(c => c.time >= Date.parse(hash + 'T00:00:00Z') / 1000) : -1;
setNow(start >= 0 ? start : candles.length - 1);
applyLayers(layers.state());        // honour the boxes that were left unticked last time
window.__srPlayground = { state: () => ({ now, view, request, annotations, setups: setups.setups(),
  layers: layers.state(), drawn: srChart.drawn() }), setNow, compute, srChart };   // for automated checks
