# QA Suite data model

Every skill in the QA Suite reads and writes the same two JSON files. This shared model lets one ID stay the same all the way from a requirement to an exported Jira test. JSON keys are always English. Human-readable values (titles, steps, expected results) are in the artifact language.

## Contents
- Workspace layout
- ID rules
- requirements.json
- test-cases.json
- results.json (optional)
- Enumerations

## Workspace layout

Unless the user names another location, create a `qa/` folder at the root of the project (or the current working directory):

```
qa/
├── requirements.src.md    compact authoring source → requirements.json (scripts/qa_compact.py req)
├── requirements.json      normalized, atomic requirements (generated; read by all scripts)
├── analysis-report.md     requirements quality review
├── clarifications.md      open questions log (Q-001 …)
├── design/                technique specs (*.json) and script outputs (*.md)
├── test-cases.src.md      compact authoring source → test-cases.json (scripts/qa_compact.py tc)
├── test-cases.json        test cases (generated; read by all scripts)
├── results.json           execution results (manual and/or from Playwright via pw_results.py)
├── automation-coverage.md automated / skeleton / missing per TC (check_automation.py)
├── test-plan.md           test plan (planning-tests) + exit-criteria.json (machine-checkable exit criteria)
├── defects.json           optional defect register (reporting-test-results)
├── completion-report.md   test completion report with exit-criteria evaluation
├── rtm.md / rtm.csv       traceability matrix + gap report
└── exports/               xray.csv, zephyr.csv, test-cases.xlsx, test-cases.md …
```

## Author in the compact format, not in JSON

Write `qa/requirements.src.md` and `qa/test-cases.src.md` in the compact text format, then generate the JSON:

```bash
python scripts/qa_compact.py req qa/requirements.src.md --out qa/requirements.json
python scripts/qa_compact.py tc  qa/test-cases.src.md  --out qa/test-cases.json
```

The script prints the full syntax with `--help`. It validates the files, expands shared `setup` precondition blocks, and never renumbers IDs. Compared with hand-written JSON, the compact format is about 35–60% shorter and you cannot produce broken JSON with it. Edit the `.src.md` file and regenerate the JSON; do not edit the JSON directly. If only JSON exists, create the source first with `--to-compact`.

The field reference below describes the **generated JSON**. You only need it when you read JSON directly or write another tool against it.

## ID rules

- Requirements: `REQ-001`, `REQ-002` … Questions: `Q-001` … Test cases: `TC-001` … Design specs: `DS-001` …
- **Never renumber.** Existing IDs keep their meaning forever. New items get the next free number. Removed items stay in the file with `"status": "deprecated"`, so links, exports and history do not break.
- Jira or other external keys go in `external_id` and never replace the internal ID.
- One requirement is one testable statement. If a source sentence holds two obligations, split it into two REQs (for example `REQ-004` and `REQ-005`) and point both at the same `source`.

## requirements.json

```json
{
  "project": "Online Shop – Coupons",
  "language": "tr",
  "version": 3,
  "requirements": [
    {
      "id": "REQ-001",
      "external_id": "SHOP-123",
      "title": "Kupon kodu ile indirim",
      "text": "Kayıtlı kullanıcı sepet tutarı 100 TL ve üzerindeyse geçerli bir kupon kodu ile %10 indirim alabilmelidir.",
      "type": "functional",
      "quality_characteristic": null,
      "source": "US-12, kabul kriteri 1",
      "priority": "high",
      "risk": { "likelihood": 3, "impact": 4, "rationale": "Gelir kaybı riski, karmaşık kurallar" },
      "acceptance_criteria": [
        "Diyelim ki sepet tutarı 150 TL, Eğer ki 'YAZ10' kodu uygulanırsa, O zaman toplam 135 TL olur"
      ],
      "status": "clarification-needed",
      "derived": false,
      "questions": ["Q-001", "Q-004"],
      "notes": ""
    }
  ]
}
```

| Field | Required | Meaning |
|---|---|---|
| `id` | yes | `REQ-###`, unique, stable |
| `title` | yes | Short name (≤ 10 words) |
| `text` | yes | The requirement statement. Keep the source wording. Put improved wording in `notes` or `acceptance_criteria` instead of silently rewriting it. |
| `type` | yes | See enumerations |
| `quality_characteristic` | for non-functional requirements | ISO/IEC 25010:2023 characteristic (see enumerations) |
| `source` | yes | Where it came from (document, section, story, ticket, meeting) |
| `priority` | yes | Business priority |
| `risk` | recommended | `likelihood` and `impact` from 1 to 5. Risk score = likelihood × impact. |
| `acceptance_criteria` | recommended | Strings, either Given/When/Then or rule-based |
| `status` | yes | See enumerations |
| `derived` | yes | `true` when the analysis inferred the requirement and no stakeholder stated it. It stays unconfirmed until someone agrees. |
| `questions` | no | IDs of related open questions |
| `external_id`, `notes`, `parent` | no | Free use. `parent` is the ID of the requirement it was split from. |

## test-cases.json

```json
{
  "project": "Online Shop – Coupons",
  "language": "tr",
  "test_cases": [
    {
      "id": "TC-001",
      "title": "100 TL sınırında kupon uygulanması – tam sınır değeri",
      "objective": "Sepet tutarı tam 100,00 TL iken indirimin uygulandığını doğrular",
      "requirement_ids": ["REQ-001"],
      "priority": "high",
      "polarity": "positive",
      "category": "functional",
      "technique": "boundary-value-analysis",
      "design_ref": "DS-001",
      "preconditions": ["Kullanıcı kayıtlı ve giriş yapmış", "'YAZ10' kuponu aktif"],
      "test_data": { "sepet_tutari": "100,00 TL", "kupon": "YAZ10" },
      "steps": [
        { "action": "Sepete toplam 100,00 TL tutarında ürün ekle", "data": "Ürün A x1 (100,00 TL)", "expected": "Sepet toplamı 100,00 TL görünür" },
        { "action": "Kupon alanına kodu gir ve 'Uygula'ya tıkla", "data": "YAZ10", "expected": "'Kupon uygulandı' mesajı görünür, indirim satırı -10,00 TL, yeni toplam 90,00 TL" }
      ],
      "postconditions": [],
      "tags": ["regression", "coupon"],
      "automation": { "candidate": true, "reason": "Deterministik, sık regresyon, veri güdümlü" },
      "status": "ready"
    }
  ]
}
```

| Field | Required | Meaning |
|---|---|---|
| `id` | yes | `TC-###`, unique, stable |
| `title` | yes | What is verified, under which condition. Two test cases must not share a title. |
| `external_id` | no | Key of the test in the test-management tool (e.g. Xray `SHOP-201`), known after import. Playwright skeletons carry it as the `test_key` annotation. |
| `requirement_ids` | yes | At least one `REQ-###`. A test with no requirement is an orphan; the only exceptions are exploratory charters, which are tagged `exploratory`. |
| `priority` | yes | Usually inherited from the highest-risk linked requirement |
| `polarity` | yes | `positive` (valid behaviour) or `negative` (invalid input or rejected action) |
| `technique` | yes | The technique that produced the case (see enumerations) |
| `steps` | yes | One or more steps. Each step has `action` and `expected`; `data` is optional. |
| `objective`, `category`, `design_ref`, `preconditions`, `test_data`, `postconditions`, `tags`, `automation`, `status` | recommended | See enumerations |

## results.json (optional)

```json
{
  "run": "Sprint 14 – RC2",
  "results": {
    "TC-001": { "status": "passed" },
    "TC-002": { "status": "failed", "defects": ["SHOP-481"] },
    "TC-003": { "status": "failed", "source": "playwright", "projects": { "chromium": "failed", "firefox": "passed" },
                "errors": ["expect(locator).toContainText(expected) failed"], "spec": "tests/req-002.spec.ts:7" },
    "TC-030": { "status": "not-run", "source": "playwright", "note": "not implemented (test.fixme skeleton)" }
  }
}
```
Required per entry: `status`. Optional fields are `defects`, `source`, `projects`, `flaky`, `errors`, `note`, `spec` and `duration_ms`. `pw_results.py` writes the Playwright fields. It keeps manual entries and defect keys that are already in the file.

## exit-criteria.json (optional)

The planning skill writes this file and the completion report evaluates it. Leave out any criterion that does not apply.

```json
{
  "min_requirement_coverage_pct": 100,
  "min_execution_pct": 95,
  "min_pass_rate_pct": 95,
  "max_open_defects": { "critical": 0, "high": 0, "medium": 5 },
  "all_critical_requirements_passed": true,
  "max_blocking_questions_open": 0,
  "min_automation_pct": 60
}
```

## defects.json (optional)

Use this when defects are tracked outside Jira, or when a snapshot is exported for the report.

```json
{
  "defects": [
    { "id": "SHOP-481", "title": "100,00 TL sınırında kupon reddediliyor", "severity": "high", "priority": "high",
      "status": "open", "test_ids": ["TC-003"], "requirement_ids": ["REQ-002"], "found_in": "RC2", "environment": "staging" }
  ]
}
```

- `severity` records the technical impact: `critical`, `high`, `medium` or `low`.
- `priority` records the urgency of the fix.
- `status` is one of `open`, `in-progress`, `resolved`, `closed`, `rejected` or `deferred`. Only `open`, `in-progress` and `resolved` count as open until the defect is verified closed.

## Enumerations

- **requirement.type**: `functional`, `non-functional`, `business-rule`, `interface`, `data`, `constraint`, `compliance`
- **requirement.quality_characteristic** (ISO/IEC 25010:2023): `functional-suitability`, `performance-efficiency`, `compatibility`, `interaction-capability`, `reliability`, `security`, `maintainability`, `flexibility`, `safety`
- **requirement.status**: `draft`, `clarification-needed`, `ready`, `deferred`, `deprecated`
- **priority**: `critical`, `high`, `medium`, `low`
- **test.polarity**: `positive`, `negative`
- **test.category**: `functional`, `ui`, `api`, `integration`, `data`, `security`, `performance`, `accessibility`, `usability`, `compatibility`, `localization`, `reliability`
- **test.technique**: `equivalence-partitioning`, `boundary-value-analysis`, `decision-table`, `state-transition`, `pairwise`, `classification-tree`, `use-case`, `scenario`, `crud`, `error-guessing`, `checklist`, `exploratory`, `requirements-based`
- **test.status**: `draft`, `ready`, `deprecated`
- **result.status**: `passed`, `failed`, `blocked`, `not-run`, `skipped`
