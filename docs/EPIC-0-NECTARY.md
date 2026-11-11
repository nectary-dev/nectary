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
Goal sentence: Let a repo pay its builders from its revenue or in its own service units, capped at cost.

## Goal

Define and ship the minimal open protocol and tooling for ticket-backed, capped, revenue-repaid cost claims, so a repository can fund its own development: contributors (humans or AI agents) complete testable tickets, completed work becomes an auditable cost claim, and repo revenue repays claims through a public queue up to cost, never above it ([mission](mission.md), [README](../README.md)). Why: open-source and agent-driven repos have large backlogs of testable work but no credible way to say "do this, prove it, and be repaid your cost from this project's revenue".

## Done means
<!-- Taken from the Objective in docs/mission.md (2026-06-12). The owner has not yet confirmed these as acceptance criteria or set evidence for them. -->

- [ ] E0-1 Funding-grade ticket template: a published template whose tickets carry acceptance criteria, evidence requirements, eligible-cost accounting and a repayment trigger ([principle 2](design-principles.md#2-claims-attach-to-auditable-deliverables)).
- [ ] E0-2 Repayment queue: revenue flows to a queue that repays eligible contributors in order, up to their eligible contributed cost and no further, written as rules in the repo.
- [ ] E0-3 Verification: submissions are tested against the ticket's deliverable, and approval and repayment follow rules written in the repo, not operator discretion.
- [ ] E0-4 Spend-only service units work on one seed repo: each accepted ticket earns non-transferable units priced in the service (burned when spent, capped issue per epic), recorded in a public ledger in that repo, as the contributor's alternative to a capped revenue claim (Jordi, market-bots E3-S2, 2026-11-11).

## Current State

Owner: Jordi (AlfaBlok); root steward: repo delivery manager
Status: active
Last attempted: 2026-11-11 E0-S5 integrated (run_f4b01362: units spec, ledger, tool with tests, page :8974, card), verified by the Delivery Manager: tests pass, verify passes, page 200
Result: spend-only units work on Nectary as the first seed repo (100 units awarded for E0-S1); spending waits on Zenod agreeing to be the service; E0-S5 in review for Jordi
Evidence: commits 352bb42, 58b30fa on main ; [units page](http://vps3.taild81fbb.ts.net:8974/) ; [units rules](units.md)
Waiting on: Jordi's review of the E0-S5 card ; Zenod's answer to desk note c9f55149 (redemption)
Approved work: none open beyond E0-S5's review
Next action: on Jordi's close of E0-S5, its followups start (pay accepted EPIC-0 tickets in units) and E0-S2 (ticket template) gets readied; place Zenod's answer when it comes
Source revision: main @ 58b30fa
Verified at: 2026-11-11

## Waiting on

- [answered EPIC-0-A1 2026-11-11 @Jordi · done 2026-11-11 7f37510] Is Nectary still an active goal, and are E0-1..E0-3 (from docs/mission.md) its Done means? — answer: active again; voice note vn_322d841c on market-bots E3-S1: "I like the idea of reactivating Nectary, because I think it's actually super important" — the Done means stay as drafted until his repayment-currency decision (row E0-S1) lands, since a utility token would change E0-2 and the Non-Goals
- [answered EPIC-0-A2 2026-11-11 @Delivery-Manager] Branch `origin/add-nectary-hero-image` (hero SVG for nectary.dev, 2026-07-05) is not in main — answer: merged into main (one new file, assets/images/nectary-hero.svg) — why: additive, nothing uses it yet, keeps the art for the future site and clears the stale branch — rollback: delete the file

## Non-Goals

Not an investment platform, equity, governance-by-wealth or sellable token launch; no return above contributed cost; spend-only service units are allowed as payment in kind (Jordi, 2026-11-11), a sellable token only after a lawyer's yes ([mission](mission.md#what-nectary-is-not)). Nothing here is legal, securities, tax or accounting advice. Memory guardian and miner roles of the [system loop](system-loop.md) belong to other projects (e.g. Zenod), not this repo.

## Pages

- [Mission & objective](mission.md): what Nectary is for and is not; source of Goal and Done means.
- [Design principles](design-principles.md): payment-not-stake and the other constraints every proposal must pass.
- [Repayment currency](repayment-currency.md): Jordi's choice (2026-11-11): per ticket a capped revenue claim or spend-only service units; unit rules; the lawyer question that gates a sellable token.
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
| E0-S1 | Researcher | run_69ad9c34-dd69-4364-b438-dcd26f4b7b41 (finished 2026-11-11) | Repayment currency: revenue-backed claims vs the app's own utility tokens; one page, bottom line first, compare upside, accounting, securities risk and what projects do today; recommend; feeds a coded ask | done (no confirm: Jordi approved the research card market-bots E3-S1; docs record his choice) | none (market-bots E3-S1 done, approved by Jordi 2026-11-11) | main | main | 181f9c9: docs/repayment-currency.md + design-principles, mission, README amended (research market-bots 351b64f, choice 58699a7) | 2026-11-11 | followups: started E0-S5 (units ledger on one seed repo); confirm: none |
| E0-S2 | Ticket worker | unassigned | E0-1: funding-grade ticket template (acceptance, evidence, eligible cost, repayment trigger) | draft | E0-S1 | none | main | none | 2026-11-11 | waits for the repayment-currency decision |
| E0-S3 | Ticket worker | unassigned | E0-2: repayment queue rules in the repo (order, cap at cost, the currency E0-S1 settles) | draft | E0-S1 | none | main | none | 2026-11-11 | waits for the repayment-currency decision |
| E0-S4 | Ticket worker | unassigned | E0-3: verification rules (submissions tested against the ticket, approval and repayment by written rule) | draft | E0-S2 | none | main | none | 2026-11-11 | after the template exists |
| E0-S5 | Ticket worker | run_f4b01362-f1ea-4709-9d2c-c16a3700227b | E0-4: spend-only service units ledger on one seed repo (market-bots E3-S2) | review | E0-S1 | none | main | [units page](http://vps3.taild81fbb.ts.net:8974/) · [card](cards/E0-S5.md) · [spec](units.md) · 352bb42 (verify OK, 10 tests) · E0-S1 awarded 100 · Zenod asked (zenod c9f55149) | 2026-11-11 | followups: start pay accepted EPIC-0 tickets in units — rates fixed; park redemption — waits for Zenod's yes; confirm: yes — Jordi judges whether units on the seed repo are what he asked for |

## Decisions

| Date | Outcome | Decision / Attempt | Durable Summary | Evidence | Revisit When |
|---|---|---|---|---|---|
| 2026-11-11 | accepted | Repayment currency chosen by Jordi; E0-4 and E0-S5 ready (L-37) | Jordi approved market-bots E3-S1 iteration 2 (units now, sellable token only after a lawyer) and started E3-S2 "restart Nectary with spend-only service units on one seed repo" (market-bots 58699a7, desk note 30c71a6). Settles E0-S1's question without an EPIC-0-A3 ask; adds Done means E0-4 and row E0-S5; Non-Goals now bar a sellable token, not units. | market-bots 58699a7, 351b64f | a lawyer answers the resale question |
| 2026-11-11 | accepted | decided by Delivery Manager: merge hero SVG branch (EPIC-0-A2) | additive asset, not ask tier — why: stale 4 months, harmless — rollback: delete assets/images/nectary-hero.svg | merge commit on main | site work starts |
| 2026-11-11 | accepted | Nectary reactivated; E0-S1 ready on Jordi's ask (L-37) | Jordi, voice note vn_322d841c on market-bots E3-S1, 2026-11-11: "I like the idea of reactivating Nectary, because I think it's actually super important, but … what about you're paid back in utility tokens? … you're paid back in the currency of the app itself … this currency will have an FX, and that's how you account for it … if you exchange for the utility token, then you have more upside … it's not you're compensated by the efforts of others. This is a payment in kind for your effort. What do you think?" Readies E0-S1 (compare and recommend); E0-S2..S4 drafted for E0-1..E0-3 behind it. | vn_322d841c | his EPIC-0-A3 answer |
| 2026-10-24 | accepted | Root spine for nectary | Goal and Done means from docs/mission.md, not invented; owner to confirm. Concept docs are pages, no child epic: none is an active plan. | EPIC-3-A1 answer 2026-10-24 | owner confirms the goal |
