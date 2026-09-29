# Trial: Demo Bank API (contract + authorisation, black box)

Reusable evaluation for the `testing-apis` skill: give an agent `api/openapi.json`, the running API
(`node api/server.js`, http://127.0.0.1:4180, test tokens `token-alice` and `token-bob`) and ask it
to test the API. **Do not show this file or `api/server.js` to the agent.**

Test data: alice owns `A-100` (TRY, balance 150.000) and `A-101` (EUR); bob owns `B-200` (TRY).
Transfers change balances, so restart the server for a clean state.

## Planted defects (the suite should find all five)
| # | Contract says | Implementation does | Found by |
|---|---|---|---|
| 1 | `amount` maximum 50000 | the maximum is not enforced; 50000.01 is accepted | generated boundary test (maximum + step) |
| 2 | missing required field → 400 | a missing `toIban` (or a non-string one) crashes the handler → 500 | generated missing-field and wrong-type tests |
| 3 | an account is only visible to its owner (403/404 for others) | `GET /accounts/{accountId}` returns another user's account (BOLA) | the BOLA skeleton, once filled in with bob's `B-200` using alice's token |
| 4 | `POST /transfers` → 201 | returns 200 | the generated happy-path and every valid create test (one root cause) |
| 5 | `Account.balance` is a number | `GET /accounts/{accountId}` returns it as a string (`"150000.00"`) | the response-schema check |

Unplanted but real (a good tester may raise them):
- `Authorization: token-alice` (no `Bearer` scheme) is accepted, because the server strips an optional
  prefix. First found by the blind trial run on 2026-09-30; the generator now tests it once per API.
- `toIban` in lower case (`tr33…`) is accepted and upper-cased, although the pattern is `^TR[0-9]{24}$`.
- The IBAN check digits (mod-97) are not validated; the contract only states the pattern, so this is a
  **contract gap** worth a question rather than an implementation defect.

## Contract gaps the review should raise
No `Idempotency-Key` for `POST /transfers`; insufficient balance has no distinct documented error
(only the generic 400); no pagination on `GET /accounts`; no rate-limit (429) documentation; IBAN
check digits not stated; 500 is not documented.

## Correct behaviour that must NOT be reported as a defect
- `POST /transfers` from another user's account (`fromAccountId: B-200` with alice's token) → 403 (documented).
- `GET /transfers/{id}` of another user's transfer → 404 (hides existence; acceptable for BOLA).
- Amount 0.99 → 400; currency `USD` → 400; description of 141 characters → 400.

## Results
See `docs/EVALUATION.md` for the recorded runs.
