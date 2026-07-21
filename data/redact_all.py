#!/usr/bin/env python3
"""Create a fully redacted version of a cleaned DM file.

Usage: python data/redact_all.py path/to/xxx_cleaned.txt [--delete]

This writes a file with suffix _redacted.txt where every non-empty line is replaced
with the single token [REDACTED].
"""
import sys
from pathlib import Path


def redact_file(p: Path, delete_original: bool = False):
    text = p.read_text(encoding='utf-8', errors='replace')
    lines = text.splitlines()
    redacted_lines = []
    for ln in lines:
        if ln.strip():
            redacted_lines.append('[REDACTED]')
        else:
            redacted_lines.append('')
    out = p.with_name(p.stem.replace('_cleaned','') + '_redacted' + p.suffix)
    out.write_text('\n'.join(redacted_lines) + '\n', encoding='utf-8')
    print(f'Wrote redacted file: {out}')
    if delete_original:
        p.unlink()
        print(f'Deleted original cleaned file: {p}')


def main():
    if len(sys.argv) < 2:
        print('Usage: python data/redact_all.py path/to/xxx_cleaned.txt [--delete]')
        sys.exit(1)
    p = Path(sys.argv[1])
    if not p.exists():
        print('File not found:', p)
        sys.exit(2)
    delete = '--delete' in sys.argv[2:]
    redact_file(p, delete_original=delete)


if __name__ == '__main__':
    main()
