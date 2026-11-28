"""Check that every guideline heading in guidelines/*.md has RULE, RATIONALE and EXAMPLE (ST-12).

Read-only, stdlib only. Usage (from the repository root):
    python backend/tools/check_guidelines.py
Prints one OK or MISSING line per `### FE-nn`, `### BE-nn` and `### DB-nn` heading.
Exit code 0 only when no label is missing and at least one heading was found.
"""
import re
import sys
from pathlib import Path

FILES = ('frontend', 'backend', 'database')
LABELS = ('RULE', 'RATIONALE', 'EXAMPLE')
HEADING_RE = re.compile(r'(?m)^### ((?:FE|BE|DB)-\d{2})')
NEXT_HEADING_RE = re.compile(r'(?m)^#{1,3} ')


def check_text(text: str) -> list[tuple[str, list[str]]]:
    """(heading id, missing labels) for each guideline heading, labels matched as **LABEL."""
    results = []
    for match in HEADING_RE.finditer(text):
        rest = text[match.end():]
        following = NEXT_HEADING_RE.search(rest)
        body = rest[:following.start()] if following else rest
        missing = [k for k in LABELS if not re.search(r'\*\*' + k, body, re.I)]
        results.append((match.group(1), missing))
    return results


def main(argv: list[str]) -> int:
    root = Path(argv[1] if len(argv) > 1 else 'guidelines')
    total, failed = 0, False
    for name in FILES:
        text = (root / f'{name}.md').read_text(encoding='utf-8')
        for heading, missing in check_text(text):
            total += 1
            failed = failed or bool(missing)
            print(name, heading, 'OK' if not missing else 'MISSING ' + ','.join(missing))
    print(total, 'headings')
    return 1 if failed or total == 0 else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
