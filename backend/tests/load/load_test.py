"""Standard-library load-test script (T-52, v2).

Simulates virtual users on 1 Board (5 Columns, 50 Cards) over a time window (default
200 users, 600 s). P95 latency is computed only from `X-Server-Duration-Ms` headers
returned by the API server (TC-23). Failed requests and responses without the header
are counted and reported, never folded into the P95.

Usage:
    python load_test.py http://localhost:5000 --seed
    python load_test.py https://api.example.com --board-id <uuid> --token <jwt>
"""
import argparse
import concurrent.futures
import json
import math
import random
import time
import urllib.request
import uuid
from dataclasses import dataclass, field
from typing import Optional

SCRIPT_VERSION = 'load_test.py v2'
COLUMNS = 5
CARDS = 50
PASSWORD = 'Passw0rd!load'


def _call(url: str, method: str = 'GET', token: Optional[str] = None,
          body: Optional[dict] = None) -> tuple[dict, Optional[float]]:
    """Return (parsed JSON body, server duration in ms or None when the header is absent)."""
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    data = json.dumps(body).encode('utf-8') if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=15) as resp:
        raw = resp.headers.get('X-Server-Duration-Ms')
        return json.loads(resp.read() or b'{}'), float(raw) if raw is not None else None


def seed(base_url: str) -> tuple[str, str]:
    """Create a user, a Board with 5 Columns and 50 Cards; return (board_id, token)."""
    base = base_url.rstrip('/')
    tag = uuid.uuid4().hex[:16]
    user = {'name': 'Load User', 'username': f'load_{tag}',
            'email': f'load_{tag}@example.com', 'password': PASSWORD}
    _call(f'{base}/api/auth/register', 'POST', body=user)
    login, _ = _call(f'{base}/api/auth/login', 'POST',
                     body={'email': user['email'], 'password': PASSWORD})
    token = login['data']['access_token']
    board, _ = _call(f'{base}/api/boards', 'POST', token, {'name': 'Load Board'})
    board_id = board['data']['id']
    column_ids = []
    for i in range(COLUMNS):
        col, _ = _call(f'{base}/api/boards/{board_id}/columns', 'POST', token,
                       {'name': f'Column {i + 1}'})
        column_ids.append(col['data']['id'])
    for i in range(CARDS):
        _call(f'{base}/api/columns/{column_ids[i % COLUMNS]}/cards', 'POST', token,
              {'title': f'Card {i + 1}'})
    return board_id, token


@dataclass
class Tally:
    durations: list[float] = field(default_factory=list)
    errors: int = 0
    missing_header: int = 0

    def merge(self, other: 'Tally') -> None:
        self.durations.extend(other.durations)
        self.errors += other.errors
        self.missing_header += other.missing_header


def _record(tally: Tally, url: str, token: str) -> None:
    try:
        _, ms = _call(url, token=token)
    except Exception:
        tally.errors += 1
        return
    if ms is None:
        tally.missing_header += 1
    else:
        tally.durations.append(ms)


def _virtual_user(base_url: str, board_id: str, token: str, deadline: float) -> Tally:
    tally = Tally()
    rng = random.Random()
    while time.monotonic() < deadline:
        _record(tally, f'{base_url}/api/boards/{board_id}', token)
        _record(tally, f'{base_url}/api/cards?q=Card&board_id={board_id}', token)
        time.sleep(rng.uniform(0.5, 1.5))
    return tally


def percentile(sorted_values: list[float], fraction: float) -> float:
    return sorted_values[max(0, math.ceil(fraction * len(sorted_values)) - 1)]


def run_load_test(base_url: str, board_id: str, token: str, users: int, duration_s: int) -> int:
    base = base_url.rstrip('/')
    deadline = time.monotonic() + duration_s
    total = Tally()
    with concurrent.futures.ThreadPoolExecutor(max_workers=users) as pool:
        futures = [pool.submit(_virtual_user, base, board_id, token, deadline)
                   for _ in range(users)]
        for fut in concurrent.futures.as_completed(futures):
            total.merge(fut.result())

    attempts = len(total.durations) + total.errors + total.missing_header
    print(f'Script: {SCRIPT_VERSION} | users: {users} | window: {duration_s} s')
    print(f'Requests: {attempts} | measured: {len(total.durations)} | '
          f'errors: {total.errors} | missing timing header: {total.missing_header}')
    if not total.durations:
        print('No server timings recorded; P95 not measured.')
        return 1
    values = sorted(total.durations)
    print(f'Server P50 (ms): {percentile(values, 0.50):.2f} | '
          f'P95 (ms): {percentile(values, 0.95):.2f} | max (ms): {values[-1]:.2f}')
    return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Sevy API load test (200 VU / 10 min)')
    parser.add_argument('base_url', help='Base API URL, e.g. https://api.example.com')
    parser.add_argument('--seed', action='store_true',
                        help='Create a user and a Board (5 Columns, 50 Cards) first')
    parser.add_argument('--board-id', help='Seeded Board UUID (5 Columns, 50 Cards)')
    parser.add_argument('--token', help='Bearer JWT for the virtual users')
    parser.add_argument('--users', type=int, default=200)
    parser.add_argument('--duration', type=int, default=600)
    args = parser.parse_args()
    if args.seed:
        args.board_id, args.token = seed(args.base_url)
        print(f'Seeded Board {args.board_id}')
    elif not (args.board_id and args.token):
        parser.error('give --seed, or both --board-id and --token')
    raise SystemExit(
        run_load_test(args.base_url, args.board_id, args.token, args.users, args.duration))
