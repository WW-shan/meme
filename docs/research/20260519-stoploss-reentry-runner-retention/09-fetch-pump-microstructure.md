# Microstructure and Manipulation: Quantifying Pump-and-Dump Dynamics in Cryptocurrency Markets

## Abstract

Building on our prior threshold‐based analysis of six months of Poloniex trading data, we have extended both the temporal span and granularity of our study by incorporating minute‑level OHLCV records for 1,021 tokens around each confirmed pump‑and‑dump event. First, we algorithmically identify the accumulation phase—marking the initial and final insider volume spikes—and observe that 70% of pre‑event volume transacts within one hour of the pump announcement. Second, we compute conservative lower bounds on insider profits under both a single‑point liquidation at 70% of peak and a tranche‑based strategy (selling 20% at 50%, 30% at 60%, and 50% at 80% of peak), yielding median returns above 100% and upper‐quartile returns exceeding 2000%. Third, by unfolding the full pump structure and integrating social‑media verification (e.g., Telegram announcements), we confirm numerous additional events that eluded our initial model. We also categorize schemes into “pre‑accumulation” versus “on‑the‑spot” archetypes—insights that sharpen detection algorithms, inform risk assessments, and underpin actionable strategies for real‑time market‑integrity enforcement.

Keywords: Cryptocurrency, Market Manipulation, Pump and Dump, Disinformation, Financial Scam

## 1 Introduction

Cryptocurrency markets, by virtue of their 24/7 operation, low liquidity, and jurisdictional fragmentation, are particularly susceptible to coordinated market manipulations [[1](https://arxiv.org/html/2504.15790v1#bib.bib1)]. Among these, pump-and-dump (P&D) schemes stand out for their rapid price inflation, driven by organized insider purchases, and subsequent collapses that inflict heavy losses on other participants [[2](https://arxiv.org/html/2504.15790v1#bib.bib2), [3](https://arxiv.org/html/2504.15790v1#bib.bib3)]. Unlike traditional equities, where regulatory oversight and circuit breakers curtail such practices, crypto exchanges often lack enforcement mechanisms, enabling malicious actors to exploit information asymmetries and technological affordances [[4](https://arxiv.org/html/2504.15790v1#bib.bib4)].

Historically, pump-and-dump manipulation dates back to early 20th-century penny-stock frauds, and re-surged during the dot‑com bubble when unscrupulous brokers hyped illiquid internet shares [[5](https://arxiv.org/html/2504.15790v1#bib.bib5), [6](https://arxiv.org/html/2504.15790v1#bib.bib6)]. In the crypto realm, the phenomenon has been supercharged by messaging platforms such as Telegram and Discord, which facilitate anonymous coordination of thousands of participants [[5](https://arxiv.org/html/2504.15790v1#bib.bib5), [7](https://arxiv.org/html/2504.15790v1#bib.bib7)]. Prior research [[8](https://arxiv.org/html/2504.15790v1#bib.bib8)] introduced an unsupervised, threshold-based model using hourly Poloniex data — combining exponentially weighted moving averages, volatility measures, and double-conditioned volume thresholds — to detect local price–volume anomalies. While effective in flagging coarse-grained events, that framework could not resolve the sub-hour insider strategies underpinning each pump.

In order to better explain the structure of pump and dump events and quantify the behavioral dynamic from the organizers, we provide an extension to the previous work [[8](https://arxiv.org/html/2504.15790v1#bib.bib8)].
In the current article we address the following critical gaps:

Temporal Precision in Accumulation Phase: We refine the analysis window to minute-level resolution, capturing the exact timing of insider volume spikes and observing that accumulation is often compressed into the last 24 hours before the pump announcement.

Insider Profit Quantification: Leveraging first-trade and VWAP proxies for purchase cost, combined with conservative liquidation scenarios (70% of peak or staged tranches at [50%,60%,80%]), we derive lower-bound profit distributions that underscore the immense incentives driving P&D operations.

By integrating these elements and validating against social-media–confirmed events, we demonstrate improved detection accuracy and uncover previously undetected pump occurrences. The remainder of the paper is structured as follows: Section [2](https://arxiv.org/html/2504.15790v1#S2 "2 Data and Event Selection ‣ Microstructure and Manipulation: Quantifying Pump-and-Dump Dynamics in Cryptocurrency Markets") details data sources and pre-processing; Section [3](https://arxiv.org/html/2504.15790v1#S3 "3 Accumulation Phase ‣ Microstructure and Manipulation: Quantifying Pump-and-Dump Dynamics in Cryptocurrency Markets") and [4](https://arxiv.org/html/2504.15790v1#S4 "4 Quantification of the Accumulation Phase ‣ Microstructure and Manipulation: Quantifying Pump-and-Dump Dynamics in Cryptocurrency Markets") analyze accumulation-phase dynamics; Section [5](https://arxiv.org/html/2504.15790v1#S5 "5 Profit Estimation ‣ Microstructure and Manipulation: Quantifying Pump-and-Dump Dynamics in Cryptocurrency Markets") introduces profit estimation methods and results; Section [6](https://arxiv.org/html/2504.15790v1#S6 "6 Conclusion ‣ Microstructure and Manipulation: Quantifying Pump-and-Dump Dynamics in Cryptocurrency Markets") concludes with implications and future work.

## 2 Data and Event Selection

We obtained our dataset from Poloniex’s public API [[9](https://arxiv.org/html/2504.15790v1#bib.bib9)], comprising 1,101 trading pairs over the six‑month period from 15 August 2024 to 15 February 2025. Applying the hourly threshold model [[8](https://arxiv.org/html/2504.15790v1#bib.bib8)], we identified 1,021 tokens with at least one flagged event (hereafter “Target Date”). For each token–event pair (grouped by {symbol, target\_date}), we extracted minute‑level OHLCV data from four days before to two days after each event, yielding approximately 8.2 million records. All timestamps were converted to UTC.

Some tokens exhibited multiple flagged events and thus appear under more than one Target Date. Our initial detection model employed hourly data to reduce market noise and successfully flag candidate pump‑and‑dump episodes. Building on this, our objective was to “zoom in” around these detected episodes, leveraging higher‑resolution data, to uncover finer patterns that reliably confirm event occurrence.

Previous work suggests that pump‑and‑dump (P&D) schemes unfold in three phases: accumulation, pump, and dump [[10](https://arxiv.org/html/2504.15790v1#bib.bib10), [11](https://arxiv.org/html/2504.15790v1#bib.bib11), [12](https://arxiv.org/html/2504.15790v1#bib.bib12)]. During the accumulation phase, organizers covertly accumulate the target token at low prices without attracting market attention. However, several practical considerations constrain the duration of this phase:

Speculative trading style: P&D organizers treat these operations as short‑term speculation, not long‑term investment, and hence prefer not to tie up capital for extended periods.

Risk of counter‑schemes: Early accumulation increases the risk that other organizers might target the same token, potentially forcing the initial accumulators to buy at inflated prices or suffer losses.

On these grounds, we posit that the accumulation phase most likely occurs within four days preceding the Target Date. Although the pump and dump themselves typically conclude within minutes, we conservatively include a two‑day post‑event window to capture any residual market effects.

## 3 Accumulation Phase

To characterize and quantify the accumulation phase within our dataset, we performed targeted visual analyses on several subsets of 20 tokens. For each selected token, we plotted minute‐level trading volume over time, inspecting volume spikes that may indicate insider accumulation. To supplement this quantitative approach, we cross‐referenced tokens lacking clear volume signatures with announcements on social media platforms, notably Telegram pump channels, and confirmed organized events for many cases previously unrecognized.

Visualizations were produced in two formats, each designed to highlight different facets of the accumulation process. Below, we describe each visualization type along with key observations and directions for further study.

### Visualization Type 1: Volume Spikes

We first plotted token‐quantity (base‐asset) traded per minute, as this measure most directly reflects accumulation activity. Although quote‐asset volume would yield equivalent insights, base‐asset quantity conveys the actual number of tokens exchanged.

For numerous tokens, small but sharp spikes in base‐asset volume appeared within seconds or up to one minute prior to the Target Date. Figure [1](https://arxiv.org/html/2504.15790v1#S3.F1 "Figure 1 ‣ Visualization Type 1: Volume Spikes ‣ 3 Accumulation Phase ‣ Microstructure and Manipulation: Quantifying Pump-and-Dump Dynamics in Cryptocurrency Markets") illustrates representative cases. Our results confirm our expectation that accumulation often occurs very close the pump announcement rather than within the preceding four‐days or more window.

![Refer to caption](extracted/6380150/FLOKICEO_USDT.png)

### Visualization Type 2: High, Low and Volume Spikes

To further probe market dynamics, we plotted minute‐level High and Low prices around the Target Date. Trading ”candles” are defined as:

Open: Price of the first trade in the interval.

High: Maximum trade price in the interval.

Low: Minimum trade price in the interval.

Close: Price of the last trade in the interval.

Crypto markets operate continuously (24/7), so unlike traditional equity markets, there is no time gap between each close and the next open.
Our data reveal a distinctive pattern where for extended intervals, minute‑level OHLC prices remain essentially constant, indicating prolonged inactivity. These low‑liquidity, “dormant” tokens are disproportionately targeted by pump‑and‑dump schemes, a finding that corroborates previous market, manipulation studies [[13](https://arxiv.org/html/2504.15790v1#bib.bib13), [14](https://arxiv.org/html/2504.15790v1#bib.bib14), [15](https://arxiv.org/html/2504.15790v1#bib.bib15)].

In tokens with confirmed pump events, High and Low prices diverged significantly during the pump itself (lasting only a few minutes) and then re-converged immediately afterward, returning to pre‐event levels. This behavior underscores a rapid price expansion and contraction consistent with classic pump‐and‐dump activity. Figure [2](https://arxiv.org/html/2504.15790v1#S3.F2 "Figure 2 ‣ Visualization Type 2: High, Low and Volume Spikes ‣ 3 Accumulation Phase ‣ Microstructure and Manipulation: Quantifying Pump-and-Dump Dynamics in Cryptocurrency Markets") shows an example.

![Refer to caption](extracted/6380150/RDNT_USDT.png)

Our observations reveal two archetypal pump strategies:

Pre‑Accumulated Tokens:
Assets for which insiders deliberately build positions in advance, creating observable volume spikes before the announcement.

On‑The‑Spot Tokens:
Assets with no discernible accumulation period, where buying and pumping occur almost simultaneously.

Recognizing these categories allows us to tailor both detection algorithms and risk assessments to the specific dynamics of each pump archetype.

![Refer to caption](extracted/6380150/LOOT_No_Accumulation.png)

## 4 Quantification of the Accumulation Phase

To refine our detection model, we formalize the accumulation phase as the time interval during which discrete, transient volume spikes occur before the Target Date. We pose two primary questions:

Spike Timing: What is the distribution of delays between observed volume spikes and the Target Date? Specifically, what proportion of spikes occur within defined intervals (e.g., minutes or hours) before the pump?

Spike Span: What is the duration between the earliest and latest spikes per event, and does this imply a concentrated or protracted accumulation?

### Proposed Algorithmic Framework

We define the following computational steps to measure accumulation spans for each token–event pair:

### Aggregated Analysis

We evaluated the presence and duration of pre‐pump accumulation phases across all identified pump‐and‐dump events. Our dataset comprised 485 candidate events for which we had minute‐level OHLCV data spanning four days before to two days after each event’s target date. By scanning each event’s time series for non‐zero traded quantities prior to the pump onset, we derived two new timestamps, accum\_start and accum\_end, which bound the accumulation window.

Event Coverage and Accumulation Prevalence: Out of 485 total events, 336 (69.3%) exhibited at least one minute with non‐zero traded volume before the pump start, indicating a detectable accumulation phase. The remaining 149 events (30.7%) showed no such pre‐pump trading, suggesting either extremely rapid accumulation or an absence of insider positioning detectable at minute granularity:

| Metric | Value |
| --- | --- |
| Total Events | 485 |
| Events with Accumulation | 336 (69.3%) |
| Events without Accumulation | 149 (30.7%) |

Accumulation Duration Statistics: For those events with accumulation, we computed the span between the first and last minute of pre‐pump trading. The distribution of accumulation spans (in minutes) exhibits considerable variability:

| Statistic | Span (minutes) |
| --- | --- |
| Minimum | 1 |
| Average | 2,160.8 |
| Maximum | 5,873 |
| Standard Deviation | 2,108.2 |

Figure [4](https://arxiv.org/html/2504.15790v1#S4.F4 "Figure 4 ‣ Aggregated Analysis ‣ 4 Quantification of the Accumulation Phase ‣ Microstructure and Manipulation: Quantifying Pump-and-Dump Dynamics in Cryptocurrency Markets") shows the full distribution of accumulation spans, highlighting the heavy right‐tail of events with very extended pre‐pump positioning.

![Refer to caption](extracted/6380150/accumulation_span_histogram.png)

Interpretation: The fact that nearly 70% of events feature a detectable accumulation phase, often spanning some days, supports the hypothesis that insider organizers typically build positions incrementally to avoid drawing market attention. However, the 30% of events lacking pre‐pump volume at minute resolution may correspond to rapid, high‐frequency accumulation or to events where insider orders are sufficiently concealed within order books. These findings justify a two‐pronged detection strategy that (i) monitors for sustained accumulation over hours or days and (ii) remains sensitive to near‐instantaneous build‐ups detectable only at sub‐minute granularity.

## 5 Profit Estimation

To gauge the economic incentive driving pump‑and‑dump (P&D) schemes, we compute a conservative lower bound on insider profits. Using the minute‑level OHLCV data and accumulation intervals identified in Section [4](https://arxiv.org/html/2504.15790v1#S4 "4 Quantification of the Accumulation Phase ‣ Microstructure and Manipulation: Quantifying Pump-and-Dump Dynamics in Cryptocurrency Markets"), we estimate both the cost basis for tokens acquired during accumulation and the proceeds from their subsequent liquidation at the event’s peak.

Insiders rarely unload their entire position at once, since an abrupt sell‑off would collapse the price before they finish exiting [[16](https://arxiv.org/html/2504.15790v1#bib.bib16), [17](https://arxiv.org/html/2504.15790v1#bib.bib17)]. Empirical reports of real‑world P&D operations suggest a tranche‑based strategy:

Sell 20% of accumulated volume at 50% of the peak high price.

Sell 30% at 60% of the peak high price.

Sell 50% at 80% of the peak high price.

This approach balances extracting maximal profit against avoiding premature price collapse. To simplify calculations, and given our reliance on minute‑level data, we define two conservative unloading scenarios below to produce lower‑bound profit estimates.

### Methodology

Data Inputs:

Minute‑level OHLCV series for each event, spanning four days before to two days after the Target Date.

Accumulation start/end timestamps from Section [4](https://arxiv.org/html/2504.15790v1#S4 "4 Quantification of the Accumulation Phase ‣ Microstructure and Manipulation: Quantifying Pump-and-Dump Dynamics in Cryptocurrency Markets").

Step 1 - Purchase‑Price Proxies: We introduce two scenarios and estimate the profit in each case:

First‑Trade Proxy: Price at the first minute during which quantity >0absent0>0> 0 in the accumulation window.

VWAP Proxy: Volume‑weighted average price over all accumulation minutes:

|  |  |  |
| --- | --- | --- |
|  | VWAP=∑tPt⁢Vt∑tVtVWAPsubscript𝑡subscript𝑃𝑡subscript𝑉𝑡subscript𝑡subscript𝑉𝑡\mathrm{VWAP}\;=\;\frac{\sum\_{t}P\_{t}\,V\_{t}}{\sum\_{t}V\_{t}}roman\_VWAP = divide start\_ARG ∑ start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT italic\_P start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT italic\_V start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT end\_ARG start\_ARG ∑ start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT italic\_V start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT end\_ARG |  |

where Ptsubscript𝑃𝑡P\_{t}italic\_P start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT and Vtsubscript𝑉𝑡V\_{t}italic\_V start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT denote price and volume in minute t𝑡titalic\_t.

Step 2 - Liquidation Scenarios

*Single‑Point Liquidation:* Sell full volume V𝑉Vitalic\_V at

|  |  |  |
| --- | --- | --- |
|  | 0.70×H,0.70𝐻0.70\times H,0.70 × italic\_H , |  |

where H𝐻Hitalic\_H is the observed peak high price.

*Tranche Liquidation:* Sell

|  |  |  |
| --- | --- | --- |
|  | 0.20⁢V⁢at ⁢0.50⁢H,0.30⁢V⁢at ⁢0.60⁢H,0.50⁢V⁢at ⁢0.80⁢H.  0.20𝑉at 0.50𝐻0.30𝑉at 0.60𝐻0.50𝑉at 0.80𝐻0.20\,V\ \text{at }0.50\,H,\quad 0.30\,V\ \text{at }0.60\,H,\quad 0.50\,V\ % \text{at }0.80\,H.0.20 italic\_V at 0.50 italic\_H , 0.30 italic\_V at 0.60 italic\_H , 0.50 italic\_V at 0.80 italic\_H . |  |

Step 3 - Profit and Return Calculations

|  |  |  |  |
| --- | --- | --- | --- |
|  | Cost | =V×Pproxy,absent𝑉subscript𝑃proxy\displaystyle=V\times P\_{\text{proxy}},= italic\_V × italic\_P start\_POSTSUBSCRIPT proxy end\_POSTSUBSCRIPT , |  |
|  |  |  |  |
| --- | --- | --- | --- |
|  | ProceedssinglesubscriptProceedssingle\displaystyle\text{Proceeds}\_{\text{single}}Proceeds start\_POSTSUBSCRIPT single end\_POSTSUBSCRIPT | =V×(0.70⁢H),absent𝑉0.70𝐻\displaystyle=V\times(0.70\,H),= italic\_V × ( 0.70 italic\_H ) , |  |
|  |  |  |  |
| --- | --- | --- | --- |
|  | ProceedstranchesubscriptProceedstranche\displaystyle\text{Proceeds}\_{\text{tranche}}Proceeds start\_POSTSUBSCRIPT tranche end\_POSTSUBSCRIPT | =0.20⁢V×0.50⁢H+ 0.30⁢V×0.60⁢H+ 0.50⁢V×0.80⁢H,absent0.20𝑉0.50𝐻0.30𝑉0.60𝐻0.50𝑉0.80𝐻\displaystyle=0.20\,V\times 0.50\,H\;+\;0.30\,V\times 0.60\,H\;+\;0.50\,V% \times 0.80\,H,= 0.20 italic\_V × 0.50 italic\_H + 0.30 italic\_V × 0.60 italic\_H + 0.50 italic\_V × 0.80 italic\_H , |  |
|  |  |  |  |
| --- | --- | --- | --- |
|  | Profit | =Proceeds−Cost,absentProceedsCost\displaystyle=\text{Proceeds}-\text{Cost},= Proceeds - Cost , |  |
|  |  |  |  |
| --- | --- | --- | --- |
|  | Return% | =100×ProfitCost.absent100ProfitCost\displaystyle=100\times\frac{\text{Profit}}{\text{Cost}}.= 100 × divide start\_ARG Profit end\_ARG start\_ARG Cost end\_ARG . |  |

Step 4 - Sensitivity Analysis: For each scenario, we compute:

Mean and median absolute profits.

Mean and median percentage returns.

Distribution percentiles to assess variation.

Comparison across purchase‑price proxies and liquidation strategies.

|  |  |  |  |
| --- | --- | --- | --- |
|  | A𝐴\displaystyle Aitalic\_A | :P=P1,single at ⁢0.70⁢H,:absent𝑃  subscript𝑃1single at 0.70𝐻\displaystyle:P=P\_{1},\ \text{single at }0.70H,: italic\_P = italic\_P start\_POSTSUBSCRIPT 1 end\_POSTSUBSCRIPT , single at 0.70 italic\_H , |  |
|  |  |  |  |
| --- | --- | --- | --- |
|  | B𝐵\displaystyle Bitalic\_B | :P=P1,tranches ⁢[0.50⁢H,0.60⁢H,0.80⁢H],:absent𝑃  subscript𝑃1tranches   0.50𝐻0.60𝐻0.80𝐻\displaystyle:P=P\_{1},\ \text{tranches }[0.50H,0.60H,0.80H],: italic\_P = italic\_P start\_POSTSUBSCRIPT 1 end\_POSTSUBSCRIPT , tranches [ 0.50 italic\_H , 0.60 italic\_H , 0.80 italic\_H ] , |  |
|  |  |  |  |
| --- | --- | --- | --- |
|  | C𝐶\displaystyle Citalic\_C | :P=PVWAP,single at ⁢0.70⁢H,:absent𝑃  subscript𝑃VWAPsingle at 0.70𝐻\displaystyle:P=P\_{\mathrm{VWAP}},\ \text{single at }0.70H,: italic\_P = italic\_P start\_POSTSUBSCRIPT roman\_VWAP end\_POSTSUBSCRIPT , single at 0.70 italic\_H , |  |
|  |  |  |  |
| --- | --- | --- | --- |
|  | D𝐷\displaystyle Ditalic\_D | :P=PVWAP,tranches ⁢[0.50⁢H,0.60⁢H,0.80⁢H].:absent𝑃  subscript𝑃VWAPtranches   0.50𝐻0.60𝐻0.80𝐻\displaystyle:P=P\_{\mathrm{VWAP}},\ \text{tranches }[0.50H,0.60H,0.80H].: italic\_P = italic\_P start\_POSTSUBSCRIPT roman\_VWAP end\_POSTSUBSCRIPT , tranches [ 0.50 italic\_H , 0.60 italic\_H , 0.80 italic\_H ] . |  |

### Results

Table [3](https://arxiv.org/html/2504.15790v1#S5.T3 "Table 3 ‣ Results ‣ 5 Profit Estimation ‣ Microstructure and Manipulation: Quantifying Pump-and-Dump Dynamics in Cryptocurrency Markets") presents the average and median profit (absolute and percentage) across scenarios A–D. Although each pump event targets low‑priced, low‑liquidity tokens—limiting per‑event gains—the rapid proliferation and frequency of P&D operations imply substantial cumulative returns for organizers.

| ID | avg\_profit\_abs | median\_profit\_abs | avg\_profit\_pct | median\_profit\_pct |
| --- | --- | --- | --- | --- |
| A | 617.27 | 23.34 | 2642.78 | 126.70 |
| B | 587.64 | 20.86 | 2564.42 | 120.23 |
| C | 537.37 | 18.11 | 2187.23 | 97.67 |
| D | 507.73 | 15.65 | 2121.88 | 92.02 |

These findings align closely with our social‐media monitoring, where insiders actively broadcast pump announcements to grow channel membership and ensure sufficient participation. Without adequate buy‑in from subscribers, the organizers cannot realize any profit.

![Refer to caption](extracted/6380150/pump_results1.png)
![Refer to caption](extracted/6380150/pump_results2.png)

## 6 Conclusion

This study extends traditional pump‑and‑dump analysis by leveraging minute‑level market data to uncover the fine‑grained dynamics of insider accumulation and profit extraction. We demonstrate that accumulation is overwhelmingly concentrated within the final hour before each pump, justifying the adoption of sub‑hourly monitoring thresholds. Conservative profit modeling reveals that insiders routinely achieve median returns in excess of 100%, with extreme gains surpassing 2000%, underscoring the powerful economic drivers of these schemes. Moreover, the identification of two distinct archetypes—pre‑accumulation versus on‑the‑spot pumps—enables the design of differentiated detection algorithms and risk assessments. Going forward, integrating social‑media signal analysis and machine‑learning classifiers promises to enhance real‑time alert systems, empowering exchanges and regulators to more effectively deter manipulative activity in decentralized markets.

Declaration
This research did not receive any specific grant from funding agencies in the public, commercial, or not-for-profit sectors. The data used in this study were obtained from the free API provided by Poloniex exchange and are publicly accessible. The author declares no competing interests.

## References

![Mascot Sammy](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAsAAAAOCAYAAAD5YeaVAAAAAXNSR0IArs4c6QAAAAZiS0dEAP8A/wD/oL2nkwAAAAlwSFlzAAALEwAACxMBAJqcGAAAAAd0SU1FB9wKExQZLWTEaOUAAAAddEVYdENvbW1lbnQAQ3JlYXRlZCB3aXRoIFRoZSBHSU1Q72QlbgAAAdpJREFUKM9tkL+L2nAARz9fPZNCKFapUn8kyI0e4iRHSR1Kb8ng0lJw6FYHFwv2LwhOpcWxTjeUunYqOmqd6hEoRDhtDWdA8ApRYsSUCDHNt5ul13vz4w0vWCgUnnEc975arX6ORqN3VqtVZbfbTQC4uEHANM3jSqXymFI6yWazP2KxWAXAL9zCUa1Wy2tXVxheKA9YNoR8Pt+aTqe4FVVVvz05O6MBhqUIBGk8Hn8HAOVy+T+XLJfLS4ZhTiRJgqIoVBRFIoric47jPnmeB1mW/9rr9ZpSSn3Lsmir1fJZlqWlUonKsvwWwD8ymc/nXwVBeLjf7xEKhdBut9Hr9WgmkyGEkJwsy5eHG5vN5g0AKIoCAEgkEkin0wQAfN9/cXPdheu6P33fBwB4ngcAcByHJpPJl+fn54mD3Gg0NrquXxeLRQAAwzAYj8cwTZPwPH9/sVg8PXweDAauqqr2cDjEer1GJBLBZDJBs9mE4zjwfZ85lAGg2+06hmGgXq+j3+/DsixYlgVN03a9Xu8jgCNCyIegIAgx13Vfd7vdu+FweG8YRkjXdWy329+dTgeSJD3ieZ7RNO0VAXAPwDEAO5VKndi2fWrb9jWl9Esul6PZbDY9Go1OZ7PZ9z/lyuD3OozU2wAAAABJRU5ErkJggg==)
