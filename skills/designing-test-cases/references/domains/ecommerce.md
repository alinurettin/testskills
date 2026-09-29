# Domain pack: E-commerce and marketplaces

Use this pack for catalogue, cart, campaign, checkout, payment, order, shipping and return features. It lists what to ask and test, not legal advice. Confirm current consumer-protection and tax rules with the legal team.

## Contents
1. Regulations and standards to check
2. Implicit requirements checklist
3. High-risk rules → test design
4. Test data
5. Non-functional focus
6. Defects typically found

---

## 1. Regulations and standards to check
| Area | What it usually drives |
|---|---|
| Distance contracts (in Türkiye: Mesafeli Sözleşmeler Yönetmeliği; in the EU: the Consumer Rights Directive) | Pre-information form and contract shown before payment, right of withdrawal (14 days, with exceptions), refund timelines |
| Price display and discount announcements | Prices shown with VAT (KDV) included; rules on how a "discount" may reference a previous price. Confirm the current rule. |
| Commercial electronic messages (in Türkiye: İYS) | Consent before marketing SMS/e-mail; opt-out handling |
| E-invoice and e-archive invoice | Invoice generation, cancellation and return documents |
| Payments (PCI DSS, 3-D Secure, the provider's rules) | No card data on your servers when a hosted/tokenised flow is used; 3DS challenge flows; installment rules (legal limits per product category may apply) |
| Personal data (KVKK / GDPR), cookies | Consent banner, minimisation, retention, guest vs account data |
| Accessibility (the European Accessibility Act for EU e-commerce) | WCAG 2.2 AA on the key journeys: search, product, cart, checkout |

## 2. Implicit requirements checklist
- **Price:**
  - Which price is the base for rules: list, sale, after coupon, with or without shipping and VAT?
  - What is the rounding per line vs per order?
  - What happens when the price changes between cart and checkout?
- **Campaigns and coupons:**
  - stacking and exclusivity (coupon + campaign + loyalty points);
  - minimum basket and cap;
  - eligible and excluded categories and sellers;
  - validity window (inclusive end, time zone);
  - usage per user and in total;
  - what happens to the coupon on cancellation or return.
- **Stock:** reservation timing (add to cart vs checkout vs payment); the last item bought by two users at the same time; backorder.
- **Checkout:** guest vs registered; address validation; a basket change during payment; a payment timeout; returning from 3DS; double submit.
- **Payment:** installments (eligible cards, minimum amount, campaign limits); partial authorisation; a failed payment after stock reservation; refund to the original method.
- **Orders:** the status lifecycle (created → paid → preparing → shipped → delivered / cancelled / returned); who may cancel when; partial shipment; split orders across sellers.
- **Shipping:** free-shipping threshold (calculated before or after discounts?); delivery options; tracking notifications; undeliverable addresses.
- **Returns:** the return window and its exceptions (hygiene or custom products), partial returns, refunds when a campaign was applied (proportional?), and refunds of shipping costs.
- **Search and catalogue:** Turkish-aware search (ı/i, ş/s), sorting, filters, empty results, variants (size and colour), out-of-stock display.
- **Marketplace:** seller-specific rules, commission, the seller cancelling, product and seller ratings.

## 3. High-risk rules → test design
| Rule shape | Technique |
|---|---|
| Discount, coupon and shipping thresholds | 3-value BVA on the amount thresholds and caps; decision table for stacking and exclusivity |
| Coupon and campaign eligibility | Decision table (user type × basket × category × validity × usage) |
| Order, return and refund lifecycle | State transition including invalid transitions (cancel after shipping) and partial flows |
| Checkout across browsers, devices and payment methods | Pairwise, with constraints (Apple Pay only on Safari/iOS, etc.) |
| Stock and coupon races | Error guessing with concurrency: two sessions, the same last item or the same single-use coupon |
| Price manipulation | API-level negative tests (ASVS V2): tampered price, quantity or discount in the request |

## 4. Test data
- Products that sit exactly on the thresholds (99,99 / 100,00 / 100,01 TL), categories that are and are not eligible, and products with and without stock.
- Coupons: active, expired (yesterday 23:59:59), not yet started, single-use already used, capped.
- Users: guest, new, returning, blocked; with and without İYS consent.
- The payment provider's sandbox cards, including 3DS challenge, declined and insufficient-funds cases.
- A clock control and a campaign calendar for time-bound rules.

## 5. Non-functional focus
- **Performance:** campaign peaks (11.11, Black Friday, campaign start at 00:00). Spike profile. Search and checkout p95 thresholds; stock and coupon consistency under load.
- **Reliability:** behaviour when the payment provider or the shipping API is slow or down. No lost orders and no double charges.
- **Security:** ASVS V2 (business logic), V8 (other users' orders and addresses), V3 (front end), V14 (personal data).
- **Accessibility:** WCAG 2.2 AA on search → product → cart → checkout, including the 3DS and OTP screens.

## 6. Defects typically found
- A discount applied twice through stacking, or the cap not applied on multi-item baskets.
- The free-shipping threshold is calculated before the discount, so shipping is wrongly free.
- A coupon stays applied after items are removed and the basket drops below the minimum.
- The same single-use coupon is accepted in two parallel sessions.
- A refund with a campaign applied gives back more than was paid.
- Turkish search misses "ışık" when "isik" is typed, or the other way round (requirement dependent).
