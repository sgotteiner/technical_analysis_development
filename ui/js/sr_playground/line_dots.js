// A dot at the end of each drawn line instead of text on the chart, and a gold STAR on the line where a
// breakout, retest or fakeout happened at it during the move running now (business_logic_services/
// line_events.py). Clicking either opens the chart card (owner, 2026-10-08: "the lines dont write text
// show a dot at the end of the line" ... "events related to the lines mark in gold ... a star shape").
import { meaning, sketch } from './event_sketches.js';

const NEAR_PX = 10;
const AHEAD = 30;            // the lines run on 30 days past "now" (sr_chart.js): the dot sits at that end

export function createLineDots({ card, chart, series, drawings, onFocus = () => {} }) {
  let dots = [], stars = [];
  const source = {
    hit(p) {
      const near = d => {
        const x = chart.timeScale().timeToCoordinate(d.time), y = series.priceToCoordinate(d.price);
        return x !== null && y !== null && Math.hypot(p.point.x - x, p.point.y - y) <= NEAR_PX;
      };
      const st = stars.filter(near);
      if (st.length) return { head: `${st[0].date} · ${st[0].role}`, items: st.map(e => ({
        title: `${e.type} ${e.direction}`, text: e.why, pic: sketch(e.type, e.direction), meaning: meaning(e.type),
        color: e.direction === 'up' ? '#26a69a' : '#ef5350' })) };
      const d = dots.find(near);
      return d ? { head: d.title, role: d.line.role, items: [{ title: `${Math.round(d.line.price).toLocaleString()} now`,
        text: d.line.how || '', color: d.color }] } : null;
    },
    // a clicked line shows alone, with the zigzag dots it is made of (owner, 2026-10-09: "when i click
    // a line i want to see the zigzag dots it used")
    onOpen: hit => { if (hit.role) onFocus(hit.role); }, onClose: () => onFocus(null),
  };
  card.register(source);

  // groups: the points answer per size (with .story.lines and .color); `shown`: the lines on screen
  function show(groups, candles, now, visible, starsOn = true) {
    const end = Math.min(now + AHEAD, candles.length - 1);
    dots = !visible ? [] : groups.flatMap(g => ((g.story || {}).lines || []).map(l => ({
      line: l, title: l.role, color: g.color, time: candles[end].time,
      // a trend line keeps its slope to the end; a level is flat
      price: l.slope_pct_day == null ? l.price : l.price * Math.pow(1 + l.slope_pct_day / 100, end - now) })));
    const roles = new Set(groups.flatMap(g => ((g.story || {}).lines || []).map(l => l.role)));
    stars = !visible || !starsOn ? [] : groups.flatMap(g => (g.line_events || []).filter(e => roles.has(e.role)));
    drawings.setLineDots(dots.concat(stars.map(e => ({ ...e, star: true }))));
  }

  return { show };
}
