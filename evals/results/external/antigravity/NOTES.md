# Kör Değerlendirme Çalıştırma Notları (`testskills` `v0.11.2`)

## 1. Ortam, Araç, Model, Tarih ve İnternet Durumu

- **Araç:** Google Antigravity masaüstü uygulaması, sürüm `44.4.3` (alt-ajan mekanizması: `define_subagent` / `invoke_subagent`, rol şablonu `qa-eval-runner`), Windows işletim sistemi üzerinde çalıştırıldı. Yardımcı çalışma zamanları: Node.js `v24.19.0`, Python `3.13.15`.
- **Tam model adı:** Antigravity ayarlarında görünen insan-okur model seçimi `Gemini 4 Hydrogen (XHigh)` (`Model: inherit`). Sağlayıcı API'sinin iç tam model kimliği (exact API model ID string) bu oturuma açıkça yansıtılmadığı için **bilinmiyor**.
- **Tarih:** `2026-11-16` ve `2026-11-17` (yerel saat `UTC+03:00`).
  - Nihai tutulan `skill` koşuları: `2026-11-16 18:11:35 +03:00` – `2026-11-16 23:25:24 +03:00`
  - Nihai tutulan `noskill` koşuları: `2026-11-17 00:21:20 +03:00` – `2026-11-17 00:48:36 +03:00`
- **İnternet açık mıydı:** Evet, makinede ve çalıştırma ortamında internet bağlantısı açıktı (hazırlık aşamasında GitHub'dan `git clone` ile depo klonlandı; ağ/güvenlik duvarı düzeyinde dış bağlantı engeli yoktu). Ancak tüm alt-ajanlara hem sistem istemi hem kullanıcı istemiyle internete çıkmamaları söylendi; 18 nihai alt-ajan dökümünün tamamında harici URL erişimi (`ext_urls=[]`) tespit edilmedi.
- **Kapsam & Puanlama Notu:** Değerlendirme kör bırakıldı; `repo/evals/keys/` altındaki hiçbir dosya açılmadı, puanlama yapılmadı ve `report.json` / gözlem dosyası üretilmedi.
- **Ek dosyalar:** `tools/eval_harness.py` kullanılmadığı için `*.manifest.json` dosyası üretilmemiştir. Antigravity'nin iç hesap/oturum durumu dosyaları (`antigravity_state.pbtxt`, `installation_id`, `conversation_summaries.db`) güvenlik gerekçesiyle kopyalanmamıştır; sunucu başlatma betiği (`start-servers`) eklenmiştir.

---

## 2. Koşular Tablosu (Nihai Tutulan 18 Koşu)

Tüm sunuculu koşulara ait sunucu kodları çalışma alanları dışındaki `./servers/<run_id>/` klasörlerine kopyalandı ve her koşu için bağımsız bir Node.js süreci `./start-servers --foreground` ile başlatıldı. Hiçbir sunucu aynı anda birden fazla koşu tarafından paylaşılmadı.

> **Sunucu yeniden başlatma notu (`trial-api2`):** `trial-api2` sunucusu (`server.js`), kasıtlı yerleştirilen hata gereği `null` JSON gövdesi gibi girdilerde süreç çökmesi (`exit code 1`) yaşamaktadır. `./start-servers --foreground` bu durumlarda yalnızca çöken koşunun sunucusunu ~0,3 sn içinde otomatik olarak taze süreçle yeniden başlatmıştır (diğer koşular etkilenmemiştir). Nihai koşu sırasında gerçekleşen otomatik çökme-toparlama sayıları tabloda ayrıca belirtilmiştir.

| run_id | deneme | kol | başlangıç saati (+03:00) | bitiş saati (+03:00) | sunucu adresi ve portu | aynı anda paylaşan diğer koşular | koşudan önce sunucu yeniden başlatıldı mı |
|---|---|---|---|---|---|---|---|
| `R01` | `trial-api2` | `noskill` | `2026-11-17 00:21:20` | `2026-11-17 00:27:16` | `http://localhost:4101` | Hiçbiri (tekil izole sunucu) | Evet (yeniden koşum öncesi taze başlatıldı; koşu içinde çökme kaynaklı 5 otomatik yeniden başlatma) |
| `R02` | `trial-design` | `skill` | `2026-11-16 18:11:35` | `2026-11-16 18:24:22` | Yok (sunucusuz) | Yok | Yok (sunucusuz) |
| `R03` | `trial-design` | `noskill` | `2026-11-17 00:21:21` | `2026-11-17 00:30:19` | Yok (sunucusuz) | Yok | Yok (sunucusuz) |
| `R04` | `trial-api2` | `noskill` | `2026-11-17 00:21:23` | `2026-11-17 00:25:12` | `http://localhost:4102` | Hiçbiri (tekil izole sunucu) | Evet (yeniden koşum öncesi taze başlatıldı; koşu içinde çökme kaynaklı 3 otomatik yeniden başlatma) |
| `R05` | `trial-design` | `skill` | `2026-11-16 18:11:48` | `2026-11-16 18:27:04` | Yok (sunucusuz) | Yok | Yok (sunucusuz) |
| `R06` | `trial-exploratory` | `noskill` | `2026-11-17 00:21:30` | `2026-11-17 00:33:48` | `http://127.0.0.1:4103` | Hiçbiri (tekil izole sunucu) | Evet (yeniden koşum öncesi taze başlatıldı; koşu içinde çökme olmadı) |
| `R07` | `trial-design` | `skill` | `2026-11-16 18:27:49` | `2026-11-16 18:43:36` | Yok (sunucusuz) | Yok | Yok (sunucusuz) |
| `R08` | `trial-exploratory` | `noskill` | `2026-11-17 00:21:31` | `2026-11-17 00:32:26` | `http://127.0.0.1:4104` | Hiçbiri (tekil izole sunucu) | Evet (yeniden koşum öncesi taze başlatıldı; koşu içinde çökme olmadı) |
| `R09` | `trial-design` | `noskill` | `2026-11-17 00:34:22` | `2026-11-17 00:41:37` | Yok (sunucusuz) | Yok | Yok (sunucusuz) |
| `R10` | `trial-api2` | `skill` | `2026-11-16 18:28:07` | `2026-11-16 18:35:41` | `http://localhost:4105` | Hiçbiri (tekil izole sunucu) | Evet (koşu öncesi taze başlatıldı; koşu içinde çökme kaynaklı 4 otomatik yeniden başlatma) |
| `R11` | `trial-api2` | `skill` | `2026-11-16 18:28:09` | `2026-11-16 18:36:14` | `http://localhost:4106` | Hiçbiri (tekil izole sunucu) | Evet (koşu öncesi taze başlatıldı; koşu içinde çökme kaynaklı 7 otomatik yeniden başlatma) |
| `R12` | `trial-exploratory` | `skill` | `2026-11-16 18:28:11` | `2026-11-16 18:41:56` | `http://127.0.0.1:4107` | Hiçbiri (tekil izole sunucu) | Evet (koşu öncesi taze başlatıldı; koşu içinde çökme olmadı) |
| `R13` | `trial-api2` | `skill` | `2026-11-16 18:44:07` | `2026-11-16 18:50:37` | `http://localhost:4108` | Hiçbiri (tekil izole sunucu) | Evet (koşu öncesi taze başlatıldı; koşu içinde çökme olmadı) |
| `R14` | `trial-design` | `noskill` | `2026-11-17 00:34:28` | `2026-11-17 00:43:19` | Yok (sunucusuz) | Yok | Yok (sunucusuz) |
| `R15` | `trial-api2` | `noskill` | `2026-11-17 00:34:30` | `2026-11-17 00:40:55` | `http://localhost:4109` | Hiçbiri (tekil izole sunucu) | Evet (yeniden koşum öncesi taze başlatıldı; koşu içinde çökme kaynaklı 4 otomatik yeniden başlatma) |
| `R16` | `trial-exploratory` | `skill` | `2026-11-16 23:12:32` | `2026-11-16 23:25:24` | `http://127.0.0.1:4110` | Hiçbiri (tekil izole sunucu) | Evet (3. deneme öncesi taze başlatıldı; koşu içinde çökme olmadı) |
| `R17` | `trial-exploratory` | `skill` | `2026-11-16 18:44:21` | `2026-11-16 18:54:27` | `http://127.0.0.1:4111` | Hiçbiri (tekil izole sunucu) | Evet (koşu öncesi taze başlatıldı; koşu içinde çökme olmadı) |
| `R18` | `trial-exploratory` | `noskill` | `2026-11-17 00:34:31` | `2026-11-17 00:48:36` | `http://127.0.0.1:4112` | Hiçbiri (tekil izole sunucu) | Evet (yeniden koşum öncesi taze başlatıldı; koşu içinde çökme olmadı) |

---

## 3. Yeniden Koşturulan Koşular

İlk denemelerin çalışma klasörü çıktıları yeniden koşum öncesinde silindi (`runs-discarded/` altında saklanan çıktı yoktur).

1. **`R16` (`trial-exploratory`, `skill`, port `4110`) — 2 kez yeniden koşturuldu:**
   - **1. Deneme (`2026-11-16 18:44:19` – `18:52:14 +03:00`):** Ajan `._probe_ch1_attacks.js` ve `"IDOR CANCEL VICTIM PNR"` çıktısı ürettikten sonra Gemini güvenlik filtresine takılıp durdu; gönderilen devam mesajı da aynı konuşma geçmişi nedeniyle tekrar filtreye takıldı ve `kesif-raporu.md` üretilemedi. Oturum sonlandırıldı, üretilen geçici dosyalar (`kanitlar/`, `._probe_*`) silindi.
   - **2. Deneme (`2026-11-16 18:59:12` – `19:12:27 +03:00`):** Temizlenmiş klasör ve taze sunucu ile aynı `skill` istemiyle yeniden başlatıldı; ancak `kesif-raporu.md` yazılmadan `RESOURCE_EXHAUSTED (code 429)` kota sınırına çarpıp durdu. Klasördeki geçici dosyalar (`.playwright-cli/`, `kanitlar/`, `tmp_qa/`) silindi.
   - **3. Deneme (tutulan nihai koşu, `2026-11-16 23:12:32` – `23:25:24 +03:00`):** Kota sıfırlandıktan sonra çalışma klasörü sıfırlandı, taze sunucu başlatıldı ve aynı `skill` istemiyle sorunsuz tamamlandı. İstemde değişiklik yapılmadı.

2. **Tüm 9 `noskill` koşusu (`R01`, `R03`, `R04`, `R06`, `R08`, `R09`, `R14`, `R15`, `R18`) — 1 kez yeniden koşturuldu:**
   - **1. Deneme saatleri (+03:00):**
     - `R01`: `2026-11-16 18:11:33` – `18:19:16`
     - `R03`: `2026-11-16 18:11:41` – `18:20:17`
     - `R04`: `2026-11-16 18:11:46` – `18:20:46`
     - `R06`: `2026-11-16 18:11:50` – `18:27:05`
     - `R08`: `2026-11-16 18:27:58` – `18:38:51`
     - `R09`: `2026-11-16 18:28:04` – `18:36:25`
     - `R14`: `2026-11-16 18:44:10` – `18:51:28`
     - `R15`: `2026-11-16 18:44:17` – `18:50:48`
     - `R18`: `2026-11-16 18:44:22` – `18:58:39`
   - **Neden yeniden koşturuldu:**
     1. İlk denemede `noskill` istemi, `skill` isteminden yalnızca `./skills` paragrafının çıkarılmasıyla oluşturulmuştu; ancak kullanıcı daha sonra `"Use your own expertise and general tools."` cümlesini içeren standart `noskill` istemini verip tüm 9 `noskill` koşusunun bu birebir istemle sıfırdan çalıştırılmasını istedi.
     2. (Ek bağlam: 1. denemede Batch 1 başlangıcında `R01`, `R04`, `R06` arka plan sunucuları `run_command` çıkışında sonlandığı için `--foreground` modu eklenerek yeniden başlatılmış ve `R01`/`R04`/`R06` ajanlarına devam mesajı gönderilmişti; `R04` ayrıca `null` gövde çökmesi sonrası otomatik yeniden başlatma eklenirken kısa süre beklemişti. 2. denemede ise baştan kararlı `--foreground` otomatik-toparlama ile tüm 9 `noskill` koşusu sıfır kesintiyle ve sıfır ara mesajla tamamlandı.)
   - **Ne değişti:**
     - Tüm 9 `noskill` klasörü (`shutil.rmtree` ile silinip) girdi dosyalarından sıfırdan kuruldu; ilk deneme çıktıları silindi (`runs-discarded/` yok).
     - İstem metni yeni `noskill` sürümüne güncellendi (`"Use your own expertise and general tools."` eklendi).
     - Sunucular sıfırdan taze süreçlerle başlatıldı (`R01`, `R04`, `R06`, `R08` için `task-265`; `R15`, `R18` için `task-293`).

---

## 4. Alt-Ajanlara Verilen İstemlerin Tam Metni

### 4.1. Ortak `SystemPrompt` (`qa-eval-runner` — tüm sürümlerde aynı)

```text
You are an independent senior QA engineer working on a client assignment.

Strict isolation and execution rules:
1. Your assigned workspace directory will be given in the user prompt. Treat that directory as your exclusive working directory ("the current directory").
2. In every `run_command` call, first `Set-Location` into your assigned workspace directory. In `read_file`, `write_file`, and `edit_file`, only use paths strictly inside your assigned workspace directory.
3. Never read, list, inspect, or search any file or directory outside your assigned workspace directory (including parent folders `..`, sibling folders, or any external repository).
4. Do not browse the internet, do not search for external repositories, and do not install any packages.
5. Use synthetic data only. Do not alter the original input files in the workspace.
6. Keep all requested deliverables inside your assigned workspace directory (matching the exact paths and filenames requested in TASK.md).
```

### 4.2. `skill` Kolu İstem Metni (tek sürüm — `<RUN_ID>` yerine `R02`, `R05`, `R07`, `R10`, `R11`, `R12`, `R13`, `R16`, `R17`)

```text
Your working directory ("the current directory") for this assignment is:
C:/eval/runs/<RUN_ID>

You are a senior QA engineer doing a job for a client. Work only inside the current directory (C:/eval/runs/<RUN_ID>).
Start with TASK.md and do exactly what it asks, as a professional would in about 25 minutes, in the language TASK.md uses. Write all deliverables into the current directory (following the exact paths/filenames specified in TASK.md).

A professional QA skill package is available in ./skills (one folder per skill, each with a SKILL.md whose description says when to use it). Pick the relevant skill(s), read their SKILL.md and follow them, using their scripts and references where they help.

Rules: do not browse the internet, do not look for this project's repository, do not read anything outside the current directory, do not install anything. Use synthetic data only.
Finish with 3-6 lines: the deliverable file names and your headline conclusion.
```

### 4.3. `noskill` Kolu İstem Metni — İlk Sürüm (atılan 1. denemelerde kullanıldı; `<RUN_ID>` yerine `R01`, `R03`, `R04`, `R06`, `R08`, `R09`, `R14`, `R15`, `R18`)

```text
Your working directory ("the current directory") for this assignment is:
C:/eval/runs/<RUN_ID>

You are a senior QA engineer doing a job for a client. Work only inside the current directory (C:/eval/runs/<RUN_ID>).
Start with TASK.md and do exactly what it asks, as a professional would in about 25 minutes, in the language TASK.md uses. Write all deliverables into the current directory (following the exact paths/filenames specified in TASK.md).

Rules: do not browse the internet, do not look for this project's repository, do not read anything outside the current directory, do not install anything. Use synthetic data only.
Finish with 3-6 lines: the deliverable file names and your headline conclusion.
```

### 4.4. `noskill` Kolu İstem Metni — Yeni Sürüm (tutulan nihai 2. denemelerde kullanıldı; `<RUN_ID>` yerine `R01`, `R03`, `R04`, `R06`, `R08`, `R09`, `R14`, `R15`, `R18`)

```text
Your working directory ("the current directory") for this assignment is:
C:/eval/runs/<RUN_ID>

You are a senior QA engineer doing a job for a client. Work only inside the current directory (C:/eval/runs/<RUN_ID>).
Start with TASK.md and do exactly what it asks, as a professional would in about 25 minutes, in the language TASK.md uses. Write all deliverables into the current directory (following the exact paths/filenames specified in TASK.md). Use your own expertise and general tools.

Rules: do not browse the internet, do not look for this project's repository, do not read anything outside the current directory, do not install anything. Use synthetic data only.
Finish with 3-6 lines: the deliverable file names and your headline conclusion.
```

*(Not: Tutulan nihai 18 koşunun hiçbirinde koşu sırasında alt-ajanlara ara mesaj gönderilmemiştir; `user_msgs=0`.)*

---

## 5. Alt-Ajanların Dosya Sistemi Erişimi ve İzolasyon Denetimi

- **Teknik erişim sınırı:** Alt-ajanlar Windows işletim sistemi üzerinde kapsayıcı/OS dosya sistemi sandbox'ı olmadan (`Workspace: inherit`, aktif IDE workspace yok, kullanıcının normal Windows yetkileriyle) çalıştı. Bu nedenle işletim sistemi düzeyinde `./repo` (ve `evals/keys/` dahil), diğer `runs/Rxx` klasörleri, `./servers/`, `./manifest.csv` ve üst dizinlere erişim **teknik olarak açıktı**; kısıtlama yalnızca `SystemPrompt` ve istem talimatlarıyla sağlandı.
- **Kural uyumu ve koşu sonrası denetim:** Tutulan 18 alt-ajanın tamamının oturum araç çağrısı dökümleri (`transcript.jsonl`) otomatik olarak tarandı:
  - Tüm `read_file` / `write_file` / `edit_file` çağrıları yalnızca ilgili alt-ajanın kendi `runs/<RUN_ID>` klasörü içinde kaldı (`outside=[]`).
  - `run_command` komutlarında üst dizin geçişi (`..`) bulunmadı (`dotdot_hits=0`); standart Windows/Python/Node/tarayıcı ikili yolları dışında harici bir proje/depo/koşu dizinine erişim görülmedi (`issues=0`).
  - Tüm `runs/<RUN_ID>` girdi dosyaları ve `skills/` kopyaları değiştirilmeden kaldı (`INPUT INTEGRITY OK`, `skills_ok=True`).
- **Teslimat kapsamı notu (`evals/results/external/antigravity/`):** Depoya yalnızca her koşunun ürettiği nihai teslimatlar (`trial-design`: `cikti/*`; `trial-api2`: `bulgular.md`, `test-kayitlari.md`; `trial-exploratory`: `kesif-raporu.md` ve `kanitlar/*`), `manifest.csv`, `start-servers` ve `NOTES.md` eklendi; özgün girdi dosyaları, `skills/` kopyaları ve ara çalışma klasörleri (`qa/` vb.) hariç tutuldu.

## Redaction

Before publication the local working-folder prefix was replaced with `C:/eval` (or `C:\eval`) in this file and in 11 deliverables (R01, R04, R07, R11, R13, R15), 25 occurrences in total. Nothing else in the deliverables was changed. The prompts above are verbatim apart from that prefix.
