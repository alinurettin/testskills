# Karar tablosu: DS-002 Yeni şifre kabul kuralları

REQ: REQ-006, REQ-007, REQ-008
Kombinasyon: 32 (olası 32) · kural: 6 · boşluk: 0 · çelişki: 15 · sadeleştirilmiş kolon: 6 · test koşulu: 6

## ⛔ Çelişkiler: aynı kombinasyon için kurallar farklı sonuç veriyor

- K003: uzunluk_8_20=E, buyuk_harf=E, kucuk_harf=E, rakam=H, son_3_sifreden=E :: R5 → sonuc=reddedilir, mesaj=kural; R6 → sonuc=reddedilir, mesaj=son 3 şifre
- K005: uzunluk_8_20=E, buyuk_harf=E, kucuk_harf=H, rakam=E, son_3_sifreden=E :: R4 → sonuc=reddedilir, mesaj=kural; R6 → sonuc=reddedilir, mesaj=son 3 şifre
- K007: uzunluk_8_20=E, buyuk_harf=E, kucuk_harf=H, rakam=H, son_3_sifreden=E :: R4 → sonuc=reddedilir, mesaj=kural; R5 → sonuc=reddedilir, mesaj=kural; R6 → sonuc=reddedilir, mesaj=son 3 şifre
- K009: uzunluk_8_20=E, buyuk_harf=H, kucuk_harf=E, rakam=E, son_3_sifreden=E :: R3 → sonuc=reddedilir, mesaj=kural; R6 → sonuc=reddedilir, mesaj=son 3 şifre
- K011: uzunluk_8_20=E, buyuk_harf=H, kucuk_harf=E, rakam=H, son_3_sifreden=E :: R3 → sonuc=reddedilir, mesaj=kural; R5 → sonuc=reddedilir, mesaj=kural; R6 → sonuc=reddedilir, mesaj=son 3 şifre
- K013: uzunluk_8_20=E, buyuk_harf=H, kucuk_harf=H, rakam=E, son_3_sifreden=E :: R3 → sonuc=reddedilir, mesaj=kural; R4 → sonuc=reddedilir, mesaj=kural; R6 → sonuc=reddedilir, mesaj=son 3 şifre
- K015: uzunluk_8_20=E, buyuk_harf=H, kucuk_harf=H, rakam=H, son_3_sifreden=E :: R3 → sonuc=reddedilir, mesaj=kural; R4 → sonuc=reddedilir, mesaj=kural; R5 → sonuc=reddedilir, mesaj=kural; R6 → sonuc=reddedilir, mesaj=son 3 şifre
- K017: uzunluk_8_20=H, buyuk_harf=E, kucuk_harf=E, rakam=E, son_3_sifreden=E :: R2 → sonuc=reddedilir, mesaj=kural; R6 → sonuc=reddedilir, mesaj=son 3 şifre
- K019: uzunluk_8_20=H, buyuk_harf=E, kucuk_harf=E, rakam=H, son_3_sifreden=E :: R2 → sonuc=reddedilir, mesaj=kural; R5 → sonuc=reddedilir, mesaj=kural; R6 → sonuc=reddedilir, mesaj=son 3 şifre
- K021: uzunluk_8_20=H, buyuk_harf=E, kucuk_harf=H, rakam=E, son_3_sifreden=E :: R2 → sonuc=reddedilir, mesaj=kural; R4 → sonuc=reddedilir, mesaj=kural; R6 → sonuc=reddedilir, mesaj=son 3 şifre
- K023: uzunluk_8_20=H, buyuk_harf=E, kucuk_harf=H, rakam=H, son_3_sifreden=E :: R2 → sonuc=reddedilir, mesaj=kural; R4 → sonuc=reddedilir, mesaj=kural; R5 → sonuc=reddedilir, mesaj=kural; R6 → sonuc=reddedilir, mesaj=son 3 şifre
- K025: uzunluk_8_20=H, buyuk_harf=H, kucuk_harf=E, rakam=E, son_3_sifreden=E :: R2 → sonuc=reddedilir, mesaj=kural; R3 → sonuc=reddedilir, mesaj=kural; R6 → sonuc=reddedilir, mesaj=son 3 şifre
- K027: uzunluk_8_20=H, buyuk_harf=H, kucuk_harf=E, rakam=H, son_3_sifreden=E :: R2 → sonuc=reddedilir, mesaj=kural; R3 → sonuc=reddedilir, mesaj=kural; R5 → sonuc=reddedilir, mesaj=kural; R6 → sonuc=reddedilir, mesaj=son 3 şifre
- K029: uzunluk_8_20=H, buyuk_harf=H, kucuk_harf=H, rakam=E, son_3_sifreden=E :: R2 → sonuc=reddedilir, mesaj=kural; R3 → sonuc=reddedilir, mesaj=kural; R4 → sonuc=reddedilir, mesaj=kural; R6 → sonuc=reddedilir, mesaj=son 3 şifre
- K031: uzunluk_8_20=H, buyuk_harf=H, kucuk_harf=H, rakam=H, son_3_sifreden=E :: R2 → sonuc=reddedilir, mesaj=kural; R3 → sonuc=reddedilir, mesaj=kural; R4 → sonuc=reddedilir, mesaj=kural; R5 → sonuc=reddedilir, mesaj=kural; R6 → sonuc=reddedilir, mesaj=son 3 şifre

## Sadeleştirilmiş karar tablosu

| | D01 | D02 | D03 | D04 | D05 | D06 |
|---|---|---|---|---|---|---|
| **Koşul:** uzunluk_8_20 | - | - | - | E | E | H |
| **Koşul:** buyuk_harf | - | - | H | E | E | E |
| **Koşul:** kucuk_harf | - | H | E | E | E | E |
| **Koşul:** rakam | H | E | E | E | E | E |
| **Koşul:** son_3_sifreden | H | H | H | E | H | H |
| **Aksiyon:** sonuc | reddedilir | reddedilir | reddedilir | reddedilir | kaydedilir | reddedilir |
| **Aksiyon:** mesaj | kural | kural | kural | son 3 şifre | başarı | kural |
| Kural | R2,R3,R4,R5 | R2,R3,R4 | R2,R3 | R6 | R1 | R2 |

## Test koşulları

| ID | Koşul değerleri | Beklenen sonuç | Kolon |
|---|---|---|---|
| C-01 | uzunluk_8_20=E, buyuk_harf=E, kucuk_harf=E, rakam=H, son_3_sifreden=H | sonuc=reddedilir, mesaj=kural | D01 |
| C-02 | uzunluk_8_20=E, buyuk_harf=E, kucuk_harf=H, rakam=E, son_3_sifreden=H | sonuc=reddedilir, mesaj=kural | D02 |
| C-03 | uzunluk_8_20=E, buyuk_harf=H, kucuk_harf=E, rakam=E, son_3_sifreden=H | sonuc=reddedilir, mesaj=kural | D03 |
| C-04 | uzunluk_8_20=E, buyuk_harf=E, kucuk_harf=E, rakam=E, son_3_sifreden=E | sonuc=reddedilir, mesaj=son 3 şifre | D04 |
| C-05 | uzunluk_8_20=E, buyuk_harf=E, kucuk_harf=E, rakam=E, son_3_sifreden=H | sonuc=kaydedilir, mesaj=başarı | D05 |
| C-06 | uzunluk_8_20=H, buyuk_harf=E, kucuk_harf=E, rakam=E, son_3_sifreden=H | sonuc=reddedilir, mesaj=kural | D06 |
