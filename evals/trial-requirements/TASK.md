# Görev

Aşağıdaki mesaj, Nergis Çarşı QA ekibinden bir test mühendisinin talebidir.

---

Merhaba,

Nergis Çarşı'da sipariş sonrası deneyim ekibinin QA'iyim. Ürün ekibi yeni **Kolay İade ve Geri Ödeme** özelliğinin PRD'sini (v1.3) ve kategori bazlı iade kuralları tablosunu (Ek-B) paylaştı. Önümüzdeki sprintte test tasarımına başlayacağız; test senaryolarını yazmadan önce gereksinimleri senin analiz etmeni istiyorum.

Senden beklediklerim:

1. Gereksinimlerdeki belirsiz, çelişkili, eksik veya test edilemeyen noktaları bul. Her biri için dokümandaki yerini (bölüm / ID, örn. AC-2.3, BR-05) göster, neden sorun olduğunu ve teste etkisini kısaca açıkla, önceliğini belirt (Kritik / Yüksek / Orta / Düşük).
2. Her sorun için ürün ekibine sorulacak net bir netleştirme sorusu yaz.
3. En önemli sorunlar için (en az 5 tane) ilgili gereksinimi test edilebilir biçimde yeniden yaz: ölçülebilir kabul kriterleri, net sınır değerleri, beklenen sonuçlar. Önerdiğin değerler varsayımsa bunu açıkça belirt.

Ürün ekibi uzun soru listelerinden pek hoşlanmıyor; lütfen yalnızca gerçekten netleştirilmesi gereken noktaları yaz.

Teşekkürler!

---

## Girdiler

- `girdiler/PRD-Kolay-Iade-v1.3.md` — Kolay İade ve Geri Ödeme PRD'si (v1.3)
- `girdiler/Ek-B-kategori-iade-kurallari.csv` — Ek-B, kategori bazlı iade kuralları (UTF-8, `;` ayraçlı)

## Beklenen çıktılar (çalışma klasörünün kök dizinine yazılacak)

- `gereksinim-analizi.md` — Bulgular tablosu (en az şu sütunlarla: Bulgu ID, Yer, Tür, Açıklama ve teste etkisi, Öncelik, Netleştirme sorusu)
- `test-edilebilir-gereksinimler.md` — En önemli sorunlar için test edilebilir biçimde yeniden yazılmış gereksinimler

Tüm çıktılar Türkçe olmalıdır.
