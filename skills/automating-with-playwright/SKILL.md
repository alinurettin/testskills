---
name: automating-with-playwright
description: Turns QA Suite test cases into maintainable Playwright TypeScript automation that keeps full traceability. It scaffolds the project (config, fixtures, page objects, auth setup, CI) and generates spec skeletons in which every test keeps its manual TC ID as a tag and its steps as test.step. It then implements them with role-based locators and web-first assertions, and feeds the Playwright results back into the requirements traceability matrix. It also supports Xray result import. Use this whenever someone wants to automate test cases, write Playwright or end-to-end/UI/API tests, turn manual tests into automation, set up a Playwright project or CI, or connect automated results to requirements. Also use it for Turkish requests such as "otomasyon yaz", "Playwright testleri", "test case'leri otomatize et", "e2e test", "regresyonu otomatikleştir".
license: MIT
metadata:
  suite: qa-suite
  version: "0.4.0"
---

# Automating with Playwright

Automation is only as good as the test design behind it, and only as useful as its traceability. This skill keeps both:
- every automated test *is* a manual test case (same `TC-###`, same steps, same expected results), and
- every run flows back into the RTM, so "which requirements are proven by automation, and which fail" is always answerable.

Three rules matter more than any pattern:
1. **Never weaken an expected result to make a test pass.** If the product disagrees with the requirement, the test stays red, or is marked `test.fail` with a defect key, and the defect gets reported.
2. **No false green.** Generated skeletons carry `test.fixme(...)` and report as *not run* until they are really implemented. A test that does not assert the expected outcome is not implemented.
3. **No real credentials.** Use only test accounts, supplied through environment variables or CI secrets.

## Reading plan
- This file covers the workflow.
- Read `references/playwright-patterns.md` before implementing the first test (locators, assertions, data, auth, mocks, clock, known bugs).
- Read `references/manual-to-automation.md` when deciding how a technique maps to code (data-driven, projects, API level).
- Read `references/ci-and-reporting.md` for CI, Xray and the results loop.

## Prerequisites
- Node.js 18+ (`node --version`).
- The application URL for a test environment.
- A test account if login is needed.
- `qa/test-cases.json`, produced by `designing-test-cases`. When it does not exist, design the tests first: automating undesigned tests produces fragile click-scripts with no oracle.
- Installing npm packages and browsers downloads files. **Ask the user** before running `npm install` / `npx playwright install` if they have not already agreed.

## Workflow

```
- [ ] 1. Scope: which TCs (smoke first), which app URL / environment
- [ ] 2. Scaffold the project (once)
- [ ] 3. Generate skeletons from test-cases.json
- [ ] 4. Explore the app and build page objects
- [ ] 5. Implement tests (remove test.fixme only when the steps assert the expected results)
- [ ] 6. Run, stabilise, classify failures (test bug vs product bug)
- [ ] 7. Results → qa/results.json → RTM; automation coverage report
- [ ] 8. CI (and Xray) if requested
```

### 1. Scope
Start with the `@smoke` and critical/high candidates (`automation.candidate: true`). Automating everything in one go produces many half-finished tests; ten solid tests are worth more than sixty skeletons.

### 2. Scaffold (once per repository)
```bash
python scripts/scaffold_project.py --dir automation --project "<product>" --base-url https://test.example.com \
       [--locale tr-TR --timezone Europe/Istanbul] [--repo-root .] [--no-ci]
cd automation && npm install && npx playwright install
```
The script creates `playwright.config.ts` with these defaults:
- reporters: list, html, **json** (for the results loop) and junit
- trace on first retry
- tr-TR locale
- `data-testid`
- setup-project auth
- chromium, firefox and webkit projects

It also creates `tests/fixtures.ts`, `tests/auth.setup.ts`, `pages/BasePage.ts`, `.env.example`, `.gitignore`, and a GitHub Actions workflow at the repository root. Existing files are never overwritten.

### 3. Generate skeletons
```bash
python scripts/generate_specs.py --tests ../qa/test-cases.json --requirements ../qa/requirements.json --out tests [--only TC-001,TC-004]
```
- **Output:** one spec file per requirement. Each test has:
  - title `TC-### …`,
  - tags `@TC-###`, `@REQ-###`, `@<priority>` and the test's own tags,
  - annotations `qa_id`, `requirements` (Jira keys) and `test_key` (when the test case has `ext:`),
  - one `test.step` per manual step, with the data and expected result as comments,
  - the `test.fixme` marker.
- **Data-driven groups:** BVA/EP variants whose steps differ only in values become a `for (const c of casesN)` block, with one test and one TC tag per case.
- **Re-running** only adds tests whose `@TC-###` does not exist yet. Nothing is overwritten.

### 4. Explore and build page objects
- Open the application with `npx playwright codegen <url>` or a browser tool, if one is available.
- Create one page object per page or component in `pages/`, with role-based locators and intent-level actions. Register the page objects as fixtures in `tests/fixtures.ts`.
- If a needed element has no accessible name and no `data-testid`, record it as a testability finding for the developers, and do not fall back to brittle CSS.

### 5. Implement
For each skeleton:
1. Replace `{ page }` with the fixtures you need.
2. Implement the preconditions through API, seed data or mocks where possible.
3. Implement each `test.step` so it **performs the action and asserts the expected result** from the comment.
4. Delete the `test.fixme(...)` line.
5. Keep the title, tags and annotations unchanged.

For data-driven blocks, add structured fields to each case (`basket: "800,00"`) and use them in the loop.

If implementing reveals that a manual test is wrong or ambiguous (for example, the UI copy differs from the draft text in the question log), fix `qa/test-cases.src.md` or log a question. **Do not let code and test cases drift apart.**

### 6. Run and stabilise
```bash
npx playwright test --project=chromium --grep @smoke     # fast loop
npx playwright test                                      # all projects
npx playwright show-report
```
Classify every failure:
- **Test bug** (locator, wait, data): fix the test.
- **Product bug** (the behaviour contradicts the requirement): keep the assertion. Report the defect, add its key to `qa/results.json`, and optionally mark the test with `test.fail(true, 'KEY: summary')`.
- **Flaky** (passes only on retry): fix the root cause. Never raise timeouts blindly.

### 7. Close the loop
```bash
python scripts/pw_results.py test-results/results.json --out ../qa/results.json --run "<label>"
python scripts/check_automation.py --tests ../qa/test-cases.json --specs tests --out ../qa/automation-coverage.md
python <tracing-requirements>/scripts/build_rtm.py --requirements ../qa/requirements.json --tests ../qa/test-cases.json --results ../qa/results.json --out-dir ../qa
```
Report to the user:
- automation coverage: candidates automated, skeletons left, missing;
- the run result per requirement, from the RTM;
- product defects found, with the failing TCs;
- flaky tests;
- remaining testability requests to the developers.

### 8. CI and Xray
See `references/ci-and-reporting.md`. It covers the GitHub Actions workflow (already scaffolded), an Azure DevOps outline, sharding, `--grep @smoke` on pull requests, and the Xray JUnit reporter with `test_key` annotations.

## BDD
If the team wants Gherkin scenarios as the automation entry point, use the `writing-bdd-scenarios` skill. It generates `.feature` files with the same `@TC-###` tags and runs them through playwright-bdd, using the same page objects.

## Files
- `scripts/scaffold_project.py`: project skeleton from `assets/template/`; never overwrites.
- `scripts/generate_specs.py`: test-cases.json → traceable spec skeletons, idempotent, data-driven groups.
- `scripts/check_automation.py`: static automation coverage (automated, skeleton, missing, orphan, duplicate); `--strict` for CI.
- `scripts/pw_results.py`: Playwright JSON report → `qa/results.json` (per TC, across projects, flaky, fixme).
- `assets/template/`: `playwright.config.ts`, `package.json`, `tsconfig.json`, fixtures, auth setup, `BasePage`, CI workflow, `.env.example`, `.gitignore`.
- `references/playwright-patterns.md`, `references/manual-to-automation.md`, `references/ci-and-reporting.md`.
