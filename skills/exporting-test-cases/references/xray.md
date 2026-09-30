# Importing into Xray (Jira) with the Test Case Importer

Applies to Xray Cloud and Xray Server/DC. The menu names differ slightly between versions. Before a bulk import, **always do a trial import of 2–3 tests into a sandbox project.**

Verified against https://docs.getxray.app/display/XRAYCLOUD/Importing+Tests+using+Test+Case+Importer on 2026-09-30.
Verified against https://docs.getxray.app/display/XRAYCLOUD/Examples+using+Test+Case+Importer on 2026-09-30.
Verified against https://docs.getxray.app/display/XRAY/Importing+Manual+Tests+using+Test+Case+Importer (Server/DC) on 2026-09-30.
These are documentation checks: no file has been imported into a real Xray yet. The import kit and the checklist for a real import are in `docs/IMPORT-VERIFICATION.md` at the repository root.

## Contents
1. What the exporter produces
2. Steps in the importer (Cloud, Server/DC)
3. Limits
4. Notes and pitfalls
5. Results import (JUnit, Playwright)

## What the exporter produces (`--format xray`)

There is one CSV row per **step**. All rows of a test share the same `TCID`. Only the first row carries the test-level fields. The exception is `Test Type`, which is repeated on every row, as in Xray's own importer examples.

| Column | Map to (Importer "Map fields" step) | Notes |
|---|---|---|
| `TCID` | **Test ID** (mandatory; the importer calls it *Issue Id* in Cloud and *Test Case Identifier* in Server/DC) | Groups the step rows into one test. Carries our `TC-###`. |
| `Summary` | **Summary** (mandatory) | The test title |
| `Description` | Description | Objective, preconditions (as text), test data, requirement refs, technique, QA-ID |
| `Test Type` | **Test Type** (mandatory on Cloud) | `Manual` by default (change it with `--test-type`). The value must be a test type of the target project; the defaults are Manual, Generic and Cucumber. |
| `Priority` | Priority | Mapped from critical/high/medium/low to Highest/High/Medium/Low (the Jira defaults). Change the mapping with `--priority-map`. |
| `Labels` | Labels | Tags + REQ IDs + technique + polarity. Separated by `--list-delimiter` (default `;`). |
| `Component` | Component/s | Optional (`--component`). The component must already exist. |
| `Requirement Keys` | **Link "Tests"** | Jira keys from `external_id`, in one cell separated by the list delimiter. On Cloud, link fields are list fields. The requirement issues must already exist. |
| `Requirement Key 1..n` | **Link "Tests"**, one mapping per column | Only with `--xray-links columns`. Use it for Server/DC, whose docs say: "If the Test covers multiple requirements, then multiple CSV columns must be used, each one being mapped in the same way." |
| `Action` | Manual Test Step: **Action** (mandatory on Server/DC) | |
| `Data` | Manual Test Step: **Data** | |
| `Expected Result` | Manual Test Step: **Expected Result** | |
| `Test Repository Folder` | **Test Repository Folder** (Cloud) / **Test Repository Path** (Server/DC) | Only when `--folder` is given. Always written as `A/B`, whether you pass `A/B` or `A > B`. |

## Steps in the importer

1. Cloud: open **Apps → Xray** and choose **Test Case Importer** in the Xray side menu. Server/DC: *Tests → Test Case Importer* (administrators also find it under *System → Import and Export → External System Import*). Menu paths verified 2026-09-30.
2. Choose **CSV**. **File Import step:** upload the file. If you saved a configuration earlier, load it here.
3. **Setup step:**
   - Default project: the target Jira project.
   - File encoding: **UTF-8**. Xray's docs say nothing about a BOM. The exporter writes none by default, so leave out `--bom`. If you exported with `--bom` and see a stray character before `TCID`, re-export without it.
   - CSV delimiter: the same as `--delimiter` (default `,`). Cloud offers only comma or semicolon.
   - List value delimiter: the same as `--list-delimiter` (default `;`).
   - Date format: not used by the exporter.
   - Folders: when the file has `Test Repository Folder`, enable folder creation. On Server/DC this option is **Hierarchical Test Organization – Create Folders**.
4. **Map fields:**
   - Map the mandatory fields. Cloud: Test ID, Summary and Test Type. Server/DC: Test Case Identifier, Summary and Action.
   - Map Action, Data and Expected Result to the manual step fields.
   - Map `Requirement Keys` to **Link "Tests"**. For a file exported with `--xray-links columns`, map every `Requirement Key n` column to Link "Tests".
   - Map `Test Repository Folder` to Test Repository Folder (Cloud) or Test Repository Path (Server/DC).
5. Run the import. Check one imported test: the steps, the labels and the folder. Also check that the requirement shows the test under **Test Coverage**.
6. Save the configuration (the importer can export a JSON config) so later imports reuse the mapping.

## Limits

- **Xray Cloud:** at most **1000 issues per import**. A file may hold at most **2000 issue links**, not counting the first link of each test. The exporter warns above both limits. Split the export with `--only` or `--tag`.
- **Xray Server/DC:** the docs state that "there is no limit on the number of tests that can be imported". Large files are still easier to check and roll back when you import by feature folder or tag.

## Notes and pitfalls

- **Preconditions:** Xray models preconditions as separate *Pre-Condition* issues. The exporter puts preconditions as text in the Description, which is safe. If the team uses Pre-Condition issues, create them first and map a column holding their keys.
- **Requirement links need Jira keys.** When `external_id` is empty, the link is kept only as a label (`REQ-003`). Add the keys to requirements.json and re-export to get real coverage in Xray.
- **Labels cannot contain spaces.** The exporter replaces spaces with `-`.
- **Re-imports create duplicates.** The Test Case Importer updates an existing test only when the CSV has a column mapped to the Jira **Issue Key** (on Server/DC this overwrites the test's manual steps); the exporter does not write Jira keys, so every row becomes a new issue. Before a re-import, export only new tests (`--only TC-041,TC-042`, or filter by tag), or update the existing tests in Jira directly.
- **Cucumber / Gherkin tests** (planned for a later phase of the suite) use `Test Type = Cucumber` and a Gherkin Definition column instead of step columns.

**Changes in 0.7.0, after the documentation check:**
- `Test Type` is repeated on every step row.
- `--folder` adds a `Test Repository Folder` column.
- `--xray-links columns` was added for Server/DC.
- The exporter warns about the Cloud limits and about delimiters other than `,` and `;`.

Files exported without `--folder` keep the old columns.

## Results import (JUnit, Playwright)

Verified against https://github.com/Xray-App/playwright-junit-reporter on 2026-09-30.
Verified against https://docs.getxray.app/display/XRAYCLOUD/Taking+advantage+of+JUnit+XML+reports on 2026-09-30.
Verified against https://docs.getxray.app/display/XRAYCLOUD/Import+Execution+Results+-+REST+v2 on 2026-09-30.

The `automating-with-playwright` skill describes this path in its `ci-and-reporting.md` reference. It matches these docs:
- **Reporter:** `@xray-app/playwright-junit-reporter` with `embedAnnotationsAsProperties: true`. `ignoreTestCasesWithoutTestKey` is an option of the reporter: tests without a `test_key` are left out of the XML.
- **`test_key` annotation:** after the CSV import, put each test's Xray key (for example `KIT-12`) in its `external_id` and regenerate the specs. The JUnit import then records the result on that existing test.
- **Tests without `test_key`:** Xray matches or creates *Generic* tests by `classname` + `name`. This creates a second test next to the imported Manual one.
- **`requirements` annotation:** comma-separated Jira keys, which Xray links as covered requirements. Only real Jira keys belong there. Note that `generate_specs.py` falls back to internal `REQ-###` IDs when a requirement has no `external_id`, and Xray cannot resolve those IDs.
- **Upload (Cloud):** `POST /api/v2/import/execution/junit?projectKey=KIT`, optionally with `testExecKey`, `testPlanKey`, `testEnvironments`, `revision` and `fixVersion`. Authenticate with a Bearer token.
