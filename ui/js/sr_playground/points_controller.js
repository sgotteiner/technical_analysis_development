// Swing points and the lines through them.
// Rule "owner" (the default): every recent point gives a level at its own price, and history only
// says how often that price acted before; trend lines come from the recent points only.
// Rule "touches": any line through two points, ranked by touch count (kept for comparison).
import { api } from './api.js';
import { renderPointsPanel } from './points_panel.js';

const COLORS = ['#29b6f6', '#ffca28', '#ab47bc', '#66bb6a'];
const KEY = 'sr_playground_points_v4';
const DEFAULTS = { targetDays: 14, sizesText: '8', show: true, drawLines: true, mode: 'owner',
  tolPct: 1.5, minTouches: 3, maxSlope: '', top: 6, lookback: '', anchorDays: 120, maxHistory: 2 };

export function createPointsController({ root, srChart, getCandles, getNow, status }) {
  let state = { ...DEFAULTS }, info = null, seq = 0;
  try { Object.assign(state, JSON.parse(localStorage.getItem(KEY)) || {}); } catch (e) {}
  const save = () => { try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (e) {} };
  const parseSizes = () => state.sizesText.split(/[,\s]+/).filter(Boolean)
    .map(s => +s / 100).filter(s => s >= 0.005 && s <= 1);

  // a level is drawn as a flat line between its first and last touch
  const asLine = lv => ({ x1: lv.first, y1: Math.log(lv.price), slope: 0, first: lv.first, last: lv.last });
  const drawables = g => state.mode === 'owner'
    ? (g.levels || []).map(asLine).concat(g.trends || [])
    : (g.lines || []);

  async function refresh() {
    draw();
    const now = getNow();
    if (!state.show) {
      info = null;
      srChart.setPointMarkers([]);
      srChart.drawPointLines([], getCandles(), now);
      draw(++seq);
      return;
    }
    const sizes = parseSizes(), mine = ++seq;
    const body = {
      end: now, sizes, target_days: sizes.length ? null : +state.targetDays,
      lookback_days: state.lookback ? +state.lookback : null,
      lines: state.drawLines ? {
        mode: state.mode, tol_pct: +state.tolPct, min_touches: +state.minTouches,
        max_slope_pct: state.maxSlope === '' ? null : +state.maxSlope, top: +state.top,
        anchor_days: +state.anchorDays, max_history: state.maxHistory === '' ? null : +state.maxHistory,
      } : null,
    };
    try {
      const res = await api.points(body);
      if (mine !== seq) return;
      info = res;
      const groups = res.sizes.map((g, i) => ({ color: COLORS[i % COLORS.length], ...g }));
      srChart.setPointMarkers(groups);
      srChart.drawPointLines(state.drawLines ? groups.map(g => ({ color: g.color, lines: drawables(g) })) : [],
        getCandles(), now);
      draw(mine);
    } catch (e) {
      if (mine === seq) { status(`points: ${e.message}`, 'err'); info = null; draw(mine); }
    }
  }

  function draw(answered) {
    renderPointsPanel({ root, state, info, colors: COLORS, candles: getCandles(), answered,
      onChange: (key, value) => { state[key] = value; save(); refresh(); } });
  }

  draw();
  return { refresh };
}
