# Görev

Merhaba,

Nehir Mobil'e bu sprintte eklenen **IBAN'a FAST Transferi** özelliği (US-214) için test ekibimiz manuel test case'lerini Excel'de hazırladı. Set, regresyon paketine alınmadan önce bağımsız bir gözle gözden geçirilsin istiyoruz.

**Ekibin Excel'deki test case'lerini incele, kalitesini değerlendir, eksik ve hatalı olanları bul, düzeltme önerisi ver.**

## Girdiler

- `inputs/FAST_Transfer_Test_Cases.xlsx` — ekibin test seti ("Test Cases" ve "Bilgi" sayfaları)
- `inputs/US-214_FAST_Transfer.md` — user story ve kabul kriterleri

Uygulamaya ya da test ortamına erişimin yok; inceleme yalnızca bu iki doküman üzerinden yapılacak.

## Beklenen çıktılar

1. Çalışma klasörünün kökünde **`inceleme-raporu.md`**:
   - Test setinin genel kalitesine dair kısa bir değerlendirme,
   - Her bulgu için: ilgili Test ID('ler) veya kabul kriteri, sorunun ne olduğu, neden önemli olduğu, önem derecesi ve somut düzeltme önerisi,
   - Eklenmesi gereken testler varsa; her biri için başlık, ön koşul, adımlar ve beklenen sonuç.
2. Orijinal Excel dosyasını değiştirme. İstersen düzeltilmiş test setini ayrı bir dosya olarak (ör. `FAST_Transfer_Test_Cases_duzeltilmis.xlsx`) ekleyebilirsin; bu zorunlu değil.
