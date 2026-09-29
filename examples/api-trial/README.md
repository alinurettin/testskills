# Örnek: kör API denemesi (Demo Bank API)

`testing-apis` skill'iyle yapılan kör denemenin **gerçek, düzenlenmemiş çıktıları**. Ajana yalnızca OpenAPI dokümanı, çalışan API ve iki test kullanıcısı verildi. Uygulama kodu ve cevap anahtarı ([evals/trial-api/ANSWER-KEY.md](../../evals/trial-api/ANSWER-KEY.md)) gösterilmedi.

| | Sonuç |
|---|---|
| Yerleştirilen hatalar | **5/5 bulundu** (BOLA, üst sınır, eksik alanda 500, 200/201, string bakiye) |
| Yerleştirilmemiş gerçek hatalar | 2: `Bearer` olmadan gönderilen token kabul ediliyor; EUR hesaptan TRY transfer kur çevrimi olmadan kabul ediliyor |
| Sözleşme soruları | 17 (1'i bloke edici) |
| Testler | 42 test (29'u üreticiden, 13'ü elle: yetkilendirme, iş kuralı, hata modeli) · 31 geçti / 11 kaldı |
| Bağımsız yeniden koşum | Temiz sunucuda aynı sonuç: 31/11 |
| Süre | ~10 dakika |

## Dosyalar
- [qa/defect-report.md](qa/defect-report.md): kök nedene göre gruplanmış hata raporu (istek/yanıt kanıtı, sınıflandırma)
- [qa/clarifications.md](qa/clarifications.md): sözleşme boşlukları ve sorular
- [qa/test-cases.src.md](qa/test-cases.src.md): test case'ler (kompakt format)
- [qa/rtm.md](qa/rtm.md), [qa/results.json](qa/results.json), [qa/completion-report.md](qa/completion-report.md)
- [automation/](automation/): koşturulan Playwright API testleri (`@TC-###` etiketli)

Denemenin geri bildirimleri skill'e işlendi (0.6.0). Ayrıntılar: [docs/EVALUATION.md](../../docs/EVALUATION.md).
