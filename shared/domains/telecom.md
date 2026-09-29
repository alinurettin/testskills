# Domain pack: Telecommunications

Use this pack in requirements analysis (completeness walk) and test design when the feature sells or changes tariffs and bundles, rates and charges usage, bills customers, activates lines or SIMs, ports numbers, or runs self-care channels of a mobile, fixed or broadband operator. It lists **what to ask and test**, not legal advice. Confirm the regulations that apply, tax rates and their current versions with the regulatory affairs team.

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
| Electronic communications law and regulator (in Türkiye: Law No. 5809, regulated by BTK; in the EU: the European Electronic Communications Code, EECC) | Contract information, tariff transparency, contract duration and termination, consumer complaints, quality-of-service reporting |
| Subscriber identification and SIM activation (in Türkiye: BTK rules on subscriber verification, e-signature or in-store checks) | Identity verification before activation, limits per person, SIM swap and SIM replacement controls |
| Number portability | Porting windows, validation with the donor operator, rejection reasons, service continuity, rollback |
| Personal data and traffic data (KVKK / GDPR, sector rules on electronic communications data, ePrivacy in the EU) | Consent for location and traffic data use, retention periods, masking of call detail records |
| Roaming (in the EU: Roam-Like-at-Home and fair-use rules) | Zone detection, fair-use thresholds, welcome and threshold SMS, cost caps |
| Open internet / net neutrality (in the EU: the Open Internet Regulation) | Zero-rating and traffic management rules in bundles |
| Taxes (in Türkiye: special communication tax ÖİV and VAT; rates change, so confirm them) | Tax base, rounding, tax per line vs per invoice, exemptions |
| Industry standards (3GPP, TM Forum Open APIs and SID, ETSI) | Interface contracts for ordering, product catalogue, usage and billing integrations |

## 2. Implicit requirements checklist
Ask each question. When the specification does not answer it, record a question or a derived requirement.
- **Product catalogue:** which bundles can be combined, which are exclusive, and which require another product? What are the eligibility rules (segment, contract, device, credit score)?
- **Rating and charging:**
  - units and rounding (per second, per minute, per started 100 KB, per SMS part);
  - bundle consumption order when several bundles apply;
  - what happens when a bundle runs out in the middle of a session (a call, a data session);
  - real-time balance for prepaid, and the behaviour at zero balance;
  - special numbers (emergency 112 must always work, premium-rate, toll-free, international).
- **Billing:**
  - bill cycle dates and proration on activation, change and termination in the middle of a cycle;
  - discounts and campaigns with start and end dates, stacking rules;
  - commitment contracts: early termination fee and its calculation (cayma bedeli);
  - taxes, rounding, credit notes, disputes and adjustments;
  - invoice delivery (e-invoice, e-archive) and the payment channels.
- **Usage notifications:** thresholds such as 80% and 100% of a bundle, roaming welcome messages, spending caps. Are they sent once, on time, and in the customer's language?
- **Order and activation lifecycle:** order → validated → provisioned → active → suspended → terminated, including partial failures across network elements and rollback.
- **Number portability:** request, validation, scheduled port, completed, rejected, cancelled. What does the customer see at each step?
- **Self-care channels:** app, web, IVR and store must show the same balance, bundle and invoice data.
- **Fraud:** SIM swap after a password reset, subscription fraud, international revenue share fraud (IRSF), bundle abuse.

## 3. High-risk rules → test design
| Rule shape | Technique | Notes |
|---|---|---|
| Rating units and rounding | BVA on unit edges (59, 60, 61 seconds; bundle size −1, exact, +1) | Compare with rating examples signed off by the billing team |
| Bundle eligibility and combination | Decision table (full coverage for money rules), pairwise for catalogue combinations | Include exclusive and prerequisite products |
| Proration and cycle changes | BVA on dates: the first and last day of the cycle, the day of the change, month ends, leap years | Tariff change and termination on the same day |
| Order, activation and porting lifecycle | State transition with 1-switch plus invalid transitions | Partial provisioning failure must roll back or stay visible |
| Usage thresholds and caps | BVA on 80% / 100% and the cap; concurrent sessions | Exactly one notification per threshold |
| Prepaid balance | BVA at zero and at the minimum charge; concurrency (two sessions charging together) | The balance must never go negative unless allowed |
| Authorisation in self-care | CRUD × role; object-level checks (another subscriber's line or invoice) | Line owner vs user in corporate accounts |

## 4. Test data (synthetic only)
- **Never use real subscriber, traffic or location data.** Call detail records (CDRs) are personal data. Use synthetic subscribers and generated usage.
- **MSISDN:** use numbers allocated to the test environment; the format is +90 5xx xxx xx xx for mobile numbers in Türkiye. There is no reserved fictional range, so keep them in test systems.
- **Usage generation:** CDR or usage events with controlled timestamps, durations on the unit edges, roaming zones, special numbers, and bundle exhaustion in the middle of a session.
- **Identity numbers:** see the checksum partitions in the fintech pack (TCKN, VKN).
- **IMSI, ICCID, IMEI:** use the test ranges given by the network or SIM vendor. IMEI has a Luhn check digit: test valid, wrong check digit and wrong length.
- **Time:** control the clock for cycle ends, midnight, month ends, daylight-saving transitions in other countries (roaming), and campaign end dates.

## 5. Non-functional focus
- **Performance and volume:** billing runs with production-size CDR volumes; real-time charging latency; peaks on New Year's Eve, holidays, big sports events and emergencies.
- **Accuracy:** revenue assurance, where usage in equals rated usage out. Reconcile the counts and totals between network, mediation, rating and billing (see the testing-data-migrations skill for reconciliation techniques).
- **Availability:** 99.9% and higher for charging and activation; degraded modes when the online charging system is down (and whose revenue risk that is).
- **Security:** SIM swap controls, OTP delivery, self-care authorisation, API security for partner APIs (TM Forum Open APIs), ASVS L2 as the minimum.
- **Accessibility:** self-care apps and IVR menus; WCAG 2.2 for web and app; in the EU, the European Accessibility Act covers electronic communications services.

## 6. Defects typically found
- A charge rounded in the wrong direction or unit, visible only in aggregated volumes.
- Proration off by one day, or the tariff change and the termination on the same day double-charged.
- A bundle is consumed in the wrong order, so the customer pays for usage that a bundle covered.
- Threshold SMS sent twice, late or never; the roaming welcome message missing.
- Prepaid balance negative after concurrent sessions.
- An order is partially provisioned (billing active, network not), or the reverse.
- The app, web and IVR show different balances.
- Another subscriber's invoice or usage is reachable by changing the line ID.
