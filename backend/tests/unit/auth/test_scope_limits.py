"""Scope guards for features excluded by V1."""

from pathlib import Path

FORBIDDEN_NAMES = {
    'attachment', 'attachments', 'label', 'labels', 'due_date', 'due_dates',
    'websocket', 'password_reset', 'oauth',
}


def test_no_out_of_scope_models_routes_or_modules():
    app_files = [path for path in Path('app').rglob('*') if path.is_file()]
    names = {
        path.name.lower().removesuffix(path.suffix.lower())
        for path in app_files
    }
    names.update(part.lower() for path in app_files for part in path.parts)
    assert names.isdisjoint(FORBIDDEN_NAMES)
