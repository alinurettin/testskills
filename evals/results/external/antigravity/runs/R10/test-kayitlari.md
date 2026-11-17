# Test Kayıtları ve Kanıt Günlüğü — Anadolu Güven Sigorta API

Bu belge, `http://localhost:4105` (`127.0.0.1:4105`) adresinde çalışan **Anadolu Güven Sigorta - Poliçe & Hasar API** üzerinde `openapi.yaml` (v1.0.0) sözleşmesine dayanılarak yürütülen yayın öncesi test koşumlarının kanıt kaydıdır.

> Tüm testlerde yalnızca `TASK.md` içinde verilen sentetik test token'ları ve kurgusal veriler kullanılmıştır.

## 1. Koşum Özeti

- **Hedef URL:** `http://127.0.0.1:4105` (`TASK.md`: `http://localhost:4105`)
- **Referans Sözleşme:** `openapi.yaml` (OpenAPI 3.1.0, 9 operasyon)
- **Toplam Gönderilen İstek:** 193
- **Durum Kodu Dağılımı:**
  - `200`: 122 istek
  - `400`: 16 istek
  - `401`: 16 istek
  - `403`: 13 istek
  - `404`: 16 istek
  - `405`: 2 istek
  - `201`: 0 istek *(Sözleşme `POST /claims` için `201` beklemesine rağmen sunucu `200` dönmektedir)*
  - `422`: 0 istek *(Teminat limiti aşımında beklenen `422` dönülmemiştir)*
  - Bağlantı kesilmesi / erişilememe (`-1`): 8 istek *(4 kez JSON `null` gövdesiyle kasıtlı yeniden üretilen sunucu çökmesi ve 4 kez çökme sonrası kısa yeniden başlatma penceresinde alınan `ConnectionRefusedError`)*

## 2. Test Hesapları ve Başlangıç Sentetik Veri Durumu

| Token | Kullanıcı ID | Rol | Başlangıç Poliçeleri | Başlangıç Hasarları |
|---|---|---|---|---|
| `tok_user1_ayse` | `u1` | normal kullanıcı | `pol_1` (kasko, limit 50.000, active), `pol_2` (konut, limit 100.000, active), `pol_5` (trafik, limit 75.000, active) | `clm_1`–`clm_5` (5 kayıt) |
| `tok_user2_mehmet` | `u2` | normal kullanıcı | `pol_3` (saglik, limit 20.000, **cancelled**), `pol_4` (kasko, limit 150.000, active) | `clm_6`, `clm_7` (2 kayıt) |
| `tok_admin_root` | `admin` | yönetici (`admin`) | Tüm poliçeler (5 kayıt, toplam prim 9.800) | Tüm hasarlar (7 kayıt) |

Programatik OpenAPI şema doğrulaması (`check_schemas.py`): Başlangıçtaki tüm `Policy` kayıtları (`pol_1`–`pol_5`) `openapi.yaml` şemasına uygundur; başlangıçtaki ve sonradan oluşturulan tüm `Claim` kayıtlarında ise `required` listesindeki `claimNumber` alanı eksiktir.

---

## 3. Faz 1 — Salt Okunur (Read-Only) Testler (`RO-01` – `RO-61`)

Kapsam: `/health`, `/policies`, `/policies/{id}`, `/claims`, `/claims/{id}`, `/admin/policies`, `/admin/stats` uçları; kimlik doğrulama başlığı varyasyonları, BOLA/BFLA kontrolleri, sayfalama (`page`, `pageSize`), `policyId` filtrelemesi ve desteklenmeyen yöntem/yol kontrolleri.

| ID | İstek | Yetkilendirme | İstek Gövdesi | HTTP | Yanıt Özeti |
|---|---|---|---|---|---|
| `RO-01` | `GET /health` | *(yok)* | — | **200** | `{"status":"ok","service":"anadolu-guven-sigorta-api"}` |
| `RO-02` | `GET /policies` | *(yok)* | — | **401** | `{"error":"Yetkisiz","message":"Geçerli bir bearer token gerekli."}` |
| `RO-03` | `GET /policies` | `tok_user1_ayse` | — | **401** | `{"error":"Yetkisiz","message":"Geçerli bir bearer token gerekli."}` |
| `RO-04` | `GET /policies` | `Basic tok_user1_ayse` | — | **401** | `{"error":"Yetkisiz","message":"Geçerli bir bearer token gerekli."}` |
| `RO-05` | `GET /policies` | `Bearer ` | — | **401** | `{"error":"Yetkisiz","message":"Geçerli bir bearer token gerekli."}` |
| `RO-06` | `GET /policies` | `Bearer invalid_token_xyz` | — | **401** | `{"error":"Yetkisiz","message":"Geçerli bir bearer token gerekli."}` |
| `RO-07` | `GET /policies` | `bearer tok_user1_ayse` | — | **200** | `[{"id":"pol_1","policyNumber":"POL-2026-0001","ownerUserId":"u1","holderName":"Ayşe Yılmaz","holderTckn":"11111111110","coverageType":"kasko","premium":1500,"coverageLimit":5000...` |
| `RO-08` | `GET /policies` | `Bearer  tok_user1_ayse` | — | **200** | `[{"id":"pol_1","policyNumber":"POL-2026-0001","ownerUserId":"u1","holderName":"Ayşe Yılmaz","holderTckn":"11111111110","coverageType":"kasko","premium":1500,"coverageLimit":5000...` |
| `RO-09` | `GET /policies` | `Bearer tok_user1_ayse` | — | **200** | `[{"id":"pol_1","policyNumber":"POL-2026-0001","ownerUserId":"u1","holderName":"Ayşe Yılmaz","holderTckn":"11111111110","coverageType":"kasko","premium":1500,"coverageLimit":5000...` |
| `RO-10` | `GET /policies` | `Bearer tok_user2_mehmet` | — | **200** | `[{"id":"pol_3","policyNumber":"POL-2026-0003","ownerUserId":"u2","holderName":"Mehmet Demir","holderTckn":"22222222220","coverageType":"saglik","premium":900,"coverageLimit":200...` |
| `RO-11` | `GET /policies` | `Bearer tok_admin_root` | — | **200** | `[{"id":"pol_1","policyNumber":"POL-2026-0001","ownerUserId":"u1","holderName":"Ayşe Yılmaz","holderTckn":"11111111110","coverageType":"kasko","premium":1500,"coverageLimit":5000...` |
| `RO-12` | `GET /policies/pol_1` | *(yok)* | — | **401** | `{"error":"Yetkisiz","message":"Geçerli bir bearer token gerekli."}` |
| `RO-13` | `GET /policies/pol_1` | `Bearer tok_user1_ayse` | — | **200** | `{"id":"pol_1","policyNumber":"POL-2026-0001","ownerUserId":"u1","holderName":"Ayşe Yılmaz","holderTckn":"11111111110","coverageType":"kasko","premium":1500,"coverageLimit":50000...` |
| `RO-14` | `GET /policies/pol_2` | `Bearer tok_user1_ayse` | — | **200** | `{"id":"pol_2","policyNumber":"POL-2026-0002","ownerUserId":"u1","holderName":"Ayşe Yılmaz","holderTckn":"11111111110","coverageType":"konut","premium":2400,"coverageLimit":10000...` |
| `RO-15` | `GET /policies/pol_3` | `Bearer tok_user1_ayse` | — | **403** | `{"error":"Erişim engellendi","message":"Bu poliçeye erişim yetkiniz yok."}` |
| `RO-16` | `GET /policies/pol_4` | `Bearer tok_user1_ayse` | — | **403** | `{"error":"Erişim engellendi","message":"Bu poliçeye erişim yetkiniz yok."}` |
| `RO-17` | `GET /policies/pol_1` | `Bearer tok_user2_mehmet` | — | **403** | `{"error":"Erişim engellendi","message":"Bu poliçeye erişim yetkiniz yok."}` |
| `RO-18` | `GET /policies/pol_1` | `Bearer tok_admin_root` | — | **200** | `{"id":"pol_1","policyNumber":"POL-2026-0001","ownerUserId":"u1","holderName":"Ayşe Yılmaz","holderTckn":"11111111110","coverageType":"kasko","premium":1500,"coverageLimit":50000...` |
| `RO-19` | `GET /policies/pol_3` | `Bearer tok_admin_root` | — | **200** | `{"id":"pol_3","policyNumber":"POL-2026-0003","ownerUserId":"u2","holderName":"Mehmet Demir","holderTckn":"22222222220","coverageType":"saglik","premium":900,"coverageLimit":2000...` |
| `RO-20` | `GET /policies/does-not-exist-000` | `Bearer tok_user1_ayse` | — | **404** | `{"error":"Bulunamadı","message":"Poliçe bulunamadı."}` |
| `RO-21` | `GET /policies/%27%20OR%20%271%27%3D%271` | `Bearer tok_user1_ayse` | — | **404** | `{"error":"Bulunamadı","message":"Poliçe bulunamadı."}` |
| `RO-22` | `GET /claims` | *(yok)* | — | **401** | `{"error":"Yetkisiz","message":"Geçerli bir bearer token gerekli."}` |
| `RO-23` | `GET /claims` | `Bearer tok_user1_ayse` | — | **200** | `{"data":[{"id":"clm_1","policyId":"pol_1","ownerUserId":"u1","amount":12000,"status":"submitted","description":"Çarpma hasarı","createdAt":"2026-05-02T09:00:00Z"},{"id":"clm_2",...` |
| `RO-24` | `GET /claims` | `Bearer tok_user2_mehmet` | — | **200** | `{"data":[{"id":"clm_6","policyId":"pol_4","ownerUserId":"u2","amount":5000,"status":"approved","description":"Çarpma hasarı","createdAt":"2026-05-18T10:20:00Z"},{"id":"clm_7","p...` |
| `RO-25` | `GET /claims` | `Bearer tok_admin_root` | — | **200** | `{"data":[{"id":"clm_1","policyId":"pol_1","ownerUserId":"u1","amount":12000,"status":"submitted","description":"Çarpma hasarı","createdAt":"2026-05-02T09:00:00Z"},{"id":"clm_2",...` |
| `RO-26` | `GET /claims?page=1&pageSize=2` | `Bearer tok_user1_ayse` | — | **200** | `{"data":[{"id":"clm_1","policyId":"pol_1","ownerUserId":"u1","amount":12000,"status":"submitted","description":"Çarpma hasarı","createdAt":"2026-05-02T09:00:00Z"},{"id":"clm_2",...` |
| `RO-27` | `GET /claims?page=2&pageSize=2` | `Bearer tok_user1_ayse` | — | **200** | `{"data":[{"id":"clm_3","policyId":"pol_2","ownerUserId":"u1","amount":3000,"status":"approved","description":"Su baskını","createdAt":"2026-06-01T08:15:00Z"},{"id":"clm_4","poli...` |
| `RO-28` | `GET /claims?page=3&pageSize=2` | `Bearer tok_user1_ayse` | — | **200** | `{"data":[{"id":"clm_5","policyId":"pol_2","ownerUserId":"u1","amount":2000,"status":"submitted","description":"Hırsızlık","createdAt":"2026-07-03T16:05:00Z"}],"meta":{"page":3,"...` |
| `RO-29` | `GET /claims?page=4&pageSize=2` | `Bearer tok_user1_ayse` | — | **200** | `{"data":[],"meta":{"page":4,"pageSize":2,"total":0}}` |
| `RO-30` | `GET /claims?page=0&pageSize=2` | `Bearer tok_user1_ayse` | — | **200** | `{"data":[],"meta":{"page":0,"pageSize":2,"total":0}}` |
| `RO-31` | `GET /claims?page=-1&pageSize=2` | `Bearer tok_user1_ayse` | — | **200** | `{"data":[{"id":"clm_2","policyId":"pol_1","ownerUserId":"u1","amount":8000,"status":"rejected","description":"Cam kırığı","createdAt":"2026-05-10T11:30:00Z"},{"id":"clm_3","poli...` |
| `RO-32` | `GET /claims?page=abc&pageSize=2` | `Bearer tok_user1_ayse` | — | **200** | `{"data":[],"meta":{"page":null,"pageSize":2,"total":0}}` |
| `RO-33` | `GET /claims?page=1&pageSize=0` | `Bearer tok_user1_ayse` | — | **200** | `{"data":[],"meta":{"page":1,"pageSize":0,"total":0}}` |
| `RO-34` | `GET /claims?page=1&pageSize=-5` | `Bearer tok_user1_ayse` | — | **200** | `{"data":[],"meta":{"page":1,"pageSize":-5,"total":0}}` |
| `RO-35` | `GET /claims?page=1&pageSize=100` | `Bearer tok_user1_ayse` | — | **200** | `{"data":[{"id":"clm_1","policyId":"pol_1","ownerUserId":"u1","amount":12000,"status":"submitted","description":"Çarpma hasarı","createdAt":"2026-05-02T09:00:00Z"},{"id":"clm_2",...` |
| `RO-36` | `GET /claims?page=1&pageSize=101` | `Bearer tok_user1_ayse` | — | **200** | `{"data":[{"id":"clm_1","policyId":"pol_1","ownerUserId":"u1","amount":12000,"status":"submitted","description":"Çarpma hasarı","createdAt":"2026-05-02T09:00:00Z"},{"id":"clm_2",...` |
| `RO-37` | `GET /claims?page=1&pageSize=abc` | `Bearer tok_user1_ayse` | — | **200** | `{"data":[],"meta":{"page":1,"pageSize":null,"total":0}}` |
| `RO-38` | `GET /claims?policyId=pol_1` | `Bearer tok_user1_ayse` | — | **200** | `{"data":[{"id":"clm_1","policyId":"pol_1","ownerUserId":"u1","amount":12000,"status":"submitted","description":"Çarpma hasarı","createdAt":"2026-05-02T09:00:00Z"},{"id":"clm_2",...` |
| `RO-39` | `GET /claims?policyId=pol_4` | `Bearer tok_user1_ayse` | — | **200** | `{"data":[{"id":"clm_6","policyId":"pol_4","ownerUserId":"u2","amount":5000,"status":"approved","description":"Çarpma hasarı","createdAt":"2026-05-18T10:20:00Z"}],"meta":{"page":...` |
| `RO-40` | `GET /claims?policyId=pol_3` | `Bearer tok_user1_ayse` | — | **200** | `{"data":[{"id":"clm_7","policyId":"pol_3","ownerUserId":"u2","amount":1000,"status":"rejected","description":"Muayene masrafı","createdAt":"2026-06-11T13:00:00Z"}],"meta":{"page...` |
| `RO-41` | `GET /claims?policyId=pol_1` | `Bearer tok_user2_mehmet` | — | **200** | `{"data":[{"id":"clm_1","policyId":"pol_1","ownerUserId":"u1","amount":12000,"status":"submitted","description":"Çarpma hasarı","createdAt":"2026-05-02T09:00:00Z"},{"id":"clm_2",...` |
| `RO-42` | `GET /claims?policyId=pol_999` | `Bearer tok_user1_ayse` | — | **200** | `{"data":[],"meta":{"page":1,"pageSize":20,"total":0}}` |
| `RO-43` | `GET /claims?policyId=pol_1&page=1&pageSize=1` | `Bearer tok_user1_ayse` | — | **200** | `{"data":[{"id":"clm_1","policyId":"pol_1","ownerUserId":"u1","amount":12000,"status":"submitted","description":"Çarpma hasarı","createdAt":"2026-05-02T09:00:00Z"}],"meta":{"page...` |
| `RO-44` | `GET /claims?page=1&pageSize=3` | `Bearer tok_admin_root` | — | **200** | `{"data":[{"id":"clm_1","policyId":"pol_1","ownerUserId":"u1","amount":12000,"status":"submitted","description":"Çarpma hasarı","createdAt":"2026-05-02T09:00:00Z"},{"id":"clm_2",...` |
| `RO-45` | `GET /claims/clm_1` | *(yok)* | — | **401** | `{"error":"Yetkisiz","message":"Geçerli bir bearer token gerekli."}` |
| `RO-46` | `GET /claims/clm_1` | `Bearer tok_user1_ayse` | — | **200** | `{"id":"clm_1","policyId":"pol_1","ownerUserId":"u1","amount":12000,"status":"submitted","description":"Çarpma hasarı","createdAt":"2026-05-02T09:00:00Z"}` |
| `RO-47` | `GET /claims/clm_6` | `Bearer tok_user1_ayse` | — | **403** | `{"error":"Erişim engellendi","message":"Bu hasar talebine erişim yetkiniz yok."}` |
| `RO-48` | `GET /claims/clm_1` | `Bearer tok_user2_mehmet` | — | **403** | `{"error":"Erişim engellendi","message":"Bu hasar talebine erişim yetkiniz yok."}` |
| `RO-49` | `GET /claims/clm_6` | `Bearer tok_admin_root` | — | **200** | `{"id":"clm_6","policyId":"pol_4","ownerUserId":"u2","amount":5000,"status":"approved","description":"Çarpma hasarı","createdAt":"2026-05-18T10:20:00Z"}` |
| `RO-50` | `GET /claims/clm_1` | `Bearer tok_admin_root` | — | **200** | `{"id":"clm_1","policyId":"pol_1","ownerUserId":"u1","amount":12000,"status":"submitted","description":"Çarpma hasarı","createdAt":"2026-05-02T09:00:00Z"}` |
| `RO-51` | `GET /claims/does-not-exist-000` | `Bearer tok_user1_ayse` | — | **404** | `{"error":"Bulunamadı","message":"Hasar talebi bulunamadı."}` |
| `RO-52` | `GET /admin/policies` | *(yok)* | — | **401** | `{"error":"Yetkisiz","message":"Geçerli bir bearer token gerekli."}` |
| `RO-53` | `GET /admin/policies` | `Bearer tok_user1_ayse` | — | **403** | `{"error":"Erişim engellendi","message":"Yönetici yetkisi gerekli."}` |
| `RO-54` | `GET /admin/policies` | `Bearer tok_user2_mehmet` | — | **403** | `{"error":"Erişim engellendi","message":"Yönetici yetkisi gerekli."}` |
| `RO-55` | `GET /admin/policies` | `Bearer tok_admin_root` | — | **200** | `[{"id":"pol_1","policyNumber":"POL-2026-0001","ownerUserId":"u1","holderName":"Ayşe Yılmaz","holderTckn":"11111111110","coverageType":"kasko","premium":1500,"coverageLimit":5000...` |
| `RO-56` | `GET /admin/stats` | *(yok)* | — | **401** | `{"error":"Yetkisiz","message":"Geçerli bir bearer token gerekli."}` |
| `RO-57` | `GET /admin/stats` | `Bearer tok_user1_ayse` | — | **200** | `{"totalPolicies":5,"totalClaims":7,"totalPremium":9800}` |
| `RO-58` | `GET /admin/stats` | `Bearer tok_user2_mehmet` | — | **200** | `{"totalPolicies":5,"totalClaims":7,"totalPremium":9800}` |
| `RO-59` | `GET /admin/stats` | `Bearer tok_admin_root` | — | **200** | `{"totalPolicies":5,"totalClaims":7,"totalPremium":9800}` |
| `RO-60` | `GET /nonexistent` | `Bearer tok_user1_ayse` | — | **404** | `{"error":"Bulunamadı","message":"Kaynak yok."}` |
| `RO-61` | `DELETE /policies/pol_1` | `Bearer tok_user1_ayse` | — | **405** | `{"error":"Yöntem desteklenmiyor"}` |

---

## 4. Faz 2A — `PATCH /policies/{id}` Doğrulama, Mass Assignment ve Güvenlik (`PAT-01` – `PAT-34`)

Kapsam: Yetkilendirme (401/403), 404, geçerli güncelleme ve kalıcılık, hatalı veri tipleri, bozuk JSON, salt okunur alanların (`premium`, `coverageLimit`, `status`, `ownerUserId`, `policyNumber`, `coverageType`, `holderTckn`, `id`, `startDate`, `endDate`) tek tek değiştirilme denemeleri, SQLi/XSS yoklamaları.

| ID | İstek | Yetkilendirme | İstek Gövdesi | HTTP | Yanıt Özeti |
|---|---|---|---|---|---|
| `PAT-01` | `PATCH /policies/pol_2` | *(yok)* | `{"holderName": "Test"}` | **401** | `{"error":"Yetkisiz","message":"Geçerli bir bearer token gerekli."}` |
| `PAT-02` | `PATCH /policies/pol_2` | `Bearer tok_user2_mehmet` | `{"holderName": "Hack"}` | **403** | `{"error":"Erişim engellendi","message":"Bu poliçeye erişim yetkiniz yok."}` |
| `PAT-03` | `PATCH /policies/pol_4` | `Bearer tok_user1_ayse` | `{"holderName": "Hack"}` | **403** | `{"error":"Erişim engellendi","message":"Bu poliçeye erişim yetkiniz yok."}` |
| `PAT-04` | `PATCH /policies/does-not-exist-000` | `Bearer tok_user1_ayse` | `{"holderName": "Test"}` | **404** | `{"error":"Bulunamadı","message":"Poliçe bulunamadı."}` |
| `PAT-05` | `PATCH /policies/pol_2` | `Bearer tok_user1_ayse` | `{"holderName": "Ayşe Yılmaz-Test", "agentName": "Ali Veli"}` | **200** | `{"id":"pol_2","policyNumber":"POL-2026-0002","ownerUserId":"u1","holderName":"Ayşe Yılmaz-Test","holderTckn":"11111111110","coverageType":"konut","premium":2400,"coverageLimit":...` |
| `PAT-06` | `GET /policies/pol_2` | `Bearer tok_user1_ayse` | — | **200** | `{"id":"pol_2","policyNumber":"POL-2026-0002","ownerUserId":"u1","holderName":"Ayşe Yılmaz-Test","holderTckn":"11111111110","coverageType":"konut","premium":2400,"coverageLimit":...` |
| `PAT-07` | `PATCH /policies/pol_2` | `Bearer tok_user1_ayse` | `{"agentName": null}` | **200** | `{"id":"pol_2","policyNumber":"POL-2026-0002","ownerUserId":"u1","holderName":"Ayşe Yılmaz-Test","holderTckn":"11111111110","coverageType":"konut","premium":2400,"coverageLimit":...` |
| `PAT-08` | `PATCH /policies/pol_2` | `Bearer tok_user1_ayse` | `{"holderName": "Ayşe Yılmaz"}` | **200** | `{"id":"pol_2","policyNumber":"POL-2026-0002","ownerUserId":"u1","holderName":"Ayşe Yılmaz","holderTckn":"11111111110","coverageType":"konut","premium":2400,"coverageLimit":10000...` |
| `PAT-09` | `GET /policies/pol_2` | `Bearer tok_user1_ayse` | — | **200** | `{"id":"pol_2","policyNumber":"POL-2026-0002","ownerUserId":"u1","holderName":"Ayşe Yılmaz","holderTckn":"11111111110","coverageType":"konut","premium":2400,"coverageLimit":10000...` |
| `PAT-10` | `PATCH /policies/pol_2` | `Bearer tok_admin_root` | `{"agentName": "Admin Acente"}` | **200** | `{"id":"pol_2","policyNumber":"POL-2026-0002","ownerUserId":"u1","holderName":"Ayşe Yılmaz","holderTckn":"11111111110","coverageType":"konut","premium":2400,"coverageLimit":10000...` |
| `PAT-11` | `PATCH /policies/pol_2` | `Bearer tok_user1_ayse` | `{"agentName": null}` | **200** | `{"id":"pol_2","policyNumber":"POL-2026-0002","ownerUserId":"u1","holderName":"Ayşe Yılmaz","holderTckn":"11111111110","coverageType":"konut","premium":2400,"coverageLimit":10000...` |
| `PAT-12` | `PATCH /policies/pol_2` | `Bearer tok_user1_ayse` | `{}` | **200** | `{"id":"pol_2","policyNumber":"POL-2026-0002","ownerUserId":"u1","holderName":"Ayşe Yılmaz","holderTckn":"11111111110","coverageType":"konut","premium":2400,"coverageLimit":10000...` |
| `PAT-13` | `PATCH /policies/pol_2` | `Bearer tok_user1_ayse` | `{"holderName": 12345}` | **200** | `{"id":"pol_2","policyNumber":"POL-2026-0002","ownerUserId":"u1","holderName":12345,"holderTckn":"11111111110","coverageType":"konut","premium":2400,"coverageLimit":100000,"statu...` |
| `PAT-14` | `PATCH /policies/pol_2` | `Bearer tok_user1_ayse` | `{"holderName": null}` | **200** | `{"id":"pol_2","policyNumber":"POL-2026-0002","ownerUserId":"u1","holderName":null,"holderTckn":"11111111110","coverageType":"konut","premium":2400,"coverageLimit":100000,"status...` |
| `PAT-15` | `PATCH /policies/pol_2` | `Bearer tok_user1_ayse` | `{"holderName": ""}` | **200** | `{"id":"pol_2","policyNumber":"POL-2026-0002","ownerUserId":"u1","holderName":"","holderTckn":"11111111110","coverageType":"konut","premium":2400,"coverageLimit":100000,"status":...` |
| `PAT-16` | `PATCH /policies/pol_2` | `Bearer tok_user1_ayse` | `{"agentName": 12345}` | **200** | `{"id":"pol_2","policyNumber":"POL-2026-0002","ownerUserId":"u1","holderName":"","holderTckn":"11111111110","coverageType":"konut","premium":2400,"coverageLimit":100000,"status":...` |
| `PAT-17` | `PATCH /policies/pol_2` | `Bearer tok_user1_ayse` | `{invalid json` | **400** | `{"error":"Geçersiz JSON","detail":"Expected property name or '}' in JSON at position 1 (line 1 column 2)","stack":"SyntaxError: Expected property name or '}' in JSON at position...` |
| `PAT-18` | `PATCH /policies/pol_2` | `Bearer tok_user1_ayse` | `(boş)` | **200** | `{"id":"pol_2","policyNumber":"POL-2026-0002","ownerUserId":"u1","holderName":"","holderTckn":"11111111110","coverageType":"konut","premium":2400,"coverageLimit":100000,"status":...` |
| `PAT-19` | `GET /policies/pol_5` | `Bearer tok_user1_ayse` | — | **200** | `{"id":"pol_5","policyNumber":"POL-2026-0005","ownerUserId":"u1","holderName":"Ayşe Yılmaz","holderTckn":"11111111110","coverageType":"trafik","premium":1800,"coverageLimit":7500...` |
| `PAT-20` | `PATCH /policies/pol_5` | `Bearer tok_user1_ayse` | `{"holderName": "Ayşe Yılmaz", "premium": 1}` | **200** | `{"id":"pol_5","policyNumber":"POL-2026-0005","ownerUserId":"u1","holderName":"Ayşe Yılmaz","holderTckn":"11111111110","coverageType":"trafik","premium":1800,"coverageLimit":7500...` |
| `PAT-21` | `GET /policies/pol_5` | `Bearer tok_user1_ayse` | — | **200** | `{"id":"pol_5","policyNumber":"POL-2026-0005","ownerUserId":"u1","holderName":"Ayşe Yılmaz","holderTckn":"11111111110","coverageType":"trafik","premium":1800,"coverageLimit":7500...` |
| `PAT-22` | `PATCH /policies/pol_5` | `Bearer tok_user1_ayse` | `{"coverageLimit": 9999999}` | **200** | `{"id":"pol_5","policyNumber":"POL-2026-0005","ownerUserId":"u1","holderName":"Ayşe Yılmaz","holderTckn":"11111111110","coverageType":"trafik","premium":1800,"coverageLimit":7500...` |
| `PAT-23` | `PATCH /policies/pol_5` | `Bearer tok_user1_ayse` | `{"status": "cancelled"}` | **200** | `{"id":"pol_5","policyNumber":"POL-2026-0005","ownerUserId":"u1","holderName":"Ayşe Yılmaz","holderTckn":"11111111110","coverageType":"trafik","premium":1800,"coverageLimit":7500...` |
| `PAT-24` | `PATCH /policies/pol_5` | `Bearer tok_user1_ayse` | `{"policyNumber": "POL-HACK-9999"}` | **200** | `{"id":"pol_5","policyNumber":"POL-2026-0005","ownerUserId":"u1","holderName":"Ayşe Yılmaz","holderTckn":"11111111110","coverageType":"trafik","premium":1800,"coverageLimit":7500...` |
| `PAT-25` | `PATCH /policies/pol_5` | `Bearer tok_user1_ayse` | `{"coverageType": "saglik"}` | **200** | `{"id":"pol_5","policyNumber":"POL-2026-0005","ownerUserId":"u1","holderName":"Ayşe Yılmaz","holderTckn":"11111111110","coverageType":"trafik","premium":1800,"coverageLimit":7500...` |
| `PAT-26` | `PATCH /policies/pol_5` | `Bearer tok_user1_ayse` | `{"holderTckn": "99999999999"}` | **200** | `{"id":"pol_5","policyNumber":"POL-2026-0005","ownerUserId":"u1","holderName":"Ayşe Yılmaz","holderTckn":"11111111110","coverageType":"trafik","premium":1800,"coverageLimit":7500...` |
| `PAT-27` | `PATCH /policies/pol_5` | `Bearer tok_user1_ayse` | `{"id": "pol_hacked"}` | **200** | `{"id":"pol_5","policyNumber":"POL-2026-0005","ownerUserId":"u1","holderName":"Ayşe Yılmaz","holderTckn":"11111111110","coverageType":"trafik","premium":1800,"coverageLimit":7500...` |
| `PAT-28` | `PATCH /policies/pol_5` | `Bearer tok_user1_ayse` | `{"startDate": "2020-01-01", "endDate": "2099-12-31"}` | **200** | `{"id":"pol_5","policyNumber":"POL-2026-0005","ownerUserId":"u1","holderName":"Ayşe Yılmaz","holderTckn":"11111111110","coverageType":"trafik","premium":1800,"coverageLimit":7500...` |
| `PAT-29` | `PATCH /policies/pol_5` | `Bearer tok_user1_ayse` | `{"unknownField": "xyz", "isAdmin": true}` | **200** | `{"id":"pol_5","policyNumber":"POL-2026-0005","ownerUserId":"u1","holderName":"Ayşe Yılmaz","holderTckn":"11111111110","coverageType":"trafik","premium":1800,"coverageLimit":7500...` |
| `PAT-30` | `PATCH /policies/pol_5` | `Bearer tok_user1_ayse` | `{"ownerUserId": "u2"}` | **200** | `{"id":"pol_5","policyNumber":"POL-2026-0005","ownerUserId":"u1","holderName":"Ayşe Yılmaz","holderTckn":"11111111110","coverageType":"trafik","premium":1800,"coverageLimit":7500...` |
| `PAT-31` | `GET /policies/pol_5` | `Bearer tok_admin_root` | — | **200** | `{"id":"pol_5","policyNumber":"POL-2026-0005","ownerUserId":"u1","holderName":"Ayşe Yılmaz","holderTckn":"11111111110","coverageType":"trafik","premium":1800,"coverageLimit":7500...` |
| `PAT-32` | `PATCH /policies/pol_2` | `Bearer tok_user1_ayse` | `{"holderName": "' OR '1'='1' --"}` | **200** | `{"id":"pol_2","policyNumber":"POL-2026-0002","ownerUserId":"u1","holderName":"' OR '1'='1' --","holderTckn":"11111111110","coverageType":"konut","premium":2400,"coverageLimit":1...` |
| `PAT-33` | `PATCH /policies/pol_2` | `Bearer tok_user1_ayse` | `{"holderName": "<script>alert(1)</script>"}` | **200** | `{"id":"pol_2","policyNumber":"POL-2026-0002","ownerUserId":"u1","holderName":"<script>alert(1)</script>","holderTckn":"11111111110","coverageType":"konut","premium":2400,"covera...` |
| `PAT-34` | `PATCH /policies/pol_2` | `Bearer tok_user1_ayse` | `{"holderName": "Ayşe Yılmaz"}` | **200** | `{"id":"pol_2","policyNumber":"POL-2026-0002","ownerUserId":"u1","holderName":"Ayşe Yılmaz","holderTckn":"11111111110","coverageType":"konut","premium":2400,"coverageLimit":10000...` |

---

## 5. Faz 2B — `POST /claims` İş Kuralları, Sınırlar, Idempotency ve Ek Durum Testleri (`RST`, `CLM`, `PAT-35..37`, `CHK`)

Kapsam: Auth/BOLA/404, zorunlu alan ve tip doğrulamaları, tutar sınırları (`0`, `-100`, `0.99`, `1`, `50000`, `50000.01`, `50001`, `100000`), iptal poliçe üzerinde hasar talebi (`pol_3`), `POST /claims` üzerinde mass assignment, sıralı ve eşzamanlı `Idempotency-Key` testleri, `pol_3` durum geçişi (`cancelled` → `active` → `bogus_status`) ve yönetici istatistik tutarlılığı.

| ID | İstek | Yetkilendirme | İstek Gövdesi | HTTP | Yanıt Özeti |
|---|---|---|---|---|---|
| `RST-01` | `PATCH /policies/pol_2` | `Bearer tok_user1_ayse` | `{"agentName": null}` | **200** | `{"id":"pol_2","policyNumber":"POL-2026-0002","ownerUserId":"u1","holderName":"Ayşe Yılmaz","holderTckn":"11111111110","coverageType":"konut","premium":2400,"coverageLimit":10000...` |
| `RST-02` | `PATCH /policies/pol_5` | `Bearer tok_user1_ayse` | `{"status": "active"}` | **200** | `{"id":"pol_5","policyNumber":"POL-2026-0005","ownerUserId":"u1","holderName":"Ayşe Yılmaz","holderTckn":"11111111110","coverageType":"trafik","premium":1800,"coverageLimit":7500...` |
| `CLM-01` | `POST /claims` | *(yok)* | `{"policyId": "pol_1", "amount": 500}` | **401** | `{"error":"Yetkisiz","message":"Geçerli bir bearer token gerekli."}` |
| `CLM-02` | `POST /claims` | `tok_user1_ayse` | `{"policyId": "pol_1", "amount": 500}` | **401** | `{"error":"Yetkisiz","message":"Geçerli bir bearer token gerekli."}` |
| `CLM-03` | `POST /claims` | `Bearer invalid_tok` | `{"policyId": "pol_1", "amount": 500}` | **401** | `{"error":"Yetkisiz","message":"Geçerli bir bearer token gerekli."}` |
| `CLM-04` | `POST /claims` | `Bearer tok_user1_ayse` | `{"policyId": "pol_4", "amount": 500}` | **403** | `{"error":"Erişim engellendi","message":"Bu poliçe için hasar talebi oluşturamazsınız."}` |
| `CLM-05` | `POST /claims` | `Bearer tok_user2_mehmet` | `{"policyId": "pol_1", "amount": 500}` | **403** | `{"error":"Erişim engellendi","message":"Bu poliçe için hasar talebi oluşturamazsınız."}` |
| `CLM-06` | `POST /claims` | `Bearer tok_user1_ayse` | `{"policyId": "pol_999", "amount": 500}` | **404** | `{"error":"Bulunamadı","message":"Poliçe bulunamadı."}` |
| `CLM-07` | `POST /claims` | `Bearer tok_admin_root` | `{"policyId": "pol_1", "amount": 500, "description": "Admin claim"}` | **200** | `{"id":"clm_8","policyId":"pol_1","ownerUserId":"admin","amount":500,"status":"submitted","description":"Admin claim","createdAt":"2026-08-01T00:00:00Z"}` |
| `CLM-08` | `POST /claims` | `Bearer tok_user1_ayse` | `{"amount": 500}` | **400** | `{"error":"Eksik alan","message":"policyId ve amount zorunludur."}` |
| `CLM-09` | `POST /claims` | `Bearer tok_user1_ayse` | `{"policyId": "pol_1"}` | **400** | `{"error":"Eksik alan","message":"policyId ve amount zorunludur."}` |
| `CLM-10` | `POST /claims` | `Bearer tok_user1_ayse` | `{}` | **400** | `{"error":"Eksik alan","message":"policyId ve amount zorunludur."}` |
| `CLM-11` | `POST /claims` | `Bearer tok_user1_ayse` | `{"policyId": 12345, "amount": 500}` | **404** | `{"error":"Bulunamadı","message":"Poliçe bulunamadı."}` |
| `CLM-12` | `POST /claims` | `Bearer tok_user1_ayse` | `{"policyId": "pol_1", "amount": "abc"}` | **400** | `{"error":"Geçersiz tip","message":"amount sayısal olmalıdır."}` |
| `CLM-13` | `POST /claims` | `Bearer tok_user1_ayse` | `{"policyId": "pol_1", "amount": null}` | **400** | `{"error":"Geçersiz tip","message":"amount sayısal olmalıdır."}` |
| `CLM-14` | `POST /claims` | `Bearer tok_user1_ayse` | `{"policyId": "pol_1", "amount": true}` | **400** | `{"error":"Geçersiz tip","message":"amount sayısal olmalıdır."}` |
| `CLM-15` | `POST /claims` | `Bearer tok_user1_ayse` | `{"policyId": "pol_1", "amount": "500"}` | **400** | `{"error":"Geçersiz tip","message":"amount sayısal olmalıdır."}` |
| `CLM-16` | `POST /claims` | `Bearer tok_user1_ayse` | `{"policyId": "pol_1", "amount": 500, "description": 12345}` | **200** | `{"id":"clm_9","policyId":"pol_1","ownerUserId":"u1","amount":500,"status":"submitted","description":"","createdAt":"2026-08-01T00:00:00Z"}` |
| `CLM-17` | `POST /claims` | `Bearer tok_user1_ayse` | `{"policyId": "pol_1", "amount": 500, "description": null}` | **200** | `{"id":"clm_10","policyId":"pol_1","ownerUserId":"u1","amount":500,"status":"submitted","description":"","createdAt":"2026-08-01T00:00:00Z"}` |
| `CLM-18` | `POST /claims` | `Bearer tok_user1_ayse` | `{bad json` | **400** | `{"error":"Geçersiz JSON","detail":"Expected property name or '}' in JSON at position 1 (line 1 column 2)","stack":"SyntaxError: Expected property name or '}' in JSON at position...` |
| `CLM-19` | `POST /claims` | `Bearer tok_user1_ayse` | `{"policyId": "pol_1", "amount": 0}` | **200** | `{"id":"clm_11","policyId":"pol_1","ownerUserId":"u1","amount":0,"status":"submitted","description":"","createdAt":"2026-08-01T00:00:00Z"}` |
| `CLM-20` | `POST /claims` | `Bearer tok_user1_ayse` | `{"policyId": "pol_1", "amount": -100}` | **200** | `{"id":"clm_12","policyId":"pol_1","ownerUserId":"u1","amount":-100,"status":"submitted","description":"","createdAt":"2026-08-01T00:00:00Z"}` |
| `CLM-21` | `POST /claims` | `Bearer tok_user1_ayse` | `{"policyId": "pol_1", "amount": 0.99}` | **200** | `{"id":"clm_13","policyId":"pol_1","ownerUserId":"u1","amount":0.99,"status":"submitted","description":"","createdAt":"2026-08-01T00:00:00Z"}` |
| `CLM-22` | `POST /claims` | `Bearer tok_user1_ayse` | `{"policyId": "pol_1", "amount": 1, "description": "Min sınır 1"}` | **200** | `{"id":"clm_14","policyId":"pol_1","ownerUserId":"u1","amount":1,"status":"submitted","description":"Min sınır 1","createdAt":"2026-08-01T00:00:00Z"}` |
| `CLM-23` | `POST /claims` | `Bearer tok_user1_ayse` | `{"policyId": "pol_1", "amount": 50000, "description": "Tam limit 50000"}` | **200** | `{"id":"clm_15","policyId":"pol_1","ownerUserId":"u1","amount":50000,"status":"submitted","description":"Tam limit 50000","createdAt":"2026-08-01T00:00:00Z"}` |
| `CLM-24` | `POST /claims` | `Bearer tok_user1_ayse` | `{"policyId": "pol_1", "amount": 50000.01, "description": "Limit aşımı 50000.01"}` | **200** | `{"id":"clm_16","policyId":"pol_1","ownerUserId":"u1","amount":50000.01,"status":"submitted","description":"Limit aşımı 50000.01","createdAt":"2026-08-01T00:00:00Z"}` |
| `CLM-25` | `POST /claims` | `Bearer tok_user1_ayse` | `{"policyId": "pol_1", "amount": 50001, "description": "Limit aşımı 50001"}` | **200** | `{"id":"clm_17","policyId":"pol_1","ownerUserId":"u1","amount":50001,"status":"submitted","description":"Limit aşımı 50001","createdAt":"2026-08-01T00:00:00Z"}` |
| `CLM-26` | `POST /claims` | `Bearer tok_user1_ayse` | `{"policyId": "pol_1", "amount": 100000, "description": "Limit aşımı 100000"}` | **200** | `{"id":"clm_18","policyId":"pol_1","ownerUserId":"u1","amount":100000,"status":"submitted","description":"Limit aşımı 100000","createdAt":"2026-08-01T00:00:00Z"}` |
| `CLM-27` | `POST /claims` | `Bearer tok_user2_mehmet` | `{"policyId": "pol_3", "amount": 100, "description": "İptal poliçeye hasar"}` | **200** | `{"id":"clm_19","policyId":"pol_3","ownerUserId":"u2","amount":100,"status":"submitted","description":"İptal poliçeye hasar","createdAt":"2026-08-01T00:00:00Z"}` |
| `CLM-28` | `POST /claims` | `Bearer tok_user1_ayse` | `{"policyId": "pol_1", "amount": 200, "status": "approved", "ownerUserId": "u2", "id": "clm_hacked", "claimNumber": "CLM-HACK", "role": "a...` | **200** | `{"id":"clm_20","policyId":"pol_1","ownerUserId":"u1","amount":200,"status":"submitted","description":"","createdAt":"2026-08-01T00:00:00Z"}` |
| `CLM-29` | `POST /claims` | `Bearer tok_user1_ayse` · Ek başlık: `{"Idempotency-Key": "idem-key-001"}` | `{"policyId": "pol_2", "amount": 300, "description": "Idem test"}` | **200** | `{"id":"clm_21","policyId":"pol_2","ownerUserId":"u1","amount":300,"status":"submitted","description":"Idem test","createdAt":"2026-08-01T00:00:00Z"}` |
| `CLM-30` | `POST /claims` | `Bearer tok_user1_ayse` · Ek başlık: `{"Idempotency-Key": "idem-key-001"}` | `{"policyId": "pol_2", "amount": 300, "description": "Idem test"}` | **200** | `{"id":"clm_22","policyId":"pol_2","ownerUserId":"u1","amount":300,"status":"submitted","description":"Idem test","createdAt":"2026-08-01T00:00:00Z"}` |
| `CLM-31` | `GET /claims?policyId=pol_2` | `Bearer tok_user1_ayse` | — | **200** | `{"data":[{"id":"clm_3","policyId":"pol_2","ownerUserId":"u1","amount":3000,"status":"approved","description":"Su baskını","createdAt":"2026-06-01T08:15:00Z"},{"id":"clm_5","poli...` |
| `CLM-32` | `POST /claims` | `Bearer tok_user2_mehmet` · Ek başlık: `{"Idempotency-Key": "idem-key-001"}` | `{"policyId": "pol_4", "amount": 400, "description": "Other user same key"}` | **200** | `{"id":"clm_23","policyId":"pol_4","ownerUserId":"u2","amount":400,"status":"submitted","description":"Other user same key","createdAt":"2026-08-01T00:00:00Z"}` |
| `CLM-33` | `POST /claims` | `Bearer tok_user1_ayse` · Ek başlık: `{"Idempotency-Key": "idem-key-001"}` | `{"policyId": "pol_2", "amount": 999, "description": "Different body same key"}` | **200** | `{"id":"clm_24","policyId":"pol_2","ownerUserId":"u1","amount":999,"status":"submitted","description":"Different body same key","createdAt":"2026-08-01T00:00:00Z"}` |
| `CLM-34-2` | `POST /claims` | `Bearer tok_user1_ayse` · Ek başlık: `{"Idempotency-Key": "idem-concurrent-001"}` | `{"policyId": "pol_2", "amount": 350, "description": "Concurrent idem"}` | **200** | `{"id":"clm_25","policyId":"pol_2","ownerUserId":"u1","amount":350,"status":"submitted","description":"Concurrent idem","createdAt":"2026-08-01T00:00:00Z"}` |
| `CLM-34-1` | `POST /claims` | `Bearer tok_user1_ayse` · Ek başlık: `{"Idempotency-Key": "idem-concurrent-001"}` | `{"policyId": "pol_2", "amount": 350, "description": "Concurrent idem"}` | **200** | `{"id":"clm_26","policyId":"pol_2","ownerUserId":"u1","amount":350,"status":"submitted","description":"Concurrent idem","createdAt":"2026-08-01T00:00:00Z"}` |
| `CLM-35` | `GET /claims?policyId=pol_2` | `Bearer tok_user1_ayse` | — | **200** | `{"data":[{"id":"clm_3","policyId":"pol_2","ownerUserId":"u1","amount":3000,"status":"approved","description":"Su baskını","createdAt":"2026-06-01T08:15:00Z"},{"id":"clm_5","poli...` |
| `CLM-36` | `POST /claims` | `Bearer tok_user1_ayse` | `{"policyId": "' OR '1'='1' --", "amount": 10}` | **404** | `{"error":"Bulunamadı","message":"Poliçe bulunamadı."}` |
| `CLM-37` | `POST /claims` | `Bearer tok_user1_ayse` | `{"policyId": "<script>alert(1)</script>", "amount": 10}` | **404** | `{"error":"Bulunamadı","message":"Poliçe bulunamadı."}` |
| `CLM-38` | `POST /claims` | `Bearer tok_user1_ayse` | `{"policyId": "pol_1", "amount": 10, "description": "<script>alert(1)</script>"}` | **200** | `{"id":"clm_27","policyId":"pol_1","ownerUserId":"u1","amount":10,"status":"submitted","description":"<script>alert(1)</script>","createdAt":"2026-08-01T00:00:00Z"}` |
| `PAT-35` | `PATCH /policies/pol_3` | `Bearer tok_user2_mehmet` | `{"status": "active"}` | **200** | `{"id":"pol_3","policyNumber":"POL-2026-0003","ownerUserId":"u2","holderName":"Mehmet Demir","holderTckn":"22222222220","coverageType":"saglik","premium":900,"coverageLimit":2000...` |
| `PAT-36` | `PATCH /policies/pol_3` | `Bearer tok_user2_mehmet` | `{"status": "bogus_status"}` | **200** | `{"id":"pol_3","policyNumber":"POL-2026-0003","ownerUserId":"u2","holderName":"Mehmet Demir","holderTckn":"22222222220","coverageType":"saglik","premium":900,"coverageLimit":2000...` |
| `PAT-37` | `PATCH /policies/pol_3` | `Bearer tok_user2_mehmet` | `{"status": "cancelled"}` | **200** | `{"id":"pol_3","policyNumber":"POL-2026-0003","ownerUserId":"u2","holderName":"Mehmet Demir","holderTckn":"22222222220","coverageType":"saglik","premium":900,"coverageLimit":2000...` |
| `CHK-01` | `GET /admin/stats` | `Bearer tok_admin_root` | — | **200** | `{"totalPolicies":5,"totalClaims":27,"totalPremium":9800}` |
| `CHK-02` | `GET /claims?page=1&pageSize=100` | `Bearer tok_admin_root` | — | **200** | `{"data":[{"id":"clm_1","policyId":"pol_1","ownerUserId":"u1","amount":12000,"status":"submitted","description":"Çarpma hasarı","createdAt":"2026-05-02T09:00:00Z"},{"id":"clm_2",...` |

---

## 6. Faz 3 — Kötü Girdi, Kök JSON Tipleri ve Çökme (DoS) Keşfi (`EDG-01` – `EDG-28`)

> **Önemli Not:** `EDG-01` (`POST /claims` gövde `null`) ve `EDG-06` (`PATCH /policies/pol_2` gövde `null`) istekleri sunucuyu anında çökertmiştir. `EDG-02`, `EDG-03`, `EDG-04` ile `EDG-07` isteklerindeki `ConnectionRefusedError` hataları, sunucunun çöküp otomatik olarak yeniden başlaması arasındaki kısa sürede gerçekleştiği için tek başına geçersiz girdi davranışı olarak yorumlanmamış; bu girdiler Faz 4'te (`VER-04`–`VER-08`) sunucu ayaktayken izole edilerek yeniden test edilmiştir. Ayrıca `EDG-01` ve `EDG-06` sonrasında sunucu belleği başlangıç durumuna (`pol_1`–`pol_5`, `clm_1`–`clm_7`) sıfırlandığından `EDG-10` sonrası oluşan ilk hasar kaydı yeniden `clm_8` kimliğini almıştır.

| ID | İstek | Yetkilendirme | İstek Gövdesi | HTTP | Yanıt Özeti |
|---|---|---|---|---|---|
| `EDG-01` | `POST /claims` | `Bearer tok_user1_ayse` | `null` | Bağlantı kesildi (-1) | `ConnectionResetError(10054, 'Varolan bir bağlantı uzaktaki bir ana bilgisayar tarafından zorla kapatıldı', None, 10054, None)` |
| `EDG-02` | `POST /claims` | `Bearer tok_user1_ayse` | `[]` | Bağlantı kesildi (-1) | `URLError(ConnectionRefusedError(10061, 'Hedef makine etkin olarak reddettiğinden bağlantı kurulamadı', None, 10061, None))` |
| `EDG-03` | `POST /claims` | `Bearer tok_user1_ayse` | `123` | Bağlantı kesildi (-1) | `URLError(ConnectionRefusedError(10061, 'Hedef makine etkin olarak reddettiğinden bağlantı kurulamadı', None, 10061, None))` |
| `EDG-04` | `POST /claims` | `Bearer tok_user1_ayse` | `"hello"` | Bağlantı kesildi (-1) | `URLError(ConnectionRefusedError(10061, 'Hedef makine etkin olarak reddettiğinden bağlantı kurulamadı', None, 10061, None))` |
| `EDG-05` | `POST /claims` | `Bearer tok_user1_ayse` | `(boş)` | **400** | `{"error":"Eksik alan","message":"policyId ve amount zorunludur."}` |
| `EDG-06` | `PATCH /policies/pol_2` | `Bearer tok_user1_ayse` | `null` | Bağlantı kesildi (-1) | `ConnectionResetError(10054, 'Varolan bir bağlantı uzaktaki bir ana bilgisayar tarafından zorla kapatıldı', None, 10054, None)` |
| `EDG-07` | `PATCH /policies/pol_2` | `Bearer tok_user1_ayse` | `[]` | Bağlantı kesildi (-1) | `URLError(ConnectionRefusedError(10061, 'Hedef makine etkin olarak reddettiğinden bağlantı kurulamadı', None, 10061, None))` |
| `EDG-08` | `PATCH /policies/pol_2` | `Bearer tok_user1_ayse` | `123` | **200** | `{"id":"pol_2","policyNumber":"POL-2026-0002","ownerUserId":"u1","holderName":"Ayşe Yılmaz","holderTckn":"11111111110","coverageType":"konut","premium":2400,"coverageLimit":10000...` |
| `EDG-09` | `PATCH /policies/pol_2` | `Bearer tok_user1_ayse` | `"hello"` | **200** | `{"id":"pol_2","policyNumber":"POL-2026-0002","ownerUserId":"u1","holderName":"Ayşe Yılmaz","holderTckn":"11111111110","coverageType":"konut","premium":2400,"coverageLimit":10000...` |
| `EDG-10` | `POST /claims` | `Bearer tok_user1_ayse` | `{"policyId": "pol_1", "amount": 1e+308}` | **200** | `{"id":"clm_8","policyId":"pol_1","ownerUserId":"u1","amount":1e+308,"status":"submitted","description":"","createdAt":"2026-08-01T00:00:00Z"}` |
| `EDG-11` | `POST /claims` | `Bearer tok_user1_ayse` | `{"policyId": "pol_1", "amount": 100, "description": "İıŞşĞğÜüÖöÇç test"}` | **200** | `{"id":"clm_9","policyId":"pol_1","ownerUserId":"u1","amount":100,"status":"submitted","description":"İıŞşĞğÜüÖöÇç test","createdAt":"2026-08-01T00:00:00Z"}` |
| `EDG-12` | `POST /claims` | `Bearer tok_user1_ayse` | `{"policyId": null, "amount": 100}` | **404** | `{"error":"Bulunamadı","message":"Poliçe bulunamadı."}` |
| `EDG-13` | `POST /claims` | `Bearer tok_user1_ayse` | `{"policyId": "", "amount": 100}` | **404** | `{"error":"Bulunamadı","message":"Poliçe bulunamadı."}` |
| `EDG-14` | `PATCH /policies/pol_2` | `Bearer tok_user1_ayse` | `{"holderName": ["arr"], "agentName": {"obj": 1}}` | **200** | `{"id":"pol_2","policyNumber":"POL-2026-0002","ownerUserId":"u1","holderName":["arr"],"holderTckn":"11111111110","coverageType":"konut","premium":2400,"coverageLimit":100000,"sta...` |
| `EDG-15` | `PATCH /policies/pol_2` | `Bearer tok_user1_ayse` | `{"holderName": "Ayşe Yılmaz", "agentName": null}` | **200** | `{"id":"pol_2","policyNumber":"POL-2026-0002","ownerUserId":"u1","holderName":"Ayşe Yılmaz","holderTckn":"11111111110","coverageType":"konut","premium":2400,"coverageLimit":10000...` |
| `EDG-16` | `GET /claims?page=1.5&pageSize=2` | `Bearer tok_user1_ayse` | — | **200** | `{"data":[{"id":"clm_1","policyId":"pol_1","ownerUserId":"u1","amount":12000,"status":"submitted","description":"Çarpma hasarı","createdAt":"2026-05-02T09:00:00Z"},{"id":"clm_2",...` |
| `EDG-17` | `GET /claims?page=1&pageSize=1.5` | `Bearer tok_user1_ayse` | — | **200** | `{"data":[{"id":"clm_1","policyId":"pol_1","ownerUserId":"u1","amount":12000,"status":"submitted","description":"Çarpma hasarı","createdAt":"2026-05-02T09:00:00Z"}],"meta":{"page...` |
| `EDG-18` | `GET /claims?page=1&page=2&pageSize=2` | `Bearer tok_user1_ayse` | — | **200** | `{"data":[{"id":"clm_1","policyId":"pol_1","ownerUserId":"u1","amount":12000,"status":"submitted","description":"Çarpma hasarı","createdAt":"2026-05-02T09:00:00Z"},{"id":"clm_2",...` |
| `EDG-19` | `GET /claims?page=1&pageSize=101` | `Bearer tok_admin_root` | — | **200** | `{"data":[{"id":"clm_1","policyId":"pol_1","ownerUserId":"u1","amount":12000,"status":"submitted","description":"Çarpma hasarı","createdAt":"2026-05-02T09:00:00Z"},{"id":"clm_2",...` |
| `EDG-20` | `GET /claims?policyId=` | `Bearer tok_user1_ayse` | — | **200** | `{"data":[{"id":"clm_1","policyId":"pol_1","ownerUserId":"u1","amount":12000,"status":"submitted","description":"Çarpma hasarı","createdAt":"2026-05-02T09:00:00Z"},{"id":"clm_2",...` |
| `EDG-21` | `GET /claims/clm_8` | `Bearer tok_user1_ayse` | — | **200** | `{"id":"clm_8","policyId":"pol_1","ownerUserId":"u1","amount":1e+308,"status":"submitted","description":"","createdAt":"2026-08-01T00:00:00Z"}` |
| `EDG-22` | `GET /claims?policyId=pol_1` | `Bearer tok_user1_ayse` | — | **200** | `{"data":[{"id":"clm_1","policyId":"pol_1","ownerUserId":"u1","amount":12000,"status":"submitted","description":"Çarpma hasarı","createdAt":"2026-05-02T09:00:00Z"},{"id":"clm_2",...` |
| `EDG-23` | `GET /admin/stats` | `tok_user1_ayse` | — | **401** | `{"error":"Yetkisiz","message":"Geçerli bir bearer token gerekli."}` |
| `EDG-24` | `GET /admin/stats/` | `Bearer tok_user1_ayse` | — | **404** | `{"error":"Bulunamadı","message":"Kaynak yok."}` |
| `EDG-25` | `GET /policies/` | `Bearer tok_user1_ayse` | — | **404** | `{"error":"Bulunamadı","message":"Kaynak yok."}` |
| `EDG-26` | `GET /policies/%2e%2e%2fadmin%2fstats` | `Bearer tok_user1_ayse` | — | **404** | `{"error":"Bulunamadı","message":"Poliçe bulunamadı."}` |
| `EDG-27` | `PUT /policies/pol_2` | `Bearer tok_user1_ayse` | `{"holderName": "Test"}` | **405** | `{"error":"Yöntem desteklenmiyor"}` |
| `EDG-28` | `POST /health` | *(yok)* | `{}` | **401** | `{"error":"Yetkisiz","message":"Geçerli bir bearer token gerekli."}` |

---

## 7. Faz 4 ve 5 — İzole Doğrulamalar ve Ek Sınır Kontrolleri (`VER-01` – `VER-16`, `EXT-01` – `EXT-08`)

Kapsam: Yönetici tarafından açılan hasar talebinin sahiplik davranışı (`VER-01`–`VER-03`), `[]` / `123` / `"hello"` / `true` gövdelerinin çökme yapmadığının izole kanıtı (`VER-04`–`VER-08`), `null` çökmesinin tekrarlanabilirlik doğrulaması (`VER-09`–`VER-10`), `Content-Type: text/plain` hata gövdesi (`VER-11`), Türkçe virgüllü tutar (`"100,50"`) ve ondalık tutar (`100.5`) (`VER-12`–`VER-13`), 5000 karakterlik açıklama (`EXT-05`), kalıcılık kontrolü (`EXT-06`–`EXT-07`).

| ID | İstek | Yetkilendirme | İstek Gövdesi | HTTP | Yanıt Özeti |
|---|---|---|---|---|---|
| `VER-01` | `POST /claims` | `Bearer tok_admin_root` | `{"policyId": "pol_1", "amount": 250, "description": "Admin talebi"}` | **200** | `{"id":"clm_10","policyId":"pol_1","ownerUserId":"admin","amount":250,"status":"submitted","description":"Admin talebi","createdAt":"2026-08-01T00:00:00Z"}` |
| `VER-02` | `GET /claims/clm_10` | `Bearer tok_user1_ayse` | — | **403** | `{"error":"Erişim engellendi","message":"Bu hasar talebine erişim yetkiniz yok."}` |
| `VER-03` | `GET /claims?policyId=pol_1` | `Bearer tok_user1_ayse` | — | **200** | `{"data":[{"id":"clm_1","policyId":"pol_1","ownerUserId":"u1","amount":12000,"status":"submitted","description":"Çarpma hasarı","createdAt":"2026-05-02T09:00:00Z"},{"id":"clm_2",...` |
| `VER-04` | `POST /claims` | `Bearer tok_user1_ayse` | `[]` | **400** | `{"error":"Eksik alan","message":"policyId ve amount zorunludur."}` |
| `VER-05` | `POST /claims` | `Bearer tok_user1_ayse` | `123` | **400** | `{"error":"Eksik alan","message":"policyId ve amount zorunludur."}` |
| `VER-06` | `POST /claims` | `Bearer tok_user1_ayse` | `"hello"` | **400** | `{"error":"Eksik alan","message":"policyId ve amount zorunludur."}` |
| `VER-07` | `POST /claims` | `Bearer tok_user1_ayse` | `true` | **400** | `{"error":"Eksik alan","message":"policyId ve amount zorunludur."}` |
| `VER-08` | `PATCH /policies/pol_2` | `Bearer tok_user1_ayse` | `[]` | **200** | `{"id":"pol_2","policyNumber":"POL-2026-0002","ownerUserId":"u1","holderName":"Ayşe Yılmaz","holderTckn":"11111111110","coverageType":"konut","premium":2400,"coverageLimit":10000...` |
| `VER-09` | `POST /claims` | `Bearer tok_user1_ayse` | `null` | Bağlantı kesildi (-1) | `ConnectionResetError(10054, 'Varolan bir bağlantı uzaktaki bir ana bilgisayar tarafından zorla kapatıldı', None, 10054, None)` |
| `VER-10` | `PATCH /policies/pol_2` | `Bearer tok_user1_ayse` | `null` | Bağlantı kesildi (-1) | `ConnectionResetError(10054, 'Varolan bir bağlantı uzaktaki bir ana bilgisayar tarafından zorla kapatıldı', None, 10054, None)` |
| `VER-11` | `POST /claims` | `Bearer tok_user1_ayse` | `policyId=pol_1&amount=100` | **400** | `{"error":"Geçersiz JSON","detail":"Unexpected token 'p', \"policyId=p\"... is not valid JSON","stack":"SyntaxError: Unexpected token 'p', \"policyId=p\"... is not valid JSON\n  ...` |
| `VER-12` | `POST /claims` | `Bearer tok_user1_ayse` | `{"policyId": "pol_1", "amount": "100,50"}` | **400** | `{"error":"Geçersiz tip","message":"amount sayısal olmalıdır."}` |
| `VER-13` | `POST /claims` | `Bearer tok_user1_ayse` | `{"policyId": "pol_1", "amount": 100.5}` | **200** | `{"id":"clm_8","policyId":"pol_1","ownerUserId":"u1","amount":100.5,"status":"submitted","description":"","createdAt":"2026-08-01T00:00:00Z"}` |
| `VER-14` | `GET /admin/policies` | `Bearer tok_user1_ayse` | — | **403** | `{"error":"Erişim engellendi","message":"Yönetici yetkisi gerekli."}` |
| `VER-15` | `GET /admin/stats` | `Bearer tok_user1_ayse` | — | **200** | `{"totalPolicies":5,"totalClaims":8,"totalPremium":9800}` |
| `VER-16` | `GET /claims?page=1&pageSize=101` | `Bearer tok_admin_root` | — | **200** | `{"data":[{"id":"clm_1","policyId":"pol_1","ownerUserId":"u1","amount":12000,"status":"submitted","description":"Çarpma hasarı","createdAt":"2026-05-02T09:00:00Z"},{"id":"clm_2",...` |
| `EXT-01` | `POST /health` | `Bearer tok_user1_ayse` | `{}` | **404** | `{"error":"Bulunamadı","message":"Kaynak yok."}` |
| `EXT-02` | `GET /policies/pol_1` | `Bearer tok_user1_ayse` | — | **200** | `{"id":"pol_1","policyNumber":"POL-2026-0001","ownerUserId":"u1","holderName":"Ayşe Yılmaz","holderTckn":"11111111110","coverageType":"kasko","premium":1500,"coverageLimit":50000...` |
| `EXT-03` | `GET /admin/stats` | `Bearer tok_user2_mehmet` | — | **200** | `{"totalPolicies":5,"totalClaims":8,"totalPremium":9800}` |
| `EXT-04` | `GET /admin/claims` | `Bearer tok_admin_root` | — | **404** | `{"error":"Bulunamadı","message":"Kaynak yok."}` |
| `EXT-05` | `POST /claims` | `Bearer tok_user1_ayse` | `{"policyId": "pol_1", "amount": 500, "description": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa...` | **200** | `{"id":"clm_9","policyId":"pol_1","ownerUserId":"u1","amount":500,"status":"submitted","description":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa...` |
| `EXT-06` | `PATCH /policies/pol_2` | `Bearer tok_user1_ayse` | `{"holderName": 12345}` | **200** | `{"id":"pol_2","policyNumber":"POL-2026-0002","ownerUserId":"u1","holderName":12345,"holderTckn":"11111111110","coverageType":"konut","premium":2400,"coverageLimit":100000,"statu...` |
| `EXT-07` | `GET /policies/pol_2` | `Bearer tok_user1_ayse` | — | **200** | `{"id":"pol_2","policyNumber":"POL-2026-0002","ownerUserId":"u1","holderName":12345,"holderTckn":"11111111110","coverageType":"konut","premium":2400,"coverageLimit":100000,"statu...` |
| `EXT-08` | `PATCH /policies/pol_2` | `Bearer tok_user1_ayse` | `{"holderName": "Ayşe Yılmaz"}` | **200** | `{"id":"pol_2","policyNumber":"POL-2026-0002","ownerUserId":"u1","holderName":"Ayşe Yılmaz","holderTckn":"11111111110","coverageType":"konut","premium":2400,"coverageLimit":10000...` |

---

## 8. Sözleşme İncelemesi (`openapi.yaml`) ve Açık Sorular

`skills/testing-apis/scripts/openapi_tests.py` ile üretilen sözleşme soruları ve manuel inceleme bulguları:

1. `GET /policies/{id}` ve `PATCH /policies/{id}`: Yol parametresi `id` için örnek (`example`) tanımlı değil.
2. `PATCH /policies/{id}`: `holderName` için `minLength`/`maxLength` veya karakter kısıtı tanımlı değil.
3. `PATCH /policies/{id}` (`PolicyUpdate`): Açıklamalar fazla alanların yok sayılacağını söylerken şema `additionalProperties: false` tanımlayarak kendisiyle çelişmektedir (bkz. `bulgular.md` — `BLG-16`).
4. `GET /claims`: `policyId` yetkilendirme kuralı ve `page`/`pageSize` sayısal sınırları tanımlı olmasına rağmen `responses` bölümünde `403` ve `400` yanıtları eksiktir.
5. `POST /claims`: `policyId` için uzunluk/biçim kısıtı yok; `Policy.status` içinde `cancelled`, `expired`, `pending` değerleri bulunmasına rağmen hangi poliçe durumlarında hasar talebi açılabileceği sözleşmede belirtilmemiştir.

---

## 9. Kapsam Dışı Kalan / Test Edilemeyen Alanlar (`NOT covered`)

- **Hız sınırlama (Rate Limiting / 429) ve Yük/Performans Testi:** Ortamda hız sınırı sözleşmede tanımlanmamıştır ve yük testi çalıştırılmamıştır.
- **`expired` ve `pending` poliçe durumları üzerinde `POST /claims`:** Başlangıç verisinde yalnızca `active` (`pol_1`, `pol_2`, `pol_4`, `pol_5`) ve `cancelled` (`pol_3`) poliçeler bulunduğu için yalnızca `cancelled` durumu test edilebilmiştir (`CLM-27`).
- **Süresi dolmuş veya kriptografik olarak imzası bozulmuş JWT token testleri:** Test ortamı statik bearer token kullandığından yalnızca eksik token, şemasız başlık, yanlış şema (`Basic`), boş token ve geçersiz rastgele token senaryoları koşturulmuştur.
- **Yanıt önbellek/güvenlik başlıkları derinlemesine taraması:** API yalnızca `Content-Type: application/json; charset=utf-8` döndürmekte olup tarayıcıya yönelik CORS/CSP politikası sözleşmede tanımlanmadığından hata olarak işaretlenmemiştir.

---

## 10. Gözlem Notu (Kusur Olarak Raporlanmayan Davranışlar)

- Yeni oluşturulan tüm hasar kayıtlarında `createdAt` alanı sabit `"2026-08-01T00:00:00Z"` zaman damgasıyla dönmektedir (`CLM-22`, `VER-13` vb.). Bu durum test ortamındaki deterministik saat (mock clock) kurgusundan kaynaklanıyor olabileceğinden kusur olarak raporlanmamıştır; ancak canlıya geçiş öncesi gerçek sistem saatinin kullanıldığı doğrulanmalıdır.
- `Authorization: bearer tok_user1_ayse` (küçük harfli `bearer` şeması, `RO-07`) ve `Bearer  tok_user1_ayse` (çift boşluk, `RO-08`) sunucu tarafından kabul edilmektedir; HTTP Bearer standardında şema adı büyük/küçük harfe duyarsız olduğundan ve şemasız/yanlış şemalı istekler (`RO-03`, `RO-04`) `401` ile reddedildiğinden kusur sayılmamıştır.
