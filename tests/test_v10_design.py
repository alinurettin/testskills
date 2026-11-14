"""Regression tests for the 0.10.0 test-design fixes (audit docs/audit-2026-11/gap-design.md, findings 3, 4, 7, 10, 14).

Run:  python -m unittest tests.test_v10_design -v
"""
from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "skills" / "designing-test-cases" / "scripts"
TECHNIQUES = ROOT / "skills" / "designing-test-cases" / "references" / "techniques.md"


def load(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem + "_v10", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


ep = load(SCRIPTS / "ep_bva.py")
dt = load(SCRIPTS / "decision_table.py")

AGE = [{"name": "age", "type": "integer", "min": 18, "max": 65}]


def bounds(params, **spec):
    res = ep.run({"parameters": params, **spec}, "en")
    return [b["value"] for b in res["parameters"][0]["boundaries"]]


class BvaConsistency(unittest.TestCase):
    """Finding 3: the reference and the script must give the same 3-value sets."""

    def test_two_value_is_the_same_in_both_scopes(self):
        self.assertEqual(bounds(AGE), ["17", "18", "65", "66"])
        self.assertEqual(bounds(AGE, bva_scope="valid"), ["17", "18", "65", "66"])

    def test_three_value_scope_all_is_the_default(self):
        self.assertEqual(bounds(AGE, bva="3-value"), ["16", "17", "18", "19", "64", "65", "66", "67"])

    def test_three_value_scope_valid(self):
        self.assertEqual(bounds(AGE, bva="3-value", bva_scope="valid"), ["17", "18", "19", "64", "65", "66"])

    def test_scope_valid_keeps_both_sides_between_two_valid_partitions(self):
        p = [{"name": "score", "type": "integer", "domain_min": 0, "partitions": [
            {"label": "reject", "min": 0, "max": 499}, {"label": "approve", "min": 500, "max": 1000}]}]
        got = bounds(p, bva="3-value", bva_scope="valid")
        for v in ("498", "499", "500", "501", "999", "1000", "1001"):
            self.assertIn(v, got)
        self.assertNotIn("1002", got)   # neighbour of the unspecified partition's boundary

    def test_reference_states_the_sets_the_script_emits(self):
        text = TECHNIQUES.read_text(encoding="utf-8")
        self.assertIn("16, 17, 18, 19 and 64, 65, 66, 67", text)
        self.assertIn("17, 18, 19 and 64, 65, 66", text)
        self.assertIn("neighbours exercised", text)   # the 3-value coverage formula

    def test_items_are_labelled_boundary_or_neighbour_and_counted(self):
        res = ep.run({"bva": "3-value", "parameters": AGE}, "en")
        kinds = {b["value"]: b["kind"] for b in res["parameters"][0]["boundaries"]}
        self.assertEqual({v for v, k in kinds.items() if k == "boundary"}, {"17", "18", "65", "66"})
        self.assertEqual({v for v, k in kinds.items() if k == "neighbour"}, {"16", "19", "64", "67"})
        self.assertEqual((res["summary"]["bva_boundaries"], res["summary"]["bva_neighbours"]), (4, 4))
        self.assertEqual(res["summary"]["boundary_values"], 8)   # unchanged field: all BVA coverage items

    def test_invalid_option_values_are_rejected(self):
        for bad in ({"bva": "4-value"}, {"bva_scope": "some"}, {"strategy": "x"}):
            with self.assertRaises(ValueError):
                ep.run({"parameters": AGE, **bad}, "en")


class OpenBorders(unittest.TestCase):
    """Finding 7: 'min_exclusive' used to be ignored silently (the lower boundary was never tested)."""

    def test_exclusive_bounds_become_boundary_values(self):
        p = [{"name": "h", "type": "decimal", "step": "0.01", "min_exclusive": "1.29", "max_exclusive": "2.50"}]
        res = ep.run({"parameters": p}, "en")
        b = {x["value"]: x for x in res["parameters"][0]["boundaries"]}
        self.assertEqual(sorted(b), ["1.29", "1.30", "2.49", "2.50"])
        self.assertEqual((b["1.29"]["valid"], b["1.30"]["valid"], b["2.49"]["valid"], b["2.50"]["valid"]),
                         (False, True, True, False))
        self.assertEqual((b["1.29"]["point"], b["1.30"]["point"]), ("OFF", "ON"))
        self.assertIn("> 1.29", b["1.30"]["note"])
        self.assertEqual(res["warnings"], [])

    def test_min_and_min_exclusive_together_is_an_error(self):
        with self.assertRaises(ValueError):
            ep.run({"parameters": [{"name": "x", "type": "integer", "min": 1, "min_exclusive": 0, "max": 5}]}, "en")

    def test_unknown_type_is_an_error_not_a_crash(self):
        with self.assertRaises(ValueError):
            ep.run({"parameters": [{"name": "x", "type": "money", "min": 1, "max": 5}]}, "en")


class SyntaxFormat(unittest.TestCase):
    """Finding 14: formatted fields get valid values and single-mutation invalid values."""

    PLATE = {"name": "plate", "type": "format", "segments": [
        {"name": "city", "chars": "digit", "min": 2, "max": 2}, {"name": "sep1", "literal": " "},
        {"name": "letters", "chars": "upper", "min": 1, "max": 3}, {"name": "sep2", "literal": " "},
        {"name": "number", "chars": "digit", "min": 2, "max": 4}]}

    def test_valid_values_match_and_invalid_values_do_not(self):
        res = ep.run({"parameters": [self.PLATE]}, "en")
        rx = ep.format_regex(self.PLATE["segments"])
        parts = res["parameters"][0]["partitions"]
        valid = [q["representative"] for q in parts if q["valid"]]
        invalid = [q["representative"] for q in parts if not q["valid"]]
        self.assertIn("12 ABC 1234", valid)
        self.assertIn("12 A 1234", valid)      # letters at minimum length
        self.assertTrue(all(rx.fullmatch(v) for v in valid), valid)
        self.assertTrue(invalid and not any(rx.fullmatch(v) for v in invalid), invalid)
        self.assertEqual(len(set(valid + invalid)), len(valid + invalid))
        labels = " | ".join(q["label"] for q in parts)
        for word in ("too short", "too long", "wrong character class", "missing", "wrong separator", "empty value"):
            self.assertIn(word, labels)

    def test_each_invalid_value_is_tested_alone(self):
        res = ep.run({"parameters": [self.PLATE, AGE[0]]}, "en")
        for c in res["conditions"]:
            if c["valid"] is not True:
                self.assertIsNotNone(c["varied"])
                others = [n for n in c["values"] if n != c["varied"]]
                self.assertTrue(all(c["values"][n] == res["nominal"][n] for n in others), c)

    def test_options_and_optional_segments(self):
        p = {"name": "iban", "type": "format", "segments": [
            {"name": "country", "options": ["TR", "DE"]}, {"name": "digits", "chars": "digit", "length": 4},
            {"name": "suffix", "literal": "-X", "optional": True}]}
        parts = ep.run({"parameters": [p]}, "en")["parameters"][0]["partitions"]
        valid = [q["representative"] for q in parts if q["valid"]]
        self.assertEqual(valid, ["TR1234-X", "DE1234-X", "TR1234"])
        self.assertIn("XX1234-X", [q["representative"] for q in parts if not q["valid"]])


class CoverageItemRows(unittest.TestCase):
    """Finding 10: C-## rows name the coverage items they exercise; a rejected input covers one item only."""

    def test_covers_and_model(self):
        res = ep.run({"parameters": AGE + [{"name": "cur", "type": "enum", "valid": ["TRY", "EUR"], "invalid": ["USD"]}]}, "en")
        model = ep.coverage_model(res)
        items = {(m["name"], i) for m in model["measures"] for i in m["items"]}
        covered = {x for refs in model["refs"].values() for x in refs}
        self.assertEqual(covered, items)      # executing every C-## row gives 100% of both measures
        for c in res["conditions"]:
            if c["valid"] is not True:
                self.assertTrue(all(key.startswith(c["varied"]) for _, key in c["covers"]), c)

    def test_markdown_heading_uses_coverage_items(self):
        for lang, word in (("en", "Coverage items"), ("tr", "Kapsam öğeleri")):
            md = ep.to_md(ep.run({"parameters": AGE}, lang), lang, {"parameters": AGE})
            self.assertIn(f"## {word}", md)
            self.assertNotIn("Test conditions", md)
            self.assertNotIn("Test koşulları", md)


class DecisionTableMinimisation(unittest.TestCase):
    """Finding 4: infeasible combinations blocked merging, '-' always took the first value, subsumed rules were silent."""

    SPEC = {"conditions": [{"name": "member", "values": ["Y", "N"]}, {"name": "coupon", "values": ["valid", "none"]},
                           {"name": "staff", "values": ["Y", "N"]}],
            "actions": ["discount"],
            "rules": [{"id": "R1", "when": {"coupon": "valid"}, "then": {"discount": "yes"}},
                      {"id": "R2", "when": {"coupon": "none"}, "then": {"discount": "no"}},
                      {"id": "R3", "when": {"coupon": "none", "member": "Y"}, "then": {"discount": "no"}}],
            "infeasible": [{"member": "N", "staff": "Y"}]}

    def setUp(self):
        self.res = dt.run(json.loads(json.dumps(self.SPEC)), "collapsed", "en")

    def test_infeasible_combinations_do_not_block_merging(self):
        self.assertEqual(self.res["summary"]["collapsed_columns"], 2)   # was 4
        self.assertEqual([c["values"] for c in self.res["collapsed"]],
                         [{"member": "-", "coupon": "valid", "staff": "-"}, {"member": "-", "coupon": "none", "staff": "-"}])

    def test_test_inputs_are_feasible_and_cover_every_combination_once(self):
        ok = {r["id"]: r["values"] for r in self.res["full_table"] if r["status"] == "ok"}
        covered = [c for t in self.res["test_conditions"] for c in t["covers"]]
        self.assertEqual(sorted(covered), sorted(ok))
        for t in self.res["test_conditions"]:
            self.assertIn(t["values"], ok.values())
            self.assertFalse(t["values"]["member"] == "N" and t["values"]["staff"] == "Y")

    def test_dont_care_values_rotate(self):
        used = {(k, v) for t in self.res["test_conditions"] for k, v in t["values"].items()}
        for pair in (("member", "Y"), ("member", "N"), ("staff", "Y"), ("staff", "N")):   # member=N was never used
            self.assertIn(pair, used)
        self.assertEqual(self.res["untested_values"], [])

    def test_untested_value_is_reported_when_rotation_cannot_reach_it(self):
        spec = {"conditions": [{"name": "a", "values": ["1", "2", "3"]}, {"name": "b", "values": ["x", "y"]}],
                "rules": [{"id": "R1", "when": {}, "then": {"r": "same"}}]}
        res = dt.run(spec, "collapsed", "en")
        self.assertEqual(res["summary"]["collapsed_columns"], 1)
        self.assertEqual(res["summary"]["untested_values"], len(res["untested_values"]))
        self.assertEqual(len(res["untested_values"]), 3)    # one test shows one value of a and one of b
        self.assertIn("no test input uses", dt.to_md(res, "en"))
        self.assertEqual(dt.run(spec, "full", "en")["untested_values"], [])

    def test_redundant_rule_is_reported(self):
        self.assertEqual(self.res["redundant_rules"], [{"rule": "R3", "subsumed_by": "R2"}])
        self.assertIn("R3 ⊆ R2", dt.to_md(self.res, "en"))

    def test_duplicate_rule_reports_the_later_one(self):
        spec = {"conditions": [{"name": "a", "values": ["Y", "N"]}],
                "rules": [{"id": "R1", "when": {"a": "Y"}, "then": {"r": "1"}},
                          {"id": "R2", "when": {"a": "Y"}, "then": {"r": "1"}},
                          {"id": "R3", "when": {"a": "N"}, "then": {"r": "2"}}]}
        self.assertEqual(dt.run(spec, "collapsed", "en")["redundant_rules"], [{"rule": "R2", "subsumed_by": "R1"}])

    def test_checksum(self):
        ck = self.res["checksum"]
        self.assertTrue(ck["ok"])
        self.assertEqual((ck["minimised"], ck["with_outcome"], ck["infeasible_absorbed"], ck["full_table"],
                          ck["infeasible"]), (8, 6, 2, 8, 2))
        self.assertRegex(dt.to_md(self.res, "en"), r"Checksum: .* → OK")

    def test_gap_or_conflict_inside_a_cube_still_blocks_the_merge(self):
        spec = {"conditions": [{"name": "a", "values": ["Y", "N"]}, {"name": "b", "values": ["Y", "N"]}],
                "rules": [{"id": "R1", "when": {"a": "Y", "b": "Y"}, "then": {"r": "1"}},
                          {"id": "R2", "when": {"a": "N", "b": "Y"}, "then": {"r": "1"}},
                          {"id": "R3", "when": {"a": "Y", "b": "N"}, "then": {"r": "1"}}]}
        res = dt.run(spec, "collapsed", "en")          # a=N, b=N is a gap, not an infeasible combination
        self.assertEqual(res["summary"]["gaps"], 1)
        self.assertTrue(res["checksum"]["ok"])
        for col in res["collapsed"]:
            self.assertFalse(col["values"]["a"] in ("-", "N") and col["values"]["b"] in ("-", "N"), col)

    def test_example_spec_is_unchanged_and_consistent(self):
        spec = json.loads((ROOT / "skills" / "designing-test-cases" / "assets" / "spec-examples" /
                           "decision-table.json").read_text(encoding="utf-8"))
        res = dt.run(spec, "collapsed", "en")
        self.assertEqual((res["summary"]["collapsed_columns"], res["summary"]["gaps"], res["summary"]["conflicts"]), (5, 1, 1))
        self.assertTrue(res["checksum"]["ok"])
        self.assertEqual(res["redundant_rules"], [])

    def test_turkish_output_and_cli(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "DS-009.json"
            p.write_text(json.dumps(dict(self.SPEC, language="tr"), ensure_ascii=False), encoding="utf-8")
            r = subprocess.run([sys.executable, str(SCRIPTS / "decision_table.py"), str(p)],
                               capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("Sağlama:", r.stdout)
            self.assertIn("Kapsam öğeleri", r.stdout)
            self.assertIn("Gereksiz kurallar", r.stdout)
            out = Path(d) / "out.md"
            subprocess.run([sys.executable, str(SCRIPTS / "decision_table.py"), str(p), "--out", str(out)], check=True,
                           capture_output=True)
            self.assertNotIn(b"\r\n", out.read_bytes())


class EpBvaCli(unittest.TestCase):
    def test_cli_exit_codes_and_lf_output(self):
        with tempfile.TemporaryDirectory() as d:
            good, bad, out = Path(d) / "DS-001.json", Path(d) / "bad.json", Path(d) / "o.md"
            good.write_text(json.dumps({"language": "tr", "bva": "3-value", "bva_scope": "valid", "parameters": AGE}),
                            encoding="utf-8")
            bad.write_text(json.dumps({"bva_scope": "none", "parameters": AGE}), encoding="utf-8")
            r = subprocess.run([sys.executable, str(SCRIPTS / "ep_bva.py"), str(good), "--out", str(out)],
                               capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(r.returncode, 0, r.stderr)
            data = out.read_bytes()
            self.assertNotIn(b"\r\n", data)
            text = data.decode("utf-8")
            self.assertIn("Kapsam öğeleri", text)
            self.assertTrue(re.search(r"3 sınır|sınır değeri \+", text))
            r = subprocess.run([sys.executable, str(SCRIPTS / "ep_bva.py"), str(bad)],
                               capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(r.returncode, 2)
            self.assertIn("bva_scope", r.stderr)


if __name__ == "__main__":
    unittest.main()
