# Veri göçü mutabakatı

**Karar: FAIL**

## Onay kuralları
| Kural | Değer | Eşik | Sonuç |
|---|---:|---:|:---:|
| Anahtarı boş satırlar | 0 | 0 | ✅ |
| Kaynakta mükerrer anahtar | 0 | 0 | ✅ |
| Hedefte mükerrer anahtar | 1 | 0 | ❌ |
| Hedefte eksik | 1 | 0 | ❌ |
| Hedefte beklenmeyen | 1 | 0 | ❌ |
| Alan uyuşmazlıkları (dönüşüm hataları dahil) | 6 | 0 | ❌ |
| Toleransı aşan kontrol toplamı farkları | 4 | 0 | ❌ |
| Hedef dosyada olmayan eşlenmiş hedef kolonlar | 0 | 0 | ✅ |
| Eşleme kararı olmayan kaynak kolonlar | 0 | 0 | ✅ |

## Girdiler
| | Dosya | Kodlama | Ayraç | Satır | Tekil anahtar |
|---|---|---|---|---:|---:|
| Kaynak | `data/legacy_customers.csv` | cp1254 | `;` | 40 | 40 |
| Hedef | `data/new_customers.csv` | utf-8-sig | `,` | 41 | 40 |

Anahtar: `customer_id` · Eşleşen anahtar: 39 · ∅ = boş. Değerler olduğu gibi gösterilir; metin tam eşitlikle, sayılar 0 toleransla karşılaştırılır.

## Eşleme kapsamı
- Hedefi de 'taşınmayacak' kararı da olmayan kaynak kolonlar: yok
- Açıkça taşınmayan kaynak kolonlar: `FAKS`
- Örtük aynı-ad eşlemeleri (eşleme spesifikasyonunda teyit edin): yok
- Hedef dosyada olmayan eşlenmiş hedef kolonlar: yok
- Eşlemesi olmayan hedef kolonlar (karşılaştırılmadı): yok
- Yok sayılan hedef kolonlar: yok

## Anahtar mutabakatı

### Kaynakta mükerrer anahtarlar (0)

### Hedefte mükerrer anahtarlar (1)
`1035` ×2

### Hedefte eksik (kaynakta var, hedefte yok) (1)
`1017`

### Hedefte beklenmeyen (hedefte var, kaynakta yok) (1)
`9001`

## Alan düzeyinde karşılaştırma
| Kolon | Kural | Karşılaştırılan | Uyuşmazlık | Dönüşüm hatası | Kabul edilen |
|---|---|---:|---:|---:|---:|
| `full_name` | `AD + SOYAD` concat → collapse_spaces → upper_tr | 39 | 2 | 0 | 0 |
| `birth_date` | `DOGUM_TARIHI` trim → date | 39 | 1 | 0 | 0 |
| `branch` | `SUBE_KODU` trim → map | 39 | 0 | 0 | 0 |
| `balance` | `BAKIYE` trim → decimal | 39 | 2 | 0 | 0 |
| `status` | `DURUM` trim → map | 39 | 1 | 0 | 0 |
| `email` | `EPOSTA` trim → lower | 39 | 0 | 0 | 0 |

### `full_name` – Örnekler (2/2)
| Anahtar | Kaynak değer | Beklenen (dönüştürülmüş) | Hedef değer | İpucu |
|---|---|---|---|---|
| `1004` | `İbrahim + Şahin` | `İBRAHİM ŞAHİN` | `Ä°BRAHÄ°M ÅžAHÄ°N` | kodlama: utf-8 metin cp1252 olarak okunmuş (bozuk karakter) |
| `1022` | `Gülşen + Işık` | `GÜLŞEN IŞIK` | `GÜLÞEN IÞIK` | kodlama: cp1254 metin cp1252 olarak okunmuş (bozuk karakter) |

### `birth_date` – Örnekler (1/1)
| Anahtar | Kaynak değer | Beklenen (dönüştürülmüş) | Hedef değer | İpucu |
|---|---|---|---|---|
| `1012` | `05.03.1990` | `1990-03-05` | `1990-05-03` | gün/ay yer değiştirmiş |

### `balance` – Örnekler (2/2)
| Anahtar | Kaynak değer | Beklenen (dönüştürülmüş) | Hedef değer | İpucu |
|---|---|---|---|---|
| `1009` | `4.350,57` | `4350.57` | `4350.56` | yuvarlama farkı (-0.01) |
| `1031` | `3.456,78` | `3456.78` | `345678.00` | ×100: ondalık ayracı kaybolmuş |

### `status` – Örnekler (1/1)
| Anahtar | Kaynak değer | Beklenen (dönüştürülmüş) | Hedef değer | İpucu |
|---|---|---|---|---|
| `1027` | `K` | `CLOSED` | `PASSIVE` | geçerli kod, ama başka bir kaynak kodun eşlemesi |

## Kontrol toplamları

### `balance`
| Grup | Kaynak | Hedef | Fark | Sonuç |
|---|---:|---:|---:|:---:|
| (tüm satırlar) | 1689826.46 | 2024947.67 | 335121.21 | ❌ |
| `ANK` | 178065.73 | 170965.73 | -7100.00 | ❌ |
| `IST` | 1461886.36 | 1804107.58 | 342221.22 | ❌ |
| `IZM` | 49874.37 | 49874.36 | -0.01 | ❌ |

### Adet – `branch`
| Grup | Kaynak | Hedef | Fark |
|---|---:|---:|---:|
| `ANK` | 13 | 13 | 0 |
| `IST` | 14 | 15 | +1 |
| `IZM` | 13 | 13 | 0 |

## Boş değer oranları
| Kolon | Beklenen boş % | Hedef boş % | Değişim (puan) |
|---|---:|---:|---:|
| `full_name` | 0.0 | 0.0 | 0 |
| `birth_date` | 0.0 | 0.0 | 0 |
| `branch` | 0.0 | 0.0 | 0 |
| `balance` | 0.0 | 0.0 | 0 |
| `status` | 0.0 | 0.0 | 0 |
| `email` | 2.5 | 2.44 | -0.06 |

## Hata sınıflandırma rehberi
- Dönüşüm hataları ve 'eşlemede yok' kodları: **kaynak veri kalitesi** (profille ve temizle) ya da **eşleme spesifikasyonu boşluğu** (kural bu değeri kapsamıyor).
- Karakter bozulması/kodlama ipuçlu uyuşmazlık: **çıkarma veya yükleme hatası** (yanlış kod sayfası), veri sahibinin sorunu değil.
- Kural biçimli ipucu (×100, gün/ay yer değiştirmesi, yuvarlama, harf büyüklüğü, yanlış kod): **dönüşüm hatası**.
- Eksik/beklenmeyen/mükerrer anahtar: **yükleme hatası** (reddedilen kayıt, filtre, idempotent olmayan tekrar çalıştırma) ya da spesifikasyonda **kapsam boşluğu** (test/kapalı kayıtlar).
- Satır bulgusu olmadan kontrol toplamı farkı: karşılaştırma kapsamından veya toplam sorgusundan şüphelenin; satır bulgusu varsa fark onun sonucudur, satır düzeyindeki nedeni raporlayın.
