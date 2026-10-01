---
name: planning-tests
description: Writes a risk-based test plan for a release or feature (ISO/IEC/IEEE 29119-3) with scope, risk register, approach, measurable entry/exit criteria, environments, schedule and an effort estimate computed from QA Suite artifacts. Use when testing must be planned or estimated. Triggers include test plan, test strategy, entry and exit criteria, test estimation; Turkish "test planı hazırla", "test stratejisi", "test eforu tahmini".
license: MIT
metadata:
  suite: qa-suite
  version: "0.7.1"
---

# Planning tests

A test plan is a **decision document**. It says what will and will not be tested, why, how deep, with what, by whom, and how the team will know it is done. Plans fail when they are generic. Every section here must cite this release's facts: requirement IDs, risks, environments, numbers.

## Language
Write the plan in the user's language (TR/EN). Keep IDs and the keys of `exit-criteria.json` in English.

## Reading plan
- This file covers the workflow.
- Read `references/test-strategy.md` for choosing levels and types, checkable criteria, estimation, environments and data, and common plan defects.
- The template is `assets/test-plan-template.md`, bilingual; keep only your language.

## Workflow

```
- [ ] 1. Gather facts (plan_facts.py) and context (release, dates, team, environments)
- [ ] 2. Decide scope and approach per risk
- [ ] 3. Write measurable entry/exit/suspension criteria (+ qa/exit-criteria.json)
- [ ] 4. Environments, data, testability dependencies with owners
- [ ] 5. Schedule and effort (range + method)
- [ ] 6. Write qa/test-plan.md; summarise decisions and open points
```

### 1. Gather facts
```bash
python scripts/plan_facts.py --qa qa [--min-per-step 2 --min-per-test 5 --cycles 2]
```
It computes:
- the scope, the risk distribution and the top risks;
- the tests by priority, technique and category, and the automation candidates;
- the environment matrix from the pairwise specs;
- the open and blocking questions;
- the effort estimate.

If `qa/` does not exist yet, the plan can still be written from the requirements. Say that the numbers are estimates, and recommend running `analyzing-requirements` and `designing-test-cases` first. Ask the user only for what the artifacts cannot know: release dates, team, environments that exist, tools. Do not invent these; mark them as `{{to confirm}}`.

### 2. Scope and approach
- In and out of scope, per requirement or feature, **with reasons** for exclusions.
- The approach follows risk:
  - which levels and types,
  - which techniques at which depth (as in `designing-test-cases`),
  - what gets automated and when (smoke on every pull request, regression nightly),
  - exploratory sessions for thin specifications,
  - non-functional testing (use `testing-nonfunctional`) with the baselines it will use: WCAG 2.2 AA, the ASVS level, the performance thresholds.

### 3. Criteria
Write entry, exit and suspension criteria that can be **measured from the artifacts** (see `references/test-strategy.md` section 3). Copy `assets/exit-criteria.json` to `qa/exit-criteria.json` and adjust the values to the risk. The `reporting-test-results` skill evaluates this file at the end.

### 4. Environments, data and testability
List the environments with their configurations (the pairwise matrix from the facts), the test accounts per role, the test data and who owns it, and the privacy rules. Turn every testability need into a **dependency with an owner**: stubs, seed APIs, clock control, `data-testid`.

### 5. Schedule and effort
Use the facts' estimate. Add the cycles, the defect verification, the environment and data setup, the automation effort and a buffer. Give a **range** with its assumptions. Put milestones in the release calendar.

### 6. Write and summarise
Write `qa/test-plan.md` from the template. Omit sections that do not apply rather than filling them with boilerplate. In chat, summarise:
- the scope decision,
- the top risks and how testing mitigates them,
- the exit criteria,
- the effort range,
- the dependencies needing owners,
- the open points that block the plan.

## Files
- `scripts/plan_facts.py`: facts for the plan from `qa/*`; Markdown or JSON output.
- `assets/test-plan-template.md`: bilingual template following the 29119-3 structure.
- `assets/exit-criteria.json`: default measurable exit criteria.
- `references/test-strategy.md`: levels and types, criteria, estimation, environments and data, pitfalls.
