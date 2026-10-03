// Chart <-> pixels, in one place: the only thing the input half and the drawing half share.
// Every one of these returns null when the point is off the chart (past the last candle, over an
// axis) - callers must check, because a half-resolved point used to send the drag to the chart,
// which pans, so drawing "moved the screen instead".
export function createCoords({ chart, series, container }) {
  const xOf = time => chart.timeScale().timeToCoordinate(time);
  const yOf = price => series.priceToCoordinate(price);
  const xy = pt => {
    const x = xOf(pt.time), y = yOf(pt.price);
    return x === null || y === null ? null : [x, y];
  };
  const at = e => {               // where an event is, in chart terms
    const r = container.getBoundingClientRect(), x = e.clientX - r.left, y = e.clientY - r.top;
    const time = chart.timeScale().coordinateToTime(x);
    return time === null ? null : { time, price: series.coordinateToPrice(y), x, y };
  };
  return { xOf, yOf, xy, at };
}
