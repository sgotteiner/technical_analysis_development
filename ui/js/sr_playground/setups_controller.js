// Setups and detections: keeps the setup list and its detector verdicts in sync with the server,
// and steps the chart through the detector's setups.
import { api } from './api.js';
import { renderSetups } from './setups_panel.js';
import { renderDetections } from './detections_panel.js';

export function createSetupsController({ drawings, getAnnotations, setNow, status, onChange }) {
  let setups = [], evaluation = {}, episodes = null, current = null;
  const $ = id => document.getElementById(id);
  const fail = verb => e => status(`not ${verb}: ${e.message}`, 'err');

  async function reload() {
    [setups, evaluation] = await Promise.all([api.setups(), api.evaluation()]);
    render(); onChange();
  }

  function render() {
    renderSetups($('setups'), setups, getAnnotations(), evaluation, {
      onCreate: name => api.addSetup({ name }).then(reload, fail('saved')),
      onPatch: (s, patch) => api.patchSetup(s.id, patch).then(reload, fail('saved')),
      onDelete: s => confirm(`Delete setup "${s.name}"? Its drawings stay.`) && api.deleteSetup(s.id).then(reload, fail('deleted')),
    });
  }

  async function assign(drawing, setupId) {       // a drawing belongs to at most one setup
    try {
      for (const s of setups.filter(s => s.members.includes(drawing.id) && s.id !== setupId))
        await api.patchSetup(s.id, { members: s.members.filter(m => m !== drawing.id) });
      const target = setups.find(s => s.id === setupId);
      if (target && !target.members.includes(drawing.id))
        await api.patchSetup(target.id, { members: [...target.members, drawing.id] });
      await reload();
    } catch (e) { fail('saved')(e); }
  }

  function renderDet() {
    renderDetections($('detections'), episodes, current, {
      onPick: j => {
        current = j;
        const ep = episodes[j];
        setNow(ep.last);
        drawings.setDetected([{ kind: 'line', points: ep.line.points, label: 'detected resistance' },
                              { kind: 'box', points: ep.box.points, label: 'detected flag' }]);
        renderDet();
      },
      onClear: () => { current = null; drawings.setDetected([]); renderDet(); },
    });
  }

  renderDet();
  api.detections().then(eps => { episodes = eps; renderDet(); }, fail('loaded'));
  return { reload, assign, setups: () => setups };
}
