# -*- coding: utf-8 -*-
"""Rebuilds inputs/FAST_Transfer_Test_Cases.xlsx byte-for-byte with Python stdlib only (zipfile + XML).
Usage: python tools/gen_xlsx.py inputs/FAST_Transfer_Test_Cases.xlsx
Evaluator-side helper; hand the agent only TASK.md and inputs/."""
import sys
import zipfile
from xml.sax.saxutils import escape

OUT = sys.argv[1]

IB_DENIZ = "TR48 0099 1000 0073 0915 2844 06"
IB_DENIZ_BADCHK = "TR59 0099 1000 0073 0915 2844 06"
IB_DENIZ_SHORT = "TR48 0099 1000 0073 0915 2844 0"
IB_CAGLA = "TR13 0098 7000 0055 2190 3377 81"
IB_MURAT = "TR36 0099 1000 0060 4417 8299 35"
IB_SENDER = "TR83 0098 7000 0041 8273 6500 12"
IB_HATICE = "TR55 0098 7000 0091 3365 0422 18"
IB_DE = "DE39 9999 9999 0012 3456 78"

OK = "Ortak ön koşul (Bilgi sayfası) sağlanmış."

HEADERS = ["Test ID", "Başlık", "Ön Koşul", "Adımlar", "Beklenen Sonuç", "Öncelik", "Gereksinim"]

T = []
def tc(i, title, pre, steps, exp, prio, req):
    T.append(["FT-%03d" % i, title, pre, steps, exp, prio, req])

tc(1, "Geçerli IBAN ve alıcı adı ile alıcı bilgisi girilir", OK,
   "1. Para Transferi > IBAN'a Gönder menüsünü aç.\n"
   f"2. Alıcı IBAN alanına {IB_DENIZ} gir.\n"
   "3. Alıcı Adı Soyadı alanına \"Deniz Arıkan\" gir.\n"
   "4. Tutar alanına 250,00 gir.",
   "- IBAN ve alıcı adı alanlarında hata mesajı gösterilmez.\n- \"Devam\" butonu aktif olur.",
   "Yüksek", "AC-1, AC-2")

tc(2, "MOD-97 kontrolünden geçmeyen IBAN reddedilir", OK,
   "1. IBAN'a Gönder ekranını aç.\n"
   f"2. Alıcı IBAN alanına {IB_DENIZ_BADCHK} gir (kontrol basamakları hatalı).\n"
   "3. Alıcı adına \"Deniz Arıkan\", tutara 250,00 gir.",
   "- IBAN alanının altında \"Geçerli bir IBAN giriniz.\" mesajı gösterilir.\n- \"Devam\" butonu pasif kalır.",
   "Yüksek", "AC-1")

tc(3, "25 karakterli (eksik) IBAN reddedilir", OK,
   "1. IBAN'a Gönder ekranını aç.\n"
   f"2. Alıcı IBAN alanına {IB_DENIZ_SHORT} gir (25 karakter).\n"
   "3. Alıcı adı ve tutarı geçerli değerlerle doldur.",
   "- \"Geçerli bir IBAN giriniz.\" mesajı gösterilir.\n- \"Devam\" butonu pasif kalır.",
   "Orta", "AC-1")

tc(4, "TR dışı ülke kodlu IBAN reddedilir", OK,
   "1. IBAN'a Gönder ekranını aç.\n"
   f"2. Alıcı IBAN alanına {IB_DE} gir (MOD-97 açısından geçerli bir Almanya IBAN'ı).\n"
   "3. Alıcı adı ve tutarı geçerli değerlerle doldur.",
   "- \"Geçerli bir IBAN giriniz.\" mesajı gösterilir.\n- \"Devam\" butonu pasif kalır.",
   "Orta", "AC-1")

tc(5, "Boşluklu ve küçük harfle girilen IBAN normalize edilerek kabul edilir", OK,
   "1. IBAN'a Gönder ekranını aç.\n"
   f"2. Alıcı IBAN alanına \"{IB_DENIZ.lower()}\" gir (küçük harf, boşluklu).\n"
   "3. Alıcı adına \"Deniz Arıkan\", tutara 250,00 gir.\n"
   "4. Devam'a dokun.",
   "- Hata mesajı gösterilmez, \"Devam\" butonu aktif olur.\n"
   f"- Onay ekranında IBAN \"{IB_DENIZ}\" olarak gösterilir.",
   "Orta", "AC-1")

tc(6, "Alıcı adı soyadı boş bırakılamaz", OK,
   "1. IBAN'a Gönder ekranını aç.\n"
   f"2. Alıcı IBAN alanına {IB_DENIZ}, tutara 250,00 gir.\n"
   "3. Alıcı Adı Soyadı alanını boş bırak.",
   "- \"Alıcı adı soyadı zorunludur.\" mesajı gösterilir.\n- \"Devam\" butonu pasif kalır.",
   "Orta", "AC-2")

tc(7, "Türkçe karakterli ve kısa çizgili alıcı adı kabul edilir", OK,
   "1. IBAN'a Gönder ekranını aç.\n"
   f"2. IBAN: {IB_CAGLA}, Alıcı: \"Çağla Şükriye Öğüt-İnce\", Tutar: 150,00 gir.\n"
   "3. Devam > Onayla ile transferi tamamla.\n"
   "4. Sonuç ekranından PDF dekontu indir ve aç.",
   "- Alıcı adı alanında hata gösterilmez.\n"
   "- Onay ekranında ve PDF dekontta alıcı adı \"Çağla Şükriye Öğüt-İnce\" olarak, karakterler bozulmadan görünür.",
   "Orta", "AC-2")

tc(8, "Geçerli tutarla (2.500,00 TL) transfer tamamlanır", OK,
   "1. IBAN'a Gönder ekranını aç.\n"
   f"2. IBAN: {IB_DENIZ}, Alıcı: \"Deniz Arıkan\", Tutar: 2.500,00 gir.\n"
   "3. Devam'a dokun.\n"
   "4. Onay ekranında \"Onayla\"ya dokun.",
   "- Onay ekranında tutar 2.500,00 TL ve alıcı bilgileri doğru gösterilir.\n"
   "- OTP istenmez.\n"
   "- Sonuç ekranında \"İşleminiz gerçekleşti\" mesajı gösterilir.",
   "Yüksek", "AC-3, AC-9")

tc(9, "Tek işlem limitini aşan tutar reddedilir", OK,
   "1. IBAN'a Gönder ekranını aç.\n"
   f"2. IBAN: {IB_DENIZ}, Alıcı: \"Deniz Arıkan\" gir.\n"
   "3. Tutar alanına 75.000,00 gir.",
   "- \"Tutar 1,00 TL ile 50.000,00 TL arasında olmalıdır.\" mesajı gösterilir.\n- \"Devam\" butonu pasif kalır.",
   "Kritik", "AC-3")

tc(10, "20.000,00 TL tutar kabul edilir ve OTP adımına geçilir", OK,
   "1. IBAN'a Gönder ekranını aç.\n"
   f"2. IBAN: {IB_MURAT}, Alıcı: \"Murat Yıldırım\", Tutar: 20.000,00 gir.\n"
   "3. Devam'a, ardından onay ekranında Onayla'ya dokun.",
   "- Tutar alanında hata gösterilmez.\n"
   "- Onay ekranında tutar 20.000,00 TL gösterilir.\n"
   "- Onayla sonrası OTP ekranı açılır.",
   "Yüksek", "AC-3, AC-6")

tc(11, "Yetersiz bakiye durumunda transfer başlatılmaz",
   OK + "\nVadesiz TL hesabının kullanılabilir bakiyesi 1.000,00 TL'ye ayarlanmış.",
   "1. IBAN'a Gönder ekranını aç.\n"
   f"2. IBAN: {IB_DENIZ}, Alıcı: \"Deniz Arıkan\" gir.\n"
   "3. Tutar alanına 1.500,00 gir.\n"
   "4. Devam'a dokun.",
   "- \"Yetersiz bakiye\" mesajı gösterilir.\n"
   "- Onay ekranına geçilmez, işlem başlatılmaz.\n"
   "- Kullanılabilir bakiye 1.000,00 TL olarak kalır.",
   "Yüksek", "AC-4")

tc(12, "Kullanılabilir bakiyenin tamamı gönderilebilir",
   "Müşteri Hatice Demirtaş hesabıyla giriş yapılır:\n"
   "Müşteri No: 48213377\n"
   "TCKN: 28461937502\n"
   "Doğum Tarihi: 14.03.1987\n"
   "Anne Kızlık Soyadı: Karaca\n"
   "E-posta: hatice.demirtas87@example.com\n"
   "Mobil şifre: 482913\n"
   f"Vadesiz TL hesabı {IB_HATICE}, kullanılabilir bakiye 3.750,00 TL.",
   "1. IBAN'a Gönder ekranını aç.\n"
   f"2. IBAN: {IB_DENIZ}, Alıcı: \"Deniz Arıkan\", Tutar: 3.750,00 gir.\n"
   "3. Devam > Onayla'ya dokun.",
   "- \"Yetersiz bakiye\" mesajı gösterilmez.\n"
   "- Transfer tamamlanır.\n"
   "- Kullanılabilir bakiye 0,00 TL olur.",
   "Orta", "AC-4")

tc(13, "Günlük limiti tam dolduran transfer kabul edilir",
   OK + "\nAynı gün içinde toplam 140.000,00 TL giden FAST transferi yapılmış (45.000,00 + 45.000,00 + 45.000,00 + 5.000,00).",
   "1. IBAN'a Gönder ekranını aç.\n"
   f"2. IBAN: {IB_MURAT}, Alıcı: \"Murat Yıldırım\", Tutar: 10.000,00 gir.\n"
   "3. Devam > Onayla'ya dokun, SMS ile gelen OTP'yi gir.\n"
   "4. Profil > Limitlerim ekranını aç.",
   "- Limit uyarısı gösterilmez.\n"
   "- Transfer tamamlanır.\n"
   "- Limitlerim ekranında FAST günlük kalan limit 0,00 TL görünür.",
   "Yüksek", "AC-5")

tc(14, "Günlük limiti aşan transfer reddedilir",
   OK + "\nAynı gün içinde toplam 140.000,00 TL giden FAST transferi yapılmış.",
   "1. IBAN'a Gönder ekranını aç.\n"
   f"2. IBAN: {IB_MURAT}, Alıcı: \"Murat Yıldırım\", Tutar: 10.000,01 gir.\n"
   "3. Devam'a dokun.",
   "- \"Günlük transfer limitiniz aşılıyor. Kalan limit: 10.000,00 TL\" mesajı gösterilir.\n"
   "- İşlem gerçekleşmez, bakiye değişmez.",
   "Kritik", "AC-5")

tc(15, "Günlük limit gece yarısı sıfırlanır",
   OK + "\nTest ortamı sanal saati 23:50'ye ayarlı; gün içinde toplam 150.000,00 TL giden FAST transferi yapılmış.",
   "1. Saat 23:55'te 100,00 TL tutarında transfer dene.\n"
   "2. Sanal saati ertesi gün 00:05'e ilerlet.\n"
   "3. Aynı alıcıya 100,00 TL tutarında transferi tekrar dene.\n"
   "4. Profil > Limitlerim ekranını aç.",
   "- 1. adımda \"Günlük transfer limitiniz aşılıyor. Kalan limit: 0,00 TL\" mesajı gösterilir.\n"
   "- 3. adımda transfer tamamlanır.\n"
   "- Limitlerim ekranında FAST günlük kalan limit 149.900,00 TL görünür.",
   "Orta", "AC-5")

tc(16, "Kalan günlük limit Limitlerim ekranında güncellenir", OK,
   "1. 30.000,00 TL tutarında FAST transferi yap ve OTP ile onayla.\n"
   "2. Profil > Limitlerim ekranını aç.\n"
   "3. FAST günlük kalan limit değerini kontrol et.",
   "",
   "Orta", "AC-5")

tc(17, "9.999,99 TL transferde OTP istenmez", OK,
   "1. IBAN'a Gönder ekranını aç.\n"
   f"2. IBAN: {IB_MURAT}, Alıcı: \"Murat Yıldırım\", Tutar: 9.999,99 gir.\n"
   "3. Devam > Onayla'ya dokun.",
   "- OTP ekranı açılmaz, SMS gönderilmez.\n"
   "- Sonuç ekranında \"İşleminiz gerçekleşti\" mesajı gösterilir.",
   "Kritik", "AC-6")

tc(18, "10.000,00 TL transferde OTP istenir", OK,
   "1. IBAN'a Gönder ekranını aç.\n"
   f"2. IBAN: {IB_MURAT}, Alıcı: \"Murat Yıldırım\", Tutar: 10.000,00 gir.\n"
   "3. Devam > Onayla'ya dokun.",
   "- 6 haneli kod giriş alanı olan OTP ekranı açılır.\n"
   "- Kayıtlı cep telefonuna SMS ile 6 haneli kod gelir.\n"
   "- Kod girilmeden transfer gerçekleşmez.",
   "Kritik", "AC-6")

tc(19, "Doğru OTP ile transfer tamamlanır", OK,
   f"1. IBAN: {IB_MURAT}, Alıcı: \"Murat Yıldırım\", Tutar: 12.000,00 gir.\n"
   "2. Devam > Onayla'ya dokun.\n"
   "3. SMS ile gelen 6 haneli kodu 60 saniye içinde gir ve Onayla'ya dokun.",
   "- Sonuç ekranında \"İşleminiz gerçekleşti\" mesajı gösterilir.\n"
   "- Kullanılabilir bakiye 188.000,00 TL olur.",
   "Kritik", "AC-6, AC-9")

tc(20, "Bir hatalı OTP sonrası doğru kod ile devam edilebilir", OK,
   f"1. IBAN: {IB_MURAT}, Alıcı: \"Murat Yıldırım\", Tutar: 12.000,00 gir; Devam > Onayla'ya dokun.\n"
   "2. OTP ekranına yanlış kod (000000) gir ve Onayla'ya dokun.\n"
   "3. SMS ile gelen doğru kodu gir ve Onayla'ya dokun.",
   "- 2. adımda \"Hatalı kod. Kalan deneme hakkı: 2\" mesajı gösterilir.\n"
   "- 3. adımda transfer tamamlanır ve \"İşleminiz gerçekleşti\" mesajı gösterilir.",
   "Yüksek", "AC-6")

tc(21, "3 hatalı OTP girişinde işlem iptal edilir", OK,
   f"1. IBAN: {IB_MURAT}, Alıcı: \"Murat Yıldırım\", Tutar: 12.000,00 gir; Devam > Onayla'ya dokun.\n"
   "2. OTP ekranına art arda 3 kez yanlış kod gir (000000, 111111, 222222).",
   "- 1. ve 2. hatalı girişte kalan deneme hakkı sırasıyla 2 ve 1 olarak gösterilir.\n"
   "- 3. hatalı girişte \"Güvenliğiniz için işleminiz iptal edildi.\" mesajı gösterilir ve kullanıcı ana sayfaya yönlendirilir.\n"
   "- Transfer gerçekleşmez, bakiye 200.000,00 TL olarak kalır.",
   "Düşük", "AC-6")

tc(22, "Süresi dolan OTP kodu reddedilir", OK,
   f"1. IBAN: {IB_MURAT}, Alıcı: \"Murat Yıldırım\", Tutar: 12.000,00 gir; Devam > Onayla'ya dokun.\n"
   "2. OTP ekranı açıldıktan sonra kodu girmeden 120 saniye bekle.\n"
   "3. 121. saniyede SMS ile gelen kodu gir ve Onayla'ya dokun.",
   "- \"Doğrulama kodunun süresi doldu.\" mesajı gösterilir.\n"
   "- Transfer gerçekleşmez, bakiye değişmez.",
   "Kritik", "AC-6")

tc(23, "Pazar günü 03:00'te başka bankaya FAST transferi anında gerçekleşir",
   OK + "\nTest ortamı sanal saati Pazar 03:00'e ayarlı.",
   "1. IBAN'a Gönder ekranını aç.\n"
   f"2. IBAN: {IB_DENIZ}, Alıcı: \"Deniz Arıkan\", Tutar: 1.200,00 gir.\n"
   "3. Devam > Onayla'ya dokun.\n"
   "4. Hesap Hareketleri ekranını aç.",
   "- \"EFT saatleri dışında\" benzeri bir uyarı gösterilmez.\n"
   "- Transfer anında gerçekleşir.\n"
   "- Hesap Hareketleri'nde işlem \"Tamamlandı\" durumunda görünür.",
   "Orta", "AC-7")

tc(24, "Onay ekranında işlem ücreti 0,00 TL gösterilir", OK,
   "1. IBAN'a Gönder ekranını aç.\n"
   f"2. IBAN: {IB_DENIZ}, Alıcı: \"Deniz Arıkan\", Tutar: 500,00 gir.\n"
   "3. Devam'a dokun ve onay ekranını incele.\n"
   "4. Onayla'ya dokun.",
   "- Onay ekranında \"İşlem ücreti: 0,00 TL\" yazar.\n"
   "- İşlem sonrası hesaptan yalnızca 500,00 TL düşer (bakiye 199.500,00 TL).",
   "Orta", "AC-7")

tc(25, "Başarılı transfer sonrası bakiye anında düşer", OK,
   "1. Hesaplarım ekranında vadesiz TL hesabının bakiyesini not al (200.000,00 TL).\n"
   f"2. IBAN: {IB_DENIZ}, Alıcı: \"Deniz Arıkan\", Tutar: 2.500,00 ile transfer yap.\n"
   "3. Sonuç ekranından Hesaplarım ekranına dön.",
   "- Bakiye, sayfa yenilemeye gerek kalmadan 197.500,00 TL olarak gösterilir.",
   "Yüksek", "AC-9")

DUP = ["Başarılı transfer Hesap Hareketleri'nde \"Tamamlandı\" olarak listelenir", OK,
   f"1. IBAN: {IB_DENIZ}, Alıcı: \"Deniz Arıkan\", Tutar: 2.500,00 ile transfer yap.\n"
   "2. Hesaplarım > Vadesiz TL > Hesap Hareketleri ekranını aç.",
   "- Listenin en üstünde 2.500,00 TL tutarlı, alıcısı \"Deniz Arıkan\" olan işlem görünür.\n"
   "- İşlem durumu \"Tamamlandı\"dır.",
   "Yüksek", "AC-9"]
tc(26, *DUP)

tc(27, "PDF dekont indirilir ve alıcı IBAN'ı maskelidir", OK,
   f"1. IBAN: {IB_DENIZ}, Alıcı: \"Deniz Arıkan\", Tutar: 2.500,00 ile transfer yap.\n"
   "2. Sonuç ekranında \"Dekont\" butonuna dokun.\n"
   "3. İndirilen PDF'i aç.",
   "- PDF dekont açılır; tutar, tarih-saat, alıcı adı ve açıklama yer alır.\n"
   "- Alıcı IBAN'ı \"TR48 **** **** **** **** **44 06\" şeklinde, yalnızca ilk 4 ve son 4 karakter görünür biçimde yazar.",
   "Yüksek", "AC-9")

tc(28, "Açıklama boş bırakılırsa dekontta \"FAST Transfer\" yazar", OK,
   f"1. IBAN: {IB_DENIZ}, Alıcı: \"Deniz Arıkan\", Tutar: 300,00 gir; Açıklama alanını boş bırak.\n"
   "2. Transferi tamamla.\n"
   "3. Sonuç ekranından PDF dekontu indir ve aç.",
   "- Dekontun açıklama alanında \"FAST Transfer\" yazar.",
   "Düşük", "AC-10")

tc(29, "140 karakterlik açıklama kabul edilir", OK,
   f"1. IBAN: {IB_DENIZ}, Alıcı: \"Deniz Arıkan\", Tutar: 300,00 gir.\n"
   "2. Açıklama alanına tam 140 karakterlik metin gir (test verisi: \"A\" harfi 140 kez).\n"
   "3. Transferi tamamla ve PDF dekontu aç.",
   "- Sayaç \"140/140\" gösterir, hata mesajı gösterilmez.\n"
   "- Dekontta açıklamanın 140 karakterinin tamamı görünür.",
   "Orta", "AC-10")

tc(30, "Açıklama alanına 141. karakter girilemez", OK,
   "1. IBAN'a Gönder ekranını aç.\n"
   "2. Açıklama alanına 140 karakterlik metin gir (\"A\" harfi 140 kez).\n"
   "3. 141. karakter olarak \"B\" yazmayı dene.",
   "- \"B\" karakteri alana eklenmez.\n"
   "- Sayaç \"140/140\" olarak kalır.",
   "Orta", "AC-10")

tc(31, "Uçtan uca FAST transferi ve doğrulamalar", OK,
   f"1. IBAN'a Gönder ekranını aç, IBAN alanına {IB_DENIZ_BADCHK} gir ve hata mesajını kontrol et.\n"
   f"2. IBAN'ı {IB_DENIZ} olarak düzelt.\n"
   "3. Alıcı adını boş bırak ve hata mesajını kontrol et; ardından \"Deniz Arıkan\" gir.\n"
   "4. Tutar alanına 60.000,00 gir ve hata mesajını kontrol et.\n"
   "5. Tutarı 15.000,00 olarak değiştir, Devam > Onayla'ya dokun.\n"
   "6. OTP ekranında 2 kez yanlış kod gir, mesajları kontrol et.\n"
   "7. Doğru kodu gir.\n"
   "8. Dekontu indir; Hesap Hareketleri'ni ve bakiyeyi kontrol et.",
   "Tüm adımlar başarılı olmalı.",
   "Yüksek", "AC-1, AC-2, AC-3, AC-6, AC-9")

tc(32, "Transfer ekranı kontrolü", "Uygulama cihaza yüklü.",
   "1. Uygulamaya giriş yap.\n"
   "2. Para Transferi ekranını aç.\n"
   "3. Ekranın çalıştığını kontrol et.",
   "Ekran düzgün çalışmalı, hata olmamalı.",
   "Orta", "AC-1")

tc(33, "Hatalı girişlerde hata mesajları", OK,
   "1. IBAN'a Gönder ekranını aç.\n"
   "2. Alanlara hatalı değerler gir.\n"
   "3. Devam'a dokun.",
   "Uygun hata mesajları gösterilmeli.",
   "Yüksek", "AC-1, AC-2, AC-3")

tc(34, "Alıcı adı yalnızca boşluklardan oluşamaz", OK,
   "1. IBAN'a Gönder ekranını aç.\n"
   f"2. Alıcı IBAN alanına {IB_DENIZ}, tutara 100,00 gir.\n"
   "3. Alıcı Adı Soyadı alanına yalnızca 3 boşluk karakteri gir.",
   "TBD",
   "Orta", "AC-2")

tc(35, "OTP ekranında 180 saniyelik geri sayım gösterilir", OK,
   f"1. IBAN: {IB_MURAT}, Alıcı: \"Murat Yıldırım\", Tutar: 12.000,00 gir; Devam > Onayla'ya dokun.\n"
   "2. OTP ekranındaki geri sayım sayacını gözlemle.",
   "- Sayaç 03:00'dan başlayarak saniye saniye geri sayar.\n"
   "- Kod girilmezse sayaç 00:00'da durur.",
   "Orta", "AC-6")

tc(36, "Bakiyeden yüksek tutar girildiğinde uyarı verilmesi",
   "Kullanıcı mobil uygulamaya giriş yapmıştır. Hesap bakiyesi 1.000 TL'dir.",
   "1. IBAN'a Gönder ekranını aç.\n"
   f"2. Deniz Arıkan'ın IBAN'ını ({IB_DENIZ}) gir.\n"
   "3. 1.500 TL tutar gir ve Devam'a bas.",
   "Yetersiz bakiye uyarısı çıkar. Transfer gerçekleşmez ve bakiye değişmez.",
   "Orta", "AC-4")

tc(37, "Tutar alanına virgülden sonra 2'den fazla hane girilemez", OK,
   "1. IBAN'a Gönder ekranını aç.\n"
   "2. Tutar alanına \"150,255\" yazmayı dene.",
   "- Üçüncü ondalık hane (\"5\") alana eklenmez.\n"
   "- Alanda \"150,25\" görünür.",
   "Orta", "AC-3")

tc(38, *DUP)

tc(39, "Ana sayfada FAST kampanya banner'ı gösterilir",
   OK + "\n\"Ekim FAST Kampanyası\" test ortamında aktif.",
   "1. Uygulamaya giriş yap.\n"
   "2. Ana sayfadaki banner alanını incele.\n"
   "3. Banner'a dokun.",
   "- \"FAST ile 7/24 ücretsiz gönder\" banner'ı gösterilir.\n"
   "- Banner'a dokununca IBAN'a Gönder ekranı açılır.",
   "Düşük", "AC-11")

tc(40, "USD hesabından yurt dışına SWIFT transferi",
   "Kullanıcının USD vadesiz hesabı var, kullanılabilir bakiye 5.000,00 USD.",
   "1. Para Transferi > Yurt Dışına Gönder menüsünü aç.\n"
   f"2. Alıcı IBAN: {IB_DE}, SWIFT: KSTLDEFFXXX, Alıcı: \"Jonas Weber\", Tutar: 1.000,00 USD gir.\n"
   "3. Devam > Onayla'ya dokun.",
   "- Transfer talebi alınır.\n"
   "- Sonuç ekranında SWIFT referans numarası gösterilir.",
   "Orta", "")

INFO = [
    ["Alan", "Değer"],
    ["Doküman", "US-214 IBAN'a FAST Transferi – Manuel Test Seti"],
    ["Versiyon", "0.9 (gözden geçirme öncesi)"],
    ["Hazırlayan", "Burak Tunç, Elif Karadağ (Nehir Bank Test Ekibi)"],
    ["Tarih", "22.09.2026"],
    ["Test ortamı", "Nehir Mobil 4.12.0 test sürümü – https://mobil-test.nehirbank.example.test"],
    ["Ortak ön koşul",
     "Test kullanıcısı ft.test01 ile Nehir Mobil'e giriş yapılmıştır.\n"
     f"Vadesiz TL hesabı: {IB_SENDER}\n"
     "Kullanılabilir bakiye: 200.000,00 TL\n"
     "Kayıtlı cep telefonu: test SMS geçidine bağlı sanal numara\n"
     "O gün yapılmış giden transfer yoktur (aksi test ön koşulunda belirtilir)."],
    ["", ""],
    ["Öncelik", "Tanım"],
    ["Kritik", "Para kaybı, güvenlik / dolandırıcılık önleme veya yasal limitlerle ilgili kurallar. Her sürümde koşulur."],
    ["Yüksek", "Transferin tamamlanması için gerekli ana akış ve temel kontroller."],
    ["Orta", "Alan doğrulamaları, bilgi mesajları ve yan akışlar."],
    ["Düşük", "Kozmetik ve bilgilendirme amaçlı kontroller."],
]

# ---------------- XLSX writer ----------------
sst, sst_index = [], {}
def s(v):
    if v not in sst_index:
        sst_index[v] = len(sst)
        sst.append(v)
    return sst_index[v]

def col(n):
    r = ""
    while n:
        n, m = divmod(n - 1, 26)
        r = chr(65 + m) + r
    return r

def sheet_xml(rows, widths, header_style_rows, freeze=True, autofilter=True):
    out = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
           '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
           'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">']
    ncols = max(len(r) for r in rows)
    out.append('<dimension ref="A1:%s%d"/>' % (col(ncols), len(rows)))
    if freeze:
        out.append('<sheetViews><sheetView workbookViewId="0" tabSelected="1"><pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/>'
                   '<selection pane="bottomLeft" activeCell="A2" sqref="A2"/></sheetView></sheetViews>')
    else:
        out.append('<sheetViews><sheetView workbookViewId="0"/></sheetViews>')
    out.append('<sheetFormatPr defaultRowHeight="15"/>')
    out.append('<cols>' + ''.join('<col min="%d" max="%d" width="%s" customWidth="1"/>' % (i + 1, i + 1, w)
                                  for i, w in enumerate(widths)) + '</cols>')
    out.append('<sheetData>')
    for ri, row in enumerate(rows, start=1):
        style = 1 if ri in header_style_rows else 2
        cells = []
        for ci, v in enumerate(row, start=1):
            ref = "%s%d" % (col(ci), ri)
            if v == "":
                cells.append('<c r="%s" s="%d"/>' % (ref, style))
            else:
                cells.append('<c r="%s" s="%d" t="s"><v>%d</v></c>' % (ref, style, s(v)))
        out.append('<row r="%d">%s</row>' % (ri, ''.join(cells)))
    out.append('</sheetData>')
    if autofilter:
        out.append('<autoFilter ref="A1:%s%d"/>' % (col(ncols), len(rows)))
    out.append('<pageMargins left="0.7" right="0.7" top="0.75" bottom="0.75" header="0.3" footer="0.3"/>')
    out.append('</worksheet>')
    return ''.join(out)

rows1 = [HEADERS] + T
sheet1 = sheet_xml(rows1, [10, 40, 42, 62, 58, 10, 16], {1})
sheet2 = sheet_xml(INFO, [20, 100], {1, 9}, freeze=False, autofilter=False)

def sst_xml():
    items = []
    for v in sst:
        items.append('<si><t xml:space="preserve">%s</t></si>' % escape(v))
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" count="%d" uniqueCount="%d">%s</sst>'
            % (sum(1 for r in rows1 + INFO for v in r if v != ""), len(sst), ''.join(items)))

CT = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
      '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
      '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
      '<Default Extension="xml" ContentType="application/xml"/>'
      '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
      '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
      '<Override PartName="/xl/worksheets/sheet2.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
      '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
      '<Override PartName="/xl/sharedStrings.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml"/>'
      '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>'
      '<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>'
      '</Types>')

RELS = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
        '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>'
        '<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>'
        '</Relationships>')

WB = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
      '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
      'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
      '<bookViews><workbookView activeTab="0"/></bookViews>'
      '<sheets><sheet name="Test Cases" sheetId="1" r:id="rId1"/><sheet name="Bilgi" sheetId="2" r:id="rId2"/></sheets>'
      '<definedNames><definedName name="_xlnm._FilterDatabase" localSheetId="0" hidden="1">\'Test Cases\'!$A$1:$G$%d</definedName></definedNames>'
      '</workbook>' % len(rows1))

WB_RELS = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
           '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
           '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
           '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet2.xml"/>'
           '<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
           '<Relationship Id="rId4" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/sharedStrings" Target="sharedStrings.xml"/>'
           '</Relationships>')

STYLES = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
          '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
          '<fonts count="2"><font><sz val="11"/><name val="Calibri"/><family val="2"/></font>'
          '<font><b/><sz val="11"/><name val="Calibri"/><family val="2"/></font></fonts>'
          '<fills count="3"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill>'
          '<fill><patternFill patternType="solid"><fgColor rgb="FFD9E1F2"/><bgColor indexed="64"/></patternFill></fill></fills>'
          '<borders count="2"><border><left/><right/><top/><bottom/><diagonal/></border>'
          '<border><left style="thin"><color auto="1"/></left><right style="thin"><color auto="1"/></right>'
          '<top style="thin"><color auto="1"/></top><bottom style="thin"><color auto="1"/></bottom><diagonal/></border></borders>'
          '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
          '<cellXfs count="3">'
          '<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>'
          '<xf numFmtId="0" fontId="1" fillId="2" borderId="1" xfId="0" applyFont="1" applyFill="1" applyBorder="1" applyAlignment="1">'
          '<alignment vertical="center" wrapText="1"/></xf>'
          '<xf numFmtId="49" fontId="0" fillId="0" borderId="1" xfId="0" applyNumberFormat="1" applyBorder="1" applyAlignment="1">'
          '<alignment vertical="top" wrapText="1"/></xf>'
          '</cellXfs>'
          '<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>'
          '</styleSheet>')

CORE = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
        'xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" '
        'xmlns:dcmitype="http://purl.org/dc/dcmitype/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
        '<dc:title>US-214 FAST Transfer Test Seti</dc:title><dc:creator>Elif Karadağ</dc:creator>'
        '<cp:lastModifiedBy>Burak Tunç</cp:lastModifiedBy>'
        '<dcterms:created xsi:type="dcterms:W3CDTF">2026-09-15T08:30:00Z</dcterms:created>'
        '<dcterms:modified xsi:type="dcterms:W3CDTF">2026-09-22T14:10:00Z</dcterms:modified>'
        '</cp:coreProperties>')

APP = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
       '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" '
       'xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">'
       '<Application>Microsoft Excel</Application><DocSecurity>0</DocSecurity><ScaleCrop>false</ScaleCrop>'
       '<HeadingPairs><vt:vector size="2" baseType="variant"><vt:variant><vt:lpstr>Worksheets</vt:lpstr></vt:variant>'
       '<vt:variant><vt:i4>2</vt:i4></vt:variant></vt:vector></HeadingPairs>'
       '<TitlesOfParts><vt:vector size="2" baseType="lpstr"><vt:lpstr>Test Cases</vt:lpstr><vt:lpstr>Bilgi</vt:lpstr></vt:vector></TitlesOfParts>'
       '<Company>Nehir Bank A.Ş.</Company><AppVersion>16.0300</AppVersion></Properties>')

parts = [
    ("[Content_Types].xml", CT),
    ("_rels/.rels", RELS),
    ("docProps/core.xml", CORE),
    ("docProps/app.xml", APP),
    ("xl/workbook.xml", WB),
    ("xl/_rels/workbook.xml.rels", WB_RELS),
    ("xl/styles.xml", STYLES),
    ("xl/worksheets/sheet1.xml", sheet1),
    ("xl/worksheets/sheet2.xml", sheet2),
]
with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
    for name, data in parts + [("xl/sharedStrings.xml", sst_xml())]:
        zi = zipfile.ZipInfo(name, date_time=(2026, 9, 22, 14, 10, 0))
        zi.compress_type = zipfile.ZIP_DEFLATED
        zi.external_attr = 0o644 << 16
        z.writestr(zi, data.encode("utf-8"))

print("wrote", OUT, "tests:", len(T), "shared strings:", len(sst))
