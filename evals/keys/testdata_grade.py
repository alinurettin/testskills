#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Objective grader for trial-testdata (TEST DATA PREPARATION and MASKING).
Python 3 stdlib only. Key/rubric: testdata.md (same folder).

Usage
  python testdata_grade.py --teslim <workdir>/teslim [--rerun] [--run2 <dir>] [--fp N] [--json out.json]
  python testdata_grade.py --check-inputs          # verify every planted item is present in the pristine inputs

  --teslim   the agent's delivery folder (contains uretim/, maskeleme/, RAPOR.md, uret.*, maskele.*)
  --girdi    pristine input folder (default: ../trial-testdata/girdi next to this script). Always grade
             against the pristine copy, never against the agent's working copy.
  --rerun    re-run the agent's uret.(py|js) and maskele.(py|js) into temp folders (MASKELEME_ANAHTARI unset)
             and compare byte-for-byte with the delivered outputs (determinism evidence, M4 / G6).
  --run2     alternative to --rerun: a folder holding a second run (either a teslim-like folder with
             uretim/ + maskeleme/, or a folder that directly holds the two masked CSVs).
  --fp N     number of false positives confirmed by the human reviewer (trap hits); -2 points each.
"""
import argparse
import csv
import datetime as dt
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_GIRDI = os.path.normpath(os.path.join(HERE, "..", "trial-testdata", "girdi"))
REF = dt.date(2026, 9, 30)

# ----------------------------------------------------------------------------------------------
# Planted values (must match girdi/canli_kesit; verified by --check-inputs)
# ----------------------------------------------------------------------------------------------
PLANTED = {
    "phones_notes": {  # K1 -- national 10-digit form; P1 is customer MS-100411's own mobile in another format
        "P1": ("0551 960 07 12", "5519600712"),
        "P2": ("+90 (505) 318 44 12", "5053184412"),
        "P3": ("5427781203", "5427781203"),
        "P4": ("0 555 902 11 36", "5559021136"),
        "P5": ("0 (216) 455 70 81", "2164557081"),
        "P6": ("0505-771-20-93", "5057712093"),
        "P7": ("+905366102284", "5366102284"),
    },
    "emails_notes": {  # K2
        "E1": "SEBNEM.OGUZHANOGLU@POSTA.EXAMPLE.TEST",
        "E2": "ozlem.tas1987@example.test",
        "E3": "hasan.yurekli@karacamtekstil.example.test",
        "E4": "tunc.egilmez.1979@example.test",
    },
    "tckn_notes": {"C1": "27075526846", "C2": "27060945126", "C3": "63202010420"},  # K3
    "ibans_aciklama": {  # K5
        "I1": "TR750099200000123456789012",
        "I2": "TR850099300000098765432101",
        "I3": "TR170099100000456712339822",
    },
    "third_party_names": ["Hasan Yürekli", "Nurten Akbulut", "Tuğrul Başaran", "Saadet Kılınçarslan", "Özlem Taş"],
    "legacy_tckn_rows": [7, 9, 11, 13, 15, 18, 19, 23, 25, 27, 30, 32, 34, 36, 39],  # K4, 1-based data rows
    "dirty_key_rows": [14, 21, 23],  # K8, 1-based data rows of destek_kayitlari
    "special_csv_rows": {15: "yeni numara sisteme", 28: "basımı başlatıldı", 29: "acil"},  # K7b
    "t4_lookalikes": ["20240227114", "71004583216", "0850 455 12 12", "destek@yelkovan.example.test"],
    "ykn": "99086354688",
    "n_ozet": 40,
    "n_destek": 60,
}

OZ_COLS = ["musteri_no", "ad_soyad", "kimlik_no", "musteri_tipi", "dogum_tarihi", "cinsiyet", "il", "posta_kodu",
           "cep_telefonu", "eposta", "eski_musteri_kodu", "segment", "kayit_tarihi"]
DK_COLS = ["kayit_no", "musteri_no", "tarih", "kanal", "konu", "aciklama", "temsilci_notu", "islem_tutari", "durum"]
MUS = ["musteri_no", "musteri_tipi", "ad", "soyad", "unvan", "tckn", "vkn", "dogum_tarihi", "telefon", "eposta", "il",
       "kayit_tarihi", "senaryo"]
HES = ["hesap_no", "musteri_no", "iban", "banka_kodu", "doviz", "acilis_tarihi", "durum", "kapanis_tarihi", "bakiye",
       "senaryo"]
ISL = ["islem_no", "hesap_no", "islem_tarihi", "islem_tipi", "tutar", "karsi_iban", "aciklama", "senaryo"]

ILLER = set("""Adana Adıyaman Afyonkarahisar Ağrı Amasya Ankara Antalya Artvin Aydın Balıkesir Bilecik Bingöl Bitlis
Bolu Burdur Bursa Çanakkale Çankırı Çorum Denizli Diyarbakır Edirne Elazığ Erzincan Erzurum Eskişehir Gaziantep
Giresun Gümüşhane Hakkari Hatay Isparta Mersin İstanbul İzmir Kars Kastamonu Kayseri Kırklareli Kırşehir Kocaeli
Konya Kütahya Malatya Manisa Kahramanmaraş Mardin Muğla Muş Nevşehir Niğde Ordu Rize Sakarya Samsun Siirt Sinop
Sivas Tekirdağ Tokat Trabzon Tunceli Şanlıurfa Uşak Van Yozgat Zonguldak Aksaray Bayburt Karaman Kırıkkale Batman
Şırnak Bartın Ardahan Iğdır Yalova Karabük Kilis Osmaniye Düzce""".split())
assert len(ILLER) == 81
ILLER_OK = ILLER | {"Hakkâri"}
TR_CHARS = set("çğıİöşüÇĞÖŞÜ")
MOJIBAKE = ["�", "Ã", "Ä", "Å", "Ý", "Þ", "ð", "ý", "þ"]


# ----------------------------------------------------------------------------------------------
# validators / helpers
# ----------------------------------------------------------------------------------------------
def tckn_valid(s):
    if not (len(s) == 11 and s.isdigit() and s[0] != "0"):
        return False
    d = [int(c) for c in s]
    d10 = ((d[0] + d[2] + d[4] + d[6] + d[8]) * 7 - (d[1] + d[3] + d[5] + d[7])) % 10
    d11 = (sum(d[:9]) + d10) % 10
    return d[9] == d10 and d[10] == d11


def vkn_valid(s):
    if not (len(s) == 10 and s.isdigit()):
        return False
    total = 0
    for i in range(9):
        tmp = (int(s[i]) + 9 - i) % 10
        v = (tmp * (2 ** (9 - i))) % 9
        if tmp != 0 and v == 0:
            v = 9
        total += v
    return (10 - total % 10) % 10 == int(s[9])


def iban_valid(s):
    s = s.replace(" ", "")
    if len(s) != 26 or not s.startswith("TR") or not s[2:].isdigit() or s[9] != "0":
        return False
    r = s[4:] + s[:4]
    return int("".join(str(int(c, 36)) for c in r)) % 97 == 1


DATE_RE = re.compile(r"^(\d{2})\.(\d{2})\.(\d{4})$")
AMT_RE = re.compile(r"^-?\d+,\d{2}$")
EMAIL_TOKEN_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")


def pdate(s):
    m = DATE_RE.match(s or "")
    if not m:
        return None
    try:
        return dt.date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
    except ValueError:
        return None


def amt(s):
    if not AMT_RE.match(s or ""):
        return None
    return round(float(s.replace(",", ".")), 2)


def age_on(dob, day):
    a = day.year - dob.year - ((day.month, day.day) < (dob.month, dob.day))
    # lenient 29.02 rule: birthday counted as reached on 28.02 in non-leap years
    if (dob.month, dob.day) == (2, 29) and (day.month, day.day) == (2, 28):
        a = day.year - dob.year
    return a


def digits(s):
    return re.sub(r"\D", "", s or "")


def fold(s):
    return (s or "").replace("İ", "i").replace("I", "ı").lower()


ASCII_MAP = str.maketrans("çğıöşüâîû", "cgiosuaiu")


def afold(s):
    return fold(s).translate(ASCII_MAP)


def word_in(word, text):
    w = afold(word)
    return re.search(r"(?<![a-z0-9])" + re.escape(w) + r"(?![a-z0-9])", afold(text)) is not None


def skel(s):
    return "".join(c.lower() if (c.isascii() and c.isalnum()) or c == " " else "?" for c in (s or ""))


def name_in(name, text):
    """full-name match; tolerant to case, Turkish/ASCII folding and to mojibake of non-ASCII letters"""
    if afold(name) in afold(text):
        return True
    pat = "".join("[^a-z0-9 ]{1,2}" if ch == "?" else re.escape(ch) for ch in skel(name))
    return re.search(pat, skel(text)) is not None


def read_text(path):
    """returns (text, encoding, strict_utf8)"""
    raw = open(path, "rb").read()
    try:
        return raw.decode("utf-8-sig"), "utf-8", True
    except UnicodeDecodeError:
        pass
    try:
        return raw.decode("cp1254"), "cp1254", False
    except UnicodeDecodeError:
        return raw.decode("latin-1"), "latin-1", False


def parse_csv(text):
    return list(csv.reader(io.StringIO(text, newline=""), delimiter=";"))


def load_table(path):
    text, enc, strict = read_text(path)
    rows = parse_csv(text)
    return {"header": rows[0] if rows else [], "rows": rows[1:], "enc": enc, "utf8": strict, "text": text}


def as_dicts(tab, cols):
    h = tab["header"]
    idx = {c: (h.index(c) if c in h else (cols.index(c) if cols.index(c) < len(h) else None)) for c in cols}
    out = []
    for r in tab["rows"]:
        if not any(x.strip() for x in r):
            continue
        out.append({c: (r[i].strip() if i is not None and i < len(r) else "") for c, i in idx.items()})
    return out


def find_file(folder, name, hints):
    p = os.path.join(folder, name)
    if os.path.isfile(p):
        return p, None
    if not os.path.isdir(folder):
        return None, "klasör yok: %s" % folder
    cands = [f for f in os.listdir(folder) if f.lower().endswith(".csv") and any(h in f.lower() for h in hints)]
    if len(cands) == 1:
        return os.path.join(folder, cands[0]), "dosya adı farklı: %s" % cands[0]
    return None, "bulunamadı: %s" % name


def pts(score, maxp, detail, status=None):
    return {"score": round(score, 2), "max": maxp, "detail": detail, "status": status}


# ----------------------------------------------------------------------------------------------
# pristine inputs
# ----------------------------------------------------------------------------------------------
def load_pristine(girdi):
    ck = os.path.join(girdi, "canli_kesit")
    oz_raw = open(os.path.join(ck, "musteri_ozet.csv"), "rb").read()
    dk_raw = open(os.path.join(ck, "destek_kayitlari.csv"), "rb").read()
    oz = parse_csv(oz_raw.decode("utf-8-sig"))
    dk = parse_csv(dk_raw.decode("cp1254"))
    return {"oz_h": oz[0], "oz": oz[1:], "dk_h": dk[0], "dk": dk[1:], "oz_raw": oz_raw, "dk_raw": dk_raw}


def check_inputs(girdi):
    P = load_pristine(girdi)
    ok = True
    msgs = []

    def chk(cond, msg):
        nonlocal ok
        ok = ok and cond
        msgs.append(("OK  " if cond else "FAIL") + " " + msg)

    chk(P["oz_raw"].startswith(b"\xef\xbb\xbf"), "musteri_ozet.csv is UTF-8 with BOM")
    try:
        P["dk_raw"].decode("utf-8")
        chk(False, "destek_kayitlari.csv is NOT valid UTF-8 (cp1254)")
    except UnicodeDecodeError:
        chk(True, "destek_kayitlari.csv is NOT valid UTF-8 (cp1254)")
    chk(len(P["oz"]) == PLANTED["n_ozet"] and len(P["dk"]) == PLANTED["n_destek"], "row counts 40 / 60")
    chk(P["oz_h"] == OZ_COLS and P["dk_h"] == DK_COLS, "headers")
    chk(all(len(r) == 9 for r in P["dk"]), "every destek record has 9 fields (quoted ; and newline parsed)")
    notes = [r[6] for r in P["dk"]]
    acik = [r[5] for r in P["dk"]]
    for k, (txt, nat) in PLANTED["phones_notes"].items():
        chk(any(txt in n for n in notes), "K1 %s phone '%s' in temsilci_notu" % (k, txt))
    chk(PLANTED["phones_notes"]["P1"][1] == digits(P["oz"][0][8])[2:], "K1 P1 equals customer row1 mobile")
    for k, e in PLANTED["emails_notes"].items():
        chk(any(e in n for n in notes), "K2 %s e-mail '%s' in temsilci_notu" % (k, e))
    for k, t in PLANTED["tckn_notes"].items():
        chk(tckn_valid(t) and any(t in n for n in notes), "K3 %s TCKN %s valid and in temsilci_notu" % (k, t))
    kim = {r[2] for r in P["oz"]}
    chk(PLANTED["tckn_notes"]["C2"] not in kim and PLANTED["tckn_notes"]["C3"] not in kim,
        "K3 C2/C3 are third-party TCKNs (not in kimlik_no)")
    chk("TC" + PLANTED["tckn_notes"]["C3"] in "".join(notes), "K3 C3 glued to 'TC' prefix")
    for r in PLANTED["legacy_tckn_rows"]:
        row = P["oz"][r - 1]
        chk(tckn_valid(row[10]) and row[10] == row[2], "K4 row %d eski_musteri_kodu holds the TCKN" % r)
    chk(all(not tckn_valid(P["oz"][i][10]) for i in range(5)), "K4 first 5 rows of eski_musteri_kodu are EMK codes")
    for k, ib in PLANTED["ibans_aciklama"].items():
        chk(iban_valid(ib) and any(digits(ib) in digits(a) for a in acik), "K5 %s IBAN %s valid and in aciklama" % (k, ib))
    pairs = [(r[4], r[7]) for r in P["oz"] if r[3] == "BIREYSEL"]
    chk(len(set(pairs)) == len(pairs), "K6 (dogum_tarihi, posta_kodu) unique for every BIREYSEL row")
    oz_keys = {r[0] for r in P["oz"]}
    for r in PLANTED["dirty_key_rows"]:
        k = P["dk"][r - 1][1]
        chk(k not in oz_keys and k.strip().upper() in oz_keys, "K8 row %d key %r dirty but normalisable" % (r, k))
    clean = [r for i, r in enumerate(P["dk"], 1) if i not in PLANTED["dirty_key_rows"]]
    chk(all(r[1] in oz_keys for r in clean), "every clean destek key joins exactly")
    for r, tail in PLANTED["special_csv_rows"].items():
        chk(tail in P["dk"][r - 1][6], "K7b row %d special CSV field intact" % r)
    raw = P["dk_raw"]
    chk(b'""acil""' in raw and b"\xfd" in raw and b"\xfe" in raw, "raw bytes: doubled quotes + cp1254 ı/ş bytes")
    chk(not tckn_valid(PLANTED["t4_lookalikes"][0]) and not tckn_valid(PLANTED["t4_lookalikes"][1]),
        "T4 11-digit lookalikes FAIL the TCKN checksum")
    chk(tckn_valid(PLANTED["ykn"]) and PLANTED["ykn"].startswith("99"), "T3 YKN starts with 99 and is valid")
    corp = [r[2] for r in P["oz"] if r[3] == "KURUMSAL"]
    chk(len(corp) == 5 and all(vkn_valid(v) for v in corp), "T2 5 KURUMSAL rows with valid 10-digit VKN")
    chk(all(tckn_valid(r[2]) for r in P["oz"] if r[3] == "BIREYSEL"), "all BIREYSEL kimlik_no valid")
    chk(sum(1 for r in P["oz"] if r[4].startswith("29.02")) == 2 and any(r[2] == "29.02.2024" for r in P["dk"]),
        "T1 leap-day dates present")
    return ok, msgs


# ----------------------------------------------------------------------------------------------
# generation grading
# ----------------------------------------------------------------------------------------------
def grade_generation(udir):
    res = {}
    files = {}
    notes = []
    for name, cols in (("musteriler.csv", MUS), ("hesaplar.csv", HES), ("islemler.csv", ISL)):
        p = os.path.join(udir, name)
        if os.path.isfile(p):
            files[name] = load_table(p)
        else:
            notes.append("eksik dosya: " + name)
    if len(files) < 3:
        for k, m in (("G1", 2), ("G2", 2), ("G3", 2), ("G4", 3), ("G5", 1), ("K9", 3), ("K10", 2)):
            res[k] = pts(0, m, "üretim dosyaları eksik: " + "; ".join(notes))
        return res
    mus = as_dicts(files["musteriler.csv"], MUS)
    hes = as_dicts(files["hesaplar.csv"], HES)
    isl = as_dicts(files["islemler.csv"], ISL)
    mus_by = {}
    for m in mus:
        mus_by.setdefault(m["musteri_no"], m)
    hes_by = {}
    for h in hes:
        hes_by.setdefault(h["hesap_no"], h)

    # --- G1 structure & counts
    sub = {}
    sub["headers"] = (files["musteriler.csv"]["header"] == MUS and files["hesaplar.csv"]["header"] == HES
                      and files["islemler.csv"]["header"] == ISL)
    sub["200_musteri"] = len(mus) == 200
    nk = sum(1 for m in mus if m["musteri_tipi"] == "KURUMSAL")
    sub["kurumsal_20_30"] = bool(mus) and 0.20 <= nk / len(mus) <= 0.30
    sub["islem_ge_1000"] = len(isl) >= 1000
    cnt = {}
    for h in hes:
        cnt[h["musteri_no"]] = cnt.get(h["musteri_no"], 0) + 1
    sub["hesap_1_3"] = bool(mus) and all(1 <= cnt.get(m["musteri_no"], 0) <= 3 for m in mus)
    enum_bad = sum(1 for m in mus if m["musteri_tipi"] not in ("BIREYSEL", "KURUMSAL") or m["senaryo"] not in ("NORMAL", "SINIR"))
    enum_bad += sum(1 for h in hes if h["doviz"] not in ("TRY", "USD", "EUR") or h["durum"] not in ("AKTIF", "KAPALI", "BLOKELI")
                    or h["banka_kodu"] not in ("00991", "00992", "00993") or h["senaryo"] not in ("NORMAL", "SINIR"))
    enum_bad += sum(1 for t in isl if t["islem_tipi"] not in ("HAVALE", "EFT", "FAST", "KART", "IADE") or t["senaryo"] not in ("NORMAL", "SINIR"))
    sub["enum_degerleri"] = enum_bad == 0
    npass = sum(sub.values())
    res["G1"] = pts(2 if npass == 6 else (1 if npass >= 4 else 0), 2,
                    "musteri=%d (kurumsal=%d), hesap=%d, islem=%d; %s" % (len(mus), nk, len(hes), len(isl),
                    ", ".join("%s=%s" % (k, "ok" if v else "FAIL") for k, v in sub.items())))

    # --- G2 formats
    checked = 0
    bad = {}

    def v(cond, key):
        nonlocal checked
        checked += 1
        if not cond:
            bad[key] = bad.get(key, 0) + 1

    tr_names = 0
    ind = [m for m in mus if m["musteri_tipi"] == "BIREYSEL"]
    for m in mus:
        v(pdate(m["kayit_tarihi"]) is not None, "tarih_bicimi")
        v(re.match(r"^\+905\d{9}$", m["telefon"]) is not None, "telefon")
        v(m["il"] in ILLER_OK, "il")
        if m["musteri_tipi"] == "BIREYSEL":
            d = pdate(m["dogum_tarihi"])
            v(d is not None, "tarih_bicimi")
            if d:
                v(18 <= age_on(d, REF) <= 100, "yas_18_100")
            v(2 <= len(m["ad"]) <= 30 and 2 <= len(m["soyad"]) <= 30, "ad_soyad_uzunluk")
            if set(m["ad"] + m["soyad"]) & TR_CHARS:
                tr_names += 1
        elif m["musteri_tipi"] == "KURUMSAL":
            v(0 < len(m["unvan"]) <= 100, "unvan_uzunluk")
    for h in hes:
        v(pdate(h["acilis_tarihi"]) is not None, "tarih_bicimi")
        if h["kapanis_tarihi"]:
            v(pdate(h["kapanis_tarihi"]) is not None, "tarih_bicimi")
        v(amt(h["bakiye"]) is not None, "tutar_bicimi")
    for t in isl:
        v(pdate(t["islem_tarihi"]) is not None, "tarih_bicimi")
        v(amt(t["tutar"]) is not None, "tutar_bicimi")
        v(len(t["aciklama"]) <= 140, "aciklama_140")
    utf8 = all(f["utf8"] for f in files.values())
    tr_share = tr_names / len(ind) if ind else 0
    nbad = sum(bad.values())
    rate = nbad / checked if checked else 1
    g2 = 2 if (nbad == 0 and utf8 and tr_share >= 0.30) else (1 if rate <= 0.01 and tr_share >= 0.30 else 0)
    res["G2"] = pts(g2, 2, "hatalı hücre=%d/%d %s; utf8=%s; türkçe karakterli bireysel ad oranı=%.0f%%" %
                    (nbad, checked, bad or "", utf8, 100 * tr_share))

    # --- G3 referential integrity
    pk_dup = (len(mus) - len({m["musteri_no"] for m in mus}) + len(hes) - len({h["hesap_no"] for h in hes})
              + len(isl) - len({t["islem_no"] for t in isl}))
    pk_fmt = (sum(1 for m in mus if not re.match(r"^M\d{6}$", m["musteri_no"]))
              + sum(1 for h in hes if not re.match(r"^H\d{8}$", h["hesap_no"]))
              + sum(1 for t in isl if not re.match(r"^I\d{10}$", t["islem_no"])))
    fk_bad = sum(1 for h in hes if h["musteri_no"] not in mus_by) + sum(1 for t in isl if t["hesap_no"] not in hes_by)
    fk_rate = fk_bad / max(1, len(hes) + len(isl))
    g3 = 2 if (pk_dup == 0 and fk_bad == 0 and pk_fmt == 0) else (1 if pk_dup == 0 and fk_rate <= 0.01 else 0)
    res["G3"] = pts(g3, 2, "PK tekrar=%d, PK biçim hatası=%d, kırık FK=%d" % (pk_dup, pk_fmt, fk_bad))

    # --- G4 boundary rows
    def edge_m(m):
        d = pdate(m["dogum_tarihi"])
        return ((m["musteri_tipi"] == "BIREYSEL" and (len(m["ad"]) in (2, 30) or len(m["soyad"]) in (2, 30)))
                or (m["musteri_tipi"] == "KURUMSAL" and len(m["unvan"]) == 100)
                or m["dogum_tarihi"] in ("30.09.2008", "01.10.1925") or (d is not None and (d.month, d.day) == (2, 29))
                or m["kayit_tarihi"] in ("01.01.2015", "30.09.2026"))

    def edge_h(h):
        m = mus_by.get(h["musteri_no"], {})
        return (h["bakiye"] in ("0,00", "5000000,00") or (m and h["acilis_tarihi"] == m.get("kayit_tarihi"))
                or (h["durum"] == "KAPALI" and h["kapanis_tarihi"] and h["kapanis_tarihi"] == h["acilis_tarihi"]))

    def edge_t(t):
        h = hes_by.get(t["hesap_no"], {})
        a = t["tutar"].lstrip("-")
        return (a in ("0,01", "1000000,00") or (t["islem_tipi"] == "FAST" and t["tutar"] == "100000,00")
                or (h and t["islem_tarihi"] == h.get("acilis_tarihi"))
                or (h and h.get("durum") == "KAPALI" and t["islem_tarihi"] == h.get("kapanis_tarihi"))
                or t["islem_tarihi"] == "30.09.2026" or len(t["aciklama"]) == 140)

    g4 = 0
    det = []
    for name, rows, fn in (("musteriler", mus, edge_m), ("hesaplar", hes, edge_h), ("islemler", isl, edge_t)):
        lab = [r for r in rows if r["senaryo"] == "SINIR"]
        ver = [r for r in lab if fn(r)]
        share = len(ver) / len(rows) if rows else 0
        ok = share >= 0.15
        g4 += 1 if ok else 0
        det.append("%s: SINIR etiketli=%d, doğrulanan=%d (%.1f%%)%s" % (name, len(lab), len(ver), 100 * share,
                                                                       "" if ok else " <15%"))
    res["G4"] = pts(g4, 3, "; ".join(det))

    # --- G5 e-mail domains
    bad_mail = [m["eposta"] for m in mus if not re.match(r"^[a-z0-9._%+\-]+@example\.com$", m["eposta"])]
    dup_mail = len(mus) - len({m["eposta"] for m in mus})
    other = set()
    for f in files.values():
        for tok in EMAIL_TOKEN_RE.findall(f["text"]):
            if not tok.lower().endswith("@example.com"):
                other.add(tok)
    g5 = 1 if not bad_mail and dup_mail == 0 and not other else 0
    res["G5"] = pts(g5, 1, "geçersiz/başka alan adı=%d, tekrar=%d, dosyalarda başka alan adlı adres=%d %s" %
                    (len(bad_mail), dup_mail, len(other), sorted(other)[:3]))

    # --- K10 identifiers
    chk = 0
    okc = 0
    probs = {}

    def idc(cond, key):
        nonlocal chk, okc
        chk += 1
        if cond:
            okc += 1
        else:
            probs[key] = probs.get(key, 0) + 1

    for m in mus:
        if m["musteri_tipi"] == "BIREYSEL":
            idc(tckn_valid(m["tckn"]), "tckn_gecersiz")
            idc(m["vkn"] == "", "bireyselde_vkn_dolu")
        elif m["musteri_tipi"] == "KURUMSAL":
            idc(vkn_valid(m["vkn"]), "vkn_gecersiz")
            idc(m["tckn"] == "", "kurumsalda_tckn_dolu")
    for h in hes:
        idc(iban_valid(h["iban"]), "iban_gecersiz")
    for t in isl:
        if t["karsi_iban"]:
            idc(iban_valid(t["karsi_iban"]), "karsi_iban_gecersiz")
    for col, rows in (("tckn", mus), ("vkn", mus), ("iban", hes)):
        vals = [r[col] for r in rows if r[col]]
        dups = len(vals) - len(set(vals))
        idc(dups == 0, col + "_tekrar")
    rate = okc / chk if chk else 0
    res["K10"] = pts(2 if rate == 1 else (1 if rate >= 0.95 else 0), 2,
                     "geçerli=%d/%d (%.1f%%) %s" % (okc, chk, 100 * rate, probs or ""))

    # --- K9 business rules
    ga, gb, gc = {}, {}, {}

    def inc(g, k):
        g[k] = g.get(k, 0) + 1

    for m in mus:
        k = pdate(m["kayit_tarihi"])
        if k and not (dt.date(2015, 1, 1) <= k <= REF):
            inc(ga, "kayit_aralik_disi")
        d = pdate(m["dogum_tarihi"])
        if m["musteri_tipi"] == "BIREYSEL" and d and k and age_on(d, k) < 18:
            inc(ga, "kayitta_18_yas_alti")
    for h in hes:
        m = mus_by.get(h["musteri_no"])
        a = pdate(h["acilis_tarihi"])
        c = pdate(h["kapanis_tarihi"])
        k = pdate(m["kayit_tarihi"]) if m else None
        if a and a > REF:
            inc(ga, "acilis_gelecekte")
        if a and k and a < k:
            inc(ga, "acilis_kayittan_once")
        if c and a and c < a:
            inc(ga, "kapanis_acilistan_once")
        if c and c > REF:
            inc(ga, "kapanis_gelecekte")
        if (h["durum"] == "KAPALI") != bool(h["kapanis_tarihi"]):
            inc(gb, "kapanis_tarihi_durum_uyumsuz")
        b = amt(h["bakiye"])
        if h["durum"] == "KAPALI" and b is not None and b != 0:
            inc(gb, "kapali_hesap_bakiye_sifir_degil")
        if b is not None and not (0 <= b <= 5000000):
            inc(gb, "bakiye_aralik_disi")
        if h["iban"][4:9] != h["banka_kodu"]:
            inc(gb, "iban_banka_kodu_uyumsuz")
    for t in isl:
        h = hes_by.get(t["hesap_no"])
        d = pdate(t["islem_tarihi"])
        if h and d:
            a = pdate(h["acilis_tarihi"])
            c = pdate(h["kapanis_tarihi"])
            if a and d < a:
                inc(ga, "islem_acilistan_once")
            if h["durum"] == "KAPALI" and c and d > c:
                inc(ga, "kapali_hesapta_kapanis_sonrasi_islem")
        if d and d > REF:
            inc(ga, "islem_gelecekte")
        x = amt(t["tutar"])
        tip = t["islem_tipi"]
        if x is not None:
            if tip == "IADE" and not (-1000000 <= x <= -0.01):
                inc(gc, "iade_tutar_isareti_araligi")
            if tip != "IADE" and not (0.01 <= x <= 1000000):
                inc(gc, "tutar_araligi")
            if tip == "FAST" and x > 100000:
                inc(gc, "fast_limit_asimi")
        if tip in ("HAVALE", "EFT", "FAST"):
            if not t["karsi_iban"]:
                inc(gc, "karsi_iban_eksik")
            elif h and t["karsi_iban"] == h["iban"]:
                inc(gc, "karsi_iban_kendi_iban")
        elif tip in ("KART", "IADE") and t["karsi_iban"]:
            inc(gc, "kart_iade_karsi_iban_dolu")
    k9 = (0 if ga else 1) + (0 if gb else 1) + (0 if gc else 1)
    res["K9"] = pts(k9, 3, "A-tarih zinciri: %s | B-hesap kuralları: %s | C-işlem kuralları: %s" %
                    (ga or "0 ihlal", gb or "0 ihlal", gc or "0 ihlal"))
    return res


# ----------------------------------------------------------------------------------------------
# masking grading
# ----------------------------------------------------------------------------------------------
def grade_masking(mdir, P):
    res = {}
    info = {}
    po, perr = find_file(mdir, "musteri_ozet.csv", ("ozet",))
    pd_, derr = find_file(mdir, "destek_kayitlari.csv", ("destek",))
    if not po or not pd_:
        for k, m in (("K1", 2), ("K2", 2), ("K3", 3), ("K4", 3), ("K5", 2), ("K6", 3), ("K7", 3), ("K8", 3),
                     ("M1", 3), ("M2", 2), ("M3", 2), ("M5", 2), ("M6", 2)):
            res[k] = pts(0, m, "maskeleme çıktısı eksik: %s %s" % (perr or "", derr or ""))
        return res, info
    O = load_table(po)
    D = load_table(pd_)
    info["dosya_notu"] = [x for x in (perr, derr) if x]
    info["encoding"] = {"musteri_ozet": O["enc"], "destek_kayitlari": D["enc"]}
    oz, dk = P["oz"], P["dk"]

    def col(tab, cols, name):
        h = tab["header"]
        return h.index(name) if name in h else cols.index(name)

    def cell(tab, cols, i, name):
        rows = tab["rows"]
        j = col(tab, cols, name)
        if i < len(rows) and j < len(rows[i]):
            return rows[i][j]
        return ""

    Orows, Drows = O["rows"], D["rows"]
    dk_all = [c for r in Drows for c in r]
    oz_all = [c for r in Orows for c in r]
    dk_digits = [digits(c) for c in dk_all]
    dk_low = [c.lower() for c in dk_all]

    def in_dk_digits(val):
        return any(val in d for d in dk_digits)

    # --- K1 phones in notes
    left = [k for k, (_, nat) in PLANTED["phones_notes"].items() if in_dk_digits(nat)]
    n = len(PLANTED["phones_notes"])
    rem = n - len(left)
    res["K1"] = pts(2 if rem == n else (1 if rem >= 4 else 0), 2, "temizlenen telefon=%d/%d, kalan=%s" % (rem, n, left))

    # --- K2 e-mails in notes
    left = []
    for k, e in PLANTED["emails_notes"].items():
        local = e.split("@")[0].lower()
        if any(e.lower() in c or local in c for c in dk_low):
            left.append(k)
    n = len(PLANTED["emails_notes"])
    rem = n - len(left)
    res["K2"] = pts(2 if rem == n else (1 if rem >= 3 else 0), 2, "temizlenen e-posta=%d/%d, kalan=%s" % (rem, n, left))

    # --- K3 TCKN in notes
    left = [k for k, t in PLANTED["tckn_notes"].items() if in_dk_digits(t)]
    res["K3"] = pts(3 - len(left), 3, "temizlenen TCKN=%d/3, kalan=%s" % (3 - len(left), left))

    # --- K4 legacy TCKN in eski_musteri_kodu
    j = col(O, OZ_COLS, "eski_musteri_kodu")
    eski_cells = [digits(r[j]) if j < len(r) else "" for r in Orows]
    leg_vals = [oz[r - 1][10] for r in PLANTED["legacy_tckn_rows"]]
    left = [x for x in leg_vals if any(x in c for c in eski_cells)]
    anywhere = [x for x in leg_vals if any(x in digits(c) for c in oz_all + dk_all)]
    k4 = 3 if not left else (1 if len(left) <= 3 else 0)
    res["K4"] = pts(k4, 3, "eski_musteri_kodu içinde kalan TCKN=%d/%d (çıktının herhangi bir yerinde=%d)" %
                    (len(left), len(leg_vals), len(anywhere)))

    # --- K5 IBAN in aciklama
    left = []
    for k, ib in PLANTED["ibans_aciklama"].items():
        dg = digits(ib)
        if in_dk_digits(dg) or in_dk_digits(dg[-16:]):
            left.append(k)
    rem = 3 - len(left)
    res["K5"] = pts(2 if rem == 3 else (1 if rem == 2 else 0), 2, "temizlenen IBAN=%d/3, kalan=%s" % (rem, left))

    # --- K6 quasi-identifier (dogum_tarihi + posta_kodu)
    ind_rows = [i for i, r in enumerate(oz) if r[3] == "BIREYSEL"]
    kept_pair = kept_dob = pk_changed = band_ok = 0
    coarse = 0
    dms = {}
    out_pairs = {}
    for i in ind_rows:
        od, opk = oz[i][4], oz[i][7]
        md, mpk = cell(O, OZ_COLS, i, "dogum_tarihi").strip(), cell(O, OZ_COLS, i, "posta_kodu").strip()
        out_pairs[(md, mpk)] = out_pairs.get((md, mpk), 0) + 1
        if md == od and mpk == opk:
            kept_pair += 1
        if md == od:
            kept_dob += 1
        if mpk != opk:
            pk_changed += 1
        o_age = age_on(pdate(od), REF)
        d = pdate(md)
        m_age = None
        if d:
            m_age = age_on(d, REF)
            dms[md[:5]] = dms.get(md[:5], 0) + 1
        else:
            coarse += 1
            y = re.search(r"(19|20)\d{2}", md)
            band = re.search(r"(\d{2})\s*[-–]\s*(\d{2})", md)
            if y:
                m_age = REF.year - int(y.group(0))
            elif band:
                m_age = int(band.group(1))
        if m_age is not None and (m_age // 10 == o_age // 10 or abs(m_age - o_age) <= 1):
            band_ok += 1
    n = len(ind_rows)
    top_dm = max(dms.values()) if dms else 0
    dob_generalised = (coarse + top_dm) >= 0.9 * n
    pk_generalised = pk_changed >= 0.9 * n
    utility = band_ok >= 0.9 * n
    if kept_pair > 0:
        k6 = 0
    elif not utility:
        k6 = 1
    elif dob_generalised or (kept_dob == 0 and pk_generalised):
        k6 = 3
    elif kept_dob == 0:
        k6 = 2
    else:
        k6 = 1.5
    kmin = min(out_pairs.values()) if out_pairs else 0
    res["K6"] = pts(k6, 3, "aynen kalan (doğum,posta) çifti=%d/%d, aynen kalan doğum tarihi=%d, değişen posta kodu=%d, "
                    "doğum genelleştirilmiş=%s, yaş dilimi korunan=%d/%d, çıktıda min k=%d" %
                    (kept_pair, n, kept_dob, pk_changed, dob_generalised, band_ok, n, kmin))

    # --- K7 file format: encoding + quoted fields
    moj = sum(O["text"].count(m) + D["text"].count(m) for m in MOJIBAKE)
    # text correctness is checked on records matched by kayit_no, so CSV mis-parsing (K7b) is not double-counted here
    jk = col(D, DK_COLS, "kayit_no")
    by_kayit = {r[jk]: r for r in Drows if jk < len(r)}
    txt_ok = 0
    for r in dk:
        o = by_kayit.get(r[0])
        if o and all(col(D, DK_COLS, c) < len(o) and o[col(D, DK_COLS, c)] == r[DK_COLS.index(c)]
                     for c in ("kanal", "konu", "durum")):
            txt_ok += 1
    a_ok = moj == 0 and txt_ok >= 0.9 * len(dk)
    k7a = (1.5 if (O["utf8"] and D["utf8"]) else 1.0) if a_ok else 0
    drec = [r for r in Drows if any(x.strip() for x in r)]
    b_ok = len(drec) == len(dk) and all(len(r) == len(D["header"]) for r in drec)
    aligned = sum(1 for i, r in enumerate(dk) if all(cell(D, DK_COLS, i, c) == r[DK_COLS.index(c)]
                                                     for c in ("kayit_no", "tarih", "islem_tutari")))
    bdet = []
    for rn in PLANTED["special_csv_rows"]:
        i = rn - 1
        good = all(cell(D, DK_COLS, j, c) == dk[j][DK_COLS.index(c)]
                   for j in (i, i + 1) if j < len(dk) for c in ("kayit_no", "tarih", "islem_tutari"))
        bdet.append(good)
    b_ok = b_ok and all(bdet) and aligned == len(dk)
    k7b = 1.5 if b_ok else 0
    res["K7"] = pts(k7a + k7b, 3, "çıktı kodlaması=%s/%s, bozuk karakter=%d, kanal/konu/durum birebir=%d/%d; "
                    "kayıt sayısı=%d, sütunları hizalı kayıt=%d/%d, özel CSV kayıtları (+sonraki) sağlam=%s" %
                    (O["enc"], D["enc"], moj, txt_ok, len(dk), len(drec), aligned, len(dk), bdet))

    # --- join (M5 clean rows, K8 dirty rows)
    oz_idx = {r[0]: i for i, r in enumerate(oz)}
    out_keys = [cell(O, OZ_COLS, i, "musteri_no").strip().upper() for i in range(len(oz))]
    uniq = len(set(out_keys)) == len(out_keys) and all(out_keys)
    orig_keys_left = sum(1 for r in oz if r[0] in set(out_keys))
    pseudo = orig_keys_left == 0

    def join_ok(i):
        j = oz_idx.get(dk[i][1].strip().upper())
        if j is None:
            return False
        return cell(D, DK_COLS, i, "musteri_no").strip().upper() == out_keys[j]

    clean = [i for i in range(len(dk)) if (i + 1) not in PLANTED["dirty_key_rows"]]
    cj = sum(1 for i in clean if join_ok(i))
    frac = cj / len(clean)
    res["M5"] = pts(2 if (frac == 1 and uniq) else (1 if frac >= 0.9 else 0), 2,
                    "temiz satırlarda doğru birleşme=%d/%d, maskeli anahtarlar benzersiz=%s" % (cj, len(clean), uniq))
    dj = [join_ok(r - 1) for r in PLANTED["dirty_key_rows"]]
    if not pseudo:
        k8 = 0
    else:
        k8 = 3 if all(dj) else (1 if any(dj) else 0)
    res["K8"] = pts(k8, 3, "kirli anahtarlı satırlarda doğru birleşme=%s, özgün anahtar kalan=%d/%d" %
                    (dj, orig_keys_left, len(oz)))

    # --- M1 direct columns
    tot = okm = 0
    miss = {}
    for i, r in enumerate(oz):
        tot += 1
        if r[0].upper() not in cell(O, OZ_COLS, i, "musteri_no").upper():
            okm += 1
        else:
            miss["musteri_no"] = miss.get("musteri_no", 0) + 1
        if r[3] != "BIREYSEL":
            continue
        name_c = cell(O, OZ_COLS, i, "ad_soyad")
        checks = {
            "ad_soyad": not name_in(r[1], name_c),
            "kimlik_no": r[2] not in digits(cell(O, OZ_COLS, i, "kimlik_no")),
            "cep_telefonu": digits(r[8])[2:] not in digits(cell(O, OZ_COLS, i, "cep_telefonu")),
            "eposta": (r[9].lower() not in cell(O, OZ_COLS, i, "eposta").lower()
                       and r[9].split("@")[0].lower() not in cell(O, OZ_COLS, i, "eposta").lower()),
        }
        for k, good in checks.items():
            tot += 1
            if good:
                okm += 1
            else:
                miss[k] = miss.get(k, 0) + 1
    f = okm / tot
    res["M1"] = pts(3 if f == 1 else (2 if f >= 0.95 else (1 if f >= 0.8 else 0)), 3,
                    "maskelenen doğrudan alan=%d/%d, kalan=%s" % (okm, tot, miss or "yok"))

    # --- M2 format preservation
    tot = okf = 0
    fb = {}
    for i, r in enumerate(oz):
        kim = cell(O, OZ_COLS, i, "kimlik_no").strip()
        tel = cell(O, OZ_COLS, i, "cep_telefonu").strip()
        checks = {"telefon": re.match(r"^\+90 5\d{2} \d{3} \d{2} \d{2}$", tel) is not None}
        if r[3] == "BIREYSEL":
            checks["tckn"] = tckn_valid(kim)
            checks["eposta"] = re.match(r"^[^@\s;]+@example\.com$", cell(O, OZ_COLS, i, "eposta").strip()) is not None
        else:
            checks["vkn"] = vkn_valid(kim)
        for k, good in checks.items():
            tot += 1
            if good:
                okf += 1
            else:
                fb[k] = fb.get(k, 0) + 1
    f = okf / tot
    res["M2"] = pts(2 if f >= 0.98 else (1 if f >= 0.8 else 0), 2, "biçimi geçerli=%d/%d, hatalı=%s" % (okf, tot, fb or "yok"))

    # --- M3 utility: structure + preserved columns + meaningful free text
    same_struct = (O["header"] == OZ_COLS and D["header"] == DK_COLS and len(Orows) == len(oz)
                   and len([r for r in Drows if any(x.strip() for x in r)]) == len(dk))
    diff = {}
    for i, r in enumerate(oz):
        for c in ("musteri_tipi", "cinsiyet", "il", "segment"):
            if cell(O, OZ_COLS, i, c) != r[OZ_COLS.index(c)]:
                diff[c] = diff.get(c, 0) + 1
    for i, r in enumerate(dk):
        for c in ("kayit_no", "tarih", "islem_tutari"):
            if cell(D, DK_COLS, i, c) != r[DK_COLS.index(c)]:
                diff[c] = diff.get(c, 0) + 1
    m3a = 1 if (same_struct and not diff) else 0
    name_tokens = set()
    for r in oz:
        if r[3] == "BIREYSEL":
            name_tokens |= set(fold(r[1]).split())
    for nm in PLANTED["third_party_names"]:
        name_tokens |= set(fold(nm).split())
    shares = []
    emptied = 0
    for i, r in enumerate(dk):
        for c in ("aciklama", "temsilci_notu"):
            o = r[DK_COLS.index(c)]
            m = cell(D, DK_COLS, i, c)
            if o.strip() and not m.strip():
                emptied += 1
            toks = [t for t in re.findall(r"[a-zçğıöşüâîû]{4,}", fold(o)) if t not in name_tokens and "@" not in t]
            toks = [t for t in toks if not any(t in fold(e) for e in PLANTED["emails_notes"].values())]
            if toks:
                fm = fold(m)
                shares.append(sum(1 for t in toks if t in fm) / len(toks))
    avg = sum(shares) / len(shares) if shares else 0
    m3b = 1 if (avg >= 0.6 and emptied == 0) else 0
    res["M3"] = pts(m3a + m3b, 2, "yapı aynı=%s, değişen korunacak hücre=%s; serbest metin kelime koruma=%.0f%%, "
                    "boşaltılan hücre=%d" % (same_struct, diff or "yok", 100 * avg, emptied))

    # --- M6 names in free text
    left = []
    for nm in PLANTED["third_party_names"]:
        sur = nm.split()[-1]
        if any(name_in(nm, c) or (len(sur) >= 5 and word_in(sur, c)) for c in dk_all):
            left.append(nm)
    for i, r in enumerate(dk):
        for o in oz:
            if o[3] == "BIREYSEL" and o[1] in r[6]:
                m = cell(D, DK_COLS, i, "temsilci_notu")
                sur = o[1].split()[-1]
                if name_in(o[1], m) or (len(sur) >= 5 and word_in(sur, m)):
                    left.append(o[1])
    n_planted = len(PLANTED["third_party_names"]) + sum(
        1 for r in dk for o in oz if o[3] == "BIREYSEL" and o[1] in r[6])
    res["M6"] = pts(2 if not left else (1 if len(left) <= 3 else 0), 2,
                    "serbest metinde kalan kişi adı=%d/%d %s" % (len(left), n_planted, left))

    # --- residual PII anywhere (informational)
    allc = oz_all + dk_all
    alld = [digits(c) for c in allc]
    resid = {}

    def count(label, vals, test):
        k = sum(1 for x in set(vals) if test(x))
        resid[label] = "%d/%d" % (k, len(set(vals)))

    ind = [r for r in oz if r[3] == "BIREYSEL"]
    count("tckn_ykn", [r[2] for r in ind] + [PLANTED["tckn_notes"]["C2"], PLANTED["tckn_notes"]["C3"]],
          lambda x: any(x in d for d in alld))
    count("telefon", [digits(r[8])[2:] for r in ind] + [v[1] for v in PLANTED["phones_notes"].values()],
          lambda x: any(x in d for d in alld))
    count("eposta", [r[9] for r in ind] + list(PLANTED["emails_notes"].values()),
          lambda x: any(x.lower().split("@")[0] in c.lower() for c in allc))
    count("iban", list(PLANTED["ibans_aciklama"].values()), lambda x: any(digits(x)[-16:] in d for d in alld))
    count("musteri_no", [r[0] for r in oz], lambda x: any(x.upper() in c.upper() for c in allc))
    count("ad_soyad", [r[1] for r in ind] + PLANTED["third_party_names"], lambda x: any(name_in(x, c) for c in allc))
    count("dogum+posta_ciftleri", ["%s|%s" % (r[4], r[7]) for r in ind],
          lambda x: any(cell(O, OZ_COLS, i, "dogum_tarihi") + "|" + cell(O, OZ_COLS, i, "posta_kodu") == x
                        for i in range(len(Orows))))
    count("kurumsal_vkn(bilgi)", [r[2] for r in oz if r[3] == "KURUMSAL"], lambda x: any(x in d for d in alld))
    info["kalan_kisisel_veri"] = resid
    info["kalan_toplam"] = sum(int(v.split("/")[0]) for k, v in resid.items() if "bilgi" not in k)
    return res, info


# ----------------------------------------------------------------------------------------------
# determinism
# ----------------------------------------------------------------------------------------------
def compare(a_dir, b_dir, names):
    out = {}
    for n in names:
        pa, pb = os.path.join(a_dir, n), os.path.join(b_dir, n)
        if not (os.path.isfile(pa) and os.path.isfile(pb)):
            out[n] = "eksik"
            continue
        ra, rb = open(pa, "rb").read(), open(pb, "rb").read()
        if ra == rb:
            out[n] = "birebir"
        else:
            ta, tb = parse_csv(read_text(pa)[0]), parse_csv(read_text(pb)[0])
            if ta == tb:
                out[n] = "içerik aynı (bayt farkı)"
            else:
                nd = sum(1 for x, y in zip(ta, tb) if x != y) + abs(len(ta) - len(tb))
                out[n] = "FARKLI (%d satır)" % nd
    ok = all(v in ("birebir", "içerik aynı (bayt farkı)") for v in out.values())
    return ok, out


def run_script(teslim, base, args, timeout=300):
    for ext, cmd in ((".py", [sys.executable]), (".js", ["node"])):
        p = os.path.join(teslim, base + ext)
        if os.path.isfile(p):
            env = dict(os.environ)
            env.pop("MASKELEME_ANAHTARI", None)
            try:
                r = subprocess.run(cmd + [p] + args, cwd=teslim, env=env, capture_output=True, timeout=timeout)
                return r.returncode == 0, "%s%s rc=%d %s" % (base, ext, r.returncode,
                                                            r.stderr.decode("utf-8", "replace")[-300:])
            except Exception as e:  # noqa
                return False, "%s%s çalıştırılamadı: %s" % (base, ext, e)
    return False, "%s.py/.js bulunamadı" % base


# ----------------------------------------------------------------------------------------------
# trap helper (manual review)
# ----------------------------------------------------------------------------------------------
TRAP_TOKENS = {
    "T1": ["29.02", "29 şubat", "artık yıl", "leap"],
    "T2": ["vkn", "10 hane", "10 haneli", "on hane"],
    "T3": ["99", "ykn", "yabancı"],
    "T4": ["20240227114", "71004583216", "0850", "kargo", "dekont", "destek@yelkovan"],
}
NEG = ["geçersiz", "hatalı", "invalid", "bozuk", "yanlış", "tutarsız", "sorun", "hata", "anomali", "şüpheli",
       "uyumsuz", "kişisel veri", "pii", "tckn"]


def trap_scan(teslim):
    p = os.path.join(teslim, "RAPOR.md")
    if not os.path.isfile(p):
        return {"_": ["RAPOR.md yok"]}
    lines = read_text(p)[0].splitlines()
    out = {}
    for t, toks in TRAP_TOKENS.items():
        for ln in lines:
            fl = fold(ln)
            if any(tok in fl for tok in toks) and any(n in fl for n in NEG):
                out.setdefault(t, []).append(ln.strip()[:220])
    return out


# ----------------------------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--teslim")
    ap.add_argument("--girdi", default=DEFAULT_GIRDI)
    ap.add_argument("--rerun", action="store_true")
    ap.add_argument("--run2")
    ap.add_argument("--fp", type=int, default=0)
    ap.add_argument("--json")
    ap.add_argument("--check-inputs", action="store_true")
    a = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa
        pass

    if a.check_inputs:
        ok, msgs = check_inputs(a.girdi)
        print("\n".join(msgs))
        print("\nINPUT CHECK:", "PASS" if ok else "FAIL")
        sys.exit(0 if ok else 1)
    if not a.teslim:
        ap.error("--teslim gerekli")

    P = load_pristine(a.girdi)
    teslim = os.path.abspath(a.teslim)
    gen = grade_generation(os.path.join(teslim, "uretim"))
    mask, info = grade_masking(os.path.join(teslim, "maskeleme"), P)

    det_m = det_g = None
    det_note = []
    tmp = None
    if a.rerun:
        tmp = tempfile.mkdtemp(prefix="tdgrade_")
        inp = os.path.join(tmp, "girdi_kopya")
        shutil.copytree(os.path.join(a.girdi, "canli_kesit"), inp)
        okr, msg = run_script(teslim, "maskele", [inp, os.path.join(tmp, "maskeleme")])
        det_note.append(msg)
        if okr:
            det_m = compare(os.path.join(teslim, "maskeleme"), os.path.join(tmp, "maskeleme"),
                            ["musteri_ozet.csv", "destek_kayitlari.csv"])
        okr, msg = run_script(teslim, "uret", [os.path.join(tmp, "uretim")])
        det_note.append(msg)
        if okr:
            det_g = compare(os.path.join(teslim, "uretim"), os.path.join(tmp, "uretim"),
                            ["musteriler.csv", "hesaplar.csv", "islemler.csv"])
    elif a.run2:
        r2 = os.path.abspath(a.run2)
        m2 = os.path.join(r2, "maskeleme") if os.path.isdir(os.path.join(r2, "maskeleme")) else r2
        det_m = compare(os.path.join(teslim, "maskeleme"), m2, ["musteri_ozet.csv", "destek_kayitlari.csv"])
        if os.path.isdir(os.path.join(r2, "uretim")):
            det_g = compare(os.path.join(teslim, "uretim"), os.path.join(r2, "uretim"),
                            ["musteriler.csv", "hesaplar.csv", "islemler.csv"])
    if det_m is None:
        mask["M4"] = pts(0, 3, "değerlendirilmedi (--rerun ya da --run2 verin) " + " | ".join(det_note), "NOT_EVALUATED"
                         if not a.rerun else "RERUN_FAILED")
    else:
        mask["M4"] = pts(3 if det_m[0] else 0, 3, str(det_m[1]))
    if det_g is None:
        gen["G6"] = pts(0, 1, "değerlendirilmedi " + " | ".join(det_note), "NOT_EVALUATED" if not a.rerun else "RERUN_FAILED")
    else:
        gen["G6"] = pts(1 if det_g[0] else 0, 1, str(det_g[1]))
    if tmp:
        shutil.rmtree(tmp, ignore_errors=True)

    allr = {}
    allr.update(gen)
    allr.update(mask)
    korder = ["K%d" % i for i in range(1, 11)]
    oorder = ["G1", "G2", "G3", "G4", "G5", "G6", "M1", "M2", "M3", "M4", "M5", "M6"]
    ks = sum(allr[k]["score"] for k in korder)
    km = sum(allr[k]["max"] for k in korder)
    os_ = sum(allr[k]["score"] for k in oorder)
    om = sum(allr[k]["max"] for k in oorder)
    total = max(0.0, ks + os_ - 2 * a.fp)
    mx = km + om
    traps = trap_scan(teslim)

    names = {"K1": "Notlarda telefonlar", "K2": "Notlarda e-postalar", "K3": "Notlarda TCKN (3. kişi dahil)",
             "K4": "Yanıltıcı başlık: eski_musteri_kodu=TCKN", "K5": "Açıklamada IBAN",
             "K6": "Yarı-tanımlayıcı: doğum tarihi+posta kodu", "K7": "Dosya biçimi: cp1254 + tırnaklı alanlar",
             "K8": "Kirli join anahtarları", "K9": "Üretim: iş kuralları / tarih zinciri",
             "K10": "Üretim: TCKN/VKN/IBAN geçerliliği",
             "G1": "Üretim yapı ve sayılar", "G2": "Üretim biçimleri", "G3": "Referans bütünlüğü",
             "G4": "SINIR satır payı (>=%15, doğrulanmış)", "G5": "E-posta alan adı example.com",
             "G6": "Üretim determinizmi", "M1": "Doğrudan PII sütunları", "M2": "Maskeli değerlerin biçim geçerliliği",
             "M3": "Fayda: yapı/korunan alanlar/serbest metin", "M4": "Maskeleme determinizmi",
             "M5": "Temiz satırlarda join", "M6": "Serbest metinde kişi adları"}
    print("=" * 100)
    print("trial-testdata grader  |  teslim: %s" % teslim)
    print("=" * 100)
    for k in korder + oorder:
        r = allr[k]
        st = (" [" + r["status"] + "]") if r.get("status") else ""
        print("%-4s %-44s %4.1f/%-2d%s\n       %s" % (k, names[k], r["score"], r["max"], st, r["detail"]))
    print("-" * 100)
    print("Kalan kişisel veri (maskeli çıktının herhangi bir yerinde): %s  toplam=%s" %
          (info.get("kalan_kisisel_veri"), info.get("kalan_toplam")))
    if info.get("dosya_notu"):
        print("Dosya notu:", info["dosya_notu"])
    print("Tuzak adayları (RAPOR.md, elle kontrol edin; doğrulanan her FP için --fp ile -2):")
    if not traps:
        print("   (aday satır yok)")
    for t, ls in traps.items():
        for ln in ls[:6]:
            print("   %s: %s" % (t, ln))
    print("-" * 100)
    print("K puanı: %.1f/%d   Nesnel kontroller: %.1f/%d   FP cezası: -%d   TOPLAM: %.1f/%d (%.0f%%)" %
          (ks, km, os_, om, 2 * a.fp, total, mx, 100 * total / mx))
    if a.json:
        with open(a.json, "w", encoding="utf-8") as f:
            json.dump({"teslim": teslim, "items": allr, "k_score": ks, "k_max": km, "objective_score": os_,
                       "objective_max": om, "fp": a.fp, "total": total, "max": mx, "info": info,
                       "trap_candidates": traps}, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
