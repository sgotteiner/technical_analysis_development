// The toolbar and the keyboard: which tool is armed, and how each one is used.
// A drawing tool nobody can find is a tool nobody has (owner, 2026-10-03: "the drawing doesnt work
// and there isnt a text how to use it") - so arming a tool always says how to use it.
const HOW = {
  pan: 'drag to pan · Ctrl + drag to sketch something you want to explain',
  line: 'click two points to draw a line · Esc to cancel',
  box: 'click two opposite corners to draw a box · Esc to cancel',
  sketch: 'hold the mouse down and draw freely, then say what you are showing · Esc to cancel',
};

const KEY_TOOL = { l: 'line', b: 'box', s: 'sketch' };

export function createTools({ drawings, status, sketchpad, step }) {
  function setTool(t) {
    drawings.setTool(t);
    document.querySelectorAll('[data-tool]').forEach(b => b.classList.toggle('on', b.dataset.tool === t));
    status(HOW[t] || '');
  }
  document.querySelectorAll('[data-tool]').forEach(b => b.onclick = () => setTool(b.dataset.tool));
  document.addEventListener('keydown', e => {
    if (e.target.tagName === 'INPUT' && e.target.type !== 'checkbox') return;   // arrows edit fields
    if (e.key === 'ArrowLeft') return step(-(e.shiftKey ? 7 : 1));
    if (e.key === 'ArrowRight') return step(e.shiftKey ? 7 : 1);
    if (e.key === 'Escape') {
      if (sketchpad.pending()) sketchpad.discard();     // an undecided sketch goes first
      drawings.cancel();
      return setTool('pan');
    }
    const t = KEY_TOOL[e.key.toLowerCase()];
    if (t) setTool(t);
  });
  return { setTool };
}
