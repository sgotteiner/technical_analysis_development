// The swing-points panel: sizes, the line rule and its settings, and what was found.
// The found lines and the owner's verdict on each live in ./found_lines.js.
import { foundRows, bindFound, theStory } from './found_lines.js';
import { conceptSettings, bindConcepts } from './concepts_panel.js';

function lineSettings(state) {
  if (!state.drawLines) return '';
  const touchesRule = state.mode === 'touches';
  return `<div class="row">
      <label>rule <select id="pt-mode">
        <option value="moves"${state.mode === 'moves' ? ' selected' : ''}>by the move that ran into it</option>
        <option value="touches"${touchesRule ? ' selected' : ''}>any line, by touch count</option>
        <option value="channels"${state.mode === 'channels' ? ' selected' : ''}>TradingView S/R Channels (47.5K uses)</option>
        <option value="zigzag"${state.mode === 'zigzag' ? ' selected' : ''}>from the zigzag (kept lines)</option>
        <option value="concepts"${state.mode === 'concepts' ? ' selected' : ''}>concepts (choose below)</option>
      </select></label>
      ${state.mode === 'concepts' ? conceptSettings(state) + '</div>' : ''}
      ${['concepts', 'zigzag'].includes(state.mode) ? '' : `<label>max distance <input id="pt-tol" type="number" step="0.1" min="0.1" value="${state.tolPct}">%</label>
      <label>recent = last <input id="pt-anchor" type="number" min="1" value="${state.anchorDays}"> days</label>
      <label>show <input id="pt-top" type="number" min="1" max="50" value="${state.top}"></label>
      <label>min touches <input id="pt-touch" type="number" min="2" max="20" value="${state.minTouches}"></label>
      <label>history <input id="pt-hist" type="number" min="0" max="50" value="${state.maxHistory}" placeholder="all"> visits</label>
      <label>merge within <input id="pt-merge" type="number" min="0" step="0.5" value="${state.mergePct}">%</label>
      <label>targets <input id="pt-targets" type="number" min="0" max="5" value="${state.targets}"> each way</label>
      <label>min visits <input id="pt-visits" type="number" min="1" max="10" value="${state.minVisits}"></label>
      <label>crowded area <select id="pt-prefer">
        <option value="recent"${state.prefer === 'recent' ? ' selected' : ''}>most recent wins</option>
        <option value="visits"${state.prefer === 'visits' ? ' selected' : ''}>most visits wins</option>
      </select></label>
      ${touchesRule ? `<label>max slope <input id="pt-slope" type="number" step="0.05" min="0" value="${state.maxSlope}" placeholder="any">%/day</label>` : ''}
    </div>`}`;
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

export function renderPointsPanel({ root, state, info, colors, candles, answered, presets = [], busy = false,
                                    secs = null, judgements = [], drawings = [], verdictError = null,
                                    focus = null, onFocus = () => {},
                                    onChange, onLoadPreset, onSavePreset, ...verdict }) {
  const c = info && info.calibrated, groups = info ? info.sizes : [];
  if (answered) root.dataset.rev = String(answered);        // "this is the answer to request N"
  // while it is working, the lines below belong to the PREVIOUS "now": say so here, not only in
  // the top bar (owner, 2026-09-24: "no sign it is busy")
  root.dataset.busy = busy ? '1' : '';
  root.innerHTML = presetRow(presets, state)
    + (verdictError ? `<div class="row err" id="pt-jerr">${verdictError}</div>` : '')
    + (busy ? '<div class="row warn" id="pt-busy">computing… (the lines below are the previous answer)</div>'
       : secs === null ? '' : `<div class="row hint" id="pt-took">${secs.toFixed(2)} s</div>`)
    + `<div class="row">
      <label><input type="checkbox" id="pt-show" ${state.show ? 'checked' : ''}> show points</label>
      <label class="${state.sizesText ? 'hint' : ''}">trade length <input id="pt-days" type="number" min="1" max="365" value="${state.targetDays}"> days${state.sizesText ? ' (unused)' : ''}</label>
      <label>or sizes % <input id="pt-sizes" value="${state.sizesText}" placeholder="6, 12"></label>
      <label>lookback <input id="pt-look" type="number" min="30" value="${state.lookback}" placeholder="all"> d</label>
      <label><input type="checkbox" id="pt-lines" ${state.drawLines ? 'checked' : ''}> lines</label>
    </div>
    ${c && c.size ? `<div class="m"><b>${(c.size * 100).toFixed(1)}%</b> · median leg ${c.median_days.toFixed(0)} days · ${c.legs} legs in the last 2 years</div>`
      : c ? '<div class="m warn">not enough history to calibrate a size</div>' : ''}
    ${groups.map((g, i) => `<div class="m" style="color:${colors[i % colors.length]}">${(g.size * 100).toFixed(1)}%: ${g.points.length} points up to now</div>`).join('')}
    ${lineSettings(state)}
    ${foundRows({ state, info, colors, candles, judgements, drawings })}`;
  bindFound(root, { candles, info, judgements, ...verdict });   // onJudge / onUnjudge / onNote / …
  // the explanation has its own card, and a line in it can be clicked to see only that line
  const story = document.getElementById('story');
  if (story) {
    story.innerHTML = ((info && info.sizes) || [])
      .map(g => theStory(g, focus, { candles, info, judgements, drawings })).join('');
    bindFound(story, { candles, info, judgements, ...verdict });   // the same verdicts, in this card
    story.querySelectorAll('.line[data-role]').forEach(row => {
      // the marks and the note box live inside the row: clicking them must not also focus the line
      row.onclick = e => {
        if (e.target.closest('.judge, .why')) return;
        onFocus(row.dataset.role === focus ? null : row.dataset.role);
      };
    });
    const all = story.querySelector('#st-all');
    if (all) all.onclick = e => { e.preventDefault(); onFocus(null); };
  }

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
   ['#pt-hist', 'maxHistory'], ['#pt-merge', 'mergePct'], ['#pt-targets', 'targets'], ['#pt-visits', 'minVisits'], ['#pt-prefer', 'prefer'],
   ['#pt-slope', 'maxSlope']].forEach(([id, key]) => bind(id, key));
  bindConcepts(root, state, onChange);
}
