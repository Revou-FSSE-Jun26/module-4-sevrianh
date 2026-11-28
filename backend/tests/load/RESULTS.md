# Load Test Results

Status: **not measured**

A run against the deployed API is not performed in this task.

| Date | Script name and version | Railway plan | Gunicorn worker class and worker count | Database plan | P95 (ms) | Status |
|---|---|---|---|---|---|---|
| NOT RECORDED | `backend/tests/load/load_test.py` v1 | NOT RECORDED | NOT RECORDED | NOT RECORDED | NOT MEASURED | not measured |

- Duration source: `X-Server-Duration-Ms` response header measured at the API server.
- Run shape: 200 virtual users, one Board, 5 Columns, 50 Cards, 10-minute window.
- A P95 above 300 ms is recorded as `not met`; no value below is inferred until measured.
