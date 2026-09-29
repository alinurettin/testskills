"""Tests for skills/testing-data-migrations (reconcile.py) - standard library only.

Run:  python -m unittest tests.test_testing_data_migrations -v
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "skills" / "testing-data-migrations"
SCRIPT = SKILL / "scripts" / "reconcile.py"
TRIAL = ROOT / "evals" / "trial-migration"
FIX = Path(__file__).resolve().parent / "fixtures" / "testing-data-migrations"

_spec = importlib.util.spec_from_file_location("reconcile", SCRIPT)
rec = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rec)


def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


def write(path: Path, text: str, encoding: str = "utf-8") -> str:
    path.write_bytes(text.encode(encoding))
    return str(path)


class TransformTests(unittest.TestCase):
    def ops(self, *ops):
        return rec.compile_ops(list(ops), "test")

    def test_turkish_casing(self):
        self.assertEqual(rec.apply_ops("Zeynep Çelik", {}, self.ops("upper_tr")), "ZEYNEP ÇELİK")
        self.assertEqual(rec.apply_ops("IŞIK İNCE", {}, self.ops("lower_tr")), "ışık ince")
        self.assertEqual(rec.apply_ops("ZEYNEP.CELIK@EXAMPLE.COM", {}, self.ops("lower")), "zeynep.celik@example.com")

    def test_decimal_parsing_formats_and_scale(self):
        cases = {"1.234,56": "1234.56", "1,234.56": "1234.56", "1234.56": "1234.56", "875,5": "875.50",
                 "-150,00": "-150.00", "150,00-": "-150.00", "1.234.567,89": "1234567.89", "0,005": "0.01"}
        for raw, want in cases.items():
            self.assertEqual(rec.apply_ops(raw, {}, self.ops("decimal:2")), want, raw)
        # forcing the comma: a single dot is a thousands separator
        self.assertEqual(rec.apply_ops("1.234", {}, self.ops("decimal:2:,")), "1234.00")
        self.assertEqual(rec.apply_ops("1.234", {}, self.ops("decimal")), "1.234")
        with self.assertRaises(rec.TransformError):
            rec.apply_ops("12a,5", {}, self.ops("decimal"))
        # Decimal, never float: 0.1 + 0.2 is exactly 0.3
        self.assertEqual(rec.parse_decimal("0,1") + rec.parse_decimal("0,2"), Decimal("0.3"))

    def test_date_map_default_concat_zeros(self):
        self.assertEqual(rec.apply_ops("05.03.1990", {}, self.ops("date:%d.%m.%Y>%Y-%m-%d")), "1990-03-05")
        with self.assertRaises(rec.TransformError):
            rec.apply_ops("31.02.1990", {}, self.ops("date:%d.%m.%Y>%Y-%m-%d"))
        m = self.ops({"map": {"A": "ACTIVE", "K": "CLOSED"}})
        self.assertEqual(rec.apply_ops("K", {}, m), "CLOSED")
        with self.assertRaises(rec.TransformError):
            rec.apply_ops("X", {}, m)
        self.assertEqual(rec.apply_ops("X", {}, self.ops('map:{"A":"ACTIVE","*":"UNKNOWN"}')), "UNKNOWN")
        self.assertEqual(rec.apply_ops("  ", {}, self.ops("default:TR")), "TR")
        self.assertEqual(rec.apply_ops("0001017", {}, self.ops("strip_leading_zeros")), "1017")
        self.assertEqual(rec.apply_ops("0000", {}, self.ops("strip_leading_zeros")), "0")
        self.assertEqual(rec.apply_ops("12", {}, self.ops("zfill:4")), "0012")
        row = {"AD": "  Mehmet  Ali", "SOYAD": "Tuncer", "X": ""}
        self.assertEqual(rec.apply_ops("", row, self.ops({"concat": ["AD", "X", "SOYAD", " "]}, "collapse_spaces", "upper_tr")),
                         "MEHMET ALİ TUNCER")
        with self.assertRaises(rec.UsageError):
            self.ops("reverse")

    def test_diagnose_hints(self):
        t = rec.T["en"]
        self.assertIn("utf-8", rec.diagnose("İBRAHİM", "İBRAHİM".encode("utf-8").decode("cp1252"), False, t))
        self.assertIn("cp1254", rec.diagnose("ŞAHİN", "ŞAHİN".encode("cp1254").decode("cp1252"), False, t))
        self.assertIn("×100", rec.diagnose("3456.78", "345678.00", True, t))
        self.assertIn("rounding", rec.diagnose("4350.57", "4350.56", True, t))
        self.assertIn("day/month", rec.diagnose("1990-03-05", "1990-05-03", False, t))
        self.assertIn("case", rec.diagnose("ÇELİK", "ÇELIK".lower(), False, t))
        self.assertIn("ASCII", rec.diagnose("ŞAHİN", "SAHIN", False, t))
        self.assertIn("different source code", rec.diagnose("CLOSED", "PASSIVE", False, t, frozenset({"CLOSED", "PASSIVE"})))

    def test_example_mapping_asset_is_valid(self):
        m = json.loads((SKILL / "assets" / "mapping-example.json").read_text(encoding="utf-8"))
        for col, spec in m["columns"].items():
            rec.compile_ops(spec.get("transform"), col)
        self.assertTrue(all(e.get("reason") for e in m["accepted_exceptions"]))


class TrialMigrationTests(unittest.TestCase):
    """The planted-defect trial: a correct mapping must find exactly the planted defects."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        out = Path(cls.tmp.name)
        cls.proc = run("--source", str(TRIAL / "legacy_customers.csv"), "--target", str(TRIAL / "new_customers.csv"),
                       "--key", "customer_id", "--mapping", str(FIX / "trial-mapping.json"), "--sum", "balance",
                       "--group-by", "branch", "--encoding-source", "cp1254", "--delimiter-source", ";",
                       "--max-examples", "100", "--lang", "tr", "--out", str(out / "rec.md"), "--json", str(out / "rec.json"))
        cls.res = json.loads((out / "rec.json").read_text(encoding="utf-8"))
        cls.md = (out / "rec.md").read_text(encoding="utf-8")

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_verdict_fail_exit_1(self):
        self.assertEqual(self.proc.returncode, 1, self.proc.stderr)
        self.assertEqual(self.res["verdict"], "FAIL")
        self.assertEqual((self.res["counts"]["source_rows"], self.res["counts"]["target_rows"]), (40, 41))

    def test_every_planted_defect_and_nothing_else(self):
        r = self.res
        self.assertEqual(r["missing_in_target"]["keys"], ["1017"])
        self.assertEqual(r["unexpected_in_target"]["keys"], ["9001"])
        self.assertEqual(r["duplicates"]["target"]["keys"], ["1035"])
        self.assertEqual(r["duplicates"]["source"]["count"], 0)
        self.assertEqual(r["empty_keys"]["count"], 0)
        got = {c: sorted(v["mismatch_keys"]) for c, v in r["columns"].items() if v["mismatch_keys"]}
        self.assertEqual(got, {"full_name": ["1004", "1022"], "balance": ["1009", "1031"],
                               "birth_date": ["1012"], "status": ["1027"]})
        self.assertEqual(sum(v["transform_errors"] for v in r["columns"].values()), 0)
        self.assertEqual(r["coverage"]["unmapped_source_columns"], [])
        self.assertEqual(r["coverage"]["not_migrated"], ["FAKS"])

    def test_hints_classify_the_defects(self):
        hints = {e["key"]: e["hint"] for c in self.res["columns"].values() for e in c["examples"]}
        self.assertIn("utf-8", hints["1004"])
        self.assertIn("cp1254", hints["1022"])
        self.assertIn("yuvarlama", hints["1009"])
        self.assertIn("×100", hints["1031"])
        self.assertIn("gün/ay", hints["1012"])
        self.assertIn("başka bir kaynak kod", hints["1027"])

    def test_control_totals_per_group(self):
        tot = self.res["control_totals"]["balance"]
        self.assertEqual(tot["difference"], "335121.21")
        self.assertEqual({g: v["difference"] for g, v in tot["groups"].items()},
                         {"ANK": "-7100.00", "IST": "342221.22", "IZM": "-0.01"})
        self.assertEqual(self.res["group_counts"]["IST"], {"source": 14, "target": 15})
        self.assertIn("Veri göçü mutabakatı", self.md)
        self.assertIn("Ä°BRAHÄ°M", self.md)


class ReconcileBehaviourTests(unittest.TestCase):
    SRC = "id;name;amount;branch\n1;Ayşe;1.000,50;A\n2;Ümit;20,00;A\n3;Işık;5,25;B\n"
    TGT = "id,name,amount,branch\n1,Ayşe,1000.50,A\n2,Ümit,20.00,A\n3,Işık,5.25,B\n"

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = Path(self.tmp.name)
        self.mapping = self.d / "m.json"
        self.mapping.write_text(json.dumps({"columns": {"id": "id", "name": "name", "branch": "branch",
                                                        "amount": {"source": "amount", "transform": ["decimal:2:,"]}}}),
                                encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def reconcile(self, src: str, tgt: str, *extra: str):
        s = write(self.d / "s.csv", src, "cp1254")
        t = write(self.d / "t.csv", tgt)
        p = run("--source", s, "--target", t, "--key", "id", "--mapping", str(self.mapping), "--sum", "amount",
                "--group-by", "branch", "--encoding-source", "cp1254", "--delimiter-source", ";",
                "--out", str(self.d / "r.md"), "--json", str(self.d / "r.json"), *extra)
        res = json.loads((self.d / "r.json").read_text(encoding="utf-8")) if p.returncode in (0, 1) else None
        return p, res

    def test_clean_migration_passes(self):
        p, res = self.reconcile(self.SRC, self.TGT)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertEqual(res["verdict"], "PASS")
        self.assertEqual(res["control_totals"]["amount"]["source"], "1025.75")
        self.assertIn("PASS", p.stdout)

    def test_tolerance(self):
        tgt = self.TGT.replace("1000.50", "1000.504")
        p, res = self.reconcile(self.SRC, tgt, "--tolerance", "0.005", "--total-tolerance", "0.005")
        self.assertEqual(p.returncode, 0, p.stdout)
        p, res = self.reconcile(self.SRC, tgt)
        self.assertEqual(p.returncode, 1)
        self.assertEqual(res["columns"]["amount"]["mismatch_keys"], ["1"])

    def test_accepted_exceptions_and_stale_ones(self):
        m = json.loads(self.mapping.read_text(encoding="utf-8"))
        m["accepted_exceptions"] = [
            {"check": "column", "key": "2", "column": "name", "reason": "DEF-1 accepted"},
            {"check": "missing", "key": "99", "reason": "never happens"}]
        self.mapping.write_text(json.dumps(m), encoding="utf-8")
        p, res = self.reconcile(self.SRC, self.TGT.replace("2,Ümit", "2,Umit"))
        self.assertEqual(p.returncode, 0, p.stdout)
        self.assertEqual(res["columns"]["name"]["accepted"], 1)
        observed = {e["key"]: e["observed"] for e in res["accepted_exceptions"]}
        self.assertEqual(observed, {"2": True, "99": False})

    def test_duplicates_in_source_and_unmapped_source_column(self):
        src = "id;name;amount;branch;fax\n1;Ayşe;1,00;A;x\n1;Ayşe;1,00;A;x\n"
        p, res = self.reconcile(src, "id,name,amount,branch\n1,Ayşe,1.00,A\n")
        self.assertEqual(p.returncode, 1)
        self.assertEqual(res["duplicates"]["source"]["keys"], ["1"])
        self.assertEqual(res["coverage"]["unmapped_source_columns"], ["fax"])

    def test_transform_error_is_reported_as_source_problem(self):
        p, res = self.reconcile(self.SRC.replace("5,25", "5,2x"), self.TGT)
        self.assertEqual(p.returncode, 1)
        self.assertEqual(res["columns"]["amount"]["transform_errors"], 1)
        self.assertIn("source not transformable", res["columns"]["amount"]["examples"][0]["hint"])
        self.assertEqual(res["unparseable"]["source"], 1)

    def test_composite_key_without_mapping(self):
        s = write(self.d / "a.csv", "order,line,qty\n1,1,5\n1,2,3\n2,1,7\n")
        t = write(self.d / "b.csv", "order,line,qty\n1,1,5\n1,2,4\n2,2,7\n")
        p = run("--source", s, "--target", t, "--key", "order,line", "--sum", "qty", "--out", str(self.d / "r.md"),
                "--json", str(self.d / "r.json"))
        res = json.loads((self.d / "r.json").read_text(encoding="utf-8"))
        self.assertEqual(p.returncode, 1)
        self.assertEqual(res["missing_in_target"]["keys"], ["2|1"])
        self.assertEqual(res["unexpected_in_target"]["keys"], ["2|2"])
        self.assertEqual(res["columns"]["qty"]["mismatch_keys"], ["1|2"])

    def test_usage_errors_exit_2(self):
        s = write(self.d / "s.csv", self.SRC, "cp1254")
        t = write(self.d / "t.csv", self.TGT)
        out = str(self.d / "r.md")
        # cp1254 file read as UTF-8 -> clear decode error, not a traceback
        p = run("--source", s, "--target", t, "--key", "id", "--delimiter-source", ";", "--out", out)
        self.assertEqual(p.returncode, 2)
        self.assertIn("cp1254", p.stderr)
        p = run("--source", s, "--target", t, "--key", "nope", "--encoding-source", "cp1254", "--delimiter-source", ";", "--out", out)
        self.assertEqual(p.returncode, 2)
        bad = self.d / "bad.json"
        bad.write_text(json.dumps({"columns": {"id": {"source": "id", "transform": ["reverse"]}}}), encoding="utf-8")
        p = run("--source", s, "--target", t, "--key", "id", "--mapping", str(bad), "--encoding-source", "cp1254",
                "--delimiter-source", ";", "--out", out)
        self.assertEqual(p.returncode, 2)
        self.assertIn("unknown transform op", p.stderr)

    def test_help_runs(self):
        p = run("--help")
        self.assertEqual(p.returncode, 0)
        self.assertIn("upper_tr", p.stdout)


if __name__ == "__main__":
    unittest.main()
