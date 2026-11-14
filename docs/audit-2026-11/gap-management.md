# Gap analysis: test management, planning, monitoring, reporting, traceability

Audited: `planning-tests`, `reporting-test-results`, `tracing-requirements`, `qa-orchestrator`, `shared/data-model.md`. Findings 1, 2, 3 and 10 were reproduced by running the scripts on a throwaway fixture in the scratchpad (repo untouched).

## Sources checked

| Source | Version / date | Status |
|---|---|---|
| ISTQB CTFL syllabus, ch. 5 — https://www.istqb.org/wp-content/uploads/2024/11/ISTQB_CTFL_Syllabus_v4.0.1.pdf | v4.0.1, 2024-09-15 (errata of v4.0). istqb.org page (modified 2026-08-22) lists nothing newer | VERIFIED (text read) |
| ISTQB CTAL-TM syllabus — https://www.istqb.org/wp-content/uploads/2024/11/ISTQB_CTAL-TM_Syllabus_v3.0_zKjKsaN.pdf | v3.0, 2024-05-03; chapters: Managing the Test Activities / the Product / the Team | VERIFIED (§1.3, 2.1–2.3 read) |
| ISO/IEC/IEEE 29119-3 — https://standards.iteh.ai/catalog/standards/iso/b4f42a41-dd8f-446c-9674-238ba5dc90f1/iso-iec-ieee-29119-3-2021 | 2021, ed. 2 | Headings of 7.3/7.4 VERIFIED via catalogue listings; body paywalled; incident-report fields UNVERIFIED |
| ISO/IEC/IEEE 29119-2 | 2021 | UNVERIFIED (iso.org returned 403) |
| IEEE 1044-2009 — https://standards.ieee.org/ieee/1044/4607 | Inactive-reserved since 2020-03-05 | Status VERIFIED; content UNVERIFIED |
| DORA metrics guide — https://dora.dev/guides/dora-metrics/ | Updated 2026-01-05; five metrics | VERIFIED |
| Yoo & Harman, regression survey (STVR 2012) | — | Existence VERIFIED; details UNVERIFIED |
| PRAM (Black 2009), PRISMA (van Veenendaal 2012), FMEA | Named in CTAL-TM §1.3.5 | Naming VERIFIED; books UNVERIFIED |
| TMMi R1.3, TPI Next | — | UNVERIFIED; not used |

The repo cites "CTFL v4.0" and "29119-3" without year: write v4.0.1 and :2021.

## Findings

| # | Finding | Kind | Source | Where | Concrete fix | Effort | Script? |
|---|---|---|---|---|---|---|---|
| 1 | Blocked tests count as executed and are excluded from pass rate. Fixture with 6 passed, 4 blocked: execution 100%, pass rate 100%, both criteria "met". | wrong | CTAL-TM §2.1.1, §2.1.3 (status vs planned; blocked is its own status) | `completion_report.py` L125, L174–175 | `executed = passed + failed`; add `passed_of_planned_pct`; new criterion `max_blocked_pct`; print blocked separately. | S | yes |
| 2 | Open-defect criteria pass silently. An open defect with no severity, one with `"Critical "` and a deferred critical all gave "critical ≤ 0: met". Contradicts SKILL.md L60. Defect keys in results.json absent from defects.json are ignored. | wrong | CTFL §5.3.2 (unmitigated risks, defects not fixed); 29119-3 §7.4.7 | `completion_report.py` L28, L163–164, L204–208 | Strip/validate severity; any open defect without valid severity makes every `max_open_defects.*` unknown; list deferred defects as "known defects shipped" plus `max_deferred_defects`; warn on unregistered keys. | S | yes |
| 3 | Regression budget fill is depth-first with a skip bug: a 50-minute must test was skipped, later cheaper tests kept filling, all selected tests hit one requirement, exit 0, no warning. | wrong | CTAL-TM §1.3.4 (depth-first vs breadth-first under time pressure); CTFL §5.1.5 (additional coverage) | `select_regression.py` L118, L122–132 | Under a budget order each tier breadth-first: one test per not-yet-covered requirement in risk order, then seconds (`--order breadth\|depth`). If any must test is left out, print "MUST tier exceeds budget" and exit 1. List requirements with zero selected tests. | M | yes |
| 4 | Estimate is one point, execution only, though the skill demands a range. Cycle 2 assumes a full rerun; pairwise configurations are not multiplied; "if automated" subtracts hours at zero automation cost. | shallow | CTFL §5.1.4 (three-point: E=(a+4m+b)/6, SD=(b−a)/6; ratios; extrapolation); CTAL-TM §2.2.3 | `plan_facts.py` L86, L104–109; `test-strategy.md` §4 | Output a/m/b and E ± SD (`--optimistic 0.7 --pessimistic 1.8`); use `duration_ms` when present and say "extrapolated"; print ratio add-ons (defect handling 25%, configurations, retest share, automation build hours per candidate) as named assumptions. | M | yes |
| 5 | No risk-coverage metric; the gate checks only the critical band, so a failed or unrun high-risk requirement can pass. | missing | CTAL-TM §2.1.3 (risks with all tests passed / some failed / not completely tested), §1.3.4 | `completion_report.py` L173, L198; `exit-criteria.json` | Add a per-risk-level table (passed / failed / not completely tested) and `min_requirements_passed_pct: {"critical":100,"high":100,"medium":90}`. | S | yes |
| 6 | No accepted-risk path: criteria are only met / not met / unknown, so real releases bypass the gate informally. | missing | CTFL §5.1.3 (ending on time or budget is valid once stakeholders have "reviewed and accepted the risk") | `exit-criteria.json`; `completion_report.py` L185–210 | Optional `waivers: [{criterion, approved_by, date, reason, expires}]`; fourth state "waived" shown with approver; exit 0 only with `--allow-waived`; the agent never writes a waiver itself. | M | yes |
| 7 | Ordinal L×I product treated as arithmetic: impact 5 (regulatory, data leak, safety) with likelihood 1–3 lands in medium or high; only 4×5, 5×4, 5×5 reach critical. Three script copies differ (select_regression falls back to 6 and needs ints). | shallow | CTAL-TM §1.3.3 (ordinal values combine through a risk matrix; product is for quantitative data) | `risk()` in three scripts; analyzing-requirements §6; `technique-selection.md` §2 | One shared function with matrix overrides: impact 5 is at least high; impact 5 and likelihood ≥ 3 is critical. Show L and I separately in registers. Add churn and defect history to likelihood anchors. | M | yes |
| 8 | Status report equals completion report with another title. | missing | 29119-3:2021 §7.3 (incl. new and changed risks, planned testing) vs §7.4 (deviations, blockers, measures, residual risks, deliverables, reusable assets, lessons); CTFL §5.3.2 | `completion_report.py --kind`; SKILL.md part B | Status: period, deltas against `--baseline` facts JSON, impediments (blocked tests with notes), suspension check (> 30% blocked), fill-in headings for new/changed risks and next period. Completion: headings for deviations and deliverables/reusable assets. | M | yes |
| 9 | Defect report and `defects.json` lack date, reporter, status and classification data, so no defect metric can be computed (found vs resolved, clusters, reopen and rejection rate, DDP). Status enum omits `reopened`/`duplicate` though the code accepts `reopened`. | missing | CTFL §5.5, §5.3.1; CTAL-TM §2.3.5–2.3.6; IEEE 1044 as taxonomy only | `defect-reporting.md` §1; `data-model.md` defects.json; report defects block | Optional keys `reported_on, reported_by, detected_in, introduced_in, root_cause, component, resolution, reopened_count`. Report: defects per requirement (top clusters), open vs resolved, reopen and rejection rate; DDP only when production defects are recorded, else "not measurable yet". | M | yes |
| 10 | `min_automation_pct` measures automated share of executed tests (two automated runs alone give 100%); defaults disagree (50 vs 60); `select_regression` lists a `ci`-sourced test as manual. | wrong | CTAL-TM Table 2 (actual vs planned automated test cases) | `completion_report.py` L128, L176; `exit-criteria.json` L8; `data-model.md` L173; `select_regression.py` L117 | automation_pct = automated ÷ automation candidates; one `is_automated()` rule in both scripts; align defaults. | S | yes |
| 11 | "Covered" means at least one non-deprecated test (drafts count); acceptance criteria are not traced. | shallow | CTFL §5.3 (coverage of risks, requirements or acceptance criteria) | `build_rtm.py` L243–249, L268 | Report designed vs verified coverage (all linked tests passed); gaps `AC_THIN` (tests < acceptance criteria on high/critical) and `DRAFT_ONLY`. | S | yes |
| 12 | Plan template lacks metrics to collect, stakeholders, project risks with response and owner; entry criteria are prose only. | missing | CTFL §5.1.1, §5.2.4; 29119-3 test plan | `test-plan-template.md` §3, §5; `plan_facts.py` | Risk register columns: Type, L, I, Level, Response (mitigate/accept/transfer/contingency), Owner, Status. Add "Metrics and reporting". `plan_facts.py` prints entry readiness: % requirements ready, blocking questions, high/critical requirements without tests. | S | small |

## What is already right

- Unknown stays unknown, no rounding up, exit code 1 on unknown; the release decision stays with stakeholders.
- Per-requirement roll-up (failed beats blocked beats passed) and risk-ordered residual-risk list.
- Regression reasons per test (CHANGED, RELATED, RETEST, SMOKE) with the cut listed as residual risk.
- Severity vs priority separation, product-bug-or-test-bug check, boundary both-sides rule.
- Calibration smells (PRIORITY_SKEW, REDUNDANT) and stable IDs with `deprecated` instead of deletion.

## Not worth doing

- TMMi / TPI Next maturity content: assesses organisations, changes no artifact.
- FMEA / FTA procedures: heavyweight, safety-critical; one sentence pointing to them is enough.
- DORA metrics computation: needs deployment data the suite does not hold; mention change fail rate only as the post-release check in lessons learned.
- Code-coverage gates: not derivable from `qa/`; the existing "requirements coverage only" caveat suffices.
- Wideband Delphi / planning poker scripts: team rituals; one line in `test-strategy.md` §4 is enough.
