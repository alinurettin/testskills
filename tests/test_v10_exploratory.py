"""0.10 regression tests for running-exploratory-tests (audit 2026-11, findings 2, 3, 10 and the Turkish terms).

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

spec = importlib.util.spec_from_file_location("sbtm_v10", SBTM)
sbtm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sbtm)


def run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SBTM), *args], capture_output=True, text=True, encoding="utf-8")


SHEET = ("charter: Explore the order flow with the P1 probes\n"
         "duration: 30\n\n"
         "COVERED: pay order / views, boundary, repeat\n"
         "BUG: Double click on Pay creates two orders\n"
         "  steps: Add one item; double-click Pay\n"
         "  expected: One order\n"
         "  actual: Two orders\n"
         "  severity: high\n"
         "  confidence: confirmed\n"
         "BUG: Order total differs between list and API once\n"
         "  confidence: seen once\n"
         "HATA: Liste eski toplamı gösteriyor\n"
         "  güven: bir kez görüldü\n"
         "BUG: Search drops the last result\n"
         "BUG: Sort order flips\n"
         "  confidence: maybe\n")


class ConfidenceTests(unittest.TestCase):
    """Finding 2: an unreproduced bug is reported with a confidence, never dropped or downgraded."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.sheet = self.dir / "S-020.md"
        self.sheet.write_text(SHEET, encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_confidence_is_parsed_in_english_and_turkish_and_notes_need_no_time(self):
        s, errors, warns = sbtm.parse_session(self.sheet)
        self.assertEqual(errors, [])
        bugs = [n for n in s["notes"] if n["tag"] == "BUG"]
        self.assertEqual([n.get("confidence") for n in bugs], ["confirmed", "seen once", "seen once", None, ""])
        self.assertTrue(all(n["time"] == "" for n in s["notes"]))
        self.assertEqual(len([w for w in warns if "confidence 'maybe' not understood" in w]), 1)
        self.assertFalse([w for w in warns if "untagged" in w], warns)

    def test_seen_once_bug_keeps_its_defect_draft_and_regression_test(self):
        p = run("report", str(self.sheet), "--out-dir", str(self.dir / "out"))
        self.assertEqual(p.returncode, 0, p.stderr)
        defects = (self.dir / "out" / "defects.md").read_text(encoding="utf-8")
        self.assertEqual(defects.count("\n## D-"), 5)
        self.assertIn("- **Confidence:** confirmed\n", defects)
        self.assertEqual(defects.count("- **Confidence:** seen once - reproduce before filing; do not drop it"), 2)
        self.assertIn("- **Confidence:** not stated", defects)
        self.assertIn("- **Confidence:** maybe", defects)  # not understood: shown as written, plus a warning
        summary = (self.dir / "out" / "session-summary.md").read_text(encoding="utf-8")
        self.assertIn("Bugs by confidence: confirmed 1 · seen once 2 · not stated 2.", summary)
        self.assertIn("| D-02 | TC-002 | seen once |", summary)
        cand = (self.dir / "out" / "candidate-tests.src.md").read_text(encoding="utf-8")
        self.assertEqual(cand.count("tags: regression, from-exploratory"), 5)

    def test_turkish_report_uses_the_official_terms(self):
        p = run("report", str(self.sheet), "--lang", "tr", "--out-dir", str(self.dir / "tr"))
        self.assertEqual(p.returncode, 0, p.stderr)
        summary = (self.dir / "tr" / "session-summary.md").read_text(encoding="utf-8")
        self.assertIn("Bilgilendirme toplantısı (PROOF)", summary)
        self.assertIn("| Oturum | Başlatma belgesi | Test uzmanı |", summary)
        self.assertIn("bir kez görüldü 2", summary)
        defects = (self.dir / "tr" / "defects.md").read_text(encoding="utf-8")
        self.assertIn("- **Önem derecesi:**", defects)
        self.assertIn("- **Güven:** bir kez görüldü - kayda girmeden önce yeniden üretin; bulguyu atmayın", defects)
        for old in ("Kahin", "Değerlendirme (PROOF)", "Test eden", "Önem (severity)"):
            self.assertNotIn(old, summary + defects)

    def test_official_turkish_header_keys_and_old_aliases_both_parse(self):
        for key_c, key_t in (("test başlatma belgesi", "test uzmanı"), ("görev", "test eden")):
            f = self.dir / "tr.md"
            f.write_text(f"{key_c}: Sipariş akışını keşfet\n{key_t}: Test Analisti A\nsüre: 30\nKAPSAM: x\n", encoding="utf-8")
            s, errors, _ = sbtm.parse_session(f)
            self.assertEqual(errors, [], key_c)
            self.assertEqual((s["header"]["charter"], s["header"]["tester"]), ("Sipariş akışını keşfet", "Test Analisti A"))


class CharterFieldsTests(unittest.TestCase):
    """Finding 10: charters carry exit criteria, limits and past defects (CTAL-TA v4.0 section 3.4.1)."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.out = self.dir / "charters.md"

    def tearDown(self):
        self.tmp.cleanup()

    def test_done_when_and_must_never_on_every_charter(self):
        p = run("charters", "--requirements", str(FIX / "requirements.json"), "--out", str(self.out))
        self.assertEqual(p.returncode, 0, p.stderr)
        text = self.out.read_text(encoding="utf-8")
        n = text.count("\n## CH-")
        self.assertEqual((text.count("- **Done when:**"), text.count("- **Must never:**")), (n, n))
        money = next(s for s in text.split("## CH-")[1:] if "REQ-001" in s.splitlines()[0])
        self.assertIn("real payment cards or real money movements", money.split("- **Must never:**")[1].splitlines()[0])
        self.assertNotIn("Open defects on this requirement", text)  # no --defects given

    def test_open_defects_are_listed_per_requirement_and_closed_ones_are_not(self):
        d = self.dir / "defects.json"
        d.write_text(json.dumps({"defects": [
            {"id": "BANK-9", "title": "Limit ignores cents", "severity": "high", "status": "open", "requirement_ids": ["REQ-001"]},
            {"id": "BANK-3", "title": "Limit | pipe", "severity": "critical", "status": "resolved", "requirement_ids": ["REQ-001"]},
            {"id": "BANK-5", "title": "Old", "severity": "low", "status": "closed", "requirement_ids": ["REQ-001"]},
            {"id": "BANK-7", "title": "Other", "severity": "low", "status": "open", "requirement_ids": ["REQ-003"]}]}),
            encoding="utf-8")
        p = run("charters", "--requirements", str(FIX / "requirements.json"), "--defects", str(d), "--out", str(self.out))
        self.assertEqual(p.returncode, 0, p.stderr)
        sections = {s.split(" · ")[1]: s for s in self.out.read_text(encoding="utf-8").split("## CH-")[1:]}
        line = next(ln for ln in sections["REQ-001"].splitlines() if "Open defects on this requirement" in ln)
        self.assertIn("BANK-3 (critical, resolved) Limit / pipe; BANK-9 (high, open) Limit ignores cents", line)
        self.assertNotIn("BANK-5", sections["REQ-001"])
        self.assertIn("BANK-7", sections["REQ-003"])
        self.assertNotIn("Open defects on this requirement", sections["REQ-002"])

    def test_unreadable_defects_file_is_a_usage_error(self):
        p = run("charters", "--requirements", str(FIX / "requirements.json"), "--defects", str(self.dir / "none.json"),
                "--out", str(self.out))
        self.assertEqual(p.returncode, 2)
        self.assertFalse(self.out.exists())

    def test_turkish_charters_use_the_official_terms(self):
        p = run("charters", "--requirements", str(FIX / "requirements.json"), "--lang", "tr", "--out", str(self.out))
        self.assertEqual(p.returncode, 0, p.stderr)
        text = self.out.read_text(encoding="utf-8")
        self.assertIn("# Keşif testi başlatma belgeleri (charter)", text)
        self.assertIn("**Test başlatma belgesi (charter):**", text)
        self.assertIn("### Test sonucunu bilenler (oracle", text)
        self.assertIn("- **Ne zaman biter:**", text)
        self.assertIn("- **Asla yapılmaz:**", text)
        for old in ("görev kart", "Kahin", "kahin"):
            self.assertNotIn(old, text)


class GuidanceTests(unittest.TestCase):
    """Findings 2 and 3 in the guidance: no bug gating and no time-percentage rules an agent cannot measure."""

    def test_reference_no_longer_downgrades_unreproduced_bugs(self):
        ref = (SKILL / "references" / "exploratory-testing.md").read_text(encoding="utf-8")
        for gone in ("BUG only for reproduced", "a QUESTION or NOTE if it is not reproduced yet", "write a QUESTION and quote both values",
                     "≥ 75%", "CTFL Syllabus v4.0 (2023)"):
            self.assertNotIn(gone, ref)
        self.assertIn("confidence: seen once", ref)
        self.assertIn("## 17. Full SBTM workflow", ref)

    def test_every_path_named_in_the_skill_exists(self):
        import re
        body = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        for rel in set(re.findall(r"`((?:scripts|references|assets)/[\w./-]+)`", body)):
            self.assertTrue((SKILL / rel).is_file(), rel)
        self.assertNotIn("sbtm.py grid", body)  # not implemented: the skill must not promise it


if __name__ == "__main__":
    unittest.main()
