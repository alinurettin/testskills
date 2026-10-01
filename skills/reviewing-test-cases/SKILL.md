---
name: reviewing-test-cases
description: Reviews an existing test suite written by people or AI. Imports Excel (.xlsx) or tool CSV exports, flags vague or missing expected results, missing data, multi-action steps and unlinked tests, and applies a rubric for oracles, depth and risk coverage. Use when test cases need a quality audit. Triggers include review test cases, test case quality, Excel test import; Turkish "test case'leri incele", "bu testler yeterli mi".
license: MIT
metadata:
  suite: qa-suite
  version: "0.7.1"
---

# Reviewing test cases

A test review answers two questions:
- **Can someone run these tests and get an unambiguous verdict?** This is about writing quality, and it is mostly mechanical.
- **Do these tests prove the requirements, deeply enough where it matters?** This needs judgement against the requirements.

The script handles the first question; the rubric structures the second.

## Language
Write the review in the user's language (TR/EN). The script detects Turkish and English patterns in the tests themselves.

## Reading plan
- This file covers the workflow.
- Read `references/review-rubric.md` for the judgement dimensions, sampling, typical fixes and report structure.

## Workflow

```
- [ ] 1. Get the suite into QA Suite format (import if needed)
- [ ] 2. Run the automated checks
- [ ] 3. Judge with the rubric (against the requirements)
- [ ] 4. Report: findings, top fixes, rewrites, missing tests
```

### 1. Get the suite into QA Suite format
- If it is already `qa/test-cases.json`, use it directly.
- If it is an Excel workbook (`.xlsx`) or a CSV export (TestRail, Xray, Zephyr, Qase, or Excel saved as CSV), import it directly. No conversion is needed for `.xlsx`:
  ```bash
  python scripts/import_tests.py suite.xlsx --list-sheets
  python scripts/import_tests.py suite.xlsx --out qa/test-cases.src.md --lang tr [--sheet "Test Case'ler" | --sheet 2 | --sheet all] [--map title=Summary,steps=Action,expected=Result]
  python scripts/import_tests.py suite.csv --out qa/test-cases.src.md --lang tr [--delimiter ";"]
  python scripts/qa_compact.py tc qa/test-cases.src.md --out qa/test-cases.json --lenient
  ```
  The importer does four things:
  - It finds the header row even below title rows, and detects the columns by TR/EN name (`Adımlar`, `ADIMLAR` and `Adimlar` all match). It detects both layouts: numbered steps in one cell, or one row per step (ID repeated, left empty or merged over the step rows).
  - It reads the workbook with the standard library: several sheets (by default the first sheet with a test header; `--sheet all` imports every such sheet and tags each test with its sheet name), merged cells, multi-line cells, and dates stored as numbers (written as `2026-03-01`).
  - It keeps the IDs when they are all unique `TC-###`; otherwise it numbers from `--start` and keeps the original ID as a `src-…` tag.
  - It fills safe defaults where no column says otherwise: priority mapped, polarity guessed, technique `rb`, status `draft`, and `UNLINKED` when there is no requirement column.

  `--lenient` lets steps without an expected result through, so that the review can report them. Legacy `.xls` and password-protected workbooks cannot be read: ask the user to save them as `.xlsx`. If the columns are not found, run `--list-sheets` and pass `--map`.
- If the tests are in another form, such as a document or a pasted table, transcribe them into the compact format first.
- If requirements exist (a story, SRS or `qa/requirements.json`), get them. Without them, only writing quality can be reviewed. Say so.

### 2. Automated checks
```bash
python scripts/review_tests.py --tests qa/test-cases.json [--requirements qa/requirements.json] --out qa/review-report.md
```
The script produces:
- a per-test score out of 100, with findings: MISSING_EXPECTED, VAGUE_EXPECTED, NO_DATA, DEPENDENT, NO_REQ, MULTI_ACTION, TOO_MANY_STEPS, WEAK_TITLE, NO_PRIORITY, EXPECTED_ECHO;
- at suite level: duplicate titles, requirements without negative tests, and the priority distribution.

Exit code 1 means critical findings exist. Treat the findings as candidates: confirm or dismiss them in context.

If requirement links exist, also run `tracing-requirements` for the coverage gaps, PRIORITY_SKEW and REDUNDANT groups.

### 3. Judge with the rubric
Follow the sampling rule in `references/review-rubric.md`. Read each requirement, then its tests, and score D1–D8 with evidence. The most valuable findings are the ones the script cannot see:
- wrong oracles (expected results that contradict the requirement),
- missing boundaries or negative cases,
- untested rules or states,
- depth that is not proportional to risk.

If the requirements themselves are ambiguous, say so. That is an analysis finding (`analyzing-requirements`), not a test defect.

### 4. Report
Write `qa/review-report.md`: the automated summary plus the rubric sections, following the report structure in the rubric reference. In chat, give:
- the overall verdict,
- the top 5 fixes by risk reduction,
- 3 before/after rewrites,
- the list of missing tests.

Offer to apply the fixes. Edit `qa/test-cases.src.md`, keeping the IDs, and hand the missing tests to `designing-test-cases`.

## Files
- `scripts/import_tests.py`: Excel `.xlsx` (read directly, several sheets, merged cells, dates) and CSV (TestRail, Xray, Zephyr, Qase exports) → compact format, with header-row detection, TR/EN column aliases and both layouts.
- `scripts/review_tests.py`: deterministic writing-quality checks (TR/EN), scores, suite observations. Output is Markdown or JSON.
- `scripts/qa_compact.py`: compact ⇄ JSON (`--lenient` for imports).
- `references/review-rubric.md`: judgement dimensions D1–D8, sampling, typical fixes, report structure.
