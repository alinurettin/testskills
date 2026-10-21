#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""testdata2_grade.py - objective grader for trial-testdata2 (EVALUATOR-ONLY, stdlib only).

Usage:
  python testdata2_grade.py <agent_dir> [--trial DIR] [--truth FILE] [--no-exec] [--json OUT.json]

<agent_dir> is the agent workspace (containing cikti/) or the cikti/ folder itself.
Part 1 reads cikti/uretilen/*.csv, Part 2 reads cikti/maskeli/*.csv and compares them
row-by-row with <trial>/girdiler/uretim_kesiti/*.csv using testdata2_truth.json.
Unless --no-exec is given, the agent's cikti/maskele.py|.js is executed twice
(MASKE_ANAHTARI=pusula-uat-2026, separate processes) to measure determinism.
Report traps T1-T3 are judged manually; the grader prints candidate lines from rapor.md.
"""
import csv, datetime as dt, io, json, os, re, shutil, subprocess, sys, tempfile
from collections import Counter, defaultdict
from decimal import Decimal, InvalidOperation

HERE = os.path.dirname(os.path.abspath(__file__))
SNAP = dt.date(2026, 9, 30)
KEY = 'pusula-uat-2026'

# ------------------------------------------------------------------ algorithms
def tckn_valid(s):
    if not isinstance(s, str) or len(s) != 11 or not s.isdigit() or s[0] == '0':
        return False
    d = [int(c) for c in s]
    d10 = (sum(d[0:9:2]) * 7 - sum(d[1:8:2])) % 10
    return d10 == d[9] and (sum(d[:10]) % 10) == d[10]

def vkn_valid(s):
    if not isinstance(s, str) or len(s) != 10 or not s.isdigit():
        return False
    d = [int(c) for c in s]
    tot = 0
    for i in range(9):
        t = (d[i] + 9 - i) % 10
        v = (t * 2 ** (9 - i)) % 9
        if t != 0 and v == 0:
            v = 9
        tot += v
    return (10 - tot % 10) % 10 == d[9]

def iban_norm(s):
    return re.sub(r'[\s-]', '', s or '').upper()

def iban_valid(s):
    s = iban_norm(s)
    if len(s) != 26 or not s.startswith('TR') or not s[2:].isdigit():
        return False
    return int(''.join(str(int(c, 36)) for c in s[4:] + s[:4])) % 97 == 1

def iban_from(bank5, sube, hno):
    bban = bank5 + '0' + sube + '0000' + hno
    num = int(''.join(str(int(c, 36)) for c in bban + 'TR00'))
    return 'TR%02d' % (98 - num % 97) + bban

def is_leap(y):
    return y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)

def b18(d):
    y = d.year + 18
    if d.month == 2 and d.day == 29 and not is_leap(y):
        return dt.date(y, 3, 1)
    return d.replace(year=y)

def pdate(s, fmt='%Y-%m-%d'):
    try:
        return dt.datetime.strptime(s, fmt)
    except (ValueError, TypeError):
        return None

def dec(s):
    if not isinstance(s, str) or not re.fullmatch(r'-?\d+\.\d{2}', s):
        return None
    try:
        return Decimal(s)
    except InvalidOperation:
        return None

def digits(s):
    return re.sub(r'\D', '', s or '')

def phone_nat(s):
    d = digits(s)
    if d.startswith('0090'):
        d = d[4:]
    elif len(d) == 12 and d.startswith('90'):
        d = d[2:]
    elif len(d) == 11 and d.startswith('0'):
        d = d[1:]
    return d

FOLD = str.maketrans('çğıöşüâîû', 'cgiosuaiu')

def tr_fold(s):
    s = (s or '').replace('İ', 'i').replace('I', 'ı').lower().replace('̇', '')
    return re.sub(r'\s+', ' ', s.translate(FOLD))

def email_norm(s):
    s = (s or '').lower()
    s = re.sub(r'\s*(\[at\]|\(at\)|\{at\}|\[@\]|\s at\s)\s*', '@', s)
    s = re.sub(r'\s*@\s*', '@', s)
    return re.sub(r'\s*(\[dot\]|\(dot\))\s*', '.', s)

def read_csv(path):
    if not os.path.isfile(path):
        return None, None
    with open(path, encoding='utf-8-sig', newline='') as f:
        text = f.read()
    first = text.split('\n', 1)[0]
    delim = ';' if first.count(';') >= first.count(',') else ','
    rows = list(csv.reader(io.StringIO(text), delimiter=delim))
    rows = [r for r in rows if r != []]
    if not rows:
        return [], []
    head = [h.strip() for h in rows[0]]
    return head, [dict(zip(head, r + [''] * (len(head) - len(r)))) for r in rows[1:]]

# ------------------------------------------------------------------ Part 1
M_COLS = 'musteri_no;musteri_tipi;tckn;vkn;ad;soyad;unvan;sirket_turu;dogum_tarihi;kurulus_tarihi;cinsiyet;il;ilce;eposta;telefon;kayit_tarihi'.split(';')
H_COLS = 'sube_kodu;hesap_no;musteri_no;hesap_turu;doviz;kmh_limiti;acilis_tarihi;iban;bakiye'.split(';')
I_COLS = 'islem_id;sube_kodu;hesap_no;islem_tarihi;islem_tipi;tutar;karsi_iban;aciklama'.split(';')
ILCE = {'İstanbul': {'Kadıköy', 'Beşiktaş', 'Üsküdar', 'Şişli', 'Bakırköy', 'Ataşehir'},
        'Ankara': {'Çankaya', 'Keçiören', 'Yenimahalle', 'Etimesgut'}, 'İzmir': {'Konak', 'Bornova', 'Karşıyaka', 'Buca'},
        'Bursa': {'Nilüfer', 'Osmangazi'}, 'Adana': {'Seyhan', 'Çukurova'}, 'Trabzon': {'Ortahisar'},
        'Şanlıurfa': {'Halfeti', 'Haliliye'}, 'Bayburt': {'Merkez'}}
SUBE = {'0101', '0102', '0103', '0207', '0208', '0315', '0316', '0420', '0512', '0611'}
SIGN = {'YATIRMA': 1, 'HAVALE_GELEN': 1, 'FAIZ': 1, 'CEKME': -1, 'HAVALE_GIDEN': -1, 'MASRAF': -1}


def grade_part1(udir):
    res = {'present': False, 'viol': defaultdict(list), 'sd': {}, 'notes': []}
    mh, M = read_csv(os.path.join(udir, 'musteri.csv'))
    hh, H = read_csv(os.path.join(udir, 'hesap.csv'))
    ih, I = read_csv(os.path.join(udir, 'islem.csv'))
    if M is None or H is None or I is None:
        res['notes'].append('uretilen/*.csv missing')
        return res
    res['present'] = True
    for name, got, exp in (('musteri', mh, M_COLS), ('hesap', hh, H_COLS), ('islem', ih, I_COLS)):
        if got != exp:
            res['viol']['HEADER'].append('%s header %s' % (name, got))
    V = res['viol']
    # ---- customers
    cust = {}
    seen_id, seen_mail = Counter(), Counter()
    for r in M:
        seen_id[r.get('tckn') or r.get('vkn')] += 1
        seen_mail[r.get('eposta', '')] += 1
    cnt = Counter(r.get('musteri_no') for r in M)
    for n, r in enumerate(M):
        mno, typ = r.get('musteri_no', ''), r.get('musteri_tipi', '')
        if not re.fullmatch(r'M\d{6}', mno) or cnt[mno] > 1:
            V['M_FMT'].append(n)
        ind, corp = typ == 'BIREYSEL', typ == 'KURUMSAL'
        if not (ind or corp):
            V['M_TYPE'].append(n)
            continue
        f = lambda k: r.get(k, '') != ''
        if ind:
            ok = f('tckn') and not f('vkn') and f('ad') and f('soyad') and not f('unvan') and not f('sirket_turu') \
                and f('dogum_tarihi') and not f('kurulus_tarihi') and r.get('cinsiyet') in ('E', 'K')
            if not tckn_valid(r.get('tckn')):
                V['M_TCKN'].append(n)
        else:
            ok = f('vkn') and not f('tckn') and f('unvan') and r.get('sirket_turu') in ('AS', 'LTD', 'SAHIS') \
                and not f('ad') and not f('soyad') and not f('dogum_tarihi') and f('kurulus_tarihi') and not f('cinsiyet')
            if not vkn_valid(r.get('vkn')):
                V['M_VKN'].append(n)
        if not ok:
            V['M_FIELDS'].append(n)
        if seen_id[r.get('tckn') or r.get('vkn')] > 1:
            V['M_IDUNIQ'].append(n)
        if r.get('ilce') not in ILCE.get(r.get('il'), set()):
            V['M_ILCE'].append(n)
        if not re.fullmatch(r'[a-z0-9._-]+@example\.(com|test)', r.get('eposta', '')) or seen_mail[r.get('eposta')] > 1:
            V['M_EMAIL'].append(n)
        if not re.fullmatch(r'\+90 500 \d{3} \d{2} \d{2}', r.get('telefon', '')):
            V['M_PHONE'].append(n)
        kay = pdate(r.get('kayit_tarihi'))
        bad = kay is None or not (dt.datetime(2005, 1, 1) <= kay <= dt.datetime(2026, 9, 30))
        d18 = kur = None
        if ind:
            dob = pdate(r.get('dogum_tarihi'))
            if dob is None:
                bad = True
            else:
                d18 = b18(dob.date())
                bad = bad or dob.date() < dt.date(1926, 10, 1) or d18 > SNAP or (kay is not None and kay.date() < d18)
        else:
            k = pdate(r.get('kurulus_tarihi'))
            if k is None:
                bad = True
            else:
                kur = k.date()
                bad = bad or kur < dt.date(1950, 1, 1) or kur > SNAP or (kay is not None and kay.date() < kur)
        if bad:
            V['M_DATES'].append(n)
        cust[mno] = dict(typ=typ, kayit=kay.date() if kay else None, d18=d18, kur=kur,
                         feb29=bool(ind and (r.get('dogum_tarihi') or '').endswith('-02-29')))
    if M:
        share = Counter(r.get('musteri_tipi') for r in M)
        if share['KURUMSAL'] < 0.25 * len(M) or share['BIREYSEL'] < 0.5 * len(M):
            V['M_MIX'].append('dataset')
    # ---- accounts
    keys = Counter((r.get('sube_kodu'), r.get('hesap_no')) for r in H)
    ibans = Counter(r.get('iban') for r in H)
    acc = {}
    for n, r in enumerate(H):
        k = (r.get('sube_kodu'), r.get('hesap_no'))
        if keys[k] > 1 or k[0] not in SUBE or not re.fullmatch(r'[1-9]\d{7}', k[1] or ''):
            V['H_PK'].append(n)
        c = cust.get(r.get('musteri_no'))
        if c is None:
            V['H_FK'].append(n)
        lim = dec(r.get('kmh_limiti'))
        turu, dov = r.get('hesap_turu'), r.get('doviz')
        ok = turu in ('VADESIZ', 'KMH') and dov in ('TRY', 'USD', 'EUR') and lim is not None and dec(r.get('bakiye')) is not None
        if ok and turu == 'KMH':
            ok = dov == 'TRY' and Decimal('1000.00') <= lim <= Decimal('50000.00') and (c is None or c['typ'] == 'BIREYSEL')
        if ok and turu == 'VADESIZ':
            ok = lim == 0
        if not ok:
            V['H_TYPE'].append(n)
        ac = pdate(r.get('acilis_tarihi'))
        a = ac.date() if ac else None
        if a is None or a > SNAP or (c and ((c['kayit'] and a < c['kayit']) or (c['d18'] and a < c['d18']) or (c['kur'] and a < c['kur']))):
            V['H_DATES'].append(n)
        if not (k[0] in SUBE and re.fullmatch(r'[1-9]\d{7}', k[1] or '') and r.get('iban') == iban_from('00990', k[0], k[1])
                and iban_valid(r.get('iban')) and ibans[r.get('iban')] == 1):
            V['H_IBAN'].append(n)
        acc[k] = dict(row=n, turu=turu, lim=lim or Decimal(0), acilis=a, bakiye=dec(r.get('bakiye')), iban=r.get('iban'),
                      cust=c, tx=[])
    by_hno = defaultdict(set)
    for (s, h) in keys:
        by_hno[h].add(s)
    rep = sum(1 for h, s in by_hno.items() if len(s) >= 2)
    if rep < 3:
        V['H_REPEAT'].append('only %d hesap_no values repeat across branches' % rep)
    own_ibans = set(ibans)
    # ---- transactions
    ids = Counter(r.get('islem_id') for r in I)
    gid = gid_int = 0
    sd5 = 0
    for n, r in enumerate(I):
        if not re.fullmatch(r'[1-9]\d*', r.get('islem_id', '')) or ids[r.get('islem_id')] > 1:
            V['I_ID'].append(n)
        a = acc.get((r.get('sube_kodu'), r.get('hesap_no')))
        if a is None:
            V['I_FK'].append(n)
        d = pdate(r.get('islem_tarihi'))
        if d is None or d.date() > SNAP or (a and a['acilis'] and d.date() < a['acilis']):
            V['I_DATE'].append(n)
        if d and d.date() == SNAP:
            sd5 += 1
        tip, amt = r.get('islem_tipi'), dec(r.get('tutar'))
        if tip not in SIGN or amt is None or amt == 0 or (amt > 0) != (SIGN[tip] > 0):
            V['I_SIGN'].append(n)
        k = r.get('karsi_iban', '')
        if tip in ('HAVALE_GELEN', 'HAVALE_GIDEN'):
            internal = k in own_ibans
            okk = re.fullmatch(r'TR\d{24}', k or '') and iban_valid(k) and (a is None or k != a['iban']) and \
                (internal or k[4:9] in {'0099%d' % i for i in range(1, 9)})
            if not okk:
                V['I_KARSI'].append(n)
            if tip == 'HAVALE_GIDEN':
                gid += 1
                gid_int += internal
        elif k:
            V['I_KARSI'].append(n)
        if a is not None and d is not None and amt is not None:
            a['tx'].append((d, int(r.get('islem_id')) if (r.get('islem_id') or '').isdigit() else 0, amt))
    if gid and gid_int < 0.2 * gid:
        V['I_INTERNAL'].append('internal share %.1f%%' % (100.0 * gid_int / gid))
    # ---- balances + boundaries
    sd = dict(SD1=0, SD2=0, SD3=0, SD4=0, SD5=sd5, SD6=0, SD7=0)
    flagged = 0
    for k, a in acc.items():
        txs = sorted(a['tx'])
        bal, run_bad, hit0, hitlim = Decimal('0.00'), False, False, False
        for d, _i, amt in txs:
            bal += amt
            if bal < (-a['lim'] if a['turu'] == 'KMH' else 0):
                run_bad = True
            hit0 |= a['turu'] == 'VADESIZ' and bal == 0
            hitlim |= a['turu'] == 'KMH' and bal == -a['lim']
        if a['bakiye'] is None or bal != a['bakiye']:
            V['H_BAL'].append(a['row'])
        if run_bad:
            V['H_RUN'].append(a['row'])
        c = a['cust'] or {}
        s1 = bool(c.get('d18') and a['acilis'] == c['d18'])
        s3 = bool(c.get('kur') and a['acilis'] == c['kur'])
        s4 = any(d.date() == a['acilis'] for d, _i, _a in txs)
        sd['SD1'] += s1
        sd['SD2'] += s1 and c.get('feb29', False)
        sd['SD3'] += s3
        sd['SD4'] += s4
        sd['SD6'] += hit0
        sd['SD7'] += hitlim
        flagged += s1 or s3 or s4 or hit0 or hitlim
    sd['SD8_share'] = round(flagged / len(acc), 4) if acc else 0
    res['sd'] = sd
    res['counts'] = dict(musteri=len(M), hesap=len(H), islem=len(I))
    owners = Counter(r.get('musteri_no') for r in H)
    with_tx = sum(1 for a in acc.values() if a['tx'])
    res['volume_ok'] = len(M) >= 150 and len(H) >= 300 and len(I) >= 2000 and all(owners[m] for m in cust) \
        and (with_tx >= 0.9 * len(H) if H else False)
    # feb-29 customers must have zero date violations (K3)
    feb_rows = {n for n, r in enumerate(M) if r.get('musteri_tipi') == 'BIREYSEL' and (r.get('dogum_tarihi') or '').endswith('-02-29')}
    feb_mno = {M[n]['musteri_no'] for n in feb_rows}
    feb_acc_rows = {a['row'] for a in acc.values() if a['cust'] and H[a['row']].get('musteri_no') in feb_mno}
    res['feb29'] = dict(customers=len(feb_rows),
                        violations=len(feb_rows & set(V['M_DATES'])) + len(feb_acc_rows & set(V['H_DATES'])))
    tot = {'musteri': len(M), 'hesap': len(H), 'islem': len(I)}
    bad_rows = defaultdict(set)
    for rule, rows in V.items():
        t = {'M': 'musteri', 'H': 'hesap', 'I': 'islem'}.get(rule[0])
        for x in rows:
            if t and isinstance(x, int):
                bad_rows[t].add(x)
    res['rule_satisfaction'] = {t: round(100.0 * (tot[t] - len(bad_rows[t])) / tot[t], 2) if tot[t] else 0 for t in tot}
    return res


def score_part1(p):
    if not p['present']:
        return {'K1': 0, 'K2': 0, 'K3': 0, 'K4': 0, 'K5': 0}
    V, sd, n = p['viol'], p['sd'], p['counts']

    def nv(*rules):
        return sum(len(V.get(r, [])) for r in rules)

    def tier(rules, full, denom, half=None):
        v = nv(*rules)
        if v == 0:
            return full
        return (half if half is not None else full / 2) if denom and v <= 0.02 * denom else 0

    k = {}
    k['K1'] = tier(['M_FMT', 'M_TYPE', 'M_FIELDS', 'M_TCKN', 'M_VKN', 'M_IDUNIQ', 'M_ILCE', 'M_EMAIL', 'M_PHONE', 'M_MIX', 'HEADER'],
                   6, n['musteri'])
    k['K2'] = tier(['M_DATES', 'H_DATES', 'I_DATE'], 3, n['hesap']) + \
        0.6 * sum([sd['SD1'] >= 5, sd['SD3'] >= 3, sd['SD4'] >= 5, sd['SD5'] >= 5, sd['SD8_share'] >= 0.10])
    fb = p['feb29']
    k['K3'] = 10 if (sd['SD2'] >= 2 and fb['violations'] == 0) else (5 if sd['SD2'] == 1 and fb['violations'] == 0 else 0)
    k['K4'] = tier(['H_BAL'], 4, n['hesap']) + tier(['H_RUN'], 3, n['hesap']) + (1 if nv('H_TYPE') == 0 else 0) + \
        (1 if sd['SD6'] >= 5 else 0) + (1 if sd['SD7'] >= 3 else 0)
    k['K5'] = (2 if nv('H_PK') == 0 else 0) + (1 if nv('H_REPEAT') == 0 else 0) + (1 if nv('I_FK', 'H_FK') == 0 else 0) + \
        (2 if nv('H_IBAN') == 0 else 0) + (1 if nv('I_KARSI', 'I_INTERNAL') == 0 else 0) + (1 if nv('I_SIGN', 'I_ID') == 0 else 0)
    if not p['volume_ok']:
        k = {x: v / 2 for x, v in k.items()}
    return {x: round(v, 2) for x, v in k.items()}


# ------------------------------------------------------------------ Part 2
FILES = ('musteri', 'hesap', 'islem')
DATE_COLS = {('musteri', 'kayit_tarihi'): '%Y-%m-%d', ('musteri', 'kurulus_tarihi'): '%Y-%m-%d',
             ('hesap', 'acilis_tarihi'): '%Y-%m-%d', ('islem', 'islem_tarihi'): '%d.%m.%Y %H:%M:%S'}
TEXT_CELLS = (('musteri', 'notlar'), ('islem', 'aciklama'))
HVL = re.compile(r'HVL-\d{4}-\d{6}')


def load_dir(d):
    out = {}
    for f in FILES:
        h, rows = read_csv(os.path.join(d, f + '.csv'))
        out[f] = (h, rows)
    return out


def tier3(resid, full):
    return full if resid == 0 else (round(full * 0.7, 1) if resid <= 2 else (round(full * 0.4, 1) if resid <= 5 else 0))


def grade_part2(O, Mk, truth):
    r = {'notes': [], 'metrics': {}}
    m = r['metrics']
    present = all(Mk[f][1] is not None for f in FILES)
    if not present:
        r['notes'].append('maskeli/*.csv missing')
        r['scores'] = {k: 0 for k in ('K6', 'K7', 'K8', 'K9', 'K10', 'K11', 'K12')}
        r['T4_penalty'] = 0
        r['T4'] = []
        return r
    aligned = all(Mk[f][0] == O[f][0] and len(Mk[f][1]) == len(O[f][1]) for f in FILES)
    m['aligned'] = aligned
    if not aligned:
        r['notes'].append('headers or row counts differ from source -> row-aligned checks score 0')
    OM, OH, OI = O['musteri'][1], O['hesap'][1], O['islem'][1]
    MM, MH, MI = Mk['musteri'][1], Mk['hesap'][1], Mk['islem'][1]
    S = {}
    pii = truth['pii']

    def cell(f, i, c):
        try:
            return Mk[f][1][i].get(c, '')
        except (IndexError, TypeError):
            return ''

    def ocell(f, i, c):
        return O[f][1][i].get(c, '')

    # ---------------- K6 direct columns
    if aligned:
        ind = [i for i, x in enumerate(OM) if x['musteri_tipi'] == 'BIREYSEL']
        subs = {}
        mt = [MM[i]['tckn'] for i in ind]
        subs['tckn'] = all(MM[i]['tckn'] != OM[i]['tckn'] and tckn_valid(MM[i]['tckn']) for i in ind) and len(set(mt)) == len(mt)
        subs['ad_soyad'] = all(tr_fold(MM[i]['ad'] + ' ' + MM[i]['soyad']) != tr_fold(OM[i]['ad'] + ' ' + OM[i]['soyad'])
                               and MM[i]['ad'] and MM[i]['soyad'] for i in ind)
        me = [x['eposta'].lower() for x in MM]
        subs['eposta'] = all(MM[i]['eposta'].lower() != OM[i]['eposta'].lower() and
                             re.fullmatch(r'[^@\s]+@example\.test', MM[i]['eposta']) for i in range(len(OM))) and len(set(me)) == len(me)

        def skel(s):
            return re.sub(r'\d', '9', s)
        subs['telefon'] = all(skel(MM[i]['telefon']) == skel(OM[i]['telefon']) and
                              phone_nat(MM[i]['telefon']) != phone_nat(OM[i]['telefon']) and
                              (not phone_nat(OM[i]['telefon']).startswith('5') or phone_nat(MM[i]['telefon']).startswith('5'))
                              for i in range(len(OM)))
        mn = [x['musteri_no'] for x in MM]
        subs['musteri_no'] = all(MM[i]['musteri_no'] != OM[i]['musteri_no'] and re.fullmatch(r'M\d{6}', MM[i]['musteri_no'])
                                 for i in range(len(OM))) and len(set(mn)) == len(mn)
        hk = [(x['sube_kodu'], x['hesap_no']) for x in MH]
        subs['hesap_no'] = all(MH[i]['hesap_no'] != OH[i]['hesap_no'] and re.fullmatch(r'[1-9]\d{7}', MH[i]['hesap_no'])
                               for i in range(len(OH))) and len(set(hk)) == len(hk)
        subs['sahis_vkn'] = all(MM[i]['vkn'] != OM[i]['vkn'] and vkn_valid(MM[i]['vkn'])
                                for i, x in enumerate(OM) if x['sirket_turu'] == 'SAHIS')
        subs['iban_changed'] = all(iban_norm(MH[i]['iban']) != iban_norm(OH[i]['iban']) for i in range(len(OH)))
        m['K6_subchecks'] = subs
        S['K6'] = round(6.0 * sum(map(bool, subs.values())) / len(subs), 2)
    else:
        S['K6'] = 0

    # ---------------- K7 numeric residual in free text + karsi_iban
    tset, pset = set(pii['tckn']), set(pii['phone_nat'])
    itails = {x[4:] for x in pii['iban']}
    hits = []
    cells = [(f, i, c, x.get(c, '')) for f, c in TEXT_CELLS + (('islem', 'karsi_iban'),) for i, x in enumerate(Mk[f][1])]
    for f, i, c, v in cells:
        if not v:
            continue
        D = digits(v)
        if len(D) < 10:
            continue
        for t in tset:
            if t in D:
                hits.append((f, i, c, 'tckn', t))
        for p in pset:
            if p in D:
                hits.append((f, i, c, 'phone', p))
        for t in itails:
            if t in D:
                hits.append((f, i, c, 'iban', t))
    m['K7_residual'] = len(hits)
    m['K7_examples'] = hits[:8]
    S['K7'] = tier3(len(hits), 8)

    # ---------------- K8 names (per occurrence) + e-mails (global in free text)
    nres = []
    for o in truth['name_occ']:
        f, i, c = o['file'], o['row'], o['col']
        if aligned:
            if tr_fold(o['phrase']) in tr_fold(cell(f, i, c)):
                nres.append(o)
        else:
            if any(tr_fold(o['phrase']) in tr_fold(x.get(c, '')) for x in Mk[f][1]):
                nres.append(o)
    eres = []
    emails = set(pii['email'])
    for f, c in TEXT_CELLS:
        for i, x in enumerate(Mk[f][1]):
            v = email_norm(x.get(c, ''))
            if '@' in v:
                for e in emails:
                    if e in v:
                        eres.append((f, i, e))
    m['K8_name_residual'] = len(nres)
    m['K8_email_residual'] = len(eres)
    m['K8_examples'] = [o['phrase'] + '@' + o['file'] + ':' + str(o['row']) for o in nres[:8]] + [e[2] for e in eres[:4]]
    S['K8'] = tier3(len(nres) + len(eres), 10)

    # ---------------- K9 joins + determinism (determinism added in main)
    if aligned:
        okey = {(x['sube_kodu'], x['hesap_no']): j for j, x in enumerate(OH)}
        mkey = Counter((x['sube_kodu'], x['hesap_no']) for x in MH)
        tot = good = 0
        for i, x in enumerate(OI):
            j = okey.get((x['sube_kodu'], x['hesap_no']))
            if j is None:
                continue
            tot += 1
            k2 = (MI[i]['sube_kodu'], MI[i]['hesap_no'])
            good += k2 == (MH[j]['sube_kodu'], MH[j]['hesap_no']) and mkey[k2] == 1
        f1 = good / tot if tot else 0
        omno = {x['musteri_no']: k for k, x in enumerate(OM)}
        f2 = sum(MH[j]['musteri_no'] == MM[omno[x['musteri_no']]]['musteri_no'] for j, x in enumerate(OH)) / len(OH)
        oib = {iban_norm(x['iban']): j for j, x in enumerate(OH)}
        it = ig = 0
        for i, x in enumerate(OI):
            j = oib.get(iban_norm(x['karsi_iban']))
            if j is None:
                continue
            it += 1
            ig += iban_norm(MI[i]['karsi_iban']) == iban_norm(MH[j]['iban'])
        f3 = ig / it if it else 0
        m['K9_join_islem_hesap'] = round(f1, 4)
        m['K9_join_hesap_musteri'] = round(f2, 4)
        m['K9_join_internal_iban'] = round(f3, 4)
        m['K9_internal_transfer_rows'] = it
        S['K9_joins'] = 5 if min(f1, f2, f3) == 1 else round(5 * 0.8 * (f1 + f2 + f3) / 3, 2)
        changed = all(a['musteri_no'] != b['musteri_no'] for a, b in zip(OM, MM)) and \
            all(a['hesap_no'] != b['hesap_no'] for a, b in zip(OH, MH))
        uniq = len({x['musteri_no'] for x in MM}) == len(MM) and \
            len({(x['sube_kodu'], x['hesap_no']) for x in MH}) == len(MH)
        if not changed:  # keys left unmasked: joins trivially intact
            S['K9_joins'] = 0
            r['notes'].append('K9 joins not credited: musteri_no/hesap_no not pseudonymised')
        elif not uniq:  # pseudonym collisions merge different customers/accounts
            S['K9_joins'] = min(S['K9_joins'], 2.5)
            r['notes'].append('K9 joins capped: pseudonym collisions in musteri_no or (sube_kodu, hesap_no)')
    else:
        S['K9_joins'] = 0

    # ---------------- K10 IBAN validity/embedding + cross-format consistency
    if aligned:
        okh = sum(iban_norm(x['iban']) == iban_from('00990', x['sube_kodu'], x['hesap_no']) for x in MH)
        kk = [(o, mk) for o, mk in zip(OI, MI) if o['karsi_iban']]
        okk = sum(iban_valid(mk['karsi_iban']) and iban_norm(mk['karsi_iban'])[4:9] == iban_norm(o['karsi_iban'])[4:9] for o, mk in kk)
        frac = (okh + okk) / (len(MH) + len(kk))
        m['K10_iban_valid_frac'] = round(frac, 4)
        iv = 4 if frac == 1 else (2 if frac >= 0.95 else 0)
        if not m.get('K6_subchecks', {}).get('iban_changed'):
            iv = 0  # unmasked IBANs are trivially valid
        passed, failed = 0, []
        for cdef in truth['consistency']:
            ok = False
            ct = cdef['ctype']
            if ct == 'iban_same':
                vals = [iban_norm(cell(*c)) for c in cdef['cells']]
                orig = [iban_norm(ocell(*c)) for c in cdef['cells']]
                ok = len(set(vals)) == 1 and iban_valid(vals[0]) and vals[0][4:9] == cdef['bank'] and vals[0] != orig[0]
            else:
                f, i, c = cdef['cell']
                rf, ri, rc = cdef['ref_cell']
                v, ov = cell(f, i, c), ocell(f, i, c)
                mref, oref = cell(rf, ri, rc), ocell(rf, ri, rc)
                if ct == 'tckn':
                    ok = digits(mref) and digits(mref) != digits(oref) and digits(mref) in digits(v) and digits(oref) not in digits(v)
                elif ct == 'phone':
                    pm, po = phone_nat(mref), phone_nat(oref)
                    ok = pm and pm != po and pm in digits(v) and po not in digits(v)
                elif ct == 'email':
                    em, eo = mref.lower(), oref.lower()
                    ok = em and em != eo and em in email_norm(v) and eo not in email_norm(v)
                elif ct == 'mno':
                    ok = mref and mref != oref and mref in v and oref not in v
                elif ct == 'iban':
                    im, io_ = iban_norm(mref), iban_norm(oref)
                    nv = re.sub(r'[\s-]', '', v).upper()
                    ok = im and im != io_ and im in nv and io_[4:] not in nv
                elif ct == 'iban_textcol':
                    nv = re.sub(r'[\s-]', '', v).upper()
                    found = re.findall(r'TR\d{24}', nv)
                    km = iban_norm(mref)
                    ok = bool(found) and found[0] == km and km != iban_norm(oref)
            passed += bool(ok)
            if not ok:
                failed.append(cdef['id'])
        m['K10_consistency'] = '%d/%d' % (passed, len(truth['consistency']))
        m['K10_failed'] = failed
        S['K10'] = round(iv + 6.0 * passed / len(truth['consistency']), 2)
    else:
        S['K10'] = 0

    # ---------------- K11 date shift
    if aligned:
        deltas, fmt_bad, time_bad, n = Counter(), 0, 0, 0
        for (f, c), fmt in DATE_COLS.items():
            for i, x in enumerate(O[f][1]):
                if not x.get(c):
                    continue
                n += 1
                a, b = pdate(x[c], fmt), pdate(cell(f, i, c), fmt)
                if a is None or b is None:
                    fmt_bad += 1
                    continue
                if a.time() != b.time():
                    time_bad += 1
                deltas[(b.date() - a.date()).days] += 1
        mode, mc = deltas.most_common(1)[0] if deltas else (0, 0)
        const = mc / n if n else 0
        m['K11_offset_days_mode'] = mode
        m['K11_const_frac'] = round(const, 4)
        m['K11_format_bad'] = fmt_bad
        m['K11_time_bad'] = time_bad
        S['K11'] = (4 if const == 1 else (2 if const >= 0.95 else 0)) + (1 if -365 <= mode <= -30 else 0) + \
            (2 if fmt_bad == 0 else (1 if fmt_bad <= 0.05 * n else 0)) + (1 if time_bad == 0 and fmt_bad < n else 0)
        if mode == 0:  # dates not shifted at all
            S['K11'] = 0
    else:
        S['K11'] = 0

    # ---------------- K12 k-anonymity
    if aligned:
        ind = [i for i, x in enumerate(OM) if x['musteri_tipi'] == 'BIREYSEL']
        cap = int(0.05 * len(ind))
        supp, viol, groups = 0, [], Counter()
        for i in ind:
            q = (MM[i]['dogum_tarihi'], MM[i]['il'], MM[i]['ilce'], MM[i]['cinsiyet'])
            if all(v == '*' for v in q):
                supp += 1
                continue
            o = OM[i]
            y = int(o['dogum_tarihi'][-4:])
            dv = q[0]
            okd = (re.fullmatch(r'\d{4}', dv) and int(dv) == y) or \
                  (re.fullmatch(r'(\d{4})-(\d{4})', dv) and int(dv[:4]) <= y <= int(dv[5:]) and int(dv[5:]) - int(dv[:4]) <= 9) or \
                  dv == o['dogum_tarihi']
            if not (okd and q[1] == o['il'] and q[3] == o['cinsiyet'] and q[2] in (o['ilce'], '*')):
                viol.append(i)
            groups[q] += 1
        mink = min(groups.values()) if groups else 0
        oq = Counter((OM[i]['dogum_tarihi'], OM[i]['il'], OM[i]['ilce'], OM[i]['cinsiyet']) for i in ind)
        m['K12_orig_unique_combos'] = sum(1 for v in oq.values() if v == 1)
        m['K12_min_k'] = mink
        m['K12_classes_below_5'] = sum(1 for v in groups.values() if v < 5)
        m['K12_suppressed'] = '%d (cap %d)' % (supp, cap)
        m['K12_truth_violations'] = len(viol)
        if mink >= 5 and supp <= cap and not viol:
            S['K12'] = 10
        elif mink >= 3 and supp <= 2 * cap and not viol:
            S['K12'] = 4
        else:
            S['K12'] = 0
    else:
        S['K12'] = 0

    # ---------------- T4 over-masking
    pen, t4 = 0, []
    if aligned:
        groups_cols = {
            'musteri': [c for c in ('musteri_tipi', 'sirket_turu')],
            'hesap': ['sube_kodu', 'hesap_turu', 'doviz', 'kmh_limiti', 'bakiye'],
            'islem': ['islem_id', 'sube_kodu', 'islem_tipi', 'tutar']}
        for f, cols in groups_cols.items():
            bad = sum(1 for o, mk in zip(O[f][1], Mk[f][1]) for c in cols if o[c] != mk[c])
            if f == 'musteri':
                bad += sum(1 for o, mk in zip(OM, MM) if o['sirket_turu'] in ('AS', 'LTD')
                           and (o['vkn'] != mk['vkn'] or o['unvan'] != mk['unvan'] or o['il'] != mk['il']))
            if bad:
                t4.append('%s columns changed (%d cells)' % (f, bad))
        for frag in truth['preserve_fragments']:
            for f, c in TEXT_CELLS:
                for i, x in enumerate(O[f][1]):
                    if frag in x.get(c, '') and frag not in cell(f, i, c):
                        t4.append('fragment lost: %s' % frag)
                        break
                else:
                    continue
                break
        lost = sum(1 for f, c in TEXT_CELLS for i, x in enumerate(O[f][1]) for h in HVL.findall(x.get(c, '')) if h not in cell(f, i, c))
        if lost:
            t4.append('HVL references lost: %d' % lost)
        t4 = sorted(set(t4))
        pen = -min(6, len(t4))
    r['T4'] = t4
    r['T4_penalty'] = pen
    r['scores'] = S
    return r


# ------------------------------------------------------------------ determinism (executes agent code!)
def run_masker(cikti, inp, timeout=300):
    py, js = os.path.join(cikti, 'maskele.py'), os.path.join(cikti, 'maskele.js')
    if os.path.isfile(py):
        cmd0 = [sys.executable, py]
    elif os.path.isfile(js):
        cmd0 = ['node', js]
    else:
        return None, 'no maskele.py / maskele.js'
    env = dict(os.environ, MASKE_ANAHTARI=KEY)
    env.pop('PYTHONHASHSEED', None)
    outs = []
    for _ in range(2):
        d = tempfile.mkdtemp(prefix='td2_')
        try:
            p = subprocess.run(cmd0 + [inp, d], cwd=os.path.dirname(cikti), env=env, capture_output=True, timeout=timeout)
        except Exception as e:  # noqa
            return None, 'run failed: %s' % e
        if p.returncode != 0:
            return None, 'exit %d: %s' % (p.returncode, p.stderr.decode('utf-8', 'replace')[-400:])
        outs.append(d)
    return outs, None


def same_bytes(d1, d2):
    for f in FILES:
        a, b = os.path.join(d1, f + '.csv'), os.path.join(d2, f + '.csv')
        if not (os.path.isfile(a) and os.path.isfile(b)):
            return False
        with open(a, 'rb') as x, open(b, 'rb') as y:
            if x.read() != y.read():
                return False
    return True


# ------------------------------------------------------------------ report trap hints (manual T1-T3)
HINTS = {
    'T1 (same hesap_no in two branches reported as duplicate/error)':
        r'(mükerrer|tekrar|duplicate|çift kayıt|çakış).*hesap|hesap.*(mükerrer|tekrar|duplicate|çift kayıt|çakış)',
    'T2 (KMH negative balance reported as error)': r'(negatif|eksi|sıfırın altında).*(bakiye|kmh)|(bakiye|kmh).*(negatif|eksi|sıfırın altında)',
    'T3 (29 Feb customer opened on 1 March at 18 reported as underage/violation)': r'(29 ?şubat|29\.02|02-29|reşit|18 yaş)',
}


def report_hints(cikti):
    p = os.path.join(cikti, 'rapor.md')
    if not os.path.isfile(p):
        return {'missing': True}
    with open(p, encoding='utf-8', errors='replace') as f:
        lines = f.read().splitlines()
    out = {}
    for name, rx in HINTS.items():
        out[name] = [ln.strip()[:220] for ln in lines if re.search(rx, ln, re.I)][:8]
    return out


# ------------------------------------------------------------------ main
POINTS = {'K1': 6, 'K2': 6, 'K3': 10, 'K4': 10, 'K5': 8, 'K6': 6, 'K7': 8, 'K8': 10, 'K9': 8, 'K10': 10, 'K11': 8, 'K12': 10}


def main(argv):
    args = [a for a in argv if not a.startswith('--')]
    opt = lambda k, d=None: argv[argv.index(k) + 1] if k in argv and argv.index(k) + 1 < len(argv) else d
    if not args:
        print(__doc__)
        return 2
    base = os.path.abspath(args[0])
    cikti = os.path.join(base, 'cikti') if os.path.isdir(os.path.join(base, 'cikti')) else base
    trial = os.path.abspath(opt('--trial', os.path.join(HERE, '..', 'trial-testdata2')))
    truth_p = opt('--truth', os.path.join(HERE, 'testdata2_truth.json'))
    with open(truth_p, encoding='utf-8') as f:
        truth = json.load(f)
    src = os.path.join(trial, 'girdiler', 'uretim_kesiti')
    O = load_dir(src)
    p1 = grade_part1(os.path.join(cikti, 'uretilen'))
    s1 = score_part1(p1)
    p2 = grade_part2(O, load_dir(os.path.join(cikti, 'maskeli')), truth)
    S = dict(s1)
    S.update({k: v for k, v in p2['scores'].items() if not k.startswith('K9')})
    det = {'evaluated': False}
    if '--no-exec' not in argv:
        outs, err = run_masker(cikti, src)
        det['evaluated'] = True
        if err:
            det['error'] = err
            det['score'] = 0
        else:
            det['rerun_identical'] = same_bytes(outs[0], outs[1])
            det['matches_delivered'] = same_bytes(outs[0], os.path.join(cikti, 'maskeli'))
            det['score'] = 2 * det['rerun_identical'] + 1 * det['matches_delivered']
            if not p2['scores'].get('K6'):  # nothing was actually masked: determinism is trivial
                det['score'] = 0
                det['note'] = 'not credited: no direct PII column was masked'
            for d in outs:
                shutil.rmtree(d, ignore_errors=True)
    S['K9'] = round(p2['scores'].get('K9_joins', 0) + det.get('score', 0), 2)
    total = round(sum(S[k] for k in POINTS), 2)
    pen = p2['T4_penalty']
    result = {
        'scores': {k: '%s/%s' % (S[k], POINTS[k]) for k in POINTS},
        'auto_total_before_penalties': total,
        'T4_overmasking_penalty': pen, 'T4_findings': p2['T4'],
        'auto_total': max(0, round(total + pen, 2)),
        'max': 100,
        'manual': 'Apply T1-T3 report penalties (-4 each) and other unfounded source-data claims (-2 each, max -6) per testdata2.md',
        'part1': {'present': p1['present'], 'volume_ok': p1.get('volume_ok'), 'counts': p1.get('counts'),
                  'rule_satisfaction_pct': p1.get('rule_satisfaction'), 'boundaries': p1.get('sd'),
                  'feb29': p1.get('feb29'),
                  'violations': {k: (len(v), v[:5]) for k, v in p1['viol'].items() if v}, 'notes': p1['notes']},
        'part2': p2['metrics'], 'part2_notes': p2['notes'], 'determinism': det,
        'report_trap_hints': report_hints(cikti),
    }
    resid = p2['metrics'].get('K7_residual', 0) + p2['metrics'].get('K8_name_residual', 0) + p2['metrics'].get('K8_email_residual', 0)
    result['residual_pii_any_format'] = resid
    js = json.dumps(result, ensure_ascii=False, indent=1, default=str)
    if opt('--json'):
        with open(opt('--json'), 'w', encoding='utf-8') as f:
            f.write(js)
    print(js)
    return 0


if __name__ == '__main__':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:  # noqa
        pass
    sys.exit(main(sys.argv[1:]))
