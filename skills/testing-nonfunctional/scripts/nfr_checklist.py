#!/usr/bin/env python3
"""Draft accessibility (WCAG 2.2 A/AA) or security (OWASP ASVS 5.0) test cases in QA Suite compact format.

wcag: selects the success criteria relevant to the given features, emits one automated
      axe-scan test covering the machine-checkable criteria plus one manual test per
      criterion that needs human judgement (method manual/both).
asvs: selects ASVS chapters relevant to the given features and emits one test per test idea.

Output is compact text (see qa_compact.py) to review and append to qa/test-cases.src.md.
IDs continue after the highest TC-### in --tests (or start at --start).

Usage:
  python nfr_checklist.py wcag --features forms,status,auth --page "Sepet sayfası" --req REQ-012 --tests qa/test-cases.json --lang tr
  python nfr_checklist.py asvs --features auth,authz,api,payment --level L2 --req REQ-013 --tests qa/test-cases.json --out qa/design/security.src.md
  (asvs: add --baseline once per release for the general chapters V12/V13/V15/V16; --features all selects everything)
  python nfr_checklist.py wcag --list-features
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "assets"
HIGH_ASVS = {"V2", "V6", "V7", "V8", "V14"}
T = {
    "tr": {"axe_title": "Otomatik erişilebilirlik taraması (axe, WCAG 2.2 AA) – {page}",
           "axe_step": "'{page}' ekranını aç ve axe taramasını wcag2a, wcag2aa, wcag21aa, wcag22aa etiketleriyle çalıştır",
           "axe_exp": "İhlal sayısı 0; ihlal varsa kural, öğe ve WCAG kriteri kaydedilir",
           "axe_cover": "Otomatik kapsanan kriterler: {sc}",
           "man_step": "'{page}' ekranını {tool} ile incele", "man_tool": {"manual": "klavye, ekran okuyucu (NVDA/VoiceOver) ve %200/%400 yakınlaştırma", "both": "klavye ve ekran okuyucu (axe bulgusunu teyit ederek)"},
           "sec_step": "Test ortamında, yetkili test hesabıyla uygula: {idea}", "sec_exp": "Beklenen güvenli davranış gözlenir; aksi durumda bulgu kanıtıyla (istek/yanıt, log) kaydedilir",
           "auto_manual": "manuel değerlendirme", "auto_axe": "axe-core/playwright ile her build'de",
           "auto_sec": "API seviyesinde otomasyona uygun"},
    "en": {"axe_title": "Automated accessibility scan (axe, WCAG 2.2 AA) – {page}",
           "axe_step": "Open {page} and run an axe scan with tags wcag2a, wcag2aa, wcag21aa, wcag22aa",
           "axe_exp": "0 violations; any violation is recorded with rule, element and WCAG criterion",
           "axe_cover": "Automatically covered criteria: {sc}",
           "man_step": "Inspect {page} with {tool}", "man_tool": {"manual": "keyboard, screen reader (NVDA/VoiceOver) and 200%/400% zoom", "both": "keyboard and screen reader (confirming the axe finding)"},
           "sec_step": "In the test environment, with an authorised test account: {idea}", "sec_exp": "The expected secure behaviour is observed; otherwise the finding is recorded with evidence (request/response, log)",
           "auto_manual": "manual assessment", "auto_axe": "axe-core/playwright on every build",
           "auto_sec": "suitable for API-level automation"},
}


def next_id(tests_path: str | None, start: int | None) -> int:
    if start:
        return start
    if tests_path and Path(tests_path).exists():
        data = json.loads(Path(tests_path).read_text(encoding="utf-8-sig"))
        ids = [int(m.group(1)) for t in (data.get("test_cases", []) if isinstance(data, dict) else data)
               if (m := re.match(r"TC-(\d+)", t.get("id", "")))]
        return (max(ids) + 1) if ids else 1
    return 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("kind", choices=["wcag", "asvs"])
    ap.add_argument("--features", default="all", help="comma-separated feature keys (see --list-features)")
    ap.add_argument("--list-features", action="store_true")
    ap.add_argument("--level", help="wcag: A or AA (default AA = A+AA); asvs: L1/L2/L3 (label only)")
    ap.add_argument("--page", default="", help="page/screen/API under test, used in titles and steps")
    ap.add_argument("--req", required=False, default="", help="requirement ID(s) the tests trace to, comma-separated")
    ap.add_argument("--tests", help="existing test-cases.json to continue TC numbering")
    ap.add_argument("--start", type=int, help="first TC number (overrides --tests)")
    ap.add_argument("--baseline", action="store_true",
                    help="asvs: also include the general chapters that apply to every application (V2, V12, V13, V15, V16)")
    ap.add_argument("--lang", choices=["tr", "en"], default="en")
    ap.add_argument("--out")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    data = json.loads((ASSETS / ("wcag22-aa.json" if a.kind == "wcag" else "asvs5-chapters.json")).read_text(encoding="utf-8"))
    if a.list_features:
        for k, v in data["features"].items():
            print(f"{k:12s} {v}")
        return 0
    if not a.req:
        print("error: --req is required so the generated tests are traceable", file=sys.stderr)
        return 2
    feats = {f.strip() for f in a.features.split(",") if f.strip()}
    unknown = feats - set(data["features"]) - {"all"}
    if unknown:
        print(f"error: unknown features {sorted(unknown)}; use --list-features", file=sys.stderr)
        return 2
    t = T[a.lang]
    page = a.page or ("uygulama" if a.lang == "tr" else "the application")
    n = next_id(a.tests, a.start)
    out = [f"# Draft generated by nfr_checklist.py {a.kind} (features: {','.join(sorted(feats))}). "
           "Review, adapt steps to the real page, then append to qa/test-cases.src.md."]

    def block(title, pri, pol, tech, cat, steps, tags, auto, obj=""):
        nonlocal n
        tid = f"TC-{n:03d}"
        n += 1
        out.extend(["", f"## {tid} | {title}",
                    f"req: {a.req} | pri: {pri} | pol: {pol} | tech: {tech} | cat: {cat}"])
        if obj:
            out.append(f"obj: {obj}")
        for i, (act, exp) in enumerate(steps, 1):
            out.append(f"{i}. {act} => {exp}")
        out.append(f"tags: {', '.join(tags)} | auto: {auto} | status: draft")

    if a.kind == "wcag":
        levels = {"A"} if (a.level or "AA").upper() == "A" else {"A", "AA"}
        crits = [c for c in data["criteria"] if c["level"] in levels
                 and ("all" in feats or "all" in c["features"] or feats & set(c["features"]))]
        autos = [c for c in crits if c["method"] in ("auto", "both")]
        if autos:
            block(t["axe_title"].format(page=page), "h", "+", "cl", "accessibility",
                  [(t["axe_step"].format(page=page), t["axe_exp"])],
                  ["accessibility", "wcag22", "axe", "regression"], f"yes, {t['auto_axe']}",
                  obj=t["axe_cover"].format(sc=", ".join(c["sc"] for c in autos)))
        for c in crits:
            if c["method"] == "auto":
                continue
            check = c["check_tr"] if a.lang == "tr" else c["check"]
            block(f"WCAG {c['sc']} {c['name']} ({c['level']}) – {page}", "h" if c["level"] == "A" else "m", "+", "cl",
                  "accessibility", [(t["man_step"].format(page=page, tool=t["man_tool"][c["method"]]), check)],
                  ["accessibility", "wcag22", f"wcag-{c['sc'].replace('.', '-')}", c["level"].lower()],
                  f"no, {t['auto_manual']}")
        summary = f"{len(crits)} criteria selected ({len(autos)} machine-checkable), {n - next_id(a.tests, a.start)} tests"
    else:
        chapters = [c for c in data["chapters"] if "all" in feats or feats & set(c["features"])
                    or (a.baseline and "all" in c["features"])]
        first = n
        for c in chapters:
            ideas = c["ideas_tr"] if a.lang == "tr" else c["ideas"]
            name = c["name_tr"] if a.lang == "tr" else c["name"]
            for i, idea in enumerate(ideas, 1):
                short = re.split(r"[;:.(]", idea)[0][:70].strip()
                block(f"ASVS {c['id']} {name} – {short}", "h" if c["id"] in HIGH_ASVS else "m", "-", "cl", "security",
                      [(t["sec_step"].format(idea=idea), t["sec_exp"])],
                      ["security", "asvs5", c["id"].lower()] + ([a.level.lower()] if a.level else []),
                      f"yes, {t['auto_sec']}" if c["id"] in {"V2", "V4", "V7", "V8", "V9"} else f"no, {t['auto_manual']}")
        summary = f"{len(chapters)} ASVS chapters selected, {n - first} tests"
    text = "\n".join(out) + "\n"
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(text, encoding="utf-8")
        print(f"wrote {a.out}: {summary}")
    else:
        print(text)
        print(f"# {summary}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
