#!/usr/bin/env python3
"""Convert a Playwright JSON report into QA Suite results.json (keyed by TC IDs).

TC IDs are read from each test's tags (the JSON report lists them without "@",
e.g. "TC-001") and, as a fallback, from the title. A TC run in several projects
(chromium, firefox, ...) is aggregated: failed if any project failed, passed if
at least one passed and none failed (flaky runs are passed but flagged),
otherwise skipped. Skeletons still marked with test.fixme(...) become
"not-run" with note "not implemented". Tests marked test.fail(...) for a known
product defect stay "failed" for the requirement (Playwright calls them
"expected"); if such a test starts passing it is reported as passed with a
note to remove the mark.

Existing entries of --out that this report does not mention (e.g. manual results)
are kept.

Usage:
  python pw_results.py automation/test-results/results.json --out qa/results.json [--run "Sprint 14 RC2"]
Then:  python build_rtm.py --requirements qa/requirements.json --tests qa/test-cases.json --results qa/results.json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

TC = re.compile(r"\bTC-\d{3,}\b")


def walk(suite: dict, out: list):
    for spec in suite.get("specs", []):
        out.append(spec)
    for child in suite.get("suites", []):
        walk(child, out)


def first_error(test: dict) -> str:
    for r in test.get("results", []):
        errs = r.get("errors") or ([r["error"]] if r.get("error") else [])
        for e in errs:
            msg = (e.get("message") or e.get("value") or "").strip()
            if msg:
                msg = re.sub(r"\x1b\[[0-9;]*m", "", msg)
                return msg.splitlines()[0][:300]
    return ""


def classify(test: dict) -> str:
    status = test.get("status")
    anns = {a.get("type") for a in test.get("annotations", [])}
    if status == "skipped":
        return "fixme" if "fixme" in anns else "skipped"
    if "fail" in anns:
        # test.fail(...) marks a known product defect: Playwright reports the (expected) failure as
        # "expected". For requirements it is still a failure. If it unexpectedly passes, the bug looks fixed.
        return "known-defect" if status == "expected" else "fixed-known-defect"
    return {"expected": "passed", "unexpected": "failed", "flaky": "flaky"}.get(status, "failed")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("report", help="Playwright JSON report (reporter 'json')")
    ap.add_argument("--out", required=True, help="QA Suite results.json to create or update")
    ap.add_argument("--run", help="run label (default: report start time)")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    try:
        rep = json.loads(Path(a.report).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    specs: list = []
    for s in rep.get("suites", []):
        walk(s, specs)

    per_tc: dict[str, dict] = {}
    untagged = []
    for spec in specs:
        ids = sorted({t.lstrip("@") for t in spec.get("tags", []) if TC.fullmatch(t.lstrip("@"))} or set(TC.findall(spec.get("title", ""))))
        if not ids:
            untagged.append(spec.get("title", "?"))
            continue
        for test in spec.get("tests", []):
            kind = classify(test)
            dur = sum(r.get("duration", 0) for r in test.get("results", []))
            for tid in ids:
                e = per_tc.setdefault(tid, {"projects": {}, "errors": [], "duration_ms": 0,
                                            "file": f"{spec.get('file', '')}:{spec.get('line', '')}"})
                e["projects"][test.get("projectName") or "default"] = kind
                e["duration_ms"] += dur
                if kind == "failed":
                    err = first_error(test)
                    if err and err not in e["errors"]:
                        e["errors"].append(err)

    results = {}
    counts: dict[str, int] = {}
    for tid, e in sorted(per_tc.items()):
        kinds = set(e["projects"].values())
        if kinds & {"failed", "known-defect"}:
            status = "failed"
        elif kinds & {"passed", "flaky", "fixed-known-defect"}:
            status = "passed"
        elif kinds == {"fixme"}:
            status = "not-run"
        else:
            status = "skipped"
        entry = {"status": status, "source": "playwright", "projects": e["projects"],
                 "duration_ms": round(e["duration_ms"]), "spec": e["file"]}
        if "flaky" in kinds:
            entry["flaky"] = True
        if "known-defect" in kinds:
            entry["note"] = "known product defect (test.fail): expected behaviour still not met"
        if "fixed-known-defect" in kinds:
            entry["note"] = "test.fail test now passes: defect looks fixed, remove test.fail and re-verify"
        if kinds == {"fixme"}:
            entry["note"] = "not implemented (test.fixme skeleton)"
        if e["errors"]:
            entry["errors"] = e["errors"][:3]
        results[tid] = entry
        counts[status] = counts.get(status, 0) + 1

    out = Path(a.out)
    doc = {}
    if out.exists():
        doc = json.loads(out.read_text(encoding="utf-8-sig"))
    merged = dict(doc.get("results", {}))
    for tid, entry in results.items():
        old = merged.get(tid, {})
        if old.get("defects"):
            entry["defects"] = old["defects"]  # keep manually linked defect keys
        merged[tid] = entry
    start = (rep.get("stats") or {}).get("startTime") or datetime.now(timezone.utc).isoformat()
    doc = {"run": a.run or f"Playwright {start[:16].replace('T', ' ')}", "results": dict(sorted(merged.items()))}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"wrote {out}: {len(results)} test cases from Playwright · " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())))
    if untagged:
        print(f"warning: {len(untagged)} Playwright tests carry no TC-### tag (not traceable): "
              + "; ".join(untagged[:5]) + (" …" if len(untagged) > 5 else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
