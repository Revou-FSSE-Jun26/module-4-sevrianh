"""Standard-library load-test harness; no runtime dependency (TC-23)."""
import argparse
import concurrent.futures
import math
import statistics
import time
import urllib.request


def percentile(values: list[float], percent: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return 0.0
    rank = (len(ordered) - 1) * percent / 100
    lower = math.floor(rank)
    upper = math.ceil(rank)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (rank - lower)


def request_once(url: str) -> float:
    started = time.monotonic()
    with urllib.request.urlopen(url, timeout=30) as response:
        response.read()
        header = response.headers.get('X-Server-Duration-Ms')
        server_ms = float(header) if header is not None else (time.monotonic() - started) * 1000
    return server_ms


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('api_url')
    parser.add_argument('--board-id', required=True)
    parser.add_argument('--duration-seconds', type=int, default=600)
    parser.add_argument('--users', type=int, default=200)
    args = parser.parse_args()

    url = args.api_url.rstrip('/') + '/api/boards/' + args.board_id
    deadline = time.monotonic() + args.duration_seconds
    durations: list[float] = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.users) as pool:
        while time.monotonic() < deadline:
            batch = [pool.submit(request_once, url) for _ in range(args.users)]
            durations.extend(f.result() for f in concurrent.futures.as_completed(batch))

    p95 = percentile(durations, 95)
    print(f'Samples: {len(durations)}')
    print(f'P95 (server ms): {p95:.3f}')
    print(f'Mean (server ms): {statistics.fmean(durations):.3f}' if durations else 'No samples')


if __name__ == '__main__':
    main()
