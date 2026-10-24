# EPIC-0: Nectary funding protocol

Spine profile: compact
Repository: nectary-dev/nectary
Primary document: docs/EPIC-0-NECTARY.md
Spine ID: nectary-root
Root spine: self
Parent spine: none
Additional root rationale: n/a
Integration branch: main
Integration policy: main-direct

## Goal

Define and ship the minimal open protocol and tooling for ticket-backed, capped, revenue-repaid cost claims, so a repository can fund its own development: contributors (humans or AI agents) complete testable tickets, completed work becomes an auditable cost claim, and repo revenue repays claims through a public queue up to cost, never above it ([mission](mission.md), [README](../README.md)). Why: open-source and agent-driven repos have large backlogs of testable work but no credible way to say "do this, prove it, and be repaid your cost from this project's revenue".

## Done means
<!-- Taken from the Objective in docs/mission.md (2026-06-12). The owner has not yet confirmed these as acceptance criteria or set evidence for them. -->

- [ ] E0-1 Funding-grade ticket template: a published template whose tickets carry acceptance criteria, evidence requirements, eligible-cost accounting and a repayment trigger ([principle 2](design-principles.md#2-claims-attach-to-auditable-deliverables)).
- [ ] E0-2 Repayment queue: revenue flows to a queue that repays eligible contributors in order, up to their eligible contributed cost and no further, written as rules in the repo.
- [ ] E0-3 Verification: submissions are tested against the ticket's deliverable, and approval and repayment follow rules written in the repo, not operator discretion.

## Current State

Owner: Jordi (AlfaBlok); root steward: repo delivery manager
Status: active
Last attempted: 2026-10-24 root spine created (EPIC-3 E3-3, EPIC-3-A1 answered `all`)
Result: pre-alpha, docs only: README plus four concept pages (mission, design principles, name, system loop), 2026-06-12. No protocol spec, ticket template, queue or code yet. Unmerged branch `origin/add-nectary-hero-image` (one SVG for nectary.dev, 2026-07-05, Codex).
Evidence: [README](../README.md) Status "Pre-alpha. Defining the protocol spec and ticket template."; git log main @ 8c7e05b
Waiting on: EPIC-0-A1, EPIC-0-A2 (owner)
Approved work: none beyond keeping this spine true
Next action: owner answers EPIC-0-A1; then the first goal (likely the ticket template, E0-1) gets its own epic via `spine_new.py`
Source revision: main @ 8c7e05b
Verified at: 2026-10-24

## Waiting on

- [ask EPIC-0-A1: decide @Jordi since 2026-10-24] Is Nectary still an active goal, and are E0-1..E0-3 (from docs/mission.md) its Done means? — options: yes | edit them | park (Status: deferred) — recommend: yes, and name the first deliverable (ticket template, per the README) — unblocks: the first child epic — effort: ~2 min — context: [mission](mission.md)
- [ask EPIC-0-A2: decide @Jordi since 2026-10-24] Branch `origin/add-nectary-hero-image` (hero SVG for nectary.dev, 2026-07-05) is not in main — options: merge | drop | keep — recommend: merge if the site still wants it — unblocks: branch cleanup — effort: ~1 min — context: [README](../README.md)

## Non-Goals

Not an investment platform, equity, governance-by-wealth or token launch; no return above contributed cost ([mission](mission.md#what-nectary-is-not)). Nothing here is legal, securities, tax or accounting advice. Memory guardian and miner roles of the [system loop](system-loop.md) belong to other projects (e.g. Zenod), not this repo.

## Pages

- [Mission & objective](mission.md): what Nectary is for and is not; source of Goal and Done means.
- [Design principles](design-principles.md): payment-not-stake and the other constraints every proposal must pass.
- [Why "Nectary"](name.md): the flower/bee metaphor and its allowed meaning.
- [The system loop](system-loop.md): memory → mining → queue → execution; Nectary as queue drainer; Zenod as first adopter.

## Spine Map

No child spines.

The concept pages above are reference pages, not goals.

## Operating Learnings

**Always**

- L-1 | any naming, copy, contract or ticket text | never use stake, share, investment or return language; claims are capped cost repayment | design principle 1, legal framing | confirmed 2026-06-12

**Scoped index**

none

## Issue Ledger

| Issue | Role | Owner / Assignment | Title | Status | Depends On | PR/Branch | Base | Latest Evidence | Last Verified | Next Action |
|---|---|---|---|---|---|---|---|---|---|---|
| draft | Owner | Jordi | Confirm goal and Done means (see Waiting on) | draft | none | none | main | this spine | 2026-10-24 | owner answer |

## Decisions

| Date | Outcome | Decision / Attempt | Durable Summary | Evidence | Revisit When |
|---|---|---|---|---|---|
| 2026-10-24 | accepted | Root spine for nectary | Goal and Done means from docs/mission.md, not invented; owner to confirm. Concept docs are pages, no child epic: none is an active plan. | EPIC-3-A1 answer 2026-10-24 | owner confirms the goal |
