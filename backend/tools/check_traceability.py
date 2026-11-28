"""Check that every acceptance criterion R<N>.<k> of requirements.md is in design.md and tasks.md.

Read-only, stdlib only. Usage (from the repository root):
    python backend/tools/check_traceability.py [spec_dir]
The default spec_dir is .kiro/specs/task-management-app; pass `specs` to check the
submission copy. design.md writes IDs as `R<N>.<k>`; tasks.md lists them as `<N>.<k>` in
`_Requirements:` lines, so both spellings are accepted in both files.
Exit code 0 when no ID is missing, 1 otherwise.
"""
import re
import sys
from pathlib import Path

DEFAULT_DIR = '.kiro/specs/task-management-app'
REQUIREMENT_RE = re.compile(r'^### Requirement (\d+):', re.M)
CRITERIA_HEADING = '#### Acceptance Criteria'
NUMBERED_RE = re.compile(r'^(\d+)\. ', re.M)


def criterion_ids(requirements: str) -> list[str]:
    """IDs `R<N>.<k>` in document order: the kth numbered item under each criteria heading."""
    ids: list[str] = []
    blocks = REQUIREMENT_RE.split(requirements)
    for number, body in zip(blocks[1::2], blocks[2::2]):
        if CRITERIA_HEADING not in body:
            continue
        section = body.split(CRITERIA_HEADING, 1)[1]
        section = re.split(r'^#{1,4} ', section, maxsplit=1, flags=re.M)[0]
        ids.extend(f'R{number}.{k}' for k in NUMBERED_RE.findall(section))
    return ids


def _mentioned(text: str, criterion: str) -> bool:
    bare = criterion[1:]
    return re.search(rf'(?<![\w.])R?{re.escape(bare)}(?![\w.]*\d)', text) is not None


def missing_ids(ids: list[str], text: str) -> list[str]:
    return [criterion for criterion in ids if not _mentioned(text, criterion)]


def main(argv: list[str]) -> int:
    spec_dir = Path(argv[1] if len(argv) > 1 else DEFAULT_DIR)
    read = lambda name: (spec_dir / name).read_text(encoding='utf-8')  # noqa: E731
    ids = criterion_ids(read('requirements.md'))
    failed = False
    for name in ('design.md', 'tasks.md'):
        absent = missing_ids(ids, read(name))
        print(f'{name}: {len(ids) - len(absent)}/{len(ids)} criterion IDs found')
        if absent:
            failed = True
            print('  MISSING: ' + ', '.join(absent))
    return 1 if failed or not ids else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
