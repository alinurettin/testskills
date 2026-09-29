#!/usr/bin/env python3
"""Package every skill as a .zip for upload to claude.ai / the Claude API (Settings → Skills).

Each zip contains one top-level folder named after the skill (SKILL.md + scripts/ references/ assets/).
Runs the validator first; nothing is written if a skill is invalid.

Usage: python tools/package_skills.py [--out dist]
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP = {"__pycache__", ".DS_Store"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "dist"))
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    if subprocess.run([sys.executable, str(ROOT / "tools" / "validate_skills.py")], capture_output=True).returncode:
        print("validation failed - run tools/validate_skills.py", file=sys.stderr)
        return 1
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    for skill in sorted(p for p in (ROOT / "skills").iterdir() if (p / "SKILL.md").exists()):
        target = out / f"{skill.name}.zip"
        with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as z:
            for f in sorted(skill.rglob("*")):
                if f.is_file() and not (SKIP & set(f.parts)) and f.suffix != ".pyc":
                    z.write(f, f"{skill.name}/{f.relative_to(skill).as_posix()}")
        print(f"{target.name:34s} {target.stat().st_size // 1024:4d} KB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
