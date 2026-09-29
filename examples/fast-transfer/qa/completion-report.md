# Test Tamamlama Raporu: Demo Bank – FAST ile para transferi (US-310)

2026-09-29 · US-310 test ortamı koşusu 2026-09-29 (chromium)

## Özet

Çıkış kriterleri: 9 kriterden 4 tanesi karşılandı. Yayın kararı paydaşlara aittir; karar için aşağıdaki kalan riskleri kullanın.

- Gereksinim kapsamı: 19/19 (100.0%)
- Koşum: 46/47 (97.9%) · passed 37 · failed 9 · blocked 0 · not run 1
- Geçme oranı: 80.4%
- Otomasyonla koşulan: 46/46 (100.0%)
- Açık bloke eden soru: 1
- Hatalar (açık, defects.json): critical: 1, high: 4, medium: 2

## Çıkış kriterleri

| Kriter | Hedef | Gerçekleşen | Durum |
|---|---|---|---|
| Gereksinim kapsamı ≥ | 100 | 100.0 | ✔ karşılandı |
| Koşulan test ≥ | 95 | 97.9 | ✔ karşılandı |
| Geçme oranı ≥ | 95 | 80.4 | ✘ karşılanmadı |
| Açık hata ≤ (critical) | 0 | 1 | ✘ karşılanmadı |
| Açık hata ≤ (high) | 0 | 4 | ✘ karşılanmadı |
| Açık hata ≤ (medium) | 3 | 2 | ✔ karşılandı |
| Tüm kritik riskli gereksinimler geçti | True | 0/1 | ✘ karşılanmadı |
| Açık bloke eden soru ≤ | 0 | 1 | ✘ karşılanmadı |
| Otomasyonla koşulan ≥ | 80 | 100.0 | ✔ karşılandı |

## Gereksinimler (sonuca göre)

| Sonuç | # |
|---|---|
| failed | 8 |
| in-progress | 2 |
| passed | 9 |

## Kalan riskler (geçmeyenler, en yüksek risk önce)

| REQ | Risk seviyesi | Sonuç | Neden | Hatalar |
|---|---|---|---|---|
| REQ-003 Günlük FAST limiti 100.000,00 TL (kümülatif) | critical (20) | failed | kalan testler: TC-006, TC-008 | DEF-001 |
| REQ-011 60 saniye içinde aynı alıcıya aynı tutarda tekrar uyarısı | high (16) | in-progress | kısmen koşuldu (koşulmayan: TC-046) | - |
| REQ-005 10.000,00 TL ve üzeri transferlerde SMS OTP | high (15) | failed | kalan testler: TC-003, TC-016 | DEF-002, DEF-003 |
| REQ-017 Mükerrer gönderim (çift tıklama) tek transfer oluşturur | high (15) | in-progress | kısmen koşuldu (koşulmayan: TC-046) | - |
| REQ-002 İşlem başına azami tutar 50.000,00 TL | high (12) | failed | kalan testler: TC-003 | DEF-002 |
| REQ-004 Alıcı IBAN doğrulaması (TR, 26 karakter, mod-97) | high (12) | failed | kalan testler: TC-010 | DEF-004 |
| REQ-006 5.000,00 TL'yi aşan transferlerde 5,00 TL işlem ücreti | high (12) | failed | kalan testler: TC-020 | DEF-005 |
| REQ-019 Tutar biçimi ve geçersiz tutar girişi | high (12) | failed | kalan testler: TC-045, TC-047 | DEF-007 |
| REQ-015 Kayıtlı alıcıya transfer | medium (9) | failed | kalan testler: TC-038 | DEF-006 |
| REQ-007 İşlem ücreti dekontta gösterilir | medium (6) | failed | kalan testler: TC-020 | DEF-005 |

---

## Değerlendirme (test analisti)

### Özet
US-310 için 19 gereksinimden (4'ü türetilmiş) 47 test tasarlandı; 46'sı Playwright ile otomatikleştirilip test ortamında Chromium'da koşuldu (37 geçti, 9 başarısız), 1 keşif turu (TC-046) koşulmadı. Plandan sapmalar: yük testi yapılmadı (hedef tanımsız, Q-008), günlük sıfırlama test edilemedi (ortam her oturumda sıfırlıyor), AK-6 testlerinin ön koşulu bakiye seed'i yerine DEF-001 sayesinde hazırlanabildi. En önemli bulgular: günlük limit hiç uygulanmıyor (DEF-001, kritik) ve üç eşikte (5.000 / 10.000 / 50.000 TL) sınır hatası var; tutar ayrıştırma '15.000'ü 15,00 TL olarak gönderiyor.

### Risk alanına göre kalite
- **Yüksek güven:** alt sınır (1,00 TL), IBAN uzunluk/ülke kontrolü, açıklama kuralları, bakiye kontrolü (tutar + ücret, TC-022…024 — ön koşul notuyla), mükerrer uyarısı (60 sn sınırı saat kontrolüyle 59/60 sn doğrulandı), hatalı OTP, OTP adımında tutar değişimi, çift tıklama, 7/24.
- **Düşük güven:** günlük limit (DEF-001), OTP eşiği (DEF-003), ücret eşiği (DEF-005), işlem üst sınırı (DEF-002), IBAN kontrol basamağı (DEF-004), tutar biçimi (DEF-007).
- **Değerlendirilmedi:** performans yük altında, günlük sıfırlama, döviz hesapları (AK-10), kayıtlı alıcı (arayüz yok), güvenlik (ASVS) ve erişilebilirlik (WCAG) — kapsam dışı bırakıldı.

### İş diliyle kalan riskler
- **REQ-003 / DEF-001 (kritik):** Müşteri günlük 100.000 TL limitini sınırsız aşabiliyor; mevzuat ve dolandırıcılık riski. DEF-003 ile birleştiğinde ele geçirilmiş bir oturumdan 10.000,00 TL'lik OTP'siz işlemlerle hesap boşaltılabilir.
- **REQ-006 / DEF-005 (yüksek):** Tam 5.000,00 TL gönderen her müşteriden haksız 5,00 TL ücret alınıyor; şikâyet ve iade yükü.
- **REQ-019 / DEF-007 (yüksek):** '15.000' yazan müşteri 15,00 TL gönderiyor; ödeme yapılmamış sanılan borçlar, müşteri şikâyeti.
- **REQ-004 / DEF-004 (yüksek):** Kontrol basamağı hatalı IBAN'a gönderim başarılı görünüyor; FAST ağında red ve iade süreci gerekir.
- **REQ-005 / DEF-003 (yüksek):** Tam 10.000,00 TL'de SCA yok.
- **REQ-002 / DEF-002 (orta):** 50.000,00 TL gönderilemiyor; iki işlemle geçici çözüm var.
- **REQ-015 / DEF-006 (orta):** Kayıtlı alıcı özelliği yok (kapsam sorusu Q-009).

### Öneri (seçenekler — karar paydaşlarda)
1. **Yayını durdur, düzeltmeleri bekle (önerilen):** DEF-001, DEF-003, DEF-004, DEF-005, DEF-007 düzeltilip ilgili testler ve sınır komşuları (`build_rtm.py --changed REQ-003,REQ-005,REQ-004,REQ-006,REQ-019`) yeniden koşulduktan sonra karar ver. DEF-001 düzeltildiğinde TC-022…024 için bakiye seed'i (B-1) hazır olmalı.
2. **Kısmi yayın kabul edilemez:** DEF-001 kritik ve para/mevzuat etkili; geçici çözümü yok. Kabul edilecekse risk sahibi (Ürün + Uyum/Risk) yazılı onay vermeli.
3. DEF-002 ve DEF-006 PO kararıyla sonraki sürüme ertelenebilir (DEF-006 Q-009 cevabına bağlı).
Ayrıca Q-001 (döviz hesapları) bloke eden soru olarak açık; kapsam dışı kararının PO tarafından yazılı onaylanması gerekiyor.

### Çıkarılan dersler
- Eşik ifadeleri ("ve üzeri", "aşan", "en fazla") hikâyede doğru yazılmış ama üçü de ters kodlanmış: kabul kriterlerine sınır değer örnekleri (5.000,00 → 0 TL ücret) eklenmeli ve birim testlerde zorunlu tutulmalı.
- Test verisi: bakiye > günlük limit olduğundan AK-6 limit içinde test edilemiyor; test müşterisi için bakiye ayarı/seed API planlama aşamasında istenmeli.
- Tutar biçimi gibi yerel ayar riskleri hikâyede yoktu; hata tahmini ile bulundu — fintech hikâyelerinde tutar biçimi kabul kriteri standart hale getirilmeli.
