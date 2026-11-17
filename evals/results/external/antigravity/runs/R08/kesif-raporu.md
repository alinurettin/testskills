# Perdeaçık Bilet (v0.9 Demo) — Keşif Testi Raporu

**Test edilen ortam:** `http://127.0.0.1:4104` (kara kutu test)  
**Referans doküman:** `urun-notu.md`  
**Test tarih/saati:** 17 Kasım 2026, 00:21 – 00:31 (+03:00)  
**Kullanılan ortam ve araçlar:** Google Chrome (`157.0.8103.52` headless CDP), Microsoft Edge (headless CDP), Python `httpx` ile doğrudan HTTP API ve eşzamanlılık istekleri.

---

## 1. Oturum Notları

### Test Charter'ları
1. **Charter 1 — Katalog Keşfi, Arama, Filtre, Sıralama ve Türkçe Yerelleştirme:** Etkinlik listesi, arama kutusu, şehir filtresi, tarih/fiyat/ad sıralamaları, Türkçe büyük/küçük harf uyumu ve TL/tarih biçimlendirmesi.
2. **Charter 2 — Bilet Seçimi, Fiyat Hesaplama, Sınır Değerler ve Kampanya (`PERDE50`):** Tam/Öğrenci (%20 indirim), bilet başına 12,50 TL hizmet bedeli, ondalık yuvarlama, 1–6 adet sınırları, tükenen etkinlik davranışı ve 300,00 TL kampanya eşiği.
3. **Charter 3 — Sipariş Tamamlama, Form Doğrulama, Kapasite ve PNR Akışı:** İletişim formu doğrulamaları, KVKK onayı, çift tıklama, sayfa yenileme/geri dönüş ve koltuk stok düşümü.
4. **Charter 4 — "Biletlerim", E-posta Sorgusu, 24 Saat İptal Kuralı ve Koltuk İadesi:** Büyük/küçük harf ve boşluk toleransı, 24 saatten az/fazla kalan etkinliklerde iptal davranışı, iptal edilen koltukların satışa dönmesi ve durum görünümü.
5. **Charter 5 — Kötü Niyetli Testçi (Adversarial API, Manipülasyon, Yarış Koşulları ve XSS):** İstemci doğrulamalarını atlayarak `POST /api/siparisler`, `POST /api/siparisler/{pnr}/iptal` ve `GET` uç noktalarını kurcalama; fiyat/adet manipülasyonu, eşzamanlı son koltuk yarışı, eşzamanlı çift iptal ve XSS denemeleri.
6. **Charter 6 — Çapraz Tarayıcı, Duyarlı Tasarım (Mobil/Masaüstü) ve Erişilebilirlik (WCAG 2.1 AA):** Chrome ve Edge'de `1280×800`, `390×844` ve `375×812` görünümler; yalnızca klavyeyle (`Tab`/`Enter`/`Esc`) gezinme, ARIA rolleri, canlı bölgeler (`aria-live`), odak yönetimi ve renk kontrastı denetimi.

### Zaman Damgalı Oturum Günlüğü
- **00:21–00:22** — Görev ve `urun-notu.md` incelendi; Chrome headless CDP bağlantısı ve UTF-8 çıktı doğrulandı.
- **00:22–00:23 (Charter 1):** Ana sayfa (`9` etkinlik) ve `/api/etkinlikler` incelendi. Sıralama (`tarih`, `fiyat`, `ad` — Türkçe alfabetik `Ç`, `İ`, `Ö`, `Ş`, `Ü` dahil) ve şehir filtresi beklendiği gibi çalıştı. Ancak arama kutusunda `"istanbul"`, `"izmir"`, `"İZMİR"` ve `"KISA"` aramalarının **0 sonuç** döndürdüğü tespit edildi (`İSTANBUL` 3, `İzmir` 2 sonuç döndürüyor).
- **00:24–00:25 (Charter 2):** Etkinlik detay sayfaları (`104`, `105`, `106`, `107`, `108`) test edildi. Öğrenci %20 indirimi ve yuvarlama (`164,99 -> 131,99 TL`), hizmet bedeli (`12,50 × adet`) ve `PERDE50` 300,00 TL tam sınırı (`107` 2×Tam = `300,00 TL` kabul, `108` 4×Tam = `290,00 TL` ret, `perde50` ve boşluklu `  PERDE50  ` kabul, çift uygulamada mükerrer indirim olmaması) doğrulandı. Buna karşılık bilet türü seçiminin (`Tam` / `Öğrenci`) klavyeyle erişilemeyen `div.chip` öğeleri olduğu ve `#adet` alanına `0`, `-2`, `""` girildiğinde `#/odeme` ekranına geçildiği görüldü.
- **00:25–00:26 (Charter 2–3):** Ödeme ekranına `-2` adetle geçilip sipariş gönderildiğinde sunucunun `201 Created` (`T43DFD`) döndürdüğü ve `108` numaralı etkinliğin kalan koltuğunu `90` kapasitenin üzerine çıkararak `92` yaptığı yakalandı. `T43DFD` iptal edildiğinde stok tekrar `90`'a indi.
- **00:26–00:28 (Charter 3–4):** Form doğrulamaları, Türkçe adlar, PNR onay ekranı (`7C85ML`), `#/odeme` yenileme (`undefined`/`NaN TL`), `Biletlerim` tablosundaki eksik ondalık/binlik biçimleri (`250 TL`, `162,4 TL`, `1100 TL`, `1014,94 TL`), çift tıklamayla mükerrer sipariş (`LVRF8P`, `KEZP6H`), `105` numaralı etkinliğin tükenip iptalle tekrar açılması ve **24 saatten az kalan `101` (`HHADRJ`) ile `102` (`CN263F`) siparişlerinin iptal edilebilmesi** tespit edildi.
- **00:28–00:29 (Charter 5):** Doğrudan HTTP istekleriyle tükenen `106` numaralı etkinliğe `adet: -1` (`8PSYAJ`) ile koltuk açılıp ardından `adet: 1` (`F9BYEK`) satın alındı; `adet: 7` (`STGVLS`) ile 6 bilet sınırı aşıldı; olmayan `etkinlikId: 9999` ve `null` isteklerinde `HTTP 500` ve sunucu yığın izi görüldü. Eşzamanlı 5 adet son-koltuk yarışı (`105`, `kalan=1`) ve 4 adet eşzamanlı iptal (`H28ZHD`) test edildi — bellek içi kilitleme/tekillik burada doğru çalıştı (`1` başarı, `4`/`3` adet `409`).
- **00:29–00:31 (Charter 6):** Chrome ve Edge üzerinde masaüstü ve mobil (`390×844`, `375×812`) ekran görüntüleri alındı; yatay taşma olmadığı ve mobilde tablonun karta dönüştüğü doğrulandı. XSS denemeleri güvenli çıktı. Klavye `Tab` turu, kontrast ve ARIA denetimi tamamlandı.

### Kullanılan Sentetik Test Verileri
- **E-postalar:** `ayse.yilmaz@example.com`, `AYSE.YILMAZ@EXAMPLE.COM`, `zeynep.kaya@example.com`, `mert.demir@example.com`, `negatif.test@example.com`, `cifttik@example.com`, `kaan@example.com`, `apitest@example.com`, `yaris0@example.com`–`yaris4@example.com`, `t1@example.com`–`t5@example.com`.
- **Adlar ve telefonlar:** `Ayşe Yılmaz`, `Zeynep Kaya`, `Mert Demir`, `İbrahim Şahin`, `Çağrı Ğüşöç`, `Ayşe-Nur Kaya`, `Dr. Ali Demir`, `O'Connor Test`, `0555 111 22 33`, `0555 333 44 55`, `+90 555 111 22 33`, `0212 111 22 33`, `123`.
- **Olumsuz / kötü niyetli girdiler:** `adet`: `-2`, `-1`, `0`, `1.5`, `7`, `100`, `999`, `""`, `null`, `"abc"`; `etkinlikId`: `9999`, `null`; `toplam: 0.01`; arama/e-posta alanında `<img src=x onerror="window.__xss=1">`, `<script>alert(1)</script>`; Türkçe arama dizgeleri: `istanbul`, `İSTANBUL`, `izmir`, `İZMİR`, `KISA`.

---

## 2. Hata Listesi

### HATA-01 — Negatif, sıfır, boş ve ondalıklı bilet adetlerinin kabul edilmesi; tükenen etkinliğin yeniden satışa açılması ve kapasitenin aşılması
- **Önem Derecesi:** Kritik
- **Tekrar Üretme Adımları:**
  1. **Arayüzden:** `#/etkinlik/108` (`kalan: 90`, `kapasite: 90`) sayfasını açın, `Bilet adedi` (`#adet`) alanına `-2` (veya `0` ya da alanı silip boş `""`) yazın ve `Devam et` düğmesine tıklayın.
  2. `#/odeme` ekranında özetin `-2 × Tam bilet` ve `-145,00 TL` (boş bırakıldıysa `NaN TL`) olarak açıldığını görün. Geçerli iletişim bilgilerini doldurup `Siparişi tamamla`'ya basın.
  3. **API üzerinden (tükenen etkinlik istismarı):** `kalan: 0` olan `106` numaralı (`Zeybek ve Ege Ezgileri`) etkinliğe `POST /api/siparisler` ile `{"etkinlikId":106,"tur":"tam","adet":-1,"kampanyaKodu":"","adSoyad":"API Test Kullanici","eposta":"apitest@example.com","telefon":"0555 000 00 10","kvkk":true}` gönderin, hemen ardından aynı etkinliğe `adet: 1` gönderin.
- **Beklenen Sonuç:** En az 1 tam sayı bilet zorunlu olmalı; `< 1`, boş, `null` veya ondalıklı değerler hem arayüzde hem API'de `400` hatasıyla reddedilmeli, `kalan` asla `kapasite` üstüne çıkmamalı ve tükenen etkinliğe satış yapılamamalıdır.
- **Gerçekleşen Sonuç:**
  - Arayüz `-2`, `0` ve `""` değerleriyle `#/odeme` adımına geçişe izin verdi. `-2` ile gönderilen sipariş `201 Created` (`PNR: T43DFD`, `toplam: -145`) alarak `108` numaralı etkinliğin kalan koltuk sayısını `90`'dan `92`'ye (`kapasite: 90` üstüne) çıkardı.
  - API'de `adet: 0` (`D5VHKK`), `adet: null` (`U9CS4G`, `adet: 0`), `adet: 1.5` (`C7PFFT`, `1`'e yuvarlandı) `201 Created` döndürdü.
  - Tükenen `106` numaralı etkinliğe gönderilen `adet: -1` isteği `201 Created` (`PNR: 8PSYAJ`, `toplam: -108`) döndürerek `kalan`'ı `0`'dan `1`'e yükseltti; ardından gönderilen `adet: 1` isteği de `201 Created` (`PNR: F9BYEK`) ile başarıyla bilet kesti.
- **Kanıt:**
  - `kanitlar/07-negatif-adet-odeme.png`
  - `kanitlar/08-kapasite-asimi-kalan-92.png`
  - `kanitlar/09-negatif-siparis-biletlerim.png`
  - HTTP yanıtı (`POST /api/siparisler`, `adet=-1`, `etkinlikId=106`): `201 {"pnr":"8PSYAJ","etkinlikId":106,...,"adet":-1,...,"toplam":-108,"durum":"aktif",...}`

---

### HATA-02 — Etkinliğe 24 saatten az süre kaldığında sipariş iptalinin engellenmemesi
- **Önem Derecesi:** Kritik
- **Tekrar Üretme Adımları:**
  1. Mevcut saat `17 Kasım 2026 00:27` iken, aynı gün saat `10:00`'daki `Boğaziçi Caz Gecesi` (`id: 101`, kalan süre ~9,5 saat) ve saat `22:30`'daki `İstanbul Gençlik Senfonisi: Mevsimler` (`id: 102`, kalan süre ~22 saat) etkinliklerinden birer sipariş oluşturun (`HHADRJ` ve `CN263F`).
  2. `#/biletlerim` sayfasında `zeynep.kaya@example.com` ile siparişleri listeleyin.
  3. `HHADRJ` ve `CN263F` satırlarındaki `İptal et` düğmesine tıklayıp onay kutusunda `Evet, iptal et` deyin (veya doğrudan `POST /api/siparisler/HHADRJ/iptal` gönderin).
- **Beklenen Sonuç:** Ürün notuna göre etkinliğe 24 saat veya daha az süre kaldığında sipariş iptal edilememeli; düğme pasif/gizli olmalı ve API de `400`/`409` ile iptali reddetmelidir.
- **Gerçekleşen Sonuç:** Her iki etkinlik için de `İptal et` düğmesi aktifti (`disabled: false`), onay diyalogu açıldı ve `POST /api/siparisler/HHADRJ/iptal` ile `POST /api/siparisler/CN263F/iptal` istekleri `HTTP 200` döndürerek siparişleri `"İptal edildi"` durumuna geçirdi ve koltukları iade etti.
- **Kanıt:**
  - `kanitlar/13-biletlerim-24saat-ve-binlik.png`
  - `kanitlar/15-24saat-icinde-iptal-sonucu.png`
  - HTTP isteği/yanıtı: `POST http://127.0.0.1:4104/api/siparisler/HHADRJ/iptal -> 200 {"pnr":"HHADRJ","etkinlikId":101,"etkinlikTarih":"2026-11-17T07:00:00.000Z",...,"durum":"iptal",...}`

---

### HATA-03 — API'de sipariş başına en fazla 6 bilet sınırının denetlenmemesi (`adet > 6` kabul ediliyor)
- **Önem Derecesi:** Yüksek
- **Tekrar Üretme Adımları:**
  1. Doğrudan HTTP istemcisi ile `POST http://127.0.0.1:4104/api/siparisler` adresine `adet: 7` içeren geçerli bir JSON gövdesi gönderin (`etkinlikId: 108`).
- **Beklenen Sonuç:** Ürün notundaki "Bir siparişte en az 1, en fazla 6 bilet olabilir" kuralı gereği sunucu `400 Bad Request` döndürmelidir.
- **Gerçekleşen Sonuç:** Sunucu yalnızca `adet > kalan` olduğunda `409` veriyor; `adet: 7` isteği `201 Created` (`PNR: STGVLS`, `adet: 7`, `toplam: 507.5`) ile onaylandı ve stoktan `7` koltuk düşüldü.
- **Kanıt:**
  - HTTP yanıtı: `GET /api/siparisler/STGVLS -> 200 {"pnr":"STGVLS","etkinlikId":108,...,"adet":7,...,"toplam":507.5,"durum":"aktif",...}`

---

### HATA-04 — Geçersiz veya bulunamayan `etkinlikId` gönderildiğinde sunucunun `500` hatası verip dahili dosya yolu ve yığın izi (stack trace) sızdırması
- **Önem Derecesi:** Yüksek
- **Tekrar Üretme Adımları:**
  1. `POST http://127.0.0.1:4104/api/siparisler` adresine `etkinlikId: 9999` (veya `etkinlikId: null`) içeren bir sipariş JSON'u gönderin.
- **Beklenen Sonuç:** Sunucu `404 Etkinlik bulunamadı` (veya `null` için `400`) döndürmeli ve dahili hata ayrıntısı/dosya yolu paylaşmamalıdır.
- **Gerçekleşen Sonuç:** Sunucu yakalanmamış tip hatasıyla `HTTP 500` döndürdü ve yanıtın `detay` alanında sunucu fonksiyon adını ve dosya sistemi yolunu açıkça döndürdü.
- **Kanıt:**
  - HTTP yanıtı (`POST /api/siparisler`, `etkinlikId: 9999`): `500 {"hata":"Beklenmeyen bir hata oluştu: Cannot read properties of undefined (reading 'tarih')","detay":"TypeError: Cannot read properties of undefined (reading 'tarih')\n    at siparisOlustur (<sunucu-dosya-yolu>...)\n..."}`

---

### HATA-05 — Etkinlik aramasında Türkçe `i/İ` ve `ı/I` büyük/küçük harf eşleşmesinin bozuk olması
- **Önem Derecesi:** Yüksek
- **Tekrar Üretme Adımları:**
  1. Ana sayfayı (`#/`) açın.
  2. `Ara` (`#ara`) kutusuna sırayla `"istanbul"`, `"izmir"`, `"İZMİR"` ve `"KISA"` yazın.
- **Beklenen Sonuç:** Türkçe harf dönüşüm kurallarına uygun olarak `"istanbul"` için İstanbul'daki 3 etkinlik, `"izmir"` ve `"İZMİR"` için İzmir'deki 2 etkinlik, `"KISA"` için `Ödüllü Kısa Filmler Gösterimi` listelenmelidir.
- **Gerçekleşen Sonuç:** Bu sorguların tamamı **0 sonuç** ve `"Aramanızla eşleşen etkinlik bulunamadı."` mesajını verdi (buna karşın `"İSTANBUL"` 3, `"İzmir"` 2 sonuç verdi; `"ç/Ç"`, `"ş/Ş"`, `"ö/Ö"`, `"ü/Ü"` harfleri sorunsuz çalıştı). Yerel olmayan küçük harfe çevirme nedeniyle `İ -> i\u0307` ve `I -> i` dönüşümü gerçekleştiği görülmektedir.
- **Kanıt:**
  - `kanitlar/02-arama-istanbul-kucuk-harf.png`
  - Oturum çıktısı: `q="istanbul" => count=0`, `q="İSTANBUL" => count=3`, `q="izmir" => count=0`, `q="İZMİR" => count=0`, `q="İzmir" => count=2`, `q="KISA" => count=0`.

---

### HATA-06 — "Siparişi tamamla" düğmesine çift tıklamada mükerrer sipariş oluşması
- **Önem Derecesi:** Yüksek
- **Tekrar Üretme Adımları:**
  1. Herhangi bir etkinlik için (ör. `109`) bilet seçip `#/odeme` ekranına geçin.
  2. Tüm iletişim alanlarını doldurup KVKK kutusunu işaretleyin.
  3. `Siparişi tamamla` düğmesine art arda iki kez hızlıca tıklayın.
- **Beklenen Sonuç:** İlk tıklamadan itibaren işlem bitene dek düğme devre dışı bırakılmalı (`disabled`) ve yalnızca tek sipariş oluşturulmalıdır.
- **Gerçekleşen Sonuç:** Ekranda `"Siparişiniz işleniyor, lütfen bekleyin…"` yazısı belirmesine rağmen düğme pasifleşmedi; iki ayrı `POST /api/siparisler` isteği gönderildi, ikisi de `201 Created` döndürdü ve `cifttik@example.com` için iki ayrı aktif sipariş (`LVRF8P` ve `KEZP6H`) oluşturuldu.
- **Kanıt:**
  - `kanitlar/14-cift-tiklama-mukerrer-siparis.png`
  - Ağ günlüğü: iki adet `POST http://127.0.0.1:4104/api/siparisler -> 201` yanıtı.

---

### HATA-07 — Erişilebilirlik (WCAG 2.1 AA): Bilet türü seçimi ("Tam / Öğrenci") klavyeyle erişilemiyor ve anlamsal rolü bulunmuyor
- **Önem Derecesi:** Yüksek
- **Tekrar Üretme Adımları:**
  1. `#/etkinlik/104` sayfasını açın.
  2. Fare kullanmadan yalnızca klavyede `Tab` tuşuyla form kontrolleri arasında ilerleyin.
- **Beklenen Sonuç:** WCAG 2.1 AA (2.1.1 Klavye, 4.1.2 Ad/Rol/Değer) uyarınca `Tam` ve `Öğrenci` seçenekleri `<input type="radio">` veya `<button>`/`role="radio"` olarak odaklanabilir olmalı ve klavyeyle seçilebilmelidir.
- **Gerçekleşen Sonuç:** Seçenekler `tabindex`, `role` ve `aria-checked`/`aria-pressed` öznitelikleri olmayan düz `<div class="chip">` öğeleridir. `Tab` sırası `← Tüm etkinlikler` bağlantısından doğrudan `#adet` kutusuna atlamakta; klavye ve ekran okuyucu kullanıcıları `Öğrenci (%20 indirimli)` bilet türünü seçememektedir.
- **Kanıt:**
  - İncelenen DOM: `<div class="chip secili" data-tur="tam">...</div>` ve `<div class="chip" data-tur="ogrenci">...</div>` (`tabIndex: -1`, `role: null`, `ariaChecked: null`).
  - `Tab` odak sırası kaydı: `← Tüm etkinlikler -> INPUT#adet -> BUTTON#devamEt`.

---

### HATA-08 — Ödeme sayfası (`#/odeme`) tarayıcıda yenilendiğinde sayfanın `undefined` ve `NaN TL` ile bozulması
- **Önem Derecesi:** Orta
- **Tekrar Üretme Adımları:**
  1. Herhangi bir etkinlik detayından `Devam et`'e tıklayarak `#/odeme` sayfasına geçin.
  2. Tarayıcıda sayfayı yenileyin (`F5` / `location.reload()`).
- **Beklenen Sonuç:** Seçili sipariş özeti korunmalı (ör. `sessionStorage` / URL parametreleriyle) ya da durum kaybolduysa kullanıcı bilgilendirilerek etkinlik sayfasına/listesine yönlendirilmelidir.
- **Gerçekleşen Sonuç:** Sayfa yenilenince özet kutusu etkinlik adı yerine `undefined`, bilet satırında `undefined × Tam bilet (NaN TL)`, hizmet bedeli ve toplamda `NaN TL` değerleriyle bozuk şekilde render edilmektedir.
- **Kanıt:**
  - `kanitlar/12-odeme-yenileme-undefined-nan.png`

---

### HATA-09 — "Biletlerim" tablosunda tutarların Türkçe iki ondalıklı ve binlik ayraçlı biçimde gösterilmemesi
- **Önem Derecesi:** Orta
- **Tekrar Üretme Adımları:**
  1. Küsüratsız veya sonu sıfırlı tutarlara sahip siparişler oluşturun (ör. `7C85ML`: `250,00 TL`; `CN263F`: `1.100,00 TL`; `HHADRJ`: `162,40 TL`; `PFHUC2`: `1.014,94 TL`).
  2. `#/biletlerim` sayfasından bu siparişleri sorgulayın.
- **Beklenen Sonuç:** Ürün notuna göre tüm tutarlar iki ondalık basamakla ve Türkçe binlik ayraçla gösterilmelidir (ör. `250,00 TL`, `1.100,00 TL`, `162,40 TL`, `1.014,94 TL`).
- **Gerçekleşen Sonuç:** Detay, ödeme ve onay ekranlarında doğru biçimlendirme yapılmasına karşın `Biletlerim` tablosunda sırasıyla `250 TL`, `1100 TL`, `162,4 TL` ve `1014,94 TL` yazdırılmaktadır (hem eksik ondalık basamak hem eksik binlik nokta ayracı).
- **Kanıt:**
  - `kanitlar/11-biletlerim-tutar-ve-eposta.png` (`250 TL`)
  - `kanitlar/13-biletlerim-24saat-ve-binlik.png` (`1014,94 TL`, `162,4 TL`, `1100 TL`)

---

### HATA-10 — Erişilebilirlik (WCAG 2.1 AA): "Biletlerim" tablosunda boş sütun başlığı ve sayfa genelinde "İçeriğe atla" bağlantısının olmaması
- **Önem Derecesi:** Düşük
- **Tekrar Üretme Adımları:**
  1. `#/biletlerim` sayfasında siparişleri listeleyin ve tablo `<th>` başlıklarını inceleyin.
  2. Ana sayfadan klavyeyle ilk `Tab` basışında ana içeriğe atlama bağlantısı olup olmadığını kontrol edin.
- **Beklenen Sonuç:** Tablodaki işlem sütununun ekran okuyucular için görünür veya `aria-label`/görsel olarak gizli başlığı olmalı (`İşlem`); ayrıca `<main id="icerik" tabindex="-1">` için bir "İçeriğe atla" bağlantısı sunulmalıdır.
- **Gerçekleşen Sonuç:** Tablodaki 7. `<th>` hücresi boştur ve sayfada `href="#icerik"` atlama bağlantısı yoktur.
- **Kanıt:**
  - `kanitlar/11-biletlerim-tutar-ve-eposta.png` (sağ üst sütun başlığı boş) ve DOM denetim çıktısı (`Skip link exists? false`).

---

## 3. Sorular ve Gözlemler

Aşağıdaki noktalar `urun-notu.md` kapsamında kesin hata olarak sınıflandırılmamış, ürün sahibi (Selin Aksoy) ile netleştirilmesi gereken ürün/tasarım/güvenlik gözlemleri olarak ayrılmıştır:

1. **PNR ile kimlik doğrulamasız veri görüntüleme ve iptal (Gizlilik/Güvenlik):** `GET /api/siparisler/{pnr}` herhangi bir e-posta/oturum doğrulaması olmadan sipariş sahibinin tam adını, e-posta adresini ve telefon numarasını döndürüyor; `POST /api/siparisler/{pnr}/iptal` ise yalnızca 6 haneli PNR bilgisiyle siparişi iptal edebiliyor. Canlı sürümde PNR + e-posta eşleştirmesi veya ek doğrulama isteniyor mu?
2. **Ödeme sayfasında geri dönüş akışı:** `#/odeme` ekranındaki bağlantı `"← Etkinliklere dön"` diyerek kullanıcıyı doğrudan `#/` listesine gönderiyor. Bilet adedini veya türünü değiştirmek isteyen kullanıcı etkinliği baştan bulmak zorunda kalıyor.
3. **Cep telefonu ve Ad Soyad doğrulama kuralları:**
   - `Cep telefonu` alanı `0212 111 22 33` (sabit hat), `+90 555 111 22 33` (12 rakam) ve `0555 111 22 3` (10 rakam, eksik cep numarası) girdilerini kabul ediyor; yalnızca `10` rakamdan az veya `12` rakamdan fazla girdileri reddediyor. Türkiye cep telefonu (`05XX...`) kuralı sıkılaştırılmalı mı?
   - `Ad Soyad` hatası `"yalnızca harf içermelidir"` dese de gerçekte `.`, `'`, `-` karakterlerini (ör. `Dr. Ali`, `O'Connor`, `Ali-Can`) kabul ediyor, rakamları reddediyor. Kabul davranışı olumlu olsa da hata metni kullanıcıyı şaşırtabilir.
4. **Karma bilet türü ve aynı etkinlik için birden çok sipariş:** Şu an tek siparişte aynı anda `Tam + Öğrenci` seçilemiyor (ör. 1 Tam + 1 Öğrenci alıp `300 TL` kampanyasına ulaşmak mümkün değil). Öte yandan aynı e-postayla art arda birden fazla `6` biletlik sipariş verilebiliyor. Bu iki davranış ürün tasarımına uygun mu?
5. **Onay mesajı ve metin tutarlılıkları:**
   - Sipariş onay ekranında `"Sipariş ayrıntıları ... adresine gönderilecektir"` ifadesi yer alıyor; `urun-notu.md` bu sürümde e-posta gönderimi olmadığını belirttiği için test/demo kullanıcılarında kafa karışıklığı yaratabilir.
   - `102` numaralı etkinliğin (`İstanbul Gençlik Senfonisi: Mevsimler`) saati `22:30` olmasına karşın açıklamasında `"matine konserinde"` yazıyor.
   - `Biletlerim` sayfasındaki e-posta giriş kutusu masaüstünde dar olduğu için uzun e-posta adresleri (`AYSE.YILMAZ@EXAMPLE.COM`) sağdan kırpılarak görünüyor.
6. **HTTP güvenlik başlıkları ve arama kapsamı:** Yanıtlarda `Content-Security-Policy`, `X-Content-Type-Options`, `X-Frame-Options` başlıkları yer almıyor. Ayrıca ana sayfadaki arama kutusu yalnızca başlık/şehir/mekân içinde arıyor; kategori (`Konser`, `Tiyatro`) veya açıklama metninin (`Kadıköy`) aranıp aranmayacağı netleştirilebilir.

---

## 4. Debrief

### Kapsanan Alanlar
- **İşlevsel kapsam:** Ana liste, arama, şehir filtresi, 3 sıralama türü, etkinlik detayları (müsait ve tükenmiş), Tam/Öğrenci fiyat hesaplamaları ve ondalık yuvarlama (`164,99 -> 131,99 TL`), hizmet bedeli, `PERDE50` eşiği (`290 TL` ret vs `300,00 TL` tam sınır kabul, büyük/küçük harf ve boşluk), form doğrulamaları, PNR oluşturma, `Biletlerim` e-posta sorgusu, iptal akışı ve koltuk iadesi, geçersiz hash rotaları (`#/etkinlik/999`, `#/onay/ZZZZZZ`, `#/olmayan-sayfa`).
- **Kötü niyetli / API & eşzamanlılık:** Doğrudan HTTP istekleriyle adet/tür/fiyat/kampanya manipülasyonu, `500` hata davranışları, `105` (`kalan=1`) üzerinde 5 eşzamanlı satın alma yarışı, `109` üzerinde 4 eşzamanlı iptal yarışı ve XSS denemeleri.
- **Tarayıcı, duyarlılık ve erişilebilirlik:** Chrome ve Edge (masaüstü `1280×800`, mobil `390×844` ve `375×812`), görsel ekran incelemesi, klavye `Tab` akışı, `<dialog>` `Esc`/odak dönüşü, ARIA canlı bölgeleri ve WCAG 2.1 AA kontrast kontrolü.

### Kapsanamayan / Sınırlı Kalan Alanlar
- **Saat dilimi / tam 24:00:00 sınır testi:** Etkinlik saatleri sabit veride olduğu için tam `24 saat 00 dakika 00 saniye` sınırını (ör. `23:59:59` vs `24:00:01`) gerçek zamanlı olarak test edemedik; ancak `<10 saat` ve `~22 saat` kalan iki etkinlikte de iptalin açık olması kuralın hiç uygulanmadığını kanıtladı.
- **Gerçek yardımcı teknoloji (NVDA/JAWS) ve fiziksel mobil cihazlar:** Ekran okuyucu davranışı gerçek sesli okuyucu yerine DOM/ARIA, odak yönetimi ve klavye olayları üzerinden doğrulandı; mobil testler Chrome/Edge mobil emülasyonuyla yapıldı.
- **Sunucu yeniden başlatma ve uzun süreli bellek/yük testi:** Tek oturumluk keşif testinde yük/dayanıklılık ve süreç yeniden başlatma testleri kapsam dışı bırakıldı.

### Güçlü Çalışan Noktalar (Kısa Not)
- İstemciden gönderilen `toplam` manipülasyonunu (`0.01 TL`) sunucu dikkate almıyor; tutarı kendi hesaplıyor.
- Eşzamanlı son koltuk yarışı (`105`) ve eşzamanlı çift iptal (`109`) testlerinde stok tutarlılığı korundu (`409 Conflict` döndü).
- Arama ve `Biletlerim` sorgularındaki XSS girişimleri güvenli şekilde etkisizleştiriliyor; mobil görünümde (`390px` ve `375px`) yatay taşma yok, `Biletlerim` tablosu karta dönüşüyor ve metin kontrastları WCAG 2.1 AA koşulunu sağlıyor.

### En Büyük Riskler
1. **Stok ve kapasite bütünlüğü riski (Kritik):** Hem arayüz hem API negatif/sıfır adetleri kabul ettiği için tükenen etkinlikler yeniden açılabiliyor ve salon kapasitesi aşılabiliyor.
2. **İş kuralı ihlali (Kritik/Yüksek):** Etkinliğe 24 saatten az kala iptal yapılabilmesi ve API üzerinden `6` bilet üst sınırının aşılabilmesi gişe/operasyon planlamasını doğrudan bozar.
3. **Türkçe arama ve erişilebilirlik uyumsuzluğu (Yüksek):** Türkiye'nin en büyük iki şehri olan `"istanbul"` ve `"izmir"` küçük harfle arandığında sonuç çıkmaması ilk izlenimde ürünün bozuk görünmesine yol açar; bilet türü seçiminin klavyeyle çalışmaması ise WCAG 2.1 AA hedefini doğrudan bozar.
4. **Veri sızıntısı ve mükerrer sipariş (Yüksek):** `500` yanıtında yığın izi/dosya yolu açığa çıkması ve çift tıklamayla mükerrer PNR üretilmesi üretim kalitesine engeldir.

### Sürüm Önerisi
**Öneri: Perşembe günkü sürüm ertelenmeli / Koşullu Red (No-Go).**  
Mevcut v0.9 sürümü, **HATA-01** (negatif/sıfır/ondalıklı adetler), **HATA-02** (24 saat iptal kuralı), **HATA-03** (API'de 6 bilet sınırı), **HATA-04** (`500` stack trace sızıntısı), **HATA-05** (Türkçe `i/İ` ve `ı/I` arama hatası), **HATA-06** (çift tıklamada mükerrer sipariş) ve **HATA-07** (bilet türü klavye erişilebilirliği) düzeltilip yeniden doğrulanmadan yayına alınmamalıdır. Bu 7 Kritik/Yüksek bulgu kapatıldıktan sonra Orta/Düşük bulgular (`HATA-08`, `HATA-09`, `HATA-10`) da düzeltilerek hedeflenen demo kalitesine ulaşılabilir.
