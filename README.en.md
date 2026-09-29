# QA Suite: professional software-testing skills for AI agents

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE) ![Version](https://img.shields.io/badge/version-0.5.1-blue) ![Agent Skills](https://img.shields.io/badge/Agent%20Skills-11%20skills-purple) ![Language](https://img.shields.io/badge/lang-TR%20%7C%20EN-orange)

**[Türkçe README →](README.md)**

![QA Suite](docs/assets/qa-suite-card.png)

QA Suite is a package of 11 Agent Skills that teaches your AI assistant to **work like a senior test analyst**. It runs on Claude Code, claude.ai, the Claude API, and any tool that supports the open Agent Skills standard. It covers:

1. requirements analysis
2. test design with ISTQB techniques
3. traceability
4. export to Xray, Zephyr or Excel
5. Playwright and BDD automation
6. performance, accessibility and security testing
7. defect and completion reporting

Output is in Turkish or English.

## Why it is different
- **It computes the combinatorics instead of guessing them.** Deterministic Python scripts calculate the boundary values, decision tables, state transitions and pairwise sets. The gaps and conflicts they find come back as clarification questions.
- **One ID chain.** Everything stays linked through a single chain of IDs:
  `REQ-001` → design evidence → `TC-001` → a Playwright test tagged `@TC-001` → its result → the traceability matrix → Jira/Xray.
- **Honest by design.** An unimplemented test never counts as passed. Missing data is reported as "unknown", not as zero. An expected result is never bent to match buggy behaviour.

## Evidence: a blind end-to-end trial
We built a new banking scenario, a FAST money transfer. The demo app had **5 hidden defects**, and the agent was not told about them.

| | Result |
|---|---|
| Planted defects | **5/5 found**, plus one real unplanted defect |
| Story ambiguities ("fast", "appropriate message", "TBD") | All raised as questions |
| Test design | 47 tests; 2% critical, 34% high |
| Playwright | 46/46 candidates automated: 37 passed, 9 failed. An independent rerun gave the same result. |
| Release verdict | "Not ready" (4 of 9 exit criteria met), which was correct |

All real outputs are in **[examples/fast-transfer](examples/fast-transfer/README.md)**. The artifacts there are in Turkish.

## Skills
| Skill | What it does |
|---|---|
| `qa-orchestrator` | Runs the end-to-end flow, its stages and its gates |
| `planning-tests` | Writes an ISO 29119-3 test plan with measurable exit criteria and an effort range |
| `analyzing-requirements` | ISO 29148 quality review, TR/EN ambiguity linter, missing requirements and NFR discovery (ISO 25010), risk scoring, question log |
| `designing-test-cases` | EP/BVA, decision table, state transition and pairwise scripts; risk-based test cases; TCKN/IBAN test data checks |
| `testing-nonfunctional` | k6 load tests with thresholds taken from the requirements; WCAG 2.2 A/AA (55 criteria); OWASP ASVS 5.0 |
| `tracing-requirements` | Traceability matrix, coverage gaps, checks for priority inflation and redundant tests, change impact |
| `exporting-test-cases` | Export to Xray, Zephyr Scale, Excel, CSV and Markdown |
| `automating-with-playwright` | Project scaffold and `@TC`-tagged specs; feeds the results back into the traceability matrix |
| `writing-bdd-scenarios` | Gherkin in TR/EN, run through playwright-bdd |
| `reporting-test-results` | Defect reports, and a completion report that evaluates the exit criteria automatically |
| `reviewing-test-cases` | Imports Excel or TestRail CSV exports and audits the tests' quality |

There are also **domain packs** for fintech/banking, e-commerce, health and the public sector. Each contains a regulations checklist, the requirements people often forget, high-risk rules, and synthetic test data.

## Install
**Claude Code (recommended):**
```bash
claude plugin marketplace add alinurettin/testskills
claude plugin install qa-suite@qa-suite-marketplace
```

**claude.ai / Claude API:** download the skill zips from [Releases](https://github.com/alinurettin/testskills/releases) and upload them under **Settings → Skills**. The skills hand work to each other, so upload all 11.

**Other agents (Codex, Copilot, Cursor, Gemini CLI…):** the package follows the open Agent Skills standard. Copy the folders under `skills/` into your tool's skills directory.

**Requirements:**
- Python 3.9+ (the scripts use only the standard library)
- For automation: Node.js 18+ and `@playwright/test`

## Quick start
```
Run a full test analysis for this user story and prepare an Xray import CSV: <story>
Design boundary-value and decision-table tests for the loan application form.
Automate the smoke tests in qa/test-cases.json with Playwright and link the results to the RTM.
Review our team's Excel test cases and find the weak and missing ones.
Prepare the sprint test completion report: are the exit criteria met?
```
Outputs go to `qa/` in your project: requirements, questions, design evidence, test cases, the traceability matrix, export files and reports. Automation goes to `automation/`.

## Standards
- **Test design:** ISTQB CTFL v4.0 and CTAL-TA v4.0, ISO/IEC/IEEE 29119-3/-4
- **Requirements and quality:** ISO/IEC/IEEE 29148, EARS, INVEST, ISO/IEC 25010:2023
- **Accessibility and security:** WCAG 2.2 AA, OWASP ASVS 5.0, OWASP Top 10:2025

No standard text is reproduced; the content is paraphrased into actionable checklists.

## Known limits
- **Not yet tested against real tools:** the Xray/Zephyr imports and the Xray results reporter follow the official documentation but have not been run against a live Jira. Do a 2–3 test trial import first.
- **k6:** the scripts are generated and syntax-checked, but no real load run has been done.
- **Triggering:** automatic skill triggering has only been measured with a proxy method (62/62).
- **Domain packs** are checklists, not legal advice. Confirm the current regulations with your compliance team.

## Development
```bash
python tools/sync_shared.py && python tools/validate_skills.py && python -m unittest discover -s tests
python tools/package_skills.py       # zips for claude.ai (dist/)
```
Issues and pull requests are welcome. See [CHANGELOG.md](CHANGELOG.md) for the history.

## License
[MIT](LICENSE) © 2026 Ali Nurettin Demir
