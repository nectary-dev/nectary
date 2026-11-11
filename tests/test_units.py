import copy
import json
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import units  # noqa: E402

SPINE = """# EPIC-T
## Issue Ledger
| Row | Role | Owner | Scope | Status |
|---|---|---|---|---|
| T-1 | w | x | a | done (no confirm: test) |
| T-2 | w | x | b | done (approved) |
| T-3 | w | x | c | review |
| T-4 | w | x | d | done |
"""


class UnitsTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        with open(os.path.join(self.dir, "spine.md"), "w") as f:
            f.write(SPINE)
        rate = {"units": 50, "pay_in": "units", "fixed": "2026-11-01", "before_work": True}
        self.ledger = {"epics": {"T": {"spine": "spine.md", "cap": 100, "rates": {
            "T-1": dict(rate), "T-2": dict(rate), "T-3": dict(rate),
            "T-4": dict(rate, pay_in="claim")}}}, "entries": []}

    def award(self, row, holder="ana", date="2026-11-02"):
        return units.award(self.ledger, holder, "T", row, "https://example.org/e", date, self.dir)

    def test_award_spend_balance(self):
        self.award("T-1")
        units.spend(self.ledger, "ana", "T", 20, "https://example.org/s", "2026-11-03", root=self.dir)
        self.assertEqual(units.balances(self.ledger), {"ana": 30})
        self.assertEqual(units.verify(self.ledger, self.dir), [])

    def test_row_not_done_refused(self):
        with self.assertRaisesRegex(units.LedgerError, "not done"):
            self.award("T-3")
        self.assertEqual(self.ledger["entries"], [])

    def test_claim_ticket_earns_no_units(self):
        with self.assertRaisesRegex(units.LedgerError, "capped revenue claim"):
            self.award("T-4")

    def test_double_award_refused(self):
        self.award("T-1")
        with self.assertRaisesRegex(units.LedgerError, "already awarded"):
            self.award("T-1", holder="bob")

    def test_cap_enforced(self):
        self.ledger["epics"]["T"]["cap"] = 60
        self.award("T-1")
        with self.assertRaisesRegex(units.LedgerError, "over its cap"):
            self.award("T-2")

    def test_negative_balance_refused(self):
        self.award("T-1")
        with self.assertRaisesRegex(units.LedgerError, "below zero"):
            units.spend(self.ledger, "ana", "T", 51, "https://example.org/s", "2026-11-03", root=self.dir)
        with self.assertRaisesRegex(units.LedgerError, "below zero"):
            units.spend(self.ledger, "bob", "T", 1, "https://example.org/s", "2026-11-03", root=self.dir)

    def transfer(self, frm, to, n, date="2026-11-03"):
        return units.transfer(self.ledger, frm, to, n, date, note="test", root=self.dir)

    def test_transfer_ok_and_balances(self):
        self.award("T-1")
        self.transfer("ana", "bob", 20)
        self.assertEqual(units.balances(self.ledger), {"ana": 30, "bob": 20})
        units.spend(self.ledger, "bob", "T", 20, "https://example.org/s", "2026-11-04", root=self.dir)
        self.assertEqual(units.balances(self.ledger), {"ana": 30, "bob": 0})
        self.assertEqual(units.burned(self.ledger), 20)
        self.assertEqual(units.issued(self.ledger, "T"), 50)
        self.assertEqual(units.verify(self.ledger, self.dir), [])

    def test_transfer_overdraft_refused(self):
        self.award("T-1")
        with self.assertRaisesRegex(units.LedgerError, "below zero"):
            self.transfer("ana", "bob", 51)
        with self.assertRaisesRegex(units.LedgerError, "below zero"):
            self.transfer("carl", "bob", 1)
        self.assertEqual(len(self.ledger["entries"]), 1)

    def test_transfer_to_self_or_nonpositive_refused(self):
        self.award("T-1")
        with self.assertRaisesRegex(units.LedgerError, "oneself"):
            self.transfer("ana", "ana", 5)
        for n in (0, -5):
            with self.assertRaisesRegex(units.LedgerError, "positive"):
                self.transfer("ana", "bob", n)
        self.assertEqual(len(self.ledger["entries"]), 1)

    def test_transfer_keeps_chain(self):
        self.award("T-1")
        self.transfer("ana", "bob", 10)
        self.award("T-2", holder="bob", date="2026-11-04")
        self.assertEqual(units.verify(self.ledger, self.dir), [])
        self.ledger["entries"][1]["units"] = 40
        self.assertTrue(any("chain" in e for e in units.verify(self.ledger, self.dir)))

    def test_received_units_spendable_not_more(self):
        self.award("T-1")
        self.transfer("ana", "bob", 10)
        with self.assertRaisesRegex(units.LedgerError, "below zero"):
            units.spend(self.ledger, "bob", "T", 11, "https://example.org/s", "2026-11-04", root=self.dir)

    def test_unknown_type_rejected(self):
        units.append(self.ledger, {"type": "mint", "date": "2026-11-03", "holder": "ana", "units": 10})
        self.assertTrue(any("not allowed" in e for e in units.verify(self.ledger, self.dir)))

    def test_rate_must_match_and_predate(self):
        self.award("T-1")
        bad = copy.deepcopy(self.ledger)
        bad["entries"][0]["units"] = 80
        self.assertTrue(any("differs" in e for e in units.verify(bad, self.dir)))
        late = copy.deepcopy(self.ledger)
        late["epics"]["T"]["rates"]["T-1"]["fixed"] = "2026-11-05"
        self.assertTrue(any("after the award" in e for e in units.verify(late, self.dir)))

    def test_history_rewrite_breaks_chain(self):
        self.award("T-1")
        self.award("T-2", holder="bob")
        self.ledger["entries"][0]["holder"] = "mallory"
        self.assertTrue(any("chain" in e for e in units.verify(self.ledger, self.dir)))

    def test_committed_ledger_verifies(self):
        ledger = units.load(units.DEFAULT_LEDGER)
        self.assertEqual(units.verify(ledger), [])
        self.assertGreater(len(ledger["entries"]), 0)
        self.assertTrue(any(e["type"] == "transfer" for e in ledger["entries"]))


if __name__ == "__main__":
    unittest.main()
