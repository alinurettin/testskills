"""Conservative, bounded JSON Schema subset for local OpenAPI fixture generation.

Not a complete JSON Schema implementation. Unsupported assertions are explicit UNVERIFIED
results; callers must not turn those into successful contract tests. No network or packages.
"""
from __future__ import annotations

import copy
from datetime import date, datetime
from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR
import json
import math
import re
import uuid

ANNOTATIONS = {'title', 'description', 'example', 'examples', 'default', 'deprecated', 'readOnly', 'writeOnly',
               '$schema', '$id', '$comment', '$defs', 'definitions', 'discriminator', 'xml', 'externalDocs'}
ASSERTIONS = {'type', 'nullable', 'enum', 'const', 'minimum', 'maximum', 'exclusiveMinimum', 'exclusiveMaximum',
              'multipleOf', 'minLength', 'maxLength', 'pattern', 'format', 'properties', 'required',
              'additionalProperties', 'minProperties', 'maxProperties', 'items', 'minItems', 'maxItems',
              'uniqueItems', 'allOf', 'anyOf', 'oneOf', 'not'}
FORMATS = {'email', 'uuid', 'date', 'date-time', 'uri', 'int32', 'int64', 'float', 'double', 'password'}
TYPES = {'null', 'boolean', 'object', 'array', 'number', 'integer', 'string'}
LIMIT = 1000  # synthesis bound; never allocate an unbounded contract-specified array/string


class SampleError(ValueError):
    pass


def equal(a, b):
    # JSON equality distinguishes booleans from numbers, but not 1 from 1.0.
    if isinstance(a, bool) or isinstance(b, bool):
        return type(a) is type(b) and a == b
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(equal(a[k], b[k]) for k in a)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(equal(x, y) for x, y in zip(a, b))
    return a == b


def schema_issues(s, at='$', depth=0):
    if depth > 30:
        return [f'{at}: UNVERIFIED schema depth limit']
    if isinstance(s, bool):
        return []
    if not isinstance(s, dict):
        return [f'{at}: UNVERIFIED malformed schema']
    out = []
    for k in s:
        if k == 'x-qa-unresolved' or (k not in ANNOTATIONS | ASSERTIONS and not k.startswith('x-')):
            out.append(f'{at}: UNVERIFIED unsupported keyword {k}')
    ts = s.get('type', [])
    ts = [ts] if isinstance(ts, str) else ts
    if not isinstance(ts, list) or any(not isinstance(t, str) or t not in TYPES for t in ts):
        out.append(f'{at}: UNVERIFIED invalid type')
    for k in ('minimum', 'maximum', 'multipleOf', 'exclusiveMinimum', 'exclusiveMaximum'):
        if k in s and (not isinstance(s[k], (int, float)) or not math.isfinite(s[k]) or
                       (isinstance(s[k], bool) and k not in ('exclusiveMinimum', 'exclusiveMaximum'))):
            out.append(f'{at}: UNVERIFIED invalid {k}')
    if 'multipleOf' in s and isinstance(s['multipleOf'], (int, float)) and s['multipleOf'] <= 0:
        out.append(f'{at}: UNVERIFIED non-positive multipleOf')
    for k in ('minLength', 'maxLength', 'minItems', 'maxItems', 'minProperties', 'maxProperties'):
        if k in s and (type(s[k]) is not int or s[k] < 0):
            out.append(f'{at}: UNVERIFIED invalid {k}')
    if 'required' in s and (not isinstance(s['required'], list) or any(not isinstance(x, str) for x in s['required'])):
        out.append(f'{at}: UNVERIFIED invalid required')
    if 'enum' in s and (not isinstance(s['enum'], list) or not s['enum']):
        out.append(f'{at}: UNVERIFIED invalid enum')
    if 'format' in s and s['format'] not in FORMATS:
        out.append(f'{at}: UNVERIFIED unsupported format {s["format"]}')
    if 'pattern' in s:
        try:
            # Python and ECMAScript differ here: decline non-portable constructs.
            if not isinstance(s['pattern'], str) or re.search(r'\(\?|\\[pPkK]|\\[1-9]', s['pattern']):
                raise ValueError
            re.compile(s['pattern'])
        except (ValueError, re.error):
            out.append(f'{at}: UNVERIFIED unsupported/invalid pattern')
    for k in ('allOf', 'oneOf', 'anyOf'):
        if k in s:
            if not isinstance(s[k], list) or not s[k]:
                out.append(f'{at}: UNVERIFIED invalid {k}')
            else:
                for i, sub in enumerate(s[k]):
                    out += schema_issues(sub, f'{at}.{k}[{i}]', depth + 1)
    if 'properties' in s:
        if not isinstance(s['properties'], dict):
            out.append(f'{at}: UNVERIFIED invalid properties')
        else:
            for k, sub in s['properties'].items():
                out += schema_issues(sub, f'{at}.{k}', depth + 1)
    for k in ('items', 'not', 'additionalProperties'):
        if k in s:
            out += schema_issues(s[k], f'{at}.{k}', depth + 1)
    return out


def _format_ok(v, fmt):
    try:
        if fmt == 'email':
            return bool(re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', v))
        if fmt == 'uuid':
            uuid.UUID(v)
        elif fmt == 'date':
            return len(v) == 10 and date.fromisoformat(v) is not None
        elif fmt == 'date-time':
            return 'T' in v and datetime.fromisoformat(v.replace('Z', '+00:00')).utcoffset() is not None
        elif fmt == 'uri':
            return bool(re.match(r'^[A-Za-z][A-Za-z0-9+.-]*:', v)) and not any(c.isspace() for c in v)
        return True  # numeric/password formats are annotations in this subset
    except (ValueError, OverflowError):
        return False


def validate(value, schema, at='$', depth=0):
    issues = schema_issues(schema, at)
    if issues:
        return issues
    if depth > 30:
        return [f'{at}: UNVERIFIED instance depth limit']
    if isinstance(schema, bool):
        return [] if schema else [f'{at}: false schema']
    s, out = schema, []
    for key in ('allOf', 'anyOf', 'oneOf'):
        if key in s:
            branches = [validate(value, sub, at, depth + 1) for sub in s[key]]
            count = sum(not e for e in branches)
            if (key == 'allOf' and count != len(branches)) or (key == 'anyOf' and count == 0) or (key == 'oneOf' and count != 1):
                out.append(f'{at}: {key} matched {count}/{len(branches)} branches')
    if 'not' in s and not validate(value, s['not'], at, depth + 1):
        out.append(f'{at}: matches forbidden schema')
    types = s.get('type', [])
    types = [types] if isinstance(types, str) else types
    actual = ('null' if value is None else 'boolean' if isinstance(value, bool) else 'object' if isinstance(value, dict)
              else 'array' if isinstance(value, list) else 'integer' if isinstance(value, int) or isinstance(value, float) and value.is_integer()
              else 'number' if isinstance(value, (int, float)) else 'string')
    if value is None and s.get('nullable') and types:
        types = types + ['null']
    if types and actual not in types and not (actual == 'integer' and 'number' in types):
        out.append(f'{at}: wrong type')
    if 'enum' in s and not any(equal(value, v) for v in s['enum']):
        out.append(f'{at}: not in enum')
    if 'const' in s and not equal(value, s['const']):
        out.append(f'{at}: const mismatch')
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        n = Decimal(str(value))
        for key, lower in (('minimum', True), ('maximum', False)):
            if key in s and (n < Decimal(str(s[key])) if lower else n > Decimal(str(s[key]))):
                out.append(f'{at}: outside {key}')
        for key, lower in (('exclusiveMinimum', True), ('exclusiveMaximum', False)):
            x = s.get(key)
            if x is True:
                x = s.get('minimum' if lower else 'maximum')
            elif x is False:
                x = None
            if x is not None and (n <= Decimal(str(x)) if lower else n >= Decimal(str(x))):
                out.append(f'{at}: outside {key}')
        if 'multipleOf' in s and n % Decimal(str(s['multipleOf'])) != 0:
            out.append(f'{at}: not multipleOf')
    if isinstance(value, str):
        if len(value) < s.get('minLength', 0) or len(value) > s.get('maxLength', math.inf):
            out.append(f'{at}: length outside bounds')
        if 'pattern' in s and not re.search(s['pattern'], value):
            out.append(f'{at}: pattern mismatch')
        if 'format' in s and not _format_ok(value, s['format']):
            out.append(f'{at}: format mismatch')
    if isinstance(value, list):
        if len(value) < s.get('minItems', 0) or len(value) > s.get('maxItems', math.inf):
            out.append(f'{at}: item count outside bounds')
        if s.get('uniqueItems') and any(equal(v, old) for i, v in enumerate(value) for old in value[:i]):
            out.append(f'{at}: duplicate array items')
        if 'items' in s:
            for i, v in enumerate(value):
                out += validate(v, s['items'], f'{at}[{i}]', depth + 1)
    if isinstance(value, dict):
        props = s.get('properties', {})
        for name in s.get('required', []):
            if name not in value and not (isinstance(props.get(name), dict) and props[name].get('readOnly')):
                out.append(f'{at}.{name}: required property missing')
        if len(value) < s.get('minProperties', 0) or len(value) > s.get('maxProperties', math.inf):
            out.append(f'{at}: property count outside bounds')
        for k, v in value.items():
            if k in props:
                out += validate(v, props[k], f'{at}.{k}', depth + 1)
            elif 'additionalProperties' in s:
                out += validate(v, s['additionalProperties'], f'{at}.{k}', depth + 1)
    return out


def synthesis_view(s):
    """An intersected generation hint only. Validation always uses the original schema."""
    if not isinstance(s, dict):
        return {}
    out = copy.deepcopy({k: v for k, v in s.items() if k != 'allOf'})
    for sub in s.get('allOf', []):
        for k, v in synthesis_view(sub).items():
            if k == 'required':
                out[k] = list(dict.fromkeys(out.get(k, []) + v))
            elif k == 'properties':
                props = out.setdefault(k, {})
                for name, schema in v.items():
                    props[name] = {'allOf': [props[name], schema]} if name in props else schema
            elif k in ('minimum', 'minLength', 'minItems', 'minProperties'):
                out[k] = max(out.get(k, v), v)
            elif k in ('maximum', 'maxLength', 'maxItems', 'maxProperties'):
                out[k] = min(out.get(k, v), v)
            else:
                out.setdefault(k, v)
    return out


def sample(schema, depth=0):
    """Return a checked request value or raise SampleError. Never guess a valid regex match."""
    issues = schema_issues(schema)
    if issues:
        raise SampleError('; '.join(issues))
    if depth > 8:
        raise SampleError('UNVERIFIED sample depth limit')
    if schema is False:
        raise SampleError('UNVERIFIED no value satisfies false schema')
    if schema is True:
        return None
    s = synthesis_view(schema)
    candidates = [s[k] for k in ('example', 'default', 'const') if k in s]
    examples = s.get('examples') or []
    candidates += examples if isinstance(examples, list) else list(examples.values())
    candidates += s.get('enum', [])
    for v in candidates:
        if not validate(v, schema):
            return copy.deepcopy(v)
    for sub in s.get('oneOf', []) + s.get('anyOf', []):
        try:
            v = sample({'allOf': [{k: v for k, v in s.items() if k not in ('oneOf', 'anyOf')}, sub]}, depth + 1)
            if not validate(v, schema):
                return v
        except SampleError:
            pass
    typ = s.get('type') or ('object' if 'properties' in s else 'string')
    types = typ if isinstance(typ, list) else [typ]
    for typ in types:
        try:
            if typ == 'object':
                props = s.get('properties', {})
                required = s.get('required', [])
                value = {k: sample(v, depth + 1) for k, v in props.items()
                         if not (isinstance(v, dict) and v.get('readOnly')) and (k in required or depth == 0 and not required)}
            elif typ == 'array':
                n = s.get('minItems', 0)
                if n > LIMIT:
                    raise SampleError('UNVERIFIED array synthesis limit')
                value = [sample(s.get('items', {}), depth + 1) for _ in range(n)]
            elif typ in ('integer', 'number'):
                lo, hi = Decimal(str(s.get('minimum', '-Infinity'))), Decimal(str(s.get('maximum', 'Infinity')))
                step = Decimal(str(s.get('multipleOf', 1 if typ == 'integer' else '0.01')))
                for key, lower in (('exclusiveMinimum', True), ('exclusiveMaximum', False)):
                    x = s.get(key)
                    if x is True:
                        x = s.get('minimum' if lower else 'maximum')
                    elif x is False:
                        x = None
                    if x is not None:
                        x = Decimal(str(x))
                        if lower:
                            lo = max(lo, (x / step).to_integral_value(rounding=ROUND_FLOOR) * step + step)
                        else:
                            hi = min(hi, (x / step).to_integral_value(rounding=ROUND_CEILING) * step - step)
                if lo.is_finite():
                    n = (lo / step).to_integral_value(rounding=ROUND_CEILING) * step
                elif hi.is_finite():
                    n = (hi / step).to_integral_value(rounding=ROUND_FLOOR) * step
                else:
                    n = step
                if typ == 'integer' and n != n.to_integral_value():
                    raise SampleError('UNVERIFIED integer multipleOf synthesis')
                value = int(n) if typ == 'integer' else float(n)
            elif typ == 'boolean':
                value = True
            elif typ == 'null':
                value = None
            else:
                n = s.get('minLength', 1)
                n = min(n, s.get('maxLength', n))
                if n > LIMIT:
                    raise SampleError('UNVERIFIED string synthesis limit')
                value = {'email': 'qa.test@example.com', 'date': '2026-01-15', 'date-time': '2026-01-15T10:00:00Z',
                         'uuid': '00000000-0000-4000-8000-000000000001', 'uri': 'https://example.com'}.get(s.get('format'), 'a' * n)
            if not validate(value, schema):
                return value
        except (SampleError, OverflowError):
            continue
    raise SampleError('UNVERIFIED no checked sample; provide a valid example or simplify the unsupported constraints')
