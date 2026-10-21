# Answer key — trial-mobile2 (mobile test plan review, PoyrazKlinik v4.3)

**EVALUATOR ONLY. Never give this file, `mobile2_grade.py`, or `trial-mobile2/RUN.md` to the agent.**

| | |
|---|---|
| Trial folder | `C:\projeler\TestSkills\evals\trial-mobile2\` |
| Agent receives | `TASK.md` + `girdiler/` (`urun_ozeti_v4.3.md`, `test_plani_v4.3.md`, `cihaz_kullanim_2026-08.csv`) |
| Deliverables | `plan_inceleme.md`, `cihaz_matrisi.csv` (header `platform,model,os_surumu`) |
| Kind | Mobile app test plan review, no device; Turkish context; synthetic data |
| Grader helper | `python C:\projeler\TestSkills\evals\keys\mobile2_grade.py grade <workspace>` (objective matrix part plus keyword hints) |
| Input self-check | `python ...\mobile2_grade.py verify` (62 checks) and `python ...\mobile2_grade.py selftest` |

## 1. Scoring summary

| Block | Points |
|---|---|
| K1–K12 planted gaps/errors (4 easy × 5, 4 medium × 8, 4 hard × 11) | 96 |
| M1–M5 device matrix (objective, computed from the CSV) | 20 |
| F1–F2 deliverable form | 4 |
| **Maximum** | **120** |
| T1–T4 traps | −4 each (if triggered) |
| Other false positives (§6) | −2 each, capped at −10 |
| Priority mismatch | −1 per K item whose expected priority is P1 but which the agent rated P3 |

Final score = max(0, sum − penalties). Report it as a raw score and as a percentage of 120.

Guidance for interpreting scores. These are expectations, not part of the rubric:
- A quick, intuitive pass by a strong generic model typically gets K1–K4, parts of K5–K8, maybe generic credit on K9/K10, and misses K11 and the recomputation in K12. Expect about 40–65.
- A systematic professional pass that cross-checks every expected result against the brief, recomputes the matrix from the CSV, and follows the App Links signing chain should reach 95 or more.

Grading rules:
- Each planted item is scored once. If the agent reports it in several places, merge them and score the best statement.
- A finding earns credit only when it is in `plan_inceleme.md`. Material that exists only in the agent's chat reply does not count.
- Wording may be Turkish or English. The **substance** in the acceptance rule must be present. Keywords alone are not enough.
- Extra valid findings that are not planted (§7) earn nothing and lose nothing.

## 2. Ground truth computed from the CSV

Supported means it is a phone **and** its OS is at least the 4.3 minimum (Android 10, iOS 16). Tablets and below-minimum rows are not supported.

| Platform | All users | Supported users | 80 % threshold |
|---|---|---|---|
| Android | 104 000 | **89 100** | 71 280 |
| iOS | 70 800 | **62 700** | 50 160 |

Coverage rule, from plan §6: one device covers **only its own model + OS-major row**, and the denominator is supported users.

**Supported rows by users (greedy, cumulative)**

Android: A54/15 11 200 (12.6 %) · Redmi Note 12/14 9 800 (23.6) · A34/15 8 900 (33.6) · Redmi Note 13/14 8 100 (42.6) · A54/16 7 300 (50.8) · A14/14 6 900 (58.6) · A13/14 6 200 (65.5) · Redmi Note 11/13 5 600 (71.8) · A55/16 5 000 (77.4) · **A12/12 4 300 (82.3)** · S23/16 3 400 (86.1) · A10/11 2 900 (89.3) · Redmi 13C/14 2 600 · S24/16 2 300 · Redmi Note 8/11 1 700 · P30 Lite/10 1 200 · A17/13 1 000 · Pixel 7/16 700.
The minimum is **10 devices**. The budget is 11.

iOS: 13/26 9 400 (15.0 %) · 15/26 8 700 (28.9) · 14/26 8 100 (41.8) · 11/26 7 300 (53.4) · 12/26 6 200 (63.3) · 16/26 5 600 (72.2) · 13/18 3 900 (78.5) · **11/18 2 600 (82.6)** · XR/18 2 300 · 15 Pro Max/26 2 100 · 16 Pro/26 1 700 · 14 Pro/26 1 500 · SE (2. nesil)/26 1 200 · 12/18 900 · 8/16 700 · X/16 500.
The minimum is **8 devices**. The budget is 9.

Unsupported rows: Android Galaxy A10/9 5 400, Galaxy Tab A8/14 (tablet) 4 700, Redmi Note 8/9 1 500, Galaxy Tab S6 Lite/13 (tablet) 1 300, Y7 2019/8 1 100, P30 Lite/9 900. iOS iPad (9. nesil)/18 (tablet) 3 600, iPhone 8/15 1 900, iPhone 7/15 1 600, iPad Air (5. nesil)/26 (tablet) 1 000.

**An example of a fully correct matrix:** Android, the top 10 supported rows plus P30 Lite/10 (minimum-OS device), which gives 74 500 / 89 100 = **83.6 %**. iOS, the top 8 supported rows plus iPhone 8/16 (minimum-OS device), which gives 52 500 / 62 700 = **83.7 %**.

Other useful figures: 88.7 % of supported Android users run Android 13 or later (relevant to K1), 81.3 % run Android 14 or later (K6), and Xiaomi accounts for 31.2 % of supported Android users (relevant to OEM background limits in K10).

## 3. Planted items

| ID | Area / plan ref | Difficulty | Expected priority | Points |
|---|---|---|---|---|
| K1 | Android 13+ notification permission (TC-PUSH-04) | easy | P1 | 5 |
| K2 | Upgrade only from 4.2, not from 4.1/4.0 (TC-UPG-01) | easy | P1 | 5 |
| K3 | Largest-font test in English, but Turkish strings are longer (TC-A11Y-02 note) | easy | P2 | 5 |
| K4 | Biometric enrolment change invalidates key (5.1) | easy | P2 | 5 |
| K5 | Location: "Always" not in first dialog; While-Using/Once; iOS Precise off (TC-LOC-01/03) | medium | P2 | 8 |
| K6 | Android 14+ partial photo access (TC-DOC-04) | medium | P2 | 8 |
| K7 | TC-APT-07 expected result contradicts brief; no wrong-device-clock test | medium | P1 | 8 |
| K8 | TC-DL-03 expects chooser; Android 12+ opens unverified links in browser | medium | P2 | 8 |
| K9 | Process death mid-flush; duplicate/loss window of the idempotent queue (5.6) | hard | P1 | 11 |
| K10 | TC-OFF-05 background expectations are wrong (force stop, BGAppRefresh, Doze/OEM) | hard | P2 | 11 |
| K11 | assetlinks.json lacks the Play app-signing fingerprint; plan only tests upload-key builds | hard | P1 | 11 |
| K12 | Plan device matrix miscounted; real coverage 66.9 % / 64.4 % < 80 % | hard | P2 | 11 |

### K1 — Android 13+ runtime notification permission (easy, 5 pts, expected P1)
- **Where:** plan TC-PUSH-04 says Android grants notification permission at install, so the permission flow is tested on iOS only. TC-PUSH-01 and TC-PUSH-02 are iOS-only.
- **Why it is wrong:** the brief (§2) sets `targetSdk 36`, and §4.5 says the permission is requested on "iOS ve Android 13+". From Android 13 (API 33), `POST_NOTIFICATIONS` is a runtime permission. 88.7 % of supported Android users are on 13 or later. If the user denies it, no reminder push arrives, so the in-app inbox and SMS fallback are untested on Android.
- **Acceptance:**
  - **5 pts:** the finding states that the TC-PUSH-04 premise is false or that Android 13+ needs a runtime notification permission, **and** proposes at least one concrete Android test. Examples: grant; deny leading to the in-app inbox plus SMS 2 hours before; second denial or "don't ask again" followed by re-enabling in Settings; behaviour on Android 10–12 versus 13+.
  - **3 pts:** says to "add Android notification permission tests" without saying that the plan's premise is wrong or naming Android 13+.
  - **0 pts:** anything less.

### K2 — Upgrade path from two versions back (easy, 5 pts, expected P1)
- **Where:** TC-UPG-01 covers only 4.2 → 4.3, with the justification "most users are on 4.2".
- **Why it matters:** the brief (§3) says 4.1 is 17 % and 4.0 is 12 %, so 29 % of users jump more than one version. Their migrations run as a chain: 5 → 6 → 7 or 4 → 5 → 6 → 7. The chain includes a table rename (`symptom_log` → `symptom_entries`), a new `mime_type` column, a new `retry_count` column, and a move of the biometric preference. A broken chain means data loss for nearly a third of users.
- **Acceptance:**
  - **5 pts:** proposes upgrade tests from **both 4.1 and 4.0** to 4.3, or "every supported version, 4.0 and 4.1", with data-preservation checks. The checks should cover something like symptom entries, documents, pending queue items, session or biometric setting, and should succeed without a crash.
  - **3 pts:** proposes only 4.1 → 4.3, or only says "test from older versions" without naming them.
  - **0 pts:** anything less.

### K3 — Largest font is tested in English, but Turkish strings are longer (easy, 5 pts, expected P2)
- **Where:** the note under 5.10 says TC-A11Y-02 is run in English because "the longest UI strings are English".
- **Why it is wrong:** the strings table in brief §4.9 contradicts it. Turkish totals 357 characters against 240 in English (×1.49). The longest string is Turkish (79 against 58 characters). In 10 of 12 keys the Turkish string is longer, for example "Geldim, check-in yap" against "I'm here" and "Randevuyu iptal et" against "Cancel". 96 % of users use Turkish, so the worst case for truncation or overflow is Turkish combined with the largest font size.
- **Acceptance:**
  - **5 pts:** disputes the premise with evidence from the table (an example or the ratio) **and** proposes a largest-font test in Turkish on concrete screens with pass criteria such as no truncation, no overflowing buttons, and buttons still reachable. Screens could include the check-in button, the dialogs, and the biometric-changed message. iOS AX sizes or Android maximum font scale should be named or implied.
  - **3 pts:** asks for the Turkish locale in large-font tests without challenging the premise or citing evidence.
  - **0 pts:** anything less.
  - Optional mentions earn no extra points: Turkish İ/ı casing and the Android 14 non-linear 200 % font scaling.

### K4 — Biometric enrolment change invalidates the key (easy, 5 pts, expected P2)
- **Where:** plan 5.1 covers success, failure, lockout, a device without biometrics, and disabling the feature. It has no enrolment-change scenario.
- **Why it matters:** brief §4.1 says the key is created with `setInvalidatedByBiometricEnrollment(true)` on Android and `.biometryCurrentSet` on iOS. Adding a fingerprint or face, or removing the biometrics, invalidates the key. Android raises `KeyPermanentlyInvalidatedException`. The brief requires a specific message, password login, an offer to re-enable, no crash and no lockout. This is a classic crash or lockout path.
- **Acceptance:**
  - **5 pts:** a scenario that enables biometric login, then adds a new fingerprint or face (or removes all biometrics, or removes the passcode on iOS), then relaunches. The expected result must match the brief: the message, password login, re-enable offer, and no crash or lockout. Both platforms, or "iOS ve Android".
  - **3 pts:** the enrolment change is mentioned but has no expected behaviour, or covers only one platform.
  - **0 pts:** anything less.

### K5 — Location authorisation variants (medium, 8 pts, expected P2)
- **Where:** TC-LOC-01 says "izin diyaloğunda 'Her Zaman İzin Ver' seç" on iOS and Android. TC-LOC-03 tests approximate location on **Android 12+ only**. The plan never mentions "Uygulamayı Kullanırken", "Bir Kez İzin Ver" or iOS "Kesin Konum".
- **Why it is wrong:**
  - **(a)** On iOS 13+, the first prompt offers only *Allow Once / Allow While Using App / Don't Allow*. "Always" comes from a later upgrade prompt or from Settings.
  - On Android 11+, for apps targeting API 30 or higher, "Allow all the time" is never in the dialog. It is granted on the Settings page after the foreground permission, which brief §4.3 describes as foreground first, then background. So TC-LOC-01 as written cannot be executed, and the common real outcomes (While-Using only, Allow Once, Android "only while using" or "only this time") are untested. In those cases the brief requires auto-arrival off, the "Geldim, check-in yap" fallback, and an explanation.
  - **(b)** iOS 14+ has a Precise Location toggle. The brief requires precise location and a fallback on **both** platforms ("Bu kural iOS ve Android için aynıdır"). The plan covers approximate location only on Android, and a 150 m geofence cannot work with approximate location.
- **Acceptance:**
  - **(a), up to 5 pts:**
    - **5 pts:** the agent says the TC-LOC-01 step is wrong or unexecutable on iOS and/or Android (first dialog has no Always; Android 11+ goes through Settings for background) **and** proposes While-Using/Once tests with the fallback expected.
    - **3 pts:** only one of those two.
  - **(b), 3 pts:** a test with iOS Precise Location off, set at the prompt or later in Settings, expecting auto-arrival off, the fallback and the explanation. A temporary full-accuracy request is optional.

### K6 — Android 14+ partial ("selected photos") media access (medium, 8 pts, expected P2)
- **Where:** TC-DOC-04 covers only grant/deny of `READ_MEDIA_IMAGES` on Android 13+.
- **Why it matters:** brief §4.4 says the app uses its **own** gallery grid, declares `READ_MEDIA_VISUAL_USER_SELECTED`, and must work for "tam, kısmi veya ret". On Android 14+ (81.3 % of supported Android users) the user can choose "Select photos". The custom grid must then show only the selected items and offer a way to select more, which re-requests permission. Upload must still work. Untested, this produces empty grids, crashes, or users stuck without a re-select path.
- **Acceptance:**
  - **8 pts:** an Android 14+ partial-access scenario with concrete steps (choose "Fotoğraf ve videoları seç" / "Select photos") and an expected result: only the selected photos are visible, re-selection or "select more" works, upload succeeds. It may also cover the change from partial to full or none in Settings, and behaviour after an app restart.
  - **5 pts:** partial access is named without concrete steps or expected result.
  - **0 pts:** anything less.

### K7 — Time zone and device clock (medium, 8 pts, expected P1)
- **Where:** TC-APT-07 expects the appointment time to be converted to the device time zone (14:30 TSİ shown as 13:30 in Berlin). There is no test with a wrong device clock.
- **Why it is wrong:** brief §4.2 says times are **always** shown in Europe/Istanbul with "TSİ", whatever the device time zone or clock. As written, TC-APT-07 would fail the correct implementation and pass a defect that makes patients arrive at the wrong time. The brief also says the countdown and check-in window use **server time** even when the device clock is wrong, and none of TC-APT-04/05/06 manipulates the device clock.
- **Acceptance:**
  - **(a), 5 pts:** says TC-APT-07's expected result contradicts the brief and must be "unchanged, 14:30 TSİ".
  - **(b), 3 pts:** proposes a wrong device clock test (automatic time off, clock moved forward or back) where the countdown and check-in window still follow server time. Offline check-in timestamp correction is an equally valid variant.
  - Proposing additional time-zone tests without flagging the wrong expected result earns at most 2 pts in total.

### K8 — Android 12+ unverified App Link opens in the browser (medium, 8 pts, expected P2)
- **Where:** TC-DL-03 expects that, when domain verification fails on Android 12+, the system shows an "Open with / Birlikte aç" chooser and the user picks PoyrazKlinik.
- **Why it is wrong:** since Android 12, unverified http/https links open in the default browser and no disambiguation dialog is shown. The brief (§4.8) expects the browser to open a web page with an appointment summary, "Uygulamada aç" (custom scheme) and a store link. As written, the TC tests a behaviour that cannot occur and leaves the real fallback unverified.
- **Acceptance:**
  - **(a), 5 pts:** states the TC-DL-03 expectation is wrong (no chooser on 12+; opens in the browser) and gives the correct expected result: the web fallback with "Uygulamada aç" and the store link.
  - **(b), 3 pts:** concrete ways to induce or observe verification failure: make `assetlinks.json` unreachable, return 404 or a redirect, or use a wrong fingerprint; run `adb shell pm get-app-links com.poyrazklinik.app` or `pm verify-app-links --re-verify`; or the iOS Universal Link fallback cases (AASA unreachable, the user chose "open in Safari"). Any one solid method counts.

### K9 — Process death in the middle of the queue flush (hard, 11 pts, expected P1)
- **Where:** plan 5.6 covers network loss (TC-OFF-03), backgrounding (TC-OFF-04), server 500 (TC-OFF-06), and idempotency **only at the API level via Postman** (TC-OFF-07). Nothing tests the client being killed while it flushes.
- **Why it matters:** brief §4.6 says a record is deleted locally only after 201 or 200, and its `idempotencyKey` is generated once at creation and reused. The dangerous window is when the server has accepted a record (201) and the process dies before the local delete. On restart the client must resend the **same persisted key**, the server must answer 200, and exactly one record may exist. The record could be a symptom entry, a document or a check-in. A regenerated key, a key held only in memory, or a non-transactional dequeue produces duplicate medical records or lost ones. An API-level Postman test cannot reveal client-side defects.
- **Acceptance:**
  - **11 pts:** a client-side test that kills the process (force stop, `adb shell am kill`, swipe-kill, a crash, low-memory kill, or an Xcode stop) **during the flush**. It must explicitly target the window after the server accepts but before the local removal, or check for duplicates and loss through idempotency-key reuse after restart. Expected: same key resent, 200 returned, a single server record, queue cleared, FIFO order kept, nothing lost.
  - **6 pts:** "kill the app during sync, then check for no loss and no duplicates", without the commit window or the idempotency connection.
  - **3 pts:** only "the app is killed while items are pending", with no flush timing.
  - **0 pts:** anything less.

### K10 — Background execution expectations are wrong (hard, 11 pts, expected P2)
- **Where:** TC-OFF-05 expects that after the app is closed, *including a force stop*, Android sends the queue via WorkManager "en geç 15 dakika içinde" (within 15 minutes at most). It also expects iOS to send it via `BGAppRefreshTask` "15 dakikalık periyotlarla" (in 15-minute periods).
- **Why it is wrong:**
  - (a) A force-stopped Android app is in the stopped state. Its WorkManager/JobScheduler work and alarms do not run until the user launches it again. The plan's own TC-PUSH-05 acknowledges this logic for push, so the plan contradicts itself.
  - (b) `BGAppRefreshTask` is opportunistic. The system decides when, or whether, it runs (the brief says "zamanlamayı sistem belirler"). It does not run when Background App Refresh is off or in Low Power Mode, and it typically does not run after the user force-quits the app.
  - (c) Doze, App Standby buckets, Battery Saver and OEM battery managers can postpone work. Xiaomi accounts for 31 % of supported Android users and Samsung's sleeping-apps feature has the same effect. The plan tests none of these.
- **Acceptance (additive, maximum 11):**
  - **(a), 4 pts:** says the Android force-stop expectation is wrong.
  - **(b), 4 pts:** says the iOS periodic, guaranteed expectation is wrong.
  - **(c), 3 pts:** at least 2 concrete constrained-background tests, each expecting delivery at the next foreground or connectivity trigger with no loss. Examples: `adb shell dumpsys deviceidle force-idle`, `adb shell am set-standby-bucket com.poyrazklinik.app restricted`, Battery Saver, MIUI/HyperOS or Samsung battery restrictions, iOS Low Power Mode or Background App Refresh off.

### K11 — App Links will fail for every Play-installed user (hard, 11 pts, expected P1)
- **Where:** brief §4.8 lists two certificates. The upload key `07:A5:55:…:3E:6F` signs QA/Firebase builds. The app-signing key `56:89:17:…:4A:D4` signs **all Google Play installs**. The live `assetlinks.json` lists **only the upload key**. The plan (§3, and the note under 5.8) runs all functional and deep-link tests on Firebase App Distribution builds signed with the upload key, and checks the production build only with a post-release smoke test of launch and login.
- **Why it matters:** App Links verification compares the installed APK's signing certificate with `assetlinks.json`. QA builds verify, so every planned test passes. Production installs from Play fail verification, so for every Android user, SMS and e-mail links open in the browser instead of the app. The plan structurally cannot detect this before release. It is a release-blocking production defect.
- **Acceptance:**
  - **11 pts:** identifies that the Play app-signing fingerprint is missing from `assetlinks.json`, or that only the upload key is listed, and that Play-installed builds will therefore fail verification. It also says the plan would not catch it because of the QA-only builds and the post-release smoke test. It proposes adding the app-signing SHA-256 (both keys may be listed) **and** a pre-release test on a Play-signed build: an internal testing track or internal app sharing, checking `pm get-app-links` shows `verified`.
  - **8 pts:** spots the fingerprint mismatch but gives no test or fix.
  - **4 pts:** only says "test App Links on a production or Play-signed build before release" without spotting the mismatch.
  - **0 pts:** anything less.

### K12 — The plan's device matrix is miscounted (hard, 11 pts, expected P2)
- **Where:** plan §6. The plan claims Android 77 000 / 89 100 = 86.4 % and iOS 52 400 / 62 700 = 83.6 %.
- **Why it is wrong:** the plan breaks its own rule (one device covers only its model + OS row, supported users only):
  - Android: Galaxy A54/15 is credited 18 500, which equals the 15 and 16 rows. Galaxy A10/11 is credited 8 300, which includes the **Android 9** row (below the minimum). Galaxy Tab A8 is a **tablet** (unsupported, and excluded by the plan's own §7).
  - iOS: iPhone 13/26 is credited 13 300 (the 26 and 18 rows) and iPhone 11/26 9 900 (the 26 and 18 rows). iPhone 8/16 is credited 2 600, which includes the **iOS 15** row. iPad (9. nesil) is a **tablet**.
  - Correct coverage: **Android 59 600 / 89 100 = 66.9 %**, **iOS 40 400 / 62 700 = 64.4 %**. Both are below the 80 % target, so the exit criterion is not met.
- **Acceptance:**
  - **11 pts:** both platforms are shown to be below 80 %, with recomputed values within ±2 pp of 66.9 % and 64.4 %, and at least one concrete cause named per platform (an unsupported row counted, or one device credited for two OS rows).
  - **7 pts:** invalid counting is identified on both platforms and the agent concludes that the target is not met, but the numbers are missing or off by more than 2 pp.
  - **4 pts:** only one platform, or only one cause, with no conclusion that the target is below 80 %.
  - **0 pts:** anything less.

## 4. Device matrix (M1–M5, 20 pts)

Compute M1 to M3 automatically with `mobile2_grade.py grade <workspace>`. The script normalises model names (it drops manufacturer prefixes and "5G", and maps "2nd gen" to "2. nesil") and takes the first integer of the OS field.

| ID | Rule | Points |
|---|---|---|
| M1 | Android coverage ≥ 80 % under the plan rule (model + OS row, supported denominator 89 100) **and** at most 11 Android rows | 6 |
| M2 | iOS coverage ≥ 80 % (denominator 62 700) **and** at most 9 iOS rows | 6 |
| M3 | No unsupported rows (below the minimum OS or a tablet): −1.5. No rows absent from the CSV or with an unknown platform: −1.5 | 3 |
| M4 | The coverage % reported in `plan_inceleme.md` for each platform is within ±1.0 pp of the grader's value **for the agent's own matrix**. The script auto-detects; the grader confirms by reading. 1.5 per platform | 3 |
| M5 | Manual. 1 pt: the justification explicitly applies the plan rule (exact model + OS row) and excludes unsupported rows and tablets. 1 pt: it includes a minimum-supported-OS device (Android 10 / iOS 16) or explains why not | 2 |

A row duplicated in the matrix counts toward the budget but covers nothing extra. An unmatched row also counts toward the budget.

## 5. Traps (−4 each when triggered)

| ID | What the inputs show (correct) | Triggered when the agent… | Not penalised |
|---|---|---|---|
| **T1** | iOS uses `PHPickerViewController`. No photo-library permission is requested, there is no `NSPhotoLibraryUsageDescription`, and TC-DOC-05 expects no prompt. This is correct, because PHPicker runs out of process and needs no permission. | reports missing iOS photo-library permission tests (grant/deny/"Limited/Seçili Fotoğraflar"), or demands that `NSPhotoLibraryUsageDescription` be added, as a gap or defect | iOS camera-permission tests; re-confirming that no prompt appears |
| **T2** | The plan excludes DST transition tests because Turkey has used UTC+3 permanently since 2016 and times are shown in clinic time. This is correct. | claims Europe/Istanbul observes DST, or that appointment times would shift with DST, or reports "DST tests missing" as a plan gap | device time-zone or clock tests (K7), including a device in a DST zone checking that TSİ stays unchanged |
| **T3** | The CSV has the same model on two OS versions: Galaxy A54, Galaxy A10, Redmi Note 8, P30 Lite, iPhone 13, iPhone 11, iPhone 12 and iPhone 8. These are legitimate distinct rows, and no exact duplicates exist. | reports them as duplicate or erroneous data, or asks for them to be deduplicated or merged | noting that one device covers only one OS row |
| **T4** | TC-PUSH-05: a force-stopped Android app receives no FCM push until it is relaunched. This is expected platform behaviour and the plan correctly does not log it as a bug. | reports this as a defect, or asks that push "must arrive even after force stop" | suggesting a check of the in-app inbox or SMS after relaunch; using TC-PUSH-05 to argue K10(a) |

## 6. Other false positives (−2 each, maximum −10)

Penalise only claims that the inputs or platform facts clearly refute, and only when they are presented as a gap or defect:
- "iOS 26 does not exist" or "iOS versions in the CSV are wrong". Apple switched to year-based numbering in 2025, so iOS 26 is valid.
- Demanding iPad or Android-tablet UI testing as a P1/P2 plan defect. The brief puts tablets out of scope. A low-priority remark that iPad compatibility mode is out of scope is neutral. Tablets placed in the matrix are penalised through M3 only, not here.
- Claiming the plan's supported denominators (89 100 / 62 700) are wrong.
- Claiming TC-DOC-03 is wrong (Android 10–12 correctly uses `READ_EXTERNAL_STORAGE`), or that Android 13+ should still use `READ_EXTERNAL_STORAGE`.
- Claiming that the TC-APT-04/05 boundaries (31/29 minutes before, 16 minutes after) are wrong.
- Claiming the AASA file is malformed (the `components` format is valid) or that the iOS app ID is wrong.
- Claiming the payment result should be taken from the client-side 3DS redirect. That contradicts brief §4.7.
- Any invented requirement that the brief contradicts.

## 7. Valid but unplanted findings (0 points, no penalty)

Examples:
- Test cases have no priority column, although §6 says P1 cases run on all devices.
- No forced-update screen test for versions below 4.0.
- Users stuck on 4.2 because of the minimum OS (messaging, server compatibility).
- Push-token refresh after upgrade.
- 3DS return when the process is killed during payment.
- Turkish İ/ı casing.
- Dark mode.
- Network throttling.
- Android 16 edge-to-edge or predictive back.
- Low storage while uploading 10 MB files.
- OEM autostart restrictions affecting geofence delivery. This may also support K10(c).
- Interruptions such as calls.
- Logout, account switching and the queue.

## 8. Form (F1–F2, 4 pts)

| ID | Rule | Points |
|---|---|---|
| F1 | Automatic. `cihaz_matrisi.csv` exists and parses with the exact header: 1 (0.5 if readable but the header differs). `plan_inceleme.md` exists and is not empty: 1 | 2 |
| F2 | Manual. At least 80 % of findings have a priority, a plan reference (where one applies), and concrete steps with an expected result: 2. At least 50 %: 1 | 2 |

## 9. Grader procedure

1. Run `python mobile2_grade.py grade <workspace>`. Record M1–M3 and F1, and confirm M4 by reading the report.
2. Read `plan_inceleme.md` in full. Score K1–K12 with §3 and use the script's keyword hints only to locate passages. Apply the priority rule: −1 when an expected-P1 item is rated P3.
3. Check T1–T4 and §6, then score M5 and F2.
4. Record a per-item table: K1..K12, M1..M5, F1..F2, T1..T4, FP, total out of 120.

## 10. Verification log (author)

- `mobile2_grade.py verify`: **62/62 PASS**. It checks that the inputs parse, that every K fact is reproduced from the input files (plan text versus brief text, the strings-table lengths, the assetlinks JSON fingerprints, and the matrix recomputation from the CSV), that the trap facts hold, and that the budget is feasible (Android needs 10 devices with a budget of 11, iOS needs 8 with a budget of 9).
- `mobile2_grade.py selftest`: **OK**. Checked cases:

  | Case | Android | iOS | Outcome |
  |---|---|---|---|
  | Optimal matrix | 83.6 % | 83.7 % | full M1–M3 |
  | Name and version variants | 82.3 % | 84.1 % | still match |
  | Team plan's own matrix | 66.9 % | 64.4 % | fails, M3 = 1.5 |
  | Model-level aggregation | 74.1 % | 72.2 % | fails both |
  | Naive top-N by raw users | 77.4 % | — | Android fails, M3 = 1.5 |
  | Over budget | — | — | no coverage points |
  | Unmatched model | — | — | M3 deduction |
