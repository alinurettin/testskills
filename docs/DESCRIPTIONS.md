# Skill descriptions: keep them short

Every skill's `name` and `description` sit in an always-on skill listing that Claude reads before it picks a skill. In Claude Code that listing has a **character budget of 1% of the model's context window**. When the listing overflows, Claude Code drops descriptions, **starting with the skills the user invokes least**. On a fresh install nobody has invoked anything yet, so which QA Suite skills lose their description is effectively arbitrary, and a skill without a description rarely triggers. Each entry is also capped at 1,536 characters no matter the budget. Source: [Claude Code docs, "Skill descriptions are cut short"](https://code.claude.com/docs/en/skills).

QA Suite shares that budget with every other skill the user has installed. So its descriptions have to be short.

## Limits

| Rule | Limit |
|---|---|
| Total across all 17 skills | **≤ 7,500 characters** |
| One description | **≤ 480 characters** (the spec maximum is 1,024; do not use it) |
| Frontmatter | one line, `description:` followed by a plain (unquoted) value |

Measure after every change:

```bash
python tools/validate_skills.py        # prints desc=<chars> per skill; must end with 0 errors
python -c "import glob,re;print(sum(len(re.search(r'^description:\s*(.+)$',open(p,encoding='utf-8').read(),re.M).group(1).strip()) for p in glob.glob('skills/*/SKILL.md')))"
```

## Shape of a description

```
<What it does, key use case first>. Use when <situation>. Triggers include <3-6 English terms>; Turkish "<2-4 short Turkish phrases>".
```

- Third person ("Designs…", "Tests…"). Say **what** the skill does and **when** to use it.
- Put the key use case in the first sentence: if anything gets cut, it is the end.
- No XML or HTML tags (the validator rejects them).
- Keep the value valid plain YAML: no `: ` (colon plus space) and no ` #` inside it, and do not start it with a quote.
- Keep it true to the SKILL.md body. Do not advertise a feature the skill does not have (for example, do not promise Excel import in a skill whose importer reads only CSV; `reviewing-test-cases` reads .xlsx directly since 0.7.0).

## Non-overlap rules

Two skills that claim the same trigger term compete for the same request. Each trigger term belongs to exactly one skill:

| Term | Only in | Others may say |
|---|---|---|
| IDOR / BOLA, API authorization | `testing-apis` | nothing |
| WCAG, accessibility, a11y, erişilebilirlik | `testing-nonfunctional` | `testing-mobile-apps` may say "mobile accessibility (TalkBack/VoiceOver)" |
| regression selection, regresyon seçimi | `tracing-requirements` | – |
| Excel/xlsx **import** | `reviewing-test-cases` | `exporting-test-cases` keeps "export to Excel" |
| end-to-end QA package, baştan sona | `qa-orchestrator` (end-to-end packages only) | – |
| Playwright | `automating-with-playwright` | `writing-bdd-scenarios` names the tool `playwright-bdd` |
| Xray, Zephyr, TestRail | `exporting-test-cases` | – |
| RTM, traceability, test coverage | `tracing-requirements` | – |
| test data, masking, KVKK | `preparing-test-data` | – |
| k6, performance, load testing, security testing | `testing-nonfunctional` | mobile says "OWASP MASVS", AI says "OWASP LLM Top 10" |
| release readiness | `reporting-test-results` | – |

Before adding a trigger, search the other 16 descriptions for it. If it is already there, pick a more specific term, or leave it to the skill that owns it.

## Before and after (0.6.0 → 0.7.0)

| Skill | Before | After |
|---|---:|---:|
| analyzing-requirements | 894 | 429 |
| automating-with-playwright | 852 | 415 |
| designing-test-cases | 900 | 435 |
| exporting-test-cases | 817 | 419 |
| planning-tests | 708 | 429 |
| preparing-test-data | 1,002 | 433 |
| qa-orchestrator | 954 | 416 |
| reporting-test-results | 773 | 432 |
| reviewing-test-cases | 851 | 432 |
| running-exploratory-tests | 1,000 | 455 |
| testing-ai-features | 1,016 | 451 |
| testing-apis | 852 | 459 |
| testing-data-migrations | 1,020 | 453 |
| testing-mobile-apps | 972 | 471 |
| testing-nonfunctional | 767 | 441 |
| tracing-requirements | 971 | 443 |
| writing-bdd-scenarios | 730 | 435 |
| **Total** | **15,079** | **7,448** |

The detail that left the descriptions (standards, heuristics, file formats) is still in each SKILL.md body. The body loads only after the skill has been chosen, so it costs nothing in the listing.
