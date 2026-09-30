# US-128: "Şifremi unuttum" ile şifre sıfırlama

**Ürün:** Demo Mağaza (web) · **Jira:** SHOP-128

**Hikâye:** Kayıtlı bir müşteri olarak, şifremi unuttuğumda e-posta adresime gelen bağlantıyla yeni bir şifre belirlemek istiyorum, böylece hesabıma yeniden girebileyim.

**Kabul kriterleri:**
1. Giriş sayfasındaki "Şifremi unuttum" bağlantısından e-posta adresi girilerek sıfırlama bağlantısı istenir. Adres kayıtlı olsun ya da olmasın ekranda aynı mesaj gösterilir: "E-posta adresiniz kayıtlıysa şifre sıfırlama bağlantısı gönderdik."
2. Sıfırlama bağlantısı 30 dakika geçerlidir ve yalnızca bir kez kullanılabilir.
3. Aynı e-posta adresi için 1 saat içinde en fazla 3 sıfırlama isteği gönderilir.
4. Yeni şifre 8–20 karakter olmalı; en az bir büyük harf, bir küçük harf ve bir rakam içermelidir.
5. Yeni şifre son 3 şifreden biri olamaz.
6. Şifre değiştiğinde kullanıcıya bilgilendirme e-postası gönderilir ve açık oturumların tümü kapatılır. Hatalı durumlarda kullanıcıya uygun bir mesaj gösterilir.

**Notlar:** Sayfalar hızlı açılmalı. SMS ile sıfırlama sonraki sürümde.

*Bu story sentetiktir; gerçek bir ürüne ya da kişiye ait değildir.*
