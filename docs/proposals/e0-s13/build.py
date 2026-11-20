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


def table_svg(label, rows, strong=()):
    """A small ruled table drawn as SVG: first row is the head; cells with ✓ go in the accent."""
    cw0, cw, rh = 200, 132, 38
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


open_svg = part("open.svg").replace('<defs>', '<defs>', 1)
s1 = section("p1", "hoster numbers", "1 · Hoster numbers",
             "A hoster pays about half the list price to serve credit, not a fifth.",
             [(part("split.svg"), "chart"), (part("bars.svg"), "chart")],
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
<p>Start at 2x service credit, rising monthly by a public rule toward 5x. Cash stays at cost.</p></div>
<figure class="chart">{rec_svg}</figure>
<table aria-label="Your four points, covered"><tr><th>Your point, 20 Nov</th><th>Where</th><th></th></tr>
<tr><td>"numbers for hosters having to shoulder this"</td><td><a href="#p1">screen 1</a></td><td class="y">✓</td></tr>
<tr><td>"How is inference proven?"</td><td><a href="#p2">screen 2</a></td><td class="y">✓</td></tr>
<tr><td>"end to end for each party"</td><td><a href="#p3a">builder</a>, <a href="#p3b">hoster</a>, <a href="#p3c">user</a></td><td class="y">✓</td></tr>
<tr><td>"dynamics we want as service grows"</td><td><a href="#p4">screen 4</a></td><td class="y">✓</td></tr></table>
<p class="ps-punch" data-part="bottom line">2x holds today; 5x holds near 5,000 paying users. Your call on the promise.</p></section>'''

FOOT = ("Sources. Live: Zenod Hosted €9 a month + VAT (zenod terms.html); at most $5 of AI cost per account a month "
        "(zenod limits.ts, your E26-A7); a typical team agent run $1.20 at API prices (zenod docs/evidence/e7-s1). "
        "Estimate: server €2 to €4 per account, a €20 box for 5 to 10 accounts (zenod docs/HOSTED-PLAN). "
        "Assumptions: €1 = $1.055; card fee $0.40; typical AI use $1.50, not yet measured; $1 of accepted work worth $1 "
        "to the hoster; the three scales. Every number comes from model.py beside this page. Demo names. Not legal advice.")

style = part("style.css.html").replace("</style>", """
[data-page-shell] .s13 figure.narrow svg,[data-page-shell] .s13 figure.chart svg{max-width:30rem}
[data-page-shell] .ps-diagram svg{max-width:32rem;margin:0 auto;display:block}
@media (max-width:560px){[data-page-shell] svg .ws{display:none}[data-page-shell] svg .wt{font-size:24px}[data-page-shell] svg .wh{font-size:21px}}
[data-page-shell] .s13 figure.wide{overflow-x:auto}
[data-page-shell] .s13 figure.wide svg{min-width:34rem}
[data-page-shell] .s13 details.more{margin:.4rem 0 0}
[data-page-shell] .s13 details.more summary{cursor:pointer;color:var(--muted);font:400 .95rem var(--sans)}
</style>""")

html = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Nectary economics: what credit costs a hoster, and the multiple that holds</title>
<link rel="stylesheet" href="/_shell/shell.css">
{style}
</head>
<body data-page-shell>
{DEFS}
<main class="ps-page s13">
<header class="ps-head"><p class="ps-kicker">E0-S13 · 2026-11-20 · answers your questions on EPIC-0-A3</p><h1>Nectary economics: what credit costs a hoster</h1></header>
<p class="ps-punch" data-part="bottom line">At Zenod's real costs 5x credit loses money today: hosters break even near <b>2x</b>, reaching <b>5x</b> around 5,000 paying users.</p>
<figure class="ps-diagram" data-shape="cycle">
{open_svg}
</figure>
<div class="ps-body">
{s1}
{s2}
{s3a}
{s3b}
{s3c}
{s4}
{rec}
<p class="ps-foot">{e(FOOT)} · E0-S13 keeps this page · one shared page shell (E75-S5)</p>
</div>
</main>
</body></html>
'''
(HERE / "index.html").write_text(html)
print("wrote index.html")
