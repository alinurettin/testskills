#!/usr/bin/env python3
"""Heuristic requirements linter (English + Turkish).

Flags wording that commonly makes requirements ambiguous, unverifiable or
non-atomic: vague adjectives, escape clauses, open-ended lists, TBD markers,
unmeasured performance words, compound statements, user stories without
acceptance criteria, near-duplicates and ID problems.

The linter only produces *candidates*. A human or the model must still judge
each finding in context - e.g. "fast" inside a product name is not a defect.

Input
  - requirements.json (QA Suite data model), or
  - a .txt/.md file: one requirement per line or bullet; an optional leading
    ID such as "REQ-001:" or "FR-12 -" is kept.

Usage
  python lint_requirements.py qa/requirements.json
  python lint_requirements.py reqs.md --format json --out qa/design/lint.json
  python lint_requirements.py reqs.md --lang tr

Standard library only. Exit code 0 always (the linter is advisory) unless the
input cannot be read (exit 2).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# --------------------------------------------------------------------------
# Term lists. A trailing "*" means "allow any suffix" (Turkish is agglutinative:
# hızlı -> hızlıca, hızlı bir şekilde is covered by the phrase list).
# --------------------------------------------------------------------------
VAGUE = {
    "en": [
        "fast", "faster", "quick", "quickly", "slow", "easy", "easily", "easy to use",
        "user-friendly", "user friendly", "simple", "simply", "intuitive", "efficient*",
        "flexible", "robust", "seamless*", "adequate*", "appropriate*", "sufficient*",
        "reasonable", "reasonably", "normal", "normally", "modern", "nice", "good",
        "better", "best", "high performance", "high-performance", "large", "small",
        "many", "few", "several", "some", "most", "optimal*", "optimum", "significant*",
        "clear", "clearly", "state-of-the-art", "as soon as possible", "asap",
        "immediately", "instantly", "real-time", "real time", "timely", "approximately",
        "roughly", "user-oriented", "powerful", "smooth*", "responsive", "scalable",
        "secure", "securely", "reliable", "stable", "acceptable", "satisfactory",
    "sufficiently", "reasonable time", "user-oriented",
    ],
    "tr": [
        "hızlı*", "hızla", "çabuk*", "yavaş*", "kolay*", "kullanıcı dostu",
        "basit*", "sezgisel", "verimli*", "esnek", "sağlam", "sorunsuz*", "yeterli*",
        "uygun şekilde", "uygun bir şekilde", "makul*", "normal*", "modern", "iyi",
        "daha iyi", "en iyi", "yüksek performans*", "performanslı", "büyük", "küçük",
        "birkaç", "bazı", "çoğu", "optimum", "optimal", "önemli ölçüde", "net bir şekilde",
        "anında", "anlık", "gerçek zamanlı", "zamanında", "yaklaşık", "mümkün olan en kısa sürede",
        "en kısa sürede", "hemen", "etkin*", "etkili*", "kaliteli", "stabil", "kararlı*",
        "güvenli*", "güvenilir*", "ölçeklenebilir", "akıcı", "pratik", "şık", "kullanışlı",
        "kabul edilebilir*", "tatmin edici", "makul sürede", "kısa sürede", "yeterince",
    ],
}
LOOPHOLE = {
    "en": [
        "if possible", "where possible", "when possible", "as appropriate", "as applicable",
        "if applicable", "as needed", "as required", "if necessary", "when necessary",
        "if needed", "to the extent possible", "if feasible", "where feasible",
        "as far as possible", "at least try", "should try",
    ],
    "tr": [
        "mümkünse", "mümkün olduğunca", "mümkün oldukça", "gerektiğinde", "gerekirse",
        "gerekli görülürse", "uygun görülürse", "ihtiyaç halinde", "ihtiyaç duyulursa",
        "imkan dahilinde", "imkân dahilinde", "duruma göre", "tercihen",
    ],
}
OPEN_ENDED = {
    "en": [
        "etc", "etc.", "and so on", "and so forth", "including but not limited to",
        "and/or", "such as", "among others", "or similar", "and similar",
    ],
    "tr": [
        "vb.", "vb", "v.b.", "vs.", "vs", "ve benzeri", "ve/veya", "bunlarla sınırlı olmamak",
        "ve diğer", "ve saire",
    ],
}
TBD = {
    "en": ["tbd", "tbc", "tba", "todo", "to be determined", "to be decided", "to be defined",
           "to be confirmed", "???", "xxx"],
    "tr": ["belirlenecek", "karar verilecek", "netleştirilecek", "sonra belirlenecek",
           "henüz belli değil", "tanımlanacak", "??"],
}
NEGATIVE = {
    "en": ["shall not", "must not", "should not", "will not", "never", "cannot", "can't"],
    "tr": ["asla", "hiçbir zaman", "hiçbir şekilde"],
}
UNIVERSAL = {
    "en": ["all", "every", "always", "any", "none", "everything"],
    "tr": ["tüm", "bütün", "her", "hep", "daima", "herhangi", "hiçbir", "her zaman", "tamamı"],
}
MEASURABLE_TOPICS = {
    "en": ["response time", "respond", "latency", "under load", "performance", "throughput",
           "concurrent users", "concurrent requests", "availability", "highly available", "high-availability", "uptime", "timeout", "time out", "time-out",
           "capacity", "scalab", "duration", "page load", "loading time", "load time"],
    "tr": ["yanıt süre", "cevap süre", "yanıt ver", "gecikme", "yük altında", "performans",
           "eşzamanlı kullanıcı", "eş zamanlı kullanıcı", "kesintisiz", "çalışma süre", "zaman aşımı",
           "kapasite", "ölçeklen", "işlem süre", "bekleme süre", "yükleme süre", "sayfa yüklen", "açılış süre"],
}
MODALS_EN = re.compile(r"\b(shall|must|will|should|is required to|has to|needs to)\b", re.I)
MODAL_TR = re.compile(r"\w+(?:m[aı]l[ıi]d[ıi]r|m[ea]l[iı]d[iı]r|m[aı]l[ıi]|m[ea]l[iı])\b|\bgerek(?:ir|mektedir|li)\b", re.I)
STORY_EN = re.compile(r"\bas an? .+?\bi (want|need|would like)\b", re.I | re.S)
STORY_TR = re.compile(r"\bolarak\b.+?\b(istiyorum|isterim|ihtiyacım var)\b", re.I | re.S)
BENEFIT_EN = re.compile(r"\bso that\b|\bin order to\b", re.I)
BENEFIT_TR = re.compile(r"\b(böylece|için|sayesinde|amacıyla)\b", re.I)
NUMBER = re.compile(r"\d")
TR_CHARS = set("çğıöşüÇĞİÖŞÜ")
TR_HINTS = {"ve", "bir", "ile", "için", "olarak", "kullanıcı", "sistem", "gerekir", "olmalı", "olmalıdır"}
# optional bullet, then an ID such as REQ-001, FR-12, NFR_3, US-4.2 followed by ":", ".", ")", "-" or just whitespace
ID_PREFIX = re.compile(r"^\s*(?:[-*•]|\d+[.)])?\s*(?:\[?\**([A-Z]{1,6}[-_]?\d{1,5}(?:\.\d+)*)\**\]?(?:\s*[:.)\-–]\s*|\s+))?(.*)$")

SEVERITY_WEIGHT = {"critical": 25, "major": 10, "minor": 3, "info": 0}

MESSAGES = {
    "VAGUE": {
        "sev": "major",
        "en": "Vague or subjective term '{m}': it cannot be verified. Replace it with a measurable criterion (number + unit + condition).",
        "tr": "Belirsiz/öznel ifade '{m}': doğrulanamaz. Ölçülebilir bir kriterle (sayı + birim + koşul) değiştirin.",
    },
    "LOOPHOLE": {
        "sev": "major",
        "en": "Escape clause '{m}': it makes the obligation optional. State exactly when it applies.",
        "tr": "Kaçamak ifade '{m}': yükümlülüğü isteğe bağlı hale getiriyor. Ne zaman geçerli olduğunu açıkça belirtin.",
    },
    "OPEN_ENDED": {
        "sev": "major",
        "en": "Open-ended list '{m}': test scope cannot be closed. List every item explicitly.",
        "tr": "Açık uçlu liste '{m}': test kapsamı kapatılamaz. Tüm öğeleri açıkça listeleyin.",
    },
    "TBD": {
        "sev": "critical",
        "en": "Unresolved placeholder '{m}': the requirement is incomplete and not test-ready.",
        "tr": "Çözülmemiş yer tutucu '{m}': gereksinim eksik ve teste hazır değil.",
    },
    "NEGATIVE": {
        "sev": "minor",
        "en": "Negative statement '{m}': negative requirements are hard to verify exhaustively. Check whether a positive, bounded form exists.",
        "tr": "Olumsuz ifade '{m}': olumsuz gereksinimler tam olarak doğrulanamaz. Olumlu ve sınırlı bir ifade biçimi olup olmadığını kontrol edin.",
    },
    "UNIVERSAL": {
        "sev": "info",
        "en": "Universal quantifier '{m}': confirm the set is really unbounded. Tests need the concrete population (which users, screens or records).",
        "tr": "Evrensel niceleyici '{m}': kümenin gerçekten sınırsız olduğunu teyit edin. Testler somut kapsamı (hangi kullanıcılar, ekranlar, kayıtlar) gerektirir.",
    },
    "UNMEASURED": {
        "sev": "major",
        "en": "Performance/time/capacity topic ('{m}') without a number: add a threshold, unit, load level and percentile.",
        "tr": "Performans/süre/kapasite konusu ('{m}') sayı içermiyor: eşik, birim, yük seviyesi ve yüzdelik ekleyin.",
    },
    "COMPOUND": {
        "sev": "major",
        "en": "Compound requirement ({m} obligations): split it into atomic requirements so each can pass or fail on its own.",
        "tr": "Birleşik gereksinim ({m} yükümlülük): her biri bağımsız olarak geçip kalabilsin diye atomik gereksinimlere bölün.",
    },
    "NO_MODAL": {
        "sev": "info",
        "en": "No obligation verb (shall/must): confirm whether this is a requirement, a note or a design idea.",
        "tr": "Zorunluluk bildiren fiil yok (-malı/-meli): bunun bir gereksinim mi, not mu, tasarım fikri mi olduğunu teyit edin.",
    },
    "STORY_NO_AC": {
        "sev": "major",
        "en": "User story without acceptance criteria: define Given/When/Then or rule-based criteria before designing tests.",
        "tr": "Kabul kriteri olmayan kullanıcı hikâyesi: testleri tasarlamadan önce Diyelim ki/Eğer ki/O zaman veya kural tabanlı kriterler tanımlayın.",
    },
    "STORY_NO_BENEFIT": {
        "sev": "minor",
        "en": "User story without a benefit clause ('so that …'): the value is unclear, which weakens prioritisation and risk rating.",
        "tr": "Fayda cümlesi olmayan kullanıcı hikâyesi ('… böylece'): değer belirsiz, önceliklendirme ve risk değerlendirmesi zayıflar.",
    },
    "TOO_LONG": {
        "sev": "minor",
        "en": "Long statement ({m} words): likely more than one requirement or embedded rationale. Consider splitting.",
        "tr": "Uzun ifade ({m} kelime): muhtemelen birden fazla gereksinim veya gömülü gerekçe içeriyor. Bölmeyi düşünün.",
    },
    "PRONOUN": {
        "sev": "minor",
        "en": "Starts with a pronoun ('{m}'): the subject is ambiguous when the requirement is read alone. Name the actor or system.",
        "tr": "Zamirle başlıyor ('{m}'): gereksinim tek başına okunduğunda özne belirsiz. Aktörü/sistemi adıyla belirtin.",
    },
    "DUPLICATE": {
        "sev": "major",
        "en": "Near-duplicate of {m}: merge them or make the difference explicit.",
        "tr": "{m} ile neredeyse aynı: birleştirin veya farkı açıkça belirtin.",
    },
    "ID_MISSING": {
        "sev": "critical",
        "en": "Requirement has no ID (auto-assigned {m}): traceability needs stable IDs.",
        "tr": "Gereksinimin kimliği yok (otomatik atandı: {m}): izlenebilirlik için kalıcı kimlikler gerekir.",
    },
    "ID_DUPLICATE": {
        "sev": "critical",
        "en": "Duplicate ID '{m}': every requirement needs a unique ID.",
        "tr": "Yinelenen kimlik '{m}': her gereksinimin benzersiz bir kimliği olmalıdır.",
    },
}


def tr_lower(s: str) -> str:
    return s.replace("I", "ı").replace("İ", "i").lower()


def detect_lang(text: str) -> str:
    if any(c in TR_CHARS for c in text):
        return "tr"
    words = set(re.findall(r"\w+", text.lower()))
    return "tr" if len(words & TR_HINTS) >= 2 else "en"


def term_regex(term: str) -> re.Pattern:
    suffix = term.endswith("*")
    core = re.escape(term.rstrip("*"))
    core = core.replace(r"\ ", r"\s+")
    tail = r"\w*" if suffix else ""
    # word boundaries that also work for punctuation-terminated terms (etc., vb.)
    return re.compile(rf"(?<![\w]){core}{tail}(?![\w])", re.I)


COMPILED: dict[str, dict[str, list[tuple[str, re.Pattern]]]] = {}
for _rule, _table in {
    "VAGUE": VAGUE, "LOOPHOLE": LOOPHOLE, "OPEN_ENDED": OPEN_ENDED, "TBD": TBD,
    "NEGATIVE": NEGATIVE, "UNIVERSAL": UNIVERSAL,
}.items():
    COMPILED[_rule] = {lang: [(t, term_regex(t)) for t in terms] for lang, terms in _table.items()}


# technical phrases that contain listed words but are not vague ("büyük/küçük harf" = letter case)
NOT_VAGUE = [re.compile(p, re.I) for p in (
    r"büyük\s*/?\s*küçük\s+harf\w*", r"(?:büyük|küçük)\s+harf\w*", r"upper\s*/?\s*lower\s*case",
    r"(?:upper|lower)\s*case", r"case[- ]insensitive", r"case[- ]sensitive", r"small\s+business",
)]


def mask(low: str) -> str:
    for rx in NOT_VAGUE:
        low = rx.sub(lambda m: " " * len(m.group(0)), low)
    return low


def find_terms(rule: str, text: str, lang: str) -> list[str]:
    hits: list[str] = []
    low = tr_lower(text) if lang == "tr" else text.lower()
    if rule == "VAGUE":
        low = mask(low)
    covered: list[tuple[int, int]] = []
    # longest terms first so "en kısa sürede" wins over "kısa"
    for term, rx in sorted(COMPILED[rule][lang], key=lambda x: -len(x[0])):
        for m in rx.finditer(low):
            span = m.span()
            if any(a <= span[0] < b or a < span[1] <= b for a, b in covered):
                continue
            covered.append(span)
            # lower() can change string length for rare characters; fall back to the lowered text
            src = text if len(low) == len(text) else low
            hits.append(src[span[0]:span[1]])
    return hits


def tokens(text: str) -> set[str]:
    return set(re.findall(r"\w{3,}", tr_lower(text)))


def lint_one(req: dict, lang: str) -> list[dict]:
    text = req.get("text", "")
    findings: list[dict] = []

    def add(rule: str, match: str):
        findings.append({"rule": rule, "severity": MESSAGES[rule]["sev"], "match": match})

    for rule in ("TBD", "VAGUE", "LOOPHOLE", "OPEN_ENDED", "NEGATIVE", "UNIVERSAL"):
        for hit in find_terms(rule, text, lang):
            add(rule, hit)
    if lang == "tr":
        for w in re.findall(r"\w+(?:mamalı|memeli)\w*", tr_lower(text)):
            add("NEGATIVE", w)

    low = tr_lower(text) if lang == "tr" else text.lower()
    if not NUMBER.search(text):
        for topic in MEASURABLE_TOPICS[lang]:
            if re.search(rf"(?<!\w){re.escape(topic)}", low):
                add("UNMEASURED", topic)
                break

    is_story = bool((STORY_EN if lang == "en" else STORY_TR).search(text))
    if is_story:
        if not req.get("acceptance_criteria"):
            add("STORY_NO_AC", "")
        if not (BENEFIT_EN if lang == "en" else BENEFIT_TR).search(text):
            add("STORY_NO_BENEFIT", "")
    else:
        modals = MODALS_EN.findall(text) if lang == "en" else MODAL_TR.findall(text)
        # "shall reject X and display message Y" is one observable response, not two obligations
        message_pair = len(modals) == 2 and re.search(r"mesaj|göster|uyarı|message|display|show|notify|bildir", low)
        if len(modals) >= 3 or (len(modals) == 2 and not message_pair):
            add("COMPOUND", str(len(modals)))
        elif not modals and lang == "en":
            add("NO_MODAL", "")

    words = len(re.findall(r"\w+", text))
    if words > 60:
        add("TOO_LONG", str(words))

    # Turkish demonstratives ("Bu ekranda ...") are too common to flag reliably.
    first = re.findall(r"^\W*(\w+)", low)
    if lang == "en" and first and first[0] in {"it", "this", "that", "they", "these", "those", "its"}:
        add("PRONOUN", first[0])
    return findings


def load(path: Path) -> tuple[list[dict], str | None]:
    raw = path.read_text(encoding="utf-8-sig")
    if path.suffix.lower() == ".json":
        data = json.loads(raw)
        reqs = data["requirements"] if isinstance(data, dict) else data
        return reqs, (data.get("language") if isinstance(data, dict) else None)
    return load_text(raw)


def load_text(raw: str) -> tuple[list[dict], str | None]:
    """Parse plain text / Markdown: one requirement per line or bullet, optional leading ID."""
    reqs = []
    for line in raw.splitlines():
        if not line.strip() or line.lstrip().startswith("#") or set(line.strip()) <= set("-=|: "):
            continue
        m = ID_PREFIX.match(line)
        rid, body = (m.group(1), m.group(2)) if m else (None, line.strip())
        body = body.strip()
        if len(body) < 3:
            continue
        reqs.append({"id": rid, "text": body})
    return reqs, None


def run(reqs: list[dict], lang_opt: str | None) -> dict:
    results = []
    seen: dict[str, int] = {}
    auto = 0
    for r in reqs:
        text = r.get("text") or r.get("title") or ""
        lang = lang_opt or detect_lang(text)
        f = lint_one({**r, "text": text}, lang)
        rid = r.get("id")
        if not rid:
            auto += 1
            rid = f"AUTO-{auto:03d}"
            f.insert(0, {"rule": "ID_MISSING", "severity": "critical", "match": rid})
        if rid in seen:
            f.insert(0, {"rule": "ID_DUPLICATE", "severity": "critical", "match": rid})
        seen[rid] = seen.get(rid, 0) + 1
        results.append({"id": rid, "text": text, "lang": lang, "findings": f})

    # near-duplicates (Jaccard on content tokens)
    toks = [tokens(r["text"]) for r in results]
    for i in range(len(results)):
        for j in range(i + 1, len(results)):
            a, b = toks[i], toks[j]
            if len(a) >= 4 and len(b) >= 4 and len(a & b) / len(a | b) >= 0.8:
                results[j]["findings"].append({"rule": "DUPLICATE", "severity": "major", "match": results[i]["id"]})

    for r in results:
        for f in r["findings"]:
            f["message"] = MESSAGES[f["rule"]][r["lang"]].format(m=f["match"])
        penalty = sum(SEVERITY_WEIGHT[f["severity"]] for f in r["findings"])
        r["lint_score"] = max(0, 100 - penalty)

    summary: dict = {"requirements": len(results), "by_severity": {}, "by_rule": {}}
    for r in results:
        for f in r["findings"]:
            summary["by_severity"][f["severity"]] = summary["by_severity"].get(f["severity"], 0) + 1
            summary["by_rule"][f["rule"]] = summary["by_rule"].get(f["rule"], 0) + 1
    summary["clean"] = sum(1 for r in results if not [f for f in r["findings"] if f["severity"] != "info"])
    summary["average_lint_score"] = round(sum(r["lint_score"] for r in results) / max(1, len(results)), 1)
    return {"summary": summary, "results": results}


def to_markdown(rep: dict, lang: str) -> str:
    tr = lang == "tr"
    s = rep["summary"]
    out = ["# " + ("Gereksinim Lint Raporu (sezgisel)" if tr else "Requirements Lint Report (heuristic)"), ""]
    out.append(("> Bu bulgular adaydır; her birini bağlam içinde doğrulayın veya reddedin."
                if tr else "> Findings are candidates; confirm or dismiss each one in context."))
    out.append("")
    out.append(f"- {'Gereksinim sayısı' if tr else 'Requirements'}: {s['requirements']}")
    out.append(f"- {'Temiz (info hariç bulgu yok)' if tr else 'Clean (no findings except info)'}: {s['clean']}")
    out.append(f"- {'Ortalama lint puanı' if tr else 'Average lint score'}: {s['average_lint_score']}/100")
    sev = ", ".join(f"{k}: {v}" for k, v in sorted(s["by_severity"].items(), key=lambda kv: -SEVERITY_WEIGHT[kv[0]]))
    out.append(f"- {'Önem derecesine göre' if tr else 'By severity'}: {sev or '-'}")
    rules = ", ".join(f"{k}: {v}" for k, v in sorted(s["by_rule"].items(), key=lambda kv: -kv[1]))
    out.append(f"- {'Kurala göre' if tr else 'By rule'}: {rules or '-'}")
    out.append("")
    hdr = ("| ID | Puan | Önem | Kural | Eşleşme | Açıklama |" if tr else "| ID | Score | Severity | Rule | Match | Message |")
    out += [hdr, "|---|---|---|---|---|---|"]
    order = {"critical": 0, "major": 1, "minor": 2, "info": 3}
    for r in sorted(rep["results"], key=lambda r: r["lint_score"]):
        if not r["findings"]:
            out.append(f"| {r['id']} | {r['lint_score']} | - | - | - | {'bulgu yok' if tr else 'no findings'} |")
            continue
        for f in sorted(r["findings"], key=lambda f: order[f["severity"]]):
            msg = f["message"].replace("|", "\\|")
            match = str(f["match"]).replace("|", "\\|")
            out.append(f"| {r['id']} | {r['lint_score']} | {f['severity']} | {f['rule']} | {match} | {msg} |")
    return "\n".join(out) + "\n"



def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", help="requirements.json or .txt/.md file")
    ap.add_argument("--lang", choices=["en", "tr"], help="force language (default: detect per requirement)")
    ap.add_argument("--format", choices=["md", "json"], default="md")
    ap.add_argument("--out", help="write to file instead of stdout")
    a = ap.parse_args()
    try:
        reqs, file_lang = load(Path(a.input))
    except (OSError, ValueError, KeyError) as e:
        print(f"error: cannot read {a.input}: {e}", file=sys.stderr)
        return 2
    rep = run(reqs, a.lang)
    report_lang = a.lang or file_lang or (
        "tr" if sum(1 for r in rep["results"] if r["lang"] == "tr") * 2 >= len(rep["results"]) else "en")
    text = json.dumps(rep, ensure_ascii=False, indent=2) if a.format == "json" else to_markdown(rep, report_lang)
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(text, encoding="utf-8")
        print(f"wrote {a.out}")
    else:
        sys.stdout.reconfigure(encoding="utf-8")
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
