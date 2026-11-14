#!/usr/bin/env python3
"""Equivalence partitioning + boundary value analysis (2-value / 3-value), open borders and syntax (format) testing.

Computes partitions, boundary values and single-fault test inputs from a JSON
spec, and reports gaps/overlaps/open ends in the specified ranges - those are
requirement defects worth a clarification question.

Coverage items (CTFL v4.0.1 section 4.2.1-4.2.2): each partition (EP) and each
boundary value (BVA). The C-## rows are test inputs that exercise them; the
"covers" list of a row names the coverage items it exercises.

Spec (JSON):
{
  "id": "DS-001", "title": "Loan application inputs", "requirement_ids": ["REQ-003"],
  "bva": "3-value",                      # or "2-value" (default)
  "bva_scope": "all",                    # 3-value only: "all" (default) or "valid", see below
  "strategy": "compact",                 # or "single"; the --strategy option overrides it
  "parameters": [
    {"name": "age", "type": "integer", "min": 18, "max": 65},
    {"name": "amount", "type": "decimal", "step": "0.01", "min": "1000.00", "max": "50000.00"},
    {"name": "height", "type": "decimal", "step": "0.01", "min_exclusive": "1.29", "max": "2.50"},
    {"name": "username", "type": "length", "min": 3, "max": 20},
    {"name": "start_date", "type": "date", "min": "2026-01-01", "max": "2026-12-31"},
    {"name": "score", "type": "integer", "partitions": [
        {"label": "reject", "min": 0, "max": 499, "valid": true},
        {"label": "manual review", "min": 500, "max": 699, "valid": true},
        {"label": "auto approve", "min": 700, "max": 1000, "valid": true}]},
    {"name": "currency", "type": "enum", "valid": ["TRY", "EUR"], "invalid": ["USD", ""],
     "each_value": true},
    {"name": "plate", "type": "format", "segments": [
        {"name": "city", "chars": "digit", "min": 2, "max": 2}, {"literal": " "},
        {"name": "letters", "chars": "upper", "min": 1, "max": 3}, {"literal": " "},
        {"name": "number", "chars": "digit", "min": 2, "max": 4}]},
    {"name": "age", ..., "extra_invalid": ["empty", "non-numeric 'abc'", "decimal 18.5"]}
  ]
}
Types: integer | decimal | length | date | enum | format. A partition may set
"representative". Parameters may set "domain_min"/"domain_max" (e.g. data type
limits) to add extreme-value probes.

Open borders: "min_exclusive"/"max_exclusive" (parameter or partition) state "> x" / "< x".
The border value itself then lies outside the partition (the OFF point); the closest value
inside is the ON point (CTAL-TA v4.0 section 3.1.1).

3-value BVA, "bva_scope":
  "all"   - every partition's minimum and maximum is a boundary value and gets both
            neighbours (the literal reading of CTFL v4.0.1 section 4.2.2). 18..65 gives 16, 17, 18, 19
            and 64, 65, 66, 67.
  "valid" - only the boundary values of valid partitions get both neighbours.
            18..65 gives 17, 18, 19 and 64, 65, 66.
2-value BVA gives the same values in both scopes (17, 18, 65, 66).

Format segments (syntax testing, ISO/IEC/IEEE 29119-4 section 5.2.4): "chars" is digit | upper |
lower | alpha | alnum | hex, or give your own "set": "ABC"; "min"/"max" (or "length");
{"literal": "-"}; {"options": ["TR", "DE"]}; any segment may be "optional": true.
The script emits one valid value per option and length limit, and invalid values that
each contain exactly one mutation (too short, too long, wrong character class,
missing or wrong separator, unknown option).

Usage:
  python ep_bva.py qa/design/DS-001.json                 # markdown to stdout
  python ep_bva.py spec.json --format json --out out.json
  python ep_bva.py spec.json --lang tr
Exit codes: 0 ok, 2 unreadable or invalid spec.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from decimal import Decimal
from pathlib import Path

T = {
    "en": {
        "title": "EP/BVA design", "partitions": "Equivalence partitions", "param": "Parameter",
        "part": "Partition", "range": "Range", "valid": "Valid", "rep": "Representative",
        "bounds": "Boundary values", "value": "Value", "note": "Note", "warn": "Warnings (clarify)",
        "conds": "Coverage items → test inputs (valid values may be combined; each invalid value is tested alone)",
        "id": "ID", "expected": "Expected", "valid_res": "valid (accepted)", "invalid_res": "invalid",
        "unspec": "unspecified", "yes": "yes", "no": "no", "q": "?", "base": "Nominal values",
        "gap": "Gap between '{a}' and '{b}': values {lo}..{hi} belong to no partition.",
        "overlap": "Overlap between '{a}' and '{b}': {lo}..{hi} is in both.",
        "open_hi": "'{p}' has no upper limit: what is the maximum (data type, UI, DB column)?",
        "open_lo": "'{p}' has no lower limit: what is the minimum?",
        "unspec_lo": "Values below {v} are not specified for '{p}' (treated as invalid).",
        "unspec_hi": "Values above {v} are not specified for '{p}' (treated as invalid).",
        "summary": "{n} partitions · {b} BVA coverage items ({bv} boundary values + {nb} neighbours, {mode}) · "
                   "{c} test inputs (C-##)",
        "gap_label": "gap", "boundary_of": "boundary {a} ↔ {b}", "extreme": "type/domain extreme",
        "special": "special invalid class", "neighbour_of": "neighbour of {v}", "point": "Point", "kind": "Item",
        "k_boundary": "boundary value", "k_neighbour": "neighbour", "k_extreme": "extreme",
        "open": "open border: {op} {v}", "source": "Source",
        "f_base": "valid: full form", "f_min": "valid: {s} at minimum length ({n})",
        "f_opt": "valid: {s} = {v}", "f_without": "valid: without optional {s}",
        "f_short": "{s}: too short ({n})", "f_missing": "{s}: missing", "f_long": "{s}: too long ({n})",
        "f_class": "{s}: wrong character class", "f_sep": "{s}: wrong separator", "f_unknown": "{s}: unknown option",
        "f_empty": "empty value",
    },
    "tr": {
        "title": "DS/SDA tasarımı", "partitions": "Denklik sınıfları", "param": "Parametre",
        "part": "Sınıf", "range": "Aralık", "valid": "Geçerli", "rep": "Temsilci değer",
        "bounds": "Sınır değerleri", "value": "Değer", "note": "Not", "warn": "Uyarılar (netleştirilmeli)",
        "conds": "Kapsam öğeleri → test girdileri (geçerli değerler birleştirilebilir; her geçersiz değer tek başına test edilir)",
        "id": "ID", "expected": "Beklenen", "valid_res": "geçerli (kabul)", "invalid_res": "geçersiz",
        "unspec": "tanımsız", "yes": "evet", "no": "hayır", "q": "?", "base": "Nominal değerler",
        "gap": "'{a}' ile '{b}' arasında boşluk: {lo}..{hi} değerleri hiçbir sınıfa ait değil.",
        "overlap": "'{a}' ile '{b}' çakışıyor: {lo}..{hi} her ikisinde de var.",
        "open_hi": "'{p}' için üst sınır yok: azami değer nedir (veri tipi, arayüz, veritabanı kolonu)?",
        "open_lo": "'{p}' için alt sınır yok: asgari değer nedir?",
        "unspec_lo": "'{p}' için {v} altındaki değerler tanımlanmamış (geçersiz kabul edildi).",
        "unspec_hi": "'{p}' için {v} üstündeki değerler tanımlanmamış (geçersiz kabul edildi).",
        "summary": "{n} sınıf · {b} SDA kapsam öğesi ({bv} sınır değeri + {nb} komşu, {mode}) · "
                   "{c} test girdisi (C-##)",
        "gap_label": "boşluk", "boundary_of": "sınır {a} ↔ {b}", "extreme": "tip/alan uç değeri",
        "special": "özel geçersiz sınıf", "neighbour_of": "{v} değerinin komşusu", "point": "Nokta", "kind": "Öğe",
        "k_boundary": "sınır değeri", "k_neighbour": "komşu", "k_extreme": "uç değer",
        "open": "açık sınır: {op} {v}", "source": "Kaynak",
        "f_base": "geçerli: tam biçim", "f_min": "geçerli: {s} asgari uzunlukta ({n})",
        "f_opt": "geçerli: {s} = {v}", "f_without": "geçerli: isteğe bağlı {s} olmadan",
        "f_short": "{s}: çok kısa ({n})", "f_missing": "{s}: eksik", "f_long": "{s}: çok uzun ({n})",
        "f_class": "{s}: yanlış karakter sınıfı", "f_sep": "{s}: yanlış ayırıcı", "f_unknown": "{s}: bilinmeyen seçenek",
        "f_empty": "boş değer",
    },
}
ORDERED = ("integer", "decimal", "length", "date")
BOUND_KEYS = ("min", "max", "min_exclusive", "max_exclusive")


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


def closed_bounds(q: dict, sc: Scale, where: str, opens: dict):
    """Return (min, max) as closed bounds; "min_exclusive"/"max_exclusive" become the closest inside value.

    opens collects {closed bound value: (operator, stated border value)} for the notes.
    """
    if q.get("min") is not None and q.get("min_exclusive") is not None:
        raise ValueError(f"{where}: give either 'min' or 'min_exclusive', not both")
    if q.get("max") is not None and q.get("max_exclusive") is not None:
        raise ValueError(f"{where}: give either 'max' or 'max_exclusive', not both")
    lo, hi = sc.parse(q.get("min")), sc.parse(q.get("max"))
    if q.get("min_exclusive") is not None:
        border = sc.parse(q["min_exclusive"])
        lo = border + sc.step
        opens[lo] = (">", border)
    if q.get("max_exclusive") is not None:
        border = sc.parse(q["max_exclusive"])
        hi = border - sc.step
        opens[hi] = ("<", border)
    return lo, hi


def build_partitions(p: dict, sc: Scale, t: dict, warnings: list[str], opens: dict) -> list[dict]:
    name = p["name"]
    if "partitions" in p:
        parts = []
        for q in p["partitions"]:
            lo, hi = closed_bounds(q, sc, f"parameter '{name}', partition '{q.get('label')}'", opens)
            if lo is not None and hi is not None and lo > hi:
                raise ValueError(f"parameter '{name}', partition '{q.get('label')}': the range is empty")
            parts.append({"label": q.get("label") or f"{sc.fmt(lo) if lo is not None else '-∞'}..{sc.fmt(hi)}",
                          "min": lo, "max": hi,
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

    lo, hi = closed_bounds(p, sc, f"parameter '{name}'", opens)
    if lo is not None and hi is not None and lo > hi:
        raise ValueError(f"parameter '{name}': min {sc.fmt(lo)} is greater than max {sc.fmt(hi)}")
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


def analyse_ordered(p: dict, bva: str, t: dict, warnings: list[str], scope: str = "all"):
    sc = Scale(p["type"], p.get("step"))
    opens: dict = {}
    parts = build_partitions(p, sc, t, warnings, opens)
    for q in parts:
        q["rep"] = representative(q, sc)
    values: dict = {}   # value -> (note, kind); a boundary value is never downgraded to a neighbour
    rank = {"boundary": 0, "neighbour": 1, "extreme": 2}

    def put(v, note, kind):
        if v not in values or rank[kind] < rank[values[v][1]]:
            values[v] = (note, kind)

    for a, b in zip(parts, parts[1:]):
        if a["max"] is None or b["min"] is None:
            continue
        if scope == "valid" and a["valid"] is not True and b["valid"] is not True:
            continue  # not a boundary of any valid partition
        note = t["boundary_of"].format(a=a["label"], b=b["label"])
        put(a["max"], note, "boundary")
        put(b["min"], note, "boundary")
        if bva == "3-value":
            # both neighbours of each boundary value: the adjacent partition's boundary (above) plus the
            # next value inside the own partition. "valid" scope: only for boundary values of valid partitions.
            if scope == "all" or a["valid"] is True:
                put(a["max"] - sc.step, t["neighbour_of"].format(v=sc.fmt(a["max"])), "neighbour")
            if scope == "all" or b["valid"] is True:
                put(b["min"] + sc.step, t["neighbour_of"].format(v=sc.fmt(b["min"])), "neighbour")
    for key in ("domain_min", "domain_max"):
        if p.get(key) is not None:
            put(sc.parse(p[key]), t["extreme"], "extreme")
    bounds = []
    for v in sorted(values):
        q = which(parts, v)
        if q is None:
            continue
        note, kind = values[v]
        if v in opens:
            note += " (" + t["open"].format(op=opens[v][0], v=sc.fmt(opens[v][1])) + ")"
        # domain-testing point type relative to the neighbouring valid partition (CTAL-TA v4.0 section 3.1.1)
        point = None
        if kind == "boundary":
            point = "ON" if q["valid"] is True else "OFF"
        elif kind == "neighbour":
            point = "IN" if q["valid"] is True else "OUT"
        bounds.append({"value": sc.fmt(v), "partition": q["label"], "valid": q["valid"], "note": note,
                       "kind": kind, "point": point})
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


# ---------------------------------------------------------------- syntax (format) testing
CLASSES = {"digit": "1234567890", "upper": "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "lower": "abcdefghijklmnopqrstuvwxyz",
           "hex": "1234567890ABCDEF"}
CLASSES["alpha"] = CLASSES["upper"] + CLASSES["lower"]
CLASSES["alnum"] = CLASSES["alpha"] + CLASSES["digit"]
SEPARATORS = ["-", " ", "/", ".", "_", ":"]


def _seg_kind(seg: dict) -> str:
    if "literal" in seg:
        return "literal"
    if "options" in seg:
        return "options"
    if "chars" in seg or "set" in seg:
        return "chars"
    raise ValueError(f"format segment needs 'literal', 'options', 'chars' or 'set': {seg}")


def _seg_set(seg: dict) -> str:
    if seg.get("set"):
        return str(seg["set"])
    if seg.get("chars") not in CLASSES:
        raise ValueError(f"unknown character class '{seg.get('chars')}' (use {', '.join(sorted(CLASSES))} or 'set')")
    return CLASSES[seg["chars"]]


def _seg_len(seg: dict) -> tuple[int, int]:
    lo = int(seg.get("length", seg.get("min", 1)))
    hi = int(seg.get("length", seg.get("max", lo)))
    if lo < 0 or hi < lo or hi == 0:
        raise ValueError(f"format segment has an impossible length {lo}..{hi}: {seg}")
    return lo, hi


def _fill(chars: str, n: int) -> str:
    return "".join(chars[i % len(chars)] for i in range(n))


def format_regex(segments: list[dict]) -> re.Pattern:
    out = []
    for seg in segments:
        kind = _seg_kind(seg)
        if kind == "literal":
            rx = re.escape(str(seg["literal"]))
        elif kind == "options":
            rx = "(?:" + "|".join(re.escape(str(o)) for o in seg["options"]) + ")"
        else:
            lo, hi = _seg_len(seg)
            rx = "[" + re.escape(_seg_set(seg)).replace("]", r"\]") + "]{" + f"{lo},{hi}" + "}"
        out.append(f"(?:{rx})?" if seg.get("optional") else rx)
    return re.compile("".join(out))


def analyse_format(p: dict, t: dict):
    segs = p.get("segments") or []
    if not segs:
        raise ValueError(f"parameter '{p['name']}': type 'format' needs 'segments'")
    names = [str(s.get("name") or f"#{i}") for i, s in enumerate(segs, 1)]
    rx = format_regex(segs)

    def base_of(seg):
        kind = _seg_kind(seg)
        if kind == "literal":
            return str(seg["literal"])
        if kind == "options":
            if not seg["options"]:
                raise ValueError(f"format segment has no options: {seg}")
            return str(seg["options"][0])
        return _fill(_seg_set(seg), _seg_len(seg)[1])

    base = [base_of(s) for s in segs]

    def build(i, piece):
        return "".join(base[:i] + [piece] + base[i + 1:])

    valid: list[tuple[str, str]] = [(t["f_base"], "".join(base))]
    invalid: list[tuple[str, str]] = []
    for i, seg in enumerate(segs):
        kind, name = _seg_kind(seg), names[i]
        if seg.get("optional"):
            valid.append((t["f_without"].format(s=name), build(i, "")))
        if kind == "chars":
            chars = _seg_set(seg)
            lo, hi = _seg_len(seg)
            if lo < hi and lo > 0:
                valid.append((t["f_min"].format(s=name, n=lo), build(i, _fill(chars, lo))))
            if lo >= 1 and not seg.get("optional"):
                label = t["f_missing"].format(s=name) if lo == 1 else t["f_short"].format(s=name, n=lo - 1)
                invalid.append((label, build(i, _fill(chars, lo - 1))))
            invalid.append((t["f_long"].format(s=name, n=hi + 1), build(i, _fill(chars, hi + 1))))
            wrong = next((c for c in ("A", "1", "a", "#", "é") if c not in chars), None)
            if wrong:
                invalid.append((t["f_class"].format(s=name), build(i, wrong + _fill(chars, hi)[1:])))
        elif kind == "literal":
            lit = str(seg["literal"])
            if not seg.get("optional"):
                invalid.append((t["f_missing"].format(s=name), build(i, "")))
            other = next((c for c in SEPARATORS if c != lit[:1]), "#")
            invalid.append((t["f_sep"].format(s=name), build(i, other + lit[1:])))
        else:
            for o in seg["options"][1:]:
                valid.append((t["f_opt"].format(s=name, v=o), build(i, str(o))))
            if not seg.get("optional"):
                invalid.append((t["f_missing"].format(s=name), build(i, "")))
            width = max(1, len(str(seg["options"][0])))
            unknown = next((c * width for c in "XQZ#" if c * width not in map(str, seg["options"])), "#" * (width + 1))
            invalid.append((t["f_unknown"].format(s=name), build(i, unknown)))
    invalid.append((t["f_empty"], ""))
    parts, seen = [], set()
    for label, value in valid:
        if value in seen or not rx.fullmatch(value):
            continue
        seen.add(value)
        parts.append({"label": label, "range": "-", "valid": True, "representative": value})
    for label, value in invalid:
        if value in seen or rx.fullmatch(value):   # a mutation that is still well-formed is not an invalid class
            continue
        seen.add(value)
        parts.append({"label": label, "range": "-", "valid": False, "representative": value})
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
    if p["type"] == "format":
        return f'"{value}"'
    return value


def part_key(param: str, label: str) -> str:
    return f"{param}: {label}"


def bound_key(param: str, value: str) -> str:
    return f"{param} = {value}"


def run(spec: dict, lang: str, strategy: str | None = None) -> dict:
    t = T[lang]
    strategy = strategy or spec.get("strategy") or "compact"
    if strategy not in ("compact", "single"):
        raise ValueError(f"strategy must be 'compact' or 'single' (got {strategy!r})")
    bva = spec.get("bva", "2-value")
    if bva not in ("2-value", "3-value"):
        raise ValueError(f"bva must be '2-value' or '3-value' (got {bva!r})")
    scope = spec.get("bva_scope", "all")
    if scope not in ("all", "valid"):
        raise ValueError(f"bva_scope must be 'all' or 'valid' (got {scope!r})")
    params_out = []
    warnings: list[str] = []
    for p in spec["parameters"]:
        if p["type"] == "enum":
            parts, bounds = analyse_enum(p)
        elif p["type"] == "format":
            parts, bounds = analyse_format(p, t)
        elif p["type"] in ORDERED:
            parts, bounds = analyse_ordered(p, bva, t, warnings, scope)
        else:
            raise ValueError(f"parameter '{p['name']}': unknown type '{p['type']}' "
                             "(integer, decimal, length, date, enum, format)")
        params_out.append({"name": p["name"], "type": p["type"], "partitions": parts, "boundaries": bounds})

    # nominal = representative of first valid partition
    base = {}
    for po in params_out:
        vp = next((q for q in po["partitions"] if q["valid"]), None)
        base[po["name"]] = vp["representative"] if vp else None

    # which coverage items a value of a parameter exercises: its partition, and itself when it is a BVA item
    item_of: dict = {}
    for po in params_out:
        m = item_of.setdefault(po["name"], {})
        for q in po["partitions"]:
            if q["representative"] is not None:
                m.setdefault(q["representative"], []).append(["partitions", part_key(po["name"], q["label"])])
        for b in po["boundaries"]:
            items = m.setdefault(b["value"], [])
            pk = ["partitions", part_key(po["name"], b["partition"])]
            if pk not in items:
                items.append(pk)
            items.append(["boundary_values", bound_key(po["name"], b["value"])])

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
        # A rejected input proves nothing about the other parameters' partitions (defect masking):
        # a row with an invalid or unspecified value covers only the varied parameter's items.
        names = [c["varied"]] if c["valid"] is not True and c["varied"] else list(c["values"])
        covers = []
        for n in names:
            for it in item_of.get(n, {}).get(c["values"][n], []):
                if it not in covers:
                    covers.append(it)
        c["covers"] = covers
    total_parts = sum(len(po["partitions"]) for po in params_out)
    total_bounds = sum(len(po["boundaries"]) for po in params_out)
    kinds = [b["kind"] for po in params_out for b in po["boundaries"]]
    return {"id": spec.get("id"), "title": spec.get("title"), "requirement_ids": spec.get("requirement_ids", []),
            "bva": bva, "bva_scope": scope, "strategy": strategy,
            "parameters": params_out, "nominal": base, "conditions": conds, "warnings": warnings,
            "summary": {"partitions": total_parts, "boundary_values": total_bounds, "conditions": len(conds),
                        "bva_boundaries": kinds.count("boundary"), "bva_neighbours": kinds.count("neighbour"),
                        "bva_extremes": kinds.count("extreme"), "test_inputs": len(conds)}}


def coverage_model(res: dict) -> dict:
    """Coverage items per measure and the items each C-## row exercises (used by design_coverage.py)."""
    parts = [part_key(po["name"], q["label"]) for po in res["parameters"] for q in po["partitions"]]
    bounds = [bound_key(po["name"], b["value"]) for po in res["parameters"] for b in po["boundaries"]]
    return {"technique": "equivalence-partitioning",
            "options": f"{res.get('bva', '2-value')} BVA, scope {res.get('bva_scope', 'all')}, "
                       f"strategy {res.get('strategy', 'compact')}",
            "measures": [{"name": "partitions", "technique": "equivalence-partitioning", "required": True,
                          "items": parts},
                         {"name": "boundary_values", "technique": "boundary-value-analysis", "required": True,
                          "items": bounds}],
            "refs": {c["id"]: [tuple(x) for x in c.get("covers", [])] for c in res["conditions"]}}


def yn(v, t):
    return t["yes"] if v is True else t["no"] if v is False else t["q"]


def to_md(res: dict, lang: str, spec: dict) -> str:
    t = T[lang]
    pmap = {p["name"]: p for p in spec["parameters"]}
    s = res["summary"]
    o = [f"# {t['title']}: {res.get('id') or ''} {res.get('title') or ''}".rstrip(), ""]
    if res["requirement_ids"]:
        o.append(f"REQ: {', '.join(res['requirement_ids'])} · BVA: {res['bva']}")
    mode = res["bva"] + (f", scope {res['bva_scope']}" if res["bva"] == "3-value" else "")
    o.append(t["summary"].format(n=s["partitions"], b=s["boundary_values"], bv=s["bva_boundaries"] + s["bva_extremes"],
                                 nb=s["bva_neighbours"], mode=mode, c=s["conditions"]))
    o.append("")
    if res["warnings"]:
        o += [f"## ⚠ {t['warn']}", ""] + [f"- {w}" for w in res["warnings"]] + [""]
    o += [f"## {t['partitions']}", "", f"| {t['param']} | {t['part']} | {t['range']} | {t['valid']} | {t['rep']} |",
          "|---|---|---|---|---|"]
    for po in res["parameters"]:
        for q in po["partitions"]:
            o.append(f"| {po['name']} | {q['label']} | {q['range']} | {yn(q['valid'], t)} | "
                     f"{display(pmap[po['name']], q['representative'])} |")
    o += ["", f"## {t['bounds']}", "",
          f"| {t['param']} | {t['value']} | {t['part']} | {t['valid']} | {t['kind']} | {t['point']} | {t['note']} |",
          "|---|---|---|---|---|---|---|"]
    for po in res["parameters"]:
        for b in po["boundaries"]:
            o.append(f"| {po['name']} | {display(pmap[po['name']], b['value'])} | {b['partition']} | "
                     f"{yn(b['valid'], t)} | {t['k_' + b.get('kind', 'boundary')]} | {b.get('point') or '-'} | {b['note']} |")
    names = [po["name"] for po in res["parameters"]]
    o += ["", f"## {t['conds']}", "", "| " + " | ".join([t["id"]] + names + [t["expected"], t["source"]]) + " |",
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
    ap.add_argument("--strategy", choices=["compact", "single"],
                    help="compact: valid values share tests, invalid ones alone (default); "
                         "single: one non-nominal value per test input. Overrides the spec's \"strategy\".")
    ap.add_argument("--lang", choices=["en", "tr"])
    ap.add_argument("--format", choices=["md", "json"], default="md")
    ap.add_argument("--out")
    sys.stdout.reconfigure(encoding="utf-8")
    a = ap.parse_args()
    try:
        spec = json.loads(Path(a.spec).read_text(encoding="utf-8-sig"))
        lang = a.lang or spec.get("language", "en")
        lang = lang if lang in T else "en"
        res = run(spec, lang, a.strategy)
    except (OSError, ValueError, KeyError, TypeError, ArithmeticError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    text = json.dumps(res, ensure_ascii=False, indent=2) if a.format == "json" else to_md(res, lang, spec)
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(text, encoding="utf-8", newline="\n")
        print(f"wrote {a.out}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
