"""Tests for the testing-mobile-apps skill scripts (standard library only).

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
SKILL = ROOT / "skills" / "testing-mobile-apps"
SCRIPT = SKILL / "scripts" / "mobile_checklist.py"
JUNIT = SKILL / "scripts" / "junit_results.py"
DEVICES = SKILL / "assets" / "devices-example.json"
FIX = Path(__file__).resolve().parent / "fixtures" / "coupon"
CATEGORIES = {"functional", "ui", "api", "integration", "data", "security", "performance", "accessibility",
              "usability", "compatibility", "localization", "reliability"}


def load(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem + "_mobile", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


qc = load(SKILL / "scripts" / "qa_compact.py")
mc = load(SCRIPT)


def run(*args):
    return subprocess.run([sys.executable, *map(str, args)], capture_output=True, text=True, encoding="utf-8")


class MobileChecklistTests(unittest.TestCase):
    def generate(self, d, *extra, name="m.src.md"):
        out = Path(d) / name
        r = run(SCRIPT, "--req", "REQ-030", "--out", out, *extra)
        self.assertEqual(r.returncode, 0, r.stderr)
        text = out.read_text(encoding="utf-8")
        _, items, errors = qc.parse(text, "tc")
        self.assertEqual(errors, [])
        self.assertEqual(qc.validate(items, "tc"), [])
        return text, items

    def test_all_capabilities_both_languages_parse_cleanly(self):
        with tempfile.TemporaryDirectory() as d:
            for lang in ("en", "tr"):
                text, items = self.generate(d, "--platform", "both", "--capabilities", "all", "--lang", lang,
                                            name=f"{lang}.src.md")
                ids = [t["id"] for t in items]
                titles = [t["title"] for t in items]
                self.assertEqual(len(ids), len(set(ids)))
                self.assertEqual(len(titles), len(set(titles)), "titles must be unique")
                self.assertNotIn("{via}", text)
                for t in items:
                    self.assertIn(t["category"], CATEGORIES)
                    self.assertIn(t["technique"], {"checklist", "error-guessing"})
                    self.assertEqual(t["requirement_ids"], ["REQ-030"])
                    self.assertEqual(t["tags"][0], "mobile")
                    self.assertTrue({"android", "ios"} & set(t["tags"]))
                    self.assertTrue(all(s["expected"] for s in t["steps"]))
                self.assertIn("# QUESTION:", text)

    def test_core_set_is_always_on(self):
        with tempfile.TemporaryDirectory() as d:
            _, items = self.generate(d, "--platform", "android")
            tags = [set(t["tags"]) for t in items]
            self.assertTrue(all("core" in t for t in tags))
            for needed in ("upgrade", "process-death", "rotation", "interruption", "offline", "font-scale",
                           "screen-reader", "storage", "idempotency"):
                self.assertTrue(any(needed in t for t in tags), needed)
            self.assertFalse(any("payments" in t for t in tags))

    def test_capabilities_add_their_checks(self):
        with tempfile.TemporaryDirectory() as d:
            _, base = self.generate(d, "--platform", "both", name="a.md")
            _, more = self.generate(d, "--platform", "both", "--capabilities", "payments,deeplinks", name="b.md")
            self.assertGreater(len(more), len(base))
            tags = [set(t["tags"]) for t in more]
            self.assertTrue(any("payments" in t and "idempotency" in t for t in tags))
            self.assertTrue(any("masvs-platform" in t and "deeplinks" in t for t in tags))
            self.assertFalse(any("biometrics" in t for t in tags))

    def test_platform_variants(self):
        with tempfile.TemporaryDirectory() as d:
            ios, ios_items = self.generate(d, "--platform", "ios", "--capabilities", "location,tracking", name="i.md")
            andr, and_items = self.generate(d, "--platform", "android", "--capabilities", "location,tracking", name="a.md")
            both, _ = self.generate(d, "--platform", "both", "--capabilities", "location,tracking", name="b.md")
            self.assertIn("Allow Once", ios)
            self.assertIn("App Tracking Transparency", ios)
            self.assertNotIn("Only this time", ios)
            self.assertIn("Only this time", andr)
            self.assertIn("Allow all the time", andr)
            self.assertNotIn("App Tracking Transparency", andr)
            self.assertTrue(all("android" not in t["tags"] for t in ios_items))
            self.assertTrue(all("ios" not in t["tags"] for t in and_items))
            self.assertIn("Allow Once", both)
            self.assertIn("Only this time", both)
            self.assertIn("Android: ", both)       # both platform hints in shared steps

    def test_turkish_output(self):
        with tempfile.TemporaryDirectory() as d:
            text, _ = self.generate(d, "--platform", "both", "--lang", "tr")
            self.assertIn("Önceki üretim sürümünden güncelleme", text)
            self.assertIn("uçak modu", text)       # Turkish platform hint, not the English one
            self.assertNotIn("airplane mode", text)

    def test_numbering_continues(self):
        with tempfile.TemporaryDirectory() as d:
            _, items = self.generate(d, "--tests", FIX / "test-cases.json")
            existing = json.loads((FIX / "test-cases.json").read_text(encoding="utf-8"))["test_cases"]
            top = max(int(t["id"].split("-")[1]) for t in existing)
            self.assertEqual(int(items[0]["id"].split("-")[1]), top + 1)
            _, items = self.generate(d, "--start", "500", name="s.md")
            self.assertEqual(items[0]["id"], "TC-500")

    def test_usage_errors(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "x.md"
            self.assertEqual(run(SCRIPT, "--req", "REQ-1", "--capabilities", "teleport", "--out", out).returncode, 2)
            self.assertEqual(run(SCRIPT, "--out", out).returncode, 2)                     # --req missing
            self.assertEqual(run(SCRIPT, "--devices", DEVICES).returncode, 2)             # no --matrix-out
            self.assertFalse(out.exists())

    def test_catalogue_integrity(self):
        cat = mc.load_catalogue()
        seen = set()
        for c in cat["checks"]:
            self.assertNotIn(c["id"], seen)
            seen.add(c["id"])
            self.assertIn(c["platform"], ("both", "android", "ios"))
            self.assertIn(c["pri"], ("c", "h", "m", "l"))
            self.assertIn(c["tech"], ("cl", "eg"))
            self.assertIn(c["auto"], cat["auto"])
            self.assertTrue(set(c["caps"]) <= set(cat["capabilities"]) | {"core"}, c["id"])
            self.assertEqual(len(c["en"]["steps"]), len(c["tr"]["steps"]), c["id"])
            self.assertEqual(set(c.get("via", {})), set(c.get("via_tr", {})), c["id"])
            uses_via = any("{via}" in s[0] + s[1] for s in c["en"]["steps"] + c["tr"]["steps"])
            self.assertEqual(uses_via, bool(c.get("via")), c["id"])


class DeviceMatrixTests(unittest.TestCase):
    def devices(self):
        devs, errors = mc.validate_devices(json.loads(DEVICES.read_text(encoding="utf-8")))
        self.assertEqual(errors, [])
        return devs

    def test_edges_and_target(self):
        devs = [d for d in self.devices() if d["os"] == "android"]
        sel = mc.select_devices(devs, 80)
        names = {d["name"]: r for d, r in sel}
        oldest = min(devs, key=lambda d: mc.version_key(d["version"]))
        self.assertIn(oldest["name"], names)
        self.assertTrue(any("tablet" in r for r in names.values()))
        self.assertTrue(any("foldable" in r for r in names.values()))
        self.assertTrue(any("smallest" in r for r in names.values()))
        self.assertGreaterEqual(sum(d["share"] for d, _ in sel), 80)
        # minimal: dropping the last share-picked device falls below the target
        share_picked = [d for d, r in sel if r == ["share"]]
        self.assertLess(sum(d["share"] for d, _ in sel) - share_picked[-1]["share"], 80)

    def test_edge_reuses_selected_device(self):
        devs = [{"name": "Old small", "os": "ios", "version": "16", "share": 2.0, "form_factor": "phone", "width_dp": 375},
                {"name": "Big new", "os": "ios", "version": "26", "share": 60.0, "form_factor": "phone", "width_dp": 430},
                {"name": "Mid", "os": "ios", "version": "18", "share": 30.0, "form_factor": "phone", "width_dp": 375}]
        sel = mc.select_devices(devs, 50)
        self.assertEqual([d["name"] for d, _ in sel], ["Old small", "Big new"])
        self.assertEqual(sel[0][1], ["oldest", "smallest"])

    def test_matrix_file_deterministic_and_warns(self):
        with tempfile.TemporaryDirectory() as d:
            outs = []
            for i in range(2):
                out = Path(d) / f"m{i}.md"
                r = run(SCRIPT, "--devices", DEVICES, "--matrix-out", out, "--target-share", "80")
                self.assertEqual(r.returncode, 0, r.stderr)
                outs.append(out.read_text(encoding="utf-8"))
            self.assertEqual(outs[0], outs[1])
            self.assertIn("## Android", outs[0])
            self.assertIn("## iOS", outs[0])
            r = run(SCRIPT, "--devices", DEVICES, "--matrix-out", Path(d) / "hi.md", "--target-share", "99",
                    "--platform", "ios")
            self.assertEqual(r.returncode, 0)
            self.assertIn("Target not reached", r.stdout)

    def test_invalid_devices(self):
        with tempfile.TemporaryDirectory() as d:
            bad = Path(d) / "bad.json"
            bad.write_text(json.dumps([{"name": "X", "os": "symbian", "version": "1", "share": 5},
                                       {"name": "Y", "os": "ios", "version": "17"}]), encoding="utf-8")
            r = run(SCRIPT, "--devices", bad, "--matrix-out", Path(d) / "m.md")
            self.assertEqual(r.returncode, 1)
            self.assertIn("os must be android or ios", r.stderr)
            self.assertIn("missing share", r.stderr)
            over = Path(d) / "over.json"
            over.write_text(json.dumps([{"name": "A", "os": "ios", "version": "17", "share": 70},
                                        {"name": "B", "os": "ios", "version": "18", "share": 50}]), encoding="utf-8")
            self.assertEqual(run(SCRIPT, "--devices", over, "--matrix-out", Path(d) / "m.md").returncode, 1)


class JUnitResultsTests(unittest.TestCase):
    XML = """<?xml version="1.0" encoding="UTF-8"?>
<testsuites><testsuite name="Test Suite" tests="4">
  <testcase id="a" name="TC-101 Checkout draft survives process death" classname="flows" time="12.5"/>
  <testcase name="TC-102 Offline message" classname="flows" time="3"><failure message="Assertion is false: id: offline_banner is visible"/></testcase>
  <testcase name="test_TC103_deepLinkColdStart" classname="com.example.DeepLinkTest" time="1"><skipped/></testcase>
  <testcase name="Untagged smoke" classname="flows" time="1"/>
</testsuite></testsuites>"""

    def test_merge_per_device(self):
        with tempfile.TemporaryDirectory() as d:
            rep1, rep2, out = Path(d) / "a.xml", Path(d) / "b.xml", Path(d) / "results.json"
            rep1.write_text(self.XML, encoding="utf-8")
            rep2.write_text(self.XML.replace('<failure message="Assertion is false: id: offline_banner is visible"/>', ""),
                            encoding="utf-8")
            out.write_text(json.dumps({"run": "RC1", "results": {
                "TC-050": {"status": "passed"}, "TC-101": {"status": "failed", "defects": ["SHOP-9"]}}}), encoding="utf-8")
            r = run(JUNIT, rep1, "--device", "Pixel 8 / Android 16", "--source", "maestro", "--out", out)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("no TC-###", r.stdout)
            r = run(JUNIT, rep2, "--device", "iPhone 15 / iOS 26", "--source", "maestro", "--out", out)
            self.assertEqual(r.returncode, 0, r.stderr)
            res = json.loads(out.read_text(encoding="utf-8"))["results"]
            self.assertEqual(res["TC-050"], {"status": "passed"})                 # manual entry kept
            self.assertEqual(res["TC-101"]["status"], "passed")
            self.assertEqual(res["TC-101"]["defects"], ["SHOP-9"])                # defect key kept
            self.assertEqual(res["TC-102"]["status"], "failed")                   # failed on one device
            self.assertEqual(res["TC-102"]["projects"], {"Pixel 8 / Android 16": "failed", "iPhone 15 / iOS 26": "passed"})
            self.assertEqual(res["TC-103"]["status"], "skipped")                  # TC103 in a method name
            self.assertNotIn("Untagged smoke", json.dumps(res))

    def test_unreadable_report(self):
        with tempfile.TemporaryDirectory() as d:
            bad = Path(d) / "bad.xml"
            bad.write_text("<testsuites><testcase", encoding="utf-8")
            self.assertEqual(run(JUNIT, bad, "--out", Path(d) / "r.json").returncode, 2)


class MaestroTemplateTests(unittest.TestCase):
    def test_template_carries_tc_id(self):
        text = (SKILL / "assets" / "maestro-flow-template.yaml").read_text(encoding="utf-8")
        name = next(line for line in text.splitlines() if line.startswith("name:"))
        self.assertRegex(name, r'^name: "TC-\d{3,} ')
        tc = name.split('"')[1].split()[0]
        self.assertIn(f"  - {tc}", text)
        self.assertIn("\n---\n", text)


if __name__ == "__main__":
    unittest.main()
