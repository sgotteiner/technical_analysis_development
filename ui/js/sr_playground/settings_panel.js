// Settings panel: levels (any number), how many pipes / single lines to show, and every rule.
// Emits onChange(state) on each edit; toRequest(state) builds the /api/view body.
const RULES = [   // key, label, whose rule, input kind, from-server / to-server conversion
  ['touch_pct', 'Touch = within %', 'Claude', 'num'],
  ['candidate_ratio', 'Candidate zigzag × magnitude', 'Claude', 'num'],
  ['both_sides', 'Significant on BOTH sides', 'Claude', 'bool'],
  ['min_touches', 'Min touches per line', 'open q.', 'num'],
  ['max_divergence', 'Max widening %/day (0 = never)', 'owner', 'num',
    v => +(Math.expm1(v) * 100).toFixed(4), v => Math.log1p(v / 100)],
  ['min_width_q', 'Min width = swing quantile (0 = off)', 'Claude', 'num'],
  ['max_width_mult', 'Max width × largest swing', 'owner', 'num'],
  ['act_together', 'Both lines act together', 'Claude', 'bool'],
  ['check_now', 'Width rules also at "now"', 'Claude', 'bool'],
];
const KEY = 'sr_playground_settings_v1';

export function initialState(defaults) {
  const fresh = fromDefaults(defaults);
  try { const saved = JSON.parse(localStorage.getItem(KEY)); if (saved && saved.levels) return saved; } catch (e) {}
  return fresh;
}

export function fromDefaults(d) {
  return { levels: Object.entries(d.levels).map(([name, c]) => ({ name, period: c.period,
             magnitudePct: +(c.magnitude * 100).toFixed(3), show: true })),
           pairs: 1, singles: 0, rules: { ...d.rules } };
}

export function toRequest(state, end) {
  const levels = {};
  state.levels.filter(l => l.show).forEach(l => { levels[l.name] = { period: +l.period, magnitude: l.magnitudePct / 100 }; });
  return { end, levels, rules: state.rules, pairs: +state.pairs, singles: +state.singles };
}

export function renderSettings(root, state, defaults, onChange) {
  const emit = () => { try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (e) {} onChange(state); };
  const redraw = () => { renderSettings(root, state, defaults, onChange); emit(); };
  root.innerHTML = '';
  const lv = document.createElement('table');
  lv.innerHTML = '<tr><td class="k">Level</td><td class="k">Window d</td><td class="k">Magnitude %</td><td class="k">Show</td><td></td></tr>';
  state.levels.forEach((l, i) => {
    const tr = document.createElement('tr');
    tr.innerHTML = `<td class="name"><input></td><td><input type="number" min="10" step="10" value="${l.period}"></td>
      <td><input type="number" min="0.5" step="0.5" value="${l.magnitudePct}"></td><td><input type="checkbox" ${l.show ? 'checked' : ''}></td>
      <td><button title="Remove level">×</button></td>`;
    const [name, period, mag, show] = tr.querySelectorAll('input');
    name.value = l.name;
    name.onchange = () => {
      const v = name.value.trim();
      if (!v || state.levels.some((o, j) => j !== i && o.name === v)) { name.value = l.name; return; }
      l.name = v; emit();
    };
    period.onchange = () => { l.period = +period.value; emit(); };
    mag.onchange = () => { l.magnitudePct = +mag.value; emit(); };
    show.onchange = () => { l.show = show.checked; emit(); };
    tr.querySelector('button').onclick = () => { if (state.levels.length > 1) { state.levels.splice(i, 1); redraw(); } };
    lv.appendChild(tr);
  });
  root.appendChild(lv);

  const row = document.createElement('div');
  row.className = 'row';
  row.innerHTML = `<button id="add-level">+ level</button>
    <label>Pipes/level <input id="pairs" type="number" min="0" max="10" value="${state.pairs}"></label>
    <label>Lines/level <input id="singles" type="number" min="0" max="30" value="${state.singles}"></label>`;
  root.appendChild(row);
  row.querySelector('#add-level').onclick = () => {
    const last = state.levels[state.levels.length - 1];
    state.levels.push({ name: `level${state.levels.length + 1}`, period: last.period, magnitudePct: last.magnitudePct, show: true });
    redraw();
  };
  row.querySelector('#pairs').onchange = e => { state.pairs = +e.target.value; emit(); };
  row.querySelector('#singles').onchange = e => { state.singles = +e.target.value; emit(); };

  const rt = document.createElement('table');
  RULES.forEach(([key, label, who, kind, show = v => v, back = v => v]) => {
    const tr = document.createElement('tr');
    const v = state.rules[key];
    tr.innerHTML = `<td class="k">${label} <span class="who">${who}</span></td><td>${kind === 'bool'
      ? `<input type="checkbox" ${v ? 'checked' : ''}>` : `<input type="number" step="any" value="${show(v)}">`}</td>`;
    const inp = tr.querySelector('input');
    inp.onchange = () => { state.rules[key] = kind === 'bool' ? inp.checked : back(+inp.value); emit(); };
    rt.appendChild(tr);
  });
  root.appendChild(rt);

  const reset = document.createElement('button');
  reset.textContent = 'Reset to the built rules';
  reset.onclick = () => { Object.assign(state, fromDefaults(defaults)); redraw(); };
  root.appendChild(reset);
}
