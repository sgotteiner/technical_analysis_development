// Swing points and the lines through them.
// Rule "owner" (the default): every recent point gives a level at its own price, and history only
// says how often that price acted before; trend lines come from the recent points only.
// Rule "touches": any line through two points, ranked by touch count (kept for comparison).
import { api } from './api.js';
import { renderPointsPanel } from './points_panel.js';
import { createVerdicts } from './verdicts.js';

const COLORS = ['#29b6f6', '#ffca28', '#ab47bc', '#66bb6a'];
const KEY = 'sr_playground_points_v7';      // v7: the band comes from the move, 2 visits is a level
// mergePct 0 = the band is taken from the MOVE RUNNING NOW (a quarter of it). A fixed 1.5% band
// was measured leaving two lines 3% apart inside a 12.7% move - "i dont care about 3% when the
// move is 10%" (owner, 2026-10-05).
// minVisits 2, because a flat top IS two peaks at the same height: at 3 the rule could never
// return the thing he described, and 2 also takes 2026-09-04 from 4 of his 6 lines to 5.
const DEFAULTS = { targetDays: 14, sizesText: '7', show: true, drawLines: true, mode: 'owner',
  tolPct: 1.5, minTouches: 3, maxSlope: '', top: 6, lookback: '', anchorDays: 120, maxHistory: 2,
  mergePct: 0, targets: 2, minVisits: 2, prefer: 'recent' };

export function createPointsController({ root, srChart, drawings, getCandles, getNow, status,
                                         getDrawings = () => [], armLineTool = () => {},
                                         getLayers = () => ({}),
                                         showDrawing = () => {}, onVerdictChange = () => {} }) {
  let state = { ...DEFAULTS }, info = null, seq = 0, presets = [];
  let busy = false, secs = null, inflight = null;      // what the panel says while it is working
  let focus = null, focusAt = null;    // one line of the setup, alone - at the date it was picked
  const show = { dots: true, lines: true, boxes: true, closedots: false, zigzag: false };
  try { Object.assign(state, JSON.parse(localStorage.getItem(KEY)) || {}); } catch (e) {}
  const save = () => { try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (e) {} };
  const parseSizes = () => state.sizesText.split(/[,\s]+/).filter(Boolean)
    .map(s => +s / 100).filter(s => s >= 0.005 && s <= 1);

  // a level is drawn as a flat line between its first and last touch
  const asLine = lv => ({ x1: lv.first, y1: Math.log(lv.price), slope: 0, first: lv.first, last: lv.last });
  const drawables = g => state.mode === 'touches'
    ? (g.lines || [])
    : (g.levels || []).map(asLine).concat(g.trends || []);   // "owner" and "moves" both give levels

  // a verdict is ground truth, so the ground truth card has to hear about it too
  const verdicts = createVerdicts({ status, redraw: () => { draw(); onVerdictChange(); },
    armLineTool, showDrawing,
    getNowTime: () => getCandles()[getNow()].time,
    getSettings: () => { const { presetName, ...settings } = state; return settings; } });

  async function refresh() {
    if (inflight) inflight.abort();        // its answer is already superseded: stop waiting for it
    inflight = null;
    const now = getNow();
    // one line shown alone belongs to the date it was picked at. Carrying it to another date left
    // the chart empty - the role may not exist there, and the setup is a different setup
    // (owner, 2026-10-05: "went some 7d and it doesnt show").
    if (focus !== null && focusAt !== now) { focus = null; focusAt = null; }
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
    // and say it at the TOP as well: the lines are the slow part, and the panel saying so is no
    // use when he is looking at the chart (owner, 2026-10-05: "if its calculating i would like to
    // see it on the top not only inside the swing points card")
    status('computing the lines…', 'warn');
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
      // what is switched on in his window, so the server log can say it (owner, 2026-10-07:
      // "pipes is not checked do you see my fucking window?")
      layers: getLayers(),
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
      status(`lines in ${secs.toFixed(2)} s`);
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
    // the close-measured dots, beside the high/low ones: yellow squares (owner, 2026-10-07)
    const closeDots = show.closedots && !focus
      ? groups.map(g => ({ color: '#ffca28', shape: 'square', points: g.close_points || [] })) : [];
    srChart.setPointMarkers((show.dots && !focus ? groups : []).concat(closeDots));
    drawings.setZigzag(show.zigzag && !focus ? groups.flatMap(g => g.zigzag || []) : []);
    // the boxes of the LINES, not of every dot: where price worked each level, as zones
    // (owner, 2026-10-05: "i want only the related boxes to the calculated lines")
    drawings.setSwings(!show.boxes ? []
      : groups.flatMap(g => picked(g).flatMap(l =>
          (l.zones || []).map(z => ({ ...z, role: l.role, detail: !!focus })))));
    // the touch points are the dots a CALCULATED LINE was built from, so they belong to that layer:
    // unticking "calculated lines" and still seeing them is the line without the line (owner,
    // 2026-10-04: "i unchecked the calculated lines but still see the touch points")
    drawings.setUsed(!(show.lines && state.drawLines) ? []
      : groups.flatMap(g => picked(g).flatMap(l =>
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
      focus, onFocus: role => { focus = role; focusAt = role === null ? null : getNow(); paint(); draw(); },
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

  return { refresh, trends, verdicts, linkDrawing: verdicts.linkDrawing,
    busy: () => busy,          // the lines are the slow part: nothing else may claim the top bar
    setVisible(layers) { Object.assign(show, layers); paint(); } };
}
