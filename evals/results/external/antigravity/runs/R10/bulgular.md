# Kusur Raporu (`bulgular.md`) — Anadolu Güven Sigorta Poliçe & Hasar API

**Ortam:** Test sunucusu (`http://localhost:4105` / `127.0.0.1:4105`) · **Referans Sözleşme:** `openapi.yaml` (v1.0.0) · **Kanıt Günlüğü:** [`test-kayitlari.md`](./test-kayitlari.md)
**Test Hesapları (Sentetik):** `tok_user1_ayse` (`u1`, normal kullanıcı), `tok_user2_mehmet` (`u2`, normal kullanıcı), `tok_admin_root` (`admin`, yönetici)
**Raporlayan:** Bağımsız Kıdemli QA Mühendisi · **Durum:** Açık

---

## Özet Tablo ve Yayın Hazırlığı Değerlendirmesi

Toplam **193** sözleşme, yetkilendirme, iş kuralı ve sınır/hata testi sonucunda **16 benzersiz kök nedenli kusur** (15 uygulama kusuru, 1 sözleşme dokümantasyonu kusuru) doğrulanmıştır:

| Önem Derecesi | Adet | Bulgular |
|---|---|---|
| **Kritik** | 4 | `BLG-01`, `BLG-02`, `BLG-03`, `BLG-04` |
| **Yüksek** | 5 | `BLG-05`, `BLG-06`, `BLG-07`, `BLG-08`, `BLG-09` |
| **Orta** | 6 | `BLG-10`, `BLG-11`, `BLG-12`, `BLG-13`, `BLG-14`, `BLG-15` |
| **Düşük (Sözleşme)** | 1 | `BLG-16` |

### Risk ve Yayın Değerlendirmesi (Paydaş Kararı İçin)
- **Kritik Riskler:** Kimliği doğrulanmış herhangi bir normal kullanıcı tek bir `null` JSON gövdesiyle tüm API sürecini çökertebilmekte (`BLG-01`), `GET /claims?policyId=...` filtresiyle diğer müşterilerin hasar taleplerini okuyabilmekte (`BLG-02`), `GET /admin/stats` ile yalnızca yöneticiye açık şirket genel metriklerine erişebilmekte (`BLG-03`) ve `PATCH /policies/{id}` ile salt okunur poliçe durumunu (`status`) keyfi olarak değiştirebilmektedir (`BLG-04`).
- **İş Kuralı ve Veri Bütünlüğü Riskleri:** Teminat limiti üstü (`BLG-05`) ve 1 TL altı/negatif (`BLG-06`) hasar talepleri kabul edilmekte, `Idempotency-Key` tekrar koruması çalışmamakta (`BLG-07`), iptal poliçeye hasar açılabilmekte (`BLG-09`) ve bozuk JSON isteklerinde sunucu dosya yolu ile stack trace dışarı sızmaktadır (`BLG-08`).
- **Öneri (Seçenekler):** Canlıya çıkışın en azından Kritik (`BLG-01`–`BLG-04`) ve Yüksek (`BLG-05`–`BLG-09`) bulgular giderilip yeniden test edilene kadar bekletilmesi önerilir; mevcut haliyle canlıya çıkılacaksa ürün/güvenlik sorumlularının yazılı risk kabulü gerekir.

---

## Kritik Bulgular

### BLG-01 — JSON `null` gövdesi `POST /claims` ve `PATCH /policies/{id}` uçlarında sunucuyu çökertiyor
- **Önem Derecesi:** Kritik (Öncelik: Acil — Hizmet Kesintisi / DoS)
- **Etkilenen Uçlar:** `POST /claims`, `PATCH /policies/{id}`
- **Sözleşme / İş Kuralı Atfı:** `openapi.yaml` — `POST /claims` (`requestBody` → `ClaimCreate` nesnesi, hatalı girişte `400 Bad Request`), `PATCH /policies/{id}` (`requestBody` → `PolicyUpdate` nesnesi, hatalı girişte `400 Bad Request`). Sunucu geçersiz/beklenmeyen tipte bir JSON gövdesinde asla çökmemelidir.
- **Beklenen Davranış:** Gövde olarak JSON `null` gönderildiğinde API süreci çalışmaya devam etmeli ve `400 Bad Request` (`Error` şeması) döndürmelidir.
- **Gerçekleşen Davranış:** Geçerli bir JSON değeri olan `null` gönderildiğinde sunucu yanıt döndürmeden TCP bağlantısını zorla kapatıyor (`ConnectionResetError(10054)`), hemen ardından gelen istekler sunucu yeniden başlayana kadar reddediliyor (`ConnectionRefusedError(10061)`) ve bellek içi tüm test verileri başlangıç durumuna sıfırlanıyor. (Karşılaştırma: `[]`, `123`, `"hello"`, `true` kök JSON değerleri sunucuyu çökertmemektedir.)
- **Tekrar Üretim Adımları:**
  1. **Senaryo A (`POST /claims`):**
     - İstek: `POST http://localhost:4105/claims`
     - Başlıklar: `Authorization: Bearer tok_user1_ayse`, `Content-Type: application/json`
     - Gövde: `null`
     - Gözlenen Yanıt: Yanıt dönmeden bağlantı kopar (`ConnectionResetError(10054)` / `Empty reply from server`), sunucu yeniden başlar.
  2. **Senaryo B (`PATCH /policies/{id}`):**
     - İstek: `PATCH http://localhost:4105/policies/pol_2`
     - Başlıklar: `Authorization: Bearer tok_user1_ayse`, `Content-Type: application/json`
     - Gövde: `null`
     - Gözlenen Yanıt: Yanıt dönmeden bağlantı kopar (`ConnectionResetError(10054)`), sunucu yeniden başlar.
- **Tekrarlanabilirlik:** 4/4 (her iki uçta 2'şer kez bağımsız olarak doğrulandı).
- **Kanıt ID (`test-kayitlari.md`):** `EDG-01`, `EDG-06`, `VER-09`, `VER-10` (karşılaştırma: `VER-04`–`VER-08`).
- **Not (Şüphe):** `JSON.parse("null")` sonucu dönen `null` değeri üzerinde `typeof body === 'object'` kontrolünün `null` için de `true` dönmesi nedeniyle özellik erişimi (`body.policyId` / `body.holderName`) yakalanmayan `TypeError` fırlatıyor olabilir.

---

### BLG-02 — `GET /claims?policyId=...` filtresi sahip kontrolü yapmıyor; başka kullanıcının hasarları sızıyor (BOLA)
- **Önem Derecesi:** Kritik (Öncelik: Acil — Yatay Yetki Aşımı / Veri Sızıntısı)
- **Etkilenen Uç:** `GET /claims` (`policyId` sorgu parametresi)
- **Sözleşme / İş Kuralı Atfı:** `openapi.yaml` (`info.description` satır 13–14 ve `GET /claims` satır 125–129): *"`policyId` sorgu parametresi verilirse yalnızca o poliçeye ait talepler süzülür; ancak bu durumda da yetkilendirme kuralı geçerlidir: kullanıcı yalnızca KENDİSİNE ait poliçelerin taleplerini görebilir."*
- **Beklenen Davranış:** Normal bir kullanıcı kendisine ait olmayan bir `policyId` ile sorgulama yaptığında `403 Forbidden` (veya boş yetkili liste) dönmeli; başka kullanıcıya ait hasar kayıtları kesinlikle döndürülmemelidir.
- **Gerçekleşen Davranış:** `policyId` parametresi verildiğinde kullanıcının sahipliği kontrol edilmiyor; bir normal kullanıcı başka bir kullanıcının `policyId` kimliğini tahmin ederek/bilerek o poliçeye ait tüm hasar taleplerini `200 OK` ile okuyabiliyor. Ayrıca yönetici tarafından `pol_1` üzerine açılan ve `ownerUserId: "admin"` olan `clm_10` kaydı `GET /claims/clm_10` ucunda `u1`'e `403` verirken `GET /claims?policyId=pol_1` üzerinden `u1`'e dönmektedir.
- **Tekrar Üretim Adımları:**
  1. İstek: `GET http://localhost:4105/claims?policyId=pol_4`
  2. Token: `Authorization: Bearer tok_user1_ayse` (`u1`, Ayşe Yılmaz — `pol_4` ise `u2` Mehmet Demir'e aittir)
  3. Gözlenen Yanıt: HTTP **200**
     ```json
     {"data":[{"id":"clm_6","policyId":"pol_4","ownerUserId":"u2","amount":5000,"status":"approved","description":"Çarpma hasarı","createdAt":"2026-05-18T10:20:00Z"}],"meta":{"page":1,"pageSize":20,"total":1}}
     ```
  4. Ters yön doğrulama (`u2` token'ı `tok_user2_mehmet` ile `GET /claims?policyId=pol_1`): HTTP **200** ile `u1`'in `clm_1` ve `clm_2` kayıtları döner.
- **Tekrarlanabilirlik:** Her zaman.
- **Kanıt ID (`test-kayitlari.md`):** `RO-39`, `RO-40`, `RO-41`, `VER-02`, `VER-03` (karşılaştırma: `RO-15`, `RO-16`, `RO-47` uçları `403` dönmektedir).

---

### BLG-03 — `GET /admin/stats` yönetici rolü kontrolü yapmıyor; normal kullanıcılar erişebiliyor (BFLA)
- **Önem Derecesi:** Kritik (Öncelik: Acil — Dikey Yetki Yükseltme)
- **Etkilenen Uç:** `GET /admin/stats`
- **Sözleşme / İş Kuralı Atfı:** `openapi.yaml` (`tags.admin` satır 26–27, `GET /admin/stats` satır 258–274): *"Sistem genel istatistiklerini döner. Yalnızca role=admin erişebilir; normal kullanıcı için 403 dönülmelidir."*
- **Beklenen Davranış:** `tok_user1_ayse` veya `tok_user2_mehmet` (`role=user`) ile `GET /admin/stats` çağrıldığında `403 Forbidden` (`Error` şeması) dönmelidir.
- **Gerçekleşen Davranış:** Normal kullanıcı token'larıyla `GET /admin/stats` çağrıldığında HTTP `200 OK` ile sistemin toplam poliçe sayısı, toplam hasar sayısı ve toplam prim tutarı döndürülmektedir. (`GET /admin/policies` aynı durumda doğru şekilde `403` dönmektedir.)
- **Tekrar Üretim Adımları:**
  1. İstek: `GET http://localhost:4105/admin/stats`
  2. Token: `Authorization: Bearer tok_user1_ayse` (veya `Bearer tok_user2_mehmet`)
  3. Gözlenen Yanıt: HTTP **200**
     ```json
     {"totalPolicies":5,"totalClaims":7,"totalPremium":9800}
     ```
- **Tekrarlanabilirlik:** Her zaman.
- **Kanıt ID (`test-kayitlari.md`):** `RO-57`, `RO-58`, `VER-15`, `EXT-03` (karşılaştırma: `RO-53`, `RO-54`, `VER-14`).

---

### BLG-04 — `PATCH /policies/{id}` ile salt okunur `status` alanı kullanıcı tarafından değiştirilebiliyor (Mass Assignment)
- **Önem Derecesi:** Kritik (Öncelik: Acil — Yetkisiz Durum Manipülasyonu)
- **Etkilenen Uç:** `PATCH /policies/{id}`
- **Sözleşme / İş Kuralı Atfı:** `openapi.yaml` (`PATCH /policies/{id}` satır 92–98, `Policy.status` satır 335–337): *"Poliçe sahibi YALNIZCA `holderName` ve `agentName` alanlarını güncelleyebilir. `premium`, `coverageLimit`, `status`, `ownerUserId`, `policyNumber`, `coverageType` alanları salt okunurdur ve istek gövdesiyle DEĞİŞTİRİLEMEZ; bu alanlar gövdede gönderilse bile yok sayılmalıdır. Poliçenin durumu (`status`) yalnızca iç iş süreçleriyle değişir."*
- **Beklenen Davranış:** İstek gövdesinde `status` gönderildiğinde yok sayılmalı (ve poliçe durumu değişmemeli) veya şemaya göre reddedilmelidir; hiçbir durumda normal kullanıcı poliçenin `status` değerini değiştirememelidir.
- **Gerçekleşen Davranış:** Diğer salt okunur alanlar (`premium`, `coverageLimit`, `ownerUserId`, `policyNumber`, `coverageType`, `holderTckn`, `id`, `startDate`, `endDate`) yok sayılırken, **`status` alanı güncellenmekte ve kalıcı olmaktadır**. Kullanıcı kendi `active` poliçesini `cancelled` yapabilmekte (`PAT-23`), iptal edilmiş (`cancelled`) `pol_3` poliçesini yeniden `active` durumuna çekebilmekte (`PAT-35`) ve şema enum'unda yer almayan `"bogus_status"` gibi geçersiz bir değeri bile kaydedebilmektedir (`PAT-36`).
- **Tekrar Üretim Adımları:**
  1. İstek: `PATCH http://localhost:4105/policies/pol_3`
  2. Başlıklar: `Authorization: Bearer tok_user2_mehmet`, `Content-Type: application/json`
  3. Gövde: `{"status": "active"}` (ön koşul: `pol_3` başlangıçta `"status": "cancelled"`)
  4. Gözlenen Yanıt: HTTP **200**
     ```json
     {"id":"pol_3","policyNumber":"POL-2026-0003","ownerUserId":"u2","holderName":"Mehmet Demir","holderTckn":"22222222220","coverageType":"saglik","premium":900,"coverageLimit":20000,"status":"active","agentName":"Can Öz","startDate":"2026-01-10","endDate":"2026-07-10"}
     ```
  5. Benzer şekilde `pol_5` (`tok_user1_ayse`) üzerinde `{"status": "cancelled"}` gönderildiğinde `status` kalıcı olarak `"cancelled"` olmakta (`PAT-31` `GET` ile doğrulandı); `{"status": "bogus_status"}` gönderildiğinde ise `"bogus_status"` kaydedilmektedir.
- **Tekrarlanabilirlik:** Her zaman.
- **Kanıt ID (`test-kayitlari.md`):** `PAT-23`, `PAT-31`, `PAT-35`, `PAT-36` (diğer alanların korunduğu kanıtlar: `PAT-20`–`PAT-30`).

---

## Yüksek Önem Dereceli Bulgular

### BLG-05 — `POST /claims` poliçe teminat limitini aşan tutarları `422` ile reddetmiyor
- **Önem Derecesi:** Yüksek (Finansal / İş Kuralı İhlali)
- **Etkilenen Uç:** `POST /claims`
- **Sözleşme / İş Kuralı Atfı:** `openapi.yaml` (`POST /claims` satır 171–173, `422` yanıtı satır 202–206, `ClaimCreate.amount` satır 390): *"İş kuralı: Bir hasar talebinin tutarı (`amount`), ilgili poliçenin teminat limitini (`coverageLimit`) AŞAMAZ. Aşan istekler 422 ile reddedilmelidir."*
- **Beklenen Davranış:** `coverageLimit` değeri `50000` olan `pol_1` için `amount <= 50000` kabul edilmeli; `50000.01`, `50001` veya `100000` gibi limiti aşan değerler HTTP `422` (`Error` şeması) ile reddedilmelidir.
- **Gerçekleşen Davranış:** Sınır değer `50000` kabul edilmektedir (`CLM-23`), ancak limiti aşan `50000.01`, `50001`, `100000` ve hatta `1e+308` tutarları da HTTP `200` ile kabul edilip hasar kaydı oluşturulmaktadır.
- **Tekrar Üretim Adımları:**
  1. İstek: `POST http://localhost:4105/claims`
  2. Başlıklar: `Authorization: Bearer tok_user1_ayse`, `Content-Type: application/json`
  3. Gövde: `{"policyId": "pol_1", "amount": 50000.01, "description": "Limit aşımı 50000.01"}` (`pol_1.coverageLimit = 50000`)
  4. Gözlenen Yanıt: HTTP **200**
     ```json
     {"id":"clm_16","policyId":"pol_1","ownerUserId":"u1","amount":50000.01,"status":"submitted","description":"Limit aşımı 50000.01","createdAt":"2026-08-01T00:00:00Z"}
     ```
- **Tekrarlanabilirlik:** Her zaman (`50000` kabul; `50000.01`, `50001`, `100000`, `1e+308` de kabul).
- **Kanıt ID (`test-kayitlari.md`):** `CLM-23`, `CLM-24`, `CLM-25`, `CLM-26`, `EDG-10`.

---

### BLG-06 — `POST /claims` asgari tutar kuralını (`amount >= 1`) doğrulamıyor; `0`, negatif ve `0.99` kabul ediliyor
- **Önem Derecesi:** Yüksek (Veri Bütünlüğü / Finansal Sınır İhlali)
- **Etkilenen Uç:** `POST /claims`
- **Sözleşme / İş Kuralı Atfı:** `openapi.yaml` (`ClaimCreate.amount` satır 387–390, `Claim.amount` satır 372–375): `minimum: 1` — *"Talep edilen tutar (TL). 1'den küçük olamaz"*.
- **Beklenen Davranış:** `amount = 1` kabul edilmeli; `0.99`, `0` ve negatif tutarlar (`-100`) `400` veya `422` ile reddedilmelidir.
- **Gerçekleşen Davranış:** `amount = 0`, `amount = -100` ve `amount = 0.99` gönderilen tüm istekler HTTP `200` ile kabul edilmekte ve veritabanına geçersiz tutarlarla hasar kaydı eklenmektedir.
- **Tekrar Üretim Adımları:**
  1. İstek: `POST http://localhost:4105/claims`
  2. Başlıklar: `Authorization: Bearer tok_user1_ayse`, `Content-Type: application/json`
  3. Gövde: `{"policyId": "pol_1", "amount": -100}` (veya `0` / `0.99`)
  4. Gözlenen Yanıt: HTTP **200**
     ```json
     {"id":"clm_12","policyId":"pol_1","ownerUserId":"u1","amount":-100,"status":"submitted","description":"","createdAt":"2026-08-01T00:00:00Z"}
     ```
- **Tekrarlanabilirlik:** Her zaman (alt sınırın her iki yanı test edildi: `1` kabul [`CLM-22`]; `0.99`, `0`, `-100` de kabul [`CLM-19`–`CLM-21`]).
- **Kanıt ID (`test-kayitlari.md`):** `CLM-19`, `CLM-20`, `CLM-21`, `CLM-22`.

---

### BLG-07 — `POST /claims` `Idempotency-Key` başlığını yok sayıyor; tekrarlanan istekler mükerrer kayıt oluşturuyor
- **Önem Derecesi:** Yüksek (Mükerrer Finansal Kayıt Riski)
- **Etkilenen Uç:** `POST /claims` (`Idempotency-Key` başlığı)
- **Sözleşme / İş Kuralı Atfı:** `openapi.yaml` (`POST /claims` satır 176–184): *"İstek `Idempotency-Key` başlığı ile gönderilirse, aynı anahtarla yapılan tekrar istekleri YENİ kayıt OLUŞTURMAMALI, ilk oluşturulan kaydı aynen döndürmelidir."*
- **Beklenen Davranış:** Aynı kullanıcı aynı `Idempotency-Key` değeriyle aynı isteği tekrarladığında yeni kayıt oluşturulmamalı ve ilk oluşturulan kaydın (`clm_21`) aynısı döndürülmelidir.
- **Gerçekleşen Davranış:** Aynı `Idempotency-Key` ile art arda yapılan ikinci istekte farklı bir `id` (`clm_22`) ile ikinci bir hasar kaydı oluşturuluyor. Aynı anahtar ile eşzamanlı gönderilen iki istekte de iki farklı kayıt (`clm_25` ve `clm_26`) oluşuyor ve `GET /claims?policyId=pol_2` sorgusunda hepsi listeleniyor.
- **Tekrar Üretim Adımları:**
  1. İlk istek: `POST http://localhost:4105/claims`
     - Başlıklar: `Authorization: Bearer tok_user1_ayse`, `Content-Type: application/json`, `Idempotency-Key: idem-key-001`
     - Gövde: `{"policyId": "pol_2", "amount": 300, "description": "Idem test"}`
     - Yanıt: `{"id":"clm_21",...}`
  2. İkinci istek (birebir aynı başlık ve gövdeyle tekrar):
     - Yanıt: HTTP **200**, yeni kayıt `{"id":"clm_22","policyId":"pol_2","ownerUserId":"u1","amount":300,"status":"submitted","description":"Idem test","createdAt":"2026-08-01T00:00:00Z"}`
  3. Doğrulama (`GET /claims?policyId=pol_2`, `tok_user1_ayse`): Hem `clm_21` hem `clm_22` mevcut.
- **Tekrarlanabilirlik:** Her zaman (hem sıralı hem eşzamanlı isteklerde doğrulandı).
- **Kanıt ID (`test-kayitlari.md`):** `CLM-29`, `CLM-30`, `CLM-31`, `CLM-34-1`, `CLM-34-2`, `CLM-35`.

---

### BLG-08 — Geçersiz JSON gövdesinde API tam `stack` izini ve sunucu dosya yolunu dışarı sızdırıyor
- **Önem Derecesi:** Yüksek (Güvenlik / Bilgi Sızıntısı — OWASP API8)
- **Etkilenen Uçlar:** `PATCH /policies/{id}`, `POST /claims`
- **Sözleşme / İş Kuralı Atfı:** `openapi.yaml` (`components.schemas.Error` satır 403–408): Hata yanıtları `{error, message}` biçiminde olmalıdır; iç hata yığın izi (stack trace) ve sunucu dosya yolu asla istemciye dönülmemelidir.
- **Beklenen Davranış:** Bozuk JSON veya JSON olmayan içerik gönderildiğinde yalnızca kullanıcı dostu `400 Bad Request` (`{"error": "...", "message": "..."}`) döndürülmelidir.
- **Gerçekleşen Davranış:** Hatalı JSON gönderildiğinde `400` yanıtının içinde `detail` ve tam Node.js `stack` izi (`server.js` dosya yolu ve satır numaraları dahil) dönmektedir; ayrıca `Error` şemasındaki `message` alanı yer almamaktadır.
- **Tekrar Üretim Adımları:**
  1. İstek: `PATCH http://localhost:4105/policies/pol_2` (veya `POST http://localhost:4105/claims`)
  2. Başlıklar: `Authorization: Bearer tok_user1_ayse`, `Content-Type: application/json`
  3. Ham Gövde: `{invalid json`
  4. Gözlenen Yanıt: HTTP **400**
     ```json
     {"error":"Geçersiz JSON","detail":"Expected property name or '}' in JSON at position 1 (line 1 column 2)","stack":"SyntaxError: Expected property name or '}' in JSON at position 1 (line 1 column 2)\n    at JSON.parse (<anonymous>)\n    at Server.<anonymous> (<sunucu-kok-dizini>\\servers\\R10\\server.js:155:27)\n    at process.processTicksAndRejections (node:internal/process/task_queues:104:5)"}
     ```
     *(Not: Çıktıdaki makine kullanıcı dizini ön eki raporda `<sunucu-kok-dizini>` şeklinde maskelenmiştir; gerçek API yanıtında mutlak yol tam olarak dönmektedir.)*
- **Tekrarlanabilirlik:** Her zaman.
- **Kanıt ID (`test-kayitlari.md`):** `PAT-17`, `CLM-18`, `VER-11`.

---

### BLG-09 — `POST /claims` iptal edilmiş (`status: cancelled`) poliçeye hasar talebi açılmasına izin veriyor
- **Önem Derecesi:** Yüksek (İş Kuralı İhlali ve Sözleşme Eksikliği)
- **Etkilenen Uç:** `POST /claims` (ayrıca `openapi.yaml` sözleşme belirsizliği)
- **Sözleşme / İş Kuralı Atfı:** `openapi.yaml` (`Policy.status` satır 335–337: `[active, cancelled, expired, pending]`). İptal edilmiş bir sigorta poliçesi üzerinde hasar talebi açılamaması temel sigortacılık iş kuralıdır; ancak `openapi.yaml` `POST /claims` açıklamasında poliçe durum kontrolünü açıkça belirtmemektedir.
- **Beklenen Davranış:** `status` değeri `cancelled` (veya `expired`/`pending`) olan bir poliçe için `POST /claims` isteği `422` (veya `400`) ile reddedilmelidir; bu kural `openapi.yaml` içinde de belgelenmelidir.
- **Gerçekleşen Davranış:** `tok_user2_mehmet`, `status` değeri `"cancelled"` olan `pol_3` poliçesi için hasar talebi gönderdiğinde istek HTTP `200` ile kabul edilmekte ve `clm_19` hasar kaydı oluşturulmaktadır.
- **Tekrar Üretim Adımları:**
  1. Ön koşul doğrulaması: `GET /policies` (`tok_user2_mehmet`) çıktısında `pol_3` poliçesinin `"status": "cancelled"` olduğu görülür (`RO-10`).
  2. İstek: `POST http://localhost:4105/claims`
  3. Başlıklar: `Authorization: Bearer tok_user2_mehmet`, `Content-Type: application/json`
  4. Gövde: `{"policyId": "pol_3", "amount": 100, "description": "İptal poliçeye hasar"}`
  5. Gözlenen Yanıt: HTTP **200**
     ```json
     {"id":"clm_19","policyId":"pol_3","ownerUserId":"u2","amount":100,"status":"submitted","description":"İptal poliçeye hasar","createdAt":"2026-08-01T00:00:00Z"}
     ```
- **Tekrarlanabilirlik:** Her zaman.
- **Kanıt ID (`test-kayitlari.md`):** `CLM-27`, `RO-10`.

---

## Orta Önem Dereceli Bulgular

### BLG-10 — `POST /claims` başarı durumunda `201 Created` yerine `200 OK` döndürüyor
- **Önem Derecesi:** Orta (Sözleşme / HTTP Durum Kodu Uyumsuzluğu)
- **Etkilenen Uç:** `POST /claims`
- **Sözleşme / İş Kuralı Atfı:** `openapi.yaml` (`POST /claims` satır 191–195): `'201': description: Oluşturulan hasar talebi`.
- **Beklenen Davranış:** Yeni bir hasar talebi başarıyla oluşturulduğunda HTTP `201` durum kodu döndürülmelidir.
- **Gerçekleşen Davranış:** Tüm başarılı hasar oluşturma istekleri (tüm geçerli oluşturma senaryoları dahil) HTTP `200` döndürmektedir.
- **Tekrar Üretim Adımları:**
  1. İstek: `POST http://localhost:4105/claims`
  2. Başlıklar: `Authorization: Bearer tok_user1_ayse`, `Content-Type: application/json`
  3. Gövde: `{"policyId": "pol_1", "amount": 1, "description": "Min sınır 1"}`
  4. Gözlenen Yanıt: HTTP **200** (`201` bekleniyordu), gövde `{"id":"clm_14",...}`.
- **Tekrarlanabilirlik:** Her zaman (tüm başarılı `POST /claims` çağrılarında).
- **Kanıt ID (`test-kayitlari.md`):** `CLM-22`, `CLM-23`, `CLM-29`, `VER-01`, `VER-13`, `EXT-05`.

---

### BLG-11 — `Claim` nesnelerinde sözleşmede zorunlu tanımlanan `claimNumber` alanı eksik
- **Önem Derecesi:** Orta (Sözleşme Şeması İhlali)
- **Etkilenen Uçlar:** `GET /claims`, `GET /claims/{id}`, `POST /claims`
- **Sözleşme / İş Kuralı Atfı:** `openapi.yaml` (`Claim` şeması satır 356–369): `required: [id, claimNumber, policyId, ownerUserId, amount, status, createdAt]`, `claimNumber: { type: string, examples: ['CLM-2026-0001'] }`.
- **Beklenen Davranış:** Dönen her `Claim` nesnesinde `claimNumber` string alanı mutlaka bulunmalıdır.
- **Gerçekleşen Davranış:** Hem başlangıç kayıtlarında (`clm_1`–`clm_7`) hem de `POST /claims` ile yeni oluşturulan tüm kayıtlarda (`clm_8`+) `claimNumber` alanı hiç döndürülmemektedir.
- **Tekrar Üretim Adımları:**
  1. İstek: `GET http://localhost:4105/claims/clm_1`
  2. Token: `Authorization: Bearer tok_user1_ayse`
  3. Gözlenen Yanıt: HTTP **200**
     ```json
     {"id":"clm_1","policyId":"pol_1","ownerUserId":"u1","amount":12000,"status":"submitted","description":"Çarpma hasarı","createdAt":"2026-05-02T09:00:00Z"}
     ```
     (`claimNumber` alanı yok.)
- **Tekrarlanabilirlik:** Her zaman.
- **Kanıt ID (`test-kayitlari.md`):** `RO-23`, `RO-24`, `RO-25`, `RO-46`, `RO-49`, `CLM-22`, `VER-13`.

---

### BLG-12 — `GET /claims` içindeki `meta.total` toplam kayıt sayısını değil yalnızca geçerli sayfadaki kayıt sayısını döndürüyor
- **Önem Derecesi:** Orta (Sayfalama İş Mantığı Hatası)
- **Etkilenen Uç:** `GET /claims`
- **Sözleşme / İş Kuralı Atfı:** `openapi.yaml` (`GET /claims` satır 132–134 ve `PageMeta.total` satır 400–402): *"Yanıttaki `meta.total` alanı, sayfalama uygulanmadan önceki TOPLAM (tüm sayfalardaki) kayıt sayısını belirtir; yalnızca geçerli sayfadaki kayıt sayısını değil."*
- **Beklenen Davranış:** Başlangıçta 5 hasar kaydı olan `u1` kullanıcısı `pageSize=2` ile sayfa 1, 2, 3 veya 4'ü istediğinde `meta.total` her zaman `5` olmalıdır (`policyId=pol_1` filtresiyle `2`).
- **Gerçekleşen Davranış:** `meta.total`, toplam kayıt sayısı yerine yalnızca o sayfadaki `data.length` değerini döndürmektedir (`page=1&pageSize=2` → `total: 2`, `page=3&pageSize=2` → `total: 1`, `page=4&pageSize=2` → `total: 0`). Bu durum istemcilerin toplam sayfa sayısını hesaplamasını imkânsız kılar.
- **Tekrar Üretim Adımları:**
  1. İstek: `GET http://localhost:4105/claims?page=3&pageSize=2` (ön koşul: `u1` kullanıcısının 5 hasar kaydı var)
  2. Token: `Authorization: Bearer tok_user1_ayse`
  3. Gözlenen Yanıt: HTTP **200**
     ```json
     {"data":[{"id":"clm_5","policyId":"pol_2","ownerUserId":"u1","amount":2000,"status":"submitted","description":"Hırsızlık","createdAt":"2026-07-03T16:05:00Z"}],"meta":{"page":3,"pageSize":2,"total":1}}
     ```
     (`meta.total` değeri `5` yerine `1` dönmüştür.)
- **Tekrarlanabilirlik:** Her zaman.
- **Kanıt ID (`test-kayitlari.md`):** `RO-26`, `RO-27`, `RO-28`, `RO-29`, `RO-43`, `RO-44`.

---

### BLG-13 — `GET /claims` `page` ve `pageSize` sınırlarını doğrulamıyor; negatif sayfa hatalı veri ve şema bozulması üretiyor
- **Önem Derecesi:** Orta (Giriş Doğrulama / Şema İhlali)
- **Etkilenen Uç:** `GET /claims`
- **Sözleşme / İş Kuralı Atfı:** `openapi.yaml` (`GET /claims` parametreleri satır 140–147, `PageMeta` satır 395–400): `page` (`type: integer, minimum: 1`), `pageSize` (`type: integer, minimum: 1, maximum: 100`), `PageMeta.page` ve `PageMeta.pageSize` (`type: integer`).
- **Beklenen Davranış:** `page < 1`, `pageSize < 1`, `pageSize > 100` veya sayısal olmayan (`abc`, ondalık `1.5`) değerler `400 Bad Request` ile reddedilmeli (veya en azından şemaya uygun güvenli sınırlandırma yapılmalı); `PageMeta.page` ve `PageMeta.pageSize` asla `null` veya negatif olmamalıdır.
- **Gerçekleşen Davranış:**
  - `page=-1&pageSize=2` → HTTP `200`, negatif dizi dilimlemesi (`slice(-4, -2)`) nedeniyle ortadaki kayıtları (`[clm_2, clm_3]`) ve `"meta":{"page":-1,"pageSize":2,"total":2}` döndürür (`RO-31`).
  - `page=abc` / `pageSize=abc` → HTTP `200`, `"meta":{"page":null,"pageSize":2,"total":0}` / `"pageSize":null` dönerek `PageMeta` (`type: integer`) şemasını bozar (`RO-32`, `RO-37`).
  - `page=0`, `pageSize=0`, `pageSize=-5` → HTTP `200`, `meta` içinde `0` veya `-5` döner (`RO-30`, `RO-33`, `RO-34`).
  - `pageSize=101` → HTTP `200`, maksimum `100` sınırını aşmasına rağmen `"pageSize":101` döner (`RO-36`, `VER-16`).
  - `page=1.5` / `pageSize=1.5` → Hata vermek yerine sessizce `1`'e yuvarlanır (`EDG-16`, `EDG-17`).
- **Tekrar Üretim Adımları:**
  1. İstek A: `GET http://localhost:4105/claims?page=-1&pageSize=2` (`Authorization: Bearer tok_user1_ayse`)
     - Gözlenen Yanıt: HTTP **200**, `data: [clm_2, clm_3]`, `meta: {"page":-1,"pageSize":2,"total":2}`
  2. İstek B: `GET http://localhost:4105/claims?page=abc&pageSize=2` (`Authorization: Bearer tok_user1_ayse`)
     - Gözlenen Yanıt: HTTP **200**, `{"data":[],"meta":{"page":null,"pageSize":2,"total":0}}`
  3. İstek C: `GET http://localhost:4105/claims?page=1&pageSize=101` (`Authorization: Bearer tok_admin_root`)
     - Gözlenen Yanıt: HTTP **200**, `meta.pageSize: 101`
- **Tekrarlanabilirlik:** Her zaman.
- **Kanıt ID (`test-kayitlari.md`):** `RO-30`, `RO-31`, `RO-32`, `RO-33`, `RO-34`, `RO-36`, `RO-37`, `EDG-16`, `EDG-17`, `VER-16`.

---

### BLG-14 — `PATCH /policies/{id}` ve `POST /claims` giriş veri tiplerini doğrulamıyor (`holderName`, `agentName`, `description`, `policyId`)
- **Önem Derecesi:** Orta (Veri Tipi / Bütünlük Doğrulama Eksikliği)
- **Etkilenen Uçlar:** `PATCH /policies/{id}`, `POST /claims`
- **Sözleşme / İş Kuralı Atfı:** `openapi.yaml` — `PolicyUpdate` (satır 346–353: `holderName: string`, `agentName: ['string', 'null']`), `Policy` (`holderName: string`), `ClaimCreate` (satır 383–393: `policyId: string`, `description: ['string', 'null']`). Yanlış tip `400 Bad Request` döndürmelidir.
- **Beklenen Davranış:** `holderName` için sayı/null/dizi/boş değer, `agentName` için sayı/nesne, `PATCH` kök gövdesi için `[]`, `POST /claims` içinde `description: 12345` veya `policyId: 12345` gönderildiğinde `400 Bad Request` dönmelidir.
- **Gerçekleşen Davranış:**
  - `PATCH /policies/pol_2`: `{"holderName": 12345}`, `{"holderName": null}`, `{"holderName": ["arr"]}`, `{"holderName": ""}` ve `{"agentName": 12345}` / `{"agentName": {"obj": 1}}` isteklerinin hepsi `200` ile kabul edilip poliçeye **kalıcı olarak** yazılmaktadır (`EXT-07` `GET` ile doğrulandı). Ayrıca gövde olarak `[]` gönderilmesi de `400` yerine `200` dönmektedir (`VER-08`).
  - `POST /claims`: `{"policyId": "pol_1", "amount": 500, "description": 12345}` isteği `400` yerine `200` dönüp `description` değerini sessizce `""` yapmaktadır (`CLM-16`). `{"policyId": 12345, ...}` ve `{"policyId": null, ...}` ise tip hatası (`400`) yerine `404 Poliçe bulunamadı` dönmektedir (`CLM-11`, `EDG-12`).
- **Tekrar Üretim Adımları:**
  1. İstek A: `PATCH http://localhost:4105/policies/pol_2` (`Authorization: Bearer tok_user1_ayse`, `Content-Type: application/json`)
     - Gövde: `{"holderName": 12345}` (veya `{"holderName": null}`)
     - Gözlenen Yanıt: HTTP **200**, `..."holderName":12345...` (`GET /policies/pol_2` sonrasında da `12345` döner).
  2. İstek B: `POST http://localhost:4105/claims` (`Authorization: Bearer tok_user1_ayse`, `Content-Type: application/json`)
     - Gövde: `{"policyId": "pol_1", "amount": 500, "description": 12345}`
     - Gözlenen Yanıt: HTTP **200**, `{"id":"clm_9",...,"description":""...}`.
- **Tekrarlanabilirlik:** Her zaman.
- **Kanıt ID (`test-kayitlari.md`):** `PAT-13`, `PAT-14`, `PAT-15`, `PAT-16`, `EDG-14`, `VER-08`, `EXT-06`, `EXT-07`, `CLM-16`, `CLM-11`, `EDG-12`.

---

### BLG-15 — `admin` başka kullanıcının poliçesine hasar oluşturduğunda `ownerUserId` `"admin"` atanıyor; poliçe sahibi erişemiyor
- **Önem Derecesi:** Orta (Sahiplik / Yetki Tutarsızlığı)
- **Etkilenen Uç:** `POST /claims` (ve `GET /claims/{id}`)
- **Sözleşme / İş Kuralı Atfı:** `openapi.yaml` (`info.description` satır 13–15, `GET /claims/{id}` satır 220): Yönetici tüm kaynaklara erişebilir; normal kullanıcı kendi poliçelerinin/hasarlarının sahibidir (`ownerUserId`).
- **Beklenen Davranış:** Yönetici bir müşterinin (`u1`) poliçesi (`pol_1`) adına hasar talebi oluşturduğunda (veya işlem desteklenmiyorsa reddetmiyorsa), kaydın `ownerUserId` alanı poliçe sahibine (`u1`) atanmalı; böylece poliçe sahibi `GET /claims/{id}` üzerinden kendi poliçesinin hasarını görebilmelidir.
- **Gerçekleşen Davranış:** `tok_admin_root` ile `pol_1` (`ownerUserId: "u1"`) için oluşturulan hasar talebinde `"ownerUserId": "admin"` kaydedilmektedir. Sonrasında `pol_1` sahibi `u1`, `GET /claims/clm_10` isteğinde `403 Erişim engellendi` almaktadır (`BLG-02` nedeniyle yalnızca `?policyId=pol_1` filtresiyle sızmaktadır).
- **Tekrar Üretim Adımları:**
  1. İstek 1: `POST http://localhost:4105/claims` (`Authorization: Bearer tok_admin_root`, `Content-Type: application/json`)
     - Gövde: `{"policyId": "pol_1", "amount": 250, "description": "Admin talebi"}`
     - Gözlenen Yanıt: HTTP **200**, `{"id":"clm_10","policyId":"pol_1","ownerUserId":"admin","amount":250,...}`
  2. İstek 2: `GET http://localhost:4105/claims/clm_10` (`Authorization: Bearer tok_user1_ayse`)
     - Gözlenen Yanıt: HTTP **403**, `{"error":"Erişim engellendi","message":"Bu hasar talebine erişim yetkiniz yok."}`
- **Tekrarlanabilirlik:** Her zaman.
- **Kanıt ID (`test-kayitlari.md`):** `CLM-07`, `VER-01`, `VER-02`.

---

## Düşük / Sözleşme Dokümantasyonu Kusuru

### BLG-16 — `openapi.yaml` sözleşmesinde `additionalProperties` çelişkisi ve eksik yanıt/kısıt tanımları var
- **Önem Derecesi:** Düşük (Sözleşme / Dokümantasyon Kusuru — İstemci ve Otomatik Doğrulama Uyuşmazlığı)
- **Etkilenen Kaynak:** `openapi.yaml` (`PATCH /policies/{id}`, `GET /claims`, `POST /claims`, `GET /policies/{id}`)
- **Bulunan Sözleşme Tutarsızlıkları:**
  1. **`PolicyUpdate` şema çelişkisi (satır 96–97 ve 348–353):** Açıklamalar salt okunur/fazla alanların *"gönderilse bile yok sayılacağını"* belirtirken `PolicyUpdate` şeması `additionalProperties: false` tanımlamaktadır. Katı bir OpenAPI istemcisi/ağ geçidi bu durumda fazla alanları `400` ile reddeder; oysa sunucu yok saymaktadır (`PAT-20`, `PAT-29`).
  2. **`GET /claims` eksik hata yanıtları (satır 125–162):** Açıklamada `policyId` için sahiplik/yetkilendirme kuralı ve `page`/`pageSize` için `minimum`/`maximum` sınırları tanımlanmasına rağmen `responses` altında `403` ve `400` yanıtları tanımlı değildir.
  3. **`POST /claims` poliçe durumu kuralı eksikliği (satır 167–174, 335–337):** `Policy.status` içinde `[active, cancelled, expired, pending]` değerleri bulunmasına rağmen `POST /claims` açıklamasında pasif/iptal poliçelerde hasar açılıp açılamayacağı belirtilmemiştir (`BLG-09`).
  4. **Eksik alan kısıtları ve yol örnekleri:** `PolicyUpdate.holderName` için `minLength`/`maxLength`, `ClaimCreate.policyId` için `minLength` ve `/policies/{id}` ile `/claims/{id}` yol parametreleri için `example` değeri eksiktir (`openapi_tests.py` tarafından da açık sözleşme sorusu olarak işaretlenmiştir).
- **Beklenen Davranış:** `openapi.yaml` sözleşmesi sunucunun amaçlanan davranışıyla çelişmeyecek şekilde güncellenmeli (`PolicyUpdate` içinde `additionalProperties` kararının netleştirilmesi, `GET /claims` için `400`/`403` yanıtlarının eklenmesi, `POST /claims` için poliçe `status` iş kuralının ve alan uzunluk/örnek tanımlarının eklenmesi).
- **Kanıt ID (`test-kayitlari.md`):** Bölüm 8 (`openapi_tests.py` çıktısı) ile `PAT-20`, `PAT-29`, `RO-30`–`RO-41`, `CLM-27`.
