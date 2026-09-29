#!/usr/bin/env python3
"""Check Turkish identifier test data and derive invalid variants for negative tests.

Supports TCKN (T.C. Kimlik No), VKN (tax number) and IBAN (ISO 13616, mod-97; TR = 26 chars).
TCKN and IBAN are verified against well-known published examples; the VKN check implements the
published algorithm but has not been verified against a known valid VKN - confirm it with one
valid VKN from your test data before relying on it.
It only VALIDATES values you supply and MUTATES them into invalid variants. It deliberately
does not generate new valid identifiers: valid synthetic values must come from your test
environment's designated test data, so no real person's number is produced.

Usage:
  python check_ids.py tckn 10000000146 12345678901
  python check_ids.py iban "TR33 0006 1005 1978 6457 8413 26"
  python check_ids.py tckn 10000000146 --variants        # invalid variants for negative tests (single fault each)
  python check_ids.py vkn 1234567890 --format json
"""
from __future__ import annotations

import argparse
import json
import re
import sys


def tckn(v: str) -> tuple[bool, str]:
    if not re.fullmatch(r"\d{11}", v):
        return False, "must be exactly 11 digits"
    d = [int(c) for c in v]
    if d[0] == 0:
        return False, "first digit must not be 0"
    if (sum(d[0:9:2]) * 7 - sum(d[1:8:2])) % 10 != d[9]:
        return False, "10th digit checksum wrong"
    if sum(d[:10]) % 10 != d[10]:
        return False, "11th digit checksum wrong"
    return True, "valid"


def vkn(v: str) -> tuple[bool, str]:
    if not re.fullmatch(r"\d{10}", v):
        return False, "must be exactly 10 digits"
    d = [int(c) for c in v]
    total = 0
    for i in range(9):
        t = (d[i] + 10 - (i + 1)) % 10
        if t == 9:
            total += 9
        elif t:
            total += (t * pow(2, 9 - i, 9)) % 9 or 9
    return ((10 - total % 10) % 10 == d[9]), ("valid" if (10 - total % 10) % 10 == d[9] else "check digit wrong")


def iban(v: str) -> tuple[bool, str]:
    s = re.sub(r"\s+", "", v).upper()
    if not re.fullmatch(r"[A-Z]{2}\d{2}[A-Z0-9]{10,30}", s):
        return False, "format must be CC + 2 check digits + BBAN"
    if s.startswith("TR") and len(s) != 26:
        return False, "TR IBAN must be 26 characters"
    num = "".join(str(int(c, 36)) for c in s[4:] + s[:4])
    return (int(num) % 97 == 1), ("valid" if int(num) % 97 == 1 else "mod-97 check failed")


CHECK = {"tckn": tckn, "vkn": vkn, "iban": iban}


def variants(kind: str, v: str) -> list[tuple[str, str]]:
    s = re.sub(r"\s+", "", v)
    out = []
    digit = lambda c: str((int(c) + 1) % 10)
    if kind in ("tckn", "vkn"):
        out += [(s[:-1] + digit(s[-1]), "last check digit changed"),
                (s[:-1], "one digit short"), (s + "0", "one digit long"),
                (s[:-2] + "a" + s[-1], "non-numeric character"), ("", "empty"),
                (" " + s + " ", "leading/trailing spaces (should be trimmed or rejected - clarify)")]
        if kind == "tckn":
            out += [("0" + s[1:], "first digit 0"), (s[:9] + digit(s[9]) + s[10], "10th digit changed")]
    else:
        out += [(s[:4] + s[4:-1] + digit(s[-1]), "last digit changed (mod-97 fails)"),
                (s[:2] + digit(s[2]) + s[3:], "check digit changed"), (s[:-1], "one character short"),
                (s + "0", "one character long"), (s.lower(), "lower case (accept after normalising? clarify)"),
                (" ".join(s[i:i + 4] for i in range(0, len(s), 4)), "grouped with spaces (usually accepted)"),
                ("DE" + s[2:], "wrong country code")]
    rows = []
    for val, why in out:
        ok, reason = CHECK[kind](val.strip() if kind == "iban" else val)
        rows.append((val, f"{why} -> {'VALID' if ok else 'invalid'} ({reason})"))
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("kind", choices=sorted(CHECK))
    ap.add_argument("values", nargs="+")
    ap.add_argument("--variants", action="store_true", help="derive invalid variants of each (valid) value")
    ap.add_argument("--format", choices=["md", "json"], default="md")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    res = []
    for v in a.values:
        ok, reason = CHECK[a.kind](v if a.kind == "iban" else v.strip())
        item = {"value": v, "valid": ok, "reason": reason}
        if a.variants:
            item["variants"] = [{"value": x, "note": n} for x, n in variants(a.kind, v)]
        res.append(item)
    if a.format == "json":
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        for r in res:
            print(f"{r['value']}: {'VALID' if r['valid'] else 'INVALID'} ({r['reason']})")
            for x in r.get("variants", []):
                print(f"  - {x['value']!r}: {x['note']}")
    return 0 if all(r["valid"] for r in res) else 1


if __name__ == "__main__":
    sys.exit(main())
