# Test design techniques: how to apply them

These techniques follow the ISTQB CTFL v4.0 and CTAL-TA v4.0 syllabi and ISO/IEC/IEEE 29119-4. Each section below gives the procedure, the coverage measure and the common mistakes.

## Contents
1. Equivalence partitioning (EP)
2. Boundary value analysis (BVA)
3. Decision table testing
4. State transition testing
5. Pairwise / combinatorial testing
6. Use case and scenario testing
7. CRUD testing
8. Classification tree
9. Error guessing and checklist-based testing
10. Exploratory testing (session-based)
11. Writing script specs from requirements

---

## 1. Equivalence partitioning (EP)
**Idea:** Divide each input (or output) domain into classes that the system should treat the same way. One value per class is enough.

**Procedure:**
1. For each input, list the valid classes. A range that leads to different behaviour becomes separate classes (for example score 0–499 reject, 500–699 review, 700+ approve).
2. List the invalid classes: below range, above range, wrong type, empty, wrong format, and forbidden values.
3. Pick a representative value from the middle of each class. The script does this for you.
4. Combine valid classes of different inputs in the same test. Test each invalid class on its own, with all other inputs valid.

**Coverage:** the number of classes exercised divided by the total number of classes.

**Pitfalls:**
- Forgetting output partitions. For example, "discount = 0" and "discount > 0" are different output classes.
- Forgetting "empty" and "not provided" as classes.
- Treating "valid for format" and "valid for business" as one class. A well-formatted but unknown coupon code is a different class from a malformed one.

## 2. Boundary value analysis (BVA)
**Idea:** Defects cluster at the edges of partitions (off-by-one errors, `<` versus `<=`).

- **2-value BVA:** for each boundary, test the boundary value and its nearest neighbour in the adjacent partition. For 18–65 that is 17, 18, 65, 66.
- **3-value BVA:** test the boundary value and both of its neighbours. For 18–65 that is 17, 18, 19 and 64, 65, 66. This catches more faults, such as `==` written instead of `<=`. Use it for high-risk requirements.
- The **step** is the smallest meaningful increment: 1 for integers, 0.01 for money in TRY, 1 day for dates, 1 character for length.

**Coverage:** the boundary values exercised divided by the boundary values identified.

**Pitfalls:**
- Boundaries hidden in the implementation, such as database column length, integer overflow, or file-size limits of middleware. Ask for them, and add them as `domain_min`/`domain_max`.
- Inclusive or exclusive ambiguity ("up to 100", "100'e kadar"). This is a clarification question, not an assumption to make silently.
- Date boundaries: ask whether "until 31.12" means 23:59:59 and in which time zone.

## 3. Decision table testing
**Idea:** Systematically cover combinations of conditions that lead to different actions, and expose missing or contradictory rules.

**Procedure:**
1. List the conditions and their values. Use the partitions from EP rather than raw values (for example `<100` and `>=100`).
2. List the actions or outcomes.
3. Encode each stated rule as a partial assignment. Omit the conditions that do not matter.
4. Run `decision_table.py`. Every **gap** is a question for the business, and every **conflict** is a requirement defect. Resolve them or record them as questions before writing tests for those columns.
5. Write one test per collapsed column. For critical risk, write one test per full combination.

**Coverage:** the feasible columns exercised divided by the total feasible columns.

**Pitfalls:**
- Treating impossible combinations as gaps. Declare them in `infeasible`.
- Encoding a rule's priority implicitly. If the business says "the first matching rule applies", set `first_match: true`.

## 4. State transition testing
**Idea:** Model the system as states, events, guards and transitions, and cover them.

**Procedure:**
1. Identify the states (statuses), the events (user actions, timers, external messages), the guards (conditions) and the actions (side effects: emails, stock updates).
2. Run `state_transition.py`.
   - Unreachable states, dead ends and nondeterminism are model or requirement defects.
   - Every empty cell in the state table is an **invalid transition** candidate. The question is: what should happen if the user tries this, such as via the UI, API replay, a double submit, or two tabs?
3. Write tests:
   - **0-switch:** every valid transition at least once (from the sequences).
   - **1-switch:** every pair of consecutive transitions. Use it for high or critical risk.
   - **Invalid transitions:** for each relevant empty cell, reach the state via `path_to_state`, trigger the event, and expect a rejection with no state change. Confirm the exact expected behaviour.

**Coverage:** transitions (or pairs) exercised divided by the total, plus invalid transitions tested.

**Pitfalls:**
- Forgetting timers or background events, such as "unpaid orders are cancelled after 30 minutes".
- Forgetting the side effects of transitions (the `action`). The expected result must check them, for example "the e-mail was sent" or "the stock was released".

## 5. Pairwise / combinatorial testing
**Idea:** Most interaction faults are triggered by one or two parameters together. Covering every *pair* of values finds most of them with a fraction of the tests.

**Procedure:**
1. Choose the parameters and their **valid** values. Use EP classes rather than every raw value.
2. Add constraints (`forbidden`) for combinations that cannot exist, for example Safari on Windows.
3. Add must-have combinations as `seed_tests`, for example the most common production setup.
4. Run `pairwise.py`. Check that the verification says OK. Report the reduction compared with the exhaustive number of combinations.
5. Test invalid values separately.

**Pitfalls:**
- Pairwise is not a substitute for decision tables when **business rules** depend on combinations. Use pairwise for independent parameters and decision tables for rules.
- If a constraint is missing, the tests will include impossible rows.

## 6. Use case and scenario testing
For each use case or end-to-end user goal:
- **Main success scenario:** one test.
- **Each alternative flow:** one test.
- **Each exception flow:** one test (payment declined, session expired, validation failure).
- Preconditions and postconditions come directly from the use case.

Scenarios also cover realistic journeys that cross features, such as "register → add to basket → apply coupon → pay → cancel".

## 7. CRUD testing
Build a matrix of **entity × operation (Create, Read, Update, Delete) × role**. Mark each cell as allowed or forbidden.
- Allowed cells: positive tests. Also verify that the data persists correctly and appears everywhere it should, such as lists, search, exports and audit logs.
- Forbidden cells: negative tests through the UI **and** directly through the URL or API (authorisation bypass).
- Also check the effects of Delete: linked data, soft versus hard delete, and whether a deleted item can still be reached by URL.

## 8. Classification tree
Break each input into aspects, and each aspect into classes. This is a hierarchical form of EP. Flatten the tree into parameters and classes, then either:
- cover each class at least once (each-choice), or
- feed the classes into `pairwise.py` as parameter values for pairwise coverage of the classes.

## 9. Error guessing and checklist-based testing
Use experience and fault taxonomies to target likely defects. Work through `error-guessing-checklist.md` and pick the categories that apply to the input types and flows of the feature. Each chosen item becomes a test condition. Tag the resulting tests `error-guessing`.

## 10. Exploratory testing (session-based)
When the specification is thin or the risk is high, add **charters** as test cases with `technique: exploratory` and the tag `exploratory`. Each charter has three parts:
- **Explore:** the target area.
- **With:** the resources or data to use.
- **To discover:** the information sought.

Timebox each session, usually to 60–90 minutes. Charters are the only test cases allowed to have loose steps. Their expected result is "notes, defects and questions recorded".

## 11. Writing script specs from requirements
- Save each spec as `qa/design/DS-###-<short-name>.json`. Set `requirement_ids` and `language`.
- Save each output next to its spec as `qa/design/DS-###-<short-name>.md`.
- In the test cases, set `design_ref` to the DS ID and mention the condition ID (for example `C-07`) in the objective, so a reviewer can trace test → condition → technique → requirement.
- Treat everything the scripts flag (gaps, conflicts, unspecified ranges, unreachable states, invalid transitions) as **analysis findings**. Add them to `qa/clarifications.md` as questions and link them from the requirement.
