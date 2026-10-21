# Answer Key — trial-api2 (Anadolu Güven Sigorta: Poliçe & Hasar API)

Kind: REST API testing from an OpenAPI 3.1 contract.
Trial folder: `C:\projeler\TestSkills\evals\trial-api2\`
System under test (evaluator-only): `trial-api2\server.js`
Verifier (ground truth): `C:\projeler\TestSkills\evals\keys\grade_api2.py`
→ A fresh server + verifier prints `15/15 checks behaved as designed.`

Tokens: `tok_user1_ayse` (u1), `tok_user2_mehmet` (u2), `tok_admin_root` (admin).
Seed: 5 policies (pol_1,pol_2,pol_5 → u1; pol_3,pol_4 → u2), 7 claims
(clm_1..clm_5 → u1, clm_6,clm_7 → u2). Restart = reset. Port from `PORT` env
(default 3000); parallel copies are isolated.

The agent is given only `TASK.md` + `openapi.yaml` + base URL + tokens. It must
discover defects by probing the running API and comparing to the contract.

Grade `bulgular.md` **blind**. A defect counts only if the agent names the
correct endpoint/behaviour AND gives reproduction evidence consistent with the
acceptance rule below. Vague "authorization seems weak" with no concrete request
does **not** earn the points.

Difficulty mix: Easy = K6, K7, K9 (3) · Medium = K2, K3, K5 (3) ·
Hard = K1, K4, K8, K10 (4). Max score **100** (87 detection + 13 report quality).

---

## Planted defects (K1..K10)

### K1 — BOLA / object-level authorization via QUERY param (not path)
- **What:** `GET /claims?policyId=<id>` drops the ownership scope. When a
  `policyId` the caller does **not** own is supplied, the API returns that
  policy's claims anyway.
- **Why it matters:** Any authenticated user can read any other customer's claim
  data (amounts, descriptions, status) by guessing/iterating policy ids. Classic
  Broken Object-Level Authorization (OWASP API1).
- **Acceptance rule (grader):** Report must show that **user1** calling
  `GET /claims?policyId=pol_4` (pol_4 belongs to u2) returns at least one claim
  with `ownerUserId: "u2"` (e.g. clm_6, amount 5000). Equivalent: user2 reading
  u1's policy claims via `?policyId=pol_1` / `pol_2` / `pol_5`.
- **Discriminator:** Path-based access **is** correctly blocked
  (`GET /policies/pol_1` as user2 → 403; see T3b). A tester who only checks
  `/policies/{id}` or `/claims/{id}` path access concludes authz is fine and
  misses this. The bug lives only on the `policyId` **query** path.
- **Severity:** Critical · **Difficulty:** Hard · **Points: 12**

### K2 — Broken function-level authorization (BFLA) on `/admin/stats`
- **What:** `GET /admin/stats` performs no role check; a normal user token gets
  `200` with aggregate data (`totalPolicies`, `totalClaims`, `totalPremium`).
- **Why it matters:** Admin-only function reachable by normal users (OWASP API5).
- **Acceptance rule:** Report shows `user1` (or user2) `GET /admin/stats` → `200`
  with the stats body, contrary to the contract ("normal kullanıcı için 403").
- **Discriminator:** The sibling endpoint `GET /admin/policies` **is** correctly
  protected (user → 403). A tester who tests only `/admin/policies` wrongly
  concludes all admin routes are safe.
- **Severity:** High · **Difficulty:** Medium · **Points: 10**

### K3 — Mass assignment of a read-only field (`status`) on PATCH
- **What:** `PATCH /policies/{id}` applies `status` from the request body, even
  though the contract says only `holderName` and `agentName` are editable and
  `status` is read-only.
- **Why it matters:** A customer can flip their own policy to `active` /
  `cancelled` / `expired` / `pending`, bypassing the internal lifecycle (OWASP
  API6 / mass assignment).
- **Acceptance rule:** Report shows a user PATCHing `{"status":"expired"}` (or any
  other status) on their own policy (e.g. pol_1) and a subsequent `GET` confirming
  `status` changed. Reporting `premium`/`coverageLimit`/`ownerUserId` as writable
  is **false** (see T2) and does not earn this.
- **Severity:** High · **Difficulty:** Medium · **Points: 10**

### K4 — Missing idempotency (duplicate POST creates two resources)
- **What:** `POST /claims` documents an `Idempotency-Key` header that must prevent
  duplicate creation, but the server ignores it. Two identical POSTs with the same
  key create two distinct claims.
- **Why it matters:** Network retries / double-clicks create duplicate claims →
  data integrity and potential double-payout.
- **Acceptance rule:** Report shows two `POST /claims` with the **same**
  `Idempotency-Key` (same body) returning **two different** `id`s (e.g. clm_8 and
  clm_9), instead of the same resource.
- **Severity:** Medium · **Difficulty:** Hard · **Points: 8**

### K5 — Pagination: wrong `meta.total`
- **What:** `GET /claims` returns `meta.total` equal to the **current page**
  length, not the total across all pages. Contract explicitly defines `total` as
  the pre-pagination total.
- **Why it matters:** Clients compute page counts from `total`; a wrong value
  breaks paging and hides records.
- **Acceptance rule:** Report shows that with `?page=1&pageSize=2` as user1 (who
  owns ≥5 claims), the response has `data` length 2 **and** `meta.total == 2`
  (should be ≥5). Must use a `pageSize` smaller than the owned count.
- **Discriminator:** With the default `pageSize=20`, all of u1's 5 claims fit on
  page 1 and `meta.total` coincidentally equals 5 — the bug is **invisible**
  unless the tester actually paginates. A quick smoke test misses it.
- **Severity:** Medium · **Difficulty:** Medium · **Points: 8**

### K6 — Validation gap: `amount` minimum not enforced
- **What:** `ClaimCreate.amount` is documented `minimum: 1` ("1'den küçük
  olamaz"), but `POST /claims` accepts `0` and negative amounts and creates the
  claim.
- **Why it matters:** Zero/negative claim amounts are invalid business data;
  documented constraint not enforced.
- **Acceptance rule:** Report shows `POST /claims` with `amount` ≤ 0 (e.g. -500 or
  0) on the caller's own policy → claim created (HTTP 200) with that amount,
  instead of a `400`/`422`.
- **Severity:** Medium · **Difficulty:** Easy · **Points: 6**

### K7 — Wrong status code on create (`200` instead of `201`)
- **What:** Successful `POST /claims` returns `200`; the contract specifies `201`.
- **Why it matters:** Contract/HTTP-semantics violation; breaks clients that key
  off `201`.
- **Acceptance rule:** Report notes a valid `POST /claims` returns HTTP **200**
  where the contract documents **201**.
- **Severity:** Low · **Difficulty:** Easy · **Points: 5**

### K8 — Response/schema mismatch: required `claimNumber` omitted
- **What:** The `Claim` schema lists `claimNumber` as **required**, but no claim
  response (GET list, GET by id, POST result) includes `claimNumber`.
- **Why it matters:** Response violates its own schema; contract consumers relying
  on `claimNumber` break. Only a schema-level comparison catches it.
- **Acceptance rule:** Report shows any claim response object lacking the
  `claimNumber` field and cites that the schema marks it required. (Noting other
  genuinely-required-but-present fields does not count; `claimNumber` specifically.)
- **Severity:** Medium · **Difficulty:** Hard · **Points: 9**

### K9 — Error response leaks internals (stack trace + file path)
- **What:** Sending malformed JSON to `POST /claims` (or `PATCH /policies/{id}`)
  returns `400` with a `stack` field containing the Node stack trace and the
  **absolute server file path** (`...\trial-api2\server.js:...`) plus internal
  module paths.
- **Why it matters:** Information disclosure (OWASP API8 / improper error
  handling) — reveals stack, file layout, runtime internals to any caller.
- **Acceptance rule:** Report shows an error response whose body contains a
  `stack` value (or an absolute `server.js` path / `node:internal...`). Trigger:
  body like `{bad json`.
- **Severity:** Medium · **Difficulty:** Easy · **Points: 7**

### K10 — Business-rule violation: `amount` may exceed `coverageLimit`
- **What:** Contract (POST /claims description) states a claim's `amount` cannot
  exceed the policy's `coverageLimit` (else `422`). The server never checks it.
- **Why it matters:** Claims above the insured limit are accepted → financial/
  business-logic flaw (OWASP API6 business logic).
- **Acceptance rule:** Report shows `POST /claims` with `amount` > the target
  policy's `coverageLimit` succeeding. Canonical: pol_1 `coverageLimit` = 50000,
  `POST {policyId:"pol_1", amount:60000}` as user1 → claim created (200) instead
  of 422. Any owned policy works if the tester reads its limit from
  `GET /policies/{id}` and exceeds it.
- **Discriminator:** Requires cross-checking the policy's `coverageLimit` (from
  one call) against the claim amount (another call) and reading the business rule
  in the contract description — not a surface check.
- **Severity:** High · **Difficulty:** Hard · **Points: 12**

**Detection subtotal: 87 points.**

---

## Traps (T1..T4) — correct behaviour; reporting as a defect = false positive

### T1 — `GET /policies` returns only the caller's own policies
- Correct per contract (user sees own; admin sees all). user1 → exactly
  {pol_1, pol_2, pol_5}.
- **False positive if** reported as "missing data / policies not returned / data
  loss". This is correct authorization scoping, not a bug.

### T2 — PATCH ignores non-whitelisted fields (`ownerUserId`, `premium`, `coverageLimit`)
- Sending `{"ownerUserId":"u2","premium":1}` to `PATCH /policies/{id}` leaves those
  fields unchanged (correctly ignored).
- **False positive if** reported as "mass assignment of ownerUserId/premium". Only
  `status` is actually mutable (that is K3). Do **not** award K3 for an
  ownerUserId/premium claim, and treat such a claim as a false positive.

### T3 — Admin can read any user's policy/claim
- `admin` token reading `GET /policies/pol_1` (u1's) → 200 is **documented** admin
  behaviour.
- **False positive if** reported as BOLA. (Note T3b: a *normal* user reading
  another user's policy by path is correctly `403` — path BOLA is NOT present;
  the real BOLA is the query-param one, K1.)

### T4 — `agentName` is `null` for some policies
- pol_2 and pol_5 return `agentName: null`; the schema is `type: ["string","null"]`
  (OpenAPI 3.1 nullable). Correct.
- **False positive if** reported as "null/missing field bug" or "schema
  violation". (Contrast with K8, where `claimNumber` — a **required, non-nullable**
  field — is genuinely absent.)

---

## Scoring rubric (max 100)

1. **Detection (87 pts):** award each K's points when the acceptance rule is met
   with concrete reproduction evidence.
   - Partial credit: if the agent reports the correct *symptom* but the wrong
     *root cause / wrong endpoint* (e.g. "pagination looks off" without showing
     `meta.total` vs. real total), award **half** (round down).
   - K1 and K10 require the specific cross-user / over-limit evidence; a generic
     "authz weak" or "no validation" sentence without the reproducing request
     earns **0** for that item.

2. **Report quality (13 pts):** up to 13 for (a) clear per-finding reproduction
   steps (request + token + observed response), (b) severity ratings roughly
   consistent with this key, (c) findings traceable to `test-kayitlari.md`
   evidence. Scale down for missing repro steps or no evidence log.

3. **False-positive penalty:** **−4** per reported "defect" that is actually a
   trap (T1–T4) or is otherwise incorrect/unsupported (e.g. claiming a field is
   mutable when it is not, or flagging the correct `401`/`403`/`404`/`400`
   responses as bugs). Applied after detection; findings-section total floored
   at **0** (quality points are not driven negative).

4. **Final score** = Detection + Report quality − False-positive penalties,
   clamped to [0, 100].

**Interpretation / discrimination (expected, not scored):**
- A quick intuitive pass by a strong generic model typically lands the easy/medium
  items (K6, K7, K9, K2, K3) and perhaps K1, but tends to miss at least one of the
  hard contract/business items (K5 hidden by default page size, K8 required-field
  omission, K10 limit cross-check, K4 idempotency) and/or trips a trap (commonly
  T2 or T3). Reaching 100 requires systematic, schema-level and business-rule
  testing plus trap discipline. If a run scores 100 easily, treat the trial as a
  ceiling and tighten.

---

## Verification log (performed by trial author)

Ran `node server.js` (PORT=3300) + `python grade_api2.py http://localhost:3300`:
`15/15 checks behaved as designed.`
- K1 user1 `?policyId=pol_4` → 200, data owner u2 (leak). ✔
- K2 user1 `/admin/stats` → 200 `{totalPolicies:5,totalClaims:7,totalPremium:9800}`. ✔
- K3 PATCH status=expired applied; GET shows `expired`. ✔
- K4 same Idempotency-Key → clm_8 and clm_9 (two). ✔
- K5 `page1&pageSize2` → 2 items, `meta.total=2` (should be ≥5). ✔
- K6 `amount=-500` → 200, created. ✔
- K7 valid POST → HTTP 200 (not 201). ✔
- K8 claim objects lack `claimNumber`. ✔
- K9 malformed JSON → 400 with `stack` incl. `C:\projeler\TestSkills\evals\trial-api2\server.js:216:25`. ✔
- K10 `amount=60000` on pol_1 (limit 50000) → 200, created. ✔
- T1 user1 /policies → only {pol_1,pol_2,pol_5}. ✔ (correct)
- T2 ownerUserId/premium PATCH ignored. ✔ (correct)
- T3 admin reads pol_1 → 200; T3b user2 reads pol_1 → 403. ✔ (correct)
- T4 pol_2 agentName=null. ✔ (correct)
Also verified: parallel instance on :3301 fresh (7 claims) while :3300 mutated
(12) — isolation + restart-reset confirmed. `/health` no-auth 200; missing token
→ 401.
