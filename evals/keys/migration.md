# Trial: customer migration reconciliation (blind, planted defects)

Evaluator only. This key lives in `evals/keys/`, outside the trial folder, so that copying the
trial folder never copies the key. How to run and grade a blind trial: `evals/README.md`.

Reusable evaluation for the `testing-data-migrations` skill. Give an agent `mapping-spec.md`,
`legacy_customers.csv` and `new_customers.csv` from `evals/trial-migration/`, and ask it to test the migration and say whether
it can be signed off. **Do not show this file, or `tests/fixtures/testing-data-migrations/`,
to the agent.** The regression test `tests/test_testing_data_migrations.py` runs `reconcile.py`
with a correct mapping on these files and asserts that exactly the defects below are found.

Source: 40 customers (cp1254, `;`). Target: 41 rows (40 − 1 missing + 1 duplicate + 1 unexpected).

## Planted defects (the skill should find all nine)
| Key | Customer | Check | Planted defect | Class |
|---|---|---|---|---|
| A | 1017 | key set | missing in target (SERKAN POLAT, ANK, 9100.00) | load defect (reject/filter) |
| B | 9001 | key set | unexpected row "TEST MÜŞTERİ" (IST, 0.00) | load defect / scope (test record) |
| C | 1035 | key set | duplicate key in target (identical row twice) | load defect (non-idempotent re-run) |
| D | 1004 | full_name | `Ä°BRAHÄ°M ÅžAHÄ°N` instead of `İBRAHİM ŞAHİN` (UTF-8 decoded as cp1252) | load/encoding defect |
| E | 1022 | full_name | `GÜLÞEN IÞIK` instead of `GÜLŞEN IŞIK` (cp1254 decoded as cp1252; Ü survives) | extract/encoding defect |
| F | 1009 | balance | `4350.56` instead of `4350.57` (0.01 off) | transformation defect (rounding) |
| G | 1031 | balance | `345678.00` instead of `3456.78` (decimal comma lost, ×100) | transformation defect (decimal parsing) |
| H | 1012 | birth_date | `1990-05-03` instead of `1990-03-05` (day/month swapped) | transformation defect (date format) |
| I | 1027 | status | `PASSIVE` instead of `CLOSED` (K mapped wrongly) | transformation defect (code map) |

Consequences (not separate defects): balance control totals differ overall (+335121.21),
ANK −7100.00 (A −9100.00, C +2000.00), IST +342221.22 (G +342221.22, B 0.00), IZM −0.01 (F);
count per branch IST +1; target 41 rows vs source 40.

## Traps (correct data that naive comparisons flag as wrong)
- Keys have leading zeros in the source (`0001001` → `1001`).
- Turkish upper case: `Zeynep Çelik` → `ZEYNEP ÇELİK`, `Emine Aslan` → `EMİNE ASLAN`, `Deniz Sarı` → `DENİZ SARI`,
  `Mehmet  Ali Tuncer` → `MEHMET ALİ TUNCER` (Python/SQL `upper()` without Turkish rules gives `ÇELIK`,
  `EMINE`, `DENIZ`, `ALI` → false mismatches); `Işıl Kılıç` → `IŞIL KILIÇ`.
- Extra spaces in names: `  Zeynep` (1003), `Aslı ` (1036), `Mehmet  Ali` (1040).
- Upper-case e-mail with ASCII `I` (1003 `ZEYNEP.CELIK@EXAMPLE.COM`) must become `zeynep.celik@...`;
  Turkish lower-casing would give `zeynep.celık`. Leading/trailing spaces in an e-mail (1016).
- Empty e-mail (1007) stays empty; `FAKS` is deliberately not migrated.
- Balances `875,5` → `875.50`, `-150,00` → `-150.00`, `0,00`, `1.234.567,89` → `1234567.89`.
- `29.02.1992` is a valid leap day.
- Reading the source as UTF-8 fails (it is cp1254); reading it as Latin-1 produces mojibake
  expectations and false mismatches.

## Expected quality of a good answer
- Verdict: **not ready for sign-off** (FAIL), with all nine defects A–I reported and classified.
- Control-total differences explained as consequences of A, C, F and G, not filed as extra defects.
- No false positives from the traps above.
- Mentions that the data is personal data in real life (masking/KVKK), and that the next steps are
  the fixes, a re-run of the full reconciliation and post-migration regression tests.
