project: Demo Mağaza – Şifre sıfırlama (US-128)
language: tr
setup hesap: 'ayse.test@example.com' adresiyle aktif bir müşteri hesabı var; mevcut şifre 'Mevcut2026'
setup hesap: Test ortamının e-posta kutusu (sahte SMTP) açık ve boş
setup form: 'ayse.test@example.com' için 5 dakika önce istenen, kullanılmamış sıfırlama bağlantısı açılmış; 'Yeni şifre' formu görünür
setup gecmis: Şifre geçmişi (yeniden eskiye): 'Mevcut2026' (mevcut), 'Onceki2025' (bir önceki), 'Onceki2024' (iki önceki), 'Onceki2023' (üç önceki)

## TC-001 | Şifre, e-postadaki bağlantıyla baştan sona sıfırlanır
req: REQ-001, REQ-006, REQ-007, REQ-008 | pri: c | pol: + | tech: uc | ref: DS-002 D05 | cat: functional
obj: Ana akış; DS-001 C-01 (14 karakter) ve DS-003 S-01 (T1 → T2)
pre: @hesap
1. Giriş sayfasında 'Şifremi unuttum' bağlantısına tıkla => 'Şifre sıfırlama' sayfası açılır; 'E-posta' alanı boş
2. 'E-posta' alanına adresi yaz, 'Bağlantı gönder'e tıkla [ayse.test@example.com] => 'E-posta adresiniz kayıtlıysa şifre sıfırlama bağlantısı gönderdik.' mesajı görünür
3. Test e-posta kutusunu aç => 1 dakika içinde 'ayse.test@example.com' adresine sıfırlama bağlantısı içeren 1 e-posta gelmiş (Q-006)
4. E-postadaki bağlantıyı aç => 'Yeni şifre' formu açılır
5. 'Yeni şifre' alanına yaz, 'Şifreyi kaydet'e tıkla [Guvenli2026Yaz] => 'Şifreniz değiştirildi. Yeni şifrenizle giriş yapabilirsiniz.' mesajı; giriş sayfası açılır (Q-005, Q-007)
6. Yeni şifreyle giriş yap [ayse.test@example.com / Guvenli2026Yaz] => Giriş başarılı; 'Hesabım' sayfası açılır
tags: smoke, regression | auto: yes, e-posta kutusu API'si ile uçtan uca | status: ready

## TC-002 | Kayıtsız adres için aynı mesaj gösterilir, e-posta gönderilmez
req: REQ-002, REQ-001 | pri: h | pol: - | tech: ep | cat: security
obj: Hesap numaralandırma koruması: ekran, kayıtlı adresle (TC-001 adım 2) birebir aynı olmalı
pre: 'yok.test@example.com' adresiyle kayıtlı hesap yok
pre: Test ortamının e-posta kutusu (sahte SMTP) açık ve boş
1. 'Şifre sıfırlama' sayfasında adresi yaz, 'Bağlantı gönder'e tıkla [yok.test@example.com] => 'E-posta adresiniz kayıtlıysa şifre sıfırlama bağlantısı gönderdik.' mesajı görünür; metin, sayfa adresi ve alan durumu kayıtlı adresle aynı
2. 2 dakika bekle, test e-posta kutusunu kontrol et => 'yok.test@example.com' adresine hiçbir e-posta gelmemiş
tags: regression, security | auto: yes, e-posta kutusu API'si | status: ready

## TC-003 | Büyük harfli ve boşluklu adres kayıtlı hesapla eşleşir
req: REQ-014 | pri: m | pol: + | tech: eg | cat: localization
obj: Türkçe 'I' tuzağı: dil kurallı küçük harf 'ırem' üretir ve adres bulunamaz (Q-010 varsayımı)
pre: 'irem.test@example.com' adresiyle aktif bir müşteri hesabı var
pre: Test ortamının e-posta kutusu (sahte SMTP) açık ve boş
1. 'Şifre sıfırlama' sayfasında adresi yaz, 'Bağlantı gönder'e tıkla [" IREM.TEST@EXAMPLE.COM "] => Genel mesaj görünür: 'E-posta adresiniz kayıtlıysa şifre sıfırlama bağlantısı gönderdik.'
2. Test e-posta kutusunu aç => 1 dakika içinde 'irem.test@example.com' adresine sıfırlama bağlantısı gelmiş
tags: regression, localization, error-guessing | auto: yes, veri güdümlü | status: ready

## TC-004 | Noktasız 'ı' içeren adres kayıtlı hesapla eşleşmez
req: REQ-014, REQ-002 | pri: h | pol: - | tech: eg | cat: security
obj: Bilinen hata sınıfı: Unicode harf katlamasıyla 'ı' → 'i' eşleşip bağlantı yazılan adrese giderse hesap ele geçirilir (Q-010)
pre: 'irem.test@example.com' adresiyle aktif bir müşteri hesabı var
pre: Test ortamının e-posta kutusu (sahte SMTP) açık ve boş; 'ırem.test@example.com' adresi de bu kutuda izleniyor
1. 'Şifre sıfırlama' sayfasında adresi yaz, 'Bağlantı gönder'e tıkla [ırem.test@example.com] => Genel mesaj görünür: 'E-posta adresiniz kayıtlıysa şifre sıfırlama bağlantısı gönderdik.'
2. 2 dakika bekle, test e-posta kutusunu kontrol et => Ne 'ırem.test@example.com' ne de 'irem.test@example.com' adresine sıfırlama e-postası gelmiş
tags: regression, security, localization, error-guessing | auto: yes, veri güdümlü | status: ready

## TC-005 | 60 dakika içindeki 3. istek e-posta gönderir
req: REQ-005 | pri: m | pol: + | tech: bva | ref: DS-001 C-03 | cat: functional
obj: Varsayım Q-002: kayan 60 dakika
pre: @hesap
pre: Son 60 dakika içinde 'ayse.test@example.com' için 2 sıfırlama isteği yapılmış ve 2 e-posta gelmiş
1. 'Şifre sıfırlama' sayfasında 'Bağlantı gönder'e tıkla [ayse.test@example.com] => Genel mesaj görünür
2. Test e-posta kutusunu aç => 1 dakika içinde 3. sıfırlama e-postası gelmiş
tags: regression | auto: yes, saat kontrolü gerekir | status: ready

## TC-006 | 60 dakika içindeki 4. istekte e-posta gönderilmez
req: REQ-005, REQ-002 | pri: m | pol: - | tech: bva | ref: DS-001 C-16 | cat: security
obj: Varsayım Q-002: 4. istekte ekran değişmez (numaralandırmayı önler), yalnızca e-posta gönderilmez
pre: @hesap
pre: Son 60 dakika içinde 'ayse.test@example.com' için 3 sıfırlama isteği yapılmış ve 3 e-posta gelmiş
1. 'Şifre sıfırlama' sayfasında 'Bağlantı gönder'e tıkla [ayse.test@example.com] => Aynı genel mesaj görünür; 'çok fazla deneme' gibi farklı bir metin yok
2. 2 dakika bekle, test e-posta kutusunu kontrol et => Yeni e-posta gelmemiş; toplam 3 e-posta
tags: regression, security | auto: yes, saat kontrolü gerekir | status: ready

## TC-007 | 29:59'luk bağlantıyla 20 karakterlik şifre kaydedilir
req: REQ-003, REQ-006 | pri: m | pol: + | tech: bva | ref: DS-001 C-03 | cat: functional
obj: İki geçerli üst sınır birlikte: bağlantı yaşı 1799 sn ve şifre uzunluğu 20 (Q-001 varsayımı)
pre: @hesap
pre: Test ortamında saat kontrolü açık; 'ayse.test@example.com' için sıfırlama bağlantısı 29 dakika 59 saniye önce istenmiş
1. Bağlantıyı aç => 'Yeni şifre' formu açılır
2. 'Yeni şifre' alanına yaz, 'Şifreyi kaydet'e tıkla [GuvenliSifre20262026] => 'Şifreniz değiştirildi. Yeni şifrenizle giriş yapabilirsiniz.' mesajı görünür
tags: regression | auto: yes, saat kontrolü gerekir | status: ready

## TC-008 | 30. dakikada açılan bağlantı reddedilir
req: REQ-003, REQ-011 | pri: h | pol: - | tech: bva | ref: DS-001 C-12 | cat: security
obj: Varsayım Q-001: 30:00 ve sonrası geçersiz; mesaj Q-005 önerisi
pre: @hesap
pre: Test ortamında saat kontrolü açık; 'ayse.test@example.com' için kullanılmamış sıfırlama bağlantısı tam 30 dakika önce istenmiş
1. Bağlantıyı aç => 'Yeni şifre' formu açılmaz; 'Bu bağlantı artık geçerli değil. Lütfen yeni bir sıfırlama bağlantısı isteyin.' mesajı görünür
2. Mevcut şifreyle giriş yap [ayse.test@example.com / Mevcut2026] => Giriş başarılı; şifre değişmemiş
tags: regression, security | auto: yes, saat kontrolü gerekir | status: ready

## TC-009 | Form açıkken süresi dolan bağlantıyla şifre kaydedilmez
req: REQ-003 | pri: m | pol: - | tech: st | ref: DS-003 N-03 | cat: security
obj: Varsayım Q-001: süre 'Şifreyi kaydet' anında da kontrol edilir
pre: @hesap
pre: Test ortamında saat kontrolü açık; bağlantı 29 dakika önce istenmiş ve 'Yeni şifre' formu açık
1. Saati 2 dakika ileri al => Form ekranda açık kalır
2. 'Yeni şifre' alanına yaz, 'Şifreyi kaydet'e tıkla [Guvenli2026Yaz] => Şifre kaydedilmez; 'Bu bağlantı artık geçerli değil. Lütfen yeni bir sıfırlama bağlantısı isteyin.' mesajı görünür
3. Mevcut şifreyle giriş yap [ayse.test@example.com / Mevcut2026] => Giriş başarılı
tags: regression, security | auto: yes, saat kontrolü gerekir | status: ready

## TC-010 | Kullanılmış bağlantı ikinci kez açılamaz
req: REQ-004, REQ-011 | pri: c | pol: - | tech: st | ref: DS-003 N-02 | cat: security
obj: Tekrar kullanılabilen bağlantı hesabın yeniden ele geçirilmesine izin verir
pre: @hesap
pre: 'ayse.test@example.com' 5 dakika önce sıfırlama bağlantısıyla şifresini 'Guvenli2026Yaz' yapmış
1. Aynı sıfırlama bağlantısını yeniden aç => 'Yeni şifre' formu açılmaz; 'Bu bağlantı artık geçerli değil. Lütfen yeni bir sıfırlama bağlantısı isteyin.' mesajı görünür
2. Şifreyle giriş yap [ayse.test@example.com / Guvenli2026Yaz] => Giriş başarılı; şifre ikinci kez değişmemiş
tags: smoke, regression, security | auto: yes | status: ready

## TC-011 | İkinci sekmede açık kalan formdan şifre kaydedilemez
req: REQ-004 | pri: h | pol: - | tech: eg | ref: DS-003 N-02 | cat: security
obj: Aynı bağlantının iki sekmede açılması (tekrar gönderim) N-02'nin ikinci yolu
pre: @hesap
pre: Aynı sıfırlama bağlantısı aynı tarayıcıda iki sekmede açık; iki sekmede de 'Yeni şifre' formu görünür
1. 1. sekmede 'Yeni şifre' alanına yaz, 'Şifreyi kaydet'e tıkla [Guvenli2026Yaz] => 'Şifreniz değiştirildi. Yeni şifrenizle giriş yapabilirsiniz.' mesajı görünür
2. 2. sekmede 'Yeni şifre' alanına yaz, 'Şifreyi kaydet'e tıkla [BaskaSifre2026] => Şifre kaydedilmez; 'Bu bağlantı artık geçerli değil. Lütfen yeni bir sıfırlama bağlantısı isteyin.' mesajı görünür
3. Şifreyle giriş yap [ayse.test@example.com / Guvenli2026Yaz] => Giriş başarılı
tags: regression, security, error-guessing | auto: yes, iki sayfa bağlamı | status: ready

## TC-012 | Yeni bağlantı istenince eski bağlantı geçersiz olur
req: REQ-013 | pri: m | pol: - | tech: st | ref: DS-003 N-04 | cat: security
obj: DS-003 S-03 (T1 → T5); varsayım Q-009: yalnızca en son bağlantı geçerli
pre: @hesap
pre: 'ayse.test@example.com' için 10 dakika önce 1. bağlantı, 2 dakika önce 2. bağlantı istenmiş; ikisi de kullanılmamış
1. 1. e-postadaki bağlantıyı aç => 'Yeni şifre' formu açılmaz; 'Bu bağlantı artık geçerli değil. Lütfen yeni bir sıfırlama bağlantısı isteyin.' mesajı görünür
2. 2. e-postadaki bağlantıyı aç => 'Yeni şifre' formu açılır
tags: regression, security | auto: yes | status: ready

## TC-013 | Değiştirilmiş token'lı bağlantı formu açmaz
req: REQ-004 | pri: h | pol: - | tech: st | ref: DS-003 N-01 | cat: security
obj: Sistemin üretmediği bir token hiçbir durumda form açmamalı
pre: @hesap
pre: 'ayse.test@example.com' için 5 dakika önce istenmiş, kullanılmamış sıfırlama bağlantısı var
1. Bağlantıdaki token'ın son karakterini değiştirip adresi tarayıcıda aç [son karakter 'a' ise 'b', değilse 'a'] => 'Yeni şifre' formu açılmaz; 'Bu bağlantı artık geçerli değil. Lütfen yeni bir sıfırlama bağlantısı isteyin.' mesajı görünür
2. Orijinal bağlantıyı aç => 'Yeni şifre' formu açılır; geçersiz deneme orijinal bağlantıyı bozmamış
tags: regression, security | auto: yes | status: ready

## TC-014 | 7 karakterlik şifre reddedilir, bağlantı geçerli kalır
req: REQ-006, REQ-009, REQ-011 | pri: m | pol: - | tech: bva | ref: DS-001 C-07 | cat: functional
obj: Kural ihlali bağlantıyı tüketmez (DS-003 T3); adım 3 alt sınırı doğrular (DS-001 C-02)
pre: @hesap
pre: @form
1. 'Yeni şifre' alanına yaz, 'Şifreyi kaydet'e tıkla [Guven12] => Şifre kaydedilmez; 'Şifre 8–20 karakter olmalı ve en az bir büyük harf, bir küçük harf ve bir rakam içermelidir.' mesajı görünür
2. Test e-posta kutusunu kontrol et => 'Şifreniz değiştirildi' e-postası gelmemiş
3. Aynı formda 'Yeni şifre' alanına yaz, 'Şifreyi kaydet'e tıkla [Guvenli8] => 'Şifreniz değiştirildi. Yeni şifrenizle giriş yapabilirsiniz.' mesajı görünür
tags: regression | auto: yes, veri güdümlü | status: ready

## TC-015 | 21 karakterlik şifre reddedilir
req: REQ-006 | pri: l | pol: - | tech: bva | ref: DS-001 C-08 | cat: functional
pre: @hesap
pre: @form
1. 'Yeni şifre' alanına yaz, 'Şifreyi kaydet'e tıkla [GuvenliSifre202620261] => Şifre kaydedilmez; 'Şifre 8–20 karakter olmalı ve en az bir büyük harf, bir küçük harf ve bir rakam içermelidir.' mesajı görünür
tags: regression | auto: yes, veri güdümlü | status: ready

## TC-016 | Rakamsız şifre reddedilir
req: REQ-007 | pri: m | pol: - | tech: dt | ref: DS-002 D01 | cat: functional
pre: @hesap
pre: @form
1. 'Yeni şifre' alanına yaz, 'Şifreyi kaydet'e tıkla [GuvenliSifre] => Şifre kaydedilmez; 'Şifre 8–20 karakter olmalı ve en az bir büyük harf, bir küçük harf ve bir rakam içermelidir.' mesajı görünür
tags: regression | auto: yes, veri güdümlü | status: ready

## TC-017 | Küçük harfsiz şifre reddedilir
req: REQ-007 | pri: m | pol: - | tech: dt | ref: DS-002 D02 | cat: functional
pre: @hesap
pre: @form
1. 'Yeni şifre' alanına yaz, 'Şifreyi kaydet'e tıkla [GUVENLI2026] => Şifre kaydedilmez; 'Şifre 8–20 karakter olmalı ve en az bir büyük harf, bir küçük harf ve bir rakam içermelidir.' mesajı görünür
tags: regression | auto: yes, veri güdümlü | status: ready

## TC-018 | Büyük harfsiz şifre reddedilir
req: REQ-007 | pri: m | pol: - | tech: dt | ref: DS-002 D03 | cat: functional
pre: @hesap
pre: @form
1. 'Yeni şifre' alanına yaz, 'Şifreyi kaydet'e tıkla [yenisifre2026] => Şifre kaydedilmez; 'Şifre 8–20 karakter olmalı ve en az bir büyük harf, bir küçük harf ve bir rakam içermelidir.' mesajı görünür
tags: regression | auto: yes, veri güdümlü | status: ready

## TC-019 | Tek büyük harfi 'Ş' olan şifre kabul edilir
req: REQ-007 | pri: m | pol: + | tech: eg | cat: localization
obj: Varsayım Q-003: Türkçe harfler kabul edilir ve büyük/küçük harf sayılır
pre: @hesap
pre: @form
1. 'Yeni şifre' alanına yaz, 'Şifreyi kaydet'e tıkla [Şifre2026] => 'Şifreniz değiştirildi. Yeni şifrenizle giriş yapabilirsiniz.' mesajı görünür
2. Yeni şifreyle giriş yap [ayse.test@example.com / Şifre2026] => Giriş başarılı
tags: regression, localization, error-guessing | auto: yes, veri güdümlü | status: ready

## TC-020 | İki önceki şifre yeni şifre olarak reddedilir
req: REQ-008 | pri: m | pol: - | tech: dt | ref: DS-002 D04 | cat: functional
obj: Varsayım Q-004: son 3 = mevcut + önceki 2; 'Onceki2024' son 3'ün en eskisi
pre: @hesap
pre: @gecmis
pre: @form
1. 'Yeni şifre' alanına yaz, 'Şifreyi kaydet'e tıkla [Onceki2024] => Şifre kaydedilmez; 'Yeni şifreniz son 3 şifrenizden farklı olmalıdır.' mesajı görünür
tags: regression | auto: yes, veri güdümlü | status: ready

## TC-021 | Mevcut şifre yeni şifre olarak reddedilir
req: REQ-008 | pri: m | pol: - | tech: eg | cat: functional
obj: Ayrı risk: mevcut şifre çoğu uygulamada geçmiş listesinde değil ayrı alanda tutulur; kabul kriterindeki örnek (Q-004)
pre: @hesap
pre: @gecmis
pre: @form
1. 'Yeni şifre' alanına yaz, 'Şifreyi kaydet'e tıkla [Mevcut2026] => Şifre kaydedilmez; 'Yeni şifreniz son 3 şifrenizden farklı olmalıdır.' mesajı görünür
tags: regression | auto: yes, veri güdümlü | status: ready

## TC-022 | Üç önceki şifre yeniden kullanılabilir
req: REQ-008 | pri: l | pol: + | tech: dt | ref: DS-002 D05 | cat: functional
obj: D05'in geçmiş sınırındaki temsilcisi: son 3'ün dışındaki ilk şifre (Q-004)
pre: @hesap
pre: @gecmis
pre: @form
1. 'Yeni şifre' alanına yaz, 'Şifreyi kaydet'e tıkla [Onceki2023] => 'Şifreniz değiştirildi. Yeni şifrenizle giriş yapabilirsiniz.' mesajı görünür
tags: regression | auto: yes, veri güdümlü | status: ready

## TC-023 | Şifre sıfırlanınca diğer tarayıcıdaki oturum kapanır
req: REQ-010 | pri: h | pol: + | tech: rb | cat: security
obj: Varsayım Q-007: 'Beni hatırla' dahil tüm oturumlar sonlanır; otomatik giriş yok
pre: @hesap
pre: 'ayse.test@example.com' Firefox'ta 'Beni hatırla' işaretli giriş yapmış; 'Hesabım' sayfası açık
pre: @form
pre: Sıfırlama formu Chrome'da açık; Chrome'da oturum yok
1. Chrome'daki formda 'Yeni şifre' alanına yaz, 'Şifreyi kaydet'e tıkla [Guvenli2026Yaz] => 'Şifreniz değiştirildi. Yeni şifrenizle giriş yapabilirsiniz.' mesajı; Chrome'da oturum açılmamış
2. Firefox'ta 'Hesabım' sayfasını yenile => Giriş sayfasına yönlendirilir
3. Firefox'u kapatıp yeniden aç, siteye git => Oturum açık değil; 'Beni hatırla' ile otomatik giriş olmaz
tags: regression, security | auto: yes, iki tarayıcı bağlamı | status: ready

## TC-024 | Yalnızca sıfırlama istemek açık oturumu kapatmaz
req: REQ-010 | pri: m | pol: - | tech: eg | cat: security
obj: Herkes her adres için istek yapabilir; istek tek başına oturumu kapatırsa kullanıcıyı sistemden atmak için kötüye kullanılır
pre: @hesap
pre: 'ayse.test@example.com' Firefox'ta giriş yapmış; 'Hesabım' sayfası açık
1. Chrome'da 'Şifre sıfırlama' sayfasında 'Bağlantı gönder'e tıkla [ayse.test@example.com] => Genel mesaj görünür
2. Firefox'ta 'Hesabım' sayfasını yenile => Oturum açık kalır; 'Hesabım' sayfası görünür
tags: regression, security, error-guessing | auto: yes, iki tarayıcı bağlamı | status: ready

## TC-025 | Şifre değişince bilgilendirme e-postası şifre içermeden gelir
req: REQ-009 | pri: m | pol: + | tech: rb | cat: security
obj: Varsayım Q-008: e-postada tarih-saat ve destek bağlantısı var; şifre ve sıfırlama bağlantısı yok
pre: @hesap
pre: @form
1. 'Yeni şifre' alanına yaz, 'Şifreyi kaydet'e tıkla [Guvenli2026Yaz] => 'Şifreniz değiştirildi. Yeni şifrenizle giriş yapabilirsiniz.' mesajı görünür
2. Test e-posta kutusunu aç => 1 dakika içinde 'Şifreniz değiştirildi' konulu e-posta gelmiş; değişiklik tarihi-saati (TSİ) ve 'Bu işlemi siz yapmadıysanız' destek bağlantısı var
3. E-posta gövdesinde yeni şifreyi ara [Guvenli2026Yaz] => Şifre geçmiyor; sıfırlama bağlantısı da yok
tags: regression, security | auto: yes, e-posta kutusu API'si | status: ready
