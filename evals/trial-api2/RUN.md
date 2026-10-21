# RUN.md — Evaluator only (do NOT give to the agent)

Trial: `trial-api2` — REST API testing from an OpenAPI 3.1 contract.
System under test: fictional Turkish insurance "Poliçe & Hasar" API.

## Files in this folder

| File | Give to agent? | Purpose |
|------|----------------|---------|
| `TASK.md` | **YES** | Turkish user request + access info |
| `openapi.yaml` | **YES** | OpenAPI 3.1 contract (source of expected behaviour) |
| `server.js` | **NO** | System under test (contains the planted defects) |
| `RUN.md` | **NO** | This file |

The answer key is separate: `C:\projeler\TestSkills\evals\keys\api2.md`
and verifier `C:\projeler\TestSkills\evals\keys\grade_api2.py`.

## Requirements

- Node.js 24 (built-ins only; no `npm install`).
- Python 3 (stdlib only) to run the optional verifier.
- Nothing time-sensitive; data is static. Safe for >4 hours after start.

## Start the server

Default port 3000:

```
node C:\projeler\TestSkills\evals\trial-api2\server.js
```

Custom port (for parallel runs — each copy is fully isolated, in-memory):

PowerShell:
```
$env:PORT=3300; node C:\projeler\TestSkills\evals\trial-api2\server.js
```
Bash:
```
PORT=3300 node C:\projeler\TestSkills\evals\trial-api2\server.js
```

- State is in memory. **Restart = full reset** (5 policies, 7 claims).
- Start a FRESH server per agent run (the agent will create/modify data).
- Parallel copies on different ports do not interfere.

Stop the server with Ctrl+C (or kill the PID / `taskkill /PID <pid> /F`).

## What to give the agent

1. `TASK.md`
2. `openapi.yaml`
3. The base URL you started the server on (e.g. `http://localhost:3300`) and the
   three tokens (already listed inside `TASK.md`).

Do **not** give `server.js` or anything under `C:\projeler\TestSkills\evals\keys\`.

If the agent runs in its own sandbox without network access to your host, run the
server somewhere the agent can reach and give it that URL. The agent needs only an
HTTP client (curl / Node / Python).

## Expected agent deliverables

- `bulgular.md` (defect report)
- `test-kayitlari.md` (evidence log)

## Verify the environment is sound (before/after a run)

Start a fresh server, then:

```
python C:\projeler\TestSkills\evals\keys\grade_api2.py http://localhost:3300
```

Expected: `15/15 checks behaved as designed.` (K1..K10 reproduce, T1..T4 correct).
Note: the verifier mutates data (adds claims, toggles pol_1 status then restores),
so restart the server before an agent run.

## Grading

Grade `bulgular.md` blind against `keys\api2.md` (K1..K10 acceptance rules,
T1..T4 false-positive traps, scoring rubric). The verifier output is ground truth
for whether each defect is really present.
