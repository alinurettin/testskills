# SFM — Sipariş Fiyatlandırma Motoru ve Sipariş Durum Yönetimi

## Fonksiyonel Spesifikasyon v1.4 (Onaylandı)

| Alan | Değer |
|---|---|
| Doküman no | DK-SPEC-214 |
| Şirket | Defne Kitap ve Kırtasiye A.Ş. (defnekitap.example) |
| Sahibi | Ödeme ve Sipariş Ekibi |
| Ürün sahibi | Burcu Yılmazer |
| Onay tarihi | 22.09.2026 |
| Durum | Onaylandı — geliştirmeye hazır |

---

## 1. Amaç ve kapsam

Bu doküman, Defne Kitap çevrimiçi mağazasında sepet onay adımında çalışan **Sipariş Fiyatlandırma Motoru'nun (SFM)** hesaplama kurallarını, **sipariş durum yaşam döngüsünü** ve uçtan uca ödeme akışının **desteklenen konfigürasyonlarını** tanımlar.

Kapsam dışı: stok kontrolü, ürün bazlı kampanyalar, fatura oluşturma, puanların hesaba geçmesi ve harcanması, kargo firması entegrasyonu.

## 2. Tanımlar ve hesaplama esasları

| Kısaltma | Tanım |
|---|---|
| AT | **Ara toplam:** sepetteki ürünlerin KDV dahil satış fiyatları toplamı. İstemci hesaplar, SFM'ye girdi olarak gelir. |
| KI | **Kupon indirimi** |
| NT | **Net ürün tutarı** = AT − KI |
| KU | **Kargo ücreti** (uzak bölge ek ücreti dahil) |
| HB | **Kapıda ödeme hizmet bedeli** |
| OT | **Ödenecek tutar** = NT + KU + HB |

2.1 Tüm tutarlar Türk lirası cinsindendir ve kuruş hassasiyetinde (2 ondalık) tutulur.

2.2 **Yuvarlama:** Yüzde ile hesaplanan her tutar, hesaplandığı anda kuruşa "yarım yukarı" kuralıyla yuvarlanır (ör. 12,344 → 12,34; 12,345 → 12,35). Bir tutara uygulanan üst sınır (tavan) kontrolü, yuvarlanmış tutar üzerinden yapılır.

2.3 Puan hesaplarında kesirler her zaman aşağı yuvarlanır.

## 3. SFM girdi alanları

SFM'nin fiyatlandırma çağrısı (`POST /api/v2/sepet/fiyatla`) aşağıdaki alanları alır. Kod değerleri büyük harfle ve birebir yazılmalıdır.

| Alan | Geçerli değerler | Açıklama |
|---|---|---|
| `uyelik` | `MISAFIR`, `KLASIK`, `ALTIN` | Zorunlu. |
| `ara_toplam` | 0'dan büyük, en fazla 2 ondalık basamaklı sayı | Zorunlu. Ondalık ayırıcı nokta, binlik ayırıcı yok (ör. `1499.90`). |
| `kupon` | boş (kupon yok), `DEFNE10`, `KITAP50` | Bkz. Bölüm 5. |
| `teslimat_tipi` | `STANDART`, `HIZLI`, `MAGAZA` | Zorunlu. `MAGAZA` = mağazadan teslim al. |
| `bolge` | `NORMAL`, `UZAK` | `STANDART` ve `HIZLI` için zorunlu; `MAGAZA` seçildiğinde dikkate alınmaz ve doğrulanmaz (boş olabilir). |
| `odeme_yontemi` | `KREDI_KARTI`, `BANKA_KARTI`, `KAPIDA_ODEME`, `CEPPAY` | Zorunlu. |

3.1 Zorunlu bir alanın eksik olması, alana tanımsız bir değer girilmesi veya `ara_toplam` değerinin yukarıdaki biçim kuralına uymaması durumunda SFM `ERR_GECERSIZ_GIRDI` döner.

3.2 `bolge` değeri adres servisinden gelir. Teslimat ilçesi Uzak Bölge Listesi'nde ise (ör. ada ilçeleri) `UZAK`, değilse `NORMAL` olur. SFM listeyi bilmez, yalnızca `bolge` alanını kullanır.

3.3 SFM, ödeme yönteminin platform veya üyelik uygunluğunu (bkz. 11.2) kontrol etmez; bu kısıtlar ödeme ekranında uygulanır. Kapıda ödemeye ilişkin Bölüm 7 kuralları ise SFM tarafından uygulanır. `KREDI_KARTI`, `BANKA_KARTI` ve `CEPPAY` fiyatlandırmada birbirinden farksızdır.

## 4. Sepet limitleri

4.1 AT 150,00 TL'den küçükse sipariş verilemez: `ERR_MIN_SEPET`.

4.2 AT 20.000,00 TL'den büyükse sipariş verilemez: `ERR_MAX_SEPET`.

4.3 Sepet limitleri, kupon uygulanmadan önceki tutar (AT) üzerinden kontrol edilir.

## 5. Kuponlar

5.1 Bir siparişte en fazla bir kupon kullanılabilir.

5.2 Kupon kodu büyük/küçük harf duyarlıdır ve tam eşleşmeyle doğrulanır; baştaki ve sondaki boşluklar kırpılır. Tanımsız bir kod girilirse `ERR_KUPON_GECERSIZ` döner.

5.3 **DEFNE10:** AT'nin %10'u kadar indirim. İndirim tutarı en fazla 150,00 TL'dir. Tüm üyelik seviyelerinde (`MISAFIR` dahil) geçerlidir.

5.4 **KITAP50:** 50,00 TL sabit indirim. Yalnızca `KLASIK` ve `ALTIN` üyeler için ve AT ≥ 400,00 TL olduğunda geçerlidir.

5.5 Kupon kodu tanımlı ancak kuponun koşulları sağlanmıyorsa hata dönmez: kupon uygulanmaz (KI = 0,00), sipariş kuponsuz fiyatlandırılır ve yanıtta `kupon_uygulandi = false` döner.

## 6. Kargo ücreti

6.1 Teslimat tipine göre taban ücretler:

| Teslimat tipi | Taban ücret |
|---|---|
| `STANDART` | 39,90 TL |
| `HIZLI` (ertesi gün) | 79,90 TL |
| `MAGAZA` | 0,00 TL |

6.2 **Ücretsiz standart teslimat:** NT ≥ 750,00 TL olan siparişlerde `STANDART` teslimat taban ücreti alınmaz.

6.3 **Altın üye avantajı:** `ALTIN` üyelerin `STANDART` teslimatları her durumda ücretsizdir; bu avantaj uzak bölge ek ücretini de kapsar.

6.4 **Hızlı teslimat:**
- a) 6.2 ve 6.3'teki ücretsiz teslimat avantajları `HIZLI` teslimata uygulanmaz.
- b) NT ≥ 750,00 TL ise `HIZLI` taban ücretinden 39,90 TL indirim yapılır (KU = 40,00 TL).
- c) Üyelik seviyesi `HIZLI` teslimat ücretini etkilemez.
- d) `HIZLI` teslimat yalnızca `NORMAL` bölgeye yapılır; `UZAK` bölge için `ERR_TESLIMAT_BOLGE` döner.

6.5 **Uzak bölge ek ücreti:** `UZAK` bölgeye `STANDART` teslimatta taban ücrete 25,00 TL eklenir. 6.2 kapsamındaki ücretsiz standart teslimat bu ek ücreti kapsamaz (ek ücreti yalnızca 6.3 kapsar).

6.6 **Mağazadan teslim:** `MAGAZA` seçildiğinde KU = 0,00 TL'dir; `bolge` dikkate alınmaz.

## 7. Kapıda ödeme

7.1 `KAPIDA_ODEME` yalnızca `STANDART` teslimatla kullanılabilir; diğer teslimat tiplerinde `ERR_KAPIDA_UYGUNLUK` döner.

7.2 Kapıda ödeme hizmet bedeli (HB) 12,90 TL'dir. Kargo ücretinden ayrı tahsil edilir; ücretsiz teslimat ve `ALTIN` üyelik avantajlarından etkilenmez. Diğer ödeme yöntemlerinde HB = 0,00 TL'dir.

7.3 Kuryenin nakit/POS tahsilat sınırı nedeniyle, kapıda ödemeli siparişlerde OT (HB dahil) 5.000,00 TL'yi aşamaz; aşarsa `ERR_KAPIDA_LIMIT` döner.

## 8. Sadakat puanı

8.1 Kazanılacak puan NT üzerinden hesaplanır; KU ve HB puana dahil edilmez.

8.2 Taban puan = ⌊NT / 10⌋ (her tam 10 TL için 1 puan).

8.3 Üyelik seviyesine göre kazanılacak puan:

| Üyelik | Kazanılacak puan |
|---|---|
| `MISAFIR` | 0 |
| `KLASIK` | taban puan |
| `ALTIN` | ⌊taban puan × 1,5⌋ |

8.4 Puan yalnızca başarılı (`KABUL`) fiyatlandırma yanıtında döner.

## 9. Yanıt yapısı ve hata öncelik sırası

9.1 Başarılı yanıt: `durum = KABUL`, `kupon_indirimi`, `net_tutar`, `kargo_ucreti`, `hizmet_bedeli`, `odenecek_tutar`, `kazanilacak_puan`, `kupon_uygulandi`.

9.2 Hata yanıtında yalnızca hata kodu döner; tutar ve puan alanları dönmez.

9.3 Birden fazla hata koşulu aynı anda oluşursa aşağıdaki listede **önce gelen** hata döner:

1. `ERR_GECERSIZ_GIRDI`
2. `ERR_KUPON_GECERSIZ`
3. `ERR_MIN_SEPET`
4. `ERR_MAX_SEPET`
5. `ERR_TESLIMAT_BOLGE`
6. `ERR_KAPIDA_UYGUNLUK`
7. `ERR_KAPIDA_LIMIT`

## 10. Sipariş durum yaşam döngüsü

10.1 **Durumlar**

| Durum | Açıklama | Son durum mu? |
|---|---|---|
| `ODEME_BEKLENIYOR` | Sipariş oluşturuldu, ödeme bekleniyor | Hayır |
| `ONAYLANDI` | Ödeme alındı veya kapıda ödemeli sipariş onaylandı | Hayır |
| `HAZIRLANIYOR` | Depoda hazırlanıyor | Hayır |
| `KARGODA` | Kargo firmasına teslim edildi, dağıtımda | Hayır |
| `TESLIM_EDILEMEDI` | Teslim denemesi başarısız, yeniden dağıtım bekleniyor | Hayır |
| `TESLIM_EDILDI` | Müşteriye teslim edildi | Hayır |
| `IADE_TALEP_EDILDI` | Müşteri iade talebi açtı, inceleniyor | Hayır |
| `IADE_EDILDI` | İade tamamlandı | Evet |
| `IPTAL_EDILDI` | Sipariş iptal edildi | Evet |
| `DEPOYA_DONDU` | Teslim edilemeyen sipariş depoya geri döndü | Evet |

10.2 **Başlangıç durumu:** Sipariş oluşturulduğunda ödeme yöntemi `KAPIDA_ODEME` ise durum `ONAYLANDI`, diğer ödeme yöntemlerinde `ODEME_BEKLENIYOR` olur.

10.3 **Olaylar:** `ODEME_BASARILI`, `ODEME_BASARISIZ`, `ZAMAN_ASIMI` (sistem üretir; ödeme 30 dakika içinde alınmazsa), `IPTAL(aktor=MUSTERI|OPERATOR)`, `HAZIRLAMAYA_BASLA`, `KARGOYA_VER`, `TESLIM_BASARILI`, `TESLIM_BASARISIZ`, `YENIDEN_DAGITIM`, `IADE_TALEBI(gun=n)`, `IADE_ONAY`, `IADE_RED`.

`IADE_TALEBI` olayındaki `gun`, teslim tarihinden itibaren geçen takvim günü sayısıdır (teslim günü = 0. gün).

10.4 **Geçiş tablosu**

| # | Kaynak durum | Olay | Koşul | Hedef durum | Koşul sağlanmazsa |
|---|---|---|---|---|---|
| G1 | `ODEME_BEKLENIYOR` | `ODEME_BASARILI` | — | `ONAYLANDI` | — |
| G2 | `ODEME_BEKLENIYOR` | `ODEME_BASARISIZ` | — | `ODEME_BEKLENIYOR` (müşteri yeniden deneyebilir) | — |
| G3 | `ODEME_BEKLENIYOR` | `ZAMAN_ASIMI` | — | `IPTAL_EDILDI` | — |
| G4 | `ODEME_BEKLENIYOR` | `IPTAL` | aktor = `MUSTERI` veya `OPERATOR` | `IPTAL_EDILDI` | — |
| G5 | `ONAYLANDI` | `IPTAL` | aktor = `MUSTERI` veya `OPERATOR` | `IPTAL_EDILDI` | — |
| G6 | `ONAYLANDI` | `HAZIRLAMAYA_BASLA` | — | `HAZIRLANIYOR` | — |
| G7 | `HAZIRLANIYOR` | `IPTAL` | aktor = `OPERATOR` | `IPTAL_EDILDI` | aktor = `MUSTERI` ise `ERR_GECERSIZ_GECIS` |
| G8 | `HAZIRLANIYOR` | `KARGOYA_VER` | — | `KARGODA` | — |
| G9 | `KARGODA` | `TESLIM_BASARILI` | — | `TESLIM_EDILDI` | — |
| G10 | `KARGODA` | `TESLIM_BASARISIZ` | başarısız teslim denemesi sayısı (bu deneme dahil) < 3 | `TESLIM_EDILEMEDI` | sayı = 3 ise G11 uygulanır |
| G11 | `KARGODA` | `TESLIM_BASARISIZ` | başarısız teslim denemesi sayısı (bu deneme dahil) = 3 | `DEPOYA_DONDU` | — |
| G12 | `TESLIM_EDILEMEDI` | `YENIDEN_DAGITIM` | — | `KARGODA` | — |
| G13 | `TESLIM_EDILDI` | `IADE_TALEBI` | gun ≤ 14 ve siparişte daha önce reddedilmiş iade talebi yok | `IADE_TALEP_EDILDI` | gun > 14 ise `ERR_IADE_SURESI`; önceki talep reddedilmişse `ERR_IADE_TEKRAR` |
| G14 | `IADE_TALEP_EDILDI` | `IADE_ONAY` | — | `IADE_EDILDI` | — |
| G15 | `IADE_TALEP_EDILDI` | `IADE_RED` | — | `TESLIM_EDILDI` | — |

10.5 **Olay işleme kuralları** (sırasıyla uygulanır):

1. Olay adı 10.3'te tanımlı değilse `ERR_GECERSIZ_GIRDI`.
2. Olay, mevcut durum için 10.4'te hiç yer almıyorsa `ERR_GECERSIZ_GECIS`. Son durumlar (`IADE_EDILDI`, `IPTAL_EDILDI`, `DEPOYA_DONDU`) hiçbir olayı kabul etmez.
3. Olay parametreleri eksik veya geçersizse `ERR_GECERSIZ_GIRDI` (`aktor` yalnızca `MUSTERI` / `OPERATOR` olabilir; `gun` 0 veya pozitif tam sayı olmalıdır).
4. Koşul sağlanmıyorsa tablodaki "Koşul sağlanmazsa" sütunundaki hata döner. `IADE_TALEBI` için önce süre (`ERR_IADE_SURESI`), sonra tekrar (`ERR_IADE_TEKRAR`) kontrol edilir.
5. Hata dönen her durumda sipariş durumu ve sayaçlar değişmez.

10.6 Kargoya verilmiş bir sipariş iptal edilemez; müşteri teslimden sonra iade sürecini kullanır.

## 11. Uçtan uca (E2E) ödeme akışı konfigürasyonları

11.1 Ödeme ekranından sipariş onayına kadar olan akış aşağıdaki faktörlerin her değeriyle desteklenir:

| Faktör | Değerler |
|---|---|
| Platform | `WEB`, `IOS`, `ANDROID` |
| Ödeme yöntemi | `KREDI_KARTI`, `BANKA_KARTI`, `KAPIDA_ODEME`, `CEPPAY` |
| Teslimat tipi | `STANDART`, `HIZLI`, `MAGAZA` |
| Üyelik | `MISAFIR`, `KLASIK`, `ALTIN` |

11.2 **Kısıtlar** (ödeme ekranı bu kombinasyonları seçtirmez):
- **KS-1:** `KAPIDA_ODEME` yalnızca `STANDART` teslimatla seçilebilir (bkz. 7.1).
- **KS-2:** `CEPPAY` cüzdanı yalnızca `IOS` ve `ANDROID` uygulamalarında sunulur; `WEB`'de yoktur.
- **KS-3:** `CEPPAY` üyelik hesabına bağlıdır; `MISAFIR` kullanıcılar `CEPPAY` kullanamaz.

---

## Ek-A: Örnek hesaplamalar

Bu ek bilgilendirme amaçlıdır. Kurallarla çelişki olması halinde Bölüm 4–8'deki kurallar geçerlidir.

| # | Üyelik | AT | Kupon | Teslimat | Bölge | Ödeme | KI | NT | KU | HB | OT | Puan |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Örnek 1 | KLASIK | 500,00 | DEFNE10 | STANDART | NORMAL | KREDI_KARTI | 50,00 | 450,00 | 39,90 | 0,00 | 489,90 | 45 |
| Örnek 2 | MISAFIR | 1.800,00 | DEFNE10 | HIZLI | NORMAL | BANKA_KARTI | 150,00 | 1.650,00 | 40,00 | 0,00 | 1.690,00 | 0 |
| Örnek 3 | ALTIN | 900,00 | KITAP50 | STANDART | NORMAL | KREDI_KARTI | 50,00 | 850,00 | 0,00 | 0,00 | 850,00 | 127 |
| Örnek 4 | KLASIK | 900,00 | — | STANDART | UZAK | KREDI_KARTI | 0,00 | 900,00 | 0,00 | 0,00 | 900,00 | 90 |
| Örnek 5 | MISAFIR | 640,00 | — | MAGAZA | — | KREDI_KARTI | 0,00 | 640,00 | 0,00 | 0,00 | 640,00 | 0 |
