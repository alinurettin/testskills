#!/usr/bin/env python3
"""Create a Playwright (TypeScript) automation project skeleton from the bundled template.

Never overwrites existing files (use --force to replace template files explicitly).
The GitHub Actions workflow is written to <repo-root>/.github/workflows/ because
GitHub only reads workflows from the repository root.

Usage:
  python scaffold_project.py --dir automation --project "Online Mağaza" --base-url https://staging.example.com
  python scaffold_project.py --dir e2e --repo-root . --locale en-US --timezone Europe/London --no-ci
Then:  cd automation && npm install && npx playwright install
"""
from __future__ import annotations

import argparse
import os
import re
import sys
import unicodedata
from pathlib import Path

TEMPLATE = Path(__file__).resolve().parent.parent / "assets" / "template"
TOKEN = re.compile(r"\{\{(PROJECT|PROJECT_SLUG|BASE_URL|LOCALE|TIMEZONE|AUTOMATION_DIR)\}\}")


def slug(s: str) -> str:
    s = s.replace("ı", "i").replace("İ", "I")
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-") or "project"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dir", default="automation", help="automation project folder (created if missing)")
    ap.add_argument("--repo-root", help="repository root for .github/workflows (default: parent of --dir)")
    ap.add_argument("--project", default="Project")
    ap.add_argument("--base-url", default="http://localhost:3000")
    ap.add_argument("--locale", default="tr-TR")
    ap.add_argument("--timezone", default="Europe/Istanbul")
    ap.add_argument("--no-ci", action="store_true", help="skip the GitHub Actions workflow")
    ap.add_argument("--force", action="store_true", help="overwrite existing template files")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    target = Path(a.dir).resolve()
    repo_root = Path(a.repo_root).resolve() if a.repo_root else target.parent
    rel = os.path.relpath(target, repo_root).replace("\\", "/")
    values = {"PROJECT": a.project, "PROJECT_SLUG": slug(a.project), "BASE_URL": a.base_url,
              "LOCALE": a.locale, "TIMEZONE": a.timezone, "AUTOMATION_DIR": rel if rel != "." else "."}

    written, skipped = [], []
    for src in sorted(TEMPLATE.rglob("*")):
        if src.is_dir():
            continue
        relpath = src.relative_to(TEMPLATE)
        if relpath.parts[0] == ".github":
            if a.no_ci:
                continue
            dst = repo_root / relpath
        else:
            dst = target / relpath
        if dst.exists() and not a.force:
            skipped.append(dst)
            continue
        text = TOKEN.sub(lambda m: values[m.group(1)], src.read_text(encoding="utf-8"))
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(text, encoding="utf-8", newline="\n")
        written.append(dst)
    for d in ("tests", "pages"):
        (target / d).mkdir(parents=True, exist_ok=True)

    print(f"automation project: {target}")
    for p in written:
        print(f"  + {p.relative_to(repo_root) if p.is_relative_to(repo_root) else p}")
    for p in skipped:
        print(f"  = {p.relative_to(repo_root) if p.is_relative_to(repo_root) else p} (exists, kept)")
    print(f"next: cd {rel} && npm install && npx playwright install")
    return 0


if __name__ == "__main__":
    sys.exit(main())
