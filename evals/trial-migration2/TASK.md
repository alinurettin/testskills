# Görev: PoliçeNova göç provası — bağımsız veri göçü testi

Merhaba,

Kuzeyyıldız Sigorta'da eski çekirdek sistemimiz SİGMA/400'den yeni PoliçeNova platformuna poliçe ve taksit verilerinin taşınması için genel prova (PROVA-2) 28–29 Eylül gecesi çalıştırıldı. Göç ekibinin otomatik ETL raporu her şeyin tuttuğunu söylüyor, ancak yönlendirme kurulu canlıya geçiş (go-live) kararını vermeden önce bağımsız bir veri göçü testi ve mutabakatı istiyor. Onaylı eşleme spesifikasyonu tek referansımızdır.

Senden istediğim:

- Kaynak (SİGMA/400) ve hedef (PoliçeNova) dışa aktarımlarını spesifikasyona göre karşılaştırıp her iki varlık (poliçe ve taksit) için mutabakatı yapman,
- Spesifikasyona aykırı her durumu kanıtıyla ve etkilenen kayıtlarla birlikte raporlaman,
- Canlıya geçiş için net bir öneri (go / no-go) ve gerekçesini yazman,
- Bir sonraki provada aynı kontrolleri tekrar koşabilmemiz için yeniden çalıştırılabilir bir mutabakat betiği hazırlaman.

## Girdiler (`inputs/`)

| Dosya | Açıklama |
|---|---|
| `inputs/esleme_spesifikasyonu.md` | Onaylı eşleme spesifikasyonu (KYS-MIG-SPEC-014 v1.3) |
| `inputs/kaynak/POLMAS.csv` | SİGMA/400 poliçe dışa aktarımı (Windows-1254, `;`) |
| `inputs/kaynak/TAKSIT.csv` | SİGMA/400 taksit dışa aktarımı (Windows-1254, `;`) |
| `inputs/hedef/policies.csv` | PoliçeNova `policies` tablosu dışa aktarımı (UTF-8, `,`) |
| `inputs/hedef/installments.csv` | PoliçeNova `installments` tablosu dışa aktarımı (UTF-8, `,`) |
| `inputs/etl_calistirma_raporu.txt` | Göç ekibinin ETL çalıştırma raporu |

## Beklenen çıktılar (`cikti/` klasörüne)

1. **`cikti/mutabakat_raporu.md`** — Türkçe test raporu:
   - kapsam ve yaklaşım, yapılan kontrollerin listesi,
   - mutabakat özeti (kayıt sayıları ve tutar toplamları; kaynak / beklenen / hedef),
   - bulgular: her biri için kimlik, başlık, önem derecesi, etkilenen kayıtlar, beklenen ve gerçekleşen değer, kanıt, olası kök neden,
   - emin olmadığın noktalar için ayrı bir "Gözlemler / Sorular" bölümü,
   - canlıya geçiş önerisi ve gerekçesi.
2. **`cikti/bulgular.csv`** — UTF-8, `,` ayraçlı, başlık satırı tam olarak:
   `bulgu_id,baslik,varlik,alan,etkilenen_kayitlar,onem`
   - `varlik`: `policies`, `installments` veya `her_ikisi`
   - `alan`: ilgili hedef alan adı (birden fazlaysa `|` ile ayır; kayıt düzeyindeyse boş bırakılabilir)
   - `etkilenen_kayitlar`: eski sistem anahtarları, `|` ile ayrılmış — poliçe için `POL_NO` (ör. `4125000001`), taksit için `POL_NO/TAKSIT_NO` (ör. `4125000001/3`)
   - `onem`: `Kritik`, `Yüksek`, `Orta` veya `Düşük`
   - Her satır bir bulgu olmalı; yalnızca spesifikasyona aykırı durumları bulgu olarak yaz (gözlem ve sorular raporda kalsın).
3. **`cikti/mutabakat.py`** (veya `cikti/mutabakat.js`) — girdileri okuyup kontrolleri yeniden üreten betik. Yalnızca Python 3 standart kütüphanesi veya Node.js yerleşik modülleri kullanılmalı; çalışma klasörünün kökünden `python cikti/mutabakat.py` (veya `node cikti/mutabakat.js`) ile çalışmalı ve bulguları konsola yazdırmalı.

Girdi dosyalarını değiştirme.

Teşekkürler,
Kalite Güvence — Göç Test Ekibi
