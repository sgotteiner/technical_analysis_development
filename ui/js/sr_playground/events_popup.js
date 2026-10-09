// The events' dots as a source for the chart card (chart_card.js): a day with events is one dot under
// or over its candle, and a click near it opens the card with each event of that day and its why.
import { meaning, sketch } from './event_sketches.js';

const NEAR_PX = 40;           // how close to the dot a click must land (the dot sits under / over its candle)

export function createEventsPopup({ card, series, getCandles, onOpen }) {
  let byTime = new Map();
  const source = {
    hit(p) {
      const events = p.time === undefined ? null : byTime.get(p.time);
      if (!events) return null;
      const c = getCandles().find(k => k.time === p.time);
      const y = series.priceToCoordinate(events[0].direction === 'up' ? c.low : c.high);
      if (y === null || Math.abs(p.point.y - y) > NEAR_PX) return null;
      return { head: events[0].date, events, items: events.map(e => ({
        title: `${e.type.replace(/_/g, ' ')} ${e.direction}`, text: e.why,
        pic: sketch(e.type, e.direction), meaning: meaning(e.type),
        color: e.direction === 'up' ? '#26a69a' : '#ef5350' })) };
    },
    onOpen: hit => onOpen(hit.events),
    onClose: () => onOpen(null),
  };
  card.register(source);

  return {
    setEvents(list) {               // the events known at "now": one dot per day
      byTime = new Map();
      list.forEach(e => byTime.set(e.time, [...(byTime.get(e.time) || []), e]));
      return [...byTime.values()];
    },
    close: () => { if (card.isOpen(source)) card.close(); },
  };
}
