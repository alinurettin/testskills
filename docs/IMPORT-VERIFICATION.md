# Import doğrulama kiti / Import verification kit

[Türkçe](#türkçe) · [English](#english)

`exporting-test-cases` skill'inin beş import formatı (Xray, Zephyr, TestRail, Azure DevOps, Qase) 2026-09-30'da
üreticilerin güncel import dokümanlarıyla alan alan karşılaştırıldı. Kaynak bağlantıları
`skills/exporting-test-cases/references/` içindeki "Verified against" satırlarında. **Hiçbir dosya henüz gerçek bir araca
import edilmedi.** Bu kit, bu açığı ücretsiz veya deneme hesaplarıyla, her araç için yaklaşık 30–45 dakikada kapatmak
için hazırlandı.

The five import formats of the `exporting-test-cases` skill were compared field by field with each vendor's current
import documentation on 2026-09-30. The sources are the "Verified against" lines in
`skills/exporting-test-cases/references/`. **No file has been imported into a real tool yet.** This kit closes that gap
with free or trial accounts, in roughly 30–45 minutes per tool.

---

## Türkçe

### 0. Kit

| Araç | Kullanılacak dosya | Yedek dosya (yalnızca gerekirse) | Ücretsiz / deneme çalışma alanı |
|---|---|---|---|
| Xray (Cloud) | `examples/import-kit/xray.csv` | `xray-server-dc.csv` (yalnızca Server/DC) | [Jira Cloud Free](https://www.atlassian.com/software/jira/free) + [Xray deneme (Marketplace)](https://marketplace.atlassian.com/apps/1211769/xray-test-management-for-jira) |
| Zephyr (Scale) | `examples/import-kit/zephyr.csv` | `zephyr-inline-data.csv` | Jira Cloud Free + [Zephyr deneme (Marketplace)](https://marketplace.atlassian.com/apps/1213259/zephyr-test-management-and-automation-for-jira) |
| TestRail | `examples/import-kit/testrail.csv` | – | [30 günlük deneme](https://www.testrail.com/pricing/) |
| Azure DevOps Test Plans | `examples/import-kit/azure-devops.csv` | – | [Azure DevOps](https://azure.microsoft.com/products/devops/) + [Test Plans 30 günlük deneme](https://learn.microsoft.com/en-us/azure/devops/organizations/billing/try-additional-features-vs?view=azure-devops) |
| Qase | `examples/import-kit/qase.csv` | – | [Qase Free plan](https://www.qase.io/pricing/) |

- **İçerik:** `tests/fixtures/coupon` içindeki 7 test ve 10 adım. Veriler sentetik ve Türkçe karakter içeriyor (ı, ş, ğ, ü, ö, ç).
  - `examples/fast-transfer` içinde henüz `test-cases.json` yok. Eklenirse `make_kit.py` kiti otomatik olarak ondan üretir.
- **Bilerek konmuş uç durumlar:**
  - TC-001, TC-002 ve TC-008 çok adımlı ve adım verisi var.
  - TC-004 `draft` durumunda, gereksinimi REQ-003'ün Jira anahtarı yok. Bu yüzden bağlantı **oluşmamalı**.
  - TC-005 `critical` öncelikli.
  - TC-007'nin gereksinimi yok ve önceliği `low`.
  - TC-008, requirements.json'da olmayan REQ-099'a bağlı.
- **Beklenen değerler:** `examples/import-kit/EXPECTED.md` her araç için test başına adım sayısını, öncelik/durum değerlerini, bağlantıları ve klasörü listeler. Kontrolü bu tabloyla yapın.
- **Jira anahtarları:** kit, gereksinimleri `KIT-1`, `KIT-2` ve `KIT-3` anahtarlarına bağlar (`kit-requirements.json`). Jira'da anahtarı **KIT** olan bir proje açın ve testleri import etmeden **önce** şu üç story'yi bu sırayla oluşturun:
  1. `KIT-1` Kupon ile %10 indirim
  2. `KIT-2` Süresi dolmuş kupon reddi
  3. `KIT-3` Kupon tek kullanımlık
- **Kiti yeniden üretmek** (exporter değiştiğinde): `python examples/import-kit/make_kit.py`. CI, kit bayatlarsa hata verir.
- **Güvenlik:** yalnızca bu sentetik dosyaları kullanın. Bitince deneme hesaplarını kapatın.
  - Azure DevOps'ta faturalama tanımlıysa, deneme bitince **Basic + Test Plans** atanmış kullanıcılar ücretlendirilir. Deneme bitmeden atamayı kaldırın.

### 1. Xray (Cloud)

1. Jira Cloud sitesini açın, Marketplace'ten Xray denemesini kurun ve **KIT** projesini oluşturun. Projede Xray issue tiplerinin (Test vb.) etkin olduğundan emin olun. Üç story'yi oluşturun.
2. **Apps → Xray → Test Case Importer → CSV**. File Import adımında `xray.csv` dosyasını seçin.
3. **Setup:**
   - Default project: KIT
   - File encoding: UTF-8
   - CSV delimiter: virgül
   - List value delimiter: `;`
   - Klasör oluşturma seçeneği: açık
4. **Map Fields:**

   | CSV sütunu | Xray alanı |
   |---|---|
   | TCID | Test ID |
   | Summary | Summary |
   | Description | Description |
   | Test Type | Test Type |
   | Priority | Priority |
   | Labels | Labels |
   | Requirement Keys | Link "Tests" |
   | Action | Action |
   | Data | Data |
   | Expected Result | Expected Result |
   | Test Repository Folder | Test Repository Folder |

   `Component` sütununu eşlemeyin; boş.
5. Import'u başlatın. Konfigürasyonu kaydedin (JSON) ve sonuç ekranının görüntüsünü alın.
6. **Kontrol listesi:**
   - [ ] 7 Test oluştu (10 değil).
   - [ ] Adım sayıları EXPECTED.md ile aynı. Örneğin TC-001'de 2 adım var ve 1. adımın Data alanı `Ürün A x1`.
   - [ ] Test Type `Manual`. Priority değerleri doğru: TC-005 `Highest`, TC-007 `Low`.
   - [ ] Etiketler ayrı ayrı oluştu. TC-001'de `regression`, `smoke`, `REQ-001`, `boundary-value-analysis` ve `positive` görünmeli.
   - [ ] Test Repository'de `QA Suite Kit/Kupon` klasörü oluştu ve 7 testi içeriyor.
   - [ ] Kapsam doğru:
     - KIT-1 → TC-001, TC-002, TC-008
     - KIT-2 → TC-003
     - KIT-3 → TC-005
     - TC-004 ve TC-007'nin bağlantısı yok.
   - [ ] Türkçe karakterler bozulmadı: `sınırında`, `Süresi dolmuş`.
7. **Xray sonuç yolu (isteğe bağlı):**
   - `examples/import-kit/xray-junit-sample.xml` dosyasında `KIT-4` ve `KIT-6` değerlerini, TC-001 ve TC-003'ün gerçek Xray anahtarlarıyla değiştirin.
   - Dosyayı Xray'in JUnit sonuç import'uyla (UI'daki import veya `POST /api/v2/import/execution/junit?projectKey=KIT`) yükleyin.
   - Beklenen: yeni bir Test Execution'da TC-001 PASSED, TC-003 FAILED görünür. **Yeni bir Generic test oluşmaz**, sonuçlar import edilen Manual testlere yazılır. KIT-1 ve KIT-2'nin kapsamında bu sonuçlar görünür.
   - Bu adım, Playwright'ın `test_key` yolunu Playwright çalıştırmadan doğrular. UI menüsünün adı dokümanda doğrulanamadı; bulduğunuz yolu sonuç tablosuna yazın.
8. **Yeniden dışa aktarma:** Jira arama `project = KIT AND issuetype = Test` → Export → CSV (all fields) → `tests/fixtures/exports/vendor/xray/xray-cloud-<tarih>.csv`.

Xray **Server/DC** kullanıyorsanız aynı adımları `xray-server-dc.csv` ile izleyin. Farklar:
- Zorunlu alanlar Test Case Identifier, Summary ve Action.
- `Requirement Key 1` sütunu Link "Tests" alanına eşlenir.
- Klasör sütunu Test Repository Path alanına eşlenir. Setup'ta **Hierarchical Test Organization – Create Folders** açık olmalı.

### 2. Zephyr (Scale, Cloud)

1. Aynı Jira sitesine Zephyr denemesini kurun. KIT projesini ve üç story'yi kullanın.
2. **Test Cases → More → Import from File → Excel CSV**. Dosya: `zephyr.csv`.
3. **Setup:**
   - Destination Folder: kök
   - File Encoding: UTF-8
   - CSV Delimiter: virgül
   - Start Import at Row: 1
   - "This row contains the field names" seçili
4. **Field Mapping:**

   | CSV sütunu | Zephyr alanı |
   |---|---|
   | Name | Name |
   | Objective | Objective |
   | Precondition | Precondition |
   | Folder | Folder |
   | Status | Status |
   | Priority | Priority |
   | Labels | Labels |
   | Coverage | Coverage |
   | Test Script (Step-by-Step) - Step | Test Script (Steps) - Step |
   | Test Script (Step-by-Step) - Test Data | Test Data |
   | Test Script (Step-by-Step) - Expected Result | Test Script (Steps) - Expected Result |

   Test Data için bir hedef **yoksa**: import'u iptal edin ve `zephyr-inline-data.csv` ile tekrarlayın. Bunu sonuç tablosuna yazın.
5. **Data Mapping:**
   - Status: `Approved` ve `Draft`.
   - Priority: dosyadaki `Highest`, `High`, `Medium` ve `Low` değerlerini projedeki değerlere eşleyin. Hangi değeri neye eşlediğinizi not edin.
   - Etiketlerin otomatik oluşturulmasına izin verin.
6. **Import → Results:** uyarıları kaydedin.
7. **Kontrol listesi:**
   - [ ] **7** test case oluştu. 10 oluştuysa çok satırlı adım düzeni desteklenmiyor demektir; bunu yazın ve `--zephyr-steps single` ile yeniden deneyin.
   - [ ] Adım sayıları ve adım verisi EXPECTED.md ile aynı.
   - [ ] TC-004 `Draft`, diğerleri `Approved`.
   - [ ] Etiketler **ayrı ayrı** oluştu. TC-001'de 5 etiket olmalı, `regression,smoke,…` biçiminde tek bir etiket değil.
   - [ ] Coverage doğru: KIT-1, KIT-2 ve KIT-3 (EXPECTED.md). TC-004 ve TC-007'de coverage yok.
   - [ ] `QA Suite Kit/Kupon` klasörü oluştu. Türkçe karakterler bozulmadı.
8. **Yeniden dışa aktarma:** import edilen test case'leri CSV olarak dışa aktarın. Araç yalnızca Excel veriyorsa, sayfayı "CSV UTF-8" olarak kaydedin. Hedef: `tests/fixtures/exports/vendor/zephyr/zephyr-cloud-<tarih>.csv`.

### 3. TestRail

1. 30 günlük denemeyi başlatın ve bir proje açın. "Single repository" veya suite modu fark etmez.
2. **Test Cases → araç çubuğundaki Import simgesi → Import from CSV**. Dosya: `testrail.csv`.
3. **Dosya ve seçenekler:**
   - File Encoding: UTF-8
   - Delimiter: `,`
   - Start Row: 1
   - Başlık satırı: var
   - Template: **Test Case (Steps)**
4. **Column mapping:**
   - Layout: **Test cases use multiple rows**. Yeni case'i algılayan sütun: **Title**.
   - Eşleme:

     | CSV sütunu | TestRail alanı |
     |---|---|
     | Title | Title |
     | Section | Section |
     | Priority | Priority |
     | Type | Type |
     | Preconditions | Preconditions |
     | Step | Steps (Step) |
     | Expected Result | Steps (Expected Result) |
     | References | References |
5. **Value mapping:** Priority (Critical/High/Medium/Low) ve Type (Regression/Functional). Ardından **Preview → Import**.
6. **Kontrol listesi:**
   - [ ] `QA Suite Kit > Kupon` bölümünde 7 case oluştu.
   - [ ] TC-001'de 2 **ayrı** adım var ve 1. adım metni `[Ürün A x1]` ile bitiyor. 2. adımlar eksikse "ignore rows without a valid title" seçeneğini kapatıp tekrar deneyin ve bunu yazın.
   - [ ] TC-005 `Critical`. Type değerleri EXPECTED.md ile aynı.
   - [ ] Preconditions çok satırlı ve `Test verisi:` bloğunu içeriyor.
   - [ ] References doğru, örneğin `REQ-001, KIT-1`.
7. **Yeniden dışa aktarma:** Test Cases → Export → CSV. Tüm sütunları ve adım sütunlarını seçin. Hedef: `tests/fixtures/exports/vendor/testrail/testrail-<sürüm>-<tarih>.csv`.

### 4. Azure DevOps Test Plans

1. Bir organizasyon açın.
2. **Organization settings → Billing → Start free trial** ile Test Plans denemesini başlatın ve kendinize **Basic + Test Plans** atayın.
3. Adı tam olarak **QASuiteKit** olan bir proje açın. Kitteki Area Path budur.
4. **Test Plans → New Test Plan** ile "QA Suite Kit" planını oluşturun.
   - İsteğe bağlı bağlantı kontrolü: Boards'da "Kupon ile %10 indirim" adlı bir User Story açın. Plana bu story için bir **Requirement-based suite** ekleyin ve import'u bu suite'e yapın.
5. Suite'i seçin → **Import test cases from CSV/XLSX** → `azure-devops.csv`.
   - Otomatik eşlemede dokuz zorunlu alan eşlenmiş olmalı: ID, Work Item Type, Title, Test Step, Step Action, Step Expected, Area Path, Assigned To, State. **Priority** de eşlenmeli.
   - Assigned To boş olduğu için hata verirse sütuna kendi e-postanızı yazın veya `--assigned-to` ile dosyayı yeniden üretin. Bunu not edin.
   - Ardından **Import**.
6. **Kontrol listesi:**
   - [ ] 7 test case oluştu. TC-001'de 2 adım var.
   - [ ] 1. adımın Action alanı `Ön koşullar: …` ve `Test verisi: …` satırlarıyla başlıyor.
   - [ ] Priority doğru: TC-005 `1`, TC-007 `4`. State `Design`. Area Path `QASuiteKit`.
   - [ ] Requirement-based suite kullandıysanız: test case'ler story'ye "Tested By" bağlantısıyla bağlandı.
   - [ ] Türkçe karakterler bozulmadı.
7. **Yeniden dışa aktarma:** suite → Column options → **Priority** ekleyin → Export test cases to CSV. Hedef: `tests/fixtures/exports/vendor/azure-devops/ado-services-<tarih>.csv`.

### 5. Qase

1. Free plan ile kaydolun ve "QA Suite Kit" projesini açın.
2. Repository → sağ üstteki `…` → **Import Data**.
   - Kaynak/format: **Qase.io** seçin, "Qase.io CSV [deprecated]" değil.
   - Üst suite: kök. Dosya: `qase.csv`. Ardından Import.
3. **Kontrol listesi:**
   - [ ] `QA Suite Kit` → `Kupon` suite ağacı oluştu ve 7 case içeriyor.
   - [ ] TC-001'de 2 **ayrı** adım var. Adım verisi ve beklenen sonuç doğru adımlarda.
   - [ ] priority, severity, status ve automation değerleri EXPECTED.md ile aynı. Qase geçersiz değerleri **sessizce** varsayılana çeviriyor, bu yüzden her birine bakın.
   - [ ] Etiketler, açıklamadaki `Gereksinimler:` satırı ve ön koşullardaki `Test verisi:` bloğu doğru.
4. **Yeniden dışa aktarma:** `…` → Export Data → CSV ("old format" değil). Hedef: `tests/fixtures/exports/vendor/qase/qase-cloud-<tarih>.csv`.

### 6. Sonuç tablosu

Her import'tan sonra bir satır doldurun. Ekran görüntülerini `docs/assets/import-verification/` altına koyabilir veya PR'a ekleyebilirsiniz.

| Araç | Tarih | Sürüm / plan | Dosya | Sonuç (geçti/kaldı) | Elle düzeltmeler / notlar | Ekran görüntüsü |
|---|---|---|---|---|---|---|
| Xray Cloud | | | xray.csv | | | |
| Xray sonuç yolu (JUnit) | | | xray-junit-sample.xml | | | |
| Zephyr Cloud | | | zephyr.csv | | | |
| TestRail | | | testrail.csv | | | |
| Azure DevOps Services | | | azure-devops.csv | | | |
| Qase | | | qase.csv | | | |

"Geçti" demek için kontrol listesinin tüm maddeleri sağlanmalı, elle düzeltme yapılmamalı ve değer eşlemesi dışında bir ayar değiştirilmemiş olmalı.

### 7. Yeniden dışa aktarılan dosyayı CI'a bağlamak

1. Aracın kendi CSV'sini `tests/fixtures/exports/vendor/<araç>/` klasörüne koyun. Klasör adları: `xray`, `zephyr`, `testrail`, `azure-devops`, `qase`. Ayrıntılar [vendor/README.md](../tests/fixtures/exports/vendor/README.md) dosyasında.
2. `python -m unittest tests.test_export_golden` komutunu çalıştırın. Test artık atlanmaz. Sütun adlarını ve öncelik/durum/tip değerlerini aracın dosyasıyla karşılaştırır.
3. Test kalırsa iki seçenek var:
   - Exporter'ın varsayılanını düzeltin, ardından goldens ve kiti yeniden üretin: `python tests/test_export_golden.py --update`.
   - Değeri sihirbazda bilerek eşlediyseniz, bu eşlemeyi `tests/fixtures/exports/vendor/<araç>/accepted.json` dosyasına yazın. Örnek: `{"Priority": {"Medium": "Normal"}}`.
4. İlgili `references/*.md` dosyasına "Imported into <araç, sürüm> on <tarih>" satırını ekleyin ve sonuç tablosunu bu dosyada güncelleyin.

---

## English

### 0. The kit

| Tool | File to use | Fallback (only if needed) | Free / trial workspace |
|---|---|---|---|
| Xray (Cloud) | `examples/import-kit/xray.csv` | `xray-server-dc.csv` (Server/DC only) | [Jira Cloud Free](https://www.atlassian.com/software/jira/free) + [Xray trial (Marketplace)](https://marketplace.atlassian.com/apps/1211769/xray-test-management-for-jira) |
| Zephyr (Scale) | `examples/import-kit/zephyr.csv` | `zephyr-inline-data.csv` | Jira Cloud Free + [Zephyr trial (Marketplace)](https://marketplace.atlassian.com/apps/1213259/zephyr-test-management-and-automation-for-jira) |
| TestRail | `examples/import-kit/testrail.csv` | – | [30-day trial](https://www.testrail.com/pricing/) |
| Azure DevOps Test Plans | `examples/import-kit/azure-devops.csv` | – | [Azure DevOps](https://azure.microsoft.com/products/devops/) + [30-day Test Plans trial](https://learn.microsoft.com/en-us/azure/devops/organizations/billing/try-additional-features-vs?view=azure-devops) |
| Qase | `examples/import-kit/qase.csv` | – | [Qase Free plan](https://www.qase.io/pricing/) |

- **Content:** the 7 tests and 10 steps of `tests/fixtures/coupon`. The data is synthetic and contains Turkish characters (ı, ş, ğ, ü, ö, ç).
  - `examples/fast-transfer` has no `test-cases.json` yet. Once it does, `make_kit.py` builds the kit from it automatically.
- **Deliberate edge cases:**
  - TC-001, TC-002 and TC-008 have several steps with step data.
  - TC-004 is `draft`, and its requirement REQ-003 has no Jira key, so **no** link may appear.
  - TC-005 is `critical`.
  - TC-007 has no requirement and is `low`.
  - TC-008 links REQ-099, which is not in requirements.json.
- **Expected values:** `examples/import-kit/EXPECTED.md` lists, for every tool, the step count, the priority and status values, the links and the folder of each test. Check against it.
- **Jira keys:** the kit links requirements to `KIT-1`, `KIT-2` and `KIT-3` (`kit-requirements.json`). Create a Jira project with key **KIT** and, **before** importing tests, create these three stories in this order:
  1. `KIT-1` Kupon ile %10 indirim
  2. `KIT-2` Süresi dolmuş kupon reddi
  3. `KIT-3` Kupon tek kullanımlık
- **Regenerate the kit** after exporter changes: `python examples/import-kit/make_kit.py`. CI fails when the kit is stale.
- **Safety:** use only these synthetic files. Close the trials when you are done.
  - In Azure DevOps with billing set up, users assigned **Basic + Test Plans** are charged after the trial. Remove the assignment before the trial ends.

### 1. Xray (Cloud)

1. Create the Jira Cloud site, install the Xray trial from the Marketplace and create project **KIT**. Make sure the project has the Xray issue types (Test and so on). Create the three stories.
2. **Apps → Xray → Test Case Importer → CSV**. In the File Import step, choose `xray.csv`.
3. **Setup:**
   - Default project: KIT
   - File encoding: UTF-8
   - CSV delimiter: comma
   - List value delimiter: `;`
   - Folder creation: on
4. **Map Fields:**

   | CSV column | Xray field |
   |---|---|
   | TCID | Test ID |
   | Summary | Summary |
   | Description | Description |
   | Test Type | Test Type |
   | Priority | Priority |
   | Labels | Labels |
   | Requirement Keys | Link "Tests" |
   | Action | Action |
   | Data | Data |
   | Expected Result | Expected Result |
   | Test Repository Folder | Test Repository Folder |

   Leave `Component` unmapped; it is empty.
5. Run the import. Save the configuration (JSON) and take a screenshot of the result.
6. **Checklist:**
   - [ ] 7 Tests were created (not 10).
   - [ ] Step counts match EXPECTED.md. For example, TC-001 has 2 steps and the Data of step 1 is `Ürün A x1`.
   - [ ] Test Type is `Manual`. Priorities are right: TC-005 `Highest`, TC-007 `Low`.
   - [ ] Labels were created separately. TC-001 should show `regression`, `smoke`, `REQ-001`, `boundary-value-analysis` and `positive`.
   - [ ] The Test Repository has a folder `QA Suite Kit/Kupon` holding the 7 tests.
   - [ ] Coverage is right:
     - KIT-1 → TC-001, TC-002, TC-008
     - KIT-2 → TC-003
     - KIT-3 → TC-005
     - TC-004 and TC-007 have no link.
   - [ ] Turkish characters are intact: `sınırında`, `Süresi dolmuş`.
7. **Xray results path (optional):**
   - In `examples/import-kit/xray-junit-sample.xml`, replace `KIT-4` and `KIT-6` with the real Xray keys of TC-001 and TC-003.
   - Upload the file with Xray's JUnit results import (the import in the UI, or `POST /api/v2/import/execution/junit?projectKey=KIT`).
   - Expected: a new Test Execution shows TC-001 PASSED and TC-003 FAILED. **No new Generic test is created**; the results land on the imported Manual tests. The coverage of KIT-1 and KIT-2 shows these results.
   - This checks Playwright's `test_key` path without running Playwright. The name of the UI menu could not be confirmed from the docs; write down the path you found in the result table.
8. **Re-export:** Jira search `project = KIT AND issuetype = Test` → Export → CSV (all fields) → `tests/fixtures/exports/vendor/xray/xray-cloud-<date>.csv`.

On Xray **Server/DC**, follow the same steps with `xray-server-dc.csv`. The differences:
- The mandatory fields are Test Case Identifier, Summary and Action.
- Map `Requirement Key 1` to Link "Tests".
- Map the folder column to Test Repository Path, and enable **Hierarchical Test Organization – Create Folders** in Setup.

### 2. Zephyr (Scale, Cloud)

1. Install the Zephyr trial on the same Jira site. Use project KIT and its three stories.
2. **Test Cases → More → Import from File → Excel CSV**. File: `zephyr.csv`.
3. **Setup:**
   - Destination Folder: root
   - File Encoding: UTF-8
   - CSV Delimiter: comma
   - Start Import at Row: 1
   - "This row contains the field names" selected
4. **Field Mapping:**

   | CSV column | Zephyr field |
   |---|---|
   | Name | Name |
   | Objective | Objective |
   | Precondition | Precondition |
   | Folder | Folder |
   | Status | Status |
   | Priority | Priority |
   | Labels | Labels |
   | Coverage | Coverage |
   | Test Script (Step-by-Step) - Step | Test Script (Steps) - Step |
   | Test Script (Step-by-Step) - Test Data | Test Data |
   | Test Script (Step-by-Step) - Expected Result | Test Script (Steps) - Expected Result |

   If there is **no** Test Data target, cancel and repeat with `zephyr-inline-data.csv`. Record this in the result table.
5. **Data Mapping:**
   - Status: `Approved` and `Draft`.
   - Priority: map the file's `Highest`, `High`, `Medium` and `Low` to the project's values. Note which value you mapped to which.
   - Allow automatic creation of labels.
6. **Import → Results:** record the warnings.
7. **Checklist:**
   - [ ] **7** test cases were created. If 10 were created, the multi-row step layout is not supported; record that and retry with `--zephyr-steps single`.
   - [ ] Step counts and step data match EXPECTED.md.
   - [ ] TC-004 is `Draft`, the others are `Approved`.
   - [ ] Labels were created **separately**. TC-001 should have 5 labels, not one label reading `regression,smoke,…`.
   - [ ] Coverage is right: KIT-1, KIT-2 and KIT-3 (EXPECTED.md). TC-004 and TC-007 have no coverage.
   - [ ] The folder `QA Suite Kit/Kupon` exists. Turkish characters are intact.
8. **Re-export:** export the imported test cases as CSV. If the tool only offers Excel, save the sheet as "CSV UTF-8". Target: `tests/fixtures/exports/vendor/zephyr/zephyr-cloud-<date>.csv`.

### 3. TestRail

1. Start the 30-day trial and create a project. Single repository or suite mode both work.
2. **Test Cases → Import icon in the toolbar → Import from CSV**. File: `testrail.csv`.
3. **File and options:**
   - File Encoding: UTF-8
   - Delimiter: `,`
   - Start Row: 1
   - Header row: yes
   - Template: **Test Case (Steps)**
4. **Column mapping:**
   - Layout: **Test cases use multiple rows**. Column that detects a new case: **Title**.
   - Mapping:

     | CSV column | TestRail field |
     |---|---|
     | Title | Title |
     | Section | Section |
     | Priority | Priority |
     | Type | Type |
     | Preconditions | Preconditions |
     | Step | Steps (Step) |
     | Expected Result | Steps (Expected Result) |
     | References | References |
5. **Value mapping:** Priority (Critical/High/Medium/Low) and Type (Regression/Functional). Then **Preview → Import**.
6. **Checklist:**
   - [ ] Section `QA Suite Kit > Kupon` holds 7 cases.
   - [ ] TC-001 has 2 **separate** steps, and step 1 ends with `[Ürün A x1]`. If the second steps are missing, retry with "ignore rows without a valid title" switched off, and record it.
   - [ ] TC-005 is `Critical`. The Type values match EXPECTED.md.
   - [ ] Preconditions are multi-line and include the `Test verisi:` block.
   - [ ] References are right, for example `REQ-001, KIT-1`.
7. **Re-export:** Test Cases → Export → CSV. Select all columns, including the step columns. Target: `tests/fixtures/exports/vendor/testrail/testrail-<version>-<date>.csv`.

### 4. Azure DevOps Test Plans

1. Create an organization.
2. Start the Test Plans trial in **Organization settings → Billing → Start free trial**, and assign yourself **Basic + Test Plans**.
3. Create a project named exactly **QASuiteKit**. This is the kit's Area Path.
4. **Test Plans → New Test Plan** "QA Suite Kit".
   - Optional link check: create a User Story "Kupon ile %10 indirim" in Boards, add a **Requirement-based suite** for it to the plan, and import into that suite.
5. Select the suite → **Import test cases from CSV/XLSX** → `azure-devops.csv`.
   - The automatic mapping must cover the nine required fields: ID, Work Item Type, Title, Test Step, Step Action, Step Expected, Area Path, Assigned To, State. It should also map **Priority**.
   - If the empty Assigned To causes an error, put your own e-mail in that column or regenerate the file with `--assigned-to`. Note it.
   - Then **Import**.
6. **Checklist:**
   - [ ] 7 test cases were created. TC-001 has 2 steps.
   - [ ] The Action of step 1 starts with the lines `Ön koşullar: …` and `Test verisi: …`.
   - [ ] Priority is right: TC-005 `1`, TC-007 `4`. State is `Design`. Area Path is `QASuiteKit`.
   - [ ] With a requirement-based suite: the test cases are linked to the story as "Tested By".
   - [ ] Turkish characters are intact.
7. **Re-export:** suite → Column options → add **Priority** → Export test cases to CSV. Target: `tests/fixtures/exports/vendor/azure-devops/ado-services-<date>.csv`.

### 5. Qase

1. Sign up for the Free plan and create project "QA Suite Kit".
2. Repository → `…` (top right) → **Import Data**.
   - Source/format: choose **Qase.io**, not "Qase.io CSV [deprecated]".
   - Parent suite: root. File: `qase.csv`. Then Import.
3. **Checklist:**
   - [ ] The suite tree `QA Suite Kit` → `Kupon` holds 7 cases.
   - [ ] TC-001 has 2 **separate** steps. Step data and expected results sit on the right steps.
   - [ ] The priority, severity, status and automation values match EXPECTED.md. Qase replaces invalid values with defaults **silently**, so look at each one.
   - [ ] The tags, the `Gereksinimler:` line in the description and the `Test verisi:` block in the preconditions are right.
4. **Re-export:** `…` → Export Data → CSV (not the "old format"). Target: `tests/fixtures/exports/vendor/qase/qase-cloud-<date>.csv`.

### 6. Result table

Fill in one row per import. Screenshots can go into `docs/assets/import-verification/` or into the PR.

| Tool | Date | Version / plan | File | Result (pass/fail) | Manual fixes / notes | Screenshot |
|---|---|---|---|---|---|---|
| Xray Cloud | | | xray.csv | | | |
| Xray results path (JUnit) | | | xray-junit-sample.xml | | | |
| Zephyr Cloud | | | zephyr.csv | | | |
| TestRail | | | testrail.csv | | | |
| Azure DevOps Services | | | azure-devops.csv | | | |
| Qase | | | qase.csv | | | |

"Pass" means every checklist item holds, nothing was fixed by hand, and no setting was changed other than value mapping.

### 7. Connecting the re-export to CI

1. Put the tool's own CSV into `tests/fixtures/exports/vendor/<tool>/`. The folder names are `xray`, `zephyr`, `testrail`, `azure-devops` and `qase`. Details are in [vendor/README.md](../tests/fixtures/exports/vendor/README.md).
2. Run `python -m unittest tests.test_export_golden`. The test is no longer skipped. It compares column names and priority/status/type values with the tool's file.
3. If it fails, there are two options:
   - Fix the exporter default, then regenerate the goldens and the kit: `python tests/test_export_golden.py --update`.
   - If you mapped the value on purpose in the wizard, record that mapping in `tests/fixtures/exports/vendor/<tool>/accepted.json`. Example: `{"Priority": {"Medium": "Normal"}}`.
4. Add an "Imported into <tool, version> on <date>" line to the matching `references/*.md`, and update the result table in this file.
