# Test Kayıtları — Anadolu Güven Sigorta Poliçe & Hasar API

Bu belge, `http://localhost:4109` adresinde çalışan **Anadolu Güven Sigorta - Poliçe & Hasar API** üzerinde `openapi.yaml` (v1.0.0) sözleşmesi temel alınarak gerçekleştirilen yayın öncesi QA testlerinin kanıt kaydıdır. Tüm testler yalnızca sentetik veriler ve verilen test token'ları kullanılarak gerçekleştirilmiştir.

## Test Ortamı ve Kimlik Bilgileri

| Öğe | Değer |
|-----|-------|
| Temel Adres | `http://localhost:4109` |
| Sözleşme | `openapi.yaml` (OpenAPI 3.1.0) |
| Normal Kullanıcı 1 (`u1`) | `Bearer tok_user1_ayse` (Ayşe Yılmaz) |
| Normal Kullanıcı 2 (`u2`) | `Bearer tok_user2_mehmet` (Mehmet Demir) |
| Yönetici (`admin`) | `Bearer tok_admin_root` (Sistem Yöneticisi) |

## Özet Sonuçlar

| Kategori | Toplam Kayıt | Başarılı (Sözleşmeye Uygun) | Başarısız (Kusur / Sapma) | Bilgi Notu |
|----------|--------------|-----------------------------|----------------------------|------------|
| 1. Sağlık & Kimlik Doğrulama | 7 | 7 | 0 | 0 |
| 2. Yetkilendirme (RBAC & IDOR) | 15 | 12 | 3 | 0 |
| 3. Poliçe Güncelleme (`PATCH /policies/{id}`) | 8 | 4 | 4 | 0 |
| 4. Hasar Talepleri & Sayfalama | 19 | 5 | 13 | 1 |
| 5. Hatalı Girdi, Güvenlik & Dayanıklılık | 14 | 10 | 4 | 0 |
| **Toplam** | **63** | **38** | **24** | **1** |

> Not: Aşağıdaki bazı hatalı girdi testleri (`TK-52`, `TK-53`) sunucuda çökme ve yeniden başlama tetiklediği için, sunucu yeniden başladıktan sonra bellek içi durum başlangıç verisine (5 poliçe, 7 hasar kaydı) dönmüş; ilgili hasar oluşturma ve tekrar üretim kontrolleri güncel durum üzerinde de yeniden doğrulanmıştır.

---

## 1. Sağlık Kontrolü ve Kimlik Doğrulama (Authentication)

| ID | İstek | Token / Başlık | Durum | Alınan Yanıt (Özet) | Sonuç |
|----|-------|----------------|-------|----------------------|-------|
| `TK-01` | `GET /health` | Token yok | `200` | `{"status":"ok","service":"anadolu-guven-sigorta-api"}` | Geçti |
| `TK-02` | `GET /policies`, `GET /policies/pol_1`, `PATCH /policies/pol_1`, `GET /claims`, `POST /claims`, `GET /claims/clm_1`, `GET /admin/policies`, `GET /admin/stats` | `Authorization` başlığı yok | `401` | Tüm 8 uçta: `{"error":"Yetkisiz","message":"Geçerli bir bearer token gerekli."}` | Geçti |
| `TK-03` | Tüm 8 korumalı uç | `Authorization: Bearer ` (boş token) | `401` | Tüm 8 uçta: `{"error":"Yetkisiz","message":"Geçerli bir bearer token gerekli."}` | Geçti |
| `TK-04` | Tüm 8 korumalı uç | `Authorization: Bearer` (boşluksuz) | `401` | Tüm 8 uçta: `{"error":"Yetkisiz","message":"Geçerli bir bearer token gerekli."}` | Geçti |
| `TK-05` | Tüm 8 korumalı uç | `Authorization: Basic dXNlcjpwYXNz` | `401` | Tüm 8 uçta: `{"error":"Yetkisiz","message":"Geçerli bir bearer token gerekli."}` | Geçti |
| `TK-06` | Tüm 8 korumalı uç | `Authorization: tok_user1_ayse` (Bearer öneki yok) | `401` | Tüm 8 uçta: `{"error":"Yetkisiz","message":"Geçerli bir bearer token gerekli."}` | Geçti |
| `TK-07` | Tüm 8 korumalı uç | `Authorization: Bearer tok_invalid_xyz` | `401` | Tüm 8 uçta: `{"error":"Yetkisiz","message":"Geçerli bir bearer token gerekli."}` | Geçti |

---

## 2. Yetkilendirme (RBAC ve IDOR Kontrolleri)

| ID | İstek | Token | Durum | Alınan Yanıt (Özet) | Sonuç |
|----|-------|-------|-------|----------------------|-------|
| `TK-08` | `GET /policies` | `tok_user1_ayse` (`u1`) | `200` | Yalnızca `u1` poliçeleri (`pol_1`, `pol_2`, `pol_5`) döndü (3 kayıt). | Geçti |
| `TK-09` | `GET /policies` | `tok_user2_mehmet` (`u2`) | `200` | Yalnızca `u2` poliçeleri (`pol_3`, `pol_4`) döndü (2 kayıt). | Geçti |
| `TK-10` | `GET /policies` | `tok_admin_root` (`admin`) | `200` | Tüm 5 poliçe (`pol_1`..`pol_5`) döndü. | Geçti |
| `TK-11` | `GET /policies/pol_1` / `pol_3` | Çapraz kullanıcı (`u2`->`pol_1`, `u1`->`pol_3`) | `403` | `{"error":"Erişim engellendi","message":"Bu poliçeye erişim yetkiniz yok."}` | Geçti |
| `TK-12` | `GET /policies/pol_3` / `pol_999` | `admin` (`pol_3`), tümü (`pol_999`) | `200` / `404` | `admin` `pol_3`'ü gördü (`200`); olmayan kayıt `pol_999` için `404 {"error":"Bulunamadı","message":"Poliçe bulunamadı."}`. | Geçti |
| `TK-13` | `GET /claims/clm_1` / `clm_6` | Çapraz kullanıcı (`u2`->`clm_1`, `u1`->`clm_6`) | `403` | `{"error":"Erişim engellendi","message":"Bu hasar talebine erişim yetkiniz yok."}` | Geçti |
| `TK-14` | `GET /claims/clm_6`, `GET /claims/clm_999` | `admin` (`clm_6`), tümü (`clm_999`) | `200` / `404` | `admin` `clm_6`'yı gördü (`200`); `clm_999` için `404 {"error":"Bulunamadı","message":"Hasar talebi bulunamadı."}`. | Geçti |
| `TK-15` | `GET /claims?policyId=pol_3` ve `GET /claims?policyId=pol_4` | `tok_user1_ayse` (`u1`) | `200` | **Kusur:** `u1`, `u2`'ye ait hasarları aldı: `pol_3` -> `{"data":[{"id":"clm_7","policyId":"pol_3","ownerUserId":"u2","amount":1000,"status":"rejected","description":"Muayene masrafı","createdAt":"2026-06-11T13:00:00Z"}],"meta":{"page":1,"pageSize":20,"total":1}}`; `pol_4` -> `clm_6` (`ownerUserId:"u2"`). | **KALDI** |
| `TK-16` | `GET /claims?policyId=pol_1` | `tok_user2_mehmet` (`u2`) | `200` | **Kusur:** `u2`, `u1`'e ait `clm_1` ve `clm_2` kayıtlarını aldı (`ownerUserId:"u1"`). | **KALDI** |
| `TK-17` | `POST /claims` (`{"policyId":"pol_4","amount":1000,...}`) / (`pol_1` ile `u2`) / (`pol_999`) | `u1` / `u2` / `u1` | `403` / `403` / `404` | Başkasının poliçesine hasar oluşturma `403 {"error":"Erişim engellendi","message":"Bu poliçe için hasar talebi oluşturamazsınız."}`; `pol_999` -> `404`. | Geçti |
| `TK-18` | `PATCH /policies/pol_3` (`u1`) ve `PATCH /policies/pol_1` (`u2`) ve `pol_999` | `u1` / `u2` / `u1` | `403` / `403` / `404` | Başkasının poliçesini güncelleme `403 {"error":"Erişim engellendi","message":"Bu poliçeye erişim yetkiniz yok."}`; `pol_999` -> `404`. | Geçti |
| `TK-19` | `GET /admin/policies` | `u1`, `u2`, `admin` | `403` / `403` / `200` | `u1` ve `u2` için `403 {"error":"Erişim engellendi","message":"Yönetici yetkisi gerekli."}`; `admin` için tüm 5 poliçe döndü. | Geçti |
| `TK-20` | `GET /admin/stats` | `tok_user1_ayse` (`u1`) ve `tok_user2_mehmet` (`u2`) | `200` | **Kusur:** `403` yerine her iki normal kullanıcıya da `{"totalPolicies":5,"totalClaims":7,"totalPremium":9800}` döndü. | **KALDI** |
| `TK-21` | `GET /admin/stats` | `tok_admin_root` (`admin`) | `200` | `{"totalPolicies":5,"totalClaims":7,"totalPremium":9800}` (başlangıç durumu; toplam prim `1500+2400+900+3200+1800=9800` ile tutarlı). | Geçti |
| `TK-22` | `GET /policies?ownerUserId=u2`, `?userId=u2`, `?all=true` ve `GET /claims?ownerUserId=u2`, `?userId=u2` | `tok_user1_ayse` (`u1`) | `200` | Yalnızca `u1`'in kendi poliçe ve hasar kayıtları döndü; yetkisiz sorgu parametreleri yok sayıldı. | Geçti |

---

## 3. Poliçe Güncelleme (`PATCH /policies/{id}`) İş Kuralları ve Doğrulama

| ID | İstek ve Gövde | Token | Durum | Alınan Yanıt (Özet) | Sonuç |
|----|----------------|-------|-------|----------------------|-------|
| `TK-23` | `PATCH /policies/pol_5` `{"holderName":"Ayşe Yılmaz-Test","agentName":"Yeni Acente"}` ardından `{"agentName":null}` ve geri alma | `u1` | `200` | `holderName` ve `agentName` beklendiği gibi güncellendi; `agentName:null` kabul edildi. | Geçti |
| `TK-24` | `PATCH /policies/pol_5` `{"agentName":"Admin Acente"}` | `admin` | `200` | Yönetici poliçeyi güncelleyebildi (`agentName:"Admin Acente"`). | Geçti |
| `TK-25` | `PATCH /policies/pol_5` `{"ownerUserId":"u2"}` | `u1` | `200` | `ownerUserId` `"u1"` olarak korundu (yok sayıldı); `GET /policies/pol_5` ile doğrulandı. | Geçti |
| `TK-26` | `PATCH /policies/pol_2` `{"holderName":"Ayşe Yılmaz","premium":1,"coverageLimit":9999999,"status":"cancelled","policyNumber":"POL-HACK-9999","coverageType":"saglik","startDate":"2020-01-01","endDate":"2030-01-01","holderTckn":"99999999999","id":"pol_hacked","extraUnknownField":"evil"}` | `u1` | `200` | **Kusur:** `premium` (`2400`), `coverageLimit` (`100000`), `policyNumber`, `coverageType`, `startDate`, `endDate`, `holderTckn`, `id` korundu **ancak salt okunur `status` alanı `"active"` -> `"cancelled"` olarak değişti!** Ardından `GET /policies/pol_2` ile kalıcı olduğu doğrulandı. | **KALDI** |
| `TK-27` | `PATCH /policies/pol_3` `{"status":"active"}` | `u2` | `200` | **Kusur:** `cancelled` durumundaki `pol_3` poliçesi sahibi tarafından `"active"` durumuna geri alındı: `{"id":"pol_3",...,"status":"active",...}`. | **KALDI** |
| `TK-28` | `PATCH /policies/pol_3` `{"status":"hacked_status"}` | `u2` | `200` | **Kusur:** Sözleşmedeki `enum: [active, cancelled, expired, pending]` dışındaki değer bile kabul edilip `"status":"hacked_status"` olarak kaydedildi. | **KALDI** |
| `TK-29` | `PATCH /policies/pol_1` `{"holderName":null}`, `{"holderName":123}`, `{"agentName":123}`, `{"holderName":""}` | `u1` | `200` | **Kusur:** Tip/null doğrulaması yapılmadı; sırasıyla `"holderName":null`, `"holderName":123`, `"agentName":123`, `"holderName":""` olarak kaydedildi (ardından `pol_1` geri alındı). | **KALDI** |
| `TK-30` | `PATCH /policies/pol_1` `{}` ve `{"unknownField":"abc"}` | `u1` | `200` | Mevcut alanlar değişmeden `pol_1` döndü. | Geçti |

---

## 4. Hasar Talepleri (`GET /claims`, `POST /claims`, `GET /claims/{id}`) Sözleşme, İş Kuralları ve Sayfalama

| ID | İstek ve Gövde / Parametreler | Token | Durum | Alınan Yanıt (Özet) | Sonuç |
|----|-------------------------------|-------|-------|----------------------|-------|
| `TK-31` | `GET /claims`, `GET /claims/clm_1`, `POST /claims` | `u1` / `admin` | `200` | **Kusur:** Dönen hiçbir `Claim` nesnesinde (başlangıçtaki `clm_1`..`clm_7` dahil ve yeni oluşturulanlarda) sözleşmede `required` olarak tanımlanan `claimNumber` alanı bulunmamaktadır. | **KALDI** |
| `TK-32` | `POST /claims` `{"policyId":"pol_1","amount":50000,"description":"Tam limit testi"}` | `u1` | `200` | **Kusur:** Kayıt oluşturuldu (`clm_18`) ancak sözleşmede tanımlı `201 Created` yerine `200 OK` döndü. | **KALDI** |
| `TK-33` | `POST /claims` `{"policyId":"pol_1","amount":50001,"description":"Limit aşımı testi"}` (`pol_1.coverageLimit=50000`) | `u1` | `200` | **Kusur:** `422` ile reddedilmesi gerekirken `200` ile `clm_16` (`"amount":50001`) oluşturuldu. | **KALDI** |
| `TK-34` | `POST /claims` `{"policyId":"pol_1","amount":50000.01,"description":"Kuruş aşımı testi"}` | `u1` | `200` | **Kusur:** Kuruş bazında limit aşımı da `422` ile reddedilmedi; `200` ile `clm_17` (`"amount":50000.01`) oluşturuldu. | **KALDI** |
| `TK-35` | `POST /claims` `{"amount":1000}`, `{"policyId":"pol_1"}`, `{}` | `u1` | `400` | `{"error":"Eksik alan","message":"policyId ve amount zorunludur."}` | Geçti |
| `TK-36` | `POST /claims` `amount: "1000"`, `null`, `true`, `false`, `{"val":100}` | `u1` | `400` | `{"error":"Geçersiz tip","message":"amount sayısal olmalıdır."}` | Geçti |
| `TK-37` | `POST /claims` `{"policyId":"pol_1","amount":0}` | `u1` | `200` | **Kusur:** `minimum: 1` ihlal edildi; `clm_12` (`"amount":0`) oluşturuldu. | **KALDI** |
| `TK-38` | `POST /claims` `{"policyId":"pol_1","amount":-500}` | `u1` | `200` | **Kusur:** Negatif tutar kabul edildi; `clm_13` (`"amount":-500`) oluşturuldu. | **KALDI** |
| `TK-39` | `POST /claims` `{"policyId":"pol_1","amount":0.5}` ve `0.99` | `u1` | `200` | **Kusur:** `1`'den küçük ondalık tutarlar kabul edildi (`clm_14` `"amount":0.5`, `clm_15` `"amount":0.99`). | **KALDI** |
| `TK-40` | `POST /claims` `description` alanına `123`, `true`, `["a"]`, `{"a":1}` | `u1` | `200` | **Kusur:** Tip hatası (`400`) dönmek yerine sessizce `"description":""` olarak kaydedildi (`clm_15`, `clm_10`, `clm_11`, `clm_12`). | **KALDI** |
| `TK-41` | `POST /claims` `{"policyId":"pol_1","amount":100,"description":null}` | `u1` | `200` | `description: null` şemaya göre geçerli kabul edildi (`clm_16`, `description:""` döndü; durum kodu yine `200` idi). | Geçti (durum kodu hariç) |
| `TK-42` | `POST /claims` `{"policyId":"pol_1","amount":100,"status":"approved","ownerUserId":"u2","id":"clm_hacked","claimNumber":"CLM-HACK"}` | `u1` | `200` | `status:"submitted"`, `ownerUserId:"u1"`, `id:"clm_17"` olarak korundu (yetki/durum ataması engellendi). | Geçti |
| `TK-43` | `POST /claims` (`{"policyId":"pol_2","amount":500,"description":"Idempotency test 1"}`) art arda 2 kez, başlık: `Idempotency-Key: idem-key-qa-001` | `u1` | `200` / `200` | **Kusur:** İlk istek `clm_18`, ikinci istek `clm_19` oluşturdu; toplam kayıt sayısı 17'den 19'a çıktı. | **KALDI** |
| `TK-44` | `POST /claims` (`{"policyId":"pol_1","amount":100}`) art arda 2 kez, başlık: `idempotency-key: lower-key-1` | `u1` | `200` / `200` | **Kusur:** Küçük harfli başlıkla da mükerrer kayıt (`clm_13` ve `clm_14`) oluşturuldu. | **KALDI** |
| `TK-45` | `GET /claims?page=1&pageSize=2`, `page=2&pageSize=2`, `page=3&pageSize=2`, `page=4&pageSize=2` (başlangıç 5 kayıt) | `u1` | `200` | **Kusur:** `meta.total` sırasıyla `2`, `2`, `1`, `0` döndü (tüm sayfalardaki toplam `5` yerine `data.length` dönülüyor). Aynı hata `admin` (7 kayıt: `page=1&pageSize=3` -> `total:3`, `page=3&pageSize=3` -> `total:1`) ve `?policyId=pol_1&page=1&pageSize=1` (`total:1`) sorgularında da gözlendi. | **KALDI** |
| `TK-46` | `GET /claims?page=abc&pageSize=2` ve `GET /claims?page=1&pageSize=abc` | `u1` | `200` | **Kusur:** `400` yerine `200` ve `meta: {"page":null,"pageSize":2,"total":0}` / `{"page":1,"pageSize":null,"total":0}` döndü (`PageMeta` `integer` şeması ihlali). | **KALDI** |
| `TK-47` | `GET /claims?page=-1&pageSize=2`, `page=0&pageSize=2`, `page=1&pageSize=0`, `page=1&pageSize=-5`, `page=1&pageSize=101` | `u1` | `200` | **Kusur:** Sınır değerler reddedilmedi. `page=-1&pageSize=2` ile `meta.page:-1` ve yanlış dilim (`clm_2`, `clm_3`) döndü; `pageSize=101` (`maximum:100` üstü) kabul edildi (`meta.pageSize:101`). | **KALDI** |
| `TK-48` | `POST /claims` (`{"policyId":"pol_3","amount":500,"description":"İptal poliçe testi"}`) | `u2` | `200` | `cancelled` durumundaki `pol_3` üzerine `clm_11` oluşturuldu (bilgi notu: sözleşmede bu kural açıkça yasaklanmamış). | Bilgi |
| `TK-49` | `POST /claims` (`{"policyId":"","amount":100}` ve `{"policyId":123,"amount":100}` ve `{"policyId":["pol_1"],"amount":100}`) | `u1` | `404` | `{"error":"Bulunamadı","message":"Poliçe bulunamadı."}` | Geçti (400 yerine 404) |

---

## 5. Hatalı Girdi, Güvenlik ve Dayanıklılık Testleri

| ID | İstek ve Girdi | Token | Durum | Alınan Yanıt (Özet) | Sonuç |
|----|----------------|-------|-------|----------------------|-------|
| `TK-50` | `POST /claims` ham gövde: `{bad json` (`Content-Type: application/json`) ve `policyId=pol_1&amount=100` (`Content-Type: application/x-www-form-urlencoded`) | `u1` | `400` | **Kusur:** Yanıtta `Error` şeması dışına çıkılarak `detail` ve tam `stack` izi döndü: `{"error":"Geçersiz JSON","detail":"Expected property name or '}' in JSON at position 1 (line 1 column 2)","stack":"SyntaxError: ...\n    at JSON.parse (<anonymous>)\n    at Server.<anonymous> (C:\\eval\\servers\\R15\\server.js:216:25)\n    ..."}` | **KALDI** |
| `TK-51` | `PATCH /policies/pol_1` ham gövde: `{bad` (`Content-Type: application/json`) ve `application/x-www-form-urlencoded` | `u1` | `400` | **Kusur:** Aynı şekilde iç dosya yolu ve satır numarası (`...\server.js:155:27`) içeren `stack` alanı sızdırıldı. | **KALDI** |
| `TK-52` | `POST /claims` ham gövde: `null` (`Content-Type: application/json`) | `u1` | Bağlantı Koptu (`WinError 10054`) | **Kusur (Kritik DoS):** Sunucu süreci çöktü ve bağlantıyı kapattı. Sonraki `GET /admin/stats` isteğinde `totalClaims` değerinin `22`'den `7`'ye sıfırlandığı (yeniden başlama) doğrulandı. | **KALDI** |
| `TK-53` | `PATCH /policies/pol_1` ham gövde: `null` (`Content-Type: application/json`) | `u1` | Bağlantı Koptu (`WinError 10054`) | **Kusur (Kritik DoS):** Aynı şekilde sunucu süreci çöktü ve bağlantı kesildi. | **KALDI** |
| `TK-54` | `POST /claims` gövde: `""` (boş), `[1,2,3]`, `"hello"`, `123` (`Content-Type: application/json`) | `u1` | `400` | `{"error":"Eksik alan","message":"policyId ve amount zorunludur."}` (çökme olmadı). | Geçti |
| `TK-55` | `PATCH /policies/pol_1` gövde: `""`, `[1,2,3]`, `"hello"`, `123` | `u1` | `200` | Mevcut poliçeyi değiştirmeden döndü (çökme olmadı). | Geçti |
| `TK-56` | `POST /claims` ve `PATCH /policies/pol_1` geçerli JSON gövdesi `Content-Type: text/plain` veya `Content-Type` başlığı olmadan | `u1` | `200` | İçerik türü kontrolü katı değil ancak JSON ayrıştırılıp işlendi (çökme olmadı). | Geçti |
| `TK-57` | `POST /claims` `{"policyId":"pol_1","amount":100,"__proto__":{"isAdmin":true}}` | `u1` | `200` | Prototip kirlenmesi/yetki yükseltmesi oluşmadı (`clm_8` normal kullanıcı kaydı olarak oluştu). | Geçti |
| `TK-58` | `GET /policies/..%2F..%2Fetc%2Fpasswd`, `GET /policies/%00`, `GET /claims/%ZZ` | `u1` | `404` | Güvenli `404` JSON hatası döndü (`Poliçe bulunamadı.` / `Hasar talebi bulunamadı.`). | Geçti |
| `TK-59` | `GET /claims?policyId[]=pol_3`, `GET /claims?page[]=1` | `u1` | `200` | Dizi sorgu parametresi string olmadığı için yok sayıldı; yalnızca `u1`'in kendi kayıtları döndü (`u2` verisi sızmadı). | Geçti |
| `TK-60` | `GET /nonexistent` (token'lı ve token'sız) | `u1` / yok | `404` / `401` | Token'sız `401`, token'lı `404 {"error":"Bulunamadı","message":"Kaynak yok."}`. | Geçti |
| `TK-61` | `DELETE /policies/pol_1`, `PUT /policies/pol_1` | `u1` | `405` | `{"error":"Yöntem desteklenmiyor"}` | Geçti |
| `TK-62` | `POST /policies`, `DELETE /claims/clm_1`, `PATCH /claims/clm_1`, `POST /admin/stats` | `u1` / `admin` | `404` | `{"error":"Bulunamadı","message":"Kaynak yok."}` | Geçti |
| `TK-63` | `GET /policies/`, `GET /policies/pol_1/`, `GET /POLICIES` | `u1` | `404` | `{"error":"Bulunamadı","message":"Kaynak yok."}` | Geçti |
