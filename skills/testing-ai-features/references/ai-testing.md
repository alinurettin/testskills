# Testing AI features: guide

## Contents
1. What is different about AI features
2. Requirements and acceptance thresholds
3. Non-determinism: repeats, pass rates, flaky vs regression
4. Eval datasets and golden sets
5. The assertion ladder: deterministic, model-graded, human
6. RAG quality
7. Security: OWASP Top 10 for LLM Applications 2025
8. Agents and tool use
9. Bias, fairness and toxicity
10. Privacy and personal data
11. Cost, latency and resilience
12. Regression on model, prompt or data change
13. Monitoring in production
14. Regulation awareness (EU AI Act, KVKK/GDPR)
15. Reporting
16. Limits of `ai_eval.py`

---

## 1. What is different about AI features
| Classic feature | LLM feature | Consequence for testing |
|---|---|---|
| Same input → same output | Same input → varying output | Run each case several times and report a pass **rate**, not a single pass/fail |
| Behaviour is specified by code | Behaviour is steered by a prompt, a model version and data | A prompt edit, a model upgrade or a re-index is a release and needs regression |
| Input is data | Input can contain **instructions** (from users, documents, web pages, e-mails) | Prompt injection is the central security risk; test the indirect channels too |
| Wrong output often looks wrong | Wrong output looks fluent and confident | Check grounding and "I don't know" behaviour, not only the form of the answer |
| Expected result is exact | Many answers can be acceptable | Use deterministic checks where possible and calibrated rubrics for the rest |

Useful background:
- the ISTQB Certified Tester AI Testing (CT-AI) syllabus;
- ISO/IEC TR 29119-11:2020 (guidelines on testing AI-based systems);
- the NIST AI Risk Management Framework (AI RMF 1.0) and its Generative AI Profile (NIST AI 600-1);
- ISO/IEC 42001:2023 (AI management systems), when the organisation uses it.

## 2. Requirements and acceptance thresholds
Every acceptance criterion needs a **number and a denominator**. For example: "≥ 90% of golden-set cases pass in ≥ 4 of 5 runs", "0 of 50 injection cases × 10 runs leak the canary", or "p95 total latency ≤ 4 s at 20 concurrent users".

Questions to ask (the SKILL.md step 1 lists the core set):
- **Intents and scope:** the list of supported intents, and the expected behaviour for out-of-scope requests.
- **Languages:** TR, EN, mixed; formal register (siz) or informal (sen); ASCII Turkish accepted?
- **Sources of truth:** which documents, which version, and who approves the reference answers.
- **Unknown answers:** refuse, say "I don't know", hand over to a human, or answer from general knowledge?
- **Safety policy:** prohibited content categories and the expected response (refuse, redirect, warn).
- **Personal data:** what may be shown, to whom, after which authentication step. What is logged, and for how long.
- **Tools:** the list of tools, their permissions, which actions need confirmation, and whether the confirmation is enforced in code.
- **Budgets:** latency (time to first token, total), tokens, cost per request and per day, rate limits, timeouts, fallback.
- **Versions:** model ID and version, temperature and other parameters, and the prompt version. How changes are approved.
- **Per-category thresholds:** safety and privacy 100% over all runs; quality categories a rate agreed with the product owner.

If the product owner cannot give a number, propose one from a baseline run (for example "the current version scores 87%; accept ≥ 85% and no category drop over 5 points") and record it as a derived requirement to be confirmed.

## 3. Non-determinism: repeats, pass rates, flaky vs regression
- **Repeat runs.** Use at least 3 runs per case, and 5–10 for safety categories. Report `passed runs / evaluated runs` per case, and the mean of the case rates per category and overall.
- **Absence of failures is weak evidence.** If a case passes n of n runs, the 95% upper bound on its true failure rate is about 3/n (the "rule of three"). Ten clean runs still allow a failure rate of up to about 30%. For must-never-happen behaviours, add more *different* attack cases rather than only more runs of the same one.
- **Temperature and seed.** Temperature 0 and a `seed` parameter (where the provider offers one) reduce variation, but they do not make outputs deterministic (batching, hardware, provider updates). Test with the production settings. Use fixed settings for debugging and for comparing two prompt versions.
- **Flaky or regression?** A case that is flaky in both the old and the new version is unstable behaviour. Report it as a product risk, because users see the bad answer at that rate. A case that moves from 5/5 to 2/5 after a change is a regression candidate: rerun it with more runs before filing.
- **Noise between versions.** With N cases and a pass rate p, the standard error is about √(p(1−p)/N). At p = 0.9 and N = 100 it is 3 points, so a 95% interval is about ±6 points. A 2-point drop on 100 cases is usually noise. Compare the **same cases** across versions (a paired comparison: which cases changed from pass to fail?). Use a paired test (McNemar) or a bootstrap interval when the decision matters.
- **Do not hide flakiness with retries.** "Pass if any of 3 runs passes" measures the best case, but users get a random run.

## 4. Eval datasets and golden sets
- **Sources:**
  - anonymised real requests (logs, support tickets, search queries);
  - requirement-based cases (see the designing-test-cases skill: equivalence partitions of intents, boundaries of length and format);
  - adversarial cases (the seed, red-team sessions, incidents);
  - expert-written questions with reference answers.
- **Stratify** by intent, language (TR/EN/mixed, with and without Turkish characters), difficulty, user type and channel. Report rates per stratum, because an overall average hides a broken intent.
- **Size.** A few dozen cases per important intent is a practical start. Safety needs breadth: many different attack phrasings, not one phrasing run many times.
- **Versioning.** Keep the dataset in version control (`evals.jsonl`), review changes, and record the dataset version in every report. Never renumber IDs. Deprecate cases instead of deleting them.
- **Hold-out.** If prompts are tuned against the dataset, keep a hold-out part that nobody tunes against. Otherwise the score measures overfitting.
- **Reference answers** are approved by a domain expert and dated. They age when policies change, so review them with each policy change.
- **Turkish specifics:**
  - Morphology changes word forms (iade, iadesi, iadeyi), so match stems or regexes, not full words.
  - The I/ı and İ/i case mapping differs from English; `ai_eval.py` folds these.
  - Users often type ASCII Turkish (sifre, iade, odeme).
  - Code-switching (Turkish mixed with English terms) is common.
  - Turkish text often uses noticeably more tokens than English text of the same meaning, which affects cost and context limits.
- **Personal data:** synthetic only (see §10).

## 5. The assertion ladder: deterministic, model-graded, human
Climb only as far as needed.

**1. Deterministic checks** are fast, free, repeatable and explainable. Use them for:
- **format:** `json_valid`, `json_keys`, `max_chars`, `regex`;
- **labels:** `equals`, `one_of`, for classification;
- **required or forbidden content:** `contains`, `not_contains` (canaries, markers, attacker domains);
- **safety heuristics:** `refusal`, `no_pii`;
- **budgets:** `max_latency_ms`, `max_tokens`;
- **agent behaviour:** `tool_not_called`.

**2. Model-graded (LLM-as-judge)** is used for correctness against a reference, completeness, faithfulness to context, tone and policy compliance.
- Known biases:
  - position bias (in pairwise comparisons);
  - verbosity bias (longer answers score higher);
  - self-preference (a model rates its own family's output higher);
  - leniency.
- Mitigations:
  - binary or 3-point criteria with anchors;
  - one criterion per rubric;
  - a reference answer or the retrieved context in the judge prompt;
  - swapping the order in pairwise comparisons;
  - a judge from a different model family where possible;
  - temperature 0 for the judge.
- **Calibrate before trusting.** Have two humans label 30–50 outputs, measure human–human agreement, then judge–human agreement (percent agreement and Cohen's κ). Agree the target up front; ≥ 80% raw agreement or κ ≥ 0.6 is a common starting point. The judge cannot be expected to agree with humans better than humans agree with each other. Recalibrate when the judge model, the judge prompt or the product domain changes. See `assets/rubric-template.md`.

**3. Human review** is the ground truth for subjective quality and the only check for new failure types.
- Review a random sample every run (for example 10%).
- Review all failed and flaky safety cases.
- Review a stratified sample of passes, to catch false passes of the heuristics.

`ai_eval.py score` never counts `rubric` or `human` checks as passed. It lists them as pending, and a case that has only judgement checks gets no automatic verdict.

## 6. RAG quality
Test retrieval and generation separately. Otherwise a bad answer cannot be attributed to its cause.

| Metric | Question | How |
|---|---|---|
| Hit rate@k | Is at least one relevant chunk in the top k? | Label the relevant document or chunk IDs per question and compare with the retrieved IDs |
| Recall@k / MRR | How many relevant chunks are retrieved, and how high is the first one? | Same labels; MRR = mean of 1/rank of the first relevant chunk |
| Context precision | How much of the retrieved context is relevant (noise)? | Label the chunks, or use a judge per chunk |
| Context recall | Does the retrieved context contain everything the reference answer needs? | Split the reference into claims and check each against the context |
| Faithfulness / groundedness | Is every claim in the answer supported by the retrieved context? | Split the answer into claims and let a judge or a human check support; target a number (for example ≥ 95% of claims) |
| Answer relevance | Does the answer address the question? | Rubric |
| Citation correctness | Does each cited source exist, was it retrieved, and does it support the sentence it is attached to? | Deterministic existence check plus judge or human support check |
| "I don't know" behaviour | With no relevant context, does it abstain instead of inventing an answer? | Questions whose answer is deliberately absent from the index (seed: hallucination category) |

More checks:
- **Stale documents:** remove or update a document, re-index, and check the answer changes.
- **Conflicting documents:** check that the answer uses the newest or authoritative source.
- **Permissions (LLM08):** a user must not retrieve chunks from documents they cannot open. Test with two users and tenant-specific documents.
- **Injection through documents:** any ingested document is untrusted input (seed: `injection_indirect`).
- **Changes to chunking, embedding model, top-k or re-ranker** are releases: rerun the retrieval metrics.

Example frameworks teams use for these metrics are RAGAS, DeepEval, promptfoo and TruLens. They are not required; ask before installing anything.

## 7. Security: OWASP Top 10 for LLM Applications 2025
| ID | Risk | What to test | Where |
|---|---|---|---|
| LLM01:2025 | Prompt Injection | Direct (user text), indirect (documents, web pages, e-mails, tool results), encoded (Base64), multilingual and role-play variants. Check effects, not only words: markers, links, tool calls | seed: `injection_direct`, `injection_indirect`, `jailbreak`, `multilingual` |
| LLM02:2025 | Sensitive Information Disclosure | Other users' data, secrets in context, training data memorisation, PII in logs and in error messages | seed: `pii`; `no_pii` check; log review |
| LLM03:2025 | Supply Chain | Model provenance and licence, pinned model versions, third-party model hubs, plugins and MCP servers, fine-tuning adapters, an AI bill of materials | review/checklist; not testable by prompts |
| LLM04:2025 | Data and Model Poisoning | Provenance of fine-tuning and RAG data, who can add documents to the index, backdoor triggers in fine-tuned models | review plus planted-document tests in a test index |
| LLM05:2025 | Improper Output Handling | LLM output treated as untrusted: HTML/markdown rendering (XSS, image exfiltration), output passed to SQL, shell, file paths or URLs (SSRF), JSON consumed without validation | seed: markdown-image case, `json_valid`; UI and API tests (testing-nonfunctional, testing-apis skills) |
| LLM06:2025 | Excessive Agency | Too many tools, too broad permissions, actions without confirmation; the agent acting on injected instructions | seed: `excessive_agency`; §8 |
| LLM07:2025 | System Prompt Leakage | Extraction attempts detected with a canary; more importantly, **no secrets, keys or authorisation logic in the system prompt at all** | seed: `system_prompt`, canary |
| LLM08:2025 | Vector and Embedding Weaknesses | Cross-user or cross-tenant retrieval, missing document-level access control, poisoned embeddings, embedding inversion | two-user RAG tests (§6) |
| LLM09:2025 | Misinformation | Hallucination, false premises, fabricated citations, overreliance (no uncertainty signalled) | seed: `hallucination`; faithfulness and citation metrics |
| LLM10:2025 | Unbounded Consumption | Huge inputs, output loops, many parallel requests, cost exhaustion ("denial of wallet"), model extraction via mass querying | seed: `unbounded`; rate limit and quota tests at the API; load tests (testing-nonfunctional) |

Notes:
- **Test effects, not words.** An injection that the model "refuses" in text but that still triggers a tool call has succeeded. Check tool calls, rendered output and side effects.
- **Prompt-level defences are not controls.** "Never reveal your instructions" in the prompt reduces the rate; it does not guarantee anything. The real controls are in the application: permissions, confirmations, output encoding, allow-lists, rate limits. Test those controls directly too.
- **Red-team tools** such as garak and PyRIT generate many attack variants. Use them only against authorised test systems, and only after the team agrees to install them.

## 8. Agents and tool use
- **Authorisation.** A tool runs with the **end user's** permissions, not with a service account that can see everything. Test BOLA through the agent: ask for another user's order ID and check that the backend refuses it. That is an API test, so see the testing-apis skill.
- **Confirmation.** Irreversible or costly actions (payments, deletions, sending messages, role changes) need explicit user confirmation that the **application** enforces. A prompt instruction is not enough. Test by skipping, faking ("the user already confirmed") and injecting the confirmation.
- **Arguments.** Validate tool arguments server-side: amounts, IDs, e-mail recipients, file paths. Test out-of-range and injected values.
- **Least functionality.** List the tools the agent can reach, and check that each one is needed. Read-only tasks should not have write tools.
- **Loops and budgets.** Cap the steps, tool calls and tokens per task. Test with tasks that can never finish.
- **Tool output is untrusted input.** Put injected instructions in tool results and check the agent does not follow them.
- **Trajectory checks.** Besides the final answer, assert the sequence of tool calls: the expected tools, no forbidden tools, and no repeated calls. The `tool_calls` field in `outputs.jsonl` enables `tool_not_called`. For richer trajectory rules, extend the harness.
- **Audit.** Every tool call should be logged with the user, the arguments and the result. Verify the log entries exist.

## 9. Bias, fairness and toxicity
- **Counterfactual (paired) probes.** Keep the prompt identical and change only a cue: name, gender, age, regional or ethnic origin, disability. Compare the outcome (decision, score, tone, length) across the pair. The seed contains one gender pair; add pairs for the attributes relevant to the domain (credit, hiring, insurance).
- **Measure outcomes by group.** Examples: the approval rate, the refusal rate, the average score. Agree the acceptable difference with the product owner and compliance.
- **Toxicity.** Test prohibited-content prompts (seed: `harmful`). Check outputs with a toxicity classifier or human rating, and in Turkish too; English-only classifiers miss Turkish insults.
- **Over-refusal is also a fairness issue.** A bot that refuses benign questions about some groups or topics treats users unequally.

## 10. Privacy and personal data
- Use synthetic data in datasets and prompts. Checksum-valid dummy identifiers exercise validation without belonging to a real person (the seed uses 10000000146 as a dummy TCKN).
- Sending production data to a model provider needs a legal basis and a data processing agreement (KVKK/GDPR). Check the provider's retention and training-use settings.
- Check what the product logs: prompts, outputs, tool arguments. Personal data in logs needs masking and a retention limit.
- The `no_pii` check is a pattern heuristic. It detects e-mails, TR mobile and international phone numbers, checksum-valid TCKN, TR IBAN and Luhn-valid card numbers. It does not detect names, addresses or free-text health data; review those by hand.

## 11. Cost, latency and resilience
- Measure the time to first token and the total latency (p50, p95), input and output tokens, and the cost per request and per conversation. Report them per category, because long-context RAG answers cost far more than small talk.
- Budgets come from requirements. `score --max-p95-ms` and `--max-mean-tokens` gate on them; the `max_latency_ms` and `max_tokens` checks work per case.
- **Load.** The provider's rate limits (429), queueing, timeouts and retries with back-off. Check the fallback when the provider is down: a message, a cached answer or a handover, never a hang. Use k6 via the testing-nonfunctional skill, and agree limits with the provider first.
- **Denial of wallet.** Check the per-user and per-tenant quotas, and the maximum input size, at the API layer.

## 12. Regression on model, prompt or data change
- Treat as a release every change of:
  - the model or model version (including provider aliases like "latest");
  - the system prompt or prompt templates;
  - temperature or other parameters;
  - tool definitions;
  - the retrieval index, chunking, embedding model or re-ranker;
  - guardrail or filter configuration.
- Pin versions in production and record them in every output line.
- Run the full dataset with the same number of runs. Compare per case (pass → fail transitions) and per category with the previous report, and investigate every critical failure and every category drop larger than noise (§3).
- Providers deprecate models on a schedule. Plan the migration test before the deadline.
- For risky changes use a shadow or canary release: run the new version on a sample of production traffic, grade it, and compare before switching.

## 13. Monitoring in production
- **Sample conversations** (with consent and masking) and grade them with the calibrated rubric every week or every release.
- **Watch these rates:** refusals, "I don't know", fallbacks and handovers, errors and timeouts, thumbs-down, conversations abandoned after one answer.
- **Watch latency p95, tokens and cost** per day and per tenant, with alerts on budget breaches.
- **Detect drift:** new intents, new languages, a changing input length.
- **Incident loop:** every harmful, leaking or wrong answer reported by users becomes a new eval case (keep the ID, never delete) and a regression test.

## 14. Regulation awareness (EU AI Act, KVKK/GDPR)
Testers do not classify systems legally. They raise the question early and keep the evidence that compliance will need.
- **EU AI Act (Regulation (EU) 2024/1689)** uses risk classes:
  - **unacceptable-risk practices** are prohibited;
  - **high-risk systems** have obligations for risk management, data governance, logging, human oversight, accuracy, robustness and cybersecurity. Annex III lists use cases such as employment, education, access to essential services and creditworthiness assessment of natural persons;
  - **transparency obligations** apply, for example telling users that they are interacting with an AI system and marking AI-generated content;
  - **minimal-risk systems** have no specific obligations.

  Providers of general-purpose AI models have their own obligations. The obligations apply in phases, and the dates have been the subject of amendment proposals. **Check the current status and whether the use case is in scope with the compliance or legal team.** The test evidence in this skill (datasets, rates, versions, human review records) is the kind of documentation such assessments ask for.
- **KVKK / GDPR** apply to personal data in prompts, logs and training data, whatever the AI Act classification. Check AI-specific national rules with compliance as well.

## 15. Reporting
A useful AI eval report states:
- the model, prompt, dataset and harness versions, and the settings (temperature, top-p, seed);
- the runs per case, and the rates **with denominators** per category and overall, against the agreed thresholds;
- failed critical cases, with inputs, contexts, all outputs and the versions;
- flaky cases, and cases pending model or human grading (never merged into the pass count);
- latency p50/p95, tokens and cost;
- judge calibration results (agreement, date, judge version);
- the known limits of the heuristics used, and what was not tested (for example, LLM03 was reviewed but not tested).

Use the reporting-test-results skill for the completion report, and tracing-requirements for the RTM (`score --results` writes `qa/results.json`).

## 16. Limits of `ai_eval.py`
- It does not call models. The harness is the team's own.
- `refusal`, `no_pii`, the abstention regexes and the Turkish-character check are **heuristics**:
  - a refusal phrased unusually is missed;
  - a "sorry, but…" followed by compliance is counted as a refusal;
  - names and addresses are not detected as PII.

  Read the failures, and review a sample of the passes.
- Case-insensitive matching folds Turkish diacritics (ş→s, ı/İ→i). This is right for canaries and keywords but can over-match short words; use `case_sensitive: true` for exact matching.
- The overall rate is the mean of the per-case rates (every case weighs the same). Weight important intents by adding more cases, or set per-case `min_pass_rate`.
- The seed is a **starting point**, about 34 cases. A real safety suite needs many more attack variants per category, adapted to the product's tools, data and policy.
