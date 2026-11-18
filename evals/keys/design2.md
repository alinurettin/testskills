# KEY — trial-design2 (GÜM v3.2 test case design, Poyraz Kargo)

Evaluator-only answer key. Never place this file, `design2_grader.py` or `design2_ref/` in an agent workspace.

- Trial folder: `C:\projeler\TestSkills\evals\trial-design2\` (the agent gets `TASK.md` + `girdiler\` only; see `RUN.md`)
- Kind: **test case design from a precise specification** — no system under test, no server, nothing time-sensitive.
- Grader: `C:\projeler\TestSkills\evals\keys\design2_grader.py` (Python 3 standard library, deterministic). **The script result is final; there are no manual confirmation items.**
- Reference deliverables: `design2_ref\gold\` (100 / 100) and `design2_ref\naive\` (9 / 100)
- Regression test: `python -m unittest tests.test_trial_design2`

## 1. What the agent must deliver

| File (under `cikti/`) | Row budget | Area | Max |
|---|---|---|---|
| `ucret-testleri.csv` | 40 | Pricing and promised delivery date | 44 |
| `durum-testleri.csv` | 30 | Shipment life cycle | 22 |
| `konfigurasyon-matrisi.csv` | 24 | Configuration matrix | 14 |
| `spesifikasyon-bulgulari.csv` | 8 | Specification findings | 20 |
| `test-tasarimi.md` | — | Short design note, **not scored, not read** | 0 |

Maximum **100**.

### Format rules that are graded exactly

They are stated in TASK.md and in the specification (§3.1, §3.2), so the grader applies them literally:

- UTF-8, separator `;`, first line = the template header. A file that fails this is reported `NOT GRADED` and its area scores 0 (no penalty). A missing file is treated the same way.
- Codes are case-sensitive (spec §3.1): `bireysel` is `ERR_GECERSIZ_GIRDI`, `IPTAL(aktor=operator)` is `ERR_GECERSIZ_GIRDI` (rule 10.5-3), `transfere_ver` is an unknown event (rule 10.5-1). Nothing is folded or guessed.
- Expected numbers use a decimal point and no thousands separator; dates are `YYYY-AA-GG`. `172,54` or `14.03.2028` is a wrong expected value.
- A `KABUL` pricing row needs all four expected columns; an error row must leave them empty (§9.2). A state row needs all three expected columns.

### Leniency (only where the meaning cannot change)

BOM, CRLF, blank lines, spaces around a cell, trailing zeros in an expected number (`2` = `2.0`, `172.540` = `172.54`), an unquoted `;` inside the last free-text column, and the spelling of a reference or type in the findings file (`Ek-A Örnek 4` = `A-4`, `G-11` = `G11`, `§9.3` = `9.3`, `ÇELİŞKİ` = `CELISKI`).

### Row budgets

Only the first N data rows of a file are graded (N = budget, `ORNEK-` rows are never counted). Rows after that are **ignored completely**: they earn no coverage and cannot be penalised individually. A file that exceeds its budget costs a flat **−2** in its area (and, for the matrix, item C3).

### Incomplete rows

A row whose filled expected values are all correct but which leaves an expected column blank is *incomplete*: it earns nothing and costs nothing.

## 2. Reference model (the oracle, derived strictly from the specification)

### 2.1 Pricing and delivery date (spec §2–§9, Ek-B)

1. Validation → `ERR_GECERSIZ_GIRDI`: enum not an exact code; `agirlik_kg` / `beyan_degeri` not `^\d+(\.\d{1,2})?$` or not > 0; a dimension not `^\d+$` or < 1; `kabul_zamani` not `YYYY-MM-DD HH:MM`, not a real date/time, or outside 2028-01-01 00:00 … 2028-12-15 23:59. `kampanya_kodu` is never a validation error.
2. `ERR_BOYUT`: a side > 100 or the sum of the sides > 150.
3. `ERR_AGIRLIK`: GA > 30.00.
4. HA = half-up(en × boy × yük / 3000, 2 decimals); UA = max(GA, HA) rounded **up** to a multiple of 0.5. `ERR_HACIM`: UA > 40.0.
5. `ERR_HIZMET_BOLGE`: `AYNI_GUN` outside `SEHIRICI`.
6. `ERR_AYNI_GUN_SAAT`: `AYNI_GUN` and (acceptance day is not a business day, or time > 11:00).
7. `ERR_KAMPANYA_GECERSIZ`: non-empty code other than `BAHAR15`.
8. `ERR_BEYAN_LIMIT`: declared value > 50000.00. **Not in the §9.3 list** (planted D3): when it occurs together with a listed error, the oracle accepts the first listed error *or* `ERR_BEYAN_LIMIT`.
9. Tariff by zone and UA (§5.1); TB = half-up(tariff × 1.00 / 1.35 / 1.80).
10. Discount (§6): contract = half-up(12 % TB) for `KURUMSAL`; campaign = min(half-up(15 % TB), 40.00) if the code is `BAHAR15` and the **acceptance date** is in 2028-03-01 … 2028-05-31; the larger one applies; then the floor: if TB − IT < 55.00, IT = TB − 55.00. `AYNI_GUN`: IT = 0.00.
11. NTB = TB − IT; YE = half-up(6.5 % **NTB**); SP = max(half-up(0.8 % declared value), 15.00) or 0.00; MA = NTB + YE + SP; KDV = half-up(20 % MA); TU = MA + KDV.
12. Business day = Monday–Saturday not listed in Ek-B. Processing day = acceptance day if it is a business day and the time is before the cut-off (Mon–Fri 17:00, Sat 13:00), otherwise the next business day. **Exactly at the cut-off both readings are accepted** (planted D2). Delivery = N-th business day after the processing day (§8.3); for `UZAK`, a Saturday result moves to the next business day (§8.4). `AYNI_GUN`: delivery = acceptance date.

Tariff, for reference: bands ≤ 1.0 / ≤ 5.0 / ≤ 10.0 kg = 60 / 85 / 120 (`SEHIRICI`), 75 / 105 / 150 (`YAKIN`), 95 / 135 / 195 (`UZAK`); above 10.0 kg +4.50 / +6.00 / +8.25 per 0.5 kg.

### 2.2 Life cycle (spec §10)

Initial state `KABUL_EDILDI`, counters 0. Transitions G1–G17 as in the specification table. Processing order: unknown event → `ERR_GECERSIZ_GIRDI`; event not in the table for the state → `ERR_GECERSIZ_GECIS`; missing / extra / invalid parameter → `ERR_GECERSIZ_GIRDI`; guard failure → the listed error; any error leaves state and counters unchanged.

Facts the grader derives by breadth-first search over (state, `deneme_sayisi`, `adres_degisikligi_sayisi`):

- **16 live transitions.** G11 can never fire: `TESLIM_EDILEMEDI` is entered only through G7 (counter 1 or 2) and G13 (self-loop); the third failed attempt takes G8 to `SUBEDE_BEKLIYOR` (planted D4).
- **29 feasible ordered pairs of consecutive transitions** (1-switch): G1→{G3,G4,G5}; G5→{G3,G4}; G3→{G6,G7,G9}; G7→{G10,G12,G13}; G13→{G10,G12}; G10→{G6,G7,G8,G9}; G16→{G6,G7,G8,G9}; G12→{G14,G15,G16}; G8→{G14,G15}; G4→G17; G9→G17; G15→G17. (G2 belongs to no pair. G3→G8, G8→G16, G5→G5, G5…G13 are infeasible because of the counters.)
- Every path ends in exactly one of 13 endings (G2; G4→G17 ×2 predecessors; …→G6 ×3; …→G9→G17 ×3; …→G14 ×2; …→G15→G17 ×2), so full 1-switch coverage needs at least 13 rows; full marks in the area need at least 26 rows of the 30 allowed (gold uses 27).

### 2.3 Configuration space (spec §11)

Six factors (5 × 2 × 3 × 3 × 4 × 3 = 1080 combinations), constraints KS-1 … KS-7 → **394 supported combinations, 152 feasible value pairs, 19 feasible `hizmet` × `bolge` × `teslim_noktasi` triples**. `API` with `ALICI_ODEMELI` is infeasible only by implication (KS-3 + KS-4). Lower bound: 18 non-`AYNI_GUN` triples + 5 `AYNI_GUN` rows (one per `kanal`, all `SEHIRICI` / `ADRES`) = **23 rows**; a 23-row solution exists (gold). A plain greedy generator returns 23–26 rows depending on tie-breaking; "pairwise set plus the missing triples appended" returns 26–30. The budget is 24.

## 3. Scored items — pricing (44 points, `ucret-testleri.csv`)

A sub-check is met by rows that are **correct** (every expected value equals the oracle) and inside the row budget. "Pure" error row = the named error is the only error condition of the row.

| Item | Pts | Level | Acceptance rule |
|---|---|---|---|
| P1 | 2 | easy | GA = 30.00 → `KABUL` **and** GA = 30.01 → `ERR_AGIRLIK` (pure). Both needed. |
| P2 | 2 | easy | (a) 1: longest side = 100 → `KABUL` and a row with longest side = 101, sum ≤ 150 → `ERR_BOYUT`. (b) 1: sum = 150 → `KABUL` and a row with sum = 151, sides ≤ 100 → `ERR_BOYUT`. |
| P3 | 2 | medium | (a) 1: UA = 40.0 → `KABUL`. (b) 1: UA = 40.5 → `ERR_HACIM` (pure). Reachable only through the volume, e.g. 50×50×48 / 49×50×49. |
| P4 | 2 | medium | `KABUL` rows with UA on both sides of each tariff band edge: 1.0 & 1.5, 5.0 & 5.5, 10.0 & 10.5. All three pairs 2, two pairs 1. |
| P5 | 4 | hard | Two-stage weight rounding (§2.3), `KABUL` rows where the volume decides UA: (a) 2: raw HA strictly above a 0.5 step but rounding **down** to it at 2 decimals (e.g. 10×19×79 → 5.0033 → 5.00 → UA 5.0; "round the raw value up" gives 5.5). (b) 2: raw HA exactly x.xx5 just above a 0.5 step, i.e. volume = 1500k + 15 with GA ≤ k/2 (e.g. 15×77×13 → 5.005 → 5.01 → UA 5.5; binary floating point and banker's rounding give 5.0). |
| P6 | 2 | hard | A `KABUL` row whose tariff × coefficient ends in exactly half a kuruş (e.g. `UZAK` `EKSPRES` UA 11.0: 211.50 × 1.35 = 285.525 → 285.53; `SEHIRICI` `EKSPRES` UA 10.5: 168.075 → 168.08). |
| P7 | 5 | hard | `KURUMSAL` + `BAHAR15` inside the campaign window, not `AYNI_GUN`, floor not binding: (a) 1: 15 % ≤ 40.00 and the campaign applies; (b) 2: 15 % > 40.00 and the capped 40.00 still beats 12 % (TB 266.70 … 333.29); (c) 2: 12 % > 40.00, the contract discount applies (TB ≥ 333.38). In between the two amounts are equal and the row earns neither. Crossover example: `UZAK` `STANDART` UA 18.0 (TB 327.00 → IT 40.00) vs UA 18.5 (TB 335.25 → IT 40.23). |
| P8 | 3 | medium | (a) 2: discount limited by the 55.00 floor (only TB 60.00: `SEHIRICI`, `STANDART`, UA ≤ 1.0 → IT 5.00). (b) 1: `AYNI_GUN` row of a `KURUMSAL` customer or with a valid `BAHAR15` → IT 0.00. |
| P9 | 5 | hard | `BAHAR15` rows (not `AYNI_GUN`) in which the campaign changes IT: (a) 1: accepted 2028-02-29 → not applied; (b) 1: accepted 2028-03-01 → applied; (c) 1: 2028-05-31 applied **and** 2028-06-01 not applied; (d) 2: acceptance date and processing day on different sides of the window (e.g. 2028-05-31 17:30 → applied although processed on 06-01; 2028-02-29 17:30 → not applied although processed on 03-01). |
| P10 | 3 | medium | (a) 1: declared value whose 0.8 % is below 15.00 → premium 15.00. (b) 2: 50000.00 → `KABUL` and 50000.01 → `ERR_BEYAN_LIMIT` (pure). |
| P11 | 5 | hard | (a) 1: weekday cut-off — an on-time row (16:59 or 17:00, processed the same day) and a later row (17:00 or 17:01, processed the next business day), the on-time row earlier than the late row; (b) 1: the same on a Saturday (12:59 / 13:00 / 13:01); in (a) and (b) both rows must be **date-sensitive**: for that zone, service and day the delivery date differs between same-day and next-day processing (e.g. `UZAK` `STANDART` accepted on a Monday is not: both give the following Monday). (c) 1: acceptance on a Sunday or an Ek-B day (not `AYNI_GUN`). (d) 1: an Ek-B day that is not a Sunday lies strictly between acceptance date and delivery date. (e) 1: 2028-02-29 lies in acceptance date … delivery date. |
| P12 | 3 | hard | (a) 2: `UZAK` row whose N-th business day is a Saturday → moved to the next business day. (b) 1: a row of another zone whose delivery date is a Saturday. |
| P13 | 2 | easy | (a) 1: `AYNI_GUN` at 11:00 → `KABUL` and at 11:01 on a business day → `ERR_AYNI_GUN_SAAT` (pure). (b) 1: `AYNI_GUN` at or before 11:00 on a Sunday / Ek-B day → `ERR_AYNI_GUN_SAAT` (pure). |
| P14 | 2 | easy | (a) 1: `ERR_HIZMET_BOLGE` (pure). (b) 1: two error rows with **different** sets of two or more simultaneous §9.3 errors, each expecting the first one. |
| P15 | 2 | easy | (a) 1: `ERR_GECERSIZ_GIRDI` caused by a malformed or out-of-range number or date (not only by an unknown enum). (b) 1: `ERR_KAMPANYA_GECERSIZ` (pure). |

Hard items: P5, P6, P7, P9, P11, P12 = 24 of 44.

## 4. Scored items — life cycle (22 points, `durum-testleri.csv`)

Coverage is collected from correct rows only. All events of a correct row that fire a transition count for Z1 and Z2; error results count only as the **last** event of a row.

| Item | Pts | Level | Acceptance rule |
|---|---|---|---|
| Z1 | 2 | easy | Live transitions exercised: 16 of 16 → 2; 14–15 → 1. |
| Z2 | 7 | hard | Feasible pairs of consecutive transitions: 29 of 29 → 7; ≥ 90 % (27) → 5; ≥ 75 % (22) → 3; ≥ 50 % (15) → 1. |
| Z3 | 3 | medium | States in which a row ends with an event that is not in the table for that state (`ERR_GECERSIZ_GECIS`, state unchanged): 9 of 9 → 3; 7–8 → 2; 5–6 → 1. |
| Z4 | 4 | hard | Guard failures as last event, 7 checks: `ERR_YETKI`; `ERR_ADRES_LIMIT` in `TRANSFERDE`; `ERR_ADRES_LIMIT` in `TESLIM_EDILEMEDI`; `ERR_ADRES_LIMIT` in `TESLIM_EDILEMEDI` after the address was changed in `TRANSFERDE` (shared counter); `ERR_DENEME_LIMITI`; `ERR_BEKLEME_SURESI`; `ERR_SURE_DOLMADI`. 7 → 4; 5–6 → 3; 3–4 → 2; 1–2 → 1. |
| Z5 | 2 | medium | (a) 1: `SUBEDEN_TESLIM(gun=5)` accepted (anywhere in a correct row) and `SUBEDEN_TESLIM(gun=6)` → `ERR_BEKLEME_SURESI`. (b) 1: `SURE_DOLDU(gun=6)` accepted and `SURE_DOLDU(gun=5)` → `ERR_SURE_DOLMADI`. |
| Z6 | 2 | medium | (a) 1: a rejected last event in a state where `deneme_sayisi` ≥ 1, with the unchanged counter expected. (b) 1: a correct row in which a `RED` refusal (G9) follows at least one counted attempt (counter stays). |
| Z7 | 2 | medium | (a) 1: an event allowed in the state with a missing / invalid parameter → `ERR_GECERSIZ_GIRDI`. (b) 1: rule order: an event **not** allowed in the state and with a bad parameter → `ERR_GECERSIZ_GECIS`, or an undefined event name in a final state → `ERR_GECERSIZ_GIRDI`. |

## 5. Scored items — configuration matrix (14 points, `konfigurasyon-matrisi.csv`)

Coverage is collected from supported rows inside the budget.

| Item | Pts | Level | Acceptance rule |
|---|---|---|---|
| C1 | 6 | hard | `hizmet` × `bolge` × `teslim_noktasi` triples: 19 of 19 → 6; 17–18 → 4; 14–16 → 2. |
| C2 | 6 | hard | Value pairs over all six factors: 152 of 152 → 6; ≥ 95 % (145) → 4; ≥ 85 % (130) → 2. |
| C3 | 2 | easy | At least 12 supported rows, no unsupported or unknown row, file inside the budget. |

## 6. Specification findings (20 points, `spesifikasyon-bulgulari.csv`)

Graded by `bolumler` and `tur` only; the free text is never read. A row with an unknown type or with more than four places is ignored. A row is one finding: it can earn one defect.

### 6.1 Planted defects

| Id | Pts | Subtlety | What is wrong | Credited when | Oracle |
|---|---|---|---|---|---|
| D1 | 3 | low for agents that recompute | Ek-A **A-4** contradicts §7.1: the fuel surcharge is taken on TB (174.00 → 11.31) instead of NTB (153.12 → 9.95); printed KDV 32.89 / TU 197.32, correct 32.61 / 195.68 | `tur` = `CELISKI`, places include `A-4` | Rules prevail (Ek-A header): TU 195.68 |
| D2 | 4 | medium | §2.4 "accepted **before** the cut-off" vs §8.2 "up to and **including** the cut-off": the cut-off minute itself (17:00, Saturday 13:00) is processed on different days | `tur` = `CELISKI` or `BELIRSIZLIK`, places include `2.4` **and** `8.2` | Both delivery dates accepted for a row exactly at the cut-off |
| D3 | 4 | medium | `ERR_BEYAN_LIMIT` (§7.2) is missing from the precedence list §9.3: undefined result when it coincides with another error | `tur` = `BELIRSIZLIK` or `CELISKI`, places include `7.2` **and** `9.3` | Either the first listed error or `ERR_BEYAN_LIMIT` |
| D4 | 5 | high | **G11** is a dead transition (see §2.2) | `tur` = `ERISILEMEZ` or `CELISKI`, places include `G11` | G11 is not a coverage target; a row that claims to reach it has an invalid precondition or a wrong expectation |
| D5 | 4 | medium | Missing unit: `gun` (§10.3) and the 5-day waiting period (§10.6, G14, G15) do not say calendar days or business days, although §8 distinguishes them and branches are closed on Sundays | `tur` = `BELIRSIZLIK`, places include one of `10.3`, `10.6`, `G14`, `G15` | No effect (`gun` is a number in the tests) |

### 6.2 Traps — look like defects, are resolved by another clause (−3 each)

| Id | Looks like | Why it is not a defect | Counted when |
|---|---|---|---|
| T1 | A correct Ek-A example "is wrong": A-2 (delivery 06-19, not Saturday 06-17), A-3 (UA 5.0 from HA 5.0033; premium 15.00 for 1.200 TL), A-5 (`BAHAR15` applied although processed on 06-01), A-6 (IT 40.00, not 12 %; TB 285.53), A-7 (no 12 % on `AYNI_GUN`), A-1 | §8.4; §2.3 and §7.2; §6.2 (acceptance date); §6.2–6.3 and §2.2; §6.5 | `tur` = `CELISKI`, places include `A-1`, `A-2`, `A-3`, `A-5`, `A-6` or `A-7` — **per example** |
| T2 | G16 "can never fire because `SUBEDE_BEKLIYOR` is entered after three attempts" | G12 (`SUBEYE_YONLENDIR`) enters `SUBEDE_BEKLIYOR` with counter 1 or 2; both branches of G16 are live | `tur` = `ERISILEMEZ`, places include `G16` |
| T3 | Saturday cut-off 13:00 (§8.2) vs counters open until 15:00 (§8.6) | Acceptance hours are not the cut-off; §8.2 says what happens to shipments accepted after the cut-off | `tur` = `CELISKI` or `BELIRSIZLIK`, places include `8.2` **and** `8.6` |
| T4 | GA limit 30 kg (§4.2) vs UA up to 40 kg (§4.5) / tariff above 30 kg (§5.1) | UA can exceed GA through the volumetric weight (§4.4) | `tur` = `CELISKI` or `ERISILEMEZ`, places include `4.2` and (`4.5` or `5.1`) |

A row that matches a defect is credited and not examined for traps. Rows with type `ONERI`, duplicates, and defect-type rows that match neither a defect nor a trap (unplanted remarks) are **neutral**; only the row budget limits them.

## 7. Penalties and final score

| Event | Cost | Area |
|---|---|---|
| Pricing row inside the budget with a wrong `beklenen_sonuc` or any wrong filled expected value (also: amounts filled on an error row) | −2 per row | pricing |
| State row with a wrong expected result / state / counter, or with a precondition event that is rejected | −2 per row | life cycle |
| Matrix row that violates KS-1 … KS-7 or contains an unknown value | −2 per row | matrix |
| Trap reported as a defect (§6.2) | −3 per trap | findings |
| File exceeds its row budget | −2 flat | its area |

Area score = max(0, item points − penalties of that area). **Final = sum of the four area scores**, 0 … 100. There is no other cap and no manual adjustment. A dispute about the oracle is settled by correcting the key and the grader, then re-running the script on all runs.

## 8. Known limits, and unplanted remarks seen so far

- Findings are matched by place and type, so a different remark filed on the same place with the same type would also be credited (most plausible for D5). This is the price of having no manual step; the four-place limit and the one-defect-per-row rule keep it small.
- Look-alikes that are **not** penalised (neutral): §8.1 "Saturday is a business day" vs §8.4; "what if both discounts are equal" (§6.3 answers it); "leading zeros" (§3.2 answers it); "G10's guard is always true" filed without G11.
- Unplanted but real: *(none recorded yet — add here after verifying against the specification)*.

## 9. Calibration

Grader run on the reference deliverables:

- `design2_ref\gold` — 36 pricing rows, 27 state rows, 23 matrix rows, 5 findings: **100 / 100**, no penalty.
- `design2_ref\naive` — a quick intuitive pass: 16 pricing rows (copies A-4, forgets the `UZAK` Saturday rule, no derived boundaries), 14 state rows (third failed attempt expected in `TESLIM_EDILEMEDI`, 8 of 16 transitions, 6 of 29 pairs), a 13-row matrix made by eye with a KS-7 violation and 10 of 19 triples, 6 findings (A-4 and the unit found, trap T3 reported): **9 / 100** (pricing 8 − 4, life cycle 3 − 2, matrix 0 − 2 → 0, findings 7 − 3).

- A constructed "strong but imperfect" variant of gold (not kept as a file): no exact-half rounding rows, no discount crossover, no holiday or Saturday-delivery row, one 1-kuruş slip, three long state paths missing, a first-best greedy matrix of 25 rows, three of five defects plus trap T3: **62 / 100** (29 + 17 + 8 + 8). It shows that the partial-credit steps land mid-range.

Target for a strong unaided agent in about 40 minutes: roughly 55–75. **The pilot did not confirm it.** One unaided pilot run (Claude Fable 5.2, no time limit, 45 minutes, 2026-11-18) scored **95 / 100**: it wrote its own oracle, a state-machine simulator, a search for the matrix (23 rows) and 39 mutants to check its pricing rows, and found all five planted defects and no trap. For a model of that class the trial is still at the ceiling; whether it separates weaker models is not measured. The five points it lost are P1, P3, P13 and P14: its rows for 30.01 kg, UA 40.5, 11:01 and the service/zone error each carry a second, lower-priority error condition (to test the precedence in the same row), and the grader credits a boundary only in a row with a single error condition. That rule follows the one-invalid-value-per-negative-test convention; it is strict, and it applies to every run alike.

Verification performed when the trial was built: `--selftest` passes (Ek-A as printed: A-1, A-2, A-3, A-5, A-6, A-7 reproduce, A-4 differs exactly in YE / KDV / TU; both readings at D2 and D3; rounding cases; 16 live transitions, 29 pairs; 394 / 152 / 19); the pricing oracle agrees with an independent implementation in exact fractions on 300,000 boundary-heavy random inputs (0 mismatches); the unit test parses Ek-A and Ek-B out of the specification file and compares them with the oracle; about thirty cases were recomputed by hand (§10 lists the ones tied to defects and traps).

## 10. Hand-checked reference values

| Case | Input | Correct result |
|---|---|---|
| D1 (A-4 by the rules) | KURUMSAL, 12.00 kg, 30×30×30, YAKIN, STANDART, 2028-04-11 11:20 | UA 12.0, TB 174.00, IT 20.88, NTB 153.12, YE 9.95, KDV 32.61, **TU 195.68**, 2028-04-14 |
| D2 | BIREYSEL, 2.00 kg, 20×20×10, YAKIN, EKSPRES, 2028-03-21 17:00 | TU 181.15; delivery **2028-03-22 or 2028-03-23** (16:59 → 03-22 only, 17:01 → 03-23 only) |
| D3 | GA 30.01 and declared value 50000.01 | `ERR_AGIRLIK` **or** `ERR_BEYAN_LIMIT` |
| D4 | `TRANSFERE_VER > DAGITIMA_CIKAR > 3 × (TESLIM_BASARISIZ(neden=ADRESTE_YOK) [> YENIDEN_DAGIT])` | third failure → `SUBEDE_BEKLIYOR`, counter 3; then `YENIDEN_DAGIT` → `ERR_DENEME_LIMITI` (G16), never G11 |
| D5 | `… > SUBEYE_YONLENDIR > SUBEDEN_TESLIM(gun=5)` / `(gun=6)` | `KABUL` / `ERR_BEKLEME_SURESI` — whatever the unit |
| T1 A-2 | BIREYSEL, 3.20 kg, 40×30×25, UZAK, STANDART, Mon 2028-06-12 09:30 | UA 10.0, TU 249.22, 5th business day Sat 06-17 → **2028-06-19** |
| T1 A-3 | KURUMSAL, 4.80 kg, 10×19×79, SEHIRICI, EKSPRES, 1200.00, Fri 2028-02-25 16:10 | HA 5.0033 → 5.00 → UA 5.0; TB 114.75, IT 13.77, SP 15.00, TU 147.05, Sat 2028-02-26 |
| T1 A-5 | BIREYSEL, 6.40 kg, 30×20×20, YAKIN, EKSPRES, BAHAR15, Wed 2028-05-31 17:45 | TB 202.50, IT 30.38 (30.375 half-up), TU 219.97, processed 06-01, delivery 2028-06-02 |
| T1 A-6 | KURUMSAL, 11.00 kg, 30×30×20, UZAK, EKSPRES, BAHAR15, 20000.00, Sat 2028-04-08 12:40 | TB 285.53, 12 % = 34.26, 15 % = 42.83 → 40.00, SP 160.00, TU 505.79, 2028-04-11 |
| T1 A-7 | KURUMSAL, 0.80 kg, 20×15×5, SEHIRICI, AYNI_GUN, Thu 2028-09-14 10:05 | TB 108.00, IT 0.00, TU 138.02, 2028-09-14 |
| T2 | `TRANSFERE_VER > DAGITIMA_CIKAR > TESLIM_BASARISIZ(neden=ADRESTE_YOK) > SUBEYE_YONLENDIR > YENIDEN_DAGIT` | `KABUL`, `DAGITIMDA`, counter 1 (G16 fires) |
| T3 | BIREYSEL, 1.00 kg, 10×10×10, SEHIRICI, EKSPRES, Sat 2028-03-11 14:00 | priced normally (TU 103.52), processed Mon 03-13, delivery 2028-03-14 |
| T4 | BIREYSEL, 10.00 kg, 50×50×42, SEHIRICI, STANDART, 2028-03-06 10:00 | HA 35.00 → UA 35.0, TB 345.00, YE 22.43, KDV 73.49, TU 440.92 |
| Rounding | 15×77×13 (15015 cm³) with GA 4.20 | HA 5.005 → 5.01 → UA 5.5 |
| Crossover | KURUMSAL + BAHAR15, UZAK STANDART, UA 18.0 / 18.5 | TB 327.00 → IT 40.00 (TU 366.79) / TB 335.25 → IT 40.23 (TU 377.04) |
| Floor | BIREYSEL, 1.00 kg, SEHIRICI, STANDART, BAHAR15, 2028-03-01 | TB 60.00, 15 % = 9.00 → IT 5.00, YE 3.58, TU 70.30 |
| Leap day | YAKIN STANDART accepted Mon 2028-02-28 17:30 | processed Tue 02-29, delivery 2028-03-03 |
| Holiday | YAKIN STANDART accepted Thu 2028-05-18 10:00 | Fri 05-19 (B-4) skipped, Sat counts → 2028-05-23 |

## 11. Running the grader

```
python C:\projeler\TestSkills\evals\keys\design2_grader.py <run>\cikti [--json out.json] [--verbose]
python C:\projeler\TestSkills\evals\keys\design2_grader.py --selftest
```

The last line of the output is `FINAL SCORE: x / 100  (p%)`.
