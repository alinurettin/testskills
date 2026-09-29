project: Demo Bank API 1.2.0 – Hesaplar ve Transferler
language: tr
setup users: İki test kullanıcısı: API_TOKEN=alice (A-100 TRY, A-101 EUR), API_TOKEN_OTHER=bob (B-200 TRY)


## TC-001 | GET /accounts geçerli istekle 200 döner ve yanıt şemaya uyar
req: REQ-020 | pri: h | pol: + | tech: rb | cat: api
pre: Geçerli test token'ı (API_TOKEN) tanımlı
1. İsteği gönder: GET /accounts => HTTP 200; yanıt gövdesi dokümante şemaya uyar
tags: api, contract, smoke, accounts | auto: yes, contract test | status: ready

## TC-002 | GET /accounts kimlik bilgisi olmadan 401 döner
req: REQ-022 | pri: h | pol: - | tech: eg | cat: api
1. İsteği gönder: GET /accounts (Authorization başlığı yok) => HTTP 401
tags: api, security, auth, accounts | auto: yes, contract test | status: ready

## TC-003 | GET /accounts 'Bearer' şeması olmayan Authorization başlığını 401 ile reddeder
req: REQ-022 | pri: m | pol: - | tech: eg | cat: api
1. İsteği gönder: GET /accounts (Authorization: <token>, 'Bearer' yok) => HTTP 401
tags: api, security, auth, accounts | auto: yes, contract test | status: ready

## TC-004 | GET /accounts/{accountId} geçerli istekle 200 döner ve yanıt şemaya uyar
req: REQ-020 | pri: h | pol: + | tech: rb | cat: api
pre: Geçerli test token'ı (API_TOKEN) tanımlı
1. İsteği gönder: GET /accounts/{accountId} => HTTP 200; yanıt gövdesi dokümante şemaya uyar
tags: api, contract, smoke, accounts | auto: yes, contract test | status: ready

## TC-005 | GET /accounts/{accountId} kimlik bilgisi olmadan 401 döner
req: REQ-022 | pri: h | pol: - | tech: eg | cat: api
1. İsteği gönder: GET /accounts/{accountId} (Authorization başlığı yok) => HTTP 401
tags: api, security, auth, accounts | auto: yes, contract test | status: ready

## TC-006 | GET /accounts/{accountId} olmayan kaynak için 404 döner
req: REQ-020 | pri: m | pol: - | tech: eg | cat: api
1. İsteği gönder: GET /accounts/{accountId} [{"accountId": "does-not-exist-000"}] => HTTP 404
tags: api, negative, accounts | auto: yes, contract test | status: ready

## TC-007 | GET /accounts/{accountId} başka kullanıcının kaynağına erişimi reddeder (BOLA)
req: REQ-021 | pri: h | pol: - | tech: eg | cat: api
pre: @users
1. A kullanıcısına (alice) ait /accounts/{accountId} [A-100] kaynağını B kullanıcısının token'ı (API_TOKEN_OTHER) ile iste => HTTP 403 veya 404; A'nın verisi (IBAN, bakiye) dönmez
tags: api, security, bola, accounts | auto: yes, needs two test users | status: ready

## TC-008 | POST /transfers geçerli istekle 201 döner ve yanıt şemaya uyar
req: REQ-020 | pri: h | pol: + | tech: rb | cat: api
pre: Geçerli test token'ı (API_TOKEN) tanımlı
1. İsteği gönder: POST /transfers [{"fromAccountId": "A-100", "toIban": "TR330006100519786457841326", "amount": 100.0, "currency": "TRY", "description": "Kira"}] => HTTP 201; yanıt gövdesi dokümante şemaya uyar
tags: api, contract, smoke, transfers | auto: yes, contract test | status: ready

## TC-009 | POST /transfers kimlik bilgisi olmadan 401 döner
req: REQ-022 | pri: h | pol: - | tech: eg | cat: api
1. İsteği gönder: POST /transfers (Authorization başlığı yok) => HTTP 401
tags: api, security, auth, transfers | auto: yes, contract test | status: ready

## TC-010 | POST /transfers zorunlu 'fromAccountId' eksikken 400 döner
req: REQ-020 | pri: m | pol: - | tech: ep | cat: api
1. İsteği gönder: POST /transfers [{"toIban": "TR330006100519786457841326", "amount": 100.0, "currency": "TRY", "description": "Kira"}] => HTTP 400; hata gövdesi dönülür, kaynak oluşturulmaz/değiştirilmez
tags: api, validation, transfers | auto: yes, contract test | status: ready

## TC-011 | POST /transfers zorunlu 'toIban' eksikken 400 döner
req: REQ-020 | pri: m | pol: - | tech: ep | cat: api
1. İsteği gönder: POST /transfers [{"fromAccountId": "A-100", "amount": 100.0, "currency": "TRY", "description": "Kira"}] => HTTP 400; hata gövdesi dönülür, kaynak oluşturulmaz/değiştirilmez
tags: api, validation, transfers | auto: yes, contract test | status: ready

## TC-012 | POST /transfers zorunlu 'amount' eksikken 400 döner
req: REQ-020 | pri: m | pol: - | tech: ep | cat: api
1. İsteği gönder: POST /transfers [{"fromAccountId": "A-100", "toIban": "TR330006100519786457841326", "currency": "TRY", "description": "Kira"}] => HTTP 400; hata gövdesi dönülür, kaynak oluşturulmaz/değiştirilmez
tags: api, validation, transfers | auto: yes, contract test | status: ready

## TC-013 | POST /transfers zorunlu 'currency' eksikken 400 döner
req: REQ-020 | pri: m | pol: - | tech: ep | cat: api
1. İsteği gönder: POST /transfers [{"fromAccountId": "A-100", "toIban": "TR330006100519786457841326", "amount": 100.0, "description": "Kira"}] => HTTP 400; hata gövdesi dönülür, kaynak oluşturulmaz/değiştirilmez
tags: api, validation, transfers | auto: yes, contract test | status: ready

## TC-014 | POST /transfers 'fromAccountId' yanlış tipte (12345) reddedilir
req: REQ-020 | pri: m | pol: - | tech: ep | cat: api
1. İsteği gönder: POST /transfers [{"fromAccountId": 12345, "toIban": "TR330006100519786457841326", "amount": 100.0, "currency": "TRY", "description": "Kira"}] => HTTP 400; hata gövdesi dönülür, kaynak oluşturulmaz/değiştirilmez
tags: api, validation, transfers | auto: yes, contract test | status: ready

## TC-015 | POST /transfers 'toIban' yanlış tipte (12345) reddedilir
req: REQ-020 | pri: m | pol: - | tech: ep | cat: api
1. İsteği gönder: POST /transfers [{"fromAccountId": "A-100", "toIban": 12345, "amount": 100.0, "currency": "TRY", "description": "Kira"}] => HTTP 400; hata gövdesi dönülür, kaynak oluşturulmaz/değiştirilmez
tags: api, validation, transfers | auto: yes, contract test | status: ready

## TC-016 | POST /transfers 'amount' = 1 (sınır, geçerli) kabul edilir
req: REQ-020 | pri: m | pol: + | tech: bva | cat: api
1. İsteği gönder: POST /transfers [{"fromAccountId": "A-100", "toIban": "TR330006100519786457841326", "amount": 1, "currency": "TRY", "description": "Kira"}] => HTTP 201
tags: api, boundary, transfers | auto: yes, contract test | status: ready

## TC-017 | POST /transfers 'amount' = 0.99 (alt sınırın altı) reddedilir
req: REQ-020 | pri: m | pol: - | tech: bva | cat: api
1. İsteği gönder: POST /transfers [{"fromAccountId": "A-100", "toIban": "TR330006100519786457841326", "amount": 0.99, "currency": "TRY", "description": "Kira"}] => HTTP 400; hata gövdesi dönülür, kaynak oluşturulmaz/değiştirilmez
tags: api, validation, transfers | auto: yes, contract test | status: ready

## TC-018 | POST /transfers 'amount' = 50000 (sınır, geçerli) kabul edilir
req: REQ-020 | pri: m | pol: + | tech: bva | cat: api
1. İsteği gönder: POST /transfers [{"fromAccountId": "A-100", "toIban": "TR330006100519786457841326", "amount": 50000, "currency": "TRY", "description": "Kira"}] => HTTP 201
tags: api, boundary, transfers | auto: yes, contract test | status: ready

## TC-019 | POST /transfers 'amount' = 50000.01 (üst sınırın üstü) reddedilir
req: REQ-020 | pri: m | pol: - | tech: bva | cat: api
1. İsteği gönder: POST /transfers [{"fromAccountId": "A-100", "toIban": "TR330006100519786457841326", "amount": 50000.01, "currency": "TRY", "description": "Kira"}] => HTTP 400; hata gövdesi dönülür, kaynak oluşturulmaz/değiştirilmez
tags: api, validation, transfers | auto: yes, contract test | status: ready

## TC-020 | POST /transfers 'amount' yanlış tipte ("abc") reddedilir
req: REQ-020 | pri: m | pol: - | tech: ep | cat: api
1. İsteği gönder: POST /transfers [{"fromAccountId": "A-100", "toIban": "TR330006100519786457841326", "amount": "abc", "currency": "TRY", "description": "Kira"}] => HTTP 400; hata gövdesi dönülür, kaynak oluşturulmaz/değiştirilmez
tags: api, validation, transfers | auto: yes, contract test | status: ready

## TC-021 | POST /transfers 'currency' geçersiz enum değeriyle reddedilir
req: REQ-020 | pri: m | pol: - | tech: ep | cat: api
1. İsteği gönder: POST /transfers [{"fromAccountId": "A-100", "toIban": "TR330006100519786457841326", "amount": 100.0, "currency": "__invalid__", "description": "Kira"}] => HTTP 400; hata gövdesi dönülür, kaynak oluşturulmaz/değiştirilmez
tags: api, validation, transfers | auto: yes, contract test | status: ready

## TC-022 | POST /transfers 'currency' yanlış tipte (12345) reddedilir
req: REQ-020 | pri: m | pol: - | tech: ep | cat: api
1. İsteği gönder: POST /transfers [{"fromAccountId": "A-100", "toIban": "TR330006100519786457841326", "amount": 100.0, "currency": 12345, "description": "Kira"}] => HTTP 400; hata gövdesi dönülür, kaynak oluşturulmaz/değiştirilmez
tags: api, validation, transfers | auto: yes, contract test | status: ready

## TC-023 | POST /transfers 'description' = "aaaaaaaaa…(140 chars)" (sınır, geçerli) kabul edilir
req: REQ-020 | pri: m | pol: + | tech: bva | cat: api
1. İsteği gönder: POST /transfers [{"fromAccountId": "A-100", "toIban": "TR330006100519786457841326", "amount": 100.0, "currency": "TRY", "description": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}] => HTTP 201
tags: api, boundary, transfers | auto: yes, contract test | status: ready

## TC-024 | POST /transfers 'description' = "aaaaaaaaa…(141 chars)" (en uzun uzunluğun üstü) reddedilir
req: REQ-020 | pri: m | pol: - | tech: bva | cat: api
1. İsteği gönder: POST /transfers [{"fromAccountId": "A-100", "toIban": "TR330006100519786457841326", "amount": 100.0, "currency": "TRY", "description": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}] => HTTP 400; hata gövdesi dönülür, kaynak oluşturulmaz/değiştirilmez
tags: api, validation, transfers | auto: yes, contract test | status: ready

## TC-025 | POST /transfers 'description' yanlış tipte (12345) reddedilir
req: REQ-020 | pri: m | pol: - | tech: ep | cat: api
1. İsteği gönder: POST /transfers [{"fromAccountId": "A-100", "toIban": "TR330006100519786457841326", "amount": 100.0, "currency": "TRY", "description": 12345}] => HTTP 400; hata gövdesi dönülür, kaynak oluşturulmaz/değiştirilmez
tags: api, validation, transfers | auto: yes, contract test | status: ready

## TC-026 | GET /transfers/{transferId} geçerli istekle 200 döner ve yanıt şemaya uyar
req: REQ-020 | pri: h | pol: + | tech: rb | cat: api
pre: Geçerli test token'ı (API_TOKEN) tanımlı
pre: Ortamda örnek T-1 yok; test kendi transferini oluşturur
1. alice ile 1 TRY transfer oluştur (A-100) [amount=1] => HTTP 2xx; transfer id döner
2. İsteği gönder: GET /transfers/{transferId} (oluşturulan id) => HTTP 200; yanıt gövdesi dokümante şemaya uyar
tags: api, contract, smoke, transfers | auto: yes, contract test | status: ready

## TC-027 | GET /transfers/{transferId} kimlik bilgisi olmadan 401 döner
req: REQ-022 | pri: h | pol: - | tech: eg | cat: api
1. İsteği gönder: GET /transfers/{transferId} (Authorization başlığı yok) => HTTP 401
tags: api, security, auth, transfers | auto: yes, contract test | status: ready

## TC-028 | GET /transfers/{transferId} olmayan kaynak için 404 döner
req: REQ-020 | pri: m | pol: - | tech: eg | cat: api
1. İsteği gönder: GET /transfers/{transferId} [{"transferId": "does-not-exist-000"}] => HTTP 404
tags: api, negative, transfers | auto: yes, contract test | status: ready

## TC-029 | GET /transfers/{transferId} başka kullanıcının kaynağına erişimi reddeder (BOLA)
req: REQ-021 | pri: h | pol: - | tech: eg | cat: api
pre: @users
1. alice ile 1 TRY transfer oluştur (A-100) [amount=1] => HTTP 2xx; transfer id döner
2. Bu /transfers/{transferId} kaynağını B kullanıcısının token'ı (API_TOKEN_OTHER) ile iste => HTTP 403 veya 404; A'nın verisi dönmez
tags: api, security, bola, transfers | auto: yes, needs two test users | status: ready

## TC-030 | Başka müşterinin hesabından (fromAccountId) transfer 403 ile reddedilir
req: REQ-021 | pri: c | pol: - | tech: eg | cat: security
pre: @users
1. bob'un B-200 bakiyesini oku (bob token'ı) => Bakiye X
2. alice token'ı ile POST /transfers gönder [{"fromAccountId": "B-200", "toIban": "TR330006100519786457841326", "amount": 1, "currency": "TRY"}] => HTTP 403
3. bob'un B-200 bakiyesini tekrar oku => Bakiye X (değişmemiş)
tags: api, security, bola, transfers | auto: yes | status: ready

## TC-031 | GET /accounts yalnızca çağıranın hesaplarını döner
req: REQ-021 | pri: h | pol: + | tech: eg | cat: security
pre: @users
1. alice ve bob ile GET /accounts iste => İki listede ortak hesap kimliği yok
tags: api, security, bola, accounts | auto: yes | status: ready

## TC-032 | Değiştirilmiş (tampered) token 401 ile reddedilir
req: REQ-022 | pri: h | pol: - | tech: eg | cat: security
1. GET /accounts gönder (Authorization: Bearer <API_TOKEN + 'x'>) => HTTP 401
tags: api, security, auth | auto: yes | status: ready

## TC-033 | Bakiyeyi aşan transfer reddedilir ve bakiye değişmez
req: REQ-023 | pri: c | pol: - | tech: bva | cat: api
pre: @users
1. bob'un B-200 bakiyesini oku => Bakiye X
2. bob ile POST /transfers gönder [amount = floor(X)+1; fromAccountId=B-200] => HTTP 400/409/422 (kod dokümante değil, Q-002)
3. B-200 bakiyesini tekrar oku => Bakiye X
tags: api, business-rule, transfers | auto: yes | status: ready

## TC-034 | Başarılı transfer kaynak bakiyeyi tam tutar kadar düşürür
req: REQ-023 | pri: c | pol: + | tech: rb | cat: api
pre: @users
1. alice'in A-100 bakiyesini oku => Bakiye X
2. POST /transfers gönder [amount=10.10; fromAccountId=A-100] => HTTP 2xx
3. A-100 bakiyesini tekrar oku => Bakiye X - 10,10
tags: api, business-rule, side-effect, transfers | auto: yes | status: ready

## TC-035 | Hesap para birimiyle uyuşmayan currency reddedilir (EUR hesap, TRY transfer)
req: REQ-023 | pri: h | pol: - | tech: eg | cat: api
pre: @users
1. alice'in A-101 (EUR) bakiyesini oku => Bakiye X
2. POST /transfers gönder [{"fromAccountId": "A-101", "currency": "TRY", "amount": 1}] => HTTP 400/422 (kural dokümante değil, Q-004)
3. A-101 bakiyesini tekrar oku => Bakiye X
tags: api, business-rule, transfers | auto: yes | status: ready

## TC-036 | toIban deseni (^TR[0-9]{24}$) dışındaki IBAN 400 ile reddedilir
req: REQ-020 | pri: m | pol: - | tech: ep | cat: api
1. POST /transfers gönder [toIban = TR12345 / DE89370400440532013000 / TR33000610051978645784132X] => Her biri için HTTP 400
tags: api, validation, transfers | auto: yes, veri güdümlü | status: ready

## TC-037 | Var olmayan fromAccountId ile transfer 4xx döner
req: REQ-023 | pri: m | pol: - | tech: eg | cat: api
1. POST /transfers gönder [fromAccountId=A-999] => HTTP 400/403/404/422; 2xx veya 500 değil (kod dokümante değil, Q-003)
tags: api, negative, transfers | auto: yes | status: ready

## TC-038 | Negatif tutar reddedilir
req: REQ-020 | pri: m | pol: - | tech: ep | cat: api
1. POST /transfers gönder [amount=-100] => HTTP 400
tags: api, validation, transfers | auto: yes | status: ready

## TC-039 | Salt okunur alanlar (id, status) istemciden atanamaz (mass assignment)
req: REQ-021 | pri: h | pol: - | tech: eg | cat: security
1. POST /transfers gönder [geçerli gövde + id=T-HACK-1, status=REJECTED] => Reddedilir (400/422) ya da 2xx ise yanıttaki id T-HACK-1 değil ve status REJECTED değil
tags: api, security, bopla, transfers | auto: yes | status: ready

## TC-040 | Tutar sayısal string ("100") olarak gönderilince reddedilir
req: REQ-020 | pri: m | pol: - | tech: ep | cat: api
1. POST /transfers gönder [amount="100"] => HTTP 400
tags: api, validation, transfers | auto: yes | status: ready

## TC-041 | Doğrulama hatası Error şemasında ({code, message}) döner
req: REQ-024 | pri: m | pol: - | tech: eg | cat: api
1. POST /transfers gönder [amount=0.5] => HTTP 400; gövde {code: string, message: string}
tags: api, error-model, transfers | auto: yes | status: ready

## TC-042 | Bozuk JSON gövdesi 400 döner (500 değil)
req: REQ-024 | pri: m | pol: - | tech: eg | cat: api
1. POST /transfers gönder (Content-Type: application/json, gövde yarım JSON) ["{\"fromAccountId\": \"A-100\", \"amount\": "] => HTTP 400; yığın izi yok
tags: api, error-model, transfers | auto: yes | status: ready
