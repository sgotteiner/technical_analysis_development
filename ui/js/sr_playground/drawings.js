// The owner's drawings: lines and pattern boxes on an SVG overlay that follows the chart.
// Tools: pan (default), line (click two points), box (click two corners). Esc cancels.
export function createDrawings({ chart, series, svg, container, onCreate }) {
  let tool = 'pan', anchor = null, hover = null, items = [], detected = [], zones = [], selected = null, lastSig = '';
  let pending = [];                 // strokes drawn but not yet kept, asked or discarded
  let swings = [];                  // each peak/valley as the journey it is
  let used = [];                    // the few points the answer was built from
  const show = { drawings: true, detections: true };
  const toPoint = p => (p && p.time !== undefined && p.point)
    ? { time: p.time, price: series.coordinateToPrice(p.point.y) } : null;
  // Own click detection: the chart library drops a quick second click as a double-click.
  let down = null, sketch = null;
  const SKETCH_STEP = 4;        // px between kept points: a thinned path, not every mouse sample

  const at = e => {
    const r = container.getBoundingClientRect(), x = e.clientX - r.left, y = e.clientY - r.top;
    const time = chart.timeScale().coordinateToTime(x);
    return time === null ? null : { time, price: series.coordinateToPrice(y), x, y };
  };

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
    const p = at(e);
    if (p && p.price > 0) sketch.push(p);
    try { container.setPointerCapture(e.pointerId); } catch (err) {}   // not fatal if it is refused
  });
  container.addEventListener('pointermove', e => {
    if (!sketch) return;
    const p = at(e), last = sketch[sketch.length - 1];
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
    const p = at(e);
    click(p && p.price > 0 ? { time: p.time, price: p.price } : null);
  });

  const TWO_POINT_TOOLS = ['line', 'box'];     // what a click-click actually builds

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
  chart.subscribeCrosshairMove(p => { hover = toPoint(p); });

  const xy = pt => {
    const x = chart.timeScale().timeToCoordinate(pt.time), y = series.priceToCoordinate(pt.price);
    return x === null || y === null ? null : [x, y];
  };

  // a zone: a coloured band across its life, the visits marked on it, price and count on the left
  function band(z) {
    const [a, b] = z.points.map(xy);
    if (!a || !b) return '';
    const x = Math.min(a[0], b[0]), y = Math.min(a[1], b[1]);
    const w = Math.max(Math.abs(b[0] - a[0]), 2), h = Math.max(Math.abs(b[1] - a[1]), 2);
    const mid = y + h / 2;
    const ticks = (z.visits || []).map(t => {
      const vx = chart.timeScale().timeToCoordinate(t);
      return vx === null ? '' : `<rect class="visit" x="${vx - 2}" y="${y}" width="4" height="${h}" fill="${z.color}" fill-opacity="0.75"/>`;
    }).join('');
    return `<g class="zone"><rect x="${x}" y="${y}" width="${w}" height="${h}" fill="${z.color}" fill-opacity="0.10"
      stroke="${z.color}" stroke-opacity="0.45"/>
      <line x1="${x}" y1="${mid}" x2="${x + w}" y2="${mid}" stroke="${z.color}" stroke-width="1.5" stroke-opacity="0.9"/>
      ${ticks}<text x="${x + 4}" y="${y - 3}" fill="${z.color}">${esc(z.label)}</text></g>`;
  }

  // "peak is from support to resistance to support and valley is the opposite" (owner)
  function swingBox(b) {
    const x1 = chart.timeScale().timeToCoordinate(b.from_time);
    const x2 = chart.timeScale().timeToCoordinate(b.to_time);
    const yTop = series.priceToCoordinate(b.top), yBot = series.priceToCoordinate(b.bottom);
    if (x1 === null || x2 === null || yTop === null || yBot === null) return '';
    const cls = 'swing ' + b.kind + (b.open ? ' open' : '');
    const x = Math.min(x1, x2), w = Math.abs(x2 - x1), h = Math.max(yBot - yTop, 1);
    // only label a box with room for it: with a few hundred swings on screen the text collides
    // into noise and the structure - the thing he wants to see - disappears behind it
    const note = w < 90 || h < 22 ? '' : '<text x="' + (x + 4) + '" y="' + (yTop + 12) + '">'
      + b.kind + ' ' + b.height_pct.toFixed(0) + '% \u00b7 up ' + b.up_pct.toFixed(0)
      + ' \u00b7 down ' + b.down_pct.toFixed(0) + '</text>';
    return '<g class="' + cls + '"><rect x="' + x + '" y="' + yTop + '" width="' + w
      + '" height="' + h + '"/>' + note + '</g>';
  }

  // the points the answer was actually built from, so they stand out from the hundreds
  function usedPoint(u) {
    const x = chart.timeScale().timeToCoordinate(u.time);
    const y = series.priceToCoordinate(u.price);
    if (x === null || y === null) return '';
    return '<g class="used"><circle cx="' + x + '" cy="' + y + '" r="6"/>'
      + '<text x="' + (x + 9) + '" y="' + (y + 4) + '">' + esc(u.role) + '</text></g>';
  }

  function shape(kind, points, cls, label) {
    if (kind === 'freehand') {                 // a sketch: the whole path, drawn as it was traced
      const pts = points.map(xy).filter(Boolean);
      if (pts.length < 2) return '';
      const text = label ? `<text x="${pts[0][0] + 3}" y="${pts[0][1] - 4}">${esc(label)}</text>` : '';
      return `<g class="${cls} sketch"><polyline points="${pts.map(p => p.join(',')).join(' ')}"/>${text}</g>`;
    }
    const [a, b] = points.map(xy);
    if (!a || !b) return '';
    const [tx, ty] = kind === 'line' ? a : [Math.min(a[0], b[0]), Math.min(a[1], b[1])];   // a line's label sits at its start
    const text = label ? `<text x="${tx + 3}" y="${ty - 4}">${esc(label)}</text>` : '';
    if (kind === 'line') return `<g class="${cls}"><line x1="${a[0]}" y1="${a[1]}" x2="${b[0]}" y2="${b[1]}"/>${text}</g>`;
    const x = Math.min(a[0], b[0]), y = Math.min(a[1], b[1]);
    return `<g class="${cls}"><rect x="${x}" y="${y}" width="${Math.abs(b[0] - a[0])}" height="${Math.abs(b[1] - a[1])}"/>${text}</g>`;
  }

  function frame() {
    const parts = swings.map(swingBox)                 // the structure, under everything else
      .concat(pending.map(p => shape('freehand', p, 'pending', '')))
      .concat(zones.map(band))
      .concat((show.detections ? detected : []).map(it => shape(it.kind, it.points, 'det', it.label)))
      .concat((show.drawings ? items : []).map(it => shape(it.kind, it.points, it.id === selected ? 'sel' : 'user', it.label)));
    parts.push(...used.map(usedPoint));
    if (sketch && sketch.length > 1) parts.push(shape('freehand', sketch, 'preview', ''));
    else if (anchor && hover) parts.push(shape(tool, [anchor, hover], 'preview', ''));
    const sig = parts.join('');
    if (sig !== lastSig) { svg.innerHTML = STYLE + sig; lastSig = sig; }
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
    select(id) { selected = id; },
    setDetected(list) { detected = list; },
    setZones(list) { zones = list; },
    setVisible(layers) { Object.assign(show, layers); },
  };
}

const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const STYLE = `<style>
  line, rect, polyline { stroke-width: 2; fill: none; }
  polyline { stroke-linecap: round; stroke-linejoin: round; }
  .user line, .user rect, .user polyline { stroke: #e0e0e0; } .user rect { fill: rgba(224,224,224,0.06); }
  .sel line, .sel rect, .sel polyline { stroke: #29b6f6; stroke-width: 3; } .sel rect { fill: rgba(41,182,246,0.1); }
  .preview line, .preview rect, .preview polyline { stroke: #29b6f6; stroke-dasharray: 5 4; }
  .sketch polyline { stroke-width: 2.5; }
  .pending polyline { stroke: #ffca28; stroke-width: 2.5; }   /* drawn, not yet decided */
  .swing rect { stroke-width: 1; }
  .swing.peak rect { stroke: rgba(8,153,129,0.55); fill: rgba(8,153,129,0.05); }
  .swing.valley rect { stroke: rgba(242,54,69,0.55); fill: rgba(242,54,69,0.05); }
  .swing.open rect { stroke-dasharray: 6 4; }
  .swing text { font-size: 10px; fill: #787b86; stroke-width: 2; }
  .used circle { fill: none; stroke: #29b6f6; stroke-width: 2; }
  .used text { fill: #29b6f6; font-size: 11px; }
  text { fill: #e0e0e0; font: 11px 'Trebuchet MS', sans-serif; paint-order: stroke; stroke: #131722; stroke-width: 3; }
  .sel text { fill: #29b6f6; }
  .det line, .det rect { stroke: #b388ff; stroke-dasharray: 7 4; } .det rect { fill: rgba(179,136,255,0.08); }
  .det text { fill: #b388ff; }
</style>`;
