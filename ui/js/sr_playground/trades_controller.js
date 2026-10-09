// The strategy's trades on the chart (owner, 2026-10-08: "i wanna see trade entries and exists"):
// a green triangle where it bought, a mark where it sold (blue target, red stop, grey time), a dashed
// path between them with the stop and target, and a click on either opens the chart card with the
// whole trade. The Trades card has the totals and the list; a row jumps "now" to that trade.
import { api } from './api.js';

const NEAR_PX = 10;
const COLOR = { target: '#29b6f6', stop: '#ef5350', time: '#9598a1', open: '#ffca28' };
const esc = s => String(s == null ? '' : s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

export function createTradesController({ root, card, chart, series, drawings, getNow, setNow, status }) {
  let info = null, visible = true;

  const marks = () => (info && visible ? info.trades : []).flatMap(t => [
    { t, time: t.entry_time, price: t.entry, at: 'entry' },
    ...(t.exit_time ? [{ t, time: t.exit_time, price: t.exit, at: 'exit' }] : [])]);
  card.register({
    hit(p) {
      const m = marks().find(m => {
        const x = chart.timeScale().timeToCoordinate(m.time), y = series.priceToCoordinate(m.price);
        return x !== null && y !== null && Math.hypot(p.point.x - x, p.point.y - y) <= NEAR_PX;
      });
      if (!m) return null;
      const t = m.t;
      return { head: `trade ${t.how === 'open' ? '(open)' : (t.ret_pct >= 0 ? '+' : '') + t.ret_pct.toFixed(1) + '%'}`,
        items: [{ title: 'the situation', text: t.situation, color: '#d1d4dc' },
                { title: 'why it bought', text: t.why, color: '#26a69a' },
                { title: 'how it ended', text: t.result, color: COLOR[t.how] },
                ...(t.how === 'open' ? [] : [{ title: t.ret_pct > 0 ? 'why it worked' : 'what went wrong', text: t.verdict,
                  color: t.ret_pct > 0 ? '#26a69a' : '#ef5350' }])] };
    },
    onOpen: () => {}, onClose: () => {},
  });

  function paint() {
    drawings.setTrades(info && visible ? info.trades.map(t => ({ ...t, color: COLOR[t.how] })) : []);
  }

  function draw() {
    if (!info) { root.innerHTML = '<div class="m hint">loading the trades…</div>'; return; }
    const s = info.stats || {};
    const closed = info.trades.filter(t => t.how !== 'open');
    const won = closed.filter(t => t.ret_pct > 0).length;
    root.innerHTML = '<div class="m hint">Two entries: a line on the zigzag breaks and price comes back to it (buy the retest),'
      + ' or, in an up trend by the rule, the zigzag makes a new higher low. No target: the stop rides up the zigzag\'s higher'
      + ' lows. Show or hide with "trades" above the chart.</div>'
      + `<div class="m">up to now: ${info.trades.length} trades, ${won} of ${closed.length} closed ones won`
      + (s.trades ? ` · whole history: ${s.trades} trades, win ${s.win_rate.toFixed(0)}%, avg ${s.avg_ret.toFixed(1)}% a trade, profit factor ${s.profit_factor.toFixed(2)}, compounded ${s.compounded >= 0 ? '+' : ''}${s.compounded.toFixed(0)}%` : '') + '</div>'
      + info.trades.slice().reverse().map(t => `<div class="m found tr-row" data-b="${t.entry_bar}" style="color:${COLOR[t.how]};cursor:pointer">`
        + `${esc(new Date(t.entry_time * 1000).toISOString().slice(0, 10))} buy ${Math.round(t.entry).toLocaleString()}`
        + ` → ${t.how === 'open' ? 'open' : `${t.how} ${(t.ret_pct >= 0 ? '+' : '') + t.ret_pct.toFixed(1)}%`}</div>`).join('');
    root.querySelectorAll('.tr-row').forEach(r => r.onclick = () => setNow(+r.dataset.b));
  }

  async function refresh() {
    try { info = await api.trades(getNow()); }
    catch (e) { info = null; status(`trades: ${e.message}`, 'err'); }
    paint(); draw();
  }

  draw();
  return { refresh, setVisible(on) { visible = on; paint(); } };
}
