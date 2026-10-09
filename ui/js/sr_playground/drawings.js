// Drawing BY HAND: the tools, the pointer, and the repaint loop that keeps the overlay on the
// chart. What each thing looks like is overlay.js; chart <-> pixels is chart_coords.js.
// Tools: pan (default), line (click two points), box (click two corners), sketch. Esc cancels.
import { createCoords } from './chart_coords.js';
import { band, lineDot, shape, swingBox, touchZone, usedPoint, zigzagLine, STYLE } from './overlay.js';
import { eventMark, tradeMark, EVENT_STYLE } from './event_overlay.js';

const TWO_POINT_TOOLS = ['line', 'box'];     // what a click-click actually builds
const SKETCH_STEP = 4;        // px between kept points: a thinned path, not every mouse sample

export function createDrawings({ chart, series, svg, container, onCreate }) {
  const co = createCoords({ chart, series, container });
  let tool = 'pan', anchor = null, hover = null, items = [], detected = [], zones = [], selected = null, lastSig = '';
  let pending = [];                 // strokes drawn but not yet kept, asked or discarded
  let swings = [];                  // each peak/valley as the journey it is
  let used = [];                    // the few points the answer was built from
  let zigzag = [];                  // the zigzag the trend is read from
  let events = [];                  // the events on screen (events_controller.js)
  let lineDots = [];                // a dot at each line's end (line_dots.js)
  let trades = [];                  // the strategy's trades (trades_controller.js)
  const show = { drawings: true, detections: true };
  let down = null, sketch = null;   // own click detection: the library drops a quick second click

  // Ctrl + drag = sketch freely, to explain something (owner, 2026-10-03). Panning is switched off
  // while it is held, or the chart would slide under the hand that is drawing.
  container.addEventListener('pointerdown', e => {
    down = [e.clientX, e.clientY];
    if (!e.ctrlKey && tool !== 'sketch') return;
    // start the stroke on intent alone. Resolving the first point can fail (past the last candle,
    // over the axis), and bailing there left the drag to the chart - which pans, so drawing
    // "moves the screen instead". Panning goes off now; points join as they resolve.
    chart.applyOptions({ handleScroll: false, handleScale: false });
    sketch = [];
    const p = co.at(e);
    if (p && p.price > 0) sketch.push(p);
    try { container.setPointerCapture(e.pointerId); } catch (err) {}   // not fatal if it is refused
  });
  container.addEventListener('pointermove', e => {
    if (!sketch) return;
    const p = co.at(e), last = sketch[sketch.length - 1];
    if (!p || !(p.price > 0)) return;
    if (!last || Math.hypot(p.x - last.x, p.y - last.y) >= SKETCH_STEP) sketch.push(p);
  });
  container.addEventListener('pointerup', e => {
    if (sketch) {
      const path = sketch;
      sketch = null;
      const pans = tool !== 'sketch';           // the sketch tool keeps panning off until you leave it
      chart.applyOptions({ handleScroll: pans, handleScale: pans });
      if (path.length >= 2) onCreate({ kind: 'freehand', points: path.map(p => ({ time: p.time, price: p.price })) });
      return;
    }
    if (!down || Math.hypot(e.clientX - down[0], e.clientY - down[1]) > 4) return;   // a drag pans
    const p = co.at(e);
    click(p && p.price > 0 ? { time: p.time, price: p.price } : null);
  });

  function click(pt) {
    // whitelist, not blacklist: the kind goes straight to the API, so a tool this file does not
    // know about must draw nothing rather than post its own name as a shape
    if (!TWO_POINT_TOOLS.includes(tool) || !pt || !(pt.price > 0)) return;
    if (!anchor) { anchor = pt; return; }
    const kind = tool, a = anchor;
    anchor = null;
    if (kind === 'box' && (a.time === pt.time || a.price === pt.price)) return;
    if (kind === 'line' && a.time === pt.time) return;
    onCreate({ kind, points: a.time <= pt.time ? [a, pt] : [pt, a] });
  }
  chart.subscribeCrosshairMove(p => {
    hover = (p && p.time !== undefined && p.point)
      ? { time: p.time, price: series.coordinateToPrice(p.point.y) } : null;
  });

  function frame() {
    // a touch zone belongs to a line; a swing box is one point's journey
    const parts = swings.map(b => (b.touching_bars === undefined ? swingBox : touchZone)(b, co))
      .concat(pending.map(p => shape('freehand', p, 'pending', '', co)))
      .concat(zones.map(z => band(z, co)))
      .concat((show.detections ? detected : []).map(it => shape(it.kind, it.points, 'det', it.label, co)))
      .concat((show.drawings ? items : []).map(it => shape(it.kind, it.points, it.id === selected ? 'sel' : 'user', it.label, co)));
    parts.push(zigzagLine(zigzag, co));
    parts.push(...events.map(e => eventMark(e, co)));
    parts.push(...lineDots.map(d => lineDot(d, co)));
    parts.push(...trades.map(t => tradeMark(t, co)));
    parts.push(...used.map(u => usedPoint(u, co)));
    if (sketch && sketch.length > 1) parts.push(shape('freehand', sketch, 'preview', '', co));
    else if (anchor && hover) parts.push(shape(tool, [anchor, hover], 'preview', '', co));
    const sig = parts.join('');
    if (sig !== lastSig) { svg.innerHTML = STYLE + EVENT_STYLE + sig; lastSig = sig; }
    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);

  return {
    setTool(t) {
      tool = t; anchor = null;
      container.classList.toggle('drawing', t !== 'pan');
      chart.applyOptions({ handleScroll: t !== 'sketch', handleScale: t !== 'sketch' });
    },
    tool: () => tool,
    cancel() { anchor = null; },
    setItems(list) { items = list; },
    setPending(list) { pending = list; },
    setSwings(list) { swings = list; },
    setUsed(list) { used = list; },
    setZigzag(list) { zigzag = list; },
    setEvents(list) { events = list; },
    setLineDots(list) { lineDots = list; },
    setTrades(list) { trades = list; },
    select(id) { selected = id; },
    setDetected(list) { detected = list; },
    setZones(list) { zones = list; },
    setVisible(layers) { Object.assign(show, layers); },
  };
}
