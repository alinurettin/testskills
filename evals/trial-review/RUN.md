# RUN — trial-review (manual test-suite review, .xlsx)

Kind of testing: **review of an existing manual test suite** delivered as Excel.
Answer key: `../keys/review.md` (never give it, this file, or `tools/` to the agent under test).

## What runs

Nothing needs to be started or stopped. There is no server, no port, and no state:
- `PORT` is not used by this trial. (It does not start a server, so there is no default port.)
- Every run works on its own copy of the inputs, so any number of runs can go in parallel without affecting each other.

Requirements for the evaluator helpers: Python 3 (stdlib only). The agent may use whatever it has. Reading the `.xlsx` with a stdlib zip/XML reader is enough.

## Per run

1. Create a fresh, empty working directory for the run, e.g. `runs/<variant>-<n>/` (variant = `with-skill` / `no-skill`).
2. Copy **only** these items into it, keeping the relative paths:
   - `TASK.md`
   - `inputs/FAST_Transfer_Test_Cases.xlsx`
   - `inputs/US-214_FAST_Transfer.md`
3. Start the agent with that directory as its working directory. Use the full text of `TASK.md` as the prompt, or say "TASK.md dosyasındaki görevi yap."
4. Time box: 25 minutes. A strong agent should finish in about 15 to 25 minutes.
5. Collect the results from the run directory:
   - `inceleme-raporu.md` (required)
   - an optional corrected workbook, e.g. `FAST_Transfer_Test_Cases_duzeltilmis.xlsx`
6. Check that the original workbook was not changed. The task says not to change it, and the key file scores this:
   ```
   python -c "import hashlib,sys;print(hashlib.sha256(open(sys.argv[1],'rb').read()).hexdigest())" runs/<variant>-<n>/inputs/FAST_Transfer_Test_Cases.xlsx
   ```
   Expected: `db575e8812c705335c0d18a0653197ca4f7f34e49488cfd01973423eab0a0328`
7. Grade `inceleme-raporu.md` against `../keys/review.md`.

## Evaluator helpers (stdlib, in `tools/`)

| Command (run from this folder) | Purpose |
|---|---|
| `python -B tools/dump_xlsx.py inputs/FAST_Transfer_Test_Cases.xlsx --check` | Checks the structure: 2 sheets, the header row, 40 unique test IDs and multi-line step cells. Expected output: `OK: sheets=['Test Cases', 'Bilgi'] test_cases=40 multiline_step_cells=40` |
| `python -B tools/dump_xlsx.py inputs/FAST_Transfer_Test_Cases.xlsx` | Prints every row as text, so graders can read the suite without Excel |
| `python -B tools/gen_xlsx.py inputs/FAST_Transfer_Test_Cases.xlsx` | Rebuilds the workbook byte for byte (same SHA-256 as above) if it was damaged |

`inputs/US-214_FAST_Transfer.md` SHA-256: `03fd15406a17bb5473ca7722950a76a4b31d7455e62f1ed4ca74d1e8e67047ee`

## Files

```
trial-review/
  TASK.md                              # the user request (Turkish); hand to the agent
  RUN.md                               # this file; evaluator only
  inputs/
    FAST_Transfer_Test_Cases.xlsx      # 40 test cases, sheets "Test Cases" + "Bilgi"; hand to the agent
    US-214_FAST_Transfer.md            # user story + AC-1..AC-10; hand to the agent
  tools/
    dump_xlsx.py                       # evaluator only
    gen_xlsx.py                        # evaluator only
```

All companies, people, IBANs, and IDs are fictional or synthetic. The IBANs use unassigned bank codes 00987/00991/00994. The TCKN in the workbook deliberately fails the checksum. Domains use `example.com` / `example.test`.
