# Non-functional requirements checklist (ISO/IEC 25010:2023)

ISO/IEC 25010:2023 describes product quality with nine characteristics. Use them as a map so no quality dimension is forgotten. For each characteristic that matters to the feature, check whether a **measurable** requirement exists. If none exists, raise a question or propose a derived requirement with a sensible default for the stakeholder to confirm.

A non-functional requirement is only testable when it states: **metric + threshold + conditions (load, environment, data) + measurement method**.

## Contents
1. Functional suitability
2. Performance efficiency
3. Compatibility
4. Interaction capability (formerly usability)
5. Reliability
6. Security
7. Maintainability
8. Flexibility (formerly portability)
9. Safety
10. Reference baselines (WCAG, OWASP)

---

## 1. Functional suitability
*Sub-characteristics: functional completeness, functional correctness, functional appropriateness.*
- Are all user tasks covered end to end? Are calculations specified with their precision and rounding?
- Example: "Totals are calculated to 2 decimal places using half-up rounding on the order total."

## 2. Performance efficiency
*Sub-characteristics: time behaviour, resource utilisation, capacity.*
- Response time: which operation, percentile (p95/p99), load level, and network profile.
- Throughput (transactions per second), number of concurrent users, peak versus average load, batch windows.
- Resource limits: memory, CPU, bundle size, mobile battery or data use.
- Web defaults to propose when nothing is specified (Core Web Vitals, measured at p75): LCP ≤ 2.5 s, INP ≤ 200 ms, CLS ≤ 0.1.
- Example: "POST /orders responds in ≤ 800 ms at p95 with 300 concurrent users and a 50k-order dataset."

## 3. Compatibility
*Sub-characteristics: co-existence, interoperability.*
- Supported browsers, operating systems, devices and API versions. Data exchange formats. Behaviour next to other systems (shared database, shared resources).

## 4. Interaction capability (formerly usability)
*Sub-characteristics: appropriateness recognisability, learnability, operability, user error protection, user engagement, inclusivity, user assistance, self-descriptiveness.*
- Accessibility: WCAG 2.2 level AA as the baseline. Keyboard operability, focus order and visibility, contrast, labels, error identification, target size.
- User error protection: confirmation before destructive actions, undo, input masks.
- Measurable targets: task completion rate, time on task, number of errors in a usability test.
- Languages and localisation (TR/EN), including text expansion and right-to-left support if needed.

## 5. Reliability
*Sub-characteristics: faultlessness, availability, fault tolerance, recoverability.*
- Availability target, for example 99.9% per month (about 43 minutes of downtime), with the maintenance windows excluded or included.
- Recovery Time Objective (RTO) and Recovery Point Objective (RPO), backups, failover.
- Behaviour when a dependency fails: graceful degradation, retries, queueing.

## 6. Security
*Sub-characteristics: confidentiality, integrity, non-repudiation, accountability, authenticity, resistance.*
- Authentication (MFA, password policy, lockout), session management (timeout, invalidation on logout).
- Authorisation at object and function level. Input handling (injection, XSS). Protection of secrets and personal data (encryption in transit and at rest).
- Audit trail and non-repudiation for critical actions.
- Baseline: OWASP ASVS 5.0 (choose Level 1, 2 or 3 by risk) and the OWASP Top 10:2025 risks. For APIs, use the OWASP API Security Top 10 (2023). For LLM features, use the OWASP Top 10 for LLM Applications.

## 7. Maintainability
*Sub-characteristics: modularity, reusability, analysability, modifiability, testability.*
- Testability requirements that help QA directly: stable test IDs or `data-testid` attributes, test hooks and seed data, controllable time and clock, structured logs, observable states, feature flags, a sandbox for third parties.

## 8. Flexibility (formerly portability)
*Sub-characteristics: adaptability, scalability, installability, replaceability.*
- Horizontal scaling targets, deployment and installation requirements, configurability per tenant or country.

## 9. Safety (new in 2023)
*Sub-characteristics: operational constraint, risk identification, fail safe, hazard warning, safe integration.*
- Relevant when software can cause physical, financial or health harm. What is the safe state on failure? Which warnings are shown, and when?

---

## 10. Reference baselines (current as of 2026)

| Area | Baseline to cite | Notes |
|---|---|---|
| Accessibility | WCAG 2.2 AA (also ISO/IEC 40500:2025) | WCAG 3.0 is still a draft. Do not test against it yet. |
| Web application security | OWASP ASVS 5.0, OWASP Top 10:2025 | Top 10:2025 adds A03 Software Supply Chain Failures and A10 Mishandling of Exceptional Conditions. |
| API security | OWASP API Security Top 10 (2023) | API1: broken object-level authorisation (BOLA) |
| LLM or AI features | OWASP Top 10 for LLM Applications; OWASP Agentic Top 10 (2026) | Prompt injection, sensitive information disclosure, excessive agency |
| Web performance | Core Web Vitals (LCP, INP, CLS) | Proposed defaults only. The stakeholder must confirm them. |
| Privacy | KVKK (Türkiye), GDPR (EU) | Consent, minimisation, retention, data subject rights |
