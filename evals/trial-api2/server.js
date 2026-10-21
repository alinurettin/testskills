'use strict';
/*
 * Anadolu Güven Sigorta - Poliçe & Hasar API (kurgusal / fictional)
 * Node.js 24 built-ins only. In-memory state (restart = reset).
 * PORT ortam değişkeninden okunur (varsayılan 3000).
 *
 * EVALUATOR NOTE: This file is the system-under-test. It intentionally
 * contains planted defects. Do NOT hand this file to the agent under test.
 */

const http = require('node:http');
const { URL } = require('node:url');

const PORT = parseInt(process.env.PORT || '3000', 10);

// ---------------------------------------------------------------------------
// Auth: bearer tokens -> users (two normal users + one admin)
// ---------------------------------------------------------------------------
const TOKENS = {
  'tok_user1_ayse': { userId: 'u1', name: 'Ayşe Yılmaz', role: 'user' },
  'tok_user2_mehmet': { userId: 'u2', name: 'Mehmet Demir', role: 'user' },
  'tok_admin_root': { userId: 'admin', name: 'Sistem Yöneticisi', role: 'admin' },
};

// ---------------------------------------------------------------------------
// Seed data (synthetic). TCKN values are intentionally checksum-INVALID.
// ---------------------------------------------------------------------------
function seed() {
  const policies = [
    { id: 'pol_1', policyNumber: 'POL-2026-0001', ownerUserId: 'u1', holderName: 'Ayşe Yılmaz',  holderTckn: '11111111110', coverageType: 'kasko',   premium: 1500, coverageLimit: 50000,  status: 'active',    agentName: 'Zeynep Kaya', startDate: '2026-01-01', endDate: '2026-12-31' },
    { id: 'pol_2', policyNumber: 'POL-2026-0002', ownerUserId: 'u1', holderName: 'Ayşe Yılmaz',  holderTckn: '11111111110', coverageType: 'konut',   premium: 2400, coverageLimit: 100000, status: 'active',    agentName: null,          startDate: '2026-02-15', endDate: '2027-02-14' },
    { id: 'pol_3', policyNumber: 'POL-2026-0003', ownerUserId: 'u2', holderName: 'Mehmet Demir', holderTckn: '22222222220', coverageType: 'saglik',  premium: 900,  coverageLimit: 20000,  status: 'cancelled', agentName: 'Can Öz',      startDate: '2026-01-10', endDate: '2026-07-10' },
    { id: 'pol_4', policyNumber: 'POL-2026-0004', ownerUserId: 'u2', holderName: 'Mehmet Demir', holderTckn: '22222222220', coverageType: 'kasko',   premium: 3200, coverageLimit: 150000, status: 'active',    agentName: 'Zeynep Kaya', startDate: '2026-03-01', endDate: '2027-02-28' },
    { id: 'pol_5', policyNumber: 'POL-2026-0005', ownerUserId: 'u1', holderName: 'Ayşe Yılmaz',  holderTckn: '11111111110', coverageType: 'trafik',  premium: 1800, coverageLimit: 75000,  status: 'active',    agentName: null,          startDate: '2026-04-01', endDate: '2027-03-31' },
  ];
  const claims = [
    { id: 'clm_1', claimNumber: 'CLM-2026-0001', policyId: 'pol_1', ownerUserId: 'u1', amount: 12000, status: 'submitted', description: 'Çarpma hasarı',       createdAt: '2026-05-02T09:00:00Z' },
    { id: 'clm_2', claimNumber: 'CLM-2026-0002', policyId: 'pol_1', ownerUserId: 'u1', amount: 8000,  status: 'rejected',  description: 'Cam kırığı',          createdAt: '2026-05-10T11:30:00Z' },
    { id: 'clm_3', claimNumber: 'CLM-2026-0003', policyId: 'pol_2', ownerUserId: 'u1', amount: 3000,  status: 'approved',  description: 'Su baskını',          createdAt: '2026-06-01T08:15:00Z' },
    { id: 'clm_4', claimNumber: 'CLM-2026-0004', policyId: 'pol_5', ownerUserId: 'u1', amount: 15000, status: 'submitted', description: 'Trafik kazası',       createdAt: '2026-06-20T14:45:00Z' },
    { id: 'clm_5', claimNumber: 'CLM-2026-0005', policyId: 'pol_2', ownerUserId: 'u1', amount: 2000,  status: 'submitted', description: 'Hırsızlık',           createdAt: '2026-07-03T16:05:00Z' },
    { id: 'clm_6', claimNumber: 'CLM-2026-0006', policyId: 'pol_4', ownerUserId: 'u2', amount: 5000,  status: 'approved',  description: 'Çarpma hasarı',       createdAt: '2026-05-18T10:20:00Z' },
    { id: 'clm_7', claimNumber: 'CLM-2026-0007', policyId: 'pol_3', ownerUserId: 'u2', amount: 1000,  status: 'rejected',  description: 'Muayene masrafı',     createdAt: '2026-06-11T13:00:00Z' },
  ];
  return { policies, claims };
}

let db = seed();
let claimCounter = 7; // next created claim -> clm_8

// ---------------------------------------------------------------------------
// Serializers
// ---------------------------------------------------------------------------
function serializePolicy(p) {
  return {
    id: p.id,
    policyNumber: p.policyNumber,
    ownerUserId: p.ownerUserId,
    holderName: p.holderName,
    holderTckn: p.holderTckn,
    coverageType: p.coverageType,
    premium: p.premium,
    coverageLimit: p.coverageLimit,
    status: p.status,
    agentName: p.agentName === undefined ? null : p.agentName, // 3.1 nullable
    startDate: p.startDate,
    endDate: p.endDate,
  };
}

// NOTE: claimNumber is intentionally OMITTED from the serialized output,
// although the OpenAPI Claim schema marks it as required. (planted mismatch)
function serializeClaim(c) {
  return {
    id: c.id,
    policyId: c.policyId,
    ownerUserId: c.ownerUserId,
    amount: c.amount,
    status: c.status,
    description: c.description,
    createdAt: c.createdAt,
  };
}

// ---------------------------------------------------------------------------
// HTTP helpers
// ---------------------------------------------------------------------------
function sendJson(res, status, obj) {
  const body = JSON.stringify(obj);
  res.writeHead(status, { 'Content-Type': 'application/json; charset=utf-8' });
  res.end(body);
}

function readBody(req) {
  return new Promise((resolve, reject) => {
    let raw = '';
    req.on('data', (ch) => { raw += ch; });
    req.on('end', () => resolve(raw));
    req.on('error', reject);
  });
}

function authenticate(req) {
  const h = req.headers['authorization'] || '';
  const m = /^Bearer\s+(.+)$/i.exec(h.trim());
  if (!m) return null;
  return TOKENS[m[1]] || null;
}

// ---------------------------------------------------------------------------
// Router
// ---------------------------------------------------------------------------
const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, `http://localhost:${PORT}`);
  const path = url.pathname;
  const method = req.method;

  // Public health check (no auth)
  if (method === 'GET' && path === '/health') {
    return sendJson(res, 200, { status: 'ok', service: 'anadolu-guven-sigorta-api' });
  }

  // All other endpoints require a valid bearer token.
  const user = authenticate(req);
  if (!user) {
    return sendJson(res, 401, { error: 'Yetkisiz', message: 'Geçerli bir bearer token gerekli.' });
  }

  // --- GET /policies : caller's own policies (admin -> all) -----------------
  if (method === 'GET' && path === '/policies') {
    const list = user.role === 'admin'
      ? db.policies
      : db.policies.filter((p) => p.ownerUserId === user.userId);
    return sendJson(res, 200, list.map(serializePolicy));
  }

  // --- GET/PATCH /policies/{id} ---------------------------------------------
  let m;
  if ((m = /^\/policies\/([^/]+)$/.exec(path))) {
    const id = m[1];
    const policy = db.policies.find((p) => p.id === id);
    if (!policy) return sendJson(res, 404, { error: 'Bulunamadı', message: 'Poliçe bulunamadı.' });

    const canAccess = user.role === 'admin' || policy.ownerUserId === user.userId;
    if (!canAccess) return sendJson(res, 403, { error: 'Erişim engellendi', message: 'Bu poliçeye erişim yetkiniz yok.' });

    if (method === 'GET') {
      return sendJson(res, 200, serializePolicy(policy));
    }

    if (method === 'PATCH') {
      const raw = await readBody(req);
      let body;
      try {
        body = raw ? JSON.parse(raw) : {};
      } catch (err) {
        // (planted) over-verbose error handler leaks internals
        return sendJson(res, 400, { error: 'Geçersiz JSON', detail: err.message, stack: err.stack });
      }
      // Contract: owner may edit only holderName and agentName.
      // (planted) 'status' is wrongly writable here; premium/coverageLimit/
      // ownerUserId are correctly ignored.
      const WRITABLE = ['holderName', 'agentName', 'status'];
      for (const k of WRITABLE) {
        if (Object.prototype.hasOwnProperty.call(body, k)) policy[k] = body[k];
      }
      return sendJson(res, 200, serializePolicy(policy));
    }

    return sendJson(res, 405, { error: 'Yöntem desteklenmiyor' });
  }

  // --- GET /claims : paginated; own claims, OR by policyId ------------------
  if (method === 'GET' && path === '/claims') {
    const policyId = url.searchParams.get('policyId');
    const page = parseInt(url.searchParams.get('page') || '1', 10);
    const pageSize = parseInt(url.searchParams.get('pageSize') || '20', 10);

    let items;
    if (policyId) {
      // (planted) ownership scope is dropped when policyId is provided:
      // any authenticated user can read claims of a policy they do not own.
      items = db.claims.filter((c) => c.policyId === policyId);
    } else if (user.role === 'admin') {
      items = db.claims;
    } else {
      items = db.claims.filter((c) => c.ownerUserId === user.userId);
    }

    const start = (page - 1) * pageSize;
    const pageItems = items.slice(start, start + pageSize);

    return sendJson(res, 200, {
      data: pageItems.map(serializeClaim),
      // (planted) meta.total returns the CURRENT PAGE length, not the
      // filtered total across all pages.
      meta: { page, pageSize, total: pageItems.length },
    });
  }

  // --- GET /claims/{id} -----------------------------------------------------
  if ((m = /^\/claims\/([^/]+)$/.exec(path)) && method === 'GET') {
    const id = m[1];
    const claim = db.claims.find((c) => c.id === id);
    if (!claim) return sendJson(res, 404, { error: 'Bulunamadı', message: 'Hasar talebi bulunamadı.' });
    const canAccess = user.role === 'admin' || claim.ownerUserId === user.userId;
    if (!canAccess) return sendJson(res, 403, { error: 'Erişim engellendi', message: 'Bu hasar talebine erişim yetkiniz yok.' });
    return sendJson(res, 200, serializeClaim(claim));
  }

  // --- POST /claims : create a claim ----------------------------------------
  if (method === 'POST' && path === '/claims') {
    const raw = await readBody(req);
    let body;
    try {
      body = raw ? JSON.parse(raw) : {};
    } catch (err) {
      // (planted) over-verbose error handler leaks internals
      return sendJson(res, 400, { error: 'Geçersiz JSON', detail: err.message, stack: err.stack });
    }

    // Basic presence/type validation (these ARE enforced -> correct behaviour)
    if (body.policyId === undefined || body.amount === undefined) {
      return sendJson(res, 400, { error: 'Eksik alan', message: 'policyId ve amount zorunludur.' });
    }
    if (typeof body.amount !== 'number' || Number.isNaN(body.amount)) {
      return sendJson(res, 400, { error: 'Geçersiz tip', message: 'amount sayısal olmalıdır.' });
    }

    const policy = db.policies.find((p) => p.id === body.policyId);
    if (!policy) {
      return sendJson(res, 404, { error: 'Bulunamadı', message: 'Poliçe bulunamadı.' });
    }
    // Ownership on create IS enforced (path/body cross-owner create blocked).
    if (user.role !== 'admin' && policy.ownerUserId !== user.userId) {
      return sendJson(res, 403, { error: 'Erişim engellendi', message: 'Bu poliçe için hasar talebi oluşturamazsınız.' });
    }

    // (planted) amount minimum (>=1) documented but NOT enforced.
    // (planted) business rule "amount <= coverageLimit" documented but NOT enforced.
    // (planted) Idempotency-Key header documented but IGNORED -> duplicates.

    claimCounter += 1;
    const newClaim = {
      id: 'clm_' + claimCounter,
      claimNumber: 'CLM-2026-' + String(claimCounter).padStart(4, '0'),
      policyId: body.policyId,
      ownerUserId: user.userId,
      amount: body.amount,
      status: 'submitted',
      description: typeof body.description === 'string' ? body.description : '',
      createdAt: '2026-08-01T00:00:00Z',
    };
    db.claims.push(newClaim);

    // (planted) returns 200 instead of documented 201 on creation.
    return sendJson(res, 200, serializeClaim(newClaim));
  }

  // --- GET /admin/policies : correctly admin-protected (contrast) -----------
  if (method === 'GET' && path === '/admin/policies') {
    if (user.role !== 'admin') {
      return sendJson(res, 403, { error: 'Erişim engellendi', message: 'Yönetici yetkisi gerekli.' });
    }
    return sendJson(res, 200, db.policies.map(serializePolicy));
  }

  // --- GET /admin/stats : (planted) function-level authz MISSING ------------
  if (method === 'GET' && path === '/admin/stats') {
    // BUG: no role check -> any authenticated user can read aggregates.
    const totalPremium = db.policies.reduce((s, p) => s + p.premium, 0);
    return sendJson(res, 200, {
      totalPolicies: db.policies.length,
      totalClaims: db.claims.length,
      totalPremium,
    });
  }

  return sendJson(res, 404, { error: 'Bulunamadı', message: 'Kaynak yok.' });
});

server.listen(PORT, () => {
  // eslint-disable-next-line no-console
  console.log(`Anadolu Güven Sigorta API dinlemede: http://localhost:${PORT} (PORT=${PORT})`);
});
