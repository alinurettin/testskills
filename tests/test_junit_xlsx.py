"""Tests for the framework-neutral JUnit converter (shared/scripts/junit_results.py, synced into
tracing-requirements and testing-mobile-apps) and the .xlsx import of reviewing-test-cases/import_tests.py.

Run:  python -m unittest discover -s tests -v
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIX = Path(__file__).resolve().parent / "fixtures"
JFIX = FIX / "junit"
JUNIT = ROOT / "skills" / "tracing-requirements" / "scripts" / "junit_results.py"
RTM = ROOT / "skills" / "tracing-requirements" / "scripts" / "build_rtm.py"
IMPORT = ROOT / "skills" / "reviewing-test-cases" / "scripts" / "import_tests.py"
EXPORT = ROOT / "skills" / "exporting-test-cases" / "scripts" / "export_tests.py"
COMPACT = ROOT / "skills" / "reviewing-test-cases" / "scripts" / "qa_compact.py"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


jr = load(JUNIT, "junit_results_neutral")
imp = load(IMPORT, "import_tests_xlsx")
qc = load(COMPACT, "qa_compact_xlsx")


def run(*args):
    return subprocess.run([sys.executable, *map(str, args)], capture_output=True, text=True, encoding="utf-8")


def convert(d, *inputs, extra=(), out_name="results.json"):
    out = Path(d) / out_name
    r = run(JUNIT, *inputs, "--out", out, *extra)
    return r, (json.loads(out.read_text(encoding="utf-8"))["results"] if out.exists() else None)


# fixture -> (expected status per TC, number of untagged tests)
EXPECTED = {
    "surefire-junit5": ({"TC-101": "passed", "TC-102": "failed", "TC-103": "passed", "TC-104": "skipped",
                         "TC-105": "failed", "TC-106": "passed", "TC-107": "passed"}, 1),
    "surefire-testng": ({"TC-151": "passed", "TC-152": "failed", "TC-153": "skipped", "TC-154": "passed",
                         "TC-155": "passed"}, 0),
    "gradle": ({"TC-201": "passed", "TC-202": "passed", "TC-203": "failed", "TC-204": "failed",
                "TC-205": "skipped"}, 0),
    "pytest/junit.xml": ({"TC-301": "passed", "TC-302": "failed", "TC-303": "passed", "TC-304": "failed",
                          "TC-305": "skipped", "TC-306": "failed"}, 1),
    "cypress/results-*.xml": ({"TC-401": "passed", "TC-402": "failed", "TC-403": "skipped", "TC-404": "passed"}, 1),
    "newman/newman-shop-api.xml": ({"TC-501": "passed", "TC-502": "failed", "TC-503": "passed"}, 1),
    "karate/coupons.coupons.xml": ({"TC-601": "passed", "TC-602": "failed", "TC-603": "passed"}, 0),
    "robot/xunit.xml": ({"TC-701": "passed", "TC-702": "failed", "TC-703": "skipped", "TC-704": "passed"}, 0),
    "robot/output.xml": ({"TC-751": "passed", "TC-752": "failed", "TC-753": "skipped"}, 1),
    "dotnet/Shop.Tests.net8.0.junit.xml": ({"TC-801": "passed", "TC-802": "failed", "TC-803": "passed",
                                            "TC-804": "skipped"}, 1),
    "generic/nested-properties.xml": ({"TC-901": "passed", "TC-902": "passed", "TC-903": "passed", "TC-904": "passed",
                                       "TC-905": "failed", "TC-906": "failed", "TC-907": "passed", "TC-908": "passed",
                                       "TC-909": "passed"}, 1),
}


class JUnitFixtureTests(unittest.TestCase):
    def test_every_fixture_maps_to_the_expected_statuses(self):
        for name, (expected, untagged) in EXPECTED.items():
            with self.subTest(fixture=name), tempfile.TemporaryDirectory() as d:
                r, res = convert(d, str(JFIX / name), extra=("--source", "ci"))
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertEqual({k: v["status"] for k, v in res.items()}, expected)
                for tid, entry in res.items():
                    self.assertEqual(entry["source"], "ci")
                    self.assertEqual(entry["projects"], {"default": entry["projects"]["default"]})
                    self.assertIsInstance(entry["duration_ms"], int)
                    if entry["status"] == "failed":
                        self.assertTrue(entry.get("errors") or entry.get("note"), tid)
                if untagged:
                    self.assertIn(f"warning: {untagged} tests carry no TC-###", r.stdout)
                else:
                    self.assertNotIn("carry no TC-###", r.stdout)

    def test_suite_properties_are_not_ids(self):
        with tempfile.TemporaryDirectory() as d:
            _, res = convert(d, JFIX / "surefire-junit5", JFIX / "generic")
            self.assertNotIn("TC-900", res)   # /home/ci/builds/TC-900-shop in Surefire's system properties
            self.assertNotIn("TC-999", res)   # a testsuite <property>

    def test_surefire_reruns_errors_and_skips(self):
        with tempfile.TemporaryDirectory() as d:
            _, res = convert(d, JFIX / "surefire-junit5")
            self.assertTrue(res["TC-103"]["flaky"])                       # <flakyFailure> only
            self.assertEqual(res["TC-103"]["projects"]["default"], "flaky")
            self.assertNotIn("flaky", res["TC-102"])                       # <rerunFailure> stays failed
            self.assertEqual(res["TC-102"]["errors"], ["expected: <Hatalı şifre> but was: <>"])
            self.assertEqual(res["TC-105"]["errors"], ["Connection to localhost:5432 refused."])
            self.assertEqual(res["TC-104"]["note"], "Locked-account fixture not available on staging")

    def test_repeated_tests_are_runs_unless_retries(self):
        with tempfile.TemporaryDirectory() as d:
            _, res = convert(d, JFIX / "gradle")
            self.assertEqual(res["TC-204"]["status"], "failed")
            self.assertEqual(res["TC-204"]["duration_ms"], 1209)           # both attempts
            _, res = convert(d, JFIX / "gradle", extra=("--retries",), out_name="retries.json")
            self.assertEqual((res["TC-204"]["status"], res["TC-204"].get("flaky")), ("passed", True))
            self.assertEqual(res["TC-203"]["status"], "failed")            # different names: not retries
            _, res = convert(d, JFIX / "surefire-testng", extra=("--retries",), out_name="testng.json")
            self.assertEqual(res["TC-152"]["status"], "passed")            # why data providers need the default
            _, res = convert(d, JFIX / "surefire-testng", out_name="testng2.json")
            self.assertEqual(res["TC-152"]["errors"], ["expected [90.0] but found [100.0]"])

    def test_pytest_xfail_is_a_known_defect(self):
        with tempfile.TemporaryDirectory() as d:
            _, res = convert(d, JFIX / "pytest" / "junit.xml")
            self.assertEqual(res["TC-304"]["status"], "failed")
            self.assertIn("known product defect", res["TC-304"]["note"])
            self.assertEqual(res["TC-304"]["projects"]["default"], "known-defect")
            self.assertEqual(res["TC-305"]["note"], "audit service not deployed on staging")
            self.assertTrue(res["TC-306"]["errors"][0].startswith("failed on setup"))

    def test_directory_skips_other_xml_and_explicit_other_xml_fails(self):
        with tempfile.TemporaryDirectory() as d:
            r, res = convert(d, JFIX / "surefire-testng")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("skipped (not JUnit XML): testng-results.xml", r.stdout)
            r, _ = convert(d, JFIX / "surefire-testng" / "testng-results.xml", out_name="x.json")
            self.assertEqual(r.returncode, 2)
            self.assertIn("TestNG's own report", r.stderr)
            self.assertFalse((Path(d) / "x.json").exists())

    def test_glob_without_match_and_malformed_report(self):
        with tempfile.TemporaryDirectory() as d:
            r, _ = convert(d, str(JFIX / "cypress" / "nothing-*.xml"))
            self.assertEqual(r.returncode, 2)
            self.assertIn("no report matches", r.stderr)
            bad = Path(d) / "truncated.xml"
            bad.write_text('<testsuite name="x"><testcase name="TC-001 a"', encoding="utf-8")
            r, _ = convert(d, JFIX / "karate", bad)       # one good, one broken: nothing is written
            self.assertEqual(r.returncode, 2)
            self.assertFalse((Path(d) / "results.json").exists())
            out = Path(d) / "broken.json"
            out.write_text("{not json", encoding="utf-8")
            self.assertEqual(run(JUNIT, JFIX / "karate", "--out", out).returncode, 2)

    def test_control_characters_are_stripped(self):
        esc = chr(27)
        xml = ('<?xml version="1.0" encoding="UTF-8"?><testsuite name="jest">'
               f'<testcase name="TC-011 colours" time="0.5"><failure message="{esc}[31mexpected 2{esc}[39m">'
               f'{esc}[2mstack{esc}[22m &#x1B;[0m</failure></testcase></testsuite>')
        with tempfile.TemporaryDirectory() as d:
            rep = Path(d) / "jest.xml"
            rep.write_bytes(xml.encode("utf-8"))
            r, res = convert(d, rep)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("not allowed in XML", r.stdout)
            self.assertEqual(res["TC-011"]["status"], "failed")
            self.assertEqual(res["TC-011"]["errors"], ["expected 2"])  # colour codes removed before parsing

    def test_projects_accumulate_and_manual_entries_survive(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "results.json"
            out.write_text(json.dumps({"run": "RC1", "results": {
                "TC-050": {"status": "passed"}, "TC-402": {"status": "failed", "defects": ["SHOP-77"]}}}),
                encoding="utf-8")
            pattern = str(JFIX / "cypress" / "results-*.xml")
            self.assertEqual(run(JUNIT, pattern, "--project", "chrome", "--source", "cypress", "--out", out).returncode, 0)
            firefox = Path(d) / "firefox"
            firefox.mkdir()
            for f in (JFIX / "cypress").glob("results-*.xml"):
                text = f.read_text(encoding="utf-8")
                if "TC-402" in text:  # passes on Firefox; TC-401 fails there
                    text = text.replace('<failure message="Timed out', '<x message="Timed out').replace("</failure>", "</x>")
                    text = text.replace('classname="TC-401 accepts valid credentials">',
                                        'classname="TC-401 accepts valid credentials"><failure message="boom"/>')
                (firefox / f.name).write_text(text, encoding="utf-8")
            r = run(JUNIT, firefox, "--device", "firefox", "--source", "cypress", "--out", out, "--run", "RC2")
            self.assertEqual(r.returncode, 0, r.stderr)
            doc = json.loads(out.read_text(encoding="utf-8"))
            res = doc["results"]
            self.assertEqual(doc["run"], "RC2")
            self.assertEqual(res["TC-050"], {"status": "passed"})
            self.assertEqual(res["TC-402"]["projects"], {"chrome": "failed", "firefox": "passed"})
            self.assertEqual(res["TC-402"]["status"], "failed")
            self.assertEqual(res["TC-402"]["defects"], ["SHOP-77"])
            self.assertEqual(res["TC-401"]["projects"], {"chrome": "passed", "firefox": "failed"})
            self.assertEqual(res["TC-404"]["status"], "passed")
            # another source replaces the per-project history instead of mixing with it
            run(JUNIT, JFIX / "cypress" / "results-8b1d4e77.xml", "--source", "other", "--out", out)
            self.assertEqual(json.loads(out.read_text(encoding="utf-8"))["results"]["TC-404"]["projects"],
                             {"default": "passed"})

    def test_id_patterns(self):
        cases = {
            "TC-101 Valid login": ["TC-101"], "tc101_validLogin": ["TC-101"], "test_TC_102_x": ["TC-102"],
            "loginTC103": ["TC-103"], "CouponsTc501ApplyAValidCoupon": ["TC-501"], "TC803GuestCanPay": ["TC-803"],
            "[1:7] TC-601 apply": ["TC-601"], "com.example.TC155PaymentTest": ["TC-155"],
            "test_boundaries[TC-302-99.99]": ["TC-302"], "TC-908 and TC-909": ["TC-908", "TC-909"],
            "UTC-2024 rollover": [], "etc100 items": [], "TC-12 too short": [], "ABCTC-100": [], "TC-0042": ["TC-0042"],
        }
        for text, ids in cases.items():
            with self.subTest(text=text):
                self.assertEqual(jr.tc_ids(text), ids)

    def test_time_parsing(self):
        self.assertEqual(jr.parse_time("0,25"), 0.25)
        self.assertEqual(jr.parse_time("1,234.5"), 1234.5)
        self.assertEqual(jr.parse_time(""), 0.0)
        self.assertEqual(jr.parse_time("NaN"), 0.0)
        self.assertEqual(jr.parse_time("-1"), 0.0)
        status = jr.ET.fromstring('<status status="PASS" starttime="20260928 10:15:02.100" endtime="20260928 10:15:03.350"/>')
        self.assertAlmostEqual(jr.robot_seconds(status), 1.25)             # Robot Framework 6 and older

    def test_chain_to_rtm(self):
        xml = """<testsuites><testsuite name="coupon">
  <testcase name="TC-001 boundary 100.00" classname="CouponTest" time="0.1"/>
  <testcase name="TC-002 boundary 99.99" classname="CouponTest" time="0.1"><failure message="discount applied"/></testcase>
  <testcase name="TC-003 expired" classname="CouponTest" time="0.1"/>
</testsuite></testsuites>"""
        with tempfile.TemporaryDirectory() as d:
            rep, out = Path(d) / "junit.xml", Path(d) / "results.json"
            rep.write_text(xml, encoding="utf-8")
            self.assertEqual(run(JUNIT, rep, "--out", out).returncode, 0)
            r = run(RTM, "--requirements", FIX / "coupon" / "requirements.json", "--tests", FIX / "coupon" / "test-cases.json",
                    "--results", out, "--out-dir", d, "--json")
            self.assertIn(r.returncode, (0, 1), r.stderr)
            rtm = json.loads((Path(d) / "rtm.json").read_text(encoding="utf-8"))
            rows = {row["id"]: row for row in rtm["rows"]}
            self.assertEqual(rows["REQ-001"]["execution"], "failed")          # TC-002 failed
            self.assertEqual(rows["REQ-002"]["execution"], "passed")          # TC-003 passed
            self.assertIn(("REQ-001", "FAILED"), {(g["id"], g["code"]) for g in rtm["gaps"]})
            self.assertFalse([w for w in rtm["warnings"] if "unknown test" in w])


# ------------------------------------------------------------------ xlsx
def _si(text: str) -> str:
    return f'<si><t xml:space="preserve">{text}</t></si>'


def build_messy_xlsx(path: Path):
    """A hand-made workbook the way people keep test cases in Excel: a summary sheet first, a banner and
    an author line above a Turkish upper-case header, IDs/titles/priority merged down over the step rows,
    a blank row, Alt+Enter line breaks, rich text, a date and a percentage stored as numbers, a row
    without cell references, a hidden sheet and a second visible test sheet."""
    strings = ["Kupon Modülü – Test Senaryoları", "Hazırlayan: Test Ekibi", "TEST NO", "SENARYO ADI", "ÖN KOŞUL",
               "ADIM NO", "ADIMLAR", "TEST VERİSİ", "BEKLENEN SONUÇ", "ÖNCELİK", "GEREKSİNİM",
               "K-01", "Geçerli kupon uygulanır", "Kullanıcı giriş yapmış\nSepet 150,00 TL", "Sepete git",
               "Sepet sayfası açılır", "Yüksek", "SHOP-42", "Kupon alanına kodu yaz", "Kod alana yazılır",
               "Uygula'ya tıkla", "İndirim -15,00 TL_x000D_\nToplam 135,00 TL",
               "K-02", None, "Süresi dolmuş kupon kodunu gir ve uygula", "'Kuponun süresi dolmuş' hata mesajı",
               "Orta", "SHOP-43", "K-03", "Minimum sepet tutarı", "Sepete 99,99 TL ürün ekle", "Düşük",
               "Toplam test", "Tarih"]
    sst = []
    for s in strings:
        if s is None:  # rich text with a phonetic run that must not leak into the value
            sst.append('<si><r><rPr><b/></rPr><t xml:space="preserve">Süresi dolmuş </t></r>'
                       '<r><t>kupon reddedilir</t></r><rPh sb="0" eb="1"><t>XX</t></rPh></si>')
        else:
            sst.append(_si(s.replace("&", "&amp;").replace("<", "&lt;")))
    ix = {s: i for i, s in enumerate(strings) if s is not None}

    def s(ref, text):
        return f'<c r="{ref}" t="s"><v>{ix[text]}</v></c>'

    def n(ref, value, style=0):
        return f'<c r="{ref}" s="{style}"><v>{value}</v></c>'

    def inline(ref, text):
        return f'<c r="{ref}" t="inlineStr"><is><t>{text}</t></is></c>'

    rows = [
        f'<row r="1">{s("A1", "Kupon Modülü – Test Senaryoları")}</row>',
        f'<row r="2">{s("A2", "Hazırlayan: Test Ekibi")}</row>',
        '<row r="4">' + "".join(s(f"{c}4", h) for c, h in zip("ABCDEFGHIJ", [
            "TEST NO", "SENARYO ADI", "ÖN KOŞUL", "ADIM NO", "ADIMLAR", "TEST VERİSİ", "BEKLENEN SONUÇ", "ÖNCELİK",
            "GEREKSİNİM", "Tarih"])) + "</row>",
        f'<row r="5">{s("A5", "K-01")}{s("B5", "Geçerli kupon uygulanır")}'
        f'{s("C5", "Kullanıcı giriş yapmış" + chr(10) + "Sepet 150,00 TL")}{n("D5", 1)}{s("E5", "Sepete git")}'
        f'{s("G5", "Sepet sayfası açılır")}{s("H5", "Yüksek")}{s("I5", "SHOP-42")}{n("J5", 46023, 1)}</row>',
        f'<row r="6">{n("D6", 2)}{s("E6", "Kupon alanına kodu yaz")}{inline("F6", "YAZ10")}'
        f'{s("G6", "Kod alana yazılır")}</row>',
        f'<row r="7"><c r="A7" s="0"/>{n("D7", 3)}{s("E7", "Uygula&apos;ya tıkla".replace("&apos;", chr(39)))}'
        f'{s("G7", "İndirim -15,00 TL_x000D_" + chr(10) + "Toplam 135,00 TL")}</row>',
        f'<row r="9">{s("A9", "K-02")}<c r="B9" t="s"><v>{strings.index(None)}</v></c>{n("D9", 1)}'
        f'{s("E9", "Süresi dolmuş kupon kodunu gir ve uygula")}{n("F9", 45930, 3)}'
        f'{s("G9", chr(39) + "Kuponun süresi dolmuş" + chr(39) + " hata mesajı")}{s("H9", "Orta")}{s("I9", "SHOP-43")}</row>',
        f'<row r="10">{s("A10", "K-03")}{s("B10", "Minimum sepet tutarı")}{n("D10", 1)}'
        f'{s("E10", "Sepete 99,99 TL ürün ekle")}{n("F10", "99.989999999999995")}{s("H10", "Düşük")}</row>',
        # no r attributes: row 11 follows row 10, cells are positional from column A
        '<row><c/><c/><c/><c><v>2</v></c><c t="inlineStr"><is><t>Kuponu uygula</t></is></c>'
        '<c s="2"><v>0.1</v></c><c t="inlineStr"><is><t>Kupon uygulanmaz</t></is></c></row>',
        f'<row r="13">{inline("A13", "Toplam: 3 test")}</row>',              # footer, not a test
    ]
    merges = ["A1:J1", "A5:A7", "B5:B7", "C5:C7", "H5:H7", "I5:I7"]
    sheet2 = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
              '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>'
              + "".join(rows) + f'</sheetData><mergeCells count="{len(merges)}">'
              + "".join(f'<mergeCell ref="{m}"/>' for m in merges) + "</mergeCells></worksheet>")
    sheet1 = ('<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>'
              f'<row r="1">{s("A1", "Toplam test")}{n("B1", 3)}</row></sheetData></worksheet>')
    simple = ('<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>'
              '<row r="1">' + "".join(inline(f"{c}1", h) for c, h in zip("ABCDE", ["ID", "Title", "Steps", "Expected Result", "Priority"]))
              + '</row><row r="2">' + inline("A2", "{id}") + inline("B2", "{title}")
              + inline("C2", "1. Open the payment page\n2. Pay by card") + inline("D2", "1. Page opens\n2. Paid")
              + inline("E2", "High") + "</row></sheetData></worksheet>")
    sheet3 = simple.replace("{id}", "OLD-1").replace("{title}", "Old hidden test")
    sheet4 = simple.replace("{id}", "PAY-1").replace("{title}", "Card payment succeeds")
    styles = ('<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
              '<numFmts count="1"><numFmt numFmtId="164" formatCode="dd\\.mm\\.yyyy;@"/></numFmts>'
              '<cellXfs count="4"><xf numFmtId="0"/><xf numFmtId="14" applyNumberFormat="1"/>'
              '<xf numFmtId="9" applyNumberFormat="1"/><xf numFmtId="164" applyNumberFormat="1"/></cellXfs></styleSheet>')
    rel = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
    wb = ('<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
          f'xmlns:r="{rel}"><workbookPr/><sheets>'
          '<sheet name="Özet" sheetId="1" r:id="rId1"/><sheet name="Test Senaryoları" sheetId="2" r:id="rId2"/>'
          '<sheet name="Eski" sheetId="3" state="hidden" r:id="rId3"/><sheet name="Ödeme" sheetId="4" r:id="rId4"/>'
          '</sheets></workbook>')
    wb_rels = ('<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
               f'<Relationship Id="rId1" Type="{rel}/worksheet" Target="worksheets/sheet1.xml"/>'
               f'<Relationship Id="rId2" Type="{rel}/worksheet" Target="/xl/worksheets/sheet2.xml"/>'
               f'<Relationship Id="rId3" Type="{rel}/worksheet" Target="worksheets/sheet3.xml"/>'
               f'<Relationship Id="rId4" Type="{rel}/worksheet" Target="worksheets/sheet4.xml"/>'
               f'<Relationship Id="rId5" Type="{rel}/sharedStrings" Target="sharedStrings.xml"/>'
               f'<Relationship Id="rId6" Type="{rel}/styles" Target="styles.xml"/></Relationships>')
    root_rels = ('<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                 f'<Relationship Id="rId1" Type="{rel}/officeDocument" Target="xl/workbook.xml"/></Relationships>')
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("_rels/.rels", root_rels)
        z.writestr("xl/workbook.xml", wb)
        z.writestr("xl/_rels/workbook.xml.rels", wb_rels)
        z.writestr("xl/sharedStrings.xml", '<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
                   + "".join(sst) + "</sst>")
        z.writestr("xl/styles.xml", styles)
        for i, sh in enumerate([sheet1, sheet2, sheet3, sheet4], 1):
            z.writestr(f"xl/worksheets/sheet{i}.xml", sh)


class XlsxImportTests(unittest.TestCase):
    def import_and_parse(self, src: Path, d: str, *extra, name="t.src.md"):
        out = Path(d) / name
        r = run(IMPORT, src, "--out", out, *extra)
        self.assertEqual(r.returncode, 0, r.stderr)
        _, items, errors = qc.parse(out.read_text(encoding="utf-8"), "tc")
        self.assertEqual(errors, [])
        self.assertEqual(qc.validate(items, "tc", lenient=True), [])
        return r, items

    def test_export_xlsx_round_trips(self):
        original = json.loads((FIX / "coupon" / "test-cases.json").read_text(encoding="utf-8"))["test_cases"]
        for lang in ("en", "tr"):
            with self.subTest(lang=lang), tempfile.TemporaryDirectory() as d:
                xlsx = Path(d) / "tc.xlsx"
                r = run(EXPORT, "--tests", FIX / "coupon" / "test-cases.json", "--format", "xlsx", "--lang", lang,
                        "--out", xlsx)
                self.assertEqual(r.returncode, 0, r.stderr)
                r, items = self.import_and_parse(xlsx, d, "--lang", lang)
                self.assertIn("IDs kept", (Path(d) / "t.src.md").read_text(encoding="utf-8"))
                self.assertIn("row per step", r.stdout)
                got = {t["id"]: t for t in items}
                exported = [t for t in original if t["id"] in got]
                self.assertGreaterEqual(len(exported), 6)
                self.assertEqual(len(got), len(exported))
                for t in exported:
                    g = got[t["id"]]
                    self.assertEqual(g["requirement_ids"], t["requirement_ids"] or ["UNLINKED"], t["id"])
                    for field in ("title", "priority", "polarity", "technique", "status"):
                        self.assertEqual(g.get(field), t.get(field), f"{t['id']} {field}")
                    self.assertEqual(g.get("preconditions", []), t.get("preconditions", []), t["id"])
                    self.assertEqual(g.get("test_data", {}), {k: str(v) for k, v in (t.get("test_data") or {}).items()})
                    self.assertEqual([(s["action"], s.get("data", ""), s["expected"]) for s in g["steps"]],
                                     [(s["action"], str(s.get("data", "")), s["expected"]) for s in t["steps"]], t["id"])
                    self.assertEqual(set(g["tags"]) - {"imported"}, set(t.get("tags", [])), t["id"])
                    self.assertEqual(g["automation"]["candidate"], bool((t.get("automation") or {}).get("candidate")))

    def test_messy_turkish_workbook(self):
        with tempfile.TemporaryDirectory() as d:
            xlsx = Path(d) / "kupon testleri.xlsx"
            build_messy_xlsx(xlsx)
            r = run(IMPORT, xlsx, "--list-sheets")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("1. Özet · 1 rows · no title/steps header found", r.stdout)
            self.assertIn("2. Test Senaryoları · 10 rows · header row 4", r.stdout)
            self.assertIn("3. Eski (hidden)", r.stdout)
            r, items = self.import_and_parse(xlsx, d)              # default: first visible sheet with a header
            self.assertIn("sheet 'Test Senaryoları', header row 4, row per step", r.stdout)
            self.assertIn("steps without expected 1", r.stdout)
            self.assertEqual([t["id"] for t in items], ["TC-001", "TC-002", "TC-003"])
            k1, k2, k3 = items
            self.assertEqual((k1["title"], k1["priority"], k1["requirement_ids"]),
                             ("Geçerli kupon uygulanır", "high", ["SHOP-42"]))
            self.assertEqual(k1["preconditions"], ["Kullanıcı giriş yapmış", "Sepet 150,00 TL"])
            self.assertEqual([(s["action"], s.get("data", ""), s["expected"]) for s in k1["steps"]], [
                ("Sepete git", "", "Sepet sayfası açılır"),
                ("Kupon alanına kodu yaz", "YAZ10", "Kod alana yazılır"),
                ("Uygula'ya tıkla", "", "İndirim -15,00 TL; Toplam 135,00 TL")])
            self.assertIn("src-K-01", k1["tags"])
            self.assertEqual((k2["title"], k2["priority"], k2["polarity"]), ("Süresi dolmuş kupon reddedilir", "medium", "negative"))
            self.assertEqual(k2["steps"][0]["data"], "2025-09-30")            # date serial -> ISO
            self.assertEqual((k3["priority"], k3["requirement_ids"]), ("low", ["UNLINKED"]))
            self.assertEqual([s.get("data") for s in k3["steps"]], ["99.99", "10%"])
            self.assertEqual(k3["steps"][1]["expected"], "Kupon uygulanmaz")  # row without cell references

            r, items = self.import_and_parse(xlsx, d, "--sheet", "all", name="all.src.md")
            self.assertEqual(len(items), 4)                                   # hidden sheet left out
            self.assertIn("Ödeme", items[3]["tags"])
            self.assertEqual([s["expected"] for s in items[3]["steps"]], ["Page opens", "Paid"])
            r, items = self.import_and_parse(xlsx, d, "--sheet", "4", "--lang", "en", name="4.src.md")
            self.assertEqual((len(items), items[0]["priority"]), (1, "high"))
            r, items = self.import_and_parse(xlsx, d, "--sheet", "eski", name="e.src.md")  # named sheets may be hidden
            self.assertEqual(items[0]["title"], "Old hidden test")
            self.assertEqual(run(IMPORT, xlsx, "--sheet", "Yok", "--out", Path(d) / "x.md").returncode, 2)
            self.assertEqual(run(IMPORT, xlsx, "--sheet", "Özet", "--out", Path(d) / "x.md").returncode, 2)

    def test_cell_formats(self):
        kind = imp._fmt_kind
        self.assertEqual([kind(14, None), kind(22, None), kind(20, None), kind(9, None), kind(0, None)],
                         ["date", "datetime", "time", "percent", ""])
        self.assertEqual(kind(164, "dd\\.mm\\.yyyy;@"), "date")
        self.assertEqual(kind(165, "[h]:mm:ss"), "time")
        self.assertEqual(kind(166, '#,##0.00 "TL"'), "")
        self.assertEqual(kind(167, "[$-41F]d mmmm yyyy dddd"), "date")
        self.assertEqual(kind(168, "0.0%"), "percent")
        self.assertEqual(imp._serial(46023, "date", False), "2026-01-01")
        self.assertEqual(imp._serial(46023.5, "datetime", False), "2026-01-01 12:00")
        self.assertEqual(imp._serial(0.75, "time", False), "18:00")
        self.assertEqual(imp._serial(44561, "date", True), "2026-01-01")       # 1904 date system
        self.assertEqual(imp._plain(0.1 + 0.2), "0.3")
        self.assertEqual(imp._plain(12.0), "12")

    def test_legacy_and_fake_excel_files_are_refused(self):
        with tempfile.TemporaryDirectory() as d:
            ole = Path(d) / "old.xls"
            ole.write_bytes(bytes.fromhex("d0cf11e0a1b11ae1") + b"\0" * 512)
            r = run(IMPORT, ole, "--out", Path(d) / "x.md")
            self.assertEqual(r.returncode, 2)
            self.assertIn("save as .xlsx", r.stderr)
            html = Path(d) / "export.xls"
            html.write_text("<html><table><tr><td>ID</td></tr></table></html>", encoding="utf-8")
            r = run(IMPORT, html, "--out", Path(d) / "x.md")
            self.assertEqual(r.returncode, 2)
            self.assertIn("HTML", r.stderr)

    def test_csv_with_title_rows_and_windows_1254(self):
        text = ("Kupon test seti\n\nTEST NO;BAŞLIK;ADIMLAR;BEKLENEN SONUÇ;ÖNCELİK\n"
                "1;Geçersiz kupon reddedilir;1. Kodu gir 2. Uygula;1. Kod yazılır 2. Hata mesajı;Yüksek\n")
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / "suite.csv"
            src.write_bytes(text.encode("cp1254"))
            r, items = self.import_and_parse(src, d)
            self.assertIn("Windows-1254", r.stdout)
            self.assertIn("header row 3", r.stdout)
            self.assertEqual((items[0]["title"], items[0]["priority"], len(items[0]["steps"])),
                             ("Geçersiz kupon reddedilir", "high", 2))


if __name__ == "__main__":
    unittest.main()
