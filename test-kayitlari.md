# Test Kayıtları

## Testin 1: Yetkisiz Kullanıcı Admin İstatistiklerine Erişim (Authorization Bypass)
## Kullanıcı1 admin/stats'e erişmeyi dener (BEKLENEN: 403 Forbidden)

**İstek:**
```
Method: GET
Endpoint: /admin/stats
Token: tok_user1_ayse
```

**Yanıt:**
```
Status: 200
Body:
{"totalPolicies":5,"totalClaims":7,"totalPremium":9800}
```


## Test 2: Cross-User Policy Access
## User1 User2'nin poliçesine (pol_3) erişmeyi dener

**İstek:**
```
Method: GET
Endpoint: /policies/pol_3
Token: tok_user1_ayse
```

**Yanıt:**
```
Status: 403
Body:
{"error":"Erişim engellendi","message":"Bu poliçeye erişim yetkiniz yok."}
```


## Test 3: Cross-User Claim Access
## User1 User2'nin hasar talebine (clm_6) erişmeyi dener

**İstek:**
```
Method: GET
Endpoint: /claims/clm_6
Token: tok_user1_ayse
```

**Yanıt:**
```
Status: 403
Body:
{"error":"Erişim engellendi","message":"Bu hasar talebine erişim yetkiniz yok."}
```


## Test 4: Amount Validation (Coverage Limit)
## User1 teminat limitini aşan hasar talebi oluşturmaya çalışır

**İstek:**
```
Method: POST
Endpoint: /claims
Token: tok_user1_ayse
Body: {"policyId":"pol_1","amount":999999999}
```

**Yanıt:**
```
Status: 200
Body:
{"id":"clm_8","policyId":"pol_1","ownerUserId":"u1","amount":999999999,"status":"submitted","description":"","createdAt":"2026-08-01T00:00:00Z"}
```


## Test 5: Create Claim on Another User's Policy
## User1 User2'nin poliçesi için hasar talebi oluşturmaya çalışır

**İstek:**
```
Method: POST
Endpoint: /claims
Token: tok_user1_ayse
Body: {"policyId":"pol_3","amount":5000}
```

**Yanıt:**
```
Status: 403
Body:
{"error":"Erişim engellendi","message":"Bu poliçe için hasar talebi oluşturamazsınız."}
```


## Test 6: Valid Claim Creation
## User1 kendi poliçesi için geçerli hasar talebi oluşturur

**İstek:**
```
Method: POST
Endpoint: /claims
Token: tok_user1_ayse
Body: {"policyId":"pol_1","amount":10000}
```

**Yanıt:**
```
Status: 200
Body:
{"id":"clm_9","policyId":"pol_1","ownerUserId":"u1","amount":10000,"status":"submitted","description":"","createdAt":"2026-08-01T00:00:00Z"}
```


## Test 7: Update Policy - Readonly Fields
## User1 poliçenin salt-okunur alanlarını güncellemeye çalışır (premium, status)

**İstek:**
```
Method: PATCH
Endpoint: /policies/pol_1
Token: tok_user1_ayse
Body: {"premium":9999,"status":"cancelled","coverageLimit":999999}
```

**Yanıt:**
```
Status: 200
Body:
{"id":"pol_1","policyNumber":"POL-2026-0001","ownerUserId":"u1","holderName":"Ayşe Yılmaz","holderTckn":"11111111110","coverageType":"kasko","premium":1500,"coverageLimit":50000,"status":"cancelled","agentName":"Zeynep Kaya","startDate":"2026-01-01","endDate":"2026-12-31"}
```


## Test 8: Claims Pagination
## User1 hasar taleplerini sayfalı olarak listeler

**İstek:**
```
Method: GET
Endpoint: /claims?page=1&pageSize=20
Token: tok_user1_ayse
```

**Yanıt:**
```
Status: 200
Body:
{"data":[{"id":"clm_1","policyId":"pol_1","ownerUserId":"u1","amount":12000,"status":"submitted","description":"Çarpma hasarı","createdAt":"2026-05-02T09:00:00Z"},{"id":"clm_2","policyId":"pol_1","ownerUserId":"u1","amount":8000,"status":"rejected","description":"Cam kırığı","createdAt":"2026-05-10T11:30:00Z"},{"id":"clm_3","policyId":"pol_2","ownerUserId":"u1","amount":3000,"status":"approved","description":"Su baskını","createdAt":"2026-06-01T08:15:00Z"},{"id":"clm_4","policyId":"pol_5","ownerUserId":"u1","amount":15000,"status":"submitted","description":"Trafik kazası","createdAt":"2026-06-20T14:45:00Z"},{"id":"clm_5","policyId":"pol_2","ownerUserId":"u1","amount":2000,"status":"submitted","description":"Hırsızlık","createdAt":"2026-07-03T16:05:00Z"},{"id":"clm_8","policyId":"pol_1","ownerUserId":"u1","amount":999999999,"status":"submitted","description":"","createdAt":"2026-08-01T00:00:00Z"},{"id":"clm_9","policyId":"pol_1","ownerUserId":"u1","amount":10000,"status":"submitted","description":"","createdAt":"2026-08-01T00:00:00Z"}],"meta":{"page":1,"pageSize":20,"total":7}}
```


## Test 9: No Authentication

**Testler tamamlandı**
