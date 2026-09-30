---
name: testing-data-migrations
description: Tests data migrations, ETL pipelines and system replacements against the mapping specification. Profiles source data (duplicates, cp1254 vs UTF-8, decimal comma), reconciles source and target by script (counts, keys, field mismatches, control totals) and rehearses cutover and rollback. Use when data moves between systems. Triggers include data migration, ETL testing, reconciliation, cutover; Turkish "veri göçü testi", "migrasyon testi", "mutabakat".
license: MIT
metadata:
  suite: qa-suite
  version: "0.7.0"
---

# Testing data migrations

A migration is a one-way trip for data the business has collected over years. Defects hide in rows nobody looks at: a misparsed decimal comma turns 1.234,56 TL into 123.456,00; a code page error turns "İBRAHİM" into "Ä°BRAHÄ°M"; a re-run loads a batch twice. The application may still start, so functional tests alone will not find these. This skill tests the **data**: the mapping specification is the requirement, every source row is checked against its transformed expectation, and sign-off happens against tolerances agreed in advance.

## Language
Match the user's language (`--lang tr|en` for the report). Table, column and code names stay as they are.

## Reading plan
- This file covers the workflow.
- Read `references/migration-testing.md` before writing the strategy or sign-off criteria. It covers the mapping specification, profiling, reconciliation levels, sampling, rehearsals and cutover, delta and idempotency, regression, performance, privacy, defect classification, the limits of `reconcile.py`, and how its checks become test cases and results (§14).
- Use `assets/reconciliation-queries.sql` for database-side checks, and `assets/mapping-example.json` as the starting point for a mapping file.
- The script's full option list is at `python scripts/reconcile.py --help`.

## Prerequisites and safety
- **A mapping specification.** If none exists, writing one is the first deliverable: without it there is nothing to test against.
- **Extracts of source and target** as CSV, or read access to a staging database. Know each file's encoding, delimiter and decimal format before comparing; guessing them causes false alarms.
- **Production data is personal data.** Prefer masked or synthetic data for early rehearsals. When real extracts are unavoidable, use an approved, access-controlled environment, keep extracts out of repositories, tickets and chat, and delete them when the purpose ends (KVKK/GDPR). Reports should show keys, not personal details, when they leave that environment.
- Run SQL against read-only copies or replicas. Rehearse destructive steps (truncate, reload, rollback) only in environments built for them.

## Workflow

```
- [ ] 1. Mapping specification review (the requirement; gaps → questions)
- [ ] 2. Profile the source before the first mock migration
- [ ] 3. Strategy, sign-off criteria and reconciliation test cases (REQ → TC)
- [ ] 4. Mock migration: run, time, reconcile, write results (TC → qa/results.json)
- [ ] 5. Triage: classify every finding
- [ ] 6. Post-migration functional regression and performance
- [ ] 7. Cutover rehearsal: timing, delta, re-run, rollback, go/no-go
- [ ] 8. Sign-off report (RTM and completion report)
```

### 1. Mapping specification review
Read the mapping specification as a requirement document. Check it for these gaps and record each one as a question:
- **Every source field has a decision:** a target column, or an explicit "not migrated" with a reason.
- **Every target field has a source,** a constant or default, or a derivation rule.
- **Transformation rules are testable:** exact formats (dd.MM.yyyy → ISO), rounding (HALF_UP to 2 decimals?), the complete code list with the handling of unknown codes, the null and blank rule, the key rule (leading zeros?), and character encoding.
- **Scope rules:** which records are migrated (closed accounts, test records, history older than N years), and what happens to rejects.

Turn each transformation rule into a requirement (`analyzing-requirements` can lint them). Then encode the rules as `mapping.json` for the script (start from `assets/mapping-example.json`). Keep the JSON and the human specification in sync: the JSON is the executable version of the requirement.

### 2. Profile the source
Profile before the first run. Profiling findings are cheaper to fix in the source than as defects in the target. Use the profiling queries in `assets/reconciliation-queries.sql` (section 0), or look at the extract directly. Look for:
- nulls and blanks per column;
- duplicate business keys;
- orphans (children without a parent);
- codes outside the documented list;
- impossible dates and mixed date formats;
- decimal comma and thousands separators in text amounts;
- encoding: cp1254 / ISO-8859-9 vs UTF-8, and text that is already mojibake in the legacy system;
- leading and trailing spaces, and control characters.

Report each profiling finding to the data owner with a decision request: cleanse in the source, handle it in a transformation rule, or accept it as a documented exception.

### 3. Strategy, sign-off criteria and reconciliation test cases
Write these into the test plan (`planning-tests`) before the first mock run, so that nobody negotiates the tolerances after seeing the results:
- **Reconciliation levels** (`references/migration-testing.md` §4): counts; control totals per group; key-set comparison; field-level comparison with transformation; referential integrity; business rules.
- **Full comparison vs sampling.** Compare fully whenever the volume allows it; the script and the SQL are built for that. Use sampling only for checks that need a human, such as viewing records in the new UI, and size the sample deliberately (§5).
- **Explicit tolerances.** A typical baseline: 0 missing keys, 0 unexpected keys, 0 duplicates, 0 control-total difference on money, 0 field mismatches, except documented and accepted exceptions, each with an owner and a reason.

**Generate the reconciliation test cases now, before the first run**, so that migration verdicts reach the RTM and the completion report. The mapping file is enough; no extract is needed yet:
```bash
python scripts/reconcile.py --key customer_id --mapping qa/migration/mapping.json --sum balance --group-by branch \
    --object customers --req-map qa/req-map.json --req REQ-060 --tests qa/test-cases.json --lang tr \
    --compact-out qa/design/migration-customers.src.md
```
- The script writes one compact test case per check: row counts, key set (missing, unexpected and empty keys), duplicate keys, one per compared target column, one per `--sum` column (control total), and mapping coverage with null rates.
- Requirements come from `--req-map` (`{"default": "REQ-060", "checks": {"key_set": "REQ-061", "column:balance": "REQ-062"}}`). A specific check wins over its family (`"column"`, `"total"`), the family over `default`, and `default` over `--req`. Map money, key and status columns to their own requirements rather than one REQ for everything.
- TC IDs are stable. A regeneration reuses the IDs in the file's `# reconcile-tc-map:` header line and in the `design_ref` of `qa/test-cases.json`. Checks that were dropped stay in the file as `deprecated`.
- Append the file to `qa/test-cases.src.md` and run `qa_compact.py` (`designing-test-cases`). Regenerate after every mapping change instead of editing the cases by hand.
- All generated cases are positive. The RTM flags `NO_NEGATIVE` until reject handling (unknown codes, impossible dates, empty keys) is tested with a crafted edge-case dataset; design those cases with `designing-test-cases`.

### 4. Mock migration: run, time, reconcile, write results
Run the migration as in production: same scripts, same order, production-size volume. Measure how long each step takes. Then reconcile and write the results:
```bash
python scripts/reconcile.py --source extract/legacy_customers.csv --target extract/new_customers.csv \
    --key customer_id --mapping qa/migration/mapping.json --sum balance --group-by branch \
    --encoding-source cp1254 --delimiter-source ";" --object customers --lang tr \
    --out qa/migration/reconciliation-mock1.md --json qa/migration/reconciliation-mock1.json \
    --results qa/results.json --tc-map qa/design/migration-customers.src.md --run "Mock 1"
```
The script applies the mapping's transformations to each source row and compares the result with the target. The report lists:
- row counts, and duplicate keys on each side;
- keys missing in the target, and unexpected keys in the target;
- per-column mismatches, each with the source value, the expected value and the target value, and a hint (mojibake, ×100, rounding, day/month swap, Turkish casing, wrong code);
- control totals in Decimal, overall and per group, plus counts per group;
- null-rate changes, and source columns that have no mapping decision;
- a PASS/FAIL verdict: exit code 0 for PASS, 1 for FAIL.

`--results` writes `passed` or `failed` for each mapped test case into `qa/results.json` (`"source": "reconcile"`). Each entry gets up to three findings in `errors` (keys and hints only, never field values) and a `note` that names the report. Other entries and linked defect keys are kept. A mapped check the run did not produce becomes `not-run`, and a check without a test case is reported as a warning. `--tc-map` also accepts `qa/test-cases.json`.

Accepted exceptions go into `mapping.json` with a reason, so they stay visible in every report. The script holds the source in memory (about 0.5–1 KB per row). Above a few million rows, use the SQL templates inside the database, or compare "key + row hash" extracts.

### 5. Triage: classify every finding
Classify each finding before you file it. The class decides who fixes it:

| Class | Typical evidence | Owner |
|---|---|---|
| Source data quality | invalid codes, impossible dates, duplicate or orphan source rows | data owner (cleanse or accept) |
| Mapping specification gap | a value no rule covers; an ambiguous rule; an unmapped column | business analyst / data owner |
| Transformation defect | a rule-shaped mismatch: ×100, day/month swap, wrong code, casing | migration developers |
| Load defect | missing or duplicate rows, truncation, encoding broken on write, disabled constraints | migration developers / DBA |
| Test (reconciliation) defect | wrong comparison rule or extract | the test team |

Group rows by root cause. One misparsed decimal format may affect 40,000 rows, so file one defect that lists sample keys and the count (`reporting-test-results`). Link the defect key to the root-cause test case (the column or key-set check) in `qa/results.json`; row-count and control-total failures that follow from it are consequences, not extra defects. Re-run the full reconciliation, with `--results`, after every fix, because fixes to transformations often shift other rows.

### 6. Post-migration functional regression and performance
Reconciled data can still break the application. Test the application on migrated data:
- open old records of each type and status;
- edit and save them, which triggers validation that the loader bypassed;
- run period-end and regulatory reports and compare them with the legacy reports;
- search with Turkish characters;
- check calculations that depend on history (interest, limits, loyalty).

Design these tests with `designing-test-cases`, and pick records from the edge cases that profiling found. Measure performance with production-size volumes (`testing-nonfunctional`), because indexes and statistics after a bulk load differ from the test database's.

### 7. Cutover rehearsal
Rehearse the cutover end to end at least once with production-size data, using the runbook:
- **Timing:** does the migration fit in the cutover window, with a margin for one re-run?
- **Delta or incremental loads:** do changes made after the initial load arrive exactly once (inserts, updates, deletes)?
- **Re-run and idempotency:** after a failure at step N, does restarting produce duplicates?
- **Rollback:** can the legacy system resume within the agreed time, with transactions from the cutover window handled?
- **Go/no-go:** check the reconciliation report against the sign-off criteria.

### 8. Sign-off report
Report per migration object (customers, accounts, transactions …):
- the reconciliation verdict and the rules with their values;
- accepted exceptions, each with its owner;
- open defects by class;
- rehearsal timings against the cutover window;
- the result of the regression tests.

Run the RTM (`tracing-requirements`) and the completion report (`reporting-test-results`) on `qa/`: the reconciliation test cases count as executed by automation, and a failed check fails its requirement. Attach the reconciliation Markdown files as evidence.

## Files
- `scripts/reconcile.py`: CSV source/target reconciliation with a mapping (transform ops: trim, upper_tr/lower_tr, date, decimal, map, default, concat, strip_leading_zeros …). It reports counts, duplicates, missing and unexpected keys, field mismatches with hints, Decimal control totals per group, null rates and mapping coverage, and gives a PASS/FAIL verdict with accepted exceptions. `--compact-out` writes one test case per check with stable TC IDs; `--results` writes the verdict per test case into `qa/results.json`. Output is TR/EN.
- `assets/mapping-example.json`: an annotated mapping file that uses every op, ignored columns, not-migrated columns and accepted exceptions.
- `assets/reconciliation-queries.sql`: parametrised SQL for profiling, counts, control totals per group, key anti-joins, row-hash comparison (with PostgreSQL, SQL Server, Oracle and MySQL notes), orphan and business-rule checks.
- `references/migration-testing.md`: strategy, profiling, reconciliation levels, sampling, rehearsals and cutover, delta and idempotency, regression, performance, privacy, defect classification, sign-off template, and script limits.
