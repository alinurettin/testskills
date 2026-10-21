#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Reference generator for trial-testdata2 Part 1 (EVALUATOR-ONLY; proves full marks are reachable).
Usage: python uret.py <output_dir> [seed]"""
import csv, datetime as dt, os, random, sys
from decimal import Decimal

OUT = sys.argv[1]
R = random.Random(int(sys.argv[2]) if len(sys.argv) > 2 else 42)
SNAP = dt.date(2026, 9, 30)
D2 = Decimal('0.01')
ILCE = {'İstanbul': ['Kadıköy', 'Beşiktaş', 'Üsküdar', 'Şişli', 'Bakırköy', 'Ataşehir'],
        'Ankara': ['Çankaya', 'Keçiören', 'Yenimahalle', 'Etimesgut'], 'İzmir': ['Konak', 'Bornova', 'Karşıyaka', 'Buca'],
        'Bursa': ['Nilüfer', 'Osmangazi'], 'Adana': ['Seyhan', 'Çukurova'], 'Trabzon': ['Ortahisar'],
        'Şanlıurfa': ['Halfeti', 'Haliliye'], 'Bayburt': ['Merkez']}
SUBE = ['0101', '0102', '0103', '0207', '0208', '0315', '0316', '0420', '0512', '0611']
FN = {'E': 'Arda Bora Cem Deniz Efe Kaan Mert Ozan Selim Tuna Umut Yusuf Barış Onur Kerem'.split(),
      'K': 'Ada Bade Ceren Duru Ela Ezgi İpek Lale Melis Nehir Sena Yağmur Zeren Ilgın Öykü'.split()}
LN = 'Akgün Balcı Cengiz Dalkılıç Erol Fırat Gezer Halıcı Işıklar Kaynak Laçin Metin Nalçacı Oktay Sevinç Tuna Ünsal Yalın'.split()
ASCII = str.maketrans('çğıöşüÇĞİÖŞÜ', 'cgiosuCGIOSU')


def leap(y):
    return y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)


def b18(d):
    return dt.date(d.year + 18, 3, 1) if (d.month, d.day) == (2, 29) and not leap(d.year + 18) else d.replace(year=d.year + 18)


def rdate(a, b):
    return a + dt.timedelta(days=R.randint(0, max(0, (b - a).days)))


def tckn():
    d = [R.randint(1, 9)] + [R.randint(0, 9) for _ in range(8)]
    d10 = (sum(d[0:9:2]) * 7 - sum(d[1:8:2])) % 10
    return ''.join(map(str, d + [d10, (sum(d) + d10) % 10]))


def vkn():
    d = [R.randint(0, 9) for _ in range(9)]
    tot = 0
    for i in range(9):
        t = (d[i] + 9 - i) % 10
        v = (t * 2 ** (9 - i)) % 9
        tot += 9 if (t and not v) else v
    return ''.join(map(str, d)) + str((10 - tot % 10) % 10)


def iban(bank, acc16):
    bban = bank + '0' + acc16
    return 'TR%02d' % (98 - int(''.join(str(int(c, 36)) for c in bban + 'TR00')) % 97) + bban


def uniq(fn, used):
    while True:
        v = fn()
        if v not in used:
            used.add(v)
            return v


used = set()
C = []
for i in range(180):
    ind = i < 120
    il = R.choice(sorted(ILCE))
    c = dict(musteri_no='M%06d' % (100001 + i), musteri_tipi='BIREYSEL' if ind else 'KURUMSAL', il=il, ilce=R.choice(ILCE[il]),
             eposta='musteri%03d@example.%s' % (i + 1, R.choice(['com', 'test'])),
             telefon=uniq(lambda: '+90 500 %03d %02d %02d' % (R.randint(0, 999), R.randint(0, 99), R.randint(0, 99)), used))
    if ind:
        sex = R.choice('EK')
        dob = rdate(dt.date(1930, 1, 1), dt.date(2008, 6, 30))
        if i < 3:
            dob = dt.date(2000 + 4 * i, 2, 29)            # SD-2: 18th birthday = 1 March
        elif i < 7:
            dob = rdate(dt.date(1988, 1, 1), dt.date(2007, 12, 31))
        c.update(tckn=uniq(tckn, used), vkn='', ad=R.choice(FN[sex]), soyad=R.choice(LN), unvan='', sirket_turu='',
                 dob=dob, kur=None, cinsiyet=sex)
        lo = max(b18(dob), dt.date(2005, 1, 1))
        c['kayit'] = lo if i < 7 else rdate(lo, SNAP - dt.timedelta(days=60))
        c['sd1'] = i < 7
    else:
        kur = rdate(dt.date(1950, 1, 1), dt.date(2025, 12, 31))
        if i < 124:
            kur = rdate(dt.date(2005, 1, 1), dt.date(2025, 12, 31))
        c.update(tckn='', vkn=uniq(vkn, used), ad='', soyad='', unvan='Deneme %s %s A.Ş.' % (R.choice(LN), i),
                 sirket_turu=R.choice(['AS', 'LTD', 'SAHIS']), dob=None, kur=kur, cinsiyet='')
        c['kayit'] = kur if i < 124 else rdate(max(kur, dt.date(2005, 1, 1)), SNAP - dt.timedelta(days=60))
        c['sd3'] = i < 124
    C.append(c)

A = []
hused = set()
for c in C:
    n = R.choice([1, 2, 2, 3])
    for k in range(n):
        ind = c['musteri_tipi'] == 'BIREYSEL'
        kmh = ind and k == 1 and R.random() < 0.5
        ac = c['kayit'] if k == 0 and (c.get('sd1') or c.get('sd3')) else rdate(c['kayit'], SNAP - dt.timedelta(days=10))
        A.append(dict(sube=R.choice(SUBE), hno=uniq(lambda: str(R.randint(10000000, 99999999)), hused), c=c,
                      turu='KMH' if kmh else 'VADESIZ', doviz='TRY' if (kmh or k == 0) else R.choice(['TRY', 'USD', 'EUR']),
                      lim=Decimal(R.choice([2000, 5000, 10000, 25000])) if kmh else Decimal(0), acilis=ac, bal=Decimal(0)))
for x, y in [(A[10], A[20]), (A[30], A[40]), (A[50], A[60])]:   # İK-12 composite key
    if x['sube'] == y['sube']:
        y['sube'] = SUBE[(SUBE.index(x['sube']) + 1) % len(SUBE)]
    y['hno'] = x['hno']
assert len({(a['sube'], a['hno']) for a in A}) == len(A)
for a in A:
    a['iban'] = iban('00990', a['sube'] + '0000' + a['hno'])

T = []
ext = lambda: iban('0099%d' % R.randint(1, 8), '%016d' % R.randint(0, 10 ** 16 - 1))


def add(a, d, tip, amt, karsi='', acik=''):
    a['bal'] += amt
    T.append(dict(id=len(T) + 1, a=a, d=d, tip=tip, amt=amt, karsi=karsi, acik=acik))


events = [(a['acilis'], 0, i) for i, a in enumerate(A)] + \
         [(rdate(a['acilis'], SNAP), 1, i) for _ in range(7) for i, a in enumerate(A)]
events.sort()
for d, kind, i in events:
    a = A[i]
    if kind == 0:
        add(a, d, 'YATIRMA', Decimal(R.randint(20, 200) * 100), acik='Açılış yatırması')
        continue
    room = a['bal'] + a['lim']
    tip = R.choices(['YATIRMA', 'HAVALE_GELEN', 'FAIZ', 'CEKME', 'HAVALE_GIDEN', 'MASRAF'], [15, 15, 5, 25, 30, 10])[0]
    if tip in ('CEKME', 'HAVALE_GIDEN', 'MASRAF') and room < 10:
        tip = 'YATIRMA'
    amt = (Decimal(R.randint(100, 500000)) / 100).quantize(D2)
    if tip in ('CEKME', 'HAVALE_GIDEN', 'MASRAF'):
        amt = min(amt, (room * Decimal('0.8')).quantize(D2))
        if tip == 'HAVALE_GIDEN' and a['doviz'] == 'TRY' and R.random() < 0.5:
            dsts = [b for b in A if b is not a and b['doviz'] == 'TRY' and b['acilis'] <= d]
            if dsts:
                b = R.choice(dsts)
                add(a, d, 'HAVALE_GIDEN', -amt, b['iban'], 'İç transfer')
                add(b, d, 'HAVALE_GELEN', amt, a['iban'], 'İç transfer')
                continue
        add(a, d, tip, -amt, ext() if tip == 'HAVALE_GIDEN' else '', 'Çıkış')
    else:
        add(a, d, tip, amt, ext() if tip == 'HAVALE_GELEN' else '', 'Giriş')
vz = [a for a in A if a['turu'] == 'VADESIZ' and a['bal'] > 0][:6]
km = [a for a in A if a['turu'] == 'KMH' and a['bal'] + a['lim'] > 0][:4]
for a in vz:                          # SD-6 + SD-5
    add(a, SNAP, 'CEKME', -a['bal'], acik='Sınır: sıfır bakiye')
for a in km:                          # SD-7
    add(a, SNAP, 'CEKME', -(a['bal'] + a['lim']), acik='Sınır: KMH limiti')

os.makedirs(OUT, exist_ok=True)


def w(name, head, rows):
    with open(os.path.join(OUT, name), 'w', encoding='utf-8', newline='') as f:
        wr = csv.writer(f, delimiter=';', lineterminator='\n')
        wr.writerow(head.split(';'))
        wr.writerows(rows)


iso = lambda d: d.isoformat() if d else ''
w('musteri.csv', 'musteri_no;musteri_tipi;tckn;vkn;ad;soyad;unvan;sirket_turu;dogum_tarihi;kurulus_tarihi;cinsiyet;il;ilce;eposta;telefon;kayit_tarihi',
  [[c['musteri_no'], c['musteri_tipi'], c['tckn'], c['vkn'], c['ad'], c['soyad'], c['unvan'], c['sirket_turu'], iso(c['dob']),
    iso(c['kur']), c['cinsiyet'], c['il'], c['ilce'], c['eposta'], c['telefon'], iso(c['kayit'])] for c in C])
w('hesap.csv', 'sube_kodu;hesap_no;musteri_no;hesap_turu;doviz;kmh_limiti;acilis_tarihi;iban;bakiye',
  [[a['sube'], a['hno'], a['c']['musteri_no'], a['turu'], a['doviz'], '%.2f' % a['lim'], iso(a['acilis']), a['iban'],
    '%.2f' % a['bal']] for a in A])
w('islem.csv', 'islem_id;sube_kodu;hesap_no;islem_tarihi;islem_tipi;tutar;karsi_iban;aciklama',
  [[t['id'], t['a']['sube'], t['a']['hno'], iso(t['d']), t['tip'], '%.2f' % t['amt'], t['karsi'], t['acik']] for t in T])
print(len(C), len(A), len(T))
