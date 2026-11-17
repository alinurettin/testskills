# Kusur (Defect) Raporu — Anadolu Güven Sigorta Poliçe & Hasar API

**Test Edilen Ortam:** `http://localhost:4101`  
**Referans Sözleşme:** `openapi.yaml` (OpenAPI 3.1.0, v1.0.0)  
**Kanıt Kaydı:** [`test-kayitlari.md`](./test-kayitlari.md) (`TC-001` – `TC-079`)

---

## Yönetici Özeti

Yayın öncesi bağımsız API testi kapsamında `openapi.yaml` sözleşmesindeki tüm uçlar, yetkilendirme kuralları, iş kuralları, sayfalama/filtreleme, idempotency ve beklenmedik/hatalı girdiler test edilmiştir. Toplam **13 adet kusur** tespit edilmiştir:

- **Kritik (3):** `GET /admin/stats` yetki aşımı, `GET /claims?policyId=...` üzerinden başkasının hasar kayıtlarına erişim (IDOR), `null` JSON gövdesi ile sunucu çökmesi (DoS).
- **Yüksek (3):** `PATCH /policies/{id}` ile salt okunur `status` alanının değiştirilebilmesi, `POST /claims` tutarının teminat limitini aşabilmesi (`422` kontrolünün olmaması), `Idempotency-Key` başlığının yok sayılması.
- **Orta (7):** Hatalı JSON'da yığın izi (`stack`) ve dosya yolu sızıntısı, `POST /claims` durum kodunun `201` yerine `200` dönmesi, `Claim.claimNumber` zorunlu alanının eksikliği, `GET /claims` `meta.total` hatası, `POST /claims` girdi doğrulama eksiklikleri, `GET /claims` sayfalama parametre doğrulama eksiklikleri, `PATCH /policies/{id}` tip/gövde doğrulama eksiklikleri.

Mevcut haliyle API'nin **canlı ortama alınması önerilmez**; özellikle Kritik ve Yüksek önem dereceli yetkilendirme, iş kuralı ve kararlılık kusurları yayın öncesi giderilmelidir.

| Bulgu ID | Önem | Başlık | Etkilenen Uç(lar) | Kanıt |
|----------|------|--------|-------------------|-------|
| BULGU-01 | Kritik | Normal kullanıcılar `GET /admin/stats` ucuna erişebiliyor | `GET /admin/stats` | `TC-070`, `TC-071` |
| BULGU-02 | Kritik | `policyId` filtresi ile başka kullanıcının hasar talepleri okunabiliyor (IDOR) | `GET /claims?policyId=...` | `TC-036`, `TC-037` |
| BULGU-03 | Kritik | `null` JSON gövdesi sunucuyu çökertiyor ve bellek içi durumu sıfırlıyor (DoS) | `PATCH /policies/{id}`, `POST /claims` | `TC-075`–`TC-079` |
| BULGU-04 | Yüksek | Salt okunur `status` alanı `PATCH` ile değiştirilebiliyor ve geçersiz enum kabul ediliyor | `PATCH /policies/{id}` | `TC-021`–`TC-024` |
| BULGU-05 | Yüksek | Hasar tutarının poliçe `coverageLimit` değerini aşması engellenmiyor (`422` yok) | `POST /claims` | `TC-054`, `TC-055` |
| BULGU-06 | Yüksek | `Idempotency-Key` başlığı yok sayılıyor ve mükerrer hasar kaydı oluşuyor | `POST /claims` | `TC-056`, `TC-057` |
| BULGU-07 | Orta | Bozuk JSON hata yanıtında `stack` ve sunucu dosya yolu sızdırılıyor | `PATCH /policies/{id}`, `POST /claims` | `TC-031`, `TC-066` |
| BULGU-08 | Orta | `POST /claims` `201 Created` yerine `200 OK` döndürüyor | `POST /claims` | `TC-053`–`TC-065` |
| BULGU-09 | Orta | `Claim` nesnelerinde zorunlu `claimNumber` alanı eksik | `GET /claims`, `GET /claims/{id}`, `POST /claims` | `TC-033`, `TC-034`, `TC-047`, `TC-053` |
| BULGU-10 | Orta | `GET /claims` `meta.total` toplam kayıt yerine geçerli sayfa sayısını dönüyor | `GET /claims` | `TC-038`, `TC-039`, `TC-040` |
| BULGU-11 | Orta | `POST /claims` `amount` alt sınır (`minimum: 1`), `1e309` ve tip doğrulaması eksik | `POST /claims` | `TC-058`–`TC-061`, `TC-063`, `TC-064` |
| BULGU-12 | Orta | `GET /claims` `page` ve `pageSize` parametreleri doğrulanmıyor | `GET /claims` | `TC-041`–`TC-046` |
| BULGU-13 | Orta | `PATCH /policies/{id}` alan tipi, boş değer ve nesne-dışı gövde doğrulaması eksik | `PATCH /policies/{id}` | `TC-025`–`TC-030` |

---

## Ayrıntılı Bulgular

### BULGU-01 — Normal Kullanıcıların Yönetici İstatistik Ucuna Erişebilmesi (Yetki Aşımı)
- **Önem Derecesi:** Kritik
- **Etkilenen Uç:** `GET /admin/stats` (`adminStats`)
- **Sözleşme / İş Kuralı Atfı:** `openapi.yaml` (`paths./admin/stats.get`, satır 257–273): *"Sistem genel istatistiklerini döner. Yalnızca role=admin erişebilir; normal kullanıcı için 403 dönülmelidir."* Ayrıca genel yetkilendirme kuralları (satır 11–15, 26–27).
- **Beklenen Davranış:** `role=user` olan kullanıcılar (`tok_user1_ayse`, `tok_user2_mehmet`) için `403 Forbidden` (`Error` şeması) dönülmelidir (tıpkı `GET /admin/policies` ucunun yaptığı gibi; bkz. `TC-067`).
- **Gerçekleşen Davranış:** Normal kullanıcı token'ları ile `GET /admin/stats` isteği atıldığında `200 OK` dönülmekte ve tüm sistemdeki poliçe sayısı, hasar sayısı ve toplam prim tutarı sızdırılmaktadır.
- **Tekrar Üretim Adımları:**
  1. Token: `Authorization: Bearer tok_user1_ayse` (veya `tok_user2_mehmet`)
  2. İstek:
     ```http
     GET http://localhost:4101/admin/stats
     Authorization: Bearer tok_user1_ayse
     ```
  3. Gözlenen Yanıt (`TC-070`, `TC-071`):
     ```text
     HTTP 200 OK
     {"totalPolicies":5,"totalClaims":19,"totalPremium":9800}
     ```
- **Kanıt Referansı:** `test-kayitlari.md` → `TC-070`, `TC-071` (karşılaştırma için `TC-067`, `TC-069`, `TC-072`).

---

### BULGU-02 — `GET /claims?policyId=...` Üzerinden Başkasının Hasar Taleplerini Okuma (IDOR)
- **Önem Derecesi:** Kritik
- **Etkilenen Uç:** `GET /claims` (`listClaims`, `policyId` sorgu parametresi)
- **Sözleşme / İş Kuralı Atfı:** `openapi.yaml` (`paths./claims.get`, satır 125–129): *"Kimliği doğrulanan kullanıcının KENDİ hasar taleplerini sayfalı olarak döner. `policyId` sorgu parametresi verilirse yalnızca o poliçeye ait talepler süzülür; ancak bu durumda da yetkilendirme kuralı geçerlidir: kullanıcı yalnızca KENDİSİNE ait poliçelerin taleplerini görebilir."*
- **Beklenen Davranış:** Normal bir kullanıcı kendisine ait olmayan bir `policyId` ile sorgulama yaptığında karşı kullanıcının hasar kayıtları kesinlikle döndürülmemelidir (`403` veya kendi kayıtları süzülerek boş liste; sözleşmeye göre başka kullanıcının kayıtlarına erişim yasaktır).
- **Gerçekleşen Davranış:** `policyId` sorgu parametresi verildiğinde kimliği doğrulanan kullanıcının `ownerUserId` kontrolü devre dışı kalmakta; herhangi bir kullanıcı `policyId` değerini değiştirerek tüm diğer kullanıcıların hasar kayıtlarını (`ownerUserId`, `amount`, `status`, `description`, `createdAt`) `200 OK` ile listeleyebilmektedir.
- **Tekrar Üretim Adımları:**
  1. Token: `Authorization: Bearer tok_user1_ayse` (`u1`)
  2. İstek (`u2`'ye ait `pol_3` poliçesi için):
     ```http
     GET http://localhost:4101/claims?policyId=pol_3
     Authorization: Bearer tok_user1_ayse
     ```
  3. Gözlenen Yanıt (`TC-036`):
     ```text
     HTTP 200 OK
     {"data":[{"id":"clm_7","policyId":"pol_3","ownerUserId":"u2","amount":1000,"status":"rejected","description":"Muayene masrafı","createdAt":"2026-06-11T13:00:00Z"}],"meta":{"page":1,"pageSize":20,"total":1}}
     ```
  4. Ters yönde (`u2` token'ı ile `GET /claims?policyId=pol_1`) de `u1`'in hasar kayıtları dönmektedir (`TC-037`).
- **Kanıt Referansı:** `test-kayitlari.md` → `TC-036`, `TC-037`.

---

### BULGU-03 — `null` JSON Gövdesi İle Sunucunun Çökmesi ve Durum Sıfırlanması (DoS)
- **Önem Derecesi:** Kritik
- **Etkilenen Uçlar:** `PATCH /policies/{id}` (`updatePolicy`), `POST /claims` (`createClaim`)
- **Sözleşme / İş Kuralı Atfı:** `openapi.yaml` (`PolicyUpdate` şeması satır 345–346 `type: object`, `ClaimCreate` şeması satır 382–383 `type: object`, `BadRequest` satır 110–111, 196–197, 298–302).
- **Beklenen Davranış:** Gövde olarak JSON `null` gönderildiğinde sunucu kontrollü biçimde `400 Bad Request` (`Error` şeması) dönmeli ve çalışmaya devam etmelidir.
- **Gerçekleşen Davranış:** Geçerli bir kullanıcı token'ı ile `Content-Type: application/json` başlığı altında gövde olarak `null` gönderildiğinde sunucu yanıt vermeden TCP bağlantısını kesmekte (`ConnectionResetError 10054`), süreç çökmekte ve yeniden başlamaktadır. Yeniden başlatma sonrasında bellek içi tüm değişiklikler/kayıtlar silinerek başlangıç durumuna (`7` hasar talebi) dönmektedir.
- **Tekrar Üretim Adımları:**
  1. Token: `Authorization: Bearer tok_user1_ayse`
  2. İstek 1 (`PATCH`):
     ```http
     PATCH http://localhost:4101/policies/pol_2
     Authorization: Bearer tok_user1_ayse
     Content-Type: application/json

     null
     ```
  3. İstek 2 (`POST`):
     ```http
     POST http://localhost:4101/claims
     Authorization: Bearer tok_user1_ayse
     Content-Type: application/json

     null
     ```
  4. Gözlenen Sonuç (`TC-075`, `TC-077`, `TC-079`): Her iki istekte de yanıt alınamadan bağlantı kapatılır (`ConnectionResetError(10054)`). Ardından `GET /claims` (`TC-079`) ile daha önce oluşturulan kayıtların (`clm_8`–`clm_19`) kaybolduğu ve sayının `7`'ye sıfırlandığı doğrulanmıştır.
- **Kanıt Referansı:** `test-kayitlari.md` → `TC-075`, `TC-076`, `TC-077`, `TC-078`, `TC-079`.

---

### BULGU-04 — `PATCH /policies/{id}` İle Salt Okunur `status` Alanının Değiştirilebilmesi
- **Önem Derecesi:** Yüksek
- **Etkilenen Uç:** `PATCH /policies/{id}` (`updatePolicy`)
- **Sözleşme / İş Kuralı Atfı:** `openapi.yaml` (`paths./policies/{id}.patch`, satır 92–98; `Policy.status` satır 335–337): *"`premium`, `coverageLimit`, `status`, `ownerUserId`, `policyNumber`, `coverageType` alanları salt okunurdur ve istek gövdesiyle DEĞİŞTİRİLEMEZ; bu alanlar gövdede gönderilse bile yok sayılmalıdır. Poliçenin durumu (`status`) yalnızca iç iş süreçleriyle değişir."* Ayrıca `status` yalnızca `[active, cancelled, expired, pending]` değerlerini alabilir.
- **Beklenen Davranış:** Gövdede `status` gönderildiğinde yok sayılmalı, poliçenin mevcut `status` değeri değişmeden kalmalıdır. (Diğer salt okunur alanlar `premium`, `coverageLimit`, `ownerUserId`, `policyNumber`, `coverageType` test edilmiş ve yok sayıldığı görülmüştür — `TC-020`.)
- **Gerçekleşen Davranış:** `status` alanı gövde ile doğrudan güncellenebilmektedir. Poliçe sahibi iptal edilmiş (`cancelled`) bir poliçeyi kendi başına `active` yapabilmekte (`TC-021`), ayrıca `"bogus_status"` gibi sözleşmedeki enum dışında geçersiz değerleri dahi kaydedebilmektedir (`TC-023`).
- **Tekrar Üretim Adımları:**
  1. Token: `Authorization: Bearer tok_user2_mehmet` (`pol_3` sahibi; başlangıç durumu `cancelled`)
  2. İstek:
     ```http
     PATCH http://localhost:4101/policies/pol_3
     Authorization: Bearer tok_user2_mehmet
     Content-Type: application/json

     {"status": "active"}
     ```
  3. Gözlenen Yanıt (`TC-021`):
     ```text
     HTTP 200 OK
     {"id":"pol_3","policyNumber":"POL-2026-0003","ownerUserId":"u2","holderName":"Mehmet Demir","holderTckn":"22222222220","coverageType":"saglik","premium":900,"coverageLimit":20000,"status":"active","agentName":"Can Öz","startDate":"2026-01-10","endDate":"2026-07-10"}
     ```
  4. Benzer şekilde `tok_user1_ayse` ile `PATCH /policies/pol_5` gövdesi `{"status": "bogus_status"}` gönderildiğinde `200 OK` ile `"status":"bogus_status"` kaydedilmiştir (`TC-023`).
- **Kanıt Referansı:** `test-kayitlari.md` → `TC-021`, `TC-022`, `TC-023`, `TC-024` (ve diğer alanlar için `TC-020`).

---

### BULGU-05 — Hasar Talebi Tutarının Poliçe Teminat Limitini Aşması Engellenmiyor (`422` Eksik)
- **Önem Derecesi:** Yüksek
- **Etkilenen Uç:** `POST /claims` (`createClaim`)
- **Sözleşme / İş Kuralı Atfı:** `openapi.yaml` (`paths./claims.post`, satır 171–173, 202–206; `ClaimCreate.amount` satır 390): *"İş kuralı: Bir hasar talebinin tutarı (`amount`), ilgili poliçenin teminat limitini (`coverageLimit`) AŞAMAZ. Aşan istekler 422 ile reddedilmelidir."*
- **Beklenen Davranış:** `coverageLimit` değeri `50000` olan `pol_1` poliçesi için `amount > 50000` (ör. `50000.01` veya `50001`) gönderildiğinde `422` dönülmeli ve kayıt oluşturulmamalıdır.
- **Gerçekleşen Davranış:** Poliçenin teminat limiti hiç kontrol edilmemekte, limiti aşan hasar talepleri başarılı kabul edilip kaydedilmektedir.
- **Tekrar Üretim Adımları:**
  1. Token: `Authorization: Bearer tok_user1_ayse` (`pol_1` poliçesi, `coverageLimit: 50000`)
  2. İstek:
     ```http
     POST http://localhost:4101/claims
     Authorization: Bearer tok_user1_ayse
     Content-Type: application/json

     {"policyId": "pol_1", "amount": 50001, "description": "Limit aşımı"}
     ```
  3. Gözlenen Yanıt (`TC-054`):
     ```text
     HTTP 200 OK
     {"id":"clm_10","policyId":"pol_1","ownerUserId":"u1","amount":50001,"status":"submitted","description":"Limit aşımı","createdAt":"2026-08-01T00:00:00Z"}
     ```
  4. `amount: 50000.01` ile de kayıt (`clm_11`) oluşturulmuştur (`TC-055`).
- **Kanıt Referansı:** `test-kayitlari.md` → `TC-054`, `TC-055`.

---

### BULGU-06 — `POST /claims` `Idempotency-Key` Başlığını Yok Sayıyor (Mükerrer Kayıt Oluşumu)
- **Önem Derecesi:** Yüksek
- **Etkilenen Uç:** `POST /claims` (`createClaim`)
- **Sözleşme / İş Kuralı Atfı:** `openapi.yaml` (`paths./claims.post`, satır 176–184): *"Idempotency (tekrar koruması): İstek `Idempotency-Key` başlığı ile gönderilirse, aynı anahtarla yapılan tekrar istekleri YENİ kayıt OLUŞTURMAMALI, ilk oluşturulan kaydı aynen döndürmelidir."*
- **Beklenen Davranış:** Aynı `Idempotency-Key` değeriyle tekrarlanan ikinci istek yeni hasar talebi açmamalı ve ilk oluşturulan kaydı (aynı `id`) geri döndürmelidir.
- **Gerçekleşen Davranış:** `Idempotency-Key` başlığı tamamen göz ardı edilmektedir; aynı anahtar ve aynı gövdeyle gönderilen her istek yeni bir `id` ile mükerrer hasar talebi oluşturmaktadır.
- **Tekrar Üretim Adımları:**
  1. Token: `Authorization: Bearer tok_user1_ayse`
  2. İstek (aynı isteği 2 kez arka arkaya gönderin):
     ```http
     POST http://localhost:4101/claims
     Authorization: Bearer tok_user1_ayse
     Content-Type: application/json
     Idempotency-Key: qa-idem-001

     {"policyId": "pol_5", "amount": 2500, "description": "Idem test"}
     ```
  3. Gözlenen Yanıtlar (`TC-056` ve `TC-057`):
     - 1. istek (`TC-056`): `HTTP 200` → `{"id":"clm_12","policyId":"pol_5","ownerUserId":"u1","amount":2500,...}`
     - 2. istek (`TC-057`): `HTTP 200` → `{"id":"clm_13","policyId":"pol_5","ownerUserId":"u1","amount":2500,...}` (yeni kayıt oluştu!)
- **Kanıt Referansı:** `test-kayitlari.md` → `TC-056`, `TC-057`.

---

### BULGU-07 — Hatalı JSON Yanıtlarında Yığın İzi (`stack`) ve Sunucu Dosya Yolu Sızıntısı
- **Önem Derecesi:** Orta
- **Etkilenen Uçlar:** `PATCH /policies/{id}`, `POST /claims`
- **Sözleşme / İş Kuralı Atfı:** `openapi.yaml` (`components.responses.BadRequest`, satır 298–302; `components.schemas.Error`, satır 403–408): Hata yanıtları `{error, message}` formatındaki `Error` şemasına uymalı; iç sistem ayrıntıları dışarı sızdırılmamalıdır.
- **Beklenen Davranış:** Geçersiz sözdizimli JSON gönderildiğinde yalnızca güvenli bir `400` hata mesajı (`{"error": "...", "message": "..."}`) dönülmelidir.
- **Gerçekleşen Davranış:** `400` yanıtı içinde sözleşmede yer almayan `detail` ve `stack` alanları dönülerek sunucunun Node.js yığın izi, satır numaraları ve tam yerel dosya yolu istemciye açılmaktadır.
- **Tekrar Üretim Adımları:**
  1. Token: `Authorization: Bearer tok_user1_ayse`
  2. İstek:
     ```http
     POST http://localhost:4101/claims
     Authorization: Bearer tok_user1_ayse
     Content-Type: application/json

     {"policyId": "pol_1", 
     ```
  3. Gözlenen Yanıt (`TC-066`; benzeri `TC-031`'de `PATCH /policies/pol_2` için de gözlenmiştir):
     ```json
     {"error":"Geçersiz JSON","detail":"Expected double-quoted property name in JSON at position 22 (line 1 column 23)","stack":"SyntaxError: Expected double-quoted property name in JSON at position 22 (line 1 column 23)\n    at JSON.parse (<anonymous>)\n    at Server.<anonymous> (C:\\eval\\servers\\R01\\server.js:216:25)\n    at process.processTicksAndRejections (node:internal/process/task_queues:104:5)"}
     ```
- **Kanıt Referansı:** `test-kayitlari.md` → `TC-031`, `TC-066`.

---

### BULGU-08 — `POST /claims` Başarılı Yanıt Durum Kodu Sözleşmeye Aykırı (`200` Yerine `201`)
- **Önem Derecesi:** Orta
- **Etkilenen Uç:** `POST /claims` (`createClaim`)
- **Sözleşme / İş Kuralı Atfı:** `openapi.yaml` (`paths./claims.post.responses.'201'`, satır 190–195): Başarılı kaynak oluşturma yanıtı `'201'` olarak tanımlıdır; `'200'` yanıtı tanımlı değildir.
- **Beklenen Davranış:** Geçerli hasar talebi oluşturulduğunda HTTP `201 Created` dönülmelidir.
- **Gerçekleşen Davranış:** Başarılı olan tüm `POST /claims` istekleri HTTP `200 OK` döndürmektedir.
- **Tekrar Üretim Adımları:**
  1. Token: `Authorization: Bearer tok_user1_ayse`
  2. İstek:
     ```http
     POST http://localhost:4101/claims
     Authorization: Bearer tok_user1_ayse
     Content-Type: application/json

     {"policyId": "pol_1", "amount": 1500, "description": "QA geçerli talep"}
     ```
  3. Gözlenen Yanıt (`TC-053`): `HTTP 200 OK` (`201` bekleniyordu).
- **Kanıt Referansı:** `test-kayitlari.md` → `TC-053` (ayrıca `TC-054`–`TC-061`, `TC-064`, `TC-065`).

---

### BULGU-09 — `Claim` Nesnelerinde Zorunlu `claimNumber` Alanı Eksik
- **Önem Derecesi:** Orta
- **Etkilenen Uçlar:** `GET /claims`, `GET /claims/{id}`, `POST /claims`
- **Sözleşme / İş Kuralı Atfı:** `openapi.yaml` (`components.schemas.Claim`, satır 354–369): `Claim` şemasının `required` listesinde `claimNumber` (`type: string`, ör. `'CLM-2026-0001'`) zorunlu alan olarak belirtilmiştir.
- **Beklenen Davranış:** Dönen her `Claim` nesnesinde `claimNumber` alanı bulunmalıdır.
- **Gerçekleşen Davranış:** Hem mevcut tohum verilerindeki (`clm_1`–`clm_7`) hem de `POST /claims` ile yeni oluşturulan kayıtlardaki (`clm_9`+) `Claim` JSON nesnelerinde `claimNumber` alanı hiç yer almamaktadır.
- **Tekrar Üretim Adımları:**
  1. Token: `Authorization: Bearer tok_user1_ayse`
  2. İstek: `GET http://localhost:4101/claims/clm_1` (veya `GET /claims`, `POST /claims`)
  3. Gözlenen Yanıt (`TC-047`):
     ```json
     {"id":"clm_1","policyId":"pol_1","ownerUserId":"u1","amount":12000,"status":"submitted","description":"Çarpma hasarı","createdAt":"2026-05-02T09:00:00Z"}
     ```
     (`claimNumber` alanı yok.)
- **Kanıt Referansı:** `test-kayitlari.md` → `TC-033`, `TC-034`, `TC-047`, `TC-053`.

---

### BULGU-10 — `GET /claims` Sayfalama Yanıtında `meta.total` Değerinin Yanlış Hesaplanması
- **Önem Derecesi:** Orta
- **Etkilenen Uç:** `GET /claims` (`listClaims`)
- **Sözleşme / İş Kuralı Atfı:** `openapi.yaml` (`paths./claims.get`, satır 132–134; `PageMeta.total`, satır 400–402): *"Yanıttaki `meta.total` alanı, sayfalama uygulanmadan önceki TOPLAM (tüm sayfalardaki) kayıt sayısını belirtir; yalnızca geçerli sayfadaki kayıt sayısını değil."*
- **Beklenen Davranış:** `u1` kullanıcısının `6` kaydı varken `?page=1&pageSize=2` isteğinde `meta.total` değeri `6` olmalıdır (benzer şekilde `admin` için `8` kayıt varken `?page=1&pageSize=3` isteğinde `total: 8` olmalıdır).
- **Gerçekleşen Davranış:** `meta.total` her zaman sayfalama sonrası geçerli sayfadaki kayıt sayısını (`data.length`) döndürmektedir.
- **Tekrar Üretim Adımları:**
  1. Token: `Authorization: Bearer tok_user1_ayse` (`u1`'in toplam 6 kaydı varken)
  2. İstek: `GET http://localhost:4101/claims?page=1&pageSize=2`
  3. Gözlenen Yanıt (`TC-038`): `data` içinde 2 kayıt, `meta: {"page":1,"pageSize":2,"total":2}` (`6` yerine `2` döndü). `admin` token'ı ile `GET /claims?page=1&pageSize=3` (`TC-040`) isteğinde de toplam 8 kayıt varken `"total":3` dönmüştür.
- **Kanıt Referansı:** `test-kayitlari.md` → `TC-038`, `TC-039`, `TC-040`.

---

### BULGU-11 — `POST /claims` Tutar Alt Sınırı (`minimum: 1`), Taşan Sayı ve Alan Tipi Doğrulaması Eksik
- **Önem Derecesi:** Orta
- **Etkilenen Uç:** `POST /claims` (`createClaim`)
- **Sözleşme / İş Kuralı Atfı:** `openapi.yaml` (`Claim.amount` satır 372–375; `ClaimCreate` satır 382–393): `amount` `minimum: 1` (*"1'den küçük olamaz"*), `policyId` `type: string`, `description` `type: ['string', 'null']`.
- **Beklenen Davranış:** `amount < 1` (`0`, `-100`, `0.5`), sonlu olmayan taşan sayılar (`1e309` → JS `Infinity`), string olmayan `policyId: null` ve string/null olmayan `description: 999` istekleri `400 Bad Request` ile reddedilmelidir.
- **Gerçekleşen Davranış:**
  - `amount: 0` (`TC-058`), `amount: -100` (`TC-059`) ve `amount: 0.5` (`TC-060`) istekleri `200` ile kabul edilip geçersiz tutarlı hasar kaydı oluşturmaktadır.
  - `amount: 1e309` (`TC-061`) gönderildiğinde `Infinity` sayısı `typeof === 'number'` kontrolünden geçmekte ve JSON serileştirmede `"amount": null` olarak kaydedilmektedir (hem tip ihlali hem limit kontrolü bypass'ı).
  - `policyId: null` (`TC-063`) `400` yerine `404 Poliçe bulunamadı` dönmektedir.
  - `description: 999` (`TC-064`) reddedilmek yerine sessizce `""` yapılmaktadır.
- **Tekrar Üretim Adımları:**
  1. Token: `Authorization: Bearer tok_user1_ayse`
  2. İstek (`amount: -100`):
     ```http
     POST http://localhost:4101/claims
     Authorization: Bearer tok_user1_ayse
     Content-Type: application/json

     {"policyId": "pol_5", "amount": -100}
     ```
  3. Gözlenen Yanıt (`TC-059`):
     ```text
     HTTP 200 OK
     {"id":"clm_15","policyId":"pol_5","ownerUserId":"u1","amount":-100,"status":"submitted","description":"","createdAt":"2026-08-01T00:00:00Z"}
     ```
  4. `{"policyId":"pol_5","amount":1e309}` (`TC-061`) gönderildiğinde yanıt: `{"id":"clm_17",...,"amount":null,...}`.
- **Kanıt Referansı:** `test-kayitlari.md` → `TC-058`, `TC-059`, `TC-060`, `TC-061`, `TC-063`, `TC-064`.

---

### BULGU-12 — `GET /claims` Sayfalama Parametrelerinin (`page`, `pageSize`) Doğrulanmaması
- **Önem Derecesi:** Orta
- **Etkilenen Uç:** `GET /claims` (`listClaims`)
- **Sözleşme / İş Kuralı Atfı:** `openapi.yaml` (`paths./claims.get.parameters`, satır 140–147; `PageMeta` satır 394–402): `page` (`integer, minimum: 1`), `pageSize` (`integer, minimum: 1, maximum: 100`); `PageMeta.page` ve `PageMeta.pageSize` zorunlu `integer` alanlardır.
- **Beklenen Davranış:** Sınır dışı (`page <= 0`, `pageSize <= 0`, `pageSize > 100`) veya sayı olmayan (`abc`) değerlerde `400 Bad Request` dönülmeli ya da `PageMeta` şeması bozulmamalıdır.
- **Gerçekleşen Davranış:**
  - `page=-1&pageSize=2` (`TC-041`) verildiğinde negatif dizi dilimlemesi (`slice(-4, -2)`) nedeniyle dizinin sonundan rastgele kayıtlar (`clm_3`, `clm_4`) ve `"page": -1` dönmektedir.
  - `page=abc` (`TC-043`) veya `pageSize=abc` (`TC-044`) verildiğinde `NaN` serileşerek `meta.page: null` / `meta.pageSize: null` dönmekte ve `PageMeta` (`type: integer`) şeması ihlal edilmektedir.
  - `page=0` (`TC-042`), `pageSize=-5` (`TC-045` — `clm_1` dönüyor) ve `pageSize=200` (`TC-046` — `maximum: 100` sınırını aşıyor) değerleri `200 OK` ile kabul edilmektedir.
- **Tekrar Üretim Adımları:**
  1. Token: `Authorization: Bearer tok_user1_ayse`
  2. İstek 1: `GET http://localhost:4101/claims?page=-1&pageSize=2` → `200`, `clm_3`, `clm_4` kayıtları ve `"meta":{"page":-1,"pageSize":2,"total":2}` (`TC-041`).
  3. İstek 2: `GET http://localhost:4101/claims?page=abc&pageSize=2` → `200`, `{"data":[],"meta":{"page":null,"pageSize":2,"total":0}}` (`TC-043`).
- **Kanıt Referansı:** `test-kayitlari.md` → `TC-041`, `TC-042`, `TC-043`, `TC-044`, `TC-045`, `TC-046`.

---

### BULGU-13 — `PATCH /policies/{id}` Alan Tipi, Boş Değer ve Nesne-Dışı Gövde Doğrulaması Eksik
- **Önem Derecesi:** Orta
- **Etkilenen Uç:** `PATCH /policies/{id}` (`updatePolicy`)
- **Sözleşme / İş Kuralı Atfı:** `openapi.yaml` (`Policy` satır 322, 338–339; `PolicyUpdate` satır 345–353): `PolicyUpdate` gövdesi `type: object`, `holderName` `type: string` (boş/null/sayı olmamalı), `agentName` `type: ['string', 'null']`.
- **Beklenen Davranış:** `holderName` için `null`, boş string `""` veya sayısal değer (`12345`); `agentName` için sayısal değer (`12345`); ya da JSON nesnesi olmayan (`[]`, `123`) gövdeler `400 Bad Request` ile reddedilmelidir.
- **Gerçekleşen Davranış:** Tüm bu geçersiz girdiler `200 OK` ile kabul edilmekte ve `holderName: null`, `holderName: 12345`, `agentName: 12345` veya `holderName: ""` gibi `Policy` şemasını bozan değerler doğrudan poliçeye kaydedilmektedir.
- **Tekrar Üretim Adımları:**
  1. Token: `Authorization: Bearer tok_user1_ayse`
  2. İstek:
     ```http
     PATCH http://localhost:4101/policies/pol_2
     Authorization: Bearer tok_user1_ayse
     Content-Type: application/json

     {"holderName": 12345, "agentName": 12345}
     ```
  3. Gözlenen Yanıt (`TC-026`):
     ```text
     HTTP 200 OK
     {"id":"pol_2","policyNumber":"POL-2026-0002","ownerUserId":"u1","holderName":12345,"holderTckn":"11111111110","coverageType":"konut","premium":2400,"coverageLimit":100000,"status":"active","agentName":12345,"startDate":"2026-02-15","endDate":"2027-02-14"}
     ```
- **Kanıt Referansı:** `test-kayitlari.md` → `TC-025`, `TC-026`, `TC-027`, `TC-029`, `TC-030`.

---

## Sözleşmeye Uygun Çalıştığı Doğrulanan Alanlar (Özet)

Yanlış pozitif üretmemek adına aşağıdaki kontrollerin doğru çalıştığı ayrıca teyit edilmiştir:
- `/health` kimlik doğrulamasız `200` dönüyor; diğer tüm uçlar token olmadığında veya geçersiz/boş/`Basic` token gönderildiğinde `401` dönüyor (`TC-001`–`TC-005`, `TC-015`, `TC-032`, `TC-035`, `TC-050`, `TC-069`).
- `GET /policies`, `GET /policies/{id}`, `PATCH /policies/{id}` ve `GET /claims/{id}` uçlarında kullanıcılar arası erişim (IDOR) koruması doğru çalışıyor (`403`, `TC-007`–`TC-012`, `TC-016`, `TC-048`).
- `GET /admin/policies` ucu normal kullanıcılara `403` dönüyor (`TC-067`, `TC-068`).
- `PATCH /policies/{id}` ucunda `premium`, `coverageLimit`, `ownerUserId`, `policyNumber` ve `coverageType` alanları gönderilse de sözleşmeye uygun şekilde yok sayılıyor (`TC-020`).
- `POST /claims` ucunda başka kullanıcının poliçesi için hasar talebi açma girişimi `403` (`TC-051`), olmayan poliçe `404` (`TC-052`) ile engelleniyor; gövdede gönderilen `status`, `ownerUserId` ve `id` alanları yok sayılıyor (`TC-065`).
