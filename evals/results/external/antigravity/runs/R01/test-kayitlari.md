# Test Kayıtları — Anadolu Güven Sigorta Poliçe & Hasar API

Bu belge, `http://localhost:4101` adresinde çalışan Poliçe & Hasar API'sine karşı `openapi.yaml` sözleşmesi temel alınarak yürütülen tekrarlanabilir test isteklerinin tam kanıt kaydıdır.

## Özet

- **Toplam çalıştırılan senaryo:** 79
- **Başarılı (sözleşmeye uygun):** 37
- **Başarısız (kusur tespit edilen):** 41
- **Ek durum kanıtı:** 1
- **Kullanılan test token'ları:** `tok_user1_ayse` (Ayşe Yılmaz / `u1`), `tok_user2_mehmet` (Mehmet Demir / `u2`), `tok_admin_root` (Sistem Yöneticisi / `admin`), ayrıca kimlik doğrulamasız/hatalı token durumları.

## İstek / Yanıt Matrisi

| ID | Grup | Senaryo | İstek | Token | Durum | Sonuç | İlgili Bulgu |
|----|------|---------|-------|-------|-------|-------|--------------|
| TC-001 | 1-Auth | GET /health kimlik doğrulamasız | `GET /health` | yok | `200` | BAŞARILI | - |
| TC-002 | 1-Auth | GET /policies token olmadan | `GET /policies` | yok | `401` | BAŞARILI | - |
| TC-003 | 1-Auth | GET /policies geçersiz token | `GET /policies` | `Bearer invalid_token_123` | `401` | BAŞARILI | - |
| TC-004 | 1-Auth | GET /policies Basic auth şeması | `GET /policies` | `Basic dTE6cGFzcw==` | `401` | BAŞARILI | - |
| TC-005 | 1-Auth | GET /policies boş Bearer | `GET /policies` | `Bearer ` | `401` | BAŞARILI | - |
| TC-006 | 1-Auth | GET /policies küçük harf bearer | `GET /policies` | `bearer tok_user1_ayse` | `200` | BAŞARILI | - |
| TC-007 | 2-Policies-GET | GET /policies u1 kendi poliçeleri | `GET /policies` | u1 | `200` | BAŞARILI | - |
| TC-008 | 2-Policies-GET | GET /policies u2 kendi poliçeleri | `GET /policies` | u2 | `200` | BAŞARILI | - |
| TC-009 | 2-Policies-GET | GET /policies admin tüm poliçeler | `GET /policies` | admin | `200` | BAŞARILI | - |
| TC-010 | 2-Policies-GET | GET /policies/pol_1 u1 kendi poliçesi | `GET /policies/pol_1` | u1 | `200` | BAŞARILI | - |
| TC-011 | 2-Policies-GET | GET /policies/pol_3 u1 başkasının poliçesi (IDOR) | `GET /policies/pol_3` | u1 | `403` | BAŞARILI | - |
| TC-012 | 2-Policies-GET | GET /policies/pol_1 u2 başkasının poliçesi (IDOR) | `GET /policies/pol_1` | u2 | `403` | BAŞARILI | - |
| TC-013 | 2-Policies-GET | GET /policies/pol_3 admin erişimi | `GET /policies/pol_3` | admin | `200` | BAŞARILI | - |
| TC-014 | 2-Policies-GET | GET /policies/pol_999 olmayan poliçe | `GET /policies/pol_999` | u1 | `404` | BAŞARILI | - |
| TC-015 | 3-Policies-PATCH | PATCH /policies/pol_5 token olmadan | `PATCH /policies/pol_5` | yok | `401` | BAŞARILI | - |
| TC-016 | 3-Policies-PATCH | PATCH /policies/pol_5 u2 başkasının poliçesi | `PATCH /policies/pol_5` | u2 | `403` | BAŞARILI | - |
| TC-017 | 3-Policies-PATCH | PATCH /policies/pol_999 olmayan poliçe | `PATCH /policies/pol_999` | u1 | `404` | BAŞARILI | - |
| TC-018 | 3-Policies-PATCH | PATCH /policies/pol_5 geçerli holderName ve agentName güncellemesi | `PATCH /policies/pol_5` | u1 | `200` | BAŞARILI | - |
| TC-019 | 3-Policies-PATCH | PATCH /policies/pol_5 agentName null ve holderName geri alma | `PATCH /policies/pol_5` | u1 | `200` | BAŞARILI | - |
| TC-020 | 3-Policies-PATCH | PATCH /policies/pol_5 salt okunur alanlar (premium, coverageLimit, ownerUserId, policyNumber, coverageType) | `PATCH /policies/pol_5` | u1 | `200` | BAŞARILI | - |
| TC-021 | 3-Policies-PATCH | PATCH /policies/pol_3 u2 iptal poliçe status -> active | `PATCH /policies/pol_3` | u2 | `200` | BAŞARISIZ | BULGU-04 |
| TC-022 | 3-Policies-PATCH | PATCH /policies/pol_3 u2 status geri cancelled yapma | `PATCH /policies/pol_3` | u2 | `200` | BAŞARISIZ | BULGU-04 |
| TC-023 | 3-Policies-PATCH | PATCH /policies/pol_5 u1 enum dışı status -> bogus_status | `PATCH /policies/pol_5` | u1 | `200` | BAŞARISIZ | BULGU-04 |
| TC-024 | 3-Policies-PATCH | PATCH /policies/pol_5 status geri active yapma | `PATCH /policies/pol_5` | u1 | `200` | BAŞARISIZ | BULGU-04 |
| TC-025 | 3-Policies-PATCH | PATCH /policies/pol_2 holderName null | `PATCH /policies/pol_2` | u1 | `200` | BAŞARISIZ | BULGU-13 |
| TC-026 | 3-Policies-PATCH | PATCH /policies/pol_2 holderName sayısal 12345 ve agentName 12345 | `PATCH /policies/pol_2` | u1 | `200` | BAŞARISIZ | BULGU-13 |
| TC-027 | 3-Policies-PATCH | PATCH /policies/pol_2 holderName boş string | `PATCH /policies/pol_2` | u1 | `200` | BAŞARISIZ | BULGU-13 |
| TC-028 | 3-Policies-PATCH | PATCH /policies/pol_2 geri alma | `PATCH /policies/pol_2` | u1 | `200` | BAŞARILI | - |
| TC-029 | 3-Policies-PATCH | PATCH /policies/pol_2 nesne dışı gövde [] | `PATCH /policies/pol_2` | u1 | `200` | BAŞARISIZ | BULGU-13 |
| TC-030 | 3-Policies-PATCH | PATCH /policies/pol_2 nesne dışı gövde 123 | `PATCH /policies/pol_2` | u1 | `200` | BAŞARISIZ | BULGU-13 |
| TC-031 | 3-Policies-PATCH | PATCH /policies/pol_2 bozuk JSON | `PATCH /policies/pol_2` | u1 | `400` | BAŞARISIZ | BULGU-07 |
| TC-032 | 4-Claims-GET | GET /claims token olmadan | `GET /claims` | yok | `401` | BAŞARILI | - |
| TC-033 | 4-Claims-GET | GET /claims u1 kendi talepleri | `GET /claims` | u1 | `200` | BAŞARISIZ | BULGU-09 |
| TC-034 | 4-Claims-GET | GET /claims u2 kendi talepleri | `GET /claims` | u2 | `200` | BAŞARISIZ | BULGU-09 |
| TC-035 | 4-Claims-GET | GET /claims?policyId=pol_3 token olmadan | `GET /claims?policyId=pol_3` | yok | `401` | BAŞARILI | - |
| TC-036 | 4-Claims-GET | GET /claims?policyId=pol_3 u1 başkasının poliçesi (IDOR) | `GET /claims?policyId=pol_3` | u1 | `200` | BAŞARISIZ | BULGU-02 |
| TC-037 | 4-Claims-GET | GET /claims?policyId=pol_1 u2 başkasının poliçesi (IDOR) | `GET /claims?policyId=pol_1` | u2 | `200` | BAŞARISIZ | BULGU-02 |
| TC-038 | 4-Claims-GET | GET /claims?page=1&pageSize=2 u1 meta.total kontrolü | `GET /claims?page=1&pageSize=2` | u1 | `200` | BAŞARISIZ | BULGU-10, BULGU-09 |
| TC-039 | 4-Claims-GET | GET /claims?page=3&pageSize=2 u1 meta.total kontrolü | `GET /claims?page=3&pageSize=2` | u1 | `200` | BAŞARISIZ | BULGU-10, BULGU-09 |
| TC-040 | 4-Claims-GET | GET /claims?page=1&pageSize=3 admin meta.total kontrolü | `GET /claims?page=1&pageSize=3` | admin | `200` | BAŞARISIZ | BULGU-10, BULGU-09 |
| TC-041 | 4-Claims-GET | GET /claims?page=-1&pageSize=2 negatif sayfa | `GET /claims?page=-1&pageSize=2` | u1 | `200` | BAŞARISIZ | BULGU-12 |
| TC-042 | 4-Claims-GET | GET /claims?page=0&pageSize=2 sıfır sayfa | `GET /claims?page=0&pageSize=2` | u1 | `200` | BAŞARISIZ | BULGU-12 |
| TC-043 | 4-Claims-GET | GET /claims?page=abc&pageSize=2 geçersiz page | `GET /claims?page=abc&pageSize=2` | u1 | `200` | BAŞARISIZ | BULGU-12 |
| TC-044 | 4-Claims-GET | GET /claims?page=1&pageSize=abc geçersiz pageSize | `GET /claims?page=1&pageSize=abc` | u1 | `200` | BAŞARISIZ | BULGU-12 |
| TC-045 | 4-Claims-GET | GET /claims?page=1&pageSize=-5 negatif pageSize | `GET /claims?page=1&pageSize=-5` | u1 | `200` | BAŞARISIZ | BULGU-12 |
| TC-046 | 4-Claims-GET | GET /claims?page=1&pageSize=200 üst sınır üstü pageSize | `GET /claims?page=1&pageSize=200` | u1 | `200` | BAŞARISIZ | BULGU-12 |
| TC-047 | 4-Claims-GET | GET /claims/clm_1 u1 kendi talebi | `GET /claims/clm_1` | u1 | `200` | BAŞARISIZ | BULGU-09 |
| TC-048 | 4-Claims-GET | GET /claims/clm_6 u1 başkasının talebi | `GET /claims/clm_6` | u1 | `403` | BAŞARILI | - |
| TC-049 | 4-Claims-GET | GET /claims/clm_999 olmayan talep | `GET /claims/clm_999` | u1 | `404` | BAŞARILI | - |
| TC-050 | 5-Claims-POST | POST /claims token olmadan | `POST /claims` | yok | `401` | BAŞARILI | - |
| TC-051 | 5-Claims-POST | POST /claims u1 başkasının poliçesi pol_4 | `POST /claims` | u1 | `403` | BAŞARILI | - |
| TC-052 | 5-Claims-POST | POST /claims u1 olmayan poliçe pol_999 | `POST /claims` | u1 | `404` | BAŞARILI | - |
| TC-053 | 5-Claims-POST | POST /claims u1 geçerli talep (durum kodu 200 vs 201 ve claimNumber) | `POST /claims` | u1 | `200` | BAŞARISIZ | BULGU-08, BULGU-09 |
| TC-054 | 5-Claims-POST | POST /claims teminat limiti aşımı (pol_1 limit=50000, amount=50001) | `POST /claims` | u1 | `200` | BAŞARISIZ | BULGU-05, BULGU-08, BULGU-09 |
| TC-055 | 5-Claims-POST | POST /claims teminat limiti küsurat aşımı (amount=50000.01) | `POST /claims` | u1 | `200` | BAŞARISIZ | BULGU-05, BULGU-08, BULGU-09 |
| TC-056 | 5-Claims-POST | POST /claims Idempotency-Key ilk istek | `POST /claims` | u1 | `200` | BAŞARISIZ | BULGU-08, BULGU-09 |
| TC-057 | 5-Claims-POST | POST /claims Idempotency-Key tekrar istek (aynı anahtar) | `POST /claims` | u1 | `200` | BAŞARISIZ | BULGU-06, BULGU-08, BULGU-09 |
| TC-058 | 5-Claims-POST | POST /claims amount=0 (minimum 1 ihlali) | `POST /claims` | u1 | `200` | BAŞARISIZ | BULGU-11, BULGU-08, BULGU-09 |
| TC-059 | 5-Claims-POST | POST /claims amount=-100 (negatif tutar) | `POST /claims` | u1 | `200` | BAŞARISIZ | BULGU-11, BULGU-08, BULGU-09 |
| TC-060 | 5-Claims-POST | POST /claims amount=0.5 (1'den küçük) | `POST /claims` | u1 | `200` | BAŞARISIZ | BULGU-11, BULGU-08, BULGU-09 |
| TC-061 | 5-Claims-POST | POST /claims amount=1e309 (Infinity -> null) | `POST /claims` | u1 | `200` | BAŞARISIZ | BULGU-11, BULGU-05, BULGU-08 |
| TC-062 | 5-Claims-POST | POST /claims amount='500' (string tip) | `POST /claims` | u1 | `400` | BAŞARILI | - |
| TC-063 | 5-Claims-POST | POST /claims policyId=null | `POST /claims` | u1 | `404` | BAŞARISIZ | BULGU-11 |
| TC-064 | 5-Claims-POST | POST /claims description=999 (sayı) | `POST /claims` | u1 | `200` | BAŞARISIZ | BULGU-11, BULGU-08 |
| TC-065 | 5-Claims-POST | POST /claims ekstra alanlar (status, ownerUserId, id) | `POST /claims` | u1 | `200` | BAŞARISIZ | BULGU-08, BULGU-09 |
| TC-066 | 5-Claims-POST | POST /claims bozuk JSON | `POST /claims` | u1 | `400` | BAŞARISIZ | BULGU-07 |
| TC-067 | 6-Admin | GET /admin/policies u1 yetkisiz | `GET /admin/policies` | u1 | `403` | BAŞARILI | - |
| TC-068 | 6-Admin | GET /admin/policies admin | `GET /admin/policies` | admin | `200` | BAŞARILI | - |
| TC-069 | 6-Admin | GET /admin/stats token olmadan | `GET /admin/stats` | yok | `401` | BAŞARILI | - |
| TC-070 | 6-Admin | GET /admin/stats u1 normal kullanıcı (Yetki Aşımı!) | `GET /admin/stats` | u1 | `200` | BAŞARISIZ | BULGU-01 |
| TC-071 | 6-Admin | GET /admin/stats u2 normal kullanıcı (Yetki Aşımı!) | `GET /admin/stats` | u2 | `200` | BAŞARISIZ | BULGU-01 |
| TC-072 | 6-Admin | GET /admin/stats admin | `GET /admin/stats` | admin | `200` | BAŞARILI | - |
| TC-073 | 6-Other | DELETE /policies/pol_1 desteklenmeyen yöntem | `DELETE /policies/pol_1` | admin | `405` | BAŞARILI | - |
| TC-074 | 6-Other | GET /unknown olmayan uç | `GET /unknown` | admin | `404` | BAŞARILI | - |
| TC-075 | 7-Crash-DoS | PATCH /policies/pol_2 gövde null (DoS çökme) | `PATCH /policies/pol_2` | u1 | `CONN_ERR` | BAŞARISIZ | BULGU-03 |
| TC-076 | 7-Crash-DoS | GET /health PATCH null sonrası kontrol | `GET /health` | yok | `200` | BAŞARILI | - |
| TC-077 | 7-Crash-DoS | POST /claims gövde null (DoS çökme) | `POST /claims` | u1 | `CONN_ERR` | BAŞARISIZ | BULGU-03 |
| TC-078 | 7-Crash-DoS | GET /health POST null sonrası kontrol | `GET /health` | yok | `200` | BAŞARILI | - |
| TC-079 | 7-Crash-DoS | GET /claims çökme/yeniden başlatma sonrası durum sıfırlanması kontrolü | `GET /claims` | admin | `200` | KANIT | BULGU-03 |

## Ayrıntılı İstek ve Yanıt Kayıtları

### Grup: 1-Auth

#### TC-001 — GET /health kimlik doğrulamasız [BAŞARILI]
- **İstek:** `GET http://localhost:4101/health`
- **Başlıklar:** (yok)
- **HTTP Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{"status":"ok","service":"anadolu-guven-sigorta-api"}
```

#### TC-002 — GET /policies token olmadan [BAŞARILI]
- **İstek:** `GET http://localhost:4101/policies`
- **Başlıklar:** (yok)
- **HTTP Durum Kodu:** `401`
- **Yanıt Gövdesi:**
```json
{"error":"Yetkisiz","message":"Geçerli bir bearer token gerekli."}
```

#### TC-003 — GET /policies geçersiz token [BAŞARILI]
- **İstek:** `GET http://localhost:4101/policies`
- **Başlıklar:** `Authorization: Bearer invalid_token_123`
- **HTTP Durum Kodu:** `401`
- **Yanıt Gövdesi:**
```json
{"error":"Yetkisiz","message":"Geçerli bir bearer token gerekli."}
```

#### TC-004 — GET /policies Basic auth şeması [BAŞARILI]
- **İstek:** `GET http://localhost:4101/policies`
- **Başlıklar:** `Authorization: Basic dTE6cGFzcw==`
- **HTTP Durum Kodu:** `401`
- **Yanıt Gövdesi:**
```json
{"error":"Yetkisiz","message":"Geçerli bir bearer token gerekli."}
```

#### TC-005 — GET /policies boş Bearer [BAŞARILI]
- **İstek:** `GET http://localhost:4101/policies`
- **Başlıklar:** `Authorization: Bearer `
- **HTTP Durum Kodu:** `401`
- **Yanıt Gövdesi:**
```json
{"error":"Yetkisiz","message":"Geçerli bir bearer token gerekli."}
```

#### TC-006 — GET /policies küçük harf bearer [BAŞARILI]
- **İstek:** `GET http://localhost:4101/policies`
- **Başlıklar:** `Authorization: bearer tok_user1_ayse`
- **HTTP Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
[{"id":"pol_1","policyNumber":"POL-2026-0001","ownerUserId":"u1","holderName":"Ayşe Yılmaz","holderTckn":"11111111110","coverageType":"kasko","premium":1500,"coverageLimit":50000,"status":"active","agentName":"Zeynep Kaya","startDate":"2026-01-01","endDate":"2026-12-31"},{"id":"pol_2","policyNumber":"POL-2026-0002","ownerUserId":"u1","holderName":"Ayşe Yılmaz","holderTckn":"11111111110","coverageType":"konut","premium":2400,"coverageLimit":100000,"status":"active","agentName":null,"startDate":"2026-02-15","endDate":"2027-02-14"},{"id":"pol_5","policyNumber":"POL-2026-0005","ownerUserId":"u1","holderName":"Ayşe Yılmaz","holderTckn":"11111111110","coverageType":"trafik","premium":1800,"coverag... (kısaltıldı)
```

### Grup: 2-Policies-GET

#### TC-007 — GET /policies u1 kendi poliçeleri [BAŞARILI]
- **İstek:** `GET http://localhost:4101/policies`
- **Başlıklar:** `Authorization: Bearer tok_user1_ayse`
- **HTTP Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
[{"id":"pol_1","policyNumber":"POL-2026-0001","ownerUserId":"u1","holderName":"Ayşe Yılmaz","holderTckn":"11111111110","coverageType":"kasko","premium":1500,"coverageLimit":50000,"status":"active","agentName":"Zeynep Kaya","startDate":"2026-01-01","endDate":"2026-12-31"},{"id":"pol_2","policyNumber":"POL-2026-0002","ownerUserId":"u1","holderName":"Ayşe Yılmaz","holderTckn":"11111111110","coverageType":"konut","premium":2400,"coverageLimit":100000,"status":"active","agentName":null,"startDate":"2026-02-15","endDate":"2027-02-14"},{"id":"pol_5","policyNumber":"POL-2026-0005","ownerUserId":"u1","holderName":"Ayşe Yılmaz","holderTckn":"11111111110","coverageType":"trafik","premium":1800,"coverag... (kısaltıldı)
```

#### TC-008 — GET /policies u2 kendi poliçeleri [BAŞARILI]
- **İstek:** `GET http://localhost:4101/policies`
- **Başlıklar:** `Authorization: Bearer tok_user2_mehmet`
- **HTTP Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
[{"id":"pol_3","policyNumber":"POL-2026-0003","ownerUserId":"u2","holderName":"Mehmet Demir","holderTckn":"22222222220","coverageType":"saglik","premium":900,"coverageLimit":20000,"status":"cancelled","agentName":"Can Öz","startDate":"2026-01-10","endDate":"2026-07-10"},{"id":"pol_4","policyNumber":"POL-2026-0004","ownerUserId":"u2","holderName":"Mehmet Demir","holderTckn":"22222222220","coverageType":"kasko","premium":3200,"coverageLimit":150000,"status":"active","agentName":"Zeynep Kaya","startDate":"2026-03-01","endDate":"2027-02-28"}]
```

#### TC-009 — GET /policies admin tüm poliçeler [BAŞARILI]
- **İstek:** `GET http://localhost:4101/policies`
- **Başlıklar:** `Authorization: Bearer tok_admin_root`
- **HTTP Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
[{"id":"pol_1","policyNumber":"POL-2026-0001","ownerUserId":"u1","holderName":"Ayşe Yılmaz","holderTckn":"11111111110","coverageType":"kasko","premium":1500,"coverageLimit":50000,"status":"active","agentName":"Zeynep Kaya","startDate":"2026-01-01","endDate":"2026-12-31"},{"id":"pol_2","policyNumber":"POL-2026-0002","ownerUserId":"u1","holderName":"Ayşe Yılmaz","holderTckn":"11111111110","coverageType":"konut","premium":2400,"coverageLimit":100000,"status":"active","agentName":null,"startDate":"2026-02-15","endDate":"2027-02-14"},{"id":"pol_3","policyNumber":"POL-2026-0003","ownerUserId":"u2","holderName":"Mehmet Demir","holderTckn":"22222222220","coverageType":"saglik","premium":900,"coverag... (kısaltıldı)
```

#### TC-010 — GET /policies/pol_1 u1 kendi poliçesi [BAŞARILI]
- **İstek:** `GET http://localhost:4101/policies/pol_1`
- **Başlıklar:** `Authorization: Bearer tok_user1_ayse`
- **HTTP Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{"id":"pol_1","policyNumber":"POL-2026-0001","ownerUserId":"u1","holderName":"Ayşe Yılmaz","holderTckn":"11111111110","coverageType":"kasko","premium":1500,"coverageLimit":50000,"status":"active","agentName":"Zeynep Kaya","startDate":"2026-01-01","endDate":"2026-12-31"}
```

#### TC-011 — GET /policies/pol_3 u1 başkasının poliçesi (IDOR) [BAŞARILI]
- **İstek:** `GET http://localhost:4101/policies/pol_3`
- **Başlıklar:** `Authorization: Bearer tok_user1_ayse`
- **HTTP Durum Kodu:** `403`
- **Yanıt Gövdesi:**
```json
{"error":"Erişim engellendi","message":"Bu poliçeye erişim yetkiniz yok."}
```

#### TC-012 — GET /policies/pol_1 u2 başkasının poliçesi (IDOR) [BAŞARILI]
- **İstek:** `GET http://localhost:4101/policies/pol_1`
- **Başlıklar:** `Authorization: Bearer tok_user2_mehmet`
- **HTTP Durum Kodu:** `403`
- **Yanıt Gövdesi:**
```json
{"error":"Erişim engellendi","message":"Bu poliçeye erişim yetkiniz yok."}
```

#### TC-013 — GET /policies/pol_3 admin erişimi [BAŞARILI]
- **İstek:** `GET http://localhost:4101/policies/pol_3`
- **Başlıklar:** `Authorization: Bearer tok_admin_root`
- **HTTP Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{"id":"pol_3","policyNumber":"POL-2026-0003","ownerUserId":"u2","holderName":"Mehmet Demir","holderTckn":"22222222220","coverageType":"saglik","premium":900,"coverageLimit":20000,"status":"cancelled","agentName":"Can Öz","startDate":"2026-01-10","endDate":"2026-07-10"}
```

#### TC-014 — GET /policies/pol_999 olmayan poliçe [BAŞARILI]
- **İstek:** `GET http://localhost:4101/policies/pol_999`
- **Başlıklar:** `Authorization: Bearer tok_user1_ayse`
- **HTTP Durum Kodu:** `404`
- **Yanıt Gövdesi:**
```json
{"error":"Bulunamadı","message":"Poliçe bulunamadı."}
```

### Grup: 3-Policies-PATCH

#### TC-015 — PATCH /policies/pol_5 token olmadan [BAŞARILI]
- **İstek:** `PATCH http://localhost:4101/policies/pol_5`
- **Başlıklar:** `Content-Type: application/json`
- **İstek Gövdesi:** `{"holderName": "Test"}`
- **HTTP Durum Kodu:** `401`
- **Yanıt Gövdesi:**
```json
{"error":"Yetkisiz","message":"Geçerli bir bearer token gerekli."}
```

#### TC-016 — PATCH /policies/pol_5 u2 başkasının poliçesi [BAŞARILI]
- **İstek:** `PATCH http://localhost:4101/policies/pol_5`
- **Başlıklar:** `Authorization: Bearer tok_user2_mehmet`, `Content-Type: application/json`
- **İstek Gövdesi:** `{"holderName": "Hack"}`
- **HTTP Durum Kodu:** `403`
- **Yanıt Gövdesi:**
```json
{"error":"Erişim engellendi","message":"Bu poliçeye erişim yetkiniz yok."}
```

#### TC-017 — PATCH /policies/pol_999 olmayan poliçe [BAŞARILI]
- **İstek:** `PATCH http://localhost:4101/policies/pol_999`
- **Başlıklar:** `Authorization: Bearer tok_user1_ayse`, `Content-Type: application/json`
- **İstek Gövdesi:** `{"holderName": "Test"}`
- **HTTP Durum Kodu:** `404`
- **Yanıt Gövdesi:**
```json
{"error":"Bulunamadı","message":"Poliçe bulunamadı."}
```

#### TC-018 — PATCH /policies/pol_5 geçerli holderName ve agentName güncellemesi [BAŞARILI]
- **İstek:** `PATCH http://localhost:4101/policies/pol_5`
- **Başlıklar:** `Authorization: Bearer tok_user1_ayse`, `Content-Type: application/json`
- **İstek Gövdesi:** `{"holderName": "Ayşe Yılmaz QA", "agentName": "Ali Veli"}`
- **HTTP Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{"id":"pol_5","policyNumber":"POL-2026-0005","ownerUserId":"u1","holderName":"Ayşe Yılmaz QA","holderTckn":"11111111110","coverageType":"trafik","premium":1800,"coverageLimit":75000,"status":"active","agentName":"Ali Veli","startDate":"2026-04-01","endDate":"2027-03-31"}
```

#### TC-019 — PATCH /policies/pol_5 agentName null ve holderName geri alma [BAŞARILI]
- **İstek:** `PATCH http://localhost:4101/policies/pol_5`
- **Başlıklar:** `Authorization: Bearer tok_user1_ayse`, `Content-Type: application/json`
- **İstek Gövdesi:** `{"holderName": "Ayşe Yılmaz", "agentName": null}`
- **HTTP Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{"id":"pol_5","policyNumber":"POL-2026-0005","ownerUserId":"u1","holderName":"Ayşe Yılmaz","holderTckn":"11111111110","coverageType":"trafik","premium":1800,"coverageLimit":75000,"status":"active","agentName":null,"startDate":"2026-04-01","endDate":"2027-03-31"}
```

#### TC-020 — PATCH /policies/pol_5 salt okunur alanlar (premium, coverageLimit, ownerUserId, policyNumber, coverageType) [BAŞARILI]
- **İstek:** `PATCH http://localhost:4101/policies/pol_5`
- **Başlıklar:** `Authorization: Bearer tok_user1_ayse`, `Content-Type: application/json`
- **İstek Gövdesi:** `{"premium": 1, "coverageLimit": 999999, "ownerUserId": "u2", "policyNumber": "POL-HACK", "coverageType": "saglik"}`
- **HTTP Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{"id":"pol_5","policyNumber":"POL-2026-0005","ownerUserId":"u1","holderName":"Ayşe Yılmaz","holderTckn":"11111111110","coverageType":"trafik","premium":1800,"coverageLimit":75000,"status":"active","agentName":null,"startDate":"2026-04-01","endDate":"2027-03-31"}
```

#### TC-021 — PATCH /policies/pol_3 u2 iptal poliçe status -> active [BAŞARISIZ]
- **İstek:** `PATCH http://localhost:4101/policies/pol_3`
- **Başlıklar:** `Authorization: Bearer tok_user2_mehmet`, `Content-Type: application/json`
- **İstek Gövdesi:** `{"status": "active"}`
- **Beklenen:** 400 veya status değişmemeli
- **Gözlenen Özet:** 200; pol_3 status 'active' oldu (İlgili: **BULGU-04**)
- **HTTP Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{"id":"pol_3","policyNumber":"POL-2026-0003","ownerUserId":"u2","holderName":"Mehmet Demir","holderTckn":"22222222220","coverageType":"saglik","premium":900,"coverageLimit":20000,"status":"active","agentName":"Can Öz","startDate":"2026-01-10","endDate":"2026-07-10"}
```

#### TC-022 — PATCH /policies/pol_3 u2 status geri cancelled yapma [BAŞARISIZ]
- **İstek:** `PATCH http://localhost:4101/policies/pol_3`
- **Başlıklar:** `Authorization: Bearer tok_user2_mehmet`, `Content-Type: application/json`
- **İstek Gövdesi:** `{"status": "cancelled"}`
- **Beklenen:** status değişmemeli
- **Gözlenen Özet:** 200; pol_3 status 'cancelled' geri alındı (İlgili: **BULGU-04**)
- **HTTP Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{"id":"pol_3","policyNumber":"POL-2026-0003","ownerUserId":"u2","holderName":"Mehmet Demir","holderTckn":"22222222220","coverageType":"saglik","premium":900,"coverageLimit":20000,"status":"cancelled","agentName":"Can Öz","startDate":"2026-01-10","endDate":"2026-07-10"}
```

#### TC-023 — PATCH /policies/pol_5 u1 enum dışı status -> bogus_status [BAŞARISIZ]
- **İstek:** `PATCH http://localhost:4101/policies/pol_5`
- **Başlıklar:** `Authorization: Bearer tok_user1_ayse`, `Content-Type: application/json`
- **İstek Gövdesi:** `{"status": "bogus_status"}`
- **Beklenen:** status yok sayılmalı / enum dışı reddedilmeli
- **Gözlenen Özet:** 200; status 'bogus_status' oldu (İlgili: **BULGU-04**)
- **HTTP Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{"id":"pol_5","policyNumber":"POL-2026-0005","ownerUserId":"u1","holderName":"Ayşe Yılmaz","holderTckn":"11111111110","coverageType":"trafik","premium":1800,"coverageLimit":75000,"status":"bogus_status","agentName":null,"startDate":"2026-04-01","endDate":"2027-03-31"}
```

#### TC-024 — PATCH /policies/pol_5 status geri active yapma [BAŞARISIZ]
- **İstek:** `PATCH http://localhost:4101/policies/pol_5`
- **Başlıklar:** `Authorization: Bearer tok_user1_ayse`, `Content-Type: application/json`
- **İstek Gövdesi:** `{"status": "active"}`
- **Beklenen:** status değişmemeli
- **Gözlenen Özet:** 200; pol_5 status 'active' geri alındı (İlgili: **BULGU-04**)
- **HTTP Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{"id":"pol_5","policyNumber":"POL-2026-0005","ownerUserId":"u1","holderName":"Ayşe Yılmaz","holderTckn":"11111111110","coverageType":"trafik","premium":1800,"coverageLimit":75000,"status":"active","agentName":null,"startDate":"2026-04-01","endDate":"2027-03-31"}
```

#### TC-025 — PATCH /policies/pol_2 holderName null [BAŞARISIZ]
- **İstek:** `PATCH http://localhost:4101/policies/pol_2`
- **Başlıklar:** `Authorization: Bearer tok_user1_ayse`, `Content-Type: application/json`
- **İstek Gövdesi:** `{"holderName": null}`
- **Beklenen:** 400 (holderName string olmalı)
- **Gözlenen Özet:** 200; holderName null kaydedildi (İlgili: **BULGU-13**)
- **HTTP Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{"id":"pol_2","policyNumber":"POL-2026-0002","ownerUserId":"u1","holderName":null,"holderTckn":"11111111110","coverageType":"konut","premium":2400,"coverageLimit":100000,"status":"active","agentName":null,"startDate":"2026-02-15","endDate":"2027-02-14"}
```

#### TC-026 — PATCH /policies/pol_2 holderName sayısal 12345 ve agentName 12345 [BAŞARISIZ]
- **İstek:** `PATCH http://localhost:4101/policies/pol_2`
- **Başlıklar:** `Authorization: Bearer tok_user1_ayse`, `Content-Type: application/json`
- **İstek Gövdesi:** `{"holderName": 12345, "agentName": 12345}`
- **Beklenen:** 400 (string tip doğrulaması)
- **Gözlenen Özet:** 200; holderName=12345, agentName=12345 (İlgili: **BULGU-13**)
- **HTTP Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{"id":"pol_2","policyNumber":"POL-2026-0002","ownerUserId":"u1","holderName":12345,"holderTckn":"11111111110","coverageType":"konut","premium":2400,"coverageLimit":100000,"status":"active","agentName":12345,"startDate":"2026-02-15","endDate":"2027-02-14"}
```

#### TC-027 — PATCH /policies/pol_2 holderName boş string [BAŞARISIZ]
- **İstek:** `PATCH http://localhost:4101/policies/pol_2`
- **Başlıklar:** `Authorization: Bearer tok_user1_ayse`, `Content-Type: application/json`
- **İstek Gövdesi:** `{"holderName": "", "agentName": null}`
- **Beklenen:** 400 (boş holderName reddedilmeli)
- **Gözlenen Özet:** 200; holderName='' kaydedildi (İlgili: **BULGU-13**)
- **HTTP Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{"id":"pol_2","policyNumber":"POL-2026-0002","ownerUserId":"u1","holderName":"","holderTckn":"11111111110","coverageType":"konut","premium":2400,"coverageLimit":100000,"status":"active","agentName":null,"startDate":"2026-02-15","endDate":"2027-02-14"}
```

#### TC-028 — PATCH /policies/pol_2 geri alma [BAŞARILI]
- **İstek:** `PATCH http://localhost:4101/policies/pol_2`
- **Başlıklar:** `Authorization: Bearer tok_user1_ayse`, `Content-Type: application/json`
- **İstek Gövdesi:** `{"holderName": "Ayşe Yılmaz", "agentName": null}`
- **HTTP Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{"id":"pol_2","policyNumber":"POL-2026-0002","ownerUserId":"u1","holderName":"Ayşe Yılmaz","holderTckn":"11111111110","coverageType":"konut","premium":2400,"coverageLimit":100000,"status":"active","agentName":null,"startDate":"2026-02-15","endDate":"2027-02-14"}
```

#### TC-029 — PATCH /policies/pol_2 nesne dışı gövde [] [BAŞARISIZ]
- **İstek:** `PATCH http://localhost:4101/policies/pol_2`
- **Başlıklar:** `Content-Type: application/json`, `Authorization: Bearer tok_user1_ayse`
- **İstek Gövdesi:** `[]`
- **Beklenen:** 400 (PolicyUpdate object olmalı)
- **Gözlenen Özet:** 200 döndü (İlgili: **BULGU-13**)
- **HTTP Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{"id":"pol_2","policyNumber":"POL-2026-0002","ownerUserId":"u1","holderName":"Ayşe Yılmaz","holderTckn":"11111111110","coverageType":"konut","premium":2400,"coverageLimit":100000,"status":"active","agentName":null,"startDate":"2026-02-15","endDate":"2027-02-14"}
```

#### TC-030 — PATCH /policies/pol_2 nesne dışı gövde 123 [BAŞARISIZ]
- **İstek:** `PATCH http://localhost:4101/policies/pol_2`
- **Başlıklar:** `Content-Type: application/json`, `Authorization: Bearer tok_user1_ayse`
- **İstek Gövdesi:** `123`
- **Beklenen:** 400 (PolicyUpdate object olmalı)
- **Gözlenen Özet:** 200 döndü (İlgili: **BULGU-13**)
- **HTTP Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{"id":"pol_2","policyNumber":"POL-2026-0002","ownerUserId":"u1","holderName":"Ayşe Yılmaz","holderTckn":"11111111110","coverageType":"konut","premium":2400,"coverageLimit":100000,"status":"active","agentName":null,"startDate":"2026-02-15","endDate":"2027-02-14"}
```

#### TC-031 — PATCH /policies/pol_2 bozuk JSON [BAŞARISIZ]
- **İstek:** `PATCH http://localhost:4101/policies/pol_2`
- **Başlıklar:** `Content-Type: application/json`, `Authorization: Bearer tok_user1_ayse`
- **İstek Gövdesi:** `{"holderName": `
- **Beklenen:** 400 güvenli Error şeması (stack yok)
- **Gözlenen Özet:** 400; 'detail' ve 'stack' (dosya yolu) sızdı (İlgili: **BULGU-07**)
- **HTTP Durum Kodu:** `400`
- **Yanıt Gövdesi:**
```json
{"error":"Geçersiz JSON","detail":"Unexpected end of JSON input","stack":"SyntaxError: Unexpected end of JSON input\n    at JSON.parse (<anonymous>)\n    at Server.<anonymous> (C:\\eval\\servers\\R01\\server.js:155:27)\n    at process.processTicksAndRejections (node:internal/process/task_queues:104:5)"}
```

### Grup: 4-Claims-GET

#### TC-032 — GET /claims token olmadan [BAŞARILI]
- **İstek:** `GET http://localhost:4101/claims`
- **Başlıklar:** (yok)
- **HTTP Durum Kodu:** `401`
- **Yanıt Gövdesi:**
```json
{"error":"Yetkisiz","message":"Geçerli bir bearer token gerekli."}
```

#### TC-033 — GET /claims u1 kendi talepleri [BAŞARISIZ]
- **İstek:** `GET http://localhost:4101/claims`
- **Başlıklar:** `Authorization: Bearer tok_user1_ayse`
- **Beklenen:** 200 ve Claim.claimNumber zorunlu alanı mevcut
- **Gözlenen Özet:** 200 ama 'claimNumber' alanı eksik (İlgili: **BULGU-09**)
- **HTTP Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{"data":[{"id":"clm_1","policyId":"pol_1","ownerUserId":"u1","amount":12000,"status":"submitted","description":"Çarpma hasarı","createdAt":"2026-05-02T09:00:00Z"},{"id":"clm_2","policyId":"pol_1","ownerUserId":"u1","amount":8000,"status":"rejected","description":"Cam kırığı","createdAt":"2026-05-10T11:30:00Z"},{"id":"clm_3","policyId":"pol_2","ownerUserId":"u1","amount":3000,"status":"approved","description":"Su baskını","createdAt":"2026-06-01T08:15:00Z"},{"id":"clm_4","policyId":"pol_5","ownerUserId":"u1","amount":15000,"status":"submitted","description":"Trafik kazası","createdAt":"2026-06-20T14:45:00Z"},{"id":"clm_5","policyId":"pol_2","ownerUserId":"u1","amount":2000,"status":"submitted... (kısaltıldı)
```

#### TC-034 — GET /claims u2 kendi talepleri [BAŞARISIZ]
- **İstek:** `GET http://localhost:4101/claims`
- **Başlıklar:** `Authorization: Bearer tok_user2_mehmet`
- **Beklenen:** 200 ve Claim.claimNumber zorunlu alanı mevcut
- **Gözlenen Özet:** 200 ama 'claimNumber' alanı eksik (İlgili: **BULGU-09**)
- **HTTP Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{"data":[{"id":"clm_6","policyId":"pol_4","ownerUserId":"u2","amount":5000,"status":"approved","description":"Çarpma hasarı","createdAt":"2026-05-18T10:20:00Z"},{"id":"clm_7","policyId":"pol_3","ownerUserId":"u2","amount":1000,"status":"rejected","description":"Muayene masrafı","createdAt":"2026-06-11T13:00:00Z"}],"meta":{"page":1,"pageSize":20,"total":2}}
```

#### TC-035 — GET /claims?policyId=pol_3 token olmadan [BAŞARILI]
- **İstek:** `GET http://localhost:4101/claims?policyId=pol_3`
- **Başlıklar:** (yok)
- **HTTP Durum Kodu:** `401`
- **Yanıt Gövdesi:**
```json
{"error":"Yetkisiz","message":"Geçerli bir bearer token gerekli."}
```

#### TC-036 — GET /claims?policyId=pol_3 u1 başkasının poliçesi (IDOR) [BAŞARISIZ]
- **İstek:** `GET http://localhost:4101/claims?policyId=pol_3`
- **Başlıklar:** `Authorization: Bearer tok_user1_ayse`
- **Beklenen:** 403 veya boş liste (yalnızca kendi talepleri)
- **Gözlenen Özet:** 200; u2'nin clm_7 talebi sızdırıldı (İlgili: **BULGU-02**)
- **HTTP Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{"data":[{"id":"clm_7","policyId":"pol_3","ownerUserId":"u2","amount":1000,"status":"rejected","description":"Muayene masrafı","createdAt":"2026-06-11T13:00:00Z"}],"meta":{"page":1,"pageSize":20,"total":1}}
```

#### TC-037 — GET /claims?policyId=pol_1 u2 başkasının poliçesi (IDOR) [BAŞARISIZ]
- **İstek:** `GET http://localhost:4101/claims?policyId=pol_1`
- **Başlıklar:** `Authorization: Bearer tok_user2_mehmet`
- **Beklenen:** 403 veya boş liste (yalnızca kendi talepleri)
- **Gözlenen Özet:** 200; u1'in clm_1, clm_2, clm_8 talepleri sızdırıldı (İlgili: **BULGU-02**)
- **HTTP Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{"data":[{"id":"clm_1","policyId":"pol_1","ownerUserId":"u1","amount":12000,"status":"submitted","description":"Çarpma hasarı","createdAt":"2026-05-02T09:00:00Z"},{"id":"clm_2","policyId":"pol_1","ownerUserId":"u1","amount":8000,"status":"rejected","description":"Cam kırığı","createdAt":"2026-05-10T11:30:00Z"},{"id":"clm_8","policyId":"pol_1","ownerUserId":"u1","amount":100,"status":"submitted","description":"utf8 test şıö","createdAt":"2026-08-01T00:00:00Z"}],"meta":{"page":1,"pageSize":20,"total":3}}
```

#### TC-038 — GET /claims?page=1&pageSize=2 u1 meta.total kontrolü [BAŞARISIZ]
- **İstek:** `GET http://localhost:4101/claims?page=1&pageSize=2`
- **Başlıklar:** `Authorization: Bearer tok_user1_ayse`
- **Beklenen:** meta.total=6 ve claimNumber mevcut
- **Gözlenen Özet:** meta.total=2 döndü; claimNumber eksik (İlgili: **BULGU-10, BULGU-09**)
- **HTTP Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{"data":[{"id":"clm_1","policyId":"pol_1","ownerUserId":"u1","amount":12000,"status":"submitted","description":"Çarpma hasarı","createdAt":"2026-05-02T09:00:00Z"},{"id":"clm_2","policyId":"pol_1","ownerUserId":"u1","amount":8000,"status":"rejected","description":"Cam kırığı","createdAt":"2026-05-10T11:30:00Z"}],"meta":{"page":1,"pageSize":2,"total":2}}
```

#### TC-039 — GET /claims?page=3&pageSize=2 u1 meta.total kontrolü [BAŞARISIZ]
- **İstek:** `GET http://localhost:4101/claims?page=3&pageSize=2`
- **Başlıklar:** `Authorization: Bearer tok_user1_ayse`
- **Beklenen:** meta.total=6
- **Gözlenen Özet:** meta.total=2 döndü (İlgili: **BULGU-10, BULGU-09**)
- **HTTP Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{"data":[{"id":"clm_5","policyId":"pol_2","ownerUserId":"u1","amount":2000,"status":"submitted","description":"Hırsızlık","createdAt":"2026-07-03T16:05:00Z"},{"id":"clm_8","policyId":"pol_1","ownerUserId":"u1","amount":100,"status":"submitted","description":"utf8 test şıö","createdAt":"2026-08-01T00:00:00Z"}],"meta":{"page":3,"pageSize":2,"total":2}}
```

#### TC-040 — GET /claims?page=1&pageSize=3 admin meta.total kontrolü [BAŞARISIZ]
- **İstek:** `GET http://localhost:4101/claims?page=1&pageSize=3`
- **Başlıklar:** `Authorization: Bearer tok_admin_root`
- **Beklenen:** meta.total=8
- **Gözlenen Özet:** meta.total=3 döndü (İlgili: **BULGU-10, BULGU-09**)
- **HTTP Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{"data":[{"id":"clm_1","policyId":"pol_1","ownerUserId":"u1","amount":12000,"status":"submitted","description":"Çarpma hasarı","createdAt":"2026-05-02T09:00:00Z"},{"id":"clm_2","policyId":"pol_1","ownerUserId":"u1","amount":8000,"status":"rejected","description":"Cam kırığı","createdAt":"2026-05-10T11:30:00Z"},{"id":"clm_3","policyId":"pol_2","ownerUserId":"u1","amount":3000,"status":"approved","description":"Su baskını","createdAt":"2026-06-01T08:15:00Z"}],"meta":{"page":1,"pageSize":3,"total":3}}
```

#### TC-041 — GET /claims?page=-1&pageSize=2 negatif sayfa [BAŞARISIZ]
- **İstek:** `GET http://localhost:4101/claims?page=-1&pageSize=2`
- **Başlıklar:** `Authorization: Bearer tok_user1_ayse`
- **Beklenen:** 400 (page >= 1)
- **Gözlenen Özet:** 200; negatif dilimleme ile clm_3, clm_4 ve meta.page=-1 (İlgili: **BULGU-12**)
- **HTTP Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{"data":[{"id":"clm_3","policyId":"pol_2","ownerUserId":"u1","amount":3000,"status":"approved","description":"Su baskını","createdAt":"2026-06-01T08:15:00Z"},{"id":"clm_4","policyId":"pol_5","ownerUserId":"u1","amount":15000,"status":"submitted","description":"Trafik kazası","createdAt":"2026-06-20T14:45:00Z"}],"meta":{"page":-1,"pageSize":2,"total":2}}
```

#### TC-042 — GET /claims?page=0&pageSize=2 sıfır sayfa [BAŞARISIZ]
- **İstek:** `GET http://localhost:4101/claims?page=0&pageSize=2`
- **Başlıklar:** `Authorization: Bearer tok_user1_ayse`
- **Beklenen:** 400 (page >= 1)
- **Gözlenen Özet:** 200; meta.page=0, data=[] (İlgili: **BULGU-12**)
- **HTTP Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{"data":[],"meta":{"page":0,"pageSize":2,"total":0}}
```

#### TC-043 — GET /claims?page=abc&pageSize=2 geçersiz page [BAŞARISIZ]
- **İstek:** `GET http://localhost:4101/claims?page=abc&pageSize=2`
- **Başlıklar:** `Authorization: Bearer tok_user1_ayse`
- **Beklenen:** 400 (page integer)
- **Gözlenen Özet:** 200; meta.page=null (şema ihlali) (İlgili: **BULGU-12**)
- **HTTP Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{"data":[],"meta":{"page":null,"pageSize":2,"total":0}}
```

#### TC-044 — GET /claims?page=1&pageSize=abc geçersiz pageSize [BAŞARISIZ]
- **İstek:** `GET http://localhost:4101/claims?page=1&pageSize=abc`
- **Başlıklar:** `Authorization: Bearer tok_user1_ayse`
- **Beklenen:** 400 (pageSize integer)
- **Gözlenen Özet:** 200; meta.pageSize=null (şema ihlali) (İlgili: **BULGU-12**)
- **HTTP Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{"data":[],"meta":{"page":1,"pageSize":null,"total":0}}
```

#### TC-045 — GET /claims?page=1&pageSize=-5 negatif pageSize [BAŞARISIZ]
- **İstek:** `GET http://localhost:4101/claims?page=1&pageSize=-5`
- **Başlıklar:** `Authorization: Bearer tok_user1_ayse`
- **Beklenen:** 400 (pageSize >= 1)
- **Gözlenen Özet:** 200; meta.pageSize=-5 ve clm_1 döndü (İlgili: **BULGU-12**)
- **HTTP Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{"data":[{"id":"clm_1","policyId":"pol_1","ownerUserId":"u1","amount":12000,"status":"submitted","description":"Çarpma hasarı","createdAt":"2026-05-02T09:00:00Z"}],"meta":{"page":1,"pageSize":-5,"total":1}}
```

#### TC-046 — GET /claims?page=1&pageSize=200 üst sınır üstü pageSize [BAŞARISIZ]
- **İstek:** `GET http://localhost:4101/claims?page=1&pageSize=200`
- **Başlıklar:** `Authorization: Bearer tok_user1_ayse`
- **Beklenen:** 400 (pageSize <= 100)
- **Gözlenen Özet:** 200; pageSize=200 kabul edildi (İlgili: **BULGU-12**)
- **HTTP Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{"data":[{"id":"clm_1","policyId":"pol_1","ownerUserId":"u1","amount":12000,"status":"submitted","description":"Çarpma hasarı","createdAt":"2026-05-02T09:00:00Z"},{"id":"clm_2","policyId":"pol_1","ownerUserId":"u1","amount":8000,"status":"rejected","description":"Cam kırığı","createdAt":"2026-05-10T11:30:00Z"},{"id":"clm_3","policyId":"pol_2","ownerUserId":"u1","amount":3000,"status":"approved","description":"Su baskını","createdAt":"2026-06-01T08:15:00Z"},{"id":"clm_4","policyId":"pol_5","ownerUserId":"u1","amount":15000,"status":"submitted","description":"Trafik kazası","createdAt":"2026-06-20T14:45:00Z"},{"id":"clm_5","policyId":"pol_2","ownerUserId":"u1","amount":2000,"status":"submitted... (kısaltıldı)
```

#### TC-047 — GET /claims/clm_1 u1 kendi talebi [BAŞARISIZ]
- **İstek:** `GET http://localhost:4101/claims/clm_1`
- **Başlıklar:** `Authorization: Bearer tok_user1_ayse`
- **Beklenen:** 200 ve claimNumber mevcut
- **Gözlenen Özet:** 200 ama 'claimNumber' eksik (İlgili: **BULGU-09**)
- **HTTP Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{"id":"clm_1","policyId":"pol_1","ownerUserId":"u1","amount":12000,"status":"submitted","description":"Çarpma hasarı","createdAt":"2026-05-02T09:00:00Z"}
```

#### TC-048 — GET /claims/clm_6 u1 başkasının talebi [BAŞARILI]
- **İstek:** `GET http://localhost:4101/claims/clm_6`
- **Başlıklar:** `Authorization: Bearer tok_user1_ayse`
- **HTTP Durum Kodu:** `403`
- **Yanıt Gövdesi:**
```json
{"error":"Erişim engellendi","message":"Bu hasar talebine erişim yetkiniz yok."}
```

#### TC-049 — GET /claims/clm_999 olmayan talep [BAŞARILI]
- **İstek:** `GET http://localhost:4101/claims/clm_999`
- **Başlıklar:** `Authorization: Bearer tok_user1_ayse`
- **HTTP Durum Kodu:** `404`
- **Yanıt Gövdesi:**
```json
{"error":"Bulunamadı","message":"Hasar talebi bulunamadı."}
```

### Grup: 5-Claims-POST

#### TC-050 — POST /claims token olmadan [BAŞARILI]
- **İstek:** `POST http://localhost:4101/claims`
- **Başlıklar:** `Content-Type: application/json`
- **İstek Gövdesi:** `{"policyId": "pol_1", "amount": 100}`
- **HTTP Durum Kodu:** `401`
- **Yanıt Gövdesi:**
```json
{"error":"Yetkisiz","message":"Geçerli bir bearer token gerekli."}
```

#### TC-051 — POST /claims u1 başkasının poliçesi pol_4 [BAŞARILI]
- **İstek:** `POST http://localhost:4101/claims`
- **Başlıklar:** `Authorization: Bearer tok_user1_ayse`, `Content-Type: application/json`
- **İstek Gövdesi:** `{"policyId": "pol_4", "amount": 100}`
- **HTTP Durum Kodu:** `403`
- **Yanıt Gövdesi:**
```json
{"error":"Erişim engellendi","message":"Bu poliçe için hasar talebi oluşturamazsınız."}
```

#### TC-052 — POST /claims u1 olmayan poliçe pol_999 [BAŞARILI]
- **İstek:** `POST http://localhost:4101/claims`
- **Başlıklar:** `Authorization: Bearer tok_user1_ayse`, `Content-Type: application/json`
- **İstek Gövdesi:** `{"policyId": "pol_999", "amount": 100}`
- **HTTP Durum Kodu:** `404`
- **Yanıt Gövdesi:**
```json
{"error":"Bulunamadı","message":"Poliçe bulunamadı."}
```

#### TC-053 — POST /claims u1 geçerli talep (durum kodu 200 vs 201 ve claimNumber) [BAŞARISIZ]
- **İstek:** `POST http://localhost:4101/claims`
- **Başlıklar:** `Authorization: Bearer tok_user1_ayse`, `Content-Type: application/json`
- **İstek Gövdesi:** `{"policyId": "pol_1", "amount": 1500, "description": "QA geçerli talep"}`
- **Beklenen:** 201 Created ve claimNumber mevcut
- **Gözlenen Özet:** 200 OK döndü; 'claimNumber' eksik (İlgili: **BULGU-08, BULGU-09**)
- **HTTP Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{"id":"clm_9","policyId":"pol_1","ownerUserId":"u1","amount":1500,"status":"submitted","description":"QA geçerli talep","createdAt":"2026-08-01T00:00:00Z"}
```

#### TC-054 — POST /claims teminat limiti aşımı (pol_1 limit=50000, amount=50001) [BAŞARISIZ]
- **İstek:** `POST http://localhost:4101/claims`
- **Başlıklar:** `Authorization: Bearer tok_user1_ayse`, `Content-Type: application/json`
- **İstek Gövdesi:** `{"policyId": "pol_1", "amount": 50001, "description": "Limit aşımı"}`
- **Beklenen:** 422 (tutar teminat limitini aşıyor)
- **Gözlenen Özet:** 200 OK; clm_10 (50001 TL) oluşturuldu (İlgili: **BULGU-05, BULGU-08, BULGU-09**)
- **HTTP Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{"id":"clm_10","policyId":"pol_1","ownerUserId":"u1","amount":50001,"status":"submitted","description":"Limit aşımı","createdAt":"2026-08-01T00:00:00Z"}
```

#### TC-055 — POST /claims teminat limiti küsurat aşımı (amount=50000.01) [BAŞARISIZ]
- **İstek:** `POST http://localhost:4101/claims`
- **Başlıklar:** `Authorization: Bearer tok_user1_ayse`, `Content-Type: application/json`
- **İstek Gövdesi:** `{"policyId": "pol_1", "amount": 50000.01, "description": "Küsurat aşımı"}`
- **Beklenen:** 422 (tutar teminat limitini aşıyor)
- **Gözlenen Özet:** 200 OK; clm_11 (50000.01 TL) oluşturuldu (İlgili: **BULGU-05, BULGU-08, BULGU-09**)
- **HTTP Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{"id":"clm_11","policyId":"pol_1","ownerUserId":"u1","amount":50000.01,"status":"submitted","description":"Küsurat aşımı","createdAt":"2026-08-01T00:00:00Z"}
```

#### TC-056 — POST /claims Idempotency-Key ilk istek [BAŞARISIZ]
- **İstek:** `POST http://localhost:4101/claims`
- **Başlıklar:** `Idempotency-Key: qa-idem-001`, `Authorization: Bearer tok_user1_ayse`, `Content-Type: application/json`
- **İstek Gövdesi:** `{"policyId": "pol_5", "amount": 2500, "description": "Idem test"}`
- **Beklenen:** 201 Created ve claimNumber mevcut
- **Gözlenen Özet:** 200 OK (clm_12); 'claimNumber' eksik (İlgili: **BULGU-08, BULGU-09**)
- **HTTP Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{"id":"clm_12","policyId":"pol_5","ownerUserId":"u1","amount":2500,"status":"submitted","description":"Idem test","createdAt":"2026-08-01T00:00:00Z"}
```

#### TC-057 — POST /claims Idempotency-Key tekrar istek (aynı anahtar) [BAŞARISIZ]
- **İstek:** `POST http://localhost:4101/claims`
- **Başlıklar:** `Idempotency-Key: qa-idem-001`, `Authorization: Bearer tok_user1_ayse`, `Content-Type: application/json`
- **İstek Gövdesi:** `{"policyId": "pol_5", "amount": 2500, "description": "Idem test"}`
- **Beklenen:** İlk kaydı (clm_12) döndürmeli, yeni kayıt açmamalı
- **Gözlenen Özet:** 200 OK; yeni kayıt clm_13 oluşturuldu (İlgili: **BULGU-06, BULGU-08, BULGU-09**)
- **HTTP Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{"id":"clm_13","policyId":"pol_5","ownerUserId":"u1","amount":2500,"status":"submitted","description":"Idem test","createdAt":"2026-08-01T00:00:00Z"}
```

#### TC-058 — POST /claims amount=0 (minimum 1 ihlali) [BAŞARISIZ]
- **İstek:** `POST http://localhost:4101/claims`
- **Başlıklar:** `Authorization: Bearer tok_user1_ayse`, `Content-Type: application/json`
- **İstek Gövdesi:** `{"policyId": "pol_5", "amount": 0}`
- **Beklenen:** 400 (amount >= 1)
- **Gözlenen Özet:** 200 OK; amount=0 (clm_14) oluşturuldu (İlgili: **BULGU-11, BULGU-08, BULGU-09**)
- **HTTP Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{"id":"clm_14","policyId":"pol_5","ownerUserId":"u1","amount":0,"status":"submitted","description":"","createdAt":"2026-08-01T00:00:00Z"}
```

#### TC-059 — POST /claims amount=-100 (negatif tutar) [BAŞARISIZ]
- **İstek:** `POST http://localhost:4101/claims`
- **Başlıklar:** `Authorization: Bearer tok_user1_ayse`, `Content-Type: application/json`
- **İstek Gövdesi:** `{"policyId": "pol_5", "amount": -100}`
- **Beklenen:** 400 (amount >= 1)
- **Gözlenen Özet:** 200 OK; amount=-100 (clm_15) oluşturuldu (İlgili: **BULGU-11, BULGU-08, BULGU-09**)
- **HTTP Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{"id":"clm_15","policyId":"pol_5","ownerUserId":"u1","amount":-100,"status":"submitted","description":"","createdAt":"2026-08-01T00:00:00Z"}
```

#### TC-060 — POST /claims amount=0.5 (1'den küçük) [BAŞARISIZ]
- **İstek:** `POST http://localhost:4101/claims`
- **Başlıklar:** `Authorization: Bearer tok_user1_ayse`, `Content-Type: application/json`
- **İstek Gövdesi:** `{"policyId": "pol_5", "amount": 0.5}`
- **Beklenen:** 400 (amount >= 1)
- **Gözlenen Özet:** 200 OK; amount=0.5 (clm_16) oluşturuldu (İlgili: **BULGU-11, BULGU-08, BULGU-09**)
- **HTTP Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{"id":"clm_16","policyId":"pol_5","ownerUserId":"u1","amount":0.5,"status":"submitted","description":"","createdAt":"2026-08-01T00:00:00Z"}
```

#### TC-061 — POST /claims amount=1e309 (Infinity -> null) [BAŞARISIZ]
- **İstek:** `POST http://localhost:4101/claims`
- **Başlıklar:** `Content-Type: application/json`, `Authorization: Bearer tok_user1_ayse`
- **İstek Gövdesi:** `{"policyId":"pol_5","amount":1e309}`
- **Beklenen:** 400/422 (geçersiz/taşan sayı)
- **Gözlenen Özet:** 200 OK; amount=null (clm_17) kaydedildi (İlgili: **BULGU-11, BULGU-05, BULGU-08**)
- **HTTP Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{"id":"clm_17","policyId":"pol_5","ownerUserId":"u1","amount":null,"status":"submitted","description":"","createdAt":"2026-08-01T00:00:00Z"}
```

#### TC-062 — POST /claims amount='500' (string tip) [BAŞARILI]
- **İstek:** `POST http://localhost:4101/claims`
- **Başlıklar:** `Authorization: Bearer tok_user1_ayse`, `Content-Type: application/json`
- **İstek Gövdesi:** `{"policyId": "pol_5", "amount": "500"}`
- **HTTP Durum Kodu:** `400`
- **Yanıt Gövdesi:**
```json
{"error":"Geçersiz tip","message":"amount sayısal olmalıdır."}
```

#### TC-063 — POST /claims policyId=null [BAŞARISIZ]
- **İstek:** `POST http://localhost:4101/claims`
- **Başlıklar:** `Authorization: Bearer tok_user1_ayse`, `Content-Type: application/json`
- **İstek Gövdesi:** `{"policyId": null, "amount": 100}`
- **Beklenen:** 400 (policyId string olmalı)
- **Gözlenen Özet:** 404 Poliçe bulunamadı döndü (İlgili: **BULGU-11**)
- **HTTP Durum Kodu:** `404`
- **Yanıt Gövdesi:**
```json
{"error":"Bulunamadı","message":"Poliçe bulunamadı."}
```

#### TC-064 — POST /claims description=999 (sayı) [BAŞARISIZ]
- **İstek:** `POST http://localhost:4101/claims`
- **Başlıklar:** `Authorization: Bearer tok_user1_ayse`, `Content-Type: application/json`
- **İstek Gövdesi:** `{"policyId": "pol_5", "amount": 100, "description": 999}`
- **Beklenen:** 400 (description string|null)
- **Gözlenen Özet:** 200 OK; description='' olarak oluşturuldu (İlgili: **BULGU-11, BULGU-08**)
- **HTTP Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{"id":"clm_18","policyId":"pol_5","ownerUserId":"u1","amount":100,"status":"submitted","description":"","createdAt":"2026-08-01T00:00:00Z"}
```

#### TC-065 — POST /claims ekstra alanlar (status, ownerUserId, id) [BAŞARISIZ]
- **İstek:** `POST http://localhost:4101/claims`
- **Başlıklar:** `Authorization: Bearer tok_user1_ayse`, `Content-Type: application/json`
- **İstek Gövdesi:** `{"policyId": "pol_5", "amount": 200, "status": "approved", "ownerUserId": "u2", "id": "clm_hack"}`
- **Beklenen:** 201 (ekstra alanlar yok sayılır, claimNumber mevcut)
- **Gözlenen Özet:** 200 OK; ekstra alanlar yok sayıldı ama 200 ve claimNumber yok (İlgili: **BULGU-08, BULGU-09**)
- **HTTP Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{"id":"clm_19","policyId":"pol_5","ownerUserId":"u1","amount":200,"status":"submitted","description":"","createdAt":"2026-08-01T00:00:00Z"}
```

#### TC-066 — POST /claims bozuk JSON [BAŞARISIZ]
- **İstek:** `POST http://localhost:4101/claims`
- **Başlıklar:** `Content-Type: application/json`, `Authorization: Bearer tok_user1_ayse`
- **İstek Gövdesi:** `{"policyId": "pol_1", `
- **Beklenen:** 400 güvenli Error şeması (stack yok)
- **Gözlenen Özet:** 400; 'detail' ve 'stack' (dosya yolu) sızdı (İlgili: **BULGU-07**)
- **HTTP Durum Kodu:** `400`
- **Yanıt Gövdesi:**
```json
{"error":"Geçersiz JSON","detail":"Expected double-quoted property name in JSON at position 22 (line 1 column 23)","stack":"SyntaxError: Expected double-quoted property name in JSON at position 22 (line 1 column 23)\n    at JSON.parse (<anonymous>)\n    at Server.<anonymous> (C:\\eval\\servers\\R01\\server.js:216:25)\n    at process.processTicksAndRejections (node:internal/process/task_queues:104:5)"}
```

### Grup: 6-Admin

#### TC-067 — GET /admin/policies u1 yetkisiz [BAŞARILI]
- **İstek:** `GET http://localhost:4101/admin/policies`
- **Başlıklar:** `Authorization: Bearer tok_user1_ayse`
- **HTTP Durum Kodu:** `403`
- **Yanıt Gövdesi:**
```json
{"error":"Erişim engellendi","message":"Yönetici yetkisi gerekli."}
```

#### TC-068 — GET /admin/policies admin [BAŞARILI]
- **İstek:** `GET http://localhost:4101/admin/policies`
- **Başlıklar:** `Authorization: Bearer tok_admin_root`
- **HTTP Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
[{"id":"pol_1","policyNumber":"POL-2026-0001","ownerUserId":"u1","holderName":"Ayşe Yılmaz","holderTckn":"11111111110","coverageType":"kasko","premium":1500,"coverageLimit":50000,"status":"active","agentName":"Zeynep Kaya","startDate":"2026-01-01","endDate":"2026-12-31"},{"id":"pol_2","policyNumber":"POL-2026-0002","ownerUserId":"u1","holderName":"Ayşe Yılmaz","holderTckn":"11111111110","coverageType":"konut","premium":2400,"coverageLimit":100000,"status":"active","agentName":null,"startDate":"2026-02-15","endDate":"2027-02-14"},{"id":"pol_3","policyNumber":"POL-2026-0003","ownerUserId":"u2","holderName":"Mehmet Demir","holderTckn":"22222222220","coverageType":"saglik","premium":900,"coverag... (kısaltıldı)
```

#### TC-069 — GET /admin/stats token olmadan [BAŞARILI]
- **İstek:** `GET http://localhost:4101/admin/stats`
- **Başlıklar:** (yok)
- **HTTP Durum Kodu:** `401`
- **Yanıt Gövdesi:**
```json
{"error":"Yetkisiz","message":"Geçerli bir bearer token gerekli."}
```

#### TC-070 — GET /admin/stats u1 normal kullanıcı (Yetki Aşımı!) [BAŞARISIZ]
- **İstek:** `GET http://localhost:4101/admin/stats`
- **Başlıklar:** `Authorization: Bearer tok_user1_ayse`
- **Beklenen:** 403 Forbidden (yalnızca admin)
- **Gözlenen Özet:** 200 OK; tüm sistem istatistikleri döndü (İlgili: **BULGU-01**)
- **HTTP Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{"totalPolicies":5,"totalClaims":19,"totalPremium":9800}
```

#### TC-071 — GET /admin/stats u2 normal kullanıcı (Yetki Aşımı!) [BAŞARISIZ]
- **İstek:** `GET http://localhost:4101/admin/stats`
- **Başlıklar:** `Authorization: Bearer tok_user2_mehmet`
- **Beklenen:** 403 Forbidden (yalnızca admin)
- **Gözlenen Özet:** 200 OK; tüm sistem istatistikleri döndü (İlgili: **BULGU-01**)
- **HTTP Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{"totalPolicies":5,"totalClaims":19,"totalPremium":9800}
```

#### TC-072 — GET /admin/stats admin [BAŞARILI]
- **İstek:** `GET http://localhost:4101/admin/stats`
- **Başlıklar:** `Authorization: Bearer tok_admin_root`
- **HTTP Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{"totalPolicies":5,"totalClaims":19,"totalPremium":9800}
```

### Grup: 6-Other

#### TC-073 — DELETE /policies/pol_1 desteklenmeyen yöntem [BAŞARILI]
- **İstek:** `DELETE http://localhost:4101/policies/pol_1`
- **Başlıklar:** `Authorization: Bearer tok_admin_root`
- **HTTP Durum Kodu:** `405`
- **Yanıt Gövdesi:**
```json
{"error":"Yöntem desteklenmiyor"}
```

#### TC-074 — GET /unknown olmayan uç [BAŞARILI]
- **İstek:** `GET http://localhost:4101/unknown`
- **Başlıklar:** `Authorization: Bearer tok_admin_root`
- **HTTP Durum Kodu:** `404`
- **Yanıt Gövdesi:**
```json
{"error":"Bulunamadı","message":"Kaynak yok."}
```

### Grup: 7-Crash-DoS

#### TC-075 — PATCH /policies/pol_2 gövde null (DoS çökme) [BAŞARISIZ]
- **İstek:** `PATCH http://localhost:4101/policies/pol_2`
- **Başlıklar:** `Content-Type: application/json`, `Authorization: Bearer tok_user1_ayse`
- **İstek Gövdesi:** `null`
- **Beklenen:** 400 Bad Request, sunucu ayakta kalmalı
- **Gözlenen Özet:** CONN_ERR (10054); sunucu çöktü ve yeniden başladı (İlgili: **BULGU-03**)
- **HTTP Durum Kodu:** `CONN_ERR`
- **Yanıt Gövdesi:**
```json
ConnectionResetError(10054, 'Varolan bir bağlantı uzaktaki bir ana bilgisayar tarafından zorla kapatıldı', None, 10054, None)
```

#### TC-076 — GET /health PATCH null sonrası kontrol [BAŞARILI]
- **İstek:** `GET http://localhost:4101/health`
- **Başlıklar:** (yok)
- **HTTP Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{"status":"ok","service":"anadolu-guven-sigorta-api"}
```

#### TC-077 — POST /claims gövde null (DoS çökme) [BAŞARISIZ]
- **İstek:** `POST http://localhost:4101/claims`
- **Başlıklar:** `Content-Type: application/json`, `Authorization: Bearer tok_user1_ayse`
- **İstek Gövdesi:** `null`
- **Beklenen:** 400 Bad Request, sunucu ayakta kalmalı
- **Gözlenen Özet:** CONN_ERR (10054); sunucu çöktü ve yeniden başladı (İlgili: **BULGU-03**)
- **HTTP Durum Kodu:** `CONN_ERR`
- **Yanıt Gövdesi:**
```json
ConnectionResetError(10054, 'Varolan bir bağlantı uzaktaki bir ana bilgisayar tarafından zorla kapatıldı', None, 10054, None)
```

#### TC-078 — GET /health POST null sonrası kontrol [BAŞARILI]
- **İstek:** `GET http://localhost:4101/health`
- **Başlıklar:** (yok)
- **HTTP Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{"status":"ok","service":"anadolu-guven-sigorta-api"}
```

#### TC-079 — GET /claims çökme/yeniden başlatma sonrası durum sıfırlanması kontrolü [KANIT]
- **İstek:** `GET http://localhost:4101/claims`
- **Başlıklar:** `Authorization: Bearer tok_admin_root`
- **Beklenen:** Önceki kayıtlar korunmalı
- **Gözlenen Özet:** 200; çökme sonrası bellek sıfırlandı (total=7) (İlgili: **BULGU-03**)
- **HTTP Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{"data":[{"id":"clm_1","policyId":"pol_1","ownerUserId":"u1","amount":12000,"status":"submitted","description":"Çarpma hasarı","createdAt":"2026-05-02T09:00:00Z"},{"id":"clm_2","policyId":"pol_1","ownerUserId":"u1","amount":8000,"status":"rejected","description":"Cam kırığı","createdAt":"2026-05-10T11:30:00Z"},{"id":"clm_3","policyId":"pol_2","ownerUserId":"u1","amount":3000,"status":"approved","description":"Su baskını","createdAt":"2026-06-01T08:15:00Z"},{"id":"clm_4","policyId":"pol_5","ownerUserId":"u1","amount":15000,"status":"submitted","description":"Trafik kazası","createdAt":"2026-06-20T14:45:00Z"},{"id":"clm_5","policyId":"pol_2","ownerUserId":"u1","amount":2000,"status":"submitted... (kısaltıldı)
```
