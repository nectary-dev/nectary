import contextlib
import importlib.util
import io
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from units import LedgerError, load  # noqa: E402

# tools/queue.py shares its name with the stdlib queue module: load it by path so neither shadows the other.
_spec = importlib.util.spec_from_file_location("nectary_queue", os.path.join(ROOT, "tools", "queue.py"))
q = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(q)

EXAMPLE = os.path.join(ROOT, "tickets", "EXAMPLE-1.md")

SPINE = """# EPIC-T
## Issue Ledger
| Row | Role | Owner | Scope | Status |
|---|---|---|---|---|
| T-1 | w | x | a | done (approved) |
| T-2 | w | x | b | done (no confirm: test) |
| T-3 | w | x | c | review |
| T-4 | w | x | d | done (approved) |
"""


class QueueTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        with open(os.path.join(self.dir, "spine.md"), "w") as f:
            f.write(SPINE)
        # $40 profit a month, $0.50 to serve $1 of credit: the queue gets $20 a month less credit served.
        month = {"profit_cents": 4000, "serve_cost_per_credit_dollar": 0.5}
        self.C = {"hosters": {"h": {"service": "S", "months": {"2026-11": dict(month), "2026-12": dict(month),
                                                                  "2027-01": dict(month)}}},
                  "entries": []}
        self.U = {"entries": []}
        self.L = {"spines": {"T": "spine.md"}, "entries": []}

    def claim(self, row, cents, holder=None, date="2026-11-10", ticket=None, **kw):
        e = {"type": "claim", "kind": "ticket", "date": date, "accepted": date, "holder": holder or f"b-{row}",
             "hoster": "h", "ticket": ticket or row, "epic": "T", "row": row, "price_cents": cents, "cents": cents,
             "evidence": "log"}
        e.update(kw)
        return q._commit(self.L, e, self.C, self.U, self.dir)

    def settle(self, month, date):
        return q.settle(self.L, self.C, "h", month, date, self.U, self.dir)

    def paid(self):
        return q.lines(self.L)[1]

    def errs(self):
        return q.verify(self.L, self.C, self.U, self.dir)

    def forge(self, entry):
        """Append an entry without the tool's checks, as a hand edit of the file would."""
        q.append(self.L, entry)
        return self.errs()

    # order
    def test_oldest_claim_is_paid_first(self):
        a, b = self.claim("T-1", 1500), self.claim("T-2", 1500, date="2026-11-11")
        f, *pays = self.settle("2026-11", "2026-12-01")
        self.assertEqual(f["cents"], 2000)
        self.assertEqual([(p["claim"], p["cents"]) for p in pays], [(a["seq"], 1500), (b["seq"], 500)])
        self.assertEqual(self.errs(), [])

    def test_a_later_claim_cannot_jump_the_line(self):
        self.claim("T-1", 1500)
        b = self.claim("T-2", 500, date="2026-11-11")
        f = self.settle("2026-11", "2026-12-01")[0]
        self.L["entries"] = self.L["entries"][:f["seq"]]  # drop the tool's payments, pay out of order by hand
        errs = self.forge({"type": "pay", "date": "2026-12-01", "hoster": "h", "holder": "b-T-2", "claim": b["seq"],
                           "fund": f["seq"], "cents": 500})
        self.assertTrue(any("jumps the line" in e for e in errs), errs)

    # cap at the fixed price, never exceeded
    def test_claim_is_the_fixed_price_never_more(self):
        with self.assertRaises(LedgerError):
            self.claim("T-1", 1600, price_cents=1000)

    def test_payment_never_goes_over_the_claim(self):
        a = self.claim("T-1", 1000)
        f = self.settle("2026-11", "2026-12-01")[0]
        self.assertEqual(self.paid()[a["seq"]], 1000)  # $20 in, $10 owed: $10 paid, nothing more
        self.L["entries"] = self.L["entries"][:f["seq"]]
        errs = self.forge({"type": "pay", "date": "2026-12-01", "hoster": "h", "holder": "b-T-1", "claim": a["seq"],
                           "fund": f["seq"], "cents": 1200})
        self.assertTrue(any("over its fixed price" in e for e in errs), errs)

    def test_payment_never_goes_over_the_month_fund(self):
        a = self.claim("T-1", 5000)
        f = self.settle("2026-11", "2026-12-01")[0]
        self.L["entries"] = self.L["entries"][:f["seq"]]
        errs = self.forge({"type": "pay", "date": "2026-12-01", "hoster": "h", "holder": "b-T-1", "claim": a["seq"],
                           "fund": f["seq"], "cents": 2500})
        self.assertTrue(any("left" in e for e in errs), errs)

    # partial payments
    def test_partial_payments_over_months_reach_the_claim_exactly(self):
        a = self.claim("T-1", 4500)
        for m, d in (("2026-11", "2026-12-01"), ("2026-12", "2027-01-01"), ("2027-01", "2027-02-01")):
            self.settle(m, d)
        pays = [e["cents"] for e in self.L["entries"] if e["type"] == "pay"]
        self.assertEqual(pays, [2000, 2000, 500])
        self.assertEqual(self.paid()[a["seq"]], 4500)
        self.assertEqual(q.lines(self.L)[0].get("h"), [])
        self.assertEqual(self.errs(), [])

    def test_credit_served_comes_off_the_month_first(self):
        self.C["entries"].append({"type": "honour", "date": "2026-11-20", "hoster": "h", "holder": "x", "cents": 1000})
        self.claim("T-1", 5000)
        f, pay = self.settle("2026-11", "2026-12-01")
        self.assertEqual((f["credit_cost_cents"], f["cents"], pay["cents"]), (500, 1500, 1500))

    def test_no_profit_pays_nothing_and_nothing_accrues(self):
        self.C["hosters"]["h"]["months"]["2026-11"]["profit_cents"] = -300
        a = self.claim("T-1", 1000)
        out = self.settle("2026-11", "2026-12-01")
        self.assertEqual((len(out), out[0]["cents"]), (1, 0))
        self.settle("2026-12", "2027-01-01")
        self.assertEqual(self.paid()[a["seq"]], 1000)  # no interest: still exactly the fixed price

    # no claim paid twice
    def test_a_paid_claim_is_never_paid_again(self):
        a = self.claim("T-1", 1000)
        self.settle("2026-11", "2026-12-01")
        f2 = self.settle("2026-12", "2027-01-01")
        self.assertEqual(len(f2), 1)  # the December fund pays nobody: the line is empty
        errs = self.forge({"type": "pay", "date": "2027-01-01", "hoster": "h", "holder": "b-T-1", "claim": a["seq"],
                           "fund": f2[0]["seq"], "cents": 1})
        self.assertTrue(any("already paid in full" in e for e in errs), errs)

    def test_one_claim_per_ticket(self):
        self.claim("T-1", 1000)
        with self.assertRaises(LedgerError):
            self.claim("T-1", 1000, date="2026-11-12")

    def test_a_month_funds_the_queue_once_and_only_when_over(self):
        self.claim("T-1", 9000)
        with self.assertRaises(LedgerError):
            self.settle("2026-11", "2026-11-30")
        self.settle("2026-11", "2026-12-01")
        with self.assertRaises(LedgerError):
            self.settle("2026-11", "2026-12-02")

    def test_fund_must_match_the_books(self):
        errs = self.forge({"type": "fund", "date": "2026-12-01", "hoster": "h", "month": "2026-11",
                           "profit_cents": 4000, "credit_cost_cents": 0, "cents": 3000})
        self.assertTrue(any("should put 2000 in" in e for e in errs), errs)

    # never two currencies, accepted only
    def test_ticket_paid_in_credit_or_units_cannot_claim_cash(self):
        self.C["entries"].append({"type": "issue", "ticket": "T-1", "cents": 2000})
        with self.assertRaises(LedgerError):
            self.claim("T-1", 1000)
        self.U["entries"].append({"type": "award", "row": "T-2"})
        with self.assertRaises(LedgerError):
            self.claim("T-2", 1000)

    def test_row_must_be_done(self):
        with self.assertRaises(LedgerError):
            self.claim("T-3", 1000)

    def test_bootstrap_joins_the_same_line_at_cost(self):
        self.claim("T-1", 1500)
        b = q.bootstrap(self.L, self.C, "founder", "h", "BOOT-1", "T", "T-4", 1000, "40 runs x $0.25, run log",
                        "log", "2026-11-12", self.U, root=self.dir)
        pays = self.settle("2026-11", "2026-12-01")[1:]
        self.assertEqual([(p["claim"], p["cents"]) for p in pays], [(1, 1500), (b["seq"], 500)])
        with self.assertRaises(LedgerError):
            q.bootstrap(self.L, self.C, "founder", "h", "BOOT-2", "T", "T-4", 100, "", "log", "2026-12-02", self.U,
                        root=self.dir)

    def test_rewriting_history_breaks_the_chain(self):
        self.claim("T-1", 1000)
        self.claim("T-2", 1000, date="2026-11-11")
        self.L["entries"][0]["cents"] = 900
        self.L["entries"][0]["price_cents"] = 900
        self.assertTrue(any("chain" in e for e in self.errs()))


class TemplateTest(unittest.TestCase):
    """The queue reads tickets through the template (tools/ticket.py) and the worked example."""

    def setUp(self):
        self.C = load(os.path.join(ROOT, "ledger", "credit.json"))

    def test_example_as_cash_claim_is_its_fixed_price(self):
        C = {"hosters": self.C["hosters"], "entries": []}
        L = {"spines": {}, "entries": []}
        e = q.claim(L, C, EXAMPLE, "worked example", "2026-11-26", as_claim=True)
        self.assertEqual((e["hoster"], e["cents"], e["price_cents"], e["holder"]),
                         ("zenod", 1000, 1000, "Ana (example builder)"))

    def test_example_already_credited_cannot_also_claim_cash(self):
        with self.assertRaises(LedgerError):  # the real credit ledger credited EXAMPLE-1 $20
            q.claim({"spines": {}, "entries": []}, self.C, EXAMPLE, "x", "2026-11-26", as_claim=True)

    def test_a_credit_ticket_is_not_a_cash_claim(self):
        with self.assertRaises(LedgerError):
            q.claim({"spines": {}, "entries": []}, {"hosters": self.C["hosters"], "entries": []}, EXAMPLE, "x",
                    "2026-11-26")

    def test_only_an_example_may_be_read_as_a_claim(self):
        d = tempfile.mkdtemp()
        with open(EXAMPLE) as f:
            text = f.read().replace('"example": true,', '"example": false,')
        path = os.path.join(d, "REAL.md")
        with open(path, "w") as f:
            f.write(text)
        with self.assertRaises(LedgerError):
            q.read_ticket(path, as_claim=True)

    def test_worked_run(self):
        L, log, credit = q.demo()
        self.assertEqual(q.verify(L, credit), [])
        self.assertEqual(credit["entries"][0]["holder"], "Dee (example builder)")
        text = "\n".join(log)
        self.assertIn("2026-11: half of $45.95 profit = $22.97, less $9.48 credit served = $13.49 in; "
                      "Ana (example builder) $10.00; Ben (example builder) $3.49", text)
        self.assertIn("Cy (example builder) $1.04", text)
        self.assertEqual(text.count("· paid in full"), 3)
        self.assertEqual(text.count("refused"), 2)
        self.assertNotIn("NOT refused", text)

    def test_real_ledger_verifies(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(q.main(["verify"]), 0)
        self.assertIn("OK", out.getvalue())



if __name__ == "__main__":
    unittest.main()
