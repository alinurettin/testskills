# Accessibility testing (WCAG 2.2 AA)

## Contents
1. Baseline and legal context
2. Method: automated + manual
3. Manual test toolkit
4. Automation in Playwright
5. Reporting findings

---

## 1. Baseline and legal context
- **WCAG 2.2 level AA** is the professional default. It is also ISO/IEC 40500:2025.
- WCAG 3.0 is still a draft. Do not test against it.
- Level AA means conformance with all 55 level A and level AA success criteria (31 A + 24 AA). The data is in `assets/wcag22-aa.json`.
- Legal drivers the user may cite:
  - the European Accessibility Act (EU, from June 2025, including e-commerce and banking),
  - public-sector rules,
  - contractual requirements.

  State the driver in the test plan. Do not give legal advice beyond naming it.

## 2. Method: automated + manual
- **Automated scans** such as axe-core find roughly a third to a half of the issues: contrast, missing labels and names, lang, titles, some ARIA misuse. They are fast, repeatable and belong in CI.
- **Manual evaluation is mandatory** for the rest: keyboard operation, focus order and visibility, meaningful sequence, error handling, time limits, dragging alternatives, accessible authentication, screen-reader output.
- `scripts/nfr_checklist.py wcag` selects the relevant criteria by feature. It emits one axe test covering the machine-checkable criteria, plus one manual test per criterion that needs judgement.
- Test the **key user journeys**, not just single pages: login, search, product, cart, checkout, form errors, confirmation. Test each state as well: errors shown, dialogs open, menus expanded.

## 3. Manual test toolkit
- **Keyboard:**
  - Tab and Shift+Tab to move through the page;
  - Enter and Space to activate controls;
  - arrow keys inside widgets;
  - Esc to close.

  Also check that focus is visible and that it is never trapped or hidden behind sticky elements.
- **Screen readers:** NVDA or JAWS with Chrome or Firefox on Windows; VoiceOver with Safari on macOS and iOS; TalkBack with Chrome on Android. Check the Turkish pronunciation (`lang="tr"`).
- **Zoom and reflow:** 200% zoom, and a 320 px wide viewport (400%). Test text spacing with a bookmarklet.
- **Colour:** a contrast checker, a grayscale view (the information must still be there), and a forced-colours or high-contrast mode.
- **Motion and timing:** a reduced-motion preference; session timeout warnings with the option to extend.

## 4. Automation in Playwright
```ts
import AxeBuilder from '@axe-core/playwright';   // npm i -D @axe-core/playwright (ask before installing)

test('TC-101 Otomatik erişilebilirlik taraması – Sepet', { tag: ['@TC-101', '@accessibility'] }, async ({ page }) => {
  await page.goto('/sepet');
  const results = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa', 'wcag22aa']).analyze();
  expect(results.violations.map(v => `${v.id}: ${v.nodes.length}`)).toEqual([]);
});
```
- Run the scan in each relevant **state**: after opening a dialog, after triggering validation errors.
- `toMatchAriaSnapshot()` pins the accessible structure of key components against regressions.

## 5. Reporting findings
For each finding, record the WCAG criterion (for example, 2.4.11), the page and state, the element, how to reproduce it (keys, screen reader and browser), the impact on users, and a suggested fix. Severity:
- a user cannot complete a key task (keyboard trap, unlabeled payment field): **high/critical**
- the task is possible but hard: **medium**
- cosmetic: **low**
