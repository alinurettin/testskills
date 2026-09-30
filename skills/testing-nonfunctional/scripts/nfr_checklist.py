#!/usr/bin/env python3
"""Draft accessibility (WCAG 2.2 A/AA) or security (OWASP ASVS 5.0) test cases in QA Suite compact format.

wcag: selects the success criteria relevant to the given features, emits one automated
      axe-scan test covering the machine-checkable criteria plus one manual test per
      criterion that needs human judgement (method manual/both).
asvs: selects ASVS chapters relevant to the given features and emits one test per test idea.

Output is compact text (see qa_compact.py) to review and append to qa/test-cases.src.md.
IDs continue after the highest TC-### in --tests (or start at --start).

Requirement links: every test traces to the requirement(s) of its area.
  --req-map FILE  {"default": "REQ-050", "areas": {"wcag": "REQ-050", "forms": "REQ-051", "1.4.3": "REQ-052",
                   "asvs": "REQ-060", "V6": "REQ-061", "asvs:auth": ["REQ-061", "REQ-062"]}}
  "areas" keys: the kind (wcag | asvs), a WCAG success criterion (1.4.3), an ASVS chapter (V6),
  a feature key (forms, auth ...; only features selected with --features count), or "axe" for
  the automated scan. Prefix "wcag:" / "asvs:" to scope a key to one kind (it wins over the bare
  key). Values: a REQ ID or a list. Keys are case-insensitive.
  Precedence: criterion/chapter > feature (union of the selected features) > kind > req-map
  default > --req. The axe scan uses "axe", else the union of the criteria it covers.
  A test without a requirement stops the run (exit 2) with the list of unmapped criteria/chapters.
  One REQ for everything hides thin or negative-free requirements in the RTM.

Usage:
  python nfr_checklist.py wcag --features forms,status,auth --page "Sepet sayfası" --req REQ-012 --tests qa/test-cases.json --lang tr
  python nfr_checklist.py asvs --features auth,authz,api,payment --level L2 --req-map qa/req-map.json --tests qa/test-cases.json --out qa/design/security.src.md
  (asvs: add --baseline once per release for the general chapters V12/V13/V15/V16; --features all selects everything)
  python nfr_checklist.py wcag --list-features
Exit codes: 0 ok, 2 usage error, unreadable input or unmapped tests.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
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


# ---------------------------------------------------------------- requirement mapping (--req-map)
REQ_MAP_KEYS = {"default", "operations", "tags", "capabilities", "categories", "areas"}
REQ_TOKEN = re.compile(r"^[A-Za-z][A-Za-z0-9_.:-]*$")


def req_list(value, where: str) -> list[str]:
    """A REQ ID, a comma-separated string or a list of them -> de-duplicated list (ValueError if malformed)."""
    out: list[str] = []
    for v in value if isinstance(value, list) else [value]:
        if not isinstance(v, str):
            raise ValueError(f"{where}: expected a REQ ID or a list of REQ IDs, got {json.dumps(v)}")
        for x in (p.strip() for p in v.split(",")):
            if not REQ_TOKEN.match(x):
                raise ValueError(f"{where}: invalid requirement ID {x!r}")
            if x not in out:
                out.append(x)
    if not out:
        raise ValueError(f"{where}: no requirement ID")
    return out


def load_req_map(path: str | None, sections: tuple[str, ...]) -> tuple[dict, list[str]]:
    """--req-map JSON -> ({"default": [...], section: {key: [...]}}, warnings). ValueError when unusable."""
    rmap: dict = {"default": [], **{s: {} for s in sections}}
    if not path:
        return rmap, []
    try:
        raw = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as e:
        raise ValueError(f"--req-map: cannot read {path}: {e}")
    if not isinstance(raw, dict):
        raise ValueError(f"--req-map {path}: must be a JSON object")
    warnings = [f"--req-map: unknown key '{k}' ignored" for k in raw if k not in REQ_MAP_KEYS and not k.startswith(("_", "$"))]
    if raw.get("default") not in (None, "", []):
        rmap["default"] = req_list(raw["default"], "--req-map default")
    for s in sections:
        sec = raw.get(s) or {}
        if not isinstance(sec, dict):
            raise ValueError(f"--req-map: '{s}' must be an object of key -> REQ ID(s)")
        rmap[s] = {str(k): req_list(v, f"--req-map {s}.{k}") for k, v in sec.items()}
    return rmap, warnings


def req_summary(links: list[tuple[list[str], str]]) -> str:
    """'REQ-051 12 (neg 0), REQ-052 3 (neg 0)': generated tests per requirement."""
    count: Counter = Counter()
    neg: Counter = Counter()
    for reqs, pol in links:
        for r in reqs:
            count[r] += 1
            neg[r] += pol == "-"
    return ", ".join(f"{r} {count[r]} (neg {neg[r]})" for r in count)


class AreaMap:
    """Resolves the requirement(s) of one WCAG criterion / ASVS chapter from the req-map "areas"."""

    def __init__(self, kind: str, areas: dict, default: list[str], fallback: list[str], feats: set[str]):
        self.kind, self.default, self.fallback, self.feats = kind, default, fallback, feats
        self.areas = {k.strip().lower(): v for k, v in areas.items()}

    def key(self, name: str) -> list[str]:
        """'wcag:forms' wins over 'forms'."""
        name = name.lower()
        return self.areas.get(f"{self.kind}:{name}") or self.areas.get(name) or []

    def specific(self, ident: str, features: list[str]) -> list[str]:
        """criterion/chapter key, else the union of the keys of its features selected in this run."""
        found = self.key(ident)
        if found:
            return found
        out: list[str] = []
        for f in features:
            if f != "all" and ("all" in self.feats or f in self.feats):
                out += [r for r in self.key(f) if r not in out]
        return out

    def general(self) -> list[str]:
        return self.areas.get(self.kind) or self.default or self.fallback


def known_area_keys() -> set[str]:
    """Every valid "areas" key (bare and kind-qualified), for typo warnings."""
    keys = {"wcag", "asvs", "axe", "wcag:axe"}
    for kind, file, ident in (("wcag", "wcag22-aa.json", "sc"), ("asvs", "asvs5-chapters.json", "id")):
        data = json.loads((ASSETS / file).read_text(encoding="utf-8"))
        names = set(data["features"]) - {"all"}
        names |= {str(c[ident]) for c in data["criteria" if kind == "wcag" else "chapters"]}
        keys |= {x.lower() for x in names} | {f"{kind}:{x.lower()}" for x in names}
    return keys


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("kind", choices=["wcag", "asvs"])
    ap.add_argument("--features", default="all", help="comma-separated feature keys (see --list-features)")
    ap.add_argument("--list-features", action="store_true")
    ap.add_argument("--level", help="wcag: A or AA (default AA = A+AA); asvs: L1/L2/L3 (label only)")
    ap.add_argument("--page", default="", help="page/screen/API under test, used in titles and steps")
    ap.add_argument("--req", required=False, default="", help="fallback requirement ID(s), comma-separated, for tests "
                    "the --req-map does not cover (--req and/or --req-map is needed)")
    ap.add_argument("--req-map", dest="req_map", help="JSON map areas (kind, criterion, chapter, feature) -> requirement ID(s)")
    ap.add_argument("--tests", help="existing test-cases.json to continue TC numbering")
    ap.add_argument("--start", type=int, help="first TC number (overrides --tests)")
    ap.add_argument("--baseline", action="store_true",
                    help="asvs: also include the general chapters that apply to every application (V2, V12, V13, V15, V16)")
    ap.add_argument("--lang", choices=["tr", "en"], default="en")
    ap.add_argument("--out")
    sys.stdout.reconfigure(encoding="utf-8")
    a = ap.parse_args()
    data = json.loads((ASSETS / ("wcag22-aa.json" if a.kind == "wcag" else "asvs5-chapters.json")).read_text(encoding="utf-8"))
    if a.list_features:
        for k, v in data["features"].items():
            print(f"{k:12s} {v}")
        return 0
    if not a.req.strip() and not a.req_map:
        print("error: --req and/or --req-map is required so the generated tests are traceable", file=sys.stderr)
        return 2
    try:
        fallback = req_list(a.req, "--req") if a.req.strip() else []
        rmap, map_warnings = load_req_map(a.req_map, ("areas",))
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    feats = {f.strip() for f in a.features.split(",") if f.strip()}
    unknown = feats - set(data["features"]) - {"all"}
    if unknown:
        print(f"error: unknown features {sorted(unknown)}; use --list-features", file=sys.stderr)
        return 2
    amap = AreaMap(a.kind, rmap["areas"], rmap["default"], fallback, feats)
    known = known_area_keys()
    map_warnings += [f"--req-map: areas key '{k}' is not a kind, criterion, chapter, feature or 'axe'"
                     for k in rmap["areas"] if k.strip().lower() not in known]
    if a.kind == "wcag":
        levels = {"A"} if (a.level or "AA").upper() == "A" else {"A", "AA"}
        crits = [c for c in data["criteria"] if c["level"] in levels
                 and ("all" in feats or "all" in c["features"] or feats & set(c["features"]))]
        autos = [c for c in crits if c["method"] in ("auto", "both")]
        reqs = {c["sc"]: amap.specific(c["sc"], c["features"]) or amap.general() for c in crits if c["method"] != "auto"}
        axe_reqs = list(amap.key("axe"))
        for c in autos if not axe_reqs else []:
            axe_reqs += [r for r in amap.specific(c["sc"], c["features"]) if r not in axe_reqs]
        axe_reqs = axe_reqs or amap.general()
        unmapped = [f"WCAG {sc}" for sc, r in reqs.items() if not r] + (["axe scan"] if autos and not axe_reqs else [])
    else:
        chapters = [c for c in data["chapters"] if "all" in feats or feats & set(c["features"])
                    or (a.baseline and "all" in c["features"])]
        reqs = {c["id"]: amap.specific(c["id"], c["features"]) or amap.general() for c in chapters}
        unmapped = [f"ASVS {cid}" for cid, r in reqs.items() if not r]
    if unmapped:
        more = f" ... and {len(unmapped) - 20} more" if len(unmapped) > 20 else ""
        print(f"error: no requirement for: {', '.join(unmapped[:20])}{more}. Map them in --req-map (areas: '{a.kind}', "
              "a criterion/chapter, a feature, or default) or pass --req.", file=sys.stderr)
        return 2
    for w in map_warnings:
        print(f"warning: {w}", file=sys.stderr)
    links: list[tuple[list[str], str]] = []
    t = T[a.lang]
    page = a.page or ("uygulama" if a.lang == "tr" else "the application")
    n = next_id(a.tests, a.start)
    out = [f"# Draft generated by nfr_checklist.py {a.kind} (features: {','.join(sorted(feats))}). "
           "Review, adapt steps to the real page, then append to qa/test-cases.src.md."]

    def block(title, pri, pol, tech, cat, steps, tags, auto, req, obj=""):
        nonlocal n
        tid = f"TC-{n:03d}"
        n += 1
        links.append((req, pol))
        out.extend(["", f"## {tid} | {title}",
                    f"req: {', '.join(req)} | pri: {pri} | pol: {pol} | tech: {tech} | cat: {cat}"])
        if obj:
            out.append(f"obj: {obj}")
        for i, (act, exp) in enumerate(steps, 1):
            out.append(f"{i}. {act} => {exp}")
        out.append(f"tags: {', '.join(tags)} | auto: {auto} | status: draft")

    if a.kind == "wcag":
        if autos:
            block(t["axe_title"].format(page=page), "h", "+", "cl", "accessibility",
                  [(t["axe_step"].format(page=page), t["axe_exp"])],
                  ["accessibility", "wcag22", "axe", "regression"], f"yes, {t['auto_axe']}", axe_reqs,
                  obj=t["axe_cover"].format(sc=", ".join(c["sc"] for c in autos)))
        for c in crits:
            if c["method"] == "auto":
                continue
            check = c["check_tr"] if a.lang == "tr" else c["check"]
            block(f"WCAG {c['sc']} {c['name']} ({c['level']}) – {page}", "h" if c["level"] == "A" else "m", "+", "cl",
                  "accessibility", [(t["man_step"].format(page=page, tool=t["man_tool"][c["method"]]), check)],
                  ["accessibility", "wcag22", f"wcag-{c['sc'].replace('.', '-')}", c["level"].lower()],
                  f"no, {t['auto_manual']}", reqs[c["sc"]])
        summary = f"{len(crits)} criteria selected ({len(autos)} machine-checkable), {n - next_id(a.tests, a.start)} tests"
    else:
        first = n
        for c in chapters:
            ideas = c["ideas_tr"] if a.lang == "tr" else c["ideas"]
            name = c["name_tr"] if a.lang == "tr" else c["name"]
            for i, idea in enumerate(ideas, 1):
                short = re.split(r"[;:.(]", idea)[0][:70].strip()
                block(f"ASVS {c['id']} {name} – {short}", "h" if c["id"] in HIGH_ASVS else "m", "-", "cl", "security",
                      [(t["sec_step"].format(idea=idea), t["sec_exp"])],
                      ["security", "asvs5", c["id"].lower()] + ([a.level.lower()] if a.level else []),
                      f"yes, {t['auto_sec']}" if c["id"] in {"V2", "V4", "V7", "V8", "V9"} else f"no, {t['auto_manual']}",
                      reqs[c["id"]])
        summary = f"{len(chapters)} ASVS chapters selected, {n - first} tests"
    text = "\n".join(out) + "\n"
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(text, encoding="utf-8", newline="\n")
        print(f"wrote {a.out}: {summary}")
    else:
        print(text)
        print(f"# {summary}")
    if links:
        print(f"{'  ' if a.out else '# '}requirements: {req_summary(links)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
