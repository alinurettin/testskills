# TestRail, Azure DevOps Test Plans and Qase

These three importers change more often than Xray's. The mapping below is based on each vendor's public import documentation (2025–2026). **Always do a trial import of 2–3 tests first**, and compare with a CSV exported from your own instance when something does not map.

## Contents
1. TestRail
2. Azure DevOps Test Plans
3. Qase
4. What none of them import

---

## 1. TestRail (`--format testrail`)
**Import path:** Test Cases → Import → CSV.
- **Template:** "Test Case (Steps)". The steps go into the separated-steps field.
- **Layout:** "Test cases use multiple rows". Choose **Title** as the column that detects a new case. Continuation rows leave Title empty.

| Column | Source | Notes |
|---|---|---|
| Title | `TC-xxx` + title | The TC ID stays visible, so RTM and TestRail stay aligned |
| Section | `--folder` | Use `A > B` for nested sections; missing sections are created |
| Priority | priority → Critical/High/Medium/Low | Map the names to your instance's priorities in the wizard |
| Type | `Regression` if tagged `regression`, else `Functional` | |
| Preconditions | preconditions + test data | |
| Step / Expected Result | one step per row | Map to "Steps (Step)" and "Steps (Expected Result)" |
| References | REQ IDs + Jira keys | With a Jira integration, the keys become links |

**Verify:** custom fields that are required in your instance, and priority names that were renamed.

## 2. Azure DevOps Test Plans (`--format azure-devops`)
**Import path:** Test Plans → a suite → Import test cases from CSV. In some versions this is the Boards CSV import with Work Item Type `Test Case`.
- **Layout:** one row per step. Title, Area Path, Priority and State repeat on every row. Test Step is numbered 1..n. Leave ID empty to create new items.
- **Priority:** 1–4 (critical → 1, low → 4). **State:** `Design`.
- **Preconditions:** there is no precondition field, so they are prefixed to the first step's action.
- **Area Path** (`--area-path`) must already exist. **Assigned To** (`--assigned-to`) must be a valid user; otherwise leave it empty.
- **Requirement links cannot be imported through CSV.** Import into a **requirement-based suite** (the suite of the user story), or link the tests afterwards. The TC ID in the title keeps the RTM traceable.
- The title is cut at 128 characters.

## 3. Qase (`--format qase`)
**Import path:** Repository → Import → CSV.
- **Header set:** V2 (`v2.id, title, description, preconditions, …, suite_id, suite, suite_without_cases`).
- **Suite:** the first data row is a suite row (`suite_id` 1, `suite_without_cases` 1). Cases reference `suite_id` 1.
- **Steps:** one row per case. Actions, expected results and data are **numbered inside one cell each**: `1. "…"` then a newline and `2. "…"`.
- **Enums** are lowercase:
  - priority: high/medium/low
  - severity: critical/major/normal/minor
  - behavior: positive/negative
  - automation: to-be-automated/is-not-automated
  - status: actual/draft
- The requirement IDs and Jira keys go into the description, and the REQ IDs also go into the tags.

**Verify:** Qase documents the V2 step-cell encoding only partly. If steps land in one step, export one manually created case from your workspace and compare its cells with this file.

## 4. What none of them import
- **Execution history.** Results come from runs, via `pw_results.py` and the tool's own API or JUnit import.
- **Attachments and screenshots.**
- **Links to requirements in another system**, other than the reference fields.

Re-importing creates duplicates in all three tools, so export only new tests (`--only`, `--tag`) next time.
