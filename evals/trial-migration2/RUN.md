# RUN — trial-migration2 (EVALUATOR ONLY — do not give to the agent)

**Kind:** data migration testing (two related entities: policies + premium installments), Turkish context.
**Format:** file-based. **No server, no ports, no network.** Python 3 stdlib or Node.js 24 built-ins are enough for the agent; the evaluator scripts are Python 3 stdlib.
**Key:** `evals/keys/migration2.md` (+ `migration2_expected.json`, `migration2_verify.py`, `migration2_grade.py`, `migration2_generate.py`).

## 1. What the agent gets

Give the agent **only**:

- `TASK.md` (the Turkish user request — paste it as the prompt or tell the agent to read it)
- the whole `inputs/` folder:
  - `inputs/esleme_spesifikasyonu.md`
  - `inputs/kaynak/POLMAS.csv`, `inputs/kaynak/TAKSIT.csv`
  - `inputs/hedef/policies.csv`, `inputs/hedef/installments.csv`
  - `inputs/etl_calistirma_raporu.txt`

Never give: this `RUN.md`, `.gitattributes`, anything under `evals/keys/`, or any other folder of the repository (the agent's working directory must not be inside the repo, so it cannot browse the key).

## 2. Per-run setup (Windows PowerShell)

```powershell
$run = "C:\trials\migration2\run-01"          # one fresh folder per run (per arm, per model, per repetition)
New-Item -ItemType Directory -Force $run | Out-Null
Copy-Item C:\projeler\TestSkills\evals\trial-migration2\TASK.md $run
Copy-Item C:\projeler\TestSkills\evals\trial-migration2\inputs "$run\inputs" -Recurse
```

Start the agent with its working directory set to `$run`. Suggested prompt (identical for both arms):

> `TASK.md` dosyasındaki görevi tamamla. Girdiler `inputs/` klasöründe; çıktıları `cikti/` klasörüne yaz.

- With-package vs. without-package arms differ **only** in whether the QA skill package is installed.
- Parallel runs cannot interfere: every run has its own folder; there is no server, port, shared state or clock dependency (the data uses a fixed cut-off date of 30.09.2026).
- Expected effort for a strong agent: ~20–30 minutes. Suggested hard stop: 45 minutes.

## 3. Stop / reset

Nothing to stop. Reset = delete the run folder. After a run, optionally confirm the agent did not modify the inputs:

```powershell
Get-ChildItem "$run\inputs" -Recurse -File | ForEach-Object { "{0}  {1}" -f (Get-FileHash $_.FullName -Algorithm SHA256).Hash.ToLower(), $_.Name }
```

| File | Bytes | SHA-256 |
|---|---|---|
| `inputs/esleme_spesifikasyonu.md` | 9101 | `74f04dd516e7f5189ada64875551333f37fcd45875340103a9f11f3b90e944d2` |
| `inputs/etl_calistirma_raporu.txt` | 2270 | `3701a22f549611497c649342249634718444394948b076186e0613a577f5aa74` |
| `inputs/hedef/installments.csv` | 23905 | `8b7717137f7c878c7ba399ace11aeef87d3d32c631eb1c853e32c6fde3b9aa05` |
| `inputs/hedef/policies.csv` | 13339 | `6442d3c6e18088aa3c64a185cc9f18ea1a121ecd6f72b3128e44842348b133e9` |
| `inputs/kaynak/POLMAS.csv` | 12084 | `75967c1fae5ecd09c1d44a52688e6f7c45e006632c75ab7adf33e9f5032ab88a` |
| `inputs/kaynak/TAKSIT.csv` | 14570 | `331c71873fb49fcbf5235a3682604a1630f16298e38faac560e6ae3a5fc94296` |

(`.gitattributes` in this folder disables EOL conversion so the legacy files keep cp1254 + CRLF and the hashes stay stable after a git checkout.)

## 4. Expected deliverables (from TASK.md)

- `cikti/mutabakat_raporu.md` — Turkish test report with findings and a go/no-go recommendation
- `cikti/bulgular.csv` — `bulgu_id,baslik,varlik,alan,etkilenen_kayitlar,onem` (legacy keys `POL_NO` / `POL_NO/TAKSIT_NO`)
- `cikti/mutabakat.py` or `cikti/mutabakat.js` — re-runnable reconciliation script (run from the run root)

## 5. Grading

```powershell
python C:\projeler\TestSkills\evals\keys\migration2_grade.py $run --run-script
```

The script suggests points per planted item, flags probable trap hits and lists unmatched findings; a human grader then applies the acceptance rules, trap/false-positive penalties and method points in `evals/keys/migration2.md` (max 38).

## 6. Regenerating and verifying the inputs (designer / evaluator)

```powershell
python C:\projeler\TestSkills\evals\keys\migration2_generate.py   # deterministic; rewrites inputs/ except the spec
python C:\projeler\TestSkills\evals\keys\migration2_verify.py     # must end with: RESULT: ALL CHECKS PASSED
```

`migration2_verify.py` re-implements the spec independently, confirms every planted item K1–K11 reproduces on exactly the keyed records, that nothing else deviates from the spec, and that each trap T1–T4 looks wrong under a naive comparison but is spec-correct.
