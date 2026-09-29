---
name: reviewing-test-cases
description: Reviews an existing test-case suite, whether written by the team, by AI, or imported from Excel, TestRail, Xray or Zephyr CSV. An importer maps TR/EN column names and both row layouts into QA Suite format. A deterministic checker flags missing or vague expected results, missing test data, test dependencies, multi-action steps, missing requirement links, weak titles and priority skew. A rubric covers what scripts cannot judge (oracle correctness, technique depth, negative and risk coverage, traceability, executability), and the review ends with prioritised fixes and rewrites. Use this whenever someone asks to review, audit, assess, clean up or improve test cases or a test suite, including Turkish requests such as "test case'leri incele", "test setimizi değerlendir", "Excel'deki testleri kontrol et", "test kalitesi", "bu testler yeterli mi".
license: MIT
metadata:
  suite: qa-suite
  version: "0.4.0"
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
- If it is a CSV export (from Excel, save as "CSV UTF-8"):
  ```bash
  python scripts/import_tests.py suite.csv --out qa/test-cases.src.md --lang tr [--delimiter ";"] [--map title=Summary,steps=Action,expected=Result]
  python scripts/qa_compact.py tc qa/test-cases.src.md --out qa/test-cases.json --lenient
  ```
  The importer does three things:
  - It detects the columns by TR/EN name, and detects both layouts: numbered steps in one cell, or one row per step sharing an ID.
  - It keeps the original ID as a `src-…` tag.
  - It fills safe defaults: priority mapped, polarity guessed, technique `rb`, and `UNLINKED` when there is no requirement column.

  `--lenient` lets steps without an expected result through, so that the review can report them.
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
- `scripts/import_tests.py`: CSV (Excel, TestRail, Xray, Zephyr exports) → compact format, with TR/EN column aliases and both layouts.
- `scripts/review_tests.py`: deterministic writing-quality checks (TR/EN), scores, suite observations. Output is Markdown or JSON.
- `scripts/qa_compact.py`: compact ⇄ JSON (`--lenient` for imports).
- `references/review-rubric.md`: judgement dimensions D1–D8, sampling, typical fixes, report structure.
