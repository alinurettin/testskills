"""Launch hygiene: answer-key isolation, working links, the quickstart example and the privacy claim.

These tests guard statements made in README.md / README.en.md, evals/README.md and
examples/quickstart: if the data or the scripts drift, the docs would silently lie.
Standard library only.
"""
import ast
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
QS = ROOT / "examples" / "quickstart"
SKILLS = ROOT / "skills"

# Markdown files whose relative links must resolve (files owned by the launch-hygiene change
# plus the documents whose answer-key links it rewrote).
LINKED_DOCS = [
    "README.md", "README.en.md", "CONTRIBUTING.md",
    "evals/README.md", "evals/keys/fast.md", "evals/keys/api.md", "evals/keys/migration.md",
    "docs/MANUEL-TEST-REHBERI.md", "docs/EVALUATION.md", "docs/EVALUATION.en.md",
    "examples/quickstart/README.md", "examples/quickstart/README.en.md",
    "examples/fast-transfer/README.md", "examples/api-trial/README.md", "examples/migration-trial/README.md",
    ".github/pull_request_template.md",
]

NETWORK_MODULES = {"urllib", "urllib2", "urllib3", "http", "socket", "requests", "httpx", "aiohttp",
                   "ftplib", "smtplib", "poplib", "imaplib", "telnetlib", "xmlrpc", "webbrowser", "ssl"}

EXPERIMENTAL = ["running-exploratory-tests", "testing-ai-features", "testing-mobile-apps", "preparing-test-data"]


def run_py(script: Path, *args, cwd: Path = ROOT) -> subprocess.CompletedProcess:
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    return subprocess.run([sys.executable, str(script), *map(str, args)], cwd=cwd, env=env,
                          capture_output=True, text=True, encoding="utf-8")


def strip_code(md: str) -> str:
    md = re.sub(r"```.*?```", "", md, flags=re.S)
    return re.sub(r"`[^`\n]*`", "", md)


def github_slug(heading: str) -> str:
    s = heading.strip().lower().replace("`", "")
    s = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", s)
    s = re.sub(r"[^\w\- ]", "", s)
    return s.replace(" ", "-")


def anchors_of(md_path: Path) -> set:
    text = re.sub(r"```.*?```", "", md_path.read_text(encoding="utf-8"), flags=re.S)
    return {github_slug(m.group(1)) for m in re.finditer(r"^#{1,6}\s+(.+?)\s*#*\s*$", text, re.M)}


class AnswerKeyIsolation(unittest.TestCase):
    def test_keys_live_outside_trial_folders(self):
        for name in ("fast", "api", "migration"):
            self.assertTrue((ROOT / "evals" / "keys" / f"{name}.md").is_file(), name)
        leaked = [p.relative_to(ROOT).as_posix() for p in (ROOT / "evals").glob("trial-*/**/*")
                  if p.is_file() and re.search(r"answer[-_ ]?key", p.name, re.I)]
        self.assertEqual(leaked, [], "answer keys must not sit inside a trial folder")

    def test_no_stale_answer_key_paths(self):
        stale = []
        for p in list(ROOT.glob("*.md")) + list((ROOT / "docs").glob("*.md")) + list((ROOT / "examples").glob("*/README*.md")) \
                + list((ROOT / "evals").glob("**/*.md")):
            if "workspace" in p.parts:
                continue
            if re.search(r"trial-(fast|api|migration)/ANSWER-KEY", p.read_text(encoding="utf-8")):
                stale.append(p.relative_to(ROOT).as_posix())
        self.assertEqual(stale, [])

    def test_evals_readme_names_every_key_of_the_old_trials(self):
        text = (ROOT / "evals" / "README.md").read_text(encoding="utf-8")
        for name in ("keys/fast.md", "keys/api.md", "keys/migration.md", "RUN.md", "outside the repository"):
            self.assertIn(name, text)


class RelativeLinks(unittest.TestCase):
    def test_relative_links_and_anchors_resolve(self):
        broken = []
        for rel in LINKED_DOCS:
            path = ROOT / rel
            self.assertTrue(path.is_file(), rel)
            for target in re.findall(r"\]\(([^)\s]+)\)", strip_code(path.read_text(encoding="utf-8"))):
                if re.match(r"^[a-z]+:", target):
                    continue
                file_part, _, anchor = target.partition("#")
                dest = (path.parent / file_part).resolve() if file_part else path
                if not dest.exists():
                    broken.append(f"{rel} -> {target}")
                    continue
                if anchor and dest.suffix == ".md" and anchor not in anchors_of(dest):
                    broken.append(f"{rel} -> {target} (anchor)")
        self.assertEqual(broken, [])


class QuickstartExample(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reqs = json.loads((QS / "qa" / "requirements.json").read_text(encoding="utf-8"))["requirements"]
        cls.tests = json.loads((QS / "qa" / "test-cases.json").read_text(encoding="utf-8"))["test_cases"]

    def test_json_is_generated_from_the_compact_sources(self):
        compact = SKILLS / "designing-test-cases" / "scripts" / "qa_compact.py"
        with tempfile.TemporaryDirectory() as tmp:
            for kind, src, out in (("req", "requirements.src.md", "requirements.json"),
                                   ("tc", "test-cases.src.md", "test-cases.json")):
                r = run_py(compact, kind, QS / "qa" / src, "--out", Path(tmp) / out)
                self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
                self.assertEqual(json.loads((Path(tmp) / out).read_text(encoding="utf-8")),
                                 json.loads((QS / "qa" / out).read_text(encoding="utf-8")), out)

    def test_budget_and_priority_calibration(self):
        self.assertTrue(8 <= len(self.reqs) <= 15)
        self.assertLessEqual(sum(1 for r in self.reqs if r.get("derived")), 6)
        self.assertTrue(15 <= len(self.tests) <= 25, len(self.tests))
        prio = [t["priority"] for t in self.tests]
        self.assertLessEqual(prio.count("critical") / len(prio), 0.20)
        self.assertLessEqual((prio.count("critical") + prio.count("high")) / len(prio), 0.60)

    def test_rtm_has_no_validation_errors_and_matches_the_readme(self):
        rtm = SKILLS / "tracing-requirements" / "scripts" / "build_rtm.py"
        with tempfile.TemporaryDirectory() as tmp:
            r = run_py(rtm, "--requirements", QS / "qa" / "requirements.json", "--tests", QS / "qa" / "test-cases.json",
                       "--out-dir", tmp, "--json")
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            rep = json.loads((Path(tmp) / "rtm.json").read_text(encoding="utf-8"))
        self.assertEqual(rep["errors"], [])
        self.assertEqual(rep["duplicates"], [])
        m = rep["metrics"]
        self.assertEqual((m["requirements_covered"], m["requirements_in_scope"]), (13, 14))
        self.assertEqual(m["functional_with_negative"], m["functional_total"])
        # The one uncovered requirement is the documented exception (no measurable target, Q-006).
        self.assertEqual([g["id"] for g in rep["gaps"] if g["code"] == "UNCOVERED"], ["REQ-012"])
        for text in ((QS / "README.md").read_text(encoding="utf-8"), (QS / "README.en.md").read_text(encoding="utf-8")):
            self.assertIn("13/14", text)
            self.assertIn("REQ-012", text)

    def test_readme_numbers_match_the_data(self):
        pos = sum(1 for t in self.tests if t["polarity"] == "positive")
        prio = [t["priority"] for t in self.tests]
        questions = re.findall(r"^\| (Q-\d{3}) \|", (QS / "qa" / "clarifications.md").read_text(encoding="utf-8"), re.M)
        tr = (QS / "README.md").read_text(encoding="utf-8")
        en = (QS / "README.en.md").read_text(encoding="utf-8")
        self.assertIn(f"{len(self.reqs)} gereksinim", tr)
        self.assertIn(f"{len(set(questions))} soru", tr)
        self.assertIn(f"{len(self.tests)} test: {pos} pozitif, {len(self.tests) - pos} negatif", tr)
        self.assertIn(f"{prio.count('critical')} kritik, {prio.count('high')} yüksek, "
                      f"{prio.count('medium')} orta, {prio.count('low')} düşük", tr)
        self.assertIn(f"{len(self.reqs)} requirements", en)
        self.assertIn(f"{len(set(questions))} questions", en)
        self.assertIn(f"{len(self.tests)} tests: {pos} positive, {len(self.tests) - pos} negative", en)

    def test_design_refs_point_to_existing_conditions(self):
        missing = []
        for t in self.tests:
            ref = t.get("design_ref") or ""
            m = re.match(r"(DS-\d{3})\s+([A-Z]+-?\d+)", ref)
            if not ref:
                continue
            self.assertIsNotNone(m, f"{t['id']}: {ref}")
            outputs = list((QS / "qa" / "design").glob(f"{m.group(1)}-*.md"))
            self.assertEqual(len(outputs), 1, ref)
            if m.group(2) not in outputs[0].read_text(encoding="utf-8"):
                missing.append(f"{t['id']}: {ref}")
        self.assertEqual(missing, [])

    def test_xlsx_export_holds_every_test(self):
        with zipfile.ZipFile(QS / "qa" / "exports" / "test-cases.xlsx") as z:
            sheet = z.read("xl/worksheets/sheet1.xml").decode("utf-8")
        self.assertEqual(set(re.findall(r"TC-\d{3}", sheet)), {t["id"] for t in self.tests})


class PrivacyClaim(unittest.TestCase):
    def test_skill_scripts_import_no_network_modules(self):
        offenders = []
        for py in SKILLS.glob("*/scripts/*.py"):
            tree = ast.parse(py.read_text(encoding="utf-8"), filename=str(py))
            for node in ast.walk(tree):
                names = []
                if isinstance(node, ast.Import):
                    names = [a.name for a in node.names]
                elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                    names = [node.module]
                for n in names:
                    if n.split(".")[0] in NETWORK_MODULES:
                        offenders.append(f"{py.relative_to(ROOT).as_posix()}: {n}")
        self.assertEqual(offenders, [], "README 'Privacy' section says the scripts make no network calls")


class ExperimentalStatus(unittest.TestCase):
    def test_status_line_in_body_and_readme_tables(self):
        readme_tr = (ROOT / "README.md").read_text(encoding="utf-8")
        readme_en = (ROOT / "README.en.md").read_text(encoding="utf-8")
        for skill in EXPERIMENTAL:
            text = (SKILLS / skill / "SKILL.md").read_text(encoding="utf-8")
            body = text.split("\n---\n", 1)[1]
            self.assertIn("Status: experimental (no blind trial yet)", body, skill)
            self.assertIn(f"`{skill}` **(deneysel)**", readme_tr)
            self.assertIn(f"`{skill}` **(experimental)**", readme_en)


class GitHubTemplates(unittest.TestCase):
    def test_issue_forms_and_pr_template_exist(self):
        base = ROOT / ".github" / "ISSUE_TEMPLATE"
        for name in ("bug.yml", "import-failed.yml", "trial-report.yml", "domain-request.yml"):
            text = (base / name).read_text(encoding="utf-8")
            for key in ("name:", "description:", "body:"):
                self.assertRegex(text, rf"(?m)^{key}", f"{name}: {key}")
            self.assertNotIn("\t", text, f"{name}: tabs are not valid YAML indentation")
            self.assertRegex(text, r"(?m)^\s+- type: (input|textarea|dropdown)", name)
        self.assertIn("blank_issues_enabled", (base / "config.yml").read_text(encoding="utf-8"))
        self.assertTrue((ROOT / ".github" / "pull_request_template.md").is_file())

    def test_import_form_asks_for_the_fields_an_importer_bug_needs(self):
        text = (ROOT / ".github" / "ISSUE_TEMPLATE" / "import-failed.yml").read_text(encoding="utf-8")
        for field_id in ("tool", "tool-version", "file", "error", "screenshot"):
            self.assertRegex(text, rf"(?m)^\s+id: {re.escape(field_id)}$", field_id)


if __name__ == "__main__":
    unittest.main()
