# Değişiklik günlüğü

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
