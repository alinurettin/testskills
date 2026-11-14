# Excel değişiklikleri ve yerel güncelleme / Workbook edits and local updates

## Contents

- Türkçe: önerilen akış, düzenleme kuralları, JSON adayı, şema ve vendor sınırı
- English: review/apply, editing rules, provenance, schema and vendor boundaries

## Türkçe

Yeni QA Suite Excel export'ları, görünür test ve özet sayfalarının yanında sürümlü, gizli
`_qa_suite` sayfası taşır. Bu sayfa **yalnızca seçili testlerin** başlangıç JSON'unu, özel
alanlarını, dış araç ID'lerini, adım metadatasını ve görünür hücrelerini korur. Belge
seviyesindeki metadata da korunur. Gizli sayfa gizlilik veya erişim kontrolü değildir;
dosyayı paylaşırken içeriğini hesaba katın. Sayfayı silmeyin veya değiştirmeyin.

Değişmeyen hücrelerde özgün JSON tipi, çok satırlı metin ve isteğe bağlı alanların
varlığı/yokluğu korunur. Bu garanti genel Excel/CSV dosyalarına değil, yeni QA Suite
workbook formatına aittir. Eski genel importer'ın varsayılan compact davranışı sürer.

### Önerilen akış

Excel'de düzeltin, ardından `reviewing-test-cases` skill kökünden:

```bash
python scripts/update_tests.py plan --source qa/test-cases.json --incoming edited.xlsx --out qa/update-plan.json
python scripts/update_tests.py apply --source qa/test-cases.json --plan qa/update-plan.json
```

1. `plan` kaynağı değiştirmez. Manifestte `add`, `update`, `deprecate`, belge `metadata`
   değişiklikleri, önce/sonra değerleri ve çatışmalar yer alır. Otomatik vendor import'u yapılmaz.
2. Manifesti gözden geçirin. Excel ve kaynak aynı testi farklı değiştirmişse çatışma oluşur.
   Farklı testlerdeki değişiklikler birleştirilir; aynı testte alan bazlı otomatik birleştirme yapılmaz.
3. Çatışmaları bilinçli çözün ve planı yeniden üretin. Çatışmalı plan uygulanmaz.
4. `apply` açık bir komuttur. Kaynak dosyanın bayt düzeyinde SHA256'sı plan anından farklıysa
   işlemi reddeder. Geçici dosya aynı dizinde yazılıp flush/fsync edilir; sonra atomik olarak
   değiştirilir. Hata öncesi kaynak korunur, bu araca ait staging ve kilit dosyası temizlenir.

Advisory kilit yalnız bu aracı kullanan işlemleri koordine eder. Kilitsiz harici editörlerle
işletim sistemi düzeyinde transaction garantisi yoktur. Son hash kontrolü dış düzenlemeleri
değiştirme öncesinde yakalar; plan/apply sırasında kaynağı başka araçla düzenlemeyin.
Çökmeden kalan kilidi ancak başka güncellemenin çalışmadığını doğruladıktan sonra kaldırın.

Başarılı apply sonrasında aynı girdiden yeniden plan üretmek sıfır eylem verir. Eski planı
değişmiş kaynağa yeniden uygulamak yerine yeni plan üretin. Kaldırılan testler silinmez,
`deprecated` olur. Kısmi Excel export'unda bulunmayan kaynak testleri korunur.

### Excel düzenleme kuralları

- Başlıkları, eski test ID'lerini ve eski adımların `Step/Adım` numaralarını koruyun.
  Her satırda ID olmalı; aynı testte adım numarası benzersiz olmalı.
- Yeni testte kullanılmamış bir `TC-###` verin. Test seviyesi alanlarını ilk adım satırına
  yazın. Diğer satırlarda aynı alanın farklı bir değeri varsa import reddedilir.
- Yeni adım için kullanılmamış pozitif numara kullanın. Adımlar numaraya göre sıralanır.
  Bir testin tüm satırlarını kaldırmak, plan üzerinde deprecate önerisi oluşturur.
- Başlık, gereksinim ID'leri, öncelik, polarite, teknik, ön koşullar, test verisi, adım
  action/data/expected alanları, etiketler, otomasyon adayı ve durum düzenlenebilir.
- Gereksinimler/etiketler düzenlenirse virgül, noktalı virgül veya satır sonuyla ayrılır.
  Ön koşullarda her satır bir öğedir. Karmaşık liste öğelerini JSON üzerinden güncelleyin.
- Değiştirilen `Test data/Test verisi` hücresi JSON object olmalı: `{"amount":100,"valid":true}`.
  Mevcut, değiştirilmemiş nesneler özgün tipleriyle korunur.
- Jira gereksinim anahtarları bilgi alanıdır; değiştirmek için gereksinim kaynağını düzenleyin.
  Testin kendi `external_id` değeri gizli metadatada korunur. Formül hücreleri reddedilir;
  düz metin olarak başlayan `=` karakteri güvenle korunur.

### Ayrı JSON adayına ihtiyaç varsa

```bash
python scripts/import_tests.py edited.xlsx --format json --out qa/candidate.json
python scripts/update_tests.py plan --source qa/test-cases.json --incoming qa/candidate.json --out qa/update-plan.json
```

Importer ayrıca `candidate.json.qa-baseline.json` üretir. Bu sidecar'ı adayla birlikte
tutun: başlangıç sürümünü ve aday hash'ini koruyarak üç yönlü çatışma denetimini sağlar.
Adayı ayrıca düzenlerseniz hash denetimi onu reddeder; Excel'den yeniden import edin.
Sidecar içermeyen JSON girdisi açık bir **tam istenen test seti** olarak değerlendirilir;
geçmiş Excel çatışmalarını tespit edemez ve eksik testleri deprecate etmeyi önerir.

JSON update akışında güncellenmiş JSON kaynaktır. Eski `test-cases.src.md` dosyasından JSON'u
yeniden üretmeyin: compact biçim özel alanların tümünü ifade edemez. Bu araç eski compact
kaynağı sessizce yeniden yazmaz. Başarılı değişiklik `test-cases.json.qa-reviewed.json`
işaretçisi bırakır; compact converter bu işaretçiyi görünce varsayılan olarak yazmayı durdurur.
Bu bir stale-workflow korumasıdır, güvenlik veya audit kaydı değildir. Compact akışına dönmeden
önce tüm alanları karşılaştırın; ancak bilinçli seçimle `--replace-reviewed` kullanın.

### Şema geçişi ve vendor sınırı

`schema_version` olmayan eski belgeler ve açık `schema_version: 1` kabul edilir.
Bilinmeyen/gelecek sürümler reddedilir. İş gereksinimi `version` alanı değiştirilmez.
Açık bir geçiş adayı üretmek için:

```bash
python scripts/update_tests.py migrate --source qa/test-cases.json --out qa/schema-v1-candidate.json
```

Ardından adayı planlayın ve inceleyip uygulayın. Hiçbir komut vendor güncelleme API'si çağırmaz.
Manifest vendor import formatı değildir. Yeni testler normal exporter ile seçilerek
aktarılabilir; mevcut testlerin güncellenmesi hedef aracın gerçek, doğrulanmış yolunu gerektirir.

## English

New QA Suite XLSX exports contain a versioned hidden `_qa_suite` sheet. It retains the
original JSON, custom fields, external IDs, per-step metadata and visible cells for **selected
tests only**, plus document-level metadata. Hidden is not private: account for that content
when sharing the workbook. Do not edit or remove this sheet.

Unchanged cells retain original types, multiline text and optional-field presence. This
guarantee applies to the new QA Suite workbook format. General XLSX/CSV import continues
to use the existing compact workflow by default.

### Review and apply

From the reviewing-test-cases skill root:

```bash
python scripts/update_tests.py plan --source qa/test-cases.json --incoming edited.xlsx --out qa/update-plan.json
python scripts/update_tests.py apply --source qa/test-cases.json --plan qa/update-plan.json
```

`plan` leaves the source unchanged and writes deterministic add/update/deprecate and document
metadata actions, before/after values and conflicts. Different edits to the same test conflict;
unrelated tests merge. Resolve conflicts deliberately, then regenerate the plan. There is no
automatic field-level conflict resolution.

`apply` is explicit. It rejects a changed source-byte SHA256, validates the manifest, takes an
exclusive advisory lock, stages and fsyncs a file beside the source and atomically replaces it.
Failures before replacement preserve the source and clean this operation's temporary files.
The advisory lock coordinates this tool only. There is no OS transaction with non-cooperating
editors; a final hash check detects changes before replacement. Do not edit the source with
other tools during apply. Inspect a crash-left lock before removing it.

Planning the same input after successful apply produces no actions. Regenerate instead of
reapplying an old plan to changed data. Removed tests become deprecated, never deleted.
Source tests excluded from a partial workbook export remain untouched.

### Editing rules

- Keep headers, existing TC IDs and existing step numbers. Every row needs an ID; step numbers
  must be positive and unique per test. Use a free TC ID for a new test and a free number for
  a new step. Test fields belong on its first step row; inconsistent repeated fields are rejected.
- Editable fields: title, requirement IDs, priority, polarity, technique, preconditions,
  test data, step action/data/expected, tags, automation candidate and status.
- Edited requirements/tags split on comma, semicolon or newline; preconditions split by line.
  Use JSON updates for complex list items. Edited test data must be a JSON object, for example
  `{"amount":100,"valid":true}`. Unchanged structured data retains its original types.
- Jira requirement keys are informational. Change their requirement source instead. The test's
  own external ID is retained in metadata. Formula cells are rejected; literal text beginning
  with `=` is retained safely. Removing all rows of a test proposes deprecation.

For a separate JSON candidate, run:

```bash
python scripts/import_tests.py edited.xlsx --format json --out qa/candidate.json
```

Keep the generated `candidate.json.qa-baseline.json` beside the candidate; it preserves
baseline conflict provenance and checks the candidate hash. Re-import after editing Excel;
separate candidate edits invalidate that hash. JSON without a sidecar is an explicit full
desired suite; it cannot detect historical workbook conflicts and proposes deprecation of
omitted tests.

In this update workflow JSON becomes authoritative. Do not regenerate it from a stale compact
source: compact text cannot express every extension field. This tool does not silently rewrite
that source. Successful changes leave `test-cases.json.qa-reviewed.json`; the compact converter
refuses to write by default when this marker exists. This is a stale-workflow guard, not a
security or audit record. Compare all fields before deliberately using `--replace-reviewed`
to return to compact authoring.

### Schema and vendors

Unversioned legacy documents and explicit `schema_version: 1` are accepted. Unknown/future
versions are rejected; the business `version` field remains unchanged. To write a lossless
migration candidate, use `update_tests.py migrate --source ... --out ...`, then plan and apply
it after review. The manifest is a local delta, not a vendor update/import format. No vendor API
is called. Export new tests selectively with the existing exporter; updates to existing vendor
records require a separately verified vendor-supported workflow.
