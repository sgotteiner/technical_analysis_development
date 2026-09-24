// The owner's drawings: lines and pattern boxes on an SVG overlay that follows the chart.
// Tools: pan (default), line (click two points), box (click two corners). Esc cancels.
export function createDrawings({ chart, series, svg, container, onCreate }) {
  let tool = 'pan', anchor = null, hover = null, items = [], detected = [], zones = [], selected = null, lastSig = '';
  const show = { drawings: true, detections: true };
  const toPoint = p => (p && p.time !== undefined && p.point)
    ? { time: p.time, price: series.coordinateToPrice(p.point.y) } : null;
  // Own click detection: the chart library drops a quick second click as a double-click.
  let down = null;
  container.addEventListener('pointerdown', e => { down = [e.clientX, e.clientY]; });
  container.addEventListener('pointerup', e => {
    if (!down || Math.hypot(e.clientX - down[0], e.clientY - down[1]) > 4) return;   // a drag pans
    const r = container.getBoundingClientRect(), x = e.clientX - r.left, y = e.clientY - r.top;
    const time = chart.timeScale().coordinateToTime(x);
    click(time === null ? null : { time, price: series.coordinateToPrice(y) });
  });

  function click(pt) {
    if (tool === 'pan' || !pt || !(pt.price > 0)) return;
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

  function shape(kind, points, cls, label) {
    const [a, b] = points.map(xy);
    if (!a || !b) return '';
    const [tx, ty] = kind === 'line' ? a : [Math.min(a[0], b[0]), Math.min(a[1], b[1])];   // a line's label sits at its start
    const text = label ? `<text x="${tx + 3}" y="${ty - 4}">${esc(label)}</text>` : '';
    if (kind === 'line') return `<g class="${cls}"><line x1="${a[0]}" y1="${a[1]}" x2="${b[0]}" y2="${b[1]}"/>${text}</g>`;
    const x = Math.min(a[0], b[0]), y = Math.min(a[1], b[1]);
    return `<g class="${cls}"><rect x="${x}" y="${y}" width="${Math.abs(b[0] - a[0])}" height="${Math.abs(b[1] - a[1])}"/>${text}</g>`;
  }

  function frame() {
    const parts = zones.map(band)
      .concat((show.detections ? detected : []).map(it => shape(it.kind, it.points, 'det', it.label)))
      .concat((show.drawings ? items : []).map(it => shape(it.kind, it.points, it.id === selected ? 'sel' : 'user', it.label)));
    if (anchor && hover) parts.push(shape(tool, [anchor, hover], 'preview', ''));
    const sig = parts.join('');
    if (sig !== lastSig) { svg.innerHTML = STYLE + sig; lastSig = sig; }
    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);

  return {
    setTool(t) { tool = t; anchor = null; container.classList.toggle('drawing', t !== 'pan'); },
    tool: () => tool,
    cancel() { anchor = null; },
    setItems(list) { items = list; },
    select(id) { selected = id; },
    setDetected(list) { detected = list; },
    setZones(list) { zones = list; },
    setVisible(layers) { Object.assign(show, layers); },
  };
}

const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const STYLE = `<style>
  line, rect { stroke-width: 2; fill: none; }
  .user line, .user rect { stroke: #e0e0e0; } .user rect { fill: rgba(224,224,224,0.06); }
  .sel line, .sel rect { stroke: #29b6f6; stroke-width: 3; } .sel rect { fill: rgba(41,182,246,0.1); }
  .preview line, .preview rect { stroke: #29b6f6; stroke-dasharray: 5 4; }
  text { fill: #e0e0e0; font: 11px 'Trebuchet MS', sans-serif; paint-order: stroke; stroke: #131722; stroke-width: 3; }
  .sel text { fill: #29b6f6; }
  .det line, .det rect { stroke: #b388ff; stroke-dasharray: 7 4; } .det rect { fill: rgba(179,136,255,0.08); }
  .det text { fill: #b388ff; }
</style>`;
