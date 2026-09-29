#!/usr/bin/env python3
"""Merge a JUnit XML report (Maestro, Espresso/Gradle, XCUITest via a JUnit converter, Appium runners)
into QA Suite results.json, keyed by TC ID.

The TC ID is read from each <testcase> name and classname: "TC-101", or "TC101" / "TC_101" in
method names that cannot contain a hyphen (test_TC101_draftSurvivesProcessDeath) -> TC-101.
Maestro writes the flow `name` there, so start every flow name with its TC ID.
A testcase with <failure> or <error> is failed, with <skipped> is skipped, otherwise passed
(a Maestro status attribute such as ERROR/FAILED also counts as failed).

Results are recorded per device under "projects" (like Playwright projects), so running the same
flows on several devices accumulates: a TC is failed if it failed on any device, passed if it passed
on at least one and failed on none, otherwise skipped. Existing entries of --out that this report
does not mention (manual results) are kept, and so are defect keys.

Usage:
  maestro test --format junit --output reports/pixel8.xml flows/
  python junit_results.py reports/pixel8.xml --device "Pixel 8 / Android 16" --out qa/results.json --run "RC2"
  python junit_results.py reports/iphone15.xml --device "iPhone 15 / iOS 26" --out qa/results.json
Exit codes: 0 ok, 2 unreadable report.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# TC-101, and TC101 / TC_101 for method names that cannot contain a hyphen (Espresso, XCUITest)
TC = re.compile(r"(?<![A-Za-z0-9])TC[-_]?(\d{3,})(?!\d)", re.IGNORECASE)
FAILED_STATUS = {"error", "failed", "failure"}


def classify(tc: ET.Element) -> tuple[str, str]:
    for tag in ("failure", "error"):
        el = tc.find(tag)
        if el is not None:
            msg = (el.get("message") or el.text or "").strip().splitlines()
            return "failed", (msg[0][:300] if msg else tag)
    if tc.find("skipped") is not None:
        return "skipped", ""
    if (tc.get("status") or "").lower() in FAILED_STATUS:
        return "failed", f"status {tc.get('status')}"
    return "passed", ""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("report", help="JUnit XML file")
    ap.add_argument("--out", required=True, help="QA Suite results.json to create or update")
    ap.add_argument("--device", default="default", help="device/OS label for this run, e.g. 'Pixel 8 / Android 16'")
    ap.add_argument("--source", default="junit", help="value of the 'source' field (e.g. maestro, espresso, xcuitest)")
    ap.add_argument("--run", help="run label")
    sys.stdout.reconfigure(encoding="utf-8")
    a = ap.parse_args()
    try:
        root = ET.parse(a.report).getroot()
    except (OSError, ET.ParseError) as e:
        print(f"error: cannot read {a.report}: {e}", file=sys.stderr)
        return 2
    found: dict[str, dict] = {}
    untagged = []
    for tc in root.iter("testcase"):
        label = f"{tc.get('name', '')} {tc.get('classname', '')}"
        ids = sorted({f"TC-{m}" for m in TC.findall(label)})
        if not ids:
            untagged.append(tc.get("name", "?"))
            continue
        status, err = classify(tc)
        try:
            ms = round(float(tc.get("time") or 0) * 1000)
        except ValueError:
            ms = 0
        for tid in ids:
            e = found.setdefault(tid, {"status": "skipped", "errors": [], "duration_ms": 0})
            rank = {"failed": 2, "passed": 1, "skipped": 0}
            if rank[status] > rank[e["status"]]:
                e["status"] = status
            if err and err not in e["errors"]:
                e["errors"].append(err)
            e["duration_ms"] += ms

    out = Path(a.out)
    doc = json.loads(out.read_text(encoding="utf-8-sig")) if out.exists() else {}
    merged = dict(doc.get("results", {}))
    counts: dict[str, int] = {}
    for tid, e in sorted(found.items()):
        old = merged.get(tid, {})
        projects = dict(old.get("projects", {})) if old.get("source") == a.source else {}
        projects[a.device] = e["status"]
        kinds = set(projects.values())
        status = "failed" if "failed" in kinds else "passed" if "passed" in kinds else "skipped"
        entry = {"status": status, "source": a.source, "projects": projects, "duration_ms": e["duration_ms"]}
        if e["errors"]:
            entry["errors"] = e["errors"][:3]
        elif status == "failed" and old.get("errors"):
            entry["errors"] = old["errors"]
        if old.get("defects"):
            entry["defects"] = old["defects"]
        merged[tid] = entry
        counts[e["status"]] = counts.get(e["status"], 0) + 1
    doc = {"run": a.run or doc.get("run") or f"{a.source} run", "results": dict(sorted(merged.items()))}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    print(f"wrote {out}: {len(found)} test cases from {Path(a.report).name} on '{a.device}' · "
          + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())))
    if untagged:
        print(f"warning: {len(untagged)} testcases carry no TC-### in name or classname (not traceable): "
              + "; ".join(untagged[:5]) + (" …" if len(untagged) > 5 else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
