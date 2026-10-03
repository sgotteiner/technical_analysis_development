// The sidebar as cards you open and close (owner, 2026-10-03: "the sidebar is too confusing should
// be opening cards that each current sections is a card and one card will be explanation").
// Each <h2> and the <section> under it become one card; what is open is remembered per browser.
const KEY = 'sr_playground_cards_v1';

export function createCards({ root, open = [] }) {
  let state = {};
  try { state = JSON.parse(localStorage.getItem(KEY)) || {}; } catch (e) {}

  const heads = [...root.querySelectorAll('h2')];
  heads.forEach(h => {
    const body = h.nextElementSibling;
    if (!body || body.tagName !== 'SECTION') return;
    const id = body.id;
    const wrap = document.createElement('div');
    wrap.className = 'card-sec';
    h.parentNode.insertBefore(wrap, h);
    wrap.appendChild(h);
    wrap.appendChild(body);
    // a card nobody has set an opinion on follows the defaults, so the page opens on what matters
    const isOpen = id in state ? state[id] : open.includes(id);
    wrap.classList.toggle('shut', !isOpen);
    h.insertAdjacentHTML('afterbegin', '<span class="caret"></span>');
    h.onclick = () => {
      const shut = wrap.classList.toggle('shut');
      state[id] = !shut;
      try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (e) {}
    };
  });
  return {
    /** Open one card by the id of its section (used when something lands in it). */
    show(id) {
      const body = root.querySelector('#' + id);
      if (body && body.parentNode.classList.contains('shut')) body.parentNode.classList.remove('shut');
    },
  };
}
