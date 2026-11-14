#!/usr/bin/env python3
"""Test status / completion report with automatic exit-criteria evaluation.

Reads from --qa (default qa/): requirements.json, test-cases.json, results.json and,
when present, defects.json, exit-criteria.json and clarifications.md. Computes:
  - requirement coverage, execution % (passed + failed; blocked is NOT executed), pass rate,
    passed of planned, blocked %, per-requirement verdicts
  - risk coverage: per risk level, requirements passed / failed / not completely tested
  - defects: open by severity, deferred ("known defects shipped"), clusters per requirement,
    reopen and rejection rate, defect detection percentage when production defects are recorded
  - automation: automated tests / automation targets (candidates plus tests already automated)
  - every exit criterion: met / not met / unknown (data missing) / waived (qa/exit-criteria.json "waivers")
  - residual risks: in-scope requirements not passed, highest risk first, with reasons
The go/no-go decision stays with the stakeholders; the report states facts.

Usage:
  python completion_report.py --qa qa [--kind completion|status] [--lang tr|en] [--out qa/completion-report.md]
      [--json] [--json-out qa/report-facts.json] [--baseline qa/report-facts.prev.json] [--period "Sprint 14, week 2"]
      [--allow-waived] [--suspend-blocked-pct 30] [--date YYYY-MM-DD]
Exit code: 0 all exit criteria met (or none defined; with --allow-waived a valid waiver also counts),
1 some criterion not met, unknown or waived, 2 unreadable input.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

SEV = ["critical", "high", "medium", "low"]
LEVELS = ["critical", "high", "medium", "low", "-"]
RESULT_STATUS = {"passed", "failed", "blocked", "not-run", "skipped"}
OPEN_DEFECT = {"new", "open", "in-progress", "resolved", "reopened"}   # open until verified closed
CLOSED_DEFECT = {"closed", "rejected", "duplicate"}
DEFERRED = "deferred"
MANUAL_SOURCES = {"", "manual", "exploratory"}
PRODUCTION = {"production", "prod", "live", "field", "canli", "canlı"}
KNOWN_KEYS = {"min_requirement_coverage_pct", "min_execution_pct", "min_pass_rate_pct", "min_passed_of_planned_pct",
              "max_blocked_pct", "min_automation_pct", "all_critical_requirements_passed", "min_requirements_passed_pct",
              "max_blocking_questions_open", "max_open_defects", "max_deferred_defects"}
IGNORED_KEYS = {"waivers", "notes", "comment", "$schema"}
ARTIFACTS = ["test-plan.md", "requirements.json", "clarifications.md", "test-cases.json", "rtm.md", "regression.md",
             "results.json", "defects.json", "automation-coverage.md", "exports"]

L = {
    "en": {"completion": "Test Completion Report", "status": "Test Status Report", "summary": "Summary",
           "exit": "Exit criteria", "crit": "Criterion", "target": "Target", "actual": "Actual", "met": "Met",
           "yes": "✔ met", "no": "✘ not met", "unk": "? unknown", "waived": "⚠ waived by {by} until {exp}",
           "reqs": "Requirements by verdict",
           "risk": "Risk level", "defects": "Defects", "open": "open", "residual": "Residual risks (not passed, highest risk first)",
           "reason": "Reason", "verdict": "Verdict", "none": "none",
           "decision": "Exit criteria: {m} of {n} met{w}{u}. The release decision belongs to the stakeholders; "
                       "use the residual risks below to decide.",
           "unknown_n": ", {k} unknown (data missing)", "waived_n": ", {k} waived (accepted risk)",
           "no_criteria": "No qa/exit-criteria.json found; criteria not evaluated.",
           "names": {"min_requirement_coverage_pct": "Requirement coverage ≥", "min_execution_pct": "Tests executed ≥",
                     "min_pass_rate_pct": "Pass rate ≥", "min_passed_of_planned_pct": "Passed of planned ≥",
                     "max_blocked_pct": "Blocked tests ≤ %", "max_open_defects": "Open defects ≤",
                     "max_deferred_defects": "Deferred defects ≤",
                     "all_critical_requirements_passed": "All critical-risk requirements passed",
                     "min_requirements_passed_pct": "Requirements passed % ≥",
                     "max_blocking_questions_open": "Blocking questions open ≤",
                     "min_automation_pct": "Automation targets automated ≥"},
           "m": {"cov": "Requirement coverage", "exec": "Execution (passed + failed)", "pass": "Pass rate (of executed)",
                 "pop": "passed of planned", "blocked": "Blocked", "tests": "Active tests",
                 "auto": "Automation", "auto_d": "{a} of {t} automation targets automated ({p}) · of executed tests: {e}",
                 "q": "Blocking questions open", "deferred": "deferred",
                 "counts": "passed {p} · failed {f} · blocked {b} · not run {n}"},
           "why": {"failed": "failed tests: {t}", "blocked": "blocked tests: {t}", "not-run": "not executed",
                   "in-progress": "partly executed (not run: {t})", "-": "no tests"},
           "riskcov": "Risk coverage", "rc_reqs": "Requirements", "rc_passed": "All tests passed", "rc_failed": "Some test failed",
           "rc_nct": "Not completely tested", "rc_pct": "Passed %", "unrated": "unrated",
           "suspend": "⚠ Suspension check: {p}% of the planned tests are blocked (limit {lim}%). Consider suspending "
                      "execution until the impediments below are removed.",
           "waivers": "Waivers (accepted risks)", "w_line": "{c}: approved by {by} on {d}, expires {exp}. Reason: {r} (was: {was})",
           "was": {"not_met": "not met", "unknown": "unknown"},
           "known": "Known defects shipped (deferred)", "sev": "Severity", "title": "Title",
           "dm": "Defect metrics", "dm_total": "Reported: {t} · open {o} (of these {r} resolved, awaiting the confirmation test) · closed {c} · deferred {d} · rejected {x} · duplicate {u}",
           "dm_reopen": "Reopen rate: {v} ({a} of {b} fixed defects came back)",
           "dm_reject": "Rejection rate: {v} ({a} of {b} reported; duplicates {u})",
           "dm_ddp": "Defect detection percentage: {v} ({a} of {b} valid defects found before production)",
           "dm_ddp_no": "Defect detection percentage: not measurable yet (no production defects recorded; set `detected_in`)",
           "dm_clusters": "Defect clusters (valid defects per requirement)", "dm_by": "By {k}: {v}",
           "imped": "Impediments", "imp_blocked": "Blocked tests", "note": "Note", "imp_q": "Open blocking questions: {n}",
           "delta": "Changes since the baseline", "d_metric": "Metric", "d_before": "Baseline", "d_now": "Now", "d_change": "Change",
           "d_verdicts": "Requirement verdicts changed", "d_none": "no changes",
           "fill_risks": "New and changed risks", "fill_next": "Planned for the next period",
           "fill_dev": "Deviations from the plan", "fill_deliv": "Deliverables and reusable assets",
           "fill_lessons": "Lessons learned", "found": "Found in {qa}: {f}",
           "h_risks": "{{New product or project risks since the last report; risks whose level changed, and why.}}",
           "h_next": "{{Testing planned for the next period; what must be unblocked first, and by whom.}}",
           "h_dev": "{{Scope cut, schedule or environment deviations, tests not run and why.}}",
           "h_deliv": "{{Which of these are handed over, to whom; what can be reused (regression set, test data, automation).}}",
           "h_lessons": "{{What to change next time; include the post-release check (escaped defects, change fail rate).}}",
           "warnings": "Data warnings"},
    "tr": {"completion": "Test Tamamlama Raporu", "status": "Test Durum Raporu", "summary": "Özet",
           "exit": "Çıkış kriterleri", "crit": "Kriter", "target": "Hedef", "actual": "Gerçekleşen", "met": "Durum",
           "yes": "✔ karşılandı", "no": "✘ karşılanmadı", "unk": "? bilinmiyor",
           "waived": "⚠ muafiyet: {by}, {exp} tarihine kadar",
           "reqs": "Gereksinimler (sonuca göre)",
           "risk": "Risk seviyesi", "defects": "Hatalar", "open": "açık", "residual": "Kalan riskler (geçmeyenler, en yüksek risk önce)",
           "reason": "Neden", "verdict": "Sonuç", "none": "yok",
           "decision": "Çıkış kriterleri: {n} kriterden {m} tanesi karşılandı{w}{u}. Yayın kararı paydaşlara aittir; "
                       "karar için aşağıdaki kalan riskleri kullanın.",
           "unknown_n": ", {k} tanesi bilinmiyor (veri eksik)", "waived_n": ", {k} tanesi için muafiyet var (kabul edilmiş risk)",
           "no_criteria": "qa/exit-criteria.json bulunamadı; kriterler değerlendirilmedi.",
           "names": {"min_requirement_coverage_pct": "Gereksinim kapsamı ≥", "min_execution_pct": "Koşulan test ≥",
                     "min_pass_rate_pct": "Geçme oranı ≥", "min_passed_of_planned_pct": "Planlananın geçen oranı ≥",
                     "max_blocked_pct": "Bloke test ≤ %", "max_open_defects": "Açık hata ≤",
                     "max_deferred_defects": "Ertelenen hata ≤",
                     "all_critical_requirements_passed": "Tüm kritik riskli gereksinimler geçti",
                     "min_requirements_passed_pct": "Geçen gereksinim % ≥",
                     "max_blocking_questions_open": "Açık bloke eden soru ≤",
                     "min_automation_pct": "Otomasyon hedeflerinin otomatize edilen oranı ≥"},
           "m": {"cov": "Gereksinim kapsamı", "exec": "Koşum (geçen + kalan)", "pass": "Geçme oranı (koşulanların)",
                 "pop": "planlananın geçen oranı", "blocked": "Bloke", "tests": "Aktif test",
                 "auto": "Otomasyon", "auto_d": "{t} otomasyon hedefinden {a} tanesi otomatize ({p}) · koşulan testlerde: {e}",
                 "q": "Açık bloke eden soru", "deferred": "ertelenen",
                 "counts": "passed {p} · failed {f} · blocked {b} · not run {n}"},   # result enums stay English
           "why": {"failed": "kalan testler: {t}", "blocked": "bloke testler: {t}", "not-run": "koşulmadı",
                   "in-progress": "kısmen koşuldu (koşulmayan: {t})", "-": "test yok"},
           "riskcov": "Risk kapsamı", "rc_reqs": "Gereksinim", "rc_passed": "Tüm testleri geçti", "rc_failed": "Kalan testi var",
           "rc_nct": "Tam test edilmedi", "rc_pct": "Geçen %", "unrated": "derecelendirilmemiş",
           "suspend": "⚠ Askıya alma kontrolü: planlanan testlerin %{p} kadarı bloke (sınır %{lim}). Aşağıdaki engeller "
                      "kalkana kadar koşumu askıya almayı değerlendirin.",
           "waivers": "Muafiyetler (kabul edilen riskler)",
           "w_line": "{c}: {by} tarafından {d} tarihinde onaylandı, {exp} tarihinde sona erer. Gerekçe: {r} (önceki durum: {was})",
           "was": {"not_met": "karşılanmadı", "unknown": "bilinmiyor"},
           "known": "Yayına bilinen hata olarak çıkanlar (ertelenen)", "sev": "Önem", "title": "Başlık",
           "dm": "Hata metrikleri", "dm_total": "Raporlanan: {t} · açık {o} (bunların {r} tanesi çözüldü, doğrulama testi bekliyor) · kapanan {c} · ertelenen {d} · reddedilen {x} · mükerrer {u}",
           "dm_reopen": "Yeniden açılma oranı: {v} (düzeltilen {b} hatadan {a} tanesi geri döndü)",
           "dm_reject": "Reddedilme oranı: {v} (raporlanan {b} hatadan {a} tanesi; mükerrer {u})",
           "dm_ddp": "Hata yakalama yüzdesi (DDP): {v} ({b} geçerli hatadan {a} tanesi canlıdan önce bulundu)",
           "dm_ddp_no": "Hata yakalama yüzdesi (DDP): henüz ölçülemiyor (canlıda bulunan hata kaydı yok; `detected_in` alanını doldurun)",
           "dm_clusters": "Hata kümeleri (gereksinim başına geçerli hata)", "dm_by": "{k} bazında: {v}",
           "imped": "Engeller", "imp_blocked": "Bloke testler", "note": "Not", "imp_q": "Açık bloke eden soru: {n}",
           "delta": "Önceki rapora göre değişim", "d_metric": "Metrik", "d_before": "Önceki", "d_now": "Şimdi", "d_change": "Değişim",
           "d_verdicts": "Sonucu değişen gereksinimler", "d_none": "değişiklik yok",
           "fill_risks": "Yeni ve değişen riskler", "fill_next": "Sonraki dönem için planlanan",
           "fill_dev": "Plandan sapmalar", "fill_deliv": "Teslim edilenler ve yeniden kullanılabilir varlıklar",
           "fill_lessons": "Çıkarılan dersler", "found": "{qa} altında bulunanlar: {f}",
           "h_risks": "{{Son rapordan bu yana ortaya çıkan ürün veya proje riskleri; seviyesi değişen riskler ve nedeni.}}",
           "h_next": "{{Sonraki dönemde planlanan testler; önce hangi engelin, kim tarafından kaldırılması gerektiği.}}",
           "h_dev": "{{Kapsam daralması, takvim veya ortam sapmaları, koşulmayan testler ve nedeni.}}",
           "h_deliv": "{{Bunlardan hangisi kime devredildi; neler yeniden kullanılabilir (regresyon seti, test verisi, otomasyon).}}",
           "h_lessons": "{{Bir dahaki sefere ne değişmeli; canlı sonrası kontrolü ekleyin (kaçan hatalar, değişiklik hata oranı).}}",
           "warnings": "Veri uyarıları"},
}


def jload(p: Path, key: str | None = None):
    if not p.exists():
        return None
    d = json.loads(p.read_text(encoding="utf-8-sig"))
    return d.get(key, d if key is None else []) if isinstance(d, dict) and key else d


def norm(v) -> str:
    """'In Progress ', 'in_progress' -> 'in-progress'; None -> ''."""
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


risk = risk_of  # earlier name


def is_automated(res: dict) -> bool:
    """A test counts as automated when a tool wrote its last result and the tool really ran it.
    Same rule in select_regression.py. A skeleton (source set, status not-run) is not automated."""
    return norm(res.get("source")) not in MANUAL_SOURCES and norm(res.get("status")) in ("passed", "failed", "blocked")


def blocking_open(md: Path) -> int | None:
    if not md.exists():
        return None
    n = 0
    for line in md.read_text(encoding="utf-8-sig").splitlines():
        if re.match(r"^\|\s*Q-\d+", line) and re.search(r"bloke|blocking", line, re.I) \
                and not re.search(r"\|\s*(closed|kapalı|cevaplandı|answered|resolved)\s*\|", line, re.I):
            n += 1
    return n


def pct(a: int, b: int) -> float | None:
    return round(100 * a / b, 1) if b else None


def parse_day(v) -> date | None:
    try:
        return date.fromisoformat(str(v).strip())
    except ValueError:
        return None


def number(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def defect_facts(defects, results: dict, tests: list, warnings: list) -> dict:
    """Classify defects; nothing is assumed: an invalid severity or an unregistered key is 'unknown'."""
    linked = defaultdict(set)                      # defect key -> test ids, from results.json
    for tid, r in results.items():
        for k in r.get("defects") or []:
            linked[str(k)].add(tid)
    req_of_test = {t["id"]: t.get("requirement_ids") or [] for t in tests}
    out = {"source": "defects.json" if defects is not None else "results.json (severity unknown)", "open": [], "deferred": [],
           "open_by_severity": Counter(), "deferred_by_severity": Counter(), "metrics": None, "unregistered": []}
    if defects is None:
        for k in sorted(linked):
            out["open"].append({"id": k, "severity": "unknown", "status": "unknown"})
            out["open_by_severity"]["unknown"] += 1
        return out
    seen, counts = set(), Counter()
    per_req, by_component, by_cause = Counter(), Counter(), Counter()
    reopened = fixed = awaiting = closed = production = with_phase = 0
    for d in defects:
        if not isinstance(d, dict):
            warnings.append("defects.json: an entry is not an object; ignored")
            continue
        did = str(d.get("id") or "?")
        seen.add(did)
        status, sev = norm(d.get("status") or "open"), norm(d.get("severity"))
        if sev not in SEV:
            warnings.append(f"defects.json: {did} has no valid severity ({d.get('severity')!r}); counted as unknown")
            sev = "unknown"
        if status not in OPEN_DEFECT and status not in CLOSED_DEFECT and status != DEFERRED:
            warnings.append(f"defects.json: {did} has unknown status {d.get('status')!r}; counted as open")
            status = "open"
        row = {"id": did, "title": d.get("title", ""), "severity": sev, "status": status,
               "requirement_ids": sorted(set(d.get("requirement_ids") or [])
                                         or {q for t in list(d.get("test_ids") or []) + sorted(linked.get(did, []))
                                             for q in req_of_test.get(t, [])})}
        cls = "open" if status in OPEN_DEFECT else status
        counts[cls] += 1
        if cls == "open":
            out["open"].append(row)
            out["open_by_severity"][sev] += 1
        elif cls == DEFERRED:
            out["deferred"].append(row)
            out["deferred_by_severity"][sev] += 1
        if cls in ("rejected", "duplicate"):
            continue
        for q in row["requirement_ids"]:
            per_req[q] += 1
        if d.get("component"):
            by_component[str(d["component"])] += 1
        if d.get("root_cause"):
            by_cause[str(d["root_cause"])] += 1
        try:
            again = int(d.get("reopened_count") or 0) > 0
        except (TypeError, ValueError):
            again = False
        again = again or status == "reopened"
        reopened += 1 if again else 0
        fixed += 1 if again or status in ("resolved", "closed") else 0
        awaiting += 1 if status == "resolved" else 0
        closed += 1 if status == "closed" else 0
        if d.get("detected_in"):
            with_phase += 1
            production += 1 if norm(d["detected_in"]) in PRODUCTION else 0
    for k in sorted(set(linked) - seen):
        out["unregistered"].append(k)
        out["open"].append({"id": k, "severity": "unknown", "status": "unknown", "title": "",
                            "requirement_ids": sorted({q for t in linked[k] for q in req_of_test.get(t, [])})})
        out["open_by_severity"]["unknown"] += 1
    if out["unregistered"]:
        warnings.append("results.json links defects that are not in defects.json (counted as open, severity unknown): "
                        + ", ".join(out["unregistered"]))
    total = sum(counts.values())
    valid = total - counts["rejected"] - counts["duplicate"]
    order = lambda c: sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))
    out["metrics"] = {
        "reported": total, "valid": valid, "open": counts["open"], "awaiting_confirmation_test": awaiting, "closed": closed,
        "deferred": counts[DEFERRED], "rejected": counts["rejected"], "duplicate": counts["duplicate"],
        "reopened": reopened, "reopen_rate_pct": pct(reopened, fixed), "fixed_at_least_once": fixed,
        "rejection_rate_pct": pct(counts["rejected"], total),
        "clusters": [{"requirement": k, "defects": v} for k, v in order(per_req)[:5]],
        "by_component": dict(order(by_component)[:5]), "by_root_cause": dict(order(by_cause)[:5]),
        "production_defects": production,
        "ddp_pct": pct(valid - production, valid) if production else None,
        "ddp_note": None if production else "not measurable yet: no production defects recorded"
                    + ("" if with_phase else " (detected_in is empty)"),
    }
    return out


def evaluate(criteria: dict, m: dict, df: dict, rc: dict, unrated: int, warnings: list) -> list[dict]:
    evals = []

    def add(key, target, actual, ok):
        evals.append({"criterion": key, "target": target, "actual": actual, "met": ok,
                      "state": "met" if ok is True else "not_met" if ok is False else "unknown"})

    def at_least(key, target, actual):
        if not number(target):
            warnings.append(f"exit-criteria.json: {key} must be a number, got {target!r}; criterion unknown")
            return add(key, target, actual, None)
        add(key, target, actual, None if actual is None else actual >= target)

    def at_most(key, target, actual, unknown=False):
        if not number(target):
            warnings.append(f"exit-criteria.json: {key} must be a number, got {target!r}; criterion unknown")
            return add(key, target, actual, None)
        add(key, target, actual, None if actual is None else False if actual > target else None if unknown else True)

    def defect_limits(key, target, by_sev: Counter):
        unknown = by_sev.get("unknown", 0) > 0
        if number(target):                                         # one limit for all severities together
            return at_most(key, target, sum(by_sev.values()))
        if not isinstance(target, dict):
            warnings.append(f"exit-criteria.json: {key} must be an object per severity or a number; criterion unknown")
            return add(key, target, None, None)
        for sev, lim in target.items():
            if norm(sev) not in SEV:
                warnings.append(f"exit-criteria.json: {key}.{sev} is not a severity ({', '.join(SEV)}); criterion unknown")
                add(f"{key}.{sev}", lim, None, None)
                continue
            at_most(f"{key}.{sev}", lim, by_sev.get(norm(sev), 0), unknown)

    simple = {"min_requirement_coverage_pct": "coverage_pct", "min_execution_pct": "execution_pct",
              "min_pass_rate_pct": "pass_rate_pct", "min_passed_of_planned_pct": "passed_of_planned_pct",
              "min_automation_pct": "automation_pct"}
    for key, target in criteria.items():
        if key in IGNORED_KEYS or key.startswith("_"):
            continue
        if key in simple:
            at_least(key, target, m[simple[key]])
        elif key == "max_blocked_pct":
            at_most(key, target, m["blocked_pct"])
        elif key == "all_critical_requirements_passed":
            c = rc["critical"]
            ok = c["passed"] == c["requirements"]
            add(key, target, f"{c['passed']}/{c['requirements']}", True if not target else False if not ok else None if unrated else True)
        elif key == "min_requirements_passed_pct":
            if not isinstance(target, dict):
                warnings.append(f"exit-criteria.json: {key} must be an object per risk level; criterion unknown")
                add(key, target, None, None)
                continue
            for lvl, lim in target.items():
                c = rc.get(norm(lvl))
                if c is None or norm(lvl) == "-" or not number(lim):
                    warnings.append(f"exit-criteria.json: {key}.{lvl} needs a risk level (critical, high, medium, low) "
                                    "and a number; criterion unknown")
                    add(f"{key}.{lvl}", lim, None, None)
                    continue
                actual = 100.0 if not c["requirements"] else c["passed_pct"]   # no requirement at this level: nothing to fail
                ok = actual >= lim
                add(f"{key}.{lvl}", lim, f"{actual} ({c['passed']}/{c['requirements']})", False if not ok else None if unrated else True)
        elif key == "max_blocking_questions_open":
            at_most(key, target, m["blocking_questions_open"])
        elif key == "max_open_defects":
            defect_limits(key, target, df["open_by_severity"])
        elif key == "max_deferred_defects":
            defect_limits(key, target, df["deferred_by_severity"])
        else:
            warnings.append(f"exit-criteria.json: unknown criterion '{key}' cannot be evaluated; check the spelling")
            add(key, target, None, None)
    return evals


def apply_waivers(evals: list, waivers, today: date, warnings: list) -> None:
    """A waiver is a stakeholder decision recorded in exit-criteria.json. It never turns a criterion into 'met'."""
    if waivers in (None, []):
        return
    if not isinstance(waivers, list):
        warnings.append("exit-criteria.json: waivers must be a list; ignored")
        return
    for w in waivers:
        if not isinstance(w, dict):
            warnings.append("exit-criteria.json: a waiver is not an object; ignored")
            continue
        crit = str(w.get("criterion") or "").strip()
        missing = [k for k in ("criterion", "approved_by", "reason", "expires") if not str(w.get(k) or "").strip()]
        if missing:
            warnings.append(f"waiver for '{crit or '?'}' ignored: missing {', '.join(missing)}")
            continue
        exp = parse_day(w["expires"])
        if exp is None:
            warnings.append(f"waiver for '{crit}' ignored: expires is not a date (YYYY-MM-DD): {w['expires']!r}")
            continue
        hit = [e for e in evals if e["criterion"] == crit or e["criterion"].partition(".")[0] == crit]
        if not hit:
            warnings.append(f"waiver for '{crit}' ignored: no such criterion in exit-criteria.json")
            continue
        if exp < today:
            warnings.append(f"waiver for '{crit}' expired on {exp.isoformat()}; the criterion counts again")
            continue
        for e in hit:
            if e["state"] in ("met", "waived"):
                continue
            e["waiver"] = {"approved_by": str(w["approved_by"]).strip(), "date": str(w.get("date") or "").strip(),
                           "reason": str(w["reason"]).strip(), "expires": exp.isoformat(), "was": e["state"]}
            e["state"] = "waived"


def deltas(base: dict, m: dict, verdicts: dict, open_total: int) -> dict:
    bm = base.get("metrics", {}) if isinstance(base, dict) else {}
    rows = []
    now = dict(m, open_defects=open_total)
    before = dict(bm, open_defects=sum((bm.get("open_defects_by_severity") or {}).values()))
    for k in ("coverage_pct", "execution_pct", "pass_rate_pct", "passed", "failed", "blocked", "not_run", "open_defects"):
        a, b = before.get(k), now.get(k)
        change = round(b - a, 1) if number(a) and number(b) else None
        rows.append({"metric": k, "baseline": a, "now": b, "change": change})
    bv = base.get("requirement_verdicts", {}) if isinstance(base, dict) else {}
    changed = [{"id": k, "baseline": bv.get(k, "-"), "now": v} for k, v in sorted(verdicts.items()) if k in bv and bv[k] != v]
    changed += [{"id": k, "baseline": "(new)", "now": v} for k, v in sorted(verdicts.items()) if bv and k not in bv]
    return {"metrics": rows, "verdicts": changed}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--qa", default="qa")
    ap.add_argument("--kind", choices=["completion", "status"], default="completion")
    ap.add_argument("--lang", choices=["en", "tr"])
    ap.add_argument("--out")
    ap.add_argument("--json", action="store_true", help="print the computed facts as JSON instead of Markdown")
    ap.add_argument("--json-out", help="also write the facts as JSON (the --baseline of the next report)")
    ap.add_argument("--baseline", help="facts JSON of an earlier report; the report then shows what changed")
    ap.add_argument("--period", default="", help="reporting period shown in the header, e.g. 'Sprint 14, week 2'")
    ap.add_argument("--allow-waived", action="store_true",
                    help="exit 0 when every criterion is met or has a valid, unexpired waiver")
    ap.add_argument("--suspend-blocked-pct", type=float, default=30.0,
                    help="warn that the suspension criterion is reached above this %% of blocked tests (default 30)")
    ap.add_argument("--date", help="report date YYYY-MM-DD (default today); waivers expire against it")
    sys.stdout.reconfigure(encoding="utf-8")
    a = ap.parse_args()
    qa = Path(a.qa)
    today = parse_day(a.date) if a.date else date.today()
    if today is None:
        print(f"error: --date must be YYYY-MM-DD, got {a.date!r}", file=sys.stderr)
        return 2
    try:
        rq = jload(qa / "requirements.json") or {}
        reqs = rq.get("requirements", []) if isinstance(rq, dict) else rq
        tests = [t for t in (jload(qa / "test-cases.json", "test_cases") or [])
                 if isinstance(t, dict) and t.get("id") and t.get("status") != "deprecated"]
        rs = jload(qa / "results.json") or {}
        results = rs.get("results", {}) if isinstance(rs, dict) else {}
        results = {k: v for k, v in results.items() if isinstance(v, dict)} if isinstance(results, dict) else {}
        defects = jload(qa / "defects.json", "defects")
        criteria = jload(qa / "exit-criteria.json")
        base = json.loads(Path(a.baseline).read_text(encoding="utf-8-sig")) if a.baseline else None
        questions = blocking_open(qa / "clarifications.md")
    except (OSError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    reqs = [r for r in reqs if isinstance(r, dict) and r.get("id")] if isinstance(reqs, list) else []
    if not reqs or not tests:
        print(f"error: requirements.json and test-cases.json are required under {qa}", file=sys.stderr)
        return 2
    if defects is not None and not isinstance(defects, list):
        print("error: defects.json must hold a list under 'defects'", file=sys.stderr)
        return 2
    if criteria is not None and not isinstance(criteria, dict):
        print("error: exit-criteria.json must be a JSON object", file=sys.stderr)
        return 2
    lang = a.lang or (rq.get("language") if isinstance(rq, dict) else None) or "en"
    t = L[lang if lang in L else "en"]
    warnings: list[str] = []

    status = {}
    for tc in tests:
        s = norm(results.get(tc["id"], {}).get("status") or "not-run")
        if s not in RESULT_STATUS:
            warnings.append(f"results.json: {tc['id']} has unknown status {results[tc['id']].get('status')!r}; counted as not-run")
            s = "not-run"
        status[tc["id"]] = s
    passed = [k for k, s in status.items() if s == "passed"]
    failed = [k for k, s in status.items() if s == "failed"]
    blocked = [k for k, s in status.items() if s == "blocked"]
    executed = passed + failed                      # a blocked test was attempted, not executed
    automated = {k for k in status if is_automated(results.get(k, {}))}
    candidates = {tc["id"] for tc in tests if (tc.get("automation") or {}).get("candidate")}
    targets = candidates | automated
    auto_exec = [k for k in executed if k in automated]

    by_req = defaultdict(list)
    for tc in tests:
        for rid in tc.get("requirement_ids") or []:
            by_req[rid].append(tc["id"])
    in_scope = [r for r in reqs if r.get("status") not in ("deferred", "deprecated")]
    verdicts, residual = {}, []
    rc = {lvl: {"requirements": 0, "passed": 0, "failed": 0, "not_completely_tested": 0, "passed_pct": None} for lvl in LEVELS}
    for r in in_scope:
        ids = by_req.get(r["id"], [])
        st = [status[i] for i in ids]
        if not ids:
            v = "-"
        elif "failed" in st:
            v = "failed"
        elif "blocked" in st:
            v = "blocked"
        elif all(s == "passed" for s in st):
            v = "passed"
        elif all(s in ("not-run", "skipped") for s in st):
            v = "not-run"
        else:
            v = "in-progress"
        verdicts[r["id"]] = v
        score, lvl = risk_of(r)
        c = rc[lvl]
        c["requirements"] += 1
        c["passed" if v == "passed" else "failed" if v == "failed" else "not_completely_tested"] += 1
        if v != "passed":
            which = {"failed": [i for i in ids if status[i] == "failed"], "blocked": [i for i in ids if status[i] == "blocked"],
                     "in-progress": [i for i in ids if status[i] in ("not-run", "skipped")]}.get(v, [])
            defs = sorted({d for i in ids for d in results.get(i, {}).get("defects") or []})
            residual.append({"id": r["id"], "title": r.get("title", ""), "score": score, "level": lvl, "verdict": v,
                             "tests": which, "defects": defs})
    residual.sort(key=lambda x: (-x["score"], x["id"]))
    for c in rc.values():
        c["passed_pct"] = pct(c["passed"], c["requirements"])
    unrated = rc["-"]["requirements"]
    if unrated:
        warnings.append(f"{unrated} in-scope requirement(s) have neither likelihood x impact nor a priority; "
                        "criteria per risk level cannot be confirmed (unknown)")

    df = defect_facts(defects, results, tests, warnings)
    open_by_sev = df["open_by_severity"]
    covered = [r for r in in_scope if by_req.get(r["id"])]
    n = len(tests)
    m = {"coverage_pct": pct(len(covered), len(in_scope)), "execution_pct": pct(len(executed), n),
         "pass_rate_pct": pct(len(passed), len(executed)), "passed_of_planned_pct": pct(len(passed), n),
         "blocked_pct": pct(len(blocked), n),
         "automation_pct": pct(len(automated), len(targets)), "automation_targets": len(targets),
         "automation_candidates": len(candidates), "automated_tests": len(automated),
         "automated_of_executed_pct": pct(len(auto_exec), len(executed)),
         "tests": n, "executed": len(executed),
         "passed": len(passed), "failed": len(failed), "blocked": len(blocked),
         "not_run": sum(1 for s in status.values() if s in ("not-run", "skipped")),
         "blocking_questions_open": questions,
         "requirements_by_verdict": dict(Counter(verdicts.values())),
         "critical_requirements": rc["critical"]["requirements"],
         "critical_requirements_passed": rc["critical"]["passed"],
         "unrated_requirements": unrated,
         "open_defects_by_severity": dict(open_by_sev),
         "deferred_defects_by_severity": dict(df["deferred_by_severity"]), "defect_source": df["source"]}

    evals = evaluate(criteria, m, df, rc, unrated, warnings) if isinstance(criteria, dict) else []
    if isinstance(criteria, dict):
        apply_waivers(evals, criteria.get("waivers"), today, warnings)
    met = sum(1 for e in evals if e["state"] == "met")
    unknown = sum(1 for e in evals if e["state"] == "unknown")
    waived = sum(1 for e in evals if e["state"] == "waived")
    code = 0 if met == len(evals) or (a.allow_waived and met + waived == len(evals)) else 1

    impediments = [{"id": k, "note": str(results.get(k, {}).get("note") or ""),
                    "requirements": next((tc.get("requirement_ids") or [] for tc in tests if tc["id"] == k), [])}
                   for k in blocked]
    suspend = m["blocked_pct"] is not None and m["blocked_pct"] > a.suspend_blocked_pct
    found = [f for f in ARTIFACTS if (qa / f).exists()]
    facts = {"kind": a.kind, "date": today.isoformat(), "period": a.period, "metrics": m, "exit_criteria": evals,
             "gate": {"criteria": len(evals), "met": met, "waived": waived, "unknown": unknown,
                      "not_met": len(evals) - met - waived - unknown, "exit_code": code},
             "risk_coverage": rc, "requirement_verdicts": verdicts, "residual_risks": residual,
             "defects": {"open": df["open"], "known_defects_shipped": df["deferred"], "metrics": df["metrics"],
                         "unregistered_keys": df["unregistered"]},
             "impediments": {"blocked_tests": impediments, "suspension_check": {"limit_pct": a.suspend_blocked_pct,
                                                                                "reached": suspend}},
             "artifacts_found": found, "warnings": warnings}
    if base is not None:
        facts["changes_since_baseline"] = deltas(base, m, verdicts, sum(open_by_sev.values()))
    for w in warnings:
        print(f"warning: {w}", file=sys.stderr)
    if a.json_out:
        Path(a.json_out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.json_out).write_text(json.dumps(facts, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    if a.json:
        print(json.dumps(facts, ensure_ascii=False, indent=2))
        return code

    fmt = lambda v, suffix="%": "–" if v is None else f"{v}{suffix}"
    sev_line = lambda c: ", ".join(f"{k}: {v}" for k, v in sorted(
        c.items(), key=lambda kv: SEV.index(kv[0]) if kv[0] in SEV else 9)) or t["none"]
    esc = lambda s: str(s).replace("|", "\\|").replace("\n", " ")
    title = t[a.kind] + (f": {rq.get('project')}" if isinstance(rq, dict) and rq.get("project") else "")
    run = rs.get("run", "") if isinstance(rs, dict) else ""
    o = [f"# {title}", "", " · ".join(x for x in (today.isoformat(), run, a.period) if x), "", f"## {t['summary']}", ""]
    if evals:
        o.append(t["decision"].format(m=met, n=len(evals), w=t["waived_n"].format(k=waived) if waived else "",
                                      u=t["unknown_n"].format(k=unknown) if unknown else ""))
    else:
        o.append(t["no_criteria"])
    o += ["", f"- {t['m']['cov']}: {len(covered)}/{len(in_scope)} ({fmt(m['coverage_pct'])})",
          f"- {t['m']['exec']}: {m['executed']}/{n} ({fmt(m['execution_pct'])}) · "
          + t["m"]["counts"].format(p=m["passed"], f=m["failed"], b=m["blocked"], n=m["not_run"]),
          f"- {t['m']['pass']}: {fmt(m['pass_rate_pct'])} · {t['m']['pop']}: {fmt(m['passed_of_planned_pct'])}",
          f"- {t['m']['blocked']}: {m['blocked']}/{n} ({fmt(m['blocked_pct'])})",
          f"- {t['m']['auto']}: " + t["m"]["auto_d"].format(a=len(automated), t=len(targets), p=fmt(m["automation_pct"]),
                                                          e=f"{len(auto_exec)}/{m['executed']}"),
          f"- {t['m']['q']}: {fmt(m['blocking_questions_open'], '')}",
          f"- {t['defects']} ({t['open']}, {df['source']}): {sev_line(open_by_sev)}"
          + (f" · {t['m']['deferred']}: {sev_line(df['deferred_by_severity'])}" if df["deferred"] else "")]
    if suspend:
        o += ["", t["suspend"].format(p=m["blocked_pct"], lim=f"{a.suspend_blocked_pct:g}")]
    if evals:
        o += ["", f"## {t['exit']}", "", f"| {t['crit']} | {t['target']} | {t['actual']} | {t['met']} |", "|---|---|---|---|"]
        for e in evals:
            base_key, _, sub = e["criterion"].partition(".")
            name = t["names"].get(base_key, base_key) + (f" ({sub})" if sub else "")
            state = {"met": t["yes"], "not_met": t["no"], "unknown": t["unk"]}.get(e["state"]) or t["waived"].format(
                by=esc(e["waiver"]["approved_by"]), exp=e["waiver"]["expires"])
            o.append(f"| {name} | {e['target']} | {e['actual'] if e['actual'] is not None else '–'} | {state} |")
        if waived:
            o += ["", f"### {t['waivers']}", ""]
            for e in evals:
                if e["state"] == "waived":
                    w = e["waiver"]
                    o.append("- " + t["w_line"].format(c=e["criterion"], by=w["approved_by"], d=w["date"] or "–",
                                                       exp=w["expires"], r=w["reason"], was=t["was"][w["was"]]))
    o += ["", f"## {t['riskcov']}", "",
          f"| {t['risk']} | {t['rc_reqs']} | {t['rc_passed']} | {t['rc_failed']} | {t['rc_nct']} | {t['rc_pct']} |",
          "|---|---|---|---|---|---|"]
    for lvl in LEVELS:
        c = rc[lvl]
        if lvl == "-" and not c["requirements"]:
            continue
        o.append(f"| {t['unrated'] if lvl == '-' else lvl} | {c['requirements']} | {c['passed']} | {c['failed']} | "
                 f"{c['not_completely_tested']} | {fmt(c['passed_pct'])} |")
    o += ["", f"## {t['reqs']}", "", f"| {t['verdict']} | # |", "|---|---|"]
    for k, v in sorted(m["requirements_by_verdict"].items()):
        o.append(f"| {k} | {v} |")
    o += ["", f"## {t['residual']}", ""]
    if residual:
        o += [f"| REQ | {t['risk']} | {t['verdict']} | {t['reason']} | {t['defects']} |", "|---|---|---|---|---|"]
        for x in residual:
            why = t["why"].get(x["verdict"], x["verdict"]).format(t=", ".join(x["tests"]) or "-")
            o.append(f"| {x['id']} {esc(x['title'])} | {x['level']} ({x['score']}) | {x['verdict']} | {why} | "
                     f"{', '.join(x['defects']) or '-'} |")
    else:
        o.append(t["none"])
    if df["deferred"] or df["metrics"]:
        o += ["", f"## {t['defects']}", ""]
        dm = df["metrics"]
        if dm:
            o.append("- " + t["dm_total"].format(t=dm["reported"], o=dm["open"], r=dm["awaiting_confirmation_test"], c=dm["closed"], d=dm["deferred"],
                                                 x=dm["rejected"], u=dm["duplicate"]))
            o.append("- " + t["dm_reopen"].format(v=fmt(dm["reopen_rate_pct"]), a=dm["reopened"], b=dm["fixed_at_least_once"]))
            o.append("- " + t["dm_reject"].format(v=fmt(dm["rejection_rate_pct"]), a=dm["rejected"], b=dm["reported"],
                                                  u=dm["duplicate"]))
            o.append("- " + (t["dm_ddp"].format(v=fmt(dm["ddp_pct"]), a=dm["valid"] - dm["production_defects"], b=dm["valid"])
                             if dm["ddp_pct"] is not None else t["dm_ddp_no"]))
            if dm["clusters"]:
                o.append(f"- {t['dm_clusters']}: " + ", ".join(f"{c['requirement']}: {c['defects']}" for c in dm["clusters"]))
            for label, key in (("component", "by_component"), ("root_cause", "by_root_cause")):
                if dm[key]:
                    o.append("- " + t["dm_by"].format(k=label, v=", ".join(f"{k}: {v}" for k, v in dm[key].items())))
        if df["deferred"]:
            o += ["", f"### {t['known']}", "", f"| ID | {t['sev']} | {t['title']} | REQ |", "|---|---|---|---|"]
            for d in sorted(df["deferred"], key=lambda d: (SEV.index(d["severity"]) if d["severity"] in SEV else 9, d["id"])):
                o.append(f"| {esc(d['id'])} | {d['severity']} | {esc(d['title'])} | {', '.join(d['requirement_ids']) or '-'} |")
    if a.kind == "status" or impediments:
        o += ["", f"## {t['imped']}", ""]
        if impediments:
            o += [f"| {t['imp_blocked']} | REQ | {t['note']} |", "|---|---|---|"]
            o += [f"| {x['id']} | {', '.join(x['requirements']) or '-'} | {esc(x['note']) or '-'} |" for x in impediments]
        else:
            o.append(f"- {t['imp_blocked']}: {t['none']}")
        if questions:
            o += ["", "- " + t["imp_q"].format(n=questions)]
    if base is not None:
        ch = facts["changes_since_baseline"]
        o += ["", f"## {t['delta']}", "", f"| {t['d_metric']} | {t['d_before']} | {t['d_now']} | {t['d_change']} |", "|---|---|---|---|"]
        for r in ch["metrics"]:
            sign = "–" if r["change"] is None else f"{r['change']:+g}"
            o.append(f"| {r['metric']} | {fmt(r['baseline'], '')} | {fmt(r['now'], '')} | {sign} |")
        o += ["", f"{t['d_verdicts']}: " + ("; ".join(f"{v['id']} {v['baseline']} → {v['now']}" for v in ch["verdicts"])
                                             or t["d_none"])]
    if a.kind == "status":
        o += ["", f"## {t['fill_risks']}", "", t["h_risks"], "", f"## {t['fill_next']}", "", t["h_next"]]
    else:
        o += ["", f"## {t['fill_dev']}", "", t["h_dev"], "", f"## {t['fill_deliv']}", "",
              t["found"].format(qa=qa.name, f=", ".join(found) or t["none"]), "", t["h_deliv"],
              "", f"## {t['fill_lessons']}", "", t["h_lessons"]]
    if warnings:
        o += ["", f"## {t['warnings']}", ""] + [f"- ⚠ {esc(w)}" for w in warnings]
    text = "\n".join(o) + "\n"
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(text, encoding="utf-8", newline="\n")
        print(f"wrote {a.out}: exit criteria {met}/{len(evals)} met" + (f", {waived} waived" if waived else "")
              + (f", {unknown} unknown" if unknown else ""))
    else:
        print(text)
    return code


if __name__ == "__main__":
    sys.exit(main())
