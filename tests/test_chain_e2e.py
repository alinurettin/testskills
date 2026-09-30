"""End-to-end regression: REQ -> TC -> results.json -> RTM -> completion report across the newer skills.

One qa/ workspace in a temp dir, no network. The chain, in the order a team runs it:
  1. qa/test-cases.src.md starts with a hand-written test (TC-001, the deliberately thin REQ-006)
  2. openapi_tests.py evals/trial-api/api/openapi.json --req-map qa/req-map.json --tests qa/test-cases.json
     -> qa/design/api-tests.src.md (3 REQs) + automation/tests/api-contract.spec.ts; appended, qa_compact.py tc
  3. reconcile.py --compact-out (trial-migration mapping, 2 REQs from the same req-map) --tests; appended, qa_compact.py
  4. results.json: a manual entry, a synthetic Playwright JSON report of the generated spec (pw_results.py),
     a defect key linked by the tester, then reconcile.py --results on the trial extracts (--tc-map test-cases.json)
  5. build_rtm.py and completion_report.py over everything

Run:  python -m unittest tests.test_chain_e2e -v
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SK = ROOT / "skills"
FIX = Path(__file__).resolve().parent / "fixtures" / "chain"
OPENAPI = SK / "testing-apis" / "scripts" / "openapi_tests.py"
QA_COMPACT = SK / "designing-test-cases" / "scripts" / "qa_compact.py"
RECONCILE = SK / "testing-data-migrations" / "scripts" / "reconcile.py"
PW_RESULTS = SK / "automating-with-playwright" / "scripts" / "pw_results.py"
RTM = SK / "tracing-requirements" / "scripts" / "build_rtm.py"
REPORT = SK / "reporting-test-results" / "scripts" / "completion_report.py"
API_DOC = ROOT / "evals" / "trial-api" / "api" / "openapi.json"
TRIAL = ROOT / "evals" / "trial-migration"
MAPPING = Path(__file__).resolve().parent / "fixtures" / "testing-data-migrations" / "trial-mapping.json"

API_REQS = ("REQ-001", "REQ-002", "REQ-003")
MIGRATION_REQS = ("REQ-004", "REQ-005")
THIN_REQ = "REQ-006"
NOT_RUN_REQ = "REQ-003"  # its operation is not part of the Playwright run below
DEFECT = "BANK-17"
RUN = "Sprint 3 RC1"
# evals/trial-migration answer key: 8 of the 11 checks fail, and which requirement each check traces to (req-map.json)
MIGRATION_FAILED = {"row_count", "key_set", "duplicate_keys", "column:full_name", "column:birth_date",
                    "column:balance", "column:status", "total:balance"}
MIGRATION_PASSED = {"column:branch", "column:email", "coverage"}
CHECK_REQ = {"row_count": "REQ-004", "key_set": "REQ-004", "duplicate_keys": "REQ-004", "total:balance": "REQ-004",
             "column:full_name": "REQ-005", "column:birth_date": "REQ-005", "column:branch": "REQ-005",
             "column:balance": "REQ-005", "column:status": "REQ-005", "column:email": "REQ-005",
             "coverage": "REQ-005"}

SPEC_TEST = re.compile(r'^\s*test\("((?:[^"\\]|\\.)*)",\s*\{\s*tag:\s*\[([^\]]*)\]')
SPEC_DESCRIBE = re.compile(r'^test\.describe\("((?:[^"\\]|\\.)*)"')


def run(script: Path, *args, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(script), *map(str, args)], capture_output=True, text=True,
                          encoding="utf-8", errors="replace", cwd=cwd)


def jload(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def append(dst: Path, src: Path) -> None:
    text = dst.read_text(encoding="utf-8").rstrip("\n") + "\n\n" + src.read_text(encoding="utf-8")
    dst.write_text(text, encoding="utf-8", newline="\n")


def spec_tests(spec: str) -> list[dict]:
    """(describe, title, tags, line, skeleton) of every test in the generated Playwright spec."""
    out, describe = [], ""
    lines = spec.splitlines()
    for no, line in enumerate(lines, 1):
        d = SPEC_DESCRIBE.match(line)
        if d:
            describe = json.loads(f'"{d.group(1)}"')
            continue
        t = SPEC_TEST.match(line)
        if not t:
            continue
        title = json.loads(f'"{t.group(1)}"')
        tags = [x.lstrip("@") for x in re.findall(r"'([^']+)'", t.group(2))]
        tid = next(x for x in tags if re.fullmatch(r"TC-\d{3,}", x))
        body = []
        for nxt in lines[no:]:
            if SPEC_TEST.match(nxt) or SPEC_DESCRIBE.match(nxt):
                break
            body.append(nxt)
        skeleton = f"QA Suite skeleton {tid}" in "\n".join(body)
        out.append({"describe": describe, "title": title, "tags": tags, "line": no, "id": tid, "skeleton": skeleton})
    return out


def playwright_report(tests: list[dict], plan: dict[str, str], file: str) -> dict:
    """A Playwright 'json' reporter document for the tests in plan: passed | failed | fixme."""
    suites: dict[str, list] = {}
    for t in tests:
        kind = plan.get(t["id"])
        if kind is None:
            continue
        if kind == "passed":
            test = {"projectName": "api", "status": "expected", "annotations": [],
                    "results": [{"status": "passed", "duration": 140}]}
        elif kind == "failed":
            test = {"projectName": "api", "status": "unexpected", "annotations": [],
                    "results": [{"status": "failed", "duration": 310, "errors": [
                        {"message": "Error: \u001b[2mexpect(\u001b[22mreceived).toBe(expected)\n\nExpected: 400\nReceived: 201"}]}]}
        else:
            test = {"projectName": "api", "status": "skipped",
                    "annotations": [{"type": "fixme", "description": f"QA Suite skeleton {t['id']}"}],
                    "results": [{"status": "skipped", "duration": 0}]}
        suites.setdefault(t["describe"], []).append(
            {"title": t["title"], "tags": t["tags"], "file": file, "line": t["line"], "tests": [test]})
    return {"config": {}, "stats": {"startTime": "2026-09-30T08:00:00.000Z"},
            "suites": [{"title": file, "file": file, "specs": [],
                        "suites": [{"title": d, "file": file, "specs": s} for d, s in suites.items()]}]}


def header_map(path: Path) -> dict:
    maps = [json.loads(line.split(":", 1)[1]) for line in path.read_text(encoding="utf-8").splitlines()
            if line.startswith("# reconcile-tc-map:")]
    assert len(maps) == 1, maps
    return maps[0]


def verdict(statuses: list[str]) -> str:
    if not statuses:
        return "-"
    if "failed" in statuses:
        return "failed"
    if all(s == "passed" for s in statuses):
        return "passed"
    if all(s in ("not-run", "skipped") for s in statuses):
        return "not-run"
    return "in-progress"


class RequirementToCompletionChainTests(unittest.TestCase):
    """The whole chain runs once in setUpClass; each test checks one link of it."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.d = d = Path(cls.tmp.name)
        qa = cls.qa = d / "qa"
        (qa / "design").mkdir(parents=True)
        (qa / "migration").mkdir()
        (d / "automation" / "tests").mkdir(parents=True)
        for name in ("requirements.json", "req-map.json", "test-cases.src.md", "exit-criteria.json"):
            shutil.copy(FIX / name, qa / name)
        shutil.copy(FIX / "results-manual.json", qa / "results.json")
        cls.procs: dict[str, subprocess.CompletedProcess] = {}

        def step(name: str, script: Path, *args, ok=(0,)):
            p = run(script, *args, cwd=d)
            cls.procs[name] = p
            if p.returncode not in ok:
                raise AssertionError(f"chain broken at '{name}' (exit {p.returncode}):\n{p.stdout}\n{p.stderr}")
            return p

        # 1. hand-written tests -> JSON (numbering source for the generators)
        step("compact-manual", QA_COMPACT, "tc", "qa/test-cases.src.md", "--out", "qa/test-cases.json")
        # 2. API contract tests, requirements from the shared req-map, numbering continues after TC-001
        step("openapi", OPENAPI, API_DOC, "--req-map", "qa/req-map.json", "--tests", "qa/test-cases.json",
             "--lang", "tr", "--out", "qa/design/api-tests.src.md",
             "--spec-out", "automation/tests/api-contract.spec.ts")
        append(qa / "test-cases.src.md", qa / "design" / "api-tests.src.md")
        step("compact-api", QA_COMPACT, "tc", "qa/test-cases.src.md", "--out", "qa/test-cases.json")
        # 3. migration reconciliation checks (design mode: mapping only), numbering continues after the API tests
        step("reconcile-design", RECONCILE, "--key", "customer_id", "--mapping", MAPPING, "--sum", "balance",
             "--group-by", "branch", "--object", "customers", "--compact-out", "qa/design/migration-customers.src.md",
             "--req-map", "qa/req-map.json", "--tests", "qa/test-cases.json", "--lang", "tr")
        append(qa / "test-cases.src.md", qa / "design" / "migration-customers.src.md")
        step("compact-all", QA_COMPACT, "tc", "qa/test-cases.src.md", "--out", "qa/test-cases.json")
        cls.tests = jload(qa / "test-cases.json")["test_cases"]
        cls.by_req = defaultdict(list)
        for t in cls.tests:
            for rid in t["requirement_ids"]:
                cls.by_req[rid].append(t["id"])
        cls.tc_map = header_map(qa / "design" / "migration-customers.src.md")["checks"]

        # 4a. synthetic Playwright run of the generated spec: REQ-001 and REQ-002 operations, one REQ-002 failure
        spec = (d / "automation" / "tests" / "api-contract.spec.ts").read_text(encoding="utf-8")
        cls.spec_tests = spec_tests(spec)
        by_id = {t["id"]: t for t in cls.tests}
        cls.skeletons = {t["id"] for t in cls.spec_tests if t["skeleton"]}
        cls.failed_api = next(t["id"] for t in cls.spec_tests if not t["skeleton"]
                              and by_id[t["id"]]["requirement_ids"] == ["REQ-002"]
                              and by_id[t["id"]]["polarity"] == "negative")
        cls.plan = {}
        for t in cls.spec_tests:
            if NOT_RUN_REQ in by_id[t["id"]]["requirement_ids"]:
                continue
            cls.plan[t["id"]] = ("fixme" if t["skeleton"] else "failed" if t["id"] == cls.failed_api else "passed")
        report = d / "automation" / "test-results" / "results.json"
        report.parent.mkdir(parents=True)
        report.write_text(json.dumps(playwright_report(cls.spec_tests, cls.plan, "api-contract.spec.ts")),
                          encoding="utf-8", newline="\n")
        step("pw_results", PW_RESULTS, report, "--out", "qa/results.json", "--run", RUN)
        # 4b. the tester links the defect found by the failed contract test
        res = jload(qa / "results.json")
        res["results"][cls.failed_api]["defects"] = [DEFECT]
        (qa / "results.json").write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n", encoding="utf-8",
                                         newline="\n")
        # 4c. mock migration run: per-check verdicts into the same results.json, TC map from design_ref
        step("reconcile-run", RECONCILE, "--source", TRIAL / "legacy_customers.csv",
             "--target", TRIAL / "new_customers.csv", "--encoding-source", "cp1254", "--delimiter-source", ";",
             "--key", "customer_id", "--mapping", MAPPING, "--sum", "balance", "--group-by", "branch",
             "--object", "customers", "--lang", "tr", "--out", "qa/migration/rec-mock1.md",
             "--results", "qa/results.json", "--tc-map", "qa/test-cases.json", ok=(1,))
        cls.results = jload(qa / "results.json")

        # 5. RTM and completion report
        step("rtm", RTM, "--requirements", "qa/requirements.json", "--tests", "qa/test-cases.json",
             "--results", "qa/results.json", "--out-dir", "qa", "--json")
        cls.rtm = jload(qa / "rtm.json")
        cls.rows = {r["id"]: r for r in cls.rtm["rows"]}
        cls.gaps = {(g["id"], g["code"]) for g in cls.rtm["gaps"]}
        cls.facts = json.loads(step("report-json", REPORT, "--qa", "qa", "--json", ok=(1,)).stdout)
        step("report-md", REPORT, "--qa", "qa", "--out", "qa/completion-report.md", ok=(1,))
        cls.report_md = (qa / "completion-report.md").read_text(encoding="utf-8")

        # expected per-TC status, derived from the plan above and the migration answer key
        cls.expected = {tid: "not-run" for tid in (t["id"] for t in cls.tests)}
        cls.expected["TC-001"] = "passed"
        cls.expected.update({tid: "not-run" if k == "fixme" else k for tid, k in cls.plan.items()})
        cls.expected.update({tid: "failed" if cid in MIGRATION_FAILED else "passed" for cid, tid in cls.tc_map.items()})

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    # --- design: REQ -> TC -------------------------------------------------------------------------------------

    def test_generated_tests_trace_to_their_own_requirements(self):
        ids = [t["id"] for t in self.tests]
        self.assertEqual(len(ids), len(set(ids)), "TC IDs collide after appending the generated files")
        self.assertEqual(ids[0], "TC-001")
        self.assertEqual(self.by_req[THIN_REQ], ["TC-001"])
        api = [t for t in self.tests if "api" in t["tags"]]
        self.assertEqual({t["id"] for t in api}, {t["id"] for t in self.spec_tests})  # spec and JSON share TC IDs
        self.assertEqual(ids[1], api[0]["id"], "openapi_tests.py --tests did not continue after TC-001")
        self.assertEqual({r for t in api for r in t["requirement_ids"]}, set(API_REQS))
        self.assertTrue(all(len(t["requirement_ids"]) == 1 for t in api))
        for rid in API_REQS:  # one REQ per operation group: each has its own happy path and negative tests
            pol = {t["polarity"] for t in api if rid in t["requirement_ids"]}
            self.assertEqual(pol, {"positive", "negative"}, rid)

    def test_migration_checks_are_appended_after_the_api_tests(self):
        self.assertEqual(set(self.tc_map), set(CHECK_REQ))
        api_max = max(int(t["id"][3:]) for t in self.tests if "api" in t["tags"])
        self.assertEqual(sorted(int(v[3:]) for v in self.tc_map.values()), list(range(api_max + 1, api_max + 12)))
        by_id = {t["id"]: t for t in self.tests}
        for cid, tid in self.tc_map.items():
            self.assertEqual(by_id[tid]["requirement_ids"], [CHECK_REQ[cid]], cid)
            self.assertEqual(by_id[tid]["design_ref"], f"reconcile:customers:{cid}")
        self.assertNotIn("unknown key", self.procs["reconcile-design"].stderr)  # the API sections are ignored

    # --- execution: TC -> results.json -------------------------------------------------------------------------

    def test_results_merge_manual_playwright_and_reconcile_entries(self):
        res = self.results["results"]
        self.assertEqual(self.results["run"], RUN)  # reconcile keeps the run label
        self.assertEqual(res["TC-001"], {"status": "passed", "source": "manual",
                                         "note": "Tester: synthetic run, test mailbox"})
        self.assertEqual(res[self.failed_api]["defects"], [DEFECT])  # linked by hand, kept by reconcile
        self.assertEqual(res[self.failed_api]["source"], "playwright")
        self.assertEqual(res[self.failed_api]["errors"], ["Error: expect(received).toBe(expected)"])  # ANSI stripped
        for tid in self.skeletons & set(self.plan):
            self.assertEqual((res[tid]["status"], res[tid]["note"]), ("not-run", "not implemented (test.fixme skeleton)"))
        for cid, tid in self.tc_map.items():
            self.assertEqual(res[tid]["source"], "reconcile", cid)
            self.assertIn("rec-mock1.md", res[tid]["note"])
        got = {tid: e["status"] for tid, e in res.items()}
        want = {tid: s for tid, s in self.expected.items() if not (s == "not-run" and tid not in self.plan)}
        self.assertEqual(got, want)  # REQ-003 tests were not in this run: no entry, counted as not-run
        self.assertIn("results: 11 test cases", self.procs["reconcile-run"].stdout)
        self.assertIn("failed 8, passed 3", self.procs["reconcile-run"].stdout)

    # --- RTM ---------------------------------------------------------------------------------------------------

    def test_rtm_computes_coverage_and_execution_per_requirement(self):
        self.assertEqual(self.rtm["errors"], [])
        self.assertEqual([w for w in self.rtm["warnings"] if w.startswith("results.json")], [])
        m = self.rtm["metrics"]
        self.assertEqual((m["requirements_in_scope"], m["requirements_covered"], m["coverage_pct"]), (6, 6, 100.0))
        self.assertEqual(m["tests_active"], len(self.tests))
        self.assertEqual(m["orphans"], 0)
        for rid, row in self.rows.items():
            self.assertEqual(row["tests"], self.by_req[rid], rid)
            self.assertEqual(row["execution"], verdict([self.expected[t] for t in self.by_req[rid]]), rid)
        self.assertEqual(self.rows["REQ-002"]["execution"], "failed")
        self.assertEqual(self.rows["REQ-002"]["defects"], [DEFECT])
        self.assertEqual(self.rows[NOT_RUN_REQ]["execution"], "not-run")
        self.assertEqual(self.rows[THIN_REQ]["execution"], "passed")
        for rid in MIGRATION_REQS:
            self.assertEqual(self.rows[rid]["execution"], "failed", rid)
        self.assertEqual(len(self.rows["REQ-004"]["tests"]), 4)
        self.assertEqual(len(self.rows["REQ-005"]["tests"]), 7)
        rev = {r["id"]: r["result"] for r in self.rtm["reverse"]}
        self.assertEqual(rev, self.expected)

    def test_rtm_gaps_flag_the_thin_requirement_and_the_failures(self):
        self.assertIn((THIN_REQ, "THIN"), self.gaps)
        self.assertIn((THIN_REQ, "NO_NEGATIVE"), self.gaps)
        self.assertEqual((self.rows[THIN_REQ]["positive"], self.rows[THIN_REQ]["negative"]), (1, 0))
        for rid in API_REQS:  # per-operation mapping: no false THIN/NO_NEGATIVE on the API requirements
            self.assertFalse({c for r, c in self.gaps if r == rid} & {"UNCOVERED", "THIN", "NO_NEGATIVE"}, rid)
        for rid in ("REQ-002", *MIGRATION_REQS):
            self.assertIn((rid, "FAILED"), self.gaps)
        for rid in MIGRATION_REQS:  # generated reconciliation checks are positive by design (SKILL.md)
            self.assertIn((rid, "NO_NEGATIVE"), self.gaps)
        self.assertNotIn("UNCOVERED", {c for _, c in self.gaps})
        md = (self.qa / "rtm.md").read_text(encoding="utf-8")
        self.assertRegex(md, rf"\| {THIN_REQ} \| [^|]+ \| THIN \|")
        self.assertIn("coverage 6/6 (100.0%)", self.procs["rtm"].stdout)

    # --- completion report -------------------------------------------------------------------------------------

    def test_completion_report_counts_the_migration_failures(self):
        m = self.facts["metrics"]
        executed = [t for t, s in self.expected.items() if s in ("passed", "failed")]
        passed = sum(1 for s in self.expected.values() if s == "passed")
        failed = sum(1 for s in self.expected.values() if s == "failed")
        self.assertEqual(failed, len(MIGRATION_FAILED) + 1)
        self.assertEqual((m["tests"], m["executed"], m["passed"], m["failed"], m["not_run"]),
                         (len(self.tests), len(executed), passed, failed, len(self.tests) - len(executed)))
        self.assertEqual(m["coverage_pct"], 100.0)
        self.assertEqual(m["automation_pct"], round(100 * (len(executed) - 1) / len(executed), 1))  # TC-001 manual
        want_verdicts = defaultdict(int)
        for rid in self.rows:
            want_verdicts[verdict([self.expected[t] for t in self.by_req[rid]])] += 1
        self.assertEqual(m["requirements_by_verdict"], dict(want_verdicts))
        self.assertEqual((m["critical_requirements"], m["critical_requirements_passed"]), (2, 0))
        self.assertEqual(m["open_defects_by_severity"], {"unknown": 1})

        residual = {x["id"]: x for x in self.facts["residual_risks"]}
        self.assertNotIn(THIN_REQ, residual)
        self.assertEqual([x["id"] for x in self.facts["residual_risks"]][:2], ["REQ-002", "REQ-004"])  # risk 20 first
        for rid in MIGRATION_REQS:
            want = sorted(self.tc_map[c] for c in MIGRATION_FAILED if CHECK_REQ[c] == rid)
            self.assertEqual(residual[rid]["verdict"], "failed")
            self.assertEqual(sorted(residual[rid]["tests"]), want, rid)
        self.assertEqual((residual["REQ-002"]["tests"], residual["REQ-002"]["defects"]), ([self.failed_api], [DEFECT]))
        self.assertEqual(residual[NOT_RUN_REQ]["verdict"], "not-run")

        crit = {e["criterion"]: e["met"] for e in self.facts["exit_criteria"]}
        self.assertEqual(crit, {"min_requirement_coverage_pct": True, "min_pass_rate_pct": False,
                                "all_critical_requirements_passed": False, "min_automation_pct": True,
                                "max_open_defects.critical": None})

    def test_completion_markdown_shows_counts_and_failed_migration_tests(self):
        md = self.report_md
        m = self.facts["metrics"]
        self.assertIn(f"passed {m['passed']} · failed {m['failed']} · blocked 0 · not run {m['not_run']}", md)
        self.assertIn(RUN, md)
        rows = {line.split(" ", 2)[1]: line for line in md.splitlines() if re.match(r"^\| REQ-\d{3} ", line)}
        self.assertEqual(set(rows), {x["id"] for x in self.facts["residual_risks"]})
        for cid in MIGRATION_FAILED:
            self.assertIn(self.tc_map[cid], rows[CHECK_REQ[cid]], cid)
        for cid in MIGRATION_PASSED:
            self.assertNotIn(self.tc_map[cid], md, cid)
        self.assertIn(DEFECT, rows["REQ-002"])


if __name__ == "__main__":
    unittest.main()
