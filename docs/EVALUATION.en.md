# Evaluation report: QA Suite 0.6.0

**[Türkçe →](EVALUATION.md)**

This document summarises how the package was tested and what the results were, **without inflating them**: what was measured, what was not, and how the findings went back into the skills. All trials ran on 29–30 September 2026 with Claude (an Opus-class model). The trial files are in `evals/`, so every trial can be repeated.

## Summary
| Evaluation | What it measures | Result |
|---|---|---|
| Blind end-to-end trial: FAST transfer (0.5.0) | The story → analysis → design → Playwright → report chain | **5/5 planted defects** plus 1 real one; the release decision was correct ("not ready") |
| Blind API trial (0.6.0) | `testing-apis`: OpenAPI → contract and authorisation tests | **5/5 planted defects** plus 2 real ones; 17 contract questions; an independent rerun gave the same result (31/11) |
| Blind data-migration trial (0.6.0) | `testing-data-migrations`: reconciliation, classification, go/no-go | **9/9 planted defects**; no false positives on the traps; the decision was correct (no-go) |
| With vs without skills (0.2.0) | 3 tasks graded against a fixed checklist | 93% vs 82% pass rate (+11 points) |
| Proxy routing | Is the right skill chosen from its name and description? | 17 skills, 84 requests: **84/84** (22/22 for the new skills) |
| Unit and regression tests | Behaviour of the 30 scripts | **150 tests**, run in CI on every push |

## 1. Blind end-to-end trial: FAST transfer
- **Setup:** a banking user story (FAST money transfer) and a demo web app with 5 planted defects. The agent never saw the app's code or the answer key.
- **Result:**
  - All 5 defects were found, plus a real one nobody planted: amounts with a thousands separator were parsed wrongly.
  - Every ambiguity in the story was raised as a question.
  - 47 tests were designed, 2% of them critical.
  - The Playwright run gave 37 passed / 9 failed, and an independent rerun gave the same result.
  - The decision was "not ready", because 4 of 9 exit criteria were met.
- **Cost:** about 334k tokens and about 26 minutes.
- Files: [evals/trial-fast](../evals/trial-fast/) · answer key: [evals/keys/fast.md](../evals/keys/fast.md) · real outputs: [examples/fast-transfer](../examples/fast-transfer/README.md)

## 2. Blind API trial: Demo Bank API
- **Setup:** an OpenAPI 3 document, a locally running API and two test users. Five defects were planted:
  - object-level authorisation (BOLA);
  - an upper limit that is not enforced;
  - a 500 on a missing field;
  - 200 instead of 201;
  - a balance returned as a string.

  The agent never saw the implementation or the answer key.
- **Run 1 (0.6.0 draft):** a safety classifier stopped the agent during exploration. We repeated the trial with a new agent and a prompt that made clear the server was our own local test environment. The partial run had already found the BOLA defect, the string balance and an **unplanted defect**: a token sent without the `Bearer` scheme was accepted. It also reported 5 gaps in the skill, and all of them were fixed.
- **Run 2:**
  - **All 5** planted defects were found, plus two unplanted real ones: the `Bearer`-less token, and a TRY transfer from a EUR account accepted without currency conversion.
  - 42 tests were written, 29 by the generator and 13 by hand. Result: 31 passed / 11 failed.
  - 17 contract questions were raised.
  - Defects were grouped by root cause; for example, 200-vs-201 is one defect covering 4 tests.
- **Independent check:** we reran the agent's suite against a fresh server and got the same result, **31 passed / 11 failed**.
- **12 findings fed back into the skill** (11 fixed in 0.6.0; the Turkish help text on the Windows console is documented in the README):
  - contract gaps become `# QUESTION` lines automatically;
  - invalid-pattern tests for fields with a `pattern`;
  - BOLA skeletons for IDs in the request body;
  - a GET by ID creates its resource with POST first;
  - negative tests check the error-body schema;
  - request and response evidence is attached to the report automatically, with the token masked;
  - warnings about reporters and about budgeting test state;
  - no more false "REDUNDANT" warnings in the RTM for generated tests.
- **The final generator on the same API and a fresh server:** 31 tests. With no human changes, 20 passed, 9 failed and 2 are skeletons. The 9 failures catch all 5 planted defects and the `Bearer` defect.
- Files: [evals/trial-api](../evals/trial-api/) · answer key: [evals/keys/api.md](../evals/keys/api.md) · real outputs: [examples/api-trial](../examples/api-trial/README.md)

## 3. Blind data-migration trial: customer data
- **Setup:**
  - a legacy extract of 40 rows in cp1254 with `;` delimiters;
  - a new-system extract of 41 rows in UTF-8;
  - a mapping document written in plain language.

  Nine defects were planted. So were traps: correct data that naive comparisons flag as wrong, such as Turkish upper case (İ/I), leading zeros, extra spaces and a leap day. The agent never saw the correct mapping or the answer key.
- **Result:**
  - **9/9** defects were found and classified correctly as load or transformation defects.
  - **No false positives** on the traps.
  - The whole control-total difference of +335,121.21 was explained by the row-level findings.
  - The decision was no-go, and 9 questions about the mapping spec were raised.
- **Time:** about 3 minutes. The reconciliation script ran in 0.2 s.
- **Fed back into the skill:**
  - the "rounding" hint now also covers precision loss;
  - the report explains the denominator effect on null rates;
  - the report shows file names instead of full paths.
- Files: [evals/trial-migration](../evals/trial-migration/) · answer key: [evals/keys/migration.md](../evals/keys/migration.md) · real outputs: [examples/migration-trial](../examples/migration-trial/README.md)

## 4. With vs without skills (0.2.0)
The same three tasks ran with and without the skills: Turkish end-to-end coupons, Turkish payment test design, and an English loan requirements review. A fixed checklist graded the outputs.

| | With skills | Without |
|---|---|---|
| Pass rate | 93% | 82% |
| Time | ~451 s | ~277 s |
| Tokens | ~136k | ~83k |

The skills raise quality, but they cost more time and tokens. 0.2.0 cut token use by 31% compared with 0.1.0 (from 197k to 136k). This comparison used the first 5 skills; it was not repeated for the 0.6.0 skills. Summary tables: `evals/results/benchmark-0.1.0.md`, `benchmark-0.2.0.md`.

## 5. Proxy routing
- **Method:** a model sees only the skill list (names and descriptions) and picks one skill per request, or "none". This is **not** Claude Code's real trigger mechanism; it is a cheap proxy. `tools/trigger_eval.py` measures the real mechanism, but it needs a logged-in `claude` CLI and we did not run it.
- **Sets:**
  - 42 basic requests;
  - 20 hard requests;
  - 22 new requests for 0.6.0. Five of them are near-misses that need no skill: Postman, SQL, Flutter, Faker, and an OpenAI API error.
- **Result:** 42/42 basic, 20/20 hard, 22/22 new. Every near-miss got "none".
- **Key change (for transparency):** two hard requests now go to the new, more specific skills: the IDOR question to `testing-apis`, and TCKN test data to `preparing-test-data`. Their expected answers were written before these skills existed, so the key now also accepts the new skill for them. With the old key the score is 18/20.
- To reproduce: `python tools/routing_proxy.py build …` and `score …`. Results: `evals/results/routing-proxy-2026-09-30.json`.

## 6. Unit and regression tests
- 150 tests written with the standard-library `unittest`. They cover:
  - boundary values, decision tables, state transitions and pairwise;
  - the RTM;
  - the export formats (Xray, Zephyr, TestRail, Azure DevOps, Qase, xlsx);
  - the OpenAPI generator and regression selection;
  - SBTM and AI eval scoring;
  - test data generation and masking;
  - the mobile checklist and data reconciliation.
- Checksummed identifiers are checked against independent reference implementations: 1000 each of TCKN, VKN and IBAN are generated and verified.
- A regression test runs the migration trial data with the correct mapping and asserts that exactly the 9 planted defects are found, no more.
- CI (GitHub Actions) runs the sync check, the skill validation (Agent Skills spec) and the unit tests on every push.

## What was not measured (honestly)
- **Skills without a blind trial:** exploratory testing, AI features, mobile and test data. They were validated only by unit tests and script demos. The mobile checklist was not tried on a real device, and the AI eval scoring was not tried on a real LLM product.
- **Imports into test-management tools:** the Xray, Zephyr, TestRail, Azure DevOps and Qase formats follow the vendors' documentation. None was imported into a real server. Do a trial import of 2–3 tests first.
- **Load testing:** the k6 scripts pass a syntax check, but no real load test was run.
- **Sample size:** each blind trial is a single run. The results are a strong signal, not statistical proof.
- **References written from memory:** the citations of regulations and standards (KVKK/GDPR articles, MASVS, OWASP LLM Top 10, store rules) were written without network access. Each skill's reference asks you to verify them.

## Repeat a trial yourself
```bash
node evals/trial-api/api/server.js      # http://127.0.0.1:4180, token-alice / token-bob
# Give the agent only evals/trial-api/api/openapi.json. Do not show it server.js or the evals/keys/ folder.
```
For the migration trial, give the agent only the two CSV files and `mapping-spec.md` from `evals/trial-migration/`.

How to set up a blind trial correctly (copy the folder outside the repo, keep the answer keys away from the agent) and how to grade it: [evals/README.md](../evals/README.md).
