// Swing points and the lines through them.
// Rule "owner" (the default): every recent point gives a level at its own price, and history only
// says how often that price acted before; trend lines come from the recent points only.
// Rule "touches": any line through two points, ranked by touch count (kept for comparison).
import { api } from './api.js';
import { renderPointsPanel } from './points_panel.js';
import { createVerdicts } from './verdicts.js';

const COLORS = ['#29b6f6', '#ffca28', '#ab47bc', '#66bb6a'];
const KEY = 'sr_playground_points_v6';
// measured against the owner's own lines (2026-09-24): 7% swings, a 1.5% band, 3 visits and
// "the most recently visited cluster wins" reproduce his 58 and 67 and drop his 59, 64 and 70.
const DEFAULTS = { targetDays: 14, sizesText: '7', show: true, drawLines: true, mode: 'owner',
  tolPct: 1.5, minTouches: 3, maxSlope: '', top: 6, lookback: '', anchorDays: 120, maxHistory: 2,
  mergePct: 1.5, targets: 2, minVisits: 3, prefer: 'recent' };

export function createPointsController({ root, srChart, drawings, getCandles, getNow, status,
                                         getDrawings = () => [], armLineTool = () => {},
                                         showDrawing = () => {} }) {
  let state = { ...DEFAULTS }, info = null, seq = 0, presets = [];
  let busy = false, secs = null, inflight = null;      // what the panel says while it is working
  let focus = null;                                    // one line of the setup, alone
  const show = { dots: true, lines: true, boxes: true };
  try { Object.assign(state, JSON.parse(localStorage.getItem(KEY)) || {}); } catch (e) {}
  const save = () => { try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (e) {} };
  const parseSizes = () => state.sizesText.split(/[,\s]+/).filter(Boolean)
    .map(s => +s / 100).filter(s => s >= 0.005 && s <= 1);

  // a level is drawn as a flat line between its first and last touch
  const asLine = lv => ({ x1: lv.first, y1: Math.log(lv.price), slope: 0, first: lv.first, last: lv.last });
  const drawables = g => state.mode === 'touches'
    ? (g.lines || [])
    : (g.levels || []).map(asLine).concat(g.trends || []);   // "owner" and "moves" both give levels

  const verdicts = createVerdicts({ status, redraw: () => draw(), armLineTool, showDrawing,
    getNowTime: () => getCandles()[getNow()].time,
    getSettings: () => { const { presetName, ...settings } = state; return settings; } });

  async function refresh() {
    if (inflight) inflight.abort();        // its answer is already superseded: stop waiting for it
    inflight = null;
    const now = getNow();
    if (!state.show) {
      info = null;
      busy = false; secs = null;
      srChart.setPointMarkers([]);
      srChart.drawPointLines([], getCandles(), now);
      draw(++seq);
      return;
    }
    busy = true;
    draw();                                // say "computing…" BEFORE the wait, not after it
    const sizes = parseSizes(), mine = ++seq;
    const body = {
      end: now, sizes, target_days: sizes.length ? null : +state.targetDays,
      lookback_days: state.lookback ? +state.lookback : null,
      lines: state.drawLines ? {
        mode: state.mode, tol_pct: +state.tolPct, min_touches: +state.minTouches,
        max_slope_pct: state.maxSlope === '' ? null : +state.maxSlope, top: +state.top,
        anchor_days: +state.anchorDays, max_history: state.maxHistory === '' ? null : +state.maxHistory,
        merge_pct: state.mergePct === '' ? 0 : +state.mergePct,
        targets_each_way: state.targets === '' ? 0 : +state.targets,
        min_visits: +state.minVisits, prefer: state.prefer,
      } : null,
    };
    const ctrl = new AbortController(), t0 = performance.now();
    inflight = ctrl;
    try {
      const res = await api.points(body, ctrl.signal);
      if (mine !== seq) return;
      info = res; secs = (performance.now() - t0) / 1000;
      busy = false; inflight = null;
      paint();
      draw(mine);
    } catch (e) {
      if (e.name === 'AbortError') return;          // a newer "now" took over; it owns the panel
      if (mine === seq) {
        busy = false; secs = null; inflight = null;
        status(`points: ${e.message}`, 'err'); info = null; draw(mine);
      }
    }
  }

  function loadPreset(name) {
    const preset = presets.find(p => p.name === name);
    state = preset ? { ...DEFAULTS, ...preset.settings, presetName: name } : { ...state, presetName: '' };
    save();
    refresh();
  }

  async function savePreset(name, note) {
    const { presetName, ...settings } = state;
    try {
      const saved = await api.savePreset({ name, settings, note });
      presets = await api.presets();
      state.presetName = saved.name;
      save();
      status(`preset "${saved.name}" saved on commit ${saved.commit || '?'}`);
      draw();
    } catch (e) { status(`preset not saved: ${e.message}`, 'err'); }
  }

  function paint() {          // put on the chart whatever the layer checkboxes allow
    const groups = (info ? info.sizes : []).map((g, i) => ({ color: COLORS[i % COLORS.length], ...g }));
    const storyLines = g => ((g.story || {}).lines || []);
    const picked = g => storyLines(g).filter(l => !focus || l.role === focus);
    // focused on one line: show that line, the points it was built from, and nothing else - the
    // answer to "i want to click a line and see only whats related to it"
    srChart.setPointMarkers(show.dots && !focus ? groups : []);
    // focused: the boxes the line was actually built from, so the journey behind it shows
    drawings.setSwings(!show.boxes ? []
      : focus ? groups.flatMap(g => picked(g).flatMap(l => l.boxes || []))
              : groups.flatMap(g => g.boxes || []));
    drawings.setUsed(groups.flatMap(g => picked(g).flatMap(l =>
      (l.times || []).map(t => ({ time: t, price: l.price, role: l.role })))));
    const lines = focus
      ? groups.map(g => ({ color: g.color, lines: picked(g).map(l => ({
          x1: Math.min(...(l.points || [getNow()])), y1: Math.log(l.price), slope: 0,
          first: Math.min(...(l.points || [getNow()])), last: getNow() })) }))
      : groups.map(g => ({ color: g.color, lines: drawables(g) }));
    srChart.drawPointLines(show.lines && state.drawLines ? lines : [], getCandles(), getNow());
  }

  // `answered` is the points request this paint is the ANSWER to. Only the request path passes it:
  // `seq` decides which answer wins, so a repaint (a preset, a verdict) must never bump it or the
  // answer already on its way is thrown away as superseded.
  function draw(answered) {
    renderPointsPanel({ root, state, info, colors: COLORS, candles: getCandles(), answered, presets, busy, secs,
      judgements: verdicts.all(), drawings: getDrawings(), verdictError: verdicts.failed(),
      focus, onFocus: role => { focus = role; paint(); draw(); },
      onChange: (key, value) => {
        state[key] = value;
        if (key === 'targetDays') state.sizesText = '';      // a typed size would silently win
        state.presetName = '';
        save();
        refresh();
      },
      onLoadPreset: loadPreset, onSavePreset: savePreset, ...verdicts.handlers });
  }

  draw();
  api.presets().then(list => { presets = list; draw(); }, () => {});
  // the trend lines on screen, for the scoreboard: their price at "now" and their slope
  const trends = () => (info ? info.sizes : []).flatMap(g => (g.trends || []).map(t => ({
    at_now: Math.exp(t.y1 + t.slope * (getNow() - t.x1)), slope_pct_day: Math.expm1(t.slope) * 100 })));

  return { refresh, trends, linkDrawing: verdicts.linkDrawing, setVisible(layers) { Object.assign(show, layers); paint(); } };
}
