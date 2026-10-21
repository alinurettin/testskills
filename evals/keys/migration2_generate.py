#!/usr/bin/env python3
"""EVALUATOR-ONLY generator for evals/trial-migration2 (never give this file to the agent).

Deterministically builds:
  trial-migration2/inputs/kaynak/POLMAS.csv, TAKSIT.csv   (legacy SIGMA/400 exports, cp1254, ';')
  trial-migration2/inputs/hedef/policies.csv, installments.csv (PolicyNova exports produced by a
      simulated, deliberately buggy ETL that reads the legacy files exactly as written)
  trial-migration2/inputs/etl_calistirma_raporu.txt        (the migration team's run report)
  keys/migration2_expected.json                            (planted item / trap key sets)

Python 3 standard library only.  Usage:  python migration2_generate.py
"""
import calendar
import csv
import io
import json
import os
import random
from datetime import date, datetime, timedelta
from decimal import Decimal, ROUND_DOWN, ROUND_HALF_UP

HERE = os.path.dirname(os.path.abspath(__file__))
TRIAL = os.path.normpath(os.path.join(HERE, '..', 'trial-migration2'))
INP = os.path.join(TRIAL, 'inputs')

rnd = random.Random(20260929)
CUTOFF = date(2026, 9, 30)
TZ_OFFSET = timedelta(hours=3)          # Europe/Istanbul, permanent UTC+03:00
D2 = Decimal('0.01')

# ---------------------------------------------------------------- reference data
AGENCY_MAP = {  # legacy -> (new code, name, city)
    'A01': ('ACN-3401', 'Boğaziçi Anadolu Sigorta Aracılık Ltd. Şti.', 'İstanbul'),
    'A02': ('ACN-3402', 'Haliç Güvence Acentelik A.Ş.', 'İstanbul'),
    'A03': ('ACN-0601', 'Başkent Kalkan Sigorta Aracılık Ltd. Şti.', 'Ankara'),
    'A04': ('ACN-3501', 'Ege Körfez Sigorta Acentesi Ltd. Şti.', 'İzmir'),
    'A05': ('ACN-1601', 'Uludağ Teminat Aracılık A.Ş.', 'Bursa'),
    'A06': ('ACN-0701', 'Akdeniz Liman Sigorta Ltd. Şti.', 'Antalya'),
    'A07': ('ACN-4201', 'Selçuklu Güven Sigorta Aracılık Ltd. Şti.', 'Konya'),
    'A08': ('ACN-2701', 'Zeugma Risk Danışmanlık A.Ş.', 'Gaziantep'),
    'A09': ('ACN-3502', 'Kordon Sigorta Acentesi Ltd. Şti.', 'İzmir'),
    'A10': ('ACN-6101', 'Karadeniz Dalga Sigorta Aracılık A.Ş.', 'Trabzon'),
}
OTHER_CITIES = ['Muğla', 'Eskişehir', 'Çanakkale', 'Iğdır', 'Şanlıurfa', 'Kırşehir',
                'Diyarbakır', 'Kocaeli', 'Ağrı', 'Tekirdağ']
PARTIES = [('1', ['A01', 'A02', 'A03']), ('2', ['A04', 'A05', 'A07']),
           ('3', ['A06', 'A08']), ('4', ['A09', 'A10'])]

FIRST_F = ['Ayşe', 'Fatma', 'Emine', 'Gülşen', 'Özge', 'Ilgın', 'Işıl', 'Ebru', 'Zeynep', 'Selin',
           'Kübra', 'Tuğba', 'Sevgi', 'Cemre', 'Nazlı', 'Şeyma', 'Çiğdem', 'Irmak', 'Özlem']
FIRST_M = ['Mehmet', 'Mustafa', 'Hüseyin', 'İbrahim', 'Şükrü', 'Çağrı', 'Ömer', 'Doğan', 'Yusuf',
           'Burak', 'Oğuz', 'Gökhan', 'Ümit', 'Barış', 'İlker', 'Gürkan']
LAST = ['Yılmaz', 'Kaya', 'Demir', 'Şahin', 'Çelik', 'Yıldız', 'Öztürk', 'Aydın', 'Özdemir',
        'Arslan', 'Doğan', 'Kılıç', 'Aslan', 'Çetin', 'Kara', 'Koç', 'Kurt', 'Özkan', 'Şimşek',
        'Polat', 'Güneş', 'Akın', 'Tekin', 'Ünal', 'Uçar', 'Işık', 'Sarı', 'Ilıcak', 'Göçmen',
        'Çakır', 'Erginöz', 'Soğukpınar']
COMPANIES = ['Bozkır Un Sanayi Ltd. Şti.', 'Kıyı Lojistik Taşımacılık A.Ş.',
             'Göktaş Mermer Tic. Ltd. Şti.', 'Ilıca Tekstil San. ve Tic. A.Ş.',
             'Çınaraltı Gıda Ltd. Şti.', 'Öztepe Otomotiv Yedek Parça A.Ş.',
             'Sarıçam Ambalaj San. Ltd. Şti.', 'Doruk Soğuk Hava Depoculuk A.Ş.',
             'Yeşilvadi Fidancılık Ltd. Şti.']
MAH = ['Atatürk', 'Cumhuriyet', 'Yeşilyurt', 'Kültür', 'Bahçelievler', 'Fatih', 'Gazi', 'İnönü',
       'Çamlık', 'Şirinevler', 'Güzelyalı', 'Esentepe', 'Barış', 'Ilıca', 'Özgürlük']
SOK = ['Gül Sok.', 'Lale Sok.', 'Çınar Cad.', 'Menekşe Sok.', 'Papatya Sok.', 'Şehit Ali Rıza Sok.',
       'Ihlamur Cad.', 'Söğüt Sok.', 'Değirmen Sok.', 'Okul Cad.']
LONG_ADDR = {
    9: 'Yenişehir Mahallesi Gazi Mustafa Kemal Bulvarı Kardelen Apartmanı No:118 Daire:14',
    19: 'Bahçelievler Mahallesi Şehit Pilot Ertuğrul Gökçe Sokak No:27 Kat:3 Daire:9',
    24: 'Kazımdirik Mahallesi 372/8 Sokak Ege Park Konutları B Blok No:4 Daire:22',
    35: 'Güzeloba Mahallesi Ilıca Caddesi Turunç Sitesi C Blok No:56 Daire:7',
    41: 'Hocacihan Mahallesi Saraçoğlu Caddesi Büyükşehir Konutları No:203/A Daire:11',
    53: 'Mavişehir Mahallesi Deniz Feneri Bulvarı Albatros Sitesi No:88 Kat:6 Daire:24',
    57: 'Kaşüstü Mahallesi Sahil Yolu Üzeri Karadeniz Evleri 2. Etap No:15 Daire:3',
}
SEMICOLON_ADDR = {8: 'Fevzi Çakmak Mah. 1203 Sok. No:7; Kat:2 D:5'}
LOSS_PAYEES = {
    1: 'Yıldızbank T.A.Ş.',
    15: 'Ilgaz Katılım Bankası A.Ş.',
    21: 'Doğu Şirket Finansman A.Ş.',
    38: 'Güneşli Kalkınma Bankası A.Ş.',
    49: 'Çağlayan Finansal Kiralama A.Ş.',
    55: 'Özbirlik Bankası A.Ş.',
    60: 'Kuzeydoğu Tüketici Finansmanı A.Ş.',
}
PREMIUM_RANGE = {  # (product, currency group) -> (lo, hi)
    ('KSK', 'TRY'): (9000, 42000), ('TRF', 'TRY'): (3200, 11500), ('KNT', 'TRY'): (950, 4800),
    ('ISY', 'TRY'): (18000, 95000), ('ISY', 'USD'): (2400, 8900), ('ISY', 'EUR'): (3100, 6900),
    ('FKZ', 'TRY'): (450, 2400), ('SYH', 'EUR'): (45, 260), ('SYH', 'USD'): (60, 300),
}

# idx: (agency, product, DOVIZ, DURUM, n_regular, start, extras)
#   extras: kur, days (travel), iptal, pay {inst_no: local datetime}, t1p (late-night last update)
PLAN = {
    1: ('A01', 'KSK', 'TL', 'A', 6, '2026-02-11', {}),
    2: ('A01', 'TRF', '', 'S', 1, '2024-10-03', {}),
    3: ('A01', 'KNT', 'TL', 'A', 12, '2025-10-20', {}),
    4: ('A01', 'ISY', 'USD', 'A', 4, '2026-05-02', {'kur': '34.1287'}),
    5: ('A01', 'FKZ', 'TL', 'S', 1, '2025-03-01', {}),
    6: ('A01', 'KSK', 'TL', 'A', 9, '2025-12-08', {'t1p': True}),
    7: ('A01', 'SYH', 'EUR', 'S', 1, '2026-07-04', {'kur': '37.8412', 'days': 21}),
    8: ('A02', 'KSK', 'TL', 'A', 4, '2026-04-09', {}),
    9: ('A02', 'KNT', 'TL', 'A', 4, '2026-01-12', {}),
    10: ('A02', 'TRF', 'TL', 'I', 2, '2025-09-05', {'iptal': '2026-02-17'}),
    11: ('A02', 'KSK', '', 'Y', 6, '2024-11-07', {}),
    12: ('A02', 'ISY', 'EUR', 'A', 6, '2025-11-01', {'kur': '38.1200'}),
    13: ('A02', 'KSK', 'TL', 'A', 3, '2026-03-30', {'pay': {2: datetime(2026, 5, 1, 1, 22)}}),
    14: ('A02', 'FKZ', 'TL', 'A', 1, '2026-06-15', {}),
    15: ('A03', 'KSK', 'TL', 'A', 9, '2025-11-24', {}),
    16: ('A03', 'TRF', 'TL', 'S', 2, '2025-02-10', {}),
    17: ('A03', 'KNT', 'TL', 'A', 6, '2026-01-05', {'pay': {3: datetime(2026, 3, 5, 0, 31)}}),
    18: ('A03', 'SYH', 'USD', 'A', 1, '2026-09-12', {'kur': '34.5521', 'days': 40}),
    19: ('A03', 'KSK', '', 'S', 3, '2024-12-02', {}),
    20: ('A03', 'FKZ', 'TL', 'A', 1, '2026-08-03', {'t1p': True}),
    21: ('A04', 'KSK', 'TL', 'A', 6, '2026-04-21', {}),
    22: ('A04', 'ISY', 'TL', 'A', 4, '2025-10-07', {}),
    23: ('A04', 'KNT', 'TL', 'S', 1, '2025-06-11', {}),
    24: ('A04', 'TRF', 'TL', 'A', 2, '2026-07-01', {}),
    25: ('A04', 'KSK', 'TL', 'A', 6, '2026-02-27', {'pay': {4: datetime(2026, 5, 27, 1, 58)}}),
    26: ('A04', 'SYH', 'EUR', 'S', 1, '2026-08-06', {'kur': '36.9055', 'days': 14}),
    27: ('A05', 'KSK', 'TL', 'A', 11, '2025-12-05', {}),
    28: ('A05', 'TRF', 'TL', 'A', 1, '2026-09-08', {}),
    29: ('A05', 'KNT', '', 'Y', 1, '2024-10-28', {}),
    30: ('A05', 'ISY', 'USD', 'S', 2, '2025-04-04', {'kur': '33.9500'}),
    31: ('A05', 'KSK', 'TL', 'I', 3, '2025-08-12', {'iptal': '2026-01-15'}),
    32: ('A05', 'FKZ', 'TL', 'A', 1, '2026-05-19', {'t1p': True}),
    33: ('A06', 'KSK', 'TL', 'A', 3, '2026-06-03', {}),
    34: ('A06', 'TRF', 'TL', 'A', 2, '2026-02-02', {}),
    35: ('A06', 'KNT', 'TL', 'A', 4, '2025-12-10', {}),
    36: ('A06', 'KSK', 'TL', 'S', 6, '2025-01-09', {}),
    37: ('A06', 'FKZ', 'TL', 'A', 1, '2026-04-04', {}),
    38: ('A06', 'KSK', 'TL', 'A', 6, '2025-10-29', {}),
    39: ('A07', 'KSK', 'TL', 'A', 9, '2025-11-11', {'pay': {5: datetime(2026, 3, 12, 0, 47)}}),
    40: ('A07', 'TRF', 'TL', 'S', 1, '2025-05-06', {}),
    41: ('A07', 'KNT', 'TL', 'A', 6, '2026-03-03', {}),
    42: ('A07', 'ISY', 'TL', 'I', 1, '2025-07-01', {'iptal': '2026-03-02'}),
    43: ('A07', 'KSK', 'TL', 'A', 6, '2026-01-21', {'t1p': True}),
    44: ('A07', 'FKZ', '', 'S', 1, '2024-12-20', {}),
    45: ('A08', 'KSK', 'TL', 'A', 6, '2026-03-17', {}),
    46: ('A08', 'TRF', 'TL', 'A', 4, '2025-10-13', {}),
    47: ('A08', 'KNT', 'TL', 'S', 1, '2025-08-08', {}),
    48: ('A08', 'ISY', 'EUR', 'A', 4, '2026-06-25', {'kur': '37.6638'}),
    49: ('A08', 'KSK', 'TL', 'A', 3, '2026-07-14', {}),
    50: ('A08', 'FKZ', 'TL', 'Y', 1, '2025-02-03', {}),
    51: ('A09', 'KSK', 'TL', 'A', 9, '2026-01-02', {'pay': {7: datetime(2026, 7, 3, 2, 15)}}),
    52: ('A09', 'TRF', 'TL', 'A', 2, '2026-05-27', {'pay': {2: datetime(2026, 6, 27, 2, 44)}}),
    53: ('A09', 'KNT', 'TL', 'S', 4, '2025-03-12', {}),
    54: ('A09', 'ISY', 'USD', 'A', 2, '2026-08-18', {'kur': '34.0389'}),
    55: ('A09', 'KSK', 'TL', 'A', 6, '2025-12-30', {'t1p': True}),
    56: ('A10', 'KSK', 'TL', 'A', 6, '2026-04-28', {}),
    57: ('A10', 'TRF', 'TL', 'S', 2, '2025-06-02', {}),
    58: ('A10', 'KNT', 'TL', 'A', 4, '2026-02-16', {}),
    59: ('A10', 'FKZ', 'TL', 'A', 1, '2026-09-01', {}),
    60: ('A10', 'KSK', 'TL', 'Y', 9, '2025-01-22', {}),
    # quotes (DURUM_KD = B) - out of migration scope
    61: ('A02', 'KSK', 'TL', 'B', 6, '2026-10-06', {}),
    62: ('A05', 'ISY', 'USD', 'B', 2, '2026-10-15', {'kur': '34.2210'}),
    63: ('A08', 'KNT', 'TL', 'B', 4, '2026-10-21', {}),
    64: ('A10', 'TRF', 'TL', 'B', 1, '2026-10-01', {}),
}
K10_IDX = {13, 39, 51}         # paid 00:00-02:59 local on due date + 1  -> must be PAID_LATE
T1I_IDX = {17, 25, 52}         # paid 00:00-02:59 local on due date      -> PAID_ON_TIME, UTC date = due-1
NO_STOP_IDX = {3, 27, 10, 31, 42, 13, 39, 51, 17, 25, 52}  # never "stopped paying"


# ---------------------------------------------------------------- helpers
def d(s):
    return date.fromisoformat(s)


def add_months(x, m):
    y = x.year + (x.month - 1 + m) // 12
    mo = (x.month - 1 + m) % 12 + 1
    return date(y, mo, min(x.day, calendar.monthrange(y, mo)[1]))


def money(lo, hi):
    return Decimal(rnd.randint(lo * 100, hi * 100)) / 100


def tr_amount(v):
    s = f"{abs(v):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    return s + ('-' if v < 0 else '')


def tr_rate(v):
    return f"{v:.4f}".replace('.', ',')


def rand_time(day, h0=9, h1=21):
    return datetime(day.year, day.month, day.day, rnd.randint(h0, h1), rnd.randint(0, 59))


def translit(s):
    return s.translate(str.maketrans('ıİşŞğĞüÜöÖçÇ', 'iIsSgGuUoOcC'))


# ---------------------------------------------------------------- build legacy (semantic)
def build_policies():
    used_cust = set()
    used_names = set()
    company_i = 0
    pols = []
    for idx in sorted(PLAN):
        ag, prod, dov, durum, n, start, ex = PLAN[idx]
        bas = d(start)
        bit = bas + timedelta(days=ex['days']) if 'days' in ex else add_months(bas, 12)
        cur = {'TL': 'TRY', '': 'TRY'}.get(dov, dov)
        lo, hi = PREMIUM_RANGE[(prod, cur)]
        original = money(lo, hi)
        # customer
        while True:
            cno = rnd.randint(210000, 389999)
            if cno not in used_cust:
                used_cust.add(cno)
                break
        if prod == 'ISY':
            name = COMPANIES[company_i]
            company_i += 1
        else:
            while True:
                pool = FIRST_F if rnd.random() < 0.5 else FIRST_M
                fn = rnd.choice(pool)
                if rnd.random() < 0.2:
                    fn = fn + ' ' + rnd.choice([x for x in pool if x != fn])
                name = f"{fn} {rnd.choice(LAST)}"
                if name not in used_names:
                    used_names.add(name)
                    break
        assert len(name) <= 40
        city = AGENCY_MAP[ag][2] if rnd.random() < 0.7 else rnd.choice(OTHER_CITIES)
        if idx in LONG_ADDR:
            adres = LONG_ADDR[idx]
        elif idx in SEMICOLON_ADDR:
            adres = SEMICOLON_ADDR[idx]
        else:
            adres = f"{rnd.choice(MAH)} Mah. {rnd.choice(SOK)} No:{rnd.randint(1, 160)} D:{rnd.randint(1, 18)}"
            assert len(adres) <= 50, adres
        # regular installments
        base = (original / n).quantize(D2, ROUND_DOWN)
        amounts = [original - base * (n - 1)] + [base] * (n - 1)
        insts = []
        for i in range(1, n + 1):
            insts.append({'no': i, 'tip': 'N', 'vade': add_months(bas, i - 1),
                          'tutar': amounts[i - 1], 'odenen': None, 'odeme': None})
        # payments
        stop_from = None
        if durum in ('A', 'S', 'Y') and n >= 3 and idx not in NO_STOP_IDX and rnd.random() < 0.18:
            past = [x['no'] for x in insts if x['vade'] < CUTOFF and x['no'] >= 2]
            if past:
                stop_from = rnd.choice(past)
        for x in insts:
            if durum == 'B':
                continue
            special = ex.get('pay', {}).get(x['no'])
            if special:
                x['odeme'] = special
            elif x['vade'] >= CUTOFF:
                continue  # future installment, unpaid (OPEN)
            elif x['no'] == 1:
                x['odeme'] = rand_time(bas)
            elif stop_from and x['no'] >= stop_from:
                continue  # OVERDUE
            else:
                if rnd.random() < 0.15 and x['vade'] + timedelta(days=12) < CUTOFF:
                    payday = x['vade'] + timedelta(days=rnd.randint(2, 12))
                else:
                    payday = x['vade'] - timedelta(days=rnd.randint(0, 5))
                x['odeme'] = rand_time(payday)
            x['odenen'] = x['tutar']
        brut = original
        iptal = None
        if durum == 'I':
            iptal = d(ex['iptal'])
            refund = (original * Decimal((bit - iptal).days) / Decimal((bit - bas).days)).quantize(D2, ROUND_HALF_UP)
            rdue = iptal + timedelta(days=7)
            insts.append({'no': n + 1, 'tip': 'Z', 'vade': rdue, 'tutar': -refund,
                          'odenen': -refund, 'odeme': rand_time(rdue, 10, 16)})
            brut = original - refund
        # last update timestamp (local)
        events = [datetime.combine(bas, datetime.min.time()).replace(hour=9)]
        events += [x['odeme'] for x in insts if x['odeme']]
        if iptal:
            events.append(datetime.combine(iptal, datetime.min.time()).replace(hour=9))
        last = max(events)
        if ex.get('t1p'):
            nd = last.date() + timedelta(days=1)
            son = datetime(nd.year, nd.month, nd.day, rnd.randint(0, 2), rnd.randint(0, 59), rnd.randint(0, 59))
        else:
            lo_t = max(last + timedelta(minutes=1), datetime(last.year, last.month, last.day, 9, 0))
            hi_t = datetime(last.year, last.month, last.day, 21, 59)
            if lo_t > hi_t:
                lo_t = hi_t = last + timedelta(minutes=1)
            span = int((hi_t - lo_t).total_seconds())
            son = lo_t + timedelta(seconds=rnd.randint(0, max(span, 0)))
        if durum == 'B':
            son = rand_time(date(2026, 9, rnd.randint(18, 28)))
        assert son.date() < CUTOFF, (idx, son)
        kur = Decimal(ex['kur']) if 'kur' in ex else (Decimal('1.0000') if dov == 'TL' else None)
        pols.append({
            'idx': idx, 'agency': ag, 'urun': prod, 'doviz': dov, 'durum': durum, 'n': n,
            'bas': bas, 'bit': bit, 'brut': brut, 'kur': kur, 'cust': cno, 'name': name,
            'city': city, 'adres': adres, 'dain': LOSS_PAYEES.get(idx, ''), 'iptal': iptal,
            'son': son, 'insts': insts,
        })
    # POL_NO in issue (start date) order
    pols.sort(key=lambda p: (p['bas'], p['idx']))
    seq = 100101
    for p in pols:
        p['pol_no'] = f"4125{seq:06d}"
        seq += rnd.randint(1, 29)
    pols.sort(key=lambda p: p['pol_no'])
    return pols


# ---------------------------------------------------------------- write legacy CSVs
POL_COLS = ['POL_NO', 'MUST_NO', 'SIGORTALI_ADI', 'URUN_KD', 'DURUM_KD', 'BAS_TAR', 'BIT_TAR', 'DOVIZ',
            'BRUT_PRIM', 'KUR', 'TAKSIT_SAY', 'ACENTE_KD', 'IL', 'ADRES', 'DAIN_MURTEHIN', 'IPTAL_TAR',
            'SON_ISLEM_ZMN']
TAK_COLS = ['POL_NO', 'TAKSIT_NO', 'TAKSIT_TIP', 'VADE_TAR', 'TUTAR', 'ODENEN_TUTAR', 'ODEME_ZMN']


def write_legacy(pols):
    with open(os.path.join(INP, 'kaynak', 'POLMAS.csv'), 'w', encoding='cp1254', newline='') as f:
        w = csv.writer(f, delimiter=';', lineterminator='\r\n')
        w.writerow(POL_COLS)
        for p in pols:
            w.writerow([p['pol_no'], p['cust'], p['name'].ljust(40), p['urun'], p['durum'],
                        p['bas'].strftime('%d.%m.%Y'), p['bit'].strftime('%d/%m/%Y'), p['doviz'],
                        tr_amount(p['brut']), tr_rate(p['kur']) if p['kur'] is not None else '',
                        p['n'], p['agency'], p['city'], p['adres'], p['dain'],
                        p['iptal'].strftime('%d.%m.%Y') if p['iptal'] else '',
                        p['son'].strftime('%d.%m.%Y %H:%M:%S')])
    with open(os.path.join(INP, 'kaynak', 'TAKSIT.csv'), 'w', encoding='cp1254', newline='') as f:
        w = csv.writer(f, delimiter=';', lineterminator='\r\n')
        w.writerow(TAK_COLS)
        for p in pols:
            for x in p['insts']:
                w.writerow([p['pol_no'], x['no'], x['tip'], x['vade'].strftime('%d.%m.%Y'),
                            tr_amount(x['tutar']),
                            tr_amount(x['odenen']) if x['odenen'] is not None else '',
                            x['odeme'].strftime('%d/%m/%Y %H:%M') if x['odeme'] else ''])


# ---------------------------------------------------------------- simulated (buggy) ETL
STATUS_ETL = {'A': 'ACTIVE', 'I': 'CANCELLED', 'S': 'SUSPENDED', 'Y': 'RENEWED'}   # BUG K1 (S)
PRODUCT = {'KSK': 'MOTOR_OWN_DAMAGE', 'TRF': 'MOTOR_TPL', 'KNT': 'HOME', 'ISY': 'COMMERCIAL_PROPERTY',
           'FKZ': 'PERSONAL_ACCIDENT', 'SYH': 'TRAVEL_HEALTH'}
CURRENCY = {'TL': 'TRY', '': 'TRY', 'USD': 'USD', 'EUR': 'EUR'}
AGENCY_ETL = {k: v[0] for k, v in AGENCY_MAP.items()}
AGENCY_ETL['A04'], AGENCY_ETL['A09'] = AGENCY_MAP['A09'][0], AGENCY_MAP['A04'][0]   # BUG K9


def etl_amount(s):
    # BUG K8: trailing minus silently stripped
    return Decimal(s.replace('.', '').replace(',', '.').rstrip('-'))


def etl_ts(s, fmt):
    return (datetime.strptime(s, fmt) - TZ_OFFSET)


def run_etl():
    with open(os.path.join(INP, 'kaynak', 'POLMAS.csv'), encoding='cp1254', newline='') as f:
        raw_lines = f.read().split('\r\n')
    with open(os.path.join(INP, 'kaynak', 'POLMAS.csv'), encoding='cp1254', newline='') as f:
        staging = {r['POL_NO']: r for r in csv.DictReader(f, delimiter=';')}   # lookup copy
    with open(os.path.join(INP, 'kaynak', 'TAKSIT.csv'), encoding='cp1254', newline='') as f:
        tak = list(csv.DictReader(f, delimiter=';'))

    # naive line parser (BUG K5: quoted ';' -> wrong field count -> silently skipped)
    parsed, rejected = {}, []
    for line in raw_lines[1:]:
        if not line:
            continue
        parts = line.split(';')
        key = parts[0]
        if len(parts) != len(POL_COLS):
            rejected.append(key)
            continue
        parsed[key] = dict(zip(POL_COLS, parts))

    def party_of(ag):
        for pid, ags in PARTIES:
            if ag in ags:
                return pid

    in_scope = [k for k, r in staging.items() if r['DURUM_KD'] != 'B']

    def transform_policy(r, run):
        gross = etl_amount(r['BRUT_PRIM'])
        rate = Decimal(r['KUR'].replace(',', '.')) if r['KUR'] else Decimal('1')
        rate = rate.quantize(D2, ROUND_HALF_UP)                                      # BUG K11
        upd = etl_ts(r['SON_ISLEM_ZMN'], '%d.%m.%Y %H:%M:%S')
        return {
            'policy_id': 'KYS-' + r['POL_NO'], 'legacy_policy_no': r['POL_NO'],
            'customer_no': r['MUST_NO'], 'insured_name': r['SIGORTALI_ADI'].strip(),
            'product_code': PRODUCT[r['URUN_KD']], 'status': STATUS_ETL[r['DURUM_KD']],
            'start_date': datetime.strptime(r['BAS_TAR'], '%d.%m.%Y').date().isoformat(),
            'end_date': (datetime.strptime(r['BIT_TAR'], '%d/%m/%Y').date() - timedelta(days=1)).isoformat(),
            'currency': CURRENCY[r['DOVIZ']], 'gross_premium': f"{gross:.2f}",
            'fx_rate': f"{rate:.4f}", 'premium_try': f"{(gross * rate).quantize(D2, ROUND_HALF_UP):.2f}",
            'installment_count': r['TAKSIT_SAY'], 'agency_code': AGENCY_ETL[r['ACENTE_KD']],
            'city': r['IL'].strip(), 'address_line': r['ADRES'].strip()[:50],               # BUG K2
            'loss_payee': translit(r['DAIN_MURTEHIN'].strip()),                             # BUG K4
            'cancel_date': (datetime.strptime(r['IPTAL_TAR'], '%d.%m.%Y').date().isoformat()
                            if r['IPTAL_TAR'] else '1900-01-01'),                           # BUG K3
            'updated_at': upd.strftime('%Y-%m-%dT%H:%M:%SZ'), 'migration_run_id': run,
        }

    inst_seq = [100001]

    def transform_inst(t, run):
        no = int(t['TAKSIT_NO'])
        tip = 'REGULAR' if t['TAKSIT_TIP'] == 'N' else 'REFUND'
        due = datetime.strptime(t['VADE_TAR'], '%d.%m.%Y').date()
        amount = etl_amount(t['TUTAR'])
        paid_amount = etl_amount(t['ODENEN_TUTAR']) if t['ODENEN_TUTAR'] else None
        paid_at = etl_ts(t['ODEME_ZMN'], '%d/%m/%Y %H:%M') if t['ODEME_ZMN'] else None
        if tip == 'REFUND':
            st = 'REFUNDED' if paid_at else 'REFUND_PENDING'
        elif paid_at:
            st = 'PAID_ON_TIME' if paid_at.date() <= due else 'PAID_LATE'                  # BUG K10
        else:
            st = 'OVERDUE' if due < CUTOFF else 'OPEN'
        row = {
            'installment_id': f"INS-{inst_seq[0]}", 'policy_id': 'KYS-' + t['POL_NO'],
            'installment_no': str(no), 'installment_type': tip, 'due_date': due.isoformat(),
            'amount': f"{amount:.2f}", 'currency': CURRENCY[staging[t['POL_NO']]['DOVIZ']],
            'paid_amount': f"{paid_amount:.2f}" if paid_amount is not None else '',
            'paid_at': paid_at.strftime('%Y-%m-%dT%H:%M:%SZ') if paid_at else '',
            'payment_status': st, 'migration_run_id': run,
        }
        inst_seq[0] += 1
        return row

    new_pols, new_insts, report = [], [], []
    pos = {}
    dup_keys = []
    lost_keys = []
    for run in ('R1', 'R2'):
        for pid, ags in PARTIES:
            if run == 'R2' and pid != '3':
                continue
            pkeys = sorted(k for k in in_scope if staging[k]['ACENTE_KD'] in ags)
            tkeys = [t for t in tak if t['POL_NO'] in pkeys]
            for k in pkeys:
                if k not in parsed:
                    continue  # swallowed reject
                row = transform_policy(parsed[k], run)
                if k in pos:
                    new_pols[pos[k]] = row  # MERGE
                else:
                    pos[k] = len(new_pols)
                    new_pols.append(row)
            written = 0
            for t in tkeys:
                if run == 'R1' and pid == '3' and written == 5:
                    break  # timeout in R1, party 3
                if int(t['TAKSIT_NO']) >= 10:                                               # BUG K6
                    if run == 'R1':
                        lost_keys.append(f"{t['POL_NO']}/{t['TAKSIT_NO']}")
                    continue
                new_insts.append(transform_inst(t, run))
                written += 1
                if run == 'R1' and pid == '3':
                    dup_keys.append(f"{t['POL_NO']}/{t['TAKSIT_NO']}")                      # BUG K7
            report.append((run, pid, ags, len(pkeys), len(tkeys)))
    return staging, tak, new_pols, new_insts, report, rejected, dup_keys, lost_keys


NEW_POL_COLS = ['policy_id', 'legacy_policy_no', 'customer_no', 'insured_name', 'product_code', 'status',
                'start_date', 'end_date', 'currency', 'gross_premium', 'fx_rate', 'premium_try',
                'installment_count', 'agency_code', 'city', 'address_line', 'loss_payee', 'cancel_date',
                'updated_at', 'migration_run_id']
NEW_INST_COLS = ['installment_id', 'policy_id', 'installment_no', 'installment_type', 'due_date', 'amount',
                 'currency', 'paid_amount', 'paid_at', 'payment_status', 'migration_run_id']


def write_new(new_pols, new_insts):
    for name, cols, rows in (('policies.csv', NEW_POL_COLS, new_pols),
                             ('installments.csv', NEW_INST_COLS, new_insts)):
        with open(os.path.join(INP, 'hedef', name), 'w', encoding='utf-8', newline='') as f:
            w = csv.DictWriter(f, fieldnames=cols, lineterminator='\n')
            w.writeheader()
            w.writerows(rows)


def write_report(pols, staging, tak, report):
    in_scope = [p for p in pols if p['durum'] != 'B']
    n_tak = sum(len(p['insts']) for p in in_scope)
    tot = {}
    for p in in_scope:
        c = CURRENCY[p['doviz']]
        tot[c] = tot.get(c, Decimal('0')) + p['brut']
    by_party = {}
    for run, pid, ags, np_, nt in report:
        by_party[(run, pid)] = (ags, np_, nt)
    L = []
    L.append('PoliçeNova Göç Aracı (migtool v2.4.1) - Çalıştırma Raporu')
    L.append('Ortam            : PROVA-2 (genel prova / dress rehearsal)')
    L.append('Kaynak           : SIGMA/400 dışa aktarımı 28.09.2026 18:00 (POLMAS.csv, TAKSIT.csv)')
    L.append('Hedef            : PNOVA_MIG şeması (policies, installments)')
    L.append('Kesim tarihi     : 30.09.2026')
    L.append('Filtre           : DURUM_KD <> \'B\' (teklifler ve teklif taksitleri hariç)')
    L.append('Yükleme sırası   : parti bazında; parti içinde POL_NO, TAKSIT_NO artan')
    L.append('')
    L.append('=== Çalıştırma R1 ===')
    L.append('Başlangıç : 28.09.2026 22:04:51 (TRT)')
    L.append('Mod       : poliçe MERGE (anahtar: policy_id), taksit INSERT (installment_id = sıra no)')
    for pid, ags in PARTIES:
        a, np_, nt = by_party[('R1', pid)]
        if pid == '3':
            L.append(f"Parti {pid} ({', '.join(a)}): poliçe okunan {np_} / yazılan {np_} / reddedilen 0 ; "
                     f"taksit okunan {nt} / yazılan 5 / reddedilen 0")
            L.append('          HATA: hedef veritabanı bağlantısı zaman aşımı (300 sn). Parti 3 yarıda kesildi.')
        else:
            L.append(f"Parti {pid} ({', '.join(a)}): poliçe okunan {np_} / yazılan {np_} / reddedilen 0 ; "
                     f"taksit okunan {nt} / yazılan {nt} / reddedilen 0")
    L.append('Bitiş     : 28.09.2026 23:41:07 (TRT) - DURUM: KISMEN BAŞARILI (1 parti hatalı)')
    L.append('')
    L.append('=== Çalıştırma R2 (yeniden çalıştırma) ===')
    L.append('Başlangıç : 29.09.2026 01:12:30 (TRT)')
    L.append('Kapsam    : yalnızca Parti 3')
    L.append('Mod       : poliçe MERGE (anahtar: policy_id), taksit INSERT (installment_id = sıra no)')
    a, np_, nt = by_party[('R2', '3')]
    L.append(f"Parti 3 ({', '.join(a)}): poliçe okunan {np_} / yazılan {np_} / reddedilen 0 ; "
             f"taksit okunan {nt} / yazılan {nt} / reddedilen 0")
    L.append('Bitiş     : 29.09.2026 01:19:44 (TRT) - DURUM: BAŞARILI')
    L.append('')
    L.append('=== Mutabakat özeti (migtool otomatik; yükleme sayaçları ve hazırlık tablosu toplamları) ===')
    L.append(f"Poliçe sayısı   : kaynak (teklif hariç) {len(in_scope)} | hedef {len(in_scope)} | fark 0   OK")
    L.append(f"Taksit sayısı   : kaynak (teklif hariç) {n_tak} | hedef {n_tak} | fark 0   OK")
    for c in ('TRY', 'USD', 'EUR'):
        L.append(f"Brüt prim {c}   : kaynak {tr_amount(tot[c])} | hedef {tr_amount(tot[c])} | fark 0,00   OK")
    L.append('Uyarı sayısı    : 0')
    L.append('')
    L.append('SONUÇ: Mutabakat başarılı. Canlı geçiş için teknik engel bulunmamaktadır.')
    L.append('Hazırlayan: Göç Ekibi (migtool otomatik rapor)')
    with open(os.path.join(INP, 'etl_calistirma_raporu.txt'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(L) + '\n')
    return len(in_scope), n_tak


def main():
    pols = build_policies()
    write_legacy(pols)
    staging, tak, new_pols, new_insts, report, rejected, dup_keys, lost_keys = run_etl()
    write_new(new_pols, new_insts)
    n_pol, n_tak = write_report(pols, staging, tak, report)

    by_idx = {p['idx']: p for p in pols}
    pn = lambda i: by_idx[i]['pol_no']  # noqa: E731
    in_scope = [p for p in pols if p['durum'] != 'B']
    quotes = [p for p in pols if p['durum'] == 'B']

    def ikey(i, no):
        return f"{pn(i)}/{no}"

    def inst_by_no(i, no):
        return [x for x in by_idx[i]['insts'] if x['no'] == no][0]

    exp = {
        'meta': {
            'legacy_policies': len(pols), 'legacy_installments': sum(len(p['insts']) for p in pols),
            'in_scope_policies': n_pol, 'in_scope_installments': n_tak,
            'target_policies': len(new_pols), 'target_installments': len(new_insts),
        },
        'K1_status_S_to_SUSPENDED': sorted(p['pol_no'] for p in in_scope if p['durum'] == 'S'),
        'K2_address_truncated_50': sorted(pn(i) for i in LONG_ADDR),
        'K3_cancel_date_1900': sorted(p['pol_no'] for p in in_scope
                                      if p['iptal'] is None and p['pol_no'] not in rejected),
        'K4_loss_payee_transliterated': sorted(pn(i) for i in LOSS_PAYEES),
        'K5_missing_parent': {'policy': rejected,
                              'orphan_installments': [f"{p['pol_no']}/{x['no']}" for p in pols
                                                      if p['pol_no'] in rejected for x in p['insts']]},
        'K6_lost_installments_ge10': {'policies': sorted({k.split('/')[0] for k in lost_keys}),
                                      'installments': lost_keys},
        'K7_duplicate_installments_rerun': dup_keys,
        'K8_refund_sign_lost': {'policies': sorted(p['pol_no'] for p in in_scope if p['durum'] == 'I'),
                                'installments': [f"{p['pol_no']}/{x['no']}" for p in in_scope
                                                 for x in p['insts'] if x['tip'] == 'Z']},
        'K9_agency_A04_A09_swapped': {'A04': sorted(p['pol_no'] for p in in_scope if p['agency'] == 'A04'),
                                      'A09': sorted(p['pol_no'] for p in in_scope if p['agency'] == 'A09')},
        'K10_late_flag_utc_date': sorted(ikey(i, list(PLAN[i][6]['pay'])[0]) for i in K10_IDX),
        'K11_fx_rate_rounded': sorted(p['pol_no'] for p in in_scope if p['kur'] is not None
                                      and p['kur'] != p['kur'].quantize(D2)),
        'K11_fx_rate_unaffected_foreign': sorted(p['pol_no'] for p in in_scope if p['kur'] is not None
                                                 and p['doviz'] in ('USD', 'EUR')
                                                 and p['kur'] == p['kur'].quantize(D2)),
        'T1_utc_shift_crosses_midnight': {
            'policies': sorted(p['pol_no'] for p in in_scope if p['son'].hour < 3
                               and p['pol_no'] not in rejected),
            'installments': sorted(f"{p['pol_no']}/{x['no']}" for p in in_scope for x in p['insts']
                                   if x['odeme'] and x['odeme'].hour < 3)},
        'T1_on_time_midnight_payments': sorted(ikey(i, list(PLAN[i][6]['pay'])[0]) for i in T1I_IDX),
        'T2_quotes_not_migrated': {'policies': sorted(p['pol_no'] for p in quotes),
                                   'installments': [f"{p['pol_no']}/{x['no']}" for p in quotes
                                                    for x in p['insts']]},
        'T3_empty_currency_to_TRY': sorted(p['pol_no'] for p in in_scope if p['doviz'] == ''),
        'T4_end_date_minus_1': 'all migrated policies (end_date = BIT_TAR - 1 day)',
        'T4_month_boundary_examples': sorted(p['pol_no'] for p in in_scope if p['bit'].day == 1),
        'agency_totals_legacy': {},
    }
    for ag in sorted(AGENCY_MAP):
        s = sum((p['brut'] for p in in_scope if p['agency'] == ag and CURRENCY[p['doviz']] == 'TRY'),
                Decimal('0'))
        exp['agency_totals_legacy'][ag] = f"{s:.2f} TRY"
    with open(os.path.join(HERE, 'migration2_expected.json'), 'w', encoding='utf-8') as f:
        json.dump(exp, f, ensure_ascii=False, indent=2)
    print(json.dumps(exp['meta'], indent=2))
    print('rejected:', rejected, 'dups:', dup_keys, 'lost:', lost_keys)


if __name__ == '__main__':
    main()
