#!/usr/bin/env python3
"""List the test data each test case needs, from qa/test-cases.json, as a data-requirements table.

For every test case it reads `test_data` (and the `data` of its steps) and classifies the need:
  exact     the value itself is the test (boundary values, partitions, decision-table rules,
            states) -> put it in a fixed, reviewed fixture; never randomise it
  any-valid the test needs *a* valid record of that shape -> generate it (gen_data.py)
It also flags test data that looks like real personal data (e-mails outside example.* domains,
checksum-valid TCKNs or IBANs, mobile numbers) and test cases that document no data at all.
With --schema-out it writes a starter gen_data.py schema inferred from the observed values.

Usage:
  python data_needs.py qa/test-cases.json --out qa/test-data/data-needs.md --lang tr \
      [--schema-out qa/test-data/schema.json]
Exit codes: 0 ok, 1 possible real personal data found in test cases, 2 usage error.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gen_data as gd  # noqa: E402

EXACT = {"boundary-value-analysis", "equivalence-partitioning", "decision-table", "state-transition",
         "pairwise", "classification-tree"}
EMAIL_RE = re.compile(r"[\w.+-]+@([\w-]+\.)+[A-Za-z]{2,}")
PHONE_RE = re.compile(r"(?<![\d\w])(\+?90|0)?\s*\(?5\d{2}\)?[\s-]*\d{3}[\s-]*\d{2}[\s-]*\d{2}(?!\d)")
T = {"en": {"title": "Test data needs", "per_tc": "Per test case", "items": "Data items", "warn": "Warnings",
            "tc": "TC", "tech": "Technique", "data": "Data", "kind": "Need", "key": "Item", "vals": "Values (TCs)",
            "type": "Inferred type", "exact": "exact (fixture)", "any": "any valid (generate)",
            "none": "None.", "nodata": "{tc}: no test data documented - add `test_data` or step data",
            "email": "{tc}: '{v}' is an e-mail outside example.com/example.test - use a reserved domain",
            "tckn": "{tc}: '{v}' is a checksum-valid TCKN - confirm it is synthetic",
            "iban": "{tc}: '{v}' is a valid IBAN - confirm it is synthetic",
            "phone": "{tc}: '{v}' looks like a real mobile number - confirm it is synthetic and never messaged",
            "hint": "Exact values go to a reviewed fixture file; 'any valid' needs can be generated."},
     "tr": {"title": "Test verisi ihtiyaçları", "per_tc": "Test senaryosu bazında", "items": "Veri kalemleri",
            "warn": "Uyarılar", "tc": "TC", "tech": "Teknik", "data": "Veri", "kind": "İhtiyaç", "key": "Kalem",
            "vals": "Değerler (TC)", "type": "Çıkarılan tip", "exact": "birebir (fixture)",
            "any": "herhangi geçerli (üret)", "none": "Yok.",
            "nodata": "{tc}: test verisi belgelenmemiş - `test_data` veya adım verisi ekleyin",
            "email": "{tc}: '{v}' example.com/example.test dışında bir e-posta - ayrılmış alan adı kullanın",
            "tckn": "{tc}: '{v}' checksum'ı geçerli bir TCKN - sentetik olduğunu teyit edin",
            "iban": "{tc}: '{v}' geçerli bir IBAN - sentetik olduğunu teyit edin",
            "phone": "{tc}: '{v}' gerçek bir cep numarasına benziyor - sentetik olduğunu ve mesaj atılmadığını "
                     "teyit edin",
            "hint": "Birebir değerler gözden geçirilmiş bir fixture dosyasına; 'herhangi geçerli' ihtiyaçlar "
                    "üretilebilir."}}


def pii_warnings(tc: str, value: str, t: dict) -> list[str]:
    out = []
    for m in EMAIL_RE.finditer(value):
        dom = m.group(0).split("@", 1)[1].lower()
        if dom not in gd.EMAIL_DOMAINS and not dom.endswith((".example.com", ".example.test")):
            out.append(t["email"].format(tc=tc, v=m.group(0)))
    for tok in re.findall(r"\b\d{11}\b", value):
        if gd.is_valid_tckn(tok):
            out.append(t["tckn"].format(tc=tc, v=tok))
    for tok in re.findall(r"\bTR\d{2}(?:\s?\d{4}){5}\s?\d{2}\b", value):
        if gd.is_valid_iban(tok):
            out.append(t["iban"].format(tc=tc, v=tok))
    for m in PHONE_RE.finditer(value):
        if len(re.sub(r"\D", "", m.group(0))) >= 10:
            out.append(t["phone"].format(tc=tc, v=m.group(0).strip()))
    return out


def infer_field(name: str, values: list[str]) -> dict:
    vals = [v.strip() for v in values if v.strip()]
    field = {"name": re.sub(r"\W+", "_", name.translate(gd.FOLD).lower()).strip("_") or "field"}
    nums = [re.sub(r"\s*(TL|TRY|USD|EUR|₺|\$|€)\s*", "", v) for v in vals]
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
    if vals and all(gd.is_valid_tckn(v) for v in vals):
        return {**field, "type": "tckn"}
    if vals and all(gd.is_valid_iban(v) for v in vals):
        return {**field, "type": "iban_tr"}
    distinct = sorted(set(vals))
    if distinct and len(distinct) <= 12:
        return {**field, "type": "enum", "values": distinct}
    return {**field, "type": "text", "min_len": 0, "max_len": max((len(v) for v in vals), default=20)}


def analyse(doc: dict, lang: str = "en") -> tuple[str, dict, list[str]]:
    t = T[lang]
    rows, items, warns, pii = [], {}, [], []
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
            pii += pii_warnings(tid, v, t)
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
    pii = list(dict.fromkeys(pii))
    lines += ["", f"## {t['warn']}", ""] + ([f"- {w}" for w in pii + warns] or [t["none"]]) + [""]
    schema = {"description": "Starter schema inferred by data_needs.py - review types, ranges and add edge/unique.",
              "fields": [{"name": "id", "type": "seq", "prefix": "TD-{run}", "width": 4}] + fields,
              "unique": ["id"]}
    return "\n".join(lines), schema, pii


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
    report, schema, pii = analyse(doc, a.lang)
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
    for w in pii:
        print(f"WARN  {w}")
    return 1 if pii else 0


if __name__ == "__main__":
    sys.exit(main())
