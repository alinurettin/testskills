#!/usr/bin/env python3
"""Turkish identifier checksums: TCKN, VKN, TR IBAN and generic IBAN (ISO 13616, mod 97).

This is the ONE implementation used by the suite. It is copied into the scripts/ folder of
designing-test-cases (check_ids.py), preparing-test-data (gen_data.py, mask_data.py,
data_needs.py) and testing-ai-features (ai_eval.py). Edit it only as shared/scripts/tr_ids.py
and run `python tools/sync_shared.py`; the copies are overwritten.

Pure functions, standard library only, no I/O. Import it from a script in the same folder:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from tr_ids import is_valid_tckn, gen_tckn

  validate_tckn / validate_vkn / validate_iban / validate_tr_iban (value) -> (ok, reason)
      Strict: TCKN and VKN are checked exactly as given (" 10000000146 " is invalid, so a
      "surrounding spaces" variant stays a separate negative test). IBANs are normalised first:
      all whitespace removed, upper-cased (the printed, grouped form is legal).
  is_valid_tckn / is_valid_vkn / is_valid_iban / is_valid_tr_iban (value) -> bool
      Lenient: str(value) with surrounding whitespace ignored, for data that was read from files.
  tckn_check_digits(first9), vkn_check_digit(first9), iban_check_digits(country, bban)
  gen_tckn(rng), gen_vkn(rng), gen_tr_iban(rng, bank_codes=None)
      One checksum-valid synthetic value from a random.Random (deterministic for a seed).
  invalid_variants(kind, value) -> [(variant, fault, expect)]
      Single-fault variants for negative tests; expect is "invalid", or "clarify" for notation
      variants (spaces, case, grouping) whose acceptance is a requirement decision.
Only ASCII digits count as digits (a full-width or Arabic-Indic digit makes the value invalid).

Algorithms
  TCKN (T.C. kimlik no): 11 digits, first digit not 0.
      d10 = ((d1+d3+d5+d7+d9) * 7 - (d2+d4+d6+d8)) mod 10;  d11 = (d1+...+d10) mod 10.
  VKN (vergi kimlik no): 10 digits. For each of the first nine digits d_i (i = 1..9):
      t_i = (d_i + 10 - i) mod 10;  p_i = t_i * 2^(10-i) mod 9, and p_i = 9 when t_i = 9;
      d10 = (10 - (p_1+...+p_9) mod 10) mod 10.
      Verified on 2026-09-30 against VKNs that legal entities publish on their "bilgi toplumu
      hizmetleri" pages (Turkish Commercial Code art. 1524):
        4730030397  https://www.ilbank.gov.tr/sayfa/bilgi-toplumu-hizmetleri
        1430023849  https://www.basf.com/tr/tr/legal/bilgi-toplumu-hizmetleri
  IBAN (ISO 13616; check digits ISO 7064 MOD 97-10): move the first four characters to the end,
      replace letters by 10..35 (A..Z); the resulting number mod 97 must be 1.
      TR IBAN: 26 characters = TR + 2 check digits + 5-digit bank code + 1 reserve digit
      (always 0 in practice) + 16-character account number (IBAN registry: TR kk 5!n 1!n 16!c).
      Only the TR length and layout are checked; other countries' lengths are not.

POLICY: a checksum-valid value is valid by algorithm only. Türkiye has no reserved fictional
TCKN, VKN or IBAN ranges, so a generated value can belong to a real person, company or account.
Synthetic checksum-valid values are allowed in TEST environments and must come from these
generators (check_ids.py --generate, gen_data.py, mask_data.py fake); never put them into
production or into systems shared outside the test boundary (real registries, payment
networks, e-mail/SMS gateways, partners).
"""
from __future__ import annotations

import re

__all__ = [
    "DEFAULT_BANK_CODES", "tckn_check_digits", "validate_tckn", "is_valid_tckn", "vkn_check_digit",
    "validate_vkn", "is_valid_vkn", "normalize_iban", "iban_check_digits", "validate_iban", "is_valid_iban",
    "validate_tr_iban", "is_valid_tr_iban", "iban_display", "gen_tckn", "gen_vkn", "gen_tr_iban",
    "invalid_variants", "KINDS",
]

# A few well-known Turkish bank codes (5 digits) for synthetic IBANs. Pass your own list when the
# system under test validates bank codes against the current participant list.
DEFAULT_BANK_CODES = ("00010", "00012", "00015", "00046", "00062", "00064", "00067")
KINDS = ("tckn", "vkn", "iban", "tr_iban")

_DIGITS = re.compile(r"[0-9]+")
_IBAN_SHAPE = re.compile(r"[A-Z]{2}[0-9]{2}[A-Z0-9]{10,30}")
_TR_IBAN_SHAPE = re.compile(r"TR[0-9]{2}[0-9]{6}[A-Z0-9]{16}")


def _digits(s: str, n: int) -> bool:
    return len(s) == n and _DIGITS.fullmatch(s) is not None


# ---------------------------------------------------------------------------------------- TCKN
def tckn_check_digits(first9: str) -> str:
    """The 10th and 11th digit of a T.C. kimlik no for the given first nine digits."""
    d = [int(c) for c in first9]
    d10 = ((d[0] + d[2] + d[4] + d[6] + d[8]) * 7 - (d[1] + d[3] + d[5] + d[7])) % 10
    d11 = (sum(d) + d10) % 10
    return f"{d10}{d11}"


def validate_tckn(value: str) -> tuple[bool, str]:
    """(ok, reason) for the value exactly as given."""
    v = str(value)
    if not _digits(v, 11):
        return False, "must be exactly 11 digits"
    if v[0] == "0":
        return False, "first digit must not be 0"
    cd = tckn_check_digits(v[:9])
    if cd[0] != v[9]:
        return False, "10th digit checksum wrong"
    if cd[1] != v[10]:
        return False, "11th digit checksum wrong"
    return True, "valid"


def is_valid_tckn(value) -> bool:
    return validate_tckn(str(value).strip())[0]


# ----------------------------------------------------------------------------------------- VKN
def vkn_check_digit(first9: str) -> str:
    """The 10th digit of a vergi kimlik no (VKN) for the given first nine digits."""
    total = 0
    for i, c in enumerate(first9):  # i = 0..8, position i + 1
        t = (int(c) + 9 - i) % 10
        if t == 9:
            total += 9
        elif t:
            total += (t * 2 ** (9 - i)) % 9  # never 0 for t in 1..8 (2^k is coprime to 9)
    return str((10 - total % 10) % 10)


def validate_vkn(value: str) -> tuple[bool, str]:
    """(ok, reason) for the value exactly as given."""
    v = str(value)
    if not _digits(v, 10):
        return False, "must be exactly 10 digits"
    if vkn_check_digit(v[:9]) != v[9]:
        return False, "check digit wrong"
    return True, "valid"


def is_valid_vkn(value) -> bool:
    return validate_vkn(str(value).strip())[0]


# ---------------------------------------------------------------------------------------- IBAN
def normalize_iban(value: str) -> str:
    """Remove all whitespace and upper-case (the electronic form of an IBAN)."""
    return re.sub(r"\s+", "", str(value)).upper()


def _mod97(s: str) -> int:
    return int("".join(str(int(ch, 36)) for ch in s)) % 97


def iban_check_digits(country: str, bban: str) -> str:
    """ISO 13616 / ISO 7064 MOD 97-10 check digits for a country code and BBAN."""
    return f"{98 - _mod97((bban + country + '00').upper()):02d}"


def validate_iban(value: str) -> tuple[bool, str]:
    """(ok, reason) for any country; TR IBANs must also have the TR length and layout."""
    s = normalize_iban(value)
    if not _IBAN_SHAPE.fullmatch(s):
        return False, "format must be CC + 2 check digits + BBAN"
    if s.startswith("TR"):
        if len(s) != 26:
            return False, "TR IBAN must be 26 characters"
        if not _TR_IBAN_SHAPE.fullmatch(s):
            return False, "TR IBAN bank code and reserve digit must be digits"
    if _mod97(s[4:] + s[:4]) != 1:
        return False, "mod-97 check failed"
    return True, "valid"


def is_valid_iban(value) -> bool:
    return validate_iban(str(value))[0]


def validate_tr_iban(value: str) -> tuple[bool, str]:
    """(ok, reason); like validate_iban, but the country code must be TR."""
    s = normalize_iban(value)
    if not s.startswith("TR"):
        return False, "country code must be TR"
    return validate_iban(s)


def is_valid_tr_iban(value) -> bool:
    return validate_tr_iban(str(value))[0]


def iban_display(iban: str) -> str:
    """The printed form: groups of four characters."""
    s = normalize_iban(iban)
    return " ".join(s[i:i + 4] for i in range(0, len(s), 4))


# ---------------------------------------------------------------------------------- generation
def gen_tckn(rng) -> str:
    """A checksum-valid synthetic TCKN (first digit 1-9). Can coincide with a real person."""
    first9 = str(rng.randint(1, 9)) + "".join(str(rng.randint(0, 9)) for _ in range(8))
    return first9 + tckn_check_digits(first9)


def gen_vkn(rng) -> str:
    """A checksum-valid synthetic VKN. Can coincide with a real taxpayer."""
    first9 = "".join(str(rng.randint(0, 9)) for _ in range(9))
    return first9 + vkn_check_digit(first9)


def gen_tr_iban(rng, bank_codes=None) -> str:
    """A mod-97-valid synthetic TR IBAN (compact form, reserve digit 0). Can coincide with a real account."""
    bban = str(rng.choice(bank_codes or DEFAULT_BANK_CODES)) + "0" + "".join(str(rng.randint(0, 9)) for _ in range(16))
    return "TR" + iban_check_digits("TR", bban) + bban


# ------------------------------------------------------------------------------------ variants
def invalid_variants(kind: str, value: str) -> list[tuple[str, str, str]]:
    """Single-fault variants of a (valid) value: [(variant, fault, expect)].

    expect "invalid": a validator must reject it. expect "clarify": a notation variant (spaces,
    case, grouping) that a system may legitimately normalise; the requirement must decide.
    kind: tckn | vkn | iban | tr_iban (tr_iban uses the IBAN variants).
    """
    if kind not in KINDS:
        raise ValueError(f"unknown kind {kind!r} (use {', '.join(KINDS)})")
    s = re.sub(r"\s+", "", str(value))
    if not s:
        return []

    def bump(c: str) -> str:
        return str((int(c) + 1) % 10) if c.isdigit() else ("B" if c.upper() == "A" else "A")

    if kind in ("tckn", "vkn"):
        out = [(s[:-1] + bump(s[-1]), "last check digit changed", "invalid"),
               (s[:-1], "one digit short", "invalid"), (s + "0", "one digit long", "invalid"),
               (s[:-2] + "a" + s[-1], "non-numeric character", "invalid"), ("", "empty", "invalid"),
               (" " + s + " ", "leading/trailing spaces (should be trimmed or rejected - clarify)", "clarify")]
        if kind == "tckn" and len(s) == 11:
            out += [("0" + s[1:], "first digit 0", "invalid"),
                    (s[:9] + bump(s[9]) + s[10], "10th digit changed", "invalid")]
        return out
    return [(s[:4] + s[4:-1] + bump(s[-1]), "last digit changed (mod-97 fails)", "invalid"),
            (s[:2] + bump(s[2]) + s[3:], "check digit changed", "invalid"),
            (s[:-1], "one character short", "invalid"), (s + "0", "one character long", "invalid"),
            (s.lower(), "lower case (accept after normalising? clarify)", "clarify"),
            (" ".join(s[i:i + 4] for i in range(0, len(s), 4)), "grouped with spaces (usually accepted)", "clarify"),
            ("DE" + s[2:], "wrong country code", "invalid")]


# ---------------------------------------------------------------- international (0.7.2)
# Payment card numbers: only PUBLISHED TEST numbers (Visa/Mastercard/Amex test PANs listed by payment
# providers for sandbox use, e.g. https://docs.stripe.com/testing). They pass Luhn but are never real cards.
TEST_CARDS = {
    "visa": ["4111111111111111", "4242424242424242", "4012888888881881"],
    "mastercard": ["5555555555554444", "5105105105105100", "2223003122003222"],
    "amex": ["378282246310005", "371449635398431"],
}


def luhn_ok(value) -> bool:
    """Luhn (mod 10) check used by payment card numbers and IMEIs. Spaces and dashes are ignored."""
    d = re.sub(r"[\s-]", "", str(value))
    if not d.isdigit() or len(d) < 2:
        return False
    total = 0
    for i, ch in enumerate(reversed(d)):
        n = int(ch)
        if i % 2:
            n = n * 2 - 9 if n > 4 else n * 2
        total += n
    return total % 10 == 0


# BBAN layouts (n = digit, a = upper-case letter) for synthetic IBANs. Only mod-97 is guaranteed;
# national check digits inside the BBAN (e.g. the French RIB key) are not computed.
IBAN_BBAN = {"TR": "nnnnn0nnnnnnnnnnnnnnnn", "DE": "nnnnnnnnnnnnnnnnnn", "GB": "aaaannnnnnnnnnnnnn",
             "FR": "nnnnnnnnnnnnnnnnnnnnnnn", "NL": "aaaannnnnnnnnn", "ES": "nnnnnnnnnnnnnnnnnnnn",
             "IT": "annnnnnnnnnnnnnnnnnnnnnn"}


def gen_iban(rng, country: str = "TR") -> str:
    """A mod-97-valid synthetic IBAN for one of IBAN_BBAN's countries. Can coincide with a real account."""
    layout = IBAN_BBAN[country.upper()]
    bban = "".join(str(rng.randint(0, 9)) if c == "n" else (chr(rng.randint(65, 90)) if c == "a" else c) for c in layout)
    return country.upper() + iban_check_digits(country.upper(), bban) + bban
