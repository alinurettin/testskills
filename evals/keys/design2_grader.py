#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
design2_grader.py - objective grader for evals/trial-design2 (GUM v3.2, Poyraz Kargo).

Evaluator-only. Do NOT give this file to the agent under test.

Usage:
    python design2_grader.py <cikti_dir> [--json OUT.json] [--verbose]
    python design2_grader.py --selftest

<cikti_dir> must contain (a missing or unreadable file scores 0 for its area, no penalty):
    ucret-testleri.csv, durum-testleri.csv, konfigurasyon-matrisi.csv, spesifikasyon-bulgulari.csv

What it does (see design2.md for the rules in prose):
  * Recomputes the expected result of every pricing row and every state row with a reference
    oracle derived from the specification PK-SPEC-131 v3.2. A wrong expected value costs points.
  * Scores the planned test conditions P1..P15, Z1..Z7, C1..C3 on CORRECT rows only, and only on
    the rows inside the row budget of each file.
  * Scores the specification findings D1..D5 and the traps T1..T4 from the findings CSV by the
    section references and the type code, never by the wording.
  * Fully deterministic, no manual confirmation items. Python 3 standard library only.

Exactness: codes are case-sensitive, the separator is ';', the header must be the template
header. Leniency only where the meaning cannot change: BOM, CRLF, blank lines, spaces around a
cell, trailing zeros in an expected number.
"""
import argparse
import csv
import datetime as dt
import io
import itertools
import json
import os
import re
import sys
from decimal import Decimal, ROUND_HALF_UP

D = Decimal
CENT = D("0.01")
ZERO = D("0.00")
ONE_DAY = dt.timedelta(days=1)

MAX_SCORE = 100
BUDGET = {"ucret": 40, "durum": 30, "konfig": 24, "bulgu": 8}
FILES = {
    "ucret": "ucret-testleri.csv",
    "durum": "durum-testleri.csv",
    "konfig": "konfigurasyon-matrisi.csv",
    "bulgu": "spesifikasyon-bulgulari.csv",
}
HEADERS = {
    "ucret": ("test_id;musteri_tipi;agirlik_kg;en_cm;boy_cm;yukseklik_cm;bolge;hizmet;kampanya_kodu;"
              "beyan_degeri;kabul_zamani;beklenen_sonuc;beklenen_ucret_agirligi;beklenen_indirim;"
              "beklenen_toplam;beklenen_teslim_tarihi;aciklama"),
    "durum": "test_id;olay_dizisi;beklenen_sonuc;beklenen_son_durum;beklenen_deneme_sayisi;aciklama",
    "konfig": "test_id;kanal;musteri_tipi;hizmet;bolge;odeme;teslim_noktasi",
    "bulgu": "bulgu_id;bolumler;tur;aciklama",
}
PEN_ROW = 2        # wrong expected value / invalid precondition / constraint violation, per row
PEN_TRAP = 3       # per trap reported as a defect
PEN_BUDGET = 2     # flat, per file that exceeds its row budget


def q2(x):
    """Half-up rounding to kurus (spec 2.2)."""
    return x.quantize(CENT, rounding=ROUND_HALF_UP)


# --------------------------------------------------------------------------------------------
# CSV reading (strict format, see module docstring)
# --------------------------------------------------------------------------------------------
def read_table(path, kind):
    """Returns dict: present, ok, problem, rows (list of dict), over_budget, total_rows, warnings."""
    res = {"present": os.path.exists(path), "ok": False, "problem": None, "rows": [],
           "total_rows": 0, "over_budget": 0, "warnings": []}
    if not res["present"]:
        res["problem"] = "file missing"
        return res
    with open(path, "rb") as f:
        raw = f.read()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        res["problem"] = "not UTF-8"
        return res
    lines = [ln for ln in text.replace("\r\n", "\n").replace("\r", "\n").split("\n") if ln.strip()]
    if not lines:
        res["problem"] = "empty file"
        return res
    cols = HEADERS[kind].split(";")
    try:
        parsed = list(csv.reader(io.StringIO("\n".join(lines)), delimiter=";", quotechar='"'))
    except csv.Error as e:
        res["problem"] = "CSV error: %s" % e
        return res
    head = [c.strip() for c in parsed[0]]
    if head != cols:
        res["problem"] = "header differs from the template (separator must be ';', columns unchanged)"
        return res
    res["ok"] = True
    free_text_last = cols[-1] == "aciklama"
    data = []
    for cells in parsed[1:]:
        cells = [c.strip() for c in cells]
        if not any(cells):
            continue
        if len(cells) > len(cols):
            if free_text_last:   # an unquoted ';' inside the free-text column: meaning unchanged
                cells = cells[:len(cols) - 1] + [";".join(cells[len(cols) - 1:])]
                res["warnings"].append("%s: extra ';' joined into aciklama" % cells[0])
            else:
                cells = cells[:len(cols)] + ["<EXTRA>"]
        while len(cells) < len(cols):
            cells.append("")
        row = dict(zip(cols, cells))
        row["_extra"] = len(cells) > len(cols)
        if row[cols[0]].startswith("ORNEK-"):
            continue                      # template format examples are never graded
        data.append(row)
    res["total_rows"] = len(data)
    res["over_budget"] = max(0, len(data) - BUDGET[kind])
    res["rows"] = data[:BUDGET[kind]]
    return res


# --------------------------------------------------------------------------------------------
# Reference oracle: pricing and promised delivery date (spec sections 2-9, Ek-B)
# --------------------------------------------------------------------------------------------
MUSTERI = ("BIREYSEL", "KURUMSAL")
BOLGE = ("SEHIRICI", "YAKIN", "UZAK")
HIZMET = ("STANDART", "EKSPRES", "AYNI_GUN")
KAMPANYA = "BAHAR15"
TARIFE = {  # band <= 1.0 kg, <= 5.0 kg, <= 10.0 kg, increment per 0.5 kg above 10.0 kg
    "SEHIRICI": (D("60.00"), D("85.00"), D("120.00"), D("4.50")),
    "YAKIN": (D("75.00"), D("105.00"), D("150.00"), D("6.00")),
    "UZAK": (D("95.00"), D("135.00"), D("195.00"), D("8.25")),
}
KATSAYI = {"STANDART": D("1.00"), "EKSPRES": D("1.35"), "AYNI_GUN": D("1.80")}
SURE = {("STANDART", "SEHIRICI"): 2, ("STANDART", "YAKIN"): 3, ("STANDART", "UZAK"): 5,
        ("EKSPRES", "SEHIRICI"): 1, ("EKSPRES", "YAKIN"): 1, ("EKSPRES", "UZAK"): 2}
ERR_ORDER = ["ERR_GECERSIZ_GIRDI", "ERR_BOYUT", "ERR_AGIRLIK", "ERR_HACIM", "ERR_HIZMET_BOLGE",
             "ERR_AYNI_GUN_SAAT", "ERR_KAMPANYA_GECERSIZ"]
ERR_BEYAN = "ERR_BEYAN_LIMIT"   # defined in 7.2, missing from the precedence list 9.3 (planted D3)
HOLIDAYS = {                     # Ek-B
    dt.date(2028, 1, 1): "B-1", dt.date(2028, 4, 23): "B-2", dt.date(2028, 5, 1): "B-3",
    dt.date(2028, 5, 19): "B-4", dt.date(2028, 7, 15): "B-5", dt.date(2028, 8, 30): "B-6",
    dt.date(2028, 10, 29): "B-7",
}
KABUL_MIN = dt.datetime(2028, 1, 1, 0, 0)
KABUL_MAX = dt.datetime(2028, 12, 15, 23, 59)
CAMP_FROM = dt.date(2028, 3, 1)
CAMP_TO = dt.date(2028, 5, 31)
LEAP_DAY = dt.date(2028, 2, 29)
DEC2_RE = re.compile(r"^\d+(\.\d{1,2})?$")
INT_RE = re.compile(r"^\d+$")
DT_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2})$")
PRICE_INPUTS = ("musteri_tipi", "agirlik_kg", "en_cm", "boy_cm", "yukseklik_cm", "bolge", "hizmet",
                "kampanya_kodu", "beyan_degeri", "kabul_zamani")


def is_gunu(d):
    """8.1: Monday-Saturday, not listed in Ek-B."""
    return d.weekday() != 6 and d not in HOLIDAYS


def sonraki_is_gunu(d):
    d = d + ONE_DAY
    while not is_gunu(d):
        d += ONE_DAY
    return d


def ekle_is_gunu(d, n):
    for _ in range(n):
        d = sonraki_is_gunu(d)
    return d


def kesim_saati(d):
    return dt.time(13, 0) if d.weekday() == 5 else dt.time(17, 0)


def teslim_from(islem, hizmet, bolge):
    """Returns (N-th business day, promised date after the 8.4 Saturday rule for UZAK)."""
    pre = ekle_is_gunu(islem, SURE[(hizmet, bolge)])
    fin = sonraki_is_gunu(pre) if (bolge == "UZAK" and pre.weekday() == 5) else pre
    return pre, fin


def parse_kabul(s):
    m = DT_RE.match(s)
    if not m:
        return None
    y, mo, d, h, mi = (int(g) for g in m.groups())
    try:
        t = dt.datetime(y, mo, d, h, mi)
    except ValueError:
        return None
    return t if KABUL_MIN <= t <= KABUL_MAX else None


def discount(tb, kurumsal, camp_active, hizmet):
    """6.1-6.5. Returns dict with it, contract, camp_raw, camp, kind, floor_bound."""
    camp_raw = q2(tb * D("0.15"))
    out = {"contract": None, "camp_raw": camp_raw, "camp": None, "kind": "none",
           "floor_bound": False, "it": ZERO}
    if hizmet == "AYNI_GUN":
        out["kind"] = "aynigun"
        return out
    if kurumsal:
        out["contract"] = q2(tb * D("0.12"))
    if camp_active:
        out["camp"] = min(camp_raw, D("40.00"))
    it = ZERO
    if out["contract"] is not None:
        it, out["kind"] = out["contract"], "contract"
    if out["camp"] is not None and out["camp"] > it:
        it, out["kind"] = out["camp"], "camp"
    if out["kind"] != "none" and tb - it < D("55.00"):
        it = tb - D("55.00")
        out["floor_bound"] = True
    out["it"] = it
    return out


def price(f):
    """f: dict of the ten raw input strings (already stripped).
    Returns dict:
      accept_err : list of acceptable error codes (empty when the request is priced)
      conds      : applicable errors of the 9.3 list, in precedence order
      beyan_err  : True when 7.2 limit is exceeded
      invalid    : names of the fields that fail validation
      plus parsed inputs and, when priced, 'calc' and 'variants' (acceptable delivery dates).
    """
    r = {"accept_err": [], "conds": [], "beyan_err": False, "invalid": []}
    inv = r["invalid"]
    if f["musteri_tipi"] not in MUSTERI:
        inv.append("musteri_tipi")
    ga = None
    if DEC2_RE.match(f["agirlik_kg"]) and D(f["agirlik_kg"]) > 0:
        ga = D(f["agirlik_kg"])
    else:
        inv.append("agirlik_kg")
    dims = []
    for k in ("en_cm", "boy_cm", "yukseklik_cm"):
        if INT_RE.match(f[k]) and int(f[k]) >= 1:
            dims.append(int(f[k]))
        else:
            inv.append(k)
    dims = dims if len(dims) == 3 else None
    bolge = f["bolge"] if f["bolge"] in BOLGE else None
    if bolge is None:
        inv.append("bolge")
    hizmet = f["hizmet"] if f["hizmet"] in HIZMET else None
    if hizmet is None:
        inv.append("hizmet")
    beyan = None
    if f["beyan_degeri"] != "":
        if DEC2_RE.match(f["beyan_degeri"]) and D(f["beyan_degeri"]) > 0:
            beyan = D(f["beyan_degeri"])
        else:
            inv.append("beyan_degeri")
    t = parse_kabul(f["kabul_zamani"])
    if t is None:
        inv.append("kabul_zamani")
    kod = f["kampanya_kodu"]
    r.update({"ga": ga, "dims": dims, "bolge": bolge, "hizmet": hizmet, "beyan": beyan, "t": t,
              "kod": kod, "musteri": f["musteri_tipi"]})

    conds = set()
    if inv:
        conds.add("ERR_GECERSIZ_GIRDI")
    if dims and (max(dims) > 100 or sum(dims) > 150):
        conds.add("ERR_BOYUT")
    if ga is not None and ga > D("30.00"):
        conds.add("ERR_AGIRLIK")
    steps = None
    if dims and ga is not None:
        p = dims[0] * dims[1] * dims[2]
        ha_c = (2 * p + 30) // 60                   # HA in 0.01 kg, half-up of p/3000 (4.3)
        ga_c = int(ga * 100)
        steps = -(-max(ga_c, ha_c) // 50)           # UA in 0.5 kg steps, rounded up (4.4)
        r.update({"p": p, "ha_c": ha_c, "ga_c": ga_c, "steps": steps})
        if steps > 80:
            conds.add("ERR_HACIM")
    if hizmet == "AYNI_GUN" and bolge is not None and bolge != "SEHIRICI":
        conds.add("ERR_HIZMET_BOLGE")
    if hizmet == "AYNI_GUN" and t is not None:
        if not is_gunu(t.date()) or t.time() > dt.time(11, 0):
            conds.add("ERR_AYNI_GUN_SAAT")
    if kod != "" and kod != KAMPANYA:
        conds.add("ERR_KAMPANYA_GECERSIZ")
    if beyan is not None and beyan > D("50000.00"):
        r["beyan_err"] = True
    r["conds"] = [c for c in ERR_ORDER if c in conds]
    if r["conds"]:
        r["accept_err"] = [r["conds"][0]] + ([ERR_BEYAN] if r["beyan_err"] else [])
        return r
    if r["beyan_err"]:
        r["accept_err"] = [ERR_BEYAN]
        return r

    # ---- priced
    band = TARIFE[bolge]
    if steps <= 2:
        tarife = band[0]
    elif steps <= 10:
        tarife = band[1]
    elif steps <= 20:
        tarife = band[2]
    else:
        tarife = band[2] + band[3] * (steps - 20)
    tb_exact = tarife * KATSAYI[hizmet]
    tb = q2(tb_exact)
    kd = t.date()
    camp_window = CAMP_FROM <= kd <= CAMP_TO
    camp_active = kod == KAMPANYA and camp_window
    kur = f["musteri_tipi"] == "KURUMSAL"
    dsc = discount(tb, kur, camp_active, hizmet)
    it = dsc["it"]
    ntb = tb - it
    ye = q2(ntb * D("0.065"))
    sp = ZERO
    sp_raw = None
    if beyan is not None:
        sp_raw = q2(beyan * D("0.008"))
        sp = max(sp_raw, D("15.00"))
    ma = ntb + ye + sp
    kdv = q2(ma * D("0.20"))
    tu = ma + kdv
    calc = {"ua": D(steps) / 2, "tarife": tarife, "tb_exact": tb_exact, "tb": tb, "it": it,
            "ntb": ntb, "ye": ye, "sp": sp, "sp_raw": sp_raw, "ma": ma, "kdv": kdv, "tu": tu,
            "dsc": dsc, "camp_window": camp_window, "camp_active": camp_active, "kurumsal": kur,
            "it_if_camp": discount(tb, kur, kod == KAMPANYA, hizmet)["it"],
            "it_if_nocamp": discount(tb, kur, False, hizmet)["it"]}
    r["calc"] = calc

    variants = []
    hyp = {"same": None, "next": None}
    if hizmet == "AYNI_GUN":
        variants.append({"mode": "aynigun", "islem": kd, "pre": kd, "teslim": kd})
    else:
        nxt = sonraki_is_gunu(kd)
        hyp["next"] = teslim_from(nxt, hizmet, bolge)[1]
        if is_gunu(kd):
            hyp["same"] = teslim_from(kd, hizmet, bolge)[1]
            c = kesim_saati(kd)
            if t.time() < c:
                modes = ["same"]
            elif t.time() == c:
                modes = ["same", "next"]       # planted D2: 8.2 (inclusive) vs 2.4 (exclusive)
            else:
                modes = ["next"]
        else:
            modes = ["next"]
        for m in modes:
            islem = kd if m == "same" else nxt
            pre, fin = teslim_from(islem, hizmet, bolge)
            variants.append({"mode": m, "islem": islem, "pre": pre, "teslim": fin})
    r["variants"] = variants
    r["hyp"] = hyp
    r["sensitive"] = hyp["same"] is not None and hyp["same"] != hyp["next"]
    return r


NUM_RE = re.compile(r"^\d+(\.\d+)?$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
PRICE_EXPECTED = ("beklenen_ucret_agirligi", "beklenen_indirim", "beklenen_toplam", "beklenen_teslim_tarihi")


def grade_ucret(tab):
    out = {"correct": [], "wrong": [], "incomplete": []}
    for row in tab["rows"]:
        f = {k: row[k] for k in PRICE_INPUTS}
        o = price(f)
        exp = row["beklenen_sonuc"]
        info = {"id": row["test_id"], "row": row, "o": o, "exp": exp}
        mism, blanks = [], []
        if o["accept_err"]:
            if exp not in o["accept_err"]:
                mism.append("beklenen_sonuc %s, oracle %s" % (exp or "<bos>", " / ".join(o["accept_err"])))
            elif any(row[c] != "" for c in PRICE_EXPECTED):
                mism.append("error row with filled amount/date columns (9.2)")
        elif exp != "KABUL":
            mism.append("beklenen_sonuc %s, oracle KABUL" % (exp or "<bos>"))
        else:
            c = o["calc"]
            for col, key in (("beklenen_ucret_agirligi", "ua"), ("beklenen_indirim", "it"),
                             ("beklenen_toplam", "tu")):
                v = row[col]
                if v == "":
                    blanks.append(col)
                elif not NUM_RE.match(v) or D(v) != c[key]:
                    mism.append("%s %s, oracle %s" % (col, v, c[key]))
            v = row["beklenen_teslim_tarihi"]
            ok_dates = [x["teslim"].isoformat() for x in o["variants"]]
            if v == "":
                blanks.append("beklenen_teslim_tarihi")
            elif not DATE_RE.match(v) or v not in ok_dates:
                mism.append("beklenen_teslim_tarihi %s, oracle %s" % (v, " / ".join(sorted(set(ok_dates)))))
            else:
                info["matched"] = [x for x in o["variants"] if x["teslim"].isoformat() == v]
        if mism:
            info["mismatch"] = mism
            out["wrong"].append(info)
        elif blanks:
            info["blanks"] = blanks
            out["incomplete"].append(info)
        else:
            out["correct"].append(info)
    return out


def score_ucret(g):
    """P1..P15 on correct rows. Returns ordered dict item -> {max, sub: [(label, got, max)]}."""
    ok = [r for r in g["correct"] if r["exp"] == "KABUL"]
    er = [r for r in g["correct"] if r["exp"] != "KABUL"]
    T = dt.time

    def calc(r):
        return r["o"]["calc"]

    def pure(r, code):
        return r["exp"] == code and r["o"]["conds"] == ([code] if code != ERR_BEYAN else []) \
            and r["o"]["beyan_err"] == (code == ERR_BEYAN)

    def any_ok(pred):
        return any(pred(r) for r in ok)

    def any_er(pred):
        return any(pred(r) for r in er)

    def modes(r):
        return {x["mode"] for x in r["matched"]}

    P = {}
    # P1 actual weight limit (4.2)
    a = any_ok(lambda r: r["o"]["ga"] == D("30.00"))
    b = any_er(lambda r: pure(r, "ERR_AGIRLIK") and r["o"]["ga"] == D("30.01"))
    P["P1"] = (2, [("GA 30.00 -> KABUL and GA 30.01 -> ERR_AGIRLIK", 2 if (a and b) else 0, 2)])
    # P2 dimension limits (4.1)
    a = any_ok(lambda r: max(r["o"]["dims"]) == 100) and \
        any_er(lambda r: r["exp"] == "ERR_BOYUT" and r["o"]["dims"] and max(r["o"]["dims"]) == 101
               and sum(r["o"]["dims"]) <= 150)
    b = any_ok(lambda r: sum(r["o"]["dims"]) == 150) and \
        any_er(lambda r: r["exp"] == "ERR_BOYUT" and r["o"]["dims"] and sum(r["o"]["dims"]) == 151
               and max(r["o"]["dims"]) <= 100)
    P["P2"] = (2, [("side 100 -> KABUL and side 101 -> ERR_BOYUT", 1 if a else 0, 1),
                   ("sum 150 -> KABUL and sum 151 -> ERR_BOYUT", 1 if b else 0, 1)])
    # P3 chargeable weight limit (4.5)
    a = any_ok(lambda r: r["o"]["steps"] == 80)
    b = any_er(lambda r: pure(r, "ERR_HACIM") and r["o"]["steps"] == 81)
    P["P3"] = (2, [("UA 40.0 -> KABUL", 1 if a else 0, 1), ("UA 40.5 -> ERR_HACIM", 1 if b else 0, 1)])
    # P4 tariff band boundaries (5.1)
    uas = {r["o"]["steps"] for r in ok}
    pairs = sum(1 for lo, hi in ((2, 3), (10, 11), (20, 21)) if lo in uas and hi in uas)
    P["P4"] = (2, [("tariff band boundaries UA 1.0/1.5, 5.0/5.5, 10.0/10.5 (%d of 3 pairs)" % pairs,
                    2 if pairs == 3 else (1 if pairs == 2 else 0), 2)])
    # P5 two-stage weight rounding (2.3, 4.3, 4.4)
    a = any_ok(lambda r: r["o"]["ha_c"] % 50 == 0 and r["o"]["p"] * 100 > r["o"]["ha_c"] * 3000
               and r["o"]["ga_c"] <= r["o"]["ha_c"])
    b = any_ok(lambda r: r["o"]["p"] % 1500 == 15 and r["o"]["ga_c"] <= r["o"]["ha_c"] - 1)
    P["P5"] = (4, [("raw HA just above a 0.5 step rounds down to it (UA stays on the step)", 2 if a else 0, 2),
                   ("raw HA exactly x.xx5 above a 0.5 step rounds half-up (UA moves to the next step)",
                    2 if b else 0, 2)])
    # P6 half-up on the freight charge (2.2, 5.2)
    a = any_ok(lambda r: (calc(r)["tb_exact"] * 1000) % 10 == 5)
    P["P6"] = (2, [("TB = tariff x coefficient ends in exactly half a kurus", 2 if a else 0, 2)])
    # P7 mutually exclusive discounts (6.1-6.3)

    def both(r):
        d = calc(r)["dsc"]
        return d["contract"] is not None and d["camp"] is not None and not d["floor_bound"]
    a = any_ok(lambda r: both(r) and calc(r)["dsc"]["camp_raw"] <= D("40.00") and calc(r)["dsc"]["kind"] == "camp")
    b = any_ok(lambda r: both(r) and calc(r)["dsc"]["camp_raw"] > D("40.00") and calc(r)["dsc"]["kind"] == "camp")
    c = any_ok(lambda r: both(r) and calc(r)["dsc"]["contract"] > D("40.00"))
    P["P7"] = (5, [("KURUMSAL+BAHAR15: campaign below its cap wins", 1 if a else 0, 1),
                   ("KURUMSAL+BAHAR15: capped campaign (40.00) still beats 12 %", 2 if b else 0, 2),
                   ("KURUMSAL+BAHAR15: 12 % exceeds the capped campaign", 2 if c else 0, 2)])
    # P8 floor and same-day exclusion (6.4, 6.5)
    a = any_ok(lambda r: calc(r)["dsc"]["floor_bound"])
    b = any_ok(lambda r: r["o"]["hizmet"] == "AYNI_GUN" and (calc(r)["kurumsal"] or calc(r)["camp_active"]))
    P["P8"] = (3, [("discount limited by the 55.00 floor", 2 if a else 0, 2),
                   ("AYNI_GUN with a discount-eligible request -> IT 0.00", 1 if b else 0, 1)])
    # P9 campaign validity by acceptance date (6.2)

    def camp_row(r, day, active):
        c = calc(r)
        return (r["o"]["kod"] == KAMPANYA and r["o"]["hizmet"] != "AYNI_GUN" and r["o"]["t"].date() == day
                and c["camp_active"] == active and c["it_if_camp"] != c["it_if_nocamp"])
    a1 = any_ok(lambda r: camp_row(r, dt.date(2028, 2, 29), False))
    a2 = any_ok(lambda r: camp_row(r, dt.date(2028, 3, 1), True))
    b = any_ok(lambda r: camp_row(r, dt.date(2028, 5, 31), True)) and \
        any_ok(lambda r: camp_row(r, dt.date(2028, 6, 1), False))

    def split_row(r):
        c = calc(r)
        if not (r["o"]["kod"] == KAMPANYA and r["o"]["hizmet"] != "AYNI_GUN"
                and c["it_if_camp"] != c["it_if_nocamp"]):
            return False
        return all((CAMP_FROM <= x["islem"] <= CAMP_TO) != c["camp_window"] for x in r["matched"])
    c = any_ok(split_row)
    P["P9"] = (5, [("BAHAR15 on 2028-02-29 not applied", 1 if a1 else 0, 1),
                   ("BAHAR15 on 2028-03-01 applied", 1 if a2 else 0, 1),
                   ("BAHAR15 on 2028-05-31 applied and on 2028-06-01 not applied", 1 if b else 0, 1),
                   ("acceptance date and processing day on different sides of the campaign window",
                    2 if c else 0, 2)])
    # P10 insurance (7.2)
    a = any_ok(lambda r: calc(r)["sp_raw"] is not None and calc(r)["sp_raw"] < D("15.00"))
    b = any_ok(lambda r: r["o"]["beyan"] == D("50000.00")) and \
        any_er(lambda r: pure(r, ERR_BEYAN) and r["o"]["beyan"] == D("50000.01"))
    P["P10"] = (3, [("minimum premium 15.00 binding", 1 if a else 0, 1),
                    ("beyan 50000.00 -> KABUL and 50000.01 -> ERR_BEYAN_LIMIT", 2 if b else 0, 2)])
    # P11 cut-off, calendar, leap day (8.1-8.3, Ek-B)

    def cut(r, sat, times, mode):
        o = r["o"]
        if o["hizmet"] == "AYNI_GUN" or not o["sensitive"]:
            return False
        kd = o["t"].date()
        return ((kd.weekday() == 5) == sat and is_gunu(kd) and o["t"].time() in times
                and modes(r) == {mode})

    def cut_pair(sat, on_times, late_times):
        on = [r["o"]["t"].time() for r in ok if cut(r, sat, on_times, "same")]
        late = [r["o"]["t"].time() for r in ok if cut(r, sat, late_times, "next")]
        return any(x < y for x in on for y in late)
    a = cut_pair(False, (T(16, 59), T(17, 0)), (T(17, 0), T(17, 1)))
    b = cut_pair(True, (T(12, 59), T(13, 0)), (T(13, 0), T(13, 1)))
    c = any_ok(lambda r: not is_gunu(r["o"]["t"].date()))
    d = any_ok(lambda r: any(h.weekday() != 6 and r["o"]["t"].date() < h < min(x["teslim"] for x in r["matched"])
                             for h in HOLIDAYS))
    e = any_ok(lambda r: r["o"]["t"].date() <= LEAP_DAY <= min(x["teslim"] for x in r["matched"]))
    P["P11"] = (5, [("weekday cut-off: on-time and late row one minute apart, both date-sensitive", 1 if a else 0, 1),
                    ("Saturday cut-off: on-time and late row one minute apart, both date-sensitive", 1 if b else 0, 1),
                    ("acceptance on a Sunday or an Ek-B holiday", 1 if c else 0, 1),
                    ("an Ek-B holiday (not a Sunday) lies between acceptance and delivery", 1 if d else 0, 1),
                    ("29 February inside acceptance..delivery", 1 if e else 0, 1)])
    # P12 no Saturday delivery in UZAK (8.4)
    a = any_ok(lambda r: r["o"]["bolge"] == "UZAK" and all(x["pre"].weekday() == 5 for x in r["matched"]))
    b = any_ok(lambda r: r["o"]["bolge"] != "UZAK" and all(x["teslim"].weekday() == 5 for x in r["matched"]))
    P["P12"] = (3, [("UZAK: N-th business day is a Saturday -> moved to the next business day", 2 if a else 0, 2),
                    ("other zone: delivery on a Saturday stays", 1 if b else 0, 1)])
    # P13 same-day service time rule (8.5)
    a = any_ok(lambda r: r["o"]["hizmet"] == "AYNI_GUN" and r["o"]["t"].time() == T(11, 0)) and \
        any_er(lambda r: pure(r, "ERR_AYNI_GUN_SAAT") and r["o"]["t"].time() == T(11, 1)
               and is_gunu(r["o"]["t"].date()))
    b = any_er(lambda r: pure(r, "ERR_AYNI_GUN_SAAT") and r["o"]["t"].time() <= T(11, 0)
               and not is_gunu(r["o"]["t"].date()))
    P["P13"] = (2, [("AYNI_GUN 11:00 -> KABUL and 11:01 -> ERR_AYNI_GUN_SAAT", 1 if a else 0, 1),
                    ("AYNI_GUN before 11:00 on a non-business day -> ERR_AYNI_GUN_SAAT", 1 if b else 0, 1)])
    # P14 service/zone error and error precedence (5.3, 9.3)
    a = any_er(lambda r: pure(r, "ERR_HIZMET_BOLGE"))
    sets = {frozenset(r["o"]["conds"]) for r in er if len(r["o"]["conds"]) >= 2 and not r["o"]["beyan_err"]}
    P["P14"] = (2, [("ERR_HIZMET_BOLGE", 1 if a else 0, 1),
                    ("two rows with different sets of simultaneous errors (%d found)" % len(sets),
                     1 if len(sets) >= 2 else 0, 1)])
    # P15 input validation (3.2, 3.3, 6.2)
    num = {"agirlik_kg", "en_cm", "boy_cm", "yukseklik_cm", "beyan_degeri", "kabul_zamani"}
    a = any_er(lambda r: r["exp"] == "ERR_GECERSIZ_GIRDI" and num & set(r["o"]["invalid"]))
    b = any_er(lambda r: pure(r, "ERR_KAMPANYA_GECERSIZ"))
    P["P15"] = (2, [("ERR_GECERSIZ_GIRDI for a malformed number or date", 1 if a else 0, 1),
                    ("ERR_KAMPANYA_GECERSIZ", 1 if b else 0, 1)])
    return P


# --------------------------------------------------------------------------------------------
# Reference oracle: shipment life cycle (spec section 10)
# --------------------------------------------------------------------------------------------
STATES = ("KABUL_EDILDI", "TRANSFERDE", "DAGITIMDA", "TESLIM_EDILEMEDI", "SUBEDE_BEKLIYOR",
          "TESLIM_EDILDI", "IADE_YOLUNDA", "IADE_EDILDI", "IPTAL_EDILDI")
FINAL = ("TESLIM_EDILDI", "IADE_EDILDI", "IPTAL_EDILDI")
GUN_RE = re.compile(r"^\d+$")
EVENTS = {   # event -> {param: validator}
    "TRANSFERE_VER": {}, "DAGITIMA_CIKAR": {}, "TESLIM_BASARILI": {}, "YENIDEN_DAGIT": {},
    "SUBEYE_YONLENDIR": {}, "ADRES_DEGISTIR": {}, "IADE_TESLIM": {},
    "TESLIM_BASARISIZ": {"neden": lambda v: v in ("ADRESTE_YOK", "RED")},
    "SUBEDEN_TESLIM": {"gun": lambda v: bool(GUN_RE.match(v))},
    "SURE_DOLDU": {"gun": lambda v: bool(GUN_RE.match(v))},
    "IPTAL": {"aktor": lambda v: v in ("GONDERICI", "OPERATOR")},
}
TABLE = {
    "KABUL_EDILDI": ("TRANSFERE_VER", "IPTAL"),
    "TRANSFERDE": ("DAGITIMA_CIKAR", "IPTAL", "ADRES_DEGISTIR"),
    "DAGITIMDA": ("TESLIM_BASARILI", "TESLIM_BASARISIZ"),
    "TESLIM_EDILEMEDI": ("YENIDEN_DAGIT", "SUBEYE_YONLENDIR", "ADRES_DEGISTIR"),
    "SUBEDE_BEKLIYOR": ("SUBEDEN_TESLIM", "SURE_DOLDU", "YENIDEN_DAGIT"),
    "IADE_YOLUNDA": ("IADE_TESLIM",),
}
ALL_G = tuple("G%d" % i for i in range(1, 18))


def new_ctx():
    return {"state": "KABUL_EDILDI", "deneme": 0, "adres": 0}


def apply_event(ctx, name, params):
    """10.5 rules in order. Mutates ctx only on success. Returns (result, transition id or None)."""
    st = ctx["state"]
    if name not in EVENTS:
        return "ERR_GECERSIZ_GIRDI", None                       # rule 1
    if name not in TABLE.get(st, ()):
        return "ERR_GECERSIZ_GECIS", None                       # rule 2
    spec = EVENTS[name]
    if set(params) != set(spec) or not all(spec[k](v) for k, v in params.items()):
        return "ERR_GECERSIZ_GIRDI", None                       # rule 3

    def go(target, gid):
        ctx["state"] = target
        return "KABUL", gid
    if st == "KABUL_EDILDI":
        return go("TRANSFERDE", "G1") if name == "TRANSFERE_VER" else go("IPTAL_EDILDI", "G2")
    if st == "TRANSFERDE":
        if name == "DAGITIMA_CIKAR":
            return go("DAGITIMDA", "G3")
        if name == "IPTAL":
            return go("IADE_YOLUNDA", "G4") if params["aktor"] == "OPERATOR" else ("ERR_YETKI", None)
        if ctx["adres"] >= 1:
            return "ERR_ADRES_LIMIT", None
        ctx["adres"] += 1
        return go("TRANSFERDE", "G5")
    if st == "DAGITIMDA":
        if name == "TESLIM_BASARILI":
            return go("TESLIM_EDILDI", "G6")
        if params["neden"] == "RED":
            return go("IADE_YOLUNDA", "G9")
        ctx["deneme"] += 1
        return go("TESLIM_EDILEMEDI", "G7") if ctx["deneme"] < 3 else go("SUBEDE_BEKLIYOR", "G8")
    if st == "TESLIM_EDILEMEDI":
        if name == "YENIDEN_DAGIT":
            return go("DAGITIMDA", "G10") if ctx["deneme"] < 3 else go("IADE_YOLUNDA", "G11")
        if name == "SUBEYE_YONLENDIR":
            return go("SUBEDE_BEKLIYOR", "G12")
        if ctx["adres"] >= 1:
            return "ERR_ADRES_LIMIT", None
        ctx["adres"] += 1
        return go("TESLIM_EDILEMEDI", "G13")
    if st == "SUBEDE_BEKLIYOR":
        if name == "SUBEDEN_TESLIM":
            return go("TESLIM_EDILDI", "G14") if int(params["gun"]) <= 5 else ("ERR_BEKLEME_SURESI", None)
        if name == "SURE_DOLDU":
            return go("IADE_YOLUNDA", "G15") if int(params["gun"]) > 5 else ("ERR_SURE_DOLMADI", None)
        return go("DAGITIMDA", "G16") if ctx["deneme"] < 3 else ("ERR_DENEME_LIMITI", None)
    return go("IADE_EDILDI", "G17")                              # IADE_YOLUNDA + IADE_TESLIM


def parse_sequence(text):
    """'A > B(k=v) > C' -> [(name, {k: v})]. Names and values are taken literally (case-sensitive).
    Anything that is not NAME or NAME(k=v,...) becomes an unknown event or an unknown parameter,
    which the oracle then rejects exactly as the specification says (10.5 rules 1 and 3)."""
    t = text.strip()
    if t == "":
        return []
    out = []
    for tok in t.split(">"):
        tok = tok.strip()
        m = re.match(r"^([^()]*)\((.*)\)$", tok)
        if not m:
            out.append((tok, {}))
            continue
        name, inner = m.group(1).strip(), m.group(2).strip()
        params = {}
        if inner:
            for i, part in enumerate(inner.split(",")):
                if "=" in part:
                    k, v = part.split("=", 1)
                    params[k.strip()] = v.strip()
                else:
                    params["_%d" % i] = part.strip()
        out.append((name, params))
    return out


def model_facts():
    """Breadth-first search over (state, deneme, adres, last transition).
    Returns (live transitions, feasible ordered pairs of consecutive transitions)."""
    choices = []
    for ev, spec in EVENTS.items():
        if "neden" in spec:
            choices += [(ev, {"neden": "ADRESTE_YOK"}), (ev, {"neden": "RED"})]
        elif "gun" in spec:
            choices += [(ev, {"gun": "5"}), (ev, {"gun": "6"})]
        elif "aktor" in spec:
            choices += [(ev, {"aktor": "GONDERICI"}), (ev, {"aktor": "OPERATOR"})]
        else:
            choices.append((ev, {}))
    start = ("KABUL_EDILDI", 0, 0, None)
    seen, todo = {start}, [start]
    live, pairs = set(), set()
    while todo:
        st, dn, ad, last = todo.pop()
        for ev, pr in choices:
            ctx = {"state": st, "deneme": dn, "adres": ad}
            res, gid = apply_event(ctx, ev, dict(pr))
            if res != "KABUL":
                continue
            live.add(gid)
            if last:
                pairs.add((last, gid))
            nxt = (ctx["state"], ctx["deneme"], ctx["adres"], gid)
            if nxt not in seen:
                seen.add(nxt)
                todo.append(nxt)
    return live, pairs


def grade_durum(tab):
    out = {"correct": [], "wrong": [], "incomplete": []}
    for row in tab["rows"]:
        info = {"id": row["test_id"], "row": row}
        seq = parse_sequence(row["olay_dizisi"])
        ctx = new_ctx()
        fired, bad_prefix = [], None
        for i, (ev, pr) in enumerate(seq[:-1]):
            res, gid = apply_event(ctx, ev, pr)
            if res != "KABUL":
                bad_prefix = "precondition event #%d %s is rejected (%s in %s)" % (i + 1, ev, res, ctx["state"])
                break
            fired.append(gid)
        if bad_prefix:
            info["mismatch"] = [bad_prefix]
            out["wrong"].append(info)
            continue
        pre = dict(ctx)
        gid = None
        if seq:
            res, gid = apply_event(ctx, seq[-1][0], seq[-1][1])
            if gid:
                fired.append(gid)
        else:
            res = "KABUL"
        info.update({"pre": pre, "last": seq[-1] if seq else None, "result": res, "fired": fired,
                     "last_gid": gid,
                     "final": ctx["state"], "deneme": ctx["deneme"], "adres": ctx["adres"]})
        mism, blanks = [], []
        e_res, e_st, e_dn = row["beklenen_sonuc"], row["beklenen_son_durum"], row["beklenen_deneme_sayisi"]
        if e_res != res:
            mism.append("beklenen_sonuc %s, oracle %s" % (e_res or "<bos>", res))
        if e_st == "":
            blanks.append("beklenen_son_durum")
        elif e_st != ctx["state"]:
            mism.append("beklenen_son_durum %s, oracle %s" % (e_st, ctx["state"]))
        if e_dn == "":
            blanks.append("beklenen_deneme_sayisi")
        elif not GUN_RE.match(e_dn) or int(e_dn) != ctx["deneme"]:
            mism.append("beklenen_deneme_sayisi %s, oracle %d" % (e_dn, ctx["deneme"]))
        if mism:
            info["mismatch"] = mism
            out["wrong"].append(info)
        elif blanks:
            info["blanks"] = blanks
            out["incomplete"].append(info)
        else:
            out["correct"].append(info)
    return out


def steps_pts(value, table):
    """table: [(threshold, points)] in descending threshold order."""
    for thr, pts in table:
        if value >= thr:
            return pts
    return 0


def score_durum(g):
    live, pairs = model_facts()
    ok = g["correct"]
    cov_t, cov_p = set(), set()
    for r in ok:
        cov_t.update(r["fired"])
        cov_p.update(zip(r["fired"], r["fired"][1:]))
    cov_t &= live
    cov_p &= pairs
    last = [r for r in ok if r["last"] is not None]

    def any_last(pred):
        return any(pred(r) for r in last)

    Z = {}
    n = len(cov_t)
    Z["Z1"] = (2, [("valid transitions exercised: %d of %d" % (n, len(live)),
                    steps_pts(n, [(len(live), 2), (len(live) - 2, 1)]), 2)])
    n = len(cov_p)
    pct = 100.0 * n / len(pairs)
    Z["Z2"] = (7, [("pairs of consecutive transitions (1-switch): %d of %d" % (n, len(pairs)),
                    steps_pts(pct, [(100, 7), (90, 5), (75, 3), (50, 1)]), 7)])
    st_inv = {r["pre"]["state"] for r in last if r["result"] == "ERR_GECERSIZ_GECIS"}
    n = len(st_inv)
    Z["Z3"] = (3, [("states with a rejected event not in the table: %d of %d" % (n, len(STATES)),
                    steps_pts(n, [(9, 3), (7, 2), (5, 1)]), 3)])
    guards = {
        "ERR_YETKI": any_last(lambda r: r["result"] == "ERR_YETKI"),
        "ERR_ADRES_LIMIT in TRANSFERDE": any_last(
            lambda r: r["result"] == "ERR_ADRES_LIMIT" and r["pre"]["state"] == "TRANSFERDE"),
        "ERR_ADRES_LIMIT in TESLIM_EDILEMEDI": any_last(
            lambda r: r["result"] == "ERR_ADRES_LIMIT" and r["pre"]["state"] == "TESLIM_EDILEMEDI"),
        "ERR_ADRES_LIMIT across states (changed in TRANSFERDE, refused in TESLIM_EDILEMEDI)": any_last(
            lambda r: r["result"] == "ERR_ADRES_LIMIT" and r["pre"]["state"] == "TESLIM_EDILEMEDI"
            and "G5" in r["fired"]),
        "ERR_DENEME_LIMITI": any_last(lambda r: r["result"] == "ERR_DENEME_LIMITI"),
        "ERR_BEKLEME_SURESI": any_last(lambda r: r["result"] == "ERR_BEKLEME_SURESI"),
        "ERR_SURE_DOLMADI": any_last(lambda r: r["result"] == "ERR_SURE_DOLMADI"),
    }
    n = sum(1 for v in guards.values() if v)
    Z["Z4"] = (4, [("guard failures: %d of 7 (%s)" % (n, "; ".join(k for k, v in guards.items() if not v) or "all"),
                    steps_pts(n, [(7, 4), (5, 3), (3, 2), (1, 1)]), 4)])

    def gun(r, ev, val, res):
        g_ = r["last"][1].get("gun", "")
        return (r["last"][0] == ev and bool(GUN_RE.match(g_)) and int(g_) == val and r["result"] == res
                and r["pre"]["state"] == "SUBEDE_BEKLIYOR")
    a = any_last(lambda r: gun(r, "SUBEDEN_TESLIM", 5, "KABUL")) or \
        any(("SUBEDEN_TESLIM", 5) in r["prefix_gun"] for r in ok)
    a = a and any_last(lambda r: gun(r, "SUBEDEN_TESLIM", 6, "ERR_BEKLEME_SURESI"))
    b = any_last(lambda r: gun(r, "SURE_DOLDU", 6, "KABUL")) or \
        any(("SURE_DOLDU", 6) in r["prefix_gun"] for r in ok)
    b = b and any_last(lambda r: gun(r, "SURE_DOLDU", 5, "ERR_SURE_DOLMADI"))
    Z["Z5"] = (2, [("SUBEDEN_TESLIM gun=5 accepted and gun=6 refused", 1 if a else 0, 1),
                   ("SURE_DOLDU gun=6 accepted and gun=5 refused", 1 if b else 0, 1)])
    a = any_last(lambda r: r["result"] != "KABUL" and r["pre"]["deneme"] >= 1)
    b = any(r["deneme"] >= 1 and "G9" in r["fired"] for r in ok)
    Z["Z6"] = (2, [("a rejected event leaves a non-zero deneme_sayisi unchanged (10.5 rule 5)", 1 if a else 0, 1),
                   ("a RED refusal after a counted attempt leaves the counter unchanged", 1 if b else 0, 1)])
    a = any_last(lambda r: r["result"] == "ERR_GECERSIZ_GIRDI" and r["last"][0] in TABLE.get(r["pre"]["state"], ()))

    def order_row(r):
        ev, pr = r["last"]
        if ev not in EVENTS:                    # rule 1 before rule 2: unknown event in a final state
            return r["pre"]["state"] in FINAL and r["result"] == "ERR_GECERSIZ_GIRDI"
        spec = EVENTS[ev]
        bad = set(pr) != set(spec) or not all(spec[k](v) for k, v in pr.items())
        return bad and r["result"] == "ERR_GECERSIZ_GECIS"      # rule 2 before rule 3
    b = any_last(order_row)
    Z["Z7"] = (2, [("invalid or missing parameter on an allowed event -> ERR_GECERSIZ_GIRDI", 1 if a else 0, 1),
                   ("rule order 10.5 (state check before parameters, or unknown event in a final state)",
                    1 if b else 0, 1)])
    return Z, {"transitions_missing": sorted(live - cov_t, key=lambda x: int(x[1:])),
               "pairs_missing": sorted("%s>%s" % p for p in pairs - cov_p)}


def annotate_prefix_gun(g):
    """Record (event, gun) of accepted time-guarded events in the prefix, for the Z5 accept side."""
    for r in g["correct"]:
        seq = parse_sequence(r["row"]["olay_dizisi"])
        r["prefix_gun"] = tuple((ev, int(pr["gun"])) for ev, pr in seq[:-1] if "gun" in pr)


# --------------------------------------------------------------------------------------------
# Configuration model (spec section 11)
# --------------------------------------------------------------------------------------------
CFG = [
    ("kanal", ("WEB", "MOBIL", "GISE", "CAGRI", "API")),
    ("musteri_tipi", ("BIREYSEL", "KURUMSAL")),
    ("hizmet", ("STANDART", "EKSPRES", "AYNI_GUN")),
    ("bolge", ("SEHIRICI", "YAKIN", "UZAK")),
    ("odeme", ("GONDERICI_NAKIT", "GONDERICI_KART", "ALICI_ODEMELI", "CARI_HESAP")),
    ("teslim_noktasi", ("ADRES", "SUBE", "OTOMAT")),
]
TRIPLE = (2, 3, 5)   # hizmet x bolge x teslim_noktasi


def cfg_violations(c):
    kanal, mus, hiz, bol, ode, nok = c
    v = []
    if hiz == "AYNI_GUN" and bol != "SEHIRICI":
        v.append("KS-1")
    if ode == "CARI_HESAP" and mus != "KURUMSAL":
        v.append("KS-2")
    if kanal == "API" and mus != "KURUMSAL":
        v.append("KS-3")
    if ode == "ALICI_ODEMELI" and mus != "BIREYSEL":
        v.append("KS-4")
    if nok == "OTOMAT" and ode == "ALICI_ODEMELI":
        v.append("KS-5")
    if hiz == "AYNI_GUN" and nok != "ADRES":
        v.append("KS-6")
    if ode == "GONDERICI_NAKIT" and kanal not in ("GISE", "CAGRI"):
        v.append("KS-7")
    return v


def cfg_facts():
    combos = [c for c in itertools.product(*[v for _, v in CFG]) if not cfg_violations(c)]
    pairs, triples = set(), set()
    for c in combos:
        for i, j in itertools.combinations(range(len(CFG)), 2):
            pairs.add((i, c[i], j, c[j]))
        triples.add(tuple(c[i] for i in TRIPLE))
    return combos, pairs, triples


def grade_konfig(tab):
    combos, pairs, triples = cfg_facts()
    out = {"valid": 0, "bad": [], "pairs_total": len(pairs), "triples_total": len(triples)}
    cp, ct = set(), set()
    for row in tab["rows"]:
        c = tuple(row[name] for name, _ in CFG)
        unknown = [name for (name, vals), v in zip(CFG, c) if v not in vals]
        if unknown or row["_extra"]:
            out["bad"].append("%s: unknown value in %s" % (row["test_id"], ",".join(unknown) or "extra column"))
            continue
        v = cfg_violations(c)
        if v:
            out["bad"].append("%s: violates %s" % (row["test_id"], ",".join(v)))
            continue
        out["valid"] += 1
        for i, j in itertools.combinations(range(len(CFG)), 2):
            cp.add((i, c[i], j, c[j]))
        ct.add(tuple(c[i] for i in TRIPLE))
    out["pairs_covered"] = len(cp)
    out["triples_covered"] = len(ct)
    out["pairs_missing"] = sorted("%s=%s & %s=%s" % (CFG[i][0], a, CFG[j][0], b) for i, a, j, b in pairs - cp)
    out["triples_missing"] = sorted("/".join(t) for t in triples - ct)
    return out


def score_konfig(g, tab):
    C = {}
    n = g["triples_covered"]
    C["C1"] = (6, [("hizmet x bolge x teslim_noktasi triples: %d of %d" % (n, g["triples_total"]),
                    steps_pts(n, [(19, 6), (17, 4), (14, 2)]), 6)])
    pct = 100.0 * g["pairs_covered"] / g["pairs_total"]
    C["C2"] = (6, [("pairs over all six factors: %d of %d" % (g["pairs_covered"], g["pairs_total"]),
                    steps_pts(pct, [(100, 6), (95, 4), (85, 2)]), 6)])
    clean = g["valid"] >= 12 and not g["bad"] and tab["over_budget"] == 0
    C["C3"] = (2, [("at least 12 rows, only supported combinations, inside the row budget", 2 if clean else 0, 2)])
    return C


# --------------------------------------------------------------------------------------------
# Specification findings (planted defects D1..D5, traps T1..T4)
# --------------------------------------------------------------------------------------------
_TR = str.maketrans({"ç": "c", "Ç": "C", "ğ": "g", "Ğ": "G", "ı": "i", "İ": "I", "ö": "o", "Ö": "O",
                     "ş": "s", "Ş": "S", "ü": "u", "Ü": "U", "§": " "})
_SEP = r"[\s\-/#:_.]*"
_END = r"\b(?!\.\d)"          # 'A 7.1' is not example A-7
REF_RE = re.compile(
    r"(?:\bEK" + _SEP + r")?\bA" + _SEP + r"(?:ORNEK" + _SEP + r")?(?P<a>\d+)" + _END +
    r"|\bORNEK" + _SEP + r"(?P<o>\d+)" + _END +
    r"|(?:\bEK" + _SEP + r")?\bB" + _SEP + r"(?P<b>\d+)" + _END +
    r"|\bG" + _SEP + r"(?P<g>\d+)" + _END +
    r"|\bKS" + _SEP + r"(?P<k>\d+)" + _END +
    r"|(?P<n>\d+(?:\.\d+)*)")
TYPES = ("CELISKI", "BELIRSIZLIK", "ERISILEMEZ", "ONERI")
CORRECT_EXAMPLES = ("A-1", "A-2", "A-3", "A-5", "A-6", "A-7")


def norm_refs(text):
    """'2.4, Ek-A Ornek 4 ve G-11' -> {'2.4', 'A-4', 'G11'}. Lenient: the reference is the same."""
    t = text.translate(_TR).upper()
    refs = set()
    for m in REF_RE.finditer(t):
        if m.group("a"):
            refs.add("A-%d" % int(m.group("a")))
        elif m.group("o"):
            refs.add("A-%d" % int(m.group("o")))
        elif m.group("b"):
            refs.add("B-%d" % int(m.group("b")))
        elif m.group("g"):
            refs.add("G%d" % int(m.group("g")))
        elif m.group("k"):
            refs.add("KS-%d" % int(m.group("k")))
        else:
            refs.add(m.group("n"))
    return refs


DEFECTS = [   # id, points, accepted types, predicate on the reference set, short label
    ("D1", 3, ("CELISKI",), lambda s: "A-4" in s,
     "Ek-A example A-4 contradicts 7.1 (fuel surcharge taken on TB instead of NTB)"),
    ("D2", 4, ("CELISKI", "BELIRSIZLIK"), lambda s: "2.4" in s and "8.2" in s,
     "2.4 (before the cut-off) vs 8.2 (cut-off inclusive)"),
    ("D3", 4, ("BELIRSIZLIK", "CELISKI"), lambda s: "9.3" in s and "7.2" in s,
     "ERR_BEYAN_LIMIT (7.2) has no place in the precedence list 9.3"),
    ("D4", 5, ("ERISILEMEZ", "CELISKI"), lambda s: "G11" in s,
     "G11 can never fire (counter is 1 or 2 in TESLIM_EDILEMEDI)"),
    ("D5", 4, ("BELIRSIZLIK",), lambda s: bool(s & {"10.3", "10.6", "G14", "G15"}),
     "unit of 'gun' / the 5-day waiting period (calendar or business days) is not stated"),
]
MAX_REFS = 4   # TASK.md: one finding per row, at most four places


def trap_hits(refs, tur):
    hits = []
    if tur == "CELISKI":
        hits += ["T1:%s" % a for a in CORRECT_EXAMPLES if a in refs]
    if tur == "ERISILEMEZ" and "G16" in refs:
        hits.append("T2")
    if tur in ("CELISKI", "BELIRSIZLIK") and "8.2" in refs and "8.6" in refs:
        hits.append("T3")
    if tur in ("CELISKI", "ERISILEMEZ") and "4.2" in refs and ("4.5" in refs or "5.1" in refs):
        hits.append("T4")
    return hits


def grade_bulgu(tab):
    out = {"found": {}, "traps": {}, "ignored": [], "neutral": []}
    for row in tab["rows"]:
        tur = row["tur"].translate(_TR).upper()
        refs = norm_refs(row["bolumler"])
        rid = row["bulgu_id"]
        if tur not in TYPES:
            out["ignored"].append("%s: unknown type %r" % (rid, row["tur"]))
            continue
        if len(refs) > MAX_REFS:
            out["ignored"].append("%s: more than %d places in one finding" % (rid, MAX_REFS))
            continue
        matched = [d for d in DEFECTS if tur in d[2] and d[3](refs)]
        if matched:   # one row is one finding: it can earn one defect, the first not yet credited
            new = [d for d in matched if d[0] not in out["found"]]
            if new:
                out["found"][new[0][0]] = rid
            continue
        hits = trap_hits(refs, tur)
        if hits:
            for h in hits:
                out["traps"].setdefault(h, rid)
        else:
            out["neutral"].append("%s [%s] %s" % (rid, tur, ",".join(sorted(refs)) or "-"))
    return out


def score_bulgu(g):
    F = {}
    for did, pts, _, _, label in DEFECTS:
        hit = did in g["found"]
        F[did] = (pts, [("%s%s" % (label, " (row %s)" % g["found"][did] if hit else ""), pts if hit else 0, pts)])
    return F


# --------------------------------------------------------------------------------------------
# Whole-folder grading
# --------------------------------------------------------------------------------------------
AREAS = (("ucret", "Pricing and delivery date", 44), ("durum", "Shipment life cycle", 22),
         ("konfig", "Configuration matrix", 14), ("bulgu", "Specification findings", 20))


def grade_folder(folder):
    res = {"folder": os.path.abspath(folder), "areas": {}, "max": MAX_SCORE}
    total = 0
    for kind, title, amax in AREAS:
        tab = read_table(os.path.join(folder, FILES[kind]), kind)
        area = {"title": title, "max": amax, "file": FILES[kind], "ok": tab["ok"], "problem": tab["problem"],
                "rows_total": tab["total_rows"], "rows_graded": len(tab["rows"]),
                "over_budget": tab["over_budget"], "warnings": tab["warnings"], "items": {},
                "penalties": [], "details": {}}
        if tab["ok"]:
            if kind == "ucret":
                g = grade_ucret(tab)
                items = score_ucret(g)
            elif kind == "durum":
                g = grade_durum(tab)
                annotate_prefix_gun(g)
                items, extra = score_durum(g)
                area["details"].update(extra)
            elif kind == "konfig":
                g = grade_konfig(tab)
                items = score_konfig(g, tab)
                area["details"].update({k: g[k] for k in ("valid", "pairs_missing", "triples_missing")})
                for b in g["bad"]:
                    area["penalties"].append((PEN_ROW, "unsupported combination " + b))
            else:
                g = grade_bulgu(tab)
                items = score_bulgu(g)
                area["details"].update({"neutral_rows": g["neutral"], "ignored_rows": g["ignored"]})
                for trap, rid in sorted(g["traps"].items()):
                    area["penalties"].append((PEN_TRAP, "trap %s reported as a defect (row %s)" % (trap, rid)))
            if kind in ("ucret", "durum"):
                area["details"]["correct"] = len(g["correct"])
                area["details"]["incomplete"] = ["%s: blank %s" % (r["id"], ",".join(r["blanks"]))
                                                 for r in g["incomplete"]]
                for r in g["wrong"]:
                    area["penalties"].append((PEN_ROW, "wrong row %s: %s" % (r["id"], "; ".join(r["mismatch"]))))
            if tab["over_budget"]:
                area["penalties"].append((PEN_BUDGET, "row budget %d exceeded by %d row(s); the extra rows are "
                                          "not graded" % (BUDGET[kind], tab["over_budget"])))
            for key, (imax, subs) in items.items():
                area["items"][key] = {"max": imax, "got": sum(s[1] for s in subs),
                                      "sub": [{"label": s[0], "got": s[1], "max": s[2]} for s in subs]}
        got = sum(i["got"] for i in area["items"].values())
        pen = sum(p for p, _ in area["penalties"])
        area["points"] = got
        area["penalty"] = pen
        area["score"] = max(0, got - pen)
        total += area["score"]
        res["areas"][kind] = area
    res["final"] = total
    res["percent"] = round(100.0 * total / MAX_SCORE, 1)
    return res


def print_report(res, verbose=False):
    p = print
    p("=== trial-design2 grader (GUM v3.2) ===")
    p("Folder: %s" % res["folder"])
    for kind, _, _ in AREAS:
        a = res["areas"][kind]
        p("")
        p("--- %s (%s): %d / %d" % (a["title"], a["file"], a["score"], a["max"]))
        if not a["ok"]:
            p("    NOT GRADED: %s" % a["problem"])
            continue
        p("    rows: %d in file, %d graded (budget %d)" % (a["rows_total"], a["rows_graded"], BUDGET[kind]))
        for key, it in a["items"].items():
            p("    %-4s %d/%d" % (key, it["got"], it["max"]))
            for s in it["sub"]:
                p("         [%s] %s (%d/%d)" % ("x" if s["got"] == s["max"] else ("~" if s["got"] else " "),
                                              s["label"], s["got"], s["max"]))
        p("    points %d, penalty -%d" % (a["points"], a["penalty"]))
        for pts, txt in a["penalties"]:
            p("      -%d %s" % (pts, txt))
        d = a["details"]
        for key in ("transitions_missing", "pairs_missing", "triples_missing", "incomplete", "neutral_rows",
                    "ignored_rows"):
            if d.get(key) and (verbose or len(d[key]) <= 12):
                p("    %s: %s" % (key, "; ".join(d[key])))
            elif d.get(key):
                p("    %s: %d entries (use --verbose)" % (key, len(d[key])))
        for w in a["warnings"]:
            p("    warning: %s" % w)
    p("")
    p("FINAL SCORE: %d / %d  (%s%%)" % (res["final"], res["max"], res["percent"]))


# --------------------------------------------------------------------------------------------
# Self-test of the oracle against the specification
# --------------------------------------------------------------------------------------------
def _p(mus, ga, en, boy, yuk, bolge, hizmet, kod, beyan, kz):
    return price({"musteri_tipi": mus, "agirlik_kg": ga, "en_cm": str(en), "boy_cm": str(boy),
                  "yukseklik_cm": str(yuk), "bolge": bolge, "hizmet": hizmet, "kampanya_kodu": kod,
                  "beyan_degeri": beyan, "kabul_zamani": kz})


def selftest():
    ok = True

    def chk(name, got, exp):
        nonlocal ok
        flag = got == exp
        ok &= flag
        print("%-74s %s%s" % (name, "OK" if flag else "FAIL", "" if flag else "  got %r, expected %r" % (got, exp)))

    def summary(r):
        c = r["calc"]
        return ("%.1f" % c["ua"], str(c["tb"]), str(c["it"]), str(c["ye"]), str(c["sp"]), str(c["kdv"]),
                str(c["tu"]), "/".join(sorted({v["teslim"].isoformat() for v in r["variants"]})))

    # calendar facts printed in Ek-B
    wd = ["Pzt", "Sal", "Car", "Per", "Cum", "Cmt", "Paz"]
    chk("Ek-B weekdays", [wd[d.weekday()] for d in sorted(HOLIDAYS)],
        ["Cmt", "Paz", "Pzt", "Cum", "Cmt", "Car", "Paz"])
    chk("2028-02-29 exists and is a Tuesday", wd[dt.date(2028, 2, 29).weekday()], "Sal")
    # Ek-A examples exactly as printed in the specification
    chk("A-1", summary(_p("BIREYSEL", "2.00", 20, 20, 10, "YAKIN", "STANDART", "", "", "2028-03-06 10:15")),
        ("2.0", "105.00", "0.00", "6.83", "0.00", "22.37", "134.20", "2028-03-09"))
    chk("A-2 (trap: UZAK Saturday rule 8.4)",
        summary(_p("BIREYSEL", "3.20", 40, 30, 25, "UZAK", "STANDART", "", "", "2028-06-12 09:30")),
        ("10.0", "195.00", "0.00", "12.68", "0.00", "41.54", "249.22", "2028-06-19"))
    chk("A-3 (trap: HA 5.0033 -> 5.00, minimum premium)",
        summary(_p("KURUMSAL", "4.80", 10, 19, 79, "SEHIRICI", "EKSPRES", "", "1200.00", "2028-02-25 16:10")),
        ("5.0", "114.75", "13.77", "6.56", "15.00", "24.51", "147.05", "2028-02-26"))
    r = _p("KURUMSAL", "12.00", 30, 30, 30, "YAKIN", "STANDART", "", "", "2028-04-11 11:20")
    chk("A-4 by the rules (spec prints YE 11.31 / KDV 32.89 / TU 197.32 = planted D1)", summary(r),
        ("12.0", "174.00", "20.88", "9.95", "0.00", "32.61", "195.68", "2028-04-14"))
    chk("A-4 as printed = fuel surcharge on TB", str(q2(D("174.00") * D("0.065"))), "11.31")
    chk("A-5 (trap: campaign by acceptance date, processed 06-01)",
        summary(_p("BIREYSEL", "6.40", 30, 20, 20, "YAKIN", "EKSPRES", "BAHAR15", "", "2028-05-31 17:45")),
        ("6.5", "202.50", "30.38", "11.19", "0.00", "36.66", "219.97", "2028-06-02"))
    chk("A-6 (trap: capped campaign beats 12 %; TB 285.525 -> 285.53)",
        summary(_p("KURUMSAL", "11.00", 30, 30, 20, "UZAK", "EKSPRES", "BAHAR15", "20000.00", "2028-04-08 12:40")),
        ("11.0", "285.53", "40.00", "15.96", "160.00", "84.30", "505.79", "2028-04-11"))
    chk("A-7 (trap: no discount on AYNI_GUN)",
        summary(_p("KURUMSAL", "0.80", 20, 15, 5, "SEHIRICI", "AYNI_GUN", "", "", "2028-09-14 10:05")),
        ("1.0", "108.00", "0.00", "7.02", "0.00", "23.00", "138.02", "2028-09-14"))
    # weight rounding
    chk("HA 15015/3000 = 5.005 -> 5.01 -> UA 5.5", _p("BIREYSEL", "1.00", 15, 77, 13, "YAKIN", "STANDART", "", "", "2028-03-06 10:00")["steps"], 11)
    chk("HA 15010/3000 = 5.0033 -> 5.00 -> UA 5.0", _p("BIREYSEL", "1.00", 10, 19, 79, "YAKIN", "STANDART", "", "", "2028-03-06 10:00")["steps"], 10)
    chk("UA 40.0 accepted (50x50x48)", _p("BIREYSEL", "1.00", 50, 50, 48, "YAKIN", "STANDART", "", "", "2028-03-06 10:00")["accept_err"], [])
    chk("UA 40.5 -> ERR_HACIM (49x50x49)", _p("BIREYSEL", "1.00", 49, 50, 49, "YAKIN", "STANDART", "", "", "2028-03-06 10:00")["accept_err"], ["ERR_HACIM"])
    # discounts
    r = _p("KURUMSAL", "18.00", 10, 10, 10, "UZAK", "STANDART", "BAHAR15", "", "2028-03-06 10:00")
    chk("KURUMSAL+BAHAR15 TB 327.00 -> IT 40.00 (campaign)", (str(r["calc"]["tb"]), str(r["calc"]["it"])), ("327.00", "40.00"))
    r = _p("KURUMSAL", "18.50", 10, 10, 10, "UZAK", "STANDART", "BAHAR15", "", "2028-03-06 10:00")
    chk("KURUMSAL+BAHAR15 TB 335.25 -> IT 40.23 (contract)", (str(r["calc"]["tb"]), str(r["calc"]["it"])), ("335.25", "40.23"))
    r = _p("BIREYSEL", "1.00", 10, 10, 10, "SEHIRICI", "STANDART", "BAHAR15", "", "2028-03-06 10:00")
    chk("floor: TB 60.00, 15 % = 9.00 -> IT 5.00, TU 70.30", (str(r["calc"]["it"]), str(r["calc"]["tu"])), ("5.00", "70.30"))
    r = _p("BIREYSEL", "2.00", 10, 10, 10, "YAKIN", "STANDART", "BAHAR15", "", "2028-02-29 18:00")
    chk("BAHAR15 on 02-29 after cut-off (processed 03-01): not applied", str(r["calc"]["it"]), "0.00")
    # planted D2 and D3: both readings accepted
    r = _p("BIREYSEL", "2.00", 10, 10, 10, "YAKIN", "EKSPRES", "", "", "2028-03-06 17:00")
    chk("D2: 17:00 exactly accepts both dates", sorted(v["teslim"].isoformat() for v in r["variants"]), ["2028-03-07", "2028-03-08"])
    r = _p("BIREYSEL", "2.00", 10, 10, 10, "YAKIN", "EKSPRES", "", "", "2028-03-06 17:01")
    chk("17:01 is unambiguous", [v["teslim"].isoformat() for v in r["variants"]], ["2028-03-08"])
    r = _p("BIREYSEL", "30.01", 10, 10, 10, "YAKIN", "EKSPRES", "", "50000.01", "2028-03-06 10:00")
    chk("D3: ERR_BEYAN_LIMIT together with ERR_AGIRLIK accepts both", r["accept_err"], ["ERR_AGIRLIK", "ERR_BEYAN_LIMIT"])
    chk("precedence ERR_BOYUT before ERR_HACIM", _p("BIREYSEL", "1.00", 101, 60, 60, "YAKIN", "EKSPRES", "", "", "2028-03-06 10:00")["accept_err"], ["ERR_BOYUT"])
    chk("lower-case code -> ERR_GECERSIZ_GIRDI", _p("bireysel", "1.00", 10, 10, 10, "YAKIN", "EKSPRES", "", "", "2028-03-06 10:00")["accept_err"], ["ERR_GECERSIZ_GIRDI"])
    chk("2028-02-30 -> ERR_GECERSIZ_GIRDI", _p("BIREYSEL", "1.00", 10, 10, 10, "YAKIN", "EKSPRES", "", "", "2028-02-30 10:00")["accept_err"], ["ERR_GECERSIZ_GIRDI"])
    # life cycle
    live, pairs = model_facts()
    chk("live transitions", sorted(set(ALL_G) - live), ["G11"])
    chk("feasible 1-switch pairs", len(pairs), 29)
    ctx = new_ctx()
    seq = parse_sequence("TRANSFERE_VER > DAGITIMA_CIKAR > TESLIM_BASARISIZ(neden=ADRESTE_YOK) > SUBEYE_YONLENDIR > "
                         "YENIDEN_DAGIT > TESLIM_BASARISIZ(neden=ADRESTE_YOK) > YENIDEN_DAGIT > "
                         "TESLIM_BASARISIZ(neden=ADRESTE_YOK) > YENIDEN_DAGIT")
    out = [apply_event(ctx, e, pr) for e, pr in seq]
    chk("G16 is live (trap T2) and the 3rd failure leads to ERR_DENEME_LIMITI",
        ([g for _, g in out][3:5], out[-1][0], ctx["state"], ctx["deneme"]),
        (["G12", "G16"], "ERR_DENEME_LIMITI", "SUBEDE_BEKLIYOR", 3))
    ctx = new_ctx()
    apply_event(ctx, "TRANSFERE_VER", {})
    chk("case-sensitive parameter value", apply_event(ctx, "IPTAL", {"aktor": "operator"})[0], "ERR_GECERSIZ_GIRDI")
    chk("state check before parameter check", apply_event(ctx, "SUBEDEN_TESLIM", {})[0], "ERR_GECERSIZ_GECIS")
    # configuration model
    combos, cpairs, triples = cfg_facts()
    chk("config: valid combinations / pairs / triples", (len(combos), len(cpairs), len(triples)), (394, 152, 19))
    chk("config: API with ALICI_ODEMELI is infeasible (KS-3 + KS-4)",
        any(c[0] == "API" and c[4] == "ALICI_ODEMELI" for c in combos), False)
    # reference normaliser
    chk("norm_refs", norm_refs("2.4, Ek-A Örnek 4 ve G-11; §9.3 / KS2"), {"2.4", "A-4", "G11", "9.3", "KS-2"})
    print("SELFTEST", "PASSED" if ok else "FAILED")
    return 0 if ok else 1


def main(argv=None):
    try:
        sys.stdout.reconfigure(errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description="Grader for evals/trial-design2")
    ap.add_argument("cikti", nargs="?", help="folder with the four CSV deliverables")
    ap.add_argument("--json", help="write the full result to this file")
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    if not a.cikti:
        ap.error("the cikti folder is required")
    res = grade_folder(a.cikti)
    print_report(res, a.verbose)
    if a.json:
        with open(a.json, "w", encoding="utf-8") as f:
            json.dump(res, f, ensure_ascii=False, indent=2, default=str)
    return 0


if __name__ == "__main__":
    sys.exit(main())
