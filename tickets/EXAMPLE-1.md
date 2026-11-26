---
{
  "template": "nectary-ticket/1",
  "id": "EXAMPLE-1",
  "example": true,
  "title": "Zenod recall takes a --since date filter",
  "epic": "EXAMPLE",
  "row": "EXAMPLE-1",
  "hoster": "Jordi (Zenod Hosted)",
  "service": "Zenod Hosted",
  "status": "accepted",
  "builder": "Ana (example builder)",
  "deliverable": "zenod recall accepts --since YYYY-MM-DD and lists only memories saved on or after that day, in the CLI and the API.",
  "acceptance": {
    "tests": [
      {"id": "T1", "checks": "recall --since 2026-11-01 lists only memories saved on or after 1 Nov", "cmd": "pytest tests/test_recall_since.py::test_filters_by_day"},
      {"id": "T2", "checks": "recall without --since lists the same memories as before the change", "cmd": "pytest tests/test_recall_since.py::test_no_flag_unchanged"},
      {"id": "T3", "checks": "a malformed date is refused with a clear message and exit code 2", "cmd": "pytest tests/test_recall_since.py::test_bad_date"},
      {"id": "T4", "checks": "the API takes since= with the same meaning as the CLI flag", "cmd": "pytest tests/test_api_recall.py::test_since_param"},
      {"id": "T5", "checks": "the whole suite still passes", "cmd": "pytest"}
    ],
    "hidden_tests": {"count": 7, "held_by": "hoster", "sha256": "66f328067e680d5e7ce9905b78d03a7efef60e1b5a684dfd8f95c2fcaac7796d"},
    "jury": {"models": 3, "pass": 2}
  },
  "evidence": [
    "commit SHA of the submission on a branch the hoster can fetch",
    "log of the ticket's own tests T1 to T5, all passing",
    "result of the hidden tests, run by the hoster on that commit, all passing",
    "the three jury verdicts, at least 2 saying the change does what the deliverable says and nothing else",
    "the run log: one line per agent run with its run id"
  ],
  "eligible_cost": {
    "counts": ["agent runs spent on this ticket, at the price fixed before work"],
    "excludes": ["runs on other tickets", "hardware, rent or salaries", "time spent after the ticket was rejected"],
    "recorded_as": "the run log in the evidence; it is kept for the record and never changes the amount owed",
    "basis": "fixed_price"
  },
  "price": {
    "currency": "USD",
    "estimate": {
      "by": "Nectary AI estimator",
      "at": "2026-11-26T09:00Z",
      "runs": 8,
      "run_cost": 1.2,
      "amount": 9.6,
      "basis": "5 own tests and 7 hidden, 3 files touched, similar recall tickets took 7 to 9 runs"
    },
    "posted": 10,
    "posted_at": "2026-11-26T09:05Z",
    "step_up": 0.25,
    "step_hours": 48,
    "cap_multiple": 1.5,
    "ticket_max": 50,
    "price_cap": 15,
    "held_at": "2026-11-26T15:40Z",
    "fixed": 10
  },
  "credit": {"multiple": 2, "multiple_month": "2026-11", "amount": 20},
  "pay_in": {"choice": "credit"},
  "repayment_trigger": {
    "when": "the row is accepted in its spine: own tests and hidden tests pass on the submitted commit and at least 2 of 3 jury models agree",
    "credit": "the credit ledger issues 2 x the fixed price as Zenod Hosted service credit to the builder the day the row is accepted",
    "claim": "a cash claim of the fixed price, never more, joins the repayment queue in order and is repaid from revenue",
    "units": "the units ledger awards the rate fixed before work, under the epic's cap (docs/units.md)"
  },
  "requotes": []
}
---

# EXAMPLE-1: Zenod recall takes a --since date filter

*A worked example of [the ticket template](../docs/ticket-template.md), with the numbers from the [economics page](http://vps3.taild81fbb.ts.net:8976/). Ana and this ticket are illustrations, not real work.*

## Deliverable

`zenod recall` accepts `--since YYYY-MM-DD` and lists only memories saved on or after that day. The API takes `since=` with the same meaning.

## Acceptance

The builder runs tests T1 to T5 (in the front matter). The hoster then runs 7 hidden tests whose file hashes to the `sha256` posted with the ticket, so nobody can change them after the fact. Three AI models read the diff and the deliverable; at least 2 must say the change does what it says and nothing else.

## Evidence

The commit, the log of T1 to T5, the hidden test result, the three jury verdicts and the run log. Nothing is accepted without all five.

## Eligible cost

What is owed is set by the price fixed before work, never by tokens counted after it. Ana's agent took 7 runs ($8.40): she keeps the $1.60 saving. Had it taken 11 runs ($13.20), she would still get the same: the builder carries an overrun.

## Price and credit

| Step | Value |
|---|---|
| Estimate | 8 runs x $1.20 = $9.60 |
| Posted | $10, 26 Nov 09:05 UTC |
| Ladder if nobody holds it | $10, then $12.50 after 48 h, then $15 (cap: 1.5x, never above $50) |
| Held by Ana | 26 Nov 15:40 UTC, inside the first 48 h: fixed at $10 |
| Credit at 2x (November multiple) | $20 of Zenod Hosted service, about two months |
| Cash claim instead | $10 from revenue, never more |
| Hoster's cost to serve the credit | about $9.48 (95 cents per $1 of price) |

The price is re-quoted only when the hoster changes the ticket; Ana could then drop it.

## Repayment trigger

Ana chose credit. When the row is accepted, the credit ledger issues $20 of Zenod Hosted service to her that day.
