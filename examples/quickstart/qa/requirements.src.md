project: Demo Mağaza – Şifre sıfırlama (US-128)
language: tr

## REQ-001 | "Şifremi unuttum" ile e-postaya sıfırlama bağlantısı istenir
type: functional | pri: h | risk: 2x4 Kurtarma yolu çalışmazsa kullanıcı hesabına giremez; mantık basit | src: US-128 AK-1 | ext: SHOP-128 | status: ready
text: Giriş sayfasındaki "Şifremi unuttum" bağlantısından e-posta adresi girilerek sıfırlama bağlantısı istenir.
ac: Diyelim ki 'ayse.test@example.com' kayıtlı, Eğer ki bu adresle sıfırlama istenirse, O zaman adrese sıfırlama bağlantısı içeren bir e-posta gönderilir
q: Q-006 | derived: no

## REQ-002 | Kayıtlı ve kayıtsız adres için aynı ekran mesajı
type: business-rule | pri: h | risk: 3x4 Farklı mesaj ya da farklı davranış, bir e-postanın müşteri olup olmadığını sızdırır (hesap numaralandırma) | src: US-128 AK-1 | ext: SHOP-128 | status: ready
text: Adres kayıtlı olsun ya da olmasın ekranda aynı mesaj gösterilir: "E-posta adresiniz kayıtlıysa şifre sıfırlama bağlantısı gönderdik."
ac: Diyelim ki 'yok.test@example.com' kayıtlı değil, Eğer ki bu adresle sıfırlama istenirse, O zaman kayıtlı adresle birebir aynı mesaj gösterilir ve e-posta gönderilmez
q: Q-002 | derived: no | nfr: security

## REQ-003 | Sıfırlama bağlantısı 30 dakika geçerlidir
type: business-rule | pri: h | risk: 3x4 Süresi dolmuş bağlantının kabul edilmesi hesap ele geçirme penceresini uzatır; sınır (dahil/hariç) belirsiz | src: US-128 AK-2 | ext: SHOP-128 | status: cn
text: Sıfırlama bağlantısı 30 dakika geçerlidir.
ac: Diyelim ki bağlantı 30 dakika önce istendi, Eğer ki bağlantı açılırsa, O zaman şifre formu açılmaz ve bağlantının geçersiz olduğu mesajı gösterilir
q: Q-001 | derived: no | nfr: security
notes: Varsayım (Q-001): süre isteğin alındığı andan başlar; 29:59'da geçerli, 30:00 ve sonrası geçersiz; kontrol 'Şifreyi kaydet' anında da yapılır.

## REQ-004 | Sıfırlama bağlantısı yalnızca bir kez kullanılabilir
type: business-rule | pri: h | risk: 2x5 Tekrar kullanılabilen bağlantı, e-postası ele geçen hesabın yeniden devralınmasına izin verir | src: US-128 AK-2 | ext: SHOP-128 | status: ready
text: Sıfırlama bağlantısı yalnızca bir kez kullanılabilir.
ac: Diyelim ki bağlantıyla şifre değiştirildi, Eğer ki aynı bağlantı yeniden açılırsa, O zaman şifre formu açılmaz ve bağlantının geçersiz olduğu mesajı gösterilir
q: Q-005 | derived: no | nfr: security

## REQ-005 | Aynı e-posta için 1 saatte en fazla 3 sıfırlama isteği
type: business-rule | pri: m | risk: 3x3 Pencere türü ve 4. istekteki davranış belirsiz; aşım e-posta bombardımanına ve maliyete yol açar | src: US-128 AK-3 | ext: SHOP-128 | status: cn
text: Aynı e-posta adresi için 1 saat içinde en fazla 3 sıfırlama isteği gönderilir.
ac: Diyelim ki son 60 dakikada aynı adres için 3 istek gönderildi, Eğer ki 4. istek yapılırsa, O zaman e-posta gönderilmez ve ekranda yine aynı genel mesaj görünür
q: Q-002 | derived: no | nfr: security
notes: Varsayım (Q-002): kayan 60 dakika; sayaç kayıtlı olsun olmasın her adres için tutulur.

## REQ-006 | Yeni şifre uzunluğu 8–20 karakter
type: business-rule | pri: m | risk: 2x3 Basit uzunluk kontrolü; sınır hatası kullanıcıyı engeller ya da zayıf şifreye izin verir | src: US-128 AK-4 | ext: SHOP-128 | status: ready
text: Yeni şifre 8–20 karakter olmalıdır.
ac: Diyelim ki diğer kurallara uyan 7 karakterlik şifre girildi, Eğer ki 'Şifreyi kaydet'e basılırsa, O zaman şifre değişmez ve kural mesajı gösterilir
q: Q-005 | derived: no

## REQ-007 | Yeni şifre büyük harf, küçük harf ve rakam içerir
type: business-rule | pri: m | risk: 3x3 Türkçe harflerin (Ş, ı, İ) büyük/küçük harf sayılıp sayılmadığı belirsiz | src: US-128 AK-4 | ext: SHOP-128 | status: cn
text: Yeni şifre en az bir büyük harf, bir küçük harf ve bir rakam içermelidir.
ac: Diyelim ki rakam içermeyen 'Guvenli-Sifre' girildi, Eğer ki 'Şifreyi kaydet'e basılırsa, O zaman şifre değişmez ve kural mesajı gösterilir
q: Q-003, Q-005, Q-011 | derived: no

## REQ-008 | Yeni şifre son 3 şifreden biri olamaz
type: business-rule | pri: m | risk: 3x3 "Son 3"ün mevcut şifreyi içerip içermediği belirsiz | src: US-128 AK-5 | ext: SHOP-128 | status: cn
text: Yeni şifre son 3 şifreden biri olamaz.
ac: Diyelim ki kullanıcının mevcut şifresi 'Mevcut2026', Eğer ki yeni şifre olarak 'Mevcut2026' girilirse, O zaman şifre değişmez ve eski şifre mesajı gösterilir
q: Q-004, Q-005, Q-011 | derived: no

## REQ-009 | Şifre değişince bilgilendirme e-postası gönderilir
type: functional | pri: m | risk: 2x3 E-posta gitmezse kullanıcı yetkisiz bir değişikliği fark edemez | src: US-128 AK-6 | ext: SHOP-128 | status: cn
text: Şifre değiştiğinde kullanıcıya bilgilendirme e-postası gönderilir.
ac: Diyelim ki şifre bağlantıyla değiştirildi, O zaman kullanıcıya 'Şifreniz değiştirildi' konulu e-posta gönderilir ve e-postada şifre yer almaz
q: Q-006, Q-008 | derived: no | nfr: security

## REQ-010 | Şifre değişince açık oturumların tümü kapatılır
type: business-rule | pri: h | risk: 3x4 Açık kalan oturum, şifresi sıfırlanan hesapta saldırganın kalmasına izin verir | src: US-128 AK-6 | ext: SHOP-128 | status: cn
text: Şifre değiştiğinde açık oturumların tümü kapatılır.
ac: Diyelim ki kullanıcı başka bir tarayıcıda oturum açık, Eğer ki şifre sıfırlanırsa, O zaman o tarayıcıdaki sonraki istek giriş sayfasına yönlendirilir
q: Q-007 | derived: no | nfr: security

## REQ-011 | Hatalı durumlarda kullanıcıya mesaj gösterilir
type: functional | pri: l | risk: 2x2 Mesaj metni kozmetik; işlemin kendisini etkilemez | src: US-128 AK-6 | ext: SHOP-128 | status: cn
text: Hatalı durumlarda kullanıcıya uygun bir mesaj gösterilir.
ac: Diyelim ki 'ayse.test@' girildi, Eğer ki 'Bağlantı gönder'e basılırsa, O zaman 'Geçerli bir e-posta adresi girin.' mesajı gösterilir ve istek gönderilmez
q: Q-005 | derived: no
notes: "Uygun" ölçülebilir değil; önerilen mesaj metinleri Q-005'te onaya sunuldu.

## REQ-012 | Sayfalar hızlı açılmalı
type: non-functional | pri: l | risk: 2x2 Ölçülebilir hedef yok; etki kullanıcı deneyimiyle sınırlı | src: US-128 Notlar | ext: SHOP-128 | status: cn
text: Sayfalar hızlı açılmalı.
q: Q-006 | derived: no | nfr: performance-efficiency
notes: Varsayım (Q-006): sayfalar p95 ≤ 2 sn (test ortamı, tekil kullanıcı); sıfırlama e-postası 1 dakika içinde gelen kutusunda.

## REQ-013 | Yeni istek önceki sıfırlama bağlantılarını geçersiz kılar
type: business-rule | pri: m | risk: 2x4 Aynı anda birden çok geçerli bağlantı, eski bir e-postanın kötüye kullanılmasına izin verir | src: US-128 AK-2 (türetilmiş) | ext: SHOP-128 | status: cn
text: Aynı adres için yeni bir sıfırlama bağlantısı istendiğinde, daha önce gönderilmiş ve kullanılmamış bağlantılar geçersiz olur.
ac: Diyelim ki 1. bağlantı henüz kullanılmadı, Eğer ki 2. bağlantı istenip 1. bağlantı açılırsa, O zaman bağlantının geçersiz olduğu mesajı gösterilir
q: Q-009 | derived: yes | nfr: security

## REQ-014 | E-posta adresi büyük/küçük harf ve boşluktan bağımsız eşleştirilir
type: business-rule | pri: m | risk: 3x3 Türkçe yerel ayarla küçük harfe çevirmede 'I' → 'ı' olur ve kayıtlı adres bulunamaz; kullanıcı sıfırlama e-postası alamaz | src: US-128 AK-1 (türetilmiş) | ext: SHOP-128 | status: cn
text: Sıfırlama isteğinde e-posta adresi büyük/küçük harf farkı ve baştaki/sondaki boşluklar yok sayılarak kayıtlı adresle eşleştirilir.
ac: Diyelim ki 'irem.test@example.com' kayıtlı, Eğer ki ' IREM.TEST@EXAMPLE.COM ' girilirse, O zaman 'irem.test@example.com' adresine sıfırlama e-postası gönderilir
q: Q-010 | derived: yes
