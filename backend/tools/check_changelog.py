"""Check the TC-21 evidence in a spec CHANGELOG.md.

Read-only, stdlib only. Usage (from the repository root):
    python backend/tools/check_changelog.py [changelog_path]
The default path is specs/CHANGELOG.md. A refinement round is every `## V<N> - ` entry
after the V1 baseline; each round needs the labels **Prompt**, **Before** and **After**.
Exit code 0 only with at least 5 rounds and no round missing a label.
"""
import re
import sys
from pathlib import Path

DEFAULT_PATH = 'specs/CHANGELOG.md'
LABELS = ('**Prompt**', '**Before**', '**After**')
MIN_ROUNDS = 5


def split_rounds(text: str) -> list[str]:
    entries = re.split(r'(?m)^(?=## V\d+ - )', text)[1:]
    return [entry for entry in entries if not entry.startswith('## V1 - ')]


def rounds_missing_labels(rounds: list[str]) -> list[str]:
    return [r.splitlines()[0] for r in rounds if not all(label in r for label in LABELS)]


def main(argv: list[str]) -> int:
    path = Path(argv[1] if len(argv) > 1 else DEFAULT_PATH)
    rounds = split_rounds(path.read_text(encoding='utf-8'))
    bad = rounds_missing_labels(rounds)
    print(f'{len(rounds)} refinement rounds (need {MIN_ROUNDS}); missing labels: {bad}')
    return 0 if len(rounds) >= MIN_ROUNDS and not bad else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv))
