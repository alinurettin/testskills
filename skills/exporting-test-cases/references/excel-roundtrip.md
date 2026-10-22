# Kayıpsız Excel düzeltmeleri / Lossless Excel edits

## Türkçe

Yeni `.xlsx` export'larında iki görünür sayfaya ek olarak sürümlü gizli `_qa_suite` metadata
sayfası bulunur. Seçili testlerin tüm JSON alanlarını, özel alanlarını, dış ID'lerini ve adım
metadatasını korur. Belge metadatası da taşınır; seçilmeyen test kayıtları taşınmaz.
Gizli sayfa erişim kontrolü değildir. Dosyayı paylaşmadan önce bu içeriği hesaba katın.

Eski ID'leri/adım numaralarını ve başlıkları koruyarak görünür test sayfasını düzenleyin.
Sonra `reviewing-test-cases` skill'ini kullanın. O skill'in `update_tests.py plan` komutu,
workbook ile mevcut JSON'u karşılaştırıp ekleme/güncelleme/deprecate/çatışma manifesti üretir.
`apply` açık komutuyla yalnız değişmemiş kaynak hash'ine uygulanır. Gerçek vendor'a yazılmaz;
manifest vendor update formatı değildir. Aynı girdiyi uygulamadan sonra yeniden planlamak
sıfır eylem verir. Kısmi export kaynakta diğer testleri deprecate etmez.

Değişmeyen hücreler kaynak tiplerini ve özel alanları korur. Test verisi hücresini değiştirirken
JSON object kullanın; örneğin `{"amount":100}`. Jira gereksinim anahtarları bilgi alanıdır;
gereksinim kaynağından güncellenir. Formül hücreleri kabul edilmez.

`import_tests.py --format json` ayrı aday istendiğinde kullanılabilir; üretilen baseline sidecar'ı
adayla birlikte tutun. Genel Excel/CSV → compact import varsayılanı eski uyumluluk için sürer,
ancak bütün özel alanların kayıpsız geri alınmasını sağlamaz. JSON update sonrasında eski
compact kaynaktan JSON'u yeniden üretmeyin. Tam kurallar reviewing skill'indeki workbook
güncelleme rehberindedir.

Eski, `schema_version` olmayan belgeler kabul edilir. Açık sürümde yalnız `schema_version: 1`
desteklenir. Gelecek/bilinmeyen sürüm export edilmeden reddedilir. Vendor import formatları
değişmemiştir; gerçek import doğrulama durumu ayrı belgelenir.

## English

New XLSX exports add a versioned hidden `_qa_suite` metadata sheet beside the visible tests
and summary. It retains every selected test's original JSON, extension fields, external IDs,
step metadata and document metadata. Unselected test records are excluded. Hidden is not
private; account for this content when sharing files.

Edit the visible test sheet, preserving headers, existing IDs and step numbers. Then use the
reviewing-test-cases skill's `update_tests.py plan` command to review adds, updates, deprecations
and conflicts against current source JSON. Explicit `apply` requires the unchanged source hash.
The manifest is local, not a vendor update format, and no vendor is written. Replanning the
same input after apply gives no actions. Partial exports do not retire other source tests.

Unchanged cells preserve original types and extension metadata. Edited test-data cells require
a JSON object, for example `{"amount":100}`. Jira requirement keys are informational and must
be changed at their requirement source. Formula cells are rejected.

Use `import_tests.py --format json` only when a separate candidate is needed, retaining its
baseline sidecar. The general Excel/CSV-to-compact importer remains backward compatible;
it does not offer lossless extension-field recovery. After a JSON update do not regenerate
JSON from stale compact source. The reviewing skill's workbook update reference explains
the full editing, provenance and concurrency rules.

Unversioned legacy documents remain accepted. Explicit schema version 1 is supported;
unknown/future versions are rejected before export. Vendor CSV formats are unchanged and
real import verification remains a separate activity.
