# PoliçeNova Veri Göçü — Poliçe ve Taksit Eşleme Spesifikasyonu

| | |
|---|---|
| Belge no | KYS-MIG-SPEC-014 |
| Sürüm | 1.3 (onaylı) — 15.09.2026 |
| Sahibi | Kuzeyyıldız Sigorta A.Ş. — Veri Göçü Çalışma Grubu |
| Kaynak sistem | SİGMA/400 (eski çekirdek sigorta sistemi) |
| Hedef sistem | PoliçeNova |

**Sürüm geçmişi**

| Sürüm | Tarih | Değişiklik |
|---|---|---|
| 1.0 | 12.06.2026 | İlk sürüm |
| 1.1 | 08.07.2026 | Acente kod tablosu eklendi (bölüm 5.4) |
| 1.2 | 19.08.2026 | `premium_try` ve `fx_rate` alanları eklendi; teklif kayıtları kapsam dışına alındı |
| 1.3 | 15.09.2026 | `end_date` tanımı netleştirildi; 5.5 ödeme durumu kuralında takvim günü tanımı netleştirildi |

---

## 1. Amaç ve kapsam

Bu belge, SİGMA/400'deki poliçe (`POLMAS`) ve taksit (`TAKSIT`) kayıtlarının PoliçeNova'daki `policies` ve `installments` tablolarına dönüşüm kurallarını tanımlar. Göç doğrulaması için tek referans bu belgedir.

- **Kesim tarihi:** 30.09.2026 (Europe/Istanbul).
- **Kapsam:** `DURUM_KD` değeri `A`, `I`, `S` veya `Y` olan poliçeler ve bu poliçelere ait **tüm** `TAKSIT` satırları (normal ve iade taksitleri).
- **Kapsam dışı:** `DURUM_KD = B` (teklif) kayıtları. Teklifler poliçe değildir; ne teklif kaydı ne de teklife ait `TAKSIT` satırları taşınır.

## 2. Dosya biçimleri

### 2.1 Kaynak (SİGMA/400 dışa aktarımı)

- Karakter kodlaması **Windows-1254**, alan ayracı `;`, ilk satır başlık, satır sonu CRLF. Ayraç içeren alanlar çift tırnak (`"`) içinde verilir.
- Sayılar: ondalık ayraç virgül, binlik ayraç nokta (ör. `12.450,75`). **Negatif tutarlar AS/400 biçiminde sonda eksi ile yazılır** (ör. `1.250,00-` = −1250,00).
- `KUR` 4 ondalıklıdır (ör. `34,1287`).
- Tarih biçimi alana göre değişir (bkz. bölüm 3 ve 4): `gg.aa.yyyy` veya `gg/aa/yyyy`.
- Zaman damgaları (`SON_ISLEM_ZMN`, `ODEME_ZMN`) **Türkiye yerel saatidir** (Europe/Istanbul, sabit UTC+03:00; yaz saati uygulaması yoktur).
- `SIGORTALI_ADI` sabit uzunluklu (CHAR(40)) bir alandır ve sağdan boşlukla doldurulmuştur.

### 2.2 Hedef (PoliçeNova dışa aktarımı)

- Karakter kodlaması **UTF-8** (BOM yok), alan ayracı `,`, ilk satır başlık, RFC 4180 tırnaklama.
- Ondalık ayraç nokta, binlik ayraç yok. Tutarlar 2, kurlar 4 ondalıklı yazılır. Negatif tutarlar başta eksi ile yazılır (ör. `-1250.00`).
- Tarihler `YYYY-AA-GG` (ISO 8601).
- Zaman damgaları **UTC**, ISO 8601, `Z` son ekli (ör. `2026-03-14T09:05:00Z`).
- Boş alan NULL anlamına gelir.
- Tüm metin alanlarında Türkçe karakterler (ç, ğ, ı, İ, ö, ş, ü ve büyük harfleri) **olduğu gibi korunur**; harf dönüşümü veya büyük/küçük harf değişikliği yapılmaz. Metin alanlarının baş ve sonundaki boşluklar kırpılır (trim).

## 3. `POLMAS` → `policies`

| Hedef alan | Tip | Kaynak alan | Kural |
|---|---|---|---|
| `policy_id` | varchar(20) | `POL_NO` | `'KYS-' + POL_NO` (birincil anahtar) |
| `legacy_policy_no` | varchar(10) | `POL_NO` | Aynen |
| `customer_no` | int | `MUST_NO` | Aynen |
| `insured_name` | varchar(100) | `SIGORTALI_ADI` | Trim; aksi halde aynen |
| `product_code` | varchar(30) | `URUN_KD` | Tablo 5.2 |
| `status` | varchar(12) | `DURUM_KD` | Tablo 5.1 |
| `start_date` | date | `BAS_TAR` (`gg.aa.yyyy`) | ISO tarihe çevrilir |
| `end_date` | date | `BIT_TAR` (`gg/aa/yyyy`) | **`BIT_TAR − 1 gün`**. SİGMA/400'de `BIT_TAR` poliçenin öğlen 12:00'de sona erdiği gündür; PoliçeNova'da `end_date` teminatın tam gün geçerli olduğu son gündür (ör. `BIT_TAR = 15/03/2026` → `end_date = 2026-03-14`) |
| `currency` | char(3) | `DOVIZ` | Tablo 5.3 |
| `gross_premium` | decimal(14,2) | `BRUT_PRIM` | Aynen (poliçe para birimi cinsinden; iade zeyilleri düşülmüş güncel brüt prim) |
| `fx_rate` | decimal(10,4) | `KUR` | Aynen, 4 ondalık. `KUR` boş ve `currency = TRY` ise `1.0000` |
| `premium_try` | decimal(14,2) | hesaplanan | `ROUND_HALF_UP(gross_premium × fx_rate, 2)` |
| `installment_count` | int | `TAKSIT_SAY` | Aynen (yalnızca normal taksit sayısı; iade taksitleri sayılmaz) |
| `agency_code` | varchar(10) | `ACENTE_KD` | Tablo 5.4 |
| `city` | varchar(40) | `IL` | Trim; aksi halde aynen |
| `address_line` | varchar(250) | `ADRES` | Trim; aksi halde aynen (kısaltma yapılmaz) |
| `loss_payee` | varchar(120) | `DAIN_MURTEHIN` | Trim; aksi halde aynen. Boşsa NULL |
| `cancel_date` | date | `IPTAL_TAR` (`gg.aa.yyyy`) | ISO tarihe çevrilir. **Boşsa NULL** |
| `updated_at` | timestamp (UTC) | `SON_ISLEM_ZMN` (`gg.aa.yyyy SS:dd:ss`, yerel) | Yerel saatten UTC'ye çevrilir |
| `migration_run_id` | varchar(4) | — | ETL çalıştırma kimliği (yalnızca izlenebilirlik) |

## 4. `TAKSIT` → `installments`

| Hedef alan | Tip | Kaynak alan | Kural |
|---|---|---|---|
| `installment_id` | varchar(12) | — | ETL'in ürettiği vekil anahtar (`INS-` + sıra no); kaynakla karşılaştırılmaz |
| `policy_id` | varchar(20) | `POL_NO` | `'KYS-' + POL_NO`; `policies.policy_id`'ye yabancı anahtar |
| `installment_no` | int | `TAKSIT_NO` | Aynen. (`policy_id`, `installment_no`) **benzersizdir** |
| `installment_type` | varchar(10) | `TAKSIT_TIP` | `N` → `REGULAR`, `Z` (zeyil iadesi) → `REFUND` |
| `due_date` | date | `VADE_TAR` (`gg.aa.yyyy`) | ISO tarihe çevrilir |
| `amount` | decimal(14,2) | `TUTAR` | Aynen, **işaret korunur** (iade taksitleri negatiftir) |
| `currency` | char(3) | — | İlgili poliçenin `currency` değeri |
| `paid_amount` | decimal(14,2) | `ODENEN_TUTAR` | Aynen, işaret korunur. Boşsa NULL |
| `paid_at` | timestamp (UTC) | `ODEME_ZMN` (`gg/aa/yyyy SS:dd`, yerel) | Yerel saatten UTC'ye çevrilir. Boşsa NULL |
| `payment_status` | varchar(16) | hesaplanan | Kural 5.5 |
| `migration_run_id` | varchar(4) | — | ETL çalıştırma kimliği (yalnızca izlenebilirlik) |

## 5. Kod tabloları ve hesaplama kuralları

### 5.1 Poliçe durumu (`DURUM_KD` → `status`)

| SİGMA/400 | Anlamı | PoliçeNova |
|---|---|---|
| `A` | Yürürlükte | `ACTIVE` |
| `I` | İptal | `CANCELLED` |
| `S` | Süresi doldu | `EXPIRED` |
| `Y` | Yenilendi | `RENEWED` |
| `B` | Teklif | taşınmaz (kapsam dışı) |

### 5.2 Ürün (`URUN_KD` → `product_code`)

| SİGMA/400 | Ürün | PoliçeNova |
|---|---|---|
| `KSK` | Kasko | `MOTOR_OWN_DAMAGE` |
| `TRF` | Zorunlu Trafik | `MOTOR_TPL` |
| `KNT` | Konut | `HOME` |
| `ISY` | İşyeri | `COMMERCIAL_PROPERTY` |
| `FKZ` | Ferdi Kaza | `PERSONAL_ACCIDENT` |
| `SYH` | Seyahat Sağlık | `TRAVEL_HEALTH` |

### 5.3 Döviz (`DOVIZ` → `currency`)

| SİGMA/400 | PoliçeNova | Not |
|---|---|---|
| `TL` | `TRY` | |
| *(boş)* | `TRY` | `DOVIZ` alanı Ocak 2025'te eklendi; daha eski poliçelerde boştur ve TL'dir |
| `USD` | `USD` | |
| `EUR` | `EUR` | |

### 5.4 Acente (`ACENTE_KD` → `agency_code`)

| SİGMA/400 | PoliçeNova | Acente unvanı |
|---|---|---|
| `A01` | `ACN-3401` | Boğaziçi Anadolu Sigorta Aracılık Ltd. Şti. |
| `A02` | `ACN-3402` | Haliç Güvence Acentelik A.Ş. |
| `A03` | `ACN-0601` | Başkent Kalkan Sigorta Aracılık Ltd. Şti. |
| `A04` | `ACN-3501` | Ege Körfez Sigorta Acentesi Ltd. Şti. |
| `A05` | `ACN-1601` | Uludağ Teminat Aracılık A.Ş. |
| `A06` | `ACN-0701` | Akdeniz Liman Sigorta Ltd. Şti. |
| `A07` | `ACN-4201` | Selçuklu Güven Sigorta Aracılık Ltd. Şti. |
| `A08` | `ACN-2701` | Zeugma Risk Danışmanlık A.Ş. |
| `A09` | `ACN-3502` | Kordon Sigorta Acentesi Ltd. Şti. |
| `A10` | `ACN-6101` | Karadeniz Dalga Sigorta Aracılık A.Ş. |

### 5.5 Ödeme durumu (`payment_status`)

Sırasıyla uygulanır:

1. `installment_type = REFUND` ise: `ODEME_ZMN` doluysa `REFUNDED`, boşsa `REFUND_PENDING`.
2. `installment_type = REGULAR` ve `ODEME_ZMN` dolu ise: ödemenin yapıldığı **Türkiye yerel takvim günü** (Europe/Istanbul) `due_date` ile aynı gün veya daha önce ise `PAID_ON_TIME`, sonra ise `PAID_LATE`.
3. `installment_type = REGULAR` ve `ODEME_ZMN` boş ise: `due_date < 2026-09-30` ise `OVERDUE`, aksi halde `OPEN`.

## 6. Bütünlük ve mutabakat kuralları

| No | Kural |
|---|---|
| M1 | Kapsamdaki her `POLMAS` kaydı `policies` içinde **tam bir kez** bulunur; kapsam dışı veya kaynağı olmayan kayıt bulunmaz. |
| M2 | Kapsamdaki her `TAKSIT` kaydı `installments` içinde **tam bir kez** bulunur; (`policy_id`, `installment_no`) benzersizdir. |
| M3 | Her `installments.policy_id` değeri `policies` içinde mevcuttur (yetim taksit olamaz). |
| M4 | Her poliçe için `gross_premium = Σ installments.amount` (iade taksitleri dahil). Kaynakta `BRUT_PRIM = Σ TUTAR` eşitliği kapsamdaki her poliçe için sağlanmaktadır. |
| M5 | `installment_count` = poliçenin `REGULAR` taksit sayısı. |
| M6 | Para birimi bazında ve **acente bazında** `gross_premium` toplamları kaynakla birebir tutar (acente komisyon hakedişleri bu toplamlardan hesaplanır). |
| M7 | Bölüm 3–5'teki alan kurallarının tamamı kayıt bazında sağlanır. `installment_id` ve `migration_run_id` karşılaştırma dışıdır. |
