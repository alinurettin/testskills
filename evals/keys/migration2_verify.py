#!/usr/bin/env python3
"""EVALUATOR-ONLY reference reconciliation for evals/trial-migration2.

Implements the mapping spec (inputs/esleme_spesifikasyonu.md) independently of the
generator, reconciles the legacy and target exports, classifies every discrepancy,
and asserts that:
  * every planted item K1..K11 reproduces exactly on the expected records,
  * there is NO discrepancy outside the planted items,
  * every trap T1..T4 looks wrong to a naive comparison but is correct per the spec.
Python 3 stdlib only.  Usage:  python migration2_verify.py   (exit code 0 = all checks pass)
"""
import csv
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP

HERE = os.path.dirname(os.path.abspath(__file__))
INP = os.path.normpath(os.path.join(HERE, '..', 'trial-migration2', 'inputs'))
EXP = json.load(open(os.path.join(HERE, 'migration2_expected.json'), encoding='utf-8'))

STATUS = {'A': 'ACTIVE', 'I': 'CANCELLED', 'S': 'EXPIRED', 'Y': 'RENEWED'}
PRODUCT = {'KSK': 'MOTOR_OWN_DAMAGE', 'TRF': 'MOTOR_TPL', 'KNT': 'HOME', 'ISY': 'COMMERCIAL_PROPERTY',
           'FKZ': 'PERSONAL_ACCIDENT', 'SYH': 'TRAVEL_HEALTH'}
CURRENCY = {'TL': 'TRY', '': 'TRY', 'USD': 'USD', 'EUR': 'EUR'}
AGENCY = {'A01': 'ACN-3401', 'A02': 'ACN-3402', 'A03': 'ACN-0601', 'A04': 'ACN-3501', 'A05': 'ACN-1601',
          'A06': 'ACN-0701', 'A07': 'ACN-4201', 'A08': 'ACN-2701', 'A09': 'ACN-3502', 'A10': 'ACN-6101'}
CUTOFF = '2026-09-30'
Q2 = Decimal('0.01')

results = []


def check(name, cond, detail=''):
    results.append((name, bool(cond), detail))


def tr_num(s):
    s = s.strip()
    neg = s.endswith('-')
    v = Decimal(s.rstrip('-').replace('.', '').replace(',', '.'))
    return -v if neg else v


def to_utc(s, fmt):
    return (datetime.strptime(s, fmt) - timedelta(hours=3)).strftime('%Y-%m-%dT%H:%M:%SZ')


def read_legacy(name):
    raw = open(os.path.join(INP, 'kaynak', name), 'rb').read()
    txt = raw.decode('cp1254')
    if name == 'POLMAS.csv':   # TAKSIT.csv is pure ASCII (numbers/dates only)
        check(f'input {name} decodes as cp1254 and has Turkish chars', any(c in txt for c in 'şğıİŞĞ'))
        try:
            raw.decode('utf-8')
            check(f'input {name} is NOT valid UTF-8 (true cp1254 bytes)', False)
        except UnicodeDecodeError:
            check(f'input {name} is NOT valid UTF-8 (true cp1254 bytes)', True)
    check(f'input {name} uses CRLF line endings', b'\r\n' in raw)
    return list(csv.DictReader(txt.splitlines(), delimiter=';'))


def read_target(name):
    raw = open(os.path.join(INP, 'hedef', name), 'rb').read()
    check(f'input {name} is UTF-8 without BOM', not raw.startswith(b'\xef\xbb\xbf'))
    return list(csv.DictReader(raw.decode('utf-8').splitlines()))


POL = read_legacy('POLMAS.csv')
TAK = read_legacy('TAKSIT.csv')
NPOL = read_target('policies.csv')
NINS = read_target('installments.csv')
check('legacy POLMAS rows parse with 17 fields', all(len(r) == 17 and None not in r for r in POL))
check('legacy TAKSIT rows parse with 7 fields', all(len(r) == 7 and None not in r for r in TAK))

# ------------------------------------------------------------------ expected target per spec
scope = {r['POL_NO']: r for r in POL if r['DURUM_KD'] in STATUS}
quotes = {r['POL_NO']: r for r in POL if r['DURUM_KD'] == 'B'}
check('every legacy policy is in scope or a quote', len(scope) + len(quotes) == len(POL))

exp_pol = {}
for k, r in scope.items():
    gross = tr_num(r['BRUT_PRIM'])
    cur = CURRENCY[r['DOVIZ']]
    fx = tr_num(r['KUR']) if r['KUR'] else (Decimal('1') if cur == 'TRY' else None)
    exp_pol[k] = {
        'policy_id': 'KYS-' + k, 'legacy_policy_no': k, 'customer_no': r['MUST_NO'],
        'insured_name': r['SIGORTALI_ADI'].strip(), 'product_code': PRODUCT[r['URUN_KD']],
        'status': STATUS[r['DURUM_KD']],
        'start_date': datetime.strptime(r['BAS_TAR'], '%d.%m.%Y').date().isoformat(),
        'end_date': (datetime.strptime(r['BIT_TAR'], '%d/%m/%Y').date() - timedelta(days=1)).isoformat(),
        'currency': cur, 'gross_premium': f'{gross:.2f}', 'fx_rate': f'{fx:.4f}',
        'premium_try': f'{(gross * fx).quantize(Q2, ROUND_HALF_UP):.2f}',
        'installment_count': r['TAKSIT_SAY'], 'agency_code': AGENCY[r['ACENTE_KD']],
        'city': r['IL'].strip(), 'address_line': r['ADRES'].strip(),
        'loss_payee': r['DAIN_MURTEHIN'].strip(),
        'cancel_date': datetime.strptime(r['IPTAL_TAR'], '%d.%m.%Y').date().isoformat() if r['IPTAL_TAR'] else '',
        'updated_at': to_utc(r['SON_ISLEM_ZMN'], '%d.%m.%Y %H:%M:%S'),
    }

exp_ins = {}
for t in TAK:
    if t['POL_NO'] not in scope:
        continue
    typ = {'N': 'REGULAR', 'Z': 'REFUND'}[t['TAKSIT_TIP']]
    due = datetime.strptime(t['VADE_TAR'], '%d.%m.%Y').date()
    if typ == 'REFUND':
        st = 'REFUNDED' if t['ODEME_ZMN'] else 'REFUND_PENDING'
    elif t['ODEME_ZMN']:
        local_day = datetime.strptime(t['ODEME_ZMN'], '%d/%m/%Y %H:%M').date()
        st = 'PAID_ON_TIME' if local_day <= due else 'PAID_LATE'
    else:
        st = 'OVERDUE' if due.isoformat() < CUTOFF else 'OPEN'
    exp_ins[(t['POL_NO'], t['TAKSIT_NO'])] = {
        'policy_id': 'KYS-' + t['POL_NO'], 'installment_no': t['TAKSIT_NO'], 'installment_type': typ,
        'due_date': due.isoformat(), 'amount': f"{tr_num(t['TUTAR']):.2f}",
        'currency': CURRENCY[scope[t['POL_NO']]['DOVIZ']],
        'paid_amount': f"{tr_num(t['ODENEN_TUTAR']):.2f}" if t['ODENEN_TUTAR'] else '',
        'paid_at': to_utc(t['ODEME_ZMN'], '%d/%m/%Y %H:%M') if t['ODEME_ZMN'] else '',
        'payment_status': st,
    }

# legacy is internally consistent (spec M4/M5 hold in the source)
for k, r in scope.items():
    s = sum((tr_num(t['TUTAR']) for t in TAK if t['POL_NO'] == k), Decimal('0'))
    nreg = sum(1 for t in TAK if t['POL_NO'] == k and t['TAKSIT_TIP'] == 'N')
    if s != tr_num(r['BRUT_PRIM']) or nreg != int(r['TAKSIT_SAY']):
        check(f'legacy invariant M4/M5 holds for {k}', False)
check('legacy invariants M4/M5 hold for all in-scope policies',
      all(n for name, n, _ in results if name.startswith('legacy invariant')))
check('every legacy installment belongs to a legacy policy', all(t['POL_NO'] in POL_NO_SET
      for t in TAK) if (POL_NO_SET := {r['POL_NO'] for r in POL}) else False)

# ------------------------------------------------------------------ reconcile policies
tp = defaultdict(list)
for r in NPOL:
    tp[r['legacy_policy_no']].append(r)
missing_pol = sorted(set(exp_pol) - set(tp))
extra_pol = sorted(set(tp) - set(exp_pol))
dup_pol = sorted(k for k, v in tp.items() if len(v) > 1)
pdiff = defaultdict(list)          # field -> [(key, expected, actual)]
for k, e in exp_pol.items():
    if k not in tp:
        continue
    a = tp[k][0]
    for f, v in e.items():
        if a[f] != v:
            pdiff[f].append((k, v, a[f]))

# ------------------------------------------------------------------ reconcile installments
ti = defaultdict(list)
for r in NINS:
    ti[(r['policy_id'][4:], r['installment_no'])].append(r)
missing_ins = sorted(set(exp_ins) - set(ti))
extra_ins = sorted(set(ti) - set(exp_ins))
dup_ins = sorted(k for k, v in ti.items() if len(v) > 1)
target_pids = {r['policy_id'] for r in NPOL}
orphans = sorted({(r['policy_id'][4:], r['installment_no']) for r in NINS if r['policy_id'] not in target_pids})
idiff = defaultdict(list)
for k, e in exp_ins.items():
    for a in ti.get(k, []):
        for f, v in e.items():
            if a[f] != v:
                idiff[f].append(('%s/%s' % k, v, a[f]))
dup_identical = all(
    all({f: r[f] for f in exp_ins[k]} == {f: ti[k][0][f] for f in exp_ins[k]} for r in ti[k]) for k in dup_ins)
dup_runs = {k: sorted(r['migration_run_id'] for r in ti[k]) for k in dup_ins}

# target invariants
sum_by_pol = defaultdict(Decimal)
cnt_reg = Counter()
for r in NINS:
    sum_by_pol[r['policy_id']] += Decimal(r['amount'])
    if r['installment_type'] == 'REGULAR':
        cnt_reg[r['policy_id']] += 1
m4_viol = sorted(r['legacy_policy_no'] for r in NPOL if Decimal(r['gross_premium']) != sum_by_pol[r['policy_id']])
m5_viol = sorted(r['legacy_policy_no'] for r in NPOL if int(r['installment_count']) != cnt_reg[r['policy_id']])
src_ag, tgt_ag = defaultdict(Decimal), defaultdict(Decimal)
for k, e in exp_pol.items():
    src_ag[(e['agency_code'], e['currency'])] += Decimal(e['gross_premium'])
for r in NPOL:
    tgt_ag[(r['agency_code'], r['currency'])] += Decimal(r['gross_premium'])
ag_mismatch = sorted({a for a, c in set(src_ag) | set(tgt_ag) if src_ag[(a, c)] != tgt_ag[(a, c)]})
src_cur, tgt_cur = defaultdict(Decimal), defaultdict(Decimal)
for e in exp_pol.values():
    src_cur[e['currency']] += Decimal(e['gross_premium'])
for r in NPOL:
    tgt_cur[r['currency']] += Decimal(r['gross_premium'])

# ------------------------------------------------------------------ classify against the key
def keys(lst):
    return sorted(x[0] for x in lst)


def translit(s):
    return s.translate(str.maketrans('ıİşŞğĞüÜöÖçÇ', 'iIsSgGuUoOcC'))


k_exp = EXP
# K1
check('K1 status S -> SUSPENDED (should be EXPIRED) on exactly the S policies',
      keys(pdiff['status']) == k_exp['K1_status_S_to_SUSPENDED']
      and all(v == 'EXPIRED' and a == 'SUSPENDED' for _, v, a in pdiff['status']),
      f"{len(pdiff['status'])} rows")
# K2
check('K2 address_line truncated to 50 chars on exactly the long-address policies',
      keys(pdiff['address_line']) == k_exp['K2_address_truncated_50']
      and all(len(v) > 50 and a == v[:50] for _, v, a in pdiff['address_line']),
      f"{len(pdiff['address_line'])} rows")
check('K2 no address <= 50 chars was altered', all(len(v) > 50 for _, v, _a in pdiff['address_line']))
# K3
check('K3 empty IPTAL_TAR -> cancel_date 1900-01-01 (should be NULL)',
      keys(pdiff['cancel_date']) == k_exp['K3_cancel_date_1900']
      and all(v == '' and a == '1900-01-01' for _, v, a in pdiff['cancel_date']),
      f"{len(pdiff['cancel_date'])} rows")
# K4
check('K4 loss_payee transliterated (only this text field)',
      keys(pdiff['loss_payee']) == k_exp['K4_loss_payee_transliterated']
      and all(a == translit(v) and a != v for _, v, a in pdiff['loss_payee']),
      f"{len(pdiff['loss_payee'])} rows")
check('K4 insured_name / city / address keep Turkish chars (no diffs besides K2)',
      not pdiff['insured_name'] and not pdiff['city'])
# K5
k5 = k_exp['K5_missing_parent']
check('K5 exactly one in-scope policy missing in target', missing_pol == k5['policy'], str(missing_pol))
check('K5 its installments are orphans in target (FK violation)',
      ['%s/%s' % o for o in orphans] == sorted(k5['orphan_installments']), str(orphans))
check('K5 root cause: the missing policy has a quoted ";" inside ADRES',
      all(';' in scope[k]['ADRES'] for k in missing_pol))
# K6
k6 = k_exp['K6_lost_installments_ge10']
check('K6 installments with TAKSIT_NO >= 10 missing in target',
      sorted('%s/%s' % m for m in missing_ins) == sorted(k6['installments'])
      and all(int(n) >= 10 for _, n in missing_ins), str(missing_ins))
check('K6 no installment with TAKSIT_NO >= 10 exists in target', all(int(r['installment_no']) < 10 for r in NINS))
# K7
check('K7 duplicate (policy_id, installment_no) rows from re-run',
      sorted('%s/%s' % k for k in dup_ins) == sorted(k_exp['K7_duplicate_installments_rerun'])
      and dup_identical and all(v == ['R1', 'R2'] for v in dup_runs.values()), str(dup_runs))
check('K6/K7 masking: target installment count equals in-scope source count',
      len(NINS) == len(exp_ins), f'{len(NINS)} vs {len(exp_ins)}')
# K8
k8 = k_exp['K8_refund_sign_lost']
amt = idiff['amount']
check('K8 refund amounts lost their minus sign (amount and paid_amount)',
      keys(amt) == sorted(k8['installments']) and all(Decimal(a) == -Decimal(v) and Decimal(v) < 0 for _, v, a in amt)
      and keys(idiff['paid_amount']) == sorted(k8['installments']), str(keys(amt)))
check('K8 M4 violated for refund policies (plus K6 policies, plus K7 dup policy)',
      set(k8['policies']) <= set(m4_viol), str(m4_viol))
expected_m4 = set(k8['policies']) | set(k6['policies']) | {k.split('/')[0] for k in k_exp['K7_duplicate_installments_rerun']}
check('M4 violations are exactly K6 + K7 + K8 policies', set(m4_viol) == expected_m4, str(m4_viol))
check('M5 violations are exactly K6 + K7 policies',
      set(m5_viol) == set(k6['policies']) | {k.split('/')[0] for k in k_exp['K7_duplicate_installments_rerun']},
      str(m5_viol))
# K9
k9 = k_exp['K9_agency_A04_A09_swapped']
ag = pdiff['agency_code']
check('K9 A04 <-> A09 agency codes swapped',
      sorted(x[0] for x in ag) == sorted(k9['A04'] + k9['A09'])
      and all((v, a) in {('ACN-3501', 'ACN-3502'), ('ACN-3502', 'ACN-3501')} for _, v, a in ag), f'{len(ag)} rows')
check('K9 per-agency totals mismatch only for ACN-3501/ACN-3502 (plus agency of K5 policy)',
      set(ag_mismatch) == {'ACN-3501', 'ACN-3502', AGENCY[scope[missing_pol[0]]['ACENTE_KD']]}, str(ag_mismatch))
check('K9 overall TRY total is unaffected by the swap (diff == missing policy only)',
      src_cur['TRY'] - tgt_cur['TRY'] == Decimal(exp_pol[missing_pol[0]]['gross_premium']))
# K10
ps = idiff['payment_status']
check('K10 PAID_LATE shown as PAID_ON_TIME for payments 00:00-02:59 local on due+1',
      keys(ps) == k_exp['K10_late_flag_utc_date'] and all(v == 'PAID_LATE' and a == 'PAID_ON_TIME' for _, v, a in ps),
      str(ps))
check('K10 those rows have UTC paid_at date == due_date (why naive check passes)',
      all(ti[tuple(k.split('/'))][0]['paid_at'][:10] == ti[tuple(k.split('/'))][0]['due_date'] for k, _, _ in ps))
# K11
check('K11 fx_rate rounded to 2 decimals on foreign policies with 4-decimal rates',
      keys(pdiff['fx_rate']) == k_exp['K11_fx_rate_rounded']
      and all(Decimal(a) == Decimal(v).quantize(Q2, ROUND_HALF_UP) for _, v, a in pdiff['fx_rate']), str(pdiff['fx_rate']))
check('K11 premium_try wrong on the same policies',
      keys(pdiff['premium_try']) == k_exp['K11_fx_rate_rounded'], str(pdiff['premium_try']))
check('K11 foreign policies with 2-decimal rates are correct', not set(k_exp['K11_fx_rate_unaffected_foreign'])
      & set(keys(pdiff['fx_rate']) + keys(pdiff['premium_try'])))

# no unexpected discrepancy anywhere
known_p = {'status', 'address_line', 'cancel_date', 'loss_payee', 'agency_code', 'fx_rate', 'premium_try'}
known_i = {'amount', 'paid_amount', 'payment_status'}
check('no unexpected policy field discrepancies', set(f for f in pdiff if pdiff[f]) == known_p,
      str({f: len(v) for f, v in pdiff.items() if f not in known_p}))
check('no unexpected installment field discrepancies', set(f for f in idiff if idiff[f]) == known_i,
      str({f: len(v) for f, v in idiff.items() if f not in known_i}))
check('no extra installment keys other than none (quotes absent)', not extra_ins, str(extra_ins))
check('no extra / duplicate policies in target', not extra_pol and not dup_pol, str(extra_pol + dup_pol))
check('installment currency correct everywhere', not idiff['currency'])

# ------------------------------------------------------------------ traps
t1 = k_exp['T1_utc_shift_crosses_midnight']
naive_upd = sorted(k for k, e in exp_pol.items() if k in tp and
                   tp[k][0]['updated_at'][:10] != datetime.strptime(scope[k]['SON_ISLEM_ZMN'], '%d.%m.%Y %H:%M:%S').date().isoformat())
check('T1 naive date compare of updated_at differs exactly on the late-night rows', naive_upd == t1['policies'], str(naive_upd))
check('T1 updated_at is spec-correct (no diff after local->UTC)', not pdiff['updated_at'])
naive_paid = sorted('%s/%s' % k for k in exp_ins if k in ti and exp_ins[k]['paid_at'] and
                    ti[k][0]['paid_at'][:10] != datetime.strptime(
                        [t for t in TAK if (t['POL_NO'], t['TAKSIT_NO']) == k][0]['ODEME_ZMN'], '%d/%m/%Y %H:%M').date().isoformat())
check('T1 naive date compare of paid_at differs exactly on 00:00-02:59 payments', naive_paid == t1['installments'], str(naive_paid))
check('T1 paid_at is spec-correct', not idiff['paid_at'])
check('T1 on-time midnight payments keep PAID_ON_TIME (correct)',
      all(ti[tuple(k.split('/'))][0]['payment_status'] == 'PAID_ON_TIME' for k in k_exp['T1_on_time_midnight_payments']))
t2 = k_exp['T2_quotes_not_migrated']
check('T2 quotes absent from target (correct per spec 1)', sorted(quotes) == t2['policies']
      and not set(quotes) & set(tp) and not any(r['policy_id'][4:] in quotes for r in NINS))
check('T2 naive raw count gap = quotes + K5', len(POL) - len(NPOL) == len(quotes) + 1
      and len(TAK) - len(NINS) == len(t2['installments']))
t3 = k_exp['T3_empty_currency_to_TRY']
check('T3 empty DOVIZ/KUR -> TRY/1.0000 and is spec-correct',
      sorted(k for k, r in scope.items() if r['DOVIZ'] == '') == t3
      and all(tp[k][0]['currency'] == 'TRY' and tp[k][0]['fx_rate'] == '1.0000' for k in t3))
naive_end = [k for k in exp_pol if k in tp and tp[k][0]['end_date'] !=
             datetime.strptime(scope[k]['BIT_TAR'], '%d/%m/%Y').date().isoformat()]
check('T4 every end_date differs from BIT_TAR naively but equals BIT_TAR-1 (spec)',
      len(naive_end) == len(tp) - 0 and not pdiff['end_date'])
check('T4 month-boundary examples correct', all(tp[k][0]['end_date'][8:] in ('28', '29', '30', '31')
                                                 for k in k_exp['T4_month_boundary_examples']),
      str(k_exp['T4_month_boundary_examples']))

# ETL report claims vs reality (context)
rep = open(os.path.join(INP, 'etl_calistirma_raporu.txt'), encoding='utf-8').read()
check('ETL report claims 60 target policies (actual 59)', 'hedef 60' in rep and len(NPOL) == 59)
check('ETL report installment count claim equals actual (masking)', f'hedef {len(NINS)}' in rep)

# ------------------------------------------------------------------ output
w = max(len(n) for n, _, _ in results)
fails = 0
for n, ok, det in results:
    if n.startswith('legacy invariant') and ok:
        continue
    print(('PASS ' if ok else 'FAIL ') + n.ljust(w) + ('  ' + det if det and not ok else ''))
    fails += (not ok)
print('\nsummary:', {'policies src/scope/target': (len(POL), len(scope), len(NPOL)),
                     'installments src/scope/target': (len(TAK), len(exp_ins), len(NINS)),
                     'm4_violations': m4_viol, 'agency_total_mismatch': ag_mismatch})
print('RESULT:', 'ALL CHECKS PASSED' if not fails else f'{fails} CHECK(S) FAILED')
sys.exit(1 if fails else 0)
