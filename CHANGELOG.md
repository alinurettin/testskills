# Değişiklik günlüğü

**0.7.1**: Dış (Gemini) incelemesinden gelen sağlamlaştırma
- **Export:** CSV formül enjeksiyonu (CWE-1236) kapatıldı. Riskli hücrelerin başına `'` ekleniyor; madde işaretleri ve negatif sayılar korunuyor; eski davranış için `--no-formula-escape`.
- **`openapi_tests.py`:** OpenAPI 3.1'deki `type: ["string","null"]` gibi tip listelerinde artık çökmüyor.
- **`decision_table.py`:** Kombinasyon patlamasına karşı sınır eklendi (varsayılan 2048, değiştirmek için `--max-combinations`); aşıldığında yol gösteren bir hata mesajı veriyor.
- **`ep_bva.py`:** Sıfır veya negatif adım (`step`) ile ters aralık (min > max) artık hata kodu 2 ile reddediliyor.
- **Testler:** `tests/test_hardening.py` eklendi.

**0.7.0**: Derinleştirme, kanıt ve paylaşım hazırlığı
- Skill açıklamaları 15.079 karakterden 7.441'e kısaltıldı (skill listesi bütçesi); CI bütçeyi koruyor.
- `--req-map`: API, mobil, NFR ve AI üreticilerinde testler doğru gereksinime bağlanıyor; veri taşıma sonuçları `results.json`/RTM'ye akıyor; uçtan uca zincir testi.
- Ortak `tr_ids.py` (TCKN/VKN/IBAN) ve kimlik politikası; ortak `junit_results.py` (Selenium, Cypress, pytest, REST Assured...); `.xlsx` inceleme importu.
- Export formatları üretici dokümanlarıyla doğrulandı (Zephyr etiket ayracı artık virgül: kırıcı değişiklik); import kiti ve golden testler.
- `docs/volatile-facts.json` + CI uyarısı; Play API 36, Node 22+, AB AI Act güncellendi. Xray `requirements` notu yalnızca Jira anahtarı taşıyor.
- Hızlı başlangıç, manuel test rehberi, gizlilik bölümü, CONTRIBUTING, issue şablonları; cevap anahtarları `evals/keys/`.
- 5 yeni bağımsız kör deneme; skill'li/skill'siz 30 koşu (sonuçlar karışık, bkz. `docs/EVALUATION.md` §7).
- 266 test.

**0.6.0**: Faz 5, kapsam genişletme ve kör denemeler
- **6 yeni skill, toplam 17:**
  - `testing-apis`: OpenAPI 3'ten sözleşme testleri ve aynı TC ID'leriyle koşturulabilir Playwright API paketi üretir. Kapsamı: şema kontrolü, sınır/enum/tip/pattern testleri, 401 ve `Bearer`'sız başlık, yol ve gövde düzeyinde BOLA, önce oluşturup sonra okuma, hata gövdesi şeması, sözleşme boşluğu soruları, istek/yanıt kanıtı.
  - `running-exploratory-tests`: SBTM ile keşif testi. Riske göre sıralı görev kartları, sezgisel yöntem kataloğu, oturum notu şablonu; notlardan özet, hata taslakları ve regresyon testleri üretilir.
  - `testing-ai-features`: LLM, chatbot ve RAG testi. OWASP LLM Top 10 2025'e eşlenmiş TR/EN saldırgan eval seti, tekrarlı koşularda deterministik puanlama, kararsızlık tespiti ve yayın kapısı, rubrik şablonu.
  - `preparing-test-data`: geçerli TCKN/VKN/IBAN'lı, ilişkisel bütünlüklü, seed'li sentetik veri; HMAC ile deterministik maskeleme (KVKK/GDPR); test case'lerin veri ihtiyacı analizi.
  - `testing-mobile-apps`: iOS/Android kontrol listesi (82 kontrol), MASVS ve WCAG eşlemesi, kullanım payından cihaz matrisi, Maestro şablonu, JUnit → `results.json` dönüştürücü.
  - `testing-data-migrations`: kaynak–hedef mutabakatı (anahtar kümeleri, alan dönüşümleri, Decimal kontrol toplamları, Türkçe kodlama bozulması teşhisi), SQL şablonları, imza kriterleri.
- **Export:** TestRail, Azure DevOps Test Plans ve Qase formatları eklendi.
- **Regresyon seçimi:** `select_regression.py` eklendi. Seçim must/should/could katmanlarında gerekçeleriyle yapılır; test sayısı veya süre bütçesi aşılırsa dışarıda kalanlar kalan risk olarak raporlanır. Otomatik testler için Playwright `--grep` komutu üretilir.
- **Sektör paketleri:** sigorta/emeklilik ve telekom eklendi (toplam 6).
- **Kör denemeler:**
  - API denemesinde yerleştirilen 5 hatanın 5'i ve yerleştirilmemiş 2 gerçek hata bulundu. Bağımsız yeniden koşum aynı sonucu verdi.
  - Veri taşıma denemesinde yerleştirilen 9 hatanın 9'u bulundu, yanlış alarm çıkmadı.
  - Denemelerden gelen 12 bulgunun 11'i düzeltildi, 1'i README'de belgelendi. Ayrıntılar: `docs/EVALUATION.md`, gerçek çıktılar: `examples/`.
- **Yönlendirme:** `tools/routing_proxy.py` eklendi. Vekil ölçüm 17 skill ve 84 istekte 84/84 verdi.
- **Düzeltmeler:**
  - `qa_compact.py` artık `# QUESTION` gibi yorum satırlarını her yerde kabul ediyor.
  - İki script'in `--help` çıktısı Windows cp1254 konsolunda çöküyordu; düzeltildi.
  - RTM'nin REDUNDANT kontrolü `generated` etiketli üretici çıktısını atlıyor.
- **Testler:** 70'ten 150 birim testine çıktı.

**0.5.1**: Herkese açık paylaşıma hazırlık
- **Lisans ve dokümantasyon:** MIT lisansı eklendi. README Türkçe ve İngilizce olarak yeniden yazıldı; kanıt tablosu, kurulum adımları, Mermaid akış şeması ve bilinen sınırlar bölümleri eklendi.
- **Örnek çıktılar:** `examples/fast-transfer` klasörüne kör uçtan uca denemenin gerçek çıktıları kondu.
- **Paketleme:** `tools/package_skills.py` ile claude.ai'ye yüklenecek skill zip'leri üretilebiliyor.
- **Manifest:** Plugin ve marketplace manifest'ine lisans ve depo bilgisi eklendi. İkisi de `claude plugin validate` kontrolünden uyarısız geçiyor.
- **Görsel:** Paylaşım görseli eklendi: `docs/assets/qa-suite-card.png`.

**0.5.0**: Faz 4, sektör paketleri ve yayına hazırlık
- **4 sektör paketi** (fintech/bankacılık, e-ticaret, sağlık, kamu). Her biri analiz ve tasarım skill'lerine eklendi ve şunları içeriyor: kontrol edilecek mevzuat, örtük gereksinimler, yüksek riskli kurallar ve teknikler, sentetik test verisi, tipik hatalar.
- **`check_ids.py`:** TCKN/VKN/IBAN test verisini doğrular ve tek hatalı geçersiz varyantlar türetir. Geçerli kimlik üretmez.
- **`tools/trigger_eval.py`:** tüm skill'ler için Windows uyumlu tetiklenme ve yönlendirme ölçümü (`claude -p`, giriş yapılmış CLI gerekir).
- **Vekil yönlendirme ölçümü:** 42/42 ve 20 zor istekte 20/20. Gerçek tetiklenme mekanizması ölçülmedi.
- **Depo CI'ı (GitHub Actions):** senkronizasyon kontrolü, skill doğrulaması ve birim testleri.
- **Export skill'i:** Excel/CSV'deki testler için önce içe aktarma ve inceleme yönlendirmesi eklendi.

**0.4.0**: Faz 3, planlama, fonksiyonel olmayan testler, raporlama ve inceleme
- **4 yeni skill ve 7 yeni script.** Paket artık 11 skill içeriyor:
  - `planning-tests`: sayıları QA artefaktlarından hesaplanan test planı ve makine tarafından kontrol edilebilen çıkış kriterleri.
  - `testing-nonfunctional`: gereksinim eşiklerinden k6 script'i (Node sözdizimi kontrolünden geçti), WCAG 2.2 A/AA'nın 55 kriteri (31 A + 24 AA, TR/EN), ASVS 5.0'ın 17 bölümüne göre güvenlik testleri.
  - `reporting-test-results`: hata raporu standardı; tamamlama raporunda eksik veri "bilinmiyor" olarak gösterilir, asla 0 varsayılmaz.
  - `reviewing-test-cases`: Excel/TestRail CSV içe aktarımı ve Türkçe/İngilizce yazım kalitesi kontrolleri.
- **Ek iyileştirmeler:**
  - `qa_compact.py --lenient`: içe aktarılan setler için.
  - `.gitattributes`: satır sonları LF'ye sabitlendi.

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
