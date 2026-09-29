#!/usr/bin/env python3
"""Deterministic quality review of a test-case suite (TR/EN) - the objective half of a test review.

Per test case it flags:
  MISSING_EXPECTED (critical)  step without an expected result
  VAGUE_EXPECTED   (major)     expected result is a judgement ("works", "başarılı", "doğru çalışır") without
                               anything observable (no number, quote, message, status or value)
  NO_DATA          (major)     an input step ("gir", "enter", "seç", "upload") without concrete data
  DEPENDENT        (major)     relies on another test ("TC-012'yi çalıştır", "önceki testte", "previous test")
  NO_REQ           (major)     no requirement link (or placeholder UNLINKED)
  MULTI_ACTION     (minor)     one step performs several actions
  TOO_MANY_STEPS   (minor)     > 15 steps (probably a scenario that should be split)
  WEAK_TITLE       (minor)     title is generic ("Test 1", "Login testi", "Verify …" only)
  NO_PRIORITY      (minor)     priority missing
  EXPECTED_ECHO    (minor)     expected result repeats the action
and at suite level: duplicate titles, requirements without negative tests, priority distribution.

The judgement half (is the oracle right? are techniques adequate? is coverage risk-appropriate?)
is done by the reviewer using references/review-rubric.md.

Usage:
  python review_tests.py --tests qa/test-cases.json [--requirements qa/requirements.json] [--out qa/review-report.md] [--lang tr|en] [--json]
Exit code 0 if no critical findings, 1 otherwise.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

W = {"critical": 25, "major": 10, "minor": 3}
SEV = {"MISSING_EXPECTED": "critical", "VAGUE_EXPECTED": "major", "NO_DATA": "major", "DEPENDENT": "major",
       "NO_REQ": "major", "MULTI_ACTION": "minor", "TOO_MANY_STEPS": "minor", "WEAK_TITLE": "minor",
       "NO_PRIORITY": "minor", "EXPECTED_ECHO": "minor"}
VAGUE = re.compile(
    r"(doğru (şekilde )?çalış|düzgün (şekilde )?çalış|başarı(lı|yla)|sorunsuz|beklendiği gibi|beklenen (şekilde|sonuç)|"
    r"uygun (şekilde|mesaj|hata)|hata (olmamalı|almamalı|vermemeli)|çalışmalı|çalışır\b|işlem (tamamlan|gerçekleş)|"
    r"\bworks?\b|\bcorrect(ly)?\b|as expected|\bproperly\b|successful(ly)?|should work|no errors?\b|\bfine\b|\bok\b|"
    r"appropriate (message|error)|is displayed correctly)", re.I)
OBSERVABLE = re.compile(r"\d|['\"“”‘’«»]|\b(mesaj|message|status|durum|toplam|total|url|sayfa|page|kod|code|"
                        r"tl|eur|usd|%|göster|display|görün|visible|alan|field|liste|list|e-?posta|email)\b", re.I)
# input verbs as whole words (Turkish imperative/passive forms): "Giriş butonu" must not match "gir"
INPUT = re.compile(r"\b(gir|girin|giriniz|girilir|yaz|yazın|yazınız|seç|seçin|seçiniz|yükle|yükleyin|doldur|doldurun|"
                   r"enter|type|input|select|choose|upload|fill in|fill)\b", re.I)
CONCRETE = re.compile(r"\d|['\"“”‘’«»]|\S+@\S+\.\w+|https?://|\b[A-Z]{2,}\d*\b")
PLACEHOLDER = {"-", "—", "–", "n/a", "na", "yok", "none", "?", "tbd", "."}
DEP = re.compile(r"\bTC-\d{3,}\b|önceki test|bir önceki|previous test|test [0-9]+'?(i|ı|u|ü|de|da)?\s*(çalıştır|koş)|"
                 r"after (running )?test", re.I)
MULTI = re.compile(r"\s(ve sonra|ardından|sonra|and then|then)\s|;\s*\w", re.I)
WEAK_TITLE = re.compile(r"^(test\s*\d*|tc\s*\d*|verify|check|kontrol|doğrula)\b[\s\w]{0,12}$|^(\w+\s)?test(i)?$", re.I)
L = {
    "en": {"title": "Test Case Review", "summary": "Summary", "tests": "Tests reviewed", "score": "Average quality score",
           "by_rule": "Findings by rule", "worst": "Tests needing the most work", "suite": "Suite-level observations",
           "dup": "Duplicate titles", "noneg": "Requirements without a negative test", "prio": "Priority distribution",
           "none": "none", "note": "Automated checks cover writing quality only; judge oracle correctness, technique adequacy "
           "and risk coverage with references/review-rubric.md."},
    "tr": {"title": "Test Case İncelemesi", "summary": "Özet", "tests": "İncelenen test", "score": "Ortalama kalite puanı",
           "by_rule": "Kurala göre bulgular", "worst": "En çok iyileştirme gereken testler", "suite": "Set düzeyi gözlemler",
           "dup": "Yinelenen başlıklar", "noneg": "Negatif testi olmayan gereksinimler", "prio": "Öncelik dağılımı",
           "none": "yok", "note": "Otomatik kontroller yalnızca yazım kalitesini ölçer; beklenen sonucun doğruluğunu, teknik "
           "yeterliliğini ve risk kapsamını references/review-rubric.md ile değerlendirin."},
}
MSG = {
    "en": {"MISSING_EXPECTED": "step {s} has no expected result", "VAGUE_EXPECTED": "step {s}: vague expected result '{m}'",
           "NO_DATA": "step {s}: input without concrete data", "DEPENDENT": "depends on another test ('{m}')",
           "NO_REQ": "no requirement link", "MULTI_ACTION": "step {s} performs several actions",
           "TOO_MANY_STEPS": "{m} steps; consider splitting", "WEAK_TITLE": "generic title",
           "NO_PRIORITY": "priority missing", "EXPECTED_ECHO": "step {s}: expected result repeats the action"},
    "tr": {"MISSING_EXPECTED": "{s}. adımda beklenen sonuç yok", "VAGUE_EXPECTED": "{s}. adım: belirsiz beklenen sonuç '{m}'",
           "NO_DATA": "{s}. adım: somut veri olmadan girdi", "DEPENDENT": "başka teste bağımlı ('{m}')",
           "NO_REQ": "gereksinim bağlantısı yok", "MULTI_ACTION": "{s}. adımda birden fazla aksiyon var",
           "TOO_MANY_STEPS": "{m} adım; bölmeyi düşünün", "WEAK_TITLE": "genel/anlamsız başlık",
           "NO_PRIORITY": "öncelik yok", "EXPECTED_ECHO": "{s}. adım: beklenen sonuç aksiyonu tekrarlıyor"},
}


def review(t: dict) -> list[tuple[str, str, str]]:
    f: list[tuple[str, str, str]] = []
    steps = t.get("steps") or []
    for i, s in enumerate(steps, 1):
        act, exp, data = str(s.get("action", "")), str(s.get("expected", "")).strip(), str(s.get("data", "") or "")
        if (not exp or exp.lower() in PLACEHOLDER) and t.get("technique") != "exploratory":
            f.append(("MISSING_EXPECTED", str(i), ""))
            continue
        m = VAGUE.search(exp)
        if m and not OBSERVABLE.search(VAGUE.sub("", exp)):
            f.append(("VAGUE_EXPECTED", str(i), m.group(0)))
        if INPUT.search(act) and not data and not CONCRETE.search(act) and not t.get("test_data"):
            f.append(("NO_DATA", str(i), ""))
        if MULTI.search(act) or len(re.findall(r"\w+", act)) > 30:
            f.append(("MULTI_ACTION", str(i), ""))
        if exp and re.sub(r"\W", "", exp.lower()) == re.sub(r"\W", "", act.lower()):
            f.append(("EXPECTED_ECHO", str(i), ""))
    text = " ".join([str(t.get("preconditions", ""))] + [str(s.get("action", "")) for s in steps])
    dm = DEP.search(text.replace(t.get("id", "@@"), ""))
    if dm:
        f.append(("DEPENDENT", "", dm.group(0)))
    reqs = [r for r in t.get("requirement_ids", []) if r and r.upper() != "UNLINKED"]
    if not reqs and "exploratory" not in t.get("tags", []):
        f.append(("NO_REQ", "", ""))
    if len(steps) > 15:
        f.append(("TOO_MANY_STEPS", "", str(len(steps))))
    title = str(t.get("title", "")).strip()
    if not title or WEAK_TITLE.match(title) or len(title.split()) < 3:
        f.append(("WEAK_TITLE", "", ""))
    if not t.get("priority"):
        f.append(("NO_PRIORITY", "", ""))
    return f


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tests", required=True)
    ap.add_argument("--requirements")
    ap.add_argument("--out")
    ap.add_argument("--lang", choices=["en", "tr"])
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    try:
        tc = json.loads(Path(a.tests).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    tests = [t for t in (tc.get("test_cases", []) if isinstance(tc, dict) else tc) if t.get("status") != "deprecated"]
    lang = a.lang or (tc.get("language") if isinstance(tc, dict) else None) or "en"
    lang = lang if lang in L else "en"
    t_, msg = L[lang], MSG[lang]

    rows = []
    for t in tests:
        f = review(t)
        score = max(0, 100 - sum(W[SEV[c]] for c, _, _ in f))
        rows.append({"id": t.get("id", "?"), "title": t.get("title", ""), "score": score,
                     "findings": [{"rule": c, "severity": SEV[c], "message": msg[c].format(s=s, m=m)} for c, s, m in f]})
    by_rule = Counter(x["rule"] for r in rows for x in r["findings"])
    titles = Counter(str(t.get("title", "")).strip().lower() for t in tests)
    dups = [k for k, v in titles.items() if k and v > 1]
    neg = defaultdict(int)
    for t in tests:
        for rid in t.get("requirement_ids", []):
            neg[rid] += 1 if t.get("polarity") == "negative" else 0
    reqs = []
    if a.requirements and Path(a.requirements).exists():
        rq = json.loads(Path(a.requirements).read_text(encoding="utf-8-sig"))
        reqs = [r for r in (rq.get("requirements", []) if isinstance(rq, dict) else rq)
                if r.get("type") not in ("non-functional", "constraint", "compliance")
                and r.get("status") not in ("deferred", "deprecated")]
    no_neg = ([r["id"] for r in reqs if neg.get(r["id"], 0) == 0] if reqs
              else [k for k, v in neg.items() if v == 0 and k.upper() != "UNLINKED"])
    prio = Counter(t.get("priority", "-") for t in tests)
    avg = round(sum(r["score"] for r in rows) / len(rows), 1) if rows else 0
    rep = {"tests": len(rows), "average_score": avg, "by_rule": dict(by_rule), "duplicate_titles": dups,
           "requirements_without_negative": no_neg, "priority": dict(prio), "results": rows}
    critical = any(x["severity"] == "critical" for r in rows for x in r["findings"])
    if a.json:
        print(json.dumps(rep, ensure_ascii=False, indent=2))
        return 1 if critical else 0

    o = [f"# {t_['title']}", "", f"## {t_['summary']}", "", f"- {t_['tests']}: {len(rows)}",
         f"- {t_['score']}: {avg}/100",
         f"- {t_['by_rule']}: " + (", ".join(f"{k} ({SEV[k]}): {v}" for k, v in by_rule.most_common()) or t_["none"]),
         "", f"> {t_['note']}", "", f"## {t_['suite']}", "",
         f"- {t_['dup']}: {', '.join(dups) or t_['none']}",
         f"- {t_['noneg']}: {', '.join(no_neg) or t_['none']}",
         f"- {t_['prio']}: " + ", ".join(f"{k}: {v} ({round(100 * v / len(rows))}%)" for k, v in prio.most_common()),
         "", f"## {t_['worst']}", "", "| ID | Score | Findings |", "|---|---|---|"]
    for r in sorted(rows, key=lambda r: (r["score"], r["id"])):
        if r["findings"]:
            o.append(f"| {r['id']} {r['title'][:50]} | {r['score']} | " + "; ".join(x["message"] for x in r["findings"]).replace("|", "\\|") + " |")
    text = "\n".join(o) + "\n"
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(text, encoding="utf-8")
        print(f"wrote {a.out}: {len(rows)} tests · average {avg}/100 · " + ", ".join(f"{k} {v}" for k, v in by_rule.most_common()))
    else:
        print(text)
    return 1 if critical else 0


if __name__ == "__main__":
    sys.exit(main())
