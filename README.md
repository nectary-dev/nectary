# Nectary

**A funding protocol for open-source repos.**

Contributors complete well-defined tasks and receive capped, revenue-repaid cost claims — no equity, no tokens, no upside participation. If the repo generates revenue, contributors are repaid up to their eligible contributed cost.

## The idea in one paragraph

Every meaningful piece of work in a repo can be expressed as a testable GitHub issue. When a contributor (human or agent) completes that issue, a cost claim is recorded against the repo: a specific amount, tied to a specific deliverable, capped at cost. No profit multiple. No stake. If the repo later earns revenue, revenue flows into a repayment queue and outstanding claims are paid in order. If the repo never earns, no one owes anyone anything.

## Key properties

- **Payment, not investment.** Claims are repayment of contributed cost. No equity, no revenue share, no return above cost.
- **Auditable.** Claims are attached to merged PRs and accepted deliverables. Every claim has a provenance link.
- **Agent-friendly.** Issues have machine-readable acceptance criteria. AI agents can pick up, complete, and get credit for tasks the same way humans do.
- **No gatekeeping.** The protocol is open. Any repo can adopt it.

## Documentation

- [Mission & objective](docs/mission.md) — what Nectary is for and what it is not
- [Design principles](docs/design-principles.md) — payment-not-stake and the other constraints that govern every decision
- [Why "Nectary"](docs/name.md) — the flower/bee metaphor and what it is (and isn't) allowed to mean
- [The system loop](docs/system-loop.md) — memory → mining → queue → execution, and Nectary's role as queue drainer

## Status

Pre-alpha. Defining the protocol spec and ticket template.

## License

[MIT](LICENSE)
