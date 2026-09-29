# API testing guide

## Contents
1. Test layers for APIs
2. What the contract generator covers, and what it cannot
3. Authorization (the #1 API risk)
4. State, data and idempotency
5. Error model, status codes, headers
6. Pagination, filtering, rate limits
7. Versioning and backward compatibility
8. GraphQL and async APIs
9. Reporting API failures

---

## 1. Test layers for APIs
| Layer | Question | Tooling in this suite |
|---|---|---|
| Contract / conformance | Does the implementation do what the OpenAPI document promises (status codes, schemas, validation)? | `openapi_tests.py` → executable Playwright API spec |
| Business rules | Are domain rules enforced server-side (limits, states, calculations)? | `designing-test-cases` techniques at API level, via the `request` fixture |
| Security | Authentication, authorisation (BOLA, BFLA), input handling, mass assignment, rate limiting | This file §3, plus `testing-nonfunctional` ASVS V4/V8 |
| Integration / consumer | Do consumers and providers agree across versions? | Consumer-driven contracts (for example Pact) if the teams use them; out of scope for the generator |
| Performance | Latency and throughput under load | `testing-nonfunctional` → k6 |

## 2. What the contract generator covers, and what it cannot
**Covered.** The generator derives tests only from what the contract states:
- the happy path with a schema check
- 401 without credentials
- missing required fields and parameters
- boundaries from `minimum`/`maximum`/`minLength`/`maxLength`
- invalid enum values and wrong types
- 404 for unknown resources
- an object-level authorisation skeleton

**Not covered, so design these tests yourself:**
- rules that the schema cannot express: cross-field rules, balances, states, limits per day;
- authorisation with two users, and roles (fill in the BOLA skeleton);
- idempotency and concurrency;
- side effects (was the e-mail sent, did the balance change?);
- anything that is undocumented.

**Weak contracts produce weak tests.** When the specification lacks error responses, examples, formats or constraints, the gaps come back as `# QUESTION` lines. Missing constraints are **API documentation defects**, so report them to the API owners.

## 3. Authorization (the #1 API risk)
OWASP API Security Top 10 (2023): API1 BOLA, API3 BOPLA, API5 BFLA.
- **BOLA (object level).** User A requests or modifies user B's object by ID, in the path, the query or the body. Expected result: 403 or 404, and **no data is leaked**. Test every path parameter that identifies an object, and every ID in a body (for example `fromAccountId`).
- **BFLA (function level).** A normal user calls admin endpoints or admin methods.
- **BOPLA / mass assignment.** Send properties that should be read-only (`role`, `balance`, `status`). Expected result: they are ignored or rejected, and they are never applied.
- **Credentials.** Test with no token, an expired token, a tampered token, a token of another tenant, and a malformed header: the token without its scheme (`Authorization: <token>`), the wrong scheme (`Basic`), and extra spaces. A middleware that strips an optional `Bearer ` prefix accepts all of them.
  - *Observed in the QA Suite API trial:* a blind tester found that `Authorization: <token>` without `Bearer` was accepted. The generator now adds this test once per API.

These tests need **two or more test users**. Put their tokens in the environment (`API_TOKEN`, `API_TOKEN_OTHER`). Never use real users.

## 4. State, data and idempotency
- **Creating tests change state.** A transfer lowers a balance; a created order uses up stock. Tests must therefore not depend on the leftovers of earlier runs.
  - Use a dedicated test account with a generous balance, or a reset or seed endpoint before each run, or a new account per run.
  - Run state-changing suites with `--workers=1` unless the data is isolated per worker.
  - *Observed in the QA Suite trial:* rerunning a transfer suite three times against the same server drained the balance, and turned a correct boundary test into a false failure.
- **Idempotency.** Send the same POST twice, especially with an `Idempotency-Key` header if the API supports one. Expected result: one resource, one side effect. Also check what happens when the client retries after a timeout.
- **Concurrency.** Fire parallel requests at a limited resource (the last stock item, a daily limit). Check that the invariant holds.

## 5. Error model, status codes, headers
- **Status codes:**
  - 201 for created resources, with a `Location` header if documented;
  - 204 for empty responses;
  - 400 or 422 for validation failures (be consistent);
  - 401 vs 403 (unauthenticated vs forbidden);
  - 404 for unknown resources, or hidden ones under BOLA;
  - 409 for conflicts;
  - 429 for rate limits.
- **A 500 on bad input is always a defect.** It means validation or error handling is missing.
- **Error bodies** follow one documented shape (for example `{code, message}` or RFC 9457 `application/problem+json`). They never contain stack traces, SQL or internal hostnames.
- **Headers:** `Content-Type`, caching headers on sensitive data (`no-store`), CORS for browser clients, and security headers.

## 6. Pagination, filtering, rate limits
- **Pagination:**
  - the first page, the last page, an empty page, page size at its limit and limit + 1;
  - stable ordering across pages (no duplicates or gaps when data changes);
  - cursor tampering.
- **Filtering and sorting:** unknown fields (400, never ignored silently unless documented), injection-shaped values, Turkish characters, case sensitivity.
- **Rate limits:** the 429 response, the `Retry-After` header, the limit per user vs per IP. Run these only in environments where they are agreed.

## 7. Versioning and backward compatibility
- Adding optional fields is compatible. Removing or renaming fields, changing types, or making optional fields required is **breaking**.
- Compare the OpenAPI documents of two versions (a diff tool, or review) and run the previous version's contract tests against the new build.
- Check deprecation headers and sunset dates when the API documents them.

## 8. GraphQL and async APIs
- **GraphQL:**
  - query depth and complexity limits;
  - introspection disabled in production;
  - field-level authorisation;
  - errors returned with HTTP 200 (assert the `errors` array, not only the status).
- **Async (webhooks, queues):**
  - signature verification;
  - duplicate and out-of-order delivery;
  - retries and back-off;
  - behaviour when the consumer is down.

## 9. Reporting API failures
- **Group failures by root cause before filing defects.** One wrong status code (for example 200 instead of 201) fails every test that creates something. File one defect with the list of affected TCs, not one per test.
- Attach the exact request (method, path, body; the token redacted), the response (status, headers, body) and the contract excerpt (the schema or response definition).
- Classify each failure:
  - an implementation defect (the contract is right, the implementation is wrong);
  - a contract defect (the documentation is wrong or incomplete);
  - a test data problem (see §4).
