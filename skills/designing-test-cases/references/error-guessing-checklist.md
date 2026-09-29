# Error guessing checklist (fault taxonomy)

Pick the categories that match the feature's inputs and flows. Each item you choose becomes a test condition. Tag the tests with `error-guessing`. Security probes here are **benign** checks for correct input handling on the user's own system under test. They are not attacks.

## Contents
1. Text inputs
2. Numbers and money
3. Dates and times
4. Files
5. Forms and UI behaviour
6. Sessions, auth and permissions
7. Concurrency and timing
8. Integrations and network
9. Data and state
10. Localization (TR focus)
11. API-specific
12. Mobile-specific

---

## 1. Text inputs
- Empty; only spaces; leading or trailing spaces (is the value trimmed?); a newline in a single-line field
- Exactly the maximum length, maximum + 1, and very long input (10k characters)
- Turkish characters: `çÇğĞıIİiöÖşŞüÜ`. Also check case-insensitive matching: "İSTANBUL" vs "istanbul", and "I" vs "ı".
- Emoji and multi-byte characters (`👍🏽`), combining characters, zero-width space, right-to-left text
- HTML or script markup (`<b>x</b>`, `<script>alert(1)</script>`): is it shown escaped as text?
- SQL meta characters (`' " ; --`): the application must behave normally and return no database error
- Duplicate value where uniqueness is required, differing only in case or whitespace
- Pasted text with formatting

## 2. Numbers and money
- 0, -0, a negative number, the minimum, the maximum, max + 1, a very large number (overflow)
- Decimal separator: `12,5` vs `12.5`; thousands separator: `1.000` vs `1,000`
- Too many decimal places (`10.999` for money). Check the rounding mode and whether rounding is per line or per total.
- Leading zeros (`007`), `+5`, scientific notation (`1e3`), non-numeric input
- Currency mismatch, and percentage vs absolute amount
- Discount larger than the price (negative total?). 100% discount. Stacking of discounts.

## 3. Dates and times
- Today, yesterday, tomorrow, and a date far in the past or future
- End of month, 29.02 (leap and non-leap years), 31.12 → 01.01
- Time zone differences between user, server and storage. Midnight UTC vs midnight Türkiye time (UTC+3).
- Daylight saving transitions for users in other countries
- Date format input (`dd.MM.yyyy` vs `MM/dd/yyyy`). Invalid dates (`31.04.2026`).
- Validity: exactly at the start or expiry instant (inclusive or exclusive?)
- Age calculation on the birthday itself

## 4. Files
- Allowed type with a wrong extension; a renamed executable; a double extension (`x.pdf.exe`)
- 0-byte file, exactly the maximum size, maximum + 1, a very large file
- Name with Turkish characters, spaces, very long names, or the same name uploaded twice
- A corrupt file, a password-protected file, or many files at once
- Upload cancelled halfway, or the network lost during upload

## 5. Forms and UI behaviour
- Double-click the submit button (duplicate submission?)
- Refresh after submitting (re-post?), the browser back button after completion, and deep links opened directly
- Required field left empty after a previous error: are all errors shown at once? Is the entered data kept?
- Tab order, keyboard-only use, and the Enter key submitting the form
- Very small and very large viewports, zoom to 200%, landscape and portrait
- Autofill or password-manager filled fields
- A disabled button bypassed with the keyboard, or with a request edited in dev tools

## 6. Sessions, auth and permissions
- Session expires mid-flow: is data lost? Is the user redirected, and back to the right place after login?
- The same user in two tabs or two devices. Logging out in one tab.
- Accessing a forbidden page or action by URL or API as a lower role
- Changing an ID in the URL or payload to reach another user's object (object-level authorisation)
- Account locked or disabled while logged in
- Password reset link used twice or used after it expires

## 7. Concurrency and timing
- Two users updating the same record at the same time
- The same coupon or stock item claimed by two users simultaneously; the last item in stock
- A scheduled job (timer) runs during a user action
- A slow response followed by the user retrying (idempotency)

## 8. Integrations and network
- The third party times out, returns 5xx, returns malformed data, or answers slowly (e.g. 20 s)
- Network lost after the request was sent but before the response came back. Does the retry duplicate the operation?
- A callback or webhook arrives twice, out of order, or never
- The rate limit (429) is reached

## 9. Data and state
- Empty list, one item, many items, and exactly the page size or page size + 1
- A deleted or archived entity referenced from elsewhere
- Data created by an older version of the system (migration)
- A cache showing stale data after an update

## 10. Localization (TR focus)
- All UI texts, errors and emails appear in the selected language, with no key placeholders like `error.coupon.invalid`
- Turkish sorting (ç after c, ı before i) and Turkish-aware search
- Text expansion: Turkish strings can be longer and may overflow buttons
- Number, currency and date formatting follow the locale (`1.234,56 ₺`)

## 11. API-specific
- A missing required field, an extra unknown field, a null field, or a wrong type
- An invalid enum value, an empty array, or a very large payload
- Wrong or missing `Content-Type`, `Accept` and auth headers
- HTTP method not allowed. Status codes and error body structure match the contract.
- Pagination parameters out of range; sorting or filtering by an invalid field

## 12. Mobile-specific
- App sent to the background mid-flow; incoming call; low battery mode
- Permission denied (camera, location, notifications) and then granted later
- Offline, then back online. Airplane mode during a request.
- OS font size at maximum. Dark mode.
