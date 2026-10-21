#!/usr/bin/env python3
"""
Objective verifier / grader probe for trial-api2 (Anadolu Güven Sigorta API).

Usage:
    # start the server first (evaluator side):
    #   node C:\\projeler\\TestSkills\\evals\\trial-api2\\server.js   (PORT optional)
    # then:
    python grade_api2.py [BASE_URL]

Default BASE_URL = http://localhost:3000  (or env API2_BASE).

This script does NOT grade an agent's written report. It independently
reproduces each planted defect (K1..K10) and confirms each trap (T1..T4)
behaves CORRECTLY, so an evaluator can confirm the trial is sound and can
cross-check an agent's findings against ground truth.

Stdlib only (urllib). Exit code 0 if all checks behave as designed.
"""
import json
import sys
import os
import urllib.request
import urllib.error

BASE = (sys.argv[1] if len(sys.argv) > 1 else os.environ.get("API2_BASE", "http://localhost:3000")).rstrip("/")

U1 = "tok_user1_ayse"
U2 = "tok_user2_mehmet"
ADMIN = "tok_admin_root"

results = []


def req(method, path, token=None, body=None, headers=None, raw_body=None):
    url = BASE + path
    data = None
    h = {}
    if headers:
        h.update(headers)
    if token:
        h["Authorization"] = "Bearer " + token
    if raw_body is not None:
        data = raw_body.encode("utf-8")
        h.setdefault("Content-Type", "application/json")
    elif body is not None:
        data = json.dumps(body).encode("utf-8")
        h.setdefault("Content-Type", "application/json")
    r = urllib.request.Request(url, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(r) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8") or "null")
    except urllib.error.HTTPError as e:
        payload = e.read().decode("utf-8")
        try:
            payload = json.loads(payload)
        except Exception:
            pass
        return e.code, payload


def check(name, ok, detail):
    results.append((name, ok, detail))
    mark = "PASS" if ok else "FAIL"
    print(f"[{mark}] {name}: {detail}")


# --- K1: BOLA via query param (policyId bypasses ownership) ----------------
st, body = req("GET", "/claims?policyId=pol_4", token=U1)  # pol_4 belongs to u2
leaked = st == 200 and isinstance(body, dict) and any(
    c.get("ownerUserId") == "u2" for c in body.get("data", []))
check("K1 BOLA via query policyId", leaked,
      f"user1 GET /claims?policyId=pol_4 -> {st}, data owners={[c.get('ownerUserId') for c in body.get('data',[])] if isinstance(body,dict) else body}")

# --- K2: function-level authz missing on /admin/stats ----------------------
st, body = req("GET", "/admin/stats", token=U1)
check("K2 BFLA /admin/stats", st == 200 and isinstance(body, dict) and "totalPolicies" in body,
      f"user1 GET /admin/stats -> {st}, body={body}")

# --- K3: mass assignment of read-only 'status' via PATCH -------------------
st0, _ = req("PATCH", "/policies/pol_1", token=U1, body={"status": "expired"})
st1, after = req("GET", "/policies/pol_1", token=U1)
check("K3 mass assignment status", after.get("status") == "expired",
      f"PATCH status=expired -> {st0}; GET status now={after.get('status')}")
# restore
req("PATCH", "/policies/pol_1", token=U1, body={"status": "active"})

# --- K4: missing idempotency (duplicate POST creates two) ------------------
key = "idem-test-123"
st_a, a = req("POST", "/claims", token=U1,
              body={"policyId": "pol_1", "amount": 100, "description": "idem"},
              headers={"Idempotency-Key": key})
st_b, b = req("POST", "/claims", token=U1,
              body={"policyId": "pol_1", "amount": 100, "description": "idem"},
              headers={"Idempotency-Key": key})
dup = isinstance(a, dict) and isinstance(b, dict) and a.get("id") != b.get("id")
check("K4 missing idempotency", dup,
      f"two POSTs same Idempotency-Key -> ids {a.get('id') if isinstance(a,dict) else a} / {b.get('id') if isinstance(b,dict) else b}")

# --- K5: pagination meta.total wrong (returns page length) -----------------
st, body = req("GET", "/claims?page=1&pageSize=2", token=U1)
total = body.get("meta", {}).get("total") if isinstance(body, dict) else None
npage = len(body.get("data", [])) if isinstance(body, dict) else None
# u1 owns >=5 original claims; with added idem claims total is higher, but
# the planted bug is: meta.total equals the current page length (==pageSize here).
check("K5 pagination wrong total", total == npage and npage == 2,
      f"page1 pageSize2 -> returned {npage} items, meta.total={total} (should be the full count, >2)")

# --- K6: validation gap, amount minimum (>=1) not enforced -----------------
st, body = req("POST", "/claims", token=U1,
               body={"policyId": "pol_1", "amount": -500, "description": "neg"})
check("K6 amount minimum not enforced", st in (200, 201) and isinstance(body, dict) and body.get("amount") == -500,
      f"POST amount=-500 -> {st}, amount={body.get('amount') if isinstance(body,dict) else body}")

# --- K7: wrong status code on create (200 instead of 201) ------------------
st, body = req("POST", "/claims", token=U1,
               body={"policyId": "pol_1", "amount": 100, "description": "status code test"})
check("K7 wrong status code on create", st == 200,
      f"POST /claims (valid) -> HTTP {st} (contract says 201)")

# --- K8: response schema mismatch (claimNumber required but omitted) -------
st, body = req("GET", "/claims?pageSize=1", token=U1)
first = (body.get("data") or [None])[0] if isinstance(body, dict) else None
missing = isinstance(first, dict) and "claimNumber" not in first
check("K8 claimNumber missing (schema mismatch)", missing,
      f"GET /claims first item keys={sorted(first.keys()) if isinstance(first,dict) else first}")

# --- K9: error response leaks internals (stack trace) ----------------------
st, body = req("POST", "/claims", token=U1, raw_body="{bad json")
leak = isinstance(body, dict) and ("stack" in body)
has_path = leak and ("server.js" in str(body.get("stack", "")))
check("K9 error leaks internals", leak,
      f"POST malformed JSON -> {st}, has 'stack' field={leak}, has file path={has_path}")

# --- K10: business rule amount <= coverageLimit not enforced ---------------
# pol_1 coverageLimit = 50000; request amount 60000 should be 422 but succeeds.
st, body = req("POST", "/claims", token=U1,
               body={"policyId": "pol_1", "amount": 60000, "description": "over limit"})
check("K10 amount>coverageLimit not enforced", st in (200, 201) and isinstance(body, dict) and body.get("amount") == 60000,
      f"POST amount=60000 on pol_1 (limit 50000) -> {st}")

print("-" * 60)

# --- T1: GET /policies correctly scopes to owner ---------------------------
st, body = req("GET", "/policies", token=U1)
ids = sorted(p.get("id") for p in body) if isinstance(body, list) else None
only_own = isinstance(body, list) and all(p.get("ownerUserId") == "u1" for p in body)
check("T1 (trap) own-policy scoping correct", only_own and set(ids) == {"pol_1", "pol_2", "pol_5"},
      f"user1 GET /policies -> {ids} (correct: only u1's -> NOT a defect)")

# --- T2: PATCH ignores non-whitelisted ownerUserId/premium -----------------
st0, _ = req("PATCH", "/policies/pol_2", token=U1,
             body={"ownerUserId": "u2", "premium": 1})
st1, after = req("GET", "/policies/pol_2", token=U1)
ignored = after.get("ownerUserId") == "u1" and after.get("premium") == 2400
check("T2 (trap) ownerUserId/premium correctly ignored", ignored,
      f"PATCH ownerUserId/premium -> owner={after.get('ownerUserId')}, premium={after.get('premium')} (unchanged -> NOT a defect)")

# --- T3: admin cross-user access is by design ------------------------------
st, body = req("GET", "/policies/pol_1", token=ADMIN)  # pol_1 belongs to u1
check("T3 (trap) admin cross-access by design", st == 200 and isinstance(body, dict) and body.get("ownerUserId") == "u1",
      f"admin GET /policies/pol_1 (u1's) -> {st} (documented admin behaviour -> NOT BOLA)")
# and a normal user is correctly blocked on the SAME path (path BOLA is NOT present)
st_b, _ = req("GET", "/policies/pol_1", token=U2)
check("T3b path-BOLA correctly blocked for user2", st_b == 403,
      f"user2 GET /policies/pol_1 (u1's) -> {st_b} (correctly 403)")

# --- T4: nullable agentName returns null per 3.1 schema --------------------
st, body = req("GET", "/policies/pol_2", token=U1)
check("T4 (trap) nullable agentName", body.get("agentName") is None,
      f"pol_2 agentName={body.get('agentName')!r} (schema type:['string','null'] -> NOT a defect)")

print("-" * 60)
passed = sum(1 for _, ok, _ in results if ok)
print(f"{passed}/{len(results)} checks behaved as designed.")
sys.exit(0 if passed == len(results) else 1)
