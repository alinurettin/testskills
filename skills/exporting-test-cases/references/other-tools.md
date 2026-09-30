# TestRail, Azure DevOps Test Plans and Qase

These three importers change more often than Xray's. The mapping below was checked field by field against each vendor's public import documentation on 2026-09-30; the URLs are listed per tool. No file has been imported into a real instance yet, and the import kit for that is in `docs/IMPORT-VERIFICATION.md` at the repository root. **Always do a trial import of 2–3 tests first**, and compare with a CSV exported from your own instance when something does not map.

## Contents
1. TestRail
2. Azure DevOps Test Plans
3. Qase
4. What none of them import

---

## 1. TestRail (`--format testrail`)
Verified against https://support.testrail.com/hc/en-us/articles/7101779988372-Import-test-cases-from-CSV-or-Excel on 2026-09-30. The site refuses automated readers (HTTP 403), so the text was read from the public mirror https://github.com/nendokasei/testrail-docs/blob/main/TestRail-Test-Cases.md. Re-read the original page in a browser before relying on a detail.

**Import path:** Test Cases (the test suite or case repository) → **Import** icon in the toolbar → **Import from CSV**. The wizard has four steps:
1. **File and options:**
   - CSV file: at most **10 MB**. Split larger exports; the exporter warns.
   - File Encoding: **UTF-8**. Excel/Windows files are often Windows-1252.
   - CSV Delimiter: `,`. Start Row: `1`. Keep the header row option selected.
   - Template: **Test Case (Steps)**.
2. **Column mapping:**
   - Layout: **Test cases use multiple rows**, with **Title** as the column that detects the start of a new test case.
   - Map the columns as in the table below.
   - Keep "ignore CSV rows/records without a valid, non-empty title column" enabled, as the docs recommend. If steps 2+ are missing after the import, import again with it disabled.
3. **Value mapping:** map Priority and Type to your instance's values. Critical, High, Medium and Low are TestRail's default priorities.
4. **Preview**, then import.

The docs describe this layout for the Test Case (Steps) template: "all of the standard fields, the first step, and the expected result are defined in the first row, and each additional step and the expected result should be on a separate row". This is exactly what the exporter writes.

| Column | Source | Notes |
|---|---|---|
| Title | `TC-xxx` + title | The TC ID stays visible, so RTM and TestRail stay aligned. It also makes the detection column unique per case, as the docs require. |
| Section | `--folder` | Written as `A > B` (docs: "Top Section > Sub-section 1 > Sub-section 2"). `A/B` is converted. Missing sections are created. |
| Priority | priority → Critical/High/Medium/Low | Map the names to your instance's priorities in the wizard |
| Type | `Regression` if tagged `regression`, else `Functional` | |
| Preconditions | preconditions + test data | |
| Step / Expected Result | one step per row, step data appended as `[data]` | Map to "Steps (Step)" and "Steps (Expected Result)" |
| References | REQ IDs + Jira keys | The docs define references as "a list of IDs, separated by comma or space". With a Jira integration, the keys become links. |

**Verify:** custom fields that are required in your instance, and priority names that were renamed.

## 2. Azure DevOps Test Plans (`--format azure-devops`)
Verified against https://learn.microsoft.com/en-us/azure/devops/test/bulk-import-export-test-cases (ms.date 2026-08-10) on 2026-09-30.
Verified against https://learn.microsoft.com/en-us/azure/devops/test/reference-qa (import FAQ and limits) on 2026-09-30.

**Import path:** Test Plans → a test plan → a suite → **Import test cases from CSV/XLSX** (Microsoft Learn, updated August 2026; verified 2026-09-30). Azure DevOps Services shows a mapping wizard and expects nine mapped fields: ID, Work Item Type, Title, Test Step, Step Action, Step Expected, Area Path, Assigned To, State. Azure DevOps Server imports directly without the mapping step. Older versions used the Boards CSV import with Work Item Type `Test Case`.
- **Layout:** one row per step. Title, Area Path, Priority and State repeat on every row. Test Step is numbered 1..n. Leave ID empty to create new items.
- **Priority:** 1–4 (critical → 1, low → 4). **State:** `Design`.
- **Preconditions and test data:** a Test Case has no field for them, so both are prefixed to the first step's action, one line each. Before 0.7.0 the test data was dropped.
- **Area Path** (`--area-path`) must already exist. Use `\` between levels (`MyProject\Web`); the project name alone is always valid. The exporter warns when the area path is empty or contains `/`. On Azure DevOps Server, Area Path is not required and the import does not change it.
- **Assigned To** (`--assigned-to`) must be a valid user. The exporter leaves it empty unless you pass it. The FAQ lists "Empty required fields" as an import error, so if the wizard complains, re-export with `--assigned-to <e-mail>`.
- **Requirement links cannot be imported through CSV.** Import into a **requirement-based suite** (the suite of the user story), or link the tests afterwards. The FAQ says this suite type "is the **only** way to support end-to-end requirement traceability". The TC ID in the title keeps the RTM traceable.
- **Limits (FAQ):**
  - Titles are cut at 128 characters; the exporter says which ones.
  - Files may be at most 20 MB.
  - A new test case's state must be in the `Proposed` category; `Design` is the default.
  - An operation fails when a test case has more than 1,000 related links.
- **Re-importing with an ID** replaces all steps of that test case. The exporter always leaves ID empty, so it only creates new test cases.
- **Wizard (Services):**
  1. Drop the file.
  2. Check the automatic mapping: the nine required fields plus Priority.
  3. Optionally download the mapping as a template.
  4. Select **Import**.

## 3. Qase (`--format qase`)
Verified against https://docs.qase.io/en/articles/5563719-import-test-cases on 2026-09-30.
Verified against https://docs.qase.io/en/articles/14441496-qase-csv-adding-test-steps on 2026-09-30.
Verified against https://docs.qase.io/en/articles/14442561-qase-csv-create-suites on 2026-09-30.
Verified against https://docs.qase.io/en/articles/14442545-qase-csv-nesting-suites on 2026-09-30.
Verified against https://docs.qase.io/en/articles/14596319-qase-csv-a-walkthrough-guide on 2026-09-30.
Verified against the V2 export sample in https://docs.getxray.app/display/XRAY/Importing+Qase+test+cases+using+Test+Case+Importer on 2026-09-30.

**Import path:** in the repository, the `…` menu (top right) → **Import Data** → format **Qase.io** (the V2 CSV; verified 2026-09-30).
- Do not pick "Qase.io CSV [deprecated]", which is the V1 format.
- Then choose the parent suite and upload the file.
- **Header set:** V2 (`v2.id, title, description, preconditions, …, suite_id, suite, suite_without_cases`). Leave `v2.id` empty for new cases. The docs: "Unlike test case IDs, you can specify the suite ID."
- **Suites:** suite rows come first (`suite_without_cases` 1), numbered from 1, parents before children.
  - `--folder "A/B"` (or `A > B`) creates suite `A` (id 1) and child suite `B` (id 2, `suite_parent_id` 1).
  - Cases reference the leaf suite by `suite_id` and suite name, and its parent in `suite_parent_id`.
  - Without `--folder`, all cases go into one suite called `QA Suite`.
- **Steps:** one row per case. Actions, expected results and data are **numbered inside one cell each**: `1. "…"` then a newline and `2. "…"`.
  - V2 "wraps each step's content so that special characters are preserved". In Qase's own V2 export, a line break inside a step appears as the two characters `\n`, and the exporter writes it the same way since 0.7.0.
  - Double quotes inside a step become `'`.
- **Enums** are lowercase:
  - priority: high/medium/low
  - severity: critical/major/normal/minor
  - behavior: positive/negative
  - automation: to-be-automated/is-not-automated
  - status: actual/draft
- The requirement IDs and Jira keys go into the description, and the REQ IDs also go into the tags. Preconditions and test data go into `preconditions`; before 0.7.0 the test data was dropped.
- **Silent defaults:** the walkthrough warns: "If a value doesn't match, it's silently skipped and a default is applied instead." After a trial import, check priority, severity, type, behavior, automation and status on one case.

**Verify:** Qase documents the V2 step-cell encoding only partly. The line-break encoding above comes from Qase's own export sample, not from a written rule. If steps land in one step, export one manually created case from your workspace and compare its cells with this file.

## 4. What none of them import
- **Execution history.** Results come from runs, via `pw_results.py` and the tool's own API or JUnit import.
- **Attachments and screenshots.**
- **Links to requirements in another system**, other than the reference fields.

Re-importing creates duplicates in all three tools, so export only new tests (`--only`, `--tag`) next time.
