# Keşif Testi Raporu — Perdeaçık Bilet (v0.9 demo)

**Test edilen ortam:** `http://127.0.0.1:4103` (kara kutu, bellekte çalışan demo)  
**Tarih / saat:** 17 Kasım 2026, `00:21 – 00:34 (+03:00)`  
**Referans doküman:** `urun-notu.md` (Selin Aksoy, Ürün Sahibi)  
**Tarayıcılar ve araçlar:** Google Chrome (`157.0.8103.52` headless CDP, masaüstü `1280×800` ve mobil `375×812`), Microsoft Edge (CDP, masaüstü `1280×800`), `httpx` / `curl` (doğrudan HTTP/API ve eşzamanlılık testleri)

---

## 1. Oturum Notları

Oturum, 5 keşif charter'ı etrafında yapılandırıldı. Kaynak koda erişim olmadan, gerçek bir kullanıcı ve sınır/kötüye kullanım senaryoları deneyen bir test uzmanı perspektifiyle ("tur" yaklaşımıyla) ilerledi.

### Charter'lar ve Zaman Damgalı Notlar

1. **Charter 1 — Etkinlik Keşfi, Arama, Filtreleme, Sıralama ve Mutlu Yol Satın Alma** (`00:21 – 00:24`)
   - **Tur / fikirler:** Ana sayfayı yükleme, 9 etkinliğin listelenmesi, `Tarihe göre` / `Fiyata göre (artan)` / `Ada göre (A–Z)` sıralama, şehir filtresi, Türkçe karakter (`İ/i`, `I/ı`, `Ş`, `Ç`, `Ğ`, `Ö`, `Ü`) büyük/küçük harf duyarlılığıyla arama, boşluk ve XSS girdisi denemeleri.
   - **Gözlem:** Sıralama (`Ç`, `İ`, `Ö`, `Ş`, `Ü` Türkçe alfabetik düzeni ve sayısal fiyat sırası) doğru çalışıyor; ancak `Ara` kutusunda `istanbul`, `izmir`, `İZMİR`, `BOĞAZİÇİ`, `NİŞANTAŞI`, `KAVAKLIDERE` sorguları `0` sonuç döndürdü (**HATA-03**).
   - **Kanıtlar:** `kanitlar/01-anasayfa.png`, `kanitlar/02-siralama-ad.png`, `kanitlar/03-arama-istanbul.png`.

2. **Charter 2 — Bilet Seçimi, Fiyatlandırma, `PERDE50` Kampanyası ve Sınır Değerleri** (`00:24 – 00:26`)
   - **Tur / fikirler:** `Tam` / `Öğrenci` (%20 indirim) fiyat hesabı, bilet başı `12,50 TL` hizmet bedeli, `PERDE50` için `300,00 TL` eşik sınırları (`290,00 TL` vs tam `300,00 TL`, hizmet bedeli olmadan `300` altı ama hizmet bedeliyle `>= 300` senaryoları), `164,99 TL × %80 = 131,992` küsurat yuvarlaması, binlik ayraç (`1.150,00 TL`), adet sınırları (`0`, `-1`, `2.5`, `""`, `"abc"`, `6`, `7`, kalan stok `3` iken `4`), `#/odeme` üzerinde F5 yenileme.
   - **Gözlem:** `PERDE50` eşiği (`290,00 TL` reddedildi, `300,00 TL` ve `324,80 TL` kabul edildi), küçük harf (`perde50`) ve boşluk (`  PERDE50  `) kırpma doğru çalıştı. Ancak `adet = 0`, `-1`, `2.5`, `""`, `"abc"` değerleriyle `#/odeme` sayfasına geçilebildi (**HATA-01**); `#/odeme` yenilendiğinde `undefined / NaN TL` göründü (**HATA-08**).
   - **Kanıtlar:** `kanitlar/04-etkinlik-detay-101.png`, `kanitlar/05-etkinlik-tukendi-106.png`, `kanitlar/06-odeme-formu.png`, `kanitlar/07-perde50-300tl-sinir.png`, `kanitlar/08-binlik-format-1150tl.png`, `kanitlar/09-negatif-adet-odeme.png`, `kanitlar/10-odeme-yenileme-nan.png`.

3. **Charter 3 — Sipariş Tamamlama, Form Doğrulamaları, Biletlerim ve 24 Saat İptal Kuralı** (`00:26 – 00:28`)
   - **Tur / fikirler:** Ad soyad (Türkçe karakter, tire, kesme işareti, 2 harf, rakam, XSS), e-posta, cep telefonu (sabit hat, +90, boşluksuz), KVKK onayı testleri; `adet = -1` ile sipariş tamamlama denemesi; mutlu yol PNR onayı (`N4SVK8`); `< 24 saat` kalan etkinlikler (`102` — ~22 saat, `101` — ~9,5 saat) ile `> 24 saat` kalan etkinlik (`103`) için Biletlerim listeleme ve iptal akışı, modal `Vazgeç` / `Evet, iptal et` ve iptal sonrası stok artışı.
   - **Gözlem:** `-1 × Tam` siparişi (`E5NV7U`, `-162,40 TL`) onaylandı ve `101` numaralı etkinliğin kalan koltuğu `38 -> 40` oldu (**HATA-01**). Ayrıca etkinliğe 24 saatten az kalmasına rağmen `DJ36ZD` (~22 saat kala) arayüzden iptal edildi (**HATA-02**); Biletlerim tablosunda tutarlar `287,5 TL`, `327 TL` biçiminde göründü (**HATA-06**).
   - **Kanıtlar:** `kanitlar/11-siparis-onayi-pnr.png`, `kanitlar/11b-negatif-siparis-onayi.png`, `kanitlar/12-biletlerim-liste.png`, `kanitlar/13-iptal-dialog.png`, `kanitlar/14-iptal-edildi.png`, `kanitlar/15-biletlerim-format-ve-24saat.png`.

4. **Charter 4 — "Kötü Niyetli" API, Güvenlik, Yuvarlama ve Eşzamanlılık Turları** (`00:28 – 00:30`)
   - **Tur / fikirler:** Doğrudan `POST /api/siparisler` ile `adet` sınırlarını (`0`, `-3`, `1.5`, `7`), tükenen etkinliğe (`106`) `adet: -1` göndermeyi, istemciden `toplam: 0.01`, `fiyat: 0`, `pnr: "HACKED"` manipülasyonunu, `300 TL` altı `PERDE50` zorlamasını, XSS yüklerini, çift iptali, düşük stoklu (`kalan: 3`) `105` numaralı etkinliğe aynı anda 4 paralel `adet: 2` yarış isteğini ve arayüzde `"Siparişi tamamla"` butonuna çift tıklamayı denedik.
   - **Gözlem:** Sunucu fiyat manipülasyonunu (`UUJM25` -> `72.5` TL), çift iptali (`409`), ve paralel stok yarışını (`1×201`, `3×409`) doğru engelledi. Ancak `adet = 0, -3, 7` ve tükenen `106`'ya `adet = -1` kabul edildi (**HATA-01**), `104` `3×Öğrenci + PERDE50` için `383.47600000000006` döndü (**HATA-06, HATA-07**), çift tıklama 2 sipariş açtı (**HATA-05**), `< 10 saat` kalan `72TNGT` API'den iptal edildi (**HATA-02**), `GET/POST /api/siparisler/:pnr` e-posta doğrulaması istemedi (**HATA-09**).
   - **Kanıtlar:** `kanitlar/16-yuvarlama-onay-tfa5da.png`, `kanitlar/17-biletlerim-yuvarlama-negatif.png`.

5. **Charter 5 — WCAG 2.1 AA Erişilebilirlik, Mobil Duyarlılık ve Çapraz Tarayıcı** (`00:30 – 00:32`)
   - **Tur / fikirler:** Chrome üzerinde tüm sayfalarda kontrast oranı ölçümü, başlık (`h1–h2`) hiyerarşisi, form `label` ve hata `aria-*` bağlantıları, klavye `Tab`/`Escape` akışı ve Chrome Accessibility Tree incelemesi; `375×812` mobil genişlikte yatay taşma kontrolü; Microsoft Edge üzerinde temel uçtan uca akış (filtre, satın alma, iptal) doğrulaması; onay sonrası tarayıcı `Geri` tuşu ve kampanya kodu üzerine yazma testi.
   - **Gözlem:** Kontrast ölçümleri (`lowContrast: []`), mobil `375px` akışı (0 yatay taşma) ve Edge smoke testi (`S7KJUN`) sorunsuz geçti; ancak bilet türü seçimi (`Tam`/`Öğrenci`) klavye ve ekran okuyucuya tamamen kapalı (**HATA-04**), form hatalarında `aria-invalid`/`aria-describedby` yok (**HATA-10**) ve `#/onay` üzerinden `Geri` tuşuna basınca `#/odeme` bozuluyor (**HATA-08**).
   - **Kanıtlar:** `kanitlar/18-mobil-anasayfa.png`, `kanitlar/18b-mobil-detay.png`, `kanitlar/19-mobil-odeme.png`, `kanitlar/19b-mobil-biletlerim.png`, `kanitlar/20-edge-anasayfa.png`.

### Kullanılan Başlıca Sentetik Test Verileri

- E-postalar: `deniz.caglar@example.com`, `negatif.test@example.com`, `sec.test@example.com`, `zaman.test@example.com`, `dblclick.test@example.com`, `cap.test@example.com`, `race.test@example.com`, `edge.smoke@example.com`, `cagri.sahin@example.com`, `ali.oneil@example.com`, `test.space@example.com`, `yok@example.com`
- İsimler ve telefonlar: `Deniz Çağlar`, `Çağrı Şahin-Öz`, `Ali O'Neil`, `Test Kullanıcısı`, `Güvenlik Testi`; `0555 111 22 33`, `0555 000 00 01`, `0212 111 22 33`, `+905550000002`, `5551112233`

---

## 2. Hata Listesi

### HATA-01 — Negatif, sıfır, ondalık ve sınır dışı bilet adediyle (`adet <= 0` veya `adet > 6`) sipariş oluşturulabilmesi
- **Önem derecesi:** Kritik
- **Tekrar üretme adımları:**
  1. **Arayüzden:** `http://127.0.0.1:4103/#/etkinlik/101` (`Boğaziçi Caz Gecesi`, `Kalan: 38 koltuk`) sayfasını açın.
  2. `Bilet adedi` (`#adet`) alanına `-1` (veya `0`, `2.5`, boş) yazın ve `Devam et` butonuna tıklayın.
  3. Açılan `#/odeme` ekranında geçerli iletişim bilgileri (`Test Kullanıcısı`, `negatif.test@example.com`, `0555 000 00 01`, KVKK onaylı) girip `Siparişi tamamla` butonuna tıklayın.
  4. **API'den:** `POST /api/siparisler` uç noktasına `adet: -3`, `adet: 0`, `adet: 7` veya tükenen `106` numaralı etkinlik için `adet: -1` gönderin.
- **Beklenen sonuç:** Hem ön yüz hem arka uç yalnızca `1` ile `min(6, kalan)` arasındaki tam sayıları kabul etmeli; `0`, negatif, ondalık, `> 6` veya tükenen etkinliğe gelen istekleri doğrulama hatasıyla (`400`/`422`) reddetmelidir.
- **Gerçekleşen sonuç:** Ön yüz yalnızca `> 6` ve `> kalan` durumlarını engelledi; `-1` ve `0` ile `#/odeme` sayfasına geçilip `-162,40 TL` tutarlı `E5NV7U` (ve `SP4ES4`) siparişleri `201 Created` ile oluştu ve `101` numaralı etkinliğin kalan koltuğu `38`'den `40`'a yükseldi. Doğrudan API çağrılarında `adet: 0` (`ESZT9B`), `adet: -3` (`MZTSJZ`), `adet: 7` (`VK9VAA`) ve tükenmiş (`kalan: 0`) `106` numaralı etkinlikte `adet: -1` (`6J79HH`, kalanı `1`'e çıkardı) `201 Created` döndü; `adet: 1.5` sessizce `1`'e çevrildi (`BVAUE8`). (Test sonrası `106` stoğu `HM7T9M` ile geri `0` yapıldı.)
- **Kanıt:**
  - `kanitlar/09-negatif-adet-odeme.png`, `kanitlar/11b-negatif-siparis-onayi.png`, `kanitlar/17-biletlerim-yuvarlama-negatif.png`
  - HTTP: `POST http://127.0.0.1:4103/api/siparisler` gövdesi `{"etkinlikId":106,"tur":"tam","adet":-1,...}` -> `201 {"pnr":"6J79HH","adet":-1,"toplam":-108,"durum":"aktif"}`

---

### HATA-02 — Etkinliğe 24 saatten az süre kalmış siparişlerin iptal edilebilmesi
- **Önem derecesi:** Yüksek
- **Tekrar üretme adımları:**
  1. Test saatinde (`17 Kasım 2026 00:27 +03:00`) aynı gün başlayacak iki etkinlik için sipariş oluşturun: `102` (`İstanbul Gençlik Senfonisi: Mevsimler`, `17 Kasım 2026 22:30` — ~22 saat sonra) ve `101` (`Boğaziçi Caz Gecesi`, `17 Kasım 2026 10:00` — ~9,5 saat sonra).
  2. `#/biletlerim` sayfasına gidip ilgili e-postayla (`deniz.caglar@example.com` veya `zaman.test@example.com`) siparişleri listeleyin.
  3. 24 saatten az kalmış siparişin satırındaki `İptal et` butonuna tıklayıp onaylayın (`Evet, iptal et`).
  4. Doğrudan `POST /api/siparisler/72TNGT/iptal` isteğini gönderin.
- **Beklenen sonuç:** `urun-notu.md` gereğince etkinliğe **24 saatten fazla** süre kalmadıysa sipariş iptal edilememeli; arayüzde iptal seçeneği kapalı/açıklamalı olmalı ve arka uç iptal isteğini `422`/`400` ile reddetmelidir.
- **Gerçekleşen sonuç:** Hem ~22 saat kalan `DJ36ZD` / `7KDNEB` hem de ~9,5 saat kalan `72TNGT` siparişlerinde `İptal et` butonu aktif göründü. Arayüzden `DJ36ZD` ve API'den `72TNGT` `200 OK` ile iptal edildi ve koltuklar yeniden satışa açıldı.
- **Kanıt:**
  - `kanitlar/12-biletlerim-liste.png`, `kanitlar/13-iptal-dialog.png`, `kanitlar/14-iptal-edildi.png`, `kanitlar/15-biletlerim-format-ve-24saat.png`
  - HTTP: `POST http://127.0.0.1:4103/api/siparisler/DJ36ZD/iptal` -> `200`, `POST http://127.0.0.1:4103/api/siparisler/72TNGT/iptal` -> `200 {"pnr":"72TNGT",...,"durum":"iptal"}`

---

### HATA-03 — Arama (`Ara`) işlevinde Türkçe `İ/i` ve `I/ı` harf dönüşümü nedeniyle geçerli aramaların 0 sonuç döndürmesi
- **Önem derecesi:** Yüksek
- **Tekrar üretme adımları:**
  1. `http://127.0.0.1:4103/#/` ana sayfasını açın.
  2. `Ara` (`#ara`) kutusuna küçük harfle `istanbul` yazın.
  3. Kutuyu temizleyip sırasıyla `izmir`, `İZMİR`, `BOĞAZİÇİ`, `NİŞANTAŞI`, `KAVAKLIDERE` kelimelerini yazın.
- **Beklenen sonuç:** Büyük/küçük harf fark etmeksizin Türkçe kurallarına uygun olarak `istanbul` yazınca İstanbul'daki 3 etkinlik, `izmir`/`İZMİR` yazınca İzmir'deki 2 etkinlik, mekân/etkinlik aramalarında da ilgili etkinlikler listelenmelidir.
- **Gerçekleşen sonuç:** `istanbul`, `izmir`, `İZMİR`, `BOĞAZİÇİ`, `NİŞANTAŞI`, `KAVAKLIDERE` aramalarının tümü `0` sonuç ve `"Aramanızla eşleşen etkinlik bulunamadı."` mesajı döndürdü (`İstanbul`, `İzmir`, `boğaziçi`, `nişantaşı`, `kavaklıdere` ise eşleşti; kök neden yerel ayarsız `.toLowerCase()` ile `İ -> i\u0307` ve `I -> i` dönüşüm farkı).
- **Kanıt:** `kanitlar/03-arama-istanbul.png`

---

### HATA-04 — Bilet türü seçiminin (`Tam` / `Öğrenci`) klavye ve ekran okuyucu ile kullanılamaması (WCAG 2.1 AA)
- **Önem derecesi:** Yüksek
- **Tekrar üretme adımları:**
  1. `http://127.0.0.1:4103/#/etkinlik/101` detay sayfasını açın.
  2. Fare kullanmadan `Tab` tuşuyla sayfadaki kontroller arasında gezinin.
  3. Chrome DevTools / Accessibility Tree üzerinden `#turSecimi` öğelerini inceleyin.
- **Beklenen sonuç:** WCAG 2.1 AA (2.1.1 Klavye ve 4.1.2 Ad, Rol, Değer) gereği `Tam` ve `Öğrenci` seçimleri odaklanabilir (`<input type="radio">` veya `role="radio"` / `<button>`), `Tab` + ok/Space/Enter tuşlarıyla seçilebilir ve seçili durumu yardımcı teknolojilere bildirebilir olmalıdır.
- **Gerçekleşen sonuç:** Seçenekler tıklama dinleyicili sıradan `<div class="chip" data-tur="...">` öğeleri olarak tanımlanmış; `Tab` sırası `← Tüm etkinlikler` bağlantısından doğrudan `Bilet adedi` (`#adet`) alanına atlıyor. Accessibility Tree'de `StaticText` (`focusable: false`) olarak görünüyor; klavye kullanıcısı `%20` indirimli `Öğrenci` biletini seçemiyor.
- **Kanıt:** `kanitlar/04-etkinlik-detay-101.png`, DOM incelemesi (`<div class="chips" id="turSecimi"><div class="chip secili" data-tur="tam">...`), `Tab` ve `Accessibility.getFullAXTree` çıktıları.

---

### HATA-05 — "Siparişi tamamla" butonunda çift tıklama (double-submit) koruması olmaması
- **Önem derecesi:** Yüksek
- **Tekrar üretme adımları:**
  1. Herhangi bir etkinlik (ör. `108`) için `#/odeme` ekranına geçin ve iletişim bilgilerini (`dblclick.test@example.com`) doldurun.
  2. `"Siparişi tamamla"` butonuna art arda iki kez hızlıca tıklayın (sunucu yanıtı ~700 ms sürüp `"Siparişiniz işleniyor, lütfen bekleyin…"` mesajı gösterilirken).
  3. `#/biletlerim` üzerinden `dblclick.test@example.com` siparişlerini sorgulayın.
- **Beklenen sonuç:** İlk tıklamada buton devre dışı bırakılmalı (`disabled = true`) veya gönderim kilidi uygulanmalı; yalnızca tek sipariş oluşturulmalıdır.
- **Gerçekleşen sonuç:** İlk tıklamadan sonra buton devre dışı kalmıyor (`btn.disabled === false`); iki tıklama iki ayrı `POST /api/siparisler` isteği göndererek iki ayrı PNR siparişi oluşturdu ve koltuk stoğunu iki kez düşürdü (`created orders count: 2`).
- **Kanıt:** Çift tıklama otomasyon çıktısı (`btn.disabled after 1st click: False | created orders count: 2`).

---

### HATA-06 — "Biletlerim" sayfasında tutarların Türkçe iki ondalık/binlik formatına uymaması ve ham kayan nokta sızması
- **Önem derecesi:** Orta
- **Tekrar üretme adımları:**
  1. `1150 TL` (`7KDNEB`), `162,4 TL` (`72TNGT`), `327 TL` (`N4SVK8`), `287,5 TL` (`DJ36ZD`) ve `İzmir Kordon Akustik` `3 × Öğrenci + PERDE50` (`TFA5DA`) siparişlerini oluşturun.
  2. `#/biletlerim` ekranından ilgili e-postaları (`zaman.test@example.com`, `deniz.caglar@example.com`, `sec.test@example.com`) sorgulayın ve `Tutar` sütununu inceleyin.
- **Beklenen sonuç:** `urun-notu.md` gereğince tüm tutarlar iki ondalık basamak ve binlik nokta ayracıyla (`1.150,00 TL`, `162,40 TL`, `327,00 TL`, `287,50 TL`, `383,48 TL`) gösterilmelidir.
- **Gerçekleşen sonuç:** Tutarlar sıfırları ve binlik noktası olmadan `1150 TL`, `162,4 TL`, `327 TL`, `287,5 TL` şeklinde yazdırılıyor; `TFA5DA` siparişinde ise IEEE-754 kayan nokta artığı doğrudan **`383,47600000000006 TL`** olarak tabloya yansıyor.
- **Kanıt:** `kanitlar/12-biletlerim-liste.png`, `kanitlar/15-biletlerim-format-ve-24saat.png`, `kanitlar/17-biletlerim-yuvarlama-negatif.png`.

---

### HATA-07 — İndirimli bilet küsuratında ödeme özeti ile sipariş onayı/API arasında 1 kuruş tutarsızlık
- **Önem derecesi:** Orta
- **Tekrar üretme adımları:**
  1. `#/etkinlik/104` (`İzmir Kordon Akustik`, tam bilet `164,99 TL`) sayfasında `Öğrenci` biletini ve `3` adedini seçip `Devam et`e basın.
  2. `#/odeme` ekranında `PERDE50` kampanyasını uygulayıp `Ödenecek toplam` tutarını okuyun.
  3. Siparişi tamamlayıp `#/onay/:pnr` ekranındaki (`TFA5DA`) `Ödenecek toplam` tutarını karşılaştırın.
- **Beklenen sonuç:** Kullanıcıya ödeme öncesi gösterilen toplam ile onay ekranında ve sunucuda kaydedilen toplam kuruşu kuruşuna aynı olmalıdır.
- **Gerçekleşen sonuç:** `#/odeme` ekranı birim öğrenci fiyatını `131,99 TL`'ye yuvarlayarak toplamı `3 × 131,99 + 37,50 - 50,00 = 383,47 TL` gösterdi; ancak sunucu ham `164,99 × 0,8 × 3` üzerinden `383,47600000000006` kaydettiği için onay ekranı (`#/onay/TFA5DA`) **`383,48 TL`** gösterdi.
- **Kanıt:** `kanitlar/16-yuvarlama-onay-tfa5da.png` (`383,48 TL`), ödeme özeti çıktısı (`383,47 TL`), `GET /api/siparisler/TFA5DA` (`"toplam":383.47600000000006`).

---

### HATA-08 — `#/odeme` sayfasında sayfa yenileme (F5) veya onaydan "Geri" dönüşte `undefined / NaN TL` hatası
- **Önem derecesi:** Orta
- **Tekrar üretme adımları:**
  1. Herhangi bir etkinlikten `Devam et` ile `#/odeme` sayfasına geçin ve tarayıcıyı yenileyin (`F5`) **veya**
  2. Siparişi tamamladıktan sonra `#/onay/:pnr` ekranındayken tarayıcının `Geri` tuşuna basın.
- **Beklenen sonuç:** Taslak sipariş bilgisi `sessionStorage` üzerinde korunmalı veya taslak yoksa kullanıcı temiz bir bilgilendirme mesajıyla etkinlik listesine yönlendirilmelidir.
- **Gerçekleşen sonuç:** Sayfa çöküyor gibi görünmese de sipariş özetinde `undefined`, `undefined × Tam bilet (NaN TL)`, `Hizmet bedeli (undefined × 12,50 TL) NaN TL`, `Ödenecek toplam NaN TL` metinleri basılıyor.
- **Kanıt:** `kanitlar/10-odeme-yenileme-nan.png`, `history.back()` test çıktısı (`#/onay/CTP9LS -> #/odeme`).

---

### HATA-09 — PNR ile sipariş sorgulama ve iptal uç noktalarında e-posta/sahiplik doğrulaması olmaması
- **Önem derecesi:** Orta
- **Tekrar üretme adımları:**
  1. Başka bir kullanıcıya ait 6 karakterli bir PNR koduyla `GET /api/siparisler/{PNR}` isteği atın.
  2. E-posta adresi veya onay bilgisi göndermeden `POST /api/siparisler/{PNR}/iptal` isteği atın.
- **Beklenen sonuç:** Sipariş kişisel bilgilerini (ad soyad, e-posta, cep telefonu) görme ve iptal işlemi için en azından sipariş e-postası eşleştirmesi veya oturum/imzalı bağlantı doğrulaması aranmalıdır.
- **Gerçekleşen sonuç:** Sadece PNR bilmek/tahmin etmek `GET /api/siparisler/{PNR}` ile müşterinin ad soyad, e-posta ve telefon bilgilerini okumaya ve `POST /api/siparisler/{PNR}/iptal` ile biletini iptal etmeye yetiyor.
- **Kanıt:** `GET http://127.0.0.1:4103/api/siparisler/E5NV7U -> 200` (tüm kişisel verilerle), `POST http://127.0.0.1:4103/api/siparisler/72TNGT/iptal` (gövdesiz `200 OK`).

---

### HATA-10 — Ödeme formunda doğrulama hatalarının alanlarla `aria-invalid` / `aria-describedby` üzerinden ilişkilendirilmemesi (WCAG 2.1 AA)
- **Önem derecesi:** Düşük
- **Tekrar üretme adımları:**
  1. `#/odeme` sayfasında tüm alanları boş bırakıp `Siparişi tamamla` butonuna tıklayın.
  2. `#odemeFormu` içindeki `input` öğelerinin `aria-invalid` ve `aria-describedby` niteliklerini inceleyin.
- **Beklenen sonuç:** WCAG 2.1 AA (3.3.1 Hata Tanımlama ve 1.3.1 Bilgi ve İlişkiler) kapsamında hatalı alanlara `aria-invalid="true"` atanmalı ve hata mesajı alanla programatik olarak ilişkilendirilmelidir.
- **Gerçekleşen sonuç:** Genel hata kutusu `#odemeHata` (`role="alert"`) görünmesine rağmen tüm alanlarda `aria-invalid` ve `aria-describedby` nitelikleri `null` kalıyor (ayrıca sayfa başında "İçeriğe atla" bağlantısı bulunmuyor).
- **Kanıt:** DOM erişilebilirlik kontrol çıktısı (`ariaInvalid: None, ariaDescribedby: None` for `adSoyad`, `eposta`, `telefon`, `kvkk`; `Skip link present? False`).

---

## 3. Sorular ve Gözlemler

Aşağıdaki noktalar kesin bir hata olarak değil, ürün sahibi (Selin Aksoy) kararı netleştirilmesi gereken belirsizlikler ve küçük kalite gözlemleri olarak ayrılmıştır:

1. **Onay sayfasındaki e-posta vaadi:** `urun-notu.md` "Gerçek ödeme ve e-posta gönderimi bu sürümde yoktur" demesine karşın onay ekranı (`#/onay/:pnr`) *"Sipariş ayrıntıları ... adresine gönderilecektir."* mesajını veriyor. Demo sürümde bunun demo notu olarak değiştirilmesi mi yoksa v1 üretim metni olarak kalması mı isteniyor?
2. **`Cep telefonu` format kuralı:** Alan etiketi "Cep telefonu" ve ipucu `05XX XXX XX XX` olmasına rağmen `0212 111 22 33` (sabit hat) ve başı sıfırsız `5551112233` değerleri kabul ediliyor. Yalnızca `05XX` ile başlayan Türkiye GSM numaraları mı kabul edilmeli, yoksa esnek 10–11 hane yeterli mi?
3. **`Ad Soyad` 3 harf kuralı:** İki harfli değerler (`Su`) reddediliyor (`"Ad soyad en az 3 harften oluşmalı..."`). "Ad soyad" beklentisi nedeniyle mantıklı görünse de tek isimli testler/kısa adlar (`Su Ak` 5 karakter geçiyor) için limitin tam olarak ne olması bekleniyor?
4. **Tek siparişte karma bilet türü (Tam + Öğrenci):** Şu an bir siparişte yalnızca tek tür (`Tam` veya `Öğrenci`) seçilebiliyor. Aynı siparişte örneğin 1 Tam + 2 Öğrenci bilet alma ihtiyacı var mı?
5. **Etkinlik detayında `adet` alanının `max` niteliği ve tükenen etkinlik görünümü:** `Şebnem'in Düğünü` etkinliğinde `Kalan: 3 koltuk` iken `<input id="adet" max="6">` sabit kalıyor (tıklayınca hata veriyor). Ayrıca tükenen `Zeybek ve Ege Ezgileri` (`106`) ekranında buton `Tükendi` (disabled) olsa da `Bilet al` formu ve fiyat hesabı (`108,00 TL`) ekranda aktif görünümlü duruyor; sadeleştirilmeli mi?
6. **Arama/filtre/sıralama durumunun URL'de saklanmaması:** Bir etkinliğin detayına girip `← Tüm etkinlikler` veya tarayıcı `Geri` ile dönüldüğünde seçili şehir filtresi, arama metni ve sıralama sıfırlanıyor.
7. **Etkinlik verisi ve `PERDE50` tekrar kullanımı:** `İstanbul Gençlik Senfonisi: Mevsimler` açıklamasında *"matine konserinde"* yazarken saatin `22:30` görünmesi muhtemelen demo tarih kaydırma verisinden kaynaklanıyor. Ayrıca `PERDE50` kodu aynı e-postayla sınırsız sayıda siparişte kullanılabiliyor; kişi başı kullanım limiti bekleniyor mu?
8. **Ödeme sayfasındaki geri dönüş bağlantısı:** `#/odeme` sayfasındaki `← Etkinliklere dön` bağlantısı doğrudan ana sayfaya (`#/`) gidiyor; kullanıcının bilet adedini/türünü değiştirmek istemesi halinde etkinlik detay sayfasına dönüş beklenebilir.

---

## 4. Debrief

### Neleri Kapsadık
- **Fonksiyonel akışlar:** Etkinlik listeleme, arama, şehir filtresi, 3 sıralama seçeneği, etkinlik detayı (normal, az stoklu, tükenmiş, olmayan etkinlik), fiyatlandırma (`Tam`, `Öğrenci` %20, `12,50 TL` hizmet bedeli, küsurat yuvarlama, binlik format), `PERDE50` kampanyası (`290`, `300,00`, `324,80`, `325,50 TL`, büyük/küçük harf, boşluk, geçersiz kod, üzerine yazma), form doğrulamaları, PNR oluşturma, "Biletlerim" sorgulama (büyük/küçük harf, boşluk, boş sonuç), iptal diyalogu ve koltukların satışa geri dönmesi.
- **Kötüye kullanım, API ve eşzamanlılık:** Doğrudan `POST /api/siparisler` manipülasyonları (`adet`, `toplam`, `fiyat`, `pnr`, `kvkk`, `tur`, `kampanyaKodu`), XSS denemeleri, bozuk JSON, 4 paralel istekle düşük stok (`kalan: 3`) yarış durumu, çift iptal idempotency testi, çift tıklama, `F5` yenileme ve tarayıcı `Geri` tuşu.
- **Kalite beklentileri:** Türkçe karakter/yerel ayar desteği, TL formatı, WCAG 2.1 AA (kontrast, başlık hiyerarşisi, tablo semantiği, klavye `Tab`/`Escape` ve odak dönüşü, Accessibility Tree, form `aria-*`), Chrome masaüstü (`1280×800`) ve mobil (`375×812`) duyarlı tasarım, Microsoft Edge masaüstü uçtan uca doğrulaması.

### Neleri Kapsayamadık
- **Gerçek mobil cihazlar / Edge mobil ve Safari/Firefox:** Testler Windows üzerinde Chrome (`375×812` emülasyonu) ve Edge masaüstüyle yapıldı; gerçek dokunmatik cihaz, ekran okuyucu (NVDA/JAWS ile sesli okuma) ve masaüstü dışı tarayıcılar denenmedi.
- **Tam `24:00:00` saat sınırı ve geçmiş tarihli etkinlikler:** Hazır veri setinde tam `24 saat 0 dakika` sınırında veya tarihi geçmiş etkinlik bulunmadığı ve veritabanına/sunucu saatine müdahale edilmediği için iptal kuralı `~9,5 saat`, `~22 saat` ve `>3 gün` örnekleriyle doğrulandı.
- **Yük/stres testi ve kalıcılık:** Yalnızca 4 paralel istek düzeyinde yarış testi yapıldı; yüksek eşzamanlılık altında bellek/performans profili çıkarılmadı (kalıcılık zaten demo gereği bellek içi).

### En Büyük Riskler
1. **Stok ve sipariş bütünlüğü (Kritik — HATA-01):** Negatif/sıfır/sınır dışı bilet adetlerinin arayüz ve API tarafından engellenmemesi, tükenmiş etkinliklerin dahi yapay olarak koltuk kazanmasına ve negatif tutarlı siparişler oluşmasına yol açıyor.
2. **İş kuralı ve gelir/gişe tutarsızlığı (Yüksek/Orta — HATA-02, HATA-05, HATA-07):** 24 saat iptal kuralının çalışmaması, çift tıklamayla mükerrer sipariş oluşması ve ödeme ekranıyla gişe/onay tutarı arasında 1 kuruşluk fark çıkması (`383,47` vs `383,48` vs `383,476...`) operasyonel sorun yaratır.
3. **Türkçe arama ve erişilebilirlik engelleri (Yüksek — HATA-03, HATA-04):** Kullanıcıların `istanbul`/`izmir` aradığında hiç etkinlik bulamaması doğrudan dönüşüm kaybına yol açar; klavyeyle öğrenci bileti seçilememesi WCAG 2.1 AA hedefini bozar.

### Sürüm İçin Öneri
**Perşembe günkü sürüm için öneri: Şu haliyle ÇIKILMAMALI (No-Go) — Kritik/Yüksek düzeltmeler sonrası koşullu çıkış.**  
İyi haber olarak, uygulamanın çekirdek yarış durumu kilidi (`409`), çift iptal koruması, sunucu tarafı fiyat hesaplama güvenliği, mobil `375px` düzeni ve temel renk kontrastı sağlam çalışıyor. Ancak özellikle **HATA-01** (`adet` doğrulaması), **HATA-02** (24 saat iptal kontrolü), **HATA-03** (Türkçe arama), **HATA-04** (bilet türü klavye/ARIA erişilebilirliği), **HATA-05** (çift tıklama koruması) ve **HATA-06/07** (tutar yuvarlama ve `0,00 TL` format tutarlılığı) giderilip kısa bir doğrulama turu yapılmadan canlıya alınmaması önerilir.
