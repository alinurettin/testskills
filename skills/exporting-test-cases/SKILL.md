---
name: exporting-test-cases
description: Exports QA Suite test-cases.json into validated import files for Xray, Zephyr Scale, TestRail, Azure DevOps and Qase, or an Excel workbook, CSV or Markdown document, keeping Jira requirement links and Turkish characters intact. Use when test cases must move into a test management tool. Triggers include Xray, Zephyr, TestRail, Jira import file, export to Excel; Turkish "Xray'e aktar", "Jira'ya import", "Excel'e dök".
license: MIT
metadata:
  suite: qa-suite
  version: "0.6.0"
---

# Exporting test cases

The export is where test design meets the team's tooling. A wrong column mapping, a lost requirement link or broken Turkish characters silently destroy traceability. That is why the export is a validated script, not hand-written CSV.

## Inputs

- `qa/test-cases.json`, required (schema in `references/data-model.md`)
- `qa/requirements.json`, strongly recommended. Its `external_id` values (Jira keys such as `SHOP-123`) become real requirement links in Xray and Zephyr. Without them, the links survive only as labels.

If the test cases exist only as prose or a table in the conversation, first convert them into `qa/test-cases.json`. The `designing-test-cases` skill does this through its compact format.

If they live in Excel, TestRail or another tool's CSV (for example, "move our Excel tests into Xray"), import them first with the `reviewing-test-cases` skill:
1. Run `../reviewing-test-cases/scripts/import_tests.py`, then `qa_compact.py --lenient`.
2. Run `review_tests.py`. Otherwise vague steps and missing expected results migrate into Jira unchanged.
3. Export the result.

When all requirements come from one Jira story or epic, derived and split requirements can carry that story's key as their `external_id`. The Xray/Zephyr link then points to the story. The exporter writes each key only once per test.

## Workflow

1. **Pick the target and the options.** Ask only for what you cannot infer:
   - The tool: Xray, Zephyr Scale, TestRail, Azure DevOps Test Plans, Qase, Excel, CSV or Markdown.
   - Whether the requirements have Jira keys. If they do not, offer to add them to `external_id` first.
   - The Zephyr folder, the Xray component, and whether the project uses non-default priority names.
   - The delimiter for Excel users in a Turkish locale: `;`.

2. **Run the traceability check first** when the `tracing-requirements` skill is available. Exporting orphan, duplicate or broken-link tests just moves the mess into Jira:
   ```bash
   python ../tracing-requirements/scripts/build_rtm.py --requirements qa/requirements.json --tests qa/test-cases.json --out-dir qa
   ```

3. **Export:**
   ```bash
   # Xray (Jira)
   python scripts/export_tests.py --tests qa/test-cases.json --requirements qa/requirements.json \
       --format xray --out qa/exports/xray.csv
   # Zephyr Scale
   python scripts/export_tests.py --tests qa/test-cases.json --requirements qa/requirements.json \
       --format zephyr --folder "Checkout/Coupon" --out qa/exports/zephyr.csv
   # TestRail ("Test Case (Steps)" template), Azure DevOps Test Plans, Qase
   python scripts/export_tests.py --tests qa/test-cases.json --requirements qa/requirements.json --format testrail --folder "Checkout > Coupon" --out qa/exports/testrail.csv
   python scripts/export_tests.py --tests qa/test-cases.json --format azure-devops --area-path "Shop\Web" --out qa/exports/ado.csv
   python scripts/export_tests.py --tests qa/test-cases.json --requirements qa/requirements.json --format qase --folder "Coupon" --out qa/exports/qase.csv
   # Excel workbook (steps sheet + summary sheet), generic CSV, Markdown document
   python scripts/export_tests.py --tests qa/test-cases.json --requirements qa/requirements.json --format xlsx --out qa/exports/test-cases.xlsx
   python scripts/export_tests.py --tests qa/test-cases.json --format csv --delimiter ";" --out qa/exports/test-cases.csv
   python scripts/export_tests.py --tests qa/test-cases.json --requirements qa/requirements.json --format markdown --out qa/exports/test-cases.md
   ```

   Useful options:
   - `--only TC-001,TC-007` or `--tag smoke`, for an incremental or partial export
   - `--include-deprecated`
   - `--priority-map '{"medium":"Normal"}'`
   - `--test-type Manual`, `--component`
   - `--folder "A/B"` or `"A > B"`, written in each tool's own folder syntax (Xray, Zephyr, TestRail, Qase)
   - `--xray-links columns` (Xray Server/DC: one column per requirement key)
   - `--zephyr-steps rows|single`, and `--zephyr-data inline` when the Zephyr wizard offers no Test Data target
   - `--area-path`, `--assigned-to` (Azure DevOps)
   - `--list-delimiter` (default `;` for Xray, `,` for Zephyr)
   - `--bom`
   - `--lang tr|en` (column headers of csv, xlsx and markdown)

   The script validates before writing and exits 1 without writing anything if a test has no ID, no title or no steps. It warns about missing Jira keys, unknown requirement IDs and tests with no requirement. It also warns about documented importer limits and required fields: Xray Cloud 1000 issues per file, TestRail 10 MB, Azure DevOps 20 MB, 128-character titles, and an empty Area Path.

4. **Give import instructions** tailored to the target: read `references/xray.md`, `references/zephyr-scale.md` or `references/other-tools.md` (TestRail, Azure DevOps, Qase). Always recommend a **trial import of 2–3 tests** in a sandbox project first. Importers differ between versions, and a bulk import with the wrong mapping is painful to undo.

5. **Report to the user:**
   - The file paths.
   - Test and step counts.
   - The warnings, such as requirements without Jira keys.
   - The field-mapping table for their tool.
   - The re-import caveat: importers create new issues, so export only new tests next time.

## Encoding and locale

- Xray, Zephyr, TestRail, Azure DevOps and Qase: plain UTF-8, delimiter `,` by default. Choose UTF-8 in the importer.
- Generic CSV for Excel: written **with a BOM** automatically, so Excel shows `ç ğ ı İ ö ş ü` correctly. Excel in a Turkish locale expects `;` as the delimiter, so use `--delimiter ";"`.
- `.xlsx` avoids delimiter and encoding problems completely. Prefer it for humans, and CSV for importers.

## Files

- `scripts/export_tests.py`: exporter for xray, zephyr, testrail, azure-devops, qase, csv, xlsx and markdown. Standard library only; it includes a minimal xlsx writer.
- `references/xray.md`: Xray Test Case Importer mapping, steps, limits and pitfalls, plus the JUnit results path (Playwright `test_key`). Like the other references, it names the vendor pages it was checked against and the date.
- `references/zephyr-scale.md`: Zephyr Scale import mapping, the two step layouts and pitfalls.
- `references/other-tools.md`: TestRail, Azure DevOps Test Plans and Qase import mapping, what is certain and what to verify.
- `references/data-model.md`: shared JSON schema.
