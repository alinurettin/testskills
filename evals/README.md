# Evaluations

**Türkçe özet aşağıda.**

This folder holds everything used to measure QA Suite: the blind trials with planted defects, their answer keys, the routing (trigger) query sets and the with/without-skill benchmark. The recorded results are in [docs/EVALUATION.en.md](../docs/EVALUATION.en.md).

| Path | What it is | Show it to the agent under test? |
|---|---|---|
| `trial-*/` | One blind trial per folder: the task, the inputs and, for some, a system under test (`server.js`, `demo-app/`, `app/`) | Only the files the trial's `RUN.md` names |
| `trial-*/RUN.md` | Evaluator instructions: what to copy, what to start, how long to allow | **No** |
| `keys/` | Answer keys: planted defects, traps, rubrics, grading helpers | **Never** |
| `files/`, `evals.json` | Inputs and assertions of the with/without-skill benchmark | Only the files an eval names |
| `trigger-queries*.json` | Routing (trigger) query sets for `tools/routing_proxy.py` and `tools/trigger_eval.py` | No |
| `results/` | Recorded results | No |
| `workspace/` | Scratch output of earlier runs | No |

## Running a blind trial correctly

A blind trial only means something if the agent sees exactly what a tester would see. The repository is full of material that would give the answers away: the keys, the demo implementations, the regression tests in `tests/` and the outputs of earlier runs in `examples/` and `workspace/`. So:

1. **Copy the trial outside the repository.** Create a fresh, empty folder per run (for example `C:\eval-runs\api\skill-1`), and copy into it only the files the trial's `RUN.md` names. Never start the agent with the repository, or any folder inside it, as its working directory. An agent can search upwards and across the disk.
2. **Hand over only what `RUN.md` names.** Keep the relative paths it gives. Do not copy `RUN.md` itself.
3. **Keep these away from the agent:** `evals/keys/`, `tests/` (including `tests/fixtures/`), `examples/`, `evals/workspace/`, other trial folders, and the system under test's source (`server.js`, `demo-app/`, `app/`). A web app's pages and scripts that any browser user can load are part of the black box; the source files on disk are not.
4. **Start servers on the evaluator side.** Run them from the repository, or from a copy the agent will not browse (see `trial-exploratory/RUN.md`). Give the agent only the URL and the test credentials. Use a fresh server process per run, because the demo servers keep state in memory.
5. **Install the skills, not the repository.** For the "with skill" arm, install the plugin or copy `skills/` into the agent's skills folder. For the "without skill" arm, give the same files, the same prompt and the same time budget, with no skills installed.
6. **Use a fresh session.** A session that has read a key, a `RUN.md` or this repository must not be the agent under test.
7. **Record the run:** model, QA Suite version, date, wall-clock time, tokens and tool calls if available. Keep the whole run folder.

### Trials without a `RUN.md`

The first three trials predate `RUN.md`. Use this table instead.

| Trial | Hand to the agent | Start on the evaluator side | Key |
|---|---|---|---|
| `trial-fast` (end to end, web) | `docs/US-310-fast-transfer.md`, plus the URL `http://localhost:4174` | `node evals/trial-fast/demo-app/server.js` | [keys/fast.md](keys/fast.md) |
| `trial-api` (OpenAPI) | `api/openapi.json`, plus the URL `http://127.0.0.1:4180` and the tokens `token-alice` and `token-bob` | `node evals/trial-api/api/server.js` | [keys/api.md](keys/api.md) |
| `trial-migration` (data) | `mapping-spec.md`, `legacy_customers.csv`, `new_customers.csv` | nothing | [keys/migration.md](keys/migration.md) |

Both servers read the `PORT` environment variable. Example for the API trial (PowerShell):
```powershell
$run = "C:\eval-runs\api\skill-1"
New-Item -ItemType Directory -Force "$run\api" | Out-Null
Copy-Item C:\projeler\TestSkills\evals\trial-api\api\openapi.json "$run\api\"
node C:\projeler\TestSkills\evals\trial-api\api\server.js     # separate terminal; fresh process per run
```
Start the agent in `$run` with a prompt such as: "Bu API'yi `api/openapi.json` dokümanından test et. API http://127.0.0.1:4180 adresinde çalışıyor; test kullanıcıları token-alice ve token-bob."

The newer trials (`trial-ai`, `trial-exploratory`, `trial-mobile`, `trial-review`, `trial-testdata`) each have a `RUN.md`. Follow it; their keys are in `keys/`.

## Grading with the key

1. **Only after the run**, open the trial's key in `keys/`.
2. **Planted defects:** count a defect as found only if the output shows evidence: a failing test, or a defect report with steps and the observed result. A vague "might be a problem" does not count.
3. **Traps:** correct behaviour that the key says must *not* be reported. Every such report is a false positive.
4. **Ambiguities and questions:** check the ambiguities the key lists against the agent's question log.
5. **Verdict:** compare the release or sign-off decision with the key.
6. **Unplanted findings:** verify each one against the system yourself. If it is real, add it to the key under "unplanted but real", so later runs are graded fairly.
7. **Write it down:** add the result to `docs/EVALUATION.md` and `docs/EVALUATION.en.md`, including the cost and what was *not* measured. Findings that point to a gap in a skill go back into that skill, and the change log says so.

One run is a signal, not proof. When you compare with and without skills, run both arms on the same model, with the same prompt and the same budget, and preferably more than once.

---

## Türkçe özet

- **Kör deneme ancak ajan yalnızca bir test uzmanının göreceğini görürse anlamlıdır.** Depoda cevabı ele veren çok şey var: `evals/keys/` (cevap anahtarları), demo uygulamaların kodu, `tests/` altındaki regresyon testleri, `examples/` ve `evals/workspace/` altındaki eski çıktılar.
- **Deneme klasörünü depo DIŞINA kopyalayın.** Her koşu için boş bir klasör açın. Ajana yalnızca ilgili `RUN.md`'nin saydığı dosyaları verin. `RUN.md`'si olmayan ilk üç deneme için yukarıdaki tabloyu kullanın.
- **Ajan asla görmemeli:** `evals/keys/`, `tests/`, `examples/`, `evals/workspace/`, diğer deneme klasörleri ve test edilen sistemin kaynak kodu.
- **Sunucuları değerlendirici tarafında başlatın.** Ajana yalnızca adresi ve test kullanıcılarını verin. Her koşuda sunucuyu yeniden başlatın.
- **Deposu değil, skill'leri kurun.** Skill'siz kolda aynı dosya, aynı istem, aynı süre. Anahtarı ya da `RUN.md`'yi okumuş bir oturumu test edilen ajan olarak kullanmayın.
- **Puanlama:** anahtarı koşu bittikten sonra açın. Bir hata ancak kanıtla bulunmuş sayılır: kalan bir test ya da adımlı bir hata raporu. Tuzaklarda raporlanan her şey yanlış alarmdır. Soruları, kararı ve yerleştirilmemiş gerçek bulguları anahtarla karşılaştırın. Sonucu, maliyetiyle ve ölçülmeyenlerle birlikte `docs/EVALUATION.md`'ye yazın.
