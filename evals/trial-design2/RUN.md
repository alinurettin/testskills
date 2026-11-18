# RUN — trial-design2 (evaluator only, do NOT give this file to the agent)

Trial kind: **test case design from a precise specification** (Turkish context), second generation.
Fictional company "Poyraz Kargo A.Ş." (poyrazkargo.example): parcel pricing, promised delivery date,
shipment life cycle and an end-to-end configuration space. All data are synthetic.
Answer key: `C:\projeler\TestSkills\evals\keys\design2.md` (+ `design2_grader.py`, `design2_ref\`).
Never copy anything from the key folder into the agent workspace.

Why it exists: `trial-design` no longer separates strong agents (all 6 runs of the last trial at 35–36 / 36). This
trial has interacting pricing rules, a date calendar, a guarded state model, a mixed-strength
configuration matrix, row budgets, and planted specification defects next to traps. It is graded
by script only; there is nothing to confirm by hand.

## What the agent gets

Copy exactly these into a fresh, empty working directory per run (one directory per run, so that
parallel runs cannot see each other's outputs):

```
TASK.md
girdiler/GUM-spesifikasyon-v3.2.md
girdiler/sablonlar/ucret-testleri.csv
girdiler/sablonlar/durum-testleri.csv
girdiler/sablonlar/konfigurasyon-matrisi.csv
girdiler/sablonlar/spesifikasyon-bulgulari.csv
```

Do **not** copy `RUN.md`. There is no server and no system under test: the task is pure test design
from the specification. Nothing listens on a port, nothing depends on the current date (all dates in
the specification are fixed in 2028), there is no state to reset. A run needs only a file system.
Node.js / Python are available to the agent if it wants to compute expected values with its own
script; that is allowed and is good practice.

Example (PowerShell, run N):

```powershell
$run = "C:\trials\design2-run-01"
New-Item -ItemType Directory -Force $run | Out-Null
Copy-Item C:\projeler\TestSkills\evals\trial-design2\TASK.md $run
Copy-Item -Recurse C:\projeler\TestSkills\evals\trial-design2\girdiler $run
```

Prompt to the agent: the content of `TASK.md` (or "Read TASK.md and do the task"), working
directory = `$run`. Give both arms (with and without the package) the same prompt, files and time.

## Expected agent outputs

```
$run\cikti\ucret-testleri.csv            (at most 40 rows)
$run\cikti\durum-testleri.csv            (at most 30 rows)
$run\cikti\konfigurasyon-matrisi.csv     (at most 24 rows)
$run\cikti\spesifikasyon-bulgulari.csv   (at most 8 rows)
$run\cikti\test-tasarimi.md              (short note, not scored)
```

Suggested time box: **40 minutes** wall-clock. Record model, package version, date, wall-clock time
and, if available, tokens and tool calls.

## Grading

```powershell
python C:\projeler\TestSkills\evals\keys\design2_grader.py C:\trials\design2-run-01\cikti --json C:\trials\design2-run-01\grade.json
```

The script recomputes every expected value with the reference oracle, scores the items P1–P15,
Z1–Z7, C1–C3 and D1–D5 (maximum 100), applies the penalties (wrong expected value, unsupported
combination, trap reported as a defect, row budget exceeded) and prints `FINAL SCORE: x / 100` as
its last line. The result is final: there are no `[MANUAL]` items. `--verbose` lists every missing
pair and every row that was not counted.

Things to know when reading a result:

- Format is graded exactly as TASK.md states it: UTF-8, `;` separator, the template header,
  case-sensitive codes. A file with a different header or encoding is reported as `NOT GRADED` and
  its area scores 0. BOM, CRLF, blank lines, spaces around a cell and trailing zeros are tolerated.
- Only the first N rows of a file are graded (N = its row budget); the rest is ignored and the file
  costs a flat 2 points.
- At the two points where the specification is defective in a way that changes an expected value
  (cut-off minute, `ERR_BEYAN_LIMIT` precedence) both readings are accepted.
- `test-tasarimi.md` is not read by the script.

Grade blind: strip the run's condition (package / no package, model) from the folder name before
grading. If an agent reports a specification problem that is real but not in the key, it is neither
rewarded nor penalised by the script; add it to `design2.md` §8 so that later runs are read fairly.

Sanity checks for the grader itself:

```powershell
python C:\projeler\TestSkills\evals\keys\design2_grader.py --selftest
python C:\projeler\TestSkills\evals\keys\design2_grader.py C:\projeler\TestSkills\evals\keys\design2_ref\gold    # 100 / 100
python C:\projeler\TestSkills\evals\keys\design2_grader.py C:\projeler\TestSkills\evals\keys\design2_ref\naive   # 9 / 100
python -m unittest tests.test_trial_design2        # from the repository root
```

## Stop / cleanup

Nothing to stop. Keep the run folder with `grade.json` until the result is recorded, then delete it.
