# Verification: how a submission is judged (E0-3)

**A submission is accepted only when its own tests, then the hoster's hidden tests, then 2 of 3 AI jurors pass it; the tool computes the outcome, and the outcome alone pays.** Nobody types "accepted": `tools/verify_ticket.py` writes the verdict from the results, the public record refuses any verdict that does not follow from them, and the credit and cash ledgers pay only an accepted verdict on a row set done.

```
 builder submits ──> 1 own tests ──> 2 hidden tests ──> 3 jury of 3 ──> verdict ──> row done ──> pay
 commit on a        builder can     hoster holds,      fixed prompt,   public,      by the        credit 2x price
 branch the hoster  run them first  hash posted        2 must pass     hash chain   verdict       or cash claim 1x
 can fetch               │                │                 │                                     or units
                        fail ──────────> fail ───────────> fail ──> rejected (one appeal, 72 h)
```

- Tool: [tools/verify_ticket.py](../tools/verify_ticket.py). Record: [ledger/verdicts.json](../ledger/verdicts.json). Tests: `python3 -m unittest tests.test_verify_ticket`.
- Check: `python3 tools/verify_ticket.py verify`. Worked run: `python3 tools/verify_ticket.py demo` (below).
- Reads tickets through the [template](ticket-template.md); pays through the [credit ledger](credit-ledger.md) and the [repayment queue](repayment-queue.md).
- The order comes from the [economics page](http://vps3.taild81fbb.ts.net:8976/), screen 2: tests in the ticket, hidden tests, a jury of three different models, contest once.

## Who does what

| Step | Who runs it | What the builder sees | What is made public, when |
|---|---|---|---|
| Own tests (`acceptance.tests`) | The hoster's verifier, in a clean checkout of the submitted commit | Everything: the builder runs them before submitting | Each command, exit code and last log lines, in the verdict |
| Hidden tests (`acceptance.hidden_tests`) | The hoster's verifier, same checkout, only after every own test passes | Only the count and the sha256 posted with the ticket | The whole hidden file, in the verdict, once it is written: anyone can hash it against the posted sha256 and rerun it |
| Jury (`acceptance.jury`) | The hoster's verifier calls the models, only after every hidden test passes; the hoster pays the calls | Nothing until the verdict | The prompt, its sha256, each juror's model name, raw answer, verdict and reason |
| Verdict | The tool, from the results | The verdict | The whole entry, appended to `ledger/verdicts.json` |
| Row done, payment | The epic's Delivery Manager sets the row `done (accepted: verdict #n)`; then `verify_ticket.py pay` writes the credit issue or cash claim | Their credit or claim | The credit or queue entry, citing the verdict |

The hoster runs the verifier because the hoster holds the hidden tests and pays for the service the credit buys. It still decides nothing by hand: the outcome is computed, `verify` recomputes it for every entry, and the commit, the revealed hidden file and the jurors' raw answers let anyone rerun the judgement.

## Rules

1. **Cheapest first, stop at the first failure.** Own tests, then hidden tests, then the jury. A submission that fails its own tests never costs a jury call.
2. **Own test files are locked.** A change that edits a file the ticket's own test commands name is rejected before anything runs.
3. **Hidden tests are fixed before work.** The hoster posts the hidden file's sha256 and test count with the ticket. The verifier refuses a hidden file that hashes differently or holds a different count. The files are placed in the checkout for the run and removed after it.
4. **Hidden tests stay hidden until the verdict.** The hoster keeps the file off the repo and out of the builder's sight. The verdict publishes it whole, so a builder can check it was the posted file and that it tests what the deliverable says.
5. **The jury: N different models, M must pass.** N and M come from the ticket (3 and 2 by default). The same model never sits twice. Each juror gets the same fixed prompt (version `jury/1`, in the tool): the deliverable, the ticket's own tests, the test results and the diff. Each answers one JSON object `{"verdict": "pass" | "fail", "reason": "…"}`. An answer that cannot be read counts as fail.
6. **The jury is pluggable.** `StubJuror` is deterministic and free: tests and the worked run use it. `CommandJuror` pipes the prompt to a command the hoster configures (`--juror name=command`, three times). No model is called unless the hoster plugs one in, and the hoster pays for those calls.
7. **The outcome follows from the results.** The record refuses an entry whose outcome or reason differs from what the rule computes from its own results, an entry that breaks the hash chain, a juror whose recorded verdict differs from its raw answer, a prompt that does not match its hash, and a second acceptance of the same ticket.
8. **One appeal, within 72 hours, to a fresh jury.** A builder may contest a rejection by the hidden tests or the jury once. The appeal reruns both test steps on the same commit and asks three models that did not sit on the first jury. For a hidden-test failure, the appeal jury sees the failing hidden tests and lists any that check something the deliverable does not say (`out_of_scope`); a test that M of N jurors call out of scope is set aside. The appeal's verdict is final. A failure of the builder's own tests or a locked-file edit cannot be appealed: the builder could have run them first.
9. **What a rejection costs.** Nothing is paid: the builder carries the runs they spent (the eligible cost excludes them). The hold ends and the ticket goes back on the board at its current ladder price; anyone, the same builder included, may hold it again. A new builder's $5 hold deposit (economics page, screen 2) is kept by the hoster on a final rejection, to pay for the verification; it comes back with an acceptance.
10. **Acceptance pays one currency, once.** An accepted verdict carries what it pays, read from the ticket: credit = the multiple x the fixed price, a cash claim = the fixed price, 1x, or units at the rate fixed before work. `pay` writes the credit ledger's `issue` (tools/credit.py) or the queue's `claim` (tools/queue.py) with the verdict as its evidence. Both ledgers check that the row is done in its spine and refuse to pay a ticket twice. Units are awarded with tools/units.py.
11. **Words.** A verdict, a prompt and a reason never call a payment a stake, share, investment or return (L-1). Cash is repayment of cost, capped at the fixed price.

## Worked run on EXAMPLE-1

`python3 tools/verify_ticket.py demo` builds real git checkouts of a small recall app ([tests/fixtures/example1](../tests/fixtures/example1)), runs the real test commands of [tickets/EXAMPLE-1.md](../tickets/EXAMPLE-1.md) and its 7 hidden tests ([hidden-tests.json](../tests/fixtures/example1/hidden-tests.json), the file whose sha256 the ticket posts), uses stub jurors, and writes nothing to the public ledgers. Output, 2026-11-26:

```
#1 Ben, change that fits only the visible tests: own 5/5, hidden 6/7 -> REJECTED: hidden tests failed: H1
#2 Ana, the change as asked: own 5/5, hidden 7/7, jury stub-1=pass stub-2=pass stub-3=fail -> ACCEPTED: own tests and hidden tests pass, jury 2 of 3
#3 Ben appeals #1, fresh jury appeal-1..3 -> REJECTED (final): hidden tests failed: H1 (the appeal jury held them in scope)
#4 Cy, edits a locked test file -> REJECTED: the change edits the ticket's own test files, which are locked: tests/test_recall_since.py
pay #2 -> credit ledger issue: Ana (example builder) $20.00 (2x the fixed $10.00), evidence ledger/verdicts.json #2 (4484d7df5e63, own tests and hidden tests pass, jury 2 of 3)
refused, pay #1 (rejected): verdict 1 is rejected: nothing is paid
refused, pay #2 twice: entry 2: ticket EXAMPLE-1 already credited
refused, flip #1 to accepted: verdict 5: outcome 'accepted' does not follow from its results (rejected)
verify: OK, chain intact, every outcome follows from its results
```

Ben's change compares days with `>` instead of `>=`: it passes all five visible tests and misses a memory saved on the `--since` day itself, which hidden test H1 checks. Ana's change passes everything; one juror says fail and 2 of 3 still accept. Her $20 of Zenod Hosted credit is the same entry the real credit ledger already holds for this example.

## Not settled here

- The monthly human sample that can lower a builder's rating after a bad acceptance (economics page): the credit ledger has no entry that cancels issued credit, and its rule 4 says issued credit never shrinks. Left for the rating work.
- Which real models sit on a hoster's jury, and their cost per verdict: each hoster's choice, made when it plugs real jurors in.

*Not legal, securities, tax or accounting advice.*
