#!/usr/bin/env python3
"""Proxy routing evaluation: does the right skill get picked from its name + description?

This is NOT Claude Code's real trigger mechanism (see tools/trigger_eval.py for that, which needs a
logged-in `claude` CLI). It measures the same signal cheaply: a model sees only the skill list
(name: description) and picks one skill per request, or "none".

  1. python tools/routing_proxy.py build evals/trigger-queries.json [more.json ...] --out prompt.txt
     Give prompt.txt to a model (a fresh session or a subagent without tools) and save its JSON answer.
  2. python tools/routing_proxy.py score evals/trigger-queries.json [more.json ...] --answers answers.json \
         --out evals/results/routing-proxy-<date>.json

Query files are JSON lists of {"query": str, "expect": str | [str, ...]} ("none" = no skill expected).
The answer is a JSON list of {"n": 1, "skill": "...", "why": "..."} in prompt order.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

HEAD = """You are simulating the skill-selection step of Claude Code. Below is the list of available skills exactly as the model sees it (name: description).
For EACH user request, decide independently (as if it were the only request in a fresh session) which ONE skill you would invoke first with the Skill tool, or 'none' if you would answer or act without any skill.
Judge each request on its own. Do not use any tools; answer from the list only.

## Available skills
"""


def skills() -> list[tuple[str, str]]:
    out = []
    for p in sorted((ROOT / "skills").glob("*/SKILL.md")):
        fm = p.read_text(encoding="utf-8").split("---")[1]
        name = re.search(r"^name:\s*(.+)$", fm, re.M).group(1).strip()
        desc = re.search(r"^description:\s*(.+)$", fm, re.M).group(1).strip()
        out.append((name, desc))
    return out


def load_queries(files: list[str]) -> list[dict]:
    rows = []
    for f in files:
        for q in json.loads(Path(f).read_text(encoding="utf-8")):
            exp = q["expect"] if isinstance(q["expect"], list) else [q["expect"]]
            rows.append({"query": q["query"], "expect": exp, "set": Path(f).stem})
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=["build", "score"])
    ap.add_argument("queries", nargs="+")
    ap.add_argument("--answers")
    ap.add_argument("--out", required=True)
    sys.stdout.reconfigure(encoding="utf-8")
    a = ap.parse_args()
    rows = load_queries(a.queries)
    if a.mode == "build":
        text = HEAD + "\n".join(f"- {n}: {d}" for n, d in skills())
        text += "\n\n## Requests\n" + "\n".join(f"{i}. {r['query']}" for i, r in enumerate(rows, 1))
        text += '\n\nReturn ONLY a JSON array like [{"n":1,"skill":"...","why":"<=12 words"}, ...] covering all requests.\n'
        Path(a.out).write_text(text, encoding="utf-8")
        print(f"wrote {a.out}: {len(skills())} skills, {len(rows)} requests")
        return 0
    if not a.answers:
        ap.error("score needs --answers")
    raw = Path(a.answers).read_text(encoding="utf-8")
    answers = {x["n"]: x["skill"] for x in json.loads(raw[raw.index("["): raw.rindex("]") + 1])}
    result = {"method": "proxy: a model chose a skill from the name+description list (not the real Claude Code trigger mechanism)",
              "skills": len(skills()), "sets": {}}
    for i, r in enumerate(rows, 1):
        picked = answers.get(i, "missing")
        s = result["sets"].setdefault(r["set"], {"ok": 0, "n": 0, "rows": []})
        ok = picked in r["expect"]
        s["ok"] += ok
        s["n"] += 1
        s["rows"].append({"query": r["query"], "expect": r["expect"], "picked": picked, "ok": ok})
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    for name, s in result["sets"].items():
        print(f"{name}: {s['ok']}/{s['n']}")
        for x in s["rows"]:
            if not x["ok"]:
                print(f"  MISS expected {'|'.join(x['expect'])}, picked {x['picked']}: {x['query'][:90]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
