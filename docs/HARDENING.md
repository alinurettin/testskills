# Reliable local workflows / Güvenilir yerel iş akışları

## Contents
- English
- Türkçe

## English

These changes are under development after 0.9.0; historical benchmark scores have not been remeasured. Python scripts remain standard-library only and offline. Node 22.18+, 24 or 26 executes the distributed TypeScript behavior tests; Playwright is needed only to execute generated API/browser tests, not the mock-based helper tests.

### Preflight and design

```text
python tools/doctor.py --profile core
python tools/doctor.py --profile api --project /path/to/automation
python skills/designing-test-cases/scripts/pairwise.py spec.json --max-nodes 100000 --max-tuples 250000 --format json
```

Doctor is read-only and resolves Playwright in the selected project. It does not install packages. Pairwise requires every feasible tuple to be covered; exact search proves impossibility or reports unknown. Exit 1 means incomplete coverage. Reduce the scope or raise a budget deliberately. Model omissions remain a human review responsibility.

### Lossless Excel edits and reviewed deltas

```text
python skills/exporting-test-cases/scripts/export_tests.py --tests qa/test-cases.json --format xlsx --out qa/tests.xlsx
python skills/reviewing-test-cases/scripts/update_tests.py plan --source qa/test-cases.json --incoming qa/edited.xlsx --out qa/update-plan.json
python skills/reviewing-test-cases/scripts/update_tests.py apply --source qa/test-cases.json --plan qa/update-plan.json
```

Edit visible cells in a QA Suite workbook and retain its hidden `_qa_suite` sheet. It carries the exported tests' baseline and custom metadata, not a copy of unselected tests. It can contain non-visible data: review metadata before sharing. New exports support lossless no-edit roundtrips; old/foreign workbooks without metadata use the existing best-effort importer. Use `import_tests.py --format json` for a JSON candidate; retain the generated `.qa-baseline.json` sidecar for conflict detection. Prefer planning directly from XLSX.

Inspect plan actions and conflicts. Apply rejects stale source-byte hashes and invalid plans, uses a cooperative lock and atomic replacement. Unrelated editors do not participate in that lock; this is not a multi-process database transaction. Omitted tests from a full desired JSON document are deprecated, never deleted. Partial XLSX exports preserve unselected source tests. A delta manifest is a local review artifact, not a vendor update-import format.

After apply, JSON is authoritative. The `.qa-reviewed.json` sidecar blocks accidental regeneration from stale compact source. Preserve it. `qa_compact.py --replace-reviewed` explicitly discards the guard and may discard arbitrary JSON fields. Prefer further reviewed plan/apply operations. Legacy unversioned suites remain accepted; `update_tests.py migrate --source ... --out ...` creates a schema_version 1 candidate. Unknown versions are rejected by roundtrip/update tools.

### API and test data

API schema validation supports a documented subset; unsupported constructs must be marked UNVERIFIED, not treated as valid. Inspect generated questions and skeletons before execution. Positive samples and negative mutations need a valid contract baseline. See the API skill's reference for its supported keywords and limitations.

Evidence is sanitized before truncation. Sensitive headers, URL values and unknown/raw bodies are omitted/redacted by default. Explicit field allowlists do not override sensitive-name masking. Use test accounts and synthetic data; a field allowlist cannot certify arbitrary data as safe. See `API_EVIDENCE`, `API_EVIDENCE_ALLOW_FIELDS` and `API_EVIDENCE_REDACT_KEYS` in the API skill documentation.

Synthetic decimal values respect representable scale bounds; impossible intervals fail. Datetime bounds must consistently include or omit timezone information. Distinct references are committed only after a row passes uniqueness, and final invariants are checked. JSON decimal output preserves numeric precision without converting through a binary float; consumers must also preserve precision when parsing.

### Local checks and evidence

```text
python tools/sync_shared.py --check
python tools/validate_skills.py
python -m unittest discover -s tests -v
node --test tests/api_helpers_hardening.mjs
```

The CI matrix configures Windows/Linux with Python 3.12/3.13 and Node 24. A configured platform is not a completed CI run. No new paid model run or live vendor verification is claimed. See [evaluation harness](EVALUATION-HARNESS.md) and [vendor verification](IMPORT-VERIFICATION.md).

## Türkçe

Önce `doctor.py --profile core` ile Python'u kontrol edin; API/otomasyonda `--profile api --project <proje>` kullanın. Araç kurulum veya ağ isteği yapmaz.

Pairwise sonucu ancak doğrulama başarılı ve unknown sayısı sıfırsa tam kapsam kanıtıdır. Kaynak sınırına ulaşmak imkânsızlık kanıtı değildir. Modelde unutulan iş kurallarını insan incelemesi tamamlar.

Excel'de düzenlediğiniz yeni QA Suite çıktısının gizli `_qa_suite` sayfasını koruyun. Önce yukarıdaki `plan` komutuyla değişiklikleri inceleyin, ardından `apply` çalıştırın. Eski veya yabancı Excel dosyalarında kayıpsız geri alım garantisi yoktur. Metadata görünür olmayan veri de içerir; paylaşmadan önce kontrol edin. JSON candidate dosyasının `.qa-baseline.json` yan dosyasını da koruyun.

Apply sonrasında JSON asıl kaynaktır. `.qa-reviewed.json` koruması eski `.src.md`den sessiz ezmeyi engeller. Özel alanlar compact biçimde tam temsil edilemediği için bundan sonra plan/apply akışını sürdürün. `--replace-reviewed` korumayı açıkça kaldırır ve alan kaybına yol açabilir. Kilit yalnız bu araçla çalışan süreçleri koordine eder; harici editörler için tam işlem garantisi vermez.

API sözleşmesinde desteklenmeyen yapılar UNVERIFIED olarak görünür; üretilen soruları ve skeleton'ları inceleyin. Kanıtlar hassas alanlardan arındırılır, ham/bilinmeyen gövdeler varsayılan kaydedilmez. Gerçek üretim verisi yerine sentetik veri kullanın. Decimal aralık/ölçek, timezone ve distinct ilişkileri üretim sonunda da kontrol edilir.

CI yapılandırması Windows/Linux ve Python 3.12/3.13'ü kapsar; burada yalnız gerçekten çalıştırılan kontroller teslim raporunda başarılı sayılır. Gerçek vendor importu ve yeni kör model deneyleri yapılmış gibi sunulmaz.
