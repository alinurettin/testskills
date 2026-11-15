---
name: reporting-test-results
description: Writes defect reports (severity vs priority, evidence) and computes test status and completion reports with pass rate, per-requirement verdicts, open defects, residual risks and exit-criteria verdicts. Use when results must become a bug report or a release decision. Triggers include bug report, defect report, test summary report, release readiness, QA sign-off; Turkish "hata raporu yaz", "test özet raporu", "yayına hazır mıyız".
license: MIT
metadata:
  suite: qa-suite
  version: "0.11.1"
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
python scripts/completion_report.py --qa qa --kind status --out qa/status-report.md \
    --period "Sprint 14, week 2" --json-out qa/report-facts.json [--baseline qa/report-facts.prev.json]   # interim
python scripts/completion_report.py --qa qa --json                                            # facts only
```

Inputs are read from `qa/`:
- **Required:** `requirements.json`, `test-cases.json`, `results.json`
- **Optional:** `defects.json` (without it, open-defect criteria are *unknown*; so are they when an open defect has no valid severity or a defect key in `results.json` is not in the register), `exit-criteria.json` (from `planning-tests`), `clarifications.md` (blocking questions: a `| Q-### |` table row counts as blocking when it contains "blocking" or "bloke" and is not marked closed/answered/kapalı/cevaplandı)

The script computes:
- coverage, execution % (passed + failed; **a blocked test is not executed**), pass rate (passed ÷ executed), passed of planned, and blocked %;
- automation: automated tests ÷ automation targets (candidates plus tests a tool already runs);
- per-requirement verdicts: failed if any linked test failed, passed only if all passed;
- risk coverage: per risk level, the requirements passed / failed / not completely tested;
- open defects by severity, deferred defects as **known defects shipped**, and defect metrics (clusters per requirement, reopen and rejection rate; detection percentage only when production defects are recorded);
- each exit criterion, marked met / not met / unknown / waived. A misspelt criterion is unknown, never skipped;
- the residual risks (in-scope requirements not passed, highest risk first), with the failing or unexecuted TCs and defect keys.

A status report adds the impediments (blocked tests with their notes), a suspension check (more than 30% blocked) and, with `--baseline`, what changed since the last report. Both kinds end with fill-in headings (`{{…}}`): fill them or delete them.

Exit code 1 means at least one criterion is not met, unknown or waived, which is useful as a CI gate.

**Waivers.** When stakeholders accept a risk, they record it in `qa/exit-criteria.json` under `waivers` with `criterion`, `approved_by`, `date`, `reason` and `expires`. The report then shows the criterion as *waived* with the approver; it never becomes *met*, and `--allow-waived` is needed for exit code 0. An expired or incomplete waiver does not count. **Never write a waiver yourself**: ask who accepts the risk and until when.

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
