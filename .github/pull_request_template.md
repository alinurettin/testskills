## Ne değişti? / What changed?


## Neden? / Why?
<!-- İlgili issue / Related issue: #... -->


## Kontroller / Checks
- [ ] `python tools/sync_shared.py` (paylaşılan dosyaları `shared/` altında düzenledim / I edited shared files in `shared/`, not the synced copies)
- [ ] `python tools/validate_skills.py` → 0 hata / 0 errors
- [ ] `python -m unittest discover -s tests` → hepsi geçti / all pass
- [ ] Script değiştiyse: yalnızca standart kütüphane, Python 3.12 ve 3.13, UTF-8 çıktı, yeni ya da güncel testler / If a script changed: standard library only, Python 3.12 and 3.13, UTF-8 output, new or updated tests
- [ ] SKILL.md değiştiyse: gövde < 500 satır, açıklama [docs/DESCRIPTIONS.md](https://github.com/alinurettin/testskills/blob/main/docs/DESCRIPTIONS.md) bütçesinde, adı geçen yollar mevcut / If a SKILL.md changed: body < 500 lines, description within the [docs/DESCRIPTIONS.md](https://github.com/alinurettin/testskills/blob/main/docs/DESCRIPTIONS.md) budget, every named path exists
- [ ] Yalnızca sentetik veri / Synthetic data only
- [ ] Davranış ya da sayılar değiştiyse TR ve EN dokümanlar ile `CHANGELOG.md` güncellendi / If behaviour or numbers changed, the TR and EN docs and `CHANGELOG.md` are updated
- [ ] Yeni skill ise: 3 bağımsız istek ve kör deneme tasarımı içeren issue bağlandı / If this is a new skill: the linked issue has 3 independent requests and a blind trial design ([CONTRIBUTING.md](https://github.com/alinurettin/testskills/blob/main/CONTRIBUTING.md))

## Kanıt / Evidence
<!-- Test çıktısı, örnek girdi/çıktı, deneme sonucu. / Test output, sample input/output, trial result. -->
