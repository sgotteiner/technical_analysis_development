// The lines the code found, each with the owner's verdict on it (2026-10-03: "if you want me to
// see and judge tell me"). A verdict belongs to a line at a date, so the row carries the price and
// the "now" it is being judged at; re-clicking the active mark takes the verdict back.
const SAME_LINE_PCT = 0.5;        // must match SAME_LINE_PCT in repositories/sr_annotation_repo.py

const day = (candles, bar) => new Date(candles[bar].time * 1000).toISOString().slice(0, 10);
const num = v => Math.round(v).toLocaleString();
const pctDay = slope => (Math.expm1(slope) * 100).toFixed(2);

export const verdictFor = (judgements, at, kind, price) => judgements.find(j =>
  j.at === at && j.kind === kind && Math.abs(j.price / price - 1) * 100 <= SAME_LINE_PCT);

// a level is judged at its own price; a trend at the price it holds at "now", so the two are
// comparable and a verdict survives a settings change that moves the line slightly
export const trendPriceAt = (t, bar) => Math.exp(t.y1 + t.slope * (bar - t.x1));

function marks(kind, price, verdict, extra = '') {
  const on = v => verdict && verdict.verdict === v ? ' on' : '';
  const d = `data-jk="${kind}" data-jp="${price}"${extra}`;
  return `<span class="judge">`
    + `<button class="j good${on('good')}" ${d} data-jv="good" title="good line">✓</button>`
    + `<button class="j bad${on('bad')}" ${d} data-jv="bad" title="not a line I'd use">✗</button>`
    + `</span>`;
}

const esc = s => String(s == null ? '' : s).replace(/[&<>"]/g, c =>
  ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

/** Under a judged row: why, and the line he drew instead (owner, 2026-10-03). */
function reason(verdict, drawings) {
  if (!verdict) return '';
  const drawn = verdict.replacement && drawings.find(a => a.id === verdict.replacement);
  return `<div class="m why" data-jid="${verdict.id}">`
    + `<input class="jnote" placeholder="why${verdict.verdict === 'bad' ? ' not' : ''}? (optional)"`
    + ` value="${esc(verdict.note)}">`
    + (drawn ? `<button class="jrep on" title="go to the line you drew instead">instead: ${esc(drawn.label)}</button>`
             : `<button class="jrep" title="draw the line you would use instead">draw instead</button>`)
    + `</div>`;
}

export function foundRows({ state, info, colors, candles, judgements = [], drawings = [] }) {
  if (!info || !state.drawLines) return '';
  const at = candles[info.end] ? candles[info.end].time : 0;
  return info.sizes.map((g, i) => {
    const color = colors[i % colors.length];
    const row = (text, tail = '') => `<div class="m found" style="color:${color}">${text}${tail}</div>`;
    if (state.mode === 'touches') {
      return (g.lines || []).map((l, j) => row(`line ${j + 1}: ${l.touches} touches · ${pctDay(l.slope)}%/day`
        + ` · ${day(candles, l.first)} → ${day(candles, l.last)}`)).join('');
    }
    const levels = (g.levels || []).map(lv => {
      const v = verdictFor(judgements, at, 'level', lv.price);
      // Branch on the SHAPE of the answer, not on the rule selected: switching rule repaints with
      // the previous answer still in hand, and those lines have no move to show.
      const text = lv.vs_now !== undefined
        ? `${num(lv.price)} ${lv.label}${lv.at_price_now ? ' (price on it)' : ''}`
          + ` · move ${lv.move.toFixed(0)}% = ${lv.vs_now.toFixed(2)}× now — ${lv.term}`
          + ` · ${lv.touches} touches${lv.dropped ? ` (${lv.dropped} too old for their move)` : ''}`
          + ` · ${day(candles, lv.first)} → ${day(candles, lv.last)}`
        : `level ${num(lv.price)}${lv.from_history ? ' (target)' : ''}`
          + `${lv.at_price_now ? ' (price on it)' : ''}`
          + ` · touched ${lv.touches}× (${lv.history} before) · ${day(candles, lv.first)} → ${day(candles, lv.last)}`;
      return row(text, marks('level', lv.price, v)) + reason(v, drawings);
    }).join('');
    const trends = (g.trends || []).map(t => {
      const p = trendPriceAt(t, info.end);
      const v = verdictFor(judgements, at, 'trend', p);
      return row(`${t.role} trend ${pctDay(t.slope)}%/day · ${t.touches} touches`
        + ` · ${day(candles, t.first)} → ${day(candles, t.last)} · ${num(p)} now`,
        marks('trend', p, v, ` data-js="${pctDay(t.slope)}"`)) + reason(v, drawings);
    }).join('');
    return theTrade(g, color) + levels + trends;
  }).join('');
}

/** The setup in words: what each line is and how it was found, with the points it used, so the
    ones it actually used can be told apart from the hundreds on the chart (owner, 2026-10-03). */
export function theStory(g, focus = null) {
  const st = g.story;
  if (!st || !st.lines || !st.lines.length) return '';
  const rows = st.lines.map(l =>
    '<div class="m line' + (focus === l.role ? ' on' : '') + '" data-role="' + esc(l.role) + '"'
    + ' title="click to see only this line">'
    + '<b>' + esc(l.role) + '</b> ' + num(l.price)
    + (l.dates && l.dates.length ? ' <span class="used">from ' + l.dates.join(', ') + '</span>' : '')
    + '<div class="how">' + esc(l.how) + '</div></div>').join('');
  return '<div class="card story"><div class="t">the setup \u00b7 price ' + num(st.price_now)
    + ', the move running now +' + st.current_move.toFixed(1) + '% from ' + esc(st.move_from)
    + (focus ? ' \u00b7 <a href="#" id="st-all">show all</a>' : '')
    + '</div>' + rows + '</div>';
}

/** The trade the ladder describes: what you buy, where you are wrong, where you sell. */
function theTrade(g, color) {
  const l = g.ladder;
  if (!l || !l.entry || !l.stop || !l.risk_pct || g.current_move == null) return '';
  const rungs = (l.targets || []).filter(t => t.reward_pct != null && t.r != null).map((t, i) =>
    `<div class="m">target ${i + 1} ${num(t.price)} · +${t.reward_pct.toFixed(1)}% · <b>${t.r.toFixed(2)} R</b></div>`).join('');
  return `<div class="card trade" style="border-left-color:${color}">
      <div class="t">the trade · move running now ${g.current_move.toFixed(1)}%</div>
      <div class="m">buy the break of ${num(l.entry)} · stop ${num(l.stop)} · risk ${l.risk_pct.toFixed(1)}%</div>
      ${rungs || '<div class="m">nothing above to aim at</div>'}
    </div>`;
}

/** Wire the marks, the note and the "draw instead" button. */
export function bindFound(root, { candles, info, judgements, onJudge, onUnjudge, onNote, onDrawInstead,
                                  onShowReplacement }) {
  const at = info && candles[info.end] ? candles[info.end].time : 0;
  root.querySelectorAll('button.j').forEach(b => b.onclick = () => {
    const kind = b.dataset.jk, price = +b.dataset.jp, want = b.dataset.jv;
    const had = verdictFor(judgements, at, kind, price);
    if (had && had.verdict === want) return onUnjudge(had.id);     // clicking it again takes it back
    onJudge(kind, price, want, b.dataset.js === undefined ? null : +b.dataset.js);
  });
  root.querySelectorAll('.why').forEach(w => {
    const id = w.dataset.jid, note = w.querySelector('.jnote'), rep = w.querySelector('.jrep');
    note.onchange = () => onNote(id, note.value);
    note.onkeydown = e => { if (e.key === 'Enter') note.blur(); };
    rep.onclick = () => (rep.classList.contains('on') ? onShowReplacement : onDrawInstead)(id);
  });
}
