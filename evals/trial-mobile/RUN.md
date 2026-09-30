# RUN — trial-mobile (mobile app test planning / review, no device)

Evaluator-only instructions. Do **not** hand this file to the agent under test.

## What this trial is

A desk-review task: the agent reads a product brief, an analytics CSV and an existing mobile
test plan for the fictional Turkish grocery + wallet app "Bakkalix" v3.0, then writes a review
report (gaps with priorities, proposed missing tests, device matrix covering >= 80% per platform).
All companies, people, domains (`*.example.com`) and numbers are synthetic.

## Nothing to start

- No server, no emulator, no network access needed. `PORT` is not used by this trial.
- No state is kept anywhere, so parallel runs cannot interfere as long as each run has its own
  working directory.

## Per-run setup (one fresh directory per run)

Hand the agent exactly these files, keeping the relative layout:

```
TASK.md
girdiler/URUN_OZETI.md
girdiler/cihaz_os_dagilimi.csv
girdiler/MEVCUT_TEST_PLANI.md
```

PowerShell:

```powershell
$run = "C:\eval-runs\mobile\run-01"          # new directory per run / per arm
New-Item -ItemType Directory -Force $run | Out-Null
Copy-Item C:\projeler\TestSkills\evals\trial-mobile\TASK.md $run
Copy-Item C:\projeler\TestSkills\evals\trial-mobile\girdiler $run -Recurse
```

Bash (Git Bash):

```bash
run=/c/eval-runs/mobile/run-01
mkdir -p "$run" && cp -r /c/projeler/TestSkills/evals/trial-mobile/{TASK.md,girdiler} "$run"/
```

Start the agent with `$run` as its working directory and this prompt (or paste the body of
`TASK.md` as the user message):

> `TASK.md` dosyasındaki isteği yerine getir. Tüm girdiler bu klasörde.

Suggested time budget: 25 minutes wall clock. Both arms (with-skill / no-skill) get the same
files, the same prompt and the same budget.

## Expected output

- `$run/INCELEME_RAPORU.md` (Turkish Markdown report). Nothing else is required.

## After the run

1. Confirm `INCELEME_RAPORU.md` exists.
2. Confirm the inputs were not modified (expected SHA-256):

| File | SHA-256 |
|---|---|
| `TASK.md` | `d1bf3bab94a34fe39dba5e372aa484a1d9c09ea5572cbe2e0f098d82675492c3` |
| `girdiler/URUN_OZETI.md` | `fed2ba21406c3960c4a212357e8f1b4daa3bf4caec82b8ce97b07641eb6d57d4` |
| `girdiler/MEVCUT_TEST_PLANI.md` | `2d6988d20537da8e20da5b00e4572540740b664a905a0cd575044cfdfe74d966` |
| `girdiler/cihaz_os_dagilimi.csv` | `d5fe02cd7d01272715306f41100e628b0ae64699069e482ecab65d7faf9b44ae` |

```powershell
Get-FileHash "$run\TASK.md", "$run\girdiler\*" -Algorithm SHA256 | Format-Table Hash, Path
```

3. Grade the report with the key file `C:\projeler\TestSkills\evals\keys\mobile.md`
   (kept outside the trial folder). The key contains the planted items, traps, rubric and a
   stdlib-only Python checker for the device-matrix numbers (save the code block from the key as
   `check_matrix.py` and run `python check_matrix.py <run>\girdiler\cihaz_os_dagilimi.csv`).

## Stop / cleanup

Nothing to stop. Delete the run directories when grading is finished.
