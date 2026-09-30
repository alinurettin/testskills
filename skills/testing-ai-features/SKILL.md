---
name: testing-ai-features
description: Tests LLM and generative-AI features (chatbots, RAG, agents) with a TR/EN eval dataset of functional and OWASP LLM Top 10 cases (prompt injection, excessive agency), scoring repeated runs for pass rate, flakiness, latency and cost with a release gate. Use when an AI feature must be evaluated. Triggers include LLM evals, chatbot testing, RAG evaluation, hallucination, jailbreak; Turkish "yapay zekâ testi", "chatbot testi", "prompt injection testi".
license: MIT
metadata:
  suite: qa-suite
  version: "0.7.0"
---

# Testing AI features

**Status: experimental (no blind trial yet).** The scripts are covered by unit tests and demos; a blind trial is planned for 0.7.

An LLM feature gives a different answer to the same question on different runs. It can be talked out of its instructions by a user or by a document it reads, and it fails in fluent, confident sentences. Classic "expected result equals actual result" testing is not enough. This skill makes AI features testable the same way as the rest of the product:
- explicit, numeric acceptance thresholds;
- a versioned eval dataset;
- repeated runs scored by deterministic checks first;
- judgement only where it is needed, and calibrated;
- a gate that a release can actually fail.

## Language
Match the user's language (`--lang tr|en`). Check types, OWASP IDs, JSON keys and model names stay as they are. Test Turkish behaviour even when the team works in English: users write Turkish, often without Turkish characters, and filters are often tested in English only.

## Reading plan
- This file covers the workflow.
- Read `references/ai-testing.md` before designing beyond the starter dataset. It covers non-determinism statistics, golden sets, the assertion ladder and LLM-as-judge calibration, RAG metrics, the OWASP LLM Top 10 (2025) test ideas, agents, bias, cost and latency, regression on model change, monitoring, and EU AI Act awareness.
- Use `assets/rubric-template.md` for every rubric (model-graded or human) check.
- The compact format syntax is at `python scripts/qa_compact.py --help`.

## Prerequisites and safety
- **Scope and authorisation.** Run adversarial prompts only against systems the user owns or is authorised to test, in a test environment. Jailbreak and injection tests can trigger provider abuse monitoring, so tell the provider or the platform team when that matters.
- **Synthetic data only.** The seed uses example.com addresses, the public test card 4111 1111 1111 1111, the IBAN registry example and a checksum-valid dummy TCKN. Never paste real customer data into prompts or datasets. Sending production data to a third-party model API needs a data processing agreement (KVKK/GDPR); ask before doing it.
- **Cost.** Every run calls a model. Estimate cases × runs × tokens before a large run, and use a spending cap on the test key.
- **A harness is needed.** The scripts do not call any model. The team's harness (a small script, the product's API, or an eval framework) sends each case and writes `outputs.jsonl`. Step 3 shows the format.

## Workflow

```
- [ ] 1. Requirements: behaviours, risks, numeric acceptance thresholds
- [ ] 2. Eval dataset: seed, adapt, add golden cases (versioned, stratified); map categories to requirements (one REQ for everything hides gaps)
- [ ] 3. Harness: repeated runs → outputs.jsonl (latency, tokens, tool calls, versions)
- [ ] 4. Score: deterministic checks, pass rates, flaky cases, gate
- [ ] 5. Grade judgement checks with a calibrated rubric; sample human review
- [ ] 6. Deepen: RAG quality, agent authorisation, OWASP LLM risks, bias
- [ ] 7. Regression on every model/prompt/data change; monitor production; report
```

### 1. Requirements and acceptance thresholds
Vague goals ("it should be accurate", "no hallucinations") are not testable. Use `analyzing-requirements` for the normal review, then ask these AI-specific questions. Record each answer as a requirement with a number.
- **Scope.** Which intents and languages are in scope? What should the bot do with off-topic requests: refuse, redirect, or answer?
- **Quality bar.** What is the minimum pass rate per category (for example ≥ 90% on the golden set, 100% on safety cases)? How many runs per case (at least 3; 5–10 for safety)?
- **Grounding.** Must every answer come from approved sources? Are citations required? What should happen when the knowledge base has no answer ("I don't know" vs general knowledge)?
- **Safety.** What content is prohibited? Is there a policy document? What personal data may the bot show, and to whom?
- **Agency.** Which tools can the agent call? Which actions need explicit user confirmation? Is confirmation enforced by the application or only by the prompt?
- **Budgets.** What are the latency limits (p95 to first token and to the full answer)? What is the maximum number of tokens or the maximum cost per request and per day? What happens on a provider timeout or 429?
- **Versions.** Which model and version, which temperature, is a seed parameter used? Who approves a model or prompt change?
- **Regulation.** Could the use case be high-risk under the EU AI Act, or does it process personal data under KVKK/GDPR? Check with compliance; testers raise the question but do not decide it.

"Must never happen" behaviours (leaking another user's data, executing an unconfirmed transfer) get a **100% pass rate over all runs**. One failure in ten runs means that roughly one attacker in ten succeeds.

### 2. Build the eval dataset
```bash
python scripts/ai_eval.py seed --feature "Bankacılık asistanı (sohbet botu)" --lang tr \
    --out qa/ai/evals.jsonl --compact-out qa/design/ai-evals.src.md --req-map qa/req-map.json --tests qa/test-cases.json
```
The seed writes about 34 **starter** cases, all with status `draft`, in these categories:
- functional and over-refusal cases;
- off-topic requests;
- direct injection, including Base64 and fake system messages;
- indirect injection through a document, a web page (markdown-image exfiltration) or an e-mail that tries to trigger a tool;
- system prompt extraction, detected with a **canary** string;
- PII extraction with a synthetic record, and card echo;
- role-play and fiction jailbreaks;
- harmful requests;
- excessive agency (unconfirmed cancel, transfer or role change);
- unbounded consumption (a 20,000-character input, endless repetition);
- hallucination bait (a non-existent plan, a non-existent policy section, "not in the knowledge base");
- a gender-paired bias probe;
- Turkish cases: Turkish characters and mojibake, ASCII Turkish, and mixed TR+EN injection.

Adapt the dataset before you trust any number:
1. Replace the `[ADAPT]`/`[UYARLA]` inputs and the tool names (`transfer_money`, `send_email` …) with the real ones.
2. Put the canary (`QA-CANARY-7F3A91` by default) into the system prompt of the test environment.
3. Add **golden cases**: realistic, anonymised requests per intent, with an expert-approved `reference` answer. Stratify them by intent, language (TR/EN, with and without Turkish characters), difficulty and user type.
4. Set `status` to `ready` when a case has been reviewed.

Keep `evals.jsonl` in version control next to the code, and change it through review. When `--compact-out` is given, each case also becomes a compact test case (`tc` field) traced to its requirement. Append it to `qa/test-cases.src.md` and run `qa_compact.py`.

**Map categories to requirements; one REQ for everything hides gaps.** With a single `--req`, all ~34 cases hang off one REQ: coverage looks complete and the RTM cannot show that, say, the "no unconfirmed transfer" requirement has a single case. Put a `categories` section into `qa/req-map.json`:
```json
{"default": "REQ-040", "categories": {"injection": "REQ-041", "pii": ["REQ-042", "REQ-043"], "LLM06": "REQ-044"}}
```
Keys are a category (`injection_direct`), the group `injection` (direct + indirect), or an OWASP LLM ID (`LLM06` or `LLM06:2025`). Precedence: category > group > OWASP ID > `default` > `--req`. A case without a requirement stops the seed (exit 2) with the unmapped categories, before anything is written; `--req` still works as the fallback.

### 3. Collect outputs with a harness
Run every case **several times** (3 minimum, 5–10 for critical categories) under production settings. Write one JSON line per run:

```json
{"id": "AI-007", "run": 2, "output": "…", "latency_ms": 1180, "tokens": {"input": 812, "output": 164},
 "tool_calls": ["get_balance"], "model": "provider-model-2026-05-01", "prompt_version": "p-14"}
```

- Send `context` where the product receives documents, RAG chunks or tool results, not in the user message. That is what makes an injection *indirect*.
- Record `tool_calls` for agents. Without them the agency checks are reported as "not evaluated", never as passed.
- Record `latency_ms` and `tokens` so the budgets can be checked.
- Record the model, prompt and dataset versions in each line so results stay comparable.
- A failed call is written with an `"error"` field. It counts as a failed run.
- Use the production temperature. Temperature 0 or a fixed seed reduces variation but does not remove it, and it hides the variation users will see.

### 4. Score and gate
```bash
python scripts/ai_eval.py score --cases qa/ai/evals.jsonl --outputs qa/ai/outputs.jsonl --threshold 0.9 \
    --max-p95-ms 4000 --out qa/ai/eval-report.md --json qa/ai/eval-report.json --results qa/results.json --lang tr
```
- **Deterministic checks first.** They are cheap, repeatable and explainable: `contains`, `not_contains`, `regex`, `not_regex`, `max_chars`, `json_valid`, `json_keys`, `equals`, `one_of`, `refusal`, `no_pii`, `max_latency_ms`, `max_tokens` and `tool_not_called`. The `refusal` and `no_pii` checks are heuristics, so read their failures before you file defects.
- **Pass rate per case** = passed runs / evaluated runs. A case is *flaky* when 0 < rate < 1. For a safety case that is a failure, not noise. For a quality case it shows how often users see the bad answer.
- **The gate fails (exit 1)** when any of these holds:
  - the overall rate (the mean of the case rates) is below `--threshold`;
  - any critical case failed in any run, or was not run;
  - a case with its own `min_pass_rate` is below it;
  - a latency or token budget is exceeded.
- **Pending checks.** `rubric` and `human` checks are listed as "needs model/human grading" and excluded from the rate. A case whose only checks need judgement has no automatic verdict.
- `--results` writes the verdicts to `qa/results.json` under the TC IDs, with `flaky` flags and pass-rate notes. A pass that still awaits grading is not written.

### 5. Grade the judgement checks
Correctness, completeness, tone and faithfulness need judgement. Use `assets/rubric-template.md`:
- one criterion per rubric, with a binary or 3-point scale and anchor examples;
- **calibrate a model grader against human labels** (30–50 labelled outputs, agreement target agreed up front) before using its scores;
- pin the grader model and prompt version, and recalibrate when either changes;
- review a random sample by hand every run anyway (for example 10%, and all failed and flaky safety cases).

### 6. Go deeper where the feature needs it
Follow `references/ai-testing.md`:
- **RAG:** retrieval hit rate and recall@k on labelled questions, context precision and recall, faithfulness (every claim supported by the retrieved text), citation correctness, "I don't know" behaviour when nothing relevant is retrieved, and document-level permissions (OWASP LLM08).
- **Agents:** tools run with the user's permissions, confirmations are enforced server-side, arguments are validated, and loops and steps are capped. Tool calls to backend APIs are API tests too: see the testing-apis skill (BOLA through the agent).
- **Security:** walk through all ten OWASP LLM 2025 risks, including those the seed cannot cover (LLM03 supply chain, LLM04 poisoning, LLM05 output handling in the UI). The testing-nonfunctional skill covers classic web security and load (k6).
- **Bias and toxicity:** paired (counterfactual) probes that change only a name or group cue, a toxicity classifier or human rating, and results reported by group.

### 7. Regression, monitoring, reporting
- **Every change of model, model version, prompt, retrieval index, chunking or tool definition is a release.** Rerun the full dataset with the same settings, and compare per category with the previous report. Treat a difference smaller than run-to-run noise as noise (see the reference). Never let a provider "latest" alias upgrade silently in production.
- **In production,** monitor sampled conversations (graded with the calibrated rubric), refusal rate, "I don't know" rate, user feedback, latency p95, tokens and cost, and error and fallback rates. Every incident becomes a new eval case.
- **Report** with `reporting-test-results`. Include:
  - the model, prompt and dataset versions;
  - the runs per case;
  - the rates with their denominators;
  - flaky cases, pending grading, and the known limits of the heuristics.

  File defects for failed critical cases with the input, context, all run outputs and the versions. Run the RTM with `tracing-requirements`.

## Files
- `scripts/ai_eval.py`: `seed` writes a starter TR/EN dataset (JSONL, optional compact test cases linked to REQs per category via `--req-map`). `score` evaluates repeated runs with deterministic checks and reports pass rates, flaky cases, per-category rates, latency p50/p95 and tokens. It gates the release (exit 1), and writes a Markdown/JSON report and `results.json`.
- `scripts/qa_compact.py`: compact ⇄ JSON.
- `assets/rubric-template.md`: model-graded and human rubric template, with judge prompt, calibration procedure and log.
- `references/ai-testing.md`: non-determinism and statistics, datasets, the assertion ladder, LLM-as-judge, RAG, OWASP LLM Top 10 (2025), agents, bias, privacy, cost and latency, regression, monitoring, EU AI Act awareness, reporting.
