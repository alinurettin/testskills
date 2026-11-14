"""Evaluation provenance and statistics must not require paid model calls."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("eval_harness", ROOT / "tools/eval_harness.py")
harness = importlib.util.module_from_spec(spec)
spec.loader.exec_module(harness)


class EvaluationHarnessTests(unittest.TestCase):
    def test_original_results_are_read_only_and_averages_reproduce(self):
        path = ROOT / "evals/results/trials-0.9.0.json"
        before = path.read_bytes()
        result = harness.summarize([json.loads(before)])
        rows = result["groups"]
        for model, expected in [("haiku", 89.253), ("sonnet", 94.925), ("opus", 95.196)]:
            means = [r["mean"] for r in rows if r["model"] == model and r["arm"] == "skill"]
            self.assertAlmostEqual(sum(means) / len(means), expected, places=2)
        self.assertEqual(sum(r["ceiling_count"] for r in rows), 50)
        self.assertEqual(path.read_bytes(), before)

    def test_prepare_and_record_detect_changed_inputs_and_missing_cost(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            repo = base / "repo"
            repo.mkdir()
            (repo / "input.txt").write_text("synthetic input", encoding="utf-8")
            config = {"run_id": "R-1", "trial": "example", "model": "example-model-v1", "arm": "baseline",
                      "inputs": [{"source": "input.txt", "path": "inputs/input.txt"}]}
            manifest = harness.prepare(config, base / "workspace", repo)
            self.assertFalse(manifest.is_relative_to(base / "workspace"))
            (base / "workspace/inputs/input.txt").write_text("changed", encoding="utf-8")
            record = harness.record(manifest, {"score": 2, "max": 3}, base / "result.json")
            self.assertIsNone(record["cost"])
            self.assertTrue(record["contaminated"])
            self.assertTrue(record["contamination_reasons"])
            self.assertEqual(harness.summarize([record])["excluded_contaminated"], ["R-1"])

    def test_cannot_copy_keys_or_escape_workspace_or_reuse_directory(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            repo = base / "repo"
            (repo / "evals/keys").mkdir(parents=True)
            (repo / "evals/keys/answer.md").write_text("secret answers", encoding="utf-8")
            config = {"run_id": "r", "model": "m", "trial": "t", "arm": "baseline",
                      "inputs": [{"source": "evals/keys/answer.md", "path": "input.md"}]}
            with self.assertRaises(ValueError):
                harness.prepare(config, base / "out", repo)
            config["inputs"] = [{"source": "input.txt", "path": "../leak.txt"}]
            with self.assertRaises(ValueError):
                harness.prepare(config, base / "out", repo)
            for path in (repo / "run", base):
                with self.assertRaises(ValueError):
                    harness.prepare(config, path, repo)

    def test_statistics_show_variation_and_exclude_contamination(self):
        runs = [{"id": str(i), "trial": "t", "model": "m", "arm": "baseline", "score": s, "max": 100}
                for i, s in enumerate([50, 75, 100])]
        result = harness.summarize([{"runs": runs}])
        row = result["groups"][0]
        self.assertEqual((row["mean"], row["median"], row["stdev"], row["ceiling_count"]), (75, 75, 25, 1))
        self.assertEqual(row["missing_metadata"]["tokens"], 3)
        with self.assertRaises(ValueError):
            harness.summarize([{"runs": [runs[0], runs[0]]}])

    def test_intervals_resample_tasks_and_keep_four_arms(self):
        runs = []
        for task in range(5):
            for arm, score in [("baseline", 70), ("checklist", 75), ("scripts", 80), ("full", 90)]:
                runs.append({"id": f"{task}-{arm}", "trial": str(task), "model": "m",
                             "arm": arm, "score": score, "max": 100})
        result = harness.summarize([{"runs": runs}])
        self.assertEqual(len(result["comparisons"]), 3)
        full = next(c for c in result["comparisons"] if c["arm"] == "full")
        self.assertEqual(full["bootstrap_95_task_interval"], [20, 20])
        self.assertEqual(full["independent_tasks"], 5)

    def test_bad_scores_and_future_versions_are_rejected(self):
        for score in (-1, float("nan"), True, 101):
            with self.subTest(score=score), self.assertRaises(ValueError):
                harness.summarize([{"id": "x", "model": "m", "arm": "baseline", "trial": "t", "score": score, "max": 100}])
        with self.assertRaises(ValueError):
            harness.versioned({"schema_version": 99})

    def test_relative_paths_reject_empty_dot_and_nonstring_values(self):
        for value in ("", ".", "inputs/../answer", "NUL.txt", "a/file.", [], None):
            with self.subTest(value=value), self.assertRaises(ValueError):
                harness.checked_relative(value)

    def test_prepare_rejects_case_variant_keys_and_target_prefix_collisions(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            repo = base / "repo"
            (repo / "evals/KEYS").mkdir(parents=True)
            (repo / "evals/KEYS/answer.md").write_text("answer", encoding="utf-8")
            (repo / "input.txt").write_text("input", encoding="utf-8")
            config = {"run_id": "r", "model": "m", "trial": "t", "arm": "baseline",
                      "inputs": [{"source": "evals/KEYS/answer.md", "path": "input.md"}]}
            with self.assertRaises(ValueError):
                harness.prepare(config, base / "out", repo)
            self.assertFalse((base / "out").exists())
            config["inputs"] = [{"source": "input.txt", "path": "a"},
                                {"source": "input.txt", "path": "a/b"}]
            with self.assertRaises(ValueError):
                harness.prepare(config, base / "out2", repo)
            self.assertFalse((base / "out2").exists())

    def test_grader_and_repository_revision_define_separate_cohorts(self):
        runs = []
        for grader, commit, score in (("grader-a", "revision-a", 10), ("grader-b", "revision-a", 90),
                                      ("grader-a", "revision-b", 50)):
            runs.append({"id": f"{grader}-{commit}", "trial": "t", "model": "m", "arm": "full",
                         "grader": grader, "repository_commit": commit, "score": score, "max": 100})
        result = harness.summarize([{"runs": runs}])
        self.assertEqual(len(result["groups"]), 3)
        self.assertEqual(result["comparisons"], [])

    def test_contamination_and_observation_types_cannot_be_truthy_strings(self):
        base = {"id": "x", "trial": "t", "model": "m", "arm": "baseline", "score": 50, "max": 100}
        for bad in ({"contaminated": "false"}, {"contamination_reasons": "not a list"},
                    {"tokens": -2}, {"tool_calls": 2.5}, {"false_positives": -1},
                    {"missed": "K1"}, {"found": 3, "total": 2}):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                harness.summarize([{**base, **bad}])

    def test_skill_links_are_rejected_before_copying_anything(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            repo = base / "repo"
            (repo / "skills/demo/assets").mkdir(parents=True)
            (repo / "skills/demo/SKILL.md").write_text("demo", encoding="utf-8")
            (repo / "input.txt").write_text("input", encoding="utf-8")
            (base / "secret.txt").write_text("answer", encoding="utf-8")
            try:
                (repo / "skills/demo/assets/link.txt").symlink_to(base / "secret.txt")
            except OSError:
                self.skipTest("this runner does not permit symlink creation")
            config = {"run_id": "r", "model": "m", "trial": "t", "arm": "full", "skills": ["demo"],
                      "inputs": [{"source": "input.txt", "path": "input.txt"}]}
            with self.assertRaisesRegex(ValueError, "linked/escaping"):
                harness.prepare(config, base / "out", repo)
            self.assertFalse((base / "out").exists())

    def test_record_validates_metadata_and_keeps_evaluator_files_outside_workspace(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            repo = base / "repo"
            repo.mkdir()
            (repo / "input.txt").write_text("input", encoding="utf-8")
            config = {"run_id": "r", "model": "m", "trial": "t", "arm": "baseline",
                      "inputs": [{"source": "input.txt", "path": "input.txt"}]}
            manifest = harness.prepare(config, base / "out", repo)
            for bad in ({"contaminated": "false"}, {"contamination_reasons": "text"}, {"artifacts": "input.txt"}):
                with self.subTest(bad=bad), self.assertRaises(ValueError):
                    harness.record(manifest, {"score": 1, "max": 2, **bad}, base / "result.json")
            with self.assertRaisesRegex(ValueError, "outside"):
                harness.record(manifest, {"score": 1, "max": 2}, base / "out/result.json")
            (base / "out/report.md").write_text("evidence", encoding="utf-8")
            result = harness.record(manifest, {"score": 1, "max": 2, "artifacts": ["report.md"],
                                               "grader": {"model": "grader-v1", "rubric_sha256": "abc"}},
                                    base / "result.json")
            self.assertEqual(harness.summarize([result])["groups"][0]["n"], 1)


if __name__ == "__main__":
    unittest.main()
