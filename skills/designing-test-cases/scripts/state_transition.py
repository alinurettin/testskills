#!/usr/bin/env python3
"""State transition analysis and test sequence generation.

From a state model it produces:
  - state table (state x event) - empty cells are invalid-transition test
    candidates (and questions: "what should happen if <event> in <state>?")
  - model defects: unreachable states, non-final dead ends, final states with
    outgoing transitions, nondeterminism (same state+event without guards)
  - valid test sequences achieving 0-switch coverage (every transition once)
    or 1-switch coverage (every pair of consecutive transitions), each
    starting at the initial state
  - invalid-transition test conditions

Spec (JSON):
{
  "id": "DS-003", "title": "Order lifecycle", "requirement_ids": ["REQ-010"],
  "initial": "Created",
  "final": ["Delivered", "Cancelled"],
  "transitions": [
    {"id": "T1", "from": "Created", "event": "pay", "to": "Paid", "guard": "payment approved"},
    {"id": "T2", "from": "Created", "event": "pay", "to": "Created", "guard": "payment declined"},
    {"from": "Paid", "event": "ship", "to": "Shipped", "action": "send tracking e-mail"}
  ],
  "events": ["pay", "ship", "deliver", "cancel"],       # optional, derived if omitted
  "ignore_invalid": [{"state": "Delivered", "event": "*"}]  # optional: cells not worth testing
}

Usage:
  python state_transition.py spec.json [--switch 0|1] [--max-length 12] [--format md|json] [--lang tr] [--out f]
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import deque
from pathlib import Path

T = {
    "en": {"title": "State transition design", "table": "State table (— = no transition defined)",
           "defects": "Model findings (clarify)", "seq": "Valid test sequences", "invalid": "Invalid transition tests",
           "summary": "{s} states · {e} events · {t} transitions · coverage: {cov} · sequences: {n} · "
                      "invalid-transition candidates: {inv}",
           "unreach": "State '{s}' is unreachable from the initial state '{i}'.",
           "dead": "State '{s}' has no outgoing transitions but is not declared final.",
           "finalout": "Final state '{s}' has outgoing transitions.",
           "nondet": "State '{s}' + event '{e}' has several transitions without distinguishing guards ({ids}).",
           "uncov": "Transitions not coverable from the initial state: {ids}",
           "state": "State", "event": "Event", "steps": "Steps", "path": "Path", "covers": "Covers",
           "expected": "Expected", "reject": "rejected / no state change (confirm expected behaviour)",
           "id": "ID", "cells": "{n} of {m} (state, event) cells have no transition"},
    "tr": {"title": "Durum geçişi tasarımı", "table": "Durum tablosu (— = tanımlı geçiş yok)",
           "defects": "Model bulguları (netleştirilmeli)", "seq": "Geçerli test dizileri",
           "invalid": "Geçersiz geçiş testleri",
           "summary": "{s} durum · {e} olay · {t} geçiş · kapsam: {cov} · dizi: {n} · geçersiz geçiş adayı: {inv}",
           "unreach": "'{s}' durumuna başlangıç durumu '{i}' üzerinden ulaşılamıyor.",
           "dead": "'{s}' durumundan çıkış geçişi yok ama son durum olarak tanımlanmamış.",
           "finalout": "Son durum '{s}' için çıkış geçişleri tanımlı.",
           "nondet": "'{s}' durumu + '{e}' olayı için ayırt edici koşulu (guard) olmayan birden fazla geçiş var ({ids}).",
           "uncov": "Başlangıç durumundan kapsanamayan geçişler: {ids}",
           "state": "Durum", "event": "Olay", "steps": "Adımlar", "path": "Yol", "covers": "Kapsadığı",
           "expected": "Beklenen", "reject": "reddedilir / durum değişmez (beklenen davranışı teyit edin)",
           "id": "ID", "cells": "{m} (durum, olay) hücresinden {n} tanesinde geçiş yok"},
}


def load_model(spec: dict):
    trans = []
    for i, t in enumerate(spec["transitions"], 1):
        t = dict(t)
        t.setdefault("id", f"T{i}")
        trans.append(t)
    states = list(dict.fromkeys([spec["initial"]] + [x for t in trans for x in (t["from"], t["to"])]
                                + list(spec.get("final", [])) + list(spec.get("states", []))))
    events = list(dict.fromkeys(spec.get("events") or [t["event"] for t in trans]))
    return states, events, trans


def shortest_path(trans, start, goal_pred):
    """BFS over transitions; returns list of transitions from start to a state satisfying goal_pred."""
    if goal_pred(start):
        return []
    prev = {start: None}
    q = deque([start])
    while q:
        s = q.popleft()
        for t in trans:
            if t["from"] == s and t["to"] not in prev:
                prev[t["to"]] = t
                if goal_pred(t["to"]):
                    path, cur = [], t["to"]
                    while prev[cur] is not None:
                        path.append(prev[cur])
                        cur = prev[cur]["from"]
                    return list(reversed(path))
                q.append(t["to"])
    return None


def _contains(seq_ids: list, window: list) -> bool:
    n = len(window)
    return any(seq_ids[k:k + n] == window for k in range(len(seq_ids) - n + 1))


def cover(trans, initial, finals, targets, max_len):
    """Greedy: targets are tuples of consecutive transitions to traverse."""
    remaining = list(targets)
    sequences = []
    unreachable = []
    while remaining:
        seq, cur = [], initial
        progressed = False
        while remaining and len(seq) < max_len:
            # nearest remaining target from current state
            best = None
            for tg in remaining:
                p = shortest_path(trans, cur, lambda s, tg=tg: s == tg[0]["from"])
                if p is not None and (best is None or len(p) < len(best[0])):
                    best = (p, tg)
            if best is None:
                break
            p, tg = best
            if seq and len(seq) + len(p) + len(tg) > max_len:
                break
            seq += p + list(tg)
            cur = tg[-1]["to"]
            progressed = True
            ids = [x["id"] for x in seq]
            remaining = [r for r in remaining if not _contains(ids, [x["id"] for x in r])]
            if cur in finals and not any(t["from"] == cur for t in trans):
                break
        if not progressed:
            unreachable = remaining
            break
        sequences.append(seq)
    return sequences, unreachable


def run(spec: dict, switch: int, max_len: int) -> dict:
    states, events, trans = load_model(spec)
    initial, finals = spec["initial"], set(spec.get("final", []))
    ignore = spec.get("ignore_invalid", [])
    findings = []

    reach = {initial}
    frontier = [initial]
    while frontier:
        s = frontier.pop()
        for t in trans:
            if t["from"] == s and t["to"] not in reach:
                reach.add(t["to"])
                frontier.append(t["to"])
    for s in states:
        outs = [t for t in trans if t["from"] == s]
        if s not in reach:
            findings.append(("unreach", {"s": s, "i": initial}))
        if not outs and s not in finals:
            findings.append(("dead", {"s": s}))
        if outs and s in finals:
            findings.append(("finalout", {"s": s}))
    for s in states:
        for e in events:
            same = [t for t in trans if t["from"] == s and t["event"] == e]
            guards = [t.get("guard") for t in same]
            if len(same) > 1 and (None in guards or len(set(guards)) < len(guards)):
                findings.append(("nondet", {"s": s, "e": e, "ids": ", ".join(t["id"] for t in same)}))

    table = {s: {e: [t for t in trans if t["from"] == s and t["event"] == e] for e in events} for s in states}

    def ignored(s, e):
        return any(i.get("state") in (s, "*") and i.get("event") in (e, "*") for i in ignore)

    invalid = [(s, e) for s in states for e in events
               if not table[s][e] and not ignored(s, e) and s in reach]

    if switch == 0:
        targets = [(t,) for t in trans]
    else:
        targets = [(a, b) for a in trans for b in trans if a["to"] == b["from"]]
        targets += [(t,) for t in trans if not any(t["to"] == b["from"] for b in trans)]
    sequences, unreachable = cover(trans, initial, finals, targets, max_len)

    return {
        "id": spec.get("id"), "title": spec.get("title"), "requirement_ids": spec.get("requirement_ids", []),
        "states": states, "events": events, "initial": initial, "final": sorted(finals),
        "coverage": f"{switch}-switch",
        "table": {s: {e: [f"{t['id']}→{t['to']}" + (f" [{t['guard']}]" if t.get("guard") else "")
                          for t in table[s][e]] for e in events} for s in states},
        "findings": [{"type": k, **v} for k, v in findings],
        "uncoverable": [[x["id"] for x in tg] for tg in unreachable],
        "sequences": [{"id": f"S-{i:02d}", "transitions": [t["id"] for t in seq],
                       "steps": [{"from": t["from"], "event": t["event"], "guard": t.get("guard"),
                                  "to": t["to"], "action": t.get("action")} for t in seq]}
                      for i, seq in enumerate(sequences, 1)],
        "invalid_transitions": [{"id": f"N-{i:02d}", "state": s, "event": e,
                                 "path_to_state": [t["id"] for t in (shortest_path(trans, initial, lambda x, s=s: x == s) or [])]}
                                for i, (s, e) in enumerate(invalid, 1)],
        "summary": {"states": len(states), "events": len(events), "transitions": len(trans),
                    "sequences": len(sequences), "invalid_candidates": len(invalid),
                    "empty_cells": sum(1 for s in states for e in events if not table[s][e]),
                    "cells": len(states) * len(events)},
    }


def to_md(res: dict, lang: str) -> str:
    t = T[lang]
    s = res["summary"]
    o = [f"# {t['title']}: {res.get('id') or ''} {res.get('title') or ''}".rstrip(), ""]
    if res["requirement_ids"]:
        o.append("REQ: " + ", ".join(res["requirement_ids"]))
    o += [t["summary"].format(s=s["states"], e=s["events"], t=s["transitions"], cov=res["coverage"],
                              n=s["sequences"], inv=s["invalid_candidates"]), ""]
    if res["findings"] or res["uncoverable"]:
        o += [f"## ⚠ {t['defects']}", ""]
        for f in res["findings"]:
            o.append("- " + t[f["type"]].format(**{k: v for k, v in f.items() if k != "type"}))
        if res["uncoverable"]:
            o.append("- " + t["uncov"].format(ids=", ".join("+".join(x) for x in res["uncoverable"])))
        o.append("")
    o += [f"## {t['table']}", "", f"| {t['state']} \\ {t['event']} | " + " | ".join(res["events"]) + " |",
          "|---|" + "---|" * len(res["events"])]
    for st in res["states"]:
        mark = " (start)" if st == res["initial"] else " (final)" if st in res["final"] else ""
        o.append(f"| **{st}**{mark} | " + " | ".join("<br>".join(res["table"][st][e]) or "—" for e in res["events"]) + " |")
    o += ["", t["cells"].format(n=s["empty_cells"], m=s["cells"]), "",
          f"## {t['seq']} ({res['coverage']})", "", f"| {t['id']} | {t['path']} | {t['steps']} |", "|---|---|---|"]
    for q in res["sequences"]:
        path = res["initial"] + "".join(f" –{x['event']}" + (f"[{x['guard']}]" if x["guard"] else "") + f"→ {x['to']}"
                                        for x in q["steps"])
        o.append(f"| {q['id']} | {path} | {len(q['steps'])} |")
    if res["invalid_transitions"]:
        o += ["", f"## {t['invalid']}", "", f"| {t['id']} | {t['state']} | {t['event']} | {t['path']} | {t['expected']} |",
              "|---|---|---|---|---|"]
        for n in res["invalid_transitions"]:
            o.append(f"| {n['id']} | {n['state']} | {n['event']} | {' → '.join(n['path_to_state']) or '(start)'} | {t['reject']} |")
    return "\n".join(o) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec")
    ap.add_argument("--switch", type=int, choices=[0, 1], default=0)
    ap.add_argument("--max-length", type=int, default=15, help="max transitions per sequence")
    ap.add_argument("--lang", choices=["en", "tr"])
    ap.add_argument("--format", choices=["md", "json"], default="md")
    ap.add_argument("--out")
    a = ap.parse_args()
    try:
        spec = json.loads(Path(a.spec).read_text(encoding="utf-8-sig"))
        lang = a.lang or spec.get("language", "en")
        lang = lang if lang in T else "en"
        res = run(spec, a.switch, a.max_length)
    except (OSError, ValueError, KeyError, TypeError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    text = json.dumps(res, ensure_ascii=False, indent=2) if a.format == "json" else to_md(res, lang)
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(text, encoding="utf-8")
        print(f"wrote {a.out}")
    else:
        sys.stdout.reconfigure(encoding="utf-8")
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
