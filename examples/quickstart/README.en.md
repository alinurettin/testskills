# Start in 10 minutes: a password-reset story

**[Türkçe →](README.md)**

See what QA Suite produces from a small, synthetic user story with 6 acceptance criteria: [US-128-sifre-sifirlama.md](US-128-sifre-sifirlama.md) (password reset through "Şifremi unuttum", i.e. "Forgot my password"). The story and the outputs are in Turkish, because the suite writes in the user's language.

The files in `qa/` are the expected outputs for this story. They were produced by following the skill instructions step by step:
1. `qa-orchestrator`, light mode
2. `analyzing-requirements`
3. `designing-test-cases`
4. `tracing-requirements`
5. `exporting-test-cases`

The scripts computed the numbers; nothing was edited by hand.

## 1. Set up
1. Install QA Suite: [README → Install](../../README.en.md#install).
2. Create an empty folder and copy `US-128-sifre-sifirlama.md` into it. On claude.ai, paste the story text into the chat instead. Do not run it inside this repository: if the assistant sees the expected outputs here, the result is no longer its own analysis.

## 2. Paste this prompt
```
Run a full end-to-end test analysis for the user story in US-128-sifre-sifirlama.md.
Use light mode. Mark the questions with their default answers and continue without waiting.
Design the test cases, build the traceability matrix and export them to Excel (xlsx).
No automation.
```
If you write the prompt in English, the artifacts come out in English. Use the Turkish prompt from [README.md](README.md) to get outputs comparable with `qa/`.

## 3. What you will see
The assistant works through these steps in order:
1. **Requirements analysis.** It splits the story into atomic, testable requirements, scores their risk and writes the ambiguities down as questions. At the end of this step it shows the counts and the most important questions. Because you said "continue without waiting", it proceeds on the documented defaults.
2. **Test design.** It runs the boundary-value, decision-table and state-transition scripts. The conflicts they find become new questions. Then it writes the test cases.
3. **Traceability and calibration.** It builds the matrix, checks coverage gaps and priority inflation, and fixes them in at most two passes.
4. **Excel export** and a short summary.

**Time and cost:** expect about 10 minutes in light mode for a story of this size. This is an estimate; it was not measured for this example. Two measured references ([docs/EVALUATION.en.md](../../docs/EVALUATION.en.md)):
- In the 0.2.0 comparison, a task with the skills took ~7.5 minutes and ~136k tokens on average. One of the tasks was an end-to-end analysis from a coupon story to an Xray CSV.
- The full end-to-end FAST trial, including automation and reports, took ~26 minutes and ~334k tokens. Light mode without automation costs clearly less.

## 4. Expected outputs
| File | Contents | In this example |
|---|---|---|
| [qa/requirements.src.md](qa/requirements.src.md) → [.json](qa/requirements.json) | Requirements with source, risk (likelihood × impact) and status | 14 requirements. 2 are derived: the story does not state them, but they need tests. Risk: 4 high, 8 medium, 2 low |
| [qa/clarifications.md](qa/clarifications.md) | Questions with options, a default answer, why it matters and who should answer | 11 questions, none blocking. One came from the decision-table script (Q-011) |
| [qa/design/](qa/design/) | Design evidence: the script inputs (`.json`) and outputs (`.md`) | DS-001: boundary values. DS-002: decision table (6 columns, 15 conflicts → Q-011). DS-003: state transitions (5 transitions, 4 invalid transitions) |
| [qa/test-cases.src.md](qa/test-cases.src.md) → [.json](qa/test-cases.json) | Test cases with steps, data, expected results, priority and technique | 25 tests: 8 positive, 17 negative. Priority: 2 critical, 6 high, 15 medium, 2 low |
| [qa/rtm.md](qa/rtm.md) · [qa/rtm.csv](qa/rtm.csv) | Traceability matrix and coverage gaps | Coverage 13/14 (92.9%). All 13 functional requirements have negative tests |
| [qa/exports/test-cases.xlsx](qa/exports/test-cases.xlsx) | Excel workbook with a test-case sheet and a summary sheet | 25 tests, 52 steps |

The report also shows honestly what was left open:
- **REQ-012 ("pages should open fast") has no test.** It has no measurable target; a performance test follows once Q-006 is answered.
- **The calibration's REDUNDANT warning (TC-016..TC-018) is kept, with a reason.** The three tests check three different decision-table columns (the digit, lower-case and upper-case rules); they are not the same equivalence class.

Your run will not match word for word. The counts should stay within the skill's budget: 8–15 requirements, 6–12 questions and 15–35 tests for a story of this size.

## 5. A few tests worth a look
- **TC-004, dotless ı:** typing `ırem.test@example.com` must not send a link for the `irem.test@example.com` account. Loose Unicode matching is a known defect class that can send the reset link to the wrong address.
- **TC-011, two tabs:** with the same link open in two tabs, the second tab must not be able to save a password.
- **TC-024, sessions:** merely requesting a reset must not end open sessions. Otherwise anyone could log any user out.

## 6. Opening the outputs in Excel
- Double-click `qa/exports/test-cases.xlsx`. Turkish characters and multi-line steps display correctly.
- `qa/rtm.csv` is UTF-8 with a BOM and comma-delimited. Excel with a Turkish (or other `;`-separator) locale may show everything in one column on double-click. In that case use **Data → From Text/CSV** and choose UTF-8 and the comma delimiter.

Prompt cards for manual testers (in Turkish): [docs/MANUEL-TEST-REHBERI.md](../../docs/MANUEL-TEST-REHBERI.md).

## Next steps
- Send the questions to the product owner. When the answers arrive, say "Q-001..Q-011 are answered, update the tests"; the IDs stay stable.
- Export to your test-management tool: "export the test cases to Xray" (or Zephyr, TestRail, Azure DevOps, Qase). Do a trial import of 2–3 tests first.
- To run the scripts yourself (from the repository root):
  ```bash
  cd examples/quickstart
  python ../../skills/tracing-requirements/scripts/build_rtm.py --requirements qa/requirements.json --tests qa/test-cases.json --out-dir qa
  python ../../skills/exporting-test-cases/scripts/export_tests.py --tests qa/test-cases.json --requirements qa/requirements.json --format xlsx --lang tr --out qa/exports/test-cases.xlsx
  ```
