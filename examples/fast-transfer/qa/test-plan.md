# Test Planı (hafif): US-310 FAST ile para transferi (BANK-310)

| | |
|---|---|
| Sürüm | 1 · 2026-09-29 |
| Sorumlu | QA (QA Suite ile hazırlandı) |
| Onaylayanlar | {{PO, geliştirme lideri — onaylanacak}} |
| İlgili | qa/requirements.json · qa/test-cases.json · qa/rtm.md · qa/exit-criteria.json · qa/clarifications.md |

## 1. Bağlam ve hedefler
- Bireysel müşterinin web arayüzünden FAST ile yeni IBAN'a anlık TL transferi (US-310).
- Test şunları kanıtlamalı: işlem ve günlük limitler (AK-1, AK-2), IBAN doğrulaması (AK-3), SMS OTP eşiği (AK-4), ücret ve dekont (AK-5, AK-9), bakiye kontrolü (AK-6), açıklama kuralları (AK-7), mükerrer uyarısı (AK-8).

## 2. Kapsam
- **Kapsam içi:** REQ-001 … REQ-019 (19 gereksinim; 4'ü türetilmiş, onay bekliyor).
- **Kapsam dışı:** AK-10 döviz hesaplarından FAST (Q-001, bloke eden, "belirlenecek"); mobil uygulama (test ortamı yalnız web); yük/performans testi (hedef tanımsız, Q-008; uygulama istemci tarafında çalışıyor, test edilebilir API yok); günlük limitin gün değişiminde sıfırlanması (ortam her oturumda sıfırlıyor; kalıcı kullanım + saat kontrolü gerekir).
- **Test nesnesi:** http://localhost:4174 (demo-app, test ortamı), Chromium.

## 3. Risk kaydı (plan_facts.py)
| Risk | REQ | Seviye (O×E) | Test ile azaltma |
|---|---|---|---|
| Günlük limitin kümülatif uygulanmaması | REQ-003 | kritik (4×5=20) | 3-değer SDA (DS-002), TC-005…TC-008, otomasyon |
| Mükerrer ödeme | REQ-011, REQ-017 | yüksek (16, 15) | Karar tablosu + saat kontrollü SDA (DS-005/007), çift tıklama |
| OTP (SCA) atlatılması | REQ-005, REQ-018 | yüksek (15) | SDA 9.999,99/10.000,00, hatalı OTP, OTP adımında tutar değişimi |
| Ücretin bakiye kontrolüne katılmaması | REQ-008 | yüksek (15) | DS-004 SDA (tutar+ücret = bakiye ± 0,01) |
| Bakiye/limit tutarsızlığı | REQ-016 | yüksek (15) | Her para testinde bakiye ve kalan limit doğrulaması |

## 4. Test yaklaşımı
- **Seviye:** sistem testi (UI, kara kutu).
- **Teknikler (riske göre):** kritik → 3-değer SDA; yüksek → 2-değer SDA, sadeleştirilmiş karar tablosu, 0-switch + geçersiz geçişler; hata tahmini (çift tıklama, TR sayı biçimi); 1 keşif tüzüğü (TC-046).
- **Otomasyon:** Playwright (Chromium). 46 aday testin tamamı hedef (TC-047 koşum sırasında hata tahmininden eklendi); en az AK-1…AK-6 ve AK-8 sınır/kural testleri. Smoke: TC-003, TC-006, TC-016, TC-021.
- **Manuel:** TC-046 keşif oturumu (45 dk).
- **Regresyon:** tüm Playwright seti her build'de; değişiklik etkisi `build_rtm.py --changed`.

## 5. Giriş kriterleri
- Bloke eden soru (Q-001) cevaplandı veya varsayılan (kapsam dışı) PO tarafından kabul edildi — **şu an: varsayımla ilerleniyor**.
- Build test ortamında, smoke testleri geçti.

## 6. Çıkış kriterleri (qa/exit-criteria.json)
- Gereksinim kapsamı %100 · koşum ≥ %95 · başarı oranı ≥ %95
- Açık kritik 0, yüksek 0, orta ≤ 3 hata
- Kritik riskli tüm gereksinimler (REQ-003) geçti
- Açık bloke eden soru 0
- Koşulan testlerin ≥ %80'i otomasyonla

## 7. Askıya alma ve devam
- Smoke testlerinden biri başarısızsa veya ortam > 2 saat erişilemezse askıya al; yeni build smoke'u geçince devam et.

## 8. Ortamlar ve test verisi
| Ortam | Amaç | Konfigürasyon | Veri |
|---|---|---|---|
| Test (localhost:4174) | Sistem testi + otomasyon | Chromium, tr-TR, Europe/Istanbul | Test müşterisi bakiye 120.000,00 TL; IBAN TR330006100519786457841326 (check_ids.py: geçerli); OTP 123456 |

**Test edilebilirlik bağımlılıkları:**
- **B-1 (sahibi: Dev/Ops):** Bakiye seed'i. Bakiye (120.000) günlük limitten (100.000) büyük olduğu için AK-6 (yetersiz bakiye) limit içinde kalınarak test edilemez. Bu turda bakiye yalnızca limitin uygulanmaması (REQ-003 hatası) sayesinde düşürülebildi; hata düzeltildiğinde TC-022…TC-024 için bakiye ayarlanabilir test müşterisi gerekir.
- **B-2 (sahibi: Test verisi):** İkinci geçerli sentetik IBAN (DS-007 D04 "farklı alıcı" kolonu için).
- **B-3 (sahibi: Dev):** Günlük sıfırlama için kalıcı kullanım + saat kontrolü.
- **B-4 (sahibi: Dev):** Form alanlarında `data-testid` yok (erişilebilir etiketler yeterli); kayıtlı alıcı arayüzü yok (Q-009).

## 9. Takvim ve efor
| Aktivite | Efor | Not |
|---|---|---|
| Manuel koşum (47 test, 2 döngü) | ~13,5 sa (plan_facts sezgisel: 5 dk/test + 2 dk/adım) | Otomasyonla ~0,2 sa |
| Otomasyon geliştirme | 6–10 sa | 45 aday, veri güdümlü gruplar |
| Hata raporlama/doğrulama | +%25 | |
| Tampon (açık 14 soru) | +%20 | |
| **Toplam aralık** | **~20–30 sa** | Varsayım: tek QA, ortam kararlı |

## 10–11. Roller ve çıktılar
QA: tasarım, otomasyon, raporlama. PO: soruların cevabı. Çıktılar: gereksinimler, test case'ler, RTM, Xray CSV, Playwright seti, hata raporları, tamamlama raporu.

## 12. Açık konular ve varsayımlar
qa/clarifications.md içindeki 14 soru (1 bloke eden: Q-001). Kullanıcı "sorularla bekleme" dediği için tüm varsayılanlar geçici olarak kabul edildi.
