"""Independent exhaustive oracle for bounded constrained covering arrays."""
import importlib.util
import itertools
import json
import random
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills/designing-test-cases/scripts/pairwise.py"
spec = importlib.util.spec_from_file_location("pairwise_guarantees", SCRIPT)
pw = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pw)

REPRO = {
    "parameters": [{"name": n, "values": [0, 1, 2]} for n in "ABCD"],
    "forbidden": [{"C": 2, "D": 0, "B": 0}, {"C": 0, "B": 0},
                  {"B": 0, "D": 2, "C": 1}, {"A": 1, "D": 1},
                  {"A": 1, "D": 2, "C": 2}],
}


def oracle(specification):
    names = [p["name"] for p in specification["parameters"]]
    rows = [dict(zip(names, vals)) for vals in itertools.product(
        *(p["values"] for p in specification["parameters"]))]
    valid = [r for r in rows if not any(all(
        r[k] in (v if isinstance(v, list) else [v]) for k, v in f.items()
    ) for f in specification.get("forbidden", []))]
    strength = specification.get("strength", 2)
    tuples = {tuple((k, row[k]) for k in keys) for row in valid
              for keys in itertools.combinations(names, strength)}
    return valid, tuples


class PairwiseGuarantees(unittest.TestCase):
    def assert_coverage(self, specification, result):
        valid, expected = oracle(specification)
        names = [p["name"] for p in specification["parameters"]]
        covered = set()
        for test in result["tests"]:
            row = test["values"]
            self.assertIn(row, valid)
            covered.update(tuple((k, row[k]) for k in keys)
                           for keys in itertools.combinations(names, specification.get("strength", 2)))
        self.assertEqual(covered, expected)
        self.assertTrue(result["verification"]["all_tuples_covered"])
        self.assertEqual(result["summary"]["feasible_tuples"], len(expected))

    def test_greedy_miss_is_completed_exactly(self):
        result = pw.generate(REPRO, 30, 42)
        self.assertEqual(len(oracle(REPRO)[1]), 52)
        self.assert_coverage(REPRO, result)

    def test_seeds_must_be_in_domain(self):
        invalid = {"parameters": [{"name": n, "values": [0, 1]} for n in "AB"],
                   "seed_tests": [{"A": 99, "B": 0}]}
        with self.assertRaisesRegex(ValueError, "domain"):
            pw.generate(invalid, 30, 42)

    def test_small_constraints_against_independent_oracle(self):
        rng = random.Random(19)
        for i in range(25):
            params = [{"name": n, "values": [0, 1, 2]} for n in "ABCD"]
            forbidden = []
            for _ in range(i % 7):
                keys = rng.sample(list("ABCD"), rng.choice([2, 3]))
                forbidden.append({k: rng.randrange(3) for k in keys})
            case = {"parameters": params, "forbidden": forbidden, "strength": 2 + i % 2}
            with self.subTest(i=i):
                self.assert_coverage(case, pw.generate(case, 2, 42))

    def test_infeasibility_can_be_indirect(self):
        case = {"parameters": [{"name": n, "values": [0, 1]} for n in "ABC"],
                "forbidden": [{"A": 0, "C": 0}, {"A": 0, "C": 1}]}
        result = pw.generate(case, 2, 42)
        self.assert_coverage(case, result)
        self.assertTrue(result["infeasible"])

    def test_resource_limit_is_unknown_not_success(self):
        result = pw.generate(REPRO, 30, 42, max_nodes=0)
        self.assertFalse(result["verification"]["all_tuples_covered"])
        self.assertEqual(result["summary"]["unknown_tuples"], 1)
        self.assertIn({"A": 1, "B": 0}, result["verification"]["missing"])

    def test_cli_resource_limit_fails_and_reports_unknown(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "spec.json"
            path.write_text(json.dumps(REPRO), encoding="utf-8")
            result = subprocess.run([sys.executable, str(SCRIPT), str(path), "--max-nodes", "0",
                                     "--format", "json"], capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertEqual(json.loads(result.stdout)["summary"]["unknown_tuples"], 1)

    def test_bad_inputs_rejected_before_search(self):
        for case in [
            {"parameters": [{"name": "A", "values": []}]},
            {"parameters": [{"name": "A", "values": [0]}, {"name": "A", "values": [1]}]},
            {"parameters": [{"name": "A", "values": [0, 0]}]},
            {"parameters": [{"name": n, "values": [float("nan")]} for n in "AB"]},
        ]:
            with self.subTest(case=case), self.assertRaises(ValueError):
                pw.generate(case, 30, 42)

    def test_constraint_expansion_is_bounded_before_allocation(self):
        # Only 24 candidate tuples at strength=1, but this rule expands to 4096.
        case = {"strength": 1, "parameters": [{"name": f"P{i}", "values": [0, 1]} for i in range(12)],
                "forbidden": [{f"P{i}": [0, 1] for i in range(12)}]}
        with self.assertRaisesRegex(ValueError, "constraint|forbidden"):
            pw.generate(case, 1, 42, max_tuples=100)


if __name__ == "__main__":
    unittest.main()
