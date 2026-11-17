# Perdeaçık Bilet (v0.9 Demo) — Keşif Testi Raporu

**Test edilen ortam:** `http://127.0.0.1:4111` (bellek içi demo/test ortamı)  
**Referans doküman:** `urun-notu.md` (Perdeaçık Bilet — Ürün notu v0.9 demo)  
**Test tarih ve saati:** 16.11.2026, `18:45`–`18:53` (UTC+3 / Türkiye saati)  
**Tarayıcı ve platformlar:** Google Chrome (masaüstü `1280×900` ve mobil `390×844`), Microsoft Edge (masaüstü `1280×900` ve mobil `390×844`), ayrıca doğrudan HTTP API istekleri (`GET`, `POST`, `PUT`, `DELETE`)  
**Rol ve kapsam:** Kara kutu keşif testi (kaynak koda bakılmaksızın yalnızca tarayıcı arayüzü, DevTools ağ/konsol/erişilebilirlik ağacı ve HTTP API yanıtlarıyla test edildi).

---

## 1. Oturum Notları

Oturum, ürün notundaki iş risklerine göre önceliklendirilmiş 4 **test başlatma belgesi (charter)** ve **SBTM (Session-Based Test Management)** etiketli gözlem yöntemiyle yürütüldü. Önce veri değiştiren akışlarda (sipariş oluşturma, kampanya uygulama, sipariş iptali) P1 saldırıları (görünümler arası tutarlılık / *follow the data*, sınır değerler, çift gönderim/tekrarlama, ID değiştirme/yetkilendirme), ardından P2 saldırıları (eşzamanlılık/yarış, Türkçe `İ/ı` dönüşümü, klavye/erişilebilirlik, hata sızıntısı, tarayıcı yenileme/eski sekme, mobil uyumluluk) uygulandı.

### 1.1 Test Başlatma Belgeleri (Charters) ve Turlar

| ID | Risk | Test Başlatma Belgesi (Charter) | Uygulanan Turlar ve Sezgisel Yaklaşımlar (Heuristics) |
|---|---|---|---|
| **CH-01** | Kritik | **Bilet siparişi, fiyat/indirim, `PERDE50` kampanyası ve stok akışını** sınır değerler, çift tıklama, eşzamanlı istekler, fazla alan gönderimi (mass assignment) ve görünümler arası veri takibiyle keşfet; amaç: hesaplama, yuvarlama, kampanya eşiği, stok aşımı ve çift sipariş hatalarını bulmak. | *Money Tour*, *FedEx / Follow-the-Data Tour*, *Obsessive-Compulsive Tour* (çift gönderim/tekrar), *Antisocial Tour* (negatif/boş/ondalık adet), Sınır Değerler, Yarış Durumu (2 paralel istek). |
| **CH-02** | Yüksek | **"Biletlerim", 24 saat iptal kuralı, koltuk iadesi ve sipariş API uçlarını** zaman sınırları, tekrar/paralel iptal, eski sekme (stale tab) ve IDOR/BOLA saldırılarıyla keşfet; amaç: kural ihlali, yetkisiz erişim/iptal ve tutarsız durum geçişlerini bulmak. | *State Model Walk*, *Interruptions* (ikinci sekme), *Role Swap / BOLA* (PNR ile e-postasız erişim/iptal), *Never & Always* (iptal sonrası koltuk ve durum tutarlılığı). |
| **CH-03** | Orta-Yüksek | **Etkinlik listeleme, arama, şehir filtresi, sıralama ve metin alanlarını** Türkçe harfler (`İ/ı`, `I/i`, `ç, ğ, ö, ş, ü`), TL biçimlendirme, tarih gösterimi ve HTML/XSS-benzeri girdilerle keşfet; amaç: arama/sıralama eksiklikleri, yerelleştirme ve biçim hatalarını bulmak. | *Guidebook Tour*, *Violate Data Format Rules* (Türkçe `İ/ı` harf dönüşümü, HTML etiketleri), *Metamorphic Oracle* (şehir toplamları = tüm liste). |
| **CH-04** | Orta-Yüksek | **Tüm SPA ekranlarını (`#/`, `#/etkinlik/{id}`, `#/odeme`, `#/onay/{pnr}`, `#/biletlerim`, iptal diyaloğu)** yalnızca klavye, Chrome Accessibility Tree, renk kontrastı, Chrome & Edge (masaüstü/mobil), yenileme/doğrudan URL ve bozuk API gövdeleriyle keşfet; amaç: WCAG 2.1 AA engelleri, düzen bozulmaları ve 500/bilgi sızıntısını bulmak. | *Supermodel Tour*, *Saboteur Tour* (bozuk JSON, yanlış veri tipi/HTTP metodu), *Keyboard & Screen Reader Probe*, *Configurations* (Chrome/Edge × Masaüstü/Mobil). |

### 1.2 Kullanılan Sentetik Test Verileri

Tüm testlerde yalnızca kurgusal isimler ve `@example.com` uzantılı sentetik veriler kullanıldı:
- **Müşteri / E-posta:** `Zeynep Kaya` (`zeynep.kaya@example.com`), `Mert Demir` (`mert.demir@example.com`), `Çift Tık Test` (`cifttik@example.com`), `API Test` (`api.probe@example.com`), `Yarış Bir` / `Yarış İki` (`race1@example.com`, `race2@example.com`), `İpek Işık` (`ipek.isik@example.com`), `Bugun Test` (`bugun@example.com`), `Sekme Test` (`sekme@example.com`), `Kampanya Test` (`kamp@example.com`), `Negatif Arayuz` (`neg.ui@example.com`), `Bos Adet` (`bos.adet@example.com`), `İsmail Şahin-Öztürk`, `Çağrı Işık`, `Gökçe Ünal`, `Dr. Ali Can` (`val2@example.com`).
- **Telefonlar (sentetik):** `0555 000 00 01` .. `0555 000 00 99`, `+90 555 000 00 11`, `5550000013`, `0555-000-00-12`, `(0555) 000 00 11`, `0555.000.00.11`, `0555 abc 00 14`, `123`, `abc`.
- **Sınır değerler ve dizgeler:** Adet: `""`, `0`, `-1`, `-5`, `-20`, `1.5`, `1,5`, `4`, `6`, `7`, `null`, `"iki"`; Kampanya: `PERDE50`, `perde50`, `  PERDE50  `, `299.99`, `300`, `300.00`, `300.01`; Arama/E-posta Türkçe: `istanbul`, `İSTANBUL`, `ISTANBUL`, `izmir`, `İZMİR`, `IZMIR`, `kavaklıdere`, `KAVAKLIDERE`, `İPEK.ISIK@EXAMPLE.COM`, `IPEK.ISIK@EXAMPLE.COM`; HTML testi: `<b>Ali</b> Can`, `<b>xss</b>@example.com`, `<img src=x onerror="window.__xss=1"><b>KALIN</b>`.

### 1.3 Zaman Damgalı Oturum Günlüğü

*(Notlar test yürütümü sırasında gerçek sistem saatine göre `UTC+3` kaydedilmiştir. Etiketler: `NOT`, `KAPSAM`, `HATA`, `SORU`, `FİKİR`.)*

- `18:45` `NOT:` Ön keşif (Recon) başlatıldı (`kanitlar/01-anasayfa.png`, `kanitlar/02-biletlerim-ilk.png`). `GET /api/etkinlikler` 9 kurgusal etkinlik döndü (`#101`–`#109`). `#101` bugün (`2026-11-16T19:00:00.000Z` -> 22:00 UTC+3), `#102` yarın (`2026-11-17T14:30:00.000Z` -> 17:30 UTC+3), `#105` son 3 koltuk (`kalan: 3`), `#106` tükenmiş (`kalan: 0`). Konsolda hata yok.
- `18:45` `NOT:` Veri haritası çıkarıldı: `GET /api/etkinlikler`, `GET /api/etkinlikler/{id}`, `GET /api/kampanya?kod=...&tutar=...`, `POST /api/siparisler`, `GET /api/siparisler/{pnr}`, `GET /api/siparisler?eposta=...`, `POST /api/siparisler/{pnr}/iptal`.
- `18:46` `KAPSAM:` **CH-01** normal akış: `#103` (`220,00 TL`) için 2 × Öğrenci (`176,00 TL`) + `PERDE50` -> `327,00 TL` sipariş oluşturuldu (`9FNNBM`, `kanitlar/07-siparis-onay.png`). `#103 kalan` `52 -> 50` olarak hem liste hem detay API'de güncellendi.
- `18:46` `HATA:` `Biletlerim` tablosunda `9FNNBM` tutarı `327,00 TL` yerine `327 TL` görünüyor (`kanitlar/08-biletlerim-liste.png`) -> Bkz. **HATA-08**.
- `18:46` `KAPSAM:` `GET /api/kampanya` sınırları test edildi: `tutar=299.99` -> `422` (doğru), `300` / `300.00` / `300.01` / `perde50` / ` PERDE50 ` -> `200 indirim: 50` (doğru), `0` / `-500` / `abc` -> `422`, `INVALID` / boş -> `404`. `#107` (`137,50 TL`) 2 × Tam = tam `300,00 TL` ile arayüzde `PERDE50` kabul edildi (`250,00 TL`, doğru).
- `18:46` `HATA:` `#104` (`164,99 TL`) 3 × Öğrenci + `PERDE50`: detay ve ödeme ekranları `383,47 TL` gösterirken API `383.47600000000006` kaydetti, onay sayfası (`YP5KBG`) `383,48 TL`, `Biletlerim` ise `383,47600000000006 TL` gösterdi; aynı sayfada `#102` (`1.437,50 TL`, `HTJF8Z`) `1437,5 TL` göründü (`kanitlar/09-biletlerim-tutar-bicimi.png`) -> Bkz. **HATA-04** ve **HATA-08**.
- `18:47` `KAPSAM:` `#/odeme` ekranında `PERDE50` uygulayıp tarayıcı `history.back()` ile dönüp adedi `2`'den `1`'e düşürünce kampanya sıfırlandı (`232,50 TL`). `POST /api/siparisler` `< 300 TL` iken `PERDE50` / `perde50` gönderimini `400` ile reddetti; ekstra alanlarla (mass assignment: `toplam: 1`, `durum: "iptal"`, `pnr: "HACK99"`) gönderim sunucu tarafından yok sayıldı (`L9YZCE`, `toplam: 72.5`, `durum: "aktif"`).
- `18:47` `HATA:` `#/odeme` formunda `"Siparişi tamamla"` düğmesine hızlı çift tıklamada 2 ayrı `POST /api/siparisler` gitti ve 2 aktif sipariş oluştu (`DN2ANA`, `GR59ZU`) -> Bkz. **HATA-05**.
- `18:47` `KAPSAM:` `#105` (`kalan: 3`) için 2 paralel `POST /api/siparisler` (`adet: 2` + `adet: 2`) gönderildi: biri `201` (`9EVV55`, `kalan: 1`), diğeri `409` (`Kalan koltuk: 1`) döndü; yarışta fazla satış (oversell) oluşmadı.
- `18:47`–`18:48` `HATA:` `POST /api/siparisler` ve arayüz (`#adet`) `0`, `-1`, `-5`, `-20`, `""` (`NaN`), `null`, `7` (`>6`) ve `1.5` değerlerini kabul etti; `#106` (`kalan: 0`) `adet: -1` ile `kalan: 1` olarak yeniden satışa açıldı (`RFLCZZ`), `#108` (`kapasite: 90`) `adet: -20` ile `kalan: 100` oldu (`25L469`) (`kanitlar/10-negatif-adet-odeme.png`, `kanitlar/11-negatif-adet-onay.png`, `kanitlar/25-bos-adet-odeme-nan.png`) -> Bkz. **HATA-01**.
- `18:48` `HATA:` Arayüzde `Cep telefonu` alanına `0555-000-00-12` girildiğinde (ve API'de `(0555) 000 00 11`, `0555.000.00.11`, `abc`, bilinmeyen/metin `etkinlikId` gönderildiğinde) HTTP `500` ve tam stack trace döndü; arayüzde `"Teknik ayrıntı"` altında kullanıcıya gösterildi (`kanitlar/12-telefon-tire-500-stacktrace.png`) -> Bkz. **HATA-03**.
- `18:49` `KAPSAM:` **CH-02** normal iptal: `9FNNBM` (`#103`, 2 bilet, >24 saat) `#/biletlerim` üzerinden iptal edildi (`kanitlar/13-iptal-dialog.png`, `kanitlar/14-iptal-sonrasi-biletlerim.png`); `#103 kalan` `48 -> 50` arttı; tekrarlanan veya paralel ikinci iptal isteği `409 ("Bu sipariş zaten iptal edilmiş.")` döndürdü; eski sekmeden iptal denemesinde UI bu uyarıyı doğru gösterdi (`kanitlar/19-eski-sekme-iptal.png`).
- `18:49` `HATA:` 24 saatten az kalan etkinliklerde (`HTJF8Z` ~22s40dk kala; `SHDDRV` ~3s10dk kala) `"İptal et"` düğmesi aktif göründü ve iptal işlemi `200 OK` ile gerçekleşti (`kanitlar/15-24saat-iptal-denemesi.png`) -> Bkz. **HATA-02**.
- `18:49` `HATA:` İptal edilmiş `9FNNBM` için `#/onay/9FNNBM` sayfası hâlâ `"Siparişiniz alındı"` gösterdi (`kanitlar/16-onay-sayfasi-iptal-sonrasi.png`) -> Bkz. **HATA-12**.
- `18:49` `HATA:` E-posta doğrulaması olmadan yalnızca PNR (`KMFMP5`) ile `POST /api/siparisler/KMFMP5/iptal` `200 OK` ile başkasının siparişini iptal etti ve `GET /api/siparisler/{pnr}` ad/e-posta/telefon döndürdü -> Bkz. **HATA-07** (ayrıca **SORU-01**).
- `18:49` `HATA:` `ipek.isik@example.com` için `İPEK.ISIK@EXAMPLE.COM` sorgusu `0` sipariş döndü -> Bkz. **HATA-10**.
- `18:50` `KAPSAM:` **CH-03** şehir filtresi (5 şehir toplamı = 9 etkinlik) ve sıralama (`tarih`, `fiyat` sayısal, `ad` Türkçe harf sırası `kanitlar/17-siralama-ad-turkce.png`) doğrulandı. HTML etiketleri XSS çalıştırmadı (`window.__xss === false`), onay sayfasında HTML kaçışı yapıldı; ancak `POST /api/siparisler` `<b>xss</b>@example.com` adresini `201` ile kaydetti -> Bkz. **HATA-14**.
- `18:50` `HATA:` Ana sayfada `#ara` alanına `istanbul`, `izmir`, `İZMİR`, `KAVAKLIDERE` yazıldığında `0` sonuç döndü (`kanitlar/20-arama-istanbul-sonuc-yok.png`) -> Bkz. **HATA-09**.
- `18:50` `HATA:` `#/odeme` doğrudan açıldığında veya yenilendiğinde (`Page.reload`) `undefined` / `NaN TL` göründü (`kanitlar/18-odeme-yenileme-undefined-nan.png`) -> Bkz. **HATA-11**.
- `18:50` `HATA:` **CH-04** klavye Tab testi ve AXTree incelemesinde `#turSecimi` (`Tam` / `Öğrenci`) düz `<div>` olduğu için klavye odağı almadı ve AXTree'de etkileşimli kontrol olarak görünmedi -> Bkz. **HATA-06**. Ödeme formunda hata sonrası `aria-invalid` / `aria-describedby` atanmadı -> Bkz. **HATA-13**.
- `18:51` `KAPSAM:` Chrome ve Edge'de masaüstü (`1280×900`) ve mobil (`390×844`) görünümler test edildi (`kanitlar/22-chrome-mobil-390-biletlerim.png`, `kanitlar/24-edge-mobil-390-anasayfa.png`). Tüm sayfalarda yatay taşma (`scrollWidth > innerWidth`) yok, `Biletlerim` mobilde kart görünümüne sorunsuz geçiyor, kontrast kontrolleri geçti, konsol/JS hatası yok. İptal diyaloğu (`#iptalKutusu`) `Esc` ile kapanıyor.
- `18:52` `NOT:` Test sırasında `-1` adetle açılan `#106` koltuğunu başlangıç durumuna (`Tükendi`) döndürmek için `1` test siparişi verildi (`201`).

---

## 2. Hata Listesi

| Kimlik | Önem | Başlık | Güven |
|---|---|---|---|
| **HATA-01** | Kritik | Arayüz ve API, sıfır, negatif veya boş bilet adetlerini (ve API'de `>6` / ondalığı) kabul ediyor | Doğrulandı |
| **HATA-02** | Kritik | Etkinliğe 24 saatten az kala sipariş iptali engellenmiyor (arayüz ve API) | Doğrulandı |
| **HATA-03** | Yüksek | Tire/nokta/parantez içeren telefon ve bilinmeyen `etkinlikId` sunucuyu 500 ile çökertiyor; arayüzde stack trace sızdırılıyor | Doğrulandı |
| **HATA-04** | Yüksek | Kuruş kesirli öğrenci indiriminde ödeme özeti (`383,47 TL`) ile API/onay (`383,48 TL`) tutarları uyuşmuyor | Doğrulandı |
| **HATA-05** | Yüksek | `"Siparişi tamamla"` düğmesine çift tıklamada iki ayrı sipariş oluşturuluyor | Doğrulandı |
| **HATA-06** | Yüksek | Bilet türü seçimi (`Tam`/`Öğrenci`) klavye ve ekran okuyucu için erişilemez (WCAG 2.1 AA) | Doğrulandı |
| **HATA-07** | Yüksek | Yalnızca PNR ile kimlik/e-posta doğrulaması olmadan sipariş iptali ve müşteri PII okunması mümkün | Doğrulandı |
| **HATA-08** | Orta | `"Biletlerim"` tablosunda tutarlar `1.234,50 TL` biçimine uymuyor ve ham kayan nokta sayısı görünüyor | Doğrulandı |
| **HATA-09** | Orta | Türkçe `İ/ı` harf dönüşümü hatası nedeniyle `"istanbul"`, `"izmir"`, `"İZMİR"` aramaları 0 sonuç veriyor | Doğrulandı |
| **HATA-10** | Orta | `"Biletlerim"` sorgusunda Türkçe büyük `İ` içeren e-posta (`İPEK...`) kayıtlı siparişi bulamıyor | Doğrulandı |
| **HATA-11** | Orta | `#/odeme` sayfasında yenileme veya doğrudan erişimde `undefined` ve `NaN TL` görünüyor | Doğrulandı |
| **HATA-12** | Orta | İptal edilmiş siparişin onay bağlantısı (`#/onay/{pnr}`) hâlâ `"Siparişiniz alındı"` gösteriyor | Doğrulandı |
| **HATA-13** | Düşük | Ödeme formundaki doğrulama hatalarında `aria-invalid` / `aria-describedby` bağı eksik | Doğrulandı |
| **HATA-14** | Düşük | `POST /api/siparisler` `<` ve `>` karakterleri içeren e-posta adresini kabul ediyor | Doğrulandı |

---

### HATA-01 — Arayüz ve API, sıfır, negatif veya boş bilet adetlerini (ve API'de `>6` / ondalığı) kabul ediyor
- **Önem derecesi:** Kritik (Güven: Doğrulandı)
- **Ortam:** Chrome / Windows · `http://127.0.0.1:4111` (arayüz ve HTTP API)
- **Tekrar üretme adımları:**
  1. **Arayüz (negatif/0/boş):** `http://127.0.0.1:4111/#/etkinlik/103` sayfasını açın. `Bilet adedi` (`#adet`) kutusuna `-1` yazıp `Devam et`e tıklayın. `#/odeme` sayfasında iletişim alanlarını (`Negatif Arayuz`, `neg.ui@example.com`, `0555 000 00 21`) ve KVKK onayını doldurup `Siparişi tamamla`ya tıklayın. (Aynı şekilde `#adet` değerini `0` veya tamamen boş `""` bırakıp `Devam et`e tıklayın ve formu gönderin.)
  2. **API (tükenmiş etkinlik & kapasite aşımı & >6):**
     - Tükenen `#106` (`kalan: 0`) için `POST /api/siparisler` gövdesiyle `adet: -1` gönderin.
     - `#108` (`kapasite: 90`, `kalan: 80`) için `POST /api/siparisler` gövdesiyle `adet: -20` gönderin.
     - `#108` için `adet: 7` ve `adet: 1.5` gönderin.
- **Beklenen sonuç (`urun-notu.md`):** Bir siparişte en az 1, en fazla 6 tam sayı bilet olabilir; tükenen etkinlik için bilet alınamaz. `0`, negatif, boş, ondalık veya `6`'dan büyük değerler hem arayüzde hem sunucuda reddedilmeli (`400`), `kalan` değeri asla artmamalı/kapasiteyi aşmamalıdır.
- **Gerçekleşen sonuç:**
  - Arayüzde `adet: -1` engellenmedi; `#/odeme` ekranında `-1 × Tam bilet (-220,00 TL)` ve `Ödenecek toplam: -232,50 TL` hesapladı, gönderim sonunda `#/onay/V92BGM` (`Bilet: -1 × Tam`, `Ödenecek toplam: -232,50 TL`) oluştu.
  - Arayüzde `adet: ""` (boş) bırakıldığında `#/odeme` ekranında `NaN × Tam bilet`, `Ödenecek toplam: NaN TL` göründü; form gönderildiğinde `#/onay/SVEN3T` (`adet: 0, toplam: 0`) oluştu. (`adet: 0` da `#/odeme`ye geçti.)
  - API'de `#108` üzerinde `adet: 0` (`UM35DR`, `toplam: 0`), `adet: -1` (`8Y4NMS`, `toplam: -72.5`), `adet: -5` (`LJ3SAV`, `toplam: -362.5`), `adet: 7` (`N8DDUL`, `toplam: 507.5`), `adet: 1.5` (`7ZSN5Y`, `adet: 1` olarak sessiz kesildi), `adet: null` (`86YBMG`, `adet: 0`) tümü `201 Created` döndürdü.
  - Tükenen `#106` (`kalan: 0`) `adet: -1` ile `201` (`RFLCZZ`, `toplam: -108`) döndürüp `kalan: 1` olarak yeniden satışa açıldı; `#108` ise `adet: -20` (`25L469`, `toplam: -1450`) sonrası `kalan: 100` (`kapasite: 90` üstü!) oldu.
- **Kanıt:** `kanitlar/10-negatif-adet-odeme.png`, `kanitlar/11-negatif-adet-onay.png`, `kanitlar/25-bos-adet-odeme-nan.png`, `kanitlar/24-edge-mobil-390-anasayfa.png` (Etkinlik #106 `Kalan: 1 koltuk`, #108 `Kalan: 98 koltuk`), `GET /api/siparisler/SVEN3T`, `POST /api/siparisler` yanıtları.

---

### HATA-02 — Etkinliğe 24 saatten az kala sipariş iptali engellenmiyor (arayüz ve API)
- **Önem derecesi:** Kritik (Güven: Doğrulandı)
- **Ortam:** Chrome / Windows · `16.11.2026 18:49 (UTC+3)`
- **Ön koşul:** Test anında `#101` etkinliği `2026-11-16T19:00:00.000Z` (~3 saat 10 dakika sonra), `#102` etkinliği `2026-11-17T14:30:00.000Z` (~22 saat 40 dakika sonra) başlayacaktır.
- **Tekrar üretme adımları:**
  1. `#102` etkinliği için `5 × Tam` (`HTJF8Z`, `mert.demir@example.com`) ve `#101` etkinliği için `1 × Tam` (`SHDDRV`, `bugun@example.com`) siparişlerini oluşturun.
  2. `#/biletlerim` sayfasında ilgili e-postayı sorgulayın.
  3. Sipariş satırındaki `İptal et` düğmesine tıklayıp onay kutusundan `Evet, iptal et`i seçin (veya doğrudan `POST /api/siparisler/SHDDRV/iptal` çağırın).
- **Beklenen sonuç (`urun-notu.md`):** Etkinliğe 24 saatten az süre kaldığı için sipariş iptal edilememelidir (arayüzde iptal engellenmeli ve API isteği `4xx` ile reddedilmelidir).
- **Gerçekleşen sonuç:** Her iki siparişte de `İptal et` düğmesi aktif gösterildi. Onaylandığında `POST /api/siparisler/HTJF8Z/iptal` ve `POST /api/siparisler/SHDDRV/iptal` `200 OK` döndü, ekranda `"HTJF8Z kodlu siparişiniz iptal edildi. Koltuklar yeniden satışa açıldı."` mesajı çıktı ve `#102` kalan koltuk sayısı `59`'dan `64`'e yükseldi.
- **Kanıt:** `kanitlar/09-biletlerim-tutar-bicimi.png`, `kanitlar/15-24saat-iptal-denemesi.png`, `POST /api/siparisler/SHDDRV/iptal` -> `200`.

---

### HATA-03 — Tire/nokta/parantez içeren telefon ve bilinmeyen `etkinlikId` sunucuyu 500 ile çökertiyor; arayüzde stack trace sızdırılıyor
- **Önem derecesi:** Yüksek (Güven: Doğrulandı)
- **Tekrar üretme adımları:**
  1. **Arayüz:** `#/etkinlik/103` -> `Devam et`. Ad Soyad: `Gökçe Ünal`, E-posta: `val2@example.com`, KVKK onaylı; `Cep telefonu` (`#telefon`) alanına `0555-000-00-12` yazıp `Siparişi tamamla`ya tıklayın.
  2. **API:** `POST /api/siparisler` isteğinde `telefon` alanına `"(0555) 000 00 11"`, `"0555.000.00.11"` veya `"abc"` ya da `etkinlikId` alanına `999` veya `"abc"` gönderin.
- **Beklenen sonuç:** Geçersiz telefon veya bulunamayan etkinlik için `400` veya `404` durum koduyla anlaşılır Türkçe doğrulama hatası dönmeli; sunucu `500` üretmemeli ve dosya yolu/stack trace gibi teknik iç bilgiler kullanıcıya gösterilmemelidir.
- **Gerçekleşen sonuç:** Sunucu `HTTP 500` döndürdü; yanıt gövdesinde `detay` alanı tam Node.js yığın izini ve sunucu dosya yolunu verdi:
  - Telefon `0555-000-00-12`: `Beklenmeyen bir hata oluştu: Cannot convert 0555-000-00-12 to a BigInt` + açık `"Teknik ayrıntı"` kutusunda `SyntaxError` ve dosya yolu/satır numaraları.
  - `(0555) 000 00 11` -> `500 SyntaxError: Cannot convert (0555)0000011 to a BigInt`.
  - `0555.000.00.11` -> `500 SyntaxError: Cannot convert 0555.000.00.11 to a BigInt`.
  - `etkinlikId: 999` veya `"abc"` -> `500 TypeError: Cannot read properties of undefined (reading 'tarih')`.
  - *(Şüphe: `telefonNormalEt` yalnızca boşlukları temizleyip `BigInt()` çağırıyor ve sunucu hata yakalayıcısı `err.stack` bilgisini `detay` içinde istemciye gönderiyor.)*
- **Kanıt:** `kanitlar/12-telefon-tire-500-stacktrace.png` ve `POST /api/siparisler` `500` yanıtları.

---

### HATA-04 — Kuruş kesirli öğrenci indiriminde ödeme özeti (`383,47 TL`) ile API/onay (`383,48 TL`) tutarları uyuşmuyor
- **Önem derecesi:** Yüksek (Güven: Doğrulandı)
- **Tekrar üretme adımları:**
  1. `#/etkinlik/104` (`İzmir Kordon Akustik`, tam bilet `164,99 TL`) sayfasını açın.
  2. `Öğrenci` (`131,99 TL (%20 indirimli)`) ve `Bilet adedi: 3` seçip `Devam et`e tıklayın.
  3. `#/odeme` ekranında `PERDE50` kampanya kodunu uygulayın.
  4. Geçerli bilgilerle siparişi tamamlayın (`YP5KBG`) ve onay ekranını, API yanıtını ve `#/biletlerim` listesini karşılaştırın.
- **Beklenen sonuç (`urun-notu.md` + tutarlılık kuralı):** İndirim ve yuvarlama hesabı ön yüz ile arka yüz arasında birebir aynı olmalı; ödeme adımında gösterilen tutar onay ve sipariş kayıtlarıyla çelişmemelidir.
- **Gerçekleşen sonuç:**
  - Detay (`#detayOzet`) ve ödeme (`#odemeOzet`) ekranları: `3 × 131,99 = 395,97 TL` + `37,50 TL` - `50,00 TL` = **`383,47 TL`**.
  - `POST /api/siparisler` ve `GET /api/siparisler/YP5KBG`: **`toplam: 383.47600000000006`** (`3 × 164.99 × 0.8 + 37.5 - 50`).
  - Onay sayfası (`#/onay/YP5KBG`): **`383,48 TL`** (ödeme ekranından 1 kuruş fazla!).
  - `Biletlerim` tablosu: **`383,47600000000006 TL`**.
- **Kanıt:** `kanitlar/09-biletlerim-tutar-bicimi.png`, `c1_part_a.py` ağ ve DOM çıktıları (`YP5KBG`).

---

### HATA-05 — `"Siparişi tamamla"` düğmesine çift tıklamada iki ayrı sipariş oluşturuluyor
- **Önem derecesi:** Yüksek (Güven: Doğrulandı)
- **Tekrar üretme adımları:**
  1. `#/etkinlik/108` -> `Devam et` ile `#/odeme` sayfasına geçin.
  2. Geçerli bilgiler (`Çift Tık Test`, `cifttik@example.com`, `0555 000 00 03`, KVKK onaylı) girin.
  3. `Siparişi tamamla` düğmesine art arda hızlıca iki kez tıklayın (işlem ~700 ms sürdüğü için istek bitmeden ikinci tıklama gerçekleşir).
- **Beklenen sonuç:** İlk tıklamada düğme kilitlenmeli/devre dışı kalmalı veya tekrar gönderim engellenmeli; yalnızca 1 sipariş oluşmalıdır.
- **Gerçekleşen sonuç:** Tarayıcı aynı zaman damgasında (`2026-11-16T15:47:41.228Z`) iki ayrı `POST /api/siparisler` isteği gönderdi; ikisi de `201 Created` döndü ve `DN2ANA` ile `GR59ZU` PNR'lı iki ayrı aktif sipariş oluşturularak toplam 2 koltuk düşüldü.
- **Kanıt:** `GET /api/siparisler?eposta=cifttik@example.com` çıktısı (2 aktif sipariş: `DN2ANA`, `GR59ZU`) ve ağ günlüğü.

---

### HATA-06 — Bilet türü seçimi (`Tam`/`Öğrenci`) klavye ve ekran okuyucu için erişilemez (WCAG 2.1 AA)
- **Önem derecesi:** Yüksek (Güven: Doğrulandı)
- **Tekrar üretme adımları:**
  1. `#/etkinlik/103` sayfasını açın.
  2. Yalnızca `Tab` tuşunu kullanarak sayfadaki kontroller arasında gezinmeye çalışın ve `Öğrenci (%20 indirimli)` seçeneğine ulaşmayı deneyin.
  3. Chrome DevTools / Accessibility Tree üzerinden `#turSecimi` düğümlerini inceleyin.
- **Beklenen sonuç (`urun-notu.md`, WCAG 2.1 AA 2.1.1 Keyboard & 4.1.2 Name, Role, Value):** Bilet türü seçenekleri klavye odağı alabilmeli, `Enter`/`Space` veya ok tuşlarıyla seçilebilmeli ve ekran okuyucuya rol (`radio`/`button`) ve seçili durum (`aria-checked`/`aria-pressed`) bildirmelidir.
- **Gerçekleşen sonuç:** Seçenekler düz `<div class="chip" data-tur="tam|ogrenci">` öğeleridir; `tabindex`, `role` ve `aria-checked` yoktur. `Tab` sırası `← Tüm etkinlikler` -> `Bilet adedi (#adet)` -> `Devam et (#devamEt)` şeklinde ilerleyip bilet türü seçimini tamamen atlamaktadır. AXTree içinde yalnızca `StaticText` olarak görünür; klavye kullanıcısı öğrenci bileti alamaz.
- **Kanıt:** `c4_a11y.py` klavye `Tab` odak sırası ve `Accessibility.getFullAXTree` çıktısı, `kanitlar/03-detay-101.png`.

---

### HATA-07 — Yalnızca PNR ile kimlik/e-posta doğrulaması olmadan sipariş iptali ve müşteri PII okunması mümkün
- **Önem derecesi:** Yüksek (Güven: Doğrulandı)
- **Tekrar üretme adımları:**
  1. Başka bir müşteriye ait siparişin 6 karakterli PNR'ı ile (`val2@example.com` -> `KMFMP5`) herhangi bir e-posta veya oturum bilgisi vermeden `GET /api/siparisler/KMFMP5` isteği atın.
  2. Ardından `POST /api/siparisler/KMFMP5/iptal` isteğini doğrudan gönderin.
- **Beklenen sonuç:** "Biletlerim" sayfası siparişleri görmek ve iptal etmek için müşterinin e-posta adresini şart koşarken, API uçları da PNR sahipliğini (en azından siparişin e-posta adresiyle eşleşmesini) doğrulamalıdır; yalnızca PNR tahmini/sızıntısıyla üçüncü kişiler müşteri telefon/e-postasını okuyamamalı ve siparişi iptal edememelidir.
- **Gerçekleşen sonuç:** `GET /api/siparisler/KMFMP5` doğrudan `adSoyad`, `eposta`, `telefon` bilgilerini döndürdü (`200`); `POST /api/siparisler/KMFMP5/iptal` ise hiçbir ek doğrulama olmadan `200 OK` ile siparişi iptal etti (`durum: "iptal"`).
- **Kanıt:** `c2_part_b.py` çıktısı (`POST /api/siparisler/KMFMP5/iptal -> 200`).

---

### HATA-08 — `"Biletlerim"` tablosunda tutarlar `1.234,50 TL` biçimine uymuyor ve ham kayan nokta sayısı görünüyor
- **Önem derecesi:** Orta (Güven: Doğrulandı)
- **Tekrar üretme adımları:**
  1. `#103` (`327,00 TL` -> `9FNNBM`), `#102` (`1.437,50 TL` -> `HTJF8Z`) ve `#104` (`383,476... TL` -> `YP5KBG`) siparişlerini oluşturun.
  2. `#/biletlerim` sayfasında ilgili e-postaları sorgulayıp `Tutar` sütununa bakın (hem masaüstü hem mobil `390px`).
- **Beklenen sonuç (`urun-notu.md`):** Tutarlar TL cinsinden, iki ondalık basamaklı, binlik ayıracı nokta ve ondalık ayıracı virgül olacak şekilde Türkçe gösterilmelidir (`327,00 TL`, `1.437,50 TL`, `383,48 TL`).
- **Gerçekleşen sonuç:** Tabloda sırasıyla **`327 TL`**, **`1437,5 TL`** ve **`383,47600000000006 TL`** görüntülendi. *(Şüphe: Diğer sayfalardaki `tl()` biçimlendiricisi yerine `Biletlerim` tablosunda doğrudan `String(s.toplam).replace('.', ',') + ' TL'` kullanılıyor.)*
- **Kanıt:** `kanitlar/08-biletlerim-liste.png`, `kanitlar/09-biletlerim-tutar-bicimi.png`, `kanitlar/22-chrome-mobil-390-biletlerim.png`.

---

### HATA-09 — Türkçe `İ/ı` harf dönüşümü hatası nedeniyle `"istanbul"`, `"izmir"`, `"İZMİR"` aramaları 0 sonuç veriyor
- **Önem derecesi:** Orta (Güven: Doğrulandı)
- **Tekrar üretme adımları:**
  1. Ana sayfayı (`#/`) açın (İstanbul'da 3, İzmir'de 2, Kavaklıdere'de 1 etkinlik mevcuttur).
  2. `Ara` (`#ara`) kutusuna sırasıyla `istanbul`, `izmir`, `İZMİR` ve `KAVAKLIDERE` yazın.
- **Beklenen sonuç (`urun-notu.md`):** Türkçe arayüzde büyük/küçük harf duyarsız arama yapılmalı; `"istanbul"` için 3, `"izmir"` / `"İZMİR"` için 2, `"KAVAKLIDERE"` için 1 etkinlik listelenmelidir.
- **Gerçekleşen sonuç:** Tümü `"Aramanızla eşleşen etkinlik bulunamadı."` mesajıyla **0 sonuç** verdi. (Buna karşılık `"İSTANBUL"` 3, `"İzmir"` 2, `"kavaklıdere"` 1 sonuç verdi.) *(Şüphe: JavaScript `.toLowerCase()` kullanımı `İ` karakterini `'i\u0307'` (birleşik noktalı i), `I` karakterini `'i'` yaptığı için Türkçe metinlerle eşleşmiyor.)*
- **Kanıt:** `kanitlar/20-arama-istanbul-sonuc-yok.png`, `c3_probes.py` arama çıktıları.

---

### HATA-10 — `"Biletlerim"` sorgusunda Türkçe büyük `İ` içeren e-posta (`İPEK...`) kayıtlı siparişi bulamıyor
- **Önem derecesi:** Orta (Güven: Doğrulandı)
- **Tekrar üretme adımları:**
  1. `ipek.isik@example.com` adresiyle bir sipariş oluşturun.
  2. `#/biletlerim` üzerinden `İPEK.ISIK@EXAMPLE.COM` yazarak arayın (veya `GET /api/siparisler?eposta=İPEK.ISIK@EXAMPLE.COM` çağırın).
- **Beklenen sonuç:** E-posta araması Türkçe büyük/küçük `İ/i` dönüşümünü destekleyerek kayıtlı `1` siparişi getirmelidir.
- **Gerçekleşen sonuç:** `IPEK.ISIK@EXAMPLE.COM` (ASCII `I`) `1` sipariş bulurken, `İPEK.ISIK@EXAMPLE.COM` (Türkçe `İ`) `0` sipariş (`{"siparisler":[]}`) döndürdü.
- **Kanıt:** `c2_part_b.py` sorgu çıktısı (`count=0`).

---

### HATA-11 — `#/odeme` sayfasında yenileme veya doğrudan erişimde `undefined` ve `NaN TL` görünüyor
- **Önem derecesi:** Orta (Güven: Doğrulandı)
- **Tekrar üretme adımları:**
  1. Herhangi bir etkinlik detayından `Devam et`e tıklayıp `#/odeme` ekranına geçtikten sonra tarayıcıyı yenileyin (`F5`) **veya** yeni sekmede doğrudan `http://127.0.0.1:4111/#/odeme` adresini açın.
- **Beklenen sonuç:** Seçili etkinlik durumu kaybolduysa kullanıcı etkinlik listesine (`#/`) yönlendirilmeli veya anlamlı bir boş durum/geri dönüş mesajı gösterilmelidir.
- **Gerçekleşen sonuç:** Ekranda `"undefined"`, `"undefined × Tam bilet (NaN TL) NaN TL"`, `"Hizmet bedeli (undefined × 12,50 TL) NaN TL"`, `"Ödenecek toplam NaN TL"` metinleriyle bozuk ödeme formu render edildi.
- **Kanıt:** `kanitlar/18-odeme-yenileme-undefined-nan.png`.

---

### HATA-12 — İptal edilmiş siparişin onay bağlantısı (`#/onay/{pnr}`) hâlâ `"Siparişiniz alındı"` gösteriyor
- **Önem derecesi:** Orta (Güven: Doğrulandı)
- **Tekrar üretme adımları:**
  1. Oluşturulan bir siparişi (`9FNNBM`) `#/biletlerim` üzerinden iptal edin (`durum: "iptal"`).
  2. `http://127.0.0.1:4111/#/onay/9FNNBM` adresini açın.
- **Beklenen sonuç:** İptal edilmiş siparişin durumu sayfada açıkça `"İptal edildi"` olarak belirtilmeli; gişede geçerli aktif sipariş izlenimi verilmemelidir.
- **Gerçekleşen sonuç:** Sayfa `"Siparişiniz alındı"`, `"PNR kodunuz: 9FNNBM"` ve `"Ödemenizi etkinlik girişinde gişede yapabilirsiniz."` şeklinde aktif sipariş gibi görüntülendi.
- **Kanıt:** `kanitlar/16-onay-sayfasi-iptal-sonrasi.png`.

---

### HATA-13 — Ödeme formundaki doğrulama hatalarında `aria-invalid` / `aria-describedby` bağı eksik (WCAG 2.1 AA)
- **Önem derecesi:** Düşük (Güven: Doğrulandı)
- **Tekrar üretme adımları:**
  1. `#/odeme` sayfasında iletişim alanlarını boş bırakıp `Siparişi tamamla`ya tıklayın.
  2. `#adSoyad`, `#eposta`, `#telefon` ve `#kvkk` öğelerinin ARIA niteliklerini inceleyin.
- **Beklenen sonuç (WCAG 2.1 AA 3.3.1 Error Identification & 4.1.2):** Hatalı alanlar `aria-invalid="true"` ve hata kutusuna bağlı `aria-describedby` ile işaretlenmeli; zorunlu KVKK onay kutusu da uygun biçimde belirtilmelidir.
- **Gerçekleşen sonuç:** Hata mesajı yalnızca form altındaki `#odemeHata` (`role="alert"`) alanında metin olarak gösterildi; `#adSoyad`, `#eposta`, `#telefon` ve `#kvkk` öğelerinde `aria-invalid: null` ve `aria-describedby: null` kaldı (`#kvkk` üzerinde `required` niteliği de yok).
- **Kanıt:** `c4_a11y.py` form ARIA inceleme çıktısı.

---

### HATA-14 — `POST /api/siparisler` `<` ve `>` karakterleri içeren e-posta adresini kabul ediyor
- **Önem derecesi:** Düşük (Güven: Doğrulandı)
- **Tekrar üretme adımları:**
  1. `POST /api/siparisler` uç noktasına `{"etkinlikId":108,"tur":"tam","adet":1,"adSoyad":"Ali Can","eposta":"<b>xss</b>@example.com","telefon":"0555 000 00 50","kvkk":true}` gönderin.
- **Beklenen sonuç:** RFC/HTML standartlarına göre geçersiz olan `<` ve `>` karakterli e-posta adresi `400` ile reddedilmelidir.
- **Gerçekleşen sonuç:** `201 Created` (`6K9EBG`) döndü ve `eposta: "<b>xss</b>@example.com"` kaydedildi. (Onay sayfasında DOM kaçışı uygulandığı için HTML/XSS çalışmadı: `&lt;b&gt;xss&lt;/b&gt;@example.com`.)
- **Kanıt:** `c3_probes.py` çıktısı (`6K9EBG`).

---

## 3. Sorular ve Gözlemler (Ürün Sahibine)

Aşağıdaki noktalar mevcut ürün notunda (`urun-notu.md`) açıkça tanımlanmadığı için hata yerine ürün kararı gerektiren sorular olarak ayrılmıştır:

1. **SORU-01 (Üyeliksiz yapıda PNR güvenliği ve iptal yetkilendirmesi):** İlk sürümde üyelik yok; ancak şu anda yalnızca 6 haneli PNR bilen/tutturan herkes `#/onay/{pnr}` veya API üzerinden müşterinin ad soyad, e-posta ve telefon bilgisini görebiliyor ve siparişi iptal edebiliyor (HATA-07). İptal ve PNR detayı için e-posta eşleştirme doğrulaması (ör. PNR + e-posta) isteniyor mu?
2. **SORU-02 (Kuruş yuvarlama kuralı):** İndirimli bilet fiyatı kuruşun altına indiğinde (`164,99 TL × %80 = 131,992 TL`), 3 bilet için toplam `3 × 131,99 = 395,97 TL` (birim fiyattan yuvarlama) mi yoksa `round(3 × 131,992) = 395,98 TL` (satır toplamından yuvarlama) mı esas alınmalı? (HATA-04 çözümünde tek kural seçilmeli.)
3. **SORU-03 (24 saat kuralı saat dilimi ve tam sınır):** "Etkinliğe 24 saatten fazla varsa" kuralı `> 24:00:00` şeklinde mi yoksa `>= 24:00:00` şeklinde mi uygulanmalı ve sistem saat dilimi Türkiye saati (UTC+3) olarak mı sabitlenmeli? Ayrıca tarihi geçmiş etkinlikler satışa kapanıyor mu?
4. **SORU-04 (24 saatten az kalan siparişlerde arayüz davranışı):** İptal süresi dolmuş siparişlerde `"İptal et"` düğmesi tamamen gizlenmeli mi, yoksa devre dışı bırakılıp yanında `"Etkinliğe 24 saatten az kaldığı için iptal edilemez"` açıklaması mı gösterilmeli?
5. **SORU-05 (E-posta başına bilet sınırı):** "Bir siparişte en fazla 6 bilet olabilir" kuralı yalnızca tek sipariş için mi geçerli, yoksa aynı e-posta adresi aynı etkinliğe birden fazla siparişle 6'dan fazla bilet alabilmeli mi?
6. **SORU-06 (Kabul edilen telefon biçimleri):** Cep telefonu alanında `+90 5XX...` ve başındaki `0` olmadan `5550000013` şu an kabul ediliyor; `0555-000-00-12` veya `(0555) 000 00 11` gibi biçimler normalize edilip kabul edilmeli mi yoksa yalnızca `05XX` rakamları mı desteklenmeli?
7. **SORU-07 (Öğrenci bileti gişe uyarısı):** Öğrenci bileti seçildiğinde sipariş özetinde veya onay ekranında `"Gişede öğrenci kimliği ibraz edilmesi gerekir"` gibi bir bilgilendirme metni isteniyor mu?
8. **SORU-08 (Arama kapsamı ve filtre kalıcılığı):** `#ara` kutusu şu an yalnızca ad/şehir/mekân mı aramalı, yoksa kategori (`Tiyatro`, `Konser`) ve açıklama alanları da aramaya dahil edilmeli mi? Ayrıca bir etkinlik detayına girip `"← Tüm etkinlikler"` ile geri dönüldüğünde önceki arama/şehir/sıralama seçiminin korunması bekleniyor mu?

---

## 4. Debrief (PROOF Değerlendirmesi ve Sürüm Önerisi)

### 4.1 Neleri Kapsadım (Past & Results)
- **Kapsanan iş akışları:** Etkinlik listeleme, arama, şehir filtresi, 3 sıralama seçeneği (`tarih`, `fiyat`, `ad`), etkinlik detayı (`Tam`/`Öğrenci`, stokta kalan/son koltuk/tükendi durumları), sipariş özeti, `PERDE50` kampanyası (`299,99` / `300,00` / `300,01` ve büyük/küçük harf), sipariş tamamlama ve onay ekranı, `Biletlerim` sorgulama ve sipariş iptali ile iptal sonrası koltuk iadesi.
- **Kapsanan teknik ve kalite boyutları:**
  - *Veri tutarlılığı:* Ön yüz detay/ödeme/onay/Biletlerim ekranları ile API yanıtlarının karşılaştırılması.
  - *Dayanıklılık ve güvenlik:* Çift tıklama, 2'li paralel satın alma ve 2'li paralel iptal yarışları, eski sekme iptali, tarayıcı geri/yenileme/doğrudan URL, ekstra JSON alanları (mass assignment), bozuk JSON, geçersiz tipler, HTML enjeksiyonu ve PNR ile BOLA/IDOR kontrolü.
  - *Yerelleştirme ve biçimlendirme:* Türkçe `İ/ı` harf dönüşümü, Türkçe alfabetik sıralama (`Ç, İ, Ö, Ş, Ü`), `TL` kuruş/binlik ayracı biçimi ve UTC+3 saat gösterimi.
  - *Erişilebilirlik ve tarayıcılar:* Klavye ile `Tab`/`Esc` gezinmesi, Accessibility Tree, renk kontrastı hesabı, Google Chrome ve Microsoft Edge üzerinde masaüstü (`1280×900`) ve mobil (`390×844`) görünümler.
- **Olumlu doğrulanmış alanlar (temiz çalışanlar):**
  - `PERDE50` eşiği (`299,99` ret / `300,00` ve `300,01` kabul, `< 300 TL` iken API'de `400` ret, geri gidip adet düşürünce kampanyanın temizlenmesi).
  - Eşzamanlı 2'li yarışta stok koruma (`kalan: 3` için iki adet `2`'li paralel istekten yalnızca biri geçti) ve paralel çift iptalde stok şişmemesi (`409`).
  - Şehir filtresi ve `ad` Türkçe alfabetik sıralama + `fiyat` sayısal sıralama.
  - HTML/XSS kaçışı, masaüstü/mobilde sıfır yatay taşma ve konsolda sıfır JavaScript hatası.

### 4.2 Neleri Kapsayamadım (Obstacles & Kalan Risk)
1. **Tam `24:00:00` ± 1 dakika sınır testi:** Demo ortamı sabit etkinlik tarihleri içerdiği ve saat manipülasyonu yapılamadığı için tam 24.00 saat sınırındaki `>` / `>=` ayrımı test edilemedi (ancak ~3 saat ve ~22s40dk kala iptalin çalıştığı kanıtlandığından kuralın hiç uygulanmadığı görüldü).
2. **Yük / performans testi:** Çoklu eşzamanlı kullanıcı altında yanıt süreleri ve bellek davranışı (ör. k6 yük testi) ölçülmedi; yalnızca 2'li paralel istekler denendi.
3. **Gerçek ekran okuyucu ve fiziksel mobil cihazlar:** Erişilebilirlik Chrome Accessibility Tree, klavye olayları ve DOM kontrast analiziyle değerlendirildi; NVDA/JAWS/VoiceOver ile canlı sesli okuma ve gerçek iOS Safari/Android Chrome cihaz testi yapılmadı.
4. **Uzun oturum ve sunucu yeniden başlatma:** Uzun süreli açık sekme (memory leak) ve sunucu restart sonrası bellek sıfırlanması test edilmedi.
5. **Ödeme ve gerçek e-posta gönderimi:** Ürün notuna göre bu sürümde yer almadığı için kapsam dışıydı.

### 4.3 En Büyük Riskler
1. **Finansal ve stok bütünlüğü riski (Kritik):** Hem arayüzden hem API'den `-1`/`0`/boş adetle eksi tutarlı sipariş verilebilmesi, tükenen etkinliklerin yeniden açılabilmesi ve kapasitenin (`90` yerine `100`) aşılabilmesi (HATA-01).
2. **İş kuralı ihlali (Kritik):** Etkinliğe saatler kala dahi tüm siparişlerin iptal edilebilmesi (HATA-02).
3. **Kullanıcı güveni ve güvenlik riski (Yüksek):** Standart tireli telefon girişinde (`0555-000-00-12`) sunucunun 500 ile çöküp iç dosya yolunu içeren stack trace göstermesi (HATA-03), kuruşlu fiyatlarda ödeme ekranı ile onay/API arasında 1 kuruş fark ve ham float sızıntısı (HATA-04, HATA-08), çift tıklamayla çift sipariş (HATA-05) ve PNR ile doğrulamasız iptal/PII ifşası (HATA-07).
4. **WCAG 2.1 AA uyumsuzluğu ve Türkçe arama kaybı (Yüksek/Orta):** Klavye kullanıcılarının Öğrenci bileti alamaması (HATA-06) ve `"istanbul"`/`"izmir"` arayan kullanıcıların etkinlikleri hiç görememesi (HATA-09).

### 4.4 Sürüm İçin Öneri
Perşembe günkü sürüm kararı için **mevcut v0.9 demo yapısının bu haliyle canlıya/dış kullanıcıya ÇIKARILMAMASINI (Hold / No-Go)** öneriyorum. Uygulamanın temel tarama, sıralama, kampanya eşiği ve duyarlı (responsive) tasarımı sağlam bir iskelet sunsa da, **2 Kritik** ve **5 Yüksek** önem dereceli hata doğrudan bilet stoğunu, tutar doğruluğunu, erişilebilirliği ve temel iş kurallarını bozmaktadır.

**Sürüm öncesi asgari düzeltme kapısı (Release Gate):**
1. **Zorunlu (Yayın Öncesi Bloklayıcı):** HATA-01 (hem UI hem API'de `1 <= adet <= 6`, tam sayı ve `<= kalan` doğrulaması), HATA-02 (24 saat iptal kuralının API ve UI'da uygulanması), HATA-03 (telefon normalizasyonu + üretim/demo hatalarında stack trace gizlenmesi), HATA-04 & HATA-08 (kuruş yuvarlama ve Türkçe TL biçiminin tüm ekranlarda birleştirilmesi), HATA-05 (`Siparişi tamamla` çift tıklama koruması) ve HATA-06 (bilet türü seçiminde klavye/ARIA erişilebilirliği).
2. **Güçlü Tavsiye (Aynı Sürüme Alınmalı):** HATA-09 & HATA-10 (Türkçe `toLocaleLowerCase('tr')` düzeltmesi — düzeltmesi çok düşük maliyetli, kullanıcı etkisi yüksek), HATA-11 (`#/odeme` yenileme yönlendirmesi) ve HATA-12 (iptal sonrası onay sayfası durumu).
3. **Paydaş Kararıyla Netleştirilecek:** HATA-07 (PNR + e-posta doğrulaması gereksinimi) ile Bölüm 3'teki ürün sahibi soruları.
