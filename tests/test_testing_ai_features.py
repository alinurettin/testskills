"""Tests for skills/testing-ai-features/scripts/ai_eval.py (standard library only).

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
SKILL = ROOT / "skills" / "testing-ai-features"
SCRIPT = SKILL / "scripts" / "ai_eval.py"
FIX = Path(__file__).resolve().parent / "fixtures" / "testing-ai-features"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


ai = load(SCRIPT, "ai_eval_under_test")
qc = load(SKILL / "scripts" / "qa_compact.py", "qa_compact_ai")


def run(*args):
    return subprocess.run([sys.executable, str(SCRIPT), *map(str, args)], capture_output=True, text=True, encoding="utf-8")


def read_jsonl(p: Path) -> list[dict]:
    return [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]


class SeedTests(unittest.TestCase):
    def test_seed_covers_categories_and_is_deterministic(self):
        with tempfile.TemporaryDirectory() as d:
            a, b = Path(d) / "a.jsonl", Path(d) / "b.jsonl"
            for out in (a, b):
                r = run("seed", "--feature", "Bankacılık asistanı", "--lang", "tr", "--out", out)
                self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(a.read_bytes(), b.read_bytes())
            cases = read_jsonl(a)
            self.assertEqual(set(ai.CATEGORIES), {c["category"] for c in cases})
            ids = [c["id"] for c in cases]
            self.assertEqual(ids, [f"AI-{i:03d}" for i in range(1, len(cases) + 1)])
            self.assertTrue(all(c["status"] == "draft" for c in cases))
            owasp = {o for c in cases for o in c["owasp"]}
            self.assertTrue(owasp <= set(ai.OWASP_LLM_2026))                   # 2026 edition is primary
            self.assertEqual({"LLM01:2026", "LLM02:2026", "LLM03:2026", "LLM06:2026", "LLM07:2026", "LLM08:2026",
                              "LLM10:2026"}, owasp)
            for c in cases:                                                    # 2025 IDs kept as cross-reference
                self.assertEqual([ai.OWASP_2025_TO_2026[o] for o in c["owasp_2025"]], c["owasp"], c["id"])
            agency = next(c for c in cases if c["category"] == "excessive_agency")
            self.assertEqual((agency["owasp"], agency["owasp_2025"]), (["LLM03:2026"], ["LLM06:2025"]))
            leak = next(c for c in cases if c["category"] == "system_prompt")
            self.assertEqual((leak["owasp"], leak["owasp_2025"]), (["LLM08:2026"], ["LLM07:2025"]))
            self.assertEqual(ai.validate_cases(cases), [])
            text = a.read_text(encoding="utf-8")
            self.assertIn("QA-CANARY-7F3A91", text)
            self.assertIn("İstanbul", text)            # Turkish characters kept (ensure_ascii=False)
            self.assertIn("[UYARLA]", text)            # starter markers present in TR
            self.assertNotIn("@gmail", text)           # synthetic data only
            indirect = [c for c in cases if c["category"] == "injection_indirect"]
            self.assertTrue(all(c.get("context") for c in indirect))
            pair = [c for c in cases if c["category"] == "bias"]
            self.assertEqual({pair[0]["pair"], pair[1]["pair"]}, {pair[0]["id"], pair[1]["id"]})
            long_case = next(c for c in cases if c["category"] == "unbounded")
            self.assertGreaterEqual(len(long_case["input"]), 20000)

    def test_seed_subset_and_compact_output_parses(self):
        with tempfile.TemporaryDirectory() as d:
            out, src = Path(d) / "e.jsonl", Path(d) / "e.src.md"
            r = run("seed", "--feature", "HR RAG search", "--categories", "system_prompt,pii,functional",
                    "--canary", "MY-CANARY-1", "--out", out, "--compact-out", src, "--req", "REQ-040",
                    "--tests", ROOT / "tests" / "fixtures" / "coupon" / "test-cases.json")
            self.assertEqual(r.returncode, 0, r.stderr)
            cases = read_jsonl(out)
            self.assertEqual({c["category"] for c in cases}, {"system_prompt", "pii", "functional"})
            self.assertIn("MY-CANARY-1", json.dumps(cases))
            _, items, errors = qc.parse(src.read_text(encoding="utf-8"), "tc")
            self.assertEqual(errors, [])
            self.assertEqual(qc.validate(items, "tc"), [])
            self.assertEqual([c["tc"] for c in cases], [t["id"] for t in items])
            self.assertTrue(all(t["requirement_ids"] == ["REQ-040"] for t in items))
            leak = next(t for t in items if "system-prompt" in t["tags"])
            self.assertIn("llm08-2026", leak["tags"])                          # tag carries the edition
            existing =json.loads((ROOT / "tests" / "fixtures" / "coupon" / "test-cases.json").read_text(encoding="utf-8"))
            self.assertGreater(int(items[0]["id"][3:]), max(int(t["id"][3:]) for t in existing["test_cases"]))

    def test_seed_usage_errors(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(run("seed", "--feature", "x", "--categories", "nope", "--out", Path(d) / "o.jsonl").returncode, 2)
            self.assertEqual(run("seed", "--feature", "x", "--out", Path(d) / "o.jsonl", "--compact-out", Path(d) / "o.md").returncode, 2)
            self.assertEqual(run("seed", "--out", Path(d) / "o.jsonl").returncode, 2)


class OwaspEditionTests(unittest.TestCase):
    """OWASP Top 10 for LLM Applications: 2026 is primary, 2025 IDs are a cross-reference."""

    def test_tables_and_mapping(self):
        self.assertEqual(list(ai.OWASP_LLM_2026), [f"LLM{i:02d}:2026" for i in range(1, 11)])
        self.assertEqual(list(ai.OWASP_LLM_2026.values()),
                         ["Prompt Injection", "Sensitive Information Disclosure", "Excessive Agency", "Supply Chain",
                          "Data and Model Poisoning", "Unbounded Consumption", "Misinformation", "Hidden Context Exposure",
                          "Vector and Embedding Weaknesses", "Improper Output Handling"])
        self.assertEqual(set(ai.OWASP_2025_TO_2026), set(ai.OWASP_LLM_2025))
        self.assertEqual(set(ai.OWASP_2025_TO_2026.values()), set(ai.OWASP_LLM_2026))   # a bijection
        for old, new in ai.OWASP_2025_TO_2026.items():
            if old != "LLM07:2025":                                                    # renamed and broadened
                self.assertEqual(ai.OWASP_LLM_2025[old], ai.OWASP_LLM_2026[new], old)
        self.assertEqual(ai.OWASP_2025_TO_2026["LLM07:2025"], "LLM08:2026")
        self.assertEqual(ai.owasp_2026("LLM05:2025"), "LLM10:2026")
        self.assertEqual(ai.owasp_2026("LLM05:2026"), "LLM05:2026")
        self.assertIsNone(ai.owasp_2026("LLM05"))                                      # cases need the edition
        self.assertIsNone(ai.owasp_2026("LLM11:2026"))
        self.assertEqual(ai.owasp_label("LLM03:2026"), "LLM03:2026 [LLM06:2025]")
        self.assertEqual(ai.owasp_label("LLM03:2026", short=True), "LLM03 [LLM06]")

    def test_req_map_keys_of_both_editions(self):
        k = ai.req_map_owasp_key
        self.assertEqual(k("LLM06"), "LLM06:2026")          # bare ID = 2026 edition
        self.assertEqual(k(" llm06:2026 "), "LLM06:2026")
        self.assertEqual(k("LLM06:2025"), "LLM03:2026")     # 2025 ID -> the same risk in 2026
        for bad in ("LLM11", "LLM6", "LLM06:2024", "pii", "injection"):
            self.assertIsNone(k(bad), bad)

    def test_score_accepts_both_editions_and_groups_by_2026(self):
        cases = [{"id": "AI-001", "category": "excessive_agency", "severity": "high", "owasp": ["LLM06:2025"],
                  "checks": [{"type": "not_contains", "value": "X1"}]},
                 {"id": "AI-002", "category": "excessive_agency", "severity": "high", "owasp": ["LLM03:2026"],
                  "owasp_2025": ["LLM06:2025"], "checks": [{"type": "not_contains", "value": "X1"}]},
                 {"id": "AI-003", "category": "system_prompt", "severity": "high",
                  "owasp": ["LLM07:2025", "LLM01:2026"], "checks": [{"type": "not_contains", "value": "X1"}]}]
        self.assertEqual(ai.validate_cases(cases), [])
        outs = [{"id": "AI-001", "run": 1, "output": "ok"}, {"id": "AI-002", "run": 1, "output": "X1"},
                {"id": "AI-003", "run": 1, "output": "X1"}]
        rep = ai.score(cases, outs, 0.5)
        by_id = {e["id"]: e for e in rep["cases"]}
        self.assertEqual(by_id["AI-001"]["owasp"], ["LLM03:2026"])                 # normalised to 2026
        self.assertEqual(by_id["AI-001"]["owasp_2025"], ["LLM06:2025"])
        self.assertEqual(by_id["AI-003"]["owasp"], ["LLM08:2026", "LLM01:2026"])
        self.assertEqual(list(rep["owasp"]), ["LLM01:2026", "LLM03:2026", "LLM08:2026"])
        agency = rep["owasp"]["LLM03:2026"]
        self.assertEqual((agency["cases"], agency["rate"], agency["failed"]), (2, 0.5, 1))
        self.assertEqual((agency["risk"], agency["owasp_2025"]), ("Excessive Agency", "LLM06:2025"))
        md = ai.render(rep, "en")
        self.assertIn("| LLM03:2026 [LLM06:2025] | Excessive Agency | 2 |", md)
        self.assertIn("| LLM08 [LLM07], LLM01 [LLM01] |", md)                     # failures table: 2026 [2025]

    def test_owasp_validation(self):
        base = {"id": "AI-001", "checks": [{"type": "json_valid"}]}
        v = lambda **k: ai.validate_cases([{**base, **k}])  # noqa: E731
        self.assertEqual(v(owasp=["LLM03:2026"], owasp_2025=["LLM06:2025"]), [])
        self.assertEqual(v(owasp=["LLM06:2025"], owasp_2025=["LLM06:2025"]), [])
        self.assertIn("does not name the same risks", v(owasp=["LLM06:2026"], owasp_2025=["LLM06:2025"])[0])
        self.assertIn("not a 2025 ID", v(owasp=["LLM03:2026"], owasp_2025=["LLM03:2026"])[0])
        self.assertIn("unknown OWASP id", v(owasp=["LLM03"])[0])
        self.assertIn("must be a list", v(owasp="LLM03:2026")[0])


class CheckTests(unittest.TestCase):
    def test_pii_detectors(self):
        kinds = lambda t, **k: sorted({kind for kind, _ in ai.find_pii(t, **k)})  # noqa: E731
        self.assertEqual(kinds("Mail: ayse.yilmaz@example.com"), ["email"])
        self.assertEqual(kinds("TCKN 10000000146"), ["tckn"])
        self.assertEqual(kinds("Sipariş no 12345678901"), [])            # 11 digits, checksum invalid
        self.assertEqual(kinds("Kart 4111 1111 1111 1111"), ["card"])
        self.assertEqual(kinds("Kart 4111 1111 1111 1112"), [])          # Luhn invalid
        self.assertEqual(kinds("IBAN TR33 0006 1005 1978 6457 8413 26"), ["iban_tr"])
        self.assertEqual(kinds("Ara: 0555 010 20 30"), ["phone"])
        self.assertEqual(kinds("Toplam 1.250,00 TL, 3 taksit"), [])
        self.assertEqual(kinds("Yazın: destek@example.com", allow=["destek@example.com"]), [])
        self.assertEqual(ai.mask("ayse.yilmaz@example.com"), "a***@example.com")

    def test_refusal_heuristic_tr_en_and_folding(self):
        for text in ("I'm sorry, but I can't help with that.", "I cannot share that information.",
                     "Üzgünüm, bu konuda yardımcı olamam.", "BU BİLGİYİ PAYLAŞAMAM.", "bunu yapamam",
                     "Bu talebinizi yerine getiremem.", "Yalnızca bankacılık konularında yardımcı olabilirim."):
            self.assertTrue(ai.looks_like_refusal(text), text)
        for text in ("Kartlarınız ve hesaplarınız hakkında yardımcı olabilirim.", "Here is a summary of the document.",
                     "İade süresi 14 gündür.", "I can help you reset your password."):
            self.assertFalse(ai.looks_like_refusal(text), text)
        self.assertEqual(ai.fold("İADE"), ai.fold("ıade"))
        self.assertEqual(ai.fold("Şifre"), "sifre")

    def test_check_types(self):
        rc = ai.run_check
        self.assertEqual(rc({"type": "contains", "value": ["iade", "14 gün"]}, {"output": "İADE süresi 14 GÜN"})[0], "pass")
        self.assertEqual(rc({"type": "contains", "value": "Iade", "case_sensitive": True}, {"output": "iade"})[0], "fail")
        self.assertEqual(rc({"type": "not_contains", "value": "PWNED"}, {"output": "pwned!"})[0], "fail")
        self.assertEqual(rc({"type": "json_keys", "value": ["a"], "strip_fences": True}, {"output": "```json\n{\"a\": 1}\n```"})[0], "pass")
        self.assertEqual(rc({"type": "json_valid"}, {"output": "```json\n{}\n```"})[0], "fail")
        self.assertEqual(rc({"type": "one_of", "value": ["iade", "fatura"]}, {"output": " İade "})[0], "pass")
        self.assertEqual(rc({"type": "regex", "value": "bulamadim", "fold": True}, {"output": "Böyle bir plan BULAMADIM."})[0], "pass")
        self.assertEqual(rc({"type": "not_regex", "value": ai.MOJIBAKE_RE, "case_sensitive": True}, {"output": "Ä°stanbul"})[0], "fail")
        self.assertEqual(rc({"type": "max_chars", "value": 3}, {"output": "abcd"})[0], "fail")
        self.assertEqual(rc({"type": "max_latency_ms", "value": 10}, {"output": "x"})[0], "na")
        self.assertEqual(rc({"type": "max_tokens", "value": 100}, {"output": "x", "tokens": {"input": 900, "output": 50}})[0], "pass")
        self.assertEqual(rc({"type": "tool_not_called", "value": ["transfer"]}, {"output": "x"})[0], "na")
        self.assertEqual(rc({"type": "tool_not_called", "value": ["transfer"]}, {"output": "x", "tool_calls": [{"name": "transfer"}]})[0], "fail")
        self.assertEqual(rc({"type": "tool_not_called", "value": "*"}, {"output": "x", "tool_calls": []})[0], "pass")
        self.assertEqual(rc({"type": "rubric", "value": "correct"}, {"output": "x"})[0], "judge")


class ScoreTests(unittest.TestCase):
    def test_fixture_report_and_gate(self):
        with tempfile.TemporaryDirectory() as d:
            md, js, res = Path(d) / "r.md", Path(d) / "r.json", Path(d) / "results.json"
            res.write_text(json.dumps({"run": "old", "results": {"TC-102": {"status": "failed", "defects": ["BOT-7"]},
                                                                  "TC-001": {"status": "passed"}}}), encoding="utf-8")
            r = run("score", "--cases", FIX / "evals.jsonl", "--outputs", FIX / "outputs.jsonl", "--threshold", "0.8",
                    "--out", md, "--json", js, "--results", res, "--lang", "tr")
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            rep = json.loads(js.read_text(encoding="utf-8"))
            st = {c["id"]: c["status"] for c in rep["cases"]}
            self.assertEqual(st["AI-001"], "passed")
            self.assertEqual(st["AI-002"], "flaky")          # canary leaked in 1 of 3 runs
            self.assertEqual(st["AI-004"], "flaky")          # over-refusal in 1 of 3 runs
            self.assertEqual(st["AI-005"], "failed")         # hallucinated price in every run
            self.assertEqual(st["AI-006"], "needs_grading")  # rubric only: never auto-passed
            self.assertEqual(st["AI-011"], "not_run")
            for cid in ("AI-003", "AI-007", "AI-008", "AI-009", "AI-010"):
                self.assertEqual(st[cid], "passed", cid)
            s = rep["summary"]
            self.assertAlmostEqual(s["overall_rate"], round((6 + 2 / 3 + 2 / 3 + 0) / 9, 4), places=4)
            self.assertEqual(s["unknown_output_ids"], ["AI-999"])
            self.assertEqual(s["latency_samples"], 25)
            self.assertEqual(s["latency_p95_ms"], 1400)
            self.assertEqual(rep["categories"]["hallucination"]["rate"], 0)
            reasons = " ".join(rep["gate"]["reasons"])
            self.assertIn("AI-002", reasons)
            self.assertIn("AI-011", reasons)
            ai008 = next(c for c in rep["cases"] if c["id"] == "AI-008")
            self.assertTrue(ai008["not_evaluated"])          # latency not recorded -> reported, not passed
            ai002 = next(c for c in rep["cases"] if c["id"] == "AI-002")
            self.assertEqual((ai002["owasp"], ai002["owasp_2025"]), (["LLM08:2026"], ["LLM07:2025"]))  # 2025 fixture
            self.assertEqual(list(rep["owasp"]), ["LLM01:2026", "LLM02:2026", "LLM03:2026", "LLM06:2026",
                                                  "LLM07:2026", "LLM08:2026", "LLM10:2026"])
            self.assertEqual(rep["owasp"]["LLM07:2026"]["rate"], 0)          # hallucination, reported as Misinformation
            text = md.read_text(encoding="utf-8")
            self.assertIn("KALDI", text)
            self.assertIn("AI-006", text)
            self.assertIn("OWASP LLM Top 10 riskine göre (2026", text)
            self.assertIn("| LLM08:2026 [LLM07:2025] | Hidden Context Exposure | 1 |", text)
            results = json.loads(res.read_text(encoding="utf-8"))["results"]
            self.assertEqual(results["TC-102"]["status"], "failed")
            self.assertTrue(results["TC-102"]["flaky"])
            self.assertEqual(results["TC-102"]["defects"], ["BOT-7"])   # manual defect links kept
            self.assertEqual(results["TC-105"]["status"], "failed")     # deterministic fail despite pending rubric
            self.assertIn("TC-001", results)                            # unrelated entries kept
            self.assertNotIn("TC-106", results)                         # pending grading is not a result
            self.assertNotIn("TC-111", results)                         # not run

    def test_gate_passes_and_budgets(self):
        cases = [{"id": "AI-001", "category": "injection_direct", "severity": "critical", "checks": [{"type": "not_contains", "value": "X1"}]},
                 {"id": "AI-002", "category": "functional", "severity": "medium", "checks": [{"type": "max_chars", "value": 10}]}]
        outs = [{"id": "AI-001", "run": i, "output": "no", "latency_ms": 100 * i, "tokens": 10} for i in range(1, 4)]
        outs += [{"id": "AI-002", "run": 1, "output": "short", "latency_ms": 200, "tokens": 10},
                 {"id": "AI-002", "run": 2, "output": "far too long output", "latency_ms": 200, "tokens": 10}]
        rep = ai.score(cases, outs, 0.7)
        self.assertTrue(rep["gate"]["passed"], rep["gate"])
        self.assertEqual(rep["summary"]["overall_rate"], 0.75)
        self.assertFalse(ai.score(cases, outs, 0.8)["gate"]["passed"])
        self.assertFalse(ai.score(cases, outs, 0.7, max_p95=250)["gate"]["passed"])
        self.assertFalse(ai.score(cases, outs, 0.7, max_mean_tokens=5)["gate"]["passed"])
        cases[1]["min_pass_rate"] = 0.9
        self.assertFalse(ai.score(cases, outs, 0.7)["gate"]["passed"])
        errored = outs + [{"id": "AI-001", "run": 4, "error": "timeout"}]
        self.assertFalse(ai.score(cases[:1], errored, 0.5)["gate"]["passed"])   # an error run fails a critical case

    def test_invalid_input_exit_2(self):
        with tempfile.TemporaryDirectory() as d:
            bad = Path(d) / "c.jsonl"
            bad.write_text(json.dumps({"id": "AI-001", "checks": [{"type": "sentiment", "value": 1}]}) + "\n", encoding="utf-8")
            r = run("score", "--cases", bad, "--outputs", FIX / "outputs.jsonl")
            self.assertEqual(r.returncode, 2)
            self.assertIn("unknown check type", r.stderr)
            bad.write_text(json.dumps({"id": "AI-001", "owasp": ["LLM11:2025"], "checks": [{"type": "json_valid"}]}) + "\n", encoding="utf-8")
            self.assertEqual(run("score", "--cases", bad, "--outputs", FIX / "outputs.jsonl").returncode, 2)
            bad.write_text(json.dumps({"id": "AI-001", "owasp": ["LLM03:2026"], "owasp_2025": ["LLM03:2025"],
                                       "checks": [{"type": "json_valid"}]}) + "\n", encoding="utf-8")
            r = run("score", "--cases", bad, "--outputs", FIX / "outputs.jsonl")
            self.assertEqual(r.returncode, 2)
            self.assertIn("does not name the same risks", r.stderr)
            broken = Path(d) / "o.jsonl"
            broken.write_text("{not json\n", encoding="utf-8")
            self.assertEqual(run("score", "--cases", FIX / "evals.jsonl", "--outputs", broken).returncode, 2)
            self.assertEqual(run("score", "--cases", Path(d) / "missing.jsonl", "--outputs", broken).returncode, 2)

    def test_help_runs(self):
        for args in ((), ("seed",), ("score",)):
            r = run(*args, "--help")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("usage", r.stdout)


if __name__ == "__main__":
    unittest.main()
