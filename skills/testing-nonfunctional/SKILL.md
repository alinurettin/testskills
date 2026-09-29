---
name: testing-nonfunctional
description: Designs and runs non-functional tests traced to requirements. Performance tests are k6 scripts whose thresholds come from the requirement (p95, error rate, load profile smoke/load/stress/spike/soak). Accessibility follows WCAG 2.2 AA, with an axe scan plus manual checks per success criterion selected by feature. Security is functional testing based on OWASP ASVS 5.0 chapters selected by feature and level. Output is drafted as QA Suite test cases (TR/EN). Use this whenever someone asks about performance, load or stress testing, response-time requirements, k6/JMeter, accessibility, WCAG, a11y, erişilebilirlik, screen readers, security testing, OWASP, ASVS, authorization/IDOR checks, "güvenlik testi", "yük testi", "performans testi" or "erişilebilirlik testi".
license: MIT
metadata:
  suite: qa-suite
  version: "0.4.0"
---

# Testing non-functional requirements

Non-functional requirements fail silently. Nobody files a bug for "a bit slow", "not usable with a keyboard", or "another user's order is visible by changing the ID", until a customer, an auditor or an attacker does. This skill makes them **testable, traced and repeatable**:
- numbers from the requirement become thresholds;
- standards (WCAG 2.2, ASVS 5.0) become selected checklists;
- every check becomes a QA Suite test case linked to its REQ.

## Language
Match the user's language. `scripts/nfr_checklist.py --lang tr|en` writes Turkish or English drafts. The WCAG criterion names stay in their official English form.

## Reading plan
Read only the area you are working on:
- `references/performance.md`
- `references/accessibility.md`
- `references/security.md`

## Safety and scope (all areas)
- Load tests and active security checks only against **environments the user owns and is authorised to test**, never production or third parties without written approval. Confirm this before running anything.
- Only test accounts and test tokens, passed through environment variables.
- Installing tools downloads files (k6, `@axe-core/playwright`, OWASP ZAP). **Ask the user first.**

## Workflow

```
- [ ] 1. Find the NFRs (requirements.json quality_characteristic, derived NFRs, NFR questions)
- [ ] 2. Missing numbers/levels → questions (never invent thresholds silently)
- [ ] 3. Generate drafts per area (k6 spec / WCAG / ASVS) linked to REQ IDs
- [ ] 4. Review and tailor; merge into qa/test-cases.src.md; regenerate JSON
- [ ] 5. Run (if agreed) and record results in qa/results.json; findings → defect reports
```

### 1–2. Find the NFRs and their numbers
Look for the following:
- `quality_characteristic` values in `qa/requirements.json`: performance-efficiency, interaction-capability, security, reliability.
- Derived NFRs and questions from the analysis, such as the UNMEASURED linter findings.

For each NFR, confirm the measurable target:
- **Performance:** percentile, load level and environment.
- **Accessibility:** WCAG 2.2 AA, or a stated exception.
- **Security:** the ASVS level (L1, L2 or L3).

If a target is missing, raise a question with a proposed default. Do not test against an invented target without marking it as an assumption.

### 3. Generate drafts
**Performance (k6).** Write a spec such as `assets/spec-examples/k6-perf.json` to `qa/design/DS-###-perf.json`:
- the requests of the journey,
- the load target,
- the profile,
- the thresholds from the requirement.

Then:
```bash
python scripts/generate_k6.py qa/design/DS-010-perf.json --out perf/DS-010.k6.js
```
Create one QA test case for each performance requirement (category `performance`). Its step runs the k6 script, and its expected result names the thresholds.

**Accessibility (WCAG 2.2 A/AA):**
```bash
python scripts/nfr_checklist.py wcag --list-features
python scripts/nfr_checklist.py wcag --features forms,errors,status,auth --page "Sepet" --req REQ-012 --tests qa/test-cases.json --lang tr --out qa/design/a11y-sepet.src.md
```
This produces one automated axe test (the machine-checkable criteria) plus one manual test per criterion needing judgement. Run it per key page or journey.

**Security (ASVS 5.0):**
```bash
python scripts/nfr_checklist.py asvs --features auth,authz,api,payment --level L2 --req REQ-013 --tests qa/test-cases.json --lang tr --out qa/design/security.src.md
```
This produces one test per test idea of the chapters matching the features, with polarity negative and category `security`. Add `--baseline` once per release to include the general chapters that apply to every application (V12 TLS, V13 configuration, V15 architecture, V16 logging).

### 4. Review and merge
The drafts are generic by design. For each test:
- make the step concrete for the page or API: which field, which ID to tamper with, which role;
- drop the items that do not apply, and justify them in the summary;
- adjust the priority to risk. Access control, authentication and payment are usually high.

Then append the tests to `qa/test-cases.src.md`, run `qa_compact.py`, and re-run the RTM. Generate one draft at a time with `--tests`, so the TC numbers continue and do not collide.

### 5. Run and record
- **Performance:** `k6 run ...`. Exit code 0 means passed; exit code 99 means a threshold failed.
- **Accessibility:** the axe test runs in the Playwright suite; the manual criteria are assessed by a person with the toolkit in `references/accessibility.md`.
- **Security:** API-level checks can be automated with Playwright's `request` fixture; the rest are manual.

Record each result in `qa/results.json`. Findings become defect reports through the `reporting-test-results` skill. For WCAG findings add the criterion; for security findings add the ASVS IDs, and mark them confidential.

## Files
- `scripts/generate_k6.py`: k6 script from a performance spec (thresholds, profiles, open or closed model, auth from the environment).
- `scripts/nfr_checklist.py`: WCAG 2.2 A/AA and ASVS 5.0 test-case drafts in compact format (TR/EN), selected by feature.
- `assets/wcag22-aa.json`: the 55 A/AA success criteria with features, automated or manual method, and checks (TR/EN).
- `assets/asvs5-chapters.json`: ASVS 5.0 chapters V1–V17 with feature triggers and test ideas (TR/EN).
- `assets/spec-examples/k6-perf.json`: example performance spec.
- `references/performance.md`, `references/accessibility.md`, `references/security.md`.
