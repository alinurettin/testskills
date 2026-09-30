# Manuel test uzmanları için rehber

Bu rehber, testleri elle koşan ve test case'lerini Excel'de, Xray'de ya da TestRail'de tutan test uzmanları içindir. Kod yazmanız gerekmez. QA Suite'e bir story ya da mevcut test setinizi verirsiniz; soru listesi, test case'ler, izlenebilirlik matrisi, içe aktarılabilir dosyalar ve raporlar alırsınız.

Asistan testlerinizi sizin yerinize koşmaz. Ürettiği her şey bir **taslaktır**; gözden geçirmek ve onaylamak sizin işiniz.

İlk deneme için: [examples/quickstart](../examples/quickstart/README.md). 10 dakikalık, sentetik bir şifre sıfırlama örneği.

## 1. İhtiyacınız olan 5 skill
| Skill | Ne zaman | Size ne verir |
|---|---|---|
| `analyzing-requirements` | Story ya da analiz dokümanı geldiğinde, test yazmadan önce | Tek tek test edilebilir gereksinimler, risk puanları, ürün sahibine gönderilecek soru listesi |
| `designing-test-cases` | Test case yazarken | Script'le hesaplanmış sınır değerler, karar tabloları ve durum geçişleri; adım, veri ve beklenen sonuç içeren test case'ler |
| `reviewing-test-cases` | Ekibin ya da başka bir aracın yazdığı test setini gözden geçirirken | Belirsiz adımlar, eksik beklenen sonuçlar, tekrarlar ve eksik testler; her biri için düzeltme önerisi |
| `exporting-test-cases` | Test case'leri bir araca taşırken | Xray, Zephyr Scale, TestRail, Azure DevOps, Qase, Excel, CSV ya da Markdown dosyası |
| `reporting-test-results` | Koşumdan sonra | Hata raporu; çıkış kriterlerini değerlendiren test özet ve tamamlama raporu |

Kurulumda 17 skill'in hepsini yükleyin. Skill'ler işi birbirine devrediyor: örneğin test tasarımı, kalibrasyon için `tracing-requirements`'ı; uçtan uca istekler `qa-orchestrator`'ı kullanır. Günlük işte bu beşini kullanırsınız. Kurulum: [README → Kurulum](../README.md#kurulum).

## 2. İstem kartları
Kartlardaki metni kopyalayın; `<...>` ile işaretli yerleri kendi içeriğinizle değiştirin. Çıktılar çalıştığınız klasörün altındaki `qa/` klasörüne yazılır.

### Kart 1: Story'yi incele, soruları çıkar
**Ne zaman:** Sprint planlamasından önce ya da story size geldiği gün.
```
Bu user story'yi incele. Belirsiz, eksik ve çelişkili noktaları ürün sahibine
sorulacak sorular olarak listele. Her soruya seçenekler ve varsayılan bir cevap yaz.
Test case yazma.

<story metni>
```
**Çıktı:** `qa/requirements.json` (gereksinimler, risk puanları) ve `qa/clarifications.md` (soru tablosu).
**İpucu:** Soru tablosunu olduğu gibi ürün sahibine gönderin. Cevapları aynı ID'lerle geri verin: "Q-003: Türkçe harfler kabul edilir."

### Kart 2: Test case yaz
**Ne zaman:** Story netleştikten sonra ya da sorular beklenirken, varsayımlarla.
```
Bu story için test case yaz. Hafif mod kullan. Soruları varsayılan cevaplarıyla
işaretle ve beklemeden devam et. Sonunda test case'leri Excel'e (xlsx) aktar.

<story metni ya da dosya adı>
```
**Çıktı:** `qa/test-cases.src.md` (okunabilir kaynak), `qa/test-cases.json`, `qa/rtm.md` ve `qa/exports/test-cases.xlsx`.
**İpucu:** 5–8 kabul kriterli bir story için 15–35 test beklenir. Çok daha fazlası çıkarsa "Neden bütçeyi aştın? Aynı sınıftan fazladan değer var mı?" diye sorun.

### Kart 3: Sınır değer ve karar tablosu
**Ne zaman:** Tutar, limit, yaş ya da tarih gibi aralıklar ve birden çok koşula bağlı iş kuralları olduğunda.
```
Kredi başvurusunda tutar 1.000,00–50.000,00 TL, vade 12–60 ay.
Onay kuralları: <kurallar>. Sınır değer ve karar tablosu testlerini tasarla.
Script çıktısını ve bulduğu boşlukları da göster.
```
**Çıktı:** `qa/design/DS-*.md`: hesaplanmış sınır değerleri, karar tablosu kolonları, kuralların boşlukları ve çelişkileri.
**İpucu:** Script'in bulduğu her boşluk ya da çelişki bir sorudur. Asistan bunları sessizce çözmez; soru listesine ekler.

### Kart 4: Ekibin Excel test setini incele
**Ne zaman:** Bir test seti regresyon paketine alınmadan önce ya da yeni bir ekip üyesinin testlerini gözden geçirirken.
```
Ekteki Excel test setini ve ilgili story'yi incele. Belirsiz adımları, eksik
beklenen sonuçları, tekrar eden ve eksik testleri bul. Her bulgu için düzeltme
önerisi ver. Orijinal dosyayı değiştirme.
```
**Çıktı:** Bulgu listesi ve inceleme raporu. İsterseniz düzeltilmiş test seti ayrı bir dosya olarak.
**İpucu:** `.xlsx` doğrudan okunur. Eski `.xls` ya da şifreli dosyaları önce `.xlsx` veya "CSV UTF-8" olarak kaydedin.

### Kart 5: Test yönetim aracına aktar
**Ne zaman:** Test case'ler hazır ve onaylıyken.
```
qa/test-cases.json'daki testleri Xray'e aktarılacak CSV olarak hazırla.
Story'nin Jira anahtarı <SHOP-128>. Önce yalnızca 3 testlik bir deneme dosyası da üret.
```
**Çıktı:** `qa/exports/xray.csv`, alan eşleme tablosu ve içe aktarma adımları.
**İpucu:** İçe aktarımlar gerçek bir Xray, Zephyr, TestRail, Azure DevOps ya da Qase sunucusunda denenmedi; resmi dokümantasyona göre hazırlandı. Her zaman önce 2–3 testlik bir deneme projesine aktarın.

### Kart 6: Hata raporu ve test özet raporu
**Ne zaman:** Bir test kaldığında ve sprint ya da sürüm sonunda.
```
TC-010 kaldı: kullanılmış şifre sıfırlama bağlantısı ikinci kez açılabiliyor ve
yeni şifre kaydedilebiliyor. Ortam: test, Chrome. Bunun için hata raporu yaz.
```
```
Sprint sonu test özet raporu hazırla. 25 testten 21'i geçti, 3'ü kaldı, 1'i bloke.
Çıkış kriterleri sağlandı mı? Hangi riskler açık kalıyor?
```
**Çıktı:** Hata raporu (adımlar, beklenen ve gerçekleşen sonuç, önem ve öncelik, kanıt) ve `qa/completion-report.md`.
**İpucu:** Asistan koşulmamış bir testi "geçti" saymaz ve eksik veriyi "0" değil "bilinmiyor" olarak raporlar. %94,8 yürütme, %95'lik bir kriteri karşılamaz.

## 3. Gerçek bir story'yi yapıştırmadan önce: anonimleştirme
**Önce kurumunuzun kuralını öğrenin.** Birçok banka ve kurum, iş dokümanlarının harici bir yapay zekâ hizmetine gönderilmesini yasaklar ya da yalnızca onaylı bir kurumsal hesaba izin verir. Emin değilseniz bilgi güvenliği ya da KVKK sorumlunuza sorun. Bu bölüm hukuki tavsiye değildir.

**Nereye ne gider?** QA Suite'in script'leri bilgisayarınızda çalışır ve ağa bağlanmaz. Ama asistana yazdığınız ya da okuttuğunuz her şey (istem, dosya içeriği, ekran görüntüsü) modeli sağlayan hizmete gider ve kullandığınız planın koşullarına tabidir. Ayrıntılar: [README → Veri gizliliği](../README.md#veri-gizliliği-makinenizden-ne-çıkar).

| Ne | Ne yapın | Örnek |
|---|---|---|
| Kişi adları (müşteri, çalışan, onaylayan) | Rol ya da açıkça sahte bir ad kullanın | "Ahmet Yılmaz" → "Müşteri A" |
| TCKN, VKN, IBAN, kart numarası, telefon | Sentetik değer ya da yer tutucu kullanın | Gerçek IBAN → `<IBAN-1>` ya da asistanın ürettiği sentetik test IBAN'ı |
| E-posta adresleri | `example.com` alan adını kullanın | "ahmet.yilmaz@banka.com.tr" → "musteri.a@example.com" |
| Kurum, ürün ve kampanya kod adları | Genel bir ad kullanın | "XBank Mobil Kasım Kampanyası" → "Demo Banka mobil kampanya" |
| İç sistem adları, URL, IP, sunucu adları, iç bağlantılar | Silin ya da genelleştirin | "https://jira.xbank.local/browse/PAY-812" → "PAY-812" |
| Gizli eşikler ve kurallar (dolandırıcılık skorları, iç limitler) | Temsili bir değer verin. Çıktıdaki sayıları sonra kendiniz gerçek değerle değiştirin. | "Skor ≥ 713 ise manuel onay" → "Skor ≥ 700 ise manuel onay" |
| Ekran görüntüleri | Test ortamından, gerçek veri içermeyen görüntü kullanın | |
| Üretim extract'ları, loglar, müşteri kayıtları | **Asla yapıştırmayın.** Sentetik veri isteyin. Maskeleme gerçekten gerekiyorsa `preparing-test-data`'nın `mask_data.py` script'ini kendiniz, yerelde çalıştırın; asistana yalnızca maskeli çıktıyı verin. | |

Maskelenmiş veri KVKK açısından çoğu zaman hâlâ kişisel veridir (takma adlandırma, anonimleştirme değildir). Üretim verisini test için kullanmadan önce veri sahibinin onayını alın.

**Önce / sonra:**
```
Önce:  Ahmet Yılmaz (TCKN 1234…) XBank Mobil'de 25.000 TL üzeri FAST'ta 713 skorlu
       müşteriler için manuel onaya düşer. Bkz. https://confluence.xbank.local/x/PAY
Sonra: Müşteri A, Demo Banka mobil uygulamasında 25.000 TL üzeri FAST transferinde
       risk skoru 700 ve üzeriyse manuel onaya düşer.
```

**Son kontrol:** "Bu metin herkese açık bir sayfada yayımlansa sorun olur muydu?" Cevabınız evetse, göndermeyin.

## 4. Hafif mod ve maliyet beklentisi
| Mod | Ne zaman | Ne yapar |
|---|---|---|
| **Hafif** (test case isteklerinde varsayılan) | Tek story, net kapsam | En ilgili 3–5 alanı tarar. Tipik çıktı: 8–15 gereksinim, 6–12 soru, 15–35 test. |
| **Tam** | Açıkça gereksinim incelemesi istediğinizde; kapsam büyük, regüle ya da yüksek riskliyse | Tüm kontrol listelerini ve sektör paketini kullanır, ayrıca bir analiz raporu yazar. Daha uzun sürer, daha çok token harcar. |

İstemde "hafif mod" ya da "tam inceleme" diyerek modu siz seçebilirsiniz.

**Ölçülmüş maliyetler** ([docs/EVALUATION.md](EVALUATION.md)):
- **Tam uçtan uca kör deneme** (FAST transferi): analiz, test planı, tasarım, Playwright otomasyonu ve raporlar birlikte ~26 dakika ve ~334 bin token sürdü.
- **0.2.0 karşılaştırması:** Skill'li bir görev ortalama ~7,5 dakika ve ~136 bin token sürdü; skill'siz ~4,6 dakika ve ~83 bin token. Sabit kontrol listesinde geçme oranı skill'le %93, skill'siz %82 oldu.
- **Hafif modda tek story, otomasyonsuz:** 10 dakika civarı bekleyin. Bu bir tahmindir, ayrıca ölçülmedi.

Token'ın size maliyeti planınıza bağlıdır; aboneliklerde kullanım limitinizden düşer.

**Maliyeti düşürmek için:**
- Kapsamı sınırlayın: "hafif mod", "otomasyon yapma", "yalnızca Excel'e aktar".
- Her story için yeni bir oturum açın.
- 100 sayfalık bir SRS yerine ilgili bölümü verin.
- Sorulara kendiniz cevap vermek istiyorsanız analizden sonra durmasına izin verin. Tek seferde bitsin istiyorsanız "beklemeden devam et" deyin.

## 5. Çıktıları Excel'de açmak
- **Test case'ler:** Asistandan Excel çıktısı isteyin ("Excel'e aktar"). `qa/exports/test-cases.xlsx` dosyasına çift tıklayın. "Test Case'ler" sayfasında her adım ayrı bir satırdır. "Özet" sayfasında önceliğe, polariteye ve tekniğe göre test sayıları vardır. Türkçe karakterlerde ve ayraçlarda sorun olmaz.
- **CSV isterseniz:** "Excel için noktalı virgüllü CSV" deyin. Türkçe bölge ayarlı Excel ayraç olarak `;` bekler. Dosya BOM'lu UTF-8 yazılır; Türkçe karakterler doğru görünür.
- **İzlenebilirlik matrisi:** `qa/rtm.csv` virgül ayraçlıdır. Çift tıklayınca her şey tek sütunda görünürse **Veri → Metinden/CSV'den** ile açın; kodlama olarak UTF-8'i, ayraç olarak virgülü seçin.
- **Markdown dosyaları** (`.md`: soru listesi, RTM, raporlar): Herhangi bir metin editöründe açılır. VS Code'da önizleme için `Ctrl+Shift+V`'ye basın. GitHub ve Azure DevOps wiki de bunları tablo olarak gösterir.
- **Excel'de düzenleme:** Excel'de yaptığınız değişiklikler `qa/test-cases.json`'a kendiliğinden geri dönmez. Düzeltmeleri asistana söyleyin ("TC-014'ün beklenen sonucunu şöyle değiştir") ya da düzenlediğiniz Excel'i Kart 4 ile yeniden içe aktarın.

## 6. Bilmeniz gerekenler
- Asistan, ürününüzün gerçek mesaj metinlerini ve ekranlarını bilemez. Beklenen sonuçlardaki metinler story'den ya da onaya sunulan varsayımlardan gelir; ürünle karşılaştırın.
- `running-exploratory-tests`, `testing-ai-features`, `testing-mobile-apps` ve `preparing-test-data` skill'leri **deneysel**dir: henüz kör denemeleri yapılmadı.
- Hata ya da içe aktarma sorunu bulursanız bir issue açın: [CONTRIBUTING.md](../CONTRIBUTING.md).
