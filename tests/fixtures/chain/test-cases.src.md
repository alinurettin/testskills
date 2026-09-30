project: Demo Bank – uçtan uca izlenebilirlik zinciri
language: tr

# Hand-written part of qa/test-cases.src.md. REQ-006 is deliberately under-tested: one positive
# manual test for a high-risk requirement -> the RTM must report THIN and NO_NEGATIVE.

## TC-001 | Başarılı transfer sonrası dekont e-postası 5 dakika içinde gelir
req: REQ-006 | pri: h | pol: + | tech: rb | ref: US-106 AK-1 | cat: functional
pre: Test müşterisi 'musteri.test@example.com' ile giriş yapmış
1. Geçerli bir transfer oluştur [tutar=100,00 TL] => Transfer 'Tamamlandı' durumunda
2. Test posta kutusunu kontrol et => 5 dakika içinde transfer dekontu e-postası gelir
tags: manual, regression | auto: no | status: ready
