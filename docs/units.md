# Units: the spec (E0-4)

Rules for **transferable service units**, the contributor's alternative to a capped revenue claim. Why they exist and what was weighed: [repayment-currency.md](repayment-currency.md). The ledger is [ledger/units.json](../ledger/units.json); the tool that writes and checks it is [tools/units.py](../tools/units.py).

## Definition

- **1 unit = 1,000 Zenod memory operations** (one operation = one memory saved or recalled through Zenod). Units are priced in that service only, never in dollars or euros.
- **Redemption is not live yet.** Zenod's team agreed in principle on 2026-11-11 to be the service units are spent on; going live costs money and waits for Jordi's yes (parked as E0-S6). Until then, units are recorded, counted and can be transferred, but nothing can be bought with them. If Zenod says no, the service named here changes before any unit is spent, and the ledger says so.

## Rules

1. **Issued only for accepted tickets.** A unit is awarded only when the ticket's row in its epic's Issue Ledger has status `done` (accepted). Never per line, commit or pull request size.
2. **Rate fixed before work.** Each ticket's units are written in the ledger's `rates` before work starts. The award equals that rate, no more.
3. **Choice per ticket.** For each ticket the contributor picks `units` or `claim` (a capped revenue claim, repaid at cost from repo revenue). A ticket paid as a claim earns no units; never both.
4. **Public cap per epic.** Each epic's total units are written in the ledger before its tickets open. Awards beyond the cap are invalid.
5. **Transferable between holders.** A holder can move units to another holder with a `transfer` entry in the ledger. Nothing is issued or burned by a transfer. A transfer is refused if it is to oneself, of zero or fewer units, or of more than the sender holds. The project never sells units, never lists them on an exchange and never talks about their price.
6. **Burned when spent.** A spend entry destroys the units it uses. Supply only shrinks through use.
7. **No price talk.** Nobody on the project says units will rise in value. The team's own units follow the same rates and caps, with no founder premium.

## The ledger

`ledger/units.json` is public and append-only. Each entry is `award`, `transfer` or `spend`, with `seq`, `date`, `holder`, `units` and `prev` (the hash of the entry before it, so any rewrite of history breaks the chain). Awards and spends also carry `epic`, `row` and `evidence`; awards carry `rate`. A transfer carries `to` (the receiver) and an optional `note`; its `holder` is the sender.

`python3 tools/units.py verify` fails when: an entry type is not award, transfer or spend, the hash chain or order breaks, an award's row is not `done` in its spine, the award differs from the rate fixed for it, a ticket is paid twice or was chosen as a claim, an epic goes over its cap, a transfer or spend takes a holder below zero, or a transfer goes to its own sender.

Commands: `award --holder --epic --row --evidence`, `transfer --from --to --units [--note]`, `spend --holder --epic --units --evidence`, `balance`, `verify`.

## Seed repo

Nectary itself is the first seed repo: its own EPIC-0 tickets are the work. EPIC-0's cap is **1,000 units**; each EPIC-0 ticket is offered at **100 units**. E0-S1 and E0-S5 got their rate on 2026-11-11, after their work had started, because the ledger did not exist yet; the ledger marks them `seed_exception`. Every later ticket gets its rate before work.

The ledger's second entry is a demonstration transfer on 2026-11-11: 10 of the 100 units awarded for E0-S1 moved from the team account to Jordi, to show transfers working. Nothing was paid for it.

## Risk and the lawyer question

Transferability raises the securities and MiCA risk the research described: units that can change hands can be sold between holders, which the research found is what turns a service voucher toward an investment contract in the US and can remove MiCA's exemptions in the EU ([the research, section 0](http://vps3.taild81fbb.ts.net:8973/), [repayment-currency.md](repayment-currency.md)). The guard rails keep it small: the project never sells or lists units, never talks about their price, and keeps them in this repo's ledger, off-chain. An on-chain token or exchange listing waits for a lawyer's answer to: *"We pay contributors in service units they can transfer to other holders, recorded in a public ledger, never sold or listed by us. Is that a security in the US or a crypto-asset needing a MiCA white paper in the EU, and would putting the units on-chain or on an exchange change the answer?"*

*Not legal, securities, tax or accounting advice.*
