---
name: writing-bdd-scenarios
description: Writes BDD Gherkin scenarios (.feature files, Turkish or English) from QA Suite test cases or acceptance criteria. Every scenario keeps its TC ID as a tag. Drafts are generated deterministically, rewritten into declarative business language, and run as Playwright tests through playwright-bdd with shared page objects and the same results loop into the traceability matrix. Use this whenever someone asks for Gherkin, BDD, Cucumber, Given/When/Then scenarios, feature files, "living documentation", or wants acceptance criteria turned into executable specifications. Also use it for Turkish requests such as "Gherkin yaz", "BDD senaryosu", "feature dosyası", "Diyelim ki / Eğer ki / O zaman", "kabul kriterlerini senaryoya çevir".
license: MIT
metadata:
  suite: qa-suite
  version: "0.5.0"
---

# Writing BDD scenarios

Gherkin is valuable when business people read, review or co-write the scenarios. It turns acceptance criteria into specifications that everyone can check and machines can run. It is overhead when nobody outside QA reads them. In that case, plain Playwright specs from `automating-with-playwright` are simpler. Say so if the user has not decided.

## Language
Match the user's language. Turkish features start with `# language: tr` and use `Özellik`, `Geçmiş`, `Senaryo`, `Senaryo taslağı`, `Örnekler`, `Diyelim ki`, `Eğer ki`, `O zaman`, `Ve` and `Fakat`. Tags and IDs stay as they are.

## Reading plan
- Read `references/gherkin-style.md` before rewriting drafts (rules, Turkish phrasing, outlines, tags).
- Read `references/playwright-bdd.md` when the scenarios should run (setup, step definitions, run and results).

## Workflow

```
- [ ] 1. Source: qa/test-cases.json (preferred) or acceptance criteria
- [ ] 2. Generate drafts (generate_features.py)
- [ ] 3. Rewrite declaratively; keep tags and expected results
- [ ] 4. (If executable) step definitions reusing page objects; playwright-bdd config
- [ ] 5. Run; results → qa/results.json → RTM
```

### 1. Source
Use `qa/test-cases.json` from `designing-test-cases`. Its techniques, boundaries and TC IDs carry over. If only acceptance criteria exist, write the scenarios directly, but assign or confirm TC IDs, so they stay traceable.

### 2. Generate drafts
```bash
python scripts/generate_features.py --tests qa/test-cases.json --requirements qa/requirements.json --out features [--lang tr|en] [--all] [--only TC-003,TC-004]
```
The drafts have this structure:
- one Feature per requirement (`@REQ-###`, with the requirement text as its description);
- a Background built from preconditions shared by all of the feature's scenarios;
- one Scenario per test case (`@TC-###`, priority and tags);
- Given from preconditions, When/Then per manual step, with data as a `"quoted"` value;
- data variants merged into a Scenario Outline with **one tagged Examples block per TC**.

By default only automation candidates are included; `--all` includes every test case. Re-running only adds missing TCs.

### 3. Rewrite declaratively
The drafts are faithful but imperative. For each scenario:
- rewrite the steps into business language;
- aim for 3–5 steps and one behaviour;
- reuse existing step phrases.

Follow the before/after example and the rules in `references/gherkin-style.md`. **Keep every tag and every expected result.** The wording changes; what is verified must not. Show the user the rewritten feature for review when business stakeholders are the audience.

### 4. Make it executable (optional)
With the user's agreement to install `playwright-bdd`:
- configure `defineBddConfig`;
- create `steps/fixtures.ts` with `createBdd(test)`, reusing the page objects from `automating-with-playwright`;
- implement the step definitions with Cucumber expressions (`{string}`, `{int}`).

`npx bddgen` lists any undefined steps. See `references/playwright-bdd.md`.

### 5. Run and close the loop
```bash
npx bddgen && npx playwright test
python <automating-with-playwright>/scripts/pw_results.py test-results/results.json --out qa/results.json
```
The Gherkin tags become Playwright tags, so the results map to TCs and the RTM shows the execution status per requirement. Report the scenarios written, the scenarios executed, failures (product bug vs step bug), and steps still undefined.

## Files
- `scripts/generate_features.py`: test cases → Gherkin drafts (TR/EN), Background, outlines with per-TC Examples, idempotent.
- `references/gherkin-style.md`: declarative rules, Turkish phrasing, outlines, tags, before/after example.
- `references/playwright-bdd.md`: setup, fixtures, step definitions, run, results, Xray Cucumber note.
