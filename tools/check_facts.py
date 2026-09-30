#!/usr/bin/env python3
"""Check the registry of volatile facts (docs/volatile-facts.json) and flag entries due for re-verification.

Store rules, standard versions, legal dates and tool formats change. Each fact the skills rely on
is registered once with the files that state it, a source and the date it was last verified:

  [{"id": "google-play-target-api",                 lowercase letters, digits, hyphens; unique
    "fact": "Since 31 August 2026 ... API 36 ...",  what was verified, in one or two sentences
    "files": ["skills/.../mobile-testing.md"],      repo-relative files that state the fact
    "source_url": "https://developer.android.com/...",
    "verified_on": "2026-09-30",                    YYYY-MM-DD
    "note": "optional"}]

For every entry older than --max-age-days (default 180) it prints a GitHub Actions warning
("::warning::..."), which shows up as an annotation in CI without failing the build. Files that
no longer exist are warnings too. When you re-verify a fact: open the source, fix the stale text
in every listed file, and set verified_on to today.

Usage:
  python tools/check_facts.py
  python tools/check_facts.py --max-age-days 90 --today 2027-04-01
Exit codes: 0 valid (warnings possible), 1 file missing or malformed, 2 usage error.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date, timedelta
from pathlib import Path, PurePosixPath, PureWindowsPath

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_FILE = ROOT / "docs" / "volatile-facts.json"
REQUIRED = ("id", "fact", "files", "source_url", "verified_on")
OPTIONAL = ("note",)
ID_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")


def gh_escape(text: str) -> str:
    """Escape a message for a GitHub Actions workflow command."""
    return text.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")


def parse_day(value) -> date | None:
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def validate(data, today: date, root: Path = ROOT) -> tuple[list[str], list[str]]:
    """(errors, warnings) for the parsed JSON. Errors mean the registry is malformed."""
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(data, list):
        return ["top level must be a JSON list of fact objects"], []
    seen: set[str] = set()
    for n, e in enumerate(data, 1):
        where = f"entry {n}"
        if not isinstance(e, dict):
            errors.append(f"{where}: must be an object")
            continue
        fid = e.get("id")
        if isinstance(fid, str) and fid:
            where = f"entry {n} ({fid})"
        missing = [k for k in REQUIRED if k not in e]
        unknown = sorted(set(e) - set(REQUIRED) - set(OPTIONAL))
        if missing:
            errors.append(f"{where}: missing {', '.join(missing)}")
        if unknown:
            errors.append(f"{where}: unknown key(s) {', '.join(unknown)} (allowed: {', '.join(REQUIRED + OPTIONAL)})")
        if "id" in e:
            if not isinstance(fid, str) or not ID_RE.fullmatch(fid):
                errors.append(f"{where}: id must be lowercase letters, digits and hyphens")
            elif fid in seen:
                errors.append(f"{where}: duplicate id")
            else:
                seen.add(fid)
        for k in ("fact",) + OPTIONAL:
            if k in e and (not isinstance(e[k], str) or not e[k].strip()):
                errors.append(f"{where}: {k} must be a non-empty string")
        files = e.get("files")
        if "files" in e:
            if not isinstance(files, list) or not files or not all(isinstance(f, str) and f.strip() for f in files):
                errors.append(f"{where}: files must be a non-empty list of repo-relative paths")
                files = []
            for f in files:
                posix = PurePosixPath(f.replace("\\", "/"))
                if posix.is_absolute() or PureWindowsPath(f).drive or ".." in posix.parts:
                    errors.append(f"{where}: file path must be repo-relative: {f}")
                elif not (root / f).exists():
                    warnings.append(f"{fid or where}: listed file not found: {f} - update the registry")
        url = e.get("source_url")
        if "source_url" in e and (not isinstance(url, str) or not re.fullmatch(r"https://\S+", url)):
            errors.append(f"{where}: source_url must be an https:// URL")
        if "verified_on" in e:
            day = parse_day(e["verified_on"])
            if day is None:
                errors.append(f"{where}: verified_on must be a date YYYY-MM-DD")
            elif day > today + timedelta(days=1):
                errors.append(f"{where}: verified_on {day} is in the future")
    return errors, warnings


def stale(data: list, today: date, max_age: int) -> list[str]:
    """Warnings for entries verified more than max_age days before today."""
    out = []
    for e in data:
        day = parse_day(e.get("verified_on"))
        if day is None:
            continue
        age = (today - day).days
        if age > max_age:
            out.append(f"{e['id']}: last verified {day} ({age} days ago, limit {max_age}) - re-check "
                       f"{e['source_url']} and update {', '.join(e['files'])}")
    return out


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--file", default=str(DEFAULT_FILE), help="registry JSON (default docs/volatile-facts.json)")
    ap.add_argument("--max-age-days", type=int, default=180, dest="max_age")
    ap.add_argument("--today", help="YYYY-MM-DD (default: the current date; for tests)")
    ap.add_argument("--root", default=str(ROOT), help="repository root the file paths are relative to")
    a = ap.parse_args()
    today = parse_day(a.today) if a.today else date.today()
    if today is None or a.max_age < 0:
        print("error: --today must be YYYY-MM-DD and --max-age-days >= 0", file=sys.stderr)
        return 2
    path = Path(a.file)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        print(f"::error::{gh_escape(f'cannot read {path}: {e}')}")
        return 1
    errors, warnings = validate(data, today, Path(a.root))
    for m in errors:
        print(f"::error::{gh_escape(f'{path.name}: {m}')}")
    if errors:
        print(f"{path.name}: {len(errors)} error(s) - fix the registry")
        return 1
    due = stale(data, today, a.max_age)
    for m in due + warnings:
        print(f"::warning::{gh_escape(m)}")
    print(f"{path.name}: {len(data)} fact(s), {len(due)} due for re-verification (older than {a.max_age} days), "
          f"{len(warnings)} other warning(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
