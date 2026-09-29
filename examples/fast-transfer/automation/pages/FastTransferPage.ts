import { type Locator, type Page, expect } from '@playwright/test';
import { BasePage } from './BasePage';

/** Test data (synthetic). IBAN validated with check_ids.py (VALID, mod-97). */
export const VALID_IBAN = 'TR330006100519786457841326';
export const TEST_OTP = '123456'; // test-environment SMS code shown on the page
export const MSG = {
  success: 'Transfer başarıyla gerçekleşti.',
  min: 'Tutar en az 1,00 TL olmalıdır.',
  max: 'İşlem başına en fazla 50.000,00 TL gönderebilirsiniz.',
  descRequired: 'Açıklama zorunludur.',
  invalidIban: 'Geçersiz IBAN. Lütfen TR ile başlayan 26 karakterlik IBAN girin.',
  otpRequired: 'Bu işlem için SMS doğrulaması gerekiyor.',
  duplicate: 'Aynı alıcıya aynı tutarda 60 saniye içinde transfer yaptınız. Yine de göndermek istiyor musunuz?',
};

export interface TransferInput {
  iban?: string;
  name?: string;
  amount: string;
  desc?: string;
}

/** 'FAST ile Para Gönder' page. Locators follow role/label first; data-testid only for amounts. */
export class FastTransferPage extends BasePage {
  readonly path = '/';

  constructor(page: Page) {
    super(page);
  }

  get iban(): Locator { return this.page.getByLabel('Alıcı IBAN'); }
  get name(): Locator { return this.page.getByLabel('Alıcı adı'); }
  get amount(): Locator { return this.page.getByLabel('Tutar (TL)'); }
  get desc(): Locator { return this.page.getByLabel('Açıklama'); }
  get continueBtn(): Locator { return this.page.getByRole('button', { name: 'Devam' }); }
  get balance(): Locator { return this.page.getByTestId('balance'); }
  get dailyRemaining(): Locator { return this.page.getByTestId('daily-remaining'); }

  get duplicateWarning(): Locator { return this.page.getByRole('region', { name: 'Tekrar uyarısı' }); }
  get sendAnywayBtn(): Locator { return this.page.getByRole('button', { name: 'Yine de gönder' }); }
  get cancelBtn(): Locator { return this.page.getByRole('button', { name: 'Vazgeç' }); }

  get otpStep(): Locator { return this.page.getByRole('region', { name: 'SMS doğrulama' }); }
  get otpInput(): Locator { return this.page.getByLabel('SMS kodu'); }
  get otpConfirmBtn(): Locator { return this.page.getByRole('button', { name: 'Onayla' }); }

  get receipt(): Locator { return this.page.getByRole('region', { name: 'Dekont' }); }
  get receiptAmount(): Locator { return this.page.getByTestId('receipt-amount'); }
  get receiptFee(): Locator { return this.page.getByTestId('receipt-fee'); }
  get receiptTotal(): Locator { return this.page.getByTestId('receipt-total'); }
  get receiptIban(): Locator { return this.page.getByTestId('receipt-iban'); }
  get receiptDesc(): Locator { return this.page.getByTestId('receipt-desc'); }
  get newTransferBtn(): Locator { return this.page.getByRole('button', { name: 'Yeni transfer' }); }

  /** Fills the form; unspecified fields get the default valid test data. */
  async fill(input: TransferInput): Promise<void> {
    await this.iban.fill(input.iban ?? VALID_IBAN);
    await this.name.fill(input.name ?? 'Ayşe Test');
    await this.amount.fill(input.amount);
    await this.desc.fill(input.desc ?? 'Kira');
  }

  async submit(input: TransferInput): Promise<void> {
    await this.fill(input);
    await this.continueBtn.click();
  }

  async confirmOtp(code: string = TEST_OTP): Promise<void> {
    await this.otpInput.fill(code);
    await this.otpConfirmBtn.click();
  }

  /** Starts a new transfer from the receipt screen when it is shown. */
  async startNew(): Promise<void> {
    if (await this.newTransferBtn.isVisible()) await this.newTransferBtn.click();
  }

  /**
   * Precondition helper: performs a transfer that must succeed (handles OTP and, if asked, the
   * duplicate warning). Asserts success so a broken precondition never passes silently.
   */
  async transferOk(input: TransferInput, opts: { sendAnyway?: boolean } = {}): Promise<void> {
    await this.startNew();
    await this.submit(input);
    const outcome = this.receipt.or(this.otpStep).or(this.duplicateWarning);
    await expect(outcome.first()).toBeVisible();
    if (opts.sendAnyway && (await this.duplicateWarning.isVisible())) {
      await this.sendAnywayBtn.click();
    }
    await expect(this.receipt.or(this.otpStep).first()).toBeVisible();
    if (await this.otpStep.isVisible()) await this.confirmOtp();
    await expect(this.alert).toHaveText(MSG.success);
    await expect(this.receipt).toBeVisible();
  }

  /** Asserts that no transfer happened: no receipt and balance/limit equal to the given values. */
  async expectNoTransfer(balance: string, remaining?: string): Promise<void> {
    await expect(this.receipt).toBeHidden();
    await expect(this.balance).toHaveText(balance);
    if (remaining) await expect(this.dailyRemaining).toHaveText(remaining);
  }
}
