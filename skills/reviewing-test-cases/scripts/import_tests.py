#!/usr/bin/env python3
"""Import an existing test suite from CSV (Excel/TestRail/Xray/Zephyr export) into QA Suite compact format.

Detects columns by header name (TR/EN aliases) and two layouts:
  - one row per test, steps/expected numbered inside cells ("1. … 2. …")
  - one row per step, rows of the same test sharing an ID (Xray/Zephyr style)
Unknown values get safe defaults and are flagged so the review can fix them:
  priority → mapped (Highest/Kritik→c, High/Yüksek→h, Medium/Normal/Orta→m, Low/Lowest/Düşük→l, else m)
  polarity → guessed from wording (reject/error/invalid/geçersiz/hata/red → negative)
  technique → rb (requirements-based); tag "imported"
  requirement → from a requirement/coverage/labels column (REQ-### or Jira keys), else "UNLINKED"
New IDs: original IDs are kept in a tag ("src-<id>"); QA IDs are TC-### from --start (default 1).

Usage:
  python import_tests.py suite.csv --out qa/test-cases.src.md [--delimiter ";"] [--lang tr] [--start 1] [--map title=Summary,steps=Action]
  python ../../analyzing-requirements/scripts/qa_compact.py tc qa/test-cases.src.md --out qa/test-cases.json
Excel: save the sheet as CSV UTF-8 first.
"""
from __future__ import annotations

import argparse
import csv
import io
import re
import sys
from collections import OrderedDict
from pathlib import Path

ALIASES = {
    "id": ["id", "test id", "tcid", "test case id", "key", "issue key", "case id", "no", "test no", "test kodu"],
    "title": ["title", "summary", "name", "test case", "test case name", "başlık", "baslik", "test adı", "senaryo", "ad"],
    "pre": ["precondition", "preconditions", "pre-condition", "ön koşul", "ön koşullar", "on kosul", "önkoşul"],
    "steps": ["steps", "step", "action", "test steps", "adımlar", "adım", "aksiyon", "test script (step-by-step) - step"],
    "data": ["data", "test data", "veri", "test verisi", "test script (step-by-step) - test data"],
    "expected": ["expected", "expected result", "expected results", "beklenen", "beklenen sonuç", "result",
                 "test script (step-by-step) - expected result"],
    "priority": ["priority", "öncelik", "oncelik", "severity"],
    "req": ["requirement", "requirements", "requirement keys", "coverage", "references", "refs", "gereksinim",
            "gereksinimler", "story", "user story", "labels"],
    "tags": ["tags", "etiketler", "component", "components", "section", "folder"],
}
PRI = {"highest": "c", "blocker": "c", "critical": "c", "kritik": "c", "p1": "c", "high": "h", "yüksek": "h",
       "yuksek": "h", "major": "h", "p2": "h", "medium": "m", "normal": "m", "orta": "m", "p3": "m",
       "low": "l", "lowest": "l", "minor": "l", "trivial": "l", "düşük": "l", "dusuk": "l", "p4": "l"}
NEG = re.compile(r"(geçersiz|hatal|hata mesaj|reddedil|red |izin veril(mez|memeli)|engellen|yetkisiz|invalid|error|"
                 r"reject|denied|not allowed|fail|blocked|unauthori[sz]ed|negative|negatif)", re.I)
NUM = re.compile(r"(?:^|\n|\s)(\d{1,2})[.)]\s+")


def norm(h: str) -> str:
    return re.sub(r"\s+", " ", h.strip().lower().replace("_", " "))


def detect(headers: list[str], overrides: dict) -> dict:
    cols = {}
    low = [norm(h) for h in headers]
    for key, names in ALIASES.items():
        if key in overrides:
            cols[key] = low.index(norm(overrides[key])) if norm(overrides[key]) in low else None
            continue
        for n in names:
            if n in low:
                cols[key] = low.index(n)
                break
    return cols


def split_numbered(cell: str) -> list[str]:
    cell = (cell or "").strip()
    if not cell:
        return []
    parts = NUM.split("\n" + cell)
    if len(parts) >= 3:  # ['', '1', 'text', '2', 'text' ...]
        return [p.strip().replace("\n", " ") for p in parts[2::2]]
    return [line.strip(" -•\t") for line in cell.splitlines() if line.strip()] or [cell]


def one(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("csv")
    ap.add_argument("--out", required=True)
    ap.add_argument("--delimiter", help="default: auto-detect , ; or tab")
    ap.add_argument("--start", type=int, default=1)
    ap.add_argument("--lang", choices=["tr", "en"], default="tr")
    ap.add_argument("--project", default="")
    ap.add_argument("--map", default="", help="explicit column mapping, e.g. title=Summary,steps=Action,expected=Result")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    raw = Path(a.csv).read_bytes().decode("utf-8-sig", errors="replace")
    delim = a.delimiter or csv.Sniffer().sniff(raw.splitlines()[0], delimiters=",;\t").delimiter
    rows = list(csv.reader(io.StringIO(raw), delimiter=delim))
    if len(rows) < 2:
        print("error: no data rows", file=sys.stderr)
        return 2
    overrides = dict(p.split("=", 1) for p in a.map.split(",") if "=" in p)
    cols = detect(rows[0], overrides)
    if cols.get("title") is None or cols.get("steps") is None:
        print(f"error: could not find title/steps columns in {rows[0]}; use --map title=...,steps=...", file=sys.stderr)
        return 2
    get = lambda r, k: (r[cols[k]] if cols.get(k) is not None and cols[k] < len(r) else "").strip()

    tests: "OrderedDict[str, dict]" = OrderedDict()
    row_per_step = cols.get("id") is not None and len({get(r, "id") for r in rows[1:] if get(r, "id")}) < len(rows) - 1
    last = None
    for n, r in enumerate(rows[1:], 2):
        if not any(c.strip() for c in r):
            continue
        rid = get(r, "id") or (last if row_per_step and not get(r, "title") else f"row{n}")
        t = tests.get(rid)
        if t is None:
            t = tests[rid] = {"src": rid, "title": one(get(r, "title")), "pre": get(r, "pre"), "priority": get(r, "priority"),
                              "req": get(r, "req"), "tags": get(r, "tags"), "steps": []}
        last = rid
        acts = split_numbered(get(r, "steps"))
        exps = split_numbered(get(r, "expected"))
        datas = split_numbered(get(r, "data")) if not row_per_step else [get(r, "data")]
        if row_per_step:
            if get(r, "steps") or get(r, "expected"):
                t["steps"].append((one(get(r, "steps")), one(get(r, "data")), one(get(r, "expected"))))
        else:
            for i in range(max(len(acts), len(exps))):
                t["steps"].append((acts[i] if i < len(acts) else "", datas[i] if i < len(datas) else "",
                                   exps[i] if i < len(exps) else ""))

    out = [f"# Imported by import_tests.py from {Path(a.csv).name} ({'row per step' if row_per_step else 'row per test'}). "
           "Defaults: pol guessed, tech rb, req UNLINKED when missing - review before use.",
           f"language: {a.lang}"] + ([f"project: {a.project}"] if a.project else [])
    num, stats = a.start, {"tests": 0, "unlinked": 0, "no_expected": 0}
    for rid, t in tests.items():
        if not t["steps"]:
            t["steps"] = [("(adım yok)" if a.lang == "tr" else "(no steps)", "", "")]
        reqs = re.findall(r"\bREQ-\d+\b|\b[A-Z][A-Z0-9]+-\d+\b", t["req"])
        if not reqs:
            stats["unlinked"] += 1
        text = " ".join([t["title"]] + [s[2] for s in t["steps"]])
        pol = "-" if NEG.search(text) else "+"
        pri = PRI.get(t["priority"].strip().lower(), "m")
        tags = ["imported", f"src-{re.sub(r'[^A-Za-z0-9-]', '-', rid)}"] + [re.sub(r"\s+", "-", x.strip()) for x in re.split(r"[,;]", t["tags"]) if x.strip()]
        out += ["", f"## TC-{num:03d} | {t['title'] or rid}",
                f"req: {', '.join(dict.fromkeys(reqs)) or 'UNLINKED'} | pri: {pri} | pol: {pol} | tech: rb"]
        for p in split_numbered(t["pre"]) if t["pre"] else []:
            out.append(f"pre: {one(p)}")
        for i, (act, data, exp) in enumerate(t["steps"], 1):
            if not exp:
                stats["no_expected"] += 1
            d = f" [{data}]" if data and "[" not in data and "]" not in data else ""
            out.append(f"{i}. {act or '-'}{d} => {exp}")
        out.append(f"tags: {', '.join(dict.fromkeys(tags))} | status: draft")
        num += 1
        stats["tests"] += 1
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"wrote {a.out}: {stats['tests']} tests ({'row per step' if row_per_step else 'row per test'}) · "
          f"unlinked {stats['unlinked']} · steps without expected {stats['no_expected']}")
    print("columns: " + ", ".join(f"{k}={rows[0][v]}" for k, v in cols.items() if v is not None))
    return 0


if __name__ == "__main__":
    sys.exit(main())
