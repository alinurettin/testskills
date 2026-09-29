# Hata Raporları: US-310 FAST ile para transferi (BANK-310)

Ortak ortam: test ortamı http://localhost:4174 (demo-app) · Chromium (Playwright 1.63, Desktop Chrome) · Windows 11 · tr-TR / Europe/Istanbul · test müşterisi (bakiye 120.000,00 TL, her oturumda günlük kullanım sıfırlanır) · koşu 2026-09-29.
Tekrarlanabilirlik: tüm hatalar 4/4 (1 koşu + `--repeat-each=3`); akıcı (flaky) test yok.
Kanıt: `automation/test-results/<test klasörü>/test-failed-1.png`, `video.webm`, `error-context.md`. Yerel koşuda `retries=0` olduğu için trace yalnız CI'da (on-first-retry) üretilir; gerekirse `--trace on` ile yeniden koşulabilir.
Anahtarlar geçicidir (DEF-00x); Jira'ya açıldığında `qa/defects.json` ve `qa/results.json` güncellenmelidir. Öncelik PO tarafından kesinleştirilecek.

---

## DEF-001 · Günlük 100.000,00 TL FAST limiti kümülatif uygulanmıyor; limit dolduktan sonra transfer gerçekleşiyor
- **Bağlantılar:** TC-006 (kritik, başarısız), TC-008 (başarısız) · REQ-003 (AK-2) · ilgili: DEF-003
- **Ön koşul:** Yeni oturum; aynı IBAN'a (TR330006100519786457841326) 49.999,99 TL ve 49.000,00 TL (SMS 123456) başarılı transfer; 'Günlük kalan limit' 1.000,01 TL
- **Adımlar:** 1) 'Tutar (TL)' = 1.000,02, 'Açıklama' = Limit, 'Devam'a tıkla
- **Beklenen (REQ-003):** Gün içindeki başarılı transferlerin toplamı 100.000,00 TL'yi aşamaz → transfer reddedilir, limit mesajı gösterilir, bakiye 20.990,01 TL ve kalan limit 1.000,01 TL kalır
- **Gerçekleşen:** "Transfer başarıyla gerçekleşti." · dekont oluşur · günlük toplam 100.000,01 TL
- **Sınırın iki yanı:** toplam 99.999,99 TL (TC-007) ve 100.000,00 TL (TC-005) kabul — doğru; toplam 100.000,01 TL kabul — hatalı. Limit 0,00 TL gösterilirken 1,00 TL de gönderiliyor (TC-008). Keşif sırasında aynı oturumda toplam 100.001,00 TL gönderildi.
- **Önem:** critical (para limit dışında çıkıyor, tüm müşteriler, mevzuat/limit ihlali; DEF-003 ile birlikte 10.000,00 TL'lik OTP'siz tekrarlarla hesap boşaltılabilir)
- **Kanıt:** `test-results/req-003-gunluk-fast-limiti-ffb18-karacak-transfer-reddedilir-chromium/`, `…-af506-1-00-TL-transfer-reddedilir-chromium/`
- **Not (şüphe):** Kalan limit göstergesi doğru hesaplanıyor; limit yalnız işlem başına kontrol ediliyor, kümülatif kontrol yok gibi.

## DEF-002 · İşlem üst sınırı 50.000,00 TL'lik transfer reddediliyor (49.999,99 TL kabul)
- **Bağlantılar:** TC-003 (başarısız) · REQ-002 (AK-1)
- **Adımlar:** 1) Yeni oturumda 'Tutar (TL)' = 50.000,00, 'Devam'a tıkla
- **Beklenen (REQ-002):** "en fazla 50.000,00 TL" → 50.000,00 TL dahil; SMS doğrulama adımı açılır, onay sonrası dekontta Tutar 50.000,00 / Ücret 5,00 / Toplam 50.005,00 TL
- **Gerçekleşen:** "İşlem başına en fazla 50.000,00 TL gönderebilirsiniz." — mesaj kendisiyle çelişiyor; SMS adımı açılmıyor
- **Sınırın iki yanı:** 49.999,99 TL → SMS adımı (doğru); 50.000,00 TL → red (hatalı); 50.000,01 TL → red (doğru, TC-004)
- **Önem:** medium (para yanlış hareket etmiyor; iki işlemle geçici çözüm var) · Öncelik önerisi: high (AK metninin doğrudan ihlali, müşteri görünür)
- **Kanıt:** `test-results/req-002-islem-basina-azami-a462a-S-doğrulama-ile-gerçekleşir-chromium/`
- **Not (şüphe):** karşılaştırma `<= 50000` yerine `< 50000`.

## DEF-003 · Tam 10.000,00 TL transferde SMS OTP istenmiyor (10.000,01 TL'de isteniyor)
- **Bağlantılar:** TC-016 (başarısız) · REQ-005 (AK-4) · ilgili: DEF-001
- **Adımlar:** 1) Yeni oturumda 'Tutar (TL)' = 10.000,00, 'Devam'a tıkla
- **Beklenen (REQ-005):** "10.000,00 TL ve üzeri" → SMS doğrulama adımı açılır; OTP'siz transfer yapılmaz
- **Gerçekleşen:** OTP istenmeden "Transfer başarıyla gerçekleşti."; dekont Tutar 10.000,00 / Ücret 5,00 / Toplam 10.005,00 TL; bakiye 109.995,00 TL
- **Sınırın iki yanı:** 9.999,99 TL → OTP yok (doğru, TC-017); 10.000,00 TL → OTP yok (hatalı); 10.000,01 TL → OTP isteniyor (doğru)
- **Önem:** high (güçlü müşteri doğrulaması eşikte atlanıyor; tek tutar değeri) · Öncelik önerisi: critical (DEF-001 ile birlikte limitsiz ve OTP'siz 10.000,00 TL'lik tekrarlar mümkün)
- **Kanıt:** `test-results/req-005-10-000-00-tl-ve-uz-f4abd-dahil-SMS-doğrulama-istenir-chromium/`
- **Not (şüphe):** `>= 10000` yerine `> 10000`.

## DEF-004 · Kontrol basamağı (mod-97) hatalı IBAN'a transfer başarılı sayılıyor
- **Bağlantılar:** TC-010 (başarısız) · REQ-004 (AK-3)
- **Test verisi:** TR330006100519786457841327 — `check_ids.py iban`: INVALID (mod-97 check failed); geçerli örnek …326'nın son hanesi değiştirilmiş
- **Adımlar:** 1) Yeni oturumda 'Alıcı IBAN' = TR330006100519786457841327, 'Tutar (TL)' = 100,00, 'Açıklama' = Kira, 'Devam'a tıkla
- **Beklenen (REQ-004):** "doğru kontrol basamağı" → transfer yapılmaz, geçersiz IBAN mesajı gösterilir, bakiye 120.000,00 TL kalır
- **Gerçekleşen:** "Transfer başarıyla gerçekleşti."; dekontta Alıcı TR330006100519786457841327; bakiye 119.900,00 TL
- **Karşılaştırma:** 25/27 karakter ve DE ülke kodu doğru reddediliyor (TC-011…TC-013) — yalnız uzunluk/önek kontrol ediliyor
- **Önem:** high (geçersiz hesaba para çıkışı "başarılı" gösteriliyor; iade/mutabakat sorunu)
- **Kanıt:** `test-results/req-004-alici-iban-dogrula-90ecc-talı-mod-97-IBAN-reddedilir-chromium/`

## DEF-005 · Tam 5.000,00 TL transferde 5,00 TL işlem ücreti alınıyor (eşik dahil uygulanıyor)
- **Bağlantılar:** TC-020 (başarısız) · REQ-006, REQ-007 (AK-5)
- **Adımlar:** 1) Yeni oturumda 'Tutar (TL)' = 5.000,00, 'Devam'a tıkla 2) Dekontu incele
- **Beklenen (REQ-006):** "5.000,00 TL'yi aşan" transferlerde ücret → 5.000,00 TL'de İşlem ücreti 0,00 TL, Toplam 5.000,00 TL, bakiye 115.000,00 TL
- **Gerçekleşen:** İşlem ücreti 5,00 TL, Toplam 5.005,00 TL; bakiye 114.995,00 TL (keşifte '5000' girişiyle de aynı)
- **Sınırın iki yanı:** 4.999,99 TL → 0,00 TL (doğru); 5.000,00 TL → 5,00 TL (hatalı); 5.000,01 TL → 5,00 TL (doğru, TC-021)
- **Önem:** high (yuvarlak ve sık kullanılan tutarda tüm müşterilerden haksız ücret)
- **Kanıt:** `test-results/req-006-5-000-00-tl-yi-asa-70dcd-e-ücret-eşiği-ücret-alınmaz-chromium/`
- **Not (şüphe):** `> 5000` yerine `>= 5000`.

## DEF-006 · Transfer ekranında kayıtlı alıcı seçimi yok
- **Bağlantılar:** TC-038 (başarısız) · REQ-015 (hikâye metni) · Q-009 (kapsam sorusu açık)
- **Adımlar:** 1) Yeni oturumda 'FAST ile Para Gönder' sayfasını aç
- **Beklenen (REQ-015, varsayım Q-009):** Kayıtlı alıcılar listelenir ve seçilince 'Alıcı IBAN'/'Alıcı adı' dolar
- **Gerçekleşen:** Sayfada yalnız 'Alıcı IBAN', 'Alıcı adı', 'Tutar (TL)', 'Açıklama' alanları ve 'Devam' düğmesi var; kayıtlı alıcı kontrolü yok
- **Önem:** medium (yeni IBAN'a gönderim çalışıyor; geçici çözüm var) — PO kapsam dışı derse "rejected/deferred" yapılmalı
- **Kanıt:** `test-results/req-015-kayitli-aliciya-tr-31395--seçilerek-transfer-yapılır-chromium/`

## DEF-007 · Virgülsüz tutarda nokta ondalık sayılıyor: '15.000' 15,00 TL olarak gönderiliyor
- **Bağlantılar:** TC-047 (başarısız), TC-045 (başarısız, aynı kök neden) · REQ-019 · Q-012
- **Adımlar:** 1) Yeni oturumda 'Tutar (TL)' = 15.000, 'Devam'a tıkla
- **Beklenen (REQ-019, TR biçimi: '.' binlik ayırıcı):** 15.000,00 TL olarak işlenir (SMS adımı açılır) ya da biçim hatası gösterilir; 15,00 TL gönderilmez
- **Gerçekleşen:** OTP istenmeden "Transfer başarıyla gerçekleşti."; dekont Tutar 15,00 TL; bakiye 119.985,00 TL. Aynı şekilde '1.000' → 1,00 TL; '100.50' → 100,50 TL (TC-045). Virgüllü '1.000,50' doğru ayrıştırılıyor (TC-040).
- **Etki:** Kullanıcının niyetinden 1000 kat farklı tutar gönderilir; ayrıca '10.000' girişi OTP eşiğini de devre dışı bırakır (10,00 TL olarak işlenir).
- **Önem:** high
- **Kanıt:** `test-results/req-019-tutar-bicimi-ve-ge-db51a-15-00-TL-olarak-gönderilmez-chromium/`, `…-ced71-ı-10-050-TL-olarak-işlenmez-chromium/`
- **Not:** TC-045'in beklenen sonucu (red) Q-012 varsayımına dayanıyor; PO noktayı ondalık kabul etmeye karar verirse TC-045 güncellenir, ancak '15.000' belirsizliği yine çözülmelidir.
