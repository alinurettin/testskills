# Gereksinim İzlenebilirlik Matrisi: Demo Bank – FAST ile para transferi (US-310)

## Özet

- Kapsamdaki gereksinimler: 19 / 19 (hariç: ertelenen/kullanımdan kalkan)
- En az 1 aktif testle kapsanan: 19 / 19 (**100.0%**)
- Negatif testi olan fonksiyonel gereksinim: 15 / 18
- Aktif testler: 47 (+0 kullanımdan kalkmış) · positive: 19, negative: 28
- Önceliğe göre testler: critical: 1 (2%), high: 16 (34%), medium: 23 (49%), low: 7 (15%)
- Tekniğe göre testler: boundary-value-analysis: 20, equivalence-partitioning: 11, error-guessing: 6, decision-table: 4, state-transition: 3, checklist: 1, use-case: 1, exploratory: 1
- Koşum: passed: 37, failed: 9, not-run: 1
- Sahipsiz testler: 0 · kopya grupları: 0 · Bağlı hatalar: 7

## Doğrulama

Sorun bulunmadı.

## Kapsam boşlukları (en yüksek risk önce)

| Gereksinim | Risk | Gap | |
|---|---|---|---|
| REQ-003 | critical (20) | FAILED | bağlı test başarısız |
| REQ-003 | critical (20) | OPEN_QUESTIONS | varsayımlarla test ediliyor (açık sorular) |
| REQ-011 | high (16) | OPEN_QUESTIONS | varsayımlarla test ediliyor (açık sorular) |
| REQ-005 | high (15) | FAILED | bağlı test başarısız |
| REQ-005 | high (15) | OPEN_QUESTIONS | varsayımlarla test ediliyor (açık sorular) |
| REQ-008 | high (15) | OPEN_QUESTIONS | varsayımlarla test ediliyor (açık sorular) |
| REQ-016 | high (15) | OPEN_QUESTIONS | varsayımlarla test ediliyor (açık sorular) |
| REQ-016 | high (15) | UNCONFIRMED | türetilmiş gereksinim henüz onaylanmadı |
| REQ-017 | high (15) | UNCONFIRMED | türetilmiş gereksinim henüz onaylanmadı |
| REQ-018 | high (15) | OPEN_QUESTIONS | varsayımlarla test ediliyor (açık sorular) |
| REQ-018 | high (15) | UNCONFIRMED | türetilmiş gereksinim henüz onaylanmadı |
| REQ-002 | high (12) | FAILED | bağlı test başarısız |
| REQ-004 | high (12) | FAILED | bağlı test başarısız |
| REQ-004 | high (12) | OPEN_QUESTIONS | varsayımlarla test ediliyor (açık sorular) |
| REQ-006 | high (12) | FAILED | bağlı test başarısız |
| REQ-006 | high (12) | OPEN_QUESTIONS | varsayımlarla test ediliyor (açık sorular) |
| REQ-019 | high (12) | FAILED | bağlı test başarısız |
| REQ-019 | high (12) | OPEN_QUESTIONS | varsayımlarla test ediliyor (açık sorular) |
| REQ-019 | high (12) | UNCONFIRMED | türetilmiş gereksinim henüz onaylanmadı |
| REQ-013 | medium (9) | OPEN_QUESTIONS | varsayımlarla test ediliyor (açık sorular) |
| REQ-015 | medium (9) | FAILED | bağlı test başarısız |
| REQ-015 | medium (9) | NO_NEGATIVE | fonksiyonel kural için negatif test yok |
| REQ-015 | medium (9) | OPEN_QUESTIONS | varsayımlarla test ediliyor (açık sorular) |
| REQ-007 | medium (6) | FAILED | bağlı test başarısız |
| REQ-007 | medium (6) | NO_NEGATIVE | fonksiyonel kural için negatif test yok |
| REQ-012 | medium (6) | OPEN_QUESTIONS | varsayımlarla test ediliyor (açık sorular) |
| REQ-014 | medium (6) | NO_NEGATIVE | fonksiyonel kural için negatif test yok |
| REQ-009 | low (4) | OPEN_QUESTIONS | varsayımlarla test ediliyor (açık sorular) |
| REQ-010 | low (4) | OPEN_QUESTIONS | varsayımlarla test ediliyor (açık sorular) |

## Gereksinim → Test

| Gereksinim | Kaynak | Başlık | Öncelik | Risk | Durum | Testler | Poz | Neg | Teknikler | Koşum | Hatalar |
|---|---|---|---|---|---|---|---|---|---|---|---|
| REQ-001 (BANK-310) | US-310 AK-1 | İşlem başına asgari tutar 1,00 TL | medium | medium | ready | TC-001, TC-002, TC-043 | 1 | 2 | boundary-value-analysis, equivalence-partitioning | passed |  |
| REQ-002 (BANK-310) | US-310 AK-1 | İşlem başına azami tutar 50.000,00 TL | high | high | ready | TC-003, TC-004 | 1 | 1 | boundary-value-analysis | failed | DEF-002 |
| REQ-003 (BANK-310) | US-310 AK-2 | Günlük FAST limiti 100.000,00 TL (kümülatif) | critical | critical | clarification-needed | TC-005, TC-006, TC-007, TC-008, TC-009, TC-046 | 2 | 4 | boundary-value-analysis, equivalence-partitioning, error-guessing, exploratory | failed | DEF-001 |
| REQ-004 (BANK-310) | US-310 AK-3 | Alıcı IBAN doğrulaması (TR, 26 karakter, mod-97) | high | high | clarification-needed | TC-010, TC-011, TC-012, TC-013, TC-014, TC-015 | 1 | 5 | boundary-value-analysis, equivalence-partitioning | failed | DEF-004 |
| REQ-005 (BANK-310) | US-310 AK-4 | 10.000,00 TL ve üzeri transferlerde SMS OTP | high | high | clarification-needed | TC-003, TC-016, TC-017, TC-018, TC-019, TC-024, TC-035 | 4 | 3 | boundary-value-analysis, decision-table, state-transition | failed | DEF-002, DEF-003 |
| REQ-006 (BANK-310) | US-310 AK-5 | 5.000,00 TL'yi aşan transferlerde 5,00 TL işlem ücreti | high | high | clarification-needed | TC-017, TC-018, TC-020, TC-021 | 3 | 1 | boundary-value-analysis, decision-table | failed | DEF-005 |
| REQ-007 (BANK-310) | US-310 AK-5 | İşlem ücreti dekontta gösterilir | medium | medium | ready | TC-020, TC-021 | 2 | 0 | boundary-value-analysis | failed | DEF-005 |
| REQ-008 (BANK-310) | US-310 AK-6 | Yetersiz bakiyede (tutar + ücret) transfer yapılmaz | high | high | clarification-needed | TC-022, TC-023, TC-024 | 1 | 2 | boundary-value-analysis, decision-table | passed |  |
| REQ-009 (BANK-310) | US-310 AK-7 | Açıklama alanı zorunludur | low | low | clarification-needed | TC-025, TC-026 | 0 | 2 | boundary-value-analysis, equivalence-partitioning | passed |  |
| REQ-010 (BANK-310) | US-310 AK-7 | Açıklama en fazla 50 karakter | low | low | clarification-needed | TC-027, TC-028 | 1 | 1 | boundary-value-analysis | passed |  |
| REQ-011 (BANK-310) | US-310 AK-8 | 60 saniye içinde aynı alıcıya aynı tutarda tekrar uyarısı | high | high | clarification-needed | TC-029, TC-030, TC-031, TC-032, TC-033, TC-034, TC-035, TC-046 | 4 | 4 | boundary-value-analysis, decision-table, error-guessing, exploratory, state-transition | in-progress |  |
| REQ-012 (BANK-310) | US-310 AK-9 | Sonuç ekranında dekont gösterilir | medium | medium | clarification-needed | TC-001, TC-002, TC-027, TC-036 | 3 | 1 | boundary-value-analysis, checklist | passed |  |
| REQ-013 (BANK-310) | US-310 AK-9 | Transfer hızlı gerçekleşmeli (performans) | medium | medium | clarification-needed | TC-036 | 1 | 0 | checklist | passed |  |
| REQ-014 (BANK-310) | US-310 Notlar | 7/24 çalışma (mesai dışı) | medium | medium | ready | TC-037 | 1 | 0 | equivalence-partitioning | passed |  |
| REQ-015 (BANK-310) | US-310 Hikâye | Kayıtlı alıcıya transfer | medium | medium | clarification-needed | TC-038 | 1 | 0 | use-case | failed | DEF-006 |
| REQ-016 (BANK-310) * | US-310 AK-2, AK-5, AK-6 | Başarılı transfer bakiyeden tutar+ücreti, limitten tutarı düşer | high | high | clarification-needed | TC-009, TC-021 | 1 | 1 | boundary-value-analysis, error-guessing | passed |  |
| REQ-017 (BANK-310) * | Fintech örtük gereksinim (idempotency) | Mükerrer gönderim (çift tıklama) tek transfer oluşturur | high | high | clarification-needed | TC-039, TC-046 | 0 | 2 | error-guessing, exploratory | in-progress |  |
| REQ-018 (BANK-310) * | US-310 AK-4 (örtük) | Hatalı OTP ile transfer yapılmaz | high | high | clarification-needed | TC-018, TC-019 | 0 | 2 | decision-table, state-transition | passed |  |
| REQ-019 (BANK-310) * | Fintech örtük gereksinim (para/yerel ayar) | Tutar biçimi ve geçersiz tutar girişi | high | high | clarification-needed | TC-040, TC-041, TC-042, TC-043, TC-044, TC-045, TC-047 | 1 | 6 | equivalence-partitioning, error-guessing | failed | DEF-007 |

\* türetilmiş

## Test → Gereksinim

| Test | Başlık | Gereksinim | Öncelik | ± | Teknikler | Koşum |
|---|---|---|---|---|---|---|
| TC-001 | 1,00 TL (alt sınır) transfer ücretsiz gerçekleşir ve dekont gösterilir | REQ-001, REQ-012 | medium | + | boundary-value-analysis | passed |
| TC-002 | 0,99 TL (alt sınırın altı) reddedilir | REQ-001, REQ-012 | medium | − | boundary-value-analysis | passed |
| TC-003 | 50.000,00 TL (işlem üst sınırı) SMS doğrulama ile gerçekleşir | REQ-002, REQ-005 | high | + | boundary-value-analysis | failed |
| TC-004 | 50.000,01 TL (işlem üst sınırının üstü) reddedilir | REQ-002 | high | − | boundary-value-analysis | passed |
| TC-005 | Günlük toplam tam 100.000,00 TL'ye ulaşan transfer kabul edilir | REQ-003 | high | + | boundary-value-analysis | passed |
| TC-006 | Günlük toplamı 100.000,01 TL'ye çıkaracak transfer reddedilir | REQ-003 | critical | − | boundary-value-analysis | failed |
| TC-007 | Günlük toplamı 99.999,99 TL'ye çıkaran transfer kabul edilir | REQ-003 | medium | + | boundary-value-analysis | passed |
| TC-008 | Günlük limit dolduktan sonra 1,00 TL transfer reddedilir | REQ-003 | high | − | equivalence-partitioning | failed |
| TC-009 | Reddedilen transfer bakiyeyi ve günlük limiti tüketmez | REQ-016, REQ-003 | medium | − | error-guessing | passed |
| TC-010 | Kontrol basamağı hatalı (mod-97) IBAN reddedilir | REQ-004 | high | − | equivalence-partitioning | failed |
| TC-011 | 25 karakterlik IBAN reddedilir | REQ-004 | medium | − | boundary-value-analysis | passed |
| TC-012 | 27 karakterlik IBAN reddedilir | REQ-004 | medium | − | boundary-value-analysis | passed |
| TC-013 | TR dışı ülke kodlu IBAN reddedilir | REQ-004 | medium | − | equivalence-partitioning | passed |
| TC-014 | Boş IBAN reddedilir | REQ-004 | low | − | equivalence-partitioning | passed |
| TC-015 | Boşluklu ve küçük harfli geçerli IBAN kabul edilir | REQ-004 | low | + | equivalence-partitioning | passed |
| TC-016 | 10.000,00 TL'de (OTP eşiği, dahil) SMS doğrulama istenir | REQ-005 | high | + | boundary-value-analysis | failed |
| TC-017 | 9.999,99 TL'de OTP istenmez, 5,00 TL ücret alınır | REQ-005, REQ-006 | medium | + | boundary-value-analysis | passed |
| TC-018 | Hatalı SMS kodu ile transfer yapılmaz | REQ-018, REQ-005, REQ-006 | high | − | decision-table | passed |
| TC-019 | SMS adımı açıkken değiştirilen tutar OTP ile onaylanamaz | REQ-018, REQ-005 | high | − | state-transition | passed |
| TC-020 | 5.000,00 TL'de (ücret eşiği) ücret alınmaz | REQ-006, REQ-007 | high | + | boundary-value-analysis | failed |
| TC-021 | 5.000,01 TL'de 5,00 TL ücret alınır; bakiye ve limit doğru düşer | REQ-006, REQ-007, REQ-016 | high | + | boundary-value-analysis | passed |
| TC-022 | Tutar + ücret bakiyeye tam eşitse transfer gerçekleşir | REQ-008 | medium | + | boundary-value-analysis | passed |
| TC-023 | Tutar bakiyeye sığıp tutar + ücret bakiyeyi 0,01 TL aşarsa transfer yapılmaz | REQ-008 | high | − | boundary-value-analysis | passed |
| TC-024 | Tutar bakiyeyi aşarsa SMS gönderilmeden reddedilir | REQ-008, REQ-005 | medium | − | decision-table | passed |
| TC-025 | Boş açıklama ile transfer reddedilir | REQ-009 | low | − | boundary-value-analysis | passed |
| TC-026 | Yalnız boşluktan oluşan açıklama reddedilir | REQ-009 | low | − | equivalence-partitioning | passed |
| TC-027 | Türkçe karakterli 50 karakterlik açıklama kabul edilir ve dekontta tam görünür | REQ-010, REQ-012 | low | + | boundary-value-analysis | passed |
| TC-028 | 51 karakterlik açıklama ile transfer yapılmaz | REQ-010 | low | − | boundary-value-analysis | passed |
| TC-029 | 60 sn içinde aynı IBAN ve tutara ikinci transferde uyarı; 'Vazgeç' transferi durdurur | REQ-011 | high | − | decision-table | passed |
| TC-030 | Tekrar uyarısında 'Yine de gönder' ikinci transferi gerçekleştirir | REQ-011 | medium | + | state-transition | passed |
| TC-031 | Önceki transferden 59 sn sonra aynı IBAN ve tutarda uyarı gösterilir | REQ-011 | medium | − | boundary-value-analysis | passed |
| TC-032 | Önceki transferden 60 sn sonra aynı IBAN ve tutarda uyarı gösterilmez | REQ-011 | medium | + | boundary-value-analysis | passed |
| TC-033 | Aynı IBAN'a farklı tutarda 60 sn içinde transferde uyarı gösterilmez | REQ-011 | medium | + | decision-table | passed |
| TC-034 | Aynı IBAN boşluklu yazılsa da 60 sn içinde uyarı gösterilir | REQ-011 | medium | − | error-guessing | passed |
| TC-035 | Tekrar uyarısı sonrası ≥ 10.000,00 TL transfer yine SMS doğrulaması ister | REQ-011, REQ-005 | medium | + | state-transition | passed |
| TC-036 | Sonuç ekranı ve dekont onaydan sonra 3 sn içinde görünür | REQ-013, REQ-012 | medium | + | checklist | passed |
| TC-037 | Pazar 23:30'da (mesai dışı) transfer gerçekleşir | REQ-014 | medium | + | equivalence-partitioning | passed |
| TC-038 | Kayıtlı alıcı listeden seçilerek transfer yapılır | REQ-015 | medium | + | use-case | failed |
| TC-039 | 'Devam'a çift tıklama tek transfer oluşturur | REQ-017 | high | − | error-guessing | passed |
| TC-040 | '1.000,50' biçimli tutar doğru ayrıştırılır | REQ-019 | high | + | equivalence-partitioning | passed |
| TC-041 | Sayısal olmayan tutar reddedilir | REQ-019 | medium | − | equivalence-partitioning | passed |
| TC-042 | İkiden fazla ondalık basamaklı tutar reddedilir | REQ-019 | medium | − | error-guessing | passed |
| TC-043 | Negatif tutar reddedilir | REQ-001, REQ-019 | medium | − | equivalence-partitioning | passed |
| TC-044 | Boş tutar reddedilir | REQ-019 | low | − | equivalence-partitioning | passed |
| TC-045 | Nokta ondalık ayırıcılı '100.50' tutarı 10.050 TL olarak işlenmez | REQ-019 | high | − | error-guessing | failed |
| TC-047 | Virgülsüz TR binlik biçimli '15.000' tutarı 15,00 TL olarak gönderilmez | REQ-019 | high | − | error-guessing | failed |
| TC-046 | Keşif turu: oturum, yenileme, geri tuşu ve çoklu sekmede FAST transferi | REQ-003, REQ-011, REQ-017 | medium | − | exploratory | not-run |
