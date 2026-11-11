#!/usr/bin/env python3
"""Nectary spend-only service units: award, spend, balance, verify (docs/units.md).

Stdlib only. The ledger is append-only JSON; every entry carries the sha256 of the one before it.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_LEDGER = os.path.join(ROOT, "ledger", "units.json")
ENTRY_TYPES = ("award", "spend")
GENESIS = "0" * 64


class LedgerError(Exception):
    pass


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save(path, ledger):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(ledger, f, indent=2, ensure_ascii=False)
        f.write("\n")


def entry_hash(entry):
    return hashlib.sha256(json.dumps(entry, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def row_status(spine_path, row):
    """Status cell of `row` in a spine's Issue Ledger table, or None."""
    with open(spine_path, encoding="utf-8") as f:
        for line in f:
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if line.lstrip().startswith("|") and cells and cells[0] == row and len(cells) > 4:
                return cells[4]
    return None


def is_done(status):
    return bool(status) and re.match(r"done\b", status) is not None


def balances(ledger):
    out = {}
    for e in ledger["entries"]:
        sign = 1 if e["type"] == "award" else -1
        out[e["holder"]] = out.get(e["holder"], 0) + sign * e["units"]
    return out


def issued(ledger, epic):
    return sum(e["units"] for e in ledger["entries"] if e["type"] == "award" and e["epic"] == epic)


def verify(ledger, root=ROOT):
    """Return a list of problems (empty = valid)."""
    errs = []
    epics = ledger.get("epics", {})
    prev, last_date = GENESIS, ""
    bal, awarded_rows, epic_issued = {}, set(), {}
    for i, e in enumerate(ledger.get("entries", []), 1):
        where = f"entry {i}"
        t = e.get("type")
        if t not in ENTRY_TYPES:
            errs.append(f"{where}: type {t!r} not allowed (only award or spend; units are non-transferable)")
            continue
        if any(k in e for k in ("to", "from", "recipient")):
            errs.append(f"{where}: carries a transfer field; units are non-transferable")
        if e.get("seq") != i:
            errs.append(f"{where}: seq {e.get('seq')} should be {i}")
        if e.get("prev") != prev:
            errs.append(f"{where}: prev hash breaks the chain (ledger was rewritten?)")
        prev = entry_hash(e)
        d = e.get("date", "")
        if d < last_date:
            errs.append(f"{where}: date {d} is before the previous entry")
        last_date = max(last_date, d)
        units, holder = e.get("units"), e.get("holder")
        if not isinstance(units, int) or units <= 0:
            errs.append(f"{where}: units must be a positive whole number")
            continue
        if not holder:
            errs.append(f"{where}: no holder")
        if not e.get("evidence"):
            errs.append(f"{where}: no evidence link")
        epic = epics.get(e.get("epic"))
        if epic is None:
            errs.append(f"{where}: unknown epic {e.get('epic')!r}")
            continue
        if t == "award":
            row = e.get("row")
            rate = epic.get("rates", {}).get(row)
            if rate is None:
                errs.append(f"{where}: no rate fixed for {row}")
                continue
            if rate.get("pay_in") != "units":
                errs.append(f"{where}: {row} was chosen as a capped revenue claim, not units")
            if rate.get("fixed", "9999") > d:
                errs.append(f"{where}: rate for {row} fixed after the award")
            if not rate.get("before_work") and not rate.get("seed_exception"):
                errs.append(f"{where}: rate for {row} was not fixed before work")
            if e.get("rate") != rate.get("units") or units != rate.get("units"):
                errs.append(f"{where}: award {units} differs from the fixed rate {rate.get('units')}")
            key = (e.get("epic"), row)
            if key in awarded_rows:
                errs.append(f"{where}: {row} already awarded")
            awarded_rows.add(key)
            status = row_status(os.path.join(root, epic["spine"]), row)
            if not is_done(status):
                errs.append(f"{where}: {row} is not done in {epic['spine']} (status: {status})")
            epic_issued[e["epic"]] = epic_issued.get(e["epic"], 0) + units
            if epic_issued[e["epic"]] > epic["cap"]:
                errs.append(f"{where}: {e['epic']} over its cap of {epic['cap']}")
            bal[holder] = bal.get(holder, 0) + units
        else:
            bal[holder] = bal.get(holder, 0) - units
            if bal[holder] < 0:
                errs.append(f"{where}: {holder} would go below zero")
    return errs


def append(ledger, entry):
    entries = ledger.setdefault("entries", [])
    entry = dict(entry, seq=len(entries) + 1, prev=entry_hash(entries[-1]) if entries else GENESIS)
    entries.append(entry)
    return entry


def award(ledger, holder, epic, row, evidence, date, root=ROOT):
    rate = ledger["epics"][epic]["rates"][row]["units"]
    entry = append(ledger, {"type": "award", "date": date, "holder": holder, "epic": epic,
                            "row": row, "rate": rate, "units": rate, "evidence": evidence})
    errs = verify(ledger, root)
    if errs:
        ledger["entries"].pop()
        raise LedgerError("; ".join(errs))
    return entry


def spend(ledger, holder, epic, units, evidence, date, note="", root=ROOT):
    entry = append(ledger, {"type": "spend", "date": date, "holder": holder, "epic": epic,
                            "row": None, "units": units, "evidence": evidence, "note": note})
    errs = verify(ledger, root)
    if errs:
        ledger["entries"].pop()
        raise LedgerError("; ".join(errs))
    return entry


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--ledger", default=DEFAULT_LEDGER)
    sub = p.add_subparsers(dest="cmd", required=True)
    today = dt.date.today().isoformat()
    a = sub.add_parser("award")
    a.add_argument("--holder", required=True); a.add_argument("--epic", required=True)
    a.add_argument("--row", required=True); a.add_argument("--evidence", required=True)
    a.add_argument("--date", default=today)
    s = sub.add_parser("spend")
    s.add_argument("--holder", required=True); s.add_argument("--epic", required=True)
    s.add_argument("--units", type=int, required=True); s.add_argument("--evidence", required=True)
    s.add_argument("--note", default=""); s.add_argument("--date", default=today)
    sub.add_parser("balance")
    sub.add_parser("verify")
    args = p.parse_args(argv)
    ledger = load(args.ledger)
    root = os.path.dirname(os.path.dirname(os.path.abspath(args.ledger)))
    try:
        if args.cmd == "award":
            print(json.dumps(award(ledger, args.holder, args.epic, args.row, args.evidence, args.date, root)))
            save(args.ledger, ledger)
        elif args.cmd == "spend":
            print(json.dumps(spend(ledger, args.holder, args.epic, args.units, args.evidence, args.date, args.note, root)))
            save(args.ledger, ledger)
        elif args.cmd == "balance":
            for h, b in sorted(balances(ledger).items()):
                print(f"{h}\t{b}")
            for name, ep in ledger["epics"].items():
                print(f"# {name}: issued {issued(ledger, name)} of cap {ep['cap']}")
        else:
            errs = verify(ledger, root)
            for e in errs:
                print("FAIL", e)
            if errs:
                return 1
            print(f"OK: {len(ledger['entries'])} entries, caps held, no negative balances, no transfers")
    except (LedgerError, KeyError) as e:
        print("refused:", e, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
