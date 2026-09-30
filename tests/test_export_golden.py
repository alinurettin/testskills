"""Golden-file and vendor-compatibility tests for skills/exporting-test-cases/scripts/export_tests.py.

1. Golden files: tests/fixtures/exports/golden/<tool>.csv hold the exporter's output for
   tests/fixtures/coupon. Any change to that output fails here, so a format change is always deliberate.
   To accept an intended change, regenerate the goldens and the import kit, then review the diff:

       QA_UPDATE_GOLDEN=1 python -m unittest tests.test_export_golden     (PowerShell: $env:QA_UPDATE_GOLDEN=1)
       python tests/test_export_golden.py --update                       (same, without unittest)

2. Vendor hook: when tests/fixtures/exports/vendor/<tool>/ holds a CSV that was exported from the real
   tool after importing examples/import-kit/<tool>.csv, the column names and value vocabularies of the
   current export are checked against it. Without such a file the test is skipped. Known, deliberate value
   translations made in the import wizard go in vendor/<tool>/accepted.json, e.g. {"Priority": {"Highest": "High"}}.
   See docs/IMPORT-VERIFICATION.md.

3. The import kit (examples/import-kit) must match the current exporter (python examples/import-kit/make_kit.py).
"""
from __future__ import annotations

import csv
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXPORT = ROOT / "skills" / "exporting-test-cases" / "scripts" / "export_tests.py"
COUPON = ROOT / "tests" / "fixtures" / "coupon"
GOLDEN = ROOT / "tests" / "fixtures" / "exports" / "golden"
VENDOR = ROOT / "tests" / "fixtures" / "exports" / "vendor"
KIT = ROOT / "examples" / "import-kit"
UPDATE = os.environ.get("QA_UPDATE_GOLDEN") == "1"

# tool -> exporter arguments used for the golden file (tool == vendor folder name)
CASES = {
    "xray": ["--format", "xray", "--folder", "QA Suite/Kupon"],
    "zephyr": ["--format", "zephyr", "--folder", "QA Suite/Kupon"],
    "testrail": ["--format", "testrail", "--folder", "QA Suite > Kupon"],
    "azure-devops": ["--format", "azure-devops", "--area-path", "QASuiteKit"],
    "qase": ["--format", "qase", "--folder", "QA Suite/Kupon"],
}

# Vendor re-export compatibility. "required": our column -> names it may have in the tool's own CSV export
# (checked when our export has that column). "vocab": our column -> vendor column names whose values must
# cover every value we write (checked when the vendor file has that column and values).
VENDOR_SPEC = {
    "xray": {  # Jira issue search -> Export -> CSV (all fields)
        "required": {"Summary": ["Summary"], "Priority": ["Priority"], "Labels": ["Labels"],
                     "Description": ["Description"]},
        "vocab": {"Priority": ["Priority"],
                  "Test Type": ["Test Type", "Test type", "Custom field (Test Type)"]},
    },
    "zephyr": {
        "required": {"Name": ["Name"], "Objective": ["Objective"], "Precondition": ["Precondition"],
                     "Folder": ["Folder"], "Status": ["Status"], "Priority": ["Priority"], "Labels": ["Labels"],
                     "Coverage": ["Coverage (Issues)", "Coverage"],
                     "Test Script (Step-by-Step) - Step": ["Test Script (Step-by-Step) - Step",
                                                           "Test Script (Steps) - Step"],
                     "Test Script (Step-by-Step) - Expected Result": ["Test Script (Step-by-Step) - Expected Result",
                                                                      "Test Script (Steps) - Expected Result"]},
        "vocab": {"Status": ["Status"], "Priority": ["Priority"]},
    },
    "testrail": {
        "required": {"Title": ["Title"], "Section": ["Section", "Section Hierarchy"], "Priority": ["Priority"],
                     "Type": ["Type"], "Preconditions": ["Preconditions"],
                     "Step": ["Steps (Step)", "Steps", "Step"],
                     "Expected Result": ["Steps (Expected Result)", "Expected Result"],
                     "References": ["References"]},
        "vocab": {"Priority": ["Priority"], "Type": ["Type"]},
    },
    "azure-devops": {  # the nine required import columns must be spelled exactly as in the tool's export
        "required": {c: [c] for c in ("ID", "Work Item Type", "Title", "Test Step", "Step Action", "Step Expected",
                                      "Area Path", "Assigned To", "State")},
        "vocab": {"Work Item Type": ["Work Item Type"], "State": ["State"], "Priority": ["Priority"]},
    },
    "qase": {  # V2: every header must exist with the same spelling
        "required": {c: [c] for c in ("v2.id", "title", "description", "preconditions", "postconditions", "tags",
                                      "priority", "severity", "type", "behavior", "automation", "status", "is_flaky",
                                      "layer", "steps_type", "steps_actions", "steps_result", "steps_data",
                                      "milestone_id", "milestone", "suite_id", "suite_parent_id", "suite",
                                      "suite_without_cases", "parameters")},
        "vocab": {c: [c] for c in ("priority", "severity", "type", "behavior", "automation", "status", "is_flaky",
                                   "layer", "steps_type")},
    },
}


# ------------------------------------------------------------------ helpers
def run_export(args: list[str], out: Path, tests: Path = COUPON / "test-cases.json",
               reqs: Path | None = COUPON / "requirements.json") -> subprocess.CompletedProcess:
    cmd = [sys.executable, str(EXPORT), "--tests", str(tests), "--out", str(out)] + list(args)
    if reqs:
        cmd += ["--requirements", str(reqs)]
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")


def parse(text: str, delimiter: str = ",") -> list[list[str]]:
    """CSV rows with line breaks normalised: .gitattributes (eol=lf) may rewrite CRLF in checked-in files."""
    rows = list(csv.reader(io.StringIO(text.lstrip("﻿").replace("\r\n", "\n")), delimiter=delimiter))
    return [[c.replace("\r\n", "\n") for c in r] for r in rows]


def read_vendor(path: Path) -> list[list[str]]:
    raw = path.read_bytes()
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:  # Excel/Windows "CSV" export
        text = raw.decode("cp1252")
    first = text.split("\n", 1)[0]
    delimiter = max((",", ";", "\t"), key=first.count)
    return parse(text, delimiter)


def vendor_problems(tool: str, ours: list[list[str]], vendor_rows: list[list[str]], accepted: dict,
                    name: str = "vendor file") -> list[str]:
    """Differences between our export and the tool's own export of the imported cases."""
    spec, problems = VENDOR_SPEC[tool], []
    vhead = [h.strip() for h in vendor_rows[0]] if vendor_rows else []
    for col, names in spec["required"].items():
        if col in ours[0] and not any(n in vhead for n in names):
            problems.append(f"{name}: no column {' / '.join(repr(n) for n in names)} for our column {col!r}")
    for col, names in spec["vocab"].items():
        if col not in ours[0]:
            continue
        idx = [i for i, h in enumerate(vhead) if h in names]
        vendor_vals = {r[i].strip() for r in vendor_rows[1:] for i in idx if i < len(r) and r[i].strip()}
        if not vendor_vals:
            continue
        oi = ours[0].index(col)
        our_vals = {r[oi].strip() for r in ours[1:] if oi < len(r) and r[oi].strip()}
        allowed = set(accepted.get(col, {}))
        unknown = sorted(v for v in our_vals if v not in vendor_vals and v not in allowed)
        if unknown:
            problems.append(f"{name}: {col} values {unknown} not among the tool's values {sorted(vendor_vals)} "
                            f"(change the exporter default or record the wizard mapping in accepted.json)")
    return problems


def load_make_kit():
    spec = importlib.util.spec_from_file_location("make_kit", KIT / "make_kit.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def regenerate() -> list[str]:
    GOLDEN.mkdir(parents=True, exist_ok=True)
    written = []
    for tool, args in CASES.items():
        r = run_export(args, GOLDEN / f"{tool}.csv")
        if r.returncode != 0:
            raise RuntimeError(f"{tool}: {r.stderr}")
        written.append(f"golden/{tool}.csv")
    mk = load_make_kit()
    for name, text in mk.build().items():
        (KIT / name).write_text(text, encoding="utf-8", newline="" if name.endswith(".csv") else "\n")
        written.append(f"import-kit/{name}")
    return written


def first_difference(a: list[list[str]], b: list[list[str]]) -> str:
    for i in range(max(len(a), len(b))):
        ra = a[i] if i < len(a) else None
        rb = b[i] if i < len(b) else None
        if ra != rb:
            if ra is None or rb is None:
                return f"row {i + 1}: golden={ra!r} now={rb!r}"
            for j in range(max(len(ra), len(rb))):
                ca = ra[j] if j < len(ra) else "<missing>"
                cb = rb[j] if j < len(rb) else "<missing>"
                if ca != cb:
                    col = a[0][j] if j < len(a[0]) else f"#{j + 1}"
                    return f"row {i + 1}, column {col!r}: golden={ca!r} now={cb!r}"
    return "no difference"


HOW_TO_UPDATE = ("If the change is intended, regenerate and review the diff: QA_UPDATE_GOLDEN=1 python -m unittest "
                 "tests.test_export_golden (or: python tests/test_export_golden.py --update).")


# ------------------------------------------------------------------ tests
class GoldenExportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if UPDATE:
            print("\nregenerated: " + ", ".join(regenerate()), file=sys.stderr)
        cls.tmp = tempfile.TemporaryDirectory()
        cls.fresh = {}
        for tool, args in CASES.items():
            out = Path(cls.tmp.name) / f"{tool}.csv"
            r = run_export(args, out)
            if r.returncode != 0:
                raise AssertionError(f"{tool} export failed: {r.stderr}")
            cls.fresh[tool] = out.read_bytes()

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_output_matches_golden(self):
        for tool in CASES:
            with self.subTest(tool=tool):
                golden = GOLDEN / f"{tool}.csv"
                self.assertTrue(golden.exists(), f"missing {golden}. {HOW_TO_UPDATE}")
                want = parse(golden.read_text(encoding="utf-8"))
                now = parse(self.fresh[tool].decode("utf-8"))
                self.assertTrue(want == now, f"{tool} export changed: {first_difference(want, now)}. {HOW_TO_UPDATE}")

    def test_encoding_is_plain_utf8_with_turkish_text(self):
        for tool, data in self.fresh.items():
            with self.subTest(tool=tool):
                self.assertFalse(data.startswith(b"\xef\xbb\xbf"), "importer files are written without BOM")
                self.assertIn("ı", data.decode("utf-8"))

    def test_every_step_survives_in_every_format(self):
        mk = load_make_kit()
        tc = json.loads((COUPON / "test-cases.json").read_text(encoding="utf-8"))
        want = {t["id"]: len(t["steps"]) for t in tc["test_cases"] if t.get("status") != "deprecated"}
        for tool, args in CASES.items():
            with self.subTest(tool=tool):
                got = {s["id"]: s["steps"] for s in mk.summarize(args[1], parse(self.fresh[tool].decode("utf-8")))}
                self.assertEqual(got, want)

    def test_vendor_reexport_compatibility(self):
        found = False
        for tool in CASES:
            folder = VENDOR / tool
            files = sorted(folder.glob("*.csv")) if folder.is_dir() else []
            if not files:
                continue
            found = True
            accepted_file = folder / "accepted.json"
            accepted = json.loads(accepted_file.read_text(encoding="utf-8")) if accepted_file.exists() else {}
            ours = parse(self.fresh[tool].decode("utf-8"))
            for f in files:
                with self.subTest(tool=tool, file=f.name):
                    problems = vendor_problems(tool, ours, read_vendor(f), accepted, f"{tool}/{f.name}")
                    self.assertEqual(problems, [], "\n".join(problems))
        if not found:
            self.skipTest(f"no vendor re-export under {VENDOR.relative_to(ROOT).as_posix()}/<tool>/*.csv "
                          "(see docs/IMPORT-VERIFICATION.md)")


class VendorHookSelfTests(unittest.TestCase):
    """The vendor check runs only after a real import, so its logic is tested here on synthetic files."""

    def export_rows(self, tool: str) -> list[list[str]]:
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "x.csv"
            self.assertEqual(run_export(CASES[tool], out).returncode, 0)
            return parse(out.read_text(encoding="utf-8"))

    def test_identical_export_passes(self):
        for tool in ("qase", "azure-devops"):
            ours = self.export_rows(tool)
            self.assertEqual(vendor_problems(tool, ours, ours, {}), [])

    def test_renamed_vendor_columns_are_accepted(self):
        ours = self.export_rows("zephyr")
        vendor = [list(r) for r in ours]
        vendor[0] = [{"Coverage": "Coverage (Issues)"}.get(h, h.replace("(Step-by-Step)", "(Steps)")) for h in ours[0]]
        vendor[0].insert(0, "Key")
        for r in vendor[1:]:
            r.insert(0, "KIT-T1")
        self.assertEqual(vendor_problems("zephyr", ours, vendor, {}), [])

    def test_missing_column_and_unknown_value_are_reported(self):
        ours = self.export_rows("qase")
        pi = ours[0].index("priority")
        vendor = [list(r) for r in ours]
        vendor[0] = ["sev" if h == "severity" else h for h in vendor[0]]
        for r in vendor[1:]:
            if r[pi]:
                r[pi] = "P1"
        problems = vendor_problems("qase", ours, vendor, {})
        self.assertTrue(any("'severity'" in p for p in problems), problems)
        self.assertTrue(any("priority values" in p for p in problems), problems)
        # a wizard mapping recorded in accepted.json silences the value difference
        accepted = {"priority": {"high": "P1", "medium": "P1", "low": "P1"}}
        self.assertFalse(any("priority values" in p for p in vendor_problems("qase", ours, vendor, accepted)))

    def test_semicolon_cp1252_vendor_file_is_read(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "export.csv"
            p.write_bytes("Title;Section;Priority\r\nA é;S;High\r\n".encode("cp1252"))
            rows = read_vendor(p)
            self.assertEqual(rows[0], ["Title", "Section", "Priority"])
            self.assertEqual(rows[1][0], "A é")


class ImportKitTests(unittest.TestCase):
    def test_kit_matches_current_exporter(self):
        mk = load_make_kit()
        for name, text in mk.build().items():
            with self.subTest(file=name):
                path = KIT / name
                self.assertTrue(path.exists(), f"missing {path}; run python examples/import-kit/make_kit.py")
                self.assertEqual(path.read_text(encoding="utf-8").replace("\r\n", "\n"), text.replace("\r\n", "\n"),
                                 f"{name} is stale; run python examples/import-kit/make_kit.py")

    def test_kit_links_use_kit_project_keys(self):
        text = (KIT / "xray.csv").read_text(encoding="utf-8")
        self.assertIn("KIT-1", text)
        self.assertNotIn("SHOP-", text)


class FormatDetailTests(unittest.TestCase):
    """Vendor-documented details (2026-09-30) that the goldens alone would not explain."""

    def export(self, *args, only="TC-001,TC-003"):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "x.csv"
            r = run_export(list(args) + ["--only", only], out)
            self.assertEqual(r.returncode, 0, r.stderr)
            return parse(out.read_text(encoding="utf-8")), r.stdout

    def test_xray_test_type_on_every_row_and_repository_folder(self):
        rows, _ = self.export("--format", "xray", "--folder", "A > B")
        h = rows[0]
        self.assertEqual([r[h.index("Test Type")] for r in rows[1:]], ["Manual"] * 3)
        self.assertEqual(h[-1], "Test Repository Folder")
        self.assertEqual(rows[1][-1], "A/B")

    def test_xray_server_dc_one_column_per_requirement(self):
        tc = {"test_cases": [{"id": "TC-001", "title": "x", "requirement_ids": ["REQ-001", "REQ-002"],
                              "steps": [{"action": "a", "expected": "b"}]}]}
        rq = {"requirements": [{"id": "REQ-001", "external_id": "KIT-1"}, {"id": "REQ-002", "external_id": "KIT-2"}]}
        with tempfile.TemporaryDirectory() as d:
            t, q, out = Path(d) / "t.json", Path(d) / "r.json", Path(d) / "x.csv"
            t.write_text(json.dumps(tc), encoding="utf-8")
            q.write_text(json.dumps(rq), encoding="utf-8")
            r = run_export(["--format", "xray", "--xray-links", "columns"], out, tests=t, reqs=q)
            self.assertEqual(r.returncode, 0, r.stderr)
            rows = parse(out.read_text(encoding="utf-8"))
        h = rows[0]
        self.assertEqual(rows[1][h.index("Requirement Key 1")], "KIT-1")
        self.assertEqual(rows[1][h.index("Requirement Key 2")], "KIT-2")

    def test_zephyr_labels_comma_and_inline_data(self):
        rows, _ = self.export("--format", "zephyr", "--zephyr-data", "inline", only="TC-001")
        h = rows[0]
        self.assertNotIn("Test Script (Step-by-Step) - Test Data", h)
        self.assertIn("[Ürün A x1]", rows[1][h.index("Test Script (Step-by-Step) - Step")])
        self.assertIn("regression,smoke", rows[1][h.index("Labels")])

    def test_qase_nested_suites_and_escaped_line_breaks(self):
        tc = {"test_cases": [{"id": "TC-001", "title": "x", "steps": [
            {"action": "line 1\nline 2", "expected": 'say "hi"'}, {"action": "b", "expected": "c"}]}]}
        with tempfile.TemporaryDirectory() as d:
            t, out = Path(d) / "t.json", Path(d) / "q.csv"
            t.write_text(json.dumps(tc), encoding="utf-8")
            r = run_export(["--format", "qase", "--folder", "Top/Child"], out, tests=t, reqs=None)
            self.assertEqual(r.returncode, 0, r.stderr)
            rows = parse(out.read_text(encoding="utf-8"))
        h = rows[0]
        col = lambda r, c: r[h.index(c)]  # noqa: E731
        self.assertEqual([(col(r, "suite_id"), col(r, "suite_parent_id"), col(r, "suite")) for r in rows[1:3]],
                         [("1", "", "Top"), ("2", "1", "Child")])
        case = rows[3]
        self.assertEqual((col(case, "suite_id"), col(case, "suite_parent_id")), ("2", "1"))
        self.assertEqual(col(case, "steps_actions"), '1. "line 1\\nline 2"\n2. "b"')
        self.assertEqual(col(case, "steps_result").splitlines()[0], "1. \"say 'hi'\"")

    def test_ado_test_data_kept_and_notes(self):
        rows, out = self.export("--format", "azure-devops", "--area-path", "Shop/Web", only="TC-001")
        self.assertIn("Test verisi: sepet: 100,00 TL; kupon: YAZ10", rows[1][4])
        self.assertIn("use '\\'", out)
        self.assertIn("Assigned To is empty", out)


if __name__ == "__main__":
    if "--update" in sys.argv:
        sys.stdout.reconfigure(encoding="utf-8")
        print("regenerated:\n  " + "\n  ".join(regenerate()))
        sys.exit(0)
    unittest.main()
