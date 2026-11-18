'use strict';
/*
 * Turna Oto Kiralama - Rezervasyon ve Kiralama API (kurgusal / fictional)
 * Node.js 24 built-ins only. In-memory state, deterministic seed (restart = reset).
 * Port: env PORT (default 3210).
 *
 * EVALUATOR NOTE: this file is the system under test of trial-api3. It contains
 * sixteen planted defects (K1..K16, each marked "PLANTED Kn" below and described
 * in evals/keys/api3.md). Do NOT hand this file to the agent under test.
 *
 * Evaluator-only switch: env API3_PLANTED=off starts a contract-correct reference
 * server (all planted defects disabled). Never use it for an agent run.
 *
 * The server runs on a FIXED simulated clock (NOW below); nothing depends on the
 * real date or time. Error responses never contain stack traces or file paths.
 */

const http = require('node:http');

const PORT = Number.parseInt(process.env.PORT || '3210', 10);
const DEFECTS_ON = String(process.env.API3_PLANTED || 'on').toLowerCase() !== 'off';
const PLANTED = {};
for (let i = 1; i <= 16; i += 1) PLANTED['K' + i] = DEFECTS_ON;

// ---------------------------------------------------------------------------
// Time helpers (fixed clock, Turkey time = UTC+03:00 all year)
// ---------------------------------------------------------------------------
const HOUR = 3600 * 1000;
const DAY = 24 * HOUR;
const TZ = 3 * HOUR;
const BUFFER = 2 * HOUR;

function pad(n, w) { return String(n).padStart(w || 2, '0'); }

function validYMD(y, m, d) {
  if (m < 1 || m > 12 || d < 1) return false;
  const leap = y % 4 === 0 && (y % 100 !== 0 || y % 400 === 0);
  const dim = [31, leap ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][m - 1];
  return d <= dim;
}

function utcMs(y, mo, d, h, mi, s, ms) {
  const dt = new Date(0);
  dt.setUTCFullYear(y, mo - 1, d);
  dt.setUTCHours(h, mi, s, ms);
  return dt.getTime();
}

// RFC 3339 date-time with mandatory offset -> epoch ms, or null.
function parseDateTime(s) {
  if (typeof s !== 'string' || s.length > 40) return null;
  const m = /^(\d{4})-(\d{2})-(\d{2})[Tt](\d{2}):(\d{2}):(\d{2})(?:\.(\d{1,9}))?(?:([Zz])|([+-])(\d{2}):(\d{2}))$/.exec(s);
  if (!m) return null;
  const y = Number(m[1]); const mo = Number(m[2]); const d = Number(m[3]);
  const h = Number(m[4]); const mi = Number(m[5]); const se = Number(m[6]);
  if (!validYMD(y, mo, d) || h > 23 || mi > 59 || se > 59) return null;
  const frac = m[7] ? Number((m[7] + '00').slice(0, 3)) : 0;
  let off = 0;
  if (!m[8]) {
    const oh = Number(m[10]); const om = Number(m[11]);
    if (oh > 23 || om > 59) return null;
    off = (oh * 60 + om) * 60000 * (m[9] === '-' ? -1 : 1);
  }
  return utcMs(y, mo, d, h, mi, se, frac) - off;
}

function fmtDateTime(ms) {
  const d = new Date(ms + TZ);
  const f = d.getUTCMilliseconds();
  return pad(d.getUTCFullYear(), 4) + '-' + pad(d.getUTCMonth() + 1) + '-' + pad(d.getUTCDate())
    + 'T' + pad(d.getUTCHours()) + ':' + pad(d.getUTCMinutes()) + ':' + pad(d.getUTCSeconds())
    + (f ? '.' + pad(f, 3) : '') + '+03:00';
}

function parseDate(s) {
  if (typeof s !== 'string') return null;
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(s);
  if (!m || !validYMD(Number(m[1]), Number(m[2]), Number(m[3]))) return null;
  return s;
}

function localDate(ms) { return fmtDateTime(ms).slice(0, 10); }

function utcDate(ms) {
  const d = new Date(ms);
  return pad(d.getUTCFullYear(), 4) + '-' + pad(d.getUTCMonth() + 1) + '-' + pad(d.getUTCDate());
}

// Completed years between two calendar dates (anniversary day counts as completed).
function fullYears(from, to) {
  const a = from.split('-').map(Number);
  const b = to.split('-').map(Number);
  let n = b[0] - a[0];
  if (b[1] < a[1] || (b[1] === a[1] && b[2] < a[2])) n -= 1;
  return n;
}

const NOW = parseDateTime('2026-03-10T09:00:00+03:00');

// ---------------------------------------------------------------------------
// Money helpers (integer kurus internally, TL numbers in JSON)
// ---------------------------------------------------------------------------
function tl(k) { return k / 100; }
// percent of an amount, rounded half-up to the kurus
function pct(amountK, percent) { return Math.floor((amountK * percent * 2 + 100) / 200); }
// PLANTED K16: VAT is truncated to the kurus instead of rounded half-up.
function vatOf(subtotalK) {
  return PLANTED.K16 ? Math.floor((subtotalK * 20) / 100) : pct(subtotalK, 20);
}

// ---------------------------------------------------------------------------
// Static data
// ---------------------------------------------------------------------------
const USERS = new Map([
  ['tok_musteri_elif', { id: 'mus_1', name: 'Elif Aksoy', role: 'customer' }],
  ['tok_musteri_baran', { id: 'mus_2', name: 'Baran Çetin', role: 'customer' }],
  ['tok_personel_ist', { id: 'per_1', name: 'Deniz Korkmaz', role: 'staff', branchId: 'IST' }],
  ['tok_yonetici', { id: 'yon_1', name: 'Sistem Yöneticisi', role: 'admin' }],
]);

const BRANCHES = ['ANK', 'IST', 'IZM'];
const CLASSES = ['ekonomi', 'orta', 'suv', 'premium'];
const TRANSMISSIONS = ['manuel', 'otomatik'];
const EXTRAS = ['cocuk_koltugu', 'navigasyon', 'ek_surucu', 'tam_koruma'];
const RES_STATUSES = ['confirmed', 'active', 'completed', 'cancelled'];
const INV_STATUSES = ['issued', 'void'];

const LINE_TEXT = {
  kiralama: 'Kiralama bedeli',
  sure_indirimi: 'Uzun süre indirimi',
  kupon_indirimi: 'Kupon indirimi',
  cocuk_koltugu: 'Çocuk koltuğu',
  navigasyon: 'Navigasyon cihazı',
  ek_surucu: 'Ek sürücü',
  tam_koruma: 'Tam koruma paketi',
  genc_surucu: 'Genç sürücü bedeli',
  tek_yon: 'Tek yön bedeli',
  gecikme: 'Gecikme bedeli',
  asim_km: 'Kilometre aşım bedeli',
  yakit: 'Eksik yakıt bedeli',
  hasar: 'Hasar bedeli',
};

function seedVehicles() {
  const v = (id, make, model, cls, transmission, seats, branchId, rateK, kmK, status) => (
    { id, make, model, class: cls, transmission, seats, branchId, rateK, kmK, status });
  return [
    v('arc_01', 'Fiat', 'Egea', 'ekonomi', 'manuel', 5, 'IST', 115000, 350, 'available'),
    v('arc_02', 'Renault', 'Megane', 'orta', 'otomatik', 5, 'IST', 145000, 400, 'available'),
    v('arc_03', 'Dacia', 'Duster', 'suv', 'manuel', 5, 'IST', 189000, 500, 'available'),
    v('arc_04', 'Volvo', 'S90', 'premium', 'otomatik', 5, 'IST', 329999, 900, 'available'),
    v('arc_05', 'Hyundai', 'i20', 'ekonomi', 'otomatik', 5, 'IST', 118745, 350, 'available'),
    v('arc_06', 'Ford', 'Tourneo', 'suv', 'manuel', 7, 'IST', 210000, 550, 'maintenance'),
    v('arc_07', 'Renault', 'Clio', 'ekonomi', 'manuel', 5, 'ANK', 109000, 350, 'available'),
    v('arc_08', 'Toyota', 'Corolla', 'orta', 'otomatik', 5, 'ANK', 152000, 400, 'available'),
    v('arc_09', 'Peugeot', '3008', 'suv', 'otomatik', 5, 'ANK', 225000, 550, 'available'),
    v('arc_10', 'Fiat', 'Egea', 'ekonomi', 'manuel', 5, 'IZM', 112000, 350, 'available'),
    v('arc_11', 'Volkswagen', 'Passat', 'orta', 'otomatik', 5, 'IZM', 167550, 450, 'available'),
    v('arc_12', 'Opel', 'Corsa', 'ekonomi', 'manuel', 5, 'IZM', 99000, 300, 'retired'),
  ];
}

const db = { vehicles: seedVehicles(), reservations: [], invoices: [], idem: new Map() };
let resSeq = 1000;
let invSeq = 5000;

function vehicleById(id) { return db.vehicles.find((v) => v.id === id) || null; }

// ---------------------------------------------------------------------------
// Errors
// ---------------------------------------------------------------------------
class ApiError extends Error {
  constructor(status, code, message, details, headers) {
    super(message);
    this.status = status;
    this.code = code;
    this.details = details;
    this.headers = headers;
  }
}
function fail(status, code, message, details, headers) {
  throw new ApiError(status, code, message, details, headers);
}
function bad(details) {
  fail(400, 'VALIDATION_ERROR', 'İstek doğrulanamadı.', Array.isArray(details) ? details : [details]);
}

// ---------------------------------------------------------------------------
// Pricing and business rules
// ---------------------------------------------------------------------------
function rentalDays(pickupMs, returnMs) {
  const d = returnMs - pickupMs;
  const full = Math.floor(d / DAY);
  const rem = d - full * DAY;
  return Math.max(1, full + (rem > HOUR ? 1 : 0));
}

function durationRateFor(days) { return days >= 14 ? 20 : days >= 7 ? 10 : 0; }

// in: { pickupMs, returnMs, returnBranchId, extras, couponCode, driverBirthDate }
// staleRate: when given, used instead of the rate that belongs to the day count.
function computePrice(v, inp, staleRate) {
  const days = rentalDays(inp.pickupMs, inp.returnMs);
  const base = days * v.rateK;
  const rate = staleRate === undefined ? durationRateFor(days) : staleRate;
  let durationDiscount = pct(base, rate);
  let couponDiscount = 0;
  if (inp.couponCode === 'BAHAR15') couponDiscount = pct(base, 15);
  else if (inp.couponCode === 'TURNA300') couponDiscount = 30000;
  if (durationDiscount > 0 && couponDiscount > 0) {
    if (couponDiscount > durationDiscount) durationDiscount = 0;
    else couponDiscount = 0;
  }
  const extras = [];
  for (const code of inp.extras) {
    if (code === 'cocuk_koltugu') extras.push({ code, amount: 12000 * Math.min(days, 7) });
    else if (code === 'navigasyon') extras.push({ code, amount: 9000 * days });
    else if (code === 'ek_surucu') extras.push({ code, amount: 15000 * days });
    else if (code === 'tam_koruma') extras.push({ code, amount: pct(base, 18) });
  }
  const extrasTotal = extras.reduce((s, e) => s + e.amount, 0);
  // PLANTED K5: the under-25 test of the young-driver fee uses the driver's age
  // on the server's "today" instead of the age on the pick-up day.
  const ageDay = PLANTED.K5 ? localDate(NOW) : localDate(inp.pickupMs);
  const youngDriverFee = fullYears(inp.driverBirthDate, ageDay) < 25 ? 20000 * Math.min(days, 10) : 0;
  const oneWayFee = inp.returnBranchId !== v.branchId ? 90000 : 0;
  const subtotal = base - durationDiscount - couponDiscount + extrasTotal + youngDriverFee + oneWayFee;
  const vat = vatOf(subtotal);
  return {
    durationRate: rate,
    price: {
      days, dailyRate: v.rateK, baseAmount: base, durationDiscount, couponDiscount,
      extras, extrasTotal, youngDriverFee, oneWayFee, subtotal, vat, total: subtotal + vat,
    },
  };
}

function isBlocked(vehicleId, pickupMs, returnMs, excludeId, statuses) {
  return db.reservations.some((o) => o.vehicleId === vehicleId && o.id !== excludeId
    && statuses.includes(o.status)
    && pickupMs < o.returnMs + BUFFER && o.pickupMs < returnMs + BUFFER);
}

// Validations shared by POST /quotes, POST /reservations and PATCH /reservations/{id}.
function checkBooking(inp, ctx) {
  const v = vehicleById(inp.vehicleId);
  if (!v) fail(404, 'VEHICLE_NOT_FOUND', 'Araç bulunamadı.');
  if (v.status !== 'available') fail(409, 'VEHICLE_OUT_OF_SERVICE', 'Araç şu anda kiralamaya açık değil.');
  if (inp.returnMs - inp.pickupMs < HOUR) fail(422, 'INVALID_PERIOD', 'Dönüş zamanı, alış zamanından en az 1 saat sonra olmalıdır.');
  if (inp.pickupMs - NOW < 2 * HOUR) fail(422, 'PICKUP_TOO_SOON', 'Alış zamanı en erken 2 saat sonrası olabilir.');
  if (inp.pickupMs - NOW > 90 * DAY) fail(422, 'PICKUP_TOO_FAR', 'Alış zamanı en geç 90 gün sonrası olabilir.');
  const days = rentalDays(inp.pickupMs, inp.returnMs);
  if (days > 30) fail(422, 'RENTAL_TOO_LONG', 'Kiralama süresi en fazla 30 gündür.');
  const pickupDay = localDate(inp.pickupMs);
  if (fullYears(inp.driverBirthDate, pickupDay) < 21) fail(422, 'DRIVER_TOO_YOUNG', 'Sürücü alış gününde 21 yaşını doldurmuş olmalıdır.');
  if (fullYears(inp.licenseIssuedOn, pickupDay) < 2) fail(422, 'LICENSE_TOO_NEW', 'Ehliyet alış gününde en az 2 yıllık olmalıdır.');
  if (inp.couponCode !== null) {
    if (inp.couponCode !== 'BAHAR15' && inp.couponCode !== 'TURNA300') fail(422, 'COUPON_INVALID', 'Kupon kodu geçersiz.');
    if (inp.couponCode === 'BAHAR15') {
      if (days < 3) fail(422, 'COUPON_NOT_APPLICABLE', 'BAHAR15 en az 3 günlük kiralamalarda geçerlidir.');
      // PLANTED K6: cancelled reservations still count as a use of BAHAR15.
      const used = db.reservations.some((o) => o.customerId === ctx.customerId && o.id !== ctx.excludeId
        && o.couponCode === 'BAHAR15' && (PLANTED.K6 || o.status !== 'cancelled'));
      if (used) fail(422, 'COUPON_ALREADY_USED', 'BAHAR15 kuponu bu müşteri tarafından daha önce kullanılmış.');
    } else if (days * v.rateK < 200000) {
      fail(422, 'COUPON_NOT_APPLICABLE', 'TURNA300 en az 2000 TL kiralama bedelinde geçerlidir.');
    }
  }
  // PLANTED K15: only `confirmed` reservations block the vehicle here; `active`
  // ones (car currently out on rental) are ignored. GET /vehicles is correct.
  const blocking = PLANTED.K15 ? ['confirmed'] : ['confirmed', 'active'];
  if (isBlocked(v.id, inp.pickupMs, inp.returnMs, ctx.excludeId, blocking)) {
    fail(409, 'VEHICLE_ALREADY_BOOKED', 'Araç bu zaman aralığında başka bir rezervasyon nedeniyle müsait değil.');
  }
  return v;
}

function buildInvoice(r, v, damageK, issuedMs) {
  const p = r.price;
  const pk = r.pickupRecord;
  const rt = r.returnRecord;
  const lines = [];
  const add = (code, amount) => { if (amount !== 0) lines.push({ code, description: LINE_TEXT[code], amount }); };
  add('kiralama', p.baseAmount);
  add('sure_indirimi', -p.durationDiscount);
  add('kupon_indirimi', -p.couponDiscount);
  for (const e of p.extras) add(e.code, e.amount);
  add('genc_surucu', p.youngDriverFee);
  add('tek_yon', p.oneWayFee);
  const late = rt.atMs - r.returnMs;
  let lateFee = 0;
  if (late > HOUR) {
    const started = Math.ceil(late / HOUR);
    // PLANTED K14: the cap is always ONE daily rate, also when the car is more
    // than 24 hours late (contract: one daily rate per started 24 hours).
    const capDays = PLANTED.K14 ? 1 : Math.ceil(late / DAY);
    lateFee = Math.min(pct(started * p.dailyRate, 10), capDays * p.dailyRate);
  }
  add('gecikme', lateFee);
  const excessKm = Math.max(0, rt.odometerKm - pk.odometerKm - 250 * p.days);
  add('asim_km', excessKm * v.kmK);
  add('yakit', Math.max(0, pk.fuelLevel - rt.fuelLevel) * 22000);
  add('hasar', r.extras.includes('tam_koruma') ? 0 : damageK);
  const subtotal = lines.reduce((s, l) => s + l.amount, 0);
  const vat = vatOf(subtotal);
  invSeq += 1;
  const inv = {
    id: 'fat_' + invSeq, reservationId: r.id, customerId: r.customerId, branchId: r.pickupBranchId,
    status: 'issued', issuedMs, lines, subtotal, vat, total: subtotal + vat,
  };
  db.invoices.push(inv);
  return inv;
}

// ---------------------------------------------------------------------------
// Seed (deterministic)
// ---------------------------------------------------------------------------
function seed() {
  const T = parseDateTime;
  const DRIVERS = {
    mus_1: ['1990-06-14', '2010-09-01'],
    mus_2: ['2001-03-20', '2020-07-15'],
    mus_3: ['1985-11-02', '2006-04-18'],
  };
  const mk = (customerId, vehicleId, pickupAt, returnAt, o) => {
    const opt = o || {};
    const v = vehicleById(vehicleId);
    const r = {
      id: 'rez_' + (resSeq += 1), customerId, vehicleId,
      pickupBranchId: v.branchId, returnBranchId: opt.returnBranchId || v.branchId,
      pickupMs: T(pickupAt), returnMs: T(returnAt), status: 'confirmed',
      extras: opt.extras || [], couponCode: opt.couponCode || null,
      driverBirthDate: DRIVERS[customerId][0], licenseIssuedOn: DRIVERS[customerId][1],
      createdMs: T(opt.createdAt), cancellation: null, pickupRecord: null, returnRecord: null,
      invoiceId: null, staffNote: opt.staffNote || null,
    };
    const c = computePrice(v, r);
    r.price = c.price;
    r.durationRate = c.durationRate;
    if (opt.cancel) {
      r.status = 'cancelled';
      r.cancellation = { cancelledMs: T(opt.cancel[0]), fee: opt.cancel[1] };
    }
    if (opt.pickup) {
      r.status = 'active';
      r.pickupRecord = { atMs: T(opt.pickup[0]), odometerKm: opt.pickup[1], fuelLevel: opt.pickup[2] };
    }
    if (opt.ret) {
      r.status = 'completed';
      r.returnRecord = { atMs: T(opt.ret[0]), odometerKm: opt.ret[1], fuelLevel: opt.ret[2] };
      if (opt.voidFirst) {
        const wrong = buildInvoice(r, v, opt.voidFirst[0], r.returnRecord.atMs);
        wrong.status = 'void';
      }
      const inv = buildInvoice(r, v, opt.ret[3] || 0, opt.issuedAt ? T(opt.issuedAt) : r.returnRecord.atMs);
      r.invoiceId = inv.id;
    }
    db.reservations.push(r);
  };

  // rez_1001..1003: cars currently out on rental (active)
  mk('mus_1', 'arc_02', '2026-03-08T10:00:00+03:00', '2026-03-13T10:00:00+03:00',
    { createdAt: '2026-03-01T11:20:00+03:00', pickup: ['2026-03-08T10:05:00+03:00', 41200, 8] });
  mk('mus_3', 'arc_08', '2026-03-07T12:00:00+03:00', '2026-03-12T12:00:00+03:00',
    { createdAt: '2026-02-27T15:45:00+03:00', returnBranchId: 'IST', pickup: ['2026-03-07T12:00:00+03:00', 28750, 6] });
  mk('mus_2', 'arc_09', '2026-03-09T09:00:00+03:00', '2026-03-11T09:00:00+03:00',
    { createdAt: '2026-03-04T09:30:00+03:00', pickup: ['2026-03-09T09:10:00+03:00', 15300, 7] });
  // rez_1004..1009: confirmed, pick-up in the future
  mk('mus_1', 'arc_03', '2026-03-14T10:00:00+03:00', '2026-03-17T10:00:00+03:00',
    { createdAt: '2026-03-02T18:05:00+03:00', extras: ['navigasyon'],
      staffNote: 'Önceki kiralamada araç 3 saat geç iade edildi; teslimde depozito teyidi yapılsın.' });
  mk('mus_2', 'arc_01', '2026-03-21T01:30:00+03:00', '2026-03-23T01:30:00+03:00',
    { createdAt: '2026-03-06T22:10:00+03:00' });
  mk('mus_1', 'arc_10', '2026-03-28T00:45:00+03:00', '2026-03-30T12:00:00+03:00',
    { createdAt: '2026-03-07T08:40:00+03:00' });
  mk('mus_2', 'arc_05', '2026-03-11T15:00:00+03:00', '2026-03-14T15:00:00+03:00',
    { createdAt: '2026-03-03T13:15:00+03:00', extras: ['ek_surucu'],
      staffNote: 'Ek sürücünün ehliyet fotokopisi eksik; teslimde aslı görülecek.' });
  mk('mus_3', 'arc_02', '2026-03-13T14:00:00+03:00', '2026-03-16T14:00:00+03:00',
    { createdAt: '2026-03-05T10:00:00+03:00' });
  mk('mus_3', 'arc_07', '2026-03-20T10:00:00+03:00', '2026-03-27T10:00:00+03:00',
    { createdAt: '2026-03-08T19:25:00+03:00' });
  // rez_1010..1011: cancelled
  mk('mus_2', 'arc_03', '2026-03-18T10:00:00+03:00', '2026-03-22T10:00:00+03:00',
    { createdAt: '2026-03-01T09:00:00+03:00', couponCode: 'BAHAR15', cancel: ['2026-03-05T16:20:00+03:00', 0] });
  mk('mus_1', 'arc_01', '2026-03-06T09:00:00+03:00', '2026-03-08T09:00:00+03:00',
    { createdAt: '2026-02-28T14:00:00+03:00', cancel: ['2026-03-05T12:00:00+03:00', 230000] });
  // rez_1012..1017: completed, with invoices fat_5001..fat_5007 (fat_5005 is void)
  mk('mus_1', 'arc_01', '2026-02-10T10:00:00+03:00', '2026-02-13T10:00:00+03:00',
    { createdAt: '2026-02-01T12:00:00+03:00', pickup: ['2026-02-10T10:10:00+03:00', 30500, 8],
      ret: ['2026-02-13T09:40:00+03:00', 31020, 8] });
  mk('mus_2', 'arc_07', '2026-02-14T09:00:00+03:00', '2026-02-16T09:00:00+03:00',
    { createdAt: '2026-02-05T17:30:00+03:00', pickup: ['2026-02-14T09:00:00+03:00', 51200, 8],
      ret: ['2026-02-16T08:50:00+03:00', 51610, 8] });
  mk('mus_3', 'arc_11', '2026-02-20T12:00:00+03:00', '2026-02-24T12:00:00+03:00',
    { createdAt: '2026-02-10T10:10:00+03:00', pickup: ['2026-02-20T12:15:00+03:00', 18400, 8],
      ret: ['2026-02-24T15:00:00+03:00', 19150, 8] });
  mk('mus_1', 'arc_08', '2026-02-25T10:00:00+03:00', '2026-02-27T10:00:00+03:00',
    { createdAt: '2026-02-15T09:05:00+03:00', returnBranchId: 'IST', pickup: ['2026-02-25T10:00:00+03:00', 28100, 8],
      ret: ['2026-02-27T09:30:00+03:00', 28560, 8] });
  mk('mus_3', 'arc_03', '2026-02-26T10:00:00+03:00', '2026-02-28T10:00:00+03:00',
    { createdAt: '2026-02-18T16:40:00+03:00', pickup: ['2026-02-26T10:00:00+03:00', 60200, 8],
      ret: ['2026-02-28T10:10:00+03:00', 60590, 8, 150000], voidFirst: [500000], issuedAt: '2026-02-28T11:00:00+03:00',
      staffNote: 'Sağ arka kapıda çizik; ilk fatura hatalı tutarla kesildiği için iptal edilip yeniden düzenlendi.' });
  mk('mus_2', 'arc_10', '2026-03-02T10:00:00+03:00', '2026-03-05T10:00:00+03:00',
    { createdAt: '2026-02-20T20:00:00+03:00', extras: ['cocuk_koltugu'], pickup: ['2026-03-02T10:00:00+03:00', 44100, 8],
      ret: ['2026-03-05T10:20:00+03:00', 45000, 6] });
}
seed();

// ---------------------------------------------------------------------------
// Serializers
// ---------------------------------------------------------------------------
function serVehicle(v) {
  return {
    id: v.id, make: v.make, model: v.model, class: v.class, transmission: v.transmission,
    seats: v.seats, branchId: v.branchId, dailyRate: tl(v.rateK), extraKmRate: tl(v.kmK), status: v.status,
  };
}

function serPrice(p) {
  return {
    days: p.days, dailyRate: tl(p.dailyRate), baseAmount: tl(p.baseAmount),
    durationDiscount: tl(p.durationDiscount), couponDiscount: tl(p.couponDiscount),
    extras: p.extras.map((e) => ({ code: e.code, amount: tl(e.amount) })), extrasTotal: tl(p.extrasTotal),
    youngDriverFee: tl(p.youngDriverFee), oneWayFee: tl(p.oneWayFee),
    subtotal: tl(p.subtotal), vat: tl(p.vat), total: tl(p.total), currency: 'TRY',
  };
}

function serRecord(x) {
  return x ? { at: fmtDateTime(x.atMs), odometerKm: x.odometerKm, fuelLevel: x.fuelLevel } : null;
}

function serReservation(r, user, withNote) {
  const o = {
    id: r.id, customerId: r.customerId, vehicleId: r.vehicleId,
    pickupBranchId: r.pickupBranchId, returnBranchId: r.returnBranchId,
    pickupAt: fmtDateTime(r.pickupMs), returnAt: fmtDateTime(r.returnMs), status: r.status,
    extras: r.extras.slice(), couponCode: r.couponCode,
    driverBirthDate: r.driverBirthDate, licenseIssuedOn: r.licenseIssuedOn,
    price: serPrice(r.price), createdAt: fmtDateTime(r.createdMs),
    cancellation: r.cancellation ? { cancelledAt: fmtDateTime(r.cancellation.cancelledMs), fee: tl(r.cancellation.fee) } : null,
    pickupRecord: serRecord(r.pickupRecord), returnRecord: serRecord(r.returnRecord),
    invoiceId: r.invoiceId,
  };
  if (user.role !== 'customer' || withNote) o.staffNote = r.staffNote;
  return o;
}

function serInvoice(i) {
  return {
    id: i.id, reservationId: i.reservationId, customerId: i.customerId, branchId: i.branchId,
    status: i.status, issuedAt: fmtDateTime(i.issuedMs),
    lines: i.lines.map((l) => ({ code: l.code, description: l.description, amount: tl(l.amount) })),
    subtotal: tl(i.subtotal), vat: tl(i.vat), total: tl(i.total), currency: 'TRY',
  };
}

// ---------------------------------------------------------------------------
// Request helpers
// ---------------------------------------------------------------------------
const MAX_BODY = 100000; // bytes; the contract says 413 above 100 000 bytes

function readBody(req) {
  return new Promise((resolve) => {
    const chunks = [];
    let size = 0;
    let done = false;
    const finish = (v) => { if (!done) { done = true; resolve(v); } };
    req.on('data', (c) => {
      size += c.length;
      if (size <= MAX_BODY) chunks.push(c); else chunks.length = 0;
    });
    req.on('end', () => finish(size > MAX_BODY ? { tooLarge: true } : { raw: Buffer.concat(chunks) }));
    req.on('error', () => finish({ aborted: true }));
    req.on('close', () => finish({ aborted: true }));
  });
}

function isObj(x) { return x !== null && typeof x === 'object' && !Array.isArray(x); }
function has(o, k) { return Object.prototype.hasOwnProperty.call(o, k); }

function jsonBody(ctx) {
  let text = ctx.raw.toString('utf8');
  if (text.charCodeAt(0) === 0xFEFF) text = text.slice(1);
  if (text.trim() === '') bad('Gövde zorunludur (JSON nesnesi).');
  let body;
  try { body = JSON.parse(text); } catch (e) { bad('Gövde geçerli bir JSON değil.'); }
  if (!isObj(body)) bad('Gövde bir JSON nesnesi olmalıdır.');
  return body;
}

function unknownFields(body, allowed, errs) {
  for (const k of Object.keys(body)) if (!allowed.includes(k)) errs.push(k + ': tanımsız alan');
}

function vDateTime(body, k, required, errs) {
  if (!has(body, k)) { if (required) errs.push(k + ': zorunlu alan'); return undefined; }
  const ms = parseDateTime(body[k]);
  if (ms === null) { errs.push(k + ': ofsetli ISO 8601 tarih-saat olmalı (ör. 2026-03-15T10:00:00+03:00)'); return undefined; }
  return ms;
}

function vDate(body, k, required, errs) {
  if (!has(body, k)) { if (required) errs.push(k + ': zorunlu alan'); return undefined; }
  const d = parseDate(body[k]);
  if (d === null) { errs.push(k + ': YYYY-AA-GG biçiminde geçerli bir tarih olmalı'); return undefined; }
  return d;
}

function vInt(body, k, min, max, required, errs) {
  if (!has(body, k)) { if (required) errs.push(k + ': zorunlu alan'); return undefined; }
  const x = body[k];
  if (typeof x !== 'number' || !Number.isInteger(x) || x < min || x > max) {
    errs.push(k + ': ' + min + ' ile ' + max + ' arasında tam sayı olmalı');
    return undefined;
  }
  return x;
}

function vNote(body, errs) {
  if (!has(body, 'note')) return undefined;
  if (typeof body.note !== 'string' || body.note.length > 500) { errs.push('note: en fazla 500 karakterlik metin olmalı'); return undefined; }
  return body.note;
}

function vBranch(body, k, errs) {
  if (!has(body, k)) return undefined;
  if (typeof body[k] !== 'string' || !BRANCHES.includes(body[k])) { errs.push(k + ': IST, ANK veya IZM olmalı'); return undefined; }
  return body[k];
}

function vExtras(body, errs) {
  if (!has(body, 'extras')) return undefined;
  const x = body.extras;
  if (!Array.isArray(x) || x.length > 4) { errs.push('extras: en fazla 4 öğeli dizi olmalı'); return undefined; }
  for (let i = 0; i < x.length; i += 1) {
    if (typeof x[i] !== 'string' || x[i].length > 40) { errs.push('extras[' + i + ']: geçersiz değer'); return undefined; }
    // PLANTED K2: the enum check is skipped, unknown extra codes are accepted.
    if (!PLANTED.K2 && !EXTRAS.includes(x[i])) { errs.push('extras[' + i + ']: bilinmeyen ekstra kodu'); return undefined; }
    if (x.indexOf(x[i]) !== i) { errs.push('extras[' + i + ']: aynı ekstra birden fazla kez verilemez'); return undefined; }
  }
  return x.slice();
}

// Body of POST /quotes and POST /reservations
function parseBookingBody(ctx) {
  const body = jsonBody(ctx);
  const errs = [];
  unknownFields(body, ['vehicleId', 'pickupAt', 'returnAt', 'returnBranchId', 'extras', 'couponCode', 'driverBirthDate', 'licenseIssuedOn'], errs);
  let vehicleId;
  if (!has(body, 'vehicleId')) errs.push('vehicleId: zorunlu alan');
  else if (typeof body.vehicleId !== 'string') errs.push('vehicleId: metin olmalı');
  else vehicleId = body.vehicleId;
  const pickupMs = vDateTime(body, 'pickupAt', true, errs);
  const returnMs = vDateTime(body, 'returnAt', true, errs);
  const returnBranchId = vBranch(body, 'returnBranchId', errs);
  const extras = vExtras(body, errs);
  let couponCode = null;
  if (has(body, 'couponCode') && body.couponCode !== null) {
    if (typeof body.couponCode !== 'string' || body.couponCode.length > 40) errs.push('couponCode: en fazla 40 karakterlik metin veya null olmalı');
    else couponCode = body.couponCode;
  }
  const driverBirthDate = vDate(body, 'driverBirthDate', true, errs);
  const licenseIssuedOn = vDate(body, 'licenseIssuedOn', true, errs);
  if (errs.length) bad(errs);
  return { vehicleId, pickupMs, returnMs, returnBranchId, extras: extras || [], couponCode, driverBirthDate, licenseIssuedOn };
}

function qInt(q, k, min, max, def) {
  const s = q.get(k);
  if (s === null) return def;
  if (!/^\d{1,15}$/.test(s)) bad(k + ': tam sayı olmalı');
  const n = Number(s);
  if (n < min || (max !== null && n > max)) bad(k + ': ' + min + (max !== null ? ' ile ' + max + ' arasında' : ' veya daha büyük') + ' olmalı');
  return n;
}
function qEnum(q, k, values, def) {
  const s = q.get(k);
  if (s === null) return def;
  if (!values.includes(s)) bad(k + ': geçersiz değer (izin verilenler: ' + values.join(', ') + ')');
  return s;
}
function qDate(q, k) {
  const s = q.get(k);
  if (s === null) return null;
  const d = parseDate(s);
  if (d === null) bad(k + ': YYYY-AA-GG biçiminde geçerli bir tarih olmalı');
  return d;
}
function qDateTime(q, k) {
  const s = q.get(k);
  if (s === null) return null;
  const ms = parseDateTime(s);
  if (ms === null) bad(k + ': ofsetli ISO 8601 tarih-saat olmalı');
  return ms;
}

function paged(items, page, pageSize, ser) {
  const total = items.length;
  const start = (page - 1) * pageSize;
  return {
    data: items.slice(start, start + pageSize).map(ser),
    meta: { page, pageSize, total, totalPages: Math.ceil(total / pageSize) },
  };
}

function sorter(keyFn, order) {
  const dir = order === 'desc' ? -1 : 1;
  return (a, b) => {
    const ka = keyFn(a); const kb = keyFn(b);
    if (ka < kb) return -dir;
    if (ka > kb) return dir;
    return a.id < b.id ? -1 : a.id > b.id ? 1 : 0;
  };
}

function canSeeReservation(user, r) {
  if (user.role === 'admin') return true;
  if (user.role === 'customer') return r.customerId === user.id;
  return r.pickupBranchId === user.branchId || r.returnBranchId === user.branchId;
}
function canSeeInvoice(user, i) {
  if (user.role === 'admin') return true;
  if (user.role === 'customer') return i.customerId === user.id;
  return i.branchId === user.branchId;
}
function forbid() { fail(403, 'FORBIDDEN', 'Bu işlem için yetkiniz yok.'); }
function getReservation(id) {
  const r = db.reservations.find((x) => x.id === id);
  if (!r) fail(404, 'NOT_FOUND', 'Rezervasyon bulunamadı.');
  return r;
}

// ---------------------------------------------------------------------------
// Handlers
// ---------------------------------------------------------------------------
function listVehicles(ctx) {
  const q = ctx.query;
  const branchId = qEnum(q, 'branchId', BRANCHES, null);
  const cls = qEnum(q, 'class', CLASSES, null);
  const transmission = qEnum(q, 'transmission', TRANSMISSIONS, null);
  const minSeats = qInt(q, 'minSeats', 1, 9, null);
  const from = qDateTime(q, 'availableFrom');
  const to = qDateTime(q, 'availableTo');
  if ((from === null) !== (to === null)) bad('availableFrom ve availableTo birlikte verilmelidir');
  if (from !== null && to <= from) bad('availableTo, availableFrom değerinden sonra olmalıdır');
  const sort = qEnum(q, 'sort', ['id', 'dailyRate', 'seats'], 'id');
  const order = qEnum(q, 'order', ['asc', 'desc'], 'asc');
  const page = qInt(q, 'page', 1, null, 1);
  const pageSize = qInt(q, 'pageSize', 1, 50, 20);
  const items = db.vehicles.filter((v) => (ctx.user.role !== 'customer' || v.status !== 'retired')
    && (branchId === null || v.branchId === branchId)
    && (cls === null || v.class === cls)
    && (transmission === null || v.transmission === transmission)
    && (minSeats === null || v.seats >= minSeats)
    && (from === null || (v.status === 'available' && !isBlocked(v.id, from, to, null, ['confirmed', 'active']))));
  const cmp = sorter(sort === 'dailyRate' ? (v) => v.rateK : sort === 'seats' ? (v) => v.seats : (v) => v.id, order);
  if (PLANTED.K11) {
    // PLANTED K11: the page is cut out first (in id order) and only that page is sorted.
    const out = paged(items, page, pageSize, (v) => v);
    out.data = out.data.sort(cmp).map(serVehicle);
    return [200, out];
  }
  return [200, paged(items.sort(cmp), page, pageSize, serVehicle)];
}

function quote(ctx) {
  if (ctx.user.role !== 'customer') forbid();
  const inp = parseBookingBody(ctx);
  const v0 = vehicleById(inp.vehicleId);
  if (inp.returnBranchId === undefined) inp.returnBranchId = v0 ? v0.branchId : null;
  const v = checkBooking(inp, { customerId: ctx.user.id, excludeId: null });
  const c = computePrice(v, inp);
  return [200, {
    vehicleId: v.id, pickupBranchId: v.branchId, returnBranchId: inp.returnBranchId,
    pickupAt: fmtDateTime(inp.pickupMs), returnAt: fmtDateTime(inp.returnMs),
    extras: inp.extras.slice(), couponCode: inp.couponCode, price: serPrice(c.price),
  }];
}

function createReservation(ctx) {
  if (ctx.user.role !== 'customer') forbid();
  const inp = parseBookingBody(ctx);
  const v0 = vehicleById(inp.vehicleId);
  if (inp.returnBranchId === undefined) inp.returnBranchId = v0 ? v0.branchId : null;
  let idemKey = null;
  const hdr = ctx.req.headers['idempotency-key'];
  if (hdr !== undefined) {
    if (typeof hdr !== 'string' || hdr.length < 1 || hdr.length > 64) bad('Idempotency-Key: 1-64 karakter olmalı');
    // PLANTED K8: keys are stored globally instead of per user.
    idemKey = PLANTED.K8 ? hdr : ctx.user.id + '\n' + hdr;
    const fp = JSON.stringify([inp.vehicleId, inp.pickupMs, inp.returnMs, inp.returnBranchId,
      inp.extras.slice().sort(), inp.couponCode, inp.driverBirthDate, inp.licenseIssuedOn]);
    const hit = db.idem.get(idemKey);
    if (hit) {
      if (hit.fp !== fp) fail(409, 'IDEMPOTENCY_KEY_REUSED', 'Bu Idempotency-Key daha önce farklı bir gövdeyle kullanıldı.');
      return [200, serReservation(getReservation(hit.id), ctx.user, false)];
    }
    idemKey = { key: idemKey, fp };
  }
  const v = checkBooking(inp, { customerId: ctx.user.id, excludeId: null });
  const c = computePrice(v, inp);
  const r = {
    id: 'rez_' + (resSeq += 1), customerId: ctx.user.id, vehicleId: v.id,
    pickupBranchId: v.branchId, returnBranchId: inp.returnBranchId,
    pickupMs: inp.pickupMs, returnMs: inp.returnMs, status: 'confirmed',
    extras: inp.extras, couponCode: inp.couponCode,
    driverBirthDate: inp.driverBirthDate, licenseIssuedOn: inp.licenseIssuedOn,
    price: c.price, durationRate: c.durationRate, createdMs: NOW,
    cancellation: null, pickupRecord: null, returnRecord: null, invoiceId: null, staffNote: null,
  };
  db.reservations.push(r);
  if (idemKey) db.idem.set(idemKey.key, { fp: idemKey.fp, id: r.id });
  return [201, serReservation(r, ctx.user, false)];
}

function listReservations(ctx) {
  const q = ctx.query;
  const status = qEnum(q, 'status', RES_STATUSES, null);
  const vehicleId = q.get('vehicleId');
  const from = qDate(q, 'pickupFrom');
  const to = qDate(q, 'pickupTo');
  if (from !== null && to !== null && from > to) bad('pickupFrom, pickupTo değerinden büyük olamaz');
  const sort = qEnum(q, 'sort', ['pickupAt', 'createdAt', 'total'], 'pickupAt');
  const order = qEnum(q, 'order', ['asc', 'desc'], 'asc');
  const page = qInt(q, 'page', 1, null, 1);
  const pageSize = qInt(q, 'pageSize', 1, 50, 20);
  // PLANTED K12: the calendar day of pickupAt is taken in UTC instead of Turkey time.
  const dayOf = PLANTED.K12 ? utcDate : localDate;
  const items = db.reservations.filter((r) => canSeeReservation(ctx.user, r)
    && (status === null || r.status === status)
    && (vehicleId === null || r.vehicleId === vehicleId)
    && (from === null || dayOf(r.pickupMs) >= from)
    && (to === null || dayOf(r.pickupMs) <= to));
  const key = sort === 'createdAt' ? (r) => r.createdMs : sort === 'total' ? (r) => r.price.total : (r) => r.pickupMs;
  items.sort(sorter(key, order));
  return [200, paged(items, page, pageSize, (r) => serReservation(r, ctx.user, false))];
}

function getReservationOp(ctx) {
  const r = getReservation(ctx.params.id);
  if (!canSeeReservation(ctx.user, r)) forbid();
  return [200, serReservation(r, ctx.user, false)];
}

function patchReservation(ctx) {
  if (ctx.user.role === 'staff') forbid();
  const r = getReservation(ctx.params.id);
  if (!canSeeReservation(ctx.user, r)) forbid();
  const body = jsonBody(ctx);
  const errs = [];
  unknownFields(body, ['pickupAt', 'returnAt', 'returnBranchId', 'extras'], errs);
  const pickupMs = vDateTime(body, 'pickupAt', false, errs);
  const returnMs = vDateTime(body, 'returnAt', false, errs);
  const returnBranchId = vBranch(body, 'returnBranchId', errs);
  const extras = vExtras(body, errs);
  if (Object.keys(body).length === 0) errs.push('En az bir alan gönderilmelidir.');
  if (errs.length) bad(errs);
  if (r.status !== 'confirmed') fail(409, 'INVALID_STATE', 'Yalnızca confirmed durumundaki rezervasyon değiştirilebilir.');
  const inp = {
    vehicleId: r.vehicleId,
    pickupMs: pickupMs === undefined ? r.pickupMs : pickupMs,
    returnMs: returnMs === undefined ? r.returnMs : returnMs,
    returnBranchId: returnBranchId === undefined ? r.returnBranchId : returnBranchId,
    extras: extras === undefined ? r.extras : extras,
    couponCode: r.couponCode, driverBirthDate: r.driverBirthDate, licenseIssuedOn: r.licenseIssuedOn,
  };
  const v = checkBooking(inp, { customerId: r.customerId, excludeId: r.id });
  // PLANTED K7: the duration-discount percentage fixed at creation is reused; it
  // is not re-evaluated for the new number of days.
  const c = PLANTED.K7 ? computePrice(v, inp, r.durationRate) : computePrice(v, inp);
  r.pickupMs = inp.pickupMs;
  r.returnMs = inp.returnMs;
  r.returnBranchId = inp.returnBranchId;
  r.extras = inp.extras;
  r.price = c.price;
  r.durationRate = c.durationRate;
  // PLANTED K10: PATCH and cancel answer with the staff view (staffNote included)
  // even when the caller is a customer.
  return [200, serReservation(r, ctx.user, PLANTED.K10)];
}

function cancelReservation(ctx) {
  if (ctx.user.role === 'staff') forbid();
  const r = getReservation(ctx.params.id);
  if (!canSeeReservation(ctx.user, r)) forbid();
  // PLANTED K3: cancelling an already cancelled reservation answers 200 again.
  if (PLANTED.K3 && r.status === 'cancelled') return [200, serReservation(r, ctx.user, PLANTED.K10)];
  if (r.status !== 'confirmed') fail(409, 'INVALID_STATE', 'Yalnızca confirmed durumundaki rezervasyon iptal edilebilir.');
  const left = r.pickupMs - NOW;
  let fee;
  // PLANTED K4: exactly 48 hours before pick-up is treated as "more than 48 hours".
  if (PLANTED.K4 ? left >= 48 * HOUR : left > 48 * HOUR) fee = 0;
  else if (left > 24 * HOUR) fee = r.price.dailyRate;
  else fee = 2 * r.price.dailyRate;
  fee = Math.min(fee, r.price.subtotal);
  r.status = 'cancelled';
  r.cancellation = { cancelledMs: NOW, fee };
  return [200, serReservation(r, ctx.user, PLANTED.K10)];
}

function pickupReservation(ctx) {
  if (ctx.user.role === 'customer') forbid();
  const r = getReservation(ctx.params.id);
  if (ctx.user.role === 'staff' && r.pickupBranchId !== ctx.user.branchId) forbid();
  const body = jsonBody(ctx);
  const errs = [];
  unknownFields(body, ['pickedUpAt', 'odometerKm', 'fuelLevel', 'note'], errs);
  const atMs = vDateTime(body, 'pickedUpAt', true, errs);
  const odometerKm = vInt(body, 'odometerKm', 0, 2000000, true, errs);
  const fuelLevel = vInt(body, 'fuelLevel', 0, 8, true, errs);
  const note = vNote(body, errs);
  if (errs.length) bad(errs);
  if (r.status !== 'confirmed') fail(409, 'INVALID_STATE', 'Yalnızca confirmed durumundaki rezervasyon teslim edilebilir.');
  if (atMs < r.pickupMs - HOUR) fail(422, 'PICKUP_TOO_EARLY', 'Araç, planlanan alış zamanından en fazla 1 saat önce teslim edilebilir.');
  if (atMs >= r.returnMs) fail(422, 'INVALID_PERIOD', 'Teslim zamanı, planlanan dönüş zamanından önce olmalıdır.');
  r.status = 'active';
  r.pickupRecord = { atMs, odometerKm, fuelLevel };
  if (note !== undefined) r.staffNote = note;
  return [200, serReservation(r, ctx.user, false)];
}

function returnReservation(ctx) {
  if (ctx.user.role === 'customer') forbid();
  const r = getReservation(ctx.params.id);
  // PLANTED K9: the staff check uses the PICK-UP branch; the contract says the
  // RETURN branch. Only one-way rentals show the difference.
  const branchOfReturn = PLANTED.K9 ? r.pickupBranchId : r.returnBranchId;
  if (ctx.user.role === 'staff' && branchOfReturn !== ctx.user.branchId) forbid();
  const body = jsonBody(ctx);
  const errs = [];
  unknownFields(body, ['returnedAt', 'odometerKm', 'fuelLevel', 'damageAmount', 'note'], errs);
  const atMs = vDateTime(body, 'returnedAt', true, errs);
  const odometerKm = vInt(body, 'odometerKm', 0, 2000000, true, errs);
  const fuelLevel = vInt(body, 'fuelLevel', 0, 8, true, errs);
  let damageK = 0;
  if (has(body, 'damageAmount')) {
    const x = body.damageAmount;
    if (typeof x !== 'number' || !Number.isFinite(x) || x < 0 || x > 1000000 || Math.abs(x * 100 - Math.round(x * 100)) > 1e-6) {
      errs.push('damageAmount: 0 ile 1000000 arasında, en fazla 2 ondalıklı sayı olmalı');
    } else damageK = Math.round(x * 100);
  }
  const note = vNote(body, errs);
  if (errs.length) bad(errs);
  if (r.status !== 'active') fail(409, 'INVALID_STATE', 'Yalnızca active durumundaki rezervasyon iade alınabilir.');
  if (atMs <= r.pickupRecord.atMs) fail(422, 'INVALID_PERIOD', 'İade zamanı, teslim zamanından sonra olmalıdır.');
  if (odometerKm < r.pickupRecord.odometerKm) fail(422, 'ODOMETER_INVALID', 'İade kilometresi, teslim kilometresinden küçük olamaz.');
  r.status = 'completed';
  r.returnRecord = { atMs, odometerKm, fuelLevel };
  if (note !== undefined) r.staffNote = note;
  const inv = buildInvoice(r, vehicleById(r.vehicleId), damageK, atMs);
  r.invoiceId = inv.id;
  return [200, serReservation(r, ctx.user, false)];
}

function listInvoices(ctx) {
  const q = ctx.query;
  const status = qEnum(q, 'status', INV_STATUSES, null);
  const from = qDate(q, 'issuedFrom');
  const to = qDate(q, 'issuedTo');
  if (from !== null && to !== null && from > to) bad('issuedFrom, issuedTo değerinden büyük olamaz');
  const page = qInt(q, 'page', 1, null, 1);
  const pageSize = qInt(q, 'pageSize', 1, 50, 20);
  const items = db.invoices.filter((i) => canSeeInvoice(ctx.user, i)
    && (status === null || i.status === status)
    && (from === null || localDate(i.issuedMs) >= from)
    && (to === null || localDate(i.issuedMs) <= to));
  items.sort(sorter((i) => i.issuedMs, 'asc'));
  return [200, paged(items, page, pageSize, serInvoice)];
}

function getInvoice(ctx) {
  const i = db.invoices.find((x) => x.id === ctx.params.id);
  if (!i) fail(404, 'NOT_FOUND', 'Fatura bulunamadı.');
  // PLANTED K1: no ownership check for customers on the single-invoice endpoint.
  const allowed = (PLANTED.K1 && ctx.user.role === 'customer') ? true : canSeeInvoice(ctx.user, i);
  if (!allowed) forbid();
  return [200, serInvoice(i)];
}

function revenueReport(ctx) {
  if (ctx.user.role !== 'admin') forbid();
  const q = ctx.query;
  const from = qDate(q, 'from');
  const to = qDate(q, 'to');
  if (from === null || to === null) bad('from ve to zorunludur (YYYY-AA-GG)');
  if (from > to) bad('from, to değerinden büyük olamaz');
  const branchId = qEnum(q, 'branchId', BRANCHES, null);
  const inRange = (i) => localDate(i.issuedMs) >= from && localDate(i.issuedMs) <= to;
  // PLANTED K13: the status condition is missing, so `void` invoices are counted.
  const pool = db.invoices.filter((i) => inRange(i) && (PLANTED.K13 || i.status === 'issued')
    && (branchId === null || i.branchId === branchId));
  const rows = (branchId === null ? BRANCHES : [branchId]).map((b) => {
    const mine = pool.filter((i) => i.branchId === b);
    return {
      branchId: b, invoiceCount: mine.length,
      subtotal: mine.reduce((s, i) => s + i.subtotal, 0),
      vat: mine.reduce((s, i) => s + i.vat, 0),
      total: mine.reduce((s, i) => s + i.total, 0),
    };
  });
  const sum = (k) => rows.reduce((s, x) => s + x[k], 0);
  const totals = { invoiceCount: sum('invoiceCount'), subtotal: tl(sum('subtotal')), vat: tl(sum('vat')), total: tl(sum('total')) };
  return [200, {
    from, to, branchId, currency: 'TRY',
    rows: rows.map((x) => ({ branchId: x.branchId, invoiceCount: x.invoiceCount, subtotal: tl(x.subtotal), vat: tl(x.vat), total: tl(x.total) })),
    totals,
  }];
}

// ---------------------------------------------------------------------------
// Router
// ---------------------------------------------------------------------------
const ROUTES = [
  [/^\/vehicles$/, { GET: listVehicles }],
  [/^\/quotes$/, { POST: quote }],
  [/^\/reservations$/, { GET: listReservations, POST: createReservation }],
  [/^\/reservations\/([^/]+)$/, { GET: getReservationOp, PATCH: patchReservation }],
  [/^\/reservations\/([^/]+)\/cancel$/, { POST: cancelReservation }],
  [/^\/reservations\/([^/]+)\/pickup$/, { POST: pickupReservation }],
  [/^\/reservations\/([^/]+)\/return$/, { POST: returnReservation }],
  [/^\/invoices$/, { GET: listInvoices }],
  [/^\/invoices\/([^/]+)$/, { GET: getInvoice }],
  [/^\/reports\/revenue$/, { GET: revenueReport }],
];

function send(res, status, obj, headers) {
  if (res.headersSent || res.writableEnded) return;
  const body = JSON.stringify(obj);
  res.writeHead(status, Object.assign({
    'Content-Type': 'application/json; charset=utf-8',
    'Content-Length': Buffer.byteLength(body),
    'Cache-Control': 'no-store',
  }, headers || {}));
  res.end(body);
}

function dispatch(req, raw) {
  // Routes are matched on the raw path; only the {id} segment is percent-decoded,
  // so an encoded slash can never turn into a path separator.
  const target = String(req.url || '/');
  const qi = target.indexOf('?');
  const path = qi === -1 ? target : target.slice(0, qi);
  const query = new URLSearchParams(qi === -1 ? '' : target.slice(qi + 1));
  if (path === '/health') {
    if (req.method !== 'GET') fail(405, 'METHOD_NOT_ALLOWED', 'Bu adres için desteklenmeyen HTTP yöntemi.', undefined, { Allow: 'GET' });
    return [200, { status: 'ok', service: 'turna-oto-kiralama-api', now: fmtDateTime(NOW) }];
  }
  const m = /^Bearer\s+(\S+)$/i.exec(String(req.headers.authorization || '').trim());
  const user = m ? USERS.get(m[1]) : undefined;
  if (!user) fail(401, 'UNAUTHENTICATED', 'Geçerli bir Bearer token gereklidir.');
  if (raw.tooLarge) fail(413, 'PAYLOAD_TOO_LARGE', 'İstek gövdesi 100 000 bayt sınırını aşıyor.');
  for (const [re, methods] of ROUTES) {
    const pm = re.exec(path);
    if (pm) {
      const handler = has(methods, req.method) ? methods[req.method] : null;
      if (!handler) fail(405, 'METHOD_NOT_ALLOWED', 'Bu adres için desteklenmeyen HTTP yöntemi.', undefined, { Allow: Object.keys(methods).join(', ') });
      let id;
      try { id = pm[1] === undefined ? undefined : decodeURIComponent(pm[1]); } catch (e) {
        fail(400, 'VALIDATION_ERROR', 'Adresteki kimlik çözümlenemedi.');
      }
      return handler({ req, user, query, params: { id }, raw: raw.raw || Buffer.alloc(0) });
    }
  }
  return fail(404, 'NOT_FOUND', 'Adres bulunamadı.');
}

const server = http.createServer((req, res) => {
  readBody(req).then((raw) => {
    if (raw.aborted) return;
    try {
      const out = dispatch(req, raw);
      send(res, out[0], out[1]);
    } catch (e) {
      if (e instanceof ApiError) {
        const body = { code: e.code, message: e.message };
        if (e.details) body.details = e.details;
        send(res, e.status, body, e.headers);
      } else {
        console.error('[api3] unexpected error:', e && e.message);
        send(res, 500, { code: 'INTERNAL_ERROR', message: 'Beklenmeyen bir hata oluştu.' });
      }
    }
  }).catch(() => {
    try { send(res, 500, { code: 'INTERNAL_ERROR', message: 'Beklenmeyen bir hata oluştu.' }); } catch (e) { /* socket gone */ }
  });
});

// A request whose headers or body do not arrive completely is answered with 408
// after these limits instead of keeping the connection open.
server.headersTimeout = 10000;
server.requestTimeout = 20000;

server.on('clientError', (err, socket) => {
  if (socket.writable) {
    const timeout = err && err.code === 'ERR_HTTP_REQUEST_TIMEOUT';
    const body = JSON.stringify(timeout
      ? { code: 'REQUEST_TIMEOUT', message: 'İstek zamanında tamamlanmadı.' }
      : { code: 'VALIDATION_ERROR', message: 'HTTP isteği çözümlenemedi.' });
    socket.end('HTTP/1.1 ' + (timeout ? '408 Request Timeout' : '400 Bad Request')
      + '\r\nContent-Type: application/json; charset=utf-8\r\nContent-Length: '
      + Buffer.byteLength(body) + '\r\nConnection: close\r\n\r\n' + body);
  } else {
    socket.destroy();
  }
});
process.on('uncaughtException', (e) => { console.error('[api3] uncaught:', e && e.message); });
process.on('unhandledRejection', (e) => { console.error('[api3] unhandled rejection:', e && e.message); });

server.listen(PORT, () => {
  console.log('Turna Oto Kiralama API dinlemede: http://localhost:' + PORT
    + ' (PORT=' + PORT + ', saat sabit: ' + fmtDateTime(NOW) + (DEFECTS_ON ? '' : ', REFERANS KİPİ: planted defects OFF') + ')');
});
