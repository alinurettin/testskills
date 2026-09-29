# Hata raporu: Demo Bank API 1.2.0

**Ortam:** yerel test ortamı `http://127.0.0.1:4180` (bellek içi sentetik veri) · OpenAPI 1.2.0 (`api/openapi.json`) · Playwright 1.63 `request` fixture'ı (tarayıcı yok) · Windows 11
**Test kullanıcıları:** `token-alice` (A-100 TRY, A-101 EUR) ve `token-bob` (B-200 TRY). Kanıtlarda token değerleri `<redacted>` olarak gizlendi.
**Koşum:** 2026-09-30. Run 1 00:53'te 42 testle, run 2 00:54'te 40 testle koşuldu (TC-018 ve TC-019 hariç, gerekçe §Test verisi). Ek tekil `curl` kanıtları 00:55'te alındı.
**Sonuç:** 42 test koşuldu. 31 geçti, 11 başarısız oldu. Bu 11 başarısız test 7 kök nedene dayanıyor. Bunlara ek olarak, başarısız testi olmayan 1 düşük önemli gözlem var.
**Kanıt kaynağı:** `automation/results/pw-report-run2.json`. Her test, gönderilen isteği ve alınan yanıtı `http` annotation'ı olarak taşır. Makine okunur kayıtlar `qa/defects.json` ve `qa/results.json` dosyalarındadır.

## Özet (kök nedene göre)

| ID | Başlık | Önem | Sınıf | Etkilenen TC | REQ |
|---|---|---|---|---|---|
| DEF-001 | GET /accounts/{accountId} başka müşterinin hesabını (IBAN, bakiye) döndürüyor (BOLA) | **critical** | Uygulama hatası | TC-007 | REQ-021 |
| DEF-002 | 'Bearer' şeması olmadan gönderilen token kabul ediliyor | high | Uygulama hatası | TC-003 | REQ-022 |
| DEF-003 | POST /transfers `amount` üst sınırı (50000) uygulanmıyor | high | Uygulama hatası | TC-019 | REQ-020 |
| DEF-007 | EUR hesaptan TRY transfer, kur çevrimi olmadan kabul ediliyor | high (Q-004 yanıtına bağlı) | Sözleşme eksikliği + muhtemel uygulama hatası | TC-035 | REQ-023 |
| DEF-004 | POST /transfers başarıda 201 yerine 200 dönüyor | medium | Uygulama hatası (sözleşme 201 diyor) | TC-008, TC-016, TC-018, TC-023 | REQ-020 |
| DEF-005 | `toIban` eksik ya da string değilse 500 Internal dönüyor | medium | Uygulama hatası | TC-011, TC-015 | REQ-020, REQ-024 |
| DEF-006 | GET /accounts/{accountId} `balance` alanını string döndürüyor | medium | Uygulama hatası | TC-004 | REQ-020 |
| DEF-008 | Bozuk JSON ve yanlış tipte `fromAccountId` için yanıltıcı hata mesajı | low | Uygulama hatası (gözlem) | TC-042 ve TC-014 durum kodu açısından geçti | REQ-024 |

Önem, gereksinim riskine bağlandı: REQ-021, REQ-022 ve REQ-023 kritik risktedir. Öncelik PO tarafından belirlenecek.

---

## DEF-001: GET /accounts/{accountId} başka müşterinin hesabını döndürüyor (BOLA)
- **Bağlantılar:** TC-007 (başarısız), REQ-021 · OWASP API1:2023 BOLA
- **Ön koşul:** alice'in hesabı A-100, bob'un hesabı B-200 (her iki kullanıcının `GET /accounts` yanıtıyla doğrulandı)
- **Adımlar:**
  1. `GET /accounts/A-100`, `Authorization: Bearer <bob token>` ile gönderilir.
  2. Ters yönde: `GET /accounts/B-200`, `Authorization: Bearer <alice token>` ile gönderilir.
- **Beklenen (sözleşme):** `summary: "Get one of the caller's accounts"` · `"403": {"description": "The account belongs to another customer"}`. Beklenen yanıt 403'tür ve veri dönmez.
- **Gerçekleşen:**
  ```
  GET /accounts/A-100 [auth: Bearer <bob>]   -> 200 {"id":"A-100","iban":"TR120006200000000000000100","currency":"TRY","balance":"49774.79"}
  GET /accounts/B-200 [auth: Bearer <alice>] -> 200 {"id":"B-200","iban":"TR120006200000000000000200","currency":"TRY","balance":"1500.00"}
  ```
- **Tekrarlanabilirlik:** Her denemede tekrarlandı (run 1, run 2 ve curl ile 3/3). Hesap kimlikleri tahmin edilebilir (A-100, A-101, B-200).
- **Kapsam notu:** Liste endpoint'i (TC-031), transfer okuma (TC-029, 404) ve başkasının hesabından transfer (TC-030, 403) doğru korunuyor. Açık yalnızca tekil hesap okumada.
- **Önem:** critical. Başka müşterinin IBAN ve bakiye bilgisi sızıyor ve kimlikler sıralı olduğu için tüm müşteriler taranabilir.
- **Şüphe (not):** Yetki kontrolü liste ve transfer işlemlerinde var. `GET /accounts/{id}` yalnızca hesabın varlığını kontrol ediyor olabilir.

## DEF-002: 'Bearer' şeması olmadan gönderilen token kabul ediliyor
- **Bağlantılar:** TC-003 (başarısız), REQ-022
- **Adım:** `GET /accounts`, `Authorization: token-<redacted>` başlığıyla (şema yok) gönderilir.
- **Beklenen (sözleşme):** `securitySchemes.bearerAuth: {type: http, scheme: bearer}` · `401: Missing or invalid token`.
- **Gerçekleşen:** `200 [{"id":"A-100",...,"balance":49774.79},{"id":"A-101",...}]`
- **Sınır değerleri:** `Basic <token>` → 401 (doğru). Tahrifli token → 401 (TC-032, doğru). Token yok → 401 (doğru). `bearer <token>` (küçük harf) → 200; RFC 7235'e göre şema adı büyük/küçük harfe duyarsızdır, bu nedenle kabul edilebilir. `Bearer  <token>` (çift boşluk) → 200 (Q-016).
- **Tekrarlanabilirlik:** 3/3
- **Önem:** high. Bu, isteğe bağlı `Bearer ` önekini silen bir ara katmana işaret eder (şüphe). Token'ın farklı biçimlerde kabul edilmesi, loglama/WAF kurallarının atlatılmasına yol açabilir.

## DEF-003: POST /transfers `amount` üst sınırı (50000) uygulanmıyor
- **Bağlantılar:** TC-019 (başarısız, run 1), REQ-020 · ilgili: Q-010
- **Adım:** `POST /transfers {"fromAccountId":"A-100","toIban":"TR330006100519786457841326","amount":50000.01,"currency":"TRY","description":"Kira"}`
- **Beklenen (sözleşme):** `TransferRequest.amount: {minimum: 1, maximum: 50000}` · `400 Validation error` (Error şeması).
- **Gerçekleşen (run 1, 00:53):** HTTP 200 döndü ve transfer oluşturuldu. A-100'den 50000,01 TRY düşüldü. Bakiye kontrolü 150000 → 49785,89 ile tutarlı.
- **Sınırın iki tarafı:** 50000 kabul edildi (doğru, yalnızca durum kodu 200, bkz. DEF-004). 50000,01 kabul edildi (hatalı).
- **Ek kanıt (curl, 00:55, bakiye ~49572 TRY):** Doğrulama çalışsaydı bu istekler `VALIDATION` dönerdi, ancak hepsi bakiye kontrolüne kadar ilerliyor:
  ```
  amount=50000.02   -> 400 {"code":"INSUFFICIENT_FUNDS","message":"Insufficient balance"}
  amount=100000     -> 400 {"code":"INSUFFICIENT_FUNDS",...}
  amount=1000000000 -> 400 {"code":"INSUFFICIENT_FUNDS",...}
  ```
  Karşılaştırma için alt sınır doğru çalışıyor: `amount=0.99` → `400 {"code":"VALIDATION","message":"amount must be a number >= 1"}` (TC-017).
- **Önem:** high. İşlem başına limit parasal bir kontroldür ve yüksek bakiyeli hesaplarda limitsiz transfer yapılabiliyor.
- **Not:** Bu test run 2'de bilinçli olarak tekrar koşulmadı. Düşük bakiyede `INSUFFICIENT_FUNDS` ile 400 dönerdi ve test **yanlış geçerdi**.

## DEF-004: POST /transfers başarıda 201 yerine 200 dönüyor
- **Bağlantılar:** TC-008, TC-016, TC-018, TC-023 (başarısız), REQ-020. Tek kök neden: her başarılı oluşturma bu yüzden başarısız oluyor.
- **Adım:** `POST /transfers {"fromAccountId":"A-100","toIban":"TR330006100519786457841326","amount":100,"currency":"TRY","description":"Kira"}`
- **Beklenen (sözleşme):** `"201": {"description": "Transfer created", schema: Transfer}`
- **Gerçekleşen:** `200 {"id":"T-14","status":"COMPLETED","amount":100,"currency":"TRY","fromAccountId":"A-100","toIban":"TR330006100519786457841326","description":"Kira"}`. Gövde Transfer şemasına uyuyor, yalnızca durum kodu yanlış.
- **Tekrarlanabilirlik:** Her başarılı POST'ta (15+ istek)
- **Önem:** medium. `201`'e göre dallanan istemciler başarılı transferi hata sanıp yeniden deneyebilir. Idempotency tanımlı olmadığı için (Q-006) bu çift transfer riski taşır.
- **Sınıf:** Uygulama hatası. Ekip 200'ü amaçladıysa sözleşme hatası olarak yeniden sınıflandırılmalı.

## DEF-005: `toIban` eksik ya da string değilse 500 Internal dönüyor
- **Bağlantılar:** TC-011, TC-015 (başarısız), REQ-020, REQ-024
- **Adımlar ve gerçekleşen:**
  ```
  POST /transfers {"fromAccountId":"A-100","amount":100,"currency":"TRY","description":"Kira"}                   -> 500 {"code":"INTERNAL","message":"Internal server error"}
  POST /transfers {"fromAccountId":"A-100","toIban":12345,"amount":100,"currency":"TRY","description":"Kira"}  -> 500 {"code":"INTERNAL","message":"Internal server error"}
  ```
- **Beklenen (sözleşme):** `required: [..., "toIban", ...]`, `toIban: {type: string, pattern: ^TR[0-9]{24}$}` · `400 Validation error`.
- **Karşılaştırma:** Diğer zorunlu alanlar doğru şekilde 400 dönüyor (TC-010, TC-012, TC-013). Hatalı desenli string IBAN da doğru şekilde 400 dönüyor (TC-036: `"toIban must be a TR IBAN"`).
- **Şüphe (not):** Desen kontrolü, tip veya varlık kontrolü yapılmadan string metodu çağırıyor olabilir.
- **Önem:** medium. Veri değişmiyor, ancak hatalı girdi 500 üretiyor, istemci hatayı ayrıştıramıyor ve izleme alarmları gereksiz tetikleniyor. Yığın izi sızmıyor.

## DEF-006: GET /accounts/{accountId} `balance` alanını string döndürüyor
- **Bağlantılar:** TC-004 (başarısız), REQ-020 · ilgili: Q-008
- **Adım:** `GET /accounts/A-100` (alice)
- **Beklenen (sözleşme):** `Account.balance: {type: number}`
- **Gerçekleşen:** `200 {"id":"A-100",...,"balance":"49774.79"}`. Şema denetimi: `$.balance: expected number, got string ("49774.79")`.
- **Tutarsızlık:** Aynı hesap `GET /accounts` listesinde sayı olarak geliyor: `"balance":49774.79`.
- **Önem:** medium. Sayı bekleyen istemcilerde tip hatası veya string birleştirme hatası oluşabilir.

## DEF-007: EUR hesaptan TRY para birimli transfer, kur çevrimi olmadan kabul ediliyor
- **Bağlantılar:** TC-035 (başarısız), REQ-023 (türetilmiş, onay bekliyor) · **Q-004 engelleyici**
- **Adım:** `POST /transfers {"fromAccountId":"A-101","toIban":"TR330006100519786457841326","amount":1,"currency":"TRY","description":"TC-035"}` (A-101 bir EUR hesabı)
- **Beklenen (türetilmiş kural, sözleşmede yok):** Hesap para birimiyle uyuşmayan transfer reddedilir (400/422) ya da dokümante bir kur ile çevrilir.
- **Gerçekleşen:** `200 {"id":"T-12","status":"COMPLETED","amount":1,"currency":"TRY","fromAccountId":"A-101",...}`. A-101 bakiyesi 2499,50 → 2498,50 EUR oldu: 1 TRY'lik transfer için 1 EUR düşüldü.
- **Sınıf:** Sözleşme eksikliği (kural tanımlı değil) ve muhtemel uygulama hatası. Kur çevrimi olmadan para birimi karışması yanlış tutar hareketi demektir.
- **Önem:** high (Q-004 yanıtı "reddedilmeli" veya "kur çevrilmeli" olursa).

## DEF-008 (düşük, gözlem): Yanıltıcı doğrulama mesajları
- `Content-Type: application/json` ile yarım JSON `{"fromAccountId": "A-100", "amount": ` gönderildi → `400 {"code":"VALIDATION","message":"fromAccountId is required"}`. Aynı bozuk gövde `text/plain` ile gönderildiğinde doğru mesaj dönüyor: `400 {"code":"BAD_JSON","message":"Body is not valid JSON"}`. Ayrıştırma hatası sessizce boş gövdeye çevriliyor olabilir (şüphe).
- `"fromAccountId": 12345` → `400 "fromAccountId is required"`. Alan gönderilmiş, yalnızca tipi yanlış.
- Durum kodları doğru olduğu için TC-042 ve TC-014 geçti. Sorun yalnızca mesajın tüketiciyi yanıltması. Sınıf: uygulama hatası, önem: low.

---

## Test verisi sorunları ve test tarafı düzeltmeleri (ürün hatası değil)
1. **OpenAPI örneği `T-1` ortamda yoktu.** Başlangıçta `GET /transfers/T-1` her iki kullanıcı için 404 döndü. Üretilen TC-026 ve TC-029 bu örnek kimliği kullandığı için yanlış başarısız olurdu. Düzeltme: iki test kendi 1 TRY'lik transferini oluşturup onun kimliğini kullanıyor. Bu, sözleşme sorusu Q-012'ye de girdi.
2. **Run 1'de 4 test yanlış başarısız oldu.** TC-026, TC-029, TC-034 ve TC-039, ön koşul adımında (test verisi oluşturma) `201` bekliyordu, bu yüzden DEF-004'ün maskelediği yanlış başarısızlıklar üretti. TC-039 ise 200'ü "reddedildi" dalı olarak yorumladı. Düzeltme: ön koşullar yalnızca 2xx bekliyor, 201 kontrolü TC-008'de kalıyor. Run 2'de dördü de geçti: transfer okumada BOLA yok (404), bakiye tam tutar kadar düşüyor, `id`/`status` istemciden atanamıyor.
3. **Bakiye bütçesi.** Ortam sıfırlanamıyor. Run 1, A-100'den 100.214,11 TRY tüketti (150.000 → 49.785,89). Bunun 50.000,01 TRY'si DEF-003 yüzünden kabul edilen transferdir. Run 1'in JSON raporu, CLI'da `--reporter` ile yapılandırmadaki reporter'ın ezilmesi nedeniyle diske yazılmadı (test ekibinin hatası). Run 2 bu yüzden gerekti ve TC-018/TC-019 hariç tutuldu: 50000'lik testler düşük bakiyede yanlış sonuç verirdi. İki testin sonuçları run 1'in line çıktısından `qa/results.json`'a not düşülerek aktarıldı.
4. **Sonraki koşum için öneri:** Seed veya sıfırlama endpoint'i ya da ayrılmış yüksek bakiyeli bir test hesabı istenmeli. Aksi halde TC-018 ve TC-019 anlamlı biçimde tekrar koşulamaz.

## Yeniden test
Her hata için yeniden test, aynı TC ile ve sınırın komşularıyla yapılmalı: DEF-003 için 50000 / 50000,01, DEF-005 için diğer zorunlu alanlar. Etki listesi `python build_rtm.py ... --changed REQ-020,REQ-021` ile alınabilir.
