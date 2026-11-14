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
           "redundant": "Redundant rules (another rule with the same outcome already covers them)",
           "untested": "Condition values no test input uses (add a test or use --coverage full)",
           "checksum": "Checksum: minimised columns represent {m} combinations = {k} with an outcome + {a} infeasible "
                       "absorbed as don't care; full table {f} = {k} + {g} gaps + {c} conflicts + {i} infeasible → {ok}",
           "tests": "Coverage items → test inputs", "cond": "Condition", "action": "Action", "rule": "Rule",
           "none": "none", "undetermined": "UNDEFINED", "conflict": "CONFLICT", "col": "Column",
           "id": "ID", "values": "Condition values", "expected": "Expected outcome", "covers": "Covers"},
    "tr": {"title": "Karar tablosu", "summary": "Kombinasyon: {total} (olası {feas}) · kural: {rules} · "
           "boşluk: {gaps} · çelişki: {conf} · sadeleştirilmiş kolon: {cols} · test koşulu: {tc}",
           "gaps": "Boşluklar: hiçbir kuralın kapsamadığı kombinasyonlar (ne olması gerektiğini sorun)",
           "conf": "Çelişkiler: aynı kombinasyon için kurallar farklı sonuç veriyor",
           "overlap": "Kural sırası ile çözülen örtüşmeler (ilk eşleşen)",
           "dead": "Ölü kurallar (hiçbir olası kombinasyonla eşleşmiyor)", "collapsed": "Sadeleştirilmiş karar tablosu",
           "redundant": "Gereksiz kurallar (aynı sonucu veren başka bir kural zaten kapsıyor)",
           "untested": "Hiçbir test girdisinin kullanmadığı koşul değerleri (test ekleyin veya --coverage full kullanın)",
           "checksum": "Sağlama: sadeleştirilmiş kolonlar {m} kombinasyonu temsil ediyor = sonucu olan {k} + önemsiz "
                       "sayılan {a} olanaksız; tam tablo {f} = {k} + {g} boşluk + {c} çelişki + {i} olanaksız → {ok}",
           "tests": "Kapsam öğeleri → test girdileri", "cond": "Koşul", "action": "Aksiyon", "rule": "Kural",
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


def collapse(rows: list[dict], conds: list[dict], feasible_ids: dict | None = None) -> list[dict]:
    """Merge rows with identical outcome that differ in one condition only.

    A merge needs every value of that condition to be either present in the group or impossible:
    infeasible combinations are disregarded (treated as don't care), as CTAL-TA v4.0 section 3.3.1
    recommends. feasible_ids maps each feasible combination (tuple of values in condition order)
    to its row ID; without it only a group that covers the whole domain is merged.
    """
    rows = [dict(r, values=dict(r["values"]), covers=list(r["covers"])) for r in rows]
    names = [c["name"] for c in conds]
    domains = {c["name"]: c["values"] for c in conds}

    def cube_has_feasible(values: dict) -> bool:
        if feasible_ids is None:
            return True
        axes = [domains[n] if values[n] == DASH else [values[n]] for n in names]
        return any(combo in feasible_ids for combo in itertools.product(*axes))

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
                present = {r["values"][name] for r in grp}
                missing = [v for v in domain if v not in present]
                if all(not cube_has_feasible(dict(grp[0]["values"], **{name: v})) for v in missing):
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

    size = 1
    for c in conds:
        size *= len(c["values"])
    limit = int(spec.get("max_combinations", MAX_COMBINATIONS))
    if size > limit:
        raise ValueError(f"{size} combinations ({len(conds)} conditions) exceed the limit of {limit}. "
                         "Split the rule set into independent tables, merge condition values into "
                         "equivalence classes, or use pairwise.py for configuration-style factors. "
                         "Raise the limit with --max-combinations only if you really need the full table.")
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

    # redundant rules: every feasible combination a rule matches is also matched by one other rule with the
    # same outcome (of two identical rules the later one is reported)
    feasible_rows = [t for t in table]
    match_ids = {r["id"]: {t["id"] for t in feasible_rows if matches(r["when"], t["values"])} for r in rules}
    redundant = []
    for i, a in enumerate(rules):
        if not match_ids[a["id"]] or a["id"] in dead:
            continue
        for j, b in enumerate(rules):
            if i == j or outcome_key(a["then"], actions) != outcome_key(b["then"], actions):
                continue
            if match_ids[a["id"]] < match_ids[b["id"]] or (match_ids[a["id"]] == match_ids[b["id"]] and j < i):
                redundant.append({"rule": a["id"], "subsumed_by": b["id"]})
                break

    ok_rows = [r for r in table if r["status"] == "ok"]
    feasible_ids = {tuple(t["values"][n] for n in names): t["id"] for t in table}
    collapsed = collapse(ok_rows, conds, feasible_ids)
    for i, r in enumerate(collapsed, 1):
        r["column"] = f"D{i:02d}"

    # checksum (CTAL-TA v4.0 section 3.3.1): each "-" multiplies a column's score by the number of values
    by_id = {t["id"]: t for t in table}
    score = 0
    for r in collapsed:
        n = 1
        for c in conds:
            if r["values"][c["name"]] == DASH:
                n *= len(c["values"])
        score += n
    absorbed = score - len(ok_rows)
    covered_ids = [x for r in collapsed for x in r["covers"]]
    exact = True   # every column represents exactly its own feasible combinations, none twice
    for r in collapsed:
        inside = {t["id"] for t in table if all(r["values"][n] in (DASH, t["values"][n]) for n in names)}
        exact = exact and inside == set(r["covers"])
    infeasible_n = len(combos) - feasible
    checksum = {"minimised": score, "with_outcome": len(ok_rows), "infeasible_absorbed": absorbed,
                "full_table": len(combos), "gaps": len(gaps), "conflicts": len(conflicts),
                "infeasible": infeasible_n,
                "ok": (exact and len(covered_ids) == len(set(covered_ids)) == len(ok_rows) and 0 <= absorbed <= infeasible_n
                       and len(combos) == len(ok_rows) + len(gaps) + len(conflicts) + infeasible_n)}

    source = collapsed if coverage == "collapsed" else ok_rows
    tests = []
    seen_pairs = {(n, r["values"][n]) for r in source for n in names if r["values"][n] != DASH}
    for i, r in enumerate(source, 1):
        # "-" cells rotate: take the covered combination that shows the most condition values no test has
        # used yet (the first one on a tie), so a feasible value is not left untested by the collapsing
        best, best_gain = None, -1
        for cid in r["covers"]:
            vals = by_id[cid]["values"]
            gain = sum(1 for n in names if r["values"][n] == DASH and (n, vals[n]) not in seen_pairs)
            if gain > best_gain:
                best, best_gain = vals, gain
        concrete = dict(best)
        seen_pairs |= set(concrete.items())
        tests.append({"id": f"C-{i:02d}", "values": concrete,
                      "expected": dict(zip(actions, r["outcome"])),
                      "column": r.get("column", r["id"]), "covers": r["covers"]})
    testable = {(n, t["values"][n]) for t in ok_rows for n in names}
    untested = [{"condition": n, "value": v} for c in conds for n in [c["name"]] for v in c["values"]
                if (n, v) in testable and (n, v) not in seen_pairs]
    for g in gaps + conflicts + overlaps:
        g["values"] = g.pop("combo")
    return {
        "id": spec.get("id"), "title": spec.get("title"), "requirement_ids": spec.get("requirement_ids", []),
        "conditions": conds, "actions": actions, "first_match": first_match,
        "summary": {"combinations": len(combos), "feasible": feasible, "rules": len(rules), "gaps": len(gaps),
                    "conflicts": len(conflicts), "overlaps": len(overlaps), "dead_rules": len(dead),
                    "collapsed_columns": len(collapsed), "test_conditions": len(tests),
                    "redundant_rules": len(redundant), "untested_values": len(untested)},
        "gaps": gaps, "conflicts": conflicts, "overlaps": overlaps, "dead_rules": dead,
        "redundant_rules": redundant, "checksum": checksum, "untested_values": untested,
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
    if res.get("redundant_rules"):
        o += [f"## {t['redundant']}", ""] + [f"- {x['rule']} ⊆ {x['subsumed_by']}" for x in res["redundant_rules"]] + [""]
    if res.get("untested_values"):
        o += [f"## ⚠ {t['untested']}", ""] + [f"- {x['condition']}={x['value']}" for x in res["untested_values"]] + [""]
    ck = res.get("checksum")
    if ck:
        o += [t["checksum"].format(m=ck["minimised"], k=ck["with_outcome"], a=ck["infeasible_absorbed"],
                                   f=ck["full_table"], g=ck["gaps"], c=ck["conflicts"], i=ck["infeasible"],
                                   ok="OK" if ck["ok"] else "MISMATCH"), ""]
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


MAX_COMBINATIONS = 2048


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec")
    ap.add_argument("--coverage", choices=["collapsed", "full"], default="collapsed")
    ap.add_argument("--lang", choices=["en", "tr"])
    ap.add_argument("--format", choices=["md", "json"], default="md")
    ap.add_argument("--out")
    ap.add_argument("--max-combinations", type=int, help=f"guard against combinatorial explosion (default {MAX_COMBINATIONS})")
    sys.stdout.reconfigure(encoding="utf-8")
    a = ap.parse_args()
    try:
        spec = json.loads(Path(a.spec).read_text(encoding="utf-8-sig"))
        if a.max_combinations:
            spec["max_combinations"] = a.max_combinations
        lang = a.lang or spec.get("language", "en")
        lang = lang if lang in T else "en"
        res = run(spec, a.coverage, lang)
    except (OSError, ValueError, KeyError, TypeError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    text = json.dumps(res, ensure_ascii=False, indent=2) if a.format == "json" else to_md(res, lang)
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(text, encoding="utf-8", newline="\n")
        print(f"wrote {a.out}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
