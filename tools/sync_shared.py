#!/usr/bin/env python3
"""Copy shared/ files into every skill that needs them.

Skills must be self-contained (they are installed and loaded individually), so
shared/data-model.md is duplicated into each skill's references/ and
shared/scripts/qa_compact.py into the scripts/ of the skills that author
artifacts. Edit only the files in shared/, then run:

    python tools/sync_shared.py          # copy
    python tools/sync_shared.py --check  # exit 1 if any copy is out of date (CI)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# shared file -> (target folder inside each skill, skills that receive it)
SHARED = {
    "data-model.md": ("references", ["qa-orchestrator", "analyzing-requirements", "designing-test-cases",
                                     "tracing-requirements", "exporting-test-cases", "reporting-test-results"]),
    "scripts/qa_compact.py": ("scripts", ["analyzing-requirements", "designing-test-cases", "reviewing-test-cases",
                                          "testing-nonfunctional"]),
}
# shared folder -> (target folder inside each skill, skills that receive every file of it)
SHARED_DIRS = {
    "domains": ("references/domains", ["analyzing-requirements", "designing-test-cases"]),
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    stale = []
    items = dict(SHARED)
    for d, (folder, skills) in SHARED_DIRS.items():
        for f in sorted((ROOT / "shared" / d).glob("*.md")):
            items[f"{d}/{f.name}"] = (folder, skills)
    for name, (folder, skills) in items.items():
        src = (ROOT / "shared" / name).read_bytes()
        for skill in skills:
            dst = ROOT / "skills" / skill / folder / Path(name).name
            if dst.exists() and dst.read_bytes() == src:
                continue
            stale.append(str(dst.relative_to(ROOT)))
            if not a.check:
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.write_bytes(src)
    if a.check:
        for s in stale:
            print(f"out of date: {s}")
        return 1 if stale else 0
    print(f"synced {len(stale)} file(s)" if stale else "all shared files up to date")
    return 0


if __name__ == "__main__":
    sys.exit(main())
