# RUN — trial-testdata (test verisi hazırlama + maskeleme)

This file is for the evaluator. Do not hand it to the agent.

## What the agent receives

Hand over only these, copied into a fresh, empty working folder:

- `TASK.md`: the user request (Turkish). Give it verbatim as the prompt, or tell the agent to read it.
- `girdi/`: the whole folder, meaning `girdi/sema.md`, `girdi/canli_kesit/musteri_ozet.csv` and `girdi/canli_kesit/destek_kayitlari.csv`.

Do not copy `RUN.md`, and do not give access to `evals/keys/` or to any other trial folder.

All data is synthetic. The company (Yelkovan Ödeme), the people, the numbers and the domains (`example.test`, `example.com`) are fictional.

## Servers and ports

None. This trial needs no server, so no `PORT` is used. Everything is files plus Python 3 or Node.js (stdlib or built-ins only), fully offline. State lives only in each run's working folder, so parallel runs never interfere.

## Setting up one run (PowerShell)

```powershell
$trial = "C:\projeler\TestSkills\evals\trial-testdata"
$work  = "C:\eval-runs\testdata-<variant>-<n>"      # e.g. testdata-skill-1, testdata-noskill-2
New-Item -ItemType Directory -Force $work | Out-Null
Copy-Item "$trial\TASK.md" $work
Copy-Item "$trial\girdi" $work -Recurse
```

Start the agent with `$work` as its working directory. Suggested time cap: **25 minutes** (a strong agent needs about 15–25).

Expected deliverable: `$work\teslim\` containing `uret.(py|js)`, `maskele.(py|js)`, `uretim\*.csv`, `maskeleme\*.csv` and `RAPOR.md`.

## Grading one run

```powershell
python C:\projeler\TestSkills\evals\keys\testdata_grade.py --teslim "$work\teslim" --rerun --json "$work\grade.json"
```

- The grader always compares against the pristine inputs in `trial-testdata\girdi`, not against the agent's copy. It locates them automatically; override with `--girdi`.
- `--rerun` executes the agent's `maskele.*` and `uret.*` into temporary folders with `MASKELEME_ANAHTARI` unset, then compares byte-for-byte with the delivered outputs. This is the determinism evidence. Because it runs agent-written code, run it in the same sandbox or VM the agent used.
- To avoid running agent code in the grader, re-run the scripts yourself into `$work\run2\uretim` and `$work\run2\maskeleme`, then pass `--run2 "$work\run2"` instead of `--rerun`:
  - `python uret.py ..\run2\uretim`
  - `python maskele.py ..\girdi\canli_kesit ..\run2\maskeleme`
- Manual step: the grader prints "Tuzak adayları", which are lines from `RAPOR.md` that may be false positives. Check each against the trap list in the key. Count the confirmed false positives and re-run with `--fp N`. Each one costs 2 points.
- Report the K score, the objective score and the total separately. When comparing with-skill against no-skill runs, compare medians over at least 3 runs per arm.

## Sanity check of the trial itself

```powershell
python C:\projeler\TestSkills\evals\keys\testdata_grade.py --check-inputs
```

This must print `INPUT CHECK: PASS`. It proves that every planted item is still present in the inputs, for example after someone has edited them.

## Reset

Delete the run's working folder. The trial folder is never written to.
