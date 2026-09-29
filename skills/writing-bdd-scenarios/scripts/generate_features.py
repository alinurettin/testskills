#!/usr/bin/env python3
"""Generate Gherkin .feature files (TR/EN) from QA Suite test cases.

The output is a faithful first draft; each scenario keeps its identity:
  - Feature per requirement, tagged @REQ-###; Scenario per test case, tagged
    @TC-### (+ @<priority>, test tags)
  - preconditions shared by every scenario of the file become the Background
  - steps become Given (preconditions) / When (action) / Then (expected);
    step data is appended as a quoted "string" so step definitions can capture it
  - >= 3 cases of one requirement whose steps differ only in numbers/data become a
    Scenario Outline with one tagged Examples block per test case (TC tags survive)
Rewrite the drafts into declarative business language afterwards, but keep the tags.

Idempotent: test cases whose @TC-### tag already exists under --out are skipped.

Usage:
  python generate_features.py --tests qa/test-cases.json --requirements qa/requirements.json --out features [--lang tr|en]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from collections import OrderedDict
from pathlib import Path

KW = {
    "tr": {"feature": "Özellik", "background": "Geçmiş", "scenario": "Senaryo", "outline": "Senaryo taslağı",
           "examples": "Örnekler", "given": "Diyelim ki", "when": "Eğer ki", "then": "O zaman", "and": "Ve"},
    "en": {"feature": "Feature", "background": "Background", "scenario": "Scenario", "outline": "Scenario Outline",
           "examples": "Examples", "given": "Given", "when": "When", "then": "Then", "and": "And"},
}
TC_TAG = re.compile(r"@(TC-\d{3,})\b")


def slug(s: str, n: int = 40) -> str:
    s = s.replace("ı", "i").replace("İ", "I")
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:n].strip("-") or "x"


def one_line(s) -> str:
    return re.sub(r"\s+", " ", str(s or "")).strip()


def as_list(v) -> list[str]:
    if not v:
        return []
    if isinstance(v, list):
        return [one_line(x) for x in v]
    if isinstance(v, dict):
        return [f"{k} = {x}" for k, x in v.items()]
    return [one_line(v)]


def cell(s) -> str:
    return one_line(s).replace("|", "\\|")


def tags_for(t: dict) -> str:
    tags = [f"@{t['id']}"]
    if t.get("priority"):
        tags.append(f"@{t['priority']}")
    tags += [f"@{slug(x, 30)}" for x in t.get("tags", [])]
    tags += [f"@{r}" for r in t.get("requirement_ids", [])[1:]]  # the first REQ is on the Feature
    if t.get("polarity") == "negative":
        tags.append("@negative")
    return " ".join(dict.fromkeys(tags))


def with_data(action: str, data) -> str:
    return f'{one_line(action)} "{one_line(data)}"' if data else one_line(action)


class Writer:
    def __init__(self, kw: dict):
        self.kw, self.lines, self.last = kw, [], None

    def step(self, kind: str, text: str, ind: str = "    "):
        word = self.kw["and"] if kind == self.last else self.kw[kind]
        self.lines.append(f"{ind}{word} {text}")
        self.last = kind

    def reset(self):
        self.last = None


def shape(t: dict) -> tuple:
    norm = lambda s: re.sub(r"\d[\d.,]*", "#", str(s or "").lower()).strip()
    return tuple(norm(s.get("action")) for s in t.get("steps", []))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tests", required=True)
    ap.add_argument("--requirements")
    ap.add_argument("--out", required=True)
    ap.add_argument("--lang", choices=["tr", "en"])
    ap.add_argument("--only", help="comma-separated TC IDs")
    ap.add_argument("--all", action="store_true", help="include tests that are not automation candidates")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    try:
        tc = json.loads(Path(a.tests).read_text(encoding="utf-8-sig"))
        rq = json.loads(Path(a.requirements).read_text(encoding="utf-8-sig")) if a.requirements else {}
    except (OSError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    lang = a.lang or (tc.get("language") if isinstance(tc, dict) else None) or "en"
    kw = KW.get(lang, KW["en"])
    tests = tc["test_cases"] if isinstance(tc, dict) else tc
    reqs = {r["id"]: r for r in (rq.get("requirements", []) if isinstance(rq, dict) else rq)}
    out = Path(a.out)
    done = set()
    if out.exists():
        for f in out.rglob("*.feature"):
            done |= set(TC_TAG.findall(f.read_text(encoding="utf-8", errors="ignore")))
    wanted = {x.strip() for x in a.only.split(",")} if a.only else None

    groups: "OrderedDict[str, list]" = OrderedDict()
    skipped = []
    for t in tests:
        if t.get("status") == "deprecated" or t.get("technique") == "exploratory":
            continue
        if wanted and t["id"] not in wanted:
            continue
        if not a.all and not wanted and not (t.get("automation") or {}).get("candidate"):
            continue
        if t["id"] in done:
            skipped.append(t["id"])
            continue
        groups.setdefault((t.get("requirement_ids") or ["no-req"])[0], []).append(t)

    for rid, items in groups.items():
        title = reqs.get(rid, {}).get("title", "")
        path = out / f"{slug(rid, 12)}{('-' + slug(title, 40)) if title else ''}.feature"
        new_file = not path.exists()
        # a Background can only be written into a new file; when appending, keep every precondition in its scenario
        common = (set.intersection(*[set(as_list(t.get("preconditions"))) for t in items])
                  if new_file and len(items) > 1 else set())
        w = Writer(kw)
        if new_file:
            if lang != "en":
                w.lines.append(f"# language: {lang}")
            w.lines += ["# Generated by QA Suite (generate_features.py). Rewrite steps declaratively; keep the tags.",
                        f"@{rid}", f"{kw['feature']}: {(rid + ' ' + title).strip()}"]
            if reqs.get(rid, {}).get("text"):
                w.lines.append(f"  {one_line(reqs[rid]['text'])}")
            if common:
                w.lines += ["", f"  {kw['background']}:"]
                w.reset()
                for p in sorted(common):
                    w.step("given", p)
        else:
            w.lines.append("\n  # Added by QA Suite generate_features.py")
        # data-driven outlines
        shapes: "OrderedDict[tuple, list]" = OrderedDict()
        for t in items:
            shapes.setdefault(shape(t), []).append(t)
        emitted = set()
        for shp, grp in shapes.items():
            if len(grp) < 3 or not shp:
                continue
            first = grp[0]
            n = len(first["steps"])
            has_data = [any(t["steps"][i].get("data") for t in grp) for i in range(n)]
            w.lines += ["", f"  {kw['outline']}: <id> <title>"]
            w.reset()
            gcommon = set.intersection(*[set(as_list(t.get("preconditions"))) for t in grp]) - common
            for p in sorted(gcommon):
                w.step("given", p)
            w.step("given", "<pre>")
            for i, s in enumerate(first["steps"], 1):
                w.step("when", with_data(s.get("action"), f"<d{i}>" if has_data[i - 1] else ""))
                w.step("then", f"<e{i}>")
            cols = ["id", "title", "pre"]
            for i in range(1, n + 1):
                cols += ([f"d{i}"] if has_data[i - 1] else []) + [f"e{i}"]
            for t in grp:
                pre = "; ".join(p for p in as_list(t.get("preconditions")) if p not in common and p not in gcommon) or "-"
                row = [t["id"], t["title"], pre]
                for i, s in enumerate(t["steps"]):
                    row += ([s.get("data", "")] if has_data[i] else []) + [s.get("expected", "")]
                w.lines += ["", f"    {tags_for(t)}", f"    {kw['examples']}:",
                            "      | " + " | ".join(cols) + " |", "      | " + " | ".join(cell(x) for x in row) + " |"]
            emitted |= {t["id"] for t in grp}
        for t in items:
            if t["id"] in emitted:
                continue
            w.lines += ["", f"  {tags_for(t)}", f"  {kw['scenario']}: {t['id']} {one_line(t['title'])}"]
            w.reset()
            for p in as_list(t.get("preconditions")) + as_list(t.get("test_data")):
                if p not in common:
                    w.step("given", p)
            for s in t.get("steps", []):
                w.step("when", with_data(s.get("action"), s.get("data")))
                w.step("then", one_line(s.get("expected")))
        text = "\n".join(w.lines) + "\n"
        path.parent.mkdir(parents=True, exist_ok=True)
        if new_file:
            path.write_text(text, encoding="utf-8", newline="\n")
        else:
            with path.open("a", encoding="utf-8", newline="\n") as f:
                f.write(text)
        print(f"wrote {path}: {len(items)} scenarios ({', '.join(t['id'] for t in items)})")
    if skipped:
        print(f"already in features (kept): {', '.join(skipped)}")
    if not groups:
        print("nothing new to generate")
    return 0


if __name__ == "__main__":
    sys.exit(main())
