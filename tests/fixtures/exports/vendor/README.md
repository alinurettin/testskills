# Vendor re-exports

After importing `examples/import-kit/<tool>.csv` into the real tool, export the imported cases from the
tool and save the file here. From then on, `tests/test_export_golden.py` checks every CI run against it.
Until a file exists, that check is skipped.

| Tool | Folder | What to export |
|---|---|---|
| Xray | `xray/` | Jira issue search `project = KIT AND issuetype = Test` → Export → CSV (all fields) |
| Zephyr (Scale) | `zephyr/` | the imported test cases as CSV. If the tool only offers Excel, save the sheet as "CSV UTF-8". |
| TestRail | `testrail/` | Test Cases → Export → CSV, all columns, including the step columns |
| Azure DevOps | `azure-devops/` | Test Plans → suite → Column options: add Priority → Export test cases to CSV |
| Qase | `qase/` | Repository → `…` → Export Data → CSV (the current format, not the "old format") |

Name the file after the tool version and date, for example `xray/xray-cloud-2026-10-02.csv`. Keep only
synthetic data: the kit contains no personal data, so the re-export should not either.

## What is checked

- **Columns:** every column our export writes (e.g. `Priority`, `Coverage`) must exist in the tool's
  file under a known name. The names are listed in `VENDOR_SPEC` in the test.
- **Values:** for enumerated columns such as priority, status, type and severity, every value we write
  must appear in the tool's file.

A difference means the exporter's defaults do not match the tool. Either fix the exporter default, or,
when the value was translated on purpose in the import wizard, record it in `<tool>/accepted.json`:

```json
{"Priority": {"Highest": "High", "Medium": "Normal"}}
```

The keys are our column names, and each maps our value to the value the tool shows.
