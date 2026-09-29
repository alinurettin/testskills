# Karar tablosu: DS-006 Transfer sonucu: tutar bandı × bakiye × OTP

REQ: REQ-005, REQ-006, REQ-008, REQ-018
Kombinasyon: 18 (olası 8) · kural: 5 · boşluk: 0 · çelişki: 0 · sadeleştirilmiş kolon: 8 · test koşulu: 8

## Sadeleştirilmiş karar tablosu

| | D01 | D02 | D03 | D04 | D05 | D06 | D07 | D08 |
|---|---|---|---|---|---|---|---|---|
| **Koşul:** tutar_bandi | 1-5.000,00 | 1-5.000,00 | 5.000,01-9.999,99 | 5.000,01-9.999,99 | 10.000,00-50.000,00 | 10.000,00-50.000,00 | 10.000,00-50.000,00 | 10.000,00-50.000,00 |
| **Koşul:** bakiye_yeterli | E | H | E | H | E | E | H | H |
| **Koşul:** otp | istenmez | istenmez | istenmez | istenmez | dogru | hatali | dogru | hatali |
| **Aksiyon:** ucret | 0,00 | - | 5,00 | - | 5,00 | - | - | - |
| **Aksiyon:** otp_adimi | hayır | ? | hayır | ? | evet | evet | ? | ? |
| **Aksiyon:** sonuc | başarılı + dekont | red, yetersiz bakiye | başarılı + dekont | red, yetersiz bakiye | başarılı + dekont | red, hata mesajı | red, yetersiz bakiye | red, yetersiz bakiye |
| Kural | R1 | R5 | R2 | R5 | R3 | R4 | R5 | R5 |

## Test koşulları

| ID | Koşul değerleri | Beklenen sonuç | Kolon |
|---|---|---|---|
| C-01 | tutar_bandi=1-5.000,00, bakiye_yeterli=E, otp=istenmez | ucret=0,00, otp_adimi=hayır, sonuc=başarılı + dekont | D01 |
| C-02 | tutar_bandi=1-5.000,00, bakiye_yeterli=H, otp=istenmez | ucret=-, otp_adimi=?, sonuc=red, yetersiz bakiye | D02 |
| C-03 | tutar_bandi=5.000,01-9.999,99, bakiye_yeterli=E, otp=istenmez | ucret=5,00, otp_adimi=hayır, sonuc=başarılı + dekont | D03 |
| C-04 | tutar_bandi=5.000,01-9.999,99, bakiye_yeterli=H, otp=istenmez | ucret=-, otp_adimi=?, sonuc=red, yetersiz bakiye | D04 |
| C-05 | tutar_bandi=10.000,00-50.000,00, bakiye_yeterli=E, otp=dogru | ucret=5,00, otp_adimi=evet, sonuc=başarılı + dekont | D05 |
| C-06 | tutar_bandi=10.000,00-50.000,00, bakiye_yeterli=E, otp=hatali | ucret=-, otp_adimi=evet, sonuc=red, hata mesajı | D06 |
| C-07 | tutar_bandi=10.000,00-50.000,00, bakiye_yeterli=H, otp=dogru | ucret=-, otp_adimi=?, sonuc=red, yetersiz bakiye | D07 |
| C-08 | tutar_bandi=10.000,00-50.000,00, bakiye_yeterli=H, otp=hatali | ucret=-, otp_adimi=?, sonuc=red, yetersiz bakiye | D08 |
