"""Tests for tools/check_facts.py and the docs/volatile-facts.json registry.

Run:  python -m unittest tests.test_check_facts -v
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOL = ROOT / "tools" / "check_facts.py"
REGISTRY = ROOT / "docs" / "volatile-facts.json"

spec = importlib.util.spec_from_file_location("check_facts_under_test", TOOL)
cf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cf)


def entry(**over):
    e = {"id": "demo-fact", "fact": "Demo fact.", "files": ["README.md"],
         "source_url": "https://example.com/source", "verified_on": "2026-09-30"}
    e.update(over)
    return e


class RegistryTests(unittest.TestCase):
    def test_the_real_registry_is_valid_and_complete(self):
        data = json.loads(REGISTRY.read_text(encoding="utf-8"))
        errors, warnings = cf.validate(data, date.today())
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [], "every listed file must exist")
        self.assertGreaterEqual(len(data), 10)
        ids = {e["id"] for e in data}
        for must in ("google-play-target-api", "apple-xcode-sdk-minimum", "owasp-top10-web", "owasp-asvs-version",
                     "owasp-llm-top10", "owasp-masvs-version", "wcag-version", "eu-ai-act-dates",
                     "playwright-version", "vkn-checksum-published-examples"):
            self.assertIn(must, ids)

    def test_known_stale_text_was_fixed(self):
        mobile = (ROOT / "skills" / "testing-mobile-apps" / "references" / "mobile-testing.md").read_text(encoding="utf-8")
        self.assertNotIn("API 35 from 31 August 2025", mobile)
        self.assertIn("API 36", mobile)


class ValidateTests(unittest.TestCase):
    today = date(2026, 9, 30)

    def errors(self, data):
        return cf.validate(data, self.today, ROOT)[0]

    def test_valid_entry(self):
        self.assertEqual(cf.validate([entry(), entry(id="other", note="n")], self.today, ROOT), ([], []))

    def test_malformed_entries(self):
        self.assertTrue(self.errors({"id": "x"}))  # not a list
        self.assertTrue(self.errors(["text"]))
        cases = {
            "missing": {k: v for k, v in entry().items() if k != "source_url"},
            "unknown key": entry(owner="qa"),
            "bad id": entry(id="Bad ID"),
            "empty fact": entry(fact=" "),
            "empty files": entry(files=[]),
            "files not a list": entry(files="README.md"),
            "absolute path": entry(files=["/etc/passwd"]),
            "parent path": entry(files=["../x.md"]),
            "http url": entry(source_url="http://example.com"),
            "bad date": entry(verified_on="30.09.2026"),
            "impossible date": entry(verified_on="2026-02-30"),
            "future date": entry(verified_on="2026-12-01"),
        }
        for name, e in cases.items():
            self.assertTrue(self.errors([e]), name)
        self.assertTrue(any("duplicate" in m for m in self.errors([entry(), entry()])))

    def test_missing_file_is_a_warning(self):
        errors, warnings = cf.validate([entry(files=["docs/no-such-file.md"])], self.today, ROOT)
        self.assertEqual(errors, [])
        self.assertEqual(len(warnings), 1)
        self.assertIn("no-such-file.md", warnings[0])

    def test_age_limit(self):
        data = [entry(id="old", verified_on="2026-04-02"), entry(id="edge", verified_on="2026-04-03")]
        due = cf.stale(data, self.today, 180)  # 181 and 180 days
        self.assertEqual(len(due), 1)
        self.assertTrue(due[0].startswith("old:"))
        self.assertIn("181 days", due[0])

    def test_gh_escape(self):
        self.assertEqual(cf.gh_escape("50%\nx"), "50%25%0Ax")


class CliTests(unittest.TestCase):
    def run_tool(self, data=None, *args, raw=None):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "facts.json"
            p.write_text(raw if raw is not None else json.dumps(data), encoding="utf-8", newline="\n")
            return subprocess.run([sys.executable, str(TOOL), "--file", str(p), "--root", str(ROOT), *args],
                                  capture_output=True, text=True, encoding="utf-8")

    def test_default_registry_passes(self):
        r = subprocess.run([sys.executable, str(TOOL)], capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertNotIn("::error::", r.stdout)

    def test_stale_entries_warn_but_pass(self):
        r = self.run_tool([entry(verified_on="2025-01-01"), entry(id="fresh")], "--today", "2026-09-30")
        self.assertEqual(r.returncode, 0, r.stdout)
        warn = [line for line in r.stdout.splitlines() if line.startswith("::warning::")]
        self.assertEqual(len(warn), 1)
        self.assertIn("demo-fact", warn[0])
        self.assertIn("1 due for re-verification", r.stdout)
        r = self.run_tool([entry()], "--today", "2026-09-30", "--max-age-days", "0")
        self.assertEqual(r.returncode, 0)
        self.assertNotIn("::warning::", r.stdout)  # verified today: age 0

    def test_malformed_file_fails(self):
        r = self.run_tool([entry(verified_on="soon")], "--today", "2026-09-30")
        self.assertEqual(r.returncode, 1)
        self.assertIn("::error::", r.stdout)
        r = self.run_tool(raw="[{broken")
        self.assertEqual(r.returncode, 1)
        self.assertIn("::error::", r.stdout)
        r = self.run_tool([entry()], "--today", "tomorrow")
        self.assertEqual(r.returncode, 2)


if __name__ == "__main__":
    unittest.main()
