# Importing into Zephyr Scale (SmartBear, Jira)

This guide targets **Zephyr Scale** (Cloud and Data Center). SmartBear's Cloud docs now call the product just "Zephyr". The older "Zephyr Squad" product uses a different importer. If the team is on Squad, use `--format csv` and its own Excel/CSV importer mapping. The import wizard differs slightly between versions, so **always do a trial import of 2–3 tests first.**

Verified against https://support.smartbear.com/zephyr/docs/en/test-cases/import-test-cases.html (Cloud) on 2026-09-30.
Verified against https://support.smartbear.com/zephyr-scale-server/docs/test-cases/import/from-csv.html (Data Center) on 2026-09-30.
These are documentation checks: no file has been imported into a real Zephyr yet. Three points are **not documented** and must be confirmed by the import kit in `docs/IMPORT-VERIFICATION.md` at the repository root:
- the multi-row step layout;
- whether Test Data is a mapping target;
- the separator for several labels.

## What the exporter produces (`--format zephyr`)

| Column | Zephyr field | Notes |
|---|---|---|
| `Name` | **Name** (required) | `TC-### <title>`. Keeping our ID in the name makes the trace visible in Jira. |
| `Objective` | Objective | Objective, REQ IDs, technique, QA-ID |
| `Precondition` | Precondition | Preconditions and test data (multi-line) |
| `Folder` | Folder | From `--folder`, e.g. `Checkout/Coupon` (`Checkout > Coupon` is converted). Folders are separated by `/`. Missing folders are created; existing ones are merged. |
| `Status` | Status | `Approved` for `ready` tests, otherwise `Draft`. Map these values in the wizard's data-mapping step. |
| `Priority` | Priority | Highest/High/Medium/Low by default. Map them in the wizard, or change them with `--priority-map` (for example Zephyr's default High/Normal/Low: `--priority-map '{"critical":"High","high":"High","medium":"Normal","low":"Low"}'`). The import docs do not list the default priority names. |
| `Labels` | Labels | Separated by `,` by default (`--list-delimiter`). Before 0.7.0 the default was `;`. |
| `Coverage` | Coverage | Jira keys from `external_id`, separated by `, `. The docs say: "An issue key list separated by a comma. If an issue doesn't exist for a given key, it will not be imported and a warning will be generated." |
| `Test Script (Step-by-Step) - Step` | Test Script (Steps) - Step | Only in `--zephyr-steps rows` mode. The column name is the one Zephyr uses in its own exports. |
| `Test Script (Step-by-Step) - Test Data` | step Test Data, if the wizard offers it | The import docs list only Step and Expected Result as step targets. If Test Data is not offered, re-export with `--zephyr-data inline`, which appends the data to the Step cell as `[data]`. |
| `Test Script (Step-by-Step) - Expected Result` | Test Script (Steps) - Expected Result | Only in `--zephyr-steps rows` mode |
| `Test Script (Plain Text)` | Test Script (Plain Text) | Only in `--zephyr-steps single` mode. The docs call it a "Text field, single line". Check that the line breaks between steps survive. |

### Two step layouts

- **`--zephyr-steps rows` (default):** the first row of a test carries all fields plus step 1. The following rows leave the test fields empty and carry only the step columns. This is the common multi-row layout for step-by-step scripts. Confirm it with a trial import. If your version creates one test per row instead, switch to `single`.
- **`--zephyr-steps single`:** one row per test. All steps go in one Plain Text script cell as `1. action [data] => expected`. This always imports, but the steps are not individually executable in Zephyr.

## Steps in the import wizard

1. Open the importer:
   - Cloud: **Test Cases → More → Import from File**, then choose **Excel CSV**.
   - Data Center: **Tests → More → Import from File**, then choose **CSV**.
2. **Setup:**
   - Destination Folder: leave it at the root; the `Folder` column creates the path below it.
   - Date Format: not used by the exporter.
   - File Encoding: **UTF-8**.
   - CSV Delimiter: the same as `--delimiter`.
   - Start Import at Row: `1`.
   - Keep **This row contains the field names** selected.
3. **Field Mapping:** map the columns as in the table above. Unmapped fields are not created. Map the step columns only when you use `rows`, and the Plain Text column only when you use `single`; the two must not be mixed.
4. **Data Mapping:** map the Status, Priority and Label values to the values that exist in your project. The wizard can create unmapped labels automatically.
5. Select **Import**. The **Results** stage lists messages and errors, for example coverage keys that do not exist. Open one test to verify its steps, step data and coverage links.

## Notes and pitfalls

- **Coverage needs Jira keys.** Tests with empty `external_id` show their REQ IDs in labels and the objective only.
- **Re-imports create new test cases.** Export only new tests (`--only`, or `--tag`) for incremental imports.
- **Owner** must be a Jira account ID on Cloud, or a Jira user key such as `JIRAUSER10100` on Data Center. The exporter leaves it out. Add the column yourself if it is needed.
- **Excel users:** Zephyr imports CSV only. Excel creates one CSV file per sheet, so export to CSV from Excel before importing.
- **Backslashes (Data Center):** the docs say "A backslash (\\) alone is not displayed, as it works as an escape character to escape double quotes." Test text with Windows paths or regular expressions loses its backslashes there. Double them by hand, or check the imported text.
- **HTML** is accepted in multi-line fields (Data Center docs). Text that looks like HTML tags may be rendered instead of shown.

**Changes in 0.7.0, after the documentation check:**
- Labels are comma-separated by default. Pass `--list-delimiter ";"` for the old behaviour.
- `--zephyr-data inline` was added.
- `--folder` also accepts `A > B`.
