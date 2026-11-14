#!/usr/bin/env python3
"""Turn the k6 summary written by a generate_k6.py script into a verdict in qa/results.json.

The generated script exports handleSummary(), which writes <spec id>-summary.json (override with
-e K6_SUMMARY=path). This converter reads that file and records the result under the test case, so
the load-test verdict reaches the RTM row of its requirement.

Verdict of one run:
  failed   a threshold was breached (the breached thresholds and observed values go into "errors")
  blocked  no verdict is possible: the run ended before the planned duration, a thresholded
           response-time metric has no successful sample, or k6 exited with an error (--exit-code)
  not-run  a smoke run met its thresholds: it shows the script works, not that the requirement is met
  passed   every threshold was met on the steady state of a load, stress, spike or soak run
Several summaries of one test case roll up: failed > blocked > passed > not-run.

The test case is --test, else "test_id" of the spec, else (with --tests) the only performance test
case linked to the spec's requirement_ids. With --tests the script also checks that the test case
exists and traces to those requirements; otherwise the result would never appear in the RTM.
Existing entries of --out that are not touched (manual, Playwright) and linked defect keys are kept.

Usage:
  k6 run -e BASE_URL=https://staging.example.com perf/DS-010.k6.js ; echo $?
  python k6_results.py perf/DS-010-summary.json --out qa/results.json --tests qa/test-cases.json [--run "RC2 load"]
  python k6_results.py DS-010-summary.json --out qa/results.json --test TC-027 --exit-code 99 --strict
Exit codes: 0 written, 1 with --strict when a recorded verdict is not "passed", 2 unusable input.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

TC = re.compile(r"^TC-\d{3,}$")
ORDER = {"failed": 3, "blocked": 2, "passed": 1, "not-run": 0}
MS_METRIC = re.compile(r"^qa_([a-z_]+?)_ms_(.+)$")


class InputError(ValueError):
    pass


def num(x) -> str:
    return f"{round(float(x), 2):g}" if isinstance(x, (int, float)) and not isinstance(x, bool) else str(x)


def load_summary(path: Path) -> dict:
    try:
        doc = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as e:
        raise InputError(f"{path}: {e}")
    if not isinstance(doc, dict) or not isinstance(doc.get("metrics"), dict):
        raise InputError(f"{path}: not a summary written by a generate_k6.py script (no 'metrics' object). "
                         "The --summary-export file is not supported: its format differs between k6 versions")
    if not isinstance(doc.get("qa_suite"), dict):
        raise InputError(f"{path}: no 'qa_suite' block; regenerate the script with generate_k6.py and rerun")
    return doc


def thresholds_of(metrics: dict) -> list[tuple[str, str, bool]]:
    out = []
    for name in sorted(metrics):
        th = (metrics[name] or {}).get("thresholds") or {}
        for expr in sorted(th):
            v = th[expr]
            if not isinstance(v, dict) or not isinstance(v.get("ok"), bool):
                raise InputError(f"threshold '{name}: {expr}' has no boolean 'ok': not a handleSummary() file")
            out.append((name, expr, v["ok"]))
    return out


def samples(metric: dict) -> float | None:
    """Number of samples of a trend, None when the summary does not tell."""
    v = (metric or {}).get("values") or {}
    if isinstance(v.get("count"), (int, float)):
        return float(v["count"])
    if v and all(isinstance(x, (int, float)) and x == 0 for x in v.values()):
        return 0.0
    return None


def evaluate(doc: dict, exit_code: int | None) -> dict:
    """One summary -> {status, note, errors, performance}."""
    qa, metrics = doc["qa_suite"], doc["metrics"]
    th = thresholds_of(metrics)
    if not th:
        raise InputError("the summary contains no thresholds, so there is no pass/fail criterion")
    verdict_phases = list(qa.get("verdict_phases") or ["steady"])
    phase_s = {p["name"]: 0.0 for p in qa.get("phases") or []}
    for p in qa.get("phases") or []:
        phase_s[p["name"]] += p["end_s"] - p["start_s"]
    breached = []
    for name, expr, ok in th:
        if not ok:
            vals = (metrics[name].get("values") or {})
            shown = ", ".join(f"{k}={num(v)}" for k, v in sorted(vals.items()) if k in ("rate", "count", "p(95)", "p(99)"))
            breached.append(f"{name}: {expr} breached" + (f" ({shown})" if shown else ""))
    planned_ms = float(qa.get("planned_duration_s") or 0) * 1000
    actual_ms = float((doc.get("state") or {}).get("testRunDurationMs") or 0)
    reasons = []
    if exit_code is not None and exit_code not in (0, 99):
        reasons.append(f"k6 exited with {exit_code} (not 0 or 99): the run did not complete normally")
    if planned_ms and actual_ms < 0.98 * planned_ms:
        reasons.append(f"the run ended after {num(actual_ms / 1000)} s of {num(planned_ms / 1000)} s planned")
    empty = []
    for name, expr, _ in th:
        mm = MS_METRIC.match(name)
        if mm and samples(metrics[name]) == 0 and name not in empty:
            empty.append(name)
    if empty:
        reasons.append("no successful sample for " + ", ".join(empty) + ": its response-time threshold was not evaluated")
    for ph in verdict_phases:
        it = ((metrics.get(f"qa_{ph}_iterations") or {}).get("values") or {}).get("count")
        if it == 0 or (it is None and f"qa_{ph}_iterations" not in metrics):
            reasons.append(f"no journey completed in the {ph} phase")
    profile = qa.get("profile", "")
    if reasons:
        status, note = "blocked", "no verdict: " + "; ".join(reasons)
        if breached:
            note += f" ({len(breached)} threshold(s) also breached)"
    elif breached:
        status, note = "failed", f"k6 {profile}: {len(breached)} of {len(th)} thresholds breached"
    elif profile == "smoke":
        status, note = "not-run", "k6 smoke run met its thresholds: the script works; run the load profile for a verdict"
    else:
        status, note = "passed", f"k6 {profile}: all {len(th)} thresholds met on the {' and '.join(verdict_phases)} phase"
    if exit_code == 0 and breached:
        note += "; WARNING: k6 exit code 0 but the summary shows breached thresholds"
    if exit_code == 99 and not breached:
        note += "; WARNING: k6 exit code 99 but the summary shows no breached threshold (wrong summary file?)"

    perf: dict = {"spec": qa.get("spec_id", ""), "profile": profile, "model": qa.get("model", ""),
                  "requirements": list(qa.get("requirement_ids") or []), "run_s": round(actual_ms / 1000, 1)}
    first = verdict_phases[0]
    it = ((metrics.get(f"qa_{first}_iterations") or {}).get("values") or {}).get("count")
    if isinstance(it, (int, float)) and phase_s.get(first):
        perf["achieved_journeys_per_s"] = round(it / phase_s[first], 2)
    target = qa.get("target") or {}
    if "journeys_per_s" in target:
        perf["target_journeys_per_s"] = target["journeys_per_s"]
    if "vus" in target:
        perf["target_vus"] = target["vus"]
    dropped = ((metrics.get("dropped_iterations") or {}).get("values") or {}).get("count")
    perf["dropped_iterations"] = int(dropped) if isinstance(dropped, (int, float)) else 0
    for ph in qa.get("measured_phases") or verdict_phases:
        block: dict = {}
        rate = ((metrics.get(f"qa_{ph}_failed") or {}).get("values") or {}).get("rate")
        if isinstance(rate, (int, float)):
            block["error_rate"] = round(rate, 5)
        reqs = {}
        for name in sorted(metrics):
            mm = MS_METRIC.match(name)
            if mm and mm.group(1) == ph:
                v = metrics[name].get("values") or {}
                reqs[mm.group(2)] = {k2: round(v[k], 1) for k, k2 in (("p(95)", "p95_ms"), ("p(99)", "p99_ms"), ("count", "count"))
                                     if isinstance(v.get(k), (int, float))}
        if reqs:
            block["requests"] = reqs
        if block:
            perf.setdefault("phases", {})[ph] = block
    perf["thresholds"] = {f"{n}: {e}": ok for n, e, ok in th}
    return {"status": status, "note": note, "errors": breached[:10], "performance": perf, "duration_ms": round(actual_ms)}


def resolve_tc(qa: dict, forced: str | None, tests: dict | None, where: str) -> tuple[str, list[str]]:
    """(TC ID, warnings). InputError when the result cannot be attached to exactly one test case."""
    reqs = list(qa.get("requirement_ids") or [])
    warnings: list[str] = []
    tid = forced or qa.get("test_id") or ""
    if not tid and tests is not None:
        cands = sorted(k for k, t in tests.items() if t.get("status") != "deprecated" and t.get("category") == "performance"
                       and set(reqs) & set(t.get("requirement_ids") or []))
        if len(cands) == 1:
            tid = cands[0]
        else:
            raise InputError(f"{where}: the spec has no test_id and {len(cands)} performance test cases trace to "
                             f"{', '.join(reqs) or 'its requirements'}; pass --test TC-###")
    if not tid:
        raise InputError(f"{where}: no test case: add \"test_id\" to the spec, or pass --test TC-### or --tests")
    if not TC.match(tid):
        raise InputError(f"{where}: {tid!r} is not a TC ID (TC-###)")
    if tests is not None:
        if tid not in tests:
            raise InputError(f"{where}: {tid} is not in the test cases; the result would never reach the RTM")
        linked = set(tests[tid].get("requirement_ids") or [])
        missing = [r for r in reqs if r not in linked]
        if missing:
            warnings.append(f"{tid} does not trace to {', '.join(missing)} (spec {qa.get('spec_id', '')}): "
                            "the RTM will not show this result under that requirement")
    return tid, warnings


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("summaries", nargs="+", help="summary JSON file(s) written by the generated k6 script")
    ap.add_argument("--out", required=True, help="QA Suite results.json to create or update")
    ap.add_argument("--test", help="TC ID to record the result under (default: test_id of the spec)")
    ap.add_argument("--tests", help="qa/test-cases.json: checks the TC exists and traces to the spec's requirements")
    ap.add_argument("--exit-code", dest="exit_code", type=int, help="exit code of the k6 run (0, 99 = thresholds; others = error)")
    ap.add_argument("--run", help="run label")
    ap.add_argument("--strict", action="store_true", help="exit 1 unless every recorded verdict is 'passed'")
    sys.stdout.reconfigure(encoding="utf-8")
    a = ap.parse_args()
    if a.test and len(a.summaries) > 1:
        print("error: --test names one test case; pass one summary, or put test_id into each spec", file=sys.stderr)
        return 2
    try:
        tests = None
        if a.tests:
            try:
                tc = json.loads(Path(a.tests).read_text(encoding="utf-8-sig"))
            except (OSError, ValueError) as e:
                raise InputError(f"--tests: {e}")
            tests = {t["id"]: t for t in (tc.get("test_cases", []) if isinstance(tc, dict) else tc) if isinstance(t, dict) and t.get("id")}
        per_tc: dict[str, list[dict]] = {}
        warnings: list[str] = []
        for s in a.summaries:
            doc = load_summary(Path(s))
            tid, w = resolve_tc(doc["qa_suite"], a.test, tests, s)
            warnings += w
            try:
                per_tc.setdefault(tid, []).append(evaluate(doc, a.exit_code))
            except InputError as e:
                raise InputError(f"{s}: {e}")
        out = Path(a.out)
        doc = {}
        if out.exists():
            try:
                doc = json.loads(out.read_text(encoding="utf-8-sig"))
            except ValueError as e:
                raise InputError(f"--out {out}: {e}")
            if not isinstance(doc, dict):
                raise InputError(f"--out {out}: not a results.json object")
    except InputError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    merged = dict(doc.get("results") or {})
    lines = []
    for tid in sorted(per_tc):
        runs = per_tc[tid]
        worst = max(runs, key=lambda r: ORDER[r["status"]])
        entry = {"status": worst["status"], "source": "k6",
                 "projects": {r["performance"]["profile"] or "k6": r["status"] for r in runs},
                 "duration_ms": sum(r["duration_ms"] for r in runs), "note": worst["note"],
                 "performance": worst["performance"] if len(runs) == 1 else [r["performance"] for r in runs]}
        errors = [e for r in runs for e in r["errors"]]
        if errors:
            entry["errors"] = errors[:10]
        old = merged.get(tid) or {}
        if old.get("defects"):
            entry["defects"] = old["defects"]
        merged[tid] = entry
        lines.append(f"{tid}: {entry['status']} - {entry['note']}")
    stamp = datetime.now(timezone.utc).isoformat()[:16].replace("T", " ")
    new = {**doc, "run": a.run or doc.get("run") or f"k6 {stamp}", "results": dict(sorted(merged.items()))}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(new, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {out}: {len(per_tc)} test case(s) from k6")
    for ln in lines:
        print(f"  {ln}")
    for w in warnings:
        print(f"warning: {w}", file=sys.stderr)
    if a.strict and any(merged[t]["status"] != "passed" for t in per_tc):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
