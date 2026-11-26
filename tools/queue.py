#!/usr/bin/env python3
"""Nectary repayment queue: claim, settle, balance, verify, demo (docs/repayment-queue.md).

A builder who picks cash gets a claim of the ticket's price fixed before work, 1x, never more.
Claims join one public line per hoster in the order their tickets were accepted. Each closed month
the hoster puts half its profit, less what it spent serving builder credit that month
(ledger/credit.json), into the line; the money pays the oldest open claim first, part by part,
until each is paid in full. No interest, no amount above the fixed price, no claim paid twice.

Same public, append-only JSON with a sha256 hash chain as the units and credit ledgers.
Money is held in whole US cents. Stdlib only.

  python3 tools/queue.py claim --ticket tickets/X.md --evidence <link>   a cash claim joins the line
  python3 tools/queue.py settle --hoster zenod --month 2026-11           fund a closed month, pay the line
  python3 tools/queue.py balance | verify | demo
"""
import argparse
import copy
import datetime as dt
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from units import GENESIS, LedgerError, ROOT, entry_hash, is_done, load, row_status, save  # noqa: E402
import ticket as ticketlib  # noqa: E402

DEFAULT_LEDGER = os.path.join(ROOT, "ledger", "queue.json")
ENTRY_TYPES = ("claim", "fund", "pay")
KINDS = ("ticket", "bootstrap")


def month_of(date):
    return date[:7]


def month_closed_by(month, date):
    """True when `date` falls after the last day of `month` (a month is funded only once it is over)."""
    return month_of(date) > month


def credit_cost_cents(credit, hoster, month):
    """What serving builder credit cost the hoster in `month`: credit honoured x its serve cost."""
    rec = credit.get("hosters", {}).get(hoster, {}).get("months", {}).get(month)
    if rec is None:
        return 0
    honoured = sum(e["cents"] for e in credit.get("entries", [])
                   if e["type"] == "honour" and e.get("hoster") == hoster and month_of(e["date"]) == month)
    return int(round(honoured * rec["serve_cost_per_credit_dollar"]))


def funding(credit, hoster, month):
    """(profit, credit cost, cash for the queue) for one hoster-month, in cents, or None without public books."""
    rec = credit.get("hosters", {}).get(hoster, {}).get("months", {}).get(month)
    if rec is None:
        return None
    profit = rec["profit_cents"]
    cost = credit_cost_cents(credit, hoster, month)
    return profit, cost, max(0, profit // 2 - cost) if profit > 0 else 0


def lines(ledger):
    """Per hoster, the open claims in line order: [(seq, owed cents)]; plus paid cents per claim."""
    paid, line = {}, {}
    for e in ledger["entries"]:
        if e["type"] == "claim":
            line.setdefault(e["hoster"], []).append(e["seq"])
            paid[e["seq"]] = 0
        elif e["type"] == "pay":
            paid[e["claim"]] = paid.get(e["claim"], 0) + e["cents"]
    out = {}
    for h, seqs in line.items():
        out[h] = [(s, ledger["entries"][s - 1]["cents"] - paid[s]) for s in seqs
                  if ledger["entries"][s - 1]["cents"] - paid[s] > 0]
    return out, paid


def other_currency(ticket_id, row, credit, units):
    """Why a claim for this ticket would be a second currency, or None."""
    if any(e["type"] == "issue" and e.get("ticket") == ticket_id for e in credit.get("entries", [])):
        return f"{ticket_id} was already paid in builder credit"
    if row and any(e["type"] == "award" and e.get("row") == row for e in units.get("entries", [])):
        return f"{row} was already paid in units"
    return None


def verify(ledger, credit, units=None, root=ROOT):
    """Every problem in the queue ledger (empty = consistent)."""
    units = units or {"entries": []}
    errs = []
    prev, last_date = GENESIS, ""
    claims, paid, tickets, funded, fund_left, line = {}, {}, set(), set(), {}, {}
    for i, e in enumerate(ledger.get("entries", []), 1):
        where = f"entry {i}"
        t = e.get("type")
        if t not in ENTRY_TYPES:
            errs.append(f"{where}: type {t!r} not allowed (only {', '.join(ENTRY_TYPES)})")
            continue
        if e.get("seq") != i:
            errs.append(f"{where}: seq {e.get('seq')} should be {i}")
        if e.get("prev") != prev:
            errs.append(f"{where}: prev hash breaks the chain (ledger was rewritten?)")
        prev = entry_hash(e)
        d = e.get("date", "")
        if d < last_date:
            errs.append(f"{where}: date {d} is before the previous entry")
        last_date = max(last_date, d)
        c, h = e.get("cents"), e.get("hoster")
        if not isinstance(c, int) or c < 0 or (t != "fund" and c == 0):
            errs.append(f"{where}: cents must be a positive whole number")
            continue
        if h not in credit.get("hosters", {}):
            errs.append(f"{where}: unknown hoster {h!r} (hosters and their books live in the credit ledger)")
            continue
        if t == "claim":
            kind, tid = e.get("kind"), e.get("ticket")
            if kind not in KINDS:
                errs.append(f"{where}: kind {kind!r} not allowed (only {', '.join(KINDS)})")
                continue
            if not e.get("holder") or not e.get("evidence"):
                errs.append(f"{where}: a claim names its holder and its evidence")
                continue
            if tid in tickets:
                errs.append(f"{where}: {tid} already has a claim (one claim per ticket)")
                continue
            if kind == "ticket":
                if e.get("price_cents") != c:
                    errs.append(f"{where}: claim {c} is not the fixed price {e.get('price_cents')} (1x, never more)")
                why = other_currency(tid, e.get("row"), credit, units)
                if why:
                    errs.append(f"{where}: {why} (never two currencies)")
            elif not e.get("cost_basis"):
                errs.append(f"{where}: a bootstrap claim records what the cost was and how it was counted")
            if d < e.get("accepted", "9999"):
                errs.append(f"{where}: joins the line before its row was accepted")
            if not e.get("demonstration"):
                spine = ledger.get("spines", {}).get(e.get("epic"))
                status = row_status(os.path.join(root, spine), e.get("row")) if spine else None
                if not is_done(status):
                    errs.append(f"{where}: {e.get('row')} is not accepted (done) in its spine (status: {status})")
            tickets.add(tid)
            claims[i] = e
            paid[i] = 0
            line.setdefault(h, []).append(i)
        elif t == "fund":
            m = e.get("month", "")
            if (h, m) in funded:
                errs.append(f"{where}: {h} {m} already funded the queue")
                continue
            if not month_closed_by(m, d):
                errs.append(f"{where}: {m} is funded on {d}, before the month is over")
            got = funding(credit, h, m)
            if got is None:
                errs.append(f"{where}: {h} has no public books for {m} in the credit ledger")
                continue
            profit, cost, cash = got
            if (e.get("profit_cents"), e.get("credit_cost_cents"), c) != (profit, cost, cash):
                errs.append(f"{where}: {h} {m} should put {cash} in (half of {profit} profit less {cost} credit served), "
                            f"not {c}")
            funded.add((h, m))
            fund_left[i] = c
        else:  # pay
            cs, fs = e.get("claim"), e.get("fund")
            cl = claims.get(cs)
            if cl is None:
                errs.append(f"{where}: pays no known claim ({cs})")
                continue
            if paid[cs] >= cl["cents"]:
                errs.append(f"{where}: claim {cs} is already paid in full (no claim is paid twice)")
                continue
            if e.get("holder") != cl["holder"] or h != cl["hoster"]:
                errs.append(f"{where}: does not match claim {cs} (holder and hoster)")
                continue
            head = next((s for s in line[h] if paid[s] < claims[s]["cents"]), None)
            if head != cs:
                errs.append(f"{where}: claim {cs} jumps the line (claim {head} waits first)")
            if paid[cs] + c > cl["cents"]:
                errs.append(f"{where}: pays {paid[cs] + c} on claim {cs}, over its fixed price {cl['cents']} (never more)")
            if fs not in fund_left or ledger["entries"][fs - 1].get("hoster") != h:
                errs.append(f"{where}: draws on no fund of {h} ({fs})")
            elif fund_left[fs] < c:
                errs.append(f"{where}: pays {c} but fund {fs} has {fund_left[fs]} left")
            else:
                fund_left[fs] -= c
            paid[cs] += c
    return errs


def append(ledger, entry):
    entries = ledger.setdefault("entries", [])
    entry = dict(entry, seq=len(entries) + 1, prev=entry_hash(entries[-1]) if entries else GENESIS)
    entries.append(entry)
    return entry


def _commit(ledger, entry, credit, units, root):
    e = append(ledger, entry)
    errs = verify(ledger, credit, units, root)
    if errs:
        ledger["entries"].pop()
        raise LedgerError("; ".join(errs))
    return e


def read_ticket(path, as_claim=False):
    """The front matter of a ticket that passes the template; `as_claim` reads a worked example as if cash were picked."""
    with open(path, encoding="utf-8") as f:
        text = f.read()
    t, body = ticketlib.parse(text)
    if as_claim:
        if not t.get("example"):
            raise LedgerError(f"{t.get('id')}: only a worked example may be read as a claim; a real builder's choice stands")
        t = copy.deepcopy(t)
        t["pay_in"] = {"choice": "claim", "claim_amount": t["price"].get("fixed")}
        text = "---\n" + json.dumps(t) + "\n---\n" + body
    errs = ticketlib.check_text(text)
    if errs:
        raise LedgerError(f"{path} fails the ticket template: " + "; ".join(errs))
    return t


def claim(ledger, credit, path, evidence, date, hoster=None, units=None, as_claim=False, root=ROOT):
    """An accepted ticket paid in cash joins the line: its claim is the fixed price, 1x."""
    t = read_ticket(path, as_claim)
    if t["status"] != "accepted":
        raise LedgerError(f"{t['id']} is {t['status']}, not accepted")
    if t["pay_in"]["choice"] != "claim":
        raise LedgerError(f"{t['id']} is paid in {t['pay_in']['choice']}, not a cash claim")
    if hoster is None:
        hoster = next((k for k, h in credit["hosters"].items() if h.get("service") == t.get("service")), None)
    cents = int(round(ticketlib.money(t["pay_in"]["claim_amount"]) * 100))
    entry = {"type": "claim", "kind": "ticket", "date": date, "accepted": date, "holder": t["builder"],
             "hoster": hoster, "ticket": t["id"], "epic": t.get("epic"), "row": t.get("row"),
             "price_cents": int(round(ticketlib.money(t["price"]["fixed"]) * 100)), "cents": cents,
             "evidence": evidence, "source": os.path.relpath(os.path.abspath(path), root)}
    if t.get("example"):
        entry["demonstration"] = True
    return _commit(ledger, entry, credit, units, root)


def bootstrap(ledger, credit, holder, hoster, ref, epic, row, cents, cost_basis, evidence, date, units=None,
              demonstration=False, root=ROOT):
    """Design principle 5: a founder's already-spent cost joins the same line under the same cap, no premium."""
    entry = {"type": "claim", "kind": "bootstrap", "date": date, "accepted": date, "holder": holder, "hoster": hoster,
             "ticket": ref, "epic": epic, "row": row, "cents": cents, "cost_basis": cost_basis, "evidence": evidence}
    if demonstration:
        entry["demonstration"] = True
    return _commit(ledger, entry, credit, units, root)


def settle(ledger, credit, hoster, month, date, units=None, root=ROOT):
    """Fund a closed month from the hoster's books and pay the line, oldest claim first, part by part."""
    got = funding(credit, hoster, month)
    if got is None:
        raise LedgerError(f"{hoster} has no public books for {month} in the credit ledger")
    profit, cost, cash = got
    f = _commit(ledger, {"type": "fund", "date": date, "hoster": hoster, "month": month, "profit_cents": profit,
                         "credit_cost_cents": cost, "cents": cash}, credit, units, root)
    out, left = [f], cash
    for seq, owed in lines(ledger)[0].get(hoster, []):
        if left <= 0:
            break
        part = min(owed, left)
        cl = ledger["entries"][seq - 1]
        out.append(_commit(ledger, {"type": "pay", "date": date, "hoster": hoster, "holder": cl["holder"],
                                    "claim": seq, "fund": f["seq"], "cents": part}, credit, units, root))
        left -= part
    return out


def dollars(c):
    return f"${c / 100:,.2f}"


def report(ledger):
    """One line per claim: holder, ticket, owed, paid, left, in line order."""
    _, paid = lines(ledger)
    rows = []
    for e in ledger["entries"]:
        if e["type"] == "claim":
            p = paid.get(e["seq"], 0)
            state = "paid in full" if p == e["cents"] else ("part paid" if p else "waiting")
            rows.append(f"#{e['seq']} {e['holder']} · {e['ticket']} · claim {dollars(e['cents'])} · paid {dollars(p)} · "
                        f"left {dollars(e['cents'] - p)} · {state}")
    return rows


def demo(root=ROOT):
    """The worked run on tickets/EXAMPLE-1.md (docs/repayment-queue.md): in memory, nothing is written."""
    real = load(os.path.join(root, "ledger", "credit.json"))
    credit = {"hosters": copy.deepcopy(real["hosters"]), "entries": []}
    z = credit["hosters"]["zenod"]["months"]
    z["2026-12"] = dict(z["2026-11"], basis="demo: December assumed equal to November")
    z["2027-01"] = dict(z["2026-11"], basis="demo: January assumed equal to November")
    # Dee, another example builder, spent $20 of credit at Zenod in November: that cost comes off first.
    credit["entries"].append({"type": "honour", "date": "2026-11-28", "hoster": "zenod", "holder": "Dee (example builder)",
                              "cents": 2000})
    L = {"spines": {}, "entries": []}
    ex = os.path.join(root, "tickets", "EXAMPLE-1.md")
    log = []
    claim(L, credit, ex, "tickets/EXAMPLE-1.md (worked example)", "2026-11-26", "zenod", as_claim=True, root=root)
    for who, ref, cents, day in (("Ben (example builder)", "EXAMPLE-2", 1500, "2026-11-27"),
                                 ("Cy (example builder)", "EXAMPLE-3", 1250, "2026-11-29")):
        e = {"type": "claim", "kind": "ticket", "date": day, "accepted": day, "holder": who, "hoster": "zenod",
             "ticket": ref, "epic": "EXAMPLE", "row": ref, "price_cents": cents, "cents": cents,
             "evidence": "illustration", "demonstration": True}
        _commit(L, e, credit, None, root)
    log.append("Line at Zenod: " + ", ".join(f"{e['holder']} {dollars(e['cents'])}" for e in L["entries"]))
    for month, day in (("2026-11", "2026-12-01"), ("2026-12", "2027-01-01"), ("2027-01", "2027-02-01")):
        f, *pays = settle(L, credit, "zenod", month, day, root=root)
        log.append(f"{month}: half of {dollars(f['profit_cents'])} profit = {dollars(f['profit_cents'] // 2)}, "
                   f"less {dollars(f['credit_cost_cents'])} credit served = {dollars(f['cents'])} in; "
                   + ("; ".join(f"{p['holder']} {dollars(p['cents'])}" for p in pays) or "nothing waiting"))
    log += report(L)
    for label, bad in (("paying Ana again", {"type": "pay", "date": "2027-02-01", "hoster": "zenod",
                                             "holder": "Ana (example builder)", "claim": 1, "fund": 7, "cents": 1}),
                       ("a second claim for EXAMPLE-1", dict(L["entries"][0], date="2027-02-01"))):
        try:
            _commit(L, {k: v for k, v in bad.items() if k not in ("seq", "prev")}, credit, None, root)
            log.append(f"NOT refused: {label}")
        except LedgerError as err:
            log.append(f"refused, {label}: {str(err).split(': ', 1)[-1]}")
    return L, log, credit


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--ledger", default=DEFAULT_LEDGER)
    p.add_argument("--credit", default=os.path.join(ROOT, "ledger", "credit.json"))
    p.add_argument("--units", default=os.path.join(ROOT, "ledger", "units.json"))
    sub = p.add_subparsers(dest="cmd", required=True)
    today = dt.date.today().isoformat()
    a = sub.add_parser("claim", help="an accepted ticket paid in cash joins the line")
    a.add_argument("--ticket", required=True); a.add_argument("--evidence", required=True)
    a.add_argument("--hoster"); a.add_argument("--date", default=today)
    b = sub.add_parser("bootstrap", help="a founder's already-spent cost joins the same line (principle 5)")
    for k in ("holder", "hoster", "ref", "epic", "row", "cost-basis", "evidence"):
        b.add_argument("--" + k, required=True)
    b.add_argument("--cents", type=int, required=True); b.add_argument("--date", default=today)
    s = sub.add_parser("settle", help="fund a closed month and pay the line in order")
    s.add_argument("--hoster", required=True); s.add_argument("--month", required=True)
    s.add_argument("--date", default=today)
    sub.add_parser("balance"); sub.add_parser("verify"); sub.add_parser("demo", help="the worked run on EXAMPLE-1")
    args = p.parse_args(argv)
    root = os.path.dirname(os.path.dirname(os.path.abspath(args.ledger)))
    if args.cmd == "demo":
        _, log, _ = demo(root)
        print("\n".join(log))
        return 0
    ledger, credit = load(args.ledger), load(args.credit)
    units = load(args.units) if os.path.exists(args.units) else None
    try:
        if args.cmd == "claim":
            print(json.dumps(claim(ledger, credit, args.ticket, args.evidence, args.date, args.hoster, units, root=root)))
        elif args.cmd == "bootstrap":
            print(json.dumps(bootstrap(ledger, credit, args.holder, args.hoster, args.ref, args.epic, args.row, args.cents,
                                       args.cost_basis, args.evidence, args.date, units, root=root)))
        elif args.cmd == "settle":
            print(json.dumps(settle(ledger, credit, args.hoster, args.month, args.date, units, root)))
        elif args.cmd == "balance":
            print("\n".join(report(ledger)) or "# no claims in line")
            return 0
        else:
            errs = verify(ledger, credit, units, root)
            for e in errs:
                print("FAIL", e)
            if errs:
                return 1
            open_, _ = lines(ledger)
            n = sum(1 for e in ledger["entries"] if e["type"] == "claim")
            print(f"OK: {n} claim(s), {len(ledger['entries'])} entries, chain intact; every claim = its fixed price (1x); "
                  f"paid in line order; none over its price or paid twice; {sum(len(v) for v in open_.values())} waiting")
            return 0
        save(args.ledger, ledger)
    except (LedgerError, KeyError, ticketlib.TicketError) as e:
        print("refused:", e, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
