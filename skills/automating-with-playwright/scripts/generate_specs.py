#!/usr/bin/env python3
"""Generate Playwright TypeScript spec skeletons from QA Suite test cases.

Every generated test keeps the manual test's identity:
  - title "TC-001 <title>", tags ["@TC-001", "@REQ-001", "@<priority>", "@smoke" ...]
  - annotations qa_id, requirements (Jira keys when known) and test_key (the
    test's external_id, e.g. its Xray key) for the Xray JUnit reporter
  - one test.step per manual step, with data and expected result as comments
  - test.fixme(...) marker, so an unimplemented skeleton is reported as
    skipped, never as a false "passed". Delete the marker once implemented.

Idempotent: tests whose "@TC-###" tag already appears anywhere under --out are
skipped; new tests for an existing file are appended as a new describe block.
Nothing is ever overwritten.

Selection: status != deprecated, technique != exploratory, and
automation.candidate == true (use --all to ignore the candidate flag).
Data-driven: >= 3 tests of one requirement whose steps differ only in numbers
and data become one `for (const c of cases)` block, one test (and TC tag) per case.

Usage:
  python generate_specs.py --tests qa/test-cases.json --requirements qa/requirements.json --out automation/tests
  python generate_specs.py --tests qa/test-cases.json --out automation/tests --only TC-001,TC-004 --no-data-driven
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import unicodedata
from collections import OrderedDict
from pathlib import Path

TC_TAG = re.compile(r"@(TC-\d{3,})\b")
MARK = "QA Suite skeleton"


def slug(s: str, n: int = 40) -> str:
    s = s.replace("ı", "i").replace("İ", "I")
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:n].strip("-") or "x"


def ts(s) -> str:
    """TypeScript string literal (JSON double-quoted strings are valid TS)."""
    return json.dumps("" if s is None else str(s), ensure_ascii=False)


def comment(s) -> str:
    return re.sub(r"\s+", " ", str(s)).strip()


def as_list(v) -> list:
    if v is None or v == "":
        return []
    if isinstance(v, list):
        return v
    if isinstance(v, dict):
        return [f"{k}={x}" for k, x in v.items()]
    return [str(v)]


def existing_ids(out: Path) -> set[str]:
    found = set()
    if out.exists():
        for f in out.rglob("*.ts"):
            found |= set(TC_TAG.findall(f.read_text(encoding="utf-8", errors="ignore")))
    return found


def tags_for(t: dict) -> list[str]:
    tags = [f"@{t['id']}"] + [f"@{r}" for r in t.get("requirement_ids", [])]
    if t.get("priority"):
        tags.append(f"@{t['priority']}")
    tags += [f"@{slug(x, 30)}" for x in t.get("tags", []) if slug(x, 30) not in ("x",)]
    return list(dict.fromkeys(tags))


def annotations_for(t: dict, ext: dict) -> list[tuple[str, str]]:
    ann = [("qa_id", t["id"])]
    keys = list(dict.fromkeys(ext[r] for r in t.get("requirement_ids", []) if ext.get(r)))
    ann.append(("requirements", ",".join(keys) if keys else ",".join(t.get("requirement_ids", []))))
    if t.get("external_id"):
        ann.append(("test_key", t["external_id"]))
    return ann


def fixture_arg(t: dict) -> str:
    return "{ request }" if t.get("category") == "api" else "{ page }"


def step_shape(t: dict) -> tuple:
    norm = lambda s: re.sub(r"\d[\d.,]*", "#", str(s or "").lower()).strip()
    return (fixture_arg(t), tuple(norm(s.get("action")) for s in t.get("steps", [])))


def render_test(t: dict, ext: dict, ind: str) -> list[str]:
    ann = ", ".join(f"{{ type: {ts(k)}, description: {ts(v)} }}" for k, v in annotations_for(t, ext))
    o = [f"{ind}test({ts(t['id'] + ' ' + t['title'])}, {{",
         f"{ind}  tag: [{', '.join(ts(x) for x in tags_for(t))}],",
         f"{ind}  annotation: [{ann}],",
         f"{ind}}}, async ({fixture_arg(t)}) => {{",
         f"{ind}  test.fixme(true, {ts(MARK + ' ' + t['id'] + ': implement the steps, then delete this line')});"]
    for p in as_list(t.get("preconditions")):
        o.append(f"{ind}  // Precondition: {comment(p)}")
    for d in as_list(t.get("test_data")):
        o.append(f"{ind}  // Test data: {comment(d)}")
    for i, s in enumerate(t.get("steps", []), 1):
        o.append(f"{ind}  await test.step({ts(f'{i}. ' + comment(s.get('action', '')))}, async () => {{")
        if s.get("data"):
            o.append(f"{ind}    // data: {comment(s['data'])}")
        o.append(f"{ind}    // expected: {comment(s.get('expected', ''))}")
        o.append(f"{ind}  }});")
    for p in as_list(t.get("postconditions")):
        o.append(f"{ind}  // Postcondition: {comment(p)}")
    o.append(f"{ind}}});")
    return o


def render_data_driven(group: list[dict], ext: dict, ind: str, n: int) -> list[str]:
    ids = ", ".join(t["id"] for t in group)
    var = f"cases{n}"
    common = set.intersection(*[set(as_list(t.get("preconditions"))) for t in group])
    o = [f"{ind}// Data-driven: {ids}. The steps are identical; values live in each case.",
         f"{ind}const {var} = ["]
    for t in group:
        ann = ", ".join(f"{{ type: {ts(k)}, description: {ts(v)} }}" for k, v in annotations_for(t, ext))
        pre = [p for p in as_list(t.get("preconditions")) if p not in common] + as_list(t.get("test_data"))
        o += [f"{ind}  {{",
              f"{ind}    id: {ts(t['id'])},",
              f"{ind}    title: {ts(t['title'])},",
              f"{ind}    tag: [{', '.join(ts(x) for x in tags_for(t))}],",
              f"{ind}    annotation: [{ann}],",
              f"{ind}    pre: [{', '.join(ts(comment(p)) for p in pre)}],",
              f"{ind}    steps: ["]
        o += [f"{ind}      {{ data: {ts(s.get('data', ''))}, expected: {ts(comment(s.get('expected', '')))} }},"
              for s in t.get("steps", [])]
        o += [f"{ind}    ],", f"{ind}  }},"]
    o += [f"{ind}];", f"{ind}for (const c of {var}) {{",
          f"{ind}  test(`${{c.id}} ${{c.title}}`, {{ tag: c.tag, annotation: c.annotation }}, async ({fixture_arg(group[0])}) => {{",
          f"{ind}    test.fixme(true, {ts(MARK + ' (data-driven: ' + ids + '): implement the steps, then delete this line')});",
          f"{ind}    // Case-specific preconditions and data: c.pre"]
    for p in sorted(common):
        o.append(f"{ind}    // Precondition: {comment(p)}")
    for i, s in enumerate(group[0].get("steps", []), 1):
        o.append(f"{ind}    await test.step({ts(f'{i}. ' + comment(s.get('action', '')))}, async () => {{")
        o.append(f"{ind}      // data: c.steps[{i - 1}].data · expected: c.steps[{i - 1}].expected")
        o.append(f"{ind}    }});")
    o += [f"{ind}  }});", f"{ind}}}"]
    return o


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tests", required=True)
    ap.add_argument("--requirements")
    ap.add_argument("--out", required=True, help="tests folder of the automation project")
    ap.add_argument("--fixtures", help="fixtures module (default: <out>/fixtures.ts)")
    ap.add_argument("--only", help="comma-separated TC IDs")
    ap.add_argument("--all", action="store_true", help="ignore automation.candidate")
    ap.add_argument("--no-data-driven", action="store_true")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    try:
        tc = json.loads(Path(a.tests).read_text(encoding="utf-8-sig"))
        rq = json.loads(Path(a.requirements).read_text(encoding="utf-8-sig")) if a.requirements else {}
    except (OSError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    tests = tc["test_cases"] if isinstance(tc, dict) else tc
    reqs = {r["id"]: r for r in (rq.get("requirements", []) if isinstance(rq, dict) else rq)}
    ext = {k: r.get("external_id") for k, r in reqs.items()}
    out = Path(a.out)
    fixtures = Path(a.fixtures) if a.fixtures else out / "fixtures.ts"

    wanted = {x.strip() for x in a.only.split(",")} if a.only else None
    done = existing_ids(out)
    sel, skipped_existing, not_candidate = [], [], []
    for t in tests:
        if t.get("status") == "deprecated" or t.get("technique") == "exploratory":
            continue
        if wanted and t["id"] not in wanted:
            continue
        if not a.all and not (t.get("automation") or {}).get("candidate"):
            not_candidate.append(t["id"])
            continue
        if t["id"] in done:
            skipped_existing.append(t["id"])
            continue
        sel.append(t)

    groups: "OrderedDict[str, list]" = OrderedDict()
    for t in sel:
        key = (t.get("requirement_ids") or ["no-req"])[0]
        groups.setdefault(key, []).append(t)

    written = []
    for rid, items in groups.items():
        title = reqs.get(rid, {}).get("title", "")
        path = out / f"{slug(rid, 12)}{('-' + slug(title, 40)) if title else ''}.spec.ts"
        imp = os.path.relpath(fixtures.with_suffix(""), path.parent).replace("\\", "/")
        imp = imp if imp.startswith(".") else "./" + imp
        blocks, used = [], set()
        n = 1
        if not a.no_data_driven:
            shapes: "OrderedDict[tuple, list]" = OrderedDict()
            for t in items:
                shapes.setdefault(step_shape(t), []).append(t)
            for shape, grp in shapes.items():
                if len(grp) >= 3 and shape[1]:
                    blocks.append(("dd", grp))
                    used |= {t["id"] for t in grp}
        for t in items:
            if t["id"] not in used:
                blocks.append(("one", t))
        body = [f"test.describe({ts((rid + ' ' + title).strip())}, () => {{"]
        for kind, item in blocks:
            body.append("")
            if kind == "dd":
                body += render_data_driven(item, ext, "  ", n)
                n += 1
            else:
                body += render_test(item, ext, "  ")
        body.append("});")
        if path.exists():
            # each describe callback is its own scope, so `const casesN` cannot clash with earlier blocks
            text = path.read_text(encoding="utf-8").rstrip() + "\n\n// Added by QA Suite generate_specs.py\n" + "\n".join(body) + "\n"
        else:
            head = [f"// Generated by QA Suite (generate_specs.py) from {Path(a.tests).name}.",
                    "// Tests keep their manual TC IDs as tags; remove each test.fixme(...) line once implemented.",
                    f"import {{ test, expect }} from {ts(imp)};", ""]
            text = "\n".join(head + body) + "\n"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")
        written.append((path, [t["id"] for t in items]))

    for p, ids in written:
        print(f"wrote {p}: {len(ids)} tests ({', '.join(ids)})")
    if skipped_existing:
        print(f"already automated (kept): {', '.join(skipped_existing)}")
    if not_candidate:
        print(f"not automation candidates (use --all to include): {', '.join(not_candidate)}")
    if not written:
        print("nothing new to generate")
    return 0


if __name__ == "__main__":
    sys.exit(main())
