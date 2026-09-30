# Görev: Bakkalix v3.0 mobil test planı incelemesi

Merhaba,

Bakkalix'in v3.0 mobil sürümü 20 Ekim'de App Store ve Google Play'e çıkıyor. Mobil QA ekibimiz test planının taslağını hazırladı; yayından önce bağımsız, deneyimli bir gözün planı incelemesini istiyorum. Şu an elimizde test cihazı yok, bu yüzden iş tamamen masa başı: dokümanları okuyup değerlendirme ve öneri. Hiçbir şeyi cihazda çalıştırmanı beklemiyorum.

## Girdiler

Bu klasörün `girdiler/` dizininde:

- `girdiler/URUN_OZETI.md` — ürün ekibinin v3.0 ürün özeti (özellikler, desteklenen platformlar, kurallar)
- `girdiler/cihaz_os_dagilimi.csv` — analitikten aldığımız son 30 günlük aktif kullanıcıların cihaz / işletim sistemi dağılımı (Ağustos 2026)
- `girdiler/MEVCUT_TEST_PLANI.md` — QA ekibinin mevcut test planı (taslak v0.4)

## Senden istediklerim

1. **Planı incele, eksikleri ve hataları listele.** Her bulgu için: planın hangi maddesi veya bölümüyle ilgili olduğu (ör. `MT-12`, `§3`; tamamen eksik bir konuysa "yok" de), sorunun ne olduğu, neden önemli olduğu ve önceliği (P0 = yayını durdurur, P1 = yayından önce mutlaka, P2 = önemli, P3 = iyi olur). Listeyi önceliğe göre sırala.
2. **Eksik testleri öner.** Eksik gördüğün her konu için somut test senaryosu yaz: ön koşul, adımlar, beklenen sonuç, platform (iOS / Android / ikisi) ve gerçek cihaz mı emülatör/simülatör mü gerektiği.
3. **Cihaz matrisi öner.** Analitik verisine göre iOS ve Android için ayrı ayrı, kullanıcıların **en az %80'ini** kapsayan bir test cihazı matrisi öner. Hesaplamanı göster (hangi satırları / sürümleri topladığın ve kümülatif pay), seçimlerinin gerekçesini yaz ve mevcut matriste (planın §3'ü) neyin değişmesi gerektiğini belirt.

## Teslim

- Raporunun tamamını bu klasörde **`INCELEME_RAPORU.md`** adlı tek bir Markdown dosyası olarak yaz. Rapor Türkçe olsun.
- Rapor şu bölümleri içersin: (1) Bulgular (öncelik sıralı), (2) Önerilen ek test senaryoları, (3) Önerilen cihaz matrisi ve kapsama hesabı, (4) En kritik 5 aksiyonun kısa özeti.
- `girdiler/` altındaki dosyaları değiştirme.

Ekip yayına kadar sınırlı zamanda neyi düzeltmesi gerektiğini net olarak görmek istiyor; bulgularını somut ve uygulanabilir yaz.
