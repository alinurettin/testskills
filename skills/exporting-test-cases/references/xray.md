# Importing into Xray (Jira) with the Test Case Importer

Applies to Xray Cloud and Xray Server/DC. The menu names differ slightly between versions. Before a bulk import, **always do a trial import of 2–3 tests into a sandbox project.**

## What the exporter produces (`--format xray`)

There is one CSV row per **step**. All rows of a test share the same `TCID`, and only the first row carries the test-level fields.

| Column | Map to (Importer "Map fields" step) | Notes |
|---|---|---|
| `TCID` | **Test ID** (mandatory) | Groups the step rows into one test. Carries our `TC-###`. |
| `Summary` | **Summary** (mandatory) | The test title |
| `Description` | Description | Objective, preconditions (as text), test data, requirement refs, technique, QA-ID |
| `Test Type` | **Test Type** (mandatory) | `Manual` by default (change it with `--test-type`) |
| `Priority` | Priority | Mapped from critical/high/medium/low to Highest/High/Medium/Low. Change the mapping with `--priority-map`. |
| `Labels` | Labels | Tags + REQ IDs + technique + polarity. Separated by `--list-delimiter` (default `;`). |
| `Component` | Component/s | Optional (`--component`) |
| `Requirement Keys` | the link field that makes a Test **cover** a Requirement (for example "Tests" / requirement link) | Jira issue keys from `external_id` in requirements.json |
| `Action` | Manual Test Step: **Action** | |
| `Data` | Manual Test Step: **Data** | |
| `Expected Result` | Manual Test Step: **Expected Result** | |

## Steps in the importer

1. Open **Xray → Import → Test Case Importer**. On Server/DC this is under *Tests → Test Case Importer*.
2. Choose **CSV**, upload the file, and select the target Jira project.
3. **Setup:**
   - CSV delimiter: the same as `--delimiter` (default `,`).
   - List delimiter: the same as `--list-delimiter` (default `;`).
   - File encoding: **UTF-8**.
   - If you exported with `--bom` and see a stray character before `TCID`, re-export without `--bom`.
4. **Map fields:**
   - Map the mandatory Test ID, Summary and Test Type fields (as in the table above).
   - Map Action, Data and Expected Result to the manual step fields.
   - Map `Requirement Keys` to the requirement link field. The value must be a list of existing issue keys.
5. Run the import. Check one imported test: the steps, the labels, and whether the requirement shows the test under **Test Coverage**.
6. Save the configuration (the importer can export a JSON config) so later imports reuse the mapping.

## Notes and pitfalls

- **Preconditions:** Xray models preconditions as separate *Pre-Condition* issues. The exporter puts preconditions as text in the Description, which is safe. If the team uses Pre-Condition issues, create them first and map a column holding their keys.
- **Requirement links need Jira keys.** When `external_id` is empty, the link is kept only as a label (`REQ-003`). Add the keys to requirements.json and re-export to get real coverage in Xray.
- **Labels cannot contain spaces.** The exporter replaces spaces with `-`.
- **Re-imports create duplicates.** The Test Case Importer creates new issues; it does not update existing ones. Before a re-import, export only new tests (`--only TC-041,TC-042`, or filter by tag), or update the existing tests in Jira directly.
- **Cucumber / Gherkin tests** (planned for a later phase of the suite) use `Test Type = Cucumber` and a Gherkin Definition column instead of step columns.
- **Large files:** split imports above a few thousand rows, and import by feature folder or tag.
