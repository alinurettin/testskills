-- =====================================================================================
-- QA Suite · testing-data-migrations · reconciliation query templates
-- -------------------------------------------------------------------------------------
-- Replace the {{placeholders}} before running:
--   {{src}} / {{tgt}}        source and target tables (or staging copies of the extracts)
--   {{key}}                  business key column (for composite keys repeat the join terms)
--   {{grp}}                  grouping column (branch, product, currency, month ...)
--   {{amt}}                  money/amount column for control totals
--   {{cols_src}} / {{cols_tgt}}  normalised column expressions, in the SAME order, for row hashes
--   {{parent}} / {{parent_key}} / {{fk}}   parent table, its key, and the child's foreign key
-- Written in standard SQL; dialect notes are marked "-- PG:", "-- MSSQL:", "-- ORA:", "-- MYSQL:".
-- Run against READ-ONLY copies or replicas, never with write access to production.
-- When source and target live in different databases, stage both into one database, or
-- extract "key + control columns + row hash" from each side and compare with reconcile.py.
-- =====================================================================================


-- -------------------------------------------------------------------------------------
-- 0. SOURCE PROFILING (before the first mock migration)
-- -------------------------------------------------------------------------------------

-- 0.1 Row count, null count and distinct count per column (repeat per column)
SELECT COUNT(*)                                        AS row_count,
       COUNT(*) - COUNT({{col}})                       AS null_count,
       SUM(CASE WHEN TRIM({{col}}) = '' THEN 1 ELSE 0 END) AS blank_count,  -- ORA: '' IS NULL, drop this line
       COUNT(DISTINCT {{col}})                         AS distinct_count,
       MIN({{col}}) AS min_value, MAX({{col}}) AS max_value
FROM {{src}};

-- 0.2 Duplicate business keys in the source
SELECT {{key}}, COUNT(*) AS occurrences
FROM {{src}}
GROUP BY {{key}}
HAVING COUNT(*) > 1
ORDER BY occurrences DESC;

-- 0.3 Invalid codes: values that the mapping specification does not cover
SELECT {{code_col}}, COUNT(*) AS rows_with_code
FROM {{src}}
WHERE {{code_col}} IS NULL OR {{code_col}} NOT IN ('A', 'P', 'K')   -- the codes listed in the mapping spec
GROUP BY {{code_col}};

-- 0.4 Orphans in the source (child rows whose parent does not exist) - these will fail FK constraints in the target
SELECT c.*
FROM {{src}} c
LEFT JOIN {{parent}} p ON p.{{parent_key}} = c.{{fk}}
WHERE c.{{fk}} IS NOT NULL AND p.{{parent_key}} IS NULL;

-- 0.5 Dates stored as text that do not match the documented format dd.MM.yyyy
SELECT {{key}}, {{date_col}}
FROM {{src}}
WHERE {{date_col}} IS NOT NULL
  AND NOT ({{date_col}} LIKE '__.__.____');
-- PG:    AND {{date_col}} !~ '^\d{2}\.\d{2}\.\d{4}$'   plus  to_date(...) inside a safe function for impossible dates (31.02)
-- MSSQL: AND TRY_CONVERT(date, {{date_col}}, 104) IS NULL      (style 104 = dd.mm.yyyy)
-- ORA:   AND VALIDATE_CONVERSION({{date_col}} AS DATE, 'DD.MM.YYYY') = 0   (12.2+)

-- 0.6 Non-ASCII characters (Turkish letters, mojibake such as 'Ã', 'Ä°', 'Þ', 'Ý', '?')
SELECT {{key}}, {{text_col}}
FROM {{src}}
WHERE {{text_col}} LIKE '%Ã%' OR {{text_col}} LIKE '%Ä%' OR {{text_col}} LIKE '%Å%'
   OR {{text_col}} LIKE '%Þ%' OR {{text_col}} LIKE '%Ý%' OR {{text_col}} LIKE '%ý%' OR {{text_col}} LIKE '%þ%'
   OR {{text_col}} LIKE '%?%';
-- Legitimate Turkish text never contains Ã, Ä, Å, Þ, Ý, ý or þ; their presence means text was
-- decoded with the wrong code page somewhere upstream. '?' may be a lost character (check it).

-- 0.7 Decimal comma stored in a text amount column (will be misparsed by a naive loader)
SELECT {{key}}, {{amt_text}}
FROM {{src}}
WHERE {{amt_text}} LIKE '%,%';


-- -------------------------------------------------------------------------------------
-- 1. COUNTS
-- -------------------------------------------------------------------------------------
SELECT 'source' AS side, COUNT(*) AS row_count, COUNT(DISTINCT {{key}}) AS distinct_keys FROM {{src}}
UNION ALL
SELECT 'target', COUNT(*), COUNT(DISTINCT {{key}}) FROM {{tgt}};


-- -------------------------------------------------------------------------------------
-- 2. CONTROL TOTALS PER GROUP (counts and sums; money must match exactly)
-- -------------------------------------------------------------------------------------
-- Apply the mapping's group transformation on the source side (e.g. CASE for 34 -> 'IST').
WITH s AS (
  SELECT {{grp_src_expr}} AS grp, COUNT(*) AS n, SUM({{amt_src_expr}}) AS total
  FROM {{src}} GROUP BY {{grp_src_expr}}
), t AS (
  SELECT {{grp}} AS grp, COUNT(*) AS n, SUM({{amt}}) AS total
  FROM {{tgt}} GROUP BY {{grp}}
)
SELECT COALESCE(s.grp, t.grp)                   AS grp,
       s.n AS src_count,  t.n AS tgt_count,  COALESCE(t.n, 0) - COALESCE(s.n, 0)         AS count_diff,
       s.total AS src_total, t.total AS tgt_total, COALESCE(t.total, 0) - COALESCE(s.total, 0) AS total_diff
FROM s FULL OUTER JOIN t ON s.grp = t.grp          -- MYSQL: no FULL OUTER JOIN; UNION a LEFT and a RIGHT join
WHERE COALESCE(s.n, 0) <> COALESCE(t.n, 0)
   OR COALESCE(s.total, 0) <> COALESCE(t.total, 0)
ORDER BY 1;
-- Keep amounts in DECIMAL/NUMERIC. Never SUM a FLOAT/REAL money column: the total itself will be inexact.
-- If the source stores '1.234,56' as text:
--   PG:    CAST(REPLACE(REPLACE({{amt_text}}, '.', ''), ',', '.') AS NUMERIC(18,2))
--   MSSQL: CAST(REPLACE(REPLACE({{amt_text}}, '.', ''), ',', '.') AS DECIMAL(18,2))
--   ORA:   TO_NUMBER({{amt_text}}, '999G999G999D99', 'NLS_NUMERIC_CHARACTERS='',.''')


-- -------------------------------------------------------------------------------------
-- 3. KEY-SET COMPARISON (both directions)
-- -------------------------------------------------------------------------------------
-- 3.1 Missing in target
SELECT s.{{key}}
FROM {{src}} s
WHERE NOT EXISTS (SELECT 1 FROM {{tgt}} t WHERE t.{{key}} = {{key_src_expr}});   -- e.g. CAST(LTRIM(s.no, '0') AS ...)

-- 3.2 Unexpected in target
SELECT t.{{key}}
FROM {{tgt}} t
WHERE NOT EXISTS (SELECT 1 FROM {{src}} s WHERE {{key_src_expr}} = t.{{key}});

-- 3.3 Duplicate keys in target (a non-idempotent re-run shows up here)
SELECT {{key}}, COUNT(*) AS occurrences
FROM {{tgt}}
GROUP BY {{key}}
HAVING COUNT(*) > 1;
-- Also check NOT EXISTS with NULL keys: NOT IN (subquery) returns nothing when the subquery has a NULL.


-- -------------------------------------------------------------------------------------
-- 4. ROW HASH COMPARISON (find rows whose content differs)
-- -------------------------------------------------------------------------------------
-- Both sides must produce the SAME normalised string before hashing:
--   * same column order, a separator that cannot occur in the data (e.g. '|' or CHR(31))
--   * NULL made explicit: COALESCE(col, '<NULL>') - CONCAT_WS silently SKIPS NULLs in PG and
--     MSSQL, so ('a', NULL, 'b') and ('a', 'b', NULL) would hash the same
--   * the mapping's transformations applied on the source side (trim, case, code maps)
--   * dates as ISO text (YYYY-MM-DD), numbers with a fixed scale and '.' as decimal separator
--   * the same character encoding: hash UTF-8 bytes on both sides
-- Standard-ish pattern:
--   <hash>( COALESCE(TRIM(c1), '<NULL>') || '|' || COALESCE(TO_CHAR_ISO(c2), '<NULL>') || '|' || ... )
--
-- PG:    md5(...)  or  encode(sha256(convert_to(..., 'UTF8')), 'hex')                   (PG 11+)
-- MSSQL: CONVERT(char(64), HASHBYTES('SHA2_256', CAST((...) COLLATE Latin1_General_100_CI_AS_SC_UTF8 AS varchar(max))), 2)
--        HASHBYTES hashes the BYTES: NVARCHAR gives UTF-16LE, VARCHAR gives the column's code page
--        (cp1254 for Turkish_CI_AS). Cast to a UTF-8 collation (SQL Server 2019+) or the hashes
--        will never match another DBMS. Input limit of 8000 bytes applies before SQL Server 2016.
-- ORA:   STANDARD_HASH(..., 'SHA256')  (12c+; hashes the database character set bytes - AL32UTF8 = UTF-8)
--        ORA_HASH is 32-bit: acceptable for bucketing, NOT for proving equality (collisions).
-- MYSQL: SHA2(CONCAT_WS('|', COALESCE(c1,'<NULL>'), ...), 256)  (connection charset utf8mb4)

WITH s AS (
  SELECT {{key_src_expr}} AS k, {{hash_fn}}({{cols_src}}) AS h FROM {{src}}
), t AS (
  SELECT {{key}} AS k, {{hash_fn}}({{cols_tgt}}) AS h FROM {{tgt}}
)
SELECT s.k
FROM s JOIN t ON s.k = t.k
WHERE s.h <> t.h;
-- Then compare those keys column by column (or export key+columns and run reconcile.py for hints).
-- Cross-database: export "key,row_hash" from each side to CSV and run
--   reconcile.py --source src_hash.csv --target tgt_hash.csv --key k


-- -------------------------------------------------------------------------------------
-- 5. REFERENTIAL INTEGRITY IN THE TARGET (orphans)
-- -------------------------------------------------------------------------------------
SELECT c.{{fk}}, COUNT(*) AS orphan_rows
FROM {{tgt_child}} c
LEFT JOIN {{tgt_parent}} p ON p.{{parent_key}} = c.{{fk}}
WHERE c.{{fk}} IS NOT NULL AND p.{{parent_key}} IS NULL
GROUP BY c.{{fk}};
-- Migrations often load with constraints disabled for speed; re-enable them WITH validation
-- (MSSQL: ALTER TABLE ... WITH CHECK CHECK CONSTRAINT ALL; ORA: ENABLE VALIDATE) or run this query.


-- -------------------------------------------------------------------------------------
-- 6. BUSINESS-RULE RECONCILIATION (the data must still make sense)
-- -------------------------------------------------------------------------------------
-- 6.1 Account balance = opening balance + sum of migrated transactions
SELECT a.{{acc_key}}, a.balance, a.opening_balance + COALESCE(SUM(tx.amount), 0) AS computed
FROM {{tgt_accounts}} a
LEFT JOIN {{tgt_transactions}} tx ON tx.{{acc_key}} = a.{{acc_key}}
GROUP BY a.{{acc_key}}, a.balance, a.opening_balance
HAVING a.balance <> a.opening_balance + COALESCE(SUM(tx.amount), 0);

-- 6.2 Status consistency (e.g. CLOSED accounts must have zero balance and a closing date)
SELECT {{key}}, status, balance, closed_at
FROM {{tgt}}
WHERE status = 'CLOSED' AND (balance <> 0 OR closed_at IS NULL);

-- 6.3 Distribution check: counts per status/code before and after (catches wrong code maps)
SELECT {{code_col}} AS code, COUNT(*) FROM {{tgt}} GROUP BY {{code_col}} ORDER BY 1;
