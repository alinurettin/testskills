---
name: analyzing-requirements
description: Turns user stories, PRD/SRS documents or tickets into atomic, testable requirements with REQ IDs, ISO 29148 quality review, contradiction and gap detection, risk scores and clarification questions. Use when requirements need review before test design. Triggers include requirements analysis, user story review, acceptance criteria, missing requirements; Turkish "gereksinim analizi", "gereksinimleri incele", "kabul kriteri yaz".
license: MIT
metadata:
  suite: qa-suite
  version: "0.8.0"
---

# Analyzing requirements

The goal is to turn whatever the stakeholder gave you into a **set of requirements that can be tested**, and to make visible everything that stops that from happening. An ambiguity caught here costs one question. Caught in production, it costs an incident.

Three principles govern this skill:

1. **Surface, don't invent.** Never fill a gap silently. Ask a question, or propose a *derived* requirement that is explicitly marked unconfirmed.
2. **Traceability from the first minute.** Every requirement gets a stable ID and a `source`. Everything downstream depends on these IDs.
3. **Proportion.** A single story does not need 80 questions and 20 invented requirements. Calibrated risk and a focused question list are more useful than exhaustive ones. The team has to read and answer what you produce.

## Language

Write all artifacts in the user's language: Turkish if the user writes Turkish, otherwise English, unless the user asks for something else. IDs, field keys, enum values and rule codes stay in English.

## Modes and budget

| Mode | When | Completeness walk | Typical output for one story (5–8 ACs) |
|---|---|---|---|
| **Light** | Small or clear scope, or analysis as the first step of test design | 3–5 most relevant areas from the quick list below | 8–15 REQs (≤ 6 derived), 6–12 questions |
| **Full** | The user explicitly asks for a review, or the scope is large, regulated or high-risk | Relevant areas of `references/implicit-requirements.md` + `references/nfr-checklist.md` | Scales with scope; state the counts |

Going beyond the budget is fine when the input really demands it. Say why.

## Reading plan (keep context lean)

- **Light mode:** this file is enough. Open `references/quality-criteria.md` only if you need the full writing rules.
- **Full mode:** also read `references/quality-criteria.md`, and the relevant sections of `references/implicit-requirements.md` and `references/nfr-checklist.md`.
- **When proposing rewrites:** read `references/ears-and-stories.md` (EARS patterns, Gherkin TR/EN).
- **Domain packs, in both modes:** when the product is in banking/payments, e-commerce, health, the public sector, insurance/pensions or telecommunications, read the matching pack in `references/domains/` and use its implicit-requirements checklist and regulations list during the completeness walk. The packs are `fintech.md`, `ecommerce.md`, `health.md`, `public-sector.md`, `insurance.md` and `telecom.md`.
- **Compact format syntax:** run `python scripts/qa_compact.py --help`. You do not need `references/data-model.md` unless you read the JSON directly.

## Inputs this skill handles

- User stories, epics, acceptance criteria, Jira or Azure DevOps tickets.
- PRD, BRD, SRS or FSD documents, meeting notes and emails. Extract the text from .docx or .pdf first.
- UI mockups and screenshots: cross-check them against the text. A UI element with no requirement is a finding.
- OpenAPI specifications: each endpoint, parameter constraint and error code is a requirement candidate.
- An existing `qa/requirements.json`: re-analyse it and increment `version`.

## Workflow

```
- [ ] 1. Scope and context captured
- [ ] 2. Requirements normalized (qa/requirements.src.md → JSON)
- [ ] 3. Linter run and findings triaged
- [ ] 4. Quality + contradiction review
- [ ] 5. Completeness walk (light or full)
- [ ] 6. Risk scored with the anchors
- [ ] 7. Clarification log written
- [ ] 8. Report and summary
```

### 1. Capture scope and context
Establish the product, the feature boundary, the actors, the platforms and the domain from the input. Ask the user only about things that genuinely block you, at most 3 questions. Otherwise state your assumptions and continue.

### 2. Normalize into atomic requirements
Write `qa/requirements.src.md` in the compact format, then convert it:

```bash
python scripts/qa_compact.py req qa/requirements.src.md --out qa/requirements.json
```

```text
project: Online Mağaza – Kupon
language: tr

## REQ-002 | 100 TL asgari sepet tutarı
type: business-rule | pri: h | risk: 3x3 Eşik hatası gelir kaybı | src: US-42 AK-1 | ext: SHOP-42 | status: cn
text: Sepet tutarı 100 TL ve üzerindeyse geçerli kupon uygulanır.
ac: Diyelim ki sepet 100,00 TL, Eğer ki YAZ10 uygulanırsa, O zaman indirim 10,00 TL olur
q: Q-002 | derived: no
```

- **Split compound statements.** Each REQ must be able to pass or fail on its own. Link the split parts with `parent:` or a shared `src:`.
- **Keep the original wording in `text:`.** Put your proposed rewrite in `notes:` or `ac:`.
- **Treat an item that is really an open question** ("Misafir kullanabilir mi? (belirlenecek)") as a question, not as a requirement.
- **Keep source IDs** such as FR-12 or a Jira key in `ext:`.

### 3. Run the linter, then triage
```bash
python scripts/lint_requirements.py qa/requirements.json --out qa/design/lint-report.md
```
The linter is heuristic and works in Turkish and English. It flags:
- vague terms, escape clauses, open lists and TBDs,
- unmeasured performance words and compound statements,
- stories without acceptance criteria, near-duplicates and ID problems.

Confirm or dismiss each finding in context, and report how many you dismissed. The linter cannot see contradictions, missing requirements or wrong logic. Those need steps 4–5.

### 4. Quality and contradiction review
Check each requirement: is it unambiguous, complete, singular, verifiable, feasible and consistent? Then scan the whole set:
- **numbers:** limits, amounts, durations. The same concept must have the same value everywhere;
- **enumerations:** roles, statuses, methods. Is every value handled by the rules?
- **permissions:** who may do what;
- **states:** do all requirements agree on the allowed transitions?

A rule that applies to a value another rule forbids is a **contradiction**. Record it as critical. Examples: "credit card ≥ 500 TL shows installments" vs "foreign cards: no installments"; "registered customers" vs "can guests use it?".

### 5. Completeness walk: find what nobody wrote
**Light mode:** walk this quick list and keep only what matters for the feature:
1. Invalid input and error messages
2. Roles and permissions, including direct URL/API access
3. States and invalid transitions, double submit, concurrency
4. Money, time and locale: rounding, time zone, inclusive or exclusive limits, Turkish characters
5. Integrations: timeout, failure and retry
6. Non-functional: measurable performance, security baseline, accessibility (WCAG 2.2 AA), privacy (KVKK/GDPR)

**Full mode:** walk the relevant areas of `references/implicit-requirements.md` and `references/nfr-checklist.md`.

**Questions vs derived requirements.** Prefer a question. Create a **derived requirement** (`derived: yes`, `status: cn`) only when both of these hold:
- it will get tests of its own, and
- a sensible default exists that the stakeholder only needs to confirm.

Everything else is a question. Group minor implicit expectations into one derived requirement rather than creating one per detail.

### 6. Score risk with anchors
Score each requirement with `risk: LxI rationale`, where L is likelihood and I is impact, each 1–5. Use the anchors below. **When in doubt, choose the lower score and say why.** Depth and priorities downstream multiply whatever you choose here.

| Score | Impact (I) | Likelihood (L) |
|---|---|---|
| 5 | Money wrongly moved **at scale**, a legal or regulatory breach, a personal or payment data leak, a safety hazard | New, complex logic with several integrations and unclear specification |
| 4 | Core journey blocked for many users; significant revenue loss | Complex rule set, or an unclear specification |
| 3 | Important function wrong, but a workaround exists or few users are affected | Moderate complexity |
| 2 | Minor function degraded; mostly cosmetic effect on business | Simple, well-understood logic |
| 1 | Cosmetic | Trivial or reused, proven logic |

The score is L × I, banded as 1–4 low, 5–9 medium, 10–16 high, 17–25 critical. **Expect the distribution** to be: about ≤ 20% critical, most requirements medium or high. If more than a third are critical, recalibrate before handing off.

### 7. Write the clarification log
Write `qa/clarifications.md` from `assets/clarifications-template.md`. Every question gets:
- concrete **options**,
- a **default assumption**,
- **why it matters** for testing,
- **who** should answer it.

Put the blocking questions first. Merge questions that one decision answers. Aim for questions that a product owner can answer in a few minutes each.

Rules for every question:
- **Link it to at least one REQ.** A set-level question links to the requirements it affects most.
- **Give either options or a default.** If you genuinely cannot propose one ("which fields does the form have?"), turn it into a closed question. Offer a draft list to confirm, for example "Proposed: name, TCKN, income, term 12–60 months; confirm or correct".

### 8. Report and hand off
In **full mode**, write `qa/analysis-report.md` from `assets/analysis-report-template.md`. Leave out any section that does not apply. In **light mode**, the report can be a short section of the chat summary.

In chat, give:
- the counts,
- the top 3–5 risks,
- the blocking questions,
- a recommendation: proceed, proceed with assumptions, or wait.

If test cases come next, continue with the `designing-test-cases` skill.

## Quality bar

- Every REQ has an ID, source, type, priority, risk and status. No REQ contains two obligations.
- Every contradiction found is logged as a critical finding with a question.
- Every confirmed vague term has either a measurable rewrite or a question.
- Derived requirements are few, marked `derived: yes`, and each one will get tests.
- The risk distribution is plausible, and the counts in the summary are real.

## Files

- `scripts/qa_compact.py`: compact text ⇄ JSON (`req` / `tc`), with validation and merging.
- `scripts/lint_requirements.py`: heuristic TR/EN linter, output as Markdown or JSON.
- `references/quality-criteria.md`: 29148 characteristics, writing rules, severity guide, contradiction scan.
- `references/implicit-requirements.md`: discovery questions by area, and domain packs.
- `references/nfr-checklist.md`: ISO 25010:2023 with measurable examples, and WCAG/OWASP baselines.
- `references/ears-and-stories.md`: EARS (EN/TR), INVEST, Gherkin (EN/TR), rewrites.
- `references/domains/fintech.md`, `references/domains/ecommerce.md`, `references/domains/health.md`, `references/domains/public-sector.md`, `references/domains/insurance.md`, `references/domains/telecom.md`: domain packs covering regulations, implicit requirements, high-risk rules, test data and typical defects.
- `references/data-model.md`: the generated JSON schema.
- `assets/analysis-report-template.md`, `assets/clarifications-template.md`: bilingual templates.
