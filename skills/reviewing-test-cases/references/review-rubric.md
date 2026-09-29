# Test review rubric (the judgement half)

`review_tests.py` checks *how* tests are written. This rubric covers what a script cannot judge: *whether they test the right things, correctly, deeply enough*. Score each dimension 0–2 per requirement or feature. Report the score together with its evidence.

## Contents
1. Dimensions
2. How to sample
3. Typical findings and fixes
4. Report structure

---

## 1. Dimensions
| # | Dimension | 0 (poor) | 1 (partial) | 2 (good) |
|---|---|---|---|---|
| D1 | **Oracle correctness**: do the expected results match the requirement? | Contradicts the requirement, or invents behaviour | Matches, but one-sided (only the message, not the state or amount) | Matches the requirement verbatim: values, messages, state and side effects |
| D2 | **Technique adequacy**: are partitions, boundaries, rules and states systematically covered? | Happy path only | Some boundaries or negatives, chosen ad hoc | Techniques visible (EP/BVA, decision table, state, pairwise) at a depth that matches risk |
| D3 | **Negative and error coverage** | None | Obvious invalid inputs only | Invalid inputs, forbidden actions, error paths, concurrency and permissions |
| D4 | **Risk proportionality**: is depth focused where impact and likelihood are high? | Uniform or random | Partly | Critical areas deep, low-risk areas light; priorities calibrated |
| D5 | **Traceability**: does each test link to a requirement, and is each requirement covered? | Links missing | Links exist, but there are gaps or orphans | Bidirectional; gaps justified |
| D6 | **Executability**: can someone else run the test without asking questions? | Vague steps or missing data | Mostly runnable | Concrete data, preconditions, observable results; independent tests |
| D7 | **Maintainability**: duplication, size, reuse | Heavy duplication; very long tests | Some redundancy | Atomic tests, shared setup separated, data-driven where values vary |
| D8 | **Automation readiness** | No candidates marked; oracles not deterministic | Partly | Candidates marked with reasons; stable oracles; testability needs listed |

## 2. How to sample
- Small suites (fewer than 50 tests): review all of them.
- Larger suites:
  - review every critical- and high-risk requirement fully;
  - take a random sample of about 20% of the rest, stratified by feature;
  - add every test that `review_tests.py` scored below 70.
- Always read the requirement first, then its tests. Oracle errors are only visible against the requirement.

## 3. Typical findings and fixes
| Finding | Fix |
|---|---|
| "Should work", "Başarılı olmalı" | Write the observable result: message text, amount, status change, record created |
| One giant test covering a whole journey | Split it into atomic tests; keep a single end-to-end scenario test if needed |
| Boundary tested only on one side | Add the value just outside the range (2-value BVA), and both neighbours for critical risk (3-value) |
| Many tests from one equivalence class | Keep one representative per partition, plus the boundaries |
| No permission tests | Add CRUD × role tests, including direct URL/API access |
| Test depends on another test's data | Make the precondition explicit and create the data in setup |
| Missing requirement links | Link to the REQ; if none exists, the test reveals a missing requirement, so raise a question |
| Everything "critical" | Re-rate each test by its own impact (see the priority rules in `designing-test-cases`) |

## 4. Report structure
1. **Scope:** which suite, how many tests, the sampling method.
2. **Automated findings:** the `review_tests.py` summary.
3. **Rubric scores per area,** with 1–2 lines of evidence each.
4. **Top 5 improvements**, ordered by risk reduction per effort.
5. **Concrete rewrites** for 3–5 representative tests (before/after).
6. **Missing tests:** requirements or conditions with no test, found by the review. Hand these to `designing-test-cases`.
