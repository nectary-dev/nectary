"""E0-S13 numbers: what Nectary credit costs a Zenod hoster. Every input is labelled REAL (with its source) or ASSUMPTION.
Run: python3 model.py  (prints every number the page shows)."""
PRICE_EUR = 9.0            # REAL: Zenod Hosted EUR 9/month + VAT (zenod apps/site/public/legal/terms.html)
FX = 1.055                 # ASSUMPTION: EUR 1 = USD 1.055
PRICE = PRICE_EUR * FX     # USD list price of one month of Zenod = one "credit-month"
CARD = 0.40                # ASSUMPTION: Stripe EU card fee, about 1.5% + EUR 0.25
MODEL_CAP = 5.0            # REAL: at most $5 of model cost per account a month (zenod limits.ts, Jordi E26-A7)
INFRA_TODAY = 3.0          # REAL estimate: a EUR 20 Hetzner box hosts 5-10 accounts, EUR 2-4 each (zenod docs/HOSTED-PLAN-2026-07-02.md)
MODEL_TYPICAL = 1.5        # ASSUMPTION: a typical account uses half of the $3 answer allowance (not yet measured)
WORK_VALUE = 1.0           # ASSUMPTION: $1 of accepted builder inference is worth $1 to the hoster (what it would pay to do it itself)

SCALES = {   # paying users, builders, $ inference per builder a month, model $/user, infra $/user
    "small":  dict(users=10,   builders=5,   inf=10, model=1.5, infra=3.0),   # ASSUMPTION: about today
    "medium": dict(users=200,  builders=40,  inf=10, model=1.5, infra=2.0),   # ASSUMPTION: fuller boxes
    "large":  dict(users=5000, builders=500, inf=10, model=1.0, infra=1.0),   # ASSUMPTION: bigger boxes, cheaper models
}

def serve_cost(model, infra):           # hoster's cost of one credit-month (no card fee: nobody pays)
    return model + infra

def cost_per_dollar(k, model, infra):   # hoster cost of k x credit per $1 of builder inference
    return k * serve_cost(model, infra) / PRICE

def breakeven(model, infra):            # multiple where credit cost = value of the work
    return WORK_VALUE * PRICE / serve_cost(model, infra)

if __name__ == "__main__":
    print(f"price ${PRICE:.2f}")
    for name, (m, i) in {"typical": (MODEL_TYPICAL, INFRA_TODAY), "at cap": (MODEL_CAP, INFRA_TODAY)}.items():
        s = serve_cost(m, i)
        print(f"{name}: serve ${s:.2f}/credit-month = {s/PRICE:.0%} of price; break-even {breakeven(m, i):.1f}x;",
              " ".join(f"{k}x=${cost_per_dollar(k, m, i):.2f}" for k in (1, 2, 3, 5, 10)))
    profit = PRICE - MODEL_TYPICAL - INFRA_TODAY - CARD
    print(f"user: model {MODEL_TYPICAL} infra {INFRA_TODAY} card {CARD} profit {profit:.2f} half {profit/2:.2f}")
    print(f"work funded per paying user a month at 2x: ${profit/2/cost_per_dollar(2, MODEL_TYPICAL, INFRA_TODAY):.2f}; 5x: ${profit/2/cost_per_dollar(5, MODEL_TYPICAL, INFRA_TODAY):.2f}")
    # builder example: $10 ticket
    for k in (2, 5):
        credit = 10 * k; months = credit / PRICE; cost = months * serve_cost(MODEL_TYPICAL, INFRA_TODAY)
        print(f"ticket $10 at {k}x: credit ${credit} = {months:.1f} months; hoster cost ${cost:.2f}; net on work {10 - cost:+.2f}")
    for name, s in SCALES.items():
        p = PRICE - s["model"] - s["infra"] - CARD
        fund = s["users"] * p / 2
        inflow = s["builders"] * s["inf"]
        be = breakeven(s["model"], s["infra"])
        cost2 = cost_per_dollar(2, s["model"], s["infra"]) * inflow
        cost5 = cost_per_dollar(5, s["model"], s["infra"]) * inflow
        kfund = fund / cost_per_dollar(1, s["model"], s["infra"]) / inflow
        print(f"{name}: profit/user {p:.2f} fund ${fund:,.0f}/mo inflow ${inflow:,}/mo; cost 2x ${cost2:,.0f} 5x ${cost5:,.0f}; break-even {be:.1f}x; fund covers {kfund:.1f}x; supported {min(be, kfund):.1f}x")

# ---- E0-S14: the 2x multiplies a price known before work, never the inference burned ----
RUN_COST = 1.20            # REAL: a typical team agent run costs $1.20 at API prices (zenod docs/evidence/e7-s1)
STEP_UP = 0.25             # PROPOSAL: an unheld ticket's price rises 25% every 48 hours
CAP_X = 1.5                # PROPOSAL: the price never goes above 1.5x the first estimate (the hoster's ceiling)
TICKET_MAX = 50.0          # PROPOSAL: no single ticket above $50; bigger work is split
SPREAD = 0.35              # ASSUMPTION: real inference varies around a calibrated estimate, log-normal sigma 0.35

def estimate(runs):                       # AI estimator: expected agent runs (tests, size, past tickets) x run cost
    return round(runs * RUN_COST)

def price_ladder(est):                    # posted price after 0, 1, 2 ... unheld 48 h windows, up to the cap
    out, p = [], float(est)
    while p < est * CAP_X:
        out.append(round(p, 2)); p *= 1 + STEP_UP
    return out + [round(est * CAP_X, 2)]

def hoster_cost(price, k=2, model=MODEL_TYPICAL, infra=INFRA_TODAY):   # known the moment the price is posted
    return k * price * serve_cost(model, infra) / PRICE

def share_under(k, sigma=SPREAD):         # share of builders whose real inference exceeds k x price (credit < 1x real)
    import math
    return 0.5 * math.erfc(math.log(k) / (sigma * math.sqrt(2)))

if __name__ == "__main__":
    est = estimate(8)
    print(f"\nE0-S14 estimate: 8 runs x ${RUN_COST} = ${8*RUN_COST:.2f} -> ${est}; ladder {price_ladder(est)}")
    for name, real in (("Ana", 7 * RUN_COST), ("Ben", 11 * RUN_COST)):
        print(f"{name}: real ${real:.2f}, credit ${2*est} = {2*est/real:.1f}x the real inference, keeps {est-real:+.2f}")
    print(f"hoster cost at price ${est}: 2x ${hoster_cost(est):.2f} typical, ${hoster_cost(est, model=MODEL_CAP):.2f} at AI cap;"
          f" at cap price ${est*CAP_X:.0f}: ${hoster_cost(est*CAP_X):.2f}; per $1 of price ${hoster_cost(1):.2f}")
    print(f"share of tickets where credit < real inference at 2x: {share_under(2):.1%}; at 1x price (cash at cost): {share_under(1):.0%}")
    print(f"tickets the small fund pays a month: {(PRICE-MODEL_TYPICAL-INFRA_TODAY-CARD)*10/2/hoster_cost(est):.1f} at ${est}")
