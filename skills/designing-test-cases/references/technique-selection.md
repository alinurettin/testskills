# Technique selection and risk-based depth

## Contents
1. Choose techniques by the shape of the requirement
2. Test depth by risk level (+ test budget)
3. Combining techniques without duplication
4. Recording coverage

---

## 1. Choose techniques by the shape of the requirement

Look at what the requirement *contains*, not at what it is called. A single requirement often needs two or three techniques.

| If the requirement contains… | Use | Script | Coverage item |
|---|---|---|---|
| Numeric ranges, lengths, amounts, dates, limits, thresholds | Equivalence partitioning + boundary value analysis | `ep_bva.py` | Each partition, each boundary value (2- or 3-value) |
| A finite set of options (enum, dropdown, type, status as input) | Equivalence partitioning (each value, or grouped classes) | `ep_bva.py` (`enum`) | Each partition |
| Business rules with several conditions leading to outcomes ("if A and B but not C then…") | Decision table | `decision_table.py` | Each feasible column (collapsed) or each combination (full) |
| Statuses, lifecycles, workflows, modes, screens with navigation | State transition | `state_transition.py` | 0-switch (every valid transition) plus the invalid transitions; 1-switch for high risk |
| Many independent configuration parameters (browser × OS × payment × language…) | Pairwise / combinatorial | `pairwise.py` | Every pair (t=2); every triple (t=3) for critical |
| A multi-step user goal with alternatives and exceptions | Use case / scenario testing | (manual) | Main flow, every alternative flow, every exception flow |
| An entity with create, read, update and delete operations across roles | CRUD matrix | (manual) | Each operation × each role (allowed and forbidden) |
| Hierarchical input classifications | Classification tree | (manual; flatten into `pairwise.py` parameters) | Each class, or pairwise across the classes |
| Anything, especially complex or new code | Error guessing, checklist-based | `error-guessing-checklist.md` | Each relevant fault category |
| Vague or new domain with little specification | Exploratory testing (session-based, with charters) | (manual) | Charters completed |

**Non-functional requirements** use their own methods, and some are planned for later phases of this suite:
- Performance: load and stress scenarios
- Accessibility: map to WCAG 2.2 success criteria
- Security: map to OWASP ASVS requirements

In this phase, still write the functional or verifiable checks for them as test cases, such as "the response is under X ms" or "keyboard-only completion of the flow". Tag them with the right `category`.

## 2. Test depth by risk level

The risk score is likelihood × impact (1–25), taken from requirements.json. It sets how deep testing goes.

| Level (score) | Minimum techniques and coverage |
|---|---|
| **Critical (17–25)** | EP + **3-value** BVA; full decision table (`--coverage full`); state transition **1-switch** + all invalid transitions; pairwise **t=3** for configuration; error guessing across all relevant categories; negative tests for every validation and permission |
| **High (10–16)** | EP + 2-value BVA; collapsed decision table; 0-switch + invalid transitions from reachable states; pairwise t=2; error guessing on the top categories; at least one negative test per rule |
| **Medium (5–9)** | EP + 2-value BVA on the main inputs; collapsed decision table; 0-switch; main negative paths |
| **Low (1–4)** | Happy path + one representative negative; EP on the main input |

When no risk score exists, use the priority: critical → Critical, high → High, and so on. State in the summary that the depth came from priority because risk was not scored.

**Depth follows risk, so a wrong risk score multiplies the suite.** One inflated "critical" requirement switches on 3-value BVA, a full decision table and 1-switch coverage. Before designing, check that the risk levels look plausible. In a typical feature, no more than about 10–20% of requirements are critical. If most are critical or high, re-read the risk anchors in the analysis skill and re-score before you start.

### Test budget (a guide, not a quota)

| Requirement risk | Typical number of test cases |
|---|---|
| Critical | 4–8 |
| High | 3–5 |
| Medium | 2–3 |
| Low | 1–2 |

For a single user story with about 5–8 acceptance criteria, a sound suite usually has **15–35 test cases**. Pairwise rows come on top of this, at one per row.

Going beyond the budget is fine when the script outputs demand it, for example 12 real decision-table columns. In that case, say why in the summary. If you are well over the budget without such a reason, the usual causes are:
- extra values from partitions that are already covered,
- one test per message variant,
- derived requirements that should have stayed questions.

## 3. Combining techniques without duplication

- Build the **test conditions** first, from the script outputs and your own analysis, then turn conditions into test cases.
- One test case may cover several conditions when they do not interfere, for example valid values of different fields in one successful submission. Record this in the title or objective.
- **Never combine two invalid values in one test.** The first rejection masks the second, so you learn nothing about the second value.
- When a boundary value from EP/BVA already equals a decision-table value, do not create a second test for it. Reference both techniques in `tags` (for example `bva`, `decision-table`) and keep `technique` as the primary one.
- Pairwise rows are environment or configuration combinations. Each row is usually one execution of the **same** functional scenario. Model this as one test case per row (title ends with the combination), or as one test case whose `test_data` holds the matrix, depending on the target tool. Xray and Zephyr handle one-case-per-row best.

## 4. Recording coverage

In the delivery summary, report for each requirement:
- The techniques applied, and the design spec ID (`DS-###`) with its script output file.
- The coverage achieved, for example "12/12 boundary values, 7/7 transitions (0-switch), 26/26 pairs".
- What was **deliberately not covered** and why (risk accepted, out of scope, blocked by a question).
