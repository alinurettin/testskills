# KEY: trial-review (manual test-suite review of an .xlsx)

**CONFIDENTIAL: grader only.** Never put this file, `trial-review/RUN.md`, or `trial-review/tools/` in an agent's working directory.

- Trial folder: `C:\projeler\TestSkills\evals\trial-review\`
- The agent receives `TASK.md`, `inputs/FAST_Transfer_Test_Cases.xlsx` and `inputs/US-214_FAST_Transfer.md`.
- Deliverable: `inceleme-raporu.md`. A corrected workbook is optional.
- Input hashes (SHA-256):
  - `FAST_Transfer_Test_Cases.xlsx` = `db575e8812c705335c0d18a0653197ca4f7f34e49488cfd01973423eab0a0328`
  - `US-214_FAST_Transfer.md` = `03fd15406a17bb5473ca7722950a76a4b31d7455e62f1ed4ca74d1e8e67047ee`

## 1. Scenario

- Nehir Bank A.Ş. (fictional) adds "IBAN'a FAST Transferi" to its Nehir Mobil app. The user story is US-214, with acceptance criteria AC-1 to AC-10.
- The team's workbook has two sheets:
  - **"Test Cases"**: 40 cases, FT-001 to FT-040. Columns: Test ID, Başlık, Ön Koşul, Adımlar, Beklenen Sonuç, Öncelik, Gereksinim. Step cells span several lines.
  - **"Bilgi"**: document info, a common precondition (user `ft.test01`, balance 200.000,00 TL, no transfers yet that day) and the priority definitions:
    - Kritik = para kaybı / güvenlik / dolandırıcılık önleme / yasal limit
    - Yüksek = ana akış
    - Orta = alan doğrulama / mesaj / yan akış
    - Düşük = kozmetik / bilgilendirme
- There are **10 planted defects (K1 to K10)** and **4 traps (T1 to T4)**.
- Everything else is written to be correct. Section 4 lists known neutral and false-positive findings.

AC coverage, from the Gereksinim column:

| AC | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | "AC-11" |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Tests | 8 | 6 | 6 | 3 | 4 | 9 | 2 | **0** | 7 | 3 | 1 (does not exist) |

Suite map. Every row not listed as K or T is clean.

| Test | Role | Test | Role |
|---|---|---|---|
| FT-001–004 | clean | FT-022 | **K10** |
| FT-005 | **T1** | FT-023 | **T3** |
| FT-006–010 | clean | FT-024, 025 | clean |
| FT-011 | **K1b** (pair with 036) | FT-026 | **K1a** (pair with 038) |
| FT-012 | **K9** | FT-027–030 | clean |
| FT-013 | **T4** | FT-031 | **K4** |
| FT-014, 015 | clean | FT-032, 033 | **K3** |
| FT-016 | **K2** | FT-034 | **K2** |
| FT-017, 018 | **T2** (pair) | FT-035, 037 | clean |
| FT-019, 020 | clean | FT-036 | **K1b** |
| FT-021 | **K5** | FT-038 | **K1a** |
| | | FT-039, 040 | **K6** |
| (no test) | **K7** = AC-8 | (AC-3 amounts) | **K8** |

## 2. Planted defects

The "Sev." column is the severity of the defect as a quality problem in the suite. Difficulty is how hard it is to find.

| ID | Where | Sev. | Difficulty | Points |
|---|---|---|---|---|
| K1 | FT-026 = FT-038; FT-011 ≈ FT-036 | Low | easy / medium | 2 (1 + 1) |
| K2 | FT-016, FT-034 | Medium | easy | 1 (0.5 + 0.5) |
| K3 | FT-032, FT-033 | Medium | easy | 1 (0.5 + 0.5) |
| K4 | FT-031 | Medium | easy–medium | 2 |
| K5 | FT-021 | High | medium | 2 |
| K6 | FT-039, FT-040 | Low | medium | 2 (1 + 1) |
| K7 | AC-8 (no test) | High | hard | 3 |
| K8 | AC-3 amount limits | High | medium–hard | 3 |
| K9 | FT-012 | High | easy | 2 |
| K10 | FT-022 | High | hard | 3 |
| | | | **Total** | **21** |

### K1: Duplicate test cases (exact and near)
- **What:**
  - (a) **FT-038 is an exact copy of FT-026.** Title, precondition, steps, expected result, priority and requirement are all identical. Only the ID differs.
  - (b) **FT-036 is a reworded duplicate of FT-011.** Both cover AC-4 "Yetersiz bakiye" with the same data: balance 1.000, amount 1.500, the same IBAN TR48…2844 06 and the same result. The differences are only the wording, the less precise "1.000 TL / 1.500 TL" format, and the priority (Orta vs Yüksek).
- **Why it matters:** Duplicates inflate the size and execution cost of the suite. They drift apart when one copy is maintained and the other is not, and they distort coverage metrics.
- **Acceptance:**
  - 1 pt: the report says FT-026 and FT-038 are duplicates or identical, naming both IDs.
  - 1 pt: the report says FT-011 and FT-036 test the same behaviour or data and one should be removed or merged, naming both IDs.
  - Calling them only "similar", without saying one is redundant, gets 0.5.

### K2: Missing expected result
- **What:** FT-016 ("Kalan günlük limit Limitlerim ekranında güncellenir") has an **empty** Beklenen Sonuç. FT-034 ("Alıcı adı yalnızca boşluklardan oluşamaz") has **"TBD"**.
- **Why it matters:** Without an oracle a tester cannot give a pass or fail verdict. For FT-034, AC-2 already defines the expected result: "Alıcı adı soyadı zorunludur." and a passive "Devam". For FT-016 it should be "kalan limit 120.000,00 TL".
- **Acceptance:** 0.5 pt for each test that is explicitly flagged as having no or a placeholder expected result. A proposed concrete expected result is needed for the fix part (see 5.2).

### K3: Vague steps or oracle
- **What:**
  - FT-032: steps "Ekranın çalıştığını kontrol et", expected "Ekran düzgün çalışmalı, hata olmamalı", precondition "Uygulama cihaza yüklü".
  - FT-033: steps "Alanlara hatalı değerler gir", expected "Uygun hata mesajları gösterilmeli". It gives no data and no message text.
- **Why it matters:** Nobody can check these results, different testers will run them differently, and they give false confidence in the AC-1, AC-2 and AC-3 coverage.
- **Acceptance:** 0.5 pt for each test flagged as vague, unmeasurable or lacking concrete data or an oracle. Also accepted: "no value, delete it or rewrite it with concrete values".

### K4: Several behaviours in one test
- **What:** FT-031 "Uçtan uca FAST transferi ve doğrulamalar" has 8 steps spanning AC-1, AC-2, AC-3, AC-6 and AC-9. It checks an invalid IBAN, an empty name, an over-limit amount, 2 wrong OTPs, a success, the receipt, the history and the balance. It has a single expected result: "Tüm adımlar başarılı olmalı."
- **Why it matters:** When one check fails, the rest are blocked, and the failure cannot be traced to one AC. It duplicates the atomic tests and has no oracle for each check.
- **Acceptance:**
  - 2 pt: the report flags FT-031 as mixing several behaviours or requirements and recommends splitting it (or dropping it in favour of the atomic tests).
  - 1 pt: the report flags only its vague single expected result.

### K5: Wrong priority on a critical security rule
- **What:** FT-021 "3 hatalı OTP girişinde işlem iptal edilir" (AC-6, a fraud and security control) has priority **Düşük**. By the team's own definitions on the "Bilgi" sheet, Düşük means cosmetic, and security rules are Kritik. The other OTP tests are Kritik.
- **Why it matters:** Low-priority cases are dropped first when regression time is short, so a brute-force protection could ship untested.
- **Acceptance:** 2 pt if the report names FT-021 and says its priority should be Kritik, or at least Yüksek. A generic remark such as "priorities are inconsistent" without FT-021 gets 0.

### K6: Tests not traceable to any acceptance criterion
- **What:**
  - FT-039 (home-page FAST campaign banner) references **"AC-11", which does not exist**. Campaigns and banners are also listed under Kapsam dışı.
  - FT-040 (USD account, SWIFT abroad) has an **empty Gereksinim**, and SWIFT and foreign-currency transfers are explicitly out of scope.
- **Why it matters:** These tests belong to other features. They distort coverage and pull execution effort away from US-214.
- **Acceptance:** 1 pt for each test flagged as untraceable, out of scope or pointing to a non-existent AC. The fix can be to move it to the right suite, or to remove it.

### K7: Acceptance criterion with no test (AC-8)
- **What:** AC-8 (duplicate-transaction warning: same IBAN and same amount within 10 minutes, a warning dialog, Vazgeç / Devam) is **not referenced by any test**, and no test exercises it.
- **Why it matters:** This is a fraud and mistake prevention control with **zero coverage**. It is only found by mapping every AC to the tests.
- **Acceptance:** 3 pt if the report states that AC-8, or the "mükerrer işlem uyarısı" behaviour, has no test. A general remark such as "some ACs may be under-covered" that does not name AC-8 gets 0. Concrete proposed tests are rewarded under Q1.

### K8: Missing boundary and negative tests for the amount limits (AC-3)
- **What:** AC-3 sets 1,00 TL ≤ amount ≤ 50.000,00 TL, inclusive, and the field accepts only digits and a comma. The tests use only 2.500 and 20.000 (valid) and 75.000 and 60.000 (the latter inside FT-031) for invalid values, plus the 3-decimal case in FT-037. Nothing covers:
  - 1,00, 0,99 or 0,00
  - 50.000,00 or 50.000,01
  - a negative amount or letters in the field
- **Why it matters:** Off-by-one errors at the limits are the most likely defects in limit logic (for example `<` instead of `≤`). 50.000 is also a regulatory transaction limit.
- **Acceptance:**
  - 3 pt: the report names concrete missing boundary values on **both** the lower side (1,00 / 0,99 / 0) and the upper side (50.000,00 / 50.000,01).
  - 2 pt: only one side is named with values.
  - 1 pt: only a generic "tutar sınır değer / negatif testleri eksik" with no values.
  - Proposing those exact tests also counts toward Q2.

### K9: Production-looking personal data and a credential in a test
- **What:** The precondition of FT-012 holds a full real-looking customer identity: name Hatice Demirtaş, Müşteri No 48213377, TCKN 28461937502, date of birth, anne kızlık soyadı, e-mail and **"Mobil şifre: 482913"**. It also ignores the synthetic common test user. (The TCKN deliberately fails the checksum, so it belongs to no real person.)
- **Why it matters:** This breaks KVKK and data-minimisation rules, puts a credential in a shared document, and suggests production data is being used in test. It is also not repeatable on other environments.
- **Acceptance:**
  - 2 pt: the report flags FT-012 for personal data, sensitive data or a password, and recommends synthetic or masked data (for example the ft.test01 user or a test-data reference).
  - 1 pt: it only notes that FT-012 uses a different, hard-coded user, with no privacy or credential concern.

### K10: Expected result contradicts the story
- **What:** FT-022 waits **120 s** (enters the code at second 121) and expects "Doğrulama kodunun süresi doldu." AC-6 says the code is valid for **180 s**, and FT-035 itself expects a 03:00 countdown. At 121 s the code is still valid and the transfer should succeed.
- **Why it matters:** Run on a correct build, this test fails it. Run on a wrong build that expires the code at 120 s, it passes. Either way it hides a real defect or raises a false one on a Kritik security rule.
- **Acceptance:** 3 pt if the report names FT-022 and the 120 s vs 180 s conflict, and proposes a fix such as waiting past 180 s (e.g. 181 s), optionally with a 179 s pair. Flagging FT-022 for any other reason gets 0.

## 3. Traps (correct items that careless reviewers report)

| ID | Where | Why it is correct | Counted as a false positive when the report… | Penalty |
|---|---|---|---|---|
| T1 | FT-005 | AC-1 requires removing spaces and uppercasing, so `tr48 0099 …` must be **accepted** and shown as `TR48 0099 …`. | …says FT-005's expected result is wrong, or that a lowercase or spaced IBAN should be rejected. | −2 |
| T2 | FT-017 / FT-018 | They are a deliberate boundary pair for the OTP threshold: 9.999,99 gives no OTP, 10.000,00 gives OTP, matching "10.000,00 TL veya üzerindeyse". | …calls them duplicates or redundant, or recommends merging them or deleting one. | −2 |
| T3 | FT-023 | AC-7 says FAST runs 24/7 including weekends. A Sunday 03:00 transfer completing instantly with no EFT-hours warning is correct, and the story mentions the test environment's virtual clock. | …says the transfer should be rejected, queued or warned about, or that the precondition is unrealistic or invalid. | −2 |
| T4 | FT-013 | 140.000 + 10.000 = 150.000,00 exactly. AC-5 says the limit is inclusive ("150.000,00 TL dahil"), so acceptance with 0,00 left is correct. It pairs with FT-014 (10.000,01, rejected). | …says 150.000,00 should be rejected, or that the expected result contradicts AC-5. | −2 |

## 4. Other findings: false positives (−1) and neutral (0)

### 4.1 Known false positives (−1 each, at most −6 in total for this category)
- FT-008, FT-025, FT-026 and FT-027 called duplicates of each other. They share a 2.500 TL setup but check different things: the result screen, the balance, the history and the receipt. Only FT-026 and FT-038 are duplicates.
- FT-004 called invalid because "the DE IBAN is valid". That is intended: a valid non-TR IBAN must be rejected.
- FT-012's expected result called wrong. Sending the full available balance is allowed by AC-4. Only the data in FT-012 is the defect.
- FT-014's "Kalan limit: 10.000,00 TL" or FT-015's "149.900,00" called wrong. Both are arithmetically correct.
- FT-027's mask `TR48 **** **** **** **** **44 06` called wrong. It shows the first 4 and last 4 characters over 26 positions.
- FT-037 called contradictory. AC-3 says the field does not let a 3rd decimal be typed.
- FT-029 and FT-030 called duplicates. They are the 140 / 141 boundary pair.
- Claims that suite IBANs are invalid. All are valid (MOD-97) except the intentionally invalid ones in FT-002, FT-003 and FT-031 step 1. FT-004's DE IBAN is valid but non-TR.
- Claims that AC-5 or AC-10 lack boundary tests. AC-5 has FT-013 / FT-014 and AC-10 has FT-029 / FT-030.
- Claims that AC-7 has no tests. It has FT-023 and FT-024.
- Claims that AC-8 is "partly covered" by some existing test. This hurts K7 credit: award 0 for K7 if the report says AC-8 is covered.
- **General rule:** any claimed defect that the story plus the workbook show to be correct is −1.

### 4.2 Neutral (0 points, no penalty)
- Priority nitpicks other than FT-021, for example "FT-013 / FT-015 / FT-020 / FT-035 should be Kritik".
- FT-010 partly overlaps FT-018 (both reach the OTP screen). A redundancy remark is fine, as long as it does not say FT-017 and FT-018 are duplicates.
- Loosely specified data, for example:
  - "geçerli değerlerle doldur" in FT-003 and FT-004
  - FT-015 step 3 not naming the recipient
  - "000000" as a wrong OTP
- FT-035 "sayaç 00:00'da durur" is not stated in the story.
- FT-015 has two phases, before and after midnight.
- Missing tests that the story does not demand, such as OTP resend, back navigation or network loss. Also a public-holiday case for AC-7.
- Structural suggestions: add Test Verisi, Durum or Tip columns, rename IDs, tags, or reliance on the common precondition in the "Bilgi" sheet.
- Tests FT-025, FT-026 and FT-027 could be combined into one "post-transfer" check. This is a style opinion, as long as they are not called duplicates.

## 5. Scoring

### 5.1 Objective checks (do these first)

| # | Check | Effect |
|---|---|---|
| OC1 | `inceleme-raporu.md` exists in the run root and is not empty | if it fails, the **total score is 0** |
| OC2 | SHA-256 of `inputs/FAST_Transfer_Test_Cases.xlsx` is unchanged (`db575e88…0328`) | −2 if it changed |
| OC3 | The report is in Turkish | −1 if it is mostly not Turkish |
| OC4 | The grep aid below lists which key IDs the report mentions | locator only: the grader must read the context before awarding or penalising |

Grep aid. Run from the run directory:
```
python -c "import re,sys;t=open('inceleme-raporu.md',encoding='utf-8').read();ids=['FT-005','FT-011','FT-012','FT-013','FT-016','FT-017','FT-018','FT-021','FT-022','FT-023','FT-026','FT-031','FT-032','FT-033','FT-034','FT-036','FT-038','FT-039','FT-040','AC-8','50.000','180','120'];print({i:len(re.findall(re.escape(i),t)) for i in ids})"
```

### 5.2 Points
- **Detection (maximum 21).** Award the K1 to K10 points by the acceptance rules in section 2.
  - A finding counts only if it is tied to the right test ID or AC.
  - **Fix requirement:** if a credited finding has no actionable fix, halve its points. Examples of an actionable fix: the concrete expected result, the split into specific tests, the corrected priority, or the corrected wait time.
- **Report-quality bonus Q (maximum 3):**
  - Q1 (+1): a proposed test for AC-8 with steps and an expected result that include the warning text or the Vazgeç / Devam behaviour.
  - Q2 (+1): proposed AC-3 boundary tests with concrete values and the exact error message.
  - Q3 (+1): an AC-to-test traceability summary or matrix covering all 10 ACs.
- **Penalties:**
  - −2 for each trap triggered (T1 to T4).
  - −1 for each other false positive (section 4.1), at most −6 in total.
  - The OC penalties from 5.1.
- **Final score** = max(0, Detection + Q − Penalties). The maximum is **24**.
- **Also record:**
  - recall = number of K items with at least partial credit, out of 10
  - traps triggered, out of 4
  - false-positive count
  - wall-clock time

  Compare the with-skill and no-skill runs on the mean and the spread across runs.

### 5.3 Bands (guidance)

| Score | Rating |
|---|---|
| ≥ 19 | excellent |
| 14–18.5 | good |
| 9–13.5 | fair |
| < 9 | weak |

A strong review should find K1 to K6 and K9 almost always. K7, K8 and K10 separate systematic reviews (an AC-to-test matrix, boundary analysis, and cross-checking each oracle against the story) from skim reviews.

## 6. Verification record (by the trial author, 2026-09-30)

- The workbook was generated with `tools/gen_xlsx.py` (stdlib zipfile + XML) and rebuilds byte for byte to the SHA-256 above.
- It was parsed back with stdlib: `python -B tools/dump_xlsx.py inputs/FAST_Transfer_Test_Cases.xlsx --check` printed `OK: sheets=['Test Cases', 'Bilgi'] test_cases=40 multiline_step_cells=40`.
- It was opened read-only in Microsoft Excel through COM. Excel showed:
  - "Test Cases" with 41 used rows × 7 columns and "Bilgi" with 13 × 2
  - a 2-line step cell in FT-021
  - an empty E17 (FT-016)
  - no repair prompt
- Every planted item and trap was checked with the script below. All 15 checks plus the IBAN-data check printed PASS:
  - K1a, K1b, K2 to K10
  - T1 to T4
  - "only the intended IBANs are invalid"

  It also printed the AC coverage shown in section 1, and the amounts used in steps showed none of 0,00 / 0,99 / 1,00 / 50.000,00 / 50.000,01.

Verification script. Save it as `verify_review_trial.py` and run `python verify_review_trial.py C:\projeler\TestSkills\evals\trial-review`:

```python
# -*- coding: utf-8 -*-
import re, sys, importlib.util
sys.stdout.reconfigure(encoding="utf-8"); sys.dont_write_bytecode = True
TRIAL = sys.argv[1]
spec = importlib.util.spec_from_file_location("d", TRIAL + "/tools/dump_xlsx.py")
d = importlib.util.module_from_spec(spec); spec.loader.exec_module(d)
sheets = dict(d.read_workbook(TRIAL + "/inputs/FAST_Transfer_Test_Cases.xlsx"))
story = open(TRIAL + "/inputs/US-214_FAST_Transfer.md", encoding="utf-8").read()
rows, info = sheets["Test Cases"], sheets["Bilgi"]
H = rows[0]; TC = {r[0]: dict(zip(H, r + [""] * (7 - len(r)))) for r in rows[1:]}
res = []
def ok(name, cond):
    print(("PASS " if cond else "FAIL ") + name); res.append(bool(cond))
def mod97(i):
    i = i.replace(" ", "").upper(); r = i[4:] + i[:4]
    return int("".join(str(int(c, 36)) for c in r)) % 97 == 1
ibans = set(re.findall(r"[Tt][Rr]\d{2}(?: ?\d{4}){5} ?\d{1,2}", "\n".join("\t".join(r) for r in rows + info)))
bad = {i.replace(" ", "").upper() for i in ibans if not (mod97(i) and len(i.replace(" ", "")) == 26)}
ok("data: only the intended invalid IBANs (FT-002/FT-003/FT-031) are invalid", bad == {"TR590099100000730915284406", "TR48009910000073091528440"})
ACS = set(re.findall(r"### (AC-\d+)", story)); cov = {}
for tid, t in TC.items():
    for a in re.findall(r"AC-\d+", t["Gereksinim"]): cov.setdefault(a, []).append(tid)
print("coverage:", {a: len(cov.get(a, [])) for a in sorted(ACS | set(cov), key=lambda x: int(x[3:]))})
f = lambda tid: [TC[tid][h] for h in H[1:]]
ok("K1a exact duplicate FT-026 == FT-038", f("FT-026") == f("FT-038"))
a, b = TC["FT-011"], TC["FT-036"]
ok("K1b near duplicate FT-011 ~ FT-036", a["Gereksinim"] == b["Gereksinim"] == "AC-4" and a["Başlık"] != b["Başlık"]
   and all(x in a["Ön Koşul"] + a["Adımlar"] and x in b["Ön Koşul"] + b["Adımlar"] for x in ["1.000", "1.500", "TR48 0099 1000 0073 0915 2844 06"]))
ok("K2 missing expected: FT-016 empty, FT-034 'TBD'", TC["FT-016"]["Beklenen Sonuç"] == "" and TC["FT-034"]["Beklenen Sonuç"] == "TBD")
ok("K3 vague steps/oracle: FT-032, FT-033", "çalıştığını kontrol et" in TC["FT-032"]["Adımlar"] and "düzgün çalışmalı" in TC["FT-032"]["Beklenen Sonuç"]
   and "hatalı değerler gir" in TC["FT-033"]["Adımlar"] and TC["FT-033"]["Beklenen Sonuç"].startswith("Uygun hata"))
ok("K4 multi-behaviour FT-031", TC["FT-031"]["Adımlar"].count("\n") == 7 and len(re.findall(r"AC-\d+", TC["FT-031"]["Gereksinim"])) == 5
   and TC["FT-031"]["Beklenen Sonuç"] == "Tüm adımlar başarılı olmalı.")
ok("K5 FT-021 (3 wrong OTP -> cancel) is 'Düşük', Düşük = kozmetik", TC["FT-021"]["Öncelik"] == "Düşük"
   and "Kozmetik" in [r for r in info if r and r[0] == "Düşük"][0][1] and "3. hatalı girişte" in story)
ok("K6 FT-039 -> AC-11 (nonexistent), FT-040 empty + SWIFT out of scope", TC["FT-039"]["Gereksinim"] == "AC-11" and "AC-11" not in ACS
   and TC["FT-040"]["Gereksinim"] == "" and "SWIFT" in story.split("## Kapsam dışı")[1])
alltext = "\n".join("\t".join(r) for r in rows[1:])
ok("K7 AC-8 has no test", "AC-8" in ACS and not cov.get("AC-8") and not re.search(r"[Mm]ükerrer|10 dakika|kısa süre önce", alltext))
steps = "\n".join(TC[t]["Adımlar"] for t in TC)
amounts = set(re.findall(r"(?<![\d.,])(\d{1,3}(?:\.\d{3})*,\d{2,3})(?!\d)", steps))
print("amounts used in steps:", sorted(amounts, key=lambda s: float(s.replace(".", "").replace(",", "."))))
ok("K8 no AC-3 boundary / negative amount tests", not (amounts & {"0,00", "0,99", "1,00", "1,01", "49.999,99", "50.000,00", "50.000,01"})
   and not re.search(r"-\d|harf", "\n".join(TC[t]["Adımlar"] for t in TC if "AC-3" in TC[t]["Gereksinim"])))
p = TC["FT-012"]["Ön Koşul"]
ok("K9 PII in FT-012", re.search(r"TCKN: \d{11}", p) and all(x in p for x in ["Anne Kızlık Soyadı", "Doğum Tarihi", "Mobil şifre", "Müşteri No"]))
ok("K10 FT-022 expiry at 120 s vs story 180 s", "120 saniye" in TC["FT-022"]["Adımlar"] and "süresi doldu" in TC["FT-022"]["Beklenen Sonuç"]
   and "**180 saniye**" in story and "03:00" in TC["FT-035"]["Beklenen Sonuç"])
ok("T1 FT-005 normalised IBAN accepted", "küçük harf" in TC["FT-005"]["Adımlar"] and "Hata mesajı gösterilmez" in TC["FT-005"]["Beklenen Sonuç"]
   and "küçük harfler büyük harfe çevrilir" in story)
ok("T2 FT-017/FT-018 OTP boundary pair", "9.999,99" in TC["FT-017"]["Adımlar"] and "OTP ekranı açılmaz" in TC["FT-017"]["Beklenen Sonuç"]
   and "10.000,00" in TC["FT-018"]["Adımlar"] and "OTP ekranı açılır" in TC["FT-018"]["Beklenen Sonuç"] and "10.000,00 TL veya üzerindeyse" in story)
ok("T3 FT-023 Sunday 03:00 succeeds", "Pazar 03:00" in TC["FT-023"]["Ön Koşul"] and "anında gerçekleşir" in TC["FT-023"]["Beklenen Sonuç"] and "7 gün 24 saat" in story)
ok("T4 FT-013 exactly 150.000 accepted", "140.000,00" in TC["FT-013"]["Ön Koşul"] and "10.000,00" in TC["FT-013"]["Adımlar"]
   and "Transfer tamamlanır" in TC["FT-013"]["Beklenen Sonuç"] and "150.000,00 TL dahil" in story)
print("ALL PASS" if all(res) else "SOME FAILED"); sys.exit(0 if all(res) else 1)
```
