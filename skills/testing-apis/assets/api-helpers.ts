// QA Suite API test helpers (copy next to the generated api-contract.spec.ts). No extra dependencies.
import { test } from '@playwright/test';
import type { APIRequestContext, APIResponse } from '@playwright/test';

// 127.0.0.1 rather than localhost: on Windows, localhost may resolve to ::1 while the server listens on IPv4 only.
const BASE = process.env.API_BASE_URL ?? 'http://127.0.0.1:3000';

/** auth: false sends no token · as: 'other' uses API_TOKEN_OTHER (second test user, for BOLA/BFLA) · token overrides both. */
type Opts = { body?: unknown; auth?: boolean; as?: 'main' | 'other'; token?: string; headers?: Record<string, string> };

/** Send a request: {name} placeholders in `path` are filled from `params`, the rest become the query string. */
export async function api(request: APIRequestContext, method: string, path: string,
                          params: Record<string, unknown> = {}, opts: Opts = {}): Promise<APIResponse> {
  let url = path;
  const query: Record<string, string> = {};
  for (const [k, v] of Object.entries(params)) {
    if (url.includes(`{${k}}`)) url = url.replace(`{${k}}`, encodeURIComponent(String(v)));
    else if (v !== undefined && v !== null) query[k] = String(v);
  }
  const headers: Record<string, string> = { 'Content-Type': 'application/json', ...(opts.headers ?? {}) };
  const token = opts.token ?? (opts.as === 'other' ? process.env.API_TOKEN_OTHER : process.env.API_TOKEN);
  if (opts.as === 'other' && !token) throw new Error('API_TOKEN_OTHER is not set (second test user needed for this test)');
  if (opts.auth !== false && token) headers.Authorization = `Bearer ${token}`;
  const sendBody = opts.body !== undefined && opts.body !== null && !['GET', 'DELETE', 'HEAD'].includes(method);
  const res = await request.fetch(BASE + url, { method, headers, params: query, data: sendBody ? opts.body : undefined });
  if (process.env.API_EVIDENCE !== 'off') await attachEvidence(method, BASE + url, query, sendBody ? opts.body : undefined, headers, res);
  return res;
}

/** Attach request + response to the test report (evidence for defect reports). Tokens are masked. API_EVIDENCE=off disables it. */
async function attachEvidence(method: string, url: string, query: Record<string, string>, body: unknown,
                              headers: Record<string, string>, res: APIResponse): Promise<void> {
  let info;
  try { info = test.info(); } catch { return; } // called outside a test (e.g. global setup)
  let text = '';
  try { text = (await res.text()).slice(0, 4000); } catch { /* body not readable */ }
  const auth = headers.Authorization;
  const masked = auth ? auth.replace(/(\S+\s+)?(\S{4})\S*/, (_m, scheme = '', head) => `${scheme}${head}…`) : 'none';
  const evidence = { request: { method, url, query, headers: { ...headers, Authorization: masked }, body },
                     response: { status: res.status(), headers: res.headers(), body: text } };
  await info.attach(`${method} ${url} -> ${res.status()}`, { body: JSON.stringify(evidence, null, 2), contentType: 'application/json' });
}

type Schema = {
  type?: string | string[]; nullable?: boolean; required?: string[]; properties?: Record<string, Schema>;
  items?: Schema; enum?: unknown[]; minimum?: number; maximum?: number; minLength?: number; maxLength?: number;
  oneOf?: Schema[]; anyOf?: Schema[]; format?: string; pattern?: string;
};

function typeOf(v: unknown): string {
  if (v === null) return 'null';
  if (Array.isArray(v)) return 'array';
  if (typeof v === 'number') return Number.isInteger(v) ? 'integer' : 'number';
  return typeof v;
}

/** Minimal JSON-schema check for OpenAPI response schemas. Returns a list of violations (empty = valid). */
export function checkSchema(value: unknown, schema: Schema, at = '$'): string[] {
  if (!schema) return [];
  const alts = schema.oneOf ?? schema.anyOf;
  if (alts) return alts.some(s => checkSchema(value, s, at).length === 0) ? [] : [`${at}: matches none of oneOf/anyOf`];
  const errs: string[] = [];
  const types = Array.isArray(schema.type) ? schema.type : schema.type ? [schema.type] : [];
  const actual = typeOf(value);
  if (value === null && (schema.nullable || types.includes('null'))) return [];
  if (types.length && !types.some(t => t === actual || (t === 'number' && actual === 'integer'))) {
    return [`${at}: expected ${types.join('|')}, got ${actual} (${JSON.stringify(value)?.slice(0, 40)})`];
  }
  if (schema.enum && !schema.enum.includes(value)) errs.push(`${at}: ${JSON.stringify(value)} not in enum`);
  if (typeof value === 'number') {
    if (schema.minimum !== undefined && value < schema.minimum) errs.push(`${at}: ${value} < minimum ${schema.minimum}`);
    if (schema.maximum !== undefined && value > schema.maximum) errs.push(`${at}: ${value} > maximum ${schema.maximum}`);
  }
  if (typeof value === 'string') {
    if (schema.minLength !== undefined && value.length < schema.minLength) errs.push(`${at}: shorter than ${schema.minLength}`);
    if (schema.maxLength !== undefined && value.length > schema.maxLength) errs.push(`${at}: longer than ${schema.maxLength}`);
    if (schema.pattern !== undefined && !new RegExp(schema.pattern, 'u').test(value)) errs.push(`${at}: ${JSON.stringify(value)} does not match ${schema.pattern}`);
  }
  if (actual === 'object' && value) {
    const obj = value as Record<string, unknown>;
    for (const r of schema.required ?? []) if (!(r in obj)) errs.push(`${at}.${r}: required property missing`);
    for (const [k, s] of Object.entries(schema.properties ?? {})) if (k in obj) errs.push(...checkSchema(obj[k], s, `${at}.${k}`));
  }
  if (actual === 'array' && schema.items) (value as unknown[]).forEach((v, i) => errs.push(...checkSchema(v, schema.items!, `${at}[${i}]`)));
  return errs;
}
