# KEY — trial-mobile (mobile app test planning / review, no device)

Grader-only. Never place this file (or any part of it) in the agent's working directory.

Trial folder: `C:\projeler\TestSkills\evals\trial-mobile\`
Agent inputs: `TASK.md`, `girdiler/URUN_OZETI.md` (brief), `girdiler/cihaz_os_dagilimi.csv` (analytics),
`girdiler/MEVCUT_TEST_PLANI.md` (plan, items MT-01..MT-35, matrix D1..D7).
Expected output: `INCELEME_RAPORU.md` (Turkish).

App: "Bakkalix" v3.0 (fictional), grocery delivery + wallet, iOS 16.0+ / Android 9.0 (API 28)+,
card payments with 3D Secure, wallet, camera QR payment in stores, push, location, biometric login
with app-PIN fallback, offline cart, SMS campaign deep links (Universal/App Links), third-party
attribution SDK reading IDFA/AAID, v2.x -> v3.0 local data migration.

---

## 1. Ground-truth facts (from the inputs)

| Fact | Source |
|---|---|
| Min supported: iOS 16.0, Android 9.0 (API 28); iOS 15 and Android 8.x cannot install v3.0 | brief §2 |
| Phones + foldable outer screen: portrait only. Tablets + foldable inner screen: portrait + landscape | brief §2 |
| Biometric failure x5 / lockout -> 6-digit Bakkalix PIN; device passcode fallback deliberately NOT offered (GÜV-114) | brief §3.1 |
| Tokens move UserDefaults -> Keychain, SharedPreferences -> Keystore-encrypted store in v3.0 | brief §3.1 |
| Search follows Turkish case rules; ASCII spellings (`INCIR`, `sut`) get only a "Bunu mu demek istediniz" suggestion (ARA-31) | brief §3.2 |
| Local cart migrates SQLite `sepet` (TL decimal) -> `cart_items` (kuruş integer) on first launch | brief §3.3 |
| Approximate location must still find a store; pin corrected manually | brief §3.4 |
| Every payment carries client UUID `odeme_istek_no`; server must not charge twice for the same id | brief §3.5 |
| No IAP: only physical goods / delivery are sold | brief §3.5 |
| QR payment only on phones (hidden on tablets) | brief §3.6 |
| Deep links `/siparis/{siparis_no}` and `/cuzdan/yukle?tutar=` require a session; without one -> login, then continue; users see only their own orders | brief §3.8 |
| OlcumPro SDK reads IDFA (iOS) / AAID (Android) | brief §3.9 |
| WCAG 2.1 AA, text scaling up to 200 %, VoiceOver + TalkBack end-to-end ordering | brief §3.10 |
| Upgrade from v2.8.x / v2.9.x must keep session, cart, addresses, biometric preference; 95 % of active users are on v2.8/v2.9 | brief §1, §3.11 |

---

## 2. Planted defects / gaps (K1..K10)

Scoring convention: points are awarded if the finding appears **anywhere** in the report
(findings list, proposed tests, or matrix section). Turkish or English wording both count.
The grader should record a short quote from the report as evidence for every awarded item.

### K1 — No process-death / state-restoration test (hard) — severity HIGH — 3 pts

- **What:** The plan never tests the OS killing the app process while it is in the background and
  the user returning (Android low-memory kill / "Etkinlikleri tutma" (Don't keep activities) /
  `adb shell am kill`, background process limit; iOS termination under memory pressure). MT-18
  only backgrounds the app for 10 s (process stays alive), MT-16 only switches to the bank app and
  back, MT-19 only an incoming call. None of them exercise process death.
- **Why it matters:** During 3D Secure the user sits in a banking app (brief §3.5) or the camera is
  open; mid/low-end Android devices (Redmi 12C, Galaxy A13 ~14 % of Android users) frequently kill
  the backgrounded process. On return the app cold-starts: lost checkout state, lost 3DS result,
  user may pay again or think payment failed; restored forms must not persist PAN/CVV to disk.
- **Acceptance (full, 3):** report names the scenario of the **OS / system terminating the app
  process** (terms such as process death, "işlem/uygulama sistem tarafından sonlandırılır",
  "bellek yetersizliğinde öldürülür", Don't keep activities / Etkinlikleri tutma, `am kill`,
  saved-instance-state / state restoration after kill) **and** expects the flow/state to be
  restored or reconciled (checkout form, 3DS result / order status, cart, deep-link target).
- **Partial (1):** only the *user* force-closing / swiping away the app mid-payment and checking
  order-status reconciliation on relaunch, without the OS-kill angle.
- **Not accepted:** "arka plana al / öne getir", "uygulama değiştir", "gelen arama", "kesintiler",
  rotation/configuration change alone — these are already in the plan (MT-18, MT-16, MT-19, MT-27).

### K2 — Permission revoked later from system Settings (medium) — severity MEDIUM — 2 pts

- **What:** Permission tests only cover the first prompt (MT-12 grant, MT-13 deny, MT-23 camera
  deny on first QR attempt). Missing: user grants camera/location/notification, later turns it off
  in iOS Settings / Android App info while the app is backgrounded (both OSes kill the process on
  revoke), or Android 11+ auto-resets permissions of unused apps.
- **Why it matters:** App must re-check permission on every use; stale "granted" state leads to a
  crash or black camera at the checkout counter (QR payment), or silent loss of order notifications.
- **Acceptance (2):** report explicitly describes revoking / turning off a previously granted
  permission from system Settings (or Android permission auto-reset / "kullanılmayan uygulama
  izinlerini kaldır") and the expected app behaviour. Any of camera, location, notifications.
- **Not accepted:** first-time deny only, "Ayarlar'a git" button test (already MT-23).

### K3 — One-time / approximate location states missing (medium) — severity MEDIUM — 2 pts

- **What:** MT-12/MT-13 treat location as binary grant/deny. Missing: iOS "Bir Kez İzin Ver"
  (Allow Once), Android 11+ "Yalnızca bu sefer" (Only this time) — permission gone on next session
  (Android also applies one-time to camera); and approximate location (iOS "Kesin Konum" off,
  Android 12+ "Yaklaşık"), which brief §3.4 explicitly requires (store found, pin corrected by hand).
- **Acceptance (2):** report names **either** one-time permission (Allow Once / Only this time /
  bir kez / yalnızca bu sefer) **or** approximate / imprecise location as a missing test state.
  Both mentioned = still 2.
- **Not accepted:** generic "konum izin testleri eksik" with no mention of either state.

### K4 — Offline mid-payment retry has no double-charge / idempotency check (hard) — severity CRITICAL — 3 pts

- **What:** MT-17 ("Öde" -> connection drops -> "Tekrar dene") expects only "Ödeme tamamlanır,
  sipariş onay ekranı açılır". It never verifies that the card was charged **once**, that one
  order exists, that the retry reuses the same `odeme_istek_no` (brief §3.5), nor the nastier case
  where the request reached the server/bank and only the response was lost (timeout after charge).
  The test as written passes even if the customer is charged twice.
- **Why it matters:** Duplicate charges on a payment/wallet product = direct financial loss,
  chargebacks, customer complaints, regulator exposure. Also applies to wallet top-up and QR pay.
- **Acceptance (3):** report ties the payment retry / network loss during payment to **duplicate
  charge or duplicate order prevention** — keywords: çift çekim, mükerrer/çift sipariş, iki kez
  çekim, idempotency/idempotent, aynı `odeme_istek_no`, "yanıt kayboldu ama çekim yapıldı",
  "tekrar denemeden önce ödeme durumunu sorgula", verify single transaction in bank/sandbox panel.
- **Not accepted:** "ödeme sırasında ağ kesintisi testi ekleyin" or "timeout mesajı" without the
  double-charge / idempotency angle (MT-17 already covers the happy retry).
- **Priority bonus (see §5):** +1 if ranked P0 or P1.

### K5 — Deep links to authenticated screens never tested without a session (medium) — severity CRITICAL — 3 pts

- **What:** Only MT-29 (campaign link while logged in) and MT-30 (product link, app not installed).
  Nothing for `/siparis/{siparis_no}` or `/cuzdan/yukle?tutar=` (brief §3.8) when logged out,
  after logout, with an expired refresh token, or on a fresh install; nothing for continuing to the
  target after login; nothing for another user's order number.
- **Why it matters:** SMS links are sent en masse; an auth-required screen opening without login
  (or showing another user's order / pre-filled wallet top-up) is a data-exposure / fraud bug.
- **Acceptance (full, 3):** report describes opening an auth-required deep link (sipariş or cüzdan)
  **without a valid session** (logged out / expired / fresh install / biometric-locked) and expects
  login gate + continuation to the target (or at least the login gate).
- **Partial (2):** only the other-user order number (authorization / IDOR) case, or only
  "post-login continuation" without stating the logged-out entry condition.
- **Not accepted:** generic "geçersiz kampanya kodu", "uygulama yüklü değilken" (already MT-30),
  "derin bağlantı testleri artırılmalı" without the auth dimension.
- **Priority bonus (see §5):** +1 if ranked P0 or P1.

### K6 — No upgrade test from v2.8.x / v2.9.x; plan forces clean install (medium) — severity HIGH — 3 pts

- **What:** Plan §2 mandates uninstall + clean install before every run, so the v2.x -> v3.0 store
  update path (95 % of active users) is never exercised. v3.0 migrates the cart DB (`sepet` TL
  decimal -> `cart_items` kuruş integer) and moves tokens to Keychain/Keystore (brief §3.1, §3.3,
  §3.11). MT-32 only checks the force-update gate for v2.4.
- **Why it matters:** Migration bugs hit almost every user on day one: forced logout, lost cart,
  price x100 errors from the TL->kuruş conversion, lost biometric preference, crash loops.
- **Acceptance (full, 3):** report flags the missing upgrade/update-over-install test **and**
  names at least one migration concern (cart migration / price unit conversion, token move to
  Keychain/Keystore, session kept, addresses or biometric preference kept), **or** explicitly
  criticises §2's always-clean-install policy as hiding upgrade defects.
- **Partial (2):** "güncelleme (upgrade) testi eksik" with no data/migration aspect.
- **Not accepted:** force-update screen only (already MT-32), install/uninstall only.

### K7 — Accessibility limited to contrast (easy) — severity MEDIUM — 2 pts

- **What:** MT-33 only measures colour contrast. Brief §3.10 requires text scaling up to 200 %
  (iOS Dynamic Type / Android font size) and full ordering with VoiceOver and TalkBack.
- **Acceptance:** 1 pt for font scaling (Dinamik Yazı / büyük yazı tipi / yazı boyutu %200 /
  display size), 1 pt for screen reader (VoiceOver and/or TalkBack / ekran okuyucu).

### K8 — Plan wrongly states Android needs no notification permission (medium) — severity HIGH — 2 pts

- **What:** MT-26: "Android: bildirim izni istenmez (varsayılan açık), izin testi gerekmez".
  Wrong since Android 13 (API 33): `POST_NOTIFICATIONS` is a runtime permission (targetSdk 36 per
  brief §2). From the CSV, Android 13+ = **77.0 %** of Android users. The deny path (order status
  must remain visible in-app) and the "ask after first order" timing are untested on Android.
- **Acceptance (full, 2):** report says MT-26's Android statement is wrong / Android 13+ (API 33,
  POST_NOTIFICATIONS, runtime notification permission) requires a permission prompt and tests.
- **Partial (1):** "Android'de de bildirim izni / reddi test edilmeli" with no version or rationale.

### K9 — iOS App Tracking Transparency (ATT) missing (medium) — severity MEDIUM — 2 pts

- **What:** Brief §3.9: OlcumPro SDK reads IDFA. On iOS 14.5+ that requires the ATT prompt
  (`NSUserTrackingUsageDescription`); the plan only has KVKK consent (MT-31). Missing: ATT prompt
  shown at the right moment, deny/"Uygulamadan izlememesini iste" path (SDK must not read IDFA /
  fingerprint, app fully usable), and Settings > Privacy > Tracking toggled off later.
- **Why it matters:** App Store rejection (Guideline 5.1.2) and privacy/legal exposure; KVKK
  consent does not replace ATT.
- **Acceptance (2):** ATT / App Tracking Transparency / "izleme izni (tracking)" prompt / IDFA
  consent on iOS named as missing. Mentioning the deny path is expected but not required.
- **Not accepted:** KVKK / marketing consent only (already MT-31).

### K10 — Device matrix wrong: oldest supported OS missing, coverage claim false (easy + hard) — severity HIGH — 4 pts

- **What:** Plan §3 D1–D7 contains iOS 26/18 and Android 16/15/14 only. It says it covers
  "iOS %91, Android %83" and that "iOS 17 altı, Android 13 altı" shares are low.
  - (a) Oldest supported versions **iOS 16** (iPhone 8, 5.1 % of iOS users) and **Android 9 / API 28**
    (Redmi 7, 2.5 %) are not tested at all (brief §2 minimum). These are also the only Touch ID
    phones / oldest WebView / pre-Android-13 permission model in scope.
  - (b) Recomputed from the CSV, the plan matrix covers **Android 63.05 %** (below 80 %) and
    **iOS 84.26 %** (not 91 %). Android below 13 is **22.96 %** of all Android users (21.43 % on
    supported versions) — not "low".
- **Acceptance (a) — 2 pts:** 1 pt per platform for stating that the oldest supported OS (iOS 16,
  Android 9 / API 28) is missing from the existing matrix.
- **Acceptance (b) — 2 pts:** 2 pts if the report recomputes the existing matrix's Android coverage
  (≈63 %, tolerance ±2 pp) or the Android below-13 share (≈21–23 %) and flags the claim as false /
  below the 80 % target; 1 pt if it only says the claim is wrong/unverifiable without a correct
  number, or only recomputes iOS (≈84 %).

### Severity / difficulty overview

| ID | Topic | Severity | Difficulty | Max pts |
|---|---|---|---|---|
| K1 | Process death / state restoration | High | Hard | 3 |
| K2 | Permission revoked in Settings | Medium | Medium | 2 |
| K3 | Allow once / approximate location | Medium | Medium | 2 |
| K4 | Payment retry idempotency (MT-17) | Critical | Hard | 3 |
| K5 | Deep link to auth screen without session | Critical | Medium | 3 |
| K6 | Upgrade v2.x -> v3.0 migration / clean-install policy | High | Medium | 3 |
| K7 | Font scaling + screen reader | Medium | Easy | 2 |
| K8 | Android 13+ notification permission (MT-26 error) | High | Medium | 2 |
| K9 | iOS ATT | Medium | Medium | 2 |
| K10 | Matrix: oldest OS + false coverage claim | High | Easy (a) / Hard (b) | 4 |
| | **Total K** | | | **26** |

---

## 3. Traps (correct items that look odd) — penalty −2 each if reported as a defect

| ID | Plan item | Why it is correct | Counts as false positive when the report… | Not a false positive |
|---|---|---|---|---|
| T1 | §1 Kapsam dışı: no IAP (StoreKit / Play Billing) tests | Brief §3.5: no digital goods or subscriptions; physical goods/delivery must use card/other payment, not IAP (store rules) | …says IAP / subscription / restore-purchase / StoreKit / Play Billing tests are missing, or that scoping IAP out is a gap | Neutral remark to keep store-review notes on card payments |
| T2 | §1 Kapsam dışı: no landscape tests on phones | Brief §2: phones and foldable outer screen are portrait-locked by product decision; tablets and foldable inner screens ARE tested in landscape (MT-27) | …says rotation/landscape tests on **phones** are missing or that the exclusion is a defect | Landscape on tablet / foldable inner screen; Android 16 ignoring orientation locks on large screens (sw ≥ 600dp) for targetSdk 36; fold/unfold; rotation used as config-change trigger on tablets |
| T3 | MT-08 Turkish search: `INCIR` gets no direct result, only a suggestion | Brief §3.2 / ARA-31: Turkish case rules (I↔ı, İ↔i) and suggestion-only for ASCII spellings is the specified behaviour; `ISPANAK`→ıspanak and `İNCİR`→incir are correct | …calls MT-08's expected result wrong, says `INCIR` must match `incir`, or calls the Turkish-I handling a bug in the plan | Suggesting extra Turkish-character tests (ş, ğ, ü, ö, ç), or clearly labelled product feedback questioning ARA-31 (not presented as a plan error) |
| T4 | MT-05: after 5 failed biometric attempts app PIN is required and **no device passcode option** | Brief §3.1 / GÜV-114 deliberately excludes device-passcode fallback | …says MT-05 is wrong, that the device passcode / LAPolicy deviceOwnerAuthentication / DEVICE_CREDENTIAL fallback must be offered or tested as expected behaviour | Tests that the PIN screen itself works, PIN lockout, biometric enrollment change |

Each trap is penalised at most once per report.

---

## 4. Device-matrix objective check

### 4.1 Reference numbers (computed from `cihaz_os_dagilimi.csv`, active-user counts)

iOS (151,625 users; supported 146,990 = 96.94 %):

| OS | Share of all iOS | Cumulative (supported, desc) | Note |
|---|---|---|---|
| 26 | 62.59 % | 62.59 % | |
| 18 | 21.66 % | 84.26 % | |
| 17 | 7.57 % | 91.82 % | |
| 16 | 5.12 % | 96.94 % | oldest supported |
| 15 | 3.06 % | — | unsupported (cannot install v3.0) |

Android (249,313 users; supported 245,514 = 98.48 %):

| OS (API) | Share of all Android | Cumulative (supported, desc) | Note |
|---|---|---|---|
| 15 (35) | 23.94 % | 23.94 % | |
| 14 (34) | 21.10 % | 45.04 % | |
| 16 (36) | 18.01 % | 63.05 % | |
| 13 (33) | 14.00 % | 77.04 % | |
| 12 (31) | 9.02 % | 86.06 % | |
| 11 (30) | 5.86 % | 91.93 % | |
| 10 (29) | 4.01 % | 95.94 % | |
| 9 (28) | 2.54 % | 98.48 % | oldest supported |
| 8.1 (27) | 1.52 % | — | unsupported |

- **Minimum OS set for ≥ 80 %:** iOS {26, 18} = 84.26 % (86.91 % of supported). Android
  {15, 14, 16, 13, 12} = 86.06 % (87.40 % of supported). Four Android versions are NOT enough:
  77.04 % of all / 78.24 % of supported — true under either denominator.
- **With oldest supported added (recommended answer):** iOS {26, 18, 16} = 89.38 %;
  Android {16, 15, 14, 13, 12, 9} = 88.60 %.
- **Existing plan matrix:** iOS {26, 18} = 84.26 % (claims 91 %); Android {16, 15, 14} = 63.05 %
  (claims 83 %).
- Alternative row-level interpretation (exact model@OS rows): minimum 6 iOS rows (80.16 %) and
  10 Android rows (84.88 %). Accept this interpretation only if the report defines it explicitly
  and the arithmetic is right.
- Android 13+ (API ≥ 33) = 77.04 % of Android users (used in K8).
- Form factors in data: iPads 7.08 % of iOS (iPad 9th gen on 26, iPad Air 4 on 17);
  Android tablet 3.02 % (Tab A9+), foldables 4.03 % (Z Flip6 on 16, Z Fold5 on 14).
- Touch ID phones: iPhone 8 (iOS 16) and iPhone SE 2 (iOS 17) = 9.70 % of iOS users; the plan's
  iOS devices are all Face ID (useful context for K10a / valid extra).

### 4.2 Matrix checks for the agent's PROPOSED matrix (1 pt each, max 6)

| ID | Check | How |
|---|---|---|
| M1 | iOS proposal reaches ≥ 80 % (unsupported versions not counted) | run checker with the proposal's iOS OS set |
| M2 | Android proposal reaches ≥ 80 % (unsupported versions not counted) | run checker with the proposal's Android OS set |
| M3 | Both oldest supported versions (iOS 16 and Android 9/API 28) are in the proposal (real device preferred; an explicitly assigned simulator/emulator slot also passes) | checker prints M3 per platform; both must pass |
| M4 | iOS 15 / Android 8.1 are not counted as supported coverage (listing them only as "v3.0 must not be offered / v2.8 keeps working" is fine) | read the report's coverage arithmetic |
| M5 | Proposal includes an iPad, an Android tablet and a foldable (all three are supported form factors with distinct behaviour in the brief) | read the proposal |
| M6 | The coverage percentages the report states for its own proposal match the checker within ±1.0 pp (either denominator, if stated) | compare |

### 4.3 Checker (Python 3 stdlib) — save as `check_matrix.py`

```python
#!/usr/bin/env python3
"""Objective device-matrix check for trial-mobile (stdlib only).
Usage:
  python check_matrix.py <cihaz_os_dagilimi.csv>                       # reference numbers
  python check_matrix.py <csv> --ios 26,18,16 --android 16,15,14,13,12,9  # score an OS-version proposal
  python check_matrix.py <csv> --rows "iPhone 15@26;Galaxy A55@15"      # score a row-level (model@os) proposal
"""
import csv, sys, argparse
from collections import defaultdict

MIN_SUPPORTED = {"iOS": "16", "Android": "9"}      # brief section 2
UNSUPPORTED   = {"iOS": {"15"}, "Android": {"8.1"}}  # rows below minimum
PLAN_MATRIX   = {"iOS": {"26", "18"}, "Android": {"16", "15", "14"}}  # D1-D7 in the plan
PLAN_CLAIM    = {"iOS": 91.0, "Android": 83.0}

def load(path):
    rows = []
    with open(path, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            r["n"] = int(r["aktif_kullanici_30g"])
            rows.append(r)
    return rows

def by_os(rows, plat):
    d = defaultdict(int)
    for r in rows:
        if r["platform"] == plat:
            d[r["os_surumu"]] += r["n"]
    return d

def pct(a, b):
    return 100.0 * a / b

def reference(rows):
    for plat in ("iOS", "Android"):
        d = by_os(rows, plat)
        tot = sum(d.values())
        sup = tot - sum(d[v] for v in UNSUPPORTED[plat])
        print(f"== {plat}: total active users {tot}, supported {sup} ({pct(sup, tot):.2f}%)")
        cum = 0
        chosen, reached = [], False
        for v, n in sorted(d.items(), key=lambda kv: -kv[1]):
            flag = " (UNSUPPORTED)" if v in UNSUPPORTED[plat] else (" (OLDEST SUPPORTED)" if v == MIN_SUPPORTED[plat] else "")
            if v not in UNSUPPORTED[plat]:
                cum += n
                if not reached:
                    chosen.append(v)
                    reached = pct(cum, tot) >= 80
            print(f"   OS {v:>4}: {pct(n, tot):6.2f}% of all | cumulative(supported, desc) {pct(cum, tot):6.2f}% of all / {pct(cum, sup):6.2f}% of supported{flag}")
        c_all = pct(sum(d[v] for v in chosen), tot)
        c_sup = pct(sum(d[v] for v in chosen), sup)
        print(f"   MIN OS SET for >=80% of all users: {chosen} -> {c_all:.2f}% of all / {c_sup:.2f}% of supported")
        withmin = sorted(set(chosen) | {MIN_SUPPORTED[plat]}, key=lambda v: -d[v])
        print(f"   + oldest supported: {withmin} -> {pct(sum(d[v] for v in withmin), tot):.2f}% of all")
        pm = PLAN_MATRIX[plat]
        print(f"   PLAN MATRIX OS {sorted(pm)}: actual {pct(sum(d[v] for v in pm), tot):.2f}% of all / "
              f"{pct(sum(d[v] for v in pm), sup):.2f}% of supported (plan claims {PLAN_CLAIM[plat]}%)")
        # model@os row-level minimum (alternative interpretation)
        rs = sorted([r for r in rows if r["platform"] == plat and r["os_surumu"] not in UNSUPPORTED[plat]], key=lambda r: -r["n"])
        cum, k = 0, 0
        for r in rs:
            cum += r["n"]; k += 1
            if pct(cum, tot) >= 80:
                break
        print(f"   row-level (model@os) minimum rows for >=80% of all users: {k} rows -> {pct(cum, tot):.2f}%")
    d = by_os(rows, "Android"); tot = sum(d.values())
    below13 = sum(n for v, n in d.items() if float(v) < 13)
    below13s = sum(n for v, n in d.items() if float(v) < 13 and v not in UNSUPPORTED["Android"])
    print(f"== Plan says 'Android 13 alti payi dusuk': actual below-13 share {pct(below13, tot):.2f}% of all "
          f"({pct(below13s, tot):.2f}% supported-only rows)")
    d = by_os(rows, "iOS"); tot = sum(d.values())
    below17 = sum(n for v, n in d.items() if float(v) < 17)
    print(f"== Plan says 'iOS 17 alti payi dusuk': actual below-17 share {pct(below17, tot):.2f}% of all "
          f"(iOS 16 alone {pct(d['16'], tot):.2f}%)")

def score_os(rows, prop):
    ok_all = True
    for plat, vers in prop.items():
        d = by_os(rows, plat); tot = sum(d.values())
        unknown = [v for v in vers if v not in d]
        uns = [v for v in vers if v in UNSUPPORTED[plat]]
        counted = [v for v in vers if v in d and v not in UNSUPPORTED[plat]]
        cov = pct(sum(d[v] for v in counted), tot)
        m_cov = cov >= 80
        m_min = MIN_SUPPORTED[plat] in vers
        print(f"== {plat} proposal {vers}: coverage {cov:.2f}% of all users (unsupported excluded)")
        print(f"   M{'1' if plat=='iOS' else '2'} >=80%: {'PASS' if m_cov else 'FAIL'}")
        print(f"   M3 oldest supported {MIN_SUPPORTED[plat]} included: {'PASS' if m_min else 'FAIL'}")
        print(f"   M4 note: unsupported versions listed as test targets: {uns or 'none'}  (FAIL M4 only if they are counted as supported coverage)")
        if unknown:
            print(f"   WARNING: versions not in CSV: {unknown}")
        ok_all &= m_cov and m_min
    return ok_all

def score_rows(rows, spec):
    wanted = [s.strip() for s in spec.split(";") if s.strip()]
    for plat in ("iOS", "Android"):
        tot = sum(r["n"] for r in rows if r["platform"] == plat)
        hit = [r for r in rows if r["platform"] == plat and f"{r['model']}@{r['os_surumu']}" in wanted]
        cov = pct(sum(r["n"] for r in hit if r["os_surumu"] not in UNSUPPORTED[plat]), tot)
        print(f"== {plat} row-level coverage of {len(hit)} matched rows: {cov:.2f}% -> {'PASS' if cov >= 80 else 'FAIL'}")
    miss = [w for w in wanted if not any(f"{r['model']}@{r['os_surumu']}" == w for r in rows)]
    if miss:
        print(f"   WARNING: rows not found in CSV: {miss}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--ios")
    ap.add_argument("--android")
    ap.add_argument("--rows")
    a = ap.parse_args()
    rows = load(a.csv)
    if a.rows:
        score_rows(rows, a.rows)
    elif a.ios or a.android:
        prop = {}
        if a.ios: prop["iOS"] = [v.strip() for v in a.ios.split(",")]
        if a.android: prop["Android"] = [v.strip() for v in a.android.split(",")]
        sys.exit(0 if score_os(rows, prop) else 1)
    else:
        reference(rows)
```

Example: `python check_matrix.py C:\eval-runs\mobile\run-01\girdiler\cihaz_os_dagilimi.csv --ios 26,18,17,16 --android 16,15,14,13,12,9`
(exit code 0 = M1, M2, M3 all pass). Verified outputs: good proposal above -> iOS 96.94 %, Android
88.60 %, all PASS; plan matrix `--ios 26,18 --android 16,15,14` -> iOS 84.26 % PASS but M3 FAIL,
Android 63.05 % FAIL.

---

## 5. Scoring rubric

| Component | Points |
|---|---|
| K1–K10 (§2) | 26 |
| M1–M6 matrix checks (§4.2) | 6 |
| Priority bonus: K4 found and ranked P0/P1 (+1); K5 found and ranked P0/P1 (+1) | 2 |
| **Maximum** | **34** |

Penalties:

- **Trap reported as a defect (T1–T4): −2 each** (once per trap).
- **Other false positives: −1 each, capped at −4.** Counts: claiming the plan lacks something it
  clearly has (e.g. "OTP testi yok", "3D Secure hata testi yok", "çevrimdışı sepet testi yok",
  "zorunlu güncelleme testi yok", "gelen arama kesintisi yok", "tablet yatay testi yok"),
  contradicting the brief as if it were fact (e.g. "Android 9 desteklenmiyor", "iOS 15 matrise
  eklenmeli" as a supported target), or wrong arithmetic presented as a finding about the plan.
  Valid extras (§6) and reasonable opinions are **not** false positives.

Gates:

- `INCELEME_RAPORU.md` missing or empty -> score 0.
- Input files modified (hash mismatch, see RUN.md) -> −2.
- Report not in Turkish -> note it; no point deduction (content is graded).

Final: `raw = K + M + bonus − penalties`, floor at 0; normalised = raw / 34.
Also record per-run: number of K items found (0–10), traps hit (0–4), matrix pass (M1 & M2 & M3).

Suggested score sheet (one per run):

```
run_id:        arm: with-skill | no-skill
K1  _/3  evidence: "..."
K2  _/2  K3 _/2  K4 _/3  K5 _/3  K6 _/3  K7 _/2  K8 _/2  K9 _/2  K10a _/2  K10b _/2
M1 _ M2 _ M3 _ M4 _ M5 _ M6 _   (checker command + output line)
bonus K4-prio _ K5-prio _
traps hit: T1 T2 T3 T4        other FPs: n (list)
raw: __/34   normalised: __
```

---

## 6. Valid extras (no points, no penalty)

Reasonable findings not planted; do not penalise them and do not award points:

- Low storage / 150 MB image cache limit, cache eviction, device almost full during migration.
- Biometric enrollment change (new fingerprint/face added -> key invalidated, PIN required).
- Touch ID coverage (iPhone 8 / SE 2 / iPads) — all plan iOS devices are Face ID.
- Keychain items survive uninstall/reinstall on iOS; Android Auto Backup restoring token/prefs to a
  new device; Keystore key loss.
- Android 15 edge-to-edge enforcement (targetSdk ≥ 35); Android 16 large-screen orientation /
  resizability behaviour on tablet and foldable inner screen; multi-window / split screen.
- Doze / battery optimisation / OEM background killers (Xiaomi, Samsung) delaying push;
  notification channels; iOS Focus modes.
- Deep-link parameter tampering (`tutar` outside 50–5,000 TL, negative, non-numeric), link from
  untrusted domain, Universal/App Link verification (AASA / assetlinks.json) failing.
- Android `AD_ID` permission for AAID (targetSdk 33+), iOS privacy manifest for the third-party SDK.
- OTP expiry at 120 s, time-zone/clock change, SMS Retriever on devices without GMS (Huawei P30
  Lite is GMS; newer Huawei are not in data).
- SSL pinning, root/jailbreak detection, screenshot protection on card/PIN screens, PAN/CVV not
  persisted in saved state.
- Low-end performance (Redmi 12C, Galaxy A13), memory, app size, cold start on the oldest device.
- Currency/number formatting (`1.234,56 TL`), Turkish characters in addresses.
- Backend compatibility for users stuck on v2.8.x (iOS 15 / Android 8.1).
- Inconsistency: MT-32 installs v2.4 although §2 mandates clean v3.0 installs; MT-27 needs a
  foldable/iPad that the matrix does not contain (risk §6 mentions renting them).
- QR: poor light, damaged/foreign QR code, screen brightness of cashier display, camera in use by
  another app.

---

## 7. Reference outline of a strong answer (for calibration only)

1. P0/P1: MT-17 idempotency (K4); auth-required deep links without session (K5); upgrade/migration
   & clean-install policy (K6); matrix false coverage + oldest OS (K10); Android 13+ notification
   permission error in MT-26 (K8); process death during 3DS/bank app switch (K1).
2. P1/P2: ATT (K9); permission revoke in Settings / auto-reset (K2); Allow once / approximate
   location (K3); Dynamic Type 200 % + VoiceOver/TalkBack (K7).
3. Matrix e.g. iOS: iPhone 15 or 16 Pro (26), iPhone 13/11 (26), iPhone 12 or XR (18),
   iPhone SE 2 (17, Touch ID), iPhone 8 (16, oldest, Touch ID), iPad 9th gen (26) -> 96.9 %.
   Android: Galaxy A55 (15), Redmi Note 13 Pro (15), Galaxy A34 or Redmi Note 12 (14),
   Galaxy A56/S25 (16), Z Flip6 (16, foldable) or Z Fold5 (14), Redmi 12C (13), Redmi Note 10 (12),
   Tab A9+ (15, tablet), Redmi 7 (9, oldest) -> 88.6 %.
   With arithmetic shown and the four-versions-are-not-enough point for Android (77.0 %).
4. Leaves T1–T4 alone (or explicitly confirms them as correct).
