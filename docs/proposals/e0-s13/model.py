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
