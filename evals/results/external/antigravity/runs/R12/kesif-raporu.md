# Perdeaçık Bilet (v0.9 Demo) — Keşif Testi Raporu

**Test edilen uygulama:** `http://127.0.0.1:4107`  
**Referans doküman:** `urun-notu.md` (Perdeaçık Etkinlik Hizmetleri — Ürün Sahibi: Selin Aksoy)  
**Tarih ve oturum aralığı:** 16 Kasım 2026, `18:29:36 – 18:39:11` (UTC+3)  
**Test yaklaşımı:** Kara kutu keşif testi (oturum bazlı charter yaklaşımı, gerçek Chrome ve Microsoft Edge tarayıcıları + CDP ağ/konsol/erişilebilirlik ağacı denetimi + doğrudan HTTP API istekleri)  
**Kanıt klasörü:** `kanitlar/`

---

## 1. Oturum Notları

### 1.1 Veri ve Uç Nokta Haritası (Recon Çıktısı)

Keşif başında uygulama gezilerek arayüz rotaları, etkileşimli alanlar ve ağ trafiğindeki REST uç noktaları haritalandı:

- **Arayüz rotaları (SPA):**
  - `#/` — Etkinlik listesi, arama (`#ara`), şehir filtresi (`#sehir`), sıralama (`#sirala`), sonuç sayacı (`#sonucSayisi`), etkinlik kartları (`#kartlar`)
  - `#/etkinlik/:id` — Etkinlik detayı, kalan koltuk (`.kalan`), bilet türü seçimi (`#turSecimi`: Tam / Öğrenci), adet (`#adet`), fiyat özeti (`#detayOzet`), `Devam et` (`#devamEt`)
  - `#/odeme` — Sipariş özeti (`#odemeOzet`), kampanya kodu (`#kampanyaKodu`, `#kampanyaUygula`), iletişim ve KVKK formu (`#adSoyad`, `#eposta`, `#telefon`, `#kvkk`)
  - `#/onay/:pnr` — Sipariş onay ekranı (PNR kodu, sipariş özeti, ödenmesi gereken toplam)
  - `#/biletlerim` — E-posta ile sipariş sorgulama (`#sorguEposta`), sipariş tablosu (`#siparisListesi`), iptal onay diyaloğu (`#iptalKutusu`)
- **API uç noktaları (ağ günlüğünden gözlenen):**
  - `GET /api/etkinlikler` (9 etkinlik; istemci tarafı filtreleme/sıralama)
  - `GET /api/etkinlikler/:id`
  - `GET /api/kampanya?kod=...&tutar=...`
  - `POST /api/siparisler`
  - `GET /api/siparisler?eposta=...`
  - `GET /api/siparisler/:pnr`
  - `POST /api/siparisler/:pnr/iptal`

### 1.2 Test Başlatma Belgeleri (Charter'lar) ve Turlar

Risk sırasına göre dört charter tanımlandı:

1. **C1 — Katalog, Arama, Filtreleme ve Yerelleştirme (Landmark & Türkçe Turu):**  
   *Hedef:* Ana sayfa listeleme, arama, şehir filtresi, sıralama ve tarih/para biçimlerini gerçek tarayıcı, Türkçe karakterler (`İ/ı/I/i/ş/ğ/ç/ö/ü`) ve `GET /api/etkinlikler` verileriyle keşfetmek; amaç: veri tutarsızlıklarını, arama/sıralama hatalarını ve tükenen etkinlik gösterimini bulmak.
2. **C2 — Bilet Seçimi, Fiyat/İndirim Hesaplama ve Sınır Değerler (Money & Boundary Turu):**  
   *Hedef:* Tam/Öğrenci fiyatlandırmasını, %20 indirimi, 12,50 TL hizmet bedelini, 1–6 bilet sınırını ve `PERDE50` (300,00 TL eşiği) kampanyasını sınır değerler (`0`, `-1`, `6`, `7`, `1.5`, `1,5`, `299,99`/`300,00`/`300,01` TL), kuruş yuvarlama ve doğrudan API istekleriyle keşfetmek; amaç: hesaplama, yuvarlama ve doğrulama açıklarını bulmak.
3. **C3 — Sipariş, Stok Yarışı, Biletlerim ve İptal/Yetkilendirme (Follow-the-Data, Concurrency & BOLA Turu):**  
   *Hedef:* Sipariş tamamlama, stok düşümü/iadesi, çift gönderim, Geri/Yenile/bayat sekme davranışları, 24 saat iptal kuralı ve PNR/e-posta yetkilendirmesini arayüz ve paralel HTTP istekleriyle keşfetmek; amaç: çift kayıt, stok tutarsızlığı, zaman kuralı ihlali ve yetkisiz erişim hatalarını bulmak.
4. **C4 — Kalite, WCAG 2.1 AA Erişilebilirlik, Mobil/Reflow ve Dayanıklılık (Supermodel & Antisocial Turu):**  
   *Hedef:* Tüm ekranları klavye navigasyonu, Chrome Accessibility Tree, kontrast ölçümü, masaüstü (`1280×900`) / mobil (`375×812`) / reflow (`320×568`) görünümleri, Microsoft Edge smoke testi, XSS ve bozuk JSON istekleriyle keşfetmek; amaç: erişilebilirlik engelleri, yerleşim taşmaları ve hata sızıntılarını bulmak.

### 1.3 Zaman Damgalı Oturum Notları

Etiketler: `NOT` (gözlem/hazırlık), `KAPSAM` (incelenen alan), `HATA` (bulunan hata), `SORU` (PO kararı gereken nokta), `FİKİR` (ek test fikri).

- `18:29:36` `NOT`: Test ortamı saati `2026-11-16 18:29:36 +03:00` olarak doğrulandı. Chrome headless + CDP başlatıldı.
- `18:29:59` `KAPSAM`: [C1] Ana sayfa açıldı (`01-ana-sayfa.png`), `GET /api/etkinlikler` ile 9 etkinlik doğrulandı: `101` (bugün `21:30`, 38 koltuk), `102` (yarın `17:00`, 64 koltuk — 24 saatten az!), `105` (3 koltuk), `106` (`kalan: 0`, Tükendi). Konsol hatası yok.
- `18:30:12` `KAPSAM`: [C1/C4] `#/etkinlik/103`, `#/etkinlik/106` (Tükendi) ve `#/biletlerim` gezildi. `106` detayında `#adet` ve `#devamEt` devre dışı.
- `18:30:12` `HATA`: [C4] Etkinlik detayında `.chip` bilet türü seçicileri `<div>` ile yapılmış; klavye erişimi veya ARIA rolü görünmüyor (C4'te doğrulanacak).
- `18:30:22` `KAPSAM`: [C1] `#/odeme` sayfası form ve özet alanları incelendi (`05-odeme-formu.png`).
- `18:30:42` `HATA`: [C1] `#ara` kutusunda `"istanbul"`, `"ISTANBUL"`, `"izmir"`, `"İZMİR"`, `"IZMIR"` aramaları 0 sonuç verdi; `"İSTANBUL"` ise 3 etkinlik döndürdü (`c1-arama-istanbul.png`).
- `18:30:52` `KAPSAM`: [C1] Şehir filtresi toplamları doğrulandı (Ankara 2 + Bursa 1 + Eskişehir 1 + İstanbul 3 + İzmir 2 = 9). Tarih, fiyat ve Türkçe ada göre (`A–Z`) sıralamalar (`Ç, İ, Ö, Ş, Ü` sırası dahil) doğru çalıştı (`c1-siralama-ad.png`).
- `18:30:54` `NOT`: [C1] `GET /api/etkinlikler?ara=...&sehir=...` sorgu parametreleri sunucu tarafından işlenmiyor (9 etkinliğin tamamı dönüyor); arama/filtreleme istemci tarafında yapılıyor.
- `18:32:29` `KAPSAM`: [C2] Öğrenci %20 indirimi ve hizmet bedeli (12,50 TL × adet) `101`, `103`, `104`, `107`, `108` üzerinde doğrulandı. `104` (`164,99 TL`) için Öğrenci birim fiyatı arayüzde `131,99 TL` gösteriliyor (`c2-104-ogrenci-1x.png`).
- `18:32:47` `KAPSAM`: [C2] `PERDE50` kampanya sınırı `GET /api/kampanya` ile `299.99` (422), `300` / `300.00` / `300.01` (200, 50 TL indirim), `perde50` / `' PERDE50 '` (200), `GECERSIZ` (404) ve arayüzde `107` 2× Tam (`300,00 TL` tam sınır) üzerinde test edildi (`c2-107-300tl-perde50.png`). `102` 6× Tam (`1.725,00 TL`) binlik/ondalık biçimi doğrulandı (`c2-102-1725tl-perde50.png`).
- `18:33:13` `HATA`: [C1] Ek Türkçe arama doğrulaması: `"İzmir"` 2 sonuç verirken `"izmir"` ve `"İZMİR"` 0 sonuç; `"resital"` 1 sonuç verirken `"RESİTAL"` 0 sonuç; `"kısa"` 1, `"KISA"` 0; `"konseri"` 1, `"KONSERİ"` 0; `"boğaziçi"` 1, `"BOĞAZİÇİ"` 0 döndürdü.
- `18:33:16` `HATA`: [C2/C3] `#/etkinlik/103` sayfasında `#adet` alanına `-1` girildiğinde `Devam et` engellemedi; `#/odeme` ekranında `-232,50 TL` özet gösterildi ve form gönderildiğinde `POST /api/siparisler` `201 Created` ile `89VMYD` PNR'lı `-1 × Tam` siparişi oluşturdu!
- `18:34:13` `HATA`: [C3] `#/odeme` sayfasında `"Siparişi tamamla"` butonuna çift tıklama 1 ms arayla iki `POST /api/siparisler` isteği gönderdi; aynı kullanıcı ve etkinlik (`108`) için `PEDRUJ` ve `R7H6BS` olmak üzere iki aktif sipariş oluştu (`c3-biletlerim-cem-iptal-oncesi.png`).
- `18:34:25` `KAPSAM`: [C3] `#/biletlerim` sorgulamasında büyük/küçük harf ve boşluk toleransı doğrulandı (`CEM.KAYA@EXAMPLE.COM`, `' cem.kaya@example.com '`). `PEDRUJ` arayüz üzerinden iptal edildi (`c3-iptal-onay-kutusu.png`, `c3-biletlerim-iptal-sonrasi.png`), stok `88 -> 89` geri açıldı.
- `18:34:48` `HATA`: [C3] `Biletlerim` tablosunda tüm tutarların sonundaki sıfırlar düşüyor (`232,5 TL`, `287,5 TL`, `162,4 TL`, `72,5 TL`).
- `18:34:49` `HATA`: [C2/C3] Doğrudan `POST /api/siparisler` saldırılarında `adet: 0` (`201`), `adet: -5` (`201`, toplam `-662.5`, Event `109` kalan koltuğu `75`'ten yukarı çekti), `adet: 7` (`201`, maksimum 6 sınırı aşıldı) ve `adet: 1.5` (`201`, `1` olarak kaydedildi) kabul edildi.
- `18:34:54` `HATA`: [C3] Yetkilendirme / BOLA: `GET /api/siparisler/F9S5VY` kimlik/e-posta olmadan tüm kişisel verileri döndürdü; `POST /api/siparisler/F9S5VY/iptal` farklı bir e-posta (`saldirgan@example.com`) ile gönderilmesine rağmen `200 OK` verip Cem Kaya'nın siparişini iptal etti.
- `18:34:54` `KAPSAM`: [C3] Çift iptal (idempotency): `PEDRUJ` ikinci kez iptal edilmek istendiğinde `409` döndü, stok çift artmadı. Paralel çift iptal yarışında (`H7CHBH`) biri `200`, diğeri `409` döndü. Bozuk JSON `400` döndü. `mass_assign` alanları (`toplam: 0.01`, `durum: "iptal"`, `pnr: "HACK99"`) sunucu tarafından yoksayıldı.
- `18:35:18` `HATA`: [C2/C3] `104` (`164,99 TL`) için `5 × Öğrenci + PERDE50`: Ödeme ekranı `672,45 TL` gösterirken sunucu `672.46` döndürdü ve onay ekranı `672,46 TL` gösterdi (`c3-siparis-onay-104.png`). `3 × Öğrenci` (`VEBDUD`) detay/ödemede `433,47 TL`, onayda `433,48 TL`, `Biletlerim`'de **`433,47600000000006 TL`** olarak göründü (`c3-biletlerim-tek-ondalik.png`, `c3-onay-yuvarlama-VEBDUD.png`).
- `18:35:18` `KAPSAM`: [C3] Stok yarışı: Event `105` (`kalan: 3`) için iki paralel `adet: 2` isteğinden ilki `201` (`kalan: 1`), ikincisi `409` (`Bu etkinlik için yeterli koltuk yok. Kalan koltuk: 1.`) döndü; aşırı satış olmadı.
- `18:36:08` `HATA`: [C3] 24 saat iptal kuralı ihlali: Etkinliğe ~3 saat kalan `101` (`LL84F2`) API üzerinden ve ~22,5 saat kalan `102` (`RBT2ND`) hem API hem Biletlerim arayüzü üzerinden başarıyla iptal edildi (`c3-24saat-altinda-iptal-basarili.png`).
- `18:37:29` `HATA`: [C3] `#/onay/:pnr` ekranından tarayıcı **Geri** tuşuna basıldığında, `#/odeme` yenilendiğinde veya doğrudan `#/odeme` açıldığında özet alanı `undefined × Tam bilet (NaN TL)` / `Ödenecek toplam NaN TL` gösteriyor (`c3-onay-sonrasi-geri-tusu.png`, `c3-dogrudan-odeme-bos-oturum.png`).
- `18:38:21` `KAPSAM`: [C3] Bayat sekme testi: Arka planda son koltukları tükenen `105` için açık `#/odeme` sekmesinden gönderilen sipariş `409` ile reddedildi ve kullanıcıya `"Bu etkinlik için yeterli koltuk yok. Kalan koltuk: 0."` gösterildi (`c3-bayat-sekme-tukendi-hata.png`).
- `18:38:29` `KAPSAM`: [C4] Microsoft Edge headless üzerinden ana sayfa, `103` Öğrenci seçimi ve `#/odeme` akışı duman testiyle sorunsuz doğrulandı.
- `18:36:49–18:39:11` `HATA` & `KAPSAM`: [C4] Klavye `Tab` akışında `#turSecimi` chiplerine erişilemedi (AXTree `StaticText`). `375×812` mobil görünüm sorunsuz; `320×568` reflow'da yalnızca `#/odeme` `352 px`'e taştı (`c4-reflow-320-odeme.png`). Kontrast oranları tüm metinlerde `>= 5.97:1` ve hedef boyutları `>= 24×24 px` geçti. XSS denemeleri (`<b>`, `<img onerror=...>`) çalıştırılmadı.

### 1.4 Kullanılan Test Verileri (Tamamı Uydurma)

- **Test kişileri:**
  - `Defne Yılmaz` — `defne.yilmaz@example.com` — `0555 000 00 01`
  - `Cem Kaya` — `cem.kaya@example.com` — `0555 000 00 02`
  - `Test Negatif` — `negatif.test@example.com` — `0555 000 00 99`
  - `Yuvarlama Testi` — `yuvarlama2@example.com` — `0555 000 00 10`
  - `Yirmi Dört Test` — `saat24@example.com` — `0555 000 00 50`
  - `Kampanya Sınır` — `kampanya300@example.com` — `0555 000 00 51`
  - `Geri Tuşu Test` — `geritusu@example.com` — `0555 000 00 52`
  - `Son Koltuk Alan` / `Geç Kalan Kullanıcı` — `sonkoltuk@example.com` / `geckalan@example.com`
  - İsim/telefon/API saldırı verileri: `api.bad@example.com`, `race1@example.com`, `race2@example.com`, `cancelrace@example.com`, `Ali-Can Yılmaz`, `Şebnem O'Connor`, `Dr. Ayşe Kaya`, `İğçöşü İĞÇÖŞÜ`, `<b>Ali Yılmaz</b>`, `0212 123 45 67`, `+90 555 123 45 67`, `0555 000 00 00`.
- **Arama ve kampanya verileri:** `istanbul`, `İSTANBUL`, `ISTANBUL`, `İzmir`, `izmir`, `İZMİR`, `resital`, `RESİTAL`, `kısa`, `KISA`, `konseri`, `KONSERİ`, `boğaziçi`, `BOĞAZİÇİ`, `<b>test</b>`, `PERDE50`, `perde50`, `' PERDE50 '`, `GECERSIZ`.

---

## 2. Hata Listesi

### HATA-01 — Etkinliğe 24 saatten az kalmasına rağmen sipariş iptali yapılabiliyor
- **Önem derecesi:** Kritik
- **Güven / Tekrarlanabilirlik:** Doğrulandı (her denemede tekrarlandı — hem `101` hem `102` etkinliğinde)
- **Ortam:** Chrome 141+ (masaüstü) & HTTP API (`http://127.0.0.1:4107`) · Sistem saati: `2026-11-16 18:36` (+03:00)
- **Ön koşul:** Başlangıç saati 24 saatten yakın bir etkinlik için aktif sipariş oluşturulmuş olması (ör. `101` — 16 Kasım `21:30` / ~3 saat kaldı; `102` — 17 Kasım `17:00` / ~22,5 saat kaldı).
- **Tekrar üretme adımları:**
  1. `102` numaralı etkinlik (`İstanbul Gençlik Senfonisi: Mevsimler`, tarih `2026-11-17T14:00:00.000Z` / `17 Kasım 2026 Salı · 17:00`) için 1 adet bilet siparişi oluşturun (ör. `saat24@example.com`, dönen PNR: `RBT2ND`).
  2. `#/biletlerim` sayfasına gidin ve `saat24@example.com` adresini sorgulayın.
  3. `RBT2ND` satırındaki `İptal et` düğmesine tıklayın ve açılan onay penceresinde `Evet, iptal et` seçin.
  4. (API doğrulaması) Etkinliğe ~3 saat kalan `101` (`LL84F2`) için `POST /api/siparisler/LL84F2/iptal` isteği gönderin.
- **Beklenen sonuç (`urun-notu.md`):** *"Etkinliğe 24 saatten fazla varsa siparişini iptal edebilmeli"*. Etkinliğe 24 saatten az kaldığı için iptal düğmesi sunulmamalı/etkin olmamalı ve API isteği reddedilmelidir.
- **Gerçekleşen sonuç:** Arayüzde `İptal et` düğmesi aktif geldi, onay sonrası `"RBT2ND kodlu siparişiniz iptal edildi. Koltuklar yeniden satışa açıldı."` mesajı gösterildi ve sipariş `"İptal edildi"` durumuna geçti. `POST /api/siparisler/LL84F2/iptal` (`~3 saat` kala) ve `POST /api/siparisler/RBT2ND/iptal` (`~22,5 saat` kala) her ikisi de `HTTP 200` ve `"durum": "iptal"` döndürdü.
- **Kanıt:** `kanitlar/c3-24saat-altinda-iptal-basarili.png`, API yanıtı: `POST /api/siparisler/LL84F2/iptal -> 200 {"pnr":"LL84F2",...,"etkinlikTarih":"2026-11-16T18:30:00.000Z","durum":"iptal"}`

---

### HATA-02 — Bilet adedinde alt/üst sınır ve tam sayı doğrulaması eksik; `0`, `-1` (negatif tutar ve stok artışı!) ve `7` kabul ediliyor
- **Önem derecesi:** Kritik
- **Güven / Tekrarlanabilirlik:** Doğrulandı (5/5 — hem arayüzde hem API'de)
- **Ortam:** Chrome & HTTP API (`http://127.0.0.1:4107`)
- **Ön koşul:** Satışta olan bir etkinlik (ör. `103` veya `109`).
- **Tekrar üretme adımları:**
  1. **Arayüz (negatif/sıfır):** `#/etkinlik/103` sayfasına gidin (`Kalan: 52 koltuk`). `Bilet adedi` (`#adet`) alanına `-1` (veya `0`, boş, `abc`) yazın ve `Devam et` düğmesine tıklayın.
  2. `#/odeme` sayfasında iletişim bilgilerini doldurup KVKK kutusunu işaretleyin ve `Siparişi tamamla` düğmesine tıklayın.
  3. **API (üst sınır ve ondalık):** `POST /api/siparisler` uç noktasına sırayla `"adet": 0`, `"adet": -5`, `"adet": 7` ve `"adet": 1.5` gövdeleri gönderin (`etkinlikId: 109`, başlangıç `kalan: 75`).
- **Beklenen sonuç (`urun-notu.md`):** *"Bir siparişte en az 1, en fazla 6 bilet olabilir."* Hem arayüz hem sunucu `1`–`6` aralığı dışındaki ve tam sayı olmayan değerleri doğrulama hatasıyla (`400`/`422`) reddetmelidir.
- **Gerçekleşen sonuç:**
  - Arayüzde `adet = -1` ile `#/odeme` sayfasına geçildi ve `-1 × Tam bilet (-220,00 TL)`, `Hizmet bedeli (-1 × 12,50 TL) -12,50 TL`, `Ödenecek toplam -232,50 TL` hesaplandı. Form gönderildiğinde `HTTP 201` ile `89VMYD` PNR'lı `-1 × Tam` siparişi oluştu ve `103` kalan koltuğu `52`'den `53`'e yükseldi (iptal edildiğinde 1 koltuk eksilip `51`'e düştü). `0`, boş `""` ve `"abc"` de `#/odeme` adımına geçiriyor.
  - Doğrudan `POST /api/siparisler` istekleri: `adet: 0` -> `201` (`AKPZH8`, `toplam: 0`); `adet: -5` -> `201` (`RM5B3N`, `toplam: -662.5`, Event `109` stoğunu +5 artırdı); `adet: 7` -> `201` (`S9JC9P`, `toplam: 927.5`); `adet: 1.5` -> `201` (`4SMHTS`, sessizce `adet: 1` olarak kesildi).
- **Kanıt:** `kanitlar/c2-103-adet-eksi1-detay.png`, `kanitlar/c2-103-adet-eksi1-odeme.png`, `kanitlar/c3-negatif-biletlerim.png`, `POST /api/siparisler` (`89VMYD`, `RM5B3N`, `S9JC9P`, `AKPZH8`, `4SMHTS`) HTTP 201 yanıtları.
- **Not (şüphe):** Arayüzde yalnızca `adet > 6` kontrolü yapılıp `adet < 1` / `!Number.isInteger` kontrolü unutulmuş; sunucuda ise `adet` üzerinde hiç aralık doğrulaması yok ve `kalan -= adet` işlemi doğrudan uygulanıyor.

---

### HATA-03 — Öğrenci biletinde kuruşlu fiyatlarda ekranlar ve API arasında toplam tutar uyuşmazlığı
- **Önem derecesi:** Yüksek
- **Güven / Tekrarlanabilirlik:** Doğrulandı (her denemede — `104` etkinliği Öğrenci `3` ve `5` adet)
- **Ortam:** Chrome & HTTP API (`http://127.0.0.1:4107`)
- **Ön koşul:** %20 indirimi yarım kuruş üreten bir etkinlik (ör. `104 — İzmir Kordon Akustik`, Tam fiyatı `164,99 TL`; `%20` indirimli fiyat `131,992 TL`).
- **Tekrar üretme adımları:**
  1. `#/etkinlik/104` sayfasında `Öğrenci` bilet türünü seçin, adedi `5` yapın ve `Devam et` ile `#/odeme` sayfasına geçin.
  2. `Kampanya kodu` alanına `PERDE50` yazıp `Uygula`'ya tıklayın ve `#odemeOzet` toplamını okuyun.
  3. Formu doldurup `Siparişi tamamla`ya basın; açılan `#/onay/:pnr` ekranındaki ve `POST /api/siparisler` yanıtındaki toplamı karşılaştırın.
  4. Aynı karşılaştırmayı `3 × Öğrenci` (kampanyasız) için de tekrarlayın.
- **Beklenen sonuç (`urun-notu.md` + tutarlılık ilkesi):** Etkinlik detayı, ödeme özeti, sipariş onay sayfası, Biletlerim ve API aynı sipariş için birebir aynı tutarı göstermelidir.
- **Gerçekleşen sonuç:**
  - `5 × Öğrenci + PERDE50`: Detay/Ödeme özeti birim fiyatı yuvarlayarak hesaplar (`5 × 131,99 + 62,50 - 50,00 =` **`672,45 TL`**). Ancak `POST /api/siparisler` (`BEUPD9`, `5AKUNF`), Onay ekranı ve Biletlerim **`672,46 TL`** gösterir (`164,99 × 0,8 × 5 = 659,96`).
  - `3 × Öğrenci` (`VEBDUD`): Detay/Ödeme özeti **`433,47 TL`** (`3 × 131,99 + 37,50`), Onay ekranı **`433,48 TL`**, API yanıtı `toplam: 433.47600000000006` gösterir.
- **Kanıt:** `kanitlar/c3-siparis-onay-104.png` (`672,46 TL`), `kanitlar/c3-onay-yuvarlama-VEBDUD.png` (`433,48 TL`), `POST /api/siparisler` yanıtı (`toplam: 672.46` / `433.47600000000006`).
- **Not (şüphe):** İstemci tarafı birim fiyatı önce 2 ondalığa yuvarlayıp adetle çarparken, sunucu yuvarlamasız kayan nokta çarpımı yapmaktadır.

---

### HATA-04 — Arama kutusunda Türkçe `İ/ı` büyük/küçük harf duyarsızlığı bozuk (`istanbul`, `izmir`, `İZMİR`, `RESİTAL` sonuç döndürmüyor)
- **Önem derecesi:** Yüksek
- **Güven / Tekrarlanabilirlik:** Doğrulandı (her denemede — tüm `İ/I/i/ı` içeren terimlerde)
- **Ortam:** Chrome (`http://127.0.0.1:4107/#/`)
- **Ön koşul:** Ana sayfadaki 9 etkinlik yüklü.
- **Tekrar üretme adımları:**
  1. `#/` sayfasındaki `Ara` (`#ara`) kutusuna sırayla `"istanbul"`, `"izmir"`, `"İZMİR"`, `"RESİTAL"`, `"KISA"`, `"KONSERİ"`, `"BOĞAZİÇİ"` yazın.
  2. Karşılaştırma için `"İSTANBUL"`, `"İzmir"`, `"resital"`, `"kısa"`, `"konseri"`, `"boğaziçi"` yazın.
- **Beklenen sonuç (`urun-notu.md`):** *"etkinlik adı, şehir veya mekâna göre arama yapabilmeli"* ve *"Arayüz Türkçe; Türkçe içerik sorunsuz desteklenmeli"*. Türkçe büyük/küçük harf kurallarına göre `"istanbul"` / `"İSTANBUL"` 3 etkinlik, `"izmir"` / `"İzmir"` / `"İZMİR"` 2 etkinlik, `"resital"` / `"RESİTAL"` 1 etkinlik döndürmelidir.
- **Gerçekleşen sonuç:** `"istanbul"`, `"izmir"`, `"İZMİR"`, `"RESİTAL"`, `"KISA"`, `"KONSERİ"`, `"BOĞAZİÇİ"` aramalarının tümü `"Aramanızla eşleşen etkinlik bulunamadı."` (0 sonuç) döndürürken, yalnızca `"İSTANBUL"` (3), `"İzmir"` (2), `"resital"` (1), `"kısa"` (1), `"konseri"` (1), `"boğaziçi"` (1) sonuç döndürmektedir.
- **Kanıt:** `kanitlar/c1-arama-istanbul.png`
- **Not (şüphe):** Türkçe locale (`toLocaleLowerCase('tr-TR')`) yerine varsayılan `.toLowerCase()` kullanılıyor olabilir (`'İ'.toLowerCase()` -> `'i\u0307'`).

---

### HATA-05 — "Siparişi tamamla" düğmesine çift tıklamada aynı sipariş iki kez oluşturuluyor
- **Önem derecesi:** Yüksek
- **Güven / Tekrarlanabilirlik:** Doğrulandı
- **Ortam:** Chrome (`http://127.0.0.1:4107/#/odeme`)
- **Ön koşul:** Herhangi bir etkinlik (ör. `108`, `kalan: 90`) için `#/odeme` sayfasında geçerli iletişim bilgileri ve KVKK onayı doldurulmuş.
- **Tekrar üretme adımları:**
  1. `#/etkinlik/108` -> `Devam et` ile `#/odeme` sayfasına geçin.
  2. Ad Soyad (`Cem Kaya`), E-posta (`cem.kaya@example.com`), Telefon (`0555 000 00 02`) ve KVKK onayını doldurun.
  3. `Siparişi tamamla` düğmesine hızlıca iki kez tıklayın.
  4. `#/biletlerim` üzerinden `cem.kaya@example.com` siparişlerini ve `108` kalan koltuk sayısını kontrol edin.
- **Beklenen sonuç:** İlk tıklamada düğme devre dışı bırakılmalı / yüklenme durumuna geçmeli ve kullanıcı aynı işlem için tek sipariş oluşturmalıdır.
- **Gerçekleşen sonuç:** Tarayıcı 1 ms arayla iki `POST /api/siparisler` isteği gönderdi (`15:34:13.909Z` ve `15:34:13.910Z`); sunucu ikisini de `201 Created` ile işleyerek aynı etkinlik için iki ayrı aktif sipariş (`PEDRUJ` ve `R7H6BS`) oluşturdu ve stok 2 koltuk düştü (`90 -> 88`).
- **Kanıt:** `kanitlar/c3-biletlerim-cem-iptal-oncesi.png` (`R7H6BS` ve `PEDRUJ` çift satır)

---

### HATA-06 — Etkinlik detayında bilet türü seçimi (`Tam` / `Öğrenci`) klavyeyle erişilemiyor (WCAG 2.1 AA ihlali)
- **Önem derecesi:** Yüksek (Erişilebilirlik)
- **Güven / Tekrarlanabilirlik:** Doğrulandı (Chrome Tab sırası ve Accessibility Tree denetimi)
- **Ortam:** Chrome (`http://127.0.0.1:4107/#/etkinlik/103`)
- **Ön koşul:** Herhangi bir etkinlik detay sayfası açık.
- **Tekrar üretme adımları:**
  1. `#/etkinlik/103` sayfasında `Tab` tuşuyla etkileşimli öğeler arasında ilerleyin.
  2. Odak `"← Tüm etkinlikler"` bağlantısındayken bir kez `Tab`'a basın; `Öğrenci` seçeneğine odaklanmayı ve `Enter`/`Space` ile seçmeyi deneyin.
- **Beklenen sonuç (`urun-notu.md` / WCAG 2.1 SC 2.1.1 & SC 4.1.2):** Tüm işlevler klavyeyle kullanılabilmeli; bilet türü seçenekleri odaklanabilir olmalı ve rol/durum bilgisi (`radio`/`button`, `aria-checked`/`aria-pressed`) ekran okuyuculara iletilmelidir.
- **Gerçekleşen sonuç:** `#turSecimi` içindeki seçenekler `<div class="chip" data-tur="tam">` ve `<div class="chip" data-tur="ogrenci">` olarak tanımlanmış; `tabindex`, `role`, `aria-checked` ve klavye olayı yok. `Tab` sırası `"← Tüm etkinlikler"` bağlantısından doğrudan `#adet` alanına atlıyor; klavye kullanıcısı `%20 indirimli Öğrenci` biletini seçemiyor. Accessibility Tree içinde yalnızca `StaticText` olarak yer alıyor.
- **Kanıt:** Chrome CDP Tab dizisi (`['A#.[← Tüm etkinlikler]', 'INPUT#adet.[1]', 'BUTTON#devamEt.birincil[Devam et]']`) ve DOM çıktısı.

---

### HATA-07 — Yalnızca PNR koduyla başka kullanıcıların kişisel verileri okunabiliyor ve siparişleri iptal edilebiliyor (BOLA / IDOR)
- **Önem derecesi:** Yüksek (Güvenlik / Gizlilik)
- **Güven / Tekrarlanabilirlik:** Doğrulandı
- **Ortam:** HTTP API (`http://127.0.0.1:4107`)
- **Ön koşul:** Sistemde başka bir kullanıcıya ait aktif bir sipariş bulunması (ör. `cem.kaya@example.com` -> `F9S5VY`).
- **Tekrar üretme adımları:**
  1. Oturum/çerez/e-posta olmadan `GET http://127.0.0.1:4107/api/siparisler/F9S5VY` isteği gönderin.
  2. Ardından `POST http://127.0.0.1:4107/api/siparisler/F9S5VY/iptal` isteğini boş gövdeyle `{}` veya ilgisiz bir e-postayla (`{"eposta":"saldirgan@example.com"}`) gönderin.
- **Beklenen sonuç (OWASP API1:2023 BOLA / ASVS V8 & V14):** Yalnızca PNR koduyla üçüncü kişilerin tam ad soyad, e-posta ve cep telefonu bilgilerine erişilememeli; sipariş iptali sahiplik doğrulaması (en azından sipariş sahibinin e-postası veya doğrulama belirteci) olmadan gerçekleştirilememelidir.
- **Gerçekleşen sonuç:** `GET /api/siparisler/F9S5VY` `HTTP 200` ile sipariş sahibinin `adSoyad`, `eposta` ve `telefon` bilgilerini döndürdü. `POST /api/siparisler/F9S5VY/iptal` ise gönderilen `eposta` alanını kontrol etmeden `HTTP 200` döndürüp Cem Kaya'nın siparişini iptal etti.
- **Kanıt:**
  - `GET /api/siparisler/F9S5VY -> 200 {"pnr":"F9S5VY",...,"adSoyad":"Cem Kaya","eposta":"cem.kaya@example.com","telefon":"0555 000 00 02","durum":"aktif"}`
  - `POST /api/siparisler/F9S5VY/iptal` (`{"eposta":"saldirgan@example.com"}`) `-> 200 {..., "durum":"iptal"}`

---

### HATA-08 — "Biletlerim" tablosunda tutarlar iki ondalık basamakla biçimlendirilmiyor ve ham kayan nokta değerleri görünüyor
- **Önem derecesi:** Orta
- **Güven / Tekrarlanabilirlik:** Doğrulandı (her denemede)
- **Ortam:** Chrome (`http://127.0.0.1:4107/#/biletlerim`)
- **Ön koşul:** Kuruş hanesi `0` ile biten (ör. `232,50`, `162,40`) veya yuvarlanmamış Öğrenci indirimli (`104` etkinliği `1×` veya `3×` Öğrenci) siparişlerin olması.
- **Tekrar üretme adımları:**
  1. `#/biletlerim` sayfasında `cem.kaya@example.com` ve `yuvarlama2@example.com` e-postalarını sorgulayın.
  2. Tablodaki `Tutar` sütununu inceleyin.
- **Beklenen sonuç (`urun-notu.md`):** *"Tutarlar TL cinsinden, iki ondalık basamakla ve Türkçe biçimde gösterilmeli (ör. 1.234,50 TL)."*
- **Gerçekleşen sonuç:**
  - `cem.kaya@example.com` siparişlerinde `232,5 TL`, `287,5 TL`, `162,4 TL`, `72,5 TL` (sondaki sıfır eksik, tek ondalık) görünüyor.
  - `yuvarlama2@example.com` siparişlerinde `VEBDUD` (`3 × Öğrenci`) için **`433,47600000000006 TL`** ve `PM5V8B` (`1 × Öğrenci`) için **`144,49200000000002 TL`** gösteriliyor.
- **Kanıt:** `kanitlar/c3-biletlerim-cem-iptal-oncesi.png`, `kanitlar/c3-biletlerim-tek-ondalik.png`

---

### HATA-09 — `#/odeme` sayfası yenilendiğinde, doğrudan açıldığında veya onaydan "Geri" dönüldüğünde `undefined` / `NaN TL` gösteriyor
- **Önem derecesi:** Orta
- **Güven / Tekrarlanabilirlik:** Doğrulandı
- **Ortam:** Chrome (`http://127.0.0.1:4107/#/odeme`)
- **Ön koşul:** (A) Yeni sekmede `#/odeme` adresinin açılması, (B) `#/odeme` sayfasında tarayıcı yenilemesi (`F5`), veya (C) sipariş onayından (`#/onay/:pnr`) tarayıcının Geri tuşuna basılması.
- **Tekrar üretme adımları:**
  1. Yeni bir tarayıcı profilinde doğrudan `http://127.0.0.1:4107/#/odeme` adresine gidin; veya bir sipariş tamamlayıp `#/onay/:pnr` ekranından tarayıcı Geri düğmesine basın.
  2. `Sipariş özeti` kutusunu inceleyin.
  3. Aynı sekmede daha önce bir etkinlik seçilmişse (yenileme veya Geri sonrası), iletişim bilgilerini doldurup `Siparişi tamamla`ya tıklayın.
- **Beklenen sonuç:** Geçerli seçilmiş bilet yoksa kullanıcı etkinlik listesine yönlendirilmeli veya anlamlı bir uyarı gösterilmeli; bozuk/anlamsız fiyat hesapları görüntülenmemeli ve gizli bir önceki seçimle sipariş gönderilmemelidir.
- **Gerçekleşen sonuç:** Sipariş özeti **`undefined`**, **`undefined × Tam bilet (NaN TL)`**, **`Hizmet bedeli (undefined × 12,50 TL) NaN TL`**, **`Ödenecek toplam NaN TL`** olarak görüntüleniyor. Ayrıca önceden aynı sekmede `105` etkinliği seçilmişse, `NaN TL` görünmesine rağmen form gönderildiğinde arka planda `{"etkinlikId":105,"tur":"tam","adet":1,...}` siparişi gönderiliyor.
- **Kanıt:** `kanitlar/c3-onay-sonrasi-geri-tusu.png`, `kanitlar/c3-dogrudan-odeme-bos-oturum.png`

---

### HATA-10 — 320 px genişlikte ödeme sayfasında yatay taşma oluşuyor (WCAG 2.1 AA Reflow)
- **Önem derecesi:** Orta (Mobil / Erişilebilirlik)
- **Güven / Tekrarlanabilirlik:** Doğrulandı
- **Ortam:** Chrome DevTools mobil emülasyon (`320×568` CSS px)
- **Ön koşul:** `103` etkinliği seçilerek `#/odeme` sayfasına geçilmiş.
- **Tekrar üretme adımları:**
  1. Tarayıcı genişliğini `320 px` (`320×568`) yapın (`%400` yakınlaştırma / WCAG 1.4.10 Reflow genişliği).
  2. `#/odeme` sayfasını görüntüleyin ve `document.documentElement.scrollWidth` değerini kontrol edin.
- **Beklenen sonuç (`urun-notu.md` / WCAG 2.1 SC 1.4.10 Reflow):** 320 CSS px genişlikte içerik iki yönlü yatay kaydırma gerektirmeden ekrana sığmalıdır. (`375×812` genişliğinde sığmaktadır.)
- **Gerçekleşen sonuç:** `#odemeFormu` (`336,16 px`) ve içerik 320 px dışına taşarak doküman genişliğini `352 px`'e çıkarıyor; üst çubuk ve alt bilgi sağ kenarda 320 px'te kesilip sağda beyaz boşluk bırakıyor.
- **Kanıt:** `kanitlar/c4-reflow-320-odeme.png`

---

### HATA-11 — Ödeme formu hata mesajları ilgili alanlarla programatik olarak ilişkilendirilmemiş
- **Önem derecesi:** Düşük (Erişilebilirlik)
- **Güven / Tekrarlanabilirlik:** Doğrulandı
- **Ortam:** Chrome (`http://127.0.0.1:4107/#/odeme`)
- **Ön koşul:** `#/odeme` ekranı açık.
- **Tekrar üretme adımları:**
  1. Form alanlarını boş bırakarak `Siparişi tamamla`ya tıklayın.
  2. DOM üzerindeki `#adSoyad`, `#eposta`, `#telefon`, `#kvkk` alanlarının `aria-invalid`, `aria-describedby` özniteliklerini ve aktif odağı inceleyin.
- **Beklenen sonuç (WCAG 2.1 SC 3.3.1):** Hata durumundaki alanlar `aria-invalid="true"` ve `aria-describedby` ile ilgili hata mesajına bağlanmalı veya odak ilk hatalı alana taşınmalıdır.
- **Gerçekleşen sonuç:** Hatalar yalnızca alttaki `#odemeHata` (`role="alert"`) kutusunda listeleniyor; inputların tamamında `aria-invalid: null` ve `aria-describedby: null` kalıyor, odak formu gönderen öğe/içerikte (`#icerik`) kalıyor.
- **Kanıt:** `kanitlar/c4-odeme-hata-durumu.png`

---

## 3. Sorular ve Gözlemler

Aşağıdaki noktalar mevcut ürün notunda (`urun-notu.md`) açıkça tanımlanmadığından hata olarak yazılmamış, ürün sahibinin (Selin Aksoy) karar vermesi gereken sorular ve mimari gözlemler olarak ayrılmıştır:

1. **[SORU — PNR ve sahiplik politikası]:** İlk sürümde üyelik yok; bu nedenle onay sayfası `#/onay/:pnr` PNR kodu ile açılıyor. Ancak `Biletlerim` e-posta ile çalışırken API uç noktaları PNR bilen herkesin bilgileri görmesine ve iptal etmesine izin veriyor (bkz. `HATA-07`). Sadece **iptal** işlemi için e-posta eşleşmesi zorunlu tutulmalı mı, yoksa onay sayfasında kişisel veriler maskelenmeli mi?
2. **[SORU — 24 saat iptal sınırı ve saat dilimi]:** `HATA-01` düzeltilirken tam `24:00:00` sınır anı iptale izin vermeli mi yoksa yalnızca `> 24 saat` (`24 saat 1 saniye` ve üzeri) mi izinli olmalı? Ayrıca kontrol sunucu saatine (`UTC+3`) göre mi yapılmalı?
3. **[SORU — Öğrenci indirimi kuruş yuvarlama yöntemi]:** `164,99 TL` gibi fiyatların `%20` indiriminde (`131,992 TL`), yuvarlama **bilet başına mı** (`131,99 × 5 = 659,95 TL`) yoksa **sipariş/satır toplamında mı** (`164,99 × 0,8 × 5 = 659,96 TL`) uygulanmalı? (Ekranlar arası tutarsızlık `HATA-03`'te raporlanmıştır.)
4. **[SORU — Aynı siparişte karma bilet türü]:** Şu an bir siparişte yalnızca `Tam` veya yalnızca `Öğrenci` seçilebiliyor (ör. 1 Tam + 1 Öğrenci aynı siparişte alınamıyor; bu durum `PERDE50` 300 TL eşiğine tek siparişte ulaşmayı da etkileyebilir). Bu v0.9 için bilinçli bir kısıt mı?
5. **[SORU — Uygulanan kampanya kodunu kaldırma ve kullanım sınırı]:** Ödeme ekranında `PERDE50` uygulandıktan sonra kodu kaldırmak/iptal etmek için bir düğme yok (yalnızca geçersiz bir kod yazılırsa veya sayfa değiştirilirse sıfırlanıyor). Ayrıca aynı e-posta adresiyle `PERDE50` sınırsız kez kullanılabiliyor. Kullanım sınırı veya "Kaldır" butonu bekleniyor mu?
6. **[SORU — Cep telefonu ve Ad Soyad doğrulama kuralları]:**
   - `Cep telefonu` alanı `"0212 123 45 67"` gibi sabit hat numaralarını ve `0555 000 00 00` değerini kabul ediyor; yalnızca `05XX` mobil numara mı zorunlu tutulmalı?
   - `Ad Soyad` alanı `"A B"` (2 harf + 1 boşluk) değerini kabul ederken `"Yarış 1"` gibi rakam içeren girdileri `"Ad soyad en az 3 harften oluşmalı ve yalnızca harf içermelidir."` diyerek reddediyor. Minimum harf sayısı boşluk hariç mi sayılmalı?
7. **[GÖZLEM — API durum kodları ve istemci filtreleme]:** `GET /api/etkinlikler?sehir=Ankara` sorgu parametrelerini görmezden gelip tüm listeyi dönüyor (filtreleme tamamen istemcide). Ayrıca geçersiz kampanya koşulu `GET /api/kampanya`'da `422`, `POST /api/siparisler`'de `400` dönüyor. İleride harici tüketiciler eklenecekse API hata kodlarının ve filtre parametrelerinin standartlaştırılması önerilir.
8. **[GÖZLEM — Güvenlik başlıkları ve Erişilebilirlik iyileştirmesi]:** Sunucu yanıtlarında `Cache-Control: no-store` bulunuyor; ancak `X-Content-Type-Options: nosniff`, `Content-Security-Policy` ve `X-Frame-Options` başlıkları yok. Erişilebilirlik tarafında ise `<nav>`/`<main>` landmark'ları ve kontrast değerleri (`>= 5,97:1`) güçlü olmakla birlikte, klavye kullanıcıları için `"İçeriğe atla"` bağlantısı eklenmesi ve SPA geçişlerinde odak yönetiminin netleştirilmesi faydalı olacaktır.

---

## 4. Debrief

### Kapsanan Alanlar
- **Ana sayfa:** Tüm etkinlik listesi (9 etkinlik), arama (Türkçe büyük/küçük harf, boşluk, HTML/XSS), şehir filtresi, 3 sıralama seçeneği, tükenen etkinlik rozeti (`106`), `GET /api/etkinlikler` ile ekran tutarlılığı.
- **Etkinlik detayı & fiyatlama:** Tam/Öğrenci seçimi, `%20` indirim ve `12,50 TL` hizmet bedeli hesapları, kuruş yuvarlama (`104`), `1–6` adet sınır değerleri (`0`, `-1`, `1`, `6`, `7`, `1.5`, `1,5`, `abc`, boş), stok sınırı (`105` kalan 3 iken 4/6 denemesi) ve tükenen etkinlik engeli (`106`).
- **Ödeme, kampanya & sipariş oluşturma:** `PERDE50` eşik sınırları (`299,99` / `300,00` / `300,01 TL`), büyük/küçük harf ve boşluk toleransı, form doğrulama kuralları, çift tıklama (`double-submit`), tarayıcı Yenile / Geri tuşu, bayat sekme stok tükenmesi (`105`), paralel stok yarışı (concurrency) ve doğrudan API manipülasyonu (`toplam`/`durum`/`pnr` mass assignment, bozuk JSON).
- **Biletlerim & iptal:** E-posta sorgulama (büyük/küçük harf, boşluk, XSS), sipariş tablosu ve para birimi gösterimi, iptal onay diyaloğu (`Esc` ve odak dönüşü dahil), stok iadesi, çift/paralel iptal idempotency, 24 saat iptal kuralı (`~3 saat` ve `~22,5 saat` kalan etkinlikler), PNR tabanlı BOLA/IDOR.
- **Kalite nitelikleri:** Chrome (`1280×900`, `375×812`, `320×568`) ve Microsoft Edge duman testi, klavye `Tab` akışı, Chrome AXTree, renk kontrastı, hedef boyutları (`>= 24×24 px`), HTTP yanıt başlıkları.

### Kapsanamayan Alanlar (Kalan Boşluklar)
- **Gerçek ekran okuyucu (NVDA / VoiceOver / TalkBack) ile sesli okuma testi:** AXTree ve HTML nitelikleri incelendi, ancak gerçek yardımcı teknoloji yazılımıyla Türkçe telaffuz dinlenmedi.
- **%200 tarayıcı yakınlaştırma (SC 1.4.4) ve metin aralığı artırma (SC 1.4.12) testi:** Yalnızca `320 px` reflow ve `375 px` mobil genişlik test edildi.
- **Sunucu yeniden başlatma / bellek sıfırlama ve uzun süreli yük/performans testi (k6):** Ürün notunda verilerin bellekte tutulduğu belirtilmiş; performans eşiği tanımlanmadığından yük testi yapılmadı.
- **Kayıtlı veri kalıcılığı ve gerçek e-posta / gişe ödeme entegrasyonları:** Demo kapsamında kapsam dışı olduğundan test edilmedi.
- **Tam 24:00:00 sınır saniyesi:** Test ortamı saatiyle `~3 saat` ve `~22,5 saat` kalan etkinlikler mevcuttu (`23:59:59` vs `24:00:01` arası etkinlik yoktu).

### En Büyük Riskler
1. **Finansal ve stok bütünlüğü riski (`HATA-02`, `HATA-03`, `HATA-05`):** Negatif ve sıfır bilet adediyle sipariş oluşturulup stok artırılabilmesi, 6 bilet üst sınırının API'de aşılabilmesi, çift tıklamayla mükerrer sipariş oluşması ve ödeme ekranındaki tutarın onay/API tutarıyla kuruş farkı göstermesi doğrudan gelir, koltuk kapasitesi ve müşteri güvenini tehdit ediyor.
2. **İş kuralı ve yetkisiz işlem riski (`HATA-01`, `HATA-07`):** Etkinliğe 24 saatten az kala siparişlerin iptal edilebilmesi etkinlik gününde koltukların son anda boşalmasına yol açar. PNR bilen herkesin doğrulamasız kişisel verileri okuyabilmesi ve başkasının biletini iptal edebilmesi ciddi gizlilik ve suistimal riskidir.
3. **Türkçe kullanıcı ve erişilebilirlik engeli (`HATA-04`, `HATA-06`):** İstanbul ve İzmir gibi ana şehir aramalarının küçük harfle sıfır sonuç vermesi ilk temasta uygulamanın bozuk algılanmasına neden olur; klavye kullanıcılarının Öğrenci indirimi seçememesi ise WCAG 2.1 Level A bariyeri oluşturur.

### Sürüm İçin Öneri (Perşembe Sürüm Kararı)
Karar paydaşlara aittir; mevcut bulgular ışığında **üç net seçenek** sunulmaktadır:

- **Seçenek A — Önerilen (Düzeltme sonrası yayın / Koşullu Onay):** Perşembe gününe kadar en azından **Kritik ve Yüksek** öncelikli iş/erişilebilirlik/güvenlik hataları (`HATA-01` 24 saat iptal kilidi, `HATA-02` `1–6` tam sayı bilet adedi doğrulaması, `HATA-03` & `HATA-08` yuvarlama birliği ve 2 ondalık TL biçimi, `HATA-04` Türkçe arama, `HATA-05` çift tıklama engeli, `HATA-06` klavye ile bilet türü seçimi, `HATA-07` iptalde e-posta/sahiplik doğrulaması) kapatılıp regresyon doğrulaması yapılmadan canlıya çıkılmaması önerilir.
- **Seçenek B — Erteleme:** Bu düzeltmeler Perşembe gününe yetişmeyecekse genel kullanıma açılışın ertelenmesi önerilir.
- **Seçenek C — Risk kabulü ile kısıtlı demo:** Uygulama yalnızca iç/kapalı bir demo tanıtımı için açılacaksa ürün sahibi **Selin Aksoy**'un yukarıdaki açık riskleri (özellikle `HATA-01`, `HATA-02`, `HATA-04`, `HATA-06`, `HATA-07`) yazılı olarak kabul etmesi gerekir; aksi halde gerçek kullanıcıya açık sürüm için uygun değildir.
