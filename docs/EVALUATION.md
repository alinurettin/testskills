# Değerlendirme raporu: QA Suite 0.6.0

**[English →](EVALUATION.en.md)**

Bu belge, paketin nasıl test edildiğini ve hangi sonuçları verdiğini **abartmadan** özetler: neyin ölçüldüğü, neyin ölçülmediği ve bulguların skill'e nasıl geri döndüğü. Tüm denemeler 29–30 Eylül 2026'da Claude (Opus sınıfı model) ile yapıldı. Tekrarlanabilmeleri için deneme dosyaları `evals/` altında duruyor.

## Özet
| Değerlendirme | Ne ölçer | Sonuç |
|---|---|---|
| Kör uçtan uca deneme: FAST transfer (0.5.0) | Story → analiz → tasarım → Playwright → rapor zinciri | Yerleştirilen **5/5 hata** + 1 gerçek hata; yayın kararı doğru ("hazır değil") |
| Kör API denemesi (0.6.0) | `testing-apis`: OpenAPI → sözleşme ve yetkilendirme testleri | Yerleştirilen **5/5 hata** + 2 gerçek hata; 17 sözleşme sorusu; bağımsız yeniden koşum aynı sonucu verdi (31/11) |
| Kör veri taşıma denemesi (0.6.0) | `testing-data-migrations`: mutabakat, sınıflandırma, go/no-go | Yerleştirilen **9/9 hata**; tuzaklarda yanlış alarm yok; karar doğru (no-go) |
| Skill'li / skill'siz karşılaştırma (0.2.0) | 3 görev, sabit kontrol listesiyle puanlama | Geçme oranı %93'e karşı %82 (+11 puan) |
| Vekil yönlendirme ölçümü | Doğru skill'in adından ve açıklamasından seçilmesi | 17 skill, 84 istek: **84/84** (yeni skill'ler için 22/22) |
| Birim ve regresyon testleri | 30 script'in davranışı | **150 test**, CI'da her push'ta koşar |

## 1. Kör uçtan uca deneme: FAST transfer
- **Kurulum:** Bir bankacılık user story'si (FAST para transferi) ve 5 hata yerleştirilmiş bir demo web uygulaması. Ajan uygulama kodunu ve cevap anahtarını görmedi.
- **Sonuç:** 5/5 hata bulundu, üstüne yerleştirilmemiş gerçek bir hata (binlik ayraçlı tutarın yanlış ayrıştırılması). Belirsizliklerin hepsi soru olarak raporlandı. 47 test tasarlandı (%2 kritik). Playwright koşumu 37 geçti / 9 kaldı; bağımsız yeniden koşum aynı sonucu verdi. Çıkış kriterlerinin 9'undan 4'ü karşılandığı için karar "hazır değil" oldu.
- **Maliyet:** ~334 bin token, ~26 dakika.
- Dosyalar: [evals/trial-fast](../evals/trial-fast/) · cevap anahtarı: [evals/keys/fast.md](../evals/keys/fast.md) · gerçek çıktılar: [examples/fast-transfer](../examples/fast-transfer/README.md)

## 2. Kör API denemesi: Demo Bank API
- **Kurulum:** OpenAPI 3 dokümanı ve yerelde çalışan bir API. İki test kullanıcısı vardı. 5 hata yerleştirildi: nesne düzeyinde yetkilendirme açığı (BOLA), uygulanmayan üst sınır, eksik alanda 500, 201 yerine 200, string dönen bakiye. Ajan uygulama kodunu ve cevap anahtarını görmedi.
- **1. koşu (0.6.0 taslağı):** Bir güvenlik sınıflandırıcısı ajanı keşif aşamasında durdurdu. İstem "bu bizim yerel test sunucumuz" diye netleştirilerek yeni bir ajanla tekrarlandı. Yarım kalan koşu yine de BOLA'yı, string bakiyeyi ve **yerleştirilmemiş bir hatayı** buldu: `Bearer` şeması olmadan gönderilen token kabul ediliyordu. Ayrıca 5 skill eksiği raporladı; hepsi düzeltildi.
- **2. koşu:** Yerleştirilen hataların **5'i de** bulundu. Yerleştirilmemiş iki gerçek hata daha çıktı: `Bearer`'sız token ve EUR hesaptan TRY transferin kur çevrimi olmadan kabulü. 42 test yazıldı (29'u üreticiden, 13'ü elle), sonuç 31 geçti / 11 kaldı. 17 sözleşme sorusu çıkarıldı. Hatalar kök nedene göre gruplandı (örneğin 200/201 sorunu tek hata, 4 test).
- **Bağımsız doğrulama:** Temiz sunucuda ajanın test paketini yeniden koşturduk: **31 geçti / 11 kaldı**, aynı sonuç.
- **Skill'e geri dönen 12 bulgu** (11'i 0.6.0'da düzeltildi; Windows konsolunda Türkçe yardım metni sorunu README'de belgelendi):
  - sözleşme boşlukları otomatik `# QUESTION` satırı olarak üretiliyor;
  - `pattern` alanları için geçersiz değer testi;
  - istek gövdesindeki kimlikler için BOLA iskeleti;
  - ID ile okumadan önce kaynağı `POST` ile oluşturma;
  - hata gövdesinin şema kontrolü;
  - istek ve yanıt kanıtının rapora otomatik eklenmesi (token maskelenir);
  - raporlayıcı ve durum bütçesi uyarıları;
  - üretilen testlerde RTM'deki yanlış "REDUNDANT" uyarısının giderilmesi.
- **Son hâliyle üretici** (aynı API, temiz sunucu): 31 test çıktı. İnsan müdahalesi olmadan 20 geçti / 9 kaldı / 2 iskelet. Kalan 9 test yerleştirilen 5 hatanın hepsini ve `Bearer` hatasını yakalıyor.
- Dosyalar: [evals/trial-api](../evals/trial-api/) · cevap anahtarı: [evals/keys/api.md](../evals/keys/api.md) · gerçek çıktılar: [examples/api-trial](../examples/api-trial/README.md)

## 3. Kör veri taşıma denemesi: müşteri verisi
- **Kurulum:** Eski sistemden alınan cp1254 kodlu, `;` ayraçlı 40 satırlık extract; yeni sistemden UTF-8 kodlu 41 satır; insan dilinde yazılmış bir mapping dokümanı. 9 hata yerleştirildi; ayrıca doğru olduğu hâlde naif karşılaştırmaların hatalı sanacağı tuzaklar kondu: Türkçe büyük harf İ/I, baştaki sıfırlar, fazla boşluklar, artık gün. Ajan doğru mapping'i ve cevap anahtarını görmedi.
- **Sonuç:** **9/9** hata bulundu ve doğru sınıflandırıldı (yükleme veya dönüşüm hatası). Tuzaklarda **yanlış alarm çıkmadı**. +335.121,21'lik kontrol toplamı farkının tamamı satır bulgularıyla açıklandı. Karar "go değil" oldu. 9 mapping sorusu çıkarıldı.
- **Süre:** ~3 dakika. Mutabakat script'i 0,2 saniyede koştu.
- **Skill'e geri dönenler:** "yuvarlama" ipucu hassasiyet kaybını da kapsayacak şekilde düzeltildi; boş değer oranlarındaki payda etkisi açıklandı; raporda tam dosya yolları yerine yalnızca dosya adı gösteriliyor.
- Dosyalar: [evals/trial-migration](../evals/trial-migration/) · cevap anahtarı: [evals/keys/migration.md](../evals/keys/migration.md) · gerçek çıktılar: [examples/migration-trial](../examples/migration-trial/README.md)

## 4. Skill'li ve skill'siz karşılaştırma (0.2.0)
Aynı üç görev (Türkçe uçtan uca kupon, Türkçe ödeme tasarımı, İngilizce kredi gereksinim incelemesi) skill'le ve skill'siz koşturuldu. Çıktılar sabit bir kontrol listesiyle puanlandı.

| | Skill'le | Skill'siz |
|---|---|---|
| Geçme oranı | %93 | %82 |
| Süre | ~451 sn | ~277 sn |
| Token | ~136 bin | ~83 bin |

Skill'ler kaliteyi artırıyor ama daha fazla zaman ve token harcıyor. 0.2.0'da token kullanımı 0.1.0'a göre %31 azaltıldı (197 binden 136 bine). Bu karşılaştırma ilk 5 skill'le yapıldı; 0.6.0'daki skill'ler için tekrarlanmadı. Özet tablolar: `evals/results/benchmark-0.1.0.md`, `benchmark-0.2.0.md`.

## 5. Vekil yönlendirme ölçümü
- **Yöntem:** Bir model yalnızca skill listesini (ad ve açıklama) görür ve her istek için bir skill seçer ya da "none" der. Bu Claude Code'un gerçek tetiklenme mekanizması **değildir**; ucuz bir vekil ölçümdür. Gerçek ölçüm için `tools/trigger_eval.py` var, ama giriş yapılmış bir `claude` CLI gerektiriyor ve biz koşturmadık.
- **Setler:**
  - 42 temel istek;
  - 20 zor istek;
  - 0.6.0 için 22 yeni istek. Bunların 5'i skill gerektirmeyen yakın istekler: Postman, SQL, Flutter, Faker, OpenAI API hatası.
- **Sonuç:** temel set 42/42, zor set 20/20, yeni set 22/22. Skill gerektirmeyen yakın isteklerin hepsinde "none" seçildi.
- **Anahtar değişikliği (şeffaflık için):** Zor setteki iki istek artık yeni ve daha özel skill'lere gidiyor: IDOR sorusu `testing-apis`'e, TCKN test verisi `preparing-test-data`'ya. Beklenen cevaplar bu skill'ler yokken yazılmıştı. Bu iki soruda yeni skill de kabul edilecek şekilde güncellendi. Eski anahtarla sonuç 18/20.
- Yeniden üretmek için: `python tools/routing_proxy.py build …` ve `score …`. Sonuçlar: `evals/results/routing-proxy-2026-09-30.json`

## 6. Birim ve regresyon testleri
- 150 test, standart kütüphane `unittest` ile yazıldı. Kapsamı: sınır değer, karar tablosu, durum geçişi, pairwise, RTM, export formatları (Xray, Zephyr, TestRail, Azure DevOps, Qase, xlsx), OpenAPI üretici, regresyon seçimi, SBTM, AI eval puanlaması, test verisi üretimi ve maskeleme, mobil kontrol listesi, veri mutabakatı.
- Kontrol toplamlı kimlik numaraları bağımsız referans uygulamalarla doğrulanıyor: 1000'er TCKN, VKN ve IBAN üretilip kontrol ediliyor.
- Veri taşıma deneme verisinde, doğru mapping ile tam olarak 9 hatanın bulunduğu (fazlasının değil) regresyon testiyle korunuyor.
- CI (GitHub Actions) her push'ta şunları koşar: senkronizasyon kontrolü, skill doğrulaması (Agent Skills spesifikasyonu) ve birim testleri.

## Ölçülmeyenler (dürüstçe)
- **Kör denemesi olmayan skill'ler:** keşif testi, yapay zekâ özellikleri, mobil ve test verisi. Bunlar yalnızca birim testleri ve script demolarıyla doğrulandı. Mobil kontrol listesi gerçek bir cihazda, AI eval puanlaması gerçek bir LLM ürününde denenmedi.
- **Test yönetim araçlarına içe aktarma:** Xray, Zephyr, TestRail, Azure DevOps ve Qase formatları resmi dokümantasyona göre hazırlandı; gerçek bir sunucuya aktarılmadı. Önce 2–3 testlik deneme importu yapın.
- **Yük testi:** k6 script'leri sözdizimi kontrolünden geçti, ama gerçek bir yük testi koşturulmadı.
- **Örneklem:** Her kör deneme tek koşu. Sonuçlar güçlü bir sinyal, ama istatistiksel bir kanıt değil.
- **Hafızadan yazılan referanslar:** Mevzuat ve standart atıfları (KVKK/GDPR maddeleri, MASVS, OWASP LLM Top 10, mağaza kuralları) ağ erişimi olmadan yazıldı. Her skill'in referansında "teyit edin" notu var.

## Denemeyi kendiniz tekrarlayın
```bash
node evals/trial-api/api/server.js      # http://127.0.0.1:4180, token-alice / token-bob
# Ajana yalnızca evals/trial-api/api/openapi.json dosyasını verin. server.js'i ve evals/keys/ klasörünü göstermeyin.
```
Veri taşıma denemesi için ajana yalnızca `evals/trial-migration/` altındaki iki CSV'yi ve `mapping-spec.md`'yi verin.

Kör denemeyi doğru kurmak (klasörü repo dışına kopyalamak, cevap anahtarını ajandan uzak tutmak) ve puanlamak için: [evals/README.md](../evals/README.md).

## 7. 0.7.0 kör denemeleri: skill'li ve skill'siz karşılaştırma (30 koşu)
- **Kurulum:** Bağımsız tasarlanmış 5 deneme × skill'li/skill'siz × 3 tekrar. Model Opus 5.5, maliyeti düşürmek için düşük çaba (low) ayarında. Her koşuyu, hangi koldan geldiğini bilmeyen ayrı bir değerlendirici cevap anahtarına göre puanladı. Ham veri: `evals/results/trials-0.7.0.json`.
- **Sonuçlar** (medyan puan %, parantezde koşu başına yanlış alarm):

| Deneme | Skill'li | Skill'siz | Yorum |
|---|---|---|---|
| Excel test seti incelemesi | **96** (0,0,0) | 92 (0,0,3) | Skill daha tutarlı; yanlış alarm yok |
| Yapay zekâ chatbot testi | **65** | 59 | Küçük artış; iki kol da zor bulgularda eksik |
| Keşif testi | 81 | **90** | **Skill bu denemede katkı sağlamadı, geride kaldı** |
| Mobil test planı incelemesi | 100 | 100 | Tavan etkisi; görev ayırt edici değil |
| Test verisi ve maskeleme | 96 | **100** | Skill'li kolda 2 küçük yanlış alarm |

- **Dürüst yorum:** Güçlü bir modelde bu 4 skill'in katkısı sınırlı; Excel incelemesinde ve AI testinde küçük bir fayda var, keşif testinde ise olumsuz etki görüldü. Skill'ler daha çok tutarlılık sağlıyor (daha düşük varyans), daha fazla hata bulmuyor. Bu yüzden keşif testi, mobil ve test verisi skill'leri **deneysel** etiketini koruyor.
- **Sınırlar:**
  - Koşu başına n=3. Düşük çaba ayarı kullanıldı. Sonnet ve Haiku ile koşulmadı.
  - Yarıda kesilen ilk çalıştırmadan kalan dosyalar bazı çalışma klasörlerinde kalmış olabilir (en az bir koşu önceki raporu yeniden kullandı).
  - Mobil ve test verisi denemeleri tavana dayandı; daha zor sürümleri gerekiyor.
- **Yönlendirme (0.7.0, açıklamalar kısaltıldıktan sonra):** 84/84; Opus ile 2 kez, Haiku ile 2 kez.
