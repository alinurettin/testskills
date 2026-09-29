# Domain pack: Fintech and banking

Use this pack in requirements analysis (completeness walk) and test design when the feature moves money, manages accounts, lending, cards, or payments. It lists **what to ask and test**, not legal advice. Confirm the regulations that apply, and their current versions, with the compliance team.

## Contents
1. Regulations and standards to check
2. Implicit requirements checklist
3. High-risk rules → test design
4. Test data (synthetic only)
5. Non-functional focus
6. Defects typically found

---

## 1. Regulations and standards to check
| Area | What it usually drives in requirements and tests |
|---|---|
| Banking regulation and IT rules (in Türkiye: BDDK regulations on information systems and electronic banking) | Authentication strength, session rules, audit trails, change control, outsourcing, business continuity |
| Payment services and e-money (in Türkiye: Law No. 6493 and TCMB regulations; in the EU: PSD2/PSD3) | Strong customer authentication, transaction limits, consent, dispute and refund flows |
| AML/CFT (in Türkiye: MASAK) | KYC at onboarding, suspicious-transaction flags, sanctions screening, record keeping |
| Personal data (KVKK / GDPR) | Consent, minimisation, masking, retention, data subject requests |
| Card data (PCI DSS v4.x) | No storage of CVV or full PAN in logs or UI, tokenisation, network segmentation (scope) |
| Instant and interbank payments (FAST, EFT, SWIFT) | Operating hours, cut-off times, amount limits (these change, so confirm the current values), status callbacks, idempotency |
| Consumer credit | Pre-contract information, APR/cost display, right of withdrawal, affordability checks |

## 2. Implicit requirements checklist
Ask each question. When the specification does not answer it, record a question or a derived requirement.
- **Limits:** per transaction, daily, monthly, per channel, per customer segment. Are they inclusive? When do they reset (calendar day in Europe/Istanbul, or a rolling 24 hours)? Is there a shared limit across channels?
- **Time:**
  - cut-off times;
  - weekends and public holidays, including half days (arife);
  - value date vs transaction date;
  - behaviour at 23:59:59 and 00:00:00;
  - the time zone of the server vs the customer.
- **Money:**
  - currency and minor units;
  - rounding mode and step (per line or per total);
  - FX rate source, timestamp and validity window;
  - fees and taxes (for example BSMV, stamp duty), and who pays them.
- **Idempotency:** a double click, a retry after a timeout, or a duplicate callback must not move money twice. Which idempotency key is used?
- **Lifecycle:** statuses such as initiated → authorised → pending → completed / failed / reversed. Cover reversal, partial refund and chargeback. What happens to a pending transaction at cut-off?
- **Consistency:** double-entry balance and end-of-day reconciliation. Is the customer-facing balance equal to the ledger balance? Does a failed transfer release the held amount?
- **Security:**
  - step-up authentication (OTP, push approval) for new payees and high amounts;
  - device binding;
  - session timeout;
  - changing a payee requires re-authentication;
  - masking of IBAN and PAN.
- **Fraud and AML:** velocity rules, unusual amounts, sanctions hits. What does the customer see, and what does operations see?
- **Notifications:** SMS/push/e-mail per event; wording; failure handling. An OTP must not leak into logs.
- **Statements and documents:** receipts (dekont), statements, legal texts shown before confirmation.

## 3. High-risk rules → test design
| Rule shape | Technique | Notes |
|---|---|---|
| Limits and amount thresholds | 3-value BVA on every limit, per channel | Include cumulative limits (the second transaction crosses the limit) |
| Fee, commission and eligibility rules | Decision table (full coverage for money rules) | Conditions: customer type, channel, amount band, currency, time window |
| Transfer, loan or card lifecycle | State transition with 1-switch plus invalid transitions | Reach states through API or seed data; assert ledger effects at each transition |
| Cut-off and holiday behaviour | BVA on time with clock control (`page.clock`) | Holiday calendar as test data; value date assertions |
| Concurrency and duplicates | Error guessing: parallel requests, duplicate callbacks | Assert exactly one ledger entry |
| Authorisation | CRUD × role; object-level checks (another customer's account ID) | OWASP ASVS V8, V6 and V7 at L2 or L3 |

## 4. Test data (synthetic only)
- **Never use real customer data.** Use synthetic identities, and test accounts supplied by the bank's test environment or the payment provider's sandbox.
- **TC Kimlik No (TCKN) validation partitions:**
  - exactly 11 digits;
  - the first digit is not 0;
  - the 10th digit = ((sum of digits 1, 3, 5, 7, 9) × 7 − (sum of digits 2, 4, 6, 8)) mod 10;
  - the 11th digit = (sum of the first 10 digits) mod 10.

  Test valid, wrong length, first digit 0, wrong 10th digit, wrong 11th digit, non-numeric, and empty. Take valid synthetic values from the test environment's designated data, not from the internet.
- **IBAN (TR):**
  - 26 characters: `TR` + 2 check digits + 5-digit bank code + 1 reserve digit + 16-character account;
  - checked with mod-97;
  - test the formatting variants too (spaces, lower-case `tr`).
- **Tax number (VKN):** 10 digits with its own checksum. Test it the same way as the TCKN.
- **Cards:** only the payment provider's published test card numbers, and only in its sandbox.

## 5. Non-functional focus
- **Performance:** peaks on salary days, month and year end, and campaign days. Set thresholds per critical API.
- **Availability and recovery:** RTO and RPO; behaviour during partial outages (core banking down → a graceful message, no money moved).
- **Security:** ASVS L2 as the minimum, L3 for high-value flows. Audit and logging (V16). Data protection (V14).
- **Accessibility:** banking is in scope of the European Accessibility Act in the EU. Test OTP and timeout flows against WCAG 2.2.2.1 and 3.3.8.

## 6. Defects typically found
- Limits checked per request but not cumulatively, or bypassed through another channel or the API.
- Rounding differs between the UI, the receipt and the ledger by 1 kuruş.
- A retry after a timeout creates a duplicate transfer.
- A pending transaction at cut-off is shown as completed.
- Another customer's account or transaction is reachable by changing its ID.
- An OTP or PAN appears in logs, analytics or error messages.
