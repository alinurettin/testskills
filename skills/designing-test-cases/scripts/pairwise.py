#!/usr/bin/env python3
"""Combinatorial (pairwise / t-wise) test generation with constraints.

Deterministic greedy AETG-style generator with bounded exact completion.
Reports proven infeasible tuples separately from unresolved searches. Coverage
is successful only when every tuple is covered or proven impossible.

Spec (JSON):
{
  "id": "DS-004", "title": "Checkout compatibility", "requirement_ids": ["REQ-020"],
  "strength": 2,                                   # 2 = pairwise, 3 = 3-wise
  "parameters": [
    {"name": "browser", "values": ["Chrome", "Firefox", "Safari", "Edge"]},
    {"name": "os", "values": ["Windows", "macOS", "iOS", "Android"]},
    {"name": "payment", "values": ["card", "wallet", "transfer"]}
  ],
  "forbidden": [                                   # any test containing ALL pairs of an entry is invalid
    {"os": "Windows", "browser": "Safari"},
    {"os": ["iOS", "Android"], "browser": "Edge"}   # lists = any of these values
  ],
  "seed_tests": [ {"browser": "Chrome", "os": "Windows", "payment": "card"} ]   # must-include rows
}
Put only VALID values here. Test invalid values separately, one per test
(single-fault), so they do not mask each other.

Usage:
  python pairwise.py spec.json [--candidates 30] [--seed 42] [--format md|json|csv] [--lang tr] [--out f]
"""
from __future__ import annotations

import argparse
import csv
import io
import itertools
import json
import random
import sys
from math import isfinite, prod
from pathlib import Path

T = {
    "en": {"title": "Combinatorial design", "summary": "{n} tests cover {cov} verified feasible {t}-way combinations "
           "(exhaustive: {full} tests, reduction {red}%).", "infeasible": "Combinations excluded by constraints",
           "unplaced": "Feasible-looking combinations that could not be placed (check constraints)",
           "tests": "Tests", "id": "ID", "verified": "Independent verification: {ok}", "ok": "OK", "fail": "FAILED"},
    "tr": {"title": "Kombinatoryal tasarım", "summary": "{n} test, mümkün olduğu doğrulanmış {cov} adet {t}'li kombinasyonu kapsıyor "
           "(tüm kombinasyonlar: {full} test, azalma %{red}).", "infeasible": "Kısıtlar nedeniyle hariç tutulan kombinasyonlar",
           "unplaced": "Yerleştirilemeyen kombinasyonlar (kısıtları kontrol edin)",
           "tests": "Testler", "id": "ID", "verified": "Bağımsız doğrulama: {ok}", "ok": "BAŞARILI", "fail": "BAŞARISIZ"},
}


def normalize_forbidden(forbidden, names, max_rules=250000):
    out = []
    for f in forbidden:
        for k in f:
            if k not in names:
                raise ValueError(f"forbidden refers to unknown parameter '{k}'")
        keys = list(f)
        options = [f[k] if isinstance(f[k], list) else [f[k]] for k in keys]
        if len(out) + prod(map(len, options)) > max_rules:
            raise ValueError(f"forbidden constraint expansion exceeds the {max_rules}-rule resource budget")
        for combo in itertools.product(*options):
            out.append(dict(zip(keys, combo)))
    return out


def violates(assign: dict, forbidden: list[dict]) -> bool:
    return any(all(k in assign and assign[k] == v for k, v in f.items()) for f in forbidden)


def tuples_of(test: dict, names: list[str], t: int):
    for combo in itertools.combinations(names, t):
        yield tuple((n, test[n]) for n in combo)


def exact_completion(partial, names, values, forbidden, budget):
    """Return (found|infeasible|unknown, witness); budget is shared by the run."""
    if budget[0] <= 0:
        return "unknown", None
    budget[0] -= 1
    if violates(partial, forbidden):
        return "infeasible", None
    remaining = [n for n in names if n not in partial]
    if not remaining:
        return "found", dict(partial)
    # Smallest domain first, stable tie order. Exhaust all branches before
    # claiming infeasibility; exhausting the budget cannot prove anything.
    name = min(remaining, key=lambda n: len(values[n]))
    for value in values[name]:
        status, witness = exact_completion(dict(partial, **{name: value}), names, values, forbidden, budget)
        if status != "infeasible":
            return status, witness
    return "infeasible", None


def generate(spec: dict, n_candidates: int, seed: int, *, max_nodes=100000, max_tuples=250000):
    params = spec["parameters"]
    names = [p["name"] for p in params]
    values = {p["name"]: list(p["values"]) for p in params}
    if not names or len(names) > 100 or len(names) != len(set(names)):
        raise ValueError("parameters must have 1..100 unique names")
    if any(not isinstance(n, str) or not n for n in names):
        raise ValueError("parameter names must be nonempty strings")
    for name, domain in values.items():
        if not domain or any(not isinstance(v, (str, int, float, bool, type(None))) for v in domain):
            raise ValueError(f"{name}: domain must contain nonempty scalar values")
        if any(isinstance(v, float) and not isfinite(v) for v in domain):
            raise ValueError(f"{name}: domain numbers must be finite JSON values")
        if len(domain) != len(set(domain)):
            raise ValueError(f"{name}: domain values must be unique")
    if n_candidates < 1 or max_nodes < 0 or max_tuples < 1:
        raise ValueError("candidates and max-tuples must be positive; max-nodes must be nonnegative")
    t = int(spec.get("strength", 2))
    if t < 1 or t > len(names):
        raise ValueError(f"strength must be between 1 and {len(names)}")
    forbidden = normalize_forbidden(spec.get("forbidden", []), names, max_tuples)
    for rule in forbidden:
        if any(v not in values[n] for n, v in rule.items()):
            raise ValueError(f"forbidden value is outside its domain: {rule}")
    tuple_count = 0
    for combo in itertools.combinations(names, t):
        tuple_count += prod(len(values[n]) for n in combo)
        if tuple_count > max_tuples:
            raise ValueError(f"candidate tuples exceed max-tuples={max_tuples}; reduce domains/strength")

    all_tuples, infeasible = [], []
    for combo in itertools.combinations(names, t):
        for vals in itertools.product(*[values[n] for n in combo]):
            tup = tuple(zip(combo, vals))
            (infeasible if violates(dict(tup), forbidden) else all_tuples).append(tup)
    uncovered = set(all_tuples)
    order_index = {tup: i for i, tup in enumerate(all_tuples)}
    pos = {n: i for i, n in enumerate(names)}

    tests = []
    for s in spec.get("seed_tests", []):
        if set(s) != set(names):
            raise ValueError(f"seed test must set every parameter: {s}")
        if any(s[n] not in values[n] for n in names):
            raise ValueError(f"seed test contains a value outside its domain: {s}")
        if violates(s, forbidden):
            raise ValueError(f"seed test violates a constraint: {s}")
        tests.append(dict(s))
        uncovered -= set(tuples_of(s, names, t))

    rng = random.Random(seed)
    proven_infeasible = set()
    budget = [max_nodes]
    while uncovered:
        target = min(uncovered, key=order_index.get)
        best, best_gain = None, -1
        for c in range(n_candidates):
            assign = dict(target)
            rest = [n for n in names if n not in assign]
            if c:
                rng.shuffle(rest)
            ok = True
            for n in rest:
                choice, choice_gain = None, -1
                vals = values[n][:]
                if c:
                    rng.shuffle(vals)
                for v in vals:
                    trial = dict(assign, **{n: v})
                    if violates(trial, forbidden):
                        continue
                    # tuples newly completed by setting n=v: n plus any (t-1) already assigned params
                    gain = 0
                    for others in itertools.combinations([k for k in assign], t - 1):
                        key = tuple(sorted(((k, trial[k]) for k in others + (n,)), key=lambda kv: pos[kv[0]]))
                        if key in uncovered:
                            gain += 1
                    if gain > choice_gain:
                        choice, choice_gain = v, gain
                if choice is None:
                    ok = False
                    break
                assign[n] = choice
            if not ok:
                continue
            gain = sum(1 for tup in tuples_of(assign, names, t) if tup in uncovered)
            if gain > best_gain:
                best, best_gain = assign, gain
        if best is None:
            status, best = exact_completion(dict(target), names, values, forbidden, budget)
            if status != "found":
                if status == "infeasible":
                    proven_infeasible.add(target)
                uncovered.discard(target)
                continue
        best = {n: best[n] for n in names}
        tests.append(best)
        uncovered -= set(tuples_of(best, names, t))

    # Rebuild coverage from final full rows. Unknown searches stay missing,
    # even though the greedy work queue has removed them to make progress.
    covered = set()
    for tc in tests:
        for combo in itertools.combinations(names, t):
            covered.add(tuple((n, tc[n]) for n in combo))
    missing = [tup for tup in all_tuples if tup not in covered and tup not in proven_infeasible]
    valid_rows = all(set(tc) == set(names) and all(tc[n] in values[n] for n in names)
                     and not violates(tc, forbidden) for tc in tests)
    infeasible.extend(tup for tup in all_tuples if tup in proven_infeasible)
    return {
        "id": spec.get("id"), "title": spec.get("title"), "requirement_ids": spec.get("requirement_ids", []),
        "strength": t, "parameters": names,
        "tests": [{"id": f"C-{i:02d}", "values": tc} for i, tc in enumerate(tests, 1)],
        "summary": {"tests": len(tests), "feasible_tuples": len(all_tuples) - len(proven_infeasible) - len(missing),
                    "exhaustive": prod(len(values[n]) for n in names),
                    "infeasible_tuples": len(infeasible), "unplaced_tuples": len(missing),
                    "unknown_tuples": len(missing), "exact_nodes": max_nodes - budget[0]},
        "infeasible": [dict(x) for x in infeasible],
        "unplaced": [dict(x) for x in missing],
        "unknown": [dict(x) for x in missing],
        "verification": {"all_tuples_covered": not missing and valid_rows, "all_rows_valid": valid_rows,
                         "missing": [dict(x) for x in missing]},
    }


def to_md(res: dict, lang: str) -> str:
    t = T[lang]
    s = res["summary"]
    red = round(100 * (1 - s["tests"] / s["exhaustive"]), 1) if s["exhaustive"] else 0
    ok = res["verification"]["all_tuples_covered"] and res["verification"]["all_rows_valid"]
    o = [f"# {t['title']}: {res.get('id') or ''} {res.get('title') or ''}".rstrip(), ""]
    if res["requirement_ids"]:
        o.append("REQ: " + ", ".join(res["requirement_ids"]))
    o += [t["summary"].format(n=s["tests"], cov=s["feasible_tuples"], t=res["strength"], full=s["exhaustive"], red=red),
          t["verified"].format(ok=t["ok"] if ok else t["fail"]), ""]
    if not ok:
        o += ["INCOMPLETE / EKSİK: unresolved tuples are not proven infeasible; no full coverage guarantee.", ""]
    if res["unplaced"]:
        o += [f"## ⚠ {t['unplaced']}", ""] + ["- " + ", ".join(f"{k}={v}" for k, v in u.items()) for u in res["unplaced"]] + [""]
    if res["infeasible"]:
        o += [f"## {t['infeasible']} ({len(res['infeasible'])})", ""]
        o += ["- " + ", ".join(f"{k}={v}" for k, v in u.items()) for u in res["infeasible"][:30]]
        if len(res["infeasible"]) > 30:
            o.append(f"- … +{len(res['infeasible']) - 30}")
        o.append("")
    names = res["parameters"]
    o += [f"## {t['tests']}", "", "| " + " | ".join([t["id"]] + names) + " |", "|" + "---|" * (len(names) + 1)]
    for tc in res["tests"]:
        o.append("| " + " | ".join([tc["id"]] + [str(tc["values"][n]) for n in names]) + " |")
    return "\n".join(o) + "\n"


def to_csv(res: dict) -> str:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["id"] + res["parameters"])
    for tc in res["tests"]:
        w.writerow([tc["id"]] + [tc["values"][n] for n in res["parameters"]])
    return buf.getvalue()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec")
    ap.add_argument("--candidates", type=int, default=30, help="candidate tests evaluated per step")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--max-nodes", type=int, default=100000, help="shared exact-search node budget; exhausted searches remain unknown")
    ap.add_argument("--max-tuples", type=int, default=250000, help="maximum candidate tuple count before allocation")
    ap.add_argument("--lang", choices=["en", "tr"])
    ap.add_argument("--format", choices=["md", "json", "csv"], default="md")
    ap.add_argument("--out")
    sys.stdout.reconfigure(encoding="utf-8")
    a = ap.parse_args()
    try:
        spec = json.loads(Path(a.spec).read_text(encoding="utf-8-sig"))
        lang = a.lang or spec.get("language", "en")
        lang = lang if lang in T else "en"
        res = generate(spec, a.candidates, a.seed, max_nodes=a.max_nodes, max_tuples=a.max_tuples)
    except (OSError, ValueError, KeyError, TypeError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    text = {"json": lambda: json.dumps(res, ensure_ascii=False, indent=2), "csv": lambda: to_csv(res),
            "md": lambda: to_md(res, lang)}[a.format]()
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(text, encoding="utf-8", newline="\n")
        print(f"wrote {a.out}")
    else:
        sys.stdout.reconfigure(encoding="utf-8")
        print(text)
    return 0 if res["verification"]["all_tuples_covered"] else 1


if __name__ == "__main__":
    sys.exit(main())
