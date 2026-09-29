---
name: tracing-requirements
description: Builds and maintains a bidirectional Requirements Traceability Matrix (RTM) linking requirements to test cases, execution results and defects. It validates the QA artifacts (IDs, required fields, broken links), measures coverage, and produces a risk-ordered gap report covering uncovered requirements, missing negative tests, thinly covered high-risk items, orphan and duplicate tests, unconfirmed derived requirements and failed tests. It also answers change-impact questions. Use this whenever the user asks about test coverage, traceability, an RTM or "izlenebilirlik matrisi", which requirements are untested, what to re-test after a requirement changed, release readiness from a coverage view, or wants to check a test suite for gaps, duplicates or orphans. Use it after designing test cases, before exporting them, and whenever execution results arrive.
license: MIT
metadata:
  suite: qa-suite
  version: "0.4.0"
---

# Tracing requirements

Traceability answers three questions every QA lead gets asked:
- *Is every requirement tested?* (coverage)
- *Why does this test exist?* (justification)
- *What do we re-test if this changes?* (impact)

The RTM is only trustworthy if it is **generated from the artifacts**, not maintained by hand. So this skill runs a script over `requirements.json`, `test-cases.json` and, optionally, `results.json`.

## Inputs

- `qa/requirements.json` and `qa/test-cases.json` (schema in `references/data-model.md`)
- Optional `qa/results.json`: execution results and defect keys per test

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
   | REDUNDANT | Three or more tests (five or more for BVA) share requirement, polarity, technique and outcome pattern | Keep one representative per partition plus the boundary values, or state the distinct risk each extra test targets |

4. **Change impact.** When a requirement changes, run with `--changed REQ-xxx`. List the affected tests, update them (never renumber), and mark obsolete ones `deprecated`.

5. **Report to the user:**
   - Coverage % (covered in-scope requirements divided by all in-scope requirements).
   - The number of functional requirements with negative tests.
   - The top gaps by risk.
   - The execution status, when results are available.
   - A clear statement of the limits. Coverage here is **requirements coverage**. It says nothing about code coverage, or about requirements nobody wrote down; the analysis step targets those.

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
- `references/data-model.md`: shared JSON schema.
