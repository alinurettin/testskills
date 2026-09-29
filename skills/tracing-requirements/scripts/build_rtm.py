#!/usr/bin/env python3
"""Requirements Traceability Matrix (RTM) + coverage gap report + validation.

Reads the QA Suite requirements.json and test-cases.json (optionally
results.json) and produces:
  - schema validation errors/warnings (IDs, required fields, enums, links)
  - bidirectional RTM: requirement -> tests (-> results -> defects) and test -> requirements
  - coverage metrics and gap report ordered by risk:
      UNCOVERED, NO_NEGATIVE, THIN (high/critical risk with a single test),
      ORPHAN tests, BROKEN_LINK, DUPLICATE tests, UNCONFIRMED derived requirements
  - optional change-impact list (--changed REQ-003,REQ-007)

Usage:
  python build_rtm.py --requirements qa/requirements.json --tests qa/test-cases.json \
      [--results qa/results.json] [--out-dir qa] [--lang tr] [--changed REQ-003] [--strict]

Outputs <out-dir>/rtm.md and <out-dir>/rtm.csv (UTF-8 with BOM so Excel shows
Turkish characters). Exit code: 0 ok, 1 validation errors (or gaps with --strict), 2 unreadable input.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

REQ_TYPES = {"functional", "non-functional", "business-rule", "interface", "data", "constraint", "compliance"}
REQ_STATUS = {"draft", "clarification-needed", "ready", "deferred", "deprecated"}
PRIORITIES = {"critical", "high", "medium", "low"}
POLARITY = {"positive", "negative"}
TECHNIQUES = {"equivalence-partitioning", "boundary-value-analysis", "decision-table", "state-transition", "pairwise",
              "classification-tree", "use-case", "scenario", "crud", "error-guessing", "checklist", "exploratory",
              "requirements-based"}
TC_STATUS = {"draft", "ready", "deprecated"}
RESULT_STATUS = {"passed", "failed", "blocked", "not-run", "skipped"}
REQ_ID = re.compile(r"^REQ-\d{3,}$")
TC_ID = re.compile(r"^TC-\d{3,}$")
NEG_EXEMPT_TYPES = {"non-functional", "constraint", "compliance"}

L = {
    "en": {
        "title": "Requirements Traceability Matrix", "summary": "Summary", "validation": "Validation",
        "errors": "Errors", "warnings": "Warnings", "gaps": "Coverage gaps (highest risk first)",
        "rtm": "Requirement → Test", "reverse": "Test → Requirement", "impact": "Change impact",
        "req": "Requirement", "src": "Source", "title_c": "Title", "risk": "Risk", "prio": "Priority", "status": "Status",
        "tests": "Tests", "pos": "Pos", "neg": "Neg", "tech": "Techniques", "exec": "Execution", "defects": "Defects",
        "cov": "Coverage", "none": "none", "ok": "No problems found.",
        "m_reqs": "Requirements in scope", "m_cov": "Covered by ≥1 active test", "m_neg": "Functional reqs with a negative test",
        "m_tests": "Active tests", "m_orph": "Orphan tests", "m_exec": "Execution", "m_def": "Linked defects",
        "m_tech": "Tests by technique", "m_prio": "Tests by priority", "excluded": "excluded: deferred/deprecated",
        "g": {"UNCOVERED": "no active test", "NO_NEGATIVE": "no negative test for a functional rule",
              "THIN": "high/critical risk covered by a single test", "UNCONFIRMED": "derived requirement not yet confirmed",
              "OPEN_QUESTIONS": "tested on assumptions (open questions)", "FAILED": "linked test failed",
              "NOT_RUN": "tests not executed"},
        "affected": "Tests to review/re-run for changed requirements",
        "orphan": "test without requirement", "dup": "identical preconditions/steps/data",
        "dups": "duplicate groups", "depr": "deprecated", "derived": "derived",
        "calib": "Calibration (review)",
        "skew": "Priority inflation: {c}% critical, {ch}% critical+high (target ≈ 5–15% critical, ≤ 50% critical+high). Re-rate: only go/no-go tests are critical; variants and boundary neighbours are one level lower.",
        "redundant": "{n} tests ({ids}) share requirement, polarity, technique ({tech}) and outcome pattern: likely the same equivalence class. Keep one representative plus the boundary values.",
    },
    "tr": {
        "title": "Gereksinim İzlenebilirlik Matrisi", "summary": "Özet", "validation": "Doğrulama",
        "errors": "Hatalar", "warnings": "Uyarılar", "gaps": "Kapsam boşlukları (en yüksek risk önce)",
        "rtm": "Gereksinim → Test", "reverse": "Test → Gereksinim", "impact": "Değişiklik etkisi",
        "req": "Gereksinim", "src": "Kaynak", "title_c": "Başlık", "risk": "Risk", "prio": "Öncelik", "status": "Durum",
        "tests": "Testler", "pos": "Poz", "neg": "Neg", "tech": "Teknikler", "exec": "Koşum", "defects": "Hatalar",
        "cov": "Kapsam", "none": "yok", "ok": "Sorun bulunmadı.",
        "m_reqs": "Kapsamdaki gereksinimler", "m_cov": "En az 1 aktif testle kapsanan", "m_neg": "Negatif testi olan fonksiyonel gereksinim",
        "m_tests": "Aktif testler", "m_orph": "Sahipsiz testler", "m_exec": "Koşum", "m_def": "Bağlı hatalar",
        "m_tech": "Tekniğe göre testler", "m_prio": "Önceliğe göre testler", "excluded": "hariç: ertelenen/kullanımdan kalkan",
        "g": {"UNCOVERED": "aktif test yok", "NO_NEGATIVE": "fonksiyonel kural için negatif test yok",
              "THIN": "yüksek/kritik risk tek bir testle kapsanıyor", "UNCONFIRMED": "türetilmiş gereksinim henüz onaylanmadı",
              "OPEN_QUESTIONS": "varsayımlarla test ediliyor (açık sorular)", "FAILED": "bağlı test başarısız",
              "NOT_RUN": "testler koşulmadı"},
        "affected": "Değişen gereksinimler için gözden geçirilecek/yeniden koşulacak testler",
        "orphan": "gereksinime bağlı olmayan test", "dup": "ön koşul/adım/veri birebir aynı",
        "dups": "kopya grupları", "depr": "kullanımdan kalkmış", "derived": "türetilmiş",
        "calib": "Kalibrasyon (gözden geçirin)",
        "skew": "Öncelik şişmesi: %{c} kritik, %{ch} kritik+yüksek (hedef ≈ %5–15 kritik, ≤ %50 kritik+yüksek). Yeniden derecelendirin: yalnızca yayın durdurucu (go/no-go) testler kritiktir; varyantlar ve sınır komşuları bir seviye aşağıdadır.",
        "redundant": "{n} test ({ids}) aynı gereksinim, polarite, teknik ({tech}) ve sonuç kalıbını paylaşıyor: büyük olasılıkla aynı denklik sınıfı. Bir temsilci ve sınır değerlerini bırakın.",
    },
}


def risk_of(r: dict) -> tuple[int, str]:
    rk = r.get("risk") or {}
    try:
        score = int(rk.get("likelihood", 0)) * int(rk.get("impact", 0))
    except (TypeError, ValueError):
        score = 0
    if score == 0:
        score = {"critical": 20, "high": 12, "medium": 6, "low": 2}.get(r.get("priority"), 0)
    level = "critical" if score >= 17 else "high" if score >= 10 else "medium" if score >= 5 else "low" if score else "-"
    return score, level


def norm_steps(tc: dict) -> str:
    parts = [re.sub(r"\s+", " ", str(tc.get("preconditions", ""))).lower()]
    for s in tc.get("steps", []):
        parts.append(re.sub(r"\s+", " ", f"{s.get('action', '')}|{s.get('data', '')}|{s.get('expected', '')}").lower())
    parts.append(json.dumps(tc.get("test_data", ""), sort_keys=True, ensure_ascii=False).lower())
    return "\n".join(parts)


def validate(reqs: list, tests: list, results: dict):
    errors, warnings = [], []
    ids = Counter(r.get("id") for r in reqs)
    for r in reqs:
        rid = r.get("id")
        if not rid:
            errors.append(f"requirement without id: {str(r)[:80]}")
            continue
        if not REQ_ID.match(rid):
            warnings.append(f"{rid}: id does not follow REQ-### pattern")
        if ids[rid] > 1:
            errors.append(f"{rid}: duplicate requirement id")
        for f in ("title", "text", "type", "priority", "status", "source"):
            if not r.get(f):
                (errors if f in ("text",) else warnings).append(f"{rid}: missing '{f}'")
        if r.get("type") and r["type"] not in REQ_TYPES:
            warnings.append(f"{rid}: unknown type '{r['type']}'")
        if r.get("status") and r["status"] not in REQ_STATUS:
            warnings.append(f"{rid}: unknown status '{r['status']}'")
        if r.get("priority") and r["priority"] not in PRIORITIES:
            warnings.append(f"{rid}: unknown priority '{r['priority']}'")
    tids = Counter(t.get("id") for t in tests)
    known = set(ids)
    for t in tests:
        tid = t.get("id")
        if not tid:
            errors.append(f"test without id: {t.get('title', '')[:60]}")
            continue
        if not TC_ID.match(tid):
            warnings.append(f"{tid}: id does not follow TC-### pattern")
        if tids[tid] > 1:
            errors.append(f"{tid}: duplicate test id")
        if not t.get("title"):
            errors.append(f"{tid}: missing title")
        if t.get("priority") not in PRIORITIES:
            errors.append(f"{tid}: priority must be one of {sorted(PRIORITIES)}")
        if t.get("polarity") not in POLARITY:
            errors.append(f"{tid}: polarity must be positive|negative")
        if t.get("technique") and t["technique"] not in TECHNIQUES:
            warnings.append(f"{tid}: unknown technique '{t['technique']}'")
        if t.get("status") and t["status"] not in TC_STATUS:
            warnings.append(f"{tid}: unknown status '{t['status']}'")
        steps = t.get("steps") or []
        if not steps:
            errors.append(f"{tid}: no steps")
        for i, s in enumerate(steps, 1):
            if not str(s.get("action", "")).strip():
                errors.append(f"{tid} step {i}: missing action")
            if not str(s.get("expected", "")).strip() and t.get("technique") != "exploratory":
                errors.append(f"{tid} step {i}: missing expected result")
        for rid in t.get("requirement_ids", []):
            if rid not in known:
                errors.append(f"{tid}: BROKEN_LINK to unknown requirement {rid}")
    titles = Counter((t.get("title") or "").strip().lower() for t in tests if t.get("status") != "deprecated")
    for title, n in titles.items():
        if title and n > 1:
            warnings.append(f"duplicate test title ({n}x): '{title[:70]}'")
    for tid, res in results.items():
        if tid not in tids:
            warnings.append(f"results.json: unknown test {tid}")
        if res.get("status") not in RESULT_STATUS:
            warnings.append(f"results.json: {tid} has unknown status '{res.get('status')}'")
    return errors, warnings


def calibration(active: list) -> list[dict]:
    """Deterministic smells: priority inflation and likely equivalent-class redundancy."""
    out = []
    n = len(active)
    if n >= 8:
        crit = sum(1 for t in active if t.get("priority") == "critical")
        top = crit + sum(1 for t in active if t.get("priority") == "high")
        if crit / n > 0.20 or top / n > 0.60:
            out.append({"code": "PRIORITY_SKEW", "tests": [], "detail": {
                "critical_pct": round(100 * crit / n), "critical_high_pct": round(100 * top / n)}})
    groups = defaultdict(list)
    for t in active:
        steps = t.get("steps") or [{}]
        last = re.sub(r"\d[\d.,]*", "#", str(steps[-1].get("expected", "")).lower())
        last = re.sub(r"\s+", " ", last).strip()
        key = (tuple(sorted(t.get("requirement_ids", []))), t.get("polarity"), t.get("technique"), last)
        groups[key].append(t["id"])
    for key, ids in groups.items():
        if key[2] == "pairwise":
            continue  # pairwise rows repeat one scenario across configurations by design
        limit = 5 if key[2] == "boundary-value-analysis" else 3
        if len(ids) >= limit:
            out.append({"code": "REDUNDANT", "tests": ids, "detail": {"technique": key[2]}})
    return out


def build(reqs: list, tests: list, results: dict, changed: list[str]):
    active = [t for t in tests if t.get("status") != "deprecated"]
    by_req = defaultdict(list)
    for t in active:
        for rid in t.get("requirement_ids", []):
            by_req[rid].append(t)
    rows, gaps = [], []
    in_scope = [r for r in reqs if r.get("status") not in ("deferred", "deprecated")]
    for r in reqs:
        rid = r["id"]
        ts = by_req.get(rid, [])
        pos = sum(1 for t in ts if t.get("polarity") == "positive")
        neg = sum(1 for t in ts if t.get("polarity") == "negative")
        techs = sorted({t.get("technique", "?") for t in ts})
        statuses = [results.get(t["id"], {}).get("status", "not-run") for t in ts]
        defects = sorted({d for t in ts for d in results.get(t["id"], {}).get("defects", [])})
        if not ts:
            ex = "-"
        elif "failed" in statuses:
            ex = "failed"
        elif "blocked" in statuses:
            ex = "blocked"
        elif all(s == "passed" for s in statuses):
            ex = "passed"
        elif all(s in ("not-run", "skipped") for s in statuses):
            ex = "not-run"
        else:
            ex = "in-progress"
        score, level = risk_of(r)
        row = {"id": rid, "external_id": r.get("external_id", ""), "source": r.get("source", ""), "title": r.get("title", ""),
               "type": r.get("type", ""), "priority": r.get("priority", ""), "status": r.get("status", ""),
               "risk_score": score, "risk_level": level, "tests": [t["id"] for t in ts], "positive": pos,
               "negative": neg, "techniques": techs, "execution": ex, "defects": defects,
               "derived": bool(r.get("derived")), "questions": r.get("questions", [])}
        rows.append(row)
        if r.get("status") in ("deferred", "deprecated"):
            continue
        g = []
        if not ts:
            g.append("UNCOVERED")
        else:
            if neg == 0 and r.get("type") not in NEG_EXEMPT_TYPES:
                g.append("NO_NEGATIVE")
            if len(ts) == 1 and level in ("high", "critical"):
                g.append("THIN")
            if ex == "failed":
                g.append("FAILED")
        if r.get("derived") and r.get("status") != "ready":
            g.append("UNCONFIRMED")
        if r.get("questions") and r.get("status") == "clarification-needed":
            g.append("OPEN_QUESTIONS")
        for code in g:
            gaps.append({"id": rid, "code": code, "risk_score": score, "risk_level": level})
    gaps.sort(key=lambda g: (-g["risk_score"], g["id"], g["code"]))
    orphans = [t["id"] for t in active if not t.get("requirement_ids") and "exploratory" not in t.get("tags", [])]
    dupes = defaultdict(list)
    for t in active:
        dupes[norm_steps(t)].append(t["id"])
    duplicate_groups = [ids for ids in dupes.values() if len(ids) > 1]
    impact = []
    for rid in changed:
        impact.append({"requirement": rid, "tests": [t["id"] for t in by_req.get(rid, [])]})

    covered = [r for r in rows if r["tests"] and r["status"] not in ("deferred", "deprecated")]
    functional = [r for r in rows if r["status"] not in ("deferred", "deprecated") and r["type"] not in NEG_EXEMPT_TYPES]
    exec_counts = Counter(results.get(t["id"], {}).get("status", "not-run") for t in active)
    metrics = {
        "requirements_total": len(reqs), "requirements_in_scope": len(in_scope),
        "requirements_covered": len(covered),
        "coverage_pct": round(100 * len(covered) / len(in_scope), 1) if in_scope else 0.0,
        "functional_with_negative": sum(1 for r in functional if r["negative"] > 0),
        "functional_total": len(functional),
        "tests_active": len(active), "tests_deprecated": len(tests) - len(active),
        "orphans": len(orphans), "duplicate_groups": len(duplicate_groups),
        "by_technique": dict(Counter(t.get("technique", "?") for t in active).most_common()),
        "by_priority": {p: sum(1 for t in active if t.get("priority") == p) for p in ("critical", "high", "medium", "low")},
        "by_polarity": dict(Counter(t.get("polarity", "?") for t in active)),
        "execution": dict(exec_counts),
        "defects": len({d for r in rows for d in r["defects"]}),
    }
    reverse = [{"id": t["id"], "title": t.get("title", ""), "requirements": t.get("requirement_ids", []),
                "priority": t.get("priority", ""), "polarity": t.get("polarity", ""),
                "technique": t.get("technique", ""),
                "result": results.get(t["id"], {}).get("status", "not-run")} for t in active]
    metrics["priority_pct"] = {p: round(100 * c / len(active)) if active else 0 for p, c in metrics["by_priority"].items()}
    return {"metrics": metrics, "rows": rows, "gaps": gaps, "orphans": orphans,
            "duplicates": duplicate_groups, "reverse": reverse, "impact": impact, "calibration": calibration(active)}


def esc(s) -> str:
    return str(s).replace("|", "\\|").replace("\n", " ")


def to_md(rep: dict, errors: list, warnings: list, lang: str, project: str) -> str:
    t = L[lang]
    m = rep["metrics"]
    o = [f"# {t['title']}" + (f": {project}" if project else ""), "", f"## {t['summary']}", ""]
    o.append(f"- {t['m_reqs']}: {m['requirements_in_scope']} / {m['requirements_total']} ({t['excluded']})")
    o.append(f"- {t['m_cov']}: {m['requirements_covered']} / {m['requirements_in_scope']} (**{m['coverage_pct']}%**)")
    o.append(f"- {t['m_neg']}: {m['functional_with_negative']} / {m['functional_total']}")
    o.append(f"- {t['m_tests']}: {m['tests_active']} (+{m['tests_deprecated']} {t['depr']}) · "
             f"{', '.join(f'{k}: {v}' for k, v in m['by_polarity'].items())}")
    o.append(f"- {t['m_prio']}: " + ", ".join(f"{k}: {v} ({m['priority_pct'][k]}%)" for k, v in m["by_priority"].items()))
    o.append(f"- {t['m_tech']}: " + ", ".join(f"{k}: {v}" for k, v in m["by_technique"].items()))
    o.append(f"- {t['m_exec']}: " + ", ".join(f"{k}: {v}" for k, v in m["execution"].items()))
    o.append(f"- {t['m_orph']}: {m['orphans']} · {t['dups']}: {m['duplicate_groups']} · {t['m_def']}: {m['defects']}")
    o += ["", f"## {t['validation']}", ""]
    if not errors and not warnings:
        o.append(t["ok"])
    for e in errors:
        o.append(f"- ❌ {esc(e)}")
    for w in warnings:
        o.append(f"- ⚠ {esc(w)}")
    o += ["", f"## {t['gaps']}", ""]
    if rep["gaps"] or rep["orphans"] or rep["duplicates"]:
        o += [f"| {t['req']} | {t['risk']} | Gap | |", "|---|---|---|---|"]
        for g in rep["gaps"]:
            o.append(f"| {g['id']} | {g['risk_level']} ({g['risk_score']}) | {g['code']} | {t['g'][g['code']]} |")
        for tid in rep["orphans"]:
            o.append(f"| {tid} | - | ORPHAN | {t['orphan']} |")
        for grp in rep["duplicates"]:
            o.append(f"| {', '.join(grp)} | - | DUPLICATE | {t['dup']} |")
    else:
        o.append(t["ok"])
    if rep["calibration"]:
        o += ["", f"## {t['calib']}", ""]
        for c in rep["calibration"]:
            if c["code"] == "PRIORITY_SKEW":
                o.append("- ⚠ PRIORITY_SKEW: " + t["skew"].format(c=c["detail"]["critical_pct"], ch=c["detail"]["critical_high_pct"]))
            else:
                o.append("- ⚠ REDUNDANT: " + t["redundant"].format(n=len(c["tests"]), ids=", ".join(c["tests"]), tech=c["detail"]["technique"]))
    o += ["", f"## {t['rtm']}", "",
          f"| {t['req']} | {t['src']} | {t['title_c']} | {t['prio']} | {t['risk']} | {t['status']} | {t['tests']} | {t['pos']} | "
          f"{t['neg']} | {t['tech']} | {t['exec']} | {t['defects']} |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in rep["rows"]:
        rid = r["id"] + (f" ({r['external_id']})" if r["external_id"] else "") + (" *" if r["derived"] else "")
        o.append(f"| {rid} | {esc(r['source'])} | {esc(r['title'])} | {r['priority']} | {r['risk_level']} | {r['status']} | "
                 f"{', '.join(r['tests']) or '**' + t['none'] + '**'} | {r['positive']} | {r['negative']} | "
                 f"{', '.join(r['techniques'])} | {r['execution']} | {', '.join(r['defects'])} |")
    o.append("")
    o.append(f"\\* {t['derived']}")
    o += ["", f"## {t['reverse']}", "", f"| Test | {t['title_c']} | {t['req']} | {t['prio']} | ± | {t['tech']} | {t['exec']} |",
          "|---|---|---|---|---|---|---|"]
    for x in rep["reverse"]:
        o.append(f"| {x['id']} | {esc(x['title'])} | {', '.join(x['requirements']) or '-'} | {x['priority']} | "
                 f"{'+' if x['polarity'] == 'positive' else '−'} | {x['technique']} | {x['result']} |")
    if rep["impact"]:
        o += ["", f"## {t['impact']}", "", t["affected"] + ":", ""]
        for i in rep["impact"]:
            o.append(f"- {i['requirement']}: {', '.join(i['tests']) or t['none']}")
    return "\n".join(o) + "\n"


def write_csv(rep: dict, path: Path, lang: str):
    t = L[lang]
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow([t["req"], "External ID", t["src"], t["title_c"], "Type", t["prio"], "Risk score", t["risk"], t["status"],
                    "Derived", t["tests"], t["pos"], t["neg"], t["tech"], t["exec"], t["defects"], "Gaps"])
        gaps = defaultdict(list)
        for g in rep["gaps"]:
            gaps[g["id"]].append(g["code"])
        for r in rep["rows"]:
            w.writerow([r["id"], r["external_id"], r["source"], r["title"], r["type"], r["priority"], r["risk_score"], r["risk_level"],
                        r["status"], "yes" if r["derived"] else "", " ".join(r["tests"]), r["positive"], r["negative"],
                        " ".join(r["techniques"]), r["execution"], " ".join(r["defects"]), " ".join(gaps[r["id"]])])


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--requirements", required=True)
    ap.add_argument("--tests", required=True)
    ap.add_argument("--results")
    ap.add_argument("--out-dir", default="qa")
    ap.add_argument("--lang", choices=["en", "tr"])
    ap.add_argument("--changed", default="", help="comma-separated REQ IDs whose tests should be listed")
    ap.add_argument("--strict", action="store_true", help="exit 1 when coverage gaps exist (for CI)")
    ap.add_argument("--json", action="store_true", help="also write rtm.json")
    a = ap.parse_args()
    try:
        rq = json.loads(Path(a.requirements).read_text(encoding="utf-8-sig"))
        tc = json.loads(Path(a.tests).read_text(encoding="utf-8-sig"))
        rs = json.loads(Path(a.results).read_text(encoding="utf-8-sig")) if a.results else {}
    except (OSError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    reqs = rq["requirements"] if isinstance(rq, dict) else rq
    tests = tc["test_cases"] if isinstance(tc, dict) else tc
    results = rs.get("results", rs) if isinstance(rs, dict) else {}
    lang = a.lang or (rq.get("language") if isinstance(rq, dict) else None) or "en"
    lang = lang if lang in L else "en"
    errors, warnings = validate(reqs, tests, results)
    reqs_ok = [r for r in reqs if r.get("id")]
    tests_ok = [t for t in tests if t.get("id")]
    rep = build(reqs_ok, tests_ok, results, [c.strip() for c in a.changed.split(",") if c.strip()])
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    project = rq.get("project", "") if isinstance(rq, dict) else ""
    (out / "rtm.md").write_text(to_md(rep, errors, warnings, lang, project), encoding="utf-8")
    write_csv(rep, out / "rtm.csv", lang)
    if a.json:
        (out / "rtm.json").write_text(json.dumps({"errors": errors, "warnings": warnings, **rep},
                                                 ensure_ascii=False, indent=2), encoding="utf-8")
    m = rep["metrics"]
    sys.stdout.reconfigure(encoding="utf-8")
    print(f"coverage {m['requirements_covered']}/{m['requirements_in_scope']} ({m['coverage_pct']}%) · "
          f"tests {m['tests_active']} · gaps {len(rep['gaps'])} · orphans {m['orphans']} · "
          f"duplicates {m['duplicate_groups']} · errors {len(errors)} · warnings {len(warnings)}")
    print("priority " + ", ".join(f"{k} {v}%" for k, v in m["priority_pct"].items()))
    for c in rep["calibration"]:
        print(f"  CALIBRATION {c['code']}: {', '.join(c['tests']) or c['detail']}")
    for e in errors[:20]:
        print(f"  ERROR {e}")
    print(f"wrote {out / 'rtm.md'} and {out / 'rtm.csv'}")
    if errors:
        return 1
    if a.strict and (rep["gaps"] or rep["orphans"]):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
