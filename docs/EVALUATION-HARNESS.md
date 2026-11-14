# Reproducible evaluation records / Tekrarlanabilir değerlendirme kayıtları

## Contents
- English
- Türkçe

## English

`tools/eval_harness.py` makes no service/model calls and never changes historical results. It prepares an explicit allowlist, records provenance and produces descriptive JSON reports. A manifest is kept beside the agent workspace, not inside it. **A copied directory is not a security boundary.** The evaluator must enforce filesystem/tool permissions externally, start a fresh agent session and keep keys, old outputs and server sources inaccessible. The tool records this requirement; it does not claim to enforce an OS sandbox.

Create a config outside the agent workspace:

```json
{
  "schema_version": 1,
  "run_id": "api-baseline-001",
  "trial": "api",
  "model": "exact-provider-model-id",
  "parameters": {"effort": "low"},
  "seed": 42,
  "arm": "baseline",
  "inputs": [{"source":"evals/trial-api/api/openapi.json","path":"api/openapi.json"}]
}
```

Run from the repository root; the destination must be new and outside this repository:

```text
python tools/eval_harness.py prepare config.json --dest ../eval-runs/api-baseline-001
```

Arms: `baseline` copies only allowlisted inputs; `checklist` also writes the config's `checklist` text; `scripts` copies scripts/assets of the explicit `skills` list without SKILL instructions; `full` copies those entire skill folders. `scripts` and `full` require `skills`, for example `["testing-apis"]`. The runner must still make installed tools and execution permissions match the selected arm. Keep prompts, budgets and grader fixed. The manifest hashes inputs and copied context and records the Git commit. It contains local paths: review it before sharing.

After a real run, write an observation JSON, using null for unavailable measurements:

```json
{
  "schema_version": 1,
  "score": 8,
  "max": 10,
  "duration_seconds": null,
  "tokens": null,
  "tool_calls": null,
  "cost": null,
  "grader": {"model":"exact-grader-id","prompt_sha256":"actual-prompt-hash"},
  "artifacts": ["output/report.md"],
  "contamination_reasons": []
}
```

```text
python tools/eval_harness.py record ../eval-runs/api-baseline-001.manifest.json observation.json --out ../eval-runs/api-baseline-001.result.json
python tools/eval_harness.py report ../eval-runs/api-baseline-001.result.json --out ../eval-runs/report.json
python tools/eval_harness.py report evals/results/trials-0.9.0.json --out ../historical-summary.json
```

Output files are created exclusively; existing results are never overwritten. Changed/missing inputs and explicit contamination flags exclude a run from summaries. This detects file changes, not an agent reading an external answer key; external access control and evaluator inspection remain essential. Scores must be finite and within bounds. Reports include mean, median, sample standard deviation, range, ceiling counts and missing metadata. Repeated runs are not counted as independent problems. Bootstrap intervals resample matched task means (2,000 draws, seed 42), require at least five tasks and are exploratory; independence and grader correctness must be assessed separately. Different model settings must not be pooled. Historical skill/noskill labels are supported. Missing cost is unknown, never zero. No new LLM evaluation has been run merely by adding this tooling.

## Türkçe

New manifests include `suite_version` and `repository_dirty`. Use a clean, committed checkout for comparisons; a dirty HEAD alone does not uniquely identify local changes. Copied inputs/context have individual hashes, but these hashes are not a repository-wide source snapshot. Reports separate parameters, grader and commit cohorts; historical unknown metadata remains unknown.

Araç, ücretli model veya servis çağrısı yapmadan allowlist'li çalışma klasörü, girdi/bağlam hash'leri, manifest ve sonuç özeti üretir. Yukarıdaki komutlar aynı şekilde kullanılır. Dört kol: `baseline`, `checklist`, `scripts`, `full`. Son iki kol için açık `skills` listesi gerekir.

Manifest `suite_version` ve `repository_dirty` alanlarını kaydeder. Karşılaştırmaları temiz ve commit edilmiş kaynakta yapın; yalnız HEAD, yerel değişikliklerin sürümünü tek başına tanımlamaz. Parametre, grader ve commit grupları raporda ayrılır.

**Dosyaları kopyalamak erişim izolasyonu sağlamaz.** Ajanı yeni oturumda başlatın; cevap anahtarlarına, eski çıktılara ve sunucu kaynaklarına erişimi değerlendirici tarafında engelleyin. Manifest ajan klasörünün yanında tutulur; harici erişimi işletim sistemi/runner sınırlandırmalıdır. Değişen girdiler ve bildirilen kirlenme özette hariç tutulur; dışarıdaki anahtarın okunması tek başına dosya hash'lerinden anlaşılamaz.

Gerçek koşum bittikten sonra gözlemi kaydedin. Süre/token/maliyet bilinmiyorsa `null` bırakın. Ham çıktıların hash'leri ve grader sürümü kaydedilebilir. Var olan sonuçlar ezilmez. Ortalama, medyan, standart sapma, aralık, tavan etkisi ve eksik metadata görünür. Güven aralıkları tekrarlanan koşuları değil, eşleştirilmiş görevleri yeniden örnekler; küçük ve seçilmiş görev setlerinde genelleme sınırlıdır. Bu altyapı eklenmesi yeni bir model deneyi yapılmış olduğu anlamına gelmez.
