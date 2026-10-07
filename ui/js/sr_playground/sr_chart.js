// Chart: past / future candles around "now", and the algorithm's lines from a /api/view result.
const AHEAD = 30;
const LEVEL_WIDTH = [3, 2, 1];
const RANK_ALPHA = [1, 0.6, 0.42, 0.3];
const RGB = { support: '8,153,129', resistance: '242,54,69', single: '245,166,35' };

export function createSrChart(el) {
  const chart = LightweightCharts.createChart(el, {
    autoSize: true,
    layout: { background: { type: 'solid', color: '#131722' }, textColor: '#d1d4dc', fontSize: 11 },
    grid: { vertLines: { color: '#1f2430' }, horzLines: { color: '#1f2430' } },
    crosshair: { mode: LightweightCharts.CrosshairMode.Normal },
    rightPriceScale: { borderColor: '#2a2e39', mode: LightweightCharts.PriceScaleMode.Logarithmic },
    timeScale: { borderColor: '#2a2e39' },
  });
  const CANDLES = { upColor: '#089981', downColor: '#f23645', borderUpColor: '#089981',
    borderDownColor: '#f23645', wickUpColor: '#089981', wickDownColor: '#f23645' };
  const fade = 'rgba(120,123,134,0.35)';
  const FUTURE = { upColor: fade, downColor: fade, wickUpColor: fade, wickDownColor: fade };
  const HIDDEN = { upColor: 'rgba(0,0,0,0)', downColor: 'rgba(0,0,0,0)', borderUpColor: 'rgba(0,0,0,0)',
    borderDownColor: 'rgba(0,0,0,0)', wickUpColor: 'rgba(0,0,0,0)', wickDownColor: 'rgba(0,0,0,0)' };
  const past = chart.addCandlestickSeries({ ...CANDLES, priceLineVisible: false });
  const future = chart.addCandlestickSeries({ ...FUTURE, borderVisible: false, priceLineVisible: false,
    lastValueVisible: false });
  // the close-only line chart (owner, 2026-10-07: "id like to be able to see the close only graph
  // (line graph) like trading view allows it"). The candles stay as the anchor - transparent, not
  // removed - so the dots, his drawings and click-to-draw keep the same series and price scale.
  const closePast = chart.addLineSeries({ color: '#2962ff', lineWidth: 2, priceLineVisible: false,
    lastValueVisible: false, visible: false });
  const closeFuture = chart.addLineSeries({ color: fade, lineWidth: 2, priceLineVisible: false,
    lastValueVisible: false, visible: false });
  const closes = cs => cs.map(c => ({ time: c.time, value: c.close }));

  function makePool() {          // one pool per feature, so they never fight over the same series
    const series = [];
    let used = 0;
    return {
      start: () => { used = 0; },
      segment(points, color, width, style) {
        if (!series[used]) series[used] = chart.addLineSeries({ priceLineVisible: false, lastValueVisible: false,
          crosshairMarkerVisible: false, autoscaleInfoProvider: () => null });   // lines never squash the candles
        series[used].applyOptions({ color, lineWidth: width, lineStyle: style });
        series[used++].setData(points);
      },
      end: () => { for (let i = used; i < series.length; i++) series[i].setData([]); },
    };
  }
  const viewPool = makePool(), pointPool = makePool();
  const drawn = { markers: 0, pointLines: 0, viewLines: 0, closeLine: false };   // what is on the chart (for checks)
  let pool = viewPool;
  const segment = (points, color, width, style) => pool.segment(points, color, width, style);

  function drawLine(ln, candles, now, color, width, dashedOnly) {
    const at = x => ({ time: candles[x].time, value: Math.exp(ln.y1 + ln.slope * (x - ln.x1)) });
    const last = ln.last_touch, xEnd = Math.min(now + AHEAD, candles.length - 1);
    const Solid = LightweightCharts.LineStyle.Solid, Dashed = LightweightCharts.LineStyle.Dashed;
    if (last > ln.x1) segment([at(ln.x1), at(last)], color, width, dashedOnly ? LightweightCharts.LineStyle.Dotted : Solid);
    if (xEnd > last) segment([at(last), at(xEnd)], color, width, dashedOnly ? LightweightCharts.LineStyle.Dotted : Dashed);
  }

  function setNow(candles, now) {
    past.setData(candles.slice(0, now + 1));
    future.setData(candles.slice(now + 1));
    closePast.setData(closes(candles.slice(0, now + 1)));
    closeFuture.setData(closes(candles.slice(now + 1)));
  }

  function setCloseLine(on) {
    past.applyOptions(on ? HIDDEN : CANDLES);
    future.applyOptions(on ? HIDDEN : FUTURE);
    closePast.applyOptions({ visible: on });
    closeFuture.applyOptions({ visible: on });
    drawn.closeLine = on;
  }

  function drawView(view, candles, now) {
    pool = viewPool;
    pool.start();
    drawn.viewLines = Object.values(view ? view.levels : {})
      .reduce((n, lvl) => n + lvl.pipes.length * 2 + lvl.lines.length, 0);
    Object.values(view ? view.levels : {}).forEach((lvl, li) => {
      const width = LEVEL_WIDTH[Math.min(li, LEVEL_WIDTH.length - 1)];
      lvl.pipes.forEach((p, r) => {
        const a = RANK_ALPHA[Math.min(r, RANK_ALPHA.length - 1)];
        drawLine(p.support, candles, now, `rgba(${RGB.support},${a})`, width, false);
        drawLine(p.resistance, candles, now, `rgba(${RGB.resistance},${a})`, width, false);
      });
      lvl.lines.forEach((ln, r) => drawLine(ln, candles, now,
        `rgba(${RGB.single},${RANK_ALPHA[Math.min(r, RANK_ALPHA.length - 1)]})`, width, true));
    });
    pool.end();
  }

  // Lines through the swing points: solid where they were touched, dashed on to now + 30 days.
  function drawPointLines(groups, candles, now) {
    pool = pointPool;
    pool.start();
    groups.forEach(g => g.lines.forEach((ln, i) => {
      const at = x => ({ time: candles[x].time, value: Math.exp(ln.y1 + ln.slope * (x - ln.x1)) });
      const width = ln.far ? 1 : (i === 0 ? 2 : 1), xEnd = Math.min(now + AHEAD, candles.length - 1);
      // a trend further than the move can reach is drawn dotted: there, but not a line in play
      const S = LightweightCharts.LineStyle, solid = ln.far ? S.Dotted : S.Solid, after = ln.far ? S.Dotted : S.Dashed;
      if (ln.last > ln.first) segment([at(ln.first), at(ln.last)], g.color, width, solid);
      if (xEnd > ln.last) segment([at(ln.last), at(xEnd)], g.color, width, after);
    }));
    pool.end();
    drawn.pointLines = groups.reduce((n, g) => n + g.lines.length, 0);
  }

  function focus(candles, now) {
    const from = candles[Math.max(0, now - 240)].time, to = candles[Math.min(candles.length - 1, now + 45)].time;
    chart.timeScale().setVisibleRange({ from, to });
  }

  function setPointMarkers(groups) {
    const markers = groups.flatMap(g => g.points.map(p => ({
      time: p.time, position: p.kind === 'peak' ? 'aboveBar' : 'belowBar', color: g.color,
      shape: g.shape || 'circle', size: 0.6 })));
    past.setMarkers(markers.sort((a, b) => a.time - b.time));
    drawn.markers = markers.length;
  }

  return { chart, series: past, setNow, setCloseLine, drawView, focus, setPointMarkers, drawPointLines,
    drawn: () => ({ ...drawn }) };
}
