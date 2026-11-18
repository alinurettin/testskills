# Answer Key — trial-api3 (Turna Oto Kiralama: Rezervasyon ve Kiralama API)

Kind: REST API testing from an OpenAPI 3.1 contract (successor of trial-api2).
Trial folder: `C:\projeler\TestSkills\evals\trial-api3\`
System under test (evaluator-only): `trial-api3\server.js`
Verifier (ground truth): `C:\projeler\TestSkills\evals\keys\grade_api3.py`
→ A fresh server + verifier prints `91/91 checks behaved as designed.`

The agent is given only `TASK.md` + `openapi.yaml` + base URL + the four tokens.
It must find defects by probing the running API and comparing with the contract.

**Why this trial exists.** In trial-api2 every strong run found all ten planted
defects in about 25 minutes, because they were one- or two-request findings.
Here only three of sixteen defects are of that kind. The others need a sequence
of requests, a specific prior state, arithmetic derived from the prose rules, a
comparison between two endpoints, or a seed record with a special property. For
each of them the cheap check passes (see "Discriminator").

Max score **100** = 88 detection + 12 report quality, minus penalties.

---

## Environment facts the grader needs

- Tokens: `tok_musteri_elif` (customer `mus_1`), `tok_musteri_baran` (customer
  `mus_2`), `tok_personel_ist` (staff `per_1`, branch `IST`), `tok_yonetici`
  (admin). A third customer `mus_3` exists in the data and has no token.
- Fixed simulated clock: **2026-03-10T09:00:00+03:00** (a Tuesday). Nothing
  depends on the real date. Restart = reset. Port from `PORT` (default 3210);
  parallel copies are independent.
- Evaluator-only: `API3_PLANTED=off` starts a contract-correct reference server
  (all sixteen defects disabled). `grade_api3.py <url> --reference` passes
  against it. Use it to decide doubtful claims (see "Scoring rubric").

### Seed vehicles

| id | car | class | gear | seats | branch | dailyRate | extraKmRate | status |
|----|-----|-------|------|-------|--------|-----------|-------------|--------|
| arc_01 | Fiat Egea | ekonomi | manuel | 5 | IST | 1150.00 | 3.50 | available |
| arc_02 | Renault Megane | orta | otomatik | 5 | IST | 1450.00 | 4.00 | available |
| arc_03 | Dacia Duster | suv | manuel | 5 | IST | 1890.00 | 5.00 | available |
| arc_04 | Volvo S90 | premium | otomatik | 5 | IST | **3299.99** | 9.00 | available |
| arc_05 | Hyundai i20 | ekonomi | otomatik | 5 | IST | **1187.45** | 3.50 | available |
| arc_06 | Ford Tourneo | suv | manuel | 7 | IST | 2100.00 | 5.50 | maintenance |
| arc_07 | Renault Clio | ekonomi | manuel | 5 | ANK | 1090.00 | 3.50 | available |
| arc_08 | Toyota Corolla | orta | otomatik | 5 | ANK | 1520.00 | 4.00 | available |
| arc_09 | Peugeot 3008 | suv | otomatik | 5 | ANK | 2250.00 | 5.50 | available |
| arc_10 | Fiat Egea | ekonomi | manuel | 5 | IZM | 1120.00 | 3.50 | available |
| arc_11 | Volkswagen Passat | orta | otomatik | 5 | IZM | 1675.50 | 4.50 | available |
| arc_12 | Opel Corsa | ekonomi | manuel | 5 | IZM | 990.00 | 3.00 | retired |

### Seed reservations (17) and invoices (7)

| id | customer | car | pick-up → return (+03:00) | status | notes |
|----|----------|-----|---------------------------|--------|-------|
| rez_1001 | mus_1 | arc_02 | 03-08 10:00 → 03-13 10:00 | active | handed over at 41200 km, fuel 8 |
| rez_1002 | mus_3 | arc_08 | 03-07 12:00 → 03-12 12:00 | active | one-way ANK → **IST**; fuel 6 at hand-over |
| rez_1003 | mus_2 | arc_09 | 03-09 09:00 → 03-11 09:00 | active | ANK → ANK |
| rez_1004 | mus_1 | arc_03 | 03-14 10:00 → 03-17 10:00 | confirmed | `navigasyon`; **has a staffNote** |
| rez_1005 | mus_2 | arc_01 | **03-21 01:30** → 03-23 01:30 | confirmed | night pick-up; young-driver fee 400 although the driver is 25 on 03-21 (K5) |
| rez_1006 | mus_1 | arc_10 | **03-28 00:45** → 03-30 12:00 | confirmed | night pick-up |
| rez_1007 | mus_2 | arc_05 | 03-11 15:00 → 03-14 15:00 | confirmed | `ek_surucu`; **has a staffNote**; 30 h before pick-up |
| rez_1008 | mus_3 | arc_02 | 03-13 14:00 → 03-16 14:00 | confirmed | |
| rez_1009 | mus_3 | arc_07 | 03-20 10:00 → 03-27 10:00 | confirmed | 7 days, 10% discount |
| rez_1010 | mus_2 | arc_03 | 03-18 10:00 → 03-22 10:00 | **cancelled** | coupon **BAHAR15**; fee 0 |
| rez_1011 | mus_1 | arc_01 | 03-06 09:00 → 03-08 09:00 | cancelled | fee 2300.00 |
| rez_1012 | mus_1 | arc_01 | 02-10 → 02-13 | completed | fat_5001 (IST) 3450.00 / 690.00 / 4140.00 |
| rez_1013 | mus_2 | arc_07 | 02-14 → 02-16 | completed | fat_5002 (ANK) 2580.00 / 516.00 / 3096.00 |
| rez_1014 | mus_3 | arc_11 | 02-20 → 02-24 | completed | 3 h late; fat_5003 (IZM) 7204.65 / 1440.93 / 8645.58 |
| rez_1015 | mus_1 | arc_08 | 02-25 → 02-27 | completed | one-way ANK → IST; fat_5004 (ANK) 3940.00 / 788.00 / 4728.00 |
| rez_1016 | mus_3 | arc_03 | 02-26 → 02-28 | completed | **fat_5005 (IST) is `void`** 8780.00 / 1756.00 / 10536.00; fat_5006 (IST) issued 5280.00 / 1056.00 / 6336.00 |
| rez_1017 | mus_2 | arc_10 | 03-02 → 03-05 | completed | fat_5007 (IZM) 5285.00 / 1057.00 / 6342.00 |

Driver data in the seed: mus_1 born 1990-06-14, mus_2 born **2001-03-20**
(turns 25 ten days after "now"), mus_3 born 1985-11-02.

---

## Planted defects (K1..K16)

Grade `bulgular.md` **blind**. A defect counts only if the report names the
endpoint and the behaviour and gives reproduction evidence that satisfies the
acceptance rule. One root cause reported several times counts once.

Full points need the item under "Kusurlar". Half points (rounded down) are
awarded in exactly two cases, otherwise the item earns nothing:

1. the item's own "Half" rule below is met (K6, K7, K10, K13, K15, K16), or
2. the acceptance rule is met with full evidence, but the item stands only under
   "Açık sorular ve gözlemler": the tester saw it and did not commit, although
   the contract is explicit.

Three items are "checklist" findings (K1–K3). All others belong to one of the
hard classes; K4–K6 are rated medium because one well-chosen request (or one
look at the seed) is enough once the tester thinks of it.

| K | Defect | Class | Severity | Difficulty | Points |
|---|--------|-------|----------|------------|--------|
| K1 | Customer reads any invoice by id | checklist (object-level authz) | High | Easy | 4 |
| K2 | Unknown extra code accepted | checklist (schema enum) | Low | Easy | 4 |
| K3 | Cancelling a cancelled reservation answers 200 | checklist (state / status code) | Low | Easy | 4 |
| K4 | Cancellation exactly 48 h before pick-up is free | time-dependent boundary | Medium | Medium | 6 |
| K5 | Young-driver fee uses the age "today" | time-dependent | Medium | Medium | 6 |
| K6 | BAHAR15 stays "used" after the reservation is cancelled | prior state / seed record | Medium | Medium | 6 |
| K7 | PATCH keeps the old duration-discount percentage | sequence + cross-endpoint + arithmetic | High | Hard | 6 |
| K8 | Idempotency keys are shared between users | sequence, two tokens | High | Hard | 6 |
| K9 | Return is authorised by the pick-up branch | role × one-way rental | High | Hard | 6 |
| K10 | `staffNote` returned to customers by PATCH / cancel | field-level authz, seed record | Medium | Hard | 5 |
| K11 | `GET /vehicles` sorts after cutting the page | sort × pagination | Medium | Hard | 6 |
| K12 | `pickupFrom` / `pickupTo` use the UTC day | time zone, seed record | Medium | Hard | 5 |
| K13 | Revenue report counts `void` invoices | cross-endpoint arithmetic, seed record | High | Hard | 6 |
| K14 | Late-fee cap is one daily rate also after 24 h | arithmetic, 4-request sequence | Medium | Hard | 6 |
| K15 | `active` reservations do not block the car | prior state + cross-endpoint | Critical | Hard | 7 |
| K16 | VAT truncated instead of rounded half-up | rounding, only some cars | Low | Hard | 5 |

**Detection subtotal: 88 points** (checklist 12 · medium 18 · hard 58).

### K1 — Customer reads any invoice by id
- **What:** `GET /invoices/{id}` has no ownership check for the customer role.
  `tok_musteri_baran` → `GET /invoices/fat_5001` (owner `mus_1`) → 200.
- **Contract:** `GET /invoices/{id}`: "müşteri yalnızca kendi faturasını … görebilir.
  Kapsam dışındaki fatura için 403 döner."
- **Acceptance:** a customer token reads an invoice of another customer through
  `GET /invoices/{id}` (status 200 and the foreign `customerId`).
- **Discriminator:** `GET /invoices` (list) is scoped correctly; reservations by
  id are protected (403); a staff member of another branch gets 403 on the same
  endpoint.
- Severity High · Easy · **4 points**

### K2 — Unknown extra code accepted
- **What:** `extras` items are not checked against the enum in `POST /quotes`,
  `POST /reservations` and `PATCH /reservations/{id}`. `["navigasyon","sunroof"]`
  → 200/201; the unknown code is stored and echoed, it is not priced.
- **Contract:** `BookingRequest.extras`: enum `ExtraCode` and "Listede olmayan bir
  ekstra kodu ya da aynı kodun tekrarı 400 `VALIDATION_ERROR` ile reddedilir."
- **Acceptance:** a request with an extra code outside the enum is accepted.
- **Discriminator:** duplicates, non-string items, more than 4 items and every
  other field are validated (400).
- Severity Low · Easy · **4 points**

### K3 — Cancelling a cancelled reservation answers 200
- **What:** a second `POST /reservations/{id}/cancel` returns 200 with the
  unchanged cancelled reservation.
- **Contract:** "Yalnızca `confirmed` durumundaki rezervasyon iptal edilebilir; diğer
  bütün durumlarda (zaten iptal edilmiş rezervasyon dahil) 409 `INVALID_STATE` döner."
- **Acceptance:** cancel on a reservation that is already `cancelled` → 200.
- **Discriminator:** cancel on `active` and `completed` reservations → 409.
- Severity Low · Easy · **4 points**

### K4 — Cancellation exactly 48 hours before pick-up is free
- **What:** the fee tier test is `>= 48 h` instead of `> 48 h`. A reservation
  with `pickupAt` = `2026-03-12T09:00:00+03:00` (exactly 48 h after "now") is
  cancelled with `cancellation.fee` 0.
- **Contract:** cancel: "48 saatten FAZLA kaldıysa: 0." / "48 saat veya daha az, ama
  24 saatten fazla kaldıysa: bir günlük ücret (`price.dailyRate`)."
- **Acceptance:** evidence of a cancellation with exactly 48 h left and fee 0,
  with the expected fee (one daily rate) stated.
- **Discriminator:** 47 h 59 min 59 s → one daily rate; 48 h 0 min 1 s → 0;
  exactly 24 h → two daily rates; the cap at `price.subtotal` works. Every
  "round" test (3 days ahead, tomorrow, in 30 hours) is correct.
- Severity Medium · Medium · **6 points**

### K5 — Young-driver fee uses the driver's age "today"
- **What:** the under-25 test of `youngDriverFee` uses the age on 2026-03-10
  (server clock), not on the pick-up day. A driver whose 25th birthday lies
  between "now" and the pick-up day is charged 200 TL per day.
  Canonical: `driverBirthDate` 2001-03-15, `pickupAt` 2026-03-20 → fee 400 for
  2 days (contract: 0). Visible in the seed too: `rez_1005` (driver born
  2001-03-20, pick-up 2026-03-21) carries `youngDriverFee` 400.
- **Contract:** section 8.6 "sürücü alış gününde 25 yaşını doldurmamışsa günlük
  200,00 TL"; section 9 "Sürücünün yaşı … alış anının (`pickupAt`) Türkiye saatine göre
  takvim gününde ("alış günü") hesaplanır".
- **Acceptance:** a quote, reservation or the seed record `rez_1005` where the
  driver is 25 or older on the pick-up day and `youngDriverFee` > 0, with both
  dates shown.
- **Discriminator:** the minimum age (21) and the licence age ARE evaluated on
  the pick-up day; drivers who are under 25 on both days and drivers who are
  25 on both days are priced correctly.
- Severity Medium · Medium · **6 points**

### K6 — BAHAR15 stays "used" after the reservation is cancelled
- **What:** the single-use check counts cancelled reservations.
  (a) Seed: `mus_2`'s only BAHAR15 reservation is `rez_1010` (cancelled), yet any
  quote or reservation of `mus_2` with BAHAR15 (3 days or more) → 422
  `COUPON_ALREADY_USED`.
  (b) Sequence: `mus_1` creates with BAHAR15 → cancels → next BAHAR15 request →
  422 `COUPON_ALREADY_USED`.
- **Contract:** section 8.4 "Her müşteri bu kuponu en fazla BİR rezervasyonda
  kullanabilir; `cancelled` durumundaki rezervasyonlar bu sayıma girmez."
- **Acceptance:** `COUPON_ALREADY_USED` for a customer whose only BAHAR15
  reservations are cancelled, **and** the report shows that state (names
  `rez_1010` as cancelled, or shows the create → cancel → retry sequence).
- **Half (3):** reports that `mus_2` cannot use BAHAR15 as a defect or suspicion
  but does not show that the earlier use is a cancelled reservation.
- **Discriminator:** the quick conclusion for `mus_2` is "already used, fine";
  a second use without cancelling is rejected correctly; `mus_1` can use the
  coupon once.
- Severity Medium · Medium · **6 points**

### K7 — PATCH keeps the old duration-discount percentage
- **What:** `PATCH /reservations/{id}` recalculates the price with the discount
  percentage (0 / 10 / 20) that belonged to the day count at creation. Shortening
  an 8-day reservation to 3 days keeps 10% (`arc_04`: `durationDiscount` 990.00
  on a base of 9899.97, contract 0); extending 3 → 8 days gives no discount
  (contract 2639.99). The price object stays internally consistent.
- **Contract:** PATCH: "Fiyat, tüm fiyatlandırma kuralları (bölüm 8) yeni değerlere
  göre baştan uygulanarak yeniden hesaplanır; sonuç, aynı girdilerle yeni oluşturulacak
  bir rezervasyonun fiyatıyla aynıdır." and section 8.3.
- **Acceptance:** a PATCH that moves the day count across the 7-day or 14-day
  threshold (either direction) with the resulting `durationDiscount` that does
  not belong to the new day count.
- **Half (3):** shows that the price after PATCH differs from the quote / from
  a fresh reservation with the same inputs, without identifying the duration
  discount as the differing part.
- **Discriminator:** PATCH inside one tier (3 → 4 days, new extras, one-way
  change) recalculates base, extras, VAT and total correctly.
- Severity High · Hard · **6 points**

### K8 — Idempotency keys are shared between users
- **What:** the key store is global. `mus_1` creates with `Idempotency-Key: X`;
  `mus_2` sends the same key and body → **200 with `mus_1`'s reservation**
  (`customerId: mus_1`, dates, driver birth date, price). With another body
  `mus_2` gets 409 `IDEMPOTENCY_KEY_REUSED` for a key it never used.
- **Contract:** `POST /reservations`: "Anahtarlar kullanıcıya özeldir: bir kullanıcının
  kullandığı anahtar başka bir kullanıcının isteklerini etkilemez."; section 1
  (a customer sees only own reservations).
- **Acceptance:** either manifestation with both requests shown (two tokens,
  same key).
- **Discriminator:** idempotency for one user works exactly as documented
  (replay → 200 same reservation; other body → 409; failed requests do not bind
  the key).
- Severity High · Hard · **6 points**

### K9 — Return is authorised by the pick-up branch
- **What:** `POST /reservations/{id}/return` checks the staff member's branch
  against `pickupBranchId`. (a) `tok_personel_ist` → return of `rez_1002`
  (ANK → IST, active) → 403 although IST is the return branch. (b) A one-way
  rental IST → ANK can be returned by IST staff (200) although ANK is the return
  branch.
- **Contract:** return: "Personel yalnızca rezervasyonun DÖNÜŞ şubesinin
  (`returnBranchId`) personeliyse işlemi yapabilir; başka şubenin personeli 403 alır."
- **Acceptance:** either direction, with the reservation's two branches shown.
- **Discriminator:** same-branch rentals behave correctly; IST staff is blocked
  on ANK → ANK rentals (403) and on ANK pick-ups (403); IST staff can read
  `rez_1002`. Only a one-way rental shows the defect.
- Severity High · Hard · **6 points**

### K10 — `staffNote` returned to customers by PATCH / cancel
- **What:** the responses of `PATCH /reservations/{id}` and
  `POST /reservations/{id}/cancel` use the staff view. For a customer the body
  contains `staffNote` (null, or the note). `mus_1` → PATCH `rez_1004` → the
  internal note "Önceki kiralamada araç 3 saat geç iade edildi; …"; `mus_2` →
  PATCH or cancel `rez_1007` → "Ek sürücünün ehliyet fotokopisi eksik; …".
- **Contract:** `Reservation.staffNote`: "Müşteri rolüne verilen yanıtlarda bu alan
  HİÇBİR uçta yer almaz."
- **Acceptance:** the text of a staff note returned to a customer token.
- **Half (2):** shows only that the key `staffNote` (value null) is present in
  a customer's PATCH or cancel response and cites the sentence.
- **Discriminator:** `GET /reservations`, `GET /reservations/{id}`, the create
  response and the idempotent replay hide the field. Only two seed reservations
  that a customer can still change carry a note.
- Severity Medium · Hard · **5 points**

### K11 — `GET /vehicles` sorts after cutting the page
- **What:** with a `pageSize` smaller than the result, the page is cut out in
  `id` order and only then sorted. `?sort=dailyRate&order=asc&pageSize=4` as a
  customer → `arc_01, arc_02, arc_03, arc_04`; contract → `arc_07, arc_10,
  arc_01, arc_05`. `sort=id&order=desc` is affected in the same way.
- **Contract:** section 6 "Sıralama, süzülmüş sonuç kümesinin TAMAMINA uygulanır;
  sayfalama sıralanmış küme üzerinde yapılır."
- **Acceptance:** a sorted request with a small page whose page 1 is not the
  head of the globally sorted list, or pages that are not sorted when joined.
- **Discriminator:** every single page is sorted; with the default page size
  (20 ≥ 12 cars) the whole list is sorted; `GET /reservations` sorts correctly
  before paginating.
- Severity Medium · Hard · **6 points**

### K12 — `pickupFrom` / `pickupTo` use the UTC day
- **What:** `GET /reservations` compares the filter dates with the UTC date of
  `pickupAt`. Pick-ups between 00:00 and 02:59 Turkey time fall on the previous
  day. `mus_1`: `?pickupFrom=2026-03-28&pickupTo=2026-03-28` → empty (contract:
  `rez_1006`, pick-up 2026-03-28T00:45+03:00); `…=2026-03-27` → `rez_1006`.
  Same for `mus_2` / `rez_1005` (03-21 01:30).
- **Contract:** section 3 ("Takvim günü gerektiren her hesap (… tarih süzgeçleri …)
  Türkiye saatine (UTC+03:00) göre yapılır … her iki ucu da dahildir") and
  `GET /reservations` ("`pickupAt` değerinin Türkiye saatine göre takvim günü bu
  aralıkta (uçlar dahil) olan rezervasyonlar döner").
- **Acceptance:** a reservation with its `pickupAt` shown that is missing from
  the filter of its own Turkey-time day, or returned for the day before.
- **Discriminator:** daytime pick-ups filter correctly; wide ranges are correct;
  `issuedFrom` / `issuedTo` of invoices and the report range are correct.
- Severity Medium · Hard · **5 points**

### K13 — Revenue report counts `void` invoices
- **What:** `GET /reports/revenue` ignores the invoice status. February 2026:
  the IST row is 3 invoices / 17510.00 / 3502.00 / 21012.00; contract: 2 /
  8730.00 / 1746.00 / 10476.00 (`fat_5005` is void). With `branchId=IST` the
  same. `totals` are consistent with the wrong rows.
- **Contract:** report: "Rapora yalnızca durumu `issued` olan faturalar girer; `void`
  faturalar hiçbir koşulda dahil edilmez."
- **Acceptance:** report figures compared with the invoices, naming the void
  invoice (`fat_5005`) as counted.
- **Half (3):** shows that the report does not equal the sum of the issued
  invoices for IST / February without identifying the void invoice.
- **Discriminator:** the report equals the sum of **all** listed invoices, rows
  add up to `totals`, and any period without a void invoice (for example March)
  is correct.
- Severity High · Hard · **6 points**

### K14 — Late-fee cap is one daily rate also after 24 hours
- **What:** the cap of the late fee is always one daily rate. A car returned
  26 hours late on `arc_11` is invoiced `gecikme` 1675.50; contract:
  min(26 × 167.55, ceil(26 / 24) × 1675.50) = 3351.00.
- **Contract:** return: "Bedel, gecikmenin her başlayan 24 saati için bir günlük ücreti
  aşamaz: üst sınır = `ceil(gecikme / 24 saat) × dailyRate`."
- **Acceptance:** an invoice of a return more than 24 hours late whose `gecikme`
  line is one daily rate, with the expected amount stated.
- **Discriminator:** both worked examples of the contract are correct (2 h
  10 min → 30%; 14 h → one daily rate), exactly 60 minutes is free, the seed
  invoice `fat_5003` (3 h late) is correct.
- Severity Medium · Hard · **6 points**

### K15 — `active` reservations do not block the car
- **What:** the availability check of `POST /quotes`, `POST /reservations` and
  `PATCH` looks only at `confirmed` reservations. A car that is out on rental
  can be booked for the same time: `arc_02` 2026-03-10 12:00 → 03-12 12:00
  (inside active `rez_1001`) → 200/201. Same for `arc_08` (`rez_1002`),
  `arc_09` (`rez_1003`) and any reservation after its pick-up.
- **Contract:** section 7.2 "`confirmed` veya `active` durumundaki her rezervasyon
  aracı bloke eder."
- **Acceptance:** a quote, reservation or PATCH accepted for a period that
  overlaps an `active` reservation of the same car (reservation id or pick-up
  step shown).
- **Half (3):** shows that `GET /vehicles?availableFrom&availableTo` does not
  offer a car which quote / create accepts for the same period, without
  identifying the `active` reservation as the cause.
- **Discriminator:** overlap with a `confirmed` reservation → 409, including the
  2-hour buffer; `GET /vehicles` with the availability filter is correct.
- Severity Critical · Hard · **7 points**

### K16 — VAT truncated instead of rounded half-up
- **What:** `vat` = floor(20% of `subtotal`) to the kuruş, in quotes,
  reservations and invoices. It differs from the contract only when the subtotal
  in kuruş leaves remainder 3 or 4 modulo 5. That never happens for the seven
  bookable cars with round rates. It happens for `arc_04` (3299.99) on 1, 2, 6,
  7, 8, 12… days without extras, for `arc_05` (1187.45) from 7 days on or with
  `tam_koruma`, and for `arc_11` (1675.50) only with `tam_koruma`.
  Canonical: `arc_04`, 1 day: subtotal 3299.99 → `vat` 659.99, `total` 3959.98
  (contract 660.00 / 3959.99).
- **Contract:** section 8.9 "KDV (`vat`) = `subtotal` tutarının %20'si (kuruşa yarım
  yukarı yuvarlanır)"; section 4.
- **Acceptance:** an example with `subtotal`, returned `vat` and the correctly
  rounded value, attributed to the VAT rounding.
- **Half (2):** reports a 0.01 difference in `total` or `vat` against the
  tester's own calculation without attributing it to rounding of the VAT.
- **Discriminator:** the worked example of the contract and every price on a
  car with a round daily rate are exact; discounts and `tam_koruma` ARE rounded
  half-up.
- Severity Low · Hard · **5 points**

---

## Traps (T1..T7) — correct by the contract; reported under "Kusurlar" = wrong claim (−4)

| T | Looks wrong | Why it is correct (contract) |
|---|-------------|------------------------------|
| T1 | A car returned two days early is invoiced for all planned days | return: "Erken iade: ücret iadesi yapılmaz; kiralama bedeli her zaman planlanan gün sayısı (`price.days`) üzerinden faturalanır." |
| T2 | Admin (and staff) get 403 on `POST /reservations` and `POST /quotes` | "Rezervasyonu yalnızca müşteri, kendi adına oluşturur; personel ve yönetici 403 alır." / quotes: "Yalnızca müşteri çağırabilir; personel ve yönetici 403 alır." |
| T3 | The idempotent replay answers 200, not 201 | "ilk oluşturulan rezervasyon **200** ile döner (201 değil)" |
| T4 | A page after the last one answers 200 with empty `data` (not 404 / 400) | section 6 "Son sayfadan sonraki bir sayfa istenirse 200 ile boş `data` döner." |
| T5 | The car and period of a cancelled (or completed) reservation can be booked again — looks like double booking | section 7 "`cancelled` ve `completed` rezervasyonlar aracı bloke etmez; iptal edilen bir rezervasyonun aracı ve zaman aralığı yeniden kiralanabilir." |
| T6 | A valid coupon gives `couponDiscount` 0 on a long rental, stays in `couponCode`, and BAHAR15 is "used" afterwards | section 8.4 "İkisi de geçerliyse yalnızca tutarı büyük olan uygulanır, diğeri 0 olur … Kupon indirimi 0'a düşse bile `couponCode` rezervasyonda kayıtlı kalır ve BAHAR15 için kullanım hakkı harcanmış sayılır." (TURNA300 never applies from 7 days on, BAHAR15 loses from 14 days on.) |
| T7 | A one-day rental cancelled three hours before pick-up costs one daily rate, not two | cancel: "İptal ücreti hiçbir durumda rezervasyonun `price.subtotal` değerini aşamaz; aşıyorsa `price.subtotal` uygulanır." |

Related correct behaviours that follow from quoted sentences and are graded the
same way if reported as defects: 25 hours is one rental day and 60 minutes late
is free (tolerance); child seat charged for at most 7 days and young-driver fee
for at most 10; `tam_koruma` removes the damage line; staff of IST can read a
rental picked up in ANK that returns to IST; that staff member cannot read its
invoice (invoices belong to the pick-up branch); `maintenance` cars are listed
to customers and answer 409 `VEHICLE_OUT_OF_SERVICE`; staff gets 403 on PATCH
and cancel; a rental picked up late is billed from the planned time.

---

## Contract-silent behaviours (S1..S14)

The contract says nothing about these. Under "Açık sorular ve gözlemler" they
cost nothing. Under "Kusurlar" with an expected result the contract does not
state they are an *invented rule* (−2 each). The verifier checks each one.

| S | Behaviour of the server | Expectation a tester might invent |
|---|-------------------------|-----------------------------------|
| S1 | Role and branch checks (403) run before the body is validated (400). Staff → `POST /quotes` with broken JSON → 403. | "400 must come first" |
| S2 | Body validation (400) runs before the state check (409) and the business rules. When several business rules are broken, one error is returned in this fixed order: vehicle not found (404) → out of service (409) → `INVALID_PERIOD` → `PICKUP_TOO_SOON` → `PICKUP_TOO_FAR` → `RENTAL_TOO_LONG` → `DRIVER_TOO_YOUNG` → `LICENSE_TOO_NEW` → coupon errors (`INVALID`, `NOT_APPLICABLE`, `ALREADY_USED`) → `VEHICLE_ALREADY_BOOKED`. | a different order, or all errors at once |
| S3 | Driver data is not checked for plausibility: no maximum age, `licenseIssuedOn` may be earlier than `driverBirthDate`. | "licence before 18 must be rejected", "age limit 75" |
| S4 | One customer may hold reservations for different cars in the same period. | "a customer cannot rent two cars at once" |
| S5 | Coupon codes are case-sensitive (`bahar15` → 422 `COUPON_INVALID`); an empty string is an unknown code (422 `COUPON_INVALID`), `null` or a missing field means no coupon. | "codes must be case-insensitive", "empty string = no coupon / 400" |
| S6 | Unknown path → 404 `NOT_FOUND`; known path with another method (PUT, DELETE, HEAD, OPTIONS) → 405 `METHOD_NOT_ALLOWED` with an `Allow` header; unknown path without token → 401. The contract never mentions 405. | "must be 404", "must be 405", "OPTIONS must work" |
| S7 | `Content-Type` is not checked; a JSON body sent as `text/plain` or without the header is processed. No 415. | "415 for a wrong content type" |
| S8 | Unknown query parameters are ignored; of a repeated parameter the first value is used; `vehicleId=<unknown>` gives an empty list. | "unknown parameter must be 400" |
| S9 | An idempotent replay returns the reservation in its **current** state (after PATCH or cancel), not a stored copy of the first response. "Same body" is compared by meaning: the same instant in another offset, extras in another order and spelled-out defaults are the same body. | "replay must return the original response byte for byte" |
| S10 | `pickedUpAt` and `returnedAt` are not compared with the simulated clock; they may lie after "now", and there is no upper limit for a late return. | "a hand-over in the future must be rejected" |
| S11 | Odometer and fuel continuity between rentals is not checked (a car may be handed over at a lower reading than its last return), and a one-way rental does not move the car to the other branch in `GET /vehicles`. | "odometer must not go backwards", "the car must now be in the other branch" |
| S12 | A late return that runs into the next reservation of the same car is accepted; the next reservation is not changed. | "the next reservation must be flagged / moved" |
| S13 | A body sent to `POST …/cancel` is ignored, valid JSON or not. | "must be 400" |
| S14 | `note: ""` is stored as an empty `staffNote` (there is no `minLength`); a missing `note` leaves the old note. | "empty note must be rejected / ignored" |

Not observable in this environment (so it cannot be reported with evidence):
anniversaries of 29 February in a non-leap year. Every pick-up day is between
2026-03-10 and 2026-06-08.

Also silent, and equally "invented rule" when filed as defects with an invented
expectation: missing security headers, CORS, rate limiting, static tokens that
never expire, sequential ids, no `Location` header on 201, HTML or script text
stored in a note, no handling of a customer who never shows up, error messages
being Turkish text.

---

## Scoring rubric (max 100)

1. **Detection (88 points).** Award each K's points when its acceptance rule is
   met with concrete evidence under "Kusurlar". Award half (rounded down) only
   in the two cases named at the top of "Planted defects"; otherwise nothing.

2. **Report quality (12 points).**
   - every defect has request + token + observed response — **4**
   - every defect cites the contract statement it breaks — **4**
   - severities roughly consistent with this key (at most one level away for
     most defects) — **2**
   - defects traceable to the evidence log `test-kayitlari.md` — **2**

   The first, second and fourth part are awarded in proportion to the share of
   reported real defects (K items and unplanned real defects) that satisfy them,
   rounded to the nearest half point. Severity: 2 if at least three quarters of
   the reported K items are at most one level away from this key, 1 if at least
   half are, otherwise 0.

3. **Penalties by class.** Classify every item listed under "Kusurlar" that is
   not one of K1..K16:
   - **(a) wrong claim** — the reported behaviour does not occur, or a trap
     (T1..T7 or a related correct behaviour above) is reported as a defect:
     **−4 each**.
   - **(b) invented rule** — the behaviour occurs, the contract is silent (an S
     item or similar), and it is listed under "Kusurlar" with an expected result
     the contract does not state: **−2 each**. The same item under "Açık sorular
     ve gözlemler" costs **0**.
   - **(c) unplanned real defect** — the behaviour occurs and contradicts a
     quotable contract statement but is not in this key: no points, no penalty.
     List it under `unplanned_real` in the grading record and add it to this key
     after checking it.
   - **(d)** one root cause reported several times counts once (for points and
     for penalties).

   How to decide: reproduce the claim against a fresh server. If it does not
   reproduce → (a). If it reproduces, look for the contract sentence the report
   quotes; if the sentence says what the report claims → K or (c); if the
   contract says the opposite → (a); if there is no such sentence → (b). A claim
   that also reproduces on the reference server (`API3_PLANTED=off`) is never a
   planted defect.

4. **Final score** = detection + quality − penalties, clamped to 0..100.

Grading record (one per run), so that two graders can be compared line by line:

```json
{
  "run": "<id>",
  "detection": {"K1": 4, "K2": 0, "K6": 3, "...": 0},
  "quality": {"repro": 4, "contract_citation": 3.5, "severity": 2, "traceable": 2},
  "penalties": [
    {"item": "<title in bulgular.md>", "class": "wrong_claim", "ref": "T4", "points": -4},
    {"item": "<title>", "class": "invented_rule", "ref": "S7", "points": -2}
  ],
  "unplanned_real": [{"item": "<title>", "contract_statement": "<quote>", "verified_on_reference_server": true}],
  "duplicates_merged": ["<title> = K15"],
  "final": 0
}
```

---

## Expected difficulty (not scored)

Target: a strong agent working unaided for about 40 minutes finds roughly
55–75% of the detection points. Author's estimate per item (probability that
such a run earns the full points): K1–K3 ≈ 0.95; K4 0.65, K5 0.6, K6 0.7;
K15 0.6, K11 0.55, K8 0.55, K13 0.55, K7 0.45, K9 0.4, K16 0.45, K14 0.4,
K10 0.35, K12 0.3 → about 50–52 of 88 points with half credits (57–59%). The
estimate was not checked with agent runs. If runs land above 80%, tighten (for
example let K13 appear only with the `branchId` filter, or remove the seed
manifestations of K5 and K6); if they land below 45%, extend the time budget
before changing the trial.

**Pilot result (2026-11-18): the estimate above was wrong for the strongest model.** One unaided pilot run (Claude Fable 5.2, no time limit, 37 minutes, 4,152 requests driven by its own price oracle and scripts) reported exactly sixteen defects, one for each of K1..K16, nothing else under "Kusurlar", and 24 items under "Açık sorular ve gözlemler". The mapping was checked by title and the evidence of the hard items by sampling, not line by line; the tool calls of the run were audited and show no access outside its folder. For a model of that class the trial is at the ceiling; whether it separates weaker models, or runs with a fixed request or time budget, is not measured.

What separates runs: an independent price oracle run over all cars (K16, K5),
pushing every rule across its threshold after a state change (K7, K6, K4),
repeating each authorisation check with one-way data and with the mutation
responses (K9, K10), comparing endpoints with each other (K13, K15), and
oracle-based checks of filter + sort + page combinations (K11, K12).

---

## Verification log (performed by the trial author, 2026-11-18)

- `node server.js` on a free port + `python grade_api3.py <url>` →
  `91/91 checks behaved as designed.` Repeated after a restart: identical output.
- `API3_PLANTED=off` + `python grade_api3.py <url> --reference` → `91/91`. The
  planted verifier against the reference server fails exactly the 21 K checks,
  nothing else: each K scenario differs from the contract only by its defect.
- `python -m unittest tests.test_trial_api3` → 4 tests OK (key matches server
  and a restart gives the same output; reference server; verifier refuses a
  used server; two parallel copies are independent).
- Differential fuzz (author's scratch scripts, not in the repository): an
  independent Python model of the contract compared with the server on about
  10,000 requests per run (random quotes, creates, PATCHes, cancels, hand-overs,
  returns with invoices, all list filters / sorts / pages, the report, access by
  every role), several seeds. Reference server vs. contract model: 0 mismatches.
  Planted server vs. model with the sixteen defects switched on: 0 mismatches.
- Robustness fuzz, both modes, about 1,900 checks: null / array / string /
  number bodies, malformed and deeply nested JSON, wrong types and limits for
  every field, unknown fields, 150 kB bodies (413), wrong content types, bad
  paging and filter values, unknown ids and paths, unsupported methods, broken
  HTTP on a raw socket, every role on every operation, every form of a missing
  or wrong token. No 5xx, no crash, no hang; every error body is
  `{code, message[, details]}` without internals.
