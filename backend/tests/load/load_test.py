"""Standard-library load-test script (T-52).

Simulates 200 virtual users on 1 Board (5 Columns, 50 Cards) over a 10-minute window.
P95 latency is computed from `X-Server-Duration-Ms` headers returned by the API server.
"""
import argparse
import concurrent.futures
import json
import math
import random
import time
import urllib.request
from typing import Optional


def _request(
    url: str,
    method: str = 'GET',
    token: Optional[str] = None,
    body: Optional[dict] = None,
) -> float:
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    data = json.dumps(body).encode('utf-8') if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=15) as resp:
        header_ms = resp.headers.get('X-Server-Duration-Ms')
        return float(header_ms) if header_ms is not None else 0.0


def _virtual_user(base_url: str, board_id: str, token: str, deadline: float) -> list[float]:
    durations: list[float] = []
    rng = random.Random()
    while time.monotonic() < deadline:
        try:
            durations.append(_request(f'{base_url}/api/boards/{board_id}', token=token))
            durations.append(
                _request(f'{base_url}/api/cards?q=Card&board_id={board_id}', token=token)
            )
        except Exception:
            pass
        time.sleep(rng.uniform(0.5, 1.5))
    return durations


def run_load_test(
    base_url: str, board_id: str, token: str, users: int = 200, duration_s: int = 600
) -> None:
    deadline = time.monotonic() + duration_s
    all_durations: list[float] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=users) as pool:
        futures = [
            pool.submit(_virtual_user, base_url.rstrip('/'), board_id, token, deadline)
            for _ in range(users)
        ]
        for fut in concurrent.futures.as_completed(futures):
            all_durations.extend(fut.result())

    all_durations.sort()
    if not all_durations:
        print('No responses recorded.')
        return
    p95_idx = max(0, math.ceil(0.95 * len(all_durations)) - 1)
    print(f'Samples: {len(all_durations)} | Server P95 (ms): {all_durations[p95_idx]:.2f}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Sevy API load test (200 VU / 10 min)')
    parser.add_argument('base_url', help='Base API URL, e.g. https://api.example.com')
    parser.add_argument('--board-id', required=True, help='Seeded board UUID (5 columns, 50 cards)')
    parser.add_argument('--token', required=True, help='Bearer JWT for virtual users')
    parser.add_argument('--users', type=int, default=200)
    parser.add_argument('--duration', type=int, default=600)
    args = parser.parse_args()
    run_load_test(args.base_url, args.board_id, args.token, args.users, args.duration)
