// One small card over the chart that explains whatever dot was clicked - an event's dot or a line's
// end dot (owner, 2026-10-08: "i want a dot that i can click and it opens a card and explains" ...
// "the lines dont write text show a dot at the end of the line"). Every dot source registers a
// `hit(click)`; the first source that claims the click opens the card, and a click on nothing closes it.
import { api } from './api.js';

const esc = s => String(s == null ? '' : s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

export function createChartCard({ chart, container, canClick }) {
  const card = document.createElement('div');
  card.style.cssText = 'position:absolute;z-index:5;display:none;max-width:420px;background:#1e222d;'
    + 'border:1px solid #434651;border-radius:6px;padding:8px 10px;font-size:12px;color:#d1d4dc;'
    + 'box-shadow:0 4px 14px rgba(0,0,0,0.5)';
  container.appendChild(card);
  const sources = [];
  let current = null;                       // the source whose card is open

  function close() {
    card.style.display = 'none';
    const was = current; current = null;
    if (was) was.onClose();
  }

  // `items`: [{title, color, text, pic?, meaning?}] - one block per thing explained
  function open(source, head, items, point) {
    if (current && current !== source) close();
    card.innerHTML = '<div style="display:flex;justify-content:space-between;margin-bottom:4px">'
      + `<b>${esc(head)}</b><a href="#" data-x style="color:#787b86">✕</a></div>`
      + items.map(it => `<div style="margin:6px 0;color:${it.color}"><b>${esc(it.title)}</b>`
        // `pic`: a picture of what the name means (event_sketches.js) - built here, never from data
        + (it.pic ? `<div style="display:flex;gap:8px;align-items:center;margin:3px 0">${it.pic}`
          + `<span style="color:#9598a1">${esc(it.meaning || '')}</span></div>` : '')
        + `<div style="color:#d1d4dc;margin-top:2px">${esc(it.text)}</div></div>`).join('');
    // in the top corner AWAY from the dot: beside it, the card hid the very thing it explained
    // (owner, 2026-10-08: "but the pop up hides it")
    const right = point.x < container.clientWidth / 2;
    card.style.left = right ? 'auto' : '8px';
    card.style.right = right ? '70px' : 'auto';          // clear of the price scale
    card.style.top = '8px';
    card.style.display = 'block';
    card.querySelector('[data-x]').onclick = e => { e.preventDefault(); close(); };
    current = source;
    // the server log says what he opened, so a report needs no pasting
    api.seen({ head, first: items.length ? `${items[0].title}: ${items[0].text}` : '' });
  }

  chart.subscribeClick(p => {
    if (!canClick() || !p || !p.point) return;
    for (const s of sources) {
      const hit = s.hit(p);
      if (hit) { open(s, hit.head, hit.items, p.point); s.onOpen(hit); return; }
    }
    close();
  });

  return {
    register(source) { sources.push(source); },
    close,
    isOpen: source => current === source,
  };
}
