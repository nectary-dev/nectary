# The repayment queue: the rules (E0-2)

**A builder who picks cash is repaid the ticket's price fixed before work, 1x and never more, from half the hoster's monthly profit, oldest accepted claim first, in parts until paid.** Builder credit (2x, Jordi's EPIC-0-A5 answer of 2026-11-26: "Yes: build the ledger and ticket board on 2x the price set before work") draws on the same half first; cash gets what is left.

```
 ticket accepted ──> claim joins the line ──> month closes ──> fund ──────────────────────> pay, oldest first
 builder picked      1x the fixed price       hoster's books   half the month's profit       part by part, until
 cash ($10 ticket)   ($10), in order of       (credit ledger)  less what serving builder     each claim is paid
                     acceptance                                credit cost that month        in full, then closed
```

- Ledger: [ledger/queue.json](../ledger/queue.json). Tool: [tools/queue.py](../tools/queue.py). Tests: `python3 -m unittest tests.test_queue`.
- Check: `python3 tools/queue.py verify`. Worked run: `python3 tools/queue.py demo`.
- Siblings: the [credit ledger](credit-ledger.md) (2x service credit) and the [units ledger](units.md) (service units). The [ticket template](ticket-template.md) is where the builder picks one of the three.

## Three ways to be paid, one per ticket

| Builder picks | Gets | From | Where it is kept |
|---|---|---|---|
| `credit` | 2x the fixed price in the hoster's service | half the hoster's monthly profit, waiting in line when it runs out | [ledger/credit.json](../ledger/credit.json) |
| `claim` | the fixed price in cash, 1x, never more | what is left of that half after credit, through this queue | [ledger/queue.json](../ledger/queue.json) |
| `units` | the units rate fixed before work, priced in Zenod operations | no cash and no revenue: spent as service, burned | [ledger/units.json](../ledger/units.json) |

A ticket is paid in one of them only. The queue refuses a claim for a ticket already credited in the credit ledger or awarded units in the units ledger. Units never enter the queue: they are counted in Zenod operations, never in dollars ([units.md](units.md) rule 1), so they have no place in a cash line.

## Rules

1. **Who joins.** A ticket whose row is `done` (accepted) in its spine and whose builder picked `claim` joins the line the day it is accepted. `queue.py claim --ticket tickets/<id>.md` reads it through the template validator (`tools/ticket.py`), so a ticket that fails the template cannot join. A founder's cost already spent joins the same line under the same rule, with what it cost and how that was counted (`bootstrap`, [design principle 5](design-principles.md#5-bootstrap-cost-is-a-cost-like-any-other)). No founder premium, no place ahead.
2. **How much.** A claim is the ticket's `pay_in.claim_amount`, which the template holds equal to `price.fixed`: the price fixed when the builder held it, before work. Never the inference actually spent, never more. One claim per ticket.
3. **Order: first accepted, first repaid.** Each hoster has one line, in the order claims joined. Money always goes to the oldest claim that is still owed. A later claim never jumps an earlier one.
4. **What feeds it.** When a month is over, the hoster puts in half of that month's profit, from its public books, less what serving builder credit cost it that month (credit honoured x its cost to serve $1 of credit). This keeps Jordi's bound for the two together: a hoster never pays out more than half its monthly profit. Credit comes off first because it is honoured during the month as builders spend it; the queue is settled after the month closes. The books live in the credit ledger's `hosters`, one copy for both ledgers.
5. **Partial payments.** If the month's money is less than the oldest claim, that claim gets all of it and stays first in line. The next month pays the rest before anyone behind it. A claim is closed the moment it is paid in full.
6. **Never more, never twice.** Payments to one claim add up to its fixed price at most. A closed claim takes no further payment. A month funds the queue once.
7. **No interest, no deadline.** A claim does not grow while it waits. A month with no profit puts nothing in and nobody is owed more for it. If the project never earns, nothing is repaid and nobody owes anything ([repayment-currency.md](repayment-currency.md)).
8. **Unused money stays with the hoster.** If the line is empty, the rest of that month's half is not held back for later claims. The queue is a ceiling on what is paid, not a deposit.

Nobody on the project calls a claim a stake, share, investment or return. It is repayment of a cost (L-1, [design principle 1](design-principles.md#1-payment-not-stake)).

## Entries

| Type | Fields | Checked |
|---|---|---|
| `claim` | kind (`ticket` or `bootstrap`), holder, hoster, ticket, epic, row, accepted, cents, evidence; a ticket claim adds price_cents and source, a bootstrap claim cost_basis | row done in its spine, cents = the fixed price, one per ticket, not paid in credit or units, not before acceptance |
| `fund` | hoster, month, profit_cents, credit_cost_cents, cents | the month is over, funded once, cents = half the profit less the credit cost, from the credit ledger's books |
| `pay` | holder, hoster, claim, fund, cents | the oldest open claim of that hoster, never over its price, never on a closed claim, never more than the fund has left |

Every entry also has `seq`, `date` and `prev` (the sha256 of the entry before it), so a rewrite of history breaks the chain. Money is in whole US cents.

## Commands

`claim --ticket <file> --evidence <link>`, `bootstrap --holder --hoster --ref --epic --row --cents --cost-basis --evidence`, `settle --hoster --month` (fund a closed month and pay the line), `balance`, `verify`, `demo`.

## Worked run on EXAMPLE-1

[EXAMPLE-1](../tickets/EXAMPLE-1.md) is the template's worked ticket: posted and held at $10. In the real ledgers Ana picked credit and was credited $20, so the queue refuses a cash claim for it. `queue.py demo` reads it again as if she had picked cash, in memory, and puts two more example builders behind her. Zenod's November books are the credit ledger's (profit $45.95, the E0-S13 small-scale assumption); December and January are assumed equal. Dee, a fourth example builder, spent $20 of credit at Zenod in November. Nothing is written to the ledgers.

```
Line at Zenod: Ana (example builder) $10.00, Ben (example builder) $15.00, Cy (example builder) $12.50
2026-11: half of $45.95 profit = $22.97, less $9.48 credit served = $13.49 in; Ana (example builder) $10.00; Ben (example builder) $3.49
2026-12: half of $45.95 profit = $22.97, less $0.00 credit served = $22.97 in; Ben (example builder) $11.51; Cy (example builder) $11.46
2027-01: half of $45.95 profit = $22.97, less $0.00 credit served = $22.97 in; Cy (example builder) $1.04
#1 Ana (example builder) · EXAMPLE-1 · claim $10.00 · paid $10.00 · left $0.00 · paid in full
#2 Ben (example builder) · EXAMPLE-2 · claim $15.00 · paid $15.00 · left $0.00 · paid in full
#3 Cy (example builder) · EXAMPLE-3 · claim $12.50 · paid $12.50 · left $0.00 · paid in full
refused, paying Ana again: claim 1 is already paid in full (no claim is paid twice)
refused, a second claim for EXAMPLE-1: EXAMPLE-1 already has a claim (one claim per ticket)
```

Ana is paid in full in the first month. Ben is paid in two parts, Cy in two. Nobody gets a cent above the fixed price. In January $21.93 is left over and stays with Zenod.

## What is in the ledger now

Nothing. No accepted Nectary ticket has picked cash yet. The first real claim is written by `queue.py claim` when one does.

## Not settled here

- Who runs the hidden tests and jury, and the rule that accepts a row: [verification.md](verification.md) (E0-S4). A row is set done only on an accepted verdict; the queue trusts that `done`.
- Paying out cash at all needs a hoster with real profit and real books. Zenod's numbers are a model until it publishes them; no money moves before that.

*Not legal, securities, tax or accounting advice.*
