"""Regression tests for the adversarial findings fixed in 0.7.1 (CSV injection, OpenAPI 3.1 type lists,
decision-table explosion, invalid EP/BVA ranges)."""
from __future__ import annotations

import csv
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SK = Path(__file__).resolve().parent.parent / "skills"


def run(script: Path, *args) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(script), *map(str, args)], capture_output=True, text=True, encoding="utf-8")


class HardeningTests(unittest.TestCase):
    def test_csv_formula_injection_is_neutralised(self):
        with tempfile.TemporaryDirectory() as d:
            tc = Path(d) / "t.json"
            tc.write_text(json.dumps({"test_cases": [{
                "id": "TC-001", "title": "=1+1", "requirement_ids": ["REQ-1"], "priority": "high", "polarity": "positive",
                "preconditions": ["- bullet stays", "-150"],
                "steps": [{"action": "@SUM(A1)", "expected": "-2+3+cmd|' /C calc'!A0"}]}]}), encoding="utf-8")
            out = Path(d) / "o.csv"
            self.assertEqual(run(SK / "exporting-test-cases/scripts/export_tests.py", "--tests", tc, "--format", "testrail",
                                 "--out", out).returncode, 0)
            rows = list(csv.reader(io.StringIO(out.read_text(encoding="utf-8"))))
            cells = [c for r in rows[1:] for c in r if c]
            self.assertFalse([c for c in cells if c[0] in "=+@" or (c.startswith("-") and len(c) > 1 and not c[1].isspace())],
                             cells)
            gen = Path(d) / "g.csv"
            run(SK / "exporting-test-cases/scripts/export_tests.py", "--tests", tc, "--format", "csv", "--out", gen)
            self.assertIn("'=1+1", gen.read_text(encoding="utf-8-sig"))
            raw = Path(d) / "raw.csv"
            run(SK / "exporting-test-cases/scripts/export_tests.py", "--tests", tc, "--format", "testrail", "--out", raw,
                "--no-formula-escape")
            self.assertIn("=1+1", raw.read_text(encoding="utf-8"))

    def test_openapi_31_type_lists(self):
        doc = {"openapi": "3.1.0", "info": {"title": "x", "version": "1"}, "paths": {"/a": {"post": {
            "requestBody": {"content": {"application/json": {"schema": {"type": "object", "required": ["n"], "properties": {
                "n": {"type": ["string", "null"], "maxLength": 5}, "k": {"type": ["integer", "null"], "maximum": 9}}}}}},
            "responses": {"201": {"description": "ok"}, "400": {"description": "bad"}}}}}}
        with tempfile.TemporaryDirectory() as d:
            spec = Path(d) / "o.json"
            spec.write_text(json.dumps(doc), encoding="utf-8")
            r = run(SK / "testing-apis/scripts/openapi_tests.py", spec, "--req", "REQ-1", "--out", Path(d) / "o.md",
                    "--spec-out", Path(d) / "o.ts")
            self.assertEqual(r.returncode, 0, r.stderr)
            ts = (Path(d) / "o.ts").read_text(encoding="utf-8")
            self.assertIn("aaaaaa", ts)  # maxLength + 1 probe
            self.assertIn("10", ts)      # maximum + 1 probe

    def test_decision_table_explosion_is_refused(self):
        with tempfile.TemporaryDirectory() as d:
            spec = Path(d) / "dt.json"
            spec.write_text(json.dumps({"id": "DS-1", "title": "x", "actions": ["a"],
                                        "conditions": [{"name": f"c{i}", "values": ["Y", "N"]} for i in range(14)],
                                        "rules": [{"id": "R1", "when": {"c0": "Y"}, "then": {"a": "X"}}]}), encoding="utf-8")
            r = run(SK / "designing-test-cases/scripts/decision_table.py", spec, "--out", Path(d) / "o.md")
            self.assertEqual(r.returncode, 2)
            self.assertIn("exceed the limit", r.stderr)

    def test_ep_bva_rejects_zero_step_and_inverted_range(self):
        for p in ({"name": "a", "type": "decimal", "step": "0", "min": "1", "max": "5"},
                  {"name": "a", "type": "integer", "min": 100, "max": 10}):
            with tempfile.TemporaryDirectory() as d:
                spec = Path(d) / "e.json"
                spec.write_text(json.dumps({"id": "DS-1", "title": "x", "parameters": [p]}), encoding="utf-8")
                r = run(SK / "designing-test-cases/scripts/ep_bva.py", spec, "--out", Path(d) / "o.md")
                self.assertEqual(r.returncode, 2, r.stdout)
                self.assertIn("error:", r.stderr)


class InternationalDataTests(unittest.TestCase):
    def test_new_types_are_valid(self):
        sys.path.insert(0, str(SK / "preparing-test-data" / "scripts"))
        import tr_ids
        with tempfile.TemporaryDirectory() as d:
            schema = Path(d) / "s.json"
            schema.write_text(json.dumps({"fields": [
                {"name": "card", "type": "card_test"}, {"name": "us", "type": "phone_intl", "country": "US"},
                {"name": "gb", "type": "phone_intl", "country": "GB"},
                {"name": "iban", "type": "iban", "country": "DE"}, {"name": "nl", "type": "iban", "country": "NL"}]}),
                encoding="utf-8")
            out = Path(d) / "o.csv"
            r = run(SK / "preparing-test-data/scripts/gen_data.py", "--schema", schema, "--rows", 200, "--seed", 7, "--out", out)
            self.assertEqual(r.returncode, 0, r.stderr)
            rows = list(csv.DictReader(io.StringIO(out.read_text(encoding="utf-8-sig"))))
            published = {c for v in tr_ids.TEST_CARDS.values() for c in v}
            for row in rows:
                self.assertIn(row["card"], published)
                self.assertTrue(tr_ids.luhn_ok(row["card"]))
                self.assertRegex(row["us"], r"^\+1\d{3}5550(1\d\d)$")   # NANPA fictional 555-0100..0199
                self.assertRegex(row["gb"], r"^\+447700900\d{3}$")       # Ofcom drama range
                self.assertTrue(tr_ids.is_valid_iban(row["iban"]) and row["iban"].startswith("DE"))
                self.assertTrue(tr_ids.is_valid_iban(row["nl"]))
        self.assertFalse(tr_ids.luhn_ok("4111111111111112"))


class SecurityProbeTests(unittest.TestCase):
    def test_probes_are_opt_in(self):
        doc = SK.parent / "evals" / "trial-api" / "api" / "openapi.json"
        with tempfile.TemporaryDirectory() as d:
            for flag, expect in ((None, False), ("--security-probes", True)):
                args = [doc, "--req", "REQ-1", "--out", Path(d) / "o.md", "--spec-out", Path(d) / "o.ts"] + ([flag] if flag else [])
                self.assertEqual(run(SK / "testing-apis/scripts/openapi_tests.py", *args).returncode, 0)
                ts = (Path(d) / "o.ts").read_text(encoding="utf-8")
                self.assertEqual("' OR '1'='1' --" in ts and "<script>alert(1)</script>" in ts, expect)


if __name__ == "__main__":
    unittest.main()
