# Gap analysis: test analysis and test design

Paths are relative to `C:\projeler\TestSkills\skills\` (DTC = `designing-test-cases`). Script behaviour was confirmed by running the scripts on small specs (stdout only; the repo is untouched).

## Sources checked

| Source | Version / date | Status |
|---|---|---|
| ISTQB CTFL syllabus (istqb.org/wp-content/uploads/2024/11/ISTQB_CTFL_Syllabus_v4.0.1.pdf) | v4.0.1, 2024-09-15; no newer release found | VERIFIED (§1.4, 3.2, 4.2, 4.4, 4.5 read) |
| ISTQB CTAL-TA syllabus (istqb.org/wp-content/uploads/sdm-uploads/ISTQB-CTAL-TA-Syllabus-v4.0-EN-4.pdf) | v4.0 GA, 2025-05-02; v3.1.2 exams end 2026-11-16 | VERIFIED (§1.2–1.3, 3, 5.2 read) |
| ISTQB CTAL-AT (Agile Tester) syllabus (Brightest mirror of the istqb.org PDF) | v2.0, 2026-04-17; replaces CTFL-AT (sunset). Newer than anything the repo cites | VERIFIED (§4.1, 5.3 read) |
| ISTQB CTAL-TTA syllabus (istqb.org/wp-content/uploads/2024/11/ISTQB-CTAL-TTA_Syllabus_v4.0.pdf) | v4.0, 2021-06-30 | VERIFIED (contents only) |
| ISO/IEC/IEEE 29119-4 (assets.vde-verlag.de preview) | Ed. 2, 2021-10 | Clause 5–6 list VERIFIED; clause text UNVERIFIED (paywalled) |
| ISO/IEC/IEEE 29148 (genorma.com; iso.org returned 403) | 2018 still current; 3rd edition at DIS ballot since 2026-09-14 | Status VERIFIED; characteristic list UNVERIFIED (memory) |
| ISO/IEC 25010 (iso25000.com) | 2023 | Characteristics 1–4 VERIFIED; 5–9 UNVERIFIED (memory) |
| EARS (alistairmavin.com/ears) | 2009 notation | VERIFIED |
| NIST combinatorial testing (csrc.nist.gov/projects/automated-combinatorial-testing-for-software) | Page updated 2026-06-08; ACTS 3.3 | VERIFIED |
| Gherkin reference (cucumber.io/docs/gherkin/reference) | Current | VERIFIED |
| Segura et al., metamorphic testing (TSE 2016 survey; TSE 2018 REST patterns) | — | Pattern names VERIFIED via search snippets; definitions UNVERIFIED |
| Beizer 1990, Copeland 2004, Kaner 2013 | — | UNVERIFIED (memory) |

## Findings

| # | Finding | Kind | Source | Where in the repo | Concrete fix | Effort | Script? |
|---|---|---|---|---|---|---|---|
| 1 | Technique coverage is claimed by hand, never computed. No script links coverage items (`DS-001 C-07`, `S-02`, `N-05`) to tests, so "12/12 boundary values" in the summary is unchecked. | missing | CTFL §4.2.1–4.2.4; 29119-4 cl. 6.2 | `DTC/SKILL.md` step 7; `DTC/references/technique-selection.md` §4; `tracing-requirements/scripts/build_rtm.py` | New `DTC/scripts/design_coverage.py`: read each `qa/design/DS-*.json` output, match `design_ref`, print covered/total per technique and list uncovered items. Run it in step 6. | M | Yes |
| 2 | `techniques.md` says it follows CTAL-TA v4.0 but teaches the v3.1.2 set. Metamorphic testing and the test-oracle problem are absent across the repo, including the `technique` enum. | outdated / missing | CTAL-TA §1.3.4, §3.3.2; 29119-4 5.2.11 | `DTC/references/techniques.md` line 3; `shared/data-model.md` enumerations; `qa_compact.py` `TECH` | Add a section: relation catalogue (permutation, scaling, add-then-remove, filter gives subset, disjoint partitions), one worked example, source and follow-up written as one test. Add `metamorphic` (`mt`) to the enum. Selection row: "no trustworthy expected value: calculations, search, reports, AI". | M | Yes (enum) |
| 3 | 3-value BVA: doc and script disagree. `techniques.md` gives 17, 18, 19 / 64, 65, 66 for 18–65; `ep_bva.py` emits 16–19 and 64–67 (it treats 17 and 66 as boundary values of the invalid partitions, the CTFL reading). The coverage formula given is the 2-value one. | wrong (inconsistent) | CTFL §4.2.2 | `DTC/references/techniques.md` §2; `DTC/scripts/ep_bva.py` `analyse_ordered` | Fix the example to match the script, add the 3-value formula (boundary values plus neighbours), add spec key `"bva_scope": "valid"\|"all"`, adjust the critical-risk test budget. | S | Small |
| 4 | Decision-table minimisation is weak. Infeasible combinations block merging (4 columns where 2 suffice). `-` is always filled with the first value, so a feasible value may never be tested (`member=N` in my probe). A rule subsumed by another with the same outcome is silent. | shallow | CTAL-TA §3.3.1 | `DTC/scripts/decision_table.py` `collapse`, `run` (test-condition loop) | Treat infeasible combinations as wildcards when merging; rotate don't-care values so every condition value appears at least once; report redundant or overlapping rules; print the checksum. | M | Yes |
| 5 | State transition offers only 0/1-switch. No round-trip coverage, no N ≥ 2, no all-states level, and no covered/total figures. | missing | CTFL §4.2.4; CTAL-TA §3.2.2 | `DTC/scripts/state_transition.py` (`--switch` choices 0, 1); `techniques.md` §4 | Generalise `--switch N`; add `--coverage round-trip` (simple cycles per state); print covered/total for states, valid transitions and all transitions; note BVA on guard conditions. | M | Yes |
| 6 | CRUD testing is described as entity × operation × role, which is a permission matrix. Missing: the function × entity matrix, the completeness check (an entity lacking C, R, U or D is a question) and lifecycle consistency tests with negatives (read, update or delete before create and after delete). | wrong (loose) | CTAL-TA §3.2.1 | `DTC/references/techniques.md` §7; `technique-selection.md` §1 row "CRUD matrix" | Rewrite §7 in two parts: CRUD matrix (completeness, lifecycle sequence, coverage = operations exercised / operations in matrix) and permission matrix (keep the current text). | S | No |
| 7 | Domain testing is absent. `ep_bva.py` handles one variable with closed bounds only, so `> 1.29` must be converted by hand and compound borders (`instalment / income ≤ 0.5 AND age ≥ 18`) cannot be modelled. | missing | CTAL-TA §3.1.1; Beizer ch. 6; Kaner | `DTC/scripts/ep_bva.py` spec; `techniques.md` (no section) | Add `min_exclusive` / `max_exclusive` keys. Add a section with ON/OFF/IN/OUT points, simplified domain coverage (one ON and one OFF per border, other variables at IN values) and a two-variable example. | M | Small |
| 8 | Review automation misses manual test smells now in the syllabus: "or" or branching in expected results, an action verb inside the expected result, no preconditions, no cleanup after data creation, near-duplicate tests differing only in data. The rubric lacks necessity, consistency and precision. | missing | CTAL-AT v2.0 §5.3; CTAL-TA §1.3.2 | `reviewing-test-cases/scripts/review_tests.py`; `references/review-rubric.md` §1 | Add rules `BRANCHING_EXPECTED`, `ACTION_IN_EXPECTED`, `NO_PRECONDITION`, `NO_CLEANUP`, `NEAR_DUPLICATE` (TR/EN). Add a rubric table mapping D1–D8 to the nine quality criteria. | M | Yes |
| 9 | Combinatorial: no base-choice criterion; each-choice (`strength: 1`) works but is undocumented; an existing set cannot be measured during a review. | missing | CTAL-TA §3.1.2, §3.5.1; 29119-4 5.2.5; NIST | `DTC/scripts/pairwise.py`; `technique-selection.md` §2 | Add `"criterion": "base-choice"` with a `base` row and `--measure rows.csv` (t-way coverage % of an existing set). Depth table: low each-choice, medium base-choice, high pairwise, critical 3-way or all combinations. | M | Yes |
| 10 | Script outputs label `C-##` rows "Test conditions". In CTFL v4 these are coverage items; test conditions come from analysis (SKILL step 2 uses the term correctly). | terminology | CTFL §1.4.1, §1.4.3 | `ep_bva.py`, `decision_table.py` (`T` dicts); `techniques.md` §11 | Rename the heading to "Coverage items" / "Kapsam öğeleri". Add one line: test condition → coverage item → test case. | S | Labels |
| 11 | Scenario testing covers main, alternative and exception flows only. No rule for loops, and coverage is undefined. | shallow | CTAL-TA §3.2.3 | `DTC/references/techniques.md` §6 | Add simple loop coverage (zero, one, typical, maximum iterations) and coverage = scenarios exercised / identified. | S | No |
| 12 | Requirement review is checklist-only. No perspective-based or scenario dry-run pass and no example mapping. The linter never reads `acceptance_criteria` and accepts weak modals (should, may, `-ebilir`). | shallow | CTAL-TA §5.2.2; CTAL-AT §4.1.3, §4.1.5; 29148 | `analyzing-requirements/scripts/lint_requirements.py` `lint_one`; `references/ears-and-stories.md` | Lint acceptance criteria; add `WEAK_MODAL`. Add "Example mapping" (rule → examples → questions; many rules or questions means slice the story) and a four-perspective pass for full mode. | M | Yes |
| 13 | Nothing checks that a declarative rewrite kept every tag and expected value. `Kural` (Rule) is listed but never used. | missing | Gherkin reference; CTFL §4.5.3 | `writing-bdd-scenarios/scripts/generate_features.py`; `references/gherkin-style.md` | Add `--check features/`: compare `@TC` tags and quoted values with `test-cases.json`; flag more than one When, a missing Then, UI verbs and over seven steps. Document grouping scenarios under `Rule:`. | M | Yes |
| 14 | Syntax testing exists only for TCKN/VKN/IBAN. Other formatted fields (phone, plate, postcode, coupon code) get ad hoc error guessing. | missing | 29119-4 5.2.4 | `DTC/scripts/ep_bva.py`; `check_ids.py` | Add parameter type `format` with segments; emit one valid value per option and single-mutation invalid values (missing, extra, wrong class, wrong separator). | M | Yes |

## What is already right

- 2-value BVA, each-choice combination of valid values and the single-fault rule for invalid values match CTFL §4.2.1–4.2.2.
- Decision-table gap, conflict and dead-rule detection, and "no minimisation at high risk", match CTAL-TA §3.3.1.
- The state table with invalid transitions tested one per test, plus unreachable, dead-end and nondeterminism findings, matches CTFL §4.2.4 and CTAL-TA §5.2.1.
- `pairwise.py` handles constraints, seed rows and t-way strength, verifies its own output and exits non-zero on gaps.
- The 29148 characteristics, EARS patterns, 25010:2023 names, INVEST and the two acceptance-criteria formats are correct and current.

## Not worth doing

- Cause-effect graphing and crowd testing: the decision-table script already delivers the first; the second is organisational.
- White-box measures (statement, branch, MC/DC) in a black-box design skill: one pointer line at most.
- A classification-tree tool: v4.0 treats the tree as a modelling aid; "flatten into `pairwise.py`" is enough.
- Random testing as its own script: it has no coverage criterion; mention it only as a seeded input source for metamorphic relations.
- Rewriting for the 29148 third edition: still a draft; revisit on publication.
