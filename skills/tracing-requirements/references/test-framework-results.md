# Test framework results → results.json → RTM

How to get automated results from any test framework into the traceability matrix. The chain is:

```
test code tagged with TC-###  →  JUnit XML report  →  scripts/junit_results.py  →  qa/results.json  →  scripts/build_rtm.py
```

Playwright has its own converter (`pw_results.py` in automating-with-playwright), because its JSON report carries tags. Everything else goes through JUnit XML, which nearly every runner can write.

## Contents
- 1. The TC ID rule
- 2. Framework recipes: JUnit 5 with Selenium or REST Assured (Maven, Gradle), TestNG, pytest, Cypress, Karate, Postman/Newman, Robot Framework, SpecFlow/Reqnroll and .NET
- 3. Running junit_results.py
- 4. Building the RTM
- 5. Troubleshooting

## 1. The TC ID rule

The ID has to reach the XML, and **most JUnit XML writers drop tags, groups, categories and descriptions**. Only the test name, the class name and (for some runners) `<property>` elements survive. So:

- Put the ID in the **test name**: `TC-101 Valid login`, or `tc101_validLogin` / `test_TC101_valid_login` / `TC101ValidLogin` where a hyphen is not allowed. All of these read as `TC-101`.
- Keep framework tags as well (`@Tag("TC-101")`, `@TC-101`, `[Tags]  TC-101`): they are what you select a regression set with, but on their own they do not reach the report.
- Use IDs that exist in `qa/test-cases.json` (3+ digits). One test may carry several IDs; several tests may share one ID (parameterized rows, several assertions). The TC is failed if any of its tests failed.

Where the converter looks, first hit wins: (1) the test itself: name, testcase `<property>` values, tag or category elements, Robot `[Tags]`; (2) the classname; (3) the enclosing suite names. So an ID on a class, a Newman request or a Robot suite covers every test inside it that has no ID of its own. Suite-level properties are ignored; they hold build and system values.

## 2. Framework recipes

### JUnit 5 with Selenium or REST Assured (Maven Surefire, Gradle)

```java
@Test
@Tag("TC-101")                                        // selection: mvn test -Dgroups=TC-101 (not in the XML)
@DisplayName("TC-101 Valid credentials log the user in")
void tc101_validCredentialsLogIn() {
    driver.get(baseUrl + "/login");                    // Selenium
    ...
}

@ParameterizedTest(name = "TC-203 basket {0} -> discount {1}")
@CsvSource({"100.00, 10.00", "99.99, 0.00"})
void minimumBasket(BigDecimal basket, BigDecimal discount) { ... }

@Test
@DisplayName("TC-501 Apply a valid coupon")
void tc501_applyValidCoupon() {                        // REST Assured
    given().contentType(ContentType.JSON).body(Map.of("code", "YAZ10", "basket", 150.00))
    .when().post("/api/coupons/apply")
    .then().statusCode(200).body("discount", equalTo(15.0f));
}
```

- **Maven Surefire / Failsafe** write the method name by default, so the method name must carry the ID. To get `@DisplayName` into the report instead, configure the reporter (Surefire 3.x):
  ```xml
  <statelessTestsetReporter implementation="org.apache.maven.plugin.surefire.extensions.junit5.JUnit5Xml30StatelessReporter">
    <usePhrasedTestCaseMethodName>true</usePhrasedTestCaseMethodName>
  </statelessTestsetReporter>
  ```
  `mvn test` writes `target/surefire-reports/TEST-*.xml`; `mvn verify` (Failsafe) writes `target/failsafe-reports/TEST-*.xml`. With `-Dsurefire.rerunFailingTestsCount=2`, a test that passes on a rerun is reported as passed and flagged `flaky`.
- **Gradle** writes display names: `gradle test` → `build/test-results/test/TEST-*.xml`. With the test-retry plugin, set `reports.junitXml.mergeReruns = true` on the test task so a retried test appears once (flaky) instead of once per attempt; otherwise pass `--retries` to the converter.

### TestNG

```java
@Test(description = "TC-151 Add a product to the cart", groups = {"TC-151", "smoke"})
public void tc151_addToCart() { ... }
```

`description` and `groups` are not in the JUnit XML: the method name must carry the ID. Each data-provider invocation is its own testcase; one failing row fails the TC. Surefire writes `target/surefire-reports/TEST-*.xml`; the same folder also holds TestNG's own `testng-results.xml` (skipped by the converter) and often a `junitreports/` copy of the same tests, so pass the glob `"target/surefire-reports/TEST-*.xml"` rather than the folder. Without Maven, TestNG writes `test-output/junitreports/TEST-*.xml`.

### pytest

```python
def test_TC301_valid_coupon_applies(api): ...

@pytest.mark.parametrize("basket, expected", [("99.99", "0.00"), ("100.00", "10.00")],
                         ids=["TC-302-99.99", "TC-302-100.00"])
def test_coupon_boundaries(api, basket, expected): ...

@pytest.mark.tc("TC-303")                              # copied into the report by conftest.py below
def test_expired_coupon_is_rejected(api): ...
```

```python
# conftest.py: every @pytest.mark.tc(...) becomes <property name="tc" value="TC-303"/> in the JUnit XML
def pytest_configure(config):
    config.addinivalue_line("markers", "tc(*ids): QA Suite test case IDs")

def pytest_collection_modifyitems(items):
    for item in items:
        for mark in item.iter_markers("tc"):
            item.user_properties.extend(("tc", tc) for tc in mark.args)
```

Run `pytest --junitxml=reports/pytest.xml`. pytest warns that testcase properties are outside the xunit2 schema; the converter reads them anyway (`-o junit_family=xunit1` silences the warning). `@pytest.mark.xfail(reason="SHOP-512 …")` is reported as **failed** with the note "known product defect", like Playwright's `test.fail()`: the requirement is still not met. `pytest.skip` is skipped.

### Cypress

```js
describe('Login', () => {
  it('TC-401 accepts valid credentials', () => { /* … */ })
  // @cypress/grep tags select tests; only the title reaches the report
  it('TC-402 shows an error for a wrong password', { tags: ['@TC-402', '@smoke'] }, () => { /* … */ })
})
```

```js
// cypress.config.js: the built-in "junit" reporter (mocha-junit-reporter)
reporter: 'junit',
reporterOptions: { mochaFile: 'reports/junit/results-[hash].xml', includePending: true },
```

`npx cypress run` writes one file per spec. Delete `reports/junit/` before each run, or old files are read again. Pending (`it.skip`) tests appear only with `includePending: true`.

### Karate

```gherkin
@TC-601 @smoke
Scenario: TC-601 apply a valid coupon

@TC-603
Scenario Outline: TC-603 minimum basket <basket>
```

```java
Results results = Runner.path("classpath:coupons").outputJunitXml(true).parallel(5);
```

The report (`target/karate-reports/*.xml`) names each test `[1:7] TC-601 apply a valid coupon`; tags are not in it, so the scenario title carries the ID. Every outline example row is its own testcase.

### Postman / Newman

Put the ID in the request name (`Coupons / TC-501 Apply a valid coupon`); every `pm.test` of that request inherits it. An ID in a `pm.test` name (`pm.test("TC-503 order is created", …)`) works too.

```bash
newman run shop.postman_collection.json -e staging.postman_environment.json \
    -r cli,junit --reporter-junit-export reports/newman.xml
```

Any failing assertion of the request fails the TC. Newman already merges iterations: an assertion that failed in any iteration is one failure.

### Robot Framework

```robotframework
*** Test Cases ***
TC-701 Valid Login
    [Tags]    TC-701    smoke
    Open Login Page
    ...
```

`robot --outputdir reports --xunit xunit.xml tests/` writes `reports/output.xml` and `reports/xunit.xml`. The xUnit file has no tags, so either keep the ID in the test name or pass **`reports/output.xml`** to the converter: it reads Robot's own output and takes the IDs from `[Tags]`. An ID in a suite name (file `TC-704_password_reset.robot`) covers the tests in it.

### SpecFlow / Reqnroll and other .NET tests

```gherkin
@TC-803
Scenario: TC-803 Guest can pay by card
```

```csharp
[Fact(DisplayName = "TC-801 Valid coupon is applied")]   // xUnit; NUnit/MSTest: name the method TC801_ValidCouponIsApplied
public void TC801_ValidCouponIsApplied() { ... }
```

Gherkin tags become NUnit categories, xUnit traits or MSTest categories, and the JUnit logger does not write those, so the scenario title carries the ID. The generated test name (`TC803GuestCanPayByCard`, or the display name) is recognised. Add the logger package `JunitXml.TestLogger` to the test project, then:

```bash
dotnet test --logger "junit;LogFilePath=TestResults/{assembly}.{framework}.junit.xml"
```

## 3. Running junit_results.py

```bash
python scripts/junit_results.py <files | folders | "globs"> --out qa/results.json \
    [--project chrome] [--source cypress] [--run "Sprint 14 RC2"] [--retries]
```

| Option | Meaning |
|---|---|
| inputs | Report files, folders (every `*.xml` inside, recursively; non-JUnit XML is skipped) or quoted globs, several at once |
| `--project` (`--device`, `--env`) | The environment of this run: browser, device, OS or stage. Runs on several environments accumulate under `projects`. |
| `--source` | The `source` value (`surefire`, `pytest`, `cypress`, …). A TC keeps the per-project results of earlier runs **only when the source is the same**; give all converters one `--source` (for example `ci`) if a TC is automated in two frameworks. |
| `--run` | Run label shown in reports (default: the existing label) |
| `--retries` | A test repeated inside one report is a retry: the last attempt counts, earlier failures mark it flaky. Without it, every repetition is a run of its own and any failure fails it. |

Status of one test: `<failure>` or `<error>` → failed; `<skipped>` → skipped (with the skip reason as `note`); `<flakyFailure>`/`<flakyError>` only → passed and `flaky: true`; a Maestro-style `status="ERROR"` → failed. Per TC over all its tests: failed if any failed, passed if one passed and none failed, otherwise skipped. Per TC over projects, the same rule.

The converter keeps entries it does not mention (manual results) and defect keys already linked in `results.json`. It prints the tests that carry no TC ID; they are not traceable until they get one.

Exit codes: 0 ok, 2 a report is unreadable or malformed, a pattern matches nothing, or `--out` is unreadable (nothing is written).

## 4. Building the RTM

```bash
python scripts/build_rtm.py --requirements qa/requirements.json --tests qa/test-cases.json \
    --results qa/results.json --out-dir qa
```

Each requirement rolls up the results of its linked tests (failed if any failed, passed only if all passed). Failed requirements show up as `FAILED` gaps. The warning `results.json: unknown test TC-…` means an automated test carries an ID that is not in `test-cases.json`: a typo, or a test that was never designed. Fix the name, or design the test case.

A typical CI step:

```bash
python scripts/junit_results.py "target/surefire-reports/TEST-*.xml" --source ci --project api --out qa/results.json
python scripts/junit_results.py "reports/junit/results-*.xml" --source ci --project chrome --out qa/results.json
python scripts/build_rtm.py --requirements qa/requirements.json --tests qa/test-cases.json \
    --results qa/results.json --out-dir qa --strict
```

## 5. Troubleshooting

| Symptom | Cause and fix |
|---|---|
| "N tests carry no TC-###" | The ID is only in a tag, group, category or description. Put it in the test name (section 1). |
| Every TC counted twice, doubled durations | The same tests are in two files (TestNG `junitreports/`, an old Cypress file). Pass a narrower glob or clean the report folder. |
| A glob matches nothing on Windows | Quote it; the converter expands `*`, `?` and `**` itself. |
| "root element <…> is not JUnit XML" | The file is another format: TestNG `testng-results.xml`, NUnit/xUnit/TRX. Use the runner's JUnit output. |
| "contained characters that are not allowed in XML" | ANSI colour codes in failure messages; they were removed. Disable colours in CI to keep messages clean. |
| A flaky test shows as failed | The runner wrote each attempt separately. Merge reruns in the runner (Surefire rerun, Gradle `mergeReruns`) or pass `--retries`. |
| Skipped tests are missing | The reporter drops pending tests (Cypress: `includePending: true`). |
