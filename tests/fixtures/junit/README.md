# JUnit XML fixtures

These reports are **representative, not captured**. They were written by hand from the documented
output schema of each reporter, as it was known when they were written, to exercise
`shared/scripts/junit_results.py` (tests: `tests/test_junit_xlsx.py`). All names, hosts, URLs and data are
synthetic. Real reports carry more attributes, properties and output; minor details (attribute order,
whitespace, exact message wording, version-specific attributes) will differ.

| Folder / file | Written after | What it exercises |
|---|---|---|
| `surefire-junit5/` | Maven Surefire 3.x report, JUnit 5 | method names `tc101_…`, `<failure>` + `<rerunFailure>`, `<flakyFailure>` (rerunFailingTestsCount), `<error>`, `<skipped message>`, suite `<properties>` that must be ignored (`TC-900` in a path), phrased `@DisplayName` names in a second file, folder input |
| `surefire-testng/` | Maven Surefire 3.x report, TestNG | one `TEST-TestSuite.xml` for all classes, a data-provider method repeated three times (one failing run fails the TC), ID only in the class name (`TC155PaymentTest`), a `testng-results.xml` (TestNG's own format) in the same folder that must be skipped |
| `gradle/` | Gradle `test` task report, JUnit Platform | display names `TC-201 …`, parameterized invocation names, `test-retry` plugin without `mergeReruns` (the same test twice: failed, then passed; `--retries` turns it into passed + flaky), `<skipped/>` |
| `pytest/junit.xml` | `pytest --junitxml` | `test_TC301_…` names, parametrize ids `[TC-302-…]`, `record_property` / `user_properties` (`test_id`, `tc`), `pytest.xfail` (known defect), `pytest.skip`, setup `<error>` |
| `cypress/results-*.xml` | Cypress `reporter: junit` (mocha-junit-reporter), `mochaFile` with `[hash]` | two files read through a glob, full-title names with the describe prefix, `Root Suite` testsuite with `file`, `<skipped/>` (includePending) |
| `newman/newman-shop-api.xml` | `newman run -r junit` | one testsuite per request (`Folder / TC-501 …`), `pm.test` assertions as testcases, classname made by the reporter (`CouponsTc501ApplyAValidCoupon`), `Failed 1 times.` CDATA |
| `karate/coupons.coupons.xml` | Karate `outputJunitXml(true)` | `[1:7] TC-601 …` scenario names, outline rows `[3.1:30]`, step log in `<system-out>` / `<failure>` |
| `robot/xunit.xml` | `robot --xunit` (RF 7) | nested suites, `SkipExecution`, suite documentation as properties, ID only in a suite name (`TC-704 Password Reset`) |
| `robot/output.xml` | Robot Framework 7 `output.xml` (schema 5) | IDs in `[Tags]`, `PASS/FAIL/SKIP`, `elapsed` times |
| `dotnet/Shop.Tests.net8.0.junit.xml` | `dotnet test --logger junit` (JunitXml.TestLogger) | `TC801_…` methods, theory arguments in the name, Reqnroll/SpecFlow method name `TC803GuestCanPayByCard`, `<skipped />` |
| `generic/nested-properties.xml` | no single tool | nested `testsuites`, IDs from `<property name="tc">`, a tag-list property, a bare-number `test_case_id`, an `id` attribute, a suite name; Maestro-style `status="ERROR"`, `<flakyError>`, `0,25` and `1,234.5` times, a suite property that must be ignored (`TC-999`) |

Expected results per fixture are asserted in `tests/test_junit_xlsx.py`. When you capture a real report
from one of these tools, add it next to the representative one (do not replace it) and extend the test.
