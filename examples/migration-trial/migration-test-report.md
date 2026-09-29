# Veri Göçü Test Raporu – Müşteri (legacy MÜŞTERİ → yeni CRM `customers`)

| | |
|---|---|
| Nesne | Müşteri (customer) |
| Eşleme spesifikasyonu | `mapping-spec.md` v1.2 |
| Kaynak extract | `legacy_customers.csv` (cp1254, `;`, 40 satır) |
| Hedef extract | `new_customers.csv` (UTF-8, BOM yok, `,`, 41 satır) |
| Çalıştırma | Mock-1 mutabakatı, 2026-09-30 |
| Araç | `reconcile.py` (testing-data-migrations v0.6.0) + bağımsız Decimal kontrol toplamı hesabı |
| Kanıt dosyaları | `mapping.json`, `reconciliation-mock1.md`, `reconciliation-mock1.json` |
| Veri | Sentetik (kişisel veri yok) |

## 1. Yönetici özeti

**Karar: FAIL → Öneri: NO-GO.**

40 kaynak müşterinin 39'u hedefte eşleşti; 1 müşteri kayıp, 1 müşteri iki kez yüklenmiş, 1 test kaydı üretim hedefine girmiş. Eşleşen 39 kaydın 6'sında birer alan uyuşmazlığı var (bakiye ×100, bakiye −0,01, gün/ay yer değiştirmesi, yanlış durum kodu, iki farklı karakter bozulması). Toplam bakiye kaynakta **1.689.826,46**, hedefte **2.024.947,67** (fark **+335.121,21**); üç şubenin üçünde de kontrol toplamı tutmuyor. Spesifikasyonun §4 onay kriterlerinin hiçbiri (0 eksik, 0 beklenmeyen, 0 mükerrer, 0 alan farkı, 0,00 toplam farkı) karşılanmıyor.

Toplam 9 bulgu: **3 kritik, 6 yüksek**. Sınıf dağılımı: 4 dönüşüm hatası, 5 yükleme hatası, 0 kaynak veri kalitesi hatası. Ayrıca spesifikasyon için 9 açık soru var (bölüm 5).

## 2. Kapsam ve yöntem

Yapılanlar (seviye 1–4, `references/migration-testing.md` §4):
1. Eşleme spesifikasyonu gözden geçirildi, `mapping.json` olarak kodlandı (M1–M8, her kaynak kolonun kararı var; `FAKS` = taşınmıyor, DM-07).
2. Kaynak profillendi (boşluk, mükerrer, kod listesi, tarih geçerliliği, ondalık biçimi, kodlama, baş/son boşluk, kontrol karakteri).
3. Tam karşılaştırma yapıldı (örnekleme yok): satır sayısı, anahtar kümesi, mükerrer anahtar, dönüşüm uygulanmış alan karşılaştırması, şube bazında Decimal kontrol toplamları.
4. Kontrol toplamları scriptten bağımsız ikinci bir Decimal hesabıyla doğrulandı (aynı sonuç).

Yapılmayanlar (bu raporun kapsamı dışında, go kararı için gerekli):
- Seviye 5–7: hedef veritabanında referans bütünlüğü, iş kuralı kontrolleri, uygulama düzeyinde regresyon.
- Cutover provası: süre ölçümü, delta, yeniden çalıştırma/idempotency, rollback. (Migrasyon süreleri bize iletilmedi.)
- Extract bütünlüğü: extract satır sayılarının tablo sayılarıyla eşit olduğu teyit edilmedi (bkz. soru S9).

## 3. Kaynak profili

| Kontrol | Sonuç | Değerlendirme |
|---|---|---|
| Satır / tekil anahtar | 40 / 40; sıfır atıldıktan sonra da çakışma yok | temiz |
| Boş değerler | `EPOSTA` 1 boş (`1007`), `FAKS` 37 boş; diğer kolonlar dolu | M7 "boş boş kalır" kuralı kapsıyor |
| Kod listeleri | `SUBE_KODU` ∈ {34, 06, 35}; `DURUM` ∈ {A, P, K} | liste dışı kod yok, ret beklenmez |
| Tarihler | 40/40 geçerli `dd.MM.yyyy`; `29.02.1992` geçerli (artık yıl); 18 satırda gün ≤ 12 (gün/ay takası yalnızca alan karşılaştırmasıyla yakalanır) | temiz |
| Tutarlar | Hepsi Türkçe biçim; tek ondalıklı (`875,5`), çoklu binlik ayracı (`1.234.567,89`), negatif (`-150,00`, 1006, spec izin veriyor) | kurallarla kapsanıyor |
| Baş/son/çift boşluk | `AD`: 1003 (baştaki boşluklar), 1036 (sondaki boşluk), 1040 (çift boşluk); `EPOSTA`: 1016 | M2/M7 trim/collapse kapsıyor |
| Büyük harfli e-posta | 1003 | M7 lower kapsıyor |
| Kodlama | Kaynak geçerli cp1254; Türkçe karakterler kaynakta doğru (İbrahim Şahin, Gülşen Işık dahil) | kaynakta bozulma yok |
| Kontrol karakteri | yok | temiz |

Sonuç: Kaynakta düzeltme gerektiren bir veri kalitesi hatası bulunmadı. Hedefteki bozulmaların hiçbiri kaynaktan gelmiyor.

## 4. Mutabakat sonuçları

| Kural (spec §4) | Değer | Eşik | Sonuç |
|---|---:|---:|:---:|
| Hedefte eksik müşteri | 1 | 0 | ❌ |
| Hedefte beklenmeyen müşteri | 1 | 0 | ❌ |
| Hedefte mükerrer müşteri no | 1 (1035 ×2) | 0 | ❌ |
| Alan farkı (dönüşüm sonrası) | 6 | 0 | ❌ |
| Kontrol toplamı farkı (genel + şube) | 4 / 4 | 0,00 | ❌ |
| Kararı olmayan kaynak kolon | 0 | 0 | ✅ |

Kolon bazında: `full_name` 2, `birth_date` 1, `balance` 2, `status` 1, `branch` 0, `email` 0 uyuşmazlık (39 eşleşen kayıt üzerinde).

### Kontrol toplamı farklarının açıklaması (satır bulgularıyla tam uyumlu)
| Şube | Fark | Açıklayan bulgular |
|---|---:|---|
| ANK | −7.100,00 | 1017 eksik (−9.100,00) + 1035 mükerrer (+2.000,00) |
| IST | +342.221,22 | 1031 ×100 (+342.221,22) + 9001 test kaydı (0,00; adet +1) |
| IZM | −0,01 | 1009 bakiye −0,01 |
| Toplam | +335.121,21 | yukarıdakilerin toplamı |

Kontrol toplamı farkının satır düzeyinde açıklanamayan kısmı yok; ayrıca kapsam/sorgu hatası şüphesi yok.

## 5. Bulgular

Önem derecesi iş etkisine göre verildi (para, kimlik, hukuki ve müşteriye görünen veri önce), satır sayısına göre değil.

| ID | Anahtar | Kolon | Kaynak | Beklenen | Hedef | Sınıf | Önem | Sahip |
|---|---|---|---|---|---|---|---|---|
| MIG-01 | 1031 | balance | `3.456,78` | `3456.78` | `345678.00` | Dönüşüm hatası | Kritik | Migrasyon geliştirme |
| MIG-02 | 1017 | (satır) | satır mevcut, geçerli (06, `9.100,00`, A) | hedefte olmalı | yok | Yükleme hatası | Kritik | Migrasyon geliştirme / DBA |
| MIG-03 | 1035 | (anahtar) | 1 satır | 1 satır | 2 özdeş satır | Yükleme hatası | Kritik | Migrasyon geliştirme / DBA |
| MIG-04 | 9001 | (satır) | kaynakta yok | hedefte olmamalı | `TEST MÜŞTERİ`, IST, 0.00, ACTIVE | Yükleme hatası | Yüksek | Migrasyon geliştirme |
| MIG-05 | 1027 | status | `K` | `CLOSED` | `PASSIVE` | Dönüşüm hatası | Yüksek | Migrasyon geliştirme (+ S7) |
| MIG-06 | 1012 | birth_date | `05.03.1990` | `1990-03-05` | `1990-05-03` | Dönüşüm hatası | Yüksek | Migrasyon geliştirme |
| MIG-07 | 1009 | balance | `4.350,57` | `4350.57` | `4350.56` | Dönüşüm hatası | Yüksek | Migrasyon geliştirme |
| MIG-08 | 1004 | full_name | `İbrahim` + `Şahin` | `İBRAHİM ŞAHİN` | `Ä°BRAHÄ°M ÅžAHÄ°N` | Yükleme hatası (kodlama) | Yüksek | Migrasyon geliştirme / DBA |
| MIG-09 | 1022 | full_name | `Gülşen` + `Işık` | `GÜLŞEN IŞIK` | `GÜLÞEN IÞIK` | Yükleme hatası (kodlama) | Yüksek | Migrasyon geliştirme / DBA |

### Bulgu ayrıntıları ve kanıt

**MIG-01 – Bakiye ×100 (ondalık ayracı kaybı).** M5'e göre `3.456,78` → `3456.78` olmalı; hedefte `345678.00`. Hem binlik noktası hem ondalık virgülü silinmiş. Diğer 37 tutar (çoklu binlik ayraçlı `1.234.567,89` dahil) doğru dönüşmüş; bu yüzden hata tutar biçimine değil, bir kod yoluna/partiye bağlı olabilir. IST toplamını +342.221,22 bozuyor. Müşteri bakiyesi 100 kat şişik görünür: doğrudan finansal risk. Kanıt: `reconciliation-mock1.md` › `balance` örnekleri, ipucu "×100".

**MIG-02 – Müşteri 1017 kayıp.** Kaynak satırı her kurala uyuyor (kod listesi içinde, geçerli tarih ve tutar); spesifikasyona göre reddedilmesi için bir sebep yok. Ret/hata logu iletilmedi. ANK toplamını −9.100,00 bozuyor. Kontrol: yükleyicinin ret tablosu ve batch sınırları (1017 tek başına mı düştü, bir batch'in son/ilk kaydı mı?).

**MIG-03 – Müşteri 1035 iki kez yüklenmiş.** Hedefte 1035'in iki özdeş satırı var (ikincisi 1038 ile 1039 arasında). Kaynakta tek satır. İdempotent olmayan yeniden çalıştırma ya da çift batch belirtisi; hedefte `customer_id` için benzersizlik kısıtı yok ya da yükleme sırasında kapalıydı. ANK toplamını +2.000,00 bozuyor. Spec §2 "her müşteri tam bir kez" kuralını ihlal ediyor.

**MIG-04 – Test kaydı 9001 hedefte.** `TEST MÜŞTERİ`, doğum tarihi 2000-01-01, bakiye 0.00, ACTIVE. Spec §2 test/dummy kayıtları açıkça yasaklıyor. Bakiye 0 olduğu için tutar etkisi yok, ancak IST adedini +1 yapıyor ve üretimde aktif, sahte bir müşteri demek. Muhtemel neden: hedef ortam test verisiyle temizlenmeden kullanıldı ya da yükleme test seed'ini içeriyor. (Ortam kaynaklı çıkarsa sınıfı "ortam" olarak güncellenir.)

**MIG-05 – Durum K → PASSIVE.** 1027 kaynakta `K` (kapalı), hedefte `PASSIVE`. Diğer iki `K` kaydı (1011, 1038) doğru şekilde `CLOSED`. 1027'yi diğerlerinden ayıran özellik bakiyesinin `0,00` olması; spesifikasyonda olmayan bir "sıfır bakiyeli kapalı → pasif" mantığı kodda olabilir (bkz. S7). Kapalı bir müşterinin pasif görünmesi yeniden aktive edilmesine yol açabilir.

**MIG-06 – Doğum tarihi gün/ay yer değiştirmiş.** `05.03.1990` → `1990-05-03` yüklenmiş; olması gereken `1990-03-05`. Gün ≤ 12 olduğu için tarih geçerli görünüyor, yalnızca alan karşılaştırması yakalıyor. Kaynakta gün ≤ 12 olan 18 kayıt var; diğer 17'si doğru, yani sistematik bir biçim hatası değil, satıra/koda bağlı. Kimlik verisi (KYC, yaş hesabı) etkileniyor.

**MIG-07 – Bakiye 0,01 eksik.** `4.350,57` → `4350.56`. Kaynakta zaten 2 ondalık var; HALF_UP yuvarlamanın hiçbir etkisi olmamalı. Script ipucu "yuvarlama farkı" diyor, ancak gerçek neden büyük olasılıkla ikili kayan nokta (float) kullanımı ve kesme (truncate). Kök neden doğrulanmadı. IZM toplamını −0,01 bozuyor; spec para için tam eşitlik istiyor.

**MIG-08 – İsim çift UTF-8 kodlanmış.** `İBRAHİM ŞAHİN` hedefte `Ä°BRAHÄ°M ÅžAHÄ°N`: UTF-8 baytları cp1252/Latin-1 olarak okunup yeniden UTF-8'e yazılmış. Kaynakta isim doğru. Aynı karakterleri (İ, Ş) içeren diğer kayıtlar (ör. 1016 `DERYA ŞİMŞEK`, 1025 `İPEK ÜNAL`) doğru; hata tek satırda/partide.

**MIG-09 – İsim cp1254 → cp1252 bozulması.** `GÜLŞEN IŞIK` hedefte `GÜLÞEN IÞIK`: cp1254 baytları cp1252/Latin-1 ile çözülmüş (Ş → Þ). Ü doğru kaldığı için gözden kaçması kolay. MIG-08'den farklı bir mekanizma, bu yüzden ayrı kayıt. İki bulgu aynı yükleme/kodlama yolunda ortak bir kök nedene işaret edebilir; düzeltmede birlikte ele alınmalı.

### Yanlış pozitif / belirsiz noktalar
- `email` boş oranı "2,5 → 2,44" farklı görünüyor; bu bir bulgu değil, payda farkı (40 beklenen / 41 hedef satır). 1007'nin boş e-postası doğru şekilde boş taşınmış.
- MIG-07'nin sınıfı dönüşüm hatası; kök neden (float + kesme) hipotez.
- MIG-04 ortam kaynaklıysa sınıfı "ortam" olabilir; spec gereği yine de hata.
- MIG-05 spesifikasyonda olmayan bir iş kuralından kaynaklanıyorsa sınıfı "eşleme spesifikasyonu boşluğu"na döner; spec şu haliyle `K → CLOSED` diyor, yani şu an hata.

## 6. Eşleme spesifikasyonu soruları (analist / veri sahibi)

| # | Kural | Soru |
|---|---|---|
| S1 | M4, M6 | "Diğer kodlar reddedilir": reddedilen satırlar nereye yazılıyor, kim inceliyor, mutabakatta "eksik" sayılıyor mu? Ret logu teste iletilmeli (MIG-02'nin analizi için şart). |
| S2 | M5 | Negatif tutarlarda "round half up" yönü nedir (−0,005 → −0,01 mi, 0,00 mı)? Kaynakta 2'den fazla ondalık gelebilir mi? Hedef tipi `DECIMAL(18,2)` mi? |
| S3 | M3 | Geçersiz/imkânsız ya da boş doğum tarihi (`00.00.0000`, `31.02.xxxx`, `01.01.1900` "bilinmiyor") kuralı yok. |
| S4 | M1 | Boş `MUSTERI_NO` ve sıfırlar atıldıktan sonra çakışan numaralar (`01017` ve `001017`) için kural yok. |
| S5 | M2 | `AD` veya `SOYAD` boşsa ne olur? `full_name` hedefte maksimum uzunluk nedir, uzun isim kesilir mi reddedilir mi (UTF-8'de Türkçe harf 2 bayt)? |
| S6 | M5, M3, M6 | Null/boş kuralı yalnızca `EPOSTA` için tanımlı; `BAKIYE`, `DURUM`, `SUBE_KODU` boşsa ret mi, varsayılan mı? |
| S7 | M6 | Sıfır bakiyeli kapalı müşteri için `PASSIVE` gibi bir istisna kuralı var mı (MIG-05)? Yoksa kod spesifikasyona uydurulmalı. |
| S8 | M7 | E-posta biçim doğrulaması var mı; geçersiz adres taşınır mı, temizlenir mi? |
| S9 | §1, §2 | Extract'ların tablo sayılarıyla uyumu kim teyit ediyor? Kaynak extract'ın kesim (snapshot) zamanı ve cutover sonrası delta (ekleme/güncelleme/silme) kuralı tanımlanmalı. |

## 7. Go / No-Go önerisi

**NO-GO.** Gerekçe: 3 kritik (para ×100, kayıp müşteri, mükerrer müşteri) ve 6 yüksek önemli açık hata; spec §4 onay kriterlerinin tamamı ihlal ediliyor; toplam bakiye farkı +335.121,21. Kabul edilmiş istisna yok.

### Go için onay kriterleri (bir sonraki mock'ta hepsi sağlanmalı)
| # | Kriter | Eşik |
|---|---|---|
| 1 | Kararı olmayan kaynak kolon | 0 |
| 2 | Hedefte eksik müşteri (belgelenmiş kapsam dışı hariç) | 0 |
| 3 | Hedefte beklenmeyen müşteri (test/dummy dahil) | 0 |
| 4 | Hedefte mükerrer `customer_id`; hedefte benzersizlik kısıtı etkin | 0; kısıt açık |
| 5 | `balance` kontrol toplamı farkı, genel ve şube bazında | 0,00 |
| 6 | Kritik kolonlarda alan farkı (`customer_id`, `balance`, `status`, `birth_date`, `full_name`) | 0 |
| 7 | Kritik olmayan kolonlarda alan farkı | 0 ya da sahibi ve gerekçesi olan kabul edilmiş istisna (`mapping.json` › `accepted_exceptions`) |
| 8 | Spesifikasyon soruları S1–S9 | yanıtlanmış, spec v1.3'e ve `mapping.json`'a işlenmiş |
| 9 | MIG-01…09 | kapatılmış; düzeltme sonrası **tam** mutabakat yeniden koşturulmuş (düzeltmeler başka satırları kaydırabilir) |
| 10 | Yeniden çalıştırma / idempotency testi (MIG-03 nedeniyle zorunlu) | yükleme N. adımda kesilip yeniden başlatıldığında mükerrer 0, toplam farkı 0,00 |
| 11 | Hedefte referans bütünlüğü ve iş kuralları (ör. CLOSED ⇒ bakiye kuralı, S7 yanıtına göre) | 0 ihlal |
| 12 | Üretim hacminde prova süresi | ≤ cutover penceresi − anlaşılan pay (bir yeniden çalıştırma dahil) |
| 13 | Rollback | prova edilmiş ve süresi ölçülmüş |
| 14 | Göç sonrası regresyon: eski kayıtları açma/düzenleme/kaydetme, Türkçe karakterle arama (İ/ı, Ş), şube bazında bakiye raporunun eski sistemle karşılaştırılması | geçti; açık kritik/yüksek hata yok |

### Önerilen sonraki adımlar
1. Geliştirme: MIG-01, 06, 07 için tutar ve tarih ayrıştırmasının tek bir, locale'e açıkça bağlı (Decimal, `dd.MM.yyyy`) kod yolundan geçtiğini doğrulayın; tek satırlık bu hataların hangi batch/kod yolundan geldiğini bulun.
2. Geliştirme/DBA: Yükleme zincirinde kodlamayı uçtan uca sabitleyin (cp1254 okuma → UTF-8 yazma, tek dönüşüm) (MIG-08, 09); `customer_id` benzersizlik kısıtını açın (MIG-03); ret logunu teste verin (MIG-02); hedef ortamı test verisinden temizleyin (MIG-04).
3. Analist/veri sahibi: S1–S9'u yanıtlayıp spec v1.3'ü yayımlayın; test ekibi `mapping.json`'ı günceller.
4. Test: Düzeltmelerden sonra Mock-2'de tam mutabakat (`reconciliation-mock2.md`), ardından seviye 5–7 kontrolleri ve cutover provası.

## 8. Sınırlar
- Tek varlık (müşteri) ve 40 satırlık sentetik extract; hesap/işlem gibi bağlı varlıklar ve yetim kontrolleri kapsam dışı.
- Tarihler metin olarak karşılaştırıldı; hedef extract ISO biçiminde olduğu için geçerli.
- Script ipuçları sezgiseldir; MIG-07 ve MIG-05 kök nedenleri geliştirici tarafından doğrulanmalı.
- Rapor sentetik veriyle hazırlandı; gerçek veriyle kullanılırsa kişisel alanlar (isim, e-posta, doğum tarihi) paylaşımdan önce maskelenmeli, yalnızca anahtarlar bırakılmalıdır (KVKK).
