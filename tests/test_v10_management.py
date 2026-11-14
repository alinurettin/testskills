"""0.10.0 regression tests for the management scripts (audit docs/audit-2026-11/gap-management.md).

completion_report.py: blocked is not executed, defect severities are never assumed, deferred defects are
listed, unknown criteria and waivers, risk coverage, automation share of the automation targets.
select_regression.py: breadth-first budget fill, exit 1 when the must tier does not fit, visible residual risk.
plan_facts.py: three-point estimate with named assumptions, entry readiness.
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
SK = ROOT / "skills"
REPORT = SK / "reporting-test-results" / "scripts" / "completion_report.py"
SELECT = SK / "tracing-requirements" / "scripts" / "select_regression.py"
PLAN = SK / "planning-tests" / "scripts" / "plan_facts.py"
RTM = SK / "tracing-requirements" / "scripts" / "build_rtm.py"


def run(script, *args):
    return subprocess.run([sys.executable, str(script), *map(str, args)], capture_output=True, text=True, encoding="utf-8")


def load(path: Path):
    spec = importlib.util.spec_from_file_location("v10_" + path.stem, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def req(n, li=3, im=3, **kw):
    return {"id": f"REQ-{n:03d}", "title": f"Requirement {n}", "text": "t", "type": "functional", "priority": "medium",
            "status": "ready", "source": "s", "risk": {"likelihood": li, "impact": im}, **kw}


def tc(n, reqs, **kw):
    return {"id": f"TC-{n:03d}", "title": f"Test {n}", "requirement_ids": [f"REQ-{r:03d}" for r in reqs],
            "priority": "medium", "polarity": "positive", "technique": "requirements-based", "status": "ready",
            "steps": [{"action": "a", "expected": "e"}], **kw}


def make_qa(tmp, reqs, tests, results, defects=None, criteria=None):
    qa = Path(tmp) / "qa"
    qa.mkdir()
    (qa / "requirements.json").write_text(json.dumps({"language": "en", "requirements": reqs}), encoding="utf-8")
    (qa / "test-cases.json").write_text(json.dumps({"test_cases": tests}), encoding="utf-8")
    (qa / "results.json").write_text(json.dumps({"run": "RC1", "results": results}), encoding="utf-8")
    if defects is not None:
        (qa / "defects.json").write_text(json.dumps({"defects": defects}), encoding="utf-8")
    if criteria is not None:
        (qa / "exit-criteria.json").write_text(json.dumps(criteria), encoding="utf-8")
    return qa


def report(qa, *args):
    p = run(REPORT, "--qa", qa, "--json", "--date", "2026-11-15", *args)
    return p, json.loads(p.stdout)


def states(facts):
    return {e["criterion"]: e["state"] for e in facts["exit_criteria"]}


class BlockedIsNotExecuted(unittest.TestCase):
    """Finding 1: 6 passed + 4 blocked used to give execution 100%, pass rate 100%, both criteria met."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        tests = [tc(i, [1]) for i in range(1, 11)]
        results = {f"TC-{i:03d}": {"status": "passed"} for i in range(1, 7)}
        results.update({f"TC-{i:03d}": {"status": "blocked", "note": "test environment down"} for i in range(7, 11)})
        self.qa = make_qa(self.tmp.name, [req(1)], tests, results,
                          criteria={"min_execution_pct": 95, "min_pass_rate_pct": 95, "max_blocked_pct": 10,
                                    "min_passed_of_planned_pct": 90})

    def tearDown(self):
        self.tmp.cleanup()

    def test_blocked_lowers_execution_and_fails_the_gate(self):
        p, f = report(self.qa)
        m = f["metrics"]
        self.assertEqual((m["executed"], m["passed"], m["blocked"]), (6, 6, 4))
        self.assertEqual((m["execution_pct"], m["blocked_pct"], m["passed_of_planned_pct"]), (60.0, 40.0, 60.0))
        self.assertEqual(m["pass_rate_pct"], 100.0)           # of executed tests only, so it cannot stand alone
        self.assertEqual(states(f), {"min_execution_pct": "not_met", "min_pass_rate_pct": "met",
                                     "max_blocked_pct": "not_met", "min_passed_of_planned_pct": "not_met"})
        self.assertEqual(p.returncode, 1)

    def test_status_report_lists_impediments_and_suspension(self):
        out = self.qa / "status.md"
        p = run(REPORT, "--qa", self.qa, "--kind", "status", "--out", out, "--date", "2026-11-15", "--period", "week 2")
        self.assertEqual(p.returncode, 1)
        md = out.read_text(encoding="utf-8")
        self.assertIn("Blocked: 4/10 (40.0%)", md)
        self.assertIn("Suspension check: 40.0% of the planned tests are blocked (limit 30%)", md)
        self.assertIn("| TC-007 | REQ-001 | test environment down |", md)
        self.assertIn("## New and changed risks", md)
        self.assertIn("week 2", md)

    def test_baseline_shows_what_changed(self):
        base = Path(self.tmp.name) / "base.json"
        run(REPORT, "--qa", self.qa, "--json", "--json-out", base, "--date", "2026-11-08")
        rs = json.loads((self.qa / "results.json").read_text(encoding="utf-8"))
        rs["results"]["TC-007"] = {"status": "failed"}
        (self.qa / "results.json").write_text(json.dumps(rs), encoding="utf-8")
        _, f = report(self.qa, "--baseline", base)
        ch = f["changes_since_baseline"]
        self.assertEqual({r["metric"]: r["change"] for r in ch["metrics"]}["failed"], 1)
        self.assertEqual(ch["verdicts"], [{"id": "REQ-001", "baseline": "blocked", "now": "failed"}])

    def test_unknown_result_status_is_reported_not_dropped(self):
        rs = {"results": {"TC-001": {"status": "PASSED "}, "TC-002": {"status": "ok"}}}
        (self.qa / "results.json").write_text(json.dumps(rs), encoding="utf-8")
        p, f = report(self.qa)
        self.assertEqual((f["metrics"]["passed"], f["metrics"]["not_run"]), (1, 9))
        self.assertIn("TC-002 has unknown status 'ok'", p.stderr)


class DefectCriteriaNeverPassSilently(unittest.TestCase):
    """Finding 2: no severity, 'Critical ' and a deferred critical all gave 'critical <= 0: met'."""
    CRIT = {"max_open_defects": {"critical": 0, "high": 0}}

    def qa(self, tmp, defects, criteria=None, results=None):
        return make_qa(tmp, [req(1)], [tc(1, [1]), tc(2, [1])],
                       results or {"TC-001": {"status": "failed", "defects": ["D-1"]}, "TC-002": {"status": "passed"}},
                       defects=defects, criteria=criteria or self.CRIT)

    def test_severity_is_normalised(self):
        with tempfile.TemporaryDirectory() as d:
            p, f = report(self.qa(d, [{"id": "D-1", "severity": "Critical ", "status": " Open"}]))
            self.assertEqual(f["metrics"]["open_defects_by_severity"], {"critical": 1})
            self.assertEqual(states(f), {"max_open_defects.critical": "not_met", "max_open_defects.high": "met"})
            self.assertEqual(p.returncode, 1)

    def test_missing_or_invalid_severity_makes_every_limit_unknown(self):
        for sev in (None, "", "blocker"):
            with self.subTest(sev=sev), tempfile.TemporaryDirectory() as d:
                p, f = report(self.qa(d, [{"id": "D-1", "severity": sev, "status": "open"}]))
                self.assertEqual(states(f), {"max_open_defects.critical": "unknown", "max_open_defects.high": "unknown"})
                self.assertEqual(p.returncode, 1)
                self.assertIn("D-1 has no valid severity", p.stderr)

    def test_a_known_breach_is_not_met_even_when_another_severity_is_unknown(self):
        with tempfile.TemporaryDirectory() as d:
            _, f = report(self.qa(d, [{"id": "D-1", "severity": "critical", "status": "open"},
                                      {"id": "D-2", "status": "open"}]))
            self.assertEqual(states(f), {"max_open_defects.critical": "not_met", "max_open_defects.high": "unknown"})

    def test_unknown_status_counts_as_open(self):
        with tempfile.TemporaryDirectory() as d:
            p, f = report(self.qa(d, [{"id": "D-1", "severity": "high", "status": "triage"}]))
            self.assertEqual(states(f)["max_open_defects.high"], "not_met")
            self.assertIn("unknown status 'triage'", p.stderr)

    def test_unregistered_defect_key_is_open_with_unknown_severity(self):
        with tempfile.TemporaryDirectory() as d:
            p, f = report(self.qa(d, [{"id": "D-9", "severity": "low", "status": "closed"}]))
            self.assertEqual(f["defects"]["unregistered_keys"], ["D-1"])
            self.assertEqual(states(f)["max_open_defects.critical"], "unknown")
            self.assertIn("not in defects.json", p.stderr)

    def test_deferred_defects_are_listed_as_known_defects_shipped(self):
        with tempfile.TemporaryDirectory() as d:
            defects = [{"id": "D-1", "title": "Wrong total", "severity": "critical", "status": "deferred", "test_ids": ["TC-001"]}]
            qa = self.qa(d, defects, criteria={"max_open_defects": {"critical": 0}, "max_deferred_defects": {"critical": 0}})
            p, f = report(qa)
            self.assertEqual([x["id"] for x in f["defects"]["known_defects_shipped"]], ["D-1"])
            self.assertEqual(f["defects"]["known_defects_shipped"][0]["requirement_ids"], ["REQ-001"])
            self.assertEqual(states(f), {"max_open_defects.critical": "met", "max_deferred_defects.critical": "not_met"})
            self.assertEqual(p.returncode, 1)
            out = Path(d) / "r.md"
            run(REPORT, "--qa", qa, "--out", out, "--date", "2026-11-15")
            md = out.read_text(encoding="utf-8")
            self.assertIn("### Known defects shipped (deferred)", md)
            self.assertIn("| D-1 | critical | Wrong total | REQ-001 |", md)

    def test_defect_metrics(self):
        with tempfile.TemporaryDirectory() as d:
            defects = [{"id": "D-1", "severity": "high", "status": "closed", "reopened_count": 1, "detected_in": "system test",
                        "requirement_ids": ["REQ-001"]},
                       {"id": "D-2", "severity": "low", "status": "rejected"},
                       {"id": "D-3", "severity": "low", "status": "duplicate"},
                       {"id": "D-4", "severity": "medium", "status": "closed", "detected_in": "production",
                        "requirement_ids": ["REQ-001"]}]
            _, f = report(self.qa(d, defects, results={"TC-001": {"status": "passed"}}))
            m = f["defects"]["metrics"]
            self.assertEqual((m["reported"], m["valid"], m["rejected"], m["duplicate"]), (4, 2, 1, 1))
            self.assertEqual((m["reopen_rate_pct"], m["rejection_rate_pct"], m["ddp_pct"]), (50.0, 25.0, 50.0))
            self.assertEqual(m["clusters"], [{"requirement": "REQ-001", "defects": 2}])

    def test_ddp_is_not_invented_without_production_defects(self):
        with tempfile.TemporaryDirectory() as d:
            _, f = report(self.qa(d, [{"id": "D-1", "severity": "low", "status": "closed"}]))
            self.assertIsNone(f["defects"]["metrics"]["ddp_pct"])
            self.assertIn("not measurable yet", f["defects"]["metrics"]["ddp_note"])


class CriteriaStatesAndWaivers(unittest.TestCase):
    def qa(self, tmp, criteria, reqs=None, results=None):
        return make_qa(tmp, reqs or [req(1, 4, 5), req(2, 3, 4), req(3, 2, 3)],
                       [tc(1, [1]), tc(2, [2]), tc(3, [3])],
                       results if results is not None else
                       {"TC-001": {"status": "passed"}, "TC-002": {"status": "failed"}, "TC-003": {"status": "passed"}},
                       criteria=criteria)

    def test_misspelt_criterion_is_unknown_not_skipped(self):
        with tempfile.TemporaryDirectory() as d:
            p, f = report(self.qa(d, {"min_pass_rate": 50, "min_execution_pct": "95"}))
            self.assertEqual(states(f), {"min_pass_rate": "unknown", "min_execution_pct": "unknown"})
            self.assertEqual(p.returncode, 1)
            self.assertIn("unknown criterion 'min_pass_rate'", p.stderr)

    def test_risk_coverage_per_level(self):
        with tempfile.TemporaryDirectory() as d:
            p, f = report(self.qa(d, {"all_critical_requirements_passed": True,
                                      "min_requirements_passed_pct": {"critical": 100, "high": 100, "medium": 90, "low": 50}}))
            rc = f["risk_coverage"]
            self.assertEqual((rc["critical"]["passed"], rc["high"]["failed"], rc["medium"]["passed_pct"]), (1, 1, 100.0))
            self.assertEqual(states(f), {"all_critical_requirements_passed": "met",
                                         "min_requirements_passed_pct.critical": "met",
                                         "min_requirements_passed_pct.high": "not_met",     # the old gate saw only critical
                                         "min_requirements_passed_pct.medium": "met",
                                         "min_requirements_passed_pct.low": "met"})          # no low requirement: nothing to fail
            self.assertEqual(p.returncode, 1)

    def test_not_run_high_risk_requirement_counts_as_not_completely_tested(self):
        with tempfile.TemporaryDirectory() as d:
            _, f = report(self.qa(d, {"min_requirements_passed_pct": {"high": 100}}, results={"TC-001": {"status": "passed"}}))
            self.assertEqual(f["risk_coverage"]["high"]["not_completely_tested"], 1)
            self.assertEqual(states(f)["min_requirements_passed_pct.high"], "not_met")

    def test_unrated_requirement_makes_risk_criteria_unknown(self):
        with tempfile.TemporaryDirectory() as d:
            reqs = [req(1, 4, 5), {"id": "REQ-002", "title": "x", "text": "t", "status": "ready"}, req(3)]
            _, f = report(self.qa(d, {"all_critical_requirements_passed": True}, reqs=reqs,
                                  results={k: {"status": "passed"} for k in ("TC-001", "TC-002", "TC-003")}))
            self.assertEqual(states(f), {"all_critical_requirements_passed": "unknown"})

    def waiver(self, **kw):
        return {"criterion": "min_pass_rate_pct", "approved_by": "A. Product Owner", "date": "2026-11-14",
                "reason": "REQ-002 ships behind a feature flag", "expires": "2026-12-01", **kw}

    def test_valid_waiver_is_a_fourth_state(self):
        with tempfile.TemporaryDirectory() as d:
            qa = self.qa(d, {"min_pass_rate_pct": 95, "min_execution_pct": 100, "waivers": [self.waiver()]})
            p, f = report(qa)
            e = f["exit_criteria"][0]
            self.assertEqual((e["state"], e["met"], e["waiver"]["approved_by"], e["waiver"]["was"]),
                             ("waived", False, "A. Product Owner", "not_met"))
            self.assertEqual(p.returncode, 1)                      # a waiver alone never opens the gate
            p, f = report(qa, "--allow-waived")
            self.assertEqual((p.returncode, f["gate"]["met"], f["gate"]["waived"]), (0, 1, 1))
            out = Path(d) / "r.md"
            run(REPORT, "--qa", qa, "--out", out, "--date", "2026-11-15")
            md = out.read_text(encoding="utf-8")
            self.assertIn("⚠ waived by A. Product Owner until 2026-12-01", md)
            self.assertIn("1 waived (accepted risk)", md)
            self.assertIn("Reason: REQ-002 ships behind a feature flag (was: not met)", md)

    def test_expired_or_incomplete_waiver_does_not_count(self):
        cases = {"expired": self.waiver(expires="2026-11-14"), "missing approved_by": self.waiver(approved_by=" "),
                 "missing reason": self.waiver(reason=""), "missing expires": self.waiver(expires=None),
                 "not a date": self.waiver(expires="next month"), "no such criterion": self.waiver(criterion="min_pass_rate")}
        for name, w in cases.items():
            with self.subTest(name), tempfile.TemporaryDirectory() as d:
                p, f = report(self.qa(d, {"min_pass_rate_pct": 95, "waivers": [w]}), "--allow-waived")
                self.assertEqual(states(f), {"min_pass_rate_pct": "not_met"})
                self.assertEqual(p.returncode, 1)
                self.assertIn("waiver for", p.stderr)

    def test_waiver_on_a_met_criterion_changes_nothing(self):
        with tempfile.TemporaryDirectory() as d:
            p, f = report(self.qa(d, {"min_pass_rate_pct": 50, "waivers": [self.waiver()]}))
            self.assertEqual(states(f), {"min_pass_rate_pct": "met"})
            self.assertEqual(p.returncode, 0)


class AutomationShare(unittest.TestCase):
    """Finding 10: two automated runs alone used to give automation 100%."""

    def test_share_of_automation_targets(self):
        with tempfile.TemporaryDirectory() as d:
            tests = [tc(i, [1], automation={"candidate": i <= 8}) for i in range(1, 11)]
            results = {"TC-001": {"status": "passed", "source": "playwright"}, "TC-002": {"status": "failed", "source": "ci"},
                       "TC-003": {"status": "not-run", "source": "playwright", "note": "test.fixme skeleton"},
                       "TC-009": {"status": "passed", "source": "manual"}}
            p, f = report(make_qa(d, [req(1)], tests, results, criteria={"min_automation_pct": 50}))
            m = f["metrics"]
            self.assertEqual((m["automated_tests"], m["automation_targets"], m["automation_pct"]), (2, 8, 25.0))
            self.assertEqual(m["automated_of_executed_pct"], 66.7)      # the earlier definition, kept under its own name
            self.assertEqual(states(f), {"min_automation_pct": "not_met"})

    def test_same_rule_in_both_scripts(self):
        rep, sel = load(REPORT), load(SELECT)
        for res in ({"status": "passed", "source": "ci"}, {"status": "passed", "source": "manual"}, {"status": "passed"},
                    {"status": "not-run", "source": "playwright"}, {"status": "failed", "source": "Playwright "}):
            self.assertEqual(rep.is_automated(res), sel.is_automated(res), res)
        self.assertTrue(sel.is_automated({"status": "passed", "source": "ci"}))
        self.assertFalse(sel.is_automated({"status": "not-run", "source": "playwright"}))


class RiskLevelMatrix(unittest.TestCase):
    """Finding 7: one rule in four scripts; impact 5 is at least high, with likelihood >= 3 critical."""

    def test_four_copies_agree_and_overrides_apply(self):
        mods = [load(p) for p in (REPORT, SELECT, PLAN, RTM)]
        grid = [{"risk": {"likelihood": li, "impact": im}} for li in range(0, 6) for im in range(0, 6)]
        grid += [{"priority": p} for p in ("critical", "high", "medium", "low", None)]
        grid += [{"risk": {"likelihood": "4", "impact": "5"}}, {"risk": {"likelihood": "x", "impact": 5}}, {"risk": None}]
        for r in grid:
            got = {m.risk_of(r) for m in mods}
            self.assertEqual(len(got), 1, r)
        f = mods[0].risk_of
        self.assertEqual(f({"risk": {"likelihood": 1, "impact": 5}}), (5, "high"))
        self.assertEqual(f({"risk": {"likelihood": 3, "impact": 5}}), (15, "critical"))
        self.assertEqual(f({"risk": {"likelihood": 5, "impact": 3}}), (15, "high"))
        self.assertEqual(f({"risk": {"likelihood": "4", "impact": "5"}}), (20, "critical"))
        self.assertEqual(f({"priority": "high"}), (12, "high"))
        self.assertEqual(f({}), (0, "-"))


class RegressionBudget(unittest.TestCase):
    """Finding 3: depth-first fill with a skip; all selected tests on one requirement, exit 0, no warning."""

    def files(self, d, reqs, tests, results=None):
        d = Path(d)
        (d / "req.json").write_text(json.dumps({"requirements": reqs}), encoding="utf-8")
        (d / "tc.json").write_text(json.dumps({"test_cases": tests}), encoding="utf-8")
        (d / "res.json").write_text(json.dumps({"results": results or {}}), encoding="utf-8")
        return ["--requirements", d / "req.json", "--tests", d / "tc.json", "--results", d / "res.json",
                "--out", d / "o.md", "--json", d / "o.json"]

    def sel(self, d, base, *extra):
        p = run(SELECT, *base, *extra)
        return p, json.loads((Path(d) / "o.json").read_text(encoding="utf-8")), (Path(d) / "o.md").read_text(encoding="utf-8")

    def test_breadth_first_spreads_the_budget_over_requirements(self):
        with tempfile.TemporaryDirectory() as d:
            reqs = [req(1, 3, 3), req(2, 2, 4), req(3, 2, 3)]          # all in the could tier
            tests = [tc(1, [1]), tc(2, [1]), tc(3, [1]), tc(4, [2]), tc(5, [2]), tc(6, [3])]
            base = self.files(d, reqs, tests)
            p, data, md = self.sel(d, base, "--level", "could", "--budget", "3")
            self.assertEqual(p.returncode, 0, p.stderr)
            self.assertEqual([x["id"] for x in data["selected"]], ["TC-001", "TC-004", "TC-006"])
            self.assertEqual(data["requirements_without_selected_test"], [])
            p, data, md = self.sel(d, base, "--level", "could", "--budget", "3", "--order", "depth")
            self.assertEqual([x["id"] for x in data["selected"]], ["TC-001", "TC-002", "TC-003"])
            self.assertEqual([u["id"] for u in data["requirements_without_selected_test"]], ["REQ-002", "REQ-003"])
            self.assertIn("## Requirements with no selected test (residual risk)", md)
            self.assertIn("- REQ-002 Requirement 2 (medium 8; all tests left out by the budget)", md)

    def test_must_tier_over_the_minute_budget_exits_1_and_says_so(self):
        with tempfile.TemporaryDirectory() as d:
            reqs = [req(1, 4, 4), req(2, 2, 2)]
            tests = [tc(1, [1]), tc(2, [1]), tc(3, [2])]
            results = {"TC-001": {"status": "passed", "duration_ms": 50 * 60000}}
            base = self.files(d, reqs, tests, results)
            p, data, md = self.sel(d, base, "--changed", "REQ-001", "--level", "could", "--budget-minutes", "30")
            self.assertEqual(p.returncode, 1)
            self.assertIn("MUST tier exceeds budget: 1 of 2 must tests left out (TC-001)", p.stderr)
            self.assertIn("MUST tier exceeds budget", md)
            self.assertEqual((data["must_left_out"], data["must_tier_fits"]), (["TC-001"], False))
            left = {x["id"]: x for x in data["left_out"]}
            self.assertEqual((left["TC-001"]["left_reason"], left["TC-001"]["cost_minutes"]), ("minutes", 50.0))
            self.assertIn("needs 50 min, 30 min left", md)
            p, data, _ = self.sel(d, base, "--changed", "REQ-001", "--level", "could", "--budget-minutes", "60")
            self.assertEqual((p.returncode, data["must_tier_fits"]), (0, True))

    def test_changed_requirement_without_tests_is_residual_risk(self):
        with tempfile.TemporaryDirectory() as d:
            base = self.files(d, [req(1), req(2, 4, 5)], [tc(1, [1])])
            p, data, md = self.sel(d, base, "--changed", "REQ-002")
            self.assertEqual(p.returncode, 0)
            self.assertEqual([(u["id"], u["why"], u["level"]) for u in data["requirements_without_selected_test"]],
                             [("REQ-002", "none", "critical"), ("REQ-001", "level", "medium")])

    def test_ci_sourced_test_is_not_listed_as_manual(self):
        with tempfile.TemporaryDirectory() as d:
            results = {"TC-001": {"status": "passed", "source": "ci"}, "TC-002": {"status": "passed", "source": "playwright"}}
            base = self.files(d, [req(1)], [tc(1, [1]), tc(2, [1]), tc(3, [1])], results)
            _, data, md = self.sel(d, base, "--changed", "REQ-001", "--lang", "tr")
            self.assertIn("- ci: TC-001", md)
            self.assertIn('--grep "@TC-002"', md)
            self.assertIn("(1): TC-003", md)

    def test_string_risk_values_and_impact_5_are_high_risk(self):
        with tempfile.TemporaryDirectory() as d:
            reqs = [req(1), {**req(2), "risk": {"likelihood": "4", "impact": "4"}}, req(3, 1, 5)]
            base = self.files(d, reqs, [tc(1, [1]), tc(2, [2]), tc(3, [3])])
            _, data, _ = self.sel(d, base, "--level", "should")
            self.assertEqual({x["id"]: x["reasons"] for x in data["selected"]},
                             {"TC-002": ["HIGH_RISK"], "TC-003": ["HIGH_RISK"]})

    def test_unreadable_input_is_exit_2(self):
        with tempfile.TemporaryDirectory() as d:
            p = run(SELECT, "--requirements", Path(d) / "none.json", "--tests", Path(d) / "none.json", "--out", Path(d) / "o.md")
            self.assertEqual(p.returncode, 2)


class ThreePointEstimate(unittest.TestCase):
    """Finding 4: one point, full rerun in cycle 2, automation at zero cost."""

    def facts(self, d, results=None, *args):
        tests = [tc(i, [1], automation={"candidate": i <= 2}) for i in range(1, 5)]       # 4 tests x (5 + 2) = 28 min
        qa = make_qa(d, [req(1, 4, 5), req(2, 4, 4, status="clarification-needed")], tests, results or {})
        (qa / "clarifications.md").write_text("| Q-001 | blocking | REQ-002 | ? | open |\n| Q-002 | blocking | REQ-001 | ? | answered |\n",
                                              encoding="utf-8")
        p = run(PLAN, "--qa", qa, "--format", "json", *args)
        self.assertEqual(p.returncode, 0, p.stderr)
        return json.loads(p.stdout), qa

    def test_range_formula_and_named_assumptions(self):
        with tempfile.TemporaryDirectory() as d:
            f, qa = self.facts(d, None, "--cycles", "2", "--retest-share", "0.5", "--defect-handling-pct", "25",
                               "--min-per-test", "55", "--min-per-step", "5")       # 4 h per cycle
            ee = f["effort_estimate"]
            tp = ee["three_point"]
            self.assertEqual(ee["most_likely_breakdown"]["execution_hours"], 6.0)    # 4 h x 1.5, not a full rerun
            self.assertEqual((tp["optimistic_hours"], tp["most_likely_hours"], tp["pessimistic_hours"]), (5.2, 7.5, 13.5))
            self.assertEqual((tp["expected_hours"], tp["sd_hours"]), (8.1, 1.4))      # (a + 4m + b) / 6, (b - a) / 6
            self.assertEqual(tp["range_hours"], [6.8, 9.5])                     # 8.125 -/+ 1.375
            self.assertTrue(any("cycles: 2" in x for x in ee["assumptions"]))
            self.assertTrue(any("not included" in x for x in ee["assumptions"]))
            au = ee["automation"]
            self.assertEqual((au["candidates_not_automated"], au["build_hours"], au["manual_hours_saved_per_cycle"],
                              au["break_even_cycles"]), (2, 4.0, 2.0, 2))
            md = run(PLAN, "--qa", qa).stdout
            self.assertIn("Test execution effort (three-point)", md)
            self.assertIn("assumption: defect reporting and verification: 25% of execution time", md)
            self.assertIn("REQ-001 Requirement 1 (critical; L4 × I5 = 20)", md)

    def test_measured_durations_extrapolate_and_automated_tests_are_not_manual(self):
        with tempfile.TemporaryDirectory() as d:
            results = {f"TC-00{i}": {"status": "passed", "duration_ms": 14 * 60000} for i in (1, 2, 3)}
            results["TC-004"] = {"status": "passed", "source": "playwright", "duration_ms": 900}
            f, _ = self.facts(d, results)
            b = f["effort_estimate"]["basis"]
            self.assertEqual((b["manual_tests"], b["automated_tests"], b["measured_manual_tests"], b["extrapolation_factor"]),
                             (3, 1, 3, 2.0))
            self.assertEqual(f["effort_estimate"]["most_likely_breakdown"]["cycle_1_execution_hours"], 0.7)   # 3 x 14 min
            self.assertTrue(any("extrapolating from 3 manual results" in x for x in f["effort_estimate"]["assumptions"]))

    def test_entry_readiness(self):
        with tempfile.TemporaryDirectory() as d:
            f, _ = self.facts(d)
            er = f["entry_readiness"]
            self.assertEqual((er["requirements_ready_pct"], er["blocking_questions_open"], er["blocking_open_ids"]),
                             (50.0, 1, ["Q-001"]))
            self.assertEqual(er["high_critical_without_tests"], ["REQ-002"])

    def test_invalid_factor_is_a_usage_error(self):
        with tempfile.TemporaryDirectory() as d:
            _, qa = self.facts(d)
            self.assertEqual(run(PLAN, "--qa", qa, "--optimistic", "1.2").returncode, 2)


if __name__ == "__main__":
    unittest.main()
