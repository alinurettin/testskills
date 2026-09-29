# Mapping specification: customers (legacy MÜŞTERİ → new core `customers`)

Version 1.2 · entity: customer · owner: data migration team (fictional example data)

## 1. Files
| | Source (legacy extract) | Target (new core extract) |
|---|---|---|
| File | `legacy_customers.csv` | `new_customers.csv` |
| Encoding | Windows-1254 (cp1254) | UTF-8 |
| Delimiter | `;` | `,` |
| Header row | yes | yes |
| Decimal format | Turkish: `.` thousands, `,` decimals (`1.234,56`) | `.` decimals, no thousands separator (`1234.56`) |
| Date format | `dd.MM.yyyy` | ISO `yyyy-MM-dd` |

## 2. Scope
- All customers in the legacy extract are migrated, including passive (`P`) and closed (`K`) ones.
- The target must contain no customer that does not exist in the source (test or dummy records are not allowed in production).
- Each customer exists exactly once in the target.

## 3. Field mapping
| # | Target column | Source column(s) | Transformation rule |
|---|---|---|---|
| M1 | `customer_id` (key) | `MUSTERI_NO` | Trim; remove leading zeros (`0001017` → `1017`). |
| M2 | `full_name` | `AD`, `SOYAD` | `AD` + one space + `SOYAD`; collapse repeated spaces and trim; convert to upper case using **Turkish** rules (`i` → `İ`, `ı` → `I`). |
| M3 | `birth_date` | `DOGUM_TARIHI` | `dd.MM.yyyy` → `yyyy-MM-dd`. |
| M4 | `branch` | `SUBE_KODU` | `34` → `IST`, `06` → `ANK`, `35` → `IZM`. Other codes are rejected. |
| M5 | `balance` | `BAKIYE` | Turkish decimal text → decimal with 2 fraction digits (round half up). Negative balances are allowed. Money: the total per branch must match exactly. |
| M6 | `status` | `DURUM` | `A` → `ACTIVE`, `P` → `PASSIVE`, `K` → `CLOSED`. Other codes are rejected. |
| M7 | `email` | `EPOSTA` | Trim; lower case (addresses are ASCII). Empty stays empty. |
| M8 | — | `FAKS` | **Not migrated** (fax is no longer used; decision DM-07). |

## 4. Sign-off criteria
- 0 customers missing in the target, 0 unexpected customers, 0 duplicate customer IDs.
- 0 field differences after applying the rules above.
- Control total of `balance` per `branch` and overall: difference 0.00.
- Exceptions only if they are documented and accepted by the data owner.
