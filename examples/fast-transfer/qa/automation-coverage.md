# Automation coverage

- Automation candidates: 46
- Automated (implemented): 46 (100.0%)
- Skeletons still to implement: 0
- Missing (candidate without spec): 0
- Orphan spec tags: 0 · duplicate tags: 0 · automated non-candidates: 0

## Automated

| TC | Title | Priority | Location |
|---|---|---|---|
| TC-001 | 1,00 TL (alt sınır) transfer ücretsiz gerçekleşir ve dekont gösterilir | medium | req-001-islem-basina-asgari-tutar-1-00-tl.spec.ts:8 |
| TC-002 | 0,99 TL (alt sınırın altı) reddedilir | medium | req-001-islem-basina-asgari-tutar-1-00-tl.spec.ts:31 |
| TC-003 | 50.000,00 TL (işlem üst sınırı) SMS doğrulama ile gerçekleşir | high | req-002-islem-basina-azami-tutar-50-000-00-tl.spec.ts:8 |
| TC-004 | 50.000,01 TL (işlem üst sınırının üstü) reddedilir | high | req-002-islem-basina-azami-tutar-50-000-00-tl.spec.ts:30 |
| TC-005 | Günlük toplam tam 100.000,00 TL'ye ulaşan transfer kabul edilir | high | req-003-gunluk-fast-limiti-100-000-00-tl-kumulat.spec.ts:16 |
| TC-006 | Günlük toplamı 100.000,01 TL'ye çıkaracak transfer reddedilir | critical | req-003-gunluk-fast-limiti-100-000-00-tl-kumulat.spec.ts:32 |
| TC-007 | Günlük toplamı 99.999,99 TL'ye çıkaran transfer kabul edilir | medium | req-003-gunluk-fast-limiti-100-000-00-tl-kumulat.spec.ts:49 |
| TC-008 | Günlük limit dolduktan sonra 1,00 TL transfer reddedilir | high | req-003-gunluk-fast-limiti-100-000-00-tl-kumulat.spec.ts:64 |
| TC-009 | Reddedilen transfer bakiyeyi ve günlük limiti tüketmez | medium | req-016-basarili-transfer-bakiyeden-tutar-ucreti.spec.ts:8 |
| TC-010 | Kontrol basamağı hatalı (mod-97) IBAN reddedilir | high | req-004-alici-iban-dogrulamasi-tr-26-karakter-mo.spec.ts:43 |
| TC-011 | 25 karakterlik IBAN reddedilir | medium | req-004-alici-iban-dogrulamasi-tr-26-karakter-mo.spec.ts:13 |
| TC-012 | 27 karakterlik IBAN reddedilir | medium | req-004-alici-iban-dogrulamasi-tr-26-karakter-mo.spec.ts:20 |
| TC-013 | TR dışı ülke kodlu IBAN reddedilir | medium | req-004-alici-iban-dogrulamasi-tr-26-karakter-mo.spec.ts:27 |
| TC-014 | Boş IBAN reddedilir | low | req-004-alici-iban-dogrulamasi-tr-26-karakter-mo.spec.ts:59 |
| TC-015 | Boşluklu ve küçük harfli geçerli IBAN kabul edilir | low | req-004-alici-iban-dogrulamasi-tr-26-karakter-mo.spec.ts:70 |
| TC-016 | 10.000,00 TL'de (OTP eşiği, dahil) SMS doğrulama istenir | high | req-005-10-000-00-tl-ve-uzeri-transferlerde-sms.spec.ts:8 |
| TC-017 | 9.999,99 TL'de OTP istenmez, 5,00 TL ücret alınır | medium | req-005-10-000-00-tl-ve-uzeri-transferlerde-sms.spec.ts:30 |
| TC-018 | Hatalı SMS kodu ile transfer yapılmaz | high | req-018-hatali-otp-ile-transfer-yapilmaz.spec.ts:8 |
| TC-019 | SMS adımı açıkken değiştirilen tutar OTP ile onaylanamaz | high | req-018-hatali-otp-ile-transfer-yapilmaz.spec.ts:27 |
| TC-020 | 5.000,00 TL'de (ücret eşiği) ücret alınmaz | high | req-006-5-000-00-tl-yi-asan-transferlerde-5-00-t.spec.ts:8 |
| TC-021 | 5.000,01 TL'de 5,00 TL ücret alınır; bakiye ve limit doğru düşer | high | req-006-5-000-00-tl-yi-asan-transferlerde-5-00-t.spec.ts:26 |
| TC-022 | Tutar + ücret bakiyeye tam eşitse transfer gerçekleşir | medium | req-008-yetersiz-bakiyede-tutar-ucret-transfer-y.spec.ts:20 |
| TC-023 | Tutar bakiyeye sığıp tutar + ücret bakiyeyi 0,01 TL aşarsa transfer yapılmaz | high | req-008-yetersiz-bakiyede-tutar-ucret-transfer-y.spec.ts:38 |
| TC-024 | Tutar bakiyeyi aşarsa SMS gönderilmeden reddedilir | medium | req-008-yetersiz-bakiyede-tutar-ucret-transfer-y.spec.ts:56 |
| TC-025 | Boş açıklama ile transfer reddedilir | low | req-009-aciklama-alani-zorunludur.spec.ts:8 |
| TC-026 | Yalnız boşluktan oluşan açıklama reddedilir | low | req-009-aciklama-alani-zorunludur.spec.ts:19 |
| TC-027 | Türkçe karakterli 50 karakterlik açıklama kabul edilir ve dekontta tam görünür | low | req-010-aciklama-en-fazla-50-karakter.spec.ts:11 |
| TC-028 | 51 karakterlik açıklama ile transfer yapılmaz | low | req-010-aciklama-en-fazla-50-karakter.spec.ts:25 |
| TC-029 | 60 sn içinde aynı IBAN ve tutara ikinci transferde uyarı; 'Vazgeç' transferi durdurur | high | req-011-60-saniye-icinde-ayni-aliciya-ayni-tutar.spec.ts:20 |
| TC-030 | Tekrar uyarısında 'Yine de gönder' ikinci transferi gerçekleştirir | medium | req-011-60-saniye-icinde-ayni-aliciya-ayni-tutar.spec.ts:38 |
| TC-031 | Önceki transferden 59 sn sonra aynı IBAN ve tutarda uyarı gösterilir | medium | req-011-60-saniye-icinde-ayni-aliciya-ayni-tutar.spec.ts:55 |
| TC-032 | Önceki transferden 60 sn sonra aynı IBAN ve tutarda uyarı gösterilmez | medium | req-011-60-saniye-icinde-ayni-aliciya-ayni-tutar.spec.ts:70 |
| TC-033 | Aynı IBAN'a farklı tutarda 60 sn içinde transferde uyarı gösterilmez | medium | req-011-60-saniye-icinde-ayni-aliciya-ayni-tutar.spec.ts:86 |
| TC-034 | Aynı IBAN boşluklu yazılsa da 60 sn içinde uyarı gösterilir | medium | req-011-60-saniye-icinde-ayni-aliciya-ayni-tutar.spec.ts:100 |
| TC-035 | Tekrar uyarısı sonrası ≥ 10.000,00 TL transfer yine SMS doğrulaması ister | medium | req-011-60-saniye-icinde-ayni-aliciya-ayni-tutar.spec.ts:113 |
| TC-036 | Sonuç ekranı ve dekont onaydan sonra 3 sn içinde görünür | medium | req-013-transfer-hizli-gerceklesmeli-performans.spec.ts:9 |
| TC-037 | Pazar 23:30'da (mesai dışı) transfer gerçekleşir | medium | req-014-7-24-calisma-mesai-disi.spec.ts:8 |
| TC-038 | Kayıtlı alıcı listeden seçilerek transfer yapılır | medium | req-015-kayitli-aliciya-transfer.spec.ts:8 |
| TC-039 | 'Devam'a çift tıklama tek transfer oluşturur | high | req-017-mukerrer-gonderim-cift-tiklama-tek-trans.spec.ts:8 |
| TC-040 | '1.000,50' biçimli tutar doğru ayrıştırılır | high | req-019-tutar-bicimi-ve-gecersiz-tutar-girisi.spec.ts:8 |
| TC-041 | Sayısal olmayan tutar reddedilir | medium | req-019-tutar-bicimi-ve-gecersiz-tutar-girisi.spec.ts:24 |
| TC-042 | İkiden fazla ondalık basamaklı tutar reddedilir | medium | req-019-tutar-bicimi-ve-gecersiz-tutar-girisi.spec.ts:26 |
| TC-043 | Negatif tutar reddedilir | medium | req-001-islem-basina-asgari-tutar-1-00-tl.spec.ts:45 |
| TC-044 | Boş tutar reddedilir | low | req-019-tutar-bicimi-ve-gecersiz-tutar-girisi.spec.ts:28 |
| TC-045 | Nokta ondalık ayırıcılı '100.50' tutarı 10.050 TL olarak işlenmez | high | req-019-tutar-bicimi-ve-gecersiz-tutar-girisi.spec.ts:46 |
| TC-047 | Virgülsüz TR binlik biçimli '15.000' tutarı 15,00 TL olarak gönderilmez | high | req-019-tutar-bicimi-ve-gecersiz-tutar-girisi.spec.ts:60 |

