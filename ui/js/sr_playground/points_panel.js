// The swing-points panel: sizes, the line rule and its settings, and what was found.
const day = (candles, bar) => new Date(candles[bar].time * 1000).toISOString().slice(0, 10);
const num = v => Math.round(v).toLocaleString();

function foundRows(state, info, colors, candles) {
  if (!info || !state.drawLines) return '';
  return info.sizes.map((g, i) => {
    const color = colors[i % colors.length];
    const row = text => `<div class="m" style="color:${color}">${text}</div>`;
    if (state.mode === 'owner') {
      return (g.levels || []).map(lv => row(`level ${num(lv.price)} · touched ${lv.touches}× (${lv.history} before) · ${day(candles, lv.first)} → ${day(candles, lv.last)}`)).join('')
        + (g.trends || []).map(t => row(`${t.role} trend ${(Math.expm1(t.slope) * 100).toFixed(2)}%/day · ${t.touches} touches · ${day(candles, t.first)} → ${day(candles, t.last)}`)).join('');
    }
    return (g.lines || []).map((l, j) => row(`line ${j + 1}: ${l.touches} touches · ${(Math.expm1(l.slope) * 100).toFixed(2)}%/day · ${day(candles, l.first)} → ${day(candles, l.last)}`)).join('');
  }).join('');
}

function lineSettings(state) {
  if (!state.drawLines) return '';
  const touchesRule = state.mode === 'touches';
  return `<div class="row">
      <label>rule <select id="pt-mode">
        <option value="owner"${state.mode === 'owner' ? ' selected' : ''}>recent levels + their history</option>
        <option value="touches"${touchesRule ? ' selected' : ''}>any line, by touch count</option>
      </select></label>
      <label>max distance <input id="pt-tol" type="number" step="0.1" min="0.1" value="${state.tolPct}">%</label>
      <label>recent = last <input id="pt-anchor" type="number" min="1" value="${state.anchorDays}"> days</label>
      <label>show <input id="pt-top" type="number" min="1" max="50" value="${state.top}"></label>
      <label>min touches <input id="pt-touch" type="number" min="2" max="20" value="${state.minTouches}"></label>
      <label>history <input id="pt-hist" type="number" min="0" max="50" value="${state.maxHistory}" placeholder="all"> visits</label>
      ${touchesRule ? `<label>max slope <input id="pt-slope" type="number" step="0.05" min="0" value="${state.maxSlope}" placeholder="any">%/day</label>` : ''}
    </div>`;
}

function presetRow(presets, state) {
  const current = presets.find(p => p.name === state.presetName);
  return `<div class="row">
      <label>preset <select id="pt-preset"><option value="">(not saved)</option>
        ${presets.map(p => `<option value="${p.name}"${p.name === state.presetName ? ' selected' : ''}>${p.name}</option>`).join('')}
      </select></label>
      <button id="pt-save-preset" title="Save these settings with the current commit">save current…</button>
      ${current ? `<span class="hint">commit ${current.commit || '?'}${current.tag ? ' · tag ' + current.tag : ''}</span>` : ''}
    </div>`;
}

export function renderPointsPanel({ root, state, info, colors, candles, answered, presets = [], onChange, onLoadPreset, onSavePreset }) {
  const c = info && info.calibrated, groups = info ? info.sizes : [];
  if (answered) root.dataset.rev = String(answered);        // "this is the answer to request N"
  root.innerHTML = presetRow(presets, state) + `<div class="row">
      <label><input type="checkbox" id="pt-show" ${state.show ? 'checked' : ''}> show points</label>
      <label>trade length <input id="pt-days" type="number" min="1" max="365" value="${state.targetDays}"> days</label>
      <label>or sizes % <input id="pt-sizes" value="${state.sizesText}" placeholder="6, 12"></label>
      <label>lookback <input id="pt-look" type="number" min="30" value="${state.lookback}" placeholder="all"> d</label>
      <label><input type="checkbox" id="pt-lines" ${state.drawLines ? 'checked' : ''}> lines</label>
    </div>
    ${c && c.size ? `<div class="m"><b>${(c.size * 100).toFixed(1)}%</b> · median leg ${c.median_days.toFixed(0)} days · ${c.legs} legs in the last 2 years</div>`
      : c ? '<div class="m warn">not enough history to calibrate a size</div>' : ''}
    ${groups.map((g, i) => `<div class="m" style="color:${colors[i % colors.length]}">${(g.size * 100).toFixed(1)}%: ${g.points.length} points up to now</div>`).join('')}
    ${lineSettings(state)}
    ${foundRows(state, info, colors, candles)}`;

  const bind = (id, key, kind) => {
    const el = root.querySelector(id);
    if (el) el.onchange = e => onChange(key, kind === 'check' ? e.target.checked : e.target.value);
  };
  bind('#pt-show', 'show', 'check');
  bind('#pt-lines', 'drawLines', 'check');
  root.querySelector('#pt-preset').onchange = e => onLoadPreset(e.target.value);
  root.querySelector('#pt-save-preset').onclick = () => {
    const name = prompt('Save these settings as:', state.presetName || '');
    if (name && name.trim()) onSavePreset(name.trim(), prompt('A note (optional):', '') || '');
  };
  [['#pt-days', 'targetDays'], ['#pt-sizes', 'sizesText'], ['#pt-look', 'lookback'], ['#pt-mode', 'mode'],
   ['#pt-tol', 'tolPct'], ['#pt-anchor', 'anchorDays'], ['#pt-top', 'top'], ['#pt-touch', 'minTouches'],
   ['#pt-hist', 'maxHistory'],
   ['#pt-slope', 'maxSlope']].forEach(([id, key]) => bind(id, key));
}
