Merhaba,

Yeni bilet satış uygulamamız **Perdeaçık Bilet**'in ilk demo sürümü test ortamına kuruldu. Elimizde ayrıntılı bir gereksinim dokümanı yok; sadece ürün sahibinin yazdığı kısa bir ürün notu var. Perşembe günkü sürüm kararından önce uygulamanın gerçekte ne durumda olduğunu görmek istiyoruz.

Bu uygulamada 60–90 dakikalık bir keşif testi (exploratory testing) oturumu yapar mısın? Kendi charter'larını belirle, uygulamayı gerçek bir kullanıcı gibi ve biraz da "kötü niyetli" bir test uzmanı gibi kurcala. Bulduğun hataları başkasının tekrar üretebileceği şekilde yaz; sonunda da bize kısa bir değerlendirme (debrief) ver.

## Girdiler

- **Uygulama:** http://127.0.0.1:4310 (test ortamı; istediğin kadar sipariş oluşturup iptal edebilirsin, veriler gerçek değil)
- **Ürün notu:** `urun-notu.md` (bu klasörde)
- Uygulamayı tarayıcıyla (Playwright/Chromium kullanabilirsin) ve/veya doğrudan HTTP istekleriyle test edebilirsin.
- Kaynak koda erişimin yok; uygulamayı kara kutu olarak test et.
- Test verisi olarak yalnızca uydurma bilgiler kullan (ör. `ad.soyad@example.com`, `0555 000 00 00`).

## Teslim etmeni beklediğim şey

Bu klasöre tek bir `kesif-raporu.md` dosyası (ekran görüntüsü vb. kanıtları istersen `kanitlar/` klasörüne koyabilirsin). Rapor şu bölümleri içersin:

1. **Oturum notları** — charter(lar), zaman damgalı kısa notlar, denediğin fikirler/turlar ve kullandığın test verileri.
2. **Hata listesi** — her hata için: kimlik, başlık, önem derecesi (Kritik / Yüksek / Orta / Düşük), adım adım tekrar üretme adımları, beklenen sonuç, gerçekleşen sonuç ve kanıt (ekran görüntüsü dosya adı, HTTP isteği/yanıtı vb.).
3. **Sorular ve gözlemler** — hata olduğundan emin olmadığın, ürün sahibine sorulması gereken noktalar (bunları hata listesine koyma).
4. **Debrief** — neleri kapsadın, neleri kapsayamadın, en büyük riskler neler ve sürüm için önerin ne.

Teşekkürler!
