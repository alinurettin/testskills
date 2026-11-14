#!/usr/bin/env python3
"""Generate a k6 load-test script from a performance requirement and print its workload model.

The script states the model it implements (open = arrival rate, closed = virtual users), measures the
thresholds on the steady state and on successful responses only, and writes a JSON summary that
k6_results.py turns into a verdict in qa/results.json. Nothing a workload model needs is invented:
what the spec lacks stops the run (exit 2) or is printed as a QUESTION.

Spec (JSON):
{
  "id": "DS-010", "title": "Kupon doğrulama performansı", "requirement_ids": ["REQ-006"], "test_id": "TC-027",
  "base_url": "https://staging.example.com",            # overridable with -e BASE_URL=...
  "profile": "load",                                     # smoke | load | stress | spike | soak
  "target": {"type": "arrival-rate", "rate": 50, "unit": "iterations"},
        # open model: journeys started per second. "unit": "requests" converts an HTTP requests/s figure
        # into journeys/s. Optional "pre_allocated_vus".
        # closed model: {"type": "vus", "vus": 200} = concurrent users; needs think_time_s or pacing_s.
        # Optional "throughput_per_s" (journeys/s the requirement expects) becomes a threshold.
  "duration": "10m", "ramp": "2m",                       # steady state and ramp-up
  "thresholds": {"p95_ms": 800, "p99_ms": 1500, "error_rate": 0.01, "checks_rate": 0.99},
  "auth": {"type": "bearer", "env": "K6_TOKEN"},         # one token from the environment, or
                                                         # {"type": "bearer", "data_field": "token"} per data row
  "think_time_s": 1,                                     # pause at the end of the journey; [min, max] = random
  "pacing_s": 10,                                        # closed model: one journey per VU every 10 s
  "data": {"file": "data/coupons.csv", "pick": "sequential"},   # sequential | random | unique | per-vu
  "requests": [
    {"name": "apply_coupon", "method": "POST", "path": "/api/cart/{{cart_id}}/coupon", "json": {"code": "{{code}}"},
     "expect_status": 200, "thresholds": {"p95_ms": 800}, "think_time_s": [1, 3]}
  ],
  "mix": [{"name": "browse", "weight": 80, "requests": [...]}, {"name": "buy", "weight": 20, "requests": [...]}]
}
"requests" is one journey (run in order per iteration). "mix" replaces it with several weighted journeys
(the operational profile); each becomes its own scenario. {{field}} in a path or JSON string is filled from
the data row ({{amount:number}} sends a number). "expect_status" may be 4xx or a list: an expected status is
not an error. Per-request thresholds override the global ones. "peak_factor" changes the overload level of
stress (default 2) and spike (default 5). "assumptions": ["..."] are copied into the script header.

Usage:
  python generate_k6.py qa/design/DS-010-coupon-perf.json --out perf/DS-010.k6.js
  k6 run -e BASE_URL=https://staging.example.com perf/DS-010.k6.js      # exit 99 = a threshold failed
  python k6_results.py perf/DS-010-summary.json --out qa/results.json    # verdict under the test case
Exit codes: 0 written, 1 open questions with --strict, 2 unreadable spec or a missing workload-model input.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

DUR = re.compile(r"^(\d+)(s|m|h)$")
NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,59}$")
PLACEHOLDER = re.compile(r"\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*(?::\s*(number|string))?\s*\}\}")
PROFILES = ("smoke", "load", "stress", "spike", "soak")
PICKS = ("sequential", "random", "unique", "per-vu")
OVERLOAD_PROFILES = ("stress", "spike")
ALLOWANCE_S = 1.0     # VU sizing only: time allowed for a request that has no latency threshold
VU_BUFFER = 1.2       # VU sizing only: head-room over rate x iteration time
RESERVED = {"default", "options", "handleSummary", "setup", "teardown", "http", "check", "sleep", "exec",
            "Counter", "Rate", "Trend", "SharedArray", "BASE_URL", "TOKEN", "QA", "PHASES", "M", "phaseNow",
            "think", "record", "parseRows", "function", "return", "const", "let", "var", "class", "new",
            "delete", "import", "export", "if", "else", "for", "while", "do", "switch", "case", "break",
            "continue", "try", "catch", "finally", "throw", "typeof", "void", "in", "of", "this", "null",
            "true", "false", "await", "async", "yield", "with", "enum", "super", "row", "res", "phase", "started"}


class SpecError(ValueError):
    """One or more inputs a workload model needs are missing or malformed."""

    def __init__(self, problems: list[str]):
        super().__init__("; ".join(problems))
        self.problems = problems


def seconds(d: str) -> int:
    m = DUR.match(str(d))
    if not m:
        raise ValueError(f"duration must look like 30s, 10m or 2h: {d!r}")
    return int(m.group(1)) * {"s": 1, "m": 60, "h": 3600}[m.group(2)]


def fmt(sec: int) -> str:
    return f"{sec // 3600}h" if sec % 3600 == 0 and sec >= 3600 else f"{sec // 60}m" if sec % 60 == 0 else f"{sec}s"


def num(x: float) -> str:
    """Deterministic short number: 50, 12.5, 0.33."""
    return f"{round(x, 2):g}"


def js(v) -> str:
    return json.dumps(v, ensure_ascii=False)


def think_pair(v, where: str, problems: list[str]) -> tuple[float, float] | None:
    """think_time_s: a number or [min, max] -> (min, max); None when absent."""
    if v is None:
        return None
    pair = v if isinstance(v, list) else [v, v]
    if (len(pair) != 2 or any(isinstance(x, bool) or not isinstance(x, (int, float)) for x in pair)
            or pair[0] < 0 or pair[1] < pair[0]):
        problems.append(f"{where}: think_time_s must be a number of seconds >= 0 or [min, max]")
        return None
    return float(pair[0]), float(pair[1])


def plan(profile: str, duration: int, ramp: int, factor: float, smoke_level: float) -> tuple[float, list[tuple[int, float, str]]]:
    """(start level, [(seconds, level at the end of the stage, phase)]) with levels as multiples of the target."""
    if profile == "smoke":
        return smoke_level, [(60, smoke_level, "steady")]
    if profile == "load":
        return 0.0, [(ramp, 1.0, "ramp_up"), (duration, 1.0, "steady"), (max(ramp // 2, 30), 0.0, "ramp_down")]
    if profile == "soak":
        return 0.0, [(ramp, 1.0, "ramp_up"), (max(duration, 3600), 1.0, "steady"), (ramp, 0.0, "ramp_down")]
    if profile == "stress":
        hold = max(duration // 4, 60)
        mid = round((1.0 + factor) / 2, 2)
        return 0.0, [(ramp, 0.5, "ramp_up"), (hold, 0.5, "warm_up"), (ramp, 1.0, "ramp_up"), (hold, 1.0, "baseline"),
                     (ramp, mid, "overload"), (hold, mid, "overload"), (ramp, factor, "overload"), (hold, factor, "overload"),
                     (ramp, 1.0, "settle"), (hold, 1.0, "recovery"), (ramp, 0.0, "ramp_down")]
    if profile == "spike":
        hold = max(duration // 3, 60)
        return 0.0, [(ramp, 1.0, "ramp_up"), (hold, 1.0, "baseline"), (10, factor, "overload"), (60, factor, "overload"),
                     (10, 1.0, "settle"), (hold, 1.0, "recovery"), (30, 0.0, "ramp_down")]
    raise ValueError(f"unknown profile {profile!r}")


def apportion(total: int, weights: list[float]) -> list[int]:
    """Largest-remainder split of `total` VUs over the journeys (each journey gets at least one)."""
    s = sum(weights)
    raw = [total * w / s for w in weights]
    out = [max(1, math.floor(x)) for x in raw]
    order = sorted(range(len(raw)), key=lambda i: (-(raw[i] - math.floor(raw[i])), i))
    i = 0
    while sum(out) < total:
        out[order[i % len(order)]] += 1
        i += 1
    return out


def time_unit(rate: float) -> tuple[int, int, bool]:
    """(timeUnit seconds, integer rate per timeUnit, exact?) for a possibly fractional rate per second."""
    for tu in (1, 10, 60):
        v = rate * tu
        if v >= 1 and abs(v - round(v)) < 1e-6:
            return tu, int(round(v)), True
    return 60, max(1, int(round(rate * 60))), False


def placeholders(value) -> set[str]:
    if isinstance(value, str):
        return {m.group(1) for m in PLACEHOLDER.finditer(value)}
    if isinstance(value, dict):
        return set().union(*[placeholders(v) for v in value.values()]) if value else set()
    if isinstance(value, list):
        return set().union(*[placeholders(v) for v in value]) if value else set()
    return set()


def template(text: str, encode: bool = False) -> str:
    """'/cart/{{id}}' -> JS template-literal body '/cart/${row.id}' (literal parts escaped)."""
    out, pos = [], 0
    for m in PLACEHOLDER.finditer(text):
        out.append(text[pos:m.start()].replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${"))
        ref = f"row[{js(m.group(1))}]"
        out.append("${" + (f"encodeURIComponent({ref})" if encode else ref) + "}")
        pos = m.end()
    out.append(text[pos:].replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${"))
    return "".join(out)


def js_value(value) -> str:
    """JSON value -> JS expression; {{field}} placeholders read the data row."""
    if isinstance(value, str):
        whole = PLACEHOLDER.fullmatch(value)
        if whole:
            ref = f"row[{js(whole.group(1))}]"
            return f"Number({ref})" if whole.group(2) == "number" else ref
        return f"`{template(value)}`" if PLACEHOLDER.search(value) else js(value)
    if isinstance(value, dict):
        return "{ " + ", ".join(f"{js(k)}: {js_value(v)}" for k, v in value.items()) + " }" if value else "{}"
    if isinstance(value, list):
        return "[" + ", ".join(js_value(v) for v in value) + "]"
    return js(value)


def normalise(spec: dict) -> dict:
    """Validate the spec and derive the workload model. Raises SpecError listing every missing input."""
    problems: list[str] = []
    questions: list[str] = []
    notes: list[str] = []
    if not isinstance(spec, dict):
        raise SpecError(["the spec must be a JSON object"])
    profile = spec.get("profile", "load")
    if profile not in PROFILES:
        problems.append(f"profile must be one of {', '.join(PROFILES)}: {profile!r}")
        profile = "load"

    # ---- journeys (the operational profile)
    raw_mix = spec.get("mix")
    if raw_mix and spec.get("requests"):
        problems.append("give either 'requests' (one journey) or 'mix' (weighted journeys), not both")
    if raw_mix:
        if not isinstance(raw_mix, list) or not all(isinstance(j, dict) for j in raw_mix):
            raise SpecError(["mix must be a list of {name, weight, requests}"])
        journeys_in = raw_mix
    else:
        journeys_in = [{"name": re.sub(r"[^A-Za-z0-9_]", "_", str(profile)), "weight": 1, "requests": spec.get("requests")}]
    global_th = spec.get("thresholds") or {}
    if not isinstance(global_th, dict):
        problems.append("thresholds must be an object")
        global_th = {}
    spec_think = think_pair(spec.get("think_time_s"), "spec", problems)
    journeys, seen = [], set()
    for j in journeys_in:
        jname = str(j.get("name", ""))
        if raw_mix and (not NAME.match(jname) or jname in RESERVED):
            problems.append(f"mix: journey name {jname!r} must be an identifier (letters, digits, _) and not a reserved word")
        if jname in seen:
            problems.append(f"duplicate name {jname!r}")
        seen.add(jname)
        w = j.get("weight", 1)
        if isinstance(w, bool) or not isinstance(w, (int, float)) or w <= 0:
            problems.append(f"journey {jname}: weight must be a number > 0")
            w = 1
        reqs_in = j.get("requests")
        if not isinstance(reqs_in, list) or not reqs_in:
            problems.append(f"journey {jname}: needs at least one request" if raw_mix else "spec needs at least one request")
            reqs_in = []
        reqs = []
        for r in reqs_in:
            if not isinstance(r, dict):
                problems.append(f"journey {jname}: each request must be an object")
                continue
            rname = str(r.get("name", ""))
            if not NAME.match(rname):
                problems.append(f"request name {rname!r} must be an identifier (letters, digits, _): it names the metric")
            if rname in seen:
                problems.append(f"duplicate name {rname!r}")
            seen.add(rname)
            if not str(r.get("path", "")).startswith("/"):
                problems.append(f"request {rname}: path must start with '/'")
            es = r.get("expect_status", 200)
            statuses = es if isinstance(es, list) else [es]
            if not statuses or any(isinstance(s, bool) or not isinstance(s, int) or not 100 <= s <= 599 for s in statuses):
                problems.append(f"request {rname}: expect_status must be an HTTP status or a list of them")
                statuses = [200]
            th = {**global_th, **(r.get("thresholds") or {})}
            for k in ("p95_ms", "p99_ms"):
                if th.get(k) is not None and (isinstance(th[k], bool) or not isinstance(th[k], (int, float)) or th[k] <= 0):
                    problems.append(f"request {rname}: {k} must be a number of milliseconds > 0")
                    th[k] = None
            reqs.append({"name": rname, "method": str(r.get("method", "GET")).upper(), "path": str(r.get("path", "/")),
                         "json": r.get("json"), "has_json": "json" in r, "statuses": statuses,
                         "p95": th.get("p95_ms"), "p99": th.get("p99_ms"),
                         "think": think_pair(r.get("think_time_s"), f"request {rname}", problems)})
        jthink = think_pair(j.get("think_time_s"), f"journey {jname}", problems) if "think_time_s" in j else spec_think
        journeys.append({"name": jname, "weight": float(w), "requests": reqs, "end_think": jthink,
                         "data": j.get("data", spec.get("data"))})

    # ---- pass/fail criteria
    for k in ("error_rate", "checks_rate"):
        v = global_th.get(k)
        if v is not None and (isinstance(v, bool) or not isinstance(v, (int, float)) or not 0 <= v <= 1):
            problems.append(f"thresholds.{k} must be a fraction between 0 and 1 (0.01 = 1%)")
    has_latency = any(r["p95"] is not None or r["p99"] is not None for j in journeys for r in j["requests"])
    if global_th.get("error_rate") is None:
        problems.append("thresholds.error_rate is missing: response times are measured on successful responses, so "
                        "without an error budget a run in which requests fail would still pass. Ask for the acceptable "
                        "error rate (a proposed value is an assumption; list it under 'assumptions')")
    if not has_latency:
        questions.append("No response-time threshold (p95_ms / p99_ms): the run is judged on the error rate only. "
                         "What response time does the requirement expect, at which percentile?")

    # ---- load target: arrival rate (open) is not the same thing as virtual users (closed)
    target = spec.get("target")
    model, rate, vus, unit = "", 0.0, 0, ""
    if not isinstance(target, dict) or target.get("type") not in ("arrival-rate", "vus"):
        problems.append("target is missing: give {\"type\": \"arrival-rate\", \"rate\": <journeys per second>} (open model) "
                        "or {\"type\": \"vus\", \"vus\": <concurrent users>} (closed model). Ask what the load level in the "
                        "requirement counts: requests per second, journeys per second or concurrent users")
        target = {}
    elif target["type"] == "arrival-rate":
        model = "open"
        rate = target.get("rate")
        if isinstance(rate, bool) or not isinstance(rate, (int, float)) or rate <= 0:
            problems.append("target.rate must be a number > 0 (per second)")
            rate = 1.0
        unit = target.get("unit", "")
        if unit not in ("", "iterations", "requests"):
            problems.append("target.unit must be 'iterations' (journeys per second) or 'requests' (HTTP requests per second)")
            unit = ""
    else:
        model = "closed"
        vus = target.get("vus")
        if isinstance(vus, bool) or not isinstance(vus, int) or vus < 1:
            problems.append("target.vus must be a whole number >= 1")
            vus = 1
        if vus < len(journeys):
            problems.append(f"target.vus ({vus}) is smaller than the number of journeys in the mix ({len(journeys)})")
    pacing = spec.get("pacing_s")
    if pacing is not None and (isinstance(pacing, bool) or not isinstance(pacing, (int, float)) or pacing <= 0):
        problems.append("pacing_s must be a number of seconds > 0")
        pacing = None
    if model == "closed":
        for j in journeys:
            if pacing is None and j["end_think"] is None and not any(r["think"] is not None for r in j["requests"]):
                problems.append(f"closed model (target.type vus), journey {j['name']}: think_time_s or pacing_s is missing. "
                                "Concurrent users without think time or pacing do not define a load: throughput = users / "
                                "(response time + think time). Ask how often one user repeats the journey (0 is a valid, "
                                "explicit answer for a back-to-back client)")
    elif pacing is not None:
        notes.append("pacing_s is ignored in the open model: the arrival rate already fixes when journeys start")
        pacing = None

    # ---- durations: stated inputs, or visible assumptions
    try:
        duration = seconds(spec.get("duration", "10m"))
        ramp = seconds(spec.get("ramp", "2m"))
    except ValueError as e:
        problems.append(str(e))
        duration, ramp = 600, 120
    if profile != "smoke":
        for key, default in (("duration", "10m"), ("ramp", "2m")):
            if key not in spec:
                questions.append(f"'{key}' is not in the spec: {default} is ASSUMED. How long does the "
                                 f"{'peak last' if key == 'duration' else 'load take to build up'} in the requirement or the plan?")
    factor = spec.get("peak_factor", 2 if profile == "stress" else 5)
    if isinstance(factor, bool) or not isinstance(factor, (int, float)) or factor <= 1:
        problems.append("peak_factor must be a number > 1")
        factor = 2

    # ---- test data and credentials
    auth = spec.get("auth") or {}
    if auth and auth.get("type") != "bearer":
        problems.append("auth.type: only 'bearer' is supported")
    if auth.get("env") and not NAME.match(str(auth["env"])):
        problems.append("auth.env must be an environment variable name")
    for j in journeys:
        d = j["data"]
        used = set()
        for r in j["requests"]:
            used |= placeholders(r["path"]) | placeholders(r["json"])
        if auth.get("data_field"):
            used.add(str(auth["data_field"]))
        j["fields"] = sorted(used)
        if d is None:
            if used:
                problems.append(f"journey {j['name']}: {{{{{', '.join(sorted(used))}}}}} needs 'data': {{\"file\": ..., \"pick\": ...}}")
            continue
        if not isinstance(d, dict) or not isinstance(d.get("file"), str) or not d["file"]:
            problems.append(f"journey {j['name']}: data must be {{\"file\": \"rows.csv\", \"pick\": \"sequential\"}}")
            j["data"] = None
            continue
        if d.get("pick", "sequential") not in PICKS:
            problems.append(f"journey {j['name']}: data.pick must be one of {', '.join(PICKS)}")
    if problems:
        raise SpecError(problems)

    # ---- derived numbers
    start_level, stages = plan(profile, duration, ramp, float(factor), 1.0)
    weights = [j["weight"] for j in journeys]
    wsum = sum(weights)
    if model == "open":
        per_iter = sum(j["weight"] / wsum * len(j["requests"]) for j in journeys)
        iter_rate = rate / per_iter if unit == "requests" else float(rate)
        if unit == "" and abs(per_iter - 1.0) > 1e-9:
            questions.append(f"target.rate {num(rate)}/s is read as journeys per second, which is {num(iter_rate * per_iter)} "
                             f"HTTP requests/s here. Does the requirement count journeys or requests? Set target.unit")
        smoke_level = min(iter_rate, 2.0) / iter_rate
    else:
        iter_rate = 0.0
        split = apportion(int(vus), weights)
        smoke_level = min(int(vus), 2) / int(vus)
    if profile == "smoke":
        start_level, stages = plan(profile, duration, ramp, float(factor), smoke_level)
    peak_level = max([start_level] + [lv for _, lv, _ in stages])
    for i, j in enumerate(journeys):
        thinks = [r["think"] for r in j["requests"] if r["think"]]
        end = j["end_think"] if model == "closed" else None      # open model: a trailing sleep only holds a VU
        j["emit_end_think"] = end
        j["think_mean"] = sum((a + b) / 2 for a, b in thinks) + ((end[0] + end[1]) / 2 if end else 0.0)
        j["allowance"] = sum((r["p99"] or r["p95"] or ALLOWANCE_S * 1000) / 1000 for r in j["requests"]) + j["think_mean"]
        j["share"] = j["weight"] / wsum
        if model == "open":
            j["rate"] = iter_rate * j["share"]
            tu, per_tu, exact = time_unit(j["rate"])
            j["time_unit"], j["rate_per_tu"] = tu, per_tu
            if not exact:
                notes.append(f"journey {j['name']}: {num(j['rate'])} journeys/s is rounded to {per_tu} per minute")
            j["levels"] = [max(1, round(per_tu * lv)) if lv > 0 else 0 for _, lv, _ in stages]
            j["start"] = max(1, round(per_tu * start_level)) if start_level > 0 else 0
            sized = max(1, math.ceil(j["rate"] * peak_level * j["allowance"] * VU_BUFFER))
            j["vus"] = int(target["pre_allocated_vus"]) if isinstance(target.get("pre_allocated_vus"), int) and len(journeys) == 1 else sized
            prev, total = j["start"], 0.0
            for (sec, _, _), lv in zip(stages, j["levels"]):
                total += (prev + lv) / 2 * sec / tu
                prev = lv
            j["planned_iterations"] = int(round(total))
            if j["end_think"] is not None and j["end_think"][1] > 0:
                notes.append(f"journey {j['name']}: the think time at the end of the journey is not emitted in the open model "
                             "(the executor schedules the next journey; a trailing sleep would only hold a VU)")
        else:
            j["vus"] = split[i]
            j["levels"] = [max(1, round(split[i] * lv)) if lv > 0 else 0 for _, lv, _ in stages]
            j["start"] = max(1, round(split[i] * start_level)) if start_level > 0 else 0
            cycle_fast = max(pacing or 0.0, j["think_mean"])
            cycle_slow = max(pacing or 0.0, j["allowance"])
            j["max_rate"] = split[i] / cycle_fast if cycle_fast > 0 else None    # responses take no time
            j["min_rate"] = split[i] / cycle_slow                                 # every response at its threshold
            if j["think_mean"] == 0 and pacing is None:
                notes.append(f"journey {j['name']}: think time 0 = every VU fires back-to-back; this measures maximum "
                             "throughput of a few clients, not the behaviour of human users")
        if any((r["think"] and r["think"][0] == r["think"][1] and r["think"][0] > 0) for r in j["requests"]) or \
                (end and end[0] == end[1] and end[0] > 0 and model == "closed"):
            notes.append(f"journey {j['name']}: a constant think time makes the VUs move in lock-step; "
                         "give a range, for example [1, 3]")
        if j["data"] is None and any(r["has_json"] or r["method"] != "GET" for r in j["requests"]):
            questions.append(f"Journey {j['name']} sends the same payload in every iteration (no 'data'): caches and row "
                             "locks will distort the result. Which distinct test data (users, codes, IDs) may the test use?")
    shared = [j["name"] for j in journeys if j["data"] and j["data"].get("pick") == "unique"
              and sum(1 for o in journeys if o["data"] and o["data"]["file"] == j["data"]["file"]) > 1]
    if shared:
        notes.append(f"journeys {', '.join(shared)} read the same data file: 'unique' is unique within one journey, "
                     "not across journeys; give each journey its own file when a row must never be reused")
    if auth.get("env") and not auth.get("data_field"):
        questions.append(f"All virtual users share one token ({auth['env']}): per-user caches, rate limits and locks are "
                         "not exercised. Can a file of test-account tokens be provided (auth.data_field + data)?")
    if profile == "soak" and duration < 3600:
        notes.append(f"soak: the steady state is extended to 1h (duration given: {fmt(duration)})")
    if profile in OVERLOAD_PROFILES:
        notes.append(f"{profile}: the overload level is {num(float(factor))}x the target (peak_factor; a convention unless the "
                     "requirement states it). Thresholds are evaluated before the overload (baseline) and after it "
                     "(recovery), not during it")
    if profile == "smoke":
        notes.append("smoke checks that the script and the environment work; it does NOT show that the requirement is met "
                     "(k6_results.py records a passed smoke run as not-run)")
    verdict = ["baseline", "recovery"] if profile in OVERLOAD_PROFILES else ["steady"]
    measured = ["baseline", "overload", "recovery"] if profile in OVERLOAD_PROFILES else ["steady"]
    phases, t = [], 0
    for sec, lv, ph in stages:
        if phases and phases[-1]["name"] == ph:
            phases[-1]["end_s"] = t + sec
        else:
            phases.append({"name": ph, "start_s": t, "end_s": t + sec})
        t += sec
    throughput = target.get("throughput_per_s") if model == "closed" else None
    if throughput is not None and (isinstance(throughput, bool) or not isinstance(throughput, (int, float)) or throughput <= 0):
        raise SpecError(["target.throughput_per_s must be a number > 0 (journeys per second)"])
    tol = target.get("tolerance", 0.05)
    if isinstance(tol, bool) or not isinstance(tol, (int, float)) or not 0 <= tol < 1:
        raise SpecError(["target.tolerance must be a fraction between 0 and 1"])
    return {"profile": profile, "model": model, "journeys": journeys, "stages": stages, "phases": phases, "total_s": t,
            "verdict": verdict, "measured": measured, "rate": iter_rate, "vus": int(vus or 0), "unit": unit,
            "given_rate": rate, "pacing": pacing, "th": global_th, "auth": auth, "questions": questions, "notes": notes,
            "duration_given": "duration" in spec, "ramp_given": "ramp" in spec, "throughput": throughput, "tolerance": tol,
            "factor": float(factor), "mixed": bool(raw_mix), "assumptions": [str(x) for x in spec.get("assumptions") or []],
            "has_latency": has_latency}


def worksheet(spec: dict, m: dict) -> list[str]:
    """The workload model in plain words: what the script will apply and how the verdict is reached."""
    out = []
    if m["model"] == "open":
        src = {"requests": f"{num(m['given_rate'])} HTTP requests/s converted", "iterations": "as given",
               "": "target.unit not given, read as journeys/s"}[m["unit"]]
        out.append(f"model: OPEN (arrival rate) - {num(m['rate'])} journeys/s start at the target, however slowly the "
                   f"system answers ({src})")
    else:
        out.append(f"model: CLOSED ({m['vus']} virtual users) - a user starts the next journey only after the previous one "
                   "ends, so the load FALLS when the system slows down; throughput is an outcome, not an input")
    for j in m["journeys"]:
        names = ", ".join(r["name"] for r in j["requests"])
        if m["model"] == "open":
            per_req = "; ".join(f"{r['name']} {num(j['rate'])} req/s" for r in j["requests"])
            out.append(f"journey {j['name']} ({num(j['share'] * 100)}%): {num(j['rate'])} journeys/s -> {per_req}; "
                       f"{j['planned_iterations']} journeys planned; {j['vus']} VUs pre-allocated = rate at peak x "
                       f"{num(j['allowance'])} s journey allowance x {VU_BUFFER} (sizing estimate, not part of the model)")
        else:
            hi = f"{num(j['max_rate'])}" if j["max_rate"] is not None else "unbounded"
            out.append(f"journey {j['name']} ({num(j['share'] * 100)}%): {j['vus']} VUs, requests {names}; think time "
                       f"{num(j['think_mean'])} s per journey" + (f", pacing {num(m['pacing'])} s" if m["pacing"] else "")
                       + f" -> between {num(j['min_rate'])} (every response at its threshold) and {hi} journeys/s "
                       "(instant responses)")
        if j["data"]:
            pick = j["data"].get("pick", "sequential")
            need = {"unique": f"at least {j.get('planned_iterations', 'one per journey')} rows (one per journey, never reused)",
                    "per-vu": f"at least {j['vus']} rows (one per VU)"}.get(pick, "enough distinct rows to defeat caching")
            out.append(f"journey {j['name']} data: {j['data']['file']} ({pick}; fields {', '.join(j['fields']) or '-'}); {need}")
    if m["model"] == "open":
        total_req = sum(j["rate"] * len(j["requests"]) for j in m["journeys"])
        out.append(f"total at target: {num(m['rate'])} journeys/s = {num(total_req)} HTTP requests/s")
    out.append("phases: " + ", ".join(f"{p['name']} {p['start_s']}-{p['end_s']}s" + (" (verdict)" if p["name"] in m["verdict"] else "")
                                       for p in m["phases"]) + f"; planned run time {fmt(m['total_s'])}")
    crit = ["response times of successful responses" if m["has_latency"] else "no response-time threshold",
            f"error rate < {m['th']['error_rate']}"]
    if m["th"].get("checks_rate") is not None:
        crit.append(f"checks > {m['th']['checks_rate']}")
    if m["model"] == "open" and m["profile"] not in OVERLOAD_PROFILES:
        crit.append("dropped_iterations == 0 (the target rate was really applied)")
    if m["throughput"]:
        crit.append(f"at least {num(m['throughput'])} journeys/s achieved (tolerance {num(m['tolerance'] * 100)}%)")
    out.append(f"verdict: thresholds on the {' and '.join(m['verdict'])} phase only: " + "; ".join(crit))
    out += [f"note: {n}" for n in m["notes"]]
    out += [f"ASSUMPTION (from the spec): {a}" for a in m["assumptions"]]
    out += [f"QUESTION: {q}" for q in m["questions"]]
    return out


def build(spec: dict, model: dict | None = None) -> str:
    m = model or normalise(spec)
    th, profile, auth = m["th"], m["profile"], m["auth"]
    reqs = ",".join(spec.get("requirement_ids", []))
    spec_id = str(spec.get("id", "perf"))
    all_reqs = [r for j in m["journeys"] for r in j["requests"]]
    uses_data = any(j["data"] for j in m["journeys"])
    summary_default = re.sub(r"[^A-Za-z0-9_.-]", "_", spec_id) + "-summary.json"

    # ---- thresholds (custom metrics per measured phase: no tag-combination syntax to get wrong)
    thresholds: dict[str, list[str]] = {}
    for ph in m["verdict"]:
        for r in all_reqs:
            lim = ([f"p(95)<{r['p95']}"] if r["p95"] is not None else []) + ([f"p(99)<{r['p99']}"] if r["p99"] is not None else [])
            if lim:
                thresholds[f"qa_{ph}_ms_{r['name']}"] = lim
        thresholds[f"qa_{ph}_failed"] = [f"rate<{th['error_rate']}"]
        if th.get("checks_rate") is not None:
            thresholds[f"checks{{phase:{ph}}}"] = [f"rate>{th['checks_rate']}"]
        floor = "count>0"
        if m["throughput"] and ph in ("steady", "baseline"):
            sec = sum(p["end_s"] - p["start_s"] for p in m["phases"] if p["name"] == ph)
            floor = f"count>={math.floor(m['throughput'] * sec * (1 - m['tolerance']))}"
        thresholds[f"qa_{ph}_iterations"] = [floor]
    if m["model"] == "open" and profile not in OVERLOAD_PROFILES:
        thresholds["dropped_iterations"] = ["count==0"]
    th_js = ",\n".join(f"    {js(k)}: {js(v)}" for k, v in thresholds.items())

    qa = {"generator": "qa-suite generate_k6.py", "schema": 1, "spec_id": spec_id, "title": spec.get("title", ""),
          "test_id": spec.get("test_id", ""), "requirement_ids": spec.get("requirement_ids", []), "profile": profile,
          "model": m["model"], "verdict_phases": m["verdict"], "measured_phases": m["measured"], "phases": m["phases"],
          "planned_duration_s": m["total_s"],
          "target": ({"journeys_per_s": round(m["rate"], 4)} if m["model"] == "open" else {"vus": m["vus"]}),
          "journeys": [{"name": j["name"], "share": round(j["share"], 4), "requests": [r["name"] for r in j["requests"]],
                        **({"journeys_per_s": round(j["rate"], 4), "planned_iterations": j["planned_iterations"]}
                           if m["model"] == "open" else {"vus": j["vus"]})} for j in m["journeys"]],
          "open_questions": len(m["questions"])}

    lines = [f"// Generated by QA Suite (generate_k6.py) from {spec_id} {spec.get('title', '')}".rstrip(),
             f"// Requirements: {reqs or '-'} · test case: {spec.get('test_id') or '-'} · profile: {profile}",
             "// Run: k6 run -e BASE_URL=<test environment> <this file>   (exit code 99 = a threshold failed)",
             "// Only run against environments you own and are allowed to load-test; never against production without approval.",
             "//", "// Workload model (derived from the spec; review it before running):"]
    lines += [f"//   {w}" for w in worksheet(spec, m)]
    lines += ["//", "import http from 'k6/http';", "import { check, sleep } from 'k6';", "import exec from 'k6/execution';",
              "import { Counter, Rate, Trend } from 'k6/metrics';"]
    if uses_data:
        lines.append("import { SharedArray } from 'k6/data';")
    lines += ["", f"const BASE_URL = __ENV.BASE_URL || {js(spec.get('base_url', 'http://localhost:3000'))};"]
    if auth.get("env") and not auth.get("data_field"):
        lines.append(f"const TOKEN = __ENV.{auth['env']};")
    lines += [f"const QA = {js(qa)};", "",
              "// Phase of the run by elapsed time. Only the verdict phases feed the thresholds: ramps are not the steady state.",
              "const PHASES = [" + ", ".join(f"[{p['end_s']}, {js(p['name'])}]" for p in m["phases"]) + "];",
              "function phaseNow() {",
              "  const t = (Date.now() - exec.scenario.startTime) / 1000;",
              "  for (const [end, name] of PHASES) if (t < end) return name;",
              "  return PHASES[PHASES.length - 1][1];",
              "}", "",
              "// Per measured phase: response time of successful responses per request, error rate, completed journeys.",
              "const M = {};",
              f"for (const p of {js(m['measured'])}) {{",
              "  M[p] = { failed: new Rate(`qa_${p}_failed`), iterations: new Counter(`qa_${p}_iterations`), ms: {} };",
              f"  for (const n of {js([r['name'] for r in all_reqs])}) M[p].ms[n] = new Trend(`qa_${{p}}_ms_${{n}}`, true);",
              "}",
              "// An expected status (also an expected 4xx) is a success: it is not counted in http_req_failed.",
              "const EXPECTED = {"]
    for r in all_reqs:
        arg = str(r["statuses"][0]) if len(r["statuses"]) == 1 else ", ".join(str(s) for s in r["statuses"])
        lines.append(f"  {r['name']}: http.expectedStatuses({arg}),")
    lines += ["};",
              "function record(name, res, phase, statuses) {",
              "  const ok = check(res, { [`${name} status ${statuses.join('|')}`]: (r) => statuses.includes(r.status) }, { phase });",
              "  const m = M[phase];",
              "  if (m) {",
              "    m.failed.add(!ok);",
              "    if (ok) m.ms[name].add(res.timings.duration);",
              "  }",
              "  return ok;",
              "}",
              "function think(min, max) {",
              "  sleep(min + Math.random() * (max - min));",
              "}"]
    if uses_data:
        lines += ["// Test data: CSV with a header row (no quoted commas) or a JSON array of objects, relative to this script.",
                  "function parseRows(file) {",
                  "  const text = open(file).replace(/^\\uFEFF/, '');",
                  "  if (file.endsWith('.json')) return JSON.parse(text);",
                  "  const rows = text.split(/\\r?\\n/).filter((l) => l.trim() !== '');",
                  "  const head = rows[0].split(',').map((h) => h.trim());",
                  "  return rows.slice(1).map((l) => {",
                  "    const cells = l.split(',');",
                  "    const o = {};",
                  "    head.forEach((h, i) => { o[h] = (cells[i] || '').trim(); });",
                  "    return o;",
                  "  });",
                  "}"]
        for j in m["journeys"]:
            if j["data"]:
                lines.append(f"const ROWS_{j['name']} = new SharedArray({js('rows_' + j['name'])}, () => parseRows({js(j['data']['file'])}));")
    lines += ["", "export const options = {",
              f"  tags: {{ testid: {js(spec_id)}, requirements: {js(reqs)} }},",
              "  // p(99) and count are not in k6's default summary; k6_results.py needs both.",
              "  summaryTrendStats: ['count', 'avg', 'min', 'med', 'max', 'p(90)', 'p(95)', 'p(99)'],",
              "  scenarios: {"]
    for j in m["journeys"]:
        stage_js = ",\n".join(f"        {{ duration: {js(fmt(sec))}, target: {lv} }}" for (sec, _, _), lv in zip(m["stages"], j["levels"]))
        lines.append(f"    {j['name']}: {{")
        if m["model"] == "open":
            lines += ["      executor: 'ramping-arrival-rate',", f"      startRate: {j['start']},",
                      f"      timeUnit: {js(fmt(j['time_unit']))},", f"      preAllocatedVUs: {j['vus']},"]
        else:
            lines += ["      executor: 'ramping-vus',", f"      startVUs: {j['start']},"]
        if m["mixed"]:
            lines.append(f"      exec: {js(j['name'])},")
        lines += ["      stages: [", stage_js, "      ],", "    },"]
    lines += ["  },", "  thresholds: {", th_js, "  },", "};"]

    for j in m["journeys"]:
        lines += ["", f"export function {j['name']}() {{" if m["mixed"] else "export default function () {",
                  "  const phase = phaseNow();"]
        if m["pacing"]:
            lines.append("  const started = Date.now();")
        if j["data"]:
            rows, pick = f"ROWS_{j['name']}", j["data"].get("pick", "sequential")
            if pick == "random":
                lines.append(f"  const row = {rows}[Math.floor(Math.random() * {rows}.length)];")
            elif pick == "per-vu":
                lines.append(f"  const row = {rows}[(exec.vu.idInTest - 1) % {rows}.length];")
            elif pick == "unique":
                lines += [f"  if (exec.scenario.iterationInTest >= {rows}.length) {{",
                          f"    exec.test.abort({js('test data exhausted: ' + j['data']['file'] + ' has fewer rows than journeys (pick: unique)')});",
                          "  }", f"  const row = {rows}[exec.scenario.iterationInTest];"]
            else:
                lines.append(f"  const row = {rows}[exec.scenario.iterationInTest % {rows}.length];")
        if auth.get("data_field"):
            bearer = f", Authorization: `Bearer ${{row[{js(str(auth['data_field']))}]}}`"
        elif auth.get("env"):
            bearer = ", Authorization: `Bearer ${TOKEN}`"
        else:
            bearer = ""
        headers = "{ 'Content-Type': 'application/json'" + bearer + " }"
        lines.append("  let res;")
        for r in j["requests"]:
            url = f"`${{BASE_URL}}{template(r['path'], encode=True)}`"
            params = f"{{ headers: {headers}, tags: {{ name: {js(r['name'])}, phase }}, responseCallback: EXPECTED.{r['name']} }}"
            if not r["has_json"]:
                body = "null"
            elif placeholders(r["json"]):
                body = f"JSON.stringify({js_value(r['json'])})"
            else:
                body = js(json.dumps(r["json"], ensure_ascii=False))
            call = f"http.get({url}, {params})" if r["method"] == "GET" else f"http.request({js(r['method'])}, {url}, {body}, {params})"
            lines += [f"  res = {call};", f"  record({js(r['name'])}, res, phase, {js(r['statuses'])});"]
            if r["think"] and r["think"][1] > 0:
                lines.append(f"  think({num(r['think'][0])}, {num(r['think'][1])});")
        end = j["emit_end_think"]
        if end and end[1] > 0:
            lines.append(f"  think({num(end[0])}, {num(end[1])});")
        lines.append("  if (M[phase]) M[phase].iterations.add(1);")
        if m["pacing"]:
            lines += ["  // Pacing: one journey per VU every " + num(m["pacing"]) + " s, whatever the response times were.",
                      f"  sleep(Math.max(0, {num(m['pacing'])} - (Date.now() - started) / 1000));"]
        lines.append("}")

    lines += ["",
              "// Writes the numbers for the RTM: python k6_results.py <summary file> --out qa/results.json",
              "export function handleSummary(data) {",
              "  const lines = ['', `${QA.spec_id} ${QA.profile} (${QA.model} model): thresholds`];",
              "  let failed = 0;",
              "  for (const name of Object.keys(data.metrics).sort()) {",
              "    const metric = data.metrics[name];",
              "    for (const expr of Object.keys(metric.thresholds || {})) {",
              "      const ok = metric.thresholds[expr].ok;",
              "      if (!ok) failed += 1;",
              "      lines.push(`  ${ok ? 'ok    ' : 'FAILED'} ${name}: ${expr}  ${JSON.stringify(metric.values)}`);",
              "    }",
              "  }",
              f"  const file = __ENV.K6_SUMMARY || {js(summary_default)};",
              "  lines.push(failed ? `${failed} threshold(s) FAILED` : 'all thresholds met', `summary: ${file}`, '');",
              "  return {",
              "    stdout: lines.join('\\n'),",
              "    [file]: JSON.stringify({ qa_suite: QA, state: data.state, metrics: data.metrics }, null, 1),",
              "  };",
              "}", ""]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec")
    ap.add_argument("--out")
    ap.add_argument("--strict", action="store_true", help="exit 1 when the workload model still has open questions")
    sys.stdout.reconfigure(encoding="utf-8")
    a = ap.parse_args()
    try:
        spec = json.loads(Path(a.spec).read_text(encoding="utf-8-sig"))
        model = normalise(spec)
        text = build(spec, model)
    except SpecError as e:
        print(f"error: {a.spec}: the workload model is incomplete ({len(e.problems)} item(s)); nothing was written", file=sys.stderr)
        for p in e.problems:
            print(f"  - {p}", file=sys.stderr)
        return 2
    except (OSError, ValueError, KeyError, TypeError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(text, encoding="utf-8", newline="\n")
        print(f"wrote {a.out}")
        print("workload model:")
        for w in worksheet(spec, model):
            print(f"  {w}")
    else:
        print(text)
    return 1 if a.strict and model["questions"] else 0


if __name__ == "__main__":
    sys.exit(main())
