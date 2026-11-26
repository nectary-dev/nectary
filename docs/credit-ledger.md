# Builder credit: the spec (E0-S10)

**An accepted builder is credited 2x the ticket's price fixed before work, in hoster service, and a hoster honours that credit from at most half its monthly profit.** This is the rule Jordi said yes to on 2026-11-26 (EPIC-0-A5): "Yes: build the ledger and ticket board on 2x the price set before work". The numbers behind it are on the [economics page](http://vps3.taild81fbb.ts.net:8976/) ([model.py](proposals/e0-s13/model.py)).

```
 ticket priced ──> builder holds ──> accepted ──> credit issued ──> spend at hoster ──> honoured, burned
 8 runs x $1.20    price fixed       row done     2 x $10 = $20     request joins       while half its
 = $10 posted      ($10)             in spine     (multiple of the  the hoster's line   monthly profit
 +25% per 48 h                                    posting month)                        lasts; else waits
```

- Ledger: [ledger/credit.json](../ledger/credit.json). Tool: [tools/credit.py](../tools/credit.py). Tests: `python3 -m unittest tests.test_credit`.
- Check: `python3 tools/credit.py verify`.
- Page: the credit section of the [units page](http://vps3.taild81fbb.ts.net:8974/#credit).

## Same ledger approach as units

The credit ledger is a sibling of the [units ledger](units.md), and `tools/credit.py` reuses its code (`tools/units.py`: load, save, hash, spine status). It is public JSON, append-only, and each entry carries the sha256 of the entry before it, so any rewrite of history breaks the chain. It is a separate file because credit is counted in dollars of a hoster's service and units are counted in Zenod operations. Mixing the two in one balance would hide which promise each holder has.

## Rules

1. **Price fixed before work.** Each ticket is priced from its template ([ticket-template.md](ticket-template.md)): the AI estimate in agent runs x $1.20, rounded to whole dollars, +25% for every 48 h nobody holds it, never above 1.5x the estimate or $50. The price is fixed when a builder holds the ticket, and work starts then. `credit.py from-ticket tickets/<id>.md` checks the ticket with `tools/ticket.py` and copies its price into the ledger's `tickets`. A ticket is priced once; only a hoster's change to the ticket re-quotes it, as a new ticket.
2. **Credit = multiple x fixed price, on acceptance.** An `issue` entry is valid only when the ticket's row is `done` in its spine, and only once per ticket. Its amount is exactly the multiple x the fixed price: $20 for a $10 ticket.
3. **Real inference never changes credit.** An issue may record the inference the builder actually spent (`inference_cents`). The check ignores it: the builder keeps a saving and carries an overrun. Ana spends $8.40 and Ben $13.20 on a $10 ticket; both get $20.
4. **The multiple is reset at most monthly, for new tickets only.** `multiples` lists each reset with its date and public source. It starts at 2x on 2026-11-26. A ticket earns the multiple in force on the day it was posted. A later reset, up or down, never changes credit already issued or tickets already posted.
5. **Transferable.** Units can be sent between holders, so credit can too: a `transfer` moves spendable credit to another holder. Never more than the sender holds, never to oneself.
6. **Spent at a hoster, burned.** A `request` sets credit aside to spend at a hoster. An `honour` entry serves a whole request and burns that credit.
7. **A hoster honours credit from at most half its monthly profit.** Each hoster's month in `hosters` records its profit and its cost to serve $1 of credit (about $0.47 for Zenod today). That month's room is half the profit divided by that cost: $22.97 / 0.474 = $48.47 of credit. Requests beyond the room wait in line and are honoured in order, starting the next month with new room. A later request never jumps an earlier one.
8. **Cash stays at cost.** Credit is service only. A builder who picks cash gets a claim of the fixed price, 1x, never more, through the repayment queue (E0-S3). Nobody on the project calls credit a stake, share, investment or return (L-1).

## Entries

| Type | Fields | Checked |
|---|---|---|
| `issue` | holder, ticket, price_cents, multiple, cents, evidence, optional inference_cents | ticket priced before work, row done, multiple of its posting day, cents = multiple x price, once per ticket |
| `transfer` | holder (sender), to, cents, note | sender has the spendable credit, not to oneself |
| `request` | holder, hoster, cents, note | known hoster, holder has the spendable credit; credit is set aside |
| `honour` | holder, hoster, request, cents | matches an open request in full, first in that hoster's line, within half the month's profit |

Every entry also has `seq`, `date` and `prev` (the hash chain). Money is in whole US cents.

## Commands

`price`, `from-ticket <file>`, `issue --holder --ticket --evidence [--inference-cents]`, `transfer --from --to --cents`, `spend --holder --hoster --cents` (request, then honour what fits), `honour --hoster` (serve the line with this month's room), `balance`, `verify`.

`verify` fails when an entry type is unknown, the chain or order breaks, a price breaks the ladder or was fixed after work started, a credit differs from the multiple of its posting day x the fixed price, a ticket is credited twice or before its row is done, a multiple is reset twice in a month, a transfer or request overdraws, an honour jumps the line, or a hoster honours more than half its profit in a month.

## What is in the ledger now

One demonstration entry: the template's worked ticket [EXAMPLE-1](../tickets/EXAMPLE-1.md), 8 runs, posted and held at $10, credited $20 to Ana, an example builder, who spent $8.40. It is marked `demonstration` because it has no real accepted row. Zenod's November profit is the E0-S13 model's small-scale assumption (10 paying users, $45.95) until Zenod publishes real books.

## Not settled here

- Spending credit at Zenod is not switched on. It costs model spend and is parked with E0-S8. The ledger records the rule, not service served.
- Who sets the monthly reset from which public books: the first reset is due in December.
- The cash repayment queue for builders who pick a claim: E0-S3.

*Not legal, securities, tax or accounting advice.*
