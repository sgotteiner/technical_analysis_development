// Everything the SVG overlay draws, and nothing about how it is drawn BY HAND: the owner's shapes,
// the structure under them, the zones, and the few dots an answer was built from.
// Input and tools live in drawings.js; both share the coordinate helpers in chart_coords.js.
const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

// a zone: a coloured band across its life, the visits marked on it, price and count on the left
export function band(z, { xy, xOf }) {
  const [a, b] = z.points.map(xy);
  if (!a || !b) return '';
  const x = Math.min(a[0], b[0]), y = Math.min(a[1], b[1]);
  const w = Math.max(Math.abs(b[0] - a[0]), 2), h = Math.max(Math.abs(b[1] - a[1]), 2);
  const mid = y + h / 2;
  const ticks = (z.visits || []).map(t => {
    const vx = xOf(t);
    return vx === null ? '' : `<rect class="visit" x="${vx - 2}" y="${y}" width="4" height="${h}" fill="${z.color}" fill-opacity="0.75"/>`;
  }).join('');
  return `<g class="zone"><rect x="${x}" y="${y}" width="${w}" height="${h}" fill="${z.color}" fill-opacity="0.10"
    stroke="${z.color}" stroke-opacity="0.45"/>
    <line x1="${x}" y1="${mid}" x2="${x + w}" y2="${mid}" stroke="${z.color}" stroke-width="1.5" stroke-opacity="0.9"/>
    ${ticks}<text x="${x + 4}" y="${y - 3}" fill="${z.color}">${esc(z.label)}</text></g>`;
}

// "peak is from support to resistance to support and valley is the opposite" (owner)
export function swingBox(b, { xOf, yOf }) {
  const x1 = xOf(b.from_time), x2 = xOf(b.to_time);
  const yTop = yOf(b.top), yBot = yOf(b.bottom);
  if (x1 === null || x2 === null || yTop === null || yBot === null) return '';
  const cls = 'swing ' + b.kind + (b.open ? ' open' : '');
  const x = Math.min(x1, x2), w = Math.abs(x2 - x1), h = Math.max(yBot - yTop, 1);
  // only label a box with room for it: with a few hundred swings on screen the text collides
  // into noise and the structure - the thing he wants to see - disappears behind it
  const note = w < 90 || h < 22 ? '' : '<text x="' + (x + 4) + '" y="' + (yTop + 12) + '">'
    + b.kind + ' ' + b.height_pct.toFixed(0) + '% · up ' + b.up_pct.toFixed(0)
    + ' · down ' + b.down_pct.toFixed(0) + '</text>';
  return '<g class="' + cls + '"><rect x="' + x + '" y="' + yTop + '" width="' + w
    + '" height="' + h + '"/>' + note + '</g>';
}

// the points the answer was actually built from, so they stand out from the hundreds
export function usedPoint(u, { xOf, yOf }) {
  const x = xOf(u.time), y = yOf(u.price);
  if (x === null || y === null) return '';
  return '<g class="used"><circle cx="' + x + '" cy="' + y + '" r="6"/>'
    + '<text x="' + (x + 9) + '" y="' + (y + 4) + '">' + esc(u.role) + '</text></g>';
}

export function shape(kind, points, cls, label, { xy }) {
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

export const STYLE = `<style>
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
