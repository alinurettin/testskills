#!/usr/bin/env python3
"""Collect the facts a test plan needs from the QA Suite artifacts, so the plan's numbers are real.

Reads qa/requirements.json, qa/test-cases.json and, when present, qa/clarifications.md,
qa/design/*.json (pairwise specs -> environment matrix) and qa/results.json.
Prints Markdown (default) or JSON with:
  scope (requirements by type/status, derived), risk distribution and top risks,
  tests by priority/technique/category/polarity, automation candidates,
  environment matrix from pairwise specs, open/blocking questions,
  a transparent manual-execution effort estimate (heuristic, parameters shown).

Usage:
  python plan_facts.py --qa qa [--format md|json] [--min-per-step 2] [--min-per-test 5] [--cycles 2]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path


def load(p: Path, key: str) -> list:
    if not p.exists():
        return []
    d = json.loads(p.read_text(encoding="utf-8-sig"))
    return d.get(key, []) if isinstance(d, dict) else d


def risk(r: dict) -> tuple[int, str]:
    rk = r.get("risk") or {}
    try:
        s = int(rk.get("likelihood", 0)) * int(rk.get("impact", 0))
    except (TypeError, ValueError):
        s = 0
    if not s:
        s = {"critical": 20, "high": 12, "medium": 6, "low": 2}.get(r.get("priority"), 0)
    lvl = "critical" if s >= 17 else "high" if s >= 10 else "medium" if s >= 5 else "low" if s else "-"
    return s, lvl


def questions(md: Path) -> dict:
    if not md.exists():
        return {"total": 0, "blocking": 0, "ids": []}
    rows = [l for l in md.read_text(encoding="utf-8").splitlines() if re.match(r"^\|\s*Q-\d+", l)]
    blocking = [l for l in rows if re.search(r"bloke|blocking", l, re.I)]
    closed = [l for l in rows if re.search(r"\|\s*(closed|kapalı|cevaplandı|answered)\s*\|", l, re.I)]
    return {"total": len(rows), "blocking": len(blocking), "closed": len(closed),
            "blocking_ids": [re.match(r"^\|\s*(Q-\d+)", l).group(1) for l in blocking]}


def environments(design: Path) -> list[dict]:
    envs = []
    for f in sorted(design.glob("*.json")) if design.exists() else []:
        try:
            spec = json.loads(f.read_text(encoding="utf-8-sig"))
        except ValueError:
            continue
        if isinstance(spec, dict) and "parameters" in spec and all("values" in p for p in spec["parameters"]):
            envs.append({"spec": f.name, "id": spec.get("id"), "strength": spec.get("strength", 2),
                         "parameters": {p["name"]: p["values"] for p in spec["parameters"]},
                         "constraints": len(spec.get("forbidden", []))})
    return envs


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--qa", default="qa")
    ap.add_argument("--format", choices=["md", "json"], default="md")
    ap.add_argument("--min-per-step", type=float, default=2.0, help="manual minutes per step")
    ap.add_argument("--min-per-test", type=float, default=5.0, help="setup/reporting minutes per test")
    ap.add_argument("--cycles", type=int, default=2, help="planned execution cycles (1st run + retest/regression)")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    qa = Path(a.qa)
    reqs = load(qa / "requirements.json", "requirements")
    tests = [t for t in load(qa / "test-cases.json", "test_cases") if t.get("status") != "deprecated"]
    if not reqs and not tests:
        print(f"error: no requirements.json / test-cases.json under {qa}", file=sys.stderr)
        return 2
    in_scope = [r for r in reqs if r.get("status") not in ("deferred", "deprecated")]
    rl = {r["id"]: risk(r) for r in reqs}
    top = sorted(in_scope, key=lambda r: -rl[r["id"]][0])[:5]
    manual_minutes = sum(a.min_per_test + a.min_per_step * len(t.get("steps", [])) for t in tests)
    auto = [t for t in tests if (t.get("automation") or {}).get("candidate")]
    facts = {
        "requirements": {"total": len(reqs), "in_scope": len(in_scope),
                         "by_type": dict(Counter(r.get("type", "?") for r in in_scope)),
                         "by_status": dict(Counter(r.get("status", "?") for r in reqs)),
                         "derived": sum(1 for r in in_scope if r.get("derived")),
                         "nfr_characteristics": sorted({r["quality_characteristic"] for r in in_scope if r.get("quality_characteristic")})},
        "risk": {"distribution": dict(Counter(rl[r["id"]][1] for r in in_scope)),
                 "top": [{"id": r["id"], "title": r.get("title", ""), "score": rl[r["id"]][0], "level": rl[r["id"]][1]} for r in top]},
        "tests": {"total": len(tests), "by_priority": dict(Counter(t.get("priority", "?") for t in tests)),
                  "by_technique": dict(Counter(t.get("technique", "?") for t in tests).most_common()),
                  "by_category": dict(Counter(t.get("category", "functional") for t in tests)),
                  "by_polarity": dict(Counter(t.get("polarity", "?") for t in tests)),
                  "smoke": sum(1 for t in tests if "smoke" in t.get("tags", [])),
                  "automation_candidates": len(auto)},
        "environments": environments(qa / "design"),
        "questions": questions(qa / "clarifications.md"),
        "effort_estimate": {"method": f"per test {a.min_per_test} min + {a.min_per_step} min per step, x {a.cycles} cycles "
                                      "(heuristic; calibrate with your team's history)",
                            "manual_hours_one_cycle": round(manual_minutes / 60, 1),
                            "manual_hours_total": round(manual_minutes * a.cycles / 60, 1),
                            "manual_hours_if_candidates_automated": round(
                                sum(a.min_per_test + a.min_per_step * len(t.get("steps", [])) for t in tests if t not in auto) * a.cycles / 60, 1)},
    }
    if a.format == "json":
        print(json.dumps(facts, ensure_ascii=False, indent=2))
        return 0
    f = facts
    o = ["# Test plan facts (computed from QA artifacts)", "",
         f"- Requirements in scope: {f['requirements']['in_scope']} / {f['requirements']['total']} "
         f"(derived {f['requirements']['derived']}) · by type: {f['requirements']['by_type']}",
         f"- Status: {f['requirements']['by_status']}",
         f"- Non-functional characteristics named: {', '.join(f['requirements']['nfr_characteristics']) or 'none'}",
         f"- Risk distribution: {f['risk']['distribution']}",
         "- Top risks: " + "; ".join(f"{x['id']} {x['title']} ({x['level']} {x['score']})" for x in f["risk"]["top"]),
         f"- Tests: {f['tests']['total']} · priority {f['tests']['by_priority']} · polarity {f['tests']['by_polarity']}",
         f"- Techniques: {f['tests']['by_technique']}",
         f"- Categories: {f['tests']['by_category']} · smoke {f['tests']['smoke']} · automation candidates {f['tests']['automation_candidates']}",
         f"- Open questions: {f['questions']['total']} (blocking {f['questions']['blocking']}: {', '.join(f['questions'].get('blocking_ids', [])) or '-'})"]
    for e in f["environments"]:
        o.append(f"- Environment matrix {e['id'] or e['spec']} (t={e['strength']}, {e['constraints']} constraints): "
                 + "; ".join(f"{k}: {', '.join(map(str, v))}" for k, v in e["parameters"].items()))
    ee = f["effort_estimate"]
    o += [f"- Manual execution effort: {ee['manual_hours_one_cycle']} h per cycle, {ee['manual_hours_total']} h total; "
          f"{ee['manual_hours_if_candidates_automated']} h if all automation candidates are automated",
          f"  - method: {ee['method']}"]
    print("\n".join(o))
    return 0


if __name__ == "__main__":
    sys.exit(main())
