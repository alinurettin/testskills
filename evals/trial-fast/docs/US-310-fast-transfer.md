# US-310: FAST ile para transferi (Mobil/Web Bankacılık)

**Jira:** BANK-310

**Hikâye:** Bireysel müşteri olarak, kayıtlı alıcılarıma veya yeni bir IBAN'a FAST ile anında para göndermek istiyorum, böylece ödemelerimi 7/24 hızlıca yapabilirim.

## Kabul kriterleri
1. Transfer tutarı en az 1,00 TL, işlem başına en fazla 50.000,00 TL olabilir.
2. Müşterinin günlük FAST limiti 100.000,00 TL'dir; gün içindeki başarılı transferlerin toplamı bu limiti aşamaz.
3. Alıcı IBAN'ı geçerli bir TR IBAN olmalıdır (26 karakter, doğru kontrol basamağı). Geçersiz IBAN'da uygun hata mesajı gösterilir.
4. 10.000,00 TL ve üzeri transferlerde SMS OTP ile ek doğrulama istenir.
5. 5.000,00 TL'yi aşan transferlerde 5,00 TL işlem ücreti alınır; diğerlerinde ücret alınmaz. Ücret dekontta gösterilir.
6. Bakiye (tutar + ücret) yetersizse transfer yapılmaz ve kullanıcıya bilgi verilir.
7. Açıklama alanı zorunludur, en fazla 50 karakterdir.
8. Aynı alıcıya aynı tutarda 60 saniye içinde ikinci transfer denenirse kullanıcı uyarılır.
9. Transfer hızlı gerçekleşmeli ve sonuç ekranında dekont gösterilmelidir.
10. Döviz hesaplarından FAST transferi: belirlenecek.

## Notlar
- Mesai saatleri dışında da çalışır (7/24).
- Test ortamı: web arayüzü, test müşterisi bakiyesi 120.000,00 TL, günlük kullanım her oturumda sıfırlanır.
