# SFM v1.4 Test Tasarımı (referans - kısaltılmış)

Teknikler: denklik sınıfı + sınır değeri (AT, KITAP50 400, DEFNE10 tavanı 1500, türetilmiş NT 750 ve kapıda OT 5000),
karar tablosu (kargo: teslimat x ALTIN x NT>=750 x bölge; kupon: kupon x üyelik x AT>=400), durum geçiş (0-switch + geçersiz
geçişler + sayaç/süre korumaları), pairwise (kısıtlı, 12 satır, 59 uygun çiftin tamamı).

## Spesifikasyon tespitleri

- Ek-A Örnek 4 kurallarla çelişiyor: 6.5'e göre KLASIK + UZAK + NT 900,00 için KU 25,00 ve OT 925,00 olmalı; örnekte 0,00 / 900,00 yazıyor.
- Ek-A'daki diğer satırlar kurallarla tutarlı; Örnek 3'teki 127 puan (85 x 1,5 = 127,5, aşağı yuvarlanır) doğrulandı.
