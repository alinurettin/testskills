"""Tests for the preparing-test-data skill scripts (standard library only).

Run:  python -m unittest tests.test_preparing_test_data -v
"""
from __future__ import annotations

import csv
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "skills" / "preparing-test-data"
SCRIPTS = SKILL / "scripts"
FIX = Path(__file__).resolve().parent / "fixtures" / "preparing-test-data"
SECRET = "unit-test-secret-0123456789abcdef"


def load(path: Path):
    spec = importlib.util.spec_from_file_location(f"ptd_{path.stem}", path)
    mod = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(path.parent))
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.path.remove(str(path.parent))
    return mod


gd = load(SCRIPTS / "gen_data.py")
md = load(SCRIPTS / "mask_data.py")
dn = load(SCRIPTS / "data_needs.py")


# --- independent reference implementations (written differently from gen_data.py) -------------
def ref_tckn(s: str) -> bool:
    if len(s) != 11 or not s.isdigit() or s[0] == "0":
        return False
    d = list(map(int, s))
    odd, even = sum(d[0:9:2]), sum(d[1:8:2])
    return (odd * 7 - even) % 10 == d[9] and sum(d[:10]) % 10 == d[10]


def ref_vkn(s: str) -> bool:
    if len(s) != 10 or not s.isdigit():
        return False
    total = 0
    for pos in range(1, 10):
        t = (int(s[pos - 1]) + 10 - pos) % 10
        v = (t * pow(2, 10 - pos, 9)) % 9
        if t != 0 and v == 0:
            v = 9
        total += v
    return (10 - total % 10) % 10 == int(s[9])


def ref_iban(s: str) -> bool:
    s = s.replace(" ", "")
    if len(s) != 26 or not s.startswith("TR") or s[9] != "0":  # TR + 2 check + 5 bank + reserve 0 + 16
        return False
    rem = 0
    for ch in s[4:] + s[:4]:
        for digit in (str(ord(ch) - 55) if ch.isalpha() else ch):
            rem = (rem * 10 + int(digit)) % 97
    return rem == 1


def gen(fields, rows=100, seed=1, **kw):
    return gd.generate_table({"name": "t", "fields": fields, "unique": kw.pop("unique", [])}, rows, seed, **kw)


class ChecksumTests(unittest.TestCase):
    def test_generated_identifiers_pass_independent_checks(self):
        fields = [{"name": "t", "type": "tckn"}, {"name": "v", "type": "vkn"}, {"name": "i", "type": "iban_tr"}]
        _, rows, _ = gen(fields, rows=1000, seed=7)
        for r in rows:
            self.assertTrue(ref_tckn(r["t"]), r["t"])
            self.assertNotEqual(r["t"][0], "0")
            self.assertTrue(ref_vkn(r["v"]), r["v"])
            self.assertTrue(ref_iban(r["i"]), r["i"])

    def test_validators_reject_corrupted_values(self):
        self.assertTrue(gd.is_valid_tckn("10000000078"))
        self.assertFalse(gd.is_valid_tckn("10000000079"))
        self.assertFalse(gd.is_valid_tckn("01234567890"))
        self.assertTrue(gd.is_valid_iban("TR33 0006 1005 1978 6457 8413 26"))  # ISO 13616 example
        self.assertFalse(gd.is_valid_iban("TR33 0006 1005 1978 6457 8413 27"))
        v = gd.gen_vkn(__import__("random").Random(3))
        bad = v[:9] + str((int(v[9]) + 1) % 10)
        self.assertTrue(ref_vkn(v) and gd.is_valid_vkn(v))
        self.assertFalse(ref_vkn(bad) or gd.is_valid_vkn(bad))

    def test_edge_identifiers_are_valid_too(self):
        fields = [{"name": n, "type": n, "edge": True} for n in ("tckn", "vkn", "iban_tr")]
        _, rows, n_edge = gen(fields, rows=200, seed=3, edge_fraction=0.5, mark_edges=True)
        self.assertEqual(n_edge, 100)
        for r in rows:
            self.assertTrue(ref_tckn(r["tckn"]) and ref_vkn(r["vkn"]) and ref_iban(r["iban_tr"]), r)


class GenerationTests(unittest.TestCase):
    def test_same_seed_same_output_different_seed_differs(self):
        with tempfile.TemporaryDirectory() as tmp:
            outs = []
            for i, seed in enumerate(("42", "42", "43")):
                d = Path(tmp) / str(i)
                r = subprocess.run([sys.executable, str(SCRIPTS / "gen_data.py"), "--schema",
                                    str(SKILL / "assets" / "schema-example.json"), "--seed", seed, "--lang", "tr",
                                    "--out", str(d)], capture_output=True, text=True, encoding="utf-8")
                self.assertEqual(r.returncode, 0, r.stderr)
                outs.append((d / "customers.csv").read_bytes() + (d / "accounts.csv").read_bytes())
            self.assertEqual(outs[0], outs[1])
            self.assertNotEqual(outs[0], outs[2])

    def test_ref_integrity_and_uniqueness(self):
        schema = json.loads((SKILL / "assets" / "schema-example.json").read_text(encoding="utf-8"))
        generated = {}
        for t in schema["tables"]:
            cols, rows, _ = gd.generate_table(t, t["rows"], 5, "tr", 0.2, generated)
            generated[t["name"]] = (cols, rows)
        ids = {r["id"] for r in generated["customers"][1]}
        accounts = generated["accounts"][1]
        self.assertTrue(all(a["customer_id"] in ids for a in accounts))
        for col in ("id", "email", "tckn"):
            vals = [r[col] for r in generated["customers"][1]]
            self.assertEqual(len(vals), len(set(vals)), col)
        self.assertEqual(len({a["iban"] for a in accounts}), len(accounts))

    def test_ref_from_csv_file_and_distinct(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "parents.csv"
            p.write_text("pid;name\nP1;a\nP2;b\nP3;c\n", encoding="utf-8")
            fields = [{"name": "x", "type": "ref", "source": "parents.csv:pid", "distinct": True}]
            _, rows, _ = gen(fields, rows=3, search_dirs=[Path(tmp)])
            self.assertEqual(sorted(r["x"] for r in rows), ["P1", "P2", "P3"])
            with self.assertRaises(gd.SchemaError):
                gen(fields, rows=4, search_dirs=[Path(tmp)])

    def test_edge_fraction_single_field_per_row(self):
        fields = [{"name": "n", "type": "int", "min": 10, "max": 20, "edge": True},
                  {"name": "s", "type": "text", "min_len": 1, "max_len": 12, "charset": "turkish", "edge": True},
                  {"name": "c", "type": "city_tr", "edge": True}]
        _, rows, n_edge = gen(fields, rows=200, seed=9, edge_fraction=0.25, mark_edges=True)
        marked = [r for r in rows if r["_edge"]]
        self.assertEqual(n_edge, 50)
        self.assertEqual(len(marked), 50)
        self.assertEqual({r["_edge"] for r in marked}, {"n", "s", "c"})
        for r in rows:
            self.assertTrue(10 <= r["n"] <= 20)
            self.assertLessEqual(len(r["s"]), 12)
        self.assertTrue({r["n"] for r in marked if r["_edge"] == "n"} <= {10, 11, 19, 20})
        _, rows0, n0 = gen(fields, rows=50, edge_fraction=0.0, mark_edges=True)
        self.assertEqual(n0, 0)

    def test_email_domain_always_reserved_and_ascii_folded(self):
        fields = [{"name": "ad", "type": "first_name", "edge": True}, {"name": "soyad", "type": "last_name"},
                  {"name": "e", "type": "email", "from": ["ad", "soyad"], "edge": True},
                  {"name": "e2", "type": "email", "domain": "example.test", "pool": "en"}]
        _, rows, _ = gen(fields, rows=500, seed=11, lang="tr", edge_fraction=0.4)
        for r in rows:
            self.assertTrue(r["e"].endswith("@example.com"), r["e"])
            self.assertTrue(r["e2"].endswith("@example.test"), r["e2"])
            local = r["e"].split("@")[0]
            self.assertTrue(local.isascii() and len(local) <= 64, local)
        self.assertEqual(gd.ascii_fold("Işıl Çağrı ŞÜKRÜ Gökçe"), "isil.cagri.sukru.gokce")
        self.assertTrue(any(ch in "çğıöşüİ" for r in rows for ch in r["ad"]))

    def test_schema_errors_are_helpful(self):
        errs = gd.validate_schema({"fields": [
            {"name": "a", "type": "decmal"}, {"name": "b", "type": "text", "max_lenght": 3},
            {"name": "c", "type": "email", "domain": "gmail.com"}, {"name": "d", "type": "int", "min": 5, "max": 1},
            {"name": "r", "type": "ref", "source": "x:id", "edge": True}], "unique": ["zz"]})
        text = "\n".join(errs)
        for needle in ("did you mean 'decimal'", "did you mean 'max_len'", "example.com", "greater than max",
                       "referential integrity", "unique field 'zz'"):
            self.assertIn(needle, text)
        self.assertEqual(gd.validate_schema(json.loads((SKILL / "assets" / "schema-example.json")
                                                       .read_text(encoding="utf-8"))), [])

    def test_unique_domain_too_small_fails_clearly(self):
        with self.assertRaises(gd.SchemaError) as cm:
            gen([{"name": "e", "type": "enum", "values": ["a", "b"]}], rows=3, unique=["e"])
        self.assertIn("too small", str(cm.exception))


class MaskTests(unittest.TestCase):
    def run_mask(self, rules, inp, out, env_secret=SECRET, extra=()):
        env = dict(os.environ)
        env.pop("MASK_SECRET", None)
        if env_secret:
            env["MASK_SECRET"] = env_secret
        return subprocess.run([sys.executable, str(SCRIPTS / "mask_data.py"), "--in", str(inp), "--rules", str(rules),
                               "--out", str(out), *extra], capture_output=True, text=True, encoding="utf-8", env=env)

    def read(self, p, delim=";"):
        with open(p, encoding="utf-8", newline="") as fh:
            return list(csv.DictReader(fh, delimiter=delim))

    def test_refuses_without_secret(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "m.csv"
            r = self.run_mask(SKILL / "assets" / "mask-rules-example.json", FIX / "extract.csv", out, env_secret=None)
            self.assertEqual(r.returncode, 2)
            self.assertIn("MASK_SECRET", r.stderr)
            self.assertFalse(out.exists())
            r = self.run_mask(SKILL / "assets" / "mask-rules-example.json", FIX / "extract.csv", out, "short")
            self.assertEqual(r.returncode, 2)

    def test_deterministic_and_join_preserving(self):
        rules = {"columns": {"musteri_no": {"rule": "hash", "length": 16}, "ad": {"rule": "fake", "type": "first_name"},
                             "email": {"rule": "fake", "type": "email", "normalize": "lower"},
                             "cep_tel": {"rule": "fake", "type": "phone_tr", "normalize": "phone"},
                             "tckn": {"rule": "fake", "type": "tckn"}, "iban": {"rule": "fake", "type": "iban_tr"},
                             "dogum_tarihi": {"rule": "generalize", "to": "year"},
                             "posta_kodu": {"rule": "generalize", "to": "postcode"}}}
        acc_rules = {"columns": {"musteri_no": {"rule": "hash", "length": 16}, "hesap_id": "keep", "bakiye": "keep"}}
        with tempfile.TemporaryDirectory() as tmp:
            t = Path(tmp)
            (t / "r.json").write_text(json.dumps(rules), encoding="utf-8")
            (t / "a.json").write_text(json.dumps(acc_rules), encoding="utf-8")
            r1 = self.run_mask(t / "r.json", FIX / "extract.csv", t / "m1.csv")
            r2 = self.run_mask(t / "r.json", FIX / "extract.csv", t / "m2.csv")
            ra = self.run_mask(t / "a.json", FIX / "accounts.csv", t / "acc.csv")
            self.assertEqual(r1.returncode, 0, r1.stdout + r1.stderr)
            self.assertEqual(ra.returncode, 0, ra.stdout + ra.stderr)
            self.assertEqual((t / "m1.csv").read_bytes(), (t / "m2.csv").read_bytes())
            cust, acc = self.read(t / "m1.csv"), self.read(t / "acc.csv", ",")
            # same input -> same output (row 1 and row 4 are the same person, written differently)
            for col in ("musteri_no", "ad", "email", "cep_tel", "tckn", "iban"):
                self.assertEqual(cust[0][col], cust[3][col], col)
            self.assertTrue(gd.is_valid_tckn(cust[0]["tckn"]) and gd.is_valid_iban(cust[0]["iban"]))
            self.assertTrue(cust[0]["email"].endswith("@example.com"))
            self.assertNotIn("100001", (t / "m1.csv").read_text(encoding="utf-8"))
            self.assertEqual([c["dogum_tarihi"] for c in cust], ["1985", "1990", "2000", "1985"])
            self.assertEqual(cust[1]["posta_kodu"], "06")
            # joins survive: hashed keys in accounts match hashed keys in customers
            cust_keys = {c["musteri_no"] for c in cust}
            joined = [a for a in acc if a["musteri_no"] in cust_keys]
            self.assertEqual([a["hesap_id"] for a in joined], ["A-1", "A-2", "A-3"])
            # a different secret gives different tokens
            self.run_mask(t / "r.json", FIX / "extract.csv", t / "m3.csv", env_secret=SECRET + "x")
            self.assertNotEqual(self.read(t / "m3.csv")[0]["musteri_no"], cust[0]["musteri_no"])

    def test_uncovered_pii_warning_default_drop_and_keep(self):
        rules = {"columns": {"segment": "keep", "not_var_olan_sutun": "drop"}}
        with tempfile.TemporaryDirectory() as tmp:
            t = Path(tmp)
            (t / "r.json").write_text(json.dumps(rules), encoding="utf-8")
            r = self.run_mask(t / "r.json", FIX / "extract.csv", t / "m.csv", env_secret=None,
                              extra=("--report", str(t / "rep.md")))
            self.assertEqual(r.returncode, 1)  # rule for a missing column needs a decision
            self.assertEqual(list(self.read(t / "m.csv")[0].keys()), ["segment"])  # everything else dropped
            report = (t / "rep.md").read_text(encoding="utf-8")
            self.assertIn("not_var_olan_sutun", report)
            self.assertIn("iletisim_bilgisi", report)  # content looks like e-mail although header does not
            r = self.run_mask(t / "r.json", FIX / "extract.csv", t / "k.csv", env_secret=None,
                              extra=("--default", "keep", "--lang", "tr"))
            self.assertEqual(r.returncode, 1)
            self.assertIn("KORUNDU", r.stdout)
            self.assertIn("'tckn'", r.stdout)

    def test_helpers(self):
        self.assertEqual(md.pii_header("MusteriSoyadi"), "soyadi")
        self.assertEqual(md.pii_header("Doğum Tarihi"), "dogum")
        self.assertIsNone(md.pii_header("urun_kodu"))
        self.assertIsNone(md.pii_header("adet"))
        self.assertEqual(md.generalize("45.250,75", {"bucket": 10000}), "[40000,50000)")
        self.assertEqual(md.generalize("-5", {"bucket": 10}), "[-10,0)")
        self.assertEqual(md.generalize("2000-02-29T10:00:00", {"to": "year-month"}), "2000-02")
        self.assertIsNone(md.generalize("abc", {"bucket": 10}))
        self.assertEqual(md.normalize("+90 532 111 22 33", "phone"), md.normalize("0532 111 2233", "phone"))
        with self.assertRaises(md.RulesError):
            md.load_rules({"columns": {"x": {"rule": "fake", "type": "passport"}}})


class DataNeedsTests(unittest.TestCase):
    def test_exact_vs_generated_and_pii_flags(self):
        doc = {"test_cases": [
            {"id": "TC-001", "technique": "boundary-value-analysis", "test_data": {"tutar": "100,00 TL"}, "steps": []},
            {"id": "TC-002", "technique": "use-case", "test_data": {"email": "real.person@gmail.com"}, "steps": []},
            {"id": "TC-003", "technique": "error-guessing", "steps": [{"action": "x", "expected": "y"}]}]}
        report, schema, pii = dn.analyse(doc, "en")
        self.assertIn("| TC-001 | boundary-value-analysis | tutar=100,00 TL | exact (fixture) |", report)
        self.assertIn("any valid (generate)", report)
        self.assertIn("TC-003: no test data documented", report)
        self.assertEqual(len(pii), 1)
        self.assertIn("gmail.com", pii[0])
        self.assertEqual(gd.validate_schema(schema), [])
        tutar = next(f for f in schema["fields"] if f["name"] == "tutar")
        self.assertEqual((tutar["type"], tutar["decimal_sep"]), ("decimal", ","))


class CliTests(unittest.TestCase):
    def test_help_runs(self):
        for script in ("gen_data.py", "mask_data.py", "data_needs.py"):
            r = subprocess.run([sys.executable, str(SCRIPTS / script), "--help"], capture_output=True, text=True,
                               encoding="utf-8")
            self.assertEqual(r.returncode, 0, script + r.stderr)


if __name__ == "__main__":
    unittest.main()
