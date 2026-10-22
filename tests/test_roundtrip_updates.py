"""Lossless workbook edits and reviewable, concurrency-checked local updates."""
import copy
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ex = load("roundtrip_export", ROOT / "skills/exporting-test-cases/scripts/export_tests.py")
im = load("roundtrip_import", ROOT / "skills/reviewing-test-cases/scripts/import_tests.py")


def sample():
    return {"project": "Synthetic", "language": "tr", "version": 7,
            "custom_root": {"retain": [True, 3]}, "test_cases": [
        {"id": "TC-001", "external_id": "SHOP-201", "title": "İşlem\nbaşlığı",
         "requirement_ids": ["REQ-001"], "priority": "high", "polarity": "negative",
         "technique": "boundary-value-analysis", "design_ref": "DS-001 C-02",
         "preconditions": ["A\nB", "C"], "test_data": {"nested": {"value": 3}},
         "steps": [{"action": "A => B [x]\nC", "data": 123, "expected": "=literal\nİyi", "custom_step": 2},
                   {"action": "Next", "expected": "Done"}], "postconditions": ["Clean"],
         "automation": {"candidate": True, "reason": "stable", "custom": 1},
         "category": "security", "status": "ready", "tags": ["a,b", "smoke"],
         "custom": {"reviewer": "tester@example.com"}},
        {"id": "TC-002", "title": "Other", "steps": [{"action": "Go", "expected": "OK"}],
         "status": "ready", "external_ids": {"qase": "DEMO-2"}}]}


def edit_cell(path, ref, text):
    with zipfile.ZipFile(path) as z:
        entries = {name: z.read(name) for name in z.namelist()}
    key = "xl/worksheets/sheet1.xml"
    root = ET.fromstring(entries[key])
    ns = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
    cell = next(c for c in root.iter(ns + "c") if c.get("r") == ref)
    cell.clear()
    cell.set("r", ref)
    cell.set("t", "inlineStr")
    ET.SubElement(ET.SubElement(cell, ns + "is"), ns + "t").text = text
    entries[key] = ET.tostring(root, encoding="utf-8")
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for name, data in entries.items():
            z.writestr(name, data)


def edit_rows(path, transform):
    sheets = im.read_xlsx(path)
    rows = [[name for name in r] for _, r in sheets[0]["rows"]]
    transform(rows)
    ex.write_xlsx(path, [(s["name"], rows if i == 0 else [r for _, r in s["rows"]], [20] * 16)
                         for i, s in enumerate(sheets)])


class RoundtripTests(unittest.TestCase):
    def workbook(self, folder, doc=None):
        doc = doc or sample()
        path = Path(folder) / "tests.xlsx"
        ex.export_xlsx(doc["test_cases"], {}, ex.H["tr"], path, doc["project"], document=doc)
        return path

    def test_unchanged_is_semantically_lossless(self):
        with tempfile.TemporaryDirectory() as d:
            path = self.workbook(d)
            self.assertEqual(im.import_roundtrip(path)["document"], sample())
            self.assertTrue(next(s for s in im.read_xlsx(path) if s["name"] == "_qa_suite")["hidden"])

    def test_edit_preserves_ids_unknown_fields_and_step_metadata(self):
        with tempfile.TemporaryDirectory() as d:
            path = self.workbook(d)
            edit_cell(path, "M2", "Düzeltilmiş\nsonuç")
            expected = sample()
            expected["test_cases"][0]["steps"][0]["expected"] = "Düzeltilmiş\nsonuç"
            self.assertEqual(im.import_roundtrip(path)["document"], expected)

    def test_future_schema_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            doc = sample()
            doc["schema_version"] = 99
            with self.assertRaisesRegex(ValueError, "schema_version"):
                self.workbook(d, doc)

    def test_changed_invalid_enum_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            path = self.workbook(d)
            edit_cell(path, "E2", "urgent-ish")
            with self.assertRaisesRegex(ValueError, "priority"):
                im.import_roundtrip(path)

    def test_large_unicode_metadata_chunks_are_lossless(self):
        with tempfile.TemporaryDirectory() as d:
            doc = sample()
            doc["large_extension"] = "İ 😀 " * 10000
            self.assertEqual(im.import_roundtrip(self.workbook(d, doc))["document"], doc)

    def test_removed_rows_deprecate_and_new_rows_keep_given_id(self):
        with tempfile.TemporaryDirectory() as d:
            path = self.workbook(d)
            def change(rows):
                rows.pop(3)  # remove TC-002 completely
                added = rows[1][:]
                added[0], added[1], added[9] = "TC-003", "New", 1
                added[8] = "{}"  # edits/new structured test data use JSON
                rows.append(added)
            edit_rows(path, change)
            result = im.import_roundtrip(path)
            self.assertEqual(result["removed_ids"], ["TC-002"])
            got = {t["id"]: t for t in result["document"]["test_cases"]}
            self.assertEqual(got["TC-002"]["status"], "deprecated")
            self.assertEqual(got["TC-003"]["title"], "New")
            self.assertEqual(got["TC-001"], sample()["test_cases"][0])

    def test_duplicate_step_number_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            path = self.workbook(d)
            edit_cell(path, "J3", "1")
            with self.assertRaisesRegex(ValueError, "duplicate step"):
                im.import_roundtrip(path)

    def test_edited_technique_alias_becomes_canonical_enum(self):
        with tempfile.TemporaryDirectory() as d:
            path = self.workbook(d)
            edit_cell(path, "G2", "sc")
            self.assertEqual(im.import_roundtrip(path)["document"]["test_cases"][0]["technique"], "scenario")


class UpdateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.up = load("roundtrip_updates", ROOT / "skills/reviewing-test-cases/scripts/update_tests.py")

    def write(self, folder, name, doc):
        path = Path(folder) / name
        path.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
        return path

    def test_plan_apply_and_rerun_are_idempotent(self):
        with tempfile.TemporaryDirectory() as d:
            source = self.write(d, "source.json", sample())
            desired = sample()
            desired["test_cases"][0]["title"] = "Changed"
            desired["test_cases"] = desired["test_cases"][:1]
            desired["test_cases"].append({"id": "TC-003", "title": "New", "steps": [{"action": "Go", "expected": "OK"}]})
            incoming = self.write(d, "incoming.json", desired)
            before = source.read_bytes()
            plan = self.up.plan_updates(source, incoming)
            self.assertEqual(source.read_bytes(), before)
            self.assertEqual({a["operation"] for a in plan["actions"]}, {"add", "update", "deprecate"})
            self.assertEqual(plan, self.up.plan_updates(source, incoming))
            self.up.apply_plan(source, plan)
            self.assertEqual(self.up.plan_updates(source, incoming)["actions"], [])
            self.assertEqual(json.loads(source.read_text(encoding="utf-8"))["test_cases"][1]["status"], "deprecated")
            import hashlib
            marker = json.loads(source.with_name(source.name + ".qa-reviewed.json").read_text(encoding="utf-8"))
            self.assertEqual(marker["schema_version"], 1)
            self.assertEqual(marker["source_sha256"], hashlib.sha256(source.read_bytes()).hexdigest())

    def test_stale_source_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as d:
            source = self.write(d, "source.json", sample())
            desired = sample()
            desired["test_cases"][0]["title"] = "Incoming"
            incoming = self.write(d, "incoming.json", desired)
            plan = self.up.plan_updates(source, incoming)
            source.write_text(source.read_text(encoding="utf-8") + "\n", encoding="utf-8")
            before = source.read_bytes()
            with self.assertRaisesRegex(ValueError, "changed|stale"):
                self.up.apply_plan(source, plan)
            self.assertEqual(source.read_bytes(), before)

    def test_workbook_conflict_and_unrelated_source_edit(self):
        with tempfile.TemporaryDirectory() as d:
            doc = sample()
            workbook = Path(d) / "tests.xlsx"
            ex.export_xlsx(doc["test_cases"], {}, ex.H["tr"], workbook, doc["project"], document=doc)
            edit_cell(workbook, "B2", "Excel edit")
            changed = sample()
            changed["test_cases"][0]["title"] = "Other edit"
            source = self.write(d, "source.json", changed)
            plan = self.up.plan_updates(source, workbook)
            self.assertEqual([c["id"] for c in plan["conflicts"]], ["TC-001"])
            with self.assertRaisesRegex(ValueError, "conflict"):
                self.up.apply_plan(source, plan)
            changed = sample()
            changed["test_cases"][1]["title"] = "Unrelated source edit"
            source = self.write(d, "source.json", changed)
            plan = self.up.plan_updates(source, workbook)
            self.assertEqual(plan["conflicts"], [])
            self.up.apply_plan(source, plan)
            result = json.loads(source.read_text(encoding="utf-8"))
            self.assertEqual(result["test_cases"][0]["title"], "Excel edit")
            self.assertEqual(result["test_cases"][1]["title"], "Unrelated source edit")

    def test_apply_failure_keeps_source_and_releases_lock(self):
        with tempfile.TemporaryDirectory() as d:
            source = self.write(d, "source.json", sample())
            incoming = self.write(d, "incoming.json", sample())
            plan = self.up.plan_updates(source, incoming)
            plan["target_document"]["test_cases"][0]["title"] = "Bad tamper"
            before = source.read_bytes()
            with self.assertRaisesRegex(ValueError, "integrity"):
                self.up.apply_plan(source, plan)
            self.assertEqual(source.read_bytes(), before)

    def test_atomic_replace_failure_preserves_source_and_cleans_staging(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as d:
            source = self.write(d, "source.json", sample())
            changed = sample()
            changed["test_cases"][0]["title"] = "New title"
            incoming = self.write(d, "incoming.json", changed)
            plan = self.up.plan_updates(source, incoming)
            before = source.read_bytes()
            with patch.object(self.up.os, "replace", side_effect=OSError("synthetic failure")):
                with self.assertRaisesRegex(OSError, "synthetic failure"):
                    self.up.apply_plan(source, plan)
            self.assertEqual(source.read_bytes(), before)
            self.assertEqual(sorted(p.name for p in Path(d).iterdir()), ["incoming.json", "source.json"])

    def test_existing_lock_is_not_removed(self):
        with tempfile.TemporaryDirectory() as d:
            source = self.write(d, "source.json", sample())
            incoming = self.write(d, "incoming.json", sample())
            plan = self.up.plan_updates(source, incoming)
            lock = Path(d) / ".source.json.qa-update.lock"
            lock.write_text("other writer", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "locked"):
                self.up.apply_plan(source, plan)
            self.assertEqual(lock.read_text(encoding="utf-8"), "other writer")

    def test_source_replace_failure_restores_previous_review_guard(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as d:
            source = self.write(d, "source.json", sample())
            changed = sample()
            changed["test_cases"][0]["title"] = "New title"
            incoming = self.write(d, "incoming.json", changed)
            plan = self.up.plan_updates(source, incoming)
            marker = source.with_name(source.name + ".qa-reviewed.json")
            marker.write_text('{"schema_version":1,"explanation":"previous"}', encoding="utf-8")
            before, old_guard = source.read_bytes(), marker.read_bytes()
            real_replace = self.up.os.replace
            def fail_source(src, dst):
                if Path(dst) == source:
                    raise OSError("synthetic source replacement failure")
                return real_replace(src, dst)
            with patch.object(self.up.os, "replace", side_effect=fail_source):
                with self.assertRaisesRegex(OSError, "synthetic source"):
                    self.up.apply_plan(source, plan)
            self.assertEqual(source.read_bytes(), before)
            self.assertEqual(marker.read_bytes(), old_guard)
            self.assertEqual(sorted(p.name for p in Path(d).iterdir()),
                             ["incoming.json", "source.json", "source.json.qa-reviewed.json"])

    def test_partial_export_does_not_disclose_or_retire_unselected_test(self):
        with tempfile.TemporaryDirectory() as d:
            doc = sample()
            workbook = Path(d) / "selected.xlsx"
            ex.export_xlsx(doc["test_cases"][:1], {}, ex.H["tr"], workbook, doc["project"], document=doc)
            recovered = im.import_roundtrip(workbook)["document"]
            self.assertEqual([t["id"] for t in recovered["test_cases"]], ["TC-001"])
            edit_cell(workbook, "B2", "Selected edit")
            source = self.write(d, "source.json", doc)
            plan = self.up.plan_updates(source, workbook)
            self.assertEqual([a["id"] for a in plan["actions"]], ["TC-001"])
            self.up.apply_plan(source, plan)
            self.assertEqual(json.loads(source.read_text(encoding="utf-8"))["test_cases"][1], doc["test_cases"][1])

    def test_workbook_for_another_project_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            doc = sample()
            workbook = Path(d) / "edited.xlsx"
            ex.export_xlsx(doc["test_cases"], {}, ex.H["tr"], workbook, doc["project"], document=doc)
            edit_cell(workbook, "B2", "Excel edit")
            doc["project"] = "Other project"
            source = self.write(d, "source.json", doc)
            with self.assertRaisesRegex(ValueError, "different project"):
                self.up.plan_updates(source, workbook)

    def test_imported_json_keeps_baseline_conflict_provenance(self):
        with tempfile.TemporaryDirectory() as d:
            doc = sample()
            workbook = Path(d) / "edited.xlsx"
            ex.export_xlsx(doc["test_cases"], {}, ex.H["tr"], workbook, doc["project"], document=doc)
            edit_cell(workbook, "B2", "Excel edit")
            candidate = Path(d) / "candidate.json"
            result = subprocess.run([sys.executable, str(ROOT / "skills/reviewing-test-cases/scripts/import_tests.py"),
                                     str(workbook), "--format", "json", "--out", str(candidate)],
                                    capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(result.returncode, 0, result.stderr)
            changed = sample()
            changed["test_cases"][0]["title"] = "Concurrent edit"
            source = self.write(d, "source.json", changed)
            self.assertEqual(len(self.up.plan_updates(source, candidate)["conflicts"]), 1)
            candidate.write_text(candidate.read_text(encoding="utf-8") + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "candidate changed"):
                self.up.plan_updates(source, candidate)

    def test_explicit_migration_preserves_legacy_content(self):
        original = sample()
        migrated = self.up.migrate_document(original)
        self.assertNotIn("schema_version", original)
        self.assertEqual(migrated.pop("schema_version"), 1)
        self.assertEqual(migrated, original)
        future = sample()
        future["schema_version"] = 2
        with self.assertRaisesRegex(ValueError, "schema_version"):
            self.up.migrate_document(future)


if __name__ == "__main__":
    unittest.main()
