"""Tests for shared/scripts/tr_ids.py (TCKN, VKN, IBAN) and the suite's ID policy.

The reference implementations below are written independently of tr_ids.py (different
formulation), so a shared mistake is unlikely. Run:  python -m unittest tests.test_tr_ids -v
"""
from __future__ import annotations

import importlib.util
import json
import random
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SHARED = ROOT / "shared" / "scripts" / "tr_ids.py"
COPIES = [ROOT / "skills" / s / "scripts" / "tr_ids.py"
          for s in ("designing-test-cases", "preparing-test-data", "testing-ai-features")]
CHECK_IDS = ROOT / "skills" / "designing-test-cases" / "scripts" / "check_ids.py"
DATA_NEEDS = ROOT / "skills" / "preparing-test-data" / "scripts" / "data_needs.py"

# VKNs that legal entities publish on their "bilgi toplumu hizmetleri" pages (Turkish Commercial
# Code art. 1524). Checked on 2026-09-30:
#   4730030397  İLBANK A.Ş.  https://www.ilbank.gov.tr/sayfa/bilgi-toplumu-hizmetleri
#                            (its MERSİS no 0473003039700017 embeds the same VKN)
#   1430023849  BASF Türk    https://www.basf.com/tr/tr/legal/bilgi-toplumu-hizmetleri
PUBLISHED_VKNS = ("4730030397", "1430023849")


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


ids = load(SHARED, "tr_ids_under_test")


# --- independent reference implementations ------------------------------------------------------
def ref_tckn(s: str) -> bool:
    if len(s) != 11 or any(c not in "0123456789" for c in s) or s[0] == "0":
        return False
    d = [ord(c) - 48 for c in s]
    weights10 = [7, -1, 7, -1, 7, -1, 7, -1, 7]  # 7*(odd positions) - (even positions)
    c10 = sum(w * x for w, x in zip(weights10, d)) % 10
    c11 = (sum(d[:9]) + c10) % 10
    return (c10, c11) == (d[9], d[10])


def ref_vkn(s: str) -> bool:
    if len(s) != 10 or any(c not in "0123456789" for c in s):
        return False
    total = 0
    for pos in range(1, 10):  # published algorithm: positions 1..9
        v1 = (int(s[pos - 1]) + 10 - pos) % 10
        v2 = (v1 * pow(2, 10 - pos)) % 9
        if v1 != 0 and v2 == 0:
            v2 = 9
        total += v2
    return (10 - total % 10) % 10 == int(s[9])


def ref_iban(s: str) -> bool:
    s = "".join(s.split()).upper()
    if len(s) < 5 or not (s[:2].isalpha() and s[:2].isascii() and s[2:4].isdigit()):
        return False
    if s.startswith("TR") and (len(s) != 26 or not s[4:10].isdigit()):
        return False
    rem = 0
    for ch in s[4:] + s[:4]:  # piecewise mod 97, letters A=10 .. Z=35
        if "0" <= ch <= "9":
            rem = (rem * 10 + int(ch)) % 97
        elif "A" <= ch <= "Z":
            rem = (rem * 100 + ord(ch) - 55) % 97
        else:
            return False
    return rem == 1


class GeneratedValuesTests(unittest.TestCase):
    def test_1000_generated_values_pass_the_reference_checks(self):
        rng = random.Random(20260930)
        for _ in range(1000):
            t, v, i = ids.gen_tckn(rng), ids.gen_vkn(rng), ids.gen_tr_iban(rng)
            self.assertTrue(ref_tckn(t) and ids.is_valid_tckn(t), t)
            self.assertNotEqual(t[0], "0")
            self.assertTrue(ref_vkn(v) and ids.is_valid_vkn(v), v)
            self.assertTrue(ref_iban(i) and ids.is_valid_tr_iban(i), i)
            self.assertEqual((len(i), i[9]), (26, "0"))  # TR length, reserve digit 0

    def test_same_seed_same_values(self):
        a, b = random.Random(7), random.Random(7)
        self.assertEqual([ids.gen_tckn(a) for _ in range(5)], [ids.gen_tckn(b) for _ in range(5)])
        self.assertEqual(ids.gen_tr_iban(random.Random(1), ["00099"])[4:9], "00099")

    def test_exactly_one_check_digit_fits_each_prefix(self):
        rng = random.Random(3)
        for _ in range(200):
            p9 = "".join(rng.choice("0123456789") for _ in range(9))
            self.assertEqual(sum(ref_vkn(p9 + str(d)) for d in range(10)), 1, p9)
            self.assertEqual(sum(ids.is_valid_vkn(p9 + str(d)) for d in range(10)), 1, p9)
            if p9[0] != "0":
                ok = [f"{d:02d}" for d in range(100) if ref_tckn(p9 + f"{d:02d}")]
                self.assertEqual(ok, [ids.tckn_check_digits(p9)])

    def test_validators_agree_with_references_on_random_input(self):
        rng = random.Random(11)
        for _ in range(3000):
            s = "".join(rng.choice("0123456789") for _ in range(rng.choice((10, 11))))
            self.assertEqual(ids.is_valid_tckn(s), ref_tckn(s), s)
            self.assertEqual(ids.is_valid_vkn(s), ref_vkn(s), s)
            iban = "TR" + "".join(rng.choice("0123456789") for _ in range(24))
            self.assertEqual(ids.is_valid_iban(iban), ref_iban(iban), iban)


class PublishedExamplesTests(unittest.TestCase):
    def test_published_vkns_validate(self):
        for v in PUBLISHED_VKNS:
            self.assertTrue(ref_vkn(v), v)
            self.assertEqual(ids.validate_vkn(v), (True, "valid"))
            bad = v[:9] + str((int(v[9]) + 1) % 10)
            self.assertEqual(ids.validate_vkn(bad), (False, "check digit wrong"))

    def test_known_tckn_and_iban_examples(self):
        self.assertTrue(ids.is_valid_tckn("10000000146"))  # widely documented test TCKN
        self.assertTrue(ids.is_valid_iban("TR33 0006 1005 1978 6457 8413 26"))  # IBAN registry example
        self.assertTrue(ids.is_valid_iban("GB82 WEST 1234 5698 7654 32"))  # ISO 13616 example
        self.assertEqual(ids.iban_check_digits("TR", "0006100519786457841326"), "33")
        self.assertEqual(ids.iban_check_digits("GB", "WEST12345698765432"), "82")


class ValidationDetailTests(unittest.TestCase):
    def test_tckn_reasons(self):
        self.assertEqual(ids.validate_tckn("00000000146"), (False, "first digit must not be 0"))
        self.assertEqual(ids.validate_tckn("10000000156"), (False, "10th digit checksum wrong"))
        self.assertEqual(ids.validate_tckn("10000000147"), (False, "11th digit checksum wrong"))
        self.assertEqual(ids.validate_tckn("1000000014"), (False, "must be exactly 11 digits"))
        self.assertEqual(ids.validate_tckn(" 10000000146 "), (False, "must be exactly 11 digits"))  # strict
        self.assertTrue(ids.is_valid_tckn(" 10000000146 "))  # lenient
        self.assertFalse(ids.is_valid_tckn("１００００００００１４６"))  # full-width digits are not digits here

    def test_iban_rules(self):
        self.assertEqual(ids.validate_iban("TR33000610051978645784132")[1], "TR IBAN must be 26 characters")
        self.assertEqual(ids.validate_iban("TR3300061005197864578413267")[1], "TR IBAN must be 26 characters")
        self.assertEqual(ids.validate_iban("TR33A006100519786457841326")[1],
                         "TR IBAN bank code and reserve digit must be digits")
        self.assertEqual(ids.validate_iban("TR330006100519786457841327"), (False, "mod-97 check failed"))
        self.assertEqual(ids.validate_iban("12"), (False, "format must be CC + 2 check digits + BBAN"))
        self.assertTrue(ids.validate_iban("tr33 0006 1005 1978 6457 8413 26")[0])  # normalised
        self.assertEqual(ids.validate_tr_iban("GB82WEST12345698765432"), (False, "country code must be TR"))
        self.assertEqual(ids.iban_display("TR330006100519786457841326"), "TR33 0006 1005 1978 6457 8413 26")


class VariantTests(unittest.TestCase):
    def check_variants(self, kind, value, strict, lenient):
        variants = ids.invalid_variants(kind, value)
        self.assertTrue(variants)
        for v, fault, expect in variants:
            self.assertIn(expect, ("invalid", "clarify"))
            if expect == "invalid":
                self.assertFalse(strict(v), (kind, v, fault))
                self.assertFalse(lenient(v), (kind, v, fault))
            else:
                self.assertTrue(lenient(v), (kind, v, fault))  # notation variant of a valid value

    def test_variants_of_generated_values_are_invalid(self):
        rng = random.Random(5)
        tckn_lenient, vkn_lenient = (lambda v: ref_tckn(v.strip())), (lambda v: ref_vkn(v.strip()))
        for _ in range(200):
            self.check_variants("tckn", ids.gen_tckn(rng), lambda v: ids.validate_tckn(v)[0], tckn_lenient)
            self.check_variants("vkn", ids.gen_vkn(rng), lambda v: ids.validate_vkn(v)[0], vkn_lenient)
            iban = ids.gen_tr_iban(rng)
            for kind in ("iban", "tr_iban"):
                self.check_variants(kind, iban, ids.is_valid_iban, ref_iban)
        for vkn in PUBLISHED_VKNS:
            self.check_variants("vkn", vkn, lambda v: ids.validate_vkn(v)[0], vkn_lenient)
        self.check_variants("iban", "GB82WEST12345698765432", ids.is_valid_iban, ref_iban)

    def test_single_fault_and_edge_input(self):
        faults = [f for _, f, _ in ids.invalid_variants("tckn", "10000000146")]
        self.assertIn("first digit 0", faults)
        self.assertIn("10th digit changed", faults)
        self.assertEqual(ids.invalid_variants("tckn", ""), [])
        self.assertTrue(ids.invalid_variants("tckn", "123"))  # short input: no IndexError
        with self.assertRaises(ValueError):
            ids.invalid_variants("passport", "X")


class SyncAndCliTests(unittest.TestCase):
    def test_skill_copies_match_the_shared_source(self):
        src = SHARED.read_bytes()
        for copy in COPIES:
            self.assertEqual(copy.read_bytes(), src, f"{copy} is stale - run python tools/sync_shared.py")

    def run_py(self, *args):
        return subprocess.run([sys.executable, *map(str, args)], capture_output=True, text=True, encoding="utf-8")

    def test_check_ids_generates_synthetic_valid_values(self):
        r = self.run_py(CHECK_IDS, "tckn", "--generate", "3", "--seed", "42", "--format", "json")
        self.assertEqual(r.returncode, 0, r.stderr)
        rows = json.loads(r.stdout)
        self.assertEqual(len(rows), 3)
        for row in rows:
            self.assertTrue(row["valid"] and row["synthetic"] and ref_tckn(row["value"]), row)
        again = json.loads(self.run_py(CHECK_IDS, "tckn", "--generate", "3", "--seed", "42", "--format", "json").stdout)
        self.assertEqual([x["value"] for x in rows], [x["value"] for x in again])
        r = self.run_py(CHECK_IDS, "iban", "--generate", "1", "--variants")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("synthetic", r.stdout)
        self.assertIn("test environments", r.stdout)  # the policy note
        self.assertEqual(self.run_py(CHECK_IDS, "vkn").returncode, 2)  # no values and no --generate
        r = self.run_py(CHECK_IDS, "vkn", *PUBLISHED_VKNS)
        self.assertEqual(r.returncode, 0, r.stdout)


class IdPolicyTests(unittest.TestCase):
    """data_needs.py: generated checksum-valid IDs are warnings; only real-looking data fails."""

    def run_needs(self, test_data: dict, *extra):
        doc = {"test_cases": [{"id": "TC-001", "technique": "use-case", "test_data": test_data, "steps": []}]}
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "tc.json"
            p.write_text(json.dumps(doc), encoding="utf-8", newline="\n")
            r = subprocess.run([sys.executable, str(DATA_NEEDS), str(p), "--schema-out", str(Path(tmp) / "s.json"),
                                *extra], capture_output=True, text=True, encoding="utf-8")
            r.schema = json.loads((Path(tmp) / "s.json").read_text(encoding="utf-8"))
            return r

    @staticmethod
    def lines(r, prefix):
        return [line for line in r.stdout.splitlines() if line.startswith(prefix)]

    def test_generated_ids_are_warnings_not_failures(self):
        rng = random.Random(1)
        r = self.run_needs({"tckn": ids.gen_tckn(rng), "iban": ids.gen_tr_iban(rng), "email": "qa+1@example.test"})
        self.assertEqual(r.returncode, 0, r.stdout)
        warnings = self.lines(r, "WARNING")
        self.assertEqual(len(warnings), 2, r.stdout)
        self.assertTrue(all("verify synthetic origin" in w for w in warnings))
        self.assertEqual(self.lines(r, "ERROR"), [])
        types = {f["name"]: f["type"] for f in r.schema["fields"]}
        self.assertEqual((types["tckn"], types["iban"]), ("tckn", "iban_tr"))  # regenerate them, not as ints
        r = self.run_needs({"tckn": "10000000146"}, "--lang", "tr")
        self.assertIn("sentetik kaynağını doğrulayın", r.stdout)

    def test_reserved_example_domains_pass_and_real_domains_fail(self):
        r = self.run_needs({"e1": "a@example.org", "e2": "b@qa.example.com", "e3": "c@shop.test"})
        self.assertEqual(r.returncode, 0, r.stdout)
        self.assertEqual(self.lines(r, "ERROR") + self.lines(r, "WARNING"), [])
        r = self.run_needs({"email": "real.person@gmail.com", "tckn": "10000000146"})
        self.assertEqual(r.returncode, 1, r.stdout)
        errors = self.lines(r, "ERROR")
        self.assertEqual(len(errors), 1)
        self.assertIn("gmail.com", errors[0])
        self.assertIn("verify synthetic origin", self.lines(r, "WARNING")[0])  # the TCKN is still only a warning


if __name__ == "__main__":
    unittest.main()
