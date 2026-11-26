#!/usr/bin/env python3
"""Nectary ticket validator (docs/ticket-template.md, schema docs/ticket.schema.json).

Stdlib only. A ticket is a Markdown file that opens with a JSON object between two `---` lines,
followed by the human sections the template names.

  python3 tools/ticket.py check tickets/*.md      exit 0 when every ticket passes, 1 otherwise
  python3 tools/ticket.py ladder --runs 8         the estimate and the price ladder for 8 agent runs
  python3 tools/ticket.py show tickets/x.md       the front matter as JSON (for the board and the ledger)
"""
import argparse
import datetime as dt
import json
import math
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEMA_PATH = os.path.join(ROOT, "docs", "ticket.schema.json")

# The price rule Jordi said yes to (EPIC-0-A5, 2026-11-26); same numbers as docs/proposals/e0-s13/model.py.
RUN_COST = 1.20
STEP_UP = 0.25
STEP_HOURS = 48
CAP_X = 1.5
TICKET_MAX = 50.0

SECTIONS = ("Deliverable", "Acceptance", "Evidence", "Eligible cost", "Price and credit", "Repayment trigger")
# L-1: never stake, share, investment or return language in ticket text.
BANNED = re.compile(r"\b(stakes?|staking|shares?|shareholders?|invest(ment|ments|or|ors|ing|ed)?|returns?)\b", re.I)
HELD_STATES = ("held", "submitted", "accepted", "rejected")


class TicketError(Exception):
    pass


def money(x):
    return round(float(x) + 1e-9, 2)


def parse(text):
    """Split a ticket into (front matter dict, Markdown body)."""
    m = re.match(r"\A---\s*\n(.*?)\n---\s*\n?(.*)\Z", text, re.S)
    if not m:
        raise TicketError("no front matter: a ticket opens with a JSON object between two '---' lines")
    try:
        meta = json.loads(m.group(1))
    except json.JSONDecodeError as e:
        raise TicketError(f"front matter is not valid JSON: {e}")
    if not isinstance(meta, dict):
        raise TicketError("front matter must be a JSON object")
    return meta, m.group(2)


def load_schema(path=SCHEMA_PATH):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


TYPES = {"object": dict, "array": list, "string": str, "boolean": bool}


def schema_errors(value, schema, path="ticket"):
    """The subset of JSON Schema the template uses: type, required, properties, items, enum,
    minItems, minLength, minimum, pattern."""
    errs = []
    t = schema.get("type")
    if t == "integer":
        ok = isinstance(value, int) and not isinstance(value, bool)
    elif t == "number":
        ok = isinstance(value, (int, float)) and not isinstance(value, bool)
    elif t:
        ok = isinstance(value, TYPES[t])
    else:
        ok = True
    if not ok:
        return [f"{path}: must be {t}"]
    if "enum" in schema and value not in schema["enum"]:
        errs.append(f"{path}: must be one of {schema['enum']}, got {value!r}")
    if isinstance(value, str):
        if len(value.strip()) < schema.get("minLength", 0):
            errs.append(f"{path}: too short (at least {schema['minLength']} characters)")
        if "pattern" in schema and not re.search(schema["pattern"], value):
            errs.append(f"{path}: {value!r} does not match {schema['pattern']}")
    if isinstance(value, (int, float)) and not isinstance(value, bool) and "minimum" in schema:
        if value < schema["minimum"]:
            errs.append(f"{path}: must be at least {schema['minimum']}")
    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            errs.append(f"{path}: needs at least {schema['minItems']} item(s)")
        for i, item in enumerate(value):
            errs += schema_errors(item, schema.get("items", {}), f"{path}[{i}]")
    if isinstance(value, dict):
        for key in schema.get("required", []):
            if key not in value:
                errs.append(f"{path}.{key}: missing")
        for key, sub in schema.get("properties", {}).items():
            if key in value:
                errs += schema_errors(value[key], sub, f"{path}.{key}")
    return errs


def when(s):
    return dt.datetime.strptime(s, "%Y-%m-%dT%H:%MZ")


def estimate_price(runs, run_cost=RUN_COST):
    """The estimate in dollars and the posted price (the estimate rounded to whole dollars)."""
    amount = money(runs * run_cost)
    return amount, max(1, int(math.floor(amount + 0.5)))


def price_cap(posted):
    return money(min(posted * CAP_X, TICKET_MAX))


def ladder(posted):
    """Posted price after 0, 1, 2 ... unheld 48 h windows; the last step is the cap."""
    cap, out, p = price_cap(posted), [], float(posted)
    while money(p) < cap:
        out.append(money(p))
        p *= 1 + STEP_UP
    return out + [cap]


def price_at(posted, posted_at, held_at):
    steps = int((when(held_at) - when(posted_at)).total_seconds() // (STEP_HOURS * 3600))
    lad = ladder(posted)
    return lad[min(max(steps, 0), len(lad) - 1)]


def banned_words(value, path="ticket"):
    """L-1 check over every string in the ticket except test commands."""
    out = []
    if isinstance(value, dict):
        for k, v in value.items():
            if k != "cmd":
                out += banned_words(v, f"{path}.{k}")
    elif isinstance(value, list):
        for i, v in enumerate(value):
            out += banned_words(v, f"{path}[{i}]")
    elif isinstance(value, str):
        for m in BANNED.finditer(value):
            out.append(f"{path}: banned word {m.group(0)!r} (L-1: claims are capped cost repayment)")
    return out


def rule_errors(t):
    """The rules a schema cannot state: price arithmetic, the ladder, credit, pay choice, jury."""
    errs = []
    p, c, pay = t["price"], t["credit"], t["pay_in"]
    est = p["estimate"]
    amount, posted = estimate_price(est["runs"], est["run_cost"])
    if money(est["amount"]) != amount:
        errs.append(f"price.estimate.amount: {est['amount']} but {est['runs']} runs x ${est['run_cost']} = {amount}")
    if amount > TICKET_MAX:
        errs.append(f"price.estimate: ${amount} is above the ${TICKET_MAX:.0f} ticket maximum; split the ticket")
    if money(p["posted"]) != posted:
        errs.append(f"price.posted: {p['posted']} but the estimate ${amount} posts at ${posted}")
    if money(p["price_cap"]) != price_cap(p["posted"]):
        errs.append(f"price.price_cap: {p['price_cap']} but min(1.5 x {p['posted']}, 50) = {price_cap(p['posted'])}")
    if when(est["at"]) > when(p["posted_at"]):
        errs.append("price.estimate.at: the estimate must be made before the ticket is posted")
    held = t["status"] in HELD_STATES
    if held:
        for key in ("held_at", "fixed"):
            if key not in p:
                errs.append(f"price.{key}: missing (a {t['status']} ticket has a price fixed when it was held)")
        if "builder" not in t or not str(t.get("builder", "")).strip():
            errs.append(f"builder: missing (a {t['status']} ticket names who holds it)")
    elif "fixed" in p or "held_at" in p:
        errs.append(f"price: a {t['status']} ticket has no fixed price yet; drop price.fixed and price.held_at")
    if "fixed" in p and "held_at" in p:
        if when(p["held_at"]) < when(p["posted_at"]):
            errs.append("price.held_at: before price.posted_at")
        else:
            want = price_at(p["posted"], p["posted_at"], p["held_at"])
            if money(p["fixed"]) != want:
                errs.append(f"price.fixed: {p['fixed']} but held after posting at {p['posted_at']} the ladder price is {want}")
        if money(p["fixed"]) > money(p["price_cap"]):
            errs.append(f"price.fixed: {p['fixed']} is above the cap {p['price_cap']}")
    if "amount" in c:
        if "fixed" not in p:
            errs.append("credit.amount: set only once the price is fixed (multiple x price.fixed)")
        elif money(c["amount"]) != money(c["multiple"] * p["fixed"]):
            errs.append(f"credit.amount: {c['amount']} but {c['multiple']} x {p['fixed']} = {money(c['multiple'] * p['fixed'])}")
    elif "fixed" in p:
        errs.append("credit.amount: missing (multiple x price.fixed, known the moment the ticket is held)")
    choice = pay["choice"]
    if t["status"] == "accepted" and choice == "open":
        errs.append("pay_in.choice: an accepted ticket records the builder's choice: credit, claim or units")
    if choice != "claim" and "claim_amount" in pay:
        errs.append("pay_in.claim_amount: only a ticket paid as a claim has one (never two currencies)")
    if choice != "units" and "units_rate" in pay:
        errs.append("pay_in.units_rate: only a ticket paid in units has one (never two currencies)")
    if choice == "claim":
        if "claim_amount" not in pay:
            errs.append("pay_in.claim_amount: missing (the fixed price, 1x, never more)")
        elif "fixed" in p and money(pay["claim_amount"]) != money(p["fixed"]):
            errs.append(f"pay_in.claim_amount: {pay['claim_amount']} but cash is repaid at cost: the fixed price {p['fixed']}, never more")
    if choice == "units" and "units_rate" not in pay:
        errs.append("pay_in.units_rate: missing (units are fixed before work, docs/units.md rule 2)")
    jury = t["acceptance"]["jury"]
    if not (jury["models"] / 2 < jury["pass"] <= jury["models"]):
        errs.append(f"acceptance.jury.pass: {jury['pass']} of {jury['models']} is not a majority")
    for i, q in enumerate(t["requotes"]):
        if when(q["at"]) > when(p["posted_at"]):
            errs.append(f"requotes[{i}]: an old quote must come before the current price.posted_at")
    return errs


def body_errors(body):
    heads = {h.strip().lower() for h in re.findall(r"^##\s+(.+?)\s*$", body, re.M)}
    return [f"body: section '## {s}' missing" for s in SECTIONS if s.lower() not in heads]


def check_text(text, schema=None):
    """Every error in one ticket's text; an empty list means it passes."""
    try:
        meta, body = parse(text)
    except TicketError as e:
        return [str(e)]
    errs = schema_errors(meta, schema or load_schema())
    if errs:  # arithmetic on a ticket with missing or mistyped fields would only add noise
        return errs + banned_words(meta) + body_errors(body)
    return rule_errors(meta) + banned_words(meta) + banned_words(body, "body") + body_errors(body)


def check_file(path, schema=None):
    with open(path, encoding="utf-8") as f:
        return check_text(f.read(), schema)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check", help="check tickets against the template")
    c.add_argument("paths", nargs="+")
    lad = sub.add_parser("ladder", help="estimate and price ladder for a number of agent runs")
    lad.add_argument("--runs", type=int, required=True)
    lad.add_argument("--run-cost", type=float, default=RUN_COST)
    lad.add_argument("--multiple", type=float, default=2.0)
    s = sub.add_parser("show", help="print a ticket's front matter as JSON")
    s.add_argument("path")
    a = ap.parse_args(argv)
    if a.cmd == "check":
        schema, bad = load_schema(), 0
        for path in a.paths:
            errs = check_file(path, schema)
            print(f"{'PASS' if not errs else 'FAIL'} {path}")
            for e in errs:
                print(f"  - {e}")
            bad += bool(errs)
        return 1 if bad else 0
    if a.cmd == "ladder":
        amount, posted = estimate_price(a.runs, a.run_cost)
        print(f"estimate {a.runs} runs x ${a.run_cost:.2f} = ${amount:.2f}; posted ${posted}; cap ${price_cap(posted):.2f}")
        for i, step in enumerate(ladder(posted)):
            print(f"  after {i * STEP_HOURS:>3} h unheld: price ${step:.2f}, credit at {a.multiple:g}x ${money(step * a.multiple):.2f}, claim ${step:.2f}")
        return 0
    if a.cmd == "show":
        with open(a.path, encoding="utf-8") as f:
            print(json.dumps(parse(f.read())[0], indent=2, ensure_ascii=False))
        return 0


if __name__ == "__main__":
    sys.exit(main())
