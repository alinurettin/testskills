#!/usr/bin/env python3
"""Measure technique coverage: which coverage items of the design outputs are exercised by a test case.

A design script (ep_bva.py, decision_table.py, state_transition.py, pairwise.py) writes its coverage
items as table rows with IDs (C-07, S-02, N-05) into qa/design/DS-###-<name>.md. A test case points to
the items it exercises in `design_ref` (compact: `ref: DS-001 C-02, C-03`); the objective is read too.
Coverage per design spec = items referenced by an active test / items in the output (CTFL v4.0.1 §4.2:
coverage is measured on coverage items, not claimed).

Usage:
  python design_coverage.py --design-dir qa/design --tests qa/test-cases.json [--out qa/design-coverage.md]
      [--json qa/design-coverage.json] [--min-coverage 100] [--lang tr|en]

Reports, per design spec: covered / total, the uncovered items, references to items that do not exist
(stale after a spec change), and tests that name a spec but no item. Exit 1 when --min-coverage is given
and any spec is below it, or when a test references an unknown item; exit 2 on unreadable input.
Not every item must become a test: write the reason for a skipped item into the spec's notes and lower
the minimum deliberately; the report keeps the gap visible.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

DS = re.compile(r"\bDS-\d+\b")
ROW = re.compile(r"^\|\s*([A-Z]{1,2}-\d+)\s*\|")
TOKEN = re.compile(r"\b(DS-\d+|[A-Z]{1,2}-\d+)\b")
NOT_ITEMS = ("TC", "DS", "AC", "US", "Q")
T = {"en": {"title": "Design coverage", "spec": "Design spec", "cov": "Covered", "unc": "Uncovered items", "none": "none",
            "unknown": "References to unknown items (stale after a spec change?)", "noitem": "Tests that name a spec but no item",
            "nospec": "Design outputs without any test", "total": "Total"},
     "tr": {"title": "Tasarım kapsamı", "spec": "Tasarım spesifikasyonu", "cov": "Kapsanan", "unc": "Kapsanmayan öğeler", "none": "yok",
            "unknown": "Bilinmeyen öğelere verilen referanslar (spesifikasyon değişti mi?)",
            "noitem": "Spesifikasyonu anan ama öğe belirtmeyen testler", "nospec": "Hiç testi olmayan tasarım çıktıları", "total": "Toplam"}}


def items_of(md: Path) -> list[str]:
    out = []
    for line in md.read_text(encoding="utf-8-sig").splitlines():
        m = ROW.match(line)
        if m and m.group(1) not in out:
            out.append(m.group(1))
    return out


def refs_of(test: dict) -> tuple[set[tuple[str, str]], set[str]]:
    """((spec, item) pairs, specs named) from design_ref and objective."""
    pairs, specs = set(), set()
    for field in ("design_ref", "objective"):
        cur = None
        for tok in TOKEN.findall(str(test.get(field) or "")):
            if tok.startswith("DS-"):
                cur = tok
                specs.add(tok)
            elif cur and tok.split("-")[0] not in NOT_ITEMS and not tok.startswith("REQ"):
                pairs.add((cur, tok))
    return pairs, specs


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--design-dir", required=True)
    ap.add_argument("--tests", required=True)
    ap.add_argument("--out")
    ap.add_argument("--json")
    ap.add_argument("--min-coverage", type=float, help="fail (exit 1) when a spec is below this percentage")
    ap.add_argument("--lang", choices=["tr", "en"], default="en")
    sys.stdout.reconfigure(encoding="utf-8")
    a = ap.parse_args()
    t = T[a.lang]
    try:
        data = json.loads(Path(a.tests).read_text(encoding="utf-8-sig"))
        tests = [x for x in (data["test_cases"] if isinstance(data, dict) else data) if x.get("status") != "deprecated"]
        specs: dict[str, list[str]] = {}
        for md in sorted(Path(a.design_dir).glob("*.md")):
            m = DS.search(md.name) or DS.search(md.read_text(encoding="utf-8-sig")[:400])
            if m:
                specs.setdefault(m.group(0), [])
                specs[m.group(0)] += [i for i in items_of(md) if i not in specs[m.group(0)]]
    except (OSError, ValueError, KeyError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    used: dict[str, dict[str, list[str]]] = {s: {} for s in specs}
    unknown, noitem = [], []
    for tc in tests:
        pairs, named = refs_of(tc)
        for s, i in sorted(pairs):
            if s in specs and i in specs[s]:
                used[s].setdefault(i, []).append(tc["id"])
            else:
                unknown.append((tc["id"], s, i))
        for s in sorted(named - {p[0] for p in pairs}):
            noitem.append((tc["id"], s))
    rows, below = [], []
    for s, items in specs.items():
        cov = [i for i in items if i in used[s]]
        pct = round(100 * len(cov) / len(items), 1) if items else None
        rows.append({"spec": s, "total": len(items), "covered": len(cov), "pct": pct,
                     "uncovered": [i for i in items if i not in used[s]]})
        if a.min_coverage is not None and pct is not None and pct < a.min_coverage:
            below.append(s)
    tot, cov = sum(r["total"] for r in rows), sum(r["covered"] for r in rows)
    result = {"specs": rows, "total": tot, "covered": cov, "pct": round(100 * cov / tot, 1) if tot else None,
              "unknown_references": [{"test": x, "spec": s, "item": i} for x, s, i in unknown],
              "tests_without_item": [{"test": x, "spec": s} for x, s in noitem], "below_minimum": below}
    L = [f"# {t['title']}", "", f"| {t['spec']} | {t['cov']} | % | {t['unc']} |", "|---|---:|---:|---|"]
    for r in rows:
        L.append(f"| {r['spec']} | {r['covered']}/{r['total']} | {'–' if r['pct'] is None else r['pct']} | "
                 f"{', '.join(r['uncovered']) or t['none']} |")
    L.append(f"| **{t['total']}** | **{cov}/{tot}** | **{result['pct'] if tot else '–'}** | |")
    if unknown:
        L += ["", f"## {t['unknown']}"] + [f"- {x}: {s} {i}" for x, s, i in unknown]
    if noitem:
        L += ["", f"## {t['noitem']}"] + [f"- {x}: {s}" for x, s in noitem]
    text = "\n".join(L) + "\n"
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(text, encoding="utf-8", newline="\n")
    else:
        print(text)
    if a.json:
        Path(a.json).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    print(f"design coverage: {cov}/{tot} items" + (f" ({result['pct']}%)" if tot else "") +
          f" · unknown references {len(unknown)} · tests without item {len(noitem)}" +
          (f" · below minimum: {', '.join(below)}" if below else ""), file=sys.stderr if a.out is None else sys.stdout)
    return 1 if (below or unknown) else 0


if __name__ == "__main__":
    sys.exit(main())
