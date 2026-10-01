---
name: qa-orchestrator
description: Runs the whole QA Suite chain from requirements through analysis, risk-based test design and gap checks to tool export and automation, with one set of stable IDs. Use only when someone wants a complete end-to-end QA package, not a single stage or test type. Triggers include end-to-end test analysis, full QA package, whole QA workflow; Turkish "baştan sona test analizi", "QA paketi hazırla", "test sürecini yürüt".
license: MIT
metadata:
  suite: qa-suite
  version: "0.8.0"
---

# QA Suite orchestrator

This skill coordinates the QA Suite so that a request like "here's the story, give me the tests" produces what a senior test analyst would deliver:
- requirements that were actually questioned,
- tests derived with named techniques at a depth that matches risk,
- proof of coverage,
- files the team can import.

Each stage has its own skill with the detailed procedure. This file decides **which stages to run, in what order, with which gates**.

## Principles (apply across all stages)

1. **Surface, don't invent.** Gaps become derived requirements (marked `derived: true`) or questions (`Q-###`). Tests built on an assumption cite it.
2. **One ID system end to end:** `REQ-###` → `DS-###` (design spec) → `TC-###` → Jira key. IDs are never renumbered. Removed items become `deprecated`.
3. **Compute, don't guess, combinatorics.** Boundaries, decision tables, state coverage and pairwise sets come from the scripts, and their findings count as analysis results.
4. **Risk sets depth.** The likelihood × impact score decides the techniques and the coverage level.
5. **Honest reporting.** Report what was covered, what was deliberately not, and what depends on open questions. Never claim "all requirements are covered" beyond what the RTM shows.
6. **Language:** write artifacts in the user's language (Turkish or English), and keep JSON keys, IDs and enums in English.

## Effort and cost

A QA package is only useful if people read it. Its cost also scales with every file read and every line written. Keep the work proportional:

- **Use light mode by default** for stage 1 when the goal is test cases. Use full mode when the user asks for a requirements review, or when the scope is large or regulated. The modes are defined in `analyzing-requirements`.
- **Follow each skill's reading plan.** Read references only for the techniques and areas you actually use. Read `data-model.md` at most once; the compact format (`qa_compact.py --help`) is all you need for authoring.
- **Author requirements and test cases in the compact format** (`*.src.md` → `qa_compact.py`). Do not hand-write JSON, and do not write your own generator scripts; the bundled converter already does this.
- **Budget for one story with 5–8 acceptance criteria:**
  - 8–15 REQs, of which at most 6 are derived,
  - 6–12 questions,
  - 15–35 test cases, plus pairwise rows.

  Exceeding this is fine when the scripts demand it. Say why in the summary.
- **Run the RTM calibration at most twice.** Leftover items are justified exceptions or questions.

## Stages

| # | Stage | Skill | Main outputs | Gate to continue |
|---|---|---|---|---|
| 0 | Test plan (optional) | `planning-tests` | `qa/test-plan.md`, `qa/exit-criteria.json` | Scope, approach and measurable exit criteria agreed |
| 1 | Requirements analysis | `analyzing-requirements` | `qa/requirements.src.md` → `.json`, `qa/clarifications.md`, in full mode also `qa/analysis-report.md` | Blocking questions surfaced. The user chooses: wait for answers, or proceed on the documented defaults. |
| 2 | Test design | `designing-test-cases` | `qa/design/DS-*.json/.md`, `qa/test-cases.src.md` → `.json` | Calibration passed: no PRIORITY_SKEW; REDUNDANT items resolved or justified |
| 2b | Non-functional (when NFRs exist) | `testing-nonfunctional` | k6 scripts, WCAG 2.2 / ASVS 5.0 test drafts merged into `qa/test-cases.src.md` | Every NFR has a measurable target or an open question |
| 2c | Specialised design (when the product needs it) | `testing-apis`, `testing-mobile-apps`, `testing-ai-features`, `testing-data-migrations` | Contract tests and API spec; mobile checklist and device matrix; AI eval dataset and score gate; reconciliation report | Tests trace to REQs like every other test: operations, capabilities, areas and categories mapped with `--req-map` (one REQ for everything hides gaps); thresholds are explicit numbers |
| 2d | Test data (when tests need it) | `preparing-test-data` | Synthetic data files, masking rules and report | No real personal data in test environments without an approved decision |
| 3 | Traceability | `tracing-requirements` | `qa/rtm.md`, `qa/rtm.csv` | No validation errors. Every gap is fixed or justified. |
| 4 | Export | `exporting-test-cases` | `qa/exports/*` | The user has picked the target tool |
| 5 | Automation (Playwright) | `automating-with-playwright` | `automation/` project, `tests/*.spec.ts` with `@TC-###` tags, `qa/results.json`, `qa/automation-coverage.md` | Tests implemented without `test.fixme`; failures classified as product vs test bugs |
| 5b | BDD (optional) | `writing-bdd-scenarios` | `features/*.feature` (TR/EN) with `@TC-###` tags, step definitions | Scenarios reviewed by the business if they are the audience |
| 5c | Exploratory sessions (recommended for high risk) | `running-exploratory-tests` | Charters, session sheets, session summary, defects, candidate regression tests | Findings turned into defects and scripted tests; debrief held |
| 6 | Reporting | `reporting-test-results` | defect reports, `qa/status-report.md` / `qa/completion-report.md` | Exit criteria evaluated; residual risks stated for the release decision |

If the skills cannot be invoked by name in your environment, read `../<skill-name>/SKILL.md` and follow it. The scripts sit in each skill's `scripts/` folder.

## Choosing the path

- **"Analyse / review these requirements"** → stage 1 only, then offer stage 2.
- **"Write test cases for this story" / "end-to-end test analysis"**:
  - Stage 1 in **light** mode → stage 2 → stage 3.
  - Use full mode for stage 1 only when the scope is large, regulated or high-risk.
- **"We need this in Xray/Zephyr/Excel"**:
  - Test cases already exist: stage 3 → stage 4.
  - No test cases yet: the full chain.
- **"What's our coverage / what do we re-test"** → stage 3. For a regression set within a time budget, use `select_regression.py` in stage 3.
- **"Automate this" / "Playwright testleri yaz"**:
  - If `qa/test-cases.json` exists: stage 5, then the results loop into stage 3.
  - If it does not exist: stages 1–3 first. Automating tests that were never designed produces click-scripts with no oracle.
- **"Test planı / strateji / çıkış kriterleri"** → stage 0. The plan's numbers come from `qa/`, so analyse and design first when those files do not exist yet.
- **Performance, accessibility or security** → stage 2b, after stage 1 has identified the NFRs.
- **"API'yi test et" / an OpenAPI document** → `testing-apis` (stage 2c), then stages 3 and 6.
- **A mobile app** → `testing-mobile-apps` (stage 2c) next to stage 2; automation there uses Appium or Maestro, not Playwright.
- **A chatbot, LLM or RAG feature** → `testing-ai-features` (stage 2c). Get explicit acceptance thresholds in stage 1.
- **A migration, ETL or system replacement** → `testing-data-migrations` (stage 2c); the mapping specification is the requirement.
- **"Test verisi hazırla" / masking** → `preparing-test-data` (stage 2d).
- **"Keşif testi" / "exploratory"** → `running-exploratory-tests` (stage 5c). Charters come from the risk scores of stage 1.
- **"Hata raporu yaz" / "yayına hazır mıyız" / "test özet raporu"** → stage 6.
- **"Mevcut test case'lerimizi incele" (Excel, TestRail…)** → `reviewing-test-cases`, then stage 2 for the missing tests it finds.
- **"Gherkin/BDD senaryoları"** → stage 5b. It uses stage 2's test cases when they exist; otherwise the acceptance criteria.
- **"Test sonuçlarını gereksinimlere bağla"** → run `pw_results.py` from stage 5, then stage 3 with `--results`.

Before any `npm install` or browser download, ask the user. Installing packages is a download.

## Running the full chain

1. **Intake:** product and feature, actors, platforms, domain, risk appetite, target tool, and output language. Infer what you can. Ask at most 3 blocking questions up front. The analysis generates the detailed ones.
2. **Stage 1.** Then pause and show the user:
   - The counts.
   - The top risks.
   - The blocking questions (with their proposed defaults).
   Ask whether to proceed on the defaults. If the user already said to go straight through ("sormadan devam et"), continue and mark the assumptions clearly.
3. **Stage 2.** Design by risk, run the scripts, and write the test cases.
4. **Stage 3.** Loop back to stage 2 until there are no unjustified gaps. Two iterations are usually enough.
5. **Stage 4** if a target was named. Otherwise offer it.
6. **Final delivery:** send the summary below.

## Final delivery summary (use the user's language)

```
## QA package: <feature>
Files: qa/requirements.json · qa/analysis-report.md · qa/clarifications.md · qa/test-cases.json · qa/rtm.md · qa/exports/…

Requirements: N (derived D, awaiting confirmation) · test-ready X / N
Open questions: Q (blocking B). The most important 3: …
Tests: T (positive P / negative N) · by priority C/H/M/L (%) · by technique …
Coverage: requirements R/N (%), functional reqs with negative tests F/G
Design evidence: DS-001 EP/BVA 3-value (x boundary values), DS-002 decision table (y columns, 1 gap → Q-004), …
Not covered / risks: …
Non-functional (if 2b ran): performance P tests (k6 thresholds from REQ-…) · WCAG W tests on <pages> · ASVS S tests (level L2) · NFRs without a target: …
API (if 2c ran): O operations → T contract tests (E executable, K skeletons) mapped to R REQs · contract questions Q · last run passed/failed
Mobile (if 2c ran): T tests (core + <capabilities>) mapped to R REQs · device matrix D devices = X% Android / Y% iOS share · failed on: …
AI (if 2c ran): E eval cases × N runs · gate passed/failed (overall X%, critical failures C, flaky F) · pending grading G
Migration (if 2c ran): reconciliation of R rows: mismatches M (by class) · sign-off criteria met / not met · rehearsal timing …
Test data (if 2d ran): datasets … (fixture / synthetic / masked) · masking report … · real personal data: none (or approved decision …)
Exploratory (if 5c ran): S sessions on C charters · defects D · new regression tests N · debrief held (yes/no)
Automation (if stage 5 ran): A of K candidates automated · last run passed P / failed F (product defects: …) · skeletons left S
Next steps: answer Q-001..; trial import into Xray; …
```
Include a stage line only when that stage ran; leave out the lines of stages that did not.

## Workspace

All artifacts live in `qa/` under the project root, unless the user names another place. The layout and schemas are in `references/data-model.md`. When `qa/` already exists, continue from it: read the existing files, keep the IDs, and increment `version` in requirements.json.
