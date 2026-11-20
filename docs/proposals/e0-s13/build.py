"""Builds index.html for the E0-S13 presentation. Numbers come from model.py (run it to see them).
Run: python3 -I build.py"""
from html import escape as e
from pathlib import Path

HERE = Path(__file__).parent
part = lambda n: (HERE / "parts" / n).read_text()
INK, MUT, ACC, PAPER, LINE = "#18211c", "#4a554e", "#1f4d3a", "#f6f2e9", "#c9c1ae"


def steps_svg(label, steps, on):
    """A sequence drawn top to bottom: (title, what, stops) per step; step `on` in the accent."""
    w, bh, gap = 420, 92, 30
    h = len(steps) * (bh + gap) - gap + 8
    out = [f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="{e(label)}" class="steps">']
    for i, (title, what, stops) in enumerate(steps):
        y = 4 + i * (bh + gap)
        fill, tc, mc = (ACC, PAPER, "#cfe0d4") if i == on else (PAPER, INK, MUT)
        out.append(f'<rect x="4" y="{y}" width="{w-8}" height="{bh}" rx="6" fill="{fill}" stroke="{ACC if i == on else INK}"/>')
        out.append(f'<text x="20" y="{y+28}" class="serif" font-size="23" style="fill:{tc}">{e(title)}</text>')
        out.append(f'<text x="20" y="{y+54}" font-size="17" style="fill:{mc}">{e(what)}</text>')
        if stops:
            out.append(f'<text x="20" y="{y+78}" font-size="15" style="fill:{mc}" font-style="italic">{e(stops)}</text>')
        if i < len(steps) - 1:
            ax = w // 2
            out.append(f'<path d="M{ax},{y+bh+4} L{ax},{y+bh+gap-6}" stroke="{INK}" stroke-width="2" marker-end="url(#ah)"/>')
    out.append("</svg>")
    return "\n".join(out)


def wheel_svg():
    import math
    nodes = [("Builders", "give inference"), ("Accepted", "tests and jury"), ("Better Zenod", "what users asked for"),
             ("More users", "pay €9 a month"), ("Credit fund", "half of hoster profit"), ("Credit spent", "friends try Zenod")]
    cx, cy, r, bw, bh = 280, 262, 190, 152, 60
    out = ['<svg viewBox="0 0 560 524" role="img" aria-label="The growth cycle: builders give inference, work is accepted, Zenod gets better, more users pay, half of hoster profit funds credit, credit is spent and friends try Zenod">']
    out.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{LINE}" stroke-width="3"/>')
    for i in range(6):
        a1, a2 = math.radians(-90 + i * 60 + 25), math.radians(-90 + i * 60 + 35)
        a2 = math.radians(-90 + (i + 1) * 60 - 25)
        x1, y1, x2, y2 = cx + r * math.cos(a1), cy + r * math.sin(a1), cx + r * math.cos(a2), cy + r * math.sin(a2)
        col = ACC if i == 4 else INK
        out.append(f'<path d="M{x1:.1f},{y1:.1f} A{r},{r} 0 0 1 {x2:.1f},{y2:.1f}" fill="none" stroke="{col}" stroke-width="{3.5 if i == 4 else 2.5}" marker-end="url(#{"aha" if i == 4 else "ah"})"/>')
    for i, (t, s) in enumerate(nodes):
        a = math.radians(-90 + i * 60)
        x, y = cx + r * math.cos(a), cy + r * math.sin(a)
        on = i == 4
        out.append(f'<rect x="{x-bw/2:.1f}" y="{y-bh/2:.1f}" width="{bw}" height="{bh}" rx="6" fill="{ACC if on else PAPER}" stroke="{ACC if on else INK}"/>')
        out.append(f'<text x="{x:.1f}" y="{y-4:.1f}" text-anchor="middle" class="serif wt" font-size="20" style="fill:{PAPER if on else INK}">{e(t)}</text>')
        out.append(f'<text x="{x:.1f}" y="{y+17:.1f}" text-anchor="middle" class="ws" font-size="14" style="fill:{"#cfe0d4" if on else MUT}">{e(s)}</text>')
    out.append(f'<text x="{cx}" y="{cy-14}" text-anchor="middle" class="serif acc" font-size="40">$2.42</text>')
    out.append(f'<text x="{cx}" y="{cy+14}" text-anchor="middle" class="wh" font-size="15">of tested work a month</text>')
    out.append(f'<text x="{cx}" y="{cy+34}" text-anchor="middle" font-size="15" class="mut wh">per paying user, at 2x</text>')
    out.append("</svg>")
    return "\n".join(out)


def table_svg(label, rows, strong=(), cw=132):
    """A small ruled table drawn as SVG: first row is the head; cells with ✓ go in the accent."""
    cw0, rh = 200, 38
    w, h = cw0 + cw * (len(rows[0]) - 1), rh * len(rows) + 8
    out = [f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="{e(label)}" class="tbl">']
    for j, row in enumerate(rows):
        y = 4 + j * rh
        if j:
            out.append(f'<line x1="0" y1="{y}" x2="{w}" y2="{y}" stroke="{INK if j == 1 else LINE}" stroke-width="{1.4 if j == 1 else 1}"/>')
        for k, cell in enumerate(row):
            x = 4 if k == 0 else cw0 + (k - 1) * cw + 6
            style = "serif" if k == 0 or j == 0 else ""
            col = ACC if "✓" in cell else ("#8a2c1c" if "✗" in cell else (MUT if j == 0 else INK))
            fw = ' font-weight="600"' if ("✓" in cell or "✗" in cell or row[0] in strong) else ""
            out.append(f'<text x="{x}" y="{y+25}" font-size="17" class="{style}" style="fill:{col}"{fw}>{e(cell)}</text>')
    out.append("</svg>")
    return "\n".join(out)


def loop_svg():
    """Opening diagram: the multiple attaches to the price known before work; real inference sits beside it, unmultiplied."""
    W = 420
    boxes = [("AI estimate", "tests, size, past tickets: $10", False),
             ("Price $10, fixed", "posted before any work", True),
             ("x 2 = $20 credit", "Zenod service, after tests and jury", False),
             ("Hoster pays $9.48", "known the moment the price is posted", False)]
    bw, bh, gap, x0 = 300, 66, 34, 4
    out = [f'<svg viewBox="0 0 {W} 470" role="img" aria-label="Price first: an AI estimate sets a ten dollar price before work, the credit is two times that price, twenty dollars, the hoster pays 9.48 dollars, and the real inference stays beside it as the builder\'s risk, never multiplied">']
    for i, (t, s, on) in enumerate(boxes):
        y = 4 + i * (bh + gap)
        out.append(f'<rect x="{x0}" y="{y}" width="{bw}" height="{bh}" rx="6" fill="{ACC if on else PAPER}" stroke="{ACC if on else INK}"/>')
        out.append(f'<text x="{x0+16}" y="{y+28}" class="serif" font-size="23" style="fill:{PAPER if on else INK}">{e(t)}</text>')
        out.append(f'<text x="{x0+16}" y="{y+52}" font-size="16" style="fill:{"#cfe0d4" if on else MUT}">{e(s)}</text>')
        if i < len(boxes) - 1:
            out.append(f'<path d="M{x0+bw//2},{y+bh+3} L{x0+bw//2},{y+bh+gap-5}" stroke="{ACC if i == 1 else INK}" stroke-width="{3 if i == 1 else 2}" marker-end="url(#{"aha" if i == 1 else "ah"})"/>')
    y1 = 4 + bh + gap + bh // 2
    out.append(f'<path d="M{x0+bw},{y1} L{W-14},{y1} L{W-14},{4+4*(bh+gap)}" fill="none" stroke="{MUT}" stroke-width="1.6" stroke-dasharray="5 5"/>')
    yb = 4 + 4 * (bh + gap)
    out.append(f'<rect x="{x0}" y="{yb}" width="{W-8}" height="62" rx="6" fill="none" stroke="{MUT}" stroke-dasharray="5 5"/>')
    out.append(f'<text x="{x0+16}" y="{yb+26}" class="serif" font-size="20">Real inference: never multiplied</text>')
    out.append(f'<text x="{x0+16}" y="{yb+49}" font-size="16" class="mut">builder keeps a saving, eats an overrun</text>')
    out.append("</svg>")
    return "\n".join(out)


def risk_svg():
    """Same $10 price, three builders: real inference against the fixed $20 credit, the multiple each one really got."""
    rows = [("Ana", 8.40, "2.4x"), ("Typical", 10.0, "2.0x"), ("Ben", 13.20, "1.5x")]
    W, x0, sc, rh = 420, 96, 13.0, 58
    out = [f'<svg viewBox="0 0 {W} 268" role="img" aria-label="Same ten dollar price for three builders: Ana spends 8.40 dollars and gets 2.4 times, a typical builder spends 10 and gets 2 times, Ben spends 13.20 and gets 1.5 times; credit is twenty dollars for all three">']
    px = x0 + 10 * sc
    for i, (n, real, k) in enumerate(rows):
        y = 26 + i * rh
        out.append(f'<text x="0" y="{y+22}" class="serif" font-size="19">{e(n)}</text>')
        out.append(f'<rect x="{x0}" y="{y+6}" width="{real*sc:.1f}" height="24" fill="{ACC if real < 10 else (MUT if real == 10 else "#8a2c1c")}" opacity="{1 if real != 10 else .55}"/>')
        out.append(f'<text x="{max(x0+real*sc, px)+8:.1f}" y="{y+24}" font-size="16">${real:.2f} · {k}</text>')
    out.append(f'<line x1="{px}" y1="14" x2="{px}" y2="{30+3*rh}" stroke="{INK}" stroke-width="2"/>')
    out.append(f'<text x="{px}" y="10" text-anchor="middle" font-size="15" class="mut">price $10</text>')
    out.append(f'<line x1="0" y1="{40+3*rh}" x2="{W}" y2="{40+3*rh}" stroke="{LINE}"/>')
    out.append(f'<text x="0" y="{68+3*rh}" font-size="17" class="acc" font-weight="600">All three get $20 of credit</text>')
    out.append("</svg>")
    return "\n".join(out)


DEFS = f'''<svg width="0" height="0" style="position:absolute" aria-hidden="true"><defs>
<marker id="ah" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{INK}"/></marker>
<marker id="aha" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{ACC}"/></marker></defs></svg>'''


def rules(items):
    return '<ul class="rules">' + "".join(f"<li><b>{e(a)}</b><span>{e(b)}</span></li>" for a, b in items) + "</ul>"


def more(summary, inner):
    return f'<details class="more"><summary>{e(summary)}</summary>{inner}</details>'


def section(id_, part_, n, h2, figures, detail=""):
    figs = "".join(f'<figure class="{c}">{f}</figure>' for f, c in figures)
    return f'<section id="{id_}" data-part="{part_}"><p class="n">{e(n)}</p><h2>{e(h2)}</h2>{figs}{detail}</section>'


compare = table_svg("Three ways to set the price before work, side by side, ours first", [
    ["", "Ours: estimate, rises", "Estimate, fixed", "Builders bid"],
    ["Known before work", "✓", "✓", "✓"],
    ["If priced too low", "✓ +25% in 48 h", "✗ sits unheld", "✓ bids rise"],
    ["If priced too high", "✓ next one −10%", "✗ hoster overpays", "✓ bids fall"],
    ["Hard to game", "✓ capped 1.5x", "✓", "✗ lowball, junk"],
    ["Starts work", "✓ at once", "✓ at once", "✗ after 2 days"],
], cw=170)
q1 = section("q1", "how the price is set", "A · The price",
             "The 2x multiplies a price set before work. Three ways to set it:",
             [(compare, "chart wide")],
             more("How the estimate is made, with the numbers", rules([
                 ("Who estimates", "An AI estimator reads the ticket's tests, the files it touches and what past tickets like it took."),
                 ("In agent runs", "It counts expected agent runs. A typical team agent run costs $1.20 at API prices."),
                 ("Example", "12 tests, 3 files, similar tickets took 7 to 9 runs: 8 runs, $9.60, posted at $10."),
                 ("Too low", "Nobody holds it in 48 hours: the price rises 25%, to $12.50, then $15, never above 1.5x."),
                 ("Learns", "Tickets taken at once lower the next estimates 10%. Tickets that had to rise raise them."),
                 ("Why not bids", "Bids race to the bottom and pull junk. They also wait two days for every ticket."),
             ])))
q2 = section("q2", "who carries the risk", "B · The risk",
             "The builder carries it: same price, same credit.",
             [(risk_svg(), "chart")],
             more("Why that is fair and hard to game", rules([
                 ("Builder keeps", "A saving. Ana's agent was efficient: $20 for $8.40 is 2.4x."),
                 ("Builder eats", "An overrun. Ben's agent wandered: $20 for $13.20 is still 1.5x."),
                 ("Below 1x", "Only when real inference is over twice the price: about 1 ticket in 40."),
                 ("Re-quote", "Only when the hoster changes the ticket after a hold. The builder may then drop it, deposit back."),
                 ("Cap", "No ticket above 1.5x its estimate, none above $50. Bigger work is split."),
                 ("Nothing to inflate", "Tokens never enter the sum, so burning more earns nothing. A release never raises the price."),
             ])))
q3 = section("q3", "hoster cost bounded", "C · The hoster",
             "The hoster knows its cost before work starts.",
             [(steps_svg("The hoster's cost, known at posting", [
                 ("Price $10", "posted, worth $10 to the hoster", ""),
                 ("x 2 = $20 credit", "about 2.1 months of Zenod", ""),
                 ("x 47¢ = $9.48", "what serving it costs: 95¢ per $1 of price", ""),
                 ("Under half the profit", "posted only when the credit fund holds it", ""),
             ], 2), "narrow")],
             more("The bounds, in numbers", rules([
                 ("Per $1 of price", "95¢ at 2x, under the $1 the work is worth. Break-even stays 2.1x."),
                 ("Worst ticket", "At the $15 cap: $14.22. At the full AI cap: $16.85 for a $10 ticket."),
                 ("Per month", "Never above half the hoster's profit. Today, 10 users: about 2 tickets of $10."),
                 ("Real inference", "Never seen by the hoster and never paid for. Only the posted price is."),
             ])))
q4 = section("q4", "one ticket end to end", "D · One ticket",
             "One ticket, posted to spent, in real numbers.",
             [(steps_svg("One ticket end to end", [
                 ("Posted, Monday", "Jordi: export memories to Markdown, 12 tests", ""),
                 ("Priced", "estimate 8 runs, $9.60: price $10, cap $15", ""),
                 ("Held", "Ana's agent takes it at $10, $5 deposit, 48 h", ""),
                 ("Built", "7 agent runs, $8.40 real, no one counts", ""),
                 ("Tested and judged", "12 plus 4 hidden tests pass, jury 3 of 3", ""),
                 ("Paid $20 credit", "2 x $10 price · Jordi's cost $9.48", ""),
                 ("Spent", "one month herself, one to a friend", ""),
             ], 5), "narrow")])

open_svg = part("open.svg").replace('<defs>', '<defs>', 1)
s1 = section("p1", "hoster numbers", "1 · Hoster numbers",
             "A hoster pays about half the list price to serve credit, not a fifth.",
             [(open_svg, "narrow"), (part("split.svg"), "chart"), (part("bars.svg"), "chart")],
             more("How the hoster comes out, and the proposal page it corrects", rules([
                 ("The month", "One month lists at €9, about $9.49. Serving it costs about $4.50."),
                 ("In profit", "Up to 2x for typical use: the work is worth more than the service."),
                 ("Loses", "Above 2.1x for typical use, above 1.2x at the full AI cap. At 5x: −$1.37 per $1."),
                 ("Never ruined", "Credit is honoured only from half the profit. The rest waits in line, in order."),
                 ("5x holds when", "Serving costs a fifth of the price: about 5,000 paying users, screen 4."),
                 ("Correction", "The page you closed said a fifth. Real numbers say close to half."),
             ])))
s2 = section("p2", "how inference is proven", "2 · How inference is proven",
             "Yes: code that passes the ticket's tests, judged by an AI jury. We never count tokens.",
             [(steps_svg("From ticket to credit, and what stops gaming at each step", [
                 ("Ticket", "its tests and a rate fixed before work", "stops waste: paid the rate, never per token"),
                 ("Hold", "a builder's agent holds it for 48 hours", "stops vanishing: $5 deposit, one hold if new"),
                 ("Code", "the agent submits a change", "stops cheating: test files are locked"),
                 ("Tests", "the ticket's tests plus hidden ones run", "stops code that only fits the tests"),
                 ("Jury", "three different AI models, two must accept", "judges what tests cannot · contest once"),
                 ("Credit", "the fixed rate times the multiple", "rating rises · a person checks a sample monthly"),
             ], 5), "narrow")],
             more("Where the rate comes from, and what exists today", rules([
                 ("The rate", "Set from what the work costs at API prices. A typical team agent run costs $1.20."),
                 ("Rating", "A good rating unlocks more holds and drops the deposit."),
                 ("A bad accept", "The monthly sample can cancel that credit and drop the rating."),
                 ("Today", "Coming: all of this. Live: the units ledger refusing credit for unaccepted tickets."),
             ])))
s3a = section("p3a", "builder example", "3 · End to end, the builder",
              "Ana gives $10 of inference and gets two months of Zenod.",
              [(steps_svg("Builder example", [
                  ("Picks a ticket", "Export memories to Markdown: $10 rate, 12 tests", ""),
                  ("Her agent builds", "about eight agent runs", ""),
                  ("Accepted", "all tests pass, jury three of three, deposit back", ""),
                  ("Gets $20 of credit", "2x: about 2.1 months of Zenod", ""),
                  ("Spends it", "one month herself, one passed to a friend", ""),
              ], 3), "narrow")],
              more("At 5x, and cash", rules([
                  ("At 5x", "$50 of credit, about 5.3 months. Too costly for the hoster today."),
                  ("Cash", "None. A cash claim instead repays her $10 from revenue, never more."),
                  ("Why she does it", "Spare inference becomes a service she uses, with her feature in it."),
              ])))
s3b = section("p3b", "hoster example", "3 · End to end, the hoster",
              "Jordi, the first hoster, serves Ana's two months for $9.48 and gets $10 of work.",
              [(steps_svg("Hoster example", [
                  ("Gets the work", "the export feature: $10 to build himself", ""),
                  ("Serves her credit", "2.1 months of Zenod for Ana", ""),
                  ("Pays $9.48", "AI $1.50 and server $3 for each month", ""),
                  ("Gains", "the feature for all users, a friend tries Zenod", ""),
                  ("Net +$0.52", "on the work alone, at 2x", ""),
              ], 4), "narrow")],
              more("At 5x, and his month", rules([
                  ("At 5x", "$23.70 for $10 of work: −$13.70, unless the friend pays three months."),
                  ("10 users a month", "$94.90 in, $49 out, $45.90 profit. Half, $22.95, funds credit."),
                  ("Why he wants it", "Builders improve what he sells for less than he could, and bring friends."),
              ])))
s3c = section("p3c", "user example", "3 · End to end, the user",
              "Marta pays €9 a month, and part of it buys work that improves her Zenod.",
              [(steps_svg("User example", [
                  ("Pays €9 + VAT", "every month, the same price as today", ""),
                  ("Gets her memory", "over WhatsApp, filing and answers", ""),
                  ("Her €9 splits", "AI $1.50 · server $3 · card $0.40 · profit $4.59", ""),
                  ("$2.30 funds credit", "half the profit buys $2.42 of tested work", ""),
                  ("Zenod gets better", "next month the export feature is there", ""),
              ], 3), "narrow")],
              more("At 1,000 users", rules([
                  ("1,000 users", "About $2,400 of tested work a month, some 2,000 agent runs."),
                  ("No higher price", "Credit comes from the hoster's profit, not from her."),
              ])))
scale = table_svg("The numbers at small, medium and large scale", [
    ["", "Small, today", "Medium", "Large"],
    ["Paying users · builders", "10 · 5", "200 · 40", "5,000 · 500"],
    ["Server · AI per user", "$3 · $1.50", "$2 · $1.50", "$1 · $1"],
    ["Credit fund a month", "$23", "$559", "$17,737"],
    ["Builder work a month", "$50", "$400", "$5,000"],
    ["Hoster breaks even", "2.1x", "2.7x", "4.7x"],
    ["Fund pays for now", "1x, rest waits", "3.8x", "16.8x"],
    ["2x", "✓ over time", "✓", "✓"],
    ["5x", "✗", "✗", "✓ about"],
], strong=("Hoster breaks even",))
s4 = section("p4", "dynamics", "4 · The dynamics as the service grows",
             "Each turn of the wheel makes the next one cheaper, until 5x can hold.",
             [(wheel_svg(), "chart"), (scale, "chart wide")],
             more("Where it breaks: too many builders, heavy users, junk, model prices", rules([
                 ("Too many builders", "More than one per four paying users at 2x: credit outgrows profit."),
                 ("Heavy users", "Credit holders at the full AI cap push break-even to 1.2x."),
                 ("Junk accepted", "Credit with no work behind it. Tests, jury and the sample guard it."),
                 ("Model prices rise", "Every number moves with AI cost. The multiple is reset monthly."),
             ])))
rec_svg = table_svg("2x against 5x, today and at large scale", [
    ["", "Today", "5,000 users"],
    ["2x service credit", "✓ $0.95 per $1", "✓ $0.42 per $1"],
    ["5x service credit", "✗ $2.37 per $1", "✓ $1.05, even"],
    ["Cash", "at cost", "at cost"],
])
rec = f'''<section id="rec" class="ps-bottom" data-part="our recommendation"><div class="ps-rec"><h2>Our recommendation</h2>
<p>2x the price set before work. Builders carry overruns. Toward 5x monthly.</p></div>
<figure class="chart">{rec_svg}</figure>
<table aria-label="Your points, covered"><tr><th>Your point, 20 Nov</th><th>Where</th><th></th></tr>
<tr><td>"we don't know inference cost upfront"</td><td><a href="#q1">A</a></td><td class="y">✓</td></tr>
<tr><td>who carries an overrun</td><td><a href="#q2">B</a></td><td class="y">✓</td></tr>
<tr><td>the hoster's cost bounded</td><td><a href="#q3">C</a></td><td class="y">✓</td></tr>
<tr><td>one ticket end to end</td><td><a href="#q4">D</a></td><td class="y">✓</td></tr>
<tr><td>"numbers for hosters having to shoulder this"</td><td><a href="#p1">screen 1</a></td><td class="y">✓</td></tr>
<tr><td>"How is inference proven?"</td><td><a href="#p2">screen 2</a></td><td class="y">✓</td></tr>
<tr><td>"end to end for each party"</td><td><a href="#p3a">builder</a>, <a href="#p3b">hoster</a>, <a href="#p3c">user</a></td><td class="y">✓</td></tr>
<tr><td>"dynamics we want as service grows"</td><td><a href="#p4">screen 4</a></td><td class="y">✓</td></tr></table>
<p class="ps-punch" data-part="bottom line">Credit is 2x a price known before work; 5x holds near 5,000 paying users. Your call.</p></section>'''

FOOT = ("Sources. Live: Zenod Hosted €9 a month + VAT (zenod terms.html); at most $5 of AI cost per account a month "
        "(zenod limits.ts, your E26-A7); a typical team agent run $1.20 at API prices (zenod docs/evidence/e7-s1). "
        "Estimate: server €2 to €4 per account, a €20 box for 5 to 10 accounts (zenod docs/HOSTED-PLAN). "
        "Assumptions: €1 = $1.055; card fee $0.40; typical AI use $1.50, not yet measured; $1 of accepted work worth $1 "
        "to the hoster; the three scales; real inference spread ±35% around the estimate (log-normal); the 25% step, 1.5x cap and $50 ticket limit are our proposal. Every number comes from model.py beside this page. Demo names. Not legal advice.")

style = part("style.css.html").replace("</style>", """
[data-page-shell] .s13 figure.narrow svg,[data-page-shell] .s13 figure.chart svg{max-width:30rem}
[data-page-shell] .ps-diagram .dg{max-width:26rem;margin:0 auto}
[data-page-shell] .ps-diagram svg{display:block;width:100%;height:auto}
@media (max-width:560px){[data-page-shell] svg .ws{display:none}[data-page-shell] svg .wt{font-size:24px}[data-page-shell] svg .wh{font-size:21px}}
[data-page-shell] .s13 figure.wide{overflow-x:auto}
[data-page-shell] .s13 figure.wide svg{min-width:34rem}
[data-page-shell] .s13 details.more{margin:.4rem 0 0}
[data-page-shell] .s13 p.earlier{margin:2.4rem 0 0;font-size:1rem}
[data-page-shell] .s13 details.more summary{cursor:pointer;color:var(--muted);font:400 .95rem var(--sans)}
</style>""")

html = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Nectary economics: 2x of a price known before work</title>
<link rel="stylesheet" href="/_shell/shell.css">
{style}
</head>
<body data-page-shell>
{DEFS}
<main class="ps-page s13">
<header class="ps-head"><p class="ps-kicker">E0-S14 · 2026-11-20 · answers "we don't know inference cost upfront" on EPIC-0-A4</p><h1>Nectary economics: 2x of a price known before work</h1></header>
<p class="ps-punch" data-part="bottom line">Credit is <b>2x the ticket's price</b>, fixed before work. The inference actually burned is the builder's risk, so nobody needs to know it upfront.</p>
<figure class="ps-diagram" data-shape="line"><div class="dg">
{loop_svg()}
</div></figure>
<div class="ps-body">
{q1}
{q2}
{q3}
{q4}
<p class="n earlier">Earlier, on EPIC-0-A3</p>
{s1}
{s2}
{s3a}
{s3b}
{s3c}
{s4}
{rec}
<p class="ps-foot">{e(FOOT)} · E0-S13 made this page, E0-S14 added the four questions · one shared page shell (E75-S5)</p>
</div>
</main>
</body></html>
'''
(HERE / "index.html").write_text(html)
print("wrote index.html")
