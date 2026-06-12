# The System Loop: Memory → Mining → Queue → Execution

Nectary is the third role in a larger self-developing cycle. Understanding the cycle clarifies what Nectary is — and, just as importantly, what it isn't.

> One role captures and organizes evidence into living memory.
> Another mines that memory into prioritized action.
> A third drains the resulting queue through verification, incentives, and execution.
> The outputs and new problems return to memory.

```text
Evidence / conversation / artifacts
        ↓
Memory guardian — captures, cites, organizes, recalls living memory
        ↓
Miner — extracts tasks, priorities, dependencies, next actions
        ↓
Nectary — receives and orders the executable queue
        ↓
Humans / agents execute, submit, verify; claims are approved and repaid
        ↓
Outcomes, receipts, new problems, decisions → back to memory
```

## The three roles

**Memory guardian (librarian).** Captures evidence, preserves sources, and organizes durable meaning so future agents have a trustworthy port of call. In the reference implementation this role is played by [Zenod](https://zenod.dev) — but the pattern generalizes: every repo can have a memory guardian holding its history, design intent, decisions, and unresolved problems.

**Miner (backlog intelligence).** Reads the living memory and surfaces actionable signal: tasks, priorities, dependencies, open problems, candidate tickets, and the evidence needed to verify them. The miner converts persisted thought into a ranked map of what should happen next.

**Nectary (queue drainer).** Drains the backlog. Receives submissions, verifies work against ticket acceptance criteria, approves or declines deliverables, and routes the resulting payment claims under the [payment-not-stake rules](design-principles.md). The role is operational: turn verified work into approved outcomes and route compensation according to the rules written in the repo.

The loop is self-developing because execution produces new evidence and new problems, which fold back into memory, which refines the backlog, which Nectary keeps draining.

## The narrative in one line

```text
Persisted thought → living memory → mined signal → executable queue → verified work → richer memory
```

## Where claims fit

Nectary's repayment mechanism (see [mission.md](mission.md)) is what makes the queue *drainable at scale*: a ticket with acceptance criteria, evidence requirements, an eligible-cost cap, and a repayment trigger is something a stranger — human or agent — can pick up, complete, and be repaid for without anyone needing to trust anyone personally.

## First adopter

Zenod is Nectary's first customer and a natural counterpart: Zenod provides the memory and document infrastructure that makes repo work legible to agents and humans, and Nectary provides the funding mechanism that pays for Zenod's own development. Two projects born together, each proving the other's case.
