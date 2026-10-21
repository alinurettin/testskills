# trial-testdata2 — evaluator notes (do NOT give this file to the agent)

Kind: test data preparation + masking (harder version). Turkish banking context, fictional bank
"Pusula Dijital Bank A.Ş.". All data is synthetic (example.com / example.test e-mails, IBAN bank codes
00990–00998 which are not assigned to real Turkish banks, generated TCKN/VKN values).

There is **no server**: nothing listens on a port, nothing is time-sensitive, runs are fully offline.
Parallel runs never interfere as long as every run gets its own workspace folder.

## What to give the agent

Copy exactly these into a fresh, empty workspace folder (one folder per run):

```
TASK.md
girdiler/uretim_kurallari.md
girdiler/maskeleme_politikasi.md
girdiler/uretim_kesiti/musteri.csv
girdiler/uretim_kesiti/hesap.csv
girdiler/uretim_kesiti/islem.csv
```

Do NOT give: this RUN.md, anything under `evals/keys/` (key, truth file, build script, grader,
reference solution). The prompt to the agent is the content of TASK.md (it is the Turkish user
request); the agent works inside the workspace and must write everything under `cikti/`.

Windows PowerShell example for one run:

```powershell
$ws = "C:\runs\testdata2-opus-skill-01"
New-Item -ItemType Directory -Force $ws | Out-Null
Copy-Item C:\projeler\TestSkills\evals\trial-testdata2\TASK.md $ws
Copy-Item -Recurse C:\projeler\TestSkills\evals\trial-testdata2\girdiler $ws
```

Expected agent deliverables (from TASK.md): `cikti/uret.py|js`, `cikti/uretilen/{musteri,hesap,islem}.csv`,
`cikti/maskele.py|js`, `cikti/maskeli/{musteri,hesap,islem}.csv` (made with `MASKE_ANAHTARI=pusula-uat-2026`),
`cikti/rapor.md`. Requirements on the agent side: Python 3 stdlib or Node.js 24 built-ins only.

Time budget: a strong agent should finish in about 20–30 minutes; suggested hard stop 45 minutes.

## Grading

```powershell
python C:\projeler\TestSkills\evals\keys\testdata2_grade.py C:\runs\testdata2-opus-skill-01 --json C:\runs\testdata2-opus-skill-01\grade.json
```

- Accepts the workspace folder or its `cikti/` folder.
- Part 1 is graded from `cikti/uretilen/`, Part 2 by row-aligned comparison of `cikti/maskeli/` with
  `girdiler/uretim_kesiti/` using `evals/keys/testdata2_truth.json`.
- Determinism (part of K9) **executes the agent's `cikti/maskele.py` or `maskele.js` twice** in separate
  processes (env `MASKE_ANAHTARI=pusula-uat-2026`, `PYTHONHASHSEED` removed, cwd = workspace, output to temp
  folders that are deleted afterwards, 300 s timeout). Run the grader in the same sandbox you trust for agent
  code, or pass `--no-exec` (then K9 can reach at most 5/8 and determinism must be judged by hand).
- Runtime of the grader: a few seconds.
- The grader prints automatic scores for K1–K12 and the T4 over-masking penalty, plus candidate lines from
  `rapor.md` for the manual traps T1–T3. Apply the manual penalties as described in
  `evals/keys/testdata2.md`.

## Rebuilding the inputs (only if they are lost or corrupted)

```powershell
python C:\projeler\TestSkills\evals\keys\testdata2_build.py
```

The build is deterministic (fixed seed) and rewrites `girdiler/uretim_kesiti/*.csv` and
`evals/keys/testdata2_truth.json`. Expected MD5 of the inputs:

```
230dcdad796a837979d2575e7f7b7763  musteri.csv
4835794a43106305a6a22829ec5cd814  hesap.csv
efcf7a75025f9fac516b7e54d2b637ba  islem.csv
```

## Sanity check (reference solution, expected 100/100)

```powershell
$ws = "$env:TEMP\td2-ref"; New-Item -ItemType Directory -Force "$ws\cikti" | Out-Null
Copy-Item C:\projeler\TestSkills\evals\keys\testdata2_ref\*.py "$ws\cikti"
python "$ws\cikti\uret.py" "$ws\cikti\uretilen"
$env:MASKE_ANAHTARI = "pusula-uat-2026"
python "$ws\cikti\maskele.py" C:\projeler\TestSkills\evals\trial-testdata2\girdiler\uretim_kesiti "$ws\cikti\maskeli"
python C:\projeler\TestSkills\evals\keys\testdata2_grade.py $ws
```
