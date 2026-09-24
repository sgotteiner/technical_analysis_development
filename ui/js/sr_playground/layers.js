// One place to show or hide what is on the chart (owner, 2026-09-24: "its a bit confusing to see
// all of that. can i have a checkbox to hide things like my drawings or dots or calculated sr lines?").
const KEY = 'sr_playground_layers_v1';
export const LAYERS = [
  ['drawings', 'my drawings'],
  ['dots', 'dots'],
  ['zones', 'zones'],
  ['lines', 'calculated lines'],
  ['pipes', 'pipes'],
  ['detections', 'detected setups'],
];

export function createLayers({ root, onChange }) {
  let state = Object.fromEntries(LAYERS.map(([key]) => [key, true]));
  try { Object.assign(state, JSON.parse(localStorage.getItem(KEY)) || {}); } catch (e) {}

  function render() {
    root.innerHTML = '<span class="hint">show:</span>' + LAYERS.map(([key, label]) =>
      `<label><input type="checkbox" data-layer="${key}" ${state[key] ? 'checked' : ''}> ${label}</label>`).join('');
    root.querySelectorAll('[data-layer]').forEach(box => {
      box.onchange = () => {
        state[box.dataset.layer] = box.checked;
        try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (e) {}
        onChange({ ...state });
      };
    });
  }

  render();
  return { state: () => ({ ...state }) };
}
