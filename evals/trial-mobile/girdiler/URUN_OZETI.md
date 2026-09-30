# Bakkalix v3.0 — Mobil Uygulama Ürün Özeti

| | |
|---|---|
| Şirket | Bakkalix Teknoloji A.Ş. (kurgusal) |
| Belge sahibi | Ürün Yönetimi — Deniz Karaca |
| Sürüm | 3.0 (hedef mağaza yayını: 20 Ekim 2026) |
| Son güncelleme | 12.09.2026 |

## 1. Ürün

Bakkalix, anlaşmalı mahalle marketlerinden ortalama 30 dakikada teslimat yapan bir market alışverişi ve dijital cüzdan uygulamasıdır. Kullanıcılar sipariş verir, Bakkalix Cüzdan'a bakiye yükler ve anlaşmalı fiziksel mağazalarda kasadaki QR kodu okutarak öder.

- 30 günlük aktif kullanıcı: yaklaşık 400.000 (Android %62, iOS %38).
- Aktif kullanıcıların uygulama sürümü dağılımı: %71 v2.8.x, %24 v2.9.x, %5 daha eski.
- Cihaz ve işletim sistemi dağılımı: ekteki `cihaz_os_dagilimi.csv` (Ağustos 2026, son 30 gün aktif kullanıcı, analitik dışa aktarımı).

## 2. Desteklenen platformlar

- **iOS 16.0 ve üzeri** — iPhone ve iPad.
- **Android 9.0 (API 28) ve üzeri** — telefon, tablet ve katlanabilir cihazlar. `targetSdkVersion` 36.
- Telefonlarda ve katlanabilir cihazların dış ekranında uygulama **yalnız dikey** çalışır. Tabletlerde ve katlanabilir cihazların iç ekranında dikey ve yatay desteklenir.
- iOS 15 ve Android 8.x cihazlar v3.0'ı mağazada göremez; bu kullanıcılar v2.8.x'te kalır (backend v2.8 API'sini 2027 sonuna kadar destekler).
- Dil: yalnız Türkçe. Para birimi: TL.

## 3. Özellikler (v3.0)

### 3.1 Giriş ve oturum

- Telefon numarası + SMS ile gelen 6 haneli tek kullanımlık kod (OTP, 120 sn geçerli). 3 hatalı denemeden sonra 5 dakika bekleme.
- iOS'ta SMS kodu klavye önerisiyle, Android'de SMS User Consent API ile otomatik doldurulur.
- İlk girişten sonra biyometrik giriş önerilir (Face ID / Touch ID; Android'de BiometricPrompt, güçlü/Class 3 biyometri).
- Biyometrik doğrulama 5 kez başarısız olursa veya biyometri sistem tarafından kilitlenirse kullanıcıdan 6 haneli **Bakkalix PIN'i** istenir. Cihazın ekran kilidi şifresiyle geçiş **bilinçli olarak sunulmaz** (Güvenlik kararı GÜV-114: cihaz şifresini bilen üçüncü kişilerin cüzdana erişimini engellemek).
- Erişim tokenı 15 dakika, yenileme tokenı 30 gün geçerlidir.
- v3.0 ile tokenlar iOS'ta UserDefaults'tan Keychain'e, Android'de SharedPreferences'tan Android Keystore ile şifrelenmiş depoya taşınır.

### 3.2 Arama ve katalog

- Arama Türkçe büyük/küçük harf kurallarını uygular (I ↔ ı, İ ↔ i).
- Türkçe karakter kullanılmadan yazılan aramalar (ör. `sut`, `INCIR`) doğrudan eşleştirilmez; sonuç sayfasında "Bunu mu demek istediniz: süt / incir" önerisi gösterilir (Arama ekibi kararı ARA-31, alaka puanı gerekçesiyle).
- Ürün görselleri cihazda önbelleğe alınır (en fazla 150 MB).

### 3.3 Sepet (çevrimdışı çalışma)

- İnternet bağlantısı yokken sepete ürün eklenip çıkarılabilir; bağlantı gelince sepet sunucuyla eşitlenir. Eşitleme sırasında fiyat veya stok değişmişse kullanıcıya gösterilir.
- Sipariş vermek için bağlantı gerekir; çevrimdışı sipariş kuyruğu yoktur.
- v3.0'da yerel sepet deposu yeniden yazıldı: v2.x'teki SQLite `sepet` tablosu (fiyat TL, ondalıklı sayı) uygulamanın ilk açılışında yeni şemaya (`cart_items`, fiyat kuruş cinsinden tam sayı) taşınır.

### 3.4 Adres ve konum

- Konum izni yalnız "uygulamayı kullanırken" istenir; arka plan konumu kullanılmaz.
- Konum, en yakın mağazayı bulmak ve teslimat adresi için harita pinini önermek amacıyla kullanılır.
- Kullanıcı yalnız yaklaşık konum paylaşırsa (iOS'ta "Kesin Konum" kapalı, Android'de "Yaklaşık") mağaza yine bulunur; teslimat pini haritada kullanıcıya elle düzelttirilir.
- Konum izni verilmezse adres elle girilir.

### 3.5 Ödeme

- Yöntemler: kredi/banka kartı (3D Secure), Bakkalix Cüzdan bakiyesi, kapıda ödeme (nakit veya kart).
- 3D Secure doğrulaması uygulama içi web görünümünde açılır. Bazı bankalar kullanıcıyı kendi mobil uygulamasına yönlendirir; kullanıcı onay verdikten sonra Bakkalix'e döner ve ödeme akışı kaldığı yerden devam eder.
- Her ödeme denemesi, istemcinin ürettiği `odeme_istek_no` (UUID) ile gönderilir. Sunucu aynı `odeme_istek_no` ile gelen tekrar isteklerde yeni çekim yapmaz, ilk isteğin sonucunu döner.
- Uygulama içi satın alma (App Store / Google Play Billing) **kullanılmaz**: uygulamada dijital ürün veya abonelik satılmaz; tüm ödemeler fiziksel ürün ve teslimat içindir.
- Cüzdana bakiye yükleme yalnız kartla yapılır; en az 50 TL, en fazla 5.000 TL.

### 3.6 Kasada QR ile öde

- Anlaşmalı mağazada kasanın ekranında gösterilen dinamik QR kod (60 sn geçerli) kamera ile okutulur, tutar onaylanır ve cüzdandan ödenir.
- Özellik yalnız telefonlarda sunulur; tablette menüde görünmez.
- Kamera izni ilk QR denemesinde istenir.

### 3.7 Bildirimler

- Sipariş durumu (hazırlanıyor, yolda, teslim edildi), "kurye yaklaştı" ve kampanya bildirimleri (kampanyalar yalnız pazarlama izni verilmişse).
- Bildirim izni, kullanıcının ilk siparişi tamamlandığında istenir (onboarding sırasında değil).
- Bildirime dokunulduğunda ilgili sipariş detayı açılır.

### 3.8 SMS kampanyaları ve derin bağlantılar

- Kampanya SMS'lerinde `https://bakkalix.example.com/...` bağlantıları gönderilir (iOS Universal Links, Android App Links). Uygulama yüklü değilse aynı adres web sitesinde açılır.
- Desteklenen yollar:

| Yol | Açılan ekran | Oturum gerekir mi? |
|---|---|---|
| `/k/{kampanya_kodu}` | Kampanya sayfası | Hayır |
| `/urun/{urun_id}` | Ürün detayı | Hayır |
| `/siparis/{siparis_no}` | Sipariş detayı | Evet |
| `/cuzdan/yukle?tutar={tl}` | Cüzdana bakiye yükleme (tutar önceden dolu) | Evet |

- Oturum gerektiren bir yol oturum yokken açılırsa önce giriş istenir; girişten sonra hedef ekrana devam edilir. Kullanıcı yalnız kendi siparişlerini görebilir.

### 3.9 Ölçümleme ve rıza

- SMS kampanyalarının dönüşümünü ölçmek için üçüncü taraf atıf SDK'sı **OlcumPro** (kurgusal) kullanılır. SDK iOS'ta reklam kimliğini (IDFA), Android'de reklam kimliğini (AAID) okur.
- KVKK aydınlatma metni ve pazarlama açık rızası onboarding'de ayrı bir ekranda alınır. Pazarlama rızası verilmezse kampanya bildirimi ve SMS gönderilmez.

### 3.10 Erişilebilirlik

- Hedef: WCAG 2.1 AA.
- Sistem yazı boyutu büyütüldüğünde (iOS Dinamik Yazı, Android yazı boyutu %200'e kadar) metinler kesilmemeli, butonlar erişilebilir kalmalı.
- VoiceOver ve TalkBack ile sipariş baştan sona verilebilmeli.

### 3.11 Güncelleme

- v2.5'in altındaki sürümler açılışta zorunlu güncelleme ekranı görür (sunucu tarafı ayar).
- v2.8.x ve v2.9.x'ten v3.0'a mağaza güncellemesinde kullanıcının oturumu, sepeti, kayıtlı adresleri ve biyometrik giriş tercihi korunmalıdır (bkz. 3.1 ve 3.3).

### 3.12 Performans

- Soğuk açılış, orta segment cihazda 2,5 saniyenin altında olmalı.
