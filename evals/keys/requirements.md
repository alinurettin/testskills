# Answer key — trial-requirements (Kolay İade ve Geri Ödeme PRD v1.3)

EVALUATOR ONLY. Never place this file (or anything in `evals\keys\`) in an agent's run folder.

- Trial folder: `C:\projeler\TestSkills\evals\trial-requirements\`
- Inputs given to the agent: `TASK.md`, `girdiler\PRD-Kolay-Iade-v1.3.md`, `girdiler\Ek-B-kategori-iade-kurallari.csv`
- Expected deliverables: `gereksinim-analizi.md`, `test-edilebilir-gereksinimler.md`
- Integrity check of the inputs: `python C:\projeler\TestSkills\evals\keys\requirements_verify.py`
- Keyword pre-screen of a run: `python C:\projeler\TestSkills\evals\keys\requirements_grade_assist.py <run-folder>` (evidence only; the rubric below decides)

## Scoring summary

| Part | Max |
|---|---|
| Planted items K1–K12 (4 easy × 2, 4 medium × 3, 4 hard × 4) | 36 |
| Deliverable quality Q1–Q5 | 10 |
| **Total** | **46** |
| Trap penalties T1–T4 | −3 each (max −12) |
| Other false positives | −1 each (max −4) |

`Final = max(0, K + Q − trap penalties − other FP penalties)`. Also report the secondary metric "planted detection" = K points / 36 and the list of traps triggered.

General grading rules

- Credit an item when the deliverable (either file) states the problem in substance; exact wording, IDs or finding categories do not matter. A finding that names the location and the concrete conflict gets full credit even if the agent's priority is debatable (priority is graded in Q5).
- Credit each K at most once. One deliverable finding can earn credit for two K items only if it explicitly states both problems.
- A rewrite in `test-edilebilir-gereksinimler.md` that quietly fixes a problem without ever saying the original was ambiguous / conflicting does not earn the K credit; it may still count for Q4.
- Partial ("half") credit is given only where an item lists it.

---

## Planted items

### K1 — NFR-1 performance requirement is untestable (EASY, 2 pts, severity Medium)

- **Where:** §6 NFR-1: "İade ekranları hızlı açılmalıdır ... sistem makul sürede yanıt vermelidir."
- **Problem:** "hızlı" and "makul sürede" have no measurable target; the campaign peak load ("Kasım indirimleri", "artan iade trafiği") is not quantified. No pass/fail oracle for performance or load testing.
- **Full credit:** flags NFR-1 (or its "hızlı"/"makul" wording) as unmeasurable / untestable and asks for or proposes measurable targets (e.g. p95 response time, peak requests or concurrent users, error rate).
- **Not enough:** flagging only the US-3 narrative "paramı hızlıca" (that story's AC-3.1/BR-10 quantify it) — 0 for K1, no penalty.

### K2 — "Uygun durumda" inspection criterion is undefined (EASY, 2 pts, severity High)

- **Where:** §3 US-4 AC-4.2: "Ürün uygun durumda ise operatör 'Onayla' ... değilse 'Reddet'".
- **Problem:** No objective acceptance criteria for the warehouse decision (original packaging, labels, signs of use, missing accessories, partial acceptance of multi-unit lines). The approve/reject outcome, and therefore the refund, cannot be tested or audited consistently.
- **Full credit:** flags "uygun durum" (AC-4.2) as subjective/undefined and asks for concrete inspection criteria.

### K3 — Refund start time contradiction: 3 vs 5 business days (EASY, 2 pts, severity High)

- **Where:** AC-3.1 "en geç 3 iş günü içinde başlatılır" vs BR-10 "onay tarihinden itibaren 5 iş günü içinde başlatılır". (The v1.3 changelog says BR-10 was updated on the payments team's request, suggesting AC-3.1 was not updated, but the document is still self-contradictory.)
- **Problem:** Two different oracles for the same SLA; customer communication and SLA monitoring tests cannot both pass.
- **Full credit:** identifies the 3 vs 5 business-day conflict between AC-3.1 and BR-10 (both values or both locations named).

### K4 — No KVKK / personal-data requirements for return data, especially uploaded photos (EASY, 2 pts, severity High)

- **Where:** AC-1.3 (1–5 mandatory photos for "hasarlı/kusurlu"), AC-1.4 (e-mail/SMS), AC-4.2 (free-text rejection reason), NFR-4 (only application logs have a retention period). The PRD contains no KVKK, privacy notice (aydınlatma), consent, retention, deletion or access-control rule for this data.
- **Problem:** Photos can contain personal data (faces, addresses, labels); without retention/deletion/access rules there is nothing to test and a legal risk.
- **Full credit:** raises missing KVKK / personal-data requirements tied to at least one concrete element: uploaded photos, retention/deletion period, aydınlatma/consent, or who may access the photos/notes.
- **Half credit (1):** generic "KVKK uyumu belirtilmemiş" with no concrete data element or obligation.

### K5 — 500 TL boundary gap between Hızlı İade and mandatory inspection (MEDIUM, 3 pts, severity High)

- **Where:** BR-07 "tutarı 500 TL'nin **altındaki** iadelerinde" (Hızlı İade) vs AC-4.3 "Tutarı 500 TL'nin **üzerindeki** iadelerde depo kontrolü tamamlanmadan geri ödeme başlatılamaz".
- **Problem:** Exactly 500,00 TL is covered by neither rule: not eligible for Hızlı İade (not < 500) but inspection is not mandatory (not > 500), so behaviour at the boundary is undefined. In addition, "tutar" is undefined (per line or per request; before or after the coupon share; before or after the 39,90 TL deduction).
- **Full credit:** points out that the exact 500,00 TL boundary (inclusive/exclusive) is undefined or falls into a gap for Hızlı İade / mandatory inspection.
- **Half credit (1.5):** only the "tutar" basis ambiguity (line vs request, pre/post coupon) without the boundary point.

### K6 — Customer-service manual override has no authorization limits and no audit trail (MEDIUM, 3 pts, severity High)

- **Where:** US-5 AC-5.1 (MH can approve any request, including expired ones) and AC-5.2 (MH can change the refund amount and refund the return shipping fee "gerekli gördüğü durumlarda"). NFR-4 logs only status changes in application logs for 90 days.
- **Problem:** Unlimited manual refund changes are a fraud / financial-control risk; no role/permission definition, amount limit, second approval (four-eyes), mandatory reason, or audit record (who, when, old/new amount, reason). Nothing to test for authorization (negative tests) or auditability.
- **Full credit:** tied to the MH override (US-5 / AC-5.1 / AC-5.2): flags missing authorization limits / approval rules **or** missing audit trail for these actions (both preferred, either suffices).
- **Half credit (1.5):** generic "audit trail / yetkilendirme eksik" not tied to the MH manual override.

### K7 — Unstated dependency: the "risk skoru" used by Hızlı İade (MEDIUM, 3 pts, severity High)

- **Where:** BR-07 "Risk skoru 'düşük' olan müşterilerin ...". The term appears nowhere else (not in §2, not in stakeholders, no integration described).
- **Problem:** Hızlı İade eligibility depends on a score from an unspecified system: no owner/source/interface, no scale or threshold for "düşük", no timing (at request creation or at drop-off), no behaviour when the score is unavailable or times out. Testers cannot set up or control this input.
- **Full credit:** identifies the risk score as an undefined external input / dependency (who produces it, where it comes from, how it is obtained) **or** asks for the fallback when it is unavailable.
- **Half credit (1.5):** only says the word "düşük" is vague/threshold undefined without treating the score itself as an undefined dependency.

### K8 — Ek-B contradicts BR-04 for cosmetics (MEDIUM, 3 pts, severity High)

- **Where:** BR-04 "Kozmetik ve kişisel bakım ürünlerinde ambalajı veya koruma bandı açılmış ürünler iade alınmaz." vs Ek-B CSV row `KOZ-01;Kozmetik ve Kişisel Bakım;EVET;15;EVET;Kullanılmamış olmalı` — `acilmis_ambalaj_kabul = EVET` (opened packaging accepted). The Ek-B section of the PRD defines that column as whether an opened-package item is accepted at inspection.
- **Problem:** The two sources give opposite expected results for the same inspection case (opened cosmetic product).
- **Full credit:** identifies the KOZ-01 / BR-04 conflict on opened packaging.

### K9 — Ek-B gives phones a SHORTER period (14 days) but BR-01 only lets longer Ek-B periods override (HARD, 4 pts, severity High)

- **Where:** Ek-B row `ELK-02;Cep Telefonu;EVET;14;HAYIR;...` vs BR-01 "Standart iade süresi 15 gündür ... Ek-B'de bir kategori için **daha uzun** bir süre tanımlanmışsa o süre geçerlidir" and AC-1.5 "İade süresi standart olarak 15 gündür".
- **Problem:** The precedence rule covers only longer category periods. For phones it is undefined whether 14 or 15 days applies, so the day-15 boundary test for a phone has no oracle (and the "İade Et" button visibility in AC-1.1 is undefined on day 15). Contrast with trap T3 (30-day clothing rows are explicitly covered by BR-01).
- **Full credit:** names the phone row / 14 days and states the conflict or unclear precedence with the 15-day standard / BR-01.
- **Half credit (2):** generic "Ek-B ile BR-01 arasındaki öncelik kuralı belirsiz / eksik" without identifying the phone row or a shorter-than-standard period.

### K10 — Ek-A worked example 2 contradicts BR-06 (HARD, 4 pts, severity High)

- **Where:** Ek-A Örnek 2: order lines 4.200,00 + 600,00 + 2 × 300,00 = 5.400,00 TL, coupon 400,00 TL, returned line kahve makinesi 4.200,00 TL, reason "Fikrimi değiştirdim", Nergis Cüzdan. The table shows coupon share **280,00 TL**, refund 3.880,10 TL, bonus 116,40 TL, total **3.996,50 TL**.
- **Correct per BR-05/06/09:** coupon share = 400 × 4.200 / 5.400 = 311,11 (311,111…); refund = 4.200,00 − 311,11 − 39,90 = **3.848,99 TL**; bonus = 3 % × 3.848,99 = 115,4697 → **115,47 TL** (below the 150,00 cap); wallet total = **3.964,46 TL**. The example overpays by 32,04 TL. (If an agent takes the bonus base before the 39,90 deduction, it gets bonus 116,67 and total 3.965,66 — still credit, the key point is that 280,00 is wrong.) The rest of the example's arithmetic is internally consistent, so only recomputation from BR-06 reveals the error. Örnek 1 is correct (100,00 share, 900,00 refund).
- **Problem:** Ek-A is explicitly given to testers as a reference oracle; using it would encode a wrong expected result in the refund tests, and the document disagrees with itself about the refund formula.
- **Full credit:** states that Örnek 2's coupon share / refund / total does not follow BR-06, with at least one concrete figure (280,00 is wrong, or the correct 311,11, or a correct recomputed final amount).
- **Half credit (2):** says Ek-A examples must be checked / "hesap tutarsız olabilir" without a concrete figure, or only notes that 311,111… needs a rounding rule without noticing that the example uses 280,00.
- **False positive (−1 under "other FP"):** claiming Örnek 1 is wrong.

### K11 — Cash-on-delivery orders have no refund path (HARD, 4 pts, severity Critical)

- **Where:** §1 scope includes "kapıda ödeme (nakit veya kartla) ile verilmiş bireysel siparişler"; AC-3.2 "Geri ödeme, siparişin ödendiği yönteme (orijinal ödeme yöntemine) yapılır" with Nergis Cüzdan only as an optional alternative.
- **Problem:** A cash payment cannot be refunded to the "original payment method". There is no defined path (IBAN capture and validation, account-holder name match, KVKK for bank data, forced wallet refund, or MH handling), so an in-scope order type has no testable refund behaviour. Card-at-door (POS) refunds are also unspecified.
- **Full credit:** explicitly links cash-on-delivery (kapıda ödeme) orders to the missing refund method.
- **Half credit (2):** generic "orijinal ödeme yöntemine iade yapılamazsa (kart kapanmış vb.) ne olacak?" without connecting it to cash-on-delivery.

### K12 — Incomplete return state lifecycle (HARD, 4 pts, severity High)

- **Where:** §5 table (TALEP_ALINDI → KARGODA → DEPODA → ONAYLANDI → GERİ_ÖDEME_BAŞLATILDI → TAMAMLANDI) plus "Durumlar yalnızca tablodaki sıraya göre ilerler."
- **Missing states / transitions that the document itself requires elsewhere:**
  1. Customer cancellation before drop-off (AC-2.3) — no İPTAL state.
  2. Automatic closure when the 7-day cargo code expires (AC-2.2) — no expired/closed state.
  3. Rejection at inspection (AC-4.2 "Reddet") — no REDDEDİLDİ state, and nothing on what happens next (parcel returned to customer? refund? notification?).
  4. Hızlı İade (BR-07) starts the refund at KARGODA, before DEPODA/ONAYLANDI — the transition is not allowed by the table; and a later inspection rejection after the refund was already paid (clawback) is undefined.
  5. MH manual approval (AC-5.1), including expired requests — which states does it bypass?
  6. Refund failure (bank rejects / card closed) — no failure state or retry.
- **Full credit:** names at least 2 of the specific gaps above in relation to the state model / transitions.
- **Half credit (2):** exactly one specific gap, or a generic "negatif / alternatif durumlar eksik" without naming any.

---

## Traps (correct, defined content that careless reviewers report as problems)

Penalty −3 per trap, counted once per trap even if repeated. No penalty if the deliverable mentions the topic but recognises it is already defined (e.g. "§2'de tanımlı; test verisinde kullanıldı"). Using the definition to design boundary tests is correct behaviour.

### T1 — Return-window counting is fully defined

- **Defined in:** §2 "Teslim tarihi" (Pusula Kargo "TESLİM EDİLDİ" time, Türkiye saati UTC+3 calendar day) and "İade süresi" (counting starts the day after delivery; requests until 23:59:59 Türkiye saati on the last day are in time; worked example 1 Ekim delivery → last moment 16 Ekim 23:59:59).
- **Trap triggered if** the deliverable reports as ambiguous/missing: whether the delivery day counts, whether the last day is inclusive, the cut-off time, or the time zone of the 15/30-day return window.
- **Not a trap hit:** what happens if the delivery event never arrives or is wrong; the 7-day cargo-code validity (AC-2.2) boundary; how the 7-day code interacts with a window that ends earlier; the phone 14/15-day conflict (K9).

### T2 — "İş günü" is fully defined

- **Defined in:** §2 "İş günü": Monday–Friday, official and religious holidays excluded, half-day eves count as full business days, the start day is not counted, the period ends at 23:59:59 Türkiye saati on the last business day.
- **Trap triggered if** the deliverable reports "iş günü" as undefined, or asks whether weekends / public holidays / bayram / arife count, or whether the approval day counts.
- **Not a trap hit:** the 3 vs 5 business-day conflict (K3); "what is the approval moment for Hızlı İade / MH approval" questions.

### T3 — 30-day clothing/shoe periods do not contradict the 15-day standard

- **Defined in:** BR-01 "Ek-B'de bir kategori için daha uzun bir süre tanımlanmışsa o süre geçerlidir." Ek-B GIY-01, GIY-02, AYK-01 = 30 days.
- **Trap triggered if** the deliverable reports the 30-day Ek-B rows as conflicting with AC-1.5 / BR-01's 15 days.
- **Not a trap hit:** K9 (a shorter Ek-B period, which BR-01 does not cover).

### T4 — The wallet bonus is fully specified

- **Defined in:** BR-09: 3 % of the refund amount, max 150,00 TL per return request, rounded half-up to the kuruş, credited together with the refund in one go. AC-3.2's "ek bonus kazanır (BR-09)" points there.
- **Trap triggered if** the deliverable reports the bonus rate, amount, cap, rounding or timing as undefined (e.g. "AC-3.2'deki 'ek bonus' belirsiz").
- **Not a trap hit (neutral, 0 points):** bonus clawback when a Hızlı İade is later rejected; bonus when MH changes the amount; whether the 3 % base is before or after the 39,90 TL deduction.

## Other false positives (−1 each, max −4)

Claims that the documents directly contradict, for example:

- "Kargo ücretini kimin ödeyeceği tanımsız" (BR-05 defines it per reason, 39,90 TL).
- "İade edilemeyen ürünler tanımlı değil" (BR-02 + Ek-B `iade_edilebilir = HAYIR`).
- "Kısmi iadede gönderim kargo ücretinin iadesi belirsiz" (BR-06: refunded only when all items are returned).
- "Müşterinin başka müşterinin talebini görmesi engellenmemiş" (NFR-2).
- "Cüzdan bakiyesinin nakde çevrilip çevrilemeyeceği belirsiz" (§2 Nergis Cüzdan).
- "Aynı ürün için birden fazla açık talep açılabilir mi belirsiz" (BR-08).
- "İade süresi sipariş bazında mı ürün bazında mı belirsiz" (BR-03).
- "Desteklenen platform/tarayıcılar tanımsız" (NFR-5).
- "Ek-A Örnek 1 hatalı" (it is correct).
- Misreading a value in the CSV or PRD (e.g. stating Kozmetik has 30 days).

## Valid non-keyed findings (0 points, no penalty)

These are legitimate but not keyed; do not penalise them and do not award K points for them:

- Rounding/remainder rule for the proportional coupon share (311,111…; sum of per-line shares may differ from the coupon by 0,01 TL) and per-unit share when only part of a line's quantity is returned (AC-1.2).
- 7-day cargo-code validity vs the return window (can a request created on the last day be shipped later?); "7 gün" measured in hours or calendar days.
- Pusula Kargo integration failures (code cannot be generated, drop-off event missing) and missing delivery event.
- Photo upload limits (file types, size, malware scanning); free-text rejection reason validation.
- Notification failures; e-mail/SMS content; push opt-out.
- Accessibility: AC-6.1 status conveyed by colour only (yeşil/gri/kırmızı); no WCAG target.
- The 3-screen rule's definition of "ekran"; "İADE-" prefix with Turkish dotted İ in IDs (locale/encoding risk).
- Concurrency (customer cancels while the parcel is being scanned), idempotency of refunds.
- Log retention of 90 days possibly too short for financial records.
- The success metric (%40 call reduction) not measurable by testing.

## Quality rubric (10 pts)

| ID | Criterion | Points |
|---|---|---|
| Q1 | Both deliverables exist with the exact file names, are in Turkish, and the findings table has the requested columns (ID, yer, tür, açıklama/teste etki, öncelik, netleştirme sorusu). | 1 |
| Q2 | Every finding cites a concrete location (section / AC / BR / NFR / Ek-B row) and has a priority from the requested scale. 2 = all; 1 = at least 80 %; 0 = less. | 2 |
| Q3 | Clarification questions are specific and answerable (name the conflicting values or options, ideally closed or multiple-choice), one per finding. 2 = consistently; 1 = mixed; 0 = generic or missing. | 2 |
| Q4 | Testable rewrites: count rewrites that have measurable criteria, explicit boundary values and expected results (Given/When/Then, rule tables or equivalent) and that label invented values as assumptions pending confirmation. 4 = at least 5 qualifying rewrites covering at least 3 different K items; 3 = at least 5 qualifying, or 4 qualifying covering 3 K items; 2 = 2–3 qualifying; 1 = 1 qualifying; 0 = none. A rewrite that silently picks one side of a contradiction (e.g. "5 iş günü") without flagging it as an assumption/decision needed does not qualify. | 4 |
| Q5 | Prioritisation is sensible: of the K items found among K3, K4, K6, K8, K10, K11, K12, at least 75 % are rated Kritik or Yüksek, and no money/legal item is rated Düşük. | 1 |

## Reference: what a strong answer contains (for graders)

- K3: "AC-3.1 '3 iş günü' ile BR-10 '5 iş günü' çelişiyor; SLA testinin beklenen sonucu hangisi?"
- K5: "500,00 TL tam sınırda: BR-07 '<500' Hızlı İade, AC-4.3 '>500' zorunlu kontrol diyor; 500,00 TL'lik iade hangi akışa girer? Tutar talep toplamı mı, ürün satırı mı, kupon sonrası mı?"
- K8: "Ek-B KOZ-01 'acilmis_ambalaj_kabul = EVET', BR-04 açılmış kozmetiği reddediyor."
- K9: "Ek-B ELK-02 cep telefonu 14 gün; BR-01 yalnızca daha uzun süreler için Ek-B'yi geçerli kılıyor; telefon için 14 mü 15 mi?"
- K10: "Ek-A Örnek 2'de kupon payı 280,00 değil 400 × 4.200 / 5.400 = 311,11 olmalı; doğru cüzdan toplamı 3.848,99 + 115,47 = 3.964,46 TL (örnek 3.996,50)."
- K11: "Kapıda nakit ödenen siparişte 'orijinal ödeme yöntemine iade' mümkün değil; IBAN mı, cüzdan mı?"
- K12: "Bölüm 5'te İPTAL (AC-2.3), süresi dolan kod (AC-2.2), RED (AC-4.2) durumları ve Hızlı İade'nin KARGODA → GERİ_ÖDEME_BAŞLATILDI geçişi yok; Hızlı İade sonrası ret olursa ne olacak?"

## Expected discrimination

A quick generic pass typically finds K1–K3, K5, K4 (often only half), K6 and part of K12, and frequently trips T1 (asks whether the 15 days include the delivery day) and T2 (asks about holidays), giving roughly 40–55 % of 46. Reaching 90 %+ requires reading the CSV row by row against the BRs (K8, K9), recomputing Ek-A (K10), following an in-scope payment type through the refund rules (K11), and checking every referenced state against §5 (K12), while not reporting T1–T4.
