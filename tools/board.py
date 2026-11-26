#!/usr/bin/env python3
"""Nectary ticket board: every ticket in tickets/ with its price set before work and its credit.

Builds two files from tickets/*.md (docs/ticket-template.md), checked with tools/ticket.py:
  site/units/board/tickets.json   the feed agents read
  site/units/board/index.html     the page people open (served on :8974/board/)

Only tickets that pass `tools/ticket.py check` are listed; the others are listed apart with
their errors. Rule (Jordi, EPIC-0-A5, 2026-11-26): credit is the multiple x the price fixed
before work; an unheld ticket's price rises 25% per 48 h, never above 1.5x or $50.

  python3 tools/board.py              build both files
  python3 tools/board.py --now 2026-11-30T10:00Z --out /tmp/board
Stdlib only.
"""
import argparse
import datetime as dt
import glob
import html
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ticket  # noqa: E402
from units_page import CSS  # noqa: E402

ROOT = ticket.ROOT
TICKETS = os.path.join(ROOT, "tickets")
OUT = os.path.join(ROOT, "site", "units", "board")
CREDIT_LEDGER = os.path.join(ROOT, "ledger", "credit.json")
REPO = "https://github.com/nectary-dev/nectary/blob/main/"
STATES = ("posted", "held", "submitted", "accepted", "paid")
OPEN = ("posted",)
FMT = "%Y-%m-%dT%H:%MZ"


def credited(ledger_path=CREDIT_LEDGER):
    """{ticket id: (holder, cents)} for every credit issued in the ledger (E0-S10)."""
    try:
        with open(ledger_path, encoding="utf-8") as f:
            entries = json.load(f).get("entries", [])
    except (OSError, ValueError):
        return {}
    return {e["ticket"]: (e["holder"], e["cents"]) for e in entries if e.get("type") == "issue" and e.get("ticket")}


def state_of(t, paid):
    """The board's state: the ticket's own status, `paid` once the ledger has issued its credit."""
    if t["status"] == "accepted" and t["id"] in paid:
        return "paid"
    return t["status"]


def price_now(t, now):
    """(current price, next step time or None, price after that step or None)."""
    p = t["price"]
    if "fixed" in p:
        return ticket.money(p["fixed"]), None, None
    lad = ticket.ladder(p["posted"])
    posted_at = ticket.when(p["posted_at"])
    steps = max(0, int((now - posted_at).total_seconds() // (ticket.STEP_HOURS * 3600)))
    i = min(steps, len(lad) - 1)
    if i + 1 < len(lad):
        nxt = posted_at + dt.timedelta(hours=ticket.STEP_HOURS * (i + 1))
        return lad[i], nxt.strftime(FMT), lad[i + 1]
    return lad[i], None, None


def entry(t, path, now, paid):
    p, c = t["price"], t["credit"]
    current, next_at, next_price = price_now(t, now)
    fixed = "fixed" in p
    amount = ticket.money(c["amount"]) if "amount" in c else ticket.money(c["multiple"] * current)
    acc = t["acceptance"]
    return {
        "id": t["id"],
        "title": t["title"],
        "example": bool(t.get("example")),
        "state": state_of(t, paid),
        "status": t["status"],
        "hoster": t["hoster"],
        "service": t["service"],
        "deliverable": t["deliverable"],
        "price": {
            "currency": p["currency"],
            "current": current,
            "fixed": fixed,
            "estimate": ticket.money(p["estimate"]["amount"]),
            "estimate_runs": p["estimate"]["runs"],
            "posted": ticket.money(p["posted"]),
            "posted_at": p["posted_at"],
            "cap": ticket.money(p["price_cap"]),
            "ladder": ticket.ladder(p["posted"]),
            "next_step_at": next_at,
            "next_price": next_price,
        },
        "credit": {
            "multiple": c["multiple"],
            "amount": amount,
            "final": fixed,
            "issued": ticket.money(paid[t["id"]][1] / 100) if t["id"] in paid else None,
        },
        "pay_in": t["pay_in"]["choice"],
        "tests": {
            "own": [{"id": x["id"], "checks": x["checks"], "cmd": x["cmd"]} for x in acc["tests"]],
            "hidden": acc["hidden_tests"]["count"],
            "jury": f'{acc["jury"]["pass"]} of {acc["jury"]["models"]}',
        },
        "holder": t.get("builder"),
        "held_since": p.get("held_at"),
        "hold_until": None,
        "path": os.path.relpath(path, ROOT),
    }


def collect(paths, now, ledger_path=CREDIT_LEDGER):
    """(listed tickets, failed tickets) for the board."""
    schema, paid = ticket.load_schema(), credited(ledger_path)
    listed, failed = [], []
    for path in sorted(paths):
        with open(path, encoding="utf-8") as f:
            text = f.read()
        errs = ticket.check_text(text, schema)
        if errs:
            failed.append({"path": os.path.relpath(path, ROOT), "errors": errs})
            continue
        listed.append(entry(ticket.parse(text)[0], path, now, paid))
    order = {s: i for i, s in enumerate(STATES)}
    listed.sort(key=lambda e: (order.get(e["state"], len(STATES)), e["id"]))
    return listed, failed


def feed(listed, failed, now):
    return {
        "board": "nectary-ticket-board/1",
        "built_at": now.strftime(FMT),
        "rule": "credit = multiple x the price fixed before work; an unheld ticket's price rises 25% per 48 h, "
                "never above 1.5x the posted price or $50; cash claims never pay more than the fixed price",
        "states": list(STATES),
        "counts": {s: sum(e["state"] == s for e in listed) for s in STATES},
        "tickets": listed,
        "failed": failed,
        "ledger_page": "../credit.html#credit",
    }


def esc(x):
    return html.escape(str(x if x is not None else ""))


def usd(x):
    return f"${x:,.2f}".replace(".00", "")


def short(s):
    """26 Nov 15:40 UTC from 2026-11-26T15:40Z."""
    return ticket.when(s).strftime("%-d %b %H:%M UTC") if s else ""


def flow_svg(counts, tall=False):
    out, n = "", len(STATES)
    if tall:
        w, h, gap = 300, 50, 16
        for i, s in enumerate(STATES):
            y = i * (h + gap)
            on = counts[s] > 0
            fill, ink = ("#1f5135", "#f5f1e8") if on else ("#fbf8f1", "#1d1b16")
            out += (f'<rect x="0" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="#1d1b16"/>'
                    f'<text x="16" y="{y + 31}" fill="{ink}" font-family="Newsreader,Georgia,serif" font-size="20">{s.title()}</text>'
                    f'<text x="{w - 16}" y="{y + 31}" text-anchor="end" fill="{ink}" font-size="15">{counts[s]}</text>')
            if i:
                out += f'<path d="M{w / 2} {y - gap + 2} V{y - 3} M{w / 2 - 5} {y - 8} L{w / 2} {y - 3} L{w / 2 + 5} {y - 8}" stroke="#1d1b16" fill="none"/>'
        return f'<svg class="flow tall" viewBox="0 0 {w} {n * h + (n - 1) * gap}" role="img" aria-label="Tickets by state, top to bottom">{out}</svg>'
    w, gap = 150, 22
    for i, s in enumerate(STATES):
        x = i * (w + gap)
        on = counts[s] > 0
        fill, ink = ("#1f5135", "#f5f1e8") if on else ("#fbf8f1", "#1d1b16")
        out += (f'<rect x="{x}" y="0" width="{w}" height="64" fill="{fill}" stroke="#1d1b16"/>'
                f'<text x="{x + w / 2}" y="28" text-anchor="middle" fill="{ink}" font-family="Newsreader,Georgia,serif" font-size="19">{s.title()}</text>'
                f'<text x="{x + w / 2}" y="50" text-anchor="middle" fill="{ink}" font-size="14">{counts[s]} ticket{"s" if counts[s] != 1 else ""}</text>')
        if i:
            out += f'<path d="M{x - gap + 3} 32 H{x - 4} M{x - 9} 27 L{x - 4} 32 L{x - 9} 37" stroke="#1d1b16" fill="none"/>'
    label = ", ".join(f"{s} {counts[s]}" for s in STATES)
    return f'<svg class=flow viewBox="0 0 {n * w + (n - 1) * gap} 64" role="img" aria-label="Tickets by state: {label}">{out}</svg>'


def card(e):
    p, c, t = e["price"], e["credit"], e["tests"]
    if p["fixed"]:
        price_line = f"Fixed at {usd(p['current'])} when held. Posted {usd(p['posted'])}, cap {usd(p['cap'])}."
    elif p["next_step_at"]:
        price_line = f"Rises to {usd(p['next_price'])} on {short(p['next_step_at'])} if nobody holds it. Cap {usd(p['cap'])}."
    else:
        price_line = f"At its cap of {usd(p['cap'])}."
    credit_line = (f"{c['multiple']:g}x the fixed price" + (f", issued {usd(c['issued'])}" if c["issued"] is not None else "")
                   if c["final"] else f"{c['multiple']:g}x the price when held")
    holder = (f"{esc(e['holder'])}, since {short(e['held_since'])}. No hold limit set."
              if e["holder"] else "Nobody yet. The first builder to hold it fixes the price.")
    tests = "".join(f"<li><b>{esc(x['id'])}</b> {esc(x['checks'])}</li>" for x in t["own"])
    return f"""<article class=tk id="{esc(e['id'])}">
<p class=meta>{esc(e['id'])}{' · example' if e['example'] else ''} · {esc(e['service'])}</p>
<h3>{esc(e['title'])}</h3>
<div class=nums><div><small>Price</small><b>{usd(p['current'])}</b></div><div><small>Credit</small><b>{usd(c['amount'])}</b></div><div><small>State</small><b class=st>{esc(e['state'].title())}</b></div></div>
<table>
<tr><th>Price</th><td>{esc(price_line)} Estimate {p['estimate_runs']} agent runs, {usd(p['estimate'])}.</td></tr>
<tr><th>Credit</th><td>{esc(credit_line)}.</td></tr>
<tr><th>Held by</th><td>{holder}</td></tr>
<tr><th>Tests</th><td>{len(t['own'])} own, {t['hidden']} hidden, jury {esc(t['jury'])}<ul>{tests}</ul></td></tr>
</table>
<p class=meta><a href="{REPO}{esc(e['path'])}">The full ticket</a> · <a href="tickets.json">as JSON</a></p>
</article>"""


BOARD_CSS = """.tk{border:1px solid #1d1b16;background:#fbf8f1;padding:16px 20px;margin:18px 0}
.tk h3{margin:2px 0 12px}.tk th{width:90px;vertical-align:top}.tk ul{margin:6px 0 0;padding-left:18px;font-size:14px;color:#3a372f}
.nums{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin:0 0 8px}
.nums b{display:block;font-family:Newsreader,Georgia,serif;font-size:30px;font-weight:500;color:#1f5135}.nums .st{font-size:22px;color:#1d1b16}
.tk:target{outline:3px solid #1f5135}
"""


def page(fd):
    listed, failed, counts = fd["tickets"], fd["failed"], fd["counts"]
    open_n = sum(counts[s] for s in OPEN)
    first = listed[0] if listed else None
    punch = (f"{len(listed)} ticket{'s' if len(listed) != 1 else ''} on the board, {open_n} open to hold. "
             + (f"{esc(first['id'])} is priced {usd(first['price']['current'])} and pays {usd(first['credit']['amount'])} of credit."
                if first else ""))
    cards = "".join(card(e) for e in listed) or "<p>No tickets yet.</p>"
    fails = ("".join(f"<li><b>{esc(f['path'])}</b><span>{'<br>'.join(esc(x) for x in f['errors'])}</span></li>" for f in failed)
             if failed else "")
    fail_block = (f"<h2>Not listed: failed the ticket check</h2><ol class=fails>{fails}</ol>" if failed
                  else "<p class=ok>✓ Every ticket in the folder passes the ticket check.</p>")
    return f"""<!doctype html><html lang=en><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>Nectary ticket board</title>
<style>
{CSS}{BOARD_CSS}</style>
<main>
<p class=meta><a href="../">Nectary units</a> · <a href="../credit.html#credit">builder credit</a> · ticket board</p>
<h1>Ticket board</h1>
<p class=punch>{punch}</p>
{flow_svg(counts)}{flow_svg(counts, tall=True)}
<p class=meta>Each price is set before work. If nobody holds a ticket in 48 hours its price rises 25%, never above 1.5x or $50. An accepted builder gets the multiple times the fixed price as service credit, paid through the <a href="../credit.html#credit">credit ledger</a>. Agents read <a href="tickets.json">tickets.json</a>.</p>
{fail_block}
<h2>Tickets</h2>
{cards}
<footer>Built {esc(short(fd['built_at']))} from <a href="{REPO}tickets/">tickets/</a> · template <a href="{REPO}docs/ticket-template.md">docs/ticket-template.md</a> · not legal, tax or accounting advice.</footer>
</main></html>
"""


def build(out=OUT, now=None, paths=None, ledger_path=CREDIT_LEDGER):
    now = now or dt.datetime.now(dt.timezone.utc).replace(second=0, microsecond=0, tzinfo=None)
    paths = glob.glob(os.path.join(TICKETS, "*.md")) if paths is None else paths
    listed, failed = collect(paths, now, ledger_path)
    fd = feed(listed, failed, now)
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "tickets.json"), "w", encoding="utf-8") as f:
        json.dump(fd, f, indent=2, ensure_ascii=False)
        f.write("\n")
    with open(os.path.join(out, "index.html"), "w", encoding="utf-8") as f:
        f.write(page(fd))
    return fd


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--now", help="build as of this time, YYYY-MM-DDTHH:MMZ (default: now)")
    a = ap.parse_args(argv)
    fd = build(a.out, ticket.when(a.now) if a.now else None)
    print(f"{a.out}: {len(fd['tickets'])} listed, {len(fd['failed'])} failed the check")
    return 0


if __name__ == "__main__":
    sys.exit(main())
