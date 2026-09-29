#!/usr/bin/env python3
"""Routing/trigger evaluation for the whole QA Suite (Windows-compatible).

For every query it starts a headless Claude Code session (`claude -p`) in a temporary
project that contains all skills under .claude/skills/, and records the FIRST skill the
model reaches for (Skill tool call, or a Read of a SKILL.md). The session is killed as
soon as that first tool call is seen, so each query costs one short model turn.
This measures both triggering (does a QA Suite skill fire?) and routing (the right one?).

Uses the user's own Claude Code installation and account - ask before running.
skill-creator's run_eval.py relies on select() on pipes, which does not work on Windows;
this harness reads the stream with a thread instead.

Queries JSON: [{"query": "...", "expect": "designing-test-cases" | ["a", "b"] | "none"}]
  "none" = no QA Suite skill should fire (near-miss queries).

Usage:
  python tools/trigger_eval.py --claude "C:/.../claude.exe" --queries evals/trigger-queries.json \
      [--skills skills] [--workers 4] [--timeout 120] [--out evals/workspace/trigger/run1.json] [--only 1,5,9]
"""
from __future__ import annotations

import argparse
import json
import os
import queue
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def first_skill(claude: str, query: str, project: Path, suite: set[str], timeout: int) -> dict:
    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
    cmd = [claude, "-p", query, "--output-format", "stream-json", "--verbose", "--include-partial-messages"]
    start = time.time()
    proc = subprocess.Popen(cmd, cwd=project, env=env, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                            stdin=subprocess.DEVNULL)
    lines: "queue.Queue[str | None]" = queue.Queue()

    def pump():
        for raw in iter(proc.stdout.readline, b""):
            lines.put(raw.decode("utf-8", errors="replace"))
        lines.put(None)

    threading.Thread(target=pump, daemon=True).start()
    result = {"picked": None, "tool": None, "detail": "", "seconds": 0.0}
    pending, acc = None, ""
    try:
        while time.time() - start < timeout:
            try:
                line = lines.get(timeout=1.0)
            except queue.Empty:
                continue
            if line is None:
                break
            try:
                ev = json.loads(line)
            except ValueError:
                continue
            if ev.get("type") == "stream_event":
                se = ev.get("event", {})
                if se.get("type") == "content_block_start" and se.get("content_block", {}).get("type") == "tool_use":
                    pending, acc = se["content_block"].get("name", ""), ""
                elif se.get("type") == "content_block_delta" and pending:
                    acc += se.get("delta", {}).get("partial_json", "")
                elif se.get("type") == "content_block_stop" and pending:
                    result.update(classify(pending, acc, suite))
                    break
                elif se.get("type") == "message_stop" and not pending:
                    result.update({"picked": "none", "tool": None, "detail": "answered without tools"})
                    break
            elif ev.get("type") == "result":
                if result["picked"] is None:
                    result.update({"picked": "none", "detail": "finished without tool use"})
                break
    finally:
        if proc.poll() is None:
            proc.kill()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            pass
    if result["picked"] is None:
        result.update({"picked": "timeout", "detail": f"no decision within {timeout}s"})
    result["seconds"] = round(time.time() - start, 1)
    return result


def classify(tool: str, raw: str, suite: set[str]) -> dict:
    try:
        args = json.loads(raw) if raw else {}
    except ValueError:
        args = {"_raw": raw}
    if tool == "Skill":
        name = str(args.get("skill", args.get("_raw", ""))).split(":")[-1]
        return {"picked": name if name in suite else f"other-skill:{name}", "tool": tool, "detail": name}
    if tool == "Read":
        path = str(args.get("file_path", "")).replace("\\", "/")
        for s in suite:
            if f"/{s}/SKILL.md" in path:
                return {"picked": s, "tool": tool, "detail": path}
    return {"picked": "none", "tool": tool, "detail": raw[:120]}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--claude", required=True)
    ap.add_argument("--queries", required=True)
    ap.add_argument("--skills", default=str(ROOT / "skills"))
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--timeout", type=int, default=120)
    ap.add_argument("--only", help="comma-separated 1-based query numbers")
    ap.add_argument("--out")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    queries = json.loads(Path(a.queries).read_text(encoding="utf-8"))
    idx = [int(x) - 1 for x in a.only.split(",")] if a.only else range(len(queries))
    suite = {p.name for p in Path(a.skills).iterdir() if (p / "SKILL.md").exists()}

    project = Path(tempfile.mkdtemp(prefix="qa-trigger-"))
    shutil.copytree(a.skills, project / ".claude" / "skills")
    (project / "README.md").write_text("Scratch project for skill trigger evaluation.\n", encoding="utf-8")
    rows = []
    try:
        with ThreadPoolExecutor(max_workers=a.workers) as ex:
            futs = {ex.submit(first_skill, a.claude, queries[i]["query"], project, suite, a.timeout): i for i in idx}
            for fut in as_completed(futs):
                i = futs[fut]
                q = queries[i]
                r = fut.result()
                exp = q["expect"] if isinstance(q["expect"], list) else [q["expect"]]
                ok = r["picked"] in exp or (exp == ["none"] and (r["picked"] == "none" or r["picked"].startswith("other-skill:")))
                rows.append({"n": i + 1, "query": q["query"], "expect": exp, **r, "ok": ok})
                print(f"{'✔' if ok else '✘'} #{i + 1:02d} expect {'/'.join(exp):28s} got {r['picked']:28s} {r['seconds']:5.1f}s  {q['query'][:60]}",
                      flush=True)
    finally:
        shutil.rmtree(project, ignore_errors=True)
    rows.sort(key=lambda r: r["n"])
    per = {}
    for r in rows:
        for e in r["expect"]:
            per.setdefault(e, [0, 0])
        key = r["expect"][0]
        per[key][1] += 1
        per[key][0] += int(r["ok"])
    acc = round(100 * sum(r["ok"] for r in rows) / len(rows), 1) if rows else 0
    summary = {"accuracy_pct": acc, "n": len(rows), "per_expected": {k: f"{v[0]}/{v[1]}" for k, v in sorted(per.items()) if v[1]},
               "timeouts": sum(1 for r in rows if r["picked"] == "timeout"), "results": rows}
    print(f"\naccuracy {acc}% ({sum(r['ok'] for r in rows)}/{len(rows)}) · timeouts {summary['timeouts']}")
    for k, v in summary["per_expected"].items():
        print(f"  {k:28s} {v}")
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"wrote {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
