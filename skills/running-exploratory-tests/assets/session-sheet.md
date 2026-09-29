# Exploratory session sheet / Keşif testi oturum formu

<!--
Copy ONE of the two templates below into qa/exploratory/sessions/<session-id>.md and delete the other.
Write notes WHILE you test, one line per observation: "HH:MM TAG: text".
sbtm.py reads this file:  python scripts/sbtm.py report qa/exploratory/sessions/*.md --out-dir qa/exploratory
Lines inside HTML comments, headings (#) and tables (|) are ignored by the parser.

Tags (English | Türkçe):
  BUG      | HATA     a problem that threatens the product's value (becomes a defect draft + regression test)
  ISSUE    | SORUN    an obstacle to testing: environment down, missing data, blocked access, slow setup
  QUESTION | SORU     something only a stakeholder can answer (do not guess the expected result)
  IDEA     | FİKİR    a test idea for later (becomes a draft test case, or a new charter)
  NOTE     | NOT      what you did, set up, or observed that is not a problem
  COVERED  | KAPSAM   what you actually exercised (screens, data, states, platforms) - the coverage record
Optional "[REQ-###]" after the tag links a note to specific requirements: "10:41 BUG [REQ-002]: ...".
Indented lines under a note add detail. For BUG notes these keys fill the defect draft:
  steps / adımlar (";" separated, or numbered lines "1. ..."), expected / beklenen, actual / gerçekleşen,
  severity / önem (critical|high|medium|low), data / veri, evidence / kanıt, repro / tekrar.
tbs = percent of session time spent on Test design and execution / Bug investigation and reporting /
Setup (environment, data, access). The three numbers must add up to 100. Estimate them at the end.
opportunity = percent of time spent off-charter (worth doing, but not what the charter asked).
Use test environments and synthetic data only (example.com addresses, fictional names).
-->

## English template

session: S-001
charter: Explore <target> with <resources> to discover <information>
tester: <name or role>
start: 2026-09-30 10:00
duration: 90
req: REQ-001
tbs: 60/25/15
opportunity: 10
env: staging
build: <version or commit>

## Notes

10:00 NOTE: <setup: account, data, build>
10:05 COVERED: <what you exercised>
10:15 BUG: <what is wrong, where, under which condition>
  steps: <step 1>; <step 2>
  expected: <requirement or oracle, e.g. REQ-001 says ...>
  actual: <what happened, verbatim>
  severity: <critical|high|medium|low>
10:30 QUESTION: <what a stakeholder must decide>
10:40 ISSUE: <what slowed or blocked testing>
10:50 IDEA: <test idea for later>

## Debrief (PROOF) - fill in with your test lead

<!-- Past: what happened? Results: what was found and covered? Obstacles: what got in the way?
Outlook: what still needs doing (new charters)? Feelings: how do you feel about the product? -->

---

## Türkçe şablon

oturum: S-002
görev: <kaynaklar> kullanarak <hedef> alanını keşfet; amaç: <bilgi> bulmak
test eden: <isim veya rol>
başlangıç: 2026-09-30 14:00
süre: 90
gereksinim: REQ-001
tbs: 60/25/15
fırsat: 10
ortam: staging
sürüm: <sürüm veya commit>

## Notlar

14:00 NOT: <hazırlık: hesap, veri, sürüm>
14:05 KAPSAM: <neyi denediniz>
14:15 HATA: <ne yanlış, nerede, hangi koşulda>
  adımlar: <adım 1>; <adım 2>
  beklenen: <gereksinim veya kahin, ör. REQ-001 der ki ...>
  gerçekleşen: <olan şey, aynen>
  önem: <critical|high|medium|low>
14:30 SORU: <paydaşın karar vermesi gereken konu>
14:40 SORUN: <testi yavaşlatan veya engelleyen şey>
14:50 FİKİR: <sonrası için test fikri>

## Değerlendirme (PROOF) - test lideriyle doldurun

<!-- Past (Geçmiş): ne oldu? Results (Sonuçlar): ne bulundu ve kapsandı? Obstacles (Engeller): ne engel oldu?
Outlook (Görünüm): geriye ne kaldı (yeni görevler)? Feelings (Hisler): ürün hakkında ne hissediyorsunuz? -->
