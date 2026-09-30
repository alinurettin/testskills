# Durum geçişi tasarımı: DS-003 Sıfırlama bağlantısının yaşam döngüsü

REQ: REQ-003, REQ-004, REQ-013
5 durum · 3 olay · 5 geçiş · kapsam: 0-switch · dizi: 3 · geçersiz geçiş adayı: 4

## Durum tablosu (— = tanımlı geçiş yok)

| Durum \ Olay | sıfırlama iste | şifreyi kaydet | 30 dk dolar |
|---|---|---|---|
| **Bağlantı yok** (start) | T1→Geçerli [son 60 dk'da 3'ten az istek] | — | — |
| **Geçerli** | T5→Geçersiz kılındı [son 60 dk'da 3'ten az istek] | T2→Kullanıldı [şifre kurallara uyuyor]<br>T3→Geçerli [şifre kurallara uymuyor] | T4→Süresi doldu |
| **Kullanıldı** (final) | — | — | — |
| **Süresi doldu** (final) | — | — | — |
| **Geçersiz kılındı** (final) | — | — | — |

15 (durum, olay) hücresinden 11 tanesinde geçiş yok

## Geçerli test dizileri (0-switch)

| ID | Yol | Adımlar |
|---|---|---|
| S-01 | Bağlantı yok –sıfırlama iste[son 60 dk'da 3'ten az istek]→ Geçerli –şifreyi kaydet[şifre kurallara uyuyor]→ Kullanıldı | 2 |
| S-02 | Bağlantı yok –sıfırlama iste[son 60 dk'da 3'ten az istek]→ Geçerli –şifreyi kaydet[şifre kurallara uymuyor]→ Geçerli –30 dk dolar→ Süresi doldu | 3 |
| S-03 | Bağlantı yok –sıfırlama iste[son 60 dk'da 3'ten az istek]→ Geçerli –sıfırlama iste[son 60 dk'da 3'ten az istek]→ Geçersiz kılındı | 2 |

## Geçersiz geçiş testleri

| ID | Durum | Olay | Yol | Beklenen |
|---|---|---|---|---|
| N-01 | Bağlantı yok | şifreyi kaydet | (start) | reddedilir / durum değişmez (beklenen davranışı teyit edin) |
| N-02 | Kullanıldı | şifreyi kaydet | T1 → T2 | reddedilir / durum değişmez (beklenen davranışı teyit edin) |
| N-03 | Süresi doldu | şifreyi kaydet | T1 → T4 | reddedilir / durum değişmez (beklenen davranışı teyit edin) |
| N-04 | Geçersiz kılındı | şifreyi kaydet | T1 → T5 | reddedilir / durum değişmez (beklenen davranışı teyit edin) |
