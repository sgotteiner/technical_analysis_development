// The owner's verdicts on the lines the CODE drew (2026-10-03: "if you want me to see and judge
// tell me"). A verdict is ground truth about THIS line at THIS date - not about the settings that
// produced it - so a later search with other settings is scored against it. On a ✗ he can say why,
// and draw the line he would use instead ("a note option is always good").
import { api } from './api.js';

const SAME_LINE_PCT = 0.5;        // must match SAME_LINE_PCT in repositories/sr_annotation_repo.py
const mark = v => v === 'good' ? '✓' : '✗';

export function createVerdicts({ status, redraw, getSettings, getNowTime, armLineTool, showDrawing }) {
  let judgements = [], awaiting = null;    // the verdict whose "draw instead" line is being drawn
  let failed = null;                       // the last click that did not get saved

  api.judgements().then(list => { judgements = list; redraw(); },
                       e => { failed = `could not read your verdicts: ${e.message}`; redraw(); });

  // a click that does not reach the server must say so IN the panel: the top bar is not where he
  // is looking when he clicks a line (owner, 2026-10-03: "i clicked the 79 too and didnt see any
  // change" - his server had stopped and every click failed at the network)
  const fail = (what, e) => { failed = `${what}: ${e.message}`; status(failed, 'err'); redraw(); };
  const done = said => { failed = null; if (said) status(said); redraw(); };

  const replace = saved => [...judgements.filter(j => j.id !== saved.id
    && !(j.at === saved.at && j.kind === saved.kind
         && Math.abs(j.price / saved.price - 1) * 100 <= SAME_LINE_PCT)), saved];

  async function judge(kind, price, verdict, slope_pct_day) {
    try {
      const saved = await api.judge({ kind, price, verdict, slope_pct_day,
        at: getNowTime(), settings: getSettings() });
      judgements = replace(saved);
      done(`${mark(verdict)} ${Math.round(price).toLocaleString()} recorded`);
    } catch (e) { fail(`${mark(verdict)} ${Math.round(price).toLocaleString()} NOT saved`, e); }
  }

  async function unjudge(id) {
    try {
      await api.unjudge(id);
      judgements = judgements.filter(j => j.id !== id);
      if (awaiting === id) awaiting = null;
      done('verdict taken back');
    } catch (e) { fail('verdict NOT removed', e); }
  }

  async function patch(id, body, said) {
    try {
      const saved = await api.patchJudgement(id, body);
      judgements = judgements.map(j => j.id === id ? saved : j);
      done(said);
    } catch (e) { fail('NOT saved', e); }
  }

  return {
    all: () => judgements,
    failed: () => failed,
    handlers: {
      onJudge: judge,
      onUnjudge: unjudge,
      onNote: (id, note) => patch(id, { note }, note ? 'reason saved' : 'reason cleared'),
      onDrawInstead: id => {                 // arm the line tool; the next drawing answers this one
        awaiting = id;
        armLineTool();
        status('draw the line you would use instead (Esc to cancel)');
      },
      onShowReplacement: id => {
        const j = judgements.find(x => x.id === id);
        if (j && j.replacement) showDrawing(j.replacement);
      },
    },
    /** Called when a drawing is created: links it if one was asked for. */
    linkDrawing(annotationId) {
      if (!awaiting) return false;
      const id = awaiting;
      awaiting = null;
      patch(id, { replacement: annotationId }, 'recorded as the line you would use instead');
      return true;
    },
  };
}
