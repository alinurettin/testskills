# Gereksinim İzlenebilirlik Matrisi: Demo Mağaza – Şifre sıfırlama (US-128)

## Özet

- Kapsamdaki gereksinimler: 14 / 14 (hariç: ertelenen/kullanımdan kalkan)
- En az 1 aktif testle kapsanan: 13 / 14 (**92.9%**)
- Negatif testi olan fonksiyonel gereksinim: 13 / 13
- Aktif testler: 25 (+0 kullanımdan kalkmış) · positive: 8, negative: 17
- Önceliğe göre testler: critical: 2 (8%), high: 6 (24%), medium: 15 (60%), low: 2 (8%)
- Tekniğe göre testler: error-guessing: 6, boundary-value-analysis: 6, decision-table: 5, state-transition: 4, requirements-based: 2, use-case: 1, equivalence-partitioning: 1
- Koşum: not-run: 25
- Sahipsiz testler: 0 · kopya grupları: 0 · Bağlı hatalar: 0

## Doğrulama

Sorun bulunmadı.

## Kapsam boşlukları (en yüksek risk önce)

| Gereksinim | Risk | Gap | |
|---|---|---|---|
| REQ-003 | high (12) | OPEN_QUESTIONS | varsayımlarla test ediliyor (açık sorular) |
| REQ-010 | high (12) | OPEN_QUESTIONS | varsayımlarla test ediliyor (açık sorular) |
| REQ-005 | medium (9) | OPEN_QUESTIONS | varsayımlarla test ediliyor (açık sorular) |
| REQ-007 | medium (9) | OPEN_QUESTIONS | varsayımlarla test ediliyor (açık sorular) |
| REQ-008 | medium (9) | OPEN_QUESTIONS | varsayımlarla test ediliyor (açık sorular) |
| REQ-014 | medium (9) | OPEN_QUESTIONS | varsayımlarla test ediliyor (açık sorular) |
| REQ-014 | medium (9) | UNCONFIRMED | türetilmiş gereksinim henüz onaylanmadı |
| REQ-013 | medium (8) | OPEN_QUESTIONS | varsayımlarla test ediliyor (açık sorular) |
| REQ-013 | medium (8) | UNCONFIRMED | türetilmiş gereksinim henüz onaylanmadı |
| REQ-009 | medium (6) | OPEN_QUESTIONS | varsayımlarla test ediliyor (açık sorular) |
| REQ-011 | low (4) | OPEN_QUESTIONS | varsayımlarla test ediliyor (açık sorular) |
| REQ-012 | low (4) | OPEN_QUESTIONS | varsayımlarla test ediliyor (açık sorular) |
| REQ-012 | low (4) | UNCOVERED | aktif test yok |

## Kalibrasyon (gözden geçirin)

- ⚠ REDUNDANT: 3 test (TC-016, TC-017, TC-018) aynı gereksinim, polarite, teknik (decision-table) ve sonuç kalıbını paylaşıyor: büyük olasılıkla aynı denklik sınıfı. Bir temsilci ve sınır değerlerini bırakın.

## Gereksinim → Test

| Gereksinim | Kaynak | Başlık | Öncelik | Risk | Durum | Testler | Poz | Neg | Teknikler | Koşum | Hatalar |
|---|---|---|---|---|---|---|---|---|---|---|---|
| REQ-001 (SHOP-128) | US-128 AK-1 | "Şifremi unuttum" ile e-postaya sıfırlama bağlantısı istenir | high | medium | ready | TC-001, TC-002 | 1 | 1 | equivalence-partitioning, use-case | not-run |  |
| REQ-002 (SHOP-128) | US-128 AK-1 | Kayıtlı ve kayıtsız adres için aynı ekran mesajı | high | high | ready | TC-002, TC-004, TC-006 | 0 | 3 | boundary-value-analysis, equivalence-partitioning, error-guessing | not-run |  |
| REQ-003 (SHOP-128) | US-128 AK-2 | Sıfırlama bağlantısı 30 dakika geçerlidir | high | high | clarification-needed | TC-007, TC-008, TC-009 | 1 | 2 | boundary-value-analysis, state-transition | not-run |  |
| REQ-004 (SHOP-128) | US-128 AK-2 | Sıfırlama bağlantısı yalnızca bir kez kullanılabilir | high | high | ready | TC-010, TC-011, TC-013 | 0 | 3 | error-guessing, state-transition | not-run |  |
| REQ-005 (SHOP-128) | US-128 AK-3 | Aynı e-posta için 1 saatte en fazla 3 sıfırlama isteği | medium | medium | clarification-needed | TC-005, TC-006 | 1 | 1 | boundary-value-analysis | not-run |  |
| REQ-006 (SHOP-128) | US-128 AK-4 | Yeni şifre uzunluğu 8–20 karakter | medium | medium | ready | TC-001, TC-007, TC-014, TC-015 | 2 | 2 | boundary-value-analysis, use-case | not-run |  |
| REQ-007 (SHOP-128) | US-128 AK-4 | Yeni şifre büyük harf, küçük harf ve rakam içerir | medium | medium | clarification-needed | TC-001, TC-016, TC-017, TC-018, TC-019 | 2 | 3 | decision-table, error-guessing, use-case | not-run |  |
| REQ-008 (SHOP-128) | US-128 AK-5 | Yeni şifre son 3 şifreden biri olamaz | medium | medium | clarification-needed | TC-001, TC-020, TC-021, TC-022 | 2 | 2 | decision-table, error-guessing, use-case | not-run |  |
| REQ-009 (SHOP-128) | US-128 AK-6 | Şifre değişince bilgilendirme e-postası gönderilir | medium | medium | clarification-needed | TC-014, TC-025 | 1 | 1 | boundary-value-analysis, requirements-based | not-run |  |
| REQ-010 (SHOP-128) | US-128 AK-6 | Şifre değişince açık oturumların tümü kapatılır | high | high | clarification-needed | TC-023, TC-024 | 1 | 1 | error-guessing, requirements-based | not-run |  |
| REQ-011 (SHOP-128) | US-128 AK-6 | Hatalı durumlarda kullanıcıya mesaj gösterilir | low | low | clarification-needed | TC-008, TC-010, TC-014 | 0 | 3 | boundary-value-analysis, state-transition | not-run |  |
| REQ-012 (SHOP-128) | US-128 Notlar | Sayfalar hızlı açılmalı | low | low | clarification-needed | **yok** | 0 | 0 |  | - |  |
| REQ-013 (SHOP-128) * | US-128 AK-2 (türetilmiş) | Yeni istek önceki sıfırlama bağlantılarını geçersiz kılar | medium | medium | clarification-needed | TC-012 | 0 | 1 | state-transition | not-run |  |
| REQ-014 (SHOP-128) * | US-128 AK-1 (türetilmiş) | E-posta adresi büyük/küçük harf ve boşluktan bağımsız eşleştirilir | medium | medium | clarification-needed | TC-003, TC-004 | 1 | 1 | error-guessing | not-run |  |

\* türetilmiş

## Test → Gereksinim

| Test | Başlık | Gereksinim | Öncelik | ± | Teknikler | Koşum |
|---|---|---|---|---|---|---|
| TC-001 | Şifre, e-postadaki bağlantıyla baştan sona sıfırlanır | REQ-001, REQ-006, REQ-007, REQ-008 | critical | + | use-case | not-run |
| TC-002 | Kayıtsız adres için aynı mesaj gösterilir, e-posta gönderilmez | REQ-002, REQ-001 | high | − | equivalence-partitioning | not-run |
| TC-003 | Büyük harfli ve boşluklu adres kayıtlı hesapla eşleşir | REQ-014 | medium | + | error-guessing | not-run |
| TC-004 | Noktasız 'ı' içeren adres kayıtlı hesapla eşleşmez | REQ-014, REQ-002 | high | − | error-guessing | not-run |
| TC-005 | 60 dakika içindeki 3. istek e-posta gönderir | REQ-005 | medium | + | boundary-value-analysis | not-run |
| TC-006 | 60 dakika içindeki 4. istekte e-posta gönderilmez | REQ-005, REQ-002 | medium | − | boundary-value-analysis | not-run |
| TC-007 | 29:59'luk bağlantıyla 20 karakterlik şifre kaydedilir | REQ-003, REQ-006 | medium | + | boundary-value-analysis | not-run |
| TC-008 | 30. dakikada açılan bağlantı reddedilir | REQ-003, REQ-011 | high | − | boundary-value-analysis | not-run |
| TC-009 | Form açıkken süresi dolan bağlantıyla şifre kaydedilmez | REQ-003 | medium | − | state-transition | not-run |
| TC-010 | Kullanılmış bağlantı ikinci kez açılamaz | REQ-004, REQ-011 | critical | − | state-transition | not-run |
| TC-011 | İkinci sekmede açık kalan formdan şifre kaydedilemez | REQ-004 | high | − | error-guessing | not-run |
| TC-012 | Yeni bağlantı istenince eski bağlantı geçersiz olur | REQ-013 | medium | − | state-transition | not-run |
| TC-013 | Değiştirilmiş token'lı bağlantı formu açmaz | REQ-004 | high | − | state-transition | not-run |
| TC-014 | 7 karakterlik şifre reddedilir, bağlantı geçerli kalır | REQ-006, REQ-009, REQ-011 | medium | − | boundary-value-analysis | not-run |
| TC-015 | 21 karakterlik şifre reddedilir | REQ-006 | low | − | boundary-value-analysis | not-run |
| TC-016 | Rakamsız şifre reddedilir | REQ-007 | medium | − | decision-table | not-run |
| TC-017 | Küçük harfsiz şifre reddedilir | REQ-007 | medium | − | decision-table | not-run |
| TC-018 | Büyük harfsiz şifre reddedilir | REQ-007 | medium | − | decision-table | not-run |
| TC-019 | Tek büyük harfi 'Ş' olan şifre kabul edilir | REQ-007 | medium | + | error-guessing | not-run |
| TC-020 | İki önceki şifre yeni şifre olarak reddedilir | REQ-008 | medium | − | decision-table | not-run |
| TC-021 | Mevcut şifre yeni şifre olarak reddedilir | REQ-008 | medium | − | error-guessing | not-run |
| TC-022 | Üç önceki şifre yeniden kullanılabilir | REQ-008 | low | + | decision-table | not-run |
| TC-023 | Şifre sıfırlanınca diğer tarayıcıdaki oturum kapanır | REQ-010 | high | + | requirements-based | not-run |
| TC-024 | Yalnızca sıfırlama istemek açık oturumu kapatmaz | REQ-010 | medium | − | error-guessing | not-run |
| TC-025 | Şifre değişince bilgilendirme e-postası şifre içermeden gelir | REQ-009 | medium | + | requirements-based | not-run |
