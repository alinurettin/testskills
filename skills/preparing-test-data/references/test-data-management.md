# Test data management guide

## Contents
1. Test data is a test asset
2. From test cases to data requirements
3. Choosing the source: synthetic, masked, or production
4. Synthetic generation with gen_data.py
5. Masking and pseudonymisation (KVKK / GDPR)
6. Data isolation per test and per run
7. Environments and refresh strategy
8. Turkish specifics
9. Data catalog and ownership
10. Limits of the scripts

---

## 1. Test data is a test asset
Wrong or missing data is one of the most common causes of false failures, blocked test runs and "works on my machine" defects. ISTQB CTFL v4.0 places test data preparation in test implementation. ISO/IEC/IEEE 29119-3 has a *test data requirements* document and a *test data readiness report*. The practical meaning of both:
- **Every test case states its data.** `test_data` in `test-cases.json`, or `data` on its steps. A test without documented data cannot be repeated by someone else.
- **Data has an owner, a source, a version and a refresh rule**, like code (§9).
- **Data is ready before execution starts.** "Waiting for data" is a blocker to report, with its impact, not a reason to test with whatever happens to be there.

## 2. From test cases to data requirements
Run `scripts/data_needs.py` on `qa/test-cases.json`. It sorts every need into one of two kinds.

| Kind | Where it comes from | How to provide it |
|---|---|---|
| **Exact**: the value *is* the test | boundary values (99,99 / 100,00 / 100,01 TL), equivalence-class representatives, decision-table rules, states, pairwise combinations | A small, reviewed **fixture file** (CSV/JSON/SQL) in version control. Never random: a random value can miss the boundary. |
| **Any valid**: the test needs *a* record of the right shape | "a registered customer with an active card", "an order with 3 items" | Generated (`gen_data.py`), or created by a factory in the test itself (§6) |
| **Volume**: many records | performance, pagination, search, reports | Generated at scale with a fixed seed |
| **Negative / invalid** | invalid partitions, wrong checksums, malformed dates | Fixture rows, or generated then corrupted deliberately. Keep one invalid value per row, so one fault cannot mask another. |
| **State and history** | "customer with 3 failed logins", "account frozen yesterday" | Build it through the API (§6). Hand-edited database rows skip business rules and drift from reality. |

Also check:
- **Cross-field rules.** Birth date vs age limit, IBAN bank code vs bank, postcode vs city, currency vs amount scale.
- **Time.** Anything relative to "today" (age, expiry, due dates) breaks tomorrow. Fix the clock in the application, or compute the dates at run time. Never hard-code a date that will expire.
- **Reference data.** Product catalogues, tariffs, parameter tables: which version does the test assume?

## 3. Choosing the source: synthetic, masked, or production

| Source | Use when | Risks |
|---|---|---|
| **Synthetic** (default) | Almost always: functional, regression, automation, demo, training | May miss real-world oddities. Compensate with deliberate edge values (§4) and data profiling of production (aggregate statistics only). |
| **Masked / pseudonymised production extract** | The defect only shows with real distributions or real legacy records (migrations, complex reconciliation, reports) | Still personal data. Re-identification through quasi-identifiers. Needs an approved purpose, access control and retention. |
| **Anonymised production data** | Analytics-style volume tests where individuals no longer matter | True anonymisation is hard to achieve and hard to prove (§5). |
| **Unmasked production copy** | Practically never | A data breach waiting to happen. Test systems have weaker controls, more users, and send real e-mails and SMS. |

**Using production data in testing is a compliance decision, not a tester decision.** The data controller decides, usually through the DPO, legal and information security. They decide on the purpose, the legal basis, minimisation, the masking method, access, retention and cross-border transfer. The tester's job is to:
1. state the need (which defect class requires real data, and why synthetic data is not enough);
2. propose the minimum columns and rows;
3. apply the approved rules and keep the evidence (`mask-report.md`).

## 4. Synthetic generation with gen_data.py
- **Determinism.** The same schema and `--seed` give byte-identical output. Commit the schema and the seed, not the generated file, when the file is large. The seed is part of the defect report ("reproduces with seed 42").
- **Referential integrity.** Generate the parent table first. The child picks from its key column (`"type": "ref", "source": "customers:id"`), so every foreign key exists. `distinct: true` gives one-to-one relations.
- **Uniqueness.** `unique` lists single or composite keys. Rows are regenerated on collision. If the value domain is too small (for example 5 enum values and 10 unique rows), the script stops with an explanation.
- **Edge rows.** `edge: true` fields receive boundary and awkward values in `edge_fraction` of the rows. Each such row changes exactly one field, which keeps failures diagnosable. `--mark-edges` records the changed field in `_edge`. The values:
  - numbers: min, min+1 step, max−1 step, max, and 0 when it is in range;
  - dates: min, max, 29 February, 31 December;
  - strings: max length, min length, empty (only with `allow_empty`), Turkish characters, `IŞIK`/`İPEK` casing traps, leading and trailing spaces, an emoji (4-byte UTF-8), quotes and apostrophes;
  - Turkish formats: alternative phone and IBAN notations, leading-zero postcodes and VKNs, provinces with `İ`, `Ş`, `Ç`, `Ğ`.
  These edge values are *within* the declared domain or are representation variants. Decide the expected result for each: accept, normalise, or reject with a message. Invalid data for negative tests belongs in fixtures.
- **Per-run data.** `--run-tag` fills `{run}` in `seq` prefixes (`CUST-{run}` becomes `CUST-R20260930-`). Parallel runs and reruns then never collide, and cleanup can delete by prefix.
- **Excel.** Use `--bom` so Excel shows Turkish characters, and `--delimiter ";"` with `decimal_sep ","` for Turkish-locale Excel. Store TCKN, VKN, IBAN and postcodes as text: Excel turns them into numbers, strips leading zeros and rounds 11-digit values in scientific notation.

## 5. Masking and pseudonymisation (KVKK / GDPR)
**Terms.**
- **Anonymisation:** the person can no longer be identified by *anyone* with reasonably likely means, even by matching with other data. Anonymous data falls outside KVKK and GDPR (GDPR Recital 26; KVKK Art. 3 and Art. 7).
- **Pseudonymisation:** identifiers are replaced, but re-identification is possible with additional information such as a key or a mapping table (GDPR Art. 4(5)). **Pseudonymised data is still personal data.** Everything `mask_data.py` does with `hash` and `fake` is pseudonymisation.

**Principles that apply to test data** (GDPR Art. 5; KVKK Art. 4):
- **Purpose limitation.** Data collected to serve customers is being reused for testing. The controller must establish that this further use is compatible or otherwise lawful.
- **Data minimisation.** Only the columns and rows the defect class needs. `--default drop` enforces this for columns nobody reviewed.
- **Storage limitation.** Delete the extract and the masked copy when the purpose ends, and record the date.
- **Security** (GDPR Art. 32; KVKK Art. 12). Access control, logging, no copies on laptops, and the secret kept outside the test environment.
- **Special categories** (KVKK Art. 6; GDPR Art. 9): health, biometrics, religion, criminal records and similar. Keep them out of test data unless the approved purpose requires them.
- **Cross-border transfer** (KVKK Art. 9; GDPR Chapter V). A test environment or SaaS test tool hosted abroad makes the extract an international transfer.

**Re-identification risk.** Removing names is not enough.
- **Quasi-identifiers** combine into a fingerprint. Birth date + postcode + gender uniquely identified about 87% of the US population in Sweeney's well-known study. Generalise them: birth date to year, postcode to province prefix, and salary to buckets.
- **Rare values** identify people on their own: the only customer in a small town, a very high balance, an unusual job title. Suppress small groups (the k-anonymity idea: every combination of quasi-identifiers should occur at least *k* times).
- **Free text** (notes, complaint text, addresses, attachments) hides identifiers anywhere. Drop or redact it; masking cannot parse it reliably.
- **Linkage across tables.** A masked customer table next to an unmasked transactions table with amounts and timestamps can still re-identify. Mask the whole extract consistently.
- **Unkeyed hashes are reversible.** A TCKN has fewer than 10⁹ valid values; a plain SHA-256 of it is brute-forced in minutes. For that reason `mask_data.py` only hashes with a secret (HMAC) and refuses to run without one.

**Techniques** (see also WP29 Opinion 05/2014 on anonymisation techniques, EDPB guidelines on pseudonymisation, and the KVKK Board's guide on deletion, destruction and anonymisation):

| Technique | `mask_data.py` rule | Keeps | Notes |
|---|---|---|---|
| Suppression | `drop` | nothing | The best default for columns the tests do not need |
| Redaction | `redact` | presence or emptiness | Free text, notes |
| Keyed hashing (tokenisation) | `hash` | equality, so joins work | The same secret for every file of one extract; rotate it per extract |
| Deterministic substitution | `fake` | a realistic format and equality | Validators still pass. Collisions are possible, so use `hash` for keys. |
| Generalisation | `generalize` | coarse value | Year of birth, province, income bucket |
| Perturbation, shuffling | not provided | distributions | Changes totals; unsuitable when tests reconcile amounts |

**Referential integrity.** Hash every key column with the same secret and the same `normalize` in every file of the extract. The same input then gives the same token, and joins still work. Check it after masking: count orphans in the child tables before and after.

**Procedure:**
1. Record the approval and purpose.
2. Write the rules (start from `assets/mask-rules-example.json`).
3. Mask *inside* the production security zone.
4. Review the report; every warning is either fixed or accepted in writing.
5. Transfer only the masked files.
6. Delete on schedule.

## 6. Data isolation per test and per run
Tests that share mutable data become order-dependent and flaky, and they fail when run in parallel.
- **Each test creates what it changes.** Use a factory or builder with sensible defaults, overriding only what the test is about: `aCustomer().withSegment("premium").create()`. Shared, read-only reference data (the province list, a tariff) can be seeded once.
- **Unique per run.** Build keys, e-mails and names from a run ID and a counter (`qa+R42-17@example.test`), never from fixed literals such as `test@test.com`.
- **Idempotent setup.** "Ensure this exists" rather than "insert", so a rerun after a crash still works.
- **Teardown that cannot hide failures.** Delete by run tag after the run, not in each test's `finally` block, when the data is evidence for a failure. Alternatives: a transaction rollback per test (unit and integration level), or an ephemeral environment or container per pipeline run.

**Seeding routes:**

| Route | Pros | Cons |
|---|---|---|
| API seeding | Business rules applied; fast; stable | Needs endpoints (sometimes test-only ones, which must be secured or disabled in production) |
| UI seeding | Exercises the real flow | Slow and brittle. Use it only for the flow under test, not for preconditions. |
| Direct database seeding | Fastest; any state | Bypasses rules and events, and breaks with schema changes. Keep it for reference data and snapshots. |
| Snapshot restore | Large, consistent datasets | Refresh and versioning overhead (§7) |

- **Parallel workers** need either disjoint data per worker (worker index in the run tag) or `--workers=1` for state-changing suites.
- **Consumable data** runs out. Balances drain, stock empties, coupons are used up, and rate limits trigger. Reset it before each run, or create it per test.

## 7. Environments and refresh strategy
- **Know what each environment holds.** The data catalog (§9) says, per environment, which datasets exist, their version and seed, and when they were last refreshed.
- **Golden dataset.** A versioned, reviewed baseline (fixtures plus generated volume from a seed) that can be restored on demand. Tests may assume only what the golden dataset guarantees.
- **Refresh cadence.** Refresh at a predictable point (for example at the start of each sprint or before each regression cycle) and announce it. Refreshing during a test cycle destroys the evidence of open defects.
- **Schema migrations.** Regenerate synthetic data after each migration. A stale dataset that no longer matches the schema causes false failures, and it hides migration defects.
- **Masked refreshes** repeat the full approval and masking procedure every time; approval is per extract, not forever.
- **Time zone.** Turkey uses UTC+3 all year (no daylight saving since 2016). Servers in UTC and clients in Europe/Istanbul still shift dates near midnight. Include 00:00–03:00 local times in date tests.

## 8. Turkish specifics
**ID policy.** A checksum-valid TCKN, VKN or IBAN is valid by algorithm only. There is no reserved fictional range, so a generated value can coincide with a real person, company or account.
- **Allowed:** synthetic checksum-valid values in test environments, produced by a generator (`gen_data.py`, `mask_data.py` `fake`, `check_ids.py --generate` in designing-test-cases). Record the schema and seed in the data catalog (§9); that record is the proof of synthetic origin.
- **Not allowed:** values copied from the internet, documents or production; generated values in production or in systems shared outside the test boundary (real registries such as MERNIS/KPS, payment networks, SMS and e-mail gateways, partners' systems).
- **Checks:** `data_needs.py` reports checksum-valid IDs and mobile numbers in test cases as warnings ("verify synthetic origin") and fails (exit 1) only for data that clearly looks real, such as e-mails outside the reserved example domains.
- **Invalid values** for negative tests are single-fault variants of a valid synthetic value (`check_ids.py --variants` in designing-test-cases), one fault per row.

**Identifiers:**
- **TCKN** (T.C. kimlik no): 11 digits, first digit not 0.
  - d10 = ((d1+d3+d5+d7+d9)×7 − (d2+d4+d6+d8)) mod 10
  - d11 = (d1+…+d10) mod 10
  - Foreign residents receive a number of the same format (typically starting with 99).
- **VKN** (vergi kimlik no): 10 digits, check digit computed from the first nine with weights of powers of two mod 9 (see `vkn_check_digit` in `scripts/tr_ids.py`, which also cites the published VKNs it was verified against). Individuals are identified by their TCKN for tax purposes.
- **IBAN (TR):** 26 characters: `TR` + 2 check digits (ISO 7064 mod 97-10) + 5-digit bank code + 1 reserve digit (`0`) + 16-character account number (digits in practice). The printed form is in groups of four. Accept both forms, and store the compact one.
- **Mobile numbers:** +90 5xx xxx xx xx. There is, as far as we know, **no reserved fictional range** in Turkey (unlike, for example, the UK's drama numbers). A generated number may belong to a real subscriber, so route every test SMS and call to a sandbox gateway. Because of number portability, the prefix no longer identifies the operator.
- **Postcodes:** 5 digits; the first two are the province plate code (01–81), so leading zeros matter (`06100` Ankara).

**Characters, casing and sorting:**
- The Turkish alphabet has `ç ğ ı ö ş ü` and **two i's**: `ı/I` and `i/İ`. Locale-free upper-casing turns `i` into `I` (wrong for Turkish), and lower-casing turns `I` into `i` (also wrong).
  - JavaScript: `'i'.toLocaleUpperCase('tr-TR')` → `İ`.
  - Java: always pass a `Locale`. The default Turkish locale famously breaks `"TITLE".toLowerCase()` comparisons in code that assumes English.
  - Python: `'İ'.lower()` gives `i` + a combining dot (2 code points).
- **Test** search, login (e-mail and user-name case-insensitivity), sorting and uniqueness with `IŞIK/ışık`, `İPEK/ipek`, `Işıl/ISIL`.
- **Sorting:** the Turkish order is a b c ç d e f g ğ h ı i j k l m n o ö p r s ş t u ü v y z. Binary or English collation puts `Çelik` after `Zeki`. Check the database collation (for example `Turkish_CI_AS`, or a MySQL `utf8mb4_tr_*` collation) and the UI sort.
- **Encoding.** Mixed legacy encodings (Windows-1254, ISO-8859-9) produce `Ã§`, `Ä±` and similar mojibake. Include Turkish characters in every text field that crosses a system boundary: files, queues, e-mail, PDF, SMS (GSM 7-bit has no `ı` or `ş`; they force UCS-2 and halve the SMS length).
- **Length:** a database may count bytes and the UI characters; `ş` is 2 bytes in UTF-8 and an emoji 4.

**Formats:**
- Dates `dd.MM.yyyy` (`30.09.2026`). Ambiguous input like `01.02.2026` means 1 February in Turkey and January 2 in the US.
- Numbers: decimal comma and thousands dot (`1.234,56`); `TL` or `₺` after the amount.
- CSV in Turkish Excel uses `;`.

## 9. Data catalog and ownership
Keep one catalog (a Markdown table or a sheet) next to the test plan:

| Dataset ID | Purpose / used by | Source | Owner | Version / seed | Environments | Refresh | Personal data? | Retention |
|---|---|---|---|---|---|---|---|---|
| DS-TD-01 customers (golden) | TC-001..TC-040 | synthetic, `schema.json` | QA lead | v3, seed 42 | TEST, UAT | each sprint | no | n/a |
| DS-TD-02 migration sample | defect class "legacy address formats" | masked extract, approval ref. KVKK-2026-07 | DPO + data owner | extract 2026-09-01 | MIG-TEST only | never (one-off) | pseudonymised | delete 2026-12-31 |

- **The owner** answers "may we use this, and until when?". The QA lead answers "does it serve the tests?".
- Record the approval reference for every non-synthetic dataset, and the deletion date.
- **Link datasets to test cases.** Put the dataset ID in a test case's `preconditions` or `test_data` so the RTM shows which tests break when a dataset changes.

## 10. Limits of the scripts
- **`gen_data.py`**
  - It produces plausible, not realistic, distributions: there are no correlations between columns except `from`, `ref` and `city_field`.
  - Postcodes are valid in shape and province prefix, but not guaranteed to be assigned.
  - Bank codes default to a few well-known Turkish bank codes. Verify them against the current participant list if your system validates them, or pass `bank_codes`.
  - Name lists are small, so full-name duplicates are expected in large tables.
- **`mask_data.py`**
  - It works on CSV only, and does not open files, databases, JSON or XML.
  - It cannot find personal data inside free text. PII detection uses header names and simple value patterns, so it is a safety net, not a classifier.
  - `fake` replaces each column independently: a row's fake e-mail does not match its fake name.
  - Fake values can collide; the report counts collisions for identifier types.
  - It does not measure re-identification risk (k-anonymity); review quasi-identifiers yourself.
- **`data_needs.py`** infers types from the few values in the test cases. The starter schema's ranges are the observed values, not the real domain; widen them. Its ID warnings cannot tell a generated TCKN or IBAN from a real one; only the recorded origin (generator, schema, seed) can.
