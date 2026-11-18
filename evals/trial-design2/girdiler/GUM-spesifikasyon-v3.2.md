# GÜM — Gönderi Ücretlendirme Motoru ve Gönderi Yaşam Döngüsü

## Fonksiyonel Spesifikasyon v3.2 (Onaylandı)

| Alan | Değer |
|---|---|
| Doküman no | PK-SPEC-131 |
| Şirket | Poyraz Kargo A.Ş. (poyrazkargo.example) |
| Sahibi | Gönderi Operasyonları Ekibi |
| Ürün sahibi | Nihan Karabulut |
| Geçerlilik | 2028 tarife ve dağıtım takvimi dönemi |
| Durum | Onaylandı — geliştirmeye hazır |

---

## 1. Amaç ve kapsam

Bu doküman, Poyraz Kargo'da gönderi kabulü sırasında çalışan **Gönderi Ücretlendirme Motoru'nun (GÜM)** ücret ve taahhüt edilen teslim tarihi hesaplama kurallarını, **gönderi yaşam döngüsünü** ve uçtan uca gönderi oluşturma akışının **desteklenen konfigürasyonlarını** tanımlar.

Kapsam dışı: yurt dışı gönderileri, çok parçalı gönderiler, alıcı ödemeli gönderide tahsilatın aktarımı, hasar ve kayıp tazmini, fatura oluşturma.

## 2. Tanımlar ve hesaplama esasları

| Kısaltma | Tanım |
|---|---|
| GA | **Gerçek ağırlık** (kg). Girdi olarak gelir. |
| HA | **Hacimsel ağırlık** (kg). Paket boyutlarından hesaplanır (bkz. 4.3). |
| UA | **Ücret ağırlığı** (kg). Tarifede kullanılan ağırlık (bkz. 4.4). |
| TB | **Taşıma bedeli** = tarife bedeli × hizmet katsayısı (bkz. Bölüm 5). |
| IT | **İndirim tutarı** (bkz. Bölüm 6). |
| NTB | **Net taşıma bedeli** = TB − IT |
| YE | **Yakıt ek ücreti** (bkz. 7.1) |
| SP | **Sigorta primi** (bkz. 7.2) |
| MA | **Matrah** = NTB + YE + SP |
| KDV | **Katma değer vergisi** (bkz. 7.3) |
| TU | **Toplam ücret** = MA + KDV |

2.1 Tüm tutarlar Türk lirası cinsindendir ve kuruş hassasiyetinde (2 ondalık) tutulur. Bu dokümanda sayılar Türkçe yazımla (ondalık virgül, binlik nokta) gösterilir; API alanlarında ondalık ayırıcı noktadır ve binlik ayırıcı kullanılmaz.

2.2 **Tutarların yuvarlanması:** Bir oran veya katsayıyla hesaplanan her tutar, hesaplandığı anda kuruşa "yarım yukarı" kuralıyla yuvarlanır (ör. 12,344 → 12,34; 12,345 → 12,35). Sonraki adımlar yuvarlanmış tutarı kullanır. Bir tutara uygulanan üst sınır (tavan) ve alt sınır (taban) kontrolleri yuvarlanmış tutar üzerinden yapılır.

2.3 **Ağırlıkların yuvarlanması:** HA önce 0,01 kg hassasiyetine "yarım yukarı" kuralıyla yuvarlanır. UA, GA ile yuvarlanmış HA'dan büyük olanın 0,5 kg'ın katına **yukarı** yuvarlanmasıyla bulunur; değer zaten 0,5'in katıysa değişmez (ör. 4,00 → 4,0; 4,01 → 4,5; 4,50 → 4,5).

2.4 **İş günü, kabul tarihi, işlem günü:** İş günü Bölüm 8.1'de tanımlanır. **Kabul tarihi**, `kabul_zamani` alanının tarih kısmıdır. **İşlem günü**, gönderinin taşıma sürecine alındığı iş günüdür: gönderi bir iş gününde kesim saatinden önce kabul edilmişse işlem günü kabul tarihidir; diğer durumlarda kabul tarihini izleyen ilk iş günüdür.

## 3. Girdi alanları

GÜM'ün ücretlendirme çağrısı (`POST /api/v3/gonderi/ucretle`) aşağıdaki alanları alır.

| Alan | Zorunlu | Geçerli değerler | Açıklama |
|---|---|---|---|
| `musteri_tipi` | Evet | `BIREYSEL`, `KURUMSAL` | |
| `agirlik_kg` | Evet | 0'dan büyük sayı, en fazla 2 ondalık basamak | Gerçek ağırlık (GA), kg. Ör. `4`, `4.5`, `4.25` |
| `en_cm`, `boy_cm`, `yukseklik_cm` | Evet | 1 veya daha büyük tam sayı (ondalıksız) | Paketin üç kenarı, cm |
| `bolge` | Evet | `SEHIRICI`, `YAKIN`, `UZAK` | Varış bölgesi |
| `hizmet` | Evet | `STANDART`, `EKSPRES`, `AYNI_GUN` | |
| `kampanya_kodu` | Hayır | boş (kod yok) veya bir kampanya kodu | Bkz. 6.2 |
| `beyan_degeri` | Hayır | boş (sigorta istenmiyor) veya 0'dan büyük, en fazla 2 ondalık basamaklı tutar (TL) | Bkz. 7.2 |
| `kabul_zamani` | Evet | `YYYY-AA-GG SS:DD` (24 saat düzeni, ör. `2028-03-06 09:05`); gerçek bir takvim tarihi ve saati; 2028-01-01 00:00 ile 2028-12-15 23:59 arasında (sınırlar dahil) | Gönderinin kabul edildiği an |

3.1 **Kodlar:** Bu dokümandaki bütün kod değerleri (müşteri tipi, bölge, hizmet, kampanya kodu, durum ve olay adları, parametre adları ve değerleri) büyük/küçük harf duyarlıdır ve yazıldığı gibi birebir eşleşmelidir; örneğin `bireysel` veya `Uzak` geçerli değer değildir.

3.2 **Sayı biçimi:** Sayısal alanlar yalnızca rakamlardan ve (ondalıklı alanlarda) en fazla bir noktadan oluşur; noktanın iki yanında da en az bir rakam bulunur. İşaret, boşluk, virgül, binlik ayırıcı ve üstel gösterim kabul edilmez. Baştaki sıfırlar değeri değiştirmez ve kabul edilir (`007.50` = 7,50).

3.3 **Girdi doğrulama:** Zorunlu bir alanın boş olması veya bir alanın yukarıdaki tablonun "Geçerli değerler" sütununa uymaması `ERR_GECERSIZ_GIRDI` ile sonuçlanır. Tek istisna `kampanya_kodu` alanıdır (bkz. 6.2). Bölüm 4–8'deki iş kuralı sınırları (ör. 30 kg, 100 cm, 50.000 TL) kendi hata kodlarıyla bildirilir.

## 4. Boyut ve ağırlık kuralları

4.1 **Boyut sınırı:** Paketin hiçbir kenarı 100 cm'yi, üç kenarının toplamı 150 cm'yi aşamaz. Aşılırsa `ERR_BOYUT` döner.

4.2 **Ağırlık sınırı:** GA 30 kg'ı aşamaz (30,00 kg kabul edilir). Aşılırsa `ERR_AGIRLIK` döner.

4.3 **Hacimsel ağırlık:** HA = en × boy × yükseklik / 3000 (boyutlar cm, sonuç kg). HA, 2.3'e göre 0,01 kg'a yuvarlanır.

4.4 **Ücret ağırlığı:** UA, GA ile HA'dan büyük olanın 2.3'e göre 0,5 kg'ın katına yukarı yuvarlanmış halidir.

4.5 **Ücret ağırlığı sınırı:** UA 40,0 kg'ı aşamaz (40,0 kg kabul edilir). Aşılırsa `ERR_HACIM` döner.

## 5. Taşıma bedeli

5.1 **Tarife** (TL, KDV hariç):

| Ücret ağırlığı (UA) | `SEHIRICI` | `YAKIN` | `UZAK` |
|---|---|---|---|
| 1,0 kg'a kadar (0,5 ve 1,0) | 60,00 | 75,00 | 95,00 |
| 1,5 – 5,0 kg | 85,00 | 105,00 | 135,00 |
| 5,5 – 10,0 kg | 120,00 | 150,00 | 195,00 |
| 10,0 kg'ı aşan her 0,5 kg için (10,0 kg bedeline eklenir) | 4,50 | 6,00 | 8,25 |

Örnek: `UZAK`, UA = 11,5 kg → 195,00 + 3 × 8,25 = 219,75 TL.

5.2 **Hizmet katsayısı:** `STANDART` 1,00; `EKSPRES` 1,35; `AYNI_GUN` 1,80. TB = tarife bedeli × hizmet katsayısı (2.2'ye göre yuvarlanır).

5.3 **Aynı gün hizmetinin bölgesi:** `AYNI_GUN` hizmeti yalnızca `SEHIRICI` bölgede verilir; diğer bölgelerde `ERR_HIZMET_BOLGE` döner.

## 6. İndirimler

6.1 **Sözleşme indirimi:** `KURUMSAL` müşterilerin gönderilerinde TB'nin %12'si kadar indirim yapılır.

6.2 **Kampanya indirimi:** Tanımlı tek kampanya kodu `BAHAR15`'tir: TB'nin %15'i kadar indirim, en fazla 40,00 TL. Tüm müşteri tiplerinde geçerlidir. Kod, **kabul tarihi** 2028-03-01 ile 2028-05-31 arasında (ilk ve son gün dahil) olan gönderilerde geçerlidir; işlem günü dikkate alınmaz. Bu dönemin dışında kabul edilen gönderide hata dönmez: kampanya indirimi uygulanmaz. `kampanya_kodu` alanında tanımlı olmayan bir kod gönderilirse `ERR_KAMPANYA_GECERSIZ` döner.

6.3 **Tek indirim:** Bir gönderiye sözleşme indirimi ile kampanya indirimi birlikte uygulanmaz. İkisi de uygulanabilir durumdaysa tutarı büyük olan (kampanya indiriminde tavan uygulandıktan sonraki tutar) uygulanır; tutarlar eşitse sözleşme indirimi uygulanır. IT, uygulanan indirimin tutarıdır; indirim yoksa IT = 0,00 TL'dir.

6.4 **Asgari net taşıma bedeli:** NTB 55,00 TL'nin altına düşemez. TB − IT < 55,00 TL ise IT, NTB = 55,00 TL olacak şekilde azaltılır (IT = TB − 55,00).

6.5 **Aynı gün hizmetinde indirim:** `AYNI_GUN` gönderilerine hiçbir indirim uygulanmaz (IT = 0,00 TL). Kampanya kodu yine de 6.2'ye göre doğrulanır.

## 7. Ek ücretler, sigorta ve toplam

7.1 **Yakıt ek ücreti:** YE = NTB × %6,5. Yakıt ek ücreti indirim uygulanmış bedel (NTB) üzerinden hesaplanır.

7.2 **Sigorta:** `beyan_degeri` gönderilmişse gönderi sigortalanır: SP = beyan değeri × %0,8 (binde 8), en az 15,00 TL. Beyan değeri 50.000,00 TL'yi aşamaz (50.000,00 TL kabul edilir); aşarsa `ERR_BEYAN_LIMIT` döner. `beyan_degeri` boşsa SP = 0,00 TL'dir. SP'ye indirim ve yakıt ek ücreti uygulanmaz.

7.3 **Matrah, KDV ve toplam:** MA = NTB + YE + SP. KDV = MA × %20. TU = MA + KDV.

## 8. Taahhüt edilen teslim tarihi

8.1 **İş günü:** Pazartesiden cumartesiye (cumartesi dahil) her gün iş günüdür. Pazar günleri ve Ek-B'de listelenen günler iş günü değildir.

8.2 **Kesim saati:** Kesim saati pazartesi–cuma günleri 17:00, cumartesi günleri 13:00'tür. Bir iş gününde kesim saatine kadar (kesim saati dahil) kabul edilen gönderi aynı gün işleme alınır. Kesim saatinden sonra veya iş günü olmayan bir günde kabul edilen gönderi, kabul tarihini izleyen ilk iş günü işleme alınır.

8.3 **Teslim süresi:** Teslim tarihi, işlem gününden sonraki N'inci iş günüdür (işlem günü sayılmaz). N değerleri:

| Hizmet | `SEHIRICI` | `YAKIN` | `UZAK` |
|---|---|---|---|
| `STANDART` | 2 | 3 | 5 |
| `EKSPRES` | 1 | 1 | 2 |

8.4 **UZAK bölgede cumartesi:** `UZAK` bölgede cumartesi günleri dağıtım yapılmaz. 8.3'e göre bulunan teslim tarihi cumartesiye denk gelirse teslim tarihi, o cumartesiyi izleyen ilk iş günü olur. İş günleri sayılırken cumartesi `UZAK` bölge için de iş günü olarak sayılır.

8.5 **Aynı gün hizmeti:** `AYNI_GUN` gönderisi bir iş gününde en geç 11:00'de (11:00 dahil) kabul edilmiş olmalıdır; aksi halde `ERR_AYNI_GUN_SAAT` döner. Teslim tarihi kabul tarihidir.

8.6 **Kabul saatleri:** Şube gişeleri pazartesi–cuma 08:30–19:00, cumartesi 09:00–15:00 arasında gönderi kabul eder; çevrimiçi kanallar ve kargo otomatları her gün 24 saat kabul yapar. GÜM kabul saatlerini denetlemez; `kabul_zamani` hangi gün ve saatte olursa olsun ücretlendirme yapılır.

## 9. Yanıt yapısı ve hata öncelik sırası

9.1 Başarılı yanıt: `sonuc = KABUL`, `ucret_agirligi`, `tasima_bedeli`, `indirim`, `yakit_ek_ucreti`, `sigorta_primi`, `kdv`, `toplam`, `teslim_tarihi`.

9.2 Hata yanıtında `sonuc` alanında yalnızca hata kodu döner; diğer alanlar dönmez.

9.3 Birden fazla hata koşulu aynı anda oluşursa aşağıdaki listede **önce gelen** hata döner:

1. `ERR_GECERSIZ_GIRDI`
2. `ERR_BOYUT`
3. `ERR_AGIRLIK`
4. `ERR_HACIM`
5. `ERR_HIZMET_BOLGE`
6. `ERR_AYNI_GUN_SAAT`
7. `ERR_KAMPANYA_GECERSIZ`

## 10. Gönderi yaşam döngüsü

10.1 **Durumlar**

| Durum | Açıklama | Son durum mu? |
|---|---|---|
| `KABUL_EDILDI` | Gönderi kabul edildi, şubede | Hayır |
| `TRANSFERDE` | Aktarma merkezleri arasında taşınıyor | Hayır |
| `DAGITIMDA` | Kurye dağıtıma çıkardı | Hayır |
| `TESLIM_EDILEMEDI` | Teslim denemesi başarısız, yeni karar bekleniyor | Hayır |
| `SUBEDE_BEKLIYOR` | Alıcının şubeden teslim alması bekleniyor | Hayır |
| `TESLIM_EDILDI` | Alıcıya teslim edildi | Evet |
| `IADE_YOLUNDA` | Göndericiye geri gönderiliyor | Hayır |
| `IADE_EDILDI` | Göndericiye geri teslim edildi | Evet |
| `IPTAL_EDILDI` | Gönderi şubeden çıkmadan iptal edildi | Evet |

10.2 **Başlangıç ve sayaçlar:** Gönderi oluşturulduğunda durumu `KABUL_EDILDI`'dir ve iki sayacı sıfırdır:

- `deneme_sayisi`: kabul edilmiş ve `neden` = `ADRESTE_YOK` olan `TESLIM_BASARISIZ` olaylarının sayısı. `neden` = `RED` olan denemeler sayılmaz.
- `adres_degisikligi_sayisi`: kabul edilmiş `ADRES_DEGISTIR` olaylarının sayısı (hangi durumda yapıldığına bakılmaz).

10.3 **Olaylar**

| Olay | Parametre | Açıklama |
|---|---|---|
| `TRANSFERE_VER` | — | Şube gönderiyi aktarmaya verir |
| `DAGITIMA_CIKAR` | — | Varış şubesi gönderiyi kuryeye verir |
| `TESLIM_BASARILI` | — | Kurye gönderiyi alıcıya teslim eder |
| `TESLIM_BASARISIZ` | `neden` = `ADRESTE_YOK` \| `RED` | Alıcı adreste yok ya da gönderiyi kabul etmiyor |
| `YENIDEN_DAGIT` | — | Gönderi yeniden dağıtıma çıkarılır |
| `SUBEYE_YONLENDIR` | — | Alıcı gönderiyi şubeden almak ister |
| `ADRES_DEGISTIR` | — | Teslimat adresi değiştirilir |
| `SUBEDEN_TESLIM` | `gun` = n | Alıcı gönderiyi şubeden teslim alır |
| `SURE_DOLDU` | `gun` = n | Sistem üretir: şubede bekleme süresi doldu |
| `IPTAL` | `aktor` = `GONDERICI` \| `OPERATOR` | İptal talebi |
| `IADE_TESLIM` | — | İade gönderi göndericiye teslim edilir |

`gun`, gönderinin `SUBEDE_BEKLIYOR` durumuna son girdiği günden itibaren geçen gün sayısıdır (giriş günü = 0).

10.4 **Geçiş tablosu**

| # | Kaynak durum | Olay | Koşul | Hedef durum | Koşul sağlanmazsa |
|---|---|---|---|---|---|
| G1 | `KABUL_EDILDI` | `TRANSFERE_VER` | — | `TRANSFERDE` | — |
| G2 | `KABUL_EDILDI` | `IPTAL` | aktor = `GONDERICI` veya `OPERATOR` | `IPTAL_EDILDI` | — |
| G3 | `TRANSFERDE` | `DAGITIMA_CIKAR` | — | `DAGITIMDA` | — |
| G4 | `TRANSFERDE` | `IPTAL` | aktor = `OPERATOR` | `IADE_YOLUNDA` | aktor = `GONDERICI` ise `ERR_YETKI` |
| G5 | `TRANSFERDE` | `ADRES_DEGISTIR` | `adres_degisikligi_sayisi` = 0 | `TRANSFERDE` | `ERR_ADRES_LIMIT` |
| G6 | `DAGITIMDA` | `TESLIM_BASARILI` | — | `TESLIM_EDILDI` | — |
| G7 | `DAGITIMDA` | `TESLIM_BASARISIZ` | neden = `ADRESTE_YOK` ve bu deneme sayıldıktan sonra `deneme_sayisi` < 3 | `TESLIM_EDILEMEDI` | — |
| G8 | `DAGITIMDA` | `TESLIM_BASARISIZ` | neden = `ADRESTE_YOK` ve bu deneme sayıldıktan sonra `deneme_sayisi` = 3 | `SUBEDE_BEKLIYOR` | — |
| G9 | `DAGITIMDA` | `TESLIM_BASARISIZ` | neden = `RED` | `IADE_YOLUNDA` | — |
| G10 | `TESLIM_EDILEMEDI` | `YENIDEN_DAGIT` | `deneme_sayisi` < 3 | `DAGITIMDA` | — |
| G11 | `TESLIM_EDILEMEDI` | `YENIDEN_DAGIT` | `deneme_sayisi` = 3 | `IADE_YOLUNDA` | — |
| G12 | `TESLIM_EDILEMEDI` | `SUBEYE_YONLENDIR` | — | `SUBEDE_BEKLIYOR` | — |
| G13 | `TESLIM_EDILEMEDI` | `ADRES_DEGISTIR` | `adres_degisikligi_sayisi` = 0 | `TESLIM_EDILEMEDI` | `ERR_ADRES_LIMIT` |
| G14 | `SUBEDE_BEKLIYOR` | `SUBEDEN_TESLIM` | gun ≤ 5 | `TESLIM_EDILDI` | gun > 5 ise `ERR_BEKLEME_SURESI` |
| G15 | `SUBEDE_BEKLIYOR` | `SURE_DOLDU` | gun > 5 | `IADE_YOLUNDA` | gun ≤ 5 ise `ERR_SURE_DOLMADI` |
| G16 | `SUBEDE_BEKLIYOR` | `YENIDEN_DAGIT` | `deneme_sayisi` < 3 | `DAGITIMDA` | `deneme_sayisi` = 3 ise `ERR_DENEME_LIMITI` |
| G17 | `IADE_YOLUNDA` | `IADE_TESLIM` | — | `IADE_EDILDI` | — |

10.5 **Olay işleme kuralları** (sırasıyla uygulanır):

1. Olay adı 10.3'te tanımlı değilse `ERR_GECERSIZ_GIRDI`.
2. Olay, mevcut durum için 10.4'te hiç yer almıyorsa `ERR_GECERSIZ_GECIS`. Son durumlar hiçbir olayı kabul etmez.
3. Olayın parametreleri eksik, fazla veya geçersizse `ERR_GECERSIZ_GIRDI` (`neden` yalnızca `ADRESTE_YOK` / `RED`, `aktor` yalnızca `GONDERICI` / `OPERATOR` olabilir; `gun` 0 veya pozitif tam sayı olmalıdır).
4. Koşul sağlanmıyorsa tablodaki "Koşul sağlanmazsa" sütunundaki hata döner.
5. Hata dönen her durumda gönderinin durumu ve sayaçları değişmez.

10.6 **Şubede bekleme:** Gönderi şubede en fazla 5 gün bekletilir. Alıcı gönderiyi `gun` ≤ 5 iken teslim alabilir (G14). Süre dolduğunda (`gun` > 5) sistem `SURE_DOLDU` olayını üretir ve gönderi iadeye çevrilir (G15).

10.7 **İptal:** Aktarmaya verilmiş bir gönderi `IPTAL_EDILDI` durumuna alınmaz; operatörün iptali gönderiyi iadeye çevirir (G4). Dağıtıma çıkmış gönderi için iptal talebi kabul edilmez.

10.8 **Olay yanıtı:** Her olayın yanıtında `sonuc` (`KABUL` veya hata kodu), gönderinin `durum` değeri ve `deneme_sayisi` döner.

## 11. Uçtan uca (E2E) gönderi oluşturma konfigürasyonları

11.1 Gönderi oluşturma akışı aşağıdaki faktörlerin her değeriyle desteklenir:

| Faktör | Değerler |
|---|---|
| `kanal` | `WEB`, `MOBIL`, `GISE` (şube gişesi), `CAGRI` (çağrı merkezi, kurye adresten alır), `API` |
| `musteri_tipi` | `BIREYSEL`, `KURUMSAL` |
| `hizmet` | `STANDART`, `EKSPRES`, `AYNI_GUN` |
| `bolge` | `SEHIRICI`, `YAKIN`, `UZAK` |
| `odeme` | `GONDERICI_NAKIT`, `GONDERICI_KART`, `ALICI_ODEMELI`, `CARI_HESAP` |
| `teslim_noktasi` | `ADRES`, `SUBE`, `OTOMAT` |

11.2 **Kısıtlar** (bu kombinasyonlar seçilemez; GÜM yalnızca KS-1'i kendisi de denetler):

- **KS-1:** `AYNI_GUN` hizmeti yalnızca `SEHIRICI` bölgede seçilebilir (bkz. 5.3).
- **KS-2:** `CARI_HESAP` yalnızca `KURUMSAL` müşterilere sunulur.
- **KS-3:** `API` kanalını yalnızca `KURUMSAL` müşteriler kullanır.
- **KS-4:** `ALICI_ODEMELI` yalnızca `BIREYSEL` müşterilere sunulur.
- **KS-5:** `OTOMAT` teslim noktasında `ALICI_ODEMELI` seçilemez (otomat tahsilat yapamaz).
- **KS-6:** `AYNI_GUN` hizmetinde teslim noktası yalnızca `ADRES` olabilir.
- **KS-7:** `GONDERICI_NAKIT` yalnızca `GISE` ve `CAGRI` kanallarında seçilebilir.

---

## Ek-A: Örnek hesaplamalar

Bu ek bilgilendirme amaçlıdır. Kurallarla çelişki olması halinde Bölüm 2–9'daki kurallar geçerlidir.

| # | Müşteri | GA | En × Boy × Yük. | Bölge | Hizmet | Kod | Beyan | Kabul zamanı | UA | TB | IT | YE | SP | KDV | TU | Teslim tarihi |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A-1 | BIREYSEL | 2,00 | 20 × 20 × 10 | YAKIN | STANDART | — | — | 2028-03-06 10:15 | 2,0 | 105,00 | 0,00 | 6,83 | 0,00 | 22,37 | 134,20 | 2028-03-09 |
| A-2 | BIREYSEL | 3,20 | 40 × 30 × 25 | UZAK | STANDART | — | — | 2028-06-12 09:30 | 10,0 | 195,00 | 0,00 | 12,68 | 0,00 | 41,54 | 249,22 | 2028-06-19 |
| A-3 | KURUMSAL | 4,80 | 10 × 19 × 79 | SEHIRICI | EKSPRES | — | 1.200,00 | 2028-02-25 16:10 | 5,0 | 114,75 | 13,77 | 6,56 | 15,00 | 24,51 | 147,05 | 2028-02-26 |
| A-4 | KURUMSAL | 12,00 | 30 × 30 × 30 | YAKIN | STANDART | — | — | 2028-04-11 11:20 | 12,0 | 174,00 | 20,88 | 11,31 | 0,00 | 32,89 | 197,32 | 2028-04-14 |
| A-5 | BIREYSEL | 6,40 | 30 × 20 × 20 | YAKIN | EKSPRES | BAHAR15 | — | 2028-05-31 17:45 | 6,5 | 202,50 | 30,38 | 11,19 | 0,00 | 36,66 | 219,97 | 2028-06-02 |
| A-6 | KURUMSAL | 11,00 | 30 × 30 × 20 | UZAK | EKSPRES | BAHAR15 | 20.000,00 | 2028-04-08 12:40 | 11,0 | 285,53 | 40,00 | 15,96 | 160,00 | 84,30 | 505,79 | 2028-04-11 |
| A-7 | KURUMSAL | 0,80 | 20 × 15 × 5 | SEHIRICI | AYNI_GUN | — | — | 2028-09-14 10:05 | 1,0 | 108,00 | 0,00 | 7,02 | 0,00 | 23,00 | 138,02 | 2028-09-14 |

## Ek-B: 2028 dağıtım takvimi (iş günü olmayan günler)

Pazar günlerine ek olarak aşağıdaki günler iş günü değildir:

| # | Tarih | Gün | Açıklama |
|---|---|---|---|
| B-1 | 2028-01-01 | Cumartesi | Yılbaşı |
| B-2 | 2028-04-23 | Pazar | Ulusal Egemenlik ve Çocuk Bayramı |
| B-3 | 2028-05-01 | Pazartesi | Emek ve Dayanışma Günü |
| B-4 | 2028-05-19 | Cuma | Atatürk'ü Anma, Gençlik ve Spor Bayramı |
| B-5 | 2028-07-15 | Cumartesi | Demokrasi ve Millî Birlik Günü |
| B-6 | 2028-08-30 | Çarşamba | Zafer Bayramı |
| B-7 | 2028-10-29 | Pazar | Cumhuriyet Bayramı |

Notlar:

- Bu takvim şirketin dağıtım takvimidir ve bu spesifikasyonun tek kaynağıdır: listede olmayan bir gün, başka bir takvimde tatil görünse bile, pazar değilse iş günüdür.
- Pazara denk gelen tatil başka bir güne devretmez. Yarım gün (arife) uygulaması yoktur.
- 2028 artık yıldır: şubat 29 gündür. 1 Ocak 2028 cumartesi, 29 Şubat 2028 salı günüdür.
