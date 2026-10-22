import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("doctor", ROOT / "tools/doctor.py")
doctor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(doctor)


class PreflightAndReviewGuard(unittest.TestCase):
    def test_core_does_not_require_node_or_playwright(self):
        with patch.object(doctor.shutil, "which", return_value=None):
            report = doctor.inspect("core")
            self.assertTrue(report["ok"])
            self.assertFalse(next(c for c in report["checks"] if c["name"] == "node")["required"])
            self.assertFalse(doctor.inspect("api")["ok"])

    def test_reviewed_json_is_not_overwritten_by_stale_compact(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            source, output = base / "test.src.md", base / "test.json"
            source.write_text("## TC-001 | Changed\nreq: REQ-001 | pri: m | pol: + | tech: checklist\n1. Act => Expected\n", encoding="utf-8")
            output.write_text('{"custom":"preserved","test_cases":[]}', encoding="utf-8")
            marker = output.with_name(output.name + ".qa-reviewed.json")
            marker.write_text('{"schema_version":1}', encoding="utf-8")
            command = [sys.executable, str(ROOT / "shared/scripts/qa_compact.py"), "tc", str(source), "--out", str(output)]
            before = output.read_bytes()
            result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("reviewed", result.stderr)
            self.assertEqual(output.read_bytes(), before)
            result = subprocess.run(command + ["--replace-reviewed"], capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(output.read_text(encoding="utf-8"))["test_cases"][0]["id"], "TC-001")
            self.assertFalse(marker.exists())


if __name__ == "__main__":
    unittest.main()
