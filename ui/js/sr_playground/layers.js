// One place to show or hide what is on the chart (owner, 2026-09-24: "its a bit confusing to see
// all of that. can i have a checkbox to hide things like my drawings or dots or calculated sr lines?").
const KEY = 'sr_playground_layers_v1';
export const LAYERS = [
  ['drawings', 'my drawings'],
  ['dots', 'dots'],
  ['boxes', 'swing boxes'],
  ['zones', 'zones'],
  ['lines', 'calculated lines'],
  ['pipes', 'pipes'],
  ['detections', 'detected setups'],
  ['closeline', 'close-only line'],
  ['closedots', 'close dots'],
  ['zigzag', 'zigzag'],
  ['events', 'events'],              // every event over history, a dot a day (events_controller.js)
  ['stars', 'stars on the lines'],   // breakout / retest / fakeout at the lines on screen (line_dots.js)
  ['trades', 'trades'],              // his strategy's entries and exits (trades_controller.js)
];
const OFF_BY_DEFAULT = ['closeline', 'closedots', 'zigzag'];     // a different way to see the chart, not a layer to hide

export function createLayers({ root, onChange }) {
  let state = Object.fromEntries(LAYERS.map(([key]) => [key, !OFF_BY_DEFAULT.includes(key)]));
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
