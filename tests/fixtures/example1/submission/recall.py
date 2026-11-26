"""A toy stand-in for `zenod recall`, used only by the EXAMPLE-1 worked run of tools/verify_ticket.py."""
import argparse
import datetime
import re
import sys

MEMORIES = [
    {"id": 1, "text": "dentist moved to Friday", "saved": "2026-10-30T22:10:00"},
    {"id": 2, "text": "Ana likes the --since idea", "saved": "2026-11-01T00:00:00"},
    {"id": 3, "text": "book the flight", "saved": "2026-11-02T09:30:00"},
]


def parse_day(s):
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", s or ""):
        raise ValueError(f"--since wants YYYY-MM-DD, got {s!r}")
    return datetime.date.fromisoformat(s)


def recall(since=None, memories=MEMORIES):
    if since is None:
        return list(memories)
    day = parse_day(since).isoformat()
    return [m for m in memories if m["saved"][:10] >= day]


def main(argv=None):
    p = argparse.ArgumentParser(prog="recall")
    p.add_argument("--since")
    a = p.parse_args(argv)
    try:
        found = recall(a.since)
    except ValueError as e:
        print(f"recall: {e}", file=sys.stderr)
        return 2
    for m in found:
        print(f"{m['saved'][:10]}  {m['text']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
