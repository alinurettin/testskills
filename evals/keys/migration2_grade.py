#!/usr/bin/env python3
"""EVALUATOR-ONLY assistive grader for evals/trial-migration2.

Reads an agent's deliverables and SUGGESTS a score against keys/migration2.md.
It matches findings by the legacy keys they list (POL_NO, POL_NO/TAKSIT_NO) plus
keyword cues; a human grader must confirm every suggestion with the acceptance rules
in migration2.md (the suggestions are deliberately conservative on partial credit).

Usage:
  python migration2_grade.py <agent_workdir> [--run-script]
    <agent_workdir> contains cikti/bulgular.csv, cikti/mutabakat_raporu.md and
    cikti/mutabakat.py|.js, plus the inputs/ folder the agent worked on.
    --run-script  also executes the agent's reconciliation script (60 s timeout).
Python 3 stdlib only.
"""
import csv
import io
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = json.load(open(os.path.join(HERE, 'migration2_expected.json'), encoding='utf-8'))
KEY_RE = re.compile(r'(?<!\d)(4125\d{6})(?:\s*/\s*(\d{1,2}))?(?!\d)')


def norm(s):
    return (s or '').casefold()


def parse_keys(text):
    pols, insts = set(), set()
    for m in KEY_RE.finditer(text or ''):
        pols.add(m.group(1))
        if m.group(2):
            insts.add(f'{m.group(1)}/{int(m.group(2))}')
    return pols, insts


def load_findings(workdir):
    path = os.path.join(workdir, 'cikti', 'bulgular.csv')
    if not os.path.exists(path):
        return None
    raw = open(path, 'rb').read().decode('utf-8-sig', errors='replace')
    first = raw.splitlines()[0] if raw.strip() else ''
    delim = ';' if first.count(';') > first.count(',') else ','
    rows = list(csv.DictReader(io.StringIO(raw), delimiter=delim))
    out = []
    for r in rows:
        r = {norm(k).strip(): (v or '') for k, v in r.items() if k}
        text = ' '.join(r.get(c, '') for c in ('baslik', 'alan', 'varlik'))
        pols, insts = parse_keys(r.get('etkilenen_kayitlar', '') + ' ' + text)
        out.append({'id': r.get('bulgu_id', '?'), 'title': r.get('baslik', ''), 'text': norm(text),
                    'pols': pols, 'insts': insts, 'sev': r.get('onem', '')})
    return out


E = EXP
K = {
    'K1': dict(pts=2, pols=set(E['K1_status_S_to_SUSPENDED']),
               kw=r'suspended|expired|status|durum', need=r'suspended|expired|süresi dol'),
    'K2': dict(pts=2, pols=set(E['K2_address_truncated_50']),
               kw=r'address|adres', need=r'kırp|kes|trunc|kısal|50|eksik|yarım'),
    'K3': dict(pts=2, pols=set(E['K3_cancel_date_1900']), kw=r'cancel|iptal', need=r'1900|null|varsayılan|default|sentinel'),
    'K4': dict(pts=3, pols=set(E['K4_loss_payee_transliterated']),
               kw=r'loss_payee|dain|mürtehin|lehtar', need=r'türkçe|karakter|translit|ascii|ş|ı|harf'),
    'K5': dict(pts=3, pols=set(E['K5_missing_parent']['policy']),
               insts=set(E['K5_missing_parent']['orphan_installments']),
               kw=r'eksik|missing|yok|bulunm|taşınma|orphan|yetim|fk|yabancı anahtar|referans',
               need=r'eksik|missing|yok|bulunm|taşınma|orphan|yetim|fk|yabancı anahtar|referans'),
    'K6': dict(pts=3, pols=set(E['K6_lost_installments_ge10']['policies']),
               insts=set(E['K6_lost_installments_ge10']['installments']),
               kw=r'taksit|installment', need=r'eksik|missing|kayıp|lost|10|taşınma|bulunm|yok'),
    'K7': dict(pts=3, pols={k.split('/')[0] for k in E['K7_duplicate_installments_rerun']},
               insts=set(E['K7_duplicate_installments_rerun']),
               kw=r'taksit|installment', need=r'mükerrer|duplicate|çift|tekrar|r2|yeniden|benzersiz|unique|iki kez'),
    'K8': dict(pts=4, pols=set(E['K8_refund_sign_lost']['policies']),
               insts=set(E['K8_refund_sign_lost']['installments']),
               kw=r'iade|refund|tutar|amount|toplam|gross', need=r'işaret|negatif|eksi|sign|pozitif|-'),
    'K9': dict(pts=4, pols=set(E['K9_agency_A04_A09_swapped']['A04'] + E['K9_agency_A04_A09_swapped']['A09']),
               kw=r'acente|agency|acn-35|a04|a09', need=r'acn-3501|acn-3502|a04|a09|ters|yer değiş|swap|karış|yanlış'),
    'K10': dict(pts=4, pols={k.split('/')[0] for k in E['K10_late_flag_utc_date']},
                insts=set(E['K10_late_flag_utc_date']),
                kw=r'payment_status|paid_late|paid_on_time|gecik|late|ödeme durumu', need=r'paid_late|gecik|late'),
    'K11': dict(pts=4, pols=set(E['K11_fx_rate_rounded']),
                kw=r'fx_rate|kur|premium_try|try karşılığı', need=r'yuvarla|round|ondalık|decimal|hassas|premium_try|fx_rate|kur'),
}
TRAPS = {
    'T1': dict(pols=set(E['T1_utc_shift_crosses_midnight']['policies']),
               insts=set(E['T1_utc_shift_crosses_midnight']['installments']),
               kw=r'updated_at|paid_at|saat|utc|zaman dilimi|timezone|time zone|kayma|shift'),
    'T2': dict(pols=set(E['T2_quotes_not_migrated']['policies']),
               insts=set(E['T2_quotes_not_migrated']['installments']), kw=r'.'),
    'T3': dict(pols=set(E['T3_empty_currency_to_TRY']), kw=r'doviz|döviz|currency|para birimi|fx_rate|kur'),
    'T4': dict(pols=set(), kw=r'end_date|bitiş|bit_tar'),
}


def overlap(f, spec):
    p = len(f['pols'] & spec.get('pols', set()))
    i = len(f['insts'] & spec.get('insts', set()))
    return p, i


def match_k(f, kid, spec):
    p, i = overlap(f, spec)
    kw = re.search(spec['kw'], f['text'])
    need = re.search(spec['need'], f['text'])
    special = False
    if kid == 'K9' and re.search(r'acn-3501|acn-3502|\ba04\b|\ba09\b', f['text']):
        special = True
    if kid == 'K3' and '1900' in f['text']:
        special = True
    if kid == 'K1' and 'suspended' in f['text']:
        special = True
    hit = (p or i or special) and kw and need
    return bool(hit), p, i


def suggest(findings):
    sug = {}
    for kid, spec in K.items():
        best = None
        for f in findings:
            hit, p, i = match_k(f, kid, spec)
            if hit:
                score = spec['pts']
                note = f"{f['id']}: {f['title'][:70]} (keys pol={p} inst={i})"
                if kid == 'K5' and not (f['insts'] & spec['insts'] or re.search(r'orphan|yetim|fk|yabancı', f['text'])):
                    score, note = 2, note + ' [no orphan mention -> partial?]'
                if kid == 'K5' and f['pols'] & TRAPS['T2']['pols']:
                    score, note = 1, note + ' [lumped with quotes -> 1 pt, T2 applies]'
                if kid == 'K8' and not re.search(spec['need'], f['text']):
                    score = 2
                if kid == 'K6' and len(f['pols'] & spec['pols']) < 2 and not re.search(r'10|≥ ?10|>= ?10', f['text']):
                    score, note = 2, note + ' [one policy only?]'
                if best is None or score > best[0]:
                    best = (score, note)
        # partial-credit fallbacks (sum / total mismatch only)
        if best is None and kid in ('K6', 'K8'):
            for f in findings:
                if len(f['pols'] & spec['pols']) >= (2 if kid == 'K8' else 1) and \
                        re.search(r'toplam|sum|σ|m4|gross_premium|installment_count|sayı', f['text']):
                    best = (2 if kid == 'K8' else 1, f"{f['id']}: {f['title'][:70]} [sum/count mismatch only -> partial]")
                    break
        if best is None and kid == 'K9':
            for f in findings:
                if re.search(r'acente|agency', f['text']) and re.search(r'toplam|total|m6', f['text']):
                    best = (2, f"{f['id']}: {f['title'][:70]} [agency total mismatch only -> partial?]")
                    break
        sug[kid] = best or (0, '-')
    return sug


def traps(findings, claimed):
    flags = []
    for f in findings:
        for tid, spec in TRAPS.items():
            if f['id'] in claimed and tid != 'T2':
                continue
            p, i = overlap(f, spec)
            if tid == 'T2' and (p or i or re.search(r'teklif|quote|\bb\b', f['text'])):
                flags.append((tid, f))
            elif tid == 'T4' and re.search(spec['kw'], f['text']):
                flags.append((tid, f))
            elif tid == 'T1' and re.search(spec['kw'], f['text']) and not re.search(r'paid_late|payment_status|gecik', f['text']):
                flags.append((tid, f))
            elif tid == 'T3' and re.search(spec['kw'], f['text']) and (p or re.search(r'boş|empty|null|varsayılan|default', f['text'])) \
                    and not re.search(r'fx_rate.*yuvarla|round|premium_try', f['text']):
                flags.append((tid, f))
    return flags


def report_checks(workdir):
    path = os.path.join(workdir, 'cikti', 'mutabakat_raporu.md')
    if not os.path.exists(path):
        return None, {}
    txt = open(path, encoding='utf-8', errors='replace').read()
    t = norm(txt)
    info = {
        'mentions 60 in-scope policies': bool(re.search(r'\b60\b', t)),
        'mentions 234 in-scope installments': bool(re.search(r'\b234\b', t)),
        'mentions quotes excluded': bool(re.search(r'teklif', t)),
        'recommends NO-GO': bool(re.search(r'no[- ]?go|geçilmemeli|geçiş yapılmamalı|onay verilmemeli|ertelen|uygun değil|hazır değil', t)),
    }
    return txt, info


def run_script(workdir):
    for name, cmd in (('mutabakat.py', [sys.executable, os.path.join('cikti', 'mutabakat.py')]),
                      ('mutabakat.js', ['node', os.path.join('cikti', 'mutabakat.js')])):
        if os.path.exists(os.path.join(workdir, 'cikti', name)):
            try:
                cp = subprocess.run(cmd, cwd=workdir, capture_output=True, timeout=60)
                out = cp.stdout.decode('utf-8', errors='replace')
                return name, cp.returncode, len(out.splitlines())
            except Exception as e:  # noqa: BLE001
                return name, 'error: %s' % e, 0
    return None, None, 0


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    wd = sys.argv[1]
    findings = load_findings(wd)
    txt, info = report_checks(wd)
    print('=' * 78)
    print('trial-migration2 assistive grading for', os.path.abspath(wd))
    print('=' * 78)
    if findings is None:
        print('cikti/bulgular.csv MISSING -> grade manually from the report (keyword scan below)')
        findings = []
        if txt:
            for para in re.split(r'\n\s*\n', txt):
                pols, insts = parse_keys(para)
                findings.append({'id': 'rapor', 'title': para.strip().splitlines()[0][:80] if para.strip() else '',
                                 'text': norm(para), 'pols': pols, 'insts': insts, 'sev': ''})
    else:
        print(f'{len(findings)} findings in bulgular.csv')
    sug = suggest(findings)
    claimed = set()
    for kid, (s, note) in sug.items():
        if s and note != '-':
            claimed.add(note.split(':')[0])
    total = 0
    print('\nPlanted items (suggested points / max) - CONFIRM MANUALLY')
    for kid, (s, note) in sug.items():
        total += s
        print(f'  {kid:4} {s}/{K[kid]["pts"]}  {note}')
    tflags = traps(findings, claimed)
    print('\nPossible trap hits (-2 each if the finding really claims a defect):')
    for tid, f in tflags:
        print(f'  {tid}: {f["id"]} {f["title"][:80]}')
    if not tflags:
        print('  none detected')
    unmatched = [f for f in findings if f['id'] not in claimed and f['id'] not in {x[1]['id'] for x in tflags}]
    print('\nUnmatched findings (review: valid-but-unkeyed, duplicate of a K, or false positive -1):')
    for f in unmatched:
        print(f'  {f["id"]}: {f["title"][:90]}')
    if not unmatched:
        print('  none')
    print('\nMethod checks:')
    for k, v in info.items():
        print(f'  {k}: {v}')
    if '--run-script' in sys.argv:
        name, rc, lines = run_script(wd)
        print(f'  script: {name} exit={rc} stdout_lines={lines}')
    else:
        print('  script present:', any(os.path.exists(os.path.join(wd, 'cikti', n)) for n in ('mutabakat.py', 'mutabakat.js')),
              '(use --run-script to execute)')
    print(f'\nSuggested planted-item subtotal: {total}/34 (before trap/FP penalties and method points 0-4; max 38)')


if __name__ == '__main__':
    main()
