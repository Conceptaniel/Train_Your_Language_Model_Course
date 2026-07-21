#!/usr/bin/env python3
"""Anonymize DM export into a privacy-preserving JSONL file.

Usage: python data/anonymize_dm.py path/to/raw.txt

Output: creates path/to/raw_anonymized.jsonl with records:
  {"date":"YYYY-MM-DD","user_id":"u1","message_hash":"abcd...","attachment_count":N}

Notes: removes full timestamps (keeps date), replaces usernames with stable ids, hashes message text,
and counts attachments instead of storing URLs.
"""
import re
import sys
import json
import hashlib
from pathlib import Path

TS_USER_RE = re.compile(r"^\[(?P<ts>[^\]]+)\]\s*(?P<user>\S.*)$")
URL_RE = re.compile(r"https?://\S+")


def date_only(ts: str) -> str:
    # Try to extract YYYY-MM-DD-like or MM/DD/YYYY and convert; fallback to raw date substring
    # Example input: '8/31/2025 3:56 PM'
    m = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})", ts)
    if m:
        mm, dd, yyyy = m.group(1), m.group(2), m.group(3)
        return f"{int(yyyy):04d}-{int(mm):02d}-{int(dd):02d}"
    # fallback: try YYYY-MM-DD
    m2 = re.search(r"(\d{4})-(\d{2})-(\d{2})", ts)
    if m2:
        return f"{m2.group(1)}-{m2.group(2)}-{m2.group(3)}"
    return ts.split()[0]


def hash_text(s: str) -> str:
    h = hashlib.sha256(s.encode('utf-8', errors='ignore')).hexdigest()
    return h[:16]


def anonymize(path: Path):
    text = path.read_text(encoding='utf-8', errors='replace')
    lines = text.splitlines()
    user_map = {}
    next_id = 1
    out_lines = []
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        m = TS_USER_RE.match(line)
        if m:
            ts = m.group('ts')
            user = m.group('user').strip()
            i += 1
            msg_lines = []
            att_count = 0
            while i < len(lines):
                nxt = lines[i]
                if TS_USER_RE.match(nxt):
                    break
                if nxt.strip() == '{Attachments}':
                    i += 1
                    # count following URL lines
                    while i < len(lines) and URL_RE.search(lines[i]):
                        att_count += 1
                        i += 1
                    continue
                # count inline urls as attachments and remove them from message
                if URL_RE.search(nxt):
                    att_count += len(URL_RE.findall(nxt))
                    # strip urls
                    nxt = URL_RE.sub('', nxt)
                msg_lines.append(nxt.strip())
                i += 1

            msg = ' '.join(l for l in msg_lines if l)
            # map user to stable id
            if user not in user_map:
                user_map[user] = f'u{next_id}'
                next_id += 1
            rec = {
                'date': date_only(ts),
                'user_id': user_map[user],
                'message_hash': hash_text(msg) if msg else None,
                'attachment_count': att_count,
            }
            out_lines.append(json.dumps(rec, ensure_ascii=False))
        else:
            i += 1

    out = path.with_name(path.stem + '_anonymized.jsonl')
    out.write_text('\n'.join(out_lines) + '\n', encoding='utf-8')
    print(f'Wrote anonymized file: {out} (records: {len(out_lines)})')


def main():
    if len(sys.argv) < 2:
        print('Usage: python data/anonymize_dm.py path/to/raw.txt')
        sys.exit(1)
    p = Path(sys.argv[1])
    if not p.exists():
        print('File not found:', p)
        sys.exit(2)
    anonymize(p)


if __name__ == '__main__':
    main()
