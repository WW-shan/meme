[Request a demo](/request-a-demo)

[![](https://cdn.prod.website-files.com/637e4cd92c6f22a30d5225fc/6400aef86808c0ad8f8182fd_TALOS_logo_white_green_RGB.png)](/)

[Solutions](/our-solutions/all)

[Trading Platform](/our-solutions/trading)

[White Label](/our-solutions/white-label)

[RFQ Platform](/our-solutions/rfq-platform)

Portfolio management

[Portfolio Construction](/our-solutions/portfolio-construction)

[Portfolio & Risk Management](/our-solutions/portfolio-and-risk-management)

[Treasury & Settlement](/our-solutions/treasury-and-settlement)

DATA & ANALYTICS

Data

Coin Metrics

[Market Data Feed](/our-solutions/data/market-data-feed)

[Market Data Pro](/our-solutions/data/market-data-pro)

[Network Data Pro](/our-solutions/data/network-data-pro)

[datonomyTM](/our-solutions/data/datonomy)

[Security Master](/our-solutions/data/security-master)

[Post-Trade Analytics](/our-solutions/analytics)

Clients

Buy SIDE

[Asset Managers](/clients/asset-managers)

[ETF Issuers](/clients/etf-issuers)

[Hedge Funds](/clients/hedge-funds)

[Crypto Funds](/clients/crypto-funds)

[Proprietary Trading Firms](/clients/proprietary-trading-firms)

[Token Holders](/clients/token-holders)

Sell Side

[Banks](/clients/banks)

[Retail Investment Platforms](/clients/retail-investment-platforms)

[OTC Desks](/clients/otc-desks)

[Broker-Dealers](/clients/broker-dealers)

Service Providers

[Custodians](/clients/custodians)

[Payment Service Providers](/clients/payment-service-providers)

About Talos

[Why Choose Talos?](/about/why-talos)

[The Talos Story](/about/the-talos-story)

[The Leadership Team](/about/the-leadership-team)

Careers

[Life at Talos](/working/life-at-talos)

[Open Roles](/working/open-roles)

[Internships](/working/internships)

[Provider Network](/provider-network)[Insights](/insights)

[![](https://cdn.prod.website-files.com/637e4cd92c6f22a30d5225fc/64c9302ec3dfbebfd8988772_contact.svg)

Contact](/contact)[Request a demo](/request-a-demo)

By clicking 'accept all cookies', you agree to the storing of optional cookies on your device to enhance site navigation, analyze site usage, and assist in our marketing efforts. If you wish to adjust your cookie settings, please click 'customize cookies'. View our [Privacy Policy](/legals/privacy) for more information

[Deny all cookies](#)[Accept all cookies](#)[Customize cookies](#)

[Back to Insights](/insights)

Knowledge

# Execution Alphas in Crypto Markets: Predicting Volume, Volatility, and Spreads to Reduce Slippage

By:

Eliad Hoch, Head of Quantitative Execution Services at Talos

March 20, 2026

[Email icon](#)[Twitter icon](#)[Linkedin icon](#)



[Back to Insights](/insights)

Knowledge

[KNOWLEDGE](#)

## Execution Alphas in Crypto Markets: Predicting Volume, Volatility, and Spreads to Reduce Slippage

By:

Eliad Hoch, Head of Quantitative Execution Services at Talos

March 20, 2026

[Email icon](#)[Twitter icon](#)[Linkedin icon](#)[![Download icon](https://cdn.prod.website-files.com/637e4cd92c6f22a30d5225fc/64be67de9b938f748641daa6_download.svg)](#)

**Slippage is the hidden tax of trading. You can have strong conviction in what to trade, but execution quality often determines how much of that conviction converts into realized performance. In this excerpt from the Talos Quant Forum, Eliad Hoch, Head of Quant Execution Services, explains how “execution alphas” help quantify and reduce slippage by forecasting market microstructure conditions, then feeding real results back into models, such as the** [**Talos Market Impact Model**](https://www.talos.com/insights/understanding-market-impact-in-crypto-trading-the-talos-model-for-estimating-execution-costs)**, to improve execution over time.**

**Watch Eliad Hoch on Execution Alphas**

## Key takeaways from the talk

### 1. Slippage can be modeled as a market impact problem

Eliad frames slippage (fees included) as an expectation of market impact: trade now and you physically push the order book, trade later and you risk missing the arrival price. At a high level, market impact estimation depends on intraday expectations for volume, volatility, spreads, and trade size, with a focus on building practical “libraries” of these execution alpha signals.

### 2. The “quant execution innovation cycle”: predict, execute, measure, improve

He describes the execution R&D loop:

* Build models to predict microstructure trends
* Express them in algos designed to reduce slippage versus a benchmark
* Use transaction cost analysis (TCA) post-trade to measure what worked
* Feed learnings back to improve the models

This is the operating model for continuously improving execution quality.

### 3. Volume has repeatable intraday patterns, with pronounced “open” effects

Using a year of BTC-USDT consolidated order book data, Eliad shows that intraday volume patterns can be relatively consistent week to week, with notable step-ups around regional “opens”, particularly the US open. He highlights a phenomenon he calls the “MOCX effect” (market open, crypto explosion) where the percentage of daily volume can nearly double during the US open versus typical periods.

Why it matters: if market impact is inversely related to volume, then executing in statistically higher-volume pockets should reduce impact and improve slippage outcomes.

### 4. For Volatility the same intraday dynamic shows up

Variance/volatility exhibits similar time-of-day structure to volume but with wider dispersion. The variability is more pronounced around the US open, reinforcing the point that volatility is inherently “more volatile,” and therefore harder to forecast with high confidence.

### 5. Spreads in highly liquid crypto can be tight, with regime dependence

In the BTC-USDT example, top-of-book spreads are extremely tight and comparatively stable, but they still widen in higher-volatility regimes. In other words, spreads are more predictable than volatility, but they are not constant.

### 6. Talos builds daily, asset-level microstructure forecasts at scale

Eliad describes producing overnight predictions (at UTC midnight) for expected volume, spread, and volatility for the next 24 hours at one-minute resolution, across roughly 23,000 assets and their exchanges. The pipeline includes binning trades/quotes, feature construction, calibration choices (e.g. exponential weighting over 90–150 days at various half-lives), smoothing (adaptive splines), and clustering to improve statistical accuracy

### 7. Accuracy differs by signal, and frequent recalibration matters

He shares indicative performance metrics using an R-squared comparison of predictions vs. realized outcomes in hourly bins over a year of data (top ~75 spot and perp assets across ~50 exchanges):

* Volume: ~65–75%
* Spreads: ~80%
* Volatility: ~25–35%

A key operational point: recalibration cadence matters. Keeping a prediction fixed for 5 days can cut correlation with reality substantially versus recalibrating daily, supporting the case for overnight recalibration.

### 8. VWAP uses volume forecasts to shape execution

Eliad contrasts TWAP (linear schedule) with VWAP (volume-weighted schedule). With a VWAP approach, the execution path accelerates in periods where predicted market volume is higher, aligning trading intensity with expected liquidity. He also references how Talos surfaces these kinds of pre-trade analytics (expected spread, participation rate, interval vs daily comparisons) to help traders decide how to pace risk and execution.

### Why this matters for institutional crypto execution

The main point is not that any single model will perfectly predict markets. It is that systematic forecasts of liquidity and risk conditions, combined with disciplined measurement (TCA) and continuous recalibration, can produce repeatable improvements in execution outcomes and reduce slippage over time.

#### **Related Links:**

* [Understanding Market Impact in Crypto Trading: The Talos Model for Estimating Execution Costs →](https://www.talos.com/insights/understanding-market-impact-in-crypto-trading-the-talos-model-for-estimating-execution-costs)
* [Research paper: An Empirical Model of Market Impact in Cryptocurrency Trading →](https://www.talos.com/insights/an-empirical-model-of-market-impact-in-cryptocurrency-trading)
* [VWAP or TWAP for Crypto Execution? A Market Impact Perspective →](https://www.talos.com/insights/vwap-or-twap-for-crypto-execution-a-market-impact-perspective)

#### **About the Author**

**Eliad Hoch** is the Head of Quantitative Execution Services at Talos, the premier provider of institutional digital asset technology and data for trading and portfolio management. Based in London, he oversees the front-office lifecycle of algorithmic trading, guiding clients through slippage minimization tactics, trade scenario analysis and TCA, while overseeing the algorithmic execution tools and quantitative models available within the Talos platform. Prior to Talos, Eliad spent 2 years as the Founder of GONLabs, a systematic crypto trading hedge fund, focused on quant and machine learning-driven crypto strategies. Before that, he spent 12 years in the equities, futures and FX markets at Bank Of America Merrill Lynch and Goldman Sachs in portfolio algorithmic execution, quant modeling, central risk trading and systematic internalization market making. Eliad has co-authored several papers on systematic trading strategies and market impact, and published a 2024 paper exploring tokenomics design and DeFi value propositions. He is a guest lecturer at various UK universities on algo trading and quant modeling. Eliad holds a masters in computational finance and artificial intelligence from the University of Southampton, where he received first class honors and the top independent research award.

‍

*Disclaimer: Talos Global, Inc., together with its affiliates (collectively, “Talos”), is not an investment advisor or broker/dealer. No Talos product or service constitutes an offer to buy or sell, or a promotion or recommendation of, any digital asset, security, derivative, commodity, financial instrument or product or trading strategy. Further, No Talos product or service is intended to constitute investment advice or a recommendation to make (or refrain from making) any kind of investment decision and may not be relied on as such. Talos offers data and software as a service products that provide connectivity tools for institutional clients.*

[Watch the presentation](https://youtu.be/hyHhO0Dtr3s?si=iyJBoAEInPC-LujP)

## Latest insights and research

[![Hourly Market Invariants for Price Simulations in Digital-Asset Markets](https://cdn.prod.website-files.com/637e4cd92c6f22c15a5225fd/6a04d68bcd494aaeb7d56e87_Website%20thumbnail%20-%20Hourly%20Market%20Invariants%20for%20Price%20Simulations%20in%20Digital-Asset%20Markets.jpg)

![](https://cdn.prod.website-files.com/637e4cd92c6f22a30d5225fc/63ef7785993540e0068ad980_talos-intel-bg-block.png)

This is some text inside of a div block.

May 28, 2026

Hourly Market Invariants for Price Simulations in Digital-Asset Markets

Generating reliable daily risk scenarios for digital assets is complicated by the fact that there is no market close. Talos presents an empirically validated approach to building daily-horizon price scenarios from 24/7 hourly data.

Written by:

Marco Marchioro, Principal, Quantitative Research

1 minute read](/insights/hourly-market-invariants-for-price-simulations-in-digital-asset-markets)

[![The Infrastructure Behind the Institutional Adoption of Digital Assets](https://cdn.prod.website-files.com/637e4cd92c6f22c15a5225fd/6a16179800534197b285e66c_Media-OndernemersLounge.jpg)

![](https://cdn.prod.website-files.com/637e4cd92c6f22a30d5225fc/63ef7785993540e0068ad980_talos-intel-bg-block.png)

This is some text inside of a div block.

May 27, 2026

The Infrastructure Behind the Institutional Adoption of Digital Assets

Dutch TV Broadcast - Talos Head of EMEA Sales Frank van Zegveld on "Ondernemerslounge"

Written by:

1 minute read](/insights/the-infrastructure-behind-the-institutional-adoption-of-digital-assets)

[![Execution Cost Savings by the Numbers: The Talos Quant Execution Insights Report 2026](https://cdn.prod.website-files.com/637e4cd92c6f22c15a5225fd/6a0e11078c217aaf12ef641f_quant-execution-insights-report.png)

![](https://cdn.prod.website-files.com/637e4cd92c6f22a30d5225fc/63ef7785993540e0068ad980_talos-intel-bg-block.png)

This is some text inside of a div block.

May 27, 2026

ANALYSIS

Execution Cost Savings by the Numbers: The Talos Quant Execution Insights Report 2026

Slippage is the hidden tax of trading, and in institutional crypto, it is one of the biggest determinants of whether a strategy’s expected alpha actually survives execution. In our 2026 Quant Execution Insights Report, my colleagues Sirui Zhang, Kaan Giray and I analyze the full lifecycle of more than 250,000 parent orders across 600+ assets traded on Talos during 2025, comparing what our algorithms actually achieved against two benchmarks: arrival price and a size-feasible naive sweep. The results show where pre-trade calibration, smart liquidity sourcing and the execution alphas we’ve written about previously translate directly into basis points saved.

Written by:

Eliad Hoch, Head of Quantitative Execution Services at Talos

3 minutes](/insights/execution-cost-savings-by-the-numbers-the-talos-quant-execution-insights-report-2026)

[View all our latest insights](/insights)

## Request a demo

[Request a demo](/request-a-demo)

Find out how Talos can simplify the way you interact with the digital asset markets.

[White Label](/our-solutions/white-label)
[Portfolio Construction](/our-solutions/portfolio-construction)
[Portfolio & Risk Management](/our-solutions/portfolio-and-risk-management)
[Treasury & Settlement](/our-solutions/treasury-and-settlement)
[Analytics](/our-solutions/analytics)
