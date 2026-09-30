# Örnek: kör veri taşıma denemesi (müşteri verisi, eski sistem → yeni CRM)

`testing-data-migrations` skill'iyle yapılan kör denemenin **gerçek çıktıları**. Ajana yalnızca kaynak ve hedef extract'lar (`legacy_customers.csv` cp1254, `new_customers.csv` UTF-8) ile mapping dokümanı verildi. Doğru mapping ve cevap anahtarı ([evals/keys/migration.md](../../evals/keys/migration.md)) gösterilmedi.

| | Sonuç |
|---|---|
| Yerleştirilen hatalar | **9/9 bulundu**: eksik, fazla ve tekrarlı kayıt; iki farklı Türkçe karakter bozulması; ×100 ondalık hatası; 0,01 kuruş farkı; gün/ay yer değiştirmesi; yanlış durum kodu |
| Tuzaklar (doğru veri) | Yanlış alarm yok: baştaki sıfırlar, Türkçe büyük harf (İ/I), fazla boşluklar, 29.02 artık gün |
| Kontrol toplamları | +335.121,21 farkın tamamı satır bulgularıyla açıklandı |
| Karar | FAIL, **go değil**; imza kriterleri ve mapping soruları (S1–S9) listelendi |
| Süre | ~3 dakika (script 0,2 sn) |

## Dosyalar
- [migration-test-report.md](migration-test-report.md): sınıflandırılmış bulgular, kanıt, önem, go/no-go ve imza kriterleri
- [reconciliation-mock1.md](reconciliation-mock1.md): `reconcile.py` mutabakat raporu
- [mapping.json](mapping.json): ajanın mapping dokümanından türettiği kurallar

Ayrıntılar: [docs/EVALUATION.md](../../docs/EVALUATION.md).
