# QA Suite geliştirme teslimi — 22 Ekim 2026

Başlangıç: `f71b3d342e3d6c306d8e3a59df30dfe17df72af0` (0.9.0).
Çalışma dalı: `codex/qa-suite-hardening`. Değişiklikler Unreleased olarak tutuldu; yeni bir sürüm yayımlandığı veya model benchmark'ının tekrarlandığı iddia edilmez.

## Değişen davranış

| Alan | Önce | Sonra |
|---|---|---|
| Pairwise | Mümkün bir çift kapsam dışındayken başarı; domain dışı seed kabulü | 52 çiftlik repro tam kapsanır; exact fallback; unknown ayrı ve exit 1; seed/domain ve kaynak sınırı kontrolleri |
| API sözleşmesi | oneOf/yan kuralların atlanması, geçersiz olumlu örnekler, allOf kaybı, 2XX hatası | Belgelenmiş konservatif alt küme; orijinal şemaya karşı kontrol; UNVERIFIED soru/skeleton; durum kodu aralıkları |
| API kanıtı | Bazı header/body sırları açık kalabilir | Varsayılan atlama/ayıklama; sentetik alan allowlist'i; kesmeden önce maskeleme; bilinen sırların yansımaları da temizlenir |
| Test verisi | Decimal sınır dışı, aware datetime hatası, retry sonrası distinct ihlali | Temsil edilebilir Decimal uzayı; kesin JSON sayı yazımı; timezone tutarlılığı; satır kabulünde referans tüketimi; nihai invariant kontrolleri |
| Excel | Tek yönlü export ve metadata kaybı | Yeni XLSX'te sürümlü gizli metadata; ID/özel alan koruyan geri alım; kısmi export kapsamı korunur |
| Güncelleme | Kaynak değişiklikleri ve tekrar aktarımlar için sınırlı kontrol | Dry-run delta planı, üç yönlü çatışma kontrolü, kaynak hash'i, cooperative lock ve atomik apply |
| Compact kaynak | Eski .src.md, Excel değişikliklerini yeniden ezebilir | İncelenmiş JSON için yan dosya koruması; açık --replace-reviewed olmadan yeniden üretim durur |
| Değerlendirme | Eksik metadata ve yalnız özet sonuçlar | Dört kol için allowlist/manifest/record/report; hash'ler; kirlenmiş kayıtların dışlanması; görev bazlı dağılım; model/grader/commit grupları |
| Kurulum/CI | Sınırlı ortam kontrolü | Read-only doctor; Windows/Linux × Python 3.12/3.13 CI yapılandırması; Node davranış kontrolleri; uyumluluk matrisi |

## Gerçekten çalıştırılan kontroller

Windows üzerinde:

| Kontrol | Sonuç |
|---|---|
| Python 3.13.15: `python -m unittest discover -s tests` | 346 test; 344 başarılı, 2 atlandı; 104,677 saniye |
| Python 3.12.14: aynı paket | 346 test; 344 başarılı, 2 atlandı; 100,664 saniye |
| Node 24.19.0: `node --test tests/api_helpers_hardening.mjs` | 8/8 başarılı; dağıtılan gerçek TypeScript çalıştırılır |
| Bağımsız JSON Schema Test Suite fixture'ları | Python ve TypeScript içinde 69 sabit beklenen sonuç |
| `python tools/validate_skills.py` | 17 skill; 0 hata, 0 uyarı |
| `python tools/sync_shared.py --check` | Başarılı |
| `python tools/check_facts.py` | 30 kayıt; gecikmiş doğrulama/başka uyarı yok |
| `python tools/doctor.py --profile core` | Başarılı |
| `git diff --check` | Başarılı |
| `python tools/package_skills.py` | 17 ayrı skill ZIP'i oluşturuldu |

Atlananlar başarı sayılmadı: gerçek vendor re-export fixture'ı bulunmuyor; Windows ortamında symlink oluşturma izni yok. CI Linux/Windows için yapılandırıldı, fakat bu geliştirme sırasında uzak CI veya Linux koşumu yapılmadı. Sandbox'ın varsayılan TEMP izin sorunu, test geçicileri çalışma alanındaki klasöre yönlendirilerek aşıldı; ürün davranışını değiştirmek için kullanılmadı.

Bilinen hatalar önce başarısız regresyonlarla yeniden üretildi. Pairwise oracle'ı küçük alanlardaki tam atamaları bağımsız tarar; API oracle'ı upstream sabit sonuçları kullanır. Maskeleme testleri yalnız sahte sentinel sırlar ve mock response kullanır; canlı API isteği göndermez.

## Kısa kullanım

```text
python tools/doctor.py --profile core
python skills/exporting-test-cases/scripts/export_tests.py --tests qa/test-cases.json --format xlsx --out qa/tests.xlsx
python skills/reviewing-test-cases/scripts/update_tests.py plan --source qa/test-cases.json --incoming qa/edited.xlsx --out qa/update-plan.json
python skills/reviewing-test-cases/scripts/update_tests.py apply --source qa/test-cases.json --plan qa/update-plan.json
python tools/eval_harness.py report evals/results/trials-0.9.0.json --out ../historical-summary.json
```

Excel apply sonrasında JSON asıl kaynaktır. Gizli `_qa_suite` sayfasını ve JSON baseline/review yan dosyalarını koruyun. Eski compact kaynağı yeniden üretmek özel alanları kaybettirebilir; varsayılan koruma bunu durdurur. `--replace-reviewed` bu korumayı açıkça kaldırır.

## Geriye uyumluluk ve kalan sınırlar

- Python runtime bağımlılığı eklenmedi; script'ler standart kütüphane kullanır. Node mock testleri Playwright kurulumu gerektirmez. Gerçek otomasyon için proje ortamında Playwright gerekir; bu repoya otomatik kurulmadı.
- Eski sürümsüz test belgeleri kabul edilir. Açık schema_version 1 desteklenir; yeni roundtrip/update araçları bilinmeyen sürümleri reddeder. Vendor CSV golden dosyaları değiştirilmedi.
- Eski/yabancı Excel dosyaları metadata taşımadığından kayıpsız geri alım garantisi yoktur; mevcut importer davranışı sürer. Gizli metadata erişim kontrolü değildir ve görünür olmayan alanlar içerir.
- API desteği tam JSON Schema/OpenAPI uyumluluğu değildir. Harici/döngülü referanslar, desteklenmeyen assertion/formatlar ve üretilemeyen regex örnekleri açıkça UNVERIFIED olur. Alan allowlist'i, içeriğindeki keyfi kişisel verinin güvenli olduğunu kanıtlamaz.
- Güncelleme kilidi yalnız aynı aracı kullanan süreçleri koordine eder; harici editörlerle veritabanı işlemi garantisi vermez. Delta manifesti bir vendor güncelleme formatı değildir.
- Değerlendirme klasörü hazırlamak ajan erişimini engellemez; işletim sistemi/runner izolasyonu ayrıca gerekir. Karşılaştırmalar temiz commit üzerinden yapılmalıdır. Yeni ücretli model koşumu veya gerçek ekip pilotu yapılmadı.
- Gerçek Xray/Zephyr/TestRail/Azure DevOps/Qase import/güncelleme/sonuç aktarımı için kullanıcı ortamında ayrı doğrulama gerekir. Hazır yaşam döngüsü şablonu ve mevcut import kiti güncellendi; erişim varmış gibi sonuç üretilmedi.

Detaylar: [iş akışı rehberi](HARDENING.md), [değerlendirme altyapısı](EVALUATION-HARNESS.md), [uyumluluk](COMPATIBILITY.md), [vendor doğrulaması](IMPORT-VERIFICATION.md).

## English summary

The local hardening fixes constrained pairwise coverage, conservative API schema/sample handling, evidence redaction, exact synthetic-data invariants and lossless reviewed workbook updates. Both Python 3.12 and 3.13 ran 346 tests each (344 passed, two skipped); Node ran eight behavior tests using 69 independent schema outcomes. Skill validation, sync, facts and packaging passed. No live vendor integration, remote/Linux CI run, paid model rerun or real-team validation is claimed. Runtime Python remains standard-library only. Historical benchmark records and vendor CSV goldens are preserved.
