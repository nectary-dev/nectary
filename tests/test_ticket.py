import copy
import json
import os
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import ticket  # noqa: E402

EXAMPLE = os.path.join(ROOT, "tickets", "EXAMPLE-1.md")


def load_example():
    with open(EXAMPLE, encoding="utf-8") as f:
        return ticket.parse(f.read())


def render(meta, body):
    return "---\n" + json.dumps(meta, indent=2) + "\n---\n" + body


class TicketTest(unittest.TestCase):
    def setUp(self):
        self.meta, self.body = load_example()

    def errors(self, meta=None, body=None):
        return ticket.check_text(render(meta or self.meta, self.body if body is None else body))

    def assertFails(self, meta, needle, body=None):
        errs = self.errors(meta, body)
        self.assertTrue(errs, "expected the ticket to fail")
        self.assertTrue(any(needle in e for e in errs), f"no error mentions {needle!r}: {errs}")

    # --- the check that proves E0-S2 done ---
    def test_example_passes(self):
        self.assertEqual(ticket.check_file(EXAMPLE), [])

    def test_missing_price_fails(self):
        m = copy.deepcopy(self.meta)
        del m["price"]
        self.assertFails(m, "ticket.price: missing")

    def test_missing_tests_fails(self):
        m = copy.deepcopy(self.meta)
        del m["acceptance"]["tests"]
        self.assertFails(m, "ticket.acceptance.tests: missing")

    def test_empty_tests_fails(self):
        m = copy.deepcopy(self.meta)
        m["acceptance"]["tests"] = []
        self.assertFails(m, "ticket.acceptance.tests: needs at least 1")

    def test_missing_hidden_tests_fails(self):
        m = copy.deepcopy(self.meta)
        del m["acceptance"]["hidden_tests"]
        self.assertFails(m, "hidden_tests: missing")

    def test_missing_evidence_or_trigger_fails(self):
        for key in ("evidence", "eligible_cost", "repayment_trigger"):
            m = copy.deepcopy(self.meta)
            del m[key]
            self.assertFails(m, f"ticket.{key}: missing")

    # --- price set before work ---
    def test_estimate_arithmetic(self):
        m = copy.deepcopy(self.meta)
        m["price"]["estimate"]["amount"] = 12
        self.assertFails(m, "8 runs x $1.2 = 9.6")

    def test_posted_is_rounded_estimate(self):
        m = copy.deepcopy(self.meta)
        m["price"]["posted"] = 11
        self.assertFails(m, "posts at $10")

    def test_cap(self):
        m = copy.deepcopy(self.meta)
        m["price"]["price_cap"] = 20
        self.assertFails(m, "min(1.5 x 10, 50) = 15")

    def test_over_fifty_must_split(self):
        m = copy.deepcopy(self.meta)
        m["price"]["estimate"].update(runs=50, amount=60)
        self.assertFails(m, "split the ticket")

    def test_ladder_matches_model(self):
        self.assertEqual(ticket.ladder(10), [10.0, 12.5, 15.0])
        self.assertEqual(ticket.ladder(40), [40.0, 50.0])
        self.assertEqual(ticket.estimate_price(8), (9.6, 10))

    def test_price_rises_when_unheld(self):
        m = copy.deepcopy(self.meta)
        m["price"]["held_at"] = "2026-11-28T10:00Z"  # 49 h after posting: one step
        self.assertFails(m, "ladder price is 12.5")
        m["price"]["fixed"] = 12.5
        m["credit"]["amount"] = 25
        self.assertEqual(self.errors(m), [])
        m["price"]["held_at"] = "2026-12-20T10:00Z"  # weeks later: stays at the cap
        m["price"]["fixed"] = 15
        m["credit"]["amount"] = 30
        self.assertEqual(self.errors(m), [])

    def test_held_needs_fixed_price_and_builder(self):
        m = copy.deepcopy(self.meta)
        del m["price"]["fixed"]
        del m["builder"]
        errs = self.errors(m)
        self.assertTrue(any("price.fixed: missing" in e for e in errs))
        self.assertTrue(any("builder: missing" in e for e in errs))

    def test_posted_has_no_fixed_price(self):
        m = copy.deepcopy(self.meta)
        m["status"] = "posted"
        m["pay_in"] = {"choice": "open"}
        self.assertFails(m, "no fixed price yet")

    # --- credit and pay ---
    def test_credit_is_multiple_of_fixed_price(self):
        m = copy.deepcopy(self.meta)
        m["credit"]["amount"] = 19.2  # 2x the inference burned, not the price
        self.assertFails(m, "2 x 10 = 20")

    def test_claim_is_fixed_price_never_more(self):
        m = copy.deepcopy(self.meta)
        m["pay_in"] = {"choice": "claim", "claim_amount": 20}
        self.assertFails(m, "never more")
        m["pay_in"]["claim_amount"] = 10
        self.assertEqual(self.errors(m), [])

    def test_one_currency_per_ticket(self):
        m = copy.deepcopy(self.meta)
        m["pay_in"] = {"choice": "credit", "units_rate": 100}
        self.assertFails(m, "never two currencies")

    def test_units_need_rate(self):
        m = copy.deepcopy(self.meta)
        m["pay_in"] = {"choice": "units"}
        self.assertFails(m, "units_rate: missing")

    def test_accepted_needs_choice(self):
        m = copy.deepcopy(self.meta)
        m["pay_in"] = {"choice": "open"}
        self.assertFails(m, "records the builder's choice")

    def test_jury_majority(self):
        m = copy.deepcopy(self.meta)
        m["acceptance"]["jury"]["pass"] = 4
        self.assertFails(m, "not a majority")

    # --- words and sections ---
    def test_banned_words(self):
        m = copy.deepcopy(self.meta)
        m["deliverable"] += " Builders get a share of revenue."
        self.assertFails(m, "banned word 'share'")
        self.assertFails(self.meta, "banned word 'investment'", body=self.body + "\nA good investment.\n")

    def test_banned_words_allowed_in_commands(self):
        m = copy.deepcopy(self.meta)
        m["acceptance"]["tests"][0]["cmd"] = "pytest -k returns_zero"
        self.assertEqual(self.errors(m), [])

    def test_sections_required(self):
        self.assertFails(self.meta, "'## Evidence' missing", body=self.body.replace("## Evidence", "## Proof"))

    def test_no_front_matter(self):
        self.assertEqual(ticket.check_text("# just text\n"), ["no front matter: a ticket opens with a JSON object between two '---' lines"])

    def test_cli_exit_codes(self):
        tool = os.path.join(ROOT, "tools", "ticket.py")
        ok = subprocess.run([sys.executable, tool, "check", EXAMPLE], capture_output=True, text=True)
        self.assertEqual(ok.returncode, 0, ok.stdout)
        bad = os.path.join(ROOT, "tests", "_no_price.md")
        m = copy.deepcopy(self.meta)
        del m["price"]
        try:
            with open(bad, "w", encoding="utf-8") as f:
                f.write(render(m, self.body))
            res = subprocess.run([sys.executable, tool, "check", bad], capture_output=True, text=True)
            self.assertEqual(res.returncode, 1)
            self.assertIn("FAIL", res.stdout)
        finally:
            os.remove(bad)


if __name__ == "__main__":
    unittest.main()
