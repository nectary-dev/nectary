import contextlib
import copy
import io
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import credit  # noqa: E402
from units import LedgerError  # noqa: E402

EXAMPLE = os.path.join(ROOT, "tickets", "EXAMPLE-1.md")

SPINE = """# EPIC-T
## Issue Ledger
| Row | Role | Owner | Scope | Status |
|---|---|---|---|---|
| T-1 | w | x | a | done (approved) |
| T-2 | w | x | b | done (no confirm: test) |
| T-3 | w | x | c | review |
"""


class CreditTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        with open(os.path.join(self.dir, "spine.md"), "w") as f:
            f.write(SPINE)
        self.L = {
            "multiples": [{"from": "2026-11-01", "multiple": 2, "source": "EPIC-0-A5"}],
            "spines": {"T": "spine.md"},
            # $46 profit, $0.50 cost per credit dollar: room = $23 / 0.5 = $46 of credit a month
            "hosters": {"h": {"months": {"2026-11": {"profit_cents": 4600, "serve_cost_per_credit_dollar": 0.5},
                                         "2026-12": {"profit_cents": 4600, "serve_cost_per_credit_dollar": 0.5}}}},
            "tickets": {}, "entries": []}

    def ticket(self, tid, row, runs=8, date="2026-11-02", windows=0):
        return credit.price(self.L, tid, "h", runs, date, date, unheld_windows=windows, epic="T", row=row)

    def issue(self, tid, holder="ana", date="2026-11-10", inference=None):
        return credit.issue(self.L, holder, tid, "https://example.org/e", date, inference, self.dir)

    def ok(self):
        self.assertEqual(credit.verify(self.L, self.dir), [])

    # price set before work
    def test_price_ladder(self):
        self.assertEqual(credit.estimate_cents(8, 120), 1000)          # 8 x $1.20 = $9.60, posted at $10
        self.assertEqual(credit.price_cents(1000, 1), 1250)            # +25% after 48 h unheld
        self.assertEqual(credit.price_cents(1000, 5), 1500)            # never above 1.5x the estimate
        self.assertEqual(credit.price_cents(4500, 2), 5000)            # never above $50

    def test_price_must_be_fixed_before_work(self):
        with self.assertRaises(LedgerError):
            credit.price(self.L, "x", "h", 8, "2026-11-05", "2026-11-04")

    def test_requote_refused(self):
        self.ticket("a", "T-1")
        with self.assertRaises(LedgerError):
            self.ticket("a", "T-1", runs=20)

    # issue at 2x the fixed price on acceptance
    def test_issue_2x_fixed_price(self):
        self.ticket("a", "T-1")
        e = self.issue("a")
        self.assertEqual((e["price_cents"], e["multiple"], e["cents"]), (1000, 2, 2000))
        self.ok()

    def test_issue_needs_accepted_row(self):
        self.ticket("c", "T-3")
        with self.assertRaises(LedgerError):
            self.issue("c")

    def test_issue_twice_refused(self):
        self.ticket("a", "T-1")
        self.issue("a")
        with self.assertRaises(LedgerError):
            self.issue("a", holder="ben")

    def test_tampered_credit_fails_verify(self):
        self.ticket("a", "T-1")
        self.issue("a")
        bad = copy.deepcopy(self.L)
        bad["entries"][0]["cents"] = 5000
        self.assertTrue(any("not 2 x" in e or "chain" in e for e in credit.verify(bad, self.dir)))

    # overrun does not change credit
    def test_overrun_and_saving_do_not_change_credit(self):
        self.ticket("a", "T-1")
        self.ticket("b", "T-2")
        ana = self.issue("a", "ana", inference=840)     # spent $8.40, keeps the saving
        ben = self.issue("b", "ben", inference=1320)    # spent $13.20, eats the overrun
        self.assertEqual(ana["cents"], 2000)
        self.assertEqual(ben["cents"], 2000)
        self.ok()

    # monthly multiple only for tickets priced after the reset; issued credit never shrinks
    def test_monthly_reset_applies_only_to_new_tickets(self):
        self.ticket("a", "T-1", date="2026-11-20")              # priced at 2x
        self.L["multiples"].append({"from": "2026-12-01", "multiple": 3, "source": "December books"})
        self.ticket("b", "T-2", date="2026-12-02")              # priced at 3x
        self.assertEqual(self.issue("a", date="2026-12-05")["cents"], 2000)
        self.assertEqual(self.issue("b", date="2026-12-05")["cents"], 3000)
        self.ok()

    def test_multiple_follows_posting_day_not_hold_day(self):
        credit.price(self.L, "a", "h", 8, "2026-12-02", "2026-12-02", epic="T", row="T-1", posted="2026-11-28")
        self.L["multiples"].append({"from": "2026-12-01", "multiple": 3, "source": "December books"})
        self.assertEqual(self.issue("a", date="2026-12-05")["cents"], 2000)
        self.ok()

    def test_lower_reset_never_shrinks_issued_credit(self):
        self.ticket("a", "T-1")
        self.issue("a")
        self.L["multiples"].append({"from": "2026-12-01", "multiple": 1.5, "source": "December books"})
        self.assertEqual(credit.state(self.L)[0]["ana"], 2000)
        self.ok()

    def test_two_resets_in_one_month_fail(self):
        self.L["multiples"].append({"from": "2026-11-20", "multiple": 3, "source": "x"})
        self.assertTrue(any("once a month" in e for e in credit.verify(self.L, self.dir)))

    def test_wrong_multiple_fails_verify(self):
        self.ticket("a", "T-1")
        self.issue("a")
        bad = copy.deepcopy(self.L)
        bad["multiples"] = [{"from": "2026-11-01", "multiple": 5, "source": "x"}]
        self.assertTrue(any("multiple" in e for e in credit.verify(bad, self.dir)))

    # transfer (units are transferable, so credit is too)
    def test_transfer(self):
        self.ticket("a", "T-1")
        self.issue("a")
        credit.transfer(self.L, "ana", "jordi", 500, "2026-11-11", root=self.dir)
        free = credit.state(self.L)[0]
        self.assertEqual((free["ana"], free["jordi"]), (1500, 500))
        with self.assertRaises(LedgerError):
            credit.transfer(self.L, "ana", "jordi", 1600, "2026-11-11", root=self.dir)
        with self.assertRaises(LedgerError):
            credit.transfer(self.L, "ana", "ana", 100, "2026-11-11", root=self.dir)
        self.ok()

    # spend burns credit, within half the hoster's monthly profit; the rest waits in line, in order
    def test_spend_burns(self):
        self.ticket("a", "T-1")
        self.issue("a")
        r, done = credit.spend(self.L, "ana", "h", 1200, "2026-11-12", root=self.dir)
        self.assertEqual(len(done), 1)
        free, waiting, _ = credit.state(self.L)
        self.assertEqual((free["ana"], waiting["ana"]), (800, 0))
        self.assertEqual(credit.burned_cents(self.L), 1200)
        with self.assertRaises(LedgerError):
            credit.spend(self.L, "ana", "h", 900, "2026-11-12", root=self.dir)
        self.ok()

    def test_half_profit_cap_queues_in_order(self):
        for tid, row, who in (("a", "T-1", "ana"), ("b", "T-2", "ben")):
            self.ticket(tid, row, runs=25)                       # $30 price, $60 credit each
            self.issue(tid, who)
        _, done = credit.spend(self.L, "ana", "h", 4000, "2026-11-12", root=self.dir)   # fits: $40 of $46 room
        self.assertEqual(len(done), 1)
        _, done = credit.spend(self.L, "ben", "h", 3000, "2026-11-13", root=self.dir)   # $30 > $6 left: waits
        self.assertEqual(done, [])
        _, done = credit.spend(self.L, "ana", "h", 500, "2026-11-14", root=self.dir)    # $5 fits but must not jump ben
        self.assertEqual(done, [])
        free, waiting, queue = credit.state(self.L)
        self.assertEqual((waiting["ben"], waiting["ana"], len(queue["h"])), (3000, 500, 2))
        self.ok()
        served = credit.honour_queue(self.L, "h", "2026-12-01", self.dir)              # new month, new room
        self.assertEqual([e["holder"] for e in served], ["ben", "ana"])
        self.assertEqual(credit.burned_cents(self.L), 7500)
        self.ok()

    def test_honour_over_cap_or_out_of_order_fails_verify(self):
        for tid, row, who in (("a", "T-1", "ana"), ("b", "T-2", "ben")):
            self.ticket(tid, row, runs=25)
            self.issue(tid, who)
        credit.spend(self.L, "ana", "h", 4000, "2026-11-12", root=self.dir)
        credit.spend(self.L, "ben", "h", 3000, "2026-11-13", root=self.dir)
        credit.spend(self.L, "ana", "h", 500, "2026-11-14", root=self.dir)
        over = copy.deepcopy(self.L)
        credit.append(over, {"type": "honour", "date": "2026-11-15", "holder": "ben", "hoster": "h", "request": 5, "cents": 3000})
        self.assertTrue(any("over half its profit" in e for e in credit.verify(over, self.dir)))
        jump = copy.deepcopy(self.L)
        credit.append(jump, {"type": "honour", "date": "2026-11-15", "holder": "ana", "hoster": "h", "request": 6, "cents": 500})
        self.assertTrue(any("jumps the line" in e for e in credit.verify(jump, self.dir)))

    # wired to the ticket template (E0-S2)
    @unittest.skipUnless(os.path.exists(EXAMPLE), "ticket template not in this checkout")
    def test_from_ticket_reads_template_price(self):
        self.L["hosters"]["h"]["service"] = "Zenod Hosted"
        self.L["multiples"][0]["from"] = "2026-11-01"
        tk = credit.from_ticket(self.L, EXAMPLE)
        self.assertEqual((tk["price_cents"], tk["hoster"], tk["demonstration"]), (1000, "h", True))
        self.assertEqual(credit.issue(self.L, "ana", "EXAMPLE-1", "e", "2026-11-26", 840, self.dir)["cents"], 2000)
        self.ok()

    @unittest.skipUnless(os.path.exists(EXAMPLE), "ticket template not in this checkout")
    def test_from_ticket_refuses_claim_or_bad_ticket(self):
        with open(EXAMPLE) as f:
            text = f.read()
        for bad in (text.replace('"choice": "credit"', '"choice": "claim", "claim_amount": 10'),
                    text.replace('"fixed": 10', '"fixed": 30')):
            path = os.path.join(self.dir, "t.md")
            with open(path, "w") as f:
                f.write(bad)
            with self.assertRaises(LedgerError):
                credit.from_ticket(self.L, path, "h")

    # the published ledger
    def test_published_ledger_verifies_with_demo(self):
        L = credit.load(credit.DEFAULT_LEDGER)
        self.assertEqual(credit.verify(L), [])
        demo = [e for e in L["entries"] if e["type"] == "issue" and e["ticket"] == "EXAMPLE-1"]
        self.assertEqual((demo[0]["price_cents"], demo[0]["cents"]), (1000, 2000))

    def test_cli_verify(self):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(credit.main(["verify"]), 0)
        self.assertTrue(out.getvalue().startswith("OK:"))


if __name__ == "__main__":
    unittest.main()
