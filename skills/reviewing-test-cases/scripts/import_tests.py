#!/usr/bin/env python3
"""Import an existing test suite from Excel (.xlsx) or CSV (Excel, TestRail, Xray, Zephyr, Qase exports)
into QA Suite compact format.

Excel is read directly with the standard library (no Excel, no openpyxl): shared and inline strings,
numbers, dates stored as serial numbers (-> 2026-03-01), multi-line cells, merged cells (a test ID or
title merged down over its step rows), blank rows and several sheets (--sheet). Legacy .xls and
password-protected workbooks cannot be read: save them as .xlsx or "CSV UTF-8" first.

The header row is found automatically (title rows above it are skipped, a two-row header is joined).
Columns are detected by header name (TR/EN aliases, case- and Turkish-letter-insensitive), in two layouts:
  - one row per test, steps/expected numbered inside cells ("1. … 2. …")
  - one row per step, rows of the same test sharing an ID (Xray/Zephyr style) or leaving ID and title
    empty (or merged) below the first step
Unknown values get safe defaults and are flagged so the review can fix them:
  priority  → mapped (Highest/Kritik→c, High/Yüksek→h, Medium/Normal/Orta→m, Low/Lowest/Düşük→l, else m)
  polarity  → from a polarity column (positive/pozitif/negative/negatif), else guessed from wording
              (reject/error/invalid/geçersiz/hata/red → negative)
  technique → from a technique column (full name, ep/bva/dt/…, or Turkish name), else rb
  status    → from a status column (ready/hazır, deprecated/iptal), else draft; tag "imported"
  requirement → from a requirement/coverage/labels column (REQ-### or Jira keys), else "UNLINKED"
IDs: when every source ID is a unique TC-###, the IDs are kept (never renumber). Otherwise tests get
TC-### from --start (default 1) and the original ID is kept in a tag ("src-<id>"); --renumber forces this.

Usage:
  python import_tests.py suite.xlsx --out qa/test-cases.src.md [--sheet "Test Case'ler" | --sheet 2 | --sheet all]
  python import_tests.py suite.csv --out qa/test-cases.src.md [--delimiter ";"] [--lang tr] [--start 1]
  python import_tests.py suite.xlsx --list-sheets
  python qa_compact.py tc qa/test-cases.src.md --out qa/test-cases.json --lenient
--map overrides detection with header names: id, title, pre, steps, data, tdata (test-level data),
expected, priority, polarity, technique, req, tags, status, auto; e.g. --map title=Summary,steps=Action
Exit codes: 0 ok, 2 unreadable input or no title/steps columns found.
"""
from __future__ import annotations

import argparse
import csv
import io
import posixpath
import re
import sys
import xml.etree.ElementTree as ET
import zipfile
from collections import OrderedDict
from datetime import datetime, timedelta
from pathlib import Path

ALIASES = {
    "id": ["id", "test id", "tcid", "tc id", "test case id", "testcase id", "key", "issue key", "case id", "no",
           "test no", "test kodu", "test case no", "senaryo no", "senaryo id", "test senaryo no"],
    "title": ["title", "summary", "name", "test case", "test case name", "test name", "test title", "başlık",
              "test adı", "test başlığı", "senaryo", "senaryo adı", "test senaryosu", "test senaryo adı",
              "test case adı", "test case başlığı", "ad"],
    "pre": ["precondition", "preconditions", "pre-condition", "pre-conditions", "ön koşul", "ön koşullar",
            "önkoşul", "önkoşullar", "ön şart", "ön şartlar"],
    # action-like names first: an export may carry both a "Step" (number) and an "Action" column
    "steps": ["steps", "test steps", "steps (step)", "adımlar", "test adımları", "action", "actions", "aksiyon",
              "eylem", "işlem", "yapılacak işlem", "step description", "adım açıklaması", "step", "adım",
              "test adımı", "test script (step-by-step) - step"],
    "data": ["data", "test data", "step data", "veri", "test verisi", "adım verisi", "girdi",
             "test script (step-by-step) - test data"],
    "expected": ["expected", "expected result", "expected results", "steps (expected result)", "beklenen",
                 "beklenen sonuç", "beklenen sonuçlar", "beklenen değer", "result",
                 "test script (step-by-step) - expected result"],
    "priority": ["priority", "öncelik", "severity", "önem", "önem derecesi"],
    "polarity": ["polarity", "polarite", "pozitif/negatif", "positive/negative"],
    "technique": ["technique", "teknik", "test technique", "test tekniği", "design technique", "tasarım tekniği"],
    "req": ["requirement", "requirements", "requirement keys", "requirement id", "requirement ids", "coverage",
            "references", "refs", "gereksinim", "gereksinimler", "gereksinim no", "gereksinim id", "story",
            "user story", "labels"],
    "tags": ["tags", "etiketler", "etiket", "component", "components", "section", "folder", "modül", "module"],
    "status": ["status", "durum"],
    "tdata": ["test data", "test verisi"],
    "auto": ["automation candidate", "otomasyon adayı"],
}
TEST_LEVEL = ("id", "title", "pre", "priority", "req", "tags", "tdata", "polarity", "technique", "status", "auto")
PRI = {"highest": "c", "blocker": "c", "critical": "c", "kritik": "c", "p1": "c", "high": "h", "yüksek": "h",
       "major": "h", "p2": "h", "medium": "m", "normal": "m", "orta": "m", "p3": "m",
       "low": "l", "lowest": "l", "minor": "l", "trivial": "l", "düşük": "l", "p4": "l"}
POL = {"positive": "+", "pozitif": "+", "pos": "+", "+": "+", "negative": "-", "negatif": "-", "neg": "-", "-": "-"}
TECH = {"ep": "ep", "bva": "bva", "dt": "dt", "st": "st", "pw": "pw", "ct": "ct", "uc": "uc", "sc": "sc",
        "crud": "crud", "eg": "eg", "cl": "cl", "ex": "ex", "rb": "rb",
        "equivalence-partitioning": "ep", "boundary-value-analysis": "bva", "decision-table": "dt",
        "state-transition": "st", "pairwise": "pw", "classification-tree": "ct", "use-case": "uc",
        "scenario": "sc", "error-guessing": "eg", "checklist": "cl", "exploratory": "ex",
        "requirements-based": "rb", "denklik sınıfı": "ep", "eşdeğer sınıf": "ep", "eşdeğerlik sınıfı": "ep",
        "sınır değer analizi": "bva", "sınır değer": "bva", "karar tablosu": "dt", "durum geçişi": "st",
        "ikili test": "pw", "sınıflandırma ağacı": "ct", "kullanım senaryosu": "uc", "senaryo": "sc",
        "hata tahmini": "eg", "kontrol listesi": "cl", "keşif testi": "ex", "gereksinim tabanlı": "rb"}
STATUS = {"draft": "draft", "taslak": "draft", "ready": "ready", "hazır": "ready", "approved": "ready",
          "onaylandı": "ready", "onaylı": "ready", "deprecated": "deprecated", "obsolete": "deprecated",
          "iptal": "deprecated", "kullanım dışı": "deprecated"}
YES = {"yes", "y", "evet", "e", "true", "1", "x"}
NO = {"no", "n", "hayır", "h", "false", "0"}
NEG = re.compile(r"(geçersiz|hatal|hata mesaj|reddedil|red |izin veril(mez|memeli)|engellen|yetkisiz|invalid|error|"
                 r"reject|denied|not allowed|fail|blocked|unauthori[sz]ed|negative|negatif)", re.I)
NUM = re.compile(r"(?:^|\n|\s)(\d{1,2})[.)]\s+")
BULLET = re.compile(r"^\s*[-•*▪]\s+")
TCID = re.compile(r"^TC-\d{3,}$")
_TR = str.maketrans({"ı": "i", "ş": "s", "ğ": "g", "ü": "u", "ö": "o", "ç": "c", "â": "a", "î": "i", "û": "u"})


def fold(s: str) -> str:
    """Case- and Turkish-letter-insensitive key: 'BEKLENEN SONUÇ', 'Beklenen sonuc' -> 'beklenen sonuc'."""
    return s.casefold().replace("i" + chr(0x307), "i").translate(_TR)


def norm(h: str) -> str:
    return re.sub(r"\s+", " ", fold(h or "").replace("_", " ")).strip(" *:.")


def folded(d: dict) -> dict:
    return {norm(k): v for k, v in d.items()}


ALIASES_F = {k: list(dict.fromkeys(norm(n) for n in v)) for k, v in ALIASES.items()}
PRI_F, POL_F, TECH_F, STATUS_F = folded(PRI), folded(POL), folded(TECH), folded(STATUS)
YES_F, NO_F = {norm(x) for x in YES}, {norm(x) for x in NO}


# ------------------------------------------------------------------ column detection
def numeric_column(rows: list[list[str]], c: int) -> bool:
    vals = [r[c].strip() for r in rows if c < len(r) and r[c].strip()]
    return bool(vals) and all(re.fullmatch(r"\d{1,3}[.)]?", v) for v in vals)


def detect(headers: list[str], overrides: dict, rows: list[list[str]] = ()) -> dict:
    cols: dict = {}
    low = [norm(h) for h in headers]
    bare = [re.sub(r"\s*\([^)]*\)", "", h).strip() for h in low]
    for key, names in ALIASES_F.items():
        if key in overrides:
            want = norm(overrides[key])
            cols[key] = low.index(want) if want in low else None
            continue
        cands = [low.index(n) for n in names if n in low] or [bare.index(n) for n in names if n in bare]
        if key == "steps" and rows:
            cands = [c for c in cands if not numeric_column(rows, c)] or cands  # skip a step-number column
        if cands:
            cols[key] = cands[0]
    if cols.get("tdata") is not None and cols.get("tdata") == cols.get("data"):
        del cols["tdata"]
    return cols


def usable(cols: dict) -> bool:
    return cols.get("title") is not None and cols.get("steps") is not None


def find_header(table: list, overrides: dict):
    """-> (index of the last header row in table, header cells, cols) or None. Scans the first 30 rows,
    then tries two-row headers (a group header above sub-headers)."""
    limit = min(len(table), 30)
    for i in range(limit):
        cols = detect(table[i][1], overrides, [r for _, r in table[i + 1:i + 201]])
        if usable(cols):
            return i, table[i][1], cols
    for i in range(limit - 1):
        up, down = table[i][1], table[i + 1][1]
        comb = [down[j] if j < len(down) and down[j].strip() else (up[j] if j < len(up) else "")
                for j in range(max(len(up), len(down)))]
        cols = detect(comb, overrides, [r for _, r in table[i + 2:i + 202]])
        if usable(cols):
            return i + 1, comb, cols
    return None


# ------------------------------------------------------------------ CSV
def sniff(text: str) -> str:
    lines = [ln for ln in text.splitlines() if ln.strip()][:20]
    for ln in lines:
        try:
            d = csv.Sniffer().sniff(ln, delimiters=",;\t").delimiter
        except csv.Error:
            continue
        if len(next(csv.reader([ln], delimiter=d))) >= 3:  # a header line has several fields
            return d
    return max(",;\t", key=lambda d: sum(ln.count(d) for ln in lines))


def read_csv(path: Path, delimiter: str | None) -> tuple[list, str]:
    raw = path.read_bytes()
    note = ""
    if raw[:2] in (b"\xff\xfe", b"\xfe\xff"):
        text = raw.decode("utf-16")
    else:
        try:
            text = raw.decode("utf-8-sig")
        except UnicodeDecodeError:
            text = raw.decode("cp1254", errors="replace")  # Turkish Windows "CSV (comma delimited)"
            note = "file is not UTF-8; read as Windows-1254 (Turkish). Prefer 'CSV UTF-8' when saving from Excel."
    rows = list(csv.reader(io.StringIO(text), delimiter=delimiter or sniff(text)))
    return [(n, r) for n, r in enumerate(rows, 1)], note


# ------------------------------------------------------------------ XLSX (stdlib only)
def _local(tag) -> str:
    return tag.rsplit("}", 1)[-1] if isinstance(tag, str) else ""


def _text(el) -> str:
    """Text of a shared-string <si> or inline <is>: plain <t> or rich-text runs; phonetic runs are skipped."""
    parts = []
    for child in el:
        t = _local(child.tag)
        if t == "t":
            parts.append(child.text or "")
        elif t == "r":
            parts += [x.text or "" for x in child if _local(x.tag) == "t"]
    s = re.sub(r"_x([0-9A-Fa-f]{4})_", lambda m: chr(int(m.group(1), 16)), "".join(parts))
    return s.replace("\r\n", "\n").replace("\r", "\n")


def _fmt_kind(fid: int, code: str | None) -> str:
    if code is None:
        if fid in (9, 10):
            return "percent"
        if 14 <= fid <= 17 or 27 <= fid <= 36 or 50 <= fid <= 58:
            return "date"
        if 18 <= fid <= 21 or 45 <= fid <= 47:
            return "time"
        return "datetime" if fid == 22 else ""
    s = re.sub(r'"[^"]*"|\\.|_.|\*.', "", code).split(";")[0]
    if re.search(r"\[(h+|m+|s+)\]", s, re.I):
        return "time"
    s = re.sub(r"\[[^\]]*\]", "", s).lower()
    if s.strip() in ("general", "@", ""):
        return ""
    has_time = "h" in s or "s" in s
    has_date = "y" in s or "d" in s or ("m" in s and not has_time)
    if has_date:
        return "datetime" if has_time else "date"
    if has_time:
        return "time"
    return "percent" if "%" in s else ""


def _styles(data: bytes) -> list[str]:
    root = ET.fromstring(data)
    custom = {}
    for e in root.iter():
        if _local(e.tag) == "numFmt" and (e.get("numFmtId") or "").isdigit():
            custom[int(e.get("numFmtId"))] = e.get("formatCode", "")
    kinds = []
    for group in root:
        if _local(group.tag) == "cellXfs":
            for xf in group:
                if _local(xf.tag) == "xf":
                    fid = int(xf.get("numFmtId", "0") or 0)
                    kinds.append(_fmt_kind(fid, custom.get(fid)))
    return kinds


def _plain(f: float) -> str:
    return str(int(f)) if f.is_integer() and abs(f) < 1e15 else format(f, ".15g")


def _serial(f: float, kind: str, date1904: bool) -> str:
    base = datetime(1904, 1, 1) if date1904 else datetime(1899, 12, 31 if f < 60 else 30)  # Excel's 1900 leap bug
    dt = base + timedelta(seconds=round(f * 86400))
    if kind == "time" or (f < 1 and kind != "date"):
        return dt.strftime("%H:%M:%S" if dt.second else "%H:%M")
    if kind == "date" or (dt.hour, dt.minute, dt.second) == (0, 0, 0):
        return dt.strftime("%Y-%m-%d")
    return dt.strftime("%Y-%m-%d %H:%M:%S" if dt.second else "%Y-%m-%d %H:%M")


def _cell(c, shared: list, kinds: list, date1904: bool) -> str:
    t = c.get("t", "n")
    v = next((x.text for x in c if _local(x.tag) == "v"), None)
    if t == "s":
        return shared[int(v)] if v and v.strip().isdigit() and int(v) < len(shared) else ""
    if t == "inlineStr":
        return next((_text(x) for x in c if _local(x.tag) == "is"), "")
    if t in ("str", "e"):
        return v or ""
    if t == "b":
        return "TRUE" if (v or "").strip() == "1" else "FALSE"
    if t == "d":
        return (v or "").replace("T00:00:00", "").rstrip("Z")
    if v is None or not v.strip():
        return ""
    try:
        f = float(v)
    except ValueError:
        return v
    s = c.get("s", "0")
    kind = kinds[int(s)] if s.isdigit() and int(s) < len(kinds) else ""
    try:
        if kind in ("date", "time", "datetime"):
            return _serial(f, kind, date1904)
    except (OverflowError, ValueError):
        return _plain(f)
    return _plain(f * 100) + "%" if kind == "percent" else _plain(f)


def _ref(ref: str):
    m = re.fullmatch(r"\$?([A-Za-z]{1,3})\$?(\d+)", ref or "")
    if not m:
        return None
    col = 0
    for ch in m.group(1).upper():
        col = col * 26 + ord(ch) - 64
    return int(m.group(2)), col - 1


def _sheet(data: bytes, shared: list, kinds: list, date1904: bool) -> tuple[list, list]:
    root = ET.fromstring(data)
    cells: dict[int, dict[int, str]] = {}
    merges = []
    for el in root:
        tag = _local(el.tag)
        if tag == "sheetData":
            rn = 0
            for row in el:
                if _local(row.tag) != "row":
                    continue
                rn = int(row.get("r")) if (row.get("r") or "").isdigit() else rn + 1
                ci = -1
                for c in row:
                    if _local(c.tag) != "c":
                        continue
                    pos = _ref(c.get("r", ""))
                    ci = pos[1] if pos else ci + 1
                    val = _cell(c, shared, kinds, date1904)
                    if val.strip():
                        cells.setdefault(rn, {})[ci] = val
        elif tag == "mergeCells":
            for mc in el:
                a, _, b = (mc.get("ref") or "").partition(":")
                p, q = _ref(a), _ref(b)
                if p and q:
                    merges.append((p[0], p[1], q[0], q[1]))
    table = [(n, [cells[n].get(i, "") for i in range(max(cells[n]) + 1)]) for n in sorted(cells)]
    return table, merges


def _rels(z: zipfile.ZipFile, path: str) -> dict:
    """Relationship Id -> (type, resolved part name)."""
    if path not in z.namelist():
        return {}
    base = posixpath.dirname(posixpath.dirname(path))  # xl/_rels/workbook.xml.rels -> xl
    out = {}
    for r in ET.fromstring(z.read(path)):
        target = r.get("Target", "")
        if r.get("TargetMode") == "External":
            continue
        part = target.lstrip("/") if target.startswith("/") else posixpath.normpath(posixpath.join(base, target))
        out[r.get("Id")] = (r.get("Type", ""), part)
    return out


def read_xlsx(path: Path) -> list[dict]:
    """-> [{"name", "hidden", "rows": [(row number, cells)], "merges": [(r1, c1, r2, c2)]}]"""
    try:
        z = zipfile.ZipFile(path)
    except zipfile.BadZipFile:
        raise ValueError("not an .xlsx workbook (legacy .xls and password-protected files cannot be read: "
                         "save as .xlsx or CSV UTF-8)")
    with z:
        names = set(z.namelist())
        wb_path = next((p for t, p in _rels(z, "_rels/.rels").values() if t.endswith("/officeDocument")),
                       "xl/workbook.xml")
        if wb_path not in names:
            raise ValueError("a zip file but not an Excel workbook (.ods or .numbers?): save it as .xlsx or CSV UTF-8")
        wb = ET.fromstring(z.read(wb_path))
        rels = _rels(z, posixpath.join(posixpath.dirname(wb_path), "_rels", posixpath.basename(wb_path) + ".rels"))
        date1904 = any(_local(e.tag) == "workbookPr" and (e.get("date1904") or "").lower() in ("1", "true")
                       for e in wb.iter())
        by_type = {t.rsplit("/", 1)[-1]: p for t, p in rels.values()}
        ss_path = by_type.get("sharedStrings", "xl/sharedStrings.xml")
        st_path = by_type.get("styles", "xl/styles.xml")
        shared = [_text(si) for si in ET.fromstring(z.read(ss_path)) if _local(si.tag) == "si"] \
            if ss_path in names else []
        kinds = _styles(z.read(st_path)) if st_path in names else []
        sheets = []
        for s in wb.iter():
            if _local(s.tag) != "sheet":
                continue
            rid = next((v for k, v in s.attrib.items() if k.startswith("{") and k.endswith("}id")), None)
            typ, part = rels.get(rid, ("", ""))
            if not part or part not in names or not typ.endswith("/worksheet"):
                continue  # chart sheets, dialog sheets
            rows, merges = _sheet(z.read(part), shared, kinds, date1904)
            sheets.append({"name": s.get("name", "?"), "hidden": s.get("state", "visible") != "visible",
                           "rows": rows, "merges": merges})
    return sheets


def is_xlsx(path: Path) -> bool:
    with open(path, "rb") as fh:
        head = fh.read(8)
    if head.startswith(b"\xd0\xcf\x11\xe0"):
        raise ValueError("legacy .xls or password-protected workbook: open it in Excel and save as .xlsx or CSV UTF-8")
    if path.suffix.lower() in (".xls", ".xlsx", ".xlsm") and head.lstrip()[:1] == b"<":
        raise ValueError("this 'Excel' file is an HTML page (a web export): open it in Excel and save as .xlsx")
    return head.startswith(b"PK")


# ------------------------------------------------------------------ rows -> tests
def split_numbered(cell: str) -> list[str]:
    cell = (cell or "").strip()
    if not cell:
        return []
    lines = [ln for ln in cell.splitlines() if ln.strip()]
    if len(lines) > 1 and all(BULLET.match(ln) for ln in lines):  # "- a\n- b" (bullet list)
        return [BULLET.sub("", ln).strip() for ln in lines]
    parts = NUM.split("\n" + cell)
    if len(parts) >= 3:  # ['', '1', 'text', '2', 'text' ...]
        return [p.strip().replace("\n", " ") for p in parts[2::2]]
    return [ln.strip(" -•\t") for ln in lines] or [cell]


def one(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())


def joined(s: str) -> str:
    """A multi-line cell (Alt+Enter) -> one line, lines separated by '; '."""
    return "; ".join(one(x) for x in (s or "").splitlines() if x.strip())


def fill_merged(table: list, merges: list, cols: dict, header_row: int):
    """Merged cells hold their value only in the top-left cell: copy a test-level value (ID, title,
    priority …) down over the rows the merge spans, so step rows stay attached to their test."""
    fill = {cols[k] for k in TEST_LEVEL if cols.get(k) is not None}
    rows = dict(table)
    for r1, c1, r2, _ in merges:
        if c1 not in fill or r2 <= r1:
            continue
        top = rows.get(r1, [])
        val = top[c1] if c1 < len(top) else ""
        for r in range(max(r1 + 1, header_row + 1), r2 + 1):
            cells = rows.get(r)
            if cells is None:
                continue
            cells.extend([""] * (c1 + 1 - len(cells)))
            if not cells[c1].strip():
                cells[c1] = val


def parse_tests(data: list, cols: dict, prefix: str = "") -> tuple["OrderedDict[str, dict]", bool]:
    def get(r, k):
        return (r[cols[k]] if cols.get(k) is not None and cols[k] < len(r) else "").strip()

    def continuation(r):
        return not get(r, "id") and not get(r, "title") and bool(get(r, "steps") or get(r, "expected"))

    # rows without title, steps and expected (blank rows, "Total: 12" footers) carry no test content
    rows = [(n, r) for n, r in data if get(r, "title") or get(r, "steps") or get(r, "expected")]
    ids = [get(r, "id") for _, r in rows if get(r, "id")]
    row_per_step = (cols.get("id") is not None and len(set(ids)) < len(ids)) or any(continuation(r) for _, r in rows)
    tests: "OrderedDict[str, dict]" = OrderedDict()
    last = None
    for n, r in rows:
        rid = get(r, "id") or (last if last is not None and continuation(r) else f"row{n}")
        key = prefix + rid
        t = tests.get(key)
        if t is None:
            t = tests[key] = {"src": rid, "title": one(get(r, "title")), "pre": get(r, "pre"),
                              **{k: get(r, k) for k in ("priority", "req", "tags", "tdata", "polarity",
                                                        "technique", "status", "auto")}, "steps": []}
        last = rid
        if row_per_step:
            if get(r, "steps") or get(r, "expected"):
                t["steps"].append((joined(get(r, "steps")), joined(get(r, "data")), joined(get(r, "expected"))))
        else:
            acts, exps, datas = split_numbered(get(r, "steps")), split_numbered(get(r, "expected")), split_numbered(get(r, "data"))
            for i in range(max(len(acts), len(exps))):
                t["steps"].append((acts[i] if i < len(acts) else "", datas[i] if i < len(datas) else "",
                                   exps[i] if i < len(exps) else ""))
    return tests, row_per_step


def lookup(value: str, table: dict) -> str | None:
    v = norm(value)
    if v in table:
        return table[v]
    return next((table[tok] for tok in re.split(r"[\s/()\-_,]+", v) if tok in table), None)


def test_data_line(text: str) -> str:
    pairs = []
    for ln in text.splitlines():
        ln = BULLET.sub("", ln).strip()
        if not ln:
            continue
        m = re.match(r"^([^:=]{1,40}?)\s*[:=]\s*(.+)$", ln)
        pairs.append(f"{m.group(1).strip()}={m.group(2).strip()}" if m else ln)
    return "; ".join(p.replace(";", ",").replace(" | ", " / ") for p in pairs)


def step_line(i: int, act: str, data: str, exp: str) -> str:
    act = (act or "-").replace("=>", "->")
    data = (data or "").replace("=>", "->").replace("[", "(").replace("]", ")")
    if data:
        d = f" [{data}]"
    elif act.endswith("]"):
        d = " []"  # keeps a trailing "[label]" in the action from being read as step data
    else:
        d = ""
    return f"{i}. {act}{d} => {exp}"


def safe_tag(s: str) -> str:
    return re.sub(r"[\s|:]+", "-", s.strip()).strip("-")


def emit(tests: list[dict], a, sources: list[str]) -> tuple[list[str], dict]:
    keep = not a.renumber and bool(tests) and all(TCID.match(t["src"]) for t in tests) \
        and len({t["src"] for t in tests}) == len(tests)
    out = [f"# Imported by import_tests.py from {'; '.join(sources)}. IDs {'kept' if keep else 'renumbered'}. "
           "Defaults: pol guessed, tech rb, req UNLINKED when missing - review before use.",
           f"language: {a.lang}"] + ([f"project: {a.project}"] if a.project else [])
    num = a.start
    stats = {"tests": 0, "unlinked": 0, "no_expected": 0}
    for t in tests:
        if not t["steps"]:
            t["steps"] = [("(adım yok)" if a.lang == "tr" else "(no steps)", "", "")]
        reqs = re.findall(r"\bREQ-\d+\b|\b[A-Z][A-Z0-9]+-\d+\b", t["req"])
        if not reqs:
            stats["unlinked"] += 1
        text = " ".join([t["title"]] + [s[2] for s in t["steps"]])
        pol = lookup(t["polarity"], POL_F) if t["polarity"] else None
        pol = pol or ("-" if NEG.search(text) else "+")
        pri = lookup(t["priority"], PRI_F) if t["priority"] else None
        tech = (lookup(t["technique"], TECH_F) if t["technique"] else None) or "rb"
        status = (lookup(t["status"], STATUS_F) if t["status"] else None) or "draft"
        tags = ["imported"] + ([] if keep else [f"src-{re.sub(r'[^A-Za-z0-9-]', '-', t['src'])}"]) + t["extra_tags"] \
            + [safe_tag(x) for x in re.split(r"[,;\n]", t["tags"]) if x.strip()]
        tid = t["src"] if keep else f"TC-{num:03d}"
        out += ["", f"## {tid} | {t['title'] or t['src']}",
                f"req: {', '.join(dict.fromkeys(reqs)) or 'UNLINKED'} | pri: {pri or 'm'} | pol: {pol} | tech: {tech}"]
        for p in split_numbered(t["pre"]) if t["pre"] else []:
            out.append(f"pre: {one(p).replace(' | ', ' / ')}")
        if t["tdata"]:
            out.append(f"data: {test_data_line(t['tdata'])}")
        for i, (act, data, exp) in enumerate(t["steps"], 1):
            if not exp:
                stats["no_expected"] += 1
            out.append(step_line(i, act, data, exp))
        auto = norm(t["auto"])
        auto = " | auto: yes" if auto in YES_F else " | auto: no" if auto in NO_F else ""
        out.append(f"tags: {', '.join(t for t in dict.fromkeys(tags) if t)}{auto} | status: {status}")
        num += 1
        stats["tests"] += 1
    return out, stats


def pick_sheets(sheets: list, choice: str | None, overrides: dict) -> list:
    if choice is None:
        for s in sheets:
            if not s["hidden"] and find_header(s["rows"], overrides):
                return [s]
        return [next((s for s in sheets if not s["hidden"]), sheets[0])] if sheets else []
    if choice.lower() in ("all", "*"):
        return [s for s in sheets if not s["hidden"] and find_header(s["rows"], overrides)]
    named = [s for s in sheets if norm(s["name"]) == norm(choice)]
    if named:
        return named
    if choice.isdigit() and 1 <= int(choice) <= len(sheets):
        return [sheets[int(choice) - 1]]
    raise ValueError(f"no sheet '{choice}'; sheets: " + ", ".join(repr(s["name"]) for s in sheets))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source", help=".xlsx workbook or CSV file")
    ap.add_argument("--out")
    ap.add_argument("--sheet", help="xlsx: sheet name, 1-based number, or 'all' (default: first sheet with a header)")
    ap.add_argument("--list-sheets", action="store_true", help="print the sheets and the detected header, then exit")
    ap.add_argument("--delimiter", help="CSV: default auto-detect , ; or tab")
    ap.add_argument("--start", type=int, default=1)
    ap.add_argument("--renumber", action="store_true", help="always assign new TC IDs (the source ID goes to a src- tag)")
    ap.add_argument("--lang", choices=["tr", "en"], default="tr")
    ap.add_argument("--project", default="")
    ap.add_argument("--map", default="", help="explicit column mapping, e.g. title=Summary,steps=Action,expected=Result")
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    a = ap.parse_args()
    if not a.out and not a.list_sheets:
        ap.error("--out is required (or use --list-sheets)")
    overrides = dict(p.split("=", 1) for p in a.map.split(",") if "=" in p)
    src = Path(a.source)
    try:
        if is_xlsx(src):
            sheets = read_xlsx(src)
            note = ""
        else:
            rows, note = read_csv(src, a.delimiter)
            sheets = [{"name": src.name, "hidden": False, "rows": rows, "merges": []}]
    except (OSError, ValueError, KeyError, ET.ParseError, zipfile.BadZipFile, csv.Error) as e:
        print(f"error: cannot read {src}: {e}", file=sys.stderr)
        return 2
    if note:
        print(f"note: {note}")
    for s in sheets:
        s["rows"] = [(n, r) for n, r in s["rows"] if any(c.strip() for c in r)]
    if a.list_sheets:
        for i, s in enumerate(sheets, 1):
            h = find_header(s["rows"], overrides)
            where = (f"header row {s['rows'][h[0]][0]}: " + ", ".join(f"{k}={h[1][v]}" for k, v in h[2].items())
                     if h else "no title/steps header found")
            print(f"{i}. {s['name']}{' (hidden)' if s['hidden'] else ''} · {len(s['rows'])} rows · {where}")
        return 0
    try:
        chosen = pick_sheets(sheets, a.sheet, overrides)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    if not chosen:
        print("error: the workbook has no sheet with a title/steps header row; use --list-sheets and --map", file=sys.stderr)
        return 2
    tests, sources, layouts, colinfo = [], [], [], []
    multi = len(chosen) > 1
    for s in chosen:
        h = find_header(s["rows"], overrides)
        if h is None:
            first = s["rows"][0][1] if s["rows"] else []
            print(f"error: could not find title/steps columns in '{s['name']}' (first row: {first}); "
                  "use --map title=...,steps=...", file=sys.stderr)
            return 2
        idx, header, cols = h
        fill_merged(s["rows"], s["merges"], cols, s["rows"][idx][0])
        parsed, row_per_step = parse_tests(s["rows"][idx + 1:], cols, prefix=f"{s['name']}::" if multi else "")
        for t in parsed.values():
            t["extra_tags"] = [safe_tag(s["name"])] if multi else []
            tests.append(t)
        layout = "row per step" if row_per_step else "row per test"
        layouts.append(layout)
        where = f"sheet '{s['name']}', " if s["name"] != src.name else ""
        sources.append(f"{src.name} ({where}header row {s['rows'][idx][0]}, {layout})")
        colinfo.append(("" if not multi else f"[{s['name']}] ") + ", ".join(f"{k}={header[v]}" for k, v in cols.items() if v is not None))
    out, stats = emit(tests, a, sources)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {a.out}: {stats['tests']} tests ({', '.join(dict.fromkeys(layouts))}) · "
          f"unlinked {stats['unlinked']} · steps without expected {stats['no_expected']}")
    for s in sources:
        print(f"source: {s}")
    for c in colinfo:
        print(f"columns: {c}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
