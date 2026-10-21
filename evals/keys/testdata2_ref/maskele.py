#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Reference masker for trial-testdata2 (EVALUATOR-ONLY; proves full marks are reachable).
Usage: MASKE_ANAHTARI=... python maskele.py <input_dir> <output_dir>"""
import csv, datetime as dt, hashlib, hmac, io, os, re, sys
from collections import Counter

KEY = os.environ.get('MASKE_ANAHTARI')
if not KEY:
    sys.exit('MASKE_ANAHTARI is not set')
SRC, DST = sys.argv[1], sys.argv[2]


def H(*parts):
    return int.from_bytes(hmac.new(KEY.encode(), '|'.join(parts).encode('utf-8'), hashlib.sha256).digest(), 'big')

# ---------------------------------------------------------------- io
def read(name):
    with open(os.path.join(SRC, name), encoding='utf-8-sig', newline='') as f:
        rows = list(csv.reader(io.StringIO(f.read()), delimiter=';'))
    return rows[0], [dict(zip(rows[0], r)) for r in rows[1:]]


def write(name, head, rows):
    os.makedirs(DST, exist_ok=True)
    with open(os.path.join(DST, name), 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f, delimiter=';', lineterminator='\r\n')
        w.writerow(head)
        for r in rows:
            w.writerow([r[h] for h in head])

# ---------------------------------------------------------------- algorithms
def tckn_tail(d9):
    d10 = (sum(d9[0:9:2]) * 7 - sum(d9[1:8:2])) % 10
    return [d10, (sum(d9) + d10) % 10]


def tckn_valid(s):
    return len(s) == 11 and s.isdigit() and s[0] != '0' and [int(c) for c in s[9:]] == tckn_tail([int(c) for c in s[:9]])


def vkn_tail(d9):
    tot = 0
    for i in range(9):
        t = (d9[i] + 9 - i) % 10
        v = (t * 2 ** (9 - i)) % 9
        tot += 9 if (t and not v) else v
    return (10 - tot % 10) % 10


def iban_from(bank, acc16):
    bban = bank + '0' + acc16
    return 'TR%02d' % (98 - int(''.join(str(int(c, 36)) for c in bban + 'TR00')) % 97) + bban


def fold(s):  # 1:1 length Turkish-aware fold
    out = []
    for ch in s:
        ch = {'İ': 'i', 'I': 'ı'}.get(ch, ch).lower()[:1]
        out.append({'ç': 'c', 'ğ': 'g', 'ı': 'i', 'ö': 'o', 'ş': 's', 'ü': 'u', 'â': 'a'}.get(ch, ch))
    return ''.join(out)


def tr_upper(s):
    return s.replace('i', 'İ').replace('ı', 'I').upper()

# ---------------------------------------------------------------- deterministic maps
class Map:
    def __init__(self, gen):
        self.gen, self.m, self.used = gen, {}, set()

    def prime(self, values):
        for v in sorted(set(values)):
            self(v)

    def __call__(self, v):
        if v not in self.m:
            k = 0
            while True:
                c = self.gen(v, k)
                if c != v and c not in self.used:
                    break
                k += 1
            self.m[v] = c
            self.used.add(c)
        return self.m[v]


def g_tckn(v, k):
    n = H('tckn', v, str(k))
    d = [1 + n % 9] + [(n // 10 ** (i + 1)) % 10 for i in range(8)]
    return ''.join(map(str, d + tckn_tail(d)))


def g_vkn(v, k):
    n = H('vkn', v, str(k))
    d = [(n // 10 ** i) % 10 for i in range(9)]
    return ''.join(map(str, d)) + str(vkn_tail(d))


MNO = Map(lambda v, k: 'M%06d' % (H('mno', v, str(k)) % 1000000))
HNO = Map(lambda v, k: '%d%07d' % (1 + H('hno', v, str(k)) % 9, H('hno2', v, str(k)) % 10 ** 7))
TCKN, VKN = Map(g_tckn), Map(g_vkn)
EMAIL = Map(lambda v, k: 'k%010x@example.test' % (H('mail', v, str(k)) % 16 ** 10))
PHONE = Map(lambda v, k: (v[0] if v[0] == '5' else v[:3]) + ('%09d' % (H('tel', v, str(k)) % 10 ** 9))[: 10 - (1 if v[0] == '5' else 3)])
EXT = {}
FEM = ('Aylin Berrin Canan Damla Esin Figen Gonca Hande Jale Lerzan Mine Nevin Oya Pelin Reyhan Sevda Tijen Ülkü '
       'Vildan Yeliz Zerrin Bahar Didem Eda').split()
MAL = ('Alper Bora Cihan Doruk Ferit Görkem Haluk İlhan Kerem Lütfü Metin Necati Oğuz Rüştü Sarp Tamer Ufuk Vedat '
       'Yalçın Zafer Atilla Bekir Cemal Ersin').split()
SUR = ('Akgül Başaran Cansever Dinçer Ergün Fidan Gürsoy Hızal Irmak Kalkan Lale Mert Nalbant Okyay Pamir Rüzgar '
       'Sağlam Tanrıverdi Ulus Vural Yalaz Zorlu Akyol Bilgin Çınar Demirtaş Elmas Gündüz Karahan Ozan').split()
class NameMap(dict):
    def __init__(self, tag, pool):
        super().__init__()
        self.tag, self.pool = tag, pool

    def __call__(self, v):
        if v not in self:
            k = 0
            while fold(self.pool[(H(self.tag, v) + k) % len(self.pool)]) == v:
                k += 1
            self[v] = self.pool[(H(self.tag, v) + k) % len(self.pool)]
        return self[v]


FIRST, LAST = NameMap('fn', FEM + MAL), NameMap('ln', SUR)


def map_iban(raw):
    n = re.sub(r'[\s-]', '', raw).upper()
    bank = n[4:9]
    if bank == '00990' and n[14:18] == '0000':
        return iban_from('00990', n[10:14] + '0000' + HNO(n[18:26]))
    if n not in EXT:
        EXT[n] = iban_from(bank, '%016d' % (H('iban', n) % 10 ** 16))
    return EXT[n]


def styled_iban(raw, new):
    out = ' '.join(new[i:i + 4] for i in range(0, 26, 4)) if ' ' in raw.strip() else new
    return out.lower() if raw[:2] == 'tr' else out


def phone_nat(d):
    if d.startswith('0090'):
        return d[4:]
    if len(d) == 12 and d.startswith('90'):
        return d[2:]
    if len(d) == 11 and d.startswith('0'):
        return d[1:]
    return d


def reskin(s, newdigits):  # put new digits into the old skeleton, right-aligned
    out, nd = list(s), list(newdigits)
    for i in range(len(out) - 1, -1, -1):
        if out[i].isdigit() and nd:
            out[i] = nd.pop()
    return ''.join(out)


def mask_phone(s):
    d = re.sub(r'\D', '', s)
    nat = phone_nat(d)
    return reskin(s, PHONE(nat))


# ---------------------------------------------------------------- load
MH, M = read('musteri.csv')
HH, A = read('hesap.csv')
IH, T = read('islem.csv')
MNO.prime(r['musteri_no'] for r in M)
HNO.prime(r['hesap_no'] for r in A)
TCKN.prime(r['tckn'] for r in M if r['tckn'])
EMAIL.prime(r['eposta'].lower() for r in M)
PROTECT = sorted({r['unvan'] for r in M if r['sirket_turu'] in ('AS', 'LTD')} |
                 {'Yıldız Sitesi Yönetimi', 'Pusula Müşteri Hizmetleri'}, key=len, reverse=True)
KNOWN_FIRST = {fold(t) for r in M for t in r['ad'].split()} | {fold(x) for x in (
    'Ahmet Mehmet Mustafa Ali Hüseyin Hasan İbrahim İsmail Fatma Ayşe Emine Hatice Zeynep Elif Barış Sevim Özge '
    'Recep Gülşen Işıl Emre Yusuf Murat Ömer Osman Merve Esra Ebru Derya Kemal Can Nur Naz').split()}
SURN_OK = re.compile(r"^[A-ZÇĞİÖŞÜ][a-zçğıöşüA-ZÇĞİÖŞÜ]+$")
STOP = {fold(x) for x in 'Tekstil Oto Kırtasiye Nakliyat Hanım Bey A.Ş. Ltd. Şti. Sanayi Market'.split()}

# ---------------------------------------------------------------- free-text masking
IBAN_RX = re.compile(r'(?i)\btr\d{2}(?:[ -]?\d){22}\b')
NUM_RX = re.compile(r'(?<![\w-])\+?\(?\d[\d ().-]{7,}\d(?![\w-])')
MNO_RX = re.compile(r'\bM\d{6}\b')
MAIL_RX = re.compile(r'(?i)([a-z0-9._%+-]+)\s*(?:@|\[at\]|\(at\))\s*([a-z0-9-]+(?:\.[a-z0-9-]+)+)')


def mask_names(s):
    if not s:
        return s
    f = fold(s)
    blocked = [False] * len(s)
    for p in PROTECT:
        for mt in re.finditer(re.escape(fold(p)), f):
            for x in range(mt.start(), mt.end()):
                blocked[x] = True
    toks = [(mt.start(), mt.end()) for mt in re.finditer(r"[A-Za-zÇĞİÖŞÜçğıöşüâ]+", s)]
    W = lambda k: s[toks[k][0]:toks[k][1]]
    isfirst = lambda k: fold(W(k)) in KNOWN_FIRST and W(k)[0].isupper()
    sp = lambda k: s[toks[k][1]:toks[k + 1][0]] == ' '
    out, last, i = [], 0, 0
    while i < len(toks):
        span, j = None, i
        while j < len(toks) and isfirst(j) and (j == i or sp(j - 1)):
            j += 1
        if j > i and j < len(toks) and sp(j - 1) and SURN_OK.match(W(j)) and fold(W(j)) not in STOP:
            span = (i, j + 1, 'fwd')
        elif j == i and len(W(i)) > 1 and W(i).isupper() and fold(W(i)) not in STOP:
            k = i + 1
            while k < len(toks) and sp(k - 1) and isfirst(k) and W(k).isupper():
                k += 1
            if k > i + 1:
                span = (i, k, 'rev')
        if span:
            a, b, kind = span
            st, en = toks[a][0], toks[b - 1][1]
            if not any(blocked[st:en]):
                words = [W(x) for x in range(a, b)]
                if kind == 'fwd':
                    new = [FIRST(fold(w)) for w in words[:-1]] + [LAST(fold(words[-1]))]
                else:
                    new = [LAST(fold(words[0]))] + [FIRST(fold(w)) for w in words[1:]]
                new = ' '.join(new)
                if s[st:en].isupper():
                    new = tr_upper(new)
                out.append(s[last:st] + new)
                last, i = en, b
                continue
        i += 1
    out.append(s[last:])
    return ''.join(out)


def mask_text(s):
    if not s:
        return s
    s = IBAN_RX.sub(lambda mt: styled_iban(mt.group(0), map_iban(mt.group(0))), s)

    def mail(mt):
        e = (mt.group(1) + '@' + mt.group(2)).lower()
        return EMAIL(e)
    s = MAIL_RX.sub(mail, s)
    s = MNO_RX.sub(lambda mt: MNO(mt.group(0)) if mt.group(0) in MNO.m else mt.group(0), s)

    def num(mt):
        t = mt.group(0)
        d = re.sub(r'\D', '', t)
        if len(d) == 11 and d[0] != '0':
            return reskin(t, TCKN(d)) if tckn_valid(d) else t
        nat = phone_nat(d)
        if len(nat) == 10 and nat[0] in '5' or (len(nat) == 10 and nat[0] in '234' and len(d) > 10):
            return reskin(t, PHONE(nat))
        return t
    s = NUM_RX.sub(num, s)
    return mask_names(s)

# ---------------------------------------------------------------- dates / k-anonymity
OFF = -(30 + H('offset') % 336)


def shift(v, fmt):
    return (dt.datetime.strptime(v, fmt) + dt.timedelta(days=OFF)).strftime(fmt) if v else v


def decade(v):
    y = int(v[-4:]) // 10 * 10
    return '%d-%d' % (y, y + 9)


cls = Counter((decade(r['dogum_tarihi']), r['il'], r['cinsiyet']) for r in M if r['musteri_tipi'] == 'BIREYSEL')

# ---------------------------------------------------------------- mask rows
for r in M:
    o = dict(r)
    r['musteri_no'] = MNO(o['musteri_no'])
    if o['tckn']:
        r['tckn'] = TCKN(o['tckn'])
    if o['sirket_turu'] == 'SAHIS':
        r['vkn'] = VKN(o['vkn'])
        r['unvan'] = mask_names(o['unvan'])
    if o['ad']:
        r['ad'] = ' '.join(FIRST(fold(t)) for t in o['ad'].split())
        r['soyad'] = LAST(fold(o['soyad']))
    if o['musteri_tipi'] == 'BIREYSEL':
        q = (decade(o['dogum_tarihi']), o['il'], o['cinsiyet'])
        if cls[q] >= 5:
            r['dogum_tarihi'], r['ilce'] = q[0], '*'
        else:
            r['dogum_tarihi'] = r['il'] = r['ilce'] = r['cinsiyet'] = '*'
    r['eposta'] = EMAIL(o['eposta'].lower())
    r['telefon'] = mask_phone(o['telefon'])
    r['kayit_tarihi'] = shift(o['kayit_tarihi'], '%Y-%m-%d')
    r['kurulus_tarihi'] = shift(o['kurulus_tarihi'], '%Y-%m-%d')
    r['notlar'] = mask_text(o['notlar'])
for r in A:
    o = dict(r)
    r['musteri_no'] = MNO(o['musteri_no'])
    r['hesap_no'] = HNO(o['hesap_no'])
    r['iban'] = iban_from('00990', o['sube_kodu'] + '0000' + r['hesap_no'])
    r['acilis_tarihi'] = shift(o['acilis_tarihi'], '%Y-%m-%d')
for r in T:
    o = dict(r)
    r['hesap_no'] = HNO(o['hesap_no'])
    r['islem_tarihi'] = shift(o['islem_tarihi'], '%d.%m.%Y %H:%M:%S')
    if o['karsi_iban']:
        r['karsi_iban'] = styled_iban(o['karsi_iban'], map_iban(o['karsi_iban']))
    r['aciklama'] = mask_text(o['aciklama'])
write('musteri.csv', MH, M)
write('hesap.csv', HH, A)
write('islem.csv', IH, T)
