# Görev: PoyrazKlinik Mobil v4.3 test planı incelemesi

> **Gönderen:** Elif Karaca — QA Yöneticisi, Poyraz Sağlık Teknolojileri A.Ş.
> **Konu:** v4.3 mobil test planı — yayın öncesi bağımsız inceleme

Merhaba,

PoyrazKlinik Mobil 4.3'ü 13 Ekim'de mağazalara gönderiyoruz. Mobil QA ekibi test planını hazırladı ve takım lideri onayladı; yayından önce planın bağımsız bir gözle incelenmesini istiyorum. Şu an elimizde test cihazı yok, yani bu bir doküman incelemesi. Lütfen planı ürün özeti ve cihaz kullanım verisiyle karşılaştırarak incele:

1. **Plandaki eksik ve hatalı noktaları bul.** Her bulgu için şunları yaz:
   - öncelik (P1 / P2 / P3),
   - plandaki ilgili bölüm veya test durumu kimliği (varsa),
   - neden önemli olduğu,
   - somut önerilen test(ler): adımlar ve beklenen sonuç.

   Gürültü istemiyorum; yalnızca gerçekten eksik ya da hatalı olan noktaları raporla.

2. **Cihaz matrisi öner.** Matris, platform başına desteklenen kullanıcıların en az %80'ini kapsamalı. Kapsamayı test planının 6. bölümündeki yöntemle, cihaz kullanım CSV'sinden hesapla. Bütçe: Android'de en fazla 11, iOS'ta en fazla 9 cihaz (mevcut cihaz parkı dâhil). Seçimlerini gerekçelendir ve platform bazında hesapladığın kapsama yüzdesini yaz.

## Girdiler (`girdiler/` klasörü)

| Dosya | İçerik |
|---|---|
| `urun_ozeti_v4.3.md` | Ürün özeti (onaylı) |
| `test_plani_v4.3.md` | Mobil QA ekibinin test planı |
| `cihaz_kullanim_2026-08.csv` | Son 28 günün cihaz/OS kullanım verisi |

## Beklenen çıktılar (bu klasörün köküne)

1. **`plan_inceleme.md`** — bulgu listesi (öncelik, ilgili bölüm/TC, gerekçe, önerilen testler); ayrıca önerdiğin cihaz matrisinin gerekçesi ve platform bazında kapsama yüzdeleri.
2. **`cihaz_matrisi.csv`** — önerilen cihaz matrisi. Kurallar:
   - Başlık satırı tam olarak: `platform,model,os_surumu`
   - `platform`: `Android` veya `iOS`
   - `model`: kullanım CSV'sindeki model adıyla aynı (ör. `Galaxy A54`, `iPhone 13`)
   - `os_surumu`: kullanım CSV'sindeki gibi ana sürüm numarası (ör. `14`)
   - Her satır bir fiziksel test cihazıdır.

Teşekkürler,
Elif
