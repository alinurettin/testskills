#!/usr/bin/env python3
"""Reconcile a migrated target extract against its source extract (two CSV files).

It applies the mapping specification's transformation rules to every source row, so each
target value is compared with what it SHOULD be, not with the raw legacy value.

Checks and report sections:
  - row counts, rows with an empty key, duplicate keys on each side
  - key-set comparison: missing in target / unexpected in target
  - field-level comparison per target column (source value, transformed expectation, target
    value) with a diagnostic hint: mojibake (UTF-8 vs cp1254/cp1252), x100 decimal-separator
    misparse, rounding, day/month swap, Turkish casing, transliteration, whitespace, leading zeros
  - control totals (sum columns, Decimal - never float) overall and per group, plus counts per group
  - null-rate change per column; mapping coverage (source columns without a decision)
  - verdict PASS/FAIL against explicit rules; documented accepted exceptions do not fail it

mapping.json (all keys optional):
  {"columns": {"target_col": {"source": "SRC_COL", "transform": ["trim", "upper_tr"]},
               "balance":    {"source": "BAKIYE", "transform": ["decimal:2:,"]},
               "full_name":  {"transform": [{"concat": ["AD", "SOYAD", " "]}, "collapse_spaces"]},
               "country":    {"source": null, "transform": ["default:TR"]},
               "email": "EPOSTA"},                       <- shorthand: identity mapping
   "ignore": ["load_ts"],                                <- target columns not compared
   "not_migrated": ["FAKS"],                             <- source columns deliberately dropped
   "accepted_exceptions": [{"check": "column", "key": "1007", "column": "email",
                            "reason": "DEF-41 accepted by data owner"}]}
Transform ops (string "op" / "op:arg", or object {"op": arg}), applied left to right:
  trim, collapse_spaces (also trims), upper, lower, upper_tr, lower_tr (Turkish i/İ, ı/I),
  date:<in>><out> (e.g. date:%d.%m.%Y>%Y-%m-%d), decimal[:scale[:sep]] (auto-detects
  "1.234,56" / "1,234.56"; sep "," or "." forces the decimal separator; rounds HALF_UP),
  map:{"A":"ACTIVE"} ("*" = fallback; unknown codes are transform errors), default:<value>,
  strip_leading_zeros, zfill:<n>, concat:["col1","col2","sep"] (last item = separator; empty
  parts skipped). A column whose ops include decimal (or "type": "decimal") compares numerically.
Without --mapping, same-named columns are compared as-is (sum columns numerically).
Accepted exception checks: missing, unexpected, duplicate_source, duplicate_target, empty_key
(key = row number), column (key + column), total (column [+ group]), unmapped_source (column).

Examples:
  python reconcile.py --source legacy.csv --target new.csv --key customer_id \\
      --mapping mapping.json --sum balance --group-by branch --encoding-source cp1254 \\
      --delimiter-source ";" --lang tr --out reconciliation.md --json reconciliation.json
  python reconcile.py --source a.csv --target b.csv --key id,line_no --out rec.md

Memory: the source side is held as {key: expected values}; budget roughly 0.5-1 KB per source
row (about 0.5-1 GB for 1M rows of ~10 columns). For larger volumes reconcile inside the
database (see assets/reconciliation-queries.sql) or compare key + row-hash extracts.
Exit codes: 0 PASS, 1 FAIL, 2 usage or input error.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from functools import lru_cache
from pathlib import Path

csv.field_size_limit(2**31 - 1)

T = {
    "en": {
        "title": "Data migration reconciliation", "verdict": "Verdict", "rules": "Sign-off rules",
        "rule": "Rule", "value": "Value", "threshold": "Threshold", "result": "Result",
        "inputs": "Inputs", "file": "File", "rows": "Rows", "encoding": "Encoding", "delim": "Delimiter",
        "source": "Source", "target": "Target", "key": "Key", "distinct": "Distinct keys", "matched": "Matched keys",
        "r_empty": "Rows with an empty key", "r_dup_s": "Duplicate keys in source", "r_dup_t": "Duplicate keys in target",
        "r_missing": "Missing in target", "r_unexp": "Unexpected in target", "r_field": "Field mismatches (incl. transform errors)",
        "r_total": "Control-total differences above tolerance", "r_tcol": "Mapped target columns absent from target file",
        "r_unmapped": "Source columns without a mapping decision",
        "coverage": "Mapping coverage", "unmapped_src": "Source columns with no target and no 'not migrated' decision",
        "not_migrated": "Source columns explicitly not migrated", "implicit": "Implicit same-name mappings (confirm in the mapping spec)",
        "unmapped_tgt": "Target columns with no mapping (not compared)", "absent_tgt": "Mapped target columns absent from target file",
        "ignored": "Ignored target columns", "none": "none",
        "keys": "Key reconciliation", "dup_s": "Duplicate keys in source", "dup_t": "Duplicate keys in target",
        "missing": "Missing in target (in source, not in target)", "unexp": "Unexpected in target (in target, not in source)",
        "empty_key": "Rows with an empty key (row numbers)", "occ": "occurrences", "more": "... and {n} more",
        "key_hint": "Hint: {n} missing and {m} unexpected keys look alike after trimming/leading zeros/case - check the key transformation.",
        "fields": "Field-level comparison", "column": "Column", "rule_col": "Rule", "compared": "Compared",
        "mism": "Mismatches", "terr": "Transform errors", "acc": "Accepted", "src_val": "Source value",
        "expected": "Expected (transformed)", "tgt_val": "Target value", "hint": "Hint", "examples": "Examples",
        "totals": "Control totals", "group": "Group", "diff": "Difference", "count": "Count", "total_all": "(all rows)",
        "unparsed": "Unparseable values excluded from totals: source {s}, target {t}.",
        "nulls": "Null rates (each file on its own row count; a small change can be a denominator effect of missing/extra rows)", "exp_null": "Expected null %", "tgt_null": "Target null %", "delta": "Change (pp)",
        "accepted": "Accepted exceptions", "reason": "Reason", "used": "Observed", "stale": "not observed (stale?)",
        "classify": "Defect classification guide",
        "classify_body": [
            "Transform errors and 'not in map' codes: **source data quality** (profile and cleanse) or a **mapping spec gap** (the rule does not cover the value).",
            "Mismatch with a mojibake/encoding hint: **extract or load defect** (wrong code page), not a data owner issue.",
            "Mismatch with a rule-shaped hint (x100, day/month swap, rounding, casing, wrong code): **transformation defect**.",
            "Missing/unexpected/duplicate keys: **load defect** (rejects, filters, non-idempotent rerun) or a **scope gap** in the spec (test/closed records).",
            "Control-total differences without row-level findings: suspect the comparison scope or a totals query; with row findings they are the consequence, file the row-level cause."],
        "legend": "∅ = empty. Values are shown exactly; the comparison is exact for text and within tolerance {tol} for numbers.",
        "h_srcbad": "source not transformable: {msg}", "h_lost": "value lost (empty in target)",
        "h_extra": "value present where empty expected", "h_x100": "×100: decimal separator lost",
        "h_d100": "÷100: decimal separator misplaced", "h_sign": "sign flipped", "h_round": "small difference ({d}): rounding if the source has more decimals, otherwise precision loss/truncation (float?)",
        "h_moj": "encoding: {good} text decoded as {bad} (mojibake)", "h_moj_src": "source read with the wrong encoding? ({good} as {bad}) - check --encoding-source",
        "h_q": "encoding: characters replaced by '?'/'\ufffd'", "h_case": "letter case differs (Turkish İ/ı casing?)",
        "h_ascii": "Turkish characters transliterated to ASCII", "h_ws": "whitespace differs",
        "h_swap": "day/month swapped", "h_zero": "leading zeros differ", "h_nan": "target is not a number",
        "h_code": "valid code, but the mapping of a different source code",
    },
    "tr": {
        "title": "Veri göçü mutabakatı", "verdict": "Karar", "rules": "Onay kuralları",
        "rule": "Kural", "value": "Değer", "threshold": "Eşik", "result": "Sonuç",
        "inputs": "Girdiler", "file": "Dosya", "rows": "Satır", "encoding": "Kodlama", "delim": "Ayraç",
        "source": "Kaynak", "target": "Hedef", "key": "Anahtar", "distinct": "Tekil anahtar", "matched": "Eşleşen anahtar",
        "r_empty": "Anahtarı boş satırlar", "r_dup_s": "Kaynakta mükerrer anahtar", "r_dup_t": "Hedefte mükerrer anahtar",
        "r_missing": "Hedefte eksik", "r_unexp": "Hedefte beklenmeyen", "r_field": "Alan uyuşmazlıkları (dönüşüm hataları dahil)",
        "r_total": "Toleransı aşan kontrol toplamı farkları", "r_tcol": "Hedef dosyada olmayan eşlenmiş hedef kolonlar",
        "r_unmapped": "Eşleme kararı olmayan kaynak kolonlar",
        "coverage": "Eşleme kapsamı", "unmapped_src": "Hedefi de 'taşınmayacak' kararı da olmayan kaynak kolonlar",
        "not_migrated": "Açıkça taşınmayan kaynak kolonlar", "implicit": "Örtük aynı-ad eşlemeleri (eşleme spesifikasyonunda teyit edin)",
        "unmapped_tgt": "Eşlemesi olmayan hedef kolonlar (karşılaştırılmadı)", "absent_tgt": "Hedef dosyada olmayan eşlenmiş hedef kolonlar",
        "ignored": "Yok sayılan hedef kolonlar", "none": "yok",
        "keys": "Anahtar mutabakatı", "dup_s": "Kaynakta mükerrer anahtarlar", "dup_t": "Hedefte mükerrer anahtarlar",
        "missing": "Hedefte eksik (kaynakta var, hedefte yok)", "unexp": "Hedefte beklenmeyen (hedefte var, kaynakta yok)",
        "empty_key": "Anahtarı boş satırlar (satır numaraları)", "occ": "tekrar", "more": "... ve {n} tane daha",
        "key_hint": "İpucu: {n} eksik ve {m} beklenmeyen anahtar kırpma/baştaki sıfır/harf büyüklüğü sonrası benziyor - anahtar dönüşümünü kontrol edin.",
        "fields": "Alan düzeyinde karşılaştırma", "column": "Kolon", "rule_col": "Kural", "compared": "Karşılaştırılan",
        "mism": "Uyuşmazlık", "terr": "Dönüşüm hatası", "acc": "Kabul edilen", "src_val": "Kaynak değer",
        "expected": "Beklenen (dönüştürülmüş)", "tgt_val": "Hedef değer", "hint": "İpucu", "examples": "Örnekler",
        "totals": "Kontrol toplamları", "group": "Grup", "diff": "Fark", "count": "Adet", "total_all": "(tüm satırlar)",
        "unparsed": "Toplamlara katılmayan sayı olmayan değerler: kaynak {s}, hedef {t}.",
        "nulls": "Boş değer oranları (her dosya kendi satır sayısına göre; küçük değişim eksik/fazla satırların payda etkisi olabilir)", "exp_null": "Beklenen boş %", "tgt_null": "Hedef boş %", "delta": "Değişim (puan)",
        "accepted": "Kabul edilen istisnalar", "reason": "Gerekçe", "used": "Gözlendi", "stale": "gözlenmedi (güncel değil mi?)",
        "classify": "Hata sınıflandırma rehberi",
        "classify_body": [
            "Dönüşüm hataları ve 'eşlemede yok' kodları: **kaynak veri kalitesi** (profille ve temizle) ya da **eşleme spesifikasyonu boşluğu** (kural bu değeri kapsamıyor).",
            "Karakter bozulması/kodlama ipuçlu uyuşmazlık: **çıkarma veya yükleme hatası** (yanlış kod sayfası), veri sahibinin sorunu değil.",
            "Kural biçimli ipucu (×100, gün/ay yer değiştirmesi, yuvarlama, harf büyüklüğü, yanlış kod): **dönüşüm hatası**.",
            "Eksik/beklenmeyen/mükerrer anahtar: **yükleme hatası** (reddedilen kayıt, filtre, idempotent olmayan tekrar çalıştırma) ya da spesifikasyonda **kapsam boşluğu** (test/kapalı kayıtlar).",
            "Satır bulgusu olmadan kontrol toplamı farkı: karşılaştırma kapsamından veya toplam sorgusundan şüphelenin; satır bulgusu varsa fark onun sonucudur, satır düzeyindeki nedeni raporlayın."],
        "legend": "∅ = boş. Değerler olduğu gibi gösterilir; metin tam eşitlikle, sayılar {tol} toleransla karşılaştırılır.",
        "h_srcbad": "kaynak dönüştürülemedi: {msg}", "h_lost": "değer kaybolmuş (hedefte boş)",
        "h_extra": "boş beklenirken değer var", "h_x100": "×100: ondalık ayracı kaybolmuş",
        "h_d100": "÷100: ondalık ayracı kaymış", "h_sign": "işaret ters", "h_round": "küçük fark ({d}): kaynakta fazla ondalık varsa yuvarlama, yoksa hassasiyet kaybı/kesme (float?)",
        "h_moj": "kodlama: {good} metin {bad} olarak okunmuş (bozuk karakter)", "h_moj_src": "kaynak yanlış kodlamayla mı okundu? ({good} → {bad}) - --encoding-source kontrol edin",
        "h_q": "kodlama: karakterler '?'/'\ufffd' ile değişmiş", "h_case": "harf büyüklüğü farklı (Türkçe İ/ı dönüşümü?)",
        "h_ascii": "Türkçe karakterler ASCII'ye çevrilmiş", "h_ws": "boşluk farkı",
        "h_swap": "gün/ay yer değiştirmiş", "h_zero": "baştaki sıfırlar farklı", "h_nan": "hedef değer sayı değil",
        "h_code": "geçerli kod, ama başka bir kaynak kodun eşlemesi",
    },
}

OPS_NOARG = {"trim", "collapse_spaces", "upper", "lower", "upper_tr", "lower_tr", "strip_leading_zeros"}
OPS_ARG = {"date", "decimal", "map", "default", "zfill", "concat"}
NUM_RE = re.compile(r"[+-]?(\d+(\.\d*)?|\.\d+)")
TR_ASCII = str.maketrans("çğıöşüÇĞİÖŞÜâîûÂÎÛ", "cgiosuCGIOSUaiuAIU")


class UsageError(Exception):
    pass


class TransformError(ValueError):
    pass


class Bad(str):
    """An expected value that could not be computed (the string is the reason)."""


# ---------------------------------------------------------------- transforms
def upper_tr(s: str) -> str:
    return s.replace("i", "İ").replace("ı", "I").upper()


def lower_tr(s: str) -> str:
    return s.replace("I", "ı").replace("İ", "i").lower()


def parse_decimal(text: str, sep: str | None = None) -> Decimal:
    """'1.234,56', '1,234.56', '1234.56', '-150,00', '150,00-' -> Decimal. sep forces the decimal separator."""
    s = text.strip().replace("\u00a0", "").replace(" ", "").replace("'", "")
    neg = False
    if s.endswith("-") and len(s) > 1:
        neg, s = True, s[:-1]
    if sep is None:
        if "," in s and "." in s:
            sep = "," if s.rfind(",") > s.rfind(".") else "."
        elif "," in s:
            sep = "," if s.count(",") == 1 else "."
        else:
            sep = "." if s.count(".") <= 1 else ","
    s = s.replace("." if sep == "," else ",", "")
    if sep == ",":
        s = s.replace(",", ".")
    if not NUM_RE.fullmatch(s):
        raise TransformError(f"not a number: {text!r}")
    d = Decimal(s)
    return -d if neg else d


@lru_cache(maxsize=65536)
def convert_date(value: str, fmt_in: str, fmt_out: str) -> str:
    try:
        return datetime.strptime(value, fmt_in).strftime(fmt_out)
    except ValueError:
        raise TransformError(f"date {value!r} does not match {fmt_in}") from None


def fmt_dec(d: Decimal) -> str:
    return format(d, "f")


def compile_ops(ops, where: str) -> list:
    out = []
    for op in ops or []:
        if isinstance(op, dict):
            if len(op) != 1:
                raise UsageError(f"{where}: an object op needs exactly one key, got {op}")
            name, arg = next(iter(op.items()))
        elif isinstance(op, str):
            name, _, arg = op.partition(":")
            arg = arg if _ else None
            if name in ("map", "concat") and arg is not None:
                try:
                    arg = json.loads(arg)
                except ValueError as e:
                    raise UsageError(f"{where}: {name} argument must be JSON: {e}")
        else:
            raise UsageError(f"{where}: invalid op {op!r}")
        if name in OPS_NOARG:
            out.append((name, None))
            continue
        if name not in OPS_ARG:
            raise UsageError(f"{where}: unknown transform op '{name}'")
        if name == "date":
            if not isinstance(arg, str) or ">" not in arg:
                raise UsageError(f"{where}: date needs '<in_fmt>><out_fmt>', e.g. date:%d.%m.%Y>%Y-%m-%d")
            arg = tuple(arg.split(">", 1))
        elif name == "decimal":
            parts = str(arg).split(":") if arg not in (None, "") else []
            scale = int(parts[0]) if parts and parts[0] != "" else None
            sep = parts[1] if len(parts) > 1 else None
            if sep not in (None, ",", "."):
                raise UsageError(f"{where}: decimal separator must be ',' or '.'")
            arg = (scale, sep)
        elif name == "map":
            if not isinstance(arg, dict):
                raise UsageError(f"{where}: map needs an object, e.g. {{\"map\": {{\"A\": \"ACTIVE\"}}}}")
            arg = {str(k): str(v) for k, v in arg.items()}
        elif name == "concat":
            if not (isinstance(arg, list) and len(arg) >= 2 and all(isinstance(x, str) for x in arg)):
                raise UsageError(f"{where}: concat needs [\"col1\", ..., \"separator\"]")
        elif name == "zfill":
            arg = int(arg)
        elif name == "default":
            arg = "" if arg is None else str(arg)
        out.append((name, arg))
    return out


def apply_ops(value: str, row: dict, ops: list) -> str:
    for name, arg in ops:
        if name == "trim":
            value = value.strip()
        elif name == "collapse_spaces":
            value = " ".join(value.split())
        elif name == "upper":
            value = value.upper()
        elif name == "lower":
            value = value.lower()
        elif name == "upper_tr":
            value = upper_tr(value)
        elif name == "lower_tr":
            value = lower_tr(value)
        elif name == "strip_leading_zeros":
            value = (value.strip().lstrip("0") or "0") if value.strip() else ""
        elif name == "zfill":
            value = value.strip().zfill(arg) if value.strip() else ""
        elif name == "default":
            value = arg if value.strip() == "" else value
        elif name == "concat":
            value = arg[-1].join(row[c] for c in arg[:-1] if row.get(c, "").strip())
        elif name == "date":
            if value.strip():
                value = convert_date(value.strip(), arg[0], arg[1])
        elif name == "decimal":
            if value.strip():
                d = parse_decimal(value, arg[1])
                if arg[0] is not None:
                    d = d.quantize(Decimal(1).scaleb(-arg[0]), rounding=ROUND_HALF_UP)
                value = fmt_dec(d)
        elif name == "map":
            if value in arg:
                value = arg[value]
            elif value.strip() == "" and "" not in arg:
                pass
            elif "*" in arg:
                value = arg["*"]
            else:
                raise TransformError(f"code {value!r} not in map")
    return value


# ---------------------------------------------------------------- diagnosis
def diagnose(expected: str, target: str, numeric: bool, t: dict, codes: frozenset = frozenset()) -> str:
    if isinstance(expected, Bad):
        return t["h_srcbad"].format(msg=str(expected))
    if expected != "" and target.strip() == "":
        return t["h_lost"]
    if expected == "" and target.strip() != "":
        return t["h_extra"]
    if numeric:
        try:
            e, v = parse_decimal(expected), parse_decimal(target)
        except TransformError:
            return t["h_nan"]
        if e != 0 and v == e * 100:
            return t["h_x100"]
        if e != 0 and v * 100 == e:
            return t["h_d100"]
        if e != 0 and v == -e:
            return t["h_sign"]
        if abs(v - e) <= Decimal("0.05"):
            return t["h_round"].format(d=fmt_dec(v - e))
        return ""
    for good in ("utf-8", "cp1254"):
        for bad in ("cp1252", "cp1254", "latin-1"):
            if good == bad:
                continue
            try:
                if expected.encode(good).decode(bad) == target:
                    return t["h_moj"].format(good=good, bad=bad)
            except (UnicodeError, LookupError):
                pass
            try:
                if target.encode(good).decode(bad) == expected:
                    return t["h_moj_src"].format(good=good, bad=bad)
            except (UnicodeError, LookupError):
                pass
    if ("?" in target or "\ufffd" in target) and len(target) == len(expected) and all(
            a == b or (ord(a) > 127 and b in "?\ufffd") for a, b in zip(expected, target)):
        return t["h_q"]
    if expected.translate(TR_ASCII) == target and expected != target:
        return t["h_ascii"]
    if lower_tr(expected) == lower_tr(target) or expected.casefold() == target.casefold():
        return t["h_case"]
    if expected.translate(TR_ASCII).casefold() == target.translate(TR_ASCII).casefold() and expected.casefold() != target.casefold():
        return t["h_ascii"]
    if " ".join(expected.split()) == " ".join(target.split()):
        return t["h_ws"]
    m = re.fullmatch(r"(\d{4})([-./]?)(\d{2})\2(\d{2})", expected) or None
    if m and f"{m[1]}{m[2]}{m[4]}{m[2]}{m[3]}" == target:
        return t["h_swap"]
    m = re.fullmatch(r"(\d{2})([-./])(\d{2})\2(\d{4})", expected)
    if m and f"{m[3]}{m[2]}{m[1]}{m[2]}{m[4]}" == target:
        return t["h_swap"]
    if expected.lstrip("0") == target.lstrip("0"):
        return t["h_zero"]
    if target in codes:
        return t["h_code"]
    return ""


# ---------------------------------------------------------------- IO helpers
def open_reader(path: str, encoding: str, delimiter: str):
    try:
        fh = open(path, encoding=encoding, newline="")
        reader = csv.DictReader(fh, delimiter=delimiter, restval="")
        header = reader.fieldnames or []
    except FileNotFoundError:
        raise UsageError(f"file not found: {path}")
    except LookupError:
        raise UsageError(f"unknown encoding: {encoding}")
    except UnicodeDecodeError as e:
        raise UsageError(f"{path}: cannot decode as {encoding} ({e.reason} at byte {e.start}); "
                         "legacy Turkish files are often cp1254 or iso-8859-9")
    if not header:
        raise UsageError(f"{path}: empty file or no header row")
    header = [h.strip() for h in header]
    reader.fieldnames = header
    return fh, reader, header


def rows(reader, path: str, encoding: str):
    try:
        for i, row in enumerate(reader, start=2):
            if None in row:
                raise UsageError(f"{path}: line {i} has more fields than the header (wrong delimiter or unquoted separator?)")
            yield i, row
    except UnicodeDecodeError as e:
        raise UsageError(f"{path}: cannot decode as {encoding} ({e.reason}); "
                         "legacy Turkish files are often cp1254 or iso-8859-9")


def keystr(key: tuple) -> str:
    return "|".join(key)


def md(v) -> str:
    s = "" if v is None else str(v)
    if s == "":
        return "∅"
    s = s.replace("`", "ˋ").replace("\r", "\\r").replace("\n", "\\n").replace("|", "\\|")
    return f"`{s}`"


def pct(n: int, d: int) -> float:
    return round(100.0 * n / d, 2) if d else 0.0


# ---------------------------------------------------------------- core
def build_plan(mapping: dict | None, src_header: list, tgt_header: list, keys: list, sum_cols: list, group_by: str | None):
    """Return ordered target-column specs: name -> {source, ops, numeric, implicit}, plus coverage info."""
    plan, implicit = {}, []
    mapping = mapping or {}
    ignore = set(mapping.get("ignore", []))
    for tcol, spec in (mapping.get("columns") or {}).items():
        if isinstance(spec, str) or spec is None:
            spec = {"source": spec}
        if not isinstance(spec, dict):
            raise UsageError(f"mapping column '{tcol}': expected an object or a source column name")
        ops = compile_ops(spec.get("transform"), f"mapping column '{tcol}'")
        if "source" in spec:
            src = spec["source"]
        else:
            src = tcol if tcol in src_header and not any(n == "concat" for n, _ in ops) else None
        numeric = spec.get("type") == "decimal" or any(n == "decimal" for n, _ in ops)
        plan[tcol] = {"source": src, "ops": ops, "numeric": numeric, "implicit": False,
                      "rule": " → ".join(n for n, _ in ops) or "="}
    for tcol in tgt_header:
        if tcol in plan or tcol in ignore:
            continue
        if tcol in src_header:
            plan[tcol] = {"source": tcol, "ops": [], "numeric": tcol in sum_cols, "implicit": bool(mapping.get("columns")),
                          "rule": "="}
            if mapping.get("columns"):
                implicit.append(tcol)
    for k in keys + sum_cols + ([group_by] if group_by else []):
        if k not in plan:
            if k in src_header:
                plan[k] = {"source": k, "ops": [], "numeric": k in sum_cols, "implicit": True, "rule": "="}
                implicit.append(k)
            else:
                raise UsageError(f"column '{k}' is neither mapped nor present in the source file")
        if k in sum_cols:
            plan[k]["numeric"] = True
    for tcol, p in plan.items():
        needed = [p["source"]] if p["source"] else []
        needed += [c for n, a in p["ops"] if n == "concat" for c in a[:-1]]
        for c in needed:
            if c not in src_header:
                raise UsageError(f"mapping column '{tcol}': source column '{c}' not in source header {src_header}")
        p["needs"] = needed
        p["codes"] = frozenset(v for n, a in p["ops"] if n == "map" for v in a.values())
    for k in keys + sum_cols + ([group_by] if group_by else []):
        if k not in tgt_header:
            raise UsageError(f"column '{k}' (key/sum/group) not in target header {tgt_header}")
    used = {c for p in plan.values() for c in p["needs"]}
    not_migrated = list(mapping.get("not_migrated", []))
    coverage = {
        "unmapped_source_columns": [c for c in src_header if c not in used and c not in not_migrated],
        "not_migrated": not_migrated,
        "implicit_mappings": list(dict.fromkeys(implicit)),
        "unmapped_target_columns": [c for c in tgt_header if c not in plan and c not in ignore],
        "absent_target_columns": [c for c in plan if c not in tgt_header],
        "ignored_target_columns": [c for c in tgt_header if c in ignore],
    }
    return plan, coverage


def reconcile(a) -> dict:
    t = T[a.lang]
    mapping = None
    if a.mapping:
        try:
            mapping = json.loads(Path(a.mapping).read_text(encoding="utf-8-sig"))
        except FileNotFoundError:
            raise UsageError(f"mapping not found: {a.mapping}")
        except ValueError as e:
            raise UsageError(f"mapping is not valid JSON: {e}")
    keys = [k.strip() for k in a.key.split(",") if k.strip()]
    sum_cols = [c.strip() for c in (a.sum or "").split(",") if c.strip()]
    tol = Decimal(str(a.tolerance))
    total_tol = Decimal(str(a.total_tolerance))
    d_src = a.delimiter_source or a.delimiter
    d_tgt = a.delimiter_target or a.delimiter

    sfh, sreader, src_header = open_reader(a.source, a.encoding_source, d_src)
    tfh, treader, tgt_header = open_reader(a.target, a.encoding_target, d_tgt)
    plan, coverage = build_plan(mapping, src_header, tgt_header, keys, sum_cols, a.group_by)
    cols = [c for c in plan if c in tgt_header and c not in keys]   # compared columns (non-key)
    exp_cols = keys + cols + [c for c in sum_cols + ([a.group_by] if a.group_by else []) if c not in keys + cols]
    idx = {c: i for i, c in enumerate(exp_cols)}

    exc_raw = (mapping or {}).get("accepted_exceptions", [])
    exceptions = {}
    for e in exc_raw:
        if not isinstance(e, dict) or not e.get("check") or not e.get("reason"):
            raise UsageError(f"accepted exception needs 'check' and 'reason': {e}")
        ident = (e["check"], str(e.get("key", "")), e.get("column", ""), e.get("group", ""))
        exceptions[ident] = {**e, "observed": False}

    def accepted(check, key="", column="", group=""):
        ex = exceptions.get((check, key, column, group))
        if ex:
            ex["observed"] = True
            return True
        return False

    def expected_row(row):
        vals = []
        for c in exp_cols:
            p = plan[c]
            raw = row.get(p["source"], "") if p["source"] else ""
            try:
                vals.append(apply_ops(raw, row, p["ops"]))
            except TransformError as e:
                vals.append(Bad(str(e)))
        return vals

    # ---- pass 1: source
    src: dict = {}
    dup_s: dict = {}
    empty_s: list = []
    n_src = 0
    groups: dict = {}
    s_tot = {c: Decimal(0) for c in sum_cols}
    s_bad = 0
    s_null = {c: 0 for c in cols}
    try:
        for line, row in rows(sreader, a.source, a.encoding_source):
            n_src += 1
            vals = expected_row(row)
            for c in cols:
                if vals[idx[c]] == "" and not isinstance(vals[idx[c]], Bad):
                    s_null[c] += 1
            g = str(vals[idx[a.group_by]]) if a.group_by else None
            if g is not None:
                gs = groups.setdefault(g, {"s_n": 0, "t_n": 0, "s": {c: Decimal(0) for c in sum_cols}, "t": {c: Decimal(0) for c in sum_cols}})
                gs["s_n"] += 1
            for c in sum_cols:
                v = vals[idx[c]]
                if isinstance(v, Bad) or v.strip() == "":
                    s_bad += isinstance(v, Bad)
                    continue
                try:
                    dv = parse_decimal(v)
                except TransformError:
                    s_bad += 1
                    continue
                s_tot[c] += dv
                if g is not None:
                    gs["s"][c] += dv
            key = tuple(str(vals[idx[k]]) for k in keys)
            if any(isinstance(vals[idx[k]], Bad) or vals[idx[k]].strip() == "" for k in keys):
                empty_s.append(line)
                continue
            if key in src:
                dup_s[key] = dup_s.get(key, 1) + 1
                continue
            src[key] = tuple(vals[idx[c]] for c in cols)
    finally:
        sfh.close()

    # ---- pass 2: target (stream); matched source entries are replaced by None to free memory
    MATCHED = None
    unexp: dict = {}
    dup_t: dict = {}
    empty_t: list = []
    n_tgt = 0
    t_tot = {c: Decimal(0) for c in sum_cols}
    t_bad = 0
    t_null = {c: 0 for c in cols}
    colstat = {c: {"compared": 0, "mismatches": 0, "transform_errors": 0, "accepted": 0, "examples": []} for c in cols}
    mism_keys = {c: [] for c in cols}
    matched = 0
    try:
        for line, row in rows(treader, a.target, a.encoding_target):
            n_tgt += 1
            for c in cols:
                if row.get(c, "").strip() == "":
                    t_null[c] += 1
            g = row.get(a.group_by, "") if a.group_by else None
            if g is not None:
                gs = groups.setdefault(g, {"s_n": 0, "t_n": 0, "s": {c: Decimal(0) for c in sum_cols}, "t": {c: Decimal(0) for c in sum_cols}})
                gs["t_n"] += 1
            for c in sum_cols:
                raw = row.get(c, "")
                if raw.strip() == "":
                    continue
                try:
                    v = parse_decimal(raw)
                except TransformError:
                    t_bad += 1
                    continue
                t_tot[c] += v
                if g is not None:
                    gs["t"][c] += v
            key = tuple(row.get(k, "") for k in keys)
            if any(k.strip() == "" for k in key):
                empty_t.append(line)
                continue
            if key in src:
                exp = src[key]
                if exp is MATCHED:
                    dup_t[key] = dup_t.get(key, 1) + 1
                    continue
                src[key] = MATCHED
                matched += 1
                ks = keystr(key)
                for i, c in enumerate(cols):
                    e, v = exp[i], row.get(c, "")
                    st = colstat[c]
                    st["compared"] += 1
                    if isinstance(e, Bad):
                        ok = False
                    elif plan[c]["numeric"]:
                        if e == "" or v.strip() == "":
                            ok = e == "" and v.strip() == ""
                        else:
                            try:
                                ok = abs(parse_decimal(v) - parse_decimal(e)) <= tol
                            except TransformError:
                                ok = False
                    else:
                        ok = e == v
                    if ok:
                        continue
                    if accepted("column", ks, c):
                        st["accepted"] += 1
                        continue
                    st["mismatches"] += 1
                    st["transform_errors"] += isinstance(e, Bad)
                    mism_keys[c].append(ks)
                    if len(st["examples"]) < a.max_examples:
                        st["examples"].append({"key": ks, "source": None, "expected": "⚠" if isinstance(e, Bad) else str(e), "target": v,
                                               "hint": diagnose(e, v, plan[c]["numeric"], t, plan[c]["codes"])})
            elif key in unexp:
                dup_t[key] = dup_t.get(key, 1) + 1
            else:
                unexp[key] = line
    finally:
        tfh.close()

    missing = [k for k, v in src.items() if v is not MATCHED]
    del src

    # ---- raw source values for the examples (second, cheap pass over the source)
    need = {ex["key"] for st in colstat.values() for ex in st["examples"]}
    if need:
        sfh, sreader, _ = open_reader(a.source, a.encoding_source, d_src)
        found = {}
        try:
            for _, row in rows(sreader, a.source, a.encoding_source):
                if len(found) >= len(need):
                    break
                vals = expected_row(row)
                ks = keystr(tuple(str(vals[idx[k]]) for k in keys))
                if ks in need and ks not in found:
                    found[ks] = row
        finally:
            sfh.close()
        for c, st in colstat.items():
            p = plan[c]
            for ex in st["examples"]:
                row = found.get(ex["key"], {})
                parts = [p["source"]] if p["source"] else []
                parts += [x for n, arg in p["ops"] if n == "concat" for x in arg[:-1]]
                ex["source"] = " + ".join(row.get(x, "") for x in parts) if parts else ""

    # ---- findings with accepted exceptions applied
    def filt(check, items):
        return [k for k in items if not accepted(check, keystr(k) if isinstance(k, tuple) else str(k))]

    f_missing = filt("missing", missing)
    f_unexp = filt("unexpected", list(unexp))
    f_dup_s = filt("duplicate_source", list(dup_s))
    f_dup_t = filt("duplicate_target", list(dup_t))
    f_empty = filt("empty_key", empty_s) + filt("empty_key", [f"target:{n}" for n in empty_t])

    totals = {}
    total_fail = 0
    for c in sum_cols:
        diff = t_tot[c] - s_tot[c]
        over = abs(diff) > total_tol
        acc = over and accepted("total", "", c, "")
        total_fail += over and not acc
        entry = {"source": fmt_dec(s_tot[c]), "target": fmt_dec(t_tot[c]), "difference": fmt_dec(diff),
                 "ok": not over, "accepted": acc, "groups": {}}
        for g in sorted(groups):
            gs = groups[g]
            gd = gs["t"][c] - gs["s"][c]
            gover = abs(gd) > total_tol
            gacc = gover and accepted("total", "", c, g)
            total_fail += gover and not gacc
            entry["groups"][g] = {"source": fmt_dec(gs["s"][c]), "target": fmt_dec(gs["t"][c]),
                                  "difference": fmt_dec(gd), "ok": not gover, "accepted": gacc}
        totals[c] = entry
    group_counts = {g: {"source": groups[g]["s_n"], "target": groups[g]["t_n"]} for g in sorted(groups)}

    unmapped = coverage["unmapped_source_columns"] if mapping else []
    unmapped_f = [c for c in unmapped if not accepted("unmapped_source", "", c)]
    field_total = sum(st["mismatches"] for st in colstat.values())
    rules = [
        ("r_empty", len(f_empty)), ("r_dup_s", len(f_dup_s)), ("r_dup_t", len(f_dup_t)),
        ("r_missing", len(f_missing)), ("r_unexp", len(f_unexp)), ("r_field", field_total),
        ("r_total", total_fail), ("r_tcol", len(coverage["absent_target_columns"])),
    ]
    if mapping:
        rules.append(("r_unmapped", len(unmapped_f)))
    rule_objs = [{"id": r, "rule": t[r], "value": v, "threshold": 0, "pass": v == 0} for r, v in rules]
    verdict = "PASS" if all(r["pass"] for r in rule_objs) else "FAIL"

    def lim(items):
        return [keystr(k) if isinstance(k, tuple) else str(k) for k in items[: a.max_examples]]

    near = 0
    if f_missing and f_unexp:
        norm = lambda s: s.strip().lstrip("0").casefold()  # noqa: E731
        um = {norm(keystr(k)) for k in f_unexp}
        near = sum(1 for k in f_missing if norm(keystr(k)) in um)

    return {
        "verdict": verdict,
        "lang": a.lang,
        "rules": rule_objs,
        "inputs": {"source": {"file": a.source, "encoding": a.encoding_source, "delimiter": d_src, "rows": n_src},
                   "target": {"file": a.target, "encoding": a.encoding_target, "delimiter": d_tgt, "rows": n_tgt},
                   "key": keys, "mapping": a.mapping, "tolerance": fmt_dec(tol), "total_tolerance": fmt_dec(total_tol)},
        "counts": {"source_rows": n_src, "target_rows": n_tgt, "source_distinct_keys": n_src - len(empty_s) - sum(v - 1 for v in dup_s.values()),
                   "target_distinct_keys": n_tgt - len(empty_t) - sum(v - 1 for v in dup_t.values()), "matched_keys": matched},
        "coverage": coverage,
        "empty_keys": {"count": len(f_empty), "rows": f_empty[: a.max_examples]},
        "duplicates": {"source": {"count": len(f_dup_s), "keys": lim(f_dup_s), "occurrences": {keystr(k): dup_s[k] for k in f_dup_s[: a.max_examples]}},
                       "target": {"count": len(f_dup_t), "keys": lim(f_dup_t), "occurrences": {keystr(k): dup_t[k] for k in f_dup_t[: a.max_examples]}}},
        "missing_in_target": {"count": len(f_missing), "keys": lim(f_missing)},
        "unexpected_in_target": {"count": len(f_unexp), "keys": lim(f_unexp), "near_matches": near},
        "columns": {c: {"rule": plan[c]["rule"], "source": " + ".join(plan[c]["needs"]), "numeric": plan[c]["numeric"],
                        **{k: v for k, v in colstat[c].items()}, "mismatch_keys": mism_keys[c][: a.max_examples]} for c in cols},
        "control_totals": totals,
        "group_by": a.group_by,
        "group_counts": group_counts,
        "unparseable": {"source": s_bad, "target": t_bad},
        "null_rates": {c: {"expected": pct(s_null[c], n_src), "target": pct(t_null[c], n_tgt),
                           "delta": round(pct(t_null[c], n_tgt) - pct(s_null[c], n_src), 2)} for c in cols},
        "accepted_exceptions": [{k: v for k, v in e.items()} for e in exceptions.values()],
    }


# ---------------------------------------------------------------- report
def render(res: dict) -> str:
    t = T[res["lang"]]
    ok = lambda b: "✅" if b else "❌"  # noqa: E731
    L = [f"# {t['title']}", "", f"**{t['verdict']}: {res['verdict']}**", "", f"## {t['rules']}",
         f"| {t['rule']} | {t['value']} | {t['threshold']} | {t['result']} |", "|---|---:|---:|:---:|"]
    L += [f"| {r['rule']} | {r['value']} | {r['threshold']} | {ok(r['pass'])} |" for r in res["rules"]]
    i, c = res["inputs"], res["counts"]
    L += ["", f"## {t['inputs']}", f"| | {t['file']} | {t['encoding']} | {t['delim']} | {t['rows']} | {t['distinct']} |",
          "|---|---|---|---|---:|---:|",
          f"| {t['source']} | {md(Path(i['source']['file']).name)} | {i['source']['encoding']} | {md(i['source']['delimiter'])} | {c['source_rows']} | {c['source_distinct_keys']} |",
          f"| {t['target']} | {md(Path(i['target']['file']).name)} | {i['target']['encoding']} | {md(i['target']['delimiter'])} | {c['target_rows']} | {c['target_distinct_keys']} |",
          "", f"{t['key']}: {', '.join(md(k) for k in i['key'])} · {t['matched']}: {c['matched_keys']} · "
          + t["legend"].format(tol=i["tolerance"])]
    cv = res["coverage"]
    L += ["", f"## {t['coverage']}"]
    for label, k in (("unmapped_src", "unmapped_source_columns"), ("not_migrated", "not_migrated"), ("implicit", "implicit_mappings"),
                     ("absent_tgt", "absent_target_columns"), ("unmapped_tgt", "unmapped_target_columns"), ("ignored", "ignored_target_columns")):
        L.append(f"- {t[label]}: " + (", ".join(md(x) for x in cv[k]) if cv[k] else t["none"]))

    def keylist(title, block, occ=None):
        out = ["", f"### {title} ({block['count']})"]
        if block["count"]:
            items = [md(k) + (f" ×{occ[k]}" if occ and k in occ else "") for k in block["keys"]]
            out.append(", ".join(items) + (" " + t["more"].format(n=block["count"] - len(block["keys"])) if block["count"] > len(block["keys"]) else ""))
        return out

    L += ["", f"## {t['keys']}"]
    L += keylist(t["dup_s"], res["duplicates"]["source"], res["duplicates"]["source"]["occurrences"])
    L += keylist(t["dup_t"], res["duplicates"]["target"], res["duplicates"]["target"]["occurrences"])
    L += keylist(t["missing"], res["missing_in_target"])
    L += keylist(t["unexp"], res["unexpected_in_target"])
    if res["unexpected_in_target"]["near_matches"]:
        L += ["", t["key_hint"].format(n=res["unexpected_in_target"]["near_matches"], m=res["unexpected_in_target"]["near_matches"])]
    if res["empty_keys"]["count"]:
        L += ["", f"### {t['empty_key']} ({res['empty_keys']['count']})", ", ".join(str(x) for x in res["empty_keys"]["rows"])]

    L += ["", f"## {t['fields']}", f"| {t['column']} | {t['rule_col']} | {t['compared']} | {t['mism']} | {t['terr']} | {t['acc']} |",
          "|---|---|---:|---:|---:|---:|"]
    for col, st in res["columns"].items():
        src = st["source"] or "-"
        L.append(f"| {md(col)} | {md(src)} {st['rule']} | {st['compared']} | {st['mismatches']} | {st['transform_errors']} | {st['accepted']} |")
    for col, st in res["columns"].items():
        if not st["examples"]:
            continue
        L += ["", f"### {md(col)} – {t['examples']} ({len(st['examples'])}/{st['mismatches']})",
              f"| {t['key']} | {t['src_val']} | {t['expected']} | {t['tgt_val']} | {t['hint']} |", "|---|---|---|---|---|"]
        L += [f"| {md(e['key'])} | {md(e['source'])} | {md(e['expected'])} | {md(e['target'])} | {e['hint']} |" for e in st["examples"]]

    if res["control_totals"] or res["group_counts"]:
        L += ["", f"## {t['totals']}"]
        for col, tot in res["control_totals"].items():
            L += ["", f"### {md(col)}", f"| {t['group']} | {t['source']} | {t['target']} | {t['diff']} | {t['result']} |", "|---|---:|---:|---:|:---:|",
                  f"| {t['total_all']} | {tot['source']} | {tot['target']} | {tot['difference']} | {ok(tot['ok'] or tot['accepted'])} |"]
            L += [f"| {md(g)} | {v['source']} | {v['target']} | {v['difference']} | {ok(v['ok'] or v['accepted'])} |" for g, v in tot["groups"].items()]
        if res["group_counts"]:
            L += ["", f"### {t['count']} – {md(res['group_by'])}", f"| {t['group']} | {t['source']} | {t['target']} | {t['diff']} |", "|---|---:|---:|---:|"]
            L += [f"| {md(g)} | {v['source']} | {v['target']} | {v['target'] - v['source']:+d} |".replace("+0 |", "0 |") for g, v in res["group_counts"].items()]
        if res["unparseable"]["source"] or res["unparseable"]["target"]:
            L += ["", t["unparsed"].format(s=res["unparseable"]["source"], t=res["unparseable"]["target"])]

    L += ["", f"## {t['nulls']}", f"| {t['column']} | {t['exp_null']} | {t['tgt_null']} | {t['delta']} |", "|---|---:|---:|---:|"]
    L += [f"| {md(col)} | {v['expected']} | {v['target']} | {('**' + format(v['delta'], '+g') + '**') if abs(v['delta']) >= 1 else format(v['delta'], 'g')} |"
          for col, v in res["null_rates"].items()]
    if res["accepted_exceptions"]:
        L += ["", f"## {t['accepted']}", f"| check | {t['key']} | {t['column']} | {t['group']} | {t['reason']} | {t['used']} |", "|---|---|---|---|---|---|"]
        L += [f"| {e['check']} | {md(e.get('key', ''))} | {md(e.get('column', ''))} | {md(e.get('group', ''))} | {e['reason']} | "
              f"{'✅' if e['observed'] else t['stale']} |" for e in res["accepted_exceptions"]]
    L += ["", f"## {t['classify']}"] + [f"- {x}" for x in t["classify_body"]]
    return "\n".join(L) + "\n"


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", required=True, help="source (legacy) extract CSV")
    ap.add_argument("--target", required=True, help="target (migrated) extract CSV")
    ap.add_argument("--key", required=True, help="key column(s) in the target, comma-separated (id or id,line_no)")
    ap.add_argument("--mapping", help="mapping.json with columns/transform ops (see above)")
    ap.add_argument("--sum", help="target columns for control totals, comma-separated (money: compared exactly)")
    ap.add_argument("--group-by", help="target column for per-group counts and control totals")
    ap.add_argument("--tolerance", default="0", help="absolute tolerance for numeric field comparison (default 0)")
    ap.add_argument("--total-tolerance", default="0", help="absolute tolerance for control totals (default 0)")
    ap.add_argument("--encoding-source", default="utf-8-sig", help="e.g. cp1254, iso-8859-9 (default utf-8-sig)")
    ap.add_argument("--encoding-target", default="utf-8-sig")
    ap.add_argument("--delimiter", default=",", help="CSV delimiter for both files (default ,)")
    ap.add_argument("--delimiter-source", help="override the delimiter for the source file (e.g. ';')")
    ap.add_argument("--delimiter-target", help="override the delimiter for the target file")
    ap.add_argument("--max-examples", type=int, default=20, help="examples/keys listed per finding (default 20)")
    ap.add_argument("--lang", choices=("tr", "en"), default="en")
    ap.add_argument("--out", required=True, help="Markdown report path")
    ap.add_argument("--json", help="optional JSON result path")
    a = ap.parse_args()
    for d in ("delimiter", "delimiter_source", "delimiter_target"):
        v = getattr(a, d)
        if v is not None:
            v = "\t" if v in ("\\t", "tab") else v
            if len(v) != 1:
                print(f"error: --{d.replace('_', '-')} must be one character", file=sys.stderr)
                return 2
            setattr(a, d, v)
    try:
        Decimal(str(a.tolerance)), Decimal(str(a.total_tolerance))
    except InvalidOperation:
        print("error: tolerances must be numbers like 0.005", file=sys.stderr)
        return 2
    try:
        res = reconcile(a)
    except UsageError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(render(res), encoding="utf-8", newline="\n")
    if a.json:
        Path(a.json).parent.mkdir(parents=True, exist_ok=True)
        Path(a.json).write_text(json.dumps(res, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    c = res["counts"]
    fails = [f"{r['rule']}={r['value']}" for r in res["rules"] if not r["pass"]]
    print(f"{res['verdict']}: source {c['source_rows']} rows, target {c['target_rows']} rows, matched {c['matched_keys']}"
          + (f"; failed: {'; '.join(fails)}" if fails else "") + f" -> {a.out}")
    return 0 if res["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
