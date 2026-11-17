# Kusur (Defect) Raporu — Anadolu Güven Sigorta Poliçe & Hasar API

**Test Edilen Ortam:** `http://localhost:4109`  
**Sözleşme Referansı:** `openapi.yaml` (v1.0.0)  
**Kanıt Kayıtları:** `test-kayitlari.md`  
**Yayın Öncesi Değerlendirme:** **Canlıya Çıkış İçin Hazır Değil (No-Go)**

Yapılan bağımsız yayın öncesi testlerde **2 Kritik**, **4 Yüksek**, **6 Orta** ve **1 Düşük** önem dereceli olmak üzere toplam **13 kusur** tespit edilmiştir. Özellikle tek bir istekle sunucuyu çökertebilen hizmet dışı bırakma (DoS) açığı, `GET /claims?policyId=` üzerindeki yatay yetki aşımı (IDOR), `GET /admin/stats` üzerindeki yönetici yetki kontrolü eksikliği, poliçe `status` alanının müşteri tarafından değiştirilebilmesi ile teminat limiti (`coverageLimit`) ve `Idempotency-Key` iş kurallarının çalışmaması canlı ortam riskini kritik seviyeye taşımaktadır.

## Kusur Özeti Tablosu

| ID | Başlık | Önem | Etkilenen Uç(lar) | Kanıt |
|----|--------|------|-------------------|-------|
| `BUL-01` | JSON `null` Gövdesiyle Sunucu Çökmesi ve Durum Sıfırlanması (DoS) | **Kritik** | `POST /claims`, `PATCH /policies/{id}` | `TK-52`, `TK-53` |
| `BUL-02` | `GET /claims?policyId=...` ile Başkasının Hasar Kayıtlarına Erişim (IDOR) | **Kritik** | `GET /claims` | `TK-15`, `TK-16` |
| `BUL-03` | `GET /admin/stats` Ucuna Normal Kullanıcıların Erişebilmesi (BFLA) | **Yüksek** | `GET /admin/stats` | `TK-20` |
| `BUL-04` | Salt Okunur `status` Alanının Değiştirilebilmesi ve Geçersiz Değer Kabulü | **Yüksek** | `PATCH /policies/{id}` | `TK-26`, `TK-27`, `TK-28` |
| `BUL-05` | Teminat Limiti (`coverageLimit`) Aşımının `422` ile Engellenmemesi | **Yüksek** | `POST /claims` | `TK-33`, `TK-34` |
| `BUL-06` | `Idempotency-Key` Başlığının Yok Sayılması (Mükerrer Kayıt) | **Yüksek** | `POST /claims` | `TK-43`, `TK-44` |
| `BUL-07` | Hatalı JSON Girdisinde `stack` İzi ve Sunucu Dosya Yolunun İfşası | **Orta** | `POST /claims`, `PATCH /policies/{id}` | `TK-50`, `TK-51` |
| `BUL-08` | Tutar (`amount < 1`) Alt Sınırının ve `description` Tipinin Doğrulanmaması | **Orta** | `POST /claims` | `TK-37`–`TK-40` |
| `BUL-09` | Sayfalamada `meta.total` Değerinin Yanlış Hesaplanması | **Orta** | `GET /claims` | `TK-45` |
| `BUL-10` | `page` ve `pageSize` Parametrelerinin Doğrulanmaması ve Şema İhlali | **Orta** | `GET /claims` | `TK-46`, `TK-47` |
| `BUL-11` | `Claim` Nesnelerinde Zorunlu `claimNumber` Alanının Eksik Olması | **Orta** | `GET /claims`, `GET /claims/{id}`, `POST /claims` | `TK-31` |
| `BUL-12` | `holderName` ve `agentName` Alanlarında Tip / `null` Doğrulama Eksikliği | **Orta** | `PATCH /policies/{id}` | `TK-29` |
| `BUL-13` | Başarılı Kayıt Oluşturmada `201 Created` Yerine `200 OK` Dönülmesi | **Düşük** | `POST /claims` | `TK-32` |

---

## Detaylı Bulgular

### BUL-01: JSON `null` Gövdesiyle Sunucu Çökmesi ve Durum Sıfırlanması (DoS)
- **Önem Derecesi:** Kritik
- **Etkilenen Uçlar:** `POST /claims`, `PATCH /policies/{id}`
- **Sözleşmeye Atıf:** `openapi.yaml` -> `POST /claims` (`400 BadRequest`), `PATCH /policies/{id}` (`400 BadRequest`) ve servis kararlılığı.
- **Beklenen Davranış:** Geçerli bir JSON ama nesne olmayan `null` gövdesi gönderildiğinde API'nin isteği `400 Bad Request` (`Error` şeması) ile reddedip normal çalışmasına devam etmesi gerekir.
- **Gerçekleşen Davranış:** Gövde olarak `null` gönderildiğinde sunucu yakalanmamış bir hata nedeniyle çökmekte, TCP bağlantısı zorla kesilmekte (`ConnectionResetError: [WinError 10054]`) ve servis yeniden başlatılarak o ana kadar oluşturulan tüm kayıtlar silinip başlangıç verisine dönmektedir (ör. `totalClaims` 22'den 7'ye düşmüştür). Kimliği doğrulanmış herhangi bir kullanıcı 4 baytlık bir istekle tüm API'yi kesintiye uğratabilmektedir.
- **Tekrar Üretim Adımları (`TK-52`, `TK-53`):**
  - **İstek 1:** `POST http://localhost:4109/claims`
    - Başlıklar: `Authorization: Bearer tok_user1_ayse`, `Content-Type: application/json`
    - Gövde: `null`
  - **İstek 2:** `PATCH http://localhost:4109/policies/pol_1`
    - Başlıklar: `Authorization: Bearer tok_user1_ayse`, `Content-Type: application/json`
    - Gövde: `null`
  - **Gözlenen Yanıt:** HTTP yanıtı dönmeden bağlantı sunucu tarafından kesilir (`WinError 10054`); hemen ardından `GET /admin/stats` çağrıldığında sayaçların başlangıç değerlerine (`totalClaims: 7`) sıfırlandığı görülür.

---

### BUL-02: `GET /claims?policyId=...` Üzerinde Yatay Yetki Aşımı (IDOR)
- **Önem Derecesi:** Kritik
- **Etkilenen Uç:** `GET /claims` (`policyId` sorgu parametresi kullanıldığında)
- **Sözleşmeye Atıf:** `openapi.yaml` -> genel *Yetkilendirme kuralları* (*"Normal kullanıcı (role=user) yalnızca KENDİ poliçelerine ve KENDİ hasar taleplerine erişebilir"*) ve `GET /claims` açıklaması (*"`policyId` sorgu parametresi verilirse yalnızca o poliçeye ait talepler süzülür; ancak bu durumda da yetkilendirme kuralı geçerlidir: kullanıcı yalnızca KENDİSİNE ait poliçelerin taleplerini görebilir"*).
- **Beklenen Davranış:** `u1` (`Ayşe Yılmaz`), `u2`'ye (`Mehmet Demir`) ait `pol_3` veya `pol_4` için `GET /claims?policyId=pol_3` istediğinde `u2`'nin hasar kayıtları kesinlikle döndürülmemelidir (`403 Forbidden` veya boş sonuç).
- **Gerçekleşen Davranış:** `GET /claims/{id}` ucu 403 ile koruma sağlarken, `GET /claims?policyId=<baskasinin_policesi>` çağrısı sahip kontrolünü tamamen atlamakta ve `200 OK` ile başka kullanıcılara ait hasar taleplerini döndürmektedir.
- **Tekrar Üretim Adımları (`TK-15`, `TK-16`):**
  - **İstek:** `GET http://localhost:4109/claims?policyId=pol_3`
  - **Token:** `Authorization: Bearer tok_user1_ayse` (`u1`)
  - **Gözlenen Yanıt (`200 OK`):**
    ```json
    {"data":[{"id":"clm_7","policyId":"pol_3","ownerUserId":"u2","amount":1000,"status":"rejected","description":"Muayene masrafı","createdAt":"2026-06-11T13:00:00Z"}],"meta":{"page":1,"pageSize":20,"total":1}}
    ```
  - *(Ters yönde `tok_user2_mehmet` ile `GET /claims?policyId=pol_1` çağrıldığında da `u1`'e ait `clm_1` ve `clm_2` kayıtları `200 OK` ile dönmektedir.)*

---

### BUL-03: `GET /admin/stats` Ucuna Normal Kullanıcıların Erişebilmesi (BFLA)
- **Önem Derecesi:** Yüksek
- **Etkilenen Uç:** `GET /admin/stats`
- **Sözleşmeye Atıf:** `openapi.yaml` -> `tags: admin` (*"Yönetici işlemleri (yalnızca role=admin)"*) ve `GET /admin/stats` açıklaması (*"Sistem genel istatistiklerini döner. Yalnızca role=admin erişebilir; normal kullanıcı için 403 dönülmelidir"*).
- **Beklenen Davranış:** Normal kullanıcı token'ları (`tok_user1_ayse`, `tok_user2_mehmet`) ile `GET /admin/stats` isteği yapıldığında `403 Forbidden` dönülmelidir.
- **Gerçekleşen Davranış:** `GET /admin/policies` ucu `403` dönerken, `GET /admin/stats` ucu rol kontrolü yapmamakta ve tüm normal kullanıcılara `200 OK` ile şirket geneli toplam poliçe, hasar ve prim bilgilerini döndürmektedir.
- **Tekrar Üretim Adımları (`TK-20`):**
  - **İstek:** `GET http://localhost:4109/admin/stats`
  - **Token:** `Authorization: Bearer tok_user1_ayse` (veya `tok_user2_mehmet`)
  - **Gözlenen Yanıt (`200 OK`):**
    ```json
    {"totalPolicies":5,"totalClaims":7,"totalPremium":9800}
    ```

---

### BUL-04: `PATCH /policies/{id}` İle Salt Okunur `status` Alanının Değiştirilebilmesi ve Geçersiz Değer Kabulü
- **Önem Derecesi:** Yüksek
- **Etkilenen Uç:** `PATCH /policies/{id}`
- **Sözleşmeye Atıf:** `openapi.yaml` -> `PATCH /policies/{id}` açıklaması (*"Poliçe sahibi YALNIZCA `holderName` ve `agentName` alanlarını güncelleyebilir. `premium`, `coverageLimit`, `status`, `ownerUserId`, `policyNumber`, `coverageType` alanları salt okunurdur ve istek gövdesiyle DEĞİŞTİRİLEMEZ; bu alanlar gövdede gönderilse bile yok sayılmalıdır. Poliçenin durumu (`status`) yalnızca iç iş süreçleriyle değişir"*) ve `Policy.status` enum'u (`[active, cancelled, expired, pending]`).
- **Beklenen Davranış:** Gövdede `status` alanı gönderilse bile yok sayılmalı ve poliçenin durumu değişmemelidir.
- **Gerçekleşen Davranış:** `premium`, `coverageLimit`, `ownerUserId`, `policyNumber` ve `coverageType` alanları yok sayılırken, **`status` alanı güncellenmektedir**. Bir kullanıcı iptal edilmiş (`cancelled`) poliçesini `active` yapabilmekte, aktif poliçesini `cancelled` yapabilmekte, hatta `enum` dışı keyfi bir metin (`"hacked_status"`) dahi atayabilmektedir.
- **Tekrar Üretim Adımları (`TK-26`, `TK-27`, `TK-28`):**
  - **İstek 1:** `PATCH http://localhost:4109/policies/pol_3` (`pol_3` başlangıçta `"status":"cancelled"`)
  - **Token:** `Authorization: Bearer tok_user2_mehmet`
  - **Gövde:** `{"status":"active"}` -> **Gözlenen Yanıt (`200 OK`):** `"status":"active"` olarak güncellendi.
  - **İstek 2:** Aynı uç ve token ile **Gövde:** `{"status":"hacked_status"}` -> **Gözlenen Yanıt (`200 OK`):**
    ```json
    {"id":"pol_3","policyNumber":"POL-2026-0003","ownerUserId":"u2","holderName":"Mehmet Demir","holderTckn":"22222222220","coverageType":"saglik","premium":900,"coverageLimit":20000,"status":"hacked_status","agentName":"Can Öz","startDate":"2026-01-10","endDate":"2026-07-10"}
    ```

---

### BUL-05: `POST /claims` İle Teminat Limiti (`coverageLimit`) Aşımının Engellenmemesi
- **Önem Derecesi:** Yüksek
- **Etkilenen Uç:** `POST /claims`
- **Sözleşmeye Atıf:** `openapi.yaml` -> `POST /claims` açıklaması ve `'422'` yanıtı (*"İş kuralı: Bir hasar talebinin tutarı (`amount`), ilgili poliçenin teminat limitini (`coverageLimit`) AŞAMAZ. Aşan istekler 422 ile reddedilmelidir"*).
- **Beklenen Davranış:** `coverageLimit` değeri `50000` olan `pol_1` poliçesi için `amount > 50000` gönderildiğinde istek `422` (`Error` şeması) ile reddedilmelidir.
- **Gerçekleşen Davranış:** Hem `50001` hem de `50000.01` tutarlı hasar talepleri hiçbir limit kontrolüne takılmadan kabul edilip kaydedilmektedir.
- **Tekrar Üretim Adımları (`TK-33`, `TK-34`):**
  - **İstek:** `POST http://localhost:4109/claims`
  - **Token:** `Authorization: Bearer tok_user1_ayse`
  - **Başlık:** `Content-Type: application/json`
  - **Gövde:** `{"policyId":"pol_1","amount":50001,"description":"Limit aşımı testi"}`
  - **Gözlenen Yanıt (`200 OK`):**
    ```json
    {"id":"clm_16","policyId":"pol_1","ownerUserId":"u1","amount":50001,"status":"submitted","description":"Limit aşımı testi","createdAt":"2026-08-01T00:00:00Z"}
    ```

---

### BUL-06: `POST /claims` İsteğinde `Idempotency-Key` Başlığının Yok Sayılması
- **Önem Derecesi:** Yüksek
- **Etkilenen Uç:** `POST /claims`
- **Sözleşmeye Atıf:** `openapi.yaml` -> `POST /claims` açıklaması ve `Idempotency-Key` parametresi (*"İstek `Idempotency-Key` başlığı ile gönderilirse, aynı anahtarla yapılan tekrar istekleri YENİ kayıt OLUŞTURMAMALI, ilk oluşturulan kaydı aynen döndürmelidir"*).
- **Beklenen Davranış:** Aynı `Idempotency-Key` ile tekrarlanan istekte yeni kayıt oluşturulmamalı ve ilk oluşturulan kaydın ID/içeriği aynen döndürülmelidir.
- **Gerçekleşen Davranış:** Hem `Idempotency-Key` hem küçük harfli `idempotency-key` başlığı tamamen yok sayılmakta ve her tekrar isteğinde farklı `id` ile yeni bir hasar kaydı oluşturulmaktadır.
- **Tekrar Üretim Adımları (`TK-43`, `TK-44`):**
  - **İstek (2 kez art arda gönderilir):** `POST http://localhost:4109/claims`
  - **Token:** `Authorization: Bearer tok_user1_ayse`
  - **Başlıklar:** `Content-Type: application/json`, `Idempotency-Key: idem-key-qa-001`
  - **Gövde:** `{"policyId":"pol_2","amount":500,"description":"Idempotency test 1"}`
  - **Gözlenen Yanıtlar:**
    - 1. istek (`200`): `{"id":"clm_18","policyId":"pol_2","ownerUserId":"u1","amount":500,"status":"submitted","description":"Idempotency test 1","createdAt":"2026-08-01T00:00:00Z"}`
    - 2. istek (`200`): `{"id":"clm_19","policyId":"pol_2","ownerUserId":"u1","amount":500,"status":"submitted","description":"Idempotency test 1","createdAt":"2026-08-01T00:00:00Z"}`

---

### BUL-07: Hatalı JSON Girdisinde İç Yığın İzi (Stack Trace) ve Sunucu Dosya Yolunun İfşası
- **Önem Derecesi:** Orta
- **Etkilenen Uçlar:** `POST /claims`, `PATCH /policies/{id}`
- **Sözleşmeye Atıf:** `openapi.yaml` -> `BadRequest` / `Error` şeması (`required: [error]`, `properties: { error, message }`) ve güvenli hata yönetimi.
- **Beklenen Davranış:** Bozuk JSON veya JSON dışı içerik gönderildiğinde `400` yanıtı yalnızca kullanıcıya güvenli `{ "error": ..., "message": ... }` bilgisini döndürmelidir.
- **Gerçekleşen Davranış:** `400` hata yanıtında `detail` ve `stack` alanları yer almakta; sunucunun kullandığı teknoloji (`Node.js`), kaynak dosyanın tam yolu ve hata satır numaraları dışarıya sızdırılmaktadır.
- **Tekrar Üretim Adımları (`TK-50`, `TK-51`):**
  - **İstek:** `POST http://localhost:4109/claims` (veya `PATCH http://localhost:4109/policies/pol_1`)
  - **Token:** `Authorization: Bearer tok_user1_ayse`
  - **Başlık:** `Content-Type: application/json`
  - **Ham Gövde:** `{bad json`
  - **Gözlenen Yanıt (`400 Bad Request`):**
    ```json
    {"error":"Geçersiz JSON","detail":"Expected property name or '}' in JSON at position 1 (line 1 column 2)","stack":"SyntaxError: Expected property name or '}' in JSON at position 1 (line 1 column 2)\n    at JSON.parse (<anonymous>)\n    at Server.<anonymous> (C:\\eval\\servers\\R15\\server.js:216:25)\n    at process.processTicksAndRejections (node:internal/process/task_queues:104:5)"}
    ```

---

### BUL-08: `POST /claims` Üzerinde `amount < 1` ve `description` Tip Doğrulamasının Eksikliği
- **Önem Derecesi:** Orta
- **Etkilenen Uç:** `POST /claims`
- **Sözleşmeye Atıf:** `openapi.yaml` -> `ClaimCreate` ve `Claim` şemaları: `amount` (`type: number, minimum: 1`, *"1'den küçük olamaz"*), `description` (`type: ['string', 'null']`).
- **Beklenen Davranış:** `amount` için `1`'den küçük değerler (`0`, `-500`, `0.5`, `0.99`) ve `description` için string/null dışı tipler (`123`, `true`, `["a"]`, `{"a":1}`) `400 Bad Request` ile reddedilmelidir.
- **Gerçekleşen Davranış:** `amount` için `0`, `-500` (negatif tutar), `0.5` ve `0.99` değerleri `200` ile kaydedilmektedir. `description` alanına sayı, boolean, dizi veya nesne gönderildiğinde de hata dönmek yerine sessizce `""` (boş string) kaydedilmektedir.
- **Tekrar Üretim Adımları (`TK-37`, `TK-38`, `TK-39`, `TK-40`):**
  - **İstek:** `POST http://localhost:4109/claims`
  - **Token:** `Authorization: Bearer tok_user1_ayse`
  - **Gövde:** `{"policyId":"pol_1","amount":-500}`
  - **Gözlenen Yanıt (`200 OK`):**
    ```json
    {"id":"clm_13","policyId":"pol_1","ownerUserId":"u1","amount":-500,"status":"submitted","description":"","createdAt":"2026-08-01T00:00:00Z"}
    ```

---

### BUL-09: `GET /claims` Sayfalama Yanıtında `meta.total` Değerinin Yanlış Hesaplanması
- **Önem Derecesi:** Orta
- **Etkilenen Uç:** `GET /claims`
- **Sözleşmeye Atıf:** `openapi.yaml` -> `GET /claims` açıklaması ve `PageMeta.total` (*"Yanıttaki `meta.total` alanı, sayfalama uygulanmadan önceki TOPLAM (tüm sayfalardaki) kayıt sayısını belirtir; yalnızca geçerli sayfadaki kayıt sayısını değil"*).
- **Beklenen Davranış:** Başlangıçta 5 hasar kaydına sahip `u1` için `GET /claims?page=1&pageSize=2`, `page=3&pageSize=2` ve `page=4&pageSize=2` yanıtlarının tamamında `meta.total: 5` dönmelidir.
- **Gerçekleşen Davranış:** `meta.total` her zaman yalnızca geçerli sayfadaki eleman sayısını (`data.length`) döndürmektedir (`2`, `1`, `0`).
- **Tekrar Üretim Adımları (`TK-45`):**
  - **İstek:** `GET http://localhost:4109/claims?page=3&pageSize=2` (başlangıç verisinde `u1`'in 5 hasarı varken)
  - **Token:** `Authorization: Bearer tok_user1_ayse`
  - **Gözlenen Yanıt (`200 OK`):**
    ```json
    {"data":[{"id":"clm_5","policyId":"pol_2","ownerUserId":"u1","amount":2000,"status":"submitted","description":"Hırsızlık","createdAt":"2026-07-03T16:05:00Z"}],"meta":{"page":3,"pageSize":2,"total":1}}
    ```

---

### BUL-10: `GET /claims` Sayfalama Parametrelerinin (`page`, `pageSize`) Doğrulanmaması ve Şema İhlali
- **Önem Derecesi:** Orta
- **Etkilenen Uç:** `GET /claims`
- **Sözleşmeye Atıf:** `openapi.yaml` -> `GET /claims` parametreleri (`page: { type: integer, minimum: 1, default: 1 }`, `pageSize: { type: integer, minimum: 1, maximum: 100, default: 20 }`) ve `PageMeta` şeması (`page: integer`, `pageSize: integer`).
- **Beklenen Davranış:** Tamsayı olmayan veya `minimum`/`maximum` sınırları dışındaki `page` / `pageSize` değerleri reddedilmeli (veya güvenli varsayılanlara çekilmeli) ve `meta.page` / `meta.pageSize` alanları daima `integer` olmalıdır.
- **Gerçekleşen Davranış:**
  - `page=abc` veya `pageSize=abc` gönderildiğinde `200 OK` dönmekte ve `meta.page: null` / `meta.pageSize: null` üretilerek `PageMeta` (`type: integer`) şeması ihlal edilmektedir.
  - `page=-1&pageSize=2` ile `meta.page: -1` ve negatif dizi dilimlemesi sonucu tutarsız kayıtlar (`clm_2`, `clm_3`) dönmektedir.
  - `pageSize=101` (`maximum: 100` üzeri), `page=0`, `pageSize=0`, `pageSize=-5` değerleri de engellenmeden `200 OK` ile kabul edilmektedir.
- **Tekrar Üretim Adımları (`TK-46`, `TK-47`):**
  - **İstek 1:** `GET http://localhost:4109/claims?page=abc&pageSize=2` (`tok_user1_ayse`)
    - **Gözlenen Yanıt (`200 OK`):** `{"data":[],"meta":{"page":null,"pageSize":2,"total":0}}`
  - **İstek 2:** `GET http://localhost:4109/claims?page=-1&pageSize=2` (`tok_user1_ayse`)
    - **Gözlenen Yanıt (`200 OK`):** `clm_2` ve `clm_3` kayıtlarıyla birlikte `"meta":{"page":-1,"pageSize":2,"total":2}`

---

### BUL-11: `Claim` Nesnelerinde Zorunlu `claimNumber` Alanının Eksik Olması
- **Önem Derecesi:** Orta
- **Etkilenen Uçlar:** `GET /claims`, `GET /claims/{id}`, `POST /claims`
- **Sözleşmeye Atıf:** `openapi.yaml` -> `Claim` şeması (`required: [id, claimNumber, policyId, ownerUserId, amount, status, createdAt]`).
- **Beklenen Davranış:** Dönen tüm `Claim` nesnelerinde `claimNumber` alanı (ör. `"CLM-2026-0001"`) zorunlu olarak bulunmalıdır.
- **Gerçekleşen Davranış:** Başlangıçtaki (`clm_1`..`clm_7`) ve `POST /claims` ile yeni oluşturulan hasar kayıtlarının hiçbirinde `claimNumber` alanı yer almamaktadır.
- **Tekrar Üretim Adımları (`TK-31`):**
  - **İstek:** `GET http://localhost:4109/claims/clm_1`
  - **Token:** `Authorization: Bearer tok_user1_ayse`
  - **Gözlenen Yanıt (`200 OK`):**
    ```json
    {"id":"clm_1","policyId":"pol_1","ownerUserId":"u1","amount":12000,"status":"submitted","description":"Çarpma hasarı","createdAt":"2026-05-02T09:00:00Z"}
    ```

---

### BUL-12: `PATCH /policies/{id}` İsteğinde `holderName` ve `agentName` Tip / `null` Doğrulamasının Eksikliği
- **Önem Derecesi:** Orta
- **Etkilenen Uç:** `PATCH /policies/{id}`
- **Sözleşmeye Atıf:** `openapi.yaml` -> `PolicyUpdate` ve `Policy` şemaları (`holderName: { type: string }`, `agentName: { type: ['string', 'null'] }`).
- **Beklenen Davranış:** `holderName` için `null` veya sayı (`123`), `agentName` için sayı (`123`) gönderildiğinde `400 Bad Request` dönülmelidir (`holderName` nullable değildir).
- **Gerçekleşen Davranış:** `{"holderName": null}`, `{"holderName": 123}` ve `{"agentName": 123}` istekleri `200 OK` ile kabul edilip poliçe verisine kalıcı olarak yazılmaktadır.
- **Tekrar Üretim Adımları (`TK-29`):**
  - **İstek:** `PATCH http://localhost:4109/policies/pol_1`
  - **Token:** `Authorization: Bearer tok_user1_ayse`
  - **Gövde:** `{"holderName":null}` ardından `{"holderName":123,"agentName":123}`
  - **Gözlenen Yanıt (`200 OK`):** Poliçe `"holderName":null` ve ardından `"holderName":123,"agentName":123` değerleriyle güncellendi.

---

### BUL-13: `POST /claims` Başarılı Yanıtında `201 Created` Yerine `200 OK` Dönülmesi
- **Önem Derecesi:** Düşük
- **Etkilenen Uç:** `POST /claims`
- **Sözleşmeye Atıf:** `openapi.yaml` -> `POST /claims` `responses`: başarı durumu olarak yalnızca `'201'` (*"Oluşturulan hasar talebi"*) tanımlanmıştır.
- **Beklenen Davranış:** Yeni hasar talebi oluşturulduğunda HTTP `201 Created` dönülmelidir.
- **Gerçekleşen Davranış:** Tüm başarılı `POST /claims` çağrıları HTTP `200 OK` dönmektedir.
- **Tekrar Üretim Adımları (`TK-32`):**
  - **İstek:** `POST http://localhost:4109/claims`
  - **Token:** `Authorization: Bearer tok_user1_ayse`
  - **Gövde:** `{"policyId":"pol_1","amount":50000,"description":"Tam limit testi"}`
  - **Gözlenen Yanıt:** Durum kodu `201` yerine `200 OK`.

---

## Doğru Çalıştığı Doğrulanan Alanlar (Özet)

Olumsuz bulguların yanında aşağıdaki kontrollerin sözleşmeye uygun çalıştığı gözlenmiştir:
- `/health` hariç tüm uçlar geçersiz/eksik/hatalı `Authorization` başlıklarında tutarlı şekilde `401` (`Error` şeması) dönmektedir (`TK-01`–`TK-07`).
- `GET /policies`, `GET /policies/{id}`, `GET /claims/{id}`, `PATCH /policies/{id}`, `POST /claims` ve `GET /admin/policies` uçlarında sahiplik ve yönetici yetki kontrolleri (`403` / `404`) doğru çalışmaktadır (`TK-08`–`TK-14`, `TK-17`–`TK-19`).
- `PATCH /policies/{id}` üzerinde `status` dışındaki salt okunur alanlar (`premium`, `coverageLimit`, `ownerUserId`, `policyNumber`, `coverageType`) korunmaktadır (`TK-25`, `TK-26`).
- `POST /claims` gövdesinde `status` / `ownerUserId` gibi alanlarla yetki/durum ataması (`TK-42`), `__proto__` kirlenmesi (`TK-57`) ve yol geçişi / dizi sorgu parametresi enjeksiyonları (`TK-58`, `TK-59`) engellenmektedir.
