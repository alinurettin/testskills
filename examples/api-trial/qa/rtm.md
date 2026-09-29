# Gereksinim İzlenebilirlik Matrisi: Demo Bank API 1.2.0 – Hesaplar ve Transferler

## Özet

- Kapsamdaki gereksinimler: 5 / 5 (hariç: ertelenen/kullanımdan kalkan)
- En az 1 aktif testle kapsanan: 5 / 5 (**100.0%**)
- Negatif testi olan fonksiyonel gereksinim: 5 / 5
- Aktif testler: 42 (+0 kullanımdan kalkmış) · positive: 9, negative: 33
- Önceliğe göre testler: critical: 3 (7%), high: 14 (33%), medium: 25 (60%), low: 0 (0%)
- Tekniğe göre testler: error-guessing: 17, equivalence-partitioning: 13, boundary-value-analysis: 7, requirements-based: 5
- Koşum: passed: 31, failed: 11
- Sahipsiz testler: 0 · kopya grupları: 0 · Bağlı hatalar: 7

## Doğrulama

Sorun bulunmadı.

## Kapsam boşlukları (en yüksek risk önce)

| Gereksinim | Risk | Gap | |
|---|---|---|---|
| REQ-021 | high (16) | FAILED | bağlı test başarısız |
| REQ-023 | high (16) | FAILED | bağlı test başarısız |
| REQ-023 | high (16) | OPEN_QUESTIONS | varsayımlarla test ediliyor (açık sorular) |
| REQ-023 | high (16) | UNCONFIRMED | türetilmiş gereksinim henüz onaylanmadı |
| REQ-020 | high (12) | FAILED | bağlı test başarısız |
| REQ-022 | high (12) | FAILED | bağlı test başarısız |
| REQ-024 | medium (6) | OPEN_QUESTIONS | varsayımlarla test ediliyor (açık sorular) |
| REQ-024 | medium (6) | UNCONFIRMED | türetilmiş gereksinim henüz onaylanmadı |

## Kalibrasyon (gözden geçirin)

- ⚠ REDUNDANT: 4 test (TC-001, TC-004, TC-008, TC-026) aynı gereksinim, polarite, teknik (requirements-based) ve sonuç kalıbını paylaşıyor: büyük olasılıkla aynı denklik sınıfı. Bir temsilci ve sınır değerlerini bırakın.
- ⚠ REDUNDANT: 6 test (TC-002, TC-003, TC-005, TC-009, TC-027, TC-032) aynı gereksinim, polarite, teknik (error-guessing) ve sonuç kalıbını paylaşıyor: büyük olasılıkla aynı denklik sınıfı. Bir temsilci ve sınır değerlerini bırakın.
- ⚠ REDUNDANT: 10 test (TC-010, TC-011, TC-012, TC-013, TC-014, TC-015, TC-020, TC-021, TC-022, TC-025) aynı gereksinim, polarite, teknik (equivalence-partitioning) ve sonuç kalıbını paylaşıyor: büyük olasılıkla aynı denklik sınıfı. Bir temsilci ve sınır değerlerini bırakın.

## Gereksinim → Test

| Gereksinim | Kaynak | Başlık | Öncelik | Risk | Durum | Testler | Poz | Neg | Teknikler | Koşum | Hatalar |
|---|---|---|---|---|---|---|---|---|---|---|---|
| REQ-020 | api/openapi.json | Demo Bank API sözleşmesi (OpenAPI 1.2.0) | high | high | ready | TC-001, TC-004, TC-006, TC-008, TC-010, TC-011, TC-012, TC-013, TC-014, TC-015, TC-016, TC-017, TC-018, TC-019, TC-020, TC-021, TC-022, TC-023, TC-024, TC-025, TC-026, TC-028, TC-036, TC-038, TC-040 | 7 | 18 | boundary-value-analysis, equivalence-partitioning, error-guessing, requirements-based | failed | DEF-003, DEF-004, DEF-005, DEF-006 |
| REQ-021 | api/openapi.json summary "caller's accounts", 403 yanıtları | Nesne düzeyinde yetkilendirme (müşteri yalnızca kendi verisine erişir) | critical | high | ready | TC-007, TC-029, TC-030, TC-031, TC-039 | 1 | 4 | error-guessing | failed | DEF-001 |
| REQ-022 | api/openapi.json securitySchemes.bearerAuth | Bearer token ile kimlik doğrulama | critical | high | ready | TC-002, TC-003, TC-005, TC-009, TC-027, TC-032 | 0 | 6 | error-guessing | failed | DEF-002 |
| REQ-023 * | türetilmiş (bankacılık alanı) – sözleşmede yok | Transfer iş kuralları (bakiye, para birimi, yan etki) | critical | high | clarification-needed | TC-033, TC-034, TC-035, TC-037 | 1 | 3 | boundary-value-analysis, error-guessing, requirements-based | failed | DEF-007 |
| REQ-024 * | api/openapi.json components.schemas.Error | Hata modeli | medium | medium | clarification-needed | TC-041, TC-042 | 0 | 2 | error-guessing | passed |  |

\* türetilmiş

## Test → Gereksinim

| Test | Başlık | Gereksinim | Öncelik | ± | Teknikler | Koşum |
|---|---|---|---|---|---|---|
| TC-001 | GET /accounts geçerli istekle 200 döner ve yanıt şemaya uyar | REQ-020 | high | + | requirements-based | passed |
| TC-002 | GET /accounts kimlik bilgisi olmadan 401 döner | REQ-022 | high | − | error-guessing | passed |
| TC-003 | GET /accounts 'Bearer' şeması olmayan Authorization başlığını 401 ile reddeder | REQ-022 | medium | − | error-guessing | failed |
| TC-004 | GET /accounts/{accountId} geçerli istekle 200 döner ve yanıt şemaya uyar | REQ-020 | high | + | requirements-based | failed |
| TC-005 | GET /accounts/{accountId} kimlik bilgisi olmadan 401 döner | REQ-022 | high | − | error-guessing | passed |
| TC-006 | GET /accounts/{accountId} olmayan kaynak için 404 döner | REQ-020 | medium | − | error-guessing | passed |
| TC-007 | GET /accounts/{accountId} başka kullanıcının kaynağına erişimi reddeder (BOLA) | REQ-021 | high | − | error-guessing | failed |
| TC-008 | POST /transfers geçerli istekle 201 döner ve yanıt şemaya uyar | REQ-020 | high | + | requirements-based | failed |
| TC-009 | POST /transfers kimlik bilgisi olmadan 401 döner | REQ-022 | high | − | error-guessing | passed |
| TC-010 | POST /transfers zorunlu 'fromAccountId' eksikken 400 döner | REQ-020 | medium | − | equivalence-partitioning | passed |
| TC-011 | POST /transfers zorunlu 'toIban' eksikken 400 döner | REQ-020 | medium | − | equivalence-partitioning | failed |
| TC-012 | POST /transfers zorunlu 'amount' eksikken 400 döner | REQ-020 | medium | − | equivalence-partitioning | passed |
| TC-013 | POST /transfers zorunlu 'currency' eksikken 400 döner | REQ-020 | medium | − | equivalence-partitioning | passed |
| TC-014 | POST /transfers 'fromAccountId' yanlış tipte (12345) reddedilir | REQ-020 | medium | − | equivalence-partitioning | passed |
| TC-015 | POST /transfers 'toIban' yanlış tipte (12345) reddedilir | REQ-020 | medium | − | equivalence-partitioning | failed |
| TC-016 | POST /transfers 'amount' = 1 (sınır, geçerli) kabul edilir | REQ-020 | medium | + | boundary-value-analysis | failed |
| TC-017 | POST /transfers 'amount' = 0.99 (alt sınırın altı) reddedilir | REQ-020 | medium | − | boundary-value-analysis | passed |
| TC-018 | POST /transfers 'amount' = 50000 (sınır, geçerli) kabul edilir | REQ-020 | medium | + | boundary-value-analysis | failed |
| TC-019 | POST /transfers 'amount' = 50000.01 (üst sınırın üstü) reddedilir | REQ-020 | medium | − | boundary-value-analysis | failed |
| TC-020 | POST /transfers 'amount' yanlış tipte ("abc") reddedilir | REQ-020 | medium | − | equivalence-partitioning | passed |
| TC-021 | POST /transfers 'currency' geçersiz enum değeriyle reddedilir | REQ-020 | medium | − | equivalence-partitioning | passed |
| TC-022 | POST /transfers 'currency' yanlış tipte (12345) reddedilir | REQ-020 | medium | − | equivalence-partitioning | passed |
| TC-023 | POST /transfers 'description' = "aaaaaaaaa…(140 chars)" (sınır, geçerli) kabul edilir | REQ-020 | medium | + | boundary-value-analysis | failed |
| TC-024 | POST /transfers 'description' = "aaaaaaaaa…(141 chars)" (en uzun uzunluğun üstü) reddedilir | REQ-020 | medium | − | boundary-value-analysis | passed |
| TC-025 | POST /transfers 'description' yanlış tipte (12345) reddedilir | REQ-020 | medium | − | equivalence-partitioning | passed |
| TC-026 | GET /transfers/{transferId} geçerli istekle 200 döner ve yanıt şemaya uyar | REQ-020 | high | + | requirements-based | passed |
| TC-027 | GET /transfers/{transferId} kimlik bilgisi olmadan 401 döner | REQ-022 | high | − | error-guessing | passed |
| TC-028 | GET /transfers/{transferId} olmayan kaynak için 404 döner | REQ-020 | medium | − | error-guessing | passed |
| TC-029 | GET /transfers/{transferId} başka kullanıcının kaynağına erişimi reddeder (BOLA) | REQ-021 | high | − | error-guessing | passed |
| TC-030 | Başka müşterinin hesabından (fromAccountId) transfer 403 ile reddedilir | REQ-021 | critical | − | error-guessing | passed |
| TC-031 | GET /accounts yalnızca çağıranın hesaplarını döner | REQ-021 | high | + | error-guessing | passed |
| TC-032 | Değiştirilmiş (tampered) token 401 ile reddedilir | REQ-022 | high | − | error-guessing | passed |
| TC-033 | Bakiyeyi aşan transfer reddedilir ve bakiye değişmez | REQ-023 | critical | − | boundary-value-analysis | passed |
| TC-034 | Başarılı transfer kaynak bakiyeyi tam tutar kadar düşürür | REQ-023 | critical | + | requirements-based | passed |
| TC-035 | Hesap para birimiyle uyuşmayan currency reddedilir (EUR hesap, TRY transfer) | REQ-023 | high | − | error-guessing | failed |
| TC-036 | toIban deseni (^TR[0-9]{24}$) dışındaki IBAN 400 ile reddedilir | REQ-020 | medium | − | equivalence-partitioning | passed |
| TC-037 | Var olmayan fromAccountId ile transfer 4xx döner | REQ-023 | medium | − | error-guessing | passed |
| TC-038 | Negatif tutar reddedilir | REQ-020 | medium | − | equivalence-partitioning | passed |
| TC-039 | Salt okunur alanlar (id, status) istemciden atanamaz (mass assignment) | REQ-021 | high | − | error-guessing | passed |
| TC-040 | Tutar sayısal string ("100") olarak gönderilince reddedilir | REQ-020 | medium | − | equivalence-partitioning | passed |
| TC-041 | Doğrulama hatası Error şemasında ({code, message}) döner | REQ-024 | medium | − | error-guessing | passed |
| TC-042 | Bozuk JSON gövdesi 400 döner (500 değil) | REQ-024 | medium | − | error-guessing | passed |
