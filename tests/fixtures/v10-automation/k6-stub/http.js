// Stand-in for 'k6/http': answers from the scenario's status/duration tables, keyed by the request's name tag.
function send(method, url, body, params) {
  const k = globalThis.__K6;
  const name = ((params || {}).tags || {}).name;
  const status = name in k.statuses ? k.statuses[name] : 200;
  const duration = name in k.durations ? k.durations[name] : 100;
  k.clock += duration;
  const callback = (params || {}).responseCallback;
  k.calls.push({ method, url, body, name, tags: (params || {}).tags || {}, headers: (params || {}).headers || {},
                 expected: callback ? callback.expected : null, status });
  return { status, timings: { duration }, body: '' };
}

export default {
  get: (url, params) => send('GET', url, null, params),
  request: (method, url, body, params) => send(method, url, body, params),
  expectedStatuses: (...codes) => ({ expected: codes }),
};
