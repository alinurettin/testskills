# Running features with playwright-bdd

playwright-bdd (v9.x, works with Playwright 1.5x–1.6x) converts `.feature` files into native Playwright tests. Fixtures, page objects, projects, reporters, traces and `--grep` all keep working, so plain specs and BDD scenarios can live in one automation project.

## Setup
```bash
npm i -D playwright-bdd          # ask the user before installing packages
```

`playwright.config.ts` (a separate config such as `playwright.bdd.config.ts` is fine too):
```ts
import { defineConfig, devices } from '@playwright/test';
import { defineBddConfig } from 'playwright-bdd';

const testDir = defineBddConfig({
  features: 'features/**/*.feature',
  steps: 'steps/**/*.ts',
});

export default defineConfig({
  testDir,
  reporter: [['list'], ['html', { open: 'never' }], ['json', { outputFile: 'test-results/results.json' }]],
  use: { baseURL: process.env.BASE_URL, locale: 'tr-TR', timezoneId: 'Europe/Istanbul' },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
});
```

`steps/fixtures.ts` reuses the same page objects as the plain suite:
```ts
import { test as base, createBdd } from 'playwright-bdd';
import { CartPage } from '../pages/CartPage';

export const test = base.extend<{ cartPage: CartPage }>({
  cartPage: async ({ page }, use) => { const cart = new CartPage(page); await cart.open(); await use(cart); },
});
export const { Given, When, Then } = createBdd(test);
```

`steps/coupon.steps.ts`. Step text is matched literally, whatever the Gherkin language, and uses Cucumber expressions:
```ts
import { Given, When, Then } from './fixtures';

Given('sepet tutarı {string} TL', async ({ cartPage }, amount: string) => { await cartPage.setBasketTotal(amount); });
When('{string} kuponunu uygularsam', async ({ cartPage }, code: string) => { await cartPage.applyCoupon(code); });
Then('{string} mesajını görürüm', async ({ cartPage }, text: string) => { await cartPage.expectAlert(text); });
Then('indirim {string}, ödenecek tutar {string} olur', async ({ cartPage }, d: string, p: string) => {
  await cartPage.expectSummary(d, p);
});
```

## Run
```bash
npx bddgen && npx playwright test                 # generate .features-gen, then run
npx bddgen && npx playwright test --grep @TC-003  # one test case
```
- Add `.features-gen/` to `.gitignore`. It is regenerated on every run.
- A missing step definition makes `bddgen` fail and print snippets for the missing steps. Paste them into a steps file and implement them.

## Results and traceability
- Gherkin tags (`@REQ-002`, `@TC-003`) become Playwright tags, so the JSON report and `pw_results.py` work unchanged. This was verified with a Turkish feature: the failing Then step is shown with its Turkish text.
- For Xray Cucumber tests, Xray can also import `.feature` files directly (Test Type = Cucumber). Keep the `@TC-###` tags. Once an Xray test key exists, add it as a tag as well, e.g. `@SHOP-201`.
