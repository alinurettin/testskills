# RUN — trial-design (evaluator only, do NOT give this file to the agent)

Trial kind: **test case design from a precise specification** (Turkish context).
Fictional company "Defne Kitap ve Kırtasiye A.Ş." (defnekitap.example); all data synthetic.
Answer key: `C:\projeler\TestSkills\evals\keys\design.md` (+ `design_grader.py`). Never copy the key folder into the agent workspace.

## What the agent gets

Copy exactly these into a fresh, empty working directory per run (one directory per run, so
parallel runs cannot see each other's outputs):

```
TASK.md
girdiler/SFM-spesifikasyon-v1.4.md
girdiler/sablonlar/fiyat-test-verisi.csv
girdiler/sablonlar/durum-gecis-testleri.csv
girdiler/sablonlar/konfigurasyon-matrisi.csv
```

Do **not** copy `RUN.md`. There is no server code and no system under test: the task is pure test
design from the specification. Nothing listens on a port, nothing is time-sensitive, there is no
state to reset. Runs need only a file system (Node.js 24 / Python 3 are available to the agent if it
wants to compute expected values with its own script; that is allowed and is good practice).

Example (PowerShell, run N):

```powershell
$run = "C:\trials\design-run-01"
New-Item -ItemType Directory -Force $run | Out-Null
Copy-Item C:\projeler\TestSkills\evals\trial-design\TASK.md $run
Copy-Item -Recurse C:\projeler\TestSkills\evals\trial-design\girdiler $run
```

Prompt to the agent: the content of `TASK.md` (or "Read TASK.md and do the task"), working directory = `$run`.

## Expected agent outputs

`$run\cikti\test-tasarimi.md`, `$run\cikti\fiyat-test-verisi.csv`,
`$run\cikti\durum-gecis-testleri.csv`, `$run\cikti\konfigurasyon-matrisi.csv`.

Suggested time box: 30 minutes wall-clock (a strong agent finishes in ~20–30 min).

## Grading

```powershell
python C:\projeler\TestSkills\evals\keys\design_grader.py C:\trials\design-run-01\cikti --json C:\trials\design-run-01\grade.json
```

The script recomputes every expected value with the reference oracle, scores K1–K12, applies the
false-positive (oracle error) penalty and prints `NIHAI PUAN x / 36`. Two items are heuristic and
marked `[MANUEL ONAY]` (K11c: Ek-A Örnek 4 finding; T4: false claims that a correct Ek-A example is
wrong) — confirm them by reading `test-tasarimi.md` as described in `design.md`, then adjust.
Grade blind: strip the run's condition (skill / no-skill, model) from the folder name before grading.

Sanity checks for the grader itself:

```powershell
python C:\projeler\TestSkills\evals\keys\design_grader.py --selftest
python C:\projeler\TestSkills\evals\keys\design_grader.py C:\projeler\TestSkills\evals\keys\design_ref\gold    # 36/36
python C:\projeler\TestSkills\evals\keys\design_grader.py C:\projeler\TestSkills\evals\keys\design_ref\naive   # 5/36
```

## Stop / cleanup

Nothing to stop. Delete the run directory when the grade is recorded.
