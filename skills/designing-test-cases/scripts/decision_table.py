#!/usr/bin/env python3
"""Decision table analysis: completeness, conflicts, collapsing, test conditions.

Business rules are given as partial condition assignments ("don't care" =
condition omitted). The script expands all combinations and reports:
  - GAPS: feasible combinations no rule covers   -> clarification questions
  - CONFLICTS: combinations where rules disagree  -> requirement defects
  - DEAD RULES: rules that match no feasible combination
  - a collapsed table ("-" = don't care) and one test condition per column
    (or per full combination with --coverage full)

Spec (JSON):
{
  "id": "DS-002", "title": "Coupon eligibility", "requirement_ids": ["REQ-001", "REQ-002"],
  "conditions": [
    {"name": "registered", "values": ["Y", "N"]},
    {"name": "basket_total", "values": ["<100", ">=100"]},
    {"name": "coupon", "values": ["valid", "expired", "unknown"]}
  ],
  "actions": ["apply_discount", "message"],
  "rules": [
    {"id": "R1", "when": {"registered": "Y", "basket_total": ">=100", "coupon": "valid"},
     "then": {"apply_discount": "yes", "message": "Kupon uygulandı"}},
    {"id": "R2", "when": {"coupon": "expired"}, "then": {"apply_discount": "no", "message": "Süresi dolmuş"}}
  ],
  "infeasible": [ {"registered": "N", "coupon": "staff-only"} ],
  "first_match": false          # true = rules are ordered, first match wins (overlaps become info)
}

Usage:
  python decision_table.py spec.json [--coverage collapsed|full] [--format md|json] [--lang tr] [--out f]
"""
from __future__ import annotations

import argparse
import itertools
import json
import sys
from pathlib import Path

T = {
    "en": {"title": "Decision table", "summary": "Combinations: {total} (feasible {feas}) · rules: {rules} · "
           "gaps: {gaps} · conflicts: {conf} · collapsed columns: {cols} · test conditions: {tc}",
           "gaps": "Gaps: combinations no rule covers (ask what should happen)",
           "conf": "Conflicts: rules give different outcomes for the same combination",
           "overlap": "Overlaps resolved by rule order (first match)",
           "dead": "Dead rules (match no feasible combination)", "collapsed": "Collapsed decision table",
           "tests": "Test conditions", "cond": "Condition", "action": "Action", "rule": "Rule",
           "none": "none", "undetermined": "UNDEFINED", "conflict": "CONFLICT", "col": "Column",
           "id": "ID", "values": "Condition values", "expected": "Expected outcome", "covers": "Covers"},
    "tr": {"title": "Karar tablosu", "summary": "Kombinasyon: {total} (olası {feas}) · kural: {rules} · "
           "boşluk: {gaps} · çelişki: {conf} · sadeleştirilmiş kolon: {cols} · test koşulu: {tc}",
           "gaps": "Boşluklar: hiçbir kuralın kapsamadığı kombinasyonlar (ne olması gerektiğini sorun)",
           "conf": "Çelişkiler: aynı kombinasyon için kurallar farklı sonuç veriyor",
           "overlap": "Kural sırası ile çözülen örtüşmeler (ilk eşleşen)",
           "dead": "Ölü kurallar (hiçbir olası kombinasyonla eşleşmiyor)", "collapsed": "Sadeleştirilmiş karar tablosu",
           "tests": "Test koşulları", "cond": "Koşul", "action": "Aksiyon", "rule": "Kural",
           "none": "yok", "undetermined": "TANIMSIZ", "conflict": "ÇELİŞKİ", "col": "Kolon",
           "id": "ID", "values": "Koşul değerleri", "expected": "Beklenen sonuç", "covers": "Kapsadığı"},
}
DASH = "-"


def matches(partial: dict, combo: dict) -> bool:
    return all(combo.get(k) == v for k, v in partial.items())


def outcome_key(then: dict, actions: list[str]) -> tuple:
    return tuple(str(then.get(a, "")) for a in actions)


def validate(spec: dict) -> None:
    names = [c["name"] for c in spec["conditions"]]
    vals = {c["name"]: c["values"] for c in spec["conditions"]}
    if len(set(names)) != len(names):
        raise ValueError("duplicate condition names")
    for r in spec.get("rules", []):
        for k, v in r["when"].items():
            if k not in vals:
                raise ValueError(f"rule {r.get('id')}: unknown condition '{k}'")
            if v not in vals[k]:
                raise ValueError(f"rule {r.get('id')}: value '{v}' not in {vals[k]} for '{k}'")


def collapse(rows: list[dict], conds: list[dict]) -> list[dict]:
    """Merge rows with identical outcome whose values for one condition cover its whole domain."""
    rows = [dict(r, values=dict(r["values"]), covers=list(r["covers"])) for r in rows]
    changed = True
    while changed:
        changed = False
        for c in conds:
            name, domain = c["name"], c["values"]
            groups: dict = {}
            for r in rows:
                if r["values"][name] == DASH:
                    continue
                key = (r["outcome"], tuple((k, v) for k, v in sorted(r["values"].items()) if k != name))
                groups.setdefault(key, []).append(r)
            for key, grp in groups.items():
                if {r["values"][name] for r in grp} >= set(domain) and len(grp) >= len(domain):
                    merged = dict(grp[0], values=dict(grp[0]["values"]), covers=[])
                    merged["values"][name] = DASH
                    merged["rules"] = sorted({x for r in grp for x in r["rules"]})
                    for r in grp:
                        merged["covers"] += r["covers"]
                    rows = [r for r in rows if all(r is not g for g in grp)] + [merged]
                    changed = True
                    break
            if changed:
                break
    order = {c["name"]: c["values"] for c in conds}

    def sort_key(r):
        return tuple((-1 if r["values"][c] == DASH else order[c].index(r["values"][c])) for c in order)

    return sorted(rows, key=sort_key)


def run(spec: dict, coverage: str, lang: str) -> dict:
    validate(spec)
    conds = spec["conditions"]
    actions = spec.get("actions") or sorted({a for r in spec["rules"] for a in r["then"]})
    rules = spec["rules"]
    first_match = spec.get("first_match", False)
    infeasible = spec.get("infeasible", [])
    names = [c["name"] for c in conds]

    combos = [dict(zip(names, vals)) for vals in itertools.product(*[c["values"] for c in conds])]
    table, gaps, conflicts, overlaps = [], [], [], []
    used_rules: set[str] = set()
    feasible = 0
    for i, combo in enumerate(combos, 1):
        if any(matches(f, combo) for f in infeasible):
            continue
        feasible += 1
        hits = [r for r in rules if matches(r["when"], combo)]
        cid = f"K{i:03d}"
        if not hits:
            gaps.append({"combo": combo, "id": cid})
            table.append({"id": cid, "values": combo, "rules": [], "outcome": None, "status": "gap", "covers": [cid]})
            continue
        outs = {outcome_key(r["then"], actions) for r in hits}
        if first_match:
            used_rules.add(hits[0]["id"])
            if len(hits) > 1:
                overlaps.append({"combo": combo, "rules": [r["id"] for r in hits], "winner": hits[0]["id"]})
            table.append({"id": cid, "values": combo, "rules": [hits[0]["id"]],
                          "outcome": outcome_key(hits[0]["then"], actions), "status": "ok", "covers": [cid]})
        elif len(outs) > 1:
            used_rules.update(r["id"] for r in hits)
            conflicts.append({"combo": combo, "rules": [r["id"] for r in hits],
                              "outcomes": {r["id"]: r["then"] for r in hits}, "id": cid})
            table.append({"id": cid, "values": combo, "rules": [r["id"] for r in hits], "outcome": None,
                          "status": "conflict", "covers": [cid]})
        else:
            used_rules.update(r["id"] for r in hits)
            table.append({"id": cid, "values": combo, "rules": [r["id"] for r in hits], "outcome": outs.pop(),
                          "status": "ok", "covers": [cid]})
    dead = [r["id"] for r in rules if r["id"] not in used_rules]

    ok_rows = [r for r in table if r["status"] == "ok"]
    collapsed = collapse(ok_rows, conds)
    for i, r in enumerate(collapsed, 1):
        r["column"] = f"D{i:02d}"

    source = collapsed if coverage == "collapsed" else ok_rows
    tests = []
    for i, r in enumerate(source, 1):
        # "-" cells take their value from the first real combination this column covers
        first = next(t for t in table if t["id"] == r["covers"][0])
        concrete = dict(first["values"])
        tests.append({"id": f"C-{i:02d}", "values": concrete,
                      "expected": dict(zip(actions, r["outcome"])),
                      "column": r.get("column", r["id"]), "covers": r["covers"]})
    for g in gaps + conflicts + overlaps:
        g["values"] = g.pop("combo")
    return {
        "id": spec.get("id"), "title": spec.get("title"), "requirement_ids": spec.get("requirement_ids", []),
        "conditions": conds, "actions": actions, "first_match": first_match,
        "summary": {"combinations": len(combos), "feasible": feasible, "rules": len(rules), "gaps": len(gaps),
                    "conflicts": len(conflicts), "overlaps": len(overlaps), "dead_rules": len(dead),
                    "collapsed_columns": len(collapsed), "test_conditions": len(tests)},
        "gaps": gaps, "conflicts": conflicts, "overlaps": overlaps, "dead_rules": dead,
        "collapsed": [{"column": r["column"], "values": r["values"], "outcome": dict(zip(actions, r["outcome"])),
                       "rules": r["rules"], "covers": r["covers"]} for r in collapsed],
        "full_table": [{"id": r["id"], "values": r["values"], "status": r["status"], "rules": r["rules"],
                        "outcome": dict(zip(actions, r["outcome"])) if r["outcome"] else None} for r in table],
        "test_conditions": tests,
    }


def fmt_vals(v: dict) -> str:
    return ", ".join(f"{k}={x}" for k, x in v.items())


def to_md(res: dict, lang: str) -> str:
    t = T[lang]
    s = res["summary"]
    o = [f"# {t['title']}: {res.get('id') or ''} {res.get('title') or ''}".rstrip(), ""]
    if res["requirement_ids"]:
        o.append("REQ: " + ", ".join(res["requirement_ids"]))
    o += [t["summary"].format(total=s["combinations"], feas=s["feasible"], rules=s["rules"], gaps=s["gaps"],
                              conf=s["conflicts"], cols=s["collapsed_columns"], tc=s["test_conditions"]), ""]
    if res["gaps"]:
        o += [f"## ⚠ {t['gaps']}", ""] + [f"- {g['id']}: {fmt_vals(g['values'])}" for g in res["gaps"]] + [""]
    if res["conflicts"]:
        o += [f"## ⛔ {t['conf']}", ""]
        for c in res["conflicts"]:
            outs = "; ".join(f"{rid} → {fmt_vals(th)}" for rid, th in c["outcomes"].items())
            o.append(f"- {c['id']}: {fmt_vals(c['values'])} :: {outs}")
        o.append("")
    if res["overlaps"]:
        o += [f"## {t['overlap']}", ""] + [f"- {fmt_vals(x['values'])}: "
                                             f"{', '.join(x['rules'])} → {x['winner']}" for x in res["overlaps"]] + [""]
    if res["dead_rules"]:
        o += [f"## {t['dead']}", "", "- " + ", ".join(res["dead_rules"]), ""]
    cols = res["collapsed"]
    if cols:
        o += [f"## {t['collapsed']}", "", "| | " + " | ".join(c["column"] for c in cols) + " |",
              "|---|" + "---|" * len(cols)]
        for c in res["conditions"]:
            o.append(f"| **{t['cond']}:** {c['name']} | " + " | ".join(str(x["values"][c["name"]]) for x in cols) + " |")
        for a in res["actions"]:
            o.append(f"| **{t['action']}:** {a} | " + " | ".join(str(x["outcome"].get(a, "")) for x in cols) + " |")
        o.append(f"| {t['rule']} | " + " | ".join(",".join(x["rules"]) for x in cols) + " |")
        o.append("")
    o += [f"## {t['tests']}", "", f"| {t['id']} | {t['values']} | {t['expected']} | {t['col']} |", "|---|---|---|---|"]
    for tc in res["test_conditions"]:
        o.append(f"| {tc['id']} | {fmt_vals(tc['values'])} | {fmt_vals(tc['expected'])} | {tc['column']} |")
    return "\n".join(o) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec")
    ap.add_argument("--coverage", choices=["collapsed", "full"], default="collapsed")
    ap.add_argument("--lang", choices=["en", "tr"])
    ap.add_argument("--format", choices=["md", "json"], default="md")
    ap.add_argument("--out")
    a = ap.parse_args()
    try:
        spec = json.loads(Path(a.spec).read_text(encoding="utf-8-sig"))
        lang = a.lang or spec.get("language", "en")
        lang = lang if lang in T else "en"
        res = run(spec, a.coverage, lang)
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
