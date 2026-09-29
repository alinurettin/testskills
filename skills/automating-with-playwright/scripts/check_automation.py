#!/usr/bin/env python3
"""Automation coverage report: which test cases are automated, still skeletons, missing or orphaned.

Static scan of the spec files (no Playwright run needed):
  - automated   : a "@TC-###" tag exists and no QA Suite skeleton marker mentions the ID
  - skeleton    : generated but still marked with test.fixme("QA Suite skeleton ...")
  - missing     : automation candidate (automation.candidate == true) without any spec
  - orphan      : a spec tag refers to a TC that is not in test-cases.json (or is deprecated)
  - duplicate   : the same TC tag appears in more than one test title/tag list line
  - not candidate but automated: fine, reported for information

Usage:
  python check_automation.py --tests qa/test-cases.json --specs automation/tests [--out qa/automation-coverage.md] [--strict]
--strict exits 1 when candidates are missing or skeletons remain (CI gate).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

TAG = re.compile(r"[\"'`]@(TC-\d{3,})[\"'`]")
SKELETON = re.compile(r"QA Suite skeleton[^\"'`]*")
TC = re.compile(r"TC-\d{3,}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tests", required=True)
    ap.add_argument("--specs", required=True, help="folder with *.spec.ts / *.test.ts (searched recursively)")
    ap.add_argument("--out")
    ap.add_argument("--strict", action="store_true")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    tc = json.loads(Path(a.tests).read_text(encoding="utf-8-sig"))
    tests = {t["id"]: t for t in (tc["test_cases"] if isinstance(tc, dict) else tc)}

    where: dict[str, list[str]] = defaultdict(list)
    skeleton: set[str] = set()
    for f in sorted(Path(a.specs).rglob("*.ts")):
        text = f.read_text(encoding="utf-8", errors="ignore")
        for m in TAG.finditer(text):
            where[m.group(1)].append(f"{f.name}:{text.count(chr(10), 0, m.start()) + 1}")
        for m in SKELETON.finditer(text):
            skeleton |= set(TC.findall(m.group(0)))

    active = {k: t for k, t in tests.items() if t.get("status") != "deprecated"}
    candidates = {k for k, t in active.items()
                  if (t.get("automation") or {}).get("candidate") and t.get("technique") != "exploratory"}
    automated = {k for k in where if k in active and k not in skeleton}
    skel = {k for k in where if k in active and k in skeleton}
    missing = sorted(candidates - set(where))
    orphan = sorted(k for k in where if k not in active)
    dup = sorted(k for k, locs in where.items() if len(locs) > 1)
    extra = sorted(automated - candidates)

    n = len(candidates)
    pct = round(100 * len(candidates & automated) / n, 1) if n else 0.0
    lines = ["# Automation coverage", "",
             f"- Automation candidates: {n}",
             f"- Automated (implemented): {len(candidates & automated)} ({pct}%)",
             f"- Skeletons still to implement: {len(skel)}",
             f"- Missing (candidate without spec): {len(missing)}",
             f"- Orphan spec tags: {len(orphan)} · duplicate tags: {len(dup)} · automated non-candidates: {len(extra)}", ""]

    def section(title, ids, show_loc=True):
        if not ids:
            return
        lines.extend([f"## {title}", "", "| TC | Title | Priority | Location |", "|---|---|---|---|"])
        for k in ids:
            t = tests.get(k, {})
            loc = ", ".join(where.get(k, [])) if show_loc else "-"
            lines.append(f"| {k} | {t.get('title', '(not in test-cases.json)')} | {t.get('priority', '-')} | {loc} |")
        lines.append("")

    section("Missing", missing, show_loc=False)
    section("Skeletons (test.fixme)", sorted(skel))
    section("Orphan tags", orphan)
    section("Duplicate tags", dup)
    section("Automated", sorted(automated))
    text = "\n".join(lines) + "\n"
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(text, encoding="utf-8")
        print(f"wrote {a.out}")
    print(f"candidates {n} · automated {len(candidates & automated)} ({pct}%) · skeletons {len(skel)} · "
          f"missing {len(missing)} · orphan {len(orphan)} · duplicate {len(dup)}")
    if a.strict and (missing or skel or orphan):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
