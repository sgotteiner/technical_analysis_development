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

// "peak is from support to resistance to support and valley is the opposite" (owner), and every
// box SHOWS WHAT IT WAS DRAWN FROM (owner, 2026-10-05: "when you show me your boxes i want to see
// what you did in them"): the extreme it hangs on, the two anchors that set its other side, a tick
// on the turning point itself, and its size - always, never suppressed for want of room.
// A TOUCH ZONE: where price worked a level - a stretch of bars, as tall as the band (owner,
// 2026-10-05, drawn: "boxes with touch zones. not touch dots like you do"). Inside it: the line it
// belongs to, and how far the candles actually reached past the band.
export function touchZone(z, { xOf, yOf }) {
  const x1 = xOf(z.from_time), x2 = xOf(z.to_time);
  const yTop = yOf(z.top), yBot = yOf(z.bottom), yLine = yOf(z.price);
  if (x1 === null || x2 === null || yTop === null || yBot === null) return '';
  const x = Math.min(x1, x2), w = Math.max(Math.abs(x2 - x1), 3), h = Math.max(yBot - yTop, 3);
  const parts = ['<rect x="' + x + '" y="' + yTop + '" width="' + w + '" height="' + h + '"/>'];
  if (yLine !== null) parts.push('<line class="g-extreme" x1="' + x + '" y1="' + yLine
    + '" x2="' + (x + w) + '" y2="' + yLine + '"/>');
  // how far the candles poked out of the band, which is why the box is not their full range
  for (const p of [z.reach_top, z.reach_bottom]) {
    const yR = yOf(p);
    if (yR !== null) parts.push('<line class="g-anchor" x1="' + (x + w / 2 - 4) + '" y1="' + yR
      + '" x2="' + (x + w / 2 + 4) + '" y2="' + yR + '"/>');
  }
  // short by default - a dozen full sentences at one price collide into noise, which is what made
  // the old swing-box labels unreadable. The whole sentence appears when one line is focused.
  const label = z.detail
    ? z.kind + ' · ' + z.bars + 'd · ' + z.touching_bars + ' bars on it · '
      + z.height_pct.toFixed(1) + '% band · from ' + z.came_from + ' to ' + z.left_to
    : z.kind + ' ' + z.bars + 'd';
  parts.push('<text x="' + (x + 3) + '" y="' + (yTop - 4) + '">' + esc(label) + '</text>');
  return '<g class="zone-box ' + esc(z.kind) + '">' + parts.join('') + '</g>';
}

export function swingBox(b, { xOf, yOf }) {
  const x1 = xOf(b.from_time), x2 = xOf(b.to_time);
  const yTop = yOf(b.top), yBot = yOf(b.bottom);
  if (x1 === null || x2 === null || yTop === null || yBot === null) return '';
  const flat = b.kind.startsWith('flat');
  const peak = b.kind.indexOf('peak') === 0 || b.kind === 'flat peaks';
  const cls = 'swing ' + (flat ? 'zone ' : '') + (peak ? 'peak' : 'valley') + (b.open ? ' open' : '');
  const x = Math.min(x1, x2), w = Math.abs(x2 - x1), h = Math.max(yBot - yTop, 1);
  const parts = ['<rect x="' + x + '" y="' + yTop + '" width="' + w + '" height="' + h + '"/>'];

  // the guideline the box hangs on: the peak's high / the valley's low, across the whole box
  const yEx = yOf(b.extreme);
  if (yEx !== null) parts.push('<line class="g-extreme" x1="' + x + '" y1="' + yEx
    + '" x2="' + (x + w) + '" y2="' + yEx + '"/>');
  // the anchors that set the other side: where the journey came from and where it went
  for (const [p, at] of [[b.from_price, b.from_time], [b.to_price, b.to_time]]) {
    const yA = yOf(p), xA = xOf(at);
    if (yA === null || xA === null) continue;
    parts.push('<line class="g-anchor" x1="' + (xA - 5) + '" y1="' + yA + '" x2="' + (xA + 5)
      + '" y2="' + yA + '"/>');
  }
  // a tick on each turning point the box is made of (one, or several for a flat zone)
  for (const t of (b.point_times || [b.at_time])) {
    const xP = xOf(t);
    if (xP !== null) parts.push('<line class="g-point" x1="' + xP + '" y1="' + yTop + '" x2="'
      + xP + '" y2="' + yBot + '"/>');
  }
  // the size, always: at the extreme edge so a peak's text and a valley's never land together
  const label = flat
    ? (b.points || []).length + ' ' + (peak ? 'peaks' : 'valleys') + ' within ' + b.spread_pct.toFixed(1) + '%'
    : (peak ? 'peak' : 'valley') + ' ' + b.size_pct.toFixed(0) + '% (up ' + b.up_pct.toFixed(0)
      + ' down ' + b.down_pct.toFixed(0) + ')';
  const xMid = xOf(b.at_time);
  parts.push('<text x="' + ((xMid === null ? x : xMid) + 3) + '" y="'
    + (peak ? yTop - 3 : yBot + 10) + '">' + esc(label) + '</text>');
  return '<g class="' + cls + '">' + parts.join('') + '</g>';
}

// the zigzag the trend is read from, to lay beside the one he draws
export function zigzagLine(points, { xOf, yOf }) {
  const pts = points.map(p => [xOf(p.time), yOf(p.price)]).filter(([x, y]) => x !== null && y !== null);
  return pts.length < 2 ? '' : '<g class="zz"><polyline points="' + pts.map(p => p.join(',')).join(' ') + '"/></g>';
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
  /* what the box was drawn FROM, inside it: the extreme it hangs on, the anchors that set its
     other side, and a tick on each turning point it holds */
  .swing .g-extreme { stroke-width: 1.5; stroke-dasharray: 4 3; }
  .swing.peak .g-extreme { stroke: rgba(8,153,129,0.95); }
  .swing.valley .g-extreme { stroke: rgba(242,54,69,0.95); }
  .swing .g-anchor { stroke: #787b86; stroke-width: 2; }
  .swing .g-point { stroke: rgba(120,123,134,0.5); stroke-width: 1; stroke-dasharray: 2 3; }
  /* a flat zone / range is several points at one height: drawn as the band, not as a journey */
  .swing.zone rect { stroke-width: 2; stroke-dasharray: 10 4; }
  .swing.zone.peak rect { stroke: rgba(8,153,129,0.9); fill: rgba(8,153,129,0.07); }
  .swing.zone.valley rect { stroke: rgba(242,54,69,0.9); fill: rgba(242,54,69,0.07); }
  .swing.zone text { fill: #d1d4dc; font-size: 11px; }
  /* a touch zone on a line: where price worked it. A break is the same shape, said differently. */
  .zone-box rect { stroke-width: 1.5; }
  .zone-box.touch rect { stroke: #29b6f6; fill: rgba(41,182,246,0.12); }
  .zone-box.break rect { stroke: #ffb74d; fill: rgba(255,183,77,0.10); stroke-dasharray: 6 3; }
  .zone-box .g-extreme { stroke: rgba(41,182,246,0.9); stroke-width: 1; }
  .zone-box .g-anchor { stroke: #787b86; stroke-width: 1.5; }
  .zone-box text { font-size: 10px; fill: #29b6f6; stroke-width: 2; }
  .zone-box.break text { fill: #ffb74d; }
  .zz polyline { stroke: #ff9800; stroke-width: 1.5; }
  .used circle { fill: none; stroke: #29b6f6; stroke-width: 2; }
  .used text { fill: #29b6f6; font-size: 11px; }
  text { fill: #e0e0e0; font: 11px 'Trebuchet MS', sans-serif; paint-order: stroke; stroke: #131722; stroke-width: 3; }
  .sel text { fill: #29b6f6; }
  .det line, .det rect { stroke: #b388ff; stroke-dasharray: 7 4; } .det rect { fill: rgba(179,136,255,0.08); }
  .det text { fill: #b388ff; }
</style>`;
