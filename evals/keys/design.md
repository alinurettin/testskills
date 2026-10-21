# KEY — trial-design (SFM v1.4 test case design)

Evaluator-only answer key. Never place this file, `design_grader.py` or `design_ref/` in an agent workspace.

- Trial folder: `C:\projeler\TestSkills\evals\trial-design\` (agent gets `TASK.md` + `girdiler\` only; see `RUN.md`)
- Kind: **test case design from a precise specification** — no system under test, no server, no ports.
- Objective grader: `C:\projeler\TestSkills\evals\keys\design_grader.py` (Python 3 stdlib)
- Reference deliverables for grader calibration: `design_ref\gold\` (36/36) and `design_ref\naive\` (5/36)

## 1. What the agent must deliver

`cikti/test-tasarimi.md`, `cikti/fiyat-test-verisi.csv`, `cikti/durum-gecis-testleri.csv`,
`cikti/konfigurasyon-matrisi.csv` (formats fixed by TASK.md + templates). Planted test conditions
are scored from the CSVs (machine-checkable). The report is used only for K11c and for T4.

## 2. Reference model (the oracle — derived strictly from the spec)

Pricing (spec §3–§9), all amounts in cents-exact decimals:

1. Validation → `ERR_GECERSIZ_GIRDI` (enum not exact upper-case code, `bolge` missing/invalid for STANDART/HIZLI — ignored and not validated for MAGAZA, `ara_toplam` not `^\d+(\.\d{1,2})?$` or ≤ 0).
2. Unknown coupon (case-sensitive, trimmed) → `ERR_KUPON_GECERSIZ`.
3. AT < 150.00 → `ERR_MIN_SEPET`; AT > 20000.00 → `ERR_MAX_SEPET` (**on AT, before discount**).
4. HIZLI + UZAK → `ERR_TESLIMAT_BOLGE`; KAPIDA_ODEME + (HIZLI|MAGAZA) → `ERR_KAPIDA_UYGUNLUK`.
5. KI: DEFNE10 = min(round_half_up(AT × 0.10, 2), 150.00), any membership. KITAP50 = 50.00 if membership ∈ {KLASIK, ALTIN} and AT ≥ 400.00, else 0.00 (no error).
6. NT = AT − KI.
7. KU (decision table):

| Teslimat | Üyelik | NT ≥ 750? | Bölge | KU |
|---|---|---|---|---|
| STANDART | ALTIN | – | NORMAL / UZAK | 0.00 |
| STANDART | MISAFIR/KLASIK | E | NORMAL | 0.00 |
| STANDART | MISAFIR/KLASIK | E | UZAK | **25.00** (surcharge not covered by 750 rule) |
| STANDART | MISAFIR/KLASIK | H | NORMAL | 39.90 |
| STANDART | MISAFIR/KLASIK | H | UZAK | 64.90 |
| HIZLI | any (membership irrelevant) | E | NORMAL | 40.00 |
| HIZLI | any | H | NORMAL | 79.90 |
| HIZLI | any | – | UZAK | ERR_TESLIMAT_BOLGE |
| MAGAZA | any | – | ignored | 0.00 |

8. HB = 12.90 for KAPIDA_ODEME (always, also ALTIN / free shipping), else 0.00.
9. OT = NT + KU + HB; KAPIDA_ODEME and OT > 5000.00 → `ERR_KAPIDA_LIMIT` (**OT incl. HB and KU**).
10. Puan (only on KABUL, on NT, KU/HB excluded): base = ⌊NT/10⌋; MISAFIR 0, KLASIK base, ALTIN ⌊base × 1.5⌋.
11. Error precedence = order of steps 1→2→3→4→9.

Lifecycle (spec §10): initial state ONAYLANDI for KAPIDA_ODEME, else ODEME_BEKLENIYOR. Transitions G1–G15
exactly as in the spec table. Processing order: unknown event → `ERR_GECERSIZ_GIRDI`; event not in table
for the state (incl. every event in IADE_EDILDI / IPTAL_EDILDI / DEPOYA_DONDU) → `ERR_GECERSIZ_GECIS`;
bad/missing params → `ERR_GECERSIZ_GIRDI`; guards: HAZIRLANIYOR + IPTAL(MUSTERI) → `ERR_GECERSIZ_GECIS`;
IADE_TALEBI gun > 14 → `ERR_IADE_SURESI`, then earlier IADE_RED → `ERR_IADE_TEKRAR`; the 3rd
TESLIM_BASARISIZ → DEPOYA_DONDU (1st/2nd → TESLIM_EDILEMEDI); IADE_RED → back to TESLIM_EDILDI. On
any error state and counters are unchanged.

Pairwise (spec §11): factors Platform{WEB,IOS,ANDROID} × Ödeme{KREDI_KARTI,BANKA_KARTI,KAPIDA_ODEME,CEPPAY}
× Teslimat{STANDART,HIZLI,MAGAZA} × Üyelik{MISAFIR,KLASIK,ALTIN} = 108 combos; constraints KS-1
(KAPIDA only STANDART), KS-2 (CEPPAY not WEB), KS-3 (CEPPAY not MISAFIR) → 75 valid combos,
**59 feasible value pairs**; a 12-row constrained pairwise set exists (see `design_ref\gold\konfigurasyon-matrisi.csv`).

Spec Ek-A check: Örnek 1, 2, 3, 5 are correct. **Örnek 4 is wrong** (KLASIK, AT 900.00, STANDART, UZAK:
spec table says KU 0.00 / OT 900.00; by §6.5 the correct values are KU 25.00 / OT 925.00, puan 90).
The Ek-A header says the rules prevail, so the rule-based value is the correct oracle.

## 3. Planted items (K1–K12) — max 36 points

Scoring is on CSV rows whose expected result is fully correct (row passes the oracle). A sub-check
needs at least one such row with the relevant expected column(s) filled. Reference values come from
the oracle; any other input that meets the acceptance rule is equally valid.

| K | Difficulty | Severity if missed | Points |
|---|---|---|---|
| K1 | easy | medium | 2 |
| K2 | easy | medium | 2 |
| K3 | easy | medium | 2 |
| K4 | easy | medium | 2 |
| K5 | medium | high | 3 |
| K6 | medium | medium | 3 |
| K7 | medium | high | 3 |
| K8 | medium | medium | 3 |
| K9 | hard | high | 4 |
| K10 | hard | high | 4 |
| K11 | hard | high | 4 |
| K12 | hard | medium | 4 |

### K1 — Sepet limitleri (AT), stated boundaries — easy, 2 pts
- What: min/max basket boundaries on AT.
- Why: order acceptance; classic BVA.
- Acceptance: (a) 1 pt: a row with AT = 149.99 → `ERR_MIN_SEPET` **and** a row with AT = 150.00 → `KABUL` (all amounts correct). (b) 1 pt: AT = 20000.00 → `KABUL` **and** AT = 20000.01 → `ERR_MAX_SEPET`.
- Reference: KLASIK/STANDART/NORMAL/KREDI_KARTI: 150.00 → KI 0.00, NT 150.00, KU 39.90, HB 0.00, OT 189.90, puan 15; 20000.00 → KU 0.00, OT 20000.00, puan 2000.

### K2 — KITAP50 eligibility boundary — easy, 2 pts
- What: AT ≥ 400.00 condition for a member (KLASIK or ALTIN).
- Why: coupon leakage / customer complaints.
- Acceptance: (a) 1 pt: member + KITAP50 + AT 399.99 → `KABUL`, KI 0.00 (coupon silently not applied, no error); (b) 1 pt: member + KITAP50 + AT 400.00 → KI 50.00, NT 350.00.

### K3 — Basic invalid transitions — easy, 2 pts
- What: transitions that are not in the table are rejected and the state is unchanged.
- Acceptance: (a) 1 pt: a row whose last event is rejected with `ERR_GECERSIZ_GECIS` from a non-terminal state (not counting HAZIRLANIYOR + IPTAL, which is K7), expected state = unchanged pre-state. Examples: KARGODA + IPTAL(aktor=MUSTERI); TESLIM_EDILDI + IPTAL(...); ODEME_BEKLENIYOR + KARGOYA_VER; KAPIDA order (ONAYLANDI) + ODEME_BASARILI. (b) 1 pt: any event in a terminal state (IPTAL_EDILDI, IADE_EDILDI, DEPOYA_DONDU) → `ERR_GECERSIZ_GECIS`, state unchanged (e.g. `ZAMAN_ASIMI > ODEME_BASARILI` = late payment after timeout).

### K4 — Forbidden combinations in pricing — easy, 2 pts
- Acceptance: (a) 1 pt: HIZLI + UZAK → `ERR_TESLIMAT_BOLGE`; (b) 1 pt: KAPIDA_ODEME + HIZLI or MAGAZA → `ERR_KAPIDA_UYGUNLUK` (precedence respected: e.g. KAPIDA + HIZLI + UZAK is `ERR_TESLIMAT_BOLGE`).

### K5 — DEFNE10 cap and half-up rounding — medium, 3 pts
- What: the 150.00 cap must be tested where it actually changes the result, and rounding must be half-up.
- Why: at AT 1500.01–1500.04, 10 % rounds to 150.00 anyway, so those values do NOT test the cap; float/banker's rounding gives 1 kuruş errors.
- Acceptance: (a) 2 pts: DEFNE10 with round_half_up(AT × 0.10) > 150.00 (i.e. AT ≥ 1500.05) and expected KI 150.00 (e.g. 1500.05, 1800.00, 2000.00). (b) 1 pt: DEFNE10 under the cap where AT's last cent digit is 5 (third decimal of 10 % is 5), correct half-up KI — e.g. AT 1234.55 → KI 123.46, NT 1111.09; AT 833.35 → KI 83.34.

### K6 — Loyalty points — medium, 3 pts
- Acceptance: (a) 2 pts: an ALTIN `KABUL` row where base ⌊NT/10⌋ is odd, with correct floored points (e.g. NT 750.00 → base 75 → 112; NT 850.00 → 127). (b) 1 pt: a KLASIK/ALTIN row with a coupon actually applied where ⌊AT/10⌋ ≠ ⌊NT/10⌋, with correct points on NT (e.g. KLASIK AT 1000.00 DEFNE10 → NT 900.00 → 90, not 100).

### K7 — Actor guard in HAZIRLANIYOR — medium, 3 pts
- Acceptance: (a) 2 pts: `ODEME_BASARILI > HAZIRLAMAYA_BASLA > IPTAL(aktor=MUSTERI)` (or KAPIDA order `HAZIRLAMAYA_BASLA > IPTAL(aktor=MUSTERI)`) → `ERR_GECERSIZ_GECIS`, state HAZIRLANIYOR. (b) 1 pt: same with `aktor=OPERATOR` → `KABUL`, IPTAL_EDILDI.

### K8 — Return window boundary — medium, 3 pts
- Acceptance: from TESLIM_EDILDI with no earlier rejection: (a) 1 pt `IADE_TALEBI(gun=14)` → `KABUL`, IADE_TALEP_EDILDI; (b) 2 pts `IADE_TALEBI(gun=15)` → `ERR_IADE_SURESI`, TESLIM_EDILDI.

### K9 — DERIVED free-shipping boundary on NT (after coupon) — hard, 4 pts
- What: the 750.00 threshold applies to NT = AT − KI, so the boundary must be hit through a coupon.
- Why: the most common real defect (threshold evaluated on AT instead of NT) silently gives free shipping to every couponed order with AT ≥ 750 > NT — 39.90 TL revenue loss per order.
- Acceptance: rows with a coupon actually applied (KI > 0) and a 750-sensitive delivery (STANDART with non-ALTIN, or HIZLI with any membership): (a) 2 pts NT = 750.00 exactly with correct KU; (b) 2 pts NT = 749.99 exactly with correct KU.
- Reference: DEFNE10 AT 833.33 → KI 83.33, NT 750.00, KU 0.00, OT 750.00; AT 833.32 → KI 83.33, NT 749.99, KU 39.90, OT 789.89 (KLASIK, NORMAL, KREDI_KARTI; puan 75 / 74). KITAP50 (member) AT 800.00 → NT 750.00; AT 799.99 → NT 749.99. HIZLI: same NT → KU 40.00 / 79.90.
- Note: AT 833.34 gives NT 750.01 (not the boundary). Plain AT 750.00 / 749.99 without coupon is only the non-derived boundary (no K9 credit).

### K10 — DERIVED cash-on-delivery limit on OT (incl. HB and KU) — hard, 4 pts
- What: §7.3 caps OT (NT + KU + HB), not AT or NT.
- Why: courier cash-limit compliance; naive testers test AT 5000.00 → "KABUL", which is wrong (OT 5012.90 → `ERR_KAPIDA_LIMIT`).
- Acceptance: KAPIDA_ODEME rows: (a) 2 pts: OT exactly 5000.00 → `KABUL` with correct OT; (b) 2 pts: computed OT exactly 5000.01 → `ERR_KAPIDA_LIMIT`.
- Reference pairs (accept / reject): no coupon, NORMAL, any membership: AT 4987.10 / 4987.11; non-ALTIN UZAK: 4962.10 / 4962.11; DEFNE10 NORMAL: 5137.10 / 5137.11; KITAP50 member NORMAL: 5037.10 / 5037.11; DEFNE10 UZAK non-ALTIN: 5112.10 / 5112.11.

### K11 — Easy-to-miss rule interaction: UZAK surcharge vs. the two "free shipping" rules — hard, 4 pts
- What: §6.2 (NT ≥ 750) waives only the base fee; the 25.00 UZAK surcharge stays. §6.3 (ALTIN) waives both. Spec Ek-A Örnek 4 shows the wrong value (0.00).
- Why: revenue leakage on every island delivery; copying the spec example reproduces the defect.
- Acceptance: (a) 2 pts: MISAFIR/KLASIK + STANDART + UZAK + NT ≥ 750.00 → KU 25.00 (e.g. KLASIK AT 900.00 → KU 25.00, OT 925.00, puan 90). (b) 1 pt: ALTIN + STANDART + UZAK → KU 0.00. (c) 1 pt [manual]: `test-tasarimi.md` reports that Ek-A Örnek 4 contradicts §6.5 (any wording that identifies example 4 and the 25.00 / 925.00 discrepancy). The script flags candidate lines; the grader confirms.

### K12 — Pairwise coverage with constraints — hard, 4 pts
- Acceptance (script): coverage of all 59 feasible pairs = 100 %, **0** rows violating KS-1/KS-2/KS-3, ≤ 20 rows → 4 pts. 100 % and no violation but > 20 rows → 2 pts. ≥ 90 % coverage and no violation → 2 pts. Otherwise 0. Rows that violate a constraint never count towards coverage and are also penalised (§5).

## 4. Traps (T1–T4) — correct behaviour that careless testers turn into wrong expected results

| T | Correct behaviour (spec) | Careless (wrong) expectation | Detection |
|---|---|---|---|
| T1 | Min basket is checked on AT (§4.3): AT ≥ 150.00 with a coupon that brings NT below 150 is `KABUL` (e.g. AT 150.00 DEFNE10 → NT 135.00, OT 174.90, KLASIK puan 13) | `ERR_MIN_SEPET` | pricing row with AT ≥ 150, NT < 150 whose expectation ≠ oracle |
| T2 | ALTIN gets nothing on HIZLI (§6.4a/c): ALTIN + HIZLI + NT < 750 → KU 79.90; NT ≥ 750 → 40.00 | 0.00 (thinks ALTIN = free shipping everywhere) | ALTIN + HIZLI `KABUL` row ≠ oracle |
| T3 | KAPIDA HB 12.90 is always charged (also ALTIN / free shipping) and never adds to points (§7.2, §8.1): ALTIN AT 750.00 KAPIDA → KU 0.00, HB 12.90, OT 762.90, puan 112 | HB 0.00 for ALTIN, or points on OT | KAPIDA `KABUL` row with HB ≠ 12.90 or wrong puan |
| T4 | Ek-A Örnek 1, 2, 3, 5 are correct, e.g. Örnek 3: base 85 × 1.5 = 127.5 → **127** (floor, §2.3/§8.3); Örnek 2: cap 150.00 and HIZLI 40.00 | Reporting one of them as a spec error (e.g. "127 should be 128" or "points should be 135 on AT") | report review (script lists candidate lines `[MANUEL ONAY]`) |

## 5. False positives (oracle errors) and penalty

A false positive here is a **test whose expected result is wrong** — it would raise a false alarm against a correct implementation.

- Each pricing row whose expected `beklenen_durum` or any filled expected amount/points differs from the oracle: **−1** (−2 if it hits a trap condition T1/T2/T3).
- Each state row whose expected last-event result or final state differs from the oracle, or whose prefix events are not all valid (precondition error): **−1**.
- Each pairwise row that violates KS-1/KS-2/KS-3 (an impossible E2E case): **−1**.
- Each confirmed claim in the report that a correct Ek-A example (1, 2, 3, 5) is wrong: **−2** (T4).
- Total penalty capped at **18** (half of max). Blank expected columns on a `KABUL` row are not penalised but do not earn K credit.
- Spec questions/ambiguities raised in the report are never penalised (only wrong oracles and false "spec is wrong" claims about correct examples).

How to check without the script: recompute the row with §2 above (use exact decimals, half-up for the 10 %, floor for points). Inputs written in a non-spec style (e.g. `Klasik`, `1499,90`) are normalised by the script with a warning unless the row itself expects `ERR_GECERSIZ_GIRDI` (then the literal value is used). `ORNEK-*` rows are ignored.

## 6. Scoring rubric

- K points: K1–K4 2 each (8), K5–K8 3 each (12), K9–K12 4 each (16) → **max 36**.
- Final = max(0, K points − min(penalty, 18)). Report also `percent = final / 36`.
- Missing deliverable file → related K items 0 (no penalty).
- Manual adjustments allowed only for K11c and T4 (and for a clearly mis-parsed row; record the reason).

Calibration (grader run on reference deliverables):
- `design_ref\gold` (42 pricing, 32 state, 12 pairwise rows, Ek-A finding): K 36/36, penalty 0 → **36/36**.
- `design_ref\naive` (typical intuitive pass: limits on NT/AT confusion, Ek-A 4 copied, ALTIN free HIZLI, KAPIDA limit on AT, rounding of ALTIN points, 3rd failed delivery = TESLIM_EDILEMEDI, 9-row matrix with a KS-2 violation): K 15/36, penalty 10 → **5/36**.

## 7. Objective checklist (manual grading fallback)

Pricing CSV (only rows whose every filled expected value is correct count):
- [ ] K1a 149.99 → ERR_MIN_SEPET and 150.00 → KABUL
- [ ] K1b 20000.00 → KABUL and 20000.01 → ERR_MAX_SEPET
- [ ] K2a member KITAP50 399.99 → KI 0.00 (KABUL)
- [ ] K2b member KITAP50 400.00 → KI 50.00
- [ ] K4a HIZLI + UZAK → ERR_TESLIMAT_BOLGE
- [ ] K4b KAPIDA + HIZLI/MAGAZA → ERR_KAPIDA_UYGUNLUK
- [ ] K5a DEFNE10, AT ≥ 1500.05 → KI 150.00
- [ ] K5b DEFNE10 half-up case (AT cents end in 5, under cap), e.g. 1234.55 → 123.46
- [ ] K6a ALTIN, odd base, floored points (e.g. NT 750.00 → 112)
- [ ] K6b points on NT with an applied coupon (e.g. AT 1000 DEFNE10 → 90)
- [ ] K9a coupon applied, NT = 750.00, correct KU (0.00 STANDART non-ALTIN / 40.00 HIZLI)
- [ ] K9b coupon applied, NT = 749.99, correct KU (39.90 / 64.90 UZAK / 79.90 HIZLI)
- [ ] K10a KAPIDA, OT = 5000.00 → KABUL
- [ ] K10b KAPIDA, OT = 5000.01 → ERR_KAPIDA_LIMIT
- [ ] K11a non-ALTIN STANDART UZAK NT ≥ 750 → KU 25.00
- [ ] K11b ALTIN STANDART UZAK → KU 0.00

State CSV:
- [ ] K3a rejected event in a non-terminal state (not HAZIRLANIYOR+IPTAL), state unchanged
- [ ] K3b event in IPTAL_EDILDI / IADE_EDILDI / DEPOYA_DONDU rejected
- [ ] K7a HAZIRLANIYOR + IPTAL(MUSTERI) → ERR_GECERSIZ_GECIS, HAZIRLANIYOR
- [ ] K7b HAZIRLANIYOR + IPTAL(OPERATOR) → KABUL, IPTAL_EDILDI
- [ ] K8a IADE_TALEBI(gun=14) → KABUL, IADE_TALEP_EDILDI
- [ ] K8b IADE_TALEBI(gun=15) → ERR_IADE_SURESI, TESLIM_EDILDI

Matrix CSV:
- [ ] K12 all 59 feasible pairs, 0 violations, ≤ 20 rows

Report:
- [ ] K11c Ek-A Örnek 4 discrepancy reported
- [ ] T4 no false "example is wrong" claim about Örnek 1/2/3/5

Then count oracle errors per §5.

## 8. Extra correct values often seen (not scored, but oracle-checked)

| Input | Correct result |
|---|---|
| `ZAMAN_ASIMI` | KABUL, IPTAL_EDILDI |
| KAPIDA order, empty sequence | KABUL, ONAYLANDI |
| KAPIDA order, `ODEME_BASARILI` | ERR_GECERSIZ_GECIS, ONAYLANDI |
| `ODEME_BASARISIZ` | KABUL, ODEME_BEKLENIYOR |
| 3rd `TESLIM_BASARISIZ` (after 2× fail + YENIDEN_DAGITIM) | KABUL, DEPOYA_DONDU |
| 2nd `TESLIM_BASARISIZ` | KABUL, TESLIM_EDILEMEDI |
| `... IADE_TALEBI(gun=3) > IADE_RED > IADE_TALEBI(gun=5)` | ERR_IADE_TEKRAR, TESLIM_EDILDI |
| `... IADE_RED > IADE_TALEBI(gun=20)` | ERR_IADE_SURESI (time is checked first) |
| `ODEME_BASARILI > IPTAL` (no actor) | ERR_GECERSIZ_GIRDI, ONAYLANDI |
| `... KARGOYA_VER > IPTAL` (no actor) | ERR_GECERSIZ_GECIS (state check precedes params) |
| `IADE_TALEBI(gun=-1)` from TESLIM_EDILDI | ERR_GECERSIZ_GIRDI |
| Pricing `kupon=defne10` | ERR_KUPON_GECERSIZ (case-sensitive) |
| Pricing `kupon=XYZ`, AT 100.00 | ERR_KUPON_GECERSIZ (precedence over MIN) |
| Pricing AT 100.00, HIZLI + UZAK | ERR_MIN_SEPET |
| MISAFIR + KITAP50, AT 500.00 | KABUL, KI 0.00 |
| MAGAZA + UZAK (or empty bölge) | KU 0.00 |
| MISAFIR STANDART UZAK AT 749.99 | KU 64.90, OT 814.89 |
| AT `150.005` / `0.00` / `1.499,90` (literal) | ERR_GECERSIZ_GIRDI |

## 9. Running the grader

```
python C:\projeler\TestSkills\evals\keys\design_grader.py <run>\cikti [--json out.json] [--verbose]
python C:\projeler\TestSkills\evals\keys\design_grader.py --selftest
```

Verification performed when the trial was built: `--selftest` passes (Ek-A 1/2/3/5 reproduce, Ek-A 4
differs as planted, K9/K10/K5 reference values, T1/T2, 3rd-failure → DEPOYA_DONDU, 59 feasible pairs);
the pricing oracle was cross-checked against an independent integer-cents Node.js implementation on
25,092 input combinations (0 mismatches); gold = 36/36, naive = 5/36; the templates parse and their
`ORNEK` rows are oracle-correct; format variants (BOM, CRLF, comma decimals, Turkish headers/values,
`→` separators, `IPTAL(MUSTERI)` shorthand, comma-delimited CSV) are parsed.
