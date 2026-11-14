# CI, reporting and the results loop

## Contents
1. The results loop (Playwright → QA Suite RTM)
2. Xray results import
3. CI pipelines
4. Playwright Test Agents and AI helpers
5. Flaky-test policy

---

## 1. The results loop
```bash
npx playwright test                                   # writes test-results/results.json (json reporter)
python scripts/pw_results.py test-results/results.json --out ../qa/results.json --run "Sprint 14 RC2"
python scripts/check_automation.py --tests ../qa/test-cases.json --specs tests --out ../qa/automation-coverage.md
python ../../tracing-requirements/scripts/build_rtm.py --requirements ../qa/requirements.json \
    --tests ../qa/test-cases.json --results ../qa/results.json --out-dir ../qa
```
Adjust the paths to where the skills are installed.

- `pw_results.py` maps every Playwright test to a TC through its tags. The JSON report lists the tags **without** `@`, for example `TC-001`.
- It aggregates the browser projects: a TC fails if it failed in any project.
- It keeps manual results and defect keys that are already in `results.json`.
- Skeletons that still have `test.fixme` become `not-run` with the note "not implemented". They never count as passed.
- The RTM then shows the execution status for each requirement: failed if any linked test failed, passed only if all passed.

## 2. Xray results import
- Install `@xray-app/playwright-junit-reporter` (`npm i -D`) and enable it in `playwright.config.ts`: `['@xray-app/playwright-junit-reporter', { outputFile: 'test-results/xray-junit.xml', embedAnnotationsAsProperties: true }]`.
- Tests carry a `test_key` annotation with the Xray test issue key. `generate_specs.py` adds it when the test case has `ext:` / `external_id`. The `requirements` annotation holds only the requirement Jira keys (it is omitted when no requirement has an `external_id`, since Xray cannot resolve internal IDs); `qa_requirements` carries the REQ IDs for the RTM.
- Import the XML with Xray's JUnit import, from the UI or its REST API, into a Test Execution. Tests without `test_key` are matched or created by name, which can create duplicates. Set `ignoreTestCasesWithoutTestKey: true` once all tests have keys.
- Zephyr Scale and other tools accept standard JUnit (`test-results/junit.xml`). Map by test name, which starts with `TC-###`.

## 3. CI pipelines
- **GitHub Actions:** `scaffold_project.py` writes `.github/workflows/playwright.yml` at the repository root. It installs the browsers, runs the tests with an optional `--grep`, and uploads the report and results as artifacts. Set `BASE_URL` as a repository variable and `TEST_USER` / `TEST_PASSWORD` as secrets.
- **Azure DevOps (outline):**
  - a `NodeTool@0` task (Node 22)
  - `npm ci`
  - `npx playwright install --with-deps`
  - `npx playwright test`
  - `PublishTestResults@2` with `test-results/junit.xml`
  - `PublishPipelineArtifact` for `playwright-report`
- **Speed:** use `--shard=1/4` in a matrix for large suites. Run `@smoke` on every pull request and the full regression suite nightly.
- **Quality gate:** `check_automation.py --strict` fails if automation candidates are missing, skeletons remain or a tagged test contains no assertion. Use it on the release branch, not on every pull request.

## 4. Playwright Test Agents and AI helpers
- Since Playwright 1.56, `npx playwright init-agents --loop=claude` (or `vscode`, `codex`, `opencode`) installs three agents:
  - the **planner** explores the running application and writes a plan,
  - the **generator** turns a plan into tests,
  - the **healer** replays failing tests and repairs locators and waits.
- **How they fit QA Suite:**
  - **Our test cases are the plan.** They come from analysed requirements, not from UI exploration, so do not replace them with the planner's output. Use the planner only to discover flows the requirements missed, and feed those back as questions.
  - The **healer** is useful for broken locators after UI changes. **Review its diffs.** Never accept a "heal" that changes an expected result or weakens an assertion. That is a product bug, not a test bug (see `playwright-patterns.md` section 11).
- The Playwright MCP server and `playwright-cli` let an assistant drive a real browser to find locators while implementing skeletons.

## 5. Flaky-test policy
A flaky test gives different results on the same code. It destroys trust in the suite faster than a missing test, so treat it as a defect with an owner (CTAL-TAE v2.0, chapter 7).

**Find the cause before touching the test.** Check in this order:
1. **Product:** race conditions, non-idempotent requests, caching, time-dependent logic. This is a product defect: report it, do not hide it with a retry.
2. **Test:** fixed sleeps, shared state between tests, order dependence, selectors tied to layout, data created by another test, assertions on animations.
3. **Environment:** slow or shared test environment, third-party services, parallel runs colliding on the same account or record, clock and time zone.

**Rules:**
- Retries exist to *detect* flakiness (`retries: 2` in CI, trace on first retry). A test that passes only on retry is reported as flaky in `qa/results.json`, never as plainly passed. In CI, `failOnFlakyTests: true` makes that visible on the release branch.
- **Quarantine** only with a ticket, an owner and an expiry date (two weeks at most): tag the test `@quarantine`, run quarantined tests in a separate non-blocking job, and delete the tag or the test when the date passes. A quarantined test covers nothing: its requirement shows as not verified in the RTM until it is back.
- A skipped, `fixme` or auto-healed test is **not passed**. If an AI healer changes a locator or an expected value, a person reviews the diff: an expectation changed to match the application may be hiding a product defect.
- Track the flaky rate (flaky runs ÷ runs per test over the last 20 runs) and fix the worst first. `check_automation.py` flags the common test-side causes (fixed sleeps, `force: true`, raw selectors).

