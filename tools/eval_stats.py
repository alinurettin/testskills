#!/usr/bin/env python3
"""Uncertainty of the with-skill vs no-skill comparison in evals/results/trials-*.json.

For each model, and for all models pooled (cells = model x trial), it reports the mean score of both arms, the difference, a 95% bootstrap confidence
interval of the difference (stratified by trial: runs are resampled within each trial x arm cell,
so trials keep equal weight), and a two-sided permutation p-value (arm labels shuffled within each
trial). With 3 runs per cell the intervals are wide: read them before quoting a difference.

Usage:
  python tools/eval_stats.py evals/results/trials-0.9.0.json [--seed 1] [--boot 10000] [--md]
"""
from __future__ import annotations

import argparse
import json
import random
import statistics as st
import sys
from collections import defaultdict
from pathlib import Path


def load(path: str) -> dict:
    """model -> trial -> arm -> [score %]."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    out: dict = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    for r in data["runs"]:
        if r.get("max"):
            out[r["model"]][r["trial"]][r["arm"]].append(100.0 * r["score"] / r["max"])
    return out


def diff(cells: dict) -> float:
    """Mean over trials of (mean skill - mean noskill): every trial weighs the same."""
    return st.mean(st.mean(c["skill"]) - st.mean(c["noskill"]) for c in cells.values())


def bootstrap(cells: dict, rng: random.Random, n: int) -> tuple[float, float]:
    vals = []
    for _ in range(n):
        res = {t: {a: [rng.choice(v) for _ in v] for a, v in c.items()} for t, c in cells.items()}
        vals.append(diff(res))
    vals.sort()
    return vals[int(0.025 * n)], vals[int(0.975 * n) - 1]


def permutation_p(cells: dict, rng: random.Random, n: int) -> float:
    observed = abs(diff(cells))
    hits = 0
    for _ in range(n):
        res = {}
        for t, c in cells.items():
            pool = c["skill"] + c["noskill"]
            rng.shuffle(pool)
            k = len(c["skill"])
            res[t] = {"skill": pool[:k], "noskill": pool[k:]}
        hits += abs(diff(res)) >= observed - 1e-12
    return (hits + 1) / (n + 1)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("results")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--boot", type=int, default=10000)
    ap.add_argument("--md", action="store_true", help="print a Markdown table")
    sys.stdout.reconfigure(encoding="utf-8")
    a = ap.parse_args()
    data = load(a.results)
    rows = []
    for model in sorted(data):
        cells = {t: c for t, c in data[model].items() if c.get("skill") and c.get("noskill")}
        rng = random.Random(a.seed)
        lo, hi = bootstrap(cells, rng, a.boot)
        p = permutation_p(cells, rng, a.boot)
        skill = st.mean(st.mean(c["skill"]) for c in cells.values())
        base = st.mean(st.mean(c["noskill"]) for c in cells.values())
        rows.append((model, len(cells), sum(len(c["skill"]) + len(c["noskill"]) for c in cells.values()), skill, base,
                     skill - base, lo, hi, p))
        for t in sorted(cells):
            c = cells[t]
            one = {t: c}
            tlo, thi = bootstrap(one, random.Random(a.seed), max(2000, a.boot // 5))
            rows.append((f"  {model}/{t}", 1, len(c["skill"]) + len(c["noskill"]), st.mean(c["skill"]), st.mean(c["noskill"]),
                         diff(one), tlo, thi, None))
    pooled = {f"{m}/{t}": c for m in data for t, c in data[m].items() if c.get("skill") and c.get("noskill")}
    rng = random.Random(a.seed)
    lo, hi = bootstrap(pooled, rng, a.boot)
    rows.append(("all models", len(pooled), sum(len(c["skill"]) + len(c["noskill"]) for c in pooled.values()),
                 st.mean(st.mean(c["skill"]) for c in pooled.values()), st.mean(st.mean(c["noskill"]) for c in pooled.values()),
                 diff(pooled), lo, hi, permutation_p(pooled, rng, a.boot)))
    if a.md:
        print("| Model / trial | Runs | With skills | Without | Difference | 95% CI | p (permutation) |")
        print("|---|---:|---:|---:|---:|---|---:|")
        for name, _, n, s, b, d, lo, hi, p in rows:
            print(f"| {name.strip() if name.startswith('  ') else '**' + name + '**'} | {n} | {s:.1f} | {b:.1f} | {d:+.1f} | "
                  f"[{lo:+.1f}, {hi:+.1f}] | {'' if p is None else f'{p:.3f}'} |")
    else:
        for name, k, n, s, b, d, lo, hi, p in rows:
            tail = "" if p is None else f"  p={p:.3f}"
            print(f"{name:26s} runs={n:3d} skill={s:5.1f} noskill={b:5.1f} diff={d:+5.1f}  95% CI [{lo:+.1f}, {hi:+.1f}]{tail}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
