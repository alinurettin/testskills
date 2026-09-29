# From manual test design to automation

The manual suite already contains the thinking: the partitions, boundaries, rules, transitions and combinations. Automation should **preserve that structure**, not flatten it into ad-hoc scripts.

## Contents
1. What to automate (and what not)
2. Technique → automation shape
3. Pairwise environments → Playwright projects
4. Keeping the trace intact

---

## 1. What to automate (and what not)
Automate tests with `automation.candidate: true`, in this order:
1. `@smoke` tests. They give the fastest feedback in CI.
2. Critical and high tests with deterministic oracles: calculations, rules, boundaries.
3. Server-side negative tests, at API level.
4. Regression tests for areas that change often.

Keep these manual, or leave them to other tools:
- **Exploratory charters** (never automated; the generator skips them).
- **Pure UX judgement**: layout aesthetics, wording tone.
- **Performance tests.** They need load tools such as k6, JMeter or Gatling; Playwright is not a load tool. You may add a single-user response-time smoke check.
- **Tests needing physical devices or manual third-party steps**, e.g. real 3-D Secure SMS codes. Use the provider's test mode and mocks instead.

## 2. Technique → automation shape

| Manual technique | Automation shape |
|---|---|
| EP / BVA | **Data-driven** block: one test per value, keeping each value's TC ID. `generate_specs.py` groups these automatically. Add structured fields (amount, expected discount) to each case. |
| Decision table | Data-driven over the columns: the conditions become fixture/setup inputs, the actions become assertions. Put conditions that are expensive to set up in the UI (card origin, campaign flag) into API setup or mocks. |
| State transition | One test per sequence (S-01 …), with a `test.step` per transition. **Reach the start state through API or seed data**, not by clicking through earlier states. Invalid transitions become API tests that expect rejection and **no state change**. |
| Pairwise (application parameters: payment method, language, user type) | Data-driven block over the pairwise rows. |
| Pairwise (browser / OS / device) | **Playwright projects** (see section 3), not per-test parameters. |
| Use case / scenario | One end-to-end test per flow with steps. Keep these few, because they are slow; push details down to smaller tests. |
| CRUD × role | One storage state per role; data-driven over the operations. Test forbidden operations at API level too (direct request, a changed ID). |
| Error guessing | Network and third-party failures → `page.route` mocks. Input probes (Unicode, injection strings) → data-driven. Double submit → `Promise.all([click(), click()])`, then assert a single order. Clock edges → `page.clock`. |

## 3. Pairwise environments → Playwright projects
Browsers and devices are an execution dimension, not test logic:
- Define one Playwright project per browser/device value that appears in the pairwise rows, for example `chromium`, `firefox`, `webkit`, `mobile-chrome` and `mobile-safari` in `playwright.config.ts`.
- Run the **functional smoke subset** in every project: `--grep @smoke`. Run the full suite in one reference browser.
- An OS such as Windows or macOS depends on the CI runner. Use a runner matrix only when the pairwise design really requires a specific OS; otherwise document the approximation.
- Keep the pairwise TC IDs traceable. Tag the smoke tests that run in each project, and note the mapping in `automation/README.md`. Alternatively, keep the environment rows as data-driven tests that select a project with `test.skip(testInfo.project.name !== c.project)`.

## 4. Keeping the trace intact
- **Never** rename, merge or drop the `@TC-###` tag of a generated test. Split a manual test into several automated tests only if every part keeps the same `@TC-###` tag. The results roll up per TC.
- A test found to be wrong during automation (wrong expected result, missing precondition) must be fixed in `qa/test-cases.src.md` first. Then regenerate the JSON and adjust the spec. The manual and automated versions must not drift apart.
- Once an Xray test key is known (after import), put it in the test case's `ext:` field. Regenerated skeletons then carry the `test_key` annotation. For tests that already exist, add `{ type: 'test_key', description: 'SHOP-201' }` by hand.
