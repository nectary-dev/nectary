# The Nectary ticket template (E0-1)

**Every Nectary ticket is priced before work, tested by its own and hidden tests, and pays 2x its fixed price in service credit, or that price in cash at cost.** This is the rule Jordi said yes to on 2026-11-26 (EPIC-0-A5): "Yes: build the ledger and ticket board on 2x the price set before work".

```
 estimate ──> posted ──> held ──────> submitted ──> accepted ──> paid
 8 runs x     $10        price fixed   tests, hidden  row done     credit 2x price ($20)
 $1.20        +25% per   ($10 / 12.50  tests, jury                 or claim 1x price ($10)
 = $9.60      48 h       / 15 cap)     2 of 3                      or units at the fixed rate
```

- Machine-readable form: [ticket.schema.json](ticket.schema.json). The ticket board (E0-S11) and the credit ledger (E0-S10) read tickets through it.
- Validator: `python3 tools/ticket.py check tickets/*.md` (tests: `python3 -m unittest tests.test_ticket`).
- Worked example: [tickets/EXAMPLE-1.md](../tickets/EXAMPLE-1.md).
- Price helper: `python3 tools/ticket.py ladder --runs 8` prints the estimate, the ladder and the credit at each step.

## What a ticket is

One Markdown file in `tickets/`. It opens with a JSON object between two `---` lines (the front matter: what machines read), then six `##` sections for people: **Deliverable, Acceptance, Evidence, Eligible cost, Price and credit, Repayment trigger**. The validator refuses a ticket that is missing any of them.

## The four parts every funding-grade ticket carries

From [design principle 2](design-principles.md#2-claims-attach-to-auditable-deliverables):

| Part | Front matter | Rule |
|---|---|---|
| Acceptance criteria | `acceptance.tests`, `acceptance.hidden_tests`, `acceptance.jury` | At least one test the builder can run, written before work. At least one hidden test, held by the hoster, whose file's `sha256` is posted with the ticket so it cannot change later. A jury of at least 3 AI models; a majority must pass it. |
| Evidence | `evidence` | The list of proofs an accepted ticket must show. At least one; normally the commit, the test log, the hidden test result, the jury verdicts and the run log. |
| Eligible cost | `eligible_cost` | What counts (agent runs on this ticket), what does not, and how it is recorded. `basis` is always `fixed_price`: the amount owed is set by the price fixed before work, never by tokens counted after. |
| Repayment trigger | `repayment_trigger` | When the ticket pays (its row is accepted) and what each currency then does: credit issued, claim queued, units awarded. |

## The price, set before work

| Field | Meaning | Rule the validator checks |
|---|---|---|
| `price.estimate.runs`, `run_cost`, `amount` | The AI estimator's guess in agent runs, at $1.20 a run | `amount` = runs x run_cost |
| `price.estimate.basis`, `by`, `at` | What it read (tests, files, past tickets), who, when | made before `posted_at` |
| `price.posted`, `posted_at` | The first price, the estimate rounded to whole dollars | `posted` = round(amount); an estimate above $50 must be split |
| `step_up`, `step_hours` | Nobody holds it in 48 h: price rises 25% | fixed at 0.25 and 48 |
| `cap_multiple`, `ticket_max`, `price_cap` | The hoster's ceiling | `price_cap` = min(1.5 x posted, $50) |
| `held_at`, `fixed` | When a builder held it, and the price then | `fixed` = the ladder step for the 48 h windows that passed, never above the cap; required once the ticket is held |
| `requotes` | Old quotes, each with the change the hoster made | only a hoster's change to the ticket re-quotes it; the builder may then drop it |

The builder keeps any saving and carries any overrun: Ana's 7 runs ($8.40) on a $10 ticket still pay $20 of credit; 11 runs ($13.20) pay the same.

## Pay: one currency per ticket, chosen by the builder

| `pay_in.choice` | What the builder gets | Rule |
|---|---|---|
| `credit` | `credit.multiple` x `price.fixed` in the hoster's service (`service`) | `credit.amount` = multiple x fixed. The multiple starts at 2x; it is reset monthly from public books for new tickets (`credit.multiple_month`), and credit already issued never shrinks. |
| `claim` | `pay_in.claim_amount` in cash from revenue, through the repayment queue | equals `price.fixed`, 1x, never more |
| `units` | `pay_in.units_rate` service units ([units.md](units.md)) | rate fixed before work, under the epic's cap |
| `open` | not chosen yet | allowed until accepted; never two currencies |

## Words

No ticket says stake, share, investment or return, in any field or section (L-1). The validator refuses them everywhere except test commands. Cash is repayment of cost, capped at the fixed price.

## Status

`posted` → `held` → `submitted` → `accepted` or `rejected`; `withdrawn` when the hoster pulls it. A held, submitted, accepted or rejected ticket must name its `builder` and its fixed price. The row's status in its spine stays the source of truth for acceptance; the ticket's `status` mirrors it for the board.

## What this template does not settle yet

- The order and pace of the cash repayment queue: E0-2, row E0-S3.
- Who runs the hidden tests and jury, and the rule that approves: E0-3, row E0-S4.
- How the estimator learns (10% lower after a ticket taken at once): the ticket board, E0-S11.

*Not legal, securities, tax or accounting advice.*
