---
name: exporting-test-cases
description: Exports QA Suite test cases (test-cases.json) into import-ready files for test management tools. Supports Xray Test Case Importer CSV (one row per step, grouped by Test ID, requirement links via Jira keys), Zephyr Scale CSV (step rows or plain-text script), Excel .xlsx, generic CSV and a Markdown review document, with validation, priority mapping and Turkish-safe encoding. Use this whenever the user wants to move test cases into Jira, Xray, Zephyr, Excel or Confluence, or asks for an import file, a CSV/XLSX of tests, or a printable or reviewable test case document. Also use it for Turkish requests such as "Xray'e aktar", "Zephyr'e yükle", "Jira'ya import", "Excel'e dök", "test case'leri dışa aktar", "import dosyası hazırla".
license: MIT
metadata:
  suite: qa-suite
  version: "0.5.0"
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
   - The tool: Xray, Zephyr Scale, Excel, CSV or Markdown.
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
   - `--zephyr-steps rows|single`
   - `--list-delimiter`
   - `--bom`
   - `--lang tr|en` (column headers of csv, xlsx and markdown)

   The script validates before writing and exits 1 without writing anything if a test has no ID, no title or no steps. It warns about missing Jira keys, unknown requirement IDs and tests with no requirement.

4. **Give import instructions** tailored to the target: read `references/xray.md` or `references/zephyr-scale.md`. Always recommend a **trial import of 2–3 tests** in a sandbox project first. Importers differ between versions, and a bulk import with the wrong mapping is painful to undo.

5. **Report to the user:**
   - The file paths.
   - Test and step counts.
   - The warnings, such as requirements without Jira keys.
   - The field-mapping table for their tool.
   - The re-import caveat: importers create new issues, so export only new tests next time.

## Encoding and locale

- Xray and Zephyr: plain UTF-8, delimiter `,` by default. Choose UTF-8 in the importer.
- Generic CSV for Excel: written **with a BOM** automatically, so Excel shows `ç ğ ı İ ö ş ü` correctly. Excel in a Turkish locale expects `;` as the delimiter, so use `--delimiter ";"`.
- `.xlsx` avoids delimiter and encoding problems completely. Prefer it for humans, and CSV for importers.

## Files

- `scripts/export_tests.py`: exporter for xray, zephyr, csv, xlsx and markdown. Standard library only; it includes a minimal xlsx writer.
- `references/xray.md`: Xray Test Case Importer mapping, steps and pitfalls.
- `references/zephyr-scale.md`: Zephyr Scale import mapping, the two step layouts and pitfalls.
- `references/data-model.md`: shared JSON schema.
