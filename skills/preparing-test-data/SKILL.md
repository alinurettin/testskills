---
name: preparing-test-data
description: Prepares test data by deriving each test case's needs, generating deterministic synthetic CSV/JSON with referential integrity, edge values and valid Turkish IDs (TCKN, VKN, TR IBAN, +90 phones), and masking production extracts under KVKK/GDPR. Use when tests need seed, fixture or bulk data. Triggers include test data, synthetic data, fake customers, data masking; Turkish "test verisi hazırla", "sahte veri üret", "veri maskeleme".
license: MIT
metadata:
  suite: qa-suite
  version: "0.7.1"
---

# Preparing test data

**Status: experimental (no blind trial yet).** The scripts are covered by unit tests and demos; a blind trial is planned for 0.7.

Most "flaky" tests and many blocked test cycles are really data problems: the record was used up, another test changed it, the value missed the boundary, or nobody knew what the environment contained. This skill treats test data as a versioned test asset. **Synthetic data comes first.** It derives exactly what each test needs, generates it reproducibly from a seed, and uses masked production data only when the data owner has approved it.

## Language
Match the user's language (`--lang tr|en` for reports and messages). Field names, rule names and file formats stay as they are.

## Reading plan
- This file covers the workflow.
- Read `references/test-data-management.md` when:
  - choosing between synthetic and production-derived data;
  - writing masking rules or answering KVKK/GDPR questions;
  - designing per-test isolation and seeding;
  - planning environment refreshes;
  - handling Turkish formats, casing and sorting.
- The schema and rule syntax is in each script's `--help`.

## Prerequisites and safety
- **Use synthetic data by default.** Use production data only when a defect class truly needs it. Even then, whether to use it is a **compliance decision** (data owner, DPO, legal), not a tester decision. State the need and propose the minimum columns and rows; do not extract data yourself.
- **ID policy.** Generated TCKN, VKN, IBAN and phone numbers are valid by algorithm only. Türkiye has no reserved fictional ranges, so they can belong to real people, companies, accounts or subscribers. Checksum-valid synthetic values are allowed in **test environments** and must come from a generator (`gen_data.py`, `mask_data.py` `fake`, or `check_ids.py --generate` in designing-test-cases). Never copy them from the internet or production, and never load them into production or into systems shared outside the test boundary. Route test SMS, e-mail and payments to sandboxes. Generated e-mails always use `example.com` or `example.test`.
- **Pseudonymised data is still personal data.** Masking with `hash` or `fake` needs a secret in an environment variable (never in a file or the repository). Keep the secret outside the test environment.
- Mask inside the production security zone, and move only the masked output.
- Python 3.10+ standard library; no installs.

## Workflow

```
- [ ] 1. Derive data needs from the test cases (exact vs any-valid)
- [ ] 2. Choose the source per need (fixture, synthetic, masked extract)
- [ ] 3. Write fixtures for exact values; generate synthetic data from a schema + seed
- [ ] 4. (Only if approved) mask the production extract; review the report
- [ ] 5. Load with isolation: per-run keys, API seeding, idempotent setup, cleanup by run tag
- [ ] 6. Record datasets in the data catalog; agree the refresh rule
```

### 1. Derive data needs
```bash
python scripts/data_needs.py qa/test-cases.json --lang tr --out qa/test-data/data-needs.md \
    --schema-out qa/test-data/schema.json
```
The script groups `test_data` and step data per test case and classifies each need:
- **exact**: from boundary-value, partition, decision-table, state or pairwise techniques. The value *is* the test, so it goes in a reviewed fixture, never a random generator.
- **any valid**: the test needs *a* record of that shape, which can be generated.

It lists test cases that document no data, and applies the ID policy to the values:
- **ERROR** (exit code 1): data that looks real, such as e-mails outside the reserved example domains (`example.com`, `example.org`, `*.test`). Replace it.
- **WARNING "verify synthetic origin"**: checksum-valid TCKNs or IBANs and mobile numbers. They are fine in test environments when a generator produced them. Confirm where each one came from, and replace any value that did not come from a generator.

The starter schema infers types from the observed values; widen its ranges to the real domain.

Also check what the test cases do not say, using §2 of the reference: cross-field rules, dates relative to "today", reference data versions, and consumable data (balances, stock, coupons).

### 2. Choose the source
Use the decision table in §3 of the reference. In short:
- fixtures for exact values;
- `gen_data.py` for any-valid and volume data;
- a masked extract only for defect classes that synthetic data cannot reach (legacy formats, migrations, reconciliation), and only with a recorded approval.

### 3. Generate synthetic data
Start from `assets/schema-example.json`: customers and accounts, with `accounts.customer_id` referencing `customers.id`.
```bash
python scripts/gen_data.py --schema qa/test-data/schema.json --validate-only
python scripts/gen_data.py --schema assets/schema-example.json --seed 42 --lang tr --out qa/test-data/ \
    --run-tag R42- --mark-edges --bom
python scripts/gen_data.py --schema customers.json --rows 5000 --seed 7 --format json --out data/customers.json
```
- **Types:**
  - `seq`, `first_name`, `last_name`, `full_name`, `email`, `uuid`, `ref`;
  - `phone_tr`, `tckn`, `vkn`, `iban_tr`, `city_tr`, `postcode_tr`;
  - `int`, `decimal`, `date`, `datetime`, `enum`, `bool`, `text`.
  The name lists include Turkish characters (Işıl, Çağrı, Gökçe, Şükrü).
- **Determinism:** the same schema and seed produce the same file. Put the seed in defect reports.
- **Integrity and uniqueness:** `ref` picks existing parent keys (from an earlier table or a CSV/JSON file). `unique` covers single or composite keys.
- **Edge rows:** `"edge": true` puts one boundary or awkward value into `edge_fraction` of the rows, in a single field per row. The values include min/max, 29 February, max length, empty (with `allow_empty`), `İ/ı` casing, surrounding spaces, alternative phone and IBAN notations, and leading-zero postcodes. `--mark-edges` records which field was changed. Decide the expected result for each edge value (accept, normalise, reject).
- Schema errors are reported together, with suggestions such as `did you mean 'decimal'?`. The exit code is 1.

### 4. Mask a production extract (only with approval)
```bash
# PowerShell: $env:MASK_SECRET = "<random 32+ chars>"   bash: export MASK_SECRET=...
python scripts/mask_data.py --in extract/customers.csv --rules qa/test-data/mask-rules.json \
    --out masked/customers.csv --report qa/test-data/mask-report.md --lang tr
python scripts/mask_data.py --in extract/accounts.csv --rules qa/test-data/mask-rules-accounts.json \
    --out masked/accounts.csv
```
Rules per column (see `assets/mask-rules-example.json`):
- **`drop`**: remove the column.
- **`redact`**: replace the value with a constant.
- **`hash`**: HMAC-SHA256 token. Use the same secret for every file of the extract so joins keep working.
- **`fake`**: a deterministic synthetic first name, last name, e-mail, phone, TCKN or IBAN. The same input always gives the same fake.
- **`generalize`**: date to year or year-month, number to bucket, postcode to province prefix.
- **`keep`**: leave the value as it is.

**Columns without a rule are dropped** (`--default drop`), so only reviewed columns get through. The script refuses to run without the secret. It reports uncovered or kept columns whose header (ad, soyad, tckn, iban, adres, email, phone, birth, doğum …) or values look like personal data. Exit code 1 means a decision is needed: an uncovered PII column was kept, or a rule names a column that does not exist. Review the report with the data owner. Also check quasi-identifiers (birth date + postcode + gender), rare values, free text, and orphans after the join (§5 of the reference).

### 5. Load with isolation
- **Keep tests independent of each other's data.** Each test creates what it changes, through a factory or builder with defaults, and seeds through the API rather than the UI. Load shared reference data once, read-only.
- **Make keys unique per run.** `--run-tag` goes into `seq` prefixes; build e-mails like `qa+<run>-<n>@example.test`. Setup must be idempotent. Clean up by run tag after the run, so a failed test's data stays available as evidence.
- **Give parallel workers disjoint data**, or run state-changing suites serially. Reset consumable data (balances, stock, quotas) before each run.

### 6. Catalog and refresh
Add every dataset to the data catalog (template in §9 of the reference). For each dataset record its ID, purpose and linked TCs, source, owner, version or seed, environments, refresh rule, personal-data status, and retention or deletion date. Agree when environments are refreshed; not in the middle of a test cycle. Regenerate the data after schema migrations. Link dataset IDs in the test cases' `preconditions` or `test_data`, so the impact of a data change is traceable.

## Turkish data checklist
- TCKN: 11 digits, first digit not 0, two check digits. VKN: 10 digits with a check digit. TR IBAN: 26 characters, mod 97. Mobile numbers: `+90 5xx`. Postcodes: 5 digits beginning with the plate code. **Store all of them as text:** Excel and numeric columns strip leading zeros.
- Test `ı/I` and `i/İ` casing in search, login and uniqueness (`IŞIK` vs `ışık`, `İPEK` vs `ipek`). Test Turkish collation order (`Çelik` sorts before `Deniz`, not after `Zeki`).
- Dates `dd.MM.yyyy`, decimal comma with thousands dot (`1.234,56`), `;` in Turkish-locale CSV, time zone UTC+3 without DST.
- Include Turkish characters in every field that crosses a system boundary (files, e-mail, PDF, SMS encoding, legacy Windows-1254 systems).

## Files
- `scripts/data_needs.py`: test-cases.json → data-needs report (exact vs any-valid per TC, PII-looking test data, TCs without data) and a starter schema.
- `scripts/gen_data.py`: schema + seed → deterministic CSV/JSON (single table or related tables), with checksum-valid TCKN/VKN/IBAN, `ref` integrity, `unique`, edge rows, run tags and Excel-friendly output.
- `scripts/mask_data.py`: CSV extract + rules → masked CSV and a Markdown report (keyed hash, deterministic fake, generalise, redact, drop; default drop; PII warnings; refuses to run without the secret).
- `scripts/tr_ids.py`: the suite's single TCKN/VKN/IBAN implementation (validation, synthetic generation, single-fault invalid variants), used by the scripts above.
- `assets/schema-example.json`: customers + accounts with a reference, uniqueness and edge fields.
- `assets/mask-rules-example.json`: masking rules for a Turkish customer extract.
- `references/test-data-management.md`: data needs, source choice, KVKK/GDPR masking and re-identification, isolation and seeding, refresh, Turkish specifics, data catalog, and the scripts' limits.
