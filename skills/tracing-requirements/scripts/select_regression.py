#!/usr/bin/env python3
"""Select a risk-based regression set from the QA artifacts (impact analysis + risk + last results).

Tiers (every selected test carries its reasons):
  must    CHANGED   linked to a changed requirement (--changed)
          RELATED   linked to a parent / child of a changed requirement
          RETEST    failed or blocked in the last run (confirmation testing)
          SMOKE     tagged smoke with priority critical/high
  should  AREA      shares a tag with the changed tests or --areas (same functional area)
          HIGH_RISK linked requirement risk score >= --risk-threshold (L x I, default 12)
          FLAKY     marked flaky in the last run
  could   RISK      everything else that is active, ordered by risk score, then priority

Deprecated tests are never selected. With --budget N (tests) or --budget-minutes M (uses duration_ms from
results.json, default --default-minutes per test) the set is filled tier by tier in risk order, and what is
left out is reported as residual risk, so the cut is a visible decision and not a silent one.

Usage:
  python select_regression.py --requirements qa/requirements.json --tests qa/test-cases.json \
      [--results qa/results.json] --changed REQ-003,REQ-007 [--areas coupon] [--budget 40] \
      [--level must|should|could] [--lang tr|en] --out qa/regression.md [--json qa/regression.json]

The report ends with a Playwright command (--grep on the @TC tags) for the selected automated tests
(tests whose last result came from Playwright) and a list of manual tests.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PRIO = {"critical": 4, "high": 3, "medium": 2, "low": 1}
PRIO_RISK = {"critical": 20, "high": 12, "medium": 6, "low": 2}
TIERS = ["must", "should", "could"]
TIER_OF = {"CHANGED": "must", "RELATED": "must", "RETEST": "must", "SMOKE": "must",
           "AREA": "should", "HIGH_RISK": "should", "FLAKY": "should", "RISK": "could"}
GENERIC_TAGS = {"regression", "smoke", "api", "ui", "e2e", "manual", "automated", "mobile", "security",
                "performance", "accessibility", "exploratory", "negative", "positive"}

TEXT = {
    "en": {"title": "Regression selection", "changed": "Changed requirements", "areas": "Areas",
           "summary": "Summary", "tier": "Tier", "count": "Tests", "selected": "Selected tests",
           "reasons": "Reasons", "risk": "Risk", "prio": "Priority", "left": "Left out by the budget (residual risk)",
           "none": "none", "run": "How to run", "auto": "Automated (last result from Playwright)",
           "manual": "Manual or not yet automated", "active": "active tests", "budget": "Budget",
           "minutes": "estimated minutes", "below": "not selected (below --level)", "unknown_req": "Unknown requirement IDs in --changed",
           "legend": "CHANGED linked to a changed requirement · RELATED parent/child of a changed requirement · "
                     "RETEST failed/blocked last run · SMOKE critical/high smoke · AREA same functional area · "
                     "HIGH_RISK risk score ≥ threshold · FLAKY flaky last run · RISK remaining, by risk"},
    "tr": {"title": "Regresyon seçimi", "changed": "Değişen gereksinimler", "areas": "Alanlar",
           "summary": "Özet", "tier": "Katman", "count": "Test", "selected": "Seçilen testler",
           "reasons": "Gerekçeler", "risk": "Risk", "prio": "Öncelik", "left": "Bütçe nedeniyle dışarıda kalanlar (kalan risk)",
           "none": "yok", "run": "Nasıl koşulur", "auto": "Otomatik (son sonuç Playwright'tan)",
           "manual": "Manuel veya henüz otomatize edilmemiş", "active": "aktif test", "budget": "Bütçe",
           "minutes": "tahmini dakika", "below": "seçilmedi (--level altında)", "unknown_req": "--changed içindeki bilinmeyen gereksinim ID'leri",
           "legend": "CHANGED değişen gereksinime bağlı · RELATED değişen gereksinimin üst/alt gereksinimi · "
                     "RETEST son koşuda failed/blocked · SMOKE kritik/yüksek smoke · AREA aynı fonksiyonel alan · "
                     "HIGH_RISK risk skoru ≥ eşik · FLAKY son koşuda kararsız · RISK kalanlar, riske göre"},
}


def load_json(path: str | None, key: str):
    if not path:
        return {} if key == "results" else []
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return data.get(key, {} if key == "results" else [])


def req_risk(r: dict) -> int:
    risk = r.get("risk") or {}
    if isinstance(risk.get("likelihood"), int) and isinstance(risk.get("impact"), int):
        return risk["likelihood"] * risk["impact"]
    return PRIO_RISK.get(r.get("priority"), 6)


def select(reqs: list, tests: list, results: dict, changed: list[str], areas: list[str], risk_threshold: int):
    by_id = {r["id"]: r for r in reqs}
    related = set()
    for c in changed:
        parent = (by_id.get(c) or {}).get("parent")
        if parent:
            related.add(parent)
        related |= {r["id"] for r in reqs if r.get("parent") == c}
    related -= set(changed)
    active = [t for t in tests if t.get("status") != "deprecated"]
    changed_tags = set(areas)
    for t in active:
        if set(t.get("requirement_ids", [])) & set(changed):
            changed_tags |= {x for x in t.get("tags", []) if x not in GENERIC_TAGS}
    rows = []
    for t in active:
        rids = t.get("requirement_ids", [])
        risk = max([req_risk(by_id[r]) for r in rids if r in by_id] or [PRIO_RISK.get(t.get("priority"), 6)])
        res = results.get(t["id"], {})
        reasons = []
        if set(rids) & set(changed):
            reasons.append("CHANGED")
        if set(rids) & related:
            reasons.append("RELATED")
        if res.get("status") in ("failed", "blocked"):
            reasons.append("RETEST")
        if "smoke" in t.get("tags", []) and t.get("priority") in ("critical", "high"):
            reasons.append("SMOKE")
        if changed_tags & set(t.get("tags", [])):
            reasons.append("AREA")
        if risk >= risk_threshold:
            reasons.append("HIGH_RISK")
        if res.get("flaky"):
            reasons.append("FLAKY")
        if not reasons:
            reasons.append("RISK")
        tier = min((TIER_OF[x] for x in reasons), key=TIERS.index)
        minutes = (res.get("duration_ms") or 0) / 60000
        rows.append({"id": t["id"], "title": t.get("title", ""), "tier": tier, "reasons": reasons, "risk": risk,
                     "priority": t.get("priority", "medium"), "requirement_ids": rids,
                     "automated": res.get("source") == "playwright", "minutes": minutes})
    rows.sort(key=lambda x: (TIERS.index(x["tier"]), -x["risk"], -PRIO.get(x["priority"], 2), x["id"]))
    return rows


def apply_budget(rows: list, level: str, budget: int | None, budget_minutes: float | None, default_minutes: float):
    pool = [r for r in rows if TIERS.index(r["tier"]) <= TIERS.index(level)]
    chosen, left, used = [], [], 0.0
    for r in pool:
        cost = r["minutes"] or default_minutes
        if (budget is not None and len(chosen) >= budget) or (budget_minutes is not None and used + cost > budget_minutes):
            left.append(r)
            continue
        chosen.append(r)
        used += cost
    return chosen, left, used


def render(chosen, left, used, a, t, unknown, total_active) -> str:
    out = [f"# {t['title']}", ""]
    out.append(f"- {t['changed']}: {', '.join(a.changed_list) or t['none']}")
    if a.areas_list:
        out.append(f"- {t['areas']}: {', '.join(a.areas_list)}")
    if unknown:
        out.append(f"- ⚠ {t['unknown_req']}: {', '.join(unknown)}")
    budget = []
    if a.budget is not None:
        budget.append(f"{a.budget} {t['count'].lower()}")
    if a.budget_minutes is not None:
        budget.append(f"{a.budget_minutes:g} min")
    if budget:
        out.append(f"- {t['budget']}: {', '.join(budget)}")
    out += ["", f"## {t['summary']}", "", f"| {t['tier']} | {t['count']} |", "|---|---|"]
    for tier in TIERS:
        out.append(f"| {tier} | {sum(1 for r in chosen if r['tier'] == tier)} |")
    out.append(f"| **Σ** | **{len(chosen)}** / {total_active} {t['active']} · ~{used:.0f} {t['minutes']} |")
    below = total_active - len(chosen) - len(left)
    if below:
        out.append(f"| {t['below']} | {below} |")
    out += ["", f"## {t['selected']}", "", f"| TC | {t['tier']} | {t['reasons']} | {t['risk']} | {t['prio']} | REQ |",
            "|---|---|---|---|---|---|"]
    for r in chosen:
        out.append(f"| {r['id']} {r['title']} | {r['tier']} | {', '.join(r['reasons'])} | {r['risk']} | "
                   f"{r['priority']} | {', '.join(r['requirement_ids'])} |")
    out += ["", f"_{t['legend']}_", "", f"## {t['left']}", ""]
    if left:
        for r in left:
            out.append(f"- {r['id']} {r['title']} ({r['tier']}; {', '.join(r['reasons'])}; {t['risk'].lower()} {r['risk']})")
    else:
        out.append(f"- {t['none']}")
    auto = [r["id"] for r in chosen if r["automated"]]
    manual = [r["id"] for r in chosen if not r["automated"]]
    out += ["", f"## {t['run']}", "", f"**{t['auto']}** ({len(auto)})", ""]
    if auto:
        out += ["```bash", f'npx playwright test --grep "{"|".join("@" + i for i in auto)}"', "```"]
    else:
        out.append(f"- {t['none']}")
    out += ["", f"**{t['manual']}** ({len(manual)}): {', '.join(manual) or t['none']}", ""]
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--requirements", required=True)
    ap.add_argument("--tests", required=True)
    ap.add_argument("--results")
    ap.add_argument("--changed", default="", help="comma-separated changed REQ IDs")
    ap.add_argument("--areas", default="", help="comma-separated tags of changed functional areas")
    ap.add_argument("--level", choices=TIERS, default="should", help="lowest tier to include (default should)")
    ap.add_argument("--budget", type=int, help="maximum number of tests")
    ap.add_argument("--budget-minutes", type=float, help="maximum estimated execution minutes")
    ap.add_argument("--default-minutes", type=float, default=5.0, help="estimate for tests without duration_ms")
    ap.add_argument("--risk-threshold", type=int, default=12)
    ap.add_argument("--lang", choices=["tr", "en"], default="en")
    ap.add_argument("--out", required=True)
    ap.add_argument("--json")
    sys.stdout.reconfigure(encoding="utf-8")
    a = ap.parse_args()
    a.changed_list = [c.strip() for c in a.changed.split(",") if c.strip()]
    a.areas_list = [c.strip() for c in a.areas.split(",") if c.strip()]
    reqs = load_json(a.requirements, "requirements")
    tests = load_json(a.tests, "test_cases")
    results = load_json(a.results, "results")
    unknown = [c for c in a.changed_list if c not in {r["id"] for r in reqs}]
    rows = select(reqs, tests, results, a.changed_list, a.areas_list, a.risk_threshold)
    chosen, left, used = apply_budget(rows, a.level, a.budget, a.budget_minutes, a.default_minutes)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(render(chosen, left, used, a, TEXT[a.lang], unknown, len(rows)), encoding="utf-8")
    if a.json:
        Path(a.json).write_text(json.dumps({"changed": a.changed_list, "selected": chosen, "left_out": left,
                                            "estimated_minutes": round(used, 1), "unknown_changed": unknown},
                                           ensure_ascii=False, indent=2), encoding="utf-8")
    tiers = ", ".join(f"{x} {sum(1 for r in chosen if r['tier'] == x)}" for x in TIERS)
    print(f"wrote {a.out}: {len(chosen)} of {len(rows)} active tests selected ({tiers}); "
          f"{len(left)} left out by budget; {len(rows) - len(chosen) - len(left)} below --level {a.level}")
    if unknown:
        print(f"warning: unknown requirement IDs in --changed: {', '.join(unknown)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
