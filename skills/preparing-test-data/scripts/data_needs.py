#!/usr/bin/env python3
"""List the test data each test case needs, from qa/test-cases.json, as a data-requirements table.

For every test case it reads `test_data` (and the `data` of its steps) and classifies the need:
  exact     the value itself is the test (boundary values, partitions, decision-table rules,
            states) -> put it in a fixed, reviewed fixture; never randomise it
  any-valid the test needs *a* valid record of that shape -> generate it (gen_data.py)
It also checks the test data against the suite's ID policy and lists test cases that document
no data at all:
  ERROR    clearly real-looking personal data: e-mail addresses outside the reserved example
           domains (example.com/.net/.org and the .test/.example/.invalid/.localhost TLDs,
           RFC 2606 / RFC 6761). Exit code 1.
  WARNING  "verify synthetic origin": checksum-valid TCKNs and IBANs and mobile numbers. The suite
           generates such values itself (gen_data.py, check_ids.py --generate), and they are
           allowed in TEST environments when they come from the generator. Because they can
           coincide with real people, confirm where each one came from and never use them in
           production or shared systems. Warnings alone do not change the exit code.
With --schema-out it writes a starter gen_data.py schema inferred from the observed values.

Usage:
  python data_needs.py qa/test-cases.json --out qa/test-data/data-needs.md --lang tr \
      [--schema-out qa/test-data/schema.json]
Exit codes: 0 ok (warnings possible), 1 real-looking personal data found in test cases, 2 usage error.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gen_data as gd  # noqa: E402
from tr_ids import is_valid_iban, is_valid_tckn  # noqa: E402

# Reserved for documentation and testing (RFC 2606, RFC 6761): no real mailbox can exist there.
RESERVED_EMAIL_DOMAINS = ("example.com", "example.net", "example.org")
RESERVED_EMAIL_TLDS = ("test", "example", "invalid", "localhost")

EXACT = {"boundary-value-analysis", "equivalence-partitioning", "decision-table", "state-transition",
         "pairwise", "classification-tree"}
EMAIL_RE = re.compile(r"[\w.+-]+@([\w-]+\.)+[A-Za-z]{2,}")
PHONE_RE = re.compile(r"(?<![\d\w])(\+?90|0)?\s*\(?5\d{2}\)?[\s-]*\d{3}[\s-]*\d{2}[\s-]*\d{2}(?!\d)")
T = {"en": {"title": "Test data needs", "per_tc": "Per test case", "items": "Data items", "warn": "Warnings",
            "tc": "TC", "tech": "Technique", "data": "Data", "kind": "Need", "key": "Item", "vals": "Values (TCs)",
            "type": "Inferred type", "exact": "exact (fixture)", "any": "any valid (generate)",
            "none": "None.", "nodata": "{tc}: no test data documented - add `test_data` or step data",
            "email": "{tc}: '{v}' is an e-mail outside the reserved example domains - looks like real personal "
                     "data; use example.com or example.test",
            "tckn": "{tc}: '{v}' is a checksum-valid TCKN - verify synthetic origin (generator output, test "
                    "environments only)",
            "iban": "{tc}: '{v}' is a valid IBAN - verify synthetic origin (generator output, test environments "
                    "only)",
            "phone": "{tc}: '{v}' looks like a mobile number - verify synthetic origin and never message it",
            "error": "ERROR", "warning": "WARNING",
            "hint": "Exact values go to a reviewed fixture file; 'any valid' needs can be generated. "
                    "ERROR = looks like real personal data (exit code 1); WARNING = allowed in test environments "
                    "when generated, verify synthetic origin."},
     "tr": {"title": "Test verisi ihtiyaçları", "per_tc": "Test senaryosu bazında", "items": "Veri kalemleri",
            "warn": "Uyarılar", "tc": "TC", "tech": "Teknik", "data": "Veri", "kind": "İhtiyaç", "key": "Kalem",
            "vals": "Değerler (TC)", "type": "Çıkarılan tip", "exact": "birebir (fixture)",
            "any": "herhangi geçerli (üret)", "none": "Yok.",
            "nodata": "{tc}: test verisi belgelenmemiş - `test_data` veya adım verisi ekleyin",
            "email": "{tc}: '{v}' ayrılmış örnek alan adları dışında bir e-posta - gerçek kişisel veriye "
                     "benziyor; example.com veya example.test kullanın",
            "tckn": "{tc}: '{v}' checksum'ı geçerli bir TCKN - sentetik kaynağını doğrulayın (üretici çıktısı, "
                    "yalnızca test ortamları)",
            "iban": "{tc}: '{v}' geçerli bir IBAN - sentetik kaynağını doğrulayın (üretici çıktısı, yalnızca test "
                    "ortamları)",
            "phone": "{tc}: '{v}' bir cep numarasına benziyor - sentetik kaynağını doğrulayın, asla mesaj atmayın",
            "error": "HATA", "warning": "UYARI",
            "hint": "Birebir değerler gözden geçirilmiş bir fixture dosyasına; 'herhangi geçerli' ihtiyaçlar "
                    "üretilebilir. HATA = gerçek kişisel veriye benziyor (çıkış kodu 1); UYARI = üretilmişse test "
                    "ortamlarında serbest, sentetik kaynağını doğrulayın."}}


def reserved_email_domain(domain: str) -> bool:
    """True for the documentation/test domains of RFC 2606 / RFC 6761 (and their subdomains)."""
    d = domain.lower().rstrip(".")
    return (d in RESERVED_EMAIL_DOMAINS or d.endswith(tuple("." + r for r in RESERVED_EMAIL_DOMAINS))
            or d.rsplit(".", 1)[-1] in RESERVED_EMAIL_TLDS)


def pii_findings(tc: str, value: str, t: dict) -> tuple[list[str], list[str]]:
    """(errors, warnings) for one test data value, following the ID policy.

    errors:   clearly real-looking personal data (e-mail outside the reserved example domains).
    warnings: checksum-valid TCKN / IBAN and mobile numbers - allowed in test environments when they
              come from the generator, so the tester must verify their synthetic origin.
    """
    errors, warnings = [], []
    for m in EMAIL_RE.finditer(value):
        if not reserved_email_domain(m.group(0).split("@", 1)[1]):
            errors.append(t["email"].format(tc=tc, v=m.group(0)))
    for tok in re.findall(r"\b\d{11}\b", value):
        if is_valid_tckn(tok):
            warnings.append(t["tckn"].format(tc=tc, v=tok))
    for tok in re.findall(r"\bTR\d{2}(?:\s?\d{4}){5}\s?\d{2}\b", value):
        if is_valid_iban(tok):
            warnings.append(t["iban"].format(tc=tc, v=tok))
    for m in PHONE_RE.finditer(value):
        if len(re.sub(r"\D", "", m.group(0))) >= 10:
            warnings.append(t["phone"].format(tc=tc, v=m.group(0).strip()))
    return errors, warnings


def infer_field(name: str, values: list[str]) -> dict:
    vals = [v.strip() for v in values if v.strip()]
    field = {"name": re.sub(r"\W+", "_", name.translate(gd.FOLD).lower()).strip("_") or "field"}
    nums = [re.sub(r"\s*(TL|TRY|USD|EUR|₺|\$|€)\s*", "", v) for v in vals]
    # identifiers before plain numbers: a TCKN column must be generated as TCKNs, not as random ints
    if vals and all(is_valid_tckn(v) for v in vals):
        return {**field, "type": "tckn"}
    if vals and all(is_valid_iban(v) for v in vals):
        return {**field, "type": "iban_tr"}
    if vals and all(re.fullmatch(r"-?\d+", n) for n in nums):
        ints = [int(n) for n in nums]
        return {**field, "type": "int", "min": min(ints), "max": max(ints)}
    if vals and all(re.fullmatch(r"-?\d+([.,]\d+)?", n) for n in nums):
        sep = "," if any("," in n for n in nums) else "."
        ds = [float(n.replace(",", ".")) for n in nums]
        scale = max(len(re.split(r"[.,]", n)[1]) if re.search(r"[.,]", n) else 0 for n in nums)
        return {**field, "type": "decimal", "min": min(ds), "max": max(ds), "scale": scale, "decimal_sep": sep}
    if vals and all(EMAIL_RE.fullmatch(v) for v in vals):
        return {**field, "type": "email"}
    if vals and all(re.fullmatch(r"\d{2}\.\d{2}\.\d{4}", v) for v in vals):
        iso = sorted(f"{v[6:]}-{v[3:5]}-{v[:2]}" for v in vals)
        return {**field, "type": "date", "min": iso[0], "max": iso[-1], "format": "%d.%m.%Y"}
    if vals and all(re.fullmatch(r"\d{4}-\d{2}-\d{2}", v) for v in vals):
        return {**field, "type": "date", "min": min(vals), "max": max(vals)}
    distinct = sorted(set(vals))
    if distinct and len(distinct) <= 12:
        return {**field, "type": "enum", "values": distinct}
    return {**field, "type": "text", "min_len": 0, "max_len": max((len(v) for v in vals), default=20)}


def analyse(doc: dict, lang: str = "en") -> tuple[str, dict, list[str]]:
    """(report, starter schema, errors): errors = real-looking personal data (exit code 1)."""
    report, schema, errors, _ = analyse_full(doc, lang)
    return report, schema, errors


def analyse_full(doc: dict, lang: str = "en") -> tuple[str, dict, list[str], list[str]]:
    """(report, starter schema, errors, verify-synthetic-origin warnings)."""
    t = T[lang]
    rows, items, warns, pii, verify = [], {}, [], [], []
    for tc in doc.get("test_cases", []):
        if tc.get("status") == "deprecated":
            continue
        tid, tech = tc.get("id", "?"), tc.get("technique", "")
        data = {str(k): str(v) for k, v in (tc.get("test_data") or {}).items()}
        step_data = [str(s.get("data")) for s in tc.get("steps", []) if s.get("data")]
        if not data and not step_data:
            warns.append(t["nodata"].format(tc=tid))
        for k, v in data.items():
            items.setdefault(k, {}).setdefault(v, []).append(tid)
        for v in list(data.values()) + step_data:
            errs, wrns = pii_findings(tid, v, t)
            pii += errs
            verify += wrns
        shown = "; ".join(f"{k}={v}" for k, v in data.items()) or "; ".join(step_data)
        kind = t["exact"] if tech in EXACT else t["any"]
        rows.append(f"| {tid} | {tech} | {shown.replace('|', '/')} | {kind} |")
    fields = [infer_field(k, list(vs)) for k, vs in items.items()]
    lines = [f"# {t['title']}", "", t["hint"], "", f"## {t['per_tc']}", "",
             f"| {t['tc']} | {t['tech']} | {t['data']} | {t['kind']} |", "|---|---|---|---|", *rows, "",
             f"## {t['items']}", "", f"| {t['key']} | {t['vals']} | {t['type']} |", "|---|---|---|"]
    for (k, vs), f in zip(items.items(), fields):
        shown = "; ".join(f"{v} ({', '.join(ids)})" for v, ids in vs.items())
        lines.append(f"| {k} | {shown.replace('|', '/')} | {f['type']} |")
    pii, verify = list(dict.fromkeys(pii)), list(dict.fromkeys(verify))
    found = [f"- {t['error']} {w}" for w in pii] + [f"- {t['warning']} {w}" for w in verify] + [f"- {w}" for w in warns]
    lines += ["", f"## {t['warn']}", ""] + (found or [t["none"]]) + [""]
    schema = {"description": "Starter schema inferred by data_needs.py - review types, ranges and add edge/unique.",
              "fields": [{"name": "id", "type": "seq", "prefix": "TD-{run}", "width": 4}] + fields,
              "unique": ["id"]}
    return "\n".join(lines), schema, pii, verify


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("tests", help="qa/test-cases.json")
    ap.add_argument("--out", help="Markdown report (default: print)")
    ap.add_argument("--schema-out", dest="schema_out", help="starter schema for gen_data.py")
    ap.add_argument("--lang", choices=["tr", "en"], default="en")
    sys.stdout.reconfigure(encoding="utf-8")
    a = ap.parse_args()
    try:
        doc = json.loads(Path(a.tests).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as e:
        print(f"error: cannot read {a.tests}: {e}", file=sys.stderr)
        return 2
    report, schema, pii, verify = analyse_full(doc, a.lang)
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(report, encoding="utf-8", newline="\n")
        print(f"data needs -> {a.out}")
    else:
        print(report)
    if a.schema_out:
        Path(a.schema_out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.schema_out).write_text(json.dumps(schema, ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
                                      newline="\n")
        print(f"starter schema -> {a.schema_out}")
    t = T[a.lang]
    for w in pii:
        print(f"{t['error']}  {w}")
    for w in verify:
        print(f"{t['warning']}  {w}")
    return 1 if pii else 0


if __name__ == "__main__":
    sys.exit(main())
