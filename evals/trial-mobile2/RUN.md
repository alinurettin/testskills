# RUN — trial-mobile2 (EVALUATOR ONLY, never give this file to the agent)

**Kind:** document review of a mobile app test plan. There is no device and no server. Nothing listens on a port, nothing is time-sensitive, and there is no state to reset.

**Key and grader:**
- `C:\projeler\TestSkills\evals\keys\mobile2.md`
- `C:\projeler\TestSkills\evals\keys\mobile2_grade.py` (Python 3, standard library only)

## 1. Files to give the agent

Copy only these into a fresh, empty workspace:

```
TASK.md
girdiler\urun_ozeti_v4.3.md
girdiler\test_plani_v4.3.md
girdiler\cihaz_kullanim_2026-08.csv
```

Do **not** copy `RUN.md`, and do not copy anything from `evals\keys\`. Do not give access to the rest of the repository; the with-skill arm gets only the skill package.

PowerShell, one workspace per run:

```powershell
$run = "C:\trials\mobile2-run01"          # new folder for every run
New-Item -ItemType Directory -Force "$run\girdiler" | Out-Null
$src = "C:\projeler\TestSkills\evals\trial-mobile2"
Copy-Item "$src\TASK.md" $run
Copy-Item "$src\girdiler\*" "$run\girdiler\"
```

Parallel runs need nothing special: each run has its own folder and there are no ports.

## 2. Prompt to the agent

Start the agent with its working directory set to the workspace. Use this prompt:

> `TASK.md` dosyasındaki isteği yerine getir. Girdiler `girdiler/` klasöründe; çıktıları bu klasörün köküne yaz.

Recommended time box: 30 minutes. A strong agent needs about 20–30 minutes. Opus and Haiku get the same prompt and the same inputs.

## 3. After the run

Collect `plan_inceleme.md` and `cihaz_matrisi.csv` from the workspace root. The grader also searches subfolders, but it ignores `girdiler\`.

```powershell
python C:\projeler\TestSkills\evals\keys\mobile2_grade.py grade C:\trials\mobile2-run01
python C:\projeler\TestSkills\evals\keys\mobile2_grade.py grade C:\trials\mobile2-run01 --json > C:\trials\mobile2-run01.grade.json
```

The script prints:
- the objective matrix scores M1–M4, where M4 must be confirmed by reading;
- the F1 file checks;
- keyword hints that locate candidate passages for K1–K12 and T1–T4.

Score K, T, M5, F2 and false positives by hand with `mobile2.md`. Grade blind: hide the arm (skill or no skill) and the model from the grader.

## 4. Sanity checks for the evaluator (optional)

```powershell
python C:\projeler\TestSkills\evals\keys\mobile2_grade.py verify     # 62 checks, exit code 0
python C:\projeler\TestSkills\evals\keys\mobile2_grade.py selftest   # sample matrices, "SELFTEST OK"
```

`--trial <path>` points the script at a relocated copy of this folder. The default is `..\trial-mobile2` relative to the script.

## 5. Stop / reset

Nothing runs in the background. Delete the run workspace when you are done.
