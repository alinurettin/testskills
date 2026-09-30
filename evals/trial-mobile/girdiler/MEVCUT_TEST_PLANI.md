# Bakkalix v3.0 Mobil Test Planı

| | |
|---|---|
| Durum | Taslak v0.4 |
| Hazırlayan | Mobil QA ekibi — Selin Aydemir, Burak Tunç |
| Tarih | 15.09.2026 |
| İlgili belge | Bakkalix v3.0 Ürün Özeti (12.09.2026) |

## 1. Amaç ve kapsam

Bakkalix v3.0 iOS ve Android uygulamalarının mağaza yayını öncesi fonksiyonel, uyumluluk ve temel performans testleri.

**Kapsamda:** giriş ve oturum, biyometrik giriş, arama, çevrimdışı sepet, adres ve konum, kartla ödeme ve 3D Secure, cüzdan, kasada QR ile ödeme, bildirimler, SMS derin bağlantıları, KVKK rızası, temel erişilebilirlik ve performans.

**Kapsam dışı:**

- Uygulama içi satın alma (StoreKit / Google Play Billing): uygulamada IAP yoktur; tüm ödemeler fiziksel ürün ve teslimat içindir (Ürün Özeti §3.5).
- Telefonlarda yatay mod: uygulama telefonlarda dikey kilitlidir (Ürün Özeti §2). Yatay mod yalnız tablet ve katlanabilir iç ekranda test edilir (MT-27).
- Sunucu yük ve dayanıklılık testleri (ayrı plan: PERF-12).
- bakkalix.example.com web sitesinin kendisi; yalnız derin bağlantıların web'e düşmesi kapsamdadır.

## 2. Test ortamı

- API: `https://api.test.bakkalix.example.com` (test ortamı). Kart testleri ödeme sağlayıcısının sandbox test kartlarıyla yapılır.
- OTP kodları test ortamında SMS sandbox panelinden (`https://sms.test.bakkalix.example.com`) okunur.
- **Hazırlık:** Her test koşusundan önce uygulama cihazdan silinir ve v3.0 RC derlemesi test dağıtımından (TestFlight / Firebase App Distribution) temiz kurulum olarak yüklenir. Böylece önceki sürümlerden kalan veriler test sonuçlarını etkilemez.
- Emülatör / simülatör: arayüz ve akış testleri. Gerçek cihaz zorunlu: kamera/QR, biyometri, push bildirimleri, 3D Secure'da banka uygulamasına geçiş.
- Ağ koşulları: Wi-Fi, 4.5G, kısıtlı ağ (iOS Network Link Conditioner, Android emülatör ağ profilleri), uçak modu.

## 3. Cihaz matrisi

| # | Cihaz | Platform | OS | Tip | Seçim nedeni |
|---|---|---|---|---|---|
| D1 | iPhone 16 Pro | iOS | 26 | telefon | En yeni amiral gemisi |
| D2 | iPhone 15 | iOS | 26 | telefon | En çok kullanılan iPhone modeli |
| D3 | iPhone 12 | iOS | 18 | telefon | Önceki iOS sürümü |
| D4 | Samsung Galaxy S25 | Android | 16 | telefon | En yeni Android sürümü |
| D5 | Samsung Galaxy A55 | Android | 15 | telefon | En çok kullanılan Android modeli |
| D6 | Samsung Galaxy Tab A9+ | Android | 15 | tablet | Tablet düzeni |
| D7 | Samsung Galaxy A34 | Android | 14 | telefon | Orta segment, performans ölçümü |

Bu matris, analitik verisine göre işletim sistemi sürümü bazında iOS kullanıcılarının **%91**'ini, Android kullanıcılarının **%83**'ünü kapsamaktadır. Eski sürümlerin (iOS 17 altı, Android 13 altı) toplam payı düşük olduğundan matrise alınmamıştır.

## 4. Test senaryoları

Öncelik: P1 = yayın engelleyici, P2 = önemli, P3 = düşük. Ortam: Emü/Sim = emülatör veya simülatör, Gerçek = gerçek cihaz.

| ID | Alan | Senaryo / adımlar | Beklenen sonuç | Öncelik | Ortam |
|---|---|---|---|---|---|
| MT-01 | Giriş | Geçerli telefon numarası ve SMS kodu ile giriş yap | Ana sayfa açılır, oturum oluşur | P1 | Emü/Sim |
| MT-02 | Giriş | Arka arkaya 3 kez hatalı SMS kodu gir | Her denemede "Kod hatalı" mesajı; 3. denemeden sonra 5 dakika bekleme uyarısı | P1 | Emü/Sim |
| MT-03 | Giriş | SMS kodu gelince otomatik doldurmayı kullan (iOS klavye önerisi, Android SMS User Consent) | Kod alanı otomatik dolar, giriş tamamlanır | P2 | Gerçek |
| MT-04 | Biyometri | Girişten sonra biyometrik girişi etkinleştir; uygulamayı kapatıp aç; Face ID / Touch ID / parmak izi ile giriş yap | SMS kodu sorulmadan giriş yapılır | P1 | Gerçek |
| MT-05 | Biyometri | Biyometrik doğrulamayı 5 kez başarısız yap | 6 haneli Bakkalix PIN ekranı açılır; cihaz ekran kilidi şifresi seçeneği gösterilmez | P1 | Gerçek |
| MT-06 | Oturum | Erişim tokenının süresi (15 dk) dolduktan sonra sepete ürün ekle | Token yenileme tokenıyla sessizce yenilenir; kullanıcı giriş ekranına düşmez | P1 | Emü/Sim |
| MT-07 | Oturum | Profil > Çıkış yap | Tokenlar ve kişisel veriler cihazdan silinir; giriş ekranı açılır | P1 | Emü/Sim |
| MT-08 | Arama | Sırasıyla `ISPANAK`, `İNCİR` ve `INCIR` ara | `ISPANAK` → Ispanak ürünleri listelenir; `İNCİR` → İncir ürünleri listelenir; `INCIR` → doğrudan sonuç yok, "Bunu mu demek istediniz: incir" önerisi görünür | P2 | Emü/Sim |
| MT-09 | Sepet | Uçak modunda sepete 3 ürün ekle, 1 ürün çıkar | Sepet güncellenir; "Çevrimdışısınız" bandı görünür | P1 | Emü/Sim |
| MT-10 | Sepet | Çevrimdışı eklenen bir ürünün fiyatını test panelinden değiştir, ardından bağlantıyı aç | Eşitleme sonrası fiyat değişikliği uyarısı gösterilir, sepet toplamı güncellenir | P1 | Emü/Sim |
| MT-11 | Sepet | Çevrimdışıyken "Siparişi tamamla"ya bas | "Sipariş için internet bağlantısı gerekli" mesajı; sepet korunur | P2 | Emü/Sim |
| MT-12 | Konum | Konum iznini "Uygulamayı kullanırken" olarak ver | En yakın mağaza bulunur, teslimat pini otomatik yerleşir | P1 | Gerçek |
| MT-13 | Konum | Konum iznini reddet | Adres elle girilebilir; mağaza girilen adrese göre bulunur | P1 | Gerçek |
| MT-14 | Ödeme | Kartla öde, 3D Secure doğrulaması uygulama içi web görünümünde başarılı | Sipariş onay ekranı açılır; sipariş durumu "Hazırlanıyor" | P1 | Gerçek |
| MT-15 | Ödeme | 3D Secure ekranında hatalı SMS kodu gir | "Ödeme başarısız" mesajı; sepet korunur; karttan çekim yapılmaz | P1 | Gerçek |
| MT-16 | Ödeme | 3D Secure'da banka kendi uygulamasına yönlendirir; bankada onay ver ve Bakkalix'e dön | Ödeme akışı devam eder, sipariş onay ekranı açılır | P1 | Gerçek |
| MT-17 | Ödeme | "Öde"ye bastıktan hemen sonra bağlantıyı kes; "Bağlantı hatası" mesajı çıkınca bağlantıyı aç ve "Tekrar dene"ye bas | Ödeme tamamlanır, sipariş onay ekranı açılır | P1 | Gerçek |
| MT-18 | Ödeme | Kart bilgilerini kısmen doldurmuşken uygulamayı arka plana al, 10 sn sonra geri dön | Girilen bilgiler korunur (CVV hariç) | P2 | Emü/Sim |
| MT-19 | Ödeme | Ödeme ekranındayken telefona gelen aramayı cevapla, aramayı bitir | Uygulamaya dönüldüğünde ödeme ekranı aynı durumdadır | P2 | Gerçek |
| MT-20 | Cüzdan | Kartla 500 TL bakiye yükle | Bakiye güncellenir; hareket listesinde görünür | P1 | Gerçek |
| MT-21 | Cüzdan | 49 TL ve 5.001 TL yüklemeyi dene | Tutar doğrulama mesajı; işlem başlamaz | P2 | Emü/Sim |
| MT-22 | QR ödeme | Kasadaki geçerli QR'ı okut, tutarı onayla | Cüzdandan ödenir; dijital fiş gösterilir | P1 | Gerçek |
| MT-23 | QR ödeme | İlk QR denemesinde kamera iznini reddet | Açıklama metni ve "Ayarlar'a git" butonu gösterilir; uygulama çökmez | P1 | Gerçek |
| MT-24 | QR ödeme | Süresi dolmuş (60 sn'den eski) QR'ı okut | "QR kodun süresi doldu, kasadan yenisini isteyin" mesajı; çekim yapılmaz | P2 | Gerçek |
| MT-25 | QR ödeme | Tablette menüyü aç | "Kasada QR ile öde" seçeneği görünmez | P3 | Gerçek |
| MT-26 | Bildirim | iOS: ilk sipariş tamamlanınca bildirim izni istemi çıkar; izin ver / reddet. Android: bildirim izni istenmez (varsayılan açık), izin testi gerekmez | iOS'ta izin verildiyse sipariş durumu bildirimleri gelir; reddedildiyse sipariş durumu uygulama içinden izlenebilir. Android'de bildirimler gelir | P1 | Gerçek |
| MT-27 | Düzen | Tablette ve katlanabilir cihazın iç ekranında dikey ↔ yatay geçiş yap; katlanabilirde sepet ekranındayken cihazı katla / aç | Düzen bozulmaz; sepet ve form verisi korunur | P2 | Gerçek |
| MT-28 | Bildirim | Uygulama kapalıyken gelen "Siparişiniz yolda" bildirimine dokun | Uygulama açılır, ilgili sipariş detayı gösterilir | P1 | Gerçek |
| MT-29 | Derin bağlantı | Oturum açıkken SMS'teki `https://bakkalix.example.com/k/YAZ25` bağlantısına dokun | Uygulamada YAZ25 kampanya sayfası açılır | P1 | Gerçek |
| MT-30 | Derin bağlantı | Uygulama yüklü değilken `https://bakkalix.example.com/urun/48213` bağlantısına dokun | Web'de ürün sayfası açılır | P2 | Gerçek |
| MT-31 | KVKK | Onboarding'de KVKK aydınlatma metnini onayla; pazarlama rızasını bir koşuda kabul et, bir koşuda reddet | Ret durumunda kampanya bildirimi ve SMS gönderilmez; uygulama normal kullanılabilir | P1 | Emü/Sim |
| MT-32 | Güncelleme | v2.4 yüklü cihazda uygulamayı aç | Zorunlu güncelleme ekranı çıkar; mağazaya yönlendirir | P2 | Gerçek |
| MT-33 | Erişilebilirlik | Ana sayfa, sepet ve ödeme butonlarının renk kontrastını ölç | Metin/arka plan kontrast oranı en az 4,5:1 (WCAG AA) | P3 | Emü/Sim |
| MT-34 | Performans | Galaxy A34 ve iPhone 12'de soğuk açılış süresini ölç (5 ölçüm ortalaması) | 2,5 saniyenin altında | P2 | Gerçek |
| MT-35 | Ağ | Sipariş takip ekranındayken Wi-Fi'dan mobil veriye geç | Ekran kendini yeniler; hata mesajı çıkmaz | P2 | Gerçek |

## 5. Giriş ve çıkış kriterleri

- **Giriş:** v3.0 RC derlemesi test dağıtımında, test ortamı ve sandbox kartlar hazır, D1–D7 cihazları hazır.
- **Çıkış:** P1 senaryolarının %100'ü geçti; açık kritik/yüksek hata yok; P2 senaryolarının en az %90'ı geçti.

## 6. Riskler

- Gerçek cihaz sayısı sınırlı; katlanabilir cihaz ve iPad kiralanacak (Ekim'in ilk haftası).
- Bazı bankaların 3D Secure sandbox ortamları kararsız; MT-14–MT-17 tekrar gerektirebilir.
