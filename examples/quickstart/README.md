# 10 dakikada başla: şifre sıfırlama story'si

**[English →](README.en.md)**

Küçük, sentetik bir user story ile QA Suite'in ne ürettiğini görün. Story 6 kabul kriterinden oluşuyor: [US-128-sifre-sifirlama.md](US-128-sifre-sifirlama.md) ("Şifremi unuttum" ile şifre sıfırlama).

`qa/` klasöründeki dosyalar bu story için beklenen çıktılardır. Skill talimatları adım adım izlenerek üretildi:
1. `qa-orchestrator`, hafif mod
2. `analyzing-requirements`
3. `designing-test-cases`
4. `tracing-requirements`
5. `exporting-test-cases`

Sayıları script'ler hesapladı; elle düzeltilmedi.

## 1. Hazırlık
1. QA Suite'i kurun: [README → Kurulum](../../README.md#kurulum).
2. Boş bir klasör açın ve `US-128-sifre-sifirlama.md` dosyasını oraya kopyalayın. claude.ai kullanıyorsanız story metnini sohbete yapıştırın. Bu deponun içinde çalıştırmayın: asistan buradaki beklenen çıktıları görürse sonuç kendi analizi olmaz.

## 2. Bu istemi yapıştırın
```
US-128-sifre-sifirlama.md dosyasındaki user story için baştan sona test analizi yap.
Hafif mod kullan. Soruları varsayılan cevaplarıyla işaretle ve beklemeden devam et.
Test case'leri tasarla, izlenebilirlik matrisini çıkar ve Excel'e (xlsx) aktar.
Otomasyon yapma.
```

## 3. Ne göreceksiniz
Asistan sırayla şunları yapar:
1. **Gereksinim analizi.** Story'yi tek tek test edilebilir gereksinimlere böler, riskleri puanlar ve belirsizlikleri soru olarak yazar. Bu adımın sonunda sayıları ve en önemli soruları gösterir; siz "beklemeden devam et" dediğiniz için varsayımlarla devam eder.
2. **Test tasarımı.** Sınır değer, karar tablosu ve durum geçişi script'lerini çalıştırır. Script'lerin bulduğu çelişkiler yeni soru olur. Ardından test case'leri yazar.
3. **İzlenebilirlik ve kalibrasyon.** Matrisi üretir, kapsam boşluklarını ve öncelik şişmesini kontrol eder, en fazla iki tur düzeltir.
4. **Excel'e aktarım** ve kısa bir özet.

**Süre ve maliyet:** Bu boyutta bir story için hafif modda yaklaşık 10 dakika bekleyin. Bu bir tahmindir; bu örnek için ölçülmedi. Ölçülmüş iki referans ([docs/EVALUATION.md](../../docs/EVALUATION.md)):
- 0.2.0 karşılaştırmasında skill'li bir görev ortalama ~7,5 dakika ve ~136 bin token sürdü. Görevlerden biri bir kupon story'sinden Xray CSV'sine uçtan uca analizdi.
- Otomasyon ve raporlar dahil tam uçtan uca FAST denemesi ~26 dakika ve ~334 bin token sürdü. Hafif mod ve otomasyonsuz akış bundan belirgin biçimde ucuzdur.

## 4. Beklenen çıktılar
| Dosya | İçerik | Bu örnekte |
|---|---|---|
| [qa/requirements.src.md](qa/requirements.src.md) → [.json](qa/requirements.json) | Gereksinimler: kaynak, risk (olasılık × etki), durum | 14 gereksinim. 2'si türetilmiş, yani story'de yazmıyor ama test edilmesi gerekiyor. 4 yüksek, 8 orta, 2 düşük risk |
| [qa/clarifications.md](qa/clarifications.md) | Sorular: seçenekler, varsayılan cevap, neden önemli, kime sorulacak | 11 soru, bloke eden yok. Biri karar tablosu script'inden geldi (Q-011) |
| [qa/design/](qa/design/) | Tasarım kanıtı: script girdileri (`.json`) ve çıktıları (`.md`) | DS-001: sınır değerler. DS-002: karar tablosu (6 kolon, 15 çelişki → Q-011). DS-003: durum geçişi (5 geçiş, 4 geçersiz geçiş) |
| [qa/test-cases.src.md](qa/test-cases.src.md) → [.json](qa/test-cases.json) | Test case'ler: adım, veri, beklenen sonuç, öncelik, teknik | 25 test: 8 pozitif, 17 negatif. Öncelik: 2 kritik, 6 yüksek, 15 orta, 2 düşük |
| [qa/rtm.md](qa/rtm.md) · [qa/rtm.csv](qa/rtm.csv) | İzlenebilirlik matrisi ve kapsam boşlukları | Kapsam 13/14 (%92,9). 13 fonksiyonel gereksinimin hepsinde negatif test var |
| [qa/exports/test-cases.xlsx](qa/exports/test-cases.xlsx) | Excel: "Test Case'ler" ve "Özet" sayfaları | 25 test, 52 adım |

Açık bırakılanlar da raporda dürüstçe görünür:
- **REQ-012 ("sayfalar hızlı açılmalı") testsiz.** Ölçülebilir bir hedef yok; Q-006 cevaplanınca performans testi yazılır.
- **Kalibrasyonun REDUNDANT uyarısı (TC-016..TC-018) gerekçeli bırakıldı.** Üç test, karar tablosunun üç ayrı kolonunu (rakam, küçük harf, büyük harf kuralı) doğruluyor; aynı denklik sınıfı değiller.

Sizin çalıştırmanızın çıktısı kelimesi kelimesine aynı olmaz. Gereksinim ve test sayılarının skill'in bütçe aralığında kalması beklenir: bu boyutta bir story için 8–15 gereksinim, 6–12 soru ve 15–35 test.

## 5. Dikkat çeken birkaç test
- **TC-004, noktasız ı:** `ırem.test@example.com` yazıldığında `irem.test@example.com` hesabına bağlantı gitmemeli. Gevşek Unicode eşleştirmesi, bağlantının yanlış adrese gönderilmesine yol açabilecek bilinen bir hata sınıfıdır.
- **TC-011, iki sekme:** Aynı bağlantı iki sekmede açıkken ikinci sekmeden şifre kaydedilememeli.
- **TC-024, oturum kapatma:** Yalnızca sıfırlama istemek açık oturumu kapatmamalı. Aksi hâlde herkes, herhangi bir kullanıcıyı sistemden atabilir.

## 6. Çıktıları Excel'de açmak
- `qa/exports/test-cases.xlsx` dosyasına çift tıklayın. Türkçe karakterler ve çok satırlı adımlar doğru görünür.
- `qa/rtm.csv` UTF-8 (BOM'lu) ve virgül ayraçlıdır. Türkçe bölge ayarlı Excel ayraç olarak `;` beklediği için çift tıklayınca her şey tek sütunda görünebilir. Bu durumda **Veri → Metinden/CSV'den** ile açın, kodlama olarak UTF-8'i, ayraç olarak virgülü seçin.

Ayrıntılar ve istem kartları: [docs/MANUEL-TEST-REHBERI.md](../../docs/MANUEL-TEST-REHBERI.md).

## Sonraki adımlar
- Soruları ürün sahibine gönderin. Cevaplar gelince "Q-001..Q-011 cevaplandı, testleri güncelle" deyin; ID'ler korunur.
- Test yönetim aracınıza aktarın: "test case'leri Xray'e aktar" (ya da Zephyr, TestRail, Azure DevOps, Qase). Önce 2–3 testlik deneme importu yapın.
- Script'leri kendiniz çalıştırmak isterseniz (depo kökünden):
  ```bash
  cd examples/quickstart
  python ../../skills/tracing-requirements/scripts/build_rtm.py --requirements qa/requirements.json --tests qa/test-cases.json --out-dir qa
  python ../../skills/exporting-test-cases/scripts/export_tests.py --tests qa/test-cases.json --requirements qa/requirements.json --format xlsx --lang tr --out qa/exports/test-cases.xlsx
  ```
