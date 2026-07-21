#!/usr/bin/env python3
"""Simple DM cleaning script.

Usage: python data/clean_dm.py "path/to/file.txt"

Outputs a cleaned file next to the input with suffix _cleaned.txt and prints a small summary.
"""
import re
import sys
from pathlib import Path


OFFENSIVE = {"retards", "retard"}


def redact(text: str) -> str:
    def repl(m):
        return "[redacted]"

    # word-boundary replace for offensive words (case-insensitive)
    pattern = re.compile(r"\\b(" + "|".join(re.escape(w) for w in OFFENSIVE) + r")\\b", flags=re.IGNORECASE)
    text = pattern.sub(repl, text)
    # normalize whitespace
    text = re.sub(r"[\t\u00A0]+", " ", text)
    text = re.sub(r" +", " ", text)
    text = text.strip()
    return text


TS_USER_RE = re.compile(r"^\[(?P<ts>[^\]]+)\]\s*(?P<user>\S.*)$")
URL_RE = re.compile(r"https?://\S+")


def simplify_url(url: str) -> str:
    # keep only base path (no query params)
    return url.split("?")[0]


def clean_messages(text: str):
    lines = text.splitlines()
    out_lines = []
    i = 0
    total_msgs = 0
    removed = 0
    while i < len(lines):
        line = lines[i].rstrip()
        m = TS_USER_RE.match(line)
        if m:
            ts = m.group("ts")
            user = m.group("user").strip()
            # gather following message lines until next timestamp or blank separator
            i += 1
            msg_lines = []
            while i < len(lines):
                nxt = lines[i]
                if TS_USER_RE.match(nxt):
                    break
                # treat attachment marker and raw urls
                if nxt.strip() == "{Attachments}":
                    i += 1
                    # collect URLs following
                    att_urls = []
                    while i < len(lines) and URL_RE.search(lines[i]):
                        u = URL_RE.search(lines[i]).group(0)
                        att_urls.append(simplify_url(u))
                        i += 1
                    if att_urls:
                        msg_lines.append("[Attachment] " + ", ".join(att_urls))
                    continue
                msg_lines.append(nxt)
                i += 1

            msg = " ".join(l.strip() for l in msg_lines if l.strip())
            msg = redact(msg)
            if not msg:
                removed += 1
                continue
            # turn into single-line record: timestamp \t user: message
            out_lines.append(f"[{ts}]\t{user}: {msg}")
            total_msgs += 1
        else:
            # non-timestamp lines: keep if they contain URLs or text
            if URL_RE.search(line):
                out_lines.append("[orphaned_url] " + simplify_url(URL_RE.search(line).group(0)))
                total_msgs += 1
            elif line.strip():
                s = redact(line)
                if s:
                    out_lines.append(s)
                    total_msgs += 1
                else:
                    removed += 1
            i += 1

    return "\n".join(out_lines) + "\n", total_msgs, removed


def main():
    if len(sys.argv) < 2:
        print("Usage: python data/clean_dm.py path/to/file.txt")
        sys.exit(1)
    p = Path(sys.argv[1])
    if not p.exists():
        print("File not found:", p)
        sys.exit(2)
    raw = p.read_text(encoding="utf-8", errors="replace")
    cleaned, kept, removed = clean_messages(raw)
    out = p.with_name(p.stem + "_cleaned" + p.suffix)
    out.write_text(cleaned, encoding="utf-8")
    print(f"Cleaned: wrote {out}\nMessages kept: {kept}, removed/empty: {removed}")


if __name__ == "__main__":
    main()
