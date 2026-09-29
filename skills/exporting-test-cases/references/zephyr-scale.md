# Importing into Zephyr Scale (SmartBear, Jira)

This guide targets **Zephyr Scale** (Cloud and Data Center). The older "Zephyr Squad" product uses a different importer. If the team is on Squad, use `--format csv` and its own Excel/CSV importer mapping. The import wizard differs slightly between versions, so **always do a trial import of 2–3 tests first.**

## What the exporter produces (`--format zephyr`)

| Column | Zephyr field | Notes |
|---|---|---|
| `Name` | **Name** (required) | `TC-### <title>`. Keeping our ID in the name makes the trace visible in Jira. |
| `Objective` | Objective | Objective, REQ IDs, technique, QA-ID |
| `Precondition` | Precondition | Preconditions and test data (multi-line) |
| `Folder` | Folder | From `--folder`, e.g. `Checkout/Coupon`. Folders are separated by `/`. |
| `Status` | Status | `Approved` for `ready` tests, otherwise `Draft`. Map these values in the wizard's data-mapping step. |
| `Priority` | Priority | Highest/High/Medium/Low by default. Map them in the wizard, or change them with `--priority-map` (for example Zephyr's default High/Normal/Low: `--priority-map '{"critical":"High","high":"High","medium":"Normal","low":"Low"}'`). |
| `Labels` | Labels | Separated by `--list-delimiter` (default `;`) |
| `Coverage` | Coverage (issues) | Comma-separated Jira keys from `external_id` |
| `Test Script (Step-by-Step) - Step` / `- Test Data` / `- Expected Result` | Test Script (Steps) | Only in `--zephyr-steps rows` mode |
| `Test Script (Plain Text)` | Test Script (Plain Text) | Only in `--zephyr-steps single` mode |

### Two step layouts

- **`--zephyr-steps rows` (default):** the first row of a test carries all fields plus step 1. The following rows leave the test fields empty and carry only the step columns. This is the common multi-row layout for step-by-step scripts. Confirm it with a trial import. If your version creates one test per row instead, switch to `single`.
- **`--zephyr-steps single`:** one row per test. All steps go in one Plain Text script cell as `1. action [data] => expected`. This always imports, but the steps are not individually executable in Zephyr.

## Steps in the import wizard

1. Open **Zephyr → Test Cases → Import** (the three-dot menu, or *Import test cases*) and choose **CSV**.
2. **Setup:**
   - CSV delimiter: the same as `--delimiter`.
   - Encoding: **UTF-8**.
   - The first row contains the field names.
3. **Field mapping:** map the columns as in the table above. Unmapped columns are ignored.
4. **Data mapping:** map the Status, Priority and Label values to the values that exist in your project.
5. Run the import and check the Results page for errors. Open one test to verify its steps and coverage links.

## Notes and pitfalls

- **Coverage needs Jira keys.** Tests with empty `external_id` show their REQ IDs in labels and the objective only.
- **Re-imports create new test cases.** Export only new tests (`--only`, or `--tag`) for incremental imports.
- **Owner** must be a Jira account ID. The exporter leaves it out. Add the column yourself if it is needed.
- **Excel users:** Zephyr imports CSV only. Excel creates one CSV file per sheet, so export to CSV from Excel before importing.
