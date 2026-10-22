// QA Suite API helpers: Playwright only, conservative schema subset. See references/api-testing.md.
import { test } from '@playwright/test';
import type { APIRequestContext, APIResponse } from '@playwright/test';
const BASE = process.env.API_BASE_URL ?? 'http://127.0.0.1:3000';
type Opts = { body?: unknown; auth?: boolean; as?: 'main' | 'other'; token?: string; headers?: Record<string, string> };

export async function api(request: APIRequestContext, method: string, path: string,
                          params: Record<string, unknown> = {}, opts: Opts = {}): Promise<APIResponse> {
  let url = path;
  method = method.toUpperCase();
  const query: Record<string, string> = {};
  for (const [k, v] of Object.entries(params)) {
    if (url.includes(`{${k}}`)) url = url.replaceAll(`{${k}}`, encodeURIComponent(String(v)));
    else if (v !== undefined && v !== null) query[k] = String(v);
  }
  const headers: Record<string, string> = { 'Content-Type': 'application/json', ...(opts.headers ?? {}) };
  const token = opts.token ?? (opts.as === 'other' ? process.env.API_TOKEN_OTHER : process.env.API_TOKEN);
  if (opts.as === 'other' && !token) throw new Error('API_TOKEN_OTHER is not set (second test user needed)');
  if (opts.auth !== false && token) {
    for (const key of Object.keys(headers)) if (key.toLowerCase() === 'authorization') delete headers[key];
    headers.Authorization = `Bearer ${token}`;
  }
  const sendBody = opts.body !== undefined && opts.body !== null && !['GET', 'HEAD'].includes(method);
  const res = await request.fetch(BASE + url, { method, headers, params: query, data: sendBody ? opts.body : undefined });
  if (process.env.API_EVIDENCE !== 'off') await attachEvidence(BASE + url, params, sendBody ? opts.body : undefined, headers, res);
  return res;
}

const REDACTED = '[REDACTED]';
function isSensitive(key: string): boolean {
  const norm = (s: string) => s.replace(/[^a-z0-9]/gi, '').toLowerCase();
  const extra = (process.env.API_EVIDENCE_REDACT_KEYS ?? '').split(',').map(norm).filter(Boolean);
  return /authorization|cookie|token|secret|password|passwd|pwd|apikey|credential|session|tckn|iban|email|phone|address|birth|salary/i.test(norm(key)) || extra.includes(norm(key));
}
function mediaType(headers: Record<string, string>): string {
  const raw = Object.entries(headers).find(([k]) => k.toLowerCase() === 'content-type')?.[1] ?? '';
  if (/^application\/(?:[a-z0-9.-]+\+)?json(?:;|$)/i.test(raw)) return 'json';
  if (/^application\/x-www-form-urlencoded(?:;|$)/i.test(raw)) return 'form';
  return 'other';
}
/** Exact dotted paths only; no wildcard. Secret-like fields cannot be opted in.
 * Default: omit all body keys/values. An allowlist is a deliberate disclosure decision.
 */
function collectSecrets(value: unknown, secrets: Set<string>, secret = false, depth = 0): void {
  if (depth > 20) return;
  if (value !== null && typeof value === 'object') {
    for (const [key, item] of Object.entries(value)) collectSecrets(item, secrets, secret || isSensitive(key), depth + 1);
  } else if (secret && value !== undefined && value !== null && String(value)) secrets.add(String(value));
}
function safeStructured(value: unknown, secrets: Set<string>): object {
  const allowed = (process.env.API_EVIDENCE_ALLOW_FIELDS ?? '').split(',').map(p => p.trim()).filter(Boolean);
  if (!allowed.length) return { state: 'omitted', reason: 'no explicitly allowed fields' };
  let omitted = 0;
  function visit(v: unknown, path: string[], depth: number): unknown {
    if (depth > 20) { omitted++; return REDACTED; }
    if (v !== null && typeof v === 'object') {
      const out: Record<string, unknown> = Object.create(null);
      for (const [key, item] of Object.entries(v)) {
        const next = [...path, key], name = next.join('.');
        // A secret may also be a property name: only approved keys survive.
        if (isSensitive(key)) { omitted++; continue; }
        if (allowed.some(a => a === name || a.startsWith(name + '.'))) out[key] = visit(item, next, depth + 1);
        else omitted++;
      }
      return out;
    }
    if (allowed.includes(path.join('.'))) {
      if (typeof v === 'string') {
        for (const secret of [...secrets].sort((a, b) => b.length - a.length)) v = (v as string).split(secret).join(REDACTED);
        return v;
      }
      return v !== null && secrets.has(String(v)) ? REDACTED : v;
    }
    omitted++; return REDACTED;
  }
  const sanitized = visit(value, [], 0), text = JSON.stringify(sanitized);
  // Sanitize the complete value BEFORE truncating what is persisted.
  return text.length > 4000 ? { state: 'sanitized', omitted, truncated: true, preview: text.slice(0, 4000) }
    : { state: 'sanitized', omitted, value: sanitized };
}
function safeBody(body: unknown, kind: string, secrets: Set<string>): object {
  if (body === undefined || body === null) return { state: 'empty' };
  if (kind !== 'json' && kind !== 'form') return { state: 'omitted', reason: 'binary, text or unsupported content type' };
  if (typeof body === 'string') {
    if (body.length > 1_000_000) return { state: 'omitted', reason: 'body exceeds parsing budget' };
    try {
      const parsed = kind === 'json' ? JSON.parse(body) : Object.fromEntries(new URLSearchParams(body));
      collectSecrets(parsed, secrets);
      return safeStructured(parsed, secrets);
    }
    catch { return { state: 'omitted', reason: 'malformed structured body' }; }
  }
  if (typeof body === 'object' && !ArrayBuffer.isView(body) && !(body instanceof ArrayBuffer)) {
    collectSecrets(body, secrets);
    return safeStructured(body, secrets);
  }
  return { state: 'omitted', reason: 'unsupported body value' };
}
async function attachEvidence(url: string, params: Record<string, unknown>, body: unknown, headers: Record<string, string>, res: APIResponse): Promise<void> {
  let info;
  try { info = test.info(); } catch { return; }
  const rh = res.headers(), kind = mediaType(rh);
  const secrets = new Set<string>();
  for (const v of Object.values(params)) if (v !== undefined && v !== null) secrets.add(String(v));
  for (const [key, value] of [...Object.entries(headers), ...Object.entries(rh)]) {
    if (!['content-type', 'accept', 'content-length'].includes(key.toLowerCase())) {
      secrets.add(value);
      for (const part of value.split(/[=;,\s]+/)) if (part) secrets.add(part);
    }
  }
  for (const v of [process.env.API_TOKEN, process.env.API_TOKEN_OTHER]) if (v) secrets.add(v);
  try {
    const parsed = new URL(url);
    parsed.searchParams.forEach(v => { if (v) secrets.add(v); });
    if (parsed.username) secrets.add(decodeURIComponent(parsed.username));
    if (parsed.password) secrets.add(decodeURIComponent(parsed.password));
  } catch { /* endpoint is omitted regardless */ }
  collectSecrets(body, secrets);
  // Parse request JSON/forms before sanitizing a response that may echo those secrets.
  safeBody(body, mediaType(headers), secrets);
  let responseBody: object = { state: 'omitted', reason: 'binary, text or unsupported content type' };
  if (kind !== 'other') {
    try { responseBody = safeBody(await res.text(), kind, secrets); }
    catch { responseBody = { state: 'omitted', reason: 'body not readable' }; }
  }
  const safeHeaders = (h: Record<string, string>) => ({ count: Object.keys(h).length, values: REDACTED });
  const evidence = {
    policy: 'allowlisted fields only; secrets always omitted; sanitize before truncation',
    request: { endpoint: '[omitted]', parameters: { count: Object.keys(params).length, values: REDACTED },
      headers: safeHeaders(headers), body: safeBody(body, mediaType(headers), secrets) },
    response: { status: res.status(), mediaType: kind, headers: safeHeaders(rh), body: responseBody },
  };
  await info.attach(`API response ${res.status()}`, { body: JSON.stringify(evidence, null, 2), contentType: 'application/json' });
}

type Schema = boolean | { [key: string]: any };
const annotations = new Set(['title', 'description', 'example', 'examples', 'default', 'deprecated', 'readOnly', 'writeOnly',
  '$schema', '$id', '$comment', '$defs', 'definitions', 'discriminator', 'xml', 'externalDocs']);
const assertions = new Set(['type', 'nullable', 'enum', 'const', 'minimum', 'maximum', 'exclusiveMinimum', 'exclusiveMaximum',
  'multipleOf', 'minLength', 'maxLength', 'pattern', 'format', 'properties', 'required', 'additionalProperties',
  'minProperties', 'maxProperties', 'items', 'minItems', 'maxItems', 'uniqueItems', 'allOf', 'anyOf', 'oneOf', 'not']);
const formats = new Set(['email', 'uuid', 'date', 'date-time', 'uri', 'int32', 'int64', 'float', 'double', 'password']);
const jsonTypes = new Set(['null', 'boolean', 'object', 'array', 'number', 'integer', 'string']);

function schemaIssues(schema: Schema, at: string, depth = 0): string[] {
  if (depth > 30) return [`${at}: UNVERIFIED schema depth limit`];
  if (typeof schema === 'boolean') return [];
  if (!schema || typeof schema !== 'object' || Array.isArray(schema)) return [`${at}: UNVERIFIED malformed schema`];
  const errs: string[] = [];
  for (const key of Object.keys(schema)) if (key === 'x-qa-unresolved' || (!annotations.has(key) && !assertions.has(key) && !key.startsWith('x-')))
    errs.push(`${at}: UNVERIFIED unsupported keyword ${key}`);
  const types = Array.isArray(schema.type) ? schema.type : schema.type === undefined ? [] : [schema.type];
  if (types.some((t: unknown) => !jsonTypes.has(t as string))) errs.push(`${at}: UNVERIFIED invalid type`);
  for (const key of ['minimum', 'maximum', 'multipleOf', 'exclusiveMinimum', 'exclusiveMaximum']) {
    const v = schema[key];
    if (v !== undefined && !(typeof v === 'number' && Number.isFinite(v)) && !(key.startsWith('exclusive') && typeof v === 'boolean'))
      errs.push(`${at}: UNVERIFIED invalid ${key}`);
  }
  if (schema.multipleOf !== undefined && schema.multipleOf <= 0) errs.push(`${at}: UNVERIFIED non-positive multipleOf`);
  for (const key of ['minLength', 'maxLength', 'minItems', 'maxItems', 'minProperties', 'maxProperties'])
    if (schema[key] !== undefined && (!Number.isInteger(schema[key]) || schema[key] < 0)) errs.push(`${at}: UNVERIFIED invalid ${key}`);
  if (schema.required !== undefined && (!Array.isArray(schema.required) || schema.required.some((v: unknown) => typeof v !== 'string')))
    errs.push(`${at}: UNVERIFIED invalid required`);
  if (schema.enum !== undefined && (!Array.isArray(schema.enum) || !schema.enum.length)) errs.push(`${at}: UNVERIFIED invalid enum`);
  if (schema.format !== undefined && !formats.has(schema.format)) errs.push(`${at}: UNVERIFIED unsupported format ${schema.format}`);
  if (schema.pattern !== undefined) {
    try {
      if (typeof schema.pattern !== 'string' || /\(\?|\\[pPkK]|\\[1-9]/.test(schema.pattern)) throw Error();
      new RegExp(schema.pattern, 'u');
    } catch { errs.push(`${at}: UNVERIFIED unsupported/invalid pattern`); }
  }
  for (const key of ['allOf', 'oneOf', 'anyOf']) if (schema[key] !== undefined) {
    if (!Array.isArray(schema[key]) || !schema[key].length) errs.push(`${at}: UNVERIFIED invalid ${key}`);
    else schema[key].forEach((s: Schema, i: number) => errs.push(...schemaIssues(s, `${at}.${key}[${i}]`, depth + 1)));
  }
  if (schema.properties !== undefined) {
    if (!schema.properties || typeof schema.properties !== 'object' || Array.isArray(schema.properties)) errs.push(`${at}: UNVERIFIED invalid properties`);
    else for (const [key, sub] of Object.entries(schema.properties)) errs.push(...schemaIssues(sub as Schema, `${at}.${key}`, depth + 1));
  }
  for (const key of ['items', 'not', 'additionalProperties']) if (schema[key] !== undefined) errs.push(...schemaIssues(schema[key], `${at}.${key}`, depth + 1));
  return errs;
}
function equal(a: unknown, b: unknown): boolean {
  if (Array.isArray(a) !== Array.isArray(b)) return false;
  if (Array.isArray(a) && Array.isArray(b)) return a.length === b.length && a.every((v, i) => equal(v, b[i]));
  if (a && b && typeof a === 'object' && typeof b === 'object') {
    const aa = a as Record<string, unknown>, bb = b as Record<string, unknown>;
    return Object.keys(aa).length === Object.keys(bb).length && Object.keys(aa).every(k => Object.hasOwn(bb, k) && equal(aa[k], bb[k]));
  }
  return a === b;
}
function formatOK(v: string, format: string): boolean {
  switch (format) {
    case 'email': return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v);
    case 'uuid': return /^[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}$/i.test(v);
    case 'date': return /^\d{4}-\d{2}-\d{2}$/.test(v) && !Number.isNaN(Date.parse(v)) && new Date(v).toISOString().slice(0, 10) === v;
    case 'date-time': return /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$/.test(v) && !Number.isNaN(Date.parse(v));
    case 'uri': try { return !!new URL(v).protocol && !/\s/.test(v); } catch { return false; }
    default: return true; // numeric/password formats are annotations in this subset
  }
}
function multiple(value: number, divisor: number): boolean {
  function fraction(n: number): [bigint, number] {
    const [mantissa, exponent = '0'] = String(n).toLowerCase().split('e');
    return [BigInt(mantissa.replace('.', '')), Number(exponent) - (mantissa.split('.')[1]?.length ?? 0)];
  }
  const [v, ve] = fraction(value), [d, de] = fraction(divisor), diff = ve - de;
  return diff >= 0 ? (v * 10n ** BigInt(diff)) % d === 0n : v % (d * 10n ** BigInt(-diff)) === 0n;
}

/** [] = validated within the documented subset. Unsupported rules return UNVERIFIED.
 * Error messages omit instance values. Not a full JSON Schema validator.
 */
export function checkSchema(value: unknown, schema: Schema, at = '$', depth = 0): string[] {
  const issues = schemaIssues(schema, at);
  if (issues.length) return issues;
  if (depth > 30) return [`${at}: UNVERIFIED instance depth limit`];
  if (typeof schema === 'boolean') return schema ? [] : [`${at}: false schema`];
  const errs: string[] = [];
  for (const key of ['allOf', 'anyOf', 'oneOf']) if (schema[key]) {
    const count = schema[key].filter((s: Schema) => checkSchema(value, s, at, depth + 1).length === 0).length;
    if (key === 'allOf' && count !== schema[key].length || key === 'anyOf' && count === 0 || key === 'oneOf' && count !== 1)
      errs.push(`${at}: ${key} matched ${count}/${schema[key].length} branches`);
  }
  if (schema.not !== undefined && !checkSchema(value, schema.not, at, depth + 1).length) errs.push(`${at}: matches forbidden schema`);
  const actual = value === null ? 'null' : Array.isArray(value) ? 'array' : typeof value === 'number' && Number.isInteger(value) ? 'integer' : typeof value;
  const types = Array.isArray(schema.type) ? [...schema.type] : schema.type ? [schema.type] : [];
  if (schema.nullable && types.length) types.push('null');
  if (types.length && !types.some((t: string) => t === actual || t === 'number' && actual === 'integer')) errs.push(`${at}: wrong type`);
  if (schema.enum && !schema.enum.some((v: unknown) => equal(value, v))) errs.push(`${at}: not in enum`);
  if (Object.hasOwn(schema, 'const') && !equal(value, schema.const)) errs.push(`${at}: const mismatch`);
  if (typeof value === 'number') {
    if (!Number.isFinite(value) || Number.isInteger(value) && !Number.isSafeInteger(value)) errs.push(`${at}: UNVERIFIED unsafe/non-finite JSON number`);
    if (schema.minimum !== undefined && value < schema.minimum) errs.push(`${at}: below minimum`);
    if (schema.maximum !== undefined && value > schema.maximum) errs.push(`${at}: above maximum`);
    const lo = schema.exclusiveMinimum === true ? schema.minimum : typeof schema.exclusiveMinimum === 'number' ? schema.exclusiveMinimum : undefined;
    const hi = schema.exclusiveMaximum === true ? schema.maximum : typeof schema.exclusiveMaximum === 'number' ? schema.exclusiveMaximum : undefined;
    if (lo !== undefined && value <= lo) errs.push(`${at}: outside exclusiveMinimum`);
    if (hi !== undefined && value >= hi) errs.push(`${at}: outside exclusiveMaximum`);
    if (schema.multipleOf !== undefined && Number.isFinite(value) && !multiple(value, schema.multipleOf)) errs.push(`${at}: not multipleOf`);
  }
  if (typeof value === 'string') {
    const length = [...value].length;
    if (schema.minLength !== undefined && length < schema.minLength) errs.push(`${at}: shorter than minLength`);
    if (schema.maxLength !== undefined && length > schema.maxLength) errs.push(`${at}: longer than maxLength`);
    if (schema.pattern !== undefined && !new RegExp(schema.pattern, 'u').test(value)) errs.push(`${at}: pattern mismatch`);
    if (schema.format !== undefined && !formatOK(value, schema.format)) errs.push(`${at}: format mismatch`);
  }
  if (actual === 'object' && value) {
    const obj = value as Record<string, unknown>, props = schema.properties ?? {};
    for (const key of schema.required ?? []) if (!Object.hasOwn(obj, key) && !props[key]?.writeOnly) errs.push(`${at}.${key}: required property missing`);
    const size = Object.keys(obj).length;
    if (schema.minProperties !== undefined && size < schema.minProperties || schema.maxProperties !== undefined && size > schema.maxProperties) errs.push(`${at}: property count outside bounds`);
    for (const [key, v] of Object.entries(obj)) {
      if (Object.hasOwn(props, key)) errs.push(...checkSchema(v, props[key], `${at}.${key}`, depth + 1));
      else if (schema.additionalProperties !== undefined) errs.push(...checkSchema(v, schema.additionalProperties, `${at}.${key}`, depth + 1));
    }
  }
  if (Array.isArray(value)) {
    if (schema.minItems !== undefined && value.length < schema.minItems || schema.maxItems !== undefined && value.length > schema.maxItems) errs.push(`${at}: item count outside bounds`);
    if (schema.uniqueItems && value.some((v, i) => value.slice(0, i).some(old => equal(v, old)))) errs.push(`${at}: duplicate array items`);
    if (schema.items !== undefined) value.forEach((v, i) => errs.push(...checkSchema(v, schema.items, `${at}[${i}]`, depth + 1)));
  }
  return errs;
}
