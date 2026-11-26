#!/usr/bin/env python3
"""Nectary builder credit: price, issue, transfer, request, honour, balance, verify (docs/credit-ledger.md).

Sibling of the units ledger (tools/units.py): same public, append-only JSON with a sha256 hash chain,
same verify approach. Rule (Jordi, EPIC-0-A5, 2026-11-26): an accepted builder is credited
multiple x the ticket's price fixed before work; the multiple (2x now) is reset at most monthly
and only for tickets priced after the reset; credit already issued never shrinks; a hoster honours
credit from at most half its monthly profit and the rest waits in line, in order; cash stays at cost.
Money is held in whole cents. Stdlib only.
"""
import argparse
import datetime as dt
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from units import GENESIS, LedgerError, ROOT, entry_hash, is_done, load, row_status, save  # noqa: E402

DEFAULT_LEDGER = os.path.join(ROOT, "ledger", "credit.json")
ENTRY_TYPES = ("issue", "transfer", "request", "honour")
STEP_UP = 0.25          # an unheld ticket's price rises 25% per 48 h window
CAP_X = 1.5             # never above 1.5x the first estimate
TICKET_MAX = 5000       # never above $50 (cents)


def estimate_cents(runs, run_cost_cents):
    """AI estimate: expected agent runs x run cost, rounded to whole dollars (E0-S13 model.py)."""
    return max(1, int(math.floor(runs * run_cost_cents / 100 + 0.5 + 1e-9))) * 100


def price_cents(est, unheld_windows):
    """Posted price after n unheld 48 h windows: +25% each, capped at 1.5x the estimate and $50."""
    return min(int(round(est * (1 + STEP_UP) ** unheld_windows)), int(round(est * CAP_X)), TICKET_MAX)


def posted_on(tk):
    """The day a ticket was first posted: the multiple in force that day is the one it earns."""
    return tk.get("posted") or tk.get("price_fixed", "")


def multiple_on(ledger, date):
    """The multiple in force on `date`: the last reset dated on or before it."""
    found = None
    for m in ledger.get("multiples", []):
        if m["from"] <= date:
            found = m["multiple"]
    return found


def credit_cents(price, multiple):
    return int(round(price * multiple))


def month_of(date):
    return date[:7]


def room_cents(ledger, hoster, month):
    """Credit (cents) the hoster can still honour this month: half its profit, in credit dollars."""
    rec = ledger["hosters"].get(hoster, {}).get("months", {}).get(month)
    if rec is None:
        return 0
    budget = rec["profit_cents"] / 2 / rec["serve_cost_per_credit_dollar"]
    used = sum(e["cents"] for e in ledger["entries"]
               if e["type"] == "honour" and e["hoster"] == hoster and month_of(e["date"]) == month)
    return int(budget) - used


def state(ledger):
    """Balances (spendable, waiting in line) per holder, and the open queue per hoster."""
    free, waiting, queue = {}, {}, {}
    req = {}
    for e in ledger["entries"]:
        t, h, c = e["type"], e["holder"], e["cents"]
        if t == "issue":
            free[h] = free.get(h, 0) + c
        elif t == "transfer":
            free[h] = free.get(h, 0) - c
            free[e["to"]] = free.get(e["to"], 0) + c
        elif t == "request":
            free[h] = free.get(h, 0) - c
            waiting[h] = waiting.get(h, 0) + c
            req[e["seq"]] = e
            queue.setdefault(e["hoster"], []).append(e["seq"])
        elif t == "honour":
            r = req.get(e.get("request"))
            if r:
                waiting[r["holder"]] = waiting.get(r["holder"], 0) - c
                q = queue.get(r["hoster"], [])
                if e["request"] in q:
                    q.remove(e["request"])
    return free, waiting, queue


def issued_cents(ledger):
    return sum(e["cents"] for e in ledger["entries"] if e["type"] == "issue")


def burned_cents(ledger):
    return sum(e["cents"] for e in ledger["entries"] if e["type"] == "honour")


def verify_setup(ledger):
    errs = []
    last_month = ""
    for i, m in enumerate(ledger.get("multiples", []), 1):
        if not isinstance(m.get("multiple"), (int, float)) or m["multiple"] < 1:
            errs.append(f"multiple {i}: must be a number of at least 1")
        if month_of(m.get("from", "")) <= last_month:
            errs.append(f"multiple {i}: resets at most once a month and in date order")
        if not m.get("source"):
            errs.append(f"multiple {i}: no public source for the reset")
        last_month = month_of(m.get("from", ""))
    for tid, t in ledger.get("tickets", {}).items():
        est = estimate_cents(t["estimate_runs"], t["run_cost_cents"])
        if t["estimate_cents"] != est:
            errs.append(f"ticket {tid}: estimate {t['estimate_cents']} should be {est} ({t['estimate_runs']} runs)")
        want = price_cents(t["estimate_cents"], t.get("unheld_windows", 0))
        if t["price_cents"] != want:
            errs.append(f"ticket {tid}: price {t['price_cents']} breaks the ladder (should be {want})")
        if t["price_cents"] > TICKET_MAX:
            errs.append(f"ticket {tid}: price over $50")
        if not t.get("price_fixed") or not t.get("work_started") or t["price_fixed"] > t["work_started"]:
            errs.append(f"ticket {tid}: price not fixed before work")
        if posted_on(t) > t.get("price_fixed", ""):
            errs.append(f"ticket {tid}: posted after its price was fixed")
        if t.get("hoster") not in ledger.get("hosters", {}):
            errs.append(f"ticket {tid}: unknown hoster {t.get('hoster')!r}")
    return errs


def verify(ledger, root=ROOT):
    """Return a list of problems (empty = consistent)."""
    errs = verify_setup(ledger)
    tickets = ledger.get("tickets", {})
    prev, last_date = GENESIS, ""
    free, waiting, req, issued_tickets, honoured = {}, {}, {}, set(), set()
    queue = {}
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
        c, h = e.get("cents"), e.get("holder")
        if not isinstance(c, int) or c <= 0:
            errs.append(f"{where}: cents must be a positive whole number")
            continue
        if not h:
            errs.append(f"{where}: no holder")
            continue
        if t == "issue":
            tid = e.get("ticket")
            tk = tickets.get(tid)
            if tk is None:
                errs.append(f"{where}: unknown ticket {tid!r}")
                continue
            if tid in issued_tickets:
                errs.append(f"{where}: ticket {tid} already credited")
            issued_tickets.add(tid)
            if e.get("price_cents") != tk["price_cents"]:
                errs.append(f"{where}: price {e.get('price_cents')} is not the price fixed before work ({tk['price_cents']})")
            m = multiple_on(ledger, posted_on(tk))
            if m is None or e.get("multiple") != m:
                errs.append(f"{where}: multiple {e.get('multiple')} is not the one in force when {tid} was posted ({m})")
            if c != credit_cents(tk["price_cents"], m or 0):
                errs.append(f"{where}: credit {c} is not {m} x the fixed price {tk['price_cents']}")
            if d < tk.get("work_started", "9999"):
                errs.append(f"{where}: credited before work started")
            if not e.get("evidence"):
                errs.append(f"{where}: no evidence link")
            if tk.get("demonstration"):
                pass  # a labelled worked example: no spine row to check
            else:
                spine = ledger.get("spines", {}).get(tk.get("epic"))
                status = row_status(os.path.join(root, spine), tk.get("row")) if spine else None
                if not is_done(status):
                    errs.append(f"{where}: {tk.get('row')} is not accepted (done) in its spine (status: {status})")
            free[h] = free.get(h, 0) + c
        elif t == "transfer":
            to = e.get("to")
            if not to or to == h:
                errs.append(f"{where}: transfer needs a receiver other than the sender")
                continue
            if free.get(h, 0) < c:
                errs.append(f"{where}: {h} sends {c} but holds {free.get(h, 0)} spendable")
                continue
            free[h] -= c
            free[to] = free.get(to, 0) + c
        elif t == "request":
            if e.get("hoster") not in ledger.get("hosters", {}):
                errs.append(f"{where}: unknown hoster {e.get('hoster')!r}")
                continue
            if free.get(h, 0) < c:
                errs.append(f"{where}: {h} asks to spend {c} but holds {free.get(h, 0)} spendable")
                continue
            free[h] -= c
            waiting[h] = waiting.get(h, 0) + c
            req[i] = e
            queue.setdefault(e["hoster"], []).append(i)
        else:  # honour: the hoster serves a whole request; the credit is burned
            r = req.get(e.get("request"))
            if r is None or e.get("request") in honoured:
                errs.append(f"{where}: honours no open request ({e.get('request')})")
                continue
            if e.get("hoster") != r["hoster"] or h != r["holder"] or c != r["cents"]:
                errs.append(f"{where}: does not match request {e['request']} (hoster, holder and whole amount)")
                continue
            q = queue[r["hoster"]]
            if q[0] != e["request"]:
                errs.append(f"{where}: request {e['request']} jumps the line (request {q[0]} waits first)")
            rec = ledger["hosters"][r["hoster"]].get("months", {}).get(month_of(d))
            if rec is None:
                errs.append(f"{where}: {r['hoster']} has no public profit for {month_of(d)}")
            else:
                budget = int(rec["profit_cents"] / 2 / rec["serve_cost_per_credit_dollar"])
                used = sum(x["cents"] for x in ledger["entries"][:i]
                           if x["type"] == "honour" and x.get("hoster") == r["hoster"] and month_of(x["date"]) == month_of(d))
                if used > budget:
                    errs.append(f"{where}: {r['hoster']} honours {used} in {month_of(d)}, over half its profit ({budget})")
            honoured.add(e["request"])
            q.remove(e["request"])
            waiting[h] -= c
    return errs


def append(ledger, entry):
    entries = ledger.setdefault("entries", [])
    entry = dict(entry, seq=len(entries) + 1, prev=entry_hash(entries[-1]) if entries else GENESIS)
    entries.append(entry)
    return entry


def _commit(ledger, entry, root):
    e = append(ledger, entry)
    errs = verify(ledger, root)
    if errs:
        ledger["entries"].pop()
        raise LedgerError("; ".join(errs))
    return e


def price(ledger, tid, hoster, runs, date, work_started, run_cost_cents=120, unheld_windows=0,
          epic=None, row=None, demonstration=False, note="", posted=None, source=None):
    """Fix a ticket's price before work. The template (docs/ticket-template.md) supplies these fields."""
    if tid in ledger.setdefault("tickets", {}):
        raise LedgerError(f"ticket {tid} already priced; a re-quote happens only when the hoster changes the ticket")
    est = estimate_cents(runs, run_cost_cents)
    tk = {"hoster": hoster, "epic": epic, "row": row, "estimate_runs": runs, "run_cost_cents": run_cost_cents,
          "estimate_cents": est, "unheld_windows": unheld_windows, "price_cents": price_cents(est, unheld_windows),
          "posted": posted or date, "price_fixed": date, "work_started": work_started,
          "multiple_at_posting": multiple_on(ledger, posted or date)}
    if demonstration:
        tk["demonstration"] = True
    if note:
        tk["note"] = note
    if source:
        tk["source"] = source
    ledger["tickets"][tid] = tk
    errs = verify_setup(ledger)
    if errs:
        del ledger["tickets"][tid]
        raise LedgerError("; ".join(errs))
    return tk


def from_ticket(ledger, path, hoster=None):
    """Price a ticket from its template file (docs/ticket-template.md, checked by tools/ticket.py)."""
    import ticket  # E0-S2's validator: the template is the one source of a ticket's price
    errs = ticket.check_file(path)
    if errs:
        raise LedgerError(f"{path} fails the ticket template: " + "; ".join(errs))
    with open(path, encoding="utf-8") as f:
        t, _ = ticket.parse(f.read())
    if t["pay_in"]["choice"] not in ("credit", "open"):
        raise LedgerError(f"{t['id']} is paid in {t['pay_in']['choice']}, not credit")
    p = t["price"]
    if "fixed" not in p or "held_at" not in p:
        raise LedgerError(f"{t['id']} is not held yet: its price is not fixed")
    if hoster is None:
        hoster = next((k for k, h in ledger["hosters"].items() if h.get("service") == t.get("service")), None)
    ladder = ticket.ladder(p["posted"])
    windows = ladder.index(ticket.money(p["fixed"]))
    day = p["held_at"][:10]
    tk = price(ledger, t["id"], hoster, p["estimate"]["runs"], day, day, int(round(p["estimate"]["run_cost"] * 100)),
               windows, t.get("epic"), t.get("row"), demonstration=bool(t.get("example")),
               posted=p["posted_at"][:10], source=os.path.relpath(os.path.abspath(path), ROOT))
    want = multiple_on(ledger, tk["posted"])
    if t.get("credit", {}).get("multiple") not in (None, want):
        del ledger["tickets"][t["id"]]
        raise LedgerError(f"{t['id']} says multiple {t['credit']['multiple']}, the ledger's for its posting day is {want}")
    if tk["price_cents"] != int(round(p["fixed"] * 100)):
        del ledger["tickets"][t["id"]]
        raise LedgerError(f"{t['id']} fixed price {p['fixed']} differs from the ledger's ladder ({tk['price_cents']} cents)")
    return tk


def issue(ledger, holder, tid, evidence, date, inference_cents=None, root=ROOT):
    """Credit an accepted builder multiple x the fixed price. Real inference is recorded, never used."""
    tk = ledger["tickets"][tid]
    m = multiple_on(ledger, posted_on(tk))
    entry = {"type": "issue", "date": date, "holder": holder, "ticket": tid, "price_cents": tk["price_cents"],
             "multiple": m, "cents": credit_cents(tk["price_cents"], m or 0), "evidence": evidence}
    if inference_cents is not None:
        entry["inference_cents"] = inference_cents
    return _commit(ledger, entry, root)


def transfer(ledger, holder, to, cents, date, note="", root=ROOT):
    return _commit(ledger, {"type": "transfer", "date": date, "holder": holder, "to": to, "cents": cents, "note": note}, root)


def honour_queue(ledger, hoster, date, root=ROOT):
    """Serve waiting requests at `hoster` in order while this month's half-profit room lasts."""
    out = []
    _, _, queue = state(ledger)
    for seq in list(queue.get(hoster, [])):
        r = ledger["entries"][seq - 1]
        if r["cents"] > room_cents(ledger, hoster, month_of(date)):
            break  # in order: a later request never jumps one that does not fit
        out.append(_commit(ledger, {"type": "honour", "date": date, "holder": r["holder"], "hoster": hoster,
                                    "request": seq, "cents": r["cents"]}, root))
    return out


def spend(ledger, holder, hoster, cents, date, note="", root=ROOT):
    """Ask to spend credit at a hoster: it waits in line, then is honoured (burned) if this month's room allows."""
    r = _commit(ledger, {"type": "request", "date": date, "holder": holder, "hoster": hoster, "cents": cents, "note": note}, root)
    done = honour_queue(ledger, hoster, date, root)
    return r, done


def dollars(c):
    return f"${c / 100:,.2f}"


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--ledger", default=DEFAULT_LEDGER)
    sub = p.add_subparsers(dest="cmd", required=True)
    today = dt.date.today().isoformat()
    a = sub.add_parser("price", help="fix a ticket's price before work")
    a.add_argument("--ticket", required=True); a.add_argument("--hoster", required=True)
    a.add_argument("--runs", type=float, required=True); a.add_argument("--run-cost-cents", type=int, default=120)
    a.add_argument("--unheld-windows", type=int, default=0); a.add_argument("--work-started", required=True)
    a.add_argument("--epic"); a.add_argument("--row"); a.add_argument("--date", default=today)
    f = sub.add_parser("from-ticket", help="fix a ticket's price from its template file (tickets/*.md)")
    f.add_argument("path"); f.add_argument("--hoster")
    b = sub.add_parser("issue", help="credit an accepted builder")
    b.add_argument("--holder", required=True); b.add_argument("--ticket", required=True)
    b.add_argument("--evidence", required=True); b.add_argument("--inference-cents", type=int)
    b.add_argument("--date", default=today)
    t = sub.add_parser("transfer")
    t.add_argument("--from", dest="holder", required=True); t.add_argument("--to", required=True)
    t.add_argument("--cents", type=int, required=True); t.add_argument("--note", default="")
    t.add_argument("--date", default=today)
    s = sub.add_parser("spend", help="spend credit at a hoster (waits in line beyond half its profit)")
    s.add_argument("--holder", required=True); s.add_argument("--hoster", required=True)
    s.add_argument("--cents", type=int, required=True); s.add_argument("--note", default="")
    s.add_argument("--date", default=today)
    h = sub.add_parser("honour", help="serve the line at a hoster with this month's room")
    h.add_argument("--hoster", required=True); h.add_argument("--date", default=today)
    sub.add_parser("balance")
    sub.add_parser("verify")
    args = p.parse_args(argv)
    ledger = load(args.ledger)
    root = os.path.dirname(os.path.dirname(os.path.abspath(args.ledger)))
    try:
        if args.cmd == "price":
            print(json.dumps(price(ledger, args.ticket, args.hoster, args.runs, args.date, args.work_started,
                                   args.run_cost_cents, args.unheld_windows, args.epic, args.row)))
        elif args.cmd == "from-ticket":
            print(json.dumps(from_ticket(ledger, args.path, args.hoster)))
        elif args.cmd == "issue":
            print(json.dumps(issue(ledger, args.holder, args.ticket, args.evidence, args.date, args.inference_cents, root)))
        elif args.cmd == "transfer":
            print(json.dumps(transfer(ledger, args.holder, args.to, args.cents, args.date, args.note, root)))
        elif args.cmd == "spend":
            r, done = spend(ledger, args.holder, args.hoster, args.cents, args.date, args.note, root)
            print(json.dumps({"request": r, "honoured": done}))
        elif args.cmd == "honour":
            print(json.dumps(honour_queue(ledger, args.hoster, args.date, root)))
        elif args.cmd == "balance":
            free, waiting, queue = state(ledger)
            for who in sorted(set(free) | set(waiting)):
                print(f"{who}\tspendable {dollars(free.get(who, 0))}\twaiting in line {dollars(waiting.get(who, 0))}")
            print(f"# issued {dollars(issued_cents(ledger))}, burned {dollars(burned_cents(ledger))}")
            return 0
        else:
            errs = verify(ledger, root)
            for e in errs:
                print("FAIL", e)
            if errs:
                return 1
            n = len(ledger["entries"])
            _, _, queue = state(ledger)
            line = sum(len(q) for q in queue.values())
            print(f"OK: {len(ledger['tickets'])} priced tickets, {n} entries, chain intact; every credit = multiple in force "
                  f"at posting x the fixed price; issued {dollars(issued_cents(ledger))}, burned {dollars(burned_cents(ledger))}, "
                  f"{line} request(s) waiting in line; no hoster over half its monthly profit; no negative balances")
            return 0
        save(args.ledger, ledger)
    except (LedgerError, KeyError) as e:
        print("refused:", e, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
