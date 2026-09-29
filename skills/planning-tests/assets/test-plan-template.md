# {{Test Plan | Test Planı}}: {{product / release}}

| | |
|---|---|
| {{Version | Sürüm}} | {{n}} · {{yyyy-mm-dd}} |
| {{Owner | Sorumlu}} | {{test lead}} |
| {{Approvers | Onaylayanlar}} | {{PO, dev lead, …}} |
| {{Related | İlgili}} | qa/requirements.json · qa/test-cases.json · qa/rtm.md · qa/exit-criteria.json |

## 1. {{Context and objectives | Bağlam ve hedefler}}
{{What is being released, why, and what testing must prove (in 3–5 bullets). | Neyin, neden yayınlandığı ve testin neyi kanıtlaması gerektiği (3–5 madde).}}

## 2. {{Scope | Kapsam}}
- **{{In scope | Kapsam içi}}:** {{features / REQ ranges}}
- **{{Out of scope | Kapsam dışı}}:** {{… with reason}}
- **{{Test items | Test nesneleri}}:** {{builds, services, versions}}

## 3. {{Risk register | Risk kaydı}}
| {{Risk | Risk}} | REQ | {{Level (L×I) | Seviye (O×E)}} | {{Mitigation through testing | Test ile azaltma}} |
|---|---|---|---|
{{From plan_facts.py top risks + product/project risks (environment, dependencies, people).}}

## 4. {{Test approach | Test yaklaşımı}}
- **{{Levels | Seviyeler}}:** {{component / integration / system / acceptance — who owns which}}
- **{{Types | Tipler}}:** {{functional, regression, API, accessibility (WCAG 2.2 AA), security (ASVS L?), performance, compatibility}}
- **{{Techniques by risk | Riske göre teknikler}}:** {{e.g. critical: 3-value BVA, full decision tables, 1-switch; …}}
- **{{Automation | Otomasyon}}:** {{Playwright scope, smoke on every PR, nightly regression; target % of candidates}}
- **{{Manual / exploratory | Manuel / keşif}}:** {{charters, sessions}}
- **{{Regression strategy | Regresyon stratejisi}}:** {{what is re-run when, impact analysis via RTM --changed}}

## 5. {{Entry criteria | Giriş kriterleri}}
- {{Blocking questions answered or defaults accepted by PO | Bloke eden sorular cevaplandı veya varsayılanlar PO tarafından kabul edildi}}
- {{Build deployed to test environment, smoke passed | Build test ortamına kuruldu, smoke geçti}}
- {{Test data and accounts available | Test verisi ve hesapları hazır}}

## 6. {{Exit criteria | Çıkış kriterleri}}
{{Human-readable version of qa/exit-criteria.json, e.g.: | qa/exit-criteria.json'ın okunabilir hali, örn.:}}
- {{Requirement coverage 100% · execution ≥ 95% · pass rate ≥ 95%}}
- {{No open critical/high defects; ≤ 5 medium with workaround}}
- {{All critical-risk requirements passed}}

## 7. {{Suspension and resumption | Askıya alma ve devam}}
- {{Suspend when … (e.g. smoke fails, environment down > 2 h, > 30% blocked)}}
- {{Resume when …}}

## 8. {{Environments and test data | Ortamlar ve test verisi}}
| {{Environment | Ortam}} | {{Purpose | Amaç}} | {{Configurations (pairwise matrix) | Konfigürasyonlar}} | {{Data / accounts | Veri / hesaplar}} |
|---|---|---|---|

{{Testability needs: stubs/mocks, controllable clock, seed APIs, data-testid… | Test edilebilirlik ihtiyaçları}}

## 9. {{Schedule and effort | Takvim ve efor}}
| {{Activity | Aktivite}} | {{Effort | Efor}} | {{Window | Zaman}} | {{Owner | Sorumlu}} |
|---|---|---|---|
{{Use plan_facts.py effort estimate; state its method and buffer. | plan_facts.py tahminini kullanın; yöntemini ve tamponu belirtin.}}

## 10. {{Roles and communication | Roller ve iletişim}}
{{Who tests, who triages defects, daily status channel, reporting cadence (status report, completion report).}}

## 11. {{Deliverables | Çıktılar}}
{{Test cases, RTM, automation suite, defect reports, status reports, test completion report.}}

## 12. {{Open issues and assumptions | Açık konular ve varsayımlar}}
{{Link qa/clarifications.md; list assumptions the plan depends on.}}
