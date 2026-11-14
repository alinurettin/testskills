# Turkish test terminology (TTB official terms)

Use the official term in Turkish output. Where the official term is unfamiliar, give the common term in parentheses at first mention, for example "test başlatma belgesi (charter)". Keep the common words as trigger and import aliases only. JSON keys, tags and IDs stay in English.

Sources, both read in full on 2026-11-15:
- **G** = TTB "ISTQB Yazılım Testi Terimler Sözlüğü" v2.0 (Eylül 2026), https://www.turkishtestingboard.org/files/ISTQB-Yazilim-Testi-Terimler-Sozlugu.pdf
- **S** = TTB translation of the ISTQB CTFL syllabus v4.0.1 (section in brackets), https://www.turkishtestingboard.org/files/pdfs/ISTQB_CTFL_Syllabus-v4.0.1.pdf

The "common usage" column is field experience, not taken from either source: treat every entry in it as unverified. Rows marked UNVERIFIED have no official term in G or S.

## Test design and exploratory testing
| English term | Official Turkish term | Common usage in Turkish teams | Source | Note |
|---|---|---|---|---|
| test charter | test başlatma belgesi | charter, görev, görev kartı | G, S (4.4.2) | |
| test oracle | test sonucunu bilen | oracle, kahin | G | Not in S |
| test session | test oturumu | oturum, session | G, S (4.4.2) | |
| session-based testing | oturum bazlı test | SBTM, oturum tabanlı test | G, S (4.4.2) | |
| debriefing | bilgilendirme toplantısı | debrief, değerlendirme toplantısı | S (4.4.2) | Not a headword in G |
| exploratory testing | keşif testi | keşifsel test | G, S (4.4.2) | |
| experience-based test technique | tecrübeye dayalı test tekniği | deneyime dayalı test | S (4.4) | G headword: "tecrübeye dayalı test" |
| error guessing | hata tahminleme | hata tahmini | G, S (4.4.1) | |
| checklist-based testing | kontrol listesine dayalı test etme | checklist testi | G, S (4.4.3) | |
| heuristic | sezgisel | sezgisel yöntem, heuristic | G | Not used as a term in S |
| time box | UNVERIFIED: no headword | zaman kutusu, timebox | - | S paraphrases it as "belirli bir zaman dilimi" (4.4.2) |
| black-box test technique | kara kutu test tekniği | black box | G, S (4.2) | |
| equivalence partitioning | denklik paylarına ayırma | denklik sınıfları, eşdeğerlik sınıfı | G, S (4.2.1) | S abbreviates it "DPA" |
| equivalence partition | denklik payı | denklik sınıfı | G, S (4.2.1) | |
| boundary value analysis | sınır değer analizi | BVA | G, S (4.2.2) | |
| decision table testing | karar tablosu testi | karar tablosu | G, S (4.2.3) | |
| state transition testing | durum geçişi testi | durum geçiş testi | G, S (4.2.4) | |
| test condition | test koşulu | test durumu | G, S (1.4.1) | What to test; not the output of a technique |
| coverage item | kapsam öğesi | kapsam maddesi | G, S (4.4.2) | The output of a test technique |
| coverage | kapsam | kapsama, coverage | G, S (1.4.4) | S uses "kapsama" in compounds ("kapsama kriterleri") |
| acceptance criteria | kabul kriterleri | kabul kriteri, AC | G, S (4.5.2) | |
| user story | kullanıcı hikayesi | user story | G, S (4.5.1) | |
| acceptance test-driven development | kabul testi güdümlü geliştirme | ATDD | G, S (4.5.3) | S mostly adds "yazılım": "kabul testi güdümlü yazılım geliştirme" |

## Testware
| English term | Official Turkish term | Common usage in Turkish teams | Source | Note |
|---|---|---|---|---|
| test case | test senaryosu | test case, test vakası, test durumu | G, S (1.4.1) | |
| test procedure | test prosedürü | test adımları | G, S (1.4.1) | |
| test script | test betiği | script, test scripti | G, S (1.4.1) | |
| test suite | test grubu | test suite, test seti, test takımı | G, S (1.4.1) | |
| test data | test verisi | test datası | G, S (1.4.1) | |
| test basis | test esası | test dayanağı, test temeli | G, S (1.4.1) | |
| test object | test nesnesi | test edilen sistem | G, S (1.1) | |
| testware | test çalışma ürünleri | test varlıkları, testware | G, S (1.4.3) | |
| test plan | test planı | | G, S (5.1.1) | |
| test environment | test ortamı | | G, S (1.4.1) | |
| precondition | önkoşul | ön koşul | G, S (4.5.3) | |
| expected result | beklenen sonuç | | G, S (1.4.1) | |
| actual result | gerçekleşen sonuç | gerçek sonuç | G, S (5.5) | |
| test result | test sonucu | | G, S (1.4.1) | |
| passed / failed | başarılı / başarısız | geçti / kaldı, pass / fail | G | S mixes "geçen/geçmeyen" with "başarısız" |
| traceability | izlenebilirlik | | G, S (1.4.4) | |

## Process, roles and reports
| English term | Official Turkish term | Common usage in Turkish teams | Source | Note |
|---|---|---|---|---|
| tester | test uzmanı | testçi, test mühendisi, tester | G, S (1.1) | |
| test analyst | test analisti | | G | Not in S |
| test manager | test yöneticisi | test lideri | G, S (1.4.5) | The role in S is "test yönetimi rolü" |
| test level | test seviyesi | | G, S (2.2.1) | |
| test type | test çeşidi | test türü, test tipi | G, S (2.2.2) | |
| test design | test tasarımı | | G, S (1.4.1) | |
| test implementation | test uyarlama | test hazırlama | G, S (1.4.1) | |
| test execution | test koşumu | test yürütme, test koşturma | S (1.4.1) | G headword differs: "test yürütme" |
| test monitoring | test gözetimi | test izleme | G, S (5.3) | |
| test control | test kontrol | test kontrolü | G, S (5.3) | S uses both forms |
| test completion | test tamamlama | test kapanışı | G, S (5.3) | |
| test completion report | test tamamlama raporu | test özet raporu, test kapanış raporu | G, S (5.3.2) | |
| test progress report | test ilerleme raporu | test durum raporu | G, S (5.3.2) | |
| test summary report | test özet raporu | | G | Not in S; CTFL v4 uses "test tamamlama raporu" |
| entry criteria | giriş kriterleri | | G, S (5.1.3) | |
| exit criteria | çıkış kriterleri | | G, S (5.1.3) | |
| definition of done | tamamlandı tanımı | DoD, bitti tanımı | S (5.1.3) | G differs: "tamamlanma tanımı" |
| test automation | test otomasyonu | | G, S (6.2) | |
| static testing | statik test | | G, S (3.1) | |
| review | gözden geçirme | review, inceleme | G, S (3.2) | |
| risk-based testing | risk bazlı test | risk tabanlı test | G, S (5.2) | G hyphenates: "risk-bazlı test" |
| risk level | risk seviyesi | | G, S (5.2.1) | |
| risk likelihood | risk olasılığı | | G, S (5.2.1) | |
| risk impact | risk etkisi | | G, S (5.2.1) | |

## Defects
| English term | Official Turkish term | Common usage in Turkish teams | Source | Note |
|---|---|---|---|---|
| defect | hata | bug, defect, kusur | G, S (1.2.3) | G: "fault" is "kusur", see hata |
| defect report | hata raporu | bug kaydı, hata kaydı | G, S (5.5) | |
| failure | arıza | hata, failure | G, S (1.2.3) | |
| error (mistake) | insan hatası | hata, yanlış | G, S (1.2.3) | |
| anomaly | anomali | | G, S (5.5) | |
| root cause | kök neden | | G, S (1.2.3) | |
| severity | önem derecesi | önem, ciddiyet, şiddet | G, S (5.5) | |
| priority | öncelik | | G, S (5.5) | |
| confirmation testing | onaylama testi | yeniden test, retest, doğrulama testi | S (2.2.3) | The G entry is only a cross-reference |
| retesting | tekrar testi | yeniden test, retest | G | Not in S; prefer "onaylama testi" |
| regression testing | regresyon testi | regresyon | S (2.2.3) | G headword is just "regresyon" |
| smoke test | duman testi | smoke test | G, S (5.1.3) | |

## Test types, quality and data
| English term | Official Turkish term | Common usage in Turkish teams | Source | Note |
|---|---|---|---|---|
| functional testing | fonksiyonel test | işlevsel test | G, S (2.2.2) | |
| non-functional testing | fonksiyonel olmayan test | işlevsel olmayan test | G, S (2.2.2) | |
| quality characteristic | kalite karakteristiği | kalite özelliği | G, S (2.2.2) | |
| usability | kullanılabilirlik | | G, S (2.2.2) | |
| accessibility | erişilebilirlik | | G | Not in S |
| security testing | güvenlik testi | | G | S has only the characteristic "güvenlik" |
| performance testing | performans testi | | G | S has only "performans verimliliği" |
| portability | taşınabilirlik | | G, S (2.2.2) | |
| maintainability | sürdürülebilirlik | bakım yapılabilirlik | G, S (2.2.2) | |
| reliability | güvenilirlik | | G, S (2.2.2) | |
| migration testing | taşıma testi | veri göçü testi, migrasyon testi, veri taşıma testi | G | G points to "dönüşüm testi" (conversion testing); S only uses "taşıma" (2.3) |
| data migration | UNVERIFIED: no headword | veri göçü, veri taşıma, migrasyon | - | Follow "taşıma": veri taşıma |
| pseudonymisation | takma adlandırma | takma adlı veri, pseudonymisation | G | Not in S |
| anonymisation | anonimleştirme | anonim hale getirme | G | Not in S |

## Known inconsistencies in the sources
- G and S disagree on test execution, definition of done, ATDD and the hyphen in risk-based testing; the table follows S, the syllabus candidates are examined on, and names the G form in the note.
- G's "confirmation testing" entry cross-references compliance testing, which looks like an error in G; S uses "onaylama testi" in the ISTQB sense.
- The English text of this suite says "equivalence partitions" (not classes) and "coverage items" for technique outputs, matching CTFL v4.0.1.
