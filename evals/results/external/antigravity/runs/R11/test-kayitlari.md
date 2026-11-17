# Test Kayıtları ve Kanıt Günlüğü — Anadolu Güven Sigorta API

- **Hedef Servis:** `http://127.0.0.1:4106` (`localhost:4106`)
- **Referans Sözleşme:** `openapi.yaml` (Anadolu Güven Sigorta - Poliçe & Hasar API 1.0.0)
- **Kullanılan Test Token'ları (Sentetik):**
  - `u1`: `tok_user1_ayse` (normal kullanıcı — Ayşe Yılmaz)
  - `u2`: `tok_user2_mehmet` (normal kullanıcı — Mehmet Demir)
  - `admin`: `tok_admin_root` (yönetici — Sistem Yöneticisi)

Bu dosya, test koşumu sırasında gönderilen tüm HTTP isteklerinin ve sunucudan alınan gerçek yanıtların değiştirilmemiş kanıt kaydıdır. `bulgular.md` içindeki tüm kusurlar buradaki kayıt numaralarına (örn. `C-010`, `PA-016`, `N-004`) atıf yapar.

## Bölüm 1 — Keşif, Kimlik Doğrulama, BOLA/BFLA, Sayfalama ve Bozuk Girdiler (Batch 1)

| Kayıt ID | Açıklama | İstek | Token / Başlık | Beklenen | Gerçekleşen | Şema / Doğrulama Notu |
|---|---|---|---|---|---|---|
| **R-001** | GET /health kimliksiz | `GET /health` | (Authorization başlığı yok) | 200 | HTTP `200`<br>`{"status":"ok","service":"anadolu-guven-sigorta-api"}` | — |
| **R-002** | u1 GET /policies | `GET /policies` | tok_user1_ayse (u1, user) | 200 (yalnız u1 poliçeleri) | HTTP `200`<br>`[{"id":"pol_1","policyNumber":"POL-2026-0001","ownerUserId":"u1","holderName":"Ayşe Yılmaz","holderTckn":"11111111110","coverageType":"kasko","premium":1500,"coverageLimit":50000,"status":"active","agentName":"Zeynep ...` | — |
| **R-003** | u2 GET /policies | `GET /policies` | tok_user2_mehmet (u2, user) | 200 (yalnız u2 poliçeleri) | HTTP `200`<br>`[{"id":"pol_3","policyNumber":"POL-2026-0003","ownerUserId":"u2","holderName":"Mehmet Demir","holderTckn":"22222222220","coverageType":"saglik","premium":900,"coverageLimit":20000,"status":"cancelled","agentName":"Can...` | — |
| **R-004** | admin GET /policies | `GET /policies` | tok_admin_root (admin) | 200 (tüm poliçeler) | HTTP `200`<br>`[{"id":"pol_1","policyNumber":"POL-2026-0001","ownerUserId":"u1","holderName":"Ayşe Yılmaz","holderTckn":"11111111110","coverageType":"kasko","premium":1500,"coverageLimit":50000,"status":"active","agentName":"Zeynep ...` | — |
| **A-001** | GET /policies Authorization başlığı yok | `GET /policies` | (Authorization başlığı yok) | 401 | HTTP `401`<br>`{"error":"Yetkisiz","message":"Geçerli bir bearer token gerekli."}` | — |
| **A-002** | GET /policies Bearer şeması yok | `GET /policies` | `tok_user1_ayse` | 401 | HTTP `401`<br>`{"error":"Yetkisiz","message":"Geçerli bir bearer token gerekli."}` | — |
| **A-003** | GET /policies Basic şeması | `GET /policies` | `Basic dDE6dDI=` | 401 | HTTP `401`<br>`{"error":"Yetkisiz","message":"Geçerli bir bearer token gerekli."}` | — |
| **A-004** | GET /policies boş Bearer | `GET /policies` | `Bearer ` | 401 | HTTP `401`<br>`{"error":"Yetkisiz","message":"Geçerli bir bearer token gerekli."}` | — |
| **A-005** | GET /policies geçersiz token | `GET /policies` | `Bearer tok_invalid_999` | 401 | HTTP `401`<br>`{"error":"Yetkisiz","message":"Geçerli bir bearer token gerekli."}` | — |
| **A-006** | GET /policies küçük harfli bearer | `GET /policies` | `bearer tok_user1_ayse` | 401 veya 200 (RFC7235) | HTTP `200`<br>`[{"id":"pol_1","policyNumber":"POL-2026-0001","ownerUserId":"u1","holderName":"Ayşe Yılmaz","holderTckn":"11111111110","coverageType":"kasko","premium":1500,"coverageLimit":50000,"status":"active","agentName":"Zeynep ...` | — |
| **A-007** | GET /policies fazla boşluklu Bearer | `GET /policies` | `Bearer   tok_user1_ayse` | 401 | HTTP `200`<br>`[{"id":"pol_1","policyNumber":"POL-2026-0001","ownerUserId":"u1","holderName":"Ayşe Yılmaz","holderTckn":"11111111110","coverageType":"kasko","premium":1500,"coverageLimit":50000,"status":"active","agentName":"Zeynep ...` | — |
| **P-001** | u1 GET kendi poliçesi pol_1 | `GET /policies/pol_1` | tok_user1_ayse (u1, user) | 200 | HTTP `200`<br>`{"id":"pol_1","policyNumber":"POL-2026-0001","ownerUserId":"u1","holderName":"Ayşe Yılmaz","holderTckn":"11111111110","coverageType":"kasko","premium":1500,"coverageLimit":50000,"status":"active","agentName":"Zeynep K...` | — |
| **P-002** | u1 GET başkasının poliçesi pol_3 (BOLA) | `GET /policies/pol_3` | tok_user1_ayse (u1, user) | 403 | HTTP `403`<br>`{"error":"Erişim engellendi","message":"Bu poliçeye erişim yetkiniz yok."}` | — |
| **P-003** | u2 GET başkasının poliçesi pol_1 (BOLA) | `GET /policies/pol_1` | tok_user2_mehmet (u2, user) | 403 | HTTP `403`<br>`{"error":"Erişim engellendi","message":"Bu poliçeye erişim yetkiniz yok."}` | — |
| **P-004** | admin GET pol_1 | `GET /policies/pol_1` | tok_admin_root (admin) | 200 | HTTP `200`<br>`{"id":"pol_1","policyNumber":"POL-2026-0001","ownerUserId":"u1","holderName":"Ayşe Yılmaz","holderTckn":"11111111110","coverageType":"kasko","premium":1500,"coverageLimit":50000,"status":"active","agentName":"Zeynep K...` | — |
| **P-005** | admin GET pol_3 | `GET /policies/pol_3` | tok_admin_root (admin) | 200 | HTTP `200`<br>`{"id":"pol_3","policyNumber":"POL-2026-0003","ownerUserId":"u2","holderName":"Mehmet Demir","holderTckn":"22222222220","coverageType":"saglik","premium":900,"coverageLimit":20000,"status":"cancelled","agentName":"Can ...` | — |
| **P-006** | u1 GET olmayan poliçe pol_999 | `GET /policies/pol_999` | tok_user1_ayse (u1, user) | 404 | HTTP `404`<br>`{"error":"Bulunamadı","message":"Poliçe bulunamadı."}` | — |
| **P-007** | GET /policies/pol_1 kimliksiz | `GET /policies/pol_1` | (Authorization başlığı yok) | 401 | HTTP `401`<br>`{"error":"Yetkisiz","message":"Geçerli bir bearer token gerekli."}` | — |
| **C-001** | u1 GET /claims (varsayılan) | `GET /claims` | tok_user1_ayse (u1, user) | 200 + Claim şeması | HTTP `200`<br>`{"data":[{"id":"clm_1","policyId":"pol_1","ownerUserId":"u1","amount":12000,"status":"submitted","description":"Çarpma hasarı","createdAt":"2026-05-02T09:00:00Z"},{"id":"clm_2","policyId":"pol_1","ownerUserId":"u1","a...` | $.data[0].claimNumber: required property missing; $.data[1].claimNumber: required property missing; $.data[2].claimNumber: required property missing; $.data[3].claimNumber: required property missing; $.data[4].claimNumber: required property missing |
| **C-002** | u2 GET /claims (varsayılan) | `GET /claims` | tok_user2_mehmet (u2, user) | 200 + Claim şeması | HTTP `200`<br>`{"data":[{"id":"clm_6","policyId":"pol_4","ownerUserId":"u2","amount":5000,"status":"approved","description":"Çarpma hasarı","createdAt":"2026-05-18T10:20:00Z"},{"id":"clm_7","policyId":"pol_3","ownerUserId":"u2","amo...` | $.data[0].claimNumber: required property missing; $.data[1].claimNumber: required property missing |
| **C-003** | admin GET /claims | `GET /claims` | tok_admin_root (admin) | 200 + tüm talepler | HTTP `200`<br>`{"data":[{"id":"clm_1","policyId":"pol_1","ownerUserId":"u1","amount":12000,"status":"submitted","description":"Çarpma hasarı","createdAt":"2026-05-02T09:00:00Z"},{"id":"clm_2","policyId":"pol_1","ownerUserId":"u1","a...` | $.data[0].claimNumber: required property missing; $.data[1].claimNumber: required property missing; $.data[2].claimNumber: required property missing; $.data[3].claimNumber: required property missing; $.data[4].claimNumber: required property missing; $.data[5].claimNumber: required property missing; $.data[6].claimNumber: required property missing |
| **C-004** | GET /claims kimliksiz | `GET /claims` | (Authorization başlığı yok) | 401 | HTTP `401`<br>`{"error":"Yetkisiz","message":"Geçerli bir bearer token gerekli."}` | — |
| **C-005** | u1 GET /claims?page=1&pageSize=2 (sayfa 1) | `GET /claims?page=1&pageSize=2` | tok_user1_ayse (u1, user) | 200, 2 kayıt, meta.total=5 | HTTP `200`<br>`{"data":[{"id":"clm_1","policyId":"pol_1","ownerUserId":"u1","amount":12000,"status":"submitted","description":"Çarpma hasarı","createdAt":"2026-05-02T09:00:00Z"},{"id":"clm_2","policyId":"pol_1","ownerUserId":"u1","a...` | $.data[0].claimNumber: required property missing; $.data[1].claimNumber: required property missing |
| **C-006** | u1 GET /claims?page=2&pageSize=2 (sayfa 2) | `GET /claims?page=2&pageSize=2` | tok_user1_ayse (u1, user) | 200, 2 kayıt, meta.total=5 | HTTP `200`<br>`{"data":[{"id":"clm_3","policyId":"pol_2","ownerUserId":"u1","amount":3000,"status":"approved","description":"Su baskını","createdAt":"2026-06-01T08:15:00Z"},{"id":"clm_4","policyId":"pol_5","ownerUserId":"u1","amount...` | $.data[0].claimNumber: required property missing; $.data[1].claimNumber: required property missing |
| **C-007** | u1 GET /claims?page=3&pageSize=2 (sayfa 3) | `GET /claims?page=3&pageSize=2` | tok_user1_ayse (u1, user) | 200, 1 kayıt, meta.total=5 | HTTP `200`<br>`{"data":[{"id":"clm_5","policyId":"pol_2","ownerUserId":"u1","amount":2000,"status":"submitted","description":"Hırsızlık","createdAt":"2026-07-03T16:05:00Z"}],"meta":{"page":3,"pageSize":2,"total":1}}` | $.data[0].claimNumber: required property missing |
| **C-008** | u1 GET /claims?page=4&pageSize=2 (boş sayfa) | `GET /claims?page=4&pageSize=2` | tok_user1_ayse (u1, user) | 200, 0 kayıt, meta.total=5 | HTTP `200`<br>`{"data":[],"meta":{"page":4,"pageSize":2,"total":0}}` | — |
| **C-009** | u1 GET /claims?policyId=pol_1 (kendi poliçesi) | `GET /claims?policyId=pol_1` | tok_user1_ayse (u1, user) | 200, yalnız pol_1 talepleri (2) | HTTP `200`<br>`{"data":[{"id":"clm_1","policyId":"pol_1","ownerUserId":"u1","amount":12000,"status":"submitted","description":"Çarpma hasarı","createdAt":"2026-05-02T09:00:00Z"},{"id":"clm_2","policyId":"pol_1","ownerUserId":"u1","a...` | $.data[0].claimNumber: required property missing; $.data[1].claimNumber: required property missing |
| **C-010** | u1 GET /claims?policyId=pol_4 (u2'nin poliçesi - BOLA query) | `GET /claims?policyId=pol_4` | tok_user1_ayse (u1, user) | 403 veya boş (u2 talebi sızmamalı) | HTTP `200`<br>`{"data":[{"id":"clm_6","policyId":"pol_4","ownerUserId":"u2","amount":5000,"status":"approved","description":"Çarpma hasarı","createdAt":"2026-05-18T10:20:00Z"}],"meta":{"page":1,"pageSize":20,"total":1}}` | — |
| **C-011** | u2 GET /claims?policyId=pol_1 (u1'in poliçesi - BOLA query) | `GET /claims?policyId=pol_1` | tok_user2_mehmet (u2, user) | 403 veya boş (u1 talebi sızmamalı) | HTTP `200`<br>`{"data":[{"id":"clm_1","policyId":"pol_1","ownerUserId":"u1","amount":12000,"status":"submitted","description":"Çarpma hasarı","createdAt":"2026-05-02T09:00:00Z"},{"id":"clm_2","policyId":"pol_1","ownerUserId":"u1","a...` | — |
| **C-012** | u1 GET /claims?page=0&pageSize=20 (sınır altı page) | `GET /claims?page=0&pageSize=20` | tok_user1_ayse (u1, user) | 400 | HTTP `200`<br>`{"data":[],"meta":{"page":0,"pageSize":20,"total":0}}` | — |
| **C-013** | u1 GET /claims?page=-1 (negatif page) | `GET /claims?page=-1` | tok_user1_ayse (u1, user) | 400 | HTTP `200`<br>`{"data":[],"meta":{"page":-1,"pageSize":20,"total":0}}` | — |
| **C-014** | u1 GET /claims?pageSize=0 (sınır altı pageSize) | `GET /claims?pageSize=0` | tok_user1_ayse (u1, user) | 400 | HTTP `200`<br>`{"data":[],"meta":{"page":1,"pageSize":0,"total":0}}` | — |
| **C-015** | u1 GET /claims?pageSize=101 (sınır üstü pageSize) | `GET /claims?pageSize=101` | tok_user1_ayse (u1, user) | 400 | HTTP `200`<br>`{"data":[{"id":"clm_1","policyId":"pol_1","ownerUserId":"u1","amount":12000,"status":"submitted","description":"Çarpma hasarı","createdAt":"2026-05-02T09:00:00Z"},{"id":"clm_2","policyId":"pol_1","ownerUserId":"u1","a...` | — |
| **C-016** | u1 GET /claims?page=abc&pageSize=xyz (yanlış tip) | `GET /claims?page=abc&pageSize=xyz` | tok_user1_ayse (u1, user) | 400 | HTTP `200`<br>`{"data":[],"meta":{"page":null,"pageSize":null,"total":0}}` | — |
| **CD-001** | u1 GET kendi hasarı clm_1 | `GET /claims/clm_1` | tok_user1_ayse (u1, user) | 200 | HTTP `200`<br>`{"id":"clm_1","policyId":"pol_1","ownerUserId":"u1","amount":12000,"status":"submitted","description":"Çarpma hasarı","createdAt":"2026-05-02T09:00:00Z"}` | $.claimNumber: required property missing |
| **CD-002** | u1 GET başkasının hasarı clm_6 (BOLA) | `GET /claims/clm_6` | tok_user1_ayse (u1, user) | 403 | HTTP `403`<br>`{"error":"Erişim engellendi","message":"Bu hasar talebine erişim yetkiniz yok."}` | — |
| **CD-003** | u2 GET başkasının hasarı clm_1 (BOLA) | `GET /claims/clm_1` | tok_user2_mehmet (u2, user) | 403 | HTTP `403`<br>`{"error":"Erişim engellendi","message":"Bu hasar talebine erişim yetkiniz yok."}` | — |
| **CD-004** | admin GET clm_1 | `GET /claims/clm_1` | tok_admin_root (admin) | 200 | HTTP `200`<br>`{"id":"clm_1","policyId":"pol_1","ownerUserId":"u1","amount":12000,"status":"submitted","description":"Çarpma hasarı","createdAt":"2026-05-02T09:00:00Z"}` | $.claimNumber: required property missing |
| **CD-005** | u1 GET olmayan hasar clm_999 | `GET /claims/clm_999` | tok_user1_ayse (u1, user) | 404 | HTTP `404`<br>`{"error":"Bulunamadı","message":"Hasar talebi bulunamadı."}` | — |
| **CD-006** | GET /claims/clm_1 kimliksiz | `GET /claims/clm_1` | (Authorization başlığı yok) | 401 | HTTP `401`<br>`{"error":"Yetkisiz","message":"Geçerli bir bearer token gerekli."}` | — |
| **AD-001** | admin GET /admin/policies | `GET /admin/policies` | tok_admin_root (admin) | 200 | HTTP `200`<br>`[{"id":"pol_1","policyNumber":"POL-2026-0001","ownerUserId":"u1","holderName":"Ayşe Yılmaz","holderTckn":"11111111110","coverageType":"kasko","premium":1500,"coverageLimit":50000,"status":"active","agentName":"Zeynep ...` | — |
| **AD-002** | u1 GET /admin/policies (BFLA) | `GET /admin/policies` | tok_user1_ayse (u1, user) | 403 | HTTP `403`<br>`{"error":"Erişim engellendi","message":"Yönetici yetkisi gerekli."}` | — |
| **AD-003** | u2 GET /admin/policies (BFLA) | `GET /admin/policies` | tok_user2_mehmet (u2, user) | 403 | HTTP `403`<br>`{"error":"Erişim engellendi","message":"Yönetici yetkisi gerekli."}` | — |
| **AD-004** | GET /admin/policies kimliksiz | `GET /admin/policies` | (Authorization başlığı yok) | 401 | HTTP `401`<br>`{"error":"Yetkisiz","message":"Geçerli bir bearer token gerekli."}` | — |
| **AD-005** | admin GET /admin/stats | `GET /admin/stats` | tok_admin_root (admin) | 200 | HTTP `200`<br>`{"totalPolicies":5,"totalClaims":7,"totalPremium":9800}` | — |
| **AD-006** | u1 GET /admin/stats (BFLA) | `GET /admin/stats` | tok_user1_ayse (u1, user) | 403 | HTTP `200`<br>`{"totalPolicies":5,"totalClaims":7,"totalPremium":9800}` | $.error: required property missing |
| **AD-007** | u2 GET /admin/stats (BFLA) | `GET /admin/stats` | tok_user2_mehmet (u2, user) | 403 | HTTP `200`<br>`{"totalPolicies":5,"totalClaims":7,"totalPremium":9800}` | $.error: required property missing |
| **AD-008** | GET /admin/stats kimliksiz | `GET /admin/stats` | (Authorization başlığı yok) | 401 | HTTP `401`<br>`{"error":"Yetkisiz","message":"Geçerli bir bearer token gerekli."}` | — |
| **M-001** | POST /claims bozuk JSON | `POST /claims`<br>Gövde: `{bad json` | tok_user1_ayse (u1, user); `Content-Type: application/json` | 400 (500/stack yok) | HTTP `400`<br>`{"error":"Geçersiz JSON","detail":"Expected property name or '}' in JSON at position 1 (line 1 column 2)","stack":"SyntaxError: Expected property name or '}' in JSON at position 1 (line 1 column 2)\n    at JSON.parse ...` | — |
| **M-002** | POST /claims boş gövde | `POST /claims`<br>Gövde: `` | tok_user1_ayse (u1, user); `Content-Type: application/json` | 400 (500/stack yok) | HTTP `400`<br>`{"error":"Eksik alan","message":"policyId ve amount zorunludur."}` | — |
| **M-003** | POST /claims JSON array gövde | `POST /claims`<br>Gövde: `[]` | tok_user1_ayse (u1, user); `Content-Type: application/json` | 400 (500/stack yok) | HTTP `400`<br>`{"error":"Eksik alan","message":"policyId ve amount zorunludur."}` | — |
| **M-004** | POST /claims JSON null gövde | `POST /claims`<br>Gövde: `null` | tok_user1_ayse (u1, user); `Content-Type: application/json` | 400 (500/stack yok) | Bağlantı koptu / Hata (`-1`)<br>`ConnectionResetError(10054, 'Varolan bir bağlantı uzaktaki bir ana bilgisayar tarafından zorla kapatıldı', None, 10054, None)` | Response is not valid JSON |
| **M-005** | PATCH /policies/pol_1 bozuk JSON | `PATCH /policies/pol_1`<br>Gövde: `{bad json` | tok_user1_ayse (u1, user); `Content-Type: application/json` | 400 (500/stack yok) | HTTP `400`<br>`{"error":"Geçersiz JSON","detail":"Expected property name or '}' in JSON at position 1 (line 1 column 2)","stack":"SyntaxError: Expected property name or '}' in JSON at position 1 (line 1 column 2)\n    at JSON.parse ...` | — |
| **M-006** | POST /claims Content-Type: text/plain | `POST /claims`<br>Gövde: `{"policyId":"pol_1","amount":10}` | tok_user1_ayse (u1, user); `Content-Type: text/plain` | 400 veya 415 (500 yok) | HTTP `200`<br>`{"id":"clm_8","policyId":"pol_1","ownerUserId":"u1","amount":10,"status":"submitted","description":"","createdAt":"2026-08-01T00:00:00Z"}` | — |
| **M-007** | DELETE /policies/pol_1 (tanımsız metod) | `DELETE /policies/pol_1` | tok_user1_ayse (u1, user) | 404 veya 405 | HTTP `405`<br>`{"error":"Yöntem desteklenmiyor"}` | — |
| **M-008** | GET /policies/..%2Fadmin%2Fpolicies (path traversal) | `GET /policies/..%2Fadmin%2Fpolicies` | tok_user1_ayse (u1, user) | 400 veya 404 | HTTP `404`<br>`{"error":"Bulunamadı","message":"Poliçe bulunamadı."}` | — |

## Bölüm 2 — Poliçe Güncelleme, Hasar Oluşturma, İş Kuralları, Mass Assignment ve Idempotency (Batch 2)

| Kayıt ID | Açıklama | İstek | Token / Başlık | Beklenen | Gerçekleşen | Şema / Doğrulama Notu |
|---|---|---|---|---|---|---|
| **PA-001** | PATCH /policies/pol_1 kimliksiz | `PATCH /policies/pol_1`<br>Gövde: `{"holderName": "X"}` | (Authorization başlığı yok); `Content-Type: application/json` | 401 | HTTP `401`<br>`{"error":"Yetkisiz","message":"Geçerli bir bearer token gerekli."}` | — |
| **PA-002** | u1 PATCH başkasının poliçesi pol_3 (BOLA) | `PATCH /policies/pol_3`<br>Gövde: `{"holderName": "Hacklenen"}` | tok_user1_ayse (u1, user); `Content-Type: application/json` | 403 | HTTP `403`<br>`{"error":"Erişim engellendi","message":"Bu poliçeye erişim yetkiniz yok."}` | — |
| **PA-003** | u2 GET pol_3 (BOLA PATCH sonrası doğrulama) | `GET /policies/pol_3` | tok_user2_mehmet (u2, user) | 200 (değişmemiş olmalı) | HTTP `200`<br>`{"id":"pol_3","policyNumber":"POL-2026-0003","ownerUserId":"u2","holderName":"Mehmet Demir","holderTckn":"22222222220","coverageType":"saglik","premium":900,"coverageLimit":20000,"status":"cancelled","agentName":"Can ...` | — |
| **PA-004** | u2 PATCH başkasının poliçesi pol_1 (BOLA) | `PATCH /policies/pol_1`<br>Gövde: `{"holderName": "Hacklenen"}` | tok_user2_mehmet (u2, user); `Content-Type: application/json` | 403 | HTTP `403`<br>`{"error":"Erişim engellendi","message":"Bu poliçeye erişim yetkiniz yok."}` | — |
| **PA-005** | u1 GET pol_1 (BOLA PATCH sonrası doğrulama) | `GET /policies/pol_1` | tok_user1_ayse (u1, user) | 200 (değişmemiş olmalı) | HTTP `200`<br>`{"id":"pol_1","policyNumber":"POL-2026-0001","ownerUserId":"u1","holderName":"Ayşe Yılmaz","holderTckn":"11111111110","coverageType":"kasko","premium":1500,"coverageLimit":50000,"status":"active","agentName":"Zeynep K...` | — |
| **PA-006** | u1 PATCH olmayan poliçe pol_999 | `PATCH /policies/pol_999`<br>Gövde: `{"holderName": "Test"}` | tok_user1_ayse (u1, user); `Content-Type: application/json` | 404 | HTTP `404`<br>`{"error":"Bulunamadı","message":"Poliçe bulunamadı."}` | — |
| **PA-007** | u1 PATCH pol_1 geçerli holderName ve agentName (Türkçe) | `PATCH /policies/pol_1`<br>Gövde: `{"holderName": "İsmail Şahin Çörekçioğlu", "agentName": "Gülşah Öğüt"}` | tok_user1_ayse (u1, user); `Content-Type: application/json` | 200 | HTTP `200`<br>`{"id":"pol_1","policyNumber":"POL-2026-0001","ownerUserId":"u1","holderName":"İsmail Şahin Çörekçioğlu","holderTckn":"11111111110","coverageType":"kasko","premium":1500,"coverageLimit":50000,"status":"active","agentNa...` | — |
| **PA-008** | u1 GET pol_1 (PA-007 doğrulama) | `GET /policies/pol_1` | tok_user1_ayse (u1, user) | 200, güncellenmiş olmalı | HTTP `200`<br>`{"id":"pol_1","policyNumber":"POL-2026-0001","ownerUserId":"u1","holderName":"İsmail Şahin Çörekçioğlu","holderTckn":"11111111110","coverageType":"kasko","premium":1500,"coverageLimit":50000,"status":"active","agentNa...` | — |
| **PA-009** | u1 PATCH pol_1 yalnız agentName=null | `PATCH /policies/pol_1`<br>Gövde: `{"agentName": null}` | tok_user1_ayse (u1, user); `Content-Type: application/json` | 200, agentName=null | HTTP `200`<br>`{"id":"pol_1","policyNumber":"POL-2026-0001","ownerUserId":"u1","holderName":"İsmail Şahin Çörekçioğlu","holderTckn":"11111111110","coverageType":"kasko","premium":1500,"coverageLimit":50000,"status":"active","agentNa...` | — |
| **PA-010** | u1 PATCH pol_1 boş gövde {} | `PATCH /policies/pol_1`<br>Gövde: `{}` | tok_user1_ayse (u1, user); `Content-Type: application/json` | 200 veya 400 | HTTP `200`<br>`{"id":"pol_1","policyNumber":"POL-2026-0001","ownerUserId":"u1","holderName":"İsmail Şahin Çörekçioğlu","holderTckn":"11111111110","coverageType":"kasko","premium":1500,"coverageLimit":50000,"status":"active","agentNa...` | — |
| **PA-011** | u1 PATCH pol_1 holderName=12345 (yanlış tip) | `PATCH /policies/pol_1`<br>Gövde: `{"holderName": 12345}` | tok_user1_ayse (u1, user); `Content-Type: application/json` | 400 | HTTP `200`<br>`{"id":"pol_1","policyNumber":"POL-2026-0001","ownerUserId":"u1","holderName":12345,"holderTckn":"11111111110","coverageType":"kasko","premium":1500,"coverageLimit":50000,"status":"active","agentName":null,"startDate":...` | $.error: required property missing |
| **PA-012** | u1 PATCH pol_1 holderName=null | `PATCH /policies/pol_1`<br>Gövde: `{"holderName": null}` | tok_user1_ayse (u1, user); `Content-Type: application/json` | 400 | HTTP `200`<br>`{"id":"pol_1","policyNumber":"POL-2026-0001","ownerUserId":"u1","holderName":null,"holderTckn":"11111111110","coverageType":"kasko","premium":1500,"coverageLimit":50000,"status":"active","agentName":null,"startDate":"...` | $.error: required property missing |
| **PA-013** | u1 PATCH pol_1 holderName='' (boş string) | `PATCH /policies/pol_1`<br>Gövde: `{"holderName": ""}` | tok_user1_ayse (u1, user); `Content-Type: application/json` | 400 | HTTP `200`<br>`{"id":"pol_1","policyNumber":"POL-2026-0001","ownerUserId":"u1","holderName":"","holderTckn":"11111111110","coverageType":"kasko","premium":1500,"coverageLimit":50000,"status":"active","agentName":null,"startDate":"20...` | — |
| **PA-014** | u1 PATCH pol_1 holderName='   ' (yalnız boşluk) | `PATCH /policies/pol_1`<br>Gövde: `{"holderName": "   "}` | tok_user1_ayse (u1, user); `Content-Type: application/json` | 400 | HTTP `200`<br>`{"id":"pol_1","policyNumber":"POL-2026-0001","ownerUserId":"u1","holderName":"   ","holderTckn":"11111111110","coverageType":"kasko","premium":1500,"coverageLimit":50000,"status":"active","agentName":null,"startDate":...` | — |
| **PA-015** | u1 PATCH pol_1 agentName=12345 (yanlış tip) | `PATCH /policies/pol_1`<br>Gövde: `{"agentName": 12345}` | tok_user1_ayse (u1, user); `Content-Type: application/json` | 400 | HTTP `200`<br>`{"id":"pol_1","policyNumber":"POL-2026-0001","ownerUserId":"u1","holderName":"   ","holderTckn":"11111111110","coverageType":"kasko","premium":1500,"coverageLimit":50000,"status":"active","agentName":12345,"startDate"...` | $.error: required property missing |
| **PA-016** | u1 PATCH pol_1 salt-okunur alan enjeksiyonu (mass assignment) | `PATCH /policies/pol_1`<br>Gövde: `{"holderName": "Ayşe Yılmaz", "agentName": "Zeynep Kaya", "premium": 1, "coverageLimit": 9999999, "status": "cancelle...` | tok_user1_ayse (u1, user); `Content-Type: application/json` | salt-okunur alanlar yok sayılmalı (değişmemeli) | HTTP `200`<br>`{"id":"pol_1","policyNumber":"POL-2026-0001","ownerUserId":"u1","holderName":"Ayşe Yılmaz","holderTckn":"11111111110","coverageType":"kasko","premium":1500,"coverageLimit":50000,"status":"cancelled","agentName":"Zeyne...` | — |
| **PA-017** | admin GET pol_1 (PA-016 mass assignment kalıcılık doğrulaması) | `GET /policies/pol_1` | tok_admin_root (admin) | 200, salt-okunur alanlar orijinal kalmalı | HTTP `200`<br>`{"id":"pol_1","policyNumber":"POL-2026-0001","ownerUserId":"u1","holderName":"Ayşe Yılmaz","holderTckn":"11111111110","coverageType":"kasko","premium":1500,"coverageLimit":50000,"status":"cancelled","agentName":"Zeyne...` | — |
| **PA-018** | u1 PATCH pol_1 yalnızca status='cancelled' gönderme | `PATCH /policies/pol_1`<br>Gövde: `{"status": "cancelled"}` | tok_user1_ayse (u1, user); `Content-Type: application/json` | 400 veya 200 (status değişmemeli) | HTTP `200`<br>`{"id":"pol_1","policyNumber":"POL-2026-0001","ownerUserId":"u1","holderName":"Ayşe Yılmaz","holderTckn":"11111111110","coverageType":"kasko","premium":1500,"coverageLimit":50000,"status":"cancelled","agentName":"Zeyne...` | — |
| **PA-019** | admin GET pol_1 (PA-018 sonrası doğrulama) | `GET /policies/pol_1` | tok_admin_root (admin) | 200, status='active' kalmalı | HTTP `200`<br>`{"id":"pol_1","policyNumber":"POL-2026-0001","ownerUserId":"u1","holderName":"Ayşe Yılmaz","holderTckn":"11111111110","coverageType":"kasko","premium":1500,"coverageLimit":50000,"status":"cancelled","agentName":"Zeyne...` | — |
| **PA-020** | u1 PATCH pol_1 orijinal değerlere geri yükleme | `PATCH /policies/pol_1`<br>Gövde: `{"holderName": "Ayşe Yılmaz", "agentName": "Zeynep Kaya"}` | tok_user1_ayse (u1, user); `Content-Type: application/json` | 200 | HTTP `200`<br>`{"id":"pol_1","policyNumber":"POL-2026-0001","ownerUserId":"u1","holderName":"Ayşe Yılmaz","holderTckn":"11111111110","coverageType":"kasko","premium":1500,"coverageLimit":50000,"status":"cancelled","agentName":"Zeyne...` | — |
| **PA-021** | admin PATCH pol_3 (yönetici başka kullanıcının poliçesini güncelleyebiliyor mu?) | `PATCH /policies/pol_3`<br>Gövde: `{"agentName": "Can Öz"}` | tok_admin_root (admin); `Content-Type: application/json` | 200 veya 403 | HTTP `200`<br>`{"id":"pol_3","policyNumber":"POL-2026-0003","ownerUserId":"u2","holderName":"Mehmet Demir","holderTckn":"22222222220","coverageType":"saglik","premium":900,"coverageLimit":20000,"status":"cancelled","agentName":"Can ...` | — |
| **PC-001** | POST /claims kimliksiz | `POST /claims`<br>Gövde: `{"policyId": "pol_1", "amount": 100}` | (Authorization başlığı yok); `Content-Type: application/json` | 401 | HTTP `401`<br>`{"error":"Yetkisiz","message":"Geçerli bir bearer token gerekli."}` | — |
| **PC-002** | u1 POST /claims başkasının poliçesi pol_4 (BOLA gövde) | `POST /claims`<br>Gövde: `{"policyId": "pol_4", "amount": 100, "description": "BOLA test"}` | tok_user1_ayse (u1, user); `Content-Type: application/json` | 403 | HTTP `403`<br>`{"error":"Erişim engellendi","message":"Bu poliçe için hasar talebi oluşturamazsınız."}` | — |
| **PC-003** | u2 GET /claims (PC-002 sonrası u2 verisi kontrolü) | `GET /claims` | tok_user2_mehmet (u2, user) | 200, yeni kayıt olmamalı | HTTP `200`<br>`{"data":[{"id":"clm_6","policyId":"pol_4","ownerUserId":"u2","amount":5000,"status":"approved","description":"Çarpma hasarı","createdAt":"2026-05-18T10:20:00Z"},{"id":"clm_7","policyId":"pol_3","ownerUserId":"u2","amo...` | — |
| **PC-004** | u2 POST /claims başkasının poliçesi pol_1 (BOLA gövde) | `POST /claims`<br>Gövde: `{"policyId": "pol_1", "amount": 100}` | tok_user2_mehmet (u2, user); `Content-Type: application/json` | 403 | HTTP `403`<br>`{"error":"Erişim engellendi","message":"Bu poliçe için hasar talebi oluşturamazsınız."}` | — |
| **PC-005** | u1 POST /claims olmayan poliçe pol_999 | `POST /claims`<br>Gövde: `{"policyId": "pol_999", "amount": 100}` | tok_user1_ayse (u1, user); `Content-Type: application/json` | 404 | HTTP `404`<br>`{"error":"Bulunamadı","message":"Poliçe bulunamadı."}` | — |
| **PC-006** | u1 POST /claims boş gövde {} | `POST /claims`<br>Gövde: `{}` | tok_user1_ayse (u1, user); `Content-Type: application/json` | 400 | HTTP `400`<br>`{"error":"Eksik alan","message":"policyId ve amount zorunludur."}` | — |
| **PC-007** | u1 POST /claims policyId eksik | `POST /claims`<br>Gövde: `{"amount": 100}` | tok_user1_ayse (u1, user); `Content-Type: application/json` | 400 | HTTP `400`<br>`{"error":"Eksik alan","message":"policyId ve amount zorunludur."}` | — |
| **PC-008** | u1 POST /claims amount eksik | `POST /claims`<br>Gövde: `{"policyId": "pol_1"}` | tok_user1_ayse (u1, user); `Content-Type: application/json` | 400 | HTTP `400`<br>`{"error":"Eksik alan","message":"policyId ve amount zorunludur."}` | — |
| **PC-009** | u1 POST /claims policyId=12345 (yanlış tip) | `POST /claims`<br>Gövde: `{"policyId": 12345, "amount": 100}` | tok_user1_ayse (u1, user); `Content-Type: application/json` | 400 | HTTP `404`<br>`{"error":"Bulunamadı","message":"Poliçe bulunamadı."}` | — |
| **PC-010** | u1 POST /claims amount='abc' (yanlış tip) | `POST /claims`<br>Gövde: `{"policyId": "pol_1", "amount": "abc"}` | tok_user1_ayse (u1, user); `Content-Type: application/json` | 400 | HTTP `400`<br>`{"error":"Geçersiz tip","message":"amount sayısal olmalıdır."}` | — |
| **PC-011** | u1 POST /claims amount='100' (string sayı) | `POST /claims`<br>Gövde: `{"policyId": "pol_1", "amount": "100"}` | tok_user1_ayse (u1, user); `Content-Type: application/json` | 400 | HTTP `400`<br>`{"error":"Geçersiz tip","message":"amount sayısal olmalıdır."}` | — |
| **PC-012** | u1 POST /claims amount=null | `POST /claims`<br>Gövde: `{"policyId": "pol_1", "amount": null}` | tok_user1_ayse (u1, user); `Content-Type: application/json` | 400 | HTTP `400`<br>`{"error":"Geçersiz tip","message":"amount sayısal olmalıdır."}` | — |
| **PC-013** | u1 POST /claims amount=true | `POST /claims`<br>Gövde: `{"policyId": "pol_1", "amount": true}` | tok_user1_ayse (u1, user); `Content-Type: application/json` | 400 | HTTP `400`<br>`{"error":"Geçersiz tip","message":"amount sayısal olmalıdır."}` | — |
| **PC-014** | u1 POST /claims description=12345 (yanlış tip) | `POST /claims`<br>Gövde: `{"policyId": "pol_1", "amount": 100, "description": 12345}` | tok_user1_ayse (u1, user); `Content-Type: application/json` | 400 | HTTP `200`<br>`{"id":"clm_9","policyId":"pol_1","ownerUserId":"u1","amount":100,"status":"submitted","description":"","createdAt":"2026-08-01T00:00:00Z"}` | $.error: required property missing |
| **PC-015** | u1 POST /claims amount=0 (alt sınır altı) | `POST /claims`<br>Gövde: `{"policyId": "pol_1", "amount": 0}` | tok_user1_ayse (u1, user); `Content-Type: application/json` | 400 veya 422 | HTTP `200`<br>`{"id":"clm_10","policyId":"pol_1","ownerUserId":"u1","amount":0,"status":"submitted","description":"","createdAt":"2026-08-01T00:00:00Z"}` | $.error: required property missing |
| **PC-016** | u1 POST /claims amount=-50 (negatif) | `POST /claims`<br>Gövde: `{"policyId": "pol_1", "amount": -50}` | tok_user1_ayse (u1, user); `Content-Type: application/json` | 400 veya 422 | HTTP `200`<br>`{"id":"clm_11","policyId":"pol_1","ownerUserId":"u1","amount":-50,"status":"submitted","description":"","createdAt":"2026-08-01T00:00:00Z"}` | $.error: required property missing |
| **PC-017** | u1 POST /claims amount=0.99 (minimum=1 altı) | `POST /claims`<br>Gövde: `{"policyId": "pol_1", "amount": 0.99}` | tok_user1_ayse (u1, user); `Content-Type: application/json` | 400 veya 422 | HTTP `200`<br>`{"id":"clm_12","policyId":"pol_1","ownerUserId":"u1","amount":0.99,"status":"submitted","description":"","createdAt":"2026-08-01T00:00:00Z"}` | $.error: required property missing |
| **PC-018** | u1 POST /claims amount=0.5 (pozitif ama <1) | `POST /claims`<br>Gövde: `{"policyId": "pol_1", "amount": 0.5}` | tok_user1_ayse (u1, user); `Content-Type: application/json` | 400 veya 422 | HTTP `200`<br>`{"id":"clm_13","policyId":"pol_1","ownerUserId":"u1","amount":0.5,"status":"submitted","description":"","createdAt":"2026-08-01T00:00:00Z"}` | $.error: required property missing |
| **PC-019** | u1 POST /claims amount=1 (minimum geçerli sınır) | `POST /claims`<br>Gövde: `{"policyId": "pol_1", "amount": 1, "description": "Alt sınır 1 TL"}` | tok_user1_ayse (u1, user); `Content-Type: application/json` | 201 | HTTP `200`<br>`{"id":"clm_14","policyId":"pol_1","ownerUserId":"u1","amount":1,"status":"submitted","description":"Alt sınır 1 TL","createdAt":"2026-08-01T00:00:00Z"}` | $.claimNumber: required property missing |
| **PC-020** | u1 POST /claims amount=75001 (pol_5 teminat limiti 75000 + 1) | `POST /claims`<br>Gövde: `{"policyId": "pol_5", "amount": 75001}` | tok_user1_ayse (u1, user); `Content-Type: application/json` | 422 | HTTP `200`<br>`{"id":"clm_15","policyId":"pol_5","ownerUserId":"u1","amount":75001,"status":"submitted","description":"","createdAt":"2026-08-01T00:00:00Z"}` | $.error: required property missing |
| **PC-021** | u1 POST /claims amount=75000.01 (pol_5 teminat limiti + 0.01) | `POST /claims`<br>Gövde: `{"policyId": "pol_5", "amount": 75000.01}` | tok_user1_ayse (u1, user); `Content-Type: application/json` | 422 | HTTP `200`<br>`{"id":"clm_16","policyId":"pol_5","ownerUserId":"u1","amount":75000.01,"status":"submitted","description":"","createdAt":"2026-08-01T00:00:00Z"}` | $.error: required property missing |
| **PC-022** | u1 POST /claims amount=75000 (pol_5 tam teminat limiti) | `POST /claims`<br>Gövde: `{"policyId": "pol_5", "amount": 75000, "description": "Tam limit"}` | tok_user1_ayse (u1, user); `Content-Type: application/json` | 201 | HTTP `200`<br>`{"id":"clm_17","policyId":"pol_5","ownerUserId":"u1","amount":75000,"status":"submitted","description":"Tam limit","createdAt":"2026-08-01T00:00:00Z"}` | $.claimNumber: required property missing |
| **PC-023** | u2 POST /claims iptal edilmiş poliçe pol_3 (status=cancelled) | `POST /claims`<br>Gövde: `{"policyId": "pol_3", "amount": 500, "description": "İptal poliçe testi"}` | tok_user2_mehmet (u2, user); `Content-Type: application/json` | 422/400 veya 201 (iş kuralı kontrolü) | HTTP `200`<br>`{"id":"clm_18","policyId":"pol_3","ownerUserId":"u2","amount":500,"status":"submitted","description":"İptal poliçe testi","createdAt":"2026-08-01T00:00:00Z"}` | — |
| **PC-024** | u1 POST /claims description=null | `POST /claims`<br>Gövde: `{"policyId": "pol_1", "amount": 25, "description": null}` | tok_user1_ayse (u1, user); `Content-Type: application/json` | 201 | HTTP `200`<br>`{"id":"clm_19","policyId":"pol_1","ownerUserId":"u1","amount":25,"status":"submitted","description":"","createdAt":"2026-08-01T00:00:00Z"}` | $.claimNumber: required property missing |
| **PC-025** | u1 POST /claims SQLi + XSS description | `POST /claims`<br>Gövde: `{"policyId": "pol_1", "amount": 30, "description": "' OR '1'='1' -- <script>alert(1)</script>"}` | tok_user1_ayse (u1, user); `Content-Type: application/json` | 201 veya 400 (500 yok) | HTTP `200`<br>`{"id":"clm_20","policyId":"pol_1","ownerUserId":"u1","amount":30,"status":"submitted","description":"' OR '1'='1' -- <script>alert(1)</script>","createdAt":"2026-08-01T00:00:00Z"}` | — |
| **PC-026** | u1 POST /claims mass assignment + ekstra alanlar | `POST /claims`<br>Gövde: `{"policyId": "pol_1", "amount": 50, "id": "clm_hack999", "claimNumber": "CLM-HACK", "ownerUserId": "u2", "status": "a...` | tok_user1_ayse (u1, user); `Content-Type: application/json` | 400 (additionalProperties: false) veya salt-okunur alanlar yok sayılmalı | HTTP `200`<br>`{"id":"clm_21","policyId":"pol_1","ownerUserId":"u1","amount":50,"status":"submitted","description":"","createdAt":"2026-08-01T00:00:00Z"}` | — |
| **ID-001** | u1 POST /claims Idempotency-Key ilk istek | `POST /claims`<br>Gövde: `{"policyId": "pol_2", "amount": 111, "description": "Idem test"}` | tok_user1_ayse (u1, user); `Idempotency-Key: idem-qa-001`, `Content-Type: application/json` | 201 | HTTP `200`<br>`{"id":"clm_22","policyId":"pol_2","ownerUserId":"u1","amount":111,"status":"submitted","description":"Idem test","createdAt":"2026-08-01T00:00:00Z"}` | $.claimNumber: required property missing |
| **ID-002** | u1 POST /claims aynı Idempotency-Key tekrar istek | `POST /claims`<br>Gövde: `{"policyId": "pol_2", "amount": 111, "description": "Idem test"}` | tok_user1_ayse (u1, user); `Idempotency-Key: idem-qa-001`, `Content-Type: application/json` | aynı kaydı dönmeli, yeni kayıt açmamalı | HTTP `200`<br>`{"id":"clm_23","policyId":"pol_2","ownerUserId":"u1","amount":111,"status":"submitted","description":"Idem test","createdAt":"2026-08-01T00:00:00Z"}` | $.claimNumber: required property missing |
| **ID-003** | u1 POST /claims aynı Idempotency-Key FARKLI gövde | `POST /claims`<br>Gövde: `{"policyId": "pol_2", "amount": 222, "description": "Farklı tutar"}` | tok_user1_ayse (u1, user); `Idempotency-Key: idem-qa-001`, `Content-Type: application/json` | 409/422 veya ilk kayıt | HTTP `200`<br>`{"id":"clm_24","policyId":"pol_2","ownerUserId":"u1","amount":222,"status":"submitted","description":"Farklı tutar","createdAt":"2026-08-01T00:00:00Z"}` | — |
| **ID-004** | u2 POST /claims u1'in kullandığı Idempotency-Key ile (cross-user izolasyon) | `POST /claims`<br>Gövde: `{"policyId": "pol_4", "amount": 333, "description": "u2 aynı anahtar"}` | tok_user2_mehmet (u2, user); `Idempotency-Key: idem-qa-001`, `Content-Type: application/json` | u2 için yeni kayıt açmalı (u1 kaydını dönmemeli!) | HTTP `200`<br>`{"id":"clm_25","policyId":"pol_4","ownerUserId":"u2","amount":333,"status":"submitted","description":"u2 aynı anahtar","createdAt":"2026-08-01T00:00:00Z"}` | — |
| **ID-005** | u1 POST /claims hatalı istekte Idempotency-Key (422) | `POST /claims`<br>Gövde: `{"policyId": "pol_1", "amount": 999999}` | tok_user1_ayse (u1, user); `Idempotency-Key: idem-fail-001`, `Content-Type: application/json` | 422 | HTTP `200`<br>`{"id":"clm_26","policyId":"pol_1","ownerUserId":"u1","amount":999999,"status":"submitted","description":"","createdAt":"2026-08-01T00:00:00Z"}` | $.error: required property missing |
| **ID-006** | u1 POST /claims hatalı anahtarla geçerli tekrar | `POST /claims`<br>Gövde: `{"policyId": "pol_1", "amount": 15, "description": "Retry after 422"}` | tok_user1_ayse (u1, user); `Idempotency-Key: idem-fail-001`, `Content-Type: application/json` | 201 (başarısız istek anahtarı kilitlememeli) | HTTP `200`<br>`{"id":"clm_27","policyId":"pol_1","ownerUserId":"u1","amount":15,"status":"submitted","description":"Retry after 422","createdAt":"2026-08-01T00:00:00Z"}` | $.claimNumber: required property missing |
| **ID-RACE-1** | Paralel Idempotency-Key #1 | `POST /claims`<br>Gövde: `{"policyId": "pol_2", "amount": 444, "description": "Race 1"}` | tok_user1_ayse (u1, user); `Idempotency-Key: idem-race-001`, `Content-Type: application/json` | aynı tek kayıt | HTTP `200`<br>`{"id":"clm_28","policyId":"pol_2","ownerUserId":"u1","amount":444,"status":"submitted","description":"Race 1","createdAt":"2026-08-01T00:00:00Z"}` | — |
| **ID-RACE-2** | Paralel Idempotency-Key #2 | `POST /claims`<br>Gövde: `{"policyId": "pol_2", "amount": 444, "description": "Race 2"}` | tok_user1_ayse (u1, user); `Idempotency-Key: idem-race-001`, `Content-Type: application/json` | aynı tek kayıt | HTTP `200`<br>`{"id":"clm_29","policyId":"pol_2","ownerUserId":"u1","amount":444,"status":"submitted","description":"Race 2","createdAt":"2026-08-01T00:00:00Z"}` | — |
| **FD-001** | admin GET /claims?pageSize=100 (mutasyonlar sonrası toplam kontrol) | `GET /claims?pageSize=100` | tok_admin_root (admin) | 200 | HTTP `200`<br>`{"data":[{"id":"clm_1","policyId":"pol_1","ownerUserId":"u1","amount":12000,"status":"submitted","description":"Çarpma hasarı","createdAt":"2026-05-02T09:00:00Z"},{"id":"clm_2","policyId":"pol_1","ownerUserId":"u1","a...` | — |
| **FD-002** | admin GET /admin/stats (mutasyonlar sonrası istatistik tutarlılığı) | `GET /admin/stats` | tok_admin_root (admin) | 200, totalClaims == toplam hasar sayısı | HTTP `200`<br>`{"totalPolicies":5,"totalClaims":29,"totalPremium":9800}` | — |

## Bölüm 3 — Ek Keşif Testleri, Tip Zorlamaları, Yöntemler ve Başlık Duyarlılığı (Batch 3)

| Kayıt ID | Açıklama | İstek | Token / Başlık | Beklenen | Gerçekleşen | Şema / Doğrulama Notu |
|---|---|---|---|---|---|---|
| **E-001** | POST /claims exact 'Idempotency-Key' #1 | `POST /claims`<br>Gövde: `{"policyId": "pol_2", "amount": 77, "description": "Exact header 1"}` | tok_user1_ayse (u1, user); `Idempotency-Key: exact-case-key-1`, `Content-Type: application/json` | 201 | HTTP `200`<br>`{"id":"clm_30","policyId":"pol_2","ownerUserId":"u1","amount":77,"status":"submitted","description":"Exact header 1","createdAt":"2026-08-01T00:00:00Z"}` | — |
| **E-002** | POST /claims exact 'Idempotency-Key' #2 | `POST /claims`<br>Gövde: `{"policyId": "pol_2", "amount": 77, "description": "Exact header 1"}` | tok_user1_ayse (u1, user); `Idempotency-Key: exact-case-key-1`, `Content-Type: application/json` | same id | HTTP `200`<br>`{"id":"clm_31","policyId":"pol_2","ownerUserId":"u1","amount":77,"status":"submitted","description":"Exact header 1","createdAt":"2026-08-01T00:00:00Z"}` | — |
| **E-003** | PATCH pol_1 status='invalid_enum' (enum dışı status enjeksiyonu) | `PATCH /policies/pol_1`<br>Gövde: `{"status": "invalid_enum"}` | tok_user1_ayse (u1, user); `Content-Type: application/json` | reddedilmeli/yok sayılmalı | HTTP `200`<br>`{"id":"pol_1","policyNumber":"POL-2026-0001","ownerUserId":"u1","holderName":"Ayşe Yılmaz","holderTckn":"11111111110","coverageType":"kasko","premium":1500,"coverageLimit":50000,"status":"invalid_enum","agentName":"Ze...` | — |
| **E-004** | PATCH pol_1 status='active' (geri yükleme denemesi) | `PATCH /policies/pol_1`<br>Gövde: `{"status": "active"}` | tok_user1_ayse (u1, user); `Content-Type: application/json` | yok sayılmalı (ama değişebilir) | HTTP `200`<br>`{"id":"pol_1","policyNumber":"POL-2026-0001","ownerUserId":"u1","holderName":"Ayşe Yılmaz","holderTckn":"11111111110","coverageType":"kasko","premium":1500,"coverageLimit":50000,"status":"active","agentName":"Zeynep K...` | — |
| **E-005** | PATCH pol_1 yalnızca unknownField | `PATCH /policies/pol_1`<br>Gövde: `{"unknownField": "xyz"}` | tok_user1_ayse (u1, user); `Content-Type: application/json` | 400 veya yok sayılma | HTTP `200`<br>`{"id":"pol_1","policyNumber":"POL-2026-0001","ownerUserId":"u1","holderName":"Ayşe Yılmaz","holderTckn":"11111111110","coverageType":"kasko","premium":1500,"coverageLimit":50000,"status":"active","agentName":"Zeynep K...` | — |
| **E-006** | PATCH pol_1 empty body '' | `PATCH /policies/pol_1`<br>Gövde: `` | tok_user1_ayse (u1, user); `Content-Type: application/json` | 400 | HTTP `200`<br>`{"id":"pol_1","policyNumber":"POL-2026-0001","ownerUserId":"u1","holderName":"Ayşe Yılmaz","holderTckn":"11111111110","coverageType":"kasko","premium":1500,"coverageLimit":50000,"status":"active","agentName":"Zeynep K...` | — |
| **E-007** | PATCH pol_1 JSON array '[]' | `PATCH /policies/pol_1`<br>Gövde: `[]` | tok_user1_ayse (u1, user); `Content-Type: application/json` | 400 | HTTP `200`<br>`{"id":"pol_1","policyNumber":"POL-2026-0001","ownerUserId":"u1","holderName":"Ayşe Yılmaz","holderTckn":"11111111110","coverageType":"kasko","premium":1500,"coverageLimit":50000,"status":"active","agentName":"Zeynep K...` | — |
| **E-008** | PATCH pol_1 JSON string '"hello"' | `PATCH /policies/pol_1`<br>Gövde: `"hello"` | tok_user1_ayse (u1, user); `Content-Type: application/json` | 400 | HTTP `200`<br>`{"id":"pol_1","policyNumber":"POL-2026-0001","ownerUserId":"u1","holderName":"Ayşe Yılmaz","holderTckn":"11111111110","coverageType":"kasko","premium":1500,"coverageLimit":50000,"status":"active","agentName":"Zeynep K...` | — |
| **E-009** | PATCH pol_1 XSS/SQLi holderName & agentName | `PATCH /policies/pol_1`<br>Gövde: `{"holderName": "<script>alert(1)</script>", "agentName": "' OR '1'='1' --"}` | tok_user1_ayse (u1, user); `Content-Type: application/json` | 200 veya 400 (500 yok) | HTTP `200`<br>`{"id":"pol_1","policyNumber":"POL-2026-0001","ownerUserId":"u1","holderName":"<script>alert(1)</script>","holderTckn":"11111111110","coverageType":"kasko","premium":1500,"coverageLimit":50000,"status":"active","agentN...` | — |
| **E-010** | PATCH pol_1 geri yükle | `PATCH /policies/pol_1`<br>Gövde: `{"holderName": "Ayşe Yılmaz", "agentName": "Zeynep Kaya", "status": "active"}` | tok_user1_ayse (u1, user); `Content-Type: application/json` | 200 | HTTP `200`<br>`{"id":"pol_1","policyNumber":"POL-2026-0001","ownerUserId":"u1","holderName":"Ayşe Yılmaz","holderTckn":"11111111110","coverageType":"kasko","premium":1500,"coverageLimit":50000,"status":"active","agentName":"Zeynep K...` | — |
| **E-011** | POST /claims amount=[100] (array) | `POST /claims`<br>Gövde: `{"policyId": "pol_1", "amount": [100]}` | tok_user1_ayse (u1, user); `Content-Type: application/json` | 400 | HTTP `400`<br>`{"error":"Geçersiz tip","message":"amount sayısal olmalıdır."}` | — |
| **E-012** | POST /claims amount=[] (boş array -> JS Number([])===0!) | `POST /claims`<br>Gövde: `{"policyId": "pol_1", "amount": []}` | tok_user1_ayse (u1, user); `Content-Type: application/json` | 400 | HTTP `400`<br>`{"error":"Geçersiz tip","message":"amount sayısal olmalıdır."}` | — |
| **E-013** | POST /claims amount={} (object) | `POST /claims`<br>Gövde: `{"policyId": "pol_1", "amount": {}}` | tok_user1_ayse (u1, user); `Content-Type: application/json` | 400 | HTTP `400`<br>`{"error":"Geçersiz tip","message":"amount sayısal olmalıdır."}` | — |
| **E-014** | POST /claims policyId=['pol_1'] (array) | `POST /claims`<br>Gövde: `{"policyId": ["pol_1"], "amount": 10}` | tok_user1_ayse (u1, user); `Content-Type: application/json` | 400 | HTTP `404`<br>`{"error":"Bulunamadı","message":"Poliçe bulunamadı."}` | — |
| **E-015** | POST /claims admin on pol_1 (ownerUserId kim oluyor?) | `POST /claims`<br>Gövde: `{"policyId": "pol_1", "amount": 42, "description": "Admin claim"}` | tok_admin_root (admin); `Content-Type: application/json` | 201/403 | HTTP `200`<br>`{"id":"clm_32","policyId":"pol_1","ownerUserId":"admin","amount":42,"status":"submitted","description":"Admin claim","createdAt":"2026-08-01T00:00:00Z"}` | — |
| **E-016** | POST /claims prototype pollution payload | `POST /claims`<br>Gövde: `{"policyId":"pol_1","amount":12,"__proto__":{"isAdmin":true}}` | tok_user1_ayse (u1, user); `Content-Type: application/json` | 400 veya yok sayılma | HTTP `200`<br>`{"id":"clm_33","policyId":"pol_1","ownerUserId":"u1","amount":12,"status":"submitted","description":"","createdAt":"2026-08-01T00:00:00Z"}` | — |
| **E-017** | GET /claims?policyId=pol_999 (olmayan policyId) | `GET /claims?policyId=pol_999` | tok_user1_ayse (u1, user) | 200 boş veya 404 | HTTP `200`<br>`{"data":[],"meta":{"page":1,"pageSize":20,"total":0}}` | — |
| **E-018** | GET /claims?page=1.5&pageSize=2.5 (ondalıklı sayfa) | `GET /claims?page=1.5&pageSize=2.5` | tok_user1_ayse (u1, user) | 400 | HTTP `200`<br>`{"data":[{"id":"clm_1","policyId":"pol_1","ownerUserId":"u1","amount":12000,"status":"submitted","description":"Çarpma hasarı","createdAt":"2026-05-02T09:00:00Z"},{"id":"clm_2","policyId":"pol_1","ownerUserId":"u1","a...` | — |
| **E-019** | GET /policies/ (sonda eğik çizgi) | `GET /policies/` | tok_user1_ayse (u1, user) | 200 veya 404 | HTTP `404`<br>`{"error":"Bulunamadı","message":"Kaynak yok."}` | — |
| **E-020** | POST /policies (desteklenmeyen metod) | `POST /policies`<br>Gövde: `{"holderName": "Test"}` | tok_user1_ayse (u1, user); `Content-Type: application/json` | 405 veya 404 | HTTP `404`<br>`{"error":"Bulunamadı","message":"Kaynak yok."}` | — |
| **E-021** | PUT /policies/pol_1 (desteklenmeyen metod) | `PUT /policies/pol_1`<br>Gövde: `{"holderName": "Test"}` | tok_user1_ayse (u1, user); `Content-Type: application/json` | 405 veya 404 | HTTP `405`<br>`{"error":"Yöntem desteklenmiyor"}` | — |
| **E-022** | DELETE /claims/clm_1 (desteklenmeyen metod) | `DELETE /claims/clm_1` | tok_user1_ayse (u1, user) | 405 veya 404 | HTTP `404`<br>`{"error":"Bulunamadı","message":"Kaynak yok."}` | — |
| **E-023** | OPTIONS /policies | `OPTIONS /policies` | (Authorization başlığı yok) | 204/405/401 | HTTP `401`<br>`{"error":"Yetkisiz","message":"Geçerli bir bearer token gerekli."}` | — |
| **E-024** | GET /claims/clm_8 (null testi öncesi varlık kontrolü) | `GET /claims/clm_8` | tok_user1_ayse (u1, user) | 200 | HTTP `200`<br>`{"id":"clm_8","policyId":"pol_1","ownerUserId":"u1","amount":10,"status":"submitted","description":"","createdAt":"2026-08-01T00:00:00Z"}` | — |
| **E-025** | PATCH /policies/pol_1 body='null' | `PATCH /policies/pol_1`<br>Gövde: `null` | tok_user1_ayse (u1, user); `Content-Type: application/json` | 400 (bağlantı kopmamalı / çökmemeli) | Bağlantı koptu / Hata (`-1`)<br>`ConnectionResetError(10054, 'Varolan bir bağlantı uzaktaki bir ana bilgisayar tarafından zorla kapatıldı', None, 10054, None)` | — |
| **E-026** | POST /claims body='null' | `POST /claims`<br>Gövde: `null` | tok_user1_ayse (u1, user); `Content-Type: application/json` | 400 (bağlantı kopmamalı / çökmemeli) | Bağlantı koptu / Hata (`-1`)<br>`ConnectionResetError(10054, 'Varolan bir bağlantı uzaktaki bir ana bilgisayar tarafından zorla kapatıldı', None, 10054, None)` | — |
| **E-027** | GET /claims/clm_8 (null testi SONRASI varlık ve sunucu canlılık kontrolü) | `GET /claims/clm_8` | tok_user1_ayse (u1, user) | 200 | Bağlantı koptu / Hata (`-1`)<br>`ConnectionRefusedError(10061, 'Hedef makine etkin olarak reddettiğinden bağlantı kurulamadı', None, 10061, None)` | — |

## Bölüm 4 — JSON null Çökme İzolasyonu ve Bellek Kaybı Doğrulaması (Batch 4)

| Kayıt ID | Açıklama | İstek | Token / Başlık | Beklenen | Gerçekleşen | Şema / Doğrulama Notu |
|---|---|---|---|---|---|---|
| **N-001** | u1 POST /claims yeni kayıt (BOLA ve crash izleme için) | `POST /claims`<br>Gövde: `{"policyId": "pol_1", "amount": 250, "description": "Test hasarı"}` | tok_user1_ayse (u1, user) | 201 | HTTP `200`<br>`{"id":"clm_12","policyId":"pol_1","ownerUserId":"u1","amount":250,"status":"submitted","description":"Test hasarı","createdAt":"2026-08-01T00:00:00Z"}` | — |
| **N-002** | u1 GET /claims/clm_12 (sahip erişimi) | `GET /claims/clm_12` | tok_user1_ayse (u1, user) | 200 | HTTP `200`<br>`{"id":"clm_12","policyId":"pol_1","ownerUserId":"u1","amount":250,"status":"submitted","description":"Test hasarı","createdAt":"2026-08-01T00:00:00Z"}` | — |
| **N-003** | u2 GET /claims/clm_12 (başka kullanıcı BOLA) | `GET /claims/clm_12` | tok_user2_mehmet (u2, user) | 403 | HTTP `403`<br>`{"error":"Erişim engellendi","message":"Bu hasar talebine erişim yetkiniz yok."}` | — |
| **N-004** | u1 PATCH /policies/pol_1 body='null' (tekil çökme testi) | `PATCH /policies/pol_1`<br>Gövde: `null` | tok_user1_ayse (u1, user) | 400 | Bağlantı koptu / Hata (`-1`)<br>`ConnectionResetError(10054, 'Varolan bir bağlantı uzaktaki bir ana bilgisayar tarafından zorla kapatıldı', None, 10054, None)` | — |
| **N-005** | u1 GET /claims/clm_12 (PATCH null sonrası bellek kaybı kontrolü) | `GET /claims/clm_12` | tok_user1_ayse (u1, user) | 200 (sunucu çökmediyse durmalı) | HTTP `404`<br>`{"error":"Bulunamadı","message":"Hasar talebi bulunamadı."}` | — |
| **N-006** | u1 POST /claims yeniden kayıt | `POST /claims`<br>Gövde: `{"policyId": "pol_1", "amount": 250, "description": "Test hasarı 2"}` | tok_user1_ayse (u1, user) | 201 | HTTP `200`<br>`{"id":"clm_8","policyId":"pol_1","ownerUserId":"u1","amount":250,"status":"submitted","description":"Test hasarı 2","createdAt":"2026-08-01T00:00:00Z"}` | — |
| **N-007** | u1 POST /claims body='null' (tekil çökme testi) | `POST /claims`<br>Gövde: `null` | tok_user1_ayse (u1, user) | 400 | Bağlantı koptu / Hata (`-1`)<br>`ConnectionResetError(10054, 'Varolan bir bağlantı uzaktaki bir ana bilgisayar tarafından zorla kapatıldı', None, 10054, None)` | — |
| **N-008** | u1 GET /claims/clm_8 (POST null sonrası bellek kaybı kontrolü) | `GET /claims/clm_8` | tok_user1_ayse (u1, user) | 200 (sunucu çökmediyse durmalı) | HTTP `404`<br>`{"error":"Bulunamadı","message":"Hasar talebi bulunamadı."}` | — |
| **N-009** | GET /health (yeniden başlama sonrası canlılık) | `GET /health` | (Authorization başlığı yok) | 200 | HTTP `200`<br>`{"status":"ok","service":"anadolu-guven-sigorta-api"}` | — |

## Bölüm 5 — Temiz Durumda Ek Sınır ve Şema Kontrolleri (Batch 5)

| Kayıt ID | Açıklama | İstek | Token / Başlık | Beklenen | Gerçekleşen | Şema / Doğrulama Notu |
|---|---|---|---|---|---|---|
| **X-001** | u1 GET /policies?ownerUserId=u2 (sorgu parametresiyle BOLA denemesi) | `GET /policies?ownerUserId=u2` | tok_user1_ayse (u1, user) | 200 (yalnız u1 poliçeleri dönmeli) | HTTP `200`<br>`[{"id":"pol_1","policyNumber":"POL-2026-0001","ownerUserId":"u1","holderName":"Ayşe Yılmaz","holderTckn":"11111111110","coverageType":"kasko","premium":1500,"coverageLimit":50000,"status":"active","agentName":"Zeynep ...` | — |
| **X-002** | u1 PATCH pol_1 additionalProperties testi (ekstra alan) | `PATCH /policies/pol_1`<br>Gövde: `{"holderName": "Ayşe Yılmaz", "extraField": "test"}` | tok_user1_ayse (u1, user); `Content-Type: application/json` | 400 (PolicyUpdate additionalProperties:false) veya yok sayılma | HTTP `200`<br>`{"id":"pol_1","policyNumber":"POL-2026-0001","ownerUserId":"u1","holderName":"Ayşe Yılmaz","holderTckn":"11111111110","coverageType":"kasko","premium":1500,"coverageLimit":50000,"status":"active","agentName":"Zeynep K...` | — |
| **X-003** | u1 PATCH pol_1 holderName=true (boolean yanlış tip) | `PATCH /policies/pol_1`<br>Gövde: `{"holderName": true}` | tok_user1_ayse (u1, user); `Content-Type: application/json` | 400 | HTTP `200`<br>`{"id":"pol_1","policyNumber":"POL-2026-0001","ownerUserId":"u1","holderName":true,"holderTckn":"11111111110","coverageType":"kasko","premium":1500,"coverageLimit":50000,"status":"active","agentName":"Zeynep Kaya","sta...` | $.error: required property missing |
| **X-004** | u1 PATCH pol_1 holderName={} (object yanlış tip) | `PATCH /policies/pol_1`<br>Gövde: `{"holderName": {}}` | tok_user1_ayse (u1, user); `Content-Type: application/json` | 400 | HTTP `200`<br>`{"id":"pol_1","policyNumber":"POL-2026-0001","ownerUserId":"u1","holderName":{},"holderTckn":"11111111110","coverageType":"kasko","premium":1500,"coverageLimit":50000,"status":"active","agentName":"Zeynep Kaya","start...` | $.error: required property missing |
| **X-005** | u1 PATCH pol_1 agentName=[] (array yanlış tip) | `PATCH /policies/pol_1`<br>Gövde: `{"agentName": []}` | tok_user1_ayse (u1, user); `Content-Type: application/json` | 400 | HTTP `200`<br>`{"id":"pol_1","policyNumber":"POL-2026-0001","ownerUserId":"u1","holderName":{},"holderTckn":"11111111110","coverageType":"kasko","premium":1500,"coverageLimit":50000,"status":"active","agentName":[],"startDate":"2026...` | $.error: required property missing |
| **X-006** | u1 PATCH pol_1 geri yükle | `PATCH /policies/pol_1`<br>Gövde: `{"holderName": "Ayşe Yılmaz", "agentName": "Zeynep Kaya"}` | tok_user1_ayse (u1, user); `Content-Type: application/json` | 200 | HTTP `200`<br>`{"id":"pol_1","policyNumber":"POL-2026-0001","ownerUserId":"u1","holderName":"Ayşe Yılmaz","holderTckn":"11111111110","coverageType":"kasko","premium":1500,"coverageLimit":50000,"status":"active","agentName":"Zeynep K...` | — |
| **X-007** | u1 PATCH pol_1 çok uzun holderName (5000 karakter) | `PATCH /policies/pol_1`<br>Gövde: `{"holderName": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA...` | tok_user1_ayse (u1, user); `Content-Type: application/json` | 400 veya 200 (500 yok) | HTTP `200`<br>`{"id":"pol_1","policyNumber":"POL-2026-0001","ownerUserId":"u1","holderName":"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA...` | — |
| **X-008** | u1 PATCH pol_1 geri yükle | `PATCH /policies/pol_1`<br>Gövde: `{"holderName": "Ayşe Yılmaz", "agentName": "Zeynep Kaya"}` | tok_user1_ayse (u1, user); `Content-Type: application/json` | 200 | HTTP `200`<br>`{"id":"pol_1","policyNumber":"POL-2026-0001","ownerUserId":"u1","holderName":"Ayşe Yılmaz","holderTckn":"11111111110","coverageType":"kasko","premium":1500,"coverageLimit":50000,"status":"active","agentName":"Zeynep K...` | — |
| **X-009** | u1 POST /claims çok uzun description (10000 karakter) | `POST /claims`<br>Gövde: `{"policyId": "pol_1", "amount": 100, "description": "BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB...` | tok_user1_ayse (u1, user); `Content-Type: application/json` | 400 veya 201 (500 yok) | HTTP `200`<br>`{"id":"clm_8","policyId":"pol_1","ownerUserId":"u1","amount":100,"status":"submitted","description":"BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB...` | — |
| **X-010** | u1 POST /claims amount=1e308 (aşırı büyük sayı) | `POST /claims`<br>Gövde: `{"policyId": "pol_1", "amount": 1e+308}` | tok_user1_ayse (u1, user); `Content-Type: application/json` | 422 (teminat limitini aşıyor) | HTTP `200`<br>`{"id":"clm_9","policyId":"pol_1","ownerUserId":"u1","amount":1e+308,"status":"submitted","description":"","createdAt":"2026-08-01T00:00:00Z"}` | — |
| **X-011** | u1 POST /claims description=[] (array yanlış tip) | `POST /claims`<br>Gövde: `{"policyId": "pol_1", "amount": 50, "description": ["x"]}` | tok_user1_ayse (u1, user); `Content-Type: application/json` | 400 | HTTP `200`<br>`{"id":"clm_10","policyId":"pol_1","ownerUserId":"u1","amount":50,"status":"submitted","description":"","createdAt":"2026-08-01T00:00:00Z"}` | $.error: required property missing |
| **X-012** | u1 POST /claims Content-Type: application/json; charset=utf-8 | `POST /claims`<br>Gövde: `{"policyId": "pol_1", "amount": 50, "description": "UTF-8 başlık testi"}` | tok_user1_ayse (u1, user); `Content-Type: application/json; charset=utf-8` | 201 | HTTP `200`<br>`{"id":"clm_11","policyId":"pol_1","ownerUserId":"u1","amount":50,"status":"submitted","description":"UTF-8 başlık testi","createdAt":"2026-08-01T00:00:00Z"}` | — |
| **X-013** | u1 GET /claims?page=1&pageSize=2 (temiz pagination kontrolü) | `GET /claims?page=1&pageSize=2` | tok_user1_ayse (u1, user) | 200, meta.total tüm kayıt sayısı olmalı | HTTP `200`<br>`{"data":[{"id":"clm_1","policyId":"pol_1","ownerUserId":"u1","amount":12000,"status":"submitted","description":"Çarpma hasarı","createdAt":"2026-05-02T09:00:00Z"},{"id":"clm_2","policyId":"pol_1","ownerUserId":"u1","a...` | — |
| **X-014** | u1 GET /claims?page=99&pageSize=2 (son sayfa sonrası) | `GET /claims?page=99&pageSize=2` | tok_user1_ayse (u1, user) | 200, data=[], meta.total > 0 olmalı | HTTP `200`<br>`{"data":[],"meta":{"page":99,"pageSize":2,"total":0}}` | — |
| **X-015** | POST /health (desteklenmeyen metod) | `POST /health`<br>Gövde: `{}` | (Authorization başlığı yok); `Content-Type: application/json` | 404 veya 405 | HTTP `401`<br>`{"error":"Yetkisiz","message":"Geçerli bir bearer token gerekli."}` | — |
| **X-016** | GET /policies/pol_1?unexpected=1 | `GET /policies/pol_1` | tok_user1_ayse (u1, user) | 200 | HTTP `200`<br>`{"id":"pol_1","policyNumber":"POL-2026-0001","ownerUserId":"u1","holderName":"Ayşe Yılmaz","holderTckn":"11111111110","coverageType":"kasko","premium":1500,"coverageLimit":50000,"status":"active","agentName":"Zeynep K...` | — |

## Ek: Tam Yanıt Örnekleri (Kısaltılmamış Kanıtlar)

### C-001 — u1 GET /claims (varsayılan)
- **İstek:** `GET /claims` (`auth: u1`)
- **Yanıt Durumu:** `200`
```text
{"data":[{"id":"clm_1","policyId":"pol_1","ownerUserId":"u1","amount":12000,"status":"submitted","description":"Çarpma hasarı","createdAt":"2026-05-02T09:00:00Z"},{"id":"clm_2","policyId":"pol_1","ownerUserId":"u1","amount":8000,"status":"rejected","description":"Cam kırığı","createdAt":"2026-05-10T11:30:00Z"},{"id":"clm_3","policyId":"pol_2","ownerUserId":"u1","amount":3000,"status":"approved","description":"Su baskını","createdAt":"2026-06-01T08:15:00Z"},{"id":"clm_4","policyId":"pol_5","ownerUserId":"u1","amount":15000,"status":"submitted","description":"Trafik kazası","createdAt":"2026-06-20T14:45:00Z"},{"id":"clm_5","policyId":"pol_2","ownerUserId":"u1","amount":2000,"status":"submitted","description":"Hırsızlık","createdAt":"2026-07-03T16:05:00Z"}],"meta":{"page":1,"pageSize":20,"total":5}}
```

### C-005 — u1 GET /claims?page=1&pageSize=2 (sayfa 1)
- **İstek:** `GET /claims?page=1&pageSize=2` (`auth: u1`)
- **Yanıt Durumu:** `200`
```text
{"data":[{"id":"clm_1","policyId":"pol_1","ownerUserId":"u1","amount":12000,"status":"submitted","description":"Çarpma hasarı","createdAt":"2026-05-02T09:00:00Z"},{"id":"clm_2","policyId":"pol_1","ownerUserId":"u1","amount":8000,"status":"rejected","description":"Cam kırığı","createdAt":"2026-05-10T11:30:00Z"}],"meta":{"page":1,"pageSize":2,"total":2}}
```

### C-007 — u1 GET /claims?page=3&pageSize=2 (sayfa 3)
- **İstek:** `GET /claims?page=3&pageSize=2` (`auth: u1`)
- **Yanıt Durumu:** `200`
```text
{"data":[{"id":"clm_5","policyId":"pol_2","ownerUserId":"u1","amount":2000,"status":"submitted","description":"Hırsızlık","createdAt":"2026-07-03T16:05:00Z"}],"meta":{"page":3,"pageSize":2,"total":1}}
```

### C-008 — u1 GET /claims?page=4&pageSize=2 (boş sayfa)
- **İstek:** `GET /claims?page=4&pageSize=2` (`auth: u1`)
- **Yanıt Durumu:** `200`
```text
{"data":[],"meta":{"page":4,"pageSize":2,"total":0}}
```

### C-010 — u1 GET /claims?policyId=pol_4 (u2'nin poliçesi - BOLA query)
- **İstek:** `GET /claims?policyId=pol_4` (`auth: u1`)
- **Yanıt Durumu:** `200`
```text
{"data":[{"id":"clm_6","policyId":"pol_4","ownerUserId":"u2","amount":5000,"status":"approved","description":"Çarpma hasarı","createdAt":"2026-05-18T10:20:00Z"}],"meta":{"page":1,"pageSize":20,"total":1}}
```

### C-011 — u2 GET /claims?policyId=pol_1 (u1'in poliçesi - BOLA query)
- **İstek:** `GET /claims?policyId=pol_1` (`auth: u2`)
- **Yanıt Durumu:** `200`
```text
{"data":[{"id":"clm_1","policyId":"pol_1","ownerUserId":"u1","amount":12000,"status":"submitted","description":"Çarpma hasarı","createdAt":"2026-05-02T09:00:00Z"},{"id":"clm_2","policyId":"pol_1","ownerUserId":"u1","amount":8000,"status":"rejected","description":"Cam kırığı","createdAt":"2026-05-10T11:30:00Z"}],"meta":{"page":1,"pageSize":20,"total":2}}
```

### C-012 — u1 GET /claims?page=0&pageSize=20 (sınır altı page)
- **İstek:** `GET /claims?page=0&pageSize=20` (`auth: u1`)
- **Yanıt Durumu:** `200`
```text
{"data":[],"meta":{"page":0,"pageSize":20,"total":0}}
```

### C-015 — u1 GET /claims?pageSize=101 (sınır üstü pageSize)
- **İstek:** `GET /claims?pageSize=101` (`auth: u1`)
- **Yanıt Durumu:** `200`
```text
{"data":[{"id":"clm_1","policyId":"pol_1","ownerUserId":"u1","amount":12000,"status":"submitted","description":"Çarpma hasarı","createdAt":"2026-05-02T09:00:00Z"},{"id":"clm_2","policyId":"pol_1","ownerUserId":"u1","amount":8000,"status":"rejected","description":"Cam kırığı","createdAt":"2026-05-10T11:30:00Z"},{"id":"clm_3","policyId":"pol_2","ownerUserId":"u1","amount":3000,"status":"approved","description":"Su baskını","createdAt":"2026-06-01T08:15:00Z"},{"id":"clm_4","policyId":"pol_5","ownerUserId":"u1","amount":15000,"status":"submitted","description":"Trafik kazası","createdAt":"2026-06-20T14:45:00Z"},{"id":"clm_5","policyId":"pol_2","ownerUserId":"u1","amount":2000,"status":"submitted","description":"Hırsızlık","createdAt":"2026-07-03T16:05:00Z"}],"meta":{"page":1,"pageSize":101,"total":5}}
```

### C-016 — u1 GET /claims?page=abc&pageSize=xyz (yanlış tip)
- **İstek:** `GET /claims?page=abc&pageSize=xyz` (`auth: u1`)
- **Yanıt Durumu:** `200`
```text
{"data":[],"meta":{"page":null,"pageSize":null,"total":0}}
```

### CD-001 — u1 GET kendi hasarı clm_1
- **İstek:** `GET /claims/clm_1` (`auth: u1`)
- **Yanıt Durumu:** `200`
```text
{"id":"clm_1","policyId":"pol_1","ownerUserId":"u1","amount":12000,"status":"submitted","description":"Çarpma hasarı","createdAt":"2026-05-02T09:00:00Z"}
```

### AD-006 — u1 GET /admin/stats (BFLA)
- **İstek:** `GET /admin/stats` (`auth: u1`)
- **Yanıt Durumu:** `200`
```text
{"totalPolicies":5,"totalClaims":7,"totalPremium":9800}
```

### AD-007 — u2 GET /admin/stats (BFLA)
- **İstek:** `GET /admin/stats` (`auth: u2`)
- **Yanıt Durumu:** `200`
```text
{"totalPolicies":5,"totalClaims":7,"totalPremium":9800}
```

### M-001 — POST /claims bozuk JSON
- **İstek:** `POST /claims` (`auth: u1`)
- **İstek Gövdesi:** `{bad json`
- **Yanıt Durumu:** `400`
```text
{"error":"Geçersiz JSON","detail":"Expected property name or '}' in JSON at position 1 (line 1 column 2)","stack":"SyntaxError: Expected property name or '}' in JSON at position 1 (line 1 column 2)\n    at JSON.parse (<anonymous>)\n    at Server.<anonymous> (C:\\eval\\servers\\R11\\server.js:216:25)\n    at process.processTicksAndRejections (node:internal/process/task_queues:104:5)"}
```

### M-004 — POST /claims JSON null gövde
- **İstek:** `POST /claims` (`auth: u1`)
- **İstek Gövdesi:** `null`
- **Yanıt Durumu:** `-1`
```text
ConnectionResetError(10054, 'Varolan bir bağlantı uzaktaki bir ana bilgisayar tarafından zorla kapatıldı', None, 10054, None)
```

### M-005 — PATCH /policies/pol_1 bozuk JSON
- **İstek:** `PATCH /policies/pol_1` (`auth: u1`)
- **İstek Gövdesi:** `{bad json`
- **Yanıt Durumu:** `400`
```text
{"error":"Geçersiz JSON","detail":"Expected property name or '}' in JSON at position 1 (line 1 column 2)","stack":"SyntaxError: Expected property name or '}' in JSON at position 1 (line 1 column 2)\n    at JSON.parse (<anonymous>)\n    at Server.<anonymous> (C:\\eval\\servers\\R11\\server.js:155:27)\n    at process.processTicksAndRejections (node:internal/process/task_queues:104:5)"}
```

### M-006 — POST /claims Content-Type: text/plain
- **İstek:** `POST /claims` (`auth: u1`)
- **İstek Gövdesi:** `{"policyId":"pol_1","amount":10}`
- **Yanıt Durumu:** `200`
```text
{"id":"clm_8","policyId":"pol_1","ownerUserId":"u1","amount":10,"status":"submitted","description":"","createdAt":"2026-08-01T00:00:00Z"}
```

### PA-011 — u1 PATCH pol_1 holderName=12345 (yanlış tip)
- **İstek:** `PATCH /policies/pol_1` (`auth: u1`)
- **Ek Başlıklar:** `{"Content-Type": "application/json"}`
- **İstek Gövdesi:** `{"holderName": 12345}`
- **Yanıt Durumu:** `200`
```text
{"id":"pol_1","policyNumber":"POL-2026-0001","ownerUserId":"u1","holderName":12345,"holderTckn":"11111111110","coverageType":"kasko","premium":1500,"coverageLimit":50000,"status":"active","agentName":null,"startDate":"2026-01-01","endDate":"2026-12-31"}
```

### PA-012 — u1 PATCH pol_1 holderName=null
- **İstek:** `PATCH /policies/pol_1` (`auth: u1`)
- **Ek Başlıklar:** `{"Content-Type": "application/json"}`
- **İstek Gövdesi:** `{"holderName": null}`
- **Yanıt Durumu:** `200`
```text
{"id":"pol_1","policyNumber":"POL-2026-0001","ownerUserId":"u1","holderName":null,"holderTckn":"11111111110","coverageType":"kasko","premium":1500,"coverageLimit":50000,"status":"active","agentName":null,"startDate":"2026-01-01","endDate":"2026-12-31"}
```

### PA-015 — u1 PATCH pol_1 agentName=12345 (yanlış tip)
- **İstek:** `PATCH /policies/pol_1` (`auth: u1`)
- **Ek Başlıklar:** `{"Content-Type": "application/json"}`
- **İstek Gövdesi:** `{"agentName": 12345}`
- **Yanıt Durumu:** `200`
```text
{"id":"pol_1","policyNumber":"POL-2026-0001","ownerUserId":"u1","holderName":"   ","holderTckn":"11111111110","coverageType":"kasko","premium":1500,"coverageLimit":50000,"status":"active","agentName":12345,"startDate":"2026-01-01","endDate":"2026-12-31"}
```

### PA-016 — u1 PATCH pol_1 salt-okunur alan enjeksiyonu (mass assignment)
- **İstek:** `PATCH /policies/pol_1` (`auth: u1`)
- **Ek Başlıklar:** `{"Content-Type": "application/json"}`
- **İstek Gövdesi:** `{"holderName": "Ayşe Yılmaz", "agentName": "Zeynep Kaya", "premium": 1, "coverageLimit": 9999999, "status": "cancelled", "ownerUserId": "u2", "policyNumber": "POL-HACK-999", "coverageType": "saglik", "holderTckn": "99999999999", "id": "pol_999", "startDate": "2020-01-01", "endDate": "2030-01-01", "role": "admin", "isAdmin": true}`
- **Yanıt Durumu:** `200`
```text
{"id":"pol_1","policyNumber":"POL-2026-0001","ownerUserId":"u1","holderName":"Ayşe Yılmaz","holderTckn":"11111111110","coverageType":"kasko","premium":1500,"coverageLimit":50000,"status":"cancelled","agentName":"Zeynep Kaya","startDate":"2026-01-01","endDate":"2026-12-31"}
```

### PA-017 — admin GET pol_1 (PA-016 mass assignment kalıcılık doğrulaması)
- **İstek:** `GET /policies/pol_1` (`auth: admin`)
- **Yanıt Durumu:** `200`
```text
{"id":"pol_1","policyNumber":"POL-2026-0001","ownerUserId":"u1","holderName":"Ayşe Yılmaz","holderTckn":"11111111110","coverageType":"kasko","premium":1500,"coverageLimit":50000,"status":"cancelled","agentName":"Zeynep Kaya","startDate":"2026-01-01","endDate":"2026-12-31"}
```

### PA-018 — u1 PATCH pol_1 yalnızca status='cancelled' gönderme
- **İstek:** `PATCH /policies/pol_1` (`auth: u1`)
- **Ek Başlıklar:** `{"Content-Type": "application/json"}`
- **İstek Gövdesi:** `{"status": "cancelled"}`
- **Yanıt Durumu:** `200`
```text
{"id":"pol_1","policyNumber":"POL-2026-0001","ownerUserId":"u1","holderName":"Ayşe Yılmaz","holderTckn":"11111111110","coverageType":"kasko","premium":1500,"coverageLimit":50000,"status":"cancelled","agentName":"Zeynep Kaya","startDate":"2026-01-01","endDate":"2026-12-31"}
```

### PC-009 — u1 POST /claims policyId=12345 (yanlış tip)
- **İstek:** `POST /claims` (`auth: u1`)
- **Ek Başlıklar:** `{"Content-Type": "application/json"}`
- **İstek Gövdesi:** `{"policyId": 12345, "amount": 100}`
- **Yanıt Durumu:** `404`
```text
{"error":"Bulunamadı","message":"Poliçe bulunamadı."}
```

### PC-014 — u1 POST /claims description=12345 (yanlış tip)
- **İstek:** `POST /claims` (`auth: u1`)
- **Ek Başlıklar:** `{"Content-Type": "application/json"}`
- **İstek Gövdesi:** `{"policyId": "pol_1", "amount": 100, "description": 12345}`
- **Yanıt Durumu:** `200`
```text
{"id":"clm_9","policyId":"pol_1","ownerUserId":"u1","amount":100,"status":"submitted","description":"","createdAt":"2026-08-01T00:00:00Z"}
```

### PC-015 — u1 POST /claims amount=0 (alt sınır altı)
- **İstek:** `POST /claims` (`auth: u1`)
- **Ek Başlıklar:** `{"Content-Type": "application/json"}`
- **İstek Gövdesi:** `{"policyId": "pol_1", "amount": 0}`
- **Yanıt Durumu:** `200`
```text
{"id":"clm_10","policyId":"pol_1","ownerUserId":"u1","amount":0,"status":"submitted","description":"","createdAt":"2026-08-01T00:00:00Z"}
```

### PC-016 — u1 POST /claims amount=-50 (negatif)
- **İstek:** `POST /claims` (`auth: u1`)
- **Ek Başlıklar:** `{"Content-Type": "application/json"}`
- **İstek Gövdesi:** `{"policyId": "pol_1", "amount": -50}`
- **Yanıt Durumu:** `200`
```text
{"id":"clm_11","policyId":"pol_1","ownerUserId":"u1","amount":-50,"status":"submitted","description":"","createdAt":"2026-08-01T00:00:00Z"}
```

### PC-017 — u1 POST /claims amount=0.99 (minimum=1 altı)
- **İstek:** `POST /claims` (`auth: u1`)
- **Ek Başlıklar:** `{"Content-Type": "application/json"}`
- **İstek Gövdesi:** `{"policyId": "pol_1", "amount": 0.99}`
- **Yanıt Durumu:** `200`
```text
{"id":"clm_12","policyId":"pol_1","ownerUserId":"u1","amount":0.99,"status":"submitted","description":"","createdAt":"2026-08-01T00:00:00Z"}
```

### PC-019 — u1 POST /claims amount=1 (minimum geçerli sınır)
- **İstek:** `POST /claims` (`auth: u1`)
- **Ek Başlıklar:** `{"Content-Type": "application/json"}`
- **İstek Gövdesi:** `{"policyId": "pol_1", "amount": 1, "description": "Alt sınır 1 TL"}`
- **Yanıt Durumu:** `200`
```text
{"id":"clm_14","policyId":"pol_1","ownerUserId":"u1","amount":1,"status":"submitted","description":"Alt sınır 1 TL","createdAt":"2026-08-01T00:00:00Z"}
```

### PC-020 — u1 POST /claims amount=75001 (pol_5 teminat limiti 75000 + 1)
- **İstek:** `POST /claims` (`auth: u1`)
- **Ek Başlıklar:** `{"Content-Type": "application/json"}`
- **İstek Gövdesi:** `{"policyId": "pol_5", "amount": 75001}`
- **Yanıt Durumu:** `200`
```text
{"id":"clm_15","policyId":"pol_5","ownerUserId":"u1","amount":75001,"status":"submitted","description":"","createdAt":"2026-08-01T00:00:00Z"}
```

### PC-021 — u1 POST /claims amount=75000.01 (pol_5 teminat limiti + 0.01)
- **İstek:** `POST /claims` (`auth: u1`)
- **Ek Başlıklar:** `{"Content-Type": "application/json"}`
- **İstek Gövdesi:** `{"policyId": "pol_5", "amount": 75000.01}`
- **Yanıt Durumu:** `200`
```text
{"id":"clm_16","policyId":"pol_5","ownerUserId":"u1","amount":75000.01,"status":"submitted","description":"","createdAt":"2026-08-01T00:00:00Z"}
```

### PC-022 — u1 POST /claims amount=75000 (pol_5 tam teminat limiti)
- **İstek:** `POST /claims` (`auth: u1`)
- **Ek Başlıklar:** `{"Content-Type": "application/json"}`
- **İstek Gövdesi:** `{"policyId": "pol_5", "amount": 75000, "description": "Tam limit"}`
- **Yanıt Durumu:** `200`
```text
{"id":"clm_17","policyId":"pol_5","ownerUserId":"u1","amount":75000,"status":"submitted","description":"Tam limit","createdAt":"2026-08-01T00:00:00Z"}
```

### PC-023 — u2 POST /claims iptal edilmiş poliçe pol_3 (status=cancelled)
- **İstek:** `POST /claims` (`auth: u2`)
- **Ek Başlıklar:** `{"Content-Type": "application/json"}`
- **İstek Gövdesi:** `{"policyId": "pol_3", "amount": 500, "description": "İptal poliçe testi"}`
- **Yanıt Durumu:** `200`
```text
{"id":"clm_18","policyId":"pol_3","ownerUserId":"u2","amount":500,"status":"submitted","description":"İptal poliçe testi","createdAt":"2026-08-01T00:00:00Z"}
```

### PC-024 — u1 POST /claims description=null
- **İstek:** `POST /claims` (`auth: u1`)
- **Ek Başlıklar:** `{"Content-Type": "application/json"}`
- **İstek Gövdesi:** `{"policyId": "pol_1", "amount": 25, "description": null}`
- **Yanıt Durumu:** `200`
```text
{"id":"clm_19","policyId":"pol_1","ownerUserId":"u1","amount":25,"status":"submitted","description":"","createdAt":"2026-08-01T00:00:00Z"}
```

### PC-026 — u1 POST /claims mass assignment + ekstra alanlar
- **İstek:** `POST /claims` (`auth: u1`)
- **Ek Başlıklar:** `{"Content-Type": "application/json"}`
- **İstek Gövdesi:** `{"policyId": "pol_1", "amount": 50, "id": "clm_hack999", "claimNumber": "CLM-HACK", "ownerUserId": "u2", "status": "approved", "createdAt": "1999-01-01T00:00:00Z", "role": "admin", "extraProp": "abc"}`
- **Yanıt Durumu:** `200`
```text
{"id":"clm_21","policyId":"pol_1","ownerUserId":"u1","amount":50,"status":"submitted","description":"","createdAt":"2026-08-01T00:00:00Z"}
```

### ID-001 — u1 POST /claims Idempotency-Key ilk istek
- **İstek:** `POST /claims` (`auth: u1`)
- **Ek Başlıklar:** `{"Idempotency-Key": "idem-qa-001", "Content-Type": "application/json"}`
- **İstek Gövdesi:** `{"policyId": "pol_2", "amount": 111, "description": "Idem test"}`
- **Yanıt Durumu:** `200`
```text
{"id":"clm_22","policyId":"pol_2","ownerUserId":"u1","amount":111,"status":"submitted","description":"Idem test","createdAt":"2026-08-01T00:00:00Z"}
```

### ID-002 — u1 POST /claims aynı Idempotency-Key tekrar istek
- **İstek:** `POST /claims` (`auth: u1`)
- **Ek Başlıklar:** `{"Idempotency-Key": "idem-qa-001", "Content-Type": "application/json"}`
- **İstek Gövdesi:** `{"policyId": "pol_2", "amount": 111, "description": "Idem test"}`
- **Yanıt Durumu:** `200`
```text
{"id":"clm_23","policyId":"pol_2","ownerUserId":"u1","amount":111,"status":"submitted","description":"Idem test","createdAt":"2026-08-01T00:00:00Z"}
```

### ID-RACE-1 — Paralel Idempotency-Key #1
- **İstek:** `POST /claims` (`auth: u1`)
- **Ek Başlıklar:** `{"Idempotency-Key": "idem-race-001", "Content-Type": "application/json"}`
- **İstek Gövdesi:** `{"policyId": "pol_2", "amount": 444, "description": "Race 1"}`
- **Yanıt Durumu:** `200`
```text
{"id":"clm_28","policyId":"pol_2","ownerUserId":"u1","amount":444,"status":"submitted","description":"Race 1","createdAt":"2026-08-01T00:00:00Z"}
```

### ID-RACE-2 — Paralel Idempotency-Key #2
- **İstek:** `POST /claims` (`auth: u1`)
- **Ek Başlıklar:** `{"Idempotency-Key": "idem-race-001", "Content-Type": "application/json"}`
- **İstek Gövdesi:** `{"policyId": "pol_2", "amount": 444, "description": "Race 2"}`
- **Yanıt Durumu:** `200`
```text
{"id":"clm_29","policyId":"pol_2","ownerUserId":"u1","amount":444,"status":"submitted","description":"Race 2","createdAt":"2026-08-01T00:00:00Z"}
```

### E-001 — POST /claims exact 'Idempotency-Key' #1
- **İstek:** `POST /claims` (`auth: u1`)
- **Ek Başlıklar:** `{"Idempotency-Key": "exact-case-key-1", "Content-Type": "application/json"}`
- **İstek Gövdesi:** `{"policyId": "pol_2", "amount": 77, "description": "Exact header 1"}`
- **Yanıt Durumu:** `200`
```text
{"id":"clm_30","policyId":"pol_2","ownerUserId":"u1","amount":77,"status":"submitted","description":"Exact header 1","createdAt":"2026-08-01T00:00:00Z"}
```

### E-002 — POST /claims exact 'Idempotency-Key' #2
- **İstek:** `POST /claims` (`auth: u1`)
- **Ek Başlıklar:** `{"Idempotency-Key": "exact-case-key-1", "Content-Type": "application/json"}`
- **İstek Gövdesi:** `{"policyId": "pol_2", "amount": 77, "description": "Exact header 1"}`
- **Yanıt Durumu:** `200`
```text
{"id":"clm_31","policyId":"pol_2","ownerUserId":"u1","amount":77,"status":"submitted","description":"Exact header 1","createdAt":"2026-08-01T00:00:00Z"}
```

### E-003 — PATCH pol_1 status='invalid_enum' (enum dışı status enjeksiyonu)
- **İstek:** `PATCH /policies/pol_1` (`auth: u1`)
- **Ek Başlıklar:** `{"Content-Type": "application/json"}`
- **İstek Gövdesi:** `{"status": "invalid_enum"}`
- **Yanıt Durumu:** `200`
```text
{"id":"pol_1","policyNumber":"POL-2026-0001","ownerUserId":"u1","holderName":"Ayşe Yılmaz","holderTckn":"11111111110","coverageType":"kasko","premium":1500,"coverageLimit":50000,"status":"invalid_enum","agentName":"Zeynep Kaya","startDate":"2026-01-01","endDate":"2026-12-31"}
```

### E-015 — POST /claims admin on pol_1 (ownerUserId kim oluyor?)
- **İstek:** `POST /claims` (`auth: admin`)
- **Ek Başlıklar:** `{"Content-Type": "application/json"}`
- **İstek Gövdesi:** `{"policyId": "pol_1", "amount": 42, "description": "Admin claim"}`
- **Yanıt Durumu:** `200`
```text
{"id":"clm_32","policyId":"pol_1","ownerUserId":"admin","amount":42,"status":"submitted","description":"Admin claim","createdAt":"2026-08-01T00:00:00Z"}
```

### N-004 — u1 PATCH /policies/pol_1 body='null' (tekil çökme testi)
- **İstek:** `PATCH /policies/pol_1` (`auth: u1`)
- **İstek Gövdesi:** `null`
- **Yanıt Durumu:** `-1`
```text
ConnectionResetError(10054, 'Varolan bir bağlantı uzaktaki bir ana bilgisayar tarafından zorla kapatıldı', None, 10054, None)
```

### N-005 — u1 GET /claims/clm_12 (PATCH null sonrası bellek kaybı kontrolü)
- **İstek:** `GET /claims/clm_12` (`auth: u1`)
- **Yanıt Durumu:** `404`
```text
{"error":"Bulunamadı","message":"Hasar talebi bulunamadı."}
```

### N-007 — u1 POST /claims body='null' (tekil çökme testi)
- **İstek:** `POST /claims` (`auth: u1`)
- **İstek Gövdesi:** `null`
- **Yanıt Durumu:** `-1`
```text
ConnectionResetError(10054, 'Varolan bir bağlantı uzaktaki bir ana bilgisayar tarafından zorla kapatıldı', None, 10054, None)
```

### N-008 — u1 GET /claims/clm_8 (POST null sonrası bellek kaybı kontrolü)
- **İstek:** `GET /claims/clm_8` (`auth: u1`)
- **Yanıt Durumu:** `404`
```text
{"error":"Bulunamadı","message":"Hasar talebi bulunamadı."}
```

### X-002 — u1 PATCH pol_1 additionalProperties testi (ekstra alan)
- **İstek:** `PATCH /policies/pol_1` (`auth: u1`)
- **Ek Başlıklar:** `{"Content-Type": "application/json"}`
- **İstek Gövdesi:** `{"holderName": "Ayşe Yılmaz", "extraField": "test"}`
- **Yanıt Durumu:** `200`
```text
{"id":"pol_1","policyNumber":"POL-2026-0001","ownerUserId":"u1","holderName":"Ayşe Yılmaz","holderTckn":"11111111110","coverageType":"kasko","premium":1500,"coverageLimit":50000,"status":"active","agentName":"Zeynep Kaya","startDate":"2026-01-01","endDate":"2026-12-31"}
```

### X-003 — u1 PATCH pol_1 holderName=true (boolean yanlış tip)
- **İstek:** `PATCH /policies/pol_1` (`auth: u1`)
- **Ek Başlıklar:** `{"Content-Type": "application/json"}`
- **İstek Gövdesi:** `{"holderName": true}`
- **Yanıt Durumu:** `200`
```text
{"id":"pol_1","policyNumber":"POL-2026-0001","ownerUserId":"u1","holderName":true,"holderTckn":"11111111110","coverageType":"kasko","premium":1500,"coverageLimit":50000,"status":"active","agentName":"Zeynep Kaya","startDate":"2026-01-01","endDate":"2026-12-31"}
```

### X-010 — u1 POST /claims amount=1e308 (aşırı büyük sayı)
- **İstek:** `POST /claims` (`auth: u1`)
- **Ek Başlıklar:** `{"Content-Type": "application/json"}`
- **İstek Gövdesi:** `{"policyId": "pol_1", "amount": 1e+308}`
- **Yanıt Durumu:** `200`
```text
{"id":"clm_9","policyId":"pol_1","ownerUserId":"u1","amount":1e+308,"status":"submitted","description":"","createdAt":"2026-08-01T00:00:00Z"}
```

### X-011 — u1 POST /claims description=[] (array yanlış tip)
- **İstek:** `POST /claims` (`auth: u1`)
- **Ek Başlıklar:** `{"Content-Type": "application/json"}`
- **İstek Gövdesi:** `{"policyId": "pol_1", "amount": 50, "description": ["x"]}`
- **Yanıt Durumu:** `200`
```text
{"id":"clm_10","policyId":"pol_1","ownerUserId":"u1","amount":50,"status":"submitted","description":"","createdAt":"2026-08-01T00:00:00Z"}
```

