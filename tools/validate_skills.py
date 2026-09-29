#!/usr/bin/env python3
"""Validate every skill against the Agent Skills spec and QA Suite conventions.

Checks (errors unless noted):
  - SKILL.md exists and starts with YAML frontmatter
  - name: 1-64 chars, [a-z0-9-], no leading/trailing/double hyphen, matches the
    directory, does not contain "anthropic" or "claude"
  - description: 1-1024 chars, no XML tags
  - only portable frontmatter keys (name, description, license, compatibility,
    metadata, allowed-tools) so the skill uploads to claude.ai / API unchanged
  - SKILL.md body <= 500 lines (warning above 400)
  - every relative path mentioned as scripts/..., references/..., assets/...
    exists inside the skill
  - reference files > 100 lines have a "Contents" section (warning)
  - Python scripts compile
  - .claude-plugin/plugin.json and marketplace.json are valid JSON with names

Usage: python tools/validate_skills.py   (exit 1 on errors)
"""
from __future__ import annotations

import json
import py_compile
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ALLOWED_KEYS = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
PATH_RE = re.compile(r"(?<![\w./-])((?:scripts|references|assets)/[\w./-]+\.\w+)")


def parse_frontmatter(text: str):
    if not text.startswith("---"):
        return None, text
    end = text.find("\n---", 3)
    if end == -1:
        return None, text
    block, body = text[3:end].strip("\n"), text[end + 4:]
    data, key = {}, None
    for line in block.splitlines():
        if not line.strip():
            continue
        if line[0] in " \t" and key:
            data[key] = (data[key] + " " + line.strip()).strip() if isinstance(data[key], str) else data[key]
            continue
        m = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if m:
            key, val = m.group(1), m.group(2).strip()
            data[key] = val.strip('"').strip("'") if val else ""
    return data, body


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    errors, warnings = [], []
    skills = sorted(p for p in (ROOT / "skills").iterdir() if p.is_dir())
    for sd in skills:
        sk = sd / "SKILL.md"
        tag = sd.name
        if not sk.exists():
            errors.append(f"{tag}: SKILL.md missing")
            continue
        text = sk.read_text(encoding="utf-8")
        fm, body = parse_frontmatter(text)
        if fm is None:
            errors.append(f"{tag}: no YAML frontmatter")
            continue
        name, desc = fm.get("name", ""), fm.get("description", "")
        if not (1 <= len(name) <= 64 and NAME_RE.match(name)):
            errors.append(f"{tag}: invalid name '{name}'")
        if name != sd.name:
            errors.append(f"{tag}: name '{name}' does not match directory")
        if "anthropic" in name or "claude" in name:
            errors.append(f"{tag}: name must not contain 'anthropic' or 'claude'")
        if not (1 <= len(desc) <= 1024):
            errors.append(f"{tag}: description length {len(desc)} (must be 1-1024)")
        if re.search(r"<[A-Za-z/][^>]*>", desc):
            errors.append(f"{tag}: description contains XML/HTML tags")
        extra = set(fm) - ALLOWED_KEYS
        if extra:
            errors.append(f"{tag}: non-portable frontmatter keys {sorted(extra)}")
        lines = body.count("\n")
        if lines > 500:
            errors.append(f"{tag}: SKILL.md body has {lines} lines (> 500)")
        elif lines > 400:
            warnings.append(f"{tag}: SKILL.md body has {lines} lines (consider moving detail to references/)")
        for ref in sorted(set(PATH_RE.findall(text))):
            if not (sd / ref).exists():
                errors.append(f"{tag}: referenced file not found: {ref}")
        for ref in (sd / "references").glob("*.md") if (sd / "references").exists() else []:
            content = ref.read_text(encoding="utf-8")
            if content.count("\n") > 100 and "## Contents" not in content and ref.name != "data-model.md":
                warnings.append(f"{tag}/references/{ref.name}: > 100 lines without a '## Contents' section")
        for py in (sd / "scripts").glob("*.py") if (sd / "scripts").exists() else []:
            try:
                py_compile.compile(str(py), doraise=True)
            except py_compile.PyCompileError as e:
                errors.append(f"{tag}/scripts/{py.name}: {e.msg}")
        print(f"{'OK ' if not any(e.startswith(tag + ':') or e.startswith(tag + '/') for e in errors) else 'ERR'} "
              f"{tag:24s} desc={len(desc):4d} chars  body={lines:3d} lines")
    for f in ("plugin.json", "marketplace.json"):
        p = ROOT / ".claude-plugin" / f
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            if not data.get("name"):
                errors.append(f".claude-plugin/{f}: missing name")
        except (OSError, ValueError) as e:
            errors.append(f".claude-plugin/{f}: {e}")
    for w in warnings:
        print(f"WARN  {w}")
    for e in errors:
        print(f"ERROR {e}")
    print(f"{len(skills)} skills · {len(errors)} errors · {len(warnings)} warnings")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
