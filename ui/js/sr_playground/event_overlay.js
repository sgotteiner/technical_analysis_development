// Events on the chart (events_controller.js): drawn on the same SVG overlay as everything else.

// an EVENT: the candles of the move that decided it, as a box over the line's zone, the line it
// happened at, and - for a pattern - its points joined. Drawn only for the day he opened.
export function eventMark(e, { xOf, yOf }) {
  const cls = 'ev ' + (e.direction === 'up' ? 'up' : 'down') + (e.detail ? ' focus' : '');
  const parts = [];
  const seg = pts => pts.map(p => [xOf(p.time), yOf(p.price)]).filter(([x, y]) => x !== null && y !== null);
  const line = seg(e.line_points || []);
  if (line.length === 2) parts.push('<line class="ev-line" x1="' + line[0][0] + '" y1="' + line[0][1]
    + '" x2="' + line[1][0] + '" y2="' + line[1][1] + '"/>');
  const shape = seg(e.shape || []);
  if (shape.length > 1) parts.push('<polyline class="ev-shape" points="' + shape.map(p => p.join(',')).join(' ') + '"/>');
  const zone = e.line && e.line.zone;
  const x1 = xOf(e.from_time), x2 = xOf(e.time);
  if (zone && x1 !== null && x2 !== null) {
    const yT = yOf(zone[1]), yB = yOf(zone[0]);
    if (yT !== null && yB !== null) parts.push('<rect x="' + Math.min(x1, x2) + '" y="' + yT + '" width="'
      + Math.max(Math.abs(x2 - x1), 4) + '" height="' + Math.max(yB - yT, 3) + '"/>');
  }
  // no words: the dot's card says it
  return '<g class="' + cls + '">' + parts.join('') + '</g>';
}

// a TRADE: a green triangle at the buy, a mark at the sale in the colour of how it ended, the path
// between them dashed, and the stop and target as short lines over the trade's life
export function tradeMark(t, { xOf, yOf }) {
  const x1 = xOf(t.entry_time), y1 = yOf(t.entry);
  if (x1 === null || y1 === null) return '';
  const parts = ['<polygon points="' + x1 + ',' + (y1 - 7) + ' ' + (x1 - 6) + ',' + (y1 + 5) + ' ' + (x1 + 6) + ',' + (y1 + 5)
    + '" fill="#26a69a" stroke="#131722" stroke-width="1.5"/>'];
  const x2 = t.exit_time ? xOf(t.exit_time) : null, y2 = t.exit ? yOf(t.exit) : null;
  const end = x2 !== null ? x2 : x1 + 40;
  for (const [p, c] of [[t.stop, '#ef5350'], [t.target, '#29b6f6']]) {
    const y = p ? yOf(p) : null;
    if (y !== null) parts.push('<line x1="' + x1 + '" y1="' + y + '" x2="' + end + '" y2="' + y
      + '" stroke="' + c + '" stroke-width="1" stroke-dasharray="3 3"/>');
  }
  if (x2 !== null && y2 !== null) {
    parts.push('<line x1="' + x1 + '" y1="' + y1 + '" x2="' + x2 + '" y2="' + y2 + '" stroke="' + t.color + '" stroke-width="1.5" stroke-dasharray="5 3"/>');
    parts.push('<rect x="' + (x2 - 5) + '" y="' + (y2 - 5) + '" width="10" height="10" fill="' + t.color + '" stroke="#131722" stroke-width="1.5"/>');
  }
  return '<g class="trade">' + parts.join('') + '</g>';
}

export const EVENT_STYLE = `<style>
  .ev rect { stroke-width: 1; } .ev.up rect { stroke: #26a69a; fill: rgba(38,166,154,0.10); }
  .ev.down rect { stroke: #ef5350; fill: rgba(239,83,80,0.10); }
  .ev .ev-line { stroke: #ffca28; stroke-width: 1.5; stroke-dasharray: 6 3; }
  .ev .ev-shape { stroke: #e040fb; stroke-width: 2; }
  .ev text { font-size: 10px; } .ev.up text { fill: #26a69a; } .ev.down text { fill: #ef5350; }
  .ev.focus .ev-line { stroke-width: 2.5; } .ev.focus text { font-size: 12px; }
</style>`;
