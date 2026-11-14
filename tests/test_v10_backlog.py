"""Backlog items from docs/audit-2026-11 implemented after 0.10.0."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SK = ROOT / "skills"
FIX = ROOT / "tests" / "fixtures" / "coupon"


def run(script: Path, *args) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(script), *map(str, args)], capture_output=True, text=True, encoding="utf-8")


class AutomationLintTests(unittest.TestCase):
    SPEC = ("import { test, expect } from '@playwright/test';\n"
            "test('TC-001 x', { tag: ['@TC-001'] }, async ({ page }) => {\n"
            "%s"
            "  await expect(page.getByRole('heading')).toBeVisible();\n});\n")

    def check(self, body: str):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "a.spec.ts").write_text(self.SPEC % body, encoding="utf-8")
            out = Path(d) / "r.md"
            r = run(SK / "automating-with-playwright/scripts/check_automation.py", "--tests", FIX / "test-cases.json",
                    "--specs", d, "--out", out)
            return r, out.read_text(encoding="utf-8")

    def test_smells_are_reported(self):
        r, md = self.check("  await page.waitForTimeout(3000);\n  await page.locator('#btn').click({ force: true });\n"
                           "  const password = 'Sup3rSecret1';\n")
        for rule in ("WAIT_TIMEOUT", "FORCE", "RAW_SELECTOR", "CREDENTIAL"):
            self.assertIn(rule, md)
        self.assertIn("lint 4", r.stdout)

    def test_clean_spec_and_comments_have_no_findings(self):
        r, md = self.check("  // await page.waitForTimeout(1); explained in a comment\n"
                           "  const password = process.env.TEST_PASSWORD;\n  await page.getByRole('button', { name: 'Uygula' }).click();\n")
        self.assertNotIn("Lint findings", md)
        self.assertNotIn("lint", r.stdout)


class DesignCoverageTests(unittest.TestCase):
    def test_covered_uncovered_unknown(self):
        d = SK / "designing-test-cases"
        with tempfile.TemporaryDirectory() as t:
            design = Path(t) / "design"
            design.mkdir()
            run(d / "scripts/decision_table.py", d / "assets/spec-examples/decision-table.json", "--out", design / "DS-002-x.md")
            tc = [{"id": "TC-001", "design_ref": "DS-002 C-01, C-02"}, {"id": "TC-002", "objective": "DS-002 C-03: x"},
                  {"id": "TC-003", "design_ref": "DS-002 C-99"}, {"id": "TC-004", "design_ref": "DS-002"},
                  {"id": "TC-005", "design_ref": "DS-002 C-04", "status": "deprecated"}]
            (Path(t) / "t.json").write_text(json.dumps({"test_cases": tc}), encoding="utf-8")
            js = Path(t) / "c.json"
            r = run(d / "scripts/design_coverage.py", "--design-dir", design, "--tests", Path(t) / "t.json",
                    "--out", Path(t) / "c.md", "--json", js)
            self.assertEqual(r.returncode, 1)  # an unknown reference is always a failure
            res = json.loads(js.read_text(encoding="utf-8"))
            spec = res["specs"][0]
            self.assertEqual((spec["covered"], spec["total"]), (3, 5))
            self.assertEqual(spec["uncovered"], ["C-04", "C-05"])  # the deprecated test does not cover C-04
            self.assertEqual(res["unknown_references"][0]["item"], "C-99")
            self.assertEqual(res["tests_without_item"][0]["test"], "TC-004")

    def test_minimum_gate(self):
        d = SK / "designing-test-cases"
        with tempfile.TemporaryDirectory() as t:
            design = Path(t) / "design"
            design.mkdir()
            run(d / "scripts/decision_table.py", d / "assets/spec-examples/decision-table.json", "--out", design / "DS-002-x.md")
            (Path(t) / "t.json").write_text(json.dumps({"test_cases": [{"id": "TC-001", "design_ref": "DS-002 C-01"}]}), encoding="utf-8")
            args = [d / "scripts/design_coverage.py", "--design-dir", design, "--tests", Path(t) / "t.json", "--out", Path(t) / "c.md"]
            self.assertEqual(run(*args).returncode, 0)
            self.assertEqual(run(*args, "--min-coverage", 100).returncode, 1)


class KAnonymityTests(unittest.TestCase):
    def test_k_and_low_cardinality_hash(self):
        import os
        with tempfile.TemporaryDirectory() as t:
            t = Path(t)
            (t / "in.csv").write_text("id,dogum,il,cinsiyet,tani
1,1980-01-05,Ankara,K,A
2,1980-07-09,Ankara,K,B
"
                                      "3,1980-03-01,Ankara,K,A
4,1991-02-02,Izmir,E,C
", encoding="utf-8")
            rules = {"columns": {"id": {"rule": "hash"}, "dogum": {"rule": "generalize", "to": "year"}, "il": "keep",
                                 "cinsiyet": {"rule": "hash"}, "tani": "keep"},
                     "quasi_identifiers": ["dogum", "il", "cinsiyet"], "sensitive": "tani", "min_k": 2}
            (t / "r.json").write_text(json.dumps(rules), encoding="utf-8")
            env = dict(os.environ, MASK_SECRET="0123456789abcdef0123")
            cmd = [sys.executable, str(SK / "preparing-test-data/scripts/mask_data.py"), "--in", str(t / "in.csv"),
                   "--rules", str(t / "r.json"), "--out", str(t / "o.csv")]
            r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", env=env)
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("k = 1", r.stdout)
            self.assertIn("'cinsiyet' is hashed", r.stdout)     # 2 values over 4 rows: reversible
            self.assertNotIn("'id' is hashed", r.stdout)        # a unique key is not low-cardinality
            r = subprocess.run(cmd + ["--min-k", "1"], capture_output=True, text=True, encoding="utf-8", env=env)
            self.assertNotIn("below min_k", r.stdout)


class TemplateTests(unittest.TestCase):
    def test_exit_criteria_template_keys_are_known(self):
        tpl = json.loads((SK / "planning-tests/assets/exit-criteria.json").read_text(encoding="utf-8"))
        script = (SK / "reporting-test-results/scripts/completion_report.py").read_text(encoding="utf-8")
        for key in tpl:
            self.assertIn(f'"{key}"', script, key)


if __name__ == "__main__":
    unittest.main()
