"""Scope guards for features excluded by V1."""

from pathlib import Path

FORBIDDEN = ('attachment', 'label', 'due_date', 'websocket', 'password_reset', 'oauth')


def test_no_out_of_scope_models_routes_or_modules():
    roots = [Path('app'), Path('tests')]
    hits = []
    for root in roots:
        for path in root.rglob('*'):
            if path.is_file() and path.suffix in {'.py', '.ts', '.tsx'}:
                text = path.read_text(encoding='utf-8').lower()
                for term in FORBIDDEN:
                    if term in text:
                        hits.append((str(path), term))
    assert not hits
