#!/usr/bin/env python3
"""Merge JUnit XML reports from any test framework into QA Suite results.json, keyed by TC ID.

Reads the JUnit XML that nearly every runner writes: Maven Surefire/Failsafe (JUnit 4/5, TestNG),
Gradle, TestNG junitreports, pytest --junitxml, Cypress (mocha-junit-reporter), Newman/Postman
(-r junit), Karate (outputJunitXml), Robot Framework (--xunit), .NET (JunitXml.TestLogger), Maestro,
Espresso/XCUITest/Appium/Detox converters. Robot Framework output.xml is read as well, because only
that file carries the test [Tags]. Pass files, folders (every *.xml inside, recursively) or globs.

Where the TC ID is found (first level that yields an ID wins):
  1. the test itself: its name, its <property> values (pytest record_property("tc", "TC-101") or
     item.user_properties, <property name="tags" value="TC-101,smoke"/>), tag/category child
     elements or attributes, and Robot [Tags];
  2. the classname (Java/.NET class, Newman request, Karate feature);
  3. the enclosing testsuite names (Cypress describe, Newman request, Robot suite) and file attributes.
  "TC-101", and "TC101" / "TC_101" in identifiers that cannot hold a hyphen (test_TC101_login,
  tc101_validLogin, loginTC101, Tc201ApplyCoupon from Newman) all mean TC-101.

Status of one test:
  <failure> or <error> -> failed; <skipped> -> skipped (pytest xfail -> failed, known product defect);
  Surefire/Gradle reruns: <flakyFailure>/<flakyError> without <failure> -> passed, flaky.
  The same test repeated inside one report (TestNG data provider, repeated runs) counts once per run:
  any failed run fails it. With --retries the repeats are retries (Gradle test-retry without
  mergeReruns): the last attempt counts and earlier failures mark it flaky.
  A status/result attribute (Maestro ERROR/FAILED) counts as well.
Several tests with one TC ID: failed if any failed, passed if one passed and none failed, else skipped.

Results are recorded per --project (device, browser, OS or environment; --device is the same option)
under "projects", so reports of several environments accumulate: a TC is failed if it failed in any,
passed if it passed in at least one and failed in none, otherwise skipped. Entries of --out that these
reports do not mention (manual results) are kept, and so are defect keys.

Usage:
  python junit_results.py target/surefire-reports --out qa/results.json --source surefire --run "RC2"
  python junit_results.py "results/junit-*.xml" --project chrome --source cypress --out qa/results.json
  python junit_results.py reports/pixel8.xml --device "Pixel 8 / Android 16" --source maestro --out qa/results.json
Then:  python build_rtm.py --requirements qa/requirements.json --tests qa/test-cases.json --results qa/results.json
Exit codes: 0 ok, 2 unreadable or malformed report, no report found, or unreadable --out.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

# TC-101; TC101 / TC_101 / tc101 at an identifier boundary; loginTC101 / CouponsTc201 at a camelCase boundary
TC = re.compile(r"(?<![A-Za-z0-9])TC[-_]?(\d{3,})(?!\d)", re.IGNORECASE)
TC_CAMEL = re.compile(r"(?<=[a-z])T[Cc][-_]?(\d{3,})(?!\d)")
ID_KEYS = {"tc", "tc_id", "tcid", "test_id", "testid", "test_case", "testcase", "test_case_id", "testcaseid",
           "testcase_id", "qa_id"}
TAG_NAMES = {"tag", "tags", "label", "labels", "category", "categories", "trait", "traits"}
ATTR_KEYS = {"id", "tc", "tags", "tag", "labels", "label", "category", "categories", "test_id", "testid"}
FAILED_STATUS = {"error", "errored", "failed", "failure", "fail", "broken"}
SKIPPED_STATUS = {"skipped", "skip", "ignored", "disabled", "pending", "notrun", "not run", "not_run"}
RANK = {"failed": 4, "known-defect": 3, "flaky": 2, "passed": 1, "skipped": 0}
KNOWN_DEFECT_NOTE = "known product defect (pytest xfail): expected behaviour still not met"
ANSI = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")
BAD_CHARS = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f\ufffe\uffff]")
BAD_REFS = re.compile(r"&#(?:[xX]0*(?:[0-8bBcCeEfF]|1[0-9a-fA-F])|0*(?:[0-8]|1[124-9]|2[0-9]|3[01]));")
OTHER_FORMATS = {"testng-results": "TestNG's own report; read the JUnit files (surefire-reports/TEST-*.xml or "
                                   "test-output/junitreports/TEST-*.xml)",
                 "test-run": "NUnit 3 XML; run dotnet test with the JUnit logger (JunitXml.TestLogger)",
                 "assemblies": "xUnit v2 XML; run dotnet test with the JUnit logger (JunitXml.TestLogger)",
                 "TestRun": "TRX; run dotnet test with the JUnit logger (JunitXml.TestLogger)"}


def local(tag) -> str:
    return tag.rsplit("}", 1)[-1] if isinstance(tag, str) else ""


def kids(el, *names):
    return [k for k in el if local(k.tag) in names]


def tc_ids(text: str) -> list[str]:
    text = text or ""
    return list(dict.fromkeys(f"TC-{m}" for m in TC.findall(text) + TC_CAMEL.findall(text)))


def parse_time(value) -> float:
    """Seconds; tolerates '1,234.5' (old Surefire) and '0,25' (comma-decimal locales)."""
    s = (value or "").strip()
    if "," in s:
        s = s.replace(",", "") if "." in s else s.replace(",", ".")
    try:
        v = float(s)
    except ValueError:
        return 0.0
    return v if 0 < v < float("inf") else 0.0            # also drops NaN


def first_line(*texts) -> str:
    for raw in texts:
        lines = [x.strip() for x in ANSI.sub("", raw or "").splitlines() if x.strip()]
        if lines:
            return lines[0][:300]
    return ""


# ------------------------------------------------------------------ reading files
def load_xml(path: Path) -> tuple[ET.Element, bool]:
    """Parse; if the XML is not well-formed only because of control characters (ANSI colour codes in
    failure messages are common), strip them and parse again. Returns (root, cleaned)."""
    data = path.read_bytes()
    try:
        return ET.fromstring(data), False
    except ET.ParseError:
        m = re.match(rb"^\s*<\?xml[^>]*encoding=[\"']([A-Za-z0-9._-]+)", data.lstrip(b"\xef\xbb\xbf"))
        try:
            text = data.decode(m.group(1).decode("ascii") if m else "utf-8-sig", errors="replace")
        except LookupError:
            text = data.decode("utf-8-sig", errors="replace")
        cleaned = BAD_CHARS.sub("", BAD_REFS.sub("", ANSI.sub("", text)))
        if cleaned == text:
            raise
        return ET.fromstring(cleaned), True


def expand(inputs: list[str]) -> tuple[list[tuple[Path, bool]], list[str]]:
    """-> ([(file, named explicitly)], [patterns without matches])"""
    files, missing, seen = [], [], set()
    for item in inputs:
        p = Path(item)
        if p.is_dir():
            found = [(f, False) for f in sorted(p.rglob("*.xml"))]
        elif any(ch in item for ch in "*?["):
            found = [(Path(f), False) for f in sorted(glob.glob(item, recursive=True)) if Path(f).is_file()]
        else:
            found = [(p, True)]
        if not found:
            missing.append(item)
        for f, explicit in found:
            key = os.path.normcase(str(f.resolve()))
            if key not in seen:
                seen.add(key)
                files.append((f, explicit))
    return files, missing


# ------------------------------------------------------------------ one <testcase> -> attempt
def junit_status(tc: ET.Element) -> tuple[str, str, str]:
    """-> (kind, error, note); kind in failed, known-defect, flaky, passed, skipped"""
    for tag in ("failure", "error"):
        for el in kids(tc, tag):
            return "failed", first_line(el.get("message"), el.text) or el.get("type") or tag, ""
    for el in kids(tc, "skipped"):
        msg = first_line(el.get("message"), el.text)
        if (el.get("type") or "").lower() == "pytest.xfail":
            return "known-defect", msg, KNOWN_DEFECT_NOTE
        return "skipped", "", msg
    if kids(tc, "flakyFailure", "flakyError"):
        return "flaky", "", ""
    status = (tc.get("status") or tc.get("result") or "").strip().lower()
    if status in FAILED_STATUS:
        return "failed", f"status {tc.get('status') or tc.get('result')}", ""
    if status in SKIPPED_STATUS:
        return "skipped", "", ""
    return "passed", "", ""


def own_ids(tc: ET.Element) -> list[str]:
    ids = tc_ids(tc.get("name", ""))
    for props in kids(tc, "properties"):
        for p in kids(props, "property"):
            key = re.sub(r"[\s-]+", "_", (p.get("name") or "").strip().lower())
            val = p.get("value") if p.get("value") is not None else (p.text or "")
            found = tc_ids(val)
            if not found and key in ID_KEYS and re.fullmatch(r"\s*\d{3,}\s*", val):
                found = [f"TC-{val.strip()}"]
            ids += found
    for el in tc.iter():
        if el is not tc and local(el.tag).lower() in TAG_NAMES:
            ids += tc_ids(" ".join([el.text or "", el.get("name", ""), el.get("value", "")]))
    for key, val in tc.attrib.items():
        if local(key).lower() in ATTR_KEYS:
            ids += tc_ids(val)
    return list(dict.fromkeys(ids))


def junit_attempts(root: ET.Element, source: str) -> list[dict]:
    out = []

    def walk(el, suites):
        for child in el:
            t = local(child.tag)
            if t == "testcase":
                out.append((child, suites))
            elif t in ("testsuite", "testsuites"):
                walk(child, [child] + suites)
            elif t not in ("properties", "system-out", "system-err"):
                walk(child, suites)

    walk(root, [root] if local(root.tag) in ("testsuite", "testsuites") else [])
    attempts = []
    for tc, suites in out:
        kind, err, note = junit_status(tc)
        context = " ".join([tc.get("file", "")] + [f"{s.get('name', '')} {s.get('file', '')}" for s in suites])
        attempts.append({
            "key": (source, tuple(s.get("name", "") for s in suites), tc.get("classname", ""), tc.get("name", "")),
            "label": tc.get("name") or tc.get("classname") or "?",
            "levels": [own_ids(tc), tc_ids(tc.get("classname", "")), tc_ids(context)],
            "kind": kind, "error": err, "note": note, "seconds": parse_time(tc.get("time"))})
    return attempts


# ------------------------------------------------------------------ Robot Framework output.xml
def robot_seconds(status: ET.Element) -> float:
    if status.get("elapsed"):                                   # RF 7
        return parse_time(status.get("elapsed"))
    try:                                                        # RF <= 6
        fmt = "%Y%m%d %H:%M:%S.%f"
        return max((datetime.strptime(status.get("endtime", ""), fmt)
                    - datetime.strptime(status.get("starttime", ""), fmt)).total_seconds(), 0.0)
    except ValueError:
        return 0.0


def robot_attempts(root: ET.Element, source: str) -> list[dict]:
    out = []

    def walk(el, suites):
        for child in el:
            t = local(child.tag)
            if t == "suite":
                walk(child, suites + [child.get("name", "")])
            elif t == "test":
                out.append((child, suites))

    walk(root, [])
    attempts = []
    for test, suites in out:
        tags = [t.text or "" for t in kids(test, "tag")] + [t.text or "" for g in kids(test, "tags") for t in kids(g, "tag")]
        st = (kids(test, "status") or [ET.Element("status")])[-1]
        value = (st.get("status") or "").upper()
        msg = first_line(st.text)
        kind = {"PASS": "passed", "FAIL": "failed"}.get(value, "skipped")
        note = msg if kind == "skipped" else ""
        if value == "NOT RUN" and not note:
            note = "not run"
        attempts.append({
            "key": (source, tuple(suites), ".".join(suites), test.get("name", "")),
            "label": test.get("name") or "?",
            "levels": [list(dict.fromkeys(tc_ids(test.get("name", "")) + [i for t in tags for i in tc_ids(t)])),
                       [], tc_ids(" ".join(suites))],
            "kind": kind, "error": (msg or "FAIL") if kind == "failed" else "", "note": note,
            "seconds": robot_seconds(st)})
    return attempts


# ------------------------------------------------------------------ aggregation
def settle(attempts: list[dict], retries: bool) -> dict:
    """One test identity that may appear several times in a report. By default every appearance is a run
    of its own and the worst one counts; with retries the last attempt counts and earlier failures make
    it flaky."""
    if retries:
        pick = attempts[-1]
        kind = pick["kind"]
        if kind == "passed" and any(a["kind"] in ("failed", "flaky") for a in attempts[:-1]):
            kind = "flaky"
    else:
        pick = max(attempts, key=lambda a: RANK[a["kind"]])  # first of the worst
        kind = pick["kind"]
    return {"kind": kind, "error": pick["error"], "note": pick["note"],
            "seconds": sum(a["seconds"] for a in attempts), "levels": pick["levels"], "label": pick["label"]}


def collect(attempts: list[dict], retries: bool = False) -> tuple[dict, list[str], int]:
    identities: dict[tuple, list] = {}
    for att in attempts:
        identities.setdefault(att["key"], []).append(att)
    found: dict[str, dict] = {}
    untagged = []
    for runs in identities.values():
        test = settle(runs, retries)
        ids = next((lvl for lvl in test["levels"] if lvl), [])
        if not ids:
            untagged.append(test["label"])
            continue
        for tid in ids:
            e = found.setdefault(tid, {"kind": "skipped", "errors": [], "notes": [], "seconds": 0.0, "tests": 0})
            if RANK[test["kind"]] > RANK[e["kind"]]:
                e["kind"] = test["kind"]
            if test["error"] and test["kind"] in ("failed", "known-defect") and test["error"] not in e["errors"]:
                e["errors"].append(test["error"])
            if test["note"] and test["note"] not in e["notes"]:
                e["notes"].append(test["note"])
            e["seconds"] += test["seconds"]
            e["tests"] += 1
    return found, untagged, len(identities)


def rollup(kinds: set) -> str:
    if kinds & {"failed", "known-defect"}:
        return "failed"
    if kinds & {"passed", "flaky"}:
        return "passed"
    return "skipped"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("reports", nargs="+", help="JUnit XML files, folders or glob patterns (quote globs on Windows)")
    ap.add_argument("--out", required=True, help="QA Suite results.json to create or update")
    ap.add_argument("--project", "--device", "--env", dest="project", default="default",
                    help="label of the environment of this run, e.g. 'chrome', 'Pixel 8 / Android 16', 'staging'")
    ap.add_argument("--source", default="junit", help="value of the 'source' field (e.g. surefire, pytest, cypress, maestro)")
    ap.add_argument("--run", help="run label")
    ap.add_argument("--retries", action="store_true",
                    help="a test repeated inside one report is a retry (last attempt counts, earlier failures = flaky)")
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    a = ap.parse_args()

    files, missing = expand(a.reports)
    for m in missing:
        print(f"error: no report matches {m}", file=sys.stderr)
    if missing or not files:
        return 2
    attempts, skipped_files, read = [], [], []
    for f, explicit in files:
        try:
            root, cleaned = load_xml(f)
        except (OSError, ET.ParseError) as e:
            print(f"error: cannot read {f}: {e}", file=sys.stderr)
            return 2
        kind = local(root.tag)
        if kind in ("testsuites", "testsuite"):
            attempts += junit_attempts(root, str(f))
        elif kind == "robot":
            attempts += robot_attempts(root, str(f))
        else:
            why = OTHER_FORMATS.get(kind, f"root element <{kind}> is not JUnit XML")
            if explicit:
                print(f"error: {f}: {why}", file=sys.stderr)
                return 2
            skipped_files.append(f"{f.name} ({why})")
            continue
        read.append(f)
        if cleaned:
            print(f"note: {f.name} contained characters that are not allowed in XML (e.g. ANSI colour codes); they were ignored")
    if not read:
        print("error: none of the files is a JUnit XML report", file=sys.stderr)
        return 2

    found, untagged, n_tests = collect(attempts, a.retries)
    out = Path(a.out)
    try:
        doc = json.loads(out.read_text(encoding="utf-8-sig")) if out.exists() else {}
    except (OSError, ValueError) as e:
        print(f"error: cannot read {out}: {e}", file=sys.stderr)
        return 2
    merged = dict(doc.get("results", {}))
    counts: dict[str, int] = {}
    for tid, e in sorted(found.items()):
        old = merged.get(tid, {})
        projects = dict(old.get("projects", {})) if old.get("source") == a.source else {}
        projects[a.project] = e["kind"]
        kinds = set(projects.values())
        status = rollup(kinds)
        entry = {"status": status, "source": a.source, "projects": projects, "duration_ms": round(e["seconds"] * 1000)}
        if "flaky" in kinds:
            entry["flaky"] = True
        if e["errors"]:
            entry["errors"] = e["errors"][:3]
        elif status == "failed" and old.get("errors"):
            entry["errors"] = old["errors"]
        if "known-defect" in kinds:
            entry["note"] = KNOWN_DEFECT_NOTE
        elif status == "skipped" and e["notes"]:
            entry["note"] = "; ".join(e["notes"][:2])[:300]    # skip reasons
        if old.get("defects"):
            entry["defects"] = old["defects"]
        merged[tid] = entry
        counts[rollup({e["kind"]})] = counts.get(rollup({e["kind"]}), 0) + 1
    doc = {"run": a.run or doc.get("run") or f"{a.source} run", "results": dict(sorted(merged.items()))}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    names = read[0].name if len(read) == 1 else f"{len(read)} reports"
    print(f"wrote {out}: {len(found)} test cases from {names} ({n_tests} tests) on '{a.project}' · "
          + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())))
    if skipped_files:
        print("skipped (not JUnit XML): " + "; ".join(skipped_files[:5]) + (" …" if len(skipped_files) > 5 else ""))
    if untagged:
        print(f"warning: {len(untagged)} tests carry no TC-### in name, properties, tags, classname or suite "
              "(not traceable): " + "; ".join(untagged[:5]) + (" …" if len(untagged) > 5 else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
