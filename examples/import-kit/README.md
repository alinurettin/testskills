# Import kit / Import kiti

Files for a real trial import into Xray, Zephyr, TestRail, Azure DevOps Test Plans and Qase. The walkthrough,
the checklists and the result table are in [docs/IMPORT-VERIFICATION.md](../../docs/IMPORT-VERIFICATION.md).

Xray, Zephyr, TestRail, Azure DevOps Test Plans ve Qase'e gerçek deneme import'u için dosyalar. Adımlar, kontrol
listeleri ve sonuç tablosu [docs/IMPORT-VERIFICATION.md](../../docs/IMPORT-VERIFICATION.md) içinde.

| File | Use |
|---|---|
| `xray.csv` | Xray Cloud Test Case Importer |
| `xray-server-dc.csv` | Xray Server/DC (one `Requirement Key n` column per link) |
| `xray-junit-sample.xml` | optional: Xray JUnit results import with `test_key` (edit the keys first) |
| `zephyr.csv` | Zephyr (Scale) CSV import, one row per step |
| `zephyr-inline-data.csv` | only if the Zephyr wizard offers no Test Data target |
| `testrail.csv` | TestRail, template "Test Case (Steps)", multiple rows |
| `azure-devops.csv` | Azure DevOps Test Plans, project/Area Path `QASuiteKit` |
| `qase.csv` | Qase, source "Qase.io" (V2) |
| `EXPECTED.md` | expected steps, values, links and folders per tool (generated) |
| `kit-requirements.json` | coupon requirements with Jira keys KIT-1..KIT-3 |
| `make_kit.py` | regenerates the CSV files and EXPECTED.md: `python examples/import-kit/make_kit.py` |

Source: `tests/fixtures/coupon/test-cases.json` (7 tests, 10 steps, synthetic data). Do not edit the CSV files by
hand: `tests/test_export_golden.py` fails when they differ from the current exporter output.
