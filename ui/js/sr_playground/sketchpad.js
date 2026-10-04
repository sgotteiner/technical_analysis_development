// A sketch is several strokes explaining ONE thing, and he decides at the end what happens to it
// (owner, 2026-10-03: "id like to make more than one draw for a certain note. a setup." /
// "i want to decide if i sketch to communicate with you and forget or to really save it").
//
// Strokes are held here until he decides, so nothing reaches his drawings until he says so - which
// is also why cancelling can no longer leave trash behind.
import { api } from './api.js';

export function createSketchpad({ root, status, getNow, getCandles, chart, onSaved,
                                  onPending = () => {} }) {
  let strokes = [], note = '', at = null;      // `at` is the date of the FIRST stroke, not of "keep"

  const day = t => new Date(t * 1000).toISOString().slice(0, 10);

  const render = () => {
    if (!strokes.length) {
      root.innerHTML = `<button id="sk-clear" class="hint">clear the sketches I was only showing you</button>`;
      root.querySelector('#sk-clear').onclick = clearAsked;
      return;
    }
    root.innerHTML = `<div class="card sketchpad">
        <div class="t">${strokes.length} stroke${strokes.length > 1 ? 's' : ''} drawn on ${day(at)} —
          what are you showing? <span class="warn">not saved yet</span></div>
        <textarea id="sk-note" rows="2" placeholder="one note for all of them">${note.replace(/</g, '&lt;')}</textarea>
        <div class="row">
          <button id="sk-keep" title="save it with my drawings">keep it</button>
          <button id="sk-ask">just showing you</button>
          <button id="sk-drop" class="hint">discard</button>
        </div>
        <div class="m">keep more strokes coming — they all join this one note</div>
      </div>`;
    const area = root.querySelector('#sk-note');
    area.oninput = () => { note = area.value; };
    root.querySelector('#sk-keep').onclick = () => commit('keep');
    root.querySelector('#sk-ask').onclick = () => commit('ask');
    root.querySelector('#sk-drop').onclick = discard;
  };

  async function commit(purpose) {
    // the date he DREW at, not the date he happens to be standing on when he answers: stepping the
    // chart between the stroke and "keep it" used to stamp the sketch with the wrong day
    const group = 'g' + Date.now().toString(36);
    const items = strokes.map(points => ({ kind: 'freehand', label: 'sketch', points, note,
      purpose, group, drawn_at: at }));
    try {
      const saved = await api.addAnnotationGroup(items);
      strokes = []; note = ''; at = null;
      render(); chart.setPending([]);
      status(`${saved.length} stroke${saved.length > 1 ? 's' : ''} saved${purpose === 'ask' ? " (I'll clear them later)" : ''}`);
      onSaved(saved);
    } catch (e) { status(`sketch not saved: ${e.message}`, 'err'); }
  }

  function discard() {
    strokes = []; note = ''; at = null;
    render(); chart.setPending([]);
    status('sketch discarded');
  }

  async function clearAsked() {
    try {
      const { deleted } = await api.clearAsked();
      status(deleted ? `cleared ${deleted} sketch${deleted > 1 ? 'es' : ''} you were only showing me`
                     : 'nothing to clear');
      if (deleted) onSaved([]);
    } catch (e) { status(`not cleared: ${e.message}`, 'err'); }
  }

  render();
  return {
    /** A finished stroke joins the open sketch; NOTHING IS SAVED until he answers the card, so the
     *  card is opened and said out loud - a stroke held silently reads as a stroke lost
     *  (owner, 2026-10-04: "i drew but dont know if it saved"). */
    add(points) {
      if (!strokes.length) at = getCandles()[getNow()].time;
      strokes.push(points);
      chart.setPending(strokes);
      render();
      onPending();
      status(`${strokes.length} stroke${strokes.length > 1 ? 's' : ''} on ${day(at)} — NOT saved yet:`
             + ' say what you are showing in the Sketch card, then "keep it"', 'warn');
    },
    pending: () => strokes.length,
    discard,
  };
}
