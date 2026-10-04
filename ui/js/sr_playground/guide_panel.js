// What every card and tool on this page is for (owner, 2026-10-03: "i have many utils and cards in
// the sidebar but forgot what all of them do and how to use them and even if all are still
// relevant"). The first card, so the page explains itself before it shows anything.
//
// `state` is Claude's read of whether a card still earns its place, NOT a decision: "use" = this is
// how the lines you approved are made, "old" = an earlier feature the current answer does not come
// from, "over" = it overlaps something newer. Nothing is removed on the strength of a label here.
import { LAYERS } from './layers.js';

const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

const CHART = [
  ['◄◄ 7d / ◄ 1d / 1d ► / 7d ►►, and the date box',
   'move "now". Everything is computed as if today were that day - faded candles are the future and no rule may look at them. Arrow keys do the same, Shift + arrow jumps a week. The date is in the URL, so a view can be reopened.'],
  ['✋ Pan · ╱ Line · ▭ Box · ✎ Sketch',
   'Pan is the default. Line = click two points, Box = click two corners; both are saved as ground truth with the label in the box beside them. Sketch = hold the mouse down and draw freely, then say what you are showing - Ctrl + drag does the same from any tool. Keys: L, B, S, Esc to cancel.'],
  ['show: ' + LAYERS.map(([, label]) => label).join(' · '),
   'hide any layer on the chart when it gets busy. What you untick is remembered the next time the page opens.'],
  ['the grey timestamp at the top right',
   'when this page\'s own files were last changed. If it is older than the last edit, the browser is showing a cached page - so a stale page can never be mistaken for a broken feature.'],
];

const CARDS = [
  ['The setup, explained', 'use',
   'The answer. The move running now as the yardstick, then the trend, the current and next support and resistance - each saying WHAT it is and HOW it was found, with the dots it is made of and the precedent the backward search stopped at.',
   'Click one line to see only it on the chart, with the dots it is made of and their swing boxes. Click it again to put everything back.'],
  ['Settings (pipes)', 'old',
   'The first thing this page did (2026-09-22): every rule of the pipe search as a live setting - windows, magnitudes, width rules, how many pipes and single lines per level.',
   'The lines you approved do NOT come from here; they come from the Swing points card. Kept because it is the only way to see the pipe rules move.'],
  ['Zones & ladder from the price', 'over',
   'Price bands at a swing size, with every visit marked on the band, plus a ladder read from the current price.',
   'The ladder here is now also in The setup, explained. What is only here: the coloured band across a level\'s whole life with its visit ticks. Switch it on with "show zones" inside the card.'],
  ['Swing points (peaks & valleys)', 'use',
   'Where the lines actually come from. Pick the swing size (or a trade length to calibrate one), then the rule: "recent levels + their history" is yours, "by the move that ran into it" weighs a touch by its move, "any line, by touch count" is the plain geometric one.',
   'Every line it finds gets a ✓ / ✗ - your verdict is saved as ground truth, with a note and a "draw instead" drawing. Presets at the top save a whole set of settings by name.'],
  ['Result at "now"', 'old',
   'The pipe search\'s own output for the settings above: the ranked pipes, the single lines, and the swing sizes the width rules were judged against.',
   'Belongs to Settings (pipes), not to the setup. It also says when a search stopped early on its budget.'],
  ['Sketch', 'use',
   'Where a freehand sketch waits while you decide what it is. Several strokes count as one thing, under one note.',
   '"keep it" puts it with your drawings; "just showing you" leaves it as an explanation that can be cleared in one go later. Esc throws away an undecided one.'],
  ['My ground truth: setups, drawings, verdicts', 'use',
   'Everything you recorded, grouped by the DATE YOU DREW AT: the setups of that date with your note on each, the drawings in them, the loose ones, and the ✓/✗ you gave the code there. Each row says what the system does with it - "scored" means the algorithm is measured against it, "explains only" means it is talking to Claude. This card is the answer key.',
   'The picker at the top lists every setup and every date you drew - choose one and the page goes there. ⤒ the date puts "now" back there, so the code recomputes the setup as it was. see = show it on the chart alone · ✎ redraw = draw it again in place, keeping its note, its setup and the verdict pointing at it · × removes it (a sketch goes with all its strokes). The label and the note are editable where they sit, and "+ setup from these" makes a setup out of that date\'s loose drawings. Untick "every date on the chart" and only the date you are standing on is painted.'],
  ['Detected setups: resistance + bull flag', 'old',
   'The stage-2 detector run over the whole history: every episode it fired on, to step through and judge.',
   'About the setup detector, not the line algorithm - the line work does not read it.'],
];

const TAG = { use: ['in use', 'ok'], old: ['earlier feature', 'hint'], over: ['overlaps a newer card', 'warn'] };

export function renderGuide(root) {
  const chart = CHART.map(([what, how]) =>
    `<div class="g-row"><div class="t">${esc(what)}</div><div class="m">${esc(how)}</div></div>`).join('');
  const cards = CARDS.map(([name, state, what, how]) => {
    const [label, cls] = TAG[state];
    return `<div class="g-row"><div class="t">${esc(name)} <span class="g-tag ${cls}">${label}</span></div>
      <div class="m">${esc(what)}</div><div class="m g-how">${esc(how)}</div></div>`;
  }).join('');
  root.innerHTML = `<div class="card guide">
      <div class="t">Above the chart</div>${chart}</div>
    <div class="card guide">
      <div class="t">The cards below, in order</div>${cards}
      <div class="m g-note">"in use" / "earlier feature" / "overlaps" is Claude's read of what each
        card still earns, for you to confirm - nothing has been removed on the strength of it.</div>
    </div>`;
}
