"""Guards the always-on skill-listing budget (see docs/DESCRIPTIONS.md).

Claude Code gives the skill listing 1% of the context window and drops the descriptions of the
least-used skills when it overflows, so the suite keeps its descriptions short and non-overlapping.
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOTAL_MAX = 7500
EACH_MAX = 480


def descriptions() -> dict[str, str]:
    out = {}
    for p in sorted((ROOT / "skills").glob("*/SKILL.md")):
        m = re.search(r"^description:\s*(.+)$", p.read_text(encoding="utf-8"), re.M)
        out[p.parent.name] = m.group(1).strip()
    return out


class DescriptionBudgetTests(unittest.TestCase):
    def test_total_and_each_within_budget(self):
        d = descriptions()
        total = sum(len(v) for v in d.values())
        self.assertLessEqual(total, TOTAL_MAX, f"descriptions total {total} chars > {TOTAL_MAX}")
        for name, text in d.items():
            self.assertLessEqual(len(text), EACH_MAX, f"{name}: {len(text)} chars > {EACH_MAX}")

    def test_exclusive_trigger_terms(self):
        d = descriptions()
        owners = {r"\bIDOR\b|\bBOLA\b": {"testing-apis"}, r"\bWCAG\b": {"testing-nonfunctional"},
                  r"regression selection": {"tracing-requirements"}}
        for pattern, allowed in owners.items():
            users = {n for n, t in d.items() if re.search(pattern, t, re.I)}
            self.assertTrue(users <= allowed, f"'{pattern}' also appears in {sorted(users - allowed)}")


if __name__ == "__main__":
    unittest.main()
