// QA Suite – tests the contract cannot express (authorisation, business rules, state, error model).
// Designed per testing-apis step 3 / references/api-testing.md. Same TC IDs as qa/test-cases.src.md.
// Env: API_BASE_URL, API_TOKEN (alice: A-100 TRY, A-101 EUR), API_TOKEN_OTHER (bob: B-200 TRY). Test accounts only.
// State budget: every accepted transfer here is 1–10.10 TRY except TC-032 (rejected when correct).
import { test, expect } from '@playwright/test';
import type { APIRequestContext } from '@playwright/test';
import { api, checkSchema } from './api-helpers';

const IBAN_EXT = 'TR330006100519786457841326';
const ERROR_SCHEMA = { type: 'object', required: ['code', 'message'], properties: { code: { type: 'string' }, message: { type: 'string' } } };
const valid = (over: Record<string, unknown> = {}) =>
  ({ fromAccountId: 'A-100', toIban: IBAN_EXT, amount: 1, currency: 'TRY', description: 'QA', ...over });

async function balanceOf(request: APIRequestContext, id: string, as: 'main' | 'other' = 'main'): Promise<number> {
  const res = await api(request, 'GET', '/accounts', {}, { body: null, as });
  expect(res.status()).toBe(200);
  const acc = (await res.json()).find((a: { id: string }) => a.id === id);
  expect(acc, `account ${id} not in caller's list`).toBeTruthy();
  return Number(acc.balance);
}

test.describe('Yetkilendirme (BOLA / kimlik doğrulama)', () => {
  test('TC-030 POST /transfers başka müşterinin hesabından (fromAccountId) transfer 403 ile reddedilir', { tag: ['@TC-030', '@api', '@security'] }, async ({ request }) => {
    const before = await balanceOf(request, 'B-200', 'other');
    const res = await api(request, 'POST', '/transfers', {}, { body: valid({ fromAccountId: 'B-200', description: 'TC-030' }) });
    const after = await balanceOf(request, 'B-200', 'other');
    expect(res.status(), await res.text()).toBe(403);
    expect(after).toBe(before);
  });
  test('TC-031 GET /accounts yalnızca çağıranın hesaplarını döner', { tag: ['@TC-031', '@api', '@security'] }, async ({ request }) => {
    const a = await (await api(request, 'GET', '/accounts', {}, { body: null })).json();
    const b = await (await api(request, 'GET', '/accounts', {}, { body: null, as: 'other' })).json();
    const aIds = a.map((x: { id: string }) => x.id), bIds = b.map((x: { id: string }) => x.id);
    expect(aIds.filter((id: string) => bIds.includes(id))).toEqual([]);
  });
  test('TC-032 GET /accounts değiştirilmiş (tampered) token ile 401 döner', { tag: ['@TC-032', '@api', '@security'] }, async ({ request }) => {
    const res = await api(request, 'GET', '/accounts', {}, { body: null, token: (process.env.API_TOKEN ?? '') + 'x' });
    expect(res.status()).toBe(401);
  });
});

test.describe('İş kuralları ve durum (POST /transfers)', () => {
  test('TC-033 Bakiyeyi aşan transfer reddedilir ve bakiye değişmez', { tag: ['@TC-033', '@api'] }, async ({ request }) => {
    const before = await balanceOf(request, 'B-200', 'other');
    const amount = Math.min(50000, Math.floor(before) + 1);
    const res = await api(request, 'POST', '/transfers', {}, { body: valid({ fromAccountId: 'B-200', amount, description: 'TC-033' }), as: 'other' });
    const after = await balanceOf(request, 'B-200', 'other');
    expect([400, 409, 422], `amount ${amount} > balance ${before}: ${await res.text()}`).toContain(res.status());
    expect(after).toBe(before);
  });
  test('TC-034 Başarılı transfer kaynak bakiyeyi tam tutar kadar düşürür', { tag: ['@TC-034', '@api'] }, async ({ request }) => {
    const before = await balanceOf(request, 'A-100');
    const res = await api(request, 'POST', '/transfers', {}, { body: valid({ amount: 10.1, description: 'TC-034' }) });
    expect(res.ok(), await res.text()).toBe(true); // 2xx; the exact 201 is TC-008's job
    const after = await balanceOf(request, 'A-100');
    expect(Math.round((before - after) * 100) / 100).toBe(10.1);
  });
  test('TC-035 Hesap para birimiyle uyuşmayan currency reddedilir (EUR hesap, TRY transfer)', { tag: ['@TC-035', '@api'] }, async ({ request }) => {
    const before = await balanceOf(request, 'A-101');
    const res = await api(request, 'POST', '/transfers', {}, { body: valid({ fromAccountId: 'A-101', currency: 'TRY', description: 'TC-035' }) });
    const after = await balanceOf(request, 'A-101');
    expect([400, 422], await res.text()).toContain(res.status());
    expect(after).toBe(before);
  });
  test('TC-036 toIban deseni (^TR[0-9]{24}$) dışındaki IBAN 400 ile reddedilir', { tag: ['@TC-036', '@api'] }, async ({ request }) => {
    for (const toIban of ['TR12345', 'DE89370400440532013000', 'TR33000610051978645784132X']) {
      const res = await api(request, 'POST', '/transfers', {}, { body: valid({ toIban, description: 'TC-036' }) });
      expect.soft(res.status(), `${toIban}: ${await res.text()}`).toBe(400);
    }
  });
  test('TC-037 Var olmayan fromAccountId ile transfer 4xx döner (201/500 değil)', { tag: ['@TC-037', '@api'] }, async ({ request }) => {
    const res = await api(request, 'POST', '/transfers', {}, { body: valid({ fromAccountId: 'A-999', description: 'TC-037' }) });
    expect([400, 403, 404, 422], await res.text()).toContain(res.status());
  });
  test('TC-038 Negatif tutar (-100) reddedilir', { tag: ['@TC-038', '@api'] }, async ({ request }) => {
    const res = await api(request, 'POST', '/transfers', {}, { body: valid({ amount: -100, description: 'TC-038' }) });
    expect(res.status(), await res.text()).toBe(400);
  });
  test('TC-039 Salt okunur alanlar (id, status) istemciden atanamaz (mass assignment)', { tag: ['@TC-039', '@api', '@security'] }, async ({ request }) => {
    const res = await api(request, 'POST', '/transfers', {}, { body: { ...valid({ description: 'TC-039' }), id: 'T-HACK-1', status: 'REJECTED' } });
    if (res.ok()) {
      const t = await res.json();
      expect.soft(t.id, 'client-supplied id applied').not.toBe('T-HACK-1');
      expect.soft(t.status, 'client-supplied status applied').not.toBe('REJECTED');
    } else {
      expect([400, 422]).toContain(res.status());
    }
  });
  test('TC-040 Tutar sayısal string ("100") olarak gönderilince reddedilir', { tag: ['@TC-040', '@api'] }, async ({ request }) => {
    const res = await api(request, 'POST', '/transfers', {}, { body: valid({ amount: '100', description: 'TC-040' }) });
    expect(res.status(), await res.text()).toBe(400);
  });
});

test.describe('Hata modeli', () => {
  test('TC-041 Doğrulama hatası dokümante Error şemasında ({code, message}) döner', { tag: ['@TC-041', '@api'] }, async ({ request }) => {
    const res = await api(request, 'POST', '/transfers', {}, { body: valid({ amount: 0.5, description: 'TC-041' }) });
    expect(res.status()).toBe(400);
    expect(checkSchema(await res.json(), ERROR_SCHEMA)).toEqual([]);
  });
  test('TC-042 Bozuk JSON gövdesi 400 döner (500 değil)', { tag: ['@TC-042', '@api'] }, async ({ request }) => {
    const res = await request.fetch((process.env.API_BASE_URL ?? '') + '/transfers', {
      method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${process.env.API_TOKEN}` }, data: '{"fromAccountId": "A-100", "amount": ',
    });
    const body = await res.text();
    test.info().annotations.push({ type: 'http', description: `POST /transfers [auth: Bearer <redacted>] {malformed JSON} -> ${res.status()} ${body.slice(0, 300)}` });
    expect(res.status(), body).toBe(400);
    expect(body).not.toMatch(/at .*\.js:\d+|SyntaxError: /);
  });
});
