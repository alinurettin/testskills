# Test Kayıtları — Anadolu Güven Sigorta Poliçe & Hasar API

- **Hedef Servis:** `http://localhost:4102`
- **Referans Sözleşme:** `openapi.yaml` (Anadolu Güven Sigorta - Poliçe & Hasar API v1.0.0)
- **Test Tarihi:** 2026-11-16 / 2026-11-17
- **Kullanılan Test Token'ları (Sentetik):**
  - `u1` (Normal kullanıcı — Ayşe Yılmaz): `Authorization: Bearer tok_user1_ayse`
  - `u2` (Normal kullanıcı — Mehmet Demir): `Authorization: Bearer tok_user2_mehmet`
  - `admin` (Yönetici — Sistem Yöneticisi): `Authorization: Bearer tok_admin_root`

> **Durum Sıfırlanması Notu:** Testler sırasında JSON `null` gövde gönderimi (`TC-059` ve `TC-060`) sunucu sürecini iki kez çökertip yeniden başlatmıştır; bu nedenle bellekte geçici olarak oluşturulan hasar kayıt numaraları (`clm_8`..`clm_19`) yeniden başlatma sonrasında başlangıç durumuna (`clm_1`..`clm_7`) dönmüş ve sonraki turlarda yeniden `clm_8`..`clm_12` olarak üretilmiştir. Testlerin sonunda poliçe verilerinin (`pol_1`..`pol_5`) başlangıç değerlerine döndürüldüğü ve `/health` ucunun ayakta olduğu doğrulanmıştır.

---

## 1. Sağlık Kontrolü ve Kimlik Doğrulama (Auth)

| Test ID | Senaryo | İstek (Metot, Uç, Token/Başlık) | Beklenen | Gerçekleşen Yanıt | Durum |
|---|---|---|---|---|---|
| TC-001 | Sağlık kontrolü (yetkisiz erişim) | `GET /health` (token yok) | `200`, `{"status": "..."}` | `200` — `{"status":"ok","service":"anadolu-guven-sigorta-api"}` | GEÇTİ |
| TC-002 | Korunan uçlara tokensız erişim | `GET /policies`, `GET /claims`, `GET /admin/policies`, `GET /admin/stats`, `POST /claims`, `PATCH /policies/pol_1` (token yok) | `401` (`Error` şeması) | Tümü `401` — `{"error":"Yetkisiz","message":"Geçerli bir bearer token gerekli."}` | GEÇTİ |
| TC-003 | Geçersiz / bozuk Authorization başlıkları | `GET /policies` (`Bearer bad_token_123`, `Bearer `, `tok_user1_ayse`, `Basic dXNlcjpwYXNz`, `Bearer tok_admin_root_fake`) | `401` | Tümü `401` — `{"error":"Yetkisiz","message":"Geçerli bir bearer token gerekli."}` | GEÇTİ |
| TC-004 | Küçük harfli `bearer` şeması | `GET /policies` (`Authorization: bearer tok_user1_ayse`) | `200` (RFC uyumlu kabul) | `200` — `u1`'in 3 poliçesi (`pol_1`, `pol_2`, `pol_5`) döndü | GEÇTİ |

---

## 2. Poliçe Listeleme, Yönetici Uçları ve Tekil Poliçe Okuma

| Test ID | Senaryo | İstek (Metot, Uç, Token) | Beklenen | Gerçekleşen Yanıt | Durum |
|---|---|---|---|---|---|
| TC-005 | Normal kullanıcı `u1` poliçeleri listeler | `GET /policies` (`tok_user1_ayse`) | `200`, yalnızca `u1` poliçeleri (`Policy[]`) | `200` — 3 poliçe: `pol_1`, `pol_2`, `pol_5` (tüm alanlar `Policy` şemasına uygun) | GEÇTİ |
| TC-006 | Normal kullanıcı `u2` poliçeleri listeler | `GET /policies` (`tok_user2_mehmet`) | `200`, yalnızca `u2` poliçeleri | `200` — 2 poliçe: `pol_3` (`status:"cancelled"`), `pol_4` (`status:"active"`) | GEÇTİ |
| TC-007 | Yönetici tüm poliçeleri listeler (`GET /policies` ve `GET /admin/policies`) | `GET /policies` ve `GET /admin/policies` (`tok_admin_root`) | `200`, tüm 5 poliçe | `200` — 5 poliçe (`pol_1`..`pol_5`) | GEÇTİ |
| TC-008 | Normal kullanıcı `GET /admin/policies` erişimi | `GET /admin/policies` (`tok_user1_ayse` ve `tok_user2_mehmet`) | `403` | Her ikisi de `403` — `{"error":"Erişim engellendi","message":"Yönetici yetkisi gerekli."}` | GEÇTİ |
| TC-009 | Normal kullanıcı `GET /admin/stats` erişimi | `GET /admin/stats` (`tok_user1_ayse` ve `tok_user2_mehmet`) | `403 Forbidden` | **Her ikisi de `200 OK`** — `{"totalPolicies":5,"totalClaims":7,"totalPremium":9800}` (yeni talepler sonrası `totalClaims:12`) | **KALDI (BLG-03)** |
| TC-010 | Yönetici `GET /admin/stats` erişimi | `GET /admin/stats` (`tok_admin_root`) | `200`, doğru toplamlar | `200` — `{"totalPolicies":5,"totalClaims":7,"totalPremium":9800}` (toplam prim: 1500+2400+900+3200+1800 = 9800) | GEÇTİ |
| TC-011 | Tekil poliçe okuma — kendi poliçesi | `GET /policies/pol_1` (`tok_user1_ayse`), `GET /policies/pol_3` (`tok_user2_mehmet`) | `200` | `200` — İlgili poliçe nesnesi döndü | GEÇTİ |
| TC-012 | Tekil poliçe okuma — başka kullanıcının poliçesi (IDOR kontrolü) | `GET /policies/pol_3` (`tok_user1_ayse`), `GET /policies/pol_1` (`tok_user2_mehmet`) | `403` | `403` — `{"error":"Erişim engellendi","message":"Bu poliçeye erişim yetkiniz yok."}` | GEÇTİ |
| TC-013 | Tekil poliçe okuma — yönetici erişimi | `GET /policies/pol_1`, `GET /policies/pol_3` (`tok_admin_root`) | `200` | `200` — Her iki poliçe de döndü | GEÇTİ |
| TC-014 | Olmayan poliçe okuma | `GET /policies/pol_999` (`tok_user1_ayse`, `tok_user2_mehmet`, `tok_admin_root`) | `404` | `404` — `{"error":"Bulunamadı","message":"Poliçe bulunamadı."}` | GEÇTİ |

---

## 3. Hasar Talepleri Okuma, `policyId` Süzme ve Sayfalama (`GET /claims`, `GET /claims/{id}`)

| Test ID | Senaryo | İstek (Metot, Uç, Token) | Beklenen | Gerçekleşen Yanıt | Durum |
|---|---|---|---|---|---|
| TC-015 | Normal kullanıcı kendi hasar taleplerini listeler | `GET /claims` (`tok_user1_ayse`), `GET /claims` (`tok_user2_mehmet`) | `200`, yalnızca kendi talepleri + `Claim` şeması (`claimNumber` zorunlu) | `200` — `u1`: 5 kayıt (`clm_1`..`clm_5`), `u2`: 2 kayıt (`clm_6`, `clm_7`); **ancak hiçbir kayıtta `claimNumber` alanı yok** | **KALDI (BLG-09)** |
| TC-016 | Yönetici tüm hasar taleplerini listeler | `GET /claims` (`tok_admin_root`) | `200`, tüm talepler + `Claim` şeması | `200` — 7 kayıt (`clm_1`..`clm_7`), `meta:{"page":1,"pageSize":20,"total":7}`; **`claimNumber` alanı yok** | **KALDI (BLG-09)** |
| TC-017 | Tekil hasar talebi okuma — kendi talebi / yönetici | `GET /claims/clm_1` (`tok_user1_ayse`, `tok_admin_root`), `GET /claims/clm_6` (`tok_user2_mehmet`, `tok_admin_root`) | `200` + `Claim` şeması | `200` — Kayıt döndü fakat **`claimNumber` alanı yok** | **KALDI (BLG-09)** |
| TC-018 | Tekil hasar talebi okuma — başka kullanıcının talebi (IDOR kontrolü) | `GET /claims/clm_6` (`tok_user1_ayse`), `GET /claims/clm_1` (`tok_user2_mehmet`) | `403` | `403` — `{"error":"Erişim engellendi","message":"Bu hasar talebine erişim yetkiniz yok."}` | GEÇTİ |
| TC-019 | Olmayan hasar talebi okuma | `GET /claims/clm_999` (`tok_user1_ayse`, `tok_user2_mehmet`, `tok_admin_root`) | `404` | `404` — `{"error":"Bulunamadı","message":"Hasar talebi bulunamadı."}` | GEÇTİ |
| TC-020 | Kendi poliçesine göre süzme | `GET /claims?policyId=pol_1` (`tok_user1_ayse`) | `200`, `pol_1` talepleri | `200` — `clm_1`, `clm_2` (`claimNumber` eksik) | GEÇTİ (şema hariç) |
| TC-021 | Başkasının poliçesine göre süzme (`u1` -> `pol_3`) | `GET /claims?policyId=pol_3` (`tok_user1_ayse`) | `403` veya boş liste (başkasının talepleri dönmemeli) | **`200 OK`** — `{"data":[{"id":"clm_7","policyId":"pol_3","ownerUserId":"u2","amount":1000,"status":"rejected","description":"Muayene masrafı","createdAt":"2026-06-11T13:00:00Z"}],"meta":{"page":1,"pageSize":20,"total":1}}` | **KALDI (BLG-01)** |
| TC-022 | Başkasının poliçesine göre süzme (`u1` -> `pol_4`) | `GET /claims?policyId=pol_4` (`tok_user1_ayse`) | Başkasının talepleri dönmemeli | **`200 OK`** — `u2`'ye ait `clm_6` döndü | **KALDI (BLG-01)** |
| TC-023 | Başkasının poliçesine göre süzme (`u2` -> `pol_1`, `pol_2`) | `GET /claims?policyId=pol_1` ve `pol_2` (`tok_user2_mehmet`) | Başkasının talepleri dönmemeli | **`200 OK`** — `u1`'e ait `clm_1`, `clm_2` (`pol_1`) ve `clm_3`, `clm_5` (`pol_2`) döndü | **KALDI (BLG-01)** |
| TC-024 | Sayfalama `meta.total` kontrolü (`u1`, 5 kayıt) | `GET /claims?page=1&pageSize=1`, `page=3&pageSize=2`, `page=4&pageSize=2` (`tok_user1_ayse`) | Her yanıt `meta.total: 5` olmalı | `page=1&pageSize=1` -> `meta.total: 1`; `page=3&pageSize=2` -> `meta.total: 1`; `page=4&pageSize=2` -> `meta.total: 0` | **KALDI (BLG-10)** |
| TC-025 | Sayfalama `meta.total` kontrolü (`admin`, 7 kayıt) | `GET /claims?page=1&pageSize=2` (`tok_admin_root`) | `meta.total: 7` olmalı | `200` — `data` içinde 2 kayıt, `meta:{"page":1,"pageSize":2,"total":2}` | **KALDI (BLG-10)** |
| TC-026 | Negatif `page` parametresi | `GET /claims?page=-1&pageSize=2` (`tok_user1_ayse` ve `tok_admin_root`) | `400` veya geçersiz sayfa reddi | `u1`: `200` ile `clm_2`, `clm_3` ve `meta:{"page":-1,"pageSize":2,"total":2}`; `admin`: `200` ile `clm_4`, `clm_5` ve `page:-1` | **KALDI (BLG-10)** |
| TC-027 | Negatif `pageSize` parametresi | `GET /claims?page=1&pageSize=-5` (`tok_admin_root`) | `400` (`minimum: 1`) | `200` — `clm_1`, `clm_2` döndü ve `meta:{"page":1,"pageSize":-5,"total":2}` | **KALDI (BLG-10)** |
| TC-028 | Sayısal olmayan `page` / `pageSize` | `GET /claims?page=abc&pageSize=2` ve `page=1&pageSize=abc` (`tok_user1_ayse`) | `400` (`type: integer`) | `200` — `data:[]`, `meta:{"page":null,"pageSize":2,"total":0}` / `meta:{"page":1,"pageSize":null,"total":0}` | **KALDI (BLG-10)** |
| TC-029 | Üst sınır aşımı `pageSize=101` | `GET /claims?page=1&pageSize=101` (`tok_user1_ayse`, `tok_admin_root`) | `400` veya 100 ile sınırlama (`maximum: 100`) | `200` — `meta.pageSize: 101` ile kabul edildi | **KALDI (BLG-10)** |
| TC-030 | Ondalıklı / sıfır / aşırı büyük sayfalama | `page=0&pageSize=2`, `page=1&pageSize=0`, `page=1.5&pageSize=2`, `page=1&pageSize=1.5`, `page=999999&pageSize=20` (`tok_user1_ayse`) | `page=0`/`pageSize=0`/`1.5` için `400` | Tümü `200` (`page=1.5` -> `page:1`; `pageSize=1.5` -> `pageSize:1`; `page=0` -> `data:[], total:0`) | **KALDI (BLG-10)** |

---

## 4. Poliçe Güncelleme (`PATCH /policies/{id}`)

| Test ID | Senaryo | İstek (Metot, Uç, Token, Gövde) | Beklenen | Gerçekleşen Yanıt | Durum |
|---|---|---|---|---|---|
| TC-031 | Başkasının poliçesini güncelleme (IDOR) | `PATCH /policies/pol_3` (`tok_user1_ayse`, `{"holderName":"Hacked"}`), `PATCH /policies/pol_1` (`tok_user2_mehmet`, `{"holderName":"Hacked"}`) | `403` | `403` — `{"error":"Erişim engellendi","message":"Bu poliçeye erişim yetkiniz yok."}` | GEÇTİ |
| TC-032 | Olmayan poliçeyi güncelleme | `PATCH /policies/pol_999` (`tok_user1_ayse`, `{"holderName":"Test"}`) | `404` | `404` — `{"error":"Bulunamadı","message":"Poliçe bulunamadı."}` | GEÇTİ |
| TC-033 | Geçerli `holderName` ve `agentName` (dahil `null`) güncellemesi | `PATCH /policies/pol_2` (`tok_user1_ayse`, `{"holderName":"Ayşe Yılmaz Test","agentName":"Ali Veli"}` ve ardından `{"holderName":"Ayşe Yılmaz","agentName":null}`) | `200`, güncellenmiş poliçe | `200` — Alanlar doğru güncellendi ve geri alındı | GEÇTİ |
| TC-034 | Salt okunur alanların yok sayılması + `status` kaçak güncellemesi | `PATCH /policies/pol_5` (`tok_user1_ayse`, `{"holderName":"Ayşe Yılmaz","premium":1,"coverageLimit":9999999,"status":"cancelled","ownerUserId":"u2","policyNumber":"POL-HACK-9999","coverageType":"kasko","holderTckn":"99999999999","startDate":"2020-01-01","endDate":"2030-01-01","id":"pol_hack"}`) | Tüm salt okunur alanlar (dahil `status`) yok sayılmalı | `premium`, `coverageLimit`, `ownerUserId`, `policyNumber`, `coverageType`, `holderTckn`, `startDate`, `endDate`, `id` korundu **ancak `status` `"cancelled"` olarak değişti**! | **KALDI (BLG-04)** |
| TC-035 | `status` alanına geçersiz enum değeri yazılması | `PATCH /policies/pol_5` (`tok_user1_ayse`, `{"status":"hacked_status"}`) | Yok sayılmalı veya `400` dönmeli | **`200 OK`** — `pol_5.status` değeri `"hacked_status"` olarak kaydedildi | **KALDI (BLG-04)** |
| TC-036 | İptal edilmiş poliçeyi (`cancelled`) kullanıcının yeniden `active` yapması | `PATCH /policies/pol_3` (`tok_user2_mehmet`, `{"status":"active"}`) | `status` değişmemeli (`cancelled` kalmalı) | **`200 OK`** — `pol_3.status` `"cancelled"` -> `"active"` oldu (test sonrası `"cancelled"`'a geri alındı) | **KALDI (BLG-04)** |
| TC-037 | `holderName` ve `agentName` için yanlış veri tipleri | `PATCH /policies/pol_2` (`tok_user1_ayse`, `{"holderName":12345,"agentName":true}`) | `400 BadRequest` | **`200 OK`** — `"holderName":12345,"agentName":true` kaydedildi | **KALDI (BLG-12)** |
| TC-038 | `holderName: null` gönderilmesi | `PATCH /policies/pol_2` (`tok_user1_ayse`, `{"holderName":null}`) | `400 BadRequest` (`holderName` nullable değil) | **`200 OK`** — `"holderName":null` kaydedildi (test sonrası `"Ayşe Yılmaz"` geri yüklendi) | **KALDI (BLG-12)** |
| TC-039 | Bilinmeyen ek alan gönderilmesi | `PATCH /policies/pol_5` (`tok_user1_ayse`, `{"extraUnknown":"foo"}`) | Yok sayılmalı veya `400` | `200 OK` — `extraUnknown` yok sayıldı (kayıt değişmedi) | GEÇTİ |
| TC-040 | Yönetici tarafından poliçe güncelleme | `PATCH /policies/pol_2` (`tok_admin_root`, `{"agentName":"Admin Agent"}`) | `200` (admin tüm kaynaklara erişebilir) | `200 OK` — `agentName` güncellendi (test sonrası `null` yapıldı) | GEÇTİ |

---

## 5. Hasar Talebi Oluşturma, İş Kuralları ve Idempotency (`POST /claims`)

| Test ID | Senaryo | İstek (Metot, Uç, Token, Gövde) | Beklenen | Gerçekleşen Yanıt | Durum |
|---|---|---|---|---|---|
| TC-041 | Başkasının poliçesine hasar talebi açma (IDOR) | `POST /claims` (`tok_user1_ayse`, `{"policyId":"pol_4","amount":100}`) ve (`tok_user2_mehmet`, `{"policyId":"pol_1","amount":100}`) | `403` | `403` — `{"error":"Erişim engellendi","message":"Bu poliçe için hasar talebi oluşturamazsınız."}` | GEÇTİ |
| TC-042 | Olmayan poliçeye hasar talebi açma | `POST /claims` (`tok_user1_ayse`, `{"policyId":"pol_999","amount":100}`) | `404` | `404` — `{"error":"Bulunamadı","message":"Poliçe bulunamadı."}` | GEÇTİ |
| TC-043 | Teminat limitini (`50000`) aşan talep (`50001`) | `POST /claims` (`tok_user1_ayse`, `{"policyId":"pol_1","amount":50001,"description":"Over limit"}`) | `422 Unprocessable Entity` | **`200 OK`** — `{"id":"clm_9","policyId":"pol_1","ownerUserId":"u1","amount":50001,"status":"submitted","description":"Over limit","createdAt":"2026-08-01T00:00:00Z"}` | **KALDI (BLG-05)** |
| TC-044 | Aşırı büyük tutar (`1e308`) ile limit aşımı | `POST /claims` (`tok_user1_ayse`, `{"policyId":"pol_1","amount":1e308}`) | `422` | **`200 OK`** — `clm_10` (`amount: 1e+308`) oluşturuldu | **KALDI (BLG-05)** |
| TC-045 | Teminat limitine eşit tutar (`50000 == 50000`) | `POST /claims` (`tok_user1_ayse`, `{"policyId":"pol_1","amount":50000,"description":"Exact limit"}`) | `201 Created` + `claimNumber` | **`200 OK`** (`201` yerine) ve **`claimNumber` alanı eksik** (`clm_10`) | **KALDI (BLG-08, BLG-09)** |
| TC-046 | `amount: 0` ile hasar talebi (`minimum: 1` ihlali) | `POST /claims` (`tok_user1_ayse`, `{"policyId":"pol_1","amount":0}`) | `400` veya `422` | **`200 OK`** — `clm_11` (`amount: 0`) oluşturuldu | **KALDI (BLG-07)** |
| TC-047 | Negatif `amount: -500` ile hasar talebi | `POST /claims` (`tok_user1_ayse`, `{"policyId":"pol_1","amount":-500}`) | `400` veya `422` | **`200 OK`** — `clm_12` (`amount: -500`) oluşturuldu | **KALDI (BLG-07)** |
| TC-048 | `1`'den küçük ondalıklı `amount: 0.5` | `POST /claims` (`tok_user1_ayse`, `{"policyId":"pol_1","amount":0.5}`) | `400` veya `422` (`minimum: 1`) | **`200 OK`** — `clm_13` (`amount: 0.5`) oluşturuldu | **KALDI (BLG-07)** |
| TC-049 | Zorunlu alan eksiklikleri ve yanlış `amount` tipleri | `{"policyId":"pol_1"}`, `{"amount":500}`, `{"policyId":"pol_1","amount":"1000"}`, `{"policyId":"pol_1","amount":true}`, `{"policyId":"pol_1","amount":null}` (`tok_user1_ayse`) | `400` | Eksik alan: `400` (`"policyId ve amount zorunludur."`), yanlış tip: `400` (`"amount sayısal olmalıdır."`) | GEÇTİ |
| TC-050 | `description` için sayısal değer (`999`) gönderimi | `POST /claims` (`tok_user1_ayse`, `{"policyId":"pol_1","amount":100,"description":999}`) | `400` (`description: string\|null`) | `200 OK` — `description` sessizce `""` (boş metin) olarak kaydedildi | **KALDI (BLG-07 / tip)** |
| TC-051 | `Idempotency-Key` ile aynı isteğin tekrarlanması (ilk koşu) | 3 kez `POST /claims` (`tok_user2_mehmet`, `{"policyId":"pol_4","amount":1234,"description":"Idempotency test 1"}`, başlık: `Idempotency-Key: idem-test-key-001` ve `idempotency-key: idem-test-key-001`) | 2. ve 3. istek yeni kayıt oluşturmamalı, ilk kaydı dönmeli | Her istekte **yeni kayıt** oluştu: `clm_16`, `clm_17`, `clm_18` (hepsi `200` döndü) | **KALDI (BLG-06, BLG-08)** |
| TC-052 | `Idempotency-Key` ile temiz doğrulama koşusu | 2 kez `POST /claims` (`tok_user2_mehmet`, `{"policyId":"pol_4","amount":2500,"description":"Idempotency check"}`, başlık: `Idempotency-Key: req-idem-clean-1`) | 2. istek aynı `id` (`clm_11`) dönmeli | 1. istek `clm_11`, 2. istek **`clm_12`** oluşturdu | **KALDI (BLG-06)** |
| TC-053 | Aynı `Idempotency-Key` farklı gövde ile gönderim | `POST /claims` (`tok_user2_mehmet`, `{"policyId":"pol_4","amount":5555,"description":"Diff payload same key"}`, `Idempotency-Key: idem-test-key-001`) | Idempotency kontrolü devrede olmalı | `200 OK` — `clm_19` oluşturuldu | **KALDI (BLG-06)** |
| TC-054 | Gövdede `status`, `ownerUserId`, `id` zorlama denemesi | `POST /claims` (`tok_user1_ayse`, `{"policyId":"pol_1","amount":250,"description":"Extra fields","status":"approved","ownerUserId":"u2","id":"clm_999"}`) | Sunucu tarafından atanmalı / değiştirilememeli | `200` — `id:"clm_15","ownerUserId":"u1","status":"submitted"` olarak güvenli atandı (`200` statüsü ve `claimNumber` eksikliği hariç) | GEÇTİ (ek alan yok sayma) |
| TC-055 | İptal edilmiş poliçeye (`pol_3`) hasar talebi (gözlem) | `POST /claims` (`tok_user2_mehmet`, `{"policyId":"pol_3","amount":500,"description":"Cancelled policy claim"}`) | Sözleşmede yasaklanmamış (örnek veride `clm_7` de `pol_3` üstünde) | `200` — `clm_14` oluşturuldu | GÖZLEM |
| TC-056 | Yönetici `u1`'in poliçesine talep açınca `ownerUserId` ataması (gözlem) | `POST /claims` (`tok_admin_root`, `{"policyId":"pol_1","amount":111,"description":"Admin created on u1 pol_1"}`) | — | `200` — `clm_8` `ownerUserId:"admin"` ile oluştu; `u1` `GET /claims/clm_8` isteğinde `403` aldı | GÖZLEM |

---

## 6. Beklenmedik / Kötü Girdiler, Hata İşleme ve Dayanıklılık

| Test ID | Senaryo | İstek (Metot, Uç, Token, Gövde) | Beklenen | Gerçekleşen Yanıt | Durum |
|---|---|---|---|---|---|
| TC-057 | Bozuk JSON gönderimi (`POST /claims`) | `POST /claims` (`tok_user1_ayse`, gövde: `{bad json`, `{"policyId":`, veya `{"policyId":"pol_1","amount":Infinity}`) | `400 BadRequest` (`Error` şeması; iç yol/stack yok) | `400` — `{"error":"Geçersiz JSON","detail":"...","stack":"SyntaxError: ...\n at JSON.parse (<anonymous>)\n at Server.<anonymous> (C:\\eval\\servers\\R04\\server.js:216:25)\n ..."}` | **KALDI (BLG-11)** |
| TC-058 | Bozuk JSON gönderimi (`PATCH /policies/{id}`) | `PATCH /policies/pol_2` (`tok_user1_ayse`, gövde: `{bad`) | `400 BadRequest` (iç yol/stack yok) | `400` — `stack` içinde `...\servers\R04\server.js:155:27` sızdırıldı | **KALDI (BLG-11)** |
| TC-059 | JSON `null` gövde (`POST /claims`) | `POST /claims` (`tok_user1_ayse`, `Content-Type: application/json`, gövde: `null`) | `400 BadRequest` | **Sunucu bağlantıyı kesti (`WinError 10054` / `curl` çıkış kodu `1`) ve süreç çöküp yeniden başladı** | **KALDI (BLG-02)** |
| TC-060 | JSON `null` gövde (`PATCH /policies/{id}`) | `PATCH /policies/pol_2` (`tok_user1_ayse`, `Content-Type: application/json`, gövde: `null`) | `400 BadRequest` | **Sunucu bağlantıyı kesti (`WinError 10054`) ve süreç çöküp yeniden başladı** (`clm_8` silindi) | **KALDI (BLG-02)** |
| TC-061 | İlkel tip / dizi gövdeler (`POST /claims`) | `POST /claims` (`tok_user1_ayse`, gövdeler: `""`, `[1,2,3]`, `"hello"`, `123`) | `400` | `400` — `{"error":"Eksik alan","message":"policyId ve amount zorunludur."}` | GEÇTİ |
| TC-062 | Dizi / metin gövdeler (`PATCH /policies/{id}`) | `PATCH /policies/pol_2` (`tok_user1_ayse`, gövdeler: `[]`, `"hello"`) | `400 BadRequest` (`PolicyUpdate` nesne olmalı) | **`200 OK`** — Mevcut poliçeyi değiştirmeden döndürdü | **KALDI (BLG-12)** |
| TC-063 | Desteklenmeyen HTTP metotları ve bilinmeyen yollar | `DELETE /policies/pol_1`, `PUT /policies/pol_1`, `POST /policies`, `GET /unknown/route`, `POST /health` | `404` / `405` / `401` | `DELETE`/`PUT` -> `405 {"error":"Yöntem desteklenmiyor"}`; `POST /policies` & `GET /unknown/route` -> `404 {"error":"Bulunamadı","message":"Kaynak yok."}`; `POST /health` -> `401` | GEÇTİ |
| TC-064 | Path traversal ve prototype pollution stringleri | `GET /policies/../../etc/passwd`, `GET /policies/__proto__`, `GET /claims?policyId=__proto__`, `GET /claims?policyId=constructor` (`tok_user1_ayse`) | Güvenli `404` / `200 []` (çökme yok) | `404` (`Kaynak yok.` / `Poliçe bulunamadı.`) veya `200` (`data:[]`) | GEÇTİ |
