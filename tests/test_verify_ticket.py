import copy
import json
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import verify_ticket as vt  # noqa: E402
import ticket as ticketlib  # noqa: E402
from units import LedgerError, load  # noqa: E402

EXAMPLE = os.path.join(ROOT, "tickets", "EXAMPLE-1.md")
HIDDEN = os.path.join(ROOT, "tests", "fixtures", "example1", "hidden-tests.json")


def ticket():
    with open(EXAMPLE, encoding="utf-8") as f:
        return ticketlib.parse(f.read())[0]


def runner(failing=()):
    """A fake test runner: every command passes unless its test name is in `failing`. Records the calls."""
    calls = []

    def run(cmd, cwd):
        calls.append(cmd)
        bad = any(cmd.endswith(f) or f == cmd for f in failing)
        return (1, "FAIL") if bad else (0, "ok")
    run.calls = calls
    return run


class VerifyTest(unittest.TestCase):
    def setUp(self):
        self.t = ticket()
        self.wd = tempfile.mkdtemp()
        self.credit = load(os.path.join(ROOT, "ledger", "credit.json"))
        self.credit["entries"] = []
        self.credit["tickets"].pop("EXAMPLE-1", None)

    def judge(self, jury="stub:pass,pass,pass", failing=(), changed=("recall.py",), appeal_of=None,
              date="2026-11-26T18:00Z", ledger=None, prefix="stub"):
        r = runner(failing)
        e = vt.judge(self.t, EXAMPLE, "Ana", "abc123", self.wd, "diff --git a/recall.py", list(changed), HIDDEN,
                     vt.jurors_from_spec(jury, prefix), r, date, appeal_of)
        if ledger is not None:
            e = vt.commit_verdict(ledger, e)
        return e, r

    # the three steps, in order
    def test_own_tests_fail_rejected_before_hidden_and_jury(self):
        e, r = self.judge(failing=("test_bad_date",))
        self.assertEqual(e["outcome"], "rejected")
        self.assertIn("own tests failed: T3", e["reason"])
        self.assertIsNone(e["hidden_tests"])
        self.assertIsNone(e["jury"], "no jury money spent on a submission that fails its own tests")
        self.assertEqual(len(r.calls), 5)

    def test_hidden_tests_fail_rejected_without_jury(self):
        e, _ = self.judge(failing=("test_same_day",))
        self.assertEqual(e["outcome"], "rejected")
        self.assertEqual(e["reason"], "hidden tests failed: H1")
        self.assertIsNone(e["jury"])
        self.assertEqual(vt.sha256_text(e["hidden_revealed"]), self.t["acceptance"]["hidden_tests"]["sha256"])

    def test_jury_two_of_three_accepted(self):
        e, _ = self.judge(jury="stub:pass,fail,pass")
        self.assertEqual(e["outcome"], "accepted")
        self.assertIn("jury 2 of 3", e["reason"])
        self.assertEqual(e["pays"], {"currency": "credit", "price_cents": 1000, "multiple": 2, "cents": 2000,
                                     "service": "Zenod Hosted"})

    def test_jury_one_of_three_rejected(self):
        e, _ = self.judge(jury="stub:pass,fail,fail")
        self.assertEqual(e["outcome"], "rejected")
        self.assertEqual(e["reason"], "jury 1 of 3 pass, 2 needed")

    def test_acceptance_emits_credit_issue_entry(self):
        L = {"entries": []}
        v, _ = self.judge(jury="stub:pass,pass,fail", ledger=L)
        issue = vt.pay(v, self.credit, root=ROOT, date="2026-11-26")
        self.assertEqual(issue["type"], "issue")
        self.assertEqual((issue["holder"], issue["ticket"], issue["cents"], issue["multiple"]), ("Ana", "EXAMPLE-1", 2000, 2))
        self.assertIn("ledger/verdicts.json #1", issue["evidence"])
        with self.assertRaises(LedgerError):
            vt.pay(v, self.credit, root=ROOT, date="2026-11-27")  # credit once per ticket

    def test_rejected_pays_nothing(self):
        v, _ = self.judge(jury="stub:fail,fail,pass")
        with self.assertRaisesRegex(LedgerError, "nothing is paid"):
            vt.pay(v, self.credit, root=ROOT)

    def test_cash_claim_joins_queue(self):
        t = copy.deepcopy(self.t)
        t["pay_in"] = {"choice": "claim", "claim_amount": 10}
        self.assertEqual(vt.payout_terms(t), {"currency": "claim", "cents": 1000})

    # guards
    def test_locked_test_files(self):
        e, r = self.judge(changed=("recall.py", "tests/test_api_recall.py"))
        self.assertEqual(e["outcome"], "rejected")
        self.assertIn("locked", e["reason"])
        self.assertEqual(r.calls, [])

    def test_hidden_file_must_match_posted_hash(self):
        bad = os.path.join(self.wd, "hidden.json")
        with open(HIDDEN) as f:
            text = f.read()
        with open(bad, "w") as g:
            g.write(text.replace("H7", "H8"))
        self.t["acceptance"]["hidden_tests"]["sha256"] = vt.sha256_text(text)
        with self.assertRaisesRegex(LedgerError, "not the file the hoster committed to"):
            vt.read_hidden(bad, self.t)

    def test_hidden_files_removed_after_run(self):
        self.judge()
        self.assertFalse(os.path.exists(os.path.join(self.wd, "tests", "hidden", "test_hidden_since.py")))

    def test_jury_needs_distinct_models_in_the_posted_number(self):
        with self.assertRaisesRegex(LedgerError, "3 different models"):
            self.judge(jury="stub:pass,pass")
        with self.assertRaisesRegex(LedgerError, "3 different models"):
            vt.ask_jury(self.t, [vt.StubJuror("m", "pass")] * 3, "p")

    def test_unreadable_answer_counts_as_fail(self):
        self.assertEqual(vt.parse_answer("I think it is fine")[0], "fail")
        self.assertEqual(vt.parse_answer('{"verdict": "maybe"}')[0], "fail")
        self.assertEqual(vt.parse_answer('ok {"verdict": "pass", "reason": "r"}')[:2], ("pass", "r"))

    def test_command_juror_is_pluggable(self):
        j = vt.CommandJuror("echo-model", "cat >/dev/null; echo '{\"verdict\": \"pass\", \"reason\": \"fine\"}'")
        self.assertEqual(vt.parse_answer(j.judge("prompt"))[:2], ("pass", "fine"))

    def test_prompt_is_recorded_and_hashed(self):
        e, _ = self.judge()
        j = e["jury"]
        self.assertEqual(j["prompt_version"], "jury/1")
        self.assertEqual(vt.sha256_text(j["prompt"]), j["prompt_sha256"])
        self.assertIn(self.t["deliverable"], j["prompt"])
        self.assertEqual([x["raw"] for x in j["jurors"]][0], json.dumps({"verdict": "pass", "reason": "stub juror set to pass"}))

    # the public record
    def test_record_refuses_outcome_that_does_not_follow(self):
        L = {"entries": []}
        e, _ = self.judge(jury="stub:fail,fail,pass")
        with self.assertRaisesRegex(LedgerError, "does not follow"):
            vt.commit_verdict(L, dict(e, outcome="accepted"))
        self.assertEqual(L["entries"], [])

    def test_record_chain_breaks_on_rewrite(self):
        L = {"entries": []}
        self.judge(failing=("test_same_day",), ledger=L)
        self.judge(ledger=L, date="2026-11-26T19:00Z", jury="stub:pass,pass,fail")
        L["entries"][0]["builder"] = "Someone else"
        self.assertTrue(any("chain" in x for x in vt.verify(L)))

    def test_one_accept_per_ticket(self):
        L = {"entries": []}
        self.judge(ledger=L)
        with self.assertRaisesRegex(LedgerError, "already accepted"):
            self.judge(ledger=L, date="2026-11-26T19:00Z")

    # appeals
    def test_appeal_sets_aside_out_of_scope_hidden_test(self):
        L = {"entries": []}
        self.judge(failing=("test_same_day",), ledger=L)
        jur = [vt.StubJuror(f"appeal-{i}", "pass", out_of_scope=["H1"] if i < 3 else []) for i in (1, 2, 3)]
        e = vt.judge(self.t, EXAMPLE, "Ana", "abc123", self.wd, "d", ["recall.py"], HIDDEN, jur,
                     runner(("test_same_day",)), "2026-11-27T10:00Z", appeal_of=1)
        e = vt.commit_verdict(L, e)
        self.assertEqual(e["outcome"], "accepted")
        self.assertIn("set aside hidden H1", e["reason"])

    def test_appeal_keeps_in_scope_hidden_failure(self):
        L = {"entries": []}
        self.judge(failing=("test_same_day",), ledger=L)
        e, _ = self.judge(failing=("test_same_day",), appeal_of=1, date="2026-11-27T10:00Z", ledger=L, prefix="appeal")
        self.assertEqual(e["outcome"], "rejected")

    def test_appeal_rules(self):
        L = {"entries": []}
        self.judge(jury="stub:fail,fail,pass", ledger=L)
        with self.assertRaisesRegex(LedgerError, "reuses a model"):
            self.judge(appeal_of=1, date="2026-11-27T10:00Z", ledger=L)
        with self.assertRaisesRegex(LedgerError, "after 72 h"):
            self.judge(appeal_of=1, date="2026-11-30T10:00Z", ledger=L, prefix="appeal")
        self.judge(appeal_of=1, date="2026-11-27T10:00Z", ledger=L, prefix="appeal", jury="stub:fail,fail,fail")
        with self.assertRaisesRegex(LedgerError, "already appealed"):
            self.judge(appeal_of=1, date="2026-11-27T11:00Z", ledger=L, prefix="other")
        L2 = {"entries": []}
        self.judge(failing=("test_bad_date",), ledger=L2)
        with self.assertRaisesRegex(LedgerError, "cannot be appealed"):
            self.judge(failing=("test_bad_date",), appeal_of=1, date="2026-11-27T10:00Z", ledger=L2, prefix="appeal")

    # the worked run, end to end with real commands and git
    def test_worked_run_on_example(self):
        L, log, credit = vt.demo()
        self.assertEqual([e["outcome"] for e in L["entries"]], ["rejected", "accepted", "rejected", "rejected"])
        self.assertEqual(vt.verify(L), [])
        self.assertEqual(credit["entries"][0]["cents"], 2000)
        self.assertFalse(any(line.startswith("NOT refused") for line in log))

    def test_public_ledger_verifies(self):
        self.assertEqual(vt.verify(load(vt.DEFAULT_LEDGER)), [])


if __name__ == "__main__":
    unittest.main()
