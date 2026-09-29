# Açık sorular: Demo Bank API 1.2.0 sözleşme boşlukları

Kaynak: `api/openapi.json` (1.2.0) incelemesi ve siyah kutu koşumu (2026-09-30). Sözleşme eksikleri gerçek hatalardır, çünkü tüketiciler dokümana göre entegre olur. "Gözlenen" sütunu, API'nin şu an ne yaptığını gösterir; bu davranış doğru kabul edilmemelidir.

| ID | Konu | Soru | Gözlenen davranış | Etki / bağlı | Engelleyici mi? |
|---|---|---|---|---|---|
| Q-001 | GET /transfers/{transferId} yetkilendirme | Başka müşterinin transferi için 403 mü, 404 mü dönülmeli? Operasyonda 403 dokümante değil. | 404 `NOT_FOUND` (TC-029). Veri sızmıyor. | REQ-021 | Hayır |
| Q-002 | POST /transfers yetersiz bakiye | Hangi durum kodu ve hata kodu? (400 / 409 / 422) Yanıt dokümante değil. | 400 `{"code":"INSUFFICIENT_FUNDS"}` (TC-033) | REQ-023 | Hayır |
| Q-003 | POST /transfers bilinmeyen fromAccountId | 400, 403 ya da 404 mü? Dokümante değil. | 400 `{"code":"VALIDATION","message":"Unknown source account"}` (TC-037) | REQ-023 | Hayır |
| Q-004 | Para birimi kuralı | `currency`, kaynak hesabın para birimiyle aynı olmak zorunda mı, yoksa kur çevrimi mi yapılır? Kur, kaynak ve tarih nerede tanımlı? | EUR hesaptan (A-101) 1 TRY transfer kabul edildi. Hesaptan 1,00 EUR düştü, kur çevrimi yapılmadı (TC-035, DEF-007). | REQ-023 | **Evet, bloke eden** (DEF-007'nin sınıfını belirler) |
| Q-005 | Tutar hassasiyeti | `amount` için `multipleOf: 0.01` gibi bir kısıt var mı? 2'den fazla ondalık kabul edilecek mi, yuvarlama kuralı ne? | `amount: 1.005` kabul edildi. Transfer kaydı 1.005 gösteriyor, liste bakiyesi 2 haneli (49571.79 → 49570.79). Gerçek düşülen tutar görünmüyor. | REQ-020 | Hayır |
| Q-006 | Idempotency | Para transferi için `Idempotency-Key` (veya benzeri) mükerrer istek koruması var mı? İstemci zaman aşımında yeniden denerse ne olur? | Dokümante değil. Her POST yeni transfer oluşturuyor. | REQ-023 | Hayır |
| Q-007 | Hata modeli | 400 dışındaki hatalar (401, 403, 404, 500) için yanıt gövdesi tanımlı değil. `code` değerleri numaralandırılmamış. | Tüm hatalar `{code,message}` dönüyor. Gözlenen kodlar: UNAUTHORIZED, FORBIDDEN, NOT_FOUND, VALIDATION, INSUFFICIENT_FUNDS, BAD_JSON, INTERNAL | REQ-024 | Hayır |
| Q-008 | Account.balance tipi ve hassasiyeti | `number` olarak tanımlı. Parasal değer için ondalık string mi, sayı mı isteniyor? Kaç hane? | Liste sayı döndürüyor, tekil kayıt string döndürüyor (DEF-006). | REQ-020 | Hayır |
| Q-009 | Kısıtsız alanlar | `Account.iban` desen içermiyor, `id`/`fromAccountId` formatı yok, `description` için karakter seti ve boş string kuralı yok. | `description` gönderilmezse yanıtta `""` dönüyor. | REQ-020 | Hayır |
| Q-010 | Tutar üst sınırı anlamı | 50000 işlem başına mı, günlük mü, para birimine göre mi (50000 EUR ≠ 50000 TRY)? | Üst sınır hiç uygulanmıyor (DEF-003). | REQ-020 | Hayır |
| Q-011 | Bilinmeyen / salt okunur alanlar | `TransferRequest` için `additionalProperties: false` tanımlı değil. Bilinmeyen alanlar reddedilmeli mi, yok sayılmalı mı? | `id` ve `status` yok sayıldı, doğru (TC-039). | REQ-021 | Hayır |
| Q-012 | Örnekler | Yanıt örnekleri yok. İstek örneğindeki `A-100` ve yol örneği `T-1` ortamda garanti değil (başlangıçta T-1 yoktu). | – | REQ-020 | Hayır |
| Q-013 | Transfer durumları | `PENDING` ve `REJECTED` ne zaman oluşur? Reddedilen transfer 201 + REJECTED mi, yoksa 4xx mi döner? | Tüm başarılı transferler senkron `COMPLETED` | REQ-023 | Hayır |
| Q-014 | Kendine transfer ve alıcı IBAN | Kaynak hesabın kendi IBAN'ına transfer serbest mi? Alıcı IBAN'ın mod-97 kontrol basamağı doğrulanıyor mu? | Yalnızca desen kontrolü var, kontrol basamağı test edilmedi | REQ-023 | Hayır |
| Q-015 | Önbellek ve güvenlik başlıkları | Hesap ve bakiye yanıtları için `Cache-Control: no-store` gerekli mi? | Yanıtlarda Cache-Control başlığı yok | REQ-021 | Hayır |
| Q-016 | Authorization başlığı toleransı | Şema adında büyük/küçük harf (`bearer`, RFC 7235'e göre serbest) ve çoklu boşluk kabul edilmeli mi? | `bearer x` ve `Bearer  x` kabul ediliyor. Şemasız token da kabul ediliyor (DEF-002). | REQ-022 | Hayır |
| Q-017 | servers URL | `servers[0].url = http://localhost:4180`. Windows'ta `localhost` `::1`'e çözülebilir. Test ortamı URL'si dokümana eklenmeli. | Testler `http://127.0.0.1:4180` ile koşuldu | – | Hayır |
