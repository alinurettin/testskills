# PoyrazKlinik Mobil — Ürün Özeti (v4.3)

| Alan | Değer |
|---|---|
| Belge sahibi | Ürün Yönetimi, Poyraz Sağlık Teknolojileri A.Ş. |
| Belge sürümü | 3.1 (onaylı) |
| Hedef yayın | 20 Ekim 2026 (mağaza gönderimi: 13 Ekim 2026) |
| Uygulama kimliği | iOS: `com.poyrazklinik.app` · Android: `com.poyrazklinik.app` |

> Bu belgedeki şirket, alan adı, kişi, anahtar ve kullanıcı verileri kurgusaldır. Alan adları `*.example` uzantılıdır.

---

## 1. Ürün

PoyrazKlinik, anlaşmalı özel polikliniklerde randevu alma, kliniğe varışta check-in, tahlil sonucu/reçete gibi belgeleri yükleme, katkı payı ödeme ve semptom günlüğü tutma işlevlerini sunan bir hasta uygulamasıdır. Uygulama iOS ve Android için yerel (native) olarak geliştirilir.

## 2. Platformlar ve desteklenen cihazlar

| | 4.0 / 4.1 | 4.2 (mağazadaki sürüm) | **4.3 (bu sürüm)** |
|---|---|---|---|
| iOS en düşük sürüm | 15.0 | 15.0 | **16.0** |
| Android en düşük sürüm | 8.0 (API 26) | 9 (API 28) | **10 (API 29)** |

- **iOS:** Yalnızca iPhone. Uygulama iPad için hedeflenmez; iPad'de uyumluluk modunda açılabilse de iPad'ler destek ve test kapsamı dışındadır.
- **Android:** Yalnızca telefonlar. Android tabletler destek ve test kapsamı dışındadır (arayüz tablete uyarlanmadı).
- Android derleme: `compileSdk 36`, `targetSdk 36`. iOS derleme: Xcode 26.
- 4.3'ün en düşük OS sürümünün altında kalan kullanıcılar 4.2'de kalır; 4.2, sunucu tarafında en az 31 Mart 2027'ye kadar desteklenir.
- Dil: Türkçe (varsayılan; kullanıcıların %96'sı) ve İngilizce.
- Cihaz kullanım verisi: `cihaz_kullanim_2026-08.csv` (son 28 günün aktif kullanıcıları, model + OS ana sürümü kırılımında).

## 3. Sürüm dağılımı ve yerel veri

Aktif kullanıcıların uygulama sürümü dağılımı (Ağustos 2026):

| Sürüm | Pay |
|---|---|
| 4.2 | %71 |
| 4.1 | %17 |
| 4.0 | %12 |

4.0'dan eski sürümler açılışta zorunlu güncelleme ekranına yönlendirilir.

Yerel veritabanı (SQLite) şema sürümleri:

| Uygulama sürümü | Şema |
|---|---|
| 4.0 | 4 |
| 4.1 | 5 |
| 4.2 | 6 |
| 4.3 | 7 |

Göçler (migration) zincirleme çalışır: örneğin 4.0'dan 4.3'e geçen bir kullanıcıda 4 → 5 → 6 → 7 sırasıyla uygulanır.
- 4 → 5 (4.1): semptom günlüğü tablosu `symptom_log` → `symptom_entries` olarak yeniden adlandırıldı.
- 5 → 6 (4.2): belge tablosuna `mime_type` sütunu eklendi.
- 6 → 7 (4.3): çevrimdışı kuyruk tablosuna `retry_count` sütunu eklenir; biyometrik giriş tercihi SharedPreferences/UserDefaults'tan veritabanına taşınır.

## 4. Özellikler

### 4.1 Giriş ve biyometrik doğrulama

- Telefon numarası + şifre ile giriş; ardından isteğe bağlı biyometrik giriş (Face ID / Touch ID; Android'de BiometricPrompt, Class 3).
- Oturum yenileme belirteci (refresh token) cihazda şifreli saklanır:
  - Android: Android Keystore anahtarı, `setUserAuthenticationRequired(true)` ve `setInvalidatedByBiometricEnrollment(true)` ile oluşturulur.
  - iOS: Keychain öğesi, `SecAccessControl` + `.biometryCurrentSet` ile korunur.
- Cihaza yeni bir parmak izi/yüz eklendiğinde ya da biyometrik kayıtlar silindiğinde anahtar geçersizleşir. Bu durumda uygulama çökmemeli, kullanıcıyı kilitlememeli; "Biyometrik bilgileriniz değişti. Güvenliğiniz için şifrenizle giriş yapın." mesajını göstermeli ve şifreyle girişten sonra biyometrik girişi yeniden etkinleştirmeyi önermelidir.
- Art arda 3 başarısız biyometrik denemede şifre ekranına geçilir.

### 4.2 Randevular ve saatler

- Randevu saatleri sunucuda UTC olarak saklanır. Uygulama randevu saatlerini **her zaman kliniğin saat diliminde (Europe/Istanbul)** ve saatin yanında "TSİ" ibaresiyle gösterir. Cihazın saat dilimi veya saati değişse de gösterilen randevu saati değişmez (kullanıcı yurt dışındayken de klinik saatini görmelidir).
- Check-in penceresi randevudan 30 dakika önce açılır, randevu saatinden 15 dakika sonra kapanır. Geri sayım ve check-in penceresi **sunucu saatine** göre hesaplanır (uygulama her ön plana gelişte `/v2/time` ile saat farkını günceller); cihaz saati yanlış ayarlı olsa bile doğru çalışmalıdır.
- Randevu hatırlatmaları (24 saat ve 2 saat kala) sunucudan push bildirimi olarak gönderilir; cihazda yerel bildirim zamanlanmaz.

### 4.3 Otomatik varış (konum)

- Kullanıcı Ayarlar > "Otomatik varış" seçeneğini açtığında, randevu günü klinik çevresinde 150 m yarıçaplı bir coğrafi bölge (geofence) kaydedilir. Bölgeye girildiğinde "Kliniğe vardınız. Check-in yapalım mı?" bildirimi gösterilir.
- Gereken izinler:
  - iOS: Konum "Her Zaman" + "Kesin Konum" açık.
  - Android: `ACCESS_FINE_LOCATION` + `ACCESS_BACKGROUND_LOCATION`.
- İzin akışı: önce ön plan (foreground) konum izni istenir; verilirse arka plan izni için açıklama ekranı gösterilir ve kullanıcı sistemin yönlendirdiği adıma (iOS'ta yükseltme istemi, Android'de ayarlar sayfası) gönderilir.
- Gereken izin seviyesi yoksa (yalnızca "Uygulamayı Kullanırken", "Bir Kez İzin Ver", yaklaşık konum veya ret) otomatik varış kapalı kalır; randevu ekranında **"Geldim, check-in yap"** butonu ile manuel check-in yapılır ve kullanıcıya eksik izin açıklanır. Bu kural iOS ve Android için aynıdır.

### 4.4 Belge yükleme

- Kaynaklar: kamera, galeri, dosya (PDF).
- Kamera: iOS `NSCameraUsageDescription`; Android `CAMERA` izni.
- Galeri:
  - **iOS:** Sistem fotoğraf seçicisi `PHPickerViewController` kullanılır. Fotoğraf kitaplığı izni **istenmez**; `Info.plist` içinde `NSPhotoLibraryUsageDescription` anahtarı yoktur.
  - **Android:** Uygulamanın kendi galeri ekranı (son fotoğraflar ızgarası, çoklu seçim) kullanılır. İzinler: Android 10–12 için `READ_EXTERNAL_STORAGE`; Android 13 ve üzeri için `READ_MEDIA_IMAGES`; ayrıca manifestte `READ_MEDIA_VISUAL_USER_SELECTED` bildirilmiştir.
  - Galeri izninin sonucu ne olursa olsun (tam, kısmi veya ret) kullanıcı belge yükleyebilmelidir; ret durumunda sistem dosya seçici önerilir.
- Dosya: Android'de sistem dosya seçici (SAF), iOS'ta `UIDocumentPickerViewController`.
- Kabul edilen türler: JPEG, PNG, PDF. En büyük boyut: 10 MB.

### 4.5 Bildirimler

- Push altyapısı: Android'de FCM, iOS'ta APNs.
- Bildirim izni (iOS ve Android 13+) ilk açılışta değil, **ilk randevu oluşturulduktan sonra** bağlamsal bir açıklama ekranıyla istenir.
- Bildirim izni yoksa hatırlatmalar uygulama içi "Bildirimler" kutusunda gösterilir ve 2 saat kala hatırlatma SMS ile de gönderilir.
- Push bildirimine dokunulduğunda ilgili randevunun detayı açılır.

### 4.6 Çevrimdışı kuyruk

- Semptom günlüğü kayıtları, belge yüklemeleri ve manuel check-in, bağlantı yoksa yerel kuyruğa (SQLite, `offline_queue`) yazılır ve kullanıcıya "Bekliyor" rozeti gösterilir.
- Her kayıt oluşturulduğu anda istemci bir `idempotencyKey` (UUID v4) üretir ve kayıtla birlikte saklar. Aynı kayıt kaç kez gönderilirse gönderilsin aynı anahtar kullanılır.
- Gönderim sırası FIFO'dur. Sunucu `201 Created` (yeni kayıt) veya `200 OK` (bu anahtarla gelen kayıt daha önce işlenmiş) döndüğünde kayıt kuyruktan silinir. Diğer yanıtlarda `retry_count` artırılır ve kayıt kuyrukta kalır.
- Gönderim tetikleyicileri: uygulama ön plana geldiğinde; bağlantı geri geldiğinde; arka planda Android'de WorkManager (ağ kısıtlı periyodik iş, 15 dk), iOS'ta `BGAppRefreshTask` (zamanlamayı sistem belirler).
- Çevrimdışı alınan check-in kaydının zaman damgası, cihaz saatine son bilinen sunucu saati farkı uygulanarak yazılır.

### 4.7 Ödeme

- Katkı payı kredi/banka kartı ile ödenir. Ödeme kuruluşu: ÖdeKolay (kurgusal). Kart bilgisi uygulamada saklanmaz; kart formu ve 3D Secure doğrulaması ödeme kuruluşunun web görünümünde açılır.
- 3D Secure dönüşü `https://randevu.poyrazklinik.example/odeme/sonuc` adresine yapılır; uygulama sonucu sunucudan sorgular (istemci tarafındaki yönlendirme sonucu tek başına esas alınmaz).

### 4.8 Derin bağlantılar

- SMS ve e-postalardaki randevu bağlantıları: `https://randevu.poyrazklinik.example/r/{kod}` (kod 72 saat geçerlidir).
- iOS: Universal Links (`applinks:randevu.poyrazklinik.example`). Android: App Links (`android:autoVerify="true"`).
- Beklenen davranış:
  - Uygulama yüklü ve bağlantı doğrulanmış → uygulama açılır, randevu detayı gösterilir.
  - Uygulama yüklü değil **veya** alan adı doğrulaması başarısız → bağlantı tarayıcıda açılır; web sayfası randevu özetini, **"Uygulamada aç"** butonunu (`poyrazklinik://r/{kod}`) ve mağaza bağlantısını gösterir.
  - Süresi dolmuş kod → "Bu bağlantının süresi doldu" sayfası/ekranı.

**Android imzalama.** Play Uygulama İmzalama (Play App Signing) kullanılır.

| Anahtar | Nerede kullanılır | SHA-256 sertifika parmak izi |
|---|---|---|
| Yükleme anahtarı (upload key) | QA derlemeleri (Firebase App Distribution) ve Play Console'a yüklenen paketler | `07:A5:55:FB:96:CD:6F:D7:E7:14:B9:C0:1C:EE:1F:C6:C9:73:5E:2D:52:E5:64:84:D1:B7:40:F5:6E:74:3E:6F` |
| Uygulama imzalama anahtarı (Google Play) | Google Play'den indirilen tüm kurulumlar | `56:89:17:50:C5:96:CC:C8:0C:60:3C:19:4A:09:3A:99:EE:F8:B3:82:91:86:51:E3:BF:EA:7B:C1:D9:13:4A:D4` |

Web ekibinin yayındaki `https://randevu.poyrazklinik.example/.well-known/assetlinks.json` içeriği:

```json
[
  {
    "relation": ["delegate_permission/common.handle_all_urls"],
    "target": {
      "namespace": "android_app",
      "package_name": "com.poyrazklinik.app",
      "sha256_cert_fingerprints": [
        "07:A5:55:FB:96:CD:6F:D7:E7:14:B9:C0:1C:EE:1F:C6:C9:73:5E:2D:52:E5:64:84:D1:B7:40:F5:6E:74:3E:6F"
      ]
    }
  }
]
```

Yayındaki `https://randevu.poyrazklinik.example/.well-known/apple-app-site-association` içeriği:

```json
{
  "applinks": {
    "details": [
      {
        "appIDs": ["K7PQ2ZX9LM.com.poyrazklinik.app"],
        "components": [
          { "/": "/r/*", "comment": "Randevu bağlantıları" }
        ]
      }
    ]
  }
}
```

### 4.9 Erişilebilirlik ve yerelleştirme

- Hedef: WCAG 2.2 AA. iOS Dynamic Type (Daha Büyük Erişilebilirlik Boyutları dâhil) ve Android yazı boyutu/ekran boyutu ayarları desteklenir. Metinler kısaltılmadan (üç nokta olmadan) okunabilir kalmalı, butonlar ekrandan taşmamalıdır.
- Temel arayüz metinleri:

| Anahtar | Türkçe | İngilizce |
|---|---|---|
| `btn_checkin` | Geldim, check-in yap | I'm here |
| `btn_confirm_appt` | Randevuyu onayla | Confirm |
| `btn_cancel_appt` | Randevuyu iptal et | Cancel |
| `btn_upload` | Belge yükle | Upload |
| `btn_pay` | Katkı payını öde | Pay |
| `tab_appointments` | Randevularım | Appointments |
| `tab_documents` | Belgelerim | Documents |
| `tab_settings` | Ayarlar | Settings |
| `msg_bio_changed` | Biyometrik bilgileriniz değişti. Güvenliğiniz için şifrenizle giriş yapın. | Your biometrics changed. Sign in with your password. |
| `msg_loc_reason` | Otomatik varış için konum iznini "Her Zaman" ve "Kesin Konum" olarak ayarlayın. | For auto check-in, set location to "Always" and "Precise". |
| `msg_notif_reason` | Randevu hatırlatmalarını kaçırmamak için bildirimlere izin verin. | Allow notifications for appointment reminders. |
| `err_file_too_large` | Dosya 10 MB'tan büyük olamaz. | File must be under 10 MB. |
