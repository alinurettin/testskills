#!/usr/bin/env python3
"""Automation coverage report: which test cases are automated, still skeletons, missing or orphaned.

Static scan of the spec files (no Playwright run needed):
  - automated   : a "@TC-###" tag exists, no QA Suite skeleton marker mentions the ID, and the test
                  block contains an assertion (expect(...), expect.soft/poll or an expectXxx() helper)
  - no assertion: tagged and not a skeleton, but the block asserts nothing. It is NOT counted as
                  automated: a test without an oracle cannot fail for the right reason
  - skeleton    : generated but still marked with test.fixme("QA Suite skeleton ...")
  - missing     : automation candidate (automation.candidate == true) without any spec
  - orphan      : a spec tag refers to a TC that is not in test-cases.json (or is deprecated)
  - duplicate   : the same TC tag appears in more than one test title/tag list line
  - not candidate but automated: fine, reported for information

Usage:
  python check_automation.py --tests qa/test-cases.json --specs automation/tests [--out qa/automation-coverage.md] [--strict]
--strict exits 1 when candidates are missing, skeletons remain, tags are orphaned, a test asserts nothing, or the static lint finds a smell
(waitForTimeout, test.only, force: true, raw CSS/XPath, credential literals, networkidle) (CI gate).
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
BOUNDARY = re.compile(r"^[ \t]*(?:test|test\.describe)\(", re.M)
CASES = re.compile(r"^[ \t]*const (\w+) = \[", re.M)
LOOP = re.compile(r"^[ \t]*for \(const \w+ of (\w+)\)", re.M)
ASSERT = re.compile(r"\bexpect[A-Za-z]*\s*[.(]")
COMMENT = re.compile(r"//[^\n]*|/\*.*?\*/", re.S)


def block_of(text: str, pos: int) -> str:
    """The test block a tag at `pos` belongs to. Tags inside a data-driven `const casesN = [...]`
    array belong to the `for (const c of casesN)` loop that follows it."""
    start = pos
    arrays = [m for m in CASES.finditer(text) if m.start() < pos]
    if arrays:
        loop = next((m for m in LOOP.finditer(text, arrays[-1].end()) if m.group(1) == arrays[-1].group(1)), None)
        if loop and loop.start() > pos:
            first = BOUNDARY.search(text, loop.end())
            start = first.end() if first else loop.end()
    end = BOUNDARY.search(text, start)
    return text[start:end.start() if end else len(text)]


def asserts(block: str) -> bool:
    return bool(ASSERT.search(COMMENT.sub("", block)))


LINT = [
    ("WAIT_TIMEOUT", re.compile(r"\bwaitForTimeout\s*\("), "fixed sleep: wait for a state with a web-first assertion instead"),
    ("TEST_ONLY", re.compile(r"\b(?:test|describe)\.only\s*\("), "test.only left in: the rest of the suite does not run"),
    ("FORCE", re.compile(r"\bforce\s*:\s*true"), "force: true skips actionability checks and hides real defects"),
    ("RAW_SELECTOR", re.compile(r"""\b(?:locator|\$\$?)\(\s*['"`](?://|xpath=|[.#][\w-]+|\w+\s*>\s*\w+)"""),
     "raw CSS/XPath: prefer getByRole / getByLabel / getByTestId"),
    ("CREDENTIAL", re.compile(r"""(?i)\b(?:password|passwd|secret|api[_-]?key|token)\b\s*[:=]\s*['"`][^'"`$\s]{6,}['"`]"""),
     "credential literal: read it from the environment"),
    ("NETWORKIDLE", re.compile(r"""['"`]networkidle['"`]"""), "networkidle is discouraged: assert on what the user sees"),
]


def lint(text: str, name: str) -> list[tuple[str, str, int, str]]:
    out = []
    for no, line in enumerate(text.splitlines(), 1):
        code = line.split("//", 1)[0] if not line.lstrip().startswith("//") else ""
        for rule, rx, msg in LINT:
            if rx.search(code):
                out.append((rule, name, no, msg))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tests", required=True)
    ap.add_argument("--specs", required=True, help="folder with *.spec.ts / *.test.ts (searched recursively)")
    ap.add_argument("--out")
    ap.add_argument("--strict", action="store_true")
    sys.stdout.reconfigure(encoding="utf-8")
    a = ap.parse_args()
    tc = json.loads(Path(a.tests).read_text(encoding="utf-8-sig"))
    tests = {t["id"]: t for t in (tc["test_cases"] if isinstance(tc, dict) else tc)}

    where: dict[str, list[str]] = defaultdict(list)
    skeleton: set[str] = set()
    asserting: set[str] = set()
    smells: list[tuple[str, str, int, str]] = []
    for f in sorted(Path(a.specs).rglob("*.ts")):
        text = f.read_text(encoding="utf-8", errors="ignore")
        smells += lint(text, f.name)
        for m in TAG.finditer(text):
            where[m.group(1)].append(f"{f.name}:{text.count(chr(10), 0, m.start()) + 1}")
            if asserts(block_of(text, m.start())):
                asserting.add(m.group(1))
        for m in SKELETON.finditer(text):
            skeleton |= set(TC.findall(m.group(0)))

    active = {k: t for k, t in tests.items() if t.get("status") != "deprecated"}
    candidates = {k for k, t in active.items()
                  if (t.get("automation") or {}).get("candidate") and t.get("technique") != "exploratory"}
    automated = {k for k in where if k in active and k not in skeleton and k in asserting}
    hollow = sorted(k for k in where if k in active and k not in skeleton and k not in asserting)
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
             f"- Tagged tests without an assertion (not counted as automated): {len(hollow)}",
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
    section("No assertion (add expect(...) for each expected result)", hollow)
    section("Orphan tags", orphan)
    section("Duplicate tags", dup)
    section("Automated", sorted(automated))
    if smells:
        lines.extend(["## Lint findings (fix before trusting the results)", "", "| Rule | Location | Why |", "|---|---|---|"])
        lines.extend(f"| {r} | {n}:{no} | {m} |" for r, n, no, m in smells)
        lines.append("")
    text = "\n".join(lines) + "\n"
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(text, encoding="utf-8", newline="\n")
        print(f"wrote {a.out}")
    print(f"candidates {n} · automated {len(candidates & automated)} ({pct}%) · skeletons {len(skel)} · "
          f"missing {len(missing)} · orphan {len(orphan)} · duplicate {len(dup)} · no assertion {len(hollow)}"
          + (f" · lint {len(smells)}" if smells else ""))
    if a.strict and (missing or skel or orphan or hollow or smells):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
