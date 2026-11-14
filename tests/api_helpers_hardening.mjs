// Execute the actual distributed TypeScript, replacing only Playwright's test-info boundary.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { stripTypeScriptTypes } from 'node:module';
import test from 'node:test';
const attachments = [];
globalThis.__qaTest = { info: () => ({ attach: async (name, data) => attachments.push({ name, ...data }) }) };
const source = readFileSync(new URL('../skills/testing-apis/assets/api-helpers.ts', import.meta.url), 'utf8')
  .replace("import { test } from '@playwright/test';", 'const test = globalThis.__qaTest;');
const js = stripTypeScriptTypes(source, { mode: 'strip' });
const helpers = await import(`data:text/javascript;base64,${Buffer.from(js).toString('base64')}`);
const check = helpers.checkSchema;

test('independent JSON Schema Test Suite expected outcomes (69 fixtures)', () => {
  const groups = JSON.parse(readFileSync(new URL('./fixtures/api-hardening/schema-oracle.json', import.meta.url), 'utf8'));
  for (const group of groups) for (const fixture of group.tests) {
    const errors = check(fixture.data, group.schema);
    assert.equal(errors.length === 0, fixture.valid, `${group.description}: ${fixture.description}: ${errors}`);
  }
});

test('oneOf means exactly one; sibling constraints still apply', () => {
  assert.ok(check(4, { oneOf: [{ type: 'number' }, { type: 'integer' }] }).length);
  assert.ok(check('long', { anyOf: [{ type: 'string' }], maxLength: 2 }).length);
  assert.deepEqual(check('ok', { allOf: [{ type: 'string' }, { minLength: 2 }] }), []);
  assert.ok(check('x', { allOf: [{ type: 'string' }, { minLength: 2 }] }).length);
});
test('arrays, numbers, unicode lengths, const, deep enum and closed objects', () => {
  for (const [value, schema] of [
    [[1], { type: 'array', minItems: 2 }], [[1, 1], { uniqueItems: true }],
    [0, { type: 'number', minimum: 0, exclusiveMinimum: true }], [5, { exclusiveMinimum: 5 }],
    [.3, { multipleOf: .2 }], [{ a: 1 }, { additionalProperties: false }],
    [2, { const: 1 }], [null, { type: ['string', 'null'], enum: ['x'] }],
  ]) assert.ok(check(value, schema).length, JSON.stringify({ value, schema }));
  assert.deepEqual(check('😀', { type: 'string', maxLength: 1 }), []);
  assert.deepEqual(check({ a: 1 }, { enum: [{ a: 1 }] }), []);
});
test('unknown rules, unresolved refs and malformed regex cannot silently pass', () => {
  for (const schema of [{ unevaluatedProperties: false }, { $ref: 'elsewhere.json' }, { pattern: '[' }]) {
    assert.match(check('x', schema).join(' '), /unverified/i);
  }
});

test('deep enum equality distinguishes arrays from objects', () => {
  assert.ok(check([], { enum: [{}] }).length);
  assert.ok(check({}, { const: [] }).length);
  assert.deepEqual(check([], { enum: [[]] }), []);
});

const SENTINEL = 'SECRET_SENTINEL_83d17';
const response = (text, contentType = 'application/json') => ({
  status: () => 200, headers: () => ({ 'content-type': contentType, 'Set-Cookie': SENTINEL, 'X-Api-Key': SENTINEL }),
  text: async () => text,
});
async function evidence(body, contentType = 'application/json') {
  attachments.length = 0;
  await helpers.api({ fetch: async () => response(body, contentType) }, 'POST',
    `/login?access_token=${SENTINEL}`, { token: SENTINEL }, {
      token: SENTINEL, headers: { authorization: SENTINEL, 'X-Api-Key': SENTINEL, Cookie: SENTINEL },
      body: { profile: { password: SENTINEL }, sessionToken: SENTINEL },
    });
  return JSON.stringify(attachments);
}
test('evidence redacts query, URL/title, case-insensitive headers and nested JSON', async () => {
  process.env.API_EVIDENCE_ALLOW_FIELDS = 'ok,pad,nested.0.safe,message,password';
  assert.ok(!(await evidence(JSON.stringify({ nested: [{ refresh_token: SENTINEL }], ok: 1 }))).includes(SENTINEL));
});
test('evidence sanitizes before truncation and omits malformed / binary / free text', async () => {
  for (const [body, type] of [
    [JSON.stringify({ pad: 'x'.repeat(5000), password: SENTINEL }), 'application/json'],
    [`password=${SENTINEL}&safe=1`, 'application/x-www-form-urlencoded'],
    [`{"password":"${SENTINEL}`, 'application/json'],
    [SENTINEL, 'application/octet-stream'], [SENTINEL, 'text/plain'],
  ]) assert.ok(!(await evidence(body, type)).includes(SENTINEL), type);
});
test('known secrets echoed under allowlisted innocent names are scrubbed', async () => {
  process.env.API_EVIDENCE_ALLOW_FIELDS = 'message';
  assert.ok(!(await evidence(JSON.stringify({ message: `echo ${SENTINEL}` }))).includes(SENTINEL));
  delete process.env.API_EVIDENCE_ALLOW_FIELDS;
});
