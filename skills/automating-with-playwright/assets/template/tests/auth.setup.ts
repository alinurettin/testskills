import { test as setup, expect } from '@playwright/test';

/**
 * Logs in once and saves the session to .auth/user.json (used via storageState in playwright.config.ts).
 * Credentials come from TEST_USER / TEST_PASSWORD environment variables of a TEST account.
 * Adjust the locators to the application's login form.
 */
setup('authenticate', async ({ page }) => {
  setup.skip(!process.env.TEST_USER || !process.env.TEST_PASSWORD, 'No test credentials configured');
  await page.goto('/login');
  await page.getByLabel(/e-?posta|email/i).fill(process.env.TEST_USER!);
  await page.getByLabel(/şifre|parola|password/i).fill(process.env.TEST_PASSWORD!);
  await page.getByRole('button', { name: /giriş|login|sign in/i }).click();
  await expect(page).not.toHaveURL(/login/);
  await page.context().storageState({ path: '.auth/user.json' });
});
