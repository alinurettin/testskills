# -*- coding: utf-8 -*-
"""Evaluator helper (stdlib only): parse an .xlsx back and print every sheet as text.
Usage:  python tools/dump_xlsx.py inputs/FAST_Transfer_Test_Cases.xlsx [--check]
--check  only validates structure (sheet names, header row, row count, unique IDs) and exits non-zero on failure.
Do NOT hand this folder to the agent under test; give it only TASK.md and inputs/."""
import re
import sys
import zipfile
import xml.etree.ElementTree as ET

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
      "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
      "pr": "http://schemas.openxmlformats.org/package/2006/relationships"}


def col_index(ref):
    letters = re.match(r"[A-Z]+", ref).group(0)
    n = 0
    for ch in letters:
        n = n * 26 + (ord(ch) - 64)
    return n - 1


def read_workbook(path):
    with zipfile.ZipFile(path) as z:
        bad = z.testzip()
        if bad:
            raise SystemExit("corrupt zip member: %s" % bad)
        sst = []
        if "xl/sharedStrings.xml" in z.namelist():
            root = ET.fromstring(z.read("xl/sharedStrings.xml"))
            for si in root.findall("m:si", NS):
                sst.append("".join(t.text or "" for t in si.iter("{%s}t" % NS["m"])))
        wb = ET.fromstring(z.read("xl/workbook.xml"))
        rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
        target = {r.get("Id"): r.get("Target") for r in rels.findall("pr:Relationship", NS)}
        sheets = []
        for sh in wb.find("m:sheets", NS):
            rid = sh.get("{%s}id" % NS["r"])
            root = ET.fromstring(z.read("xl/" + target[rid]))
            rows = []
            for row in root.find("m:sheetData", NS).findall("m:row", NS):
                vals = []
                for c in row.findall("m:c", NS):
                    i = col_index(c.get("r"))
                    while len(vals) < i:
                        vals.append("")
                    v = c.find("m:v", NS)
                    if c.get("t") == "s" and v is not None:
                        vals.append(sst[int(v.text)])
                    elif c.get("t") == "inlineStr":
                        vals.append("".join(t.text or "" for t in c.iter("{%s}t" % NS["m"])))
                    else:
                        vals.append(v.text if v is not None else "")
                rows.append(vals)
            sheets.append((sh.get("name"), rows))
        return sheets


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    sheets = read_workbook(sys.argv[1])
    if "--check" in sys.argv:
        names = [n for n, _ in sheets]
        assert names == ["Test Cases", "Bilgi"], names
        rows = sheets[0][1]
        assert rows[0] == ["Test ID", "Başlık", "Ön Koşul", "Adımlar", "Beklenen Sonuç", "Öncelik", "Gereksinim"], rows[0]
        ids = [r[0] for r in rows[1:]]
        assert len(ids) == len(set(ids)), "duplicate Test IDs"
        multiline = sum(1 for r in rows[1:] if "\n" in r[3])
        print("OK: sheets=%s test_cases=%d multiline_step_cells=%d" % (names, len(ids), multiline))
        return
    for name, rows in sheets:
        print("=" * 30, name, "=" * 30)
        for r in rows:
            print(" | ".join(x.replace("\n", " / ") for x in r))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
