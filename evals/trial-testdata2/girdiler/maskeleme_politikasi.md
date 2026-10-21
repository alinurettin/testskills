# Pusula Dijital Bank A.Ş. — UAT Veri Maskeleme Politikası

Doküman no: MP-04 · Sürüm 2.1 · Onay: Bilgi Güvenliği ve KVKK Uyum Birimi · Yürürlük: 2026-07-01

## 1. Kapsam ve amaç

Canlı ortamdan alınan müşteri, hesap ve işlem kesitleri UAT ortamına yüklenmeden önce bu politikaya göre maskelenir. Amaç iki yönlüdür:

- Maskelenmiş veride gerçek bir kişiyle ilişkilendirilebilecek hiçbir bilgi kalmamalıdır (KVKK m.4 ve m.12).
- Test senaryolarının dayandığı yapı, ilişkiler, tutarlar ve zaman aralıkları bozulmamalıdır.

## 2. Kaynak biçimi

- Dosyalar: `musteri.csv`, `hesap.csv`, `islem.csv`. UTF-8 (BOM'lu), alan ayırıcı `;`, satır sonu CRLF. Çok satırlı serbest metinler çift tırnak içindedir.
- Tarih biçimleri kaynak sistemlerden geldiği gibidir:
  - `dogum_tarihi`: `GG.AA.YYYY`
  - `kayit_tarihi`, `kurulus_tarihi`, `acilis_tarihi`: `YYYY-AA-GG`
  - `islem_tarihi`: `GG.AA.YYYY SS:DD:ss`
- Serbest metin alanları: `musteri.notlar` (CRM notu) ve `islem.aciklama` (işlem açıklaması). Bunlar şube personeli, çağrı merkezi ve kanallar tarafından elle girilir; yazım standardı yoktur.
- `hesap.csv` birincil anahtarı bileşiktir: (`sube_kodu`, `hesap_no`). `islem.csv` hesaba bu iki sütunla bağlanır.

## 3. Çıktı biçimi

- Aynı üç dosya; aynı başlıklar, sütun sırası, ayırıcı ve kodlama.
- **Satır silinmez, eklenmez, sırası değişmez.** Çıktının n. satırı, kaynağın n. satırının maskelenmiş hâlidir.
- Her sütun kaynaktaki yazım biçimini korur (tarih biçimleri dahil).

## 4. Temel ilkeler

1. **Kişisel veri:** Gerçek kişiye ait ya da onunla ilişkilendirilebilen her değer: TCKN, ad-soyad, e-posta, telefon, IBAN, hesap numarası, müşteri numarası. Değer nerede ve hangi yazımla geçerse geçsin maskelenir: yapısal sütunlar ve serbest metinler; boşluklu, tireli, noktalı, parantezli, ülke kodlu, büyük/küçük harfli ya da `[at]` gibi gizlenmiş yazımlar dahil. Müşteri olmayan üçüncü kişilerin (eş, vekil, yetkili, alıcı vb.) bilgileri de kişisel veridir.
2. **Deterministik:** Aynı anahtar ve aynı girdiyle her çalıştırma bayt bayt aynı çıktıyı üretir. Aynı orijinal değer, normalize edilmiş hâliyle (boşluk, tire, nokta, parantez, ülke kodu ve büyük/küçük harf farkları yok sayılarak), hangi dosyada, sütunda ya da yazımla geçerse geçsin aynı maskeli değere dönüşür.
3. **Gizli anahtar:** Takma adlar ve tarih kaydırma ofseti `MASKE_ANAHTARI` ortam değişkenindeki anahtardan türetilir. Anahtar ve ofset hiçbir çıktıya ya da rapora yazılmaz.
4. **Geçerlilik:** Maskeli değerler UAT'deki doğrulamalardan geçmelidir (TCKN/VKN sağlama kuralı, IBAN mod-97, e-posta biçimi). Orijinaliyle aynı kalan maskeli değer kabul edilmez. Doğrulama algoritmaları için `uretim_kurallari.md` Ek A'ya bakınız.
5. **İlişki bütünlüğü:** Tablolar arası tüm ilişkiler (müşteri–hesap, hesap–işlem, işlemin karşı IBAN'ının gösterdiği hesap) maskelemeden sonra da aynı satırlar arasında kurulabilmelidir.

## 5. Sütun bazında kurallar

### 5.1 musteri.csv

| Sütun | Kural |
|---|---|
| musteri_no | Takma ad: `M` + 6 rakam, benzersiz, deterministik |
| musteri_tipi | Korunur |
| tckn | Geçerli sağlamalı sahte TCKN; benzersiz, deterministik |
| vkn | AS/LTD: korunur (tüzel kişi verisi). SAHIS: geçerli sahte VKN ile değiştirilir (şahıs şirketi gerçek kişiye aittir) |
| ad, soyad | Sahte Türkçe ad/soyad (cinsiyetle uyumlu olması tercih edilir) |
| unvan | AS/LTD: korunur. SAHIS: unvan gerçek kişi adı içerdiğinden kişi adı kısmı maskelenir (faaliyet kısmı korunabilir) |
| sirket_turu | Korunur |
| dogum_tarihi | Kaydırılmaz; Bölüm 6'ya göre genelleştirilir |
| kurulus_tarihi | Bölüm 7'ye göre kaydırılır |
| cinsiyet, il, ilce | Yarı tanımlayıcı: Bölüm 6 |
| eposta | Sahte adres, alan adı `example.test`; benzersiz, deterministik |
| telefon | Sahte numara; yazım biçimi korunur (rakam dışı karakterler ve hane sayısı aynı kalır); cep numaralarında ulusal numaranın ilk hanesi `5` kalır |
| kayit_tarihi | Bölüm 7'ye göre kaydırılır |
| notlar | İçindeki kişisel veriler maskelenir, metnin geri kalanı korunur |

### 5.2 hesap.csv

| Sütun | Kural |
|---|---|
| sube_kodu | Korunur |
| hesap_no | Takma ad: 8 rakam, 0 ile başlamaz, deterministik; (sube_kodu, hesap_no) benzersizliği korunur |
| musteri_no | musteri.csv ile aynı eşleme |
| hesap_turu, doviz, kmh_limiti, bakiye | Korunur |
| acilis_tarihi | Bölüm 7'ye göre kaydırılır |
| iban | Maskeli `sube_kodu` ve maskeli `hesap_no`'dan, `uretim_kurallari.md` İK-07 yapısıyla yeniden hesaplanır (banka kodu `00990`, geçerli kontrol haneleri) |

### 5.3 islem.csv

| Sütun | Kural |
|---|---|
| islem_id, sube_kodu, islem_tipi, tutar | Korunur |
| hesap_no | hesap.csv ile aynı eşleme |
| islem_tarihi | Bölüm 7'ye göre kaydırılır; saat korunur |
| karsi_iban | Veri setindeki bir hesaba aitse o hesabın maskeli IBAN'ı. Diğer IBAN'lar deterministik sahte IBAN'a çevrilir: ülke kodu ve banka kodu korunur, kontrol haneleri yeniden hesaplanır |
| aciklama | İçindeki kişisel veriler maskelenir, metnin geri kalanı korunur |

## 6. Yarı tanımlayıcılar ve k-anonimlik

- Bireysel müşteriler için yarı tanımlayıcı kümesi: (`dogum_tarihi`, `il`, `ilce`, `cinsiyet`).
- Maskeli `musteri.csv`'de bu dört sütunun değer birleşimi, her bireysel müşteri için **en az 5** bireysel müşteride aynı olmalıdır (k ≥ 5).
- İzin verilen genelleştirmeler: `dogum_tarihi` → yıl (`YYYY`) veya en fazla 10 yılı kapsayan kapalı aralık (`YYYY-YYYY`, ör. `1980-1989`); `ilce` → `*`. `il` ve `cinsiyet` değiştirilemez.
- Bu genelleştirmelerle k ≥ 5 sağlanamayan kayıtlar baskılanır: dört sütunun dördü de `*` yapılır. Baskılanan kayıt sayısı bireysel müşteri sayısının **%5'ini** geçemez.
- Genelleştirilmiş değer gerçeği kapsamalıdır (kişinin doğum yılı verilen yılda ya da aralıkta olmalıdır).

## 7. Tarih kaydırma

- Olay tarihleri (`kayit_tarihi`, `kurulus_tarihi`, `acilis_tarihi`, `islem_tarihi`) tüm dosyalarda **tek ve aynı** gün ofsetiyle kaydırılır; böylece olaylar arasındaki süreler (kayıt → hesap açılışı → işlemler, bir havalenin iki bacağı vb.) aynen korunur.
- Ofset anahtardan deterministik olarak türetilir, geriye doğrudur ve −30 ile −365 gün arasındadır (0 olamaz).
- Saat bilgisi değişmez.

## 8. Maskelenmeyecek bilgiler

Test senaryoları aşağıdakilere dayandığından bunlar maskelenmez:

- Tüzel kişi (AS, LTD) unvanları ve VKN'leri, serbest metinde geçenler dahil.
- İşyeri, üye işyeri, site yönetimi ve kurum adları.
- Bankanın kendi kurumsal iletişim bilgileri (çağrı merkezi numarası vb.).
- Fatura, abone, dekont ve referans numaraları. TCKN sağlama kuralına uymayan 11 haneli numaralar TCKN değildir.
- Tutarlar, işlem tipleri, şube kodları, döviz cinsleri ve `HVL-…` havale referans kodları.

## 9. Betik

Maskeleme betiği gece çalışan UAT veri tazeleme işine eklenecektir:

- `maskele.py` (Python 3, yalnızca standart kütüphane) veya `maskele.js` (Node.js 24, yalnızca yerleşik modüller).
- Kullanım: `python maskele.py <girdi_klasoru> <cikti_klasoru>` (veya `node maskele.js <girdi_klasoru> <cikti_klasoru>`); anahtar `MASKE_ANAHTARI` ortam değişkeninden okunur.
- İnternet erişimi ve ek paket yoktur.
