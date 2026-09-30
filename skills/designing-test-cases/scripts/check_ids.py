#!/usr/bin/env python3
"""Check Turkish identifier test data, derive invalid variants, and generate synthetic valid values.

Supports TCKN (T.C. Kimlik No), VKN (tax number) and IBAN (ISO 13616, mod-97; TR = 26 chars).
The checksums come from tr_ids.py (one implementation shared by the suite). TCKN and IBAN are
verified against well-known published examples, VKN against VKNs that companies publish on their
"bilgi toplumu hizmetleri" pages (sources in tr_ids.py).

ID policy: a checksum-valid value is valid by algorithm only and can belong to a real person,
company or account (Türkiye has no reserved fictional ranges). Synthetic checksum-valid values
are allowed in TEST environments only and must come from a generator (--generate here, or
gen_data.py in the preparing-test-data skill) - never copied from the internet or production,
and never used in production or in systems shared outside the test boundary.

Usage:
  python check_ids.py tckn 10000000146 12345678901
  python check_ids.py iban "TR33 0006 1005 1978 6457 8413 26"
  python check_ids.py tckn 10000000146 --variants        # invalid variants for negative tests (single fault each)
  python check_ids.py vkn 1234567890 --format json
  python check_ids.py tckn --generate 3 --seed 7          # synthetic checksum-valid values (test environments only)
  python check_ids.py iban --generate 1 --variants        # a synthetic TR IBAN and its variants
Exit codes: 0 all values valid, 1 at least one invalid value, 2 usage error.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tr_ids import gen_tckn, gen_tr_iban, gen_vkn, invalid_variants, validate_iban, validate_tckn, validate_vkn  # noqa: E402

CHECK = {"tckn": validate_tckn, "vkn": validate_vkn, "iban": validate_iban}
GENERATE = {"tckn": gen_tckn, "vkn": gen_vkn, "iban": gen_tr_iban}
POLICY = ("Note: checksum-valid values are valid by algorithm only and may belong to real people, companies "
          "or accounts. Use only generated synthetic values, only in test environments.")


def tckn(v: str) -> tuple[bool, str]:
    return validate_tckn(v)


def vkn(v: str) -> tuple[bool, str]:
    return validate_vkn(v)


def iban(v: str) -> tuple[bool, str]:
    return validate_iban(v)


def variants(kind: str, v: str) -> list[tuple[str, str]]:
    rows = []
    for val, why, _expect in invalid_variants(kind, v):
        ok, reason = CHECK[kind](val.strip() if kind == "iban" else val)
        rows.append((val, f"{why} -> {'VALID' if ok else 'invalid'} ({reason})"))
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("kind", choices=sorted(CHECK))
    ap.add_argument("values", nargs="*")
    ap.add_argument("--variants", action="store_true", help="derive invalid variants of each (valid) value")
    ap.add_argument("--generate", type=int, default=0, metavar="N",
                    help="add N synthetic checksum-valid values (IBAN: TR); test environments only")
    ap.add_argument("--seed", default="1", help="seed for --generate (same seed = same values, default 1)")
    ap.add_argument("--format", choices=["md", "json"], default="md")
    sys.stdout.reconfigure(encoding="utf-8")
    a = ap.parse_args()
    if a.generate < 0 or not (a.values or a.generate):
        ap.error("give one or more values, or --generate N")
    rng = random.Random(a.seed)
    values = [(v, False) for v in a.values] + [(GENERATE[a.kind](rng), True) for _ in range(a.generate)]
    res = []
    for v, generated in values:
        ok, reason = CHECK[a.kind](v if a.kind == "iban" else v.strip())
        item = {"value": v, "valid": ok, "reason": reason}
        if generated:
            item["synthetic"] = True
        if a.variants:
            item["variants"] = [{"value": x, "note": n} for x, n in variants(a.kind, v)]
        res.append(item)
    if a.format == "json":
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        for r in res:
            tag = ", synthetic" if r.get("synthetic") else ""
            print(f"{r['value']}: {'VALID' if r['valid'] else 'INVALID'} ({r['reason']}{tag})")
            for x in r.get("variants", []):
                print(f"  - {x['value']!r}: {x['note']}")
        if any(r["valid"] for r in res):
            print(POLICY)
    return 0 if all(r["valid"] for r in res) else 1


if __name__ == "__main__":
    sys.exit(main())
