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
| "responds within 800 ms for 95% of requests" | `http_req_duration{name:X}: ['p(95)<800']` |
| "error rate below 1%" | `http_req_failed: ['rate<0.01']` |
| "all responses correct" | `checks: ['rate>0.99']`, plus a `check` on the status code and key body fields |
| "200 concurrent users" | `target: {type: vus, vus: 200}` (closed model) |
| "50 requests/second at peak" | `target: {type: arrival-rate, rate: 50}` (open model, preferred for APIs) |

If the requirement has no numbers, **do not invent them silently.** Raise a question (the analysis linter's UNMEASURED finding). You may propose defaults such as Core Web Vitals, or p95 ≤ 1 s for interactive APIs, marked as assumptions.

## 2. Choosing the load profile
| Profile | Question it answers | Shape |
|---|---|---|
| smoke | Does the script work? Is the system alive under minimal load? | 1–2 VUs, 1 min. Run it first, every time. |
| load | Do we meet the requirement at expected peak? | Ramp to target, hold for 10–30 min, ramp down |
| stress | Where does it break, and how does it degrade? | Steps from 50% to 200% of the target |
| spike | Does it survive a sudden surge, such as a campaign start, and recover? | Short jump to 5× the target, then back |
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
k6 run --summary-export=perf/DS-010-summary.json ...                  # keep the numbers for the report
```
- Read the percentiles (p95/p99), not the averages.
- Correlate response times with server metrics: CPU, memory, database, pool saturation. Include the throughput actually achieved: at an arrival rate, dropped iterations mean the target was not reached.
- Before blaming the system, rule out the test itself: generator CPU, network, data exhaustion.

## 5. Reporting
- Record the result for the performance test case in `qa/results.json`: `passed` when k6 exited with 0, `failed` with the breached thresholds noted when it exited with 99.
- Report the profile, duration, achieved load, percentiles per request name, error rate, the environment and its differences from production, and bottlenecks observed (a suspected cause is labelled as suspicion).
- A failed threshold on a requirement is a defect like any other (see the reporting skill).
