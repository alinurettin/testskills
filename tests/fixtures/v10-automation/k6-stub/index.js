// Stand-in for 'k6': check() records every check with its tags, sleep() advances the simulated clock.
export function check(val, sets, tags) {
  let all = true;
  for (const [name, fn] of Object.entries(sets)) {
    const ok = Boolean(fn(val));
    globalThis.__K6.checks.push({ name, ok, tags: tags || {} });
    if (!ok) all = false;
  }
  return all;
}

export function sleep(seconds) {
  globalThis.__K6.clock += seconds * 1000;
  globalThis.__K6.slept += seconds;
}
