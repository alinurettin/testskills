# Görev: GÜM v3.2 için test tasarımı

**Kimden:** Derya Akın — Test Lideri, Poyraz Kargo (Gönderi Operasyonları Ekibi)
**Kime:** Kıdemli Test Analisti
**Konu:** GÜM v3.2 test tasarımı

Merhaba,

GÜM'ün (Gönderi Ücretlendirme Motoru) ve gönderi yaşam döngüsünün v3.2 spesifikasyonu onaylandı; geliştirme önümüzdeki sprintte başlıyor. Henüz çalışan bir sistem ya da kod yok, ama test tasarımının geliştirmeyle aynı anda hazır olmasını istiyoruz. Elindeki tek kaynak ekteki spesifikasyon.

Senden kıdemli bir test analistinden beklediğimiz kalitede bir test tasarımı rica ediyorum: somut test verisi ve kuruşu kuruşuna, günü gününe doğru beklenen sonuçlar. Geçen dönem otomasyondaki yanlış beklenen değerler yüzünden çok sayıda yanlış alarmla uğraştık; beklenen sonuçların doğruluğu bizim için en az kapsam kadar önemli.

Bu sürümde iki şeyi farklı yapıyoruz:

1. **Satır sınırı.** Koşu süresi ve bakım maliyeti nedeniyle her dosya için bir satır sınırı koyduk (aşağıda). Sınırı aşan dosyayı geri çeviriyoruz. Kapsamı bu sınırların içinde planlaman gerekiyor: az satırla riskli noktaların hepsine dokunan bir tasarım istiyoruz.
2. **Spesifikasyon bulguları ayrı bir dosyada.** Spesifikasyonda gördüğün çelişki, belirsizlik ve modelleme hatalarını ürün sahibiyle yapacağımız toplantıya götüreceğiz. Toplantı süremiz kısıtlı: yalnızca gerçekten düzeltilmesi gereken noktaları yaz. Başka bir maddeyle açıklığa kavuşan, yalnızca ilk bakışta çelişki gibi görünen noktalar toplantıda bize zaman kaybettiriyor.

## Girdiler

- `girdiler/GUM-spesifikasyon-v3.2.md` — onaylı spesifikasyon
- `girdiler/sablonlar/ucret-testleri.csv` — ücretlendirme testleri şablonu
- `girdiler/sablonlar/durum-testleri.csv` — gönderi durum testleri şablonu
- `girdiler/sablonlar/konfigurasyon-matrisi.csv` — E2E konfigürasyon matrisi şablonu
- `girdiler/sablonlar/spesifikasyon-bulgulari.csv` — spesifikasyon bulguları şablonu

## Beklenen teslimatlar (hepsi `cikti/` klasörüne)

| # | Dosya | İçerik | Satır sınırı |
|---|---|---|---|
| 1 | `cikti/ucret-testleri.csv` | GÜM ücret ve teslim tarihi test vakaları (Bölüm 2–9, Ek-B) | en fazla **40** |
| 2 | `cikti/durum-testleri.csv` | Gönderi yaşam döngüsü test vakaları (Bölüm 10) | en fazla **30** |
| 3 | `cikti/konfigurasyon-matrisi.csv` | E2E gönderi oluşturma regresyonunda koşulacak kombinasyonlar (Bölüm 11) | en fazla **24** |
| 4 | `cikti/spesifikasyon-bulgulari.csv` | Spesifikasyon bulguları | en fazla **8** |
| 5 | `cikti/test-tasarimi.md` | Kısa tasarım notu (en fazla bir sayfa): kullandığın teknikler, varsayımların, kapsam dışı bıraktıkların | — |

Satır sınırı başlık satırını ve `ORNEK-` satırlarını kapsamaz.

### 1. Ücretlendirme testleri

Beklediğimiz kapsam: her kuralın sınır değerleri (sınırın iki yanı), yuvarlamanın sonucu değiştirdiği noktalar, kuralların birbirini etkilediği durumlar (indirim seçimi, tavan, taban), tarih ve saat kuralları (kesim saati, hafta sonu, tatil, artık gün), hata kodları ve hata önceliği.

### 2. Durum testleri

Ekip standardımız:

- geçerli geçişlerin tamamı,
- art arda gerçekleşen iki geçerli geçişten oluşan her çift (1-switch kapsamı),
- her durumda, o durum için tabloda yer almayan en az bir olay,
- koşulu sağlanmayan her geçiş (hata kolu) ve sayaç/süre sınırlarının iki yanı,
- olay işleme kurallarının sırası (10.5).

### 3. Konfigürasyon matrisi

E2E regresyonu manuel koşuluyor; her kombinasyon yaklaşık 20 dakika sürüyor. İstediğimiz kapsam:

- altı faktörün **tüm ikili değer çiftleri** (pairwise), ve
- ücreti ve teslim tarihini belirleyen `hizmet` × `bolge` × `teslim_noktasi` için **tüm üçlü kombinasyonlar**.

Yalnızca desteklenen (11.2 kısıtlarını ihlal etmeyen) kombinasyonları yaz; kısıtlar yüzünden hiç oluşamayan çift ve üçlüler kapsam dışıdır.

### 4. Spesifikasyon bulguları

Her satır tek bir bulgu. Kolonlar:

- `bulgu_id`: `B-01`, `B-02`, …
- `bolumler`: bulgunun ilgili olduğu yer(ler). Spesifikasyondaki numarayla yaz; birden fazlaysa virgülle ayır. Madde için `6.3`, geçiş için `G7`, kısıt için `KS-2`, Ek-A örneği için `A-3`, Ek-B satırı için `B-2`. Örnek: `4.1,9.3`. Çelişkilerde çelişen iki yeri de, eksik tanımlarda eksikliğin ait olduğu bütün maddeleri yaz; bir bulguda en fazla dört yer olsun.
- `tur`: aşağıdaki kodlardan biri
  - `CELISKI` — spesifikasyonun iki yeri birbiriyle çelişiyor (kural–kural ya da örnek–kural).
  - `BELIRSIZLIK` — beklenen sonucu belirlemek için gereken bilgi eksik ya da tanımsız (tanımsız terim, eksik birim, belirtilmemiş öncelik).
  - `ERISILEMEZ` — hiçbir olay dizisiyle ulaşılamayan durum ya da hiçbir zaman gerçekleşemeyen geçiş.
  - `ONERI` — hata olmayan iyileştirme önerisi ya da not.
- `aciklama`: bulgunun kısa açıklaması ve önerdiğin çözüm.

## CSV kuralları

Otomasyon ekibi CSV dosyalarını doğrudan data-driven testlere besleyecek; bu yüzden biçime lütfen birebir uy:

- UTF-8, ayraç `;`, ilk satır şablondaki başlık satırı (kolon adlarını ve sırasını değiştirme, kolon ekleme).
- Kod değerlerini spesifikasyondaki gibi birebir yaz; büyük/küçük harf duyarlıdır (ör. `KURUMSAL`, `AYNI_GUN`, `ERR_BOYUT`, `TESLIM_BASARISIZ(neden=ADRESTE_YOK)`).
- Sayılarda ondalık ayırıcı nokta, binlik ayırıcı yok. Tutarlar 2 ondalıkla (ör. `172.54`), ücret ağırlığı 1 ondalıkla (ör. `5.5`), tarihler `YYYY-AA-GG`, kabul zamanı `YYYY-AA-GG SS:DD` biçiminde.
- Test koşucusu hücrelerin başındaki ve sonundaki boşlukları kırpar; boş hücre, alanın boş gönderildiği anlamına gelir.
- **Ücret testleri:** `beklenen_sonuc` `KABUL` ise `beklenen_ucret_agirligi`, `beklenen_indirim`, `beklenen_toplam` ve `beklenen_teslim_tarihi` kolonlarının dördünü de doldur. Hata bekleniyorsa `beklenen_sonuc` kolonuna hata kodunu yaz, diğer dört beklenen kolonu boş bırak.
- **Durum testleri:** `olay_dizisi`, gönderi oluşturulduktan sonra sırayla uygulanan olaylardır. Olaylar ` > ` ile ayrılır, parametreler parantez içinde `ad=deger` biçiminde yazılır (ör. `TRANSFERE_VER > IPTAL(aktor=OPERATOR)`). `beklenen_sonuc` dizideki **son olayın** sonucudur (`KABUL` ya da hata kodu); ondan önceki olayların hepsi kabul edilen olaylar olmalıdır (ön koşul hazırlığı). `beklenen_son_durum` ve `beklenen_deneme_sayisi`, son olaydan sonraki durum ve `deneme_sayisi` değeridir; üç beklenen kolonu her satırda doldur. Boş dizi yalnızca gönderinin oluşturulmasını ifade eder.
- Spesifikasyonun çeliştiği ya da belirsiz kaldığı bir noktaya test yazarsan, seçtiğin yorumu `aciklama` kolonunda belirt.
- Şablonlardaki `ORNEK-` ile başlayan satırlar yalnızca biçim örneğidir; silebilirsin.

Teşekkürler,
Derya
