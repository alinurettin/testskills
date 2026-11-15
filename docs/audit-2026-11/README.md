# Expert audit, November 2026

Five areas of QA Suite 0.9.0 were audited against the current syllabi and standards (ISTQB CTFL v4.0.1, CTAL-TA v4.0, CTAL-TM v3.0, CT-AI v2.0, CT-TAE, CT-PT, OWASP ASVS 5.0.0, the Turkish Testing Board Glossary v2.0 and others). Each report lists its sources with VERIFIED or UNVERIFIED, the findings with the place in the repo, and a concrete fix.

| Report | Area |
|---|---|
| [gap-design.md](gap-design.md) | Test analysis and design |
| [gap-management.md](gap-management.md) | Planning, monitoring, reporting, traceability |
| [gap-automation.md](gap-automation.md) | Automation, API, mobile, non-functional |
| [gap-ai.md](gap-ai.md) | Testing AI systems; using generative AI for testing |
| [gap-exploratory-terms.md](gap-exploratory-terms.md) | Exploratory testing, test data, migration, terminology, Turkish domain packs |

The reports describe 0.9.0. Read them together with the status below.

## Done in 0.10.0
- **Management:** findings 1–6, 8, 9, 10 done; 7 and 12 partly (shared risk rule; entry readiness in `plan_facts.py`).
- **Design:** 3 (BVA consistency) and 4 (decision-table minimisation) done; 7, 10, 14 partly (exclusive bounds, coverage-item headings, `format` parameter type).
- **Automation:** 1–3 done (k6 verdicts, workload model, `k6_results.py`); 4 partly (ASVS chapter placement); 6 partly (tests without an assertion).
- **AI:** 1 and 3 done (gate on incomplete evidence, pending grading); 2 partly (Wilson intervals).
- **Exploratory and domains:** 1, 2, 4, 5, 10, 11 done; 3 and 14 partly; Part 3 (domain packs) done; `shared/glossary-tr.md` written.
- **Evaluation claims:** confidence intervals computed (`tools/eval_stats.py`) and the README and evaluation report corrected.

## Done in 0.11.0
Design coverage script, CTAL-TA v4.0 techniques and CRUD, N-switch coverage, AI pair consistency and Turkish/ASCII-Turkish seeds, ASVS level filter and missing topics, automation lint and flaky policy, k-anonymity, READY_ON_ASSUMPTION gap, orchestrator human-review and data-intake rules, exit-criteria template, official Turkish terms in script output and README.

## Still open
1. **Design:** requirement review smells and base-choice coverage (findings 8, 9, 11–13 of the design report).
2. **Management:** verified coverage in `build_rtm.py` (`AC_THIN`, `DRAFT_ONLY`) and the plan template.
3. **Automation:** API mass-assignment and strict-schema probes, an OpenAPI diff, mobile stale facts.
4. **AI:** multi-turn and agent/tool-use checks, OWASP Agentic Top 10 mapping, the reference aligned with CT-AI v2.0.
5. **Data:** `reconcile.py --rejects` balance and time-zone-aware comparison.
6. **Terminology:** `examples/` keeps its historical wording on purpose; new outputs use `shared/glossary-tr.md`.
7. **Evidence:** re-trial the revised exploratory skill on a small model; run a generated k6 script in real k6; import the exports into a real Xray, TestRail or Qase.
