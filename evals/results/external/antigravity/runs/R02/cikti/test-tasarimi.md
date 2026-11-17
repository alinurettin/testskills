# SFM v1.4 Test Tasarım Dokümanı

**Proje / Ürün:** Defne Kitap ve Kırtasiye A.Ş. — Sipariş Fiyatlandırma Motoru (SFM) ve Sipariş Durum Yönetimi  
**Referans Spesifikasyon:** `girdiler/SFM-spesifikasyon-v1.4.md` (Doküman No: DK-SPEC-214, Onaylı v1.4)  
**Hazırlayan:** Kıdemli Test Analisti  
**Durum:** Taslak — Açık sorular (`Q-001`–`Q-011`) PO/Ekip onayına sunulmuştur  

---

## 1. Yönetici Özeti ve Teslimat Envanteri

Bu doküman, geliştirme aşamasına başlanacak SFM v1.4 (`POST /api/v2/sepet/fiyatla`), sipariş durum yaşam döngüsü ve E2E ödeme akışı için risk temelli test tasarımını içerir. Tüm test verileri, sınır değerleri, karar tabloları, durum geçiş dizileri ve ikili konfigürasyon matrisi QA Suite tasarım betikleriyle (`ep_bva.py`, `decision_table.py`, `state_transition.py`, `pairwise.py`) hesaplanmış ve bağımsız bir Python hesaplama/simülasyon doğrulayıcısıyla kuruşu kuruşuna doğrulanmıştır.

| Teslimat Dosyası | Kapsam | Vaka / Satır Sayısı | Öne Çıkan Kapsam Kanıtı |
|---|---|---:|---|
| `cikti/test-tasarimi.md` | Teknikler, EP/BVA, karar tabloları, durum modeli, pairwise, tespitler | — | 16/16 gereksinim (%100 izlenebilirlik) |
| `cikti/fiyat-test-verisi.csv` | SFM fiyatlandırma veri güdümlü test vakaları (`FIYAT-01`–`FIYAT-92`) | 92 (55 `KABUL`, 37 hata) | `DS-001` 45/45 (%100), `DS-002` 20/20 (%100), `DS-003` 30/30 (%100) |
| `cikti/durum-gecis-testleri.csv` | Sipariş durum geçiş test vakaları (`DURUM-01`–`DURUM-55`) | 55 (25 `KABUL`, 30 hata) | 10/10 durum, 17/17 geçerli geçiş, 29/29 1-switch zinciri + 26 hedefli hata/BVA/öncelik |
| `cikti/konfigurasyon-matrisi.csv` | Manuel E2E ödeme regresyon matrisi (`KONF-01`–`KONF-14`) | 14 | 59/59 mümkün ikili çift (%100), KS-1..KS-3 uyumlu, **3,5 saat** koşum süresi |

> **Ek Kapsam Notu:** `TASK.md` gereği `durum-gecis-testleri.csv` içinde son olay öncesi tüm olayların geçerli ön koşul olması zorunlu tutulduğundan, hata sonrası sayaç/durum değişmezliğini (Kural 10.5.5) iki adımda doğrulayan **2 atomiklik senaryosu (`ATOM-01`, `ATOM-02`)** ve ödeme ekranındaki yasak kombinasyonların seçilemediğini doğrulayan **3 arayüz kısıt kontrolü (`KISIT-01`–`KISIT-03`)** bu dokümanda ve iç izlenebilirlik setinde ayrıca tanımlanmıştır (toplam 166 izlenebilir test vakası).

---

## 2. Kullanılan Test Tasarım Teknikleri, Risk Derinliği ve Gerekçeleri

### 2.1 Gereksinim Risk Profili ve Bütçe Kontrolü
Spesifikasyon 16 atomik gereksinime (`REQ-001`–`REQ-016`) ayrıştırılarak `Olasılık × Etki (1–5)` ölçeğinde skorlanmıştır:
- **Kritik (17–25):** 3 gereksinim (%18,8) — `REQ-006` (`DEFNE10` yuvarlama/tavan), `REQ-008` (standart kargo / 750 TL eşiği / `UZAK` ek ücret ve Ek-A çelişkisi), `REQ-013` (sipariş yaşam döngüsü ana geçişleri).
- **Yüksek (10–16):** 9 gereksinim (%56,3) — `REQ-001`, `REQ-004`, `REQ-007`, `REQ-009`, `REQ-010`, `REQ-011`, `REQ-012`, `REQ-014`, `REQ-015`.
- **Orta (5–9):** 4 gereksinim (%25,0) — `REQ-002`, `REQ-003`, `REQ-005`, `REQ-016`.

Test vakası öncelikleri gereksinim riskinden kopyalanmamış, her testin başarısızlığının yayın kararına etkisine göre kalibre edilmiştir (166 testte: **%13 kritik (21), %30 yüksek (49), %51 orta (84), %7 düşük (12)**; öncelik şişmesi yoktur). Test sayısının gereksiz şişmesini önlemek için geçerli denklik sınıfları ve karar tablosu kolonları örtüşmeyen sınır değerleriyle birleştirilmiş, geçersiz değerler ise hata maskelenmesini engellemek amacıyla **tek hata (single-fault)** ilkesiyle ayrılmıştır.

### 2.2 Teknik Seçim Matrisi

| Kapsam Alanı | Seçilen Teknik(ler) | Tasarım Çıktısı | Gerekçe |
|---|---|---|---|
| Girdi alanları, sepet/kupon/kargo/kapıda ödeme limitleri, iade gün penceresi, teslimat sayacı | **Denklik Paylarına Ayırma (EP)** + **3-Değerli Sınır Değer Analizi (BVA)** | `DS-001`, `DS-006` | Para ve gün eşiklerinde (`<` vs `<=`) off-by-one ve kuruş yuvarlama hataları doğrudan mali kayıp ürettiğinden kritik sınırlarda 3-değerli (`sınır - adım`, `sınır`, `sınır + adım`) derinlik seçilmiştir. |
| Kupon uygunluğu & sepet limitleri | **Karar Tablosu (`first_match`)** | `DS-002` | `kupon × AT × uyelik` etkileşimi 60 kombinasyonu 20 sadeleştirilmiş kolona indirger; hata öncelik sırasını ve koşul sağlanmadığında hata dönmeme kuralını (5.5) eksiksiz kanıtlar. |
| Kargo ücreti, uzak bölge ve kapıda ödeme kuralları | **Karar Tablosu (`first_match`)** | `DS-003` | `teslimat × bolge × uyelik × nt_esik × odeme_limit` arasındaki 135 geçerli kombinasyonu 30 test koşuluna sadeleştirir; 0 boşluk, 0 çelişki ve sağlama `OK` ile doğrulanmıştır. |
| Sipariş durum yaşam döngüsü | **Durum Geçiş Testi (1-switch + hedefli geçersiz geçişler)** | `DS-004` | Finansal ve operasyonel döngülerde ardışık durum çiftleri (ör. `ODEME_BASARISIZ → ODEME_BASARILI` veya `TESLIM_BASARISIZ → YENIDEN_DAGITIM → TESLIM_BASARISIZ`) kritik olduğundan 1-switch kapsamı + 10 durumun tamamından riskli geçersiz geçişler seçilmiştir. |
| E2E ödeme regresyon matrisi | **Pairwise / İkili Kombinatoryal (t=2, kısıtlı)** | `DS-005` | Her manuel koşum ~15 dk sürdüğünden 75 geçerli kombinasyon (18,75 saat) maliyetli, t=2 pairwise ise 14 satırda (3,5 saat) tüm 59 mümkün ikili etkileşimi %100 kapsamaktadır. |
| Yuvarlama sırası, Türkçe karakter, format ve öncelik çakışmaları | **Hata Tahmini (Error Guessing)** | `FIYAT-34..44, 54..60, 85..92` | `KİTAP50` (noktalı `İ`), `1499,90` (virgül), kupon sonrası `NT < 750` düşüşü, tavan öncesi yuvarlama ve 7 seviyeli hata çakışmaları klasik e-ticaret hata kümeleridir. |

---

## 3. Denklik Sınıfları (EP) ve Sınır Değer Analizi (BVA)

### 3.1 Girdi ve Türetilmiş Parametre Denklik Sınıfları

| Parametre | Geçerli Denklik Sınıfları | Geçersiz Denklik Sınıfları | İlgili Testler |
|---|---|---|---|
| `ara_toplam` (TL) | `150.00..399.99` (`KITAP50` uygulanmaz); `400.00..1499.94` (`KITAP50` uygulanır, `DEFNE10` tavansız); `1499.95..20000.00` (`DEFNE10` tavanlı); `250` / `250.5` (0–1 ondalık) | `0.01..149.99` (`ERR_MIN_SEPET`); `> 20000.00` (`ERR_MAX_SEPET`); `<= 0.00`, 3 ondalık (`150.005`), virgül (`1499,90`), binlik nokta (`1.499.90`), metin (`abc`), boş (`ERR_GECERSIZ_GIRDI`) | `FIYAT-07`–`FIYAT-24` |
| `uyelik` | `MISAFIR`, `KLASIK`, `ALTIN` | Tanımsız (`PLATIN`), boş (`ERR_GECERSIZ_GIRDI`) | `FIYAT-01..03, 25, 26` |
| `kupon` | Boş `""`, `DEFNE10`, `KITAP50`, baş/son boşluklu (`" DEFNE10 "`, `" KITAP50 "`, `"   "` — `Q-003`) | Tanımsız (`SAHTE10`), küçük harf (`defne10`), Türkçe noktalı `İ` (`KİTAP50`) (`ERR_KUPON_GECERSIZ`) | `FIYAT-40`–`FIYAT-44, 51` |
| `teslimat_tipi` | `STANDART`, `HIZLI`, `MAGAZA` | Tanımsız (`EKSPRES`), boş (`ERR_GECERSIZ_GIRDI`) | `FIYAT-01, 02, 05, 27, 28` |
| `bolge` | `STANDART`/`HIZLI` için `NORMAL`, `UZAK`; `MAGAZA` için boş/herhangi (`Q-005`) | `STANDART`/`HIZLI` için tanımsız (`ADA`) veya boş (`ERR_GECERSIZ_GIRDI`) | `FIYAT-04, 05, 29..31, 68, 69` |
| `odeme_yontemi` | `KREDI_KARTI`, `BANKA_KARTI`, `KAPIDA_ODEME`, `CEPPAY` | Tanımsız (`HAVALE`), boş (`ERR_GECERSIZ_GIRDI`) | `FIYAT-01..06, 32, 33` |
| `NT` (Net Tutar, TL) | `135.00..749.99` (ücretli standart / tam hızlı kargo); `750.00..20000.00` (ücretsiz standart taban / indirimli hızlı kargo) | `NT < 135.00` (geçerli girdide matematiksel olarak ulaşılamaz) | `FIYAT-10, 52..60, 64..66` |
| `OT` (Kapıda Ödeme, TL) | `147.90..5000.00` (`KABUL`) | `> 5000.00` (`ERR_KAPIDA_LIMIT`) | `FIYAT-72`–`FIYAT-79` |
| `IADE_TALEBI.gun` | `0..14` (tamsayı) | `> 14` (`ERR_IADE_SURESI`); `< 0`, ondalıklı (`1.5`), eksik (`ERR_GECERSIZ_GIRDI`) | `DURUM-21`–`25, 53..55` |
| `TESLIM_BASARISIZ` sayacı | `1..2` (`TESLIM_EDILEMEDI`), `3` (`DEPOYA_DONDU`) | `<= 0` veya `> 3` (son durum kilidi ile engellenir) | `DURUM-15`–`17, 47` |

### 3.2 Kritik Sınır Değerleri (3-Değerli SDA Tablosu)

| Eşik / Kural | Sınır | Test Edilen Değerler (OFF / ON / IN) | Beklenen Sonuç | Test ID |
|---|---|---|---|---|
| Pozitif `AT` alt sınırı (3.1, 4.1) | `> 0` ve `150.00` | `-10.00` (OFF), `0.00` (OFF), `0.01` (ON min pozitif) | `ERR_GECERSIZ_GIRDI`, `ERR_GECERSIZ_GIRDI`, `ERR_MIN_SEPET` | `FIYAT-17, 16, 07` |
| Min sepet tutarı (4.1, 4.3) | `AT >= 150.00` | `149.99` (OFF), `150.00` (ON + `DEFNE10` -> `NT=135.00`), `150.01` (IN) | `ERR_MIN_SEPET`, `KABUL`, `KABUL` | `FIYAT-09, 10, 11` |
| `KITAP50` min sepet (5.4, 5.5) | `AT >= 400.00` | `399.98` (IN alt), `399.99` (OFF), `400.00` (ON), `400.01` (IN) | İlk ikisi `KABUL` (`KI=0.00, kupon_uygulandi=false`), son ikisi `KI=50.00` | `FIYAT-45, 46, 41, 47` |
| `DEFNE10` yarım-yukarı yuvarlama (2.2) | `.xx5` / `.xx4` | `150.44` (`15.044`), `150.45` (`15.045`) | `KI=15.04`, `KI=15.05` | `FIYAT-34, 35` |
| `DEFNE10` tavan sınırı (2.2, 5.3) | `KI <= 150.00` | `1499.93` (`149.99`), `1499.94` (`149.99`), `1499.95` (`150.00`), `1500.05` (`150.01→150.00`) | Yuvarlama sonrası tavan `150.00` aşmaz | `FIYAT-36`–`39` |
| Ücretsiz kargo eşiği — çıplak (6.2, 6.4b) | `NT >= 750.00` | `749.98` (IN alt), `749.99` (OFF), `750.00` (ON), `750.01` (IN) | `STANDART NORMAL`: `39.90 / 39.90 / 0.00 / 0.00`; `HIZLI`: `79.90 / 40.00` | `FIYAT-52..55, 64..66` |
| Ücretsiz kargo — kupon sonrası `NT` (6.2) | `AT - KI >= 750.00` | `760+DEFNE10` (`NT=684.00`), `799.99+KITAP50` (`749.99`), `800+KITAP50` (`750.00`), `833.32/833.33+DEFNE10` (`749.99/750.00`) | `NT < 750` iken kargo ücreti alınır; `NT=750.00`'da muaf olur | `FIYAT-56`–`60` |
| Kapıda ödeme min/max `OT` (7.2, 7.3) | `OT <= 5000.00` | Min `OT=147.90`; `NORMAL` (`AT=4987.09 / 4987.10 / 4987.11`); `UZAK` (`AT=4962.10 / 4962.11`); Kuponlu (`5137.10+DEFNE10`) | `OT=5000.00` `KABUL`, `OT=5000.01` `ERR_KAPIDA_LIMIT` | `FIYAT-72, 74`–`79` |
| Maksimum sepet tutarı (4.2, 4.3) | `AT <= 20000.00` | `19999.99` (IN), `20000.00` (ON), `20000.01` (OFF + `DEFNE10`) | `20000.01` indirimle 20 bin altına inse de `ERR_MAX_SEPET` | `FIYAT-12, 13, 14` |
| Sadakat puanı kesirleri (2.3, 8.2, 8.3) | `⌊NT/10⌋`, `⌊taban×1,5⌋` | `NT=159.99` (`KLASIK=15`, `ALTIN=22`), `NT=160.00` (`ALTIN=24`) | Kesirler daima aşağı yuvarlanır | `FIYAT-82, 83, 84` |
| İade süresi penceresi (10.4 G13) | `0 <= gun <= 14` | `-1` (OFF), `0` (ON), `1` (IN), `13` (IN), `14` (ON), `15` (OFF) | `-1` -> `ERR_GECERSIZ_GIRDI`, `0..14` -> `KABUL`, `15` -> `ERR_IADE_SURESI` | `DURUM-53, 21..25` |
| Başarısız teslim sayacı (10.4 G10–G11) | `1..2` vs `3` | `1. deneme`, `2. deneme`, `3. deneme` | `1, 2` -> `TESLIM_EDILEMEDI`; `3` -> `DEPOYA_DONDU` | `DURUM-15, 16, 17` |

---

## 4. Karar Tabloları ve Hata Öncelik Sırası

### 4.1 DS-002: Kupon Uygunluğu ve Sepet Limitleri (`first_match: true`)
`kupon (4) × at_aralik (5) × uyelik (3) = 60` kombinasyonunun tamamı 13 kural ile kapsanmıştır (**0 boşluk, 0 çelişki, sağlama OK**):

| Kolon | `kupon` | `at_aralik` | `uyelik` | `durum` | `ki_kurali` | `kupon_uygulandi` | Test ID |
|---|---|---|---|---|---|---|---|
| D01, D06, D11 | `YOK` / `DEFNE10` / `KITAP50` | `< 150` | `-` | `ERR_MIN_SEPET` | `-` | `-` | `FIYAT-09, 08, 07` |
| D02–D04 | `YOK` | `150..20000` | `-` | `KABUL` | `0.00` | `false` | `FIYAT-06, 04, 12` |
| D05, D10, D19 | `YOK` / `DEFNE10` / `KITAP50` | `> 20000` | `-` | `ERR_MAX_SEPET` | `-` | `-` | `FIYAT-15, 14` |
| D07, D08 | `DEFNE10` | `150..1499.94` | `-` | `KABUL` | `round(%10)` | `true` | `FIYAT-10, 01` |
| D09 | `DEFNE10` | `1499.95..20000` | `-` | `KABUL` | `tavan 150.00` | `true` | `FIYAT-02, 13, 38` |
| D12 | `KITAP50` | `150..399.99` | `-` | `KABUL` | `0.00` | `false` | `FIYAT-46` |
| D13, D16 | `KITAP50` | `400..20000` | `MISAFIR` | `KABUL` | `0.00` | `false` | `FIYAT-48, 49` |
| D14, D15, D17, D18 | `KITAP50` | `400..20000` | `KLASIK` / `ALTIN` | `KABUL` | `50.00` | `true` | `FIYAT-41, 03, 12, 50` |
| D20 | `TANIMSIZ` | `-` (öncelik #2) | `-` | `ERR_KUPON_GECERSIZ` | `-` | `-` | `FIYAT-42, 86, 87` |

### 4.2 DS-003: Kargo Ücreti ve Kapıda Ödeme Kuralları (`first_match: true`)
`teslimat (3) × bolge (3) × uyelik (3) × nt_esik (2) × odeme_limit (3) = 162` kombinasyonunun `27` olanaksız hücresi (`nt_esik=<750 ∧ odeme_limit=KAPIDA_>5000`) hariç `135` geçerli durumu **30 sadeleştirilmiş kolonda** kapsanmıştır (**0 boşluk, 0 çelişki, sağlama OK**):

| Kolon Grubu | `teslimat` | `bolge` | `uyelik` | `nt_esik` | `odeme_limit` | `durum` | `KU` (TL) | `HB` (TL) | Test ID |
|---|---|---|---|---|---|---|---|---|---|
| D21, D27 | `STANDART` / `HIZLI` | `BOS` | `-` | `-` | `-` | `ERR_GECERSIZ_GIRDI` | `-` | `-` | `FIYAT-30, 31` |
| D26 | `HIZLI` | `UZAK` | `-` | `-` | `-` | `ERR_TESLIMAT_BOLGE` | `-` | `-` | `FIYAT-67, 90` |
| D22, D23, D28, D30 | `HIZLI` / `MAGAZA` | `NORMAL` / `-` | `-` | `-` | `KAPIDA_*` | `ERR_KAPIDA_UYGUNLUK` | `-` | `-` | `FIYAT-80, 81, 91, 92` |
| D01, D10 | `STANDART` | `NORMAL` / `UZAK` | `-` | `>=750` | `KAPIDA_>5000` | `ERR_KAPIDA_LIMIT` | `-` | `-` | `FIYAT-76, 78` |
| D29 | `MAGAZA` | `-` | `-` | `-` | `DIGER` | `KABUL` | `0.00` | `0.00` | `FIYAT-05, 68, 69` |
| D24 | `HIZLI` | `NORMAL` | `-` | `<750` | `DIGER` | `KABUL` | `79.90` | `0.00` | `FIYAT-64` |
| D25 | `HIZLI` | `NORMAL` | `-` | `>=750` | `DIGER` | `KABUL` | `40.00` | `0.00` | `FIYAT-02, 65, 66` |
| D08, D19 | `STANDART` | `NORMAL` / `UZAK` | `ALTIN` | `-` | `DIGER` | `KABUL` | `0.00` | `0.00` | `FIYAT-03, 47, 63` |
| D09, D20 | `STANDART` | `NORMAL` / `UZAK` | `ALTIN` | `-` | `KAPIDA_<=5000` | `KABUL` | `0.00` | `12.90` | `FIYAT-72, 73` |
| D04, D06 | `STANDART` | `NORMAL` | `MISAFIR`/`KLASIK` | `<750` | `DIGER` | `KABUL` | `39.90` | `0.00` | `FIYAT-53, 01` |
| D05, D07 | `STANDART` | `NORMAL` | `MISAFIR`/`KLASIK` | `<750` | `KAPIDA_<=5000` | `KABUL` | `39.90` | `12.90` | `FIYAT-70, 35` |
| D02 | `STANDART` | `NORMAL` | `MISAFIR`/`KLASIK` | `>=750` | `DIGER` | `KABUL` | `0.00` | `0.00` | `FIYAT-54` |
| D03 | `STANDART` | `NORMAL` | `MISAFIR`/`KLASIK` | `>=750` | `KAPIDA_<=5000` | `KABUL` | `0.00` | `12.90` | `FIYAT-75` |
| D11, D15 | `STANDART` | `UZAK` | `MISAFIR`/`KLASIK` | `<750` | `DIGER` | `KABUL` | `64.90` | `0.00` | `FIYAT-10, 61, 62` |
| D12, D16 | `STANDART` | `UZAK` | `MISAFIR`/`KLASIK` | `<750` | `KAPIDA_<=5000` | `KABUL` | `64.90` | `12.90` | `FIYAT-71, 41` |
| D13, D17 | `STANDART` | `UZAK` | `MISAFIR`/`KLASIK` | `>=750` | `DIGER` | `KABUL` | `25.00` | `0.00` | `FIYAT-55, 04` |
| D14, D18 | `STANDART` | `UZAK` | `MISAFIR`/`KLASIK` | `>=750` | `KAPIDA_<=5000` | `KABUL` | `25.00` | `12.90` | `FIYAT-77, 58` |

### 4.3 Çoklu Hata Öncelik Sırası Doğrulamaları (Bölüm 9.3)
Bitişik öncelik basamaklarının tamamı eşzamanlı hata enjeksiyonu ile test edilmiştir:
- `#1 ERR_GECERSIZ_GIRDI > #2..#6`: `FIYAT-85`
- `#2 ERR_KUPON_GECERSIZ > #3 ERR_MIN_SEPET` (`FIYAT-86`) ve `> #4 ERR_MAX_SEPET` (`FIYAT-87`)
- `#3 ERR_MIN_SEPET > #5, #6`: `FIYAT-88`
- `#4 ERR_MAX_SEPET > #5, #6`: `FIYAT-89`
- `#5 ERR_TESLIMAT_BOLGE > #6 ERR_KAPIDA_UYGUNLUK`: `FIYAT-90`
- `#6 ERR_KAPIDA_UYGUNLUK > #7 ERR_KAPIDA_LIMIT`: `FIYAT-91` (`HIZLI`), `FIYAT-92` (`MAGAZA`, boş bölgeyle)

---

## 5. Sipariş Durum Geçiş Modeli (`DS-004`)

### 5.1 Başlangıç Durumları (10.2) ve Durum Tablosu (10 Durum × 13 Olay)
- **Başlangıç:** `KAPIDA_ODEME` -> `ONAYLANDI` (`DURUM-04`); `KREDI_KARTI`, `BANKA_KARTI`, `CEPPAY` -> `ODEME_BEKLENIYOR` (`DURUM-01`–`03`).
- Tablodaki `—` hücreleri **geçersiz geçişleri** (`ERR_GECERSIZ_GECIS`) ifade eder.

| Durum \ Olay | `ODEME_BASARILI` | `ODEME_BASARISIZ` | `ZAMAN_ASIMI` | `IPTAL(MUSTERI)` | `IPTAL(OPERATOR)` | `HAZIRLAMAYA_BASLA` | `KARGOYA_VER` | `TESLIM_BASARILI` | `TESLIM_BASARISIZ` | `YENIDEN_DAGITIM` | `IADE_TALEBI` | `IADE_ONAY` | `IADE_RED` |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **ODEME_BEKLENIYOR** *(başlangıç ≠ kapıda)* | G1 → `ONAYLANDI` | G2 → `ODEME_BEKLENIYOR` | G3 → `IPTAL_EDILDI` | G4 → `IPTAL_EDILDI` | G4 → `IPTAL_EDILDI` | — | — | — | — | — | — | — | — |
| **ONAYLANDI** *(başlangıç = kapıda)* | — | — | — | G5 → `IPTAL_EDILDI` | G5 → `IPTAL_EDILDI` | G6 → `HAZIRLANIYOR` | — | — | — | — | — | — | — |
| **HAZIRLANIYOR** | — | — | — | — *(ERR)* | G7 → `IPTAL_EDILDI` | — | G8 → `KARGODA` | — | — | — | — | — | — |
| **KARGODA** | — | — | — | — | — | — | — | G9 → `TESLIM_EDILDI` | G10 (`<3`) → `TESLIM_EDILEMEDI`<br>G11 (`=3`) → `DEPOYA_DONDU` | — | — | — | — |
| **TESLIM_EDILEMEDI** | — | — | — | — | — | — | — | — | — | G12 → `KARGODA` | — | — | — |
| **TESLIM_EDILDI** | — | — | — | — | — | — | — | — | — | — | G13 (`gun<=14 ∧ ilk`) → `IADE_TALEP_EDILDI` | — | — |
| **IADE_TALEP_EDILDI** | — | — | — | — | — | — | — | — | — | — | — | G14 → `IADE_EDILDI` | G15 → `TESLIM_EDILDI` |
| **IPTAL_EDILDI** *(son)* | — | — | — | — | — | — | — | — | — | — | — | — | — |
| **DEPOYA_DONDU** *(son)* | — | — | — | — | — | — | — | — | — | — | — | — | — |
| **IADE_EDILDI** *(son)* | — | — | — | — | — | — | — | — | — | — | — | — | — |

### 5.2 Geçerli ve Geçersiz Geçiş Test Stratejisi
- **Geçerli Geçişler (1-switch):** `state_transition.py --switch 1` çıktısındaki **10/10 durum, 17/17 geçiş ve 29/29 1-switch zinciri** (`DURUM-01`–`DURUM-20`, `DURUM-26`) eksiksiz test edilmiştir. (Not: Statik geçiş modeli `S-08` dizisinde `IADE_RED` sonrasında tekrar `IADE_TALEBI` üretse de G13'ün `onceki_red == false` koşulu gereği bu geçiş yasak olduğundan gerçek davranış negatif test `DURUM-27` ile doğrulanmıştır.)
- **Geçersiz Geçişler (`N-01`–`N-114` arasından risk odaklı örneklem):** 130 hücreden 114'ü geçersizdir. Tüm 114 simetrik hücre için şişirilmiş test yazmak yerine her ulaşılabilir durumdaki **yüksek riskli hata sınıfları** (`DURUM-29`–`DURUM-48`) seçilmiştir:
  1. Ödeme veya hazırlık aşamasını atlama (`N-01, N-02, N-12, N-37, N-64, N-73`)
  2. Çift ödeme / ödeme sonrası zaman aşımı / `KAPIDA_ODEME`'ye ödeme olayı (`N-09, N-10, N-11`, `DURUM-34`)
  3. Rol ve aşama bazlı iptal yasakları (`HAZIRLANIYOR` + `MUSTERI` `N-35`, `KARGODA` + `MUSTERI/OPERATOR` `N-46, N-47`, `TESLIM_EDILEMEDI` + `OPERATOR` `N-70`)
  4. Kargodayken veya açık talep varken iade açma (`N-51, N-101`)
  5. Üç son durumun tamamının (`IPTAL_EDILDI`, `DEPOYA_DONDU`, `IADE_EDILDI`) kilitli kalması (`N-19, N-23, N-87, N-114`)
- **Olay İşleme Önceliği (10.5.1–10.5.4) ve Atomiklik (10.5.5):**
  - `10.5.1` tanımsız olay adı -> `ERR_GECERSIZ_GIRDI` (`DURUM-49`)
  - `10.5.2 > 10.5.3`: `KARGODA` durumunda `IPTAL(aktor=SISTEM)` parametre hatasından önce `ERR_GECERSIZ_GECIS` döner (`DURUM-52`), oysa `ODEME_BEKLENIYOR`/`ONAYLANDI`'da `ERR_GECERSIZ_GIRDI` döner (`DURUM-50, 51`).
  - `10.5.4`: `IADE_RED` sonrasında `gun=15` gönderildiğinde `ERR_IADE_TEKRAR` yerine **`ERR_IADE_SURESI`** döner (`DURUM-28`).
  - `10.5.5` atomiklik (CSV'nin tek-hata son-olay formatı dışında iki adımlı testler):
    - **`ATOM-01`:** `... > TESLIM_BASARISIZ > YENIDEN_DAGITIM > IPTAL(aktor=MUSTERI)` (`ERR_GECERSIZ_GECIS`) ardından `TESLIM_BASARISIZ` -> sayacın hata anında artmadığı ve `DEPOYA_DONDU` yerine `TESLIM_EDILEMEDI` (2. deneme) olduğu doğrulanır.
    - **`ATOM-02`:** `... > TESLIM_BASARILI > IADE_TALEBI(gun=15)` (`ERR_IADE_SURESI`) ardından `IADE_TALEBI(gun=10)` -> hata sonrası reddedilmiş iade bayrağının yanlışlıkla işaretlenmediği ve talebin `KABUL` edildiği doğrulanır.

---

## 6. E2E Ödeme Konfigürasyon Matrisi Yaklaşımı (`DS-005`)

### 6.1 Uzay Analizi ve Maliyet Karşılaştırması
- **Teorik tam çarpım:** `3 (Platform) × 4 (Ödeme) × 3 (Teslimat) × 3 (Üyelik) = 108` kombinasyon (`27 saat`).
- **Kısıtlar (`KS-1`, `KS-2`, `KS-3`) sonrası geçerli kombinasyon:** `27 + 27 + 9 + 12 = 75` geçerli kombinasyon (`18 saat 45 dk`).
- **3-wise (`t=3`):** `39` test (`9 saat 45 dk`) — `REQ-016` orta riskli olduğundan orantısız maliyet.
- **Pairwise (`t=2` + kısıtlar):** **`14` test (`3 saat 30 dk`)** — toplamda **%87,0**, geçerli kümede **%81,3** azalma; kısıtlar altında mümkün olan **59 ikili çiftin %100'ü** kapsanmış ve `pairwise.py` bağımsız doğrulamasından `BAŞARILI` geçmiştir.

### 6.2 Koşulacak E2E Regresyon Kombinasyonları (`konfigurasyon-matrisi.csv`)

| Test ID | Platform | Ödeme Yöntemi | Teslimat Tipi | Üyelik |
|---|---|---|---|---|
| `KONF-01` | `WEB` | `KREDI_KARTI` | `STANDART` | `MISAFIR` |
| `KONF-02` | `WEB` | `BANKA_KARTI` | `HIZLI` | `KLASIK` |
| `KONF-03` | `WEB` | `KAPIDA_ODEME` | `STANDART` | `ALTIN` |
| `KONF-04` | `IOS` | `KREDI_KARTI` | `HIZLI` | `ALTIN` |
| `KONF-05` | `IOS` | `BANKA_KARTI` | `MAGAZA` | `MISAFIR` |
| `KONF-06` | `IOS` | `KAPIDA_ODEME` | `STANDART` | `KLASIK` |
| `KONF-07` | `IOS` | `CEPPAY` | `MAGAZA` | `ALTIN` |
| `KONF-08` | `ANDROID` | `KREDI_KARTI` | `MAGAZA` | `KLASIK` |
| `KONF-09` | `ANDROID` | `BANKA_KARTI` | `STANDART` | `ALTIN` |
| `KONF-10` | `ANDROID` | `KAPIDA_ODEME` | `STANDART` | `MISAFIR` |
| `KONF-11` | `ANDROID` | `CEPPAY` | `HIZLI` | `KLASIK` |
| `KONF-12` | `WEB` | `KREDI_KARTI` | `MAGAZA` | `MISAFIR` |
| `KONF-13` | `IOS` | `CEPPAY` | `STANDART` | `KLASIK` |
| `KONF-14` | `WEB` | `KREDI_KARTI` | `HIZLI` | `MISAFIR` |

- **Ödeme Ekranı Negatif Kısıt Kontrolleri (15 dk tam E2E dışı, hızlı UI doğrulamaları):**
  - `KISIT-01` (`KS-1`): `HIZLI` veya `MAGAZA` seçiliyken `KAPIDA_ODEME` seçilemez.
  - `KISIT-02` (`KS-2`): `WEB` platformunda `CEPPAY` sunulmaz.
  - `KISIT-03` (`KS-3`): `MISAFIR` kullanıcıya `IOS`/`ANDROID` uygulamasında `CEPPAY` sunulmaz.

---

## 7. Spesifikasyonla İlgili Tespitler, Tutarsızlıklar ve Sorular

### 7.1 Kritik Çelişki Tespiti (`Q-001`)
- **Konum:** `Ek-A Örnek 4` (satır 222) ↔ `Bölüm 6.5` (satır 98).
- **Çelişki:** Ek-A Örnek 4 (`KLASIK`, `AT = 900,00`, `STANDART`, `UZAK`, `KREDI_KARTI`) için `KU = 0,00 TL` ve `OT = 900,00 TL` verilmiştir. Oysa Bölüm 6.5 açıkça *"6.2 kapsamındaki ücretsiz standart teslimat bu ek ücreti kapsamaz (ek ücreti yalnızca 6.3 kapsar)"* demektedir. `KLASIK` üye 6.3 (`ALTIN`) kapsamında olmadığından kurala göre **`KU = 25,00 TL`, `OT = 925,00 TL`** olmalıdır.
- **Karar:** Bölüm 215'teki *"Kurallarla çelişki olması halinde Bölüm 4–8'deki kurallar geçerlidir"* hükmü uyarınca `FIYAT-04` testinde **`KU = 25.00`, `OT = 925.00`** beklenmiştir. Geliştiricilerin Ek-A'yı kopyalamasını önlemek için doküman düzeltmesi talep edilmelidir.

### 7.2 Netleştirme Soruları Listesi (`Q-001`–`Q-011`)

| ID | Öncelik | REQ | Tespit / Soru | Seçenekler | Varsayılan (Test Tasarımında Kullanılan) | Muhatap |
|---|---|---|---|---|---|---|
| `Q-001` | **Bloke eden** | `REQ-008` | Ek-A Örnek 4 (`KU=0,00`) ile Kural 6.5 (`KU=25,00`) çelişkisi hangisiyle çözülecek? | a) Kural 6.5 geçerli, Ek-A düzeltilir b) `KLASIK` 750+ muafiyeti eklenir | **(a)** `KU=25.00, OT=925.00` (`FIYAT-04`) | PO, Dev |
| `Q-002` | Önemli | `REQ-016` | E2E matriste `bolge` yer almıyor; `CEPPAY+MAGAZA` kombinasyonu kısıtsız mı? | a) E2E matris `NORMAL` bölgede koşulur, `CEPPAY+MAGAZA` geçerli b) `bolge` eklenir / `CEPPAY+MAGAZA` yasaklanır | **(a)** `NORMAL` bölge ve `CEPPAY+MAGAZA` geçerli (`KONF-07`) | PO, Test Lideri |
| `Q-003` | Önemli | `REQ-005` | Yalnızca boşluklardan oluşan `kupon` (`"   "`) kırpma sonrası kuponsuz (`""`) mı sayılır, `ERR_KUPON_GECERSIZ` mi döner? | a) Kırpma sonrası `""` (`KABUL`) b) `ERR_KUPON_GECERSIZ` | **(a)** Kırpma sonrası kuponsuz (`FIYAT-51`) | PO, Dev |
| `Q-004` | Önemli | `REQ-001` | `"250"`, `"250.5"`, JSON float serileştirme, `"150.000"` ve alan maksimum tipi nedir? | a) 0–2 ondalık kabul, 3+ basamak ret b) Zorunlu 2 ondalık string | **(a)** 0–2 ondalık kabul (`FIYAT-23, 24`), 3+ ret (`FIYAT-18`) | Dev, PO |
| `Q-005` | Önemli | `REQ-002` | `MAGAZA` teslimatta `bolge` alanına tanımsız enum (`"BILINMEYEN"`) gelirse doğrulanmadan geçecek mi? | a) Boş ve tanımsız değer yok sayılır b) Yalnızca boş kabul edilir | **(a)** "doğrulanmaz" gereği yok sayılır (`FIYAT-69`) | Dev, PO |
| `Q-006` | Önemli | `REQ-003` | SFM'de `MISAFIR+CEPPAY` ve `WEB+CEPPAY` serbest (3.3); sipariş oluşturma API'si KS-2/KS-3'ü backend'de engelliyor mu? | a) Sipariş servisi engeller, SFM serbest b) SFM de engeller | **(a)** SFM `KABUL` (`FIYAT-06`), API güvenlik kontrolü önerilir | Security, Dev, PO |
| `Q-007` | Önemli | `REQ-013` | `ODEME_BASARISIZ` için deneme üst limiti var mı; 30 dk `ZAMAN_ASIMI` sıfırlanıyor mu? | a) Sınırsız tekrar, 30 dk sipariş anından b) Limit/sıfırlama var | **(a)** Sınırsız tekrar (`DURUM-12`) | PO, Dev |
| `Q-008` | Önemli | `REQ-013, 014` | `KAPIDA_ODEME` iadesinde geri ödeme kanalı ve `HB=12,90 TL` iade kuralı nedir? `TESLIM_EDILEMEDI`'de operatör iptali neden yok? | a) Geri ödeme/HB ayrı kapsam, `TESLIM_EDILEMEDI` iptali yasak b) `IPTAL(OPERATOR)` eklenir | **(a)** Mevcut tabloya göre `ERR_GECERSIZ_GECIS` (`DURUM-41`) | PO, Ops |
| `Q-009` | Önemli | `REQ-014` | `IADE_RED` sonrası 14 gün yasal cayma süresi bitmeden ikinci `IADE_TALEBI`'nin tamamen bloklanması (`ERR_IADE_TEKRAR`) yasal uyumlu mu? Ayrıca `TESLIM_EDILDI` için kapanış durumu yok mu? | a) Kesin tek iade hakkı b) Belge/neden istisnası ve `TAMAMLANDI` son durumu | **(a)** Mevcut kurala göre tek hak (`DURUM-27`) | PO, Legal |
| `Q-010` | Küçük | `REQ-014` | `IADE_TALEBI(gun=n)` için tamsayı üst limiti var mı? | a) Üst limit yok, `gun > 14` -> `ERR_IADE_SURESI` b) Üst sınır tanımlanır | **(a)** `gun > 14` -> `ERR_IADE_SURESI` (`DURUM-25`) | Dev, PO |
| `Q-011` | Önemli | `REQ-001, 015` | Çift istek / webhook tekrarı (`TESLIM_BASARISIZ` veya fiyatlama) için idempotency ve p95/yetki NFR hedefleri nelerdir? | a) v1.4 kapsam dışı b) `event_id` idempotency ve NFR tanımlanır | **(a)** Fonksiyonel sözleşme test edilir, idempotency riski raporlanır | Dev, PO, Ops |

---

## 8. Varsayımlar, Kalibrasyon İstisnaları ve Kapsam Dışı Bırakılanlar

### 8.1 Varsayımlar
1. Tüm açık sorularda (`Q-001`–`Q-011`) yukarıdaki tabloda belirtilen **Varsayılan** sütunu esas alınmıştır; ilgili test vakaları ekip onayı gelene kadar `draft` statüsünde kalmalıdır.
2. `fiyat-test-verisi.csv` şablonunda `kupon_uygulandi` ayrı kolon olarak yer almadığından, `KI = 0.00` dönen ancak tanımlı kupon koşulunun sağlanmadığı vakalarda (`FIYAT-45, 46, 48, 49`) `kupon_uygulandi=false` beklentisi `aciklama` sütununda belirtilmiş ve `qa/test-cases.src.md` beklenen sonuçlarında korunmuştur.
3. `durum-gecis-testleri.csv` içinde boş `olay_dizisi` yalnızca sipariş oluşturma işlemini temsil ettiğinden `beklenen_son_olay_sonucu = KABUL` olarak kodlanmıştır (`DURUM-01`–`04`).
4. E2E konfigürasyon matrisinde yer alan 14 kombinasyonun her birinin mevcut sepet fiyatlama ve sandbox ödeme akışıyla `NORMAL` bölgede koşulacağı varsayılmıştır.

### 8.2 Kapsam Dışı Bırakılanlar
- **Spesifikasyon §1 gereği kapsam dışı:** Stok rezervasyonu/kontrolü, ürün bazlı kampanyalar, e-arşiv/e-fatura oluşturma, sadakat puanlarının hesaba işlenmesi/harcanması, kargo firması API entegrasyonu ve iade geri ödeme muhasebesi (`HB` iadesi dahil).
- **Risk bazlı tasarım kapsam dışı (bilinçli eleme):**
  - `DS-004` tablosundaki 114 geçersiz geçiş hücresinin **94 simetrik üyesi** (özellikle üç son durumdaki `3 × 13 = 39` hücrenin 35'i ve erken durumlardaki tekrarlayan geçersiz olaylar): her durum için yüksek riskli temsilciler (`DURUM-29`–`48`) seçilerek test şişmesi önlenmiştir.
  - `DS-006`'daki **9 ulaşılamaz alan dışı değer** (`NT < 135.00`, `OT < 147.90`, `OT > 20102.90`, `teslim_deneme < 1` veya `> 3`): giriş kuralları (`AT >= 150.00`) ve son durum kilidi nedeniyle ulaşılamaz olduğundan ayrıca vaka üretilmemiştir.
  - **Fonksiyonel olmayan ve API güvenlik testleri:** Yük/performans (`p95`), eşzamanlı kupon yarışı, IDOR/yetki aşımı (müşterinin `OPERATOR` parametresi göndermesi) ve WCAG 2.2 AA erişilebilirlik kontrolleri (`Q-006`, `Q-011` ile raporlanmıştır).

### 8.3 Kalibrasyon ve Doğrulama Özeti
- **RTM ve Tasarım Kapsamı:** 16/16 gereksinim %100 kapsam; 15/15 fonksiyonel/iş kuralı gereksinimi negatif testli; 0 sahipsiz veya kopya test; 0 şema doğrulama hatası; `review_tests.py` yazım kalitesi puanı **100,0/100**.
- **RTM `REDUNDANT` Kalibrasyon İncelemesi:** `build_rtm.py` aynı `(REQ, polarite, teknik, sonuç)` kalıbını paylaşan grupları (ör. farklı alanların boş/tanımsız olduğu `ERR_GECERSIZ_GIRDI` vakaları `FIYAT-17, 22, 25..33`, farklı başlangıç ödeme yöntemleri `DURUM-01..03`, farklı geçerli geçiş zincirleri `DURUM-05..14`) sezgisel olarak işaretler. Her grup farklı girdi alanı, farklı karar tablosu kolonu (`DS-003 D11/D17/D19`) veya farklı durum geçiş kuralını (`G3`–`G14`) test ettiğinden kasıtlı olarak korunmuştur.
