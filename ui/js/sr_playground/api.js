// S/R playground API client (routes/sr_playground_routes.py).
async function call(method, url, body) {
  const res = await fetch(url, { method, headers: { 'Content-Type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body) });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const d = data.detail;
    throw new Error(typeof d === 'string' ? d : Array.isArray(d) ? d.map(e => e.msg).join('; ') : res.statusText);
  }
  return data;
}

export const api = {
  candles: () => call('GET', '/api/candles'),
  defaults: () => call('GET', '/api/defaults'),
  view: req => call('POST', '/api/view', req),
  points: req => call('POST', '/api/points', req),
  annotations: () => call('GET', '/api/annotations'),
  addAnnotation: a => call('POST', '/api/annotations', a),
  patchAnnotation: (id, patch) => call('PATCH', `/api/annotations/${id}`, patch),
  deleteAnnotation: id => call('DELETE', `/api/annotations/${id}`),
  setups: () => call('GET', '/api/setups'),
  addSetup: s => call('POST', '/api/setups', s),
  patchSetup: (id, patch) => call('PATCH', `/api/setups/${id}`, patch),
  deleteSetup: id => call('DELETE', `/api/setups/${id}`),
  evaluation: () => call('GET', '/api/setups/evaluation'),
  detections: () => call('GET', '/api/setup-detections'),
};
