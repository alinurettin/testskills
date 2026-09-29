# Durum geçişi tasarımı: DS-008 Transfer ekran akışı (form, tekrar uyarısı, SMS doğrulama, dekont)

REQ: REQ-005, REQ-011, REQ-012, REQ-018
4 durum · 4 olay · 9 geçiş · kapsam: 0-switch · dizi: 5 · geçersiz geçiş adayı: 12

## Durum tablosu (— = tanımlı geçiş yok)

| Durum \ Olay | Devam | Yine de gönder | Vazgeç | Onayla |
|---|---|---|---|---|
| **Form** (start) | T1→Dekont [geçerli, tutar < 10.000, mükerrer değil]<br>T2→Form [doğrulama hatası]<br>T3→SMS doğrulama [geçerli, tutar ≥ 10.000, mükerrer değil]<br>T4→Tekrar uyarısı [aynı IBAN+tutar, < 60 sn] | — | — | — |
| **Dekont** (final) | — | — | — | — |
| **SMS doğrulama** | — | — | — | T8→Dekont [OTP doğru]<br>T9→SMS doğrulama [OTP hatalı] |
| **Tekrar uyarısı** | — | T5→Dekont [tutar < 10.000]<br>T6→SMS doğrulama [tutar ≥ 10.000] | T7→Form | — |

16 (durum, olay) hücresinden 12 tanesinde geçiş yok

## Geçerli test dizileri (0-switch)

| ID | Yol | Adımlar |
|---|---|---|
| S-01 | Form –Devam[geçerli, tutar < 10.000, mükerrer değil]→ Dekont | 1 |
| S-02 | Form –Devam[doğrulama hatası]→ Form –Devam[geçerli, tutar ≥ 10.000, mükerrer değil]→ SMS doğrulama –Onayla[OTP doğru]→ Dekont | 3 |
| S-03 | Form –Devam[aynı IBAN+tutar, < 60 sn]→ Tekrar uyarısı –Yine de gönder[tutar < 10.000]→ Dekont | 2 |
| S-04 | Form –Devam[aynı IBAN+tutar, < 60 sn]→ Tekrar uyarısı –Yine de gönder[tutar ≥ 10.000]→ SMS doğrulama –Onayla[OTP hatalı]→ SMS doğrulama | 3 |
| S-05 | Form –Devam[aynı IBAN+tutar, < 60 sn]→ Tekrar uyarısı –Vazgeç→ Form | 2 |

## Geçersiz geçiş testleri

| ID | Durum | Olay | Yol | Beklenen |
|---|---|---|---|---|
| N-01 | Form | Yine de gönder | (start) | reddedilir / durum değişmez (beklenen davranışı teyit edin) |
| N-02 | Form | Vazgeç | (start) | reddedilir / durum değişmez (beklenen davranışı teyit edin) |
| N-03 | Form | Onayla | (start) | reddedilir / durum değişmez (beklenen davranışı teyit edin) |
| N-04 | Dekont | Devam | T1 | reddedilir / durum değişmez (beklenen davranışı teyit edin) |
| N-05 | Dekont | Yine de gönder | T1 | reddedilir / durum değişmez (beklenen davranışı teyit edin) |
| N-06 | Dekont | Vazgeç | T1 | reddedilir / durum değişmez (beklenen davranışı teyit edin) |
| N-07 | Dekont | Onayla | T1 | reddedilir / durum değişmez (beklenen davranışı teyit edin) |
| N-08 | SMS doğrulama | Devam | T3 | reddedilir / durum değişmez (beklenen davranışı teyit edin) |
| N-09 | SMS doğrulama | Yine de gönder | T3 | reddedilir / durum değişmez (beklenen davranışı teyit edin) |
| N-10 | SMS doğrulama | Vazgeç | T3 | reddedilir / durum değişmez (beklenen davranışı teyit edin) |
| N-11 | Tekrar uyarısı | Devam | T4 | reddedilir / durum değişmez (beklenen davranışı teyit edin) |
| N-12 | Tekrar uyarısı | Onayla | T4 | reddedilir / durum değişmez (beklenen davranışı teyit edin) |
