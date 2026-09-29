project: Demo Bank API 1.2.0 – Hesaplar ve Transferler
language: tr

## REQ-020 | Demo Bank API sözleşmesi (OpenAPI 1.2.0)
type: interface | pri: h | risk: 3x4 Tüketiciler dokümana göre entegre olur | src: api/openapi.json | status: ready
text: API; GET /accounts, GET /accounts/{accountId}, POST /transfers ve GET /transfers/{transferId} işlemlerinde OpenAPI 1.2.0 dokümanındaki durum kodlarını, istek doğrulamalarını (zorunlu alanlar, tipler, enum, amount 1–50000, description ≤140, toIban ^TR[0-9]{24}$) ve yanıt şemalarını uygulamalıdır.
q: Q-005, Q-007, Q-008, Q-009, Q-012

## REQ-021 | Nesne düzeyinde yetkilendirme (müşteri yalnızca kendi verisine erişir)
type: business-rule | pri: c | risk: 4x4 Başka müşterinin hesap/IBAN/bakiye verisinin sızması | src: api/openapi.json summary "caller's accounts", 403 yanıtları | status: ready
text: Kimliği doğrulanmış müşteri yalnızca kendi hesaplarını ve transferlerini görebilmeli, yalnızca kendi hesabından transfer başlatabilmelidir; başka müşterinin nesnesi 403/404 ile reddedilmeli ve veri dönmemelidir. İstemci salt okunur alanları (id, status) atayamaz.
q: Q-001

## REQ-022 | Bearer token ile kimlik doğrulama
type: functional | pri: c | risk: 3x4 Kimlik doğrulama atlatma | src: api/openapi.json securitySchemes.bearerAuth | status: ready
text: Tüm işlemler 'Authorization: Bearer <token>' gerektirir; token yoksa, geçersizse veya şema hatalıysa 401 dönülür.

## REQ-023 | Transfer iş kuralları (bakiye, para birimi, yan etki)
type: business-rule | pri: c | risk: 4x4 Hatalı para hareketi | src: türetilmiş (bankacılık alanı) – sözleşmede yok | status: clarification-needed
text: Transfer, kaynak hesabın bakiyesini tam tutar kadar düşürür; bakiyeyi aşan veya hesap para birimiyle uyuşmayan transfer reddedilir; bilinmeyen kaynak hesap reddedilir.
q: Q-002, Q-003, Q-004, Q-006 | derived: yes

## REQ-024 | Hata modeli
type: interface | pri: m | risk: 2x3 Tüketiciler hataları ayrıştıramaz | src: api/openapi.json components.schemas.Error | status: clarification-needed
text: Doğrulama hataları Error şemasında ({code, message}) 400 ile dönülür; hatalı girdi hiçbir zaman 500 üretmez.
q: Q-007 | derived: yes
