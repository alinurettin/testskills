# PoyrazKlinik Mobil v4.3 — Test Planı

| Alan | Değer |
|---|---|
| Hazırlayan | Mobil QA Ekibi (Deniz Arıkan) |
| Gözden geçiren | Kerem Sezgin (Mobil Takım Lideri) |
| Plan sürümü | 1.2 — 22 Eylül 2026 |
| İlgili belgeler | Ürün Özeti v4.3 (belge sürümü 3.1), cihaz kullanım verisi (Ağustos 2026) |
| Test dönemi | 28 Eylül – 10 Ekim 2026 |

---

## 1. Amaç ve kapsam

Bu plan, PoyrazKlinik Mobil 4.3 sürümünün iOS ve Android uygulamalarının mağaza gönderiminden (13 Ekim 2026) önce doğrulanmasını tanımlar. Kapsamdaki alanlar: giriş ve biyometri, randevular, otomatik varış (konum), belge yükleme, bildirimler, çevrimdışı kuyruk, ödeme, derin bağlantılar, sürüm yükseltme ve erişilebilirlik.

## 2. Test yaklaşımı

- **Senaryo tabanlı manuel test:** Bölüm 5'teki test durumları her platformda, Bölüm 6'daki cihaz matrisinde koşulur.
- **Keşif testi:** Her alan için 60 dakikalık zaman kutulu oturumlar (toplam 10 oturum).
- **Otomasyon:** Appium ile duman (smoke) seti — giriş, randevu alma, belge yükleme, ödeme (sandbox). Her gece QA derlemesine karşı koşulur.
- **API testleri:** Postman koleksiyonu ile staging API üzerinde sözleşme ve hata kodu kontrolleri.
- **Hata önceliklendirme:** P1 (yayını engeller), P2 (yayından önce düzeltilmeli), P3 (sonraki sürüm).

## 3. Ortamlar ve derlemeler

| Bileşen | Ayrıntı |
|---|---|
| API | Staging: `https://api-staging.poyrazklinik.example` |
| Android derlemesi | QA derlemesi, Firebase App Distribution üzerinden (yükleme anahtarıyla imzalı) |
| iOS derlemesi | TestFlight (dahili test grubu) |
| Ödeme | ÖdeKolay sandbox, sağlayıcının dokümanındaki test kartları |
| Konum simülasyonu | iOS: Xcode GPX dosyaları · Android: emülatör konum araçları ve sahte konum uygulaması |
| Push | Staging FCM/APNs; hatırlatma zamanlayıcısı test için 1 dakikaya indirilebilir |

Tüm fonksiyonel testler QA derlemeleriyle yapılır. Mağaza (üretim) derlemesi, yayından sonra yalnızca duman testiyle (açılış + giriş) doğrulanır.

## 4. Riskler

| No | Risk | Etki | Olasılık | Azaltım |
|---|---|---|---|---|
| R1 | Ödeme akışında 3D Secure dönüşünün kaybolması | Yüksek | Orta | TC-PAY-04, TC-PAY-05 |
| R2 | Otomatik varış bildiriminin gelmemesi | Orta | Orta | TC-LOC-01…05 |
| R3 | Hatırlatma bildirimlerinin ulaşmaması | Yüksek | Düşük | TC-PUSH-01…05 |
| R4 | Çevrimdışı kayıtların kaybolması | Yüksek | Düşük | TC-OFF-01…07 |
| R5 | Yükseltme sonrası veri kaybı | Yüksek | Düşük | TC-UPG-01 |
| R6 | Derin bağlantıların yanlış ekranı açması | Orta | Düşük | TC-DL-01…05 |

## 5. Test durumları

### 5.1 Giriş ve biyometri

| ID | Senaryo | Adımlar | Beklenen sonuç | Platform |
|---|---|---|---|---|
| TC-BIO-01 | Başarılı biyometrik giriş | Biyometrik giriş açık; uygulamayı yeniden aç; Face ID/parmak izi doğrula | Ana ekran açılır, şifre istenmez | iOS, Android |
| TC-BIO-02 | Başarısız biyometri | 3 kez eşleşmeyen parmak/yüz dene | Şifre ekranı açılır | iOS, Android |
| TC-BIO-03 | Biyometri kilitlenmesi | Sistem biyometriyi kilitleyene kadar başarısız dene | Uygulama şifre ekranına geçer, çökme olmaz | iOS, Android |
| TC-BIO-04 | Biyometrisi olmayan cihaz | Biyometrik kaydı olmayan cihazda giriş yap | "Biyometrik giriş" seçeneği gösterilmez | iOS, Android |
| TC-BIO-05 | Biyometrik girişi kapatma | Ayarlar > Biyometrik giriş kapat; uygulamayı yeniden aç | Şifre istenir | iOS, Android |

### 5.2 Randevular

| ID | Senaryo | Adımlar | Beklenen sonuç | Platform |
|---|---|---|---|---|
| TC-APT-01 | Randevu alma | Klinik > branş > hekim > uygun saat seç; onayla | Randevu "Randevularım"da görünür | iOS, Android |
| TC-APT-02 | Dolu saat | Başka kullanıcının aldığı saati seç | "Bu saat artık uygun değil" uyarısı, liste yenilenir | iOS, Android |
| TC-APT-03 | Randevu iptali | Randevu detayı > "Randevuyu iptal et" | Randevu iptal edilir, ücret iadesi başlatılır | iOS, Android |
| TC-APT-04 | Check-in penceresi | Randevudan 31 dk ve 29 dk önce ekranı aç | 31 dk'da buton pasif, 29 dk'da aktif | iOS, Android |
| TC-APT-05 | Pencere kapanışı | Randevudan 16 dk sonra ekranı aç | Check-in butonu pasif, "Check-in süresi doldu" | iOS, Android |
| TC-APT-06 | Geri sayım | Randevu detayını aç | Kalan süre doğru ve dakikada bir güncellenir | iOS, Android |
| TC-APT-07 | Saat dilimi | Cihaz saat dilimini Europe/Berlin yap; 14:30 TSİ randevunun detayını aç | Randevu saati cihazın saat dilimine çevrilmiş gösterilir (ör. 13:30) | iOS, Android |
| TC-APT-08 | Hatırlatma push'u | Yarın 10:00 için randevu al (zamanlayıcı test modunda) | 24 saat ve 2 saat hatırlatmaları gelir | iOS, Android |

Not: Türkiye 2016'dan beri kalıcı olarak UTC+3 kullanmaktadır ve randevu saatleri klinik saat diliminde tutulur; bu nedenle yaz saati (DST) geçiş testleri kapsam dışıdır.

### 5.3 Otomatik varış (konum)

| ID | Senaryo | Adımlar | Beklenen sonuç | Platform |
|---|---|---|---|---|
| TC-LOC-01 | Otomatik varış açma | Ayarlar > Otomatik varış aç; izin diyaloğunda "Her Zaman İzin Ver" seç; simüle konumla klinik 150 m içine gir | "Kliniğe vardınız" bildirimi gelir | iOS, Android |
| TC-LOC-02 | İzin reddi | Otomatik varışı aç; konum iznini reddet | Otomatik varış kapalı kalır; randevu ekranında "Geldim, check-in yap" butonu ve açıklama görünür | iOS, Android |
| TC-LOC-03 | Yaklaşık konum | İzin diyaloğunda "Yaklaşık" seç | Otomatik varış kapalı kalır; "Geldim, check-in yap" ve kesin konum açıklaması görünür | Android 12+ |
| TC-LOC-04 | Konum servisleri kapalı | Cihazda konum servislerini kapat; otomatik varışı aç | Konum servislerini açma yönlendirmesi gösterilir | iOS, Android |
| TC-LOC-05 | Arka planda varış | "Her Zaman" izniyle uygulamayı arka plana al, ekranı kilitle, 10 dk bekle; simüle konumla klinik bölgesine gir | Bildirim gelir, dokununca check-in ekranı açılır | iOS, Android |

### 5.4 Belge yükleme

| ID | Senaryo | Adımlar | Beklenen sonuç | Platform |
|---|---|---|---|---|
| TC-DOC-01 | Kamera ile yükleme | Kamera iznini ver; fotoğraf çek; yükle | Belge "Belgelerim"de görünür | iOS, Android |
| TC-DOC-02 | Kamera izni reddi | Kamera iznini reddet | Galeri ve dosya seçeneği önerilir | iOS, Android |
| TC-DOC-03 | Depolama izni | İzni ver / reddet | Ver: galeri ızgarası açılır · Ret: sistem dosya seçici önerilir | Android 10–12 |
| TC-DOC-04 | Medya izni | `READ_MEDIA_IMAGES` iznini ver / reddet | Ver: galeri ızgarası açılır · Ret: sistem dosya seçici önerilir | Android 13+ |
| TC-DOC-05 | Galeriden seçim | Galeri > fotoğraf seç (PHPicker) | Seçici açılır, izin istemi çıkmaz; seçilen fotoğraf yüklenir | iOS |
| TC-DOC-06 | PDF yükleme | Dosya > PDF seç | PDF yüklenir, önizleme gösterilir | iOS, Android |
| TC-DOC-07 | Büyük dosya | 10,5 MB PDF seç | "Dosya 10 MB'tan büyük olamaz." hatası | iOS, Android |

### 5.5 Bildirimler

| ID | Senaryo | Adımlar | Beklenen sonuç | Platform |
|---|---|---|---|---|
| TC-PUSH-01 | Bildirim izni verme | İlk randevuyu oluştur; açıklama ekranında "Devam" > sistem isteminde izin ver | Hatırlatma push'ları gelir | iOS |
| TC-PUSH-02 | Bildirim izni reddi | Sistem isteminde reddet | Hatırlatmalar uygulama içi kutuda görünür; 2 saat kala SMS gelir | iOS |
| TC-PUSH-03 | Push'a dokunma | Uygulama ön planda / arka planda / kapalıyken hatırlatma push'una dokun | İlgili randevunun detayı açılır | iOS, Android |
| TC-PUSH-04 | Android bildirim alımı | Android'de bildirim izni kurulumla birlikte verildiğinden izin akışı yalnızca iOS'ta test edilir; Android'de push alımı ve dokunma davranışı TC-PUSH-03 ile kapsanır | Push'lar gelir | Android |
| TC-PUSH-05 | Zorla durdurulmuş uygulama | Ayarlar > Uygulamalar > PoyrazKlinik > "Zorla durdur"; hatırlatma tetikle; sonra uygulamayı aç | Zorla durdurulmuş uygulamaya push gelmemesi beklenen platform davranışıdır, hata olarak raporlanmaz. Uygulama açıldığında hatırlatma uygulama içi kutuda görünür | Android |

### 5.6 Çevrimdışı kuyruk

| ID | Senaryo | Adımlar | Beklenen sonuç | Platform |
|---|---|---|---|---|
| TC-OFF-01 | Çevrimdışı kayıt | Uçak modunu aç; semptom kaydı ekle | Kayıt "Bekliyor" rozetiyle listelenir | iOS, Android |
| TC-OFF-02 | Bağlantı dönüşü | 3 kayıt ekle; uçak modunu kapat | Kayıtlar oluşturulma sırasıyla gönderilir, rozetler kalkar | iOS, Android |
| TC-OFF-03 | Gönderimde bağlantı kesilmesi | 5 kayıtlık kuyruğun gönderimi sürerken uçak modunu aç | Gönderilemeyenler kuyrukta kalır, bağlantı dönünce gönderilir | iOS, Android |
| TC-OFF-04 | Arka plana alma | Gönderim sürerken Ana Ekran'a dön | Gönderim tamamlanır veya bir sonraki tetikleyicide devam eder | iOS, Android |
| TC-OFF-05 | Uygulama kapalıyken gönderim | Kuyrukta kayıt varken uygulamayı kapat (zorla durdurma dâhil); bağlantıyı aç | Android: WorkManager ile en geç 15 dakika içinde gönderilir · iOS: `BGAppRefreshTask` ile 15 dakikalık periyotlarla arka planda gönderilir | iOS, Android |
| TC-OFF-06 | Sunucu hatası | Staging'de 500 döndür (hata enjeksiyonu) | `retry_count` artar, kayıt kuyrukta kalır, kayıp olmaz | iOS, Android |
| TC-OFF-07 | Tekrarlı istek (API) | Postman ile aynı `idempotencyKey` taşıyan kaydı iki kez gönder | İlk yanıt 201, ikinci yanıt 200; sunucuda tek kayıt | API |

### 5.7 Ödeme

| ID | Senaryo | Adımlar | Beklenen sonuç | Platform |
|---|---|---|---|---|
| TC-PAY-01 | Başarılı ödeme | Sandbox başarılı test kartı + 3D Secure onayı | "Ödeme alındı", makbuz görünür | iOS, Android |
| TC-PAY-02 | 3D Secure başarısız | 3D Secure ekranında hatalı kod | "Ödeme tamamlanamadı", tekrar deneme seçeneği | iOS, Android |
| TC-PAY-03 | Yetersiz bakiye | Sandbox yetersiz bakiye kartı | Anlaşılır hata mesajı | iOS, Android |
| TC-PAY-04 | 3D Secure sırasında arka plan | 3D Secure ekranında uygulamayı arka plana al, 2 dk sonra dön | Ödeme durumu sunucudan sorgulanır, doğru sonuç gösterilir | iOS, Android |
| TC-PAY-05 | Ağ kesintisi | Onaydan hemen sonra uçak modunu aç, sonra kapat | Çift çekim olmaz; sonuç sunucudan sorgulanır | iOS, Android |

### 5.8 Derin bağlantılar

| ID | Senaryo | Adımlar | Beklenen sonuç | Platform |
|---|---|---|---|---|
| TC-DL-01 | Universal Link | SMS'teki `https://randevu.poyrazklinik.example/r/{kod}` bağlantısına dokun | Uygulama açılır, randevu detayı gösterilir | iOS |
| TC-DL-02 | App Link | Aynı bağlantıya dokun | Uygulama doğrudan açılır, randevu detayı gösterilir | Android |
| TC-DL-03 | Doğrulama başarısız | Alan adı doğrulaması başarısız olduğunda bağlantıya dokun | Sistem "Birlikte aç" seçim penceresini gösterir; PoyrazKlinik seçilince randevu detayı açılır | Android 12+ |
| TC-DL-04 | Süresi dolmuş kod | 72 saatten eski bağlantıya dokun | "Bu bağlantının süresi doldu" | iOS, Android |
| TC-DL-05 | Uygulama yüklü değil | Uygulamayı kaldır; bağlantıya dokun | Web sayfası açılır; "Uygulamada aç" ve mağaza bağlantısı görünür | iOS, Android |

Derin bağlantı testleri QA derlemeleriyle yapılır; Android App Links doğrulaması TC-DL-02 ile kapsanmıştır.

### 5.9 Sürüm yükseltme

| ID | Senaryo | Adımlar | Beklenen sonuç | Platform |
|---|---|---|---|---|
| TC-UPG-01 | 4.2 → 4.3 yükseltme | 4.2'de giriş yap, randevu ve belge oluştur, kuyrukta 2 kayıt bırak; 4.3'ü üzerine kur | Oturum, randevular, belgeler, kuyruk ve ayarlar korunur; şema 6 → 7 göçü hatasız | iOS, Android |

Kullanıcıların büyük çoğunluğu 4.2'de olduğundan yükseltme testi 4.2'den yapılır.

### 5.10 Erişilebilirlik

| ID | Senaryo | Adımlar | Beklenen sonuç | Platform |
|---|---|---|---|---|
| TC-A11Y-01 | Ekran okuyucu | VoiceOver / TalkBack ile randevu al | Tüm öğeler etiketli, odak sırası mantıklı | iOS, Android |
| TC-A11Y-02 | En büyük yazı boyutu | iOS: Daha Büyük Erişilebilirlik Boyutları en üst; Android: yazı boyutu en büyük. Ana ekranlar, randevu detayı, ödeme | Metinler kesilmez, butonlar taşmaz | iOS, Android |
| TC-A11Y-03 | Kontrast | Renk kontrastını araçla ölç | Metin kontrastı ≥ 4.5:1 | iOS, Android |

Not: TC-A11Y-02 cihaz dili İngilizce yapılarak koşulur; en uzun arayüz metinleri İngilizce olduğundan en kötü durumu temsil eder.

## 6. Cihaz matrisi

**Kapsama yöntemi.** Kapsama, cihaz kullanım verisindeki (Ağustos 2026) model + OS ana sürümü satırlarının aktif kullanıcı sayıları üzerinden hesaplanır. Bir test cihazı yalnızca kendi model + OS ana sürümü satırını kapsar. Payda, 4.3'ün desteklediği kullanıcılardır (iOS 16+ iPhone; Android 10+ telefon): **Android 89.100**, **iOS 62.700**. Hedef: platform başına ≥ %80.

### 6.1 Android

| # | Model | OS | Kapsanan kullanıcı |
|---|---|---|---|
| 1 | Samsung Galaxy A54 | 15 | 18.500 |
| 2 | Xiaomi Redmi Note 12 | 14 | 9.800 |
| 3 | Samsung Galaxy A34 | 15 | 8.900 |
| 4 | Xiaomi Redmi Note 13 | 14 | 8.100 |
| 5 | Samsung Galaxy A14 | 14 | 6.900 |
| 6 | Samsung Galaxy A13 | 14 | 6.200 |
| 7 | Xiaomi Redmi Note 11 | 13 | 5.600 |
| 8 | Samsung Galaxy A10 | 11 | 8.300 |
| 9 | Samsung Galaxy Tab A8 | 14 | 4.700 |
| | **Toplam** | | **77.000 / 89.100 = %86,4** |

### 6.2 iOS

| # | Model | OS | Kapsanan kullanıcı |
|---|---|---|---|
| 1 | iPhone 13 | 26 | 13.300 |
| 2 | iPhone 15 | 26 | 8.700 |
| 3 | iPhone 14 | 26 | 8.100 |
| 4 | iPhone 11 | 26 | 9.900 |
| 5 | iPhone 12 | 26 | 6.200 |
| 6 | iPhone 8 | 16 | 2.600 |
| 7 | iPad (9. nesil) | 18 | 3.600 |
| | **Toplam** | | **52.400 / 62.700 = %83,6** |

Notlar:
- Galaxy A10 ve iPhone 8, en eski donanım ve en düşük OS davranışını görmek için matristedir.
- Galaxy Tab A8 ve iPad (9. nesil) cihaz parkımızda bulunduğu için matrise eklenmiştir.
- Her test durumu matristeki tüm cihazlarda koşulmaz; P1 senaryoları tüm cihazlarda, diğerleri platform başına en az 3 cihazda koşulur.

## 7. Kapsam dışı

- iPad ve Android tablet arayüz testleri (ürün tarafından desteklenmiyor).
- Yaz saati (DST) geçiş testleri (bkz. 5.2 notu).
- Ödeme kuruluşunun 3D Secure sayfasının içeriği ve tasarımı.
- Performans/yük testleri (ayrı planda).

## 8. Giriş ve çıkış kriterleri

- **Giriş:** QA derlemeleri staging'e bağlı; özellik geliştirmesi tamamlandı; duman seti geçti.
- **Çıkış:** Açık P1 hata yok; P2 hataların her biri için düzeltme veya ürün onaylı istisna var; P1 test durumlarının %100'ü, tüm test durumlarının ≥ %95'i koşuldu.

## 9. Takvim

| Tarih | Etkinlik |
|---|---|
| 28 Eylül – 3 Ekim | Fonksiyonel testler (5.1–5.6) |
| 4 – 8 Ekim | Ödeme, derin bağlantı, yükseltme, erişilebilirlik (5.7–5.10) |
| 9 – 10 Ekim | Regresyon ve çıkış değerlendirmesi |
| 13 Ekim | Mağaza gönderimi |
