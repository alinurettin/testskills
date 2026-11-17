# Test Kanıt Kayıtları — Anadolu Güven Sigorta Poliçe & Hasar API

- **Hedef API Adresi:** `http://localhost:4108` (`127.0.0.1:4108` üzerinden koşulmuştur)
- **Sözleşme Referansı:** `openapi.yaml` (OpenAPI 3.1.0, sürüm `1.0.0`)
- **Test Verisi:** Yalnızca kurgusal/sentetik test verileri ve sağlanan test token'ları kullanılmıştır.
- **Toplam Çalıştırılan İstek Sayısı:** 222
- **Durum Kodu Dağılımı:** `HTTP 200`: 132, `HTTP 400`: 12, `HTTP 401`: 42, `HTTP 403`: 16, `HTTP 404`: 18, `HTTP 405`: 2

Bu dosya, `bulgular.md` raporundaki her kusurun dayandığı gerçek HTTP isteklerini, kullanılan token/başlıkları ve gözlenen sunucu yanıtlarını kayıt altına alır.

## 1. Tüm Çalıştırılan İsteklerin Özeti

### Faz 1 — Salt Okunur Keşif, Kimlik Doğrulama, BOLA/BFLA, Sayfalama ve Şema Kontrolleri (107 istek)

| Kayıt ID | Yöntem | Yol & Sorgu | Token / Auth | Ek Başlıklar | İstek Gövdesi | Durum | Yanıt Özeti |
|---|---|---|---|---|---|---|---|
| `P1-HEALTH-ANON` | `GET` | `/health` | (yok) | — | — | **200** | `{"status": "ok", "service": "anadolu-guven-sigorta-api"}` |
| `P1-AUTH-NOAUTH-/policies` | `GET` | `/policies` | (yok) | — | — | **401** | `{"error": "Yetkisiz", "message": "Geçerli bir bearer token gerekli."}` |
| `P1-AUTH-NOAUTH-/policies/pol_1` | `GET` | `/policies/pol_1` | (yok) | — | — | **401** | `{"error": "Yetkisiz", "message": "Geçerli bir bearer token gerekli."}` |
| `P1-AUTH-NOAUTH-/claims` | `GET` | `/claims` | (yok) | — | — | **401** | `{"error": "Yetkisiz", "message": "Geçerli bir bearer token gerekli."}` |
| `P1-AUTH-NOAUTH-/claims/clm_1` | `GET` | `/claims/clm_1` | (yok) | — | — | **401** | `{"error": "Yetkisiz", "message": "Geçerli bir bearer token gerekli."}` |
| `P1-AUTH-NOAUTH-/admin/policies` | `GET` | `/admin/policies` | (yok) | — | — | **401** | `{"error": "Yetkisiz", "message": "Geçerli bir bearer token gerekli."}` |
| `P1-AUTH-NOAUTH-/admin/stats` | `GET` | `/admin/stats` | (yok) | — | — | **401** | `{"error": "Yetkisiz", "message": "Geçerli bir bearer token gerekli."}` |
| `P1-AUTH-EMPTYAUTH-/policies` | `GET` | `/policies` | `` | — | — | **401** | `{"error": "Yetkisiz", "message": "Geçerli bir bearer token gerekli."}` |
| `P1-AUTH-EMPTYAUTH-/policies/pol_1` | `GET` | `/policies/pol_1` | `` | — | — | **401** | `{"error": "Yetkisiz", "message": "Geçerli bir bearer token gerekli."}` |
| `P1-AUTH-EMPTYAUTH-/claims` | `GET` | `/claims` | `` | — | — | **401** | `{"error": "Yetkisiz", "message": "Geçerli bir bearer token gerekli."}` |
| `P1-AUTH-EMPTYAUTH-/claims/clm_1` | `GET` | `/claims/clm_1` | `` | — | — | **401** | `{"error": "Yetkisiz", "message": "Geçerli bir bearer token gerekli."}` |
| `P1-AUTH-EMPTYAUTH-/admin/policies` | `GET` | `/admin/policies` | `` | — | — | **401** | `{"error": "Yetkisiz", "message": "Geçerli bir bearer token gerekli."}` |
| `P1-AUTH-EMPTYAUTH-/admin/stats` | `GET` | `/admin/stats` | `` | — | — | **401** | `{"error": "Yetkisiz", "message": "Geçerli bir bearer token gerekli."}` |
| `P1-AUTH-NOBEARER-/policies` | `GET` | `/policies` | `tok_user1_ayse` | — | — | **401** | `{"error": "Yetkisiz", "message": "Geçerli bir bearer token gerekli."}` |
| `P1-AUTH-NOBEARER-/policies/pol_1` | `GET` | `/policies/pol_1` | `tok_user1_ayse` | — | — | **401** | `{"error": "Yetkisiz", "message": "Geçerli bir bearer token gerekli."}` |
| `P1-AUTH-NOBEARER-/claims` | `GET` | `/claims` | `tok_user1_ayse` | — | — | **401** | `{"error": "Yetkisiz", "message": "Geçerli bir bearer token gerekli."}` |
| `P1-AUTH-NOBEARER-/claims/clm_1` | `GET` | `/claims/clm_1` | `tok_user1_ayse` | — | — | **401** | `{"error": "Yetkisiz", "message": "Geçerli bir bearer token gerekli."}` |
| `P1-AUTH-NOBEARER-/admin/policies` | `GET` | `/admin/policies` | `tok_user1_ayse` | — | — | **401** | `{"error": "Yetkisiz", "message": "Geçerli bir bearer token gerekli."}` |
| `P1-AUTH-NOBEARER-/admin/stats` | `GET` | `/admin/stats` | `tok_user1_ayse` | — | — | **401** | `{"error": "Yetkisiz", "message": "Geçerli bir bearer token gerekli."}` |
| `P1-AUTH-BASIC-/policies` | `GET` | `/policies` | `Basic dTE6dDE=` | — | — | **401** | `{"error": "Yetkisiz", "message": "Geçerli bir bearer token gerekli."}` |
| `P1-AUTH-BASIC-/policies/pol_1` | `GET` | `/policies/pol_1` | `Basic dTE6dDE=` | — | — | **401** | `{"error": "Yetkisiz", "message": "Geçerli bir bearer token gerekli."}` |
| `P1-AUTH-BASIC-/claims` | `GET` | `/claims` | `Basic dTE6dDE=` | — | — | **401** | `{"error": "Yetkisiz", "message": "Geçerli bir bearer token gerekli."}` |
| `P1-AUTH-BASIC-/claims/clm_1` | `GET` | `/claims/clm_1` | `Basic dTE6dDE=` | — | — | **401** | `{"error": "Yetkisiz", "message": "Geçerli bir bearer token gerekli."}` |
| `P1-AUTH-BASIC-/admin/policies` | `GET` | `/admin/policies` | `Basic dTE6dDE=` | — | — | **401** | `{"error": "Yetkisiz", "message": "Geçerli bir bearer token gerekli."}` |
| `P1-AUTH-BASIC-/admin/stats` | `GET` | `/admin/stats` | `Basic dTE6dDE=` | — | — | **401** | `{"error": "Yetkisiz", "message": "Geçerli bir bearer token gerekli."}` |
| `P1-AUTH-BEARER_EMPTY-/policies` | `GET` | `/policies` | `Bearer ` | — | — | **401** | `{"error": "Yetkisiz", "message": "Geçerli bir bearer token gerekli."}` |
| `P1-AUTH-BEARER_EMPTY-/policies/pol_1` | `GET` | `/policies/pol_1` | `Bearer ` | — | — | **401** | `{"error": "Yetkisiz", "message": "Geçerli bir bearer token gerekli."}` |
| `P1-AUTH-BEARER_EMPTY-/claims` | `GET` | `/claims` | `Bearer ` | — | — | **401** | `{"error": "Yetkisiz", "message": "Geçerli bir bearer token gerekli."}` |
| `P1-AUTH-BEARER_EMPTY-/claims/clm_1` | `GET` | `/claims/clm_1` | `Bearer ` | — | — | **401** | `{"error": "Yetkisiz", "message": "Geçerli bir bearer token gerekli."}` |
| `P1-AUTH-BEARER_EMPTY-/admin/policies` | `GET` | `/admin/policies` | `Bearer ` | — | — | **401** | `{"error": "Yetkisiz", "message": "Geçerli bir bearer token gerekli."}` |
| `P1-AUTH-BEARER_EMPTY-/admin/stats` | `GET` | `/admin/stats` | `Bearer ` | — | — | **401** | `{"error": "Yetkisiz", "message": "Geçerli bir bearer token gerekli."}` |
| `P1-AUTH-BEARER_LOWER-/policies` | `GET` | `/policies` | `bearer tok_user1_ayse` | — | — | **200** | `[{"id": "pol_1", "policyNumber": "POL-2026-0001", "ownerUserId": "u1", "holderName": "Ayşe Yılmaz", "holderTckn": "11111111110"...` |
| `P1-AUTH-BEARER_LOWER-/policies/pol_1` | `GET` | `/policies/pol_1` | `bearer tok_user1_ayse` | — | — | **200** | `{"id": "pol_1", "policyNumber": "POL-2026-0001", "ownerUserId": "u1", "holderName": "Ayşe Yılmaz", "holderTckn": "11111111110",...` |
| `P1-AUTH-BEARER_LOWER-/claims` | `GET` | `/claims` | `bearer tok_user1_ayse` | — | — | **200** | `{"data": [{"id": "clm_1", "policyId": "pol_1", "ownerUserId": "u1", "amount": 12000, "status": "submitted", "description": "Çar...` |
| `P1-AUTH-BEARER_LOWER-/claims/clm_1` | `GET` | `/claims/clm_1` | `bearer tok_user1_ayse` | — | — | **200** | `{"id": "clm_1", "policyId": "pol_1", "ownerUserId": "u1", "amount": 12000, "status": "submitted", "description": "Çarpma hasarı...` |
| `P1-AUTH-BEARER_LOWER-/admin/policies` | `GET` | `/admin/policies` | `bearer tok_user1_ayse` | — | — | **403** | `{"error": "Erişim engellendi", "message": "Yönetici yetkisi gerekli."}` |
| `P1-AUTH-BEARER_LOWER-/admin/stats` | `GET` | `/admin/stats` | `bearer tok_user1_ayse` | — | — | **200** | `{"totalPolicies": 5, "totalClaims": 7, "totalPremium": 9800}` |
| `P1-AUTH-BEARER_2SPACE-/policies` | `GET` | `/policies` | `Bearer  tok_user1_ayse` | — | — | **200** | `[{"id": "pol_1", "policyNumber": "POL-2026-0001", "ownerUserId": "u1", "holderName": "Ayşe Yılmaz", "holderTckn": "11111111110"...` |
| `P1-AUTH-BEARER_2SPACE-/policies/pol_1` | `GET` | `/policies/pol_1` | `Bearer  tok_user1_ayse` | — | — | **200** | `{"id": "pol_1", "policyNumber": "POL-2026-0001", "ownerUserId": "u1", "holderName": "Ayşe Yılmaz", "holderTckn": "11111111110",...` |
| `P1-AUTH-BEARER_2SPACE-/claims` | `GET` | `/claims` | `Bearer  tok_user1_ayse` | — | — | **200** | `{"data": [{"id": "clm_1", "policyId": "pol_1", "ownerUserId": "u1", "amount": 12000, "status": "submitted", "description": "Çar...` |
| `P1-AUTH-BEARER_2SPACE-/claims/clm_1` | `GET` | `/claims/clm_1` | `Bearer  tok_user1_ayse` | — | — | **200** | `{"id": "clm_1", "policyId": "pol_1", "ownerUserId": "u1", "amount": 12000, "status": "submitted", "description": "Çarpma hasarı...` |
| `P1-AUTH-BEARER_2SPACE-/admin/policies` | `GET` | `/admin/policies` | `Bearer  tok_user1_ayse` | — | — | **403** | `{"error": "Erişim engellendi", "message": "Yönetici yetkisi gerekli."}` |
| `P1-AUTH-BEARER_2SPACE-/admin/stats` | `GET` | `/admin/stats` | `Bearer  tok_user1_ayse` | — | — | **200** | `{"totalPolicies": 5, "totalClaims": 7, "totalPremium": 9800}` |
| `P1-AUTH-INVALID_TOK-/policies` | `GET` | `/policies` | `Bearer tok_gecersiz_999` | — | — | **401** | `{"error": "Yetkisiz", "message": "Geçerli bir bearer token gerekli."}` |
| `P1-AUTH-INVALID_TOK-/policies/pol_1` | `GET` | `/policies/pol_1` | `Bearer tok_gecersiz_999` | — | — | **401** | `{"error": "Yetkisiz", "message": "Geçerli bir bearer token gerekli."}` |
| `P1-AUTH-INVALID_TOK-/claims` | `GET` | `/claims` | `Bearer tok_gecersiz_999` | — | — | **401** | `{"error": "Yetkisiz", "message": "Geçerli bir bearer token gerekli."}` |
| `P1-AUTH-INVALID_TOK-/claims/clm_1` | `GET` | `/claims/clm_1` | `Bearer tok_gecersiz_999` | — | — | **401** | `{"error": "Yetkisiz", "message": "Geçerli bir bearer token gerekli."}` |
| `P1-AUTH-INVALID_TOK-/admin/policies` | `GET` | `/admin/policies` | `Bearer tok_gecersiz_999` | — | — | **401** | `{"error": "Yetkisiz", "message": "Geçerli bir bearer token gerekli."}` |
| `P1-AUTH-INVALID_TOK-/admin/stats` | `GET` | `/admin/stats` | `Bearer tok_gecersiz_999` | — | — | **401** | `{"error": "Yetkisiz", "message": "Geçerli bir bearer token gerekli."}` |
| `P1-POL-LIST-u1` | `GET` | `/policies` | tok_user1_ayse (u1) | — | — | **200** | `[{"id": "pol_1", "policyNumber": "POL-2026-0001", "ownerUserId": "u1", "holderName": "Ayşe Yılmaz", "holderTckn": "11111111110"...` |
| `P1-POL-LIST-u2` | `GET` | `/policies` | tok_user2_mehmet (u2) | — | — | **200** | `[{"id": "pol_3", "policyNumber": "POL-2026-0003", "ownerUserId": "u2", "holderName": "Mehmet Demir", "holderTckn": "22222222220...` |
| `P1-POL-LIST-admin` | `GET` | `/policies` | tok_admin_root (admin) | — | — | **200** | `[{"id": "pol_1", "policyNumber": "POL-2026-0001", "ownerUserId": "u1", "holderName": "Ayşe Yılmaz", "holderTckn": "11111111110"...` |
| `P1-POL-GET-u1-pol_1` | `GET` | `/policies/pol_1` | tok_user1_ayse (u1) | — | — | **200** | `{"id": "pol_1", "policyNumber": "POL-2026-0001", "ownerUserId": "u1", "holderName": "Ayşe Yılmaz", "holderTckn": "11111111110",...` |
| `P1-POL-GET-u1-pol_3` | `GET` | `/policies/pol_3` | tok_user1_ayse (u1) | — | — | **403** | `{"error": "Erişim engellendi", "message": "Bu poliçeye erişim yetkiniz yok."}` |
| `P1-POL-GET-u1-pol_4` | `GET` | `/policies/pol_4` | tok_user1_ayse (u1) | — | — | **403** | `{"error": "Erişim engellendi", "message": "Bu poliçeye erişim yetkiniz yok."}` |
| `P1-POL-GET-u1-pol_999` | `GET` | `/policies/pol_999` | tok_user1_ayse (u1) | — | — | **404** | `{"error": "Bulunamadı", "message": "Poliçe bulunamadı."}` |
| `P1-POL-GET-u2-pol_3` | `GET` | `/policies/pol_3` | tok_user2_mehmet (u2) | — | — | **200** | `{"id": "pol_3", "policyNumber": "POL-2026-0003", "ownerUserId": "u2", "holderName": "Mehmet Demir", "holderTckn": "22222222220"...` |
| `P1-POL-GET-u2-pol_1` | `GET` | `/policies/pol_1` | tok_user2_mehmet (u2) | — | — | **403** | `{"error": "Erişim engellendi", "message": "Bu poliçeye erişim yetkiniz yok."}` |
| `P1-POL-GET-u2-pol_999` | `GET` | `/policies/pol_999` | tok_user2_mehmet (u2) | — | — | **404** | `{"error": "Bulunamadı", "message": "Poliçe bulunamadı."}` |
| `P1-POL-GET-admin-pol_1` | `GET` | `/policies/pol_1` | tok_admin_root (admin) | — | — | **200** | `{"id": "pol_1", "policyNumber": "POL-2026-0001", "ownerUserId": "u1", "holderName": "Ayşe Yılmaz", "holderTckn": "11111111110",...` |
| `P1-POL-GET-admin-pol_3` | `GET` | `/policies/pol_3` | tok_admin_root (admin) | — | — | **200** | `{"id": "pol_3", "policyNumber": "POL-2026-0003", "ownerUserId": "u2", "holderName": "Mehmet Demir", "holderTckn": "22222222220"...` |
| `P1-POL-GET-admin-pol_999` | `GET` | `/policies/pol_999` | tok_admin_root (admin) | — | — | **404** | `{"error": "Bulunamadı", "message": "Poliçe bulunamadı."}` |
| `P1-CLM-LIST-u1-all_u1` | `GET` | `/claims` | tok_user1_ayse (u1) | — | — | **200** | `{"data": [{"id": "clm_1", "policyId": "pol_1", "ownerUserId": "u1", "amount": 12000, "status": "submitted", "description": "Çar...` |
| `P1-CLM-LIST-u1-p1_s2` | `GET` | `/claims?page=1&pageSize=2` | tok_user1_ayse (u1) | — | — | **200** | `{"data": [{"id": "clm_1", "policyId": "pol_1", "ownerUserId": "u1", "amount": 12000, "status": "submitted", "description": "Çar...` |
| `P1-CLM-LIST-u1-p2_s2` | `GET` | `/claims?page=2&pageSize=2` | tok_user1_ayse (u1) | — | — | **200** | `{"data": [{"id": "clm_3", "policyId": "pol_2", "ownerUserId": "u1", "amount": 3000, "status": "approved", "description": "Su ba...` |
| `P1-CLM-LIST-u1-p3_s2` | `GET` | `/claims?page=3&pageSize=2` | tok_user1_ayse (u1) | — | — | **200** | `{"data": [{"id": "clm_5", "policyId": "pol_2", "ownerUserId": "u1", "amount": 2000, "status": "submitted", "description": "Hırs...` |
| `P1-CLM-LIST-u1-p4_s2_empty` | `GET` | `/claims?page=4&pageSize=2` | tok_user1_ayse (u1) | — | — | **200** | `{"data": [], "meta": {"page": 4, "pageSize": 2, "total": 0}}` |
| `P1-CLM-LIST-u1-own_pol1` | `GET` | `/claims?policyId=pol_1` | tok_user1_ayse (u1) | — | — | **200** | `{"data": [{"id": "clm_1", "policyId": "pol_1", "ownerUserId": "u1", "amount": 12000, "status": "submitted", "description": "Çar...` |
| `P1-CLM-LIST-u1-own_pol1_p1_s1` | `GET` | `/claims?policyId=pol_1&page=1&pageSize=1` | tok_user1_ayse (u1) | — | — | **200** | `{"data": [{"id": "clm_1", "policyId": "pol_1", "ownerUserId": "u1", "amount": 12000, "status": "submitted", "description": "Çar...` |
| `P1-CLM-LIST-u1-other_u2_pol3` | `GET` | `/claims?policyId=pol_3` | tok_user1_ayse (u1) | — | — | **200** | `{"data": [{"id": "clm_7", "policyId": "pol_3", "ownerUserId": "u2", "amount": 1000, "status": "rejected", "description": "Muaye...` |
| `P1-CLM-LIST-u1-other_u2_pol4` | `GET` | `/claims?policyId=pol_4` | tok_user1_ayse (u1) | — | — | **200** | `{"data": [{"id": "clm_6", "policyId": "pol_4", "ownerUserId": "u2", "amount": 5000, "status": "approved", "description": "Çarpm...` |
| `P1-CLM-LIST-u1-missing_pol` | `GET` | `/claims?policyId=pol_999` | tok_user1_ayse (u1) | — | — | **200** | `{"data": [], "meta": {"page": 1, "pageSize": 20, "total": 0}}` |
| `P1-CLM-LIST-u2-other_u1_pol1` | `GET` | `/claims?policyId=pol_1` | tok_user2_mehmet (u2) | — | — | **200** | `{"data": [{"id": "clm_1", "policyId": "pol_1", "ownerUserId": "u1", "amount": 12000, "status": "submitted", "description": "Çar...` |
| `P1-CLM-LIST-u2-own_pol4_p1_s1` | `GET` | `/claims?policyId=pol_4&page=1&pageSize=1` | tok_user2_mehmet (u2) | — | — | **200** | `{"data": [{"id": "clm_6", "policyId": "pol_4", "ownerUserId": "u2", "amount": 5000, "status": "approved", "description": "Çarpm...` |
| `P1-CLM-LIST-admin-all_admin` | `GET` | `/claims` | tok_admin_root (admin) | — | — | **200** | `{"data": [{"id": "clm_1", "policyId": "pol_1", "ownerUserId": "u1", "amount": 12000, "status": "submitted", "description": "Çar...` |
| `P1-CLM-LIST-admin-admin_p1_s3` | `GET` | `/claims?page=1&pageSize=3` | tok_admin_root (admin) | — | — | **200** | `{"data": [{"id": "clm_1", "policyId": "pol_1", "ownerUserId": "u1", "amount": 12000, "status": "submitted", "description": "Çar...` |
| `P1-CLM-LIST-admin-admin_p3_s3` | `GET` | `/claims?page=3&pageSize=3` | tok_admin_root (admin) | — | — | **200** | `{"data": [{"id": "clm_7", "policyId": "pol_3", "ownerUserId": "u2", "amount": 1000, "status": "rejected", "description": "Muaye...` |
| `P1-CLM-LIST-admin-admin_pol1` | `GET` | `/claims?policyId=pol_1` | tok_admin_root (admin) | — | — | **200** | `{"data": [{"id": "clm_1", "policyId": "pol_1", "ownerUserId": "u1", "amount": 12000, "status": "submitted", "description": "Çar...` |
| `P1-CLM-LIST-admin-admin_pol3` | `GET` | `/claims?policyId=pol_3` | tok_admin_root (admin) | — | — | **200** | `{"data": [{"id": "clm_7", "policyId": "pol_3", "ownerUserId": "u2", "amount": 1000, "status": "rejected", "description": "Muaye...` |
| `P1-CLM-LIST-u1-page_0` | `GET` | `/claims?page=0` | tok_user1_ayse (u1) | — | — | **200** | `{"data": [], "meta": {"page": 0, "pageSize": 20, "total": 0}}` |
| `P1-CLM-LIST-u1-page_neg1` | `GET` | `/claims?page=-1` | tok_user1_ayse (u1) | — | — | **200** | `{"data": [], "meta": {"page": -1, "pageSize": 20, "total": 0}}` |
| `P1-CLM-LIST-u1-page_abc` | `GET` | `/claims?page=abc` | tok_user1_ayse (u1) | — | — | **200** | `{"data": [], "meta": {"page": null, "pageSize": 20, "total": 0}}` |
| `P1-CLM-LIST-u1-page_float` | `GET` | `/claims?page=1.5` | tok_user1_ayse (u1) | — | — | **200** | `{"data": [{"id": "clm_1", "policyId": "pol_1", "ownerUserId": "u1", "amount": 12000, "status": "submitted", "description": "Çar...` |
| `P1-CLM-LIST-u1-size_0` | `GET` | `/claims?pageSize=0` | tok_user1_ayse (u1) | — | — | **200** | `{"data": [], "meta": {"page": 1, "pageSize": 0, "total": 0}}` |
| `P1-CLM-LIST-u1-size_neg1` | `GET` | `/claims?pageSize=-1` | tok_user1_ayse (u1) | — | — | **200** | `{"data": [{"id": "clm_1", "policyId": "pol_1", "ownerUserId": "u1", "amount": 12000, "status": "submitted", "description": "Çar...` |
| `P1-CLM-LIST-u1-size_100` | `GET` | `/claims?pageSize=100` | tok_user1_ayse (u1) | — | — | **200** | `{"data": [{"id": "clm_1", "policyId": "pol_1", "ownerUserId": "u1", "amount": 12000, "status": "submitted", "description": "Çar...` |
| `P1-CLM-LIST-u1-size_101` | `GET` | `/claims?pageSize=101` | tok_user1_ayse (u1) | — | — | **200** | `{"data": [{"id": "clm_1", "policyId": "pol_1", "ownerUserId": "u1", "amount": 12000, "status": "submitted", "description": "Çar...` |
| `P1-CLM-LIST-u1-size_abc` | `GET` | `/claims?pageSize=abc` | tok_user1_ayse (u1) | — | — | **200** | `{"data": [], "meta": {"page": 1, "pageSize": null, "total": 0}}` |
| `P1-CLM-GET-u1-clm_1` | `GET` | `/claims/clm_1` | tok_user1_ayse (u1) | — | — | **200** | `{"id": "clm_1", "policyId": "pol_1", "ownerUserId": "u1", "amount": 12000, "status": "submitted", "description": "Çarpma hasarı...` |
| `P1-CLM-GET-u1-clm_6` | `GET` | `/claims/clm_6` | tok_user1_ayse (u1) | — | — | **403** | `{"error": "Erişim engellendi", "message": "Bu hasar talebine erişim yetkiniz yok."}` |
| `P1-CLM-GET-u1-clm_7` | `GET` | `/claims/clm_7` | tok_user1_ayse (u1) | — | — | **403** | `{"error": "Erişim engellendi", "message": "Bu hasar talebine erişim yetkiniz yok."}` |
| `P1-CLM-GET-u1-clm_999` | `GET` | `/claims/clm_999` | tok_user1_ayse (u1) | — | — | **404** | `{"error": "Bulunamadı", "message": "Hasar talebi bulunamadı."}` |
| `P1-CLM-GET-u2-clm_6` | `GET` | `/claims/clm_6` | tok_user2_mehmet (u2) | — | — | **200** | `{"id": "clm_6", "policyId": "pol_4", "ownerUserId": "u2", "amount": 5000, "status": "approved", "description": "Çarpma hasarı",...` |
| `P1-CLM-GET-u2-clm_1` | `GET` | `/claims/clm_1` | tok_user2_mehmet (u2) | — | — | **403** | `{"error": "Erişim engellendi", "message": "Bu hasar talebine erişim yetkiniz yok."}` |
| `P1-CLM-GET-u2-clm_999` | `GET` | `/claims/clm_999` | tok_user2_mehmet (u2) | — | — | **404** | `{"error": "Bulunamadı", "message": "Hasar talebi bulunamadı."}` |
| `P1-CLM-GET-admin-clm_1` | `GET` | `/claims/clm_1` | tok_admin_root (admin) | — | — | **200** | `{"id": "clm_1", "policyId": "pol_1", "ownerUserId": "u1", "amount": 12000, "status": "submitted", "description": "Çarpma hasarı...` |
| `P1-CLM-GET-admin-clm_6` | `GET` | `/claims/clm_6` | tok_admin_root (admin) | — | — | **200** | `{"id": "clm_6", "policyId": "pol_4", "ownerUserId": "u2", "amount": 5000, "status": "approved", "description": "Çarpma hasarı",...` |
| `P1-CLM-GET-admin-clm_999` | `GET` | `/claims/clm_999` | tok_admin_root (admin) | — | — | **404** | `{"error": "Bulunamadı", "message": "Hasar talebi bulunamadı."}` |
| `P1-ADMIN-u1-/admin/policies` | `GET` | `/admin/policies` | tok_user1_ayse (u1) | — | — | **403** | `{"error": "Erişim engellendi", "message": "Yönetici yetkisi gerekli."}` |
| `P1-ADMIN-u1-/admin/stats` | `GET` | `/admin/stats` | tok_user1_ayse (u1) | — | — | **200** | `{"totalPolicies": 5, "totalClaims": 7, "totalPremium": 9800}` |
| `P1-ADMIN-u2-/admin/policies` | `GET` | `/admin/policies` | tok_user2_mehmet (u2) | — | — | **403** | `{"error": "Erişim engellendi", "message": "Yönetici yetkisi gerekli."}` |
| `P1-ADMIN-u2-/admin/stats` | `GET` | `/admin/stats` | tok_user2_mehmet (u2) | — | — | **200** | `{"totalPolicies": 5, "totalClaims": 7, "totalPremium": 9800}` |
| `P1-ADMIN-admin-/admin/policies` | `GET` | `/admin/policies` | tok_admin_root (admin) | — | — | **200** | `[{"id": "pol_1", "policyNumber": "POL-2026-0001", "ownerUserId": "u1", "holderName": "Ayşe Yılmaz", "holderTckn": "11111111110"...` |
| `P1-ADMIN-admin-/admin/stats` | `GET` | `/admin/stats` | tok_admin_root (admin) | — | — | **200** | `{"totalPolicies": 5, "totalClaims": 7, "totalPremium": 9800}` |
| `P1-MISC-GET-/unknown` | `GET` | `/unknown` | tok_user1_ayse (u1) | — | — | **404** | `{"error": "Bulunamadı", "message": "Kaynak yok."}` |
| `P1-MISC-DELETE-/policies/pol_1` | `DELETE` | `/policies/pol_1` | tok_user1_ayse (u1) | — | — | **405** | `{"error": "Yöntem desteklenmiyor"}` |
| `P1-MISC-POST-/policies` | `POST` | `/policies` | tok_user1_ayse (u1) | — | — | **404** | `{"error": "Bulunamadı", "message": "Kaynak yok."}` |

### Faz 2A — PATCH /policies/{id} Güncelleme, BOLA, Tip Doğrulama ve Mass Assignment (37 istek)

| Kayıt ID | Yöntem | Yol & Sorgu | Token / Auth | Ek Başlıklar | İstek Gövdesi | Durum | Yanıt Özeti |
|---|---|---|---|---|---|---|---|
| `P2A-CHECK-pol_5` | `GET` | `/policies/pol_5` | tok_admin_root (admin) | — | — | **200** | `{"id": "pol_5", "policyNumber": "POL-2026-0005", "ownerUserId": "u1", "holderName": "Ayşe Yılmaz", "holderTckn": "11111111110",...` |
| `P2A-CHECK-pol_3` | `GET` | `/policies/pol_3` | tok_admin_root (admin) | — | — | **200** | `{"id": "pol_3", "policyNumber": "POL-2026-0003", "ownerUserId": "u2", "holderName": "Mehmet Demir", "holderTckn": "22222222220"...` |
| `P2A-AUTH-NONE` | `PATCH` | `/policies/pol_5` | (yok) | — | `{"holderName": "X"}` | **401** | `{"error": "Yetkisiz", "message": "Geçerli bir bearer token gerekli."}` |
| `P2A-AUTH-BAD` | `PATCH` | `/policies/pol_5` | `Bearer fake` | — | `{"holderName": "X"}` | **401** | `{"error": "Yetkisiz", "message": "Geçerli bir bearer token gerekli."}` |
| `P2A-404` | `PATCH` | `/policies/pol_999` | tok_user1_ayse (u1) | — | `{"holderName": "X"}` | **404** | `{"error": "Bulunamadı", "message": "Poliçe bulunamadı."}` |
| `P2A-BOLA-U1-ON-U2` | `PATCH` | `/policies/pol_3` | tok_user1_ayse (u1) | — | `{"holderName": "HackU2"}` | **403** | `{"error": "Erişim engellendi", "message": "Bu poliçeye erişim yetkiniz yok."}` |
| `P2A-BOLA-U2-ON-U1` | `PATCH` | `/policies/pol_5` | tok_user2_mehmet (u2) | — | `{"holderName": "HackU1"}` | **403** | `{"error": "Erişim engellendi", "message": "Bu poliçeye erişim yetkiniz yok."}` |
| `P2A-CHECK-pol_3` | `GET` | `/policies/pol_3` | tok_admin_root (admin) | — | — | **200** | `{"id": "pol_3", "policyNumber": "POL-2026-0003", "ownerUserId": "u2", "holderName": "Mehmet Demir", "holderTckn": "22222222220"...` |
| `P2A-CHECK-pol_5` | `GET` | `/policies/pol_5` | tok_admin_root (admin) | — | — | **200** | `{"id": "pol_5", "policyNumber": "POL-2026-0005", "ownerUserId": "u1", "holderName": "Ayşe Yılmaz", "holderTckn": "11111111110",...` |
| `P2A-MALFORMED-JSON` | `PATCH` | `/policies/pol_5` | tok_user1_ayse (u1) | — | `{bad json` | **400** | `{"error": "Geçersiz JSON", "detail": "Expected property name or '}' in JSON at position 1 (line 1 column 2)", "stack": "SyntaxE...` |
| `P2A-EMPTY-RAW` | `PATCH` | `/policies/pol_5` | tok_user1_ayse (u1) | — | `(boş)` | **200** | `{"id": "pol_5", "policyNumber": "POL-2026-0005", "ownerUserId": "u1", "holderName": "Ayşe Yılmaz", "holderTckn": "11111111110",...` |
| `P2A-EMPTY-OBJ` | `PATCH` | `/policies/pol_5` | tok_user1_ayse (u1) | — | `{}` | **200** | `{"id": "pol_5", "policyNumber": "POL-2026-0005", "ownerUserId": "u1", "holderName": "Ayşe Yılmaz", "holderTckn": "11111111110",...` |
| `P2A-ARRAY-BODY` | `PATCH` | `/policies/pol_5` | tok_user1_ayse (u1) | — | `[]` | **200** | `{"id": "pol_5", "policyNumber": "POL-2026-0005", "ownerUserId": "u1", "holderName": "Ayşe Yılmaz", "holderTckn": "11111111110",...` |
| `P2A-HOLDER-INT` | `PATCH` | `/policies/pol_5` | tok_user1_ayse (u1) | — | `{"holderName": 12345}` | **200** | `{"id": "pol_5", "policyNumber": "POL-2026-0005", "ownerUserId": "u1", "holderName": 12345, "holderTckn": "11111111110", "covera...` |
| `P2A-HOLDER-NULL` | `PATCH` | `/policies/pol_5` | tok_user1_ayse (u1) | — | `{"holderName": null}` | **200** | `{"id": "pol_5", "policyNumber": "POL-2026-0005", "ownerUserId": "u1", "holderName": null, "holderTckn": "11111111110", "coverag...` |
| `P2A-HOLDER-EMPTY` | `PATCH` | `/policies/pol_5` | tok_user1_ayse (u1) | — | `{"holderName": ""}` | **200** | `{"id": "pol_5", "policyNumber": "POL-2026-0005", "ownerUserId": "u1", "holderName": "", "holderTckn": "11111111110", "coverageT...` |
| `P2A-HOLDER-SPACES` | `PATCH` | `/policies/pol_5` | tok_user1_ayse (u1) | — | `{"holderName": "   "}` | **200** | `{"id": "pol_5", "policyNumber": "POL-2026-0005", "ownerUserId": "u1", "holderName": "   ", "holderTckn": "11111111110", "covera...` |
| `P2A-AGENT-INT` | `PATCH` | `/policies/pol_5` | tok_user1_ayse (u1) | — | `{"agentName": 12345}` | **200** | `{"id": "pol_5", "policyNumber": "POL-2026-0005", "ownerUserId": "u1", "holderName": "   ", "holderTckn": "11111111110", "covera...` |
| `P2A-AGENT-BOOL` | `PATCH` | `/policies/pol_5` | tok_user1_ayse (u1) | — | `{"agentName": true}` | **200** | `{"id": "pol_5", "policyNumber": "POL-2026-0005", "ownerUserId": "u1", "holderName": "   ", "holderTckn": "11111111110", "covera...` |
| `P2A-XSS-HOLDER` | `PATCH` | `/policies/pol_5` | tok_user1_ayse (u1) | — | `{"holderName": "<script>alert(1)</script>"}` | **200** | `{"id": "pol_5", "policyNumber": "POL-2026-0005", "ownerUserId": "u1", "holderName": "<script>alert(1)</script>", "holderTckn": ...` |
| `P2A-SQLI-HOLDER` | `PATCH` | `/policies/pol_5` | tok_user1_ayse (u1) | — | `{"holderName": "' OR '1'='1' --"}` | **200** | `{"id": "pol_5", "policyNumber": "POL-2026-0005", "ownerUserId": "u1", "holderName": "' OR '1'='1' --", "holderTckn": "111111111...` |
| `P2A-HAPPY-TR` | `PATCH` | `/policies/pol_5` | tok_user1_ayse (u1) | — | `{"holderName": "Ayşe Yılmaz Şığüöç", "agentName": "İrem Çağlar"}` | **200** | `{"id": "pol_5", "policyNumber": "POL-2026-0005", "ownerUserId": "u1", "holderName": "Ayşe Yılmaz Şığüöç", "holderTckn": "111111...` |
| `P2A-HAPPY-NULL-AGENT` | `PATCH` | `/policies/pol_5` | tok_user1_ayse (u1) | — | `{"holderName": "Ayşe Yılmaz", "agentName": null}` | **200** | `{"id": "pol_5", "policyNumber": "POL-2026-0005", "ownerUserId": "u1", "holderName": "Ayşe Yılmaz", "holderTckn": "11111111110",...` |
| `P2A-RO-PREMIUM` | `PATCH` | `/policies/pol_5` | tok_user1_ayse (u1) | — | `{"premium": 1}` | **200** | `{"id": "pol_5", "policyNumber": "POL-2026-0005", "ownerUserId": "u1", "holderName": "Ayşe Yılmaz", "holderTckn": "11111111110",...` |
| `P2A-RO-LIMIT` | `PATCH` | `/policies/pol_5` | tok_user1_ayse (u1) | — | `{"coverageLimit": 9999999}` | **200** | `{"id": "pol_5", "policyNumber": "POL-2026-0005", "ownerUserId": "u1", "holderName": "Ayşe Yılmaz", "holderTckn": "11111111110",...` |
| `P2A-RO-STATUS` | `PATCH` | `/policies/pol_5` | tok_user1_ayse (u1) | — | `{"status": "cancelled"}` | **200** | `{"id": "pol_5", "policyNumber": "POL-2026-0005", "ownerUserId": "u1", "holderName": "Ayşe Yılmaz", "holderTckn": "11111111110",...` |
| `P2A-RO-POLICYNUM` | `PATCH` | `/policies/pol_5` | tok_user1_ayse (u1) | — | `{"policyNumber": "POL-HACK-999"}` | **200** | `{"id": "pol_5", "policyNumber": "POL-2026-0005", "ownerUserId": "u1", "holderName": "Ayşe Yılmaz", "holderTckn": "11111111110",...` |
| `P2A-RO-COVTYPE` | `PATCH` | `/policies/pol_5` | tok_user1_ayse (u1) | — | `{"coverageType": "saglik"}` | **200** | `{"id": "pol_5", "policyNumber": "POL-2026-0005", "ownerUserId": "u1", "holderName": "Ayşe Yılmaz", "holderTckn": "11111111110",...` |
| `P2A-RO-TCKN` | `PATCH` | `/policies/pol_5` | tok_user1_ayse (u1) | — | `{"holderTckn": "99999999990"}` | **200** | `{"id": "pol_5", "policyNumber": "POL-2026-0005", "ownerUserId": "u1", "holderName": "Ayşe Yılmaz", "holderTckn": "11111111110",...` |
| `P2A-RO-STARTDATE` | `PATCH` | `/policies/pol_5` | tok_user1_ayse (u1) | — | `{"startDate": "2020-01-01"}` | **200** | `{"id": "pol_5", "policyNumber": "POL-2026-0005", "ownerUserId": "u1", "holderName": "Ayşe Yılmaz", "holderTckn": "11111111110",...` |
| `P2A-RO-ID` | `PATCH` | `/policies/pol_5` | tok_user1_ayse (u1) | — | `{"id": "pol_hacked"}` | **200** | `{"id": "pol_5", "policyNumber": "POL-2026-0005", "ownerUserId": "u1", "holderName": "Ayşe Yılmaz", "holderTckn": "11111111110",...` |
| `P2A-RO-EXTRA` | `PATCH` | `/policies/pol_5` | tok_user1_ayse (u1) | — | `{"role": "admin", "isAdmin": true}` | **200** | `{"id": "pol_5", "policyNumber": "POL-2026-0005", "ownerUserId": "u1", "holderName": "Ayşe Yılmaz", "holderTckn": "11111111110",...` |
| `P2A-RO-MIXED` | `PATCH` | `/policies/pol_5` | tok_user1_ayse (u1) | — | `{"holderName": "Ayşe Yılmaz", "premium": 5, "coverageLimit": 888888, "status": "pending"}` | **200** | `{"id": "pol_5", "policyNumber": "POL-2026-0005", "ownerUserId": "u1", "holderName": "Ayşe Yılmaz", "holderTckn": "11111111110",...` |
| `P2A-CHECK-pol_5` | `GET` | `/policies/pol_5` | tok_admin_root (admin) | — | — | **200** | `{"id": "pol_5", "policyNumber": "POL-2026-0005", "ownerUserId": "u1", "holderName": "Ayşe Yılmaz", "holderTckn": "11111111110",...` |
| `P2A-RO-OWNER` | `PATCH` | `/policies/pol_5` | tok_user1_ayse (u1) | — | `{"ownerUserId": "u2"}` | **200** | `{"id": "pol_5", "policyNumber": "POL-2026-0005", "ownerUserId": "u1", "holderName": "Ayşe Yılmaz", "holderTckn": "11111111110",...` |
| `P2A-CHECK-pol_5` | `GET` | `/policies/pol_5` | tok_admin_root (admin) | — | — | **200** | `{"id": "pol_5", "policyNumber": "POL-2026-0005", "ownerUserId": "u1", "holderName": "Ayşe Yılmaz", "holderTckn": "11111111110",...` |
| `P2A-ADMIN-PATCH-U2POL` | `PATCH` | `/policies/pol_3` | tok_admin_root (admin) | — | `{"agentName": "Can Öz"}` | **200** | `{"id": "pol_3", "policyNumber": "POL-2026-0003", "ownerUserId": "u2", "holderName": "Mehmet Demir", "holderTckn": "22222222220"...` |

### Faz 2B — POST /claims Oluşturma, Limit/Alt Sınır, Idempotency, Eşzamanlılık ve Güvenlik Probları (50 istek)

| Kayıt ID | Yöntem | Yol & Sorgu | Token / Auth | Ek Başlıklar | İstek Gövdesi | Durum | Yanıt Özeti |
|---|---|---|---|---|---|---|---|
| `P2B-AUTH-NONE` | `POST` | `/claims` | (yok) | — | `{"policyId": "pol_1", "amount": 100}` | **401** | `{"error": "Yetkisiz", "message": "Geçerli bir bearer token gerekli."}` |
| `P2B-AUTH-NOBEARER` | `POST` | `/claims` | `tok_user1_ayse` | — | `{"policyId": "pol_1", "amount": 100}` | **401** | `{"error": "Yetkisiz", "message": "Geçerli bir bearer token gerekli."}` |
| `P2B-MALFORMED-JSON` | `POST` | `/claims` | tok_user1_ayse (u1) | — | `{bad json` | **400** | `{"error": "Geçersiz JSON", "detail": "Expected property name or '}' in JSON at position 1 (line 1 column 2)", "stack": "SyntaxE...` |
| `P2B-EMPTY-RAW` | `POST` | `/claims` | tok_user1_ayse (u1) | — | `(boş)` | **400** | `{"error": "Eksik alan", "message": "policyId ve amount zorunludur."}` |
| `P2B-ARRAY-BODY` | `POST` | `/claims` | tok_user1_ayse (u1) | — | `[]` | **400** | `{"error": "Eksik alan", "message": "policyId ve amount zorunludur."}` |
| `P2B-EMPTY-OBJ` | `POST` | `/claims` | tok_user1_ayse (u1) | — | `{}` | **400** | `{"error": "Eksik alan", "message": "policyId ve amount zorunludur."}` |
| `P2B-MISS-POLICYID` | `POST` | `/claims` | tok_user1_ayse (u1) | — | `{"amount": 100}` | **400** | `{"error": "Eksik alan", "message": "policyId ve amount zorunludur."}` |
| `P2B-MISS-AMOUNT` | `POST` | `/claims` | tok_user1_ayse (u1) | — | `{"policyId": "pol_1"}` | **400** | `{"error": "Eksik alan", "message": "policyId ve amount zorunludur."}` |
| `P2B-POLICYID-INT` | `POST` | `/claims` | tok_user1_ayse (u1) | — | `{"policyId": 123, "amount": 100}` | **404** | `{"error": "Bulunamadı", "message": "Poliçe bulunamadı."}` |
| `P2B-POLICYID-NULL` | `POST` | `/claims` | tok_user1_ayse (u1) | — | `{"policyId": null, "amount": 100}` | **404** | `{"error": "Bulunamadı", "message": "Poliçe bulunamadı."}` |
| `P2B-POLICYID-EMPTY` | `POST` | `/claims` | tok_user1_ayse (u1) | — | `{"policyId": "", "amount": 100}` | **404** | `{"error": "Bulunamadı", "message": "Poliçe bulunamadı."}` |
| `P2B-AMOUNT-STR-NUM` | `POST` | `/claims` | tok_user1_ayse (u1) | — | `{"policyId": "pol_1", "amount": "100"}` | **400** | `{"error": "Geçersiz tip", "message": "amount sayısal olmalıdır."}` |
| `P2B-AMOUNT-STR-ABC` | `POST` | `/claims` | tok_user1_ayse (u1) | — | `{"policyId": "pol_1", "amount": "abc"}` | **400** | `{"error": "Geçersiz tip", "message": "amount sayısal olmalıdır."}` |
| `P2B-AMOUNT-NULL` | `POST` | `/claims` | tok_user1_ayse (u1) | — | `{"policyId": "pol_1", "amount": null}` | **400** | `{"error": "Geçersiz tip", "message": "amount sayısal olmalıdır."}` |
| `P2B-AMOUNT-BOOL` | `POST` | `/claims` | tok_user1_ayse (u1) | — | `{"policyId": "pol_1", "amount": true}` | **400** | `{"error": "Geçersiz tip", "message": "amount sayısal olmalıdır."}` |
| `P2B-DESC-INT` | `POST` | `/claims` | tok_user1_ayse (u1) | — | `{"policyId": "pol_1", "amount": 100, "description": 12345}` | **200** | `{"id": "clm_8", "policyId": "pol_1", "ownerUserId": "u1", "amount": 100, "status": "submitted", "description": "", "createdAt":...` |
| `P2B-NOTFOUND-POL` | `POST` | `/claims` | tok_user1_ayse (u1) | — | `{"policyId": "pol_999", "amount": 100}` | **404** | `{"error": "Bulunamadı", "message": "Poliçe bulunamadı."}` |
| `P2B-BOLA-U1-ON-POL4` | `POST` | `/claims` | tok_user1_ayse (u1) | — | `{"policyId": "pol_4", "amount": 500, "description": "BOLA test u1->pol_4"}` | **403** | `{"error": "Erişim engellendi", "message": "Bu poliçe için hasar talebi oluşturamazsınız."}` |
| `P2B-BOLA-U1-ON-POL3` | `POST` | `/claims` | tok_user1_ayse (u1) | — | `{"policyId": "pol_3", "amount": 500, "description": "BOLA test u1->pol_3"}` | **403** | `{"error": "Erişim engellendi", "message": "Bu poliçe için hasar talebi oluşturamazsınız."}` |
| `P2B-ADMIN-ON-POL4` | `POST` | `/claims` | tok_admin_root (admin) | — | `{"policyId": "pol_4", "amount": 500, "description": "Admin claim on pol_4"}` | **200** | `{"id": "clm_9", "policyId": "pol_4", "ownerUserId": "admin", "amount": 500, "status": "submitted", "description": "Admin claim ...` |
| `P2B-CHK-POL4-U2` | `GET` | `/claims?policyId=pol_4` | tok_user2_mehmet (u2) | — | — | **200** | `{"data": [{"id": "clm_6", "policyId": "pol_4", "ownerUserId": "u2", "amount": 5000, "status": "approved", "description": "Çarpm...` |
| `P2B-AMT-NEG` | `POST` | `/claims` | tok_user1_ayse (u1) | — | `{"policyId": "pol_1", "amount": -100, "description": "negatif"}` | **200** | `{"id": "clm_10", "policyId": "pol_1", "ownerUserId": "u1", "amount": -100, "status": "submitted", "description": "negatif", "cr...` |
| `P2B-AMT-ZERO` | `POST` | `/claims` | tok_user1_ayse (u1) | — | `{"policyId": "pol_1", "amount": 0, "description": "sıfır"}` | **200** | `{"id": "clm_11", "policyId": "pol_1", "ownerUserId": "u1", "amount": 0, "status": "submitted", "description": "sıfır", "created...` |
| `P2B-AMT-0_99` | `POST` | `/claims` | tok_user1_ayse (u1) | — | `{"policyId": "pol_1", "amount": 0.99, "description": "0.99"}` | **200** | `{"id": "clm_12", "policyId": "pol_1", "ownerUserId": "u1", "amount": 0.99, "status": "submitted", "description": "0.99", "creat...` |
| `P2B-AMT-1` | `POST` | `/claims` | tok_user1_ayse (u1) | — | `{"policyId": "pol_1", "amount": 1, "description": "min sınır 1"}` | **200** | `{"id": "clm_13", "policyId": "pol_1", "ownerUserId": "u1", "amount": 1, "status": "submitted", "description": "min sınır 1", "c...` |
| `P2B-AMT-OVER-LIMIT-1` | `POST` | `/claims` | tok_user1_ayse (u1) | — | `{"policyId": "pol_1", "amount": 50001, "description": "limit+1"}` | **200** | `{"id": "clm_14", "policyId": "pol_1", "ownerUserId": "u1", "amount": 50001, "status": "submitted", "description": "limit+1", "c...` |
| `P2B-AMT-OVER-LIMIT-0_01` | `POST` | `/claims` | tok_user1_ayse (u1) | — | `{"policyId": "pol_1", "amount": 50000.01, "description": "limit+0.01"}` | **200** | `{"id": "clm_15", "policyId": "pol_1", "ownerUserId": "u1", "amount": 50000.01, "status": "submitted", "description": "limit+0.0...` |
| `P2B-AMT-AT-LIMIT` | `POST` | `/claims` | tok_user1_ayse (u1) | — | `{"policyId": "pol_1", "amount": 50000, "description": "tam limit"}` | **200** | `{"id": "clm_16", "policyId": "pol_1", "ownerUserId": "u1", "amount": 50000, "status": "submitted", "description": "tam limit", ...` |
| `P2B-AMT-CUMUL-CHECK` | `POST` | `/claims` | tok_user1_ayse (u1) | — | `{"policyId": "pol_2", "amount": 96000, "description": "kümülatif 3000+2000+96000=101000 > 100000"}` | **200** | `{"id": "clm_17", "policyId": "pol_2", "ownerUserId": "u1", "amount": 96000, "status": "submitted", "description": "kümülatif 30...` |
| `P2B-CANCELLED-POLICY` | `POST` | `/claims` | tok_user2_mehmet (u2) | — | `{"policyId": "pol_3", "amount": 500, "description": "İptal poliçeye hasar talebi"}` | **200** | `{"id": "clm_18", "policyId": "pol_3", "ownerUserId": "u2", "amount": 500, "status": "submitted", "description": "İptal poliçeye...` |
| `P2B-MASS-ASSIGN` | `POST` | `/claims` | tok_user1_ayse (u1) | — | `{"policyId": "pol_5", "amount": 100, "status": "approved", "ownerUserId": "u2", "id": "clm_hack999", "claimNumber": "CLM-HACK-9...` | **200** | `{"id": "clm_19", "policyId": "pol_5", "ownerUserId": "u1", "amount": 100, "status": "submitted", "description": "", "createdAt"...` |
| `P2B-IDEM-1` | `POST` | `/claims` | tok_user1_ayse (u1) | `{"Idempotency-Key": "idem-key-101"}` | `{"policyId": "pol_5", "amount": 250, "description": "Idem 1"}` | **200** | `{"id": "clm_20", "policyId": "pol_5", "ownerUserId": "u1", "amount": 250, "status": "submitted", "description": "Idem 1", "crea...` |
| `P2B-IDEM-2-REPEAT` | `POST` | `/claims` | tok_user1_ayse (u1) | `{"Idempotency-Key": "idem-key-101"}` | `{"policyId": "pol_5", "amount": 250, "description": "Idem 1"}` | **200** | `{"id": "clm_21", "policyId": "pol_5", "ownerUserId": "u1", "amount": 250, "status": "submitted", "description": "Idem 1", "crea...` |
| `P2B-IDEM-3-DIFFBODY` | `POST` | `/claims` | tok_user1_ayse (u1) | `{"Idempotency-Key": "idem-key-101"}` | `{"policyId": "pol_5", "amount": 777, "description": "Farklı gövde"}` | **200** | `{"id": "clm_22", "policyId": "pol_5", "ownerUserId": "u1", "amount": 777, "status": "submitted", "description": "Farklı gövde",...` |
| `P2B-IDEM-4-OTHERUSER` | `POST` | `/claims` | tok_user2_mehmet (u2) | `{"Idempotency-Key": "idem-key-101"}` | `{"policyId": "pol_4", "amount": 333, "description": "Başka kullanıcı aynı key"}` | **200** | `{"id": "clm_23", "policyId": "pol_4", "ownerUserId": "u2", "amount": 333, "status": "submitted", "description": "Başka kullanıc...` |
| `P2B-IDEM-FAIL-FIRST` | `POST` | `/claims` | tok_user1_ayse (u1) | `{"Idempotency-Key": "idem-fail-303"}` | `{"policyId": "pol_5", "amount": 999999, "description": "Limit aşımı"}` | **200** | `{"id": "clm_24", "policyId": "pol_5", "ownerUserId": "u1", "amount": 999999, "status": "submitted", "description": "Limit aşımı...` |
| `P2B-IDEM-FAIL-RETRY` | `POST` | `/claims` | tok_user1_ayse (u1) | `{"Idempotency-Key": "idem-fail-303"}` | `{"policyId": "pol_5", "amount": 150, "description": "Geçerli deneme"}` | **200** | `{"id": "clm_25", "policyId": "pol_5", "ownerUserId": "u1", "amount": 150, "status": "submitted", "description": "Geçerli deneme...` |
| `P2B-IDEM-RACE-3` | `POST` | `/claims` | tok_user1_ayse (u1) | `{"Idempotency-Key": "idem-race-202"}` | `{"policyId": "pol_5", "amount": 123, "description": "Yarış testi"}` | **200** | `{"id": "clm_26", "policyId": "pol_5", "ownerUserId": "u1", "amount": 123, "status": "submitted", "description": "Yarış testi", ...` |
| `P2B-IDEM-RACE-1` | `POST` | `/claims` | tok_user1_ayse (u1) | `{"Idempotency-Key": "idem-race-202"}` | `{"policyId": "pol_5", "amount": 123, "description": "Yarış testi"}` | **200** | `{"id": "clm_27", "policyId": "pol_5", "ownerUserId": "u1", "amount": 123, "status": "submitted", "description": "Yarış testi", ...` |
| `P2B-IDEM-RACE-2` | `POST` | `/claims` | tok_user1_ayse (u1) | `{"Idempotency-Key": "idem-race-202"}` | `{"policyId": "pol_5", "amount": 123, "description": "Yarış testi"}` | **200** | `{"id": "clm_28", "policyId": "pol_5", "ownerUserId": "u1", "amount": 123, "status": "submitted", "description": "Yarış testi", ...` |
| `P2B-NOIDEM-1` | `POST` | `/claims` | tok_user1_ayse (u1) | — | `{"policyId": "pol_5", "amount": 222, "description": "Anahtarsız tekrar"}` | **200** | `{"id": "clm_29", "policyId": "pol_5", "ownerUserId": "u1", "amount": 222, "status": "submitted", "description": "Anahtarsız tek...` |
| `P2B-NOIDEM-2` | `POST` | `/claims` | tok_user1_ayse (u1) | — | `{"policyId": "pol_5", "amount": 222, "description": "Anahtarsız tekrar"}` | **200** | `{"id": "clm_30", "policyId": "pol_5", "ownerUserId": "u1", "amount": 222, "status": "submitted", "description": "Anahtarsız tek...` |
| `P2B-XSS-DESC` | `POST` | `/claims` | tok_user1_ayse (u1) | — | `{"policyId": "pol_5", "amount": 10, "description": "<script>alert(1)</script>"}` | **200** | `{"id": "clm_31", "policyId": "pol_5", "ownerUserId": "u1", "amount": 10, "status": "submitted", "description": "<script>alert(1...` |
| `P2B-SQLI-DESC` | `POST` | `/claims` | tok_user1_ayse (u1) | — | `{"policyId": "pol_5", "amount": 10, "description": "' OR '1'='1' --"}` | **200** | `{"id": "clm_32", "policyId": "pol_5", "ownerUserId": "u1", "amount": 10, "status": "submitted", "description": "' OR '1'='1' --...` |
| `P2B-PROTO` | `POST` | `/claims` | tok_user1_ayse (u1) | — | `{"policyId": "pol_5", "amount": 10, "__proto__": {"isAdmin": true}}` | **200** | `{"id": "clm_33", "policyId": "pol_5", "ownerUserId": "u1", "amount": 10, "status": "submitted", "description": "", "createdAt":...` |
| `P2B-PATH-TRAV` | `GET` | `/policies/..%2Fadmin%2Fstats` | tok_user1_ayse (u1) | — | — | **404** | `{"error": "Bulunamadı", "message": "Poliçe bulunamadı."}` |
| `P2B-PATH-BADENC` | `GET` | `/claims/%ZZ` | tok_user1_ayse (u1) | — | — | **404** | `{"error": "Bulunamadı", "message": "Hasar talebi bulunamadı."}` |
| `P2B-FINAL-POL5-CLAIMS` | `GET` | `/claims?policyId=pol_5&pageSize=100` | tok_user1_ayse (u1) | — | — | **200** | `{"data": [{"id": "clm_4", "policyId": "pol_5", "ownerUserId": "u1", "amount": 15000, "status": "submitted", "description": "Tra...` |
| `P2B-FINAL-ALL-CLAIMS` | `GET` | `/claims?pageSize=100` | tok_admin_root (admin) | — | — | **200** | `{"data": [{"id": "clm_1", "policyId": "pol_1", "ownerUserId": "u1", "amount": 12000, "status": "submitted", "description": "Çar...` |
| `P2B-FINAL-STATS` | `GET` | `/admin/stats` | tok_admin_root (admin) | — | — | **200** | `{"totalPolicies": 5, "totalClaims": 33, "totalPremium": 9800}` |

### Faz 3 — Kenar Durumlar, Content-Type, HTTP Yöntemleri ve Sayfalama Doğrulaması (16 istek)

| Kayıt ID | Yöntem | Yol & Sorgu | Token / Auth | Ek Başlıklar | İstek Gövdesi | Durum | Yanıt Özeti |
|---|---|---|---|---|---|---|---|
| `P3-U2-LIST-CLAIMS` | `GET` | `/claims` | tok_user2_mehmet (u2) | — | — | **200** | `{"data": [{"id": "clm_6", "policyId": "pol_4", "ownerUserId": "u2", "amount": 5000, "status": "approved", "description": "Çarpm...` |
| `P3-U2-GET-CLM9` | `GET` | `/claims/clm_9` | tok_user2_mehmet (u2) | — | — | **403** | `{"error": "Erişim engellendi", "message": "Bu hasar talebine erişim yetkiniz yok."}` |
| `P3-U2-PAGE1-SIZE2` | `GET` | `/claims?page=1&pageSize=2` | tok_user2_mehmet (u2) | — | — | **200** | `{"data": [{"id": "clm_6", "policyId": "pol_4", "ownerUserId": "u2", "amount": 5000, "status": "approved", "description": "Çarpm...` |
| `P3-PATCH-TEXTPLAIN` | `PATCH` | `/policies/pol_5` | tok_user1_ayse (u1) | `{"Content-Type": "text/plain"}` | `{"holderName": "TextPlainTest"}` | **200** | `{"id": "pol_5", "policyNumber": "POL-2026-0005", "ownerUserId": "u1", "holderName": "TextPlainTest", "holderTckn": "11111111110...` |
| `P3-POST-TEXTPLAIN` | `POST` | `/claims` | tok_user1_ayse (u1) | `{"Content-Type": "text/plain"}` | `{"policyId": "pol_5", "amount": 50}` | **200** | `{"id": "clm_34", "policyId": "pol_5", "ownerUserId": "u1", "amount": 50, "status": "submitted", "description": "", "createdAt":...` |
| `P3-RESTORE-POL5` | `PATCH` | `/policies/pol_5` | tok_user1_ayse (u1) | — | `{"holderName": "Ayşe Yılmaz", "agentName": null}` | **200** | `{"id": "pol_5", "policyNumber": "POL-2026-0005", "ownerUserId": "u1", "holderName": "Ayşe Yılmaz", "holderTckn": "11111111110",...` |
| `P3-CLM-DESC-NULL` | `POST` | `/claims` | tok_user1_ayse (u1) | — | `{"policyId": "pol_5", "amount": 10, "description": null}` | **200** | `{"id": "clm_35", "policyId": "pol_5", "ownerUserId": "u1", "amount": 10, "status": "submitted", "description": "", "createdAt":...` |
| `P3-CLM-DESC-OMIT` | `POST` | `/claims` | tok_user1_ayse (u1) | — | `{"policyId": "pol_5", "amount": 10}` | **200** | `{"id": "clm_36", "policyId": "pol_5", "ownerUserId": "u1", "amount": 10, "status": "submitted", "description": "", "createdAt":...` |
| `P3-HEADERS-POL1` | `GET` | `/policies/pol_1` | tok_user1_ayse (u1) | — | — | **200** | `{"id": "pol_1", "policyNumber": "POL-2026-0001", "ownerUserId": "u1", "holderName": "Ayşe Yılmaz", "holderTckn": "11111111110",...` |
| `P3-PUT-POL` | `PUT` | `/policies/pol_5` | tok_user1_ayse (u1) | — | — | **405** | `{"error": "Yöntem desteklenmiyor"}` |
| `P3-HEAD-HEALTH` | `HEAD` | `/health` | tok_user1_ayse (u1) | — | — | **404** | `(boş)` |
| `P3-OPTIONS-POL` | `OPTIONS` | `/policies` | tok_user1_ayse (u1) | — | — | **404** | `{"error": "Bulunamadı", "message": "Kaynak yok."}` |
| `P3-PATCH-UNKNOWN-ONLY` | `PATCH` | `/policies/pol_5` | tok_user1_ayse (u1) | — | `{"unknownField": "abc"}` | **200** | `{"id": "pol_5", "policyNumber": "POL-2026-0005", "ownerUserId": "u1", "holderName": "Ayşe Yılmaz", "holderTckn": "11111111110",...` |
| `P3-POST-UNKNOWN-FIELD` | `POST` | `/claims` | tok_user1_ayse (u1) | — | `{"policyId": "pol_5", "amount": 15, "extraField": "abc"}` | **200** | `{"id": "clm_37", "policyId": "pol_5", "ownerUserId": "u1", "amount": 15, "status": "submitted", "description": "", "createdAt":...` |
| `P3-ADMIN-SIZE-NEG1` | `GET` | `/claims?pageSize=-1` | tok_admin_root (admin) | — | — | **200** | `{"data": [{"id": "clm_1", "policyId": "pol_1", "ownerUserId": "u1", "amount": 12000, "status": "submitted", "description": "Çar...` |
| `P3-GET-CLM8` | `GET` | `/claims/clm_8` | tok_user1_ayse (u1) | — | — | **200** | `{"id": "clm_8", "policyId": "pol_1", "ownerUserId": "u1", "amount": 100, "status": "submitted", "description": "", "createdAt":...` |

### Faz 4 — Sayısal Taşma (1e309 / NaN), Prototype Pollution ve Güncel İstatistik Doğrulaması (5 istek)

| Kayıt ID | Yöntem | Yol & Sorgu | Token / Auth | Ek Başlıklar | İstek Gövdesi | Durum | Yanıt Özeti |
|---|---|---|---|---|---|---|---|
| `P4-CLM-1E309` | `POST` | `/claims` | tok_user1_ayse (u1) | — | `{"policyId": "pol_5", "amount": 1e309}` | **200** | `{"id":"clm_38","policyId":"pol_5","ownerUserId":"u1","amount":null,"status":"submitted","description":"","createdAt":"2026-08-0...` |
| `P4-CLM-NAN` | `POST` | `/claims` | tok_user1_ayse (u1) | — | `{"policyId": "pol_5", "amount": NaN}` | **400** | `{"error":"Geçersiz JSON","detail":"Unexpected token 'N', ...\"\"amount\": NaN}\" is not valid JSON","stack":"SyntaxError: Unexp...` |
| `P4-PATCH-PROTO` | `PATCH` | `/policies/pol_5` | tok_user1_ayse (u1) | — | `{"__proto__": {"role": "admin"}, "holderName": "Ayşe Yılmaz"}` | **200** | `{"id":"pol_5","policyNumber":"POL-2026-0005","ownerUserId":"u1","holderName":"Ayşe Yılmaz","holderTckn":"11111111110","coverage...` |
| `P4-CLM-FLOAT` | `POST` | `/claims` | tok_user1_ayse (u1) | — | `{"policyId": "pol_5", "amount": 10.5, "description": "Ondalık tutar"}` | **200** | `{"id":"clm_39","policyId":"pol_5","ownerUserId":"u1","amount":10.5,"status":"submitted","description":"Ondalık tutar","createdA...` |
| `P4-GET-STATS-CHECK` | `GET` | `/admin/stats` | tok_user1_ayse (u1) | — | — | **200** | `{"totalPolicies":5,"totalClaims":39,"totalPremium":9800}` |

### Faz 5 — Yetki Sırası (Auth vs JSON Parse) ve PATCH Status Ek Kanıtları (7 istek)

| Kayıt ID | Yöntem | Yol & Sorgu | Token / Auth | Ek Başlıklar | İstek Gövdesi | Durum | Yanıt Özeti |
|---|---|---|---|---|---|---|---|
| `P5-UNAUTH-MALFORMED-POST` | `POST` | `/claims` | (yok) | — | `{bad` | **401** | `{"error":"Yetkisiz","message":"Geçerli bir bearer token gerekli."}` |
| `P5-UNAUTH-MALFORMED-PATCH` | `PATCH` | `/policies/pol_1` | (yok) | — | `{bad` | **401** | `{"error":"Yetkisiz","message":"Geçerli bir bearer token gerekli."}` |
| `P5-BOLA-MALFORMED-PATCH` | `PATCH` | `/policies/pol_3` | tok_user1_ayse (u1) | — | `{bad` | **403** | `{"error":"Erişim engellendi","message":"Bu poliçeye erişim yetkiniz yok."}` |
| `P5-POST-ARR-POLICYID` | `POST` | `/claims` | tok_user1_ayse (u1) | — | `{"policyId": ["pol_1"], "amount": 10}` | **404** | `{"error":"Bulunamadı","message":"Poliçe bulunamadı."}` |
| `P5-PATCH-ENDDATE` | `PATCH` | `/policies/pol_5` | tok_user1_ayse (u1) | — | `{"endDate": "2099-01-01"}` | **200** | `{"id":"pol_5","policyNumber":"POL-2026-0005","ownerUserId":"u1","holderName":"Ayşe Yılmaz","holderTckn":"11111111110","coverage...` |
| `P5-PATCH-STATUS-INVALID` | `PATCH` | `/policies/pol_5` | tok_user1_ayse (u1) | — | `{"status": "gecersiz_durum"}` | **200** | `{"id":"pol_5","policyNumber":"POL-2026-0005","ownerUserId":"u1","holderName":"Ayşe Yılmaz","holderTckn":"11111111110","coverage...` |
| `P5-PATCH-STATUS-ACTIVE` | `PATCH` | `/policies/pol_5` | tok_user1_ayse (u1) | — | `{"status": "active"}` | **200** | `{"id":"pol_5","policyNumber":"POL-2026-0005","ownerUserId":"u1","holderName":"Ayşe Yılmaz","holderTckn":"11111111110","coverage...` |

## 2. Bulgulara Dayanak Oluşturan Ham İstek ve Yanıt Kanıtları

Aşağıda `bulgular.md` içindeki bulgulara doğrudan referans verilen isteklerin kısaltılmamış tam istek ve yanıt içerikleri yer almaktadır.

### `P1-HEALTH-ANON` — `GET /health` → HTTP 200
- **Token / Authorization:** `(yok)`
- **Yanıt Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{
  "status": "ok",
  "service": "anadolu-guven-sigorta-api"
}
```

### `P1-AUTH-NOAUTH-/policies` — `GET /policies` → HTTP 401
- **Token / Authorization:** `(yok)`
- **Yanıt Durum Kodu:** `401`
- **Yanıt Gövdesi:**
```json
{
  "error": "Yetkisiz",
  "message": "Geçerli bir bearer token gerekli."
}
```

### `P1-AUTH-NOBEARER-/policies` — `GET /policies` → HTTP 401
- **Token / Authorization:** `tok_user1_ayse`
- **Yanıt Durum Kodu:** `401`
- **Yanıt Gövdesi:**
```json
{
  "error": "Yetkisiz",
  "message": "Geçerli bir bearer token gerekli."
}
```

### `P1-ADMIN-u1-/admin/policies` — `GET /admin/policies` → HTTP 403
- **Token / Authorization:** `Bearer tok_user1_ayse`
- **Yanıt Durum Kodu:** `403`
- **Yanıt Gövdesi:**
```json
{
  "error": "Erişim engellendi",
  "message": "Yönetici yetkisi gerekli."
}
```

### `P1-ADMIN-u1-/admin/stats` — `GET /admin/stats` → HTTP 200
- **Token / Authorization:** `Bearer tok_user1_ayse`
- **Yanıt Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{
  "totalPolicies": 5,
  "totalClaims": 7,
  "totalPremium": 9800
}
```

### `P1-ADMIN-u2-/admin/stats` — `GET /admin/stats` → HTTP 200
- **Token / Authorization:** `Bearer tok_user2_mehmet`
- **Yanıt Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{
  "totalPolicies": 5,
  "totalClaims": 7,
  "totalPremium": 9800
}
```

### `P1-ADMIN-admin-/admin/stats` — `GET /admin/stats` → HTTP 200
- **Token / Authorization:** `Bearer tok_admin_root`
- **Yanıt Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{
  "totalPolicies": 5,
  "totalClaims": 7,
  "totalPremium": 9800
}
```

### `P1-POL-GET-u1-pol_3` — `GET /policies/pol_3` → HTTP 403
- **Token / Authorization:** `Bearer tok_user1_ayse`
- **Yanıt Durum Kodu:** `403`
- **Yanıt Gövdesi:**
```json
{
  "error": "Erişim engellendi",
  "message": "Bu poliçeye erişim yetkiniz yok."
}
```

### `P1-CLM-GET-u1-clm_6` — `GET /claims/clm_6` → HTTP 403
- **Token / Authorization:** `Bearer tok_user1_ayse`
- **Yanıt Durum Kodu:** `403`
- **Yanıt Gövdesi:**
```json
{
  "error": "Erişim engellendi",
  "message": "Bu hasar talebine erişim yetkiniz yok."
}
```

### `P1-CLM-LIST-u1-all_u1` — `GET /claims` → HTTP 200
- **Token / Authorization:** `Bearer tok_user1_ayse`
- **Yanıt Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{
  "data": [
    {
      "id": "clm_1",
      "policyId": "pol_1",
      "ownerUserId": "u1",
      "amount": 12000,
      "status": "submitted",
      "description": "Çarpma hasarı",
      "createdAt": "2026-05-02T09:00:00Z"
    },
    {
      "id": "clm_2",
      "policyId": "pol_1",
      "ownerUserId": "u1",
      "amount": 8000,
      "status": "rejected",
      "description": "Cam kırığı",
      "createdAt": "2026-05-10T11:30:00Z"
    },
    {
      "id": "clm_3",
      "policyId": "pol_2",
      "ownerUserId": "u1",
      "amount": 3000,
      "status": "approved",
      "description": "Su baskını",
      "createdAt": "2026-06-01T08:15:00Z"
    },
    {
      "id": "clm_4",
      "policyId": "pol_5",
      "ownerUserId": "u1",
      "amount": 15000,
      "status": "submitted",
      "description": "Trafik kazası",
      "createdAt": "2026-06-20T14:45:00Z"
    },
    {
      "id": "clm_5",
      "policyId": "pol_2",
      "ownerUserId": "u1",
      "amount": 2000,
      "status": "submitted",
      "description": "Hırsızlık",
      "createdAt": "2026-07-03T16:05:00Z"
    }
  ],
  "meta": {
    "page": 1,
    "pageSize": 20,
    "total": 5
  }
}
```

### `P1-CLM-LIST-u1-p1_s2` — `GET /claims?page=1&pageSize=2` → HTTP 200
- **Token / Authorization:** `Bearer tok_user1_ayse`
- **Yanıt Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{
  "data": [
    {
      "id": "clm_1",
      "policyId": "pol_1",
      "ownerUserId": "u1",
      "amount": 12000,
      "status": "submitted",
      "description": "Çarpma hasarı",
      "createdAt": "2026-05-02T09:00:00Z"
    },
    {
      "id": "clm_2",
      "policyId": "pol_1",
      "ownerUserId": "u1",
      "amount": 8000,
      "status": "rejected",
      "description": "Cam kırığı",
      "createdAt": "2026-05-10T11:30:00Z"
    }
  ],
  "meta": {
    "page": 1,
    "pageSize": 2,
    "total": 2
  }
}
```

### `P1-CLM-LIST-u1-p3_s2` — `GET /claims?page=3&pageSize=2` → HTTP 200
- **Token / Authorization:** `Bearer tok_user1_ayse`
- **Yanıt Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{
  "data": [
    {
      "id": "clm_5",
      "policyId": "pol_2",
      "ownerUserId": "u1",
      "amount": 2000,
      "status": "submitted",
      "description": "Hırsızlık",
      "createdAt": "2026-07-03T16:05:00Z"
    }
  ],
  "meta": {
    "page": 3,
    "pageSize": 2,
    "total": 1
  }
}
```

### `P1-CLM-LIST-u1-p4_s2_empty` — `GET /claims?page=4&pageSize=2` → HTTP 200
- **Token / Authorization:** `Bearer tok_user1_ayse`
- **Yanıt Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{
  "data": [],
  "meta": {
    "page": 4,
    "pageSize": 2,
    "total": 0
  }
}
```

### `P1-CLM-LIST-u1-own_pol1_p1_s1` — `GET /claims?policyId=pol_1&page=1&pageSize=1` → HTTP 200
- **Token / Authorization:** `Bearer tok_user1_ayse`
- **Yanıt Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{
  "data": [
    {
      "id": "clm_1",
      "policyId": "pol_1",
      "ownerUserId": "u1",
      "amount": 12000,
      "status": "submitted",
      "description": "Çarpma hasarı",
      "createdAt": "2026-05-02T09:00:00Z"
    }
  ],
  "meta": {
    "page": 1,
    "pageSize": 1,
    "total": 1
  }
}
```

### `P1-CLM-LIST-u1-other_u2_pol3` — `GET /claims?policyId=pol_3` → HTTP 200
- **Token / Authorization:** `Bearer tok_user1_ayse`
- **Yanıt Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{
  "data": [
    {
      "id": "clm_7",
      "policyId": "pol_3",
      "ownerUserId": "u2",
      "amount": 1000,
      "status": "rejected",
      "description": "Muayene masrafı",
      "createdAt": "2026-06-11T13:00:00Z"
    }
  ],
  "meta": {
    "page": 1,
    "pageSize": 20,
    "total": 1
  }
}
```

### `P1-CLM-LIST-u1-other_u2_pol4` — `GET /claims?policyId=pol_4` → HTTP 200
- **Token / Authorization:** `Bearer tok_user1_ayse`
- **Yanıt Durum Kodu:** `200`
- **Yanıt Gövdesi:**
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
  "meta": {
    "page": 1,
    "pageSize": 20,
    "total": 1
  }
}
```

### `P1-CLM-LIST-u2-other_u1_pol1` — `GET /claims?policyId=pol_1` → HTTP 200
- **Token / Authorization:** `Bearer tok_user2_mehmet`
- **Yanıt Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{
  "data": [
    {
      "id": "clm_1",
      "policyId": "pol_1",
      "ownerUserId": "u1",
      "amount": 12000,
      "status": "submitted",
      "description": "Çarpma hasarı",
      "createdAt": "2026-05-02T09:00:00Z"
    },
    {
      "id": "clm_2",
      "policyId": "pol_1",
      "ownerUserId": "u1",
      "amount": 8000,
      "status": "rejected",
      "description": "Cam kırığı",
      "createdAt": "2026-05-10T11:30:00Z"
    }
  ],
  "meta": {
    "page": 1,
    "pageSize": 20,
    "total": 2
  }
}
```

### `P1-CLM-LIST-u1-page_0` — `GET /claims?page=0` → HTTP 200
- **Token / Authorization:** `Bearer tok_user1_ayse`
- **Yanıt Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{
  "data": [],
  "meta": {
    "page": 0,
    "pageSize": 20,
    "total": 0
  }
}
```

### `P1-CLM-LIST-u1-page_abc` — `GET /claims?page=abc` → HTTP 200
- **Token / Authorization:** `Bearer tok_user1_ayse`
- **Yanıt Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{
  "data": [],
  "meta": {
    "page": null,
    "pageSize": 20,
    "total": 0
  }
}
```

### `P1-CLM-LIST-u1-size_neg1` — `GET /claims?pageSize=-1` → HTTP 200
- **Token / Authorization:** `Bearer tok_user1_ayse`
- **Yanıt Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{
  "data": [
    {
      "id": "clm_1",
      "policyId": "pol_1",
      "ownerUserId": "u1",
      "amount": 12000,
      "status": "submitted",
      "description": "Çarpma hasarı",
      "createdAt": "2026-05-02T09:00:00Z"
    },
    {
      "id": "clm_2",
      "policyId": "pol_1",
      "ownerUserId": "u1",
      "amount": 8000,
      "status": "rejected",
      "description": "Cam kırığı",
      "createdAt": "2026-05-10T11:30:00Z"
    },
    {
      "id": "clm_3",
      "policyId": "pol_2",
      "ownerUserId": "u1",
      "amount": 3000,
      "status": "approved",
      "description": "Su baskını",
      "createdAt": "2026-06-01T08:15:00Z"
    },
    {
      "id": "clm_4",
      "policyId": "pol_5",
      "ownerUserId": "u1",
      "amount": 15000,
      "status": "submitted",
      "description": "Trafik kazası",
      "createdAt": "2026-06-20T14:45:00Z"
    }
  ],
  "meta": {
    "page": 1,
    "pageSize": -1,
    "total": 4
  }
}
```

### `P1-CLM-LIST-u1-size_101` — `GET /claims?pageSize=101` → HTTP 200
- **Token / Authorization:** `Bearer tok_user1_ayse`
- **Yanıt Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{
  "data": [
    {
      "id": "clm_1",
      "policyId": "pol_1",
      "ownerUserId": "u1",
      "amount": 12000,
      "status": "submitted",
      "description": "Çarpma hasarı",
      "createdAt": "2026-05-02T09:00:00Z"
    },
    {
      "id": "clm_2",
      "policyId": "pol_1",
      "ownerUserId": "u1",
      "amount": 8000,
      "status": "rejected",
      "description": "Cam kırığı",
      "createdAt": "2026-05-10T11:30:00Z"
    },
    {
      "id": "clm_3",
      "policyId": "pol_2",
      "ownerUserId": "u1",
      "amount": 3000,
      "status": "approved",
      "description": "Su baskını",
      "createdAt": "2026-06-01T08:15:00Z"
    },
    {
      "id": "clm_4",
      "policyId": "pol_5",
      "ownerUserId": "u1",
      "amount": 15000,
      "status": "submitted",
      "description": "Trafik kazası",
      "createdAt": "2026-06-20T14:45:00Z"
    },
    {
      "id": "clm_5",
      "policyId": "pol_2",
      "ownerUserId": "u1",
      "amount": 2000,
      "status": "submitted",
      "description": "Hırsızlık",
      "createdAt": "2026-07-03T16:05:00Z"
    }
  ],
  "meta": {
    "page": 1,
    "pageSize": 101,
    "total": 5
  }
}
```

### `P1-CLM-LIST-u1-size_abc` — `GET /claims?pageSize=abc` → HTTP 200
- **Token / Authorization:** `Bearer tok_user1_ayse`
- **Yanıt Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{
  "data": [],
  "meta": {
    "page": 1,
    "pageSize": null,
    "total": 0
  }
}
```

### `P1-CLM-LIST-admin-admin_p1_s3` — `GET /claims?page=1&pageSize=3` → HTTP 200
- **Token / Authorization:** `Bearer tok_admin_root`
- **Yanıt Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{
  "data": [
    {
      "id": "clm_1",
      "policyId": "pol_1",
      "ownerUserId": "u1",
      "amount": 12000,
      "status": "submitted",
      "description": "Çarpma hasarı",
      "createdAt": "2026-05-02T09:00:00Z"
    },
    {
      "id": "clm_2",
      "policyId": "pol_1",
      "ownerUserId": "u1",
      "amount": 8000,
      "status": "rejected",
      "description": "Cam kırığı",
      "createdAt": "2026-05-10T11:30:00Z"
    },
    {
      "id": "clm_3",
      "policyId": "pol_2",
      "ownerUserId": "u1",
      "amount": 3000,
      "status": "approved",
      "description": "Su baskını",
      "createdAt": "2026-06-01T08:15:00Z"
    }
  ],
  "meta": {
    "page": 1,
    "pageSize": 3,
    "total": 3
  }
}
```

### `P1-CLM-GET-u1-clm_1` — `GET /claims/clm_1` → HTTP 200
- **Token / Authorization:** `Bearer tok_user1_ayse`
- **Yanıt Durum Kodu:** `200`
- **Yanıt Gövdesi:**
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

### `P2A-BOLA-U1-ON-U2` — `PATCH /policies/pol_3` → HTTP 403
- **Token / Authorization:** `Bearer tok_user1_ayse`
- **Diğer İstek Başlıkları:** `{"Content-Type": "application/json"}`
- **İstek Gövdesi:**
```json
{
  "holderName": "HackU2"
}
```
- **Yanıt Durum Kodu:** `403`
- **Yanıt Gövdesi:**
```json
{
  "error": "Erişim engellendi",
  "message": "Bu poliçeye erişim yetkiniz yok."
}
```

### `P2A-MALFORMED-JSON` — `PATCH /policies/pol_5` → HTTP 400
- **Token / Authorization:** `Bearer tok_user1_ayse`
- **Diğer İstek Başlıkları:** `{"Content-Type": "application/json"}`
- **İstek Gövdesi:**
```json
{bad json
```
- **Yanıt Durum Kodu:** `400`
- **Yanıt Gövdesi:**
```json
{
  "error": "Geçersiz JSON",
  "detail": "Expected property name or '}' in JSON at position 1 (line 1 column 2)",
  "stack": "SyntaxError: Expected property name or '}' in JSON at position 1 (line 1 column 2)\n    at JSON.parse (<anonymous>)\n    at Server.<anonymous> (C:\\eval\\servers\\R13\\server.js:155:27)\n    at process.processTicksAndRejections (node:internal/process/task_queues:104:5)"
}
```

### `P2A-ARRAY-BODY` — `PATCH /policies/pol_5` → HTTP 200
- **Token / Authorization:** `Bearer tok_user1_ayse`
- **Diğer İstek Başlıkları:** `{"Content-Type": "application/json"}`
- **İstek Gövdesi:**
```json
[]
```
- **Yanıt Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{
  "id": "pol_5",
  "policyNumber": "POL-2026-0005",
  "ownerUserId": "u1",
  "holderName": "Ayşe Yılmaz",
  "holderTckn": "11111111110",
  "coverageType": "trafik",
  "premium": 1800,
  "coverageLimit": 75000,
  "status": "active",
  "agentName": null,
  "startDate": "2026-04-01",
  "endDate": "2027-03-31"
}
```

### `P2A-HOLDER-INT` — `PATCH /policies/pol_5` → HTTP 200
- **Token / Authorization:** `Bearer tok_user1_ayse`
- **Diğer İstek Başlıkları:** `{"Content-Type": "application/json"}`
- **İstek Gövdesi:**
```json
{
  "holderName": 12345
}
```
- **Yanıt Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{
  "id": "pol_5",
  "policyNumber": "POL-2026-0005",
  "ownerUserId": "u1",
  "holderName": 12345,
  "holderTckn": "11111111110",
  "coverageType": "trafik",
  "premium": 1800,
  "coverageLimit": 75000,
  "status": "active",
  "agentName": null,
  "startDate": "2026-04-01",
  "endDate": "2027-03-31"
}
```

### `P2A-HOLDER-NULL` — `PATCH /policies/pol_5` → HTTP 200
- **Token / Authorization:** `Bearer tok_user1_ayse`
- **Diğer İstek Başlıkları:** `{"Content-Type": "application/json"}`
- **İstek Gövdesi:**
```json
{
  "holderName": null
}
```
- **Yanıt Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{
  "id": "pol_5",
  "policyNumber": "POL-2026-0005",
  "ownerUserId": "u1",
  "holderName": null,
  "holderTckn": "11111111110",
  "coverageType": "trafik",
  "premium": 1800,
  "coverageLimit": 75000,
  "status": "active",
  "agentName": null,
  "startDate": "2026-04-01",
  "endDate": "2027-03-31"
}
```

### `P2A-HOLDER-EMPTY` — `PATCH /policies/pol_5` → HTTP 200
- **Token / Authorization:** `Bearer tok_user1_ayse`
- **Diğer İstek Başlıkları:** `{"Content-Type": "application/json"}`
- **İstek Gövdesi:**
```json
{
  "holderName": ""
}
```
- **Yanıt Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{
  "id": "pol_5",
  "policyNumber": "POL-2026-0005",
  "ownerUserId": "u1",
  "holderName": "",
  "holderTckn": "11111111110",
  "coverageType": "trafik",
  "premium": 1800,
  "coverageLimit": 75000,
  "status": "active",
  "agentName": null,
  "startDate": "2026-04-01",
  "endDate": "2027-03-31"
}
```

### `P2A-AGENT-INT` — `PATCH /policies/pol_5` → HTTP 200
- **Token / Authorization:** `Bearer tok_user1_ayse`
- **Diğer İstek Başlıkları:** `{"Content-Type": "application/json"}`
- **İstek Gövdesi:**
```json
{
  "agentName": 12345
}
```
- **Yanıt Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{
  "id": "pol_5",
  "policyNumber": "POL-2026-0005",
  "ownerUserId": "u1",
  "holderName": "   ",
  "holderTckn": "11111111110",
  "coverageType": "trafik",
  "premium": 1800,
  "coverageLimit": 75000,
  "status": "active",
  "agentName": 12345,
  "startDate": "2026-04-01",
  "endDate": "2027-03-31"
}
```

### `P2A-AGENT-BOOL` — `PATCH /policies/pol_5` → HTTP 200
- **Token / Authorization:** `Bearer tok_user1_ayse`
- **Diğer İstek Başlıkları:** `{"Content-Type": "application/json"}`
- **İstek Gövdesi:**
```json
{
  "agentName": true
}
```
- **Yanıt Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{
  "id": "pol_5",
  "policyNumber": "POL-2026-0005",
  "ownerUserId": "u1",
  "holderName": "   ",
  "holderTckn": "11111111110",
  "coverageType": "trafik",
  "premium": 1800,
  "coverageLimit": 75000,
  "status": "active",
  "agentName": true,
  "startDate": "2026-04-01",
  "endDate": "2027-03-31"
}
```

### `P2A-RO-STATUS` — `PATCH /policies/pol_5` → HTTP 200
- **Token / Authorization:** `Bearer tok_user1_ayse`
- **Diğer İstek Başlıkları:** `{"Content-Type": "application/json"}`
- **İstek Gövdesi:**
```json
{
  "status": "cancelled"
}
```
- **Yanıt Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{
  "id": "pol_5",
  "policyNumber": "POL-2026-0005",
  "ownerUserId": "u1",
  "holderName": "Ayşe Yılmaz",
  "holderTckn": "11111111110",
  "coverageType": "trafik",
  "premium": 1800,
  "coverageLimit": 75000,
  "status": "cancelled",
  "agentName": null,
  "startDate": "2026-04-01",
  "endDate": "2027-03-31"
}
```

### `P2A-RO-MIXED` — `PATCH /policies/pol_5` → HTTP 200
- **Token / Authorization:** `Bearer tok_user1_ayse`
- **Diğer İstek Başlıkları:** `{"Content-Type": "application/json"}`
- **İstek Gövdesi:**
```json
{
  "holderName": "Ayşe Yılmaz",
  "premium": 5,
  "coverageLimit": 888888,
  "status": "pending"
}
```
- **Yanıt Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{
  "id": "pol_5",
  "policyNumber": "POL-2026-0005",
  "ownerUserId": "u1",
  "holderName": "Ayşe Yılmaz",
  "holderTckn": "11111111110",
  "coverageType": "trafik",
  "premium": 1800,
  "coverageLimit": 75000,
  "status": "pending",
  "agentName": null,
  "startDate": "2026-04-01",
  "endDate": "2027-03-31"
}
```

### `P2A-CHECK-pol_5` — `GET /policies/pol_5` → HTTP 200
- **Token / Authorization:** `Bearer tok_admin_root`
- **Yanıt Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{
  "id": "pol_5",
  "policyNumber": "POL-2026-0005",
  "ownerUserId": "u1",
  "holderName": "Ayşe Yılmaz",
  "holderTckn": "11111111110",
  "coverageType": "trafik",
  "premium": 1800,
  "coverageLimit": 75000,
  "status": "pending",
  "agentName": null,
  "startDate": "2026-04-01",
  "endDate": "2027-03-31"
}
```

### `P2B-MALFORMED-JSON` — `POST /claims` → HTTP 400
- **Token / Authorization:** `Bearer tok_user1_ayse`
- **Diğer İstek Başlıkları:** `{"Content-Type": "application/json"}`
- **İstek Gövdesi:**
```json
{bad json
```
- **Yanıt Durum Kodu:** `400`
- **Yanıt Gövdesi:**
```json
{
  "error": "Geçersiz JSON",
  "detail": "Expected property name or '}' in JSON at position 1 (line 1 column 2)",
  "stack": "SyntaxError: Expected property name or '}' in JSON at position 1 (line 1 column 2)\n    at JSON.parse (<anonymous>)\n    at Server.<anonymous> (C:\\eval\\servers\\R13\\server.js:216:25)\n    at process.processTicksAndRejections (node:internal/process/task_queues:104:5)"
}
```

### `P2B-POLICYID-INT` — `POST /claims` → HTTP 404
- **Token / Authorization:** `Bearer tok_user1_ayse`
- **Diğer İstek Başlıkları:** `{"Content-Type": "application/json"}`
- **İstek Gövdesi:**
```json
{
  "policyId": 123,
  "amount": 100
}
```
- **Yanıt Durum Kodu:** `404`
- **Yanıt Gövdesi:**
```json
{
  "error": "Bulunamadı",
  "message": "Poliçe bulunamadı."
}
```

### `P2B-DESC-INT` — `POST /claims` → HTTP 200
- **Token / Authorization:** `Bearer tok_user1_ayse`
- **Diğer İstek Başlıkları:** `{"Content-Type": "application/json"}`
- **İstek Gövdesi:**
```json
{
  "policyId": "pol_1",
  "amount": 100,
  "description": 12345
}
```
- **Yanıt Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{
  "id": "clm_8",
  "policyId": "pol_1",
  "ownerUserId": "u1",
  "amount": 100,
  "status": "submitted",
  "description": "",
  "createdAt": "2026-08-01T00:00:00Z"
}
```

### `P2B-BOLA-U1-ON-POL4` — `POST /claims` → HTTP 403
- **Token / Authorization:** `Bearer tok_user1_ayse`
- **Diğer İstek Başlıkları:** `{"Content-Type": "application/json"}`
- **İstek Gövdesi:**
```json
{
  "policyId": "pol_4",
  "amount": 500,
  "description": "BOLA test u1->pol_4"
}
```
- **Yanıt Durum Kodu:** `403`
- **Yanıt Gövdesi:**
```json
{
  "error": "Erişim engellendi",
  "message": "Bu poliçe için hasar talebi oluşturamazsınız."
}
```

### `P2B-ADMIN-ON-POL4` — `POST /claims` → HTTP 200
- **Token / Authorization:** `Bearer tok_admin_root`
- **Diğer İstek Başlıkları:** `{"Content-Type": "application/json"}`
- **İstek Gövdesi:**
```json
{
  "policyId": "pol_4",
  "amount": 500,
  "description": "Admin claim on pol_4"
}
```
- **Yanıt Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{
  "id": "clm_9",
  "policyId": "pol_4",
  "ownerUserId": "admin",
  "amount": 500,
  "status": "submitted",
  "description": "Admin claim on pol_4",
  "createdAt": "2026-08-01T00:00:00Z"
}
```

### `P2B-CHK-POL4-U2` — `GET /claims?policyId=pol_4` → HTTP 200
- **Token / Authorization:** `Bearer tok_user2_mehmet`
- **Yanıt Durum Kodu:** `200`
- **Yanıt Gövdesi:**
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
    },
    {
      "id": "clm_9",
      "policyId": "pol_4",
      "ownerUserId": "admin",
      "amount": 500,
      "status": "submitted",
      "description": "Admin claim on pol_4",
      "createdAt": "2026-08-01T00:00:00Z"
    }
  ],
  "meta": {
    "page": 1,
    "pageSize": 20,
    "total": 2
  }
}
```

### `P2B-AMT-NEG` — `POST /claims` → HTTP 200
- **Token / Authorization:** `Bearer tok_user1_ayse`
- **Diğer İstek Başlıkları:** `{"Content-Type": "application/json"}`
- **İstek Gövdesi:**
```json
{
  "policyId": "pol_1",
  "amount": -100,
  "description": "negatif"
}
```
- **Yanıt Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{
  "id": "clm_10",
  "policyId": "pol_1",
  "ownerUserId": "u1",
  "amount": -100,
  "status": "submitted",
  "description": "negatif",
  "createdAt": "2026-08-01T00:00:00Z"
}
```

### `P2B-AMT-ZERO` — `POST /claims` → HTTP 200
- **Token / Authorization:** `Bearer tok_user1_ayse`
- **Diğer İstek Başlıkları:** `{"Content-Type": "application/json"}`
- **İstek Gövdesi:**
```json
{
  "policyId": "pol_1",
  "amount": 0,
  "description": "sıfır"
}
```
- **Yanıt Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{
  "id": "clm_11",
  "policyId": "pol_1",
  "ownerUserId": "u1",
  "amount": 0,
  "status": "submitted",
  "description": "sıfır",
  "createdAt": "2026-08-01T00:00:00Z"
}
```

### `P2B-AMT-0_99` — `POST /claims` → HTTP 200
- **Token / Authorization:** `Bearer tok_user1_ayse`
- **Diğer İstek Başlıkları:** `{"Content-Type": "application/json"}`
- **İstek Gövdesi:**
```json
{
  "policyId": "pol_1",
  "amount": 0.99,
  "description": "0.99"
}
```
- **Yanıt Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{
  "id": "clm_12",
  "policyId": "pol_1",
  "ownerUserId": "u1",
  "amount": 0.99,
  "status": "submitted",
  "description": "0.99",
  "createdAt": "2026-08-01T00:00:00Z"
}
```

### `P2B-AMT-1` — `POST /claims` → HTTP 200
- **Token / Authorization:** `Bearer tok_user1_ayse`
- **Diğer İstek Başlıkları:** `{"Content-Type": "application/json"}`
- **İstek Gövdesi:**
```json
{
  "policyId": "pol_1",
  "amount": 1,
  "description": "min sınır 1"
}
```
- **Yanıt Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{
  "id": "clm_13",
  "policyId": "pol_1",
  "ownerUserId": "u1",
  "amount": 1,
  "status": "submitted",
  "description": "min sınır 1",
  "createdAt": "2026-08-01T00:00:00Z"
}
```

### `P2B-AMT-AT-LIMIT` — `POST /claims` → HTTP 200
- **Token / Authorization:** `Bearer tok_user1_ayse`
- **Diğer İstek Başlıkları:** `{"Content-Type": "application/json"}`
- **İstek Gövdesi:**
```json
{
  "policyId": "pol_1",
  "amount": 50000,
  "description": "tam limit"
}
```
- **Yanıt Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{
  "id": "clm_16",
  "policyId": "pol_1",
  "ownerUserId": "u1",
  "amount": 50000,
  "status": "submitted",
  "description": "tam limit",
  "createdAt": "2026-08-01T00:00:00Z"
}
```

### `P2B-AMT-OVER-LIMIT-0_01` — `POST /claims` → HTTP 200
- **Token / Authorization:** `Bearer tok_user1_ayse`
- **Diğer İstek Başlıkları:** `{"Content-Type": "application/json"}`
- **İstek Gövdesi:**
```json
{
  "policyId": "pol_1",
  "amount": 50000.01,
  "description": "limit+0.01"
}
```
- **Yanıt Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{
  "id": "clm_15",
  "policyId": "pol_1",
  "ownerUserId": "u1",
  "amount": 50000.01,
  "status": "submitted",
  "description": "limit+0.01",
  "createdAt": "2026-08-01T00:00:00Z"
}
```

### `P2B-AMT-OVER-LIMIT-1` — `POST /claims` → HTTP 200
- **Token / Authorization:** `Bearer tok_user1_ayse`
- **Diğer İstek Başlıkları:** `{"Content-Type": "application/json"}`
- **İstek Gövdesi:**
```json
{
  "policyId": "pol_1",
  "amount": 50001,
  "description": "limit+1"
}
```
- **Yanıt Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{
  "id": "clm_14",
  "policyId": "pol_1",
  "ownerUserId": "u1",
  "amount": 50001,
  "status": "submitted",
  "description": "limit+1",
  "createdAt": "2026-08-01T00:00:00Z"
}
```

### `P2B-AMT-CUMUL-CHECK` — `POST /claims` → HTTP 200
- **Token / Authorization:** `Bearer tok_user1_ayse`
- **Diğer İstek Başlıkları:** `{"Content-Type": "application/json"}`
- **İstek Gövdesi:**
```json
{
  "policyId": "pol_2",
  "amount": 96000,
  "description": "kümülatif 3000+2000+96000=101000 > 100000"
}
```
- **Yanıt Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{
  "id": "clm_17",
  "policyId": "pol_2",
  "ownerUserId": "u1",
  "amount": 96000,
  "status": "submitted",
  "description": "kümülatif 3000+2000+96000=101000 > 100000",
  "createdAt": "2026-08-01T00:00:00Z"
}
```

### `P2B-CANCELLED-POLICY` — `POST /claims` → HTTP 200
- **Token / Authorization:** `Bearer tok_user2_mehmet`
- **Diğer İstek Başlıkları:** `{"Content-Type": "application/json"}`
- **İstek Gövdesi:**
```json
{
  "policyId": "pol_3",
  "amount": 500,
  "description": "İptal poliçeye hasar talebi"
}
```
- **Yanıt Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{
  "id": "clm_18",
  "policyId": "pol_3",
  "ownerUserId": "u2",
  "amount": 500,
  "status": "submitted",
  "description": "İptal poliçeye hasar talebi",
  "createdAt": "2026-08-01T00:00:00Z"
}
```

### `P2B-MASS-ASSIGN` — `POST /claims` → HTTP 200
- **Token / Authorization:** `Bearer tok_user1_ayse`
- **Diğer İstek Başlıkları:** `{"Content-Type": "application/json"}`
- **İstek Gövdesi:**
```json
{
  "policyId": "pol_5",
  "amount": 100,
  "status": "approved",
  "ownerUserId": "u2",
  "id": "clm_hack999",
  "claimNumber": "CLM-HACK-999"
}
```
- **Yanıt Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{
  "id": "clm_19",
  "policyId": "pol_5",
  "ownerUserId": "u1",
  "amount": 100,
  "status": "submitted",
  "description": "",
  "createdAt": "2026-08-01T00:00:00Z"
}
```

### `P2B-IDEM-1` — `POST /claims` → HTTP 200
- **Token / Authorization:** `Bearer tok_user1_ayse`
- **Diğer İstek Başlıkları:** `{"Idempotency-Key": "idem-key-101", "Content-Type": "application/json"}`
- **İstek Gövdesi:**
```json
{
  "policyId": "pol_5",
  "amount": 250,
  "description": "Idem 1"
}
```
- **Yanıt Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{
  "id": "clm_20",
  "policyId": "pol_5",
  "ownerUserId": "u1",
  "amount": 250,
  "status": "submitted",
  "description": "Idem 1",
  "createdAt": "2026-08-01T00:00:00Z"
}
```

### `P2B-IDEM-2-REPEAT` — `POST /claims` → HTTP 200
- **Token / Authorization:** `Bearer tok_user1_ayse`
- **Diğer İstek Başlıkları:** `{"Idempotency-Key": "idem-key-101", "Content-Type": "application/json"}`
- **İstek Gövdesi:**
```json
{
  "policyId": "pol_5",
  "amount": 250,
  "description": "Idem 1"
}
```
- **Yanıt Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{
  "id": "clm_21",
  "policyId": "pol_5",
  "ownerUserId": "u1",
  "amount": 250,
  "status": "submitted",
  "description": "Idem 1",
  "createdAt": "2026-08-01T00:00:00Z"
}
```

### `P2B-IDEM-FAIL-FIRST` — `POST /claims` → HTTP 200
- **Token / Authorization:** `Bearer tok_user1_ayse`
- **Diğer İstek Başlıkları:** `{"Idempotency-Key": "idem-fail-303", "Content-Type": "application/json"}`
- **İstek Gövdesi:**
```json
{
  "policyId": "pol_5",
  "amount": 999999,
  "description": "Limit aşımı"
}
```
- **Yanıt Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{
  "id": "clm_24",
  "policyId": "pol_5",
  "ownerUserId": "u1",
  "amount": 999999,
  "status": "submitted",
  "description": "Limit aşımı",
  "createdAt": "2026-08-01T00:00:00Z"
}
```

### `P2B-IDEM-RACE-1` — `POST /claims` → HTTP 200
- **Token / Authorization:** `Bearer tok_user1_ayse`
- **Diğer İstek Başlıkları:** `{"Idempotency-Key": "idem-race-202", "Content-Type": "application/json"}`
- **İstek Gövdesi:**
```json
{
  "policyId": "pol_5",
  "amount": 123,
  "description": "Yarış testi"
}
```
- **Yanıt Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{
  "id": "clm_27",
  "policyId": "pol_5",
  "ownerUserId": "u1",
  "amount": 123,
  "status": "submitted",
  "description": "Yarış testi",
  "createdAt": "2026-08-01T00:00:00Z"
}
```

### `P2B-IDEM-RACE-2` — `POST /claims` → HTTP 200
- **Token / Authorization:** `Bearer tok_user1_ayse`
- **Diğer İstek Başlıkları:** `{"Idempotency-Key": "idem-race-202", "Content-Type": "application/json"}`
- **İstek Gövdesi:**
```json
{
  "policyId": "pol_5",
  "amount": 123,
  "description": "Yarış testi"
}
```
- **Yanıt Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{
  "id": "clm_28",
  "policyId": "pol_5",
  "ownerUserId": "u1",
  "amount": 123,
  "status": "submitted",
  "description": "Yarış testi",
  "createdAt": "2026-08-01T00:00:00Z"
}
```

### `P2B-IDEM-RACE-3` — `POST /claims` → HTTP 200
- **Token / Authorization:** `Bearer tok_user1_ayse`
- **Diğer İstek Başlıkları:** `{"Idempotency-Key": "idem-race-202", "Content-Type": "application/json"}`
- **İstek Gövdesi:**
```json
{
  "policyId": "pol_5",
  "amount": 123,
  "description": "Yarış testi"
}
```
- **Yanıt Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{
  "id": "clm_26",
  "policyId": "pol_5",
  "ownerUserId": "u1",
  "amount": 123,
  "status": "submitted",
  "description": "Yarış testi",
  "createdAt": "2026-08-01T00:00:00Z"
}
```

### `P3-U2-LIST-CLAIMS` — `GET /claims` → HTTP 200
- **Token / Authorization:** `Bearer tok_user2_mehmet`
- **Yanıt Durum Kodu:** `200`
- **Yanıt Gövdesi:**
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
    },
    {
      "id": "clm_7",
      "policyId": "pol_3",
      "ownerUserId": "u2",
      "amount": 1000,
      "status": "rejected",
      "description": "Muayene masrafı",
      "createdAt": "2026-06-11T13:00:00Z"
    },
    {
      "id": "clm_18",
      "policyId": "pol_3",
      "ownerUserId": "u2",
      "amount": 500,
      "status": "submitted",
      "description": "İptal poliçeye hasar talebi",
      "createdAt": "2026-08-01T00:00:00Z"
    },
    {
      "id": "clm_23",
      "policyId": "pol_4",
      "ownerUserId": "u2",
      "amount": 333,
      "status": "submitted",
      "description": "Başka kullanıcı aynı key",
      "createdAt": "2026-08-01T00:00:00Z"
    }
  ],
  "meta": {
    "page": 1,
    "pageSize": 20,
    "total": 4
  }
}
```

### `P3-U2-GET-CLM9` — `GET /claims/clm_9` → HTTP 403
- **Token / Authorization:** `Bearer tok_user2_mehmet`
- **Yanıt Durum Kodu:** `403`
- **Yanıt Gövdesi:**
```json
{
  "error": "Erişim engellendi",
  "message": "Bu hasar talebine erişim yetkiniz yok."
}
```

### `P3-U2-PAGE1-SIZE2` — `GET /claims?page=1&pageSize=2` → HTTP 200
- **Token / Authorization:** `Bearer tok_user2_mehmet`
- **Yanıt Durum Kodu:** `200`
- **Yanıt Gövdesi:**
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
    },
    {
      "id": "clm_7",
      "policyId": "pol_3",
      "ownerUserId": "u2",
      "amount": 1000,
      "status": "rejected",
      "description": "Muayene masrafı",
      "createdAt": "2026-06-11T13:00:00Z"
    }
  ],
  "meta": {
    "page": 1,
    "pageSize": 2,
    "total": 2
  }
}
```

### `P3-CLM-DESC-NULL` — `POST /claims` → HTTP 200
- **Token / Authorization:** `Bearer tok_user1_ayse`
- **Diğer İstek Başlıkları:** `{"Content-Type": "application/json"}`
- **İstek Gövdesi:**
```json
{
  "policyId": "pol_5",
  "amount": 10,
  "description": null
}
```
- **Yanıt Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{
  "id": "clm_35",
  "policyId": "pol_5",
  "ownerUserId": "u1",
  "amount": 10,
  "status": "submitted",
  "description": "",
  "createdAt": "2026-08-01T00:00:00Z"
}
```

### `P3-PATCH-UNKNOWN-ONLY` — `PATCH /policies/pol_5` → HTTP 200
- **Token / Authorization:** `Bearer tok_user1_ayse`
- **Diğer İstek Başlıkları:** `{"Content-Type": "application/json"}`
- **İstek Gövdesi:**
```json
{
  "unknownField": "abc"
}
```
- **Yanıt Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{
  "id": "pol_5",
  "policyNumber": "POL-2026-0005",
  "ownerUserId": "u1",
  "holderName": "Ayşe Yılmaz",
  "holderTckn": "11111111110",
  "coverageType": "trafik",
  "premium": 1800,
  "coverageLimit": 75000,
  "status": "active",
  "agentName": null,
  "startDate": "2026-04-01",
  "endDate": "2027-03-31"
}
```

### `P3-POST-UNKNOWN-FIELD` — `POST /claims` → HTTP 200
- **Token / Authorization:** `Bearer tok_user1_ayse`
- **Diğer İstek Başlıkları:** `{"Content-Type": "application/json"}`
- **İstek Gövdesi:**
```json
{
  "policyId": "pol_5",
  "amount": 15,
  "extraField": "abc"
}
```
- **Yanıt Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{
  "id": "clm_37",
  "policyId": "pol_5",
  "ownerUserId": "u1",
  "amount": 15,
  "status": "submitted",
  "description": "",
  "createdAt": "2026-08-01T00:00:00Z"
}
```

### `P3-ADMIN-SIZE-NEG1` — `GET /claims?pageSize=-1` → HTTP 200
- **Token / Authorization:** `Bearer tok_admin_root`
- **Yanıt Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{
  "data": [
    {
      "id": "clm_1",
      "policyId": "pol_1",
      "ownerUserId": "u1",
      "amount": 12000,
      "status": "submitted",
      "description": "Çarpma hasarı",
      "createdAt": "2026-05-02T09:00:00Z"
    },
    {
      "id": "clm_2",
      "policyId": "pol_1",
      "ownerUserId": "u1",
      "amount": 8000,
      "status": "rejected",
      "description": "Cam kırığı",
      "createdAt": "2026-05-10T11:30:00Z"
    },
    {
      "id": "clm_3",
      "policyId": "pol_2",
      "ownerUserId": "u1",
      "amount": 3000,
      "status": "approved",
      "description": "Su baskını",
      "createdAt": "2026-06-01T08:15:00Z"
    },
    {
      "id": "clm_4",
      "policyId": "pol_5",
      "ownerUserId": "u1",
      "amount": 15000,
      "status": "submitted",
      "description": "Trafik kazası",
      "createdAt": "2026-06-20T14:45:00Z"
    },
    {
      "id": "clm_5",
      "policyId": "pol_2",
      "ownerUserId": "u1",
      "amount": 2000,
      "status": "submitted",
      "description": "Hırsızlık",
      "createdAt": "2026-07-03T16:05:00Z"
    },
    {
      "id": "clm_6",
      "policyId": "pol_4",
      "ownerUserId": "u2",
      "amount": 5000,
      "status": "approved",
      "description": "Çarpma hasarı",
      "createdAt": "2026-05-18T10:20:00Z"
    },
    {
      "id": "clm_7",
      "policyId": "pol_3",
      "ownerUserId": "u2",
      "amount": 1000,
      "status": "rejected",
      "description": "Muayene masrafı",
      "createdAt": "2026-06-11T13:00:00Z"
    },
    {
      "id": "clm_8",
      "policyId": "pol_1",
      "ownerUserId": "u1",
      "amount": 100,
      "status": "submitted",
      "description": "",
      "createdAt": "2026-08-01T00:00:00Z"
    },
    {
      "id": "clm_9",
      "policyId": "pol_4",
      "ownerUserId": "admin",
      "amount": 500,
      "status": "submitted",
      "description": "Admin claim on pol_4",
      "createdAt": "2026-08-01T00:00:00Z"
    },
    {
      "id": "clm_10",
      "policyId": "pol_1",
      "ownerUserId": "u1",
      "amount": -100,
      "status": "submitted",
      "description": "negatif",
      "createdAt": "2026-08-01T00:00:00Z"
    },
    {
      "id": "clm_11",
      "policyId": "pol_1",
      "ownerUserId": "u1",
      "amount": 0,
      "status": "submitted",
      "description": "sıfır",
      "createdAt": "2026-08-01T00:00:00Z"
    },
    {
      "id": "clm_12",
      "policyId": "pol_1",
      "ownerUserId": "u1",
      "amount": 0.99,
      "status": "submitted",
      "description": "0.99",
      "createdAt": "2026-08-01T00:00:00Z"
    },
    {
      "id": "clm_13",
      "policyId": "pol_1",
      "ownerUserId": "u1",
      "amount": 1,
      "status": "submitted",
      "description": "min sınır 1",
      "createdAt": "2026-08-01T00:00:00Z"
    },
    {
      "id": "clm_14",
      "policyId": "pol_1",
      "ownerUserId": "u1",
      "amount": 50001,
      "status": "submitted",
      "description": "limit+1",
      "createdAt": "2026-08-01T00:00:00Z"
    },
    {
      "id": "clm_15",
      "policyId": "pol_1",
      "ownerUserId": "u1",
      "amount": 50000.01,
      "status": "submitted",
      "description": "limit+0.01",
      "createdAt": "2026-08-01T00:00:00Z"
    },
    {
      "id": "clm_16",
      "policyId": "pol_1",
      "ownerUserId": "u1",
      "amount": 50000,
      "status": "submitted",
      "description": "tam limit",
      "createdAt": "2026-08-01T00:00:00Z"
    },
    {
      "id": "clm_17",
      "policyId": "pol_2",
      "ownerUserId": "u1",
      "amount": 96000,
      "status": "submitted",
      "description": "kümülatif 3000+2000+96000=101000 > 100000",
      "createdAt": "2026-08-01T00:00:00Z"
    },
    {
      "id": "clm_18",
      "policyId": "pol_3",
      "ownerUserId": "u2",
      "amount": 500,
      "status": "submitted",
      "description": "İptal poliçeye hasar talebi",
      "createdAt": "2026-08-01T00:00:00Z"
    },
    {
      "id": "clm_19",
      "policyId": "pol_5",
      "ownerUserId": "u1",
      "amount": 100,
      "status": "submitted",
      "description": "",
      "createdAt": "2026-08-01T00:00:00Z"
    },
    {
      "id": "clm_20",
      "policyId": "pol_5",
      "ownerUserId": "u1",
      "amount": 250,
      "status": "submitted",
      "description": "Idem 1",
      "createdAt": "2026-08-01T00:00:00Z"
    },
    {
      "id": "clm_21",
      "policyId": "pol_5",
      "ownerUserId": "u1",
      "amount": 250,
      "status": "submitted",
      "description": "Idem 1",
      "createdAt": "2026-08-01T00:00:00Z"
    },
    {
      "id": "clm_22",
      "policyId": "pol_5",
      "ownerUserId": "u1",
      "amount": 777,
      "status": "submitted",
      "description": "Farklı gövde",
      "createdAt": "2026-08-01T00:00:00Z"
    },
    {
      "id": "clm_23",
      "policyId": "pol_4",
      "ownerUserId": "u2",
      "amount": 333,
      "status": "submitted",
      "description": "Başka kullanıcı aynı key",
      "createdAt": "2026-08-01T00:00:00Z"
    },
    {
      "id": "clm_24",
      "policyId": "pol_5",
      "ownerUserId": "u1",
      "amount": 999999,
      "status": "submitted",
      "description": "Limit aşımı",
      "createdAt": "2026-08-01T00:00:00Z"
    },
    {
      "id": "clm_25",
      "policyId": "pol_5",
      "ownerUserId": "u1",
      "amount": 150,
      "status": "submitted",
      "description": "Geçerli deneme",
      "createdAt": "2026-08-01T00:00:00Z"
    },
    {
      "id": "clm_26",
      "policyId": "pol_5",
      "ownerUserId": "u1",
      "amount": 123,
      "status": "submitted",
      "description": "Yarış testi",
      "createdAt": "2026-08-01T00:00:00Z"
    },
    {
      "id": "clm_27",
      "policyId": "pol_5",
      "ownerUserId": "u1",
      "amount": 123,
      "status": "submitted",
      "description": "Yarış testi",
      "createdAt": "2026-08-01T00:00:00Z"
    },
    {
      "id": "clm_28",
      "policyId": "pol_5",
      "ownerUserId": "u1",
      "amount": 123,
      "status": "submitted",
      "description": "Yarış testi",
      "createdAt": "2026-08-01T00:00:00Z"
    },
    {
      "id": "clm_29",
      "policyId": "pol_5",
      "ownerUserId": "u1",
      "amount": 222,
      "status": "submitted",
      "description": "Anahtarsız tekrar",
      "createdAt": "2026-08-01T00:00:00Z"
    },
    {
      "id": "clm_30",
      "policyId": "pol_5",
      "ownerUserId": "u1",
      "amount": 222,
      "status": "submitted",
      "description": "Anahtarsız tekrar",
      "createdAt": "2026-08-01T00:00:00Z"
    },
    {
      "id": "clm_31",
      "policyId": "pol_5",
      "ownerUserId": "u1",
      "amount": 10,
      "status": "submitted",
      "description": "<script>alert(1)</script>",
      "createdAt": "2026-08-01T00:00:00Z"
    },
    {
      "id": "clm_32",
      "policyId": "pol_5",
      "ownerUserId": "u1",
      "amount": 10,
      "status": "submitted",
      "description": "' OR '1'='1' --",
      "createdAt": "2026-08-01T00:00:00Z"
    },
    {
      "id": "clm_33",
      "policyId": "pol_5",
      "ownerUserId": "u1",
      "amount": 10,
      "status": "submitted",
      "description": "",
      "createdAt": "2026-08-01T00:00:00Z"
    },
    {
      "id": "clm_34",
      "policyId": "pol_5",
      "ownerUserId": "u1",
      "amount": 50,
      "status": "submitted",
      "description": "",
      "createdAt": "2026-08-01T00:00:00Z"
    },
    {
      "id": "clm_35",
      "policyId": "pol_5",
      "ownerUserId": "u1",
      "amount": 10,
      "status": "submitted",
      "description": "",
      "createdAt": "2026-08-01T00:00:00Z"
    },
    {
      "id": "clm_36",
      "policyId": "pol_5",
      "ownerUserId": "u1",
      "amount": 10,
      "status": "submitted",
      "description": "",
      "createdAt": "2026-08-01T00:00:00Z"
    }
  ],
  "meta": {
    "page": 1,
    "pageSize": -1,
    "total": 36
  }
}
```

### `P3-GET-CLM8` — `GET /claims/clm_8` → HTTP 200
- **Token / Authorization:** `Bearer tok_user1_ayse`
- **Yanıt Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{
  "id": "clm_8",
  "policyId": "pol_1",
  "ownerUserId": "u1",
  "amount": 100,
  "status": "submitted",
  "description": "",
  "createdAt": "2026-08-01T00:00:00Z"
}
```

### `P4-CLM-1E309` — `POST /claims` → HTTP 200
- **Token / Authorization:** `Bearer tok_user1_ayse`
- **İstek Gövdesi:**
```json
{"policyId": "pol_5", "amount": 1e309}
```
- **Yanıt Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{
  "id": "clm_38",
  "policyId": "pol_5",
  "ownerUserId": "u1",
  "amount": null,
  "status": "submitted",
  "description": "",
  "createdAt": "2026-08-01T00:00:00Z"
}
```

### `P4-CLM-NAN` — `POST /claims` → HTTP 400
- **Token / Authorization:** `Bearer tok_user1_ayse`
- **İstek Gövdesi:**
```json
{"policyId": "pol_5", "amount": NaN}
```
- **Yanıt Durum Kodu:** `400`
- **Yanıt Gövdesi:**
```json
{
  "error": "Geçersiz JSON",
  "detail": "Unexpected token 'N', ...\"\"amount\": NaN}\" is not valid JSON",
  "stack": "SyntaxError: Unexpected token 'N', ...\"\"amount\": NaN}\" is not valid JSON\n    at JSON.parse (<anonymous>)\n    at Server.<anonymous> (C:\\eval\\servers\\R13\\server.js:216:25)\n    at process.processTicksAndRejections (node:internal/process/task_queues:104:5)"
}
```

### `P4-CLM-FLOAT` — `POST /claims` → HTTP 200
- **Token / Authorization:** `Bearer tok_user1_ayse`
- **İstek Gövdesi:**
```json
{
  "policyId": "pol_5",
  "amount": 10.5,
  "description": "Ondalık tutar"
}
```
- **Yanıt Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{
  "id": "clm_39",
  "policyId": "pol_5",
  "ownerUserId": "u1",
  "amount": 10.5,
  "status": "submitted",
  "description": "Ondalık tutar",
  "createdAt": "2026-08-01T00:00:00Z"
}
```

### `P4-GET-STATS-CHECK` — `GET /admin/stats` → HTTP 200
- **Token / Authorization:** `Bearer tok_user1_ayse`
- **Yanıt Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{
  "totalPolicies": 5,
  "totalClaims": 39,
  "totalPremium": 9800
}
```

### `P5-UNAUTH-MALFORMED-POST` — `POST /claims` → HTTP 401
- **Token / Authorization:** `(yok)`
- **İstek Gövdesi:**
```json
{bad
```
- **Yanıt Durum Kodu:** `401`
- **Yanıt Gövdesi:**
```json
{
  "error": "Yetkisiz",
  "message": "Geçerli bir bearer token gerekli."
}
```

### `P5-BOLA-MALFORMED-PATCH` — `PATCH /policies/pol_3` → HTTP 403
- **Token / Authorization:** `Bearer tok_user1_ayse`
- **İstek Gövdesi:**
```json
{bad
```
- **Yanıt Durum Kodu:** `403`
- **Yanıt Gövdesi:**
```json
{
  "error": "Erişim engellendi",
  "message": "Bu poliçeye erişim yetkiniz yok."
}
```

### `P5-PATCH-STATUS-INVALID` — `PATCH /policies/pol_5` → HTTP 200
- **Token / Authorization:** `Bearer tok_user1_ayse`
- **İstek Gövdesi:**
```json
{
  "status": "gecersiz_durum"
}
```
- **Yanıt Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{
  "id": "pol_5",
  "policyNumber": "POL-2026-0005",
  "ownerUserId": "u1",
  "holderName": "Ayşe Yılmaz",
  "holderTckn": "11111111110",
  "coverageType": "trafik",
  "premium": 1800,
  "coverageLimit": 75000,
  "status": "gecersiz_durum",
  "agentName": null,
  "startDate": "2026-04-01",
  "endDate": "2027-03-31"
}
```

### `P5-PATCH-STATUS-ACTIVE` — `PATCH /policies/pol_5` → HTTP 200
- **Token / Authorization:** `Bearer tok_user1_ayse`
- **İstek Gövdesi:**
```json
{
  "status": "active"
}
```
- **Yanıt Durum Kodu:** `200`
- **Yanıt Gövdesi:**
```json
{
  "id": "pol_5",
  "policyNumber": "POL-2026-0005",
  "ownerUserId": "u1",
  "holderName": "Ayşe Yılmaz",
  "holderTckn": "11111111110",
  "coverageType": "trafik",
  "premium": 1800,
  "coverageLimit": 75000,
  "status": "active",
  "agentName": null,
  "startDate": "2026-04-01",
  "endDate": "2027-03-31"
}
```
