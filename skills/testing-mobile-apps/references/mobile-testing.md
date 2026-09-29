# Mobile testing guide

## Contents
1. What is different about mobile
2. Device and OS coverage strategy
3. App lifecycle and state
4. Interruptions, multi-window, foldables
5. Network conditions and idempotency
6. Permissions (Android and iOS)
7. Push notifications
8. Deep links, universal links, App Links
9. Biometrics and secure storage
10. Payments: in-app purchase vs payment SDKs
11. Localisation (Turkish first)
12. Accessibility (WCAG 2.2 mapping)
13. Performance: startup, jank, memory, battery, size
14. Security: OWASP MASVS v2
15. Store readiness: App Store and Google Play
16. Automation tooling: an honest comparison
17. Mapping automated results to results.json
18. Limits: what needs a human and a real device

---

## 1. What is different about mobile
| App type | What you test | Typical traps |
|---|---|---|
| Native (Kotlin/Java, Swift/Objective-C) | The app binary on each OS | OS-version behaviour changes, permissions, lifecycle |
| Cross-platform (React Native, Flutter, Kotlin Multiplatform, .NET MAUI) | One codebase, two platforms | Platform-specific plugins behave differently; test both platforms, not "one is enough" |
| Hybrid (WebView shell, Capacitor/Cordova) | Native shell + web content | JavaScript bridges, WebView security, back navigation, offline |
| Mobile web / PWA | The site in mobile browsers | Real Safari on iOS differs from desktop WebKit; virtual keyboard, viewport, touch |

The mobile risks that web testing does not cover: the app can be **killed and restored at any time**, the **network changes under you**, the user **grants or revokes permissions**, the **OS updates every year**, and a **store review** stands between you and your users. Fixing a shipped defect takes days, and old versions stay installed.

## 2. Device and OS coverage strategy
**Use data, not guesses.** Take the device and OS mix from your own analytics: Firebase/Google Analytics, Play Console (Android vitals, device catalogue), App Store Connect (App Analytics), or the crash reporter. Public market statistics (for example StatCounter for Türkiye) are only a starting point for a new app. They describe the market, not your users.

**Decide the minimum supported OS explicitly.** Base it on user share, the cost of keeping old APIs, and the security support of old OS versions. Write the decision down (it becomes a requirement), then test the oldest supported version on purpose. Store constraints:
- Google Play requires new apps and updates to target a recent API level (about one year behind the newest Android release; for example API 35 from 31 August 2025). Check the current deadline. The *target* API affects behaviour; the *min* SDK decides who can install.
- Apple requires uploads to be built with a recent Xcode/SDK; the deadline is announced each year.

**Cover the physical variety that breaks layouts:**
- screen sizes and logical widths (small phones around 360 dp / 375 pt, large phones, tablets);
- densities (Android mdpi to xxxhdpi), notches, punch holes, the Dynamic Island, and safe areas;
- foldables (fold/unfold is a configuration change) and Android window size classes (compact < 600 dp, medium 600 to 840 dp, expanded ≥ 840 dp);
- iPad multitasking (Split View, Slide Over, Stage Manager, resizable windows);
- manufacturer skins on Android (Samsung One UI, Xiaomi HyperOS/MIUI, etc.), which change battery optimisation, notification and permission behaviour.

**Tiers:**
| Tier | Where | Purpose |
|---|---|---|
| Breadth | Emulators and simulators in CI | Fast feedback on every change; many OS versions and screen sizes |
| Release | Real devices (own lab or a device cloud) | The release matrix below; sensors, camera, biometrics, push, performance, battery |
| Long tail | Device cloud (BrowserStack, Sauce Labs, AWS Device Farm, Firebase Test Lab, LambdaTest) and staged rollout | Rare devices; watch crash and ANR rates during rollout |

Emulators and simulators do not reproduce real performance, thermal throttling, camera, Bluetooth, NFC, real push delivery, carrier networks or manufacturer skins. The iOS Simulator runs on the Mac's CPU and cannot receive phone calls.

**The release matrix script.** `mobile_checklist.py --devices devices.json --matrix-out ...` selects per platform:
1. mandatory edges: the oldest OS version (the minimum supported), the newest OS version, the smallest screen (logical width), and the top tablet and the top foldable when listed;
2. then the remaining devices in descending share order (ties by name), until the cumulative share reaches `--target-share` (default 80).

Shares are disjoint segments (one row = one device/OS combination), so once the edges are fixed this greedy order reaches the target with the fewest devices. Where one device satisfies two edges (for example the newest OS and the smallest screen), the script reuses it. The output is deterministic. If the listed shares cannot reach the target, the script says so: add rows or cover the tail on a device cloud. Re-run it every quarter.

## 3. App lifecycle and state
- **Install, upgrade, uninstall.** Upgrading from the previous production version is the highest-risk path: database migrations, changed preferences, a new token format. Test N-1 and the oldest version still used (N-2 or older). Test migration of queued offline data. On iOS, **Keychain items can survive app deletion**. On Android, **Auto Backup** can restore data after reinstall unless `allowBackup` or `dataExtractionRules` exclude it.
- **Cold, warm, hot start.** Cold: no process. Warm: the process exists but the activity/scene is recreated. Hot: the app is brought to the front.
- **Background and foreground.** Timers, sessions, in-flight requests and media must survive or stop as designed.
- **Process death.** Android kills background processes under memory pressure. When the user returns, the system recreates the screen and expects the app to restore saved state. To simulate it: `adb shell am kill <package>` while the app is in the background, or Developer options > Don't keep activities. iOS also terminates suspended apps; stopping the app from Xcode simulates this. A swipe-up in the app switcher is a deliberate user quit, which is a different case.
- **Low memory.** `adb shell am send-trim-memory <package> RUNNING_CRITICAL`, or Simulator > Debug > Simulate Memory Warning.
- **Low storage.** Saving, caching and database migration must fail cleanly.

## 4. Interruptions, multi-window, foldables
- Incoming and outgoing calls (Android emulator: `adb emu gsm call <number>`; iOS needs a real device), SMS, notifications, alarms, the low-battery dialog, the notification shade and Control Center, the assistant, and the screen locking by timeout.
- Rotation: layout and state are kept. WCAG 1.3.4 asks you not to lock orientation unless it is essential. Apps targeting Android 16 (API 36) cannot rely on orientation or resizability locks on large screens.
- Multi-window and split screen, window resizing, fold/unfold during input, external keyboard and mouse on tablets.
- Audio focus: another app playing audio, headphones unplugged (playback should pause), Bluetooth headset controls.

## 5. Network conditions and idempotency
Test these conditions: offline at launch, offline mid-screen, slow network (EDGE/3G profiles), high latency, packet loss, captive portals (a guest Wi-Fi returns an HTML login page with status 200 instead of your JSON), Wi-Fi to cellular hand-over, VPN, and airplane mode **in the middle of a transaction**.

**Tools:** Android emulator network controls (`adb emu network speed edge`, `adb emu network delay gprs`), `adb shell svc wifi disable` / `svc data disable`; Apple's Network Link Conditioner (on a device: Settings > Developer); throttling proxies (Charles, Proxyman, mitmproxy).

**The critical case is a lost response.** The request reached the server, but the answer never arrived. The app must not show "failed" and invite a second payment. Expected design:
- the client sends an **idempotency key** and reuses it on retry;
- the server returns the original result for a repeated key;
- the app shows a *pending* state and reconciles with the server on the next launch.

Check the server state (exactly one order or transfer), not only the UI. See the testing-apis skill for idempotency tests at API level.

## 6. Permissions (Android and iOS)
| Topic | Android | iOS |
|---|---|---|
| Model | Runtime permissions since Android 6 (API 23) | Prompt on first use; purpose string in Info.plist is mandatory |
| Deny | After the second denial the dialog no longer appears (Android 11+); send the user to app settings | After one denial iOS never asks again; send the user to Settings |
| One-time | "Only this time" for location, camera and microphone (Android 11+); revoked shortly after the app leaves the foreground | "Allow Once" for location; asked again in a later session |
| Location precision | Approximate vs precise (Android 12+) | Precise Location switch (iOS 14+) |
| Background location | Separate, later request; the user must choose "Allow all the time" in Settings (Android 11+); Play policy declaration required | "Always" requested in context, usually after "While Using" |
| Notifications | `POST_NOTIFICATIONS` runtime permission (Android 13+); notification channels (Android 8+) | Authorization prompt; provisional (quiet) authorization |
| Photos | Photo Picker without permission; partial access "Select photos and videos" (Android 14+) | PHPicker without permission; limited library access |
| Bluetooth | `BLUETOOTH_SCAN` / `BLUETOOTH_CONNECT` "Nearby devices" (Android 12+); location before 12 | Bluetooth prompt with purpose string |
| Tracking | Advertising ID can be deleted by the user (Android 12+); `AD_ID` permission | App Tracking Transparency prompt (iOS 14.5+) before any tracking |
| Revoke in Settings | The process is killed; the app must restart cleanly | The app may be terminated as well; handle it the same way |
| Auto-reset | Permissions of unused apps are reset (Android 11+) | - |

Test each permission in four states: granted, denied, one-time/limited, and revoked later in Settings. Ask only in context, and explain before the system prompt when the value is not obvious. Store reviewers check the purpose strings.

## 7. Push notifications
- **App states:** foreground (the app decides what to show), background, terminated by the user, and after a reboot. On Android a *force-stopped* app receives nothing until it is opened again; on iOS silent (background) pushes are not delivered to an app the user swiped away. Both are platform behaviour: document them, and do not file them as defects.
- **Tap routing:** opens the right screen with authorisation checks; works from a cold start.
- **Tokens:** a new token after reinstall, restore or a token refresh; the old token is unregistered; exactly one delivery per event.
- **Privacy:** after sign-out or an account switch, the previous user's notifications must not arrive. Lock-screen content follows the sensitivity policy.
- **Tools:** Firebase console test messages; `xcrun simctl push booted <bundle-id> payload.apns` on the Simulator. Development builds use the APNs sandbox environment and production builds the production environment; a token from one does not work in the other.

## 8. Deep links, universal links, App Links
- **Android App Links:** `autoVerify` intent filters plus `https://<host>/.well-known/assetlinks.json` containing the SHA-256 fingerprint of the **Play App Signing key** (the upload key alone is not enough for Play-distributed builds). Check with `adb shell pm get-app-links <package>`. Since Android 12, unverified web links open in the browser.
- **iOS universal links:** the Associated Domains entitlement plus `https://<host>/.well-known/apple-app-site-association`, served over HTTPS without redirects. A link typed into the Safari address bar opens the website; test from Notes or Messages.
- **States:** cold start, background, signed out (sign in first, then continue to the target), app not installed (website or store fallback), deferred deep links after install. Firebase Dynamic Links was shut down in August 2025; apps that relied on it need a replacement, and that replacement needs tests.
- **Security (MASVS-PLATFORM):** validate every parameter, never perform a state-changing action straight from a link, and do not load arbitrary URLs from link parameters into a WebView. Custom URL schemes can be claimed by other apps, so OAuth redirects should use claimed https links with PKCE.

## 9. Biometrics and secure storage
- A biometric prompt should **unlock a key**, not just return true. On Android use a Keystore key with `setUserAuthenticationRequired` and a `CryptoObject`; on iOS use a Keychain item with access control (for example `.biometryCurrentSet`). A callback-only check can be bypassed on a compromised device with instrumentation (MASVS-AUTH).
- **Enrolment change:** decide whether adding a fingerprint or face invalidates the key (`setInvalidatedByBiometricEnrollment`, `.biometryCurrentSet`). Then test it.
- **Fallbacks:** lockout after failures, cancel, no biometrics enrolled, biometrics removed. A PIN or password path must exist, and it must not be weaker than the main login.
- **Storage:** tokens belong in the Keychain or in Android Keystore-backed encrypted storage. They do not belong in SharedPreferences, UserDefaults, plain SQLite, logs, screenshots, the clipboard or backups (MASVS-STORAGE).
- **Simulation:** iOS Simulator > Features > Face ID/Touch ID; Android emulator `adb -e emu finger touch <id>`. Real-device testing is still required before release.

## 10. Payments: in-app purchase vs payment SDKs
| | Store in-app purchase (digital goods, content, subscriptions) | Payment SDK (physical goods and services) |
|---|---|---|
| iOS | StoreKit. Local: StoreKit Testing in Xcode with a `.storekit` file (no network, you control renewals, failures, refunds). Device and TestFlight: Sandbox Apple Account. | Provider SDK or web checkout in its test mode |
| Android | Play Billing. License testers use test instruments ("always approves", "always declines", slow cards for pending purchases). Purchases must be acknowledged within 3 days or they are refunded automatically. | Same |
| Test | purchase, cancel, failure, pending/deferred (Ask to Buy), restore on a new install, renewal, grace period, expiry, refund, upgrade/downgrade, server-side receipt validation | 3-D Secure challenge (in-app, browser or bank app and back), declines, timeouts, app killed during payment, the return deep link |

- Subscription time runs faster in sandboxes (for example, one month renews within minutes), so plan the renewal tests around that.
- **Never use real cards or real store accounts.** Use only the provider's published test cards in its sandbox.
- Whether digital goods must use store IAP depends on the storefront and current rules (for example EU DMA alternatives and US link-out changes). Ask the product owner which rules apply, and do not assume.
- For every payment path, test the double tap, the lost response and the app kill (section 5). The invariant is one charge and one order.

## 11. Localisation (Turkish first)
- **Text expansion:** Turkish words are often longer than English ones (agglutination), so labels, buttons and tabs must wrap or scale instead of being truncated. Pseudo-locales help: Android `en-XA` (accented, longer) and `ar-XB` (RTL) in Developer options; the Xcode scheme option "Double-Length Pseudolanguage".
- **Dotted and dotless i:** `i→İ` and `ı→I` in Turkish casing. Locale-sensitive `toUpperCase()`/`uppercased()` breaks technical strings: keys, enum names, e-mail addresses, header names. Use locale-invariant casing for those. Also test search and sorting with `ğüşıöçİ`.
- **Formats:** numbers `1.234,56`; dates `31.12.2026`; 24-hour time; currency as specified (for example `₺1.234,56`); phone numbers `+90 5xx xxx xx xx`.
- **Per-app language** (Android 13+, iOS): a language switch inside the app without a restart, if supported.
- **RTL** (Arabic, Hebrew) is not needed for a Turkish-only app. Test it with the RTL pseudo-locale once other markets are planned: mirrored layouts, directional icons, bidirectional text.

## 12. Accessibility (WCAG 2.2 mapping)
WCAG was written for the web, but it applies to native apps through the W3C guidance on applying WCAG to mobile and non-web ICT, and through EN 301 549 (the standard behind the European Accessibility Act, in force since 28 June 2025).

| Check | Android | iOS | WCAG 2.2 |
|---|---|---|---|
| Screen reader: names, roles, states, order | TalkBack | VoiceOver | 1.1.1, 1.3.1, 2.4.3, 4.1.2; status messages 4.1.3 |
| Large text | Font size up to 200% (Android 14+, non-linear) plus display size | Dynamic Type including the accessibility sizes | 1.4.4 Resize Text; 1.4.10 Reflow |
| Touch targets | 48×48 dp guideline | 44×44 pt guideline | 2.5.8 Target Size (Minimum) is 24×24 CSS px (AA); 2.5.5 is 44×44 (AAA) |
| Contrast | Accessibility Scanner | Accessibility Inspector | 1.4.3 (4.5:1 text), 1.4.11 (3:1 non-text) |
| Orientation | Not locked unless essential | Same | 1.3.4 Orientation |
| Gestures and motion | Alternatives to multi-finger or path gestures and to shaking | Same | 2.5.1 Pointer Gestures, 2.5.4 Motion Actuation, 2.5.7 Dragging Movements |
| Sign-in | Allow paste, password managers, OTP autofill | Same | 3.3.8 Accessible Authentication (Minimum) |
| Focus visibility (keyboard, switch access) | External keyboard, Switch Access | Full Keyboard Access, Switch Control | 2.4.7, 2.4.11 Focus Not Obscured (Minimum) |

**Automation catches only part of this.** Use Espresso `AccessibilityChecks`, XCUITest `performAccessibilityAudit()` (Xcode 15+) and the scanners for labels, targets and contrast. Screen reader flows and meaningful labels still need a human pass on a real device. For web-style WCAG test cases use the testing-nonfunctional skill.

## 13. Performance: startup, jank, memory, battery, size
| Metric | Android | iOS | Reference points |
|---|---|---|---|
| Startup | `adb shell am start -W` (TotalTime), Macrobenchmark `StartupTimingMetric`, Perfetto | `XCTApplicationLaunchMetric`, Instruments App Launch, MetricKit | Android vitals flags cold starts ≥ 5 s, warm ≥ 2 s, hot ≥ 1.5 s as excessive; set a tighter product budget on the low-tier device |
| Jank | `dumpsys gfxinfo <package> framestats`, `FrameTimingMetric`, JankStats | Instruments Animation Hitches, hitch rate in the Xcode Organizer | Frames over 16 ms at 60 Hz are slow; over 700 ms are frozen |
| Stability | Android vitals: user-perceived crash and ANR rates | Xcode Organizer crashes and hangs, MetricKit | Play's bad-behaviour thresholds: about 1.09% crash rate and 0.47% ANR rate overall (8% per device model); check the current values |
| Memory | Android Studio Memory Profiler, LeakCanary | Instruments Allocations and Leaks, memory graph | No steady growth when a flow is repeated |
| Battery | `dumpsys batterystats`, Battery Historian, Doze testing | Xcode Organizer energy, Instruments Energy Log | Wake locks, location and network use in the background |
| Size | Android App Bundle size in Play Console; APK Analyzer | App Store Connect size report per device | Watch the download size trend per release |

Measure on **release builds on the lowest-tier device of the matrix**. Debug builds and emulators are slower, or faster, in misleading ways. Repeat each measurement at least 10 times and report the median and p90.

## 14. Security: OWASP MASVS v2
OWASP MASVS v2 (the Mobile Application Security Verification Standard) has **eight control groups**. The OWASP MASTG (Mobile Application Security Testing Guide) holds the tests, and MASWE lists the weaknesses. MASVS v2 dropped the old L1/L2/R levels from the standard; MASTG uses the testing profiles MAS-L1, MAS-L2 and MAS-R instead.

| Group | Controls (short) | Tests in this skill |
|---|---|---|
| MASVS-STORAGE | 1: store sensitive data securely; 2: prevent leakage (logs, backups, screenshots, keyboard caches) | auth-storage, auth-logs, reinstall, offline cache, file sharing |
| MASVS-CRYPTO | 1: strong, current cryptography; 2: key management per best practice | covered indirectly by the Keystore/Keychain checks; review the code |
| MASVS-AUTH | 1: secure authentication and authorisation protocols; 2: local authentication per platform best practice; 3: extra authentication for sensitive operations | sign-out and token revocation, biometric key binding, enrolment change |
| MASVS-NETWORK | 1: secure all network traffic; 2: pin identities of endpoints under the developer's control where needed | TLS and proxy checks |
| MASVS-PLATFORM | 1: IPC securely; 2: WebViews securely; 3: UI securely (screenshots, overlays, snapshots) | deep links, WebView, app switcher snapshot |
| MASVS-CODE | 1: up-to-date platform version; 2: mechanism to enforce updates; 3: no components with known vulnerabilities; 4: validate and sanitise untrusted input | receipt validation, deep-link input; run SCA on dependencies |
| MASVS-RESILIENCE | 1: validate platform integrity (root/jailbreak); 2: anti-tampering; 3: anti-static analysis; 4: anti-dynamic analysis | only when the risk model needs it (banking, DRM, games) |
| MASVS-PRIVACY | 1: minimise access to sensitive data; 2: prevent identification of the user; 3: transparency; 4: user control over their data | EXIF, tracking consent, privacy labels, push content, account deletion |

**Scope.** Security testing needs **written authorisation**. Instrumentation tools (Frida, objection) and rooted or jailbroken test devices are for the app under test only. Pair MASVS with the API-side checks (OWASP API Top 10, via the testing-apis skill), because most mobile data leaks happen at the backend.

## 15. Store readiness: App Store and Google Play
**Both stores:**
- **Account deletion:** if users can create an account, they must be able to start its deletion inside the app (Apple Guideline 5.1.1(v)). Google Play also requires a web link for deletion requests.
- **Privacy disclosures** (App Store privacy details, Google Play Data safety form) match what the app and its SDKs really collect. Compare with proxy captures.
- **Permissions and purpose strings** are justified. Google Play requires declarations for sensitive permissions (background location, all-files access, SMS/Call Log, exact alarms, photo and video access).
- A **demo/test account and review notes** for reviewers when features are behind sign-in.
- No crashes, placeholder content or broken links (Apple Guideline 2.1 App Completeness).

**Apple:** privacy manifest (`PrivacyInfo.xcprivacy`) for required-reason APIs and listed third-party SDKs; App Tracking Transparency before tracking; Sign-in rule of Guideline 4.8 when third-party login is offered; IAP rules of Guideline 3.1; TestFlight beta review for external testers.

**Google Play:** target API level deadline; testing tracks (internal, closed, open); **new personal developer accounts must run a closed test with at least 12 testers for 14 days** before production access (check the current rule); the pre-launch report (automatic crawls on real devices) is free extra coverage; staged rollouts with Android vitals monitoring.

Store rules change several times a year. Treat these points as a checklist to verify against the current App Store Review Guidelines and Google Play policy pages, not as final truth.

## 16. Automation tooling: an honest comparison
| Tool | Platforms | Language | Style | Strengths | Weak spots |
|---|---|---|---|---|---|
| Espresso (+ Compose testing) | Android | Kotlin/Java | In-process, gray-box | Fast, synchronised with the UI thread, stable; runs in Gradle/CI | Android only; limited outside the app (system dialogs need UI Automator) |
| XCUITest | iOS | Swift | Out-of-process, black-box | Official, Xcode-integrated, accessibility audit | iOS only; slower; needs macOS runners |
| Appium 2.x/3.x | Android, iOS (and more) | Any WebDriver client (Java, JS/TS, Python, C#) | Black-box over WebDriver; drivers (UiAutomator2, XCUITest, Espresso) installed separately | One API for both platforms; reuses the team's Selenium skills; device clouds support it | Slower; flakier without good waits; more infrastructure |
| Maestro | Android, iOS (Simulator; check current real-device support), also RN/Flutter/web | YAML flows | Black-box with built-in waiting and retries | Very fast to write; readable by non-developers; low flakiness | Limited logic; less control; iOS real devices and some system interactions are limited |
| Detox | React Native (Android, iOS) | JavaScript/TypeScript | Gray-box, synchronises with the RN bridge and animations | Stable for RN; runs in Jest | React Native only; simulators and emulators mainly |
| Flutter `integration_test` (+ Patrol) | Flutter (Android, iOS) | Dart | In-process widget tests on a device | Same language as the app; fast; Patrol adds native dialogs and notifications | Flutter only |
| Playwright | **Mobile web only**: emulates viewport, user agent and touch in desktop engines | TS/JS, Python, Java, .NET | Browser automation | Excellent for responsive and mobile web | **Does not test native or hybrid apps.** Its WebKit is not real iOS Safari; use real devices or a device cloud for Safari on iOS |

**How to choose (there is no single answer):**
1. **App technology.** Native Android → Espresso for component and flow tests. Native iOS → XCUITest. React Native → Detox (or Maestro). Flutter → `integration_test`/Patrol (or Maestro). Hybrid → the native tool plus WebView contexts in Appium.
2. **Who writes the tests.** If app developers write them, use the in-process tool in the app's language (Espresso, XCUITest, Detox, Flutter). If a separate QA team writes them in one language for both platforms, use Appium or Maestro.
3. **One suite for two platforms?** Appium or Maestro. Accept some slowness (Appium) or less expressiveness (Maestro).
4. **CI and devices.** iOS needs macOS runners. Check that the chosen device cloud supports the framework and the OS versions of your matrix.
5. **Keep the pyramid.** Most logic belongs in unit and API tests. Put only critical user journeys and platform behaviour (lifecycle, permissions, deep links) into end-to-end UI tests.

Stable selectors come first in every tool: Android resource ids or Compose `testTag`, iOS `accessibilityIdentifier`, React Native `testID`, Flutter keys. Text selectors break on translations.

## 17. Mapping automated results to results.json
Every automated test carries its TC ID, so its result lands in `qa/results.json` and in the RTM:
- **Maestro:** start the flow `name` with the TC ID and add it as a tag (`assets/maestro-flow-template.yaml`). Run with `--format junit --output report.xml`, then run `scripts/junit_results.py report.xml --device "<model> / <OS>" --source maestro --out qa/results.json`.
- **Espresso, XCUITest, Detox, Flutter, Appium:** put the TC ID at the start of the test name (for example `test_TC101_checkoutDraftSurvivesProcessDeath`, or `"TC-101 ..."` where names are free text). Export JUnit XML: Gradle writes it under `build/outputs/androidTest-results/`; for XCUITest convert the `.xcresult` with a JUnit converter (for example xcbeautify or trainer); Detox and Appium runners use a JUnit reporter. Then use the same script: it reads `TC-101` and also `TC101` or `TC_101` (for method names that cannot contain a hyphen) and normalises them to `TC-101`.
- **Several devices:** run the script once per device report with a different `--device`. The entry records each device under `projects`. The TC is failed if any device failed.
- **Manual runs:** record `passed`/`failed`/`blocked` per TC directly in `qa/results.json` (or with the reporting-test-results skill). The script keeps manual entries and defect keys.

## 18. Limits: what needs a human and a real device
- The generated test cases are **drafts**. They name the checks that matter on mobile, but the concrete screens, ids, data and expected texts come from your app and requirements.
- Screen reader usability, gesture comfort, readability at large fonts, camera and sensor behaviour, real push delivery, carrier networks, battery drain and thermal behaviour need **real devices and people**.
- Store policies, OS behaviour and tool capabilities change every year. The references here were current in 2025-2026: verify the details (API levels, deadlines, thresholds, Maestro commands) before you rely on them.
- Share numbers in `assets/devices-example.json` are invented. A matrix is only as good as the analytics behind it.
