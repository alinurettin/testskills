# Defect reporting

A defect report has one job: let someone who was not there **reproduce the problem and understand its impact** without asking a single question. The fields follow ISTQB CTFL v4.0 §5.5.

## Contents
1. Fields
2. Severity vs priority
3. Writing rules
4. Good vs bad (TR / EN)
5. Evidence from automation
6. Product bug or test bug?

---

## 1. Fields
| Field | Content |
|---|---|
| ID / key | From the tracker, e.g. SHOP-481. Record it in `qa/results.json` under the failing TC and in `qa/defects.json`. |
| Title | **What is wrong, where, and under which condition.** Aim for 12 words or fewer. No "doesn't work". |
| Environment | Build or version, environment (test/staging), browser, OS, device, locale, test account role |
| Linked items | TC IDs (the failing test), REQ IDs (the violated requirement), related defects |
| Preconditions | The state needed before the steps (data, role, feature flags, clock) |
| Steps to reproduce | Numbered, minimal, with concrete data. Take them from the test case and remove the irrelevant steps. |
| Expected result | Quote the requirement or acceptance criterion (REQ-###), not your opinion |
| Actual result | What happened, verbatim: message text, values, status, HTTP code |
| Reproducibility | Always, or n of m attempts; any conditions |
| Severity / priority | See section 2 |
| Evidence | Screenshot, video, Playwright trace, HAR, log excerpt with timestamp and correlation ID |
| Notes | Workaround, first seen in which build, suspected area. Mark suspicion as suspicion. |

## 2. Severity vs priority
- **Severity** is the technical and business impact, judged by the tester:
  - **critical:** data loss, security breach, money wrong at scale, core flow blocked, no workaround
  - **high:** major function wrong or unavailable, or a workaround is hard
  - **medium:** function wrong but a workaround exists, or a limited population is affected
  - **low:** cosmetic, wording, minor usability
- **Priority** is the urgency of the fix, decided by the product owner (release plan, customer impact, visibility). A low-severity typo on the landing page can be high priority. A high-severity edge case in an unused feature can wait.
- Link severity to the **requirement's risk**. A failing test on a critical-risk requirement is rarely below high severity.

## 3. Writing rules
1. **One defect per report.** Two symptoms with different causes get two reports.
2. **Minimal reproduction.** Remove steps that do not matter. Say whether the problem also happens with other data or other browsers, if you checked.
3. **Facts before interpretation.** Put "Suspected cause" in the notes, clearly labelled.
4. **Neutral tone.** Describe the behaviour, not the developer.
5. **Search for duplicates** before filing. If a duplicate exists, add your evidence to it.
6. **Boundary defects deserve exact values.** Give both sides: "100,00 TL rejected, 100,01 TL accepted".
7. **Retest and close.** Verify the fix with the same TC. Also run the neighbours of the boundary and the regression tests linked to the requirement (`build_rtm.py --changed REQ-###`).

## 4. Good vs bad
**Bad:** "Kupon çalışmıyor. Acil!"

**Good (TR):**
```
Başlık: 100,00 TL sepette YAZ10 kuponu reddediliyor (100,01 TL'de kabul ediliyor)
Ortam: staging · build 2026.09.29-rc2 · Chrome 141 / Windows 11 · tr-TR · kayıtlı müşteri
Bağlantılar: TC-003 (başarısız), REQ-002 · ilgili: –
Ön koşul: 'YAZ10' aktif (%10, asgari 100 TL); kullanıcı kuponu daha önce kullanmamış
Adımlar:
 1. Sepet tutarını 100,00 TL yap
 2. Kupon alanına YAZ10 yaz, 'Uygula'ya tıkla
Beklenen (REQ-002): Kupon uygulanır; indirim -10,00 TL; ödenecek 90,00 TL
Gerçekleşen: "Bu kupon 100,00 TL ve üzeri sepetlerde geçerlidir." mesajı; indirim 0,00 TL; ödenecek 100,00 TL
Tekrarlanabilirlik: 5/5 · 99,99 TL reddediliyor (doğru), 100,01 TL kabul ediliyor (doğru)
Önem: high (gelir/kampanya etkisi, sınır kuralı) · Öncelik: PO karar verecek
Kanıt: trace.zip, test-failed-1.png, video.webm (Playwright, TC-003)
Not (şüphe): eşik karşılaştırması '>' ile yapılıyor olabilir ('>=' olmalı)
```

## 5. Evidence from automation
Playwright already produces the evidence:
- `test-results/<test>/trace.zip`: open it with `npx playwright show-trace`. It holds DOM snapshots, network requests and console output for each step.
- Screenshots and video on failure (see `playwright.config.ts`).
- The `test.step` names map to the manual steps, so the report can cite the failing step.

Attach the trace, not just a screenshot. Developers can replay the failure exactly.

## 6. Product bug or test bug?
Check this before filing:
- Does the test assert **the requirement as written**? Re-read the REQ and its accepted default for any open question.
- Is the precondition really met (data, clock, role)?
- Is the failure stable (not flaky)?
- Does the UI copy differ only in wording that is still an open question (for example, draft messages)? In that case it is a question, not a defect.

If the test is wrong, fix the test case first (`test-cases.src.md`). Never "fix" a test by weakening its expected result to match wrong behaviour.
