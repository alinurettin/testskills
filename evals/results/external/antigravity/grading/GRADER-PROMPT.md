# Grading instructions

You grade the results of blind trials. Work only inside this folder. Do not use the internet. Do not
start or call any server.

- `runs.csv` lists the runs: run_id, trial, max.
- `blind/<run_id>/` holds what one agent produced in one run. You do not know how a run was set up.
  Do not try to find out, and grade every run by the same rules.
- `keys/` holds the answer keys: `design.md` (with `design_grader.py`), `api2.md`, `exploratory.md`.
  Each key has a "Scoring rubric" section. Follow it exactly: points, partial credit, penalties, caps
  and the maximum.

For each run in `runs.csv`, in order:

1. Read the key of its trial in full (once per trial is enough).
2. Read every deliverable in `blind/<run_id>/`.
3. Trial `design`: run
   `python keys/design_grader.py blind/<run_id>/cikti --json grades/<run_id>.design.json`
   then confirm the items it marks `[MANUEL ONAY]` by reading `cikti/test-tasarimi.md` as `design.md`
   describes, and adjust the score. If the `cikti` folder is missing, the score is 0.
   Trials `api2` and `exploratory`: decide each K item (full, half or none) only from the evidence
   written in the deliverables, and count each trap or other false positive as the key says. Give no
   credit for a finding that lacks the evidence the key requires.
4. Write `grades/<run_id>.json` in this form:
   {"run_id": "R01", "trial": "api2", "score": 61, "max": 100,
    "items": {"K1": "full", "K2": "half", "K3": "none"},
    "false_positives": ["T2: what the report claimed"],
    "quality_points": 9,
    "contaminated": false, "contamination_reasons": [],
    "grader_model": "the model name you were given",
    "evidence": ["K1: bulgular.md, finding 3", "T2: bulgular.md, finding 7"]}
   `score` is the final score after penalties, between 0 and `max`. List every K item of the key in
   `items`. Use null for `quality_points` when the key has no such component.
   Set `contaminated` to true and give the reason when a deliverable shows knowledge it cannot have
   from its inputs: K or T identifiers of the key, text of the key, or the source code of the test
   system.
5. Grade strictly and consistently: the same evidence gets the same decision in every run. When you
   are in doubt between two levels, choose the lower one and say why in `evidence`.

When all runs are graded, write `grades/SUMMARY.md`: one table row per run (run_id, trial, score, max)
and the three most common misses per trial. Do not edit anything in `blind/` or `keys/`.
