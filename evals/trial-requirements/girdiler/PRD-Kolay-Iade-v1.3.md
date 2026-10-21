# Nergis Çarşı — Kolay İade ve Geri Ödeme

**Ürün Gereksinim Dokümanı (PRD) — Sürüm 1.3**

| Alan | Bilgi |
|---|---|
| Doküman sahibi | Defne Akyürek (Ürün Yöneticisi, Sipariş Sonrası Deneyim) |
| Paydaşlar | Ödeme Sistemleri, Gebze Depo Operasyonu, Müşteri Hizmetleri, Mobil Ekip, Pusula Kargo entegrasyon ekibi |
| Tarih | 18.09.2026 |
| Durum | Test analizine açık |

> Not: Nergis Çarşı A.Ş. ve Pusula Kargo kurgusal şirketlerdir; dokümandaki tüm sipariş, kişi ve tutar bilgileri örnek amaçlıdır.

### Sürüm geçmişi

| Sürüm | Tarih | Değişiklik |
|---|---|---|
| 1.0 | 12.08.2026 | İlk taslak |
| 1.2 | 03.09.2026 | Kategori istisnaları Ek-B'ye taşındı; Nergis Cüzdan bonusu (BR-09) eklendi |
| 1.3 | 18.09.2026 | Hızlı İade (BR-07) eklendi; geri ödeme başlatma süresi Ödeme ekibinin talebiyle güncellendi (BR-10) |

---

## 1. Amaç ve kapsam

Müşterilerin teslim aldıkları ürünler için çağrı merkezini aramadan web sitesi ve mobil uygulama üzerinden iade talebi oluşturabilmesi, iade paketini anlaşmalı kargo şubesine bir kodla teslim edebilmesi ve geri ödemesini uçtan uca takip edebilmesi amaçlanmaktadır. İş hedefi, iade kaynaklı çağrı merkezi aramalarını ilk 6 ayda %40 azaltmaktır.

**Kapsam içi**

- Satıcısı Nergis Çarşı olan ve Gebze deposundan gönderilen ürünler
- Kredi kartı, banka kartı ve kapıda ödeme (nakit veya kartla) ile verilmiş bireysel siparişler
- Web (masaüstü ve mobil tarayıcı), iOS ve Android uygulamaları

**Kapsam dışı:** Ürün değişimi, pazaryeri satıcılarının ürünleri, kurumsal (B2B) siparişler. Bu konular v2'de ele alınacaktır.

## 2. Tanımlar

| Terim | Tanım |
|---|---|
| Teslim tarihi | Pusula Kargo'nun gönderiyi "TESLİM EDİLDİ" olarak bildirdiği anın Türkiye saatine (UTC+3) göre takvim günü. |
| İade süresi | Teslim tarihini izleyen takvim gününden başlayarak sayılan gün sayısı. Sürenin son gününde saat 23:59:59'a (Türkiye saati) kadar oluşturulan talepler süre içinde kabul edilir. Örnek: 1 Ekim'de teslim edilen ve 15 günlük süreye tabi bir ürün için son talep anı 16 Ekim 23:59:59'dur. |
| İş günü | Pazartesi–Cuma arasındaki günler; resmî tatiller ve dinî bayram günleri hariçtir. Yarım gün olan arife günleri tam iş günü sayılır. İş günü cinsinden verilen sürelerde başlangıç günü sayılmaz; süre izleyen ilk iş gününden başlar ve son iş gününün sonunda (23:59:59, Türkiye saati) dolar. |
| Ürün satır tutarı | Bir sipariş satırındaki birim fiyat × adet (kupon öncesi). |
| Nergis Cüzdan | Müşterinin sonraki alışverişlerinde kullanabileceği TL bakiye. Cüzdan bakiyesi nakde veya karta aktarılamaz. |
| Hızlı İade | Depo kontrolü beklenmeden, iade paketi kargo şubesine teslim edildiği anda geri ödemenin başlatıldığı iade türü (koşullar: BR-07). |
| MH | Müşteri Hizmetleri |

## 3. Kullanıcı hikâyeleri

### US-1 İade talebi oluşturma

*Müşteri olarak, teslim aldığım bir ürün için uygulamadan iade talebi oluşturmak istiyorum; böylece çağrı merkezini aramak zorunda kalmam.*

- **AC-1.1** "Siparişlerim" ekranında, iade süresi dolmamış ve iade edilebilir kategorideki ürünlerin yanında "İade Et" butonu gösterilir.
- **AC-1.2** Müşteri aynı siparişten bir veya birden fazla ürünü ve iade edilecek adedi seçerek tek talep oluşturabilir.
- **AC-1.3** İade nedeni şu listeden seçilir: "Fikrimi değiştirdim", "Ürün hasarlı/kusurlu", "Yanlış ürün gönderildi", "Ürün açıklamadaki gibi değil". "Ürün hasarlı/kusurlu" seçildiğinde en az 1, en fazla 5 fotoğraf yüklenmesi zorunludur.
- **AC-1.4** Talep oluşturulduğunda ekranda talep numarası (İADE-YYYYMMDD-nnnnn biçiminde) gösterilir; müşteriye e-posta ve SMS ile bilgi verilir.
- **AC-1.5** İade süresi standart olarak 15 gündür (BR-01).

### US-2 İade kargo kodu

*Müşteri olarak, iade ürünümü anlaşmalı kargo şubesine bir kodla teslim etmek istiyorum; böylece kargo fişi doldurmakla uğraşmam.*

- **AC-2.1** Talep oluşturulduğunda Pusula Kargo entegrasyonu üzerinden 10 haneli iade kargo kodu üretilir ve talep detayında gösterilir.
- **AC-2.2** Kargo kodu üretildiği andan itibaren 7 gün geçerlidir; bu süre içinde kargoya verilmeyen talepler otomatik olarak kapatılır ve müşteriye bildirim gönderilir.
- **AC-2.3** Müşteri, paketi kargo şubesine teslim etmeden önce talebini "Talebi İptal Et" butonuyla iptal edebilir.
- **AC-2.4** Kargo şubesi paketi teslim aldığında talep durumu KARGODA olarak güncellenir.

### US-3 Geri ödeme

*Müşteri olarak, iadem onaylandığında paramı hızlıca geri almak istiyorum.*

- **AC-3.1** İade onaylandıktan sonra geri ödeme en geç 3 iş günü içinde başlatılır ve müşteriye bildirim gönderilir.
- **AC-3.2** Geri ödeme, siparişin ödendiği yönteme (orijinal ödeme yöntemine) yapılır. Müşteri dilerse orijinal ödeme yöntemi yerine Nergis Cüzdan'a iadeyi seçebilir; bu durumda ek bonus kazanır (BR-09).
- **AC-3.3** Geri ödeme tutarı BR-05 ve BR-06'ya göre hesaplanır ve talep detayında kalem kalem gösterilir.

### US-4 Depo kontrolü

*Depo operatörü olarak, gelen iade paketlerini kontrol edip sonucu sisteme girmek istiyorum; böylece geri ödeme doğru tutarla başlatılsın.*

- **AC-4.1** Operatör paketi barkod okuyucuyla okuttuğunda talep detayları ve müşterinin seçtiği iade nedeni ekranda görüntülenir.
- **AC-4.2** Ürün uygun durumda ise operatör "Onayla" seçeneğini seçer; değilse "Reddet" seçeneğini seçer ve ret nedenini serbest metin olarak girer.
- **AC-4.3** Tutarı 500 TL'nin üzerindeki iadelerde depo kontrolü tamamlanmadan geri ödeme başlatılamaz.

### US-5 Müşteri Hizmetleri işlemleri

*MH temsilcisi olarak, müşteri şikâyetlerinde iade talebini manuel yönetebilmek istiyorum; böylece mağdur müşterileri hızla memnun edebileyim.*

- **AC-5.1** MH temsilcisi, iade süresi geçmiş ürünler dahil, herhangi bir iade talebini manuel olarak onaylayabilir.
- **AC-5.2** MH temsilcisi gerekli gördüğü durumlarda geri ödeme tutarını değiştirebilir ve iade kargo ücretini müşteriye iade edebilir.
- **AC-5.3** MH ekranında müşterinin son 12 aydaki tüm iade talepleri listelenir.

### US-6 İade takibi

*Müşteri olarak, iademin hangi aşamada olduğunu görmek istiyorum.*

- **AC-6.1** Talep detayında Bölüm 5'teki durumlar zaman çizelgesi olarak gösterilir; tamamlanan adımlar yeşil, bekleyen adımlar gri, sorunlu adımlar kırmızı renkle belirtilir.
- **AC-6.2** Her durum değişikliğinde müşteriye mobil bildirim (push) gönderilir.

## 4. İş kuralları

- **BR-01** Standart iade süresi 15 gündür. Kategori bazlı istisnalar Ek-B'de tanımlıdır; Ek-B'de bir kategori için daha uzun bir süre tanımlanmışsa o süre geçerlidir.
- **BR-02** İade edilemeyen kategoriler (iç giyim ve mayo, kişiye özel üretilen ürünler, dijital kod ve hediye kartları) Ek-B'de "iade_edilebilir = HAYIR" olarak işaretlenmiştir; bu ürünlerde "İade Et" butonu gösterilmez.
- **BR-03** İade süresi ürün bazında hesaplanır; aynı siparişteki ürünler farklı tarihlerde teslim edilmiş olabilir.
- **BR-04** Kozmetik ve kişisel bakım ürünlerinde ambalajı veya koruma bandı açılmış ürünler iade alınmaz.
- **BR-05** İade kargo ücreti: "Ürün hasarlı/kusurlu", "Yanlış ürün gönderildi" ve "Ürün açıklamadaki gibi değil" nedenlerinde iade kargo ücretini Nergis Çarşı karşılar. "Fikrimi değiştirdim" nedeninde 39,90 TL iade kargo ücreti geri ödeme tutarından düşülür.
- **BR-06** Siparişe kupon uygulanmışsa, iade edilen her ürün için kuponun orantılı payı ürün satır tutarından düşülür: *Orantılı pay = Kupon tutarı × (İade edilen ürün satır tutarı ÷ Siparişteki tüm ürün satır tutarlarının toplamı)*. Siparişin gönderim kargo ücreti yalnızca siparişteki tüm ürünler iade edildiğinde geri ödenir.
- **BR-07** Hızlı İade: Risk skoru "düşük" olan müşterilerin, tutarı 500 TL'nin altındaki iadelerinde geri ödeme, paket kargo şubesine teslim edildiği anda başlatılır; depo kontrolü daha sonra yapılır.
- **BR-08** Aynı sipariş satırı için aynı anda yalnızca bir açık iade talebi bulunabilir.
- **BR-09** Nergis Cüzdan'a iade seçildiğinde, geri ödeme tutarının %3'ü kadar bonus cüzdana eklenir. Bonus, iade talebi başına en fazla 150,00 TL'dir ve kuruşa yarım yukarı yuvarlanır. Bonus, geri ödemeyle aynı anda tek seferde yüklenir.
- **BR-10** Onaylanan iadelerde geri ödeme, onay tarihinden itibaren 5 iş günü içinde başlatılır. Bankanın tutarı karta yansıtma süresi Nergis Çarşı'nın kontrolünde değildir; müşteri bildirimde bu konuda bilgilendirilir.
- **BR-11** Tüm tutarlar TL olarak, iki ondalık basamakla gösterilir.

## 5. İade durum yaşam döngüsü

| Durum | Açıklama | Sonraki durum |
|---|---|---|
| TALEP_ALINDI | Talep oluşturuldu, kargo kodu üretildi | KARGODA |
| KARGODA | Paket kargo şubesine teslim edildi | DEPODA |
| DEPODA | Paket Gebze deposuna ulaştı, kontrol bekleniyor | ONAYLANDI |
| ONAYLANDI | Depo kontrolü olumlu sonuçlandı | GERİ_ÖDEME_BAŞLATILDI |
| GERİ_ÖDEME_BAŞLATILDI | Geri ödeme talimatı bankaya veya cüzdana iletildi | TAMAMLANDI |
| TAMAMLANDI | Süreç tamamlandı | — |

Durumlar yalnızca tablodaki sıraya göre ilerler.

## 6. Fonksiyonel olmayan gereksinimler

- **NFR-1 Performans:** İade ekranları hızlı açılmalıdır. Kampanya dönemlerinde (ör. Kasım indirimleri) artan iade trafiğinde de sistem makul sürede yanıt vermelidir.
- **NFR-2 Yetkilendirme:** Müşteri yalnızca kendi hesabındaki siparişler için iade talebi görüntüleyebilir ve oluşturabilir; başka bir müşteriye ait talep numarasıyla yapılan sorgulara "Talep bulunamadı" yanıtı döner.
- **NFR-3 Kullanılabilirlik:** İade talebi, ürün seçiminden talep onayına kadar en fazla 3 ekranda tamamlanır.
- **NFR-4 Kayıt:** Talep durum değişiklikleri zaman damgasıyla uygulama loglarına yazılır; loglar 90 gün saklanır.
- **NFR-5 Platformlar:** Chrome, Safari, Edge ve Firefox'un son iki ana sürümü; iOS 16 ve üzeri; Android 10 ve üzeri.

---

## Ek-A: Örnek hesaplamalar (test ekibi için referans)

**Örnek 1 — Kısmi iade, kredi kartına**

Sipariş NRG-260914-0001: Koşu ayakkabısı 1 × 1.800,00 TL; Spor çorap (3'lü) 1 × 200,00 TL; Termos 1 × 1.000,00 TL. Ürün satır toplamı 3.000,00 TL; kupon (ILKALISVERIS) 300,00 TL; gönderim kargo ücreti 49,90 TL; müşterinin ödediği tutar 2.749,90 TL. Müşteri termosu "Ürün hasarlı/kusurlu" nedeniyle iade ediyor ve orijinal ödeme yöntemini (kredi kartı) seçiyor.

| Kalem | Tutar |
|---|---|
| Ürün satır tutarı | 1.000,00 TL |
| Kupon orantılı payı (300,00 × 1.000,00 ÷ 3.000,00) | −100,00 TL |
| İade kargo kesintisi (BR-05) | 0,00 TL |
| Gönderim kargo ücreti iadesi (kısmi iade, BR-06) | 0,00 TL |
| **Karta geri ödeme** | **900,00 TL** |

**Örnek 2 — Kısmi iade, Nergis Cüzdan'a**

Sipariş NRG-260915-0002: Kahve makinesi 1 × 4.200,00 TL; Çekirdek kahve (1 kg) 1 × 600,00 TL; Kupa 2 × 300,00 TL. Ürün satır toplamı 5.400,00 TL; kupon (EYLUL400) 400,00 TL; gönderim kargo ücretsiz; müşterinin ödediği tutar 5.000,00 TL. Müşteri kahve makinesini "Fikrimi değiştirdim" nedeniyle iade ediyor ve Nergis Cüzdan'ı seçiyor.

| Kalem | Tutar |
|---|---|
| Ürün satır tutarı | 4.200,00 TL |
| Kupon orantılı payı | −280,00 TL |
| İade kargo kesintisi (BR-05) | −39,90 TL |
| Geri ödeme tutarı | 3.880,10 TL |
| Cüzdan bonusu (%3, BR-09) | +116,40 TL |
| **Cüzdana yüklenecek toplam** | **3.996,50 TL** |

## Ek-B: Kategori bazlı iade kuralları

Ayrı dosya: `Ek-B-kategori-iade-kurallari.csv` (Kategori Yönetimi ekibi, 02.09.2026). Sütunlar: kategori kodu, kategori adı, iade edilebilirlik, iade süresi (gün) ve `acilmis_ambalaj_kabul`. `acilmis_ambalaj_kabul` sütunu, depo kontrolünde ambalajı açılmış bir ürünün iade olarak kabul edilip edilmeyeceğini belirtir.
