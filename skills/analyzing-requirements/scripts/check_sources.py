#!/usr/bin/env python3
"""Check that every requirement can be traced to the source documents (guards against invented requirements).

An AI assistant can write a plausible requirement that no stakeholder ever stated. For each requirement
in requirements.json this script measures how many of its content words (and all of its numbers) occur
in the source documents given on the command line:

  SUPPORTED     enough of the wording and every number is found in the sources
  WEAK          the wording overlaps only partly: check the source reference by hand
  NOT_FOUND     little overlap, or a number that appears nowhere in the sources
  DERIVED       marked `derived: true` (inferred by the analysis): not checked, listed for confirmation

A NOT_FOUND requirement must either be marked `derived: true` (and then confirmed by a person) or be
corrected. The check is lexical: it cannot tell whether the meaning was changed, so SUPPORTED is not proof.

Usage:
  python check_sources.py qa/requirements.json docs/story.md [more sources...] [--out qa/source-check.md]
      [--min-overlap 0.6] [--lang tr|en]
Exit 1 when a requirement is NOT_FOUND, 2 on unreadable input.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

WORD = re.compile(r"[^\W\d_]{4,}", re.UNICODE)
NUM = re.compile(r"\d+(?:[.,]\d+)*")
TR = str.maketrans("İIŞĞÜÖÇ", "iışğüöç")


def norm(s: str) -> str:
    return s.translate(TR).lower()


def stems(text: str) -> set[str]:
    """First 5 letters of each word: a crude stem that survives Turkish and English suffixes."""
    return {w[:5] for w in WORD.findall(norm(text))}


def numbers(text: str) -> set[str]:
    return {n.replace(".", "").replace(",", "") for n in NUM.findall(text)} - {""}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("requirements")
    ap.add_argument("sources", nargs="+")
    ap.add_argument("--out")
    ap.add_argument("--min-overlap", type=float, default=0.6)
    ap.add_argument("--lang", choices=["tr", "en"], default="en")
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    a = ap.parse_args()
    try:
        data = json.loads(Path(a.requirements).read_text(encoding="utf-8-sig"))
        reqs = data["requirements"] if isinstance(data, dict) else data
        src = "\n".join(Path(p).read_text(encoding="utf-8-sig") for p in a.sources)
    except (OSError, ValueError, KeyError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    s_stems, s_nums = stems(src), numbers(src)
    rows, bad = [], 0
    for r in reqs:
        if r.get("status") == "deprecated":
            continue
        if r.get("derived"):
            rows.append((r["id"], "DERIVED", "", r.get("title", "")))
            continue
        text = f"{r.get('text', '')} " + " ".join(map(str, r.get("acceptance_criteria") or []))
        st = stems(r.get("text", ""))
        overlap = len(st & s_stems) / len(st) if st else 0.0
        small = {str(i) for i in range(10)}
        missing = sorted(numbers(r.get("text", "")) - s_nums - small)       # the statement itself must keep source numbers
        ac_only = sorted(numbers(text) - s_nums - small - set(missing))     # numbers introduced in acceptance criteria
        if missing or overlap < a.min_overlap / 2:
            verdict = "NOT_FOUND"
            bad += 1
        elif overlap < a.min_overlap or ac_only:
            verdict = "WEAK"
        else:
            verdict = "SUPPORTED"
        note = f"{round(100 * overlap)}%" + (f"; numbers not in sources: {', '.join(missing)}" if missing else "") +             (f"; acceptance criteria add numbers: {', '.join(ac_only)}" if ac_only else "")
        rows.append((r["id"], verdict, note, r.get("title", "")))
    head = ("Gereksinim | Sonuç | Örtüşme | Başlık" if a.lang == "tr" else "Requirement | Verdict | Overlap | Title")
    L = ["# " + ("Kaynak kontrolü" if a.lang == "tr" else "Source check"), "", f"| {head} |", "|---|---|---|---|"]
    L += [f"| {i} | {v} | {n} | {t} |" for i, v, n, t in rows]
    text = "\n".join(L) + "\n"
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(text, encoding="utf-8", newline="\n")
    else:
        print(text)
    counts = {v: sum(1 for r in rows if r[1] == v) for v in ("SUPPORTED", "WEAK", "NOT_FOUND", "DERIVED")}
    print(" · ".join(f"{k} {v}" for k, v in counts.items()), file=sys.stderr)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
