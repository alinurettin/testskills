# Kusur (Defect) Raporu — Anadolu Güven Sigorta Poliçe & Hasar API

- **Hedef Sistem:** Anadolu Güven Sigorta — Poliçe & Hasar API (`v1.0.0`)
- **Test Ortamı:** `http://localhost:4106` (`127.0.0.1:4106`), sentetik veriler ve 3 test hesabı (`tok_user1_ayse` / `u1`, `tok_user2_mehmet` / `u2`, `tok_admin_root` / `admin`)
- **Referans Sözleşme:** `openapi.yaml` (OpenAPI 3.1.0)
- **Kanıt Kaydı:** Tüm istek/yanıt kayıtları [test-kayitlari.md](./test-kayitlari.md) dosyasında tutulmaktadır (toplam **165** HTTP isteği).
- **Özet Bulgular:** **5 Kritik**, **4 Yüksek**, **5 Orta**, **1 Düşük** olmak üzere toplam **15 kök-neden kusuru** tespit edilmiştir. Ayrıca sözleşme kapsamı dışında kalan **5 açık iş/tasarım sorusu** ayrıca not edilmiştir.

---

## Yayın Öncesi Değerlendirme (QA Özeti)

**Öneri:** API'nin mevcut haliyle **canlıya alınması önerilmez (Bloker / Hold)**. Kritik yetkilendirme açıkları (başka kullanıcının hasar taleplerine `policyId` filtresiyle erişim, normal kullanıcının yönetici istatistiklerine erişimi), `null` JSON gövdesiyle sunucunun çökmesi (DoS), poliçe `status` alanının kullanıcı tarafından değiştirilebilmesi ve teminat limiti / minimum tutar / idempotency kurallarının hiç uygulanmaması canlı ortamda doğrudan güvenlik, veri bütünlüğü ve finansal risk doğurmaktadır.

---

## Kusur Özeti Tablosu

| ID | Önem | Kısa Başlık | Etkilenen Uç(lar) | OWASP / Kural | Kanıt ID'leri |
|---|---|---|---|---|---|
| **BUG-01** | **Kritik** | `GET /claims?policyId=...` başka kullanıcının hasar taleplerini sızdırıyor (BOLA) | `GET /claims` | API1:2023 BOLA / ASVS V8 | `C-010`, `C-011` |
| **BUG-02** | **Kritik** | `PATCH /policies/{id}` ve `POST /claims` JSON `null` gövdesinde sunucuyu çökertiyor (DoS) | `PATCH /policies/{id}`, `POST /claims` | ASVS V2 / V16 | `M-004`, `E-025`–`E-027`, `N-004`–`N-008` |
| **BUG-03** | **Kritik** | `PATCH /policies/{id}` salt-okunur `status` alanının değiştirilmesine izin veriyor (Mass Assignment) | `PATCH /policies/{id}` | API3:2023 BOPLA / ASVS V15.3 | `PA-016`–`PA-019`, `E-003`, `E-004` |
| **BUG-04** | **Kritik** | `POST /claims` poliçe teminat limitini (`coverageLimit`) aşan tutarları `422` ile reddetmiyor | `POST /claims` | İş kuralı (Teminat Limiti) | `PC-020`–`PC-022`, `ID-005`, `X-010` |
| **BUG-05** | **Kritik** | `GET /admin/stats` yönetici ucuna normal kullanıcılar erişebiliyor (BFLA) | `GET /admin/stats` | API5:2023 BFLA / ASVS V8 | `AD-006`, `AD-007` |
| **BUG-06** | **Yüksek** | `POST /claims` `Idempotency-Key` başlığını yok sayıyor ve mükerrer kayıt oluşturuyor | `POST /claims` | Idempotency kuralı | `ID-001`, `ID-002`, `ID-RACE-1/2`, `E-001`, `E-002` |
| **BUG-07** | **Yüksek** | `POST /claims` `amount` alt sınırını (`minimum: 1`) doğrulamıyor; `0`, negatif ve `<1` değerleri kabul ediyor | `POST /claims` | Şema / Sınır (`minimum: 1`) | `PC-015`–`PC-019` |
| **BUG-08** | **Yüksek** | Geçersiz JSON hatası dahili sunucu dosya yolunu ve stack trace'i sızdırıyor | `POST /claims`, `PATCH /policies/{id}` | ASVS V16 / CWE-209 | `M-001`, `M-005` |
| **BUG-09** | **Yüksek** | `GET /claims` `meta.total` alanı toplam kayıt yerine geçerli sayfadaki kayıt sayısını dönüyor | `GET /claims` | Sayfalama sözleşmesi | `C-005`–`C-008`, `X-013`, `X-014` |
| **BUG-10** | **Orta** | Tüm `Claim` yanıtlarında zorunlu `claimNumber` alanı eksik | `GET /claims`, `GET /claims/{id}`, `POST /claims` | `Claim` şeması (`required`) | `C-001`–`C-003`, `CD-001`, `PC-019` |
| **BUG-11** | **Orta** | `POST /claims` yeni hasar talebi oluşturduğunda `201` yerine `200` dönüyor | `POST /claims` | HTTP durum kodu (`201`) | `PC-019`, `PC-022`, `X-012` |
| **BUG-12** | **Orta** | `PATCH /policies/{id}` `holderName` ve `agentName` alanlarında tip ve boş değer doğrulaması yapmıyor | `PATCH /policies/{id}` | `Policy` / `PolicyUpdate` şeması | `PA-011`–`PA-015`, `X-003`–`X-005` |
| **BUG-13** | **Orta** | `GET /claims` geçersiz `page`/`pageSize` parametrelerini `200` ile kabul edip şema dışı `null` `meta` dönüyor | `GET /claims` | `page`/`pageSize` & `PageMeta` şeması | `C-012`–`C-016`, `E-018` |
| **BUG-14** | **Orta** | `POST /claims` gövde doğrulamasında tip/ek alan tutarsızlıkları (`description` sessiz sıfırlama, `policyId` tipi için `404`, `additionalProperties` ihlali) | `POST /claims` | `ClaimCreate` şeması | `PC-009`, `PC-014`, `PC-024`, `PC-026`, `E-014`, `X-011` |
| **BUG-15** | **Düşük** | `openapi.yaml` sözleşme çelişkisi ve eksik kısıtlar (`PolicyUpdate` `additionalProperties: false` vs açıklama, eksik `400` / sınırlar) | `openapi.yaml` (`PATCH /policies/{id}`, `GET /claims`, `POST /claims`) | Sözleşme kalitesi | `X-002`, `openapi_tests.py` çıktısı |

---

## Ayrıntılı Kusur Raporları

### BUG-01 — `GET /claims?policyId=...` sorgu parametresinde BOLA (IDOR) yetkilendirme atlatması

- **Önem Derecesi:** Kritik (`OWASP API1:2023 BOLA` · `OWASP ASVS V8`)
- **Tekrarlanabilirlik:** Kesin (Her denemede / 2/2 test)
- **Etkilenen Uç:** `GET /claims` (`policyId` sorgu parametresi)
- **Bağlı Kanıtlar:** `test-kayitlari.md` → `C-010`, `C-011`
- **Sözleşme / İş Kuralı Atfı:**
  - `openapi.yaml` (satır 13–14): *"Normal kullanıcı (role=user) yalnızca KENDİ poliçelerine ve KENDİ hasar taleplerine erişebilir."*
  - `openapi.yaml` `GET /claims` (satır 126–129): *"`policyId` sorgu parametresi verilirse yalnızca o poliçeye ait talepler süzülür; ancak bu durumda da yetkilendirme kuralı geçerlidir: kullanıcı yalnızca KENDİSİNE ait poliçelerin taleplerini görebilir."*
- **Beklenen Davranış:** Normal kullanıcı başka bir kullanıcıya ait `policyId` ile `GET /claims?policyId=...` çağırdığında `403 Forbidden` (veya hiçbir kayıt sızdırmayan yetki reddi) dönmelidir; başka kullanıcının hasar kayıtları kesinlikle görüntülenmemelidir.
- **Gerçekleşen Davranış:** `u1` kullanıcısı `u2`'ye ait `pol_4` için sorgu yaptığında HTTP `200` ile `u2`'nin `clm_6` hasar talebi (tutar, açıklama, tarih ve sahip kimliği) döndürüldü. Ters yönde `u2` kullanıcısı da `u1`'in `pol_1` poliçesindeki `clm_1` ve `clm_2` taleplerini okuyabildi. (Not: Doğrudan `GET /claims/clm_6` çağrısı `403` ile doğru engellenirken yalnızca `GET /claims?policyId=...` filtresinde sahiplik kontrolü atlanmıştır.)
- **Tekrar Üretim Adımları:**
  1. `Authorization: Bearer tok_user1_ayse` (`u1`) başlığıyla `GET http://localhost:4106/claims?policyId=pol_4` isteği gönderin (`pol_4`, `u2` kullanıcısına aittir).
  2. **Gözlenen Yanıt (`C-010`):** HTTP `200`
     `{"data":[{"id":"clm_6","policyId":"pol_4","ownerUserId":"u2","amount":5000,"status":"approved","description":"Çarpma hasarı","createdAt":"2026-05-18T10:20:00Z"}],"meta":{"page":1,"pageSize":20,"total":1}}`
  3. Karşı doğrulama (`C-011`): `Authorization: Bearer tok_user2_mehmet` (`u2`) ile `GET http://localhost:4106/claims?policyId=pol_1` isteğinde HTTP `200` ve `u1`'in `clm_1`, `clm_2` kayıtları döner.
- **Not (şüphe):** `policyId` parametresi verildiğinde sorgu önce `ownerUserId` filtresi uygulamadan doğrudan `claims.filter(c => c.policyId === policyId)` çalıştırıyor olabilir.

---

### BUG-02 — `PATCH /policies/{id}` ve `POST /claims` uçlarına `null` JSON gövdesi gönderildiğinde sunucu çöküyor (DoS + veri kaybı)

- **Önem Derecesi:** Kritik (`OWASP ASVS V2 / V16`)
- **Tekrarlanabilirlik:** Kesin (Her denemede izole olarak doğrulandı: `M-004`, `E-025`, `E-026`, `N-004`, `N-007`)
- **Etkilenen Uçlar:** `PATCH /policies/{id}`, `POST /claims`
- **Bağlı Kanıtlar:** `test-kayitlari.md` → `M-004`, `E-024`–`E-027`, `N-001`, `N-004`–`N-009`
- **Sözleşme / İş Kuralı Atfı:** `openapi.yaml` `PATCH /policies/{id}` (`400 BadRequest`, satır 110–111) ve `POST /claims` (`400 BadRequest`, satır 196–197). Geçersiz istek gövdesi istemci hatası olarak HTTP `400` dönmeli, sunucu sürecini asla düşürmemelidir.
- **Beklenen Davranış:** Gövdesi JSON `null` olan bir `PATCH` veya `POST` isteği HTTP `400` (`Error` şeması) ile reddedilmeli ve sunucu kararlı biçimde çalışmaya devam etmelidir.
- **Gerçekleşen Davranış:** İstek gövdesine ham JSON `null` gönderildiğinde sunucu hiçbir HTTP yanıtı döndürmeden TCP bağlantısını sıfırlıyor (`ConnectionResetError 10054`), hemen ardından gelen istek reddediliyor (`ConnectionRefusedError 10061` — `E-027`) ve süreç yeniden başlatılıncaya kadar önceki bellek içi kayıtların tamamı siliniyor (`N-004` öncesi oluşturulan `clm_12` `N-005`'te `404` oluyor; `N-007` öncesi oluşturulan `clm_8` `N-008`'de `404` oluyor).
- **Tekrar Üretim Adımları:**
  1. Önce durum kalıcılığını gözlemek için `Authorization: Bearer tok_user1_ayse` ve `Content-Type: application/json` ile `POST http://localhost:4106/claims` gövdesine `{"policyId":"pol_1","amount":250,"description":"Test hasarı"}` gönderin (`N-001` → `200`, örn. `clm_12`).
  2. `Authorization: Bearer tok_user1_ayse` ve `Content-Type: application/json` ile `PATCH http://localhost:4106/policies/pol_1` isteğine ham gövde olarak `null` gönderin (`N-004`).
  3. **Gözlenen Yanıt (`N-004`):** HTTP yanıtı alınamadan bağlantı sıfırlanır (`ConnectionResetError(10054)`).
  4. 1.5 saniye sonra `GET http://localhost:4106/claims/clm_12` çağırın (`N-005`) → HTTP `404 {"error":"Bulunamadı","message":"Hasar talebi bulunamadı."}` (sunucunun çöküp yeniden başladığını kanıtlar).
  5. Aynı davranışı `POST http://localhost:4106/claims` gövdesine `null` göndererek tekrarlayın (`N-007` → bağlantı kopar, `N-008` → öncesinde oluşturulan kayıt `404` olur).
- **Not (şüphe):** `JSON.parse("null")` sonucu JavaScript'te `null` döndürür ve `typeof null === "object"` olduğu için obje kontrolü atlanıp `body.policyId` / `body.holderName` erişiminde işlenmeyen `TypeError` süreci çökertiyor olabilir (`[]` gövdesinde `M-003` ve `E-007` çökmemiştir).

---

### BUG-03 — `PATCH /policies/{id}` salt-okunur `status` alanının değiştirilmesine (Mass Assignment / BOPLA) ve geçersiz enum değerine izin veriyor

- **Önem Derecesi:** Kritik (`OWASP API3:2023 BOPLA` · `OWASP ASVS V15.3`)
- **Tekrarlanabilirlik:** Kesin (Her denemede)
- **Etkilenen Uç:** `PATCH /policies/{id}`
- **Bağlı Kanıtlar:** `test-kayitlari.md` → `PA-016`, `PA-017`, `PA-018`, `PA-019`, `E-003`, `E-004`
- **Sözleşme / İş Kuralı Atfı:**
  - `openapi.yaml` `PATCH /policies/{id}` (satır 93–98): *"Poliçe sahibi YALNIZCA `holderName` ve `agentName` alanlarını güncelleyebilir. `premium`, `coverageLimit`, `status`, `ownerUserId`, `policyNumber`, `coverageType` alanları salt okunurdur ve istek gövdesiyle DEĞİŞTİRİLEMEZ; bu alanlar gövdede gönderilse bile yok sayılmalıdır. Poliçenin durumu (`status`) yalnızca iç iş süreçleriyle değişir."*
  - `openapi.yaml` `Policy.status` (satır 335–337): `enum: [active, cancelled, expired, pending]`.
- **Beklenen Davranış:** İstek gövdesinde gönderilen `status` alanı (diğer salt-okunur alanlar gibi) yok sayılmalı (veya `PolicyUpdate` `additionalProperties: false` gereği `400` ile reddedilmeli) ve poliçenin durumu `"active"` olarak kalmalıdır.
- **Gerçekleşen Davranış:** `premium`, `coverageLimit`, `ownerUserId`, `policyNumber`, `coverageType`, `holderTckn`, `id`, `startDate`, `endDate` alanları yok sayılmasına karşın, `status` alanı gövdedeki değerle kalıcı olarak değiştirilmiştir. Poliçe sahibi kendi poliçesini `"cancelled"` durumuna alabilmekte, iptal edilmiş poliçeyi `"active"` yapabilmekte (`E-004`) ve hatta enum dışı `"invalid_enum"` değerini dahi kaydedebilmektedir (`E-003`).
- **Tekrar Üretim Adımları:**
  1. `Authorization: Bearer tok_user1_ayse` (`u1`) ve `Content-Type: application/json` ile `PATCH http://localhost:4106/policies/pol_1` isteğine `{"status": "cancelled"}` gönderin (`PA-018`).
  2. **Gözlenen Yanıt (`PA-018`):** HTTP `200`, yanıtta `"status":"cancelled"` döner.
  3. Ardından `GET http://localhost:4106/policies/pol_1` (`PA-017`/`PA-019`) ile sorgulayın → `"status":"cancelled"` kalıcı hale gelmiştir.
  4. `{"status": "invalid_enum"}` ile tekrarlayın (`E-003`) → HTTP `200`, yanıtta `"status":"invalid_enum"` döner.

---

### BUG-04 — `POST /claims` poliçe teminat limitini (`coverageLimit`) aşan tutarları `422` ile reddetmiyor

- **Önem Derecesi:** Kritik (Finansal iş kuralı ihlali)
- **Tekrarlanabilirlik:** Kesin (Tüm sınır üstü denemelerde)
- **Etkilenen Uç:** `POST /claims`
- **Bağlı Kanıtlar:** `test-kayitlari.md` → `PC-020`, `PC-021`, `PC-022` (geçerli sınır), `ID-005`, `X-010`
- **Sözleşme / İş Kuralı Atfı:** `openapi.yaml` `POST /claims` (satır 171–173 & 202–206): *"İş kuralı: Bir hasar talebinin tutarı (`amount`), ilgili poliçenin teminat limitini (`coverageLimit`) AŞAMAZ. Aşan istekler 422 ile reddedilmelidir."*
- **Beklenen Davranış:** `pol_5` poliçesinin `coverageLimit` değeri `75000` TL'dir. `amount: 75000` kabul edilmeli (`201`), ancak `amount: 75000.01`, `amount: 75001` veya `pol_1` (`coverageLimit: 50000`) için `amount: 999999` istekleri HTTP `422` (`Error`) ile reddedilmelidir.
- **Gerçekleşen Davranış:** Tam limit `75000` kabul edildiği gibi (`PC-022`), limiti aşan `75000.01` (`PC-021`), `75001` (`PC-020`), `999999` (`ID-005`) ve hatta `1e+308` (`X-010`) tutarlarının tamamı HTTP `200` ile onaylanıp yeni hasar talebi olarak kaydedildi.
- **Tekrar Üretim Adımları:**
  1. Sınırın geçerli tarafı (`PC-022`): `tok_user1_ayse` ile `POST http://localhost:4106/claims` gövdesi `{"policyId": "pol_5", "amount": 75000, "description": "Tam limit"}` → `200` (`clm_17`, kabul edilmeliydi—ancak kod 201 olmalı).
  2. Sınırın 0,01 TL üstü (`PC-021`): `tok_user1_ayse` ile `POST http://localhost:4106/claims` gövdesi `{"policyId": "pol_5", "amount": 75000.01}` gönderin.
  3. **Gözlenen Yanıt (`PC-021`):** HTTP `200` `{"id":"clm_16","policyId":"pol_5","ownerUserId":"u1","amount":75000.01,"status":"submitted","description":"","createdAt":"2026-08-01T00:00:00Z"}`
  4. Sınırın 1 TL üstü (`PC-020`): `{"policyId": "pol_5", "amount": 75001}` → HTTP `200` (`clm_15`).

---

### BUG-05 — `GET /admin/stats` yönetici ucuna normal kullanıcılar erişebiliyor (BFLA)

- **Önem Derecesi:** Kritik (`OWASP API5:2023 BFLA` · `OWASP ASVS V8`)
- **Tekrarlanabilirlik:** Kesin (Her iki normal kullanıcıda da doğrulandı)
- **Etkilenen Uç:** `GET /admin/stats`
- **Bağlı Kanıtlar:** `test-kayitlari.md` → `AD-006`, `AD-007` (karşılaştırma için `AD-002`, `AD-003`)
- **Sözleşme / İş Kuralı Atfı:** `openapi.yaml` (satır 15, 27 ve 258–260): *"Sistem genel istatistiklerini döner. Yalnızca role=admin erişebilir; normal kullanıcı için 403 dönülmelidir."*
- **Beklenen Davranış:** `u1` (`tok_user1_ayse`) ve `u2` (`tok_user2_mehmet`) gibi normal kullanıcılar (`role=user`) `GET /admin/stats` çağırdığında `GET /admin/policies` ucunda olduğu gibi HTTP `403` dönmelidir.
- **Gerçekleşen Davranış:** Hem `u1` hem de `u2` kullanıcılarına HTTP `200` ile tüm sistemdeki toplam poliçe sayısı, toplam hasar talebi sayısı ve toplam prim tutarı döndürülmektedir.
- **Tekrar Üretim Adımları:**
  1. `Authorization: Bearer tok_user1_ayse` (`u1`) başlığıyla `GET http://localhost:4106/admin/stats` isteği gönderin (`AD-006`).
  2. **Gözlenen Yanıt (`AD-006`):** HTTP `200` `{"totalPolicies":5,"totalClaims":7,"totalPremium":9800}`
  3. Aynı sonuç `tok_user2_mehmet` (`u2`) ile de alınır (`AD-007`).

---

### BUG-06 — `POST /claims` `Idempotency-Key` başlığını yok sayıyor ve mükerrer kayıt oluşturuyor

- **Önem Derecesi:** Yüksek
- **Tekrarlanabilirlik:** Kesin (Ardışık, farklı başlık harf duyarlılığı ve paralel eşzamanlı isteklerde doğrulandı)
- **Etkilenen Uç:** `POST /claims` (`Idempotency-Key` başlığı)
- **Bağlı Kanıtlar:** `test-kayitlari.md` → `ID-001`, `ID-002`, `ID-RACE-1`, `ID-RACE-2`, `E-001`, `E-002`
- **Sözleşme / İş Kuralı Atfı:** `openapi.yaml` `POST /claims` (satır 176–184): *"İstek `Idempotency-Key` başlığı ile gönderilirse, aynı anahtarla yapılan tekrar istekleri YENİ kayıt OLUŞTURMAMALI, ilk oluşturulan kaydı aynen döndürmelidir."*
- **Beklenen Davranış:** Aynı `Idempotency-Key` başlığıyla tekrarlanan (veya eşzamanlı gönderilen) istekler yeni kayıt oluşturmamalı, ilk üretilen hasar talebini (`id` dahil aynen) döndürmelidir.
- **Gerçekleşen Davranış:** Aynı `Idempotency-Key` değeriyle art arda iki istek atıldığında (`ID-001` → `clm_22`, `ID-002` → `clm_23`), ham HTTP başlık harf biçimi tam `Idempotency-Key` olarak korunduğunda (`E-001` → `clm_30`, `E-002` → `clm_31`) ve iki eşzamanlı istekte (`ID-RACE-1` → `clm_28`, `ID-RACE-2` → `clm_29`) her defasında ayrı, yeni bir hasar kaydı oluşturuldu.
- **Tekrar Üretim Adımları:**
  1. `Authorization: Bearer tok_user1_ayse`, `Content-Type: application/json`, `Idempotency-Key: exact-case-key-1` başlıklarıyla `POST http://localhost:4106/claims` gövdesi `{"policyId": "pol_2", "amount": 77, "description": "Exact header 1"}` gönderin (`E-001` → `id: "clm_30"`).
  2. Birebir aynı isteği aynı `Idempotency-Key: exact-case-key-1` ile tekrar gönderin (`E-002`).
  3. **Gözlenen Yanıt (`E-002`):** HTTP `200`, farklı bir kayıt üretilir: `{"id":"clm_31","policyId":"pol_2","ownerUserId":"u1","amount":77,"status":"submitted","description":"Exact header 1","createdAt":"2026-08-01T00:00:00Z"}`

---

### BUG-07 — `POST /claims` `amount` alt sınırını (`minimum: 1`) doğrulamıyor; `0`, negatif ve `1`'den küçük değerleri kabul ediyor

- **Önem Derecesi:** Yüksek
- **Tekrarlanabilirlik:** Kesin
- **Etkilenen Uç:** `POST /claims`
- **Bağlı Kanıtlar:** `test-kayitlari.md` → `PC-015`, `PC-016`, `PC-017`, `PC-018`, `PC-019` (geçerli sınır)
- **Sözleşme / İş Kuralı Atfı:** `openapi.yaml` `Claim.amount` (satır 373–375) ve `ClaimCreate.amount` (satır 387–390): `minimum: 1`, *"Talep edilen tutar (TL). 1'den küçük olamaz"*.
- **Beklenen Davranış:** `amount = 1` kabul edilmeli; `0.99`, `0.5`, `0` ve `-50` değerleri `400` veya `422` ile reddedilmelidir.
- **Gerçekleşen Davranış:** `amount = 1` (`PC-019`) yanında `0.99` (`clm_12`), `0.5` (`clm_13`), `0` (`clm_10`) ve negatif `-50` (`clm_11`) değerlerinin tamamı HTTP `200` ile kabul edilerek hasar kaydı oluşturuldu.
- **Tekrar Üretim Adımları:**
  1. Sınırın geçerli tarafı (`PC-019`): `tok_user1_ayse` ile `POST /claims` `{"policyId": "pol_1", "amount": 1}` → HTTP `200` (`clm_14`).
  2. Sınırın hemen altı (`PC-017`): `{"policyId": "pol_1", "amount": 0.99}` → HTTP `200` (`clm_12`).
  3. Sıfır ve negatif (`PC-015`, `PC-016`): `{"policyId": "pol_1", "amount": 0}` → `clm_10`; `{"policyId": "pol_1", "amount": -50}` → HTTP `200` `{"id":"clm_11","policyId":"pol_1","ownerUserId":"u1","amount":-50,...}`.

---

### BUG-08 — Geçersiz JSON hatası dahili sunucu dosya yolunu ve stack trace bilgisini sızdırıyor

- **Önem Derecesi:** Yüksek (`OWASP ASVS V16` · `CWE-209`)
- **Tekrarlanabilirlik:** Kesin (`M-001`, `M-005`)
- **Etkilenen Uçlar:** `POST /claims`, `PATCH /policies/{id}`
- **Bağlı Kanıtlar:** `test-kayitlari.md` → `M-001`, `M-005`
- **Sözleşme / İş Kuralı Atfı:** `openapi.yaml` `Error` şeması (satır 403–408: yalnızca `error` ve `message` alanları) ve güvenli hata yönetimi ilkesi (istemciye yığın izi, iç dosya yolu veya çalışma zamanı ayrıntısı dönülmemelidir).
- **Beklenen Davranış:** Bozuk JSON gövdesi gönderildiğinde HTTP `400` ile yalnızca `{ "error": "...", "message": "..." }` döndürülmeli; sunucu dosya yolları ve `stack` bilgisi yer almamalıdır.
- **Gerçekleşen Davranış:** `{bad json` gövdesine verilen `400` yanıtında `"detail"` ve `"stack"` alanlarıyla Node.js `SyntaxError` yığın izi, sunucu kaynak dosya yolu (`C:\...\servers\R11\server.js`) ve satır numaraları (`216:25`, `155:27`) döndürülüyor.
- **Tekrar Üretim Adımları:**
  1. `Authorization: Bearer tok_user1_ayse` ve `Content-Type: application/json` başlıklarıyla `POST http://localhost:4106/claims` isteğine ham `{bad json` gövdesi gönderin (`M-001`).
  2. **Gözlenen Yanıt (`M-001`):** HTTP `400`
     `{"error":"Geçersiz JSON","detail":"Expected property name or '}' in JSON at position 1 (line 1 column 2)","stack":"SyntaxError: Expected property name or '}' in JSON at position 1 (line 1 column 2)\n    at JSON.parse (<anonymous>)\n    at Server.<anonymous> (C:\\eval\\servers\\R11\\server.js:216:25)\n    at process.processTicksAndRejections (node:internal/process/task_queues:104:5)"}`
  3. Aynı davranış `PATCH /policies/pol_1` ucunda da görülür (`M-005`, `server.js:155:27`).

---

### BUG-09 — `GET /claims` yanıtındaki `meta.total` tüm sayfalardaki toplamı değil yalnızca mevcut sayfa eleman sayısını dönüyor

- **Önem Derecesi:** Yüksek (Sayfalama arayüzü ve toplam sayfa hesaplaması tamamen bozulur)
- **Tekrarlanabilirlik:** Kesin
- **Etkilenen Uç:** `GET /claims`
- **Bağlı Kanıtlar:** `test-kayitlari.md` → `C-001`, `C-005`, `C-006`, `C-007`, `C-008`, `X-013`, `X-014`
- **Sözleşme / İş Kuralı Atfı:**
  - `openapi.yaml` `GET /claims` (satır 132–134): *"Yanıttaki `meta.total` alanı, sayfalama uygulanmadan önceki TOPLAM (tüm sayfalardaki) kayıt sayısını belirtir; yalnızca geçerli sayfadaki kayıt sayısını değil."*
  - `openapi.yaml` `PageMeta.total` (satır 400–402).
- **Beklenen Davranış:** `u1` kullanıcısının 5 hasar talebi varken `pageSize=2` ile istenen tüm sayfalarda (`page=1`, `page=2`, `page=3`, `page=4`) `meta.total` değeri `5` olmalıdır.
- **Gerçekleşen Davranış:** `meta.total` her sayfada yalnızca o sayfadaki `data.length` değerini dönmektedir (`page=1` → `2`, `page=2` → `2`, `page=3` → `1`, `page=4` → `0`).
- **Tekrar Üretim Adımları:**
  1. `tok_user1_ayse` ile `GET http://localhost:4106/claims` çağırın (`C-001`) → 5 talep olduğu doğrulanır (`meta.total: 5`).
  2. `GET http://localhost:4106/claims?page=1&pageSize=2` (`C-005`) → 2 kayıt döner, `meta: {"page":1,"pageSize":2,"total":2}` (beklenen `total: 5`).
  3. `GET http://localhost:4106/claims?page=3&pageSize=2` (`C-007`) → 1 kayıt döner, `meta: {"page":3,"pageSize":2,"total":1}` (beklenen `total: 5`).
  4. `GET http://localhost:4106/claims?page=4&pageSize=2` (`C-008`) → 0 kayıt döner, `meta: {"page":4,"pageSize":2,"total":0}` (beklenen `total: 5`).

---

### BUG-10 — Tüm `Claim` yanıtlarında zorunlu `claimNumber` alanı eksik

- **Önem Derecesi:** Orta
- **Tekrarlanabilirlik:** Kesin (Mevcut ve yeni oluşturulan tüm kayıtlarda)
- **Etkilenen Uçlar:** `GET /claims`, `GET /claims/{id}`, `POST /claims`
- **Bağlı Kanıtlar:** `test-kayitlari.md` → `C-001`–`C-003`, `C-005`–`C-007`, `C-009`, `CD-001`, `CD-004`, `PC-019`, `PC-022`
- **Sözleşme / İş Kuralı Atfı:** `openapi.yaml` `Claim` şeması (satır 354–369): `required: [id, claimNumber, policyId, ownerUserId, amount, status, createdAt]`, `claimNumber: { type: string, examples: ['CLM-2026-0001'] }`.
- **Beklenen Davranış:** `Claim` nesnesi dönen tüm uçlarda her kaydın `claimNumber` alanına (ör. `CLM-2026-0001`) sahip olması gerekir.
- **Gerçekleşen Davranış:** Hem başlangıçtaki hazır kayıtlarda (`clm_1..clm_7`) hem de `POST /claims` ile yeni oluşturulan kayıtlarda `claimNumber` alanı hiç dönmemektedir. Otomatik şema doğrulayıcı `$.claimNumber: required property missing` hatası üretmiştir.
- **Tekrar Üretim Adımları:**
  1. `tok_user1_ayse` ile `GET http://localhost:4106/claims/clm_1` isteği gönderin (`CD-001`).
  2. **Gözlenen Yanıt (`CD-001`):** HTTP `200` `{"id":"clm_1","policyId":"pol_1","ownerUserId":"u1","amount":12000,"status":"submitted","description":"Çarpma hasarı","createdAt":"2026-05-02T09:00:00Z"}` (`claimNumber` yok).

---

### BUG-11 — `POST /claims` yeni kayıt oluşturduğunda HTTP `201` yerine `200` dönüyor

- **Önem Derecesi:** Orta
- **Tekrarlanabilirlik:** Kesin (Tüm başarılı `POST /claims` çağrılarında)
- **Etkilenen Uç:** `POST /claims`
- **Bağlı Kanıtlar:** `test-kayitlari.md` → `PC-019`, `PC-022`, `PC-024`, `ID-001`, `X-012`
- **Sözleşme / İş Kuralı Atfı:** `openapi.yaml` `POST /claims` (satır 190–195): `'201': description: Oluşturulan hasar talebi`.
- **Beklenen Davranış:** Yeni hasar talebi oluşturulduğunda HTTP `201` durum kodu dönmelidir.
- **Gerçekleşen Davranış:** Tüm başarılı `POST /claims` istekleri HTTP `200` dönmektedir (`201` bekleyen istemci ve sözleşme testleri başarısız olmaktadır).
- **Tekrar Üretim Adımları:**
  1. `tok_user1_ayse` ve `Content-Type: application/json` ile `POST http://localhost:4106/claims` gövdesi `{"policyId": "pol_1", "amount": 50, "description": "UTF-8 başlık testi"}` gönderin (`X-012`).
  2. **Gözlenen Yanıt (`X-012`):** HTTP `200` (beklenen `201`).

---

### BUG-12 — `PATCH /policies/{id}` `holderName` ve `agentName` alanlarında tip ve boş değer doğrulaması yapmıyor

- **Önem Derecesi:** Orta
- **Tekrarlanabilirlik:** Kesin
- **Etkilenen Uç:** `PATCH /policies/{id}`
- **Bağlı Kanıtlar:** `test-kayitlari.md` → `PA-011`, `PA-012`, `PA-013`, `PA-014`, `PA-015`, `X-003`, `X-004`, `X-005`
- **Sözleşme / İş Kuralı Atfı:**
  - `openapi.yaml` `Policy` ve `PolicyUpdate` şemaları (satır 322, 338–339, 351–352): `holderName: { type: string }` (null olamaz), `agentName: { type: ['string', 'null'] }`.
  - `PATCH /policies/{id}` `'400'` yanıtı (satır 110–111).
- **Beklenen Davranış:** `holderName` için sayı (`12345`), `null`, boolean (`true`), nesne (`{}`) veya `agentName` için sayı (`12345`), dizi (`[]`) gibi yanlış tipteki değerler HTTP `400` ile reddedilmelidir. Ayrıca `holderName` için boş/yalnız boşluk (`""`, `"   "`) reddedilmelidir.
- **Gerçekleşen Davranış:** Gönderilen tüm yanlış tipler ve boş stringler HTTP `200` ile kabul edilip poliçe kaydına kalıcı olarak yazılmaktadır. Bu durum sonraki `GET /policies/{id}` yanıtının da `Policy` şemasını bozmasına yol açar.
- **Tekrar Üretim Adımları:**
  1. `tok_user1_ayse` ve `Content-Type: application/json` ile `PATCH http://localhost:4106/policies/pol_1` gövdesi `{"holderName": 12345}` gönderin (`PA-011`) → HTTP `200`, `"holderName":12345` kaydedilir.
  2. `{"holderName": null}` (`PA-012`) → HTTP `200`, `"holderName":null`.
  3. `{"holderName": true}` (`X-003`) → HTTP `200`, `"holderName":true`.
  4. `{"agentName": 12345}` (`PA-015`) → HTTP `200`, `"agentName":12345`.
  5. `{"holderName": ""}` (`PA-013`) ve `{"holderName": "   "}` (`PA-014`) → HTTP `200`.

---

### BUG-13 — `GET /claims` geçersiz sayfalama parametrelerini `200` ile kabul ediyor ve şema dışı `null` `meta` dönüyor

- **Önem Derecesi:** Orta
- **Tekrarlanabilirlik:** Kesin
- **Etkilenen Uç:** `GET /claims` (`page`, `pageSize`)
- **Bağlı Kanıtlar:** `test-kayitlari.md` → `C-012`, `C-013`, `C-014`, `C-015`, `C-016`, `E-018`
- **Sözleşme / İş Kuralı Atfı:**
  - `openapi.yaml` `GET /claims` parametreleri (satır 140–147): `page` (`type: integer, minimum: 1`), `pageSize` (`type: integer, minimum: 1, maximum: 100`).
  - `openapi.yaml` `PageMeta` (satır 394–402): `page: { type: integer }`, `pageSize: { type: integer }` (`null` olamaz).
- **Beklenen Davranış:** Sınır dışı (`page=0`, `page=-1`, `pageSize=0`, `pageSize=101`) veya tamsayı olmayan (`page=abc`, `page=1.5`) parametreler `400` ile reddedilmelidir (veya üst sınır kırpılıp geçerli tamsayı dönülmelidir; hiçbir durumda `meta.page: null` dönülmemelidir).
- **Gerçekleşen Davranış:** Tüm geçersiz sayfalama değerleri HTTP `200` ile kabul edilmektedir. Özellikle `page=abc&pageSize=xyz` gönderildiğinde `meta: {"page":null,"pageSize":null,"total":0}` dönerek `PageMeta` şemasını bozmakta; `pageSize=101` ise 100 üst sınırını aşmaktadır.
- **Tekrar Üretim Adımları:**
  1. `tok_user1_ayse` ile `GET http://localhost:4106/claims?page=abc&pageSize=xyz` isteği gönderin (`C-016`).
  2. **Gözlenen Yanıt (`C-016`):** HTTP `200` `{"data":[],"meta":{"page":null,"pageSize":null,"total":0}}`
  3. `GET http://localhost:4106/claims?page=0&pageSize=20` (`C-012`) → HTTP `200` `{"data":[],"meta":{"page":0,"pageSize":20,"total":0}}`
  4. `GET http://localhost:4106/claims?pageSize=101` (`C-015`) → HTTP `200`, `meta.pageSize: 101`.

---

### BUG-14 — `POST /claims` giriş doğrulama tutarsızlıkları (`description` sessizce sıfırlanıyor, `policyId` yanlış tipte `404` dönüyor, ek alanlar reddedilmiyor)

- **Önem Derecesi:** Orta
- **Tekrarlanabilirlik:** Kesin
- **Etkilenen Uç:** `POST /claims`
- **Bağlı Kanıtlar:** `test-kayitlari.md` → `PC-009`, `PC-014`, `PC-024`, `PC-026`, `E-014`, `X-011`
- **Sözleşme / İş Kuralı Atfı:** `openapi.yaml` `ClaimCreate` (satır 382–393): `policyId: { type: string }`, `description: { type: ['string', 'null'] }`, `additionalProperties: false`; `Claim.description` (satır 379–380).
- **Beklenen Davranış:**
  - `description: 12345` veya `["x"]` yanlış tipleri `400` ile reddedilmeli (sessizce `""` yapılmamalı);
  - `policyId: 12345` veya `["pol_1"]` tip hatası olarak `400` dönmeli (`404` değil);
  - `ClaimCreate` `additionalProperties: false` kuralına göre tanımsız ek alanlar (`extraProp`, `role` vb.) `400` ile reddedilmelidir (`description: null` gönderildiğinde de `null` korunmalı veya tutarlı davranılmalıdır).
- **Gerçekleşen Davranış:**
  - `description: 12345` (`PC-014`) ve `description: ["x"]` (`X-011`) HTTP `200` ile kabul edilip sessizce `description: ""` olarak kaydedildi; `description: null` (`PC-024`) da `""` oldu.
  - `policyId: 12345` (`PC-009`) ve `policyId: ["pol_1"]` (`E-014`) tip hatası (`400`) yerine `404 {"error":"Bulunamadı","message":"Poliçe bulunamadı."}` döndü.
  - Bilinmeyen ek alanlar (`PC-026`: `extraProp`, `role` vb.) `400` ile reddedilmedi (neyse ki salt-okunur `id`, `status`, `ownerUserId` değerleri üzerine yazılmadı).
- **Tekrar Üretim Adımları:**
  1. `tok_user1_ayse` ve `Content-Type: application/json` ile `POST /claims` gövdesi `{"policyId": "pol_1", "amount": 100, "description": 12345}` gönderin (`PC-014`) → HTTP `200`, `"description":""`.
  2. `{"policyId": 12345, "amount": 100}` gönderin (`PC-009`) → HTTP `404`.
  3. `{"policyId": "pol_1", "amount": 50, "extraProp": "abc"}` gönderin (`PC-026`) → HTTP `200`.

---

### BUG-15 — `openapi.yaml` sözleşme çelişkisi ve dokümantasyon eksikleri (Sözleşme Kusuru)

- **Önem Derecesi:** Düşük (Sözleşme / Dokümantasyon Kusuru)
- **Tekrarlanabilirlik:** Kesin (`openapi.yaml` incelemesi + `openapi_tests.py` + `X-002`)
- **Etkilenen Alan:** `openapi.yaml` (`PolicyUpdate`, `GET /claims`, `PATCH /policies/{id}`, `POST /claims`)
- **Sözleşme Atfı:**
  1. `PATCH /policies/{id}` açıklaması (satır 96–97: *"bu alanlar gövdede gönderilse bile yok sayılmalıdır"*) ve `PolicyUpdate` açıklaması (satır 348–349: *"Diğer alanlar gönderilse de yok sayılır"*) ile `PolicyUpdate.additionalProperties: false` (satır 353) doğrudan çelişmektedir. `X-002` testinde sunucu `extraField` gönderimini `200` ile yok saymıştır.
  2. `GET /claims` uç noktasında `page` / `pageSize` doğrulama hataları için `'400'` yanıtı dokümante edilmemiştir.
  3. `PATCH /policies/{id}` (`holderName`) ve `POST /claims` (`policyId`, `description`) alanlarında `minLength`/`maxLength`/`pattern` kısıtları tanımlanmamış; `amount` için genel üst sınır (`maximum`) ve yol parametreleri (`{id}`) için `example` eklenmemiştir (`openapi_tests.py` sözleşme taramasında 5 soru olarak saptanmıştır).
- **Beklenen Davranış:** Sözleşme açıklamaları JSON Schema kurallarıyla çelişmemeli; hata yanıt kodları ve alan kısıtları eksiksiz dokümante edilmelidir.

---

## Sözleşme Dışı Açık İş Soruları ve Kapsam Notları

Aşağıdaki gözlemler `openapi.yaml` içinde açıkça yasaklanmadığı veya test ortamına özgü olabileceği için **kesin hata (bug)** olarak değil, ürün/geliştirme ekibinin netleştirmesi gereken **açık sorular** olarak raporlanmıştır:

1. **İptal edilmiş (`cancelled`) poliçeye hasar talebi açılabilmesi (`PC-023`):** `u2` kullanıcısı `status: "cancelled"` durumundaki `pol_3` poliçesi için `POST /claims` ile `500` TL'lik yeni hasar talebi (`clm_18`) açabilmiştir (başlangıç verisinde de `pol_3` üzerinde `clm_7` mevcuttur). Sözleşme iptal/süresi dolmuş poliçelerde talebin reddedileceğine dair kural içermiyor; ürün ekibi `cancelled`/`expired`/`pending` poliçelerde `422` dönülüp dönülmeyeceğini netleştirmelidir. (Ayrıca poliçe bazında **kümülatif** hasar toplamı mı yoksa tekil talep tutarı mı `coverageLimit` ile kıyaslanacak?)
2. **Yöneticinin (`admin`) başka kullanıcının poliçesine hasar talebi açması (`E-015`):** `admin` token'ıyla `u1`'in `pol_1` poliçesine `POST /claims` atıldığında kayıt `ownerUserId: "admin"` olarak oluşmuştur (`clm_32`). Yönetici adına açılan taleplerde `ownerUserId` poliçe sahibi (`u1`) mi olmalı, yoksa admin'in doğrudan talep açması engellenmeli mi?
3. **Uzun metinler ve `PATCH` boş gövde (`X-007`, `X-009`, `PA-010`):** `holderName` için 5.000 karakter (`X-007`), `description` için 10.000 karakter (`X-009`) ve `PATCH /policies/{id}` için boş `{}` gövde (`PA-010`) kabul edilmektedir. Üretim ortamı için makul uzunluk üst sınırları (`maxLength`) belirlenmelidir.
4. **Hata/İstek ayrıntıları (`M-006`, `X-015`, `createdAt`):**
   - `POST /claims` `Content-Type: text/plain` başlığıyla gönderilen JSON metnini de kabul etmektedir (`M-006`).
   - `POST /health` kimlik bilgisi olmadan `405` yerine `401` dönmektedir (`X-015`).
   - Yeni oluşturulan tüm hasar taleplerinde `createdAt` alanı sabit `"2026-08-01T00:00:00Z"` dönmektedir (test sunucusundaki sabit saat kurgusundan kaynaklanıyor olabilir; canlı ortamda gerçek sunucu zamanı doğrulanmalıdır).
5. **Kapsanmayan Alanlar:** Yük/performans testi ve oran sınırlama (rate limiting / `429`) testleri kapsam dışı bırakılmıştır.
