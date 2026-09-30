# Test case writing standard

This standard covers the fields and wording of a test case. The fields follow the ISO/IEC/IEEE 29119-3 test case specification and ISTQB practice, and are mapped to the QA Suite JSON (see `data-model.md`).

## Contents
1. Fields
2. Writing rules
3. Good vs. bad examples (TR and EN)
4. Priority definitions
5. Automation candidacy
6. Self-review checklist
7. Deduplication rules

---

## 1. Fields

| Field | Rule |
|---|---|
| `id` | `TC-###`. Never renumber. Take the next free number. |
| `title` | Say **what is verified under which condition**, in ≤ 12 words. Start with the object or feature, not with "Test" or "Verify". |
| `objective` | Optional, one short sentence on why the test exists. Name the design condition (`DS-001 C-07`) and any assumption it relies on (`Q-003`). Leave it out when the title already says everything. |
| `requirement_ids` | Every requirement whose verdict this test contributes to. |
| `priority` | See section 4. |
| `polarity` | `positive` or `negative`. |
| `category`, `technique`, `design_ref` | From the enumerations. `technique` is the primary technique that produced the case. |
| `preconditions` | The state that must hold **before** step 1: user, role, data, configuration, feature flags. Make each one verifiable. Setup shared by many tests goes into a `setup` block of the compact file (`pre: @name`); do not repeat it in every test. |
| `test_data` | Concrete values, never "valid data". For generated data, give the rule ("unique email: `qa+<timestamp>@example.com`"). Checksum-valid TCKN/VKN/IBAN values are synthetic output of `check_ids.py --generate` (or the preparing-test-data generator), for test environments only; say so ("TCKN: synthetic, check_ids seed 1"). |
| `steps` | Numbered actions. **Each step has exactly one action and its own observable expected result.** |
| `postconditions` | Cleanup, or the state left behind, when it matters for the next tests. |
| `tags` | `smoke`, `regression`, `sanity`, technique tags, the feature area. |
| `automation` | Candidate or not, with a reason (section 5). |

## 2. Writing rules

1. **Atomic:** one test verifies one behaviour or condition set. If the title needs "and", consider splitting it.
2. **Independent:** the test must not rely on another test having run first. Put the needed state in the preconditions.
3. **Reproducible:** another tester, or an automation engineer, gets the same result from the text alone. Include concrete data, the exact button or field names as they appear in the UI, and the URL or screen.
4. **Observable expected results:** say exactly what is seen or stored. Include message texts verbatim when the requirement defines them, values with units and formatting (`1.234,56 TL`), and state changes (status becomes "Paid"). Include side effects too (an email is received within 1 minute, an audit log entry exists).
   - ❌ "System works correctly", "Appropriate error is shown", "Başarılı olmalı"
   - ✅ "Error message 'Kupon kodu geçersiz' appears under the coupon field. The total stays 150,00 TL."
5. **Imperative actions:** "Click **Apply**", "'Uygula' butonuna tıkla". Use one verb per step.
6. **No hidden assumptions:** if the test relies on an assumption because an open question has not been answered, say so in the objective or notes, for example "(Assumption per Q-003: code is case-insensitive)".
7. **Negative tests** state what must **not** happen as well as what must: no charge taken, status unchanged, no record created.
8. **Right size:** 3–10 steps is typical. More than 15 steps is usually a scenario test, so split it or justify it.
9. **Language:** the artifact language only. Do not mix Turkish and English inside a step. UI labels are quoted exactly as they appear in the product.

## 3. Good vs. bad examples

**Bad**
```
Title: Test coupon
Steps: 1. Enter coupon  2. Check result
Expected: Should work
```

**Good (TR)**
```
ID: TC-014   Başlık: Süresi dolmuş kupon reddedilir – indirim uygulanmaz
REQ: REQ-002   Öncelik: high   Polarite: negative   Teknik: decision-table (DS-002 D03)
Ön koşullar: Kullanıcı "ayse.test@example.com" ile giriş yapmış; sepet toplamı 150,00 TL;
             "BAHAR5" kuponu 01.04.2026 tarihinde sona ermiş
Adımlar:
 1. Sepet sayfasını aç                 → Toplam 150,00 TL görünür
 2. Kupon alanına "BAHAR5" yaz, "Uygula"ya tıkla
                                       → "Bu kuponun süresi dolmuştur" mesajı kupon alanının altında görünür
 3. Sipariş özetini kontrol et         → İndirim satırı yok; toplam 150,00 TL olarak kalır
```

**Good (EN)**
```
ID: TC-031   Title: Loan amount at upper boundary 50,000.00 accepted
REQ: REQ-004   Priority: critical   Polarity: positive   Technique: boundary-value-analysis (DS-001 C-05)
Preconditions: Applicant logged in, age 30, credit score 720
Steps:
 1. Open "New application"             → Form shows empty "Amount" field
 2. Enter 50000.00 in "Amount", click "Continue"
                                       → No validation error; step 2 "Income" opens
 3. Go back to step 1                  → "Amount" shows 50,000.00
```

## 4. Priority: rate the test, not the requirement

A test's priority answers one question: **if this single test fails, what do we do with the release?** It is not copied from the requirement. A critical requirement typically has one or two critical tests (its go/no-go checks) and several high or medium ones (its variants).

| Priority | The failing test means… | Examples |
|---|---|---|
| critical | **Stop the release.** Money is wrongly taken or given at scale, data is lost or leaked, there is a legal breach, or the core journey is blocked for most users. | The main discount calculation is wrong; a used coupon can be reused; a payment is charged twice |
| high | Must be fixed before release, but a single-point failure with limited blast radius | The exact boundary value is handled wrongly; an expired coupon shows the wrong message but no discount is applied |
| medium | Fix soon; a workaround exists, or only an edge case is affected | The neighbour of a boundary (e.g. 100,01); an extra equivalence-class representative; message wording |
| low | Cosmetic, or very rare | Formatting of an extreme value; tooltip text |

Rules of thumb:
1. **Start one level below** the linked requirement's risk level. Promote a test to the requirement's level only when it is *the* check that proves the requirement works (happy path), or *the* check that proves its most damaging failure is prevented.
2. **Variants go down a level:**
   - boundary neighbours (x−1, x+1) sit one level below the exact boundary value,
   - further representatives of an already-covered partition sit one level below that,
   - message and wording checks are at most medium.
3. Error-guessing and exploratory tests are at most **high**. They can only be critical when they target a concrete, stated money, security or data-loss risk, and that risk is named in the objective.
4. **Sanity check the whole suite:**
   - critical ≈ 5–15%, high ≈ 20–35%, medium ≈ 35–50%, low ≈ 5–20%;
   - more than 20% critical, or more than 60% critical+high together, means the ratings are inflated.

   `build_rtm.py` reports this as PRIORITY_SKEW. Re-rate the suite before delivering it. A suite where everything is critical gives the team no way to triage when time runs out, and triage is the whole point of priorities.

## 5. Automation candidacy

Mark `"candidate": true` when the test is:
- deterministic (a stable oracle),
- repeated often (regression, smoke, a data-driven variant),
- stable in its UI or API,
- expensive or error-prone to run by hand (many combinations, calculations).

Mark `"candidate": false` for:
- exploratory charters,
- one-off checks, and visual or UX judgement,
- tests needing physical devices or manual third-party steps.

The `reason` goes into the export, and the automation phase (Playwright) uses it.

## 6. Self-review checklist

Run this over the whole set before handing off:
- [ ] Every requirement in scope has at least one test. Functional rules also have at least one **negative** test.
- [ ] Every boundary, decision column, transition or pair the scripts produced is covered by a test, or listed as deliberately excluded.
- [ ] No step has an expected result like "works", "correct", "appropriate", "başarılı", "doğru" or "uygun" without the concrete observation.
- [ ] Test data is concrete. No test depends on another test.
- [ ] No invalid values are combined in one test.
- [ ] Titles are unique. IDs are unique and not renumbered.
- [ ] Assumptions from open questions are cited.
- [ ] Priorities are rated per test (section 4). The distribution is plausible (≤ 20% critical), and `build_rtm.py` shows no PRIORITY_SKEW.
- [ ] No extra values from partitions that are already covered. REDUNDANT warnings are resolved or justified.
- [ ] Smoke tests (about 5–10% of the set) are tagged `smoke`.
- [ ] The artifact language is consistent.

## 7. Deduplication rules

Two tests are duplicates when they have the same preconditions, the same data class for every input, and the same expected outcome. Merge them: keep the lower ID, mark the other `deprecated` with a `notes` pointer, and union their `requirement_ids`.

Two tests whose data falls in the same EP class are **redundant**, unless one of them is a boundary value. For example, 1.000 TL and 99.999,99 TL above a 500 TL cap are one class; keep one. The only reason to keep an extra value from a covered class is a *distinct* risk. Write that risk in the objective: overflow, display formatting of large numbers, a field-length limit. Without a stated reason, drop the value.
