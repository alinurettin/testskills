"""0.10.0 regression tests: k6 generator and results converter, ASVS 5.0 placement, automation lint.

The k6 behaviour tests run the generated script in Node against stand-in modules
(tests/fixtures/v10-automation/k6-stub). They are skipped when Node is not installed; k6 itself is not needed.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SK = ROOT / "skills"
NFR = SK / "testing-nonfunctional"
PW = SK / "automating-with-playwright" / "scripts"
STUB = Path(__file__).resolve().parent / "fixtures" / "v10-automation" / "k6-stub"
NODE = shutil.which("node")


def run_py(script, *args):
    return subprocess.run([sys.executable, str(script), *map(str, args)], capture_output=True, text=True, encoding="utf-8")


def base_spec(**over) -> dict:
    spec = {"id": "DS-900", "title": "perf", "requirement_ids": ["REQ-006"], "test_id": "TC-027", "profile": "load",
            "target": {"type": "arrival-rate", "rate": 10, "unit": "iterations"}, "duration": "10m", "ramp": "2m",
            "thresholds": {"p95_ms": 800, "error_rate": 0.01},
            "requests": [{"name": "apply_coupon", "method": "POST", "path": "/api/coupon", "json": {"code": "X"}}]}
    spec.update(over)
    return spec


def generate(tmp: Path, spec: dict, *extra):
    (tmp / "spec.json").write_text(json.dumps(spec, ensure_ascii=False), encoding="utf-8")
    return run_py(NFR / "scripts" / "generate_k6.py", tmp / "spec.json", "--out", tmp / "perf.mjs", *extra)


def simulate(tmp: Path, scenario: dict) -> dict:
    """Run tmp/perf.mjs in Node with the k6 stand-in; returns calls, samples and handleSummary() output."""
    mod = tmp / "node_modules" / "k6"
    if not mod.exists():
        mod.mkdir(parents=True)
        for f in STUB.iterdir():
            if f.name != "runner.mjs":
                shutil.copy(f, mod / f.name)
        shutil.copy(STUB / "runner.mjs", tmp / "runner.mjs")
    (tmp / "scenario.json").write_text(json.dumps(scenario), encoding="utf-8")
    r = subprocess.run([NODE, "runner.mjs", "perf.mjs", "scenario.json"], cwd=tmp, capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        raise AssertionError(r.stderr)
    return json.loads(r.stdout)


class K6WorkloadModelTests(unittest.TestCase):
    def test_missing_model_inputs_stop_the_run(self):
        cases = {"target": lambda s: s.pop("target"),
                 "error_rate": lambda s: s["thresholds"].pop("error_rate"),
                 "think_time_s or pacing_s": lambda s: s.update(target={"type": "vus", "vus": 200})}
        for needle, mutate in cases.items():
            with self.subTest(needle), tempfile.TemporaryDirectory() as d:
                spec = base_spec()
                mutate(spec)
                r = generate(Path(d), spec)
                self.assertEqual(r.returncode, 2, r.stdout)
                self.assertIn(needle, r.stderr)
                self.assertFalse((Path(d) / "perf.mjs").exists())  # nothing half-written

    def test_open_model_states_rates_and_requires_no_dropped_iterations(self):
        with tempfile.TemporaryDirectory() as d:
            spec = base_spec(target={"type": "arrival-rate", "rate": 50},
                             requests=[{"name": "get_cart", "path": "/api/cart"},
                                       {"name": "apply_coupon", "method": "POST", "path": "/api/coupon", "json": {"code": "X"}}])
            r = generate(Path(d), spec)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("model: OPEN", r.stdout)
            self.assertIn("50 journeys/s = 100 HTTP requests/s", r.stdout)  # the rate is journeys, not requests
            self.assertIn("QUESTION: target.rate 50/s is read as journeys per second", r.stdout)
            js = (Path(d) / "perf.mjs").read_text(encoding="utf-8")
            self.assertIn('"dropped_iterations": ["count==0"]', js)
            self.assertNotIn("maxVUs", js)
            self.assertIn("'p(99)'", js)  # in the summary, not only in thresholds
            self.assertEqual(generate(Path(d), spec, "--strict").returncode, 1)  # open questions

    def test_requests_per_second_is_converted_to_journeys(self):
        with tempfile.TemporaryDirectory() as d:
            spec = base_spec(target={"type": "arrival-rate", "rate": 30, "unit": "requests"},
                             requests=[{"name": "a", "path": "/a"}, {"name": "b", "path": "/b"}, {"name": "c", "path": "/c"}])
            r = generate(Path(d), spec)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("10 journeys/s = 30 HTTP requests/s", r.stdout)
            self.assertIn("{ duration: \"10m\", target: 10 }", (Path(d) / "perf.mjs").read_text(encoding="utf-8"))

    def test_closed_model_needs_think_time_and_reports_throughput_range(self):
        with tempfile.TemporaryDirectory() as d:
            spec = base_spec(target={"type": "vus", "vus": 200, "throughput_per_s": 20}, think_time_s=[5, 9], pacing_s=10)
            r = generate(Path(d), spec)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("model: CLOSED (200 virtual users)", r.stdout)
            self.assertIn("pacing 10 s", r.stdout)
            js = (Path(d) / "perf.mjs").read_text(encoding="utf-8")
            self.assertIn("executor: 'ramping-vus'", js)
            self.assertNotIn("dropped_iterations", js.split("thresholds: {")[1])
            self.assertIn('"qa_steady_iterations": ["count>=11400"]', js)  # 20/s x 600 s x 0.95
            self.assertIn("think(5, 9);", js)

    def test_stress_asserts_recovery_not_the_overload(self):
        with tempfile.TemporaryDirectory() as d:
            r = generate(Path(d), base_spec(profile="stress"))
            self.assertEqual(r.returncode, 0, r.stderr)
            th = (Path(d) / "perf.mjs").read_text(encoding="utf-8").split("thresholds: {")[1].split("};")[0]
            self.assertIn("qa_recovery_ms_apply_coupon", th)
            self.assertIn("qa_baseline_failed", th)
            self.assertNotIn("qa_overload", th)
            self.assertNotIn("dropped_iterations", th)

    @unittest.skipUnless(NODE, "node not installed")
    def test_generated_scripts_are_valid_javascript(self):
        for name in ("k6-perf.json", "k6-mix.json"):
            with self.subTest(name), tempfile.TemporaryDirectory() as d:
                out = Path(d) / "perf.mjs"
                r = run_py(NFR / "scripts" / "generate_k6.py", NFR / "assets" / "spec-examples" / name, "--out", out)
                self.assertEqual(r.returncode, 0, r.stderr)
                chk = subprocess.run([NODE, "--check", str(out)], capture_output=True, text=True)
                self.assertEqual(chk.returncode, 0, chk.stderr)

    @unittest.skipUnless(NODE, "node not installed")
    def test_expected_4xx_is_not_an_error_and_ramps_are_not_measured(self):
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            spec = base_spec(requests=[{"name": "reuse_coupon", "method": "POST", "path": "/api/coupon/{{code}}",
                                        "json": {"code": "{{code}}", "qty": "{{qty:number}}"}, "expect_status": 422}],
                             data={"file": "rows.csv", "pick": "unique"})
            (tmp / "rows.csv").write_text("code,qty\nYAZ 10,2\nKIS20,3\n", encoding="utf-8")
            self.assertEqual(generate(tmp, spec).returncode, 0)
            out = simulate(tmp, {"run_ms": 780000, "iterations": [
                {"at_s": 10, "iteration": 0, "statuses": {"reuse_coupon": 422}, "durations": {"reuse_coupon": 5000}},  # ramp-up
                {"at_s": 300, "iteration": 1, "statuses": {"reuse_coupon": 422}, "durations": {"reuse_coupon": 120}},
                {"at_s": 310, "iteration": 2, "statuses": {"reuse_coupon": 422}}]})                                    # no row left
            s = out["samples"]
            self.assertEqual(s["qa_steady_ms_reuse_coupon"]["samples"], [120])   # the 5 s ramp-up sample is excluded
            self.assertEqual(s["qa_steady_failed"]["samples"], [False])           # 422 was expected: not a failure
            self.assertEqual(out["calls"][0]["expected"], [422])                  # http_req_failed agrees
            self.assertEqual(out["calls"][0]["url"], "http://localhost:3000/api/coupon/YAZ%2010")
            self.assertEqual(json.loads(out["calls"][1]["body"]), {"code": "KIS20", "qty": 3})
            self.assertIn("test data exhausted", out["aborted"])                  # unique rows are never reused
            self.assertTrue(all(c["tags"]["phase"] in ("ramp_up", "steady") for c in out["checks"]))

    @unittest.skipUnless(NODE, "node not installed")
    def test_fast_errors_do_not_improve_the_percentile(self):
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            self.assertEqual(generate(tmp, base_spec()).returncode, 0)
            its = [{"at_s": 200 + i, "statuses": {"apply_coupon": 500}, "durations": {"apply_coupon": 5}} for i in range(9)]
            its.append({"at_s": 250, "durations": {"apply_coupon": 900}})
            out = simulate(tmp, {"run_ms": 780000, "iterations": its})
            self.assertEqual(out["samples"]["qa_steady_ms_apply_coupon"]["samples"], [900])
            summary = json.loads(out["summary"]["DS-900-summary.json"])
            self.assertFalse(summary["metrics"]["qa_steady_ms_apply_coupon"]["thresholds"]["p(95)<800"]["ok"])
            self.assertFalse(summary["metrics"]["qa_steady_failed"]["thresholds"]["rate<0.01"]["ok"])


def summary(profile="load", run_ms=780000, p95=500.0, count=6000, failed_rate=0.001, dropped=0) -> dict:
    return {"qa_suite": {"spec_id": "DS-900", "test_id": "TC-027", "requirement_ids": ["REQ-006"], "profile": profile,
                         "model": "open", "verdict_phases": ["steady"], "measured_phases": ["steady"],
                         "phases": [{"name": "ramp_up", "start_s": 0, "end_s": 120}, {"name": "steady", "start_s": 120, "end_s": 720},
                                    {"name": "ramp_down", "start_s": 720, "end_s": 780}],
                         "planned_duration_s": 780, "target": {"journeys_per_s": 10}},
            "state": {"testRunDurationMs": run_ms},
            "metrics": {"qa_steady_ms_apply_coupon": {"type": "trend", "values": {"count": count, "p(95)": p95, "p(99)": p95 * 1.5},
                                                      "thresholds": {"p(95)<800": {"ok": p95 < 800}}},
                        "qa_steady_failed": {"type": "rate", "values": {"rate": failed_rate},
                                             "thresholds": {"rate<0.01": {"ok": failed_rate < 0.01}}},
                        "qa_steady_iterations": {"type": "counter", "values": {"count": count},
                                                 "thresholds": {"count>0": {"ok": count > 0}}},
                        "dropped_iterations": {"type": "counter", "values": {"count": dropped},
                                               "thresholds": {"count==0": {"ok": dropped == 0}}}}}


class K6ResultsTests(unittest.TestCase):
    SCRIPT = NFR / "scripts" / "k6_results.py"

    def convert(self, doc: dict, *extra, existing: dict | None = None):
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            (tmp / "s.json").write_text(json.dumps(doc), encoding="utf-8")
            if existing:
                (tmp / "results.json").write_text(json.dumps(existing), encoding="utf-8")
            r = run_py(self.SCRIPT, tmp / "s.json", "--out", tmp / "results.json", *extra)
            res = json.loads((tmp / "results.json").read_text(encoding="utf-8")) if (tmp / "results.json").exists() else {}
            return r, res.get("results", {})

    def test_passed_run_reaches_the_tc_and_keeps_other_entries(self):
        r, res = self.convert(summary(), "--strict", existing={"run": "x", "results": {
            "TC-001": {"status": "passed"}, "TC-027": {"status": "failed", "defects": ["SHOP-9"]}}})
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(res["TC-027"]["status"], "passed")
        self.assertEqual(res["TC-027"]["source"], "k6")
        self.assertEqual(res["TC-027"]["defects"], ["SHOP-9"])
        self.assertEqual(res["TC-027"]["performance"]["achieved_journeys_per_s"], 10.0)
        self.assertEqual(res["TC-027"]["performance"]["phases"]["steady"]["requests"]["apply_coupon"]["p95_ms"], 500.0)
        self.assertEqual(res["TC-001"], {"status": "passed"})

    def test_breached_threshold_fails_with_the_observed_value(self):
        r, res = self.convert(summary(p95=950.0, dropped=12), "--strict")
        self.assertEqual(r.returncode, 1)
        self.assertEqual(res["TC-027"]["status"], "failed")
        self.assertTrue(any("qa_steady_ms_apply_coupon: p(95)<800 breached (count=6000, p(95)=950" in e for e in res["TC-027"]["errors"]))
        self.assertTrue(any("dropped_iterations" in e for e in res["TC-027"]["errors"]))

    def test_no_false_green(self):
        for label, doc, extra, status in (
                ("smoke is not a verdict", summary(profile="smoke"), (), "not-run"),
                ("run ended early", summary(run_ms=200000), (), "blocked"),
                ("no successful sample", summary(count=0) | {}, (), "blocked"),
                ("k6 crashed", summary(), ("--exit-code", "107"), "blocked")):
            with self.subTest(label):
                r, res = self.convert(doc, *extra)
                self.assertEqual(r.returncode, 0, r.stderr)
                self.assertEqual(res["TC-027"]["status"], status, res["TC-027"]["note"])

    def test_unusable_input_is_rejected(self):
        legacy_export = {"metrics": {"http_req_duration": {"avg": 1, "thresholds": {"p(95)<800": False}}}}
        self.assertEqual(self.convert(legacy_export)[0].returncode, 2)
        no_tc = summary()
        no_tc["qa_suite"]["test_id"] = ""
        r, res = self.convert(no_tc)
        self.assertEqual((r.returncode, res), (2, {}))
        self.assertEqual(self.convert(no_tc, "--test", "TC-031")[1]["TC-031"]["status"], "passed")
        r, _ = self.convert(summary(), "--tests", ROOT / "tests" / "fixtures" / "coupon" / "test-cases.json")
        self.assertEqual(r.returncode, 2)  # TC-027 is not a known test case: it would never reach the RTM
        self.assertIn("never reach the RTM", r.stderr)


class AsvsPlacementTests(unittest.TestCase):
    """Chapter numbers checked against OWASP ASVS 5.0.0 (github.com/OWASP/ASVS, tag v5.0.0) on 2026-11-15."""

    def setUp(self):
        data = json.loads((NFR / "assets" / "asvs5-chapters.json").read_text(encoding="utf-8"))
        self.ch = {c["id"]: c for c in data["chapters"]}
        self.levels = data["levels"]

    def where(self, needle: str) -> set[str]:
        return {cid for cid, c in self.ch.items() if any(needle.lower() in i.lower() for i in c["ideas"])}

    def test_ideas_sit_in_their_asvs5_chapter(self):
        self.assertEqual(self.where("rate limiting"), {"V2"})        # V2.4 Anti-automation, was V4
        self.assertEqual(self.where("localStorage"), {"V14"})        # V14.3.3 / V14.2.1, was V3
        self.assertEqual(self.where("SCA scan"), {"V15"})            # V15.1-V15.2, was V13
        self.assertEqual(self.where("mass assignment"), {"V15"})     # V15.3.3, was V8
        self.assertEqual(self.where("HSTS"), {"V3"})                 # V3.4.1, was V12
        for c in self.ch.values():
            self.assertEqual(len(c["ideas"]), len(c["ideas_tr"]), c["id"])

    def test_level_1_is_not_described_as_black_box(self):
        self.assertNotIn("black-box", self.levels["L1"])

    def test_api_selection_still_gets_rate_limiting_and_mass_assignment(self):
        r = run_py(NFR / "scripts" / "nfr_checklist.py", "asvs", "--features", "api", "--req", "REQ-013", "--start", "100")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertRegex(r.stdout, r"ASVS V2 Validation and Business Logic – Verify rate limiting")
        self.assertRegex(r.stdout, r"ASVS V15 Secure Coding and Architecture – Verify field-level rules")
        self.assertNotRegex(r.stdout, r"ASVS V4 [^\n]*rate limiting")


SPEC_HEAD = "import { test, expect } from './fixtures';\n"


def spec_test(tid: str, body: str) -> str:
    return (f"test('{tid} t', {{ tag: ['@{tid}'] }}, async ({{ page }}) => {{\n"
            f"  await test.step('1. do', async () => {{\n{body}\n  }});\n}});\n")


class CheckAutomationAssertionTests(unittest.TestCase):
    def run_check(self, specs: dict[str, str], *extra):
        with tempfile.TemporaryDirectory() as d:
            tmp = Path(d)
            ids = ["TC-001", "TC-002", "TC-003", "TC-004"]
            (tmp / "tc.json").write_text(json.dumps({"test_cases": [
                {"id": i, "title": i, "priority": "high", "automation": {"candidate": True}} for i in ids]}), encoding="utf-8")
            (tmp / "tests").mkdir()
            for name, text in specs.items():
                (tmp / "tests" / name).write_text(text, encoding="utf-8")
            r = run_py(PW / "check_automation.py", "--tests", tmp / "tc.json", "--specs", tmp / "tests",
                       "--out", tmp / "cov.md", *extra)
            return r, (tmp / "cov.md").read_text(encoding="utf-8")

    def test_a_test_without_expect_is_not_automated(self):
        spec = (SPEC_HEAD
                + spec_test("TC-001", "    await page.getByRole('button', { name: 'Uygula' }).click();")
                + spec_test("TC-002", "    await expect(page.getByTestId('discount')).toHaveText('80,00 TL');")
                + spec_test("TC-003", "    // expect(page).toHaveURL('/x') is still to do\n    await page.goto('/x');")
                + spec_test("TC-004", "    await cartPage.expectSummary('80,00', '720,00');"))
        r, report = self.run_check({"a.spec.ts": spec}, "--strict")
        self.assertIn("automated 2 (50.0%)", r.stdout)
        self.assertIn("no assertion 2", r.stdout)
        self.assertEqual(r.returncode, 1)
        section = report.split("## No assertion")[1].split("## ")[0]
        self.assertIn("| TC-001 |", section)
        self.assertIn("| TC-003 |", section)  # an expect inside a comment does not count
        self.assertNotIn("| TC-002 |", section)

    def test_data_driven_cases_use_the_loop_body(self):
        cases = "const cases1 = [\n" + "".join(f"  {{ id: 'TC-00{i}', tag: ['@TC-00{i}'] }},\n" for i in (1, 2, 3)) + "];\n"
        loop = ("for (const c of cases1) {\n  test(`${c.id} t`, { tag: c.tag }, async ({ page }) => {\n"
                "    await expect(page.getByRole('alert')).toHaveText(c.id);\n  });\n}\n")
        r, _ = self.run_check({"a.spec.ts": SPEC_HEAD + cases + loop + spec_test("TC-004", "    await expect(page).toHaveURL('/');")}, "--strict")
        self.assertIn("automated 4 (100.0%)", r.stdout)
        self.assertIn("no assertion 0", r.stdout)
        self.assertEqual(r.returncode, 0)
        r, _ = self.run_check({"a.spec.ts": SPEC_HEAD + cases + loop.replace("await expect(page.getByRole('alert')).toHaveText(c.id);",
                                                                             "await page.goto('/');")})
        self.assertIn("automated 0 (0.0%)", r.stdout)
        self.assertIn("no assertion 3", r.stdout)


if __name__ == "__main__":
    unittest.main()
