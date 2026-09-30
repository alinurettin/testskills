"""Data-migration verdicts in the REQ -> TC -> results.json -> RTM chain (reconcile.py --compact-out / --results).

Run:  python -m unittest tests.test_migration_results -v
"""
from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "skills" / "testing-data-migrations" / "scripts" / "reconcile.py"
QA_COMPACT = ROOT / "skills" / "designing-test-cases" / "scripts" / "qa_compact.py"
RTM = ROOT / "skills" / "tracing-requirements" / "scripts" / "build_rtm.py"
REPORT = ROOT / "skills" / "reporting-test-results" / "scripts" / "completion_report.py"
TRIAL = ROOT / "evals" / "trial-migration"
FIX = Path(__file__).resolve().parent / "fixtures" / "testing-data-migrations"
MAPPING = FIX / "trial-mapping.json"

_spec = importlib.util.spec_from_file_location("qa_compact_for_migration", QA_COMPACT)
qac = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(qac)

EXTRACTS = ["--source", str(TRIAL / "legacy_customers.csv"), "--target", str(TRIAL / "new_customers.csv"),
            "--encoding-source", "cp1254", "--delimiter-source", ";"]
DESIGN = ["--key", "customer_id", "--mapping", str(MAPPING), "--sum", "balance", "--group-by", "branch",
          "--object", "customers"]
CHECKS = ["row_count", "key_set", "duplicate_keys", "column:full_name", "column:birth_date", "column:branch",
          "column:balance", "column:status", "column:email", "total:balance", "coverage"]
# evals/keys/migration.md: planted defect key -> the check (test case) that must fail with that key in its errors
PLANTED = {"1017": "key_set", "9001": "key_set", "1035": "duplicate_keys", "1004": "column:full_name",
           "1022": "column:full_name", "1009": "column:balance", "1031": "column:balance",
           "1012": "column:birth_date", "1027": "column:status"}
FAILED = {"row_count", "key_set", "duplicate_keys", "column:full_name", "column:birth_date", "column:balance",
          "column:status", "total:balance"}  # row_count and total:balance fail as consequences


def run(script: Path, *args) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(script), *map(str, args)], capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


def header_map(path: Path) -> dict:
    maps = [json.loads(line.split(":", 1)[1]) for line in path.read_text(encoding="utf-8").splitlines()
            if line.startswith("# reconcile-tc-map:")]
    assert len(maps) == 1, maps
    return maps[0]


def parse_compact(path: Path) -> list[dict]:
    _, items, errors = qac.parse(path.read_text(encoding="utf-8"), "tc")
    errors += qac.validate(items, "tc")
    if errors:
        raise AssertionError(errors)
    return items


class CompactGenerationTests(unittest.TestCase):
    """Step 1: one compact test case per check, designed from the mapping before any extract exists."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.d = Path(cls.tmp.name)
        cls.req_map = cls.d / "req-map.json"
        cls.req_map.write_text(json.dumps({
            "default": "REQ-060", "checks": {"key_set": "REQ-061", "column:balance": ["REQ-062", "REQ-063"],
                                             "total": "REQ-064"},
            "operations": {"createTransfer": "REQ-022"}}), encoding="utf-8")  # another script's section: ignored
        cls.out = cls.d / "migration-customers.src.md"
        cls.proc = run(SCRIPT, *DESIGN, "--compact-out", cls.out, "--req", "REQ-099", "--req-map", cls.req_map,
                       "--start", "101", "--lang", "tr")
        cls.items = parse_compact(cls.out)
        cls.by_id = {it["id"]: it for it in cls.items}
        cls.map = header_map(cls.out)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_design_mode_needs_no_extracts_and_parses_cleanly(self):
        self.assertEqual(self.proc.returncode, 0, self.proc.stderr)
        self.assertEqual(self.proc.stderr, "")
        self.assertEqual([it["id"] for it in self.items], [f"TC-{n}" for n in range(101, 112)])
        for it in self.items:
            self.assertEqual((it["category"], it["technique"], it["polarity"], it["status"]),
                             ("data", "requirements-based", "positive", "ready"), it["id"])
            self.assertIn("generated", it["tags"])
            self.assertTrue(it["automation"]["candidate"])
            self.assertTrue(all(s["expected"] for s in it["steps"]))
        self.assertEqual(len({it["title"] for it in self.items}), len(self.items))  # no duplicate titles for the RTM
        self.assertIn("Deneme göçü", self.items[0]["preconditions"][0])  # --lang tr

    def test_header_map_is_machine_readable_and_matches_design_refs(self):
        self.assertEqual(self.map["object"], "customers")
        self.assertEqual(list(self.map["checks"]), CHECKS)
        for cid, tid in self.map["checks"].items():
            self.assertEqual(self.by_id[tid]["design_ref"], f"reconcile:customers:{cid}")

    def test_requirement_precedence(self):
        req = {cid: self.by_id[tid]["requirement_ids"] for cid, tid in self.map["checks"].items()}
        self.assertEqual(req["key_set"], ["REQ-061"])                    # checks[check id]
        self.assertEqual(req["column:balance"], ["REQ-062", "REQ-063"])  # a list is allowed
        self.assertEqual(req["total:balance"], ["REQ-064"])              # checks[family]
        self.assertEqual(req["row_count"], ["REQ-060"])                  # req-map default beats --req
        self.assertEqual(req["coverage"], ["REQ-060"])
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "x.src.md"
            p = run(SCRIPT, *DESIGN, "--compact-out", out, "--req", "REQ-099")
            self.assertEqual(p.returncode, 0, p.stderr)
            self.assertEqual({tuple(it["requirement_ids"]) for it in parse_compact(out)}, {("REQ-099",)})

    def test_header_mode_gives_the_same_checks(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "h.src.md"
            p = run(SCRIPT, *EXTRACTS, *DESIGN, "--compact-out", out, "--req", "REQ-060", "--start", "101")
            self.assertEqual(p.returncode, 0, p.stderr)
            self.assertEqual(header_map(out)["checks"], self.map["checks"])
            self.assertEqual(sorted(x.name for x in Path(d).iterdir()), ["h.src.md"])  # no run, no report

    def test_ids_are_stable_new_checks_append_and_dropped_checks_are_deprecated(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            out = d / "m.src.md"
            shutil.copy(self.out, out)
            mapping = json.loads(MAPPING.read_text(encoding="utf-8"))
            del mapping["columns"]["email"]
            mapping["columns"]["country"] = {"source": None, "transform": ["default:TR"]}
            changed = d / "mapping.json"
            changed.write_text(json.dumps(mapping), encoding="utf-8")
            args = [a if a != str(MAPPING) else str(changed) for a in DESIGN]
            p = run(SCRIPT, *args, "--compact-out", out, "--req", "REQ-060")
            self.assertEqual(p.returncode, 0, p.stderr)
            new = header_map(out)
            for cid in CHECKS:
                if cid != "column:email":
                    self.assertEqual(new["checks"][cid], self.map["checks"][cid], cid)
            self.assertEqual(new["checks"]["column:country"], "TC-112")
            self.assertEqual(new["deprecated"], {"column:email": self.map["checks"]["column:email"]})
            items = {it["id"]: it for it in parse_compact(out)}
            self.assertEqual(items[self.map["checks"]["column:email"]]["status"], "deprecated")

            # a fresh file finds the same IDs through design_ref in test-cases.json and numbers after its max
            tests = d / "test-cases.json"
            r = run(QA_COMPACT, "tc", self.out, "--out", tests)
            self.assertEqual(r.returncode, 0, r.stderr)
            fresh = d / "fresh.src.md"
            p = run(SCRIPT, *args, "--compact-out", fresh, "--req", "REQ-060", "--tests", tests)
            self.assertEqual(p.returncode, 0, p.stderr)
            again = header_map(fresh)
            self.assertEqual(again["checks"]["key_set"], self.map["checks"]["key_set"])
            self.assertEqual(again["checks"]["column:country"], "TC-112")

    def test_usage_errors(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "x.src.md"
            p = run(SCRIPT, *DESIGN, "--compact-out", out)
            self.assertEqual(p.returncode, 2)
            self.assertIn("no requirement", p.stderr)
            self.assertFalse(out.exists())
            cases = [
                [*DESIGN],                                                     # nothing to do
                [*DESIGN, "--req", "REQ-1"],                                   # --req without --compact-out
                [*EXTRACTS, *DESIGN, "--out", Path(d) / "r.md", "--results", Path(d) / "res.json"],  # no tc map
                [*EXTRACTS, *DESIGN, "--out", Path(d) / "r.md", "--tc-map", self.out],               # tc map, no results
                [*DESIGN, "--compact-out", out, "--req", "REQ-1", "--tests", "t.json", "--start", "5"],
                [*DESIGN, "--compact-out", out, "--req", "not a req"],
            ]
            for args in cases:
                self.assertEqual(run(SCRIPT, *args).returncode, 2, args)


class ResultsTests(unittest.TestCase):
    """Step 2: the trial run writes passed/failed per TC into results.json; completion report and RTM count them."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.d = Path(cls.tmp.name)
        cls.compact = cls.d / "migration-customers.src.md"
        p = run(SCRIPT, *DESIGN, "--compact-out", cls.compact, "--req", "REQ-060", "--start", "101")
        assert p.returncode == 0, p.stderr
        cls.map = header_map(cls.compact)
        cls.tests = cls.d / "test-cases.json"
        p = run(QA_COMPACT, "tc", cls.compact, "--out", cls.tests)
        assert p.returncode == 0, p.stderr
        cls.existing = {"TC-001": {"status": "passed", "note": "manual run", "defects": ["SHOP-1"]}}
        cls.results = cls.d / "results.json"
        cls.results.write_text(json.dumps({"run": "RC1", "results": {
            **cls.existing, cls.map["checks"]["column:full_name"]: {"status": "not-run", "defects": ["MIG-7"]}}}),
            encoding="utf-8")
        cls.proc = run(SCRIPT, *EXTRACTS, *DESIGN, "--out", cls.d / "rec.md", "--json", cls.d / "rec.json",
                       "--results", cls.results, "--tc-map", cls.compact)
        cls.doc = json.loads(cls.results.read_text(encoding="utf-8"))
        cls.res = cls.doc["results"]
        cls.rec = json.loads((cls.d / "rec.json").read_text(encoding="utf-8"))

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def entry(self, cid: str) -> dict:
        return self.res[self.map["checks"][cid]]

    def test_verdict_and_summary(self):
        self.assertEqual(self.proc.returncode, 1, self.proc.stderr)
        self.assertIn("results: 11 test cases", self.proc.stdout)
        self.assertIn("failed 8, passed 3", self.proc.stdout)
        self.assertEqual(set(self.rec["checks"]), set(CHECKS))

    def test_merge_keeps_existing_entries_and_defect_keys(self):
        self.assertEqual(self.doc["run"], "RC1")
        self.assertEqual(self.res["TC-001"], self.existing["TC-001"])
        full_name = self.entry("column:full_name")
        self.assertEqual(full_name["defects"], ["MIG-7"])
        self.assertEqual(full_name["source"], "reconcile")
        self.assertEqual(len(self.res), 12)
        self.assertTrue(self.results.read_bytes().endswith(b"}\n"))

    def test_status_per_check(self):
        got = {cid: self.entry(cid)["status"] for cid in CHECKS}
        self.assertEqual({c for c, s in got.items() if s == "failed"}, FAILED)
        self.assertEqual({c for c, s in got.items() if s == "passed"}, {"column:branch", "column:email", "coverage"})
        for cid in CHECKS:
            e = self.entry(cid)
            self.assertIn("rec.md", e["note"])
            self.assertEqual(bool(e.get("errors")), cid in FAILED, cid)
            self.assertLessEqual(len(e.get("errors", [])), 3)

    def test_the_nine_planted_defects_surface_as_failed_tcs(self):
        for key, cid in PLANTED.items():
            e = self.entry(cid)
            self.assertEqual(e["status"], "failed", cid)
            self.assertTrue(any(key in err for err in e["errors"]), f"{key} not in {cid}: {e['errors']}")
        self.assertIn("mojibake", " ".join(self.entry("column:full_name")["errors"]))
        self.assertIn("×100", " ".join(self.entry("column:balance")["errors"]))
        self.assertIn("1035 ×2", self.entry("duplicate_keys")["errors"][0])
        self.assertIn("+335121.21", self.entry("total:balance")["errors"][0])
        self.assertIn("(+1)", self.entry("row_count")["errors"][0])

    def test_results_carry_keys_and_hints_not_values(self):
        text = self.results.read_text(encoding="utf-8")
        for value in ("Ä°BRAHÄ°M", "İBRAHİM", "ŞAHİN", "345678.00", "1990-05-03", "PASSIVE", "SERKAN"):
            self.assertNotIn(value, text)

    def test_other_tc_map_sources(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            # test-cases.json: the map comes from design_ref
            res1 = d / "r1.json"
            p = run(SCRIPT, *EXTRACTS, *DESIGN, "--out", d / "rec.md", "--results", res1, "--tc-map", self.tests)
            self.assertEqual(p.returncode, 1, p.stderr)
            got = json.loads(res1.read_text(encoding="utf-8"))["results"]
            self.assertEqual({k: v["status"] for k, v in got.items()},
                             {tid: "failed" if cid in FAILED else "passed" for cid, tid in self.map["checks"].items()})
            self.assertEqual(json.loads(res1.read_text(encoding="utf-8"))["run"], "reconcile customers")
            # plain JSON: two checks on one TC aggregate; an unknown check is not-run; untraced checks warn
            plain = d / "map.json"
            plain.write_text(json.dumps({"key_set": "TC-900", "duplicate_keys": "TC-900", "column:fax": "TC-901"}),
                             encoding="utf-8")
            res2 = d / "r2.json"
            p = run(SCRIPT, *EXTRACTS, *DESIGN, "--out", d / "rec.md", "--results", res2, "--tc-map", plain,
                    "--run", "Mock 2")
            doc = json.loads(res2.read_text(encoding="utf-8"))
            self.assertEqual(doc["run"], "Mock 2")
            self.assertEqual(doc["results"]["TC-900"]["status"], "failed")
            self.assertEqual(len(doc["results"]["TC-900"]["errors"]), 3)  # missing, unexpected, duplicate
            self.assertEqual(doc["results"]["TC-901"]["status"], "not-run")
            self.assertIn("warning", p.stderr)
            self.assertIn("column:balance", p.stderr)
            bad = d / "bad.json"
            bad.write_text(json.dumps({"key_set": "REQ-1"}), encoding="utf-8")
            p = run(SCRIPT, *EXTRACTS, *DESIGN, "--out", d / "rec.md", "--results", d / "r3.json", "--tc-map", bad)
            self.assertEqual(p.returncode, 2)
            self.assertFalse((d / "r3.json").exists())

    def test_completion_report_and_rtm_count_the_results(self):
        with tempfile.TemporaryDirectory() as d:
            qa = Path(d) / "qa"
            qa.mkdir()
            (qa / "requirements.json").write_text(json.dumps({"language": "en", "requirements": [{
                "id": "REQ-060", "title": "Customer migration is complete and correct", "type": "data",
                "priority": "high", "status": "ready", "source": "Mapping spec v3",
                "text": "Every customer is migrated exactly once according to the mapping specification."}]}),
                encoding="utf-8")
            shutil.copy(self.tests, qa / "test-cases.json")
            shutil.copy(self.results, qa / "results.json")
            p = run(REPORT, "--qa", qa, "--json")
            m = json.loads(p.stdout)["metrics"]
            self.assertEqual((m["tests"], m["executed"], m["passed"], m["failed"]), (11, 11, 3, 8))
            self.assertEqual(m["automation_pct"], 100.0)  # reconcile results are executed by a tool
            self.assertEqual(m["requirements_by_verdict"], {"failed": 1})
            p = run(RTM, "--requirements", qa / "requirements.json", "--tests", qa / "test-cases.json",
                    "--results", qa / "results.json", "--out-dir", qa, "--json")
            rtm = json.loads((qa / "rtm.json").read_text(encoding="utf-8"))
            self.assertEqual(rtm["errors"], [])
            row = rtm["rows"][0]
            self.assertEqual((row["execution"], len(row["tests"]), row["defects"]), ("failed", 11, ["MIG-7"]))


class CheckConsistencyTests(unittest.TestCase):
    """Accepted exceptions: a PASS verdict never leaves a failed check behind."""

    SRC = "id;name;amount;branch\n1;Ayşe;1.000,50;A\n2;Ümit;20,00;A\n3;Işık;5,25;B\n"
    TGT = "id,name,amount,branch\n1,Ayşe,1000.50,A\n2,Ümit,20.00,A\n"

    def reconcile(self, d: Path, mapping: dict, src: str | None = None) -> tuple[subprocess.CompletedProcess, dict]:
        (d / "s.csv").write_bytes((src or self.SRC).encode("cp1254"))
        (d / "t.csv").write_text(self.TGT, encoding="utf-8")
        (d / "m.json").write_text(json.dumps(mapping), encoding="utf-8")
        p = run(SCRIPT, "--source", d / "s.csv", "--target", d / "t.csv", "--key", "id", "--mapping", d / "m.json",
                "--sum", "amount", "--group-by", "branch", "--encoding-source", "cp1254", "--delimiter-source", ";",
                "--out", d / "r.md", "--json", d / "r.json")
        return p, json.loads((d / "r.json").read_text(encoding="utf-8"))

    MAPPING = {"columns": {"id": "id", "name": "name", "branch": "branch",
                          "amount": {"source": "amount", "transform": ["decimal:2:,"]}}}

    def test_accepted_scope_exclusion_passes_every_check(self):
        mapping = dict(self.MAPPING, accepted_exceptions=[
            {"check": "missing", "key": "3", "reason": "closed account, out of scope (DEC-4)"},
            {"check": "total", "column": "amount", "reason": "DEC-4"},
            {"check": "total", "column": "amount", "group": "B", "reason": "DEC-4"}])
        with tempfile.TemporaryDirectory() as d:
            p, res = self.reconcile(Path(d), mapping)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertEqual({c["status"] for c in res["checks"].values()}, {"passed"})
        self.assertIn("accepted", res["checks"]["row_count"]["note"])
        self.assertIn("1 accepted", res["checks"]["key_set"]["note"])

    def test_unaccepted_findings_fail_their_checks(self):
        src = self.SRC.replace("id;name;amount;branch", "id;name;amount;branch;fax").replace(
            ";A\n", ";A;x\n").replace(";B\n", ";B;y\n")
        with tempfile.TemporaryDirectory() as d:
            p, res = self.reconcile(Path(d), self.MAPPING, src)
        self.assertEqual(p.returncode, 1)
        ch = res["checks"]
        self.assertEqual(ch["row_count"]["status"], "failed")
        self.assertEqual(ch["key_set"]["errors"], ["missing in target (1): 3"])
        self.assertEqual(ch["coverage"]["status"], "failed")
        self.assertIn("fax", ch["coverage"]["errors"][0])
        self.assertEqual(ch["column:name"]["status"], "passed")


if __name__ == "__main__":
    unittest.main()
