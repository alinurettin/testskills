---
name: testing-mobile-apps
description: Tests native, hybrid and cross-platform iOS and Android apps (and mobile web) professionally. It drafts traceable mobile test cases for lifecycle, upgrade with data migration, process death, interruptions, offline and lost responses, permissions (Allow Once, Only this time, ATT), push, deep links, biometrics, payments, Turkish localisation, accessibility (TalkBack, VoiceOver, WCAG 2.2) and performance, plus OWASP MASVS v2 security and store-readiness checks. It builds a data-driven device coverage matrix and maps Maestro, Espresso, XCUITest or Appium results back by TC ID. Use this whenever someone wants to test a mobile app, plan devices and OS versions, choose a mobile automation tool, prepare an App Store or Google Play release, or test push, deep links, in-app purchases or app permissions, including Turkish requests such as "mobil uygulama testi", "iOS ve Android testi", "cihaz matrisi", "mobil test senaryoları", "uygulama mağazasına çıkmadan önce test".
license: MIT
metadata:
  suite: qa-suite
  version: "0.6.0"
---

# Testing mobile apps

Mobile apps fail in ways web apps do not: the system kills them in the background, the network drops mid-payment, users deny permissions, the OS changes every year, and a store review stands between a fix and the users. This skill turns those risks into **traceable test cases** (generated, then adapted to the app), a **device matrix based on real usage data**, and an **automation choice** that fits the team, with results mapped back by TC ID.

## Language
Match the user's language (`--lang tr|en`). Platform terms, commands, API names and store guideline numbers stay as they are.

## Reading plan
- This file covers the workflow.
- Read `references/mobile-testing.md` for the detail behind each area: coverage strategy, lifecycle, network, permissions (Android vs iOS table), push, deep links, biometrics, payments, Turkish localisation, the WCAG 2.2 mapping, performance tools and thresholds, OWASP MASVS v2, store readiness, and the automation tool comparison.
- The compact format syntax is at `python scripts/qa_compact.py --help`.

## Prerequisites and safety
- Know the app type (native, cross-platform, hybrid, mobile web), the platforms, and the capabilities it uses (camera, push, payments, ...). Ask if unclear; the capability list drives which tests are generated.
- For the device matrix: a device/OS usage export from the team's analytics. **Do not invent market shares.** `assets/devices-example.json` is an illustrative format with made-up numbers, not data.
- **Test accounts and sandboxes only:** synthetic users (example.com), Sandbox Apple Accounts, Google Play license testers, and payment-provider test cards in test mode. Never real cards, real store accounts or production user data. Pass secrets through the environment (`maestro test -e ...`), never in files.
- Security checks (proxy interception, instrumentation, rooted or jailbroken devices) need the owner's written authorisation and run only against the app under test.
- Ask before installing tools (Maestro, Appium drivers, SDKs) or changing device settings on someone's own phone.

## Workflow

```
- [ ] 1. Scope: app type, platforms, capabilities, minimum OS, risks (→ questions)
- [ ] 2. Device and OS coverage matrix from analytics
- [ ] 3. Generate mobile test cases (compact) and adapt them to the app
- [ ] 4. Choose automation per layer; write flows with TC IDs
- [ ] 5. Execute on the matrix; triage per device and OS
- [ ] 6. Store readiness, results → qa/results.json → RTM
```

### 1. Scope
Establish, and record open points as questions:
- the app type and technology (Kotlin/Swift, React Native, Flutter, WebView shell, PWA);
- the platforms and the **minimum supported OS versions**, decided from analytics;
- the capabilities (`python scripts/mobile_checklist.py --list-capabilities`);
- the risky flows: payments, sign-in, data sync, anything that must not duplicate or get lost.

If requirements exist (`qa/requirements.json`), link the mobile tests to the requirement for the feature, or to a dedicated one such as "Mobile platform quality (iOS/Android)". If not, create it with the analyzing-requirements skill.

### 2. Device matrix
```bash
python scripts/mobile_checklist.py --platform both --devices qa/devices.json --target-share 80 \
    --lang tr --matrix-out qa/design/device-matrix.md
```
`devices.json` lists `{name, os, version, share, form_factor, width_dp}`, where `share` is the percentage of **that platform's** users. The script selects, per platform:
1. the mandatory edges: oldest OS (the minimum supported), newest OS, smallest screen, and the top tablet and foldable if listed;
2. then the highest-share devices until the cumulative share reaches the target.

The selection is deterministic greedy, explained in the output. It lists what stays outside the matrix (the breadth tier: emulators, simulators, device cloud) and warns when the listed data cannot reach the target. Plan three tiers: emulators/simulators in CI for breadth, **real devices for release**, and a device cloud plus staged rollout for the long tail.

### 3. Generate the mobile test cases
```bash
python scripts/mobile_checklist.py --platform both --capabilities push,payments,deeplinks,auth,offline \
    --req REQ-030 --tests qa/test-cases.json --lang tr --out qa/design/mobile.src.md
```
- **Always generated (core set):** fresh install; upgrade from the previous version with data migration; reinstall (Android backup, iOS Keychain leftovers); cold start budget; background and foreground; process death (Android `am kill`, iOS termination); low memory; rotation; multi-window and foldables; interruptions; offline; connection lost mid-transaction (idempotency); slow network; captive portal; TLS and proxy; largest font scale; screen reader; touch targets and contrast; low storage; dark mode; Turkish locale; jank; store privacy disclosures.
- **Per capability:** permissions (deny, one-time, revoke), camera, location, push, payments (StoreKit sandbox, Play Billing license testers, 3-D Secure, double charge), biometrics, offline-first sync, deep links (App Links and universal-link verification, malicious links), background work, files, Bluetooth, media, auth (storage, logs, sign-out, account deletion), WebView, and tracking (ATT, advertising ID).
- **Platform variants** are separate cases with the platform in the title, for example iOS "Allow Once" vs Android "Only this time" and background location.

Each case carries a category, priority, technique (checklist or error guessing), tags (`mobile`, `android`/`ios`, capability, `masvs-*`, `wcag-*`) and an automation hint. `# QUESTION` lines at the end list the decisions the tests depend on.

The output is a **draft**. Replace generic steps with the app's real screens, data and messages; delete cases that do not apply; merge them into existing feature tests where that reads better. Then append the file to `qa/test-cases.src.md` and run `qa_compact.py`:
```bash
python scripts/qa_compact.py tc qa/test-cases.src.md --out qa/test-cases.json
```
For feature logic (limits, states, calculations) design tests with the designing-test-cases skill; this skill adds the mobile dimension on top.

### 4. Automation
Choose per layer with the logic in `references/mobile-testing.md` §16, not by habit:
- **App technology:** Espresso (Android), XCUITest (iOS), Detox (React Native), Flutter `integration_test`/Patrol.
- **Who writes the tests:** developers use the tool in the app's language; a separate QA team writing one suite for both platforms uses Appium or Maestro.
- **CI:** iOS needs macOS runners; the device cloud must support the framework.
- **Playwright only emulates mobile browsers.** It does not test native or hybrid apps. Use it for mobile web, and real Safari on iOS devices for the final check.

For black-box flows start from `assets/maestro-flow-template.yaml`. **Every automated test starts its name with the TC ID** (`TC-101 ...`, or `test_TC101_...` where a hyphen is not allowed) and, in Maestro, repeats it as a tag. Keep unit and API tests as the base of the pyramid. Automate lifecycle, permissions and deep links end to end only for the critical journeys.

### 5. Execute and triage
- Run the core set on every device of the release matrix. Run the capability sets on at least the oldest-OS, the newest-OS and the smallest-screen devices.
- Record **device, OS version and build** for each result. A mobile defect without them cannot be reproduced.
- Attach evidence: a screen recording, logs (`adb logcat`, Console.app), and the network capture for network cases.
- **Group failures by root cause across devices.** For example, "crashes on Android 11 only" is one defect, with the affected devices listed.
- Separate app defects from **platform behaviour**, for example: no push after a force stop on Android, universal links not opening from the Safari address bar, the Simulator unable to receive calls. Document platform behaviour; do not file it as a defect.

### 6. Store readiness and closing the loop
- Before submission, walk through the store checklist in `references/mobile-testing.md` §15: account deletion, privacy labels and Data safety versus the real traffic, permission purpose strings, the privacy manifest, the target API level, the reviewer demo account, and the Google Play closed-testing rule for new personal accounts.
- Map automated results by TC ID, once per device report:
  ```bash
  python scripts/junit_results.py reports/pixel8.xml --device "Pixel 8 / Android 16" --source maestro --out qa/results.json
  ```
  A TC that failed on any device is failed; per-device statuses are kept under `projects`. Manual results and defect keys already in the file are kept.
- Then build the RTM with the tracing-requirements skill and write the defect and completion reports with the reporting-test-results skill.

## Files
- `scripts/mobile_checklist.py`: mobile test cases in compact format (core set + capabilities, platform variants, TR/EN) and the device coverage matrix from `devices.json` (deterministic greedy with mandatory edges).
- `scripts/junit_results.py`: JUnit XML (Maestro, Espresso, XCUITest, Appium, Detox) → `qa/results.json` by TC ID, aggregated per device.
- `scripts/qa_compact.py`: compact ⇄ JSON.
- `assets/mobile-checks.json`: the check catalogue behind the generator (editable: add checks for your domain).
- `assets/devices-example.json`: device list format with **illustrative, invented** share numbers.
- `assets/maestro-flow-template.yaml`: Maestro flow with the TC ID in the name and tags, process-death example and common mobile commands.
- `references/mobile-testing.md`: coverage strategy, lifecycle, network, permissions, push, deep links, biometrics, payments, localisation, accessibility, performance, OWASP MASVS v2, store readiness, tool comparison, result mapping, limits.
