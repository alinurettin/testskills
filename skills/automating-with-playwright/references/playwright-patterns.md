# Playwright patterns (TypeScript, Playwright 1.5x–1.6x)

## Contents
1. Locators (priority order)
2. Assertions and waiting
3. Page objects and fixtures
4. Test data and state
5. Authentication
6. Network, time and third parties
7. API tests
8. Accessibility and visual checks
9. Locale (Turkish)
10. Flakiness policy
11. Known product bugs

---

## 1. Locators (priority order)
Prefer locators that users and assistive technology see. They survive refactors, and when one fails it usually means a real accessibility problem.

1. `page.getByRole('button', { name: 'Uygula' })`: role plus accessible name. This is the first choice.
2. `page.getByLabel('Kupon kodu')`: form fields.
3. `page.getByPlaceholder(...)`, `page.getByText(...)`: static text, used sparingly.
4. `page.getByTestId('discount')`: the attribute is set to `data-testid` in the config. Use it for values that have no accessible role, such as amounts or summary cells. If the application lacks test IDs, ask the developers to add them; that is a testability requirement.
5. CSS or XPath: last resort only. Never use generated class names or `nth-child` chains.

Scope locators inside components: `page.getByRole('row', { name: 'Test Ürünü A' }).getByRole('button', { name: 'Sil' })`. Use `locator.filter({ hasText })` instead of indexes.

Discover locators with `npx playwright codegen <url>`, the Playwright MCP server, `playwright-cli`, or the Playwright Test Agents (see `ci-and-reporting.md`). Always review generated locators against the priority list above.

## 2. Assertions and waiting
- Use **web-first assertions**, which retry automatically. Examples: `await expect(locator).toHaveText(...)`, `toBeVisible()`, `toHaveURL()`, `toHaveValue()`, `toHaveCount()`.
- **Never use `page.waitForTimeout`.** Wait for a state instead: an assertion, `page.waitForResponse(...)`, or `expect.poll(...)`.
- Assert the **exact observable outcome** of the manual test's expected result: the verbatim message, the amount with its formatting, the state change. A test that only clicks through without asserting is worse than no test, because it creates false confidence.
- Use `expect.soft(...)` only for independent cosmetic checks inside one step. Business outcomes must use hard assertions.
- Use `test.step('1. …', async () => { … })` for every manual step. Steps appear in reports and traces, and they map one-to-one to the manual test.

## 3. Page objects and fixtures
- One class per page or component in `pages/`, extending `BasePage`. A page object exposes **locators and intent-level actions** (`applyCoupon(code)`). **Business assertions stay in the specs**. Small shared checks such as `expectSummary(discount, payable)` are fine when many tests need them.
- Register page objects as fixtures in `tests/fixtures.ts`. Specs import `test` and `expect` from `./fixtures`, not from `@playwright/test`.
- Keep page objects free of test data and of `if` logic that hides failures.

## 4. Test data and state
- **Independence.** Every test creates the data it needs, or uses data isolated per worker. Tests must pass alone, in any order, and in parallel (`fullyParallel: true`).
- Seed data through **APIs or fixtures**, not through the UI, unless the UI flow is itself under test. Clean up in fixture teardown or through a test-account reset endpoint.
- Make generated data unique, e.g. `qa+${Date.now()}@example.com`. Never use real customer data.
- Keep the data-driven cases from `generate_specs.py` (`const casesN = [...]`) as the single source of values. Add structured fields to each case (`basket: '800,00'`) instead of parsing prose.

## 5. Authentication
- Use `tests/auth.setup.ts`: it logs in once, saves `storageState` to `.auth/user.json`, and the browser projects depend on the `setup` project.
- Credentials come from the `TEST_USER` and `TEST_PASSWORD` environment variables (a dedicated **test** account; CI secrets). Never hard-code credentials, and never commit `.env` or `.auth/`.
- For role-based tests, create one storage state per role (`admin.json`, `customer.json`) and switch per test with `test.use({ storageState: '.auth/admin.json' })`.

## 6. Network, time and third parties
- **Third parties** (payment gateway, SMS, BIN service): use their sandbox, or mock with `page.route('**/api/bin/**', route => route.fulfill({ json: {...} }))`. Mock the error paths as well: 500, timeout (`route.abort('timedout')`), malformed JSON. These are the negative tests from the error-guessing checklist.
- **Time.** Coupon expiry, session timeout and "valid until 23:59:59" depend on the clock. Control it with `page.clock.install({ time: new Date('2026-09-30T23:59:59+03:00') })` and `page.clock.fastForward('00:01')`. Never wait in real time.
- **Wait for backend effects** with `page.waitForResponse(r => r.url().includes('/api/cart') && r.ok())`.

## 7. API tests
- Tests with `category: api` get the `{ request }` fixture: `const res = await request.post('/api/coupons/apply', { data: {...} }); expect(res.status()).toBe(422);`
- **Server-side negative tests** from the manual suite belong at the API level. Examples: installments sent for a debit card, a manipulated discount, another user's cart ID (object-level authorisation). They are faster and more precise than UI tests.
- Check the response status, the error body structure and the **absence of side effects**: no order created, no coupon consumed.

## 8. Accessibility and visual checks
- **Accessibility.** `@axe-core/playwright` is optional and has to be installed. Run `new AxeBuilder({ page }).withTags(['wcag2a','wcag2aa','wcag21aa','wcag22aa']).analyze()`, then `expect(results.violations).toEqual([])`. Also consider `toMatchAriaSnapshot()` for key components.
- **Visual.** `await expect(page).toHaveScreenshot()` only on stable screens. Mask dynamic regions. Keep the baselines per browser and operating system in the repository.

## 9. Locale (Turkish)
- Set `locale: 'tr-TR'` and `timezoneId: 'Europe/Istanbul'` in the config. Amounts render as `1.234,56 TL`; assert the rendered text exactly as the manual test states it.
- Case-insensitive matching must respect Turkish: `/kupon uygulandı/i` is fine, but "İ/ı" lowercasing differs between the JavaScript `toLowerCase()` and `toLocaleLowerCase('tr-TR')`.
- If the product supports several languages, add a project per locale, or parameterise with `test.use({ locale: 'en-US' })`.

## 10. Flakiness policy
- `retries: 2` in CI only, with `trace: 'on-first-retry'`. A test that passes only on retry is **flaky**: `pw_results.py` flags it, and it must be fixed, not ignored.
- Common causes are:
  - missing web-first assertions,
  - shared data between tests,
  - animations (use `expect(...).toBeVisible()` before interacting),
  - real time,
  - real third parties.
- Do not raise timeouts to hide a race. Find the event to wait for instead.

## 11. Known product bugs
When an implemented test fails because the **product** is wrong (the test matches the requirement):
- **Do not change the expected result to match the bug.** That silently converts a requirement into a defect.
- Report the defect. Record its key in `qa/results.json` (`"defects": ["SHOP-481"]`).
- To keep CI green while the bug is open, mark it explicitly: `test.fail(true, 'SHOP-481: 100,00 TL boundary rejected')`. `test.fail` inverts the verdict, so the test turns red again once the bug is fixed. That tells you to remove the mark. Never use `test.skip` for this.
- **Never reach a precondition through a known defect.** For example, when a limit bug makes it possible to drain the balance for an "insufficient balance" test, the test passes only because of that bug. Mark such tests in their objective and in the defect report ("retest with a seeded account after DEF-001"), and request proper test data (a seed or API) as a testability dependency.
- Playwright reports a `test.fail` test as "expected". `pw_results.py` still records it as **failed** for the requirement, with the note "known product defect", so the RTM never shows an open defect as green. When the defect is fixed, the test passes unexpectedly. `pw_results.py` then reports it as passed with a note to remove `test.fail`.
