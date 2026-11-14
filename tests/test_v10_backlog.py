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


class TemplateTests(unittest.TestCase):
    def test_exit_criteria_template_keys_are_known(self):
        tpl = json.loads((SK / "planning-tests/assets/exit-criteria.json").read_text(encoding="utf-8"))
        script = (SK / "reporting-test-results/scripts/completion_report.py").read_text(encoding="utf-8")
        for key in tpl:
            self.assertIn(f'"{key}"', script, key)


if __name__ == "__main__":
    unittest.main()
