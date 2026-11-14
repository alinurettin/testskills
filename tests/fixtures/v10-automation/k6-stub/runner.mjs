// Runs a generated k6 script against the stand-in modules (tests only; this is NOT k6).
//   node runner.mjs <script.mjs> <scenario.json>
// scenario: { env, iterations: [{ at_s, vu, iteration, exec, statuses: {name: 200}, durations: {name: ms} }],
//             dropped, run_ms }
// Prints JSON: calls, checks, metric samples, a k6-style summary (values + threshold verdicts) and what
// handleSummary() returned.
import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

const [script, scenarioFile] = process.argv.slice(2);
const scenario = JSON.parse(fs.readFileSync(scenarioFile, 'utf8'));
const START = 1_700_000_000_000;
globalThis.__K6 = { clock: START, scenarioStart: START, iteration: 0, vu: 1, statuses: {}, durations: {},
                    calls: [], checks: [], metrics: {}, slept: 0, aborted: null };
globalThis.__ENV = scenario.env || {};
globalThis.open = (file) => fs.readFileSync(path.resolve(path.dirname(script), file), 'utf8');
Date.now = () => globalThis.__K6.clock;

const mod = await import(pathToFileURL(path.resolve(script)).href);
const k = globalThis.__K6;
for (const it of scenario.iterations || []) {
  k.clock = START + it.at_s * 1000;
  k.vu = it.vu || 1;
  k.iteration = it.iteration || 0;
  k.statuses = it.statuses || {};
  k.durations = it.durations || {};
  try {
    (it.exec ? mod[it.exec] : mod.default)();
  } catch (e) {
    if (!k.aborted) throw e;
  }
}

function percentile(sorted, p) {
  if (!sorted.length) return 0;
  const rank = (p / 100) * (sorted.length - 1);
  const lo = Math.floor(rank);
  const hi = Math.ceil(rank);
  return sorted[lo] + (sorted[hi] - sorted[lo]) * (rank - lo);
}
function valuesOf(metric) {
  const s = metric.samples;
  if (metric.type === 'counter') return { count: s.reduce((a, b) => a + b, 0) };
  if (metric.type === 'rate') {
    const passes = s.filter(Boolean).length;
    return { rate: s.length ? passes / s.length : 0, passes, fails: s.length - passes };
  }
  const sorted = [...s].sort((a, b) => a - b);
  return { count: s.length, avg: s.length ? s.reduce((a, b) => a + b, 0) / s.length : 0, min: sorted[0] || 0,
           med: percentile(sorted, 50), max: sorted[sorted.length - 1] || 0, 'p(90)': percentile(sorted, 90),
           'p(95)': percentile(sorted, 95), 'p(99)': percentile(sorted, 99) };
}
function holds(values, expr) {
  const m = expr.match(/^(p\(\d+\)|rate|count)\s*(<=|>=|==|<|>)\s*([\d.]+)$/);
  if (!m) throw new Error(`threshold expression not understood by the stand-in: ${expr}`);
  const left = values[m[1]];
  const right = Number(m[3]);
  return { '<': left < right, '>': left > right, '<=': left <= right, '>=': left >= right, '==': left === right }[m[2]];
}

const data = { state: { testRunDurationMs: scenario.run_ms }, metrics: {} };
for (const [name, metric] of Object.entries(k.metrics)) {
  data.metrics[name] = { type: metric.type, contains: metric.type === 'trend' ? 'time' : 'default', values: valuesOf(metric) };
}
data.metrics.dropped_iterations = { type: 'counter', contains: 'default', values: { count: scenario.dropped || 0 } };
for (const [key, exprs] of Object.entries(mod.options.thresholds)) {
  const tagged = key.match(/^checks\{phase:(\w+)\}$/);
  if (tagged) {
    const mine = k.checks.filter((c) => c.tags.phase === tagged[1]);
    const passes = mine.filter((c) => c.ok).length;
    data.metrics[key] = { type: 'rate', contains: 'default',
                          values: { rate: mine.length ? passes / mine.length : 0, passes, fails: mine.length - passes } };
  }
  if (!data.metrics[key]) throw new Error(`threshold on a metric the script never created: ${key}`);
  data.metrics[key].thresholds = {};
  for (const expr of exprs) data.metrics[key].thresholds[expr] = { ok: holds(data.metrics[key].values, expr) };
}
const returned = mod.handleSummary(data);
process.stdout.write(JSON.stringify({ options: mod.options, calls: k.calls, checks: k.checks, slept: k.slept,
                                      aborted: k.aborted, samples: k.metrics, summary: returned }));
