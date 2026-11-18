# RUN.md — Evaluator only (do NOT give to the agent)

Trial: `trial-api3` — REST API testing from an OpenAPI 3.1 contract.
System under test: fictional Turkish car rental "Turna Oto Kiralama —
Rezervasyon ve Kiralama API" (13 operations, 4 test tokens, 16 planted defects).

It replaces `trial-api2` as the discriminating API trial: only 3 of the 16
defects can be found with one or two obvious requests.

## Files in this folder

| File | Give to agent? | Purpose |
|------|----------------|---------|
| `TASK.md` | **YES** | Turkish client request, access info, expected deliverables |
| `openapi.yaml` | **YES** | OpenAPI 3.1 contract (the only source of expected behaviour) |
| `server.js` | **NO** | System under test (contains the planted defects, marked `PLANTED Kn`) |
| `RUN.md` | **NO** | This file |

The answer key is separate: `C:\projeler\TestSkills\evals\keys\api3.md`,
verifier `C:\projeler\TestSkills\evals\keys\grade_api3.py`.

## Requirements

- Node.js 24 (built-ins only; no `npm install`).
- Python 3 (stdlib only) for the verifier.
- Nothing depends on the real date or time: the server runs on a fixed simulated
  clock (`2026-03-10T09:00:00+03:00`, documented in the contract and returned by
  `GET /health`). A run next month behaves exactly like a run today.

## Start the server

Default port 3210:

```
node C:\projeler\TestSkills\evals\trial-api3\server.js
```

Custom port (parallel runs; every copy is independent, state is in memory):

PowerShell:
```
$env:PORT=3311; node C:\projeler\TestSkills\evals\trial-api3\server.js
```
Bash:
```
PORT=3311 node C:\projeler\TestSkills\evals\trial-api3\server.js
```

- **Restart = full reset** to the seed (12 vehicles, 17 reservations, 7 invoices).
- Start a FRESH server process for every agent run. The agent creates, changes,
  cancels and completes reservations.
- Make sure `API3_PLANTED` is **not** set in the shell that starts the server
  for an agent run (see "Reference server" below).
- The server does not crash on bad input and never returns stack traces or file
  paths, so a run should not need a restart. If you do restart during a run,
  tell the agent: its earlier records are gone.

Stop the server with Ctrl+C (or `taskkill /PID <pid> /F`).

## What to give the agent

Copy into a fresh, empty folder outside the repository:

1. `TASK.md`
2. `openapi.yaml`

and tell it the base URL you started the server on. The four tokens are listed
in `TASK.md`. Suggested prompt (same for both arms):

> `TASK.md` dosyasındaki görevi yap. API `http://localhost:3311` adresinde çalışıyor.

Do **not** give `server.js`, this file, or anything under
`C:\projeler\TestSkills\evals\keys\` or `C:\projeler\TestSkills\tests\`.

If the agent runs in a sandbox without network access to your host, run the
server somewhere the agent can reach. The agent needs only an HTTP client.

## Time budget

**40 minutes** wall-clock per run, the same for every arm. The difficulty target
of the key (a strong unaided agent finds roughly 55–75% of the detection points)
assumes this budget. Record the wall-clock time, tokens and tool calls.

## Expected agent deliverables

- `bulgular.md` with two sections: "Kusurlar" and "Açık sorular ve gözlemler"
- `test-kayitlari.md` (evidence log)

`TASK.md` does not tell the agent how the report is scored. Do not explain the
penalties either.

## Verify the environment (before a run)

Start a fresh server, then:

```
python C:\projeler\TestSkills\evals\keys\grade_api3.py http://localhost:3311
```

Expected last line: `91/91 checks behaved as designed.` (exit code 0). The
verifier reproduces K1..K16 and confirms every discriminator, trap (T1..T7) and
contract-silent behaviour (S1..S14) of the key.

The verifier changes data and refuses a server that is not in its seed state.
**Restart the server after the verifier and before the agent run.**

The same check as a unit test (starts and stops its own servers on free ports;
skipped when `node` is not on PATH):

```
python -m unittest tests.test_trial_api3
```

## Reference server (evaluator-only)

```
$env:API3_PLANTED="off"; $env:PORT=3312; node C:\projeler\TestSkills\evals\trial-api3\server.js
python C:\projeler\TestSkills\evals\keys\grade_api3.py http://localhost:3312 --reference
```

With `API3_PLANTED=off` all sixteen planted defects are disabled and the server
follows the contract. Use it while grading:

- a reported behaviour that occurs on the normal server but not on the reference
  server is one of K1..K16;
- a reported behaviour that occurs on both is either correct by the contract
  (trap), contract-silent, or an unplanned real defect — the key's rubric says
  how to tell them apart.

Never use the reference server for an agent run. Remove the variable afterwards
(`Remove-Item Env:API3_PLANTED`).

## Grading

Grade `bulgular.md` blind against `keys\api3.md`: acceptance rule and half rule
per K, traps T1..T7, contract-silent behaviours S1..S14, and the rubric
(detection 88 + report quality 12 − penalties by class). Record `unplanned_real`
findings and add verified ones to the key.
