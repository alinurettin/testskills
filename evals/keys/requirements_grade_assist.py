#!/usr/bin/env python3
"""Keyword pre-screen for trial-requirements deliverables (EVALUATOR ONLY).

Prints, for every planted item K1..K12 and trap T1..T4, the deliverable
passages that look relevant, plus an UPPER-BOUND provisional K score.
It does NOT grade: a human/LLM grader must confirm each candidate against
the acceptance rules in requirements.md (full / half / none) and decide
trap hits.  Python 3 standard library only.

Usage:  python requirements_grade_assist.py <run-folder> [--max-evidence N]
"""
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DELIVERABLES = ("gereksinim-analizi.md", "test-edilebilir-gereksinimler.md")

FOLD = str.maketrans({"İ": "i", "I": "i", "ı": "i", "Ş": "s", "ş": "s", "Ğ": "g", "ğ": "g",
                      "Ç": "c", "ç": "c", "Ö": "o", "ö": "o", "Ü": "u", "ü": "u",
                      "Â": "a", "â": "a", "Î": "i", "î": "i", "Û": "u", "û": "u", "’": "'"})


def fold(s):
    return s.translate(FOLD).lower()


# Each item: list of alternatives; an alternative is a list of regexes that must ALL match one unit.
K = {
    "K1": (2, "NFR-1 'hızlı/makul' untestable", [
        [r"nfr-?1|performans", r"hizli|makul|olculebilir|olculemez|test edilemez|p9[059]|saniye|\d\s?ms\b"]]),
    "K2": (2, "AC-4.2 'uygun durum' undefined", [[r"uygun durum"]]),
    "K3": (2, "AC-3.1 3 vs BR-10 5 iş günü", [
        [r"\b3 is gun", r"\b5 is gun"], [r"ac-?3\.1", r"br-?10"]]),
    "K4": (2, "KVKK / photo data retention", [
        [r"kvkk|kisisel veri|aydinlatma|riza", r"fotograf|gorsel|saklama|imha|silin|erisim"]]),
    "K5": (3, "500 TL boundary gap", [
        [r"500", r"dahil|haric|esit|tam 500|500[,.]00|sinir|bosluk|kapsam|ikisi|hicbiri|<=|>="]]),
    "K6": (3, "MH override authz/audit", [
        [r"\bmh\b|musteri hizmetleri|temsilci|ac-?5\.[12]|us-?5",
         r"yetki|limit|onay mekanizma|ikinci onay|dort goz|4 goz|denetim|audit|iz kayd|kim.{0,40}ne zaman|esik|tavan"]]),
    "K7": (3, "risk score dependency", [[r"risk (skor|puan)"]]),
    "K8": (3, "Ek-B KOZ-01 vs BR-04", [
        [r"koz-?01|kozmetik", r"ek-?b|csv|acilmis_ambalaj|acilmis ambalaj|tablo",
         r"br-?04|celis|tutarsiz|uyumsuz|catis|evet"]]),
    "K9": (4, "Ek-B ELK-02 14 < 15 precedence", [
        [r"elk-?02|cep telefon|telefon", r"\b14\b"]]),
    "K10": (4, "Ek-A Örnek 2 wrong (280 vs 311,11)", [
        [r"ornek[ -]?2|ek-?a", r"\b280\b|311[,.]1|3[.]?848[,.]99|3[.]?964[,.]46|115[,.]47|3[.]?965[,.]66|116[,.]67|32[,.]04"],
        [r"311[,.]11"]]),
    "K11": (4, "cash-on-delivery refund path", [[r"kapida"]]),
    "K12": (4, "incomplete state lifecycle", [
        [r"yasam dongusu|durum (makine|model|gecis|diyagram|tablo)|bolum 5|§ ?5|state|durumlar|statu",
         r"iptal|\bred\b|reddedil|kapan|suresi dol|basarisiz|hizli iade"]]),
}

T = {
    "T1": ("return-window counting reported as undefined (defined in §2)", [
        [r"iade sures|15 gun|30 gun|teslim tarih",
         r"dahil mi|haric mi|saat dilim|zaman dilim|timezone|utc|23[:.]59|gece yarisi|teslim gunu|baslangic gun|hangi gun"]]),
    "T2": ("'iş günü' reported as undefined (defined in §2)", [
        [r"is gun", r"tanim|belirsiz|tatil|hafta sonu|arife|cumartesi|bayram|sayilir mi|dahil mi"]]),
    "T3": ("30-day Ek-B rows reported as conflicting (BR-01 covers longer)", [
        [r"giyim|ayakkabi|giy-?0|ayk-?01|30 gun", r"celis|tutarsiz|uyumsuz|catis"]]),
    "T4": ("wallet bonus reported as undefined (BR-09)", [
        [r"bonus", r"belirsiz|tanimsiz|tanimlanmamis|ne kadar|belirtilmemis|net degil"]]),
}


MAX_UNIT = 1500  # longer blocks are too broad to count as evidence for one finding


def units(text):
    """Table rows, non-table lines, blank-line blocks and heading sections (without tables)."""
    out = []
    lines = text.splitlines()
    out += [l for l in lines if l.strip().startswith("|") and not re.match(r"^\|[\s:|-]+\|$", l.strip())]
    out += [l for l in lines if l.strip() and not l.strip().startswith("|")]
    blocks = re.split(r"\n\s*\n", text) + re.split(r"\n(?=#{1,6} )", text)
    for b in blocks:
        if b.strip() and len(b) <= MAX_UNIT and not re.search(r"^\s*\|", b, flags=re.M):
            out.append(b)
    # de-duplicate, keep order
    seen, res = set(), []
    for u in out:
        if u not in seen:
            seen.add(u)
            res.append(u)
    return res


def defined_remark(unit_f):
    return bool(re.search(r"tanimli|tanimlanmis|defined|sorun degil|sorun yok", unit_f)) and not re.search(
        r"belirsiz|tanimsiz|tanimlanmamis|net degil|celis", unit_f)


def matches(unit_f, alternatives):
    return any(all(re.search(p, unit_f) for p in alt) for alt in alternatives)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    max_ev = 3
    if "--max-evidence" in sys.argv:
        max_ev = int(sys.argv[sys.argv.index("--max-evidence") + 1])
    if not args:
        print(__doc__)
        sys.exit(2)
    run = Path(args[0])
    texts = {}
    for name in DELIVERABLES:
        p = run / name
        if p.is_file():
            texts[name] = p.read_text(encoding="utf-8", errors="replace")
            print(f"[found]   {name} ({len(texts[name])} chars)")
        else:
            print(f"[MISSING] {name}")
    if not texts:
        sys.exit(1)
    all_units = [(n, u) for n, t in texts.items() for u in units(t)]
    # shortest evidence first (most specific)
    all_units.sort(key=lambda x: len(x[1]))

    def show(alts, trap=False):
        hits = [(n, u) for n, u in all_units if matches(fold(u), alts)]
        if trap:  # show likely real hits before "already defined" remarks
            hits.sort(key=lambda h: defined_remark(fold(h[1])))
        for n, u in hits[:max_ev]:
            snippet = re.sub(r"\s+", " ", u).strip()
            note = "  [looks like an 'already defined' remark -> probably no penalty]" if trap and defined_remark(
                fold(u)) else ""
            print(f"      - [{n}] {snippet[:260]}{'...' if len(snippet) > 260 else ''}{note}")
        return bool(hits)

    print("\n=== Planted items (candidate = keywords found; grader decides full/half/none) ===")
    upper = 0
    for kid, (pts, title, alts) in K.items():
        print(f"\n{kid} ({pts} pts) {title}")
        if show(alts):
            upper += pts
            print(f"    -> CANDIDATE")
        else:
            print(f"    -> no keyword evidence (likely missed; still skim the deliverable)")

    print("\n=== Traps (candidate = possible false positive; grader decides) ===")
    for tid, (title, alts) in T.items():
        print(f"\n{tid} {title}")
        print("    -> POSSIBLE HIT, check wording" if show(alts, trap=True) else "    -> no keyword evidence")

    rows = sum(1 for n, t in texts.items() if n == DELIVERABLES[0]
               for l in t.splitlines() if l.strip().startswith("|"))
    print(f"\nTable rows in {DELIVERABLES[0]}: {rows} (including header/separator)")
    print(f"Upper-bound provisional K score: {upper}/36  (NOT a grade; apply requirements.md rubric)")


if __name__ == "__main__":
    main()
