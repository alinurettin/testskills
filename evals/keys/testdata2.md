# Key — trial-testdata2 (test data generation + masking, harder)

EVALUATOR-ONLY. Do not show to the agent. Trial folder: `evals/trial-testdata2/`.
Objective grader: `evals/keys/testdata2_grade.py` (stdlib). Truth file: `evals/keys/testdata2_truth.json`.
Input builder: `evals/keys/testdata2_build.py`. Reference solution (scores 100): `evals/keys/testdata2_ref/`.

## Scenario

Fictional Pusula Dijital Bank A.Ş. migrates its core banking system. The Turkish user asks for
(1) a synthetic 3-table data set (musteri / hesap / islem) that satisfies an import specification with
inter-field rules and mandatory boundary rows, and (2) deterministic masking of a production-like
extract (122 customers, 205 accounts, 2024 transactions; fully synthetic) under a written masking
policy, plus a short report. Everything needed to score full marks is stated in
`girdiler/uretim_kurallari.md` and `girdiler/maskeleme_politikasi.md`; the planted difficulties
below are concrete data situations that a quick pass misses.

## Scoring overview (max 100)

| Item | Topic | Difficulty | Severity if missed | Points |
|---|---|---|---|---|
| K1 | Part 1: customer-type identity rules (TCKN vs VKN checksums, fields, formats) | easy | High | 6 |
| K2 | Part 1: date-order rules + simple boundary rows | easy | High | 6 |
| K3 | Part 1: 29 February / 18th-birthday boundary | hard | Medium | 10 |
| K4 | Part 1: balance = Σ transactions, running-balance limits, 0.00 / −limit boundaries | hard | High | 10 |
| K5 | Part 1: composite key, FK on two columns, IBAN derivation, counter-IBAN rules | medium | High | 8 |
| K6 | Part 2: direct PII columns masked validly (incl. SAHIS VKN, phone skeleton) | easy | Critical | 6 |
| K7 | Part 2: numeric PII hidden in free text / counter-IBAN (all formats) | medium | Critical | 8 |
| K8 | Part 2: names and e-mails hidden in free text (Turkish casing, suffixes, third parties, SAHIS title) | hard | Critical | 10 |
| K9 | Part 2: joins preserved (composite key, FK, internal transfers) + determinism | medium | High | 8 |
| K10 | Part 2: masked IBAN validity/embedding + cross-format consistency | hard | High | 10 |
| K11 | Part 2: one constant date offset across mixed date formats | medium | Medium | 8 |
| K12 | Part 2: k-anonymity on (dogum_tarihi, il, ilce, cinsiyet) with unique outliers | hard | High | 10 |

Easy 18 pts, medium 32 pts, hard 50 pts.
Final score = grader `auto_total` (includes the automatic T4 penalty) − manual penalties (T1–T3, other
unfounded claims), floored at 0.

## Planted items

### K1 — Customer-type identity rules (Part 1) · easy · 6 pts
- What: BIREYSEL rows need a valid TCKN, empty VKN, ad/soyad, dogum_tarihi, cinsiyet E/K; KURUMSAL rows
  need a valid VKN (Ek A algorithm), empty TCKN, unvan, sirket_turu AS/LTD/SAHIS, kurulus_tarihi; IDs
  unique; il/ilçe from Ek B; e-mail `^[a-z0-9._-]+@example\.(com|test)$` unique; phone `+90 500 ddd dd dd`;
  ≥25 % KURUMSAL and ≥50 % BIREYSEL; exact header.
- Why: the import module rejects the whole file on one bad row; VKN checksum is less known than TCKN.
- Acceptance (grader rules M_FMT, M_TYPE, M_FIELDS, M_TCKN, M_VKN, M_IDUNIQ, M_ILCE, M_EMAIL, M_PHONE,
  M_MIX, HEADER): 0 violations → 6; violations ≤ 2 % of customer rows → 3; else 0.

### K2 — Date rules and simple boundaries (Part 1) · easy · 6 pts
- What: İK-02/03/04/08 (kayıt ≥ 18th birthday or ≥ kuruluş; age 18–100; açılış ≥ kayıt and ≥ 18th
  birthday / kuruluş; işlem between açılış and 2026-09-30) and boundary rows SD-1 (≥5 accounts opened
  on the owner's 18th birthday), SD-3 (≥3 corporate accounts opened on founding day), SD-4 (≥5 accounts
  with a transaction on the opening day), SD-5 (≥5 transactions on 2026-09-30), SD-8 (≥10 % of accounts
  on a boundary).
- Acceptance: date rules (M_DATES, H_DATES, I_DATE) 0 violations → 3 pts (≤2 % → 1.5); each of SD-1,
  SD-3, SD-4, SD-5, SD-8 met → 0.6 pts.
- Subtlety: an SD-1 account forces `kayit_tarihi` = 18th birthday as well (İK-02 + İK-04).

### K3 — 29 February boundary (Part 1) · hard · 10 pts
- What: SD-2 requires ≥2 SD-1 accounts of customers born on 29 February; İK-05 defines their 18th
  birthday as **1 March** (18 years after a leap year is never a leap year). The accounts must be opened
  exactly on 1 March and the customer's `kayit_tarihi` must also be 1 March (not earlier: İK-02).
- Why: `date.replace(year=y+18)` raises ValueError in Python; many implementations silently use
  28 February, which the spec defines as underage.
- Acceptance: SD-2 ≥ 2 and zero date-rule violations among rows of 29-Feb-born customers → 10;
  exactly one such account and zero violations → 5; else 0.

### K4 — Balances (Part 1) · hard · 10 pts
- What: İK-09 bakiye = exact Σ tutar; İK-10 running balance in (islem_tarihi, islem_id) order never below
  0.00 (VADESIZ) / −kmh_limiti (KMH); KMH only BIREYSEL + TRY with limit 1000–50000, VADESIZ limit 0.00;
  SD-6 ≥5 VADESIZ accounts hit exactly 0.00 after a transaction; SD-7 ≥3 KMH accounts hit exactly
  −kmh_limiti.
- Why: requires following each account chronologically; internal transfers move money between accounts;
  float accumulation breaks "kuruşu kuruşuna".
- Acceptance: H_BAL 0 violations → 4 (≤2 % → 2); H_RUN 0 → 3 (≤2 % → 1.5); H_TYPE 0 → 1; SD-6 met → 1;
  SD-7 met → 1.

### K5 — Keys and IBANs (Part 1) · medium · 8 pts
- What: (sube_kodu, hesap_no) unique, hesap_no `[1-9]\d{7}`, ≥3 hesap_no values in ≥2 branches (İK-12);
  islem FK uses both columns; IBAN = TR+kk+00990+0+sube+0000+hesap_no with valid mod-97, unique;
  HAVALE karsi_iban valid compact uppercase, ≠ own IBAN, internal or bank code 00991–00998, ≥20 % of
  HAVALE_GIDEN internal; type/sign rules; unique positive islem_id.
- Acceptance: H_PK 0 → 2; H_REPEAT ok → 1; H_FK + I_FK 0 → 1; H_IBAN 0 → 2; I_KARSI + I_INTERNAL 0 → 1;
  I_SIGN + I_ID 0 → 1.

Part 1 volume gate: if <150 customers, <300 accounts, <2000 transactions, a customer without account,
or <90 % of accounts with a transaction, every Part 1 item is halved.

### K6 — Direct PII columns (Part 2) · easy · 6 pts
- What (policy 5.1/5.2): for every row, tckn changed + valid + unique; ad+soyad changed; eposta changed,
  `@example.test`, unique; telefon changed with identical skeleton (non-digits and digit count) and leading
  `5` kept for mobiles (source phone column mixes `0532 123 45 67`, `+90 532 …`, `5321234567`,
  `(0532) 123-4567`); musteri_no changed `M\d{6}` unique; hesap_no changed `[1-9]\d{7}` with unique
  composite key; the 4 SAHIS customers' VKN changed and still valid (M416053, M696512, M803279, M995021);
  hesap.iban changed.
- Acceptance: 8 sub-checks, each pass/fail on 100 % of rows; score = 6 × passed/8.

### K7 — Numeric PII in free text and counter-IBANs (Part 2) · medium · 8 pts
- Planted (musteri.notlar): TCKN `491 508 845 04` (Ayşe Yılmaz), `572.690.143.30` (Hatice Arslan),
  third-party TCKN `28155-981-616` (vekil) and `58518515660` (SAHIS owner); phones `0 (554) 838 24 21`,
  `+905429748704`, bare `5536961795`, third-party `0555-044-4637`, third-party `0090 532 342 52 76`;
  IBAN `tr41 0099 0002 0700 0010 7151 61` (lower case, spaced). One note is multi-line (quoted CRLF).
- Planted (islem.aciklama): `0 (543) 914 03 92`, `+90 554 838 2421`, spaced external IBAN after
  "HAVALE: AHMET ÇAKIR /", lower-case spaced own IBAN after "Virman - kendi hesabına".
- islem.karsi_iban: ~900 IBANs, ~18 % spaced, ~6 % spaced lower case, ~6 % compact lower case.
- Acceptance (automatic): every original TCKN, phone national number (10 digits) and IBAN tail
  (IBAN[4:], 22 digits) searched as a substring of the digits of every masked `notlar`, `aciklama` and
  `karsi_iban` cell. Residual hits 0 → 8; ≤2 → 5.6; ≤5 → 3.2; else 0.

### K8 — Names and e-mails in free text (Part 2) · hard · 10 pts
- 26 planted name occurrences (truth `name_occ`), e.g. `Ayşe Yılmaz'a` (suffix), `MEHMET ÖZTÜRK'ten`,
  `IŞIL KILIÇ` and `İSMAİL ŞAHİN` (Python `lower()`/`upper()` break dotted/dotless i), surname-first
  `Sn. KAYA MEHMET ALİ`, two-token first name `Elif Naz Demir`, `Sigorta primi - Sn. İBRAHİM ÇELİK`,
  `HATİCE ARSLAN TEKSTİL'e`, third parties who are not customers (`Fatma Demir'in` spouse,
  `İSMAİL ŞAHİN` proxy, `Barış Aksoy` signatory, `Sevim Demir` mother, `Özge Ünal'a` landlord ×2,
  `AHMET ÇAKIR` payee, `Mustafa Kurt` owner), and the person names inside the 4 SAHIS titles
  (`Hatice Arslan Tekstil`, `Mustafa Kurt Oto Yedek Parça`, `Zeynep Aydın Kırtasiye`, `Recep Polat Nakliyat`).
- E-mails in text: `ali.kaya [at] example.com`, `HATICE.ARSLAN@EXAMPLE.COM`, `GULSEN.CELIK @ EXAMPLE.TEST`,
  `ayse.yilmaz@example.com`, and one `…(at)example.test`.
- Acceptance (automatic): a name occurrence is residual if its phrase is still in the same masked cell
  after Turkish-aware folding (İ→i, I→ı, lower, diacritics stripped, whitespace collapsed; so de-accented
  copies also count). E-mails: every original address searched in every masked text cell after
  normalising `[at]`, `(at)`, ` at `, spaces around `@`. Residual (names + e-mails) 0 → 10; ≤2 → 7;
  ≤5 → 4; else 0.

### K9 — Joins and determinism (Part 2) · medium · 8 pts
- What: row-aligned check that every islem row still points (sube_kodu, hesap_no) to the same hesap row,
  every hesap row to the same musteri row, and every internal transfer's karsi_iban (78 rows; many written
  with spaces or in lower case, so exact-string dictionaries miss them) equals the masked IBAN of the same
  account. Composite keys must stay unique — the three hesap_no values shared by two branches must remain
  two accounts (see T1).
- Determinism: the grader runs the agent's masker twice in fresh processes (PYTHONHASHSEED unset) with
  `MASKE_ANAHTARI=pusula-uat-2026`; `hash()`/unseeded `random`/set ordering make outputs differ.
- Acceptance: joins 5 pts if all three join fractions are 100 % (else 5 × 0.8 × mean); 0 if keys were not
  pseudonymised at all; capped at 2.5 if pseudonyms collide. Determinism: two runs byte-identical → 2,
  identical to delivered `cikti/maskeli` → 1; not credited when nothing was masked (K6 = 0), so a
  copy-through script earns nothing. With `--no-exec` judge determinism by hand (max 3).

### K10 — IBAN validity and cross-format consistency (Part 2) · hard · 10 pts
- IBAN part (4 pts): every masked hesap.iban = TR+kk+00990+0+sube+0000+masked hesap_no with valid
  check digits; every masked karsi_iban valid with the original bank code. 100 % → 4, ≥95 % → 2; 0 if
  IBANs were left unchanged.
- Consistency part (6 pts × passed/18), each check also requires the original value to be gone:
  CN1–CN2 TCKN in notes (spaced / dotted) = masked column TCKN of that customer; CN3–CN7 phones in other
  formats (notes and FAST "kolay adres" descriptions, including another customer's phone) = masked column
  phone; CN8–CN9 IBANs in text = masked hesap.iban of that account; CN10 IBAN in the "HAVALE: AHMET ÇAKIR"
  text = masked karsi_iban of the same row; CN11 an internal IBAN of a closed account not present in
  hesap.csv (`0208`/`19999999`, written once compact, once lower-case spaced) masked identically, valid,
  bank 00990; CN12 the landlord's external IBAN used in 6 rent rows with mixed formats masked identically,
  valid, bank 00993; CN13–CN14 customer numbers quoted in notes = masked musteri_no; CN15–CN18 e-mails in
  text (plain, upper case, spaced, `[at]`) = masked column e-mail.

### K11 — Date shift (Part 2) · medium · 8 pts
- What: kayit_tarihi, kurulus_tarihi, acilis_tarihi (`YYYY-AA-GG`) and islem_tarihi (`GG.AA.YYYY SS:DD:ss`)
  shifted by one constant offset in −365…−30 days; formats and time of day unchanged; dogum_tarihi is
  generalised, not shifted. Per-customer offsets break the two legs of internal transfers.
- Acceptance: all deltas identical → 4 (≥95 % → 2); offset in range → 1; all masked dates parse in the
  original column format → 2 (≤5 % failures → 1); times unchanged → 1. Unshifted dates → 0.

### K12 — k-anonymity (Part 2) · hard · 10 pts
- What: in the source every one of the 92 individuals is unique on (dogum_tarihi, il, ilce, cinsiyet).
  Allowed: dogum_tarihi → `YYYY` or a ≤10-year `YYYY-YYYY` range, ilce → `*`, suppression of all four
  fields with `*` for at most 5 % (= 4) individuals; il and cinsiyet unchanged; generalisation must contain
  the true year. The data is built so that decade + il + cinsiyet with ilce `*` gives classes ≥5 except
  three outliers that must be suppressed: M227546 (1931, Şanlıurfa/Halfeti, E), M596042 (1955,
  Bayburt/Merkez, K), M748890 (1999, İzmir/Buca, E). Year-level or 5-year generalisation, or keeping ilce,
  cannot reach k = 5 within the suppression cap.
- Acceptance: min class size ≥5, suppressed ≤4 and 0 untruthful/forbidden values → 10; min class ≥3,
  suppressed ≤8, 0 untruthful values → 4; else 0.

## Traps (correct situations a careless tester reports or "fixes")

| Trap | Situation in the extract | Correct behaviour | Penalty |
|---|---|---|---|
| T1 | hesap_no `18218855` in branches 0101 and 0102, `12408957` in 0207 and 0208, `14922516` in 0207 and 0102 | Legal under the composite key (policy §2, rules §2.2). Keep them as distinct accounts. | −4 (manual) if rapor.md calls them duplicates / an error / to be de-duplicated; merging them is also caught by K9 |
| T2 | 11 KMH accounts with negative bakiye inside their limit (e.g. 0102-10118097 −20000.00 with limit 25000.00, 0315-19938657 −9997.60 with limit 10000.00) | Legal overdraft (İK-10). | −4 (manual) if reported as a data error / rule violation |
| T3 | M408250 Elif Naz Demir born 29.02.2008, registered and account 0101-14075840 opened 2026-03-01; M820079 Emre Yıldız born 29.02.2004, registered and account 0207-14940076 opened 2022-03-01 | Exactly the 18th birthday under İK-05. | −4 (manual) if reported as underage / opened before 18 / rule violation |
| T4 | Non-personal data that looks personal: AS/LTD titles and VKNs (`Demir Çelik Sanayi A.Ş.`, `Kaya Turizm ve Seyahat A.Ş.` contain customer surnames), `Kuzey Lojistik Ltd. Şti.`, `Yıldız Sitesi Yönetimi`, bank call centre `Pusula Müşteri Hizmetleri 0850 724 00 00`, `Fatura no 40001234567` (11 digits, fails the TCKN checksum), amount `1.250,00 TL`, `HVL-…` references, preserved columns (musteri_tipi, sirket_turu, AS/LTD il, sube_kodu, hesap_turu, doviz, kmh_limiti, bakiye, islem_id, islem_tipi, tutar) | Preserve (policy §5, §8). | Automatic: −1 per finding group (each lost fragment, HVL loss, changed preserved columns per file), max −6 |

Manual judgement for T1–T3: penalise only an explicit claim that the situation is wrong (error,
inconsistency, violation, duplicate to clean). Neutral mentions ("composite key: the same hesap_no
exists in two branches, kept as is") are not penalised. The grader prints candidate lines under
`report_trap_hints`; read them in context.

### Other unfounded claims (manual)
−2 each, max −6, for claims about the source that are false: e.g. bakiye ≠ Σ tutar (all 205 balances
are exact), running balance below the allowed floor (never), invalid TCKN/VKN/IBAN checksums in the
source (all valid), a transfer whose two legs differ, a transaction before the account opening.

Neutral (no credit, no penalty): the closed-account IBAN TR06 0099 0002 0800 0019 9999 99 is not in
hesap.csv (true; realistic); source phone formats are inconsistent (true); the extract does not follow
the Part 1 import format or its 25 % KURUMSAL share (true but Part 1 rules apply to generated data).

## Verification log (executed 2026-10-01)

- `testdata2_build.py` run twice: identical MD5s (musteri 230dcdad…, hesap 4835794a…, islem efcf7a75…).
- Source extract converted to the Part 1 format and checked with the grader's Part 1 rules: zero
  violations of TCKN/VKN, fields, dates (incl. 29 Feb), composite PK, FK, IBAN, bakiye = Σ tutar and
  running balance; only expected non-rule differences (production phone formats, 24.6 % corporates,
  9 % internal transfers, closed-account IBAN). T1 (3 shared hesap_no), T2 (11 KMH negatives within
  limit) and T3 (2 Feb-29 customers opened on 1 March at exactly 18) confirmed in the files.
- All 26 name occurrences and all 18 consistency targets confirmed present in the source cells.
- Reference solution (`testdata2_ref/uret.py` + `maskele.py`): 100/100, determinism 3/3, residual PII 0,
  no T4 findings; Part 1 boundaries SD1 7, SD2 3, SD3 4, SD5 25, SD6 6, SD7 4.
- Identity copy of the source as "masked" output: 0/60 on Part 2 (no free points); a Node.js
  copy-through `maskele.js` is executed correctly by the grader and also scores 0.
- Naive masker (column hashing, `\b\d{11}\b`, simple phone regex, exact-case name replacement, year-only
  birth dates, `random.seed(hash(key))`): Part 2 14.25/60, residual PII 32, determinism 0, T4 finding
  "Fatura no 40001234567" lost.
- Mutated Part 1 data (Feb-28 handling for a 29-Feb customer, balance +0.01, invalid VKN, one islem
  moved to another branch): grader flagged M_DATES/H_DATES, H_BAL/H_RUN, M_VKN, I_FK; K3 = 0.
