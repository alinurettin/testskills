# SFM v1.4 Test Tasarım Dokümanı

| Alan | Değer |
|---|---|
| Proje / Ürün | Defne Kitap – Sipariş Fiyatlandırma Motoru (SFM) ve Sipariş Durum Yönetimi |
| Referans Spesifikasyon | `girdiler/SFM-spesifikasyon-v1.4.md` (Doküman No: DK-SPEC-214, Onay: 22.09.2026) |
| Hazırlayan | Kıdemli Test Analisti |
| Tarih | 2026-11-16 |
| Kapsamdaki Gereksinimler | 16 atomik gereksinim (`REQ-001` .. `REQ-016`) — %100 kapsandı |
| Toplam Test Vakası | **140** CSV / tasarım test vakası (`71` fiyatlandırma, `52` durum geçişi, `14` E2E konfigürasyon, `3` E2E UI kısıt kontrolü) |

---

## 1. Yönetici Özeti ve Kalite Metrikleri

Bu doküman, geliştirme öncesinde SFM v1.4 spesifikasyonunun kuruşu kuruşuna doğrulanabilir test verisiyle test tasarımını, teknik gerekçelerini, beklenen sonuç modellerini ve spesifikasyonda tespit edilen çelişki/belirsizlikleri sunar.

- **Gereksinim Kapsamı:** `16 / 16 (%100,0)` gereksinim en az bir aktif testle kapsanmıştır. Fonksiyonel ve iş kuralı gereksinimlerinin tamamı (`15 / 15`) hem pozitif hem negatif testlere sahiptir (`REQ-016` kısıt gereksinimi için de 3 negatif UI kontrolü eklenmiştir).
- **Öncelik Dağılımı:** `critical: 14 (%10)`, `high: 48 (%34)`, `medium: 64 (%46)`, `low: 14 (%10)` — öncelik şişmesi (`PRIORITY_SKEW`) yoktur.
- **Test Dağılımı:**
  - `cikti/fiyat-test-verisi.csv`: **71** fiyatlandırma testi (`TC-001` .. `TC-071`)
  - `cikti/durum-gecis-testleri.csv`: **52** durum geçiş testi (`TC-072` .. `TC-123`)
  - `cikti/konfigurasyon-matrisi.csv`: **14** E2E ödeme konfigürasyonu (`TC-124` .. `TC-137`)
  - Doküman içi UI Kısıt Testleri: **3** negatif ekran kısıtı testi (`TC-138` .. `TC-140`, `KS-1`..`KS-3`)
- **En Kritik Tespit:** Spesifikasyonun **Ek-A Örnek 4** satırı (`KLASIK`, `AT=900,00`, `STANDART`, `UZAK`) için `KU = 0,00 TL` ve `OT = 900,00 TL` yazmaktadır; ancak **Bölüm 6.2 ve 6.5** uyarınca ücretsiz standart teslimat `25,00 TL` uzak bölge ek ücretini kapsamaz (yalnızca `ALTIN` üyelik kapsar). Kurallar esas alındığından doğru beklenen sonuç **`KU = 25.00`, `OT = 925.00`** olarak modellenmiştir (`Q-005`, `TC-025`).
- **Bağımsız Doğrulama:** Tüm 3 CSV dosyasındaki her satır, spesifikasyon kurallarını (`Decimal` `ROUND_HALF_UP`, puan `floor`, 9.3 hata öncelik sırası, 10.5 olay işleme sırası, 11.2 ikili kapsama kısıtları) uygulayan bağımsız referans doğrulayıcı ile kontrol edilmiş ve **0 uyuşmazlık** elde edilmiştir. Test yazım kalitesi incelemesi (`review_tests.py`) **100,0 / 100** puan vermiştir.

---

## 2. Gereksinim Risk Profili ve Kullanılan Test Tasarım Teknikleri

### 2.1 Gereksinim Risk Özeti (`REQ-001` .. `REQ-016`)

Gereksinimler Olasılık × Etki (`1–5 × 1–5`) ölçeğiyle puanlanmıştır; test derinliği risk seviyesine göre ayarlanmıştır:

| ID | Kaynak | Başlık | Risk (O×E) | Seviye | Birincil Teknikler | Testler |
|---|---|---|---|---|---|---|
| REQ-001 | Böl. 2, 2.1–2.2 | Hesaplama formülleri ve yarım yukarı yuvarlama | 4×4 (16) | High | BVA (3-değerli), EP, EG | `TC-001, 009–013, 048–049` |
| REQ-002 | Böl. 3, 3.1–3.2 | SFM girdi alanları ve biçim doğrulaması | 4×4 (16) | High | EP, BVA, EG | `TC-031, 033, 044–056` |
| REQ-003 | Böl. 3.3 | Ödeme yöntemlerinin SFM kapsam sınırı | 3×3 (9) | Medium | EP, DT | `TC-002, 011, 026, 140` |
| REQ-004 | Böl. 4.1–4.3 | Sepet alt ve üst limit kontrolü (`AT`) | 3×4 (12) | High | BVA (3-değerli), DT, EG | `TC-001–008, 069, 071` |
| REQ-005 | Böl. 5.1–5.2 | Kupon kodu formatı, kırpma ve harf duyarlılığı | 3×3 (9) | Medium | EP | `TC-014, 019, 020` |
| REQ-006 | Böl. 5.3–5.5 | `DEFNE10` ve `KITAP50` indirim kuralları | 4×5 (20) | **Critical** | DT (tam), BVA (3-değerli), EG | `TC-005, 007, 009–018, 021, 041, 066–068, 070–071` |
| REQ-007 | Böl. 6.1–6.3, 6.5–6.6 | `STANDART`/`MAGAZA` kargo, `UZAK` ve `ALTIN` | 4×5 (20) | **Critical** | DT, BVA (3-değerli), EP | `TC-001, 021–027, 031–032, 035–036, 039, 043, 054, 064–065` |
| REQ-008 | Böl. 6.4 | `HIZLI` teslimat ücreti ve `UZAK` kısıtı | 3×4 (12) | High | DT, BVA | `TC-028, 029, 030` |
| REQ-009 | Böl. 7.1–7.3 | `KAPIDA_ODEME` uygunluk, HB ve 5000 TL limiti | 4×4 (16) | High | DT, BVA, EG | `TC-034–043, 064–065, 138` |
| REQ-010 | Böl. 2.3, 8.1–8.4 | Sadakat puanı hesaplama ve kesir aşağı yuvarlama | 3×3 (9) | Medium | BVA, DT | `TC-001–003, 013, 017, 027, 034, 038, 068` |
| REQ-011 | Böl. 9.1–9.3 | Yanıt yapısı ve 7'li hata öncelik sırası | 3×4 (12) | High | DT, EP | `TC-055, 057–063, 069–070` |
| REQ-012 | Böl. 10.1–10.4 (G1–G8), 10.6 | Başlangıç durumu, ödeme, hazırlık, iptal geçişleri | 4×5 (20) | **Critical** | ST (0/1-switch + geçersiz) | `TC-072–088, 095, 101, 104, 107–108` |
| REQ-013 | Böl. 10.4 (G9–G12) | Kargo teslim deneme sayacı (`<3` / `=3`) ve yeniden dağıtım | 3×4 (12) | High | ST (1-switch), BVA | `TC-089–094, 109, 114` |
| REQ-014 | Böl. 10.3, 10.4 (G13–G15) | İade talebi, 14 gün süre ve tekrar reddi | 3×4 (12) | High | ST, BVA, DT | `TC-095–100, 111–112, 115, 121` |
| REQ-015 | Böl. 10.1, 10.5 | Olay işleme sırası (1–5), parametre ve atomiklik | 4×4 (16) | High | ST (geçersiz), DT, EP, BVA | `TC-087, 100–123` |
| REQ-016 | Böl. 11.1–11.2 | E2E ödeme konfigürasyonları ve `KS-1..KS-3` | 3×4 (12) | High | Pairwise (`t=2`), DT | `TC-124–140` |

### 2.2 Teknik Seçimi ve Gerekçeleri

1. **Denklik Paylarına Ayırma (EP) ve Sınır Değer Analizi (BVA — `DS-001`):**
   - Sayısal eşiklerin tamamı (`150.00`, `400.00`, `750.00`, `1499.95`, `5000.00`, `20000.00`, `gun=0..14`, `deneme=1..3`) kuruş/tam sayı hassasiyetinde `<=` / `<` kayması (off-by-one) riskine açıktır. Kritik finansal eşiklerde (`150.00`, `400.00`, `750.00`, `1499.95` yuvarlama+tavan, `20000.00`) 3-değerli / çapraz sınır analizi, ikincil sınırlarda (`gun=0,14,15`, `OT=5000.00`) 2-değerli sınır analizi uygulanmıştır.
   - Her geçersiz denklik sınıfı (eksik alan, tanımsız enum, hatalı sayı formatı) **tek hata ilkesiyle** (single-fault) ayrı test vakasında doğrulanmıştır; böylece Öncelik-1 hataların birbirini maskelemesi önlenmiştir.
2. **Karar Tablosu Testi (`DS-002` ve `DS-003`):**
   - Kupon kuralları (`kupon × uyelik × AT`) ile kargo/kapıda ödeme kuralları (`uyelik × NT × teslimat_tipi × bolge × odeme_yontemi × OT`) çok koşullu iş kuralları içerir. İki bağımsız karar tablosu oluşturularak olası tüm kombinasyonlar (`60 + 96 = 156`) script ile genişletilmiş; **0 boşluk ve 0 çelişki** matematiksel olarak doğrulanmış, sadeleştirilmiş kolonların tamamı (`20/20` ve `19/19` = **%100**) testlerle kapsanmıştır.
   - Hata öncelik sırası (Bölüm 9.3) için her komşu öncelik çifti (`1>2`, `2>3`, `2>4`, `3>5`, `4>5`, `5>6`, `6>7`) özel karar testiyle kapsanmıştır (`TC-057..TC-063`).
3. **Durum Geçiş Testi (`DS-004`):**
   - 10 durum, 12 olay ve 15 geçişten oluşan sipariş yaşam döngüsü için durum×olay matrisi çıkarılmıştır (`120` hücre: `15` geçerli geçiş + `106` geçersiz hücre; `KARGODA`+`TESLIM_BASARISIZ` guard dallanması nedeniyle 2 geçiş içerir).
   - Kritik ödeme/iptal/teslim/iade akışları için yalnızca 0-switch (her geçiş en az 1 kez) değil, başlangıç durumuna (`ODEME_BEKLENIYOR` ve `KAPIDA_ODEME` → `ONAYLANDI`) ve geçiş zincirlerine göre **1-switch kapsamı** (ardışık geçerli geçiş çiftleri) uygulanmıştır.
   - 106 geçersiz hücrenin tamamını şişkin biçimde kopyalamak yerine, her ara durumdan ve 3 son durumdan (`IPTAL_EDILDI`, `DEPOYA_DONDU`, `IADE_EDILDI`) riskli geçersiz geçişler ve 10.5'teki 5 adımlı olay işleme sırası seçilmiştir.
4. **Çiftli (Pairwise, `t=2`) Kombinatoryal Test (`DS-005`):**
   - E2E ödeme regresyonunda her kombinasyon ~15 dakika manuel efor gerektirir. Tüm kartezyen uzay (`108`), kısıtlar sonrası geçerli uzay (`75` kombinasyon = 18,75 saat) ve `t=3` (`39` test = 9,75 saat) yerine kısıtlı `t=2` pairwise üretimiyle **14 test (~3,5 saat)** elde edilmiştir; tüm geçerli ikili etkileşimlerin **%100'ü (59/59)** kapsam altına alınmıştır.
5. **Hata Tahmini (Error Guessing) ve Çok Değişkenli Alan Sınırları:**
   - `AT` vs `NT` vs `OT` taban karışıklığını yakalamak için `AT=150.00+DEFNE10` (`NT=135.00`), `AT=799.99+KITAP50` (`NT=749.99`), `AT=4962.11+UZAK+KAPIDA_ODEME` (`AT<5000` ama `OT=5000.01`), `AT=5137.10+DEFNE10+KAPIDA_ODEME` (`AT>5000` ama `OT=5000.00`) ve `ALTIN` puanında `NT=158.00` (`floor(15*1.5)=22` vs yanlış `floor(15.8*1.5)=23`) kurgulanmıştır.
   - Türkiye yerel biçim hataları (`150,00` virgül, `1.500.00` binlik nokta, `defne10` küçük harf, `" DEFNE10 "` boşluk) ve `MAGAZA` + tanımsız `bolge` davranışı ayrıca test edilmiştir.

---

## 3. Denklik Sınıfları ve Sınır Değerleri (`DS-001`)

### 3.1 Sayısal ve Metin Parametrelerinin Denklik Sınıfları ve BVA Değerleri

| Parametre | Denklik Sınıfları | Sınır Değerleri (BVA) | Beklenen Davranış | Testler |
|---|---|---|---|---|
| `ara_toplam` (Sepet & Kupon & Format) | **Geçersiz Biçim/Aralık:** `<=0` (`0.00`, `-10.00`), `>2 ondalık` (`150.123`), virgül (`150,00`), binlik (`1.500.00`), metin (`abc`), boş (`""`)<br>**Geçerli Sayı ama Sepet Altı:** `0.01 .. 149.99`<br>**Temel Geçerli:** `150.00 .. 399.99`<br>**`KITAP50` Uygun:** `400.00 .. 1499.94`<br>**`DEFNE10` Tavan:** `1499.95 .. 20000.00`<br>**Sepet Üstü:** `20000.01 .. ∞` | `0.00` (OFF, `ERR_GECERSIZ_GIRDI`)<br>`0.01` (ON, `ERR_MIN_SEPET`)<br>`149.99` (ON, `ERR_MIN_SEPET`)<br>`150.00` (ON, `KABUL`), `150.01` (IN)<br>`399.99` (ON, `KITAP50` yok)<br>`400.00` (ON, `KITAP50` var), `400.01` (IN)<br>`1499.94` (ON, `KI=149.99`)<br>`1499.95` (ON, `KI=150.00`), `1500.05` (tavan aşımı)<br>`19999.99` (IN), `20000.00` (ON, `KABUL`)<br>`20000.01` (OFF, `ERR_MAX_SEPET`) | `<=0` / biçim hatası → `ERR_GECERSIZ_GIRDI`;<br>`0.01..149.99` → `ERR_MIN_SEPET`;<br>`150.00..20000.00` → `KABUL`;<br>`>20000.00` → `ERR_MAX_SEPET` | `TC-001`..`TC-017`, `TC-046`..`TC-052` |
| `DEFNE10` Yuvarlama | Yarım-yukarı 3. ondalık `<5` (`150.04*0.1=15.004`) vs `>=5` (`150.05*0.1=15.005`, `1499.95*0.1=149.995`) | `150.04` (`15.00`), `150.05` (`15.01`), `1499.94` (`149.99`), `1499.95` (`150.00`), `1500.05` (`150.01→150.00`) | Yuvarlama anında yarım-yukarı, tavan yuvarlanmış tutara | `TC-009`..`TC-013` |
| `NT` (Ücretsiz Kargo & `HIZLI` İndirimi) | `135.00 .. 749.99` (ücretli `STANDART` / `HIZLI=79.90`)<br>`750.00 .. 20000.00` (ücretsiz `STANDART` taban / `HIZLI=40.00`) | `749.99` (`AT=799.99+KITAP50`, `HIZLI AT=749.99`)<br>`750.00` (`AT=800.00+KITAP50`, `HIZLI AT=750.00`)<br>`750.01` (`STANDART`) | Kupon sonrası `NT >= 750.00` ise `STANDART` taban=0, `HIZLI`=40.00 | `TC-021`..`TC-023`, `TC-028`, `TC-029` |
| `OT` (`KAPIDA_ODEME` Limiti) | `<= 5000.00` (`KABUL`)<br>`> 5000.00` (`ERR_KAPIDA_LIMIT`) | `5000.00` (`AT=4987.10` `NORMAL`, `AT=4962.10` `UZAK`, `AT=5137.10+DEFNE10`)<br>`5000.01` (`AT=4987.11` `NORMAL`, `AT=4962.11` `UZAK`) | `OT = NT + KU + HB <= 5000.00` kabul, `>5000.00` ret | `TC-037`..`TC-041` |
| `Puan` (`floor(NT/10)`) | `MISAFIR`: `0`; `KLASIK`: `taban`; `ALTIN` (çift/tek `taban` × `1.5` aşağı yuvarlama) | `NT=158.00` (`taban=15`, `ALTIN=22`), `NT=749.99` (`74`), `NT=750.00` (`75`), `NT=350.01` (`ALTIN=52`) | Kesirler aşağı yuvarlanır; `KU`/`HB` dahil edilmez | `TC-001`..`002`, `017`, `021`..`022`, `027`, `034` |
| `iade_gun` | Geçersiz (`<0`, `1.5`, boş), Geçerli (`0..14`), Süre aşımı (`>=15`) | `-1` (OFF, `ERR_GECERSIZ_GIRDI`), `0` (ON, `KABUL`), `14` (ON, `KABUL`), `15` (OFF, `ERR_IADE_SURESI`) | `0..14` kabul; `>14` süre aşımı; `<0` veya kesir girdi hatası | `TC-095`..`097`, `TC-121`..`123` |

### 3.2 Kategorik (Enum) Denklik Sınıfları

| Alan | Geçerli Sınıflar | Geçersiz Sınıflar (Single-Fault Testleri) |
|---|---|---|
| `uyelik` | `MISAFIR` (`TC-002`), `KLASIK` (`TC-001`), `ALTIN` (`TC-013`) | `PLATIN` (`TC-044`), boş `""` (`TC-045`) → `ERR_GECERSIZ_GIRDI` |
| `kupon` | `""` (`TC-001`), `DEFNE10` (`TC-005`), `" DEFNE10 "` kırpma (`TC-014`), `KITAP50` (`TC-016`) | `defne10` küçük harf (`TC-019`), `YOK99` tanımsız (`TC-020`) → `ERR_KUPON_GECERSIZ` |
| `teslimat_tipi` | `STANDART` (`TC-001`), `HIZLI` (`TC-029`), `MAGAZA` (`TC-031`) | `VIP` (`TC-053`) → `ERR_GECERSIZ_GIRDI` |
| `bolge` | `NORMAL` (`TC-001`), `UZAK` (`TC-024`), `MAGAZA` iken boş/tanımsız (`TC-031`, `TC-033`) | `STANDART` iken boş (`TC-054`), `HIZLI` iken `ADALAR` (`TC-055`) → `ERR_GECERSIZ_GIRDI` |
| `odeme_yontemi` | `KREDI_KARTI` (`TC-001`), `BANKA_KARTI` (`TC-002`), `CEPPAY` (`TC-011`), `KAPIDA_ODEME` (`TC-034`) | `HAVALE` (`TC-056`) → `ERR_GECERSIZ_GIRDI` |

> **DS-001 Kapsam Notu:** `ep_bva.py` script'i `DS-001`'de `54` öğe üretmiştir; `37`'si doğrudan işaretlenmiştir. Kalan `17` öğe (`C-01/03/11/15` ara/komşu tekrarları, `C-21/22/31..34` alt-parametrelerin tekrarlanan `<150`/`>20000` uyarıları, `C-35/36/38` `odenecek_kapida_limit` alt teorik sınırı `162.90`, `C-44/48/49/50` diğer alanlardaki aynı boş/negatif girdi payları) kapsanmış denklik sınıfları ve daha sıkı sınır testleriyle (`TC-001..008`, `TC-045..058`, `TC-097`, `TC-121`) temsil edildiği için kasıtlı olarak ayrı satır açılmamıştır.

---

## 4. Karar Tabloları (`DS-002`, `DS-003`) ve Hata Öncelik Sırası

### 4.1 Kupon Uygunluğu ve Sepet Limiti Karar Tablosu (`DS-002`)

60 olası kombinasyonun tamamı (`first_match: true` önceliğiyle) **0 boşluk, 0 çelişki** ile 20 sadeleştirilmiş kolona indirgenmiş ve **20/20 (%100)** testle kapsanmıştır:

| Kolon | D01 | D02 | D03 | D04 | D05 | D06 | D07 | D08 | D09 | D10 | D11 | D12 | D13 | D14 | D15 | D16 | D17 | D18 | D19 | D20 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **kupon** | YOK | YOK | YOK | YOK | YOK | DEFNE10 | DEFNE10 | DEFNE10 | DEFNE10 | DEFNE10 | KITAP50 | KITAP50 | KITAP50 | KITAP50 | KITAP50 | KITAP50 | KITAP50 | KITAP50 | KITAP50 | TANIMSIZ |
| **uyelik** | - | - | - | - | - | - | - | - | - | - | - | - | - | MISAFIR | MISAFIR | KLASIK | KLASIK | ALTIN | ALTIN | - |
| **ara_toplam** | <150 | 150–399.99 | 400–1499.94 | 1499.95–20k | >20k | <150 | 150–399.99 | 400–1499.94 | 1499.95–20k | >20k | <150 | 150–399.99 | >20k | 400–1499.94 | 1499.95–20k | 400–1499.94 | 1499.95–20k | 400–1499.94 | 1499.95–20k | - |
| **sonuc** | ERR_MIN | KABUL | KABUL | KABUL | ERR_MAX | ERR_MIN | KABUL | KABUL | KABUL | ERR_MAX | ERR_MIN | KABUL | ERR_MAX | KABUL | KABUL | KABUL | KABUL | KABUL | KABUL | ERR_KUPON |
| **KI** | - | 0.00 | 0.00 | 0.00 | - | - | %10 | %10 | 150.00 | - | - | 0.00 | - | 0.00 | 0.00 | 50.00 | 50.00 | 50.00 | 50.00 | - |
| **uygulandi** | - | false | false | false | - | - | true | true | true | - | - | false | - | false | false | true | true | true | true | - |
| **Test** | TC-003 | TC-031 | TC-032 | TC-006 | TC-061 | TC-069 | TC-005 | TC-014 | TC-012 | TC-008 | TC-070 | TC-015 | TC-071 | TC-018 | TC-066 | TC-021 | TC-067 | TC-017 | TC-068 | TC-058 |

*(Kısaltmalar: `ERR_MIN = ERR_MIN_SEPET`, `ERR_MAX = ERR_MAX_SEPET`, `ERR_KUPON = ERR_KUPON_GECERSIZ`, `20k = 20000`.)*

### 4.2 Kargo Ücreti ve Kapıda Ödeme Karar Tablosu (`DS-003`)

`MISAFIR` ve `KLASIK` kargo/kapıda ödeme kurallarında özdeş olduğu için `MISAFIR_KLASIK` olarak birleştirilmiş, `KREDI_KARTI`/`BANKA_KARTI`/`CEPPAY` ise `DIGER` sınıfında modellenmiştir. `96` kombinasyonun tamamı **0 boşluk, 0 çelişki** ile 19 sadeleştirilmiş kolona indirgenmiş ve **19/19 (%100)** testle kapsanmıştır:

| Kolon | D01 | D02 | D03 | D04 | D05 | D06 | D07 | D08 | D09 | D10 | D11 | D12 | D13 | D14 | D15 | D16 | D17 | D18 | D19 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **uyelik** | - | - | - | - | - | - | - | - | - | M/K | M/K | M/K | M/K | M/K | M/K | ALTIN | ALTIN | ALTIN | ALTIN |
| **nt_araligi** | - | - | - | - | - | <750 | >=750 | >=750 | >=750 | <750 | <750 | <750 | <750 | >=750 | >=750 | - | - | <750 | <750 |
| **teslimat** | STD | HIZLI | HIZLI | MAG | MAG | HIZLI | STD | STD | HIZLI | STD | STD | STD | STD | STD | STD | STD | STD | STD | STD |
| **bolge** | - | NORM | UZAK | - | - | NORM | NORM | NORM | NORM | NORM | NORM | UZAK | UZAK | UZAK | UZAK | UZAK | UZAK | NORM | NORM |
| **odeme** | KPD | KPD | - | DIG | KPD | DIG | DIG | KPD | DIG | DIG | KPD | DIG | KPD | DIG | KPD | DIG | KPD | DIG | KPD |
| **ot_limiti** | >5000 | - | - | - | - | - | - | <=5000 | - | - | <=5000 | - | <=5000 | - | <=5000 | - | <=5000 | - | <=5000 |
| **sonuc** | ERR_LIM | ERR_UYG | ERR_BLG | KABUL | ERR_UYG | KABUL | KABUL | KABUL | KABUL | KABUL | KABUL | KABUL | KABUL | KABUL | KABUL | KABUL | KABUL | KABUL | KABUL |
| **KU** | - | - | - | 0.00 | - | 79.90 | 0.00 | 0.00 | 40.00 | 39.90 | 39.90 | 64.90 | 64.90 | 25.00 | 25.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| **HB** | - | - | - | 0.00 | - | 0.00 | 0.00 | 12.90 | 0.00 | 0.00 | 12.90 | 0.00 | 12.90 | 0.00 | 12.90 | 0.00 | 12.90 | 0.00 | 12.90 |
| **Test** | TC-038 | TC-042 | TC-030 | TC-031 | TC-043 | TC-028 | TC-022 | TC-037 | TC-029 | TC-001 | TC-034 | TC-024 | TC-064 | TC-025 | TC-036 | TC-027 | TC-035 | TC-017 | TC-065 |

*(Kısaltmalar: `M/K=MISAFIR_KLASIK`, `STD=STANDART`, `MAG=MAGAZA`, `NORM=NORMAL`, `DIG=DIGER`, `KPD=KAPIDA_ODEME`, `ERR_LIM=ERR_KAPIDA_LIMIT`, `ERR_UYG=ERR_KAPIDA_UYGUNLUK`, `ERR_BLG=ERR_TESLIMAT_BOLGE`.)*

### 4.3 Çoklu Hata Öncelik Sırası (Bölüm 9.3)

| Öncelik Çifti | Birlikte Tetiklenen Hatalar | Beklenen Kazanan Hata | Test |
|---|---|---|---|
| 1 > 2 | `uyelik=PLATIN` (`ERR_GECERSIZ_GIRDI`) + `kupon=YOK99` (`ERR_KUPON_GECERSIZ`) | `ERR_GECERSIZ_GIRDI` | `TC-057` |
| 2 > 3 | `kupon=YOK99` (`ERR_KUPON_GECERSIZ`) + `AT=100.00` (`ERR_MIN_SEPET`) | `ERR_KUPON_GECERSIZ` | `TC-058` |
| 2 > 4 | `kupon=YOK99` (`ERR_KUPON_GECERSIZ`) + `AT=25000.00` (`ERR_MAX_SEPET`) | `ERR_KUPON_GECERSIZ` | `TC-059` |
| 3 > 5 | `AT=100.00` (`ERR_MIN_SEPET`) + `HIZLI`/`UZAK` (`ERR_TESLIMAT_BOLGE`) | `ERR_MIN_SEPET` | `TC-060` |
| 4 > 5 | `AT=25000.00` (`ERR_MAX_SEPET`) + `HIZLI`/`UZAK` (`ERR_TESLIMAT_BOLGE`) | `ERR_MAX_SEPET` | `TC-061` |
| 5 > 6 | `HIZLI`/`UZAK` (`ERR_TESLIMAT_BOLGE`) + `KAPIDA_ODEME` (`ERR_KAPIDA_UYGUNLUK`) | `ERR_TESLIMAT_BOLGE` | `TC-062` |
| 6 > 7 | `HIZLI` + `KAPIDA_ODEME` (`ERR_KAPIDA_UYGUNLUK`) + `AT=6000.00` (`ERR_KAPIDA_LIMIT`) | `ERR_KAPIDA_UYGUNLUK` | `TC-063` |

---

## 5. Sipariş Durum Geçiş Modeli (`DS-004`)

### 5.1 Başlangıç Durumları ve Tam Durum × Olay Matrisi (10 Durum × 12 Olay)

- **Başlangıç (Bölüm 10.2):** `KAPIDA_ODEME` → **`ONAYLANDI`** (`TC-075`); `KREDI_KARTI`, `BANKA_KARTI`, `CEPPAY` → **`ODEME_BEKLENIYOR`** (`TC-072..TC-074`).
- **Durum × Olay Matrisi (`—` = geçersiz geçiş adayı `N-01..N-106`, kural 10.5 adım 2 gereği `ERR_GECERSIZ_GECIS` döner ve durum/sayaç değişmez):**

| Durum \ Olay | ODEME_BASARILI | ODEME_BASARISIZ | ZAMAN_ASIMI | IPTAL | HAZIRLAMAYA_BASLA | KARGOYA_VER | TESLIM_BASARILI | TESLIM_BASARISIZ | YENIDEN_DAGITIM | IADE_TALEBI | IADE_ONAY | IADE_RED |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **ODEME_BEKLENIYOR** | G1→ONAYLANDI | G2→ODEME_BEKLENIYOR | G3→IPTAL_EDILDI | G4→IPTAL_EDILDI [M/O] | — | — | — | — | — | — | — | — |
| **ONAYLANDI** | — | — | — | G5→IPTAL_EDILDI [M/O] | G6→HAZIRLANIYOR | — | — | — | — | — | — | — |
| **HAZIRLANIYOR** | — | — | — | G7→IPTAL_EDILDI [O] | — | G8→KARGODA | — | — | — | — | — | — |
| **KARGODA** | — | — | — | — | — | — | G9→TESLIM_EDILDI | G10→TESLIM_EDILEMEDI (<3)<br>G11→DEPOYA_DONDU (=3) | — | — | — | — |
| **TESLIM_EDILEMEDI** | — | — | — | — | — | — | — | — | G12→KARGODA | — | — | — |
| **TESLIM_EDILDI** | — | — | — | — | — | — | — | — | — | G13→IADE_TALEP_EDILDI | — | — |
| **IADE_TALEP_EDILDI** | — | — | — | — | — | — | — | — | — | — | G14→IADE_EDILDI | G15→TESLIM_EDILDI |
| **IPTAL_EDILDI** *(son)* | — | — | — | — | — | — | — | — | — | — | — | — |
| **DEPOYA_DONDU** *(son)* | — | — | — | — | — | — | — | — | — | — | — | — |
| **IADE_EDILDI** *(son)* | — | — | — | — | — | — | — | — | — | — | — | — |

### 5.2 Geçerli Geçişler, 1-Switch Zincirler ve İş Kuralı Kısıtları

- **Durum ve Geçiş Kapsamı:** **10/10** durum ve **15/15** geçiş (`G1..G15`, her iki `aktor` rolü dahil) kapsanmıştır (`TC-072..TC-100`).
- **1-Switch Kapsamı:** `state_transition.py` tüm ardışık geçiş çiftleri için `8` adet 1-switch zinciri (`S-01..S-08`, `25` çift) üretmiştir.
  - **Önemli Model Bulgusu:** `S-06` zincirinde statik durum grafiği `G15 (IADE_RED) -> G13 (IADE_TALEBI)` çiftini geçerli sanmaktadır; oysa `G13` koşulu (`onceki_red_yok`) `IADE_RED` sonrasında yanlış (false) hale geldiği için bu çift iş kuralı gereği **imkansızdır** ve `ERR_IADE_TEKRAR` üretir (`TC-099`). Bu nedenle `durum-gecis-testleri.csv` içinde mümkün olan tüm **24/24** 1-switch çifti kapsanmış, imkansız `G15->G13` ise negatif red testiyle (`TC-099`, `TC-100`) doğrulanmıştır.
- **Sayaç ve Koşul Sınırları:**
  - `TESLIM_BASARISIZ` 1. deneme (`TC-090`) → `TESLIM_EDILEMEDI`, 2. deneme (`TC-092`) → `TESLIM_EDILEMEDI`, 3. denemede kurtarma (`TC-093`) → `TESLIM_EDILDI`, 3. başarısızlık (`TC-094`) → `DEPOYA_DONDU`.
  - `IADE_TALEBI`: `gun=0` (`TC-095`), `gun=14` (`TC-096`), `gun=15` (`TC-097` → `ERR_IADE_SURESI`).

### 5.3 Geçersiz Geçişler (`N-##`) ve Bölüm 10.5 İşleme Sırası Stratejisi

- `106` boş hücrenin tamamı Bölüm 10.5 Adım 2 gereği aynı `ERR_GECERSIZ_GECIS` kuralına tabidir. Test setini gereksiz yere 150+ satıra şişirmemek için her **10 durumun tamamından** ve özellikle yüksek riskli iş kurallarından temsili geçersiz geçişler (`TC-087`, `TC-101..TC-115`) seçilmiştir:
  - Ödeme öncesi hazırlık/kargo atlama (`TC-101`, `TC-102`), mükerrer ödeme (`TC-103`), `KAPIDA_ODEME` zaman aşımı (`TC-104`), hazırlık atlama (`TC-105`), kargosuz teslim (`TC-106`),
  - Bölüm 10.6: `KARGODA` ve `TESLIM_EDILEMEDI` iken hem `MUSTERI` hem `OPERATOR` iptalinin engellenmesi (`TC-107`, `TC-108`, `TC-110`),
  - `TESLIM_EDILEMEDI` iken doğrudan `TESLIM_BASARILI` engeli (`TC-109`), talepsiz `IADE_ONAY` (`TC-111`), açık talepte ikinci `IADE_TALEBI` (`TC-112`),
  - Üç son durumun (`IPTAL_EDILDI`, `DEPOYA_DONDU`, `IADE_EDILDI`) kilitliliği (`TC-113`, `TC-114`, `TC-115`).
- **Bölüm 10.5 Olay İşleme Önceliği Testleri (`TC-116..TC-123`):**
  1. Kural 1 (Tanımsız olay adı → `ERR_GECERSIZ_GIRDI`): normal durumda (`TC-116`) ve **son durumda bile** (`TC-117` — Kural 1 > Kural 2).
  2. Kural 2 > Kural 3: `KARGODA` iken geçersiz parametreli `IPTAL(aktor=ADMIN)` → `ERR_GECERSIZ_GECIS` (`TC-118`, çünkü `IPTAL` `KARGODA` için tabloda yoktur).
  3. Kural 3 (Olay tabloda var ama parametre geçersiz/eksik → `ERR_GECERSIZ_GIRDI`): `HAZIRLANIYOR` + `IPTAL(aktor=ADMIN)` (`TC-119`), `ONAYLANDI` + parametresiz `IPTAL` (`TC-120`), `IADE_TALEBI` için `gun=-1`, `gun=1.5`, parametresiz (`TC-121..TC-123`).
  4. Kural 4: Önceden reddedilmiş iade varken `gun=15` gelirse `ERR_IADE_SURESI` > `ERR_IADE_TEKRAR` (`TC-100`).

---

## 6. E2E Ödeme Konfigürasyon Kombinasyonlarına Yaklaşım (`DS-005`)

### 6.1 Kombinasyon Azaltma ve Efor Analizi

Bölüm 11.1'deki 4 faktörün tam kartezyen çarpımı **`3 × 4 × 3 × 3 = 108`** kombinasyondur (15 dk/test ile **27 saat**). Bölüm 11.2 kısıtları (`KS-1..KS-3`) uygulanınca `33` geçersiz kombinasyon elenir ve **`75` geçerli kombinasyon** kalır (**18,75 saat**). Manuel regresyon bütçesi göz önünde bulundurularak alternatifler hesaplanmıştır:

| Yaklaşım | Koşulacak Satır | Tahmini Efor (15 dk/satır) | Azalma (108'e / 75'e göre) | Kapsam Güvencesi |
|---|---:|---:|---:|---|
| Tam Geçerli Uzay | 75 | 18,75 saat | %30,6 / %0 | Tüm 3 ve 4'lü etkileşimler |
| 3-lü (3-wise, `t=3`) | 39 | 9,75 saat | %63,9 / %48,0 | 112/112 mümkün 3'lü |
| **Çiftli (Pairwise, `t=2`) — Seçilen** | **14** | **3,50 saat** | **%87,0 / %81,3** | **59/59 (%100) tüm mümkün 2'li etkileşimler** |

E-ticaret ödeme hatalarının büyük çoğunluğu tek veya iki faktör etkileşiminden (`platform × odeme_yontemi`, `odeme_yontemi × teslimat_tipi`, `uyelik × odeme_yontemi`) kaynaklandığı için **kısıtlı 2'li (pairwise) kapsama** en uygun maliyet/kapsam dengesini sağlar.

### 6.2 Hariç Tutulan Kısıtlar ve Seçilen 14 Konfigürasyon (`konfigurasyon-matrisi.csv`)

- **Hariç tutulan 4 kısıtlı çift (`KS-1..KS-3`):** `(KAPIDA_ODEME, HIZLI)`, `(KAPIDA_ODEME, MAGAZA)`, `(WEB, CEPPAY)`, `(MISAFIR, CEPPAY)`. Bu kısıtların ödeme ekranında engellendiği ayrıca 3 kısa UI negatif testiyle (`TC-138..TC-140`) doğrulanır.
- **Koşulacak 14 Satır (`TC-124..TC-137`):**

| ID | platform | odeme_yontemi | teslimat_tipi | uyelik |
|---|---|---|---|---|
| TC-124 | WEB | KREDI_KARTI | STANDART | MISAFIR |
| TC-125 | WEB | BANKA_KARTI | HIZLI | KLASIK |
| TC-126 | WEB | KAPIDA_ODEME | STANDART | ALTIN |
| TC-127 | IOS | KREDI_KARTI | HIZLI | ALTIN |
| TC-128 | IOS | BANKA_KARTI | MAGAZA | MISAFIR |
| TC-129 | IOS | KAPIDA_ODEME | STANDART | KLASIK |
| TC-130 | IOS | CEPPAY | MAGAZA | ALTIN |
| TC-131 | ANDROID | KREDI_KARTI | MAGAZA | KLASIK |
| TC-132 | ANDROID | BANKA_KARTI | STANDART | ALTIN |
| TC-133 | ANDROID | KAPIDA_ODEME | STANDART | MISAFIR |
| TC-134 | ANDROID | CEPPAY | HIZLI | KLASIK |
| TC-135 | WEB | KREDI_KARTI | MAGAZA | MISAFIR |
| TC-136 | IOS | CEPPAY | STANDART | KLASIK |
| TC-137 | WEB | KREDI_KARTI | HIZLI | MISAFIR |

---

## 7. Spesifikasyonla İlgili Çelişki, Belirsizlik ve Sorular (`Q-001` .. `Q-010`)

Spesifikasyonun statik incelemesi ve karar/durum modelleri sonucunda **1 doğrudan çelişki** ve **9 belirsizlik/boşluk** tespit edilmiştir:

| ID | Öncelik | Konu / Spesifikasyon Yeri | Tespit / Belirsizlik | Seçenekler & Testlerdeki Varsayılan Kabul | Muhatap |
|---|---|---|---|---|---|
| **Q-005** | **Önemli (Çelişki)** | Ek-A Örnek 4 vs Böl. 6.2 & 6.5 (`REQ-007`) | Ek-A Örnek 4 (`KLASIK`, `AT=900,00`, `STANDART`, `UZAK`) için `KU=0,00`, `OT=900,00` yazılmıştır; oysa 6.2 ve 6.5 `25,00 TL` uzak bölge ek ücretinin `KLASIK` için devam ettiğini belirtir. | **Varsayım:** Bölüm 4–8 kuralları geçerlidir (`KU=25.00`, `OT=925.00`, `TC-025`). Ek-A Örnek 4 güncellenmelidir. | PO / BA |
| **Q-002** | Önemli | Böl. 3.1 vs 4.1 (`REQ-002`, `REQ-004`) | `ara_toplam <= 0` (`0.00`, `-10.00`) geldiğinde Bölüm 3 tablosundaki "0'dan büyük" kuralından `ERR_GECERSIZ_GIRDI` mi, yoksa 4.1'den `ERR_MIN_SEPET` mi döneceği yoruma açıktır. | **Varsayım:** `<= 0` geçerli girdi aralığı dışındadır → `ERR_GECERSIZ_GIRDI` (`TC-046`, `TC-047`). | BA / Dev |
| **Q-003** | Önemli | Böl. 3 (`REQ-002`) | (1) `MAGAZA` seçiliyken `bolge` tanımsız değer alırsa ("doğrulanmaz") hata döner mi? (2) `ara_toplam` tam sayı (`150`) veya tek ondalıklı (`150.5`) biçimde ve JSON `number`/`string` olarak kabul edilir mi? | **Varsayım:** `MAGAZA` iken `bolge` hiç doğrulanmaz (`TC-033`); geçerli CSV testleri 2 ondalıklı verilmiştir. | Dev / BA |
| **Q-006** | Önemli | Böl. 10.1–10.4 vs 6.6 (`REQ-012`, `REQ-013`) | `MAGAZA` (mağazadan teslim al) siparişlerinin `HAZIRLANIYOR` sonrası `KARGODA`/`TESLIM_BASARISIZ`/`DEPOYA_DONDU` akışına mı tabi olduğu yoksa mağazada bekleme durumu/süresi mi olduğu tanımlanmamış. | **Varsayım:** v1.4 durum makinesi tüm teslimat tiplerinde ortak uygulanır. | PO / BA |
| **Q-007** | Önemli | Böl. 10.2–10.4 vs 7 (`REQ-012`) | `KAPIDA_ODEME` siparişinde kapıda ödeme reddedilirse `TESLIM_BASARISIZ` 3 deneme kuralı mı işler, yoksa tek seferde `DEPOYA_DONDU`/`IPTAL_EDILDI` olur mu? İade yöntemi tanımlı değil. | **Varsayım:** v1.4 geçiş tablosu ödeme tipine göre ayrım yapmadığından G10–G11 aynı işler. | PO / Ops |
| **Q-004** | Orta | Böl. 5.2 (`REQ-005`) | Yalnızca boşluklardan oluşan `kupon="   "` veya JSON `null` değeri kırpma sonrası "kupon yok" mu sayılır, `ERR_KUPON_GECERSIZ` mi döner? | **Varsayım:** Kırpma sonrası boş kabul edilir (`KABUL`). Netleşene kadar yalnızca boşluklu veri CSV'ye alınmadı. | Dev / BA |
| **Q-008** | Orta | Böl. 10.4 G2–G3 (`REQ-012`) | (1) `ODEME_BASARISIZ` için maksimum deneme sayısı var mı? (2) 30. dakikada `ODEME_BASARILI` ile `ZAMAN_ASIMI` yarış durumunda hangisi kazanır? | **Varsayım:** Deneme sınırı yoktur; atomik kilit ile ilk işlenen kazanır, diğeri `ERR_GECERSIZ_GECIS` alır. | Dev / PO |
| **Q-009** | Orta | Böl. 10.4 G13–G15 (`REQ-013`, `REQ-014`) | Operatör hatalı `IADE_RED` verirse ikinci talep istisnası yok (`ERR_IADE_TEKRAR`); ayrıca iptal/iade geçişlerindeki ödeme iadesi ve kupon serbest bırakma yan etkileri yazılmamış. | **Varsayım:** v1.4 kapsamında tekrar talep tamamen engellidir (`TC-099`). | PO / BA |
| **Q-010** | Orta | Böl. 11.1 (`REQ-016`) | `WEB` için tarayıcı matrisi (Chrome, Safari, Firefox, Edge), iOS/Android OS sürümleri ve E2E testlerde `bolge`/`kupon` seçimi belirtilmemiş. | **Varsayım:** Matris 4 faktörü kapsar; tarayıcı/OS ve `bolge` E2E koşum ortamında standart olarak dağıtılır. | QA / PO |
| **Q-001** | Düşük | Böl. 2 (`REQ-001`) | `ara_toplam` istemci tarafından hesaplanıp geliyor; fiyat manipülasyonuna karşı (OWASP ASVS V2) sunucu doğrulaması SFM katmanında mı üst katmanda mı? | **Varsayım:** SFM v1.4 salt fiyatlama motorudur; kalem doğrulaması üst katman sorumluluğundadır. | Security / Dev |

*(Ek gözlem: Bölüm 10.3'teki `IADE_TALEBI(gun=n)` için takvim günü hesabının `UTC+3` Türkiye saat dilimi tarih farkına göre yapıldığı varsayılmıştır.)*

---

## 8. Varsayımlar, Kalibrasyon İstisnaları ve Kapsam Dışı Bırakılanlar

### 8.1 Varsayımlar
- Tüm test vakaları geliştirme öncesi taslak (`draft`) statüsündedir; `Q-002`, `Q-003`, `Q-005`..`Q-010` yanıtlandığında ilgili vakalar `ready` olarak onaylanacaktır.
- SFM `POST /api/v2/sepet/fiyatla` uç noktasında fiyat verileri yalnızca spesifikasyon kodlarıyla ve ondalık nokta biçiminde gönderilir; geçersiz biçimlerde (`150,00`, `1.500.00`, `abc`) istemcinin ham string iletebildiği veya API şema doğrulamasının `ERR_GECERSIZ_GIRDI` döndürdüğü kabul edilmiştir.
- E2E 14 konfigürasyonunda `bolge=NORMAL` (standart sepet) varsayılan alınıp en az 2 satırda `UZAK` bölge ve kuponlu akışın koşturulması önerilir.

### 8.2 Kalibrasyon İstisnaları (`build_rtm.py` Çıktısı)
Otomatik kalibrasyon aracının aynı `(REQ, polarite, teknik, sonuç)` imzası nedeniyle işaretlediği 6 `REDUNDANT` aday grubu incelenmiş ve **hiçbirinin gerçek kopya olmadığı** doğrulanmıştır:
1. `TC-024`, `TC-025`, `TC-032`: Farklı `DS-003` kolonlarını (`D12` `64.90`, `D14` `25.00` Ek-A düzeltmesi, `D04` `MAGAZA` `0.00`) test eder.
2. `TC-035`, `TC-036`, `TC-064`, `TC-065`: Farklı `DS-003` `KAPIDA_ODEME` kolonlarını (`D17`, `D15`, `D13`, `D19`) ve farklı toplamları (`0+12.90`, `25+12.90`, `64.90+12.90`, `0+12.90 NORMAL`) test eder.
3. `TC-044`, `TC-045`, `TC-047`, `TC-051`, `TC-052`, `TC-053`, `TC-056`: Her biri farklı bir girdi alanının (`uyelik`, `ara_toplam`, `teslimat_tipi`, `odeme_yontemi`) geçersiz sınıfını tek-hata ilkesiyle test eder; birleştirilemez.
4. `TC-072..TC-086`: Başlangıç durumları (`KREDI_KARTI`, `BANKA_KARTI`, `CEPPAY`), ödeme retry/timeout zincirleri (`G2`, `G2->G1`, `G2->G3`) ve farklı durum/aktör iptalleri (`G4-M/O`, `G5-M/O`, `G7-O`) ayrı durum geçişleridir.

### 8.3 Kapsam Dışı Bırakılanlar
- **Spesifikasyon Bölüm 1 kapsam dışıları:** Stok kontrolü, ürün bazlı kampanyalar, fatura/e-arşiv oluşturma, puanların hesaba geçmesi ve harcanması, gerçek kargo firması entegrasyonu.
- **Yönetilen Kapsam Daraltmaları:**
  - `106` geçersiz durum×olay hücresinin tamamı yerine her durumdan ve son durumlardan risk odaklı `15` geçersiz geçiş + `8` olay işleme sırası testi (toplam maliyet kontrolü).
  - E2E konfigürasyonlarında `t=3` (39 test) ve tam uzay (75 test) yerine `t=2` pairwise (14 test / 3,5 saat).
  - Performans/yük testleri (kampanya pik yükü, k6), güvenlik sızma testleri (ASVS), erişilebilirlik (WCAG 2.2) ve gerçek ödeme sağlayıcısı/3DS kesinti senaryoları fonksiyonel v1.4 tasarım kapsamı dışında bırakılmıştır.

---

## 9. Teslimat Dosyaları Özeti

| Dosya | İçerik | Kayıt / Kapsam |
|---|---|---|
| `cikti/test-tasarimi.md` | Test tasarım metodolojisi, EP/BVA, karar tabloları, durum modeli, E2E yaklaşım, çelişki/sorular | `16` REQ, `10` soru (`Q-001..Q-010`) |
| `cikti/fiyat-test-verisi.csv` | SFM fiyatlandırma test vakaları (UTF-8, `;` ayraçlı, kuruş doğrulamalı) | `71` vaka (`TC-001..TC-071`) |
| `cikti/durum-gecis-testleri.csv` | Sipariş durum geçiş test vakaları (UTF-8, `;` ayraçlı, ` > ` olay dizili) | `52` vaka (`TC-072..TC-123`) |
| `cikti/konfigurasyon-matrisi.csv` | E2E manuel ödeme regresyonu pairwise konfigürasyon matrisi | `14` vaka (`TC-124..TC-137`) |
