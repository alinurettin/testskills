#!/usr/bin/env python3
"""Mask (pseudonymise) a CSV extract column by column, driven by a rules file.

Use this only when synthetic data cannot do the job AND the data owner / DPO has approved using
a production extract for testing. Masked data with hash/fake rules is PSEUDONYMISED, not
anonymous: whoever holds the secret (or enough context) can link it back, so under KVKK / GDPR
it is still personal data. Minimise first: drop every column the tests do not need.

Rules (JSON):
  {"default": "drop",
   "columns": {
     "musteri_no":   {"rule": "hash", "length": 16},             keyed HMAC-SHA256, same input -> same token
     "ad":           {"rule": "fake", "type": "first_name"},     deterministic synthetic replacement
     "email":        {"rule": "fake", "type": "email", "normalize": "lower"},
     "dogum_tarihi": {"rule": "generalize", "to": "year"},       or "year-month"
     "maas":         {"rule": "generalize", "bucket": 5000},     -> "[5000,10000)"
     "posta_kodu":   {"rule": "generalize", "to": "prefix", "keep": 2},
     "aciklama":     {"rule": "redact", "with": "***"},
     "adres":        "drop",
     "urun_kodu":    "keep"}}
  rule        drop | redact | hash | fake | generalize | keep
  hash        length (hex chars, 8-64, default 16), prefix, normalize
  fake        type: first_name | last_name | full_name | email | phone_tr | tckn | vkn | iban_tr | city_tr;
              pool (tr|en), normalize
  generalize  to: year | year-month (dates: YYYY-MM-DD, DD.MM.YYYY, DD/MM/YYYY, datetimes);
              bucket: width (numbers, "1.234,56" and "1,234.56" understood);
              to: prefix + keep: n (postcodes, other codes; "postcode" = prefix of 2)
  normalize   trim (default) | lower | digits | phone | none - applied before hash/fake so that
              " A@x.com" and "a@x.com" (lower) or "+90 532 111 22 33" and "05321112233" (phone)
              map to the same token when you want them to.
Empty values stay empty. Values that cannot be generalized are redacted and counted.

Hash and fake are keyed with a secret read from an environment variable (--secret-env, default
MASK_SECRET). There is no default secret: the script refuses to run without one, because an
unkeyed hash of a TCKN or phone number is reversible by brute force in minutes. Use the SAME
secret for every file of one extract so joins keep working, keep it out of the test environment,
and rotate it per extract when linkage across extracts is not needed.

Columns without a rule get --default (drop unless the rules file says otherwise). The report
warns about uncovered or kept columns whose header or content looks like personal data.

Usage:
  set MASK_SECRET=<random 32+ chars>      (PowerShell: $env:MASK_SECRET = "...")
  python mask_data.py --in extract.csv --rules rules.json --out masked.csv --report mask-report.md --lang tr
Exit codes: 0 ok, 1 warnings that need a decision (uncovered PII kept, rule for a missing column),
2 usage error (no secret, invalid rules, unreadable input).
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import hmac
import json
import os
import random
import re
import sys
from datetime import datetime
from decimal import ROUND_FLOOR, Decimal, InvalidOperation
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gen_data as gd  # noqa: E402
from tr_ids import gen_tckn, gen_tr_iban, gen_vkn, is_valid_iban, is_valid_tckn  # noqa: E402

RULES = {"drop", "redact", "hash", "fake", "generalize", "keep"}
FAKE_TYPES = {"first_name", "last_name", "full_name", "email", "phone_tr", "tckn", "vkn", "iban_tr", "city_tr"}
OPTIONS = {"drop": set(), "keep": set(), "redact": {"with"}, "hash": {"length", "prefix", "normalize"},
           "fake": {"type", "pool", "normalize"}, "generalize": {"to", "bucket", "keep", "format"}}
MIN_SECRET = 16
ID_FAKES = {"email", "phone_tr", "tckn", "vkn", "iban_tr"}  # collisions reported only for identifier-like fakes
TOKEN_KEYS = {"ad", "adi", "soyad", "soyadi", "isim", "tel", "gsm", "cep", "ip", "dob", "tc", "tckn", "vkn", "iban",
              "ssn", "pan", "zip", "plaka", "name", "phone", "email", "mail", "adres", "address", "birth", "dogum",
              "maas", "salary", "cinsiyet", "gender", "passport", "pasaport", "kimlik", "sicil", "lat", "lon"}
SUBSTR_KEYS = ["email", "eposta", "e_posta", "mail", "phone", "telefon", "mobile", "tckn", "kimlik", "identity",
               "national", "iban", "adres", "address", "name", "isim", "soyad", "birth", "dogum", "passport",
               "pasaport", "vergi", "postcode", "postal", "posta", "salary", "maas", "card", "kart", "ssn",
               "account", "hesap", "health", "saglik", "religion", "gender", "cinsiyet", "location", "konum"]
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$")
PHONE_RE = re.compile(r"^(\+?90|0)?[\s(]*5\d{2}[\s)-]*\d{3}[\s-]*\d{2}[\s-]*\d{2}$")

T = {"en": {"lang": "en", "title": "Masking report", "input": "Input", "output": "Output", "rows": "Rows",
            "col": "Column", "rule": "Rule", "detail": "Details", "note": "Notes", "warnings": "Warnings",
            "none": "None.", "pii_hdr": "header looks like personal data ('{k}')",
            "pii_val": "values look like {k} ({p}% of sampled values)",
            "uncovered_keep": "Column '{c}' has no rule and was KEPT by --default keep, but {why}. Add a rule.",
            "uncovered_drop": "Column '{c}' has no rule and was dropped (default). {why}.",
            "explicit_keep": "Column '{c}' is kept explicitly although {why}. Confirm this is intended.",
            "missing": "Rule for column '{c}' matches no column in the file (typo?). The data it was meant to "
                       "protect may be under another header.",
            "unparsed": "{n} value(s) in '{c}' could not be generalized and were redacted.",
            "collide": "{n} distinct input(s) in '{c}' map to an already used fake value (uniqueness is not "
                       "guaranteed for fake; use hash for keys).",
            "default": "no rule - default", "footer": "Hash and fake produce pseudonymised data: it is still "
            "personal data under KVKK/GDPR. Keep the secret outside the test environment, keep the extract's "
            "purpose, retention and access recorded, and delete the data when the test purpose ends."},
     "tr": {"lang": "tr", "title": "Maskeleme raporu", "input": "Girdi", "output": "Çıktı", "rows": "Satır",
            "col": "Sütun", "rule": "Kural", "detail": "Ayrıntı", "note": "Notlar", "warnings": "Uyarılar",
            "none": "Yok.", "pii_hdr": "başlık kişisel veri gibi görünüyor ('{k}')",
            "pii_val": "değerler {k} gibi görünüyor (örneklenen değerlerin %{p}'i)",
            "uncovered_keep": "'{c}' sütununun kuralı yok ve --default keep ile KORUNDU, ancak {why}. Kural ekleyin.",
            "uncovered_drop": "'{c}' sütununun kuralı yok ve atıldı (varsayılan). {why}.",
            "explicit_keep": "'{c}' sütunu açıkça korunuyor, ancak {why}. Bilinçli olduğunu teyit edin.",
            "missing": "'{c}' sütunu için kural var ama dosyada bu sütun yok (yazım hatası?). Korunması gereken "
                       "veri başka bir başlık altında olabilir.",
            "unparsed": "'{c}' sütununda {n} değer genelleştirilemedi ve karartıldı.",
            "collide": "'{c}' sütununda {n} farklı girdi zaten kullanılmış bir sahte değere eşlendi (fake "
                       "benzersizlik garanti etmez; anahtarlar için hash kullanın).",
            "default": "kural yok - varsayılan", "footer": "Hash ve fake takma adlı (pseudonymised) veri üretir: "
            "KVKK/GDPR açısından hâlâ kişisel veridir. Anahtarı test ortamı dışında tutun; çekimin amacını, "
            "saklama süresini ve erişimini kayıt altına alın; test amacı bitince veriyi silin."}}


class RulesError(Exception):
    pass


def fold_header(h: str) -> str:
    h = re.sub(r"([a-z])([A-Z])", r"\1_\2", h.strip())
    return h.translate(gd.FOLD).lower()


def pii_header(h: str) -> str | None:
    """Return the keyword that makes a header look like personal data, or None."""
    f = fold_header(h)
    for tok in re.split(r"[^a-z0-9]+", f):
        if tok in TOKEN_KEYS:
            return tok
    flat = re.sub(r"[^a-z0-9_]+", "_", f)
    return next((k for k in SUBSTR_KEYS if k in flat), None)


def pii_values(values: list[str]) -> tuple[str, int] | None:
    vals = [v.strip() for v in values if v and v.strip()]
    if not vals:
        return None
    checks = [("e-mail", lambda v: bool(EMAIL_RE.match(v))), ("TCKN", is_valid_tckn),
              ("IBAN", is_valid_iban), ("phone", lambda v: bool(PHONE_RE.match(v)))]
    for label, fn in checks:
        pct = round(100 * sum(1 for v in vals if fn(v)) / len(vals))
        if pct >= 50:
            return label, pct
    return None


def load_rules(data: dict) -> tuple[dict, str | None]:
    if not isinstance(data, dict) or not isinstance(data.get("columns"), dict):
        raise RulesError("rules file needs a 'columns' object: {\"columns\": {\"email\": {\"rule\": \"fake\", ...}}}")
    out, errs = {}, []
    for col, spec in data["columns"].items():
        spec = {"rule": spec} if isinstance(spec, str) else spec
        if not isinstance(spec, dict) or spec.get("rule") not in RULES:
            errs.append(f"{col}: rule must be one of {', '.join(sorted(RULES))} (got {spec!r})")
            continue
        r = spec["rule"]
        for k in spec:
            if k not in OPTIONS[r] | {"rule", "description"}:
                errs.append(f"{col}: option '{k}' is not valid for rule {r}{gd._hint(k, OPTIONS[r])}")
        if spec.get("normalize", "trim") not in ("trim", "lower", "digits", "phone", "none"):
            errs.append(f"{col}: normalize must be trim, lower, digits, phone or none")
        if r == "fake" and spec.get("type") not in FAKE_TYPES:
            errs.append(f"{col}: fake needs type in {', '.join(sorted(FAKE_TYPES))}"
                        f"{gd._hint(str(spec.get('type')), FAKE_TYPES)}")
        if r == "hash" and not (isinstance(spec.get("length", 16), int) and 8 <= spec.get("length", 16) <= 64):
            errs.append(f"{col}: hash length must be an integer 8-64")
        if r == "generalize":
            to, bucket = spec.get("to"), spec.get("bucket")
            if bucket is not None:
                try:
                    if Decimal(str(bucket)) <= 0:
                        raise InvalidOperation
                except InvalidOperation:
                    errs.append(f"{col}: bucket must be a positive number")
            elif to not in ("year", "year-month", "prefix", "postcode"):
                errs.append(f"{col}: generalize needs 'to' (year, year-month, prefix, postcode) or 'bucket'")
            if to == "prefix" and not (isinstance(spec.get("keep"), int) and spec["keep"] > 0):
                errs.append(f"{col}: generalize to prefix needs 'keep' (number of leading characters)")
        out[col] = spec
    if errs:
        raise RulesError("; ".join(errs))
    default = data.get("default")
    if default not in (None, "keep", "drop"):
        raise RulesError("'default' must be keep or drop")
    return out, default


def normalize(v: str, how: str) -> str:
    if how == "none":
        return v
    v = v.strip()
    if how == "lower":
        return v.lower()
    if how == "digits":
        return re.sub(r"\D", "", v)
    if how == "phone":
        d = re.sub(r"\D", "", v)
        return d[2:] if d.startswith("90") and len(d) == 12 else d[1:] if d.startswith("0") and len(d) == 11 else d
    return v


def token(secret: bytes, value: str) -> str:
    return hmac.new(secret, value.encode("utf-8"), hashlib.sha256).hexdigest()


def fake_value(kind: str, value: str, secret: bytes, pool: str = "tr") -> str:
    digest = hmac.new(secret, f"fake:{kind}:{value}".encode("utf-8"), hashlib.sha256).digest()
    rng = random.Random(int.from_bytes(digest, "big"))
    first = rng.choice(gd.FIRST_TR if pool == "tr" else gd.FIRST_EN)
    last = rng.choice(gd.LAST_TR if pool == "tr" else gd.LAST_EN)
    if kind == "first_name":
        return first
    if kind == "last_name":
        return last
    if kind == "full_name":
        return f"{first} {last}"
    if kind == "email":
        return f"{gd.ascii_fold(first)}.{gd.ascii_fold(last)}.{digest.hex()[:8]}@example.com"
    if kind == "phone_tr":
        return gd.phone_format(gd.gen_phone_digits(rng), "e164")
    if kind == "tckn":
        return gen_tckn(rng)
    if kind == "vkn":
        return gen_vkn(rng)
    if kind == "iban_tr":
        return gen_tr_iban(rng, gd.BANK_CODES)
    if kind == "city_tr":
        return rng.choice(gd.CITIES_TR)
    raise RulesError(f"unknown fake type {kind}")


DATE_FORMATS = ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%d.%m.%Y %H:%M")


def parse_date(v: str, fmt: str | None):
    v = v.strip()
    for f in ([fmt] if fmt else DATE_FORMATS):
        for cand in (v, v[:10]):
            try:
                return datetime.strptime(cand, f)
            except ValueError:
                continue
    return None


def parse_number(v: str) -> Decimal | None:
    s = re.sub(r"[^\d,.\-]", "", v.strip())
    if not s:
        return None
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".") if s.rfind(",") > s.rfind(".") else s.replace(",", "")
    elif "," in s:
        s = s.replace(",", ".") if s.count(",") == 1 and len(s.split(",")[1]) != 3 else s.replace(",", "")
    try:
        return Decimal(s)
    except InvalidOperation:
        return None


def generalize(v: str, spec: dict) -> str | None:
    to, bucket = spec.get("to"), spec.get("bucket")
    if bucket is not None:
        n = parse_number(v)
        if n is None:
            return None
        w = Decimal(str(bucket))
        lo = (n / w).to_integral_value(rounding=ROUND_FLOOR) * w
        return f"[{lo.normalize():f},{(lo + w).normalize():f})"
    if to in ("year", "year-month"):
        d = parse_date(v, spec.get("format"))
        if d is None:
            return None
        return f"{d.year:04d}" if to == "year" else f"{d.year:04d}-{d.month:02d}"
    keep = 2 if to == "postcode" else spec.get("keep", 2)
    s = v.strip()
    return s[:keep] if len(s) >= keep else None


def mask_file(in_path: Path, rules: dict, secret: bytes | None, out_path: Path, default: str = "drop",
              delimiter: str | None = None) -> dict:
    needs_secret = any(s["rule"] in ("hash", "fake") for s in rules.values())
    if needs_secret and not secret:
        raise RulesError("hash/fake rules need a secret")
    with in_path.open(encoding="utf-8-sig", newline="") as fh:
        sample = fh.read(8192)
        fh.seek(0)
        delim = delimiter or max([",", ";", "\t", "|"], key=lambda d: sample.split("\n", 1)[0].count(d))
        reader = csv.reader(fh, delimiter=delim)
        header = next(reader, None)
        if not header:
            raise RulesError(f"{in_path}: empty file or no header")
        rows = list(reader)
    lookup = {c.strip().lower(): c for c in rules}
    col_rule, col_src = [], []
    for h in header:
        key = h if h in rules else lookup.get(h.strip().lower())
        col_rule.append(rules[key] if key else {"rule": default})
        col_src.append("rule" if key else "default")
    matched = {h if h in rules else lookup.get(h.strip().lower()) for h in header}
    missing = [c for c in rules if c not in matched]
    stats = [{"column": h, "rule": r["rule"], "source": src, "changed": 0, "unparsed": 0, "collisions": 0,
              "pii": None, "spec": r} for h, r, src in zip(header, col_rule, col_src)]
    for i, h in enumerate(header):
        kw = pii_header(h)
        why = ("hdr", kw) if kw else None
        pv = pii_values([r[i] for r in rows[:200] if i < len(r)])
        if pv:
            why = ("val", pv)
        stats[i]["pii"] = why
    fakes: list[dict] = [{} for _ in header]
    out_cols = [i for i, r in enumerate(col_rule) if r["rule"] != "drop"]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, delimiter=delim, lineterminator="\n")
        w.writerow([header[i] for i in out_cols])
        for r in rows:
            r = r + [""] * (len(header) - len(r))
            out = []
            for i in out_cols:
                spec, v, st = col_rule[i], r[i], stats[i]
                rule = spec["rule"]
                if rule == "keep" or v.strip() == "":
                    out.append(v)
                    continue
                if rule == "redact":
                    nv = spec.get("with", "***")
                elif rule == "hash":
                    nv = spec.get("prefix", "") + token(secret, normalize(v, spec.get("normalize", "trim")))[
                        :spec.get("length", 16)]
                elif rule == "fake":
                    src = normalize(v, spec.get("normalize", "trim"))
                    nv = fake_value(spec["type"], src, secret, spec.get("pool", "tr"))
                    seen = fakes[i]
                    if spec["type"] in ID_FAKES and nv in seen and seen[nv] != src:
                        st["collisions"] += 1
                    seen.setdefault(nv, src)
                else:
                    nv = generalize(v, spec)
                    if nv is None:
                        st["unparsed"] += 1
                        nv = "***"
                st["changed"] += nv != v
                out.append(nv)
            w.writerow(out)
    return {"input": str(in_path), "output": str(out_path), "rows": len(rows), "delimiter": delim,
            "columns": stats, "missing": missing, "default": default}


LABELS = {"tr": {"e-mail": "e-posta", "phone": "telefon"}, "en": {}}


def _why(st, t):
    kind, k = st["pii"]
    if kind == "hdr":
        return t["pii_hdr"].format(k=k)
    return t["pii_val"].format(k=LABELS.get(t["lang"], {}).get(k[0], k[0]), p=k[1])


def findings(res: dict, lang: str = "en") -> tuple[list[str], bool]:
    """(warning lines, needs_decision)."""
    t = T[lang]
    out, decide = [], False
    for c in res["missing"]:
        out.append(t["missing"].format(c=c))
        decide = True
    for st in res["columns"]:
        if st["pii"]:
            if st["source"] == "default" and st["rule"] == "keep":
                out.append(t["uncovered_keep"].format(c=st["column"], why=_why(st, t)))
                decide = True
            elif st["source"] == "default":
                out.append(t["uncovered_drop"].format(c=st["column"], why=_why(st, t)[:1].upper() + _why(st, t)[1:]))
            elif st["rule"] == "keep":
                out.append(t["explicit_keep"].format(c=st["column"], why=_why(st, t)))
        if st["unparsed"]:
            out.append(t["unparsed"].format(c=st["column"], n=st["unparsed"]))
        if st["collisions"]:
            out.append(t["collide"].format(c=st["column"], n=st["collisions"]))
    return out, decide


def render_report(res: dict, lang: str = "en") -> str:
    t = T[lang]
    lines = [f"# {t['title']}", "", f"- {t['input']}: `{Path(res['input']).name}`",
             f"- {t['output']}: `{Path(res['output']).name}`", f"- {t['rows']}: {res['rows']}", "",
             f"| {t['col']} | {t['rule']} | {t['detail']} | {t['note']} |", "|---|---|---|---|"]
    for st in res["columns"]:
        spec = {k: v for k, v in st["spec"].items() if k not in ("rule", "description")}
        detail = ", ".join(f"{k}={v}" for k, v in spec.items())
        note = t["default"] if st["source"] == "default" else ""
        if st["pii"]:
            note = (note + "; " if note else "") + _why(st, t)
        lines.append(f"| {st['column']} | {st['rule']} | {detail} | {note} |")
    warns, _ = findings(res, lang)
    lines += ["", f"## {t['warnings']}", ""] + ([f"- {w}" for w in warns] or [t["none"]])
    lines += ["", f"> {t['footer']}", ""]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--in", dest="inp", required=True, help="CSV extract (UTF-8; delimiter auto-detected)")
    ap.add_argument("--rules", required=True, help="rules JSON")
    ap.add_argument("--secret-env", dest="secret_env", default="MASK_SECRET",
                    help="name of the environment variable holding the HMAC secret (default MASK_SECRET)")
    ap.add_argument("--out", required=True, help="masked CSV")
    ap.add_argument("--report", help="Markdown report")
    ap.add_argument("--default", choices=["keep", "drop"], help="action for columns without a rule (default: drop)")
    ap.add_argument("--delimiter", help="CSV delimiter (default: auto)")
    ap.add_argument("--lang", choices=["tr", "en"], default="en")
    sys.stdout.reconfigure(encoding="utf-8")
    a = ap.parse_args()
    inp, out = Path(a.inp), Path(a.out)
    if inp.resolve() == out.resolve():
        print("error: --out must differ from --in (never overwrite the extract in place)", file=sys.stderr)
        return 2
    try:
        rules, file_default = load_rules(json.loads(Path(a.rules).read_text(encoding="utf-8-sig")))
    except (OSError, ValueError) as e:
        print(f"error: cannot read rules {a.rules}: {e}", file=sys.stderr)
        return 2
    except RulesError as e:
        print(f"error: invalid rules: {e}", file=sys.stderr)
        return 2
    secret = None
    if any(s["rule"] in ("hash", "fake") for s in rules.values()):
        raw = os.environ.get(a.secret_env, "")
        if not raw:
            print(f"error: hash/fake rules need a secret in the environment variable {a.secret_env}. There is no "
                  "built-in default on purpose. Create one, e.g.\n  python -c \"import secrets; "
                  "print(secrets.token_hex(32))\"\nand keep it outside the test environment.", file=sys.stderr)
            return 2
        if len(raw) < MIN_SECRET:
            print(f"error: the secret in {a.secret_env} is shorter than {MIN_SECRET} characters", file=sys.stderr)
            return 2
        secret = raw.encode("utf-8")
    if not inp.is_file():
        print(f"error: input not found: {inp}", file=sys.stderr)
        return 2
    try:
        res = mask_file(inp, rules, secret, out, a.default or file_default or "drop", a.delimiter)
    except RulesError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    warns, decide = findings(res, a.lang)
    if a.report:
        Path(a.report).parent.mkdir(parents=True, exist_ok=True)
        Path(a.report).write_text(render_report(res, a.lang), encoding="utf-8", newline="\n")
    kept = sum(1 for c in res["columns"] if c["rule"] != "drop")
    print(f"masked {res['rows']} rows, {kept}/{len(res['columns'])} columns kept -> {out}"
          + (f"; report -> {a.report}" if a.report else ""))
    for w in warns:
        print(f"WARN  {w}")
    return 1 if decide else 0


if __name__ == "__main__":
    sys.exit(main())
