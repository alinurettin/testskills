---
name: testing-apis
description: Tests REST APIs from their OpenAPI 3.x contract. Generates traceable test cases and an executable API suite with the same TC IDs (happy path, schema, 401, required fields, boundaries, enums, 404), then guides business-rule and idempotency tests. Use when endpoints or a Swagger document need testing. Triggers include API testing, REST endpoints, contract tests, IDOR/BOLA authorization; Turkish "API testi", "Swagger'dan test çıkar", "endpoint'leri test et".
license: MIT
metadata:
  suite: qa-suite
  version: "0.7.1"
---

# Testing APIs

APIs are where most business rules actually run, and where authorisation mistakes leak data at scale. This skill starts from the **contract** (OpenAPI). Everything the contract states becomes a traceable test case *and* an executable Playwright API test, generated deterministically. Everything the contract does not state becomes a question, or a test you design deliberately.

## Language
Match the user's language (`--lang tr|en`). HTTP methods, paths, field names and status codes stay as they are.

## Reading plan
- This file covers the workflow.
- Read `references/api-testing.md` before designing tests that go beyond the contract: authorisation, state and idempotency, error model, pagination, versioning, and reporting.
- The compact format syntax is at `python scripts/qa_compact.py --help`.

## Prerequisites and safety
- An OpenAPI 3.0/3.1 document in JSON. YAML needs PyYAML; otherwise convert it to JSON. Swagger 2.0 must be converted to 3.x first.
- A test environment URL, and **test accounts only**: one token, or two tokens for authorisation tests. Pass them through the environment (`API_BASE_URL`, `API_TOKEN`, `API_TOKEN_OTHER`), never in files.
- Run the suite only against environments the user owns and is authorised to test. The suite creates data.
- Playwright (`@playwright/test`) must be installed to run the suite. Ask before installing packages.

## Workflow

```
- [ ] 1. Contract review (gaps → questions); map operations to requirements (one REQ for everything hides gaps)
- [ ] 2. Generate contract tests (compact + executable spec)
- [ ] 3. Add business-rule, authorization and state tests the contract cannot express
- [ ] 4. Run with clean test data; group failures by root cause
- [ ] 5. Results → qa/results.json → RTM; defect reports
```

### 1. Contract review
Read the OpenAPI document as a requirement. Record a question or finding for each of these gaps:
- missing error responses (400/422/404/409);
- missing examples;
- unconstrained strings and numbers;
- undocumented authorisation rules;
- inconsistent error bodies.

Contract defects are real defects: consumers build against the document.

**Map operations to requirements; one REQ for everything hides gaps.** With a single `--req`, 30–80 tests hang off one REQ: coverage looks 100% and the RTM can never report a THIN or NO_NEGATIVE requirement. If `qa/requirements.json` does not exist yet, create the API requirements with `analyzing-requirements` first. Then either:
- copy `assets/req-map-example.json` to `qa/req-map.json` and map each operation (by `operationId` or `"METHOD /path"`) or each tag to the REQ(s) it implements; or
- add `"x-req": "REQ-021"` (or a list) to the operation in the OpenAPI document.

Precedence: `x-req` > `operations[operationId]` > `operations["METHOD /path"]` > `tags[first tag]` > `default` > `--req`. An operation without a requirement stops the generator (exit 2) with the list of unmapped operations. The same map file can carry the mobile, non-functional and AI sections; each script reads only its own keys.

### 2. Generate contract tests
```bash
python scripts/openapi_tests.py api/openapi.json --req-map qa/req-map.json --tests qa/test-cases.json --lang tr \
    --out qa/design/api-contract.src.md --spec-out automation/tests/api-contract.spec.ts
cp assets/api-helpers.ts automation/tests/api-helpers.ts
```
`--req REQ-020` still works, as the fallback for operations the map does not cover. The script prints how many tests, and how many negative ones, each requirement received; check that list before merging.

The script produces, per operation:
- the happy path (2xx plus a response-schema check);
- 401 without credentials when the operation is secured, plus one malformed-header test per API (the token without the `Bearer` scheme);
- one test per missing required body field or required query parameter;
- schema boundaries: the valid min/max and the value just outside, plus length limits;
- an invalid enum value and a wrong type;
- 404 for an unknown path ID when 404 is documented;
- an invalid-pattern value for strings with a `pattern`;
- a BOLA test when the operation is secured and takes an ID. When a `POST` on the collection returns an `id`, the test creates the resource with user A and reads it with user B, so it runs without manual data (it is skipped until `API_TOKEN_OTHER` is set). Otherwise it is a skeleton (`test.fixme`).
- a body-level BOLA skeleton for ID fields in the request body (for example `fromAccountId`);
- `GET` by ID creates its resource first when possible, instead of trusting example IDs;
- negative tests also check the documented error-body schema. It requests the example resource with the second user's token (`as: 'other'` → `API_TOKEN_OTHER`). Confirm that the example ID belongs to the `API_TOKEN` user, then delete the `fixme` line.

It uses the same TC IDs in the compact test cases and in the executable spec. **Contract gaps become `# QUESTION` lines:** undocumented error codes (asserted as a 4xx range), missing 401/404, error responses without a body schema, no idempotency key on `POST`, unconstrained strings and numbers, no rule for unknown fields, and path parameters without examples. Review the compact file, then append it to `qa/test-cases.src.md` and run `qa_compact.py`.

### 3. Tests the contract cannot express
Design these with `designing-test-cases` techniques, following `references/api-testing.md`:
- **Business rules** (limits, states, calculations): use the domain packs where they apply.
- **Authorisation:**
  1. Fill in the BOLA skeletons, using a second user's resource ID.
  2. Add BFLA tests (admin functions called with a normal user's token).
  3. Add mass-assignment tests for read-only fields.
- **State and idempotency:** duplicate POSTs, concurrent requests, side effects.
- **Pagination, filtering and rate limits**, where relevant.

Write these as normal test cases (category `api`). `automating-with-playwright/generate_specs.py` generates `{ request }` skeletons for them.

### 4. Run and triage
The suite needs only `@playwright/test`, no browsers. If the project has no Playwright config yet, a minimal one next to the tests folder is enough:
```ts
// playwright.config.ts
import { defineConfig } from '@playwright/test';
export default defineConfig({ testDir: './tests', workers: 1, reporter: [['list'], ['json', { outputFile: 'results/pw-report.json' }]] });
```
```bash
API_BASE_URL=http://127.0.0.1:4180 API_TOKEN=... API_TOKEN_OTHER=... npx playwright test tests/api-contract.spec.ts
```
When `@playwright/test` is installed in another folder, run `npx playwright test -c <path>/playwright.config.ts` from that folder, so the import resolves.
- **Keep the JSON report.** `--reporter=…` on the command line replaces the config's reporters, so the JSON report is not written; `--list` overwrites it with an empty report. Copy the report of every state-changing run before running again.
- **Evidence is captured automatically.** `api-helpers.ts` attaches every request and response (token masked) to the Playwright report. Use those attachments in defect reports. `API_EVIDENCE=off` disables it.
- **Clean data every run.** State-changing tests consume balance, stock and quotas. Reset or seed before each run, or use a dedicated high-balance test account. A drained account turns correct tests into false failures.
- **When the environment cannot be reset,** budget the state before you run: add up what one full run consumes (for example the sum of all accepted transfer amounts, including the maximum-boundary test), compare it with the available balance, and run the state-changing tests once. Explore with read-only requests (`GET`) and single `curl` calls, and rerun only the failed tests (`--last-failed`). Include the maximum-boundary test in the budget: it needs a balance above the maximum. Run tests that could corrupt state (a wrong type accepted into an amount) last.
- **Setup steps accept any 2xx.** A create step inside a business test should check `res.ok()`, not the exact code; otherwise one wrong status code (200 instead of 201) masks every business test behind it.
- **Negative tests can pass for the wrong reason.** A 400 for "insufficient funds" also satisfies "amount above the maximum is rejected". When the error body carries a code, assert it (for example `VALIDATION`), and keep balances high enough that only the rule under test can reject the request.
- **On Windows, prefer `127.0.0.1`** over `localhost` when the server listens on IPv4 only, because `localhost` may resolve to `::1`.
- **Group failures by root cause.** For example, "returns 200 instead of 201" fails every create test. File one defect listing all affected TCs. Classify each failure as an implementation defect, a contract defect or a test data problem.

### 5. Close the loop
`automating-with-playwright/scripts/pw_results.py` maps the Playwright JSON report to `qa/results.json` by TC tag. Then run the RTM (`tracing-requirements`) and write defect reports (`reporting-test-results`), with the request, the response and the contract excerpt as evidence.

## Files
- `scripts/openapi_tests.py`: OpenAPI 3.x → compact test cases plus an executable Playwright API spec with the same TC IDs. Links each operation's tests to its REQ(s) (`--req-map`, `x-req`). Resolves `$ref` and `allOf`; outputs TR/EN.
- `scripts/qa_compact.py`: compact ⇄ JSON.
- `assets/req-map-example.json`: operation and tag → requirement map for `--req-map`.
- `assets/api-helpers.ts`: request helper (path/query parameters, bearer token from the environment) and a dependency-free response-schema checker.
- `references/api-testing.md`: layers, generator limits, authorisation, state and idempotency, error model, pagination, versioning, GraphQL and async APIs, reporting.
