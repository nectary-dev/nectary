#!/usr/bin/env python3
"""Build site/units/index.html from ledger/units.json (the page Jordi opens). Stdlib only."""
import html
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import units  # noqa: E402
import credit  # noqa: E402

OUT = os.path.join(units.ROOT, "site", "units", "index.html")
CSS = """body{margin:0;background:#f5f1e8;color:#1d1b16;font:16px/1.5 "Instrument Sans",system-ui,sans-serif}
main{max-width:880px;margin:0 auto;padding:40px 24px 64px}
h1,h2,h3{font-family:Newsreader,Georgia,serif;font-weight:500;margin:0}
h1{font-size:40px;line-height:1.1} h2{font-size:26px;margin:44px 0 12px} h3{font-size:20px;margin:18px 0 6px}
small{font:14px "Instrument Sans",system-ui,sans-serif} a{color:#1f5135}
.lede{font-size:19px;max-width:680px;color:#3a372f}
.unit{border:1px solid #1d1b16;padding:16px 20px;margin:24px 0;background:#fbf8f1}
.unit b{font-family:Newsreader,Georgia,serif;font-size:24px;font-weight:500;color:#1f5135}
ol{padding:0;list-style:none;display:grid;grid-template-columns:1fr 1fr;gap:10px 28px}
ol li{border-top:1px solid #cfc7b5;padding-top:8px} ol b{display:block} ol span{color:#4a463c;font-size:15px}
table{width:100%;border-collapse:collapse;font-size:15px;margin:6px 0}
th,td{text-align:left;padding:7px 8px;border-bottom:1px solid #d8d0bf} th{font-weight:600;color:#4a463c}
.n{text-align:right;font-variant-numeric:tabular-nums}
.bar{height:10px;background:#e4dccb} .bar i{display:block;height:100%;background:#1f5135}
.meta{color:#4a463c;margin:6px 0} .ok{color:#1f5135;font-weight:600} .bad{color:#8a2a1b;font-weight:600}
.tr td{background:#eef3ec} .sum td{font-weight:600;border-top:2px solid #1d1b16}
.punch{font-family:Newsreader,Georgia,serif;font-size:22px;line-height:1.3;border:1px solid #1d1b16;background:#fbf8f1;padding:14px 18px;margin:12px 0 18px}
.flow{width:100%;height:auto;margin:6px 0 14px;font-family:"Instrument Sans",system-ui,sans-serif}
.flow.tall{display:none;max-width:340px} .tw{overflow-x:auto}
.pair{display:grid;grid-template-columns:1fr 1fr;gap:20px} .pair p{margin:4px 0;font-size:15px;color:#3a372f}
:target{scroll-margin-top:12px}
.risk{border-left:4px solid #8a2a1b;background:#fbf8f1;padding:12px 16px;margin:28px 0;font-size:15px}
footer{margin-top:48px;color:#6a655a;font-size:14px}
@media(max-width:640px){ol,.pair{grid-template-columns:1fr} .flow{display:none} .flow.tall{display:block} .ok{font-size:15px}}
"""
REPO = "https://github.com/nectary-dev/nectary/blob/main/"

RULES = [
    ("Priced in a service", "One unit buys 1,000 Zenod memory operations. Never a price in dollars or euros."),
    ("Only for accepted tickets", "Units are awarded when a ticket is accepted as done, never per line or pull request."),
    ("Rate fixed before work", "Each ticket's units are written in the ledger before anyone starts it."),
    ("Your choice per ticket", "Take units, or a capped revenue claim repaid at cost. One or the other, never both."),
    ("Public cap per epic", "Each epic can issue only the total written in the ledger."),
    ("Transferable between holders", "A holder can send units to anyone. Never more than they hold, never to themselves."),
    ("Burned when spent", "Spending destroys the units, so supply only shrinks with use."),
    ("Never sold or listed by us", "The project never sells units, never lists them on an exchange, never talks about their price."),
    ("Same rules for the team", "The team's own units follow the same rates and caps."),
]


def esc(x):
    return html.escape(str(x if x is not None else ""))


def link(url, label):
    return f'<a href="{esc(url)}">{esc(label)}</a>' if url else esc(label)


STEPS = [("Priced", "before work"), ("Accepted", "row done"), ("Credit 2x", "the fixed price"),
         ("Spent", "at a hoster"), ("Honoured", "from half its profit")]


def flow_svg():
    w, gap = 150, 22
    boxes = ""
    for i, (a, b) in enumerate(STEPS):
        x = i * (w + gap)
        fill = "#1f5135" if i == 2 else "#fbf8f1"
        ink = "#f5f1e8" if i == 2 else "#1d1b16"
        boxes += (f'<rect x="{x}" y="0" width="{w}" height="64" fill="{fill}" stroke="#1d1b16"/>'
                  f'<text x="{x + w / 2}" y="28" text-anchor="middle" fill="{ink}" font-family="Newsreader,Georgia,serif" font-size="19">{a}</text>'
                  f'<text x="{x + w / 2}" y="49" text-anchor="middle" fill="{ink}" font-size="13">{b}</text>')
        if i:
            ax = x - gap
            boxes += f'<path d="M{ax + 3} 32 H{x - 4} M{x - 9} 27 L{x - 4} 32 L{x - 9} 37" stroke="#1d1b16" fill="none"/>'
    total = len(STEPS) * w + (len(STEPS) - 1) * gap
    return (f'<svg class=flow viewBox="0 0 {total} 64" role="img" aria-label="Priced before work, accepted, credit 2x the fixed price, '
            f'spent at a hoster, honoured from half its profit">{boxes}</svg>')


def flow_svg_tall():
    h, gap, w = 52, 18, 300
    out = ""
    for i, (a, b) in enumerate(STEPS):
        y = i * (h + gap)
        fill = "#1f5135" if i == 2 else "#fbf8f1"
        ink = "#f5f1e8" if i == 2 else "#1d1b16"
        out += (f'<rect x="0" y="{y}" width="{w}" height="{h}" fill="{fill}" stroke="#1d1b16"/>'
                f'<text x="16" y="{y + 32}" fill="{ink}" font-family="Newsreader,Georgia,serif" font-size="20">{a}</text>'
                f'<text x="{w - 16}" y="{y + 32}" text-anchor="end" fill="{ink}" font-size="14">{b}</text>')
        if i:
            out += f'<path d="M{w / 2} {y - gap + 2} V{y - 3} M{w / 2 - 5} {y - 8} L{w / 2} {y - 3} L{w / 2 + 5} {y - 8}" stroke="#1d1b16" fill="none"/>'
    total = len(STEPS) * h + (len(STEPS) - 1) * gap
    return f'<svg class="flow tall" viewBox="0 0 {w} {total}" role="img" aria-label="The same five steps, top to bottom">{out}</svg>'


def credit_section(cl):
    errs = credit.verify(cl)
    free, waiting, queue = credit.state(cl)
    d = credit.dollars
    m = cl["multiples"][-1]
    tick = "".join(
        f"<tr><td>{esc(t)}{' · example' if v.get('demonstration') else ''}</td><td class=n>{d(v['estimate_cents'])}</td>"
        f"<td class=n>{d(v['price_cents'])}</td><td>{esc(v['posted'])}</td><td class=n>{esc(v.get('multiple_at_posting'))}x</td></tr>"
        for t, v in cl["tickets"].items())
    ents = ""
    for e in cl["entries"]:
        if e["type"] == "issue":
            what = (f"Credit for {esc(e['ticket'])}: {e['multiple']}x {d(e['price_cents'])}"
                    + (f" · spent {d(e['inference_cents'])} of inference, not counted" if e.get("inference_cents") else ""))
            n = "+" + d(e["cents"])
        elif e["type"] == "transfer":
            what, n = f"Sent to {esc(e['to'])}", d(e["cents"])
        elif e["type"] == "request":
            what, n = f"Asked to spend at {esc(e['hoster'])}, waits in line", d(e["cents"])
        else:
            what, n = f"Honoured by {esc(e['hoster'])}, burned", "−" + d(e["cents"])
        ents += f"<tr><td>{e['seq']}</td><td>{esc(e['date'])}</td><td>{esc(e['holder'])}</td><td>{what}</td><td class=n>{n}</td></tr>"
    bal = "".join(f"<tr><td>{esc(h)}</td><td class=n>{d(free.get(h, 0))}</td><td class=n>{d(waiting.get(h, 0))}</td></tr>"
                  for h in sorted(set(free) | set(waiting)))
    host = ""
    for name, h in cl["hosters"].items():
        for month, r in h.get("months", {}).items():
            budget = int(r["profit_cents"] / 2 / r["serve_cost_per_credit_dollar"])
            left = credit.room_cents(cl, name, month)
            host += (f"<tr><td>{esc(h.get('name', name))} {esc(month)}</td><td class=n>{d(r['profit_cents'])}</td>"
                     f"<td class=n>{d(r['profit_cents'] // 2)}</td><td class=n>{d(budget)}</td><td class=n>{d(left)}</td>"
                     f"<td class=n>{len(queue.get(name, []))}</td></tr><tr><td colspan=6 class=meta>{esc(r.get('basis', ''))}</td></tr>")
    ok = (f"<p class=ok>✓ Credit ledger checks pass: hash chain intact, every credit is the multiple of its posting month times the price fixed before work, no hoster over half its monthly profit, no negative balances.</p>"
          if not errs else "<p class=bad>✗ Credit check failed:<br>" + "<br>".join(map(esc, errs)) + "</p>")
    return f"""<section id=credit>
<h1>Builder credit</h1>
<p class=punch>An accepted builder gets 2x the ticket's price fixed before work, as hoster service. A $10 ticket pays $20 of credit.</p>
{flow_svg()}{flow_svg_tall()}
{ok}
<div class=pair>
<div><h3>Builder</h3><p>Ana's agent spends $8.40 on a $10 ticket and gets $20. Ben's spends $13.20 and still gets $20. The price is known before work, so burning more inference never earns more.</p></div>
<div><h3>Hoster</h3><p>Serving $1 of credit costs Zenod about 47 cents. It honours credit from at most half its monthly profit. What does not fit waits in line, in order, for next month.</p></div>
</div>
<p class=meta>Multiple now: <b>{m['multiple']}x</b> since {esc(m['from'])}. It is reset at most monthly from public books and only for tickets posted after the reset. Credit already issued never shrinks. Cash never pays more than the ticket's fixed price. Spending at Zenod is not switched on yet: it waits for your yes on the parked spend step.</p>
<h3>Ledger</h3>
<div class=tw><table><tr><th>#</th><th>Date</th><th>Holder</th><th>What</th><th class=n>Credit</th></tr>{ents or "<tr><td colspan=5>None yet</td></tr>"}</table></div>
<h3>Balances</h3>
<div class=tw><table><tr><th>Holder</th><th class=n>Spendable</th><th class=n>Waiting in line</th></tr>{bal or "<tr><td colspan=3>None yet</td></tr>"}</table></div>
<h3>Tickets priced before work</h3>
<div class=tw><table><tr><th>Ticket</th><th class=n>Estimate</th><th class=n>Fixed price</th><th>Posted</th><th class=n>Multiple</th></tr>{tick}</table></div>
<h3>Hoster room this month</h3>
<div class=tw><table><tr><th>Hoster</th><th class=n>Profit</th><th class=n>Half</th><th class=n>Credit it can honour</th><th class=n>Left</th><th class=n>In line</th></tr>{host}</table></div>
<p class=meta>Rules in <a href="{REPO}docs/credit-ledger.md">docs/credit-ledger.md</a>, ledger in <a href="{REPO}ledger/credit.json">ledger/credit.json</a>, numbers on the <a href="http://vps3.taild81fbb.ts.net:8976/">economics page</a>.</p>
</section>"""


def build_credit(cl):
    return f"""<!doctype html><html lang=en><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>Nectary builder credit</title>
<style>
{CSS}</style>
<main>
<p class=meta><a href="./">Nectary units</a> · builder credit</p>
{credit_section(cl)}
<footer>Built from <a href="{REPO}ledger/credit.json">ledger/credit.json</a> · not legal, tax or accounting advice.</footer>
</main></html>
"""


def build(ledger, cl=None):
    errs = units.verify(ledger)
    bal = units.balances(ledger)
    u = ledger["unit"]
    rules = "".join(f"<li><b>{esc(t)}</b><span>{esc(d)}</span></li>" for t, d in RULES)
    caps = ""
    for name, ep in ledger["epics"].items():
        n = units.issued(ledger, name)
        pct = 100 * n / ep["cap"] if ep["cap"] else 0
        rates = "".join(
            f"<tr><td>{esc(r)}</td><td class=n>{esc(v['units'])}</td><td>{'units' if v['pay_in']=='units' else 'capped claim'}</td>"
            f"<td>{esc(v['fixed'])}{' · before work' if v.get('before_work') else ' · set late, seed'}</td></tr>"
            for r, v in ep["rates"].items())
        caps += (f"<h3>{esc(name)} <small>{link(REPO + ep['spine'], 'its tickets')}</small></h3>"
                 f"<div class=bar><i style='width:{pct:.1f}%'></i></div>"
                 f"<p class=meta><b>{n}</b> of <b>{ep['cap']}</b> units issued, {ep['cap'] - n} left under the cap</p>"
                 f"<table><tr><th>Ticket</th><th class=n>Units</th><th>Paid in</th><th>Rate fixed</th></tr>{rates}</table>")
    def what(e):
        if e["type"] == "award":
            return "Award", esc(e["holder"]), f"+{e['units']}", link(e.get("evidence"), "evidence")
        if e["type"] == "transfer":
            return ("Transfer", f"{esc(e['holder'])} <b>→</b> {esc(e['to'])}", f"{e['units']}", esc(e.get("note", "")))
        return "Spend, burned", esc(e["holder"]), f"−{e['units']}", link(e.get("evidence"), "evidence")
    rows = ""
    for e in ledger["entries"]:
        kind, who, n, extra = what(e)
        cls = " class=tr" if e["type"] == "transfer" else ""
        rows += (f"<tr{cls}><td>{e['seq']}</td><td>{esc(e['date'])}</td><td>{kind}</td><td>{who}</td>"
                 f"<td>{esc(e.get('row') or '')}</td><td class=n>{n}</td><td>{extra}</td></tr>")
    transfers = [e for e in ledger["entries"] if e["type"] == "transfer"]
    trrows = "".join(f"<tr><td>{esc(e['date'])}</td><td>{esc(e['holder'])}</td><td>{esc(e['to'])}</td>"
                     f"<td class=n>{e['units']}</td><td>{esc(e.get('note', ''))}</td></tr>" for e in transfers)
    balrows = "".join(f"<tr><td>{esc(h)}</td><td class=n>{b}</td><td class=n>{b * 1000:,}</td></tr>" for h, b in sorted(bal.items()))
    total = sum(bal.values())
    status = (f"<p class=ok>✓ Ledger checks pass: hash chain intact, caps held, no negative balances, {len(transfers)} transfer{'s' if len(transfers) != 1 else ''} each covered by the sender's balance, every award cites a done ticket.</p>"
              if not errs else "<p class=bad>✗ Ledger check failed:<br>" + "<br>".join(map(esc, errs)) + "</p>")
    redeem = ("Redemption is live." if u.get("redemption_live") else
              "Not spendable yet: Zenod's team agreed in principle to be the service units are spent on. Turning it on costs money, so it waits for Jordi's yes. Until then units are counted and can be sent, but buy nothing.")
    return f"""<!doctype html><html lang=en><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>Nectary units and credit</title>
<style>
{CSS}</style>
<main>
<h1>Nectary units</h1>
<p class=lede>Contributors can be paid in units of a service instead of a capped revenue claim. Units can be sent to other holders and are burned when spent. Nectary is the first seed repo: its own tickets are the work, and this ledger is public.</p>
<div class=unit><b>1 unit = {esc(u['buys'])}</b><br>{esc(redeem)}</div>
{status}
<div class=risk><b>Risk, said plainly.</b> Units that can be sent can also be sold between holders. That raises the US securities and EU MiCA risk the <a href="http://vps3.taild81fbb.ts.net:8973/">research, section 0</a> described, which found units low-risk only while they could not be sold. We keep it small: the project never sells or lists units, never talks about their price, and keeps them off-chain in this ledger. An on-chain token or exchange listing waits for a lawyer's answer to whether transferable units like these are a security or need a MiCA white paper. Not legal advice.</div>
{'<p class=punch>New: <a href="credit.html#credit">builder credit</a>, 2x the ticket price set before work.</p>' if cl else ""}
<h2>Balances by holder</h2>
<table><tr><th>Holder</th><th class=n>Units</th><th class=n>Zenod operations</th></tr>{balrows}
<tr class=sum><td>All holders</td><td class=n>{total}</td><td class=n>{total * 1000:,}</td></tr></table>
<h2>Transfers</h2>
<p class=meta>A holder sends units to another holder. Nothing is issued or burned, and nobody can send more than they hold or send to themselves.</p>
<table><tr><th>Date</th><th>From</th><th>To</th><th class=n>Units</th><th>Note</th></tr>{trrows or "<tr><td colspan=5>None yet</td></tr>"}</table>
<h2>Caps and ticket rates</h2>{caps}
<h2>Ledger</h2>
<table><tr><th>#</th><th>Date</th><th>What</th><th>Holder</th><th>Ticket</th><th class=n>Units</th><th></th></tr>{rows}</table>
<h2>The rules</h2><ol>{rules}</ol>

<footer>Built from <a href="{REPO}ledger/units.json">ledger/units.json</a> · rules in <a href="{REPO}docs/units.md">docs/units.md</a> and <a href="{REPO}docs/repayment-currency.md">why units</a> · not legal, tax or accounting advice.</footer>
</main></html>
"""


def main():
    ledger = units.load(units.DEFAULT_LEDGER)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(build(ledger, credit.load(credit.DEFAULT_LEDGER)))
    with open(os.path.join(os.path.dirname(OUT), "credit.html"), "w", encoding="utf-8") as f:
        f.write(build_credit(credit.load(credit.DEFAULT_LEDGER)))
    print(OUT)


if __name__ == "__main__":
    main()
