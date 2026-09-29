---
name: reporting-test-results
description: Produces professional test reporting from QA Suite artifacts. It writes clear, reproducible defect reports (ISTQB fields, severity vs priority, automation evidence) and generates test status and test completion reports that compute coverage, execution, pass rate, per-requirement verdicts by risk, open defects by severity and residual risks. It evaluates the plan's exit criteria automatically as met, not met or unknown. Use this whenever someone asks for a bug or defect report, a test summary, status or completion report, release readiness, "can we release", exit criteria evaluation, or a QA sign-off, including Turkish requests such as "hata raporu yaz", "bug kaydı", "test özet raporu", "test tamamlama raporu", "yayına hazır mıyız", "çıkış kriterleri sağlandı mı".
license: MIT
metadata:
  suite: qa-suite
  version: "0.4.0"
---

# Reporting test results

Reports turn test activity into decisions. Two things make a report trustworthy:
- **computed numbers.** Coverage, execution and exit criteria come from the artifacts, never from memory.
- **honest verdicts.** Unknown stays unknown, a skeleton is not a pass, and an open defect with a `test.fail` mark is still a failure.

The release decision belongs to the stakeholders. The report gives them the facts and the residual risks.

## Language
Write in the user's language (TR/EN). Defect titles and steps follow the same language as the test cases.

## Reading plan
- **Defect reports:** read `references/defect-reporting.md` (fields, severity vs priority, writing rules, evidence, product bug vs test bug).
- **Status or completion reports:** this file and the script are enough.

## A. Defect reports
1. **Start from the failing test case.** Use its preconditions, steps, data and expected result, and the REQ it proves.
2. **Confirm that it is a product bug**, using section 6 of the reference. Check that the failure is stable, that the precondition was met, and that the expectation matches the requirement.
3. **Write the report.** Follow the field table and rules in `references/defect-reporting.md`: minimal steps, verbatim actual result, both sides of a boundary, reproducibility, severity linked to the requirement's risk, and the evidence. For automation evidence, give the Playwright trace, screenshot and video paths.
4. **Record the key** in `qa/results.json` under the TC (`"defects": ["SHOP-481"]`). If a register is kept, add the entry to `qa/defects.json` (schema in `references/data-model.md`).
5. **Do not create tickets in external trackers yourself.** Give the user the finished report text so they can file it, unless they have explicitly set up and asked for that integration.

## B. Status and completion reports
```bash
python scripts/completion_report.py --qa qa --kind completion --out qa/completion-report.md   # end of cycle or release
python scripts/completion_report.py --qa qa --kind status --out qa/status-report.md           # interim
python scripts/completion_report.py --qa qa --json                                            # facts only
```

Inputs are read from `qa/`:
- **Required:** `requirements.json`, `test-cases.json`, `results.json`
- **Optional:** `defects.json` (without it, open-defect criteria are *unknown*), `exit-criteria.json` (from `planning-tests`), `clarifications.md` (blocking questions)

The script computes:
- coverage, execution %, and pass rate (passed ÷ (passed + failed));
- the share of executed tests run by automation;
- per-requirement verdicts: failed if any linked test failed, passed only if all passed;
- open defects by severity;
- each exit criterion, marked met / not met / unknown;
- the residual risks (in-scope requirements not passed, highest risk first), with the failing or unexecuted TCs and defect keys.

Exit code 1 means at least one criterion is not met or unknown, which is useful as a CI gate.

Then add what the numbers cannot say:
- **Summary (3–5 sentences):** what was tested against the plan, deviations from the plan (scope cut, environment problems), and the most important findings.
- **Quality assessment per risk area:** where confidence is high and where it is low, and why.
- **Residual risks in business terms**, e.g. "REQ-002: coupons at exactly 100,00 TL are rejected, which affects campaign revenue (SHOP-481, high)".
- **Recommendation framed as options:** release, release with named accepted risks and workarounds, or hold until X is fixed. Say who must accept which risk. Do not decide on the stakeholders' behalf.
- **Lessons learned** (completion report only): what to change in the process next time.

Never round up. 94.8% execution against a ≥ 95% criterion is **not met**. A missing defect severity is **unknown**, not zero.

## Files
- `scripts/completion_report.py`: status and completion report, exit-criteria evaluation, residual risks. Output is Markdown or JSON.
- `references/defect-reporting.md`: defect report fields, severity/priority, rules, TR/EN example, evidence, triage.
- `references/data-model.md`: schemas, including `defects.json` and `exit-criteria.json`.
