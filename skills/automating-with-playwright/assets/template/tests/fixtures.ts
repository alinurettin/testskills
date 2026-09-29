import { test as base, expect } from '@playwright/test';
// Register page objects here so specs receive them as fixtures:
//   import { CartPage } from '../pages/CartPage';
//   type Pages = { cartPage: CartPage };
//   export const test = base.extend<Pages>({ cartPage: async ({ page }, use) => use(new CartPage(page)) });

type Pages = Record<string, never>;

export const test = base.extend<Pages>({});
export { expect };
