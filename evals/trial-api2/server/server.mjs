// Çam Yuvası Sipariş ve İade API 1.4.0 — DEĞERLENDİRME TEST ORTAMI (kurgusal şirket, sentetik veri)
// Yalnızca Node.js 24 yerleşik modülleri. Durum bellekte tutulur (yeniden başlatma = sıfırlama).
// Port: PORT ortam değişkeni (varsayılan 4802). Bu dosya test edilen ajana VERİLMEZ.
import http from 'node:http';

const PORT = Number.parseInt(process.env.PORT ?? '4802', 10);
const VERSION = '1.4.0';
const T0 = Date.now();
const HOUR = 3600_000;
const DAY = 24 * HOUR;
const iso = (ms) => new Date(ms).toISOString();
const PROBLEM_BASE = 'https://api.camyuvasi.example.test/problems/';

// ---------- para yardımcıları (kuruş, tam sayı) ----------
const toK = (tl) => Math.round(tl * 100);
const toTL = (k) => k / 100;
const halfUpDiv = (num, den) => Math.floor((2 * num + den) / (2 * den)); // num, den >= 0

const COUPONS = { YUVA10: { percent: 10 } };
const SHIPPING_FEE_K = 4990;
const FREE_SHIPPING_THRESHOLD_K = 50000;
const RETURN_WINDOW_MS = 14 * DAY;

// ---------- kullanıcılar / token'lar (sentetik) ----------
const USERS = {
  'u-101': { id: 'u-101', fullName: 'Ayşe Demirtaş', email: 'ayse.demirtas@example.com', role: 'customer', defaultRefundIban: 'TR659990100000123456789012' },
  'u-102': { id: 'u-102', fullName: 'Mehmet Özkan', email: 'mehmet.ozkan@example.com', role: 'customer', defaultRefundIban: 'TR869990100000987654321098' },
  'u-103': { id: 'u-103', fullName: 'Zeynep Arıkan', email: 'zeynep.arikan@example.com', role: 'customer', defaultRefundIban: null },
  'u-104': { id: 'u-104', fullName: 'Caner Bulut', email: 'caner.bulut@example.com', role: 'customer', defaultRefundIban: null },
  'u-900': { id: 'u-900', fullName: 'Selin Aydoğan', email: 'selin.aydogan@example.com', role: 'admin', defaultRefundIban: null },
};
const TOKENS = {
  cy_test_ayse_5d1f2c: 'u-101',
  cy_test_mehmet_8a7e44: 'u-102',
  cy_test_admin_3c9b10: 'u-900',
};

// ---------- ürünler ----------
const PRODUCTS = new Map();
[
  ['CY-1001', 'Döküm Tava 28 cm', 'Mutfak', 844.60, 40, true],
  ['CY-1002', "Bambu Kesme Tahtası Seti (3'lü)", 'Mutfak', 389.95, 60, true],
  ['CY-1003', 'Çelik Termos 750 ml', 'Mutfak', 459.90, 35, true],
  ['CY-1004', "Cam Saklama Kabı Seti (5'li)", 'Mutfak', 279.50, 80, true],
  ['CY-1005', 'Seramik Kupa İkili Set', 'Mutfak', 189.90, 120, true],
  ['CY-1006', 'Bakır Cezve No:3', 'Mutfak', 329.00, 25, true],
  ['CY-2001', "Pamuklu Havlu Seti (4'lü)", 'Banyo', 549.00, 50, true],
  ['CY-2002', 'Şal Yaka Bornoz (L)', 'Banyo', 899.90, 20, true],
  ['CY-2003', 'Kaymaz Banyo Paspası', 'Banyo', 219.99, 70, true],
  ['CY-2004', 'Mermer Görünümlü Sabunluk', 'Banyo', 129.50, 90, true],
  ['CY-3001', 'Örgü Battaniye 130x170', 'Yatak Odası', 749.00, 30, true],
  ['CY-3002', 'Saten Nevresim Takımı (Çift Kişilik)', 'Yatak Odası', 1299.00, 15, true],
  ['CY-3003', 'Yün Yastık 50x70', 'Yatak Odası', 419.00, 45, true],
  ['CY-3004', 'Şişme Yatak (Tek Kişilik)', 'Yatak Odası', 999.00, 0, false],
  ['CY-3005', 'Ahşap Ayaklı Gece Lambası', 'Yatak Odası', 574.25, 28, true],
  ['CY-4001', 'Lavanta Kokulu Mum Seti', 'Dekorasyon', 159.90, 100, true],
  ['CY-4002', 'Ahşap Duvar Saati 40 cm', 'Dekorasyon', 489.00, 18, true],
  ['CY-4003', 'Hasır Sepet (Büyük)', 'Dekorasyon', 349.90, 22, true],
  ['CY-4004', "Fotoğraf Çerçevesi Seti (6'lı)", 'Dekorasyon', 399.00, 3, true],
  ['CY-4005', 'Seramik Saksı (Orta Boy)', 'Dekorasyon', 260.00, 40, true],
  ['CY-4006', 'Mini Kristal Avize', 'Dekorasyon', 1890.00, 0, false],
  ['CY-5001', 'Su Geçirmez Bahçe Minderi', 'Bahçe', 299.90, 55, true],
].forEach(([sku, name, category, price, stock, active]) => {
  PRODUCTS.set(sku, { sku, name, category, priceK: toK(price), stock, active });
});

function priceOrder(lines, couponCode) {
  const subtotalK = lines.reduce((s, l) => s + l.priceK * l.quantity, 0);
  const discountK = couponCode ? halfUpDiv(subtotalK * COUPONS[couponCode].percent, 100) : 0;
  const shippingK = subtotalK - discountK >= FREE_SHIPPING_THRESHOLD_K ? 0 : SHIPPING_FEE_K;
  return { subtotalK, discountK, shippingK, totalK: subtotalK - discountK + shippingK };
}

// ---------- siparişler ----------
const ADDR = {
  'u-101': { fullName: 'Ayşe Demirtaş', line1: 'Örnek Mah. Deneme Sk. No:7 D:3', district: 'Kadıköy', city: 'İstanbul', postalCode: '34000' },
  'u-102': { fullName: 'Mehmet Özkan', line1: 'Kurgu Cad. No:12/4', district: 'Çankaya', city: 'Ankara', postalCode: '06000' },
  'u-103': { fullName: 'Zeynep Arıkan', line1: 'Hayal Sk. No:3', district: 'Karşıyaka', city: 'İzmir', postalCode: '35000' },
  'u-104': { fullName: 'Caner Bulut', line1: 'Taslak Bulvarı No:45', district: 'Nilüfer', city: 'Bursa', postalCode: '16000' },
};
const ORDERS = new Map();
const RETURNS = new Map();
let nextOrderNo = 164;
let nextReturnNo = 22;

function buildOrder({ id, userId, status, lines, coupon = null, createdMs, deliveredMs = null, tracking, note = null, address }) {
  const ls = lines.map(([sku, quantity]) => {
    const p = PRODUCTS.get(sku);
    return { sku, name: p.name, priceK: p.priceK, quantity };
  });
  const pr = priceOrder(ls, coupon);
  const o = {
    id,
    userId,
    status,
    items: ls.map((l) => ({ sku: l.sku, name: l.name, unitPrice: toTL(l.priceK), quantity: l.quantity, lineTotal: toTL(l.priceK * l.quantity) })),
    subtotal: toTL(pr.subtotalK),
    couponCode: coupon,
    discountAmount: toTL(pr.discountK),
    shippingFee: toTL(pr.shippingK),
    totalAmount: toTL(pr.totalK),
    shippingAddress: structuredClone(address ?? ADDR[userId]),
    note,
    createdAt: iso(createdMs),
    deliveredAt: deliveredMs == null ? null : iso(deliveredMs),
  };
  if (tracking) o.cargoTrackingNo = tracking;
  return o;
}

[
  { id: 'SIP-2026-000117', userId: 'u-101', status: 'DELIVERED', lines: [['CY-3001', 1]], createdMs: T0 - 26 * DAY, deliveredMs: T0 - 20 * DAY, tracking: 'CY-KRG-7781203' },
  { id: 'SIP-2026-000121', userId: 'u-103', status: 'DELIVERED', lines: [['CY-5001', 2]], createdMs: T0 - 22 * DAY, deliveredMs: T0 - 18 * DAY, tracking: 'CY-KRG-7782410' },
  { id: 'SIP-2026-000126', userId: 'u-102', status: 'CANCELLED', lines: [['CY-4003', 1]], createdMs: T0 - 18 * DAY },
  { id: 'SIP-2026-000133', userId: 'u-101', status: 'CANCELLED', lines: [['CY-1005', 2]], createdMs: T0 - 15 * DAY, note: 'Yanlışlıkla iki kez sipariş verdim.' },
  { id: 'SIP-2026-000138', userId: 'u-102', status: 'DELIVERED', lines: [['CY-3002', 1], ['CY-2003', 1]], createdMs: T0 - 9 * DAY, deliveredMs: T0 - 5 * DAY, tracking: 'CY-KRG-7786044' },
  { id: 'SIP-2026-000141', userId: 'u-101', status: 'DELIVERED', lines: [['CY-1001', 1], ['CY-1002', 1]], coupon: 'YUVA10', createdMs: T0 - 7 * DAY, deliveredMs: T0 - 3 * DAY, tracking: 'CY-KRG-7787391' },
  { id: 'SIP-2026-000144', userId: 'u-104', status: 'SHIPPED', lines: [['CY-2002', 1], ['CY-2004', 2]], createdMs: T0 - 4 * DAY, tracking: 'CY-KRG-7788120' },
  { id: 'SIP-2026-000149', userId: 'u-101', status: 'DELIVERED', lines: [['CY-2001', 2], ['CY-4001', 1]], createdMs: T0 - 10 * DAY, deliveredMs: T0 - 6 * DAY, tracking: 'CY-KRG-7785502' },
  { id: 'SIP-2026-000152', userId: 'u-101', status: 'SHIPPED', lines: [['CY-1003', 1]], createdMs: T0 - 3 * DAY, tracking: 'CY-KRG-7790455' },
  { id: 'SIP-2026-000155', userId: 'u-102', status: 'DELIVERED', lines: [['CY-1006', 1], ['CY-4002', 1]], createdMs: T0 - 6 * DAY, deliveredMs: T0 - 2 * DAY, tracking: 'CY-KRG-7789917' },
  { id: 'SIP-2026-000158', userId: 'u-101', status: 'CREATED', lines: [['CY-1004', 1]], createdMs: T0 - 1 * DAY, note: 'Kapıcıya bırakılabilir.' },
  { id: 'SIP-2026-000160', userId: 'u-102', status: 'PAID', lines: [['CY-2002', 1]], createdMs: T0 - 20 * HOUR },
  { id: 'SIP-2026-000161', userId: 'u-103', status: 'PAID', lines: [['CY-3003', 2]], createdMs: T0 - 12 * HOUR },
  { id: 'SIP-2026-000163', userId: 'u-101', status: 'PAID', lines: [['CY-4005', 2]], coupon: 'YUVA10', createdMs: T0 - 5 * HOUR },
].forEach((spec) => ORDERS.set(spec.id, buildOrder(spec)));

function seedReturn({ id, orderId, userId, status, lines, reason, createdMs, decidedMs = null, note = null, decisionNote = null }) {
  const order = ORDERS.get(orderId);
  const items = lines.map(([sku, quantity]) => {
    const it = order.items.find((i) => i.sku === sku);
    return { sku, name: it.name, quantity, unitPrice: it.unitPrice };
  });
  const grossK = items.reduce((s, i) => s + toK(i.unitPrice) * i.quantity, 0);
  const subK = toK(order.subtotal);
  const discK = toK(order.discountAmount);
  const refundK = grossK - (discK ? halfUpDiv(discK * grossK, subK) : 0);
  RETURNS.set(id, {
    id, orderId, userId, customerName: USERS[userId].fullName, status, reason, items,
    refundAmount: toTL(refundK), refundIban: USERS[userId].defaultRefundIban ?? 'TR659990100000123456789012',
    note, decisionNote, createdAt: iso(createdMs), decidedAt: decidedMs == null ? null : iso(decidedMs),
  });
}
seedReturn({ id: 'RET-2026-000015', orderId: 'SIP-2026-000117', userId: 'u-101', status: 'APPROVED', lines: [['CY-3001', 1]], reason: 'NOT_AS_DESCRIBED', createdMs: T0 - 19 * DAY, decidedMs: T0 - 17 * DAY, note: 'Renk fotoğraftakinden farklı.', decisionNote: 'Ürün depoya ulaştı, iade onaylandı.' });
seedReturn({ id: 'RET-2026-000021', orderId: 'SIP-2026-000138', userId: 'u-102', status: 'REQUESTED', lines: [['CY-3002', 1]], reason: 'DAMAGED', createdMs: T0 - 1 * DAY, note: 'Nevresimin dikişi sökük geldi.' });
// u-103 için IBAN'sız kullanıcıya iade tohumlanmaz.

// ---------- görünümler ----------
function orderView(o) {
  return {
    id: o.id,
    userId: o.userId,
    status: o.status,
    items: Array.isArray(o.items) ? o.items.map((i) => ({ ...i })) : o.items,
    subtotal: o.subtotal,
    couponCode: o.couponCode ?? null,
    discountAmount: o.discountAmount,
    shippingFee: o.shippingFee,
    totalAmount: o.totalAmount,
    shippingAddress: o.shippingAddress,
    note: o.note ?? null,
    cargoTrackingNo: o.cargoTrackingNo,
    createdAt: o.createdAt,
    deliveredAt: o.deliveredAt ?? null,
  };
}
const productView = (p) => ({ sku: p.sku, name: p.name, category: p.category, price: toTL(p.priceK), stock: p.stock, active: p.active });
const returnView = (r) => ({ ...r, items: r.items.map((i) => ({ ...i })) });

// ---------- HTTP yardımcıları ----------
function send(res, status, body, headers = {}, type = 'application/json; charset=utf-8') {
  const payload = body === undefined ? '' : JSON.stringify(body);
  res.writeHead(status, { 'Content-Type': type, 'Cache-Control': 'no-store', ...headers });
  res.end(payload);
}
function problem(res, status, code, title, detail, extra = {}, headers = {}) {
  send(res, status, { type: PROBLEM_BASE + code.toLowerCase().replace(/_/g, '-'), title, status, code, detail, ...extra }, headers, 'application/problem+json; charset=utf-8');
}
function validationProblem(res, errors) {
  problem(res, 400, 'VALIDATION_ERROR', 'Geçersiz istek', 'İstek sözleşmeye uymuyor.', { errors });
}

class BodyTooLarge extends Error {}
class MalformedJson extends Error {
  constructor(cause) { super(cause.message); this.cause = cause; }
}
function readBody(req) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    let size = 0;
    req.on('data', (c) => {
      size += c.length;
      if (size > 1024 * 1024) { reject(new BodyTooLarge()); req.destroy(); return; }
      chunks.push(c);
    });
    req.on('end', () => resolve(Buffer.concat(chunks).toString('utf8')));
    req.on('error', reject);
  });
}
async function jsonBody(req) {
  const raw = await readBody(req);
  if (raw.trim() === '') return undefined;
  try {
    return JSON.parse(raw);
  } catch (e) {
    throw new MalformedJson(e);
  }
}

const isObj = (v) => v !== null && typeof v === 'object' && !Array.isArray(v);
const cpLen = (s) => [...s].length;
function strField(v, field, min, max, errs, { optional = false, nullable = false } = {}) {
  if (v === undefined) { if (!optional) errs.push({ field, message: 'zorunlu alan' }); return; }
  if (v === null) { if (!nullable) errs.push({ field, message: 'null olamaz' }); return; }
  if (typeof v !== 'string') { errs.push({ field, message: 'metin olmalıdır' }); return; }
  const n = cpLen(v);
  if (n < min || n > max) errs.push({ field, message: `uzunluk ${min}-${max} karakter olmalıdır` });
}
function unknownKeys(obj, allowed, prefix, errs) {
  for (const k of Object.keys(obj)) if (!allowed.includes(k)) errs.push({ field: prefix + k, message: 'tanımsız alan' });
}
function validateAddress(a, field, errs) {
  if (!isObj(a)) { errs.push({ field, message: 'nesne olmalıdır' }); return; }
  unknownKeys(a, ['fullName', 'line1', 'district', 'city', 'postalCode'], field + '.', errs);
  strField(a.fullName, field + '.fullName', 3, 100, errs);
  strField(a.line1, field + '.line1', 5, 200, errs);
  strField(a.district, field + '.district', 2, 60, errs);
  strField(a.city, field + '.city', 2, 60, errs);
  if (typeof a.postalCode !== 'string' || !/^[0-9]{5}$/.test(a.postalCode)) errs.push({ field: field + '.postalCode', message: '5 haneli posta kodu olmalıdır' });
}
function ibanValid(iban) {
  if (typeof iban !== 'string' || !/^TR[0-9]{24}$/.test(iban)) return false;
  const re = iban.slice(4) + iban.slice(0, 4);
  const digits = re.replace(/[A-Z]/g, (c) => String(c.charCodeAt(0) - 55));
  let rem = 0;
  for (const ch of digits) rem = (rem * 10 + (ch.charCodeAt(0) - 48)) % 97;
  return rem === 1;
}
function intParam(raw, def, min, max, field, errs) {
  if (raw === null) return def;
  if (!/^[0-9]+$/.test(raw)) { errs.push({ field, message: 'tam sayı olmalıdır' }); return def; }
  const n = Number(raw);
  if (n < min || n > max) { errs.push({ field, message: `${min}-${max} aralığında olmalıdır` }); return def; }
  return n;
}
function paging(q, defSize, errs) {
  const page = intParam(q.get('page'), 1, 1, 100000, 'page', errs);
  const size = intParam(q.get('size'), defSize, 1, 50, 'size', errs);
  return { page, size };
}
function pageOf(list, page, size, total = list.length) {
  const start = (page - 1) * size;
  return { items: list.slice(start, start + size), page, size, total, totalPages: Math.ceil(total / size) };
}

const ORDER_STATUSES = ['CREATED', 'PAID', 'SHIPPED', 'DELIVERED', 'CANCELLED'];
const RETURN_STATUSES = ['REQUESTED', 'APPROVED', 'REJECTED'];
const RETURN_REASONS = ['DAMAGED', 'WRONG_ITEM', 'NOT_AS_DESCRIBED', 'CHANGED_MIND'];
const byCreatedDesc = (a, b) => (a.createdAt < b.createdAt ? 1 : a.createdAt > b.createdAt ? -1 : a.id < b.id ? 1 : -1);

// ---------- kimlik doğrulama ----------
function authenticate(req) {
  const h = req.headers.authorization;
  if (!h) return null;
  const m = /^Bearer\s+(\S+)$/i.exec(h.trim());
  if (!m) return null;
  const uid = TOKENS[m[1]];
  return uid ? USERS[uid] : null;
}
const WWW_AUTH = { 'WWW-Authenticate': 'Bearer realm="camyuvasi"' };
const unauthorized = (res) => problem(res, 401, 'UNAUTHORIZED', 'Kimlik doğrulama gerekli', 'Geçerli bir Bearer token gönderilmelidir.', {}, WWW_AUTH);
const forbidden = (res) => problem(res, 403, 'FORBIDDEN', 'Yetkisiz işlem', 'Bu işlem yalnızca yönetici rolüne açıktır.');

// ---------- işleyiciler ----------
function listProducts(req, res, ctx) {
  const errs = [];
  const { page, size } = paging(ctx.q, 20, errs);
  if (errs.length) return validationProblem(res, errs);
  const category = ctx.q.get('category');
  const matching = [...PRODUCTS.values()].filter((p) => category === null || p.category === category).sort((a, b) => (a.sku < b.sku ? -1 : 1));
  const listable = matching.filter((p) => p.active);
  const pg = pageOf(listable, page, size, matching.length);
  send(res, 200, { ...pg, items: pg.items.map(productView) });
}

function getProduct(req, res, ctx) {
  const p = PRODUCTS.get(ctx.params[0]);
  if (!p) return problem(res, 404, 'PRODUCT_NOT_FOUND', 'Ürün bulunamadı', `${ctx.params[0]} SKU'lu ürün yok.`);
  send(res, 200, productView(p));
}

function getMe(req, res, ctx) {
  const u = ctx.user;
  send(res, 200, { id: u.id, fullName: u.fullName, email: u.email, role: u.role, defaultRefundIban: u.defaultRefundIban });
}

function listOrders(req, res, ctx) {
  const errs = [];
  const { page, size } = paging(ctx.q, 10, errs);
  const status = ctx.q.get('status');
  if (status !== null && !ORDER_STATUSES.includes(status)) errs.push({ field: 'status', message: 'geçersiz durum' });
  if (errs.length) return validationProblem(res, errs);
  const list = [...ORDERS.values()].filter((o) => o.userId === ctx.user.id && (status === null || o.status === status)).sort(byCreatedDesc);
  const pg = pageOf(list, page, size);
  send(res, 200, { ...pg, items: pg.items.map(orderView) });
}

function ownOrder(res, ctx, id) {
  const o = ORDERS.get(id);
  if (!o || o.userId !== ctx.user.id) {
    problem(res, 404, 'ORDER_NOT_FOUND', 'Sipariş bulunamadı', `${id} numaralı sipariş bulunamadı.`);
    return null;
  }
  return o;
}

function getOrder(req, res, ctx) {
  const o = ownOrder(res, ctx, ctx.params[0]);
  if (o) send(res, 200, orderView(o));
}

async function createOrder(req, res, ctx) {
  const key = req.headers['idempotency-key'];
  if (key === undefined) return problem(res, 400, 'IDEMPOTENCY_KEY_REQUIRED', 'Idempotency-Key eksik', 'Sipariş oluşturma isteklerinde Idempotency-Key başlığı zorunludur.');
  if (!/^[A-Za-z0-9_-]{8,64}$/.test(key)) return problem(res, 400, 'IDEMPOTENCY_KEY_INVALID', 'Idempotency-Key geçersiz', 'Anahtar 8-64 karakter; harf, rakam, "-" veya "_" olmalıdır.');
  const body = await jsonBody(req);
  const errs = [];
  if (!isObj(body)) return validationProblem(res, [{ field: '', message: 'gövde JSON nesnesi olmalıdır' }]);
  unknownKeys(body, ['items', 'couponCode', 'shippingAddress', 'note'], '', errs);
  if (!Array.isArray(body.items) || body.items.length < 1 || body.items.length > 20) {
    errs.push({ field: 'items', message: '1-20 elemanlı dizi olmalıdır' });
  } else {
    const seen = new Set();
    body.items.forEach((it, i) => {
      const f = `items[${i}]`;
      if (!isObj(it)) { errs.push({ field: f, message: 'nesne olmalıdır' }); return; }
      unknownKeys(it, ['sku', 'quantity'], f + '.', errs);
      if (typeof it.sku !== 'string' || !/^CY-[0-9]{4}$/.test(it.sku)) errs.push({ field: f + '.sku', message: 'CY-0000 biçiminde olmalıdır' });
      else if (seen.has(it.sku)) errs.push({ field: f + '.sku', message: 'aynı SKU birden fazla satırda gönderilemez' });
      else seen.add(it.sku);
      if (!Number.isInteger(it.quantity) || it.quantity < 1 || it.quantity > 20) errs.push({ field: f + '.quantity', message: 'quantity 1 ile 20 arasında bir tam sayı olmalıdır' });
    });
  }
  strField(body.couponCode, 'couponCode', 1, 20, errs, { optional: true, nullable: true });
  if (body.shippingAddress === undefined) errs.push({ field: 'shippingAddress', message: 'zorunlu alan' });
  else validateAddress(body.shippingAddress, 'shippingAddress', errs);
  strField(body.note, 'note', 0, 250, errs, { optional: true, nullable: true });
  if (errs.length) return validationProblem(res, errs);

  const coupon = body.couponCode ?? null;
  if (coupon !== null && !COUPONS[coupon]) return problem(res, 422, 'COUPON_INVALID', 'Kupon geçersiz', `${coupon} kodlu geçerli bir kupon yok.`);
  const lines = [];
  for (const it of body.items) {
    const p = PRODUCTS.get(it.sku);
    if (!p) return problem(res, 422, 'UNKNOWN_SKU', 'Ürün bulunamadı', `${it.sku} SKU'lu ürün yok.`);
    if (!p.active) return problem(res, 422, 'PRODUCT_INACTIVE', 'Ürün satışta değil', `${it.sku} pasif durumda ve sipariş edilemez.`);
    if (p.stock < it.quantity) return problem(res, 409, 'OUT_OF_STOCK', 'Yetersiz stok', `${it.sku} için stok yetersiz (mevcut: ${p.stock}).`);
    lines.push({ p, quantity: it.quantity });
  }
  for (const l of lines) l.p.stock -= l.quantity;
  const id = `SIP-2026-${String(nextOrderNo++).padStart(6, '0')}`;
  const o = buildOrder({ id, userId: ctx.user.id, status: 'CREATED', lines: lines.map((l) => [l.p.sku, l.quantity]), coupon, createdMs: Date.now(), note: body.note ?? null, address: body.shippingAddress });
  ORDERS.set(id, o);
  send(res, 201, orderView(o), { Location: `/v1/orders/${id}` });
}

const NO_ASSIGN = new Set(['id', 'userId', 'createdAt', '__proto__', 'constructor', 'prototype']);
async function patchOrder(req, res, ctx) {
  const body = await jsonBody(req);
  const o = ownOrder(res, ctx, ctx.params[0]);
  if (!o) return;
  if (!isObj(body)) return validationProblem(res, [{ field