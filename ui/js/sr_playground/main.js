// S/R playground: settings -> live view at "now"; the owner's drawings -> ground truth.
// This file only WIRES the parts together and owns "now": every behaviour lives in its own module.
import { api } from './api.js';
import { initialState, renderSettings, toRequest } from './settings_panel.js';
import { createSrChart } from './sr_chart.js';
import { createDrawings } from './drawings.js';
import { renderResults } from './results_panel.js';
import { createAnnotations } from './annotations_controller.js';
import { createSetupsController } from './setups_controller.js';
import { createPointsController } from './points_controller.js';
import { createLayers } from './layers.js';
import { createZonesController } from './zones_controller.js';
import { createSketchpad } from './sketchpad.js';
import { createCards } from './cards.js';
import { createTools } from './tools.js';

const $ = id => document.getElementById(id);
const [candles, defaults, saved] = await Promise.all([api.candles(), api.defaults(), api.annotations()]);
const state = initialState(defaults);
let now = candles.length - 1, view = null, request = null, seq = 0, timer = null;

const srChart = createSrChart($('chart'));
const status = (text, cls = 'hint') => { $('status').textContent = text; $('status').className = cls; };

const drawings = createDrawings({ chart: srChart.chart, series: srChart.series, svg: $('overlay'), container: $('chart'),
  onCreate: async shape => {
    // a sketch is several strokes explaining one thing: it waits in the sketchpad until he says
    // what it shows and whether to keep it. Nothing is saved here, so nothing to cancel.
    if (shape.kind === 'freehand') return sketchpad.add(shape.points);
    try {
      const ann = await api.addAnnotation({ ...shape,
        label: $('label').value.trim() || 'unlabelled',
        chart: defaults.chart, drawn_at: candles[now].time });
      annotations.add(ann);
      setups.reload();
      // if it was drawn to answer a rejected line, it belongs to that verdict, not to nothing
      if (!points.linkDrawing(ann.id)) status(`saved ${ann.kind} "${ann.label}"`);
    } catch (e) { status(`not saved: ${e.message}`, 'err'); }
  } });

const annotations = createAnnotations({ root: $('annotations'), count: $('gt-count'), drawings, status,
  saved, getSetups: () => setups.setups(), centerOn,
  onAssign: (a, setupId) => setups.assign(a, setupId),
  onReload: () => setups.reload() });
const sketchpad = createSketchpad({ root: $('sketchpad'), status, chart: drawings,
  getNow: () => now, getCandles: () => candles,
  onSaved: () => annotations.reloadFromServer() });
const setups = createSetupsController({ drawings, getAnnotations: () => annotations.all(),
  setNow: i => setNow(i), status, onChange: () => annotations.refresh() });
const points = createPointsController({ root: $('points'), srChart, drawings, status,
  getCandles: () => candles, getNow: () => now,
  getDrawings: () => annotations.all(),
  armLineTool: () => tools.setTool('line'),
  showDrawing: id => {
    const a = annotations.all().find(x => x.id === id);
    if (a) { annotations.select(a.id); centerOn(a); }
  } });
const zones = createZonesController({ root: $('zones'), drawings, getNow: () => now, status,
  getTrends: () => points.trends() });
const layers = createLayers({ root: $('layers'), onChange: applyLayers });
const tools = createTools({ drawings, status, sketchpad, step: d => setNow(now + d) });

function applyLayers(show) {
  drawings.setVisible({ drawings: show.drawings, detections: show.detections });
  points.setVisible({ dots: show.dots, lines: show.lines, boxes: show.boxes });
  zones.setVisible(show.zones);
  srChart.drawView(show.pipes ? view : null, candles, now);
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

['back7', 'back1', 'fwd1', 'fwd7'].forEach((id, i) => $(id).onclick = () => setNow(now + [-7, -1, 1, 7][i]));
$('date').onchange = e => {
  const ts = Date.parse(e.target.value + 'T00:00:00Z') / 1000, i = candles.findIndex(c => c.time >= ts);
  if (i >= 0) setNow(i);
};
$('labels').innerHTML = defaults.labels.map(l => `<option value="${l}">`).join('');
// the server's view of when the page's files changed; if this page were stale it could not show it
$('build').textContent = defaults.build ? `ui ${defaults.build}` : '';

renderSettings($('settings'), state, defaults, compute);
annotations.refresh();
setups.reload();
const hash = location.hash.slice(1);
const start = /^\d{4}-\d{2}-\d{2}$/.test(hash) ? candles.findIndex(c => c.time >= Date.parse(hash + 'T00:00:00Z') / 1000) : -1;
setNow(start >= 0 ? start : candles.length - 1);
applyLayers(layers.state());        // honour the boxes that were left unticked last time
// the sidebar as cards: the explanation and the swing points open, the rest put away
const cards = createCards({ root: $('side'), open: ['story', 'points'] });
window.__srPlayground = { state: () => ({ now, view, request, annotations: annotations.all(),
  setups: setups.setups(), layers: layers.state(), drawn: srChart.drawn() }),
  setNow, compute, srChart };   // for automated checks
