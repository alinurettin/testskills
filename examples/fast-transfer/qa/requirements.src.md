project: Demo Bank – FAST ile para transferi (US-310)
language: tr

## REQ-001 | İşlem başına asgari tutar 1,00 TL
type: business-rule | pri: m | risk: 2x3 Basit alt sınır; ihlal düşük tutarlı | src: US-310 AK-1 | ext: BANK-310 | status: ready
text: Transfer tutarı en az 1,00 TL olabilir.
ac: Diyelim ki geçerli IBAN ve açıklama girilmiş, Eğer ki tutar 0,99 TL girilirse, O zaman transfer yapılmaz ve alt sınır mesajı gösterilir
q: Q-012 | derived: no

## REQ-002 | İşlem başına azami tutar 50.000,00 TL
type: business-rule | pri: h | risk: 3x4 Mevzuat/limit ihlali, dolandırıcılık maruziyeti | src: US-310 AK-1 | ext: BANK-310 | status: ready
text: Transfer tutarı işlem başına en fazla 50.000,00 TL olabilir.
ac: Diyelim ki tutar 50.000,00 TL, Eğer ki OTP ile onaylanırsa, O zaman transfer gerçekleşir; Eğer ki tutar 50.000,01 TL ise, O zaman transfer reddedilir
q: Q-012 | derived: no

## REQ-003 | Günlük FAST limiti 100.000,00 TL (kümülatif)
type: business-rule | pri: c | risk: 4x5 Kümülatif limit, sıfırlama ve ücret dahil mi belirsiz; aşım tüm müşterilerde para çıkışı | src: US-310 AK-2 | ext: BANK-310 | status: cn
text: Müşterinin günlük FAST limiti 100.000,00 TL'dir; gün içindeki başarılı transferlerin toplamı bu limiti aşamaz.
ac: Diyelim ki gün içinde 100.000,00 TL başarılı transfer yapılmış, Eğer ki 1,00 TL daha gönderilmek istenirse, O zaman transfer reddedilir ve limit mesajı gösterilir
q: Q-002 | derived: no
notes: Varsayım (Q-002): limit yalnızca transfer tutarlarını sayar (ücret hariç), toplam tam 100.000,00 TL'ye izin verilir, takvim günü (Europe/Istanbul) 00:00'da sıfırlanır; reddedilen/başarısız transferler sayılmaz.

## REQ-004 | Alıcı IBAN doğrulaması (TR, 26 karakter, mod-97)
type: business-rule | pri: h | risk: 3x4 Hatalı IBAN kontrolü yanlış hesaba/başarısız transfere yol açar | src: US-310 AK-3 | ext: BANK-310 | status: cn
text: Alıcı IBAN'ı geçerli bir TR IBAN olmalıdır (26 karakter, doğru kontrol basamağı). Geçersiz IBAN'da uygun hata mesajı gösterilir.
ac: Diyelim ki kontrol basamağı hatalı bir IBAN girilmiş, Eğer ki 'Devam'a basılırsa, O zaman transfer yapılmaz ve geçersiz IBAN mesajı gösterilir
q: Q-011, Q-010 | derived: no
notes: "Uygun hata mesajı" ölçülebilir değil; uygulamadaki metin: 'Geçersiz IBAN. Lütfen TR ile başlayan 26 karakterlik IBAN girin.'

## REQ-005 | 10.000,00 TL ve üzeri transferlerde SMS OTP
type: business-rule | pri: h | risk: 3x5 Güçlü müşteri doğrulaması (mevzuat) atlanırsa yetkisiz para çıkışı | src: US-310 AK-4 | ext: BANK-310 | status: cn
text: 10.000,00 TL ve üzeri transferlerde SMS OTP ile ek doğrulama istenir.
ac: Diyelim ki tutar 10.000,00 TL, Eğer ki 'Devam'a basılırsa, O zaman SMS doğrulama adımı açılır ve OTP girilmeden transfer yapılmaz
q: Q-004, Q-013, Q-014 | derived: no

## REQ-006 | 5.000,00 TL'yi aşan transferlerde 5,00 TL işlem ücreti
type: business-rule | pri: h | risk: 3x4 Ücret hatası tüm müşterilerde yanlış tahsilat | src: US-310 AK-5 | ext: BANK-310 | status: cn
text: 5.000,00 TL'yi aşan transferlerde 5,00 TL işlem ücreti alınır; diğerlerinde ücret alınmaz.
ac: Diyelim ki tutar 5.000,00 TL, O zaman ücret 0,00 TL; Diyelim ki tutar 5.000,01 TL, O zaman ücret 5,00 TL
q: Q-005 | derived: no

## REQ-007 | İşlem ücreti dekontta gösterilir
type: functional | pri: m | risk: 2x3 Şeffaflık; yanlış gösterim şikâyet üretir | src: US-310 AK-5 | ext: BANK-310 | status: ready
text: Ücret dekontta gösterilir.
ac: Diyelim ki 5.000,01 TL transfer yapıldı, O zaman dekontta 'İşlem ücreti: 5,00 TL' ve toplam 5.005,01 TL görünür
q: Q-005 | derived: no

## REQ-008 | Yetersiz bakiyede (tutar + ücret) transfer yapılmaz
type: business-rule | pri: h | risk: 3x5 Ücretin hesaba katılmaması karşılıksız para çıkışı | src: US-310 AK-6 | ext: BANK-310 | status: cn
text: Bakiye (tutar + ücret) yetersizse transfer yapılmaz ve kullanıcıya bilgi verilir.
ac: Diyelim ki bakiye 19.990,00 TL, Eğer ki 19.985,01 TL (toplam 19.990,01 TL) gönderilirse, O zaman transfer yapılmaz ve yetersiz bakiye mesajı gösterilir
q: Q-006, Q-013 | derived: no

## REQ-009 | Açıklama alanı zorunludur
type: business-rule | pri: l | risk: 2x2 Basit doğrulama | src: US-310 AK-7 | ext: BANK-310 | status: cn
text: Açıklama alanı zorunludur.
ac: Diyelim ki açıklama boş, Eğer ki 'Devam'a basılırsa, O zaman 'Açıklama zorunludur.' mesajı gösterilir
q: Q-007 | derived: no

## REQ-010 | Açıklama en fazla 50 karakter
type: business-rule | pri: l | risk: 2x2 Basit uzunluk kontrolü; FAST mesaj alanı taşması | src: US-310 AK-7 | ext: BANK-310 | status: cn
text: Açıklama alanı en fazla 50 karakterdir.
ac: Diyelim ki açıklama 51 karakter, Eğer ki 'Devam'a basılırsa, O zaman transfer yapılmaz (veya alan 50 karakterden fazlasını kabul etmez)
q: Q-007 | derived: no

## REQ-011 | 60 saniye içinde aynı alıcıya aynı tutarda tekrar uyarısı
type: business-rule | pri: h | risk: 4x4 Mükerrer ödeme; "aynı alıcı", süre sınırı ve uyarı sonrası akış belirsiz | src: US-310 AK-8 | ext: BANK-310 | status: cn
text: Aynı alıcıya aynı tutarda 60 saniye içinde ikinci transfer denenirse kullanıcı uyarılır.
ac: Diyelim ki 100,00 TL başarılı transfer yapıldı, Eğer ki 30 sn sonra aynı IBAN'a 100,00 TL denenirse, O zaman tekrar uyarısı gösterilir; 'Vazgeç' seçilirse transfer yapılmaz
q: Q-003, Q-014 | derived: no

## REQ-012 | Sonuç ekranında dekont gösterilir
type: functional | pri: m | risk: 2x3 Dekont eksikliği şikâyet ve ispat sorunu | src: US-310 AK-9 | ext: BANK-310 | status: cn
text: Transfer sonuç ekranında dekont gösterilmelidir.
ac: Diyelim ki transfer başarılı, O zaman dekontta tutar, ücret, toplam, alıcı IBAN ve açıklama görünür
q: Q-005 | derived: no

## REQ-013 | Transfer hızlı gerçekleşmeli (performans)
type: non-functional | pri: m | risk: 3x3 Ölçülebilir hedef yok | src: US-310 AK-9 | ext: BANK-310 | status: cn
text: Transfer hızlı gerçekleşmelidir.
ac: Diyelim ki test ortamında tekil kullanıcı, Eğer ki onay verilirse, O zaman dekont ≤ 3 sn içinde görünür (varsayım Q-008)
q: Q-008 | derived: no | nfr: performance-efficiency

## REQ-014 | 7/24 çalışma (mesai dışı)
type: functional | pri: m | risk: 2x3 Saat/gün kısıtı yanlış kodlanırsa gece/hafta sonu transfer engellenir | src: US-310 Notlar | ext: BANK-310 | status: ready
text: FAST transferi mesai saatleri dışında da çalışır (7/24).
ac: Diyelim ki saat Pazar 23:30 (Europe/Istanbul), Eğer ki geçerli transfer gönderilirse, O zaman transfer gerçekleşir
derived: no

## REQ-015 | Kayıtlı alıcıya transfer
type: functional | pri: m | risk: 3x3 Hikâyede var, arayüzde karşılığı yok | src: US-310 Hikâye | ext: BANK-310 | status: cn
text: Bireysel müşteri kayıtlı alıcılarına veya yeni bir IBAN'a FAST ile para gönderebilir.
ac: Diyelim ki müşterinin kayıtlı alıcısı var, Eğer ki transfer ekranı açılırsa, O zaman kayıtlı alıcı seçilebilir
q: Q-009 | derived: no
notes: Yeni IBAN'a gönderim tüm diğer testlerde uygulanıyor; bu gereksinim kayıtlı alıcı seçimini kapsar.

## REQ-016 | Başarılı transfer bakiyeden tutar+ücreti, limitten tutarı düşer
type: business-rule | pri: h | risk: 3x5 Defter/bakiye tutarsızlığı | src: US-310 AK-2, AK-5, AK-6 | ext: BANK-310 | status: cn
text: Başarılı transferden sonra bakiye (tutar + ücret) kadar azalır, günlük kalan limit tutar kadar azalır; reddedilen transfer bakiye ve limiti değiştirmez.
ac: Diyelim ki bakiye 120.000,00 TL, Eğer ki 5.000,01 TL gönderilirse, O zaman bakiye 114.994,99 TL ve kalan limit 94.999,99 TL olur
q: Q-002 | derived: yes

## REQ-017 | Mükerrer gönderim (çift tıklama) tek transfer oluşturur
type: business-rule | pri: h | risk: 3x5 Çift tıklama iki kez para çıkarır | src: Fintech örtük gereksinim (idempotency) | ext: BANK-310 | status: cn
text: Onay düğmesine art arda basılması veya aynı işlemin yeniden gönderilmesi yalnızca bir transfer oluşturur.
ac: Diyelim ki form geçerli, Eğer ki 'Devam'a çift tıklanırsa, O zaman bakiye yalnızca bir kez düşer
derived: yes

## REQ-018 | Hatalı OTP ile transfer yapılmaz
type: business-rule | pri: h | risk: 3x5 OTP doğrulanmadan transfer = SCA ihlali | src: US-310 AK-4 (örtük) | ext: BANK-310 | status: cn
text: Hatalı SMS OTP girildiğinde transfer gerçekleşmez ve kullanıcı bilgilendirilir.
ac: Diyelim ki 10.000,00 TL için OTP adımı açık, Eğer ki '000000' girilirse, O zaman transfer yapılmaz ve hata mesajı gösterilir
q: Q-004, Q-014 | derived: yes

## REQ-019 | Tutar biçimi ve geçersiz tutar girişi
type: business-rule | pri: h | risk: 3x4 TR ondalık/binlik ayırıcı yanlış ayrıştırılırsa yanlış tutar gönderilir | src: Fintech örtük gereksinim (para/yerel ayar) | ext: BANK-310 | status: cn
text: Tutar Türkçe biçimde (binlik '.', ondalık ',') en fazla 2 ondalık basamakla girilir; sayısal olmayan, boş veya 2'den fazla ondalık basamaklı tutar reddedilir.
ac: Diyelim ki tutar '1.000,50' girilmiş, O zaman dekontta 1.000,50 TL görünür; Eğer ki 'abc' girilirse, O zaman transfer yapılmaz
q: Q-012 | derived: yes
