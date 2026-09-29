# Test Tamamlama Raporu: Demo Bank API 1.2.0 – Hesaplar ve Transferler

2026-09-30 · Demo Bank API 1.2.0 – run 2 (2026-09-30)

## Özet

qa/exit-criteria.json bulunamadı; kriterler değerlendirilmedi.

- Gereksinim kapsamı: 5/5 (100.0%)
- Koşum: 42/42 (100.0%) · passed 31 · failed 11 · blocked 0 · not run 0
- Geçme oranı: 73.8%
- Otomasyonla koşulan: 42/42 (100.0%)
- Açık bloke eden soru: 1
- Hatalar (açık, defects.json): critical: 1, high: 3, medium: 3, low: 1

## Gereksinimler (sonuca göre)

| Sonuç | # |
|---|---|
| failed | 4 |
| passed | 1 |

## Kalan riskler (geçmeyenler, en yüksek risk önce)

| REQ | Risk seviyesi | Sonuç | Neden | Hatalar |
|---|---|---|---|---|
| REQ-021 Nesne düzeyinde yetkilendirme (müşteri yalnızca kendi verisine erişir) | high (16) | failed | kalan testler: TC-007 | DEF-001 |
| REQ-023 Transfer iş kuralları (bakiye, para birimi, yan etki) | high (16) | failed | kalan testler: TC-035 | DEF-007 |
| REQ-020 Demo Bank API sözleşmesi (OpenAPI 1.2.0) | high (12) | failed | kalan testler: TC-004, TC-008, TC-011, TC-015, TC-016, TC-018, TC-019, TC-023 | DEF-003, DEF-004, DEF-005, DEF-006 |
| REQ-022 Bearer token ile kimlik doğrulama | high (12) | failed | kalan testler: TC-003 | DEF-002 |
