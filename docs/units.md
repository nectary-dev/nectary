# Units: the spec (E0-4)

Rules for **spend-only service units**, the contributor's alternative to a capped revenue claim. Why they exist and what was weighed: [repayment-currency.md](repayment-currency.md). The ledger is [ledger/units.json](../ledger/units.json); the tool that writes and checks it is [tools/units.py](../tools/units.py).

## Definition

- **1 unit = 1,000 Zenod memory operations** (one operation = one memory saved or recalled through Zenod). Units are priced in that service only, never in dollars or euros.
- **Redemption is not live yet.** Zenod's team has been asked whether Zenod is the service units are spent on. Until they agree, units are recorded and can be counted, but nothing can be bought with them. If Zenod says no, the service named here changes before any unit is spent, and the ledger says so.

## Rules

1. **Issued only for accepted tickets.** A unit is awarded only when the ticket's row in its epic's Issue Ledger has status `done` (accepted). Never per line, commit or pull request size.
2. **Rate fixed before work.** Each ticket's units are written in the ledger's `rates` before work starts. The award equals that rate, no more.
3. **Choice per ticket.** For each ticket the contributor picks `units` or `claim` (a capped revenue claim, repaid at cost from repo revenue). A ticket paid as a claim earns no units; never both.
4. **Public cap per epic.** Each epic's total units are written in the ledger before its tickets open. Awards beyond the cap are invalid.
5. **Non-transferable.** Only the holder spends their units. The ledger has no transfer entry; units cannot be sold, sent or pooled.
6. **Burned when spent.** A spend entry destroys the units it uses. Supply only shrinks through use.
7. **No price talk.** Nobody on the project says units will rise in value. The team's own units follow the same rates and caps, with no founder premium.

## The ledger

`ledger/units.json` is public and append-only. Each entry is `award` or `spend` with: `seq`, `date`, `holder`, `epic`, `row`, `units`, `evidence` and `prev` (the hash of the entry before it, so any rewrite of history breaks the chain). Awards also carry `rate`.

`python3 tools/units.py verify` fails when: an entry type is not award or spend, the hash chain or order breaks, an award's row is not `done` in its spine, the award differs from the rate fixed for it, a ticket is paid twice or was chosen as a claim, an epic goes over its cap, or a spend takes a holder below zero.

## Seed repo

Nectary itself is the first seed repo: its own EPIC-0 tickets are the work. EPIC-0's cap is **1,000 units**; each EPIC-0 ticket is offered at **100 units**. E0-S1 and E0-S5 got their rate on 2026-11-11, after their work had started, because the ledger did not exist yet; the ledger marks them `seed_exception`. Every later ticket gets its rate before work.

*Not legal, securities, tax or accounting advice.*
