#!/usr/bin/env python3
"""Session-Based Test Management (SBTM) helper for exploratory testing.

Two subcommands:

charters  Rank requirements by risk (likelihood x impact) and write one exploratory
          charter per high-risk requirement: the charter sentence ("Explore <target>
          with <resources> to discover <information>"), heuristics chosen from the
          requirement text and type, oracles, a time box and what is out of scope.
          Requirements without a risk are scored 1x1 and listed last. Deprecated and
          deferred requirements are skipped.

report    Parse one or more session sheets (Markdown, see assets/session-sheet.md)
          and write three files into --out-dir:
            session-summary.md       per-session and total duration, TBS %, tag counts,
                                     bugs, issues, questions, ideas, coverage per REQ
            defects.md               a defect-report draft per BUG note
            candidate-tests.src.md   QA Suite compact test cases (status draft): one
                                     regression test per BUG and one per IDEA, linked
                                     to the session's REQ IDs; convert with qa_compact.py

Session sheet format (keys are case-insensitive; Turkish keys work too):
    charter: Explore the coupon field with boundary amounts to discover discount errors
    tester: Test Analyst A          start: 2026-09-30 10:00      duration: 90
    req: REQ-001, REQ-002           tbs: 60/25/15   (test/bug/setup %, optional)
    opportunity: 20   env: staging   build: 2.4.0-rc1   session: S-001   (all optional)
    ## Notes
    10:05 NOTE: Logged in as coupon.tester@example.com
    10:12 COVERED: cart total 99.99 / 100.00 / 100.01
    10:20 BUG: Coupon accepted at 99.99 total
      steps: Add items worth 99.99; apply YAZ10
      expected: Coupon rejected (REQ-001: >= 100)
      actual: 10% discount applied
      severity: high
    10:31 QUESTION: Should an expired coupon stay in the cart?
    10:40 ISSUE: Test data reset takes 10 minutes
    10:45 IDEA [REQ-003]: Coupon code with Turkish dotted/dotless i
  One field per line is the documented form; several "key: value" pairs on one header line
  are accepted when separated by two or more spaces. Tags: BUG, ISSUE, QUESTION, IDEA, NOTE,
  COVERED (Turkish: HATA, SORUN, SORU, FIKIR/FİKİR, NOT, KAPSAM). The time is optional.
  "[REQ-###]" after a tag links that note to specific requirements. Indented lines below a
  note add detail; for BUG notes the keys steps/expected/actual/severity/data/evidence
  (adımlar/beklenen/gerçekleşen/önem/veri/kanıt) fill the defect draft.

Usage:
  python sbtm.py charters --requirements qa/requirements.json --top 8 --lang tr \\
      --out qa/exploratory/charters.md
  python sbtm.py report qa/exploratory/sessions/S-001.md qa/exploratory/sessions/S-002.md \\
      --tests qa/test-cases.json --requirements qa/requirements.json --lang tr --out-dir qa/exploratory
  python qa_compact.py tc qa/exploratory/candidate-tests.src.md --out qa/exploratory/candidate-tests.json

Exit codes: 0 ok, 1 invalid input (missing charter/duration, unreadable requirements; nothing
written), 2 usage error or unreadable file.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

PRI_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3}
PRI_SHORT = {"critical": "c", "high": "h", "medium": "m", "low": "l"}
TAGS = ("BUG", "ISSUE", "QUESTION", "IDEA", "NOTE", "COVERED")
TAG_ALIASES = {"BUG": "BUG", "HATA": "BUG", "DEFECT": "BUG", "ISSUE": "ISSUE", "SORUN": "ISSUE",
               "QUESTION": "QUESTION", "SORU": "QUESTION", "IDEA": "IDEA", "FIKIR": "IDEA", "FİKİR": "IDEA",
               "NOTE": "NOTE", "NOT": "NOTE", "COVERED": "COVERED", "KAPSAM": "COVERED", "COVERAGE": "COVERED"}
HEADER_KEYS = {
    "charter": "charter", "görev": "charter", "gorev": "charter", "misyon": "charter", "mission": "charter",
    "tester": "tester", "testçi": "tester", "testci": "tester", "test eden": "tester",
    "start": "start", "başlangıç": "start", "baslangic": "start", "date": "start", "tarih": "start",
    "duration": "duration", "süre": "duration", "sure": "duration",
    "req": "req", "reqs": "req", "requirements": "req", "gereksinim": "req", "gereksinimler": "req",
    "tbs": "tbs", "opportunity": "opportunity", "fırsat": "opportunity", "firsat": "opportunity",
    "env": "env", "environment": "env", "ortam": "env", "build": "build", "sürüm": "build", "surum": "build",
    "session": "session", "oturum": "session", "timebox": "timebox", "zaman kutusu": "timebox",
    "areas": "areas", "alanlar": "areas",
}
DETAIL_KEYS = {"steps": "steps", "step": "steps", "adımlar": "steps", "adimlar": "steps", "adım": "steps",
               "expected": "expected", "beklenen": "expected", "actual": "actual", "gerçekleşen": "actual",
               "gerceklesen": "actual", "gerçek": "actual", "severity": "severity", "önem": "severity",
               "onem": "severity", "ciddiyet": "severity", "data": "data", "veri": "data",
               "evidence": "evidence", "kanıt": "evidence", "kanit": "evidence",
               "repro": "repro", "tekrar": "repro"}
SEVERITIES = {"critical": "critical", "kritik": "critical", "high": "high", "yüksek": "high", "yuksek": "high",
              "medium": "medium", "orta": "medium", "low": "low", "düşük": "low", "dusuk": "low"}
REQ_RE = re.compile(r"\bREQ-\d{3,}\b")
NOTE_RE = re.compile(r"^\s*(?:[-*+]\s+)?(?:\[?(?P<time>\d{1,2}[:.]\d{2})\]?\s*(?:[-–—]\s*)?)?"
                     r"(?P<tag>[A-Za-zİıÇçĞğÖöŞşÜü]+)\s*(?:\[(?P<reqs>[^\]]*)\])?\s*:\s*(?P<text>.*)$")
FOLD = str.maketrans("ıİşŞğĞüÜöÖçÇ", "iissgguuoocc")

T = {
    "en": {
        "ch_title": "Exploratory test charters", "ch_intro": "Generated by sbtm.py from {src}. Charters are ranked by "
        "requirement risk (likelihood x impact); requirements without a risk are scored 1x1 and listed last. "
        "Review each charter: sharpen the target, drop heuristics that do not fit, and agree the time box.",
        "ranking": "Risk ranking", "rank_cols": "| # | REQ | Title | L x I | Score | Level | Time box | Charter |",
        "budget": "Planned budget: {n} sessions, {m} min (~{h} h) of on-charter time.",
        "no_risk": "no risk", "charter": "Charter", "explore": "Explore {target} with {resources} to discover {info}.",
        "reqs": "Requirements", "risk": "Risk", "timebox": "Time box", "min": "min", "heur": "Heuristics and prompts",
        "oracles": "Oracles (how you will recognise a problem)", "oos": "Out of scope",
        "setup": "Setup and resources", "open_q": "Open questions {q}: explore to inform the answer; do not decide the "
        "expected result yourself.", "derived": "Derived (implicit) requirement: confirm it with the product owner.",
        "ac": "Acceptance criteria: {ac}", "claims": "Claims: the requirement text and its acceptance criteria",
        "also": "Also consider (weaker match)",
        "ask_risk": "ranking is provisional; ask for likelihood and impact",
        "other_oracles": "Other FEW HICCUPPS oracles: History (previous version), Image, Comparable products, "
        "User expectations, Product (consistency within it), Purpose, Statutes and standards; Familiar problems, "
        "Explainability, World (does it make sense in the real world?)",
        "sheet": "Session sheet: copy the template, set `charter:` to the sentence above and `req: {req}`.",
        "levels": {"critical": "critical", "high": "high", "medium": "medium", "low": "low"},
        "oos_generic": ["Production systems, real customer data and real payment instruments",
                        "Destructive or irreversible actions (bulk delete, real messages to people) unless the "
                        "environment is resettable and the owner agreed",
                        "Other features, except where this feature's data flows through them"],
        "setup_generic": ["Test environment URL and build number", "Test accounts only (fictional names, "
                          "example.com addresses)", "A way to reset or re-seed test data"],
        "default_heur": [("SFDIPOT sweep", "Walk Structure, Function, Data, Interfaces, Platform, Operations and Time "
                          "for this feature; note each element you visited as COVERED.")],
        "default_res": "the requirement's acceptance criteria and varied realistic data",
        "default_info": "deviations from {req} and behaviour nobody specified",
        "sum_title": "Exploratory session summary", "sessions": "Sessions", "totals": "Totals",
        "sess_cols": "| Session | Charter | Tester | Start | Duration | T / B / S % | Opp. % | BUG | ISSUE | QUESTION | IDEA | COVERED |",
        "tot_duration": "Total session time: {m} min ({h} h) in {n} sessions.",
        "tbs_line": "TBS (duration-weighted, {k} of {n} sessions recorded it): test {t}%, bug investigation {b}%, "
        "setup {s}%.", "tbs_none": "TBS: not recorded (add `tbs: test/bug/setup` to the session sheets).",
        "opp_line": "Opportunity (off-charter) time: {o}% of session time in sessions that recorded it.",
        "tag_counts": "Notes per tag", "bugs": "Bugs", "issues": "Issues and obstacles", "questions": "Open questions",
        "ideas": "Test ideas", "coverage": "Coverage by requirement", "covered_notes": "Covered (as noted)",
        "cov_cols": "| REQ | Sessions | Session minutes (shared) | BUG | QUESTION |", "none": "None.",
        "bug_cols": "| Session | Time | Bug | REQ | Defect draft | Candidate TC |",
        "debrief": "Debrief (PROOF) prompts", "proof": [
            ("Past", "What happened in the session? Where did the time go ({tbs})?"),
            ("Results", "What was achieved? {bugs} bug(s), coverage of {reqs}."),
            ("Obstacles", "What got in the way? {issues} issue(s) recorded."),
            ("Outlook", "What still needs doing? {ideas} idea(s), {qs} open question(s); new charters?"),
            ("Feelings", "How does the tester feel about the product and the session? (ask; not in the notes)")],
        "warn_title": "Warnings", "not_rec": "not recorded",
        "def_title": "Defect report drafts", "def_intro": "One draft per BUG note from the session sheets. Replace "
        "every <...> prompt, reproduce once more, search for duplicates, then file the defect in the tracker "
        "and record its key in qa/defects.json and qa/results.json.",
        "f_session": "Session", "f_linked": "Linked", "f_env": "Environment", "f_sev": "Severity",
        "f_pri": "Priority", "f_pre": "Preconditions", "f_steps": "Steps to reproduce", "f_exp": "Expected",
        "f_act": "Actual", "f_repro": "Reproducibility", "f_evid": "Evidence", "f_notes": "Notes (from the session)",
        "p_env": "<build, environment, browser/OS, locale, test account role>", "p_sev": "<critical | high | medium | low>",
        "sev_hint": " (starting point from {req} impact {i}: {s}; judge the actual impact)",
        "p_pri": "<set by the product owner>", "p_pre": "<state needed before step 1: data, role, flags>",
        "p_step": "<reproduce the note: {text}>", "p_exp": "<quote the requirement or acceptance criterion>",
        "p_exp_req": "<quote {req}: {text}>", "p_act": "<what happened, verbatim: message, value, status>",
        "p_repro": "<always / n of m attempts>", "p_evid": "<screenshot, trace, log excerpt around {time}>",
        "cand_head": "# Candidate regression tests derived by sbtm.py from exploratory session sheets. Status draft: "
        "replace every <...> prompt, then append to qa/test-cases.src.md.",
        "reg": "Regression: {text}", "obj_bug": "Guards against recurrence of the bug found in session {s} at {t}",
        "obj_idea": "Test idea from exploratory session {s} at {t}", "e_step": "<observable result of this step>",
        "e_final": "<expected result per {req}>", "e_final_none": "<expected result: agree it with the product owner>",
        "i_step": "<steps for: {text}>", "pre_env": "Test environment: {env}", "auto_reason": "regression for an "
        "exploratory finding", "auto_idea": "decide after the first manual run",
    },
    "tr": {
        "ch_title": "Keşif testi görev kartları (charter)", "ch_intro": "{src} dosyasından sbtm.py ile üretildi. "
        "Görevler gereksinim riskine (olasılık x etki) göre sıralanır; riski olmayan gereksinimler 1x1 sayılır ve "
        "sona konur. Her kartı gözden geçirin: hedefi netleştirin, uymayan sezgisel yöntemleri çıkarın, zaman "
        "kutusunda anlaşın.",
        "ranking": "Risk sıralaması", "rank_cols": "| # | REQ | Başlık | O x E | Skor | Seviye | Zaman kutusu | Görev |",
        "budget": "Planlanan bütçe: {n} oturum, {m} dk (~{h} saat) görev süresi.",
        "no_risk": "risk yok", "charter": "Görev", "explore": "{resources} kullanarak {target} alanını keşfet; "
        "amaç: {info} bulmak.",
        "reqs": "Gereksinimler", "risk": "Risk", "timebox": "Zaman kutusu", "min": "dk", "heur": "Sezgisel yöntemler ve sorular",
        "oracles": "Kahinler (sorunu nasıl tanıyacaksınız)", "oos": "Kapsam dışı",
        "setup": "Hazırlık ve kaynaklar", "open_q": "Açık sorular {q}: cevabı beslemek için keşfedin; beklenen sonucu "
        "kendiniz belirlemeyin.", "derived": "Türetilmiş (örtük) gereksinim: ürün sahibiyle teyit edin.",
        "ac": "Kabul kriterleri: {ac}", "claims": "İddialar (Claims): gereksinim metni ve kabul kriterleri",
        "also": "Ayrıca düşünün (zayıf eşleşme)",
        "ask_risk": "sıralama geçici; olasılık ve etkiyi sorun",
        "other_oracles": "Diğer FEW HICCUPPS kahinleri: Geçmiş (önceki sürüm), İmaj, Benzer ürünler, "
        "Kullanıcı beklentileri, Ürün (kendi içinde tutarlılık), Amaç, Yasalar ve standartlar; Bilinen hata "
        "kalıpları, Açıklanabilirlik, Dünya (gerçek hayatta anlamlı mı?)",
        "sheet": "Oturum formu: şablonu kopyalayın, `charter:` alanına yukarıdaki cümleyi ve `req: {req}` yazın.",
        "levels": {"critical": "kritik", "high": "yüksek", "medium": "orta", "low": "düşük"},
        "oos_generic": ["Canlı sistemler, gerçek müşteri verisi ve gerçek ödeme araçları",
                        "Yıkıcı veya geri alınamaz işlemler (toplu silme, gerçek kişilere mesaj) - ortam sıfırlanabilir "
                        "değilse ve sahibi onaylamadıysa",
                        "Diğer özellikler - bu özelliğin verisi içlerinden geçmiyorsa"],
        "setup_generic": ["Test ortamı adresi ve sürüm numarası", "Yalnızca test hesapları (kurgusal isimler, "
                          "example.com adresleri)", "Test verisini sıfırlama veya yeniden yükleme yolu"],
        "default_heur": [("SFDIPOT taraması", "Bu özellik için Yapı, İşlev, Veri, Arayüzler, Platform, Operasyon ve "
                          "Zaman öğelerini gezin; gezdiğiniz her öğeyi COVERED olarak not edin.")],
        "default_res": "kabul kriterlerini ve çeşitli gerçekçi verileri",
        "default_info": "{req} gereksiniminden sapmaları ve kimsenin tanımlamadığı davranışları",
        "sum_title": "Keşif testi oturum özeti", "sessions": "Oturumlar", "totals": "Toplamlar",
        "sess_cols": "| Oturum | Görev | Test eden | Başlangıç | Süre | T / B / S % | Fırsat % | BUG | ISSUE | QUESTION | IDEA | COVERED |",
        "tot_duration": "Toplam oturum süresi: {n} oturumda {m} dk ({h} saat).",
        "tbs_line": "TBS (süreye göre ağırlıklı, {n} oturumun {k} tanesinde kayıtlı): test %{t}, hata inceleme %{b}, "
        "hazırlık %{s}.", "tbs_none": "TBS: kaydedilmemiş (oturum formlarına `tbs: test/bug/setup` ekleyin).",
        "opp_line": "Fırsat (görev dışı) süresi: kaydeden oturumlarda sürenin %{o}'i.",
        "tag_counts": "Etiket başına not", "bugs": "Hatalar", "issues": "Sorunlar ve engeller", "questions": "Açık sorular",
        "ideas": "Test fikirleri", "coverage": "Gereksinim bazında kapsam", "covered_notes": "Kapsanan (notlara göre)",
        "cov_cols": "| REQ | Oturum | Oturum dakikası (paylaşımlı) | BUG | QUESTION |", "none": "Yok.",
        "bug_cols": "| Oturum | Saat | Hata | REQ | Hata taslağı | Aday TC |",
        "debrief": "Değerlendirme (PROOF) soruları", "proof": [
            ("Past (Geçmiş)", "Oturumda ne oldu? Zaman nereye gitti ({tbs})?"),
            ("Results (Sonuçlar)", "Ne elde edildi? {bugs} hata, {reqs} kapsamı."),
            ("Obstacles (Engeller)", "Ne engel oldu? {issues} sorun kaydedildi."),
            ("Outlook (Görünüm)", "Geriye ne kaldı? {ideas} fikir, {qs} açık soru; yeni görevler?"),
            ("Feelings (Hisler)", "Test eden ürün ve oturum hakkında ne hissediyor? (sorun; notlarda yok)")],
        "warn_title": "Uyarılar", "not_rec": "kaydedilmemiş",
        "def_title": "Hata raporu taslakları", "def_intro": "Oturum formlarındaki her BUG notu için bir taslak. "
        "Tüm <...> alanlarını doldurun, bir kez daha yeniden üretin, mükerrer kayıt arayın, sonra hatayı takip "
        "aracına girin ve anahtarını qa/defects.json ile qa/results.json dosyalarına yazın.",
        "f_session": "Oturum", "f_linked": "Bağlantılar", "f_env": "Ortam", "f_sev": "Önem (severity)",
        "f_pri": "Öncelik", "f_pre": "Ön koşullar", "f_steps": "Yeniden üretme adımları", "f_exp": "Beklenen",
        "f_act": "Gerçekleşen", "f_repro": "Tekrarlanabilirlik", "f_evid": "Kanıt", "f_notes": "Notlar (oturumdan)",
        "p_env": "<sürüm, ortam, tarayıcı/işletim sistemi, yerel ayar, test hesabı rolü>",
        "p_sev": "<critical | high | medium | low>",
        "sev_hint": " ({req} etki {i} için başlangıç önerisi: {s}; gerçek etkiyi siz değerlendirin)",
        "p_pri": "<ürün sahibi belirler>", "p_pre": "<1. adımdan önce gereken durum: veri, rol, bayraklar>",
        "p_step": "<notu yeniden üret: {text}>", "p_exp": "<gereksinimi veya kabul kriterini alıntılayın>",
        "p_exp_req": "<{req} alıntısı: {text}>", "p_act": "<olan şey, aynen: mesaj, değer, durum>",
        "p_repro": "<her zaman / m denemenin n'sinde>", "p_evid": "<ekran görüntüsü, trace, {time} civarı log>",
        "cand_head": "# sbtm.py ile keşif testi oturum formlarından türetilen aday regresyon testleri. Durum draft: "
        "tüm <...> alanlarını doldurun, sonra qa/test-cases.src.md dosyasına ekleyin.",
        "reg": "Regresyon: {text}", "obj_bug": "{s} oturumunda {t} saatinde bulunan hatanın tekrarlanmasını önler",
        "obj_idea": "{s} keşif oturumundan ({t}) test fikri", "e_step": "<bu adımın gözlenebilir sonucu>",
        "e_final": "<{req} gereksinimine göre beklenen sonuç>", "e_final_none": "<beklenen sonuç: ürün sahibiyle netleştirin>",
        "i_step": "<adımlar: {text}>", "pre_env": "Test ortamı: {env}", "auto_reason": "keşif bulgusu için regresyon",
        "auto_idea": "ilk manuel koşudan sonra karar verin",
    },
}

# Heuristic rules for charters: keywords (folded, word-prefix match) -> heuristics, resources, information.
RULES = [
    {"id": "money",
     "kw": ["money", "amount", "price", "payment", "pay ", "balance", "limit", "fee", "discount", "coupon", "currency",
            "total", "refund", "transfer", "tax", "interest", "tl ", "eur", "usd", "tutar", "ucret", "fiyat",
            "odeme", "bakiye", "indirim", "kupon", "para", "komisyon", "vergi", "iade", "havale", "eft", "faiz", "kur "],
     "types": ["business-rule"],
     "en": {"heur": [("Boundaries and Goldilocks", "Too small, just right, too big: 0, negative, min-0.01, min, max, "
                      "max+0.01, many decimals, rounding, very large totals."),
                     ("FEW HICCUPPS: Claims and Standards", "Does the result match the stated rule, currency and rounding "
                      "conventions and the receipt/invoice? Recalculate one example by hand.")],
            "res": "boundary amounts and a hand-calculated example", "info": "calculation, rounding and limit errors"},
     "tr": {"heur": [("Sınırlar ve Goldilocks", "Çok küçük, tam kararında, çok büyük: 0, negatif, min-0,01, min, max, "
                      "max+0,01, çok ondalıklı değerler, yuvarlama, çok büyük toplamlar."),
                     ("FEW HICCUPPS: İddialar ve Standartlar", "Sonuç yazılı kurala, para birimi ve yuvarlama kurallarına, "
                      "fiş/faturaya uyuyor mu? Bir örneği elle hesaplayın.")],
            "res": "sınır tutarlarını ve elle hesaplanmış bir örneği", "info": "hesaplama, yuvarlama ve limit hatalarını"}},
    {"id": "security",
     "kw": ["role", "permission", "admin", "authoriz", "authent", "login", "log in", "password", "token", "access",
            "privacy", "personal data", "owner", "another user", "own ", "tenant", "rol", "yetki", "giris yap",
            "sifre", "parola", "erisim", "gizlilik", "kisisel veri", "kvkk", "gdpr", "kendi", "baska kullanici"],
     "types": [], "qc": ["security"],
     "en": {"heur": [("Role swap / BOLA", "Repeat each action as another user and with a lower role; change IDs "
                      "in URLs, forms and requests; reuse a link after logout."),
                     ("FEW HICCUPPS: Standards and User expectations", "OWASP ASVS/Top 10 expectations, privacy "
                      "rules; would a user expect this data to be visible here?")],
            "res": "two test accounts with different roles",
            "info": "data leaks and actions allowed to the wrong user"},
     "tr": {"heur": [("Rol değiştirme / BOLA", "Her işlemi başka bir kullanıcıyla ve daha düşük bir rolle tekrarlayın; "
                      "URL, form ve isteklerdeki kimlikleri değiştirin; çıkıştan sonra bağlantıyı yeniden kullanın."),
                     ("FEW HICCUPPS: Standartlar ve Kullanıcı beklentileri", "OWASP ASVS/Top 10 beklentileri, KVKK; "
                      "kullanıcı bu verinin burada görünmesini bekler mi?")],
            "res": "farklı rollerde iki test hesabını",
            "info": "veri sızıntılarını ve yanlış kullanıcıya izin verilen işlemleri"}},
    {"id": "state",
     "kw": ["state ", "states", "state-", "status", "workflow", "approv", "cancel", "order", "expire", "session", "pending", "retry",
            "step", "lifecycle", "durum", "onay", "iptal", "siparis", "suresi", "adim", "akis", "bekle", "askida"],
     "types": [],
     "en": {"heur": [("State model walk", "Sketch the states and transitions; try every transition, including the "
                      "ones that should be impossible (skip a step, go back, repeat)."),
                     ("Interruptions", "Refresh, Back button, double-click submit, second tab, session timeout, "
                      "network drop in the middle of the flow.")],
            "res": "a sketch of the state model and a second browser tab",
            "info": "invalid transitions, double submissions and lost updates"},
     "tr": {"heur": [("Durum modeli gezisi", "Durumları ve geçişleri çizin; olmaması gerekenler dahil her geçişi "
                      "deneyin (adım atlama, geri dönme, tekrar)."),
                     ("Kesintiler", "Yenileme, Geri tuşu, gönder'e çift tıklama, ikinci sekme, oturum zaman aşımı, "
                      "akışın ortasında ağ kesintisi.")],
            "res": "durum modeli çizimini ve ikinci bir tarayıcı sekmesini",
            "info": "geçersiz geçişleri, çift gönderimleri ve kaybolan güncellemeleri"}},
    {"id": "input",
     "kw": ["input", "form", "field", "enter", "upload", "search", "text", "name", "email", "e-mail", "code", "format",
            "character", "case-insens", "uppercase", "lowercase", "girdi", "alan", "yukle", "arama", "metin", "isim", "ad ", "karakter", "bicim",
            "kod", "harf", "buyuk", "kucuk", "dosya", "file"],
     "types": ["data", "interface"],
     "en": {"heur": [("Data tour / follow the data", "Enter a value, then follow it: list, detail, edit, search, "
                      "export, e-mail, report. Is it identical everywhere?"),
                     ("Input variety", "Empty, whitespace only, leading/trailing spaces, very long, Unicode and "
                      "Turkish İ/ı/ş/ğ, emoji, HTML/script-like text, pasted text, wrong format.")],
            "res": "varied input data (empty, long, Unicode incl. Turkish letters, special characters)",
            "info": "validation gaps and data that is changed or lost on the way"},
     "tr": {"heur": [("Veri turu / veriyi takip et", "Bir değer girin ve peşinden gidin: liste, detay, düzenleme, "
                      "arama, dışa aktarma, e-posta, rapor. Her yerde aynı mı?"),
                     ("Girdi çeşitliliği", "Boş, yalnız boşluk, baş/son boşluk, çok uzun, Unicode ve Türkçe İ/ı/ş/ğ, "
                      "emoji, HTML/script benzeri metin, yapıştırılmış metin, yanlış biçim.")],
            "res": "çeşitli girdileri (boş, uzun, Türkçe karakterli Unicode, özel karakterler)",
            "info": "doğrulama boşluklarını ve yolda değişen veya kaybolan veriyi"}},
    {"id": "time",
     "kw": ["date", "time ", "day", "deadline", "timezone", "schedule", "month", "year", "tarih", "saat", "gun ", "gunu",
            "gunluk", "ay ", "yil", "takvim", "vade"],
     "types": [],
     "en": {"heur": [("Time boundaries", "Midnight, month end, 29 February, year end, time zone and daylight "
                      "saving change, a clock that is minutes ahead, an item that expires during the session.")],
            "res": "dates around midnight, month and year ends", "info": "date and time-zone errors"},
     "tr": {"heur": [("Zaman sınırları", "Gece yarısı, ay sonu, 29 Şubat, yıl sonu, saat dilimi ve yaz saati "
                      "değişimi, birkaç dakika ileri saat, oturum sırasında süresi dolan kayıt.")],
            "res": "gece yarısı, ay ve yıl sonu tarihlerini", "info": "tarih ve saat dilimi hatalarını"}},
    {"id": "performance",
     "kw": ["performance", "response time", "concurren", "load", "latency", "fast", "slow", " ms", "second",
            "p95", "performans", "yanit suresi", "eszamanli", "yuk altinda", "yuk testi", "hizli", "yavas", "saniye"],
     "types": [], "qc": ["performance-efficiency"],
     "en": {"heur": [("Tempo and volume", "Repeat quickly, add many items, throttle the network (Slow 3G), "
                      "watch spinners and timeouts. This complements, not replaces, a load test.")],
            "res": "network throttling and a large data set", "info": "slowdowns and timeouts users would notice"},
     "tr": {"heur": [("Tempo ve hacim", "Hızlı tekrarlayın, çok sayıda kayıt ekleyin, ağı yavaşlatın (Slow 3G), "
                      "bekleme göstergelerini ve zaman aşımlarını izleyin. Yük testinin yerini tutmaz, tamamlar.")],
            "res": "ağ yavaşlatmayı ve büyük veri setini", "info": "kullanıcının fark edeceği yavaşlık ve zaman aşımlarını"}},
    {"id": "integration",
     "kw": ["api", "integration", "notification", "sms", "third-party", "export", "import", "webhook", "sync",
            "entegrasyon", "bildirim", "disa aktar", "ice aktar", "senkron", "servis"],
     "types": ["interface"],
     "en": {"heur": [("Follow the data across systems", "Trace one record through every system it touches; "
                      "slow or fail the dependency (if the environment allows) and retry.")],
            "res": "access to the logs or admin view of the connected system",
            "info": "lost, duplicated or inconsistent data between systems"},
     "tr": {"heur": [("Veriyi sistemler arasında takip et", "Bir kaydı dokunduğu her sistemde izleyin; ortam "
                      "izin veriyorsa bağımlılığı yavaşlatın veya düşürün ve tekrar deneyin.")],
            "res": "bağlı sistemin loglarına veya yönetim ekranına erişimi",
            "info": "sistemler arasında kaybolan, çoğalan veya tutarsız veriyi"}},
    {"id": "ux",
     "kw": ["message", "error message", "screen", "button", "display", "show", "mobile", "accessib", "usab",
            "mesaj", "ekran", "buton", "goster", "goruntu", "mobil", "erisilebilir", "kullanilabilir"],
     "types": [], "qc": ["interaction-capability"],
     "en": {"heur": [("FEW HICCUPPS: User expectations, Product, Image", "Is the behaviour consistent with the rest "
                      "of the product and with what a first-time user expects? Would it embarrass the brand?"),
                     ("Landmark and supermodel tours", "Visit the key screens quickly, then look only at surface: "
                      "texts, alignment, keyboard use, zoom 200%, mobile width.")],
            "res": "a first-time-user mindset, keyboard only and a mobile viewport",
            "info": "confusing messages and inconsistent behaviour"},
     "tr": {"heur": [("FEW HICCUPPS: Kullanıcı beklentileri, Ürün, İmaj", "Davranış ürünün geri kalanıyla ve ilk "
                      "kez kullanan birinin beklentisiyle tutarlı mı? Markayı utandırır mı?"),
                     ("Simge yapı ve manken turları", "Ana ekranları hızla gezin, sonra yalnızca yüzeye bakın: "
                      "metinler, hizalama, klavye kullanımı, %200 yakınlaştırma, mobil genişlik.")],
            "res": "ilk kez kullanan bakışını, yalnız klavyeyi ve mobil ekranı",
            "info": "kafa karıştıran mesajları ve tutarsız davranışları"}},
]
OOS_EXTRA = {
    "performance": {"en": "Load and stress testing at scale (use the testing-nonfunctional skill)",
                    "tr": "Ölçekli yük ve stres testi (testing-nonfunctional becerisini kullanın)"},
    "security": {"en": "Penetration testing, scanners and attacks on shared infrastructure without written permission",
                 "tr": "Yazılı izin olmadan sızma testi, tarayıcılar ve paylaşılan altyapıya saldırı"},
    "money": {"en": "Real payment cards or real money movements (use the provider's test mode)",
              "tr": "Gerçek kartlar veya gerçek para hareketi (sağlayıcının test modunu kullanın)"},
}


def fold(s: str) -> str:
    return (s or "").replace("İ", "i").replace("I", "i").lower().translate(FOLD)


def matches(text: str, kw: str) -> bool:
    kw = fold(kw)
    if kw.endswith(" "):  # whole word
        return re.search(r"(?<!\w)" + re.escape(kw.strip()) + r"(?!\w)", text) is not None
    if kw.startswith(" "):
        return re.search(r"(?<!\w)" + re.escape(kw.strip()), text) is not None
    return re.search(r"(?<!\w)" + re.escape(kw), text) is not None


def risk_of(r: dict) -> tuple[int, int, bool]:
    rk = r.get("risk") or {}
    try:
        li, im = int(rk.get("likelihood")), int(rk.get("impact"))
        return li, im, True
    except (TypeError, ValueError):
        return 1, 1, False


def level_of(score: int, has: bool) -> str:
    if not has or score <= 5:
        return "low"
    if score >= 20:
        return "critical"
    if score >= 12:
        return "high"
    return "medium"


def pick_rules(r: dict) -> tuple[list[dict], list[dict]]:
    """(primary, secondary) heuristic rules. Score = distinct keyword hits + 2 for a matching quality
    characteristic + 1 for a matching requirement type. Primary: score >= a third of the best score
    (at most 3); the charter sentence uses the first two. Secondary: weaker matches, named only."""
    text = fold(" ".join([r.get("title", ""), r.get("text", "")] + list(r.get("acceptance_criteria") or [])))
    scored = []
    for i, rule in enumerate(RULES):
        sc = sum(1 for k in rule["kw"] if matches(text, k))
        sc += 2 if r.get("quality_characteristic") in rule.get("qc", []) else 0
        sc += 1 if r.get("type") in rule.get("types", []) else 0
        if sc:
            scored.append((-sc, i, rule))
    scored.sort(key=lambda x: (x[0], x[1]))
    if not scored:
        return [], []
    limit = max(1, -(-(-scored[0][0]) // 3))
    primary = [x[2] for x in scored if -x[0] >= limit][:3]
    secondary = [x[2] for x in scored if x[2] not in primary]
    return primary, secondary


def cmd_charters(a) -> int:
    t = T[a.lang]
    try:
        doc = json.loads(Path(a.requirements).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as e:
        print(f"error: cannot read requirements: {e}", file=sys.stderr)
        return 2
    reqs = [r for r in doc.get("requirements", []) if r.get("status") not in ("deprecated", "deferred")]
    if not reqs:
        print("error: no active requirements in the file", file=sys.stderr)
        return 1
    rows = []
    for r in reqs:
        li, im, has = risk_of(r)
        rows.append({"r": r, "li": li, "im": im, "has": has, "score": li * im})
    rows.sort(key=lambda x: (not x["has"], -x["score"], PRI_RANK.get(x["r"].get("priority"), 4), x["r"]["id"]))
    top = rows[: a.top] if a.top else rows
    for x in top:
        x["level"] = level_of(x["score"], x["has"])
        x["box"] = {"critical": 120, "high": a.timebox, "medium": a.timebox, "low": 60}[x["level"]]
    out = [f"# {t['ch_title']}", "", t["ch_intro"].format(src=Path(a.requirements).name), "",
           f"## {t['ranking']}", "", t["rank_cols"], "|---|---|---|---|---|---|---|---|"]
    for i, x in enumerate(rows, 1):
        r = x["r"]
        in_top = x in top
        lx = f"{x['li']} x {x['im']}" if x["has"] else t["no_risk"]
        lvl = t["levels"][x.get("level") or level_of(x["score"], x["has"])]
        out.append(f"| {i} | {r['id']} | {cell(r.get('title', ''))} | {lx} | {x['score'] if x['has'] else '-'} | {lvl} | "
                   f"{str(x['box']) + ' ' + t['min'] if in_top else '-'} | {'CH-%02d' % (top.index(x) + 1) if in_top else '-'} |")
    total = sum(x["box"] for x in top)
    out += ["", t["budget"].format(n=len(top), m=total, h=round(total / 60, 1)), ""]
    for n, x in enumerate(top, 1):
        r = x["r"]
        rules, also = pick_rules(r)
        target = f"{r.get('title', r['id'])} ({r['id']})"
        if rules:
            res = ", ".join(rule[a.lang]["res"] for rule in rules[:2])
            info = ", ".join(rule[a.lang]["info"] for rule in rules[:2])
        else:
            res, info = t["default_res"], t["default_info"].format(req=r["id"])
        sentence = t["explore"].format(target=target, resources=res, info=info)
        sentence = sentence[0].upper() + sentence[1:]
        out += ["---", "", f"## CH-{n:02d} · {r['id']} · {r.get('title', '')}", "",
                f"**{t['charter']}:** {sentence}", "",
                f"- **{t['reqs']}:** {r['id']}" + (f" ({r['external_id']})" if r.get("external_id") else ""),
                f"- **{t['risk']}:** " + (f"{x['li']} x {x['im']} = {x['score']} ({t['levels'][x['level']]})"
                                           if x["has"] else f"{t['no_risk']} ({t['levels']['low']}) - {t['ask_risk']}")
                + (f" - {r['risk'].get('rationale')}" if x["has"] and r["risk"].get("rationale") else ""),
                f"- **{t['timebox']}:** {x['box']} {t['min']}"]
        if r.get("questions") or r.get("status") == "clarification-needed":
            out.append(f"- {t['open_q'].format(q=', '.join(r.get('questions') or []))}".replace(" :", ":").replace("  ", " "))
        if r.get("derived"):
            out.append(f"- {t['derived']}")
        out += ["", f"### {t['heur']}"]
        heur = [h for rule in rules for h in rule[a.lang]["heur"]] or t["default_heur"]
        for name, prompt in heur:
            out.append(f"- **{name}:** {prompt}")
        if also:
            out.append(f"- {t['also']}: " + "; ".join(h[0] for rule in also for h in rule[a.lang]["heur"]))
        out += ["", f"### {t['oracles']}", f"- {t['claims']}"]
        for ac in r.get("acceptance_criteria") or []:
            out.append(f"  - {ac}")
        out.append("- " + t["other_oracles"])
        out += ["", f"### {t['setup']}"] + [f"- {s}" for s in t["setup_generic"]]
        for rule in rules:
            out.append(f"- {rule[a.lang]['res'][0].upper()}{rule[a.lang]['res'][1:]}")
        out += ["", f"### {t['oos']}"] + [f"- {s}" for s in t["oos_generic"]]
        for rule in rules:
            if rule["id"] in OOS_EXTRA:
                out.append(f"- {OOS_EXTRA[rule['id']][a.lang]}")
        others = [y["r"]["id"] for y in top if y is not x]
        if others:
            out.append("- " + ("Kendi görev kartı olan gereksinimler: " if a.lang == "tr" else
                               "Requirements with their own charter: ") + ", ".join(others))
        out += ["", f"_{t['sheet'].format(req=r['id'])}_", ""]
    write(Path(a.out), "\n".join(out))
    print(f"wrote {a.out}: {len(top)} charter(s) from {len(rows)} active requirement(s), {total} min planned")
    for i, x in enumerate(top, 1):
        print(f"  CH-{i:02d} {x['r']['id']} score={x['score'] if x['has'] else '-'} {x['level']} {x['box']} min")
    return 0


# ---------------------------------------------------------------- session sheets

def parse_duration(v: str) -> int | None:
    v = (v or "").strip().lower()
    m = re.match(r"^(\d+)\s*(?:m|min|mins|minutes|dk|dakika)?$", v)
    if m:
        return int(m.group(1))
    m = re.match(r"^(\d+):(\d{2})$", v)
    if m:
        return int(m.group(1)) * 60 + int(m.group(2))
    m = re.match(r"^(\d+)\s*(?:h|sa|saat)\s*(?:(\d+)\s*(?:m|min|dk)?)?$", v)
    if m:
        return int(m.group(1)) * 60 + int(m.group(2) or 0)
    return None


def parse_session(path: Path) -> tuple[dict, list[str], list[str]]:
    """Returns (session, errors, warnings)."""
    text = path.read_text(encoding="utf-8-sig")
    s = {"file": path.name, "id": path.stem, "header": {}, "notes": [], "reqs": []}
    errors, warns = [], []
    in_comment = False
    for no, raw in enumerate(text.splitlines(), 1):
        line = raw.rstrip()
        if "<!--" in line and "-->" not in line.split("<!--", 1)[1]:
            in_comment = True
            continue
        if in_comment:
            if "-->" in line:
                in_comment = False
            continue
        stripped = re.sub(r"<!--.*?-->", "", line).strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("|") or stripped == "---":
            continue
        m = NOTE_RE.match(line)
        tag = TAG_ALIASES.get(m.group("tag").upper()) if m else None
        if m and tag:
            note = {"tag": tag, "time": (m.group("time") or "").replace(".", ":"), "text": clean_text(m.group("text")),
                    "reqs": REQ_RE.findall(m.group("reqs") or "") or [], "detail": {}, "extra": [], "line": no}
            if not note["text"]:
                warns.append(f"{path.name}:{no}: empty {tag} note")
            s["notes"].append(note)
            continue
        if raw[:1] in (" ", "\t") and s["notes"]:
            cur = s["notes"][-1]
            dm = re.match(r"^\s*(?:[-*+]\s+)?([^\W\d_][\w ]*?)\s*:\s*(.+)$", line)
            nm = re.match(r"^\s*(?:\d+[.)]|[-*+])\s+(.+)$", line)
            key = DETAIL_KEYS.get(dm.group(1).strip().lower()) if dm else None
            if key == "steps":
                cur["detail"].setdefault("steps", []).extend(
                    cap(x.strip()) for x in re.split(r";\s*|\s+->\s+", dm.group(2)) if x.strip())
            elif key:
                cur["detail"][key] = clean_text(dm.group(2))
            elif nm and cur["tag"] == "BUG":
                cur["detail"].setdefault("steps", []).append(cap(clean_text(nm.group(1))))
            else:
                cur["extra"].append(clean_text(stripped.lstrip("-*+ ")))
            continue
        if not s["notes"]:
            pairs = re.split(r"\s{2,}(?=[^\W\d_][\w ]*:)", stripped.lstrip("-*+ "))
            known = False
            for pair in pairs:
                hm = re.match(r"^([^\W\d_][\w ]*?)\s*:\s*(.*)$", pair.strip())
                key = HEADER_KEYS.get(hm.group(1).strip().lower()) if hm else None
                if key:
                    known = True
                    s["header"][key] = hm.group(2).strip()
            if known:
                continue
        warns.append(f"{path.name}:{no}: untagged line kept as NOTE: {stripped[:60]}")
        s["notes"].append({"tag": "NOTE", "time": "", "text": clean_text(stripped), "reqs": [], "detail": {},
                           "extra": [], "line": no})
    h = s["header"]
    if h.get("session"):
        s["id"] = h["session"]
    if not h.get("charter"):
        errors.append(f"{path.name}: missing 'charter:' line")
    s["duration"] = parse_duration(h.get("duration", ""))
    if s["duration"] is None:
        errors.append(f"{path.name}: missing or unreadable 'duration:' (minutes, e.g. 90, 1h30, 1:30)")
    elif not 30 <= s["duration"] <= 180:
        warns.append(f"{path.name}: duration {s['duration']} min is outside the usual 60-120 min SBTM session; "
                     "split long sessions, merge very short ones")
    s["reqs"] = REQ_RE.findall(h.get("req", ""))
    if not s["reqs"]:
        warns.append(f"{path.name}: no 'req:' IDs - findings cannot be traced to requirements")
    s["tbs"] = None
    if h.get("tbs"):
        nums = [int(x) for x in re.findall(r"\d+", h["tbs"])]
        if len(nums) == 3 and sum(nums) == 100:
            s["tbs"] = tuple(nums)
        else:
            warns.append(f"{path.name}: 'tbs: {h['tbs']}' ignored - write three percentages summing to 100, e.g. 60/25/15")
    s["opp"] = None
    if h.get("opportunity"):
        om = re.search(r"\d+", h["opportunity"])
        if om and 0 <= int(om.group()) <= 100:
            s["opp"] = int(om.group())
    if not any(n["tag"] == "COVERED" for n in s["notes"]):
        warns.append(f"{path.name}: no COVERED notes - coverage cannot be reported for this session")
    for n in s["notes"]:
        if not n["reqs"]:
            detail = " ".join([n["text"]] + [v if isinstance(v, str) else " ".join(v) for v in n["detail"].values()]
                              + n["extra"])
            n["reqs"] = list(dict.fromkeys(REQ_RE.findall(detail))) or list(s["reqs"])
    return s, errors, warns


def cap(v: str) -> str:
    return v[:1].upper() + v[1:]


def clean_text(v: str) -> str:
    return re.sub(r"\s+", " ", (v or "").strip())


def compact_safe(v: str) -> str:
    """Text that cannot break the compact format (pipes, arrows, bracket data groups)."""
    return clean_text(v).replace(" | ", " / ").replace("=>", "->").replace("[", "(").replace("]", ")")


def cell(v) -> str:
    return str(v).replace("|", "/").replace("\n", " ")


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text.rstrip("\n") + "\n")


def next_tc(a) -> int:
    if a.start:
        return a.start
    if a.tests and Path(a.tests).exists():
        data = json.loads(Path(a.tests).read_text(encoding="utf-8-sig"))
        ids = [int(m.group(1)) for x in data.get("test_cases", []) if (m := re.match(r"TC-(\d+)", x.get("id", "")))]
        return max(ids) + 1 if ids else 1
    return 1


NEG_KW = ["invalid", "reject", "expired", "empty", "wrong", "negative", "over the limit", "exceed", "missing",
          "without", "another user", "unauthor", "gecersiz", "reddet", "reddedil", "suresi dol", "bos", "hatali", "yanlis", "eksik",
          "asan", "asim", "olmadan", "baska kullanici", "yetkisiz"]
TECH_KW = [("bva", ["boundary", "limit", "minimum", "maximum", "min ", "max ", "just below", "just above", "sinir",
                    "alt sinir", "ust sinir", "en az", "en fazla"]),
           ("st", ["state", "status", "back button", "refresh", "twice", "double", "second tab", "timeout", "cancel",
                   "durum", "geri tus", "yenile", "iki kez", "cift", "ikinci sekme", "zaman asimi", "iptal"])]
CAT_KW = [("security", ["another user", "role", "permission", "token", "authoriz", "admin", "leak", "baska kullanici",
                        "rol", "yetki", "sizinti"]),
          ("performance", ["slow", "timeout", "latency", "yavas", "zaman asimi"]),
          ("accessibility", ["screen reader", "keyboard", "contrast", "accessib", "ekran okuyucu", "klavye", "kontrast"]),
          ("api", ["api", "endpoint", "http ", "status code"]),
          ("usability", ["confusing", "unclear", "kafa karis", "anlasilmaz"])]


def first_match(text: str, table, default: str) -> str:
    for key, kws in table:
        if any(matches(text, k) for k in kws):
            return key
    return default


def cmd_report(a) -> int:
    t = T[a.lang]
    sessions, errors, warns = [], [], []
    for p in a.sessions:
        path = Path(p)
        try:
            s, e, w = parse_session(path)
        except OSError as ex:
            print(f"error: {ex}", file=sys.stderr)
            return 2
        sessions.append(s)
        errors += e
        warns += w
    ids = [s["id"] for s in sessions]
    for dup in sorted({i for i in ids if ids.count(i) > 1}):
        errors.append(f"duplicate session id '{dup}' - give each sheet a unique 'session:' or file name")
    if errors:
        print("invalid session sheet(s), nothing written:", file=sys.stderr)
        for e in errors:
            print(f"  {e}", file=sys.stderr)
        return 1
    reqs = {}
    if a.requirements:
        try:
            reqs = {r["id"]: r for r in json.loads(Path(a.requirements).read_text(encoding="utf-8-sig")).get("requirements", [])}
        except (OSError, ValueError) as ex:
            print(f"error: cannot read requirements: {ex}", file=sys.stderr)
            return 2
    for s in sessions:
        for rid in sorted({x for n in s["notes"] for x in n["reqs"]} | set(s["reqs"])):
            if reqs and rid not in reqs:
                warns.append(f"{s['file']}: {rid} is not in {Path(a.requirements).name}")
    n_tc = next_tc(a)
    out_dir = Path(a.out_dir)

    # candidate tests + defect drafts (assign IDs first so the summary can link them)
    cand = [t["cand_head"]]
    defects = [f"# {t['def_title']}", "", t["def_intro"]]
    titles: set[str] = set()
    d_no = 0
    for s in sessions:
        env = " / ".join(x for x in (s["header"].get("env"), s["header"].get("build")) if x)
        for n in s["notes"]:
            if n["tag"] not in ("BUG", "IDEA"):
                continue
            tid = f"TC-{n_tc:03d}"
            n_tc += 1
            n["tc"] = tid
            ftext = fold(" ".join([n["text"], n["detail"].get("expected", "")] + n["detail"].get("steps", [])))
            req = n["reqs"][0] if n["reqs"] else ""
            linked = [reqs[r] for r in n["reqs"] if r in reqs]
            pri = min((x.get("priority") for x in linked if x.get("priority") in PRI_RANK),
                      key=lambda p: PRI_RANK[p], default=None)
            sev = SEVERITIES.get(n["detail"].get("severity", "").split()[0].lower()) if n["detail"].get("severity") else None
            if n["tag"] == "BUG" and sev:
                pri = sev if pri is None or PRI_RANK[sev] < PRI_RANK[pri] else pri
            pri = PRI_SHORT.get(pri or "medium", "m")
            pol = "-" if any(matches(ftext, k) for k in NEG_KW) else "+"
            tech = first_match(ftext, TECH_KW, "eg")
            cat = first_match(ftext, CAT_KW, "functional")
            title = compact_safe(t["reg"].format(text=n["text"]) if n["tag"] == "BUG" else n["text"]) or tid
            base, k = title, 2
            while title.casefold() in titles:
                title, k = f"{base} ({k})", k + 1
            titles.add(title.casefold())
            when = n["time"] or f"line {n['line']}"
            ref = compact_safe(f"{s['id']} {n['time']}".strip())
            obj = t["obj_bug" if n["tag"] == "BUG" else "obj_idea"].format(s=s["id"], t=when)
            req_line = ", ".join(n["reqs"])
            cand += ["", f"## {tid} | {title}",
                     (f"req: {req_line} | " if req_line else "") + f"pri: {pri} | pol: {pol} | tech: {tech} | ref: {ref} | cat: {cat}",
                     f"obj: {compact_safe(obj)}"]
            if env:
                cand.append(f"pre: {compact_safe(t['pre_env'].format(env=env))}")
            if n["tag"] == "BUG":
                steps = n["detail"].get("steps") or [t["p_step"].format(text=n["text"])]
            else:
                steps = [t["i_step"].format(text=n["text"])]
            exp_final = n["detail"].get("expected") or (t["e_final"].format(req=req) if req else t["e_final_none"])
            data = compact_safe(n["detail"].get("data", "")).replace("(", "").replace(")", "")
            for i, st in enumerate(steps, 1):
                last = i == len(steps)
                d = f" [{data}]" if data and last else ""
                cand.append(f"{i}. {compact_safe(st)}{d} => {compact_safe(exp_final) if last else t['e_step']}")
            tags = ["regression", "from-exploratory"] if n["tag"] == "BUG" else ["from-exploratory", "idea"]
            if not n["reqs"]:  # qa_compact accepts untraced tests only when tagged exploratory
                tags.append("exploratory")
                warns.append(f"{s['file']}: {tid} has no REQ ID - link it before setting status ready")
            auto = f"yes, {t['auto_reason']}" if n["tag"] == "BUG" else f"no, {t['auto_idea']}"
            cand.append(f"tags: {', '.join(tags)} | auto: {auto} | status: draft")
            if n["tag"] != "BUG":
                continue
            d_no += 1
            n["defect"] = f"D-{d_no:02d}"
            det = n["detail"]
            sev_line = SEVERITIES.get(det.get("severity", "").split()[0].lower()) if det.get("severity") else None
            if not sev_line:
                sev_line = t["p_sev"]
                imp = [(r["id"], int((r.get("risk") or {}).get("impact") or 0)) for r in linked]
                imp = [x for x in imp if x[1]]
                if imp:
                    rid, i_ = max(imp, key=lambda x: x[1])
                    sug = {5: "critical", 4: "high", 3: "medium"}.get(i_, "low")
                    sev_line += t["sev_hint"].format(req=rid, i=i_, s=sug)
            exp = det.get("expected")
            if not exp:
                exp = t["p_exp_req"].format(req=req, text=reqs[req].get("text", "")) if req in reqs else t["p_exp"]
            defects += ["", f"## {n['defect']} · {n['text']}", "",
                        f"- **{t['f_session']}:** {s['id']} ({s['file']}), {when} - {s['header'].get('charter', '')}",
                        f"- **{t['f_linked']}:** {', '.join(n['reqs']) or '-'} · {tid}",
                        f"- **{t['f_env']}:** {env or t['p_env']}",
                        f"- **{t['f_sev']}:** {sev_line}",
                        f"- **{t['f_pri']}:** {t['p_pri']}",
                        f"- **{t['f_pre']}:** {t['p_pre']}",
                        f"- **{t['f_steps']}:**"]
            for i, st in enumerate(det.get("steps") or [t["p_step"].format(text=n["text"])], 1):
                defects.append(f"  {i}. {st}")
            if det.get("data"):
                defects.append(f"  - data: {det['data']}")
            defects += [f"- **{t['f_exp']}:** {exp}",
                        f"- **{t['f_act']}:** {det.get('actual') or t['p_act']}",
                        f"- **{t['f_repro']}:** {det.get('repro') or t['p_repro']}",
                        f"- **{t['f_evid']}:** {det.get('evidence') or t['p_evid'].format(time=when)}"]
            if n["extra"]:
                defects.append(f"- **{t['f_notes']}:** " + " / ".join(n["extra"]))
    if d_no == 0:
        defects += ["", t["none"]]

    # summary
    total = sum(s["duration"] for s in sessions)
    sm = [f"# {t['sum_title']}", "", f"## {t['totals']}", "",
          t["tot_duration"].format(n=len(sessions), m=total, h=round(total / 60, 1))]
    rec = [s for s in sessions if s["tbs"]]
    if rec:
        w = sum(s["duration"] for s in rec) or 1
        avg = [round(sum(s["tbs"][i] * s["duration"] for s in rec) / w) for i in range(3)]
        sm.append(t["tbs_line"].format(k=len(rec), n=len(sessions), t=avg[0], b=avg[1], s=avg[2]))
    else:
        sm.append(t["tbs_none"])
    orec = [s for s in sessions if s["opp"] is not None]
    if orec:
        w = sum(s["duration"] for s in orec) or 1
        sm.append(t["opp_line"].format(o=round(sum(s["opp"] * s["duration"] for s in orec) / w)))
    counts = {tag: sum(1 for s in sessions for n in s["notes"] if n["tag"] == tag) for tag in TAGS}
    sm += ["", f"**{t['tag_counts']}:** " + " · ".join(f"{k} {v}" for k, v in counts.items()), "",
           f"## {t['sessions']}", "", t["sess_cols"], "|" + "---|" * 12]
    for s in sessions:
        c = {tag: sum(1 for n in s["notes"] if n["tag"] == tag) for tag in TAGS}
        tbs = " / ".join(map(str, s["tbs"])) if s["tbs"] else t["not_rec"]
        sm.append(f"| {cell(s['id'])} | {cell(s['header'].get('charter', ''))} | {cell(s['header'].get('tester', '-'))} | "
                  f"{cell(s['header'].get('start', '-'))} | {s['duration']} | {tbs} | "
                  f"{s['opp'] if s['opp'] is not None else '-'} | {c['BUG']} | {c['ISSUE']} | {c['QUESTION']} | "
                  f"{c['IDEA']} | {c['COVERED']} |")

    def listing(tag, title, extra=None):
        rows = [(s, n) for s in sessions for n in s["notes"] if n["tag"] == tag]
        out = ["", f"## {title}", ""]
        if not rows:
            return out + [t["none"]]
        for s, n in rows:
            suffix = f" → {n['tc']}" if extra and n.get("tc") else ""
            out.append(f"- [{s['id']} {n['time'] or 'line ' + str(n['line'])}] {n['text']}"
                       + (f" ({', '.join(n['reqs'])})" if n["reqs"] else "") + suffix)
        return out

    sm += ["", f"## {t['bugs']}", ""]
    bugs = [(s, n) for s in sessions for n in s["notes"] if n["tag"] == "BUG"]
    if bugs:
        sm += [t["bug_cols"], "|---|---|---|---|---|---|"]
        for s, n in bugs:
            sm.append(f"| {cell(s['id'])} | {n['time'] or '-'} | {cell(n['text'])} | {', '.join(n['reqs']) or '-'} | "
                      f"{n['defect']} | {n['tc']} |")
    else:
        sm.append(t["none"])
    sm += listing("ISSUE", t["issues"]) + listing("QUESTION", t["questions"]) + listing("IDEA", t["ideas"], True)
    sm += ["", f"## {t['coverage']}", "", t["cov_cols"], "|---|---|---|---|---|"]
    all_reqs = sorted({r for s in sessions for r in s["reqs"]} | {r for s in sessions for n in s["notes"] for r in n["reqs"]})
    for rid in all_reqs:
        ss = [s for s in sessions if rid in s["reqs"]]
        b = sum(1 for s in sessions for n in s["notes"] if n["tag"] == "BUG" and rid in n["reqs"])
        q = sum(1 for s in sessions for n in s["notes"] if n["tag"] == "QUESTION" and rid in n["reqs"])
        title = f" {cell(reqs[rid].get('title', ''))}" if rid in reqs else ""
        sm.append(f"| {rid}{title} | {', '.join(cell(s['id']) for s in ss) or '-'} | {sum(s['duration'] for s in ss)} | {b} | {q} |")
    if not all_reqs:
        sm.append("| - | - | - | - | - |")
    sm += listing("COVERED", t["covered_notes"])
    sm += ["", f"## {t['debrief']}", ""]
    for s in sessions:
        c = {tag: sum(1 for n in s["notes"] if n["tag"] == tag) for tag in TAGS}
        tbs = "T/B/S " + "/".join(map(str, s["tbs"])) if s["tbs"] else "TBS " + t["not_rec"]
        sm.append(f"**{s['id']}**")
        for name, prompt in t["proof"]:
            sm.append(f"- {name}: " + prompt.format(tbs=tbs, bugs=c["BUG"], reqs=", ".join(s["reqs"]) or "-",
                                                    issues=c["ISSUE"], ideas=c["IDEA"], qs=c["QUESTION"]))
        sm.append("")
    if warns:
        sm += [f"## {t['warn_title']}", ""] + [f"- {w}" for w in warns]
    write(out_dir / "session-summary.md", "\n".join(sm))
    write(out_dir / "defects.md", "\n".join(defects))
    write(out_dir / "candidate-tests.src.md", "\n".join(cand))
    n_c = sum(1 for s in sessions for n in s["notes"] if n.get("tc"))
    print(f"{len(sessions)} session(s), {total} min · " + " · ".join(f"{k} {v}" for k, v in counts.items()))
    print(f"wrote {out_dir / 'session-summary.md'}, {out_dir / 'defects.md'} ({d_no} draft(s)), "
          f"{out_dir / 'candidate-tests.src.md'} ({n_c} test case(s))")
    for w in warns:
        print(f"warning: {w}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("charters", help="risk-ranked exploratory charters from requirements.json")
    c.add_argument("--requirements", required=True)
    c.add_argument("--top", type=int, default=10, help="number of charters (default 10; 0 = all)")
    c.add_argument("--timebox", type=int, default=90, help="minutes for high/medium risk (default 90)")
    c.add_argument("--lang", choices=["tr", "en"], default="en")
    c.add_argument("--out", required=True)
    r = sub.add_parser("report", help="session sheets -> summary, defect drafts, candidate test cases")
    r.add_argument("sessions", nargs="+", help="session sheet(s) (.md)")
    r.add_argument("--tests", help="existing test-cases.json to continue TC numbering")
    r.add_argument("--start", type=int, help="first TC number (overrides --tests)")
    r.add_argument("--requirements", help="requirements.json: priorities, severity hints, expected-result quotes")
    r.add_argument("--lang", choices=["tr", "en"], default="en")
    r.add_argument("--out-dir", required=True)
    sys.stdout.reconfigure(encoding="utf-8")
    a = ap.parse_args()
    if a.cmd == "charters":
        if a.top < 0 or a.timebox <= 0:
            ap.error("--top must be >= 0 and --timebox > 0")
        return cmd_charters(a)
    if a.start is not None and a.start < 1:
        ap.error("--start must be >= 1")
    return cmd_report(a)


if __name__ == "__main__":
    sys.exit(main())
