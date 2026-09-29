# Security testing (OWASP ASVS 5.0 based)

## Contents
1. Scope and rules of engagement
2. Choosing the ASVS level
3. Feature → ASVS chapters
4. Tools
5. Reporting security findings

---

## 1. Scope and rules of engagement
- Test **only systems the user owns or is authorised to test**, in a **test environment**, with **test accounts**. Confirm the authorisation and the scope before any active check.
- Functional security testing by QA verifies that the controls in the requirements work: authorisation, validation, session handling, data masking. It **does not** replace a professional penetration test or a code review for high-risk systems. Recommend both where the risk warrants it.
- Out of scope unless explicitly agreed:
  - denial-of-service or load against security controls,
  - social engineering,
  - third-party systems,
  - production data.
- Handle findings confidentially: do not paste real secrets or personal data into reports.

## 2. Choosing the ASVS level
- **L1:** baseline for every application. Mostly verifiable with black-box testing.
- **L2:** the default for business applications that handle personal, financial or health data, which covers most e-commerce, banking and HR systems.
- **L3:** critical applications (high-value finance, health, infrastructure). Needs architecture and code review, not only testing.

Record the chosen level in the test plan. Cite exact ASVS 5.0 requirement IDs from the official document when reporting or tracing. `assets/asvs5-chapters.json` gives the chapter structure and test ideas only; the requirement text is not reproduced.

## 3. Feature → ASVS chapters
`scripts/nfr_checklist.py asvs --features ...` selects the chapters. The common mappings:

| Feature in the requirements | Chapters |
|---|---|
| Forms and inputs echoed back | V1 Encoding and Sanitization, V2 Validation and Business Logic |
| Prices, discounts, limits, multi-step flows | **V2** (server-side recalculation, sequence, concurrency) |
| Browser front-end | V3 Web Frontend Security (headers, cookies, CSRF) |
| REST/GraphQL | V4 API and Web Service, **V8 Authorization** (BOLA), V2 |
| File upload/download | V5 File Handling |
| Login, registration, password reset, MFA | **V6 Authentication**, V7 Session Management |
| Roles, multi-tenant data, "only my orders" | **V8 Authorization** |
| JWT or other self-contained tokens | V9 |
| SSO / OAuth / OIDC | V10 |
| Payments, personal data (TCKN, IBAN, health) | V11 Cryptography, **V14 Data Protection**, V12 Secure Communication |
| Deployment and configuration | V13 Configuration |
| Logging, error pages | V16 Security Logging and Error Handling |

Map these to the OWASP Top 10:2025 for communication:
- A01 Broken Access Control → V8
- A05 Injection → V1/V2
- A07 Authentication Failures → V6/V7
- A02 Security Misconfiguration → V13/V3
- A10 Mishandling of Exceptional Conditions → V16/V2

For APIs, add the OWASP API Security Top 10 (2023), where API1 is BOLA (V8).

## 4. Tools
- **Browser developer tools and Playwright's `request` fixture:** tamper with IDs, prices and roles. Automate authorisation checks at the API level (see the automation skill).
- **OWASP ZAP:** a baseline scan (passive) of the test environment in CI. Run active scans only with authorisation and in isolated environments.
- **Dependency scanning (SCA) and secret scanning** in the pipeline, usually owned by the developers.
- **TLS scanner** against the test host for V12.

## 5. Reporting security findings
Use the defect-report format (reporting skill) and add:
- the ASVS requirement ID(s) and the Top 10 category;
- the exact request and response (secrets redacted);
- the affected roles and data;
- the preconditions (which accounts);
- the business impact.

Default severity: broken access control, authentication bypass or data exposure is critical or high. Mark security defects as confidential in the tracker.
