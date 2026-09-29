# DS/SDA tasarımı: DS-001 Transfer tutarı: işlem limitleri, ücret ve OTP eşikleri

REQ: REQ-001, REQ-002, REQ-005, REQ-006 · BVA: 2-value
8 sınıf, 8 sınır değeri, 16 test koşulu

## ⚠ Uyarılar (netleştirilmeli)

- 'tutar' için 1.00 altındaki değerler tanımlanmamış (geçersiz kabul edildi).
- 'tutar' için 50000.00 üstündeki değerler tanımlanmamış (geçersiz kabul edildi).

## Denklik sınıfları

| Parametre | Sınıf | Aralık | Geçerli | Temsilci değer |
|---|---|---|---|---|
| tutar | < 1.00 (tanımsız) | -∞ .. 0.99 | ? | 0.94 |
| tutar | ücretsiz, OTP yok | 1.00 .. 5000.00 | evet | 2500.50 |
| tutar | ücret 5,00 TL, OTP yok | 5000.01 .. 9999.99 | evet | 7500.00 |
| tutar | ücret 5,00 TL, OTP gerekli | 10000.00 .. 50000.00 | evet | 30000.00 |
| tutar | > 50000.00 (tanımsız) | 50000.01 .. ∞ | ? | 50000.06 |
| tutar | boş | - | hayır | boş |
| tutar | sayısal olmayan 'abc' | - | hayır | sayısal olmayan 'abc' |
| tutar | negatif '-100,00' | - | hayır | negatif '-100,00' |

## Sınır değerleri

| Parametre | Değer | Sınıf | Geçerli | Not |
|---|---|---|---|---|
| tutar | 0.99 | < 1.00 (tanımsız) | ? | sınır < 1.00 (tanımsız) ↔ ücretsiz, OTP yok |
| tutar | 1.00 | ücretsiz, OTP yok | evet | sınır < 1.00 (tanımsız) ↔ ücretsiz, OTP yok |
| tutar | 5000.00 | ücretsiz, OTP yok | evet | sınır ücretsiz, OTP yok ↔ ücret 5,00 TL, OTP yok |
| tutar | 5000.01 | ücret 5,00 TL, OTP yok | evet | sınır ücretsiz, OTP yok ↔ ücret 5,00 TL, OTP yok |
| tutar | 9999.99 | ücret 5,00 TL, OTP yok | evet | sınır ücret 5,00 TL, OTP yok ↔ ücret 5,00 TL, OTP gerekli |
| tutar | 10000.00 | ücret 5,00 TL, OTP gerekli | evet | sınır ücret 5,00 TL, OTP yok ↔ ücret 5,00 TL, OTP gerekli |
| tutar | 50000.00 | ücret 5,00 TL, OTP gerekli | evet | sınır ücret 5,00 TL, OTP gerekli ↔ > 50000.00 (tanımsız) |
| tutar | 50000.01 | > 50000.00 (tanımsız) | ? | sınır ücret 5,00 TL, OTP gerekli ↔ > 50000.00 (tanımsız) |

## Test koşulları (geçerli değerler birleştirilebilir; her geçersiz değer tek başına test edilir)

| ID | tutar | Beklenen | Source |
|---|---|---|---|
| C-01 | 2500.50 | geçerli (kabul) | tutar: EP: ücretsiz, OTP yok |
| C-02 | 7500.00 | geçerli (kabul) | tutar: EP: ücret 5,00 TL, OTP yok |
| C-03 | 30000.00 | geçerli (kabul) | tutar: EP: ücret 5,00 TL, OTP gerekli |
| C-04 | 1.00 | geçerli (kabul) | tutar: BVA: sınır < 1.00 (tanımsız) ↔ ücretsiz, OTP yok |
| C-05 | 5000.00 | geçerli (kabul) | tutar: BVA: sınır ücretsiz, OTP yok ↔ ücret 5,00 TL, OTP yok |
| C-06 | 5000.01 | geçerli (kabul) | tutar: BVA: sınır ücretsiz, OTP yok ↔ ücret 5,00 TL, OTP yok |
| C-07 | 9999.99 | geçerli (kabul) | tutar: BVA: sınır ücret 5,00 TL, OTP yok ↔ ücret 5,00 TL, OTP gerekli |
| C-08 | 10000.00 | geçerli (kabul) | tutar: BVA: sınır ücret 5,00 TL, OTP yok ↔ ücret 5,00 TL, OTP gerekli |
| C-09 | 50000.00 | geçerli (kabul) | tutar: BVA: sınır ücret 5,00 TL, OTP gerekli ↔ > 50000.00 (tanımsız) |
| C-10 | **0.94** | ? (tutar) | EP: < 1.00 (tanımsız) |
| C-11 | **50000.06** | ? (tutar) | EP: > 50000.00 (tanımsız) |
| C-12 | **boş** | geçersiz (tutar) | EP: boş |
| C-13 | **sayısal olmayan 'abc'** | geçersiz (tutar) | EP: sayısal olmayan 'abc' |
| C-14 | **negatif '-100,00'** | geçersiz (tutar) | EP: negatif '-100,00' |
| C-15 | **0.99** | ? (tutar) | BVA: sınır < 1.00 (tanımsız) ↔ ücretsiz, OTP yok |
| C-16 | **50000.01** | ? (tutar) | BVA: sınır ücret 5,00 TL, OTP gerekli ↔ > 50000.00 (tanımsız) |
