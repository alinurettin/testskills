# Pusula Dijital Bank A.Ş. — Test Verisi Üretim Kuralları

İçe aktarma şeması sürüm 3.2 · Sahibi: Çekirdek Bankacılık Geçiş Projesi (CBG) · Son güncelleme: 2026-09-18

Yeni çekirdek bankacılık sisteminin toplu içe aktarma modülü aşağıdaki kurallara göre çalışır. Kurala uymayan **tek bir satır bile** olsa ilgili dosya bütünüyle reddedilir. Bu doküman, test ekibinin üreteceği sentetik verinin uyması gereken şemayı, iş kurallarını ve zorunlu sınır değer satırlarını tanımlar.

## 1. Genel biçim

- Üç dosya: `musteri.csv`, `hesap.csv`, `islem.csv`.
- Kodlama UTF-8, alan ayırıcı noktalı virgül (`;`), ilk satır başlık (sütunlar aşağıdaki sırayla ve adlarıyla).
- Tarihler `YYYY-MM-DD`.
- Tutarlar nokta ondalık ayırıcılı ve **tam 2 ondalık** (`1250.00`, `-35.40`); binlik ayırıcı yok.
- Boş alan = boş dize.
- Referans tarih (veri kesim günü): **2026-09-30**. Hiçbir tarih bu günden sonra olamaz.
- Hacim: en az **150 müşteri**, **300 hesap**, **2000 işlem**. Her müşterinin en az 1 hesabı olmalı; hesapların en az %90'ında en az 1 işlem bulunmalı.
- Veri tamamen sentetik olmalıdır: e-posta alan adı yalnızca `example.com` veya `example.test`; telefonlar 500 test bloğundan; IBAN banka kodları aşağıda verilen test kodlarından.

## 2. Şema

### 2.1 musteri.csv

`musteri_no;musteri_tipi;tckn;vkn;ad;soyad;unvan;sirket_turu;dogum_tarihi;kurulus_tarihi;cinsiyet;il;ilce;eposta;telefon;kayit_tarihi`

| Sütun | BIREYSEL | KURUMSAL |
|---|---|---|
| musteri_no | `M` + 6 rakam, dosyada benzersiz | aynı |
| musteri_tipi | `BIREYSEL` | `KURUMSAL` |
| tckn | zorunlu, geçerli TCKN (Ek A) | boş |
| vkn | boş | zorunlu, geçerli VKN (Ek A) |
| ad, soyad | zorunlu | boş |
| unvan | boş | zorunlu |
| sirket_turu | boş | `AS`, `LTD` veya `SAHIS` |
| dogum_tarihi | zorunlu | boş |
| kurulus_tarihi | boş | zorunlu, 1950-01-01 veya sonrası |
| cinsiyet | `E` veya `K` | boş |
| il, ilce | Ek B'deki listeden geçerli bir il/ilçe çifti | aynı |
| eposta | zorunlu, benzersiz, `^[a-z0-9._-]+@example\.(com\|test)$` | aynı |
| telefon | zorunlu, `+90 500 ddd dd dd` biçiminde (ör. `+90 500 123 45 67`) | aynı |
| kayit_tarihi | zorunlu, 2005-01-01 ile 2026-09-30 arası | aynı |

TCKN ve VKN değerleri dosya genelinde benzersiz olmalıdır.

### 2.2 hesap.csv

`sube_kodu;hesap_no;musteri_no;hesap_turu;doviz;kmh_limiti;acilis_tarihi;iban;bakiye`

- **Birincil anahtar bileşiktir: (sube_kodu, hesap_no).** Aynı `hesap_no` farklı şubelerde ayrı hesaplar olarak bulunabilir.
- `sube_kodu`: Ek C'deki kodlardan biri. `hesap_no`: 8 rakam, `0` ile başlamaz.
- `musteri_no`: musteri.csv'de bulunmalı.
- `hesap_turu`: `VADESIZ` veya `KMH` (kredili mevduat hesabı; limit dahilinde eksi bakiyeye izin verir).
- `doviz`: `TRY`, `USD` veya `EUR`.
- `kmh_limiti`: KMH hesapta 1000.00 ile 50000.00 arası; VADESIZ hesapta `0.00`.
- `acilis_tarihi`, `iban`, `bakiye`: bkz. iş kuralları.

### 2.3 islem.csv

`islem_id;sube_kodu;hesap_no;islem_tarihi;islem_tipi;tutar;karsi_iban;aciklama`

- `islem_id`: pozitif tam sayı, benzersiz.
- (`sube_kodu`, `hesap_no`): hesap.csv'de bulunan bir hesabı göstermeli (iki sütun birlikte).
- `islem_tipi`: `YATIRMA`, `HAVALE_GELEN`, `FAIZ` (tutar pozitif) veya `CEKME`, `HAVALE_GIDEN`, `MASRAF` (tutar negatif). Tutar 0 olamaz.
- `karsi_iban`: `HAVALE_GELEN` ve `HAVALE_GIDEN` için zorunlu, geçerli TR IBAN (boşluksuz, büyük harf) ve işlemin kendi hesabının IBAN'ı olamaz; diğer tiplerde boş.
- `aciklama`: serbest metin, boş olabilir; kişisel veri içermemeli.

## 3. İş kuralları

- **İK-01 Müşteri tipi:** 2.1'deki tablo. Müşterilerin en az %25'i KURUMSAL, en az %50'si BIREYSEL olmalı.
- **İK-02 Kayıt:** Bireysel müşteri kaydı yalnızca 18 yaşını doldurmuş kişiler için yapılır: `kayit_tarihi` ≥ 18. yaş günü. Kurumsal: `kayit_tarihi` ≥ `kurulus_tarihi`.
- **İK-03 Yaş:** Referans tarihte 18–100 yaş: `dogum_tarihi` ≥ 1926-10-01 ve 18. yaş günü ≤ 2026-09-30.
- **İK-04 Hesap açılışı:** `acilis_tarihi` ≥ müşterinin `kayit_tarihi`; BIREYSEL için `acilis_tarihi` ≥ 18. yaş günü; KURUMSAL için `acilis_tarihi` ≥ `kurulus_tarihi`; `acilis_tarihi` ≤ 2026-09-30.
- **İK-05 29 Şubat doğumlular:** 18. yaş günü artık yıl olmayan bir yıla denk gelirse **1 Mart** kabul edilir (Hukuk görüşü HG-2019/07). Bu kural İK-02, İK-03 ve İK-04'te geçerlidir.
- **İK-06 KMH:** Yalnızca BIREYSEL müşterilere ve yalnızca `TRY` hesap olarak açılabilir.
- **İK-07 IBAN:** `TR` + 2 kontrol hanesi + banka kodu `00990` + rezerv `0` + `sube_kodu` (4) + `0000` + `hesap_no` (8) = 26 karakter; ISO 13616 mod-97 kontrolü geçerli; dosyada benzersiz.
- **İK-08 İşlem tarihi:** `acilis_tarihi` ≤ `islem_tarihi` ≤ 2026-09-30.
- **İK-09 Bakiye:** `bakiye` = o hesabın tüm işlemlerinin `tutar` toplamı (kuruşu kuruşuna). İşlemi olmayan hesapta `0.00`.
- **İK-10 Ara bakiye:** Bir hesabın işlemleri (`islem_tarihi`, `islem_id`) artan sırasıyla uygulandığında, her işlemden sonraki bakiye VADESIZ hesapta 0.00'ın, KMH hesapta `-kmh_limiti` değerinin altına hiçbir zaman inmemelidir.
- **İK-11 Karşı IBAN:** `HAVALE_GIDEN` işlemlerinin en az %20'si veri setindeki başka bir hesabın IBAN'ına (iç transfer) gitmeli. Veri seti dışındaki IBAN'larda banka kodu `00991`–`00998` aralığında olmalı (gerçek banka kodu kullanılmaz).
- **İK-12 Bileşik anahtar sınaması:** En az 3 farklı `hesap_no` değeri en az iki farklı şubede bulunmalı.

## 4. Zorunlu sınır değer satırları

- **SD-1:** En az 5 bireysel hesap, sahibinin 18. yaş gününde açılmış olmalı (`acilis_tarihi` = 18. yaş günü).
- **SD-2:** SD-1'deki hesaplardan en az 2'si 29 Şubat doğumlu müşterilere ait olmalı.
- **SD-3:** En az 3 kurumsal hesap, şirketin kuruluş gününde açılmış olmalı (`acilis_tarihi` = `kurulus_tarihi`).
- **SD-4:** En az 5 hesapta, hesabın açılış gününde yapılmış bir işlem bulunmalı.
- **SD-5:** En az 5 işlem referans tarihte (2026-09-30) yapılmış olmalı.
- **SD-6:** En az 5 VADESIZ hesapta, bir işlemden hemen sonra bakiye tam `0.00` olmalı.
- **SD-7:** En az 3 KMH hesapta, bir işlemden hemen sonra bakiye tam `-kmh_limiti` olmalı.
- **SD-8:** Hesapların en az %10'u SD-1, SD-3, SD-4, SD-6 veya SD-7 koşullarından en az birini sağlamalı.

## Ek A — Doğrulama algoritmaları

**TCKN** (11 hane, ilk hane 0 olamaz; d1…d11):
- d10 = ((d1 + d3 + d5 + d7 + d9) × 7 − (d2 + d4 + d6 + d8)) mod 10 (sonuç 0–9 aralığına getirilir)
- d11 = (d1 + d2 + … + d10) mod 10

**VKN** (10 hane; d1…d10):
- i = 1…9 için: t_i = (d_i + 10 − i) mod 10; v_i = (t_i × 2^(10−i)) mod 9; eğer t_i ≠ 0 ve v_i = 0 ise v_i = 9.
- d10 = (10 − (Σ v_i mod 10)) mod 10

**IBAN** (ISO 13616): ilk 4 karakter sona alınır, harfler sayıya çevrilir (A=10 … Z=35; T=29, R=27), elde edilen sayı mod 97 = 1 olmalıdır. Kontrol haneleri, kontrol hanesi yerine `00` konarak hesaplanan değerin 98'den çıkarılmasıyla bulunur.

## Ek B — Geçerli il/ilçe çiftleri

| İl | İlçeler |
|---|---|
| İstanbul | Kadıköy, Beşiktaş, Üsküdar, Şişli, Bakırköy, Ataşehir |
| Ankara | Çankaya, Keçiören, Yenimahalle, Etimesgut |
| İzmir | Konak, Bornova, Karşıyaka, Buca |
| Bursa | Nilüfer, Osmangazi |
| Adana | Seyhan, Çukurova |
| Trabzon | Ortahisar |
| Şanlıurfa | Halfeti, Haliliye |
| Bayburt | Merkez |

## Ek C — Şube kodları

| Kod | Şube | İl |
|---|---|---|
| 0101 | Kadıköy | İstanbul |
| 0102 | Beşiktaş | İstanbul |
| 0103 | Üsküdar | İstanbul |
| 0207 | Çankaya | Ankara |
| 0208 | Keçiören | Ankara |
| 0315 | Konak | İzmir |
| 0316 | Bornova | İzmir |
| 0420 | Nilüfer | Bursa |
| 0512 | Seyhan | Adana |
| 0611 | Ortahisar | Trabzon |
