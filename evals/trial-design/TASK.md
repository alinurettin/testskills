# Görev: SFM v1.4 için test tasarımı

**Kimden:** Selin Aydın — Test Lideri, Defne Kitap (Ödeme ve Sipariş Ekibi)
**Kime:** Kıdemli Test Analisti
**Konu:** SFM v1.4 test tasarımı

Merhaba,

SFM'nin (Sipariş Fiyatlandırma Motoru) ve sipariş durum yönetiminin v1.4 spesifikasyonu onaylandı; geliştirme önümüzdeki sprintte başlıyor. Henüz çalışan bir sistem ya da kod yok, ama test tasarımının geliştirmeyle aynı anda hazır olmasını istiyoruz. Elindeki tek kaynak ekteki spesifikasyon.

Senden kıdemli bir test analistinden beklediğimiz kalitede bir test tasarımı hazırlamanı rica ediyorum: somut test verisi ve kuruşu kuruşuna doğru beklenen sonuçlarla. Geçen sürümde otomasyondaki yanlış beklenen değerler yüzünden çok sayıda yanlış alarmla uğraştık; beklenen sonuçların doğruluğu bizim için en az kapsam kadar önemli. Test sayısı şişmesin, ama riskli noktalar da atlanmasın. Spesifikasyonda gözüne takılan tutarsızlık veya belirsizlik olursa ayrıca listele.

E2E ödeme regresyonu manuel koşuluyor ve her kombinasyon yaklaşık 15 dakika sürüyor. Tüm kombinasyonları koşamayız; makul sayıda satırla olabildiğince geniş kapsam istiyoruz.

## Girdiler

- `girdiler/SFM-spesifikasyon-v1.4.md` — onaylı spesifikasyon
- `girdiler/sablonlar/fiyat-test-verisi.csv` — fiyatlandırma test verisi şablonu
- `girdiler/sablonlar/durum-gecis-testleri.csv` — durum geçiş testleri şablonu
- `girdiler/sablonlar/konfigurasyon-matrisi.csv` — E2E konfigürasyon matrisi şablonu

## Beklenen teslimatlar (hepsi `cikti/` klasörüne)

1. `cikti/test-tasarimi.md` — Test tasarım dokümanı: kullandığın teknikler ve gerekçeleri, denklik sınıfları ve sınır değerleri, karar tablosu/tabloları, durum geçiş modeli (geçerli ve geçersiz geçişler), konfigürasyon kombinasyonlarına yaklaşımın, spesifikasyonla ilgili soru ve tespitlerin, varsayımların ve kapsam dışı bıraktıkların.
2. `cikti/fiyat-test-verisi.csv` — SFM fiyatlandırma test vakaları.
3. `cikti/durum-gecis-testleri.csv` — Sipariş durum geçiş test vakaları.
4. `cikti/konfigurasyon-matrisi.csv` — E2E ödeme regresyonu için koşulacak kombinasyonlar.

## CSV kuralları

Otomasyon ekibi CSV dosyalarını doğrudan data-driven testlere besleyecek; bu yüzden biçime lütfen birebir uy:

- UTF-8, ayraç `;`, ilk satır şablondaki başlık satırı (kolon adlarını ve sırasını değiştirme).
- Değerleri spesifikasyondaki kodlarla birebir yaz (ör. `KLASIK`, `KAPIDA_ODEME`, `ERR_MIN_SEPET`). Tutarlarda ondalık ayırıcı nokta, binlik ayırıcı yok (ör. `1499.90`).
- Fiyat testlerinde `beklenen_durum` `KABUL` ise tüm beklenen tutar ve puan kolonlarını doldur; hata bekleniyorsa `beklenen_durum` kolonuna hata kodunu yaz, tutar ve puan kolonlarını boş bırak.
- Durum geçiş testlerinde `olay_dizisi`, sipariş oluşturulduktan sonra sırayla uygulanan olaylardır. Olaylar ` > ` ile ayrılır, parametreler parantez içinde yazılır (ör. `ODEME_BASARILI > HAZIRLAMAYA_BASLA > IPTAL(aktor=OPERATOR)`). Beklenen sonuç ve beklenen durum, dizideki **son olay** içindir; ondan önceki olayların hepsi geçerli olmalıdır (ön koşul hazırlığı). Boş dizi yalnızca siparişin oluşturulmasını ifade eder.
- Şablonlardaki `ORNEK-` ile başlayan satırlar yalnızca biçim örneğidir, değerlendirmeye alınmaz; silebilirsin.

Teşekkürler,
Selin
