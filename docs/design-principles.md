# Design Principles

These principles constrain every part of Nectary: naming, contracts, marketing copy, ticket templates, and instrument design. When a proposal conflicts with one of these, the proposal loses.

## 1. Payment, not stake

**The instrument is a debt repayment for contributed cost. It is not equity, not a share in any company, not a security, and not profit participation.**

A contributor's claim is repayment of the cost they contributed, paid out of repo revenue, **capped at the contributed cost**. No return. No upside multiple. No revenue share beyond the cap.

This is the central legal-design principle of the project. It keeps the instrument simple to account for (a payable, a cost, a repayment — standard bookkeeping with no ambiguity) and keeps it away from securities framing: language like *stake*, *share*, *investment*, or *return* implies an expectation of profit and pulls the instrument toward Howey-style analysis. Those words are banned from naming, copy, and contract language.

The claim is binary in operation: at maturity it is either repaid from the revenue queue up to the eligible cost cap, or it is not. It does not accrue interest while it waits.

## 2. Claims attach to auditable deliverables

Revenue-backed repayment needs something testable to attach to. The unit of fundable work is a **well-described, testable ticket** — not a vague promise, not "effort."

A funding-grade ticket specifies:

- **Acceptance criteria** — how the deliverable is tested, written before work starts.
- **Evidence requirements** — what proof of completion looks like.
- **Eligible cost** — what counts toward the cap, and how it's accounted.
- **Repayment trigger** — the condition under which the claim becomes payable from the queue.

The deliverable is attached to the claim. The contributor knows exactly what is owed and exactly what must be demonstrated.

## 3. The rules live in the repo

Game mechanics are written down where anyone can read them: the queue, the tickets, the verification rules, the repayment terms. A contributor should be able to trace the full chain — repo → queue → revenue → repayment — without trusting a person's word. Trust comes from the legibility of the system, not the reputation of the operator.

Known open problem, tracked honestly: some human ultimately controls the repository. The trust chain has that link, and the project's stance is to state it plainly and design around it over time rather than pretend it away.

## 4. Humans and agents on equal terms

Tickets carry machine-readable acceptance criteria so AI agents can discover, complete, and claim work the same way humans do. Nectary assumes a world where pointing an LLM at a repo — "mining" it — is a normal way to contribute, and the reward mechanism must work identically for both kinds of contributor.

## 5. Bootstrap cost is a cost like any other

The person who bootstraps a project may record their initial labor and already-spent money as a payable contribution — quantified as **reimbursable cost**, exactly like any other claim. No founder premium, no privileged upside. The first contributor goes in the same queue under the same cap.

## 6. The story is the cycle, not the money

Public copy explains incentives and replenishment through the cycle metaphor (see [name.md](name.md)); contract language explains capped repayment of eligible contributed cost. Neither side of the story may imply ownership, speculative upside, or a revenue share.

---

*Nothing in this repository is legal, securities, tax, or accounting advice. These are design constraints the project applies to itself.*
