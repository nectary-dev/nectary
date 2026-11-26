import copy
import json
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import board  # noqa: E402
import ticket  # noqa: E402

EXAMPLE = os.path.join(ROOT, "tickets", "EXAMPLE-1.md")
LEDGER = os.path.join(ROOT, "ledger", "credit.json")


def example():
    with open(EXAMPLE, encoding="utf-8") as f:
        return ticket.parse(f.read())


def write(d, name, meta, body):
    path = os.path.join(d, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write("---\n" + json.dumps(meta, indent=2) + "\n---\n" + body)
    return path


def posted(meta):
    """EXAMPLE-1 turned back into an open ticket nobody holds yet."""
    m = copy.deepcopy(meta)
    m["id"] = m["row"] = "OPEN-1"
    m["status"] = "posted"
    m.pop("builder")
    for k in ("held_at", "fixed"):
        m["price"].pop(k)
    m["credit"].pop("amount")
    m["pay_in"] = {"choice": "open"}
    return m


class BoardTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.meta, self.body = example()
        self.now = ticket.when("2026-11-27T12:00Z")

    def build(self, paths, ledger=LEDGER, now=None):
        return board.build(os.path.join(self.dir, "out"), now or self.now, paths, ledger)

    def test_example_shows_10_dollars_and_20_credit(self):
        fd = self.build([EXAMPLE])
        t = fd["tickets"][0]
        self.assertEqual((t["id"], t["price"]["current"], t["credit"]["amount"]), ("EXAMPLE-1", 10, 20))
        self.assertTrue(t["price"]["fixed"])
        self.assertEqual(t["holder"], "Ana (example builder)")
        self.assertEqual(t["tests"]["hidden"], 7)
        self.assertEqual(len(t["tests"]["own"]), 5)

    def test_accepted_and_credited_is_paid(self):
        self.assertEqual(self.build([EXAMPLE])["tickets"][0]["state"], "paid")

    def test_accepted_without_ledger_entry_stays_accepted(self):
        fd = self.build([EXAMPLE], ledger=os.path.join(self.dir, "none.json"))
        self.assertEqual(fd["tickets"][0]["state"], "accepted")
        self.assertIsNone(fd["tickets"][0]["credit"]["issued"])

    def test_failing_ticket_listed_apart(self):
        bad = copy.deepcopy(self.meta)
        bad["id"] = "BAD-1"
        bad["credit"]["amount"] = 30
        fd = self.build([EXAMPLE, write(self.dir, "BAD-1.md", bad, self.body)])
        self.assertEqual([t["id"] for t in fd["tickets"]], ["EXAMPLE-1"])
        self.assertEqual(len(fd["failed"]), 1)
        self.assertIn("credit.amount", fd["failed"][0]["errors"][0])

    def test_open_ticket_climbs_the_ladder(self):
        path = write(self.dir, "OPEN-1.md", posted(self.meta), self.body)
        self.assertEqual(ticket.check_file(path), [])
        # posted 26 Nov 09:05: $10 for 48 h, then $12.50, then the $15 cap
        for now, price, credit, nxt in (("2026-11-27T12:00Z", 10, 20, "2026-11-28T09:05Z"),
                                        ("2026-11-28T09:05Z", 12.5, 25, "2026-11-30T09:05Z"),
                                        ("2026-12-09T00:00Z", 15, 30, None)):
            t = self.build([path], now=ticket.when(now))["tickets"][0]
            self.assertEqual(t["state"], "posted")
            self.assertEqual((t["price"]["current"], t["credit"]["amount"], t["price"]["next_step_at"]), (price, credit, nxt))
            self.assertFalse(t["credit"]["final"])
            self.assertIsNone(t["holder"])

    def test_open_tickets_listed_first(self):
        path = write(self.dir, "OPEN-1.md", posted(self.meta), self.body)
        fd = self.build([EXAMPLE, path])
        self.assertEqual([t["id"] for t in fd["tickets"]], ["OPEN-1", "EXAMPLE-1"])
        self.assertEqual(fd["counts"]["posted"], 1)
        self.assertEqual(fd["counts"]["paid"], 1)

    def test_files_written(self):
        self.build([EXAMPLE])
        out = os.path.join(self.dir, "out")
        with open(os.path.join(out, "tickets.json"), encoding="utf-8") as f:
            self.assertEqual(json.load(f)["board"], "nectary-ticket-board/1")
        with open(os.path.join(out, "index.html"), encoding="utf-8") as f:
            page = f.read()
        self.assertIn('id="EXAMPLE-1"', page)
        self.assertIn("$10", page)
        self.assertIn("$20", page)
        self.assertIn("../credit.html#credit", page)


if __name__ == "__main__":
    unittest.main()
