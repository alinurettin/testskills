# KEY — trial-migration2 (data migration testing: SİGMA/400 → PoliçeNova, policies + installments)

**EVALUATOR ONLY. Never give this file, any `migration2_*` file, or `trial-migration2/RUN.md` to the agent under test.**

Trial folder: `evals/trial-migration2/` (agent gets only `TASK.md` + `inputs/`).
Supporting key files (all Python 3 stdlib):

| File | Purpose |
|---|---|
| `keys/migration2_generate.py` | Deterministic generator of all inputs (legacy exports, buggy-ETL target exports, ETL report) + `migration2_expected.json`. Hand-written spec is not generated. |
| `keys/migration2_expected.json` | Exact key sets for every K and T (source of truth for the lists below). |
| `keys/migration2_verify.py` | Independent reference reconciliation from the spec; asserts every K reproduces, nothing else differs, and every T is spec-correct. Must print `ALL CHECKS PASSED`. |
| `keys/migration2_grade.py` | Assistive grader: `python migration2_grade.py <agent_workdir> [--run-script]`. Suggests points; a human confirms. |

## 1. Scenario and baseline numbers

Fictional insurer Kuzeyyıldız Sigorta migrates policies (`POLMAS` → `policies`) and installments (`TAKSIT` → `installments`) from the legacy AS/400-style system (Windows-1254, `;`, decimal comma + thousands dot, trailing-minus negatives, `dd.MM.yyyy` and `dd/MM/yyyy` dates, Istanbul local timestamps) to a new platform (UTF-8, ISO dates, UTC timestamps, dot decimals, new codes). The migration team's ETL report claims everything reconciles. All data is synthetic (fictional names, companies, banks, agencies; no personal IDs).

| Quantity | Value |
|---|---|
| Legacy policies / installments (raw) | 64 / 247 |
| Quotes (`DURUM_KD = B`, out of scope) / their installments | 4 / 13 |
| **In-scope (expected in target)** policies / installments | **60 / 234** |
| Actual target policies / installment rows | 59 / 234 (count matches only because 5 lost + 5 duplicated) |
| ETL report claims | 60/60 policies, 234/234 installments, totals OK, 0 rejects — the policy claim is false (counter based) |
| Target M4 violations (gross_premium ≠ Σ amount) | 6 policies: 4125100161 (K7), 4125100301 / 4125100327 / 4125100347 (K8), 4125100388 / 4125100468 (K6) |
| Target M6 per-agency mismatch | ACN-3501 and ACN-3502 (K9, TRY ±89,787.66; USD ±4,697.63; EUR ±67.94) and ACN-3402 (−28,640.46 TRY = K5) |

## 2. Planted items (max 34 points)

Difficulty mix: easy K1–K3 (3), medium K4–K7 (4), hard K8–K11 (4). "Keys" are legacy keys as the agent must report them (`POL_NO`, `POL_NO/TAKSIT_NO`). A finding earns a K once; splitting one K over several findings is neither extra credit nor a false positive.

### K1 — Status `S` mapped to `SUSPENDED` instead of `EXPIRED` (easy, 2 pts, severity High)
- **What:** Spec table 5.1: `S` (Süresi doldu) → `EXPIRED`. The ETL wrote `SUSPENDED` (a value that does not exist in the spec) for all 14 `S` policies.
- **Keys (14):** 4125100101, 4125100127, 4125100150, 4125100161, 4125100198, 4125100216, 4125100236, 4125100255, 4125100282, 4125100290, 4125100294, 4125100318, 4125100820, 4125100870
- **Why it matters:** expired policies appear suspended → renewal campaigns, claims eligibility checks and regulatory portfolio reports are wrong.
- **Accept:** a finding that `S`/expired policies carry `SUSPENDED` (or "status mapping of S is wrong, should be EXPIRED") with ≥1 key or the general rule.

### K2 — `address_line` truncated to 50 characters (easy, 2 pts, severity Medium)
- **What:** Spec: varchar(250), trim only, "kısaltma yapılmaz". All 7 addresses longer than 50 chars were cut at exactly 50 (mid-word, trailing space left).
- **Keys (7):** 4125100127, 4125100236, 4125100290, 4125100480, 4125100540, 4125100634, 4125100799
- **Why:** undeliverable mail/policy documents, wrong risk address on property policies.
- **Accept:** truncation/cut of addresses with ≥2 keys or the 50-char rule.

### K3 — Empty `IPTAL_TAR` → `cancel_date = 1900-01-01` instead of NULL (easy, 2 pts, severity High)
- **What:** Spec: "Boşsa NULL". ETL used the sentinel `1900-01-01` for all 56 non-cancelled migrated policies (only the 3 `I` policies have a real date).
- **Keys:** every migrated policy except 4125100301, 4125100327, 4125100347 (full list in `migration2_expected.json → K3_cancel_date_1900`).
- **Why:** a non-null cancellation date makes active policies look cancelled to downstream logic and reports.
- **Accept:** mentions the 1900-01-01 default / NULL not preserved for cancel_date.

### K4 — `loss_payee` (dain-i mürtehin) Turkish characters transliterated, only in this field (medium, 3 pts, severity Medium)
- **What:** Spec 2.2 + table 3: Turkish characters preserved. Only `loss_payee` was ASCII-folded (ı→i, İ→I, ş→s, ğ→g, ü→u, ö→o, ç→c); `insured_name`, `city`, `address_line` keep Turkish characters.
- **Keys (7):** 4125100180 (Kuzeydoğu Tüketici Finansmanı A.Ş. → Kuzeydogu Tuketici Finansmani A.S.), 4125100417, 4125100464, 4125100496, 4125100598, 4125100681, 4125100825
- **Why:** the bank's legal name is printed on policies and used for claim payments to the loss payee; mismatching legal names block payments.
- **Accept:** identifies `loss_payee` / dain-i mürtehin field and the character corruption with ≥2 keys or the field-wide rule. Generic "Turkish characters broken" without naming the field and with no correct key = 0.

### K5 — In-scope policy missing; its 4 installments are orphans (medium, 3 pts, severity Critical)
- **What:** Policy **4125100673** (A02, KSK, ACTIVE, 28,640.46 TRY) is absent from `policies`, while `installments` contains `4125100673/1..4` pointing to the non-existent `KYS-4125100673` (M1 and M3 violated). Root cause (for the record, not required): its `ADRES` contains a `;` inside quotes (`"Fevzi Çakmak Mah. 1203 Sok. No:7; Kat:2 D:5"`); the ETL split lines naively, silently skipped the row and still reported "yazılan 20 / reddedilen 0".
- **Accept full (3):** names 4125100673 as missing in target AND reports the orphan installments / FK violation. **2:** only one of the two. **1:** 4125100673 listed only inside a lump "5 policies missing" together with the quotes (T2 penalty also applies). Generic "policy count differs" without a key = 0.

### K6 — Installments with `TAKSIT_NO ≥ 10` lost (medium, 3 pts, severity Critical/High)
- **What:** 5 rows silently dropped: **4125100388/10, /11, /12** (12-installment HOME policy) and **4125100468/10, /11** (11-installment motor policy). `installment_count` says 12/11 while 9 rows exist; M2, M4, M5 violated. The total installment count is masked by K7 (234 = 234).
- **Why:** these receivables (incl. 4125100468/11 still OPEN) would never be collected.
- **Accept full (3):** missing installments identified for both policies, or the "≥10 dropped" pattern with ≥1 policy. **2:** one policy only. **1:** only a premium-sum / installment_count mismatch reported for these policies without saying rows are missing.

### K7 — Duplicate installments from the R2 re-run (medium, 3 pts, severity High)
- **What:** R1 aborted in party 3 after inserting 5 installment rows; R2 re-ran party 3 with plain INSERT. Rows **4125100161/1..5** exist twice (identical values, different `installment_id`, `migration_run_id` R1 and R2). (`policy_id`, `installment_no`) uniqueness (M2) violated; Σ amount for 4125100161 is 46,302.69 vs gross 25,256.01.
- **Why:** double billing / double collection; inflated receivables.
- **Accept:** duplicates identified with ≥3 of the 5 keys or "4125100161 installments 1–5 duplicated". Mentioning the R1/R2 cause is good practice but not required. Reporting only "Σ ≠ gross for 4125100161" = 1 pt.

### K8 — Refund installments lost their minus sign (hard, 4 pts, severity Critical)
- **What:** Legacy writes negatives with a trailing minus (`25.407,73-`); the ETL stripped it, so `amount` and `paid_amount` of all 3 `REFUND` rows are positive. Gross premium (net of refund) is correct, so M4 fails for the 3 cancelled policies.
- **Keys:** installments **4125100301/2, 4125100327/4, 4125100347/3**; policies 4125100301, 4125100327, 4125100347.
- **Why:** money paid back to customers appears as money collected; receivables and premium income overstated by 2 × refund (≈ 97.4k TRY).
- **Accept full (4):** states that refund amounts are positive / the sign was lost, with ≥2 of 3 keys or the general rule. **2:** only M4 (sum mismatch) for ≥2 of these policies without identifying the sign problem.

### K9 — Agency codes of A04 and A09 swapped (hard, 4 pts, severity High)
- **What:** Spec 5.4: A04 → ACN-3501, A09 → ACN-3502. ETL wrote the opposite for all 11 policies. Overall totals still match; per-agency totals (M6) do not.
- **Keys:** A04 (now ACN-3502): 4125100294, 4125100353, 4125100615, 4125100681, 4125100799, 4125100870; A09 (now ACN-3501): 4125100236, 4125100496, 4125100507, 4125100734, 4125100895.
- **Why:** commissions (hakediş) would be paid to the wrong agency (≈ 89.8k TRY premium shifted plus USD/EUR business).
- **Accept full (4):** identifies the swap / wrong agency mapping for A04 and/or A09 (mentions ACN-3501/3502 or A04/A09 with ≥2 keys or the rule). **2:** only the per-agency total mismatch for ACN-3501/3502 without the mapping cause.

### K10 — Late payments around midnight flagged `PAID_ON_TIME` (hard, 4 pts, severity Medium)
- **What:** Spec 5.5: compare the **Istanbul local calendar day** of the payment with `due_date`. The ETL used the UTC date of `paid_at`. For payments made 00:00–02:59 local on the day after the due date, the UTC date equals the due date, so they were marked `PAID_ON_TIME` instead of `PAID_LATE`.
- **Keys (3):** **4125100447/5** (due 2026-03-11, paid 12/03/2026 00:47), **4125100507/7** (due 2026-07-02, paid 03/07/2026 02:15), **4125100659/2** (due 2026-04-30, paid 01/05/2026 01:22).
- **Why:** late-payment fees, dunning and customer payment-behaviour scores are wrong; the bug will recur in daily operation, not only in migration.
- **Accept full (4):** ≥2 of 3 keys, or the UTC-vs-local-day cause with ≥1 key.
- Note: the `paid_at` values of these rows are correct (see T1); only `payment_status` is wrong.

### K11 — `fx_rate` rounded to 2 decimals; `premium_try` wrong (hard, 4 pts, severity Medium/High)
- **What:** Spec: `fx_rate` = `KUR` with 4 decimals; `premium_try = ROUND_HALF_UP(gross × fx_rate, 2)`. ETL rounded the rate to 2 decimals (e.g. 34,1287 → 34.1300) and computed `premium_try` from it.
- **Keys (6):** 4125100713 (USD, KUR 34,1287 → fx_rate 34.1300; premium_try target 126,564.28, expected 126,559.46), 4125100773 (EUR, 37,6638 → 37.6600; target 259,394.92, expected 259,421.10), 4125100820, 4125100870, 4125100895, 4125100962 (differences range from 0.09 to 26.18 TRY).
- **Unaffected foreign policies (correct, not findings):** 4125100255 (33,9500), 4125100428 (38,1200).
- **Why:** TRY-equivalent premium feeds financial / regulatory reporting and reinsurance cessions.
- **Accept full (4):** fx_rate rounding or wrong premium_try identified with ≥3 of the 6 keys or the general rule. 2 pts if only 1–2 keys and no rule.

## 3. Traps (−2 each when reported as a defect)

No penalty when the agent mentions them as correct behaviour, as an observation, or as a question in "Gözlemler / Sorular".

| ID | Looks wrong because… | Correct per spec | Records |
|---|---|---|---|
| **T1** | `updated_at` / `paid_at` differ from legacy by 3 h; for late-night rows the **date** is the previous day | Section 2.1/3/4: legacy timestamps are Istanbul local (UTC+3), target is UTC | policies 4125100474, 4125100496, 4125100548, 4125100718, 4125100847; installments 4125100447/5, 4125100507/7, 4125100523/3, 4125100615/4, 4125100659/2, 4125100734/2 (523/3, 615/4, 734/2 are on-time payments correctly `PAID_ON_TIME`) |
| **T2** | Raw counts 64 → 59 policies and 247 → 234 installments; quote POL_NOs absent | Section 1: `DURUM_KD = B` quotes and their installments are out of scope | 4125100988, 4125101014, 4125101039, 4125101063 (+13 installments) |
| **T3** | Empty `DOVIZ` / `KUR` became `TRY` / `1.0000` ("NULL defaulted") | Table 5.3 and the `fx_rate` rule | 4125100101, 4125100103, 4125100116, 4125100127, 4125100150 |
| **T4** | Every `end_date` is one day before `BIT_TAR` (e.g. 01/03/2026 → 2026-02-28) | Table 3: `end_date = BIT_TAR − 1 gün` | all 59 migrated policies |

Grading notes: reporting "5 policies missing" (quotes + K5) = T2 penalty and K5 at most 1 pt. Reporting `paid_at` shifts for the K10 rows as a timezone defect = T1 penalty, unless the finding is about the wrong `payment_status` (then it is K10).

## 4. False positives (−1 each, max −5) and neutral statements

−1 for each other distinct claimed defect that is not a spec violation, e.g.: trimmed trailing spaces in `insured_name`; number/date format changes themselves; `installment_id` or `migration_run_id` values/gaps; R2 policies carrying `migration_run_id = R2`; first installment larger than the others (remainder rule in source); short travel policy durations; `installment_count` not counting refund rows; source data-quality facts presented as migration defects (e.g. expired policy with OVERDUE installments, RENEWED without a successor policy); `premium_try` of TRY policies equal to gross; claims that correct fields are wrong because the agent mis-parsed cp1254, `dd/MM` vs `MM/dd`, thousands separators or trailing minus.

**Neutral (0):** correct statements that the ETL report is unreliable (claims 60 target policies, 0 rejects, counter-based totals); observations/questions; recommendations (FK constraints, uniqueness constraint, idempotent re-run, reject logging).

## 5. Method points (max 4)

| ID | Points | Rule |
|---|---|---|
| M-a | 2 | `cikti/mutabakat.py` (or `.js`) runs offline with stdlib from the workdir root and performs record-level reconciliation of both entities (key match + field comparison + at least one aggregate check). 1 pt if it runs but only does counts/totals, or needs manual fixes. 0 if missing. |
| M-b | 2 | Report states the correct baseline (60 in-scope policies, 234 in-scope installments, 4 quotes excluded) **and** recommends NO-GO (or "go only after fixes and a clean re-run") with severity-based rationale. 1 pt if only one of the two. |

## 6. Score

`score = Σ K points (≤34) + method (≤4) − 2 × trap hits − min(5, false positives)`, floor 0, **max 38**.
Also record per run: number of K found (0–11), hard K found (K8–K11, 0–4), trap hits (0–4), FP count, wall time.

## 7. Grading procedure

1. `python keys/migration2_grade.py <agent_workdir> --run-script` (suggestions, trap flags, unmatched findings, method checks).
2. For each K, open the cited finding(s) and apply the acceptance rule above; correct the suggestion if needed (the matcher is keyword + key based and can miss free-text-only findings — also read `mutabakat_raporu.md`).
3. Classify every unmatched finding: valid duplicate of a K (0), neutral (0) or false positive (−1).
4. Apply trap penalties only when the finding asserts a defect.
5. Fill method points by running the script and reading the report.

## 8. Verification log (designer)

`python keys/migration2_generate.py` (deterministic, re-running yields byte-identical inputs) followed by `python keys/migration2_verify.py` → `ALL CHECKS PASSED`: each K1–K11 reproduces on exactly the listed records, no other field or record differs from the spec, each T1–T4 differs under a naive comparison but matches the spec, legacy invariants (BRUT_PRIM = Σ TUTAR, TAKSIT_SAY = regular count) hold for every in-scope policy, and the grader was dry-run against a synthetic perfect answer (34/34, no trap flags) and a naive answer (7/34 suggested with T1–T4 flagged).
