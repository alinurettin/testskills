import { type Locator, type Page, expect } from '@playwright/test';

/**
 * Base for page objects. Page objects expose intent-level actions ("applyCoupon")
 * and locators; assertions about business outcomes stay in the specs.
 */
export abstract class BasePage {
  constructor(readonly page: Page) {}

  /** Path relative to baseURL, e.g. '/cart'. */
  abstract readonly path: string;

  async open(): Promise<void> {
    await this.page.goto(this.path);
  }

  /** Shared alert/toast region; override when the app uses a different pattern. */
  get alert(): Locator {
    return this.page.getByRole('alert');
  }

  async expectAlert(text: string | RegExp): Promise<void> {
    await expect(this.alert).toContainText(text);
  }
}
