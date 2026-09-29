"""Tests for skills/running-exploratory-tests/scripts/sbtm.py (standard library only).

Run:  python -m unittest discover -s tests -v
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "skills" / "running-exploratory-tests"
SBTM = SKILL / "scripts" / "sbtm.py"
FIX = Path(__file__).resolve().parent / "fixtures" / "running-exploratory-tests"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


sbtm = load(SBTM, "sbtm_exploratory")
qc = load(SKILL / "scripts" / "qa_compact.py", "qa_compact_exploratory")


def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SBTM), *args], capture_output=True, text=True, encoding="utf-8")


def compact_items(text: str):
    """Parse and validate compact test cases exactly as qa_compact.py does."""
    _, items, errors = qc.parse(text, "tc")
    return items, errors + qc.validate(items, "tc")


class ChartersTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.out = Path(self.tmp.name) / "charters.md"

    def tearDown(self):
        self.tmp.cleanup()

    def test_ranking_timeboxes_and_missing_risk_last(self):
        p = run("charters", "--requirements", str(FIX / "requirements.json"), "--out", str(self.out))
        self.assertEqual(p.returncode, 0, p.stderr)
        lines = [ln for ln in p.stdout.splitlines() if ln.strip().startswith("CH-")]
        got = [(ln.split()[1], ln.split()[3], ln.split()[4]) for ln in lines]
        self.assertEqual(got, [("REQ-001", "critical", "120"), ("REQ-003", "high", "90"),
                               ("REQ-002", "medium", "90"), ("REQ-004", "low", "60"), ("REQ-005", "low", "60")])
        text = self.out.read_text(encoding="utf-8")
        self.assertNotIn("REQ-006", text)  # deprecated requirements are skipped
        self.assertIn("ranking is provisional", text)  # REQ-005 has no risk
        self.assertIn("Explore Daily transfer limit (REQ-001) with", text)

    def test_heuristics_follow_requirement_content(self):
        run("charters", "--requirements", str(FIX / "requirements.json"), "--out", str(self.out))
        text = self.out.read_text(encoding="utf-8")
        sections = {s.split(" · ")[1]: s for s in text.split("## CH-")[1:]}
        self.assertIn("Boundaries and Goldilocks", sections["REQ-001"])
        self.assertIn("Real payment cards", sections["REQ-001"])
        self.assertIn("Role swap / BOLA", sections["REQ-003"])
        self.assertIn("Open questions Q-002", sections["REQ-003"])
        self.assertIn("State model walk", sections["REQ-002"])
        self.assertIn("Data tour / follow the data", sections["REQ-004"])
        # "statement" must not trigger the state rule; no match falls back to SFDIPOT
        self.assertIn("SFDIPOT sweep", sections["REQ-005"])
        self.assertNotIn("State model walk", sections["REQ-005"])

    def test_top_limit_turkish_and_deterministic(self):
        args = ["charters", "--requirements", str(FIX / "requirements.json"), "--top", "2", "--lang", "tr",
                "--out", str(self.out)]
        self.assertEqual(run(*args).returncode, 0)
        first = self.out.read_text(encoding="utf-8")
        run(*args)
        self.assertEqual(first, self.out.read_text(encoding="utf-8"))
        self.assertEqual(first.count("\n## CH-"), 2)
        self.assertIn("keşfet; amaç:", first)
        self.assertIn("Planlanan bütçe: 2 oturum, 210 dk", first)


class ReportTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def sheet(self, name: str, text: str) -> Path:
        p = self.dir / name
        p.write_text(text, encoding="utf-8")
        return p

    def test_parse_session_header_details_and_req_links(self):
        s, errors, warns = sbtm.parse_session(FIX / "S-001.md")
        self.assertEqual(errors, [])
        self.assertEqual((s["id"], s["duration"], s["tbs"], s["opp"]), ("S-001", 90, (60, 25, 15), 10))
        self.assertEqual((s["header"]["env"], s["header"]["build"]), ("staging", "2.4.0-rc1"))
        bugs = [n for n in s["notes"] if n["tag"] == "BUG"]
        self.assertEqual(bugs[0]["reqs"], ["REQ-001"])  # found in the 'expected:' detail
        self.assertEqual(bugs[0]["detail"]["severity"], "critical")
        self.assertEqual(len(bugs[0]["detail"]["steps"]), 2)
        self.assertEqual(bugs[1]["reqs"], ["REQ-002"])  # explicit [REQ-002]
        self.assertEqual(len(bugs[1]["detail"]["steps"]), 3)  # numbered detail lines
        self.assertTrue(any("untagged line" in w for w in warns))
        tr, errors, _ = sbtm.parse_session(FIX / "S-002.md")  # Turkish keys and tags
        self.assertEqual(errors, [])
        self.assertEqual((tr["id"], tr["duration"], tr["reqs"]), ("S-002", 60, ["REQ-003"]))
        self.assertEqual([n["tag"] for n in tr["notes"]], ["NOTE", "COVERED", "BUG", "QUESTION", "IDEA"])

    def test_report_outputs_and_candidate_tests_accepted_by_qa_compact(self):
        p = run("report", str(FIX / "S-001.md"), str(FIX / "S-002.md"), "--requirements", str(FIX / "requirements.json"),
                "--start", "20", "--out-dir", str(self.dir))
        self.assertEqual(p.returncode, 0, p.stderr)
        summary = (self.dir / "session-summary.md").read_text(encoding="utf-8")
        self.assertIn("Total session time: 150 min (2.5 h) in 2 sessions.", summary)
        self.assertIn("1 of 2 sessions recorded it): test 60%, bug investigation 25%, setup 15%", summary)
        self.assertIn("BUG 3 · ISSUE 1 · QUESTION 2 · IDEA 2", summary)
        self.assertIn("| S-001 | 10:24 |", summary)
        self.assertIn("- Feelings:", summary)
        defects = (self.dir / "defects.md").read_text(encoding="utf-8")
        self.assertEqual(defects.count("\n## D-"), 3)
        self.assertIn("starting point from REQ-002 impact 3: medium", defects)
        self.assertIn("<quote REQ-002: A transfer moves", defects)
        items, errors = compact_items((self.dir / "candidate-tests.src.md").read_text(encoding="utf-8"))
        self.assertEqual(errors, [])
        self.assertEqual([t["id"] for t in items], ["TC-020", "TC-021", "TC-022", "TC-023", "TC-024"])
        self.assertTrue(all(t["status"] == "draft" and t["requirement_ids"] for t in items))
        first = items[0]
        self.assertEqual((first["requirement_ids"], first["priority"], first["polarity"]), (["REQ-001"], "critical", "negative"))
        self.assertIn("regression", first["tags"])
        self.assertTrue(first["automation"]["candidate"])
        self.assertEqual(items[3]["category"], "security")
        self.assertNotIn("regression", items[2]["tags"])  # IDEA, not a bug

    def test_numbering_continues_from_existing_tests(self):
        tests = self.dir / "test-cases.json"
        tests.write_text(json.dumps({"test_cases": [{"id": "TC-007"}, {"id": "TC-003"}]}), encoding="utf-8")
        p = run("report", str(FIX / "S-002.md"), "--tests", str(tests), "--lang", "tr", "--out-dir", str(self.dir))
        self.assertEqual(p.returncode, 0, p.stderr)
        text = (self.dir / "candidate-tests.src.md").read_text(encoding="utf-8")
        self.assertIn("## TC-008 | Regresyon: Başka kullanıcının", text)
        self.assertIn("## TC-009 |", text)
        self.assertIn("Oturum özeti".lower(), (self.dir / "session-summary.md").read_text(encoding="utf-8").lower())

    def test_awkward_note_text_and_missing_req_still_valid_compact(self):
        s = self.sheet("S-9.md", "charter: Explore search\nduration: 45 min\n\n"
                                 "09:00 BUG: Search | filter => crashes [Apply]\n"
                                 "09:05 BUG: Search | filter => crashes [Apply]\n"
                                 "09:10 IDEA: Emoji in search box\n")
        p = run("report", str(s), "--out-dir", str(self.dir))
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("no 'req:' IDs", p.stdout)
        self.assertIn("no COVERED notes", p.stdout)
        items, errors = compact_items((self.dir / "candidate-tests.src.md").read_text(encoding="utf-8"))
        self.assertEqual(errors, [])
        self.assertEqual(len(items), 3)
        self.assertEqual(len({t["title"] for t in items}), 3)  # duplicate titles get a suffix
        self.assertTrue(all("exploratory" in t["tags"] for t in items))  # untraced: must be linked before 'ready'
        self.assertIn("TBS: not recorded", (self.dir / "session-summary.md").read_text(encoding="utf-8"))

    def test_missing_charter_or_duration_fails_and_writes_nothing(self):
        s = self.sheet("bad.md", "tester: Test Analyst C\nreq: REQ-001\n10:00 BUG: Something\n")
        p = run("report", str(s), "--out-dir", str(self.dir / "out"))
        self.assertEqual(p.returncode, 1)
        self.assertIn("missing 'charter:'", p.stderr)
        self.assertIn("'duration:'", p.stderr)
        self.assertFalse((self.dir / "out").exists())

    def test_tbs_must_sum_to_100_and_durations_parse(self):
        s = self.sheet("S-3.md", "charter: Explore x\nduration: 1h30\ntbs: 50/30/30\nreq: REQ-001\n"
                                 "10:00 COVERED: x\n")
        sess, errors, warns = sbtm.parse_session(s)
        self.assertEqual((errors, sess["duration"], sess["tbs"]), ([], 90, None))
        self.assertTrue(any("tbs" in w for w in warns))
        self.assertEqual([sbtm.parse_duration(v) for v in ("90", "90 dk", "1:15", "2h", "soon")], [90, 90, 75, 120, None])

    def test_template_halves_parse_cleanly(self):
        text = (SKILL / "assets" / "session-sheet.md").read_text(encoding="utf-8")
        en, tr = text.split("\n---\n")
        for name, part in (("en.md", en), ("tr.md", tr)):
            s, errors, warns = sbtm.parse_session(self.sheet(name, part))
            self.assertEqual(errors, [], name)
            self.assertFalse([w for w in warns if "untagged" in w], name)
            self.assertEqual(sorted({n["tag"] for n in s["notes"]}), sorted(sbtm.TAGS), name)
            self.assertEqual(s["tbs"], (60, 25, 15))

    def test_help_runs(self):
        p = run("--help")
        self.assertEqual(p.returncode, 0)
        self.assertIn("charters", p.stdout)
        self.assertEqual(run("report").returncode, 2)


if __name__ == "__main__":
    unittest.main()
