# Gap report: exploratory, test data, migration; terminology; Turkish domain packs

Audit date 2026-11-15. Read-only. Paths are relative to `C:\projeler\TestSkills`.

## Sources checked
- ISTQB CTFL v4.0.1, 2024-09-15, §4.4 — https://www.istqb.org/wp-content/uploads/2024/11/ISTQB_CTFL_Syllabus_v4.0.1.pdf — VERIFIED. The repo cites "v4.0 (2023)".
- ISTQB CTAL-TA v4.0 GA, 2025-05-02, §1.3.4, §1.3.5, §3.4 — https://www.istqb.org/wp-content/uploads/sdm-uploads/ISTQB-CTAL-TA-Syllabus-v4.0-EN-4.pdf — VERIFIED.
- TTB "ISTQB Yazılım Testi Terimler Sözlüğü" v2.0, Eylül 2026 (newer than the repo's last check) — https://www.turkishtestingboard.org/files/ISTQB-Yazilim-Testi-Terimler-Sozlugu.pdf — VERIFIED.
- TTB CTFL v4.0.1 Türkçe (çeviri Mart 2024) — https://www.turkishtestingboard.org/files/pdfs/ISTQB_CTFL_Syllabus-v4.0.1.pdf — VERIFIED.
- glossary.istqb.org — JavaScript app, not readable by the fetcher — UNVERIFIED.
- HTSM v6.3, 2024-12-02 — https://www.satisfice.com/download/heuristic-test-strategy-model — version VERIFIED, content from memory.
- NIST SP 800-188 final, Sept 2023 — https://csrc.nist.gov/pubs/sp/800/188/final — VERIFIED.
- ISO/IEC 27701:2025 (standalone, Oct 2025) — search-level VERIFIED. ISO/IEC 27001:2022 A.8.11/8.31/8.33 — UNVERIFIED (memory).
- EDPB Guidelines 01/2025 on pseudonymisation: still a consultation draft; CJEU C-413/23 P (2025-09-04) — search-level VERIFIED.
- Bach SBTM, Bolton FEW HICCUPPS, Whittaker, Kaner, ISO/IEC 25012, ISO 8000, DAMA-DMBOK — UNVERIFIED (memory). Hendrickson's charter template is VERIFIED through CTAL-TA §3.4.1.

## Findings (Part 1, ranked)

| # | Finding | Kind | Source | Where | Concrete fix | Effort | Script? |
|---|---|---|---|---|---|---|---|
| 1 | The "Short session" steps start after about 1,075 words (the core loop after about 640). Full SBTM (1,059 words, 43% of the file) sits in the body. "Read first" adds reference §2, §5, §6 (1,746 words, mostly duplicates of the body). | shallow | EVALUATION §8; CTFL §4.4.3 (checklists must stay short) | `skills/running-exploratory-tests/SKILL.md` L19-75, L77-158 | Put the "Minimum path" below at the top. Move the Full SBTM steps 1-5 to a new reference section. Delete reference §2 duplicates. Target body: 900 words or fewer. | M | no |
| 2 | BUG gating suppresses findings: "reproduce from a clean state; otherwise QUESTION or NOTE", and "unclear which value is right → QUESTION". A weak model downgrades real bugs. Hypothesis: this is the main cause of 65 vs 74. | wrong | CTAL-TA §3.4.1 (session sheet records observations) | SKILL.md L123, L134; reference §5 last paragraph, §13 step 5 | Report every anomaly as a finding with `confidence: confirmed / seen once`. Never drop one. Accept `confidence` as a detail key in `sbtm.py`. | S | yes (small) |
| 3 | Time rules an agent cannot measure: "≥ 75% hands-on", "2 min recon", "Check the time at every note", "after 3–5 minutes". These produce invented timestamps. | wrong | — | SKILL.md L25, L67-74 | Replace minutes with an action budget and make timestamps optional. Add `sbtm.py grid --actions "..."`, which prints an action × probe checklist; unticked cells become "not covered". | M | yes |
| 4 | Competing volume: "run every item … through UI and API" (10 attacks × 2 channels) plus follow-the-data (7 places × 4 triggers) per action, against "breadth first". No priority order; keyboard checks rank equal to authorization. Safety says "ask before deleting data" while CRUD probes need delete. | shallow | CTAL-TA §3.4.2 (prioritised checklist items) | SKILL.md L40, L45, L51-62 | Two tiers. P1 on every action: views agree, boundary, repeat, other user's ID. P2 with leftover budget. State that deleting records the session created needs no question. | S | no |
| 5 | Stale status lines contradict EVALUATION §8 and are the first thing read. | outdated | docs/EVALUATION.md §8 | exploratory SKILL.md L12; `preparing-test-data/SKILL.md` L12 ("planned for 0.7") | Delete them, or give one line with the 0.9.0 numbers. | S | no |
| 6 | `mask_data.py` measures no re-identification risk, and `hash` on a low-cardinality column is readable by frequency. | missing | NIST SP 800-188; WP29 05/2014 | `mask_data.py`; reference §5, §10 | Add `--quasi col,col --k 5 [--sensitive col --l 2]`: report the smallest class and rows below k, and exit 1. Warn when a hashed or kept column has fewer than 20 distinct values. | M | yes |
| 7 | `reconcile.py` has no truncation hint (the reference claims level 4 catches truncation), no reject balance and no time-zone-aware date comparison. | missing | ETL practice | `reconcile.py` hints `h_*`; reference §4, §13 | Add hint `h_trunc` (target is a prefix of expected; report the common length). Add `--rejects file` so that source = target + rejects + excluded, and missing keys split into rejected and silently lost. Add op `datetime:<fmt>:<tz>`. | M | yes |
| 8 | The description promises ETL pipelines, but recurring loads get one table row. | missing | DWH practice (SCD, CDC) | `migration-testing.md` §1, §7; `reconciliation-queries.sql` | New reference section and SQL section 7: SCD2 (one current row per key, no overlapping or gapped validity, from < to), watermark and late-arriving rows, hard deletes, surrogate-key orphans, schema drift, rerun of the same window. | M | no (SQL asset) |
| 9 | No parallel run and no post-go-live reconciliation (day 1, first month-end). | missing | cutover practice | `migration-testing.md` §7, §12 | Add two bullets and sign-off rows 13-14. | S | no |
| 10 | Charters lack fields that CTAL-TA lists: entry criteria, exit criteria ("done when"), limits ("must never") and past defects. | shallow | CTAL-TA v4.0 §3.4.1 | `sbtm.py` `cmd_charters`; reference §3 | Add "Done when" and "Must never" lines. List open defects per REQ from `qa/defects.json`. | S | yes |
| 11 | No named metamorphic or round-trip oracles. | missing | CTAL-TA v4.0 §1.3.4 | reference §5 invariants, §9 | Add five "bug if" relations: create then delete restores totals; filter A plus not-A equals all; ascending equals reversed descending; export then import is identical; page sizes sum to the count. | S | no |
| 12 | The test-data reference cites no ISO control and does not show that the EDPB text is a draft. | outdated | ISO/IEC 27001:2022 A.8.11/8.31/8.33; 27701:2025; EDPB 01/2025; C-413/23 P | `test-data-management.md` §5; SKILL.md L32 | Add an eight-question yes/no auditor checklist mapped to the three controls. Reword: "for the party holding the key, pseudonymised data stays personal data". Cite CTAL-TA §1.3.5. | S | no |
| 13 | Profiling and sign-off name no data-quality dimensions; precision (scale loss) and currentness (delta lag) are unchecked. | shallow | ISO/IEC 25012; DAMA (UNVERIFIED) | `migration-testing.md` §3, §12 | One table mapping each check to a dimension, plus two profiling queries. | S | no |
| 14 | Terminology and domain packs: see the two tables below. | terminology / outdated | TTB Glossary v2.0; Resmî Gazete | — | — | S-M | yes (strings) |

### Proposed "Minimum path" (top of SKILL.md)
```
## Minimum path (one session; read nothing else first)
1. List the actions that change data (create, edit, delete, status, pay).
   Order: money > access/ownership > status > the rest.
2. For each action, one pass, then move to the next action:
   a. Do it once. Compare the record in list, detail, totals/counts and the API GET.
      Any disagreement is a finding.
   b. Boundary: 0, negative, max+1, empty, "1,5" vs "1.5"; send blocked values to the API.
   c. Repeat: submit twice or resend the request. A second record is a finding.
   d. Other user: change the ID. Another user's data read or changed is a finding.
3. Write each finding at once: title / steps / expected and why / actual /
   severity / confidence (confirmed or seen once). Never drop a "seen once" finding.
4. Budget left? Parallel requests, stale tab or Back, Turkish İ/ı, cut-off times,
   error leakage, keyboard.
5. Stop at the action budget. Report: findings by severity, covered, NOT covered.
Planning several sessions or tracing to requirements? Read the reference section "Full SBTM".
```
Also add `assets/short-report-example.md` (one action, four probes, two findings).

## Part 2: term table

| Term in repo | Official term | Where used |
|---|---|---|
| görev kartı / görev (charter) | test başlatma belgesi | `sbtm.py` L163-169, L484; `session-sheet.md` L65; README.md L73; CHANGELOG.md L39 |
| kahin / kahinler (oracle) | test sonucunu bilen (Glossary v2.0) | `sbtm.py` L172, L178; `session-sheet.md` L81 |
| "test case'ler" (33 hits), "test vakaları", "test senaryosu" (three variants) | test senaryosu | README.md L64; docs/IMPORT-VERIFICATION.md; `reconcile.py` L245; `data_needs.py` L60 |
| Değerlendirme (PROOF) (debrief) | bilgilendirme toplantısı | `sbtm.py` L203; `session-sheet.md` L88 |
| test eden / testçi | test uzmanı | `sbtm.py` L194, L208; `session-sheet.md` L66 |
| hata tahmini | hata tahminleme | examples/fast-transfer/qa/test-cases.src.md L284, L324, L364 |
| denklik sınıfı | denklik payı | CHANGELOG.md L93; examples/api-trial/qa/rtm.md L33-35 |
| "test koşulu" for technique outputs | kapsam öğesi | examples/fast-transfer/qa/design/DS-001-tutar.md L4, L37; DS-006 L4 |
| test özet raporu | test tamamlama raporu | docs/MANUEL-TEST-REHBERI.md L16, L75, L82 |
| yeniden test | onaylama testi | examples/api-trial/qa/defect-report.md L118 |
| Önem (severity) | önem derecesi | `sbtm.py` L213 |
| veri göçü / migrasyon / veri taşıma (mixed) | taşıma testi (Glossary: Migration Testing) | `reconcile.py` L134; examples/migration-trial; docs/EVALUATION.md |
| takma adlı | takma adlandırma | `mask_data.py` L110 |
| EN "equivalence classes" | equivalence partitions | shared/domains/health.md L51 (three copies); `test-data-management.md` L28 |
| EN "test conditions" from script outputs | coverage items | designing-test-cases/references/technique-selection.md L68 |
| EN "CTFL v4.0 (2023)" | CTFL v4.0.1 (2024-09-15) | `exploratory-testing.md` L334; `test-data-management.md` L18; README L129 |

Already official: sınır değer analizi, karar tablosu testi, durum geçişi testi, izlenebilirlik, kabul kriterleri, regresyon, keşif testi, hata / hata raporu, risk bazlı, sezgisel, test tamamlama raporu. Keep the old words as trigger and import aliases only. "Test basis", "test object" and "testware" are not used in the English text; "1-switch" is correct under CTAL-TA v4.0 (N-switch coverage).

## Part 3: domain packs, verified changes

| Pack line | Change | URL |
|---|---|---|
| public-sector.md L19 | The Digital Transformation Office was closed (CBK 183, RG 28.03.2024; search-level). Cybersecurity sits with Siber Güvenlik Başkanlığı under Law 7545 (RG 19.03.2025/32846). | https://www.alomaliye.com/2025/03/19/7545-sayili-siber-guvenlik-kanunu/ |
| Accessibility rows in all packs (public-sector L21, ecommerce L24, fintech §5, health, telecom) | Genelge 2025/10 (RG 21.06.2025/32933): WCAG 2.2 with an A-level checklist. One year: public bodies, banks, private hospitals, telecom operators above 200,000 subscribers. Two years: e-commerce providers (Law 6563). | https://www.alomaliye.com/2025/06/21/web-siteleri-ve-mobil-uygulamalarin-erisilebilirligi-2025-10/ |
| ecommerce.md L18 | Mesafeli Sözleşmeler amendment (RG 24.05.2025/32909, in force 01.01.2026): return with the seller's named carrier is free; the pre-information form names the carrier and mediation; Art. 13(3) and 15(1)(i) repealed. | https://www.alomaliye.com/2025/05/24/mesafeli-sozlesmeler-yonetmeliginde-degisiklik-24-05-2025/ |
| ecommerce.md L21 | E-arşiv invoice is mandatory regardless of amount since 01.01.2026 (VUK 509 as amended by 573). | https://sovos.com/tr/blog/kdv/e-belge-uygulamalarinda-hassas-donem/ |
| telecom.md L19 | BTK amendments in force 25.06.2026: only electronically verifiable ID; line caps of 6 (citizens), 3 (foreigners), 1 (tourists); quarterly re-checks. Law 7590 (July 2026) moves domain-name and Law 5651 duties to the SGB. | https://www.trthaber.com/haber/bilim-teknoloji/btkdan-sahte-hatlara-karsi-yeni-duzenleme-947885.html ; https://www.teknoblog.com/btk-nin-internet-yetkileri-sgb-ye-gecti/ |
| health.md L18 | The pack does not name the Kişisel Sağlık Verileri Yönetmeliği, amended RG 04.07.2026/33300 (new Art. 13/A). New: Bilgilendirilmiş Rızanın Elektronik Ortamda Alınması Yönetmeliği (RG 27.10.2026/33413): SMS-OTP consent, hash and timestamp, logs, no e-consent without a verifiable legal representative. | https://www.resmigazete.gov.tr/eskiler/2026/10/20261027-4.htm ; https://www.alomaliye.com/2026/07/04/kisisel-saglik-verileri-hakkinda-yonetmelikte-degisiklik-04-07-2026/amp/ |
| fintech.md L19 | TCMB payment-services regulation amended (RG 19.03.2026/33201): safeguarding cut-off moves 15:00 → 16:30, half days 11:00 → 12:00. PSD3/PSR: texts agreed April 2026, not yet in the Official Journal. | https://www.alomaliye.com/2026/03/19/odeme-hizmetleri-ve-elektronik-para-ihraci-ile-odeme-hizmeti-saglayicilari-degisiklik/amp/ |
| insurance.md L22, L45 | BES state contribution 30% → 20% from 01.01.2026 (Karar 10811). The pack hard-codes no rate; add it to `docs/volatile-facts.json`. | https://medyascope.tv/2026/01/07/beste-devlet-katkisi-yuzde-30dan-yuzde-20ye-indi/ |

No amendment was found for the BDDK information-systems regulation, MASAK or SEDDK. KVKK: Law 7499 (in force 01.06.2024) changed Art. 6 and 9; the packs' wording still holds. Typo: fintech.md §5 "WCAG 2.2.2.1" should read "WCAG 2.2 SC 2.2.1".

## What is already right
- Charter template, time box, debrief and session sheet match CTFL §4.4.2 and CTAL-TA §3.4.1.
- Follow-the-data and the "bug if" attack table are what EVALUATION §8 credits for the Opus and Sonnet gains; keep the content and reorder it.
- Synthetic-first, default-drop, HMAC-only hashing and "pseudonymised is still personal data".
- An independent oracle from the mapping, Decimal totals, zero-failure sampling arithmetic (299 and 2,995 are correct), tolerances agreed before the first mock.
- Privacy-safe `results.json` and stable TC IDs.

## Not worth doing
- Full HTSM quality-criteria and technique lists: more guidewords hurt weak models.
- More tours or FEW HICCUPPS in SKILL.md: keep them in the reference.
- Format-preserving encryption or differential privacy in `mask_data.py`: not possible with the standard library, low use.
- Database connectors for `reconcile.py`: the SQL templates cover it.
- Renaming tags or JSON keys (BUG, `önem`) to glossary terms: breaks parsers; change display strings only.
