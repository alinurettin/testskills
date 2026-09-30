# Test verisi hazırlama ve canlı kesitin maskelenmesi

Merhaba,

Yelkovan Ödeme'de yeni "müşteri–hesap–işlem" modülünün test ortamını kuruyoruz. İki konuda desteğine ihtiyacım var.

## 1) Sentetik test verisi

`girdi/sema.md` dosyasındaki şemaya göre müşteri, hesap ve işlem verisi üretir misin? Gerçek kişilere ait hiçbir veri olmamalı ama test ortamındaki doğrulamalardan geçecek kadar gerçekçi olmalı (kimlik ve vergi numaraları, IBAN'lar vb. geçerli olsun). Sınır değer senaryoları da şemada anlatıldığı gibi olsun.

## 2) Canlı kesitin maskelenmesi

Operasyon ekibi canlıdan küçük bir kesit çekti: `girdi/canli_kesit/musteri_ozet.csv` ve `girdi/canli_kesit/destek_kayitlari.csv`. İki dosya `musteri_no` üzerinden birleşiyor. Bunu test ortamına koymadan önce kişisel verilerden arındırmamız lazım (KVKK). Beklentilerimiz:

- Maskelenmiş veriden gerçek kişilere geri dönülememeli — müşteri numarası dahil.
- İki dosya arasındaki ilişki korunmalı; maskeleme sonrası da `musteri_no` üzerinden birleşebilmeli.
- Maskeleme deterministik olmalı: aynı girdiyle her çalıştırmada birebir aynı çıktı.
- Maskelenen değerler format olarak geçerli kalmalı ki test ortamındaki doğrulamalar geçsin (kimlik numarası, telefon, e-posta). Maskelenmiş e-postalar `example.com` alan adını kullansın.
- Dosyalar kaynakla aynı sütunlara, aynı sütun sırasına ve aynı satır sırasına sahip olmalı (test otomasyonu buna bağlı).
- Raporlama ekibi bu veriyle yaş grubu (10 yıllık dilimler) ve il bazında dağılıma bakacak; bunlar bozulmasın. `musteri_tipi`, `cinsiyet`, `il`, `segment`, `kayit_no`, `tarih`, `kanal`, `konu`, `islem_tutari` ve `durum` alanları olduğu gibi kalmalı.
- Serbest metin alanları test senaryolarında anlamlı kalmalı; tamamen silmek ya da tek bir sabit metinle değiştirmek istemiyoruz, yalnızca kişisel veriler temizlensin.

## Girdiler

- `girdi/sema.md` — üretilecek verinin şeması ve kuralları
- `girdi/canli_kesit/musteri_ozet.csv` — müşteri özeti (canlı kesit)
- `girdi/canli_kesit/destek_kayitlari.csv` — destek kayıtları (canlı kesit)

## Teslimat

Her şeyi çalışma klasöründe `teslim/` altına koy:

```
teslim/
  uret.py   veya uret.js       ->  python uret.py <cikti_klasoru>        |  node uret.js <cikti_klasoru>
  maskele.py veya maskele.js   ->  python maskele.py <girdi_klasoru> <cikti_klasoru>
                                   |  node maskele.js <girdi_klasoru> <cikti_klasoru>
  uretim/     musteriler.csv, hesaplar.csv, islemler.csv
  maskeleme/  musteri_ozet.csv, destek_kayitlari.csv
  RAPOR.md
```

- Betikler yalnızca Python 3 standart kütüphanesi ya da Node.js yerleşik modülleriyle, internet bağlantısı olmadan çalışmalı.
- `<girdi_klasoru>`: iki kaynak dosyanın bulunduğu klasör (ör. `girdi/canli_kesit`). Betikler çıktı dosyalarını doğrudan `<cikti_klasoru>` içine yazsın.
- Çıktı dosyaları UTF-8 ve `;` ayraçlı olsun.
- Üretim betiği sabit bir tohumla (seed) her çalıştırmada aynı çıktıyı üretmeli.
- Maskelemede gizli anahtar/tuz kullanırsan `MASKELEME_ANAHTARI` ortam değişkeninden okunsun; değişken yoksa betikteki sabit test anahtarı kullanılsın. Teslim ettiğin çıktıları ortam değişkeni vermeden üret.
- `RAPOR.md` kısa olsun: hangi kişisel veriyi nerede bulduğun ve nasıl maskelediğin, üretilen verideki sınır değer dağılımı, kaynak veride dikkatini çeken sorunlar/tuhaflıklar ve betiklerin nasıl çalıştırılacağı.

Teşekkürler!
