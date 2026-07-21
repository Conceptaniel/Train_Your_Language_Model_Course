#!/usr/bin/env python3
"""Prepare a BPE-ready corpus from a raw DM export.

Output: data/dm_bpe.txt with one message per line.

Behavior:
- Collapse multi-line messages into single lines
- Strip timestamps and usernames
- Remove URLs and attachment markers
- Lowercase and normalize whitespace
- Filter out very short messages (<3 chars)
"""
import re
import sys
from pathlib import Path

TS_USER_RE = re.compile(r"^\[(?P<ts>[^\]]+)\]\s*(?P<user>\S.*)$")
URL_RE = re.compile(r"https?://\S+")


def clean_msg_lines(msg_lines):
    # join, remove urls, lowercase, normalize spaces
    s = ' '.join(l.strip() for l in msg_lines if l and l.strip())
    s = URL_RE.sub('', s)
    s = re.sub(r"[\t\u00A0]+", ' ', s)
    s = re.sub(r" +", ' ', s)
    s = s.strip().lower()
    return s


def prepare(path: Path, outpath: Path):
    text = path.read_text(encoding='utf-8', errors='replace')
    lines = text.splitlines()
    i = 0
    count_in = 0
    count_out = 0
    with outpath.open('w', encoding='utf-8') as f:
        while i < len(lines):
            line = lines[i].rstrip()
            m = TS_USER_RE.match(line)
            if m:
                count_in += 1
                i += 1
                msg_lines = []
                while i < len(lines):
                    nxt = lines[i]
                    if TS_USER_RE.match(nxt):
                        break
                    if nxt.strip() == '{Attachments}':
                        # skip attachments and following url lines
                        i += 1
                        while i < len(lines) and URL_RE.search(lines[i]):
                            i += 1
                        continue
                    # treat inline url lines by removing urls later
                    msg_lines.append(nxt)
                    i += 1

                cleaned = clean_msg_lines(msg_lines)
                if len(cleaned) >= 3:
                    f.write(cleaned + '\n')
                    count_out += 1
                continue
            else:
                # ignore non-timestamp top-level lines
                i += 1

    print(f'Prepared BPE corpus: wrote {outpath} (messages in: {count_in}, kept: {count_out})')


def main():
    if len(sys.argv) < 2:
        print('Usage: python data/prepare_bpe.py path/to/raw.txt')
        sys.exit(1)
    p = Path(sys.argv[1])
    if not p.exists():
        print('File not found:', p)
        sys.exit(2)
    out = Path('data') / 'dm_bpe.txt'
    prepare(p, out)


if __name__ == '__main__':
    main()
