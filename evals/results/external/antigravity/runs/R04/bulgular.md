# Kusur (Defect) Raporu — Anadolu Güven Sigorta Poliçe & Hasar API

- **Hedef Ortam:** `http://localhost:4102`
- **Referans Sözleşme:** `openapi.yaml` (v1.0.0)
- **Kanıt Kaydı:** Tüm bulgular [test-kayitlari.md](file:///C:/eval/runs/R04/test-kayitlari.md) dosyasındaki test kayıtlarına (`TC-xxx`) dayanmaktadır.

## Özet Tablo

| ID | Önem | Başlık | Etkilenen Uç(lar) | Kanıt |
|---|---|---|---|---|
| BLG-01 | **Kritik** | `GET /claims?policyId=...` Yetkilendirme Atlatma (IDOR) | `GET /claims` | `TC-021`..`TC-023` |
| BLG-02 | **Kritik** | JSON `null` İstek Gövdesiyle Sunucu Çökmesi (DoS) | `POST /claims`, `PATCH /policies/{id}` | `TC-059`, `TC-060` |
| BLG-03 | **Yüksek** | `GET /admin/stats` Ucunda Yönetici Rol Kontrolü Eksik | `GET /admin/stats` | `TC-009` |
| BLG-04 | **Yüksek** | `PATCH /policies/{id}` Salt Okunur `status` Alanını Değiştiriyor | `PATCH /policies/{id}` | `TC-034`..`TC-036` |
| BLG-05 | **Yüksek** | `POST /claims` Teminat Limiti (`coverageLimit`) İş Kuralını Uygulamıyor | `POST /claims` | `TC-043`, `TC-044` |
| BLG-06 | **Yüksek** | `POST /claims` Ucunda `Idempotency-Key` Tekrar Koruması Çalışmıyor | `POST /claims` | `TC-051`..`TC-053` |
| BLG-07 | **Orta** | `POST /claims` `amount < 1` Doğrulamasını Uygulamıyor (ve Tip Zorlama) | `POST /claims` | `TC-046`..`TC-048`, `TC-050` |
| BLG-08 | **Orta** | `POST /claims` `201 Created` Yerine `200 OK` Dönüyor | `POST /claims` | `TC-045`, `TC-051` |
| BLG-09 | **Orta** | Zorunlu `claimNumber` Alanı Tüm `Claim` Yanıtlarında Eksik | `GET /claims`, `GET /claims/{id}`, `POST /claims` | `TC-015`..`TC-017`, `TC-045` |
| BLG-10 | **Orta** | `GET /claims` Sayfalamada `meta.total` Yanlış ve Geçersiz Parametreler Doğrulanmıyor | `GET /claims` | `TC-024`..`TC-030` |
| BLG-11 | **Orta** | Bozuk JSON Gönderiminde Hata Yığını (Stack Trace) ve İç Yol Sızıntısı | `POST /claims`, `PATCH /policies/{id}` | `TC-057`, `TC-058` |
| BLG-12 | **Orta** | `PATCH /policies/{id}` Alan Tipi ve Gövde Yapısı Doğrulaması Eksik | `PATCH /policies/{id}` | `TC-037`, `TC-038`, `TC-062` |

> **Yayın Öncesi Değerlendirme:** `BLG-01`..`BLG-06` (özellikle başka kullanıcıların hasar kayıtlarının okunabilmesi, tek `null` gövdeyle sunucunun çökertilebilmesi, normal kullanıcıların sistem geneli yönetici istatistiklerini ve iptal edilmiş poliçe durumlarını değiştirebilmesi, limit aşımı ile mükerrer hasar kaydı oluşturulabilmesi) canlıya çıkış öncesi **engelleyici (blocker)** niteliktedir.

---

## Bulgu Detayları

### BLG-01: `GET /claims?policyId=...` Yetkilendirme Atlatma (IDOR / Yatay Yetki Aşımı)
- **Önem Derecesi:** Kritik
- **Etkilenen Uç:** `GET /claims?policyId={id}`
- **Sözleşme / İş Kuralı Atfı:**
  - `openapi.yaml` (`info.description`): *"Normal kullanıcı (role=user) yalnızca KENDİ poliçelerine ve KENDİ hasar taleplerine erişebilir."*
  - `openapi.yaml` (`paths./claims.get.description`): *"`policyId` sorgu parametresi verilirse yalnızca o poliçeye ait talepler süzülür; ancak bu durumda da yetkilendirme kuralı geçerlidir: kullanıcı yalnızca KENDİSİNE ait poliçelerin taleplerini görebilir."*
- **Beklenen Davranış:** Normal bir kullanıcı (`u1`) başka bir kullanıcıya (`u2`) ait `pol_3` veya `pol_4` poliçesini `policyId` parametresiyle sorguladığında `403` veya başkasının kayıtlarını içermeyen boş sonuç dönmelidir.
- **Gerçekleşen Davranış:** `policyId` parametresi verildiğinde sahiplik (`ownerUserId`) filtresi uygulanmamakta, herhangi bir kimliği doğrulanmış kullanıcı diğer tüm kullanıcıların hasar taleplerini okuyabilmektedir.
- **Tekrar Üretim Adımları:**
  - **Kanıt:** `TC-021`, `TC-022`, `TC-023`
  - **İstek:**
    ```http
    GET /claims?policyId=pol_3 HTTP/1.1
    Host: localhost:4102
    Authorization: Bearer tok_user1_ayse
    ```
  - **Gözlenen Yanıt (`200 OK`):**
    ```json
    {"data":[{"id":"clm_7","policyId":"pol_3","ownerUserId":"u2","amount":1000,"status":"rejected","description":"Muayene masrafı","createdAt":"2026-06-11T13:00:00Z"}],"meta":{"page":1,"pageSize":20,"total":1}}
    ```
  - Aynı şekilde `tok_user2_mehmet` ile `GET /claims?policyId=pol_1` çağrıldığında `u1`'e ait `clm_1` ve `clm_2` dönmektedir.

---

### BLG-02: JSON `null` İstek Gövdesiyle Sunucu Çökmesi (Hizmet Kesintisi / DoS)
- **Önem Derecesi:** Kritik
- **Etkilenen Uçlar:** `POST /claims`, `PATCH /policies/{id}`
- **Sözleşme / İş Kuralı Atfı:** `openapi.yaml` (`BadRequest` yanıtları ve `requestBody` tanımları). Geçersiz gövdelerde sunucu kararlılığını korumalı ve `Error` şemasında `400 Bad Request` dönmelidir.
- **Beklenen Davranış:** `Content-Type: application/json` ile gövde olarak `null` gönderildiğinde `400` hata yanıtı dönülmelidir.
- **Gerçekleşen Davranış:** `null` gövdesi `JSON.parse` sonrası nesne sanılarak alan okunmaya çalışılmakta; işlenmeyen istisna nedeniyle TCP bağlantısı aniden kapatılmakta (`ConnectionResetError: [WinError 10054]` / `curl` çıkış kodu `1`, boş yanıt) ve sunucu süreci çöküp yeniden başlamaktadır. Yeniden başlama nedeniyle bellekte sonradan oluşturulan tüm veriler de silinmiştir.
- **Tekrar Üretim Adımları:**
  - **Kanıt:** `TC-059`, `TC-060`
  - **İstek 1:**
    ```http
    POST /claims HTTP/1.1
    Host: localhost:4102
    Authorization: Bearer tok_user1_ayse
    Content-Type: application/json

    null
    ```
  - **İstek 2:**
    ```http
    PATCH /policies/pol_2 HTTP/1.1
    Host: localhost:4102
    Authorization: Bearer tok_user1_ayse
    Content-Type: application/json

    null
    ```
  - **Gözlenen Yanıt:** HTTP yanıtı dönmeden bağlantı kopmaktadır (`WinError 10054` / `curl` exit code `1`); hemen ardından `GET /claims` yapıldığında önceki testlerde oluşturulmuş `clm_8`..`clm_19` kayıtlarının sıfırlandığı görülmüştür.

---

### BLG-03: `GET /admin/stats` Ucunda Yönetici Rol Kontrolü Eksik (Dikey Yetki Aşımı)
- **Önem Derecesi:** Yüksek
- **Etkilenen Uç:** `GET /admin/stats`
- **Sözleşme / İş Kuralı Atfı:**
  - `openapi.yaml` (`tags.admin`): *"Yönetici işlemleri (yalnızca role=admin)"*
  - `openapi.yaml` (`paths./admin/stats.get.description` & `403`): *"Sistem genel istatistiklerini döner. Yalnızca role=admin erişebilir; normal kullanıcı için 403 dönülmelidir."*
- **Beklenen Davranış:** `tok_user1_ayse` veya `tok_user2_mehmet` (`role=user`) ile istek atıldığında `403 Forbidden` dönmelidir (`GET /admin/policies` ucunda olduğu gibi).
- **Gerçekleşen Davranış:** Normal kullanıcı token'larıyla `200 OK` dönmekte ve tüm sistemdeki toplam poliçe, hasar ve prim tutarı ifşa edilmektedir.
- **Tekrar Üretim Adımları:**
  - **Kanıt:** `TC-009`
  - **İstek:**
    ```http
    GET /admin/stats HTTP/1.1
    Host: localhost:4102
    Authorization: Bearer tok_user1_ayse
    ```
  - **Gözlenen Yanıt (`200 OK`):**
    ```json
    {"totalPolicies":5,"totalClaims":7,"totalPremium":9800}
    ```
    (`tok_user2_mehmet` ile de aynı şekilde `200 OK` dönmektedir.)

---

### BLG-04: `PATCH /policies/{id}` Salt Okunur `status` Alanını Değiştiriyor ve Geçersiz Enum Kabul Ediyor
- **Önem Derecesi:** Yüksek
- **Etkilenen Uç:** `PATCH /policies/{id}`
- **Sözleşme / İş Kuralı Atfı:**
  - `openapi.yaml` (`paths./policies/{id}.patch.description`): *"Poliçe sahibi YALNIZCA `holderName` ve `agentName` alanlarını güncelleyebilir. `premium`, `coverageLimit`, `status`, `ownerUserId`, `policyNumber`, `coverageType` alanları salt okunurdur ve istek gövdesiyle DEĞİŞTİRİLEMEZ; bu alanlar gövdede gönderilse bile yok sayılmalıdır. Poliçenin durumu (`status`) yalnızca iç iş süreçleriyle değişir."*
  - `openapi.yaml` (`Policy.status`): `enum: [active, cancelled, expired, pending]`
- **Beklenen Davranış:** Gövdede `status` gönderildiğinde yok sayılmalı ve poliçe durumu değişmemelidir.
- **Gerçekleşen Davranış:** Diğer salt okunur alanlar (`premium`, `coverageLimit`, `ownerUserId`, `policyNumber`, `coverageType`, `holderTckn`, `startDate`, `endDate`, `id`) doğru şekilde yok sayılırken, yalnızca `status` alanı güncellemeye açık bırakılmıştır. Dahası `status` alanı için enum doğrulaması da yoktur: poliçe sahibi iptal edilmiş poliçesini yeniden `active` yapabilmekte ya da `"hacked_status"` gibi geçersiz bir değer atayabilmektedir.
- **Tekrar Üretim Adımları:**
  - **Kanıt:** `TC-034`, `TC-035`, `TC-036`
  - **İstek (İptal edilmiş poliçeyi aktif etme):**
    ```http
    PATCH /policies/pol_3 HTTP/1.1
    Host: localhost:4102
    Authorization: Bearer tok_user2_mehmet
    Content-Type: application/json

    {"status": "active"}
    ```
  - **Gözlenen Yanıt (`200 OK`):**
    ```json
    {"id":"pol_3","policyNumber":"POL-2026-0003","ownerUserId":"u2","holderName":"Mehmet Demir","holderTckn":"22222222220","coverageType":"saglik","premium":900,"coverageLimit":20000,"status":"active","agentName":"Can Öz","startDate":"2026-01-10","endDate":"2026-07-10"}
    ```
  - Ayrıca `tok_user1_ayse` ile `PATCH /policies/pol_5` gövdesinde `{"status":"hacked_status"}` gönderildiğinde `200 OK` ile `"status":"hacked_status"` kaydedilmiştir.

---

### BLG-05: `POST /claims` Teminat Limiti (`coverageLimit`) İş Kuralını Uygulamıyor
- **Önem Derecesi:** Yüksek
- **Etkilenen Uç:** `POST /claims`
- **Sözleşme / İş Kuralı Atfı:** `openapi.yaml` (`paths./claims.post.description` ve `422` yanıtı): *"İş kuralı: Bir hasar talebinin tutarı (`amount`), ilgili poliçenin teminat limitini (`coverageLimit`) AŞAMAZ. Aşan istekler 422 ile reddedilmelidir."*
- **Beklenen Davranış:** `coverageLimit` değeri `50000` olan `pol_1` poliçesi için `amount > 50000` gönderildiğinde `422` durum koduyla reddedilmelidir.
- **Gerçekleşen Davranış:** Teminat limiti kontrolü yapılmamaktadır; `50001` ve hatta `1e308` tutarlarıyla yapılan talepler `200 OK` dönerek oluşturulmaktadır.
- **Tekrar Üretim Adımları:**
  - **Kanıt:** `TC-043`, `TC-044`
  - **İstek:**
    ```http
    POST /claims HTTP/1.1
    Host: localhost:4102
    Authorization: Bearer tok_user1_ayse
    Content-Type: application/json

    {"policyId": "pol_1", "amount": 50001, "description": "Over limit"}
    ```
  - **Gözlenen Yanıt (`200 OK`):**
    ```json
    {"id":"clm_9","policyId":"pol_1","ownerUserId":"u1","amount":50001,"status":"submitted","description":"Over limit","createdAt":"2026-08-01T00:00:00Z"}
    ```

---

### BLG-06: `POST /claims` Ucunda `Idempotency-Key` Tekrar Koruması Çalışmıyor
- **Önem Derecesi:** Yüksek
- **Etkilenen Uç:** `POST /claims`
- **Sözleşme / İş Kuralı Atfı:** `openapi.yaml` (`paths./claims.post.description` & `parameters.Idempotency-Key`): *"İstek `Idempotency-Key` başlığı ile gönderilirse, aynı anahtarla yapılan tekrar istekleri YENİ kayıt OLUŞTURMAMALI, ilk oluşturulan kaydı aynen döndürmelidir."*
- **Beklenen Davranış:** Aynı `Idempotency-Key` başlığı ile gönderilen ikinci ve sonraki isteklerde yeni kayıt oluşturulmamalı, ilk oluşturulan hasar talebi döndürülmelidir.
- **Gerçekleşen Davranış:** `Idempotency-Key` (veya küçük harfli `idempotency-key`) başlığı tamamen yok sayılmakta; aynı anahtarla gönderilen her tekrar istekte yeni `id` ile mükerrer hasar kaydı açılmaktadır.
- **Tekrar Üretim Adımları:**
  - **Kanıt:** `TC-051`, `TC-052`, `TC-053`
  - **İstek (2 kez art arda gönderilir):**
    ```http
    POST /claims HTTP/1.1
    Host: localhost:4102
    Authorization: Bearer tok_user2_mehmet
    Idempotency-Key: req-idem-clean-1
    Content-Type: application/json

    {"policyId": "pol_4", "amount": 2500, "description": "Idempotency check"}
    ```
  - **Gözlenen Yanıtlar (`200 OK`):**
    - 1. istek: `{"id":"clm_11","policyId":"pol_4","ownerUserId":"u2","amount":2500,"status":"submitted","description":"Idempotency check","createdAt":"2026-08-01T00:00:00Z"}`
    - 2. istek: `{"id":"clm_12","policyId":"pol_4","ownerUserId":"u2","amount":2500,"status":"submitted","description":"Idempotency check","createdAt":"2026-08-01T00:00:00Z"}` (Mükerrer `clm_12` kaydı oluştu.)

---

### BLG-07: `POST /claims` `amount` Alt Sınırını (`minimum: 1`) Uygulamıyor (ve `description` Tip Zorlaması)
- **Önem Derecesi:** Orta
- **Etkilenen Uç:** `POST /claims`
- **Sözleşme / İş Kuralı Atfı:** `openapi.yaml` (`ClaimCreate.amount` ve `Claim.amount`): `type: number, minimum: 1` (*"Talep edilen tutar (TL). 1'den küçük olamaz"*); `description`: `type: ['string', 'null']`.
- **Beklenen Davranış:** `amount < 1` (`0`, `-500`, `0.5`) değerleri ve `description` için string/null dışı tipler `400` (veya `422`) ile reddedilmelidir.
- **Gerçekleşen Davranış:** `0`, negatif (`-500`) ve `0.5` tutarları `200 OK` ile kaydedilmektedir. Ayrıca `description: 999` gönderildiğinde hata dönmek yerine sessizce `""` boş metne dönüştürülmektedir.
- **Tekrar Üretim Adımları:**
  - **Kanıt:** `TC-046`, `TC-047`, `TC-048`, `TC-050`
  - **İstek:**
    ```http
    POST /claims HTTP/1.1
    Host: localhost:4102
    Authorization: Bearer tok_user1_ayse
    Content-Type: application/json

    {"policyId": "pol_1", "amount": -500}
    ```
  - **Gözlenen Yanıt (`200 OK`):**
    ```json
    {"id":"clm_12","policyId":"pol_1","ownerUserId":"u1","amount":-500,"status":"submitted","description":"","createdAt":"2026-08-01T00:00:00Z"}
    ```

---

### BLG-08: `POST /claims` Başarılı Oluşturmada `201` Yerine `200` Durum Kodu Dönüyor
- **Önem Derecesi:** Orta
- **Etkilenen Uç:** `POST /claims`
- **Sözleşme / İş Kuralı Atfı:** `openapi.yaml` (`paths./claims.post.responses.'201'`).
- **Beklenen Davranış:** Yeni hasar talebi oluşturulduğunda HTTP `201 Created` durum kodu dönmelidir.
- **Gerçekleşen Davranış:** Tüm başarılı `POST /claims` istekleri HTTP `200 OK` durum kodu ile yanıtlanmaktadır.
- **Tekrar Üretim Adımları:**
  - **Kanıt:** `TC-045`, `TC-051`
  - **İstek:** `tok_user1_ayse` ile `POST /claims`, gövde `{"policyId":"pol_1","amount":50000,"description":"Exact limit"}`
  - **Gözlenen Yanıt:** Durum kodu `200` (beklenen `201`).

---

### BLG-09: Zorunlu `claimNumber` Alanı Tüm `Claim` Yanıtlarında Eksik
- **Önem Derecesi:** Orta
- **Etkilenen Uçlar:** `GET /claims`, `GET /claims/{id}`, `POST /claims`
- **Sözleşme / İş Kuralı Atfı:** `openapi.yaml` (`components.schemas.Claim.required`): `claimNumber` alanı zorunlu (`required`) alanlar listesinde yer almaktadır (`type: string`, örnek: `'CLM-2026-0001'`).
- **Beklenen Davranış:** Her `Claim` nesnesinde `claimNumber` alanı bulunmalıdır.
- **Gerçekleşen Davranış:** Hem hazır verilerdeki (`clm_1`..`clm_7`) hem de `POST /claims` ile yeni oluşturulan kayıtlarda `claimNumber` alanı hiç dönmemektedir.
- **Tekrar Üretim Adımları:**
  - **Kanıt:** `TC-015`, `TC-016`, `TC-017`, `TC-045`
  - **İstek:**
    ```http
    GET /claims/clm_1 HTTP/1.1
    Host: localhost:4102
    Authorization: Bearer tok_user1_ayse
    ```
  - **Gözlenen Yanıt (`200 OK`):**
    ```json
    {"id":"clm_1","policyId":"pol_1","ownerUserId":"u1","amount":12000,"status":"submitted","description":"Çarpma hasarı","createdAt":"2026-05-02T09:00:00Z"}
    ```

---

### BLG-10: `GET /claims` Sayfalamada `meta.total` Yanlış Hesaplanıyor ve Geçersiz Sayfalama Parametreleri Doğrulanmıyor
- **Önem Derecesi:** Orta
- **Etkilenen Uç:** `GET /claims`
- **Sözleşme / İş Kuralı Atfı:**
  - `openapi.yaml` (`paths./claims.get.description` & `PageMeta.total`): *"Yanıttaki `meta.total` alanı, sayfalama uygulanmadan önceki TOPLAM (tüm sayfalardaki) kayıt sayısını belirtir; yalnızca geçerli sayfadaki kayıt sayısını değil."*
  - `openapi.yaml` (`page` & `pageSize` parametreleri ve `PageMeta`): `page` (`integer, minimum: 1`), `pageSize` (`integer, minimum: 1, maximum: 100`).
- **Beklenen Davranış:**
  1. `meta.total` sayfalama öncesi toplam kayıt sayısını vermelidir (ör. `u1` için `5`, `admin` için `7`).
  2. `page < 1`, `pageSize < 1`, `pageSize > 100` veya tamsayı olmayan (`abc`, `1.5`) parametreler `400` ile reddedilmelidir.
- **Gerçekleşen Davranış:**
  1. `meta.total` yalnızca geçerli sayfadaki `data.length` değerini dönmektedir (ör. `admin` için `page=1&pageSize=2` çağrısında `meta.total: 2`; `u1` için `page=4&pageSize=2` çağrısında `meta.total: 0`).
  2. Geçersiz parametreler `200 OK` dönmektedir: `page=-1` ve `pageSize=-5` negatif dizi dilimlemesi nedeniyle beklenmedik kayıtlar döndürmekte; `page=abc` / `pageSize=abc` değerlerinde `PageMeta` şemasına aykırı olarak `"page": null` / `"pageSize": null` dönmekte; `pageSize=101` üst sınırı aşmasına rağmen kabul edilmektedir.
- **Tekrar Üretim Adımları:**
  - **Kanıt:** `TC-024`..`TC-030`
  - **İstek 1 (`meta.total` hatası):** `GET /claims?page=1&pageSize=2` (`Authorization: Bearer tok_admin_root`)
    - **Gözlenen Yanıt (`200 OK`):** `data` içinde 2 kayıt, `"meta":{"page":1,"pageSize":2,"total":2}` (beklenen `total: 7`).
  - **İstek 2 (Negatif `pageSize`):** `GET /claims?page=1&pageSize=-5` (`Authorization: Bearer tok_admin_root`)
    - **Gözlenen Yanıt (`200 OK`):** `clm_1`, `clm_2` kayıtları ve `"meta":{"page":1,"pageSize":-5,"total":2}`.
  - **İstek 3 (Sayısal olmayan `page`):** `GET /claims?page=abc&pageSize=2` (`Authorization: Bearer tok_user1_ayse`)
    - **Gözlenen Yanıt (`200 OK`):** `{"data":[],"meta":{"page":null,"pageSize":2,"total":0}}`.

---

### BLG-11: Bozuk JSON Gönderiminde Hata Yığını (Stack Trace), İç Dosya Yolu Sızıntısı ve `Error` Şeması Uyumsuzluğu
- **Önem Derecesi:** Orta
- **Etkilenen Uçlar:** `POST /claims`, `PATCH /policies/{id}`
- **Sözleşme / İş Kuralı Atfı:** `openapi.yaml` (`components.responses.BadRequest` ve `components.schemas.Error`: `{ error, message }`). İstemci hatalarında dahili uygulama yığını ve sunucu dosya sistemi yolu paylaşılmamalıdır.
- **Beklenen Davranış:** Bozuk JSON gövdesi gönderildiğinde iç ayrıntı içermeyen sade `400 Bad Request` (`{"error":"...","message":"..."}`) yanıtı dönmelidir.
- **Gerçekleşen Davranış:** Yanıt gövdesinde `message` yerine `detail` ve tam Node.js `stack` izi ile sunucunun yerel dosya yolu dışarı sızdırılmaktadır.
- **Tekrar Üretim Adımları:**
  - **Kanıt:** `TC-057`, `TC-058`
  - **İstek:**
    ```http
    POST /claims HTTP/1.1
    Host: localhost:4102
    Authorization: Bearer tok_user1_ayse
    Content-Type: application/json

    {bad json
    ```
  - **Gözlenen Yanıt (`400 Bad Request`):**
    ```json
    {"error":"Geçersiz JSON","detail":"Expected property name or '}' in JSON at position 1 (line 1 column 2)","stack":"SyntaxError: Expected property name or '}' in JSON at position 1 (line 1 column 2)\n    at JSON.parse (<anonymous>)\n    at Server.<anonymous> (C:\\eval\\servers\\R04\\server.js:216:25)\n    at process.processTicksAndRejections (node:internal/process/task_queues:104:5)"}
    ```
  - Aynı durum `PATCH /policies/pol_2` ucunda `{bad` gövdesiyle de tekrarlanmaktadır (`server.js:155:27`).

---

### BLG-12: `PATCH /policies/{id}` Alan Tipi ve Gövde Yapısı Doğrulaması Eksik
- **Önem Derecesi:** Orta
- **Etkilenen Uç:** `PATCH /policies/{id}`
- **Sözleşme / İş Kuralı Atfı:** `openapi.yaml` (`PolicyUpdate` & `Policy`): `holderName` alanı `type: string` (null olamaz), `agentName` alanı `type: ['string', 'null']` ve istek gövdesi `type: object` olmalıdır.
- **Beklenen Davranış:** `holderName` için sayı veya `null`, `agentName` için boolean gönderildiğinde ya da gövde JSON nesnesi değil (`[]`, `"hello"`) olduğunda `400 Bad Request` dönmelidir.
- **Gerçekleşen Davranış:** İstek `200 OK` ile kabul edilmekte; `holderName: 12345`, `holderName: null`, `agentName: true` gibi şemaya aykırı değerler poliçeye kaydedilmektedir. Dizi (`[]`) ve metin (`"hello"`) gövdelerinde de `400` yerine `200 OK` dönmektedir.
- **Tekrar Üretim Adımları:**
  - **Kanıt:** `TC-037`, `TC-038`, `TC-062`
  - **İstek:**
    ```http
    PATCH /policies/pol_2 HTTP/1.1
    Host: localhost:4102
    Authorization: Bearer tok_user1_ayse
    Content-Type: application/json

    {"holderName": 12345, "agentName": true}
    ```
  - **Gözlenen Yanıt (`200 OK`):**
    ```json
    {"id":"pol_2","policyNumber":"POL-2026-0002","ownerUserId":"u1","holderName":12345,"holderTckn":"11111111110","coverageType":"konut","premium":2400,"coverageLimit":100000,"status":"active","agentName":true,"startDate":"2026-02-15","endDate":"2027-02-14"}
    ```
