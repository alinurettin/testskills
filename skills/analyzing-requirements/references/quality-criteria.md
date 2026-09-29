# Requirement quality criteria

This is a working checklist based on the characteristics in ISO/IEC/IEEE 29148:2018 and on common requirement-writing rules such as the INCOSE Guide to Writing Requirements. It is a paraphrase to apply, not a copy of either standard.

## Contents
1. Characteristics of an individual requirement
2. Characteristics of a requirement set
3. Writing rules (detectable defects)
4. Severity guide
5. How to phrase a finding

---

## 1. Characteristics of an individual requirement

For each requirement, ask the detection question. A "no" is a finding.

| Characteristic | Detection question | Typical defect | Test impact |
|---|---|---|---|
| **Necessary** | Would anything be lost if this requirement were deleted? Can it be traced to a stakeholder need? | Gold plating, a design idea written as a requirement | Wasted test effort |
| **Appropriate** | Is it at the right level (business, system or component) for this document? | UI pixel detail in a business requirement | Tests at the wrong level |
| **Unambiguous** | Would two testers write the same expected result? | Vague terms, pronouns, undefined jargon, "and/or" | Contradictory verdicts |
| **Complete** | Are all conditions, inputs, outputs, error cases and units stated? | Missing error behaviour, missing units, TBD | Missing negative tests |
| **Singular** | Does it state exactly one capability or constraint? | "... and also ...", two obligation verbs | A test cannot pass or fail cleanly |
| **Feasible** | Can it be built with the known technology, budget and constraints? | "100% availability", "zero latency" | Untestable targets |
| **Verifiable** | Is there a finite, objective way to show it holds (inspection, analysis, demonstration or test)? | "user-friendly", "never fails" | No expected result |
| **Correct** | Does it match what the stakeholder actually needs? | Wrong rule copied from an old system | Tests confirm the wrong behaviour |
| **Conforming** | Does it follow the agreed template, terms and glossary? | Mixed terms ("client", "customer", "user") for the same actor | Hidden duplicates |

## 2. Characteristics of a requirement set

Check these across all requirements together:

- **Complete**: Every stakeholder need, user role, state, error path and non-functional concern is covered. Walk `implicit-requirements.md` and `nfr-checklist.md` to find what is missing.
- **Consistent**: No two requirements contradict each other. The same term always means the same thing. Units and formats agree (for example, 24-hour time in one place and 12-hour time in another is a defect). Look especially for conflicting numbers (limits, timeouts, prices) and conflicting permissions.
- **Feasible**: The set as a whole fits within the constraints. Many individually feasible performance targets can be infeasible together.
- **Comprehensible**: A new team member can understand the set without the author present. Every acronym and domain term is in a glossary.
- **Able to be validated**: Stakeholders can confirm that the set, once met, solves their problem.

**Contradiction scan (do this explicitly):**
1. Collect every number (limits, amounts, durations, counts) and every enumeration (roles, statuses, payment methods). Check the same concept has the same value everywhere.
2. For each actor, list the actions they are allowed and forbidden to take. Look for overlaps.
3. For each status or state, check every requirement agrees on which transitions are allowed.

## 3. Writing rules (detectable defects)

The linter (`scripts/lint_requirements.py`) automates the rules marked ⚙. Check the rest by reading.

| # | Rule | Example of violation | Better |
|---|---|---|---|
| W1 ⚙ | Avoid vague adjectives and adverbs | "The page loads quickly" | "The page's Largest Contentful Paint is ≤ 2.5 s at p75 on 4G" |
| W2 ⚙ | Avoid escape clauses | "if possible", "mümkünse" | State the condition, or drop it |
| W3 ⚙ | Avoid open-ended lists | "credit card, EFT etc." | List them all: "credit card, EFT, wallet" |
| W4 ⚙ | No placeholders | "TBD", "belirlenecek" | A value, or an open question with an owner and date |
| W5 ⚙ | One requirement per statement | "shall validate and shall notify" | Split into two REQs |
| W6 ⚙ | Quantify performance, capacity and time | "reasonable response time" | Threshold + unit + load + percentile |
| W7 ⚙ | Use positive statements where possible | "shall not allow invalid input" | "shall reject input that … with message …" |
| W8 ⚙ | Question universal quantifiers | "all users", "always" | Name the population and the conditions |
| W9 | Use active voice and name the actor | "The report is generated" | "The system generates the report when …" |
| W10 | Use defined terms consistently | "order" and "purchase" interchangeably | One glossary term |
| W11 | Give units and formats | "timeout of 30" | "30 seconds" |
| W12 | Avoid design detail unless it is a real constraint | "stored in a Redis cache" | "retrievable within 200 ms" (unless Redis is truly mandated) |
| W13 | State the trigger or condition explicitly | "sends an email" | "When the order is shipped, the system sends …" |
| W14 | Define the error or unwanted behaviour | only the happy path | "If the payment is declined, then …" |
| W15 | Avoid comparatives without a reference | "faster than before" | "≤ 1 s (baseline v2.3: 2.4 s)" |
| W16 | Avoid "and/or", "ve/veya" | "email and/or SMS" | State the allowed combinations |
| W17 | Resolve pronouns | "it", "they", "this" | Repeat the noun |
| W18 | Remove rationale from the statement | "…, because users complain" | Move it to `notes` |

## 4. Severity guide

- **critical**: The requirement cannot be tested, or the test would be meaningless. Examples: a TBD, a contradiction with another requirement, the core rule missing. Blocks test design for that requirement.
- **major**: Testable only on an assumption. Examples: a vague threshold, missing error behaviour, a compound requirement. Test design can continue with a documented assumption.
- **minor**: Style or clarity problems that are unlikely to change test verdicts.
- **info**: Worth knowing, no action required.

## 5. How to phrase a finding

A useful finding has:
- **location**: the requirement ID and the quoted fragment
- **problem**: which characteristic or rule is broken
- **impact**: what goes wrong in testing, development or production
- **proposal**: a concrete rewrite, or a question with options

> **REQ-006**, "kabul edilebilir düzeyde yanıt süresi" (vague term, not verifiable).
> Impact: no pass/fail threshold, so the performance test has no oracle.
> Proposal: "Sepet sayfası, 200 eşzamanlı kullanıcı altında p95 ≤ 1,5 s içinde yanıt vermelidir." (Question Q-007 to confirm the threshold and load.)
