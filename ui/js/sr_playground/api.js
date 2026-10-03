// S/R playground API client (routes/sr_playground_routes.py).
// `signal` lets a caller drop a request it no longer wants (stepping "now" again while the
// previous answer is still coming): an aborted call rejects with an AbortError.
async function call(method, url, body, signal) {
  let res;
  try {
    res = await fetch(url, { method, headers: { 'Content-Type': 'application/json' },
      body: body === undefined ? undefined : JSON.stringify(body), signal });
  } catch (e) {
    if (e.name === 'AbortError') throw e;              // we dropped it on purpose
    // a tab stays open and looks alive after its server has gone, so every click silently fails:
    // say which it is instead of leaving the page looking merely unresponsive
    throw new Error(`the server did not answer — is scripts/sr_playground.py still running? (${url})`);
  }
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const d = data.detail;
    // the page is served from disk but the routes live in the running process, so a NEW page can
    // meet an OLD server. FastAPI says "Not Found" for a missing ROUTE and something specific for
    // a missing item, so the two are distinguishable - say which it is.
    if (res.status === 404 && d === 'Not Found')
      throw new Error(`${url} is not on this server: it is older than the page — restart scripts/sr_playground.py`);
    throw new Error(typeof d === 'string' ? d : Array.isArray(d) ? d.map(e => e.msg).join('; ') : res.statusText);
  }
  return data;
}

export const api = {
  candles: () => call('GET', '/api/candles'),
  defaults: () => call('GET', '/api/defaults'),
  view: req => call('POST', '/api/view', req),
  points: (req, signal) => call('POST', '/api/points', req, signal),
  zones: req => call('POST', '/api/zones', req),
  score: req => call('POST', '/api/score', req),
  presets: () => call('GET', '/api/presets'),
  savePreset: p => call('POST', '/api/presets', p),
  judgements: () => call('GET', '/api/judgements'),
  judge: j => call('POST', '/api/judgements', j),
  patchJudgement: (id, patch) => call('PATCH', `/api/judgements/${id}`, patch),
  unjudge: id => call('DELETE', `/api/judgements/${id}`),
  annotations: () => call('GET', '/api/annotations'),
  addAnnotation: a => call('POST', '/api/annotations', a),
  addAnnotationGroup: items => call('POST', '/api/annotations/group', { items }),
  clearAsked: () => call('DELETE', '/api/annotations/asked'),
  patchAnnotation: (id, patch) => call('PATCH', `/api/annotations/${id}`, patch),
  deleteAnnotation: id => call('DELETE', `/api/annotations/${id}`),
  setups: () => call('GET', '/api/setups'),
  addSetup: s => call('POST', '/api/setups', s),
  patchSetup: (id, patch) => call('PATCH', `/api/setups/${id}`, patch),
  deleteSetup: id => call('DELETE', `/api/setups/${id}`),
  evaluation: () => call('GET', '/api/setups/evaluation'),
  detections: () => call('GET', '/api/setup-detections'),
};
