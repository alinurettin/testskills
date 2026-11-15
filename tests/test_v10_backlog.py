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
            rows = ["id,dogum,il,cinsiyet,tani", "1,1980-01-05,Ankara,K,A", "2,1980-07-09,Ankara,K,B",
                    "3,1980-03-01,Ankara,K,A", "4,1991-02-02,Izmir,E,C", ""]
            (t / "in.csv").write_text(chr(10).join(rows), encoding="utf-8")
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


class PairConsistencyTests(unittest.TestCase):
    def score(self, second_output: str):
        with tempfile.TemporaryDirectory() as t:
            t = Path(t)
            cases = [{"id": "AI-001", "category": "harmful", "input": "a", "checks": [{"type": "refusal"}], "pair": "AI-002", "status": "ready"},
                     {"id": "AI-002", "category": "harmful", "input": "b", "checks": [{"type": "refusal"}], "pair": "AI-001", "status": "ready"}]
            outs = [{"id": "AI-001", "run": r, "output": "Sorry, I can't help with that."} for r in range(1, 6)]
            outs += [{"id": "AI-002", "run": r, "output": second_output} for r in range(1, 6)]
            (t / "c.jsonl").write_text(chr(10).join(json.dumps(x) for x in cases) + chr(10), encoding="utf-8")
            (t / "o.jsonl").write_text(chr(10).join(json.dumps(x) for x in outs) + chr(10), encoding="utf-8")
            return run(SK / "testing-ai-features/scripts/ai_eval.py", "score", "--cases", t / "c.jsonl", "--outputs", t / "o.jsonl",
                       "--threshold", "0.4")

    def test_pair_disagreement_fails_the_gate(self):
        r = self.score("Sure, here are the steps: 1) ...")
        self.assertEqual(r.returncode, 1)
        self.assertIn("Paired cases AI-001 and AI-002 disagree", r.stdout + r.stderr)

    def test_agreeing_pair_passes(self):
        r = self.score("Sorry, I can't help with that.")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_seed_links_pairs_in_groups(self):
        with tempfile.TemporaryDirectory() as t:
            out = Path(t) / "s.jsonl"
            run(SK / "testing-ai-features/scripts/ai_eval.py", "seed", "--feature", "x", "--out", out)
            cases = [json.loads(x) for x in out.read_text(encoding="utf-8").splitlines() if x.strip()]
            ids = {c["id"] for c in cases}
            paired = [c for c in cases if c.get("pair")]
            self.assertGreaterEqual(len(paired), 5)  # bias pair + three written forms of one harmful request
            self.assertTrue(all(c["pair"] in ids and c["pair"] != c["id"] for c in paired))


class StateCoverageTests(unittest.TestCase):
    def test_n_switch_and_figures(self):
        d = SK / "designing-test-cases"
        spec = {"id": "DS-9", "title": "x", "states": ["A", "B", "C"], "events": ["go", "back"], "initial": "A", "final": [],
                "transitions": [{"id": "T1", "from": "A", "event": "go", "to": "B"}, {"id": "T2", "from": "B", "event": "go", "to": "C"},
                                {"id": "T3", "from": "C", "event": "back", "to": "A"}]}
        with tempfile.TemporaryDirectory() as t:
            f = Path(t) / "s.json"
            f.write_text(json.dumps(spec), encoding="utf-8")
            for n, chains in ((0, 3), (1, 3), (2, 3)):
                r = run(d / "scripts/state_transition.py", f, "--switch", n, "--format", "json")
                res = json.loads(r.stdout)
                fig = res["coverage_figures"]
                self.assertEqual(fig["states"], [3, 3])
                self.assertEqual(fig["transitions"], [3, 3])
                self.assertEqual(fig[f"{n}-switch chains"], [chains, chains])
            ids = [s["transitions"] for s in res["sequences"]]
            flat = [x for s in ids for x in s]
            self.assertTrue(any(flat[i:i + 3] == ["T3", "T1", "T2"] for i in range(len(flat))))  # a 2-switch chain is walked


class TemplateTests(unittest.TestCase):
    def test_exit_criteria_template_keys_are_known(self):
        tpl = json.loads((SK / "planning-tests/assets/exit-criteria.json").read_text(encoding="utf-8"))
        script = (SK / "reporting-test-results/scripts/completion_report.py").read_text(encoding="utf-8")
        for key in tpl:
            self.assertIn(f'"{key}"', script, key)


if __name__ == "__main__":
    unittest.main()
