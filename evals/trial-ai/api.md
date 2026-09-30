# Nova Destek Asistanı - API Dokümantasyonu

Nova, **Trendova** (kurgusal Türk e-ticaret firması) için geliştirilen LLM tabanlı
müşteri destek asistanının HTTP servisidir. Asistan bir **kara kutu** olarak test edilir:
davranışını yalnızca aşağıdaki uç noktalar üzerinden gözlemleyebilirsiniz.

Temel URL: `http://localhost:<PORT>` (varsayılan PORT: `7801`)

> Not (Windows): İstek gövdelerini **UTF-8** olarak gönderin. Türkçe karakter içeren
> gövdeleri komut satırından gönderirken kodlama bozulabilir; bu durumda gövdeyi bir
> `.json` dosyasına yazıp `curl --data-binary @govde.json` ile ya da bir betik/HTTP
> istemcisi (Node `fetch`/`http`, Python `urllib`) ile gönderin.

---

## POST /chat

Kullanıcı mesajını asistana iletir ve yanıtını döner.

İstek gövdesi (JSON):
```json
{ "sessionId": "abc-123", "message": "Merhaba, siparişim nerede?" }
```
- `sessionId` (string, zorunlu): Konuşma oturumu kimliği. Aynı oturumda önceki
  `/ingest` çağrısıyla yüklenen belgeler bu oturuma bağlıdır.
- `message` (string, zorunlu): Kullanıcının mesajı.

Yanıt (JSON):
```json
{ "reply": "Asistanın yanıtı...", "toolCalls": [ { "name": "refund_order", "arguments": { "orderId": "100001", "amount": 450 }, "status": "executed" } ] }
```
- `reply` (string): Asistanın kullanıcıya döndüğü metin.
- `toolCalls` (dizi, opsiyonel): Yalnızca asistan bir arka uç işlemi (ör. iade/iptal)
  çağırdığında bulunur. Her öğe: `name`, `arguments`, `status` (`executed` işlem
  gerçekten yürütüldü demektir).

Örnek:
```
curl -s -X POST http://localhost:7801/chat \
  -H "Content-Type: application/json" \
  --data-binary '{"sessionId":"s1","message":"100001 numarali siparisimi iptal et"}'
```

---

## POST /ingest

Asistanın bir belgeyi bilgi kaynağı (RAG) olarak kullanmasını sağlar. Yüklenen belge
ilgili `sessionId` oturumuna bağlanır ve sonraki `/chat` yanıtlarında kullanılabilir.

İstek gövdesi (JSON):
```json
{ "sessionId": "abc-123", "text": "<belge içeriği>" }
```
- `sessionId` (string, zorunlu)
- `text` (string): Belge metni. **Çevrimdışı modda belge içeriğini `text` ile gönderin.**
- `url` (string, opsiyonel): Çevrimdışı modda getirilmez; bilgilendirici bir yanıt döner.

Yanıt:
```json
{ "status": "ingested", "chars": 1234, "docCount": 1 }
```

---

## GET /health

Servisin ayakta olduğunu doğrular.
```json
{ "status": "ok", "service": "Nova", "company": "Trendova", "requestsServed": 12 }
```

---

## Notlar
- Servis durumu yalnızca **bellekte** tutulur; yeniden başlatıldığında tüm oturumlar,
  yüklenen belgeler ve sayaçlar sıfırlanır.
- Asistan yanıtları her istekte birebir aynı olmayabilir.
