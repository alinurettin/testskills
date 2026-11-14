"""tools/eval_stats.py: the published intervals in docs/EVALUATION.md must stay reproducible."""
from __future__ import annotations

import importlib.util
import random
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("eval_stats", ROOT / "tools" / "eval_stats.py")
es = importlib.util.module_from_spec(spec)
spec.loader.exec_module(es)


class EvalStatsTests(unittest.TestCase):
    def test_published_numbers(self):
        data = es.load(str(ROOT / "evals" / "results" / "trials-0.9.0.json"))
        pooled = {f"{m}/{t}": c for m in data for t, c in data[m].items()}
        self.assertEqual(sum(len(c["skill"]) + len(c["noskill"]) for c in pooled.values()), 126)
        self.assertAlmostEqual(es.diff(pooled), 2.7, delta=0.1)
        lo, hi = es.bootstrap(pooled, random.Random(1), 4000)
        self.assertGreater(lo, 0)          # pooled effect is detectable
        hlo, hhi = es.bootstrap(dict(data["haiku"]), random.Random(1), 4000)
        self.assertLess(hlo, 0)            # per-model effect on Haiku is not: keep the README honest
        self.assertGreater(hhi, 0)

    def test_no_effect_gives_interval_around_zero(self):
        cells = {"t": {"skill": [80.0, 90.0, 85.0], "noskill": [85.0, 80.0, 90.0]}}
        lo, hi = es.bootstrap(cells, random.Random(3), 2000)
        self.assertLessEqual(lo, 0)
        self.assertGreaterEqual(hi, 0)
        self.assertGreater(es.permutation_p(cells, random.Random(3), 2000), 0.5)


if __name__ == "__main__":
    unittest.main()
