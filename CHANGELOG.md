# Değişiklik günlüğü

**0.11.0**: Denetimden ertelenen maddeler
- **Kapsam hesabı:** yeni `design_coverage.py` her tasarım spesifikasyonu için kapsanan/toplam kapsam öğesini, kapsanmayanları ve eskimiş referansları verir (`--min-coverage` ile kapı).
- **Teknikler (CTAL-TA v4.0):** metamorfik test ve test sonucunu bilen (oracle) problemi, alan testi, rastgele test eklendi; CRUD testi fonksiyon × varlık matrisi olarak düzeltildi. Yeni teknik kodları: `mt`, `dom`, `rnd`.
- **Durum geçişi:** `--switch 0|1|2|3` (N-switch) ve ulaşılan kapsam sayıları (durum, geçiş, zincir).
- **Yapay zekâ:** eşleştirilmiş vakalarda tutarlılık kontrolü (`pair`); başlangıç setinde aynı zararlı istek Türkçe, ASCII Türkçe ve İngilizce.
- **Güvenlik:** `nfr_checklist.py asvs --level` artık filtreliyor; SSRF, XXE, CORS, `__Host-` çerez öneki, WebSocket ve kiracı izolasyonu kontrolleri eklendi (alt madde numaraları doğrulanmadı).
- **Otomasyon:** `check_automation.py` statik lint (sabit bekleme, `test.only`, `force: true`, ham CSS/XPath, parola sabiti, `networkidle`); kararsız (flaky) test politikası.
- **Test verisi:** `mask_data.py` k-anonimlik ve l-çeşitlilik raporu (`quasi_identifiers`, `min_k`), geri çevrilebilir hash uyarısı.
- **İzlenebilirlik:** yeni boşluk `READY_ON_ASSUMPTION` (açık soruya ya da onaylanmamış türetilmiş gereksinime dayanan "hazır" öğeler).
- **Orkestratör:** yapay zekâ çıktısı bir kişi inceleyene kadar taslak kalır; girdide kişisel/gizli veri kontrolü; teslim özetinde neyin script'le hesaplandığı ve kimin incelediği.
- **Diğer:** çıkış kriteri şablonuna yeni kriterler; erişilebilirlikte axe `incomplete` sonuçları ve EN 301 549 notu; resmi Türkçe terimler (denklik payı, hata tahminleme, test başlatma belgesi) script çıktılarında ve README'de. `examples/` altındaki geçmiş deneme çıktıları değiştirilmedi.
- Bu sürüm için yeni kör deneme yapılmadı. 463 test.

**0.10.0**: Uzman denetimi (ISTQB müfredatları ve standartlarla karşılaştırma) ve yanlış sonuç veren script'lerin düzeltilmesi
Beş alan güncel kaynaklarla denetlendi (CTFL v4.0.1, CTAL-TA v4.0, CTAL-TM v3.0, CT-AI v2.0, CT-TAE, CT-PT, ASVS 5.0, TTB Sözlüğü v2.0). Raporlar ve yapılan/ertelenen listesi: `docs/audit-2026-11/`.

**Davranış değişiklikleri (önce bunları okuyun):**
- `completion_report.py`: bloke testler artık koşulmuş sayılmıyor (koşulan = geçen + kalan). Açık bir hatanın geçerli önem derecesi yoksa ya da `results.json`'daki hata anahtarı kayıtta yoksa açık hata kriterleri "bilinmiyor" olur. Yanlış yazılmış kriter adı yok sayılmaz, "bilinmiyor" olur. `automation_pct` artık otomatize edilen ÷ otomasyon hedefi; eski değer `automated_of_executed_pct`.
- Risk seviyesi (dört script'te aynı kural): etkisi 5 olan gereksinim en az "yüksek", olasılığı da 3 veya üstüyse "kritik".
- `select_regression.py`: zorunlu (must) testler bütçeye sığmazsa çıkış kodu 1; bütçe gereksinimlere yayılarak doldurulur (`--order breadth|depth`).
- `ai_eval.py score`: karar artık GEÇTİ / KALDI / EKSİK. Koşulmamış ya da değerlendirilemeyen vaka, 3'ten az koşu (kritikte 5), taslak vaka veya bekleyen puanlama varsa EKSİK (çıkış kodu 1). Gevşetmek için `--min-runs`, `--min-runs-critical`, `--allow-draft`, `--allow-pending`. Puanlama bekleyen vakalar oranlara girmez.
- `generate_k6.py`: hedef yük, hata oranı eşiği ya da (kapalı modelde) düşünme süresi verilmemişse uydurma varsayılan kullanmaz, çıkış kodu 2 verir. Eşikler kararlı durumdaki başarılı yanıtlar üzerinden hesaplanır.
- `check_automation.py`: içinde doğrulama (`expect`) olmayan test otomatize sayılmaz.
- `decision_table.py`: `infeasible` kullanılan sadeleştirilmiş tablolarda kolon sayısı ve `-` hücreleri için seçilen değerler değişebilir. `ep_bva.py` ve `decision_table.py` çıktılarında başlık "Kapsam öğeleri → test girdileri" oldu.

**Düzeltmeler ve eklemeler:**
- Test yönetimi: feragat (waiver) durumu (onaylayan, gerekçe, son tarih; ajan kendi yazamaz), risk seviyesine göre kapsam tablosu ve `min_requirements_passed_pct`, "bilinen hatalarla yayın" listesi, durum raporunda önceki döneme göre fark ve askıya alma kontrolü, üç noktalı tahmin (aralık ve varsayımlarla).
- Test tasarımı: 3 değerli sınır değer analizi referans ve script'te tutarlı (`bva_scope`), açık aralık sınırları (`min_exclusive`/`max_exclusive`) artık işleniyor, karar tablosunda olanaksız kombinasyonlar birleştirmeyi engellemiyor, kullanılmayan koşul değerleri ve kapsanan gereksiz kurallar raporlanıyor.
- Yük testi: açık/kapalı yük modeli, işlem karışımı, test verisi parametreleri, `dropped_iterations` eşiği, beklenen 4xx'in hata sayılmaması; yeni `k6_results.py` sonuçları `qa/results.json`'a yazar. **k6 kurulu olmadığı için üretilen script'ler gerçek k6'da koşturulmadı**; yalnızca sözdizimi kontrolünden ve bir Node benzetiminden geçti.
- Güvenlik: ASVS 5.0.0 bölüm eşlemesi düzeltildi (oran sınırlama V2, HSTS V3, tarayıcı depolama V14, SCA ve mass assignment V15).
- Yapay zekâ: oranların yanında %95 Wilson güven aralığı; değerlendirilemeyen kontrolü olan koşu artık geçmiş sayılmıyor.
- Keşif testi: küçük modeller için yeniden yazıldı (en üstte "asgari yol", gövde 889 kelime); yeniden üretilemeyen hata soruya indirilmiyor, `confidence: seen once` ile raporlanıyor. **Bu sürüm henüz yeniden denenmedi.**
- Sektör paketleri: 2024–2026 mevzuat değişiklikleri işlendi (Siber Güvenlik Başkanlığı, 2025/10 erişilebilirlik genelgesi, BTK kimlik doğrulama, mesafeli sözleşmeler, e-arşiv, BES devlet katkısı %20 ve diğerleri); 11 yeni kayıt `docs/volatile-facts.json`'da. İki madde tek ikincil kaynağa dayanıyor (e-arşiv, sağlık verisi yönetmeliği).
- `shared/glossary-tr.md`: yaklaşık 85 terimin resmi Türkçe karşılığı (TTB Sözlüğü v2.0, CTFL v4.0.1 TR). Keşif skill'inin çıktıları resmi terimleri kullanıyor; diğer dosyalar henüz güncellenmedi.
- Değerlendirme: `tools/eval_stats.py` ile güven aralıkları. Üç model birlikte +2,7 puan (%95 GA +1,0…+4,4, p = 0,014); tek tek modellerde fark ayırt edilemiyor. 0.9.0'daki "en çok zayıf modele yarıyor" ifadesi düzeltildi.
- Testler: 282'den 387'ye.
**0.10.0 içinde ayrıca (22 Ekim): correctness and local workflow hardening**
- Pairwise: bounded exact completion, independent final coverage, explicit unknown/infeasible distinction, seed/domain validation and resource limits; incomplete coverage exits 1.
- API: preserved schema composition/ref siblings, checked sample synthesis, explicit UNVERIFIED skeletons, HTTP code ranges, conservative response validation and safe-by-default evidence attachments. Independent upstream JSON Schema fixtures execute in Python and TypeScript.
- Synthetic data: exact decimal scale bounds/JSON numbers, timezone-consistent edges, transactional distinct references and final invariants.
- XLSX: versioned hidden metadata for lossless selected-test roundtrips; reviewed plan/apply with source hashes, conflict detection, migration and local delta manifests. Guard against stale compact-source regeneration after apply.
- Local doctor, evaluation manifest/record/report tooling, task-level statistics, contamination tracking and documented host/dependency matrix. CI configured for Windows/Linux, Python 3.12/3.13 and Node 24.
- No new paid model evaluation or live vendor lifecycle verification is claimed. Historical results are preserved. New workflows and limits: `docs/HARDENING.md`.
- Türkçe: kapsam ve API doğruluğu, hassas kanıtların ayıklanması, test verisi kısıtları ve kayıpsız Excel güncellemeleri sağlamlaştırıldı. Yeni araçlar ve sınırlamalar belgelendi; geçmiş deney sonuçları değiştirilmedi.

**0.9.0**: Keşif skill'i düzeltmesi ve 126 koşuluk yeni değerlendirme
- 7 yeni bağımsız deneme ve cevap anahtarı; Opus, Sonnet 5.5 ve Haiku ile skill'li/skill'siz 126 koşu. Skill'ler en çok zayıf modele (Haiku) katkı sağlıyor (+3,9 puan); güçlü modellerde fark küçük. Ayrıntı: `docs/EVALUATION.md` §8.
- Keşif testi skill'i yeniden düzenlendi (aşağıda): Opus'ta 74'e karşı 90, Haiku'da hâlâ geride.
- `running-exploratory-tests`:
  - **Kısa oturum modu** (45 dakikanın altı): tek satırlık görev cümlesi, test ederken alınan notlar, sonda tek rapor; sürenin en az %75'i uygulamanın üzerinde. Tam SBTM evrakı uzun ve çok oturumlu işlerde kalıyor.
  - **Veriyi takip et:** her durum değişikliğinden sonra aynı verinin göründüğü tüm ekranlar, listeler, toplamlar, dışa aktarımlar ve API yanıtı yeniden kontrol ediliyor; yenileme, geri/ileri, ikinci sekme ve yeniden girişten sonra da.
  - **Kısa web/API saldırı listesi:** çift gönderim ve istek tekrarı, eşzamanlılık, geri/yenile/derin bağlantı, sınırlar, Türkçe karakter ve büyük/küçük harf (İ/ı), para yuvarlama ve biçim tutarlılığı, zaman kuralları, hata mesajında bilgi sızıntısı, klavye ve ekran okuyucu, kimlik değiştirerek yetki.
  - Ayrıntılar referansa taşındı (16 bölüm); SKILL.md gövdesi 157 satır.
- `sbtm.py`: 10–45 dakikalık oturumlar artık süre uyarısı vermiyor; uyarı yalnızca 10 dakikanın altı ve 180 dakikanın üstü için.
- 5 yeni test: kısa oturum ayrıştırma, süre uyarısı sınırları, referans bölüm numaraları, SKILL.md içeriği.

**0.8.0**: Uluslararası test verisi, API güvenlik denemeleri, OWASP LLM 2026
- `preparing-test-data`: `card_test` (yalnızca yayımlanmış sandbox test kartları, Luhn), `phone_intl` (ABD/İngiltere kurgusal numara aralıkları), `iban` (TR, DE, GB, FR, NL, ES, IT için mod-97). Ortak `tr_ids.py`'ye `luhn_ok` ve `gen_iban` eklendi.
- `testing-apis`: isteğe bağlı `--security-probes` ile işlem başına bir SQL enjeksiyonu ve bir XSS denemesi (5xx yok, veritabanı hatası sızmıyor, HTML'de kaçırılmamış betik yok).
- `testing-ai-features`: OWASP LLM Top 10 2026 birincil sürüm; 2025 kimlikleri çapraz referans olarak korunuyor (referans tablosu ve README güncellendi).

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
