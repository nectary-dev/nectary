# Mission & Objective

## Mission

Direct revenue to the contributors of an open-source repository in a way that is **maximally transparent**.

Nectary exists so that a repository can fund its own development: work is expressed as testable tickets, completed work becomes auditable cost claims, and revenue — if and when it arrives — repays those claims through a public queue. The goal is a self-sustaining cycle where an idea, captured in a repo, can attract the human and machine effort needed to materialize itself.

## Objective

Build the minimal protocol and tooling for **ticket-backed, capped, revenue-repaid cost claims**:

1. **Funding-grade tickets.** A ticket is funding-grade when it has acceptance criteria, evidence requirements, eligible-cost accounting, and a repayment trigger. Vague promises are not fundable; auditable deliverables are.
2. **A repayment queue.** Revenue flows to a queue. Eligible contributors are repaid from that queue, in order, up to their eligible contributed cost — and no further.
3. **Verification.** Submissions are tested against the deliverable described in the ticket. Approval and repayment follow the rules written in the repo, not the discretion of an operator.

## What Nectary is not

- It is **not** an investment platform. Claims carry no return, no upside multiple, no profit participation.
- It is **not** equity or governance-by-wealth. Holding a claim is being owed a payment, not owning a piece of anything.
- It is **not** a token launch. The mechanism is bookkeeping: cost in, capped repayment out.

## Why this matters

Open-source projects — especially AI-agent-driven ones — generate enormous backlogs of well-understood, testable work. What's missing is a credible way for a repo to say: *"do this specific thing, prove you did it, and you will be repaid your cost out of the revenue this project earns."* Nectary is that missing piece: simple enough to account for, open enough to audit, and neutral enough that humans and agents participate on the same terms.

See [design-principles.md](design-principles.md) for the constraints that govern every design decision, and [system-loop.md](system-loop.md) for where Nectary sits in the larger memory → backlog → execution cycle.
