# RUN.md — trial-requirements (EVALUATOR ONLY — do not give to the agent)

Kind: requirements analysis before test design (static review, no system under test).
Product: "Kolay İade ve Geri Ödeme" (returns and refunds) for the fictional Turkish e-commerce company Nergis Çarşı A.Ş.
Answer key: `C:\projeler\TestSkills\evals\keys\requirements.md` (never copy into a run folder).

## What the agent gets

Copy exactly these into a fresh, empty working folder for each run:

```
TASK.md
girdiler\PRD-Kolay-Iade-v1.3.md
girdiler\Ek-B-kategori-iade-kurallari.csv
```

Do NOT give the agent: this RUN.md, anything under `evals\keys\`, or any other trial folder.

Example (PowerShell, one folder per run; parallel runs just use different folder names):

```powershell
$run = "C:\eval-runs\requirements-opus-skill-01"
New-Item -ItemType Directory -Force "$run\girdiler" | Out-Null
Copy-Item C:\projeler\TestSkills\evals\trial-requirements\TASK.md $run
Copy-Item C:\projeler\TestSkills\evals\trial-requirements\girdiler\* "$run\girdiler"
```

Start the agent with its working directory set to `$run` and the prompt: "TASK.md dosyasındaki görevi yerine getir." (or paste TASK.md's content).

## Server / runtime

None. There is no server, no port, no state and nothing time-sensitive. The task is pure document analysis; runs are fully independent and can be executed in parallel without interference. Nothing needs to be stopped afterwards.

Requirements for the evaluator scripts only: Python 3 standard library (tested with Python 3.13 on Windows 11).

## Expected deliverables (in the run folder root)

- `gereksinim-analizi.md`
- `test-edilebilir-gereksinimler.md`

## Time budget

A strong agent should finish in about 20-30 minutes. Suggested hard stop: 45 minutes.

## Evaluator tooling (in `evals\keys\`)

1. Sanity-check that the inputs still contain every planted item and trap (run after any edit to the inputs):

   ```
   python C:\projeler\TestSkills\evals\keys\requirements_verify.py
   ```
   Exit code 0 and "ALL CHECKS PASSED" means the trial is intact.

2. Pre-screen a finished run (keyword evidence per K/T item; it does NOT replace the rubric):

   ```
   python C:\projeler\TestSkills\evals\keys\requirements_grade_assist.py C:\eval-runs\requirements-opus-skill-01
   ```
   Then grade blind against `requirements.md` (acceptance rules, trap penalties, quality rubric). Max score 46.

## Blinding

Strip the run-folder name (which may reveal model / skill condition) before handing deliverables to the grader; for example copy the two deliverables into `grading\<random-id>\`.
