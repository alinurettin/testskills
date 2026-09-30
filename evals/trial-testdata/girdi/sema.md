# Müşteri – Hesap – İşlem Test Verisi Şeması (v1.3)

Yelkovan Ödeme Hizmetleri A.Ş. — "müşteri-hesap-işlem" modülü test ortamı için.

## 0. Genel kurallar

- Üç dosya: `musteriler.csv`, `hesaplar.csv`, `islemler.csv`.
- Kodlama UTF-8 (BOM'lu ya da BOM'suz), alan ayracı `;`, ilk satır başlık. Başlıklar aşağıdaki tablolardaki sırayla ve aynı yazımla.
- Tarihler `dd.MM.yyyy` biçiminde (örn. `05.03.2021`).
- **Referans tarih (bugün): 30.09.2026.** Hiçbir tarih referans tarihten sonra olamaz.
- Tutarlar: ondalık ayırıcı virgül, tam 2 ondalık hane, binlik ayırıcı yok (örn. `1250,00`, `-89,90`).
- Boş değer = boş alan (iki `;` arası boşluksuz).
- Gerçek kişi/kurum verisi kullanılmaz; e-posta adresleri yalnızca `example.com` alan adında olur.

## 1. musteriler.csv — tam 200 satır

| Alan | Açıklama | Kural |
|---|---|---|
| musteri_no | `M` + 6 hane (örn. `M000123`) | benzersiz |
| musteri_tipi | `BIREYSEL` / `KURUMSAL` | KURUMSAL oranı %20–%30 |
| ad | bireysel müşterinin adı | BIREYSEL'de 2–30 karakter; KURUMSAL'da boş |
| soyad | bireysel müşterinin soyadı | BIREYSEL'de 2–30 karakter; KURUMSAL'da boş |
| unvan | şirket unvanı | KURUMSAL'da zorunlu, en fazla 100 karakter; BIREYSEL'de boş |
| tckn | T.C. Kimlik No | BIREYSEL'de zorunlu, geçerli, benzersiz; KURUMSAL'da boş |
| vkn | Vergi Kimlik No | KURUMSAL'da zorunlu, geçerli, benzersiz; BIREYSEL'de boş |
| dogum_tarihi | | BIREYSEL'de zorunlu; KURUMSAL'da boş |
| telefon | cep telefonu | `+905XXXXXXXXX` (boşluksuz, 13 karakter) |
| eposta | | küçük harf, `@example.com`, benzersiz |
| il | | 81 ilden biri, resmi yazımıyla (İstanbul, Iğdır, Şanlıurfa …) |
| kayit_tarihi | müşteri olma tarihi | 01.01.2015 – 30.09.2026 |
| senaryo | `NORMAL` / `SINIR` | bkz. Bölüm 5 |

Ad ve soyadlar Türkçe olmalı; bireysel müşterilerin en az %30'unda ad veya soyad Türkçe karakter (ç, ğ, ı, İ, ö, ş, ü …) içermeli. Bireysel müşteriler referans tarihte 18–100 yaş aralığında (sınırlar dahil) olmalı.

## 2. hesaplar.csv

| Alan | Açıklama | Kural |
|---|---|---|
| hesap_no | `H` + 8 hane | benzersiz |
| musteri_no | musteriler.musteri_no | her müşterinin 1–3 hesabı olur |
| iban | TR IBAN, 26 karakter, boşluksuz | geçerli kontrol basamakları, benzersiz |
| banka_kodu | `00991` / `00992` / `00993` | 00991 Yelkovan Katılım, 00992 Poyraz Bank, 00993 Lodos Yatırım (kurgusal) |
| doviz | `TRY` / `USD` / `EUR` | |
| acilis_tarihi | | |
| durum | `AKTIF` / `KAPALI` / `BLOKELI` | |
| kapanis_tarihi | | yalnızca KAPALI hesaplarda dolu |
| bakiye | | 0,00 – 5000000,00 |
| senaryo | `NORMAL` / `SINIR` | |

## 3. islemler.csv — en az 1000 satır

| Alan | Açıklama | Kural |
|---|---|---|
| islem_no | `I` + 10 hane | benzersiz |
| hesap_no | hesaplar.hesap_no | |
| islem_tarihi | | |
| islem_tipi | `HAVALE` / `EFT` / `FAST` / `KART` / `IADE` | |
| tutar | | IADE: -1000000,00 … -0,01; diğer tipler: 0,01 … 1000000,00 |
| karsi_iban | karşı taraf IBAN'ı | HAVALE, EFT ve FAST'te zorunlu (geçerli TR IBAN, işlemin yapıldığı hesabın IBAN'ından farklı); KART ve IADE'de boş |
| aciklama | serbest metin | en fazla 140 karakter, boş olabilir |
| senaryo | `NORMAL` / `SINIR` | |

## 4. İş kuralları

Modülün doğrulama katmanı aşağıdakileri kontrol ediyor; üretilen veri bunlara uymalı:

1. IBAN'ın banka kodu kısmı (5.–9. karakterler) hesabın `banka_kodu` değeriyle aynıdır.
2. Hesap, müşterinin kayıt tarihinden önce açılamaz.
3. Bireysel müşteri, kayıt tarihinde 18 yaşını doldurmuş olmalıdır.
4. Kapalı hesabın bakiyesi 0,00'dır; kapanış tarihi açılış tarihinden önce olamaz.
5. İşlem tarihi, hesabın açılış tarihinden önce olamaz; kapalı hesapta kapanış tarihinden sonra işlem olamaz.
6. FAST işlemlerinde tutar en fazla 100000,00 olabilir.

## 5. Sınır değer (SINIR) satırları

Her tabloda satırların **en az %15'i** `senaryo=SINIR` olarak işaretlenir ve her SINIR satırı aşağıdaki sınır koşullarından **en az birini gerçekten taşır**. Diğer satırlar `NORMAL`.

- **musteriler:** ad veya soyad tam 2 ya da tam 30 karakter; unvan tam 100 karakter; müşteri referans tarihte tam 18 yaşında (doğum tarihi 30.09.2008) ya da izin verilen en yaşlı (doğum tarihi 01.10.1925); doğum günü 29 Şubat; kayit_tarihi 01.01.2015 ya da 30.09.2026.
- **hesaplar:** bakiye 0,00 ya da 5000000,00; açılış tarihi müşterinin kayıt tarihiyle aynı gün; kapalı hesapta kapanış tarihi açılış tarihiyle aynı gün.
- **islemler:** tutarın mutlak değeri 0,01 ya da 1000000,00; FAST işleminde tutar tam 100000,00; işlem tarihi hesabın açılış tarihiyle aynı gün, kapalı hesapta kapanış tarihiyle aynı gün ya da 30.09.2026; açıklama tam 140 karakter.
