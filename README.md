# Nectary

**A funding protocol for open-source repos.**

Contributors complete well-defined tasks and receive capped, revenue-repaid cost claims — or, if they choose per ticket, spend-only service units of the app as payment in kind. No equity, no sellable token, nothing above cost on revenue claims. If the repo generates revenue, contributors are repaid up to their eligible contributed cost.

## The idea in one paragraph

Every meaningful piece of work in a repo can be expressed as a testable GitHub issue. When a contributor (human or agent) completes that issue, a cost claim is recorded against the repo: a specific amount, tied to a specific deliverable, capped at cost. No profit multiple. No stake. If the repo later earns revenue, revenue flows into a repayment queue and outstanding claims are paid in order. If the repo never earns, no one owes anyone anything.

## Key properties

- **Payment, not investment.** Claims are repayment of contributed cost. No equity, no revenue share, no return above cost.
- **Or payment in kind.** Per ticket, a contributor may take spend-only service units instead: priced in the app's service, non-transferable, burned when spent, capped per epic. No sellable token before a lawyer's yes ([repayment currency](docs/repayment-currency.md)).
- **Auditable.** Claims are attached to merged PRs and accepted deliverables. Every claim has a provenance link.
- **Agent-friendly.** Issues have machine-readable acceptance criteria. AI agents can pick up, complete, and get credit for tasks the same way humans do.
- **No gatekeeping.** The protocol is open. Any repo can adopt it.

## Documentation

- [Mission & objective](docs/mission.md) — what Nectary is for and what it is not
- [Repayment currency](docs/repayment-currency.md) — capped revenue claims or spend-only service units, and why no sellable token yet
- [Units](docs/units.md) — the unit rules, with the public [ledger](ledger/units.json) and `python3 tools/units.py verify`
- [Design principles](docs/design-principles.md) — payment-not-stake and the other constraints that govern every decision
- [Why "Nectary"](docs/name.md) — the flower/bee metaphor and what it is (and isn't) allowed to mean
- [The system loop](docs/system-loop.md) — memory → mining → queue → execution, and Nectary's role as queue drainer

## Status

Pre-alpha. Defining the protocol spec and ticket template.

## License

[MIT](LICENSE)
