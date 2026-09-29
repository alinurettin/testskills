project: Demo Bank – FAST ile para transferi (US-310)
language: tr
setup oturum: 'FAST ile Para Gönder' sayfası yeni oturumda açık (http://localhost:4174)
setup oturum: Bakiye 120.000,00 TL, 'Günlük kalan limit' 100.000,00 TL
setup oturum: Aksi belirtilmedikçe 'Alıcı IBAN' = TR330006100519786457841326, 'Alıcı adı' = Ayşe Test, 'Açıklama' = Kira
setup oturum: Test ortamı SMS kodu 123456
setup limit: 'FAST ile Para Gönder' sayfası yeni oturumda açık (http://localhost:4174); test ortamı SMS kodu 123456
setup limit: Aynı oturumda TR330006100519786457841326'ya 49.999,99 TL ve 49.000,00 TL (her biri SMS kodu 123456 ile) başarılı transfer yapılmış
setup limit: Günlük kullanım 98.999,99 TL; 'Günlük kalan limit' 1.000,01 TL
setup bakiye: 'FAST ile Para Gönder' sayfası yeni oturumda açık (http://localhost:4174); test ortamı SMS kodu 123456
setup bakiye: Bakiye 22.990,00 TL ve günlük kalan limit tutarı karşılıyor (seed gerekir; bu ortamda 49.000,00 TL + 48.000,00 TL transferleriyle hazırlanıyor, bkz. test planı bağımlılık B-1)

## TC-001 | 1,00 TL (alt sınır) transfer ücretsiz gerçekleşir ve dekont gösterilir
req: REQ-001, REQ-012 | pri: m | pol: + | tech: bva | ref: DS-001 C-04 | cat: functional
pre: @oturum
data: tutar=1,00
1. 'Tutar (TL)' alanına tutarı yaz, 'Devam'a tıkla [1,00] => 'Transfer başarıyla gerçekleşti.' mesajı; SMS doğrulama adımı açılmaz
2. 'Dekont' bölümünü incele => Tutar: 1,00 TL; İşlem ücreti: 0,00 TL; Toplam: 1,00 TL; Alıcı: TR330006100519786457841326; Açıklama: Kira
3. Bakiye ve kalan limiti incele => Bakiye 119.999,00 TL; 'Günlük kalan limit' 99.999,00 TL
tags: regression | auto: yes, deterministik sınır değeri | status: ready

## TC-002 | 0,99 TL (alt sınırın altı) reddedilir
req: REQ-001, REQ-012 | pri: m | pol: - | tech: bva | ref: DS-001 C-15 | cat: functional
pre: @oturum
data: tutar=0,99
1. 'Tutar (TL)' alanına tutarı yaz, 'Devam'a tıkla [0,99] => 'Tutar en az 1,00 TL olmalıdır.' mesajı; dekont gösterilmez
2. Bakiye ve kalan limiti incele => Bakiye 120.000,00 TL; 'Günlük kalan limit' 100.000,00 TL (değişmez)
tags: regression | auto: yes, deterministik sınır değeri | status: ready

## TC-003 | 50.000,00 TL (işlem üst sınırı) SMS doğrulama ile gerçekleşir
req: REQ-002, REQ-005 | pri: h | pol: + | tech: bva | ref: DS-001 C-09; DS-006 D05 | cat: functional
pre: @oturum
data: tutar=50.000,00; otp=123456
1. 'Tutar (TL)' alanına tutarı yaz, 'Devam'a tıkla [50.000,00] => 'Bu işlem için SMS doğrulaması gerekiyor.' mesajı; 'SMS doğrulama' bölümü açılır
2. 'SMS kodu' alanına kodu yaz, 'Onayla'ya tıkla [123456] => 'Transfer başarıyla gerçekleşti.'; dekontta Tutar 50.000,00 TL, İşlem ücreti 5,00 TL, Toplam 50.005,00 TL
3. Bakiye ve kalan limiti incele => Bakiye 69.995,00 TL; 'Günlük kalan limit' 50.000,00 TL
tags: smoke, regression | auto: yes, deterministik sınır değeri | status: ready

## TC-004 | 50.000,01 TL (işlem üst sınırının üstü) reddedilir
req: REQ-002 | pri: h | pol: - | tech: bva | ref: DS-001 C-16 | cat: functional
pre: @oturum
data: tutar=50.000,01
1. 'Tutar (TL)' alanına tutarı yaz, 'Devam'a tıkla [50.000,01] => 'İşlem başına en fazla 50.000,00 TL gönderebilirsiniz.' mesajı; SMS adımı ve dekont gösterilmez
2. Bakiye ve kalan limiti incele => Bakiye 120.000,00 TL; 'Günlük kalan limit' 100.000,00 TL
tags: regression | auto: yes, deterministik sınır değeri | status: ready

## TC-005 | Günlük toplam tam 100.000,00 TL'ye ulaşan transfer kabul edilir
req: REQ-003 | pri: h | pol: + | tech: bva | ref: DS-002 C-05 | cat: functional
obj: Kümülatif limit sınırı dahil (varsayım Q-002: toplam tam 100.000,00 TL'ye izin var, ücret hariç)
pre: @limit
data: tutar=1.000,01
1. 'Tutar (TL)' alanına tutarı yaz, 'Açıklama'ya 'Limit' yaz, 'Devam'a tıkla [1.000,01] => 'Transfer başarıyla gerçekleşti.'; dekontta Tutar 1.000,01 TL
2. Kalan limiti incele => 'Günlük kalan limit' 0,00 TL
tags: regression | auto: yes, kümülatif hazırlık otomasyonla hızlı | status: ready

## TC-006 | Günlük toplamı 100.000,01 TL'ye çıkaracak transfer reddedilir
req: REQ-003 | pri: c | pol: - | tech: bva | ref: DS-002 C-10 | cat: functional
obj: Kümülatif limit aşımının engellendiğinin go/no-go kontrolü (varsayım Q-002)
pre: @limit
data: tutar=1.000,02
1. 'Tutar (TL)' alanına tutarı yaz, 'Açıklama'ya 'Limit' yaz, 'Devam'a tıkla [1.000,02] => Günlük limit aşımını bildiren hata mesajı (role=alert); SMS adımı ve dekont gösterilmez
2. Bakiye ve kalan limiti incele => Bakiye ve 'Günlük kalan limit' (1.000,01 TL) değişmez
tags: smoke, regression | auto: yes, kritik para kuralı | status: ready

## TC-007 | Günlük toplamı 99.999,99 TL'ye çıkaran transfer kabul edilir
req: REQ-003 | pri: m | pol: + | tech: bva | ref: DS-002 C-04 | cat: functional
pre: @limit
data: tutar=1.000,00
1. 'Tutar (TL)' alanına tutarı yaz, 'Açıklama'ya 'Limit' yaz, 'Devam'a tıkla [1.000,00] => 'Transfer başarıyla gerçekleşti.'
2. Kalan limiti incele => 'Günlük kalan limit' 0,01 TL
tags: regression | auto: yes, 3-değer SDA komşusu | status: ready

## TC-008 | Günlük limit dolduktan sonra 1,00 TL transfer reddedilir
req: REQ-003 | pri: h | pol: - | tech: ep | ref: DS-002 C-07 | cat: functional
pre: @limit
pre: Ek olarak 1.000,01 TL başarılı transfer yapılmış; 'Günlük kalan limit' 0,00 TL
data: tutar=1,00
1. 'Tutar (TL)' alanına tutarı yaz, 'Açıklama'ya 'Limit2' yaz, 'Devam'a tıkla [1,00] => Günlük limit aşımını bildiren hata mesajı; dekont gösterilmez
2. Bakiyeyi incele => Bakiye değişmez; 'Günlük kalan limit' 0,00 TL
tags: regression | auto: yes, kümülatif kural | status: ready

## TC-009 | Reddedilen transfer bakiyeyi ve günlük limiti tüketmez
req: REQ-016, REQ-003 | pri: m | pol: - | tech: eg | ref: DS-002; fintech tutarlılık | cat: functional
pre: @oturum
1. 'Tutar (TL)' alanına tutarı yaz, 'Devam'a tıkla [50.000,01] => 'İşlem başına en fazla 50.000,00 TL gönderebilirsiniz.'
2. 'Tutar (TL)' alanına tutarı yaz, 'Devam'a tıkla [0,99] => 'Tutar en az 1,00 TL olmalıdır.'
3. Bakiye ve kalan limiti incele => Bakiye 120.000,00 TL; 'Günlük kalan limit' 100.000,00 TL
tags: regression | auto: yes, tutarlılık kontrolü | status: ready

## TC-010 | Kontrol basamağı hatalı (mod-97) IBAN reddedilir
req: REQ-004 | pri: h | pol: - | tech: ep | ref: check_ids.py varyant 'last digit changed' | cat: functional
pre: @oturum
data: iban=TR330006100519786457841327 (check_ids.py: INVALID mod-97); tutar=100,00
1. 'Alıcı IBAN' alanına IBAN'ı, 'Tutar (TL)' alanına 100,00 yaz, 'Devam'a tıkla [TR330006100519786457841327] => 'Geçersiz IBAN. Lütfen TR ile başlayan 26 karakterlik IBAN girin.' (veya kontrol basamağı hatasını belirten mesaj); dekont gösterilmez
2. Bakiyeyi incele => Bakiye 120.000,00 TL (değişmez)
tags: regression | auto: yes, doğrulama kuralı | status: ready

## TC-011 | 25 karakterlik IBAN reddedilir
req: REQ-004 | pri: m | pol: - | tech: bva | ref: check_ids.py varyant 'one character short' | cat: functional
pre: @oturum
data: iban=TR33000610051978645784132; tutar=100,00
1. 'Alıcı IBAN' alanına IBAN'ı, 'Tutar (TL)' alanına 100,00 yaz, 'Devam'a tıkla [TR33000610051978645784132] => 'Geçersiz IBAN. Lütfen TR ile başlayan 26 karakterlik IBAN girin.'; dekont gösterilmez
tags: regression | auto: yes, uzunluk sınırı | status: ready

## TC-012 | 27 karakterlik IBAN reddedilir
req: REQ-004 | pri: m | pol: - | tech: bva | ref: check_ids.py varyant 'one character long' | cat: functional
pre: @oturum
data: iban=TR3300061005197864578413260; tutar=100,00
1. 'Alıcı IBAN' alanına IBAN'ı, 'Tutar (TL)' alanına 100,00 yaz, 'Devam'a tıkla [TR3300061005197864578413260] => 'Geçersiz IBAN. Lütfen TR ile başlayan 26 karakterlik IBAN girin.'; dekont gösterilmez
tags: regression | auto: yes, uzunluk sınırı | status: ready

## TC-013 | TR dışı ülke kodlu IBAN reddedilir
req: REQ-004 | pri: m | pol: - | tech: ep | ref: check_ids.py varyant 'wrong country code' | cat: functional
pre: @oturum
data: iban=DE330006100519786457841326; tutar=100,00
1. 'Alıcı IBAN' alanına IBAN'ı, 'Tutar (TL)' alanına 100,00 yaz, 'Devam'a tıkla [DE330006100519786457841326] => 'Geçersiz IBAN. Lütfen TR ile başlayan 26 karakterlik IBAN girin.'; dekont gösterilmez
tags: regression | auto: yes, doğrulama kuralı | status: ready

## TC-014 | Boş IBAN reddedilir
req: REQ-004 | pri: l | pol: - | tech: ep | cat: functional
pre: @oturum
1. 'Alıcı IBAN' alanını boş bırak, 'Tutar (TL)' alanına 100,00 yaz, 'Devam'a tıkla [""] => 'Geçersiz IBAN. Lütfen TR ile başlayan 26 karakterlik IBAN girin.'; dekont gösterilmez
tags: regression | auto: yes, doğrulama kuralı | status: ready

## TC-015 | Boşluklu ve küçük harfli geçerli IBAN kabul edilir
req: REQ-004 | pri: l | pol: + | tech: ep | ref: check_ids.py varyantları (VALID); Q-011 | cat: functional
obj: Varsayım Q-011: biçim varyantları normalize edilerek kabul edilir
pre: @oturum
1. 'Alıcı IBAN' alanına boşluklu IBAN'ı, 'Tutar (TL)' alanına 100,00 yaz, 'Devam'a tıkla ["TR33 0006 1005 1978 6457 8413 26"] => 'Transfer başarıyla gerçekleşti.'; dekontta Alıcı TR330006100519786457841326
2. 'Yeni transfer'e tıkla; 'Alıcı IBAN' alanına küçük harfli IBAN'ı, 'Tutar (TL)' alanına 200,00 yaz, 'Devam'a tıkla [tr330006100519786457841326] => 'Transfer başarıyla gerçekleşti.'; dekontta Alıcı TR330006100519786457841326
tags: regression | auto: yes, biçim varyantı | status: ready

## TC-016 | 10.000,00 TL'de (OTP eşiği, dahil) SMS doğrulama istenir
req: REQ-005 | pri: h | pol: + | tech: bva | ref: DS-001 C-08 | cat: security
pre: @oturum
data: tutar=10.000,00
1. 'Tutar (TL)' alanına tutarı yaz, 'Devam'a tıkla [10.000,00] => 'Bu işlem için SMS doğrulaması gerekiyor.'; 'SMS doğrulama' bölümü açılır; dekont gösterilmez
2. Bakiyeyi incele => Bakiye 120.000,00 TL (OTP onayı olmadan değişmez)
3. 'SMS kodu' alanına kodu yaz, 'Onayla'ya tıkla [123456] => 'Transfer başarıyla gerçekleşti.'; dekontta Tutar 10.000,00 TL, İşlem ücreti 5,00 TL, Toplam 10.005,00 TL
tags: smoke, regression | auto: yes, SCA eşiği | status: ready

## TC-017 | 9.999,99 TL'de OTP istenmez, 5,00 TL ücret alınır
req: REQ-005, REQ-006 | pri: m | pol: + | tech: bva | ref: DS-001 C-07; DS-006 D03 | cat: functional
pre: @oturum
data: tutar=9.999,99
1. 'Tutar (TL)' alanına tutarı yaz, 'Devam'a tıkla [9.999,99] => 'Transfer başarıyla gerçekleşti.'; SMS doğrulama adımı açılmaz
2. 'Dekont' bölümünü incele => Tutar 9.999,99 TL; İşlem ücreti 5,00 TL; Toplam 10.004,99 TL
tags: regression | auto: yes, sınır komşusu | status: ready

## TC-018 | Hatalı SMS kodu ile transfer yapılmaz
req: REQ-018, REQ-005, REQ-006 | pri: h | pol: - | tech: dt | ref: DS-006 D06; DS-008 T9 | cat: security
obj: Varsayım Q-004: hatalı kodda transfer yapılmaz, hata mesajı gösterilir
pre: @oturum
data: tutar=20.000,00; otp=000000
1. 'Tutar (TL)' alanına tutarı yaz, 'Devam'a tıkla [20.000,00] => 'SMS doğrulama' bölümü açılır
2. 'SMS kodu' alanına hatalı kodu yaz, 'Onayla'ya tıkla [000000] => Hatalı kodu bildiren hata mesajı; dekont gösterilmez
3. Bakiye ve kalan limiti incele => Bakiye 120.000,00 TL; 'Günlük kalan limit' 100.000,00 TL
tags: regression | auto: yes, güvenlik negatif | status: ready

## TC-019 | SMS adımı açıkken değiştirilen tutar OTP ile onaylanamaz
req: REQ-018, REQ-005 | pri: h | pol: - | tech: st | ref: DS-008 N-08; Q-014 | cat: security
obj: Varsayım Q-014: OTP, istendiği andaki tutara bağlıdır; form kilitlenmeli ya da değişiklik yeni OTP gerektirmeli
pre: @oturum
1. 'Tutar (TL)' alanına tutarı yaz, 'Devam'a tıkla [20.000,00] => 'SMS doğrulama' bölümü açılır
2. 'Tutar (TL)' alanını değiştirmeyi dene [45.000,00] => Alan düzenlenemez VEYA değişiklik SMS adımını iptal eder
3. 'SMS kodu' alanına kodu yaz, 'Onayla'ya tıkla [123456] => 45.000,00 TL için transfer gerçekleşmez; dekont oluşursa Tutar 20.000,00 TL'dir
tags: regression | auto: yes, güvenlik geçersiz geçiş | status: ready

## TC-020 | 5.000,00 TL'de (ücret eşiği) ücret alınmaz
req: REQ-006, REQ-007 | pri: h | pol: + | tech: bva | ref: DS-001 C-05; DS-006 D01 | cat: functional
pre: @oturum
data: tutar=5.000,00
1. 'Tutar (TL)' alanına tutarı yaz, 'Devam'a tıkla [5.000,00] => 'Transfer başarıyla gerçekleşti.'
2. 'Dekont' bölümünü incele => Tutar 5.000,00 TL; İşlem ücreti 0,00 TL; Toplam 5.000,00 TL
3. Bakiyeyi incele => Bakiye 115.000,00 TL
tags: regression | auto: yes, ücret sınırı | status: ready

## TC-021 | 5.000,01 TL'de 5,00 TL ücret alınır; bakiye ve limit doğru düşer
req: REQ-006, REQ-007, REQ-016 | pri: h | pol: + | tech: bva | ref: DS-001 C-06; DS-006 D03 | cat: functional
pre: @oturum
data: tutar=5.000,01
1. 'Tutar (TL)' alanına tutarı yaz, 'Devam'a tıkla [5.000,01] => 'Transfer başarıyla gerçekleşti.'
2. 'Dekont' bölümünü incele => Tutar 5.000,01 TL; İşlem ücreti 5,00 TL; Toplam 5.005,01 TL
3. Bakiye ve kalan limiti incele => Bakiye 114.994,99 TL; 'Günlük kalan limit' 94.999,99 TL (varsayım Q-002: ücret limite dahil değil)
tags: smoke, regression | auto: yes, para hesaplaması | status: ready

## TC-022 | Tutar + ücret bakiyeye tam eşitse transfer gerçekleşir
req: REQ-008 | pri: m | pol: + | tech: bva | ref: DS-004 C-03; Q-006 | cat: functional
obj: Varsayım Q-006: tam eşitlik yeterli bakiye sayılır
pre: @bakiye
data: tutar=22.985,00; ucret=5,00; toplam=22.990,00
1. 'Tutar (TL)' alanına tutarı yaz, 'Devam'a tıkla, istenirse SMS kodu 123456 ile onayla [22.985,00] => 'Transfer başarıyla gerçekleşti.'; dekontta Toplam 22.990,00 TL
2. Bakiyeyi incele => Bakiye 0,00 TL
tags: regression | auto: yes, sınır değeri | status: ready

## TC-023 | Tutar bakiyeye sığıp tutar + ücret bakiyeyi 0,01 TL aşarsa transfer yapılmaz
req: REQ-008 | pri: h | pol: - | tech: bva | ref: DS-004 C-07; DS-006 D07 | cat: functional
obj: Ücretin bakiye kontrolüne dahil edildiğinin kontrolü (tutar 22.985,01 ≤ bakiye; toplam 22.990,01 > bakiye)
pre: @bakiye
data: tutar=22.985,01
1. 'Tutar (TL)' alanına tutarı yaz, 'Devam'a tıkla; SMS adımı açılırsa kodu 123456 ile onayla [22.985,01] => Yetersiz bakiyeyi bildiren mesaj; dekont gösterilmez
2. Bakiyeyi incele => Bakiye 22.990,00 TL (değişmez)
tags: regression | auto: yes, para kuralı | status: ready

## TC-024 | Tutar bakiyeyi aşarsa SMS gönderilmeden reddedilir
req: REQ-008, REQ-005 | pri: m | pol: - | tech: dt | ref: DS-006 D07/D08; Q-013 | cat: functional
obj: Varsayım Q-013: bakiye kontrolü OTP'den önce yapılır
pre: @bakiye
data: tutar=30.000,00
1. 'Tutar (TL)' alanına tutarı yaz, 'Devam'a tıkla [30.000,00] => Yetersiz bakiyeyi bildiren mesaj; 'SMS doğrulama' bölümü açılmaz; dekont gösterilmez
2. Bakiyeyi incele => Bakiye 22.990,00 TL (değişmez)
tags: regression | auto: yes, karar tablosu kolonu | status: ready

## TC-025 | Boş açıklama ile transfer reddedilir
req: REQ-009 | pri: l | pol: - | tech: bva | ref: DS-003 C-04 | cat: functional
pre: @oturum
1. 'Açıklama' alanını boş bırak, 'Tutar (TL)' alanına 100,00 yaz, 'Devam'a tıkla [""] => 'Açıklama zorunludur.' mesajı; dekont gösterilmez
tags: regression | auto: yes, doğrulama | status: ready

## TC-026 | Yalnız boşluktan oluşan açıklama reddedilir
req: REQ-009 | pri: l | pol: - | tech: ep | ref: DS-003 C-06; Q-007 | cat: functional
pre: @oturum
1. 'Açıklama' alanına yalnız boşluk yaz, 'Tutar (TL)' alanına 100,00 yaz, 'Devam'a tıkla ["   "] => 'Açıklama zorunludur.' mesajı; dekont gösterilmez
tags: regression | auto: yes, doğrulama | status: ready

## TC-027 | Türkçe karakterli 50 karakterlik açıklama kabul edilir ve dekontta tam görünür
req: REQ-010, REQ-012 | pri: l | pol: + | tech: bva | ref: DS-003 C-03 | cat: functional
pre: @oturum
data: aciklama=ÇĞİÖŞÜçğıöşü kira ödemesi Ekim 2026 daire 4B xxxxx (50 karakter)
1. 'Açıklama' alanına 50 karakterlik metni, 'Tutar (TL)' alanına 100,00 yaz, 'Devam'a tıkla [ÇĞİÖŞÜçğıöşü kira ödemesi Ekim 2026 daire 4B xxxxx] => 'Transfer başarıyla gerçekleşti.'
2. 'Dekont' bölümünü incele => Açıklama alanında metnin 50 karakterin tamamı, Türkçe karakterler bozulmadan görünür
tags: regression | auto: yes, uzunluk sınırı | status: ready

## TC-028 | 51 karakterlik açıklama ile transfer yapılmaz
req: REQ-010 | pri: l | pol: - | tech: bva | ref: DS-003 C-07; Q-007 | cat: functional
pre: @oturum
1. 'Açıklama' alanına 51 karakter yaz, 'Tutar (TL)' alanına 100,00 yaz, 'Devam'a tıkla [xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx] => Uzunluk hatası mesajı VEYA alan 50 karakterden fazlasını kabul etmez; 51 karakterlik açıklamayla dekont oluşmaz
tags: regression | auto: yes, uzunluk sınırı | status: ready

## TC-029 | 60 sn içinde aynı IBAN ve tutara ikinci transferde uyarı; 'Vazgeç' transferi durdurur
req: REQ-011 | pri: h | pol: - | tech: dt | ref: DS-007 D03; DS-008 T4, T7 | cat: functional
pre: @oturum
pre: Aynı oturumda TR330006100519786457841326'ya 100,00 TL başarılı transfer yapılmış (bakiye 119.900,00 TL)
1. 'Yeni transfer'e tıkla; aynı IBAN'a 100,00 TL için 'Devam'a tıkla (ilk transferden < 60 sn sonra) [100,00] => 'Tekrar uyarısı' bölümünde 'Aynı alıcıya aynı tutarda 60 saniye içinde transfer yaptınız. Yine de göndermek istiyor musunuz?' metni
2. 'Vazgeç'e tıkla => Dekont gösterilmez; bakiye 119.900,00 TL (ikinci transfer yapılmaz)
tags: regression | auto: yes, mükerrer ödeme riski | status: ready

## TC-030 | Tekrar uyarısında 'Yine de gönder' ikinci transferi gerçekleştirir
req: REQ-011 | pri: m | pol: + | tech: st | ref: DS-008 T5; Q-003 | cat: functional
pre: @oturum
pre: Aynı oturumda TR330006100519786457841326'ya 100,00 TL başarılı transfer yapılmış
1. 'Yeni transfer'e tıkla; aynı IBAN'a 100,00 TL için 'Devam'a tıkla [100,00] => 'Tekrar uyarısı' bölümü görünür
2. 'Yine de gönder'e tıkla => 'Transfer başarıyla gerçekleşti.'; bakiye 119.800,00 TL
tags: regression | auto: yes, akış | status: ready

## TC-031 | Önceki transferden 59 sn sonra aynı IBAN ve tutarda uyarı gösterilir
req: REQ-011 | pri: m | pol: - | tech: bva | ref: DS-005 C-04; Q-003 | cat: functional
pre: @oturum
pre: Saat kontrol edilebilir (Playwright page.clock); 100,00 TL başarılı transfer yapılmış
1. Saati 59 sn ileri al; 'Yeni transfer'e tıkla; aynı IBAN'a 100,00 TL için 'Devam'a tıkla [59 sn] => 'Tekrar uyarısı' bölümü görünür
tags: regression | auto: yes, saat kontrolü gerekir | status: ready

## TC-032 | Önceki transferden 60 sn sonra aynı IBAN ve tutarda uyarı gösterilmez
req: REQ-011 | pri: m | pol: + | tech: bva | ref: DS-005 C-05; DS-007 D01; Q-003 | cat: functional
obj: Varsayım Q-003: 60. saniyede pencere kapanmıştır
pre: @oturum
pre: Saat kontrol edilebilir (Playwright page.clock); 100,00 TL başarılı transfer yapılmış
1. Saati 60 sn ileri al; 'Yeni transfer'e tıkla; aynı IBAN'a 100,00 TL için 'Devam'a tıkla [60 sn] => Uyarı gösterilmez; 'Transfer başarıyla gerçekleşti.'
tags: regression | auto: yes, saat kontrolü gerekir | status: ready

## TC-033 | Aynı IBAN'a farklı tutarda 60 sn içinde transferde uyarı gösterilmez
req: REQ-011 | pri: m | pol: + | tech: dt | ref: DS-007 D02 | cat: functional
pre: @oturum
pre: Aynı oturumda TR330006100519786457841326'ya 100,00 TL başarılı transfer yapılmış
1. 'Yeni transfer'e tıkla; aynı IBAN'a 100,01 TL için 'Devam'a tıkla [100,01] => Uyarı gösterilmez; 'Transfer başarıyla gerçekleşti.'
tags: regression | auto: yes, karar tablosu kolonu | status: ready

## TC-034 | Aynı IBAN boşluklu yazılsa da 60 sn içinde uyarı gösterilir
req: REQ-011 | pri: m | pol: - | tech: eg | ref: Q-003, Q-011 | cat: functional
obj: Varsayım Q-003: "aynı alıcı" normalize IBAN ile karşılaştırılır; biçim farkı kontrolü atlatmamalı
pre: @oturum
pre: Aynı oturumda TR330006100519786457841326'ya 100,00 TL başarılı transfer yapılmış
1. 'Yeni transfer'e tıkla; 'Alıcı IBAN'a boşluklu yaz, 100,00 TL için 'Devam'a tıkla ["TR33 0006 1005 1978 6457 8413 26"] => 'Tekrar uyarısı' bölümü görünür
tags: regression | auto: yes, hata tahmini | status: ready

## TC-035 | Tekrar uyarısı sonrası ≥ 10.000,00 TL transfer yine SMS doğrulaması ister
req: REQ-011, REQ-005 | pri: m | pol: + | tech: st | ref: DS-008 T6, T8 | cat: security
pre: @oturum
pre: Aynı oturumda TR330006100519786457841326'ya 20.000,00 TL (SMS kodu 123456) başarılı transfer yapılmış
1. 'Yeni transfer'e tıkla; aynı IBAN'a 20.000,00 TL için 'Devam'a tıkla [20.000,00] => 'Tekrar uyarısı' bölümü görünür
2. 'Yine de gönder'e tıkla => 'SMS doğrulama' bölümü açılır; dekont gösterilmez
3. 'SMS kodu' alanına kodu yaz, 'Onayla'ya tıkla [123456] => 'Transfer başarıyla gerçekleşti.'; bakiye 79.990,00 TL
tags: regression | auto: yes, akış | status: ready

## TC-036 | Sonuç ekranı ve dekont onaydan sonra 3 sn içinde görünür
req: REQ-013, REQ-012 | pri: m | pol: + | tech: cl | ref: Q-008 | cat: performance
obj: Varsayım Q-008: tekil kullanıcı, test ortamı, onaydan dekonta ≤ 3 sn; yük altında hedef tanımlanmadı
pre: @oturum
1. 'Tutar (TL)' alanına 250,00 yaz, 'Devam'a tıkla ve süreyi ölç [250,00] => 'Dekont' bölümü ≤ 3 sn içinde görünür
tags: regression | auto: yes, zaman ölçümü | status: ready

## TC-037 | Pazar 23:30'da (mesai dışı) transfer gerçekleşir
req: REQ-014 | pri: m | pol: + | tech: ep | cat: functional
pre: @oturum
pre: Tarayıcı saati Pazar 04.10.2026 23:30 (Europe/Istanbul) olarak sabitlenmiş (Playwright page.clock)
1. 'Tutar (TL)' alanına 300,00 yaz, 'Devam'a tıkla [300,00] => 'Transfer başarıyla gerçekleşti.'; mesai saati uyarısı gösterilmez
tags: regression | auto: yes, saat kontrolü | status: ready

## TC-038 | Kayıtlı alıcı listeden seçilerek transfer yapılır
req: REQ-015 | pri: m | pol: + | tech: uc | ref: Q-009 | cat: functional
obj: Varsayım Q-009: kayıtlı alıcı seçimi bu sürümde kapsamda
pre: @oturum
pre: Test müşterisinin en az bir kayıtlı alıcısı var
1. Transfer ekranında kayıtlı alıcı seçim kontrolünü aç => Kayıtlı alıcılar listelenir
2. Bir kayıtlı alıcı seç => 'Alıcı IBAN' ve 'Alıcı adı' otomatik dolar
tags: regression | auto: yes, arayüz kontrolü | status: ready

## TC-039 | 'Devam'a çift tıklama tek transfer oluşturur
req: REQ-017 | pri: h | pol: - | tech: eg | ref: fintech idempotency | cat: functional
obj: Çift tıklamanın iki kez para çıkarması riski
pre: @oturum
1. 'Tutar (TL)' alanına 700,00 yaz, 'Devam'a çift tıkla [700,00] => 'Transfer başarıyla gerçekleşti.'; en fazla bir transfer gerçekleşir
2. Bakiye ve kalan limiti incele => Bakiye 119.300,00 TL; 'Günlük kalan limit' 99.300,00 TL (tek düşüş)
tags: regression | auto: yes, hata tahmini | status: ready

## TC-040 | '1.000,50' biçimli tutar doğru ayrıştırılır
req: REQ-019 | pri: h | pol: + | tech: ep | cat: functional
pre: @oturum
1. 'Tutar (TL)' alanına tutarı yaz, 'Devam'a tıkla [1.000,50] => 'Transfer başarıyla gerçekleşti.'; dekontta Tutar 1.000,50 TL, Toplam 1.000,50 TL
2. Bakiyeyi incele => Bakiye 118.999,50 TL
tags: regression | auto: yes, yerel ayar biçimi | status: ready

## TC-041 | Sayısal olmayan tutar reddedilir
req: REQ-019 | pri: m | pol: - | tech: ep | ref: DS-001 C-13 | cat: functional
pre: @oturum
1. 'Tutar (TL)' alanına metin yaz, 'Devam'a tıkla [abc] => Tutar hatası mesajı; dekont gösterilmez; bakiye 120.000,00 TL
tags: regression | auto: yes, doğrulama | status: ready

## TC-042 | İkiden fazla ondalık basamaklı tutar reddedilir
req: REQ-019 | pri: m | pol: - | tech: eg | ref: Q-012 | cat: functional
obj: Varsayım Q-012: '1,005' yuvarlanmaz, reddedilir
pre: @oturum
1. 'Tutar (TL)' alanına tutarı yaz, 'Devam'a tıkla [1,005] => Tutar biçimi hatası mesajı; dekont gösterilmez; bakiye 120.000,00 TL
tags: regression | auto: yes, para yuvarlama | status: ready

## TC-043 | Negatif tutar reddedilir
req: REQ-001, REQ-019 | pri: m | pol: - | tech: ep | ref: DS-001 C-14 | cat: functional
pre: @oturum
1. 'Tutar (TL)' alanına tutarı yaz, 'Devam'a tıkla [-100,00] => Tutar hatası mesajı (ör. 'Tutar en az 1,00 TL olmalıdır.'); dekont gösterilmez; bakiye 120.000,00 TL
tags: regression | auto: yes, doğrulama | status: ready

## TC-044 | Boş tutar reddedilir
req: REQ-019 | pri: l | pol: - | tech: ep | ref: DS-001 C-12 | cat: functional
pre: @oturum
1. 'Tutar (TL)' alanını boş bırak, 'Devam'a tıkla [""] => Tutar hatası mesajı; dekont gösterilmez
tags: regression | auto: yes, doğrulama | status: ready

## TC-045 | Nokta ondalık ayırıcılı '100.50' tutarı 10.050 TL olarak işlenmez
req: REQ-019 | pri: h | pol: - | tech: eg | ref: Q-012 | cat: functional
obj: Varsayım Q-012: yalnız TR biçimi; '100.50' geçersiz biçim olarak reddedilir. Risk: 100 kat fazla para gönderimi
pre: @oturum
1. 'Tutar (TL)' alanına tutarı yaz, 'Devam'a tıkla [100.50] => Tutar biçimi hatası mesajı; 10.050,00 TL veya 100,50 dışında bir tutarla dekont oluşmaz
2. Bakiyeyi incele => Bakiye 120.000,00 TL
tags: regression | auto: yes, hata tahmini (para) | status: ready

## TC-047 | Virgülsüz TR binlik biçimli '15.000' tutarı 15,00 TL olarak gönderilmez
req: REQ-019 | pri: h | pol: - | tech: eg | ref: Q-012; hata tahmini (binlik/ondalık ayırıcı) | cat: functional
obj: TR biçiminde '.' binlik ayırıcıdır; '15.000' 15.000,00 TL demektir. Risk: kullanıcının niyetinden 1000 kat farklı tutar gönderimi
pre: @oturum
1. 'Tutar (TL)' alanına tutarı yaz, 'Devam'a tıkla [15.000] => Ya 15.000,00 TL için SMS doğrulama adımı açılır ya da tutar biçimi hatası gösterilir; 15,00 TL tutarında dekont oluşmaz
2. Bakiyeyi incele => Bakiye 119.985,00 TL değildir (15,00 TL gönderilmemiştir)
tags: regression | auto: yes, hata tahmini (para) | status: ready

## TC-046 | Keşif turu: oturum, yenileme, geri tuşu ve çoklu sekmede FAST transferi
req: REQ-003, REQ-011, REQ-017 | pri: m | pol: - | tech: ex | cat: functional
obj: 45 dk'lık keşif oturumu: sayfa yenileme ve çoklu sekmede günlük limit/mükerrer kontrolünün atlatılması, Enter tuşuyla gönderim, uzun/HTML açıklama, yavaş ağ
pre: @oturum
1. Tüzüğü uygula; bulguları not al => Oturum notları ve bulgular kayıtlı; limit/mükerrer kontrolünün atlatılabildiği her yol hata olarak açılmış
tags: exploratory | auto: no, keşif testi | status: ready
