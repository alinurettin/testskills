#!/usr/bin/env python3
"""Grader helper for the hold-out trial `trial-mobile2` (mobile test plan review).

EVALUATOR-ONLY. Never give this file (or anything in evals/keys) to the agent.

Python 3 standard library only.

Sub-commands
------------
  verify                 Re-check every planted item (K1..K12) and trap (T1..T4)
                         against the trial inputs. Exit code 0 = all checks passed.
  grade <workspace>      Objective device-matrix score (M1-M4 of the rubric) for an
                         agent workspace, plus F1 and keyword *hints* for the manual
                         K/T grading. Add --json for machine-readable output.
  selftest               Runs the matrix grader on built-in sample matrices
                         (optimal, the team plan's own matrix, naive top-N, model
                         aggregation, over budget, name variants) and asserts results.

Examples
--------
  python mobile2_grade.py verify
  python mobile2_grade.py grade C:\\trials\\mobile2-run01
  python mobile2_grade.py grade C:\\trials\\mobile2-run01 --json
  python mobile2_grade.py selftest
"""
import argparse
import csv
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_TRIAL = os.path.normpath(os.path.join(HERE, "..", "trial-mobile2"))

MIN_OS = {"Android": 10, "iOS": 16}
BUDGET = {"Android": 11, "iOS": 9}
TARGET = 80.0
PCT_TOLERANCE = 1.0  # percentage points, for M4

UPLOAD_FP = "07:A5:55:FB:96:CD:6F:D7:E7:14:B9:C0:1C:EE:1F:C6:C9:73:5E:2D:52:E5:64:84:D1:B7:40:F5:6E:74:3E:6F"
APPSIGN_FP = "56:89:17:50:C5:96:CC:C8:0C:60:3C:19:4A:09:3A:99:EE:F8:B3:82:91:86:51:E3:BF:EA:7B:C1:D9:13:4A:D4"


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------
def read_text(path):
    with open(path, "r", encoding="utf-8-sig") as f:
        return f.read()


def load_usage(trial_dir):
    path = os.path.join(trial_dir, "girdiler", "cihaz_kullanim_2026-08.csv")
    rows = []
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            rows.append({
                "platform": r["platform"].strip(),
                "uretici": r["uretici"].strip(),
                "model": r["model"].strip(),
                "tip": r["cihaz_tipi"].strip(),
                "os": int(r["os_surumu"]),
                "users": int(r["aktif_kullanici_28g"]),
            })
    return rows


def supported(row):
    return row["tip"] == "telefon" and row["os"] >= MIN_OS[row["platform"]]


TR_MAP = str.maketrans({"ı": "i", "İ": "i", "ş": "s", "Ş": "s", "ğ": "g", "Ğ": "g",
                        "ü": "u", "Ü": "u", "ö": "o", "Ö": "o", "ç": "c", "Ç": "c"})


def norm_model(s):
    s = (s or "").translate(TR_MAP).lower()
    s = re.sub(r"\b(samsung|xiaomi|apple|huawei|oppo|google)\b", " ", s)
    s = re.sub(r"\b[45]g\b", " ", s)
    s = re.sub(r"(\d+)\s*\.?\s*(st|nd|rd|th)\b", r"\1", s)
    s = re.sub(r"\b(nesil|generation|gen)\b", " ", s)
    s = re.sub(r"[^a-z0-9]", "", s)
    aliases = {"iphonese2020": "iphonese2", "ipad9": "ipad9", "ipadair5": "ipadair5"}
    return aliases.get(s, s)


def norm_platform(s, model=""):
    t = (s or "").strip().lower()
    if "android" in t:
        return "Android"
    if "ios" in t or "iphone" in t or "ipados" in t or "apple" in t:
        return "iOS"
    m = (model or "").lower()
    if "iphone" in m or "ipad" in m:
        return "iOS"
    if m:
        return "Android"
    return None


def norm_os(s):
    m = re.search(r"\d+", s or "")
    return int(m.group(0)) if m else None


def platform_stats(usage):
    out = {}
    for p in ("Android", "iOS"):
        pr = [r for r in usage if r["platform"] == p]
        out[p] = {
            "all": sum(r["users"] for r in pr),
            "supported": sum(r["users"] for r in pr if supported(r)),
        }
    return out


# ----------------------------------------------------------------------------
# Matrix evaluation (objective part of the rubric)
# ----------------------------------------------------------------------------
def evaluate_matrix(entries, usage):
    """entries: list of dicts with keys platform, model, os_surumu (raw strings)."""
    stats = platform_stats(usage)
    index = {}
    for r in usage:
        index[(r["platform"], norm_model(r["model"]), r["os"])] = r
    res = {p: {"devices": 0, "covered_rows": [], "covered_users": 0, "unsupported": [],
               "unmatched": [], "duplicates": []} for p in ("Android", "iOS")}
    unknown_platform = []
    seen = set()
    for e in entries:
        p = norm_platform(e.get("platform", ""), e.get("model", ""))
        if p is None:
            unknown_platform.append(e)
            continue
        res[p]["devices"] += 1
        key = (p, norm_model(e.get("model", "")), norm_os(e.get("os_surumu", "")))
        row = index.get(key)
        label = f'{e.get("model", "").strip()} / {e.get("os_surumu", "").strip()}'
        if row is None:
            res[p]["unmatched"].append(label)
            continue
        if not supported(row):
            why = "tablet" if row["tip"] != "telefon" else f'OS {row["os"]} < min {MIN_OS[p]}'
            res[p]["unsupported"].append(f"{label} ({why})")
            continue
        if key in seen:
            res[p]["duplicates"].append(label)
            continue
        seen.add(key)
        res[p]["covered_rows"].append(f'{row["model"]} / {row["os"]} ({row["users"]})')
        res[p]["covered_users"] += row["users"]
    for p in ("Android", "iOS"):
        r = res[p]
        r["supported_total"] = stats[p]["supported"]
        r["coverage_pct"] = round(100.0 * r["covered_users"] / stats[p]["supported"], 2)
        r["within_budget"] = r["devices"] <= BUDGET[p]
        r["meets_target"] = r["coverage_pct"] >= TARGET
    # Scores
    m1 = 6 if (res["Android"]["meets_target"] and res["Android"]["within_budget"]) else 0
    m2 = 6 if (res["iOS"]["meets_target"] and res["iOS"]["within_budget"]) else 0
    has_unsup = any(res[p]["unsupported"] for p in res)
    has_unmatched = any(res[p]["unmatched"] for p in res) or bool(unknown_platform)
    m3 = 3.0 - (1.5 if has_unsup else 0) - (1.5 if has_unmatched else 0)
    return {"platforms": res, "unknown_platform": unknown_platform,
            "M1_android_cov": m1, "M2_ios_cov": m2, "M3_clean_rows": m3}


def read_matrix_csv(path):
    raw = read_text(path)
    sample = raw[:2048]
    delim = ";" if sample.count(";") > sample.count(",") else ","
    rdr = csv.reader(io.StringIO(raw), delimiter=delim)
    rows = [r for r in rdr if any(c.strip() for c in r)]
    if not rows:
        return [], False, "empty"
    header = [h.strip().lower().translate(TR_MAP) for h in rows[0]]
    exact_header = [h.strip() for h in rows[0]] == ["platform", "model", "os_surumu"]

    def find(*names):
        for n in names:
            if n in header:
                return header.index(n)
        return None
    ip = find("platform")
    im = find("model", "cihaz", "device")
    io_ = find("os_surumu", "os", "os_version", "os_surum", "surum")
    if im is None or io_ is None:
        return [], exact_header, f"unrecognised header: {rows[0]}"
    out = []
    for r in rows[1:]:
        r = r + [""] * (len(header) - len(r))
        out.append({"platform": r[ip] if ip is not None else "", "model": r[im], "os_surumu": r[io_]})
    return out, exact_header, None


PCT_RE = re.compile(r"(?:%\s*(\d{1,3}(?:[.,]\d+)?))|(?:(\d{1,3}(?:[.,]\d+)?)\s*%)")


def find_reported_pcts(md_text):
    """Return candidate coverage percentages per platform from lines mentioning the platform."""
    cands = {"Android": [], "iOS": []}
    for line in md_text.splitlines():
        low = line.lower()
        if not ("kapsa" in low or "coverage" in low or "matris" in low or "toplam" in low or "%" in low):
            continue
        vals = []
        for m in PCT_RE.finditer(line):
            v = m.group(1) or m.group(2)
            try:
                vals.append(float(v.replace(",", ".")))
            except ValueError:
                pass
        if not vals:
            continue
        if "android" in low:
            cands["Android"].extend(vals)
        if re.search(r"\bios\b", low):
            cands["iOS"].extend(vals)
    return cands


# ----------------------------------------------------------------------------
# Keyword hints for manual K/T grading (assistive only, never authoritative)
# ----------------------------------------------------------------------------
HINTS = {
    "K1 Android13 notif permission": [r"POST_NOTIFICATIONS", r"Android 13", r"TC-PUSH-04", r"bildirim izni"],
    "K2 upgrade from 4.0/4.1": [r"4\.1\s*(→|->|'den|ten|dan)", r"4\.0\s*(→|->|'dan|dan)", r"şema\s*[45]", r"iki sürüm"],
    "K3 Turkish text + largest font": [r"TC-A11Y-02", r"Türkçe.*(uzun|genişle|taş|kesil)", r"İngilizce.*(kısa|en uzun)", r"metin genişle"],
    "K4 biometric enrolment change": [r"(yeni|ek)\w* (parmak|yüz)", r"enrol", r"KeyPermanentlyInvalidated", r"biometryCurrentSet", r"biyometrik bilgileriniz değişti", r"InvalidatedByBiometricEnrollment"],
    "K5 location While-Using/Once/Precise": [r"Kullanırken", r"While Using", r"Bir Kez", r"Allow Once", r"Kesin Konum", r"Precise", r"ACCESS_BACKGROUND_LOCATION", r"Her Zaman İzin Ver", r"TC-LOC-01"],
    "K6 Android14 partial photos": [r"Android 14", r"READ_MEDIA_VISUAL_USER_SELECTED", r"kısmi", r"seçili fotoğraf", r"partial"],
    "K7 timezone/clock": [r"TC-APT-07", r"Berlin", r"TSİ", r"cihaz saati", r"saat dilimi"],
    "K8 unverified app link -> browser": [r"TC-DL-03", r"Birlikte aç", r"tarayıcı", r"disambiguation", r"pm (get|verify)-app-links"],
    "K9 process death mid-flush": [r"process death", r"süreç", r"öldür", r"\bkill\b", r"çift kayıt", r"mükerrer kayıt", r"duplicate", r"idempotency"],
    "K10 background limits": [r"TC-OFF-05", r"WorkManager", r"Doze", r"BGAppRefresh", r"Düşük Güç|Low Power", r"Arka Planda Yenile|Background App Refresh", r"standby", r"pil (tasarruf|optimiz)"],
    "K11 assetlinks app-signing fingerprint": [r"assetlinks", r"uygulama imzalama", r"app signing", r"56:89:17", r"07:A5:55", r"parmak izi"],
    "K12 plan matrix miscount": [r"86[,.]4", r"83[,.]6", r"66[,.]9", r"64[,.]4", r"Galaxy A10", r"Tab A8", r"iPad"],
    "T1 (trap) iOS photo permission": [r"NSPhotoLibrary", r"fotoğraf (kitaplığı|arşivi) izni", r"Limited", r"sınırlı erişim", r"PHPicker"],
    "T2 (trap) DST": [r"yaz saati", r"\bDST\b"],
    "T3 (trap) duplicate CSV rows": [r"mükerrer satır", r"tekrarlı satır", r"çift satır", r"duplicate row", r"veri (hatası|kalitesi)"],
    "T4 (trap) force-stop push": [r"TC-PUSH-05", r"Zorla durdur", r"force.?stop"],
}


def keyword_hints(md_text):
    lines = md_text.splitlines()
    out = {}
    for k, pats in HINTS.items():
        hits = []
        for i, line in enumerate(lines, 1):
            for p in pats:
                if re.search(p, line, re.IGNORECASE):
                    hits.append((i, line.strip()[:160]))
                    break
        out[k] = hits
    return out


# ----------------------------------------------------------------------------
# grade
# ----------------------------------------------------------------------------
def find_file(ws, name):
    p = os.path.join(ws, name)
    if os.path.isfile(p):
        return p
    for root, _dirs, files in os.walk(ws):
        if "girdiler" in root.split(os.sep):
            continue
        if name in files:
            return os.path.join(root, name)
    return None


def cmd_grade(args):
    ws = args.workspace
    usage = load_usage(args.trial)
    report = {"workspace": ws}
    mpath = find_file(ws, "cihaz_matrisi.csv")
    rpath = find_file(ws, "plan_inceleme.md")
    report["files"] = {"cihaz_matrisi.csv": mpath, "plan_inceleme.md": rpath}
    exact_header = False
    if mpath:
        entries, exact_header, err = read_matrix_csv(mpath)
        if err:
            report["matrix_error"] = err
            entries = []
    else:
        entries = []
    ev = evaluate_matrix(entries, usage)
    report["matrix"] = ev
    md = read_text(rpath) if rpath else ""
    cands = find_reported_pcts(md) if md else {"Android": [], "iOS": []}
    m4 = 0.0
    m4_detail = {}
    for p in ("Android", "iOS"):
        actual = ev["platforms"][p]["coverage_pct"]
        ok = any(abs(v - actual) <= PCT_TOLERANCE for v in cands[p])
        m4_detail[p] = {"computed": actual, "candidates_in_report": cands[p][:20], "auto_match": ok}
        if ok and entries:
            m4 += 1.5
    report["M4_reported_pct_auto"] = m4
    report["M4_detail"] = m4_detail
    f1 = 0.0
    if mpath and entries and exact_header:
        f1 += 1.0
    elif mpath and entries:
        f1 += 0.5
    if rpath and md.strip():
        f1 += 1.0
    report["F1_files"] = f1
    report["hints"] = keyword_hints(md) if md else {}
    auto_total = ev["M1_android_cov"] + ev["M2_ios_cov"] + ev["M3_clean_rows"] + m4 + f1
    report["auto_subtotal"] = auto_total
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, default=str))
        return 0
    print(f"Workspace: {ws}")
    print(f"  cihaz_matrisi.csv: {mpath or 'MISSING'}  (exact header: {exact_header})")
    print(f"  plan_inceleme.md : {rpath or 'MISSING'}")
    if report.get("matrix_error"):
        print("  MATRIX ERROR:", report["matrix_error"])
    for p in ("Android", "iOS"):
        r = ev["platforms"][p]
        print(f"\n[{p}] devices={r['devices']} (budget {BUDGET[p]}, ok={r['within_budget']})  "
              f"coverage={r['covered_users']}/{r['supported_total']} = {r['coverage_pct']}%  "
              f"meets 80%: {r['meets_target']}")
        for x in r["covered_rows"]:
            print("    covered   :", x)
        for x in r["unsupported"]:
            print("    UNSUPPORTED:", x)
        for x in r["unmatched"]:
            print("    UNMATCHED :", x)
        for x in r["duplicates"]:
            print("    DUPLICATE :", x)
        d = m4_detail[p]
        print(f"    reported % candidates in plan_inceleme.md: {d['candidates_in_report'][:10]}  auto-match ±{PCT_TOLERANCE}pp: {d['auto_match']}")
    if ev["unknown_platform"]:
        print("  rows with unknown platform:", ev["unknown_platform"])
    print("\nObjective scores:")
    print(f"  M1 Android >=80% within budget : {ev['M1_android_cov']} / 6")
    print(f"  M2 iOS >=80% within budget     : {ev['M2_ios_cov']} / 6")
    print(f"  M3 no unsupported/unmatched    : {ev['M3_clean_rows']} / 3")
    print(f"  M4 reported % match (AUTO, grader must confirm): {m4} / 3")
    print(f"  F1 deliverable files           : {f1} / 2")
    print(f"  auto subtotal                  : {auto_total} / 20   (M5 /2 and F2 /2 are manual)")
    if report["hints"]:
        print("\nKeyword hints for manual K/T grading (line numbers in plan_inceleme.md; NOT scores):")
        for k, hits in report["hints"].items():
            lines = ", ".join(str(i) for i, _ in hits[:12])
            print(f"  {k:42s}: {len(hits):3d} line(s) {('[' + lines + ']') if hits else ''}")
    return 0


# ----------------------------------------------------------------------------
# verify (inputs reproduce every planted item and trap)
# ----------------------------------------------------------------------------
class Checker:
    def __init__(self):
        self.ok = 0
        self.fail = 0

    def check(self, label, cond, detail=""):
        if cond:
            self.ok += 1
            print(f"  PASS  {label}" + (f"  — {detail}" if detail else ""))
        else:
            self.fail += 1
            print(f"  FAIL  {label}" + (f"  — {detail}" if detail else ""))


def md_table_rows(text, start_marker, end_marker=None):
    i = text.find(start_marker)
    if i < 0:
        return []
    seg = text[i:]
    if end_marker:
        j = seg.find(end_marker, len(start_marker))
        if j > 0:
            seg = seg[:j]
    rows = []
    for line in seg.splitlines():
        if line.startswith("|") and not re.match(r"^\|\s*-", line):
            rows.append([c.strip() for c in line.strip().strip("|").split("|")])
    return rows


def tc_row(plan, tc_id):
    for line in plan.splitlines():
        if line.startswith(f"| {tc_id} |"):
            return line
    return ""


def section(text, start, end):
    i = text.find(start)
    j = text.find(end, i + 1) if i >= 0 else -1
    return text[i:j] if (i >= 0 and j > i) else (text[i:] if i >= 0 else "")


def cmd_verify(args):
    t = args.trial
    c = Checker()
    print(f"Trial folder: {t}\n")
    print("Inputs parse")
    brief = read_text(os.path.join(t, "girdiler", "urun_ozeti_v4.3.md"))
    plan = read_text(os.path.join(t, "girdiler", "test_plani_v4.3.md"))
    task = read_text(os.path.join(t, "TASK.md"))
    usage = load_usage(t)
    c.check("CSV parses, 44 rows, positive integer counts", len(usage) == 44 and all(r["users"] > 0 for r in usage), f"{len(usage)} rows")
    c.check("CSV platforms only Android/iOS, types only telefon/tablet",
            {r["platform"] for r in usage} == {"Android", "iOS"} and {r["tip"] for r in usage} == {"telefon", "tablet"})
    blocks = re.findall(r"```json\s*(.*?)```", brief, re.S)
    parsed = []
    for b in blocks:
        try:
            parsed.append(json.loads(b))
        except json.JSONDecodeError as e:
            parsed.append(e)
    c.check("brief JSON blocks (assetlinks, AASA) parse", len(parsed) == 2 and not any(isinstance(x, Exception) for x in parsed))
    c.check("TASK.md names deliverables and budget", "plan_inceleme.md" in task and "cihaz_matrisi.csv" in task
            and "en fazla 11" in task and "en fazla 9" in task and "platform,model,os_surumu" in task)
    c.check("Turkish characters present in inputs", all(ch in brief + plan for ch in "çğıİöşü"))
    leaked = [w for w in ("K1", "planted", "trap", "tuzak") if re.search(rf"\b{w}\b", task + brief + plan, re.I)]
    c.check("no grader vocabulary leaked into agent-visible files", not leaked, str(leaked))

    print("\nK1 Android 13+ notification runtime permission")
    c.check("brief: permission requested on iOS and Android 13+", "Bildirim izni (iOS ve Android 13+)" in brief)
    c.check("brief: targetSdk 36", "`targetSdk 36`" in brief)
    c.check("plan TC-PUSH-04 claims Android permission granted at install",
            "kurulumla birlikte verildiğinden" in tc_row(plan, "TC-PUSH-04"))
    c.check("plan TC-PUSH-01/02 are iOS-only", tc_row(plan, "TC-PUSH-01").rstrip().endswith("| iOS |")
            and tc_row(plan, "TC-PUSH-02").rstrip().endswith("| iOS |"))
    c.check("plan never mentions POST_NOTIFICATIONS", "POST_NOTIFICATIONS" not in plan)

    print("\nK2 upgrade from two versions back")
    c.check("brief: 4.1 = %17, 4.0 = %12", "| 4.1 | %17 |" in brief and "| 4.0 | %12 |" in brief)
    upg = sorted(set(re.findall(r"\| (TC-UPG-\d+) \|", plan)))
    c.check("plan has exactly one upgrade TC (4.2 → 4.3)", upg == ["TC-UPG-01"] and "4.2 → 4.3" in tc_row(plan, "TC-UPG-01"), str(upg))
    c.check("plan never tests 4.0/4.1 → 4.3", not re.search(r"4\.[01]\s*(→|->)", plan))

    print("\nK3 Turkish text expansion at largest font size")
    srows = [r for r in md_table_rows(brief, "| Anahtar | Türkçe | İngilizce |") if r[0].startswith("`")]
    tr = [len(r[1]) for r in srows]
    en = [len(r[2]) for r in srows]
    longer = sum(1 for a, b in zip(tr, en) if a > b)
    c.check("strings table parsed (12 rows)", len(srows) == 12, f"{len(srows)} rows")
    c.check("Turkish total length > English total", sum(tr) > sum(en), f"TR {sum(tr)} vs EN {sum(en)} chars = x{sum(tr)/sum(en):.2f}")
    c.check("longest UI string is Turkish", max(tr) > max(en), f"max TR {max(tr)} vs max EN {max(en)}")
    c.check("Turkish longer in most keys", longer >= 9, f"{longer}/12 keys longer in TR")
    c.check("plan says largest-font test runs in English because English is longest",
            "TC-A11Y-02 cihaz dili İngilizce" in plan and "en uzun arayüz metinleri İngilizce" in plan)

    print("\nK4 biometric enrolment change invalidates key")
    c.check("brief: setInvalidatedByBiometricEnrollment(true) and .biometryCurrentSet",
            "setInvalidatedByBiometricEnrollment(true)" in brief and ".biometryCurrentSet" in brief)
    bio = section(plan, "### 5.1", "### 5.2")
    c.check("plan 5.1 has no enrolment-change scenario",
            not re.search(r"yeni (parmak|yüz)|(parmak izi|yüz) ekle|değiş|kayıt sil|enrol", bio))

    print("\nK5 location: 'Always' not in first dialog; While-Using/Once; iOS precise")
    c.check("plan TC-LOC-01 picks 'Her Zaman İzin Ver' in the (first) dialog on iOS and Android",
            "izin diyaloğunda \"Her Zaman İzin Ver\" seç" in tc_row(plan, "TC-LOC-01") and tc_row(plan, "TC-LOC-01").rstrip().endswith("| iOS, Android |"))
    c.check("brief: foreground first, then background via system step", "önce ön plan (foreground) konum izni istenir" in brief)
    c.check("plan never tests 'Kullanırken' / 'Bir Kez' / 'only this time'", not re.search(r"Kullanırken|Bir Kez|While Using|Once", plan))
    c.check("plan approximate-location test is Android-12+-only", tc_row(plan, "TC-LOC-03").rstrip().endswith("| Android 12+ |"))
    c.check("plan has no iOS Precise Location test", "Kesin Konum" not in plan and "Precise" not in plan)
    c.check("brief requires precise + fallback on both platforms", "Kesin Konum\" açık" in brief and "Bu kural iOS ve Android için aynıdır" in brief)

    print("\nK6 Android 14 partial photo access")
    doc = section(plan, "### 5.4", "### 5.5")
    c.check("brief declares READ_MEDIA_VISUAL_USER_SELECTED and requires full/partial/denied handling",
            "READ_MEDIA_VISUAL_USER_SELECTED" in brief and "(tam, kısmi veya ret)" in brief)
    c.check("plan 5.4 covers only grant/deny for Android 13+", "Android 14" not in doc and "kısmi" not in doc
            and "VISUAL_USER_SELECTED" not in doc and "ver / reddet" in tc_row(plan, "TC-DOC-04"))

    print("\nK7 timezone / device clock")
    c.check("brief: always shown in Europe/Istanbul with 'TSİ', regardless of device tz",
            "her zaman kliniğin saat diliminde (Europe/Istanbul)" in brief)
    c.check("plan TC-APT-07 expects conversion to device tz (13:30)", "cihazın saat dilimine çevrilmiş" in tc_row(plan, "TC-APT-07"))
    c.check("brief: countdown/check-in window use server time even if device clock wrong", "sunucu saatine" in brief and "cihaz saati yanlış" in brief)
    c.check("plan has no wrong-device-clock test", not re.search(r"cihaz saati|saati (ileri|geri)|otomatik saat", plan, re.I))

    print("\nK8 unverified App Link on Android 12+")
    c.check("plan TC-DL-03 expects 'Birlikte aç' chooser", "\"Birlikte aç\" seçim penceresini" in tc_row(plan, "TC-DL-03"))
    c.check("brief: verification failure -> opens in browser with 'Uygulamada aç'",
            "alan adı doğrulaması başarısız → bağlantı tarayıcıda açılır" in brief and "\"Uygulamada aç\"" in brief)

    print("\nK9 process death during queue flush")
    off = section(plan, "### 5.6", "### 5.7")
    c.check("brief: key generated at creation, reused, delete only on 201/200",
            "oluşturulduğu anda istemci bir `idempotencyKey`" in brief and "`201 Created`" in brief and "`200 OK`" in brief)
    c.check("plan idempotency covered only at API level (TC-OFF-07, Postman)", tc_row(plan, "TC-OFF-07").rstrip().endswith("| API |"))
    c.check("plan 5.6 has no kill/process-death-mid-flush scenario",
            not re.search(r"öldür|sonlandır|process|süreç|çök|crash|kill|bellek", off, re.I))

    print("\nK10 background execution expectations")
    r5 = tc_row(plan, "TC-OFF-05")
    c.check("plan TC-OFF-05 expects WorkManager to run after force stop within 15 min",
            "zorla durdurma dâhil" in r5 and "en geç 15 dakika içinde" in r5)
    c.check("plan TC-OFF-05 expects iOS BGAppRefreshTask every 15 min", "15 dakikalık periyotlarla" in r5)
    c.check("brief: iOS BGAppRefreshTask scheduling is decided by the system", "zamanlamayı sistem belirler" in brief)
    c.check("plan TC-PUSH-05 itself acknowledges force-stopped apps get nothing (inconsistency)",
            "Zorla durdurulmuş uygulamaya push gelmemesi beklenen platform davranışıdır" in tc_row(plan, "TC-PUSH-05"))
    c.check("plan has no Doze / standby / battery saver / Low Power / BAR-off test",
            not re.search(r"Doze|[Ss]tandby|[Pp]il tasarruf|[Pp]il optimiz|[Bb]atarya|Düşük Güç|Low Power|Arka Planda Yenile", plan))

    print("\nK11 assetlinks.json lacks the Play app-signing fingerprint")
    al = parsed[0] if parsed and isinstance(parsed[0], list) else []
    fps = set()
    for st in al:
        fps.update(st.get("target", {}).get("sha256_cert_fingerprints", []))
    c.check("assetlinks lists only the upload key", fps == {UPLOAD_FP}, str(fps))
    c.check("Play app-signing key is missing from assetlinks", APPSIGN_FP not in fps)
    c.check("brief: Play installs are signed with the app-signing key", "Google Play'den indirilen tüm kurulumlar" in brief and APPSIGN_FP in brief)
    c.check("plan tests links only with QA builds signed by upload key; prod only smoke after release",
            "QA derlemesi, Firebase App Distribution üzerinden (yükleme anahtarıyla imzalı)" in plan
            and "Derin bağlantı testleri QA derlemeleriyle yapılır" in plan
            and "yayından sonra yalnızca duman testiyle" in plan)
    aasa = parsed[1] if len(parsed) > 1 and isinstance(parsed[1], dict) else {}
    c.check("AASA (iOS) is internally consistent (control: not a planted defect)",
            aasa.get("applinks", {}).get("details", [{}])[0].get("appIDs") == ["K7PQ2ZX9LM.com.poyrazklinik.app"])

    print("\nK12 plan device matrix miscounted")
    stats = platform_stats(usage)
    c.check("supported denominators match plan (Android 89.100, iOS 62.700)",
            stats["Android"]["supported"] == 89100 and stats["iOS"]["supported"] == 62700, str(stats))
    plan_mtx = {"Android": [], "iOS": []}
    for p, start, end in (("Android", "### 6.1 Android", "### 6.2 iOS"), ("iOS", "### 6.2 iOS", "Notlar:")):
        for r in md_table_rows(plan, start, end):
            if r and r[0].isdigit():
                plan_mtx[p].append({"platform": p, "model": r[1], "os_surumu": r[2], "claimed": int(r[3].replace(".", ""))})
    claimed = {p: sum(x["claimed"] for x in plan_mtx[p]) for p in plan_mtx}
    ev = evaluate_matrix(plan_mtx["Android"] + plan_mtx["iOS"], usage)
    a = ev["platforms"]["Android"]
    i = ev["platforms"]["iOS"]
    c.check("plan claims Android 77.000 (86.4%) and iOS 52.400 (83.6%)",
            claimed == {"Android": 77000, "iOS": 52400}, str(claimed))
    c.check("actual Android coverage by plan's own rule < 80%", a["coverage_pct"] < 80, f'{a["covered_users"]}/89100 = {a["coverage_pct"]}%  unsupported={a["unsupported"]}')
    c.check("actual iOS coverage by plan's own rule < 80%", i["coverage_pct"] < 80, f'{i["covered_users"]}/62700 = {i["coverage_pct"]}%  unsupported={i["unsupported"]}')
    c.check("Android: A54 credited 18.500 (=15+16 rows), A10 credited 8.300 (=Android 9 + 11 rows)",
            any(x["claimed"] == 18500 and x["model"].endswith("A54") for x in plan_mtx["Android"])
            and any(x["claimed"] == 8300 and x["model"].endswith("A10") for x in plan_mtx["Android"]))
    c.check("iOS: iPhone 13 credited 13.300 (=26+18), iPhone 11 9.900 (=26+18), iPhone 8 2.600 (=16+15)",
            [x["claimed"] for x in plan_mtx["iOS"] if x["model"] in ("iPhone 13", "iPhone 11", "iPhone 8")] == [13300, 9900, 2600])
    c.check("plan's own section 7 excludes tablets while matrix counts Tab A8 and iPad",
            "iPad ve Android tablet arayüz testleri" in plan and any("Tab A8" in u for u in a["unsupported"])
            and any("iPad" in u for u in i["unsupported"]))

    print("\nObjective matrix check feasibility")
    for p in ("Android", "iOS"):
        sup = sorted([r for r in usage if r["platform"] == p and supported(r)], key=lambda r: -r["users"])
        cum, need = 0, None
        for k, r in enumerate(sup, 1):
            cum += r["users"]
            if need is None and 100.0 * cum / stats[p]["supported"] >= TARGET:
                need = k
        c.check(f"{p}: minimum devices for >=80% ({need}) fits budget ({BUDGET[p]})", need is not None and need <= BUDGET[p])
    naive_a = sorted([r for r in usage if r["platform"] == "Android"], key=lambda r: -r["users"])[:BUDGET["Android"]]
    ev_n = evaluate_matrix([{"platform": r["platform"], "model": r["model"], "os_surumu": str(r["os"])} for r in naive_a], usage)
    c.check("naive Android top-11 by raw users (incl. unsupported) misses 80%", not ev_n["platforms"]["Android"]["meets_target"],
            f'{ev_n["platforms"]["Android"]["coverage_pct"]}%')

    print("\nTraps")
    c.check("T1 brief: iOS uses PHPicker, no NSPhotoLibraryUsageDescription; plan TC-DOC-05 expects no prompt",
            "Fotoğraf kitaplığı izni **istenmez**" in brief and "izin istemi çıkmaz" in tc_row(plan, "TC-DOC-05"))
    dst_note = "Türkiye 2016'dan beri kalıcı olarak UTC+3" in plan
    try:
        from zoneinfo import ZoneInfo
        from datetime import datetime
        tz = ZoneInfo("Europe/Istanbul")
        offs = {datetime(2026, m, 15, 12, tzinfo=tz).utcoffset().total_seconds() / 3600 for m in range(1, 13)}
        c.check("T2 Europe/Istanbul has a fixed UTC+3 offset all year (tz database)", offs == {3.0} and dst_note, str(offs))
    except Exception as e:  # tzdata missing on some Windows Pythons
        c.check("T2 plan DST exclusion note present (tz database unavailable here: %s; Turkey abolished DST in 2016)" % type(e).__name__, dst_note)
    from collections import Counter
    keys = Counter((r["platform"], r["model"], r["os"]) for r in usage)
    multi = Counter((r["platform"], r["model"]) for r in usage)
    multi_models = sorted(f"{m} ({p})" for (p, m), n in multi.items() if n > 1)
    c.check("T3 same model appears with 2 OS versions, but no exact duplicate rows",
            all(v == 1 for v in keys.values()) and len(multi_models) >= 6, ", ".join(multi_models))
    c.check("T4 plan TC-PUSH-05 treats no push after force stop as expected platform behaviour",
            "hata olarak raporlanmaz" in tc_row(plan, "TC-PUSH-05"))

    print(f"\nRESULT: {c.ok} passed, {c.fail} failed")
    return 0 if c.fail == 0 else 1


# ----------------------------------------------------------------------------
# selftest (grader logic on sample matrices)
# ----------------------------------------------------------------------------
def cmd_selftest(args):
    usage = load_usage(args.trial)
    ok = True

    def m(rows):
        return [{"platform": p, "model": mo, "os_surumu": o} for p, mo, o in rows]

    def expect(name, entries, a_pass, i_pass, m3=None):
        nonlocal ok
        ev = evaluate_matrix(entries, usage)
        a = ev["platforms"]["Android"]
        i = ev["platforms"]["iOS"]
        got = (ev["M1_android_cov"] == 6, ev["M2_ios_cov"] == 6)
        good = got == (a_pass, i_pass) and (m3 is None or ev["M3_clean_rows"] == m3)
        ok &= good
        print(f'  {"PASS" if good else "FAIL"}  {name}: Android {a["coverage_pct"]}% ({a["devices"]} dev), '
              f'iOS {i["coverage_pct"]}% ({i["devices"]} dev), M1={ev["M1_android_cov"]} M2={ev["M2_ios_cov"]} M3={ev["M3_clean_rows"]}')

    optimal = m([("Android", "Galaxy A54", "15"), ("Android", "Redmi Note 12", "14"), ("Android", "Galaxy A34", "15"),
                 ("Android", "Redmi Note 13", "14"), ("Android", "Galaxy A54", "16"), ("Android", "Galaxy A14", "14"),
                 ("Android", "Galaxy A13", "14"), ("Android", "Redmi Note 11", "13"), ("Android", "Galaxy A55", "16"),
                 ("Android", "Galaxy A12", "12"), ("Android", "P30 Lite", "10"),
                 ("iOS", "iPhone 13", "26"), ("iOS", "iPhone 15", "26"), ("iOS", "iPhone 14", "26"), ("iOS", "iPhone 11", "26"),
                 ("iOS", "iPhone 12", "26"), ("iOS", "iPhone 16", "26"), ("iOS", "iPhone 13", "18"), ("iOS", "iPhone 11", "18"),
                 ("iOS", "iPhone 8", "16")])
    expect("optimal greedy + min-OS devices", optimal, True, True, 3.0)

    variants = m([("android", "Samsung Galaxy A54 5G", "Android 15"), ("Android", "Xiaomi Redmi Note 12", "Android 14 (HyperOS)"),
                  ("Android", "SAMSUNG GALAXY A34", "15"), ("Android", "Redmi Note 13", "14"), ("Android", "Galaxy A54", "16.0"),
                  ("Android", "Galaxy A14", "14"), ("Android", "Galaxy A13", "14"), ("Android", "Redmi Note 11", "13"),
                  ("Android", "Galaxy A55", "16"), ("Android", "Galaxy A12", "12"),
                  ("iOS", "Apple iPhone 13", "iOS 26.0"), ("iOS", "iPhone 15", "26"), ("iOS", "iPhone 14", "26.1"),
                  ("iOS", "iPhone 11", "26"), ("iOS", "iPhone 12", "26"), ("iOS", "iPhone 16", "26"),
                  ("iOS", "iPhone 13", "18.6"), ("iOS", "iPhone XR", "18"), ("iOS", "iPhone SE 2nd gen", "26")])
    expect("name/version variants still match", variants, True, True, 3.0)

    plan = m([("Android", "Samsung Galaxy A54", "15"), ("Android", "Xiaomi Redmi Note 12", "14"), ("Android", "Samsung Galaxy A34", "15"),
              ("Android", "Xiaomi Redmi Note 13", "14"), ("Android", "Samsung Galaxy A14", "14"), ("Android", "Samsung Galaxy A13", "14"),
              ("Android", "Xiaomi Redmi Note 11", "13"), ("Android", "Samsung Galaxy A10", "11"), ("Android", "Samsung Galaxy Tab A8", "14"),
              ("iOS", "iPhone 13", "26"), ("iOS", "iPhone 15", "26"), ("iOS", "iPhone 14", "26"), ("iOS", "iPhone 11", "26"),
              ("iOS", "iPhone 12", "26"), ("iOS", "iPhone 8", "16"), ("iOS", "iPad (9. nesil)", "18")])
    expect("team plan's own matrix", plan, False, False, 1.5)

    aggregated = m([("Android", "Galaxy A54", "15"), ("Android", "Redmi Note 12", "14"), ("Android", "Galaxy A34", "15"),
                    ("Android", "Redmi Note 13", "14"), ("Android", "Galaxy A14", "14"), ("Android", "Galaxy A13", "14"),
                    ("Android", "Redmi Note 11", "13"), ("Android", "Galaxy A55", "16"), ("Android", "Galaxy A12", "12"),
                    ("iOS", "iPhone 13", "26"), ("iOS", "iPhone 15", "26"), ("iOS", "iPhone 14", "26"), ("iOS", "iPhone 11", "26"),
                    ("iOS", "iPhone 12", "26"), ("iOS", "iPhone 16", "26")])
    expect("one device per model (model-level aggregation)", aggregated, False, False, 3.0)

    naive = sorted(usage, key=lambda r: -r["users"])
    na = [r for r in naive if r["platform"] == "Android"][:11] + [r for r in naive if r["platform"] == "iOS"][:9]
    expect("naive top-N by raw users (budget-limited)", m([(r["platform"], r["model"], str(r["os"])) for r in na]), False, True, 1.5)

    over = optimal + m([("Android", "Galaxy S23", "16"), ("iOS", "iPhone XR", "18")])
    expect("over budget (12 Android / 10 iOS) gets no coverage points", over, False, False, 3.0)

    unmatched = m([("Android", "Galaxy Z Fold 5", "14")]) + optimal
    expect("unmatched model costs M3 (and budget)", unmatched, False, True, 1.5)

    print("\nSELFTEST", "OK" if ok else "FAILED")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--trial", default=DEFAULT_TRIAL, help="trial folder (default: ../trial-mobile2)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("verify")
    g = sub.add_parser("grade")
    g.add_argument("workspace")
    g.add_argument("--json", action="store_true")
    sub.add_parser("selftest")
    args = ap.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if args.cmd == "verify":
        return cmd_verify(args)
    if args.cmd == "grade":
        return cmd_grade(args)
    return cmd_selftest(args)


if __name__ == "__main__":
    sys.exit(main())
