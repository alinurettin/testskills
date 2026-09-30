# Export fixtures

Used by `tests/test_export_golden.py`.

## golden/

`golden/<tool>.csv` is the output of `skills/exporting-test-cases/scripts/export_tests.py` for
`tests/fixtures/coupon` (options in `CASES` of the test). The test fails whenever the output changes, so
a format change is always deliberate. After an intended change:

```bash
QA_UPDATE_GOLDEN=1 python -m unittest tests.test_export_golden     # PowerShell: $env:QA_UPDATE_GOLDEN=1
# or
python tests/test_export_golden.py --update
```

This also regenerates `examples/import-kit/`. Review the diff before committing. The comparison parses
the CSV and ignores CRLF/LF differences, because `.gitattributes` stores text files with LF.

## vendor/

Files exported by the real tools after a real import, see [vendor/README.md](vendor/README.md).
