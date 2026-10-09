// Rule "concepts": the line concepts, each switched on or off (owner, 2026-10-08: "implementing
// these concepts with flags will help in testing it"). What each one is: docs/GEOMETRY_DEFINITIONS.md,
// "Ideas from other sources"; the code: business_logic_services/line_concepts.py.

export const CONCEPT_DEFAULTS = { cSwings: 'zigzag', cGroup: 'channels', cBand: 'move',
  cParts: ['pivots', 'bars', 'sweeps'], cTrend: 'protected1', cPick: 'roster', cPerSide: 1 };

const CHOICES = [
  ['cSwings', 'swing points', [['zigzag', 'our zigzag'], ['pivots', 'pivots (10 bars each side)'], ['atr', 'ATR zigzag (2.5 ATR)']]],
  ['cGroup', 'grouping', [['channels', 'channels: points in a band are one level'], ['off', 'off: every point a level']]],
  ['cBand', 'band', [['move', 'a share of the move (ours)'], ['range', '5% of the 300-bar range (TradingView)']]],
  ['cTrend', 'trend', [['protected1', 'protected low, 1 break'], ['protected2', 'protected low, 2 breaks'],
                       ['window', 'last peaks and valleys (before)'], ['off', 'off']]],
  ['cPick', 'which lines', [['roster', 'his roster'], ['nearest', 'nearest each side'], ['strongest', 'strongest each side']]],
];
const PARTS = [['pivots', 'pivots ×20'], ['bars', 'bars touching'], ['sweeps', 'wick sweeps ×20'],
               ['round', 'round number +20'], ['measured', 'measured %']];

export function conceptSettings(state) {
  const select = ([key, label, options]) => `<label>${label} <select data-ck="${key}">`
    + options.map(([v, t]) => `<option value="${v}"${state[key] === v ? ' selected' : ''}>${t}</option>`).join('')
    + '</select></label>';
  const parts = PARTS.map(([v, t]) => `<label><input type="checkbox" data-cp="${v}"`
    + `${state.cParts.includes(v) ? ' checked' : ''}> ${t}</label>`).join('');
  return CHOICES.map(select).join('')
    + `<label>per side <input data-ck="cPerSide" type="number" min="1" max="5" value="${state.cPerSide}"></label>`
    + `<div class="row">strength: ${parts}</div>`;
}

export function bindConcepts(root, state, onChange) {
  root.querySelectorAll('[data-ck]').forEach(el => el.onchange = e =>
    onChange(el.dataset.ck, el.type === 'number' ? +e.target.value : e.target.value));
  root.querySelectorAll('[data-cp]').forEach(el => el.onchange = e => onChange('cParts',
    e.target.checked ? [...state.cParts, el.dataset.cp] : state.cParts.filter(p => p !== el.dataset.cp)));
}

export const conceptFlags = state => ({ swings: state.cSwings, group: state.cGroup, band: state.cBand,
  parts: state.cParts, trend: state.cTrend, pick: state.cPick, per_side: +state.cPerSide });
