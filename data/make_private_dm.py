#!/usr/bin/env python3
"""Convert a raw DM export into a privacy-safe chat log in the same plain-text format as DummyData.txt."""
import re
import sys
from pathlib import Path
from datetime import datetime

TS_USER_RE = re.compile(r"^\[(?P<ts>[^\]]+)\]\s*(?P<user>\S.*)$")
URL_RE = re.compile(r"https?://\S+")
OFFENSIVE = {"retards", "retard"}


def redact(text: str) -> str:
    pattern = re.compile(r"\b(" + "|".join(re.escape(w) for w in OFFENSIVE) + r")\b", flags=re.IGNORECASE)
    text = pattern.sub("[redacted]", text)
    text = re.sub(r"[\t\u00A0]+", " ", text)
    text = re.sub(r" +", " ", text)
    return text.strip()


def fmt_ts(raw: str) -> str:
    # convert '8/31/2025 3:56 PM' -> '31/08/2025, 15:56'
    try:
        dt = datetime.strptime(raw, "%m/%d/%Y %I:%M %p")
    except ValueError:
        try:
            dt = datetime.strptime(raw, "%m/%d/%Y %I:%M%p")
        except ValueError:
            return raw
    return dt.strftime("%d/%m/%Y, %H:%M")


def parse_messages(text: str):
    lines = text.splitlines()
    msgs = []
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        m = TS_USER_RE.match(line)
        if m:
            ts = m.group("ts")
            user = m.group("user").strip()
            i += 1
            msg_lines = []
            while i < len(lines):
                nxt = lines[i]
                if TS_USER_RE.match(nxt):
                    break
                if nxt.strip() == "{Attachments}":
                    i += 1
                    while i < len(lines) and URL_RE.search(lines[i]):
                        i += 1
                    continue
                msg_lines.append(nxt)
                i += 1
            message = " ".join(l.strip() for l in msg_lines if l.strip())
            message = URL_RE.sub("", message)
            message = redact(message)
            if message:
                msgs.append((fmt_ts(ts), user, message))
            continue
        i += 1
    return msgs


def write_private_file(input_path: Path, output_path: Path):
    msgs = parse_messages(input_path.read_text(encoding="utf-8", errors="replace"))
    name_map = {}
    name_counter = 1
    lines = []
    for ts, user, msg in msgs:
        if user not in name_map:
            name_map[user] = f"Person {name_counter}"
            name_counter += 1
        lines.append(f"{ts} - {name_map[user]}: {msg}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {output_path} ({len(lines)} messages)")


def main():
    if len(sys.argv) < 2:
        print("Usage: python data/make_private_dm.py path/to/raw_dm.txt")
        sys.exit(1)
    input_path = Path(sys.argv[1])
    if not input_path.exists():
        print("File not found:", input_path)
        sys.exit(2)
    output_path = Path("data/private") / input_path.name
    write_private_file(input_path, output_path)


if __name__ == "__main__":
    main()
