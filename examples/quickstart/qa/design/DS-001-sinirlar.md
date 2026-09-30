# DS/SDA tasarımı: DS-001 Sayısal sınırlar: şifre uzunluğu, bağlantı süresi, saatlik istek sayısı

REQ: REQ-003, REQ-005, REQ-006 · BVA: 2-value
10 sınıf, 12 sınır değeri, 16 test koşulu

## Denklik sınıfları

| Parametre | Sınıf | Aralık | Geçerli | Temsilci değer |
|---|---|---|---|---|
| sifre_uzunlugu | < 8 | 0 .. 7 | hayır | 3 ('x'×3) |
| sifre_uzunlugu | 8..20 | 8 .. 20 | evet | 14 ('x'×14) |
| sifre_uzunlugu | > 20 | 21 .. ∞ | hayır | 26 ('x'×26) |
| sifre_uzunlugu | boş | - | hayır | boş |
| baglanti_yasi_sn | < 0 | -∞ .. -1 | hayır | -6 |
| baglanti_yasi_sn | 0..1799 | 0 .. 1799 | evet | 899 |
| baglanti_yasi_sn | > 1799 | 1800 .. ∞ | hayır | 1805 |
| istek_sirasi_60dk | < 1 | -∞ .. 0 | hayır | -5 |
| istek_sirasi_60dk | 1..3 | 1 .. 3 | evet | 2 |
| istek_sirasi_60dk | > 3 | 4 .. ∞ | hayır | 9 |

## Sınır değerleri

| Parametre | Değer | Sınıf | Geçerli | Not |
|---|---|---|---|---|
| sifre_uzunlugu | 7 ('x'×7) | < 8 | hayır | sınır < 8 ↔ 8..20 |
| sifre_uzunlugu | 8 ('x'×8) | 8..20 | evet | sınır < 8 ↔ 8..20 |
| sifre_uzunlugu | 20 ('x'×20) | 8..20 | evet | sınır 8..20 ↔ > 20 |
| sifre_uzunlugu | 21 ('x'×21) | > 20 | hayır | sınır 8..20 ↔ > 20 |
| baglanti_yasi_sn | -1 | < 0 | hayır | sınır < 0 ↔ 0..1799 |
| baglanti_yasi_sn | 0 | 0..1799 | evet | sınır < 0 ↔ 0..1799 |
| baglanti_yasi_sn | 1799 | 0..1799 | evet | sınır 0..1799 ↔ > 1799 |
| baglanti_yasi_sn | 1800 | > 1799 | hayır | sınır 0..1799 ↔ > 1799 |
| istek_sirasi_60dk | 0 | < 1 | hayır | sınır < 1 ↔ 1..3 |
| istek_sirasi_60dk | 1 | 1..3 | evet | sınır < 1 ↔ 1..3 |
| istek_sirasi_60dk | 3 | 1..3 | evet | sınır 1..3 ↔ > 3 |
| istek_sirasi_60dk | 4 | > 3 | hayır | sınır 1..3 ↔ > 3 |

## Test koşulları (geçerli değerler birleştirilebilir; her geçersiz değer tek başına test edilir)

| ID | sifre_uzunlugu | baglanti_yasi_sn | istek_sirasi_60dk | Beklenen | Source |
|---|---|---|---|---|---|
| C-01 | 14 ('x'×14) | 899 | 2 | geçerli (kabul) | sifre_uzunlugu: EP: 8..20; baglanti_yasi_sn: EP: 0..1799; istek_sirasi_60dk: EP: 1..3 |
| C-02 | 8 ('x'×8) | 0 | 1 | geçerli (kabul) | sifre_uzunlugu: BVA: sınır < 8 ↔ 8..20; baglanti_yasi_sn: BVA: sınır < 0 ↔ 0..1799; istek_sirasi_60dk: BVA: sınır < 1 ↔ 1..3 |
| C-03 | 20 ('x'×20) | 1799 | 3 | geçerli (kabul) | sifre_uzunlugu: BVA: sınır 8..20 ↔ > 20; baglanti_yasi_sn: BVA: sınır 0..1799 ↔ > 1799; istek_sirasi_60dk: BVA: sınır 1..3 ↔ > 3 |
| C-04 | **3 ('x'×3)** | 899 | 2 | geçersiz (sifre_uzunlugu) | EP: < 8 |
| C-05 | **26 ('x'×26)** | 899 | 2 | geçersiz (sifre_uzunlugu) | EP: > 20 |
| C-06 | **boş** | 899 | 2 | geçersiz (sifre_uzunlugu) | EP: boş |
| C-07 | **7 ('x'×7)** | 899 | 2 | geçersiz (sifre_uzunlugu) | BVA: sınır < 8 ↔ 8..20 |
| C-08 | **21 ('x'×21)** | 899 | 2 | geçersiz (sifre_uzunlugu) | BVA: sınır 8..20 ↔ > 20 |
| C-09 | 14 ('x'×14) | **-6** | 2 | geçersiz (baglanti_yasi_sn) | EP: < 0 |
| C-10 | 14 ('x'×14) | **1805** | 2 | geçersiz (baglanti_yasi_sn) | EP: > 1799 |
| C-11 | 14 ('x'×14) | **-1** | 2 | geçersiz (baglanti_yasi_sn) | BVA: sınır < 0 ↔ 0..1799 |
| C-12 | 14 ('x'×14) | **1800** | 2 | geçersiz (baglanti_yasi_sn) | BVA: sınır 0..1799 ↔ > 1799 |
| C-13 | 14 ('x'×14) | 899 | **-5** | geçersiz (istek_sirasi_60dk) | EP: < 1 |
| C-14 | 14 ('x'×14) | 899 | **9** | geçersiz (istek_sirasi_60dk) | EP: > 3 |
| C-15 | 14 ('x'×14) | 899 | **0** | geçersiz (istek_sirasi_60dk) | BVA: sınır < 1 ↔ 1..3 |
| C-16 | 14 ('x'×14) | 899 | **4** | geçersiz (istek_sirasi_60dk) | BVA: sınır 1..3 ↔ > 3 |
