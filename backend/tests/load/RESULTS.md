# Load Test Results

Status: **measured locally only; not measured on Railway**

The NFR-01 target (P95 of 300 ms or less, 200 concurrent users, one Board of 5 Columns and 50 Cards,
10-minute window) has one recorded run. That run used a local development setup, not the deployed
Railway API with the Gunicorn configuration of `Procfile`. It shows the application code and
queries stay far below 300 ms on this machine. It does not show the target is met in production.

## Run 1 (local)

| Field | Value |
| :--- | :--- |
| Date | 2026-11-28, 16:37 to 16:49 (local time) |
| Script name and version | `backend/tests/load/load_test.py` v2 (`--seed --users 200 --duration 600`) |
| Railway plan | NOT APPLICABLE: no Railway deployment; run on a local Windows 11 laptop (AMD Ryzen AI 7 350, 15 GB RAM) |
| Gunicorn worker class and worker count | NOT APPLICABLE: Gunicorn does not run on Windows. Flask development server (`flask run`, `FLASK_DEBUG=0`), one process, threaded. The `Procfile` setting (2 sync workers) was not exercised. |
| Database plan | Local PostgreSQL 18.4 on the same machine, database `sevy_test` (no network hop) |
| P95 (ms) | 58.21 |

Other figures from the same run: 42,328 requests, 0 errors, 0 responses without the timing header,
P50 27.26 ms, maximum 423.82 ms. Load: 200 virtual users, each calling `GET /api/boards/<id>` and
`GET /api/cards?q=Card&board_id=<id>` with 0.5 to 1.5 s of think time. Timings are the
`X-Server-Duration-Ms` header measured inside the API process (TC-23), so they exclude network
and accept-queue time. The load generator ran on the same machine and competed with the API for CPU.

## What is still open

- Repeat the run against the deployed Railway API and record the Railway plan, the worker class
  and count from the `Procfile`, and the database plan. Until then NFR-01 stays "not measured" for
  production.
- The script only reads (Board load and search). The mixed read and write case (PERF-02, many
  users moving Cards) has no script yet.
- A short 20-user smoke run before the main run gave P95 253.56 ms (first requests after server
  start, 160 samples). It is not a valid run and is not counted.
