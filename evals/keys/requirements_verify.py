#!/usr/bin/env python3
"""Integrity check for trial-requirements (EVALUATOR ONLY).

Verifies that the trial inputs parse and still contain every planted item
K1..K12 and every trap T1..T4 described in requirements.md.
Python 3 standard library only.  Usage:

    python requirements_verify.py [path-to-trial-requirements-folder]

Exit code 0 = all checks passed.
"""
import csv
import datetime as dt
import io
import re
import sys
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent
TRIAL = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE.parent / "trial-requirements"
PRD = TRIAL / "girdiler" / "PRD-Kolay-Iade-v1.3.md"
CSV = TRIAL / "girdiler" / "Ek-B-kategori-iade-kurallari.csv"
TASK = TRIAL / "TASK.md"
RUN = TRIAL / "RUN.md"

results = []


def check(label, cond, detail=""):
    results.append((label, bool(cond), detail))


def money(s):
    """'3.996,50' -> Decimal('3996.50')"""
    return Decimal(s.replace(".", "").replace(",", ".").replace("−", "-").strip())


def q2(x):
    return x.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


# ------------------------------------------------------------------ files
for p in (PRD, CSV, TASK, RUN):
    check(f"file exists: {p.name}", p.is_file(), str(p))
if not all(ok for _, ok, _ in results):
    for label, ok, detail in results:
        print(("PASS " if ok else "FAIL ") + label + ("  " + detail if detail else ""))
    sys.exit(1)

prd = PRD.read_text(encoding="utf-8")
task = TASK.read_text(encoding="utf-8")
check("PRD is UTF-8 with Turkish characters", all(c in prd for c in "şğıİçöüŞÇÖÜ"))
check("PRD has no BOM", not PRD.read_bytes().startswith(b"\xef\xbb\xbf"))
words = len(re.findall(r"\w+", prd))
check("PRD length is about 2-3 pages (1100-2200 words)", 1100 <= words <= 2200, f"{words} words")

# items by ID: **AC-1.1** text / **BR-01** text / **NFR-1 Performans:** text
items = {}
for line in prd.splitlines():
    m = re.match(r"^- \*\*((?:AC-\d\.\d)|(?:BR-\d\d)|(?:NFR-\d))\b[^*]*\*\*\s*(.*)$", line)
    if m:
        items[m.group(1)] = m.group(2)
expected_ids = [f"AC-{a}" for a in ("1.1", "1.2", "1.3", "1.4", "1.5", "2.1", "2.2", "2.3", "2.4",
                                    "3.1", "3.2", "3.3", "4.1", "4.2", "4.3", "5.1", "5.2", "5.3", "6.1", "6.2")]
expected_ids += [f"BR-{i:02d}" for i in range(1, 12)] + [f"NFR-{i}" for i in range(1, 6)]
missing = [i for i in expected_ids if i not in items]
check("PRD: all AC/BR/NFR items parse", not missing, f"missing={missing}")

# glossary rows
gloss = {}
for line in prd.split("## 2. Tanımlar", 1)[1].split("## 3.", 1)[0].splitlines():
    m = re.match(r"^\| ([^|]+?) \| (.+) \|$", line)
    if m and m.group(1) not in ("Terim", "---"):
        gloss[m.group(1)] = m.group(2)
check("glossary has the 7 terms",
      set(gloss) >= {"Teslim tarihi", "İade süresi", "İş günü", "Ürün satır tutarı", "Nergis Cüzdan", "Hızlı İade", "MH"},
      str(sorted(gloss)))

# CSV
raw = CSV.read_bytes()
check("CSV has no BOM", not raw.startswith(b"\xef\xbb\xbf"))
rows = list(csv.DictReader(io.StringIO(raw.decode("utf-8")), delimiter=";"))
check("CSV parses with ';' and has 14 rows", len(rows) == 14, f"{len(rows)} rows")
check("CSV columns", rows and list(rows[0].keys()) == ["kategori_kodu", "kategori_adi", "iade_edilebilir",
                                                         "iade_suresi_gun", "acilmis_ambalaj_kabul", "aciklama"])
ek = {r["kategori_kodu"]: r for r in rows}
check("CSV values are well-formed",
      all(r["iade_edilebilir"] in ("EVET", "HAYIR") and r["acilmis_ambalaj_kabul"] in ("EVET", "HAYIR")
          and r["iade_suresi_gun"].isdigit() for r in rows))
check("CSV non-returnable rows match BR-02 list (iç giyim/mayo, kişiye özel, dijital/hediye kartı)",
      sorted(k for k, r in ek.items() if r["iade_edilebilir"] == "HAYIR") == ["DIJ-01", "GIY-03", "OZL-01"])

# ------------------------------------------------------------------ K items
nfr1 = items.get("NFR-1", "")
check("K1 NFR-1 uses 'hızlı' and 'makul' with no numeric target",
      "hızlı" in nfr1 and "makul" in nfr1 and not re.search(r"\d+\s*(ms|sn|saniye|%|istek|kullanıcı)", nfr1), nfr1)

check("K2 AC-4.2 says 'uygun durumda' and 'uygun' is never defined elsewhere",
      "uygun durumda" in items.get("AC-4.2", "") and prd.count("uygun") == 1)

check("K3 AC-3.1 = 3 iş günü vs BR-10 = 5 iş günü",
      "3 iş günü" in items.get("AC-3.1", "") and "5 iş günü" in items.get("BR-10", ""))

low = prd.lower()
check("K4 AC-1.3 requires photos; PRD has no KVKK / personal-data / consent / retention rule for them",
      "fotoğraf" in items.get("AC-1.3", "")
      and not re.search(r"kvkk|kişisel veri|aydınlatma|rıza|imha", low)
      and [l for l in prd.splitlines() if "saklan" in l] == [l for l in prd.splitlines() if l.startswith("- **NFR-4")]
      )

br07, ac43 = items.get("BR-07", ""), items.get("AC-4.3", "")
check("K5 BR-07 '<500' and AC-4.3 '>500' with no inclusive wording anywhere",
      "500 TL'nin altındaki" in br07 and "500 TL'nin üzerindeki" in ac43
      and not re.search(r"500 TL ve|500,00|en az 500|500 TL dahil|500 TL'ye eşit", prd))
gap = []
for amt in (Decimal("499.99"), Decimal("500.00"), Decimal("500.01")):
    hizli, inspection_mandatory = amt < 500, amt > 500
    gap.append((str(amt), hizli, inspection_mandatory))
check("K5 simulation: 500.00 is neither Hızlı İade nor mandatory-inspection",
      gap[1][1:] == (False, False) and gap[0][1] and gap[2][2], str(gap))

us5 = prd.split("### US-5", 1)[1].split("### US-6", 1)[0]
check("K6 AC-5.1/5.2 allow expired approvals and amount changes with no limit/approval/audit rule",
      "süresi geçmiş" in items.get("AC-5.1", "") and "tutarını değiştirebilir" in items.get("AC-5.2", "")
      and not re.search(r"yetki|limit|onay(ı|lay[ıa]n)|denetim|audit|iz kaydı|gerekçe", us5.replace("onaylayabilir", ""))
      and "durum değişiklikleri" in items.get("NFR-4", ""))

check("K7 'risk skor' appears only in BR-07 (no definition, owner or integration)",
      low.count("risk skor") == 1 and "Risk skoru" in br07 and "risk" not in raw.decode("utf-8").lower())

koz = ek.get("KOZ-01", {})
check("K8 BR-04 rejects opened cosmetics but Ek-B KOZ-01 acilmis_ambalaj_kabul = EVET",
      "açılmış ürünler iade alınmaz" in items.get("BR-04", "") and koz.get("acilmis_ambalaj_kabul") == "EVET",
      str(koz))

br01 = items.get("BR-01", "")
std = int(re.search(r"Standart iade süresi (\d+) gündür", br01).group(1))
shorter = {k: r for k, r in ek.items() if r["iade_edilebilir"] == "EVET" and int(r["iade_suresi_gun"]) < std}
check("K9 only ELK-02 (Cep Telefonu, 14) is shorter than the 15-day standard; BR-01 covers only longer",
      std == 15 and list(shorter) == ["ELK-02"] and shorter["ELK-02"]["iade_suresi_gun"] == "14"
      and "daha uzun" in br01 and "daha kısa" not in low and "15 gündür" in items.get("AC-1.5", ""),
      f"shorter={list(shorter)}")

# K10: recompute Ek-A
eka = prd.split("## Ek-A", 1)[1].split("## Ek-B", 1)[0]
ex1, ex2 = eka.split("**Örnek 2", 1)


def table_amounts(block):
    out = {}
    for line in block.splitlines():
        m = re.match(r"^\| (.+?) \| (.+?) \|$", line)
        if m and "TL" in m.group(2):
            key = m.group(1).replace("**", "").strip()
            val = m.group(2).replace("**", "").replace("TL", "").replace("+", "").strip()
            out[key] = money(val)
    return out


t1, t2 = table_amounts(ex1), table_amounts(ex2)
coupon, deduction, rate, cap = Decimal("300.00"), Decimal("0"), Decimal("0.03"), Decimal("150.00")
share1 = q2(coupon * Decimal("1000.00") / Decimal("3000.00"))
refund1 = Decimal("1000.00") - share1 - deduction
check("K10 Örnek 1 is correct (share 100,00, refund 900,00)",
      -t1["Kupon orantılı payı (300,00 × 1.000,00 ÷ 3.000,00)"] == share1 == Decimal("100.00")
      and t1["Karta geri ödeme"] == refund1 == Decimal("900.00"), f"{t1}")

coupon2, line2, total2 = Decimal("400.00"), Decimal("4200.00"), Decimal("4200.00") + Decimal("600.00") + 2 * Decimal("300.00")
share2 = q2(coupon2 * line2 / total2)
refund2 = line2 - share2 - Decimal("39.90")
bonus2 = min(q2(refund2 * rate), cap)
wallet2 = refund2 + bonus2
doc_share, doc_refund, doc_bonus, doc_total = (-t2["Kupon orantılı payı"], t2["Geri ödeme tutarı"],
                                               t2["Cüzdan bonusu (%3, BR-09)"], t2["Cüzdana yüklenecek toplam"])
check("K10 Örnek 2 lines sum to 5.400,00 as stated", total2 == Decimal("5400.00") and "5.400,00 TL" in ex2)
check("K10 Örnek 2 is internally consistent except the coupon share",
      line2 - doc_share - Decimal("39.90") == doc_refund and q2(doc_refund * rate) == doc_bonus
      and doc_refund + doc_bonus == doc_total)
check("K10 Örnek 2 contradicts BR-06: doc 280,00/3.996,50 vs correct 311,11/3.964,46",
      doc_share == Decimal("280.00") and share2 == Decimal("311.11") and refund2 == Decimal("3848.99")
      and bonus2 == Decimal("115.47") and wallet2 == Decimal("3964.46") and doc_total - wallet2 == Decimal("32.04"),
      f"correct share={share2} refund={refund2} bonus={bonus2} total={wallet2}; doc total={doc_total}")

scope = prd.split("## 1.", 1)[1].split("## 2.", 1)[0]
check("K11 scope includes cash-on-delivery; AC-3.2 refunds to original method; no IBAN/cash path anywhere",
      "kapıda ödeme (nakit" in scope and "orijinal ödeme yöntemine" in items.get("AC-3.2", "")
      and not re.search(r"iban|havale|eft|nakit iade|banka hesab", low))

sec5 = prd.split("## 5.", 1)[1].split("## 6.", 1)[0]
states = re.findall(r"^\| ([A-ZÇĞİÖŞÜ_]+) \|", sec5, flags=re.M)
transitions = dict(re.findall(r"^\| ([A-ZÇĞİÖŞÜ_]+) \| [^|]+ \| ([A-ZÇĞİÖŞÜ_—-]+) \|", sec5, flags=re.M))
check("K12 lifecycle has exactly the 6 linear states",
      states == ["TALEP_ALINDI", "KARGODA", "DEPODA", "ONAYLANDI", "GERİ_ÖDEME_BAŞLATILDI", "TAMAMLANDI"], str(states))
check("K12 no cancel/expired/rejected/failed state although AC-2.2, AC-2.3, AC-4.2 need them",
      not any(re.search(r"İPTAL|RED|KAPAN|SÜRE|BAŞARISIZ|HATA", s) for s in states)
      and "otomatik olarak kapatılır" in items.get("AC-2.2", "") and "iptal" in items.get("AC-2.3", "")
      and "Reddet" in items.get("AC-4.2", ""))
check("K12 Hızlı İade needs KARGODA -> GERİ_ÖDEME_BAŞLATILDI, which the strictly linear table forbids",
      transitions.get("KARGODA") == "DEPODA" and "yalnızca tablodaki sıraya göre" in sec5
      and "depo kontrolü daha sonra yapılır" in br07)

# ------------------------------------------------------------------ traps
iade = gloss.get("İade süresi", "")
check("T1 glossary defines start day, inclusive end, 23:59:59 and Türkiye saati",
      "izleyen takvim gününden" in iade and "23:59:59" in iade and "Türkiye saati" in iade
      and "UTC+3" in gloss.get("Teslim tarihi", ""))
deliv = dt.date(2026, 10, 1)
last = deliv + dt.timedelta(days=15)
check("T1 glossary example (1 Ekim + 15 gün -> 16 Ekim 23:59:59) is arithmetically right",
      last == dt.date(2026, 10, 16) and "16 Ekim 23:59:59" in iade)

isg = gloss.get("İş günü", "")
check("T2 glossary defines iş günü: Mon-Fri, holidays, arife, start day not counted, end of day",
      all(s in isg for s in ("Pazartesi–Cuma", "resmî tatiller", "dinî bayram", "arife", "başlangıç günü sayılmaz", "23:59:59")))

longer = sorted(k for k, r in ek.items() if int(r["iade_suresi_gun"]) > std)
check("T3 only GIY-01, GIY-02, AYK-01 are longer (30) and BR-01 explicitly lets longer Ek-B periods win",
      longer == ["AYK-01", "GIY-01", "GIY-02"] and all(ek[k]["iade_suresi_gun"] == "30" for k in longer)
      and "daha uzun bir süre tanımlanmışsa o süre geçerlidir" in br01)

br09 = items.get("BR-09", "")
check("T4 BR-09 defines rate, cap, rounding and timing; AC-3.2 points to BR-09",
      all(s in br09 for s in ("%3", "150,00 TL", "yarım yukarı", "tek seferde")) and "(BR-09)" in items.get("AC-3.2", ""))

# ------------------------------------------------------------------ hygiene / independence
check("synthetic data: no e-mail addresses, IBANs or 11-digit IDs in inputs",
      not re.search(r"@|\bTR\d{2}|\b\d{11}\b", prd + raw.decode("utf-8")))
check("synthetic data: fictional-company notice present", "kurgusal" in prd)
check("TASK.md gives no hints about planted items",
      not re.search(r"500|kozmetik|kapıda|risk|telefon|Örnek 2|280|durum|tuzak|K\d|T\d", task, flags=re.I))
check("TASK.md names both inputs and both deliverables",
      all(s in task for s in ("PRD-Kolay-Iade-v1.3.md", "Ek-B-kategori-iade-kurallari.csv",
                              "gereksinim-analizi.md", "test-edilebilir-gereksinimler.md")))
check("trial folder contains no key material",
      not any(p.name.lower().startswith(("requirements", "key", "anahtar")) or "cevap" in p.name.lower()
              for p in TRIAL.rglob("*")))

failed = 0
for label, ok, detail in results:
    print(("PASS " if ok else "FAIL ") + label + (("  [" + detail + "]") if detail and not ok else ""))
    failed += not ok
print()
print(f"K10 reference: correct share {share2}, refund {refund2}, bonus {bonus2}, wallet total {wallet2} "
      f"(document: {doc_share}, {doc_refund}, {doc_bonus}, {doc_total})")
print(f"{len(results) - failed}/{len(results)} checks passed")
print("ALL CHECKS PASSED" if not failed else "SOME CHECKS FAILED")
sys.exit(1 if failed else 0)
