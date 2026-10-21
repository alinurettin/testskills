# Görev: UAT için test verisi üretimi ve üretim kesitinin maskelenmesi

Merhaba,

Pusula Dijital Bank'ta çekirdek bankacılık sistemini yeni sürüme taşıyoruz. Entegrasyon ve regresyon testleri için iki tür veriye ihtiyacımız var, ikisini de senden rica ediyorum:

**1) Sentetik veri üretimi.** `girdiler/uretim_kurallari.md` dosyasındaki 3 tabloluk şemaya (müşteri, hesap, işlem) ve iş kurallarına tamamen uyan sentetik bir veri seti üret. Yeni sistemin içe aktarma modülü kurala uymayan tek bir satır görse bile dosyanın tamamını reddediyor. Dokümanda istenen sınır değer satırları da mutlaka olmalı, sınır testlerimizi bunlarla koşacağız.

**2) Üretim kesitinin maskelenmesi.** `girdiler/uretim_kesiti/` altında canlıdan alınmış bir kesit var (3 CSV). Bunu `girdiler/maskeleme_politikasi.md`'deki politikaya göre maskele. Maskeli veri UAT'ye yüklenecek. KVKK açısından içinde gerçek kişilere ait hiçbir bilgi kalmamalı, ama tablolar arası ilişkiler ve test senaryolarımızın dayandığı özellikler de bozulmamalı. Maskeleme betiği gece çalışan veri tazeleme işine eklenecek, o yüzden her çalıştırmada birebir aynı çıktıyı üretmeli.

Son olarak kısa bir rapor yaz: ne yaptın, kuralları ve politikayı nasıl karşıladın, nasıl doğruladın, kalan riskler neler. Kaynak veride gerçek bir sorun gördüysen onu da yaz.

## Girdiler

- `girdiler/uretim_kurallari.md` — içe aktarma şeması, iş kuralları, zorunlu sınır değer satırları
- `girdiler/maskeleme_politikasi.md` — UAT veri maskeleme politikası (MP-04)
- `girdiler/uretim_kesiti/musteri.csv`
- `girdiler/uretim_kesiti/hesap.csv`
- `girdiler/uretim_kesiti/islem.csv`

## Beklenen teslimatlar (hepsi `cikti/` altında)

| Dosya | Açıklama |
|---|---|
| `cikti/uret.py` veya `cikti/uret.js` | Üretici betik. Kullanım: `python cikti/uret.py <cikti_klasoru>` (veya `node cikti/uret.js <cikti_klasoru>`) |
| `cikti/uretilen/musteri.csv`, `hesap.csv`, `islem.csv` | Üretilen sentetik veri |
| `cikti/maskele.py` veya `cikti/maskele.js` | Maskeleme betiği. Kullanım: `python cikti/maskele.py <girdi_klasoru> <cikti_klasoru>` (veya `node ...`), anahtar `MASKE_ANAHTARI` ortam değişkeninden |
| `cikti/maskeli/musteri.csv`, `hesap.csv`, `islem.csv` | `MASKE_ANAHTARI=pusula-uat-2026` ile `girdiler/uretim_kesiti` üzerinde çalıştırılmış maskeleme çıktısı |
| `cikti/rapor.md` | Kısa rapor |

## Ortam

Windows; Python 3 (yalnızca standart kütüphane) veya Node.js 24 (yalnızca yerleşik modüller). İnternet erişimi yok, ek paket kurulamaz.
