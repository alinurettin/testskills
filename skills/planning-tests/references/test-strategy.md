# Test strategy guide

## Contents
1. Plan vs strategy (ISO/IEC/IEEE 29119-3)
2. Choosing levels and types
3. Entry, exit, suspension criteria that can be checked
4. Estimation
5. Environments and test data
6. Common plan defects

---

## 1. Plan vs strategy
- **Organisational test strategy**: stable rules for all projects (tools, standards, defect workflow). Write it once. A project plan references it rather than repeating it.
- **Test plan**: one project or release. Under ISO/IEC/IEEE 29119-3 it covers context, scope, risks, the test approach (which includes the strategy for this project), roles, schedule, environments, entry/exit criteria, deliverables and communication.
- Keep plans **short and specific**. A plan that could be pasted into any project unchanged is not a plan. Every section should cite something concrete from this release: requirement IDs, risks, environments, dates.

## 2. Choosing levels and types
| Situation | Emphasis |
|---|---|
| New business rules, calculations | System-level functional tests with full technique depth; unit tests by the developers for the rule engine |
| Many integrations | Contract/API tests (the API level is cheaper than the UI); integration environment with stubs for the third parties |
| UI-heavy, many browsers or devices | Pairwise environment matrix; visual and accessibility checks; a small end-to-end smoke set per browser |
| Regulated domain (finance, health, public) | Traceability evidence (RTM), audit trail tests, security (ASVS L2/L3), accessibility (legal duty), retention and privacy |
| High load or peak events | Performance tests with explicit thresholds from the requirements; run them early on a production-like environment |
| Frequent releases | Automation of smoke and critical regression; a risk-based regression selection via RTM impact analysis |

Use the test pyramid as a guide, not a law. For frontend-heavy products, the testing trophy puts more weight on integration tests; for microservices, the honeycomb puts more weight on contract and integration tests. Say which model the plan follows, and why.

## 3. Entry, exit and suspension criteria that can be checked
- Every criterion must be **measurable from the artifacts**. `qa/exit-criteria.json` is evaluated automatically by `reporting-test-results/scripts/completion_report.py`.
- Typical values:
  - requirement coverage 100%
  - execution ≥ 95%
  - pass rate ≥ 95%
  - 0 open critical and 0 open high defects
  - all critical-risk requirements passed
  - 0 blocking questions open
- Make the criteria risk-based. A payment release may demand 100% of critical tests passed; an internal tool may accept known medium defects with workarounds.
- Suspension criteria, e.g. suspend testing when:
  - the smoke tests fail,
  - the environment is unavailable for more than 2 hours,
  - more than 30% of the planned tests are blocked,
  - a critical defect blocks the main flow.

  Resume after a new build passes the smoke tests.

## 4. Estimation
- Start from the facts: `scripts/plan_facts.py` gives the number of tests, the number of steps, and a transparent heuristic in minutes per step and per test.
- Add to the execution time:
  - retests and regression (cycles),
  - defect reporting and verification (often 20–30% of execution time),
  - environment and data preparation,
  - automation implementation (for a UI test, often 1–3 hours each, less for API tests),
  - a buffer for known unknowns, such as open blocking questions.
- State the estimate **as a range, with its assumptions**. Calibrate it with the team's history after each release.

## 5. Environments and test data
- List every environment (dev, test, staging, pre-prod) and what runs where. Name the differences from production that matter: data volume, third parties mocked or real, feature flags.
- The pairwise environment matrix (browsers, operating systems, devices) comes from the design specs. Reference it, and do not invent a new one.
- Test data:
  - Ownership: who creates it, and who resets it.
  - Privacy: no production personal data unless anonymised (KVKK/GDPR).
  - Special data: test cards, test accounts per role, clock control for time-based rules.
- Testability needs belong in the plan as **dependencies with owners**: stubs, seed APIs, `data-testid` attributes, logs.

## 6. Common plan defects
- Copy-paste boilerplate with no project facts in it.
- Exit criteria like "all tests pass" or "quality is acceptable". These are neither measurable nor realistic.
- No risk section, or risks with no mitigation through testing.
- Effort given without a method.
- Environments and data treated as "available" when nobody owns them.
- Automation promised with no scope and no maintenance owner.
