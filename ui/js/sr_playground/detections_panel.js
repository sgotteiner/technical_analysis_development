// The detector's setups over the whole history: step through them and judge each one on the chart.
export function renderDetections(root, episodes, current, { onPick, onClear }) {
  if (!episodes) { root.innerHTML = '<div class="hint">loading (first time ~7 s)…</div>'; return; }
  const i = current === null ? -1 : current;
  const ep = episodes[i];
  const pole = e => ((e.flag.pole_high / e.flag.pole_low - 1) * 100).toFixed(0);
  root.innerHTML = `<div class="row">
      <button data-d="-1">◄ prev</button><button data-d="1">next ►</button><button data-d="0">hide</button>
      <span class="hint">${i >= 0 ? `${i + 1} / ${episodes.length}` : `${episodes.length} found`}</span></div>
    ${ep ? `<div class="card det"><div class="t">${ep.first_date} → ${ep.last_date} (${ep.days} day${ep.days > 1 ? 's' : ''})</div>
      <div class="m">pole +${pole(ep)}% · flag high ${((Math.exp(ep.gap) - 1) * 100).toFixed(1)}% from the line</div>
      <div class="m">line: ${ep.touches} peaks within 1.5% · fell ${((1 - Math.exp(-ep.rejection)) * 100).toFixed(0)}% after its last peak</div>
      <div class="m">${ep.broken ? 'closed above the line' : 'still below the line'} on the last day</div></div>` : ''}
    <div class="list">${episodes.map((e, j) => `<div class="det-row${j === i ? ' sel' : ''}" data-j="${j}">${e.first_date} · ${e.days}d · pole +${pole(e)}%</div>`).join('')}</div>`;
  root.querySelectorAll('[data-d]').forEach(b => b.onclick = () => {
    const d = +b.dataset.d;
    if (d === 0) return onClear();
    onPick(Math.max(0, Math.min(episodes.length - 1, i < 0 ? (d > 0 ? 0 : episodes.length - 1) : i + d)));
  });
  root.querySelectorAll('[data-j]').forEach(r => r.onclick = () => onPick(+r.dataset.j));
}
