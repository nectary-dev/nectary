#!/usr/bin/env python3
"""Nectary verification: a submission is judged against its ticket by written rules (docs/verification.md).

Order, cheapest first, stopping at the first failure:
  1. the ticket's own tests (acceptance.tests), run by the hoster on the submitted commit;
  2. the hidden tests, held by the hoster, whose file must hash to the sha256 posted with the ticket;
  3. a jury of N AI models (acceptance.jury.models) reading one fixed prompt; acceptance.jury.pass must say pass.
The outcome is computed from the results, never typed in. Every verdict, with its prompt, each juror's raw
answer and the revealed hidden tests, goes into ledger/verdicts.json (append-only, sha256 hash chain, the
same approach as the units, credit and queue ledgers). An accepted verdict is what lets the row be set done
and the credit, cash claim or units be paid.

Jurors are pluggable: StubJuror (deterministic, for tests and the worked run) and CommandJuror (pipes the
prompt to a command the hoster configures). No model is called unless a hoster plugs one in.

  python3 tools/verify_ticket.py run --ticket tickets/X.md --workdir DIR --base REV --commit REV \
      --hidden FILE --jury stub:pass,pass,fail [--apply]
  python3 tools/verify_ticket.py appeal --verdict N --workdir DIR --hidden FILE --jury ... [--apply]
  python3 tools/verify_ticket.py pay --verdict N [--apply]       after the row is done in its spine
  python3 tools/verify_ticket.py verify | demo
"""
import argparse
import copy
import datetime as dt
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from units import GENESIS, LedgerError, ROOT, entry_hash, load, save  # noqa: E402
import credit as creditlib  # noqa: E402
import ticket as ticketlib  # noqa: E402

_spec = importlib.util.spec_from_file_location("nectary_queue", os.path.join(os.path.dirname(os.path.abspath(__file__)), "queue.py"))
queuelib = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(queuelib)

DEFAULT_LEDGER = os.path.join(ROOT, "ledger", "verdicts.json")
PROMPT_VERSION = "jury/1"
APPEAL_HOURS = 72
TEST_TIMEOUT = 600
MAX_DIFF = 60000  # characters of diff a juror reads; a longer change is cut and says so

PROMPT = """You are one of {models} independent jurors for a Nectary ticket. Judge one thing: does the change do \
what the deliverable says, and nothing else? Tests already ran; judge what tests cannot (scope, honesty, \
whether the code only fits the tests).

Ticket: {id}: {title}
Deliverable: {deliverable}

The ticket's own tests:
{tests}

Results: own tests {own}; hidden tests {hidden}.
{appeal}
The change (unified diff{cut}):
{diff}

Answer with one JSON object and nothing else:
{{"verdict": "pass" or "fail", "reason": "<one sentence>"{scope_field}}}
"""

APPEAL_PART = """
This is the builder's one appeal. These hidden tests failed; they are shown to you now:
{failed}
For each, decide whether it checks something the deliverable says. List the ids that do not in "out_of_scope".
"""


def sha256_text(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def now():
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%MZ")


def when(s):
    return dt.datetime.strptime(s, "%Y-%m-%dT%H:%MZ")


# ---- jurors ---------------------------------------------------------------------------------------------

class StubJuror:
    """Deterministic juror: always gives the verdict it was built with. Costs nothing."""

    def __init__(self, name, verdict, reason=None, out_of_scope=()):
        self.name, self.verdict = name, verdict
        self.reason = reason or f"stub juror set to {verdict}"
        self.out_of_scope = list(out_of_scope)

    def judge(self, prompt):
        d = {"verdict": self.verdict, "reason": self.reason}
        if self.out_of_scope:
            d["out_of_scope"] = self.out_of_scope
        return json.dumps(d)


class CommandJuror:
    """A real model behind a command the hoster sets (the prompt on stdin, the answer on stdout)."""

    def __init__(self, name, cmd, timeout=300):
        self.name, self.cmd, self.timeout = name, cmd, timeout

    def judge(self, prompt):
        r = subprocess.run(self.cmd, shell=True, input=prompt, capture_output=True, text=True, timeout=self.timeout)
        return r.stdout


def parse_answer(raw):
    """A juror's raw answer -> (verdict, reason, out_of_scope). Anything unreadable counts as fail."""
    m = re.search(r"\{.*\}", raw or "", re.S)
    try:
        d = json.loads(m.group(0)) if m else None
    except ValueError:
        d = None
    if not isinstance(d, dict) or d.get("verdict") not in ("pass", "fail"):
        return "fail", "unreadable answer: counted as fail", []
    oos = d.get("out_of_scope") or []
    return d["verdict"], str(d.get("reason", "")), [x for x in oos if isinstance(x, str)]


def jurors_from_spec(spec, prefix="stub"):
    """'stub:pass,pass,fail' -> three StubJurors. Real jurors come from --juror name=command, never by default."""
    kind, _, rest = spec.partition(":")
    if kind != "stub":
        raise LedgerError("--jury takes stub:<v1>,<v2>,...; plug in real models with --juror name=command")
    return [StubJuror(f"{prefix}-{i + 1}", v.strip()) for i, v in enumerate(rest.split(","))]


# ---- running tests --------------------------------------------------------------------------------------

def shell_runner(cmd, cwd, env=None):
    """Run one test command in the submission's checkout: (exit code, last lines of output)."""
    try:
        r = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True, timeout=TEST_TIMEOUT, env=env)
        out = (r.stdout + r.stderr).strip().splitlines()
        return r.returncode, "\n".join(out[-5:])
    except subprocess.TimeoutExpired:
        return 124, f"timed out after {TEST_TIMEOUT} s"


def run_tests(tests, runner, workdir):
    out = []
    for t in tests:
        code, log = runner(t["cmd"], workdir)
        out.append({"id": t["id"], "cmd": t["cmd"], "exit": code, "passed": code == 0, "log": log})
    return out


def locked_paths(t):
    """Files the ticket's own tests live in: the builder may not change them (test files are locked)."""
    paths = set()
    for test in t["acceptance"]["tests"]:
        for word in test["cmd"].split():
            p = word.split("::")[0]
            if re.search(r"\.(py|js|ts|sh|rb|go|rs)$", p):
                paths.add(p)
    return paths


def read_hidden(path, t):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    want = t["acceptance"]["hidden_tests"]
    if sha256_text(text) != want["sha256"]:
        raise LedgerError(f"hidden test file hashes to {sha256_text(text)[:12]}…, the ticket posted {want['sha256'][:12]}…: "
                          "not the file the hoster committed to")
    d = json.loads(text)
    if len(d.get("tests", [])) != want["count"]:
        raise LedgerError(f"hidden test file holds {len(d.get('tests', []))} tests, the ticket posted {want['count']}")
    return text, d


def place_hidden(d, workdir):
    """Write the hidden test files into the checkout; the caller removes them after the run."""
    placed = []
    for rel, body in d.get("files", {}).items():
        dest = os.path.normpath(os.path.join(workdir, rel))
        if not dest.startswith(os.path.normpath(workdir) + os.sep):
            raise LedgerError(f"hidden file path {rel!r} leaves the checkout")
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "w", encoding="utf-8") as f:
            f.write(body)
        placed.append(dest)
    return placed


def git_change(workdir, base, commit):
    """The submission as the jury reads it: the diff and the files it changes."""
    def git(*a):
        return subprocess.run(["git", "-C", workdir, *a], capture_output=True, text=True, check=True).stdout
    return git("diff", f"{base}..{commit}"), [p for p in git("diff", "--name-only", f"{base}..{commit}").splitlines() if p]


# ---- the rule ------------------------------------------------------------------------------------------

def jury_tally(jury, scope_failed=()):
    votes = sum(1 for j in jury["jurors"] if j["verdict"] == "pass")
    oos = [h for h in scope_failed if sum(1 for j in jury["jurors"] if h in j.get("out_of_scope", [])) >= jury["pass_needed"]]
    return votes, oos


def decide(e):
    """The outcome from the recorded results alone. verify() runs this again on every entry."""
    if e.get("touched_locked"):
        return "rejected", "the change edits the ticket's own test files, which are locked: " + ", ".join(e["touched_locked"])
    own = e["own_tests"]
    failed = [r["id"] for r in own if not r["passed"]]
    if failed:
        return "rejected", "own tests failed: " + ", ".join(failed)
    hidden_failed = [r["id"] for r in e.get("hidden_tests") or [] if not r["passed"]]
    jury = e.get("jury")
    set_aside = []
    if hidden_failed:
        if e.get("appeals") is None or not jury:
            return "rejected", "hidden tests failed: " + ", ".join(hidden_failed)
        _, set_aside = jury_tally(jury, hidden_failed)
        still = [h for h in hidden_failed if h not in set_aside]
        if still:
            return "rejected", "hidden tests failed: " + ", ".join(still) + " (the appeal jury held them in scope)"
    if not jury:
        return "rejected", "no jury verdict recorded"
    votes, _ = jury_tally(jury)
    if votes < jury["pass_needed"]:
        return "rejected", f"jury {votes} of {len(jury['jurors'])} pass, {jury['pass_needed']} needed"
    note = f"; appeal set aside hidden {', '.join(set_aside)} as outside the deliverable" if set_aside else ""
    return "accepted", f"own tests and hidden tests pass, jury {votes} of {len(jury['jurors'])}{note}"


def build_prompt(t, own, hidden, diff, appeal_failed=None):
    tests = "\n".join(f"- {x['id']}: {x['checks']}" for x in t["acceptance"]["tests"])
    hp = sum(1 for r in hidden if r["passed"])
    appeal = ""
    if appeal_failed:
        appeal = APPEAL_PART.format(failed="\n".join(f"- {h['id']}: {h.get('checks', '')} ({h['cmd']})" for h in appeal_failed))
    cut = f", cut at {MAX_DIFF} characters" if len(diff) > MAX_DIFF else ""
    return PROMPT.format(models=t["acceptance"]["jury"]["models"], id=t["id"], title=t["title"],
                         deliverable=t["deliverable"], tests=tests,
                         own=f"{sum(1 for r in own if r['passed'])} of {len(own)} pass",
                         hidden=f"{hp} of {len(hidden)} pass", appeal=appeal, cut=cut, diff=diff[:MAX_DIFF],
                         scope_field=', "out_of_scope": ["<hidden test id>", ...]' if appeal_failed else "")


def ask_jury(t, jurors, prompt):
    j = t["acceptance"]["jury"]
    names = [x.name for x in jurors]
    if len(jurors) != j["models"] or len(set(names)) != len(names):
        raise LedgerError(f"the ticket wants {j['models']} different models on its jury, got {names}")
    out = []
    for x in jurors:
        raw = x.judge(prompt)
        verdict, reason, oos = parse_answer(raw)
        out.append({"model": x.name, "raw": raw, "verdict": verdict, "reason": reason, "out_of_scope": oos})
    return {"prompt_version": PROMPT_VERSION, "prompt": prompt, "prompt_sha256": sha256_text(prompt),
            "pass_needed": j["pass"], "jurors": out}


def judge(t, ticket_path, builder, commit, workdir, diff, changed, hidden_path, jurors, runner, date, appeal_of=None):
    """Run the three steps in order and return the verdict entry (not yet in any ledger)."""
    e = {"type": "verdict", "date": date, "ticket": t["id"], "source": os.path.relpath(os.path.abspath(ticket_path), ROOT),
         "epic": t.get("epic"), "row": t.get("row"), "builder": builder, "commit": commit,
         "diff_sha256": sha256_text(diff), "changed_files": changed, "hidden_sha256": t["acceptance"]["hidden_tests"]["sha256"],
         "own_tests": [], "hidden_tests": None, "jury": None}
    if t.get("example"):
        e["demonstration"] = True
    if appeal_of is not None:
        e["appeals"] = appeal_of
    e["touched_locked"] = sorted(locked_paths(t) & set(changed))
    if not e["touched_locked"]:
        e["own_tests"] = run_tests(t["acceptance"]["tests"], runner, workdir)
    if not e["touched_locked"] and all(r["passed"] for r in e["own_tests"]):
        hidden_text, hd = read_hidden(hidden_path, t)
        placed = place_hidden(hd, workdir)
        try:
            e["hidden_tests"] = run_tests(hd["tests"], runner, workdir)
        finally:
            for f in placed:
                os.remove(f)
        e["hidden_revealed"] = hidden_text  # public once the verdict is written: anyone can hash it and rerun it
        failed = [dict(h, **r) for h, r in zip(hd["tests"], e["hidden_tests"]) if not r["passed"]]
        if not failed or appeal_of is not None:
            e["jury"] = ask_jury(t, jurors, build_prompt(t, e["own_tests"], e["hidden_tests"], diff, failed or None))
    e["outcome"], e["reason"] = decide(e)
    if e["outcome"] == "accepted":
        e["pays"] = payout_terms(t)
    return e


def payout_terms(t):
    """What acceptance pays, read from the ticket: the builder's one currency."""
    p, choice = t["price"], t["pay_in"]["choice"]
    fixed = int(round(ticketlib.money(p["fixed"]) * 100))
    if choice in ("credit", "open"):
        return {"currency": "credit", "price_cents": fixed, "multiple": t["credit"]["multiple"],
                "cents": int(round(fixed * t["credit"]["multiple"])), "service": t.get("service")}
    if choice == "claim":
        return {"currency": "claim", "cents": int(round(ticketlib.money(t["pay_in"]["claim_amount"]) * 100))}
    return {"currency": "units", "rate": t["pay_in"].get("units_rate")}


# ---- the public record ---------------------------------------------------------------------------------

def append(ledger, entry):
    entries = ledger.setdefault("entries", [])
    entry = dict(entry, seq=len(entries) + 1, prev=entry_hash(entries[-1]) if entries else GENESIS)
    entries.append(entry)
    return entry


def verify(ledger):
    """Problems in the verdict record (empty = consistent)."""
    errs, prev, accepted, appealed, by_seq = [], GENESIS, {}, set(), {}
    for i, e in enumerate(ledger.get("entries", []), 1):
        w = f"verdict {i}"
        if e.get("seq") != i:
            errs.append(f"{w}: seq {e.get('seq')} should be {i}")
        if e.get("prev") != prev:
            errs.append(f"{w}: prev hash breaks the chain (record was rewritten?)")
        prev = entry_hash(e)
        by_seq[i] = e
        if e.get("type") != "verdict":
            errs.append(f"{w}: type {e.get('type')!r} not allowed")
            continue
        if (e.get("outcome"), e.get("reason")) != decide(e):
            errs.append(f"{w}: outcome {e.get('outcome')!r} does not follow from its results ({decide(e)[0]})")
        if e.get("hidden_revealed") is not None and sha256_text(e["hidden_revealed"]) != e.get("hidden_sha256"):
            errs.append(f"{w}: revealed hidden tests do not hash to the sha256 posted with the ticket")
        j = e.get("jury")
        if j:
            if sha256_text(j["prompt"]) != j["prompt_sha256"]:
                errs.append(f"{w}: jury prompt does not match its hash")
            names = [x["model"] for x in j["jurors"]]
            if len(set(names)) != len(names):
                errs.append(f"{w}: the same model sits twice on the jury")
            for x in j["jurors"]:
                if parse_answer(x["raw"])[:2] != (x["verdict"], x["reason"]):
                    errs.append(f"{w}: {x['model']}'s recorded verdict differs from its raw answer")
        if e.get("outcome") == "accepted":
            if e["ticket"] in accepted:
                errs.append(f"{w}: {e['ticket']} already accepted in verdict {accepted[e['ticket']]}")
            accepted[e["ticket"]] = i
        a = e.get("appeals")
        if a is not None:
            first = by_seq.get(a)
            if not first or first.get("ticket") != e["ticket"] or first.get("commit") != e["commit"] or first.get("outcome") != "rejected":
                errs.append(f"{w}: appeals {a}, which is not a rejected verdict on the same ticket and commit")
            elif a in appealed:
                errs.append(f"{w}: verdict {a} was already appealed (one appeal per verdict)")
            elif first.get("appeals") is not None:
                errs.append(f"{w}: an appeal's verdict is final")
            elif first.get("touched_locked") or not all(r["passed"] for r in first["own_tests"]):
                errs.append(f"{w}: own tests and locked files cannot be appealed: the builder could run them first")
            elif (when(e["date"]) - when(first["date"])).total_seconds() > APPEAL_HOURS * 3600:
                errs.append(f"{w}: appeal after {APPEAL_HOURS} h")
            elif j and first.get("jury") and set(x["model"] for x in j["jurors"]) & set(x["model"] for x in first["jury"]["jurors"]):
                errs.append(f"{w}: the appeal jury reuses a model from the first jury")
            appealed.add(a)
    return errs


def commit_verdict(ledger, entry):
    e = append(ledger, entry)
    errs = verify(ledger)
    if errs:
        ledger["entries"].pop()
        raise LedgerError("; ".join(errs))
    return e


def evidence_of(v):
    return f"ledger/verdicts.json #{v['seq']} ({v['commit'][:12]}, {v['reason']})"


def pay(v, credit, queue=None, root=ROOT, date=None):
    """Acceptance -> the payout entry: a credit issue (tools/credit.py) or a cash claim (tools/queue.py).
    Both ledgers check the row is done in its spine; a worked example (demonstration) has no row to check."""
    if v.get("outcome") != "accepted":
        raise LedgerError(f"verdict {v.get('seq')} is {v.get('outcome')}: nothing is paid")
    date = date or v["date"][:10]
    path = os.path.join(root, v["source"])
    terms = v["pays"]
    if terms["currency"] == "credit":
        if v["ticket"] not in credit.get("tickets", {}):
            creditlib.from_ticket(credit, path)
        return creditlib.issue(credit, v["builder"], v["ticket"], evidence_of(v), date, root=root)
    if terms["currency"] == "claim":
        return queuelib.claim(queue, credit, path, evidence_of(v), date, root=root)
    return {"type": "pending", "note": f"award {terms['rate']} units with tools/units.py, evidence {evidence_of(v)}"}


# ---- the worked run ------------------------------------------------------------------------------------

FIX = os.path.join(ROOT, "tests", "fixtures", "example1")


def fixture_runner():
    env = dict(os.environ, PATH=os.path.join(FIX, "bin") + os.pathsep + os.environ.get("PATH", ""))
    return lambda cmd, cwd: shell_runner(cmd, cwd, env)


def fixture_checkout(dest, bug=False):
    """A git checkout of the EXAMPLE-1 submission: base = the code before the change, head = Ana's change."""
    stamp = "2026-11-26T18:00:00Z"
    env = dict(os.environ, GIT_AUTHOR_DATE=stamp, GIT_COMMITTER_DATE=stamp)

    def git(*a):
        return subprocess.run(["git", "-C", dest, *a], capture_output=True, text=True, check=True, env=env).stdout.strip()
    shutil.copytree(os.path.join(FIX, "submission"), dest)
    git("init", "-q")
    git("config", "user.email", "example@nectary.invalid")
    git("config", "user.name", "example")
    rec = os.path.join(dest, "recall.py")
    with open(rec, encoding="utf-8") as f:
        after = f.read()
    before = after.replace("def recall(since=None, memories=MEMORIES):\n    if since is None:\n        return list(memories)\n"
                           "    day = parse_day(since).isoformat()\n    return [m for m in memories if m[\"saved\"][:10] >= day]",
                           "def recall(memories=MEMORIES):\n    return list(memories)")
    with open(rec, "w", encoding="utf-8") as f:
        f.write(before)
    git("add", "-A")
    git("commit", "-qm", "before EXAMPLE-1")
    base = git("rev-parse", "HEAD")
    if bug:  # fits the visible tests, misses the same day: what hidden tests are for
        after = after.replace('m["saved"][:10] >= day', 'm["saved"][:10] > day')
    with open(rec, "w", encoding="utf-8") as f:
        f.write(after)
    git("commit", "-qam", "EXAMPLE-1: recall --since")
    return base, git("rev-parse", "HEAD")


def demo(root=ROOT):
    """The worked run on tickets/EXAMPLE-1.md (docs/verification.md). Temp checkouts, stub jurors, nothing written."""
    ticket_path = os.path.join(root, "tickets", "EXAMPLE-1.md")
    with open(ticket_path, encoding="utf-8") as f:
        t, _ = ticketlib.parse(f.read())
    hidden = os.path.join(FIX, "hidden-tests.json")
    real = load(os.path.join(root, "ledger", "credit.json"))
    credit = copy.deepcopy(real)
    credit["entries"] = []  # the real ledger already holds EXAMPLE-1's issue; replay it from a clean line
    credit["tickets"].pop("EXAMPLE-1", None)
    L, log, runner = {"entries": []}, [], fixture_runner()
    tmp = tempfile.mkdtemp(prefix="nectary-verify-")
    try:
        cases = [("Ben, change that fits only the visible tests", "Ben (example builder)", True, "stub:pass,pass,pass"),
                 ("Ana, the change as asked", "Ana (example builder)", False, "stub:pass,pass,fail")]
        for n, (label, who, bug, jury) in enumerate(cases, 1):
            wd = os.path.join(tmp, f"c{n}")
            base, head = fixture_checkout(wd, bug)
            diff, changed = git_change(wd, base, head)
            v = commit_verdict(L, judge(t, ticket_path, who, head, wd, diff, changed, hidden,
                                        jurors_from_spec(jury), runner, "2026-11-26T18:0%dZ" % n))
            line = f"#{v['seq']} {label}: own {sum(r['passed'] for r in v['own_tests'])}/{len(v['own_tests'])}"
            if v["hidden_tests"] is not None:
                line += f", hidden {sum(r['passed'] for r in v['hidden_tests'])}/{len(v['hidden_tests'])}"
            if v["jury"]:
                line += ", jury " + " ".join(f"{j['model']}={j['verdict']}" for j in v["jury"]["jurors"])
            log.append(line + f" -> {v['outcome'].upper()}: {v['reason']}")
        wd = os.path.join(tmp, "c1b")  # Ben appeals once: a fresh jury sees H1 and holds it in scope
        diff, changed = git_change(wd, *fixture_checkout(wd, True))
        v = commit_verdict(L, judge(t, ticket_path, "Ben (example builder)", L["entries"][0]["commit"], wd, diff, changed,
                                    hidden, jurors_from_spec("stub:fail,fail,pass", "appeal"), runner,
                                    "2026-11-27T09:00Z", appeal_of=1))
        log.append(f"#{v['seq']} Ben appeals #1, fresh jury appeal-1..3 -> {v['outcome'].upper()} (final): {v['reason']}")
        wd = os.path.join(tmp, "c3")
        base, head = fixture_checkout(wd)
        diff, changed = git_change(wd, base, head)
        changed.append("tests/test_recall_since.py")
        v = commit_verdict(L, judge(t, ticket_path, "Cy (example builder)", head, wd, diff, changed, hidden,
                                    jurors_from_spec("stub:pass,pass,pass"), runner, "2026-11-26T18:03Z"))
        log.append(f"#{v['seq']} Cy, edits a locked test file -> {v['outcome'].upper()}: {v['reason']}")
        accepted = L["entries"][1]
        assert accepted["outcome"] == "accepted"
        issue = pay(accepted, credit, root=root, date="2026-11-26")
        log.append(f"pay #{accepted['seq']} -> credit ledger issue: {issue['holder']} {creditlib.dollars(issue['cents'])} "
                   f"({issue['multiple']}x the fixed {creditlib.dollars(issue['price_cents'])}), evidence {issue['evidence']}")
        for label, bad in (("pay #1 (rejected)", lambda: pay(L["entries"][0], credit, root=root)),
                           ("pay #2 twice", lambda: pay(accepted, credit, root=root, date="2026-11-27")),
                           ("flip #1 to accepted", lambda: commit_verdict(L, dict(L["entries"][0], outcome="accepted")))):
            try:
                bad()
                log.append(f"NOT refused: {label}")
            except LedgerError as err:
                log.append(f"refused, {label}: {str(err).split('; ')[0]}")
        errs = verify(L)
        log.append("verify: " + ("OK, chain intact, every outcome follows from its results" if not errs else "; ".join(errs)))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return L, log, credit


# ---- command line ---------------------------------------------------------------------------------------

def _jurors(args):
    if args.juror:
        return [CommandJuror(*j.split("=", 1)) for j in args.juror]
    return jurors_from_spec(args.jury)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--ledger", default=DEFAULT_LEDGER)
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("run", "appeal"):
        a = sub.add_parser(name)
        if name == "run":
            a.add_argument("--ticket", required=True); a.add_argument("--builder")
            a.add_argument("--base", required=True); a.add_argument("--commit", required=True)
        else:
            a.add_argument("--verdict", type=int, required=True)
        a.add_argument("--workdir", required=True); a.add_argument("--hidden", required=True)
        a.add_argument("--jury", default=None, help="stub:pass,pass,fail (deterministic, free)")
        a.add_argument("--juror", action="append", help="name=command: a real model the hoster plugs in (paid)")
        a.add_argument("--date", default=None); a.add_argument("--apply", action="store_true")
    b = sub.add_parser("pay")
    b.add_argument("--verdict", type=int, required=True); b.add_argument("--date"); b.add_argument("--apply", action="store_true")
    sub.add_parser("verify"); sub.add_parser("demo", help="the worked run on EXAMPLE-1")
    a = p.parse_args(argv)
    try:
        if a.cmd == "demo":
            for line in demo()[1]:
                print(line)
            return 0
        ledger = load(a.ledger) if os.path.exists(a.ledger) else {"entries": []}
        if a.cmd == "verify":
            errs = verify(ledger)
            for e in errs:
                print("FAIL", e)
            n = len(ledger["entries"])
            print(f"OK: {n} verdicts, chain intact, every outcome follows from its results" if not errs else f"{len(errs)} problems")
            return 1 if errs else 0
        if a.cmd in ("run", "appeal"):
            if not a.jury and not a.juror:
                raise LedgerError("name the jury: --jury stub:... or three --juror name=command")
            if a.cmd == "run":
                path, base, head, builder, appeal_of = a.ticket, a.base, a.commit, a.builder, None
            else:
                first = ledger["entries"][a.verdict - 1]
                path, base, head, builder, appeal_of = os.path.join(ROOT, first["source"]), None, first["commit"], first["builder"], a.verdict
            with open(path, encoding="utf-8") as f:
                t, _ = ticketlib.parse(f.read())
            if a.cmd == "appeal":
                base = subprocess.run(["git", "-C", a.workdir, "rev-parse", f"{head}~1"], capture_output=True, text=True).stdout.strip()
            diff, changed = git_change(a.workdir, base, head)
            v = judge(t, path, builder or t.get("builder"), head, a.workdir, diff, changed, a.hidden, _jurors(a),
                      shell_runner, a.date or now(), appeal_of)
            v = commit_verdict(ledger, v)
            print(json.dumps({k: v[k] for k in ("seq", "ticket", "commit", "outcome", "reason")}))
        else:
            v = ledger["entries"][a.verdict - 1]
            cpath = os.path.join(ROOT, "ledger", "credit.json")
            qpath = os.path.join(ROOT, "ledger", "queue.json")
            credit, queue = load(cpath), load(qpath)
            print(json.dumps(pay(v, credit, queue, date=a.date)))
            if a.apply:
                save(cpath, credit) if v["pays"]["currency"] == "credit" else save(qpath, queue)
            return 0
        if a.apply:
            save(a.ledger, ledger)
    except (LedgerError, KeyError, ValueError, FileNotFoundError) as e:
        print("refused:", e, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
