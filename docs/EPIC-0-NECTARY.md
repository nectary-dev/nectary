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
Project name: Nectary
Goal sentence: Let a repo pay the people and agents who build it, out of what the repo earns, capped at their cost.

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
Last attempted: 2026-11-11 run_507cc01d reactivated Nectary on Jordi's voice note vn_322d841c, answered EPIC-0-A1 and EPIC-0-A2, filed E0-S1 ready and E0-S2..S4 draft
Result: pre-alpha, docs only (README, four concept pages, hero SVG now on main); repayment currency is the open design question (E0-S1)
Evidence: commits 7f37510, 826daa4, 576b1f1 on main ; research [inference for tokens](http://vps3.taild81fbb.ts.net:8973/)
Waiting on: E0-S1 holds for market-bots E3-S1 iteration 2 (run_3894ef1e), which is researching the same utility-token question
Monitoring: market-bots run_3894ef1e (E3-S1 iteration 2) since 2026-11-11T00:41Z · next check 2026-11-11T02:45Z its outcome · then dispatch E0-S1 to write the one-pager and raise EPIC-0-A3
Approved work: E0-S1 (Jordi, L-37, 2026-11-11)
Next action: dispatch E0-S1 once run_3894ef1e ends; Jordi's EPIC-0-A3 answer settles E0-2 and the Non-Goals line on tokens
Source revision: main @ 576b1f1
Verified at: 2026-11-11

## Waiting on

- [answered EPIC-0-A1 2026-11-11 @Jordi] Is Nectary still an active goal, and are E0-1..E0-3 (from docs/mission.md) its Done means? — answer: active again; voice note vn_322d841c on market-bots E3-S1: "I like the idea of reactivating Nectary, because I think it's actually super important" — the Done means stay as drafted until his repayment-currency decision (row E0-S1) lands, since a utility token would change E0-2 and the Non-Goals
- [answered EPIC-0-A2 2026-11-11 @Delivery-Manager] Branch `origin/add-nectary-hero-image` (hero SVG for nectary.dev, 2026-07-05) is not in main — answer: merged into main (one new file, assets/images/nectary-hero.svg) — why: additive, nothing uses it yet, keeps the art for the future site and clears the stale branch — rollback: delete the file

## Non-Goals

Not an investment platform, equity, governance-by-wealth or token launch; no return above contributed cost ([mission](mission.md#what-nectary-is-not)). Nothing here is legal, securities, tax or accounting advice. Memory guardian and miner roles of the [system loop](system-loop.md) belong to other projects (e.g. Zenod), not this repo.

## Pages

- [Mission & objective](mission.md): what Nectary is for and is not; source of Goal and Done means.
- [Design principles](design-principles.md): payment-not-stake and the other constraints every proposal must pass.
- [Why "Nectary"](name.md): the flower/bee metaphor and its allowed meaning.
- [The system loop](system-loop.md): memory → mining → queue → execution; Nectary as queue drainer; Zenod as first adopter.
- [Inference for tokens](http://vps3.taild81fbb.ts.net:8973/) (market-bots research, 2026-11-10, [source](https://github.com/AlfaBlok/market-bots/blob/main/docs/research/inference-for-tokens.md), row market-bots E3-S1): who pays tokens for agent work today (Gittensor, FLOP, Naïve, bounty boards); recommends building on Nectary with a non-transferable credits ledger first, no tradable token before a lawyer's read.

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
| draft | Owner | Jordi | Confirm goal and Done means (see Waiting on) | done (EPIC-0-A1 answered: active, 2026-11-11) | none | none | main | vn_322d841c | 2026-11-11 | Done means confirmed with E0-S1's decision |
| E0-S1 | Researcher | unassigned | Repayment currency: revenue-backed claims vs the app's own utility tokens; one page, bottom line first, compare upside, accounting, securities risk and what projects do today; recommend; feeds a coded ask | ready | market-bots E3-S1 iteration 2 (run_3894ef1e, started 2026-11-11T00:41Z on the same question) | main | main | Jordi's ask vn_322d841c 2026-11-11 | 2026-11-11 | when that run ends: write docs/research/repayment-currency.md from its findings plus Nectary's design, raise EPIC-0-A3; close done (fed EPIC-0-A3) |
| E0-S2 | Ticket worker | unassigned | E0-1: funding-grade ticket template (acceptance, evidence, eligible cost, repayment trigger) | draft | E0-S1 | none | main | none | 2026-11-11 | waits for the repayment-currency decision |
| E0-S3 | Ticket worker | unassigned | E0-2: repayment queue rules in the repo (order, cap at cost, the currency E0-S1 settles) | draft | E0-S1 | none | main | none | 2026-11-11 | waits for the repayment-currency decision |
| E0-S4 | Ticket worker | unassigned | E0-3: verification rules (submissions tested against the ticket, approval and repayment by written rule) | draft | E0-S2 | none | main | none | 2026-11-11 | after the template exists |

## Decisions

| Date | Outcome | Decision / Attempt | Durable Summary | Evidence | Revisit When |
|---|---|---|---|---|---|
| 2026-11-11 | accepted | decided by Delivery Manager: merge hero SVG branch (EPIC-0-A2) | additive asset, not ask tier — why: stale 4 months, harmless — rollback: delete assets/images/nectary-hero.svg | merge commit on main | site work starts |
| 2026-11-11 | accepted | Nectary reactivated; E0-S1 ready on Jordi's ask (L-37) | Jordi, voice note vn_322d841c on market-bots E3-S1, 2026-11-11: "I like the idea of reactivating Nectary, because I think it's actually super important, but … what about you're paid back in utility tokens? … you're paid back in the currency of the app itself … this currency will have an FX, and that's how you account for it … if you exchange for the utility token, then you have more upside … it's not you're compensated by the efforts of others. This is a payment in kind for your effort. What do you think?" Readies E0-S1 (compare and recommend); E0-S2..S4 drafted for E0-1..E0-3 behind it. | vn_322d841c | his EPIC-0-A3 answer |
| 2026-10-24 | accepted | Root spine for nectary | Goal and Done means from docs/mission.md, not invented; owner to confirm. Concept docs are pages, no child epic: none is an active plan. | EPIC-3-A1 answer 2026-10-24 | owner confirms the goal |
