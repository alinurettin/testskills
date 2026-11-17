# Perdeaçık Bilet (v0.9 Demo) — Keşif Testi Raporu

**Test Uzmanı:** Kıdemli QA Mühendisi  
**Test Tarihi ve Saati:** 17 Kasım 2026, 00:34 – 00:47 TRT (UTC+03:00)  
**Test Ortamı:** `http://127.0.0.1:4112` (kara kutu test; kaynak koda erişilmeden yalnızca tarayıcı arayüzü, tarayıcı geliştirici protokolü/ağ trafiği ve doğrudan HTTP API istekleri üzerinden test edildi)  
**Ortam ve Tarayıcılar:** Google Chrome `157.0.8103.52` (masaüstü `1280×800`, mobil `390×844` ve `360×740`), Microsoft Edge `157.0.4341.46` (masaüstü `1280×800`)  
**Referans Doküman:** `urun-notu.md` (Perdeaçık Bilet — Ürün notu v0.9 demo)

---

## 1. Oturum Notları

Test oturumu, SBTM (Session-Based Test Management) yaklaşımıyla 6 odak charter üzerinden yürütüldü. Test sonunda oluşturulan geçici test siparişleri iptal edilerek tüm etkinliklerin kalan koltuk sayıları başlangıç değerlerine döndürüldü (`101: 38`, `102: 64`, `103: 52`, `104: 80`, `105: 3`, `106: 0`, `107: 110`, `108: 90`, `109: 75`).

### Charter Listesi ve Zaman Damgalı Notlar

- **Charter 1 (00:34 – 00:36) — Katalog Keşfi, Arama, Şehir Filtresi, Sıralama ve Türkçe Yerelleştirme**
  - **00:34** Ana sayfa (`#/`) açıldı; 9 etkinlik listelendi. Konsol hatası veya istisna görülmedi (`kanitlar/01_ana_sayfa_masaustu.png`).
  - **00:35** Ağ trafiği gözlendi: `/api/etkinlikler` üzerinden 9 etkinlik geliyor. Saatler incelendiğinde `101` (`Boğaziçi Caz Gecesi`, 17 Kasım 10:00 — ~9,5 saat sonra) ve `102` (`İstanbul Gençlik Senfonisi: Mevsimler`, 17 Kasım 22:30 — ~22 saat sonra) etkinliklerinin 24 saatten yakın olduğu; `105` (`Şebnem'in Düğünü`) için yalnızca 3 koltuk kaldığı; `106` (`Zeybek ve Ege Ezgileri`) etkinliğinin tükendiği not edildi.
  - **00:36** Arama kutusunda Türkçe büyük/küçük harf testi yapıldı: `"istanbul"`, `"izmir"`, `"İZMİR"`, `"ESKİŞEHİR"`, `"BOĞAZİÇİ"` ve `"KISA"` aramaları `0` sonuç döndürdü (`kanitlar/19_turkce_arama_izmir.png`). Buna karşın `"Ada göre (A–Z)"` sıralamasının Türkçe alfabe sırasına (`A, B, Ç, İ, Ö, Ş, Ü, Z`) uygun çalıştığı, detay sayfasından geri dönüldüğünde seçili şehir/sıralama filtresinin korunduğu görüldü.

- **Charter 2 (00:36 – 00:39) — Etkinlik Detayı, Fiyat Hesaplama, İndirim, `PERDE50` ve Sınır Değerleri**
  - **00:37** `#/etkinlik/104` (`164,99 TL`), `#/etkinlik/105` (`kalan: 3`), `#/etkinlik/106` (`Tükendi`), `#/etkinlik/102` (`275,00 TL`) ve geçersiz `#/etkinlik/999`, `#/etkinlik/abc` rotaları incelendi.
  - **00:37** Bilet türü seçiminin (`Tam` / `Öğrenci`) `<div class="chip">` ile yapıldığı, `<input>` veya `<button>` olmadığı fark edildi.
  - **00:38** `#adet` alanına `0`, `-2`, `7`, `1.5`, `2.9`, `""`, `"abc"` değerleri girildi. `7` girildiğinde `"Bir siparişte en fazla 6 bilet alınabilir."` uyarısı çıktı; ancak `0`, `-2`, `1.5`, `""` girildiğinde hata vermeden `#/odeme` sayfasına geçti!
  - **00:38** `#/odeme` sayfasında `PERDE50` kampanya kodu test edildi: `290,00 TL` toplamda reddedildi (`422`), tam `300,00 TL` toplamda (`107 Tam × 2`) `50,00 TL` indirim uygulandı (`250,00 TL`). Küçük harf/boşluklu `"perde50"` ve `" PERDE50 "` kabul edildi. Kupon uygulandıktan sonra geri dönüp adet `1`'e düşürülünce kupon temizlendi. Ancak `#/odeme` üzerinde F5/yenileme yapıldığında ekran `undefined` / `NaN TL` gösterdi (`kanitlar/09_odeme_yenileme.png`).

- **Charter 3 (00:39 – 00:40) — Sipariş Formu Doğrulama, Satın Alma Akışı, Çift Tıklama ve Hata Durumları**
  - **00:39** Negatif (`-2`) ve boş (`""`) adetlerle `#/odeme` üzerinden sipariş gönderme denendi. `""` gönderiminde `adet: null` ile `201 Created` (`ZF2A2H`, `adet: 0, toplam: 0`) oluştu; `-2` ile doğrudan UI'dan `-2 × Tam / -354,98 TL` siparişi (`4LEHEF`) oluşturuldu!
  - **00:39–00:40** `"Siparişi tamamla"` düğmesine 50 ms arayla çift tıklandı: iki ayrı `201 Created` yanıtı (`S547VB` ve `SR2ZR6`) ve çift koltuk düşümü oluştu.
  - **00:40** Ad Soyad, e-posta ve telefon formatları denendi. `0555-000-00-03` telefon girişinde sunucu `500` hatası verdi ve yığın izini (stack trace) kullanıcı arayüzünde gösterdi (`kanitlar/12_telefon_tire_500_stacktrace.png`).

- **Charter 4 (00:40 – 00:42) — "Biletlerim", E-posta Sorgusu, 24 Saat İptal Kuralı ve Koltuk İadesi**
  - **00:41** 24 saatten kısa süre kalan `101` (~9 saat sonra) ve `102` (~22 saat sonra) ile 24 saatten uzun süre kalan `103` (3 gün sonra) etkinliklerine sipariş verildi (`83BTE5`, `DDJDYY`, `VHAZ7H`).
  - **00:41–00:42** `#/biletlerim` ekranında büyük/küçük harf duyarsız e-posta araması (`QA.ZAMAN@EXAMPLE.COM`) çalıştı; ancak tutar sütununda `465 TL`, `287,5 TL`, `162,4 TL` gibi biçimlendirme hataları görüldü.
  - **00:42** `101` (`83BTE5`) ve `102` (`DDJDYY`) siparişlerinin yanında `"İptal et"` düğmesi aktif göründü ve onaylandığında her ikisi de `200 OK` ile iptal edildi (`kanitlar/17_24saat_kurali_iptal_hatasi.png`). `105` etkinliğinin son 3 koltuğu alınıp `"Tükendi"` durumuna düşüldükten sonra iptal edilince tekrar `Kalan: 3 koltuk` olarak satışa açıldığı doğrulandı.

- **Charter 5 (00:42 – 00:44) — Doğrudan HTTP API, Kötü Niyetli Girdiler, Yuvarlama ve Eşzamanlılık (Race Condition)**
  - **00:42–00:43** `GET /api/etkinlikler`, `GET /api/siparisler`, `GET /api/kampanya` ve `POST /api/siparisler` uç noktalarına bozuk JSON, kurcalanmış fiyat (`toplam: 1`), `kvkk: false`, tükenmiş etkinlik (`106`), stok üstü adet (`105` için `4`), negatif/sıfır/ondalıklı/6 üstü adet, XSS yükleri ve eşzamanlı 5 istek gönderildi.
  - **00:43** Stok kontrolü ve eşzamanlılık (`105` kalan `3` koltuk için aynı anda 5 adet `adet: 2` isteği) başarılı çalıştı: 1 istek `201`, 4 istek `409` döndü; eksi stok oluşmadı. Fiyat kurcalaması (`toplam: 1`) sunucu tarafından yok sayıldı.
  - **00:43–00:44** Ancak `POST /api/siparisler` `adet: -2` ile kalan koltuğu `78`den `80`'e çıkardı! Ayrıca `104 Öğrenci × 6` siparişinde arka uç `toplam: 866.9520000000001` döndürürken ön yüz `866,94 TL` gösteriyordu; `#/biletlerim` ise `866,9520000000001 TL` bastı (`kanitlar/20_biletlerim_3_ondalik_tutar.png`).

- **Charter 6 (00:44 – 00:47) — Erişilebilirlik (WCAG 2.1 AA), Klavye Kullanımı, Mobil Uyumluluk ve Edge Doğrulaması**
  - **00:44–00:45** Chrome masaüstünde tüm ekranlarda renk kontrastı, başlık hiyerarşisi (`H1`→`H2`), etiketler, AXTree, `Tab` gezintisi ve `<dialog>` Escape davranışı test edildi. `#turSecimi` içindeki `Tam`/`Öğrenci` seçicisinin klavyeyle hiç odaklanamadığı doğrulandı.
  - **00:45** `390×844` ve `360×740` mobil genişliklerde 4 ana akış kontrol edildi; yatay taşma (`scrollWidth > innerWidth`) görülmedi, `"Biletlerim"` tablosu mobilde kart düzenine geçti (`kanitlar/21_mobil_biletlerim.png`).
  - **00:45** Microsoft Edge `157.0.4341.46` üzerinde uçtan uca `PERDE50` kuponlu sipariş ve iptal akışı konsol hatası olmadan doğrulandı (`K84BH2`).

### Kullanılan Sentetik Test Verileri

- **E-posta adresleri:** `qa.zaman@example.com`, `QA.ZAMAN@EXAMPLE.COM`, `qa.mehmet@example.com`, `qa.ayse@example.com`, `qa.neg@example.com`, `qa.negui@example.com`, `qa.v@example.com`, `qa.v+tag@example.com`, `qa.err@example.com`, `qa.105@example.com`, `qa.api@example.com`, `qa.roundui@example.com`, `qa.bin2@example.com`, `qa.mobil@example.com`, `qa.edge@example.com`, `qa.kupon@example.com`, `qa.unutan@example.com`, `qa.xss+<img/src=x/onerror=alert(1)>@example.com`
- **Ad Soyad örnekleri:** `Zeynep Kaya`, `Mehmet Şahin`, `Ayşe Çağlar`, `Ayşe-Gül Öztürk`, `M. Kemal Yılmaz`, `İbrahim Çınar`, `İpek Âşık`, `O'Brien Ali`, `Şükrü Öğütçü`, `Ali`, `Can Demir`
- **Telefon örnekleri:** `0555 000 00 00`, `05550000003`, `+90 555 000 00 03`, `+905550000003`, `555 000 00 03`, `0212 000 00 03`, `0555-000-00-03`, `(0555) 000 00 20`

---

## 2. Hata Listesi

### BUG-01 — Etkinliğe 24 saatten az kala sipariş iptali engellenmiyor
- **Önem Derecesi:** Kritik
- **Tekrar Üretme Adımları:**
  1. `http://127.0.0.1:4112/#/etkinlik/101` (`Boğaziçi Caz Gecesi` — test zamanı `17 Kasım 2026 00:41` iken etkinlik `17 Kasım 2026 10:00`, yani ~9 saat 20 dakika sonra) veya `#/etkinlik/102` (~21 saat 50 dakika sonra) sayfasına gidin.
  2. Geçerli bilgilerle 1 adet sipariş oluşturun (ör. PNR `83BTE5` ve `DDJDYY`).
  3. `#/biletlerim` sayfasına gidip sipariş verdiğiniz e-posta adresiyle (`qa.zaman@example.com`) sorgulayın.
  4. Etkinliğe 24 saatten az kalmış siparişin satırındaki `"İptal et"` düğmesine tıklayın ve açılan pencerede `"Evet, iptal et"` seçeneğini onaylayın (veya doğrudan `POST /api/siparisler/83BTE5/iptal` isteği gönderin).
- **Beklenen Sonuç:** Etkinliğe 24 saat veya daha az kaldığı için `"İptal et"` seçeneği sunulmamalı (veya devre dışı/bilgilendirici olmalı) ve arka uç `POST /api/siparisler/{pnr}/iptal` isteğini reddetmelidir.
- **Gerçekleşen Sonuç:** Hem ~9 saat kalan `101` hem de ~22 saat kalan `102` siparişleri için `"İptal et"` düğmesi aktif görünmekte ve onaylandığında `200 OK` yanıtıyla sipariş `"İptal edildi"` durumuna geçip koltuklar yeniden satışa açılmaktadır.
- **Kanıt:** `kanitlar/14_biletlerim_listesi_24saat.png`, `kanitlar/17_24saat_kurali_iptal_hatasi.png`; ağ yanıtı: `POST /api/siparisler/83BTE5/iptal -> 200 {"pnr":"83BTE5","etkinlikId":101,"etkinlikTarih":"2026-11-17T07:00:00.000Z",...,"durum":"iptal"}`

---

### BUG-02 — Negatif, sıfır, ondalıklı, boş ve 6 üzeri bilet adedi kabul ediliyor; negatif adet stok şişiriyor
- **Önem Derecesi:** Kritik
- **Tekrar Üretme Adımları:**
  1. **Arayüz üzerinden (negatif/boş adet):** `http://127.0.0.1:4112/#/etkinlik/104` sayfasını açın, `Bilet adedi` (`#adet`) kutusuna `-2` (veya `0`, `1.5`, boş `""`) yazın ve `"Devam et"` düğmesine tıklayın.
  2. `#/odeme` sayfasında iletişim bilgilerini doldurup KVKK kutusunu işaretleyin ve `"Siparişi tamamla"` düğmesine tıklayın.
  3. **API üzerinden:** `POST /api/siparisler` adresine `{"etkinlikId":108,"tur":"tam","adet":-2,"kampanyaKodu":"","adSoyad":"Negatif Test","eposta":"qa.neg2@example.com","telefon":"0555 000 00 21","kvkk":true}` (veya `"adet": 0`, `"adet": 10`) gövdesiyle istek gönderin.
- **Beklenen Sonuç:** Ürün notuna göre bir siparişte en az `1`, en fazla `6` tam sayı bilet olabilmelidir. `1`'den küçük, ondalıklı, boş veya `6`'dan büyük değerlerde hem ön yüz `#/odeme` adımına geçişi engellemeli hem de arka uç `400/422` doğrulama hatası döndürmelidir.
- **Gerçekleşen Sonuç:** Ön yüz `0`, `-2`, `1.5`, `""` değerlerinde hiçbir hata vermeden `#/odeme` sayfasına geçmekte; `-2` için `"-2 × Tam bilet / -354,98 TL"` göstermekte ve formu gönderince `#/onay/4LEHEF` siparişini (`adet: -2, toplam: -354.98`) oluşturmaktadır. Boş bırakıldığında `adet: null` gönderilip `adet: 0, toplam: 0` ile `201` sipariş (`ZF2A2H`) oluşmaktadır. Doğrudan API'de `adet: -2` gönderildiğinde `108` etkinliğinin kalan koltuk sayısı `78`'den `80`'e yükselmiş (`toplam: -145`); `adet: 7` ve `adet: 10` istekleri de `201` ile kabul edilmiştir.
- **Kanıt:** `kanitlar/10_negatif_adet_odeme.png`; API yanıtı: `POST /api/siparisler` (`adet: -2`) `-> 201 {"pnr":"7T3GNR","adet":-2,"toplam":-145,"durum":"aktif"}` ve öncesinde `kalan: 78` iken sonrasında `GET /api/etkinlikler/108 -> kalan: 80`.

---

### BUG-03 — Tire veya parantez içeren telefon numarası sunucuda 500 hatası ve yığın izi (stack trace) sızıntısına yol açıyor
- **Önem Derecesi:** Kritik
- **Tekrar Üretme Adımları:**
  1. Herhangi bir etkinlik için `#/odeme` adımına ilerleyin (ör. `#/etkinlik/108` -> `"Devam et"`).
  2. `Ad Soyad` ve `E-posta` alanlarını geçerli doldurun, `Cep telefonu` alanına `0555-000-00-03` yazın, onay kutusunu işaretleyin ve `"Siparişi tamamla"` düğmesine tıklayın (veya API'ye `"telefon": "(0555) 000 00 20"` gönderin).
- **Beklenen Sonuç:** Tire veya parantez gibi yaygın ayraçlar ya temizlenerek kabul edilmeli ya da kullanıcı dostu bir doğrulama mesajıyla (`400`) reddedilmelidir; sunucu çökmemeli ve iç dosya yolları/yığın izi kullanıcıya gösterilmemelidir.
- **Gerçekleşen Sonuç:** İstemci doğrulamasından geçen `0555-000-00-03` değeri `POST /api/siparisler` isteğinde sunucuyu `SyntaxError: Cannot convert 0555-000-00-03 to a BigInt` hatasıyla HTTP `500`'e düşürmektedir. Sunucu JSON yanıtının `"detay"` alanında tam Node.js yığın izi ve sunucu dosya yolu dönmekte, arayüz de bu teknik ayrıntıyı doğrudan kullanıcıya göstermektedir.
- **Kanıt:** `kanitlar/12_telefon_tire_500_stacktrace.png`; HTTP `500` yanıtı: `{"hata":"Beklenmeyen bir hata oluştu: Cannot convert 0555-000-00-03 to a BigInt","detay":"SyntaxError: Cannot convert 0555-000-00-03 to a BigInt\n    at BigInt (<anonymous>)\n    at telefonNormalEt (.../server.js:187:10)..."}`

---

### BUG-04 — "Siparişi tamamla" düğmesine çift tıklamada mükerrer sipariş ve çift koltuk düşümü oluşuyor
- **Önem Derecesi:** Yüksek
- **Tekrar Üretme Adımları:**
  1. `#/etkinlik/108` detayından `#/odeme` adımına geçin.
  2. İletişim bilgilerini geçerli doldurun ve KVKK onay kutusunu işaretleyin.
  3. `"Siparişi tamamla"` düğmesine arka arkaya hızlıca iki kez tıklayın (ör. 50 ms arayla; ağ isteği sürerken).
- **Beklenen Sonuç:** İlk tıklamada `"Siparişi tamamla"` düğmesi devre dışı (`disabled`) bırakılmalı ve ikinci gönderim engellenerek yalnızca tek bir sipariş oluşturulmalıdır.
- **Gerçekleşen Sonuç:** `"Siparişiniz işleniyor, lütfen bekleyin…"` mesajı görünmesine rağmen düğme aktif kalmakta; iki ayrı `POST /api/siparisler` isteği gönderilip ikisi de `201 Created` (`S547VB` ve `SR2ZR6`) döndürmektedir. Kullanıcı ekranda yalnızca `SR2ZR6` PNR'ını görürken arkada 2 ayrı sipariş açılıp 2 katı koltuk düşülmektedir.
- **Kanıt:** Ağ kaydı (`POST /api/siparisler` 55 ms arayla iki `201` yanıtı: `{"pnr":"S547VB",...}` ve `{"pnr":"SR2ZR6",...}`).

---

### BUG-05 — Türkçe büyük/küçük harf aramasında `İ/i` ve `I/ı` karakterleri eşleşmiyor
- **Önem Derecesi:** Yüksek
- **Tekrar Üretme Adımları:**
  1. `http://127.0.0.1:4112/#/` ana sayfasını açın.
  2. `Ara` (`#ara`) kutusuna sırasıyla `izmir`, `İZMİR`, `istanbul`, `ESKİŞEHİR`, `BOĞAZİÇİ` veya `KISA` yazın.
- **Beklenen Sonuç:** Türkçe büyük/küçük harf kurallarına uygun şekilde (`i↔İ`, `ı↔I`) eşleşen etkinlikler listelenmelidir (ör. `izmir` ve `İZMİR` aramalarında `İzmir Kordon Akustik` ile `Ödüllü Kısa Filmler Gösterimi`; `istanbul` aramasında 3 İstanbul etkinliği).
- **Gerçekleşen Sonuç:** `izmir`, `İZMİR`, `IZMIR`, `istanbul`, `ISTANBUL`, `ıstanbul`, `ESKİŞEHİR`, `BOĞAZİÇİ` ve `KISA` aramalarının tümü `0` sonuç döndürmekte ve `"Aramanızla eşleşen etkinlik bulunamadı."` mesajı göstermektedir (`İ` harfi yalnızca büyük harfle `"İSTANBUL"` yazıldığında eşleşirken, `"İzmir"` kelimesini ne `"izmir"` ne de `"İZMİR"` bulabilmektedir).
- **Kanıt:** `kanitlar/19_turkce_arama_izmir.png`; aynı oturumda `"İSTANBUL"` -> `3` sonuç, `"istanbul"` -> `0` sonuç, `"izmir"` -> `0` sonuç, `"İZMİR"` -> `0` sonuç.

---

### BUG-06 — Etkinlik detayında "Bilet türü" (Tam / Öğrenci) seçimi klavye ve ekran okuyucu ile kullanılamıyor (WCAG 2.1 AA)
- **Önem Derecesi:** Yüksek
- **Tekrar Üretme Adımları:**
  1. `http://127.0.0.1:4112/#/etkinlik/104` sayfasını açın.
  2. Fare kullanmadan yalnızca klavyede `Tab` tuşuna basarak sayfa içi öğeler arasında ilerleyin.
- **Beklenen Sonuç:** WCAG 2.1 AA (2.1.1 Klavye ve 4.1.2 Ad, Rol, Değer) gereği `Tam` ve `Öğrenci` seçenekleri klavyeyle odaklanabilir olmalı (`radio` veya `button` semantiği ve seçili durum bilgisiyle), `Enter`/`Space` veya yön tuşlarıyla değiştirilebilmelidir.
- **Gerçekleşen Sonuç:** `#turSecimi` içindeki `Tam` ve `Öğrenci` kartları `tabindex`, `role` ve klavye dinleyicisi olmayan düz `<div class="chip">` öğeleridir. `Tab` gezintisi `← Tüm etkinlikler` bağlantısından doğrudan `Bilet adedi` (`#adet`) kutusuna atlamakta; klavye ve ekran okuyucu kullanıcıları `%20` indirimli `Öğrenci` biletini seçememektedir.
- **Kanıt:** `kanitlar/04_etkinlik_104_detay.png`; Chrome `Tab` gezintisi ve `Accessibility.getFullAXTree` çıktısı (`StaticText` rolünde kapsayıcı, etkileşimli rol yok).

---

### BUG-07 — `#/odeme` sayfası yenilendiğinde veya doğrudan açıldığında "undefined / NaN TL" gösteriliyor
- **Önem Derecesi:** Orta
- **Tekrar Üretme Adımları:**
  1. Herhangi bir etkinlikten `"Devam et"` diyerek `http://127.0.0.1:4112/#/odeme` sayfasına geçin.
  2. Tarayıcıda sayfayı yenileyin (`F5` / `location.reload()`) veya yeni sekmede doğrudan `http://127.0.0.1:4112/#/odeme` adresini açın.
- **Beklenen Sonuç:** Seçili sipariş taslağı bellekte yoksa kullanıcı güvenli biçimde etkinlik listesine (`#/`) yönlendirilmeli veya `"Seçili sipariş bulunamadı"` mesajı gösterilmelidir.
- **Gerçekleşen Sonuç:** Sipariş özeti kutusunda etkinlik adı `undefined`, bilet satırı `undefined × Tam bilet (NaN TL)  NaN TL`, hizmet bedeli `Hizmet bedeli (undefined × 12,50 TL)  NaN TL` ve toplam `NaN TL` olarak basılmakta; sağ taraftaki sipariş formu ise açık kalmaktadır.
- **Kanıt:** `kanitlar/09_odeme_yenileme.png`

---

### BUG-08 — Öğrenci indirimi yuvarlaması ön yüz ile arka uç arasında 1 kuruş fark ve kayan nokta taşması üretiyor
- **Önem Derecesi:** Orta
- **Tekrar Üretme Adımları:**
  1. `http://127.0.0.1:4112/#/etkinlik/104` (`164,99 TL`) sayfasını açın.
  2. Bilet türü olarak `Öğrenci` (`131,99 TL (%20 indirimli)`) ve adet olarak `6` seçin.
  3. Detay ve `#/odeme` sayfasındaki toplamı not edip siparişi tamamlayın; ardından `#/onay/{pnr}` ve `#/biletlerim` sayfalarındaki tutarları karşılaştırın.
- **Beklenen Sonuç:** Ön yüz ile arka uç aynı yuvarlama kuralını (2 ondalık basamağa yuvarlanmış kuruş hesabı) kullanmalı ve kullanıcıya gösterilen tüm ekranlarda aynı tutar (`866,94 TL` veya `866,95 TL`) görünmelidir.
- **Gerçekleşen Sonuç:** Ön yüz birim fiyatı `131,99 TL`'ye yuvarlayıp `6 × 131,99 + 75,00 = 866,94 TL` göstermektedir. Arka uç ise `164.99 * 0.8 * 6 + 75` hesabını yuvarlamadan yaparak JSON'da `"toplam": 866.9520000000001` döndürmekte; bunun sonucunda `#/onay` ekranında `866,95 TL` (1 kuruş fazla), `#/biletlerim` tablosunda ise `866,9520000000001 TL` yazmaktadır.
- **Kanıt:** `kanitlar/20_biletlerim_3_ondalik_tutar.png`; API yanıtı: `POST /api/siparisler -> 201 {"pnr":"8Y775Y",...,"toplam":866.9520000000001}`

---

### BUG-09 — "Biletlerim" tablosunda tutarlar Türkçe iki ondalık ve binlik ayraç biçiminde gösterilmiyor
- **Önem Derecesi:** Orta
- **Tekrar Üretme Adımları:**
  1. Toplam tutarı tam sayı (`465,00 TL`), tek sıfırlı ondalık (`287,50 TL`), bin üzeri (`1.675,00 TL`) veya 3+ ondalıklı (`866,95 TL`) olacak şekilde siparişler oluşturun.
  2. `#/biletlerim` sayfasından ilgili e-postayla siparişleri listeleyin ve `Tutar` sütununu inceleyin.
- **Beklenen Sonuç:** Ürün notundaki beklentiye uygun olarak tüm tutarlar iki ondalık basamak ve Türkçe binlik ayraçla (`465,00 TL`, `287,50 TL`, `1.675,00 TL`, `866,95 TL`) gösterilmelidir.
- **Gerçekleşen Sonuç:** `Tutar` sütunu değerleri `465 TL`, `287,5 TL`, `162,4 TL`, `1675 TL` ve `866,9520000000001 TL` şeklinde göstermektedir (diğer sayfalarda tutar biçimlendirmesi doğruyken yalnızca `#/biletlerim` listesinde bozuktur).
- **Kanıt:** `kanitlar/14_biletlerim_listesi_24saat.png`, `kanitlar/18_biletlerim_tutar_bicim_hatasi.png`, `kanitlar/20_biletlerim_3_ondalik_tutar.png`

---

## 3. Sorular ve Gözlemler

Aşağıdaki noktalar doğrudan hata olarak sınıflandırılmamış olup Perşembe sürüm kararı öncesi ürün sahibinin netleştirmesi gereken ürün ve tasarım sorularıdır:

1. **Aydınlatma metni içeriği bulunmuyor:** `#/odeme` sayfasında *"Aydınlatma metnini okudum ve kişisel verilerimin sipariş için işlenmesini kabul ediyorum."* onay kutusu zorunlu tutuluyor, ancak kullanıcının tıklayıp okuyabileceği bir aydınlatma metni bağlantısı veya penceresi yer almıyor. İlk sürüme metin/modal eklenecek mi?
2. **Kampanya kodu yazılıp "Uygula"ya basılmadan sipariş verilmesi:** Kullanıcı `#/odeme` ekranında `Kampanya kodu` alanına `PERDE50` yazıp `"Uygula"` düğmesine basmadan doğrudan `"Siparişi tamamla"`ya tıklarsa, sipariş indirimsiz (`300,00 TL`) oluşturuluyor ve herhangi bir uyarı verilmiyor. Bu durum kabul edilebilir mi, yoksa gönderim öncesi uygulanmamış kod için uyarı gösterilmeli mi?
3. **Ad Soyad ve Cep Telefonu kabul kuralları ile hata mesajı uyumu:**
   - Ad Soyad doğrulaması hata mesajında *"en az 3 harften oluşmalı ve yalnızca harf içermelidir"* diyor; pratikte nokta/tire/kesme işareti (`M. Kemal Yılmaz`, `Ayşe-Gül Öztürk`, `O'Brien Ali`) ve tek kelimelik 3 harfli adlar (`"Ali"`) kabul ediliyor. İki kelime (ad ve soyad) zorunluluğu isteniyor mu?
   - Cep telefonu alanı sabit hatları (`0212 000 00 03`) ve başında `0` olmayan 10 haneli numaraları (`555 000 00 03`) kabul ediyor; yalnızca `05XX` cep telefonu numaraları mı hedefleniyor?
4. **Kalan koltuk < 6 iken `#adet` üst sınırı ve ipucu metni:** `Şebnem'in Düğünü` (`105`) etkinliğinde kalan koltuk `3` olmasına rağmen input `max="6"` ve ipucu `"Bir siparişte en fazla 6 bilet."` olarak görünüyor (kullanıcı `4` yazıp `"Devam et"`e basınca hata uyarısı çıkıyor). İpucunun ve `max` değerinin kalan koltuğa göre dinamik daraltılması tercih edilir mi?
5. **PNR ile kimlik doğrulamasız sipariş görüntüleme ve iptal:** Üyelik bulunmayan v0.9 sürümünde `/api/siparisler/{pnr}` yalnızca 6 haneli PNR kodu ile alıcının ad soyad, e-posta ve telefon bilgisini döndürüyor; `POST /api/siparisler/{pnr}/iptal` ise e-posta doğrulaması olmadan siparişi iptal edebiliyor. Üyelik olmasa bile en azından PNR sorgu/iptalinde e-posta eşleştirmesi veya hız sınırlaması (rate limiting) isteniyor mu?
6. **Etkinlik verisi ve geçmiş saat davranışı:** `102` numaralı *"İstanbul Gençlik Senfonisi: Mevsimler"* etkinliğinin açıklamasında *"matine konserinde"* ifadesi geçerken saati `22:30` olarak tanımlanmış; demo verisinin gözden geçirilmesi faydalı olur. Ayrıca başlangıç saati geçmiş etkinliklerin listeden otomatik düşüp düşmeyeceği netleştirilmeli.
7. **Ek erişilebilirlik ve gezinme gözlemleri:**
   - Tükenen etkinlikteki pasif `"Tükendi"` düğmesinin kontrast oranı `1.95:1` ölçüldü (WCAG 1.4.3'te pasif öğeler muaf olsa da görsel okunabilirlik için ton koyulaştırılabilir).
   - `#/odeme` form hataları tek bir `role="alert"` listesinde gösteriliyor; alanlara `aria-invalid` ve `aria-describedby` eklenmesi ekran okuyucu deneyimini güçlendirir. Üst menüdeki aktif bağlantıya `aria-current="page"` eklenebilir.
   - `#/odeme` sayfasındaki `"← Etkinliklere dön"` bağlantısı son etkinlik detayına değil ana sayfaya (`#/`) gidiyor; detay sayfasına dönüş bağlantısı da kullanıcıya kolaylık sağlayabilir.
   - Arama kutusunda kategori adına göre (ör. `"tiyatro"`) arama sonuç getirmiyor (ürün notunda ad/şehir/mekân belirtildiği için kapsam dışı bırakılmış görünüyor).

---

## 4. Debrief

### Neleri Kapsadım?
- **Ana sayfa ve keşif akışları:** Etkinlik listeleme, ad/şehir/mekân araması, Türkçe karakter duyarlılığı, şehir filtresi, tarih/fiyat/ad sıralamaları, boş sonuç durumu, geri dönüşte filtre korunması.
- **Detay, fiyatlandırma ve kampanya:** Tam/Öğrenci indirimi (`%20`), bilet başı `12,50 TL` hizmet bedeli, `1.000+ TL` biçimlendirmesi, `PERDE50` eşik sınırları (`290`, `299.99`, `300.00`), geçersiz/boş/negatif/ondalıklı adet sınırları, tükenmiş (`0`) ve az koltuklu (`3`) etkinlikler.
- **Sipariş, doğrulama, "Biletlerim" ve iptal yaşam döngüsü:** Form doğrulamaları, çift tıklama, sayfa yenileme, PNR onay ekranı, büyük/küçük harf duyarsız e-posta sorgusu, 24 saat kuralı (`~9 saat`, `~22 saat`, `3 gün` testleri), iptal diyalogu (`Vazgeç`, `Escape`, `Evet, iptal et`), çift iptal denemesi ve tükenen etkinliğin iptalle yeniden açılması.
- **API, güvenlik ve eşzamanlılık:** Tüm keşfedilen `/api/*` uç noktalarında negatif/aşırı/bozuk JSON testleri, fiyat manipülasyonu denemesi, XSS girişimi (`<img ...>`, `<script>`), `5` eşzamanlı stok yarışı isteği.
- **Kalite ve platform beklentileri:** Chrome 157 ve Edge 157 doğrulaması, masaüstü (`1280×800`) ve mobil (`390×844`, `360×740`) görünüm/taşma kontrolleri, WCAG 2.1 AA kontrast, başlık yapısı, AXTree ve klavye (`Tab` / `Escape`) testleri.

### Neleri Kapsayamadım?
- **Sunucu yeniden başlatma ve zaman ilerlemesi:** Demo bellek sıfırlaması ve bir etkinliğin başlangıç saati geçtikten sonraki (ör. `10:00` sonrası) canlı durum geçişi test süresi içinde gözlenemedi.
- **Gerçek ekran okuyucu ve fiziksel mobil cihaz:** Erişilebilirlik Chrome Accessibility Tree ve klavye olaylarıyla incelendi; NVDA/JAWS seslendirmesi ve gerçek dokunmatik cihaz (mobil Edge/Chrome) üzerinde manuel test yapılmadı.
- **Yüksek hacimli yük/stres testi:** 5 eşzamanlı istekte yarış koşulu sınandı; yüzlerce paralel kullanıcı altında bellek/performans profili çıkarılmadı.

### En Büyük Riskler
1. **İş kuralı ve gelir/stok bütünlüğü riski (`BUG-01`, `BUG-02`, `BUG-04`):** Etkinliğe saatler kala iptal yapılabilmesi gişe planlamasını bozar; negatif/sıfır/limit üstü bilet kabulü hem stok sayısını yapay artırabilir hem de geçersiz/negatif tutarlı siparişler üretir; çift tıklamayla çift rezervasyon oluşur.
2. **Kararlılık ve bilgi sızıntısı riski (`BUG-03`):** Türkiye'de yaygın kullanılan tireli telefon formatı (`0555-000-00-03`) sunucuda `500` çökmesine neden olup sunucu dosya yolları dahil yığın izini son kullanıcıya açıyor.
3. **Kullanılabilirlik ve erişilebilirlik riski (`BUG-05`, `BUG-06`):** Türkçe kullanıcıların `"izmir"` veya `"istanbul"` yazarak etkinlik bulamaması ana keşif deneyimini sekteye uğratıyor; klavye ve ekran okuyucu kullanıcılarının `%20` öğrenci indirimini seçememesi doğrudan WCAG 2.1 AA hedefini bozuyor.

### Sürüm Önerisi
- **Öneri: Şimdilik Sürüm Çıkışı Önerilmez (No-Go).**
- Perşembe günkü sürümden önce **tüm Kritik (`BUG-01`, `BUG-02`, `BUG-03`) ve Yüksek (`BUG-04`, `BUG-05`, `BUG-06`) hataların** kapatılması gerekir. Orta önemdeki `BUG-07`, `BUG-08` ve `BUG-09` da kısa sürede çözülebilir yapıdadır ve bu düzeltmelerin ardından hedefli bir regresyon testi sonrası yayına alınması önerilir.
