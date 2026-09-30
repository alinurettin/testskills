# KEY: trial-testdata (TEST DATA PREPARATION and MASKING)

CONFIDENTIAL: grader-only. Never place this file, or anything under `evals/keys/`, where an agent under test can read it.

- Trial folder: `C:\projeler\TestSkills\evals\trial-testdata\` (`TASK.md`, `RUN.md`, `girdi/`).
- Grader: `C:\projeler\TestSkills\evals\keys\testdata_grade.py` (Python 3 stdlib).
- All data is synthetic. The company is "Yelkovan Ödeme Hizmetleri A.Ş."; the domains are `example.test` / `example.com`; the bank codes 00991–00993 are fictional.

## 1. What the agent must do

The agent does two jobs, both described in Turkish in `TASK.md`:

1. **Generation.** Following `girdi/sema.md`, produce `musteriler.csv` (exactly 200 rows, 20–30% KURUMSAL), `hesaplar.csv` (1–3 accounts per customer) and `islemler.csv` (at least 1000 rows). The data must include:
   - valid TCKN for BIREYSEL customers and valid VKN for KURUMSAL customers;
   - valid TR IBANs;
   - phone numbers as `+905XXXXXXXXX`;
   - e-mail addresses on `@example.com`;
   - dates as `dd.MM.yyyy` and amounts with a decimal comma;
   - referential integrity between the three files;
   - the six business rules in §4 of the schema;
   - at least 15% `senaryo=SINIR` rows per table, each carrying a real boundary value (§5 of the schema).

   The generator must be seeded, so every run gives the same output.
2. **Masking.** Mask `girdi/canli_kesit/musteri_ozet.csv` (UTF-8 with BOM, 40 rows) and `destek_kayitlari.csv` (**cp1254**, 60 records). The masking must be deterministic, keep the join on `musteri_no` working, keep formats valid, and keep the same columns and row order. It must leave `musteri_tipi, cinsiyet, il, segment, kayit_no, tarih, kanal, konu, islem_tutari, durum` unchanged, keep age-band and province distributions intact, and keep free text meaningful.

Deliverable: `teslim/{uret.*, maskele.*, uretim/*.csv, maskeleme/*.csv, RAPOR.md}`.

A strong agent should finish in about 15–25 minutes.

## 2. Planted items (K1–K10)

Row numbers are 1-based **data** rows, with the header excluded. Credit is **objective**: it depends on the delivered files, computed by the grader. Whether RAPOR.md mentions an item is recorded as *discovery* (see §5) and is not scored.

| ID | Planted defect or gap | Severity | Difficulty | Points |
|---|---|---|---|---|
| K1 | Phone numbers in free-text `temsilci_notu`, in 7 different formats | High | Medium | 2 |
| K2 | E-mail addresses in `temsilci_notu`, including uppercase and third-party | High | Easy–Med | 2 |
| K3 | TCKNs in `temsilci_notu`, 2 of them third-party, 1 glued to the "TC" prefix | Critical | Hard | 3 |
| K4 | Misleading header: `eski_musteri_kodu` holds the TCKN for 15 legacy customers | Critical | Hard | 3 |
| K5 | IBANs inside `aciklama` (spaced, compact, lowercase) | High | Medium | 2 |
| K6 | Quasi-identifier pair `dogum_tarihi` + `posta_kodu` (unique for every person) | High | Hard | 3 |
| K7 | File-format traps: destek file is cp1254 (not UTF-8), with quoted fields containing `;`, a line break and `""` | Medium | Medium | 3 |
| K8 | Dirty join keys in `destek_kayitlari.musteri_no` (lowercase, leading space, trailing space) | High | Hard | 3 |
| K9 | Generation: business rules and date chain from schema §4 (easy to skim past) | High | Hard | 3 |
| K10 | Generation: identifier validity by customer type (TCKN / VKN / IBAN checksums) | Medium | Medium | 2 |

### K1: phones in `destek_kayitlari.temsilci_notu`

- **Values** (row: text → national form):
  - 1 `0551 960 07 12` → 5519600712 (the customer MS-100411's own mobile, in a different format from the column)
  - 6 `+90 (505) 318 44 12`
  - 8 `5427781203` (bare, the spouse's number)
  - 10 `0 555 902 11 36'dan` (Turkish suffix attached)
  - 17 `0 (216) 455 70 81` (work landline)
  - 15 `0505-771-20-93` (hyphens, inside a quoted field that contains `;`)
  - 20 `+905366102284` (E.164)
- **Why it matters.** These are direct contact identifiers of customers and their relatives. Only row 1 can also be found through the `cep_telefonu` column. The others exist only in free text.
- **Acceptance.** None of the 7 national 10-digit numbers remains as a digit substring of any cell of the masked destek file. Partial masking (for example keeping the last 2 digits) counts as removed. Score: 7/7 → 2; 4–6 → 1; fewer → 0.

### K2: e-mails in `temsilci_notu`

- **Values:**
  - row 2 `SEBNEM.OGUZHANOGLU@POSTA.EXAMPLE.TEST` (the customer's own address, in uppercase)
  - row 4 `hasan.yurekli@karacamtekstil.example.test` (third-party person, in parentheses)
  - row 18 `tunc.egilmez.1979@example.test` (a private address that differs from the column)
  - row 19 `ozlem.tas1987@example.test` (the daughter's address)
- **Why it matters.** These are direct identifiers. Changing only the domain still leaks the local part, which is the person's name.
- **Acceptance.** Neither the full address nor its local part occurs case-insensitively anywhere in the masked destek file. Score: 4/4 → 2; 3 → 1; fewer → 0.
- The company address `destek@yelkovan.example.test` in row 25 is **not** counted; see T4.

### K3: TCKNs in `temsilci_notu`

- **Values:**
  - C1: row 9 `TCKN 27075526846`, the customer's own number, which also appears in `kimlik_no` and `eski_musteri_kodu`.
  - C2: row 12 `TCKN: 27060945126`, belonging to the attorney "Av. Tuğrul Başaran". It is **not** in `kimlik_no`.
  - C3: row 16 `(TC63202010420)`, belonging to the mother "Saadet Kılınçarslan". It is not in `kimlik_no` and is glued to "TC", so `\b\d{11}\b` misses it.
- **Why it matters.** A national ID is the most sensitive identifier here. The third-party numbers can only be found by scanning free text with checksum validation, not by value lookup from the ID column.
- **Acceptance.** The 11 digits do not remain as a substring of the digits of any masked destek cell. Score: 1 point per TCKN removed.

### K4: misleading header `musteri_ozet.eski_musteri_kodu`

- **Values.** Rows 7, 9, 11, 13, 15, 18, 19, 23, 25, 27, 30, 32, 34, 36 and 39 are the BIREYSEL customers registered before 2018. For them this column holds the **customer's TCKN**, because the legacy core used the TCKN as the customer code. The other rows hold `EMK-nnnnnn` codes or are empty. The first 5 rows are all `EMK-` codes, so a quick `head` does not reveal the pattern.
- **Why it matters.** Masking only the columns whose names look sensitive leaves 15 national IDs in clear text.
- **Acceptance.** None of the 15 original TCKNs remains in the masked `eski_musteri_kodu` column. Score: 0 left → 3; 1–3 left → 1; more → 0. The grader also reports how many remain anywhere in the output.

### K5: IBANs inside `destek_kayitlari.aciklama`

- **Values:**
  - row 5 `TR75 0099 2000 0012 3456 7890 12` (spaced)
  - row 13 `TR850099300000098765432101` (compact)
  - row 22 `tr17 0099 1000 0045 6712 3398 22` (lowercase and spaced)
- **Why it matters.** An IBAN is a financial identifier linkable to a person. It sits in a description column that looks harmless.
- **Acceptance.** For each IBAN, neither its 24 digits nor its 16-digit account part remain in the digits of any masked destek cell. Score: 3/3 → 2; 2/3 → 1; fewer → 0.

### K6: quasi-identifier `dogum_tarihi` + `posta_kodu`

- **Fact.** The pair (full birth date, 5-digit postcode) is unique for every one of the 35 BIREYSEL rows. Together with `cinsiyet` and `il`, which must be preserved, it re-identifies people, which is the classic Sweeney result. The task requires keeping the 10-year age band and the province distribution.
- **Acceptance.** Evaluated on the 35 BIREYSEL rows:
  - Any row still holding the exact original (dob, postcode) pair → **0**.
  - Pair broken but the age band is lost in more than 10% of rows (for example random dates or blanked dates) → **1**.
  - Dob kept exactly while the postcode is generalised → **1.5**.
  - Dob shifted or perturbed (none left exact) while the postcode is kept → **2**. The linkage risk remains, because a near-date plus the exact postcode still singles people out.
  - Dob generalised (year only or age band, or a constant day-month such as `01.07.YYYY`), **or** dob perturbed together with a generalised postcode (for example `34000` or `347**`), with the age band preserved in at least 90% of rows → **3**.
- The grader also prints the minimum k of the output (dob, postcode) groups, for information only.

### K7: file format

- **Facts.**
  - `destek_kayitlari.csv` is Windows-1254 (cp1254) with CRLF. Reading it as UTF-8 either raises an error (Python) or silently produces U+FFFD (Node). Reading it as latin-1/cp1252 produces `ý þ ð Ý Þ`.
  - `musteri_ozet.csv` is UTF-8 with BOM. The two input files therefore use different encodings.
  - Record 15 contains `;` inside a quoted note. Record 28 contains a line break inside a quoted note. Record 29 contains doubled quotes `""acil""`.
- **Acceptance.** Two parts:
  - **(a) 1.5 points.** The outputs contain zero mojibake markers (`\ufffd Ã Ä Å Ý Þ ð ý þ`), and `kanal/konu/durum` equal the originals for at least 90% of records matched by `kayit_no`. Full 1.5 if both outputs are UTF-8 as requested; 1.0 if the text is correct but the output is cp1254.
  - **(b) 1.5 points.** The output has exactly 60 records of 9 fields each, `kayit_no/tarih/islem_tutari` are aligned on every row, and records 15, 28 and 29 and the records following them are intact.

### K8: dirty join keys

- **Values** in `destek_kayitlari.musteri_no`:
  - row 14 `ms-100606` (lowercase)
  - row 21 `␠MS-100683` (leading space)
  - row 23 `MS-100779␠` (trailing space)
- Each of these customers also has a clean row: rows 31, 36 and 41.
- In the source the exact join fails for these 3 rows. The join works after `strip().upper()`.
- **Why it matters.** A naive deterministic pseudonymisation, such as an HMAC of the raw cell value, gives these rows keys that match nobody. The join then silently breaks, or the same person gets two pseudonyms.
- **Acceptance.** `musteri_no` is pseudonymised, meaning none of the 40 original keys remain. The normalised masked key of each dirty row must also equal the masked key of the correct customer in the masked `musteri_ozet`. Score: 3/3 → 3; 1–2 → 1; 0, or keys not pseudonymised → 0.

### K9: generation business rules

These rules are in schema §4, plus the date and range rules in the tables. The grader checks three groups, each worth 1 point with zero violations tolerated:

- **A. Date chain:**
  - `kayit_tarihi` lies in 01.01.2015–30.09.2026;
  - `acilis_tarihi` ≥ `kayit_tarihi`, and `kapanis_tarihi` ≥ `acilis_tarihi`;
  - no date after 30.09.2026;
  - `islem_tarihi` ≥ `acilis_tarihi`, and no transaction after `kapanis_tarihi` on a KAPALI account;
  - a BIREYSEL customer is at least 18 years old at `kayit_tarihi`.

  The last rule interacts with the SINIR case "exactly 18 on 30.09.2008": such a customer can only have `kayit_tarihi = 30.09.2026`. The grader treats a 29.02 birthday leniently.
- **B. Account rules:**
  - `kapanis_tarihi` is filled if and only if the account is KAPALI;
  - a KAPALI account has `bakiye = 0,00`;
  - `bakiye` lies in 0–5000000;
  - `iban[4:9]` equals `banka_kodu`.
- **C. Transaction rules:**
  - an IADE amount is negative and lies in −1000000…−0,01; other types lie in 0,01…1000000;
  - a FAST amount is at most 100000;
  - `karsi_iban` is present for HAVALE, EFT and FAST and differs from the account's own IBAN;
  - `karsi_iban` is empty for KART and IADE.

**Why it matters.** Test data that violates the module's own validation layer is rejected at load time, or it hides bugs.

### K10: identifier validity

- **Checks:**
  - a BIREYSEL row has a valid TCKN and an empty `vkn`; a KURUMSAL row has a valid 10-digit VKN and an empty `tckn`;
  - every `hesaplar.iban` is a valid TR IBAN: 26 characters, reserve digit `0`, mod-97 = 1;
  - every non-empty `karsi_iban` is valid;
  - TCKN, VKN and IBAN values are unique.
- **Common failures.** Random 11-digit numbers, a TCKN given to companies, or `TR` followed by 24 random digits.
- **Score.** 100% valid → 2; at least 95% → 1; otherwise 0.
- **Algorithms used by the grader:**
  - **TCKN:** d10 = ((d1+d3+d5+d7+d9)·7 − (d2+d4+d6+d8)) mod 10, and d11 = (d1+…+d10) mod 10, with a first digit other than 0.
  - **VKN:** for i = 0..8, tmp = (d_i + 9 − i) mod 10 and v = tmp·2^(9−i) mod 9; if tmp ≠ 0 and v = 0 then v = 9. The check digit is (10 − Σv mod 10) mod 10. For example, 1111111114 is valid.

## 3. Traps (T1–T4): correct data that careless testers flag

Each **confirmed** false-positive claim in RAPOR.md (or in the agent's final message) costs **−2 points**. The grader's "Tuzak adayları" section lists candidate lines, and a human confirms them. Masking a trap value is never penalised.

| ID | What it is | Why it is correct | False-positive claim (penalise) |
|---|---|---|---|
| T1 | Leap-day dates: `dogum_tarihi` 29.02.2000 (ozet row 10, MS-100497) and 29.02.1996 (row 20, MS-100617); support `tarih` 29.02.2024 (destek row 7, DK-2024-001149) | 2000 is a leap year (divisible by 400); 1996 and 2024 are leap years | "invalid / impossible / suspicious birth date or record date" |
| T2 | `kimlik_no` holds a 10-digit value for the 5 KURUMSAL rows (4, 12, 21, 29, 37) | They are valid VKNs; the column holds TCKN or VKN depending on `musteri_tipi` | "invalid / short / broken TCKN in kimlik_no", "data quality error: 10 digits" |
| T3 | `kimlik_no = 99086354688` (row 40, Katarina Novak) | A valid foreign-resident ID (YKN): it starts with 99 and passes the TCKN checksum. It is still PII and must be masked. | "invalid / fake / test TCKN", or dropping or leaving it unmasked because it is "not a real TCKN" (leaving it unmasked is also caught by M1 and the residual count) |
| T4 | Non-personal look-alikes in notes: `Kargo takip no 20240227114` (row 7), `Dekont no 71004583216` (row 27), company hotline `0850 455 12 12` and `destek@yelkovan.example.test` (row 25) | The two 11-digit numbers **fail** the TCKN checksum; the hotline and support address are public corporate contacts | Reporting them as found customer TCKNs, phones or e-mails, or inflating counts (for example "5 TCKN in notes" or "8 phones") |

Other false positives, such as any factually wrong claim about the source, also cost −2 points each. Examples:

- "`destek_kayitlari.csv` is corrupted or has broken characters." The file is valid cp1254. Saying it is cp1254 or not UTF-8 is correct and counts as K7 discovery.
- "TCKN checksums in `kimlik_no` are wrong." All 35 are valid.

Pointing out that 3 destek rows do not join exactly is **correct**, and counts as K8 discovery.

## 4. Objective checks (grader)

| ID | Check | Points | Rule |
|---|---|---|---|
| G1 | Structure and counts | 2 | 6 sub-checks: headers exact; 200 customers; KURUMSAL 20–30%; at least 1000 transactions; 1–3 accounts per customer; enum values valid. All 6 → 2; at least 4 → 1 |
| G2 | Formats | 2 | Strict `dd.MM.yyyy` real dates, amounts `^-?\d+,\d{2}$`, phone `^\+905\d{9}$`, province in the 81-province list, name lengths, `aciklama` ≤ 140 characters, age 18–100, UTF-8, and at least 30% of BIREYSEL names containing a Turkish letter. 0 bad cells → 2; at most 1% → 1 |
| G3 | Referential integrity | 2 | Primary keys unique and in format; foreign keys hesaplar→musteriler and islemler→hesaplar all resolve. Perfect → 2; foreign-key breakage ≤ 1% → 1 |
| G4 | Boundary rows | 3 | 1 point per table where rows labelled SINIR **and** truly carrying a §5 boundary make up at least 15% of the table |
| G5 | E-mail domain | 1 | Every `eposta` is lowercase `@example.com` and unique, and no other domain appears anywhere in the generated files |
| G6 | Generator determinism | 1 | A rerun reproduces all 3 files (byte-identical, or identical after CSV parsing) |
| M1 | Direct PII columns | 3 | `musteri_no` changed on all 40 rows; `ad_soyad`, `kimlik_no`, `cep_telefonu` and `eposta` changed on the 35 BIREYSEL rows. 100% → 3; at least 95% → 2; at least 80% → 1 |
| M2 | Format validity after masking | 2 | Masked TCKN valid (BIREYSEL, including the YKN row); masked VKN valid (KURUMSAL); phone `^\+90 5\d{2} \d{3} \d{2} \d{2}$`; BIREYSEL e-mail `@example.com`. At least 98% → 2; at least 80% → 1 |
| M3 | Utility | 2 | (a) 1 point: same headers, row counts and order, and the preserved columns are unchanged. (b) 1 point: at least 60% of the non-name words in `aciklama`/`temsilci_notu` survive, and no originally non-empty cell is emptied |
| M4 | Masking determinism | 3 | A rerun (`--rerun` or `--run2`) reproduces both files. Not evaluated → 0 (flagged `NOT_EVALUATED`) |
| M5 | Join on clean rows | 2 | All 57 clean destek rows point to the correct masked customer and masked keys are unique → 2; at least 90% → 1 |
| M6 | Person names in free text | 2 | 9 planted names: 5 third parties (Hasan Yürekli, Nurten Akbulut, Tuğrul Başaran, Saadet Kılınçarslan, Özlem Taş) and 4 customers named in notes (rows 24, 32, 35, 37). Matching covers the full name, tolerating case, ASCII folding and mojibake, and the surname alone if it has at least 5 letters. None left → 2; at most 3 → 1 |

The grader also prints a **residual PII count**: every original value still present anywhere in the masked output, by category. The categories are TCKN/YKN, phones, e-mails, IBANs, `musteri_no`, names and (dob|postcode) pairs; corporate VKNs are listed for information only. A good run shows `toplam=0`.

## 5. Scoring rubric

- **K score:** K1–K10, max **26**.
- **Objective score:** G1–G6 + M1–M6, max **25**.
- **Total:** at most **51**, minus **2 per confirmed false positive** (`--fp N`), with a floor of 0. Report the percentage of 51.
- **Discovery flags** are not scored but should be recorded per run for analysis. Mark K4, K6, K7 and K8 as *discovered* if RAPOR.md explicitly mentions:
  - K4: the TCKN inside `eski_musteri_kodu`;
  - K6: the quasi-identifier or re-identification risk of birth date + postcode;
  - K7: the cp1254/Windows-1254 encoding, or the quoted multi-line fields;
  - K8: the dirty or unnormalised keys.

  A handled-but-undiscovered item means the handling was accidental, for example "mask every 11-digit number".
- **Comparing arms:** run at least 3 times per arm (with-skill and no-skill), then compare median K score, median total and residual-PII totals. A difference of 4 or more points in the K-score median is meaningful at this size.
- **Rough bands:** at least 45 excellent; 35–44 good (typical misses: K4, K6, K8); 20–34 shallow; under 20 naive.

## 6. Running the grader

```text
python testdata_grade.py --check-inputs                       # every planted item present -> INPUT CHECK: PASS
python testdata_grade.py --teslim <work>\teslim --rerun --json out.json
python testdata_grade.py --teslim <work>\teslim --run2 <work>\run2 --fp 1
```

`--rerun` runs the agent's code: the Python scripts with the grader's interpreter and the `.js` scripts with `node`. It clears `MASKELEME_ANAHTARI`, uses temporary folders and a pristine copy of the inputs, and has a 300 s timeout per script. If the delivered file names differ, the grader falls back to the single CSV whose name contains `ozet` / `destek` and notes it.

## 7. Verification performed while building the trial (2026-09-30)

- `--check-inputs`: **PASS**. All 55 checks confirmed:
  - every K1–K5 value is at its row;
  - the C2 and C3 TCKNs are absent from `kimlik_no`, and C3 is glued to "TC";
  - all 15 legacy rows carry the TCKN, and the first 5 rows are EMK codes;
  - all 35 (dob, postcode) pairs are unique;
  - the 3 dirty keys do not join exactly but do join after normalisation;
  - the destek file is not valid UTF-8, and its 60 records each have 9 fields under a proper CSV parser;
  - the T4 11-digit numbers fail the checksum, the YKN is valid, the 5 VKNs are valid, and the leap dates are present.
- Three throwaway reference solutions were written, run and graded with `--rerun`. They are not part of the trial.

| Reference | Result | Notes |
|---|---|---|
| **Good** (Python) | **51/51** | Residual PII 0; generator 200/378/1200 rows; SINIR 23.5% / 19.8% / 20.0% verified; both reruns byte-identical |
| **Medium** (Python: correct encoding and CSV, deterministic, but shallow regexes) | **36/51** (K 13/26) | Every hard item reproduced as a failure: K1 1/2 (missed `+90 (505)…`, landline, hyphenated); K3 2/3 (missed glued `TC6320…`); K4 0 (15/15 TCKN left); K5 0 (3 IBANs left); K6 0 (35/35 pairs kept); K8 0 (dirty rows got foreign pseudonyms); M6 0 (5 third-party names left). The trap scanner flagged its planted false-positive lines for T1 (29.02.2000 "geçersiz") and T2 (10-digit "geçersiz TCKN") |
| **Naive** (Node: `utf8` read, `split(';')`, `Math.random`, random salt) | **10/51** (K 0/26) | K7 0 (767 mojibake chars, one record mis-split); K9 0 (for example 150 customers under 18 at registration, 350 IBAN/bank-code mismatches); K10 8.8% valid; G2 fails on dot decimals; M4/G6 0 (reruns differ); residual PII 77 |

The masking half of the grader was also exercised on hand-made output variants:

| Variant | Result |
|---|---|
| cp1254 output with correct text | K7 2.5/3 |
| dob shifted +11 days with postcode kept | K6 2/3 |
| notes replaced by a constant | M3 1/2 (K7 not double-penalised) |
| no output folders | all 0, no crash |
| renamed files | fallback with a note |
| correct encoding but naive line/`;` split | K7 1.5/3 (61 records, misaligned) |

### Grader caveats

- The surname-only match used by M6 applies to surnames of at least 5 letters, such as Akbulut, Başaran, Yürekli and Karakoçan. It can in principle fire if the agent's fake-name pool happens to contain one of those surnames in the same cell. Check the M6 detail line if M6 loses points.
- Row-based checks (K6, K8, M3, M5) assume the required row order. If an agent reorders rows, those items score low. That is a requirement violation, but mention it in the review.
- M4 and G6 need `--rerun` or `--run2`. Without either they are reported as `NOT_EVALUATED` and scored 0; state that when reporting.
