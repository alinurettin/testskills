"""Tests for --req-map: requirement links of the generated test cases (standard library only).

openapi_tests.py (testing-apis), mobile_checklist.py (testing-mobile-apps), nfr_checklist.py
(testing-nonfunctional) and ai_eval.py seed --compact-out (testing-ai-features) link each generated
test to the requirement(s) of its operation / capability / area / category instead of one --req.

Run:  python -m unittest discover -s tests -v
"""
from __future__ import annotations

import importlib.util
import inspect
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SK = ROOT / "skills"
FIX = Path(__file__).resolve().parent / "fixtures" / "req-mapping"
OPENAPI = SK / "testing-apis" / "scripts" / "openapi_tests.py"
MOBILE = SK / "testing-mobile-apps" / "scripts" / "mobile_checklist.py"
NFR = SK / "testing-nonfunctional" / "scripts" / "nfr_checklist.py"
AI = SK / "testing-ai-features" / "scripts" / "ai_eval.py"
QC = SK / "testing-apis" / "scripts" / "qa_compact.py"
RTM = SK / "tracing-requirements" / "scripts" / "build_rtm.py"
DOC = FIX / "openapi.json"


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


qc = load(QC, "qa_compact_req_mapping")


def run(*args):
    return subprocess.run([sys.executable, *map(str, args)], capture_output=True, text=True, encoding="utf-8")


def write_json(path: Path, data) -> Path:
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return path


def parse(src: Path) -> list[dict]:
    _, items, errors = qc.parse(src.read_text(encoding="utf-8"), "tc")
    assert not errors, errors
    assert not qc.validate(items, "tc"), qc.validate(items, "tc")
    return items


class OpenApiReqMapTests(unittest.TestCase):
    MAP = {"default": "REQ-100",
           "operations": {"getItem": "REQ-102", "get /items/{itemId}": "REQ-199",  # operationId wins over METHOD /path
                          "put  /items/{itemId}": "REQ-103",                        # key normalised: PUT /items/{itemId}
                          "createItem": "REQ-198"},                                  # x-req in the document wins
           "tags": {"Items": "REQ-101", "Admin": "REQ-104"},
           "capabilities": {"push": "REQ-031"}}                                      # other scripts' keys are ignored

    def generate(self, d, *args):
        out, spec = Path(d) / "api.src.md", Path(d) / "api.spec.ts"
        r = run(OPENAPI, DOC, "--out", out, "--spec-out", spec, *args)
        return r, out, spec

    @staticmethod
    def by_operation(items) -> dict[str, set[tuple[str, ...]]]:
        ops: dict[str, set[tuple[str, ...]]] = {}
        for t in items:
            op = " ".join(t["title"].split(" ")[:2])  # every title starts with "METHOD /path"
            ops.setdefault(op, set()).add(tuple(t["requirement_ids"]))
        return ops

    def test_precedence_x_req_operation_id_method_path_first_tag_default(self):
        with tempfile.TemporaryDirectory() as d:
            m = write_json(Path(d) / "map.json", self.MAP)
            r, out, _ = self.generate(d, "--req-map", m, "--req", "REQ-900")
            self.assertEqual(r.returncode, 0, r.stderr)
            ops = self.by_operation(parse(out))
            self.assertEqual(ops, {
                "POST /items": {("REQ-105", "REQ-106")},        # x-req (list) beats operations[createItem]
                "GET /items/{itemId}": {("REQ-102",)},          # operationId beats "GET /items/{itemId}"
                "PUT /items/{itemId}": {("REQ-103",)},          # no operationId: "METHOD /path"
                "DELETE /items/{itemId}": {("REQ-104",)},       # first tag (Admin), not Items
                "GET /items": {("REQ-101",)},                   # tag
                "GET /health": {("REQ-100",)},                  # req-map default beats --req
            })
            self.assertIn("requirements: ", r.stdout)
            self.assertIn("# req-map: POST /items -> REQ-105, REQ-106 (x-req)", out.read_text(encoding="utf-8"))

    def test_req_is_the_last_fallback(self):
        with tempfile.TemporaryDirectory() as d:
            m = write_json(Path(d) / "map.json", {"tags": {"Items": "REQ-101"}})
            r, out, _ = self.generate(d, "--req-map", m, "--req", "REQ-900")
            self.assertEqual(r.returncode, 0, r.stderr)
            ops = self.by_operation(parse(out))
            self.assertEqual(ops["GET /health"], {("REQ-900",)})
            self.assertEqual(ops["DELETE /items/{itemId}"], {("REQ-900",)})  # first tag Admin is unmapped
            self.assertEqual(ops["GET /items"], {("REQ-101",)})

    def test_unmapped_operations_exit_2_and_write_nothing(self):
        with tempfile.TemporaryDirectory() as d:
            m = write_json(Path(d) / "map.json", {"tags": {"Items": "REQ-101"}})
            r, out, spec = self.generate(d, "--req-map", m)
            self.assertEqual(r.returncode, 2)
            self.assertIn("GET /health (getHealth)", r.stderr)
            self.assertIn("DELETE /items/{itemId} (deleteItem)", r.stderr)
            self.assertNotIn("GET /items (listItems)", r.stderr)
            self.assertFalse(out.exists() or spec.exists())
            r, out, _ = self.generate(d)  # neither --req nor --req-map: only POST /items has x-req
            self.assertEqual(r.returncode, 2)
            self.assertIn("no requirement for 5 operation(s)", r.stderr)

    def test_only_tag_needs_only_the_filtered_operations(self):
        with tempfile.TemporaryDirectory() as d:
            m = write_json(Path(d) / "map.json", {"operations": {"deleteItem": "REQ-104"}})
            r, out, _ = self.generate(d, "--req-map", m, "--only-tag", "Admin")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(self.by_operation(parse(out)), {"DELETE /items/{itemId}": {("REQ-104",)}})

    def test_backward_compatible_req_and_unchanged_spec(self):
        with tempfile.TemporaryDirectory() as d:
            r, out, spec = self.generate(d, "--req", "REQ-020,REQ-021")
            self.assertEqual(r.returncode, 0, r.stderr)
            items = parse(out)
            self.assertTrue(all(t["requirement_ids"] == ["REQ-020", "REQ-021"] for t in items
                                if not t["title"].startswith("POST /items")))
            self.assertTrue(all(t["requirement_ids"] == ["REQ-105", "REQ-106"] for t in items
                                if t["title"].startswith("POST /items")))
            plain_spec = spec.read_text(encoding="utf-8")
            m = write_json(Path(d) / "map.json", self.MAP)
            r2, out2, spec2 = self.generate(d, "--req-map", m)
            self.assertEqual(r2.returncode, 0, r2.stderr)
            self.assertEqual(spec2.read_text(encoding="utf-8"), plain_spec)  # the executable spec does not change
            self.assertEqual([t["title"] for t in parse(out2)], [t["title"] for t in items])

    def test_single_requirement_note(self):
        with tempfile.TemporaryDirectory() as d:
            doc = json.loads(DOC.read_text(encoding="utf-8"))
            del doc["paths"]["/items"]["post"]["x-req"]
            spec_doc = write_json(Path(d) / "o.json", doc)
            r = run(OPENAPI, spec_doc, "--req", "REQ-020", "--out", Path(d) / "o.src.md")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("note: all", r.stdout)
            self.assertIn("--req-map", r.stdout)

    def test_invalid_maps_and_x_req_exit_2(self):
        with tempfile.TemporaryDirectory() as d:
            bad_maps = [["REQ-1"], {"operations": {"getItem": 42}}, {"tags": {"Items": "REQ 1"}},
                        {"operations": ["getItem"]}, {"default": {"a": 1}}]
            for i, bad in enumerate(bad_maps):
                m = write_json(Path(d) / f"bad{i}.json", bad)
                r, _, _ = self.generate(d, "--req-map", m, "--req", "REQ-900")
                self.assertEqual(r.returncode, 2, bad)
                self.assertIn("error:", r.stderr)
            (Path(d) / "broken.json").write_text("{not json", encoding="utf-8")
            self.assertEqual(self.generate(d, "--req-map", Path(d) / "broken.json")[0].returncode, 2)
            self.assertEqual(self.generate(d, "--req-map", Path(d) / "missing.json")[0].returncode, 2)
            doc = json.loads(DOC.read_text(encoding="utf-8"))
            doc["paths"]["/items"]["post"]["x-req"] = 5
            r = run(OPENAPI, write_json(Path(d) / "x.json", doc), "--req", "REQ-900", "--out", Path(d) / "x.md")
            self.assertEqual(r.returncode, 2)
            self.assertIn("x-req", r.stderr)

    def test_unused_keys_warn_but_do_not_fail(self):
        with tempfile.TemporaryDirectory() as d:
            m = write_json(Path(d) / "map.json", {"default": "REQ-100", "operations": {"getItme": "REQ-1"},
                                                   "tags": {"Itemz": "REQ-2"}, "operation": {}, "_note": "comment"})
            r, _, _ = self.generate(d, "--req-map", m)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("operations key 'getItme' matches no operation", r.stderr)
            self.assertIn("tags key 'Itemz'", r.stderr)
            self.assertIn("unknown key 'operation'", r.stderr)
            self.assertNotIn("_note", r.stderr)

    def test_example_asset_is_a_valid_map(self):
        asset = SK / "testing-apis" / "assets" / "req-map-example.json"
        with tempfile.TemporaryDirectory() as d:
            r = run(OPENAPI, ROOT / "evals" / "trial-api" / "api" / "openapi.json", "--req-map", asset,
                    "--out", Path(d) / "o.src.md")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(r.stderr, "")  # every key of the example matches the trial API
            reqs = {r for t in parse(Path(d) / "o.src.md") for r in t["requirement_ids"]}
            self.assertEqual(reqs, {"REQ-021", "REQ-022", "REQ-023", "REQ-024"})


class RtmGapTests(unittest.TestCase):
    """The point of the map: an under-tested requirement becomes visible in the RTM."""

    REQS = {"project": "Req mapping (synthetic)", "language": "en", "requirements": [
        {"id": rid, "title": title, "text": f"{title}.", "type": "functional", "source": "OpenAPI", "priority": pri,
         "risk": risk, "status": "ready"}
        for rid, title, pri, risk in (
            ("REQ-105", "Create items", "high", {"likelihood": 3, "impact": 4}),
            ("REQ-106", "Item names are validated", "medium", {"likelihood": 2, "impact": 3}),
            ("REQ-110", "Health endpoint reports availability", "high", {"likelihood": 3, "impact": 4}),
            ("REQ-111", "Read, update and delete items", "high", {"likelihood": 3, "impact": 4}))]}

    def rtm(self, d: Path, *gen_args) -> dict:
        src, tc, req = d / "api.src.md", d / "test-cases.json", write_json(d / "requirements.json", self.REQS)
        r = run(OPENAPI, DOC, "--out", src, *gen_args)
        self.assertEqual(r.returncode, 0, r.stderr)
        r = run(QC, "tc", src, "--out", tc)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        r = run(RTM, "--requirements", req, "--tests", tc, "--out-dir", d / "rtm", "--json")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        rep = json.loads((d / "rtm" / "rtm.json").read_text(encoding="utf-8"))
        return {(g["id"], g["code"]) for g in rep["gaps"]}

    def test_req_map_exposes_thin_and_negative_free_requirement(self):
        with tempfile.TemporaryDirectory() as d:
            one = self.rtm(Path(d), "--req", "REQ-110,REQ-111")  # old way: everything on the same requirements
            self.assertFalse({("REQ-110", "THIN"), ("REQ-110", "NO_NEGATIVE")} & one)
            m = write_json(Path(d) / "map.json", {"default": "REQ-111", "operations": {"getHealth": "REQ-110"}})
            mapped = self.rtm(Path(d), "--req-map", m)
            self.assertIn(("REQ-110", "THIN"), mapped)          # high risk, one happy-path test
            self.assertIn(("REQ-110", "NO_NEGATIVE"), mapped)   # functional, no negative test
            self.assertFalse({g for g in mapped if g[0] == "REQ-111"})


class MobileReqMapTests(unittest.TestCase):
    CAT = json.loads((SK / "testing-mobile-apps" / "assets" / "mobile-checks.json").read_text(encoding="utf-8"))

    def generate(self, d, *args):
        out = Path(d) / "m.src.md"
        return run(MOBILE, "--platform", "both", "--out", out, *args), out

    def titles(self, check_id: str) -> str:
        return next(c["en"]["title"] for c in self.CAT["checks"] if c["id"] == check_id)

    def test_precedence_check_id_capability_union_default(self):
        multi = next(c for c in self.CAT["checks"] if {"camera", "location"} <= set(c["caps"]))
        core_id = next(c["id"] for c in self.CAT["checks"] if c["caps"] == ["core"])
        rmap = {"default": "REQ-200", "capabilities": {"core": "REQ-201", core_id: "REQ-202", "push": ["REQ-203", "REQ-204"],
                                                       "camera": "REQ-205", "location": "REQ-206"}}
        with tempfile.TemporaryDirectory() as d:
            r, out = self.generate(d, "--capabilities", "push,camera,location,payments",
                                   "--req-map", write_json(Path(d) / "map.json", rmap), "--req", "REQ-900")
            self.assertEqual(r.returncode, 0, r.stderr)
            by_title = {t["title"]: t for t in parse(out)}
            self.assertEqual(by_title[self.titles(core_id)]["requirement_ids"], ["REQ-202"])
            for t in by_title.values():
                tags = set(t["tags"])
                if "core" in tags and t["title"] != self.titles(core_id):
                    self.assertEqual(t["requirement_ids"], ["REQ-201"], t["title"])
                elif "push" in tags:
                    self.assertEqual(t["requirement_ids"], ["REQ-203", "REQ-204"], t["title"])
                elif "payments" in tags:
                    self.assertEqual(t["requirement_ids"], ["REQ-200"], t["title"])  # default beats --req
            expected = [{"camera": "REQ-205", "location": "REQ-206"}[k] for k in multi["caps"] if k in ("camera", "location")]
            self.assertEqual(by_title[multi["en"]["title"]]["requirement_ids"], expected)  # union, catalogue order

    def test_unmapped_capabilities_exit_2(self):
        with tempfile.TemporaryDirectory() as d:
            r, out = self.generate(d, "--capabilities", "push,payments",
                                   "--req-map", write_json(Path(d) / "map.json", {"capabilities": {"push": "REQ-203"}}))
            self.assertEqual(r.returncode, 2)
            self.assertIn("core (", r.stderr)
            self.assertIn("payments (", r.stderr)
            self.assertNotIn("push (", r.stderr)
            self.assertFalse(out.exists())
            r, _ = self.generate(d, "--capabilities", "push")  # neither --req nor --req-map
            self.assertEqual(r.returncode, 2)

    def test_backward_compatible_req_and_warnings(self):
        with tempfile.TemporaryDirectory() as d:
            r, out = self.generate(d, "--capabilities", "push", "--req", "REQ-030")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertTrue(all(t["requirement_ids"] == ["REQ-030"] for t in parse(out)))
            self.assertIn("note: all", r.stdout)
            m = write_json(Path(d) / "map.json", {"default": "REQ-030", "capabilities": {"teleport": "REQ-1"}})
            r, _ = self.generate(d, "--capabilities", "push", "--req-map", m)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("'teleport'", r.stderr)
            r, _ = self.generate(d, "--req-map", write_json(Path(d) / "bad.json", {"capabilities": {"push": 1}}))
            self.assertEqual(r.returncode, 2)

    def test_matrix_only_ignores_req_map(self):
        with tempfile.TemporaryDirectory() as d:
            r = run(MOBILE, "--devices", SK / "testing-mobile-apps" / "assets" / "devices-example.json",
                    "--matrix-out", Path(d) / "matrix.md", "--req-map", Path(d) / "missing.json")
            self.assertEqual(r.returncode, 0, r.stderr)


class NfrReqMapTests(unittest.TestCase):
    WCAG = json.loads((SK / "testing-nonfunctional" / "assets" / "wcag22-aa.json").read_text(encoding="utf-8"))

    def generate(self, d, kind, *args):
        out = Path(d) / f"{kind}.src.md"
        return run(NFR, kind, "--out", out, *args), out

    def manual(self, pred):
        feats = {"forms", "auth"}
        return next(c["sc"] for c in self.WCAG["criteria"] if c["method"] != "auto"
                    and ("all" in c["features"] or feats & set(c["features"])) and pred(set(c["features"])))

    def test_wcag_precedence(self):
        rmap = {"default": "REQ-300", "areas": {"wcag": "REQ-301", "forms": "REQ-302", "wcag:auth": "REQ-303",
                                                "auth": "REQ-399", "3.3.8": "REQ-304", "asvs": "REQ-398"}}
        forms_only = self.manual(lambda f: "forms" in f and "auth" not in f)
        both = self.manual(lambda f: {"forms", "auth"} <= f)
        general = self.manual(lambda f: not f & {"forms", "auth"})
        with tempfile.TemporaryDirectory() as d:
            r, out = self.generate(d, "wcag", "--features", "forms,auth", "--req", "REQ-900",
                                   "--req-map", write_json(Path(d) / "map.json", rmap))
            self.assertEqual(r.returncode, 0, r.stderr)
            items = parse(out)
            by_sc = {t["title"].split(" ")[1]: t["requirement_ids"] for t in items if t["title"].startswith("WCAG ")}
            self.assertEqual(by_sc["3.3.8"], ["REQ-304"])                  # criterion beats feature
            self.assertEqual(by_sc[forms_only], ["REQ-302"])               # feature
            self.assertEqual(by_sc[both], ["REQ-302", "REQ-303"])          # union; "wcag:auth" beats "auth"
            self.assertEqual(by_sc[general], ["REQ-301"])                  # kind
            axe = next(t for t in items if "axe" in t["tags"])
            self.assertTrue(axe["requirement_ids"])
            self.assertTrue(set(axe["requirement_ids"]) <= {"REQ-302", "REQ-303", "REQ-304"})
            self.assertFalse({"REQ-399", "REQ-398", "REQ-300", "REQ-900"} & {r for t in items for r in t["requirement_ids"]})
            rmap["areas"]["axe"] = "REQ-305"
            r, out = self.generate(d, "wcag", "--features", "forms,auth", "--req-map", write_json(Path(d) / "map.json", rmap))
            self.assertEqual(next(t for t in parse(out) if "axe" in t["tags"])["requirement_ids"], ["REQ-305"])

    def test_wcag_fallbacks_and_unmapped(self):
        general = self.manual(lambda f: not f & {"forms", "auth"})
        with tempfile.TemporaryDirectory() as d:
            m = write_json(Path(d) / "map.json", {"areas": {"forms": "REQ-302"}})
            r, out = self.generate(d, "wcag", "--features", "forms,auth", "--req-map", m)
            self.assertEqual(r.returncode, 2)
            self.assertIn(f"WCAG {general}", r.stderr)
            self.assertFalse(out.exists())
            r, out = self.generate(d, "wcag", "--features", "forms,auth", "--req-map", m, "--req", "REQ-900")
            self.assertEqual(r.returncode, 0, r.stderr)
            by_sc = {t["title"].split(" ")[1]: t["requirement_ids"] for t in parse(out) if t["title"].startswith("WCAG ")}
            self.assertEqual(by_sc[general], ["REQ-900"])                  # --req is the last fallback
            m = write_json(Path(d) / "map.json", {"default": "REQ-300"})
            r, out = self.generate(d, "wcag", "--features", "forms", "--req-map", m, "--req", "REQ-900")
            self.assertTrue(all(t["requirement_ids"] == ["REQ-300"] for t in parse(out)))  # default beats --req

    def test_asvs_chapters_and_qualified_features(self):
        rmap = {"areas": {"asvs": "REQ-400", "v8": "REQ-401", "asvs:auth": "REQ-402", "wcag:auth": "REQ-499"}}
        with tempfile.TemporaryDirectory() as d:
            r, out = self.generate(d, "asvs", "--features", "auth,authz,session",
                                   "--req-map", write_json(Path(d) / "map.json", rmap))
            self.assertEqual(r.returncode, 0, r.stderr)
            by_ch: dict[str, set] = {}
            for t in parse(out):
                by_ch.setdefault(t["title"].split(" ")[1], set()).add(tuple(t["requirement_ids"]))
            self.assertEqual(by_ch["V8"], {("REQ-401",)})                  # chapter key, case-insensitive
            self.assertEqual(by_ch["V6"], {("REQ-402",)})                  # "asvs:auth"
            self.assertEqual(by_ch["V7"], {("REQ-402",)})                  # session unmapped, auth mapped
            r, _ = self.generate(d, "asvs", "--features", "upload", "--req-map", write_json(Path(d) / "m2.json", {"areas": {"v8": "REQ-401"}}))
            self.assertEqual(r.returncode, 2)
            self.assertIn("ASVS V5", r.stderr)

    def test_backward_compatible_req_and_bad_map(self):
        with tempfile.TemporaryDirectory() as d:
            r, out = self.generate(d, "asvs", "--features", "authz", "--req", "REQ-013")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertTrue(all(t["requirement_ids"] == ["REQ-013"] for t in parse(out)))
            self.assertEqual(self.generate(d, "asvs", "--features", "authz")[0].returncode, 2)
            r, _ = self.generate(d, "asvs", "--req-map", write_json(Path(d) / "bad.json", {"areas": ["REQ-1"]}))
            self.assertEqual(r.returncode, 2)
            m = write_json(Path(d) / "warn.json", {"default": "REQ-013", "areas": {"formz": "REQ-1"}})
            r, _ = self.generate(d, "wcag", "--features", "forms", "--req-map", m)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("'formz'", r.stderr)


class AiEvalReqMapTests(unittest.TestCase):
    CATS = "functional,injection_direct,injection_indirect,pii,excessive_agency,multilingual"

    def seed(self, d, *args, cats=CATS):
        out, src = Path(d) / "evals.jsonl", Path(d) / "evals.src.md"
        r = run(AI, "seed", "--feature", "Synthetic support bot", "--categories", cats, "--out", out,
                "--compact-out", src, *args)
        return r, out, src

    def test_precedence_category_group_owasp_default(self):
        rmap = {"default": "REQ-500", "categories": {"injection": "REQ-501", "injection_indirect": "REQ-502",
                                                     "LLM06:2025": "REQ-503", "llm08": "REQ-504",
                                                     "LLM10:2026": "REQ-505"}}
        with tempfile.TemporaryDirectory() as d:
            r, out, src = self.seed(d, "--req-map", write_json(Path(d) / "map.json", rmap), "--req", "REQ-900")
            self.assertEqual(r.returncode, 0, r.stderr)
            cases = [json.loads(x) for x in out.read_text(encoding="utf-8").splitlines()]
            reqs = {t["id"]: t["requirement_ids"] for t in parse(src)}
            self.assertTrue(all(not k.startswith("_") for c in cases for k in c))  # JSONL format unchanged
            seen = set()
            for c in cases:
                got = reqs[c["tc"]]
                if c["category"] == "injection_direct":
                    self.assertEqual(got, ["REQ-501"])                       # group
                elif c["category"] == "injection_indirect":
                    self.assertEqual(got, ["REQ-502"])                       # exact category beats group
                elif c["category"] == "excessive_agency":
                    self.assertEqual(got, ["REQ-503"])                       # 2025 ID -> same risk (LLM03:2026)
                elif "LLM08:2026" in c["owasp"]:
                    self.assertEqual(got, ["REQ-504"])                       # bare ID = 2026 edition
                elif "LLM10:2026" in c["owasp"]:
                    self.assertEqual(got, ["REQ-505"])                       # 2026 ID
                else:
                    self.assertEqual(got, ["REQ-500"], c["id"])              # default beats --req
                seen.add(tuple(got))
            self.assertTrue({("REQ-503",), ("REQ-504",), ("REQ-505",)} <= seen)
            self.assertIn("requirements: ", r.stdout)
            self.assertIn("'llm08' is read as LLM08:2026 (Hidden Context Exposure)", r.stderr)  # bare ID differs by edition

    def test_owasp_keys_of_both_editions(self):
        rmap = {"default": "REQ-600", "categories": {"LLM06": "REQ-601", "LLM07:2025": "REQ-602",
                                                     "LLM03:2026": "REQ-603", "llm06:2025": "REQ-604",
                                                     "LLM01": "REQ-605"}}
        with tempfile.TemporaryDirectory() as d:
            r, out, src = self.seed(d, "--req-map", write_json(Path(d) / "map.json", rmap),
                                    cats="excessive_agency,unbounded,system_prompt,jailbreak")
            self.assertEqual(r.returncode, 0, r.stderr)
            cases = [json.loads(x) for x in out.read_text(encoding="utf-8").splitlines()]
            reqs = {t["id"]: t["requirement_ids"] for t in parse(src)}
            want = {"unbounded": ["REQ-601"],                  # bare LLM06 = LLM06:2026 Unbounded Consumption
                    "system_prompt": ["REQ-602"],              # LLM07:2025 System Prompt Leakage = LLM08:2026
                    "excessive_agency": ["REQ-603", "REQ-604"],  # LLM03:2026 and LLM06:2025 name the same risk
                    "jailbreak": ["REQ-605"]}                  # LLM01 is the same in both editions
            for c in cases:
                self.assertEqual(reqs[c["tc"]], want[c["category"]], c["id"])
            self.assertIn("'LLM06' is read as LLM06:2026 (Unbounded Consumption), not LLM06:2025", r.stderr)
            self.assertNotIn("'LLM01'", r.stderr)                     # no warning where the editions agree
            self.assertNotIn("not a category", r.stderr)

    def test_unmapped_categories_exit_2_and_write_nothing(self):
        with tempfile.TemporaryDirectory() as d:
            m = write_json(Path(d) / "map.json", {"categories": {"injection": "REQ-501"}})
            r, out, src = self.seed(d, "--req-map", m, cats="injection_direct,pii,bias")
            self.assertEqual(r.returncode, 2)
            self.assertIn("pii (", r.stderr)
            self.assertIn("bias (", r.stderr)
            self.assertNotIn("injection_direct (", r.stderr)
            self.assertFalse(out.exists() or src.exists())

    def test_backward_compatible_req_list_and_bad_map(self):
        with tempfile.TemporaryDirectory() as d:
            r, _, src = self.seed(d, "--req", "REQ-040, REQ-041", cats="pii")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertTrue(all(t["requirement_ids"] == ["REQ-040", "REQ-041"] for t in parse(src)))
            r, _, _ = self.seed(d, "--req-map", write_json(Path(d) / "bad.json", {"categories": {"pii": [1]}}), cats="pii")
            self.assertEqual(r.returncode, 2)
            r, _, _ = self.seed(d, "--req-map", write_json(Path(d) / "w.json", {"default": "REQ-040",
                                                                                "categories": {"prompt_injection": "REQ-1"}}),
                                cats="pii")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("'prompt_injection'", r.stderr)
            r = run(AI, "seed", "--feature", "x", "--categories", "pii", "--out", Path(d) / "only.jsonl",
                    "--req-map", Path(d) / "missing.json")          # no --compact-out: the map is not needed
            self.assertEqual(r.returncode, 0, r.stderr)


class SharedHelperTests(unittest.TestCase):
    """The helper is copied into each script (skills are self-contained); the copies must not drift."""

    def test_helpers_identical(self):
        mods = [load(p, f"{p.stem}_req_mapping_helpers") for p in (OPENAPI, MOBILE, NFR, AI)]
        for name in ("req_list", "load_req_map"):
            sources = {inspect.getsource(getattr(m, name)) for m in mods}
            self.assertEqual(len(sources), 1, name)
        self.assertEqual(len({(m.REQ_MAP_KEYS == mods[0].REQ_MAP_KEYS, m.REQ_TOKEN.pattern) for m in mods}), 1)
        self.assertEqual(mods[0].req_list(["REQ-1", "REQ-2, REQ-1"], "x"), ["REQ-1", "REQ-2"])
        for bad in ("", "REQ 1", 7, ["REQ-1", None], "REQ-1|x"):
            with self.assertRaises(ValueError):
                mods[0].req_list(bad, "x")


if __name__ == "__main__":
    unittest.main()
