"""Regression tests for the QA Suite scripts (standard library only).

Run:  python -m unittest discover -s tests -v
"""
from __future__ import annotations

import csv
import re
import shutil
from collections import Counter
import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import unittest
import xml.dom.minidom
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SK = ROOT / "skills"
FIX = Path(__file__).resolve().parent / "fixtures" / "coupon"
SPECS = SK / "designing-test-cases" / "assets" / "spec-examples"
EXPORT = SK / "exporting-test-cases" / "scripts" / "export_tests.py"


def load(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


lint = load(SK / "analyzing-requirements" / "scripts" / "lint_requirements.py")
ep = load(SK / "designing-test-cases" / "scripts" / "ep_bva.py")
dt = load(SK / "designing-test-cases" / "scripts" / "decision_table.py")
st = load(SK / "designing-test-cases" / "scripts" / "state_transition.py")
pw = load(SK / "designing-test-cases" / "scripts" / "pairwise.py")
rtm = load(SK / "tracing-requirements" / "scripts" / "build_rtm.py")
COMPACT = SK / "designing-test-cases" / "scripts" / "qa_compact.py"
qc = load(COMPACT)


def spec(name: str) -> dict:
    return json.loads((SPECS / name).read_text(encoding="utf-8"))


def rules_of(res, rid):
    return {f["rule"] for r in res["results"] if r["id"] == rid for f in r["findings"]}


class LintTests(unittest.TestCase):
    def setUp(self):
        self.res = lint.run([
            {"id": "R1", "text": "Sistem kupon kodunu hızlı bir şekilde doğrulamalı ve kullanım sayısını kaydetmelidir."},
            {"id": "R9", "text": "Süresi dolmuş kupon reddedilmeli ve 'Kuponun süresi doldu' mesajı gösterilmelidir."},
            {"id": "R10", "text": "Sistem kupon kodunu büyük/küçük harfe duyarsız eşleştirmelidir."},
            {"id": "R11", "text": "Aynı kuponla eşzamanlı iki sipariş isteğinde yalnızca biri kabul edilmelidir."},
            {"id": "R2", "text": "İndirim oranı belirlenecek."},
            {"id": "R3", "text": "Ödeme kredi kartı, havale vb. ile yapılabilmelidir."},
            {"id": "R4", "text": "The API shall respond within 300 ms at p95 under 200 concurrent users."},
            {"id": "R5", "text": "It should be user-friendly where possible."},
            {"id": "R6", "text": "Kayıtlı kullanıcı olarak kupon girmek istiyorum, böylece indirim alırım."},
            {"id": "R7", "text": "Süreç yönetimi ekranı yüksek çözünürlükte açılmalıdır."},
            {"id": "R8", "text": "Sepet sayfasının yanıt süresi kabul edilebilir düzeyde olmalıdır."},
        ], None)

    def test_turkish_vague_and_compound(self):
        self.assertTrue({"VAGUE", "COMPOUND"} <= rules_of(self.res, "R1"))

    def test_tbd_is_critical(self):
        self.assertIn("TBD", rules_of(self.res, "R2"))

    def test_open_ended_list(self):
        self.assertIn("OPEN_ENDED", rules_of(self.res, "R3"))

    def test_measurable_requirement_is_clean(self):
        self.assertEqual(rules_of(self.res, "R4"), set())

    def test_english_loophole_vague_pronoun(self):
        self.assertTrue({"VAGUE", "LOOPHOLE", "PRONOUN"} <= rules_of(self.res, "R5"))

    def test_story_without_ac(self):
        self.assertIn("STORY_NO_AC", rules_of(self.res, "R6"))

    def test_no_false_positive_on_surec_yuksek(self):
        self.assertNotIn("UNMEASURED", rules_of(self.res, "R7"))
        self.assertNotIn("VAGUE", rules_of(self.res, "R7"))

    def test_unmeasured_and_vague_performance(self):
        self.assertTrue({"UNMEASURED", "VAGUE"} <= rules_of(self.res, "R8"))

    def test_turkish_false_positives_suppressed(self):
        # "süresi dolmuş" is expiry, not a duration; "reddet + mesaj göster" is one response
        self.assertEqual(rules_of(self.res, "R9") - {"UNIVERSAL"}, set())
        # "büyük/küçük harf" is letter case, not a vague size
        self.assertNotIn("VAGUE", rules_of(self.res, "R10"))
        # concurrency rule, not a performance statement
        self.assertNotIn("UNMEASURED", rules_of(self.res, "R11"))

    def test_id_without_colon(self):
        reqs, _ = lint.load_text("- FR-1 The applicant must be between 18 and 65 years old.\n- NFR-2: shall be secure")
        self.assertEqual([r["id"] for r in reqs], ["FR-1", "NFR-2"])

    def test_duplicate_ids(self):
        res = lint.run([{"id": "X-1", "text": "A shall do B."}, {"id": "X-1", "text": "C shall do D."}], "en")
        self.assertIn("ID_DUPLICATE", rules_of(res, "X-1"))


class EpBvaTests(unittest.TestCase):
    def bounds(self, params, bva="2-value"):
        res = ep.run({"bva": bva, "parameters": params}, "en")
        return [b["value"] for b in res["parameters"][0]["boundaries"]]

    def test_integer_3value(self):
        self.assertEqual(self.bounds([{"name": "age", "type": "integer", "min": 18, "max": 65}], "3-value"),
                         ["16", "17", "18", "19", "64", "65", "66", "67"])

    def test_integer_2value(self):
        self.assertEqual(self.bounds([{"name": "age", "type": "integer", "min": 18, "max": 65}]), ["17", "18", "65", "66"])

    def test_decimal_step(self):
        self.assertEqual(self.bounds([{"name": "a", "type": "decimal", "step": "0.01", "min": "100", "max": "200"}]),
                         ["99.99", "100.00", "200.00", "200.01"])

    def test_date(self):
        self.assertIn("2026-03-01", self.bounds([{"name": "d", "type": "date", "min": "2026-02-01", "max": "2026-02-28"}]))

    def test_gap_detected_and_tested(self):
        res = ep.run(spec("ep-bva.json"), "tr")
        self.assertTrue(any("700..700" in w for w in res["warnings"]))
        self.assertTrue(any(c["values"]["kredi_notu"] == "700" for c in res["conditions"]))

    def test_invalid_values_never_combined(self):
        res = ep.run(spec("ep-bva.json"), "en")
        valid = {po["name"]: {q["representative"] for q in po["partitions"] if q["valid"] is True}
                 | {b["value"] for b in po["boundaries"] if b["valid"] is True} for po in res["parameters"]}
        for c in res["conditions"]:
            non_valid = [n for n, v in c["values"].items() if v not in valid[n]]
            self.assertLessEqual(len(non_valid), 1, c)

    def test_every_partition_and_boundary_is_used(self):
        res = ep.run(spec("ep-bva.json"), "en")
        for po in res["parameters"]:
            used = {c["values"][po["name"]] for c in res["conditions"]}
            wanted = {q["representative"] for q in po["partitions"]} | {b["value"] for b in po["boundaries"]}
            self.assertEqual(wanted - used, set(), po["name"])

    def test_length_has_no_negative_partition(self):
        res = ep.run({"parameters": [{"name": "u", "type": "length", "min": 0, "max": 5}]}, "en")
        self.assertFalse(any(q["label"].startswith("<") for q in res["parameters"][0]["partitions"]))


class DecisionTableTests(unittest.TestCase):
    def setUp(self):
        self.res = dt.run(spec("decision-table.json"), "collapsed", "en")

    def test_gap_and_conflict(self):
        self.assertEqual(self.res["summary"]["gaps"], 1)
        self.assertEqual(self.res["gaps"][0]["values"], {"registered": "N", "basket_total": ">=100", "coupon": "valid"})
        self.assertEqual(self.res["summary"]["conflicts"], 1)

    def test_collapsed_tests_cover_all_ok_combinations(self):
        covered = {c for t in self.res["test_conditions"] for c in t["covers"]}
        ok = {r["id"] for r in self.res["full_table"] if r["status"] == "ok"}
        self.assertEqual(covered, ok)

    def test_full_coverage_mode(self):
        self.assertEqual(dt.run(spec("decision-table.json"), "full", "en")["summary"]["test_conditions"], 10)

    def test_unknown_value_rejected(self):
        with self.assertRaises(ValueError):
            dt.run({"conditions": [{"name": "a", "values": ["Y", "N"]}],
                    "rules": [{"id": "R", "when": {"a": "X"}, "then": {}}]}, "collapsed", "en")


class StateTransitionTests(unittest.TestCase):
    def test_zero_switch_covers_all_reachable(self):
        res = st.run(spec("state-transition.json"), 0, 15)
        covered = {t for s in res["sequences"] for t in s["transitions"]}
        self.assertEqual(covered, {"T1", "T2", "T3", "T4", "T5", "T6"})
        self.assertEqual(res["uncoverable"], [["T7"]])
        self.assertTrue(any(f["type"] == "unreach" for f in res["findings"]))

    def test_sequences_are_valid_paths(self):
        s = spec("state-transition.json")
        for seq in st.run(s, 1, 15)["sequences"]:
            cur = s["initial"]
            for step in seq["steps"]:
                self.assertEqual(step["from"], cur)
                cur = step["to"]

    def test_nondeterminism(self):
        res = st.run({"initial": "A", "transitions": [{"from": "A", "event": "e", "to": "B"},
                                                      {"from": "A", "event": "e", "to": "C"}]}, 0, 10)
        self.assertTrue(any(f["type"] == "nondet" for f in res["findings"]))


class PairwiseTests(unittest.TestCase):
    def test_all_pairs_covered_with_constraints(self):
        res = pw.generate(spec("pairwise.json"), 30, 42)
        self.assertTrue(res["verification"]["all_tuples_covered"])
        self.assertTrue(res["verification"]["all_rows_valid"])
        self.assertLess(res["summary"]["tests"], res["summary"]["exhaustive"])
        for t in res["tests"]:
            self.assertFalse(t["values"]["os"] == "Windows" and t["values"]["browser"] == "Safari")

    def test_deterministic(self):
        self.assertEqual(pw.generate(spec("pairwise.json"), 30, 42)["tests"],
                         pw.generate(spec("pairwise.json"), 30, 42)["tests"])

    def test_three_wise(self):
        res = pw.generate({"strength": 3, "parameters": [{"name": n, "values": ["a", "b"]} for n in "wxyz"]}, 30, 1)
        self.assertTrue(res["verification"]["all_tuples_covered"])


class RtmTests(unittest.TestCase):
    def setUp(self):
        self.rq = json.loads((FIX / "requirements.json").read_text(encoding="utf-8"))["requirements"]
        self.tc = json.loads((FIX / "test-cases.json").read_text(encoding="utf-8"))["test_cases"]
        self.rs = json.loads((FIX / "results.json").read_text(encoding="utf-8"))["results"]

    def test_validation_finds_broken_link(self):
        errors, _ = rtm.validate(self.rq, self.tc, self.rs)
        self.assertTrue(any("REQ-099" in e for e in errors))

    def test_gaps_metrics_impact(self):
        rep = rtm.build(self.rq, self.tc, self.rs, ["REQ-001"])
        codes = {(g["id"], g["code"]) for g in rep["gaps"]}
        for expected in [("REQ-004", "UNCOVERED"), ("REQ-005", "THIN"), ("REQ-003", "NO_NEGATIVE"),
                         ("REQ-003", "UNCONFIRMED"), ("REQ-001", "FAILED")]:
            self.assertIn(expected, codes)
        self.assertNotIn(("REQ-006", "UNCOVERED"), codes)  # deferred is out of scope
        self.assertEqual(rep["orphans"], ["TC-007"])
        self.assertEqual(rep["duplicates"], [["TC-001", "TC-008"]])
        self.assertEqual(rep["metrics"]["coverage_pct"], 80.0)
        self.assertEqual(rep["impact"][0]["tests"], ["TC-001", "TC-002", "TC-008"])
        self.assertEqual(rep["gaps"][0]["id"], "REQ-005")  # highest risk first


class CalibrationTests(unittest.TestCase):
    @staticmethod
    def tc(i, pri, req="REQ-001", tech="equivalence-partitioning", exp="İndirim 50,00 TL; toplam 450,00 TL"):
        return {"id": f"TC-{i:03d}", "title": f"t{i}", "requirement_ids": [req], "priority": pri,
                "polarity": "positive", "technique": tech, "steps": [{"action": "a", "expected": exp}]}

    def test_priority_skew_detected(self):
        tests = [self.tc(i, "critical" if i < 4 else "medium", req=f"REQ-{i:03d}") for i in range(10)]
        codes = [c["code"] for c in rtm.calibration(tests)]
        self.assertIn("PRIORITY_SKEW", codes)

    def test_balanced_suite_has_no_skew(self):
        pris = ["critical", "high", "high", "medium", "medium", "medium", "medium", "low", "low", "high"]
        tests = [self.tc(i, p, req=f"REQ-{i:03d}") for i, p in enumerate(pris)]
        self.assertEqual(rtm.calibration(tests), [])

    def test_redundant_same_class_detected_numbers_masked(self):
        tests = [self.tc(1, "medium", exp="İndirim 50,00 TL; toplam 450,01 TL"),
                 self.tc(2, "medium", exp="İndirim 50,00 TL; toplam 950,00 TL"),
                 self.tc(3, "medium", exp="İndirim 50,00 TL; toplam 99.949,99 TL")]
        red = [c for c in rtm.calibration(tests) if c["code"] == "REDUNDANT"]
        self.assertEqual(red[0]["tests"], ["TC-001", "TC-002", "TC-003"])

    def test_pairwise_rows_not_redundant(self):
        tests = [self.tc(i, "medium", tech="pairwise") for i in range(6)]
        self.assertEqual([c for c in rtm.calibration(tests) if c["code"] == "REDUNDANT"], [])

    def test_bva_needs_larger_group(self):
        tests = [self.tc(i, "medium", tech="boundary-value-analysis") for i in range(4)]
        self.assertEqual([c for c in rtm.calibration(tests) if c["code"] == "REDUNDANT"], [])


class CompactFormatTests(unittest.TestCase):
    SRC = """project: Demo
language: tr
setup giris: Kullanıcı giriş yapmış
setup giris: 'YAZ10' aktif

## TC-001 | Kupon sınırda uygulanır
req: REQ-001, REQ-002 | pri: h | pol: + | tech: bva | ref: DS-001 C-02
pre: @giris
pre: Sepet 100,00 TL
data: sepet=100,00 TL; kupon=YAZ10
1. Kodu yaz, 'Uygula'ya tıkla [" YAZ10 "] => 'Kupon uygulandı'; toplam 90,00 TL
2. Özeti kontrol et => İndirim -10,00 TL
tags: smoke, regression | auto: yes, veri güdümlü | status: ready
"""

    def test_parse_expand_and_quote(self):
        header, items, errors = qc.parse(self.SRC, "tc")
        self.assertEqual(errors, [])
        t = items[0]
        self.assertEqual(t["preconditions"], ["Kullanıcı giriş yapmış", "'YAZ10' aktif", "Sepet 100,00 TL"])
        self.assertEqual(t["steps"][0]["data"], " YAZ10 ")
        self.assertEqual(t["steps"][0]["expected"], "'Kupon uygulandı'; toplam 90,00 TL")
        self.assertEqual((t["priority"], t["polarity"], t["technique"]), ("high", "positive", "boundary-value-analysis"))
        self.assertEqual(t["automation"], {"candidate": True, "reason": "veri güdümlü"})

    def test_validation_errors(self):
        _, items, errors = qc.parse("## TC-001 | x\nreq: REQ-1 | pri: urgent | pol: + | tech: bva\npre: @nope\n", "tc")
        errors += qc.validate(items, "tc")
        joined = " ".join(errors)
        self.assertIn("unknown priority", joined)
        self.assertIn("unknown setup block", joined)
        self.assertIn("no steps", joined)

    def test_cli_merge_keeps_ids_and_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            src, out = Path(d) / "tc.src.md", Path(d) / "tc.json"
            existing = {"test_cases": [{"id": "TC-000", "title": "eski", "requirement_ids": ["REQ-9"], "priority": "low",
                                        "polarity": "positive", "technique": "checklist",
                                        "steps": [{"action": "a", "expected": "b"}]}]}
            out.write_text(json.dumps(existing), encoding="utf-8")
            src.write_text(self.SRC, encoding="utf-8")
            r = subprocess.run([sys.executable, str(COMPACT), "tc", str(src), "--out", str(out), "--merge"],
                               capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(r.returncode, 0, r.stderr)
            data = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual([t["id"] for t in data["test_cases"]], ["TC-000", "TC-001"])
            back = Path(d) / "back.src.md"
            subprocess.run([sys.executable, str(COMPACT), "tc", str(out), "--to-compact", "--out", str(back)], check=True)
            again = Path(d) / "again.json"
            subprocess.run([sys.executable, str(COMPACT), "tc", str(back), "--out", str(again)], check=True,
                           capture_output=True)
            for t in data["test_cases"]:
                t.setdefault("status", "draft")  # the converter normalises a missing status
            self.assertEqual(json.loads(again.read_text(encoding="utf-8"))["test_cases"], data["test_cases"])

    def test_requirements_kind(self):
        src = ("## REQ-001 | Kupon\ntype: business-rule | pri: c | risk: 2x5 Para kaybı | src: US-42 | ext: SHOP-42 | status: cn\n"
               "text: Kupon %10 indirim sağlar.\nac: Diyelim ki ...\nq: Q-001 | derived: no\n")
        _, items, errors = qc.parse(src, "req")
        errors += qc.validate(items, "req")
        self.assertEqual(errors, [])
        r = items[0]
        self.assertEqual(r["risk"], {"likelihood": 2, "impact": 5, "rationale": "Para kaybı"})
        self.assertEqual((r["priority"], r["status"], r["external_id"]), ("critical", "clarification-needed", "SHOP-42"))

    def test_scripts_are_in_sync(self):
        shared = (ROOT / "shared" / "scripts" / "qa_compact.py").read_bytes()
        for skill in ("analyzing-requirements", "designing-test-cases"):
            self.assertEqual((SK / skill / "scripts" / "qa_compact.py").read_bytes(), shared, skill)


PW = SK / "automating-with-playwright" / "scripts"
BDD = SK / "writing-bdd-scenarios" / "scripts"


def run_py(script: Path, *args) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(script), *map(str, args)], capture_output=True, text=True, encoding="utf-8")


def dd_suite(tmp: Path) -> Path:
    """Three BVA variants of one requirement (data-driven group) plus one ordinary test."""
    def t(i, amount, exp, tech="boundary-value-analysis"):
        return {"id": f"TC-{i:03d}", "title": f"Kupon {amount} TL sepette", "requirement_ids": ["REQ-001"],
                "priority": "high", "polarity": "positive", "technique": tech, "tags": ["regression"],
                "preconditions": ["Kullanıcı giriş yapmış", f"Sepet {amount} TL"],
                "steps": [{"action": f"{amount} TL sepette kuponu uygula", "data": "YAZ10", "expected": exp}],
                "automation": {"candidate": True, "reason": "x"}, "status": "ready"}
    tests = [t(1, "100,00", "İndirim -10,00 TL"), t(2, "500,00", "İndirim -50,00 TL"), t(3, "800,00", "İndirim -50,00 TL"),
             {**t(4, "99,99", "Kupon reddedilir", tech="decision-table"), "external_id": "SHOP-204", "category": "api",
              "steps": [{"action": "API ile kupon uygula", "expected": "422 döner"}]}]
    p = tmp / "tc.json"
    p.write_text(json.dumps({"project": "Demo", "language": "tr", "test_cases": tests}, ensure_ascii=False), encoding="utf-8")
    r = tmp / "req.json"
    r.write_text(json.dumps({"requirements": [{"id": "REQ-001", "title": "Kupon indirimi", "text": "Kupon %10 indirim sağlar.",
                                               "external_id": "SHOP-42"}]}, ensure_ascii=False), encoding="utf-8")
    return p


class PlaywrightScaffoldTests(unittest.TestCase):
    def test_scaffold_tokens_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            r = run_py(PW / "scaffold_project.py", "--dir", root / "automation", "--project", "Online Mağaza",
                       "--base-url", "https://test.example.com")
            self.assertEqual(r.returncode, 0, r.stderr)
            cfg = (root / "automation" / "playwright.config.ts").read_text(encoding="utf-8")
            self.assertIn("https://test.example.com", cfg)
            self.assertIn("'tr-TR'", cfg)
            self.assertNotIn("{{", cfg)
            pkg = json.loads((root / "automation" / "package.json").read_text(encoding="utf-8"))
            self.assertEqual(pkg["name"], "online-magaza-e2e")
            wf = (root / ".github" / "workflows" / "playwright.yml").read_text(encoding="utf-8")
            self.assertIn("working-directory: automation", wf)
            self.assertIn("${{ secrets.TEST_USER }}", wf)  # GitHub expressions must survive templating
            (root / "automation" / "playwright.config.ts").write_text("// mine", encoding="utf-8")
            r2 = run_py(PW / "scaffold_project.py", "--dir", root / "automation")
            self.assertIn("exists, kept", r2.stdout)
            self.assertEqual((root / "automation" / "playwright.config.ts").read_text(encoding="utf-8"), "// mine")


class GenerateSpecsTests(unittest.TestCase):
    def test_skeletons_tags_fixme_and_idempotency(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "tests"
            r = run_py(PW / "generate_specs.py", "--tests", FIX / "test-cases.json", "--requirements",
                       FIX / "requirements.json", "--out", out)
            self.assertEqual(r.returncode, 0, r.stderr)
            text = "\n".join(f.read_text(encoding="utf-8") for f in out.glob("*.spec.ts"))
            self.assertIn('"@TC-001"', text)
            self.assertIn('{ type: "requirements", description: "SHOP-101" }', text)
            self.assertIn("QA Suite skeleton TC-001", text)
            self.assertIn('import { test, expect } from "./fixtures";', text)
            self.assertNotIn("@TC-006", text)  # deprecated
            self.assertNotIn("@TC-007", text)  # not an automation candidate
            again = run_py(PW / "generate_specs.py", "--tests", FIX / "test-cases.json", "--out", out)
            self.assertIn("nothing new to generate", again.stdout)

    def test_data_driven_group_and_api_fixture(self):
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            tc = dd_suite(tmp)
            r = run_py(PW / "generate_specs.py", "--tests", tc, "--requirements", tmp / "req.json", "--out", tmp / "tests")
            self.assertEqual(r.returncode, 0, r.stderr)
            spec = next((tmp / "tests").glob("*.spec.ts")).read_text(encoding="utf-8")
            self.assertIn("const cases1 = [", spec)
            self.assertIn("data-driven: TC-001, TC-002, TC-003", spec)
            self.assertIn('pre: ["Sepet 800,00 TL"]', spec)
            self.assertIn("async ({ request })", spec)  # category api
            self.assertIn('{ type: "test_key", description: "SHOP-204" }', spec)


class CheckAutomationTests(unittest.TestCase):
    def test_skeleton_vs_automated_vs_missing(self):
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            tc = dd_suite(tmp)
            run_py(PW / "generate_specs.py", "--tests", tc, "--out", tmp / "tests", "--only", "TC-001,TC-002,TC-003")
            r = run_py(PW / "check_automation.py", "--tests", tc, "--specs", tmp / "tests")
            self.assertIn("candidates 4 · automated 0 (0.0%) · skeletons 3 · missing 1", r.stdout)
            spec = next((tmp / "tests").glob("*.spec.ts"))
            spec.write_text(re.sub(r".*QA Suite skeleton.*\n", "", spec.read_text(encoding="utf-8")), encoding="utf-8")
            r = run_py(PW / "check_automation.py", "--tests", tc, "--specs", tmp / "tests", "--strict")
            self.assertIn("automated 3 (75.0%) · skeletons 0 · missing 1", r.stdout)
            self.assertEqual(r.returncode, 1)  # TC-004 still missing


class PwResultsTests(unittest.TestCase):
    def test_aggregation_and_merge(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "results.json"
            out.write_text(json.dumps({"results": {"TC-001": {"status": "failed", "defects": ["SHOP-481"]},
                                                   "TC-099": {"status": "passed"}}}), encoding="utf-8")
            r = run_py(PW / "pw_results.py", FIX / "playwright-report.json", "--out", out, "--run", "demo")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("1 Playwright tests carry no TC-### tag", r.stdout)
            res = json.loads(out.read_text(encoding="utf-8"))["results"]
            self.assertEqual(res["TC-001"]["status"], "failed")  # failed in firefox
            self.assertEqual(res["TC-001"]["projects"], {"chromium": "passed", "firefox": "failed"})
            self.assertEqual(res["TC-001"]["defects"], ["SHOP-481"])  # manual defect link kept
            self.assertNotIn("\x1b", res["TC-001"]["errors"][0])  # ANSI colour codes stripped
            self.assertEqual((res["TC-002"]["status"], res["TC-002"].get("flaky")), ("passed", True))
            self.assertEqual(res["TC-003"]["status"], "not-run")
            # test.fail: Playwright says "expected", but the requirement is still not met
            self.assertEqual(res["TC-004"]["status"], "failed")
            self.assertIn("known product defect", res["TC-004"]["note"])
            # test.fail test that now passes: the defect looks fixed
            self.assertEqual(res["TC-005"]["status"], "passed")
            self.assertIn("remove test.fail", res["TC-005"]["note"])
            self.assertEqual(res["TC-099"]["status"], "passed")  # manual result preserved


class GenerateFeaturesTests(unittest.TestCase):
    def test_turkish_outline_per_tc_examples(self):
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            tc = dd_suite(tmp)
            r = run_py(BDD / "generate_features.py", "--tests", tc, "--requirements", tmp / "req.json", "--out", tmp / "f")
            self.assertEqual(r.returncode, 0, r.stderr)
            feat = next((tmp / "f").glob("*.feature")).read_text(encoding="utf-8")
            self.assertTrue(feat.startswith("# language: tr"))
            self.assertIn("Özellik: REQ-001 Kupon indirimi", feat)
            self.assertIn("Geçmiş:\n    Diyelim ki Kullanıcı giriş yapmış", feat)
            self.assertIn("Senaryo taslağı: <id> <title>", feat)
            self.assertEqual(feat.count("Örnekler:"), 3)
            for tid in ("@TC-001", "@TC-002", "@TC-003", "@TC-004"):
                self.assertIn(tid, feat)
            self.assertIn("Senaryo: TC-004", feat)
            self.assertIn('Eğer ki API ile kupon uygula\n    O zaman 422 döner', feat)
            again = run_py(BDD / "generate_features.py", "--tests", tc, "--out", tmp / "f")
            self.assertIn("nothing new to generate", again.stdout)

    def test_english_keywords(self):
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            tc = dd_suite(tmp)
            run_py(BDD / "generate_features.py", "--tests", tc, "--out", tmp / "f", "--lang", "en", "--only", "TC-004")
            feat = next((tmp / "f").glob("*.feature")).read_text(encoding="utf-8")
            self.assertFalse(feat.startswith("# language"))
            self.assertIn("Scenario: TC-004", feat)
            self.assertIn("When API ile kupon uygula", feat)


PLAN = SK / "planning-tests" / "scripts"
REP = SK / "reporting-test-results" / "scripts"
NFR = SK / "testing-nonfunctional" / "scripts"
REV = SK / "reviewing-test-cases" / "scripts"


def qa_dir(tmp: Path, results=True, defects=None, criteria=None) -> Path:
    """A qa/ folder built from the coupon fixture (8 tests, TC-006 deprecated)."""
    qa = tmp / "qa"
    (qa / "design").mkdir(parents=True)
    for f in ("requirements.json", "test-cases.json") + (("results.json",) if results else ()):
        (qa / f).write_text((FIX / f).read_text(encoding="utf-8"), encoding="utf-8")
    (qa / "clarifications.md").write_text(
        "| ID | Öncelik | REQ | Soru |\n|---|---|---|---|\n| Q-001 | bloke eden | REQ-003 | Harf duyarlılığı? |\n"
        "| Q-002 | önemli | REQ-001 | Kargo dahil mi? |\n", encoding="utf-8")
    (qa / "design" / "DS-004-compat.json").write_text((SPECS / "pairwise.json").read_text(encoding="utf-8"), encoding="utf-8")
    if defects is not None:
        (qa / "defects.json").write_text(json.dumps({"defects": defects}), encoding="utf-8")
    if criteria is not None:
        (qa / "exit-criteria.json").write_text(json.dumps(criteria), encoding="utf-8")
    return qa


class PlanFactsTests(unittest.TestCase):
    def test_facts_from_artifacts(self):
        with tempfile.TemporaryDirectory() as d:
            qa = qa_dir(Path(d))
            r = run_py(PLAN / "plan_facts.py", "--qa", qa, "--format", "json")
            self.assertEqual(r.returncode, 0, r.stderr)
            f = json.loads(r.stdout)
            self.assertEqual(f["tests"]["total"], 7)  # deprecated TC-006 excluded
            self.assertEqual(f["requirements"]["in_scope"], 5)
            self.assertEqual(f["questions"]["blocking"], 1)
            self.assertEqual(f["questions"]["blocking_ids"], ["Q-001"])
            self.assertEqual(f["environments"][0]["parameters"]["browser"], ["Chrome", "Firefox", "Safari", "Edge"])
            self.assertEqual(f["risk"]["top"][0]["id"], "REQ-005")
            self.assertGreater(f["effort_estimate"]["manual_hours_total"], f["effort_estimate"]["manual_hours_one_cycle"])


class CompletionReportTests(unittest.TestCase):
    CRIT = {"min_requirement_coverage_pct": 100, "min_execution_pct": 95, "min_pass_rate_pct": 50,
            "max_open_defects": {"critical": 0, "high": 0}, "all_critical_requirements_passed": True,
            "max_blocking_questions_open": 0}

    def test_metrics_and_criteria(self):
        with tempfile.TemporaryDirectory() as d:
            defects = [{"id": "SHOP-481", "severity": "high", "status": "open", "test_ids": ["TC-002"]},
                       {"id": "SHOP-400", "severity": "critical", "status": "closed"}]
            qa = qa_dir(Path(d), defects=defects, criteria=self.CRIT)
            r = run_py(REP / "completion_report.py", "--qa", qa, "--json")
            self.assertEqual(r.returncode, 1)
            f = json.loads(r.stdout)
            m = f["metrics"]
            self.assertEqual(m["coverage_pct"], 80.0)          # REQ-004 uncovered, REQ-006 deferred
            self.assertEqual((m["executed"], m["passed"], m["failed"]), (3, 2, 1))
            self.assertAlmostEqual(m["pass_rate_pct"], 66.7)
            self.assertEqual(m["open_defects_by_severity"], {"high": 1})  # closed critical not counted
            got = {e["criterion"]: e["met"] for e in f["exit_criteria"]}
            self.assertFalse(got["min_requirement_coverage_pct"])
            self.assertFalse(got["min_execution_pct"])
            self.assertTrue(got["min_pass_rate_pct"])
            self.assertTrue(got["max_open_defects.critical"])
            self.assertFalse(got["max_open_defects.high"])
            self.assertFalse(got["all_critical_requirements_passed"])  # REQ-005 critical, not run
            self.assertFalse(got["max_blocking_questions_open"])
            self.assertEqual(f["residual_risks"][0]["id"], "REQ-005")
            failed = [x for x in f["residual_risks"] if x["verdict"] == "failed"][0]
            self.assertEqual((failed["id"], failed["defects"]), ("REQ-001", ["SHOP-481"]))

    def test_unknown_severity_without_defect_register(self):
        with tempfile.TemporaryDirectory() as d:
            qa = qa_dir(Path(d), criteria={"max_open_defects": {"high": 0}})
            f = json.loads(run_py(REP / "completion_report.py", "--qa", qa, "--json").stdout)
            self.assertIsNone(f["exit_criteria"][0]["met"])  # never assume 0 when severity is unknown

    def test_markdown_turkish(self):
        with tempfile.TemporaryDirectory() as d:
            qa = qa_dir(Path(d), criteria=self.CRIT)
            out = qa / "completion-report.md"
            run_py(REP / "completion_report.py", "--qa", qa, "--out", out)
            text = out.read_text(encoding="utf-8")
            self.assertIn("# Test Tamamlama Raporu", text)
            self.assertIn("✘ karşılanmadı", text)
            self.assertIn("| Gereksinim kapsamı ≥ | 100 | 80.0 |", text)


class NfrChecklistTests(unittest.TestCase):
    def test_wcag_axe_plus_manual_and_valid_compact(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "a11y.src.md"
            r = run_py(NFR / "nfr_checklist.py", "wcag", "--features", "forms", "--page", "Sepet", "--req", "REQ-012",
                       "--tests", FIX / "test-cases.json", "--lang", "tr", "--out", out)
            self.assertEqual(r.returncode, 0, r.stderr)
            _, items, errors = qc.parse(out.read_text(encoding="utf-8"), "tc")
            self.assertEqual(errors + qc.validate(items, "tc"), [])
            self.assertEqual(items[0]["id"], "TC-009")  # continues after TC-008
            self.assertIn("axe", items[0]["title"])
            data = json.loads((SK / "testing-nonfunctional" / "assets" / "wcag22-aa.json").read_text(encoding="utf-8"))
            sel = [c for c in data["criteria"] if "forms" in c["features"] or "all" in c["features"]]
            self.assertEqual(len(items) - 1, sum(1 for c in sel if c["method"] != "auto"))
            self.assertTrue(all(t["category"] == "accessibility" for t in items))

    def test_wcag_data_complete(self):
        data = json.loads((SK / "testing-nonfunctional" / "assets" / "wcag22-aa.json").read_text(encoding="utf-8"))
        levels = Counter(c["level"] for c in data["criteria"])
        self.assertEqual((levels["A"], levels["AA"]), (31, 24))
        self.assertNotIn("4.1.1", {c["sc"] for c in data["criteria"]})  # obsolete in 2.2
        self.assertTrue(all(c.get("check_tr") for c in data["criteria"]))

    def test_asvs_selects_authorization(self):
        r = run_py(NFR / "nfr_checklist.py", "asvs", "--features", "authz", "--req", "REQ-013", "--start", "100")
        self.assertIn("## TC-100 | ASVS V8 Authorization", r.stdout)
        self.assertIn("pol: - | tech: cl | cat: security", r.stdout)
        self.assertNotIn("ASVS V5", r.stdout)

    def test_requires_req(self):
        self.assertEqual(run_py(NFR / "nfr_checklist.py", "asvs", "--features", "auth").returncode, 2)


class GenerateK6Tests(unittest.TestCase):
    def test_thresholds_from_requirement(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "perf.mjs"
            r = run_py(NFR / "generate_k6.py", SK / "testing-nonfunctional" / "assets" / "spec-examples" / "k6-perf.json", "--out", out)
            self.assertEqual(r.returncode, 0, r.stderr)
            js = out.read_text(encoding="utf-8")
            self.assertIn("executor: 'ramping-arrival-rate'", js)
            self.assertIn('"http_req_duration{name:apply_coupon}": ["p(95)<800", "p(99)<2000"]', js)
            self.assertIn('"http_req_duration{name:get_cart}": ["p(95)<1000", "p(99)<2000"]', js)
            self.assertIn('"http_req_failed": ["rate<0.01"]', js)
            self.assertIn("__ENV.K6_TOKEN", js)
            node = shutil.which("node")
            if node:
                self.assertEqual(subprocess.run([node, "--check", str(out)], capture_output=True).returncode, 0)


class ReviewAndImportTests(unittest.TestCase):
    def test_review_rules(self):
        tests = [
            {"id": "TC-001", "title": "Login testi", "requirement_ids": ["REQ-1"], "priority": "high", "polarity": "positive",
             "steps": [{"action": "Kullanıcı adını gir", "expected": "-"}, {"action": "Giriş butonuna tıkla", "expected": "Başarılı olmalı"}]},
            {"id": "TC-002", "title": "Hatalı şifre ile giriş reddedilir", "requirement_ids": ["REQ-1"], "priority": "high",
             "polarity": "negative", "preconditions": ["TC-001 çalıştırılmış olmalı"],
             "steps": [{"action": "E-posta ayse@test.com gir", "expected": "Alan dolar"},
                       {"action": "Giriş butonuna tıkla", "expected": "'Şifre hatalı' mesajı görünür"}]},
            {"id": "TC-003", "title": "Sepete ürün ekleme akışı", "requirement_ids": [], "polarity": "positive",
             "steps": [{"action": "Sepete ekle ve sonra sepete git", "expected": "Doğru çalışır"}]}]
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "t.json"
            p.write_text(json.dumps({"language": "tr", "test_cases": tests}, ensure_ascii=False), encoding="utf-8")
            r = run_py(REV / "review_tests.py", "--tests", p, "--json")
            self.assertEqual(r.returncode, 1)  # MISSING_EXPECTED is critical
            res = {x["id"]: {f["rule"] for f in x["findings"]} for x in json.loads(r.stdout)["results"]}
            self.assertTrue({"MISSING_EXPECTED", "VAGUE_EXPECTED", "WEAK_TITLE"} <= res["TC-001"])
            self.assertEqual(res["TC-002"], {"DEPENDENT"})  # "Giriş" is not the verb "gir"; e-mail is concrete data
            self.assertTrue({"VAGUE_EXPECTED", "MULTI_ACTION", "NO_REQ", "NO_PRIORITY"} <= res["TC-003"])

    def test_imported_suite_dependency_and_missing_data(self):
        # found by the agent eval: foreign IDs ("K-02 testi …") and data missing on a step without expected result
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            run_py(REV / "import_tests.py", ROOT / "evals" / "files" / "kupon-test-seti.csv", "--out", tmp / "t.src.md")
            run_py(COMPACT, "tc", tmp / "t.src.md", "--out", tmp / "t.json", "--lenient")
            res = json.loads(run_py(REV / "review_tests.py", "--tests", tmp / "t.json", "--json").stdout)
            rules = {x["id"]: {f["rule"] for f in x["findings"]} for x in res["results"]}
            self.assertIn("DEPENDENT", rules["TC-005"])                       # "K-02 testi çalıştırılmış olmalı"
            self.assertTrue({"MISSING_EXPECTED", "NO_DATA"} <= rules["TC-004"])  # "Süresi dolmuş kuponu gir" => -
            self.assertEqual(res["duplicate_titles"], ["150 tl sepette yaz10 ile %10 indirim"])
            self.assertNotIn("DEPENDENT", rules["TC-002"])                    # its own src-K-02 tag is not a dependency

    def test_import_row_per_test_and_row_per_step(self):
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            a = tmp / "a.csv"
            a.write_text('Test No;Başlık;Adımlar;Beklenen Sonuç;Öncelik;Gereksinim\n'
                         '1;Hatalı şifre reddedilir;"1. Şifre Yanlis1 gir 2. Giriş yap";"1. Alan dolar 2. ""Hatalı"" mesajı";Kritik;SHOP-10\n',
                         encoding="utf-8-sig")
            r = run_py(REV / "import_tests.py", a, "--out", tmp / "a.src.md")
            self.assertEqual(r.returncode, 0, r.stderr)
            _, items, errors = qc.parse((tmp / "a.src.md").read_text(encoding="utf-8"), "tc")
            self.assertEqual(errors, [])
            t = items[0]
            self.assertEqual((t["priority"], t["polarity"], t["requirement_ids"], len(t["steps"])),
                             ("critical", "negative", ["SHOP-10"], 2))
            b = tmp / "b.csv"
            b.write_text("TCID,Summary,Action,Data,Expected Result,Priority\n"
                         "T1,Kupon uygulanır,Sepeti aç,,Toplam 150 TL,High\nT1,,Kodu uygula,YAZ10,İndirim -15 TL,\n"
                         "T2,Kod boş bırakılır,Uygula'ya tıkla,,,Low\n", encoding="utf-8")
            r = run_py(REV / "import_tests.py", b, "--out", tmp / "b.src.md", "--lang", "en")
            self.assertIn("row per step", r.stdout)
            self.assertIn("steps without expected 1", r.stdout)
            text = (tmp / "b.src.md").read_text(encoding="utf-8")
            _, items, errors = qc.parse(text, "tc")
            self.assertEqual([len(t["steps"]) for t in items], [2, 1])
            self.assertEqual(items[0]["steps"][1]["data"], "YAZ10")
            self.assertTrue(qc.validate(items, "tc"))            # strict: missing expected is an error
            self.assertEqual(qc.validate(items, "tc", lenient=True), [])  # lenient import passes


class ExportTests(unittest.TestCase):
    def run_export(self, *args, tests=None):
        base = [sys.executable, str(EXPORT), "--tests", str(tests or FIX / "test-cases.json")]
        if tests is None:
            base += ["--requirements", str(FIX / "requirements.json")]
        return subprocess.run(base + list(args), capture_output=True, text=True, encoding="utf-8")

    def test_xray_rows_and_links(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "x.csv"
            r = self.run_export("--format", "xray", "--out", str(out), "--only", "TC-001,TC-003")
            self.assertEqual(r.returncode, 0, r.stderr)
            text = out.read_text(encoding="utf-8")
            rows = list(csv.reader(io.StringIO(text)))
            self.assertEqual(rows[0][:4], ["TCID", "Summary", "Description", "Test Type"])
            self.assertEqual([x[0] for x in rows[1:]], ["TC-001", "TC-001", "TC-003"])
            self.assertEqual(rows[1][7], "SHOP-101")
            self.assertEqual(rows[2][1], "")  # continuation row carries only step fields
            self.assertIn("ı", text)

    def test_zephyr_single(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "z.csv"
            r = self.run_export("--format", "zephyr", "--zephyr-steps", "single", "--out", str(out), "--only", "TC-001")
            self.assertEqual(r.returncode, 0, r.stderr)
            rows = list(csv.reader(io.StringIO(out.read_text(encoding="utf-8"))))
            self.assertEqual(len(rows), 2)
            self.assertIn("2. ", rows[1][-1])

    def test_generic_csv_has_bom(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "g.csv"
            self.run_export("--format", "csv", "--delimiter", ";", "--out", str(out))
            self.assertTrue(out.read_bytes().startswith(b"\xef\xbb\xbf"))

    def test_xlsx_is_valid_zip_xml(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "t.xlsx"
            r = self.run_export("--format", "xlsx", "--out", str(out))
            self.assertEqual(r.returncode, 0, r.stderr)
            with zipfile.ZipFile(out) as z:
                for n in z.namelist():
                    xml.dom.minidom.parseString(z.read(n))
                self.assertIn("xl/worksheets/sheet2.xml", z.namelist())

    def test_jira_keys_written_once(self):
        with tempfile.TemporaryDirectory() as d:
            req = Path(d) / "r.json"
            tc = Path(d) / "t.json"
            req.write_text(json.dumps({"requirements": [{"id": "REQ-001", "external_id": "SHOP-42"},
                                                        {"id": "REQ-002", "external_id": "SHOP-42"}]}), encoding="utf-8")
            tc.write_text(json.dumps({"test_cases": [{"id": "TC-001", "title": "x", "requirement_ids": ["REQ-001", "REQ-002"],
                                                      "priority": "high", "polarity": "positive",
                                                      "steps": [{"action": "a", "expected": "b"}]}]}), encoding="utf-8")
            out = Path(d) / "x.csv"
            subprocess.run([sys.executable, str(EXPORT), "--tests", str(tc), "--requirements", str(req), "--format", "xray",
                            "--out", str(out)], check=True, capture_output=True)
            rows = list(csv.reader(io.StringIO(out.read_text(encoding="utf-8"))))
            self.assertEqual(rows[1][7], "SHOP-42")

    def test_validation_blocks_bad_tests(self):
        with tempfile.TemporaryDirectory() as d:
            bad = Path(d) / "bad.json"
            bad.write_text(json.dumps({"test_cases": [{"id": "TC-001", "title": "x", "steps": []}]}), encoding="utf-8")
            out = Path(d) / "o.csv"
            r = self.run_export("--format", "xray", "--out", str(out), tests=bad)
            self.assertEqual(r.returncode, 1)
            self.assertFalse(out.exists())


if __name__ == "__main__":
    unittest.main()
