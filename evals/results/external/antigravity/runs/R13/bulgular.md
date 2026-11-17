# Kusur (Defect) Raporu — Anadolu Güven Sigorta Poliçe & Hasar API

**Test Edilen Servis:** `anadolu-guven-sigorta-api` (`http://localhost:4108`)  
**Sözleşme Referansı:** `openapi.yaml` (OpenAPI `3.1.0`, sürüm `1.0.0`)  
**Test Kapsamı:** 9 API işlemi, kimlik doğrulama/yetkilendirme (BOLA, BFLA, BOPLA/mass assignment), şema uygunluğu, sınır değerleri, iş kuralları, sayfalama, idempotency, eşzamanlılık ve kötü/bozuk girdi dayanıklılığı (toplam **222 HTTP isteği**, tam kayıtlar için bkz. `test-kayitlari.md`).  
**Test Verisi:** Yalnızca ortamda sağlanan sentetik/kurgusal veriler ve test token'ları (`tok_user1_ayse`, `tok_user2_mehmet`, `tok_admin_root`) kullanılmıştır.

---

## Yönetici Özeti ve Yayın Değerlendirmesi

API'nin temel kimlik doğrulama (`401`) ve bazı nesne sahipliği kontrolleri (`GET/PATCH /policies/{id}`, `GET /claims/{id}`, `POST /claims` gövde `policyId` sahipliği, `GET /admin/policies` rol kontrolü) çalışmakla birlikte, **canlıya çıkışı doğrudan engelleyen 4 Kritik, 4 Yüksek, 5 Orta ve 1 Düşük önem dereceli toplam 14 kök nedenli kusur** tespit edilmiştir.

**Özet Risk Alanları:**
1. **Yetkilendirme Sızıntıları (Kritik):** Normal kullanıcılar `GET /admin/stats` üzerinden şirket geneli istatistiklere erişebilmekte (`200`), `GET /claims?policyId=<başka_kullanıcı_poliçesi>` ile diğer sigortalıların hasar taleplerini okuyabilmekte ve `PATCH /policies/{id}` ile salt okunur `status` alanını değiştirebilmektedir.
2. **Finansal İş Kuralı ve Alt Sınır İhlalleri (Kritik):** `POST /claims` teminat limitini (`coverageLimit`) aşan tutarları `422` ile reddetmemekte; negatif (`-100`), sıfır (`0`), `1`'in altı (`0.99`) ve taşan (`1e309` → `amount: null`) tutarları `200` ile kaydetmektedir.
3. **Veri Tutarlılığı ve Tekrar Koruması (Yüksek):** `Idempotency-Key` başlığı tamamen yok sayılmakta (mükerrer ve yarış koşullu kayıt oluşmaktadır); tüm `Claim` yanıtlarında zorunlu `claimNumber` alanı eksiktir; `GET /claims` sayfalama `meta.total` alanı toplam kayıt sayısı yerine yalnızca mevcut sayfadaki kayıt sayısını dönmektedir.
4. **Güvenlik ve Hata Modeli (Yüksek):** Bozuk JSON gönderildiğinde sunucunun gerçek dosya yolunu ve yığın izini (`stack`) dışarı sızdıran `400` yanıtları dönmektedir.

> **Yayın Önerisi:** Mevcut haliyle **canlıya çıkış önerilmez (Bloke)**. En azından **BULGU-01 ile BULGU-08** arası (Kritik ve Yüksek önem dereceli bulgular) giderilip regresyon testleri tekrar koşulmalıdır.

---

## Bulgular Özet Tablosu

| ID | Önem Derecesi | Kategori | Etkilenen Uç(lar) | Kısa Başlık | Kanıt ID'leri |
|---|---|---|---|---|---|
| **BULGU-01** | **Kritik** | Güvenlik (BFLA) | `GET /admin/stats` | Yönetici istatistik ucu normal kullanıcılara açık (`200` dönüyor) | `P1-ADMIN-u1-/admin/stats`, `P1-ADMIN-u2-/admin/stats`, `P4-GET-STATS-CHECK` |
| **BULGU-02** | **Kritik** | Güvenlik (BOLA/IDOR) | `GET /claims` | `policyId` filtresinde poliçe sahipliği denetlenmiyor; başka kullanıcının hasarları okunabiliyor | `P1-CLM-LIST-u1-other_u2_pol3`, `P1-CLM-LIST-u1-other_u2_pol4`, `P1-CLM-LIST-u2-other_u1_pol1` |
| **BULGU-03** | **Kritik** | Güvenlik (Mass Assignment) & İş Kuralı | `PATCH /policies/{id}` | Salt okunur `status` alanı güncellenebiliyor ve enum dışı değer kabul ediliyor | `P2A-RO-STATUS`, `P2A-RO-MIXED`, `P2A-CHECK-pol_5`, `P5-PATCH-STATUS-INVALID`, `P5-PATCH-STATUS-ACTIVE` |
| **BULGU-04** | **Kritik** | İş Kuralı & Sınır Doğrulama | `POST /claims` | Teminat limitini aşan ve `1` TL altındaki / sonlu olmayan hasar tutarları kabul ediliyor | `P2B-AMT-OVER-LIMIT-1`, `P2B-AMT-OVER-LIMIT-0_01`, `P2B-AMT-NEG`, `P2B-AMT-ZERO`, `P2B-AMT-0_99`, `P4-CLM-1E309` |
| **BULGU-05** | **Yüksek** | İş Kuralı (Idempotency) | `POST /claims` | `Idempotency-Key` başlığı yok sayılıyor; tekrarlı ve paralel istekler mükerrer kayıt oluşturuyor | `P2B-IDEM-1`, `P2B-IDEM-2-REPEAT`, `P2B-IDEM-RACE-1..3` |
| **BULGU-06** | **Yüksek** | Güvenlik (Bilgi İfşası) | `PATCH /policies/{id}`, `POST /claims` | Bozuk JSON gövdesinde sunucu dosya yolu ve stack trace sızdırılıyor | `P2A-MALFORMED-JSON`, `P2B-MALFORMED-JSON`, `P4-CLM-NAN` |
| **BULGU-07** | **Yüksek** | Sözleşme / Şema | `GET /claims`, `GET /claims/{id}`, `POST /claims` | `Claim` nesnelerinde sözleşmede zorunlu olan `claimNumber` alanı eksik | `P1-CLM-LIST-u1-all_u1`, `P1-CLM-GET-u1-clm_1`, `P2B-AMT-1`, `P3-GET-CLM8` |
| **BULGU-08** | **Yüksek** | İşlevsel / Sözleşme | `GET /claims` | Sayfalı yanıtta `meta.total` toplam kayıt yerine sayfadaki kayıt sayısını dönüyor | `P1-CLM-LIST-u1-p1_s2`, `P1-CLM-LIST-u1-p3_s2`, `P1-CLM-LIST-u1-p4_s2_empty`, `P1-CLM-LIST-u1-own_pol1_p1_s1`, `P1-CLM-LIST-admin-admin_p1_s3`, `P3-U2-PAGE1-SIZE2` |
| **BULGU-09** | **Orta** | Sözleşme (Durum Kodu) | `POST /claims` | Kaynak oluşturmada HTTP `201` yerine `200` dönüyor | `P2B-AMT-1`, `P2B-NOIDEM-1`, `P4-CLM-FLOAT` |
| **BULGU-10** | **Orta** | Girdi Doğrulama & Şema | `GET /claims` | Geçersiz `page`/`pageSize` reddedilmiyor; `pageSize=-1` son kaydı kesiyor, metin değerde `null` dönüyor | `P1-CLM-LIST-u1-size_neg1`, `P3-ADMIN-SIZE-NEG1`, `P1-CLM-LIST-u1-page_abc`, `P1-CLM-LIST-u1-size_abc`, `P1-CLM-LIST-u1-page_0`, `P1-CLM-LIST-u1-size_101` |
| **BULGU-11** | **Orta** | Girdi Doğrulama & Veri Bütünlüğü | `PATCH /policies/{id}`, `POST /claims` | Metin alanlarında yanlış tip (`12345`, `true`, `null`, `""`) ve dizi gövde reddedilmiyor | `P2A-HOLDER-INT`, `P2A-HOLDER-NULL`, `P2A-HOLDER-EMPTY`, `P2A-AGENT-INT`, `P2A-AGENT-BOOL`, `P2A-ARRAY-BODY`, `P2B-DESC-INT`, `P2B-POLICYID-INT` |
| **BULGU-12** | **Orta** | Sigortacılık İş Kuralı | `POST /claims` | İptal edilmiş (`cancelled`) poliçeye yeni hasar talebi açılabiliyor | `P2B-CANCELLED-POLICY` |
| **BULGU-13** | **Orta** | Yetkilendirme / Veri Tutarlılığı | `POST /claims`, `GET /claims/{id}` | Yönetici (`admin`) başka kullanıcının poliçesine hasar açtığında `ownerUserId: "admin"` atanıyor | `P2B-ADMIN-ON-POL4`, `P3-U2-LIST-CLAIMS`, `P3-U2-GET-CLM9`, `P2B-CHK-POL4-U2` |
| **BULGU-14** | **Düşük** | Sözleşme Dokümantasyonu | `openapi.yaml` | `additionalProperties: false` çelişkisi, eksik `400`/`403` tanımları ve kısıtsız şema alanları | `P3-PATCH-UNKNOWN-ONLY`, `P3-POST-UNKNOWN-FIELD`, `P3-CLM-DESC-NULL` |

---

## Detaylı Kusur Kayıtları

### BULGU-01 — Yönetici istatistik ucu (`GET /admin/stats`) normal kullanıcılara açık (BFLA)
- **Önem Derecesi:** Kritik *(Güvenlik / Yetki Aşımı — OWASP API5: Broken Function Level Authorization)*
- **Kök Neden Türü:** Uygulama kusuru (eksik rol kontrolü)
- **Etkilenen Uç:** `GET /admin/stats`
- **Sözleşme / İş Kuralı Atfı:** `openapi.yaml` → `tags: [admin]` (*"Yönetici işlemleri (yalnızca role=admin)"*) ve `paths./admin/stats.get.description`: *"Sistem genel istatistiklerini döner. Yalnızca role=admin erişebilir; normal kullanıcı için 403 dönülmelidir."*
- **Beklenen Davranış:** Normal kullanıcı token'ları (`tok_user1_ayse`, `tok_user2_mehmet`) ile yapılan `GET /admin/stats` istekleri HTTP `403` (`Erişim engellendi`) ile reddedilmelidir (tıpkı `GET /admin/policies` ucunda olduğu gibi — bkz. `P1-ADMIN-u1-/admin/policies`).
- **Gerçekleşen Davranış:** Her iki normal kullanıcı token'ı ile de HTTP `200 OK` dönmekte ve şirket genelindeki toplam poliçe sayısı, toplam hasar sayısı ve toplam prim tutarı paylaşılmaktadır.
- **Tekrar Üretim Adımları:**
  1. İstek gönder: `GET http://localhost:4108/admin/stats`
  2. Başlık ekle: `Authorization: Bearer tok_user1_ayse` (veya `tok_user2_mehmet`)
  3. **Gözlenen Yanıt (`HTTP 200`):**
     ```json
     {"totalPolicies": 5, "totalClaims": 7, "totalPremium": 9800}
     ```
- **Kanıt:** `test-kayitlari.md` → `P1-ADMIN-u1-/admin/stats`, `P1-ADMIN-u2-/admin/stats`, `P4-GET-STATS-CHECK` (karşılaştırma: `P1-ADMIN-u1-/admin/policies` → `403`).

---

### BULGU-02 — `GET /claims?policyId=...` sorgusunda poliçe sahipliği denetlenmiyor; başka kullanıcının hasar talepleri okunabiliyor (BOLA / IDOR)
- **Önem Derecesi:** Kritik *(Güvenlik / Nesne Düzeyinde Yetki Aşımı — OWASP API1: Broken Object Level Authorization)*
- **Kök Neden Türü:** Uygulama kusuru (sorgu filtresinde sahiplik denetiminin atlanması)
- **Etkilenen Uç:** `GET /claims` (`policyId` sorgu parametresi)
- **Sözleşme / İş Kuralı Atfı:** `openapi.yaml` → `info.description` (*"Normal kullanıcı (role=user) yalnızca KENDİ poliçelerine ve KENDİ hasar taleplerine erişebilir"*) ve `paths./claims.get.description`: *"`policyId` sorgu parametresi verilirse yalnızca o poliçeye ait talepler süzülür; ancak bu durumda da yetkilendirme kuralı geçerlidir: kullanıcı yalnızca KENDİSİNE ait poliçelerin taleplerini görebilir."*
- **Beklenen Davranış:** `u1` (`tok_user1_ayse`), `u2`'ye ait `pol_3` veya `pol_4` ile `GET /claims?policyId=pol_3` / `pol_4` istediğinde başka kullanıcının hasar kayıtları dönmemeli; yetkisiz erişim (`403`, veya sözleşmeye göre süzülmüş boş sonuç) verilmelidir.
- **Gerçekleşen Davranış:** `u1`, `pol_3` ve `pol_4` için istek attığında HTTP `200 OK` ile `u2`'ye (`ownerUserId: "u2"`) ait `clm_7` ve `clm_6` kayıtlarının tüm detaylarını (`amount`, `status`, `description`) almaktadır. Tersi yönde `u2` de `GET /claims?policyId=pol_1` ile `u1`'e ait `clm_1` ve `clm_2` kayıtlarını görebilmektedir.
- **Tekrar Üretim Adımları:**
  1. İstek gönder: `GET http://localhost:4108/claims?policyId=pol_4`
  2. Başlık ekle: `Authorization: Bearer tok_user1_ayse` (`pol_4` kullanıcısı `u2`'ye aittir)
  3. **Gözlenen Yanıt (`HTTP 200`):**
     ```json
     {
       "data": [
         {
           "id": "clm_6",
           "policyId": "pol_4",
           "ownerUserId": "u2",
           "amount": 5000,
           "status": "approved",
           "description": "Çarpma hasarı",
           "createdAt": "2026-05-18T10:20:00Z"
         }
       ],
       "meta": {"page": 1, "pageSize": 20, "total": 1}
     }
     ```
  4. Tersi doğrulama: `GET http://localhost:4108/claims?policyId=pol_1` (`Authorization: Bearer tok_user2_mehmet`) → `HTTP 200` ve `u1`'e ait `clm_1`, `clm_2` döner.
- **Kanıt:** `test-kayitlari.md` → `P1-CLM-LIST-u1-other_u2_pol3`, `P1-CLM-LIST-u1-other_u2_pol4`, `P1-CLM-LIST-u2-other_u1_pol1` (not: `GET /claims/clm_6` ise `403` dönmektedir: `P1-CLM-GET-u1-clm_6`).

---

### BULGU-03 — `PATCH /policies/{id}` ile salt okunur `status` alanı güncellenebiliyor ve enum dışı değer kabul ediliyor (Mass Assignment / BOPLA)
- **Önem Derecesi:** Kritik *(Güvenlik ve İş Kuralı İhlali — OWASP API3: Broken Object Property Level Authorization)*
- **Kök Neden Türü:** Uygulama kusuru (`status` alanı salt okunur filtrelemesinden ve enum doğrulamasından kaçmış)
- **Etkilenen Uç:** `PATCH /policies/{id}`
- **Sözleşme / İş Kuralı Atfı:** `openapi.yaml` → `paths./policies/{id}.patch.description` (*"Poliçe sahibi YALNIZCA `holderName` ve `agentName` alanlarını güncelleyebilir. `premium`, `coverageLimit`, `status`, `ownerUserId`, `policyNumber`, `coverageType` alanları salt okunurdur ve istek gövdesiyle DEĞİŞTİRİLEMEZ; bu alanlar gövdede gönderilse bile yok sayılmalıdır. Poliçenin durumu (`status`) yalnızca iç iş süreçleriyle değişir."*) ve `Policy.status` (`enum: [active, cancelled, expired, pending]`).
- **Beklenen Davranış:** `PATCH` gövdesinde `status` gönderildiğinde yok sayılmalı (ya da reddedilmeli), poliçenin mevcut `status` değeri değişmemelidir.
- **Gerçekleşen Davranış:** `premium`, `coverageLimit`, `ownerUserId`, `policyNumber`, `coverageType`, `holderTckn`, `startDate`, `endDate` alanları yok sayılırken, **`status` alanı doğrudan kabul edilip kalıcı olarak güncellenmektedir**. Poliçe sahibi kendi poliçesini `"cancelled"`, `"pending"`, `"active"` veya şema dışı keyfi bir değer olan `"gecersiz_durum"` durumuna çekebilmektedir.
- **Tekrar Üretim Adımları:**
  1. İstek gönder: `PATCH http://localhost:4108/policies/pol_5`
  2. Başlıklar: `Authorization: Bearer tok_user1_ayse`, `Content-Type: application/json`
  3. Gövde: `{"holderName": "Ayşe Yılmaz", "premium": 5, "coverageLimit": 888888, "status": "pending"}`
  4. **Gözlenen Yanıt (`HTTP 200`):** `premium` (`1800`) ve `coverageLimit` (`75000`) değişmezken **`"status": "pending"`** olarak güncellenir; ardından atılan `GET /policies/pol_5` de `"status": "pending"` döner.
  5. Enum dışı değer testi: `PATCH /policies/pol_5` gövdesi `{"status": "gecersiz_durum"}` → `HTTP 200` ve `"status": "gecersiz_durum"`.
  6. Test sonrası temizlik: `{"status": "active"}` gönderilerek `pol_5` tekrar `"active"` yapılabilmiştir (kullanıcı kendi poliçesini yeniden aktifleştirebilmektedir).
- **Kanıt:** `test-kayitlari.md` → `P2A-RO-STATUS`, `P2A-RO-MIXED`, `P2A-CHECK-pol_5`, `P5-PATCH-STATUS-INVALID`, `P5-PATCH-STATUS-ACTIVE`.

---

### BULGU-04 — `POST /claims` teminat limitini (`coverageLimit`) aşan, `1` TL altındaki ve taşan (`1e309`) tutarları reddetmiyor
- **Önem Derecesi:** Kritik *(Finansal iş kuralı ihlali ve veri bozulması)*
- **Kök Neden Türü:** Uygulama kusuru (iş kuralı ve sayısal aralık doğrulamasının eksikliği)
- **Etkilenen Uç:** `POST /claims`
- **Sözleşme / İş Kuralı Atfı:**
  - `openapi.yaml` → `paths./claims.post.description` & `responses.422`: *"İş kuralı: Bir hasar talebinin tutarı (`amount`), ilgili poliçenin teminat limitini (`coverageLimit`) AŞAMAZ. Aşan istekler 422 ile reddedilmelidir."*
  - `Claim` / `ClaimCreate`: `amount` için `minimum: 1` (*"1'den küçük olamaz ve poliçenin teminat limitini aşamaz"*).
- **Beklenen Davranış:**
  - `amount > coverageLimit` (ör. `pol_1` limiti `50000` iken `50000.01` veya `50001`) için HTTP `422` dönülmelidir.
  - `amount < 1` (`-100`, `0`, `0.99`) ve sonlu olmayan (`1e309` → JS `Infinity`) değerler HTTP `400` ile reddedilmelidir.
- **Gerçekleşen Davranış:** Aşağıdaki geçersiz tutarların tamamı HTTP `200` ile kabul edilerek veritabanına kaydedilmektedir:
  - Üst sınır aşımı: `pol_1` (`coverageLimit: 50000`) için `50000.01` (`clm_15`) ve `50001` (`clm_14`); `pol_5` (`coverageLimit: 75000`) için `999999` (`clm_24`) kabul edilmiştir. (Ek not: `pol_2` limiti `100000` iken mevcut `3000+2000` üzerine `96000` de kabul edilmektedir — kümülatif kontrol de yoktur.)
  - Alt sınır ihlali: `amount: -100` (`clm_10`), `amount: 0` (`clm_11`), `amount: 0.99` (`clm_12`) kabul edilmiştir.
  - Taşan sayı: `{"policyId": "pol_5", "amount": 1e309}` gönderildiğinde `Infinity` JSON serileştirmesiyle **`"amount": null`** (`clm_38`) olarak kaydedilmiştir.
- **Tekrar Üretim Adımları:**
  1. İstek gönder: `POST http://localhost:4108/claims`
  2. Başlıklar: `Authorization: Bearer tok_user1_ayse`, `Content-Type: application/json`
  3. **Üst sınır dışı gövde:** `{"policyId": "pol_1", "amount": 50000.01, "description": "limit+0.01"}`
     - **Gözlenen Yanıt (`HTTP 200` — beklenen `422`):** `{"id": "clm_15", "policyId": "pol_1", "ownerUserId": "u1", "amount": 50000.01, "status": "submitted", ...}` (karşılaştırma: `amount: 50000` geçerli sınırda da `200` ile `clm_16` oluşmuştur).
  4. **Alt sınır dışı gövde:** `{"policyId": "pol_1", "amount": -100, "description": "negatif"}` (veya `amount: 0`, `amount: 0.99`)
     - **Gözlenen Yanıt (`HTTP 200` — beklenen `400`):** `{"id": "clm_10", "policyId": "pol_1", "ownerUserId": "u1", "amount": -100, "status": "submitted", ...}` (karşılaştırma: `amount: 1` geçerli sınırda `clm_13` oluşmuştur).
  5. **Sayısal taşma gövde:** `{"policyId": "pol_5", "amount": 1e309}`
     - **Gözlenen Yanıt (`HTTP 200`):** `{"id": "clm_38", ..., "amount": null, ...}`
- **Kanıt:** `test-kayitlari.md` → `P2B-AMT-OVER-LIMIT-0_01`, `P2B-AMT-OVER-LIMIT-1`, `P2B-AMT-AT-LIMIT`, `P2B-AMT-CUMUL-CHECK`, `P2B-IDEM-FAIL-FIRST`, `P2B-AMT-NEG`, `P2B-AMT-ZERO`, `P2B-AMT-0_99`, `P2B-AMT-1`, `P4-CLM-1E309`.

---

### BULGU-05 — `POST /claims` `Idempotency-Key` başlığını yok sayıyor; tekrarlı ve eşzamanlı isteklerde mükerrer kayıt oluşuyor
- **Önem Derecesi:** Yüksek *(Finansal / operasyonel mükerrer kayıt riski)*
- **Kök Neden Türü:** Uygulama kusuru (`Idempotency-Key` desteğinin uygulanmamış olması)
- **Etkilenen Uç:** `POST /claims` (`Idempotency-Key` başlığı)
- **Sözleşme / İş Kuralı Atfı:** `openapi.yaml` → `paths./claims.post.description`: *"Idempotency (tekrar koruması): İstek `Idempotency-Key` başlığı ile gönderilirse, aynı anahtarla yapılan tekrar istekleri YENİ kayıt OLUŞTURMAMALI, ilk oluşturulan kaydı aynen döndürmelidir."*
- **Beklenen Davranış:** Aynı `Idempotency-Key` değeriyle tekrarlanan ardışık veya paralel `POST /claims` istekleri yeni bir hasar kaydı üretmemeli, ilk oluşan kaydın yanıtını döndürmelidir.
- **Gerçekleşen Davranış:** Aynı kullanıcı ve aynı `Idempotency-Key` ile ardışık gönderilen 2 özdeş istek iki ayrı hasar kaydı (`clm_20` ve `clm_21`) üretmiştir. Paralel gönderilen 3 eşzamanlı istek de 3 ayrı kayıt (`clm_26`, `clm_27`, `clm_28`) oluşturmuştur.
- **Tekrar Üretim Adımları:**
  1. İstek 1: `POST http://localhost:4108/claims`
     - Başlıklar: `Authorization: Bearer tok_user1_ayse`, `Idempotency-Key: idem-key-101`, `Content-Type: application/json`
     - Gövde: `{"policyId": "pol_5", "amount": 250, "description": "Idem 1"}`
     - **Yanıt 1 (`HTTP 200`):** `"id": "clm_20"`
  2. İstek 2 (birebir aynı istek ve aynı `Idempotency-Key` tekrar gönderilir):
     - **Yanıt 2 (`HTTP 200`):** `"id": "clm_21"` (yeni kayıt oluşturuldu).
  3. Eşzamanlı 3 paralel istek (`Idempotency-Key: idem-race-202`): `clm_26`, `clm_27`, `clm_28` olarak 3 ayrı kayıt oluşturuldu.
- **Kanıt:** `test-kayitlari.md` → `P2B-IDEM-1`, `P2B-IDEM-2-REPEAT`, `P2B-IDEM-RACE-1`, `P2B-IDEM-RACE-2`, `P2B-IDEM-RACE-3`.

---

### BULGU-06 — Bozuk JSON gövdesinde sunucu dosya yolu ve yığın izi (stack trace) dışarı sızıyor
- **Önem Derecesi:** Yüksek *(Güvenlik / Bilgi İfşası — CWE-209)*
- **Kök Neden Türü:** Uygulama kusuru (yakalanan JSON parse hatasının ham `stack` ve `detail` alanlarının yanıtla dönülmesi)
- **Etkilenen Uçlar:** `PATCH /policies/{id}`, `POST /claims`
- **Sözleşme / İş Kuralı Atfı:** `openapi.yaml` → `Error` şeması (`{error, message?}`) ve güvenlik kuralı (beklenmedik/kötü girdilerde iç yapı/hata detayı sızdırılmamalıdır).
- **Beklenen Davranış:** Geçersiz JSON gövdesinde yalnızca güvenli bir `400` hata mesajı (`{"error": "Geçersiz JSON", "message": "..."}`) dönülmeli, sunucu dosya yolları ve stack trace kesinlikle dönülmemelidir.
- **Gerçekleşen Davranış:** Kimliği doğrulanmış ve yetkili bir kullanıcı geçersiz JSON (`{bad json` veya `{"policyId": "pol_5", "amount": NaN}`) gönderdiğinde HTTP `400` gövdesinde `detail` ve sunucunun gerçek dosya yolunu ile çalışma zamanı satır numaralarını içeren `stack` alanı dönmektedir. *(Not: Kimliksiz `401` ve yetkisiz `403` kontrolleri JSON ayrıştırmadan önce çalıştığı için bu sızıntı yalnızca kimliği doğrulanmış/yetkili isteklerde tetiklenmektedir — bkz. `P5-UNAUTH-MALFORMED-POST`, `P5-BOLA-MALFORMED-PATCH`.)*
- **Tekrar Üretim Adımları:**
  1. İstek gönder: `PATCH http://localhost:4108/policies/pol_5` (veya `POST http://localhost:4108/claims`)
  2. Başlıklar: `Authorization: Bearer tok_user1_ayse`, `Content-Type: application/json`
  3. Gövde (ham metin): `{bad json`
  4. **Gözlenen Yanıt (`HTTP 400`):**
     ```json
     {
       "error": "Geçersiz JSON",
       "detail": "Expected property name or '}' in JSON at position 1 (line 1 column 2)",
       "stack": "SyntaxError: Expected property name or '}' in JSON at position 1 (line 1 column 2)\n    at JSON.parse (<anonymous>)\n    at Server.<anonymous> (C:\\eval\\servers\\R13\\server.js:155:27)\n    at process.processTicksAndRejections (node:internal/process/task_queues:104:5)"
     }
     ```
- **Kanıt:** `test-kayitlari.md` → `P2A-MALFORMED-JSON`, `P2B-MALFORMED-JSON`, `P4-CLM-NAN`.

---

### BULGU-07 — `Claim` yanıtlarında sözleşmede zorunlu olan `claimNumber` alanı eksik
- **Önem Derecesi:** Yüksek *(Sözleşme / Şema Uyumsuzluğu — Kırıcı API Sözleşme İhlali)*
- **Etkilenen Uçlar:** `GET /claims`, `GET /claims/{id}`, `POST /claims`
- **Sözleşme / İş Kuralı Atfı:** `openapi.yaml` → `components.schemas.Claim` (satır 354–369): `required` listesi `claimNumber` alanını zorunlu kılar (`claimNumber: { type: string, examples: ['CLM-2026-0001'] }`).
- **Beklenen Davranış:** Gerek listeleme/detay gerekse oluşturma yanıtlarındaki her `Claim` nesnesinde `claimNumber` string alanı bulunmalıdır.
- **Gerçekleşen Davranış:** Hem başlangıç verilerindeki tüm kayıtlarda (`clm_1`..`clm_7`), hem de `POST /claims` ile yeni üretilen tüm kayıtlarda (`clm_8`..`clm_39`) `claimNumber` alanı tamamen eksiktir.
- **Tekrar Üretim Adımları:**
  1. İstek gönder: `GET http://localhost:4108/claims/clm_1`
  2. Başlık: `Authorization: Bearer tok_user1_ayse`
  3. **Gözlenen Yanıt (`HTTP 200`):**
     ```json
     {
       "id": "clm_1",
       "policyId": "pol_1",
       "ownerUserId": "u1",
       "amount": 12000,
       "status": "submitted",
       "description": "Çarpma hasarı",
       "createdAt": "2026-05-02T09:00:00Z"
     }
     ```
     (`claimNumber` alanı yok. Aynı durum `GET /claims` ve `POST /claims` yanıtlarında da gözlenmiştir.)
- **Kanıt:** `test-kayitlari.md` → `P1-CLM-LIST-u1-all_u1`, `P1-CLM-GET-u1-clm_1`, `P2B-AMT-1`, `P3-GET-CLM8`.

---

### BULGU-08 — `GET /claims` sayfalama çıktısındaki `meta.total` tüm kayıt sayısını değil geçerli sayfadaki kayıt sayısını dönüyor
- **Önem Derecesi:** Yüksek *(İşlevsel hata ve açık sözleşme ihlali)*
- **Kök Neden Türü:** Uygulama kusuru (`total` hesabı sayfalama dilimlemesinden sonra yapılıyor)
- **Etkilenen Uç:** `GET /claims`
- **Sözleşme / İş Kuralı Atfı:** `openapi.yaml` → `paths./claims.get.description` (satır 132–134) ve `PageMeta.total` (satır 400–402): *"Yanıttaki `meta.total` alanı, sayfalama uygulanmadan önceki TOPLAM (tüm sayfalardaki) kayıt sayısını belirtir; yalnızca geçerli sayfadaki kayıt sayısını değil."*
- **Beklenen Davranış:** `u1` toplam 5 hasar kaydına sahipken `page=1&pageSize=2` veya `page=3&pageSize=2` ya da boş sayfa `page=4&pageSize=2` istendiğinde tüm sayfalarda `meta.total: 5` dönmelidir.
- **Gerçekleşen Davranış:** `meta.total` her zaman yalnızca o sayfada dönen `data.length` değerine eşit dönmektedir (`page=1` → `2`, `page=3` → `1`, `page=4` → `0`). Aynı hata `admin` (7 kayıt varken `page=1&pageSize=3` için `total: 3`), `u2` (3 kayıt varken `page=1&pageSize=2` için `total: 2`) ve `policyId=pol_1` filtresinde (2 kayıt varken `page=1&pageSize=1` için `total: 1`) de doğrulanmıştır.
- **Tekrar Üretim Adımları:**
  1. İstek gönder: `GET http://localhost:4108/claims?page=1&pageSize=2` (`u1`'in toplam 5 kaydı varken)
  2. Başlık: `Authorization: Bearer tok_user1_ayse`
  3. **Gözlenen Yanıt (`HTTP 200`):** `data` içinde 2 kayıt (`clm_1`, `clm_2`) ve `meta: {"page": 1, "pageSize": 2, "total": 2}` (beklenen `total: 5`).
  4. `GET http://localhost:4108/claims?page=4&pageSize=2` → `data: []` ve `meta: {"page": 4, "pageSize": 2, "total": 0}` (beklenen `total: 5`).
- **Kanıt:** `test-kayitlari.md` → `P1-CLM-LIST-u1-p1_s2`, `P1-CLM-LIST-u1-p3_s2`, `P1-CLM-LIST-u1-p4_s2_empty`, `P1-CLM-LIST-u1-own_pol1_p1_s1`, `P1-CLM-LIST-admin-admin_p1_s3`, `P3-U2-PAGE1-SIZE2`.

---

### BULGU-09 — `POST /claims` başarılı oluşturma işleminde HTTP `201` yerine `200` durum kodu dönüyor
- **Önem Derecesi:** Orta *(Sözleşme uyumsuzluğu)*
- **Kök Neden Türü:** Uygulama kusuru
- **Etkilenen Uç:** `POST /claims`
- **Sözleşme / İş Kuralı Atfı:** `openapi.yaml` → `paths./claims.post.responses`: Yeni hasar talebi oluşturulduğunda HTTP **`201`** (*"Oluşturulan hasar talebi"*) dönmelidir; `200` yanıtı sözleşmede tanımlı değildir.
- **Beklenen Davranış:** Geçerli `POST /claims` isteğinde HTTP `201 Created` dönülmelidir.
- **Gerçekleşen Davranış:** Tüm başarılı `POST /claims` istekleri HTTP `200 OK` durum kodu ile yanıtlanmaktadır.
- **Tekrar Üretim Adımları:**
  1. İstek gönder: `POST http://localhost:4108/claims`
  2. Başlıklar: `Authorization: Bearer tok_user1_ayse`, `Content-Type: application/json`
  3. Gövde: `{"policyId": "pol_1", "amount": 1, "description": "min sınır 1"}`
  4. **Gözlenen Yanıt:** HTTP **`200`** (beklenen `201`).
- **Kanıt:** `test-kayitlari.md` → `P2B-AMT-1`, `P2B-NOIDEM-1`, `P4-CLM-FLOAT`.

---

### BULGU-10 — `GET /claims` sayfalama parametreleri doğrulanmıyor; `pageSize=-1` son kaydı kesiyor, sayı dışı değerler `PageMeta` şemasını (`null`) bozuyor
- **Önem Derecesi:** Orta *(Girdi doğrulama eksikliği ve şema/veri hatası)*
- **Kök Neden Türü:** Uygulama kusuru (eksik sorgu parametresi doğrulaması ve negatif indeksli `slice`)
- **Etkilenen Uç:** `GET /claims` (`page`, `pageSize` sorgu parametreleri)
- **Sözleşme / İş Kuralı Atfı:** `openapi.yaml` → `paths./claims.get.parameters`: `page` (`integer, minimum: 1, default: 1`), `pageSize` (`integer, minimum: 1, maximum: 100, default: 20`) ve `PageMeta` (`page: integer, pageSize: integer`).
- **Beklenen Davranış:** Alt/üst sınır dışındaki (`0`, negatif, `>100`) veya sayısal olmayan (`abc`) `page`/`pageSize` değerleri `400` ile reddedilmeli (ve sözleşmeye `400` yanıtı eklenmeli), kesinlikle `null` `PageMeta` ya da negatif dilimleme üretmemelidir.
- **Gerçekleşen Davranış:**
  - `GET /claims?pageSize=-1` isteğinde hata dönülmek yerine `u1`'de 5 kayıt yerine 4 kayıt, `admin`'de ise 37 kayıt yerine 36 kayıt (`clm_37` hariç) dönmektedir (`Array.slice(0, -1)` davranışı); `meta.pageSize: -1` olarak dönmektedir.
  - `GET /claims?page=abc` → `HTTP 200` ve `meta: {"page": null, "pageSize": 20, "total": 0}` (`PageMeta.page` `integer` olmalıyken `null` döner).
  - `GET /claims?pageSize=abc` → `HTTP 200` ve `meta: {"page": 1, "pageSize": null, "total": 0}` (`PageMeta.pageSize` `integer` olmalıyken `null` döner).
  - `page=0`, `page=-1`, `pageSize=0`, `pageSize=101` değerleri de reddedilmeden `200` ile kabul edilmektedir.
- **Tekrar Üretim Adımları:**
  1. `GET http://localhost:4108/claims?pageSize=-1` (`Authorization: Bearer tok_user1_ayse`) → `HTTP 200`, `data` uzunluğu `4` (`clm_5` eksik), `meta: {"page": 1, "pageSize": -1, "total": 4}`.
  2. `GET http://localhost:4108/claims?page=abc` (`Authorization: Bearer tok_user1_ayse`) → `HTTP 200`, `meta: {"page": null, "pageSize": 20, "total": 0}`.
- **Kanıt:** `test-kayitlari.md` → `P1-CLM-LIST-u1-size_neg1`, `P3-ADMIN-SIZE-NEG1`, `P1-CLM-LIST-u1-page_abc`, `P1-CLM-LIST-u1-size_abc`, `P1-CLM-LIST-u1-page_0`, `P1-CLM-LIST-u1-size_101`.

---

### BULGU-11 — `PATCH /policies/{id}` ve `POST /claims` alan tiplerini ve boş/dizi gövdeleri doğrulamıyor; `Policy` şeması bozuluyor
- **Önem Derecesi:** Orta *(Veri bütünlüğü ve sözleşme şeması ihlali)*
- **Kök Neden Türü:** Uygulama kusuru (tip ve gövde yapısı doğrulaması eksikliği)
- **Etkilenen Uçlar:** `PATCH /policies/{id}`, `POST /claims`
- **Sözleşme / İş Kuralı Atfı:** `openapi.yaml` → `PolicyUpdate` & `Policy` (`holderName: string`, `agentName: ['string', 'null']`), `ClaimCreate` (`policyId: string`, `description: ['string', 'null']`), `responses.400`.
- **Beklenen Davranış:** İstek gövdesi JSON nesnesi olmadığında (`[]`) veya `holderName`, `agentName`, `policyId`, `description` alanları şemada tanımlanan tipler dışında gönderildiğinde `400 BadRequest` dönmelidir.
- **Gerçekleşen Davranış:**
  - `PATCH /policies/pol_5` isteğinde `{"holderName": 12345}`, `{"holderName": null}`, `{"holderName": ""}`, `{"agentName": 12345}`, `{"agentName": true}` ve hatta dizi gövde `[]` HTTP `200` ile kabul edilmektedir. Sayı/boolean/`null` değerler kalıcı olarak kaydedildiği için sonraki `GET /policies/{id}` yanıtları `Policy` şemasını bozar.
  - `POST /claims` isteğinde `{"policyId": "pol_1", "amount": 100, "description": 12345}` gönderildiğinde `400` yerine `200` ile `description: ""` olarak oluşturulmaktadır. Ayrıca `policyId: 123` veya `null` gönderildiğinde `400` (geçersiz tip) yerine `404` (`Poliçe bulunamadı`) dönmektedir (`amount` yanlış tipte `400` dönerken `policyId` için tutarsız davranış).
- **Tekrar Üretim Adımları:**
  1. `PATCH http://localhost:4108/policies/pol_5` (`Authorization: Bearer tok_user1_ayse`), gövde: `{"holderName": 12345}` → `HTTP 200` ve `"holderName": 12345`.
  2. `PATCH http://localhost:4108/policies/pol_5` (`Authorization: Bearer tok_user1_ayse`), gövde: `{"agentName": true}` → `HTTP 200` ve `"agentName": true`.
  3. `POST http://localhost:4108/claims` (`Authorization: Bearer tok_user1_ayse`), gövde: `{"policyId": "pol_1", "amount": 100, "description": 12345}` → `HTTP 200` (`clm_8`, `"description": ""`).
- **Kanıt:** `test-kayitlari.md` → `P2A-HOLDER-INT`, `P2A-HOLDER-NULL`, `P2A-HOLDER-EMPTY`, `P2A-AGENT-INT`, `P2A-AGENT-BOOL`, `P2A-ARRAY-BODY`, `P2B-DESC-INT`, `P2B-POLICYID-INT`.

---

### BULGU-12 — İptal edilmiş (`cancelled`) poliçe için `POST /claims` ile yeni hasar talebi açılabiliyor
- **Önem Derecesi:** Orta *(Sigortacılık iş kuralı ihlali ve sözleşme boşluğu)*
- **Kök Neden Türü:** İş kuralı / sözleşme eksikliği
- **Etkilenen Uç:** `POST /claims`
- **Sözleşme / İş Kuralı Atfı:** Sigortacılık temel iş kuralı (`Policy.status` değerleri: `active`, `cancelled`, `expired`, `pending`). İptal edilmiş (`cancelled`) bir poliçe teminat sağlamadığından yeni hasar talebi açılması reddedilmelidir (`422`), ayrıca bu kural `openapi.yaml` içinde açıkça belgelenmelidir.
- **Beklenen Davranış:** `status: "cancelled"` durumundaki `pol_3` poliçesi için gönderilen yeni `POST /claims` isteği `422` ile reddedilmelidir.
- **Gerçekleşen Davranış:** `pol_3` (`status: "cancelled"`) sahibi `u2` tarafından gönderilen `POST /claims` isteği HTTP `200` ile kabul edilmiş ve `clm_18` (`status: "submitted"`) oluşturulmuştur.
- **Tekrar Üretim Adımları:**
  1. İstek gönder: `POST http://localhost:4108/claims`
  2. Başlıklar: `Authorization: Bearer tok_user2_mehmet`, `Content-Type: application/json`
  3. Gövde: `{"policyId": "pol_3", "amount": 500, "description": "İptal poliçeye hasar talebi"}` (`pol_3` durumu `cancelled`'dır)
  4. **Gözlenen Yanıt (`HTTP 200`):** `{"id": "clm_18", "policyId": "pol_3", "ownerUserId": "u2", "amount": 500, "status": "submitted", ...}`
- **Kanıt:** `test-kayitlari.md` → `P2B-CANCELLED-POLICY`.

---

### BULGU-13 — Yönetici (`admin`) başka kullanıcının poliçesi için `POST /claims` yaptığında `ownerUserId: "admin"` atanıyor (sahiplik tutarsızlığı)
- **Önem Derecesi:** Orta *(Veri bütünlüğü / rol yetkilendirme tutarsızlığı)*
- **Kök Neden Türü:** Uygulama kusuru (`ownerUserId` poliçe sahibinden alınmak yerine oturum açan token'dan alınıyor)
- **Etkilenen Uçlar:** `POST /claims`, `GET /claims`, `GET /claims/{id}`
- **Sözleşme / İş Kuralı Atfı:** `openapi.yaml` → `info.description` (*"Yönetici (role=admin) tüm kaynaklara erişebilir"*) ve `Claim.ownerUserId` (poliçe sahibinin kayıt sahipliği tutarlılığı).
- **Beklenen Davranış:** Yönetici bir poliçe adına hasar talebi oluşturabiliyorsa oluşan talebin `ownerUserId` değeri ilgili poliçenin sahibine (`u2`) ait olmalı (ya da yöneticinin başka kullanıcı poliçesi adına talep açmasına izin verilmiyorsa reddedilmelidir).
- **Gerçekleşen Davranış:** `tok_admin_root` ile `u2`'ye ait `pol_4` için `POST /claims` yapıldığında oluşan `clm_9` kaydına `"ownerUserId": "admin"` atanmıştır. Bunun sonucunda poliçe sahibi `u2`:
  - `GET /claims` listesinde bu hasar kaydını görememekte,
  - `GET /claims/clm_9` isteğinde `403 Erişim engellendi` hatası almakta,
  - buna karşın `GET /claims?policyId=pol_4` (BULGU-02 nedeniyle) bu kaydı görebilmektedir.
- **Tekrar Üretim Adımları:**
  1. `POST http://localhost:4108/claims` (`Authorization: Bearer tok_admin_root`), gövde: `{"policyId": "pol_4", "amount": 500, "description": "Admin claim on pol_4"}` → `HTTP 200`, `"ownerUserId": "admin"`, `"id": "clm_9"`.
  2. `GET http://localhost:4108/claims/clm_9` (`Authorization: Bearer tok_user2_mehmet`) → `HTTP 403` (`"Bu hasar talebine erişim yetkiniz yok."`).
- **Kanıt:** `test-kayitlari.md` → `P2B-ADMIN-ON-POL4`, `P3-U2-GET-CLM9`, `P3-U2-LIST-CLAIMS`, `P2B-CHK-POL4-U2`.

---

### BULGU-14 — OpenAPI sözleşmesinde (`openapi.yaml`) şema çelişkileri ve eksik yanıt/kısıt tanımları var
- **Önem Derecesi:** Düşük *(Sözleşme dokümantasyonu kusuru — tüketiciler belgeye göre entegrasyon yapar)*
- **Kök Neden Türü:** Sözleşme kusuru
- **Etkilenen Kaynak:** `openapi.yaml`
- **Gözlenen Sözleşme Kusurları ve Kanıtları:**
  1. **`additionalProperties: false` çelişkisi:** `PolicyUpdate` (satır 353) ve `ClaimCreate` (satır 393) şemaları `additionalProperties: false` tanımlarken, `PATCH /policies/{id}` açıklaması (satır 96–97) ve `PolicyUpdate.description` (satır 348–349) bilinmeyen/salt okunur alanların *"gönderilse bile yok sayılacağını"* belirtmektedir. Sunucu da ekstra alanları `400` ile reddetmeyip sessizce yok saymaktadır (`P3-PATCH-UNKNOWN-ONLY`, `P3-POST-UNKNOWN-FIELD`).
  2. **Eksik hata yanıtları:** `GET /claims` işleminde `page`/`pageSize` sınırları (`minimum`/`maximum`) ve `policyId` sahiplik kuralı belirtildiği halde `responses` altında `400` ve `403` tanımları yoktur.
  3. **Nullable alan tutarsızlığı:** `Claim.description` ve `ClaimCreate.description` tipi `['string', 'null']` olmasına rağmen `description: null` veya alan gönderilmediğinde sunucu `null` yerine `""` dönmektedir (`P3-CLM-DESC-NULL`, `P3-CLM-DESC-OMIT`).
  4. **Eksik alan kısıtları ve yol örnekleri:** `PolicyUpdate.holderName` için `minLength`/`maxLength`, `POST /claims` `amount` için üst sınır açıklaması dışında şema kısıtı ve `{id}` yol parametreleri için `example` tanımlanmamıştır.

---

## Doğrulanan ve Sorunsuz Çalışan Kontroller (Özet)

Yalancı pozitif raporlamaktan kaçınmak amacıyla aşağıdakilerin doğru çalıştığı testlerle doğrulanmıştır:
- **Sağlık kontrolü:** `GET /health` kimlik doğrulaması olmadan `200 OK` dönmektedir (`P1-HEALTH-ANON`).
- **Kimlik doğrulama (`401`):** Tüm korumalı uçlarda eksik `Authorization`, boş başlık, `Bearer` öneki olmayan token (`Authorization: tok_user1_ayse`), `Basic` şeması, boş `Bearer ` ve geçersiz token istekleri doğru biçimde `401` dönmektedir (`P1-AUTH-*`).
- **Temel BOLA korumaları:** `GET /policies/{id}`, `PATCH /policies/{id}`, `GET /claims/{id}`, `POST /claims` (gövde `policyId`) ve `GET /admin/policies` uçlarında başka kullanıcının kaynağına/yönetici ucuna erişim `403` ile engellenmektedir (`P1-POL-GET-u1-pol_3`, `P2A-BOLA-U1-ON-U2`, `P1-CLM-GET-u1-clm_6`, `P2B-BOLA-U1-ON-POL4`, `P1-ADMIN-u1-/admin/policies`).
- **Diğer salt okunur poliçe alanları:** `PATCH /policies/{id}` içinde `premium`, `coverageLimit`, `ownerUserId`, `policyNumber`, `coverageType`, `holderTckn`, `startDate`, `endDate`, `id` ve `role`/`isAdmin` gönderildiğinde başarıyla yok sayılmaktadır (`P2A-RO-*`, `P5-PATCH-ENDDATE`).
- **Hata/yetki sırası ve enjeksiyon dayanıklılığı:** Kimlik (`401`) ve sahiplik (`403`) denetimleri JSON gövde ayrıştırmasından önce çalışmaktadır (`P5-UNAUTH-MALFORMED-*`, `P5-BOLA-MALFORMED-PATCH`). SQL enjeksiyonu ve XSS dizgileri `500` hatasına veya veritabanı hatası sızıntısına yol açmamıştır (`P2A-SQLI-HOLDER`, `P2B-SQLI-DESC`, `P2B-XSS-DESC`).

## Kapsam Dışı Kalan Alanlar
- Oran sınırlama (rate limiting) ve yük/performans testleri bu oturum kapsamına alınmamıştır.
- Sunucu yeniden başlatma sonrası kalıcılık (`TASK.md` gereği durum bellekte tutulduğundan) test edilmemiştir.
