#!/usr/bin/env python3
"""Export QA Suite test cases to test-management import formats.

Formats (each checked against the vendor's import documentation on 2026-09-30,
see references/*.md for the URLs and the wizard steps)
  xray      Xray (Jira) Test Case Importer CSV - one row per step, rows grouped
            by "TCID"; map TCID -> Test ID (Server/DC: Test Case Identifier),
            Summary, Test Type (Manual, repeated on every row) and Action/Data/
            Expected Result to the manual step fields. Requirement Keys -> Link
            "Tests" (Cloud: one cell, --list-delimiter; Server/DC: --xray-links
            columns writes one column per key). --folder adds "Test Repository
            Folder" (a/b).
  zephyr    Zephyr (Scale) CSV. --zephyr-steps rows (default): first row holds the
            test fields + step 1, following rows hold only step columns;
            --zephyr-steps single: one row per test, steps in "Test Script
            (Plain Text)". --zephyr-data inline moves step data into the Step
            cell when the wizard offers no Test Data target. Labels and Coverage
            are comma-separated. Try a 2-3 test import first.
  csv       Generic spreadsheet CSV - one row per test, steps numbered in cells.
  xlsx      Excel workbook (no third-party library needed) - Test Cases sheet
            (one row per step) + Summary sheet.
  testrail  TestRail CSV, template "Test Case (Steps)", layout "Test cases use multiple rows": Title marks a new
            case, continuation rows leave Title empty; Section "A > B"; References = REQ IDs + Jira keys.
  azure-devops  Azure DevOps Test Plans CSV import: one row per step, test fields repeated, Test Step 1..n,
            the nine required columns + Priority 1-4, State Design (--area-path, --assigned-to).
            Requirement links cannot be imported: import into a requirement-based suite instead.
  qase      Qase CSV (V2 headers, "Qase.io" source): suite rows first, steps numbered inside one cell as
            1. "text" per line; line breaks inside a step are written as \\n. --folder a/b nests suites.
  markdown  Readable document for reviews / Confluence.

--folder accepts "A/B" or "A > B" and is written in each tool's own syntax
(Xray, Zephyr: A/B; TestRail: A > B; Qase: nested suites).

Requirement links use requirements.json "external_id" (Jira keys such as
SHOP-123) when --requirements is given; internal REQ IDs are always kept in a
label/column so traceability survives the import.

Usage
  python export_tests.py --tests qa/test-cases.json --requirements qa/requirements.json \\
      --format xray --out qa/exports/xray.csv [--delimiter ,] [--list-delimiter ";"] [--bom]
  python export_tests.py --tests qa/test-cases.json --format zephyr --folder "Checkout/Coupon" --out qa/exports/zephyr.csv
  python export_tests.py --tests qa/test-cases.json --format xlsx --out qa/exports/test-cases.xlsx
  Options: --include-deprecated, --priority-map '{"critical":"Highest"}', --only TC-001,TC-004,
           --tag smoke, --lang tr|en (headers of csv/xlsx/markdown), --xray-links cell|columns,
           --zephyr-data column|inline
Exit code 0 ok, 1 validation problems (nothing written), 2 unreadable input.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import re
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape

DEFAULT_PRIORITY = {"critical": "Highest", "high": "High", "medium": "Medium", "low": "Low"}
# default separator of multi-value cells (labels, keys) per format, used when --list-delimiter is not given.
# Xray: the importer's "list value delimiter" (Setup step); Zephyr: its import docs describe list values
# (Coverage) as comma-separated.
LIST_DELIMITER = {"xray": ";", "zephyr": ","}
# vendor limits from the import documentation (see references/*.md)
XRAY_MAX_ISSUES = 1000          # Xray Cloud: issues per import
XRAY_MAX_EXTRA_LINKS = 2000     # Xray Cloud: issue links apart from the first one in every test
TESTRAIL_MAX_BYTES = 10 * 1024 * 1024
ADO_MAX_BYTES = 20 * 1024 * 1024
ADO_TITLE_MAX = 128
H = {
    "en": {"id": "ID", "title": "Title", "objective": "Objective", "reqs": "Requirements", "ext": "Jira keys",
           "priority": "Priority", "polarity": "Polarity", "category": "Category", "technique": "Technique",
           "pre": "Preconditions", "data": "Test data", "step": "Step", "action": "Action", "sdata": "Data",
           "expected": "Expected result", "post": "Postconditions", "tags": "Tags", "auto": "Automation candidate",
           "reason": "Automation reason", "status": "Status", "steps": "Steps", "doc": "Test Cases",
           "sum": "Summary", "generated": "Generated", "count": "Test cases", "yes": "yes", "no": "no",
           "positive": "positive", "negative": "negative"},
    "tr": {"id": "ID", "title": "Başlık", "objective": "Amaç", "reqs": "Gereksinimler", "ext": "Jira anahtarları",
           "priority": "Öncelik", "polarity": "Polarite", "category": "Kategori", "technique": "Teknik",
           "pre": "Ön koşullar", "data": "Test verisi", "step": "Adım", "action": "Aksiyon", "sdata": "Veri",
           "expected": "Beklenen sonuç", "post": "Son koşullar", "tags": "Etiketler", "auto": "Otomasyon adayı",
           "reason": "Otomasyon gerekçesi", "status": "Durum", "steps": "Adımlar", "doc": "Test Case'ler",
           "sum": "Özet", "generated": "Oluşturulma", "count": "Test case sayısı", "yes": "evet", "no": "hayır",
           "positive": "pozitif", "negative": "negatif"},
}


# ------------------------------------------------------------------ helpers
def as_lines(v) -> str:
    if v is None:
        return ""
    if isinstance(v, list):
        return "\n".join(f"- {x}" for x in v)
    if isinstance(v, dict):
        return "\n".join(f"{k}: {x}" for k, x in v.items())
    return str(v)


def ext_keys(t: dict, ext_map: dict) -> list[str]:
    """Distinct external (Jira) keys of a test's requirements; several REQs may share one story key."""
    return list(dict.fromkeys(ext_map[r] for r in t.get("requirement_ids", []) if ext_map.get(r)))


def label(s: str) -> str:
    """Jira labels cannot contain spaces."""
    return re.sub(r"\s+", "-", str(s).strip())


def inline(v) -> str:
    """One-line form of preconditions/test data for tools without a field of their own."""
    if v is None:
        return ""
    if isinstance(v, list):
        return "; ".join(map(str, v))
    if isinstance(v, dict):
        return "; ".join(f"{k}: {x}" for k, x in v.items())
    return str(v)


def folder_parts(folder: str | None) -> list[str]:
    """--folder "A/B" or "A > B" -> ["A", "B"]; every format writes it in its own syntax."""
    return [p.strip() for p in re.split(r"[/>]", folder or "") if p.strip()]


def pre_and_data(t: dict, h: dict) -> str:
    """Preconditions + test data as one multi-line text (TestRail, Zephyr, Qase preconditions)."""
    pre = as_lines(t.get("preconditions"))
    if t.get("test_data"):
        pre += ("\n\n" if pre else "") + f"{h['data']}:\n{as_lines(t['test_data'])}"
    return pre


def validate(tests: list[dict]) -> list[str]:
    errs = []
    seen = set()
    for t in tests:
        tid = t.get("id")
        if not tid:
            errs.append(f"test without id: {t.get('title', '')[:50]}")
            continue
        if tid in seen:
            errs.append(f"{tid}: duplicate id")
        seen.add(tid)
        if not t.get("title"):
            errs.append(f"{tid}: missing title")
        if not t.get("steps"):
            errs.append(f"{tid}: no steps")
        for i, s in enumerate(t.get("steps", []), 1):
            if not str(s.get("action", "")).strip():
                errs.append(f"{tid} step {i}: missing action")
    return errs


def description(t: dict, h: dict, ext: list[str]) -> str:
    parts = []
    if t.get("objective"):
        parts.append(f"{h['objective']}: {t['objective']}")
    if t.get("preconditions"):
        parts.append(f"{h['pre']}:\n{as_lines(t['preconditions'])}")
    if t.get("test_data"):
        parts.append(f"{h['data']}:\n{as_lines(t['test_data'])}")
    if t.get("postconditions"):
        parts.append(f"{h['post']}:\n{as_lines(t['postconditions'])}")
    refs = ", ".join(t.get("requirement_ids", [])) or "-"
    meta = f"{h['reqs']}: {refs}"
    if ext:
        meta += f" ({', '.join(ext)})"
    meta += f" | {h['technique']}: {t.get('technique', '-')}"
    if t.get("design_ref"):
        meta += f" ({t['design_ref']})"
    meta += f" | QA-ID: {t['id']}"
    parts.append(meta)
    return "\n\n".join(parts)


def labels_for(t: dict) -> list[str]:
    ls = [label(x) for x in t.get("tags", [])]
    ls += [label(r) for r in t.get("requirement_ids", [])]
    if t.get("technique"):
        ls.append(label(t["technique"]))
    if t.get("polarity"):
        ls.append(t["polarity"])
    return list(dict.fromkeys(ls))


def csv_text(rows: list[list], delimiter: str) -> str:
    buf = io.StringIO()
    w = csv.writer(buf, delimiter=delimiter, quoting=csv.QUOTE_MINIMAL, lineterminator="\r\n")
    w.writerows(rows)
    return buf.getvalue()


# ------------------------------------------------------------------ formats
def export_xray(tests, ext_map, pmap, a, h):
    """Xray Test Case Importer CSV: one row per step, grouped by TCID (Test ID / Test Case Identifier).
    Test Type is repeated on every row, as in Xray's own importer examples."""
    ld = a.list_delimiter
    links_per_test = [ext_keys(t, ext_map) for t in tests]
    if a.xray_links == "columns":  # Server/DC: "multiple CSV columns must be used, each one mapped in the same way"
        n_links = max([1] + [len(x) for x in links_per_test])
        link_cols = [f"Requirement Key {i}" for i in range(1, n_links + 1)]
    else:                          # Cloud: link fields are list fields separated by the list delimiter
        link_cols = ["Requirement Keys"]
    folder = "/".join(folder_parts(a.folder))
    header = ["TCID", "Summary", "Description", "Test Type", "Priority", "Labels", "Component"] + link_cols + \
             ["Action", "Data", "Expected Result"] + (["Test Repository Folder"] if folder else [])
    rows = [header]
    missing_keys = set()
    for t, ext in zip(tests, links_per_test):
        missing_keys |= {r for r in t.get("requirement_ids", []) if not ext_map.get(r)}
        links = [ld.join(ext)] if a.xray_links == "cell" else ext + [""] * (len(link_cols) - len(ext))
        for i, s in enumerate(t["steps"]):
            if i == 0:
                base = [t["id"], t["title"], description(t, h, ext), a.test_type,
                        pmap.get(t.get("priority"), t.get("priority", "")), ld.join(labels_for(t)),
                        a.component or ""] + links
            else:
                base = [t["id"], "", "", a.test_type, "", "", ""] + [""] * len(link_cols)
            row = base + [s.get("action", ""), s.get("data", ""), s.get("expected", "")]
            if folder:
                row.append(folder if i == 0 else "")
            rows.append(row)
    return csv_text(rows, a.delimiter), missing_keys


def zephyr_script(steps) -> str:
    out = []
    for i, s in enumerate(steps, 1):
        line = f"{i}. {s.get('action', '')}"
        if s.get("data"):
            line += f" [{s['data']}]"
        if s.get("expected"):
            line += f" => {s['expected']}"
        out.append(line)
    return "\n".join(out)


def export_zephyr(tests, ext_map, pmap, a, h):
    ld = a.list_delimiter
    missing_keys = set()
    fields = ["Name", "Objective", "Precondition", "Folder", "Status", "Priority", "Labels", "Coverage"]
    if a.zephyr_steps == "single":
        header = fields + ["Test Script (Plain Text)"]
    elif a.zephyr_data == "inline":  # the documented step targets are Step and Expected Result only
        header = fields + ["Test Script (Step-by-Step) - Step", "Test Script (Step-by-Step) - Expected Result"]
    else:
        header = fields + ["Test Script (Step-by-Step) - Step", "Test Script (Step-by-Step) - Test Data",
                           "Test Script (Step-by-Step) - Expected Result"]
    folder = "/".join(folder_parts(a.folder))
    rows = [header]
    for t in tests:
        ext = ext_keys(t, ext_map)
        missing_keys |= {r for r in t.get("requirement_ids", []) if not ext_map.get(r)}
        objective = (t.get("objective") or "") + f"\n\n{h['reqs']}: {', '.join(t.get('requirement_ids', [])) or '-'}" \
                    f" | {h['technique']}: {t.get('technique', '-')} | QA-ID: {t['id']}"
        head = [f"{t['id']} {t['title']}", objective.strip(), pre_and_data(t, h), folder,
                "Approved" if t.get("status") == "ready" else "Draft",
                pmap.get(t.get("priority"), t.get("priority", "")), ld.join(labels_for(t)), ", ".join(ext)]
        if a.zephyr_steps == "single":
            rows.append(head + [zephyr_script(t["steps"])])
            continue
        for i, s in enumerate(t["steps"]):
            prefix = head if i == 0 else [""] * len(head)
            if a.zephyr_data == "inline":
                rows.append(prefix + [step_text(s), s.get("expected", "")])
            else:
                rows.append(prefix + [s.get("action", ""), s.get("data", ""), s.get("expected", "")])
    return csv_text(rows, a.delimiter), missing_keys


TESTRAIL_PRIORITY = {"critical": "Critical", "high": "High", "medium": "Medium", "low": "Low"}
ADO_PRIORITY = {"critical": "1", "high": "2", "medium": "3", "low": "4"}
QASE_PRIORITY = {"critical": "high", "high": "high", "medium": "medium", "low": "low"}
QASE_SEVERITY = {"critical": "critical", "high": "major", "medium": "normal", "low": "minor"}
QASE_TYPE = {"functional": "functional", "security": "security", "performance": "performance", "usability": "usability",
             "compatibility": "compatibility", "integration": "integration", "api": "functional", "accessibility": "usability"}
QASE_HEADER = ["v2.id", "title", "description", "preconditions", "postconditions", "tags", "priority", "severity",
               "type", "behavior", "automation", "status", "is_flaky", "layer", "steps_type", "steps_actions",
               "steps_result", "steps_data", "milestone_id", "milestone", "suite_id", "suite_parent_id", "suite",
               "suite_without_cases", "parameters"]


def step_text(s: dict) -> str:
    return s.get("action", "") + (f" [{s['data']}]" if s.get("data") else "")


def export_testrail(tests, ext_map, a, h):
    """TestRail CSV import, template "Test Case (Steps)", row layout "Test cases use multiple rows":
    map Title as the new-case detection column; continuation rows leave Title empty."""
    rows = [["Title", "Section", "Priority", "Type", "Preconditions", "Step", "Expected Result", "References"]]
    section = " > ".join(folder_parts(a.folder))
    for t in tests:
        refs = ", ".join(dict.fromkeys(list(t.get("requirement_ids", [])) + ext_keys(t, ext_map)))
        for i, s in enumerate(t["steps"]):
            if i == 0:
                rows.append([f"{t['id']} {t['title']}", section, TESTRAIL_PRIORITY.get(t.get("priority"), "Medium"),
                             "Regression" if "regression" in t.get("tags", []) else "Functional", pre_and_data(t, h),
                             step_text(s), s.get("expected", ""), refs])
            else:
                rows.append(["", "", "", "", "", step_text(s), s.get("expected", ""), ""])
    return rows


def ado_title(t: dict) -> str:
    return f"{t['id']} {t['title']}"[:ADO_TITLE_MAX]


def export_ado(tests, ext_map, a, h):
    """Azure DevOps Test Plans CSV import: one row per step, the nine required columns (ID, Work Item Type, Title,
    Test Step, Step Action, Step Expected, Area Path, Assigned To, State) + Priority repeated on every row.
    Requirement links are not importable (import into a requirement-based suite)."""
    rows = [["ID", "Work Item Type", "Title", "Test Step", "Step Action", "Step Expected", "Area Path", "Assigned To",
             "State", "Priority"]]
    for t in tests:
        title = ado_title(t)
        # no precondition/test-data fields on a Test Case: both go in front of the first step's action
        prefix = []
        if t.get("preconditions"):
            prefix.append(f"{h['pre']}: {inline(t['preconditions'])}")
        if t.get("test_data"):
            prefix.append(f"{h['data']}: {inline(t['test_data'])}")
        for i, s in enumerate(t["steps"], 1):
            action = step_text(s)
            if i == 1 and prefix:
                action = "\n".join(prefix + [action])
            rows.append(["", "Test Case", title, str(i), action, s.get("expected", ""), a.area_path or "",
                         a.assigned_to or "", "Design", ADO_PRIORITY.get(t.get("priority"), "3")])
    return rows


def qase_step(x) -> str:
    """V2 step content: wrapped in double quotes, so inner quotes become ' and inner line breaks the two
    characters \\n (as in Qase's own V2 export)."""
    return str(x if x is not None else "").replace('"', "'").replace("\r\n", "\n").replace("\n", "\\n")


def export_qase(tests, ext_map, a, h):
    """Qase CSV (V2 header set, source "Qase.io"): suite rows first (suite_without_cases 1, parents before
    children), then one row per case; steps numbered inside steps_actions/steps_result/steps_data, one
    '1. "text"' line per step."""
    parts = folder_parts(a.folder) or ["QA Suite"]
    rows = [QASE_HEADER]
    for i, name in enumerate(parts, 1):
        rows.append([""] * 20 + [str(i), str(i - 1) if i > 1 else "", name, "1", ""])
    leaf_id, leaf_parent, leaf = str(len(parts)), (str(len(parts) - 1) if len(parts) > 1 else ""), parts[-1]

    def numbered(xs):
        return "\n".join(f'{i}. "{qase_step(x)}"' for i, x in enumerate(xs, 1))

    for t in tests:
        refs = ", ".join(dict.fromkeys(list(t.get("requirement_ids", [])) + ext_keys(t, ext_map)))
        auto = (t.get("automation") or {}).get("candidate")
        tags = ",".join(dict.fromkeys([label(x) for x in t.get("tags", [])] + [label(r) for r in t.get("requirement_ids", [])]))
        desc = "\n".join(x for x in (t.get("objective") or "", f"{h['reqs']}: {refs}" if refs else "") if x)
        rows.append(["", f"{t['id']} {t['title']}", desc, pre_and_data(t, h), as_lines(t.get("postconditions")), tags,
                     QASE_PRIORITY.get(t.get("priority"), "medium"), QASE_SEVERITY.get(t.get("priority"), "normal"),
                     QASE_TYPE.get(t.get("category", "functional"), "other"),
                     "negative" if t.get("polarity") == "negative" else "positive",
                     "to-be-automated" if auto else "is-not-automated",
                     "actual" if t.get("status") == "ready" else "draft", "no",
                     "api" if t.get("category") == "api" else "e2e", "classic",
                     numbered([s.get("action", "") for s in t["steps"]]), numbered([s.get("expected", "") for s in t["steps"]]),
                     numbered([s.get("data", "") for s in t["steps"]]), "", "", leaf_id, leaf_parent, leaf, "", ""])
    return rows


def export_generic(tests, ext_map, a, h):
    header = [h["id"], h["title"], h["objective"], h["reqs"], h["ext"], h["priority"], h["polarity"], h["category"],
              h["technique"], h["pre"], h["data"], h["steps"], h["expected"], h["post"], h["tags"], h["auto"],
              h["reason"], h["status"]]
    rows = [header]
    for t in tests:
        steps = "\n".join(f"{i}. {s.get('action', '')}" + (f" [{s['data']}]" if s.get("data") else "")
                          for i, s in enumerate(t["steps"], 1))
        exp = "\n".join(f"{i}. {s.get('expected', '')}" for i, s in enumerate(t["steps"], 1))
        auto = t.get("automation") or {}
        rows.append([t["id"], t["title"], t.get("objective", ""), ", ".join(t.get("requirement_ids", [])),
                     ", ".join(ext_keys(t, ext_map)),
                     t.get("priority", ""), h.get(t.get("polarity"), t.get("polarity", "")), t.get("category", ""),
                     t.get("technique", ""), as_lines(t.get("preconditions")), as_lines(t.get("test_data")),
                     steps, exp, as_lines(t.get("postconditions")), ", ".join(t.get("tags", [])),
                     h["yes"] if auto.get("candidate") else h["no"], auto.get("reason", ""), t.get("status", "")])
    return rows


def export_markdown(tests, ext_map, h, project):
    o = [f"# {h['doc']}" + (f": {project}" if project else ""), "",
         f"{h['count']}: {len(tests)} · {h['generated']}: {datetime.now(timezone.utc).strftime('%Y-%m-%d')}", ""]
    o += [f"| {h['id']} | {h['title']} | {h['reqs']} | {h['priority']} | ± | {h['technique']} |", "|---|---|---|---|---|---|"]
    for t in tests:
        o.append(f"| [{t['id']}](#{t['id'].lower()}) | {t['title']} | {', '.join(t.get('requirement_ids', []))} | "
                 f"{t.get('priority', '')} | {'+' if t.get('polarity') == 'positive' else '−'} | {t.get('technique', '')} |")
    for t in tests:
        ext = ext_keys(t, ext_map)
        o += ["", f"## {t['id']}", "", f"**{t['title']}**", ""]
        meta = [f"**{h['reqs']}:** {', '.join(t.get('requirement_ids', []))}" + (f" ({', '.join(ext)})" if ext else ""),
                f"**{h['priority']}:** {t.get('priority', '')}",
                f"**{h['polarity']}:** {h.get(t.get('polarity'), t.get('polarity', ''))}",
                f"**{h['technique']}:** {t.get('technique', '')}" + (f" ({t['design_ref']})" if t.get("design_ref") else "")]
        o.append(" · ".join(meta))
        if t.get("objective"):
            o += ["", f"**{h['objective']}:** {t['objective']}"]
        if t.get("preconditions"):
            o += ["", f"**{h['pre']}:**", as_lines(t["preconditions"])]
        if t.get("test_data"):
            o += ["", f"**{h['data']}:**", as_lines(t["test_data"]).replace("\n", "  \n")]
        o += ["", f"| # | {h['action']} | {h['sdata']} | {h['expected']} |", "|---|---|---|---|"]
        for i, s in enumerate(t["steps"], 1):
            cells = [str(s.get(k, "")).replace("|", "\\|").replace("\n", "<br>") for k in ("action", "data", "expected")]
            o.append(f"| {i} | " + " | ".join(cells) + " |")
        if t.get("postconditions"):
            o += ["", f"**{h['post']}:**", as_lines(t["postconditions"])]
        if t.get("tags"):
            o += ["", f"**{h['tags']}:** {', '.join(t['tags'])}"]
    return "\n".join(o) + "\n"


# ------------------------------------------------------------------ minimal xlsx writer (stdlib only)
def _col(n: int) -> str:
    s = ""
    while n:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


_BAD_XML = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def _sheet_xml(rows: list[list], widths: list[int]) -> str:
    out = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
           '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">',
           '<sheetViews><sheetView workbookViewId="0"><pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" '
           'state="frozen"/></sheetView></sheetViews>', "<cols>"]
    for i, w in enumerate(widths, 1):
        out.append(f'<col min="{i}" max="{i}" width="{w}" customWidth="1"/>')
    out.append("</cols><sheetData>")
    for r, row in enumerate(rows, 1):
        out.append(f'<row r="{r}">')
        for c, v in enumerate(row, 1):
            style = 1 if r == 1 else 2
            ref = f"{_col(c)}{r}"
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                out.append(f'<c r="{ref}" s="{style}"><v>{v}</v></c>')
            else:
                txt = escape(_BAD_XML.sub("", str(v if v is not None else "")))
                out.append(f'<c r="{ref}" s="{style}" t="inlineStr"><is><t xml:space="preserve">{txt}</t></is></c>')
        out.append("</row>")
    out.append("</sheetData>")
    if len(rows) > 1:
        out.append(f'<autoFilter ref="A1:{_col(len(rows[0]))}{len(rows)}"/>')
    out.append("</worksheet>")
    return "".join(out)


def write_xlsx(path: Path, sheets: list[tuple[str, list[list], list[int]]]):
    ct = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
          '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">',
          '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>',
          '<Default Extension="xml" ContentType="application/xml"/>',
          '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>',
          '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>']
    wb_rels = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
               '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">']
    wb = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
          '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
          'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>']
    for i, (name, _, _) in enumerate(sheets, 1):
        ct.append(f'<Override PartName="/xl/worksheets/sheet{i}.xml" '
                  'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>')
        wb_rels.append(f'<Relationship Id="rId{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/'
                       f'relationships/worksheet" Target="worksheets/sheet{i}.xml"/>')
        wb.append(f'<sheet name="{escape(name[:31])}" sheetId="{i}" r:id="rId{i}"/>')
    n = len(sheets) + 1
    wb_rels.append(f'<Relationship Id="rId{n}" Type="http://schemas.openxmlformats.org/officeDocument/2006/'
                   'relationships/styles" Target="styles.xml"/></Relationships>')
    ct.append("</Types>")
    wb.append("</sheets></workbook>")
    styles = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
              '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
              '<fonts count="2"><font><sz val="11"/><name val="Calibri"/></font>'
              '<font><b/><sz val="11"/><color rgb="FFFFFFFF"/><name val="Calibri"/></font></fonts>'
              '<fills count="3"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill>'
              '<fill><patternFill patternType="solid"><fgColor rgb="FF1F4E79"/><bgColor indexed="64"/></patternFill></fill></fills>'
              '<borders count="2"><border/><border><left style="thin"><color rgb="FFBFBFBF"/></left>'
              '<right style="thin"><color rgb="FFBFBFBF"/></right><top style="thin"><color rgb="FFBFBFBF"/></top>'
              '<bottom style="thin"><color rgb="FFBFBFBF"/></bottom></border></borders>'
              '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
              '<cellXfs count="3"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>'
              '<xf numFmtId="0" fontId="1" fillId="2" borderId="1" xfId="0" applyFont="1" applyFill="1" applyBorder="1" applyAlignment="1">'
              '<alignment vertical="center" wrapText="1"/></xf>'
              '<xf numFmtId="0" fontId="0" fillId="0" borderId="1" xfId="0" applyBorder="1" applyAlignment="1">'
              '<alignment vertical="top" wrapText="1"/></xf></cellXfs></styleSheet>')
    rels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/'
            'officeDocument" Target="xl/workbook.xml"/></Relationships>')
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", "".join(ct))
        z.writestr("_rels/.rels", rels)
        z.writestr("xl/workbook.xml", "".join(wb))
        z.writestr("xl/_rels/workbook.xml.rels", "".join(wb_rels))
        z.writestr("xl/styles.xml", styles)
        for i, (_, rows, widths) in enumerate(sheets, 1):
            z.writestr(f"xl/worksheets/sheet{i}.xml", _sheet_xml(rows, widths))


def export_xlsx(tests, ext_map, h, path: Path, project: str):
    header = [h["id"], h["title"], h["reqs"], h["ext"], h["priority"], h["polarity"], h["technique"], h["pre"],
              h["data"], h["step"], h["action"], h["sdata"], h["expected"], h["tags"], h["auto"], h["status"]]
    rows = [header]
    for t in tests:
        auto = t.get("automation") or {}
        for i, s in enumerate(t["steps"], 1):
            first = i == 1
            rows.append([
                t["id"], t["title"] if first else "", ", ".join(t.get("requirement_ids", [])) if first else "",
                ", ".join(ext_keys(t, ext_map)) if first else "",
                t.get("priority", "") if first else "", h.get(t.get("polarity"), "") if first else "",
                t.get("technique", "") if first else "", as_lines(t.get("preconditions")) if first else "",
                as_lines(t.get("test_data")) if first else "", i, s.get("action", ""), s.get("data", ""),
                s.get("expected", ""), ", ".join(t.get("tags", [])) if first else "",
                (h["yes"] if auto.get("candidate") else h["no"]) if first else "", t.get("status", "") if first else ""])
    widths = [9, 40, 16, 14, 10, 10, 20, 36, 30, 6, 45, 25, 45, 18, 10, 10]
    summary = [[h["sum"], ""], ["Project", project], [h["count"], len(tests)],
               [h["generated"], datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")], ["", ""]]
    for key, field in ((h["priority"], "priority"), (h["polarity"], "polarity"), (h["technique"], "technique")):
        counts: dict = {}
        for t in tests:
            counts[t.get(field, "-")] = counts.get(t.get(field, "-"), 0) + 1
        summary.append([key, ""])
        summary += [[f"  {k}", v] for k, v in sorted(counts.items(), key=lambda kv: -kv[1])]
    write_xlsx(path, [(h["doc"], rows, widths), (h["sum"], summary, [30, 40])])


# ------------------------------------------------------------------ vendor limits and pitfalls
def import_notes(a, tests: list[dict], ext_map: dict, text: str | None) -> list[str]:
    """Warnings for documented importer limits and required fields (see references/*.md)."""
    notes = []
    size = len(text.encode("utf-8")) if text else 0
    if a.format == "xray":
        if len(tests) > XRAY_MAX_ISSUES:
            notes.append(f"warning: {len(tests)} tests; Xray Cloud imports at most {XRAY_MAX_ISSUES} issues per file. "
                         "Split the export with --only or --tag.")
        extra_links = sum(max(0, len(ext_keys(t, ext_map)) - 1) for t in tests)
        if extra_links > XRAY_MAX_EXTRA_LINKS:
            notes.append(f"warning: {extra_links} additional requirement links; Xray Cloud accepts at most "
                         f"{XRAY_MAX_EXTRA_LINKS} links apart from the first one of each test. Split the export.")
        if a.delimiter not in (",", ";"):
            notes.append("warning: the Xray importer offers only ',' or ';' as the CSV delimiter")
        if a.list_delimiter == a.delimiter:
            notes.append("note: list delimiter equals the CSV delimiter; multi-value cells are quoted, "
                         "set the same list delimiter in the importer's Setup step")
    elif a.format == "testrail" and size > TESTRAIL_MAX_BYTES:
        notes.append("warning: file is larger than 10 MB, TestRail's CSV upload limit. Split the export.")
    elif a.format == "azure-devops":
        if size > ADO_MAX_BYTES:
            notes.append("warning: file is larger than 20 MB, the Azure DevOps import limit. Split the export.")
        if not a.area_path:
            notes.append("warning: Area Path is empty. Azure DevOps Services lists it among the nine required "
                         "columns; pass --area-path (the project name is always a valid root area).")
        elif "/" in a.area_path:
            notes.append(f"warning: Area Path '{a.area_path}' contains '/'; Azure DevOps area paths use '\\' "
                         "(e.g. MyProject\\Web)")
        if not a.assigned_to:
            notes.append("note: Assigned To is empty. If the import wizard reports empty required fields, "
                         "re-export with --assigned-to <user e-mail>.")
        cut = [t["id"] for t in tests if len(f"{t['id']} {t['title']}") > ADO_TITLE_MAX]
        if cut:
            notes.append(f"note: titles cut to {ADO_TITLE_MAX} characters (Azure DevOps limit): {', '.join(cut)}")
    return notes


# ------------------------------------------------------------------ main
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tests", required=True)
    ap.add_argument("--requirements")
    ap.add_argument("--format", required=True, choices=["xray", "zephyr", "testrail", "azure-devops", "qase", "csv", "xlsx", "markdown"])
    ap.add_argument("--out", required=True)
    ap.add_argument("--delimiter", default=",")
    ap.add_argument("--list-delimiter", help="separator for multi-value cells (labels, keys); default ';' for xray, "
                                             "',' for zephyr")
    ap.add_argument("--bom", action="store_true", help="write UTF-8 BOM (Excel); default on for --format csv")
    ap.add_argument("--priority-map", help="JSON mapping of QA priorities to tool priority names")
    ap.add_argument("--test-type", default="Manual", help="Xray Test Type value")
    ap.add_argument("--component", help="Xray component value")
    ap.add_argument("--xray-links", choices=["cell", "columns"], default="cell",
                    help="requirement keys in one list cell (Xray Cloud) or one column per key (Xray Server/DC)")
    ap.add_argument("--folder", help="folder/section/suite path, 'A/B' or 'A > B' (xray, zephyr, testrail, qase)")
    ap.add_argument("--zephyr-steps", choices=["rows", "single"], default="rows")
    ap.add_argument("--zephyr-data", choices=["column", "inline"], default="column",
                    help="step data in its own Test Data column, or appended to the Step cell as [data]")
    ap.add_argument("--area-path", help="Azure DevOps Area Path (must already exist)")
    ap.add_argument("--assigned-to", help="Azure DevOps Assigned To (a valid user)")
    ap.add_argument("--include-deprecated", action="store_true")
    ap.add_argument("--only", help="comma-separated test IDs")
    ap.add_argument("--tag", help="export only tests with this tag")
    ap.add_argument("--lang", choices=["en", "tr"])
    sys.stdout.reconfigure(encoding="utf-8")
    a = ap.parse_args()
    if a.list_delimiter is None:
        a.list_delimiter = LIST_DELIMITER.get(a.format, ";")
    try:
        tc = json.loads(Path(a.tests).read_text(encoding="utf-8-sig"))
        rq = json.loads(Path(a.requirements).read_text(encoding="utf-8-sig")) if a.requirements else {}
        pmap = dict(DEFAULT_PRIORITY, **(json.loads(a.priority_map) if a.priority_map else {}))
    except (OSError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    tests = tc["test_cases"] if isinstance(tc, dict) else tc
    reqs = rq.get("requirements", []) if isinstance(rq, dict) else rq
    ext_map = {r["id"]: r.get("external_id") for r in reqs if r.get("id")}
    lang = a.lang or (tc.get("language") if isinstance(tc, dict) else None) or "en"
    h = H[lang if lang in H else "en"]
    project = tc.get("project", "") if isinstance(tc, dict) else ""

    if not a.include_deprecated:
        tests = [t for t in tests if t.get("status") != "deprecated"]
    if a.only:
        wanted = {x.strip() for x in a.only.split(",")}
        tests = [t for t in tests if t.get("id") in wanted]
    if a.tag:
        tests = [t for t in tests if a.tag in t.get("tags", [])]
    errs = validate(tests)
    if errs:
        print("validation failed, nothing written:", file=sys.stderr)
        for e in errs:
            print(f"  {e}", file=sys.stderr)
        return 1
    if not tests:
        print("no tests selected, nothing written", file=sys.stderr)
        return 1

    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    missing: set = set()
    if a.format == "xray":
        text, missing = export_xray(tests, ext_map, pmap, a, h)
    elif a.format == "zephyr":
        text, missing = export_zephyr(tests, ext_map, pmap, a, h)
    elif a.format == "testrail":
        text = csv_text(export_testrail(tests, ext_map, a, h), a.delimiter)
    elif a.format == "azure-devops":
        text = csv_text(export_ado(tests, ext_map, a, h), a.delimiter)
    elif a.format == "qase":
        text = csv_text(export_qase(tests, ext_map, a, h), a.delimiter)
    elif a.format == "csv":
        text = csv_text(export_generic(tests, ext_map, a, h), a.delimiter)
        a.bom = True
    elif a.format == "markdown":
        text = export_markdown(tests, ext_map, h, project)
    else:
        export_xlsx(tests, ext_map, h, out, project)
        text = None
    if text is not None:
        out.write_text(text, encoding="utf-8-sig" if a.bom else "utf-8", newline="")
    steps = sum(len(t["steps"]) for t in tests)
    print(f"wrote {out} ({a.format}): {len(tests)} tests, {steps} steps")
    if reqs:
        unknown = sorted({r for t in tests for r in t.get("requirement_ids", []) if r not in ext_map})
        if unknown:
            print(f"warning: tests reference requirements missing from requirements.json: {', '.join(unknown)}")
        orphans = [t["id"] for t in tests if not t.get("requirement_ids")]
        if orphans:
            print(f"warning: tests without requirement links: {', '.join(orphans)}")
    if a.format in ("xray", "zephyr"):
        if not a.requirements:
            print("note: --requirements not given; requirement links use internal REQ IDs only (labels/description)")
        elif missing:
            print(f"note: no external_id (Jira key) for {', '.join(sorted(missing))}; those links are kept as labels only")
    for msg in import_notes(a, tests, ext_map, text):
        print(msg)
    return 0


if __name__ == "__main__":
    sys.exit(main())
