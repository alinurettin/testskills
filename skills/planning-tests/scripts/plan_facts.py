#!/usr/bin/env python3
"""Collect the facts a test plan needs from the QA Suite artifacts, so the plan's numbers are real.

Reads qa/requirements.json, qa/test-cases.json and, when present, qa/clarifications.md,
qa/design/*.json (pairwise specs -> environment matrix) and qa/results.json.
Prints Markdown (default) or JSON with:
  scope (requirements by type/status, derived), risk distribution and top risks (L and I shown separately),
  tests by priority/technique/category/polarity, automation candidates,
  environment matrix from pairwise specs, open/blocking questions,
  entry readiness (requirements ready, blocking questions open, high/critical requirements without tests),
  a three-point effort estimate: optimistic / most likely / pessimistic hours, E = (a + 4m + b) / 6 and
  SD = (b - a) / 6, with every assumption named so the team can replace it with its own history.

The most likely value: manual execution of the tests that are not automated yet (measured duration_ms of
manual results when present, else minutes per test and per step, calibrated by the measured tests), times
the configuration and cycle factors, plus defect handling. Automation build effort is listed separately.

Usage:
  python plan_facts.py --qa qa [--format md|json] [--min-per-step 2] [--min-per-test 5] [--cycles 2]
      [--retest-share 0.5] [--configurations 1] [--config-share 0.3] [--defect-handling-pct 25]
      [--optimistic 0.7] [--pessimistic 1.8] [--automation-hours-per-test 2]
Exit code: 0 ok, 2 unreadable input or invalid option.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path

MANUAL_SOURCES = {"", "manual", "exploratory"}


def load(p: Path, key: str):
    if not p.exists():
        return [] if key != "results" else {}
    d = json.loads(p.read_text(encoding="utf-8-sig"))
    return d.get(key, [] if key != "results" else {}) if isinstance(d, dict) else d


def norm(v) -> str:
    return re.sub(r"[\s_]+", "-", str(v if v is not None else "").strip().lower())


def risk_of(r: dict) -> tuple[int, str]:
    """(score, level) of a requirement. Keep identical in plan_facts, completion_report, build_rtm, select_regression.

    The score (likelihood x impact) only orders requirements. The level comes from the score bands plus two
    matrix overrides, because ordinal scales do not multiply (CTAL-TM v3.0 section 1.3.3): impact 5 is at least
    high, and impact 5 with likelihood >= 3 is critical. Without both values the level falls back to the priority."""
    rk = r.get("risk") if isinstance(r.get("risk"), dict) else {}
    try:
        li, im = int(rk.get("likelihood") or 0), int(rk.get("impact") or 0)
    except (TypeError, ValueError):
        li = im = 0
    score = li * im
    if not score:
        im = 0
        score = {"critical": 20, "high": 12, "medium": 6, "low": 2}.get(r.get("priority"), 0)
    level = "critical" if score >= 17 else "high" if score >= 10 else "medium" if score >= 5 else "low" if score else "-"
    if im >= 5 and level != "critical":
        level = "critical" if li >= 3 else "high"
    return score, level


risk = risk_of  # earlier name


def is_automated(res: dict) -> bool:
    """Same rule as completion_report.py: a tool wrote the last result and really ran the test."""
    return norm(res.get("source")) not in MANUAL_SOURCES and norm(res.get("status")) in ("passed", "failed", "blocked")


def questions(md: Path) -> dict:
    if not md.exists():
        return {"total": 0, "blocking": 0, "closed": 0, "blocking_ids": [], "blocking_open": 0, "blocking_open_ids": []}
    rows = [l for l in md.read_text(encoding="utf-8-sig").splitlines() if re.match(r"^\|\s*Q-\d+", l)]
    blocking = [l for l in rows if re.search(r"bloke|blocking", l, re.I)]
    is_closed = lambda l: re.search(r"\|\s*(closed|kapalı|cevaplandı|answered|resolved)\s*\|", l, re.I)
    qid = lambda l: re.match(r"^\|\s*(Q-\d+)", l).group(1)
    still = [l for l in blocking if not is_closed(l)]
    return {"total": len(rows), "blocking": len(blocking), "closed": sum(1 for l in rows if is_closed(l)),
            "blocking_ids": [qid(l) for l in blocking],
            "blocking_open": len(still), "blocking_open_ids": [qid(l) for l in still]}


def environments(design: Path) -> list[dict]:
    envs = []
    for f in sorted(design.glob("*.json")) if design.exists() else []:
        try:
            spec = json.loads(f.read_text(encoding="utf-8-sig"))
        except ValueError:
            continue
        params = spec.get("parameters") if isinstance(spec, dict) else None
        if isinstance(params, list) and params and all(isinstance(p, dict) and "values" in p and "name" in p for p in params):
            strength = spec.get("strength", 2) if isinstance(spec.get("strength", 2), int) else 2
            sizes = sorted((len(p["values"]) for p in params), reverse=True)
            envs.append({"spec": f.name, "id": spec.get("id"), "strength": strength,
                         "parameters": {p["name"]: p["values"] for p in params},
                         "constraints": len(spec.get("forbidden", [])),
                         # lower bound for a t-wise set: the product of the t largest parameters
                         "min_configurations": math.prod(sizes[:max(1, strength)])})
    return envs


def estimate(tests: list, results: dict, a) -> dict:
    heur = lambda t: a.min_per_test + a.min_per_step * len(t.get("steps") or [])
    res = lambda t: results.get(t["id"]) if isinstance(results.get(t["id"]), dict) else {}
    automated = [t for t in tests if is_automated(res(t))]
    manual = [t for t in tests if t not in automated]
    measured = {}
    for t in manual:
        r = res(t)
        ms = r.get("duration_ms")
        if isinstance(ms, (int, float)) and not isinstance(ms, bool) and ms > 0 and norm(r.get("status")) in ("passed", "failed"):
            measured[t["id"]] = ms / 60000
    factor = None
    if len(measured) >= 3:                               # extrapolate: calibrate the heuristic with what was measured
        factor = sum(measured.values()) / sum(heur(t) for t in manual if t["id"] in measured)
    minutes = {t["id"]: measured.get(t["id"], heur(t) * (factor or 1.0)) for t in manual}
    cycle1 = sum(minutes.values())
    config_factor = 1 + (a.configurations - 1) * a.config_share
    cycle_factor = 1 + (a.cycles - 1) * a.retest_share
    execution = cycle1 * config_factor * cycle_factor
    handling = execution * a.defect_handling_pct / 100
    m = (execution + handling) / 60
    lo, hi = m * a.optimistic, m * a.pessimistic
    expected, sd = (lo + 4 * m + hi) / 6, (hi - lo) / 6
    todo = [t for t in manual if (t.get("automation") or {}).get("candidate")]
    saving = sum(minutes[t["id"]] for t in todo) * config_factor / 60        # manual hours saved per full cycle
    build = len(todo) * a.automation_hours_per_test
    legacy = sum(heur(t) for t in tests)
    r1 = lambda x: round(x, 1)
    assumptions = [
        f"manual execution: {a.min_per_test:g} min per test + {a.min_per_step:g} min per step"
        + (f", calibrated x{factor:.2f} by extrapolating from {len(measured)} manual results with a measured duration"
           if factor else f" (heuristic; {len(measured)} manual results have a measured duration, 3 are needed to calibrate)"),
        f"{len(automated)} tests already automated (last result written by a tool) need no manual execution",
        f"configurations: {a.configurations}; each extra configuration repeats {a.config_share:.0%} of cycle 1",
        f"cycles: {a.cycles}; each later cycle repeats {a.retest_share:.0%} of cycle 1 (confirmation tests and selected regression)",
        f"defect reporting and verification: {a.defect_handling_pct:g}% of execution time",
        f"range: optimistic = most likely x {a.optimistic:g}, pessimistic = most likely x {a.pessimistic:g}",
        "not included: test analysis and design, environment and data setup, automation build (listed separately), "
        "management and reporting",
    ]
    return {
        "method": "three-point: E = (a + 4m + b) / 6, SD = (b - a) / 6 (CTFL v4.0.1 section 5.1.4); "
                  "replace the assumptions with your team's history",
        "three_point": {"optimistic_hours": r1(lo), "most_likely_hours": r1(m), "pessimistic_hours": r1(hi),
                        "expected_hours": r1(expected), "sd_hours": r1(sd),
                        "range_hours": [r1(expected - sd), r1(expected + sd)]},
        "most_likely_breakdown": {"cycle_1_execution_hours": r1(cycle1 / 60), "configuration_factor": round(config_factor, 2),
                                  "cycle_factor": round(cycle_factor, 2), "execution_hours": r1(execution / 60),
                                  "defect_handling_hours": r1(handling / 60)},
        "basis": {"tests": len(tests), "manual_tests": len(manual), "automated_tests": len(automated),
                  "measured_manual_tests": len(measured), "extrapolation_factor": round(factor, 2) if factor else None},
        "automation": {"candidates_not_automated": len(todo), "hours_per_test": a.automation_hours_per_test,
                       "build_hours": r1(build), "manual_hours_saved_per_cycle": r1(saving),
                       "break_even_cycles": math.ceil(build / saving) if saving > 0 and build > 0 else None},
        "assumptions": assumptions,
        # kept for earlier consumers: every test manual, every cycle a full rerun, automation at no cost
        "manual_hours_one_cycle": r1(legacy / 60),
        "manual_hours_total": r1(legacy * a.cycles / 60),
        "manual_hours_if_candidates_automated": r1(
            sum(heur(t) for t in tests if not (t.get("automation") or {}).get("candidate")) * a.cycles / 60),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--qa", default="qa")
    ap.add_argument("--format", choices=["md", "json"], default="md")
    ap.add_argument("--min-per-step", type=float, default=2.0, help="manual minutes per step")
    ap.add_argument("--min-per-test", type=float, default=5.0, help="setup/reporting minutes per test")
    ap.add_argument("--cycles", type=int, default=2, help="planned execution cycles (1st run + retest/regression)")
    ap.add_argument("--retest-share", type=float, default=0.5,
                    help="share of cycle 1 repeated in each later cycle (default 0.5; 1.0 = full rerun)")
    ap.add_argument("--configurations", type=int, default=1,
                    help="environment configurations the suite runs on (default 1; see min_configurations of the pairwise specs)")
    ap.add_argument("--config-share", type=float, default=0.3,
                    help="share of cycle 1 repeated on each extra configuration (default 0.3)")
    ap.add_argument("--defect-handling-pct", type=float, default=25.0,
                    help="defect reporting and verification as %% of execution time (default 25)")
    ap.add_argument("--optimistic", type=float, default=0.7, help="optimistic = most likely x this (default 0.7)")
    ap.add_argument("--pessimistic", type=float, default=1.8, help="pessimistic = most likely x this (default 1.8)")
    ap.add_argument("--automation-hours-per-test", type=float, default=2.0,
                    help="build hours per automation candidate (default 2; API tests are usually cheaper)")
    sys.stdout.reconfigure(encoding="utf-8")
    a = ap.parse_args()
    bad = [n for n, ok in (("--optimistic must be > 0 and <= 1", 0 < a.optimistic <= 1),
                           ("--pessimistic must be >= 1", a.pessimistic >= 1),
                           ("--cycles and --configurations must be >= 1", a.cycles >= 1 and a.configurations >= 1),
                           ("--retest-share and --config-share must be between 0 and 1",
                            0 <= a.retest_share <= 1 and 0 <= a.config_share <= 1),
                           ("minutes, percentages and hours cannot be negative",
                            min(a.min_per_step, a.min_per_test, a.defect_handling_pct, a.automation_hours_per_test) >= 0))
           if not ok]
    if bad:
        print("error: " + "; ".join(bad), file=sys.stderr)
        return 2
    qa = Path(a.qa)
    try:
        reqs = load(qa / "requirements.json", "requirements")
        tests = load(qa / "test-cases.json", "test_cases")
        results = load(qa / "results.json", "results")
        qs = questions(qa / "clarifications.md")
    except (OSError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    reqs = [r for r in reqs if isinstance(r, dict) and r.get("id")] if isinstance(reqs, list) else []
    tests = [t for t in tests if isinstance(t, dict) and t.get("id") and t.get("status") != "deprecated"] \
        if isinstance(tests, list) else []
    results = results if isinstance(results, dict) else {}
    if not reqs and not tests:
        print(f"error: no requirements.json / test-cases.json under {qa}", file=sys.stderr)
        return 2
    in_scope = [r for r in reqs if r.get("status") not in ("deferred", "deprecated")]
    rl = {r["id"]: risk_of(r) for r in reqs}
    top = sorted(in_scope, key=lambda r: (-rl[r["id"]][0], r["id"]))[:5]
    auto = [t for t in tests if (t.get("automation") or {}).get("candidate")]
    tested = {q for t in tests for q in t.get("requirement_ids") or []}
    ready = [r for r in in_scope if r.get("status") == "ready"]
    untested = [r["id"] for r in in_scope if rl[r["id"]][1] in ("high", "critical") and r["id"] not in tested]
    li = lambda r, k: (r.get("risk") or {}).get(k) if isinstance(r.get("risk"), dict) else None
    facts = {
        "requirements": {"total": len(reqs), "in_scope": len(in_scope),
                         "by_type": dict(Counter(r.get("type", "?") for r in in_scope)),
                         "by_status": dict(Counter(r.get("status", "?") for r in reqs)),
                         "derived": sum(1 for r in in_scope if r.get("derived")),
                         "nfr_characteristics": sorted({r["quality_characteristic"] for r in in_scope if r.get("quality_characteristic")})},
        "risk": {"distribution": dict(Counter(rl[r["id"]][1] for r in in_scope)),
                 "unrated": sum(1 for r in in_scope if rl[r["id"]][1] == "-"),
                 "top": [{"id": r["id"], "title": r.get("title", ""), "score": rl[r["id"]][0], "level": rl[r["id"]][1],
                          "likelihood": li(r, "likelihood"), "impact": li(r, "impact")} for r in top]},
        "tests": {"total": len(tests), "by_priority": dict(Counter(t.get("priority", "?") for t in tests)),
                  "by_technique": dict(Counter(t.get("technique", "?") for t in tests).most_common()),
                  "by_category": dict(Counter(t.get("category", "functional") for t in tests)),
                  "by_polarity": dict(Counter(t.get("polarity", "?") for t in tests)),
                  "smoke": sum(1 for t in tests if "smoke" in (t.get("tags") or [])),
                  "automation_candidates": len(auto)},
        "environments": environments(qa / "design"),
        "questions": qs,
        "entry_readiness": {"requirements_ready": len(ready), "requirements_in_scope": len(in_scope),
                            "requirements_ready_pct": round(100 * len(ready) / len(in_scope), 1) if in_scope else None,
                            "blocking_questions_open": qs["blocking_open"], "blocking_open_ids": qs["blocking_open_ids"],
                            "derived_unconfirmed": sum(1 for r in in_scope if r.get("derived") and r.get("status") != "ready"),
                            "high_critical_without_tests": untested},
        "effort_estimate": estimate(tests, results, a),
    }
    if a.format == "json":
        print(json.dumps(facts, ensure_ascii=False, indent=2))
        return 0
    f = facts
    lxi = lambda x: f"L{x['likelihood']} × I{x['impact']} = {x['score']}" if x["likelihood"] and x["impact"] else f"from priority, {x['score']}"
    er = f["entry_readiness"]
    o = ["# Test plan facts (computed from QA artifacts)", "",
         f"- Requirements in scope: {f['requirements']['in_scope']} / {f['requirements']['total']} "
         f"(derived {f['requirements']['derived']}) · by type: {f['requirements']['by_type']}",
         f"- Status: {f['requirements']['by_status']}",
         f"- Non-functional characteristics named: {', '.join(f['requirements']['nfr_characteristics']) or 'none'}",
         f"- Risk distribution: {f['risk']['distribution']}"
         + (f" · unrated (no L × I, no priority): {f['risk']['unrated']}" if f["risk"]["unrated"] else ""),
         "- Top risks: " + "; ".join(f"{x['id']} {x['title']} ({x['level']}; {lxi(x)})" for x in f["risk"]["top"]),
         f"- Tests: {f['tests']['total']} · priority {f['tests']['by_priority']} · polarity {f['tests']['by_polarity']}",
         f"- Techniques: {f['tests']['by_technique']}",
         f"- Categories: {f['tests']['by_category']} · smoke {f['tests']['smoke']} · automation candidates {f['tests']['automation_candidates']}",
         f"- Open questions: {f['questions']['total']} (blocking {f['questions']['blocking']}: {', '.join(f['questions'].get('blocking_ids', [])) or '-'}; "
         f"still open: {', '.join(qs['blocking_open_ids']) or '-'})",
         f"- Entry readiness: requirements ready {er['requirements_ready']}/{er['requirements_in_scope']} "
         f"({er['requirements_ready_pct'] if er['requirements_ready_pct'] is not None else '–'}%) · blocking questions open "
         f"{er['blocking_questions_open']} · derived requirements not confirmed {er['derived_unconfirmed']} · "
         f"high/critical requirements without tests: {', '.join(er['high_critical_without_tests']) or 'none'}"]
    for e in f["environments"]:
        o.append(f"- Environment matrix {e['id'] or e['spec']} (t={e['strength']}, {e['constraints']} constraints, "
                 f"at least {e['min_configurations']} configurations): "
                 + "; ".join(f"{k}: {', '.join(map(str, v))}" for k, v in e["parameters"].items()))
    ee = f["effort_estimate"]
    tp, bd, au = ee["three_point"], ee["most_likely_breakdown"], ee["automation"]
    o += [f"- Test execution effort (three-point): **{tp['expected_hours']} h ± {tp['sd_hours']} h** "
          f"(range {tp['range_hours'][0]}–{tp['range_hours'][1]} h; optimistic {tp['optimistic_hours']} / most likely "
          f"{tp['most_likely_hours']} / pessimistic {tp['pessimistic_hours']})",
          f"  - most likely = cycle 1 {bd['cycle_1_execution_hours']} h × configurations {bd['configuration_factor']} × "
          f"cycles {bd['cycle_factor']} = {bd['execution_hours']} h execution + {bd['defect_handling_hours']} h defect handling",
          f"  - method: {ee['method']}"]
    o += [f"  - assumption: {x}" for x in ee["assumptions"]]
    o.append(f"- Automation build (separate from the estimate above): {au['candidates_not_automated']} candidates × "
             f"{au['hours_per_test']:g} h = {au['build_hours']} h; saves {au['manual_hours_saved_per_cycle']} h of manual "
             "execution per full cycle"
             + (f"; pays back after {au['break_even_cycles']} full cycles" if au["break_even_cycles"] else ""))
    print("\n".join(o))
    return 0


if __name__ == "__main__":
    sys.exit(main())
