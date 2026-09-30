---
name: tracing-requirements
description: Builds a requirements traceability matrix (RTM) from QA artifacts, measures coverage, reports risk-ordered gaps (uncovered, no negatives, orphans) and change impact, and does risk-based regression selection within a time budget. Use when someone asks about coverage or what to re-test. Triggers include RTM, test coverage, traceability, change impact, regression selection; Turkish "izlenebilirlik matrisi", "test kapsamı", "regresyon seçimi".
license: MIT
metadata:
  suite: qa-suite
  version: "0.7.0"
---

# Tracing requirements

Traceability answers three questions every QA lead gets asked:
- *Is every requirement tested?* (coverage)
- *Why does this test exist?* (justification)
- *What do we re-test if this changes?* (impact)

The RTM is only trustworthy if it is **generated from the artifacts**, not maintained by hand. So this skill runs a script over `requirements.json`, `test-cases.json` and, optionally, `results.json`.

## Inputs

- `qa/requirements.json` and `qa/test-cases.json` (schema in `references/data-model.md`)
- Optional `qa/results.json`: execution results and defect keys per test, entered by hand or converted from automated test reports (see "Automated results" below)

If the user only has a spreadsheet or a list, convert it into these files first. If the links between tests and requirements are missing, propose them and let the user confirm. Never invent links silently.

## Workflow

1. **Generate:**
   ```bash
   python scripts/build_rtm.py --requirements qa/requirements.json --tests qa/test-cases.json \
       [--results qa/results.json] --out-dir qa [--changed REQ-003,REQ-007] [--json] [--strict]
   ```
   This writes:
   - `qa/rtm.md`: summary, validation, gap report, requirement → test, test → requirement, change impact.
   - `qa/rtm.csv`: UTF-8 with BOM, so Excel opens it directly.

   Exit code 1 means validation errors. With `--strict`, it also means gaps exist, which is useful as a CI quality gate.

2. **Fix validation errors first.** Duplicate IDs, broken links, and missing steps or expected results make every metric unreliable.

3. **Work the gap report in risk order:**

   | Gap | Meaning | Usual action |
   |---|---|---|
   | UNCOVERED | no active test | Design tests (`designing-test-cases`), or record a justified exclusion |
   | NO_NEGATIVE | a functional rule has only positive tests | Add invalid-input, forbidden-action and error-path tests |
   | THIN | high or critical risk covered by one test | Add boundary, decision-table and state tests according to risk depth |
   | UNCONFIRMED | a derived requirement is still unconfirmed | Get stakeholder confirmation, or drop it |
   | OPEN_QUESTIONS | tested on assumptions | Chase the answers. Revisit the tests once they arrive. |
   | FAILED | a linked test failed | Check the defect link. The requirement is not satisfied. |
   | ORPHAN | a test has no requirement | Link it, tag it `exploratory`, or deprecate it |
   | DUPLICATE | identical preconditions, steps and data | Keep one, deprecate the rest, and union their links |

   Non-functional, constraint and compliance requirements are exempt from NO_NEGATIVE.

   The **Calibration** section of the report adds two checks on the suite itself:

   | Item | Meaning | Usual action |
   |---|---|---|
   | PRIORITY_SKEW | More than 20% of tests are critical, or more than 60% are critical+high | Re-rate each test by its own impact. Only go/no-go checks are critical; variants go one level lower. |
   | REDUNDANT | Three or more tests (five or more for BVA) share requirement, polarity, technique and outcome pattern | Keep one representative per partition plus the boundary values, or state the distinct risk each extra test targets. Tests tagged `generated` (one per schema constraint) and pairwise rows are exempt. |

4. **Change impact.** When a requirement changes, run with `--changed REQ-xxx`. List the affected tests, update them (never renumber), and mark obsolete ones `deprecated`.

5. **Regression selection.** For a release, a hotfix or a change, select what to run instead of "everything" or "whatever fits":
   ```bash
   python scripts/select_regression.py --requirements qa/requirements.json --tests qa/test-cases.json        --results qa/results.json --changed REQ-003,REQ-007 [--areas coupon] [--budget 40 | --budget-minutes 120]        [--level must|should|could] --lang tr --out qa/regression.md [--json qa/regression.json]
   ```
   The tiers follow impact analysis first and risk second:
   - **must:** tests linked to changed requirements or their parent/child requirements, tests that failed or were blocked last time (confirmation testing), and critical/high smoke tests.
   - **should:** the same functional area (shared tags), high risk (L × I ≥ 12), and flaky tests.
   - **could:** everything else, ordered by risk.

   With a budget, the set is filled tier by tier. The tests that are left out are listed as **residual risk**, so the cut is a decision someone can sign off, not an accident. The report ends with a `npx playwright test --grep "@TC-…"` command for the automated tests and a list of the manual ones. Ask for the changed requirements if the user describes the change only in words. Map the description to REQ IDs and confirm the mapping.

6. **Report to the user:**
   - Coverage % (covered in-scope requirements divided by all in-scope requirements).
   - The number of functional requirements with negative tests.
   - The top gaps by risk.
   - The execution status, when results are available.
   - A clear statement of the limits. Coverage here is **requirements coverage**. It says nothing about code coverage, or about requirements nobody wrote down; the analysis step targets those.

## Automated results

Automated tests reach the RTM through their TC IDs. Read `references/test-framework-results.md` for the recipe per framework (JUnit 5 with Selenium or REST Assured, TestNG, pytest, Cypress, Karate, Postman/Newman, Robot Framework, SpecFlow/Reqnroll): how to put the ID where the report keeps it, and how to make the runner write JUnit XML.

1. Check that the automated tests carry TC IDs **in their names**. Most JUnit XML writers drop tags, groups and categories, so a tag alone is not enough.
2. Convert the reports. Files, folders and quoted globs work, once per environment:
   ```bash
   python scripts/junit_results.py "target/surefire-reports/TEST-*.xml" --source ci --project api --out qa/results.json
   python scripts/junit_results.py reports/junit --source ci --project chrome --out qa/results.json [--retries]
   ```
   The script reads JUnit XML from Maven Surefire/Failsafe, Gradle, TestNG, pytest, Cypress, Newman, Karate, Robot Framework (`--xunit`, or `output.xml` for `[Tags]`) and .NET. A TC is failed if any of its tests failed, in any environment. Reruns that passed are marked `flaky`. Manual results and defect keys already in the file are kept. Tests without a TC ID are listed as untraceable: report that number to the user.
3. Run `build_rtm.py` with `--results qa/results.json`. An `unknown test` warning means an automated test carries an ID that is not in `test-cases.json`.

Playwright uses `pw_results.py` from the automating-with-playwright skill instead.

## Notes

- `deferred` and `deprecated` requirements are listed but excluded from the coverage denominator.
- Deprecated tests are excluded from coverage and from duplicate checks.
- When no L×I risk score exists, the risk level falls back to priority.
- Execution roll-up per requirement:
  - `failed` if any linked test failed.
  - Otherwise `blocked` if any is blocked.
  - `passed` only if all linked tests passed.
  - Otherwise `not-run` or `in-progress`.

## Files

- `scripts/build_rtm.py`: validation, RTM, gap report, change impact. Outputs md, csv and optionally json. Standard library only.
- `scripts/select_regression.py`: risk-based regression selection (must/should/could tiers with reasons), time or count budget with residual risk, Playwright `--grep` command.
- `scripts/junit_results.py`: JUnit XML from any framework (and Robot Framework `output.xml`) → `qa/results.json` by TC ID, per environment, with flaky reruns.
- `references/test-framework-results.md`: tagging tests with TC IDs and producing JUnit XML per framework, converter options, troubleshooting.
- `references/data-model.md`: shared JSON schema.
