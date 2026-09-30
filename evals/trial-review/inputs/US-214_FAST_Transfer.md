# US-214 — Nehir Mobil: IBAN'a FAST Transferi

| Alan | Değer |
|---|---|
| Ürün | Nehir Mobil (iOS / Android) — Nehir Bank A.Ş. |
| Epik | EP-31 Para Transferleri Yenileme |
| Sprint | 2026-S19 |
| Ürün sahibi | Selin Aydoğan |
| Durum | Geliştirme tamamlandı, test aşamasında |

## Kullanıcı hikâyesi

**Bireysel bir müşteri olarak**, mobil uygulamadan herhangi bir bankadaki TL hesaba IBAN ile 7/24 anında para gönderebilmek **istiyorum**; **böylece** EFT saatlerini beklemeden ödemelerimi yapabilirim.

## Kabul kriterleri

### AC-1 — IBAN doğrulama
- Alıcı IBAN'ı "TR" ile başlamalı, toplam 26 karakter olmalı ve MOD-97 kontrolünden geçmelidir.
- Kullanıcının girdiği boşluklar kaldırılır, küçük harfler büyük harfe çevrilir. Örneğin `tr16 0099 4000 0028 1746 3900 57` geçerli kabul edilir ve `TR16 0099 4000 0028 1746 3900 57` biçiminde gösterilir.
- Geçersiz IBAN'da alanın altında **"Geçerli bir IBAN giriniz."** mesajı gösterilir ve "Devam" butonu pasif kalır.

### AC-2 — Alıcı adı soyadı
- Zorunludur. Boş bırakılırsa veya yalnızca boşluk karakterlerinden oluşursa **"Alıcı adı soyadı zorunludur."** mesajı gösterilir ve "Devam" butonu pasif kalır.
- Türkçe karakterler (ç, ğ, ı, İ, ö, ş, ü) ve kısa çizgi (-) desteklenir; onay ekranında ve dekontta aynen görünür.

### AC-3 — Tutar
- İşlem başına en az **1,00 TL**, en fazla **50.000,00 TL** gönderilebilir (sınır değerler dahil).
- Bu aralığın dışındaki tutarlarda **"Tutar 1,00 TL ile 50.000,00 TL arasında olmalıdır."** mesajı gösterilir ve "Devam" butonu pasif kalır.
- Tutar alanı yalnızca rakam ve virgül kabul eder; virgülden sonra en fazla 2 hane yazılmasına izin verir.

### AC-4 — Bakiye kontrolü
- Tutar, seçili hesabın kullanılabilir bakiyesinden büyükse **"Yetersiz bakiye"** mesajı gösterilir ve işlem başlatılmaz.
- Kullanılabilir bakiyeye eşit tutar gönderilebilir.

### AC-5 — Günlük limit
- Bir müşterinin gün içindeki toplam giden FAST tutarı **150.000,00 TL**'yi aşamaz (150.000,00 TL dahil).
- Limiti aşacak işlem **"Günlük transfer limitiniz aşılıyor. Kalan limit: {kalan} TL"** mesajıyla reddedilir.
- Günlük limit her gün 00:00'da (TSİ) sıfırlanır. Kalan limit, Profil > Limitlerim ekranında güncel olarak gösterilir.

### AC-6 — SMS ile doğrulama (OTP)
- Tutar **10.000,00 TL veya üzerindeyse**, onay adımından sonra kayıtlı cep telefonuna 6 haneli tek kullanımlık kod (OTP) gönderilir. 10.000,00 TL'nin altındaki tutarlarda OTP istenmez.
- Kod **180 saniye** geçerlidir; ekranda geri sayım gösterilir. Süresi dolan kod **"Doğrulama kodunun süresi doldu."** mesajıyla reddedilir ve transfer gerçekleşmez.
- Her hatalı girişte **"Hatalı kod. Kalan deneme hakkı: {n}"** mesajı gösterilir. **3. hatalı girişte** işlem iptal edilir, **"Güvenliğiniz için işleminiz iptal edildi."** mesajı gösterilir ve kullanıcı ana sayfaya yönlendirilir; hesaptan para çıkmaz.

### AC-7 — Çalışma saatleri ve ücret
- FAST transferi hafta sonu ve resmî tatiller dahil 7 gün 24 saat anında gerçekleşir; "EFT saatleri dışında" uyarısı gösterilmez.
- FAST transferlerinden ücret alınmaz; onay ekranında **"İşlem ücreti: 0,00 TL"** gösterilir.

### AC-8 — Mükerrer işlem uyarısı
- Aynı alıcı IBAN'ına **aynı tutarla son 10 dakika içinde** başarılı bir transfer yapılmışsa, onay ekranından önce **"Bu alıcıya kısa süre önce aynı tutarda transfer yaptınız. Devam etmek istiyor musunuz?"** uyarısı gösterilir.
- "Vazgeç" seçilirse işlem yapılmaz; "Devam" seçilirse akış normal şekilde sürer.

### AC-9 — İşlem sonucu ve dekont
- Başarılı transferde bakiye anında düşer ve işlem, Hesap Hareketleri ekranında **"Tamamlandı"** durumuyla listelenir.
- Sonuç ekranından PDF dekont indirilebilir. Dekontta alıcı IBAN'ının yalnızca ilk 4 ve son 4 karakteri görünür; diğer karakterler "*" ile maskelenir.

### AC-10 — Açıklama alanı
- Açıklama alanı isteğe bağlıdır ve en fazla 140 karakterdir; 141. karakter girilemez. Alanın altında "{n}/140" sayacı gösterilir.
- Açıklama boş bırakılırsa dekontta açıklama olarak "FAST Transfer" yazar.

## Kapsam dışı
- Yurt dışı (SWIFT) transferleri ve döviz hesaplarından yapılan transferler
- İleri tarihli ve düzenli (talimatlı) transferler
- Kolay Adres (telefon numarası / e-posta ile) transfer
- Kampanya, banner ve pazarlama bildirimleri

## Notlar
- Test ortamı: `https://mobil-test.nehirbank.example.test` — sanal saat ayarı ile gün/saat simülasyonu yapılabilir; SMS'ler test SMS geçidine düşer.
- Tüm tutarlar Türk Lirası'dır; ondalık ayırıcı virgül, binlik ayırıcı noktadır.
