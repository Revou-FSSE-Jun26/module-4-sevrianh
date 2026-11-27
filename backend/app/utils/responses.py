"""Response envelope helpers (BE-04, BE-07)."""
from typing import Any

from flask import Response, jsonify


def success(data: Any, status_code: int = 200) -> tuple[Response, int]:
    """Return `{ "data": <payload> }` with the given status."""
    return jsonify({'data': data}), status_code


def error(message: str, status_code: int) -> tuple[Response, int]:
    """Return `{ "error": "<one string>" }` with the given status."""
    return jsonify({'error': str(message)}), status_code


def _flatten(messages: Any, prefix: str = '') -> dict[str, list[str]]:
    """Flatten nested Marshmallow messages into `{field: [message, ...]}`."""
    if isinstance(messages, dict):
        flat: dict[str, list[str]] = {}
        for key, value in messages.items():
            path = f'{prefix}.{key}' if prefix else str(key)
            flat.update(_flatten(value, path))
        return flat
    if isinstance(messages, (list, tuple)):
        return {prefix: [str(m) for m in messages]}
    return {prefix: [str(messages)]}


def format_validation_error(messages: Any) -> str:
    """Normalize Marshmallow messages to one string.

    Fields sorted alphabetically, each `<field>: <messages joined by ", ">`,
    entries joined by " | " (BE-04).
    """
    flat = _flatten(messages)
    entries = [f'{field}: {", ".join(flat[field])}' for field in sorted(flat)]
    return ' | '.join(entries)
