# RUN — trial-exploratory (Perdeaçık Bilet)

Evaluator-facing. Do not hand this file, `app/`, or the key file to the agent.

## What is in this folder

| Path | Purpose | Give to agent? |
|---|---|---|
| `TASK.md` | The exact user request (Turkish) | Yes (as the prompt, and as a file in the workspace) |
| `inputs/urun-notu.md` | Product owner's short product note (the only "spec") | Yes (copy into the workspace root) |
| `app/server.js`, `app/public/*` | System under test: SPA + JSON API on Node's built-in `http` module | **No** |
| `RUN.md` | This file | No |

Grading key: `C:\projeler\TestSkills\evals\keys\exploratory.md` (outside this folder).

## Requirements

- Node.js 18 or newer (verified with Node 24.19.0 on Windows 11). No `npm install`, no internet, no other dependencies.
- The agent needs a browser automation tool (Playwright + Chromium) and/or an HTTP client. Browser and server must be on the same machine: event dates are shown in the machine's local time zone.

## Per-run procedure

1. **Copy the app outside the agent's workspace.** The app deliberately leaks stack traces with absolute file paths (one of the planted defects). If the agent can read the file system, running the app from a copy the agent will not browse keeps the trial black-box. Example (PowerShell):
   ```powershell
   Copy-Item -Recurse C:\projeler\TestSkills\evals\trial-exploratory\app $env:TEMP\perdeacik-4310
   ```
2. **Start the server (fresh process for every run).** The port comes from the `PORT` env var and defaults to **4310**. It binds to 127.0.0.1 (override with `HOST`).
   ```powershell
   $env:PORT = 4310; node $env:TEMP\perdeacik-4310\server.js
   ```
   ```bash
   PORT=4310 node "$TEMP/perdeacik-4310/server.js"
   ```
   The console prints `Perdeaçık Bilet demo sunucusu: http://127.0.0.1:4310`.
3. **Health check:** `GET http://127.0.0.1:4310/api/saglik` returns `{"durum":"ok"}`.
4. **Prepare the agent workspace:** an empty folder containing only `TASK.md` and `urun-notu.md` (copied from `inputs/`). If you use a port other than 4310, replace `4310` in the workspace copy of `TASK.md`.
5. **Run the agent** with the content of `TASK.md` as the user message and the workspace as its working directory. Time box: a strong agent needs about 15–25 minutes. The TASK mentions a 60–90 minute session because that is how a human would phrase it.
6. **Finish within about 2.5 hours of starting the server.** Event dates are generated relative to server start. Two events are seeded 3–23 hours ahead because planted defect K7 needs them. After roughly 3 hours the nearest one may already have started and disappear from sale.
7. **Collect** `kesif-raporu.md` (plus `kanitlar/` if present) from the workspace and grade it with the key.
8. **Stop the server** with Ctrl+C in its console, or:
   ```powershell
   Get-NetTCPConnection -State Listen -LocalPort 4310 | ForEach-Object { Stop-Process -Id $_.OwningProcess }
   ```

## State and parallel runs

- All state (events, seat counts, orders) is held in memory in the server process. Nothing is written to disk, and a restart resets everything. Always restart between runs.
- Run parallel copies on different ports (`PORT=4311`, `4312`, …). Copies do not share any state. Each agent's `TASK.md` must name its own port.
- On a 500 response the server prints stack traces to stderr. This is expected: it is part of planted defect K6.

## Seed data (regenerated at every start)

| id | Event | City | When | Price | Seats left |
|---|---|---|---|---|---|
| 101 | Boğaziçi Caz Gecesi | İstanbul | first 10:00–22:30 half-hour slot ≥ 3 h after start (3–14.5 h ahead) | 149,90 | 38 |
| 102 | İstanbul Gençlik Senfonisi: Mevsimler | İstanbul | last such slot ≤ 23 h after start (11.5–23 h ahead) | 275,00 | 64 |
| 103 | Çello ve Piyano Resitali | Ankara | +3 days 20:00 | 220,00 | 52 |
| 104 | İzmir Kordon Akustik | İzmir | +6 days 21:00 | 164,99 | 80 |
| 105 | Şebnem'in Düğünü | Eskişehir | +9 days 20:30 | 185,00 | 3 |
| 106 | Zeybek ve Ege Ezgileri | Bursa | +12 days 19:00 | 95,50 | 0 (sold out) |
| 107 | Ankara Stand-up Gecesi | Ankara | +15 days 21:30 | 137,50 | 110 |
| 108 | Ödüllü Kısa Filmler Gösterimi | İzmir | +20 days 18:00 | 60,00 | 90 |
| 109 | Üsküdar Tasavvuf Musikisi Konseri | İstanbul | +25 days 20:00 | 120,00 | 75 |

## API (for graders reading HTTP-based reports)

- `GET /api/etkinlikler`: upcoming events. `GET /api/etkinlikler/:id`: one event.
- `GET /api/kampanya?kod=&tutar=`: checks a promo code against an order amount.
- `POST /api/siparisler` with body `{etkinlikId, tur: "tam"|"ogrenci", adet, adSoyad, eposta, telefon, kampanyaKodu, kvkk: true}` creates an order.
- `GET /api/siparisler?eposta=`: orders for an e-mail address. `GET /api/siparisler/:pnr`: one order.
- `POST /api/siparisler/:pnr/iptal`: cancels an order.
- `GET /api/saglik`: health check.
