# Katkı rehberi / Contributing

**[English below ↓](#english)**

## Türkçe

Katkılarınız memnuniyetle karşılanır: hata bildirimi, içe aktarma sorunu, kör deneme raporu, sektör paketi önerisi ya da kod. Lütfen yalnızca **sentetik veya anonimleştirilmiş** veri paylaşın. Gerçek müşteri verisi, iç sistem adresi ya da gizli iş kuralı içeren issue'lar silinir.

### Kontrolleri koşturma
Python 3.12 veya 3.13 yeterli; başka bir paket gerekmez. CI, Linux üzerinde Python 3.12 ile aynı üç adımı koşar:
```bash
python tools/sync_shared.py          # shared/ dosyalarını skill'lere dağıtır (CI: --check)
python tools/validate_skills.py      # Agent Skills spesifikasyonu ve paket kuralları; 0 hata olmalı
python -m unittest discover -s tests # script regresyon testleri
```

### Issue açma
[Issue şablonlarından](https://github.com/alinurettin/testskills/issues/new/choose) birini seçin:
- **Hata:** Bir skill ya da script yanlış çalışıyor.
- **İçe aktarma başarısız:** Bir Xray, Zephyr, TestRail, Azure DevOps, Qase ya da Excel dosyası araca aktarılamadı. Aracın sürümü ve hata mesajı en değerli bilgidir; bu içe aktarımlar henüz gerçek sunucularda denenmedi.
- **Deneme raporu:** Bir skill'i gerçek bir işte ya da kör denemede kullandınız ve sonucu paylaşmak istiyorsunuz.
- **Sektör paketi isteği:** Yeni bir sektör için mevzuat ve kontrol listesi önerisi.

### Yeni bir skill önermek
Kod yazmadan önce bir issue açın. Issue'da iki şey olmalı:
1. **Birbirinden bağımsız 3 istek.** Farklı kişilerden ya da ekiplerden gelen, mevcut 17 skill'in karşılamadığı 3 gerçek istek (anonimleştirilmiş alıntı ya da bağlantı).
2. **Kör deneme tasarımı.**
   - ajana verilecek girdiler;
   - yerleştirilecek hatalar ya da beklenen bulgular;
   - yanlış alarm tuzakları;
   - `evals/keys/` altında tutulacak cevap anahtarı;
   - puanlama yöntemi.

   Kurallar: [evals/README.md](evals/README.md).

Bu ikisi netleşmeden gelen yeni skill PR'ları kabul edilmez. Mevcut bir skill'i genişletmek çoğu zaman daha iyi bir yoldur.

### Açıklama (description) bütçesi
Skill açıklamaları, Claude'un skill seçerken okuduğu ve karakter bütçesi sınırlı olan listede durur. Kurallar [docs/DESCRIPTIONS.md](docs/DESCRIPTIONS.md) dosyasındadır:
- açıklama başına en fazla 480 karakter;
- 17 skill için toplam en fazla 7.500 karakter;
- her tetikleyici terim yalnızca bir skill'de bulunur.

Değişiklikten sonra `python tools/validate_skills.py` ile ölçün.

### Stil
- **SKILL.md:**
  - frontmatter'da yalnızca `name`, `description`, `license`, `metadata` anahtarları;
  - gövde 500 satırın altında;
  - gövdede adı geçen her `scripts/`, `references/`, `assets/` yolu o skill'in içinde gerçekten bulunmalı.
- **Paylaşılan dosyalar:** `skills/*/scripts/qa_compact.py`, `tr_ids.py`, `junit_results.py`, `references/data-model.md` ve `references/domains/*` kopyadır. Kaynağı `shared/` altında düzenleyin, sonra `python tools/sync_shared.py` çalıştırın.
- **Script'ler:**
  - yalnızca standart kütüphane; ağ erişimi yok;
  - Python 3.12 ve 3.13'te çalışmalı;
  - `sys.stdout.reconfigure(encoding="utf-8")` çağrısı `parse_args()`'tan önce gelir;
  - dosyalar `encoding="utf-8"` ve `newline="\n"` ile yazılır.
- **Testler:** Yeni testler `tests/test_<konu>.py` dosyasına, fixture'lar `tests/fixtures/<konu>/` klasörüne.
- **Veri:** Yalnızca sentetik veri. E-postalar `example.com` / `example.test` alan adını kullanır; TCKN, VKN ve IBAN'lar paketteki üreticilerden gelir.
- **Dokümanlar:** Türkçe ve İngilizce birlikte güncellenir; kısa cümleler, abartısız iddialar. Sayılar değişirse `docs/EVALUATION*.md` ve `CHANGELOG.md` de güncellenir.

---

## English

Contributions are welcome: bug reports, import problems, trial reports, domain-pack proposals and code. Please share **synthetic or anonymised** data only. Issues that contain real customer data, internal system addresses or confidential business rules will be deleted.

### Running the checks
Python 3.12 or 3.13 is enough; no packages are needed. CI runs the same three steps with Python 3.12 on Linux:
```bash
python tools/sync_shared.py          # copies shared/ files into the skills (CI: --check)
python tools/validate_skills.py      # Agent Skills spec and suite rules; must report 0 errors
python -m unittest discover -s tests # script regression tests
```

### Opening an issue
Pick one of the [issue templates](https://github.com/alinurettin/testskills/issues/new/choose):
- **Bug:** a skill or a script does the wrong thing.
- **Import failed:** an Xray, Zephyr, TestRail, Azure DevOps, Qase or Excel file did not import. The tool version and the error message are the most valuable details; these imports have not yet been tried against real servers.
- **Trial report:** you used a skill on real work or in a blind trial and want to share the result.
- **Domain pack request:** a regulations and checklist proposal for a new industry.

### Proposing a new skill
Open an issue before writing code. The issue needs two things:
1. **Three independent requests.** Three real requests from different people or teams that none of the 17 skills covers (anonymised quotes or links).
2. **A blind trial design.**
   - the inputs the agent will get;
   - the planted defects or expected findings;
   - the false-positive traps;
   - an answer key kept in `evals/keys/`;
   - how the run will be graded.

   Rules: [evals/README.md](evals/README.md).

Pull requests for new skills without both are not accepted. Extending an existing skill is often the better route.

### Description budget
Skill descriptions sit in the listing Claude reads when it picks a skill, and that listing has a character budget. The rules are in [docs/DESCRIPTIONS.md](docs/DESCRIPTIONS.md):
- at most 480 characters per description;
- at most 7,500 characters for all 17 skills;
- each trigger term belongs to exactly one skill.

Measure with `python tools/validate_skills.py` after every change.

### Style
- **SKILL.md:**
  - frontmatter keys `name`, `description`, `license` and `metadata` only;
  - a body under 500 lines;
  - every `scripts/`, `references/` or `assets/` path named in the body must exist inside that skill.
- **Shared files:** `skills/*/scripts/qa_compact.py`, `tr_ids.py`, `junit_results.py`, `references/data-model.md` and `references/domains/*` are copies. Edit the source in `shared/`, then run `python tools/sync_shared.py`.
- **Scripts:**
  - standard library only, and no network access;
  - they must run on Python 3.12 and 3.13;
  - call `sys.stdout.reconfigure(encoding="utf-8")` before `parse_args()`;
  - write files with `encoding="utf-8"` and `newline="\n"`.
- **Tests:** new tests go in `tests/test_<topic>.py`, fixtures in `tests/fixtures/<topic>/`.
- **Data:** synthetic only. E-mail addresses use `example.com` or `example.test`; TCKN, VKN and IBAN values come from the bundled generators.
- **Docs:** update Turkish and English together. Use short sentences and no inflated claims. When numbers change, update `docs/EVALUATION*.md` and `CHANGELOG.md` too.
