#!/usr/bin/env python3
"""Test status / completion report with automatic exit-criteria evaluation.

Reads from --qa (default qa/): requirements.json, test-cases.json, results.json and,
when present, defects.json, exit-criteria.json and clarifications.md. Computes:
  - requirement coverage, execution %, pass rate, per-requirement verdicts by risk
  - defects by severity/status (defects.json, else defect keys found in results.json)
  - automation share of executed tests (results written by a tool: any "source" except "manual",
    e.g. playwright, junit/maestro, ai_eval, reconcile)
  - evaluation of every exit criterion: met / not met / unknown (data missing)
  - residual risks: in-scope requirements not passed, highest risk first, with reasons
The go/no-go decision stays with the stakeholders; the report states facts.

Usage:
  python completion_report.py --qa qa [--kind completion|status] [--lang tr|en] [--out qa/completion-report.md] [--json]
Exit code: 0 all exit criteria met (or none defined), 1 some not met/unknown, 2 unreadable input.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

OPEN_DEFECT = {"open", "in-progress", "resolved", "reopened", "new"}
SEV = ["critical", "high", "medium", "low"]
L = {
    "en": {"completion": "Test Completion Report", "status": "Test Status Report", "summary": "Summary",
           "exit": "Exit criteria", "crit": "Criterion", "target": "Target", "actual": "Actual", "met": "Met",
           "yes": "✔ met", "no": "✘ not met", "unk": "? unknown", "reqs": "Requirements by verdict",
           "risk": "Risk level", "defects": "Defects", "open": "open", "residual": "Residual risks (not passed, highest risk first)",
           "reason": "Reason", "verdict": "Verdict", "none": "none", "decision": "Exit criteria: {m} of {n} met{u}. The release decision belongs to the stakeholders; "
           "use the residual risks below to decide.", "unknown_n": ", {k} unknown (data missing)",
           "no_criteria": "No qa/exit-criteria.json found; criteria not evaluated.",
           "names": {"min_requirement_coverage_pct": "Requirement coverage ≥", "min_execution_pct": "Tests executed ≥",
                     "min_pass_rate_pct": "Pass rate ≥", "max_open_defects": "Open defects ≤",
                     "all_critical_requirements_passed": "All critical-risk requirements passed",
                     "max_blocking_questions_open": "Blocking questions open ≤", "min_automation_pct": "Executed by automation ≥"},
           "m": {"cov": "Requirement coverage", "exec": "Execution", "pass": "Pass rate", "tests": "Active tests",
                 "auto": "Executed by automation", "q": "Blocking questions open"},
           "why": {"failed": "failed tests: {t}", "blocked": "blocked tests: {t}", "not-run": "not executed",
                   "in-progress": "partly executed (not run: {t})", "-": "no tests"}},
    "tr": {"completion": "Test Tamamlama Raporu", "status": "Test Durum Raporu", "summary": "Özet",
           "exit": "Çıkış kriterleri", "crit": "Kriter", "target": "Hedef", "actual": "Gerçekleşen", "met": "Durum",
           "yes": "✔ karşılandı", "no": "✘ karşılanmadı", "unk": "? bilinmiyor", "reqs": "Gereksinimler (sonuca göre)",
           "risk": "Risk seviyesi", "defects": "Hatalar", "open": "açık", "residual": "Kalan riskler (geçmeyenler, en yüksek risk önce)",
           "reason": "Neden", "verdict": "Sonuç", "none": "yok", "decision": "Çıkış kriterleri: {n} kriterden {m} tanesi karşılandı{u}. Yayın kararı paydaşlara aittir; "
           "karar için aşağıdaki kalan riskleri kullanın.", "unknown_n": ", {k} tanesi bilinmiyor (veri eksik)",
           "no_criteria": "qa/exit-criteria.json bulunamadı; kriterler değerlendirilmedi.",
           "names": {"min_requirement_coverage_pct": "Gereksinim kapsamı ≥", "min_execution_pct": "Koşulan test ≥",
                     "min_pass_rate_pct": "Geçme oranı ≥", "max_open_defects": "Açık hata ≤",
                     "all_critical_requirements_passed": "Tüm kritik riskli gereksinimler geçti",
                     "max_blocking_questions_open": "Açık bloke eden soru ≤", "min_automation_pct": "Otomasyonla koşulan ≥"},
           "m": {"cov": "Gereksinim kapsamı", "exec": "Koşum", "pass": "Geçme oranı", "tests": "Aktif test",
                 "auto": "Otomasyonla koşulan", "q": "Açık bloke eden soru"},
           "why": {"failed": "kalan testler: {t}", "blocked": "bloke testler: {t}", "not-run": "koşulmadı",
                   "in-progress": "kısmen koşuldu (koşulmayan: {t})", "-": "test yok"}},
}


def jload(p: Path, key: str | None = None):
    if not p.exists():
        return None
    d = json.loads(p.read_text(encoding="utf-8-sig"))
    return d.get(key, d if key is None else []) if isinstance(d, dict) and key else d


def risk(r: dict) -> tuple[int, str]:
    rk = r.get("risk") or {}
    try:
        s = int(rk.get("likelihood", 0)) * int(rk.get("impact", 0))
    except (TypeError, ValueError):
        s = 0
    if not s:
        s = {"critical": 20, "high": 12, "medium": 6, "low": 2}.get(r.get("priority"), 0)
    return s, ("critical" if s >= 17 else "high" if s >= 10 else "medium" if s >= 5 else "low" if s else "-")


def blocking_open(md: Path) -> int | None:
    if not md.exists():
        return None
    n = 0
    for line in md.read_text(encoding="utf-8").splitlines():
        if re.match(r"^\|\s*Q-\d+", line) and re.search(r"bloke|blocking", line, re.I) \
                and not re.search(r"\|\s*(closed|kapalı|cevaplandı|answered|resolved)\s*\|", line, re.I):
            n += 1
    return n


def pct(a: int, b: int) -> float | None:
    return round(100 * a / b, 1) if b else None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--qa", default="qa")
    ap.add_argument("--kind", choices=["completion", "status"], default="completion")
    ap.add_argument("--lang", choices=["en", "tr"])
    ap.add_argument("--out")
    ap.add_argument("--json", action="store_true", help="print the computed facts as JSON instead of Markdown")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    qa = Path(a.qa)
    try:
        rq = jload(qa / "requirements.json") or {}
        reqs = rq.get("requirements", []) if isinstance(rq, dict) else rq
        tests = [t for t in (jload(qa / "test-cases.json", "test_cases") or []) if t.get("status") != "deprecated"]
        rs = jload(qa / "results.json") or {}
        results = rs.get("results", {}) if isinstance(rs, dict) else {}
        defects = jload(qa / "defects.json", "defects")
        criteria = jload(qa / "exit-criteria.json")
    except (OSError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    if not reqs or not tests:
        print(f"error: requirements.json and test-cases.json are required under {qa}", file=sys.stderr)
        return 2
    lang = a.lang or (rq.get("language") if isinstance(rq, dict) else None) or "en"
    t = L[lang if lang in L else "en"]

    status = {tc["id"]: results.get(tc["id"], {}).get("status", "not-run") for tc in tests}
    executed = [k for k, s in status.items() if s in ("passed", "failed", "blocked")]
    passed = [k for k, s in status.items() if s == "passed"]
    failed = [k for k, s in status.items() if s == "failed"]
    auto_exec = [k for k in executed if results.get(k, {}).get("source") not in (None, "", "manual")]

    by_req = defaultdict(list)
    for tc in tests:
        for rid in tc.get("requirement_ids", []):
            by_req[rid].append(tc["id"])
    in_scope = [r for r in reqs if r.get("status") not in ("deferred", "deprecated")]
    verdicts, residual = {}, []
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
        if v != "passed":
            score, lvl = risk(r)
            which = {"failed": [i for i in ids if status[i] == "failed"], "blocked": [i for i in ids if status[i] == "blocked"],
                     "in-progress": [i for i in ids if status[i] in ("not-run", "skipped")]}.get(v, [])
            defs = sorted({d for i in ids for d in results.get(i, {}).get("defects", [])})
            residual.append({"id": r["id"], "title": r.get("title", ""), "score": score, "level": lvl, "verdict": v,
                             "tests": which, "defects": defs})
    residual.sort(key=lambda x: (-x["score"], x["id"]))

    # defects
    if defects is not None:
        open_defs = [d for d in defects if str(d.get("status", "open")).lower() in OPEN_DEFECT]
        open_by_sev = Counter(str(d.get("severity", "unknown")).lower() for d in open_defs)
        defect_source = "defects.json"
    else:
        keys = sorted({d for r in results.values() for d in r.get("defects", [])})
        open_defs = [{"id": k} for k in keys]
        open_by_sev = Counter({"unknown": len(keys)}) if keys else Counter()
        defect_source = "results.json (severity unknown)"

    covered = [r for r in in_scope if by_req.get(r["id"])]
    crit_reqs = [r for r in in_scope if risk(r)[1] == "critical"]
    m = {"coverage_pct": pct(len(covered), len(in_scope)), "execution_pct": pct(len(executed), len(tests)),
         "pass_rate_pct": pct(len(passed), len(passed) + len(failed)),
         "automation_pct": pct(len(auto_exec), len(executed)), "tests": len(tests), "executed": len(executed),
         "passed": len(passed), "failed": len(failed), "blocked": sum(1 for s in status.values() if s == "blocked"),
         "not_run": sum(1 for s in status.values() if s in ("not-run", "skipped")),
         "blocking_questions_open": blocking_open(qa / "clarifications.md"),
         "requirements_by_verdict": dict(Counter(verdicts.values())),
         "critical_requirements": len(crit_reqs),
         "critical_requirements_passed": sum(1 for r in crit_reqs if verdicts.get(r["id"]) == "passed"),
         "open_defects_by_severity": dict(open_by_sev), "defect_source": defect_source}

    evals = []
    if isinstance(criteria, dict):
        def add(key, target, actual, ok):
            evals.append({"criterion": key, "target": target, "actual": actual, "met": ok})
        for key, target in criteria.items():
            if key == "min_requirement_coverage_pct":
                add(key, target, m["coverage_pct"], None if m["coverage_pct"] is None else m["coverage_pct"] >= target)
            elif key == "min_execution_pct":
                add(key, target, m["execution_pct"], None if m["execution_pct"] is None else m["execution_pct"] >= target)
            elif key == "min_pass_rate_pct":
                add(key, target, m["pass_rate_pct"], None if m["pass_rate_pct"] is None else m["pass_rate_pct"] >= target)
            elif key == "min_automation_pct":
                add(key, target, m["automation_pct"], None if m["automation_pct"] is None else m["automation_pct"] >= target)
            elif key == "all_critical_requirements_passed":
                ok = m["critical_requirements_passed"] == m["critical_requirements"]
                add(key, target, f"{m['critical_requirements_passed']}/{m['critical_requirements']}", ok if target else True)
            elif key == "max_blocking_questions_open":
                q = m["blocking_questions_open"]
                add(key, target, q, None if q is None else q <= target)
            elif key == "max_open_defects" and isinstance(target, dict):
                unknown_sev = defects is None and open_defs
                for sev, lim in target.items():
                    n = open_by_sev.get(sev, 0)
                    add(f"{key}.{sev}", lim, n, None if unknown_sev else n <= lim)
    met = sum(1 for e in evals if e["met"] is True)
    unknown = sum(1 for e in evals if e["met"] is None)
    facts = {"metrics": m, "exit_criteria": evals, "residual_risks": residual}
    if a.json:
        print(json.dumps(facts, ensure_ascii=False, indent=2))
        return 0 if evals and met == len(evals) or not evals else 1

    fmt = lambda v, suffix="%": "–" if v is None else f"{v}{suffix}"
    title = t[a.kind] + (f": {rq.get('project')}" if isinstance(rq, dict) and rq.get("project") else "")
    run = rs.get("run", "") if isinstance(rs, dict) else ""
    o = [f"# {title}", "", f"{date.today().isoformat()}" + (f" · {run}" if run else ""), "", f"## {t['summary']}", ""]
    if evals:
        o.append(t["decision"].format(m=met, n=len(evals), u=t["unknown_n"].format(k=unknown) if unknown else ""))
    else:
        o.append(t["no_criteria"])
    o += ["", f"- {t['m']['cov']}: {len(covered)}/{len(in_scope)} ({fmt(m['coverage_pct'])})",
          f"- {t['m']['exec']}: {m['executed']}/{m['tests']} ({fmt(m['execution_pct'])}) · passed {m['passed']} · "
          f"failed {m['failed']} · blocked {m['blocked']} · not run {m['not_run']}",
          f"- {t['m']['pass']}: {fmt(m['pass_rate_pct'])}",
          f"- {t['m']['auto']}: {len(auto_exec)}/{m['executed']} ({fmt(m['automation_pct'])})",
          f"- {t['m']['q']}: {fmt(m['blocking_questions_open'], '')}",
          f"- {t['defects']} ({t['open']}, {defect_source}): " + (", ".join(f"{k}: {v}" for k, v in sorted(
              open_by_sev.items(), key=lambda kv: SEV.index(kv[0]) if kv[0] in SEV else 9)) or t["none"])]
    if evals:
        o += ["", f"## {t['exit']}", "", f"| {t['crit']} | {t['target']} | {t['actual']} | {t['met']} |", "|---|---|---|---|"]
        for e in evals:
            base, _, sev = e["criterion"].partition(".")
            name = t["names"].get(base, base) + (f" ({sev})" if sev else "")
            o.append(f"| {name} | {e['target']} | {e['actual'] if e['actual'] is not None else '–'} | "
                     f"{t['yes'] if e['met'] is True else t['no'] if e['met'] is False else t['unk']} |")
    o += ["", f"## {t['reqs']}", "", f"| {t['verdict']} | # |", "|---|---|"]
    for k, v in sorted(m["requirements_by_verdict"].items()):
        o.append(f"| {k} | {v} |")
    o += ["", f"## {t['residual']}", ""]
    if residual:
        o += [f"| REQ | {t['risk']} | {t['verdict']} | {t['reason']} | {t['defects']} |", "|---|---|---|---|---|"]
        for x in residual:
            why = t["why"].get(x["verdict"], x["verdict"]).format(t=", ".join(x["tests"]) or "-")
            o.append(f"| {x['id']} {x['title']} | {x['level']} ({x['score']}) | {x['verdict']} | {why} | "
                     f"{', '.join(x['defects']) or '-'} |")
    else:
        o.append(t["none"])
    text = "\n".join(o) + "\n"
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(text, encoding="utf-8")
        print(f"wrote {a.out}: exit criteria {met}/{len(evals)} met" + (f", {unknown} unknown" if unknown else ""))
    else:
        print(text)
    return 0 if not evals or met == len(evals) else 1


if __name__ == "__main__":
    sys.exit(main())
