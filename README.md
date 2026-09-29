# QA Suite: Yapay zekâ için profesyonel yazılım test skill'leri

Gereksinimden içe aktarılabilir test paketine ve çalışan Playwright otomasyonuna uzanan uçtan uca test sürecini yapay zekâ asistanlarına (Claude Code, claude.ai, Claude API ve Agent Skills standardını destekleyen diğer araçlar) **profesyonel bir test analisti disipliniyle** yaptıran skill paketi. Çıktılar Türkçe ve İngilizce üretilebilir.

> **Farkı:** Kombinasyonları yapay zekâya tahmin ettirmez. Sınır değerleri, karar tabloları, durum geçişleri ve pairwise setleri **deterministik script'lerle hesaplanır**. Bu script'lerin bulduğu boşluklar ve çelişkiler, netleştirme sorusu olarak geri döner. Gereksinimden Jira'ya ve otomasyon sonucuna kadar **tek bir ID zinciri** (REQ → DS → TC → `@TC` etiketli Playwright testi → sonuç → RTM) korunur.

## Skill'ler

| Skill | Ne yapar | Script |
|---|---|---|
| `qa-orchestrator` | Uçtan uca akışı yönetir: aşamalar, kapılar, final özeti | – |
| `analyzing-requirements` | Gereksinimleri atomik ve izlenebilir hale getirir. ISO 29148 kalite incelemesi, belirsizlik ve çelişki taraması, örtük ve fonksiyonel olmayan gereksinim keşfi (ISO 25010:2023), risk puanlama ve netleştirme soruları üretir. | `lint_requirements.py` (TR/EN belirsizlik linter'ı) |
| `designing-test-cases` | ISTQB tekniklerini kullanarak risk bazlı test tasarımı yapar ve standart formatta manuel test case'ler yazar. | `ep_bva.py`, `decision_table.py`, `state_transition.py`, `pairwise.py` |
| `tracing-requirements` | Çift yönlü izlenebilirlik matrisi (RTM) üretir. Şema doğrulaması, risk sıralı kapsam boşlukları, sahipsiz ve kopya testler ile değişiklik etki analizi yapar. | `build_rtm.py` |
| `exporting-test-cases` | Xray, Zephyr Scale, Excel (.xlsx), CSV ve Markdown formatlarına export eder. Türkçe karakterleri güvenli şekilde kodlar. | `export_tests.py` |
| `automating-with-playwright` | Test case'leri Playwright (TypeScript) otomasyonuna dönüştürür. Proje iskeleti, Page Object ve fixture'lar, `@TC` etiketli spec'ler üretir ve koşum sonuçlarını RTM'ye geri besler. Xray'e sonuç aktarımını da destekler. | `scaffold_project.py`, `generate_specs.py`, `check_automation.py`, `pw_results.py` |
| `writing-bdd-scenarios` | Test case'lerden TR/EN Gherkin `.feature` dosyaları üretir, bunları bildirimsel dile çevirir ve playwright-bdd ile koşturur. | `generate_features.py` |

Tüm script'ler **yalnızca Python standart kütüphanesini** kullanır (Python 3.9+). Ek kurulum gerekmez. Otomasyonu koşturmak için ayrıca Node.js 18+ ve `@playwright/test` gerekir. BDD için `playwright-bdd` de gerekir.

Gereksinimler ve test case'ler elle JSON olarak yazılmaz. Kompakt bir metin formatında (`*.src.md`) yazılır, `qa_compact.py` bunu doğrulayıp JSON'a çevirir. JSON'a göre yaklaşık %35–60 daha kısa, bozuk JSON riski yok, ortak ön koşullar `setup` bloklarıyla bir kez tanımlanıyor.

## Kurulum

**Claude Code (plugin olarak):**
```bash
claude plugin marketplace add C:/projeler/TestSkills
claude plugin install qa-suite@qa-suite-marketplace
```
Depo GitHub'a yüklendiğinde yerel yol yerine `kullanici/repo` yazılır.

**Claude Code (tek tek skill olarak):** `skills/<skill-adı>` klasörlerini `~/.claude/skills/` (kişisel) veya projedeki `.claude/skills/` klasörüne kopyalayın.

**claude.ai / Claude API:** Her skill klasörünü zip'leyip Skills bölümünden yükleyin. Frontmatter yalnızca taşınabilir alanlar içerdiği için olduğu gibi kabul edilir.

**Diğer araçlar (Codex, Copilot, Cursor, Gemini CLI…):** Paket açık Agent Skills standardına (SKILL.md) uyar. Aracın skills klasörüne kopyalamanız yeterlidir.

## Kullanım örnekleri

```
Bu user story'yi analiz et, eksik gereksinimleri ve soruları çıkar: <story>
Ekteki SRS için tüm test case'leri çıkar, Xray'e aktarılacak CSV hazırla.
Kredi başvuru formu için sınır değer ve karar tablosu testlerini tasarla.
Test kapsamımızı çıkar: hangi gereksinimler test edilmiyor?
REQ-004 değişti, hangi testleri yeniden koşmalıyız?
Smoke testlerini Playwright ile otomatize et ve sonuçları RTM'ye bağla.
Bu test case'lerden Türkçe Gherkin senaryoları yaz.
```

Üretilen dosyalar projede `qa/` klasörüne yazılır:

```
qa/requirements.json   qa/analysis-report.md   qa/clarifications.md
qa/design/DS-*.json|md qa/test-cases.json      qa/rtm.md|csv   qa/exports/*
qa/results.json        qa/automation-coverage.md
automation/            (Playwright projesi: playwright.config.ts, pages/, tests/*.spec.ts)
features/              (Gherkin, isteğe bağlı)
```

Otomasyon döngüsü:
```
test-cases.json ─generate_specs.py→ tests/*.spec.ts (@TC-001, test.fixme iskelet)
   → uygulanır → npx playwright test → results.json ─pw_results.py→ qa/results.json ─build_rtm.py→ RTM
```
İskeletler `test.fixme` ile işaretlidir. Uygulanmamış bir test hiçbir zaman "passed" olarak raporlanmaz.

## Standart temeli

- **Test tasarımı:** ISTQB CTFL v4.0 ve CTAL-TA v4.0, ISO/IEC/IEEE 29119-3/-4
- **Gereksinim mühendisliği:** ISO/IEC/IEEE 29148:2018, INCOSE yazım kuralları, EARS, INVEST, Gherkin (TR anahtar kelimeleri dahil)
- **Kalite modeli:** ISO/IEC 25010:2023 (9 karakteristik)
- **Erişilebilirlik:** WCAG 2.2 AA
- **Güvenlik:** OWASP ASVS 5.0, OWASP Top 10:2025, API Security Top 10, LLM Top 10

Standart metinleri kopyalanmamıştır. İçerikler uygulanabilir kontrol listeleri halinde yeniden ifade edilmiştir.

## Geliştirme

```bash
python tools/sync_shared.py          # shared/data-model.md dosyasını skill'lere kopyalar
python tools/validate_skills.py      # Agent Skills spesifikasyonu + paket kuralları
python -m unittest discover -s tests # script regresyon testleri
```

Ortak veri modeli yalnızca `shared/data-model.md` dosyasında düzenlenir. Skill'lerdeki kopyalar `sync_shared.py` ile güncellenir.

Skill kalite değerlendirmeleri (evals) `evals/` klasöründedir.

## Sürüm notları

**0.3.0**: Faz 2, Playwright ve BDD otomasyonu
- **2 yeni skill ve 5 yeni script.** Proje iskeleti, `@TC` etiketli spec üretimi (veri güdümlü gruplar dahil), otomasyon kapsam raporu ve Playwright sonuçlarının RTM'ye aktarımı. Türkçe/İngilizce Gherkin üretimi.
- **Gerçek bir koşuyla doğrulandı (Playwright 1.63, playwright-bdd 9.2):**
  - 30 spec derlendi.
  - Demo uygulamaya yerleştirilen 100,00 TL sınır hatası hem Playwright hem Türkçe BDD senaryosunda yakalandı ve RTM'de REQ-002 "failed" göründü.
  - 11 Türkçe feature dosyası Gherkin ayrıştırıcısından hatasız geçti.
- **Ek alanlar:** Test case'e `ext:` (Xray test anahtarı) alanı eklendi. Anahtar, Playwright testinde `test_key` annotation'ı olarak taşınıyor.

**0.2.0**: öncelik kalibrasyonu ve maliyet
- **Öncelik artık test başına veriliyor.** Gereksinimden miras alınmıyor. Risk puanlamasında somut ölçütler var ve "kararsızsan düşük puan" kuralı uygulanıyor.
- **`build_rtm.py` iki yeni kontrol yapıyor:** PRIORITY_SKEW (%20'den fazla kritik test) ve REDUNDANT (aynı denklik sınıfından gereksiz testler).
- **Kompakt yazım formatı (`qa_compact.py`) ve okuma planları eklendi.** Light/full mod ayrımı ve test bütçesi (tek story için 15–35 test) de geldi.
- **Eval sonuçları, 0.1.0'a göre:**
  - Token %31, süre %42 azaldı.
  - Kritik test oranı %38 ve %30'dan %10 ve %6'ya indi.
  - Çelişki yakalama korundu.

**0.1.0**: ilk sürüm (5 skill, 7 script, eval'ler).

## Yol haritası

- **Faz 1 (tamam):** Gereksinim analizi, test tasarımı, RTM, Xray/Zephyr/Excel export, evals
- **Faz 2 (tamam, 0.3.0):** Playwright (TypeScript) otomasyonu ve BDD/Gherkin (TR/EN). Aynı TC ID'leri korunuyor, sonuçlar RTM'ye aktarılıyor.
- **Faz 3:** Fonksiyonel olmayan testler (performans senaryoları, WCAG 2.2 eşlemesi, OWASP ASVS eşlemesi), test planı ve strateji (29119-3), hata raporu ve test tamamlama raporu, test case denetleyicisi
- **Faz 4:** Tetiklenme (description) optimizasyonu, alan paketleri (fintech, e-ticaret, sağlık, kamu), marketplace'te yayın

## Lisans

MIT. Frontmatter'daki `license` alanı; ihtiyaca göre değiştirilebilir.

---

### English summary

QA Suite is a bilingual (TR/EN) set of Agent Skills. It turns requirements into a professional, traceable test package:
- requirement quality analysis with clarification questions
- risk-based test design, where EP/BVA, decision tables, state transitions and pairwise are computed by standard-library Python scripts
- an RTM with a gap report
- import-ready exports for Xray, Zephyr Scale and Excel
- Playwright (TypeScript) and BDD automation. Every automated test keeps its `@TC-###` tag, and the results flow back into the RTM.

Install it as a Claude Code plugin (`claude plugin marketplace add <path-or-repo>`), or copy the `skills/*` folders into any client that supports Agent Skills.
