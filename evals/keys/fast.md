# Trial: US-310 FAST transfer (end-to-end, black box)

Evaluator only. This key lives in `evals/keys/`, outside the trial folder, so that copying the
trial folder never copies the key. How to run and grade a blind trial: `evals/README.md`.

Reusable end-to-end evaluation: give an agent `evals/trial-fast/docs/US-310-fast-transfer.md` and the
running demo app (`node evals/trial-fast/demo-app/server.js`, http://localhost:4174) and ask it to run
the whole QA Suite chain. **Do not show this file or the `demo-app/` sources to the agent.**

## Planted defects (the suite should find all five)
| Key | Rule (story AC) | Defect in the demo app |
|---|---|---|
| A | AC-1 max 50.000,00 per transaction | exactly 50.000,00 is rejected (`>=` instead of `>`) |
| B | AC-3 valid TR IBAN incl. check digits | only the format is checked; a wrong mod-97 IBAN is accepted |
| C | AC-2 daily limit 100.000,00 cumulative | only the single amount is compared; the cumulative total is never checked |
| D | AC-5 fee only above 5.000,00 | 5.000,00 already pays the 5,00 TL fee (`>=` instead of `>`) |
| E | AC-4 OTP at 10.000,00 and above | 10.000,00 skips OTP (`>` instead of `>=`) |

Unplanted but real: amounts with a dot thousands separator ("15.000") are parsed as decimals (15,00).

## Ambiguities the analysis should raise
"uygun hata mesajı" (AC-3), "hızlı" (AC-9), "belirlenecek" (AC-10), "kullanıcı uyarılır" (AC-8),
whether the fee counts toward the daily limit, and the reset time of the daily limit.

## Result 2026-09-29 (QA Suite 0.5.0, one agent run)
All 5 planted defects found + the unplanted parsing defect. Independent rerun of its Playwright
suite: 37 passed / 9 failed (identical). All ambiguities above raised. 47 tests, 2% critical.
Cost: ~334k tokens, ~26 min, 102 tool calls.
