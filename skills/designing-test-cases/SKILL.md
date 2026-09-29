---
name: designing-test-cases
description: Designs professional manual test cases from requirements using ISTQB/ISO 29119-4 techniques. Equivalence partitioning, boundary value analysis (2/3-value), decision tables, state transitions (0/1-switch plus invalid transitions) and pairwise combinations are computed by deterministic scripts, then complemented by use-case, CRUD, error-guessing and exploratory techniques. Test depth and per-test priority are risk-calibrated, and the output is traceable test-cases.json with stable IDs. Use this whenever someone asks for test cases, test scenarios, test conditions, negative or boundary tests, a regression suite, or wants to know "what should we test" for a feature, story, form, API or workflow. Also use it for Turkish requests such as "test case yaz", "test senaryosu çıkar", "sınır değer analizi", "karar tablosu", "negatif testler", "regresyon seti hazırla", even when no technique is named.
license: MIT
metadata:
  suite: qa-suite
  version: "0.5.0"
---

# Designing test cases

A good test suite is not "many tests". It is **the smallest set of tests that exercises every meaningful partition, boundary, rule, transition and interaction, with depth proportional to risk, where every test says exactly what to observe, and where priorities let the team triage.**

This skill gets there in three ways:
- The combinatorics are computed with scripts, not guessed. The scripts cannot miss a boundary or a rule combination, and their outputs double as coverage evidence.
- Test cases are authored in a compact text format and converted to JSON by a script. That keeps the work fast and the JSON valid.
- A deterministic calibration check catches inflated priorities and redundant tests before delivery.

## Language

Write test cases in the user's language: Turkish if the user writes Turkish, otherwise English, unless the user asks for something else. Keep IDs, field keys and enum values in English. Quote UI labels exactly as they appear in the product.

## Reading plan (keep context lean)

- **Always read:** `references/technique-selection.md`. It is short and covers technique choice, depth and the test budget.
- **Read only what you use:**
  - the sections of `references/techniques.md` for the techniques you actually apply (find them via its Contents list);
  - the relevant categories of `references/error-guessing-checklist.md`.
- **Read `references/test-case-standard.md` sections 2 and 4** (writing rules and priority) before your first test. Use section 6 as the final checklist.
- **Domain packs:** for banking/payments, e-commerce, health or the public sector, read sections 3–4 of the matching pack in `references/domains/` (high-risk rules → techniques, and test data such as TCKN/IBAN validation partitions).
- **Compact format syntax:** run `python scripts/qa_compact.py --help`. You do not need `references/data-model.md` unless you read the JSON directly.

## Inputs

- **Preferred:** `qa/requirements.json` from the `analyzing-requirements` skill.
- **Raw requirements** (a story, ticket or spec) that were never analysed:
  1. Do a quick normalization in `qa/requirements.src.md`. Assign REQ IDs, source, type, priority and risk, and split compound statements.
  2. Convert it: `python scripts/qa_compact.py req qa/requirements.src.md --out qa/requirements.json`.
  3. Note the major ambiguities as questions.

  For a large or high-risk scope, run the full `analyzing-requirements` skill first.
- **An existing suite:** extend `qa/test-cases.src.md`. If only JSON exists, create the source with `--to-compact`. Never renumber. New tests take the next free `TC-###`.

## Workflow

```
- [ ] 1. Scope, risk sanity check and test budget
- [ ] 2. Test conditions per requirement
- [ ] 3. Techniques selected; script specs written and run
- [ ] 4. Script findings fed back as questions
- [ ] 5. Test cases authored in qa/test-cases.src.md → JSON
- [ ] 6. Calibration: RTM check, re-rate priorities, drop redundancy (at most 2 passes)
- [ ] 7. Summary with coverage
```

### 1. Scope, risk sanity check and budget

1. Read the requirements, including their `risk`, `priority`, `status` and `questions`.
2. Check that the risk levels are plausible. Usually only about 10–20% of requirements are critical. Depth follows risk, so an inflated score multiplies the suite.
3. Set a test budget from `references/technique-selection.md` section 2. For one story with 5–8 acceptance criteria, that is usually 15–35 tests.

When a requirement has open questions, still design for it. Use the documented default assumption and cite it (`Q-###`).

### 2. Identify test conditions

For each requirement, list what can be tested:
- inputs and their domains
- rules
- states
- roles
- outputs
- side effects
- error paths

Include the confirmed-worthy derived requirements. This list is the bridge between the requirement and the techniques.

### 3. Select techniques and run the scripts

For every computable technique, write a spec to `qa/design/DS-###-<name>.json` (examples in `assets/spec-examples/`) and run:

```bash
python scripts/ep_bva.py qa/design/DS-001-loan-inputs.json --out qa/design/DS-001-loan-inputs.md
python scripts/decision_table.py qa/design/DS-002-coupon-rules.json --out qa/design/DS-002-coupon-rules.md
python scripts/state_transition.py qa/design/DS-003-order-states.json --out qa/design/DS-003-order-states.md
python scripts/pairwise.py qa/design/DS-004-compat.json --out qa/design/DS-004-compat.md
```

Options:
- `--lang tr|en`
- `ep_bva.py --strategy compact|single`
- `decision_table.py --coverage collapsed|full` (use full only for critical risk)
- `state_transition.py --switch 1` (critical risk only)
- `pairwise.py` with `"strength": 3` (critical risk only)
- `ep_bva.py` with `"bva": "3-value"` (critical risk only; 2-value otherwise)

Model rules **exactly as written** first, even when they look contradictory. The decision-table script then exposes conflicts and gaps, instead of you resolving them silently. If you need a resolved version for testing, make it a second spec (`DS-00x-resolved`) and cite the question that justifies the resolution.

### 4. Feed findings back

Script warnings are **requirement defects**, not noise:
- range gaps, unspecified ranges and open ends,
- decision-table gaps, conflicts and dead rules,
- unreachable states, dead ends, nondeterminism, invalid-transition cells.

Add each one to `qa/clarifications.md` as a question and link it from the requirement. Then design the affected tests with an explicit assumption.

### 5. Author the test cases (compact format)

Write `qa/test-cases.src.md` and convert it:

```bash
python scripts/qa_compact.py tc qa/test-cases.src.md --out qa/test-cases.json
```

```text
project: Online Mağaza – Kupon
language: tr
setup giris: Kullanıcı 'ayse.test@example.com' ile giriş yapmış
setup giris: 'YAZ10' kuponu aktif (%10, tavan 50 TL, asgari 100 TL)

## TC-001 | Kupon 100,00 TL sınırında uygulanır
req: REQ-002 | pri: h | pol: + | tech: bva | ref: DS-001 C-02
pre: @giris
pre: Sepet toplamı 100,00 TL
1. Kupon alanına kodu yaz, 'Uygula'ya tıkla [YAZ10] => 'Kupon uygulandı'; indirim -10,00 TL; toplam 90,00 TL
tags: regression | auto: yes, veri güdümlü | status: ready
```

The essentials, with details in `references/test-case-standard.md`:
- **One step, one action, one observable expected result.** Use concrete data and verbatim messages. Never write "works correctly".
- **Valid values may share a test. Invalid values never do** (single fault).
- Link every test to its requirements (`req:`), set the technique (`tech:`) and the design reference (`ref: DS-001 C-07`).
- Cover functional rules with both **positive and negative** tests.
- **Rate the priority of each test, not of the requirement.** Start one level below the requirement's risk. Only the happy-path proof and the prevention of the most damaging failure get the requirement's level. Boundary neighbours, extra representatives and message checks go lower. Error-guessing and exploratory tests are at most high.
- **One representative per partition, plus the boundary values.** Add another value from a covered partition only for a distinct, named risk (overflow, formatting).
- Put shared setup in `setup` blocks. A block may only hold state that is true for **every** test that uses it. If a test needs a different state (for example "coupon already used" instead of "coupon never used"), define a second block or write that precondition inline, and do not reference the contradicting block. Keep objectives short, or leave them out.
- Add error-guessing tests for the relevant categories, and exploratory charters (`tech: ex`) for high-risk areas with thin specifications.
- Tag `smoke` for the few tests that prove the feature basically works. Set `auto:` with a short reason.

### 6. Calibrate (at most 2 passes)

```bash
python ../tracing-requirements/scripts/build_rtm.py --requirements qa/requirements.json --tests qa/test-cases.json --out-dir qa
```

If the `tracing-requirements` skill is installed elsewhere, use its path. The script validates the schema and reports four kinds of problem:
- UNCOVERED and NO_NEGATIVE gaps,
- **PRIORITY_SKEW** (more than 20% critical, or more than 60% critical+high),
- **REDUNDANT** groups of tests from the same equivalence class.

Fix what it reports in the `.src.md` file, regenerate, and run it once more. If an item still stands after that, it is either a justified exception, which you record in the summary, or a question for the user. Do not loop further.

### 7. Summarize

Tell the user:
- The number of test cases, broken down by priority (with %), polarity and technique.
- The coverage for each requirement: the techniques used, and the counts of boundaries, decision columns, transitions and pairs.
- What was deliberately left out, and why.
- Any new questions.
- The next steps: the RTM (`tracing-requirements`) and export to Xray, Zephyr or Excel (`exporting-test-cases`).

## Files

- `scripts/qa_compact.py`: compact text ⇄ JSON, with validation, `setup` blocks and merging.
- `scripts/ep_bva.py`: partitions and 2/3-value boundaries; detects gaps, overlaps and open ends.
- `scripts/decision_table.py`: expansion, gaps, conflicts, dead rules, collapsing.
- `scripts/state_transition.py`: state table, model defects, 0/1-switch sequences, invalid transitions.
- `scripts/pairwise.py`: t-wise covering array with constraints and verification.
- `scripts/check_ids.py`: validates TCKN/VKN/IBAN test data and derives single-fault invalid variants (it never generates new valid IDs).
- `assets/spec-examples/`: one example spec per script.
- `references/technique-selection.md`: which technique to use when, risk-based depth, test budget.
- `references/techniques.md`: procedures, coverage measures and pitfalls for each technique.
- `references/test-case-standard.md`: fields, writing rules, priority calibration, review checklist, dedupe.
- `references/error-guessing-checklist.md`: fault taxonomy with a Turkish-locale focus.
- `references/data-model.md`: generated JSON schema; only needed for reading the JSON directly.
- `references/domains/fintech.md`, `references/domains/ecommerce.md`, `references/domains/health.md`, `references/domains/public-sector.md`: domain packs.
