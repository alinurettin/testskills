#!/usr/bin/env python3
"""Select a risk-based regression set from the QA artifacts (impact analysis + risk + last results).

Tiers (every selected test carries its reasons):
  must    CHANGED   linked to a changed requirement (--changed)
          RELATED   linked to a parent / child of a changed requirement
          RETEST    failed or blocked in the last run (confirmation testing)
          SMOKE     tagged smoke with priority critical/high
  should  AREA      shares a tag with the changed tests or --areas (same functional area)
          HIGH_RISK linked requirement risk score >= --risk-threshold (L x I, default 12) or impact 5
          FLAKY     marked flaky in the last run
  could   RISK      everything else that is active, ordered by risk score, then priority

Deprecated tests are never selected. With --budget N (tests) or --budget-minutes M (uses duration_ms from
results.json, default --default-minutes per test) the set is filled tier by tier. Inside a tier the fill is
breadth-first (--order breadth, the default): first one test for every requirement, highest risk first, then
the second test of each requirement, and so on, so a tight budget is not spent on one requirement.
--order depth keeps the plain risk order. A test that does not fit is left out and cheaper tests after it may
still be taken; everything left out is listed with the reason, and the requirements that end up with no
selected test are listed as residual risk, so the cut is a visible decision and not a silent one.

Usage:
  python select_regression.py --requirements qa/requirements.json --tests qa/test-cases.json \
      [--results qa/results.json] --changed REQ-003,REQ-007 [--areas coupon] [--budget 40 | --budget-minutes 120] \
      [--order breadth|depth] [--level must|should|could] [--lang tr|en] --out qa/regression.md [--json qa/regression.json]

The report ends with a Playwright command (--grep on the @TC tags) for the selected tests whose last result
came from Playwright, the tests automated with another runner, and the manual tests.
Exit code: 0 ok, 1 the must tier does not fit the budget (the report is still written), 2 unreadable input.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

PRIO = {"critical": 4, "high": 3, "medium": 2, "low": 1}
PRIO_RISK = {"critical": 20, "high": 12, "medium": 6, "low": 2}
TIERS = ["must", "should", "could"]
LEVELS = ["-", "low", "medium", "high", "critical"]
TIER_OF = {"CHANGED": "must", "RELATED": "must", "RETEST": "must", "SMOKE": "must",
           "AREA": "should", "HIGH_RISK": "should", "FLAKY": "should", "RISK": "could"}
GENERIC_TAGS = {"regression", "smoke", "api", "ui", "e2e", "manual", "automated", "mobile", "security",
                "performance", "accessibility", "exploratory", "negative", "positive"}
MANUAL_SOURCES = {"", "manual", "exploratory"}

TEXT = {
    "en": {"title": "Regression selection", "changed": "Changed requirements", "areas": "Areas",
           "summary": "Summary", "tier": "Tier", "count": "Tests", "selected": "Selected tests",
           "reasons": "Reasons", "risk": "Risk", "prio": "Priority", "left": "Left out by the budget (residual risk)",
           "none": "none", "run": "How to run", "auto": "Automated (last result from Playwright)",
           "auto_other": "Automated with another runner (run them there)",
           "manual": "Manual or not yet automated", "active": "active tests", "budget": "Budget",
           "minutes": "estimated minutes", "below": "not selected (below --level)", "unknown_req": "Unknown requirement IDs in --changed",
           "order": {"breadth": "filled breadth-first: one test per requirement before any second test",
                     "depth": "filled depth-first: plain risk order"},
           "must_over": "MUST tier exceeds budget: {n} of {t} must tests left out ({ids}). The must tier needs "
                        "{need} tests, about {mins:.0f} minutes. Raise the budget or get the cut accepted; this set is "
                        "not a safe regression run.",
           "why_left": {"count": "test budget used up", "minutes": "needs {c:.0f} min, {r:.0f} min left"},
           "uncovered": "Requirements with no selected test (residual risk)",
           "u_why": {"budget": "all tests left out by the budget", "level": "tests below --level",
                     "none": "changed, but no active test"},
           "legend": "CHANGED linked to a changed requirement · RELATED parent/child of a changed requirement · "
                     "RETEST failed/blocked last run · SMOKE critical/high smoke · AREA same functional area · "
                     "HIGH_RISK risk score ≥ threshold or impact 5 · FLAKY flaky last run · RISK remaining, by risk"},
    "tr": {"title": "Regresyon seçimi", "changed": "Değişen gereksinimler", "areas": "Alanlar",
           "summary": "Özet", "tier": "Katman", "count": "Test", "selected": "Seçilen testler",
           "reasons": "Gerekçeler", "risk": "Risk", "prio": "Öncelik", "left": "Bütçe nedeniyle dışarıda kalanlar (kalan risk)",
           "none": "yok", "run": "Nasıl koşulur", "auto": "Otomatik (son sonuç Playwright'tan)",
           "auto_other": "Başka bir koşucuyla otomatik (orada koşun)",
           "manual": "Manuel veya henüz otomatize edilmemiş", "active": "aktif test", "budget": "Bütçe",
           "minutes": "tahmini dakika", "below": "seçilmedi (--level altında)", "unknown_req": "--changed içindeki bilinmeyen gereksinim ID'leri",
           "order": {"breadth": "genişlik öncelikli dolduruldu: ikinci testlerden önce her gereksinime bir test",
                     "depth": "derinlik öncelikli dolduruldu: düz risk sırası"},
           "must_over": "MUST katmanı bütçeyi aşıyor: {t} must testinden {n} tanesi dışarıda kaldı ({ids}). Must katmanı "
                        "{need} test, yaklaşık {mins:.0f} dakika gerektirir. Bütçeyi artırın veya kesintiyi onaylatın; bu set "
                        "güvenli bir regresyon koşusu değildir.",
           "why_left": {"count": "test bütçesi doldu", "minutes": "{c:.0f} dk gerekli, {r:.0f} dk kaldı"},
           "uncovered": "Seçilen testi olmayan gereksinimler (kalan risk)",
           "u_why": {"budget": "tüm testleri bütçe dışında kaldı", "level": "testleri --level altında",
                     "none": "değişti, ancak aktif testi yok"},
           "legend": "CHANGED değişen gereksinime bağlı · RELATED değişen gereksinimin üst/alt gereksinimi · "
                     "RETEST son koşuda failed/blocked · SMOKE kritik/yüksek smoke · AREA aynı fonksiyonel alan · "
                     "HIGH_RISK risk skoru ≥ eşik veya etki 5 · FLAKY son koşuda kararsız · RISK kalanlar, riske göre"},
}


def load_json(path: str | None, key: str):
    if not path:
        return {} if key == "results" else []
    data = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        return data if key != "results" else {}
    return data.get(key, {} if key == "results" else [])


def norm(v) -> str:
    return re.sub(r"[\s_]+", "-", str(v if v is not None else "").strip().lower())


def risk_of(r: dict) -> tuple[int, str]:
    """(score, level) of a requirement. Keep identical in plan_facts, completion_report, build_rtm, select_regression.

    The score (likelihood x impact) only orders requirements. The level comes from the score bands plus two
    matrix overrides, because ordinal scales do not multiply (CTAL-TM v3.0 section 1.3.3): impact 5 is at least
    high, and impact 5 with likelihood >= 3 is critical. Without both values the level falls back to the priority."""
    rk = r.get("risk") if isinstance(r.get("risk"), dict) else {}
    try:
        li, im = int(rk.get("likelihood") or 0), int(rk.get("impact") or 0)
    except (TypeError, ValueError):
        li = im = 0
    score = li * im
    if not score:
        im = 0
        score = {"critical": 20, "high": 12, "medium": 6, "low": 2}.get(r.get("priority"), 0)
    level = "critical" if score >= 17 else "high" if score >= 10 else "medium" if score >= 5 else "low" if score else "-"
    if im >= 5 and level != "critical":
        level = "critical" if li >= 3 else "high"
    return score, level


def req_risk(r: dict) -> int:
    return risk_of(r)[0]


def impact_5(r: dict) -> bool:
    rk = r.get("risk") if isinstance(r.get("risk"), dict) else {}
    try:
        return int(rk.get("likelihood") or 0) > 0 and int(rk.get("impact") or 0) >= 5
    except (TypeError, ValueError):
        return False


def is_automated(res: dict) -> bool:
    """A test counts as automated when a tool wrote its last result and the tool really ran it.
    Same rule in completion_report.py. A skeleton (source set, status not-run) is not automated."""
    return norm(res.get("source")) not in MANUAL_SOURCES and norm(res.get("status")) in ("passed", "failed", "blocked")


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
        if set(t.get("requirement_ids") or []) & set(changed):
            changed_tags |= {x for x in t.get("tags") or [] if x not in GENERIC_TAGS}
    rows = []
    for t in active:
        rids = t.get("requirement_ids") or []
        rated = [risk_of(by_id[r]) for r in rids if r in by_id]
        rated = [x for x in rated if x[0]]
        if rated:
            risk = max(s for s, _ in rated)
            level = max((lv for _, lv in rated), key=LEVELS.index)
        else:                      # no rated requirement: fall back to the test priority, then to medium
            risk = PRIO_RISK.get(t.get("priority"), 6)
            level = t.get("priority") if t.get("priority") in PRIO else "medium"
        res = results.get(t["id"]) if isinstance(results.get(t["id"]), dict) else {}
        reasons = []
        if set(rids) & set(changed):
            reasons.append("CHANGED")
        if set(rids) & related:
            reasons.append("RELATED")
        if norm(res.get("status")) in ("failed", "blocked"):
            reasons.append("RETEST")
        if "smoke" in (t.get("tags") or []) and t.get("priority") in ("critical", "high"):
            reasons.append("SMOKE")
        if changed_tags & set(t.get("tags") or []):
            reasons.append("AREA")
        if risk >= risk_threshold or any(impact_5(by_id[r]) for r in rids if r in by_id):
            reasons.append("HIGH_RISK")   # impact 5 is at least high whatever the product says (see risk_of)
        if res.get("flaky"):
            reasons.append("FLAKY")
        if not reasons:
            reasons.append("RISK")
        tier = min((TIER_OF[x] for x in reasons), key=TIERS.index)
        minutes = (res.get("duration_ms") or 0) / 60000
        source = norm(res.get("source"))
        rows.append({"id": t["id"], "title": t.get("title", ""), "tier": tier, "reasons": reasons, "risk": risk,
                     "level": level, "priority": t.get("priority", "medium"), "requirement_ids": rids,
                     "automated": is_automated(res), "source": source if is_automated(res) else "", "minutes": minutes})
    rows.sort(key=sort_key)
    return rows


def sort_key(x: dict):
    return (TIERS.index(x["tier"]), -x["risk"], -PRIO.get(x["priority"], 2), x["id"])


def breadth_first(tier_rows: list, known: set) -> list:
    """Round 1: the best test of every requirement, in risk order. Round 2: the next test of each, and so on."""
    remaining, ordered = list(tier_rows), []
    while remaining:
        seen, later = set(), []
        for r in remaining:
            keys = [q for q in r["requirement_ids"] if q in known] or ["test:" + r["id"]]
            if any(k not in seen for k in keys):
                ordered.append(r)
                seen.update(keys)
            else:
                later.append(r)
        remaining = later
    return ordered


def apply_budget(rows: list, level: str, budget: int | None, budget_minutes: float | None, default_minutes: float,
                 order: str = "breadth", known: set | None = None):
    pool = [r for r in rows if TIERS.index(r["tier"]) <= TIERS.index(level)]
    limited = budget is not None or budget_minutes is not None
    known = known if known is not None else {q for r in rows for q in r["requirement_ids"]}
    chosen, left, used = [], [], 0.0
    for tier in TIERS:
        tier_rows = [r for r in pool if r["tier"] == tier]
        for r in (breadth_first(tier_rows, known) if limited and order == "breadth" else tier_rows):
            cost = r["minutes"] or default_minutes
            if budget is not None and len(chosen) >= budget:
                left.append({**r, "left_reason": "count", "cost_minutes": round(cost, 1)})
            elif budget_minutes is not None and used + cost > budget_minutes:
                left.append({**r, "left_reason": "minutes", "cost_minutes": round(cost, 1),
                             "minutes_left": round(budget_minutes - used, 1)})
            else:
                chosen.append({**r, "pick": len(chosen) + 1})
                used += cost
    chosen.sort(key=sort_key)
    left.sort(key=sort_key)
    return chosen, left, used


def uncovered_requirements(reqs: list, rows: list, chosen: list, left: list, changed: list[str]) -> list[dict]:
    """In-scope requirements that have active tests but none in the selection, plus changed ones with no test."""
    picked = {q for r in chosen for q in r["requirement_ids"]}
    cut = {q for r in left for q in r["requirement_ids"]}
    has_test = {q for r in rows for q in r["requirement_ids"]}
    out = []
    for r in reqs:
        if r.get("status") in ("deferred", "deprecated") or r["id"] in picked:
            continue
        if r["id"] in has_test:
            why = "budget" if r["id"] in cut else "level"
        elif r["id"] in changed:
            why = "none"
        else:
            continue
        score, level = risk_of(r)
        out.append({"id": r["id"], "title": r.get("title", ""), "score": score, "level": level, "why": why})
    out.sort(key=lambda x: (-x["score"], x["id"]))
    return out


def render(chosen, left, used, a, t, unknown, total_active, must_all, uncovered, default_minutes) -> str:
    out = [f"# {t['title']}", ""]
    must_left = [r for r in left if r["tier"] == "must"]
    if must_left:
        out += ["> ⚠ " + t["must_over"].format(
            n=len(must_left), t=len(must_all), ids=", ".join(r["id"] for r in must_left), need=len(must_all),
            mins=sum(r["minutes"] or default_minutes for r in must_all)), ""]
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
        out.append(f"- {t['budget']}: {', '.join(budget)} ({t['order'][a.order]})")
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
            why = t["why_left"][r["left_reason"]].format(c=r["cost_minutes"], r=r.get("minutes_left", 0))
            out.append(f"- {r['id']} {r['title']} ({r['tier']}; {', '.join(r['reasons'])}; {t['risk'].lower()} {r['risk']}; {why})")
    else:
        out.append(f"- {t['none']}")
    out += ["", f"## {t['uncovered']}", ""]
    if uncovered:
        out += [f"- {u['id']} {u['title']} ({u['level']} {u['score']}; {t['u_why'][u['why']]})" for u in uncovered]
    else:
        out.append(f"- {t['none']}")
    auto = [r["id"] for r in chosen if r["source"] == "playwright"]
    other = [r for r in chosen if r["automated"] and r["source"] != "playwright"]
    manual = [r["id"] for r in chosen if not r["automated"]]
    out += ["", f"## {t['run']}", "", f"**{t['auto']}** ({len(auto)})", ""]
    if auto:
        out += ["```bash", f'npx playwright test --grep "{"|".join("@" + i for i in auto)}"', "```"]
    else:
        out.append(f"- {t['none']}")
    if other:
        out += ["", f"**{t['auto_other']}** ({len(other)})", ""]
        for src in sorted({r["source"] for r in other}):
            out.append(f"- {src}: {', '.join(r['id'] for r in other if r['source'] == src)}")
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
    ap.add_argument("--order", choices=["breadth", "depth"], default="breadth",
                    help="fill order inside a tier under a budget: breadth = one test per requirement first (default); "
                         "depth = plain risk order")
    ap.add_argument("--risk-threshold", type=int, default=12)
    ap.add_argument("--lang", choices=["tr", "en"], default="en")
    ap.add_argument("--out", required=True)
    ap.add_argument("--json")
    sys.stdout.reconfigure(encoding="utf-8")
    a = ap.parse_args()
    a.changed_list = [c.strip() for c in a.changed.split(",") if c.strip()]
    a.areas_list = [c.strip() for c in a.areas.split(",") if c.strip()]
    try:
        reqs = load_json(a.requirements, "requirements")
        tests = load_json(a.tests, "test_cases")
        results = load_json(a.results, "results")
    except (OSError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    if not isinstance(reqs, list) or not isinstance(tests, list) or not isinstance(results, dict):
        print("error: expected 'requirements' and 'test_cases' lists and a 'results' object", file=sys.stderr)
        return 2
    if (a.budget is not None and a.budget < 0) or (a.budget_minutes is not None and a.budget_minutes < 0):
        print("error: a budget cannot be negative", file=sys.stderr)
        return 2
    reqs = [r for r in reqs if isinstance(r, dict) and r.get("id")]
    tests = [t for t in tests if isinstance(t, dict) and t.get("id")]
    known = {r["id"] for r in reqs}
    unknown = [c for c in a.changed_list if c not in known]
    rows = select(reqs, tests, results, a.changed_list, a.areas_list, a.risk_threshold)
    chosen, left, used = apply_budget(rows, a.level, a.budget, a.budget_minutes, a.default_minutes, a.order, known)
    must_all = [r for r in rows if r["tier"] == "must"]
    must_left = [r for r in left if r["tier"] == "must"]
    uncovered = uncovered_requirements(reqs, rows, chosen, left, a.changed_list)
    t = TEXT[a.lang]
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(render(chosen, left, used, a, t, unknown, len(rows), must_all, uncovered, a.default_minutes),
                           encoding="utf-8", newline="\n")
    if a.json:
        Path(a.json).parent.mkdir(parents=True, exist_ok=True)
        Path(a.json).write_text(json.dumps(
            {"changed": a.changed_list, "order": a.order, "selected": chosen, "left_out": left,
             "must_left_out": [r["id"] for r in must_left], "must_tier_fits": not must_left,
             "requirements_without_selected_test": uncovered,
             "estimated_minutes": round(used, 1), "unknown_changed": unknown},
            ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    tiers = ", ".join(f"{x} {sum(1 for r in chosen if r['tier'] == x)}" for x in TIERS)
    print(f"wrote {a.out}: {len(chosen)} of {len(rows)} active tests selected ({tiers}); "
          f"{len(left)} left out by budget; {len(rows) - len(chosen) - len(left)} below --level {a.level}; "
          f"{len(uncovered)} requirements with no selected test")
    if unknown:
        print(f"warning: unknown requirement IDs in --changed: {', '.join(unknown)}", file=sys.stderr)
    if must_left:
        print("error: " + TEXT["en"]["must_over"].format(
            n=len(must_left), t=len(must_all), ids=", ".join(r["id"] for r in must_left), need=len(must_all),
            mins=sum(r["minutes"] or a.default_minutes for r in must_all)), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
