# Performance testing

## Contents
1. From requirement to thresholds
2. Choosing the load profile
3. Environment and data
4. Running and reading results
5. Reporting

---

## 1. From requirement to thresholds
A performance test without a pass/fail threshold is a demo. Take the numbers from the non-functional requirement: `quality_characteristic: performance-efficiency` in `requirements.json`.

| Requirement phrase | Threshold (k6) |
|---|---|
| "responds within 800 ms for 95% of requests" | `p95_ms: 800` → `qa_steady_ms_X: ['p(95)<800']`: steady state only, successful responses only (fast errors must not improve the percentile) |
| "error rate below 1%" | `error_rate: 0.01` → `qa_steady_failed: ['rate<0.01']`. Required: without it a run of failing requests would pass. An expected status (`expect_status: 422`) is not an error |
| "all responses correct" | `checks: ['rate>0.99']`, plus a `check` on the status code and key body fields |
| "200 concurrent users" | `target: {type: vus, vus: 200}` (closed model). Needs `think_time_s` or `pacing_s` from the requirement: throughput = users / (response time + think time), CT-PT v1.0 §4.2.4. Without it the generator stops (exit 2) |
| "50 requests/second at peak" | `target: {type: arrival-rate, rate: 50, unit: requests}` (open model, preferred for APIs). k6's rate counts **journeys** (iterations): a two-request journey at 50 journeys/s is 100 requests/s, so state the `unit`. `dropped_iterations: ['count==0']` proves the rate was really applied |

The generator prints the workload model it derived (model, journeys/s and requests/s per request, phases, VUs) and writes it into the script header. It stops with exit 2 when the target, the error budget or the closed-model think time is missing, and prints a `QUESTION` for what it had to assume. A weighted `mix` of journeys and a `data` file are shown in `assets/spec-examples/k6-mix.json`.

If the requirement has no numbers, **do not invent them silently.** Raise a question (the analysis linter's UNMEASURED finding). You may propose defaults such as Core Web Vitals, or p95 ≤ 1 s for interactive APIs, marked as assumptions.

## 2. Choosing the load profile
| Profile | Question it answers | Shape |
|---|---|---|
| smoke | Does the script work? Is the system alive under minimal load? | 1–2 VUs, 1 min. Run it first, every time. |
| load | Do we meet the requirement at expected peak? | Ramp to target, hold for 10–30 min, ramp down |
| stress | Where does it break, and does it recover? | Steps from 50% to 200% of the target, then back to the target. Thresholds apply before the overload (baseline) and after it (recovery), not during it |
| spike | Does it survive a sudden surge, such as a campaign start, and recover? | Short jump to 5× the target, then back; thresholds on baseline and recovery |
| soak | Does it stay healthy over hours (memory leaks, connection pools)? | Target held for 1–8 h |

Start with smoke, then load. Add stress, spike and soak by risk: campaigns, payments, month-end.

## 3. Environment and data
- Run against a **production-like test environment** that you own and are allowed to load. **Never** run against production or third-party services without written approval. Load tests can look like attacks, and they cost money.
- Mock or sandbox the third parties (payment, SMS). Load them only with the provider's agreement.
- Use realistic data volumes and **enough distinct test data**, such as many coupon codes and users. Otherwise caches and lock contention distort the results.
- Pass tokens and credentials through environment variables (`-e K6_TOKEN=...`) for **test accounts**. Never hard-code them.
- Keep the load generator outside the system under test, and monitor it too. A saturated generator gives false results.

## 4. Running and reading results
```bash
k6 run -e BASE_URL=https://staging.example.com perf/DS-010.k6.js      # exit 99 = a threshold failed
python scripts/k6_results.py DS-010-summary.json --out qa/results.json --tests qa/test-cases.json   # verdict under the TC
```
- The generated script writes `<spec id>-summary.json` through `handleSummary()` (`-e K6_SUMMARY=path` changes the name). k6 discourages `--summary-export`, and `k6_results.py` does not read it.
- Read the percentiles (p95/p99), not the averages.
- Correlate response times with server metrics: CPU, memory, database, pool saturation. Include the throughput actually achieved: at an arrival rate, dropped iterations mean the target was not reached.
- Before blaming the system, rule out the test itself: generator CPU, network, data exhaustion.

## 5. Reporting
- Record the result with `k6_results.py`: `failed` with the breached thresholds and observed values; `passed` only for a complete load, stress, spike or soak run; `not-run` for a smoke run (it proves the script, not the requirement); `blocked` when the run ended early, k6 crashed (`--exit-code`), or a thresholded request had no successful sample.
- Report the profile, duration, achieved load, percentiles per request name, error rate, the environment and its differences from production, and bottlenecks observed (a suspected cause is labelled as suspicion).
- A failed threshold on a requirement is a defect like any other (see the reporting skill).
