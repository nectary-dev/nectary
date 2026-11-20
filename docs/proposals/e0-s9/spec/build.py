#!/usr/bin/env python3
"""Build the E0-S9 proposal page (Nectary revived) on the shared page shell.

python3 docs/proposals/e0-s9/spec/build.py   -> docs/proposals/e0-s9/index.html
Diagrams: spec/*.json rendered with agent_team skills/house-diagram-style; mock-up: spec/board.html screenshot.
"""
import re
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE.parent
SHELL = Path.home() / "github/agent_team/scripts/page_shell.py"

TITLE = "Nectary revived: spare inference pays builders in Zenod service"
BOTTOM = ("Pay builders 5x their inference as Zenod service credit, keep cash repayment at cost, "
          "and launch it with a five-week hackathon.")

CHANGES = [
    "Credit ledger: each accepted ticket earns 5x its seat-hours as Zenod service credit, on the units ledger that already works.",
    "Ticket template: tests, seat-hours, hold time and deposit on every ticket, so an agent can read and take it alone.",
    "Agent ticket board for Zenod: list, hold, submit and release through WebMCP, with the same page for people.",
    "Hoster rules: how a hoster is certified, half its profit backs credit, its books public. You are the first, hosting Zenod.",
    "Hackathon week one on Nectary itself, with the teaser and the three-minute video script for your channel.",
]
IMPLICATIONS = [
    "Nothing changes hands in cash today. Credit costs Zenod model spend when spent, about 1 to 3 dollars per 1,000 memory operations.",
    "A cash promise of 5x or 10x, or pay that grows with the project, needs a lawyer's yes first. We keep it off the table until then.",
    "Credit is never sold or listed by us and nobody talks about its price, the same rules the units already follow.",
    "Abuse is the main risk: tests decide acceptance, the deposit and the rating slow down farmers, and the pay is per accepted ticket.",
]
RECOMMEND = "Yes to 5x service credit, cash kept at cost, Zenod first, week one on Nectary itself."


def fig(img: str, alt: str, wide: bool = True) -> str:
    return f'<figure class="e9-fig{" e9-wide" if wide else ""}"><img src="{img}" alt="{alt}"></figure>'


def why(html: str) -> str:
    return f'<details class="e9-why"><summary>Why and how</summary>\n{html}\n</details>'


def part(key: str, title: str, img: str, alt: str, line: str, more: str, shape: str) -> str:
    return (f'<section class="ps-part e9" data-part="{key}" data-shape="{shape}"><h2>{title}</h2>\n'
            f'{fig(img, alt)}\n<p class="e9-line">{line}</p>\n{why(more)}\n</section>\n')


POINTS = "".join([
    part("point 1", "1. Inference in, credit out", "compare.png", "Revenue-backed cash next to usage rights",
         "Usage rights at 5x. Cash stays repayment of cost.", """
<p>You asked for 10x, and later 5x. In service credit, 5x is a promise a hoster can keep: serving costs about a fifth
of the list price (our estimate for Zenod), so 5x credit costs the hoster roughly the inference you gave. 10x would need
margins near 90%, so we start at 5x and raise it only if the books show room.</p>
<p>Revenue-backed cash stays what Nectary already is: your cost, repaid from revenue, never more. A cash multiple, or pay
that grows at the project's pace, is profit from other people's work, which is what securities law looks for
(see the <a href="http://vps3.taild81fbb.ts.net:8973/">repayment research</a>). Not legal advice.</p>
<p>How inference is measured: by the accepted ticket, at a seat-hour rate fixed before work. Counting tokens pays for
waste, and paid-per-output networks filled with junk work.</p>
<p>Voting weight by inference: we suggest parking it until after the hackathon, since Nectary rules out power that
follows wealth.</p>""", "compare"),
    part("point 2", "2. Hosters fund it", "hosters.png", "You build, earn the right, host, honour credit, the rest waits",
         "Builders earn the right to host. You are the first, hosting Zenod.", """
<p>Anyone can run the open code. A certified hoster also accepts Nectary credit, up to half its monthly profit; credit
beyond that waits in line, in order. Certification goes to builders who gave inference, so every hoster has built the
thing. Your business is the hosting side: Zenod hosted by you, with no founder premium. Builders who already gave a
lot, like you on Zenod, record that past work at the same seat-hour rate as everyone else.</p>""", "line"),
    part("point 3", "3. Agent-first tickets", "ticket.png", "An agent knocks, holds a ticket, submits, gets its deposit back",
         "Agents hold a ticket with a 5 dollar refundable deposit and earn a rating.", """
<p>A contributor's agent reads the board through WebMCP, says it has spare capacity and holds a ticket for 48 hours.
The deposit comes back when the work is submitted or the ticket is released in time; it is kept only when a hold runs
out silently. New builders hold one ticket at a time. A good rating unlocks more holds and drops the deposit. Tests
decide acceptance. Gitcoin ran bounty boards like this; the deposit and the rating are what slow down farming.</p>""", "line"),
    part("point 4", "4. The staged hackathon", "hackathon.png", "A design question, teams answer, AI panel ranks, people vote, winner becomes tickets",
         "One idea per week, five weeks. Week one is Nectary itself.", """
<p>Of your two orders we pick all stages of one idea per week: one finished thing and one video each week, rather than
five half-done ones. Each round poses one design question. An AI panel of three different models ranks the answers
and proposes merges, people and teams vote beside it, and a team may contest once. Every team starts the next round
level. Accepted answers become tickets and earn credit on the same ledger, which is what measures your inference.</p>
<p>The weeks: 1 Nectary itself, 2 Zenod as open memory anyone can host, 3 PolyQuestion, 4 open accounting for Spain,
5 an open home-search agent (your Web3 idealista).</p>
<p>Your YouTube video carries a short teaser pointing to a standalone three-minute video in English that opens the
hackathon. A shared Minecraft-like world comes later, once the first weeks show people come.</p>""", "line"),
    part("point 5", "5. Zenod first", "zenod.png", "Zenod runs, its tickets open, builders earn and spend Zenod credit, five testers",
         "Zenod's builders become its users, which moves Zenod: 5 testers.", """
<p>Zenod already runs, with a team that agreed in principle to 1,000 memory operations per unit, so credit buys
something real on day one. Decentralized from the start: open code, any certified hoster, you the first. Opening
Zenod's code to other hosters is Zenod's own call; we sent your words to Zenod's desk.</p>""", "line"),
    part("point 6", "6. The ideas", "polyq.png", "Ask, tap your DNI, proof on the phone, one vote, public tally",
         "PolyQuestion looks buildable. Open accounting for Spain fits beside EpicBooks.", """
<p><b>PolyQuestion.</b> The DNI chip can be read by a phone, and open projects such as zkPassport and Self already
prove passport facts this way without revealing the document. The same proof says the chip was signed by Spain's
police and has not expired, plus a per-question number so each ID votes once. Limits: it proves someone holds a valid
card, not who presses the button, and location cannot be proven cheaply. Cost: checking a proof on an Ethereum layer
two is about a cent or less, much more on the main chain (our estimate). We would start with a public log anyone can
recount and add a chain later.</p>
<p><b>Open accounting for Spain.</b> An open-source AI bookkeeper for freelancers and small companies: reads invoices,
keeps the books, files the quarterly forms, meets the Verifactu invoice rules. Hosters sell it as a service and
builders earn credit in it. It sits next to EpicBooks, the team's own bookkeeping work.</p>""", "line"),
])

DECISIONS = """<figure class="e9-fig"><picture><source media="(max-width: 640px)" srcset="decide-phone.png"><img src="decide.png" alt="5x as service credit: yes builds the loop now, no waits for a lawyer"></picture></figure>
<table class="e9-table">
<tr><th>Also on the way</th><th>Our pick</th></tr>
<tr><td>Hackathon order</td><td>One idea a week</td></tr>
<tr><td>Ticket deposit</td><td>5 dollars, new builders only</td></tr>
<tr><td>PolyQuestion record</td><td>Public log, chain later</td></tr>
<tr><td>Voting by inference</td><td>Park it</td></tr>
</table>
<p class="e9-line">Handed on: the 16 seats and knowledge graph to EpicTeam, opening Zenod's code to Zenod.</p>
"""

CSS = """<style>
[data-page-shell] .e9-fig{margin:1rem 0;padding:.5rem;background:var(--stage);border-radius:6px}
[data-page-shell] .e9-fig img{display:block;width:100%;height:auto;border-radius:3px}
[data-page-shell] .e9 p{max-width:42rem}
[data-page-shell] .e9-line{font-size:1.05rem;margin:.4rem 0}
[data-page-shell] .e9-why{margin:.5rem 0 1rem}
[data-page-shell] .e9-why summary{cursor:pointer;color:var(--muted);font-size:.95rem}
[data-page-shell] .e9-why[open] summary{margin-bottom:.5rem}
[data-page-shell] .e9-boxes,[data-page-shell] .e9-weeks{list-style:none;padding:0;margin:1rem 0;display:grid;gap:.6rem;grid-template-columns:repeat(auto-fit,minmax(13rem,1fr))}
[data-page-shell] .e9-weeks{grid-template-columns:repeat(auto-fit,minmax(9.5rem,1fr))}
[data-page-shell] .e9-boxes li,[data-page-shell] .e9-weeks li{border:1px solid var(--line);border-radius:6px;padding:.7rem .85rem;font-size:.95rem;line-height:1.35}
[data-page-shell] .e9-boxes li b,[data-page-shell] .e9-weeks li b{display:block;font-family:var(--serif);font-weight:500;font-size:1.05rem;margin-bottom:.2rem}
[data-page-shell] .e9-boxes li.on{border-color:var(--accent);background:var(--accent-soft)}
[data-page-shell] .e9-table{border-collapse:collapse;width:100%;font-size:.95rem;margin:1rem 0}
[data-page-shell] .e9-table th,[data-page-shell] .e9-table td{text-align:left;vertical-align:top;padding:.6rem .5rem;border-top:1px solid var(--line)}
[data-page-shell] .e9-table tr.on td{background:var(--accent-soft)}
@media (max-width:640px){
 [data-page-shell] .e9-wide{overflow-x:auto}
 [data-page-shell] .e9-wide img{width:720px;max-width:none}
 [data-page-shell] .e9-table th,[data-page-shell] .e9-table td{display:block;border-top:0;padding:.2rem .5rem}
 [data-page-shell] .e9-table tr{display:block;border-top:1px solid var(--line);padding:.4rem 0}
 [data-page-shell] .e9-table tr:first-child{display:none}
}
</style>
"""


def main() -> None:
    cmd = ["python3", str(SHELL), "proposal", str(OUT), "--title", TITLE, "--bottom-line", BOTTOM, "--row", "E0-S9",
           "--diagram", "cycle.png", "--mockup", "board.png", "--change", *CHANGES, "--implication", *IMPLICATIONS,
           "--recommend", RECOMMEND]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL)
    page = (OUT / "index.html").read_text()
    # phones get the label-only wheel, cropped square
    page = re.sub(r'<figure class="ps-diagram"><img src="cycle.png" alt="([^"]*)"></figure>',
                  r'<figure class="ps-diagram" data-shape="cycle"><picture><source media="(max-width: 640px)" srcset="cycle-phone.png">'
                  r'<img src="cycle.png" alt="\1"></picture></figure>', page, count=1)
    page = page.replace('<h2>Mock-ups</h2>', '<h2>The ticket board an agent reads</h2>', 1)
    page = page.replace('alt="mock-up 1"', 'alt="Mock-up: Zenod tickets open for builders, each with credit, hold time and a refundable deposit"')
    # the changes: a drawn line, the list folded
    page = re.sub(r'(<section class="ps-part" data-part="the changes">)<h2>The changes</h2>(<ol class="ps-list">.*?</ol>)',
                  lambda m: POINTS + m.group(1) + '<h2>What we build once you answer</h2>'
                  + '<figure class="e9-fig e9-wide"><img src="build.png" alt="Credit ledger, ticket template, agent board, hoster rules, hackathon week one"></figure>'
                  + '<details class="e9-why"><summary>Each step</summary>' + m.group(2) + '</details>', page, count=1, flags=re.S)
    # implications: folded whole
    page = re.sub(r'(<section class="ps-part" data-part="implications">.*?</section>)',
                  r'<details class="e9-why e9-impl"><summary>Implications and risks</summary>\1</details>', page, count=1, flags=re.S)
    # recommendation: the decision drawn, then the one line
    page = page.replace('<h2>Our recommendation</h2>', '<h2>Our recommendation, and your one decision</h2>' + DECISIONS, 1)
    page = page.replace("</head>", CSS + "</head>", 1)
    (OUT / "index.html").write_text(page)
    for h in OUT.glob("*.html"):
        if h.name != "index.html":
            h.unlink()  # the renderer's editable copies; the spec JSON is the source
    print(OUT / "index.html")


if __name__ == "__main__":
    main()
