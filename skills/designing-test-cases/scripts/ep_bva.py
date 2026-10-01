#!/usr/bin/env python3
"""Equivalence partitioning + boundary value analysis (2-value / 3-value).

Computes partitions, boundary values and single-fault test conditions from a
JSON spec, and reports gaps/overlaps/open ends in the specified ranges -
those are requirement defects worth a clarification question.

Spec (JSON):
{
  "id": "DS-001", "title": "Loan application inputs", "requirement_ids": ["REQ-003"],
  "bva": "3-value",                      # or "2-value" (default)
  "parameters": [
    {"name": "age", "type": "integer", "min": 18, "max": 65},
    {"name": "amount", "type": "decimal", "step": "0.01", "min": "1000.00", "max": "50000.00"},
    {"name": "username", "type": "length", "min": 3, "max": 20},
    {"name": "start_date", "type": "date", "min": "2026-01-01", "max": "2026-12-31"},
    {"name": "score", "type": "integer", "partitions": [
        {"label": "reject", "min": 0, "max": 499, "valid": true},
        {"label": "manual review", "min": 500, "max": 699, "valid": true},
        {"label": "auto approve", "min": 700, "max": 1000, "valid": true}]},
    {"name": "currency", "type": "enum", "valid": ["TRY", "EUR"], "invalid": ["USD", ""],
     "each_value": true},
    {"name": "age", ..., "extra_invalid": ["empty", "non-numeric 'abc'", "decimal 18.5"]}
  ]
}
Types: integer | decimal | length | date | enum. A partition may set
"representative". Parameters may set "domain_min"/"domain_max" (e.g. data type
limits) to add extreme-value probes.

Usage:
  python ep_bva.py qa/design/DS-001.json                 # markdown to stdout
  python ep_bva.py spec.json --format json --out out.json
  python ep_bva.py spec.json --lang tr
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from decimal import Decimal
from pathlib import Path

T = {
    "en": {
        "title": "EP/BVA design", "partitions": "Equivalence partitions", "param": "Parameter",
        "part": "Partition", "range": "Range", "valid": "Valid", "rep": "Representative",
        "bounds": "Boundary values", "value": "Value", "note": "Note", "warn": "Warnings (clarify)",
        "conds": "Test conditions (valid values may be combined; each invalid value is tested alone)",
        "id": "ID", "expected": "Expected", "valid_res": "valid (accepted)", "invalid_res": "invalid",
        "unspec": "unspecified", "yes": "yes", "no": "no", "q": "?", "base": "Nominal values",
        "gap": "Gap between '{a}' and '{b}': values {lo}..{hi} belong to no partition.",
        "overlap": "Overlap between '{a}' and '{b}': {lo}..{hi} is in both.",
        "open_hi": "'{p}' has no upper limit: what is the maximum (data type, UI, DB column)?",
        "open_lo": "'{p}' has no lower limit: what is the minimum?",
        "unspec_lo": "Values below {v} are not specified for '{p}' (treated as invalid).",
        "unspec_hi": "Values above {v} are not specified for '{p}' (treated as invalid).",
        "summary": "{n} partitions, {b} boundary values, {c} test conditions",
        "gap_label": "gap", "boundary_of": "boundary {a} ↔ {b}", "extreme": "type/domain extreme", "special": "special invalid class",
    },
    "tr": {
        "title": "DS/SDA tasarımı", "partitions": "Denklik sınıfları", "param": "Parametre",
        "part": "Sınıf", "range": "Aralık", "valid": "Geçerli", "rep": "Temsilci değer",
        "bounds": "Sınır değerleri", "value": "Değer", "note": "Not", "warn": "Uyarılar (netleştirilmeli)",
        "conds": "Test koşulları (geçerli değerler birleştirilebilir; her geçersiz değer tek başına test edilir)",
        "id": "ID", "expected": "Beklenen", "valid_res": "geçerli (kabul)", "invalid_res": "geçersiz",
        "unspec": "tanımsız", "yes": "evet", "no": "hayır", "q": "?", "base": "Nominal değerler",
        "gap": "'{a}' ile '{b}' arasında boşluk: {lo}..{hi} değerleri hiçbir sınıfa ait değil.",
        "overlap": "'{a}' ile '{b}' çakışıyor: {lo}..{hi} her ikisinde de var.",
        "open_hi": "'{p}' için üst sınır yok: azami değer nedir (veri tipi, arayüz, veritabanı kolonu)?",
        "open_lo": "'{p}' için alt sınır yok: asgari değer nedir?",
        "unspec_lo": "'{p}' için {v} altındaki değerler tanımlanmamış (geçersiz kabul edildi).",
        "unspec_hi": "'{p}' için {v} üstündeki değerler tanımlanmamış (geçersiz kabul edildi).",
        "summary": "{n} sınıf, {b} sınır değeri, {c} test koşulu",
        "gap_label": "boşluk", "boundary_of": "sınır {a} ↔ {b}", "extreme": "tip/alan uç değeri", "special": "özel geçersiz sınıf",
    },
}


class Scale:
    """Arithmetic helper per ordered type."""

    def __init__(self, ptype: str, step):
        self.ptype = ptype
        if ptype == "date":
            self.step = dt.timedelta(days=int(step or 1))
        elif ptype == "decimal":
            self.step = Decimal(str(step or "0.01"))
        else:
            self.step = int(step or 1)
        if self.step <= (dt.timedelta(0) if ptype == "date" else 0):
            raise ValueError(f"step must be greater than zero (got {step!r})")

    def parse(self, v):
        if v is None:
            return None
        if self.ptype == "date":
            return dt.date.fromisoformat(str(v))
        if self.ptype == "decimal":
            return Decimal(str(v))
        return int(v)

    def fmt(self, v) -> str:
        if v is None:
            return "∞"
        if self.ptype == "date":
            return v.isoformat()
        if self.ptype == "decimal":
            return str(v.quantize(self.step))
        return str(v)

    def mid(self, lo, hi):
        if self.ptype == "date":
            return lo + (hi - lo) // 2
        if self.ptype == "decimal":
            n = ((hi - lo) / self.step / 2).to_integral_value()
            return lo + n * self.step
        return lo + (hi - lo) // 2


def build_partitions(p: dict, sc: Scale, t: dict, warnings: list[str]) -> list[dict]:
    name = p["name"]
    if "partitions" in p:
        parts = []
        for q in p["partitions"]:
            parts.append({"label": q.get("label") or f"{q.get('min')}..{q.get('max')}",
                          "min": sc.parse(q.get("min")), "max": sc.parse(q.get("max")),
                          "valid": q.get("valid", True), "representative": q.get("representative")})
        parts.sort(key=lambda x: (x["min"] is not None, x["min"] if x["min"] is not None else 0))
        # implicit ends
        first, last = parts[0], parts[-1]
        floor = sc.parse(p.get("domain_min"))
        if p["type"] == "length" and floor is None:
            floor = 0
        if first["min"] is not None and (floor is None or first["min"] > floor):
            warnings.append(t["unspec_lo"].format(v=sc.fmt(first["min"]), p=name))
            parts.insert(0, {"label": f"< {sc.fmt(first['min'])} ({t['unspec']})", "min": floor,
                             "max": first["min"] - sc.step, "valid": None, "representative": None})
        if last["max"] is not None:
            warnings.append(t["unspec_hi"].format(v=sc.fmt(last["max"]), p=name))
            parts.append({"label": f"> {sc.fmt(last['max'])} ({t['unspec']})", "min": last["max"] + sc.step,
                          "max": sc.parse(p.get("domain_max")), "valid": None, "representative": None})
        else:
            warnings.append(t["open_hi"].format(p=name))
        # gaps become their own (unspecified) partition so they get boundary tests; overlaps are warned
        filled = [parts[0]]
        for a, b in zip(parts, parts[1:]):
            if a["max"] is not None and b["min"] is not None:
                expected = a["max"] + sc.step
                if b["min"] > expected:
                    lo, hi = expected, b["min"] - sc.step
                    warnings.append(t["gap"].format(a=a["label"], b=b["label"], lo=sc.fmt(lo), hi=sc.fmt(hi)))
                    filled.append({"label": f"{t['gap_label']} {sc.fmt(lo)}..{sc.fmt(hi)}", "min": lo, "max": hi,
                                   "valid": None, "representative": None})
                elif b["min"] < expected:
                    warnings.append(t["overlap"].format(a=a["label"], b=b["label"], lo=sc.fmt(b["min"]),
                                                        hi=sc.fmt(a["max"])))
            filled.append(b)
        return filled

    lo, hi = sc.parse(p.get("min")), sc.parse(p.get("max"))
    if lo is not None and hi is not None and lo > hi:
        raise ValueError(f"parameter '{name}': min {p.get('min')} is greater than max {p.get('max')}")
    floor = sc.parse(p.get("domain_min"))
    if p["type"] == "length" and floor is None:
        floor = 0
    parts = []
    if lo is None:
        warnings.append(t["open_lo"].format(p=name))
    elif floor is None or lo > floor:
        parts.append({"label": f"< {sc.fmt(lo)}", "min": floor, "max": lo - sc.step, "valid": False,
                      "representative": None})
    parts.append({"label": f"{sc.fmt(lo) if lo is not None else '-∞'}..{sc.fmt(hi)}", "min": lo, "max": hi,
                  "valid": True, "representative": p.get("representative")})
    if hi is None:
        warnings.append(t["open_hi"].format(p=name))
    else:
        parts.append({"label": f"> {sc.fmt(hi)}", "min": hi + sc.step, "max": sc.parse(p.get("domain_max")),
                      "valid": False, "representative": None})
    return parts


def representative(part: dict, sc: Scale):
    if part.get("representative") is not None:
        return sc.parse(part["representative"])
    lo, hi = part["min"], part["max"]
    if lo is not None and hi is not None:
        return sc.mid(lo, hi)
    if lo is not None:
        return lo + sc.step * 5
    if hi is not None:
        return hi - sc.step * 5
    return None


def which(parts: list[dict], v):
    for q in parts:
        if (q["min"] is None or v >= q["min"]) and (q["max"] is None or v <= q["max"]):
            return q
    return None


def analyse_ordered(p: dict, bva: str, t: dict, warnings: list[str]):
    sc = Scale(p["type"], p.get("step"))
    parts = build_partitions(p, sc, t, warnings)
    for q in parts:
        q["rep"] = representative(q, sc)
    values: dict = {}
    for a, b in zip(parts, parts[1:]):
        if a["max"] is None or b["min"] is None:
            continue
        cands = [a["max"], b["min"]]
        if bva == "3-value":
            cands += [a["max"] - sc.step, b["min"] + sc.step]
        for v in cands:
            values.setdefault(v, t["boundary_of"].format(a=a["label"], b=b["label"]))
    for key in ("domain_min", "domain_max"):
        if p.get(key) is not None:
            values.setdefault(sc.parse(p[key]), t["extreme"])
    bounds = []
    for v in sorted(values):
        q = which(parts, v)
        if q is None:
            continue
        bounds.append({"value": sc.fmt(v), "partition": q["label"], "valid": q["valid"], "note": values[v]})
    out_parts = [{"label": q["label"], "range": f"{sc.fmt(q['min']) if q['min'] is not None else '-∞'} .. "
                  f"{sc.fmt(q['max'])}", "valid": q["valid"],
                  "representative": sc.fmt(q["rep"]) if q["rep"] is not None else None} for q in parts]
    for label in p.get("extra_invalid", []):
        out_parts.append({"label": label, "range": "-", "valid": False, "representative": label})
    return out_parts, bounds


def analyse_enum(p: dict):
    parts = []
    valid = p.get("valid", [])
    if p.get("each_value", True):
        parts += [{"label": str(v), "range": "-", "valid": True, "representative": str(v)} for v in valid]
    elif valid:
        parts.append({"label": "{" + ", ".join(map(str, valid)) + "}", "range": "-", "valid": True,
                      "representative": str(valid[0])})
    parts += [{"label": str(v) if v != "" else "(empty)", "range": "-", "valid": False,
               "representative": str(v)} for v in p.get("invalid", [])]
    parts += [{"label": s, "range": "-", "valid": False, "representative": s} for s in p.get("extra_invalid", [])]
    return parts, []


def display(p: dict, value: str | None) -> str:
    if value is None:
        return "-"
    if p["type"] == "length":
        try:
            n = int(value)
            return f"{n} ('x'×{n})"
        except ValueError:
            return value
    return value


def run(spec: dict, lang: str, strategy: str = "compact") -> dict:
    t = T[lang]
    bva = spec.get("bva", "2-value")
    params_out = []
    warnings: list[str] = []
    for p in spec["parameters"]:
        if p["type"] == "enum":
            parts, bounds = analyse_enum(p)
        else:
            parts, bounds = analyse_ordered(p, bva, t, warnings)
        params_out.append({"name": p["name"], "type": p["type"], "partitions": parts, "boundaries": bounds})

    # nominal = representative of first valid partition
    base = {}
    for po in params_out:
        vp = next((q for q in po["partitions"] if q["valid"]), None)
        base[po["name"]] = vp["representative"] if vp else None

    conds = []
    seen = set()

    def add(pname, value, valid, source):
        row = dict(base)
        row[pname] = value
        key = json.dumps(row, sort_keys=True, ensure_ascii=False)
        if key in seen:
            return
        seen.add(key)
        conds.append({"values": row, "varied": pname, "valid": valid, "source": source})

    if strategy == "compact":
        # valid values may share a test (each-choice); invalid/unspecified ones are tested alone (single fault)
        lists = {}
        for po in params_out:
            vals = [(q["representative"], f"EP: {q['label']}") for q in po["partitions"]
                    if q["valid"] is True and q["representative"] is not None]
            vals += [(b["value"], f"BVA: {b['note']}") for b in po["boundaries"] if b["valid"] is True]
            uniq = list({v: (v, src) for v, src in vals}.values())
            lists[po["name"]] = uniq or [(base[po["name"]], "nominal")]
        rows = max(len(v) for v in lists.values())
        for i in range(rows):
            row = {n: lists[n][i % len(lists[n])][0] for n in lists}
            key = json.dumps(row, sort_keys=True, ensure_ascii=False)
            if key not in seen:
                seen.add(key)
                srcs = "; ".join(f"{n}: {lists[n][i % len(lists[n])][1]}" for n in lists if i < len(lists[n]))
                conds.append({"values": row, "varied": None, "valid": True, "source": srcs})
    else:
        conds.append({"values": dict(base), "varied": None, "valid": True, "source": "nominal"})
        seen.add(json.dumps(base, sort_keys=True, ensure_ascii=False))
    for po in params_out:
        for q in po["partitions"]:
            if q["representative"] is not None and (strategy == "single" or q["valid"] is not True):
                add(po["name"], q["representative"], q["valid"], f"EP: {q['label']}")
        for b in po["boundaries"]:
            if strategy == "single" or b["valid"] is not True:
                add(po["name"], b["value"], b["valid"], f"BVA: {b['note']}")
    for i, c in enumerate(conds, 1):
        c["id"] = f"C-{i:02d}"
    total_parts = sum(len(po["partitions"]) for po in params_out)
    total_bounds = sum(len(po["boundaries"]) for po in params_out)
    return {"id": spec.get("id"), "title": spec.get("title"), "requirement_ids": spec.get("requirement_ids", []),
            "bva": bva, "parameters": params_out, "nominal": base, "conditions": conds, "warnings": warnings,
            "summary": {"partitions": total_parts, "boundary_values": total_bounds, "conditions": len(conds)}}


def yn(v, t):
    return t["yes"] if v is True else t["no"] if v is False else t["q"]


def to_md(res: dict, lang: str, spec: dict) -> str:
    t = T[lang]
    pmap = {p["name"]: p for p in spec["parameters"]}
    o = [f"# {t['title']}: {res.get('id') or ''} {res.get('title') or ''}".rstrip(), ""]
    if res["requirement_ids"]:
        o.append(f"REQ: {', '.join(res['requirement_ids'])} · BVA: {res['bva']}")
    o.append(t["summary"].format(n=res["summary"]["partitions"], b=res["summary"]["boundary_values"],
                                 c=res["summary"]["conditions"]))
    o.append("")
    if res["warnings"]:
        o += [f"## ⚠ {t['warn']}", ""] + [f"- {w}" for w in res["warnings"]] + [""]
    o += [f"## {t['partitions']}", "", f"| {t['param']} | {t['part']} | {t['range']} | {t['valid']} | {t['rep']} |",
          "|---|---|---|---|---|"]
    for po in res["parameters"]:
        for q in po["partitions"]:
            o.append(f"| {po['name']} | {q['label']} | {q['range']} | {yn(q['valid'], t)} | "
                     f"{display(pmap[po['name']], q['representative'])} |")
    o += ["", f"## {t['bounds']}", "", f"| {t['param']} | {t['value']} | {t['part']} | {t['valid']} | {t['note']} |",
          "|---|---|---|---|---|"]
    for po in res["parameters"]:
        for b in po["boundaries"]:
            o.append(f"| {po['name']} | {display(pmap[po['name']], b['value'])} | {b['partition']} | "
                     f"{yn(b['valid'], t)} | {b['note']} |")
    names = [po["name"] for po in res["parameters"]]
    o += ["", f"## {t['conds']}", "", "| " + " | ".join([t["id"]] + names + [t["expected"], "Source"]) + " |",
          "|" + "---|" * (len(names) + 3)]
    for c in res["conditions"]:
        cells = []
        for n in names:
            v = display(pmap[n], c["values"][n])
            cells.append(f"**{v}**" if c["varied"] == n else v)
        exp = t["valid_res"] if c["valid"] is True else (
            f"{t['invalid_res']} ({c['varied']})" if c["valid"] is False else f"{t['q']} ({c['varied']})")
        o.append("| " + " | ".join([c["id"]] + cells + [exp, c["source"]]) + " |")
    return "\n".join(o) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec")
    ap.add_argument("--strategy", choices=["compact", "single"], default="compact",
                    help="compact: valid values share tests, invalid ones alone (default); "
                         "single: one non-nominal value per condition")
    ap.add_argument("--lang", choices=["en", "tr"])
    ap.add_argument("--format", choices=["md", "json"], default="md")
    ap.add_argument("--out")
    a = ap.parse_args()
    try:
        spec = json.loads(Path(a.spec).read_text(encoding="utf-8-sig"))
        lang = a.lang or spec.get("language", "en")
        lang = lang if lang in T else "en"
        res = run(spec, lang, a.strategy)
    except (OSError, ValueError, KeyError, TypeError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    text = json.dumps(res, ensure_ascii=False, indent=2) if a.format == "json" else to_md(res, lang, spec)
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
