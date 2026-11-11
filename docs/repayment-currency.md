# Repayment currency: capped revenue claims or the app's own units

**Bottom line (2026-11-11):** a contributor chooses, per ticket, how to be paid: a **capped revenue claim** (repaid from repo revenue, at most the cost of the work) or **transferable service units** (priced in the app's service, transferable between holders, burned when spent, issued only for accepted tickets under a public cap per epic). The project never sells units, never lists them on an exchange and never talks about their price. **An on-chain token or an exchange listing is not allowed** until a lawyer answers the one question at the end of this page. Jordi chose service units on 2026-11-11 after reading the research ([section 0](http://vps3.taild81fbb.ts.net:8973/), [source](https://github.com/AlfaBlok/market-bots/blob/main/docs/research/inference-for-tokens.md)), and the same day made them transferable: "If you can't transfer only use, not what we want."

**Transferability raises the risk.** The research below found units low-risk *while they cannot be sold*. Units that holders can pass to others can also be sold between them, which moves them toward what the SEC treats as an investment contract and can remove MiCA's limited-network and utility exemptions. That risk is accepted knowingly, kept small by the guard rails below, and is the reason for the lawyer question. Source: [the research, section 0](http://vps3.taild81fbb.ts.net:8973/). Not legal advice.

*Not legal, securities, tax or accounting advice. Sources were read on 2026-11-11 unless a date says otherwise.*

## The question

Jordi asked (voice note vn_322d841c, 2026-11-11) whether contributors should be paid in the app's own currency instead: "a payment in kind for your effort", like being paid in a commodity, valued at the exchange rate of the day, worth more if the app is used, and "not compensated by the efforts of others".

## The two options side by side

| | Capped revenue claim | Service units (research read them as non-transferable) |
|---|---|---|
| **What you get** | A payable: the eligible cost of the work, repaid from repo revenue in queue order | N units, each buying a fixed amount of the app's service (for example 1 unit = 1,000 Zenod memory operations) |
| **Most you can get** | The cost of the work, never more | Whatever that service is worth when you spend the units. If the app later charges more for it, each unit buys something worth more |
| **If the project fails** | Nothing is repaid; nobody owes anything | The units buy nothing |
| **Accounting, contributor** | A receivable at cost | Income in kind at its value on the day received, like being paid in a foreign currency; later changes are gains or losses when spent. US: [IRS Notice 2014-21](https://www.irs.gov/irb/2014-16_IRB#NOT-2014-21). Spain: income in kind at euro market value on the day (DGT V1766-22, [Cuatrecasas](https://www.cuatrecasas.com/es/spain/articulo/tributacion-del-staking-en-irpf)). Pricing units at the service's list price gives a clear value; tax is still due in cash |
| **Accounting, project** | A payable until repaid | No cash out today; a debt of service until the units are spent [our reading, check with an accountant] |
| **US securities risk** | Low: repayment of cost, no profit | Low while units cannot be sold: close to a "digital tool" ("a membership, ticket, credential") in the SEC's taxonomy of 2026-03-17 ([SEC 2026-30](https://www.sec.gov/newsroom/press-releases/2026-30-sec-clarifies-application-federal-securities-laws-crypto-assets); [Release 33-11412, 2026-03-23](https://www.govinfo.gov/content/pkg/FR-2026-03-23/html/2026-05635.htm)). That same release says a token given "in exchange for the recipient providing a service", such as fixing bugs, is *not* covered by the airdrop safe reading, so a sellable version is risky |
| **EU (MiCA) risk** | Not a crypto-asset | MiCA's white-paper rules exempt a utility token "providing access to a good or service that exists or is in operation" and tokens used in a limited network; both exemptions fall away once the issuer plans to list it ([MiCA Art. 4(3)-(4), ESMA](https://www.esma.europa.eu/publications-and-data/interactive-single-rulebook/mica/article-4-offers-public-crypto-assets-other)). So the service must exist first and the units stay unlisted |

"Payment in kind" settles how a token is handed over, not what holders expect. Courts count services, not just cash, as the "investment" in the Howey test ([Fordham Corporate Journal, 2025](https://fordhamcorporatejournal.org/wp-content/uploads/2025/10/Cryptocurrencies-NFTS-and-the-Expanding-Definition-of-Investment-Contract.pdf)). In *SEC v. LBRY* (2022-11-07) a token used in a working app was still held a security because the company talked up its price ([Skadden](https://skadden.com/insights/publications/2022/11/court-rules-in-favor-of-sec)). The SEC's proposed "Regulation Crypto Assets" (2026-08-18) is a proposal, not law ([GT Law](https://www.gtlaw.com/en/insights/2026/8/sec-proposes-regulation-crypto-assets-creating-tailored-crypto-offering-exemptions-and-investment-contract-safe-harbor)).

## What projects do today

| Project | Pays in | For | How it went |
|---|---|---|---|
| Filecoin | FIL | Storing data | Network runs; FIL near $0.92, about 99% below its 2021 peak (2026-10, [Coinlore](https://www.coinlore.com/coin/filecoin)) |
| Helium | HNT | Running hotspots | SEC sued Nova Labs, then dropped the case with prejudice on 2025-04-10 ([Decrypt](https://decrypt.co/314437/sec-dismisses-helium-case-ending-gary-genslers-final-act)) |
| Gitcoin | GTC | Past contribution, airdropped 2021 | About $0.23 on 2026-10-27, from about $29 in 2021 ([CoinMarketCap](https://coinmarketcap.com/cmc-ai/gitcoin/price-analysis/)) |
| Gittensor (Bittensor subnet 74) | TAO and the SN74 token | Merged pull requests | Token far below its $2.95 high of 2026-04-08 ([CoinGecko](https://www.coingecko.com/en/coins/gittensor), read 2026-11-10); paid volume flooded sbt with junk until its maintainer shut it down on 2026-04-19 ([eed3si9n](https://eed3si9n.com/shutting-down-the-goldmine/)) |

The pattern: with a tradable token, contributors' pay follows the market more than the project, and paying for output draws farmers. None of them priced pay in units of a service.

## Jordi's choice and why

Contributors choose per ticket: a capped revenue claim, or service units. An on-chain token or exchange listing comes only after a lawyer's yes (Jordi, 2026-11-11, approving the research card market-bots E3-S1; he then started market-bots E3-S2, "restart Nectary with spend-only service units on one seed repo"). Reviewing the first units ledger the same day, he changed one rule: "If you can't transfer only use, not what we want." Units are now transferable between holders.

Why: units pay contributors in the app's service instead of cash, cost the project no cash today, and stay a prepaid voucher for a service that exists. Holders can give or pass them to someone who will use the service. Like oil that can only be burned in our own engine, which can change hands before it is burned.

## Unit rules

1. **Priced in the service**, never in dollars or euros: one unit buys a fixed amount of the app's service.
2. **Transferable between holders**: a holder can move units to another holder in the public ledger. The project itself never sells units, never lists them on an exchange and never helps anyone set a price for them.
3. **Burned when spent**: supply shrinks as the app is used.
4. **Issued only for accepted tickets**, at a rate fixed and published before work starts. Never per line or per pull request size.
5. **Public cap per epic**: the total units an epic may issue is written in the repo before its tickets open.
6. **No price talk**: nobody on the project says units will go up in value. The team's own units sit under the same rules and cap, with no founder premium.

The per-ticket rate between cost and units is set in each epic before work; the research suggested a premium in service value (for example 1.5 times cost), which is our speculation and not decided.

## The lawyer question that gates an on-chain token or a listing

> "We pay contributors in service units they can transfer to other holders, recorded in a public ledger, never sold or listed by us. Is that a security in the US or a crypto-asset needing a MiCA white paper in the EU, and would putting the units on-chain or on an exchange change the answer?"

Until a lawyer answers, units stay in the repo's ledger, off-chain and unlisted, and capped revenue claims stay repayment of cost with nothing above it.

See also: [design principles](design-principles.md), [mission](mission.md).
