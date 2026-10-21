#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
design_grader.py - objective grader for evals/trial-design (SFM v1.4 test-design trial).

Evaluator-only. Do NOT give this file to the agent under test.

Usage:
    python design_grader.py <cikti_dir> [--json OUT.json] [--verbose]
    python design_grader.py --selftest           # oracle sanity checks against the spec's Ek-A

<cikti_dir> must contain (missing files simply score 0 for the related items):
    fiyat-test-verisi.csv, durum-gecis-testleri.csv, konfigurasyon-matrisi.csv, test-tasarimi.md

What it does:
  * Re-computes the correct expected result of every pricing row and every state-transition row
    with a reference oracle (spec DK-SPEC-214 v1.4) and counts oracle errors (= false positives).
  * Checks the planted test conditions K1..K12 (see design.md) on CORRECT rows only.
  * Checks pairwise coverage (all feasible value pairs) and constraint violations.
  * Heuristically looks for the Ek-A "Örnek 4" finding (K11c) and for false claims that a correct
    Ek-A example is wrong (T4). These two are marked MANUAL - the grader must confirm them.

Python 3 stdlib only.
"""
import argparse
import csv
import io
import itertools
import json
import os
import re
import sys
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation

# --------------------------------------------------------------------------------------------
# Normalisation helpers
# --------------------------------------------------------------------------------------------
_TR = str.maketrans({
    "ç": "c", "Ç": "C", "ğ": "g", "Ğ": "G", "ı": "i", "İ": "I", "ö": "o", "Ö": "O",
    "ş": "s", "Ş": "S", "ü": "u", "Ü": "U", "â": "a", "Â": "A", "î": "i", "Î": "I",
    "û": "u", "Û": "U",
})


def fold(s):
    """Lenient code normalisation: Turkish letters -> ASCII, upper case, spaces/dashes -> '_'."""
    s = (s or "").strip().translate(_TR).upper()
    s = re.sub(r"[\s\-]+", "_", s)
    return s


def read_text(path):
    with open(path, "rb") as f:
        raw = f.read()
    for enc in ("utf-8-sig", "cp1254", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def read_csv(path):
    """Return list of dict rows with normalised header keys. Delimiter auto-detected."""
    text = read_text(path)
    lines = [ln for ln in text.splitlines() if ln.strip()]
    if not lines:
        return [], []
    header = lines[0]
    counts = {d: header.count(d) for d in (";", ",", "\t", "|")}
    delim = max(counts, key=counts.get)
    reader = csv.reader(io.StringIO("\n".join(lines)), delimiter=delim)
    rows = list(reader)
    keys = [re.sub(r"[^a-z0-9_]", "", fold(h).lower()) for h in rows[0]]
    out = []
    for r in rows[1:]:
        if not any(c.strip() for c in r):
            continue
        d = {}
        for i, k in enumerate(keys):
            d[k] = r[i].strip() if i < len(r) else ""
        out.append(d)
    return keys, out


C = Decimal("0.01")


def parse_amount_lenient(s):
    """Parse an amount written in any common style: 1499.90 / 1499,90 / 1.499,90 / 1,499.90 / '149,99 TL'."""
    if s is None:
        return None
    t = s.strip()
    if t in ("", "-", "—", "N/A", "n/a", "YOK", "yok"):
        return None
    t = re.sub(r"[^\d,.\-]", "", t)
    if not t or t in ("-", ".", ","):
        return None
    if "," in t and "." in t:
        if t.rfind(",") > t.rfind("."):
            t = t.replace(".", "").replace(",", ".")
        else:
            t = t.replace(",", "")
    elif "," in t:
        t = t.replace(",", ".")
    try:
        return Decimal(t)
    except InvalidOperation:
        return None


def parse_int_lenient(s):
    v = parse_amount_lenient(s)
    if v is None:
        return None
    if v != v.to_integral_value():
        return v  # keep the fraction -> will mismatch
    return int(v)


# --------------------------------------------------------------------------------------------
# Reference oracle: pricing (spec sections 3-9)
# --------------------------------------------------------------------------------------------
UYELIK = ("MISAFIR", "KLASIK", "ALTIN")
TESLIMAT = ("STANDART", "HIZLI", "MAGAZA")
BOLGE = ("NORMAL", "UZAK")
ODEME = ("KREDI_KARTI", "BANKA_KARTI", "KAPIDA_ODEME", "CEPPAY")
KUPONLAR = ("DEFNE10", "KITAP50")
AT_RE = re.compile(r"^\d+(\.\d{1,2})?$")


def price(uyelik, ara_toplam, kupon, teslimat, bolge, odeme):
    """All args are raw strings exactly as they would be sent to SFM.
    Returns dict: durum + (if KABUL) ki, nt, ku, hb, ot, puan.  Always carries 'calc' (pre-limit
    amounts) when the computation reached the amount stage, for K-checks (e.g. OT before limit)."""
    uyelik = (uyelik or "").strip()
    teslimat = (teslimat or "").strip()
    bolge = (bolge or "").strip()
    odeme = (odeme or "").strip()
    s = (ara_toplam or "").strip()
    if uyelik not in UYELIK or teslimat not in TESLIMAT or odeme not in ODEME:
        return {"durum": "ERR_GECERSIZ_GIRDI"}
    if teslimat in ("STANDART", "HIZLI") and bolge not in BOLGE:
        return {"durum": "ERR_GECERSIZ_GIRDI"}
    if not AT_RE.match(s):
        return {"durum": "ERR_GECERSIZ_GIRDI"}
    at = Decimal(s)
    if at <= 0:
        return {"durum": "ERR_GECERSIZ_GIRDI"}
    k = (kupon or "").strip()
    if k not in ("",) + KUPONLAR:
        return {"durum": "ERR_KUPON_GECERSIZ"}
    if at < Decimal("150.00"):
        return {"durum": "ERR_MIN_SEPET", "at": at}
    if at > Decimal("20000.00"):
        return {"durum": "ERR_MAX_SEPET", "at": at}
    if teslimat == "HIZLI" and bolge == "UZAK":
        return {"durum": "ERR_TESLIMAT_BOLGE", "at": at}
    if odeme == "KAPIDA_ODEME" and teslimat != "STANDART":
        return {"durum": "ERR_KAPIDA_UYGUNLUK", "at": at}

    ki = Decimal("0.00")
    raw_pct = None
    if k == "DEFNE10":
        raw_pct = (at * Decimal("0.10")).quantize(C, rounding=ROUND_HALF_UP)
        ki = min(raw_pct, Decimal("150.00"))
    elif k == "KITAP50" and uyelik in ("KLASIK", "ALTIN") and at >= Decimal("400.00"):
        ki = Decimal("50.00")
    nt = at - ki

    if teslimat == "MAGAZA":
        ku = Decimal("0.00")
    elif teslimat == "HIZLI":
        ku = Decimal("40.00") if nt >= Decimal("750.00") else Decimal("79.90")
    else:  # STANDART
        if uyelik == "ALTIN":
            ku = Decimal("0.00")
        else:
            ku = Decimal("0.00") if nt >= Decimal("750.00") else Decimal("39.90")
            if bolge == "UZAK":
                ku += Decimal("25.00")
    hb = Decimal("12.90") if odeme == "KAPIDA_ODEME" else Decimal("0.00")
    ot = nt + ku + hb
    base = int(nt // 10)
    if uyelik == "MISAFIR":
        puan = 0
    elif uyelik == "KLASIK":
        puan = base
    else:
        puan = (base * 3) // 2
    calc = {"at": at, "ki": ki, "nt": nt, "ku": ku, "hb": hb, "ot": ot, "puan": puan,
            "raw_pct": raw_pct, "kupon": k, "base": base}
    if odeme == "KAPIDA_ODEME" and ot > Decimal("5000.00"):
        return {"durum": "ERR_KAPIDA_LIMIT", "calc": calc, "at": at}
    res = {"durum": "KABUL", "calc": calc, "at": at}
    res.update({"ki": ki, "nt": nt, "ku": ku, "hb": hb, "ot": ot, "puan": puan})
    return res


# --------------------------------------------------------------------------------------------
# Reference oracle: order lifecycle (spec section 10)
# --------------------------------------------------------------------------------------------
EVENTS = ("ODEME_BASARILI", "ODEME_BASARISIZ", "ZAMAN_ASIMI", "IPTAL", "HAZIRLAMAYA_BASLA",
          "KARGOYA_VER", "TESLIM_BASARILI", "TESLIM_BASARISIZ", "YENIDEN_DAGITIM", "IADE_TALEBI",
          "IADE_ONAY", "IADE_RED")
STATES = ("ODEME_BEKLENIYOR", "ONAYLANDI", "HAZIRLANIYOR", "KARGODA", "TESLIM_EDILEMEDI",
          "TESLIM_EDILDI", "IADE_TALEP_EDILDI", "IADE_EDILDI", "IPTAL_EDILDI", "DEPOYA_DONDU")
TERMINAL = ("IADE_EDILDI", "IPTAL_EDILDI", "DEPOYA_DONDU")
TABLE = {
    "ODEME_BEKLENIYOR": ("ODEME_BASARILI", "ODEME_BASARISIZ", "ZAMAN_ASIMI", "IPTAL"),
    "ONAYLANDI": ("IPTAL", "HAZIRLAMAYA_BASLA"),
    "HAZIRLANIYOR": ("IPTAL", "KARGOYA_VER"),
    "KARGODA": ("TESLIM_BASARILI", "TESLIM_BASARISIZ"),
    "TESLIM_EDILEMEDI": ("YENIDEN_DAGITIM",),
    "TESLIM_EDILDI": ("IADE_TALEBI",),
    "IADE_TALEP_EDILDI": ("IADE_ONAY", "IADE_RED"),
}
SIMPLE_NEXT = {
    ("ODEME_BEKLENIYOR", "ODEME_BASARILI"): "ONAYLANDI",
    ("ODEME_BEKLENIYOR", "ODEME_BASARISIZ"): "ODEME_BEKLENIYOR",
    ("ODEME_BEKLENIYOR", "ZAMAN_ASIMI"): "IPTAL_EDILDI",
    ("ONAYLANDI", "HAZIRLAMAYA_BASLA"): "HAZIRLANIYOR",
    ("HAZIRLANIYOR", "KARGOYA_VER"): "KARGODA",
    ("KARGODA", "TESLIM_BASARILI"): "TESLIM_EDILDI",
    ("TESLIM_EDILEMEDI", "YENIDEN_DAGITIM"): "KARGODA",
    ("IADE_TALEP_EDILDI", "IADE_ONAY"): "IADE_EDILDI",
    ("IADE_TALEP_EDILDI", "IADE_RED"): "TESLIM_EDILDI",
}


def new_order(odeme):
    o = (odeme or "").strip()
    if o not in ODEME:
        return None
    return {"state": "ONAYLANDI" if o == "KAPIDA_ODEME" else "ODEME_BEKLENIYOR",
            "fails": 0, "iade_red": False}


def apply_event(ctx, ev, params):
    """Mutates ctx on success. Returns result code (KABUL or ERR_*)."""
    st = ctx["state"]
    if ev not in EVENTS:
        return "ERR_GECERSIZ_GIRDI"
    if ev not in TABLE.get(st, ()):
        return "ERR_GECERSIZ_GECIS"
    if ev == "IPTAL":
        aktor = params.get("AKTOR")
        if aktor not in ("MUSTERI", "OPERATOR"):
            return "ERR_GECERSIZ_GIRDI"
        if st == "HAZIRLANIYOR" and aktor != "OPERATOR":
            return "ERR_GECERSIZ_GECIS"
        ctx["state"] = "IPTAL_EDILDI"
        return "KABUL"
    if ev == "IADE_TALEBI":
        g = params.get("GUN")
        if g is None or not re.fullmatch(r"\d+", g):
            return "ERR_GECERSIZ_GIRDI"
        if int(g) > 14:
            return "ERR_IADE_SURESI"
        if ctx["iade_red"]:
            return "ERR_IADE_TEKRAR"
        ctx["state"] = "IADE_TALEP_EDILDI"
        return "KABUL"
    if ev == "TESLIM_BASARISIZ":
        ctx["fails"] += 1
        ctx["state"] = "DEPOYA_DONDU" if ctx["fails"] >= 3 else "TESLIM_EDILEMEDI"
        return "KABUL"
    if ev == "IADE_RED":
        ctx["iade_red"] = True
    ctx["state"] = SIMPLE_NEXT[(st, ev)]
    return "KABUL"


DEFAULT_PARAM = {"IPTAL": "AKTOR", "IADE_TALEBI": "GUN"}
SEQ_SPLIT = re.compile(r"\s*(?:->|=>|→|>|\|)\s*")
EV_RE = re.compile(r"^\s*([^\(\)]+?)\s*(?:\((.*)\))?\s*$")


def parse_sequence(text):
    """Returns list of (event, params) or raises ValueError."""
    t = (text or "").strip()
    if t in ("", "-", "—"):
        return []
    out = []
    for tok in SEQ_SPLIT.split(t):
        if not tok.strip():
            continue
        m = EV_RE.match(tok)
        if not m:
            raise ValueError("parse: %r" % tok)
        name = fold(m.group(1))
        params = {}
        if m.group(2) is not None and m.group(2).strip():
            for part in m.group(2).split(","):
                part = part.strip()
                if not part:
                    continue
                if "=" in part or ":" in part:
                    k, v = re.split(r"[=:]", part, maxsplit=1)
                    params[fold(k)] = fold(v) if fold(k) != "GUN" else v.strip()
                else:
                    key = DEFAULT_PARAM.get(name, "_")
                    params[key] = fold(part) if key != "GUN" else part.strip()
        out.append((name, params))
    return out


# --------------------------------------------------------------------------------------------
# Pairwise model (spec section 11)
# --------------------------------------------------------------------------------------------
PW_FACTORS = [
    ("platform", ("WEB", "IOS", "ANDROID")),
    ("odeme_yontemi", ODEME),
    ("teslimat_tipi", TESLIMAT),
    ("uyelik", UYELIK),
]


def pw_violation(c):
    p, o, t, u = c
    v = []
    if o == "KAPIDA_ODEME" and t != "STANDART":
        v.append("KS-1")
    if o == "CEPPAY" and p == "WEB":
        v.append("KS-2")
    if o == "CEPPAY" and u == "MISAFIR":
        v.append("KS-3")
    return v


def feasible_pairs():
    combos = [c for c in itertools.product(*[vals for _, vals in PW_FACTORS]) if not pw_violation(c)]
    pairs = set()
    for c in combos:
        for i, j in itertools.combinations(range(4), 2):
            pairs.add((i, c[i], j, c[j]))
    return combos, pairs


# --------------------------------------------------------------------------------------------
# Grading
# --------------------------------------------------------------------------------------------
PRICE_FIELDS = [("beklenen_kupon_indirimi", "ki"), ("beklenen_net_tutar", "nt"),
                ("beklenen_kargo", "ku"), ("beklenen_hizmet_bedeli", "hb"),
                ("beklenen_odenecek", "ot"), ("beklenen_puan", "puan")]


def lenient_inputs(row, exp_durum):
    """Return the raw input strings to feed the oracle, plus format warnings.
    Strict spec format is honoured when the row expects ERR_GECERSIZ_GIRDI (intentional bad input);
    otherwise obviously-intended values (e.g. 'Klasik', '1.499,90') are normalised with a warning."""
    warn = []
    vals = {}
    for col, allowed in (("uyelik", UYELIK), ("teslimat_tipi", TESLIMAT), ("bolge", BOLGE),
                         ("odeme_yontemi", ODEME)):
        raw = row.get(col, "")
        if raw.strip() in allowed or exp_durum == "ERR_GECERSIZ_GIRDI":
            vals[col] = raw
        elif fold(raw) in allowed:
            vals[col] = fold(raw)
            warn.append("%s=%r normalised" % (col, raw))
        else:
            vals[col] = raw
    raw_at = row.get("ara_toplam", "")
    if AT_RE.match(raw_at.strip()) or exp_durum == "ERR_GECERSIZ_GIRDI":
        vals["ara_toplam"] = raw_at
    else:
        v = parse_amount_lenient(raw_at)
        if v is not None and v == v.quantize(C) and v > 0:
            vals["ara_toplam"] = format(v.quantize(C), "f")
            warn.append("ara_toplam=%r normalised" % raw_at)
        else:
            vals["ara_toplam"] = raw_at
    k = row.get("kupon", "")
    if k.strip() in ("-", "—", "YOK", "yok", "Yok"):
        k = ""
    vals["kupon"] = k
    return vals, warn


def is_example(tid):
    return fold(tid).startswith("ORNEK")


def grade_pricing(path, verbose=False):
    res = {"file": path, "present": os.path.exists(path), "rows": 0, "errors": [], "warnings": [],
           "correct": []}
    if not res["present"]:
        return res
    _, rows = read_csv(path)
    for row in rows:
        tid = row.get("test_id", "")
        if is_example(tid):
            continue
        res["rows"] += 1
        exp_durum = fold(row.get("beklenen_durum", ""))
        vals, warn = lenient_inputs(row, exp_durum)
        o = price(vals["uyelik"], vals["ara_toplam"], vals["kupon"], vals["teslimat_tipi"],
                  vals["bolge"], vals["odeme_yontemi"])
        for w in warn:
            res["warnings"].append("%s: %s" % (tid, w))
        mism = []
        missing = []
        if exp_durum != o["durum"]:
            mism.append("durum: beklenen %s, dogru %s" % (exp_durum or "<bos>", o["durum"]))
        elif o["durum"] == "KABUL":
            for col, key in PRICE_FIELDS:
                raw = row.get(col, "")
                if key == "puan":
                    v = parse_int_lenient(raw)
                else:
                    v = parse_amount_lenient(raw)
                if v is None:
                    missing.append(col)
                    continue
                if key == "puan":
                    if v != o["puan"]:
                        mism.append("%s: %s != %s" % (col, raw, o["puan"]))
                else:
                    if Decimal(v).quantize(C) != o[key]:
                        mism.append("%s: %s != %s" % (col, raw, o[key]))
        if missing:
            res["warnings"].append("%s: bos beklenen kolon(lar) %s" % (tid, ",".join(missing)))
        info = {"id": tid, "row": row, "vals": vals, "oracle": o, "missing": missing}
        if mism:
            info["mismatch"] = mism
            info["traps"] = pricing_trap_tags(vals, o, row)
            res["errors"].append(info)
        else:
            res["correct"].append(info)
    return res


def pricing_trap_tags(vals, o, row):
    tags = []
    calc = o.get("calc") or {}
    if o["durum"] in ("KABUL", "ERR_KAPIDA_LIMIT") and calc:
        # T1: AT >= 150 but NT < 150 (min basket is checked on AT)
        if calc["at"] >= Decimal("150.00") and calc["nt"] < Decimal("150.00"):
            tags.append("T1")
    if o["durum"] == "KABUL":
        # T2: ALTIN + HIZLI pays the HIZLI fee (40.00 / 79.90)
        if vals["uyelik"].strip() == "ALTIN" and vals["teslimat_tipi"].strip() == "HIZLI":
            tags.append("T2")
        # T3: KAPIDA HB 12.90 always charged, never part of points
        if vals["odeme_yontemi"].strip() == "KAPIDA_ODEME":
            hb = parse_amount_lenient(row.get("beklenen_hizmet_bedeli", ""))
            pu = parse_int_lenient(row.get("beklenen_puan", ""))
            if (hb is not None and hb != Decimal("12.90")) or (pu is not None and pu != o["puan"]):
                tags.append("T3")
    return tags


def grade_states(path):
    res = {"file": path, "present": os.path.exists(path), "rows": 0, "errors": [], "warnings": [],
           "correct": []}
    if not res["present"]:
        return res
    _, rows = read_csv(path)
    for row in rows:
        tid = row.get("test_id", "")
        if is_example(tid):
            continue
        res["rows"] += 1
        odeme_raw = row.get("odeme_yontemi", "")
        odeme = odeme_raw.strip() if odeme_raw.strip() in ODEME else fold(odeme_raw)
        if odeme not in ODEME:
            if odeme_raw.strip() == "":
                odeme = "KREDI_KARTI"
                res["warnings"].append("%s: odeme_yontemi bos, KREDI_KARTI varsayildi" % tid)
        exp_res = fold(row.get("beklenen_son_olay_sonucu", ""))
        exp_state = fold(row.get("beklenen_son_durum", ""))
        info = {"id": tid, "row": row}
        try:
            seq = parse_sequence(row.get("olay_dizisi", ""))
        except ValueError as e:
            info["mismatch"] = ["olay_dizisi ayristirilamadi: %s" % e]
            res["errors"].append(info)
            continue
        if seq and (seq[0][0].startswith("SIPARIS_OLUSTUR") or seq[0][0] in ("OLUSTUR", "CREATE", "SIPARIS")):
            seq = seq[1:]  # tolerated: explicit creation step although the format says it is implicit
            res["warnings"].append("%s: bastaki siparis olusturma adimi yok sayildi" % tid)
        ctx = new_order(odeme)
        if ctx is None:
            last_res, pre_state, pre_ctx, last = "ERR_GECERSIZ_GIRDI", None, None, None
            prefix_ok = len(seq) == 0
            final_state = None
        else:
            prefix_ok = True
            for i, (ev, params) in enumerate(seq[:-1]):
                r = apply_event(ctx, ev, params)
                if r != "KABUL":
                    prefix_ok = False
                    info["mismatch"] = ["on kosul olayi #%d %s gecersiz (%s, durum %s)" %
                                        (i + 1, ev, r, ctx["state"])]
                    break
            if not prefix_ok:
                res["errors"].append(info)
                continue
            pre_ctx = dict(ctx)
            pre_state = ctx["state"]
            if seq:
                last = seq[-1]
                last_res = apply_event(ctx, last[0], last[1])
            else:
                last = None
                last_res = "KABUL"
            final_state = ctx["state"]
        mism = []
        if exp_res != last_res:
            mism.append("sonuc: beklenen %s, dogru %s" % (exp_res or "<bos>", last_res))
        if exp_state:
            if final_state is not None and exp_state != final_state:
                mism.append("durum: beklenen %s, dogru %s" % (exp_state, final_state))
        else:
            res["warnings"].append("%s: beklenen_son_durum bos" % tid)
        info.update({"pre_state": pre_state, "pre_ctx": pre_ctx, "last": last,
                     "result": last_res, "final": final_state, "odeme": odeme,
                     "state_filled": bool(exp_state)})
        if mism:
            info["mismatch"] = mism
            res["errors"].append(info)
        else:
            res["correct"].append(info)
    return res


def grade_pairwise(path):
    res = {"file": path, "present": os.path.exists(path), "rows": 0, "violations": [],
           "unknown": [], "coverage": 0.0, "missing_pairs": []}
    combos, feas = feasible_pairs()
    res["feasible_pairs"] = len(feas)
    res["valid_combos"] = len(combos)
    if not res["present"]:
        return res
    _, rows = read_csv(path)
    covered = set()
    for row in rows:
        tid = row.get("test_id", "")
        if is_example(tid):
            continue
        res["rows"] += 1
        c = []
        bad = False
        for col, vals in PW_FACTORS:
            v = fold(row.get(col, ""))
            if v not in vals:
                bad = True
            c.append(v)
        if bad:
            res["unknown"].append(tid)
            continue
        c = tuple(c)
        v = pw_violation(c)
        if v:
            res["violations"].append("%s %s %s" % (tid, "/".join(c), ",".join(v)))
            continue
        for i, j in itertools.combinations(range(4), 2):
            covered.add((i, c[i], j, c[j]))
    miss = sorted(feas - covered)
    res["coverage"] = round(100.0 * (len(feas) - len(miss)) / len(feas), 1)
    res["missing_pairs"] = ["%s=%s & %s=%s" % (PW_FACTORS[i][0], a, PW_FACTORS[j][0], b)
                            for i, a, j, b in miss]
    return res


EX_WORD = r"\b(?:ornek|orn\.?|ex(?:ample)?|ek[\s\-_]?a[\s\-_]*(?:#|no\.?|satir)?)"
DEFECT_WORDS = re.compile(
    r"(hata|yanlis|celis|tutarsiz|uyusm|uymuyor|uymamakta|dogru degil|olmali|olmasi gerek|"
    r"inconsisten|contradict|wrong|incorrect|error|defect|bug|mismatch)", re.I)
EX4_EXTRA = re.compile(r"(25[.,]00|925[.,]00|\b925\b|6\.5)")


def grade_report(path):
    """Heuristic only - every hit is printed for MANUAL confirmation by the grader.
    Ex4 (true finding, K11c): example reference on a line, defect wording or the correct values
    (25,00 / 925,00 / rule 6.5) on the same or the next line.
    Ex1/2/3/5 (possible T4 false claim): example reference AND defect wording on the SAME line."""
    res = {"file": path, "present": os.path.exists(path), "ex_flags": {}}
    if not res["present"]:
        return res
    text = read_text(path)
    lines = [ln.translate(_TR).lower() for ln in text.splitlines()]
    for n in (1, 2, 3, 4, 5):
        pat = re.compile(EX_WORD + r"[\s\-#:]*" + str(n) + r"(?!\d|[.,]\d)", re.I)
        hits = []
        for i, ln in enumerate(lines):
            if not pat.search(ln):
                continue
            if n == 4:
                window = " ".join(lines[i: i + 2])
                ok = DEFECT_WORDS.search(window) or EX4_EXTRA.search(window)
            else:
                ok = DEFECT_WORDS.search(ln)
            if ok:
                hits.append("L%d: %s" % (i + 1, ln.strip()[:220]))
        res["ex_flags"][n] = hits
    return res


def score(pr, stt, pw, rep):
    K = {}
    D = Decimal
    good = pr["correct"] if pr["present"] else []

    def prow(pred):
        return [r for r in good if pred(r)]

    def v(r, k):
        return r["vals"][k].strip()

    def filled(r, *cols):
        return all(c not in r["missing"] for c in cols)

    # K1 sepet limitleri (AT)
    a1 = prow(lambda r: r["oracle"]["durum"] == "ERR_MIN_SEPET" and r["oracle"]["at"] == D("149.99"))
    a2 = prow(lambda r: r["oracle"]["durum"] == "KABUL" and r["oracle"]["at"] == D("150.00"))
    b1 = prow(lambda r: r["oracle"]["durum"] == "KABUL" and r["oracle"]["at"] == D("20000.00"))
    b2 = prow(lambda r: r["oracle"]["durum"] == "ERR_MAX_SEPET" and r["oracle"]["at"] == D("20000.01"))
    K["K1"] = {"max": 2, "sub": {"min 149.99/150.00": 1 if (a1 and a2) else 0,
                                  "max 20000.00/20000.01": 1 if (b1 and b2) else 0}}

    # K2 KITAP50 kosul siniri (uye)
    def kitap(at_, ki_):
        return prow(lambda r: r["oracle"]["durum"] == "KABUL" and v(r, "kupon") == "KITAP50"
                    and v(r, "uyelik") in ("KLASIK", "ALTIN") and r["oracle"]["at"] == D(at_)
                    and r["oracle"]["ki"] == D(ki_) and filled(r, "beklenen_kupon_indirimi"))
    K["K2"] = {"max": 2, "sub": {"399.99 -> KI 0.00": 1 if kitap("399.99", "0.00") else 0,
                                  "400.00 -> KI 50.00": 1 if kitap("400.00", "50.00") else 0}}

    # K4 kombinasyon hatalari
    k4a = prow(lambda r: r["oracle"]["durum"] == "ERR_TESLIMAT_BOLGE")
    k4b = prow(lambda r: r["oracle"]["durum"] == "ERR_KAPIDA_UYGUNLUK")
    K["K4"] = {"max": 2, "sub": {"HIZLI+UZAK -> ERR_TESLIMAT_BOLGE": 1 if k4a else 0,
                                  "KAPIDA+HIZLI/MAGAZA -> ERR_KAPIDA_UYGUNLUK": 1 if k4b else 0}}

    # K5 DEFNE10 tavan + yarim-yukari yuvarlama
    k5a = prow(lambda r: r["oracle"]["durum"] == "KABUL" and v(r, "kupon") == "DEFNE10"
               and r["oracle"]["calc"]["raw_pct"] > D("150.00") and filled(r, "beklenen_kupon_indirimi"))
    k5b = prow(lambda r: r["oracle"]["durum"] == "KABUL" and v(r, "kupon") == "DEFNE10"
               and (r["oracle"]["at"] * 1000) % 100 == 50 and r["oracle"]["calc"]["raw_pct"] <= D("150.00")
               and filled(r, "beklenen_kupon_indirimi"))
    K["K5"] = {"max": 3, "sub": {"tavan: %10 > 150.00 iken KI = 150.00": 2 if k5a else 0,
                                  "yarim-yukari yuvarlama (x,xx5)": 1 if k5b else 0}}

    # K6 puan
    k6a = prow(lambda r: r["oracle"]["durum"] == "KABUL" and v(r, "uyelik") == "ALTIN"
               and r["oracle"]["calc"]["base"] % 2 == 1 and filled(r, "beklenen_puan"))
    k6b = prow(lambda r: r["oracle"]["durum"] == "KABUL" and v(r, "uyelik") in ("KLASIK", "ALTIN")
               and r["oracle"]["ki"] > 0 and int(r["oracle"]["at"] // 10) != r["oracle"]["calc"]["base"]
               and filled(r, "beklenen_puan"))
    K["K6"] = {"max": 3, "sub": {"ALTIN tek taban puan, asagi yuvarlama": 2 if k6a else 0,
                                  "puan NT uzerinden (kuponlu)": 1 if k6b else 0}}

    # K9 turetilmis ucretsiz kargo siniri (NT 750.00 / 749.99, kupon uygulanmis)
    def k9(nt_):
        return prow(lambda r: r["oracle"]["durum"] == "KABUL" and r["oracle"]["ki"] > 0
                    and r["oracle"]["nt"] == D(nt_)
                    and ((v(r, "teslimat_tipi") == "STANDART" and v(r, "uyelik") != "ALTIN")
                         or v(r, "teslimat_tipi") == "HIZLI")
                    and filled(r, "beklenen_kargo"))
    K["K9"] = {"max": 4, "sub": {"NT=750.00 (kuponlu) dogru kargo": 2 if k9("750.00") else 0,
                                  "NT=749.99 (kuponlu) dogru kargo": 2 if k9("749.99") else 0}}

    # K10 kapida OT limiti (HB dahil)
    k10a = prow(lambda r: r["oracle"]["durum"] == "KABUL" and v(r, "odeme_yontemi") == "KAPIDA_ODEME"
                and r["oracle"]["ot"] == D("5000.00") and filled(r, "beklenen_odenecek"))
    k10b = prow(lambda r: r["oracle"]["durum"] == "ERR_KAPIDA_LIMIT"
                and r["oracle"]["calc"]["ot"] == D("5000.01"))
    K["K10"] = {"max": 4, "sub": {"KAPIDA OT=5000.00 -> KABUL": 2 if k10a else 0,
                                   "KAPIDA OT=5000.01 -> ERR_KAPIDA_LIMIT": 2 if k10b else 0}}

    # K11 uzak bolge x 750 etkilesimi + Altin karsiti + Ek-A Ornek 4
    k11a = prow(lambda r: r["oracle"]["durum"] == "KABUL" and v(r, "teslimat_tipi") == "STANDART"
                and v(r, "uyelik") != "ALTIN" and v(r, "bolge") == "UZAK"
                and r["oracle"]["nt"] >= D("750.00") and filled(r, "beklenen_kargo"))
    k11b = prow(lambda r: r["oracle"]["durum"] == "KABUL" and v(r, "teslimat_tipi") == "STANDART"
                and v(r, "uyelik") == "ALTIN" and v(r, "bolge") == "UZAK" and filled(r, "beklenen_kargo"))
    ex4 = bool(rep.get("ex_flags", {}).get(4)) if rep["present"] else False
    K["K11"] = {"max": 4, "sub": {"UZAK+NT>=750 (ALTIN degil) -> KU 25.00": 2 if k11a else 0,
                                   "UZAK+ALTIN -> KU 0.00": 1 if k11b else 0,
                                   "Ek-A Ornek 4 celiskisi raporlandi [MANUEL ONAY]": 1 if ex4 else 0}}

    # ---- state machine
    sg = stt["correct"] if stt["present"] else []

    def srow(pred):
        return [r for r in sg if r.get("last") is not None and r.get("state_filled") and pred(r)]

    k3a = srow(lambda r: r["result"] == "ERR_GECERSIZ_GECIS" and r["pre_state"] not in TERMINAL
               and not (r["pre_state"] == "HAZIRLANIYOR" and r["last"][0] == "IPTAL"))
    k3b = srow(lambda r: r["result"] == "ERR_GECERSIZ_GECIS" and r["pre_state"] in TERMINAL)
    K["K3"] = {"max": 2, "sub": {"son-olmayan durumda gecersiz gecis": 1 if k3a else 0,
                                  "son durumda olay reddi": 1 if k3b else 0}}

    k7a = srow(lambda r: r["pre_state"] == "HAZIRLANIYOR" and r["last"][0] == "IPTAL"
               and r["last"][1].get("AKTOR") == "MUSTERI" and r["result"] == "ERR_GECERSIZ_GECIS")
    k7b = srow(lambda r: r["pre_state"] == "HAZIRLANIYOR" and r["last"][0] == "IPTAL"
               and r["last"][1].get("AKTOR") == "OPERATOR" and r["result"] == "KABUL")
    K["K7"] = {"max": 3, "sub": {"HAZIRLANIYOR + IPTAL(MUSTERI) -> ERR": 2 if k7a else 0,
                                  "HAZIRLANIYOR + IPTAL(OPERATOR) -> IPTAL_EDILDI": 1 if k7b else 0}}

    def iade(g, rr):
        return srow(lambda r: r["pre_state"] == "TESLIM_EDILDI" and r["last"][0] == "IADE_TALEBI"
                    and r["last"][1].get("GUN") == g and not r["pre_ctx"]["iade_red"] and r["result"] == rr)
    K["K8"] = {"max": 3, "sub": {"IADE_TALEBI(gun=14) -> KABUL": 1 if iade("14", "KABUL") else 0,
                                  "IADE_TALEBI(gun=15) -> ERR_IADE_SURESI": 2 if iade("15", "ERR_IADE_SURESI") else 0}}

    # ---- pairwise
    if pw["present"] and pw["rows"]:
        full = pw["coverage"] == 100.0
        noviol = not pw["violations"]
        if full and noviol and pw["rows"] <= 20:
            k12 = 4
        elif (full and noviol) or (pw["coverage"] >= 90.0 and noviol):
            k12 = 2
        else:
            k12 = 0
    else:
        k12 = 0
    K["K12"] = {"max": 4, "sub": {"pairwise kapsam %s%%, ihlal %d, satir %d" % (
        pw.get("coverage"), len(pw.get("violations", [])), pw.get("rows", 0)): k12}}

    order = ["K%d" % i for i in range(1, 13)]
    total_k = 0
    for k in order:
        K[k]["got"] = sum(K[k]["sub"].values())
        total_k += K[k]["got"]
    max_k = sum(K[k]["max"] for k in order)

    # ---- penalties
    pen_items = []
    for e in pr.get("errors", []):
        w = 2 if e.get("traps") else 1
        pen_items.append((w, "FIYAT %s %s %s" % (e["id"], "; ".join(e["mismatch"]),
                                                 ("[" + ",".join(e["traps"]) + "]") if e.get("traps") else "")))
    for e in stt.get("errors", []):
        pen_items.append((1, "DURUM %s %s" % (e["id"], "; ".join(e["mismatch"]))))
    for vline in pw.get("violations", []):
        pen_items.append((1, "PAIRWISE kisit ihlali %s" % vline))
    t4 = []
    if rep["present"]:
        for n in (1, 2, 3, 5):
            if rep["ex_flags"].get(n):
                t4.append(n)
    for n in t4:
        pen_items.append((2, "T4? Ek-A Ornek %d hatali iddia edilmis olabilir [MANUEL ONAY]" % n))
    pen_raw = sum(w for w, _ in pen_items)
    pen = min(pen_raw, 18)
    final = max(0, total_k - pen)
    return {"K": {k: K[k] for k in order}, "k_total": total_k, "k_max": max_k,
            "penalty_raw": pen_raw, "penalty": pen, "penalty_items": pen_items,
            "final": final, "percent": round(100.0 * final / max_k, 1)}


def main():
    try:
        sys.stdout.reconfigure(errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("cikti", nargs="?")
    ap.add_argument("--json")
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.cikti:
        ap.error("cikti klasoru gerekli")
    d = a.cikti
    pr = grade_pricing(os.path.join(d, "fiyat-test-verisi.csv"))
    stt = grade_states(os.path.join(d, "durum-gecis-testleri.csv"))
    pw = grade_pairwise(os.path.join(d, "konfigurasyon-matrisi.csv"))
    rep = grade_report(os.path.join(d, "test-tasarimi.md"))
    sc = score(pr, stt, pw, rep)

    p = print
    p("=== trial-design grader (SFM v1.4) ===")
    p("Klasor: %s" % os.path.abspath(d))
    for name, r in (("fiyat", pr), ("durum", stt)):
        p("%-6s: %s, %d satir, %d dogru, %d oracle hatasi" % (
            name, "VAR" if r["present"] else "YOK", r["rows"], len(r.get("correct", [])),
            len(r.get("errors", []))))
    p("pairwise: %s, %d satir, kapsam %%%s (%d uygun cift), ihlal %d, taninmayan %d" % (
        "VAR" if pw["present"] else "YOK", pw["rows"], pw["coverage"], pw["feasible_pairs"],
        len(pw["violations"]), len(pw["unknown"])))
    p("rapor : %s" % ("VAR" if rep["present"] else "YOK"))
    p("")
    for k, v in sc["K"].items():
        p("%-4s %d/%d" % (k, v["got"], v["max"]))
        for s, pts in v["sub"].items():
            p("       [%s] %s" % ("x" if pts else " ", s))
    p("")
    p("K toplam: %d / %d" % (sc["k_total"], sc["k_max"]))
    p("Ceza (ham %d, tavan 18): -%d" % (sc["penalty_raw"], sc["penalty"]))
    for w, s in sc["penalty_items"]:
        p("   -%d %s" % (w, s))
    p("NIHAI PUAN: %d / %d  (%%%s)" % (sc["final"], sc["k_max"], sc["percent"]))
    if pw.get("missing_pairs") and (a.verbose or len(pw["missing_pairs"]) <= 15):
        p("")
        p("Eksik ciftler: " + "; ".join(pw["missing_pairs"]))
    if rep["present"]:
        p("")
        p("MANUEL ONAY - rapordaki Ek-A ornek referanslari (hata kelimesiyle birlikte):")
        for n, hits in rep["ex_flags"].items():
            for h in hits:
                p("   Ornek %d -> %s" % (n, h))
    if a.verbose:
        p("")
        p("Uyarilar:")
        for w in pr.get("warnings", []) + stt.get("warnings", []):
            p("   " + w)
    if a.json:
        out = {"score": {k: v for k, v in sc.items() if k != "penalty_items"},
               "penalty_items": sc["penalty_items"],
               "pricing": {"rows": pr["rows"], "errors": [{"id": e["id"], "mismatch": e["mismatch"],
                                                           "traps": e.get("traps", [])}
                                                          for e in pr.get("errors", [])]},
               "states": {"rows": stt["rows"], "errors": [{"id": e["id"], "mismatch": e["mismatch"]}
                                                          for e in stt.get("errors", [])]},
               "pairwise": {k: pw[k] for k in ("rows", "coverage", "violations", "unknown",
                                                "missing_pairs", "feasible_pairs")},
               "report_ex_flags": rep.get("ex_flags", {})}
        with open(a.json, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2, default=str)
    return 0


def selftest():
    """Oracle sanity checks: Ek-A examples (Ornek 4 is intentionally wrong in the spec)."""
    D = Decimal
    ok = True

    def chk(name, got, exp):
        nonlocal ok
        flag = got == exp
        ok &= flag
        print("%-60s %s  (got %s, exp %s)" % (name, "OK " if flag else "FAIL", got, exp))

    r = price("KLASIK", "500.00", "DEFNE10", "STANDART", "NORMAL", "KREDI_KARTI")
    chk("Ek-A Ornek 1", (r["ki"], r["nt"], r["ku"], r["hb"], r["ot"], r["puan"]),
        (D("50.00"), D("450.00"), D("39.90"), D("0.00"), D("489.90"), 45))
    r = price("MISAFIR", "1800.00", "DEFNE10", "HIZLI", "NORMAL", "BANKA_KARTI")
    chk("Ek-A Ornek 2", (r["ki"], r["nt"], r["ku"], r["ot"], r["puan"]),
        (D("150.00"), D("1650.00"), D("40.00"), D("1690.00"), 0))
    r = price("ALTIN", "900.00", "KITAP50", "STANDART", "NORMAL", "KREDI_KARTI")
    chk("Ek-A Ornek 3", (r["ki"], r["nt"], r["ku"], r["ot"], r["puan"]),
        (D("50.00"), D("850.00"), D("0.00"), D("850.00"), 127))
    r = price("KLASIK", "900.00", "", "STANDART", "UZAK", "KREDI_KARTI")
    chk("Ek-A Ornek 4 (spec says KU 0.00 / OT 900.00 -> WRONG)", (r["ku"], r["ot"], r["puan"]),
        (D("25.00"), D("925.00"), 90))
    r = price("MISAFIR", "640.00", "", "MAGAZA", "", "KREDI_KARTI")
    chk("Ek-A Ornek 5", (r["ku"], r["ot"], r["puan"]), (D("0.00"), D("640.00"), 0))
    # derived boundaries
    chk("K9 833.33 DEFNE10 -> NT 750.00 KU 0", (price("KLASIK", "833.33", "DEFNE10", "STANDART", "NORMAL", "KREDI_KARTI")["nt"],
                                                price("KLASIK", "833.33", "DEFNE10", "STANDART", "NORMAL", "KREDI_KARTI")["ku"]),
        (D("750.00"), D("0.00")))
    chk("K9 833.32 DEFNE10 -> NT 749.99 KU 39.90", (price("KLASIK", "833.32", "DEFNE10", "STANDART", "NORMAL", "KREDI_KARTI")["nt"],
                                                    price("KLASIK", "833.32", "DEFNE10", "STANDART", "NORMAL", "KREDI_KARTI")["ku"]),
        (D("749.99"), D("39.90")))
    chk("K10 4987.10 KAPIDA -> OT 5000.00", price("KLASIK", "4987.10", "", "STANDART", "NORMAL", "KAPIDA_ODEME")["ot"], D("5000.00"))
    chk("K10 4987.11 KAPIDA -> ERR_KAPIDA_LIMIT", price("KLASIK", "4987.11", "", "STANDART", "NORMAL", "KAPIDA_ODEME")["durum"], "ERR_KAPIDA_LIMIT")
    chk("K10 5000.00 KAPIDA (naive) -> ERR_KAPIDA_LIMIT", price("KLASIK", "5000.00", "", "STANDART", "NORMAL", "KAPIDA_ODEME")["durum"], "ERR_KAPIDA_LIMIT")
    chk("K5 1500.05 DEFNE10 -> KI 150.00", price("KLASIK", "1500.05", "DEFNE10", "STANDART", "NORMAL", "KREDI_KARTI")["ki"], D("150.00"))
    chk("K5 833.35 DEFNE10 -> KI 83.34", price("KLASIK", "833.35", "DEFNE10", "STANDART", "NORMAL", "KREDI_KARTI")["ki"], D("83.34"))
    chk("T1 150.00 DEFNE10 -> KABUL NT 135.00", (price("KLASIK", "150.00", "DEFNE10", "STANDART", "NORMAL", "KREDI_KARTI")["durum"],
                                                 price("KLASIK", "150.00", "DEFNE10", "STANDART", "NORMAL", "KREDI_KARTI")["nt"]),
        ("KABUL", D("135.00")))
    chk("T2 ALTIN HIZLI 600 -> KU 79.90", price("ALTIN", "600.00", "", "HIZLI", "NORMAL", "KREDI_KARTI")["ku"], D("79.90"))
    # lifecycle
    ctx = new_order("KREDI_KARTI")
    for ev in ("ODEME_BASARILI", "HAZIRLAMAYA_BASLA", "KARGOYA_VER", "TESLIM_BASARISIZ", "YENIDEN_DAGITIM",
               "TESLIM_BASARISIZ", "YENIDEN_DAGITIM"):
        assert apply_event(ctx, ev, {}) == "KABUL"
    chk("3. basarisiz teslim -> DEPOYA_DONDU", (apply_event(ctx, "TESLIM_BASARISIZ", {}), ctx["state"]), ("KABUL", "DEPOYA_DONDU"))
    seq = parse_sequence("ODEME_BASARILI > HAZIRLAMAYA_BASLA > IPTAL(aktor=MUSTERI)")
    ctx = new_order("KREDI_KARTI")
    rr = [apply_event(ctx, e, p) for e, p in seq]
    chk("HAZIRLANIYOR + IPTAL(MUSTERI)", (rr[-1], ctx["state"]), ("ERR_GECERSIZ_GECIS", "HAZIRLANIYOR"))
    _, pairs = feasible_pairs()
    chk("uygun cift sayisi", len(pairs), 59)
    print("SELFTEST", "PASSED" if ok else "FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
