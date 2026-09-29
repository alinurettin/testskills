# Domain pack: Insurance and pensions

Use this pack in requirements analysis (completeness walk) and test design when the feature quotes, sells, renews or services policies, handles claims, or manages pension contracts. It lists **what to ask and test**, not legal or actuarial advice. Confirm the regulations that apply, their current versions, and every tariff or rate with the compliance and actuarial teams.

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
| Insurance law and supervision (in Türkiye: Insurance Law No. 5684, supervised by SEDDK; in the EU: Solvency II and national law) | Product approval, pre-contract information, cancellation and refund rules, complaint handling, reporting |
| Distribution (in the EU: the Insurance Distribution Directive, IDD) | Demands-and-needs test, suitability for investment-based products, product information documents, commission disclosure |
| Compulsory products (in Türkiye: traffic liability insurance, DASK earthquake insurance) | Regulated tariffs, caps and step systems (confirm the current values), mandatory data exchange with central systems, policy-before-registration rules |
| Central data exchange (in Türkiye: SBM, the insurance information and monitoring centre) | Querying claim history and no-claims steps, policy registration, handling of timeouts and mismatches |
| Private pensions (in Türkiye: Law No. 4632 BES and auto-enrolment OKS) | Contribution and state-contribution rules, vesting periods, fund switches per year, transfers between companies, opt-out windows |
| Accounting (IFRS 17) | Premium recognition, contract boundaries, reporting data; usually tested in finance systems |
| Personal and health data (KVKK / GDPR; special-category data) | Explicit consent for health data, minimisation, retention after claims, access control for medical documents |
| Operational resilience (in the EU: DORA, applies to insurers from 2025) | ICT incident handling, third-party risk, resilience testing |

## 2. Implicit requirements checklist
Ask each question. When the specification does not answer it, record a question or a derived requirement.
- **Rating and quoting:**
  - Which factors price the policy (age, region, vehicle, sum insured, deductible, no-claims step, occupation)? Where does each factor's value come from?
  - Are age and dates evaluated on the quote date, the start date or the birth date? What about a quote that crosses a birthday or a tariff change date?
  - Rounding of premium, taxes and fees: per instalment or per total?
  - How long is a quote valid? What happens when a factor changes after the quote?
- **Policy lifecycle:** quote → proposal → issued → active → endorsed → renewed / lapsed / cancelled / reinstated. Which transitions are allowed, and who may trigger them?
- **Endorsements (zeyil):** mid-term changes (address, vehicle, sum insured, insured persons). Pro-rata premium on the exact day count; refund or additional premium; effective date in the past?
- **Cancellation and refunds:** cancellation by the customer, by the insurer, for non-payment, for sale of the vehicle; short-rate vs pro-rata refund; the cooling-off period.
- **Instalments and payment:** number of instalments per product, failed instalment handling, grace period, automatic lapse, reinstatement conditions.
- **Claims:**
  - First notice of loss (FNOL) channels; mandatory documents per claim type;
  - coverage check on the loss date (was the policy active, was the peril covered, waiting periods);
  - deductible and limit application, per event and per year;
  - reserve setting, partial payments, subrogation, fraud flags, rejection with reasons.
- **Time:** policies often start and end at noon or midnight; time zone; leap years in day counts; renewals on 29 February.
- **Documents:** policy schedule, general and special conditions, information forms that must be shown and accepted before sale; versioning of those texts.
- **Pensions:** contribution collection dates, state contribution rules and caps, fund allocation totals of exactly 100%, switch limits per year, vesting on exit.

## 3. High-risk rules → test design
| Rule shape | Technique | Notes |
|---|---|---|
| Premium calculation with many factors | Decision table for eligibility and loadings; pairwise for factor combinations; **reference calculations** from the actuarial team as the oracle | Never re-derive the tariff in the test; compare with an approved calculator or table |
| Factor bands (age, sum insured, engine power) | 3-value BVA on every band edge | Include the date the age is evaluated on |
| Policy and claim lifecycle | State transition with 1-switch plus invalid transitions | Endorse a cancelled policy? Pay a claim on a lapsed policy? |
| Pro-rata and short-rate refunds | BVA on day counts (day 0, 1, cooling-off end, mid-term, last day), leap year | Compare with a worked example signed off by finance |
| Coverage on the loss date | Decision table: policy status × peril × waiting period × location | Loss date just before start, at start, just after end |
| Deductibles and limits | BVA around deductible and limit; cumulative per year | The second claim crosses the annual limit |
| Integration with central systems | Error guessing: timeouts, duplicates, mismatched data | The policy must not be issued as valid when registration failed |

## 4. Test data (synthetic only)
- **Never use real policyholder or claim data.** Health and claim documents are special-category data. Use synthetic identities and the central systems' test environments.
- **Identity numbers** (TCKN, VKN) and **IBAN**: use the validation partitions of the fintech pack (checksum rules). Generate them synthetically and keep them in test systems.
- **Vehicles:** plate formats per province code (01–81), chassis number (VIN, 17 characters, no I, O or Q), engine power and model year at the band edges.
- **Dates:** birthdays on the quote date, 29 February, policies crossing a tariff change, a loss date at the exact start and end time.
- **Tariffs:** freeze a tariff version for the test cycle and record it with the results. A tariff update changes every expected premium.

## 5. Non-functional focus
- **Performance:** renewal batches at month end, campaign quotes, catastrophe events (an earthquake or flood produces a claims peak within hours).
- **Accuracy and auditability:** every quoted premium must be reproducible from the stored factors and the tariff version. Test that the audit trail contains them.
- **Security:** object-level authorisation between agents, brokers and customers; access to medical documents on a need-to-know basis; ASVS L2 as the minimum.
- **Availability:** quoting integrations (central systems, payment) down → a clear message, no policy issued without payment or registration.
- **Accessibility:** long pre-contract documents and forms must be usable with a screen reader, and the time limits must be adjustable (WCAG 2.2.1).

## 6. Defects typically found
- Age or band evaluated on the wrong date, so the premium jumps a band.
- Pro-rata refund off by one day, or leap years ignored.
- An endorsement on a cancelled or lapsed policy is accepted.
- A claim is paid for a loss before the start date or during a waiting period.
- The annual limit is checked per claim, not cumulatively.
- A policy is shown as active although payment or central registration failed.
- Instalment totals differ from the annual premium by rounding.
- Agents can see policies of other agencies by changing an ID.
