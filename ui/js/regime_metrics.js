// Regime viewer: per-period metric cards, comparison table and glossary.
// Metric values come from helpers/regime_metrics.py (period_metrics); definitions must match it.
const METRICS = [
  ['return', 'Return', 'spct', 'Close at the end ÷ close at the start − 1.'],
  ['days', 'Days', 'int', 'Calendar days from start to end.'],
  ['per_month', 'Per month', 'spct', 'Return compounded per 30 days: (1 + return)^(30 / days) − 1. Makes short and long periods comparable.'],
  ['efficiency', 'Efficiency', 'num2', 'Net log move ÷ sum of absolute daily log moves. 1 = straight line, 0 = went nowhere.'],
  ['r2', 'R²', 'num2', 'How well a straight line fits log price over time. 1 = perfectly steady trend.'],
  ['up_days', 'Up days', 'pct0', 'Share of days that closed higher than the day before.'],
  ['trend_noise', 'Trend/noise', 'num1', 'Mean daily log return ÷ its standard deviation × √365. Trend per unit of noise (Sharpe-like).'],
  ['volatility', 'Volatility', 'pct0', 'Standard deviation of daily log returns × √365 (annualised).'],
  ['atr_pct', 'Avg range', 'pct1', 'Average daily true range (incl. gaps) as % of the previous close.'],
  ['max_pullback', 'Max pullback', 'neg', 'Deepest drop from a running high inside the period.'],
  ['max_bounce', 'Max bounce', 'pos', 'Biggest rise from a running low inside the period.'],
  ['pullbacks_10', 'Pullbacks >10%', 'int', 'Separate drops of more than 10% from a high (a new high ends one).'],
  ['bounces_10', 'Bounces >10%', 'int', 'Separate rises of more than 10% from a low (a new low ends one).'],
  ['band', 'Band', 'x2', 'Highest close ÷ lowest close in the period. Flat ≤ 1.15, range 1.25–1.6.'],
  ['steps', 'Flat steps', 'int', 'Separate stretches of 21+ days whose closes stay within a 15% band. Stairs have 2 or more.'],
  ['touches', 'Range touches', 'int', 'Alternating visits to the top and bottom 20% of the close range (top, bottom, top, bottom = 4). A range has 4 or more.'],
  ['best_day', 'Best day', 'spct1', 'Largest single-day close-to-close gain.'],
  ['worst_day', 'Worst day', 'spct1', 'Largest single-day close-to-close loss.'],
];

function fmtMetric(v, kind) {
  const sign = x => (x > 0 ? '+' : '');
  const cls = x => (x > 0 ? 'pos' : x < 0 ? 'neg' : '');
  switch (kind) {
    case 'spct': return `<span class="${cls(v)}">${sign(v)}${(v * 100).toFixed(0)}%</span>`;
    case 'spct1': return `<span class="${cls(v)}">${sign(v)}${(v * 100).toFixed(1)}%</span>`;
    case 'pct0': return `${(v * 100).toFixed(0)}%`;
    case 'pct1': return `${(v * 100).toFixed(1)}%`;
    case 'neg': return `<span class="neg">−${(v * 100).toFixed(0)}%</span>`;
    case 'pos': return `<span class="pos">+${(v * 100).toFixed(0)}%</span>`;
    case 'num1': return v.toFixed(1);
    case 'num2': return v.toFixed(2);
    case 'x2': return v.toFixed(2) + '×';
    default: return String(v);
  }
}

function metricGrid(m) {
  return '<div class="grid">' + METRICS.map(([key, label, kind, def]) =>
    `<div><div class="k" title="${def}">${label}</div><div class="v">${fmtMetric(m[key], kind)}</div></div>`
  ).join('') + '</div>';
}

function renderDetail(p, colors) {
  const d = document.getElementById('detail');
  d.style.borderLeftColor = colors[p.regime];
  d.innerHTML = `<div class="name"><span class="tag" style="background:${colors[p.regime]}">${p.regime} · ${p.shape}</span>${p.name}</div>
    <div class="meta">${p.start} → ${p.end}</div>
    <div class="meta">$${p.start_close.toLocaleString()} → $${p.end_close.toLocaleString()} · saved lead-in: ${p.history}d</div>
    <div class="meta">Review: <b>${p.review}</b>${p.note ? ' — ' + p.note : ''}</div>
    ${metricGrid(p.m)}`;
}

function renderCompare(periods, colors, current) {
  const head = '<th>Period</th>' + METRICS.map(([, label, , def]) => `<th title="${def}">${label}</th>`).join('');
  const rows = periods.map((p, i) => `<tr class="${i === current ? 'cur' : ''}"><td><span class="tag" style="background:${colors[p.regime]}">${p.regime} · ${p.shape}</span>${p.name}</td>`
    + METRICS.map(([key, , kind]) => `<td>${fmtMetric(p.m[key], kind)}</td>`).join('') + '</tr>').join('');
  document.getElementById('cmp').innerHTML = `<table><thead><tr>${head}</tr></thead><tbody>${rows}</tbody></table>`;
}

function renderGlossary() {
  document.getElementById('gloss').innerHTML = '<b>Metric definitions</b>' +
    METRICS.map(([, label, , def]) => `<dt>${label}</dt><dd>${def}</dd>`).join('');
}
