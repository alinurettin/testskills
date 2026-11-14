#!/usr/bin/env python3
"""Read-only local preflight. Never installs packages, signs in, or uses the network."""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


def inspect(profile="core", project=None):
    checks = [{"name": "python", "required": True, "ok": sys.version_info >= (3, 12),
               "detail": sys.version.split()[0], "requirement": ">=3.12"}]
    node = shutil.which("node")
    required = profile in {"api", "automation"}
    version, usable = None, False
    if node:
        result = subprocess.run([node, "--version"], capture_output=True, text=True, timeout=10)
        version = result.stdout.strip()
        try:
            major, minor = map(int, version.lstrip("v").split(".")[:2])
            usable = result.returncode == 0 and (major == 22 and minor >= 18 or major in {24, 26})
        except ValueError:
            pass
    checks.append({"name": "node", "required": required, "ok": usable, "detail": version,
                   "requirement": "22.18+, 24 or 26 (core scripts do not need Node)"})
    playwright = False
    if node and required:
        result = subprocess.run([node, "-e", "require.resolve('@playwright/test')"],
                                cwd=project or Path.cwd(), capture_output=True, timeout=10)
        playwright = result.returncode == 0
    checks.append({"name": "@playwright/test", "required": required, "ok": playwright,
                   "detail": "project-local resolution only; not installed by doctor"})
    return {"profile": profile, "ok": all(c["ok"] for c in checks if c["required"]), "checks": checks}


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--profile", choices=["core", "api", "automation"], default="core")
    ap.add_argument("--project", type=Path, default=Path.cwd())
    args = ap.parse_args()
    try:
        result = inspect(args.profile, args.project)
    except (OSError, subprocess.TimeoutExpired) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 1
    print(json.dumps(result, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
