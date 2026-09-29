# Örnek: FAST para transferi (uçtan uca, gerçek çıktı)

Bu klasördeki dosyaların hepsi QA Suite'in bir yapay zekâ ajanıyla **tek seferde ürettiği gerçek çıktılardır**. Elle düzeltme yapılmadı.

Ajana verilen girdiler şunlardı:
- bir user story: [US-310](../../evals/trial-fast/docs/US-310-fast-transfer.md), 10 kabul kriteri
- test ortamında çalışan bir demo banka uygulaması. Uygulamaya ajana söylenmeden 5 hata yerleştirilmişti. Ajan uygulamayı kara kutu olarak test etti.

## Sonuç
- **Hatalar:** Yerleştirilen 5 hatanın 5'i bulundu, artı yerleştirilmemiş gerçek bir hata ("15.000" tutarı 15,00 TL olarak işleniyordu).
- **Testler:** 47 test yazıldı. Öncelik dağılımı: %2 kritik, %34 yüksek, %49 orta, %15 düşük.
- **Otomasyon:** 46 otomasyon adayının hepsi Playwright'la otomatize edildi. Koşum sonucu 37 geçti, 9 kaldı. Bağımsız bir yeniden koşum aynı sonucu verdi.
- **Yayın kararı:** Tamamlama raporu, 9 çıkış kriterinden 4'ü karşılandığı için "yayına hazır değil" dedi.

## Dosyalar
| Aşama | Dosya |
|---|---|
| Gereksinim analizi | [qa/requirements.src.md](qa/requirements.src.md) · [qa/clarifications.md](qa/clarifications.md) |
| Test planı | [qa/test-plan.md](qa/test-plan.md) · [qa/exit-criteria.json](qa/exit-criteria.json) |
| Test tasarımı (script çıktıları) | [sınır değerler](qa/design/DS-001-tutar.md) · [karar tablosu](qa/design/DS-006-islem-kurallari.md) · [durum geçişi](qa/design/DS-008-akis.md) |
| Test case'ler | [qa/test-cases.src.md](qa/test-cases.src.md) |
| İzlenebilirlik | [qa/rtm.md](qa/rtm.md) |
| Xray import | [qa/exports/xray.csv](qa/exports/xray.csv) |
| Otomasyon | [Page Object](automation/pages/FastTransferPage.ts) · [spec: 50.000 TL sınırı](automation/tests/req-002-islem-basina-azami-tutar-50-000-00-tl.spec.ts) · [spec: ücret eşiği](automation/tests/req-006-5-000-00-tl-yi-asan-transferlerde-5-00-t.spec.ts) · [otomasyon kapsamı](qa/automation-coverage.md) |
| Hata raporları | [qa/defect-reports.md](qa/defect-reports.md) |
| Tamamlama raporu | [qa/completion-report.md](qa/completion-report.md) |

Denemeyi kendiniz tekrar koşmak için [evals/trial-fast](../../evals/trial-fast/ANSWER-KEY.md) klasörüne bakın. Uygulamayı ajana cevap anahtarını göstermeden verin.
