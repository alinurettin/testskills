# KEY: trial-exploratory (Perdeaçık Bilet exploratory testing)

CONFIDENTIAL. Do not show this file to the agent under test.

- Trial folder: `C:\projeler\TestSkills\evals\trial-exploratory\`
- The agent receives `TASK.md` and `urun-notu.md` only. The deliverable is `kesif-raporu.md`, with optional evidence in `kanitlar/`.
- System under test: a hash-routed SPA plus JSON API (`app/server.js`, `app/public/app.js`), served on `PORT` (default 4310). Seed data and API are described in `RUN.md`.
- 9 planted defects (K1–K9) and 4 traps (T1–T4). All were executed and verified on 2026-09-30 with Node 24.19.0, Chromium, and Windows 11. See "Verification record" at the end.

## Grading principles

1. Credit a K item only when the report's description meets that item's **acceptance rule**, in any section of the report. Wording and language do not matter; substance does.
2. **Full credit** requires reproducible steps: concrete inputs and actions a grader could follow. If the symptom is described correctly but without usable steps, or only in the "Sorular ve gözlemler" section or the debrief, award **half credit**.
3. When one report entry legitimately covers two K items, for example a K4→K6 chain (refresh checkout, submit, stack trace), credit each item whose acceptance rule is met. Count the same K item only once, however many entries mention it.
4. Reading `/app.js` in the browser (view-source or network) is allowed, since it is client code a black-box tester can see. Credit still requires a behavioural reproduction. If the transcript shows the agent read `server.js` or the key from the file system, flag the run as **contaminated**.
5. Severity labels are not scored, but a planted item must not be dismissed as "by design" in the report.

---

## Planted defects

### K1: Search fails on Turkish İ/I/ı case folding (Turkish characters) · Severity: Medium · Difficulty: hard · 4 pts

- **What:** The list search lowercases the query and the text with locale-unaware `toLowerCase()`. `"İ".toLowerCase()` is `"i̇"` (i + U+0307 combining dot), so:
  - `istanbul` → 0 results (should be 3: 101, 102, 109)
  - `izmir` → 0 results (should be 2: 104, 108)
  - `ISTANBUL` → 0 results
  - `BOĞAZİÇİ` → 0 results, while `boğaziçi` → 1 result
  - `İstanbul` → 3 results and `İzmir` → 2 results, which is correct.
- **Why it matters:** Turkish users routinely type lowercase `i` or have no `İ` on their keyboard. Discovery fails for the two largest cities, and users see "Aramanızla eşleşen etkinlik bulunamadı." as if there were no events.
- **Repro:** Etkinlikler → Ara field: type `istanbul` → "Aramanızla eşleşen etkinlik bulunamadı."; type `İstanbul` → "3 etkinlik listeleniyor."
- **Acceptance (full):** The report gives a concrete query that differs from a working one only in İ/i/I/ı casing and returns fewer or no results, for example `istanbul`, `izmir`, `ISTANBUL`, `IZMIR`, `BOĞAZİÇİ` or `İSTANBUL`-style uppercase variants.
- **Half:** "Search doesn't handle Turkish characters / is case-sensitive" with no concrete failing query.
- **Not credited:** Complaints that search is not diacritic-insensitive, such as `cello` not finding "Çello" or `sisli`. That is a neutral feature request (see N2). A claim that A–Z sorting is wrong is a false positive, because sorting uses Turkish collation correctly.

### K2: Event list shows stale seat counts after an order or cancellation · Severity: Medium · Difficulty: medium · 3 pts

- **What:** The event list is fetched once per page load and cached in the SPA. After placing or cancelling an order and returning to "Etkinlikler" (nav link, back link, or Back button), the cards still show the old "Kalan: N koltuk", including for an event that has since sold out. The detail page and the API show the correct value. Only a full reload (F5) refreshes the list.
- **Why it matters:** Users see wrong availability, and data is inconsistent across views. A sold-out event can look buyable in the list.
- **Repro:** Open the app. "Çello ve Piyano Resitali" shows Kalan 52. Buy 2 tickets for it, click "Etkinlikler": the list still says 52. Open the event: the detail says 50.
- **Acceptance (full):** The report states that the list's remaining-seat or availability numbers do not update after an order or cancellation in the same session, or that they disagree with the detail page or API until a reload.
- **Half:** "List does not refresh / shows old data" without saying what is stale.

### K3: Double submit creates duplicate orders · Severity: High · Difficulty: medium · 3 pts

- **What:** "Siparişi tamamla" stays enabled while the server processes the order (about 0.7 s of artificial delay), and neither client nor server guards against duplicates. A double-click, two quick clicks, or Enter pressed twice creates two orders with different PNRs, deducts seats twice, and shows both in Biletlerim.
- **Why it matters:** Customers are double-booked and double-charged at the box office, and inventory is wrong.
- **Repro:** Pick any event with quantity 1 → Devam et → fill the form (for example "Deniz İşcan", `deniz@example.com`, `0532 111 22 33`, tick the consent box) → **double-click** "Siparişi tamamla" → Biletlerim with that e-mail lists 2 identical "Aktif" orders.
- **Acceptance (full):** The report shows that one checkout action (double-click, rapid repeated click or Enter, or two submits before navigation) produces two or more orders.
- **Half:** Reports only that the button is not disabled or has no loading state during submission, without showing duplicates; or shows that two identical concurrent API POSTs create two orders, framed as missing duplicate protection but not tied to the UI.

### K4: Checkout without cart state shows "undefined"/"NaN TL" and is still submittable (refresh / Back / direct URL) · Severity: Medium · Difficulty: easy · 2 pts

- **What:** The cart lives only in JS memory. Pressing F5 on `#/odeme`, opening `#/odeme` directly, or pressing browser **Back** after a completed order (the cart is cleared on success) renders the summary as `undefined`, `undefined × Tam bilet (NaN TL)`, `Hizmet bedeli (undefined × 12,50 TL) NaN TL`, `Ödenecek toplam NaN TL`. The form can still be submitted, which leads to a 500 error (see K6). There is no redirect or "sepetiniz boş" message.
- **Why it matters:** A user who refreshes loses the selection and sees a broken page. The Back button after an order leads to a broken, submittable form.
- **Repro:** Detail → Devam et → F5 on the checkout page → summary shows undefined/NaN. Or: complete an order → browser Back → same result.
- **Acceptance (full):** The report shows that refresh, Back after an order, or a direct URL to checkout leaves the checkout with lost selection and undefined, NaN or empty values, or lets the user submit without a selection.

### K5: Invalid quantities accepted (0, negative, blank; >6 through the API) · Severity: High · Difficulty: medium · 3 pts

- **What:** The detail page checks only `adet > 6` and `adet > kalan`. Quantity `0`, a negative number (for example `-2`), or blank/non-numeric input (sent as 0) goes through to checkout, and the server accepts it:
  - 0 tickets gives a 0,00 TL order.
  - -2 gives "-2 × Tam", total -465,00 TL on Çello, a PNR, and **increases** the available seats by 2.
  - The server has no range check at all: POST with `adet: 7` (or 100) is accepted.
- **Why it matters:** This produces negative or zero orders, corrupts inventory, and violates the "en az 1, en fazla 6" rule from the product note.
- **Repro:** Çello detail → Bilet adedi `-2` → summary shows -465,00 TL → Devam et → complete the form → confirmation page shows "-2 × Tam" and "-465,00 TL".
- **Acceptance (full):** Any of the following: the UI lets checkout proceed with a quantity of 0, a negative number, or blank; an order is created with such a quantity; or the API accepts an order with quantity ≤ 0 or > 6.
- **Not credited as K5:** The UI rejecting 7 with "Bir siparişte en fazla 6 bilet alınabilir." That is correct behaviour (T4).

### K6: Server errors leak stack traces and internal paths to the user · Severity: High (information disclosure) · Difficulty: medium · 3 pts

- **What:** Unhandled exceptions return HTTP 500 `{hata: "Beklenmeyen bir hata oluştu: <message>", detay: <err.stack>}`. The checkout page renders both, with an open "Teknik ayrıntı" `<pre>` showing function names, the absolute server path (`...\app\server.js:LINE:COL`), and Node internals. Triggers:
  - (a) A phone number containing ≥ 10 digits plus dashes, parentheses, dots or letters, for example `0532-111-22-33`, `(0532) 111 22 33` or `0532.111.22.33`, gives `SyntaxError: Cannot convert 0532-111-22-33 to a BigInt at telefonNormalEt (...server.js...)`. The client accepts the format because it only counts digits, so this is also a functional failure for a common phone format.
  - (b) Submitting from a broken checkout (K4), or POST `/api/siparisler` without a valid `etkinlikId`, gives `TypeError: Cannot read properties of undefined (reading 'tarih') at siparisOlustur (...server.js...)`.
- **Why it matters:** This is OWASP-style information exposure (stack, paths, implementation details) and a bad user experience. A legitimate phone format also blocks purchase.
- **Acceptance (full):** The report describes or quotes an error shown to the user or returned by the API that exposes a stack trace, file path, or internal exception or function names (BigInt, TypeError, `server.js`, `siparisOlustur`, and so on).
- **Half:** Reports only that a phone with dashes or parentheses fails with an unexpected or server error, without noting the disclosure.

### K7: 24-hour cancellation rule not enforced (limit is effectively 24 minutes) · Severity: High (business rule / revenue) · Difficulty: hard · 4 pts

- **What:** The server's cancellation limit constant is `24 * 60 * 1000` ms, which is 24 minutes, not 24 hours. Orders for events less than 24 h away can be cancelled, and seats return to sale. Seeded near events: 101 "Boğaziçi Caz Gecesi", 3–14.5 h after server start, labelled "Bugün, …" or "Yarın, …"; and 102 "İstanbul Gençlik Senfonisi: Mevsimler", 11.5–23 h after server start.
- **Why it matters:** The product note says cancellation is allowed only when more than 24 h remain. Late cancellations empty seats that can no longer be resold, which costs revenue.
- **Repro:** Buy 1 ticket for "Boğaziçi Caz Gecesi" (shows "Bugün/Yarın, HH:MM") → Biletlerim → "İptal et" → "Evet, iptal et" → "…siparişiniz iptal edildi. Koltuklar yeniden satışa açıldı." and status "İptal edildi".
- **Acceptance (full):** The report shows a successful cancellation of an order for an event less than 24 h away and cites the 24-hour rule.
- **Half:** Notes that the "İptal et" button is offered for an event less than 24 h away but did not confirm that the cancellation succeeds.

### K8: Ticket type selector (Tam / Öğrenci) not keyboard or screen-reader accessible · Severity: Medium (WCAG 2.1.1, 4.1.2) · Difficulty: medium · 3 pts

- **What:** The two ticket-type options on the detail page are plain `<div class="chip">` elements with click handlers. They have no tabindex, role (radio/button), `aria-checked`/`aria-pressed`, or key handlers. The Tab order is "← Tüm etkinlikler" → Bilet adedi → Devam et, so the chips are skipped. A keyboard-only user cannot choose "Öğrenci", and assistive tech exposes the chips as generic text with no selected state.
- **Why it matters:** The product note sets a WCAG 2.1 AA target. Keyboard and screen-reader users are blocked from the student discount.
- **Repro:** Open any available event → press Tab repeatedly from the top of the content → focus never lands on "Tam" or "Öğrenci", and Enter/Space/arrow keys cannot change the type. An accessibility tree or axe scan shows the chips as generic, not radio or button.
- **Acceptance (full):** The report states that the ticket-type (Tam/Öğrenci) choice cannot be reached or operated by keyboard, or lacks an accessible role or state.
- **Half:** A generic statement that "some controls are not keyboard accessible" without identifying the ticket-type selector.

### K9: Money amounts are raw floating point in Biletlerim and the API (rounding/format), with a 1-kuruş mismatch between views · Severity: Medium · Difficulty: easy · 2 pts

- **What:** The server computes totals in binary floating point and never rounds to kuruş. Biletlerim prints the raw number with only `.` replaced by `,`. Examples:
  - 1 × Öğrenci 149,90: `132,42000000000002 TL`
  - 3 × Tam 149,90: `487,20000000000005 TL`
  - 1 × Tam 149,90: `162,4 TL` (missing trailing zero)
  - Amounts ≥ 1000 have no thousands separator, for example `1627,5 TL`.
  - The API returns values such as `"toplam": 433.47600000000006`.
  - For 3 × Öğrenci on "İzmir Kordon Akustik" (164,99), checkout shows **433,47 TL** (the client computes in kuruş), but the confirmation page shows **433,48 TL** because it rounds the server's float.
- **Why it matters:** The product note requires two decimals in Turkish format. The customer sees garbage amounts, and the amount owed differs between screens.
- **Repro:** Order 1 × Öğrenci for "Boğaziçi Caz Gecesi" → Biletlerim → Tutar `132,42000000000002 TL`.
- **Acceptance (full):** The report shows any amount with float artifacts, or not in 2-decimal Turkish format, in Biletlerim or the API, or a 1-kuruş mismatch between checkout and confirmation or Biletlerim.

---

## Traps (correct behaviour; reporting as a defect is a false positive)

### T1: Student discount does not apply to the service fee
2 × Öğrenci on Çello (220,00) = 2 × 176,00 + 2 × 12,50 = **377,00 TL**. 1 × Öğrenci 149,90 = 119,92 + 12,50 = 132,42. The product note states the fee is not discounted. **FP** if reported as "öğrenci indirimi toplamın tamamına uygulanmıyor" or "hizmet bedeli indirimsiz". Asking in "Sorular" is fine.

### T2: PERDE50 rules
- The code is rejected when the total including fees is below 300,00, with "Bu kod 300,00 TL ve üzeri siparişlerde geçerlidir." (HTTP 422, also visible as a console error).
- It is case-insensitive (`perde50` works).
- Exactly 300,00 is accepted: 2 × Ankara Stand-up = 275 + 25 = 300,00 → 250,00.
- Unknown codes give "Kampanya kodu geçersiz."

**FP** if reported as "kampanya kodu çalışmıyor" based on a sub-300 order, as the 422 console entry being a bug, or as "the threshold should exclude the service fee".

### T3: Cancelled orders remain in Biletlerim as "İptal edildi"
- A cancelled order stays in the list with status "İptal edildi" and no cancel button.
- Its seats return: the detail page and API show the count increased.
- Cancelling again returns "Bu sipariş zaten iptal edilmiş."

All of this is specified in the product note. **FP** if reported as "iptal edilen sipariş listeden silinmiyor". A report that the *list page* does not show the returned seats is K2, not an FP.

### T4: Quantity and availability limits working as designed
- The UI rejects 7 tickets with "Bir siparişte en fazla 6 bilet alınabilir."
- The limit is **per order**, so several separate orders by the same e-mail are allowed.
- "Şebnem'in Düğünü" has 3 seats left, and ordering 4 is refused with "…yeterli koltuk yok (kalan: 3)".
- "Zeybek ve Ege Ezgileri" is sold out: the button is disabled and shows "Tükendi".

**FP** if reported as "6 bilet sınırı iki ayrı siparişle aşılabiliyor", "7 bilet alınamıyor", or "tükenen etkinliğe bilet alınamıyor". Duplicate orders from a *single* double-click are K3, not T4.

## Neutral observations (no points, no penalty)

These are real but unplanted, or debatable. Do not penalise them and do not credit them as K items.

- N1: No authentication. Anyone who knows an e-mail can list and cancel its orders, and PNR lookup by URL is open. This is a privacy/IDOR risk, and noting it is a good risk comment.
- N2: Search is not diacritic-insensitive (`cello` does not find "Çello").
- N3: Contact form data is not kept when navigating away. The promo code must be re-applied after going back to the detail page.
- N4: No rate limiting, CSRF protection, or security headers.
- N5: A phone number without a leading 0, or with +90, is accepted. Names with digits or fewer than 3 letters are rejected.
- N6: Near-event times are generated relative to server start, so times can look arbitrary.
- N7: Console shows 4xx/5xx network errors. The 5xx ones relate to K6, the 422 to T2.
- N8: Visual or UX suggestions (layout, colours, copy).

## Other false positives

Any claimed defect that is not reproducible, or that contradicts the product note or the behaviour described above, counts as a generic FP. Examples: "A–Z sort is wrong for Ç/İ/Ö/Ş/Ü" (the Turkish collation is correct), or "Öğrenci price 131,99 should be 131,992".

## Scoring rubric

| Component | Points |
|---|---|
| K1 | 4 |
| K2 | 3 |
| K3 | 3 |
| K4 | 2 |
| K5 | 3 |
| K6 | 3 |
| K7 | 4 |
| K8 | 3 |
| K9 | 2 |
| **Defect subtotal** | **27** |
| S1: `kesif-raporu.md` exists in the workspace | gate: if missing, the whole score is 0 |
| S2: Session notes include at least one explicit charter and timestamped notes | 1 |
| S3: At least 80% of bug entries have steps + expected + actual | 1 |
| S4: Every bug entry has a severity (Kritik/Yüksek/Orta/Düşük or equivalent) | 1 |
| S5: Debrief covers what was covered, what was not covered, top risks, and a release recommendation | 1 |
| **Maximum** | **31** |

**Partial credit:** Half of the item's points, per the rules above.

**Penalties:**
- **−2** for each trap (T1–T4) reported as a confirmed defect in the bug list.
- **−1** for each other false positive in the bug list (not reproducible, or correct per the product note or this key).

Items placed only in "Sorular ve gözlemler" are never penalised. The final score is floored at 0.

**Objective metrics to record per run:**
- `found_full`: number of K items with full credit.
- `found_any`: number of K items with full or half credit.
- `points_K`: points from K items.
- `fp_traps`: number of trap false positives.
- `fp_other`: number of other false positives.
- `precision`: true planted or neutral-valid defects ÷ all defects in the bug list.
- `structure`: S2–S5 total.
- `total`: final score.
- `contaminated`: yes/no.

**Difficulty spread:** Easy: K4, K9. Medium: K2, K3, K5, K6, K8. Hard: K1, K7.

## Quick API reproductions (graders; bash + curl; replace 4310 with the run's port)

```bash
B=http://127.0.0.1:4310
C='"adSoyad":"Deniz Iscan","eposta":"k@example.com","kvkk":true'   # ASCII on purpose: Windows curl may mangle non-ASCII args
# K3: two identical concurrent orders both succeed (201, different PNRs)
for i in 1 2; do curl -s -X POST $B/api/siparisler -H 'Content-Type: application/json' -d "{\"etkinlikId\":103,\"tur\":\"tam\",\"adet\":2,$C,\"telefon\":\"0532 111 22 33\"}" & done; wait
# K5: negative quantity accepted (201, negative toplam)
curl -s -X POST $B/api/siparisler -H 'Content-Type: application/json' -d "{\"etkinlikId\":107,\"tur\":\"tam\",\"adet\":-2,$C,\"telefon\":\"0532 111 22 33\"}"
# K6: stack trace leak (500 with detay)
curl -s -X POST $B/api/siparisler -H 'Content-Type: application/json' -d "{\"etkinlikId\":108,\"tur\":\"tam\",\"adet\":1,$C,\"telefon\":\"0532-111-22-33\"}"
# K7: cancel an order for event 101 (<24 h away) succeeds
P=$(curl -s -X POST $B/api/siparisler -H 'Content-Type: application/json' -d "{\"etkinlikId\":101,\"tur\":\"tam\",\"adet\":1,$C,\"telefon\":\"0532 111 22 33\"}" | sed 's/.*"pnr":"\([A-Z0-9]*\)".*/\1/')
curl -s -X POST $B/api/siparisler/$P/iptal
# K9: float total
curl -s -X POST $B/api/siparisler -H 'Content-Type: application/json' -d "{\"etkinlikId\":101,\"tur\":\"ogrenci\",\"adet\":1,$C,\"telefon\":\"0532 111 22 33\"}"
```

K1, K2, K4 and K8 are UI-only. Reproduce them in a browser as described under each item.

## Verification record (2026-09-30, Node 24.19.0, Chromium via browser pane, Windows 11)

- **K1 (UI):** `istanbul` → "Aramanızla eşleşen etkinlik bulunamadı."; `İstanbul` → "3 etkinlik listeleniyor."; `izmir` → none. A–Z sort gives the correct Turkish order (Ankara…, Boğaziçi…, Çello…, İstanbul…, İzmir…, Ödüllü…, Şebnem'in…, Üsküdar…, Zeybek…).
- **K2 (UI):** After orders and a cancellation, the list showed 101 = 38 and 103 = 52 while the API showed 37 and 54.
- **K3 (UI):** A double-click on "Siparişi tamamla" produced 2 orders (5VMP7Z, SGCLS8) for `deniz@example.com`. In the API check, 2 concurrent POSTs both returned 201 and seats went from 52 to 48.
- **K4 (UI):** Back after an order, and `location.reload()` on `#/odeme`, both showed "undefined", "undefined × Tam bilet (NaN TL)" and "Ödenecek toplam NaN TL".
- **K5 (UI + API):** `-2` gave "-465,00 TL" at checkout, and the order was created with "-2 × Tam". In the API, adet 0 → 201 with toplam 0; adet -2 → 201 with toplam -300 (Ankara Stand-up); adet 7 → 201; seats changed as computed. The UI rejects 7 with the correct message.
- **K6 (UI + API):** Phone `0532-111-22-33` → 500 "Cannot convert 0532-111-22-33 to a BigInt" plus a stack with `…\app\server.js:187:10`, shown under "Teknik ayrıntı". Submitting from the broken checkout → "Cannot read properties of undefined (reading 'tarih')" at `siparisOlustur`. `(0532) 111 22 33` → 500.
- **K7 (UI + API):** Cancelled an order for "Boğaziçi Caz Gecesi" (Bugün 11:00, about 3 h ahead) through the dialog and got "İptal edildi". In the API, events 3.2 h and 14.7 h ahead were both cancelled with 200.
- **K8 (UI):** The Tab sequence on the detail page was: back link → `input#adet` → `button#devamEt` → header logo. Chips have tabIndex −1 and role null, and the accessibility tree exposes them as "generic".
- **K9 (UI + API):** Biletlerim showed `132,42000000000002 TL`. In the API, 3 × Tam 149,90 = 487.20000000000005, and 3 × Öğrenci 164,99 = 433.47600000000006 (confirmation shows 433,48; checkout showed 433,47).
- **T1–T4:** 2 × Öğrenci 220 → 377. `perde50` at 150,00 → 422 with message, at exactly 300,00 → applied (250,00). Cancelled order is listed as "İptal edildi", seats 75→73→75, second cancel → 409. Ordering 4 of 3 seats → 409; sold out → 409 and disabled button; two separate 6-ticket orders → 201 each.
- **Clean paths:** Bad JSON → 400; unknown event → 404; HTML in name → 400 (all output is escaped); missing consent → 400; invalid ticket type → 400; promo `__proto__` → 404; path traversal → 404.
- **Isolation:** Two copies on ports 4310 and 4311 ran at the same time with independent state, and a restart resets all state.
