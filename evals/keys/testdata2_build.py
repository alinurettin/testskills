#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""EVALUATOR-ONLY. Builds the production-like extract of trial-testdata2 and the
grading truth file. Fully deterministic (fixed seed), Python 3 stdlib only.
Never give this file (or testdata2_truth.json) to the agent under test.

Usage:  python testdata2_build.py [trial_dir]
Writes: <trial_dir>/girdiler/uretim_kesiti/{musteri,hesap,islem}.csv
        <keys_dir>/testdata2_truth.json
All people, companies, IDs, phones, e-mails and IBANs are synthetic.
IBAN bank codes 00990 (fictional Pusula Dijital Bank) and 00991-00998 (fictional
other banks) are not assigned to real Turkish banks.
"""
import csv, datetime as dt, json, os, random, sys
from decimal import Decimal

HERE = os.path.dirname(os.path.abspath(__file__))
TRIAL = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, '..', 'trial-testdata2')
OUT = os.path.join(TRIAL, 'girdiler', 'uretim_kesiti')
SNAP = dt.date(2026, 9, 30)
BANK = '00990'
R = random.Random(20261001)

# ---------------------------------------------------------------- algorithms
def tckn_check(d9):
    d10 = (sum(d9[0:9:2]) * 7 - sum(d9[1:8:2])) % 10
    return d10, (sum(d9) + d10) % 10

def tckn_valid(s):
    if len(s) != 11 or not s.isdigit() or s[0] == '0':
        return False
    d = [int(c) for c in s]
    return tckn_check(d[:9]) == (d[9], d[10])

def vkn_check(d9):
    tot = 0
    for i in range(9):
        t = (d9[i] + 9 - i) % 10
        v = (t * 2 ** (9 - i)) % 9
        if t != 0 and v == 0:
            v = 9
        tot += v
    return (10 - tot % 10) % 10

USED_IDS = set()

def make_tckn():
    while True:
        d = [R.randint(1, 9)] + [R.randint(0, 9) for _ in range(8)]
        s = ''.join(map(str, d + list(tckn_check(d))))
        if s not in USED_IDS:
            USED_IDS.add(s)
            return s

def make_vkn():
    while True:
        d = [R.randint(0, 9) for _ in range(9)]
        s = ''.join(map(str, d)) + str(vkn_check(d))
        if s not in USED_IDS:
            USED_IDS.add(s)
            return s

def iban_from(bank5, acc16):
    bban = bank5 + '0' + acc16
    num = int(''.join(str(int(c, 36)) for c in bban + 'TR00'))
    return 'TR%02d' % (98 - num % 97) + bban

def iban_valid(s):
    s = s.replace(' ', '').upper()
    if len(s) != 26 or not s.startswith('TR') or not s[2:].isdigit():
        return False
    return int(''.join(str(int(c, 36)) for c in s[4:] + s[:4])) % 97 == 1

def acc16(sube, hno):
    return sube + '0000' + hno

def is_leap(y):
    return y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)

def add_years(d, n):
    y = d.year + n
    if d.month == 2 and d.day == 29 and not is_leap(y):
        return dt.date(y, 3, 1)
    return d.replace(year=y)

def rdate(lo, hi):
    return lo + dt.timedelta(days=R.randint(0, (hi - lo).days))

def rtime(d, h0=8, h1=22):
    return dt.datetime(d.year, d.month, d.day, R.randint(h0, h1), R.randint(0, 59), R.randint(0, 59))

def spaced(s, n=4):
    return ' '.join(s[i:i + n] for i in range(0, len(s), n))

def fmt_phone(nat, style):
    a, b, c, d = nat[0:3], nat[3:6], nat[6:8], nat[8:10]
    return {
        'c0': '0%s %s %s %s' % (a, b, c, d),
        'c1': '+90 %s %s %s %s' % (a, b, c, d),
        'c2': nat,
        'c3': '(0%s) %s-%s%s' % (a, b, c, d),
        't_paren': '0 (%s) %s %s %s' % (a, b, c, d),
        't_plus': '+90' + nat,
        't_0090': '0090 %s %s %s %s' % (a, b, c, d),
        't_dash': '0%s-%s-%s%s' % (a, b, c, d),
        't_plusparen': '+90 (%s) %s %s %s' % (a, b, c, d),
        't_mixed': '+90 %s %s %s%s' % (a, b, c, d),
    }[style]

USED_PHONES = set()

def make_mobile():
    while True:
        n = R.choice(['532', '533', '535', '542', '543', '505', '506', '553', '554', '555']) + \
            ''.join(str(R.randint(0, 9)) for _ in range(7))
        if n not in USED_PHONES:
            USED_PHONES.add(n)
            return n

def make_landline(area):
    while True:
        n = area + str(R.randint(2, 9)) + ''.join(str(R.randint(0, 9)) for _ in range(6))
        if n not in USED_PHONES:
            USED_PHONES.add(n)
            return n

ASCII = str.maketrans('çğıöşüÇĞİÖŞÜâ', 'cgiosuCGIOSUa')

def ascii_slug(s):
    return s.translate(ASCII).lower().replace(' ', '.')

def tr_upper(s):
    return s.replace('i', 'İ').replace('ı', 'I').upper()

# ---------------------------------------------------------------- pools
FEMALE = ('Fatma Emine Zeynep Meryem Şerife Zehra Sultan Hanife Merve Havva Esra Özlem Yasemin Hülya Derya '
          'Sevgi Gamze Büşra Ebru Tuğba Sibel Aslı Nur Seda Gizem Ece Ceren Burcu Melike Nazlı Dilek Songül '
          'Nermin Gülay Filiz Nilgün Tülay Şule İpek İrem Çiğdem Şeyma Öykü İlknur Berna Feride Neslihan').split()
MALE = ('Mustafa Ahmet Hasan Osman Yusuf Murat Ömer Ramazan Halil Süleyman Abdullah Mahmut Burak Serkan '
        'Kemal Okan Volkan Tolga Cem Onur Uğur Gökhan Erkan Erdem Kaan Arda Berk Can Selim Tarık Levent '
        'Orhan Şükrü Özgür İlker Çağrı Taner Yiğit Umut İsmet Kadir Sinan Hakan Bülent Cengiz').split()
SURN = ('Yıldırım Aydın Özdemir Doğan Aslan Çetin Kara Özkan Şimşek Özer Korkmaz Erdem Akın Karaca Bulut '
        'Tekin Güneş Keskin Taş Acar Sarı Işık Uçar Tunç Türkmen Coşkun Bozkurt Kaplan Uysal Güler Eren Ateş '
        'Duman Oral Altun Toprak Ekinci Sezer İnce Ilgaz Yazıcı Kocaman Erten Soylu Akbulut Gündoğdu').split()

ILCE = {'İstanbul': ['Kadıköy', 'Beşiktaş', 'Üsküdar', 'Şişli', 'Bakırköy', 'Ataşehir'],
        'Ankara': ['Çankaya', 'Keçiören', 'Yenimahalle', 'Etimesgut'],
        'İzmir': ['Konak', 'Bornova', 'Karşıyaka', 'Buca'],
        'Bursa': ['Nilüfer', 'Osmangazi'], 'Adana': ['Seyhan', 'Çukurova'],
        'Trabzon': ['Ortahisar'], 'Şanlıurfa': ['Halfeti', 'Haliliye'], 'Bayburt': ['Merkez']}
AREA = {'İstanbul': '216', 'Ankara': '312', 'İzmir': '232', 'Bursa': '224', 'Adana': '322',
        'Trabzon': '462', 'Şanlıurfa': '414', 'Bayburt': '458'}
SUBE = {'0101': 'İstanbul', '0102': 'İstanbul', '0103': 'İstanbul', '0207': 'Ankara', '0208': 'Ankara',
        '0315': 'İzmir', '0316': 'İzmir', '0420': 'Bursa', '0512': 'Adana', '0611': 'Trabzon'}

# (il, cinsiyet, decade, count) -> every (il, cinsiyet, decade) cell has 0 or >=5 people
CELLS = [('İstanbul', 'E', 1960, 5), ('İstanbul', 'E', 1970, 6), ('İstanbul', 'E', 1980, 7),
         ('İstanbul', 'E', 1990, 6), ('İstanbul', 'E', 2000, 5), ('İstanbul', 'K', 1970, 6),
         ('İstanbul', 'K', 1980, 7), ('İstanbul', 'K', 1990, 6), ('İstanbul', 'K', 2000, 5),
         ('Ankara', 'E', 1970, 5), ('Ankara', 'E', 1980, 6), ('Ankara', 'E', 2000, 5),
         ('Ankara', 'K', 1980, 5), ('Ankara', 'K', 1990, 5), ('İzmir', 'E', 1980, 5), ('İzmir', 'K', 1990, 5)]

# tag: (first, last, il, cinsiyet, birth, ilce)
SPECIAL = {
    'AYSE': ('Ayşe', 'Yılmaz', 'İstanbul', 'K', dt.date(1984, 6, 17), 'Kadıköy'),
    'ALI': ('Ali', 'Kaya', 'İstanbul', 'E', dt.date(1976, 3, 9), 'Beşiktaş'),
    'IBRAHIM': ('İbrahim', 'Çelik', 'İstanbul', 'E', dt.date(1963, 11, 30), 'Üsküdar'),
    'HATICE': ('Hatice', 'Arslan', 'İstanbul', 'K', dt.date(1972, 1, 21), 'Bakırköy'),
    'GULSEN': ('Gülşen', 'Çelik', 'İstanbul', 'K', dt.date(1978, 9, 5), 'Ataşehir'),
    'ELIF': ('Elif Naz', 'Demir', 'İstanbul', 'K', dt.date(2008, 2, 29), 'Kadıköy'),
    'MALIKAYA': ('Mehmet Ali', 'Kaya', 'Ankara', 'E', dt.date(1971, 7, 14), 'Çankaya'),
    'MEHMETOZ': ('Mehmet', 'Öztürk', 'Ankara', 'E', dt.date(1987, 12, 2), 'Keçiören'),
    'EMRE': ('Emre', 'Yıldız', 'Ankara', 'E', dt.date(2004, 2, 29), 'Yenimahalle'),
    'HUSEYIN': ('Hüseyin', 'Kılıç', 'İzmir', 'E', dt.date(1982, 4, 26), 'Bornova'),
    'ISIL': ('Işıl', 'Kılıç', 'İzmir', 'K', dt.date(1994, 10, 11), 'Karşıyaka'),
}
OUTLIERS = [('Şanlıurfa', 'Halfeti', 'E', dt.date(1931, 5, 12)),
            ('Bayburt', 'Merkez', 'K', dt.date(1955, 8, 3)),
            ('İzmir', 'Buca', 'E', dt.date(1999, 11, 23))]
THIRD = ['Fatma Demir', 'İsmail Şahin', 'Ahmet Çakır', 'Barış Aksoy', 'Sevim Demir', 'Özge Ünal',
         'Mustafa Kurt', 'Zeynep Aydın', 'Recep Polat']

CORP = [  # unvan, sirket_turu, il, ilce
    ('Kuzey Lojistik Ltd. Şti.', 'LTD', 'İstanbul', 'Şişli'),
    ('Kaya Turizm ve Seyahat A.Ş.', 'AS', 'İzmir', 'Konak'),
    ('Demir Çelik Sanayi A.Ş.', 'AS', 'Bursa', 'Osmangazi'),
    ('Göksu İnşaat Ltd. Şti.', 'LTD', 'Ankara', 'Etimesgut'),
    ('Anadolu Gıda Pazarlama A.Ş.', 'AS', 'Ankara', 'Yenimahalle'),
    ('Ege Tekstil Dış Ticaret A.Ş.', 'AS', 'İzmir', 'Bornova'),
    ('Marmara Yazılım Ltd. Şti.', 'LTD', 'İstanbul', 'Ataşehir'),
    ('Toros Tarım Ürünleri A.Ş.', 'AS', 'Adana', 'Seyhan'),
    ('Karadeniz Su Ürünleri Ltd. Şti.', 'LTD', 'Trabzon', 'Ortahisar'),
    ('Uludağ Otomotiv Yan Sanayi A.Ş.', 'AS', 'Bursa', 'Nilüfer'),
    ('Çukurova Pamuk A.Ş.', 'AS', 'Adana', 'Çukurova'),
    ('Boğaziçi Danışmanlık Ltd. Şti.', 'LTD', 'İstanbul', 'Beşiktaş'),
    ('Kapadokya Seramik A.Ş.', 'AS', 'Ankara', 'Çankaya'),
    ('Fırat Enerji A.Ş.', 'AS', 'Şanlıurfa', 'Haliliye'),
    ('Akdeniz Narenciye A.Ş.', 'AS', 'Adana', 'Seyhan'),
    ('Trakya Un Sanayi A.Ş.', 'AS', 'İstanbul', 'Bakırköy'),
    ('Mavi Liman Denizcilik A.Ş.', 'AS', 'İzmir', 'Karşıyaka'),
    ('Bereket Ambalaj Ltd. Şti.', 'LTD', 'Bursa', 'Osmangazi'),
    ('Yeşilırmak Mobilya Ltd. Şti.', 'LTD', 'Ankara', 'Keçiören'),
    ('Kırlangıç Turizm A.Ş.', 'AS', 'Trabzon', 'Ortahisar'),
    ('Aksu Kimya A.Ş.', 'AS', 'İstanbul', 'Kadıköy'),
    ('Doruk Medikal Ltd. Şti.', 'LTD', 'İzmir', 'Buca'),
    ('Kuzgun Bilişim Ltd. Şti.', 'LTD', 'İstanbul', 'Üsküdar'),
    ('Selvi Peyzaj A.Ş.', 'AS', 'Bursa', 'Nilüfer'),
    ('Sarp Makine Sanayi A.Ş.', 'AS', 'Ankara', 'Etimesgut'),
    ('Ilgın Kozmetik A.Ş.', 'AS', 'İstanbul', 'Şişli'),
    ('Hatice Arslan Tekstil', 'SAHIS', 'İstanbul', 'Bakırköy'),
    ('Mustafa Kurt Oto Yedek Parça', 'SAHIS', 'Bursa', 'Osmangazi'),
    ('Zeynep Aydın Kırtasiye', 'SAHIS', 'Ankara', 'Çankaya'),
    ('Recep Polat Nakliyat', 'SAHIS', 'Adana', 'Seyhan'),
]

# ---------------------------------------------------------------- customers
customers = []          # dicts
by_tag = {}
used_names = {f + ' ' + l for (f, l, *_r) in SPECIAL.values()} | set(THIRD)
used_mno = set()
used_mail = set()

def new_mno():
    while True:
        m = 'M%06d' % R.randint(100000, 999999)
        if m not in used_mno:
            used_mno.add(m)
            return m

def uniq_mail(base, dom):
    m, k = base + '@' + dom, 2
    while m in used_mail:
        m, k = '%s%d@%s' % (base, k, dom), k + 1
    used_mail.add(m)
    return m

def gen_name(sex):
    while True:
        f = R.choice(FEMALE if sex == 'K' else MALE)
        l = R.choice(SURN)
        if f + ' ' + l not in used_names:
            used_names.add(f + ' ' + l)
            return f, l

def person(first, last, il, ilce, sex, birth, tag=None):
    b18 = add_years(birth, 18)
    lo = max(b18, dt.date(2005, 1, 1))
    hi = SNAP - dt.timedelta(days=40)
    kayit = rdate(lo, hi) if lo <= hi else lo
    nat = make_mobile()
    c = dict(musteri_no=new_mno(), musteri_tipi='BIREYSEL', tckn=make_tckn(), vkn='', ad=first, soyad=last,
             unvan='', sirket_turu='', dogum=birth, kurulus=None, cinsiyet=sex, il=il, ilce=ilce,
             eposta=uniq_mail(ascii_slug(first + ' ' + last), R.choice(['example.com', 'example.test'])),
             phone_nat=nat, telefon=fmt_phone(nat, R.choice(['c0', 'c0', 'c1', 'c2', 'c3'])),
             kayit=kayit, notlar='', tag=tag)
    customers.append(c)
    if tag:
        by_tag[tag] = c
    return c

for il, sex, dec, cnt in CELLS:
    specials = [(t, v) for t, v in SPECIAL.items() if v[2] == il and v[3] == sex and v[4].year // 10 * 10 == dec]
    for t, (f, l, _il, _s, b, ilce) in specials:
        person(f, l, il, ilce, sex, b, t)
    for _ in range(cnt - len(specials)):
        f, l = gen_name(sex)
        hi = dt.date(min(dec + 9, 2008), 12, 31) if dec < 2000 else dt.date(2008, 6, 30)
        person(f, l, il, R.choice(ILCE[il]), sex, rdate(dt.date(dec, 1, 1), hi))
for il, ilce, sex, b in OUTLIERS:
    f, l = gen_name(sex)
    person(f, l, il, ilce, sex, b, 'OUT_' + il)

# Feb-29 specials: registered exactly on their 18th birthday (1 March) -> trap T3
by_tag['ELIF']['kayit'] = dt.date(2026, 3, 1)
by_tag['EMRE']['kayit'] = dt.date(2022, 3, 1)
by_tag['AYSE']['eposta'] = 'ayse.yilmaz@example.com'
by_tag['ALI']['eposta'] = 'ali.kaya@example.com'
by_tag['HATICE']['eposta'] = 'hatice.arslan@example.com'
by_tag['GULSEN']['eposta'] = 'gulsen.celik@example.test'
by_tag['ALI']['telefon'] = fmt_phone(by_tag['ALI']['phone_nat'], 'c1')
by_tag['AYSE']['telefon'] = fmt_phone(by_tag['AYSE']['phone_nat'], 'c0')
by_tag['HUSEYIN']['telefon'] = fmt_phone(by_tag['HUSEYIN']['phone_nat'], 'c3')
by_tag['MEHMETOZ']['telefon'] = fmt_phone(by_tag['MEHMETOZ']['phone_nat'], 'c0')
for t in ('AYSE', 'ALI', 'HATICE', 'GULSEN'):
    used_mail.add(by_tag[t]['eposta'])

for unvan, typ, il, ilce in CORP:
    kur = rdate(dt.date(1985, 1, 1), dt.date(2022, 12, 31))
    kayit = rdate(max(kur, dt.date(2005, 1, 1)), SNAP - dt.timedelta(days=60))
    if typ == 'SAHIS':
        mail = uniq_mail(ascii_slug(' '.join(unvan.split()[:2])) + '.isletme', 'example.com')
        nat = make_mobile()
    else:
        mail = uniq_mail('iletisim.' + ascii_slug(unvan.split()[0]), 'example.com')
        nat = make_landline(AREA[il])
    c = dict(musteri_no=new_mno(), musteri_tipi='KURUMSAL', tckn='', vkn=make_vkn(), ad='', soyad='',
             unvan=unvan, sirket_turu=typ, dogum=None, kurulus=kur, cinsiyet='', il=il, ilce=ilce,
             eposta=mail, phone_nat=nat, telefon=fmt_phone(nat, R.choice(['c0', 'c1', 'c3'])),
             kayit=kayit, notlar='', tag='CORP_' + unvan.split()[0])
    customers.append(c)
    by_tag[c['tag']] = c
# a few corporates registered on their founding day (boundary, legal)
for t in ('CORP_Selvi', 'CORP_Aksu'):
    by_tag[t]['kurulus'] = by_tag[t]['kayit']

# ---------------------------------------------------------------- accounts
accounts = []
used_hno = set()

def new_hno():
    while True:
        h = '1%07d' % R.randint(0, 9999999)
        if h not in used_hno:
            used_hno.add(h)
            return h

def branch_for(c):
    opts = [s for s, il in SUBE.items() if il == c['il']]
    return R.choice(opts) if opts else R.choice(sorted(SUBE))

def account(c, turu='VADESIZ', doviz='TRY', acilis=None, sube=None):
    a = dict(sube=sube or branch_for(c), hno=new_hno(), cust=c, turu=turu, doviz=doviz,
             limit=Decimal(R.choice(['5000.00', '10000.00', '15000.00', '25000.00'])) if turu == 'KMH' else Decimal('0.00'),
             acilis=acilis or rdate(c['kayit'], SNAP - dt.timedelta(days=30)), tx=[])
    accounts.append(a)
    return a

for c in customers:
    if c['musteri_tipi'] == 'BIREYSEL':
        if c['tag'] == 'ELIF':
            account(c, acilis=dt.date(2026, 3, 1))
            continue
        if c['tag'] == 'EMRE':
            account(c, acilis=dt.date(2022, 3, 1))
            account(c, 'KMH')
            continue
        n = R.choices([1, 2, 3], [55, 33, 12])[0]
        for i in range(n):
            if i == 0 and R.random() < 0.3:
                account(c, 'KMH')
            else:
                account(c, doviz=R.choices(['TRY', 'USD', 'EUR'], [78, 13, 9])[0] if i else 'TRY')
    else:
        for i in range(R.choice([1, 2, 2, 3])):
            account(c, doviz='TRY' if i == 0 else R.choice(['TRY', 'USD', 'EUR']))
for t in ('AYSE', 'ALI', 'MEHMETOZ', 'MALIKAYA', 'HUSEYIN', 'ISIL', 'IBRAHIM', 'GULSEN', 'HATICE'):
    c = by_tag[t]
    if not any(a['cust'] is c and a['doviz'] == 'TRY' and a['turu'] == 'VADESIZ' for a in accounts):
        account(c)
if sum(1 for a in accounts if a['cust'] is by_tag['MALIKAYA']) < 2:
    account(by_tag['MALIKAYA'])
# composite key: the same hesap_no legitimately exists in two different branches (trap T1)
dups = []
pool = [a for a in accounts if a['cust']['tag'] not in SPECIAL]
R.shuffle(pool)
for a in pool:
    if len(dups) == 3:
        break
    b = next((x for x in pool if x is not a and x['sube'] != a['sube'] and x not in [d for p in dups for d in p]
              and a not in [d for p in dups for d in p]), None)
    if b:
        b['hno'] = a['hno']
        dups.append((a, b))
for a in accounts:
    a['iban'] = iban_from(BANK, acc16(a['sube'], a['hno']))
assert len({(a['sube'], a['hno']) for a in accounts}) == len(accounts)

def main_try(tag):
    return next(a for a in accounts if a['cust'] is by_tag[tag] and a['doviz'] == 'TRY' and a['turu'] == 'VADESIZ')

# ---------------------------------------------------------------- fixed dates for planted actors
def early(c):
    base = c['kurulus'] if c['kurulus'] else add_years(c['dogum'], 18)
    if c['kayit'] > dt.date(2023, 12, 31):
        c['kayit'] = rdate(max(base, dt.date(2010, 1, 1)), dt.date(2023, 12, 31))
    for a in accounts:
        if a['cust'] is c:
            a['acilis'] = rdate(c['kayit'], min(c['kayit'] + dt.timedelta(days=400), SNAP - dt.timedelta(days=30)))

for t in ('AYSE', 'ALI', 'IBRAHIM', 'HATICE', 'GULSEN', 'MALIKAYA', 'MEHMETOZ', 'HUSEYIN', 'ISIL',
          'CORP_Kuzey', 'CORP_Kaya', 'CORP_Demir', 'CORP_Göksu', 'CORP_Hatice', 'CORP_Mustafa'):
    early(by_tag[t])
mali = by_tag['MALIKAYA']
if not [a for a in accounts if a['cust'] is mali and a['doviz'] == 'TRY' and a is not main_try('MALIKAYA')]:
    account(mali, acilis=rdate(mali['kayit'], dt.date(2024, 6, 30)))
    accounts[-1]['iban'] = iban_from(BANK, acc16(accounts[-1]['sube'], accounts[-1]['hno']))
MALI2 = next(a for a in accounts if a['cust'] is mali and a['doviz'] == 'TRY' and a is not main_try('MALIKAYA'))

# ---------------------------------------------------------------- transactions
DESC = {'YATIRMA': ['ATM para yatırma', 'Şubeden nakit yatırma', 'Nakit yatırma - şube'],
        'CEKME': ['ATM para çekme', 'POS - KARDELEN MARKET', 'POS - AKÇAAĞAÇ ECZANESİ', 'POS - LALE KIRTASİYE',
                  'POS - GÜNEY AKARYAKIT', 'Şubeden nakit çekme', 'POS - MENEKŞE FIRINI'],
        'FAIZ': ['Faiz tahakkuku'], 'MASRAF': ['EFT masrafı', 'Hesap işletim ücreti', 'Kart aidatı'],
        'HAVALE_GELEN': ['Maaş ödemesi', 'Kira geliri', 'Prim ödemesi', 'Gelen EFT'],
        'HAVALE_GELEN_C': ['Fatura tahsilatı', 'Mal bedeli tahsilatı', 'Hizmet bedeli tahsilatı'],
        'HAVALE_GIDEN': ['Fatura ödemesi', 'Aidat ödemesi', 'Giden EFT', 'Okul taksiti'],
        'HAVALE_GIDEN_C': ['Tedarikçi ödemesi', 'Vergi ödemesi', 'SGK prim ödemesi', 'Kira ödemesi - işyeri']}
SIGN = {'YATIRMA': 1, 'HAVALE_GELEN': 1, 'FAIZ': 1, 'CEKME': -1, 'HAVALE_GIDEN': -1, 'MASRAF': -1}

def money(lo, hi):
    return Decimal(R.randint(int(lo * 100), int(hi * 100))) / 100

def ext_iban(bank=None):
    return iban_from(bank or '0099%d' % R.randint(1, 8), ''.join(str(R.randint(0, 9)) for _ in range(16)))

def ib_fmt(iban, style):
    return {'c': iban, 's': spaced(iban), 'ls': spaced(iban).lower(), 'l': iban.lower()}[style]

def ib_style():
    return R.choices(['c', 's', 'ls', 'l'], [70, 18, 6, 6])[0]

def tx(a, when, tip, amount, karsi='', acik='', truth=None):
    t = dict(acc=a, dt=when, tip=tip, tutar=(SIGN[tip] * abs(amount)).quantize(Decimal('0.01')), karsi=karsi, acik=acik, truth=truth or [])
    a['tx'].append(t)
    return t

for a in accounts:
    corp = a['cust']['musteri_tipi'] == 'KURUMSAL'
    tx(a, rtime(a['acilis'], 9, 12), 'YATIRMA', Decimal(R.randint(5, 200 if corp else 40) * 100), acik='Hesap açılış yatırması')
    bal = a['tx'][0]['tutar']
    n = R.randint(8, 16) if corp else R.randint(3, 11)
    for d in sorted(rdate(a['acilis'] + dt.timedelta(days=1), SNAP) for _ in range(n)):
        tip = R.choices(['YATIRMA', 'HAVALE_GELEN', 'FAIZ', 'CEKME', 'HAVALE_GIDEN', 'MASRAF'], [14, 22, 6, 26, 22, 10])[0]
        if tip == 'FAIZ' and a['doviz'] != 'TRY':
            tip = 'MASRAF'
        amt = {'YATIRMA': money(100, 5000), 'HAVALE_GELEN': money(5000, 150000) if corp else money(1000, 30000),
               'FAIZ': money(1, 150), 'CEKME': money(50, 3000), 'HAVALE_GIDEN': money(2000, 90000) if corp else money(200, 15000),
               'MASRAF': money(2.5, 45)}[tip]
        if SIGN[tip] < 0:
            room = bal + a['limit']
            if room < Decimal('5'):
                tip, amt = 'YATIRMA', money(500, 3000)
            elif amt > room:
                amt = (room * Decimal('0.9')).quantize(Decimal('0.01'))
        key = tip + ('_C' if corp and tip.startswith('HAVALE') else '')
        k = ext_iban() if tip.startswith('HAVALE') else ''
        t = tx(a, rtime(d), tip, amt, ib_fmt(k, ib_style()) if k else '', R.choice(DESC[key]))
        bal += t['tutar']

# internal transfers -----------------------------------------------------
REF = [0]

def transfer(src, dst, when, amount, acik_out, acik_in, st_out='c', st_in='c', tr_out=None, tr_in=None, ref=True):
    if ref:
        REF[0] += 1
        code = 'HVL-%d-%06d ' % (when.year, 100 + REF[0] * 37)
        acik_out, acik_in = code + acik_out, code + acik_in
    a = tx(src, when, 'HAVALE_GIDEN', amount, ib_fmt(dst['iban'], st_out), acik_out, tr_out)
    b = tx(dst, when, 'HAVALE_GELEN', amount, ib_fmt(src['iban'], st_in), acik_in, tr_in)
    return a, b

try_acc = [a for a in accounts if a['doviz'] == 'TRY']
for _ in range(24):
    s, d = R.sample(try_acc, 2)
    if s['cust'] is d['cust']:
        continue
    lo = max(s['acilis'], d['acilis']) + dt.timedelta(days=1)
    if lo >= SNAP:
        continue
    transfer(s, d, rtime(rdate(lo, SNAP)), money(100, 4000), R.choice(['Para transferi', 'Borç ödemesi', 'Aile desteği']),
             'Gelen havale', ib_style(), ib_style())
da, db = next(((x, y) for x, y in dups if x['doviz'] == y['doviz'] == 'TRY'), dups[0])
transfer(da, db, rtime(rdate(max(da['acilis'], db['acilis']) + dt.timedelta(days=1), SNAP)), money(100, 900),
         'Para transferi', 'Gelen havale')

TRUTH = dict(name_occ=[], consistency=[], third_tckn=[], third_phone=[], third_email=[], extra_iban=[])
A = {t: main_try(t) for t in ('AYSE', 'ALI', 'IBRAHIM', 'GULSEN', 'MALIKAYA', 'MEHMETOZ', 'HUSEYIN', 'ISIL', 'ELIF', 'EMRE')}
for t in ('CORP_Kuzey', 'CORP_Kaya', 'CORP_Demir', 'CORP_Göksu', 'CORP_Hatice'):
    A[t] = next(a for a in accounts if a['cust'] is by_tag[t] and a['doviz'] == 'TRY')

def nocc(phrase):
    return {'kind': 'name', 'phrase': phrase}

def cons(cid, kind, ref):
    return {'kind': 'cons', 'id': cid, 'ctype': kind, 'ref': ref}

# landlord (external, recurring, mixed formats) - P1 / CN12
L = ext_iban('00993')
TRUTH['extra_iban'].append(L)
for i, (m, st) in enumerate(zip(range(4, 10), ['c', 's', 'c', 'ls', 'c', 's'])):
    acik = "Kira ödemesi - Özge Ünal'a" if i in (0, 3) else 'Ev kirası'
    tx(A['AYSE'], dt.datetime(2026, m, 3, 10, 12 + i, 5), 'HAVALE_GIDEN', Decimal('18500.00'), ib_fmt(L, st), acik,
       [nocc('özge ünal')] if i in (0, 3) else [] + [{'kind': 'cons', 'id': 'CN12', 'ctype': 'iban_same', 'bank': '00993'}])
for t in A['AYSE']['tx']:
    if t['karsi'] and t['karsi'].replace(' ', '').upper() == L:
        if not any(o.get('id') == 'CN12' for o in t['truth']):
            t['truth'].append({'kind': 'cons', 'id': 'CN12', 'ctype': 'iban_same', 'bank': '00993'})
# Kuzey Lojistik salaries (internal; T4 fragment)
emps = [a for a in accounts if a['cust']['musteri_tipi'] == 'BIREYSEL' and a['doviz'] == 'TRY' and a['turu'] == 'VADESIZ'
        and a['acilis'] < dt.date(2026, 8, 1) and a['cust']['tag'] not in SPECIAL][:3]
for e in emps:
    transfer(A['CORP_Kuzey'], e, dt.datetime(2026, 9, 15, 9, 30, R.randint(0, 59)), money(32000, 45000),
             'Maaş ödemesi - Eylül 2026', 'Maaş ödemesi - Kuzey Lojistik Ltd. Şti.', ref=False)
# Yıldız Sitesi aidat (external)
S = ext_iban('00995')
for i, p in enumerate([a for a in accounts if a['cust']['il'] == 'İstanbul' and a['cust']['musteri_tipi'] == 'BIREYSEL'
                       and a['doviz'] == 'TRY' and a['cust']['tag'] not in SPECIAL][3:6]):
    tx(p, dt.datetime(2026, 9, 5 + i, 11, 0, 0), 'HAVALE_GIDEN', Decimal('1450.00'), S, 'Aidat - Yıldız Sitesi Yönetimi')
# Demir Çelik invoice (internal) + invoice number that is NOT a TCKN (fails checksum)
assert not tckn_valid('40001234567')
transfer(A['CORP_Göksu'], A['CORP_Demir'], dt.datetime(2026, 6, 12, 14, 22, 5), Decimal('87450.00'),
         'Fatura ödemesi - Demir Çelik Sanayi A.Ş. Fatura no 40001234567',
         'Fatura tahsilatı - Göksu İnşaat Ltd. Şti. Fatura no 40001234567', ref=False)
# Kaya Turizm (internal)
transfer(A['ALI'], A['CORP_Kaya'], dt.datetime(2026, 7, 2, 16, 40, 12), Decimal('24600.00'),
         'Tur bedeli - Kaya Turizm ve Seyahat A.Ş.', 'Tur satış tahsilatı - Ali Kaya', ref=False,
         tr_in=[nocc('ali kaya')])
gen_ind = [a for a in accounts if a['cust']['musteri_tipi'] == 'BIREYSEL' and a['doviz'] == 'TRY'
           and a['cust']['tag'] not in SPECIAL and a not in emps]
tx(gen_ind[7], rtime(rdate(gen_ind[7]['acilis'] + dt.timedelta(days=2), SNAP)), 'YATIRMA', Decimal('35.00'), '',
   'Ücret iadesi - Pusula Müşteri Hizmetleri 0850 724 00 00 kaydı')
tx(gen_ind[8], rtime(rdate(gen_ind[8]['acilis'] + dt.timedelta(days=2), SNAP)), 'CEKME', Decimal('1250.00'), '',
   'Kredi kartı borç ödemesi 1.250,00 TL')
# A2: named internal transfer
transfer(A['MEHMETOZ'], A['AYSE'], dt.datetime(2025, 11, 20, 13, 5, 44), Decimal('7500.00'),
         "Ayşe Yılmaz'a borç iadesi", "MEHMET ÖZTÜRK'ten gelen havale", 's', 'c',
         [nocc('ayşe yılmaz')], [nocc('mehmet öztürk')])
# A3/A4: FAST kolay adres with phone / e-mail of another customer
ay = by_tag['AYSE']
transfer(A['ALI'], A['AYSE'], dt.datetime(2026, 2, 14, 19, 2, 31), Decimal('2750.00'),
         'FAST kolay adres ödemesi %s' % fmt_phone(ay['phone_nat'], 't_paren'), 'FAST gelen - kolay adres', ref=False,
         tr_out=[cons('CN6', 'phone', 'AYSE')])
transfer(A['ALI'], A['AYSE'], dt.datetime(2026, 5, 1, 8, 45, 0), Decimal('1200.00'),
         'Kolay adres: %s' % ay['eposta'], 'FAST gelen - kolay adres', ref=False, tr_out=[cons('CN15', 'email', 'AYSE')])
# A5: third-party payee name + external IBAN in text (spaced) == karsi_iban column (compact)
P = ext_iban('00996')
tx(A['CORP_Göksu'], dt.datetime(2026, 8, 29, 17, 10, 3), 'HAVALE_GIDEN', Decimal('15750.00'), P,
   'HAVALE: AHMET ÇAKIR / %s' % spaced(P), [nocc('ahmet çakır'), cons('CN10', 'iban_textcol', None)])
TRUTH['extra_iban'].append(P)
# A6: payment to sole proprietorship (name in upper case with dotted İ)
x = gen_ind[9]
transfer(x, A['CORP_Hatice'], rtime(rdate(max(x['acilis'], A['CORP_Hatice']['acilis']) + dt.timedelta(days=1), SNAP)),
         Decimal('3200.00'), "HATİCE ARSLAN TEKSTİL'e ödeme", 'Gelen havale', ref=False, tr_out=[nocc('hatice arslan')])
# A12: insurance (external) with upper-case name
tx(A['IBRAHIM'], dt.datetime(2026, 3, 18, 10, 0, 0), 'HAVALE_GIDEN', Decimal('4120.00'), ext_iban('00997'),
   'Sigorta primi - Sn. İBRAHİM ÇELİK', [nocc('ibrahim çelik')])
# A13: own-account transfer, own IBAN in text (lower case, spaced)
transfer(A['MALIKAYA'], MALI2, dt.datetime(2026, 4, 9, 12, 30, 0), Decimal('5000.00'),
         'Virman - kendi hesabına %s' % spaced(MALI2['iban']).lower(), 'Virman - kendi hesabından', ref=False,
         tr_out=[cons('CN9', 'iban', 'MALI2')])
# A14: Ali's phone in a different format in someone else's transfer
y = gen_ind[10]
transfer(y, A['ALI'], rtime(rdate(max(y['acilis'], A['ALI']['acilis']) + dt.timedelta(days=1), SNAP)), Decimal('640.00'),
         'Kolay adres %s numarasına gönderim' % fmt_phone(by_tag['ALI']['phone_nat'], 't_mixed'), 'FAST gelen',
         ref=False, tr_out=[cons('CN7', 'phone', 'ALI')])
# A15: scholarship to Emre (name contains 'Yıldız')
transfer(A['CORP_Kuzey'], A['EMRE'], dt.datetime(2026, 9, 1, 10, 0, 0), Decimal('3000.00'), 'Burs ödemesi - Emre Yıldız',
         'Burs ödemesi', ref=False, tr_out=[nocc('emre yıldız')])
# A16: Gülşen -> Elif (Feb-29 customer)
transfer(A['GULSEN'], A['ELIF'], dt.datetime(2026, 3, 20, 18, 0, 0), Decimal('500.00'), 'Elif Naz Demir harçlık',
         'Harçlık - GÜLŞEN ÇELİK', ref=False, tr_out=[nocc('elif naz demir')], tr_in=[nocc('gülşen çelik')])
# A17: Hüseyin -> Işıl
transfer(A['HUSEYIN'], A['ISIL'], dt.datetime(2026, 5, 11, 20, 15, 0), Decimal('1500.00'),
         "Işıl Kılıç'a doğum günü hediyesi", 'Gelen havale', tr_out=[nocc('ışıl kılıç')])
# A18: closed internal account (not in extract) in two rows, two formats
assert not any(a['sube'] == '0208' and a['hno'] == '19999999' for a in accounts)
C = iban_from(BANK, acc16('0208', '19999999'))
TRUTH['extra_iban'].append(C)
for acc, st, when in ((A['HUSEYIN'], 'c', dt.datetime(2026, 1, 12, 9, 15, 0)), (A['ISIL'], 'ls', dt.datetime(2026, 1, 12, 9, 16, 0))):
    tx(acc, when, 'HAVALE_GELEN', Decimal('2250.00'), ib_fmt(C, st), 'Kapanan hesaptan virman',
       [{'kind': 'cons', 'id': 'CN11', 'ctype': 'iban_same', 'bank': '00990'}])

# ---------------------------------------------------------------- CRM notes (musteri.notlar)
ISMAIL_TCKN, KURT_TCKN = make_tckn(), make_tckn()
FATMA_PH, BARIS_PH = make_mobile(), make_mobile()
TRUTH['third_tckn'] += [ISMAIL_TCKN, KURT_TCKN]
TRUTH['third_phone'] += [FATMA_PH, BARIS_PH]
for c in customers:
    c['truth'] = []
B = by_tag

def note(tag, text, *occ):
    B[tag]['notlar'] = text
    B[tag]['truth'] += list(occ)

tk = B['AYSE']['tckn']
note('AYSE', 'Müşteri TCKN %s %s %s %s ile şubeye geldi, kimlik teyit edildi.' % (tk[:3], tk[3:6], tk[6:9], tk[9:]),
     cons('CN1', 'tckn', 'AYSE'))
note('ALI', 'İletişim tercihi e-posta: ali.kaya [at] example.com; cep: %s' % fmt_phone(B['ALI']['phone_nat'], 't_paren'),
     cons('CN18', 'email', 'ALI'), cons('CN3', 'phone', 'ALI'))
note('MEHMETOZ', "Şikayet kaydı #4471:\nMüşteri MEHMET ÖZTÜRK, ATM'de kartının sıkıştığını bildirdi.\nGeri arama numarası: %s"
     % fmt_phone(B['MEHMETOZ']['phone_nat'], 't_plus'), nocc('mehmet öztürk'), cons('CN4', 'phone', 'MEHMETOZ'))
note('ISIL', 'Vekaletname: vekil İSMAİL ŞAHİN (T.C. %s-%s-%s) adına düzenlendi. Müşteri IŞIL KILIÇ imzaladı.'
     % (ISMAIL_TCKN[:5], ISMAIL_TCKN[5:8], ISMAIL_TCKN[8:]), nocc('ismail şahin'), nocc('ışıl kılıç'))
note('CORP_Hatice', 'Firma sahibi Hatice Arslan aynı zamanda bireysel müşterimiz (%s). Muhasebe e-postası: HATICE.ARSLAN@EXAMPLE.COM'
     % B['HATICE']['musteri_no'], nocc('hatice arslan'), cons('CN14', 'mno', 'HATICE'), cons('CN16', 'email', 'HATICE'))
note('IBRAHIM', "Eşi Fatma Demir'in cep telefonu %s, acil durumda aranabilir." % fmt_phone(FATMA_PH, 't_dash'),
     nocc('fatma demir'))
note('MALIKAYA', 'Sn. KAYA MEHMET ALİ maaş müşterisi; maaşı IBAN %s üzerine yatıyor.' % spaced(A['MALIKAYA']['iban']).lower(),
     nocc('kaya mehmet ali'), cons('CN8', 'iban', 'MALIKAYA'))
note('HUSEYIN', 'Kardeşi Gülşen Çelik de müşterimiz (%s). WhatsApp hattı: %s' % (B['GULSEN']['musteri_no'], B['HUSEYIN']['phone_nat']),
     nocc('gülşen çelik'), cons('CN13', 'mno', 'GULSEN'), cons('CN5', 'phone', 'HUSEYIN'))
note('CORP_Kuzey', 'Yetkili: Sn. Barış Aksoy, tel %s. Kurumsal çağrı merkezi yönlendirmesi: Pusula Müşteri Hizmetleri 0850 724 00 00'
     % fmt_phone(BARIS_PH, 't_0090'), nocc('barış aksoy'))
note('ELIF', 'Annesi Sevim Demir ile şubeye geldi, ilk hesabını açtı.', nocc('sevim demir'))
note('GULSEN', 'E-posta adresi GULSEN.CELIK @ EXAMPLE.TEST olarak düzeltildi.', cons('CN17', 'email', 'GULSEN'))
note('CORP_Mustafa', 'Firma sahibi Mustafa Kurt, TCKN %s. Fatura no 40001234567 ile ilgili itiraz kaydı açıldı.' % KURT_TCKN,
     nocc('mustafa kurt'))
tk = B['HATICE']['tckn']
note('HATICE', 'Kimlik No: %s.%s.%s.%s (nüfus cüzdanı yenilendi)' % (tk[:3], tk[3:6], tk[6:9], tk[9:]), cons('CN2', 'tckn', 'HATICE'))
g = next(c for c in customers if c['musteri_tipi'] == 'BIREYSEL' and not c['tag'])
g['notlar'] = 'E-bülten aboneliği: %s' % g['eposta'].replace('@', '(at)')
GENERIC = ['Adres değişikliği talebi alındı.', 'Mobil bankacılık şifre sıfırlama yapıldı.', 'Kredi kartı limit artışı talep etti.',
           'Hesap özeti e-posta ile gönderilsin istedi.', 'Şube ziyareti - bilgi güncelleme.', 'Kampanya bilgilendirmesi istemiyor.',
           'Müşteri memnuniyeti anketine katıldı.']
for c in R.sample([c for c in customers if not c['notlar']], 26):
    c['notlar'] = 'Kurumsal internet bankacılığı yetki tanımı yapıldı.' if c['musteri_tipi'] == 'KURUMSAL' and R.random() < .5 \
        else R.choice(GENERIC)
for c in customers:
    if c['sirket_turu'] == 'SAHIS':
        c['truth'].append({'kind': 'name', 'phrase': ' '.join(c['unvan'].split()[:2]).replace('I', 'ı').replace('İ', 'i').lower(),
                           'col': 'unvan'})

# ---------------------------------------------------------------- balance fix-up + KMH negatives (trap T2)
def ordered(a):
    a['tx'].sort(key=lambda t: t['dt'])
    return a['tx']

for a in accounts:
    txs = ordered(a)
    assert txs[0]['acik'] == 'Hesap açılış yatırması' and txs[0]['dt'].date() == a['acilis'], a
    assert all(t['dt'].date() >= a['acilis'] and t['dt'].date() <= SNAP for t in txs)
    bal, low = Decimal(0), Decimal(0)
    for t in txs:
        bal += t['tutar']
        low = min(low, bal)
    if low < -a['limit']:
        txs[0]['tutar'] += ((-a['limit'] - low) / 100).to_integral_value(rounding='ROUND_CEILING') * 100 + 100
kmh_neg = []
for a in [a for a in accounts if a['turu'] == 'KMH' and a['cust']['tag'] not in SPECIAL][:4]:
    txs = ordered(a)
    bal = sum(t['tutar'] for t in txs)
    last = txs[-1]['dt']
    when = rtime(rdate(last.date() + dt.timedelta(days=1), SNAP)) if last.date() < SNAP else last + dt.timedelta(minutes=1)
    target = -(a['limit'] * Decimal(R.choice(['0.35', '0.6', '0.8']))).quantize(Decimal('0.01'))
    if bal - target < 10:
        continue
    tx(a, when, 'CEKME', bal - target, '', 'ATM para çekme')
    kmh_neg.append(a)
for a in accounts:
    bal = Decimal(0)
    for t in ordered(a):
        bal += t['tutar']
        assert bal >= -a['limit'], (a['iban'], bal)
    a['bakiye'] = bal
assert sum(1 for a in accounts if a['bakiye'] < 0) >= 4

# ---------------------------------------------------------------- write CSVs
customers.sort(key=lambda c: c['musteri_no'])
accounts.sort(key=lambda a: (a['sube'], a['hno']))
txs = sorted((t for a in accounts for t in a['tx']), key=lambda t: (t['dt'], t['acc']['sube'], t['acc']['hno'], t['tip']))
for i, t in enumerate(txs):
    t['id'] = str(7000001 + i)
cidx = {id(c): i for i, c in enumerate(customers)}
aidx = {id(a): i for i, a in enumerate(accounts)}
tidx = {id(t): i for i, t in enumerate(txs)}

def iso(d):
    return d.isoformat() if d else ''

M_COLS = 'musteri_no;musteri_tipi;tckn;vkn;ad;soyad;unvan;sirket_turu;dogum_tarihi;kurulus_tarihi;cinsiyet;il;ilce;eposta;telefon;kayit_tarihi;notlar'.split(';')
H_COLS = 'sube_kodu;hesap_no;musteri_no;hesap_turu;doviz;kmh_limiti;acilis_tarihi;iban;bakiye'.split(';')
I_COLS = 'islem_id;sube_kodu;hesap_no;islem_tarihi;islem_tipi;tutar;karsi_iban;aciklama'.split(';')
os.makedirs(OUT, exist_ok=True)

def write(name, cols, rows):
    with open(os.path.join(OUT, name), 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f, delimiter=';', lineterminator='\r\n')
        w.writerow(cols)
        w.writerows(rows)

write('musteri.csv', M_COLS, [[c['musteri_no'], c['musteri_tipi'], c['tckn'], c['vkn'], c['ad'], c['soyad'], c['unvan'],
                               c['sirket_turu'], c['dogum'].strftime('%d.%m.%Y') if c['dogum'] else '', iso(c['kurulus']),
                               c['cinsiyet'], c['il'], c['ilce'], c['eposta'], c['telefon'], iso(c['kayit']), c['notlar']]
                              for c in customers])
write('hesap.csv', H_COLS, [[a['sube'], a['hno'], a['cust']['musteri_no'], a['turu'], a['doviz'], str(a['limit']),
                             iso(a['acilis']), a['iban'], str(a['bakiye'])] for a in accounts])
write('islem.csv', I_COLS, [[t['id'], t['acc']['sube'], t['acc']['hno'], t['dt'].strftime('%d.%m.%Y %H:%M:%S'), t['tip'],
                             str(t['tutar']), t['karsi'], t['acik']] for t in txs])

# ---------------------------------------------------------------- truth
def norm_iban(s):
    return s.replace(' ', '').upper()

refrow = {'MALI2': ('hesap', aidx[id(MALI2)]), 'MALIKAYA': ('hesap', aidx[id(A['MALIKAYA'])])}
cons_list = {}

def add_occ(file, row, col, o):
    if o['kind'] == 'name':
        TRUTH['name_occ'].append({'file': file, 'row': row, 'col': o.get('col', col), 'phrase': o['phrase']})
        return
    cid = o['id']
    if o['ctype'] == 'iban_same':
        cons_list.setdefault(cid, {'id': cid, 'ctype': 'iban_same', 'bank': o['bank'], 'cells': []})['cells'].append([file, row, col])
    elif o['ctype'] == 'iban_textcol':
        cons_list[cid] = {'id': cid, 'ctype': 'iban_textcol', 'cell': [file, row, col], 'ref_cell': [file, row, 'karsi_iban']}
    elif o['ctype'] == 'iban':
        f2, r2 = refrow[o['ref']]
        cons_list[cid] = {'id': cid, 'ctype': 'iban', 'cell': [file, row, col], 'ref_cell': [f2, r2, 'iban']}
    else:
        colmap = {'tckn': 'tckn', 'phone': 'telefon', 'email': 'eposta', 'mno': 'musteri_no'}
        cons_list[cid] = {'id': cid, 'ctype': o['ctype'], 'cell': [file, row, col],
                          'ref_cell': ['musteri', cidx[id(B[o['ref']])], colmap[o['ctype']]]}

for c in customers:
    for o in c['truth']:
        add_occ('musteri', cidx[id(c)], 'notlar', o)
for t in txs:
    for o in t['truth']:
        col = 'karsi_iban' if o.get('ctype') == 'iban_same' else 'aciklama'
        add_occ('islem', tidx[id(t)], col, o)
TRUTH['consistency'] = [cons_list[k] for k in sorted(cons_list, key=lambda s: int(s[2:]))]
assert len(TRUTH['consistency']) == 18, sorted(cons_list)

def nat(p):
    d = ''.join(ch for ch in p if ch.isdigit())
    return d[-10:]

TRUTH['pii'] = {
    'tckn': sorted({c['tckn'] for c in customers if c['tckn']} | set(TRUTH['third_tckn'])),
    'phone_nat': sorted({nat(c['telefon']) for c in customers} | set(TRUTH['third_phone'])),
    'email': sorted({c['eposta'].lower() for c in customers}),
    'iban': sorted({a['iban'] for a in accounts} | {norm_iban(t['karsi']) for t in txs if t['karsi']} | set(TRUTH['extra_iban'])),
    'sahis_vkn': sorted(c['vkn'] for c in customers if c['sirket_turu'] == 'SAHIS'),
}
TRUTH['preserve_fragments'] = ['Kuzey Lojistik Ltd. Şti.', 'Yıldız Sitesi Yönetimi', 'Demir Çelik Sanayi A.Ş.',
                               'Fatura no 40001234567', 'Pusula Müşteri Hizmetleri 0850 724 00 00', '1.250,00 TL',
                               'Kaya Turizm ve Seyahat A.Ş.']
TRUTH['traps'] = {
    'T1_composite_dup_hesap_rows': [[aidx[id(x)], aidx[id(y)]] for x, y in dups],
    'T2_kmh_negative_hesap_rows': [aidx[id(a)] for a in accounts if a['bakiye'] < 0],
    'T3_feb29_musteri_rows': [cidx[id(B['ELIF'])], cidx[id(B['EMRE'])]],
    'T3_feb29_hesap_rows': [aidx[id(A['ELIF'])], aidx[id(A['EMRE'])]],
}
TRUTH['k_outlier_musteri_rows'] = sorted(cidx[id(c)] for c in customers if (c['tag'] or '').startswith('OUT_'))
TRUTH['counts'] = {'musteri': len(customers), 'hesap': len(accounts), 'islem': len(txs),
                   'bireysel': sum(c['musteri_tipi'] == 'BIREYSEL' for c in customers)}
TRUTH['mask_key'] = 'pusula-uat-2026'
with open(os.path.join(HERE, 'testdata2_truth.json'), 'w', encoding='utf-8') as f:
    json.dump(TRUTH, f, ensure_ascii=False, indent=1)
print('extract written to', os.path.abspath(OUT))
print(TRUTH['counts'], 'name_occ', len(TRUTH['name_occ']), 'cons', len(TRUTH['consistency']))
