#!/usr/bin/env python3
"""
Objective verifier for trial-api3 (Turna Oto Kiralama - Rezervasyon ve Kiralama API).

Usage:
    # start a FRESH server first (evaluator side):
    #   node C:\\projeler\\TestSkills\\evals\\trial-api3\\server.js      (PORT optional, default 3210)
    python grade_api3.py [BASE_URL] [--reference]

Default BASE_URL = http://localhost:3210 (or env API3_BASE).

This script does NOT grade an agent's report. It reproduces every planted defect
(K1..K16), and confirms that every discriminator (D), trap (T) and
contract-silent behaviour (S) of evals/keys/api3.md behaves as the key says, so
an evaluator can confirm the trial is sound before a run and can cross-check a
reported finding against ground truth afterwards.

The script changes data (creates, cancels, picks up and returns reservations),
so it needs a fresh server and the server must be restarted before an agent run.

--reference: expect the contract-correct behaviour instead of the planted one for
the K checks. Use it only against a server started with API3_PLANTED=off; it
proves that each K scenario deviates from the contract only through its defect.

Stdlib only. Exit code 0 only when every check behaves as designed.
"""
import json
import os
import sys
import urllib.error
import urllib.request

try:  # never fail on a console that cannot print Turkish letters
    sys.stdout.reconfigure(errors='backslashreplace')
except (AttributeError, ValueError):
    pass

args = [a for a in sys.argv[1:] if not a.startswith('--')]
REFERENCE = '--reference' in sys.argv[1:]
BASE = (args[0] if args else os.environ.get('API3_BASE', 'http://localhost:3210')).rstrip('/')

C1 = 'tok_musteri_elif'     # mus_1
C2 = 'tok_musteri_baran'    # mus_2
STAFF = 'tok_personel_ist'  # per_1, branch IST
ADMIN = 'tok_yonetici'

results = []


def req(method, path, token=None, body=None, raw=None, headers=None):
    h = dict(headers or {})
    if token:
        h['Authorization'] = 'Bearer ' + token
    data = None
    if raw is not None:
        data = raw.encode('utf-8')
        h.setdefault('Content-Type', 'application/json')
    elif body is not None:
        data = json.dumps(body).encode('utf-8')
        h.setdefault('Content-Type', 'application/json')
    r = urllib.request.Request(BASE + path, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(r, timeout=20) as resp:
            text = resp.read().decode('utf-8')
            return resp.status, (json.loads(text) if text else None)
    except urllib.error.HTTPError as e:
        text = e.read().decode('utf-8')
        try:
            return e.code, json.loads(text)
        except ValueError:
            return e.code, text
    except OSError as e:   # connection refused, reset or timed out: the server is not there (or died)
        print('[FAIL] %s %s: no answer from %s (%s)' % (method, path, BASE, e))
        print('0/1 checks behaved as designed.')
        sys.exit(1)


def check(name, ok, detail):
    results.append((name, bool(ok)))
    print('[%s] %s: %s' % ('PASS' if ok else 'FAIL', name, detail))


def planted(name, observed, planted_value, contract_value, detail):
    """A K check: the server must show the planted value (or, with --reference, the contract value)."""
    expected = contract_value if REFERENCE else planted_value
    check(name, observed == expected,
          '%s -> observed %r; planted behaviour %r, contract requires %r' % (detail, observed, planted_value, contract_value))


def t(day, hh=10, mm=0, ss=0):
    """Timestamp in 2026, Turkey time; day is 'MM-DD'."""
    return '2026-%s-%sT%02d:%02d:%02d+03:00' % (day[:2], day[3:], hh, mm, ss)


def booking(vehicle, pickup, ret, **extra):
    b = {'vehicleId': vehicle, 'pickupAt': pickup, 'returnAt': ret,
         'driverBirthDate': '1990-06-14', 'licenseIssuedOn': '2010-09-01'}
    b.update(extra)
    return b


def create(token, body, headers=None):
    st, js = req('POST', '/reservations', token, body, headers=headers)
    if st != 201:
        check('setup create %s %s' % (body['vehicleId'], body['pickupAt']), False, 'expected 201, got %s %s' % (st, js))
    return js if isinstance(js, dict) else {}


def code_of(js):
    return js.get('code') if isinstance(js, dict) else None


def ids(js):
    return [x['id'] for x in js['data']] if isinstance(js, dict) and 'data' in js else js


def line(inv, code):
    for ln in (inv.get('lines') or []) if isinstance(inv, dict) else []:
        if ln['code'] == code:
            return ln['amount']
    return None


def rent_and_return(vehicle, pickup, ret, returned_at, odo_km=100, fuel_out=8, fuel_in=8, **extra):
    """customer creates, admin hands over at pickup time and takes back; returns (reservation, invoice)."""
    r = create(C1, booking(vehicle, pickup, ret, **extra))
    rid = r.get('id')
    req('POST', '/reservations/%s/pickup' % rid, ADMIN, {'pickedUpAt': pickup, 'odometerKm': 1000, 'fuelLevel': fuel_out})
    st, done = req('POST', '/reservations/%s/return' % rid, ADMIN,
                   {'returnedAt': returned_at, 'odometerKm': 1000 + odo_km, 'fuelLevel': fuel_in})
    inv_id = done.get('invoiceId') if isinstance(done, dict) else None
    st2, inv = req('GET', '/invoices/%s' % inv_id, ADMIN)
    return (done if st == 200 else {}), (inv if st2 == 200 else {})


# ---------------------------------------------------------------------------
# 0. Preconditions: fresh server, fixed clock
# ---------------------------------------------------------------------------
st, health = req('GET', '/health')
check('P1 health without token, fixed clock', st == 200 and health.get('now') == '2026-03-10T09:00:00+03:00', '%s %s' % (st, health))
st, allres = req('GET', '/reservations?pageSize=50', ADMIN)
st2, allinv = req('GET', '/invoices?pageSize=50', ADMIN)
fresh = st == 200 and st2 == 200 and allres['meta']['total'] == 17 and allinv['meta']['total'] == 7
check('P2 fresh seed (17 reservations, 7 invoices)', fresh,
      'reservations=%s invoices=%s (restart the server if this fails)' % (
          allres['meta']['total'] if st == 200 else st, allinv['meta']['total'] if st2 == 200 else st2))
if not fresh:
    print('-' * 70)
    print('The server is not in its seed state; restart it and run the verifier again.')
    print('%d/%d checks behaved as designed.' % (sum(1 for _, ok in results if ok), len(results)))
    sys.exit(1)
st, js = req('GET', '/vehicles')
check('P3 missing token -> 401', st == 401 and code_of(js) == 'UNAUTHENTICATED', '%s %s' % (st, js))

print('-' * 70)
# ---------------------------------------------------------------------------
# Read-only K checks first (they need the untouched seed)
# ---------------------------------------------------------------------------
# K1 - customer reads another customer's invoice by id
st, js = req('GET', '/invoices/fat_5001', C2)          # fat_5001 belongs to mus_1
planted('K1 invoice BOLA (GET /invoices/{id})', st, 200, 403, 'mus_2 GET /invoices/fat_5001 (owner mus_1)')
st, js = req('GET', '/invoices', C2)
check('K1-D list is scoped: mus_2 sees only own invoices', st == 200 and ids(js) == ['fat_5002', 'fat_5007'], ids(js))
st, js = req('GET', '/invoices/fat_5002', STAFF)       # ANK invoice, staff is IST
check('K1-D staff of another branch is blocked on the same endpoint', st == 403, st)
st, js = req('GET', '/reservations/rez_1001', C2)
check('K1-D reservations by id are protected', st == 403, st)

# K11 - sort is applied after the page has been cut out
st, js = req('GET', '/vehicles?sort=dailyRate&order=asc&page=1&pageSize=4', C1)
planted('K11 sort after pagination (GET /vehicles)', ids(js), ['arc_01', 'arc_02', 'arc_03', 'arc_04'],
        ['arc_07', 'arc_10', 'arc_01', 'arc_05'], 'cheapest four vehicles, pageSize=4')
st, js = req('GET', '/vehicles?sort=dailyRate&order=asc', C1)
check('K11-D default page size hides it: whole list is sorted',
      ids(js) == ['arc_07', 'arc_10', 'arc_01', 'arc_05', 'arc_02', 'arc_08', 'arc_11', 'arc_03', 'arc_06', 'arc_09', 'arc_04'], ids(js))
full = sorted(allres['data'], key=lambda r: (-r['price']['total'], r['id']))
got = []
for page in (1, 2):
    st, js = req('GET', '/reservations?sort=total&order=desc&pageSize=3&page=%d' % page, ADMIN)
    got += ids(js)
check('K11-D GET /reservations sorts before paginating', got == [r['id'] for r in full[:6]], got)

# K12 - date filters of GET /reservations use the UTC day
st, js = req('GET', '/reservations?pickupFrom=2026-03-28&pickupTo=2026-03-28', C1)   # rez_1006 pickupAt 2026-03-28T00:45+03:00
planted('K12 pickupFrom/pickupTo in UTC (own day)', ids(js), [], ['rez_1006'], 'mus_1, filter 2026-03-28..2026-03-28')
st, js = req('GET', '/reservations?pickupFrom=2026-03-27&pickupTo=2026-03-27', C1)
planted('K12 pickupFrom/pickupTo in UTC (previous day)', ids(js), ['rez_1006'], [], 'mus_1, filter 2026-03-27..2026-03-27')
st, js = req('GET', '/reservations?pickupFrom=2026-03-14&pickupTo=2026-03-14', C1)
check('K12-D daytime pick-ups filter correctly', ids(js) == ['rez_1004'], ids(js))
st, js = req('GET', '/invoices?issuedFrom=2026-02-13&issuedTo=2026-02-13', ADMIN)
check('K12-D invoice date filter is correct', ids(js) == ['fat_5001'], ids(js))

# K13 - revenue report counts void invoices
st, js = req('GET', '/reports/revenue?from=2026-02-01&to=2026-02-28', ADMIN)
rows = {x['branchId']: [x['invoiceCount'], x['subtotal'], x['vat'], x['total']] for x in js['rows']} if st == 200 else {}
planted('K13 revenue report includes the void invoice', rows.get('IST'), [3, 17510, 3502, 21012], [2, 8730, 1746, 10476],
        'February, IST row (fat_5001 + fat_5006 are issued, fat_5005 is void)')
check('K13-D the other branches of the same report are correct',
      [rows.get('ANK'), rows.get('IZM')] == [[2, 6520, 1304, 7824], [1, 7204.65, 1440.93, 8645.58]], rows)
st, js = req('GET', '/reports/revenue?from=2026-03-01&to=2026-03-31', ADMIN)
rows = {x['branchId']: [x['invoiceCount'], x['subtotal'], x['vat'], x['total']] for x in js['rows']} if st == 200 else {}
check('K13-D a period without void invoices is correct (March)',
      rows == {'ANK': [0, 0, 0, 0], 'IST': [0, 0, 0, 0], 'IZM': [1, 5285, 1057, 6342]}
      and js['totals'] == {'invoiceCount': 1, 'subtotal': 5285, 'vat': 1057, 'total': 6342}, rows)

# K15 - `active` reservations do not block the vehicle in quote / create / PATCH
k15 = booking('arc_02', t('03-10', 12), t('03-12', 12))     # rez_1001 (active) holds arc_02 until 03-13 10:00
st, js = req('POST', '/quotes', C1, k15)
planted('K15 quote on a car that is out on rental', [st, code_of(js) if st != 200 else None], [200, None],
        [409, 'VEHICLE_ALREADY_BOOKED'], 'arc_02 2026-03-10 12:00..03-12 12:00 overlaps active rez_1001')
st, js = req('GET', '/vehicles?availableFrom=%s&availableTo=%s' % (k15['pickupAt'].replace('+', '%2B'), k15['returnAt'].replace('+', '%2B')), C1)
check('K15-D availability filter of GET /vehicles is correct (arc_02 not offered)',
      st == 200 and 'arc_02' not in ids(js) and 'arc_01' in ids(js), ids(js))
st, js = req('POST', '/quotes', C1, booking('arc_02', t('03-14'), t('03-15')))   # overlaps confirmed rez_1008
check('K15-D overlap with a confirmed reservation is rejected', st == 409 and code_of(js) == 'VEHICLE_ALREADY_BOOKED', '%s %s' % (st, code_of(js)))

# K16 - VAT truncated instead of rounded half-up
st, js = req('POST', '/quotes', C1, booking('arc_04', t('06-01'), t('06-02')))
p = js.get('price', {}) if st == 200 else {}
planted('K16 VAT truncated (arc_04, 1 day)', [p.get('subtotal'), p.get('vat'), p.get('total')],
        [3299.99, 659.99, 3959.98], [3299.99, 660.0, 3959.99], '20% of 3299.99 = 659.998')
st, js = req('POST', '/quotes', C1, booking('arc_02', t('04-01'), t('04-09'), extras=['cocuk_koltugu', 'tam_koruma']))
p = js.get('price', {}) if st == 200 else {}
check('K16-D worked example of the contract is exact',
      [p.get('days'), p.get('baseAmount'), p.get('durationDiscount'), p.get('extrasTotal'), p.get('subtotal'), p.get('vat'), p.get('total')]
      == [8, 11600, 1160, 2928, 13368, 2673.6, 16041.6], p)

# K2 - unknown extra code accepted
st, js = req('POST', '/quotes', C1, booking('arc_11', t('06-01'), t('06-03'), extras=['navigasyon', 'sunroof']))
planted('K2 unknown extra code accepted', st, 200, 400, "extras ['navigasyon','sunroof']")
st, js = req('POST', '/quotes', C1, booking('arc_11', t('06-01'), t('06-03'), extras=['navigasyon', 'navigasyon']))
check('K2-D duplicate extra is rejected', st == 400 and code_of(js) == 'VALIDATION_ERROR', '%s %s' % (st, code_of(js)))

# K5 - young-driver fee uses the age on the server's "today"
st, js = req('POST', '/quotes', C1, booking('arc_11', t('03-20'), t('03-22'), driverBirthDate='2001-03-15', licenseIssuedOn='2020-01-01'))
planted('K5 young-driver fee by age today', js.get('price', {}).get('youngDriverFee') if st == 200 else st, 400, 0,
        'driver born 2001-03-15 is 25 on the pick-up day 2026-03-20 (24 on 2026-03-10)')
st, js = req('POST', '/quotes', C1, booking('arc_11', t('03-20'), t('03-22'), driverBirthDate='2005-03-18', licenseIssuedOn='2024-03-01'))
check('K5-D minimum age 21 is evaluated on the pick-up day', st == 200 and js['price']['youngDriverFee'] == 400, '%s' % st)
st, js = req('POST', '/quotes', C1, booking('arc_11', t('03-20'), t('03-22'), driverBirthDate='2005-03-21', licenseIssuedOn='2024-03-01'))
check('K5-D driver who is 20 on the pick-up day is rejected', st == 422 and code_of(js) == 'DRIVER_TOO_YOUNG', '%s %s' % (st, code_of(js)))

# K6 - BAHAR15: a cancelled reservation still counts as a use (seed: mus_2, rez_1010 cancelled)
coupon_quote = booking('arc_11', t('04-10'), t('04-13'), couponCode='BAHAR15')
st, js = req('POST', '/quotes', C2, coupon_quote)
planted('K6 BAHAR15 refused because of a cancelled reservation (seed, mus_2)', [st, code_of(js) if st != 200 else None],
        [422, 'COUPON_ALREADY_USED'], [200, None], "mus_2's only BAHAR15 reservation (rez_1010) is cancelled")
st, js = req('POST', '/quotes', C1, coupon_quote)
check('K6-D BAHAR15 works for a customer who never used it', st == 200 and js['price']['couponDiscount'] == 753.98, '%s' % st)

print('-' * 70)
# ---------------------------------------------------------------------------
# K / T checks that change data
# ---------------------------------------------------------------------------
# T6 + K6 (sequence form): coupon kept although its discount is 0; later freed by cancelling
r = create(C1, booking('arc_11', t('04-10'), t('04-25'), couponCode='BAHAR15'))     # 15 days
p = r.get('price', {})
check('T6 coupon recorded but duration discount (20%) wins',
      [p.get('durationDiscount'), p.get('couponDiscount'), r.get('couponCode')] == [5026.5, 0, 'BAHAR15'], p)
st, js = req('POST', '/quotes', C1, booking('arc_04', t('04-10'), t('04-13'), couponCode='BAHAR15'))
check('T6 BAHAR15 counts as used although its discount was 0', st == 422 and code_of(js) == 'COUPON_ALREADY_USED', '%s %s' % (st, code_of(js)))
st, js = req('POST', '/quotes', C1, booking('arc_04', t('04-10'), t('04-12'), couponCode='BAHAR15'))
check('S2 coupon errors: COUPON_NOT_APPLICABLE is reported before COUPON_ALREADY_USED',
      st == 422 and code_of(js) == 'COUPON_NOT_APPLICABLE', '%s %s' % (st, code_of(js)))
st, js = req('POST', '/reservations/%s/cancel' % r.get('id'), C1)
st, js = req('POST', '/quotes', C1, booking('arc_04', t('04-10'), t('04-13'), couponCode='BAHAR15'))
planted('K6 BAHAR15 still refused after cancelling the only use (sequence, mus_1)', [st, code_of(js) if st != 200 else None],
        [422, 'COUPON_ALREADY_USED'], [200, None], 'create with BAHAR15 -> cancel -> quote with BAHAR15')

# K3 - cancelling twice
r = create(C1, booking('arc_11', t('04-01'), t('04-03')))
st1, a = req('POST', '/reservations/%s/cancel' % r.get('id'), C1)
st2, b = req('POST', '/reservations/%s/cancel' % r.get('id'), C1)
planted('K3 cancel of an already cancelled reservation', st2, 200, 409, 'first cancel %s, second cancel' % st1)
st, js = req('POST', '/reservations/rez_1001/cancel', C1)
check('K3-D cancel of an active reservation -> 409 INVALID_STATE', st == 409 and code_of(js) == 'INVALID_STATE', '%s %s' % (st, code_of(js)))
st, js = req('POST', '/reservations/rez_1012/cancel', C1)
check('K3-D cancel of a completed reservation -> 409 INVALID_STATE', st == 409 and code_of(js) == 'INVALID_STATE', '%s %s' % (st, code_of(js)))

# K4 - cancellation fee tiers: exactly 48 hours before pick-up
r = create(C1, booking('arc_11', t('03-12', 9), t('03-14', 9)))
st, js = req('POST', '/reservations/%s/cancel' % r.get('id'), C1)
planted('K4 cancellation exactly 48 h before pick-up', js.get('cancellation', {}).get('fee') if st == 200 else st, 0, 1675.5,
        'pickupAt 2026-03-12T09:00:00+03:00, now 2026-03-10T09:00:00+03:00, dailyRate 1675.50')
r = create(C1, booking('arc_11', t('03-12', 8, 59, 59), t('03-14', 9)))
st, js = req('POST', '/reservations/%s/cancel' % r.get('id'), C1)
check('K4-D 47 h 59 min 59 s before pick-up -> one daily rate', st == 200 and js['cancellation']['fee'] == 1675.5, js.get('cancellation'))
r = create(C1, booking('arc_11', t('03-12', 9, 0, 1), t('03-14', 9)))
st, js = req('POST', '/reservations/%s/cancel' % r.get('id'), C1)
check('K4-D 48 h 0 min 1 s before pick-up -> free', st == 200 and js['cancellation']['fee'] == 0, js.get('cancellation'))
r = create(C1, booking('arc_11', t('03-11', 9), t('03-14', 9)))
st, js = req('POST', '/reservations/%s/cancel' % r.get('id'), C1)
check('K4-D exactly 24 h before pick-up -> two daily rates', st == 200 and js['cancellation']['fee'] == 3351, js.get('cancellation'))

# T7 - cancellation fee is capped at price.subtotal
r = create(C1, booking('arc_11', t('03-10', 12), t('03-11', 12)))       # 1 day, pick-up in 3 hours
st, js = req('POST', '/reservations/%s/cancel' % r.get('id'), C1)
check('T7 fee capped at subtotal (1-day rental cancelled 3 h before: 1675.50, not 3351.00)',
      st == 200 and js['cancellation']['fee'] == 1675.5 and js['price']['subtotal'] == 1675.5, js.get('cancellation'))

# T5 - the slot of a cancelled reservation can be booked again
r = create(C1, booking('arc_03', t('03-18'), t('03-22')))                # exactly the slot of cancelled rez_1010
check('T5 slot of a cancelled reservation is free again', r.get('status') == 'confirmed', r.get('id'))

# K7 - PATCH keeps the duration-discount percentage fixed at creation
r = create(C1, booking('arc_04', t('05-01'), t('05-09')))                # 8 days -> 10 %
st, js = req('PATCH', '/reservations/%s' % r.get('id'), C1, {'returnAt': t('05-04')})   # 3 days -> 0 %
p = js.get('price', {}) if st == 200 else {}
planted('K7 PATCH 8 -> 3 days keeps the 10% discount', [p.get('days'), p.get('baseAmount'), p.get('durationDiscount')],
        [3, 9899.97, 990.0], [3, 9899.97, 0], 'created with 8 days (discount %s)' % r.get('price', {}).get('durationDiscount'))
r = create(C1, booking('arc_04', t('05-12'), t('05-15')))                # 3 days -> 0 %
st, js = req('PATCH', '/reservations/%s' % r.get('id'), C1, {'returnAt': t('05-16'), 'extras': ['navigasyon']})
p = js.get('price', {}) if st == 200 else {}
check('K7-D PATCH inside the same tier (3 -> 4 days) recalculates everything',
      [p.get('days'), p.get('baseAmount'), p.get('durationDiscount'), p.get('extrasTotal'), p.get('subtotal'), p.get('vat'), p.get('total')]
      == [4, 13199.96, 0, 360, 13559.96, 2711.99, 16271.95], p)
st, js = req('PATCH', '/reservations/%s' % r.get('id'), C1, {'returnAt': t('05-20'), 'extras': []})   # 8 days -> 10 %
p = js.get('price', {}) if st == 200 else {}
planted('K7 PATCH 4 -> 8 days gets no discount', [p.get('days'), p.get('durationDiscount')], [8, 0], [8, 2639.99],
        'created with 3 days')

# K8 + T3 - Idempotency-Key
k8 = booking('arc_11', t('05-01'), t('05-03'))
first = create(C1, k8, headers={'Idempotency-Key': 'grade-k8'})
st, again = req('POST', '/reservations', C1, k8, headers={'Idempotency-Key': 'grade-k8'})
check('T3 replay with the same key and body -> 200 (not 201) and the same reservation',
      st == 200 and again.get('id') == first.get('id'), '%s %s' % (st, again.get('id') if isinstance(again, dict) else again))
st, other = req('POST', '/reservations', C2, k8, headers={'Idempotency-Key': 'grade-k8'})
planted('K8 Idempotency-Key shared between users', [st, other.get('customerId') if isinstance(other, dict) else None],
        [200, 'mus_1'], [409, None], "mus_2 sends mus_1's key and body (contract: handled as mus_2's own request -> car already booked)")
st, js = req('POST', '/reservations', C1, booking('arc_11', t('05-05'), t('05-06')), headers={'Idempotency-Key': 'grade-k8'})
check('K8-D same user, same key, other body -> 409 IDEMPOTENCY_KEY_REUSED', st == 409 and code_of(js) == 'IDEMPOTENCY_KEY_REUSED', '%s %s' % (st, code_of(js)))

# S9 - "same body" is compared by meaning; a replay returns the current state of the reservation
k8z = dict(k8, pickupAt='2026-05-01T07:00:00Z', returnBranchId='IZM', extras=[], couponCode=None)
st, again = req('POST', '/reservations', C1, k8z, headers={'Idempotency-Key': 'grade-k8'})
check('S9 same instant in another offset and spelled-out defaults count as the same body',
      st == 200 and again.get('id') == first.get('id'), '%s' % st)
req('PATCH', '/reservations/%s' % first.get('id'), C1, {'extras': ['navigasyon']})
st, again = req('POST', '/reservations', C1, k8, headers={'Idempotency-Key': 'grade-k8'})
check('S9 replay returns the current state (after PATCH), not the first response',
      st == 200 and again.get('extras') == ['navigasyon'], again.get('extras') if isinstance(again, dict) else again)

s9 = booking('arc_01', t('04-10'), t('04-12'), extras=['navigasyon', 'ek_surucu'])
one = create(C1, s9, headers={'Idempotency-Key': 'grade-s9'})
st, two = req('POST', '/reservations', C1, dict(s9, extras=['ek_surucu', 'navigasyon']), headers={'Idempotency-Key': 'grade-s9'})
check('S9 extras in another order count as the same body', st == 200 and two.get('id') == one.get('id'), '%s' % st)

# S4 - one customer, two cars, same period
r = create(C1, booking('arc_10', t('05-01'), t('05-03')))
check('S4 overlapping reservations of one customer on different cars are accepted', r.get('status') == 'confirmed', r.get('id'))

# K10 - staffNote in PATCH / cancel responses of customers
st, js = req('PATCH', '/reservations/rez_1004', C1, {'extras': ['navigasyon']})
planted('K10 staffNote returned to the customer by PATCH', isinstance(js, dict) and isinstance(js.get('staffNote'), str), True, False,
        'mus_1 PATCH rez_1004 (seed note: %r)' % (js.get('staffNote') if isinstance(js, dict) else None))
st, js = req('GET', '/reservations/rez_1004', C1)
check('K10-D GET by id hides staffNote from the customer', st == 200 and 'staffNote' not in js, sorted(js)[-3:])
st, js = req('GET', '/reservations?pageSize=50', C1)
check('K10-D list hides staffNote from the customer', st == 200 and all('staffNote' not in x for x in js['data']), len(js['data']))
r = create(C1, booking('arc_11', t('06-05'), t('06-06')))
check('K10-D create response has no staffNote', 'staffNote' not in r, sorted(r)[-3:])
st, js = req('POST', '/reservations/%s/cancel' % r.get('id'), C1)
planted('K10 staffNote key present in the cancel response of a customer', isinstance(js, dict) and 'staffNote' in js, True, False,
        'cancel of an own reservation without note (value null)')
st, js = req('GET', '/reservations/rez_1004', STAFF)
check('K10-D staff sees staffNote', st == 200 and isinstance(js.get('staffNote'), str), '%s' % st)

# K9 - return authorisation uses the pick-up branch
st, js = req('GET', '/reservations/rez_1002', STAFF)        # ANK -> IST one-way, active
check('K9-D IST staff can see the one-way rental that returns to IST', st == 200 and js['returnBranchId'] == 'IST', '%s' % st)
st, js = req('POST', '/reservations/rez_1002/return', STAFF, {'returnedAt': t('03-12', 11), 'odometerKm': 29000, 'fuelLevel': 6})
planted('K9 IST staff refused for a car returned to IST (picked up in ANK)', st, 403, 200, 'rez_1002 returnBranchId IST')
oneway = create(C1, booking('arc_04', t('05-25'), t('05-27'), returnBranchId='ANK'))
st, js = req('POST', '/reservations/%s/pickup' % oneway.get('id'), STAFF, {'pickedUpAt': t('05-25'), 'odometerKm': 5000, 'fuelLevel': 8, 'note': ''})
check('K9-D IST staff hands over a car picked up in IST', st == 200 and js.get('status') == 'active', '%s' % st)
check('S14 empty note is stored as an empty string', isinstance(js, dict) and js.get('staffNote') == '', js.get('staffNote') if isinstance(js, dict) else js)
st, js = req('POST', '/reservations/%s/return' % oneway.get('id'), STAFF, {'returnedAt': t('05-27'), 'odometerKm': 5200, 'fuelLevel': 8})
planted('K9 IST staff allowed for a car returned to ANK (picked up in IST)', st, 200, 403, 'one-way IST -> ANK')
st, js = req('POST', '/reservations/rez_1003/return', STAFF, {'returnedAt': t('03-11', 9), 'odometerKm': 15500, 'fuelLevel': 7})
check('K9-D IST staff is blocked on an ANK -> ANK rental', st == 403, st)
st, js = req('POST', '/reservations/rez_1009/pickup', STAFF, {'pickedUpAt': t('03-20'), 'odometerKm': 52000, 'fuelLevel': 8})
check('K9-D IST staff cannot hand over a car of the ANK branch', st == 403, st)

# K14 - late fee cap; T1 - early return; S10/S11/S12
late26, inv26 = rent_and_return('arc_11', t('05-10'), t('05-12'), t('05-13', 12))        # 26 h late
planted('K14 late fee for 26 h (cap must be two daily rates)', line(inv26, 'gecikme'), 1675.5, 3351,
        '26 started hours x 167.55 = 4356.30; cap ceil(26/24) x 1675.50')
late14, inv14 = rent_and_return('arc_11', t('05-15'), t('05-17'), t('05-18', 0))           # 14 h late
check('K14-D 14 h late -> capped at one daily rate (contract example)', line(inv14, 'gecikme') == 1675.5, line(inv14, 'gecikme'))
late2, inv2 = rent_and_return('arc_11', t('05-20'), t('05-22'), t('05-22', 12, 10))        # 2 h 10 min late
check('K14-D 2 h 10 min late -> 30% of the daily rate (contract example)', line(inv2, 'gecikme') == 502.65, line(inv2, 'gecikme'))
ontime, inv60 = rent_and_return('arc_11', t('06-02'), t('06-04'), t('06-04', 11))          # exactly 60 min late
check('K14-D exactly 60 min late -> no late fee', inv60.get('lines') is not None and line(inv60, 'gecikme') is None, inv60.get('lines'))
early, inv_early = rent_and_return('arc_11', t('05-25'), t('05-29'), t('05-27'))           # 2 days early
check('T1 early return: all 4 planned days are invoiced, no refund',
      [(x['code'], x['amount']) for x in inv_early.get('lines', [])] == [('kiralama', 6702)] and inv_early.get('total') == 8042.4,
      inv_early.get('lines'))
check('S10 pick-up / return times after the simulated "now" are accepted', late26.get('status') == 'completed', late26.get('status'))
check('S11 odometer continuity between rentals is not checked (arc_11 handed over at 1000 km, earlier return 19150 km)',
      late26.get('pickupRecord', {}).get('odometerKm') == 1000, late26.get('pickupRecord'))
st, js = req('GET', '/vehicles?branchId=ANK', ADMIN)
check('S11 one-way rental does not move the car (arc_08 still listed in ANK)', st == 200 and 'arc_08' in ids(js), ids(js))

# S12 - a late return does not touch the next reservation of the car
a = create(C1, booking('arc_10', t('05-10'), t('05-12')))
b = create(C2, booking('arc_10', t('05-12', 13), t('05-14', 13), driverBirthDate='1988-01-01'))
req('POST', '/reservations/%s/pickup' % a.get('id'), ADMIN, {'pickedUpAt': t('05-10'), 'odometerKm': 46000, 'fuelLevel': 8})
st, js = req('POST', '/reservations/%s/return' % a.get('id'), ADMIN, {'returnedAt': t('05-13', 12), 'odometerKm': 46100, 'fuelLevel': 8})
st2, b2 = req('GET', '/reservations/%s' % b.get('id'), ADMIN)
check('S12 return 26 h late is accepted although the next rental of the car has started; that reservation is unchanged',
      st == 200 and st2 == 200 and b2.get('status') == 'confirmed' and b2.get('pickupAt') == t('05-12', 13), '%s %s' % (st, b2.get('status') if isinstance(b2, dict) else b2))

print('-' * 70)
# ---------------------------------------------------------------------------
# Remaining traps
# ---------------------------------------------------------------------------
valid = booking('arc_01', t('04-01'), t('04-03'))
st_a, _ = req('POST', '/reservations', ADMIN, valid)
st_s, _ = req('POST', '/reservations', STAFF, valid)
st_q, _ = req('POST', '/quotes', ADMIN, valid)
check('T2 admin and staff cannot create reservations or quotes (403)', [st_a, st_s, st_q] == [403, 403, 403], [st_a, st_s, st_q])
st, js = req('GET', '/reservations?page=99&pageSize=20', C1)
check('T4 page after the last one -> 200 with empty data', st == 200 and js['data'] == [] and js['meta']['total'] > 0 and js['meta']['page'] == 99, js.get('meta'))

# ---------------------------------------------------------------------------
# Remaining contract-silent behaviours
# ---------------------------------------------------------------------------
st, js = req('POST', '/quotes', STAFF, raw='{"garbage": true')
check('S1 role check (403) comes before body validation (400)', st == 403, st)
st, js = req('POST', '/reservations/%s/pickup' % first.get('id'), STAFF, {'bogus': 1})
check('S1 branch check (403) comes before body validation (400)', st == 403, st)      # arc_11 is an IZM car
chain = [
    booking('arc_99', t('04-03'), t('04-01')),                                               # unknown car + bad period
    booking('arc_06', t('04-03'), t('04-01')),                                               # out of service + bad period
    booking('arc_01', t('03-10', 10), t('03-10', 10)),                                       # bad period + too soon
    booking('arc_01', t('03-10', 10), t('03-12', 10), driverBirthDate='2010-01-01'),         # too soon + too young
    booking('arc_01', '2026-06-18T10:00:00+03:00', '2026-07-28T10:00:00+03:00'),             # too far + too long
    booking('arc_01', t('04-01'), t('05-10'), driverBirthDate='2010-01-01'),                 # too long + too young
    booking('arc_01', t('04-01'), t('04-03'), driverBirthDate='2010-01-01', licenseIssuedOn='2026-01-01'),
    booking('arc_01', t('04-01'), t('04-03'), licenseIssuedOn='2025-06-01', couponCode='XYZ'),
    booking('arc_02', t('03-14'), t('03-15'), couponCode='XYZ'),                             # bad coupon + car booked
    booking('arc_02', t('03-14'), t('03-15'), couponCode='BAHAR15'),                         # coupon not applicable + car booked
]
codes = [code_of(req('POST', '/quotes', C1, b)[1]) for b in chain]
check('S2 several violated rules: one error, in the fixed order of the key',
      codes == ['VEHICLE_NOT_FOUND', 'VEHICLE_OUT_OF_SERVICE', 'INVALID_PERIOD', 'PICKUP_TOO_SOON', 'PICKUP_TOO_FAR', 'RENTAL_TOO_LONG',
                'DRIVER_TOO_YOUNG', 'LICENSE_TOO_NEW', 'COUPON_INVALID', 'COUPON_NOT_APPLICABLE'], codes)
st, js = req('POST', '/reservations/rez_1012/pickup', ADMIN, {'bogus': 1})
check('S2 body validation (400) comes before the state check (409)', st == 400, st)
st, js = req('POST', '/quotes', C1, booking('arc_01', t('04-01'), t('04-03'), driverBirthDate='1990-06-14', licenseIssuedOn='1985-01-01'))
check('S3 licence issued before the birth date is accepted', st == 200, st)
st, js = req('POST', '/quotes', C1, booking('arc_01', t('04-01'), t('04-03'), driverBirthDate='1890-01-01'))
check('S3 no maximum driver age', st == 200, st)
st, js = req('POST', '/quotes', C1, booking('arc_01', t('04-01'), t('04-04'), couponCode='bahar15'))
st2, js2 = req('POST', '/quotes', C1, booking('arc_01', t('04-01'), t('04-04'), couponCode=''))
st3, js3 = req('POST', '/quotes', C1, booking('arc_01', t('04-01'), t('04-04'), couponCode=None))
check('S5 coupon codes are case-sensitive; empty string is an unknown code (422 COUPON_INVALID); null means no coupon',
      [st, code_of(js), st2, code_of(js2), st3] == [422, 'COUPON_INVALID', 422, 'COUPON_INVALID', 200], [st, code_of(js), st2, code_of(js2), st3])
st, js = req('DELETE', '/reservations/rez_1004', C1)
st2, js2 = req('GET', '/vehicles/arc_01', C1)
st3, js3 = req('GET', '/vehicles/arc_01')
check('S6 unsupported method -> 405 METHOD_NOT_ALLOWED; unknown path -> 404 NOT_FOUND (401 without token)',
      [st, code_of(js), st2, code_of(js2), st3] == [405, 'METHOD_NOT_ALLOWED', 404, 'NOT_FOUND', 401], [st, code_of(js), st2, code_of(js2), st3])
st, js = req('POST', '/quotes', C1, raw=json.dumps(valid), headers={'Content-Type': 'text/plain'})
check('S7 Content-Type is not checked (JSON sent as text/plain is processed)', st == 200, st)
st, js = req('GET', '/vehicles?colour=red&page=1&page=7', C1)
st2, js2 = req('GET', '/reservations?vehicleId=arc_99', ADMIN)
check('S8 unknown query parameters are ignored; a repeated parameter uses its first value; unknown vehicleId -> empty list',
      st == 200 and js['meta']['page'] == 1 and st2 == 200 and js2['data'] == [], js.get('meta') if isinstance(js, dict) else js)
r = create(C1, booking('arc_01', t('06-05'), t('06-06')))
st, js = req('POST', '/reservations/%s/cancel' % r.get('id'), C1, raw='this is not json')
check('S13 a body sent to cancel is ignored', st == 200 and js.get('status') == 'cancelled', st)
st, js = req('POST', '/reservations/rez_1004/pickup', STAFF, {'pickedUpAt': t('03-14'), 'odometerKm': 60700, 'fuelLevel': 8})
check('S14 a hand-over without note keeps the existing staffNote',
      st == 200 and isinstance(js.get('staffNote'), str) and 'depozito' in js['staffNote'], st)

# ---------------------------------------------------------------------------
# Robustness: no crash, no internals
# ---------------------------------------------------------------------------
bad_bodies = ['null', '[]', '"text"', '42', '{bad json', '']
codes = []
leak = False
for raw in bad_bodies:
    for path in ('/quotes', '/reservations'):
        st, js = req('POST', path, C1, raw=raw)
        codes.append(st)
        leak = leak or any(w in json.dumps(js) for w in ('stack', 'server.js', 'node:', '    at '))
check('R1 non-object / malformed bodies -> 400 VALIDATION_ERROR, no internals', set(codes) == {400} and not leak, codes)
st, js = req('GET', '/reservations?page=abc', C1)
st2, js2 = req('GET', '/reservations?pageSize=0', C1)
st3, js3 = req('GET', '/reservations?pageSize=51', C1)
check('R2 bad paging values -> 400', [st, st2, st3] == [400, 400, 400], [st, st2, st3])
st, js = req('GET', '/health')
check('R3 server still answers', st == 200 and js.get('status') == 'ok', st)

print('-' * 70)
passed = sum(1 for _, ok in results if ok)
print('%d/%d checks behaved as designed.' % (passed, len(results)))
sys.exit(0 if passed == len(results) else 1)
