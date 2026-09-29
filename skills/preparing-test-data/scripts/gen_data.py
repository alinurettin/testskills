#!/usr/bin/env python3
"""Generate deterministic, synthetic test data (CSV or JSON) from a small JSON schema.

Synthetic data is the default choice for test environments: it contains no personal data,
it can be regenerated at any time from (schema, seed), and it can deliberately contain the
awkward values that production data rarely has in the right place.

Schema (single table):
  {"fields": [{"name": "id", "type": "seq", "prefix": "CUST-", "width": 4},
              {"name": "ad", "type": "first_name"},
              {"name": "email", "type": "email", "from": ["ad", "soyad"]}],
   "unique": ["email"], "edge_fraction": 0.1}
Schema (several related tables, written as <name>.<format> into the --out directory):
  {"tables": [{"name": "customers", "rows": 50, "fields": [...]},
              {"name": "accounts", "rows": 80, "fields": [{"name": "customer_id", "type": "ref",
                                                            "source": "customers:id"}, ...]}]}

Field types and options (every field also takes: null_p, allow_empty, edge, description):
  seq          prefix ("{run}" is replaced by --run-tag), start, width, step
  first_name, last_name   pool (tr|en|mix; default = --lang), max_len
  full_name    pool, from ([first, last] field names), max_len
  email        from (field names), domain (example.com|example.test), unique_suffix (true)
  phone_tr     format (e164|display|national)       +90 5xx mobile numbers
  tckn         -    valid checksum, never starts with 0
  vkn          -    valid 10-digit tax number checksum
  iban_tr      bank_codes (5-digit strings), format (compact|display)
  int          min, max
  decimal      min, max, scale (2), decimal_sep ("." or ",")
  date         min, max (YYYY-MM-DD), format (strftime, default %Y-%m-%d; tr: %d.%m.%Y)
  datetime     min, max (YYYY-MM-DDTHH:MM:SS), format
  enum         values, weights
  bool         p (probability of true, 0.5)
  text         min_len (1), max_len (20), charset (alpha|alnum|digits|turkish|words)
  city_tr      -    one of the 81 provinces
  postcode_tr  city_field (keeps the 2-digit province prefix consistent with that city)
  uuid         -    version-4 layout, generated from the seed
  ref          source ("table:column" from this schema, or "file.csv:column" / "file.json:column"),
               distinct (true = every parent used at most once)
"unique": field names or lists of field names (composite keys); rows are regenerated on collision.
"edge": true on a field mixes boundary/awkward values into round(edge_fraction x rows) rows. Each
such row gets one edge value in one field (single-fault rows), cycling through the edge fields.
Edge values: min/max numbers and dates, 29 Feb, max-length and min-length strings, empty strings
(only with allow_empty), Turkish characters and i/I casing traps, leading/trailing spaces,
alternate phone/IBAN notations, leading-zero postcodes. --mark-edges adds an _edge column.

SAFETY: TCKN, VKN, IBAN and phone values are valid by algorithm only. They can coincide with
real people, companies, accounts or subscribers (Turkey has no reserved fictional ranges), so
keep generated data inside test systems and never send SMS, calls or payments to it. E-mails
always use the reserved example.com / example.test domains (RFC 2606).

Usage:
  python gen_data.py --schema customers.json --rows 200 --seed 42 --out data/customers.csv
  python gen_data.py --schema assets/schema-example.json --seed 7 --lang tr --out data/   (multi-table)
  python gen_data.py --schema s.json --rows 50 --seed 1 --format json --out s.json --mark-edges
  python gen_data.py --schema s.json --validate-only
Exit codes: 0 ok, 1 schema invalid / generation impossible, 2 usage error.
"""
from __future__ import annotations

import argparse
import csv
import difflib
import json
import random
import re
import sys
import uuid as uuidlib
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path

# ----------------------------------------------------------------------------------------------
# Checksums (importable; tests validate them against independent implementations)
# ----------------------------------------------------------------------------------------------


def tckn_check_digits(first9: str) -> str:
    """The 10th and 11th digit of a T.C. kimlik no for the given first nine digits."""
    d = [int(c) for c in first9]
    d10 = ((d[0] + d[2] + d[4] + d[6] + d[8]) * 7 - (d[1] + d[3] + d[5] + d[7])) % 10
    d11 = (sum(d) + d10) % 10
    return f"{d10}{d11}"


def is_valid_tckn(value: str) -> bool:
    s = str(value).strip()
    return len(s) == 11 and s.isascii() and s.isdigit() and s[0] != "0" and tckn_check_digits(s[:9]) == s[9:]


def vkn_check_digit(first9: str) -> str:
    """The 10th digit of a Turkish vergi kimlik no (VKN) for the given first nine digits."""
    total = 0
    for i, c in enumerate(first9):
        tmp = (int(c) + 9 - i) % 10
        if tmp == 9:
            total += 9
        elif tmp:
            total += (tmp * 2 ** (9 - i)) % 9
    return str((10 - total % 10) % 10)


def is_valid_vkn(value: str) -> bool:
    s = str(value).strip()
    return len(s) == 10 and s.isascii() and s.isdigit() and vkn_check_digit(s[:9]) == s[9]


def iban_check_digits(country: str, bban: str) -> str:
    """ISO 13616 / ISO 7064 mod 97-10 check digits."""
    num = "".join(str(int(ch, 36)) for ch in (bban + country + "00").upper())
    return f"{98 - int(num) % 97:02d}"


def is_valid_iban(value: str) -> bool:
    s = re.sub(r"\s+", "", str(value)).upper()
    if not re.fullmatch(r"[A-Z]{2}\d{2}[A-Z0-9]{8,30}", s):
        return False
    if s.startswith("TR") and not re.fullmatch(r"TR\d{24}", s):
        return False
    return int("".join(str(int(ch, 36)) for ch in s[4:] + s[:4])) % 97 == 1


# ----------------------------------------------------------------------------------------------
# Built-in fictional value pools
# ----------------------------------------------------------------------------------------------
FIRST_TR = ["Ayşe", "Fatma", "Zeynep", "Elif", "Emine", "Hatice", "Merve", "Büşra", "Gökçe", "Işıl", "İpek",
            "Özge", "Şule", "Ümran", "Öykü", "Tuğçe", "Çağla", "Gülşen", "Ilgın", "Su", "Ahmet", "Mehmet",
            "Mustafa", "Ali", "Hüseyin", "Emre", "Burak", "Çağrı", "Barış", "Buğra", "Doğan", "İlker",
            "Ömer", "Şükrü", "Ümit", "Oğuz", "Gökhan", "Kerem", "Yiğit", "Tolga"]
LAST_TR = ["Yılmaz", "Kaya", "Demir", "Şahin", "Çelik", "Yıldız", "Yıldırım", "Öztürk", "Aydın", "Özdemir",
           "Arslan", "Doğan", "Kılıç", "Aslan", "Çetin", "Kara", "Koç", "Kurt", "Özkan", "Şimşek", "Polat",
           "Güneş", "Akın", "Uçar", "İnce", "Işık", "Ünal", "Çakır", "Bulut", "Tekin", "Ekinci", "Gündoğdu",
           "Erbaş", "Karagöz", "Sönmez", "Tuncer", "Bozkurt", "Ateş", "Çınar", "Özer"]
FIRST_EN = ["Emma", "Olivia", "Ava", "Sophia", "Mia", "Amelia", "Grace", "Chloe", "Lucy", "Ella", "Liam", "Noah",
            "Oliver", "James", "Lucas", "Henry", "Jack", "Leo", "Samuel", "Daniel", "Ethan", "Owen", "Isaac",
            "Nora", "Hannah", "Ruby", "Zoe", "Adam", "Max", "Theo"]
LAST_EN = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Miller", "Davis", "Wilson", "Taylor", "Clark",
           "Walker", "Hall", "Young", "King", "Wright", "Scott", "Green", "Baker", "Adams", "Nelson", "Carter",
           "Mitchell", "Turner", "Parker", "Evans", "Collins", "Stewart", "Morris", "Cooper", "Reed"]
EDGE_FIRST = ["Işıl", "İlkay", "Çağrı", "Gökçe", "Şükrü", "Ümran", "Öykü", "Ilgın", "IŞIL", "İPEK", "Su", "Ali Rıza",
              "Ayşe Gül Nur", "Zoë", "Chloé"]
EDGE_LAST = ["Işıkoğlu", "Çağlayan", "Şenyüz", "Öztürk", "Ünlü", "İnceoğlu", "IŞIK", "Öz", "Yılmaz-Öztürk",
             "O'Neill", "Karamustafaoğulları"]
CITIES_TR = ["Adana", "Adıyaman", "Afyonkarahisar", "Ağrı", "Amasya", "Ankara", "Antalya", "Artvin", "Aydın",
             "Balıkesir", "Bilecik", "Bingöl", "Bitlis", "Bolu", "Burdur", "Bursa", "Çanakkale", "Çankırı", "Çorum",
             "Denizli", "Diyarbakır", "Edirne", "Elazığ", "Erzincan", "Erzurum", "Eskişehir", "Gaziantep", "Giresun",
             "Gümüşhane", "Hakkari", "Hatay", "Isparta", "Mersin", "İstanbul", "İzmir", "Kars", "Kastamonu",
             "Kayseri", "Kırklareli", "Kırşehir", "Kocaeli", "Konya", "Kütahya", "Malatya", "Manisa",
             "Kahramanmaraş", "Mardin", "Muğla", "Muş", "Nevşehir", "Niğde", "Ordu", "Rize", "Sakarya", "Samsun",
             "Siirt", "Sinop", "Sivas", "Tekirdağ", "Tokat", "Trabzon", "Tunceli", "Şanlıurfa", "Uşak", "Van",
             "Yozgat", "Zonguldak", "Aksaray", "Bayburt", "Karaman", "Kırıkkale", "Batman", "Şırnak", "Bartın",
             "Ardahan", "Iğdır", "Yalova", "Karabük", "Kilis", "Osmaniye", "Düzce"]  # index + 1 = plate code
EDGE_CITIES = ["İstanbul", "İzmir", "Iğdır", "Şanlıurfa", "Çanakkale", "Kırıkkale", "Afyonkarahisar", "Ağrı",
               "Uşak", "Muş"]
MOBILE_PREFIXES = ["501", "505", "506", "507"] + [f"53{i}" for i in range(10)] + [f"54{i}" for i in range(10)] \
    + [f"55{i}" for i in range(1, 10)]
BANK_CODES = ["00010", "00012", "00015", "00046", "00062", "00064", "00067"]
WORDS = {"tr": ["kalem", "masa", "deniz", "güneş", "çiçek", "kitap", "yol", "şehir", "ağaç", "ışık", "göl", "dağ",
                "öğrenci", "üzüm", "çay", "kahve", "pencere", "İzmir", "ılık", "söğüt"],
         "en": ["alpha", "river", "stone", "paper", "green", "light", "table", "cloud", "music", "ocean", "maple",
                "silver", "north", "window", "garden", "bridge"]}
CHARSETS = {"alpha": "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ",
            "alnum": "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
            "digits": "0123456789",
            "turkish": "abcçdefgğhıijklmnoöprsştuüvyzABCÇDEFGĞHIİJKLMNOÖPRSŞTUÜVYZ"}
FOLD = str.maketrans({"ç": "c", "Ç": "c", "ğ": "g", "Ğ": "g", "ı": "i", "İ": "i", "ö": "o", "Ö": "o", "ş": "s",
                      "Ş": "s", "ü": "u", "Ü": "u", "â": "a", "Â": "a", "î": "i", "Î": "i", "û": "u", "Û": "u",
                      "ë": "e", "é": "e", "è": "e", "à": "a", "'": "", "’": ""})
EMAIL_DOMAINS = ("example.com", "example.test")

COMMON = {"name", "type", "null_p", "allow_empty", "edge", "description"}
TYPES = {
    "seq": {"prefix", "start", "width", "step"},
    "first_name": {"pool", "max_len"}, "last_name": {"pool", "max_len"},
    "full_name": {"pool", "from", "max_len"},
    "email": {"from", "domain", "unique_suffix"},
    "phone_tr": {"format"}, "tckn": set(), "vkn": set(), "iban_tr": {"bank_codes", "format"},
    "int": {"min", "max"}, "decimal": {"min", "max", "scale", "decimal_sep"},
    "date": {"min", "max", "format"}, "datetime": {"min", "max", "format"},
    "enum": {"values", "weights"}, "bool": {"p"},
    "text": {"min_len", "max_len", "charset"},
    "city_tr": set(), "postcode_tr": {"city_field"}, "uuid": set(),
    "ref": {"source", "distinct"},
}
NO_EDGE = {"seq", "bool", "ref"}

MSG = {"en": {"done": "Generated {rows} rows -> {out} (seed {seed}, edge rows {edge})",
              "valid": "Schema is valid: {tables} table(s), {fields} field(s)",
              "safety": "Note: TCKN/VKN/IBAN/phone values are valid by algorithm only; keep them in test systems."},
       "tr": {"done": "{rows} satır üretildi -> {out} (seed {seed}, uç değerli satır {edge})",
              "valid": "Şema geçerli: {tables} tablo, {fields} alan",
              "safety": "Not: TCKN/VKN/IBAN/telefon değerleri yalnızca algoritmik olarak geçerlidir; test sistemlerinde tutun."}}


class SchemaError(Exception):
    pass


def ascii_fold(text: str) -> str:
    """'Ayşe Gül' -> 'ayse.gul' (for e-mail local parts)."""
    s = str(text).translate(FOLD).lower()
    return re.sub(r"[^a-z0-9]+", ".", s).strip(".")


# ----------------------------------------------------------------------------------------------
# Schema validation
# ----------------------------------------------------------------------------------------------


def _hint(word: str, choices) -> str:
    m = difflib.get_close_matches(word, list(choices), n=1)
    return f" - did you mean '{m[0]}'?" if m else ""


def _parse_date(v, what):
    try:
        return date.fromisoformat(str(v))
    except ValueError:
        raise SchemaError(f"{what}: '{v}' is not an ISO date (YYYY-MM-DD)")


def _parse_dt(v, what):
    try:
        return datetime.fromisoformat(str(v))
    except ValueError:
        raise SchemaError(f"{what}: '{v}' is not an ISO datetime (YYYY-MM-DDTHH:MM:SS)")


def _dec(v, what):
    try:
        return Decimal(str(v))
    except InvalidOperation:
        raise SchemaError(f"{what}: '{v}' is not a number")


def normalize_schema(schema: dict, default_name: str = "data") -> list[dict]:
    if not isinstance(schema, dict):
        raise SchemaError("schema must be a JSON object with 'fields' or 'tables'")
    if "tables" in schema:
        tables = schema["tables"]
        if not isinstance(tables, list) or not tables:
            raise SchemaError("'tables' must be a non-empty list of {name, rows, fields}")
    elif "fields" in schema:
        tables = [dict(schema, name=schema.get("name", default_name))]
    else:
        raise SchemaError("schema needs 'fields' (one table) or 'tables' (several related tables)")
    return tables


def validate_schema(schema: dict, default_name: str = "data") -> list[str]:
    """Return a list of human-readable problems (empty = valid)."""
    try:
        tables = normalize_schema(schema, default_name)
    except SchemaError as e:
        return [str(e)]
    errors: list[str] = []
    ef = schema.get("edge_fraction", 0.1)
    if not isinstance(ef, (int, float)) or not 0 <= ef <= 1:
        errors.append(f"edge_fraction must be between 0 and 1 (got {ef!r})")
    seen_tables: list[str] = []
    for ti, t in enumerate(tables):
        tname = t.get("name") or f"tables[{ti}]"
        if not isinstance(t.get("fields"), list) or not t["fields"]:
            errors.append(f"{tname}: 'fields' must be a non-empty list")
            continue
        if "rows" in t and (not isinstance(t["rows"], int) or t["rows"] < 0):
            errors.append(f"{tname}: 'rows' must be a non-negative integer")
        names: list[str] = []
        for fi, f in enumerate(t["fields"]):
            where = f"{tname}.fields[{fi}]"
            if not isinstance(f, dict) or not f.get("name"):
                errors.append(f"{where}: every field needs a 'name'")
                continue
            name, typ = f["name"], f.get("type")
            where = f"{tname}.{name}"
            if name in names:
                errors.append(f"{where}: duplicate field name")
            if typ not in TYPES:
                errors.append(f"{where}: unknown type '{typ}'{_hint(str(typ), TYPES)} "
                              f"(known: {', '.join(sorted(TYPES))})")
                names.append(name)
                continue
            allowed = COMMON | TYPES[typ]
            for k in f:
                if k not in allowed:
                    errors.append(f"{where}: option '{k}' is not valid for type {typ}{_hint(k, allowed)}")
            try:
                _check_field(f, typ, where, names, seen_tables)
            except SchemaError as e:
                errors.append(str(e))
            if f.get("edge") and typ in NO_EDGE:
                why = " (it would break referential integrity)" if typ == "ref" else ""
                errors.append(f"{where}: 'edge' is not supported for type {typ}{why}")
            np_ = f.get("null_p", 0)
            if not isinstance(np_, (int, float)) or not 0 <= np_ <= 1:
                errors.append(f"{where}: null_p must be between 0 and 1")
            names.append(name)
        for u in t.get("unique", []):
            cols = [u] if isinstance(u, str) else u
            if not isinstance(cols, list) or not cols:
                errors.append(f"{tname}: 'unique' entries are field names or lists of field names")
                continue
            for c in cols:
                if c not in names:
                    errors.append(f"{tname}: unique field '{c}' is not defined{_hint(str(c), names)}")
        seen_tables.append(t.get("name", ""))
    return errors


def _check_field(f: dict, typ: str, where: str, earlier: list[str], tables: list[str]) -> None:
    def rng_check(lo, hi):
        if lo is not None and hi is not None and lo > hi:
            raise SchemaError(f"{where}: min ({f.get('min')}) is greater than max ({f.get('max')})")

    if typ == "int":
        for k in ("min", "max"):
            if k in f and not isinstance(f[k], int):
                raise SchemaError(f"{where}: '{k}' must be an integer")
        rng_check(f.get("min", 0), f.get("max", 1000))
    elif typ == "decimal":
        rng_check(_dec(f.get("min", 0), where), _dec(f.get("max", 1000), where))
        sc = f.get("scale", 2)
        if not isinstance(sc, int) or not 0 <= sc <= 10:
            raise SchemaError(f"{where}: 'scale' must be an integer 0-10")
        if f.get("decimal_sep", ".") not in (".", ","):
            raise SchemaError(f"{where}: decimal_sep must be '.' or ','")
    elif typ == "date":
        rng_check(_parse_date(f.get("min", "2000-01-01"), where), _parse_date(f.get("max", "2030-12-31"), where))
    elif typ == "datetime":
        rng_check(_parse_dt(f.get("min", "2020-01-01T00:00:00"), where),
                  _parse_dt(f.get("max", "2030-12-31T23:59:59"), where))
    elif typ == "enum":
        vals = f.get("values")
        if not isinstance(vals, list) or not vals:
            raise SchemaError(f"{where}: enum needs a non-empty 'values' list")
        w = f.get("weights")
        if w is not None and (not isinstance(w, list) or len(w) != len(vals)
                              or any(not isinstance(x, (int, float)) or x < 0 for x in w) or not sum(w)):
            raise SchemaError(f"{where}: 'weights' must be non-negative numbers, one per value")
    elif typ == "bool":
        p = f.get("p", 0.5)
        if not isinstance(p, (int, float)) or not 0 <= p <= 1:
            raise SchemaError(f"{where}: p must be between 0 and 1")
    elif typ == "text":
        lo, hi = f.get("min_len", 1), f.get("max_len", 20)
        if not (isinstance(lo, int) and isinstance(hi, int) and 0 <= lo <= hi):
            raise SchemaError(f"{where}: need 0 <= min_len <= max_len (got {lo}, {hi})")
        cs = f.get("charset", "alpha")
        if cs not in CHARSETS and cs != "words":
            raise SchemaError(f"{where}: unknown charset '{cs}'{_hint(cs, list(CHARSETS) + ['words'])}")
    elif typ in ("first_name", "last_name", "full_name"):
        if f.get("pool", "tr") not in ("tr", "en", "mix"):
            raise SchemaError(f"{where}: pool must be tr, en or mix")
        if "max_len" in f and (not isinstance(f["max_len"], int) or f["max_len"] < 2):
            raise SchemaError(f"{where}: max_len must be an integer >= 2")
    elif typ == "email":
        if f.get("domain", "example.com") not in EMAIL_DOMAINS:
            raise SchemaError(f"{where}: domain must be one of {', '.join(EMAIL_DOMAINS)} "
                              "(reserved domains, so no real mailbox can ever receive test mail)")
    elif typ == "phone_tr":
        if f.get("format", "e164") not in ("e164", "display", "national"):
            raise SchemaError(f"{where}: format must be e164, display or national")
    elif typ == "iban_tr":
        codes = f.get("bank_codes", BANK_CODES)
        if not isinstance(codes, list) or not codes or any(not re.fullmatch(r"\d{5}", str(c)) for c in codes):
            raise SchemaError(f"{where}: bank_codes must be a list of 5-digit strings")
        if f.get("format", "compact") not in ("compact", "display"):
            raise SchemaError(f"{where}: format must be compact or display")
    elif typ == "seq":
        for k in ("start", "width", "step"):
            if k in f and (not isinstance(f[k], int) or (k == "step" and f[k] == 0)):
                raise SchemaError(f"{where}: '{k}' must be a (non-zero) integer")
    elif typ == "ref":
        src = f.get("source")
        if not isinstance(src, str) or ":" not in src:
            raise SchemaError(f"{where}: ref needs 'source' like 'customers:id' or 'customers.csv:id'")
    if typ in ("full_name", "email") and "from" in f:
        src = f["from"] if isinstance(f["from"], list) else [f["from"]]
        for s in src:
            if s not in earlier:
                raise SchemaError(f"{where}: 'from' field '{s}' must be defined before this field")
    if typ == "postcode_tr" and "city_field" in f and f["city_field"] not in earlier:
        raise SchemaError(f"{where}: city_field '{f['city_field']}' must be defined before this field")


# ----------------------------------------------------------------------------------------------
# Value generators
# ----------------------------------------------------------------------------------------------


def _pool(f, ctx, kind):
    pool = f.get("pool", ctx["lang"])
    if pool == "mix":
        pool = ctx["rng"].choice(["tr", "en"])
    if kind == "first":
        return FIRST_TR if pool == "tr" else FIRST_EN
    return LAST_TR if pool == "tr" else LAST_EN


def _fit(s: str, max_len: int | None) -> str:
    return s if not max_len or len(s) <= max_len else s[:max_len].rstrip()


def gen_tckn(rng) -> str:
    first9 = str(rng.randint(1, 9)) + "".join(str(rng.randint(0, 9)) for _ in range(8))
    return first9 + tckn_check_digits(first9)


def gen_vkn(rng) -> str:
    first9 = "".join(str(rng.randint(0, 9)) for _ in range(9))
    return first9 + vkn_check_digit(first9)


def gen_iban_tr(rng, codes=None) -> str:
    bban = str(rng.choice(codes or BANK_CODES)) + "0" + "".join(str(rng.randint(0, 9)) for _ in range(16))
    return "TR" + iban_check_digits("TR", bban) + bban


def iban_display(iban: str) -> str:
    return " ".join(iban[i:i + 4] for i in range(0, len(iban), 4))


def gen_phone_digits(rng) -> str:
    """Ten national digits, e.g. 5321234567."""
    return rng.choice(MOBILE_PREFIXES) + "".join(str(rng.randint(0, 9)) for _ in range(7))


def phone_format(d: str, fmt: str) -> str:
    if fmt == "display":
        return f"+90 {d[:3]} {d[3:6]} {d[6:8]} {d[8:]}"
    if fmt == "national":
        return f"0{d[:3]} {d[3:6]} {d[6:8]} {d[8:]}"
    return "+90" + d


def _rand_text(rng, charset, n, lang):
    if charset == "words":
        out = ""
        while len(out) < n:
            out = (out + " " + rng.choice(WORDS[lang])).lstrip()
        s = out[:n]
        return s[:-1] + "a" if s.endswith(" ") else s
    return "".join(rng.choice(CHARSETS[charset]) for _ in range(n))


def gen_value(f: dict, ctx: dict):
    rng, typ, row = ctx["rng"], f["type"], ctx["row"]
    if typ == "seq":
        n = f.get("start", 1) + ctx["index"] * f.get("step", 1)
        prefix = str(f.get("prefix", "")).replace("{run}", ctx["run_tag"])
        return f"{prefix}{n:0{f.get('width', 0)}d}" if (prefix or f.get("width")) else n
    if typ == "first_name":
        return _fit(rng.choice(_pool(f, ctx, "first")), f.get("max_len"))
    if typ == "last_name":
        return _fit(rng.choice(_pool(f, ctx, "last")), f.get("max_len"))
    if typ == "full_name":
        if "from" in f:
            parts = [str(row.get(x) or "") for x in f["from"]]
            return _fit(" ".join(p for p in parts if p), f.get("max_len"))
        return _fit(f"{rng.choice(_pool(f, ctx, 'first'))} {rng.choice(_pool(f, ctx, 'last'))}", f.get("max_len"))
    if typ == "email":
        src = f.get("from")
        src = src if isinstance(src, list) else ([src] if src else [])
        parts = [ascii_fold(row.get(x) or "") for x in src]
        parts = [p for p in parts if p] or [ascii_fold(rng.choice(_pool(f, ctx, "first"))),
                                           ascii_fold(rng.choice(_pool(f, ctx, "last")))]
        suffix = str(ctx["index"] + 1) if f.get("unique_suffix", True) else ""
        local = ".".join(parts)[:64 - len(suffix)].strip(".") + suffix
        return f"{local}@{f.get('domain', 'example.com')}"
    if typ == "phone_tr":
        return phone_format(gen_phone_digits(rng), f.get("format", "e164"))
    if typ == "tckn":
        return gen_tckn(rng)
    if typ == "vkn":
        return gen_vkn(rng)
    if typ == "iban_tr":
        iban = gen_iban_tr(rng, f.get("bank_codes"))
        return iban_display(iban) if f.get("format") == "display" else iban
    if typ == "int":
        return rng.randint(f.get("min", 0), f.get("max", 1000))
    if typ == "decimal":
        sc = f.get("scale", 2)
        q = Decimal(10) ** sc
        lo, hi = int(Decimal(str(f.get("min", 0))) * q), int(Decimal(str(f.get("max", 1000))) * q)
        return _fmt_dec(Decimal(rng.randint(lo, hi)) / q, f)
    if typ == "date":
        lo, hi = date.fromisoformat(str(f.get("min", "2000-01-01"))), date.fromisoformat(str(f.get("max", "2030-12-31")))
        return (lo + timedelta(days=rng.randint(0, (hi - lo).days))).strftime(f.get("format", "%Y-%m-%d"))
    if typ == "datetime":
        lo = datetime.fromisoformat(str(f.get("min", "2020-01-01T00:00:00")))
        hi = datetime.fromisoformat(str(f.get("max", "2030-12-31T23:59:59")))
        v = lo + timedelta(seconds=rng.randint(0, int((hi - lo).total_seconds())))
        return v.strftime(f.get("format", "%Y-%m-%dT%H:%M:%S"))
    if typ == "enum":
        return rng.choices(f["values"], weights=f.get("weights"))[0]
    if typ == "bool":
        return rng.random() < f.get("p", 0.5)
    if typ == "text":
        return _rand_text(rng, f.get("charset", "alpha"), rng.randint(f.get("min_len", 1), f.get("max_len", 20)),
                          ctx["lang"])
    if typ == "city_tr":
        return rng.choice(CITIES_TR)
    if typ == "postcode_tr":
        plate = _plate_for(row.get(f["city_field"]) if "city_field" in f else None, rng)
        return f"{plate:02d}{rng.randint(0, 999):03d}"
    if typ == "uuid":
        return str(uuidlib.UUID(int=rng.getrandbits(128), version=4))
    if typ == "ref":
        return ctx["refs"][f["name"]](rng)
    raise SchemaError(f"unsupported type {typ}")


def _plate_for(city, rng) -> int:
    if city in CITIES_TR:
        return CITIES_TR.index(city) + 1
    return rng.randint(1, 81)


def _fmt_dec(v: Decimal, f: dict) -> str:
    s = f"{v:.{f.get('scale', 2)}f}"
    return s.replace(".", ",") if f.get("decimal_sep") == "," else s


def edge_value(f: dict, ctx: dict):
    """A boundary or awkward-but-plausible value for the field (None = no candidate)."""
    rng, typ = ctx["rng"], f["type"]
    empty_ok = f.get("allow_empty") or f.get("null_p", 0) > 0
    cands: list = []
    if typ in ("first_name", "last_name", "full_name"):
        base = EDGE_FIRST if typ == "first_name" else EDGE_LAST
        if typ == "full_name":
            base = [f"{a} {b}" for a, b in zip(EDGE_FIRST, reversed(EDGE_LAST))]
        normal = str(gen_value(f, ctx))
        cands = list(base) + [f" {normal} ", f"{normal} "]
        ml = f.get("max_len")
        if ml:
            longest = ("Karamustafaoğulları Işıkoğlu Çağlayan " * 4)[:ml].rstrip()
            cands.append(longest + "ü" * (ml - len(longest)))
            cands = [c for c in cands if len(c) <= ml]
        else:
            cands.append("Ayşegül Nur Hümeyra Karamustafaoğulları")
    elif typ == "email":
        normal = gen_value(f, ctx)
        local, dom = normal.split("@")
        cands = [f"{local}+qa@{dom}", ".".join(p.capitalize() for p in local.split(".")) + f"@{dom}",
                 f"{local.upper()}@{dom}", f"{local.replace('.', '_')}-x@{dom}",
                 f"{(local + 'x' * 64)[:64]}@{dom}"]
    elif typ == "phone_tr":
        d = gen_phone_digits(rng)
        cands = [phone_format(d, "display"), phone_format(d, "national"), "0" + d, "90" + d, "+90" + d,
                 f"+90 ({d[:3]}) {d[3:6]}-{d[6:8]}-{d[8:]}"]
    elif typ == "tckn":
        cands = ["100000000" + tckn_check_digits("100000000"), "999999999" + tckn_check_digits("999999999")]
    elif typ == "vkn":
        cands = ["000000000" + vkn_check_digit("000000000"), "999999999" + vkn_check_digit("999999999"),
                 (lambda s: s + vkn_check_digit(s))("00" + "".join(str(rng.randint(0, 9)) for _ in range(7)))]
    elif typ == "iban_tr":
        iban = gen_iban_tr(rng, f.get("bank_codes"))
        cands = [iban if f.get("format") == "display" else iban_display(iban)]  # the other notation
    elif typ == "int":
        lo, hi = f.get("min", 0), f.get("max", 1000)
        cands = sorted({lo, min(lo + 1, hi), max(hi - 1, lo), hi} | ({0} if lo <= 0 <= hi else set()))
    elif typ == "decimal":
        sc = f.get("scale", 2)
        step = Decimal(1).scaleb(-sc)
        lo, hi = Decimal(str(f.get("min", 0))), Decimal(str(f.get("max", 1000)))
        vals = {lo, min(lo + step, hi), max(hi - step, lo), hi} | ({Decimal(0)} if lo <= 0 <= hi else set())
        cands = [_fmt_dec(v, f) for v in sorted(vals)]
    elif typ == "date":
        lo, hi = date.fromisoformat(str(f.get("min", "2000-01-01"))), date.fromisoformat(str(f.get("max", "2030-12-31")))
        vals = {lo, hi}
        for y in range(lo.year, hi.year + 1):
            if y % 4 == 0 and (y % 100 != 0 or y % 400 == 0) and lo <= date(y, 2, 29) <= hi:
                vals.add(date(y, 2, 29))
                break
        for y in range(lo.year, hi.year + 1):
            if lo <= date(y, 12, 31) <= hi:
                vals.add(date(y, 12, 31))
                break
        cands = [d.strftime(f.get("format", "%Y-%m-%d")) for d in sorted(vals)]
    elif typ == "datetime":
        lo = datetime.fromisoformat(str(f.get("min", "2020-01-01T00:00:00")))
        hi = datetime.fromisoformat(str(f.get("max", "2030-12-31T23:59:59")))
        vals = {lo, hi}
        day = lo.date() + timedelta(days=1)
        for v in (datetime(day.year, day.month, day.day), datetime(day.year, day.month, day.day, 23, 59, 59)):
            if lo <= v <= hi:
                vals.add(v)
        cands = [v.strftime(f.get("format", "%Y-%m-%dT%H:%M:%S")) for v in sorted(vals)]
    elif typ == "enum":
        vals, w = f["values"], f.get("weights")
        if w:
            m = min(w)
            cands = [v for v, x in zip(vals, w) if x == m]
        else:
            cands = [vals[0], vals[-1]]
    elif typ == "text":
        lo, hi, cs = f.get("min_len", 1), f.get("max_len", 20), f.get("charset", "alpha")
        cands = [_rand_text(rng, cs, hi, ctx["lang"])]
        if lo > 0:
            cands.append(_rand_text(rng, cs, lo, ctx["lang"]))
        if cs == "digits":
            if hi >= 2:
                cands.append(("0" * hi)[:max(lo, 2) - 1] + "1")
        else:
            for special in ("İıŞşĞğÜüÖöÇç", "IŞIK ışık İPEK", "😀 çay", "O'Neil \"x\""):
                s = special[:hi]
                if len(s) >= lo:
                    cands.append(s)
            if hi >= 3:
                core = _rand_text(rng, cs, max(1, min(hi - 2, max(lo - 2, 3))), ctx["lang"])
                cands.append(f" {core} ")
    elif typ == "city_tr":
        cands = EDGE_CITIES
    elif typ == "postcode_tr":
        if "city_field" in f and ctx["row"].get(f["city_field"]) in CITIES_TR:
            p = _plate_for(ctx["row"][f["city_field"]], rng)
            cands = [f"{p:02d}000", f"{p:02d}999"]
        else:
            cands = ["01000", f"0{rng.randint(1, 9)}{rng.randint(0, 999):03d}", "81999"]
    elif typ == "uuid":
        cands = [str(uuidlib.UUID(int=rng.getrandbits(128), version=4)).upper()]
    if empty_ok and typ in ("first_name", "last_name", "full_name", "text", "email", "city_tr"):
        cands.append("")
    return rng.choice(cands) if cands else None


# ----------------------------------------------------------------------------------------------
# Tables
# ----------------------------------------------------------------------------------------------


def load_column(path: Path, column: str) -> list:
    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        rows = data.get("rows", []) if isinstance(data, dict) else data
        if rows and column not in rows[0]:
            raise SchemaError(f"{path}: column '{column}' not found{_hint(column, rows[0].keys())}")
        return [r[column] for r in rows if r.get(column) not in (None, "")]
    with path.open(encoding="utf-8-sig", newline="") as fh:
        sample = fh.read(4096)
        fh.seek(0)
        delim = ";" if sample.count(";") > sample.count(",") else ","
        reader = csv.DictReader(fh, delimiter=delim)
        if column not in (reader.fieldnames or []):
            raise SchemaError(f"{path}: column '{column}' not found{_hint(column, reader.fieldnames or [])}")
        return [r[column] for r in reader if r[column] != ""]


def _ref_picker(values: list, distinct: bool, rows: int, where: str):
    if not values:
        raise SchemaError(f"{where}: the referenced column has no values")
    if distinct:
        if rows > len(values):
            raise SchemaError(f"{where}: distinct ref needs at least {rows} parent values, found {len(values)}")
        state = {"order": None, "i": 0}

        def pick(rng):
            if state["order"] is None:
                state["order"] = rng.sample(values, len(values))
            v = state["order"][state["i"] % len(values)]
            state["i"] += 1
            return v
        return pick
    return lambda rng: rng.choice(values)


def generate_table(table: dict, rows: int, seed, lang: str = "en", edge_fraction: float = 0.1,
                   generated: dict | None = None, search_dirs: list[Path] | None = None,
                   run_tag: str = "", mark_edges: bool = False) -> tuple[list[str], list[dict], int]:
    """Generate one table. Returns (columns, rows, number_of_edge_rows)."""
    generated = generated if generated is not None else {}
    search_dirs = search_dirs or [Path.cwd()]
    tname = table.get("name", "data")
    rng = random.Random(f"{seed}:{tname}")
    fields = table["fields"]
    refs = {}
    for f in fields:
        if f["type"] != "ref":
            continue
        src, col = f["source"].rsplit(":", 1)
        where = f"{tname}.{f['name']}"
        if src in generated:
            gcols, grows = generated[src]
            if col not in gcols:
                raise SchemaError(f"{where}: table '{src}' has no column '{col}'{_hint(col, gcols)}")
            values = [r[col] for r in grows if r.get(col) not in (None, "")]
        else:
            path = next((d / src for d in search_dirs if (d / src).is_file()), None)
            if path is None:
                raise SchemaError(f"{where}: ref source '{src}' is neither an earlier table in this schema nor a "
                                  f"file (looked in: {', '.join(str(d) for d in search_dirs)})")
            values = load_column(path, col)
        refs[f["name"]] = _ref_picker(values, bool(f.get("distinct")), rows, where)
    edge_fields = [f for f in fields if f.get("edge")]
    n_edge = round(edge_fraction * rows) if edge_fields else 0
    edge_rows = {i: edge_fields[k % len(edge_fields)]["name"]
                 for k, i in enumerate(sorted(rng.sample(range(rows), n_edge)))} if n_edge else {}
    uniques = [([u] if isinstance(u, str) else list(u)) for u in table.get("unique", [])]
    seen = [set() for _ in uniques]
    out_rows, edge_count = [], 0
    for i in range(rows):
        target = edge_rows.get(i)
        for attempt in range(1000):
            row: dict = {}
            ctx = {"rng": rng, "row": row, "index": i, "lang": lang, "refs": refs, "run_tag": run_tag}
            used_edge = ""
            for f in fields:
                if f.get("null_p") and rng.random() < f["null_p"] and not (target == f["name"] and attempt < 20):
                    row[f["name"]] = None
                    continue
                v = None
                if target == f["name"] and attempt < 20:
                    v = edge_value(f, ctx)
                    used_edge = f["name"] if v is not None else ""
                row[f["name"]] = gen_value(f, ctx) if v is None else v
            keys = [tuple(row[c] for c in u) for u in uniques]
            if all(k not in s for k, s in zip(keys, seen)):
                break
        else:
            raise SchemaError(f"{tname}: could not make row {i + 1} unique on {uniques} after 1000 attempts - "
                              "the value domain is too small for the requested rows")
        for k, s in zip(keys, seen):
            s.add(k)
        edge_count += bool(used_edge)
        if mark_edges:
            row["_edge"] = used_edge
        out_rows.append(row)
    cols = [f["name"] for f in fields] + (["_edge"] if mark_edges else [])
    return cols, out_rows, edge_count


def write_rows(path: Path, cols: list[str], rows: list[dict], fmt: str, fields: list[dict],
               delimiter: str = ",", bom: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ftype = {f["name"]: f for f in fields}
    if fmt == "json":
        def conv(k, v):
            f = ftype.get(k, {})
            if f.get("type") == "decimal" and isinstance(v, str) and f.get("decimal_sep") != "," and v:
                try:
                    return float(v) if "." in v else int(v)
                except ValueError:
                    return v
            return v
        data = [{k: conv(k, r.get(k)) for k in cols} for r in rows]
        path.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
        return
    with path.open("w", encoding="utf-8-sig" if bom else "utf-8", newline="") as fh:
        w = csv.writer(fh, delimiter=delimiter, lineterminator="\n")
        w.writerow(cols)
        for r in rows:
            w.writerow(["" if r.get(c) is None else ("true" if r[c] is True else "false" if r[c] is False else r[c])
                        for c in cols])


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--schema", required=True, help="schema JSON (single table or 'tables')")
    ap.add_argument("--rows", type=int, help="rows per table (default: 'rows' in the schema)")
    ap.add_argument("--seed", default="1", help="seed; same schema + seed = same data (default 1)")
    ap.add_argument("--format", choices=["csv", "json"], help="default: from --out extension, else csv")
    ap.add_argument("--lang", choices=["tr", "en"], default="en", help="default name pool and messages")
    ap.add_argument("--out", help="output file (single table) or directory (multi-table)")
    ap.add_argument("--edge-fraction", type=float, dest="edge_fraction", help="override schema edge_fraction")
    ap.add_argument("--mark-edges", action="store_true", dest="mark_edges", help="add an _edge column")
    ap.add_argument("--run-tag", default="", dest="run_tag", help="replaces {run} in seq prefixes (per-run data)")
    ap.add_argument("--delimiter", default=",", help="CSV delimiter (use ';' for Turkish Excel with decimal comma)")
    ap.add_argument("--bom", action="store_true", help="write UTF-8 BOM so Excel shows Turkish characters")
    ap.add_argument("--validate-only", action="store_true", dest="validate_only")
    sys.stdout.reconfigure(encoding="utf-8")
    a = ap.parse_args()
    m = MSG[a.lang]
    sp = Path(a.schema)
    try:
        schema = json.loads(sp.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as e:
        print(f"error: cannot read schema {sp}: {e}", file=sys.stderr)
        return 2
    out = Path(a.out) if a.out else None
    default_name = "data"
    errors = validate_schema(schema, default_name)
    if errors:
        print(f"schema {sp.name}: {len(errors)} problem(s)", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1
    tables = normalize_schema(schema, default_name)
    if a.validate_only:
        print(m["valid"].format(tables=len(tables), fields=sum(len(t["fields"]) for t in tables)))
        return 0
    if out is None:
        print("error: --out is required", file=sys.stderr)
        return 2
    multi = "tables" in schema
    fmt = a.format or ("json" if out.suffix.lower() == ".json" else "csv")
    ef = a.edge_fraction if a.edge_fraction is not None else schema.get("edge_fraction", 0.1)
    if not 0 <= ef <= 1:
        print("error: --edge-fraction must be between 0 and 1", file=sys.stderr)
        return 2
    generated: dict = {}
    search = [Path.cwd(), sp.resolve().parent, (out if multi else out.parent).resolve()]
    for t in tables:
        rows = t.get("rows", a.rows) if multi else (a.rows if a.rows is not None else t.get("rows"))
        if rows is None:
            print(f"error: no row count for '{t['name']}' - pass --rows or set 'rows' in the schema", file=sys.stderr)
            return 2
        try:
            cols, data, n_edge = generate_table(t, rows, a.seed, a.lang, ef, generated, search, a.run_tag,
                                                a.mark_edges)
        except SchemaError as e:
            print(f"error: {e}", file=sys.stderr)
            return 1
        generated[t["name"]] = (cols, data)
        target = out / f"{t['name']}.{fmt}" if multi else out
        write_rows(target, cols, data, fmt, t["fields"], a.delimiter, a.bom)
        print(m["done"].format(rows=rows, out=target, seed=a.seed, edge=n_edge))
    if any(f.get("type") in ("tckn", "vkn", "iban_tr", "phone_tr") for t in tables for f in t["fields"]):
        print(m["safety"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
