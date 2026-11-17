# Perdeaçık Bilet (v0.9 demo) — Keşif Testi Raporu

**Test edilen uygulama:** `http://127.0.0.1:4110`  
**Referans doküman:** `urun-notu.md` (v0.9 demo)  
**Ortam:** Windows 11 · Microsoft Edge (Playwright Chromium v1.65.1) · Doğrudan HTTP/API (`urllib` / Playwright `APIRequestContext`) · Masaüstü (`1280×800`) ve Mobil (`375×812`, `320×568`)  
**Tarih:** 2026-11-16 (oturum aralığı: `23:12`–`23:24`, UTC+3)  
**Test verileri:** Yalnızca kurgusal/sentetik test verileri (`ayse.yilmaz@example.com`, `mehmet.demir@example.com`, `api.probe2@example.com`, `val.probe@example.com`, `yirmidort@example.com`, `kupon.ux@example.com`, `yuvarlama@example.com`, `kurban@example.com`, `0555 000 00 XX`).

---

## 1. Oturum Notları

### Test Başlatma Belgeleri (Charters) ve Turlar
Keşif testi planlı oturum yönetimi (SBTM) yaklaşımıyla risk sırasına göre 5 charter altında yürütüldü. Önce veri değiştiren tüm aksiyonlarda temel P1 yoklamaları (görünümler arası tutarlılık, sınırlar, tekrar gönderim, başka kullanıcı/yetki), ardından P2 yoklamaları (paralel yarış, Geri/yenileme, Türkçe `İ/ı`, kesim saatleri, hata sızıntısı, klavye ve mobil) uygulandı:

1. **CH-01 — Para, İndirim, Kupon ve Adet Sınırları (Kritik Risk)**  
   *Test başlatma belgesi:* Bilet türü (`Tam` / `Öğrenci` %20), hizmet bedeli (`12,50 TL`), `PERDE50` kampanya eşiği (`300,00 TL`) ve bilet adedi (`1–6`) kurallarını hem arayüzde hem API üzerinde sınır değerler ve ondalıklı fiyatlarla (`164,99 TL`, `149,90 TL`, `137,50 TL`) kurcalayarak hesaplama, yuvarlama ve sınır aşımı hatalarını bulmak.  
   *Turlar/Fikirler:* Sınır Değer Analizi (`0`, `-1`, `1`, `6`, `7`, `1.5`, boş `""`), Veriyi Takip Et (Detay → Ödeme → API → Onay → Biletlerim), Yuvarlama ve yarım kuruş yoklamaları.
2. **CH-02 — Sipariş Oluşturma, Tekrar Gönderim ve Yarış Durumu (Kritik Risk)**  
   *Test başlatma belgesi:* Sipariş oluşturma akışını çift tıklama, paralel API istekleri (`Promise.all`), sayfa yenileme, tarayıcı Geri düğmesi ve tükenen (`106`) / son 3 koltuk kalan (`105`) etkinliklerle test ederek mükerrer kayıt, stok aşımı (overselling) ve durum bozulmalarını bulmak.
3. **CH-03 — Biletlerim, İptal, 24 Saat Kuralı ve Yetkilendirme / IDOR (Yüksek Risk)**  
   *Test başlatma belgesi:* Sipariş sorgulama ve iptal akışlarını e-posta eşleştirme, 24 saatten az kalan etkinlikler (`101`, `102`), ikinci sekmeden bayat iptal, paralel iptal yarışı ve başka kullanıcının PNR koduyla erişim/iptal (BOLA/IDOR) saldırılarıyla test etmek.
4. **CH-04 — Arama, Filtreleme, Sıralama ve Türkçe Yerelleştirme (Orta Risk)**  
   *Test başlatma belgesi:* Ana sayfa keşif araçlarını Türkçe `İ/ı/ş/ğ/ç/ö/ü` büyük-küçük harf dönüşümleri, boşluklu aramalar, filtre birleşimleri, sıralama modları ve HTML/XSS benzeri girdilerle test etmek.
5. **CH-05 — Erişilebilirlik (WCAG 2.1 AA), Klavye ve Mobil Görünüm (Yüksek/Orta Risk)**  
   *Test başlatma belgesi:* Ana kullanıcı akışını yalnızca klavye (`Tab`, `Enter`, `Esc`), ARIA/etiket/odak/kontrast kontrolleri ve `375 px` / `320 px` mobil genişliklerde test etmek.

### Veri Haritası (Recon sırasında çıkarıldı)
- **Etkinlikler:** `#/` (`GET /api/etkinlikler`), `#/etkinlik/{id}` (`GET /api/etkinlikler/{id}`), `#/odeme` özet kutusu.
- **Siparişler:** `POST /api/siparisler`, `#/onay/{pnr}` (`GET /api/siparisler/{pnr}`), `#/biletlerim` (`GET /api/siparisler?eposta={eposta}`), İptal (`POST /api/siparisler/{pnr}/iptal`).

### Zaman Damgalı Oturum Günlüğü
- `23:12` **NOT:** Görev tanımı (`TASK.md`) ve ürün notu (`urun-notu.md`) incelendi; test ortamının `http://127.0.0.1:4110` adresinde ayakta olduğu doğrulandı.
- `23:14` **KAPSAM (Recon):** Ana sayfa (`#/`) gezildi; `GET /api/etkinlikler` üzerinden 9 etkinlik (`101`–`109`, biri `Tükendi` (`106`), birinde son 3 koltuk (`105`), ikisi yarın (`101` saat `10:00`, `102` saat `22:00`)) görüntülendi. Kanıt: `kanitlar/01-anasayfa.png`.
- `23:15` **KAPSAM (Mutlu Yol):** `108` no'lu etkinlikten `2 × Öğrenci` siparişi (`URN5EZ`, `121,00 TL`) oluşturuldu, onay ekranı ve `#/biletlerim` kontrol edildi, ardından iptal edilerek koltuk sayısının `90`'a döndüğü doğrulandı (`kanitlar/05-onay.png`, `kanitlar/06-biletlerim-dolu.png`, `kanitlar/07-biletlerim-iptal.png`).
- `23:15` **HATA [CH-01]:** Onay ekranında `121,00 TL` görünen tutar `#/biletlerim` tablosunda `121 TL` (ondalıksız) göründü (`HATA-09`).
- `23:16` **KAPSAM [CH-01]:** `PERDE50` kodu tam `300,00 TL` sınırında (`107`, `2 × Tam = 275 + 25 = 300,00 TL` → `250,00 TL`), `290,00 TL` altında (reddedildi), küçük harf (`perde50`) ve boşluklu (` PERDE50 `) biçimlerde test edildi (`kanitlar/08-kupon-300-sinir.png`).
- `23:16` **HATA [CH-01]:** `164,99 TL` fiyatlı `104` etkinliğinde `2 × Öğrenci` siparişi (`59CK5T`) API'den `toplam: 288.98400000000004` döndü (`HATA-05`).
- `23:17` **HATA [CH-01]:** `POST /api/siparisler` uç noktası `adet: 0` (`CR3T24`), `adet: -1` (`86C8BH`, `toplam: -132.5`), `adet: 7` (`RN3BGD`, `toplam: 927.5`) ve `adet: 1.5` (`2P3M43`, sessizce `1`'e yuvarlandı) isteklerini `201 Created` ile kabul etti (`HATA-01`, `HATA-02`).
- `23:18` **HATA [CH-01]:** Tükenen `106` (`kalan: 0`) etkinliğine `adet: -2` (`49ZCZ8`) kabul edilip `kalan` `2`'ye yükseldi; `108` (`kapasite: 90, kalan: 90`) etkinliğine `adet: -5` (`KD8FFB`) kabul edilip `kalan` `95`'e (kapasite üstüne) çıktı (`HATA-01`).
- `23:18` **HATA [CH-01]:** Arayüzde `#adet` alanına `0`, `-1`, `""` girilip `Devam et` tıklandığında engelleme olmadan `#/odeme` ekranına geçildi (`-197,50 TL`, `NaN TL`) (`kanitlar/10-ui-adet-neg1.png`, `kanitlar/10-ui-adet-0.png`, `kanitlar/12-nan-odeme.png`). Ayrıca `5 × Tam + PERDE50` siparişi (`T86USA`) Biletlerim tablosunda `1387,5 TL`, `59CK5T` ise `288,98400000000004 TL` olarak göründü (`kanitlar/09-tutar-bicim-tutarsizligi.png`).
- `23:19` **KAPSAM [CH-03]:** İkinci sekmede bayat `59CK5T` iptal denemesi (`409` / `"Bu sipariş zaten iptal edilmiş."`) ve paralel çift iptal yarışı (`PHHPSJ`: `[200, 409]`, koltuk tek kez iade edildi) başarıyla engellendi.
- `23:19` **HATA [CH-01]:** `#adet` boşken (`NaN TL`) ödeme formu gönderildiğinde sunucu `201 Created` ile `adet: 0, toplam: 0` siparişi (`G5SHPD`) oluşturdu (`HATA-01`).
- `23:19` **HATA [CH-04]:** Arama kutusunda `"istanbul"`, `"izmir"` ve `"İZMİR"` aramaları `0` sonuç döndü (`kanitlar/17-turkce-arama-istanbul.png`, `HATA-07`). Şehir filtresi toplamı (`2+1+1+3+2 = 9`) ve `Ada göre (A–Z)` Türkçe sıralama doğrulandı (`kanitlar/13-siralama-turkce.png`).
- `23:20` **HATA [CH-05]:** `#/etkinlik/108` sayfasında `Tab` gezintisinde `.chip` bilet türü düğmelerinin tamamen atlandığı doğrulandı (`HATA-06`).
- `23:21` **HATA [CH-03]:** Başka kullanıcının PNR'ı (`MDZ7MJ`) ile `GET /api/siparisler/MDZ7MJ` tam kişisel veri döndürdü ve `POST /api/siparisler/MDZ7MJ/iptal` siparişi iptal etti (`HATA-04`).
- `23:21` **HATA [CH-02]:** `#/odeme` yenilendiğinde ve `#/onay/{pnr}`'den Geri gelindiğinde sayfa `undefined` / `NaN TL` gösterdi (`kanitlar/16-odeme-yenileme.png`, `HATA-08`). Çift tıklama (`dblclick` -> 1 istek) ve Event `105` (`kalan: 3`) paralel `2+2` yarışında (`8REPVM` -> `201` + `409`, `kalan: 1`) stok aşımı olmadı.
- `23:21` **HATA [CH-03]:** Yarınki etkinlikler (`101` ~10,6 saat sonra, `102` ~22,6 saat sonra) için oluşturulan `JAG9FL` ve `ZE2BKS` siparişleri hem UI hem API'den iptal edilebildi (`HATA-03`, `kanitlar/18-biletlerim-24h-onceli.png`, `kanitlar/19-24saat-alti-iptal-edildi.png`).
- `23:22` **HATA [CH-05]:** `320 px` mobil genişlikte `#/odeme` sayfasında yatay taşma (`scrollWidth: 352`) saptandı (`kanitlar/20-mobil-320-odeme.png`, `HATA-10`). `aria-invalid`/`aria-describedby` eksikliği ve `adSoyad` 60 karakter sınırı hata mesajı yanlışı (`HATA-11`) bulundu.
- `23:23` **HATA [CH-01/CH-03]:** `AJSKLC` (`104 × 3 Öğrenci + PERDE50`) için 3 farklı tutar (`383,47` / `383,48` / `383,47600000000006 TL`) ve `#/biletlerim`'de geçersiz e-posta (`"gecersiz"`) uyarısızlığı (`HATA-12`, `kanitlar/22-biletlerim-gecersiz-eposta.png`) doğrulandı. Tüm test siparişleri temizlenip etkinlik stoklarının başlangıç haline döndüğü teyit edildi.

---

## 2. Hata Listesi

### HATA-01 — Negatif, sıfır veya boş bilet adedi hem arayüzde hem API'de kabul ediliyor ve koltuk stokunu yapay artırıyor
- **Önem Derecesi:** Kritik (`Güven: Doğrulandı`)
- **Tekrar Üretme Adımları:**
  1. Tarayıcıda `http://127.0.0.1:4110/#/etkinlik/105` sayfasını açın (`Kalan: 3 koltuk`).
  2. "Bilet adedi" (`#adet`) alanına `-1` (veya `0` ya da alanı tamamen boş `""`) yazıp `Devam et` düğmesine tıklayın.
  3. Ödeme ekranında geçerli kurgusal iletişim bilgilerini girip `Siparişi tamamla`'ya tıklayın.
  4. Doğrudan API doğrulaması için:
     - `POST /api/siparisler` → `{"etkinlikId":109,"tur":"tam","adet":-1,"kampanyaKodu":"","adSoyad":"Api Test","eposta":"api.probe2@example.com","telefon":"0555 000 00 99","kvkk":true}`
     - Tükenen etkinlik (`id: 106`, `kapasite: 100`, `kalan: 0`) için `adet: -2` gönderip ardından `GET /api/etkinlikler/106` çağrısı yapın.
     - Tam kapasiteli etkinlik (`id: 108`, `kapasite: 90`, `kalan: 90`) için `adet: -5` gönderip ardından `GET /api/etkinlikler/108` çağrısı yapın.
- **Beklenen Sonuç (`urun-notu.md`):** *"Bir siparişte en az 1, en fazla 6 bilet olabilir."* ve *"Tükenen etkinlik için bilet alınamaz."* Arayüz ve API `adet < 1`, `NaN`/`null` veya boş değerleri reddetmeli (`400 Bad Request`).
- **Gerçekleşen Sonuç:**
  - Arayüz `adet="-1"`, `adet="0"` ve `adet=""` değerlerinde `#/odeme` sayfasına geçişe izin veriyor ve sırasıyla `-197,50 TL`, `0,00 TL` ve `NaN TL` toplam gösteriyor. `adet=""` gönderildiğinde sunucu `201 Created` (`pnr: "G5SHPD"`, `adet: 0`, `toplam: 0`) döndürüyor.
  - API `adet: 0` için `201 Created` (`pnr: "CR3T24"`, `toplam: 0`), `adet: -1` için `201 Created` (`pnr: "86C8BH"`, `toplam: -132.5`) döndürdü.
  - Tükenen etkinlik `106`'ya `adet: -2` gönderildiğinde `201 Created` (`pnr: "49ZCZ8"`, `toplam: -216`) oluştu ve `GET /api/etkinlikler/106` yanıtında `kalan` değeri `0`'dan `2`'ye yükseldi.
  - Etkinlik `108`'e `adet: -5` gönderildiğinde `201 Created` (`pnr: "KD8FFB"`, `toplam: -362.5`) oluştu ve `kalan` değeri `95` oldu (salon kapasitesi `90`'ı aştı).
- **Kanıt:** `kanitlar/10-ui-adet-neg1.png`, `kanitlar/10-ui-adet-0.png`, `kanitlar/12-nan-odeme.png`; API çıktıları: `86C8BH`, `CR3T24`, `G5SHPD`, `49ZCZ8`, `KD8FFB`.

---

### HATA-02 — API üzerinden en fazla 6 bilet sınırı ve tam sayı kuralı uygulanmıyor (`adet: 7` ve `1.5` kabul ediliyor)
- **Önem Derecesi:** Kritik (`Güven: Doğrulandı`)
- **Tekrar Üretme Adımları:**
  1. `POST http://127.0.0.1:4110/api/siparisler` uç noktasına `{"etkinlikId":109,"tur":"tam","adet":7,"kampanyaKodu":"","adSoyad":"Api Test","eposta":"api.probe2@example.com","telefon":"0555 000 00 99","kvkk":true}` gönderin.
  2. Aynı isteği `adet: 1.5` ile gönderin (ayrıca arayüzde `#/etkinlik/105` üzerinde `#adet` alanına `1.5` yazıp `Devam et`'e tıklayın).
- **Beklenen Sonuç (`urun-notu.md`):** *"Bir siparişte en az 1, en fazla 6 bilet olabilir."* Sunucu `adet: 7` ve tam sayı olmayan `adet: 1.5` için `400` hata dönmeli.
- **Gerçekleşen Sonuç:**
  - `adet: 7` için HTTP `201 Created` döndü (`pnr: "RN3BGD"`, `adet: 7`, `toplam: 927.5`).
  - `adet: 1.5` hem arayüzde hem API'de hata verilmeden `1` bilet olarak işlendi (API `201 Created`, `pnr: "2P3M43"`, `adet: 1`, `toplam: 132.5`).
- **Kanıt:** `POST /api/siparisler` HTTP `201` yanıtları (`RN3BGD`, `2P3M43`).

---

### HATA-03 — Etkinliğe 24 saatten az süre kalmış siparişler iptal edilebiliyor
- **Önem Derecesi:** Kritik (`Güven: Doğrulandı`)
- **Tekrar Üretme Adımları:**
  1. Sistem saati `2026-11-16 23:21` (UTC+3 / `2026-11-16T20:21:50Z`) iken:
     - `101` no'lu etkinlik (`Boğaziçi Caz Gecesi`, `2026-11-17T07:00:00.000Z` / yerel `10:00` — yaklaşık **10 saat 38 dakika** sonra) ve
     - `102` no'lu etkinlik (`İstanbul Gençlik Senfonisi: Mevsimler`, `2026-11-17T19:00:00.000Z` / yerel `22:00` — yaklaşık **22 saat 38 dakika** sonra) için birer sipariş oluşturun (`JAG9FL`, `ZE2BKS`).
  2. `#/biletlerim` sayfasında `yirmidort@example.com` ile siparişleri listeleyin.
  3. `JAG9FL` satırında `İptal et` → `Evet, iptal et` adımlarını izleyin; `ZE2BKS` için `POST /api/siparisler/ZE2BKS/iptal` isteğini gönderin.
- **Beklenen Sonuç (`urun-notu.md`):** *"Etkinliğe 24 saatten fazla varsa siparişini iptal edebilmeli"* — Her iki etkinlik de 24 saatten az süre kaldığı için arayüzde iptal seçeneği engellenmeli ve API isteği reddetmelidir (`400`/`409`).
- **Gerçekleşen Sonuç:** Arayüzde her iki siparişte de `İptal et` düğmesi aktif olarak sunuldu. `JAG9FL` (10,6 saat kala) arayüz üzerinden `200 OK` ile iptal edildi (`"JAG9FL kodlu siparişiniz iptal edildi. Koltuklar yeniden satışa açıldı."`), `ZE2BKS` (22,6 saat kala) ise API üzerinden `200 OK` ile iptal edildi (`durum: "iptal"`).
- **Kanıt:** `kanitlar/18-biletlerim-24h-onceli.png`, `kanitlar/19-24saat-alti-iptal-edildi.png`; `POST /api/siparisler/JAG9FL/iptal` ve `ZE2BKS/iptal` `200 OK` yanıtları.

---

### HATA-04 — Yalnızca 6 haneli PNR kodu ile başka kullanıcının kişisel verileri okunabiliyor ve siparişi iptal edilebiliyor (IDOR / BOLA)
- **Önem Derecesi:** Yüksek (`Güven: Doğrulandı`)
- **Tekrar Üretme Adımları:**
  1. Kullanıcı A (`kurban@example.com`, `"Kurban Kullanici"`, `"0555 111 22 33"`) adına bir sipariş oluşturun (`pnr: "MDZ7MJ"`).
  2. E-posta veya herhangi bir kimlik doğrulama bilgisi göndermeden başka bir istemciden `GET http://127.0.0.1:4110/api/siparisler/MDZ7MJ` isteğini atın.
  3. Ardından `POST http://127.0.0.1:4110/api/siparisler/MDZ7MJ/iptal` isteğini atın.
- **Beklenen Sonuç (Güvenlik / OWASP API1:2023 BOLA):** Üçüncü bir kişi yalnızca 6 karakterlik tahmin edilebilir/denenebilir PNR ile başka bir müşterinin tam adı, e-posta adresi ve telefon numarasını okuyamamalı; e-posta veya doğrulama olmaksızın siparişini iptal edememelidir.
- **Gerçekleşen Sonuç:** `GET /api/siparisler/MDZ7MJ` HTTP `200 OK` ile `adSoyad`, `eposta`, `telefon` bilgilerini eksiksiz döndürdü; `POST /api/siparisler/MDZ7MJ/iptal` ise HTTP `200 OK` ile siparişi iptal etti (`durum: "iptal"`).
- **Kanıt:** `GET /api/siparisler/MDZ7MJ` (`200 OK`) ve `POST /api/siparisler/MDZ7MJ/iptal` (`200 OK`) yanıtları.

---

### HATA-05 — Öğrenci bileti indiriminde yuvarlama ve kayan nokta hatası nedeniyle aynı sipariş için üç farklı toplam gösteriliyor
- **Önem Derecesi:** Yüksek (`Güven: Doğrulandı`)
- **Tekrar Üretme Adımları:**
  1. Birim fiyatı `164,99 TL` olan `İzmir Kordon Akustik` (`#/etkinlik/104`) sayfasını açın.
  2. Bilet türünü `Öğrenci` (`131,99 TL (%20 indirimli)` olarak gösterilir), adedi `3` seçin ve `Devam et`'e tıklayın.
  3. `#/odeme` ekranında `PERDE50` kampanya kodunu uygulayın, formu doldurup siparişi tamamlayın (`pnr: "AJSKLC"`).
  4. `#/onay/AJSKLC` ekranındaki toplamı, `#/biletlerim` (`yuvarlama@example.com`) tablosundaki tutarı ve `GET /api/siparisler/AJSKLC` yanıtını karşılaştırın. (Benzer şekilde `2 × Öğrenci` siparişi `59CK5T`'yi `#/biletlerim`'de kontrol edin.)
- **Beklenen Sonuç (`urun-notu.md` + Tutarlılık):** Hesaplama ve yuvarlama tüm katmanlarda özdeş olmalı; kuruş farkı veya ham IEEE-754 kayan nokta sayısı (`...00000006`) oluşmamalı.
- **Gerçekleşen Sonuç:** Aynı `AJSKLC` siparişi için 3 farklı değer görüldü:
  - Detay ve Ödeme ekranı: **`383,47 TL`** (`3 × 131,99 + 37,50 - 50,00`)
  - Onay ekranı (`#/onay/AJSKLC`): **`383,48 TL`**
  - Biletlerim tablosu ve API (`toplam`): **`383,47600000000006 TL`**
  - Aynı şekilde `59CK5T` (`2 × Öğrenci`) için Ödeme ekranı `288,98 TL`, Biletlerim tablosu `288,98400000000004 TL` göstermektedir.
- **Kanıt:** `kanitlar/09-tutar-bicim-tutarsizligi.png`; `GET /api/siparisler/AJSKLC` (`"toplam":383.47600000000006`).

---

### HATA-06 — Etkinlik detayında "Bilet türü" (`Tam` / `Öğrenci`) klavye ile seçilemiyor (WCAG 2.1.1)
- **Önem Derecesi:** Yüksek (`Güven: Doğrulandı`)
- **Tekrar Üretme Adımları:**
  1. `http://127.0.0.1:4110/#/etkinlik/108` sayfasını açın.
  2. Fare kullanmadan yalnızca `Tab`, `Shift+Tab`, ok tuşları, `Enter` ve `Space` ile ilerleyin.
- **Beklenen Sonuç (`urun-notu.md` WCAG 2.1 AA / WCAG 2.1.1 Keyboard):** Tüm etkileşimli kontroller klavye ile odaklanabilir ve seçilebilir olmalı; kullanıcı klavyeyle `Öğrenci` (%20 indirimli) biletini seçebilmelidir.
- **Gerçekleşen Sonuç:** `Tam` ve `Öğrenci` seçenekleri `<div class="chip" data-tur="...">` olarak kodlandığından odak sırasına girmiyor. `Tab` sırası `← Tüm etkinlikler` bağlantısından doğrudan `#adet` kutusuna atlıyor; klavye kullanıcısı öğrenci bileti alamıyor.
- **Kanıt:** `#/etkinlik/108` DOM yapısı ve Playwright `Tab` odak izleme çıktısı (`INPUT #adet` öncesi hiçbir `.chip` odak almıyor).

---

### HATA-07 — Arama kutusunda Türkçe `İ/ı` dönüşümü bozuk (`"istanbul"`, `"izmir"` ve `"İZMİR"` sonuç bulamıyor)
- **Önem Derecesi:** Yüksek (`Güven: Doğrulandı`)
- **Tekrar Üretme Adımları:**
  1. Ana sayfada (`#/`) `#ara` arama kutusuna sırayla `istanbul`, `ISTANBUL`, `izmir`, `İZMİR` ve `IZMIR` yazın.
- **Beklenen Sonuç (`urun-notu.md`):** *"Arayüz Türkçe; Türkçe içerik sorunsuz desteklenmeli."* İstanbul'daki 3 ve İzmir'deki 2 etkinlik harf büyüklüğünden bağımsız bulunabilmeli.
- **Gerçekleşen Sonuç:** Bu 5 sorgunun tamamında `"Aramanızla eşleşen etkinlik bulunamadı."` sonucu döndü (yalnızca `"İSTANBUL"` araması 3 etkinlik getirdi; `"İZMİR"` bile `"İzmir"` sonucunu getirmedi).
- **Not (şüphe):** Muhtemelen Türkçe yerel ayar (`tr-TR`) olmadan standart `.toUpperCase()` / `.toLowerCase()` çağrılıyor.
- **Kanıt:** `kanitlar/17-turkce-arama-istanbul.png`.

---

### HATA-08 — Ödeme sayfası (`#/odeme`) yenilendiğinde veya onay sayfasından Geri gelindiğinde `undefined` / `NaN TL` ekranı açılıyor
- **Önem Derecesi:** Yüksek (`Güven: Doğrulandı`)
- **Tekrar Üretme Adımları:**
  1. Herhangi bir etkinlikte `Devam et` ile `#/odeme` sayfasına geçip tarayıcıyı yenileyin (`F5`), **veya** siparişi tamamlayıp `#/onay/{pnr}` sayfasına geldikten sonra tarayıcının "Geri" düğmesine basın.
- **Beklenen Sonuç (Dayanıklılık / Durum yönetimi):** Seçili sipariş durumu korunmalı ya da kullanıcı anlamlı bir bildirimle etkinlik listesine/detayına yönlendirilmeli; bozuk `undefined` / `NaN TL` özet ekranı gösterilmemeli.
- **Gerçekleşen Sonuç:** Özet kutusunda etkinlik adı `undefined`, bilet satırı `undefined × Tam bilet (NaN TL)`, hizmet bedeli `Hizmet bedeli (undefined × 12,50 TL)` ve toplam `NaN TL` görüntüleniyor.
- **Kanıt:** `kanitlar/16-odeme-yenileme.png`.

---

### HATA-09 — "Biletlerim" tablosunda tutarlar iki ondalık basamaklı ve Türkçe binlik ayraçlı gösterilmiyor
- **Önem Derecesi:** Orta (`Güven: Doğrulandı`)
- **Tekrar Üretme Adımları:**
  1. Tam tutarlı (`121,00 TL`, `URN5EZ`) ve binlik ayraçlı (`1.387,50 TL`, `T86USA`) siparişler oluşturup `#/biletlerim` sayfasında sorgulayın.
- **Beklenen Sonuç (`urun-notu.md`):** *"Tutarlar TL cinsinden, iki ondalık basamakla ve Türkçe biçimde gösterilmeli (ör. 1.234,50 TL)."*
- **Gerçekleşen Sonuç:** Biletlerim tablosunda `121,00 TL` yerine `121 TL`, `1.387,50 TL` yerine `1387,5 TL` görünüyor.
- **Kanıt:** `kanitlar/06-biletlerim-dolu.png`, `kanitlar/09-tutar-bicim-tutarsizligi.png`.

---

### HATA-10 — 320 px mobil genişlikte ödeme sayfasında (`#/odeme`) yatay taşma oluşuyor (WCAG 1.4.10)
- **Önem Derecesi:** Orta (`Güven: Doğrulandı`)
- **Tekrar Üretme Adımları:**
  1. Tarayıcı görünüm alanını `320×568` boyutuna ayarlayın.
  2. `#/etkinlik/108` → `Devam et` ile `#/odeme` sayfasını açın.
- **Beklenen Sonuç (`urun-notu.md` WCAG 2.1 AA / WCAG 1.4.10 Reflow):** 320 px genişlikte yatay kaydırma veya içerik taşması olmamalı (`scrollWidth === 320`).
- **Gerçekleşen Sonuç:** Sayfa genişliği `scrollWidth: 352 px` olarak `320 px`'i aşıyor; kartlar üst kırmızı başlıktan sağa doğru taşıyor.
- **Kanıt:** `kanitlar/20-mobil-320-odeme.png`.

---

### HATA-11 — Ödeme formunda alan bazlı ARIA hata bağlamı eksik ve 60 karakter üstü ad-soyad için yanıltıcı hata mesajı veriliyor
- **Önem Derecesi:** Orta (`Güven: Doğrulandı`)
- **Tekrar Üretme Adımları:**
  1. `#/odeme` formunu boş gönderip `#adSoyad`, `#eposta`, `#telefon` alanlarındaki `aria-invalid` ve `aria-describedby` özniteliklerini inceleyin.
  2. `Ad Soyad` alanına 65 adet `"A"` harfi yazarak formu veya `POST /api/siparisler` isteğini gönderin (`60` karakter `201 Created` alıyor, `65` karakter `400` alıyor).
- **Beklenen Sonuç (WCAG 3.3.1 / 3.3.3 & Kullanılabilirlik):** Hatalı giriş alanları programatik olarak işaretlenmeli (`aria-invalid="true"`, `aria-describedby`); uzunluk sınırı aşıldığında karakter sınırını belirten bir hata mesajı gösterilmeli.
- **Gerçekleşen Sonuç:** Alanlarda `aria-invalid` ve `aria-describedby` bulunmuyor (`null`). 65 harflik ad-soyad için ise `"Ad soyad en az 3 harften oluşmalı ve yalnızca harf içermelidir."` şeklinde hatalı neden bildiren mesaj dönüyor.
- **Kanıt:** Playwright DOM/ARIA denetimi ve `POST /api/siparisler` (`LEN_60: 201`, `LEN_65: 400`).

---

### HATA-12 — "Biletlerim" sayfasında geçersiz e-posta biçimi girildiğinde doğrulama uyarısı yerine "sipariş bulunamadı" mesajı gösteriliyor
- **Önem Derecesi:** Orta (`Güven: Doğrulandı`)
- **Tekrar Üretme Adımları:**
  1. `#/biletlerim` sayfasında `#sorguEposta` alanına `"gecersiz"` yazıp `Siparişleri göster`'e tıklayın.
- **Beklenen Sonuç:** Ödeme formundaki e-posta kuralıyla tutarlı olarak `"Geçerli bir e-posta adresi girin."` uyarısı verilmeli.
- **Gerçekleşen Sonuç:** Biçim doğrulaması yapılmadan sunucuya istek atılıyor ve `"Bu e-posta adresiyle verilmiş sipariş bulunamadı."` mesajı gösteriliyor.
- **Kanıt:** `kanitlar/22-biletlerim-gecersiz-eposta.png`.

---

### HATA-13 — Erişilebilirlik iyileştirme eksikleri: Skip link yok, başlık çubuğundaki odak göstergesi düşük kontrastlı, "Tükendi" düğmesi kontrastı zayıf
- **Önem Derecesi:** Düşük (`Güven: Doğrulandı`)
- **Tekrar Üretme Adımları:**
  1. Ana sayfada `Tab` ile `#icerik` ana alanına atlama bağlantısı olup olmadığını kontrol edin ve koyu kırmızı üst menüdeki (`Etkinlikler`, `Biletlerim`) odak halkasını inceleyin.
  2. `#/etkinlik/106` sayfasında devre dışı `Tükendi` düğmesinin hesaplanan stillerini inceleyin.
- **Beklenen Sonuç (`urun-notu.md` WCAG 2.1 AA):** Ana içeriğe atlama bağlantısı (WCAG 2.4.1) ve koyu zemin üzerinde belirgin odak göstergesi (WCAG 2.4.7 / 1.4.11) bulunmalı; devre dışı düğme metni okunabilir kalmalıdır.
- **Gerçekleşen Sonuç:** `<a href="#icerik">` skip link yok (`0`). Üst menüde yalnızca tarayıcı varsayılanı `1px` koyu çizgi (`rgb(16, 16, 16) auto 1px`) görünüyor. `Tükendi` düğmesi beyaz zemin üstünde `opacity: 0.55` ile yaklaşık `3,08:1` kontrast üretiyor (WCAG 1.4.3 devre dışı kontrolleri muaf tutsa da okunabilirlik zayıf).
- **Kanıt:** `kanitlar/02b-detay-tukendi.png` ve stil/kontrast ölçümü.

---

### HATA-14 — Masaüstünde "Biletlerim" tablosundaki `İptal et` düğmesi iki satıra sarılıyor ve e-posta kutusu adresi kırpıyor
- **Önem Derecesi:** Düşük (`Güven: Doğrulandı`)
- **Tekrar Üretme Adımları:**
  1. `1280×800` çözünürlükte `#/biletlerim` sayfasında `mehmet.demir@example.com` adresini sorgulayın.
- **Beklenen Sonuç:** `İptal et` düğmesi tek satırda görünmeli; e-posta giriş kutusu ortalama bir e-posta adresini kesmeden gösterebilmeli.
- **Gerçekleşen Sonuç:** Düğme metni `İptal` / `et` olarak iki satıra bölünüyor; e-posta kutusu `mehmet.demir@example.c` kısmında kesiliyor.
- **Kanıt:** `kanitlar/09-tutar-bicim-tutarsizligi.png`.

---

## 3. Sorular ve Gözlemler (Ürün Sahibine)

1. **Kampanya kodu yazılıp "Uygula"ya basılmadan sipariş verilmesi:** Kullanıcı `#kampanyaKodu` alanına geçerli `PERDE50` kodunu yazıp `Uygula` düğmesine tıklamadan doğrudan `Siparişi tamamla`'ya basarsa sistem kodu `""` olarak gönderiyor ve indirim uygulamadan tam fiyattan sipariş oluşturuyor (`KJ8P4F`). Form gönderilirken kod otomatik uygulanmalı mı yoksa kullanıcı uyarılmalı mı?
2. **Etkinlik verisi tutarsızlığı (`id: 102` — "matine" vs `22:00`):** *İstanbul Gençlik Senfonisi: Mevsimler* açıklamasında *"matine konserinde yorumluyor"* yazarken saat `22:00` (`2026-11-17T19:00:00.000Z`) görünüyor. Yalnızca demo içerik hatası mı yoksa saat/zaman dilimi kaynaklı bir karışıklık mı?
3. **Cep telefonu doğrulama kapsamı:** Ürün notunda *"cep telefonu"* istenmesine karşın API ve form `0212 000 00 00` (sabit hat), `0500 000 00 00` ve 12 haneli `055512345678` değerlerini kabul etti (`ZBJ82R`, `5HVKAL`, `EVJKUT`). Türkiye cep telefonu biçimi (`05XX...`, 10/11 hane) zorunlu kılınacak mı?
4. **Üyeliksiz "Biletlerim" sorgusu ve KVKK/gizlilik beklentisi:** İlk sürümde üyelik yok; ancak şu anda yalnızca bir kişinin e-posta adresini yazan herkes o kişinin tüm sipariş geçmişini görüntüleyebiliyor ve iptal edebiliyor. Demo/v0.9 için bu yeterli mi, yoksa e-posta + PNR kombinasyonu gibi ek bir doğrulama bekleniyor mu?
5. **`PERDE50` tekrar kullanım sınırı:** Aynı e-posta adresiyle birden çok siparişte `PERDE50` sınırsız kez kullanılabiliyor; kişi/e-posta başına kullanım sınırı var mı?
6. **Gereksiz çift API isteği (Gözlem):** `#/biletlerim` sayfasında sorgu yapıldığında tarayıcı ağ günlüğünde `GET /api/siparisler?eposta=...` isteğinin aynı anda iki kez atıldığı gözlendi; yoğunlukta gereksiz yük oluşturabilir.

---

## 4. Debrief

### Kapsanan Alanlar
- **İş akışları ve kurallar:** Etkinlik listeleme, arama, şehir filtresi, sıralama (tarih/fiyat/ad), etkinlik detayı, `Tam`/`Öğrenci` (%20) ve `12,50 TL` hizmet bedeli hesaplaması, `PERDE50` (`>= 300,00 TL`, hizmet bedeli dahil) kampanya sınırı, sipariş tamamlama, PNR onay ekranı, "Biletlerim" sorgulama, iptal ve koltuk iadesi.
- **Saldırı ve sağlamlık yoklamaları:** UI ve API sınır değerleri (`0`, `-1`, `1`, `6`, `7`, `1.5`, boş `""`, 60+ karakter), çift tıklama (buton kilitleniyor, 1 istek gidiyor), paralel sipariş yarışı (`105` no'lu 3 koltuklu etkinliğe `2+2` paralel istekte `201` + `409`, stok `-1`'e düşmedi), ikinci sekme/paralel iptal yarışı (`200` + `409`, koltuk iki kez iade edilmedi), 24 saat iptal kesim noktası, Geri/yenileme, derin bağlantılar (`#/etkinlik/999`, `#/onay/ZZZZZZ`, `#/olmayan`), HTML enjeksiyonu (ekranlarda kaçış/escape doğru çalışıyor), PNR ile IDOR, klavye gezintisi ve `320 px` / `375 px` mobil görünüm.

### Kapsanamayan Alanlar (Artık Risk)
- **Tarayıcı çeşitliliği:** Yalnızca Edge (Chromium) motorunda test edildi; güncel masaüstü Chrome ve gerçek mobil cihaz tarayıcılarında ayrıca doğrulanmadı.
- **Ekran okuyucu testi:** NVDA/JAWS/VoiceOver ile canlı okuma deneyimi test edilmedi (`HATA-06` ve `HATA-11` DOM/klavye incelemesiyle yakalandı).
- **Tam 24 saat sınırı (`23:59` vs `24:01`):** 24 saat kuralı genel olarak çalışmadığı için (`10,6` ve `22,6` saat kalan etkinlikler de iptal edildi) düzeltme sonrası tam sınır saati (`23:59:59` / `24:00:01`) ve UTC/UTC+3 sınır testi ayrıca yapılmalıdır.
- **Yük/performans ve uzun oturum:** Eşzamanlı yüksek trafik ve bellek sızıntısı test edilmedi.

### En Büyük Riskler
1. **Stok ve finansal veri bozulması (`HATA-01`, `HATA-02`):** Sunucu negatif ve sıfır bilet adedini kabul ettiği için eksi tutarlı sipariş oluşturulabiliyor ve tükenen etkinliklere dışarıdan yapay koltuk eklenebiliyor.
2. **24 saat iptal kuralının hiç işlememesi (`HATA-03`):** Etkinlik saatine saatler kala yapılan iptaller kapıda boş koltuk ve gelir kaybına yol açar.
3. **Türkçe arama ve klavye erişilebilirliği engelleri (`HATA-06`, `HATA-07`):** `"istanbul"` / `"izmir"` arayan kullanıcılar sonuç bulamıyor; klavye kullanıcıları indirimli öğrenci bileti seçemiyor.
4. **Kuruş tutarsızlığı ve PNR gizliliği (`HATA-04`, `HATA-05`):** Aynı siparişte 3 farklı tutar görülmesi güven zedeler; PNR üzerinden korumasız PII sızıntısı ve yetkisiz iptal mümkündür.

### Perşembe Sürüm Kararı Önerisi
- **Öneri: Mevcut haliyle yayına ALMA (Hold / Ertele).**  
- `HATA-01`, `HATA-02` (adet alt/üst sınır ve tam sayı doğrulaması), `HATA-03` (24 saat iptal kuralı), `HATA-05` (kuruş yuvarlama tutarlılığı), `HATA-06` (klavye ile bilet türü seçimi), `HATA-07` (Türkçe arama) ve `HATA-08` (`#/odeme` yenileme/geri çökmesi) düzeltilmeden Perşembe günkü canlı sürüme çıkılması yüksek iş ve itibar riski taşır.  
- Düzeltmeler sonrasında özellikle PNR bazlı erişim modeli (`HATA-04`) ve diğer ürün soruları ürün sahibiyle netleştirilip hızlı bir regresyon + 24 saat sınır doğrulaması yapılmalıdır.
