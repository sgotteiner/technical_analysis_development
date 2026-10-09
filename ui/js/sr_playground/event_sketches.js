// A small picture for each event and pattern name (owner, 2026-10-08: "i dont know the names can you
// have an image that describes the pattern?"). The gold dashed line is the line it happens at; the
// white path is price. Each is drawn one way and mirrored for the other direction.

// [the direction it is drawn for, price path (x,y in a 120x60 box), y of the line, one line of meaning]
const BASE = {
  breakout: ['up', '5,52 25,44 45,36 58,34 66,38 78,22 95,14 115,6', 30,
    'price closes through the line and keeps going'],
  retest: ['up', '5,52 30,40 45,22 58,12 72,26 80,30 90,18 115,4', 30,
    'after a breakout, price comes back to the line and holds on the new side'],
  fakeout: ['up', '5,10 30,20 45,26 58,42 66,46 76,24 92,14 115,6', 30,
    'price closes through the line, then quickly closes back - the breakout failed'],
  sweep: ['up', '5,8 30,16 50,24 70,22 95,12 115,6', 30,
    'one candle\'s wick pokes through the line and the candle closes back'],
  bounce: ['up', '5,6 25,14 42,24 55,33 62,33 72,24 90,12 115,4', 30,
    'price comes into the line and turns back the way it came'],
  trend_change: ['up', '5,6 15,26 25,16 35,38 45,28 57,52 70,34 80,44 93,22 103,32 115,8', null,
    'lower highs and lows turn into higher ones (or the reverse)'],
  double_top: ['down', '5,56 30,12 52,34 74,12 96,46 115,56', 34,
    'two peaks at one level, then a close under the valley between them'],
  head_shoulders: ['down', '5,56 22,24 34,40 52,6 70,40 82,24 100,46 115,56', 40,
    'three peaks, the middle one highest, then a close under the line through the two valleys'],
  cup_handle: ['up', '5,12 15,26 28,40 45,46 62,46 78,38 90,22 95,12 101,20 107,18 115,4', 13,
    'a rounded dip between two equal highs, a small pullback, then a close over the rim'],
  bull_flag: ['up', '5,56 14,40 24,22 32,10 42,18 50,14 60,24 68,20 78,26 92,10 115,2', null,
    'a steep run (the pole), a short drift against it (the flag), then a break out the run\'s way'],
};
const SAME_AS = { double_bottom: 'double_top', inverse_head_shoulders: 'head_shoulders', bear_flag: 'bull_flag' };
const NATURAL = { double_bottom: 'up', inverse_head_shoulders: 'up', bear_flag: 'down' };

const flip = pts => pts.split(' ').map(p => { const [x, y] = p.split(','); return `${x},${60 - y}`; }).join(' ');

export function sketch(type, direction) {
  const base = BASE[SAME_AS[type] || type];
  if (!base) return '';
  const [drawnFor, path, lineY] = base;
  const want = direction || NATURAL[type] || drawnFor;
  const mirror = want !== drawnFor;
  const pts = mirror ? flip(path) : path;
  const y = lineY === null ? null : mirror ? 60 - lineY : lineY;
  // the sweep's one candle: its wick through the line, its body closed back on the side price came from
  const candle = type !== 'sweep' ? '' : mirror
    ? '<line x1="60" y1="16" x2="60" y2="40" stroke="#d1d4dc"/><rect x="57" y="32" width="6" height="8" fill="#d1d4dc"/>'
    : '<line x1="60" y1="20" x2="60" y2="44" stroke="#d1d4dc"/><rect x="57" y="20" width="6" height="8" fill="#d1d4dc"/>';
  return `<svg width="120" height="60" viewBox="0 0 120 60" style="background:#131722;border-radius:4px">`
    + (y === null ? '' : `<line x1="0" y1="${y}" x2="120" y2="${y}" stroke="#ffca28" stroke-dasharray="5 3"/>`)
    + `<polyline points="${pts}" fill="none" stroke="#d1d4dc" stroke-width="1.8"/>${candle}</svg>`;
}

export const meaning = type => (BASE[SAME_AS[type] || type] || [])[3] || '';

export const NAMES = ['breakout', 'retest', 'fakeout', 'sweep', 'bounce', 'trend_change', 'double_top',
  'double_bottom', 'head_shoulders', 'inverse_head_shoulders', 'cup_handle', 'bull_flag', 'bear_flag'];
