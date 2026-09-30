#!/usr/bin/env python3
"""Build the real-import verification kit: one import file per test-management tool + EXPECTED.md.

Source: examples/fast-transfer/qa/test-cases.json + requirements.json when both exist, otherwise
tests/fixtures/coupon/test-cases.json + kit-requirements.json (the coupon requirements with Jira keys
KIT-1..KIT-3, so a fresh Jira project with key KIT can host the links).

    python examples/import-kit/make_kit.py            # regenerate the kit (after exporter changes)
    python examples/import-kit/make_kit.py --check    # exit 1 if a kit file is out of date

The walkthrough for the owner is docs/IMPORT-VERIFICATION.md. tests/test_export_golden.py fails when
the kit is stale.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

KIT_DIR = Path(__file__).resolve().parent
ROOT = KIT_DIR.parent.parent
EXPORT = ROOT / "skills" / "exporting-test-cases" / "scripts" / "export_tests.py"
FOLDER = "QA Suite Kit/Kupon"          # Xray/Zephyr "QA Suite Kit/Kupon", TestRail "QA Suite Kit > Kupon", Qase nested
ADO_PROJECT = "QASuiteKit"             # name the Azure DevOps project exactly like this: it is the root Area Path

# file name -> exporter arguments (besides --tests/--requirements/--out)
KIT = [
    ("xray.csv", ["--format", "xray", "--folder", FOLDER]),
    ("xray-server-dc.csv", ["--format", "xray", "--xray-links", "columns", "--folder", FOLDER]),
    ("zephyr.csv", ["--format", "zephyr", "--folder", FOLDER]),
    ("zephyr-inline-data.csv", ["--format", "zephyr", "--zephyr-data", "inline", "--folder", FOLDER]),
    ("testrail.csv", ["--format", "testrail", "--folder", FOLDER]),
    ("azure-devops.csv", ["--format", "azure-devops", "--area-path", ADO_PROJECT]),
    ("qase.csv", ["--format", "qase", "--folder", FOLDER]),
]


def source() -> tuple[Path, Path]:
    ft = ROOT / "examples" / "fast-transfer" / "qa"
    if (ft / "test-cases.json").exists() and (ft / "requirements.json").exists():
        return ft / "test-cases.json", ft / "requirements.json"
    return ROOT / "tests" / "fixtures" / "coupon" / "test-cases.json", KIT_DIR / "kit-requirements.json"


def export(args: list[str], out: Path) -> subprocess.CompletedProcess:
    tests, reqs = source()
    return subprocess.run([sys.executable, str(EXPORT), "--tests", str(tests), "--requirements", str(reqs),
                           "--out", str(out)] + args, capture_output=True, text=True, encoding="utf-8")


def rows_of(text: str) -> list[list[str]]:
    rows = list(csv.reader(io.StringIO(text.lstrip("﻿"))))
    return [[c.replace("\r\n", "\n") for c in r] for r in rows]


# ------------------------------------------------------------------ per-tool summary of a written file
def _groups(rows: list[list[str]], start_col: str) -> list[list[dict]]:
    """Split data rows into test cases: a new case starts where start_col is non-empty."""
    head, out = rows[0], []
    for r in rows[1:]:
        d = dict(zip(head, r))
        if d.get(start_col, "").strip():
            out.append([d])
        elif out:
            out[-1].append(d)
    return out


def summarize(fmt: str, rows: list[list[str]]) -> list[dict]:
    """One dict per test case: id, steps and the tool-specific values an importer must keep."""
    head, res = rows[0], []
    if fmt == "xray":
        by_id: dict = {}
        for r in rows[1:]:
            by_id.setdefault(r[0], []).append(dict(zip(head, r)))
        link_cols = [c for c in head if c.startswith("Requirement Key")]
        for tid, g in by_id.items():
            links = [x for c in link_cols for x in re.split(r"[;,]", g[0].get(c, "")) if x.strip()]
            res.append({"id": tid, "steps": len(g), "Priority": g[0]["Priority"], "Test Type": g[0]["Test Type"],
                        "links": ", ".join(links) or "-", "folder": g[0].get("Test Repository Folder", "") or "-"})
    elif fmt == "zephyr":
        for g in _groups(rows, "Name"):
            steps = len(g) if "Test Script (Plain Text)" not in head else \
                len(re.findall(r"(?m)^\d+\. ", g[0]["Test Script (Plain Text)"]))
            res.append({"id": g[0]["Name"].split(" ")[0], "steps": steps, "Status": g[0]["Status"],
                        "Priority": g[0]["Priority"], "links": g[0]["Coverage"] or "-", "folder": g[0]["Folder"] or "-"})
    elif fmt == "testrail":
        for g in _groups(rows, "Title"):
            res.append({"id": g[0]["Title"].split(" ")[0], "steps": len(g), "Priority": g[0]["Priority"],
                        "Type": g[0]["Type"], "links": g[0]["References"] or "-", "folder": g[0]["Section"] or "-"})
    elif fmt == "azure-devops":
        by_title: dict = {}
        for r in rows[1:]:
            by_title.setdefault(r[2], []).append(dict(zip(head, r)))
        for title, g in by_title.items():
            res.append({"id": title.split(" ")[0], "steps": len(g), "Priority": g[0]["Priority"], "State": g[0]["State"],
                        "links": "-", "folder": g[0]["Area Path"] or "-"})
    elif fmt == "qase":
        data = [dict(zip(head, r)) for r in rows[1:]]
        suites = {d["suite_id"]: (d["suite"], d["suite_parent_id"]) for d in data if d["suite_without_cases"] == "1"}
        for d in data:
            if d["suite_without_cases"] == "1":
                continue
            path, sid = [], d["suite_id"]
            while sid and len(path) <= len(suites):
                name, sid = suites.get(sid, ("?", ""))
                path.insert(0, name)
            refs = re.search(r"(?m)^(?:Gereksinimler|Requirements): (.*)$", d["description"])
            res.append({"id": d["title"].split(" ")[0], "steps": len(re.findall(r'(?m)^\d+\. "', d["steps_actions"])),
                        "priority": d["priority"], "severity": d["severity"], "status": d["status"],
                        "automation": d["automation"], "links": refs.group(1) if refs else "-",
                        "folder": " / ".join(path)})
    return res


def fmt_of(args: list[str]) -> str:
    return args[args.index("--format") + 1]


def expected_md(outputs: dict[str, str]) -> str:
    tests_path, reqs_path = source()
    tc = json.loads(tests_path.read_text(encoding="utf-8-sig"))
    tests = [t for t in (tc["test_cases"] if isinstance(tc, dict) else tc) if t.get("status") != "deprecated"]
    rel = lambda p: p.relative_to(ROOT).as_posix()  # noqa: E731
    o = ["# Import kit: expected result / beklenen sonuç", "",
         f"Generated by `make_kit.py` from `{rel(tests_path)}` + `{rel(reqs_path)}`. Do not edit by hand.",
         "`make_kit.py` tarafından üretildi; elle düzenlemeyin.", "",
         f"Tests / test sayısı: **{len(tests)}** · steps / adım: **{sum(len(t['steps']) for t in tests)}** "
         "(deprecated tests are not exported / deprecated testler aktarılmaz)", "",
         "| TC | Title / Başlık | Steps / Adım |", "|---|---|---|"]
    o += [f"| {t['id']} | {t['title']} | {len(t['steps'])} |" for t in tests]
    for name, args in KIT:
        fmt = fmt_of(args)
        summary = summarize(fmt, rows_of(outputs[name]))
        keys = [k for k in summary[0] if k != "id"]
        cmd = " ".join(f'"{x}"' if " " in x else x for x in args)
        o += ["", f"## {name}", "", f"`{cmd}`", "",
              "| TC | " + " | ".join(keys) + " |", "|" + "---|" * (len(keys) + 1)]
        o += ["| " + " | ".join([s["id"]] + [str(s[k]) for k in keys]) + " |" for s in summary]
    return "\n".join(o) + "\n"


def build() -> dict[str, str]:
    """Return {kit file name: content} generated fresh by the exporter."""
    outputs = {}
    with tempfile.TemporaryDirectory() as d:
        for name, args in KIT:
            out = Path(d) / name
            r = export(args, out)
            if r.returncode != 0:
                raise SystemExit(f"export failed for {name}: {r.stderr}")
            outputs[name] = out.read_text(encoding="utf-8")
    outputs["EXPECTED.md"] = expected_md(outputs)
    return outputs


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="exit 1 if a kit file is out of date")
    a = ap.parse_args()
    stale = []
    for name, text in build().items():
        path = KIT_DIR / name
        current = path.read_text(encoding="utf-8").replace("\r\n", "\n") if path.exists() else None
        if current == text.replace("\r\n", "\n"):
            continue
        stale.append(name)
        if not a.check:
            # CSV keeps the exporter's own bytes (CRLF rows); .gitattributes may normalise them to LF, both import fine
            path.write_text(text, encoding="utf-8", newline="" if name.endswith(".csv") else "\n")
    if a.check:
        print("stale: " + ", ".join(stale) if stale else "import kit up to date")
        return 1 if stale else 0
    print(f"wrote {len(stale)} file(s) to {KIT_DIR}" if stale else "import kit already up to date")
    return 0


if __name__ == "__main__":
    sys.exit(main())
