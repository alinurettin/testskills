# Implicit requirement discovery

Stakeholders state the happy path. Most defects live in what nobody wrote down. Walk the areas that apply to the feature and ask, for each question: *does the specification answer this?* If it does not, record either:
- a **derived requirement** (`"derived": true, "status": "clarification-needed"`) when a sensible default exists that the stakeholder only needs to confirm, or
- an **open question** (`Q-###`) when the answer is a real business decision.

Do not dump the whole list on the user. Choose the areas that are relevant to this feature and domain. For a small change, 3–6 areas are usually enough. Choose by risk.

## Contents
1. Inputs and validation
2. Data lifecycle (CRUD) and persistence
3. Actors, roles and permissions
4. States, workflow and concurrency
5. Errors, recovery and messages
6. Integrations and external systems
7. Time, date, money and locale
8. Lists, search and volume
9. Notifications and communication
10. Audit, logging, privacy and compliance
11. Platform, devices and environments
12. Migration, compatibility and configuration
13. Domain packs (e-commerce, finance, health, public sector)

---

## 1. Inputs and validation
- For each field: is it mandatory? What type, format, minimum and maximum length or value, allowed characters, default value?
- What happens with empty input, whitespace-only input, leading or trailing spaces, or copy-pasted text with line breaks?
- Unicode: Turkish characters (ç ğ ı İ ö ş ü), emoji, right-to-left text. Is case-insensitive comparison locale-safe? (In Turkish, "I" lowercases to "ı", not "i".)
- Numbers: decimal separator (`,` vs `.`), thousands separator, negative values, zero, leading zeros, scientific notation.
- Is validation done on the client, the server, or both? Which one is authoritative?
- When are validation messages shown (on blur, on submit)? What is the wording? Are they in the user's language?

## 2. Data lifecycle (CRUD) and persistence
- For each entity: who can **C**reate, **R**ead, **U**pdate and **D**elete it? Build a CRUD × role matrix.
- Is deletion soft or hard? Can data be restored? What happens to linked records (cascade delete, block, orphan)?
- Is there uniqueness (duplicate names, emails)? Is it case-sensitive?
- Is there a retention period or archiving rule?
- Is the data versioned? Is there an edit history?

## 3. Actors, roles and permissions
- List every actor: anonymous user, registered user, admin, support, API client, batch job.
- What does each role see and do? What happens when an unauthorised role tries a forbidden action directly (URL, API)?
- Can a user access another user's data by changing an ID (object-level authorisation, OWASP API1)?
- What happens when a role changes during a session?

## 4. States, workflow and concurrency
- What are the entity's statuses? Which transitions are allowed, and who can trigger each? What happens with an invalid transition?
- Two users editing the same record: last write wins, optimistic lock, or merge?
- Double-click or double-submit: is the operation idempotent?
- Behaviour on page refresh, the browser back button, or multiple tabs.
- Session timeout in the middle of a workflow: is data saved or lost?

## 5. Errors, recovery and messages
- For each external call and each validation: what does the user see? Can they retry? Is partial data kept?
- Network loss, timeouts, server 5xx, rate limiting (429).
- Error message rules: no stack traces or internal IDs shown to users, actionable text, correct language.
- How is a half-finished transaction recovered (payment taken but order not created)?

## 6. Integrations and external systems
- For each integration: the contract (API version, format), timeout, retries, circuit breaker, fallback.
- What if the third party is slow, down, returns malformed data, or returns an unexpected status?
- Webhooks or callbacks: ordering, duplicates, signature verification.
- Test environments: is there a sandbox or mock for the external system?

## 7. Time, date, money and locale
- Time zone of storage versus display. Daylight saving time (Türkiye has used fixed UTC+3 since 2016, but users abroad may not). Midnight rollover.
- Date boundaries: end of month, leap day (29 February), year end, "today" in which time zone?
- Validity periods: is "valid until 31.12" inclusive? Until 23:59:59, and in which time zone?
- Money: currency, rounding rule (half-up, banker's), rounding per line or per total, VAT/KDV included or excluded, minor units (kuruş).
- Locale formats: `1.234,56` versus `1,234.56`, dates as `dd.MM.yyyy`, Turkish sorting (ç after c, ğ after g, ı before i).

## 8. Lists, search and volume
- Empty state, one item, many items, the maximum number of items.
- Pagination or infinite scroll: page size, default sort, stable ordering.
- Search: case sensitivity, Turkish characters, partial match, no results, special characters.
- Export and import: formats, maximum size, encoding (UTF-8 with or without BOM for Excel).
- Expected data volume in one year. Behaviour with large datasets.

## 9. Notifications and communication
- Channel (email, SMS, push, in-app), trigger, recipient, template, language.
- Opt-in and opt-out rules. Legal requirements for commercial messages (in Türkiye, IYS registration).
- Behaviour when delivery fails. Duplicate prevention.

## 10. Audit, logging, privacy and compliance
- Which actions must be audited (who, what, when, before and after values)?
- Personal data: is it minimised? Is it masked in logs and user interfaces? Does it follow KVKK/GDPR for consent, access, deletion and retention?
- Payment data: PCI DSS scope. Never store or log full card numbers or CVV.
- Sector rules, for example BDDK and MASAK in Turkish finance, health data rules, accessibility law.

## 11. Platform, devices and environments
- Supported browsers and versions, operating systems, mobile devices, screen sizes and orientations.
- Accessibility target (WCAG 2.2 AA is the default professional baseline).
- Offline behaviour and poor-network behaviour on mobile.
- Which environments exist (dev, test, staging, prod)? Are there differences in configuration or test data?

## 12. Migration, compatibility and configuration
- What happens to existing data or users when the feature launches? Is a data migration needed?
- Backward compatibility of APIs and stored data.
- Feature flags: what does the system do with the flag on and off? Is there a rollout percentage?
- Configurable parameters: who can change them, and what are the defaults and limits?

## 13. Domain packs

**E-commerce**: stock reservation timing, price change between cart and checkout, coupon stacking and exclusivity, minimum basket amount, shipping thresholds, returns and partial refunds, taxes, guest checkout, abandoned carts.

**Finance and banking**: transaction limits (daily, per transaction), cut-off times and holidays, idempotency of transfers, double-entry consistency, interest and rounding, two-factor authentication and step-up auth, fraud checks, regulatory reporting, reconciliation.

**Health**: patient identity matching, consent, data sensitivity levels, clinical safety (fail safe), audit trail, interoperability standards (HL7/FHIR).

**Public sector**: e-Devlet integration, identity number validation (the TC Kimlik No checksum), accessibility obligations, archival rules.
