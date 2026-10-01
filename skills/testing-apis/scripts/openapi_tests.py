#!/usr/bin/env python3
"""Derive API test cases from an OpenAPI 3.x document - as QA Suite compact test cases AND as an
executable Playwright API spec that carries the same TC IDs.

Per operation it derives (only what the contract states):
  - happy path with a valid payload (examples first, otherwise generated from the schema) →
    documented 2xx status + response-schema check                                 [positive, high, smoke]
  - missing/invalid credentials when the operation is secured → 401                [security, negative]
  - each required body field / required query or path parameter omitted → 4xx      [negative]
  - boundary values from the schema: min/max (valid, positive) and just outside
    (minLength-1, maxLength+1, minimum-step, maximum+step, exclusive bounds),
    invalid enum value, wrong type                                                  [BVA / EP]
  - unknown resource id → 404 when 404 is documented                               [negative]
  - object-level authorization (another user's resource) → skeleton (needs two test users) [security]
Everything the contract does not specify is emitted as a question comment, never invented.

Input: OpenAPI 3.0/3.1 JSON (YAML works if PyYAML is installed). Local $refs are resolved.
Usage:
  python openapi_tests.py api/openapi.json --req-map qa/req-map.json --tests qa/test-cases.json --lang tr \
      --out qa/design/api-tests.src.md --spec-out automation/tests/api-contract.spec.ts [--only-tag Transfers]
  python openapi_tests.py api/openapi.json --req REQ-020 --out qa/design/api-tests.src.md   # one REQ for all
The spec imports ./api-helpers (copy assets/api-helpers.ts next to it) and reads API_BASE_URL,
API_TOKEN (and optional API_TOKEN_OTHER) from the environment.

Requirement links: every test of an operation traces to that operation's requirement(s).
  --req-map FILE  {"default": "REQ-020", "operations": {"createTransfer": "REQ-022",
                   "GET /accounts": ["REQ-021", "REQ-025"]}, "tags": {"Accounts": "REQ-021"}}
                  (values: a REQ ID or a list; other scripts' keys such as "capabilities" are ignored)
  x-req           on an operation in the OpenAPI document: "REQ-021" or ["REQ-021", "REQ-022"]
  Precedence: x-req > operations[operationId] > operations["METHOD /path"] > tags[first tag]
              > req-map default > --req.
  An operation without a requirement stops the run (exit 2) with the list of unmapped operations.
  One REQ for everything makes coverage look complete and hides thin or negative-free requirements.
Exit codes: 0 ok, 2 usage error, unreadable input or unmapped operations.
"""
from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from collections import Counter
from pathlib import Path

METHODS = ("get", "post", "put", "patch", "delete")
HTTP_METHODS = METHODS + ("head", "options", "trace")
T = {
    "tr": {"happy": "{m} {p} geçerli istekle {code} döner ve yanıt şemaya uyar", "noauth": "{m} {p} kimlik bilgisi olmadan 401 döner",
           "missing": "{m} {p} zorunlu '{f}' eksikken {code} döner", "valid_b": "{m} {p} '{f}' = {v} (sınır, geçerli) kabul edilir",
           "invalid_b": "{m} {p} '{f}' = {v} ({why}) reddedilir", "enum": "{m} {p} '{f}' geçersiz enum değeriyle reddedilir",
           "type": "{m} {p} '{f}' yanlış tipte ({v}) reddedilir", "notfound": "{m} {p} olmayan kaynak için 404 döner",
           "bola": "{m} {p} başka kullanıcının kaynağına erişimi reddeder (BOLA)",
           "badscheme": "{m} {p} 'Bearer' şeması olmayan Authorization başlığını 401 ile reddeder",
           "pattern": "{m} {p} '{f}' kalıba uymayan değerle ({v}) reddedilir",
           "bola_body": "{m} {p} gövdedeki '{f}' başka kullanıcıya aitse işlemi reddeder (BOLA, gövde)",
           "bola_body_step": "A kullanıcısının kaynağını ('{f}') içeren isteği B kullanıcısının token'ı ile gönder",
           "setup_create": "Kurulum: kaynağı POST {p} ile oluştur (herhangi bir 2xx), dönen id'yi kullan",
           "g_401": "Güvenli işlem ama 401 yanıtı dokümante değil", "g_404": "Yol parametresi var ama 404 dokümante değil",
           "g_errbody": "Şu hata yanıtlarının gövde şeması yok; hata kodları ve mesaj biçimi dokümante edilmeli: {c}",
           "g_idem": "Idempotency-Key (veya eşdeğeri) tanımlı değil; tekrarlanan/zaman aşımı sonrası yeniden gönderilen istek ne yapar?",
           "g_free_str": "Kısıtsız metin alanları (maxLength/pattern/format/enum yok): {f}",
           "g_free_num": "Üst sınırı olmayan sayı alanları (maximum yok): {f}",
           "g_addl": "İstek gövdesinde bilinmeyen alanlar (additionalProperties) için kural yok: reddedilir mi, yok mu sayılır? (mass assignment)",
           "g_example": "Yol parametresi örneği yok ({f}); testler ortamda gerçekten var olan bir kimlik gerektirir",
           "no_auth_hdr": " (Authorization başlığı yok)", "bad_hdr": " (Authorization: <token>, 'Bearer' yok)",
           "step_send": "İsteği gönder: {m} {p}", "exp_code": "HTTP {code}", "exp_schema": "HTTP {code}; yanıt gövdesi dokümante şemaya uyar",
           "exp_reject": "HTTP {code}; hata gövdesi dönülür, kaynak oluşturulmaz/değiştirilmez",
           "bola_step": "A kullanıcısına ait {p} kaynağını B kullanıcısının token'ı (API_TOKEN_OTHER) ile iste",
           "bola_exp": "HTTP 403 veya 404; A'nın verisi dönmez", "pre_auth": "Geçerli test token'ı (API_TOKEN) tanımlı",
           "pre_two": "İki test kullanıcısı: API_TOKEN (A) ve API_TOKEN_OTHER (B); örnek kaynak kimliği A'ya ait",
           "below": "alt sınırın altı", "above": "üst sınırın üstü", "short": "en kısa uzunluğun altı", "long": "en uzun uzunluğun üstü",
           "q4xx": "Sözleşme bu hata için durum kodu belirtmiyor; 4xx varsayıldı, sorulmalı"},
    "en": {"happy": "{m} {p} with a valid request returns {code} and matches the response schema", "noauth": "{m} {p} without credentials returns 401",
           "missing": "{m} {p} without required '{f}' returns {code}", "valid_b": "{m} {p} '{f}' = {v} (boundary, valid) is accepted",
           "invalid_b": "{m} {p} '{f}' = {v} ({why}) is rejected", "enum": "{m} {p} '{f}' with an invalid enum value is rejected",
           "type": "{m} {p} '{f}' with a wrong type ({v}) is rejected", "notfound": "{m} {p} for an unknown resource returns 404",
           "bola": "{m} {p} denies access to another user's resource (BOLA)",
           "badscheme": "{m} {p} rejects an Authorization header without the 'Bearer' scheme with 401",
           "pattern": "{m} {p} '{f}' not matching the pattern ({v}) is rejected",
           "bola_body": "{m} {p} rejects the operation when body '{f}' belongs to another user (BOLA, body)",
           "bola_body_step": "Send the request containing user A's resource ('{f}') with user B's token",
           "setup_create": "Setup: create the resource with POST {p} (any 2xx) and use the returned id",
           "g_401": "Secured operation, but no 401 response is documented", "g_404": "Takes a path parameter, but no 404 is documented",
           "g_errbody": "These error responses have no body schema; document the error codes and message format: {c}",
           "g_idem": "No Idempotency-Key (or equivalent); what happens on a duplicate request or a retry after a timeout?",
           "g_free_str": "Unconstrained string fields (no maxLength/pattern/format/enum): {f}",
           "g_free_num": "Number fields without an upper bound (no maximum): {f}",
           "g_addl": "No rule for unknown request-body fields (additionalProperties): rejected or ignored? (mass assignment)",
           "g_example": "No example for path parameter(s) {f}; tests need an ID that really exists in the environment",
           "no_auth_hdr": " (no Authorization header)", "bad_hdr": " (Authorization: <token>, no 'Bearer')",
           "step_send": "Send the request: {m} {p}", "exp_code": "HTTP {code}", "exp_schema": "HTTP {code}; body matches the documented schema",
           "exp_reject": "HTTP {code}; an error body is returned and nothing is created or changed",
           "bola_step": "Request user A's {p} resource with user B's token (API_TOKEN_OTHER)",
           "bola_exp": "HTTP 403 or 404; A's data is not returned", "pre_auth": "A valid test token (API_TOKEN) is configured",
           "pre_two": "Two test users: API_TOKEN (A) and API_TOKEN_OTHER (B); the example resource ID belongs to A",
           "below": "below minimum", "above": "above maximum", "short": "shorter than minLength", "long": "longer than maxLength",
           "q4xx": "The contract documents no status for this error; 4xx assumed - ask"},
}


def load(path: Path) -> dict:
    text = path.read_text(encoding="utf-8-sig")
    if path.suffix.lower() in (".yaml", ".yml"):
        try:
            import yaml  # type: ignore
        except ImportError:
            raise SystemExit("error: YAML needs PyYAML (pip install pyyaml) - or convert the spec to JSON")
        return yaml.safe_load(text)
    return json.loads(text)


class Resolver:
    def __init__(self, doc: dict):
        self.doc = doc

    def __call__(self, node, depth=0):
        if depth > 30:
            return {}
        if isinstance(node, dict):
            if "$ref" in node:
                ref = node["$ref"]
                if not ref.startswith("#/"):
                    return {"description": f"external $ref not resolved: {ref}"}
                target = self.doc
                for part in ref[2:].split("/"):
                    target = target[part.replace("~1", "/").replace("~0", "~")]
                return self(copy.deepcopy(target), depth + 1)
            if "allOf" in node:
                merged: dict = {"type": "object", "properties": {}, "required": []}
                for sub in node["allOf"]:
                    s = self(sub, depth + 1)
                    merged["properties"].update(s.get("properties", {}))
                    merged["required"] += s.get("required", [])
                return merged
            out = {k: self(v, depth + 1) for k, v in node.items()}
            if isinstance(out.get("type"), list):  # OpenAPI 3.1: type: ["string", "null"]
                types = [x for x in out["type"] if x != "null"]
                if "null" in out["type"]:
                    out["nullable"] = True
                out["type"] = types[0] if types else "null"
                if len(types) > 1:
                    out["x-other-types"] = types[1:]
            return out
        if isinstance(node, list):
            return [self(x, depth + 1) for x in node]
        return node


def sample(schema: dict, depth=0):
    """A valid value for the schema (example > default > enum > generated)."""
    if not schema or depth > 8:
        return None
    for k in ("example", "default"):
        if k in schema:
            return schema[k]
    if schema.get("examples"):
        ex = schema["examples"]
        return ex[0] if isinstance(ex, list) else next(iter(ex.values()), None)
    if schema.get("enum"):
        return schema["enum"][0]
    t = schema.get("type")
    if isinstance(t, list):
        t = next((x for x in t if x != "null"), "string")
    if "oneOf" in schema or "anyOf" in schema:
        return sample((schema.get("oneOf") or schema.get("anyOf"))[0], depth + 1)
    if t == "object" or "properties" in schema:
        props = schema.get("properties", {})
        req = schema.get("required", list(props)[:0])
        return {k: sample(props[k], depth + 1) for k in props if k in req or depth == 0 and not req}
    if t == "array":
        return [sample(schema.get("items", {}), depth + 1)]
    if t == "integer":
        return int(schema.get("minimum", 1)) if "minimum" in schema else 1
    if t == "number":
        return schema.get("minimum", 1) if "minimum" in schema else 1.0
    if t == "boolean":
        return True
    fmt = schema.get("format", "")
    n = max(int(schema.get("minLength", 1)), 1)
    return {"email": "qa.test@example.com", "date": "2026-01-15", "date-time": "2026-01-15T10:00:00Z",
            "uuid": "00000000-0000-4000-8000-000000000001", "uri": "https://example.com"}.get(fmt, "a" * min(n, 8) if n <= 8 else "a" * n)


def boundaries(name: str, s: dict, t: dict) -> list[tuple[str, object, bool, str]]:
    """(label, value, valid, why) boundary probes for one field."""
    out = []
    typ = s.get("type")
    step = 1 if typ == "integer" else 0.01
    if typ in ("integer", "number"):
        if "minimum" in s:
            out.append(("min", s["minimum"], not s.get("exclusiveMinimum") is True, ""))
            out.append(("min-", round(s["minimum"] - step, 2), False, t["below"]))
        if isinstance(s.get("exclusiveMinimum"), (int, float)) and not isinstance(s.get("exclusiveMinimum"), bool):
            out.append(("xmin", s["exclusiveMinimum"], False, t["below"]))
        if "maximum" in s:
            out.append(("max", s["maximum"], not s.get("exclusiveMaximum") is True, ""))
            out.append(("max+", round(s["maximum"] + step, 2), False, t["above"]))
        if isinstance(s.get("exclusiveMaximum"), (int, float)) and not isinstance(s.get("exclusiveMaximum"), bool):
            out.append(("xmax", s["exclusiveMaximum"], False, t["above"]))
    if typ == "string" and "pattern" not in s and "format" not in s and "enum" not in s:
        if "minLength" in s and s["minLength"] > 0:
            out.append(("minLen", "a" * s["minLength"], True, ""))
            out.append(("minLen-", "a" * (s["minLength"] - 1), False, t["short"]))
        if "maxLength" in s:
            out.append(("maxLen", "a" * s["maxLength"], True, ""))
            out.append(("maxLen+", "a" * (s["maxLength"] + 1), False, t["long"]))
    if typ == "string" and s.get("pattern") and "enum" not in s:
        for cand in ("__invalid__", "x", "!@#", "0", ""):
            try:
                if not re.search(s["pattern"], cand):
                    out.append(("pattern", cand, False, "pattern"))
                    break
            except re.error:
                break
    return out


ID_FIELD = re.compile(r"(^id$|Id$|_id$|ID$)")


def json_schema(resp):
    return (((resp or {}).get("content", {}) or {}).get("application/json", {}) or {}).get("schema")


def wrong_type(s: dict):
    typ = s.get("type")
    return {"string": 12345, "integer": "abc", "number": "abc", "boolean": "yes", "array": "x", "object": "x"}.get(typ)


def pick(codes: list[str], prefer: tuple[str, ...], default: str) -> tuple[str, bool]:
    for c in prefer:
        if c in codes:
            return c, True
    four = sorted(c for c in codes if c.startswith("4") and c not in ("401", "403", "404"))
    return (four[0], True) if four else (default, False)


def ts(v) -> str:
    return json.dumps(v, ensure_ascii=False)


def short(v) -> str:
    s = json.dumps(v, ensure_ascii=False)
    return s if len(s) <= 24 else f"{s[:10]}…({len(v) if isinstance(v, str) else '?'} chars)\""


# ---------------------------------------------------------------- requirement mapping (--req-map, x-req)
REQ_MAP_KEYS = {"default", "operations", "tags", "capabilities", "categories", "areas"}
REQ_TOKEN = re.compile(r"^[A-Za-z][A-Za-z0-9_.:-]*$")


def req_list(value, where: str) -> list[str]:
    """A REQ ID, a comma-separated string or a list of them -> de-duplicated list (ValueError if malformed)."""
    out: list[str] = []
    for v in value if isinstance(value, list) else [value]:
        if not isinstance(v, str):
            raise ValueError(f"{where}: expected a REQ ID or a list of REQ IDs, got {json.dumps(v)}")
        for x in (p.strip() for p in v.split(",")):
            if not REQ_TOKEN.match(x):
                raise ValueError(f"{where}: invalid requirement ID {x!r}")
            if x not in out:
                out.append(x)
    if not out:
        raise ValueError(f"{where}: no requirement ID")
    return out


def load_req_map(path: str | None, sections: tuple[str, ...]) -> tuple[dict, list[str]]:
    """--req-map JSON -> ({"default": [...], section: {key: [...]}}, warnings). ValueError when unusable."""
    rmap: dict = {"default": [], **{s: {} for s in sections}}
    if not path:
        return rmap, []
    try:
        raw = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as e:
        raise ValueError(f"--req-map: cannot read {path}: {e}")
    if not isinstance(raw, dict):
        raise ValueError(f"--req-map {path}: must be a JSON object")
    warnings = [f"--req-map: unknown key '{k}' ignored" for k in raw if k not in REQ_MAP_KEYS and not k.startswith(("_", "$"))]
    if raw.get("default") not in (None, "", []):
        rmap["default"] = req_list(raw["default"], "--req-map default")
    for s in sections:
        sec = raw.get(s) or {}
        if not isinstance(sec, dict):
            raise ValueError(f"--req-map: '{s}' must be an object of key -> REQ ID(s)")
        rmap[s] = {str(k): req_list(v, f"--req-map {s}.{k}") for k, v in sec.items()}
    return rmap, warnings


def req_summary(links: list[tuple[list[str], str]]) -> str:
    """'REQ-021 12 (neg 3), REQ-022 5 (neg 0)': generated tests per requirement."""
    count: Counter = Counter()
    neg: Counter = Counter()
    for reqs, pol in links:
        for r in reqs:
            count[r] += 1
            neg[r] += pol == "-"
    return ", ".join(f"{r} {count[r]} (neg {neg[r]})" for r in count)


def op_key(key: str) -> str:
    """'post  /transfers' -> 'POST /transfers' (other keys unchanged)."""
    m = re.match(r"^\s*([A-Za-z]+)\s+(/\S*)\s*$", key)
    return f"{m.group(1).upper()} {m.group(2)}" if m and m.group(1).lower() in HTTP_METHODS else key


def resolve_op(op: dict, method: str, path: str, rmap: dict, fallback: list[str]) -> tuple[list[str], str]:
    """REQ IDs of one operation and their source. Precedence: x-req > operations[operationId] >
    operations["METHOD /path"] > tags[first tag] > req-map default > --req."""
    if op.get("x-req") not in (None, "", []):
        return req_list(op["x-req"], f"{method} {path}: x-req"), "x-req"
    ops = rmap["operations"]
    if op.get("operationId") in ops:
        return ops[op["operationId"]], "operationId"
    if f"{method} {path}" in ops:
        return ops[f"{method} {path}"], "operations"
    tags = op.get("tags") or []
    if tags and tags[0] in rmap["tags"]:
        return rmap["tags"][tags[0]], f"tag {tags[0]}"
    if rmap["default"]:
        return rmap["default"], "default"
    return fallback, "--req"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec")
    ap.add_argument("--req", default="", help="fallback requirement ID(s), comma-separated, for operations the "
                    "--req-map and x-req do not cover (optional when they cover everything)")
    ap.add_argument("--req-map", dest="req_map", help="JSON map operations/tags -> requirement ID(s) (see above)")
    ap.add_argument("--tests", help="existing test-cases.json to continue TC numbering")
    ap.add_argument("--start", type=int)
    ap.add_argument("--lang", choices=["tr", "en"], default="en")
    ap.add_argument("--only-tag", help="only operations with this OpenAPI tag")
    ap.add_argument("--out", required=True, help="compact test cases (.src.md)")
    ap.add_argument("--spec-out", dest="spec_out", help="Playwright API spec (.spec.ts) with the same TC IDs")
    sys.stdout.reconfigure(encoding="utf-8")
    a = ap.parse_args()
    doc = load(Path(a.spec))
    if not str(doc.get("openapi", "")).startswith("3"):
        print("error: only OpenAPI 3.x is supported (Swagger 2.0: convert first)", file=sys.stderr)
        return 2
    R = Resolver(doc)
    t = T[a.lang]
    try:
        fallback = req_list(a.req, "--req") if a.req.strip() else []
        rmap, map_warnings = load_req_map(a.req_map, ("operations", "tags"))
        rmap["operations"] = {op_key(k): v for k, v in rmap["operations"].items()}
        op_reqs: dict[tuple[str, str], tuple[list[str], str]] = {}
        seen_keys, seen_tags, unmapped = set(), set(), []
        for path, item in (doc.get("paths") or {}).items():
            item = R(item)
            for m in METHODS:
                op = item.get(m)
                if not isinstance(op, dict) or not op:
                    continue
                seen_keys |= {f"{m.upper()} {path}", op.get("operationId")}
                seen_tags |= set(op.get("tags") or [])
                if a.only_tag and a.only_tag not in op.get("tags", []):
                    continue
                reqs, source = resolve_op(op, m.upper(), path, rmap, fallback)
                op_reqs[(m.upper(), path)] = (reqs, source)
                if not reqs:
                    unmapped.append(f"{m.upper()} {path}" + (f" ({op['operationId']})" if op.get("operationId") else ""))
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    if unmapped:
        more = f"; ... and {len(unmapped) - 20} more" if len(unmapped) > 20 else ""
        print(f"error: no requirement for {len(unmapped)} operation(s): {'; '.join(unmapped[:20])}{more}. Map them in "
              "--req-map (operations, tags or default), add x-req to the operation, or pass --req.", file=sys.stderr)
        return 2
    map_warnings += [f"--req-map: operations key '{k}' matches no operation" for k in rmap["operations"] if k not in seen_keys]
    map_warnings += [f"--req-map: tags key '{k}' matches no operation tag" for k in rmap["tags"] if k not in seen_tags]
    for w in map_warnings:
        print(f"warning: {w}", file=sys.stderr)
    n = a.start or 1
    if not a.start and a.tests and Path(a.tests).exists():
        data = json.loads(Path(a.tests).read_text(encoding="utf-8-sig"))
        ids = [int(m.group(1)) for x in data.get("test_cases", []) if (m := re.match(r"TC-(\d+)", x.get("id", "")))]
        n = max(ids) + 1 if ids else 1
    global_sec = doc.get("security")
    schemes = (doc.get("components", {}) or {}).get("securitySchemes", {}) or {}
    bearer = any((R(x) or {}).get("scheme", "").lower() == "bearer" for x in schemes.values())
    scheme_done = False
    compact = [f"# Contract tests derived by openapi_tests.py from {Path(a.spec).name} "
               f"({doc.get('info', {}).get('title', '')} {doc.get('info', {}).get('version', '')}). Review, then append to qa/test-cases.src.md."]
    if a.req_map or any(src == "x-req" for _, src in op_reqs.values()):
        compact += [f"# req-map: {k[0]} {k[1]} -> {', '.join(v[0])} ({v[1]})" for k, v in op_reqs.items()]
    spec = ["// Generated by QA Suite (testing-apis/openapi_tests.py). Same TC IDs as the compact test cases.",
            "// Env: API_BASE_URL, API_TOKEN, API_TOKEN_OTHER (optional). Test accounts only.",
            "import { test, expect } from '@playwright/test';",
            "import { api, checkSchema } from './api-helpers';", ""]
    questions, counts = [], {"ops": 0, "tests": 0, "exec": 0, "skeleton": 0}
    errbody = []
    creators = {}  # collection path -> body of a POST that returns an object with "id" (create-then-read setup)
    for cpath, citem in doc.get("paths", {}).items():
        cop = R(citem).get("post")
        if not cop:
            continue
        ccodes = sorted(c for c in cop.get("responses", {}) if c.startswith("2"))
        cresp = json_schema(cop["responses"].get(ccodes[0])) if ccodes else None
        cbody_s = json_schema(cop.get("requestBody"))
        cex = (((cop.get("requestBody") or {}).get("content", {}) or {}).get("application/json", {}) or {}).get("example")
        if cresp and "id" in (cresp.get("properties") or {}) and cbody_s is not None:
            creators[cpath] = cex if cex is not None else sample(cbody_s)

    cur_reqs: list[str] = []  # requirement(s) of the operation being generated (see op_reqs)
    links: list[tuple[list[str], str]] = []

    def add(title, pri, pol, tech, steps, tags, auto="yes, contract test", pre=None):
        nonlocal n
        tid = f"TC-{n:03d}"
        n += 1
        links.append((cur_reqs, pol))
        compact.extend(["", f"## {tid} | {title}", f"req: {', '.join(cur_reqs)} | pri: {pri} | pol: {pol} | tech: {tech} | cat: api"])
        for p in pre or []:
            compact.append(f"pre: {p}")
        for i, (act, data, exp) in enumerate(steps, 1):
            d = f" [{json.dumps(data, ensure_ascii=False)}]" if data not in (None, "") else ""
            compact.append(f"{i}. {act}{d} => {exp}")
        compact.append(f"tags: {', '.join(tags + ['generated'])} | auto: {auto} | status: draft")
        counts["tests"] += 1
        return tid

    for path, item in doc.get("paths", {}).items():
        item = R(item)
        common_params = item.get("parameters", [])
        for m in METHODS:
            op = item.get(m)
            if not op:
                continue
            if a.only_tag and a.only_tag not in op.get("tags", []):
                continue
            counts["ops"] += 1
            M = m.upper()
            cur_reqs = op_reqs[(M, path)][0]
            params = common_params + op.get("parameters", [])
            codes = list(op.get("responses", {}).keys())
            ok_code = next((c for c in sorted(codes) if c.startswith("2")), None)
            ok_schema = ((op.get("responses", {}).get(ok_code) or {}).get("content", {}).get("application/json", {}) or {}).get("schema") if ok_code else None
            body_schema = (((op.get("requestBody") or {}).get("content", {}) or {}).get("application/json", {}) or {}).get("schema")
            body_example = (((op.get("requestBody") or {}).get("content", {}) or {}).get("application/json", {}) or {}).get("example")
            body = body_example if body_example is not None else (sample(body_schema) if body_schema else None)
            params = [p for p in params if p.get("in") in ("path", "query")]  # headers/cookies are handled by the helper
            pvals = {p["name"]: sample(p.get("schema", {})) if "example" not in p else p["example"] for p in params}
            secured = (op.get("security", global_sec) or []) != []
            err_code, documented = pick(codes, ("400", "422"), "4xx")
            has_validation = bool(op.get("requestBody")) or any(p.get("required") and p.get("in") == "query" for p in params)
            if not documented and has_validation:
                questions.append(f"{M} {path}: {t['q4xx']}")

            def gap(k, **kw):
                questions.append(f"{M} {path}: {t[k].format(**kw)}")

            if secured and "401" not in codes:
                gap("g_401")
            if any(p.get("in") == "path" for p in params) and "404" not in codes:
                gap("g_404")
            no_body = sorted(c for c in codes if c[0] in "45" and c != "500" and not json_schema(op["responses"].get(c)))
            if no_body:
                errbody.append(f"{M} {path} ({', '.join(no_body)})")
            if M == "POST" and not any(p.get("in") == "header" and "idempot" in p.get("name", "").lower()
                                       for p in common_params + op.get("parameters", [])):
                gap("g_idem")
            if body_schema and body_schema.get("properties"):
                bp = body_schema["properties"]
                free_s = [k for k, v in bp.items() if v.get("type") == "string" and not v.get("readOnly")
                          and not any(x in v for x in ("maxLength", "pattern", "format", "enum"))]
                free_n = [k for k, v in bp.items() if v.get("type") in ("integer", "number") and not v.get("readOnly")
                          and "maximum" not in v and "exclusiveMaximum" not in v and "enum" not in v]
                if free_s:
                    gap("g_free_str", f=", ".join(free_s))
                if free_n:
                    gap("g_free_num", f=", ".join(free_n))
                if "additionalProperties" not in body_schema:
                    gap("g_addl")
            parent = path.rsplit("/", 1)[0]
            create_first = (M == "GET" and len([p for p in params if p.get("in") == "path"]) == 1
                            and path.endswith("}") and parent in creators)
            no_ex = [p["name"] for p in params if p.get("in") == "path" and "example" not in p and "example" not in p.get("schema", {})]
            if no_ex and not create_first:
                gap("g_example", f=", ".join(no_ex))
            err_schema = json_schema(op.get("responses", {}).get(err_code)) if documented else None
            err_check = f" expect(checkSchema(await res.json(), {ts(err_schema)})).toEqual([]);" if err_schema else ""
            tag = re.sub(r"[^a-z0-9]+", "-", (op.get("tags") or ["api"])[0].lower()).strip("-")
            opid = op.get("operationId") or f"{m}_{path}"
            spec.append(f"test.describe({ts(f'{M} {path}')}, () => {{")
            call_args = f"{ts(M)}, {ts(path)}, {ts(pvals)}"
            created_lines, read_args = [], call_args
            if create_first:
                pname = next(p["name"] for p in params if p.get("in") == "path")
                created_lines = [f"    const created = await api(request, 'POST', {ts(parent)}, {{}}, {{ body: {ts(creators[parent])} }});",
                                 f"    expect(created.ok(), 'setup: POST {parent} must succeed (any 2xx)').toBeTruthy();",
                                 "    const createdId = (await created.json()).id;"]
                read_args = f"{ts(M)}, {ts(path)}, {{ ...{ts(pvals)}, {ts(pname)}: createdId }}"

            if ok_code:
                pre = ([t["pre_auth"]] if secured else []) + ([t["setup_create"].format(p=parent)] if create_first else [])
                tid = add(t["happy"].format(m=M, p=path, code=ok_code), "h", "+", "rb",
                          [(t["step_send"].format(m=M, p=path), body, t["exp_schema"].format(code=ok_code))],
                          ["api", "contract", "smoke", tag], pre=pre)
                spec.append(f"  test({ts(tid + ' ' + t['happy'].format(m=M, p=path, code=ok_code))}, {{ tag: ['@{tid}', '@api', '@smoke'] }}, async ({{ request }}) => {{")
                if create_first:
                    spec += created_lines
                spec += [f"    const res = await api(request, {read_args}, {{ body: {ts(body)} }});",
                         f"    expect(res.status()).toBe({int(ok_code)});"]
                if ok_schema:
                    spec.append(f"    expect(checkSchema(await res.json(), {ts(ok_schema)})).toEqual([]);")
                spec.append("  });")
                counts["exec"] += 1
            if secured:
                tid = add(t["noauth"].format(m=M, p=path), "h", "-", "eg",
                          [(t["step_send"].format(m=M, p=path) + t["no_auth_hdr"], None, t["exp_code"].format(code=401))],
                          ["api", "security", "auth", tag])
                spec += [f"  test({ts(tid + ' ' + t['noauth'].format(m=M, p=path))}, {{ tag: ['@{tid}', '@api', '@security'] }}, async ({{ request }}) => {{",
                         f"    const res = await api(request, {call_args}, {{ body: {ts(body)}, auth: false }});",
                         "    expect(res.status()).toBe(401);", "  });"]
                counts["exec"] += 1
                if not scheme_done and bearer:
                    scheme_done = True  # once per API: the auth middleware is usually shared
                    tid = add(t["badscheme"].format(m=M, p=path), "m", "-", "eg",
                              [(t["step_send"].format(m=M, p=path) + t["bad_hdr"], None, t["exp_code"].format(code=401))],
                              ["api", "security", "auth", tag])
                    spec += [f"  test({ts(tid + ' ' + t['badscheme'].format(m=M, p=path))}, {{ tag: ['@{tid}', '@api', '@security'] }}, async ({{ request }}) => {{",
                             f"    const res = await api(request, {call_args}, {{ body: {ts(body)}, auth: false, headers: {{ Authorization: process.env.API_TOKEN ?? '' }} }});",
                             "    expect(res.status()).toBe(401);", "  });"]
                    counts["exec"] += 1
            # required parameters
            for p in params:
                if p.get("required") and p.get("in") == "query":
                    q = {k: v for k, v in pvals.items() if k != p["name"]}
                    tid = add(t["missing"].format(m=M, p=path, f=p["name"], code=err_code), "m", "-", "ep",
                              [(t["step_send"].format(m=M, p=path), None, t["exp_reject"].format(code=err_code))], ["api", "validation", tag])
                    spec += [f"  test({ts(tid + ' ' + t['missing'].format(m=M, p=path, f=p['name'], code=err_code))}, {{ tag: ['@{tid}', '@api'] }}, async ({{ request }}) => {{",
                             f"    const res = await api(request, {ts(M)}, {ts(path)}, {ts(q)}, {{ body: {ts(body)} }});",
                             f"    {'expect(res.status()).toBe(' + err_code + ');' + err_check if documented else 'expect(res.status()).toBeGreaterThanOrEqual(400); expect(res.status()).toBeLessThan(500);'}",
                             "  });"]
                    counts["exec"] += 1
            if body_schema and isinstance(body, dict):
                props = body_schema.get("properties", {})
                for f in body_schema.get("required", []):
                    b2 = {k: v for k, v in body.items() if k != f}
                    tid = add(t["missing"].format(m=M, p=path, f=f, code=err_code), "m", "-", "ep",
                              [(t["step_send"].format(m=M, p=path), b2, t["exp_reject"].format(code=err_code))], ["api", "validation", tag])
                    spec += [f"  test({ts(tid + ' ' + t['missing'].format(m=M, p=path, f=f, code=err_code))}, {{ tag: ['@{tid}', '@api'] }}, async ({{ request }}) => {{",
                             f"    const res = await api(request, {call_args}, {{ body: {ts(b2)} }});",
                             f"    {'expect(res.status()).toBe(' + err_code + ');' + err_check if documented else 'expect(res.status()).toBeGreaterThanOrEqual(400); expect(res.status()).toBeLessThan(500);'}",
                             "  });"]
                    counts["exec"] += 1
                for f, s in props.items():
                    if s.get("readOnly"):
                        continue
                    probes = boundaries(f, s, t)
                    if s.get("enum"):
                        probes.append(("enum", "__invalid__", False, "enum"))
                    wt = wrong_type(s)
                    if wt is not None:
                        probes.append(("type", wt, False, "type"))
                    for label, val, valid, why in probes:
                        b2 = dict(body)
                        b2[f] = val
                        if valid:
                            title = t["valid_b"].format(m=M, p=path, f=f, v=short(val))
                            exp_c = ok_code or "2xx"
                            tid = add(title, "m", "+", "bva", [(t["step_send"].format(m=M, p=path), b2, t["exp_code"].format(code=exp_c))],
                                      ["api", "boundary", tag])
                            assertion = f"expect(res.status()).toBe({int(ok_code)});" if ok_code else "expect(res.ok()).toBeTruthy();"
                        else:
                            if label == "enum":
                                title = t["enum"].format(m=M, p=path, f=f)
                            elif label == "type":
                                title = t["type"].format(m=M, p=path, f=f, v=short(val))
                            elif label == "pattern":
                                title = t["pattern"].format(m=M, p=path, f=f, v=short(val))
                            else:
                                title = t["invalid_b"].format(m=M, p=path, f=f, v=short(val), why=why)
                            tid = add(title, "m", "-", "bva" if label not in ("enum", "type", "pattern") else "ep",
                                      [(t["step_send"].format(m=M, p=path), b2, t["exp_reject"].format(code=err_code))],
                                      ["api", "validation", tag])
                            assertion = ("expect(res.status()).toBe(" + err_code + ");" + err_check) if documented else \
                                "expect(res.status()).toBeGreaterThanOrEqual(400); expect(res.status()).toBeLessThan(500);"
                        spec += [f"  test({ts(tid + ' ' + title)}, {{ tag: ['@{tid}', '@api'] }}, async ({{ request }}) => {{",
                                 f"    const res = await api(request, {call_args}, {{ body: {ts(b2)} }});",
                                 f"    {assertion}", "  });"]
                        counts["exec"] += 1
            path_params = [p for p in params if p.get("in") == "path"]
            if path_params and "404" in codes:
                bad = {**pvals, **{p["name"]: ("999999999" if p.get("schema", {}).get("type") in ("integer", "number") else "does-not-exist-000") for p in path_params}}
                tid = add(t["notfound"].format(m=M, p=path), "m", "-", "eg",
                          [(t["step_send"].format(m=M, p=path), bad, t["exp_code"].format(code=404))], ["api", "negative", tag])
                spec += [f"  test({ts(tid + ' ' + t['notfound'].format(m=M, p=path))}, {{ tag: ['@{tid}', '@api'] }}, async ({{ request }}) => {{",
                         f"    const res = await api(request, {ts(M)}, {ts(path)}, {ts(bad)}, {{ body: {ts(body)} }});",
                         "    expect(res.status()).toBe(404);", "  });"]
                counts["exec"] += 1
            if path_params and secured:
                tid = add(t["bola"].format(m=M, p=path), "h", "-", "eg",
                          [(t["bola_step"].format(p=path), None, t["bola_exp"])], ["api", "security", "bola", tag],
                          auto="yes, needs two test users",
                          pre=[t["pre_two"]] + ([t["setup_create"].format(p=parent)] if create_first else []))
                spec.append(f"  test({ts(tid + ' ' + t['bola'].format(m=M, p=path))}, {{ tag: ['@{tid}', '@api', '@security'] }}, async ({{ request }}) => {{")
                if create_first:  # A creates the resource and B must not read it: no manual test data needed
                    spec += ["    test.skip(!process.env.API_TOKEN_OTHER, 'needs API_TOKEN_OTHER (a second test user)');"] + created_lines
                    counts["exec"] += 1
                else:
                    spec.append(f"    test.fixme(true, 'QA Suite skeleton {tid}: confirm the IDs below belong to the API_TOKEN user, set API_TOKEN_OTHER to a second test user, then delete this line');")
                    counts["skeleton"] += 1
                spec += [f"    const res = await api(request, {read_args}, {{ body: {ts(body)}, as: 'other' }});",
                         "    expect([403, 404]).toContain(res.status());", "  });"]
            props_all = (body_schema or {}).get("properties") or {}
            id_fields = [f for f, v in props_all.items()
                         if ID_FIELD.search(f) and not v.get("readOnly") and isinstance(body, dict) and f in body]
            if secured and M in ("POST", "PUT", "PATCH", "DELETE"):
                for f in id_fields:
                    tid = add(t["bola_body"].format(m=M, p=path, f=f), "h", "-", "eg",
                              [(t["bola_body_step"].format(f=f), body, t["bola_exp"])], ["api", "security", "bola", tag],
                              auto="yes, needs two test users", pre=[t["pre_two"]])
                    spec += [f"  test({ts(tid + ' ' + t['bola_body'].format(m=M, p=path, f=f))}, {{ tag: ['@{tid}', '@api', '@security'] }}, async ({{ request }}) => {{",
                             f"    test.fixme(true, 'QA Suite skeleton {tid}: confirm {f} in the body belongs to the API_TOKEN user, set API_TOKEN_OTHER, then delete this line');",
                             f"    const res = await api(request, {call_args}, {{ body: {ts(body)}, as: 'other' }});",
                             "    expect([403, 404]).toContain(res.status());", "  });"]
                    counts["skeleton"] += 1
            spec.append("});\n")
    if errbody:  # one question for the whole API: error bodies are usually one shared model
        questions.append(t["g_errbody"].format(c="; ".join(errbody)))
    if questions:
        compact.append("")
        compact += [f"# QUESTION: {q}" for q in questions]
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text("\n".join(compact) + "\n", encoding="utf-8", newline="\n")
    msg = f"wrote {a.out}: {counts['tests']} test cases from {counts['ops']} operations"
    if a.spec_out:
        Path(a.spec_out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.spec_out).write_text("\n".join(spec) + "\n", encoding="utf-8", newline="\n")
        msg += f"; {a.spec_out}: {counts['exec']} executable + {counts['skeleton']} skeleton tests"
    print(msg)
    if links:
        print(f"  requirements: {req_summary(links)}")
        if len({r for reqs, _ in links for r in reqs}) == 1 and counts["ops"] > 1:
            print(f"  note: all {counts['tests']} tests trace to {links[0][0][0]}; map operations to their requirements "
                  "with --req-map (or x-req) so the RTM can show thin or negative-free requirements")
    for q in questions:
        print(f"  question: {q}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
