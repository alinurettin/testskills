# Değerlendirme raporu: QA Suite — sürümlere göre sonuçlar

**[English →](EVALUATION.en.md)**

Bu belge sürümlere göre tarihsel sonuçları özetler. İlk denemeler 29–30 Eylül 2026'da yapıldı; 0.9.0'ın 126 koşusu 21 Ekim 2026 tarihlidir. Aşağıdaki eski sayılar ilgili sürümün kaydıdır. Sonraki kod düzeltmeleri yeni LLM deneyi anlamına gelmez. Tekrar üretilebilir yeni kayıt akışı: [EVALUATION-HARNESS.md](EVALUATION-HARNESS.md).

## Özet
| Değerlendirme | Ne ölçer | Sonuç |
|---|---|---|
| Kör uçtan uca deneme: FAST transfer (0.5.0) | Story → analiz → tasarım → Playwright → rapor zinciri | Yerleştirilen **5/5 hata** + 1 gerçek hata; yayın kararı doğru ("hazır değil") |
| Kör API denemesi (0.6.0) | `testing-apis`: OpenAPI → sözleşme ve yetkilendirme testleri | Yerleştirilen **5/5 hata** + 2 gerçek hata; 17 sözleşme sorusu; bağımsız yeniden koşum aynı sonucu verdi (31/11) |
| Kör veri taşıma denemesi (0.6.0) | `testing-data-migrations`: mutabakat, sınıflandırma, go/no-go | Yerleştirilen **9/9 hata**; tuzaklarda yanlış alarm yok; karar doğru (no-go) |
| Skill'li / skill'siz karşılaştırma (0.2.0) | 3 görev, sabit kontrol listesiyle puanlama | Geçme oranı %93'e karşı %82 (+11 puan) |
| Vekil yönlendirme ölçümü | Doğru skill'in adından ve açıklamasından seçilmesi | 17 skill, 84 istek: **84/84** (yeni skill'ler için 22/22) |
| Birim ve regresyon testleri | 30 script'in davranışı | **150 test**, CI'da her push'ta koşar |
| Dış kör deneme (0.11.2) | Antigravity + Gemini 4 Hydrogen, 3 deneme, 18 koşu; puanlayan GPT-6.1 Terra | Skill'li kol **önde değil**: %87,9'a karşı %93,3 (fark −5,3; p=0,09). Ayrıntı §10 |

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

Bu alt bölüm 0.6.0'ın tarihsel sınırlarını anlatır; sonraki kör denemeler §7–8'de yer alır. Yeni yerel sağlamlaştırma kontrolleri ve hâlâ ölçülmeyenler §9'dadır.
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

## 8. 0.9.0: 7 yeni bağımsız deneme, 3 model, 126 koşu
- **Kurulum:** Skill'leri hiç görmeyen tasarımcıların hazırladığı 7 deneme (API 3.1, iki tablolu veri taşıma, gereksinim analizi, test tasarımı, zor mobil, zor test verisi, keşif testi) × skill'li/skill'siz × Opus, Sonnet 5.5, Haiku × 3 koşu. Hepsi düşük çaba ayarında. Puanlayıcılar kör ve Sonnet 5.5 idi (§7'de Opus). Ham veri: `evals/results/trials-0.9.0.json`.
- **Medyan puan %, skill'li / skill'siz:**

| Deneme | Haiku | Sonnet 5.5 | Opus |
|---|---|---|---|
| Test tasarımı | **100 / 86** | 100 / 100 | 100 / 100 |
| API (OpenAPI 3.1) | **85 / 81** | 99 / 99 | 100 / 100 |
| Gereksinim analizi | **93 / 91** | **96 / 93** | 91 / 91 |
| Test verisi | 98 / 97 | 100 / 100 | 100 / 100 |
| Veri taşıma | 100 / 100 | 100 / 100 | 100 / 100 |
| Mobil plan incelemesi | 80 / 83 | 92 / 91 | 92 / 91 |
| Keşif testi | 65 / 74 | 79 / 74 | **90 / 74** |
| **Ortalama (tüm koşular)** | **89,3 / 85,4** | **94,9 / 92,6** | **95,2 / 93,3** |

- **İstatistik (0.10.0'da eklendi, `python tools/eval_stats.py evals/results/trials-0.9.0.json`):** Farkın %95 güven aralığı (deneme içinde yeniden örnekleme) ve permütasyon testi:

| | Koşu | Skill'li | Skill'siz | Fark | %95 güven aralığı | p |
|---|---:|---:|---:|---:|---|---:|
| Haiku | 42 | 89,3 | 85,4 | +3,8 | [−0,3, +8,4] | 0,17 |
| Sonnet 5.5 | 42 | 94,9 | 92,6 | +2,3 | [+0,4, +4,4] | 0,07 |
| Opus | 42 | 95,2 | 93,3 | +1,9 | [+0,1, +3,5] | 0,18 |
| **Üç model birlikte** | 126 | 93,1 | 90,5 | **+2,7** | [+1,0, +4,4] | **0,014** |

- **Doğru okuma:** Üç model birlikte alındığında skill'lerin küçük ama ayırt edilebilir bir katkısı var (+2,7 puan). Tek tek modellerde fark istatistiksel olarak ayırt edilemiyor; aralıklar birbirinin üzerine biniyor. Bu yüzden **"skill'ler en çok zayıf modele yarıyor" ifadesi bu veriyle kanıtlanmış değil**: Haiku'daki fark nokta tahmini olarak en büyük, ama aralığı sıfırı içeriyor. 0.9.0 sürüm notlarında ve README'de bu ifade fazla kesin yazılmıştı; düzeltildi. Hücre başına 3 koşuyla hesaplanan bootstrap aralıkları olduğundan dar çıkma eğilimindedir. Tek tek hücrelerde en net iki sonuç: Opus'ta keşif testi (+14,0 [+5,4, +22,6]) ve Haiku'da test tasarımı (+12,0 [+0,9, +24,1]).
- **Keşif testi düzeltmesi:** 0.7.0'da skill'li kol geride kalmıştı. Düzeltilmiş skill (kısa oturum modu, "veriyi takip et", saldırı listesi) Opus'ta 74'e karşı 90, Sonnet'te 74'e karşı 79 verdi. Haiku'da hâlâ geride (65'e 74): zayıf model uzun talimatı iyi kullanamıyor olabilir, bu açık kalan bir sorun.
- **Mobil planı incelemesi:** Fark yok; skill bu denemede katkı sağlamadı.
- **Sınırlar (önemli):**
  - Koşu başına n=3, düşük çaba ayarı. Farkların çoğu tek koşulardaki dalgalanma sınırında; istatistiksel kanıt değil, sinyal.
  - Puanlayıcı modeli §7'den farklı (eski Opus, bu tur Sonnet 5.5). Bu yüzden iki değerlendirmenin keşif puanları birbiriyle karşılaştırılamaz: aynı kol (Opus, skill'siz) §7'de 90, burada 74 aldı. Karşılaştırma yalnızca bu bölümün kendi içinde (aynı puanlayıcı, aynı anahtar) geçerli.
  - Denemeleri biz yazdırdık ve deneme verisi repoda herkese açık; aynı denemelerle yeniden ölçen biri, ajana anahtarı göstermediği sürece aynı koşulları kurabilir.
  - Yönlendirme ölçümü bu turda tekrarlanmadı (son: 84/84).

## 9. Yayımlanmamış yerel sağlamlaştırma

Yeni kod regresyonları tarihsel model puanlarını değiştirmez. Pairwise kapsam, şema/örnek doğruluğu, kanıt gizliliği, decimal/timezone/ref kısıtları ve Excel güncelleme yaşam döngüsü yerel fixture'larla test edilir. Tam güncel test sayısı için CI/teslim kaydına bakın; yukarıdaki 150 test 0.6.0 snapshot'ıdır. Gerçek vendor importu ve yeni ücretli/kör model koşumu yapılmış gibi sunulmaz.

0.9.0 ham verisinin yeniden hesaplanmış skill/skillsiz ortalamaları: Haiku **89,25/85,42**, Sonnet **94,93/92,61**, Opus **95,20/93,34**. 126 tekrar yalnız **7 farklı görev** içerir; 50 koşu tam puandır. Migration'ın 18 koşusu da 100'dür. Medyan tablosu tüm gerilemeleri göstermez: Opus API ortalaması skill ile 96,33, skillsiz 99,67'dir. Maliyet metadata'sı bu kayıtta yoktur. Tutarlılık ve maliyet üstünlüğü ayrı ölçülmelidir; genel ortalama tek başına bunları kanıtlamaz.

Yeni kayıtlar için [manifest/record/report akışı](EVALUATION-HARNESS.md) farklı model ayarı, grader ve commit gruplarını ayırır; bilinmeyen metadata'yı null tutar, kirlenmiş koşuları dışlar ve görev bazlı dağılım verir. Çalışma klasörünü kopyalamak ajan erişimini engellemez; izolasyonu runner/işletim sistemi sağlamalıdır.

## 10. 0.11.2: dış araçla kör deneme (Antigravity, 18 koşu)

0.10.0'dan beri hiçbir sürüm kör denemeyle ölçülmemişti. Bu tur, koşuları da puanlamayı da bizim dışımızdaki araçlara bıraktı.

- **Kurulum:** v0.11.2 (commit `330cc6a`). Üç deneme (test tasarımı, API 3.1, keşif testi) × skill'li/skill'siz × 3 koşu. Koşan: Google Antigravity 44.4.3, Gemini 4 Hydrogen (XHigh), 16–17 Kasım 2026. Puanlayan: Codex içinde GPT-6.1 Terra; yalnızca teslimleri ve anahtarları gördü, kol bilgisini görmedi. Ham veri: `evals/results/trials-external-antigravity-2026-11.json`. Teslimler, koşu notları ve puan dosyaları: [`eval/antigravity-2026-11` dalı](https://github.com/alinurettin/testskills/tree/eval/antigravity-2026-11/evals/results/external/antigravity).
- **Puanlar (koşu koşu):**

| Deneme (en yüksek puan) | Skill'li | Skill'siz | Ortalama %, skill'li / skill'siz |
|---|---|---|---|
| Test tasarımı (36) | 36, 35, 36 | 36, 36, 36 | 99,1 / 100,0 |
| API (100) | 84, 92, 76 | 87, 91, 100 | 84,0 / 92,7 |
| Keşif testi (31) | 25, 22, 28 | 25, 28, 28 | 80,6 / 87,1 |
| **Üç deneme birlikte** | | | **87,9 / 93,3** |

- **İstatistik (`python tools/eval_stats.py evals/results/trials-external-antigravity-2026-11.json`):** fark −5,3 puan, %95 güven aralığı [−10,1, −0,6], permütasyon p=0,09. Hücre başına 3 koşu var; bu bir kanıt değil, ama yön skill'lerin aleyhine.
- **Doğru okuma:**
  - **Skill'ler bu modelde ölçülebilir bir fayda sağlamadı.** Hiçbir denemede skill'li kol önde değil.
  - **API'de fark, bulma gücünden değil yanlış alarm cezasından geliyor.** Skill'li üç koşu ekili 10 hatanın hepsini tam buldu; skill'siz iki koşuda yarım puanlı maddeler var. Ceza sayılmadan puanlar skill'li 100, 100, 100 ve skill'siz 95, 91, 100 olurdu. Skill'li koşular sözleşmenin sustuğu davranışları (iptal edilmiş poliçeye hasar açılması, boş `holderName`, hata kontrollerinin sırası) kusur diye raporladı: 12 cezaya karşı 2. Anahtar "desteklenmeyen kusur" için −4 yazıyor ve puanlayıcı bunu katı ama tutarlı uyguladı. 0.9.0'da Opus'un API ortalaması da aynı yöndeydi (96,3'e karşı 99,7).
  - **Test tasarımı tavanda.** 6 koşunun 5'i tam puan; bu deneme bu sınıf modelleri ayırt etmiyor.
  - **Keşif testinde 6 koşunun hiçbiri K2'yi bulamadı.** Skill'li kol ayrıca K3 ve K6'yı daha çok kaçırdı (K6: 2'ye karşı 1, K3: 1'e karşı 0).
- **Bundan çıkan düzeltmeler (0.11.3):** `testing-apis` artık kusur ile açık soruyu ayırıyor. `design_grader.py`, küçük harfle yazılmış `aktor` değeri için katı okumayı da kabul ediyor: betik v0.11.2 hâliyle skill'siz iki koşuya (R03, R14) haksız 1 puan ceza kesmişti; puanlayıcı bunu elle düzeltti, yukarıdaki puanlar düzeltilmiş hâlidir. Bu düzeltmelerin etkisi henüz ölçülmedi.
- **Sınırlar (önemli):**
  - Tek model, hücre başına 3 koşu, tek puanlayıcı. Keşif puanlarını ikinci bir puanlayıcı doğrulamadı. Biz yalnızca tasarım puanlarını betikle, API'de bulgu eşleşmelerini ve üç ceza kararını elle denetledik.
  - Kollar karışık sırada koşmadı: skill'li koşular 16 Kasım 18:11–23:25, tutulan skill'siz koşular 17 Kasım 00:21–00:48.
  - Skill'siz kol bir kez yeniden koştu. İlk denemede üç koşunun sunucusu yarıda kapanmıştı ve istem değişti ("Use your own expertise and general tools." cümlesi eklendi). İlk denemenin çıktıları silindi; iki deneme karşılaştırılamıyor. Yeniden koşma skill'siz kolun lehine bir düzeltmedir.
  - Yalıtım yalnızca talimatla sağlandı: alt-ajanlar teknik olarak anahtar klasörüne erişebiliyordu ve internet açıktı. "Dışarı çıkan olmadı" denetimini aracın kendisi yaptı. Puanlayıcı hiçbir koşuda anahtar izi bildirmedi.
  - Körlük tam değil: skill'li teslimlerden en az biri `skills/...` yolunu anıyor.
  - API sunucusu bazı girdilerde çöküyor ve koşu sırasında yeniden başlatıldı (iki kolda da, 3–7 kez); bellekteki durum her seferinde sıfırlandı.
  - Harness kullanılmadı (giriş özetleri yok) ve modelin tam API kimliği bilinmiyor. Teslimlerdeki yerel klasör yolu yayından önce `C:\eval` ile değiştirildi; başka hiçbir şeye dokunulmadı.
  - İkinci araçla (Codex) koşu yapılmadı: iki deneme tavanda olduğu için aynı denemeleri tekrarlamak yerine önce denemelerin zorlaştırılması gerekiyor.
