# Data migration testing guide

## Contents
1. Migration types and what goes wrong
2. The mapping specification is the requirement
3. Source data profiling (with Turkish encoding, decimal and date traps)
4. Reconciliation levels
5. Full comparison vs sampling
6. Mock migrations and rehearsals
7. Cutover, delta, idempotency and rollback
8. Post-migration functional regression
9. Performance with production volumes
10. Data privacy with production extracts
11. Defect classification
12. Sign-off criteria (template)
13. reconcile.py: how it works and its limits
14. Reconciliation checks as test cases (REQ → TC → results → RTM)

---

## 1. Migration types and what goes wrong
| Type | Examples | Typical risks |
|---|---|---|
| System replacement | legacy core banking or ERP → new package | semantic mapping (codes, statuses, product types), history, open transactions |
| Database upgrade or change | Oracle 11g → 19c, SQL Server → PostgreSQL | data types (NUMBER → NUMERIC, DATE with time), collations and sorting, NULL vs '' (Oracle), encodings |
| Cloud move / re-platforming | on-premises → managed database or data warehouse | volume and time windows, network, time zones, loss of implicit behaviour (triggers, jobs) |
| ETL/ELT pipelines (recurring) | nightly loads into a warehouse or lake | incremental logic, late-arriving data, duplicates, schema drift |

The damage is quiet. Wrong data rarely crashes anything: a balance that is 100 times too large, a customer in the wrong branch or a closed account shown as passive all look like valid data. That is why testing reconciles **every row** against an independent expectation, instead of only clicking through screens.

**Independence of the test oracle.** Compute the expected values from the mapping specification, not by reusing the migration code or its SQL. If the test uses the same logic as the migration, it repeats the same mistakes and passes. `reconcile.py` with a mapping file written from the specification is an independent implementation.

## 2. The mapping specification is the requirement
A mapping specification is usually a table like this, one per target entity:

| Target column | Source column(s) | Rule | Null/blank rule | Notes / owner |
|---|---|---|---|---|
| customer_id | MUSTERI_NO | trim, strip leading zeros | never null; reject row | key |
| full_name | AD + ' ' + SOYAD | collapse spaces, upper case with Turkish rules | reject if both empty | |
| balance | BAKIYE | decimal comma text → DECIMAL(18,2), HALF_UP | 0.00 | money: control total |
| status | DURUM | A→ACTIVE, P→PASSIVE, K→CLOSED; other codes → reject | reject | |
| — | FAKS | **not migrated** (no longer used, agreed on 2026-05-10) | | data owner |

Review it like any requirement (the `analyzing-requirements` skill). Typical gaps:
- **Unmapped source fields** with no decision. Every source field needs a target, or an explicit "not migrated" with a reason and an owner. Otherwise data disappears and nobody is accountable.
- **Incomplete code lists.** What happens to a code that is not in the list: reject, a default, or a special "UNKNOWN"?
- **Missing null, blank and default rules.** Is an empty legacy e-mail migrated as NULL or ''?
- **Ambiguous formats.** "Date is converted" does not say from which format. "Amount is rounded" does not say how (HALF_UP or HALF_EVEN) or to how many decimals.
- **Unstated scope.** Closed records, test records, history depth, soft-deleted rows.
- **Derived fields.** How is the new system's value calculated, for example a risk segment? Which data does it depend on?
- **Rejects.** Where do rejected rows go, who reviews them, and do they count as "missing"?

Every rule becomes a testable requirement and a column in `mapping.json`. Also test the migration logic on a small **crafted edge-case dataset** before the first full run: one row per rule and per boundary (the longest name, an empty field, an unknown code, 29.02, a negative amount, a Turkish character in every position). Full reconciliation finds what the real data contains; a crafted set proves that rules work for data you have not seen yet.

## 3. Source data profiling
Profile before the first mock migration. Use section 0 of `assets/reconciliation-queries.sql`, or an extract. For each column, record the null and blank count, distinct values, minimum and maximum, the length distribution and the top values. For each entity, record duplicate keys and orphans.

### Encoding (Turkish)
| Code page | Where it appears | Note |
|---|---|---|
| Windows-1254 (cp1254) | Windows-era Turkish applications, CSV exports from Excel, SQL Server `Turkish_CI_AS` VARCHAR columns | Turkish letters at 0xD0/0xF0 (Ğ ğ), 0xDD/0xFD (İ ı), 0xDE/0xFE (Ş ş) |
| ISO-8859-9 (Latin-5) | Unix/Oracle legacy systems (`WE8ISO8859P9`) | same letter positions as cp1254; differs only in 0x80–0x9F (cp1254 has €, quotes etc. there) |
| IBM 857 / EBCDIC 1026 | DOS-era applications / mainframes | needs explicit conversion |
| UTF-8 | modern targets | Turkish letters take 2 bytes: watch VARCHAR(n) byte-length truncation |

What mojibake tells you (the script's hints detect these):
| Target shows | Meaning |
|---|---|
| `Ä°BRAHÄ°M`, `ÅžAHÄ°N`, `Ã‡`, `Ã¼` | UTF-8 bytes were decoded as cp1252/cp1254/Latin-1 (double encoding) |
| `ÝBRAHÝM`, `ÞAHÝN`, `ð`, `ý` | cp1254 bytes were decoded as Latin-1/cp1252. Ç, Ö and Ü survive this one, so the damage is easy to overlook |
| `?BRAH?M`, `�` | characters were lost when converting to a code page without Turkish letters; this is not reversible |
| `IBRAHIM SAHIN` | transliteration to ASCII, deliberate or accidental; check the spec |

**Turkish casing.** Generic `upper('i')` gives `I`, but Turkish needs `İ`, and `lower('I')` must give `ı`. Culture-insensitive code or a non-Turkish collation gives "ZEYNEP ÇELIK" instead of "ZEYNEP ÇELİK". Case-insensitive search and unique constraints also change behaviour under a Turkish collation (the "Turkish I problem"). Use `upper_tr`/`lower_tr` in the mapping when the specification demands Turkish rules, and plain `upper`/`lower` for ASCII identifiers such as e-mail addresses. Applying `lower_tr` to an e-mail turns `I` into `ı`.

### Decimal format
`1.234,56` (Turkish) versus `1,234.56` (English). A loader that uses the wrong locale either removes the comma (`123456` → ×100) or stops at it (`1.234`). Detect this in profiling: text amounts that contain a comma. Keep money in DECIMAL/NUMERIC end to end. Binary floating point cannot represent 0.10 exactly, so sums drift and 0.01 differences appear. The script uses Python `Decimal` and never float.

### Dates
- A day/month swap (dd.MM ↔ MM/dd) fails loudly only when the day is above 12. For days 1–12 it silently creates a valid but wrong date. The field-level comparison catches it; count checks and "does it parse" checks do not.
- Two-digit years need a pivot rule (`01.01.45`: 1945 or 2045?).
- Time zones: a date stored as a midnight timestamp and converted to UTC moves to the previous day (Türkiye is UTC+3). Birth dates and value dates are the usual victims.
- Impossible legacy values (`00.00.0000`, `31.02.1990`, `01.01.1900` used as "unknown") need an explicit rule.

### Other profiling targets
Leading zeros in keys (`0001017` vs `1017`), trailing spaces in CHAR columns, control characters and line breaks inside text fields (these break CSV extracts), negative amounts in positive-only fields, orphans, and duplicates that differ only by case or spaces.

## 4. Reconciliation levels
Use them together. Each level catches what the one before it misses.

| Level | Question | Catches | Misses |
|---|---|---|---|
| 1. Counts | same number of rows per entity? | lost batches, doubled loads | a missing row plus an extra row (net zero) |
| 2. Control totals per group | same sum of money (and count) per branch, product, currency, month? | ×100 errors, lost groups, wrong grouping | offsetting errors, text fields |
| 3. Key-set comparison | which keys are missing, and which are unexpected? | rejects, filters, test records, key transformation errors | content errors |
| 4. Row hash / field-level comparison (with the transformation applied) | does every field equal its expected value? | encoding, rounding, date swaps, wrong codes, truncation | cross-row rules |
| 5. Referential integrity in the target | do all foreign keys resolve? | orphans, wrong load order, disabled constraints | |
| 6. Business rules | balance = opening + sum of transactions? CLOSED ⇒ balance 0? | semantic errors spanning tables | |
| 7. Application-level | does the new system work with the data? | see §8 | |

Levels 1–4 are what `reconcile.py` does (for one entity at a time). Levels 5–6 are SQL (`assets/reconciliation-queries.sql` sections 5–6). Level 7 is functional testing.

Control totals have to be computed from **transformed** source values. If the mapping rounds to 2 decimals, compare the sum of the rounded source values, not the raw ones. With row-level findings, a control-total difference is a consequence: file the row-level causes. Without row-level findings, suspect the scope (filters, rejects) or the totals query itself.

## 5. Full comparison vs sampling
**Prefer a full comparison.** It is automated and cheap compared with the cost of a wrong balance, and it finds rare defects: a date swap in 0.2% of rows, one code that maps wrongly.

Sample when the check needs a human (opening records in the new UI, comparing printed statements), or when the volume truly prevents a full comparison. Size the sample with arithmetic, not by feel:
- **Zero-failure acceptance sampling.** To claim with confidence C that the defect rate is below p, you need n = ln(1−C) / ln(1−p) random samples, all of them correct. For 95% confidence that fewer than 1% of rows are wrong, n = 299. For fewer than 0.1%, n = 2,995.
- **Rule of three.** Zero defects in n random samples gives an approximate 95% upper bound of 3/n on the defect rate.
- **Stratify.** Take a random sample within each risky stratum (every status, product, branch, currency, very old records, records with Turkish characters or empty fields) and add the edge cases from profiling. A purely random sample is dominated by the most common, least risky records.
- A sample can never prove that nothing is missing. Keys and totals always need the full population.

## 6. Mock migrations and rehearsals
Plan several full mock migrations (typically 3 or more) with production-like volumes. Each one uses the latest source snapshot and the latest version of the migration code.

For every mock:
- **Time every step:** extract, transform, load, index and constraint rebuild, statistics, reconciliation, and the business checks. Compare the total with the cutover window. Leave a margin for one failed step and a re-run.
- **Reconcile fully,** and store the report per mock (`reconciliation-mock1.md`, `-mock2.md`, …). The trend shows whether defects are converging.
- **Track the data defects found per mock.** New defect types in the last mock mean you are not ready.
- **Freeze the migration code** before the final dress rehearsal. That rehearsal follows the cutover runbook step by step, including the communications and the go/no-go meeting.

## 7. Cutover, delta, idempotency and rollback
- **Big bang vs phased.** A phased migration (by branch or by product) needs coexistence tests: can the data of migrated and non-migrated entities be used together (transfers between them, consolidated reports)?
- **Delta or incremental migration.** Test that changes made after the initial load arrive exactly once:
  - inserts, updates and **deletes** (timestamp-based deltas miss hard deletes);
  - changes made during the extract;
  - clock differences between servers;
  - rows updated twice within one delta window.
  Reconcile after the delta in the same way as after the initial load.
- **Idempotency and restart.** Kill the load at step N and restart it. Then check for duplicate keys (the script reports them), doubled control totals, and half-applied batches. Loading the same batch twice has to be rejected or produce the same result.
- **Rollback.** Rehearse it and time it:
  - Can the legacy system resume?
  - What happens to transactions created in the new system after go-live (reverse sync, manual re-entry)?
  - Where is the point of no return, and who decides?
  A rollback plan that has never been rehearsed is not a plan.
- **Go/no-go.** Check the reconciliation verdict and the sign-off criteria (§12), the open defects by severity, the timing, and whether rollback is ready.

## 8. Post-migration functional regression
Passing the data checks does not mean the application works. Test at least these:
- **Open old records** of every type, status and age, including records with Turkish characters, maximum-length fields and empty optional fields.
- **Edit and save migrated records.** Validation that the bulk loader bypassed fires now: mandatory fields, formats and state rules.
- **Continue the processes:** accrue interest on migrated accounts, close a migrated account, reverse a migrated transaction.
- **Reports:** period-end, regulatory and statement reports on migrated data. Compare them with the same reports from the legacy system for the same date.
- **Search and sorting** with Turkish characters (the collation).
- **Integrations** that read migrated data: IDs, code values, formats.

Design these tests with the `designing-test-cases` skill, and choose the records from what profiling found.

## 9. Performance with production volumes
- **Load throughput:** rows per second for each step, extrapolated to the full volume and checked in a full rehearsal. Extrapolation misses index growth and lock contention.
- **After bulk loads:** rebuild indexes and gather statistics. Query plans in the new system can differ completely from those in a small test database.
- **Application performance** on production-size migrated data: search, lists and reports (the `testing-nonfunctional` skill).
- **Reconciliation performance.** The checks themselves must fit in the cutover window. Run heavy comparisons in the database (hashes, anti-joins), and keep extracts for evidence.

## 10. Data privacy with production extracts
Migration testing is where production personal data most often leaks into test environments. Under KVKK (Law No. 6698) and GDPR, test use needs a lawful basis and minimisation:
- **Prefer masked or synthetic data** for developing and unit-testing the transformation logic. Use real data only where fidelity is essential (the final mocks and the dress rehearsal), in an environment with production-grade controls.
- **Masking must preserve what the tests need:**
  - format and validity (a Turkish ID number with valid check digits, an IBAN with a valid mod-97);
  - distributions and edge cases (Turkish characters, lengths, nulls);
  - **deterministic** mapping, so that the same input gives the same masked value in every table and file. Otherwise joins and reconciliation break.
  Masking only one side of a comparison produces nothing but mismatches: mask both sides with the same function, or reconcile before masking inside the secure zone.
- **Access:** named people only, logged access, no copies on laptops, and no extracts in e-mail, tickets, chat or repositories.
- **Reports leave the secure zone with keys only.** Before sharing a report with example values, redact personal fields, or reduce `--max-examples`.
- **Retention:** delete extracts and staging copies at the end of the project, and record the deletion.

## 11. Defect classification
| Class | Evidence | Typical fix | Owner |
|---|---|---|---|
| Source data quality | invalid or unknown codes, impossible dates, duplicates or orphans in the source, text already broken in the legacy system | cleanse in the source, add a rule, or accept | data owner |
| Mapping specification gap | a value no rule covers, an ambiguous rule, a source column with no decision, a missing null rule | update the specification, then the code | analyst and data owner |
| Transformation defect | rule-shaped mismatch: ×100, rounding, day/month swap, wrong code map, casing | fix the transformation code | migration developers |
| Load defect | missing rows (rejects), duplicates (re-runs), truncation, encoding broken on write, orphans because constraints were disabled | fix the load or restart logic | migration developers / DBA |
| Test (reconciliation) defect | wrong expected rule, a wrong extract, a comparison without the transformation | fix the test; tell the team | test team |
| Environment | wrong snapshot, incomplete extract | redo the run | environment owner |

Group by root cause. A single wrong decimal parsing rule gives thousands of mismatches: file **one** defect with the count, sample keys and the rule, not thousands. Severity follows the business impact (money, legal and customer-facing data first), not the row count.

## 12. Sign-off criteria (template)
Agree on these before the first mock and record them in the test plan:

| # | Criterion | Tolerance |
|---|---|---|
| 1 | Source columns without a mapping decision | 0 |
| 2 | Keys missing in the target (excluding documented scope exclusions) | 0 |
| 3 | Unexpected keys in the target | 0 |
| 4 | Duplicate keys in the target | 0 |
| 5 | Control-total difference on money, per currency and group | 0.00 |
| 6 | Field mismatches on critical columns (keys, money, status, dates, identity) | 0 |
| 7 | Field mismatches on non-critical columns | 0, or documented exceptions with an owner |
| 8 | Orphans in the target | 0 |
| 9 | Business-rule checks (balance = transactions, status consistency) | 0 violations |
| 10 | Rehearsal duration | ≤ cutover window minus the agreed margin |
| 11 | Rollback rehearsed and timed | yes |
| 12 | Post-migration regression suite | passed; no open critical/high defects |

**Accepted exceptions** are listed one by one, each with a key, a column, a reason, an owner and a date. Put them in `mapping.json` under `accepted_exceptions`. The report then shows them every time, and it flags an exception that no longer occurs as "not observed", so that stale exceptions get removed.

## 13. reconcile.py: how it works and its limits
**How it works.**
1. It reads the source once. It applies the mapping to each row and keeps `{key: expected values}` in memory.
2. It streams the target. Each target row is compared with its expected values, and the matched source entry is released.
3. It re-reads the source briefly to fetch raw values for the examples.

Money is summed with `Decimal`. Numeric columns (the `decimal` op, `"type": "decimal"`, or `--sum` columns) compare within `--tolerance`. Text compares exactly.

**Limits. Be honest about them in the report:**
- **Memory.** Plan for about 0.5–1 KB per source row: roughly 0.5–1 GB for 1 million rows of about 10 columns. A measured run of 200,000 rows with 7 transformed columns peaked at about 105 MB and took about 13 s. Above a few million rows, reconcile in the database with the SQL templates, or export `key,row_hash` from both sides and compare those two small files.
- **CSV only**, one entity per run, and one key definition. Cross-table checks (orphans, balance = transactions) need SQL.
- **Exact matching.** There is no fuzzy matching of keys. A key transformation error shows up as "missing" plus "unexpected"; the report points this out when the keys look alike.
- **Numbers.** Automatic decimal parsing is ambiguous for `1.234` (the script reads it as 1.234). Force the separator (`decimal:2:,`) for legacy Turkish amounts.
- **Dates and times** are compared as text after the transformation. Export the target in the same format; time zones are not handled.
- **Hints are heuristics.** They suggest a class of defect; confirm it before filing.
- **Implicit mappings.** Without a mapping, or for target columns that are not in the mapping, same-named columns are compared as they are. The report lists these, so that they can be confirmed in the specification.
- **The extracts must be right.** Check that the row counts of the extracts equal the table counts. A truncated extract gives a clean but meaningless PASS.

## 14. Reconciliation checks as test cases (REQ → TC → results → RTM)
A reconciliation report on its own never reaches the RTM or the completion report. `reconcile.py --compact-out` therefore turns every check into a test case that traces to a requirement, and `--results` writes the verdict of each check into `qa/results.json` under that TC ID.

| Check id | Test case | Fails when (after accepted exceptions) |
|---|---|---|
| `row_count` | row counts, overall and per `--group-by` | the counts differ, and the difference is not fully covered by accepted exceptions |
| `key_set` | no missing, unexpected or empty keys | any missing, unexpected or empty key |
| `duplicate_keys` | no duplicate keys on either side | any duplicate key in the source or the target |
| `column:<col>` | one per compared target column | any field mismatch or transform error, or the column is absent from the target file |
| `total:<col>` | one per `--sum` column | overall or per-group difference above `--total-tolerance` |
| `coverage` | mapping coverage and null rates (with `--mapping` only) | a source column without a decision, or a null-rate change of 1 percentage point or more that no row-level finding explains |

- **Consequences fail too.** In the trial, the missing, unexpected and duplicate rows also fail `row_count`, and the ×100 balance also fails `total:balance`. Link each defect to the root-cause test case and treat the others as consequences (§4). Counts that are equal while keys are missing and unexpected pass `row_count`; `key_set` catches that case.
- **Consistency with the verdict.** Every failing sign-off rule fails at least one check, and every accepted exception is honoured by the checks too, so a PASS verdict leaves no failed reconciliation test case behind.
- **Privacy.** `results.json` goes into repositories and reports. Its entries therefore carry keys, counts, totals and hints only, never field values. The values stay in the Markdown report inside the secure zone (§10).
- **Stable IDs.** A check keeps its TC ID across regenerations: through the `# reconcile-tc-map:` header line of the generated file, and through the `design_ref` `reconcile:<object>:<check>` in `qa/test-cases.json`. Use the same `--object` for design and run, one per migration object. A check that disappears (a column removed from the mapping, a dropped `--sum`) stays as a `deprecated` test case, so that its ID is never reused.
- **What is not covered.** These test cases cover reconciliation levels 1–4 of one entity. Referential integrity, business rules, reject handling (negative cases), rehearsal timing and application-level regression still need their own test cases.
