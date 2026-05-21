# Machine Learning-Based Detection of Pump-and-Dump Schemes in Real-Time

###### Abstract

Cryptocurrency markets often face manipulation through prevalent pump-and-dump (P&D) schemes, where self-organized Telegram groups, some exceeding two million members, artificially inflate target cryptocurrency prices. These groups sell premium access to inside information, worsening information asymmetry and financial risks for subscribers and all investors. This paper presents a real-time prediction pipeline to forecast target coins and alert investors to possible P&D schemes. In a Poloniex case study, the model accurately identified the target coin among the top five from 50 random coins in 24 out of 43 (55.81%) P&D events. The pipeline uses advanced natural language processing (NLP) to classify Telegram messages, identifying 2,079 past pump events and detecting new ones in real-time. Our analysis also evaluates the susceptibility of token standards—ERC-20, ERC-721, BRC-20, Inscriptions, and Runes—to manipulation and identifies exchanges commonly involved in P&D schemes.

###### Index Terms:

## I Introduction

Blockchain is an immutable, decentralized ledger that eliminates the need for a central authority, enabling secure and transparent transactions. It facilitates the continuous tracking of ownership through digital tokens, which act as units of value. Tokens can store value, serve as participation rewards, provide voting rights, or enable interaction with products and services [[1](https://arxiv.org/html/2412.18848v1#bib.bib1), [2](https://arxiv.org/html/2412.18848v1#bib.bib2), [3](https://arxiv.org/html/2412.18848v1#bib.bib3)]. However, tokens are also susceptible to market manipulations, making their attributes critical to this study.

Cryptocurrency markets promise high returns and decentralized control but remain vulnerable to market manipulations like pump-and-dump (P&D) schemes. These schemes, orchestrated via messaging platforms such as Telegram and Discord, artificially inflate a cryptocurrency’s price, enabling organizers to profit at the expense of unsuspecting investors. A recent report by Chainalysis [[4](https://arxiv.org/html/2412.18848v1#bib.bib4)] revealed that 24% of tokens launched in 2022 exhibited characteristics typical of P&D schemes, underlining the systemic risks these activities pose to market integrity and the urgent need for effective detection and prevention mechanisms.

P&D schemes typically unfold in distinct phases: an initial announcement, a countdown to build anticipation and attract participants, and the final release of the target coin, which sparks a rapid price surge as traders rush to buy. This is immediately followed by a sell-off, where organizers and early participants offload their holdings at inflated prices, leaving latecomers with significant losses. The cycle often repeats, exploiting market vulnerabilities and undermining trust among investors, as depicted in the list below.

*Pump Announcement:* Formal announcements detailing the exchange, time, and date of the event.

*Countdown:* Reminders and promotional messages leading up to the pump event.

*Target Coin Release:* Disclosure of the target coin’s symbol, token contract, or trading pair link, often as text or images.

*Pump Results:* Summaries of the pump results, including profits and performance.

*Delay or Cancellation Notices:* Updates about postponed or canceled pumps.

*Noise:* Messages unrelated to the categories above.

Although traditional analysis of trading volume and token price can provide valuable indicators for the emergence of P&D schemes [[5](https://arxiv.org/html/2412.18848v1#bib.bib5)], recent advances in large language models (LLMs) [[6](https://arxiv.org/html/2412.18848v1#bib.bib6), [7](https://arxiv.org/html/2412.18848v1#bib.bib7), [8](https://arxiv.org/html/2412.18848v1#bib.bib8)] allow for better detection and understanding of these manipulations. LLMs enable detailed analysis of Telegram messages, often the primary medium through which P&D organizers communicate with participants. By extracting patterns and identifying key linguistic cues in these messages, LLMs can complement conventional market data analysis and offer a more comprehensive detection approach.

Additionally, the execution of P&D schemes on centralized cryptocurrency exchanges requires a sufficiently liquid and deep order book to accommodate the influx of trades and facilitate the artificial price rise. Analyzing order book depth and anomalies can provide critical insights into the preparatory activities of orchestrators, including potential insider trades and coordinated buy orders.

The introduction of new token standards, such as Ordinals [[9](https://arxiv.org/html/2412.18848v1#bib.bib9)], Inscriptions [[10](https://arxiv.org/html/2412.18848v1#bib.bib10)], and Runes [[11](https://arxiv.org/html/2412.18848v1#bib.bib11), [12](https://arxiv.org/html/2412.18848v1#bib.bib12), [13](https://arxiv.org/html/2412.18848v1#bib.bib13)], on Bitcoin, further complicates the landscape of P&D schemes. These standards spread to the EVM-chains [[14](https://arxiv.org/html/2412.18848v1#bib.bib14)], raising questions about the susceptibility of tokens beyond the widely targeted ERC-20 standard on Ethereum and other EVM-compatible chains. While ERC-20 tokens have historically been prime targets due to their widespread adoption and ease of trading, understanding whether and how emerging standards are exploited is crucial for developing holistic anti-manipulation strategies.

By integrating advanced NLP techniques, market data analysis, and an understanding of evolving token standards, this study provides new contributions to the detection and prevention of P&D schemes, offering a novel framework for safeguarding cryptocurrency markets against manipulation.

### Related Work

Early studies on P&D schemes focused on identifying price and volume anomalies after pumps occurred [[5](https://arxiv.org/html/2412.18848v1#bib.bib5)], achieving moderate success but underscoring the need for more sophisticated models. Real-time detection approaches, such as anomaly detection using machine learning [[15](https://arxiv.org/html/2412.18848v1#bib.bib15)], have shown promise but suffer from latency issues, as seen in the 30-minute lag of certain methods [[16](https://arxiv.org/html/2412.18848v1#bib.bib16)]. More recent methods [[17](https://arxiv.org/html/2412.18848v1#bib.bib17)] leverage Random Forest and AdaBoost classifiers to detect anomalies within seconds of pump initiation.

Target coin prediction aims to identify manipulated coins before a pump. Xu et al. [[18](https://arxiv.org/html/2412.18848v1#bib.bib18)] developed Random Forest models to predict pump likelihood using market metrics, while Hu et al. [[19](https://arxiv.org/html/2412.18848v1#bib.bib19)] introduced sequence-based deep-learning models leveraging channel-specific features. Despite advancements, existing approaches largely rely on historical data and lack integration of high-frequency order book data, limiting their real-time applicability.

### Contributions

This paper addresses the limitations of existing methods by introducing a cross-exchange, real-time pipeline for detecting P&D schemes before they occur. Our contributions include:

Incorporating high-frequency order book and trade data alongside Telegram messages monitoring to enhance prediction accuracy.

Developing a Z-score-based model, which can forecast target coins mere seconds prior to pump events, achieving correct predictions among the top five ranked coins in 55.81% of cases and within the top ten in 74.42% of instances.

Evaluating the susceptibility of emerging token standards like BRC-20 and Runes to P&D schemes.

By providing an early warning system, this framework aims to mitigate market manipulation risks and promote safer trading environments.

### Paper Organization

The paper is structured as follows: Section [II](https://arxiv.org/html/2412.18848v1#S2 "II Background ‣ Machine Learning-Based Detection of Pump-and-Dump Schemes in Real-Time") introduces the relevant token standards. Section [III](https://arxiv.org/html/2412.18848v1#S3 "III Pipeline System Architecture ‣ Machine Learning-Based Detection of Pump-and-Dump Schemes in Real-Time") presents the pipeline system architecture for real-time prediction of P&D schemes, Section [IV](https://arxiv.org/html/2412.18848v1#S4 "IV Data Collection and Methodology ‣ Machine Learning-Based Detection of Pump-and-Dump Schemes in Real-Time") details the data collection process. Empirical results are presented in Section [V](https://arxiv.org/html/2412.18848v1#S5 "V Empirical Results ‣ Machine Learning-Based Detection of Pump-and-Dump Schemes in Real-Time"), followed by a discussion in Section [VI](https://arxiv.org/html/2412.18848v1#S6 "VI Discussion ‣ Machine Learning-Based Detection of Pump-and-Dump Schemes in Real-Time"), and conclusions in Section [VII](https://arxiv.org/html/2412.18848v1#S7 "VII Conclusion ‣ Machine Learning-Based Detection of Pump-and-Dump Schemes in Real-Time").

## II Background

To provide context for this research, we begin with a concise introduction to various token standards.

#### II-1 ERC-20

ERC-20 is a widely adopted standard for fungible tokens on Ethereum, enabling interoperability across decentralized applications (dApps). Tokens under this standard can represent anything from assets to utility tokens, facilitating broad use cases [[20](https://arxiv.org/html/2412.18848v1#bib.bib20), [21](https://arxiv.org/html/2412.18848v1#bib.bib21)]. BEP-20, a similar standard on Binance Smart Chain, offers lower transaction fees and congestion, enhancing its appeal [[22](https://arxiv.org/html/2412.18848v1#bib.bib22)].

#### II-2 ERC-721

ERC-721 defines a standard for non-fungible tokens (NFTs), which are unique and indivisible. NFTs enable the representation of ownership for digital assets like art and collectibles, ensuring their provenance and authenticity through blockchain’s immutable records [[23](https://arxiv.org/html/2412.18848v1#bib.bib23), [24](https://arxiv.org/html/2412.18848v1#bib.bib24)].

#### II-3 Ordinals and Inscriptions

Ordinals enable individual satoshis to carry unique identifiers, granting them subjective value based on collector sentiment [[9](https://arxiv.org/html/2412.18848v1#bib.bib9)]. Inscriptions enhance this concept by attaching data like images or text to satoshis, transforming them into unique digital artifacts that can be traded [[25](https://arxiv.org/html/2412.18848v1#bib.bib25)].

#### II-4 BRC-20

The BRC-20 standard introduces fungible tokens on Bitcoin, leveraging the Ordinals protocol to inscribe metadata onto satoshis. While BRC-20 enables token creation and transfer, its programmability is limited compared to Ethereum-based standards [[10](https://arxiv.org/html/2412.18848v1#bib.bib10)]. This simplicity highlights its experimental nature, relying on off-chain tools for effective tracking and management.

#### II-5 Runes

Runes embed fungible tokens directly into Bitcoin’s UTXO system, allowing for efficient token creation, minting, and transfer. The protocol ensures integrity through a burning mechanism for invalid transactions and maintains a smaller on-chain footprint, addressing scalability concerns [[11](https://arxiv.org/html/2412.18848v1#bib.bib11), [12](https://arxiv.org/html/2412.18848v1#bib.bib12), [13](https://arxiv.org/html/2412.18848v1#bib.bib13)].

By exploring these token standards, this research provides insights into the attributes that make certain tokens more vulnerable to P&D schemes.

## III Pipeline System Architecture

![Refer to caption](extracted/6094758/Figures/data_pipeline_new.jpg)

Figure [1](https://arxiv.org/html/2412.18848v1#S3.F1 "Figure 1 ‣ III Pipeline System Architecture ‣ Machine Learning-Based Detection of Pump-and-Dump Schemes in Real-Time") illustrates the architecture of our detection pipeline system that is designed to monitor, integrate and analyze data streams in real-time to detect P&D schemes effectively. This pipeline is fully operational and deployed on the cloud infrastructure. It comprises three main components.

##### Telegram Message Processing

The system actively monitors Telegram channels, continuously classifying incoming messages into six distinct categories that correspond to different phases of P&D schemes. By employing advanced natural language processing (NLP) techniques, the model efficiently identifies announcements related to upcoming events. These classified messages are stored in a PostgreSQL database, serving as the primary trigger for subsequent stages of the pipeline.

##### Data Integration

To complement the Telegram data, the pipeline incorporates high-frequency market data, including order book and trade data, sourced from multiple exchanges such as LATOKEN, KuCoin, MEXC, Poloniex, and XT.com. Covering approximately 4,400 coins, this module processes data streams alongside market indicators to compute essential metrics. These metrics enable the pipeline to track market movements and identify suspicious patterns in real-time, ensuring comprehensive and dynamic monitoring.

##### Target Coin Prediction

The final stage of the pipeline predicts the coin most likely to be targeted in a P&D scheme. This is achieved through a two-step process. Initially, the set of candidate coins is narrowed down using a filter based on historical market capitalization data. Subsequently, a statistical anomaly detection model, leveraging Z-scores, calculates the likelihood of each coin being pumped. This process generates a ranked list of potential target coins. In a case study involving 43 pump events on Poloniex, the system accurately identified the pumped coin within the top five predictions in 55.81% of cases (24 out of 43 events), showcasing the pipeline’s precision and real-time effectiveness.

The detection pipeline system is hosted on the cloud infrastructure, leveraging multiple virtual machines with 8 GB of memory and 160 GB of disk space to handle high-frequency processing from multiple cryptocurrency exchanges. Data is stored in a PostgreSQL database, which, as of October, 2024, contains over 91,295 labeled and processed Telegram messages. This database is continuously updated to reflect ongoing P&D schemes.

## IV Data Collection and Methodology

| Data Source | Details |
| --- | --- |
| TGstats | 43 active Telegram channels identified for P&D events. |
| Telegram | 91,295 P&D messages (growing); data from 2017-12-02 to 2024-10-21. |
| LunarCrush | Social media metrics for cryptocurrencies. |
| CoinMarketCap | Market caps and token metadata. |
| CoinCodex | Historical market caps for 3,958 unpumped and 924 pumped coins (2018-01-01 to 2024-07-01). |
| CEXs (e.g., KuCoin, Poloniex) | Daily OHLCV data for 4,643 cryptocurrencies (365,982 rows) from 2024-07-01 to 2024-10-21. |
| CEXs (e.g., KuCoin, Poloniex) | Order book data (5–44M rows) and trade data (2–5M rows per exchange) from 2024-07-01 to 2024-10-21. |

The pipeline incorporates 365,982 rows of daily OHLCV (open, high, low, close, volume) price data, social metrics, and market capitalization data for 4,643 cryptocurrencies. Additionally, it stores between 5 and 44 million rows of order book metrics and between 2 and 5 million rows of trade metrics per exchange. These metrics, crucial for target coin prediction, are calculated and updated every few seconds. Table [I](https://arxiv.org/html/2412.18848v1#S4.T1 "TABLE I ‣ IV Data Collection and Methodology ‣ Machine Learning-Based Detection of Pump-and-Dump Schemes in Real-Time") presents a comprehensive overview of these data sources, which are elaborated upon in this section. Data was collected from 30 days up to 1 hour before each pump event.

### IV-A Pump Message Collection

Previous studies on target coin prediction [[18](https://arxiv.org/html/2412.18848v1#bib.bib18)] primarily relied on data from the now-defunct PumpOlymp111PumpOlymp was previously active under https://pumpolymp.com/ website to identify pump channels on Telegram. In the absence of a comparable successor, we utilized TGStats [[26](https://arxiv.org/html/2412.18848v1#bib.bib26)] to search for specific keywords within channel titles and descriptions, including crypto, pump, dump, P&D, and signal, along with their combinations. Identified channels were manually validated for active promotion of P&D schemes, resulting in the identification of 43 active channels. From these, we extracted complete message histories, creating a dataset currently comprising 91,295 messages. Telegram was chosen as the primary focus, as previous studies have established its role as the main platform for P&D activities [[18](https://arxiv.org/html/2412.18848v1#bib.bib18)].

### IV-B Pump Message Labeling

Manual examination of the collected messages revealed six distinct categories of P&D-related messages, aligned with the pump anatomy described in Section [I](https://arxiv.org/html/2412.18848v1#S1 "I Introduction ‣ Machine Learning-Based Detection of Pump-and-Dump Schemes in Real-Time").
The dataset was preprocessed to normalize characters, spaces, and emojis. User-tags were replaced with the generic token @USER, and non-informative URLs were replaced with UNKNOWN\_URL. A list of prominent centralized exchanges (CEXs), decentralized exchanges (DEXs), and defunct platforms such as HotBit and Cryptopia was compiled to tag messages mentioning exchanges with special tokens (\_CEX or \_DEX).

To automate P&D detection, we labeled approximately 25% (21,092 messages) of the dataset across the six categories using the GPT-4o model via the OpenAI API. Detailed prompts and parameter settings are available in Appendix [A-A](https://arxiv.org/html/2412.18848v1#A1.SS1 "A-A OpenAI Settings and Prompts ‣ Appendix A Appendix: Natural Language Processing ‣ Machine Learning-Based Detection of Pump-and-Dump Schemes in Real-Time"). Manual verification and re-labeling were performed to enhance label accuracy, focusing on critical classes: Pump Announcement, Countdown, Target Coin Release, and Delay/Cancellation. Only a small number of messages required re-labeling, demonstrating the reliability of GPT-4o as a baseline model.

|  |  |
| --- | --- |
| Label | Count |
| Pump Announcement | 1,184 |
| Countdown | 11,321 |
| Target Coin Release | 1,151 |
| Pump Results | 1,722 |
| Delay/Cancellation | 98 |
| Noise | 5,616 |
| Total | 21,092 |

The labeled data was used to fine-tune a BERTweet [[27](https://arxiv.org/html/2412.18848v1#bib.bib27)] model. Table [II](https://arxiv.org/html/2412.18848v1#S4.T2 "TABLE II ‣ IV-B Pump Message Labeling ‣ IV Data Collection and Methodology ‣ Machine Learning-Based Detection of Pump-and-Dump Schemes in Real-Time") summarizes the label distribution after cleaning. To address label imbalance, a weighted loss function was applied during training. The dataset was split into 80% for training and 20% for validation and testing. Duplicate messages, commonly reused across channels (e.g., ”1 HOUR UNTIL THE PUMP…”), were excluded from the test set to ensure unbiased evaluation metrics. The performance of the model is included in Appendix in Table [VI](https://arxiv.org/html/2412.18848v1#A0.T6 "TABLE VI ‣ Figure 7 ‣ -A Additional Figures and Tables ‣ Machine Learning-Based Detection of Pump-and-Dump Schemes in Real-Time").

The model was then used to predict labels for the remaining messages. From the labeled message history, we identified 2,079 distinct pump events by clustering messages based on token symbol, exchange, and the timestamp of the Target Coin Release, rounded to the nearest hour. For channels disclosing target coins via images, we manually extracted the corresponding symbols. This occurred for only three channels in the sample.

### IV-C Market Data

We analyze 365,982 rows of daily OHLCV data for 4,643 cryptocurrencies, including price, trading volume, and market capitalization metrics critical for identifying P&D targets. Data is collected via API calls to exchanges such as KuCoin and MEXC, supplemented by the CCXT library [[28](https://arxiv.org/html/2412.18848v1#bib.bib28)], and automated through a daily cron job. Preprocessed data is stored in a database and used in filter models for predictive analysis.

Challenges in historical data accuracy arose due to non-unique coin symbols and missing data for 403 of the 1,045 unique symbols, often due to delistings or defunct exchanges. To address this, our real-time pipeline incorporates self-reported market capitalization data from CoinMarketCap [[29](https://arxiv.org/html/2412.18848v1#bib.bib29)].
Additionally, derivative tokens, such as leveraged and inverse tokens, were excluded using a pattern-matching approach, ensuring that only primary cryptocurrencies were considered.

### IV-D Social Data

Social sentiment significantly impacts cryptocurrency prices [[30](https://arxiv.org/html/2412.18848v1#bib.bib30)]. Using the LunarCrush API [[31](https://arxiv.org/html/2412.18848v1#bib.bib31)], we collect metrics such as likes, shares, and social dominance. Features such as rolling interaction means and social dominance ratios are engineered to explore correlations with market trends.

### IV-E Order Book Data

Real-time order book data offers early indicators of market manipulation. Metrics such as bid-ask spread, order size, and imbalance ratios are calculated from WebSocket feeds focused on USDT pairs flagged as vulnerable to P&D schemes.

### IV-F Trade Data

Trade data provides a historical record of executed transactions, revealing actual market behavior. Metrics such as trade volume, VWAP, and taker side volume help differentiate buy and sell pressures.
Integrating trade data enhances the pipeline’s predictive accuracy by capturing a complete view of market activity.

### IV-G Target Coin Normalization

Our Z-score-based statistical model leverages historical and short-term data from order book and trade metrics to identify market configurations indicative of impending P&D schemes. By analyzing patterns such as unusual sell orders or anomalous buy trades, the model aims to detect signs of organizers accumulating positions prior to a pump and placing sell orders to realize profits during the event.

The model processes data from a three-day window leading up to each pump event for all filtered coins on the exchange. Key metrics include order book pressure, average order size, order imbalance ratio, market order impact, volume-weighted average price (VWAP), high-low spread, and trade count. For each coin, Z-scores are calculated to compare short-term market behavior against historical averages, quantifying deviations from usual activity. The Z-score formula is:

|  |  |  |
| --- | --- | --- |
|  | zi=xi−μσsubscript𝑧𝑖subscript𝑥𝑖𝜇𝜎z\_{i}=\frac{x\_{i}-\mu}{\sigma}italic\_z start\_POSTSUBSCRIPT italic\_i end\_POSTSUBSCRIPT = divide start\_ARG italic\_x start\_POSTSUBSCRIPT italic\_i end\_POSTSUBSCRIPT - italic\_μ end\_ARG start\_ARG italic\_σ end\_ARG |  |

where zisubscript𝑧𝑖z\_{i}italic\_z start\_POSTSUBSCRIPT italic\_i end\_POSTSUBSCRIPT is the Z-score of the i𝑖iitalic\_i-th observation, xisubscript𝑥𝑖x\_{i}italic\_x start\_POSTSUBSCRIPT italic\_i end\_POSTSUBSCRIPT is the short-term metric value, μ𝜇\muitalic\_μ is the historical mean, and σ𝜎\sigmaitalic\_σ is the historical standard deviation. The resulting Z-scores are normalized and ranked, providing an estimate of a coin being targeted for a pump.

##### Backtesting and Results

We evaluated the model on 43 P&D events using trade and order book data from the Poloniex API. For each event, the dataset included data for the pumped coin and a random sample of 50 coins. Figure [7](https://arxiv.org/html/2412.18848v1#A0.F7 "Figure 7 ‣ -A Additional Figures and Tables ‣ Machine Learning-Based Detection of Pump-and-Dump Schemes in Real-Time") illustrates the distribution of ranks for pumped coins based on Z-scores. When the model was run 20 seconds before the pump, the pumped coin ranked within the top five (TOP5) in 55.81% of cases and within the top 10 (TOP10) in 74.42%. Using only trade data, these percentages dropped to 46.51% and 55.81%, respectively. For order book data alone, the TOP5 and TOP10 performances were 44.19% and 72.09%.

![Refer to caption](extracted/6094758/Figures/eval_pd_pumps.png)

Figure [2](https://arxiv.org/html/2412.18848v1#S4.F2 "Figure 2 ‣ Backtesting and Results ‣ IV-G Target Coin Normalization ‣ IV Data Collection and Methodology ‣ Machine Learning-Based Detection of Pump-and-Dump Schemes in Real-Time") visualizes the relative Z-scores across all coins for each pump event, with the pumped coins highlighted. This demonstrates the model’s ability to distinguish pumped coins based on their Z-scores.

##### Performance Over Different Time Offsets

We tested the model at time offsets of 20 seconds, 40 seconds, and 1 minute before the pump. As shown in Table [III](https://arxiv.org/html/2412.18848v1#S4.T3 "TABLE III ‣ Performance Over Different Time Offsets ‣ IV-G Target Coin Normalization ‣ IV Data Collection and Methodology ‣ Machine Learning-Based Detection of Pump-and-Dump Schemes in Real-Time"), TOP5 and TOP10 performances declined with increasing time offsets, highlighting the importance of near-real-time predictions. When using both trade and order book data, the TOP5 performance decreased from 55.81% (20 seconds) to 19.05% (1 minute). Similarly, using only trade data, TOP5 performance dropped from 46.51% to 9.52%.

| Time Offset | Trade and Order Book Data | | Trade Data Only | | Order Book Data Only | |
| --- | --- | --- | --- | --- | --- | --- |
|  | TOP5 | TOP10 | TOP5 | TOP10 | TOP5 | TOP10 |
| 20 seconds | 55.81% | 74.42% | 46.51% | 55.81% | 44.19% | 72.09% |
| 40 seconds | 41.46% | 60.98% | 29.27% | 36.59% | 41.46% | 60.98% |
| 1 minute | 19.05% | 28.57% | 9.52% | 11.90% | 16.67% | 30.95% |

The Z-score model effectively identifies target coins shortly before P&D events, with combined trade and order book data yielding the best results. However, its predictive power diminishes as the time offset increases, emphasizing the need for real-time data processing in operational pipelines.

## V Empirical Results

First, the model labeled messages and extracted details such as pump times, exchanges, and target coins. This yielded a dataset of 2,079 P&D events between December 2017 and September 2024. As shown in Table [VIII](https://arxiv.org/html/2412.18848v1#A0.T8 "TABLE VIII ‣ Figure 7 ‣ -A Additional Figures and Tables ‣ Machine Learning-Based Detection of Pump-and-Dump Schemes in Real-Time"), most events occurred on centralized exchanges (CEX), with Hotbit leading despite ceasing operations in May 2023. Recent activity has shifted to LATOKEN, XT, and Poloniex, as illustrated in Figure [3](https://arxiv.org/html/2412.18848v1#S5.F3 "Figure 3 ‣ V Empirical Results ‣ Machine Learning-Based Detection of Pump-and-Dump Schemes in Real-Time").

![Refer to caption](extracted/6094758/Figures/stacked_bar_plot_all.jpg)

### V-A Quantification of P&D Schemes and Target Coins

![Refer to caption](extracted/6094758/Figures/mcap_price_vol_per_channel.png)

We analyzed market cap and price data from CoinCodex [[32](https://arxiv.org/html/2412.18848v1#bib.bib32)] for pumped coins. Supplementary Figure [4](https://arxiv.org/html/2412.18848v1#S5.F4 "Figure 4 ‣ V-A Quantification of P&D Schemes and Target Coins ‣ V Empirical Results ‣ Machine Learning-Based Detection of Pump-and-Dump Schemes in Real-Time") in Appendix highlights that most pumped coins belong to the small- and mid-cap categories.
Many coins were targeted multiple times, with some becoming frequent targets. Table [VII](https://arxiv.org/html/2412.18848v1#A0.T7 "TABLE VII ‣ Figure 7 ‣ -A Additional Figures and Tables ‣ Machine Learning-Based Detection of Pump-and-Dump Schemes in Real-Time") in Appendix lists the five most pumped coins, led by TOKKI, which was pumped nine times across four exchanges by five different channels.

#### V-A1 Volume

Our analysis reveals a significant impact of pump events on the trade volumes of targeted coins. Supplementary Figures [13](https://arxiv.org/html/2412.18848v1#A0.F13 "Figure 13 ‣ -A Additional Figures and Tables ‣ Machine Learning-Based Detection of Pump-and-Dump Schemes in Real-Time") and [13](https://arxiv.org/html/2412.18848v1#A0.F13 "Figure 13 ‣ -A Additional Figures and Tables ‣ Machine Learning-Based Detection of Pump-and-Dump Schemes in Real-Time") in Appendix illustrate the average daily trade volumes for approximately 700 pump events on KuCoin and Poloniex over an eight-day period, with the eighth day representing the pump event. The substantial increase in trade volume on the pump day compared to a typical trading day is strikingly evident.

While KuCoin exhibits higher absolute volumes on the pump day (approximately $1.86 million) compared to Poloniex ($4,800), the relative increase in trade volume is greater on Poloniex. Specifically, the ratio of the pump day volume to the day before the pump is approximately 62.562.562.562.5 for Poloniex (4809/774809774809/774809 / 77) versus 23.223.223.223.2 for KuCoin (1867411/806411867411806411867411/806411867411 / 80641), suggesting that pump events have a more pronounced relative impact on smaller exchanges.

We further analyzed average trade volumes grouped by the Telegram channels orchestrating these pump events. Supplementary Figures [13](https://arxiv.org/html/2412.18848v1#A0.F13 "Figure 13 ‣ -A Additional Figures and Tables ‣ Machine Learning-Based Detection of Pump-and-Dump Schemes in Real-Time") and [13](https://arxiv.org/html/2412.18848v1#A0.F13 "Figure 13 ‣ -A Additional Figures and Tables ‣ Machine Learning-Based Detection of Pump-and-Dump Schemes in Real-Time") in Appendix highlight the variation in trade volume increases across different channels on the pump day.
Interestingly, the observed variations cannot be solely attributed to easily measurable factors such as the number of subscribers per channel. This indicates that additional, less apparent factors play a role in determining the magnitude of a pump event’s impact.

#### V-A2 Price Spikes

Figures [6](https://arxiv.org/html/2412.18848v1#S5.F6 "Figure 6 ‣ V-A2 Price Spikes ‣ V-A Quantification of P&D Schemes and Target Coins ‣ V Empirical Results ‣ Machine Learning-Based Detection of Pump-and-Dump Schemes in Real-Time") and [6](https://arxiv.org/html/2412.18848v1#S5.F6 "Figure 6 ‣ V-A2 Price Spikes ‣ V-A Quantification of P&D Schemes and Target Coins ‣ V Empirical Results ‣ Machine Learning-Based Detection of Pump-and-Dump Schemes in Real-Time") illustrate the relative, normalized price changes during pump events on KuCoin (approximately 700 events) and Poloniex (approximately 200 events), capturing a 20-minute window spanning ten minutes before to ten minutes after the start of each event.

![Refer to caption](extracted/6094758/Figures/relative_price_changes_kucoin.png)
![Refer to caption](extracted/6094758/Figures/relative_price_changes_poloniex.png)

On average, the time to reach the maximum price spike was calculated at 1.49 minutes for KuCoin and just 0.12 minutes for Poloniex. The magnitude of the price spikes, measured relative to a baseline (the midpoint between the bid and ask prices ten minutes prior to the pump), was notably higher on Poloniex (10.85) compared to KuCoin (4.57). These results suggest that pumps on Poloniex not only reach their peak more quickly but also result in larger relative price spikes.
This difference aligns with the observations from supplementary Figures [13](https://arxiv.org/html/2412.18848v1#A0.F13 "Figure 13 ‣ -A Additional Figures and Tables ‣ Machine Learning-Based Detection of Pump-and-Dump Schemes in Real-Time") and [13](https://arxiv.org/html/2412.18848v1#A0.F13 "Figure 13 ‣ -A Additional Figures and Tables ‣ Machine Learning-Based Detection of Pump-and-Dump Schemes in Real-Time") that show lower trading volumes and liquidity on Poloniex. Limited market depth and lower liquidity make it easier to induce extreme price fluctuations, leading to shorter-lived but sharper price spikes during pump events.

#### V-A3 Order Size

Order size provides valuable insights into trader behavior during pump events, shedding light on patterns such as early positioning, cautious trading, and aggressive buying. Analyzing the average order sizes across different coins and exchanges reveals distinct behaviors and strategies.

On KuCoin, selected coins exhibit varying trends in order size during pump events. As shown in Table [IV](https://arxiv.org/html/2412.18848v1#S5.T4 "TABLE IV ‣ V-A3 Order Size ‣ V-A Quantification of P&D Schemes and Target Coins ‣ V Empirical Results ‣ Machine Learning-Based Detection of Pump-and-Dump Schemes in Real-Time"), KOL has the largest average order size before the pump, suggesting early trader positioning in anticipation of the event. Conversely, KPOL displays a significant increase in average order size during the pump, with an increase ratio of 1.30, indicating heightened interest and aggressive buying activity. IZI, pumped twice, shows a consistent decline in order size during the pump, likely due to profit-taking or cautious trading, as traders place smaller orders to mitigate risks in volatile conditions.

| Symbol | Avg Order Size (7 Days) | Avg Order Size (Pump Day) | Order Size Increase Ratio |
| --- | --- | --- | --- |
| AIEPK | 2257.07 | 2203.07 | 0.98 |
| IZI | 2199.62 | 752.08 | 0.35 |
| IZI | 2662.44 | 2130.59 | 0.80 |
| KOL | 4202.19 | 3471.90 | 0.83 |
| KPOL | 1750.89 | 2270.19 | 1.30 |
| MTS | 704.36 | 665.11 | 0.94 |

On Poloniex, market behavior during pump events is notably more volatile. Table [V](https://arxiv.org/html/2412.18848v1#S5.T5 "TABLE V ‣ V-A3 Order Size ‣ V-A Quantification of P&D Schemes and Target Coins ‣ V Empirical Results ‣ Machine Learning-Based Detection of Pump-and-Dump Schemes in Real-Time") highlights varied trends, with some coins displaying large order sizes before the pump, indicative of early positioning, while others experience sharp increases during the pump, reflecting sudden trader interest. For example, AMC shows inconsistent behavior, with stable order sizes in one instance and a dramatic increase in another, suggesting unpredictable trader dynamics. DMT and GFT demonstrate cautious trading, with declines in order size during the pump. Many coins on Poloniex experience periods of inactivity, signaling market hesitation or uncertainty leading up to the pump.

| Symbol | Avg Order Size (7 Days) | Avg Order Size (Pump Day) | Order Size Increase Ratio |
| --- | --- | --- | --- |
| AMC | 51.69 | 49.05 | 0.95 |
| AMC | 20.90 | 198.87 | 9.51 |
| COLLAB | 914.13 | 884.18 | 0.97 |
| DMT | 182.67 | 149.85 | 0.82 |
| GFT | 37.24 | 529.65 | 14.03 |
| GFT | 296.42 | 214.56 | 0.72 |
| GFT | 808.65 | 775.09 | 0.96 |

Supplementary Figures [13](https://arxiv.org/html/2412.18848v1#A0.F13 "Figure 13 ‣ -A Additional Figures and Tables ‣ Machine Learning-Based Detection of Pump-and-Dump Schemes in Real-Time") and [13](https://arxiv.org/html/2412.18848v1#A0.F13 "Figure 13 ‣ -A Additional Figures and Tables ‣ Machine Learning-Based Detection of Pump-and-Dump Schemes in Real-Time") in Appendix visualize the differences in average order sizes across both exchanges. KuCoin exhibits more predictable patterns, with traders often positioning themselves ahead of pump events, as seen with KOL. In contrast, Poloniex shows greater variability, with some coins like COLLAB maintaining consistent order sizes, while others, such as AMC and GFT, demonstrate dramatic fluctuations during the pump.

### V-B Filter Models to Reduce the Candidate Pool

Cryptocurrency exchanges often list thousands of tokens, creating significant scalability challenges for real-time tracking. For instance, MEXC lists 2,738 tokens [[33](https://arxiv.org/html/2412.18848v1#bib.bib33)]. To manage this complexity, our pipeline calculates and stores only order book and trade features in real-time, avoiding the need to store raw data. However, to further reduce the number of tokens tracked, we developed filter models to eliminate coins that lack the attributes commonly associated with pumped tokens.

Our filtering approach used a simple rule-based model to identify tokens within a specific market capitalization range. This range, spanning from 0 (unreported) to 60 million USD, targets lower market cap coins that are more vulnerable to price manipulation. As shown in Figure [4](https://arxiv.org/html/2412.18848v1#S5.F4 "Figure 4 ‣ V-A Quantification of P&D Schemes and Target Coins ‣ V Empirical Results ‣ Machine Learning-Based Detection of Pump-and-Dump Schemes in Real-Time"), the median market capitalization of pumped tokens is 2.7 million USD, with 95.7% of the 1,431 historical pumped coins falling within this range.

## VI Discussion

### VI-A Interpretation of Empirical Results

The Z-score prediction model shows strong potential in predicting target coins for P&D events, particularly when applied shortly before the pump. In our backtests, the target coin ranked within the top five by Z-score in 55.81% of cases and within the top ten in 74.42% when run 20 seconds prior to the event. However, performance declined significantly as the lead time increased, with TOP5 accuracy dropping to 41.45% at 40 seconds and 19.05% at 1 minute before the event. This suggests that critical trades or orders often occur just before the pump, making early detection more difficult.
Combining trade and order book data significantly improved the model’s performance, with a TOP5 accuracy of 55.81% when using both, compared to 46.51% with only trade data and 44.19% with only order book data. This underscores the importance of leveraging complementary data sources for a more complete view of pre-pump market activity.

#### Limitations and Challenges

The model’s declining performance with increased lead time highlights its reliance on late-stage market signals. Detectable anomalies in trade and order book data typically emerge shortly before the target coin is announced, limiting the model’s ability to predict pumps well in advance. This reflects the orchestrators’ strategy of placing key orders just before publicizing the pump, creating a narrow window for detection.
Data sparsity also posed challenges, as many coins on Poloniex exhibit minimal or no activity. This sometimes reduced the comparison pool to fewer than 50 coins, potentially inflating the model’s performance by making it statistically easier for the target coin to rank higher. While this limitation may have biased results in cases with sparse data, the model’s consistent performance in datasets with more active coins remains promising.

#### Potential Improvements and Future Research

Future iterations could benefit from integrating on-chain transaction data, as P&D organizers often transfer liquidity from other exchanges to the pump’s target platform. Monitoring large or suspicious deposits into the target exchange could serve as an early warning signal.
If on-chain data is unavailable, expanding the analysis to include multiple exchanges could improve detection capabilities, albeit with increased computational demands. Additionally, incorporating broader market indicators, such as social media sentiment and external events, could enhance early detection accuracy.
Addressing data sparsity through a more robust comparison pool is another priority. Techniques such as jump analysis [[34](https://arxiv.org/html/2412.18848v1#bib.bib34)] or fine-tuning time series transformer models [[35](https://arxiv.org/html/2412.18848v1#bib.bib35)] could further refine anomaly detection. Leveraging pretrained time series models with labeled datasets (see Appendix [E-A](https://arxiv.org/html/2412.18848v1#A5.SS1 "E-A Lag-Llama ‣ Appendix E Appendix: Further Suggestions for Future Work ‣ Machine Learning-Based Detection of Pump-and-Dump Schemes in Real-Time")) offers another promising avenue for improvement.

### VI-B Susceptibility of Token Standards for P&D Schemes

This section presents how various token standards influence their susceptibility to P&D schemes. By analyzing the implementation of non-fungible token standards such as ERC-721 [[24](https://arxiv.org/html/2412.18848v1#bib.bib24)] with fungible token standards like ERC-20 [[21](https://arxiv.org/html/2412.18848v1#bib.bib21)] and Runes [[11](https://arxiv.org/html/2412.18848v1#bib.bib11)], we assessed how their properties allow or prevent from being exploited.

#### VI-B1 Non-Fungible Token Standards

Non-fungible token (NFT) standards, such as ERC-721 tokens and Inscriptions [[25](https://arxiv.org/html/2412.18848v1#bib.bib25)], are generally unsuitable for P&D schemes. NFTs are unique and often linked to a specific digital or physical asset, making them incompatible with the mass trading needed for P&D events. Unlike fungible tokens, where multiple parties can hold large quantities simultaneously, only one entity can own an NFT at any given time.

Executing a P&D scheme for NFTs would require orchestrators to resell the same token multiple times at progressively higher prices, which is logistically challenging and impractical. Such schemes would involve significant coordination, high gas fees, and blockchain congestion. Moreover, insider trading—common in P&D schemes—would be nearly impossible, as orchestrators cannot acquire and hold unique tokens in advance for a mass sale.

Additionally, certain operational barriers exist for trading NFTs like Inscriptions, which require the ”ord” client and a fully synchronized Bitcoin node [[36](https://arxiv.org/html/2412.18848v1#bib.bib36)]. Supporting this analysis, our historical dataset revealed no instances of NFTs being targeted in P&D schemes. Telegram channels and marketplaces for NFTs, such as OpenSea and Magic Eden, lack any signs of coordinated P&D activity.
Fragmented ownership of NFTs, which enables shared liquidity, might create conditions more conducive to P&D schemes. While not observed in our data, other manipulation tactics, such as wash trading—where the same entity repeatedly buys and sells an NFT to inflate its price—are more likely in the NFT space.

#### VI-B2 Fungible Token Standards

In contrast to NFTs, fungible tokens are inherently more susceptible to P&D schemes due to their interchangeable nature. Standards such as ERC-20, BEP-20 [[37](https://arxiv.org/html/2412.18848v1#bib.bib37)], and experimental types like BRC-20 [[38](https://arxiv.org/html/2412.18848v1#bib.bib38)] or Runes enable mass trading, making them ideal for orchestrators seeking to manipulate prices. These tokens allow multiple traders to hold large amounts simultaneously, facilitating coordinated buying during the pump phase and subsequent dumping for profit.
ERC-20-like tokens, in particular, are widely used due to their ease of listing on exchanges and large market volumes. Their relatively low entry barriers for traders and higher anonymity compared to NFTs make them prime targets for manipulation. Anonymity, afforded by high token supplies, conceals orchestrators’ actions and ensures smoother coordination.

All target coins in observed P&D schemes in this study adhered to ERC-20-like standards. However, no pumps were observed involving listed BRC-20 tokens or Runes. This can be attributed to their limited trading availability on centralized exchanges [[39](https://arxiv.org/html/2412.18848v1#bib.bib39)], their experimental nature, and the lower adoption rates. Additionally, BRC-20 tokens face inefficiencies, including slower transaction speeds and higher fees, especially under network congestion [[10](https://arxiv.org/html/2412.18848v1#bib.bib10)]. These barriers reduce their attractiveness for orchestrators seeking rapid and large-scale price manipulation.

Nonetheless, the fungible nature of these newer standards implies potential susceptibility to P&D schemes as their popularity and market adoption grow. With improved infrastructure and broader exchange listings, these tokens may become more prominent targets, warranting further research into their vulnerabilities.

## VII Conclusion

This study presents a robust framework for detecting pump-and-dump (P&D) schemes in cryptocurrency markets, addressing a critical gap in research that predominantly focuses on post-event analysis or detecting pumps after they begin. By developing a real-time, ex-ante prediction pipeline, we enhance the ability to identify these schemes before they unfold.

Our approach integrates multiple data streams, including Telegram channel monitoring and high-frequency trade and order book data, to achieve accurate predictions. The Z-score-based model demonstrated strong predictive performance, correctly ranking the target coin within the top five in 55.81% of cases and within the top ten in 74.42% of cases when applied seconds before the pump event. While the model’s effectiveness diminishes as the prediction window extends, these results highlight the potential for early detection and its application in preemptive warning systems for centralized exchanges. We also provide a novel examination of token standards like BRC-20 and Runes, which we find not susceptible to the P&D schemes.

## References

### -A Additional Figures and Tables

Supplementary figures and tables detailing the characteristics of the analyzed data and empirical findings are provided on the subsequent pages of this appendix.

| Metric | Value |
| --- | --- |
| Overall Metrics |  |
| F1 weighted average | 0.982 |
| Precision | 0.982 |
| Recall | 0.982 |
| Label-specific F1 Scores |  |
| Pump Announcement | 0.976 |
| Countdown | 0.993 |
| Target Coin Release | 0.995 |
| Pump Results | 0.970 |
| Delay/Cancellation | 1.000 |
| Noise | 0.971 |

| Symbol | Name | Standard | Pumps |
| --- | --- | --- | --- |
| TOKKI | CRYPTOKKI | ERC-20 | 9 |
| DXGM | DexGame | ERC-20 | 8 |
| HMR | Homeros Game Barracks | ERC-20 | 8 |
| NAR | Narwhalswap | BEP-20 | 7 |
| JUSTICE | AssangeDAO | ERC-20 | 7 |

| Exchange | Type | Pumps | Percentage |
| --- | --- | --- | --- |
| Hotbit | CEX | 324 | 15.6% |
| LATOKEN | CEX | 304 | 14.6% |
| XT | CEX | 268 | 12.9% |
| Pancakeswap | DEX | 247 | 11.9% |
| Poloniex | CEX | 246 | 11.8% |
| KuCoin | CEX | 181 | 8.7% |
| LBank | CEX | 150 | 7.2% |
| DigiFinex | CEX | 120 | 5.8% |
| MEXC | CEX | 72 | 3.5% |
| Binance | CEX | 45 | 2.2% |
| Others | Mixed | 122 | 5.8% |

![Refer to caption](extracted/6094758/Figures/histogram_rank_pummps.png)
![Refer to caption](extracted/6094758/Figures/avg_daily_volumes_kucoin.png)
![Refer to caption](extracted/6094758/Figures/avg_daily_volumes_poloniex.png)
![Refer to caption](extracted/6094758/Figures/avg_daily_volumes_by_channels_kucoin.png)
![Refer to caption](extracted/6094758/Figures/avg_daily_volumes_by_channels_poloniex.png)
![Refer to caption](extracted/6094758/Figures/kucoin_bar_chart.png)
![Refer to caption](extracted/6094758/Figures/poloniex_order_size.png)

## Appendix A Appendix: Natural Language Processing

### A-A OpenAI Settings and Prompts

For labeling and information extraction, we utilized the latest version of GPT-4o. To improve consistency and reliability, the model’s randomness was reduced by setting the temperature parameter to 0.2 and the top\_p parameter to 0.95. All other parameters remained at their default values.

#### A-A1 Labeling Prompt

To classify Telegram messages from pump-and-dump channels, the model was instructed to assign one of six predefined labels. Each label was accompanied by a concise description, and the output format was specified as JSON. The following prompt was used:

#### A-A2 Extraction Prompts

The model also processed labeled messages to extract structured information. Two categories were targeted: announcement messages (extracting exchange, trading pair, and pump timing) and postponement/cancellation messages (updating the pump status).

##### Announcement Extraction Prompt

This prompt guided the model to extract essential details from pump announcements, as shown below:

##### Postponement/Cancellation Extraction Prompt

This prompt instructed the model to determine if a pump was postponed or canceled and to extract updated information as needed:

## Appendix B Computed Metrics

### B-A Order Book and Trade Data Metrics

Table [IX](https://arxiv.org/html/2412.18848v1#A2.T9 "TABLE IX ‣ B-A Order Book and Trade Data Metrics ‣ Appendix B Computed Metrics ‣ Machine Learning-Based Detection of Pump-and-Dump Schemes in Real-Time") defines the key metrics derived from order book and trade data, including their formulas and a brief explanation.

| Metric | Description and Formula |
| --- | --- |
| Bid-Ask Spread | Difference between the lowest ask price and highest bid price: Pminask−Pmaxbidsuperscriptsubscript𝑃minasksuperscriptsubscript𝑃maxbidP\_{\text{min}}^{\text{ask}}-P\_{\text{max}}^{\text{bid}}italic\_P start\_POSTSUBSCRIPT min end\_POSTSUBSCRIPT start\_POSTSUPERSCRIPT ask end\_POSTSUPERSCRIPT - italic\_P start\_POSTSUBSCRIPT max end\_POSTSUBSCRIPT start\_POSTSUPERSCRIPT bid end\_POSTSUPERSCRIPT |
| Average Order Size | Mean size per order: 1n⁢∑i=1nQi1𝑛superscriptsubscript𝑖1𝑛subscript𝑄𝑖\frac{1}{n}\sum\_{i=1}^{n}Q\_{i}divide start\_ARG 1 end\_ARG start\_ARG italic\_n end\_ARG ∑ start\_POSTSUBSCRIPT italic\_i = 1 end\_POSTSUBSCRIPT start\_POSTSUPERSCRIPT italic\_n end\_POSTSUPERSCRIPT italic\_Q start\_POSTSUBSCRIPT italic\_i end\_POSTSUBSCRIPT |
| Imbalance | Ratio of total bid quantity to total ask quantity: ∑Qbid∑Qasksubscript𝑄bidsubscript𝑄ask\frac{\sum Q\_{\text{bid}}}{\sum Q\_{\text{ask}}}divide start\_ARG ∑ italic\_Q start\_POSTSUBSCRIPT bid end\_POSTSUBSCRIPT end\_ARG start\_ARG ∑ italic\_Q start\_POSTSUBSCRIPT ask end\_POSTSUBSCRIPT end\_ARG |
| Imbalance Ratio | Adjusted imbalance around mid-price Pmidsubscript𝑃midP\_{\text{mid}}italic\_P start\_POSTSUBSCRIPT mid end\_POSTSUBSCRIPT: (Pbid⋅Qbid⋅Pmid)−(Pask⋅Qask⋅Pmid)Pbid⋅Qbid+Pask⋅Qask⋅subscript𝑃bidsubscript𝑄bidsubscript𝑃mid⋅subscript𝑃asksubscript𝑄asksubscript𝑃mid⋅subscript𝑃bidsubscript𝑄bid⋅subscript𝑃asksubscript𝑄ask\frac{(P\_{\text{bid}}\cdot Q\_{\text{bid}}\cdot P\_{\text{mid}})-(P\_{\text{ask}}% \cdot Q\_{\text{ask}}\cdot P\_{\text{mid}})}{P\_{\text{bid}}\cdot Q\_{\text{bid}}+% P\_{\text{ask}}\cdot Q\_{\text{ask}}}divide start\_ARG ( italic\_P start\_POSTSUBSCRIPT bid end\_POSTSUBSCRIPT ⋅ italic\_Q start\_POSTSUBSCRIPT bid end\_POSTSUBSCRIPT ⋅ italic\_P start\_POSTSUBSCRIPT mid end\_POSTSUBSCRIPT ) - ( italic\_P start\_POSTSUBSCRIPT ask end\_POSTSUBSCRIPT ⋅ italic\_Q start\_POSTSUBSCRIPT ask end\_POSTSUBSCRIPT ⋅ italic\_P start\_POSTSUBSCRIPT mid end\_POSTSUBSCRIPT ) end\_ARG start\_ARG italic\_P start\_POSTSUBSCRIPT bid end\_POSTSUBSCRIPT ⋅ italic\_Q start\_POSTSUBSCRIPT bid end\_POSTSUBSCRIPT + italic\_P start\_POSTSUBSCRIPT ask end\_POSTSUBSCRIPT ⋅ italic\_Q start\_POSTSUBSCRIPT ask end\_POSTSUBSCRIPT end\_ARG, where Pmid=Pmax+Pmin2subscript𝑃midsubscript𝑃maxsubscript𝑃min2P\_{\text{mid}}=\frac{P\_{\text{max}}+P\_{\text{min}}}{2}italic\_P start\_POSTSUBSCRIPT mid end\_POSTSUBSCRIPT = divide start\_ARG italic\_P start\_POSTSUBSCRIPT max end\_POSTSUBSCRIPT + italic\_P start\_POSTSUBSCRIPT min end\_POSTSUBSCRIPT end\_ARG start\_ARG 2 end\_ARG |
| Order Book Pressure | Proportion of bid quantity to total quantity: ∑Qbid∑Qbid+∑Qasksubscript𝑄bidsubscript𝑄bidsubscript𝑄ask\frac{\sum Q\_{\text{bid}}}{\sum Q\_{\text{bid}}+\sum Q\_{\text{ask}}}divide start\_ARG ∑ italic\_Q start\_POSTSUBSCRIPT bid end\_POSTSUBSCRIPT end\_ARG start\_ARG ∑ italic\_Q start\_POSTSUBSCRIPT bid end\_POSTSUBSCRIPT + ∑ italic\_Q start\_POSTSUBSCRIPT ask end\_POSTSUBSCRIPT end\_ARG |
| Order Book Slope | Median of bid-ask quantity differences at price levels: median⁢(Δ⁢Qbid−Δ⁢Qask)medianΔsubscript𝑄bidΔsubscript𝑄ask\text{median}(\Delta Q\_{\text{bid}}-\Delta Q\_{\text{ask}})median ( roman\_Δ italic\_Q start\_POSTSUBSCRIPT bid end\_POSTSUBSCRIPT - roman\_Δ italic\_Q start\_POSTSUBSCRIPT ask end\_POSTSUBSCRIPT ) |
| Liquidity Consumption | Total executed order quantity: ∑Qexecutedsubscript𝑄executed\sum Q\_{\text{executed}}∑ italic\_Q start\_POSTSUBSCRIPT executed end\_POSTSUBSCRIPT |
| Order Flow Imbalance (OFI) | Difference between total bid and ask quantities: ∑Qbid−∑Qasksubscript𝑄bidsubscript𝑄ask\sum Q\_{\text{bid}}-\sum Q\_{\text{ask}}∑ italic\_Q start\_POSTSUBSCRIPT bid end\_POSTSUBSCRIPT - ∑ italic\_Q start\_POSTSUBSCRIPT ask end\_POSTSUBSCRIPT |
| Market Orders Impact | Sum of market order quantities on bid and ask sides: ∑Qbid, market+∑Qask, marketsubscript𝑄bid, marketsubscript𝑄ask, market\sum Q\_{\text{bid, market}}+\sum Q\_{\text{ask, market}}∑ italic\_Q start\_POSTSUBSCRIPT bid, market end\_POSTSUBSCRIPT + ∑ italic\_Q start\_POSTSUBSCRIPT ask, market end\_POSTSUBSCRIPT |
| Relative Impact | Relative price change at liquidity levels: Pafter−PbeforePbeforesubscript𝑃aftersubscript𝑃beforesubscript𝑃before\frac{P\_{\text{after}}-P\_{\text{before}}}{P\_{\text{before}}}divide start\_ARG italic\_P start\_POSTSUBSCRIPT after end\_POSTSUBSCRIPT - italic\_P start\_POSTSUBSCRIPT before end\_POSTSUBSCRIPT end\_ARG start\_ARG italic\_P start\_POSTSUBSCRIPT before end\_POSTSUBSCRIPT end\_ARG, where Pbeforesubscript𝑃beforeP\_{\text{before}}italic\_P start\_POSTSUBSCRIPT before end\_POSTSUBSCRIPT and Paftersubscript𝑃afterP\_{\text{after}}italic\_P start\_POSTSUBSCRIPT after end\_POSTSUBSCRIPT are prices before and after consumption. |

## Appendix C Appendix: Data and Model Evaluation

### C-A XGBoost Model

This section contains the features we found to be most effective for the classification of coins into pumpable and non-pumpable. Initially, we calculated 27 features from the OHLCV (open, high, low, close, volume), market capitalization, and social time series data, which we collected for a sample of 1,714 coins (643 pumped coins and a random sample of 1,071 non-pump coins). The time series were made stationary by calculating the difference between consecutive terms in the series:

|  |  |  |  |
| --- | --- | --- | --- |
|  | yt′=yt−yt−1superscriptsubscript𝑦𝑡′subscript𝑦𝑡subscript𝑦𝑡1y\_{t}^{\prime}=y\_{t}-y\_{t-1}italic\_y start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT start\_POSTSUPERSCRIPT ′ end\_POSTSUPERSCRIPT = italic\_y start\_POSTSUBSCRIPT italic\_t end\_POSTSUBSCRIPT - italic\_y start\_POSTSUBSCRIPT italic\_t - 1 end\_POSTSUBSCRIPT |  | (1) |

Additionally, each time series was normalized by dividing it by Bitcoin’s corresponding value to remove differences over time. We chose Bitcoin because of its property as a central asset in the crypto market. Lastly, we applied min-max scaling across coins to normalize the scale of each feature while preserving inter-coin differences.

#### C-A1 Feature Selection

From the initial 27 time series features, we calculated multiple features per time series using the Python library TS Fresh, as XGBoost cannot work with data in time series format. We applied recursive feature elimination with a 5-fold cross-validation, using the weighted F1 score as the evaluation metric. Table [X](https://arxiv.org/html/2412.18848v1#A3.T10 "TABLE X ‣ C-A1 Feature Selection ‣ C-A XGBoost Model ‣ Appendix C Appendix: Data and Model Evaluation ‣ Machine Learning-Based Detection of Pump-and-Dump Schemes in Real-Time") lists the best features selected for each XGBoost model described in Section [V-B](https://arxiv.org/html/2412.18848v1#S5.SS2 "V-B Filter Models to Reduce the Candidate Pool ‣ V Empirical Results ‣ Machine Learning-Based Detection of Pump-and-Dump Schemes in Real-Time").

| Feature | Description | Model 0 | Model 1 | Model 2 | Model 3 |
| --- | --- | --- | --- | --- | --- |
| Close Price (Max) | Highest recorded closing price | X | X | X | X |
| Close Price (Min) | Lowest recorded closing price | X | X | X | X |
| Market Cap (Median) | Median market capitalization | X | X | X | X |
| Market Cap (Std. Dev.) | Volatility of market capitalization | X | X | X | X |
| Market Cap (Max) | Maximum market capitalization | X | X | X | X |
| Market Cap (Min) | Minimum market capitalization | X | X | X | X |
| Trading Vol. (Max) | Maximum trading volume | X |  |  |  |
| Close Price (Sum) | Total closing price sum |  | X |  |  |
| Close Price (RMS) | Root mean square of closing prices |  | X |  | X |
| Market Cap (Sum) | Total market capitalization sum |  | X | X | X |
| Market Cap (Variance) | Variance of market capitalization |  | X |  |  |
| Close Price Change (RMS) | RMS of closing price changes |  | X | X |  |
| User Interactions (Min) | Minimum user interactions |  |  | X | X |
| High Interaction Points (Sum) | Sum of high interaction points |  |  | X |  |
| Sentiment Score (Sum) | Total sentiment score |  |  | X | X |
| Sentiment Score (RMS) | RMS of sentiment scores |  |  | X |  |
| Sentiment Score (Max) | Maximum sentiment score |  |  | X | X |
| Sentiment Score (Min) | Minimum sentiment score |  |  | X | X |
| High Sentiment Points (Sum) | Sum of high sentiment points |  |  | X |  |
| Posts Created (Sum) | Total posts created |  |  | X |  |
| Posts Created (Min) | Minimum posts created |  |  | X | X |
| Social Dominance (Sum) | Total social dominance |  |  | X | X |
| High Social Dominance (Sum) | High social dominance points |  |  | X | X |
| Interaction-to-Market Cap Ratio (Min) | Min. interaction-to-market cap ratio |  |  | X | X |
| Close Price Spectral Entropy (Sum) | Spectral entropy of closing prices |  |  |  | X |
| Close Price Spectral Entropy (Median) | Median spectral entropy |  |  |  | X |
| Close Price RMS (Sum) | RMS of closing prices (sum) |  |  |  | X |
| Close Price RMS (Median) | Median RMS of closing prices |  |  |  | X |
| Close Price Hurst Exponent (Sum) | Sum of Hurst exponents |  |  |  | X |

#### C-A2 Hyperparameter Tuning

After feature selection, we trained the XGBoost classifier on various feature combinations. Hyperparameters, including max\_depth, min\_child\_weight, and scale\_pos\_weight, were fine-tuned using grid search with 3-fold cross-validation. Interestingly, the default parameters of the XGBClassifier in the Python xgboost library performed better than the grid-searched parameters.

#### C-A3 Performance Evaluation

![Refer to caption](extracted/6094758/Figures/confusion_matrix_XGBoost.png)

We evaluated performance using metrics like precision, recall, F1 score, and Precision-Recall AUC (Figures [15](https://arxiv.org/html/2412.18848v1#A3.F15 "Figure 15 ‣ C-A3 Performance Evaluation ‣ C-A XGBoost Model ‣ Appendix C Appendix: Data and Model Evaluation ‣ Machine Learning-Based Detection of Pump-and-Dump Schemes in Real-Time"), [16](https://arxiv.org/html/2412.18848v1#A3.F16 "Figure 16 ‣ C-A3 Performance Evaluation ‣ C-A XGBoost Model ‣ Appendix C Appendix: Data and Model Evaluation ‣ Machine Learning-Based Detection of Pump-and-Dump Schemes in Real-Time"), and [17](https://arxiv.org/html/2412.18848v1#A3.F17 "Figure 17 ‣ C-A3 Performance Evaluation ‣ C-A XGBoost Model ‣ Appendix C Appendix: Data and Model Evaluation ‣ Machine Learning-Based Detection of Pump-and-Dump Schemes in Real-Time")). Table [X](https://arxiv.org/html/2412.18848v1#A3.T10 "TABLE X ‣ C-A1 Feature Selection ‣ C-A XGBoost Model ‣ Appendix C Appendix: Data and Model Evaluation ‣ Machine Learning-Based Detection of Pump-and-Dump Schemes in Real-Time") highlights the reliance of all models on market data, such as maximum and minimum closing prices and market cap metrics. While social data (e.g., sentiment scores and user interactions) and geometric time series features (e.g., spectral entropy) marginally improved models 2 and 3, traditional market data remained the primary predictive factor.

![Refer to caption](extracted/6094758/Figures/precision-recall_curve.png)
![Refer to caption](extracted/6094758/Figures/weighted_F1_score_vs_threshold.png)
![Refer to caption](extracted/6094758/Figures/precision_recall_AUC_vs_threshold.png)

### C-B Unsupervised Clustering Experiments

Finding potential coins that have a higher likelihood of being ”pumped” in the future was a crucial phase of our research. We explored clustering, an unsupervised learning method frequently used to detect trends or anomalies in large datasets, such as cryptocurrency price data. Our analysis employed clustering algorithms, including Gaussian Mixture Models, K-means, Agglomerative Clustering, and DBSCAN. However, these methods did not produce strong results in identifying distinct groups within the data, likely due to the complexity and overlap of the dataset.

#### C-B1 Data Preprocessing

Feature Engineering: The initial dataset included a variety of social and financial metrics extracted using the tsfresh library. Features were chosen based on their importance in detecting P&D schemes.
  
Log Transformation and Scaling: Log-transformed features were used to reduce skewness and stabilize variance. To ensure equal contribution from each feature, data was standardized using StandardScaler.
  
Principal Component Analysis (PCA): PCA was applied to reduce dimensionality and preserve components capturing the greatest variance, optimizing the clustering procedure and aiding visualization of high-dimensional data.

#### C-B2 DBSCAN (Density-Based Spatial Clustering of Applications with Noise)

DBSCAN groups points based on density while classifying isolated points as noise. Unlike other methods, it does not require specifying the number of clusters. Instead, it uses two parameters: min\_samples, the minimum points to form a dense region, and eps, the radius of each neighborhood [[40](https://arxiv.org/html/2412.18848v1#bib.bib40)].

#### C-B3 K-means Clustering

K-means is widely used for dividing datasets into k𝑘kitalic\_k clusters. The algorithm iteratively updates cluster centers (centroids) and reassigns points until convergence [[41](https://arxiv.org/html/2412.18848v1#bib.bib41)]. In our study, K-means grouped coins based on historical data patterns. Multiple values of k𝑘kitalic\_k were tested to identify performance tiers among coins.

#### C-B4 Agglomerative Clustering

Agglomerative clustering is a hierarchical method where each data point starts as its own cluster, merging iteratively based on a chosen linkage criterion [[42](https://arxiv.org/html/2412.18848v1#bib.bib42)]. This method revealed multi-level hierarchies, helping visualize how clusters evolve and merge as distance thresholds increase.

#### C-B5 Gaussian Mixture Model (GMM)

GMM is a probabilistic approach that assumes data originates from multiple Gaussian distributions. Parameters for each cluster are estimated using the Expectation-Maximization (EM) algorithm [[43](https://arxiv.org/html/2412.18848v1#bib.bib43)]. GMM is particularly useful for handling clusters with varying shapes and sizes.

| Clustering Algorithm | Silhouette Score | Davies-Bouldin Score |
| --- | --- | --- |
| DBSCAN | 0.19 | 1.55 |
| K-means | 0.55 | 0.74 |
| Agglomerative | 0.46 | 0.81 |
| Gaussian Mixture (GMM) | 0.48 | 0.78 |

![Refer to caption](extracted/6094758/Figures/imgcluster.png)

As shown in Table [XI](https://arxiv.org/html/2412.18848v1#A3.T11 "TABLE XI ‣ C-B5 Gaussian Mixture Model (GMM) ‣ C-B Unsupervised Clustering Experiments ‣ Appendix C Appendix: Data and Model Evaluation ‣ Machine Learning-Based Detection of Pump-and-Dump Schemes in Real-Time"), the Silhouette and Davies-Bouldin scores indicate poor clustering performance. Low Silhouette scores suggest that clusters are not well-defined, while high Davies-Bouldin scores imply significant overlap among clusters. Despite extensive preprocessing, the dataset’s inherent structure likely contributes to these challenges. The characteristics of the clusters appear insufficiently distinct, complicating the ability of algorithms to differentiate groups effectively.

## Appendix D Target Coin Prediction Metrics

Tables [XII](https://arxiv.org/html/2412.18848v1#A4.T12 "TABLE XII ‣ D-A Target Coin Prediction Metrics ‣ Appendix D Target Coin Prediction Metrics ‣ Machine Learning-Based Detection of Pump-and-Dump Schemes in Real-Time") to [XV](https://arxiv.org/html/2412.18848v1#A4.T15 "TABLE XV ‣ D-A Target Coin Prediction Metrics ‣ Appendix D Target Coin Prediction Metrics ‣ Machine Learning-Based Detection of Pump-and-Dump Schemes in Real-Time") present order book and trade metrics of the observed coins surrounding a pump event. Each table highlights average volumes, price changes, and order sizes before and during pump events for various exchanges.

### D-A Target Coin Prediction Metrics

Tables [XII](https://arxiv.org/html/2412.18848v1#A4.T12 "TABLE XII ‣ D-A Target Coin Prediction Metrics ‣ Appendix D Target Coin Prediction Metrics ‣ Machine Learning-Based Detection of Pump-and-Dump Schemes in Real-Time") to [XV](https://arxiv.org/html/2412.18848v1#A4.T15 "TABLE XV ‣ D-A Target Coin Prediction Metrics ‣ Appendix D Target Coin Prediction Metrics ‣ Machine Learning-Based Detection of Pump-and-Dump Schemes in Real-Time") contain order book and trade metrics of the observed coins surrounding a pump event.

| Coin Name | Avg Volume | Total Volume | Volume | Avg Price | Avg Price | Price | Avg Order Size | Avg Order Size | Order Size |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  | 7 Days | Pump Day | Increase % | 7 Days | Pump Day | Increase % | 7 Days | Pump Day | Increase % |
| AIEPK | 12965.69 | 566719.68 | 43.71 | 0.0 | 0.01 | 95.25 | 2257.07 | 2203.07 | 0.98 |
| ALPINE | 2321.37 | 85013.5 | 36.62 | 1.97 | 2.23 | 12.76 | 5.57 | 4.8 | 0.86 |
| ARKER | 362214.3 | 3032225.71 | 8.37 | 0.0 | 0.0 | 91.17 | 20672.71 | 5720.09 | 0.28 |
| BIDP | 161496.98 | 931795.93 | 5.77 | 0.01 | 0.01 | 15.51 | 3513.76 | 5136.09 | 1.46 |
| BIFI | 42892.62 | 1803347.95 | 42.04 | 0.01 | 0.01 | 77.56 | 865.73 | 1020.96 | 1.18 |
| BIFI | 105011.27 | 2317914.54 | 22.07 | 0.01 | 0.01 | 131.48 | 13596.83 | 1143.4 | 0.08 |
| BMON | 10617.88 | 486288.06 | 45.8 | 0.02 | 0.02 | 50.56 | 1212.0 | 805.52 | 0.66 |
| BNC | 13846.84 | 626447.05 | 45.24 | 0.11 | 0.17 | 46.38 | 177.56 | 88.47 | 0.5 |
| BONDLY | 60793.8 | 443348.62 | 7.29 | 0.01 | 0.01 | 33.28 | 3865.7 | 2628.9 | 0.68 |
| BONDLY | 126760.27 | 8225742.92 | 64.89 | 0.0 | 0.02 | 244.09 | 19311.38 | 2413.37 | 0.12 |
| BULL | 41328.36 | 343492.38 | 8.31 | 0.0 | 0.0 | 51.84 | 12015.44 | 4834.62 | 0.4 |
| BUY | 25747.28 | 39013.32 | 1.52 | 0.0 | 0.0 | -8.15 | 3676.5 | 2273.04 | 0.62 |
| CAS | 108445.69 | 2115140.88 | 19.5 | 0.01 | 0.01 | 22.53 | 1901.48 | 2855.56 | 1.5 |
| COOHA | 105780.36 | 2194494.18 | 20.75 | 0.13 | 0.3 | 130.64 | 35.82 | 30.84 | 0.86 |
| DAPPT | 194455.15 | 843953.12 | 4.34 | 0.0 | 0.0 | -4.14 | 7162.0 | 10203.83 | 1.42 |
| DPET | 30100.73 | 1138966.11 | 37.84 | 0.11 | 0.17 | 52.26 | 51.67 | 48.4 | 0.94 |
| DPET | 130764.9 | 3364338.01 | 25.73 | 0.08 | 0.15 | 82.96 | 592.33 | 215.3 | 0.36 |
| ECOX | 7830.59 | 290573.38 | 37.11 | 0.38 | 0.59 | 52.89 | 171.35 | 68.45 | 0.4 |
| EGAME | 6121.9 | 887174.79 | 144.92 | 0.0 | 0.0 | 94.03 | 182847.28 | 250216.8 | 1.37 |
| FCL | 28417.81 | 192908.36 | 6.79 | 0.03 | 0.03 | 8.68 | 2788.48 | 1625.06 | 0.58 |
| FEAR | 44536.76 | 4491420.81 | 100.85 | 0.15 | 0.41 | 180.28 | 132.21 | 76.93 | 0.58 |
| FLAME | 195211.91 | 7258528.59 | 37.18 | 0.03 | 0.1 | 244.69 | 1203.06 | 352.45 | 0.29 |
| FLAME | 122443.44 | 273753.36 | 2.24 | 0.04 | 0.05 | 11.86 | 2187.39 | 633.25 | 0.29 |
| GAMMA | 8770.33 | 431477.2 | 49.2 | 0.18 | 0.22 | 19.19 | 49.59 | 43.08 | 0.87 |
| GGG | 11311.14 | 796141.1 | 70.39 | 0.04 | 0.07 | 76.44 | 905.0 | 239.89 | 0.27 |
| GGG | 15874.92 | 205059.16 | 12.92 | 0.04 | 0.05 | 18.25 | 569.86 | 312.69 | 0.55 |
| GMEE | 113757.09 | 740475.74 | 6.51 | 0.01 | 0.01 | 49.17 | 3633.36 | 2172.21 | 0.6 |
| GOVI | 1222.69 | 144070.47 | 117.83 | 0.15 | 0.18 | 19.66 | 182.06 | 175.44 | 0.96 |
| H2O | 123309.17 | 1532412.86 | 12.43 | 0.17 | 0.34 | 99.32 | 415.33 | 97.81 | 0.24 |
| H2O | 259385.67 | 2798775.06 | 10.79 | 0.22 | 0.38 | 74.95 | 482.66 | 196.65 | 0.41 |
| HALO | 63070.73 | 3005179.88 | 47.65 | 0.06 | 0.09 | 64.01 | 467.24 | 538.08 | 1.15 |
| HBB | 39317.16 | 2558441.68 | 65.07 | 0.1 | 0.16 | 57.27 | 324.84 | 157.9 | 0.49 |
| HMND | 56542.86 | 51172.08 | 0.91 | 0.03 | 0.03 | -12.0 | 258.07 | 206.86 | 0.8 |
| HORD | 126536.9 | 1044383.87 | 8.25 | 0.02 | 0.02 | 4.42 | 1134.03 | 749.18 | 0.66 |
| HYVE | 27495.19 | 2357516.37 | 85.74 | 0.06 | 0.11 | 97.88 | 498.18 | 280.83 | 0.56 |
| IHC | 48052.46 | 1149549.41 | 23.92 | 0.0 | 0.0 | 60.41 | 1611370.09 | 193855.92 | 0.12 |
| IHC | 7388.19 | 1082596.09 | 146.53 | 0.0 | 0.0 | 80.31 | 522887.35 | 203857.16 | 0.39 |
| IZI | 48093.69 | 825631.34 | 17.17 | 0.02 | 0.02 | 52.46 | 2129.62 | 752.08 | 0.35 |
| IZI | 6701.34 | 989259.04 | 147.62 | 0.01 | 0.01 | 52.82 | 2662.44 | 2130.59 | 0.8 |
| KLUB | 827934.34 | 4025313.86 | 4.86 | 0.02 | 0.02 | -12.86 | 4346.38 | 2073.19 | 0.48 |
| KOK | 56405.8 | 436050.7 | 7.73 | 0.01 | 0.01 | 7.22 | 587.24 | 445.64 | 0.76 |
| KOL | 19631.62 | 1541882.73 | 78.54 | 0.0 | 0.0 | 67.83 | 4202.19 | 3471.9 | 0.83 |
| KPOL | 108367.9 | 2993117.54 | 27.62 | 0.01 | 0.02 | 120.47 | 1750.89 | 2270.19 | 1.3 |
| LAVAX | 730279.83 | 4767413.11 | 6.53 | 0.08 | 0.11 | 35.21 | 276.52 | 187.65 | 0.68 |
| LAYER | 63863.53 | 3342996.3 | 52.35 | 0.07 | 0.25 | 248.81 | 844.15 | 134.56 | 0.16 |
| LBP | 16020.73 | 3167041.21 | 197.68 | 0.0 | 0.0 | 88.44 | 11167.42 | 3518.74 | 0.32 |
| LPOOL | 72984.85 | 2020915.44 | 27.69 | 0.2 | 0.42 | 105.04 | 122.16 | 54.32 | 0.44 |
| MJT | 7609.76 | 1893754.37 | 248.86 | 0.04 | 0.08 | 117.59 | 348.13 | 368.45 | 1.06 |
| MJT | 2684.11 | 129879.93 | 48.39 | 0.02 | 0.02 | 39.99 | 323.46 | 334.08 | 1.03 |
| MLK | 87842.15 | 565526.01 | 6.44 | 0.35 | 0.48 | 36.77 | 41.58 | 51.47 | 1.24 |

| Coin Name | Avg Volume | Total Volume | Volume | Avg Price | Avg Price | Price | Avg Order Size | Avg Order Size | Order Size |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  | 7 Days | Pump Day | Increase % | 7 Days | Pump Day | Increase % | 7 Days | Pump Day | Increase % |
| MODEFI | 3668.07 | 376635.56 | 102.68 | 0.2 | 0.46 | 134.66 | 118.53 | 42.05 | 0.35 |
| MONI | 117154.84 | 2145779.76 | 18.32 | 0.02 | 0.04 | 112.72 | 357.37 | 568.85 | 1.59 |
| MTS | 109942.46 | 1958262.71 | 17.81 | 0.01 | 0.03 | 94.22 | 704.36 | 665.11 | 0.94 |
| MXC | 24069.91 | 2687997.34 | 111.67 | 0.02 | 0.08 | 375.22 | 600.56 | 170.68 | 0.28 |
| NORD | 39898.22 | 1549230.0 | 38.83 | 0.14 | 0.29 | 111.01 | 123.18 | 50.01 | 0.41 |
| NRFB | 12953.67 | 97047.14 | 7.49 | 0.0 | 0.0 | 17.48 | 33809.5 | 26434.54 | 0.78 |
| OBI | 2726.84 | 173385.68 | 63.58 | 0.01 | 0.01 | 33.59 | 2677.8 | 1573.52 | 0.59 |
| OBI | 50033.97 | 274536.16 | 5.49 | 0.01 | 0.01 | 59.72 | 3593.89 | 906.52 | 0.25 |
| ODDZ | 121569.46 | 1700669.53 | 13.99 | 0.02 | 0.03 | 53.72 | 2581.77 | 958.69 | 0.3 |
| ODDZ | 86149.2 | 2113515.34 | 24.53 | 0.02 | 0.03 | 87.98 | 1249.79 | 714.07 | 0.5 |
| OGV | 1949.86 | 68539.95 | 35.15 | 0.01 | 0.01 | 53.96 | 1437.21 | 1106.13 | 0.7 |
| PEEL | 194889.38 | 1627231.48 | 8.35 | 0.07 | 0.11 | 60.21 | 285.22 | 276.82 | 0.9 |
| PEEL | 6723.92 | 191555.11 | 28.49 | 0.04 | 0.07 | 61.91 | 316.68 | 183.18 | 0.5 |
| PEL | 117958.25 | 2796686.4 | 23.71 | 0.01 | 0.02 | 106.44 | 7468.77 | 697.43 | 0.0 |
| PEL | 58490.19 | 197948.92 | 3.38 | 0.0 | 0.0 | 10.03 | 15162.06 | 3937.75 | 0.2 |
| PIP | 1507.18 | 82218.26 | 54.55 | 0.04 | 0.04 | 21.3 | 124.27 | 234.62 | 1.8 |
| PMON | 109890.02 | 1585090.07 | 14.42 | 0.94 | 1.37 | 46.22 | 23.26 | 17.9 | 0.7 |
| QUARTZ | 18298.23 | 2148955.7 | 117.44 | 0.38 | 0.73 | 93.03 | 125.22 | 52.29 | 0.4 |
| QUICK | 17697.64 | 3089217.09 | 174.56 | 65.93 | 326.92 | 395.85 | 0.15 | 0.06 | 0.41 |
| SOLS | 6372.56 | 146203.89 | 22.94 | 0.33 | 1.49 | 345.83 | 52.42 | 15.03 | 0.29 |
| SON | 23707.28 | 568531.36 | 23.98 | 0.0 | 0.0 | 21.49 | 27162.93 | 32556.65 | 1.2 |
| SON | 47785.19 | 7240703.86 | 151.53 | 0.0 | 0.0 | 216.73 | 36132.94 | 18445.38 | 0.51 |
| SQUAD | 5554.8 | 846722.25 | 152.43 | 0.0 | 0.0 | 105.62 | 2593.82 | 1922.48 | 0.74 |
| STRIKE | 231785.59 | 3499608.79 | 15.1 | 13.53 | 22.82 | 68.72 | 1.1 | 2.36 | 2.15 |
| SUIA | 122544.23 | 1391441.17 | 11.35 | 0.09 | 0.17 | 95.8 | 70.14 | 73.23 | 1.04 |
| SUIA | 9178.66 | 2221894.7 | 242.07 | 0.08 | 0.22 | 190.08 | 115.16 | 65.22 | 0.57 |
| SWP | 36627.91 | 559799.61 | 15.28 | 0.07 | 0.09 | 32.74 | 333.0 | 147.28 | 0.44 |
| SYNR | 105946.22 | 525641.42 | 4.96 | 0.01 | 0.02 | 22.22 | 7324.7 | 5227.02 | 0.71 |
| SYNR | 13074.98 | 632080.75 | 48.34 | 0.0 | 0.0 | 78.02 | 24862.46 | 28115.58 | 1.13 |
| SYNR | 11378.29 | 293891.15 | 25.83 | 0.0 | 0.0 | 71.15 | 58614.05 | 50166.66 | 0.86 |
| TT | 70562.47 | 386263.62 | 5.47 | 0.0 | 0.01 | 37.79 | 1995.49 | 4840.71 | 2.43 |
| UNIC | 113384.81 | 1425537.43 | 12.57 | 2.03 | 4.78 | 134.95 | 31.58 | 6.58 | 0.21 |
| VCORE | 13840.65 | 7337883.93 | 530.17 | 0.0 | 0.01 | 339.73 | 17237.77 | 4475.22 | 0.26 |
| VEMP | 46936.62 | 573976.26 | 12.23 | 0.01 | 0.01 | 32.4 | 1482.67 | 3169.75 | 2.14 |
| VERSE | 196703.46 | 666594.96 | 3.39 | 0.0 | 0.0 | 9.72 | 292881.52 | 187915.13 | 0.6 |
| VERSE | 145481.23 | 1784701.5 | 12.27 | 0.0 | 0.0 | 96.66 | 308337.83 | 124650.77 | 0.4 |
| WAL | 26414.69 | 3208412.64 | 121.46 | 0.02 | 0.07 | 208.14 | 1405.52 | 489.53 | 0.35 |
| WHALE | 59712.76 | 869655.61 | 14.56 | 0.69 | 0.92 | 33.0 | 21.34 | 22.62 | 1.06 |
| WOMBAT | 42570.46 | 698867.19 | 16.42 | 0.0 | 0.0 | 39.7 | 17675.28 | 6484.59 | 0.37 |
| WOMBAT | 33880.67 | 2911776.4 | 85.94 | 0.0 | 0.0 | 175.19 | 15065.79 | 6164.91 | 0.41 |
| WOOP | 34922.08 | 1301842.67 | 37.28 | 0.03 | 0.06 | 92.88 | 399.11 | 299.98 | 0.75 |
| XCV | 139480.55 | 1171051.23 | 8.4 | 0.0 | 0.01 | 23.94 | 18088.2 | 4264.62 | 0.2 |
| XCV | 92498.83 | 8795726.14 | 95.09 | 0.0 | 0.01 | 155.87 | 7800.77 | 3114.46 | 0.4 |
| XWG | 213151.21 | 2067679.99 | 9.7 | 0.0 | 0.0 | 129.36 | 19902.4 | 7709.52 | 0.39 |
| YLD | 97638.56 | 138185.58 | 1.42 | 0.06 | 0.07 | 10.17 | 1568.03 | 1126.78 | 0.72 |

| Coin Name | Avg Volume | Total Volume | Volume | Avg Price | Avg Price | Price | Avg Order Size | Avg Order Size | Order Size |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  | 7 Days | Pump Day | Increase % | 7 Days | Pump Day | Increase % | 7 Days | Pump Day | Increase % |
| AGI | 57.03 | 6700.94 | 117.49 | 0.01 | 0.03 | 439.95 | 2264.31 | 1458.15 | 0.64 |
| ALPHA | 2.26 | 590.34 | 260.68 | 0.02 | 0.11 | 536.54 | 41.92 | 95.75 | 2.28 |
| AMC | 17.54 | 3407.81 | 194.27 | 0.13 | 0.25 | 93.98 | 51.69 | 49.05 | 0.95 |
| AMC | 4.72 | 1798.07 | 380.74 | 0.04 | 0.09 | 107.84 | 20.9 | 198.88 | 9.52 |
| APU | 33.45 | 1293.77 | 38.67 | 0.0 | 0.0 | 149.48 | 59293226.1 | 27317595.96 | 0.46 |
| ARG | 0.0 | 152.96 |  | 0.0 | 0.85 |  | 0.0 | 7.3 |  |
| ATLAS | 271.68 | 1946.31 | 7.16 | 0.0 | 0.01 | 48.56 | 10008.33 | 2166.34 | 0.22 |
| ATLAS | 156.17 | 902.87 | 5.78 | 0.0 | 0.0 | 26.97 | 7468.53 | 1644.29 | 0.22 |
| B20 | 12.49 | 9906.16 | 793.37 | 0.07 | 0.56 | 707.9 | 68.85 | 53.79 | 0.78 |
| BFT | 33.22 | 1979.74 | 59.59 | 0.06 | 0.09 | 52.7 | 94.73 | 156.96 | 1.66 |
| BIF | 0.0 | 805.2 |  | 0.0 | 0.0 |  | 0.0 | 53265.11 |  |
| BITCI | 21.5 | 4230.19 | 196.78 | 0.0 | 0.01 | 233.81 | 4150.6 | 2340.13 | 0.56 |
| BITCI | 20.12 | 2270.59 | 112.86 | 0.0 | 0.0 | 91.02 | 5398.98 | 11049.23 | 2.05 |
| BLY | 0.78 | 6695.91 | 8548.54 | 0.0 | 0.05 | 4011.93 | 180.19 | 836.28 | 4.64 |
| BNBDADDY | 178.44 | 1453.79 | 8.15 | 0.0 | 0.0 | 44.47 | 22137947.57 | 21843866.48 | 0.99 |
| BNX | 37.57 | 17836.0 | 474.72 | 0.49 | 5.89 | 1094.96 | 6.66 | 41.66 | 6.26 |
| BNX | 17.39 | 1944.67 | 111.81 | 0.23 | 0.41 | 75.93 | 12.51 | 30.11 | 2.41 |
| BOTS | 0.0 | 10831.19 |  | 0.0 | 0.0 |  | 0.0 | 5344291283.17 |  |
| BTM2 | 16.26 | 4308.25 | 265.03 | 0.0 | 0.03 | 534.04 | 844.15 | 571.23 | 0.68 |
| CAPO | 0.2 | 269.75 | 1321.95 | 0.0 | 0.0 | 1580.43 | 3850.16 | 53435.54 | 13.88 |
| CEL | 19.89 | 2065.54 | 103.85 | 0.12 | 0.24 | 98.67 | 39.88 | 50.39 | 1.26 |
| CHAD | 12.62 | 1525.13 | 120.84 | 0.0 | 0.0 | 59.82 | 1051632.57 | 2174058.92 | 2.07 |
| CID | 25.52 | 17592.61 | 689.41 | 0.01 | 0.01 | 138.25 | 660.13 | 1519.17 | 2.3 |
| CID | 0.39 | 4990.56 | 12898.22 | 0.0 | 0.02 | 500.97 | 46.11 | 973.32 | 21.11 |
| CLV | 18.33 | 2624.99 | 143.19 | 0.04 | 0.07 | 66.59 | 106.32 | 257.41 | 2.42 |
| CLV | 0.0 | 946.66 |  | 0.0 | 0.09 |  | 0.0 | 111.83 |  |
| CLV | 6.94 | 850.25 | 122.45 | 0.02 | 0.06 | 163.71 | 94.85 | 193.52 | 2.04 |
| CLV | 1.65 | 296.24 | 179.54 | 0.02 | 0.07 | 296.18 | 25.22 | 122.74 | 4.87 |
| COLLAB | 16.04 | 3692.6 | 230.26 | 0.01 | 0.03 | 376.61 | 914.13 | 884.19 | 0.97 |
| CTC | 0.71 | 10680.36 | 14952.52 | 0.03 | 2.65 | 8330.93 | 3.24 | 15.32 | 4.73 |
| CTSI | 0.74 | 10328.26 | 13967.62 | 0.04 | 0.49 | 1039.17 | 4.76 | 66.81 | 14.02 |
| CULT | 63.41 | 5086.45 | 80.21 | 0.0 | 0.0 | 425.16 | 1501845.36 | 1116453.74 | 0.74 |
| CULT | 291.8 | 1494.98 | 5.12 | 0.0 | 0.0 | 84.59 | 14230116.25 | 2862094.59 | 0.2 |
| CULT | 1.58 | 782.02 | 494.86 | 0.0 | 0.0 | 1389.34 | 1897090.57 | 4042214.14 | 2.13 |
| CVP | 32.38 | 4625.23 | 142.83 | 0.21 | 0.86 | 303.39 | 79.8 | 54.75 | 0.69 |
| DAR | 0.97 | 4135.12 | 4253.3 | 0.04 | 0.23 | 458.09 | 7.83 | 144.07 | 18.39 |
| DAR | 10.69 | 4933.85 | 461.43 | 0.08 | 2.49 | 3132.91 | 45.97 | 14.35 | 0.31 |
| DAR | 73.77 | 8184.07 | 110.94 | 0.15 | 0.24 | 64.2 | 57.52 | 179.53 | 3.12 |
| DAR | 27.43 | 2334.55 | 85.1 | 0.13 | 0.15 | 14.9 | 37.69 | 127.96 | 3.4 |
| DAR | 84.27 | 1423.99 | 16.9 | 0.11 | 0.22 | 95.43 | 217.96 | 42.74 | 0.2 |
| DHT | 0.92 | 18451.74 | 20095.2 | 0.04 | 0.6 | 1454.93 | 4.89 | 58.34 | 11.92 |
| DMT | 18.15 | 3294.33 | 181.47 | 0.03 | 0.08 | 212.6 | 182.69 | 149.85 | 0.82 |
| DOBO | 0.0 | 5435.75 |  | 0.0 | 0.01 |  | 0.0 | 3319.22 |  |
| DORA | 0.42 | 3635.93 | 8667.4 | 0.27 | 4.64 | 1597.85 | 0.63 | 5.32 | 8.42 |
| DORKL | 0.25 | 4150.41 | 16560.67 | 0.0 | 0.02 | 7915.52 | 198.99 | 1702.94 | 8.56 |
| DORKL | 888.06 | 70.9 | 0.08 | 0.03 | 0.0 | -96.18 | 778.84 | 4648.83 | 5.97 |
| DORKL | 156.41 | 0.0 | 0.0 | 0.0 | 0.0 | -100.0 | 2922.58 | 0.0 | 0 |
| DORKL | 253.51 | 0.0 | 0.0 | 0.01 | 0.0 | -100.0 | 2579.98 | 0.0 | 0 |
| DOS | 15.56 | 12574.1 | 808.2 | 0.0 | 0.02 | 2057.65 | 4333.87 | 2777.59 | 0.64 |
| DUSK | 0.92 | 2286.46 | 2486.31 | 0.07 | 0.34 | 363.39 | 2.71 | 41.71 | 15.38 |
| DYP | 43.55 | 12500.31 | 287.0 | 0.15 | 0.46 | 208.04 | 80.11 | 56.35 | 0.7 |
| DYP | 53.93 | 3316.52 | 61.5 | 0.18 | 0.2 | 15.35 | 45.35 | 90.91 | 2 |
| EFI | 15.38 | 7018.25 | 456.24 | 0.02 | 0.09 | 294.47 | 221.95 | 324.78 | 1.46 |
| EGG | 1.0 | 1616.79 | 1623.4 | 0.0 | 0.0 | 588.86 | 1028.24 | 9967.61 | 9.69 |
| EGG | 6.66 | 2087.48 | 313.41 | 0.0 | 0.0 | 192.78 | 4939.03 | 10699.55 | 2.17 |
| EGG | 142.1 | 1992.98 | 14.03 | 0.0 | 0.0 | 201.89 | 33560.07 | 7710.52 | 0.23 |
| ERN | 1.71 | 8848.88 | 5162.96 | 0.45 | 6.73 | 1389.32 | 1.09 | 6.17 | 5.67 |
| FERC | 0.0 | 4266.58 |  | 0.0 | 0.33 |  | 0.0 | 66.67 |  |
| FERC | 0.66 | 440.41 | 670.29 | 0.01 | 0.03 | 417.05 | 33.0 | 401.74 | 12.17 |
| FITFI | 0.17 | 25382.43 | 148064.51 | 0.0 | 0.14 | 15268.53 | 27.12 | 1088.54 | 40.13 |
| FITFI | 0.73 | 888.1 | 1216.04 | 0.0 | 0.01 | 407.39 | 128.08 | 1877.01 | 14.65 |
| FITFI | 20.42 | 3342.6 | 163.68 | 0.0 | 0.01 | 264.2 | 2621.1 | 3375.48 | 1.29 |
| FOUR | 0.0 | 9105.65 |  | 0.0 | 0.0 |  | 0.0 | 1858339.2 |  |
| FRONT | 5.48 | 6319.63 | 1153.83 | 0.1 | 0.26 | 154.12 | 20.2 | 64.4 | 3.19 |
| FUR | 2.48 | 8231.37 | 3320.26 | 0.0 | 0.0 | 947.44 | 25266.75 | 80631.53 | 3.19 |
| GDX | 0.27 | 3311.52 | 12064.07 | 0.01 | 0.14 | 946.03 | 9.29 | 125.1 | 13.46 |
| GFT | 1.11 | 19860.82 | 17886.73 | 0.01 | 0.18 | 2015.1 | 37.82 | 529.65 | 14 |
| GFT | 37.6 | 1449.82 | 38.56 | 0.03 | 0.04 | 59.53 | 296.42 | 214.56 | 0.72 |
| GFT | 34.37 | 4261.85 | 123.99 | 0.02 | 0.03 | 70.9 | 808.65 | 775.09 | 0.96 |
| GHST | 0.0 | 6422.52 |  | 0.0 | 2.94 |  | 0.0 | 7.59 |  |
| GHST | 10.61 | 4580.7 | 431.82 | 0.38 | 1.1 | 190.62 | 11.81 | 30.84 | 2.61 |
| GODS | 85.21 | 14813.75 | 173.84 | 12.5 | 1.73 | -86.14 | 21.01 | 31.26 | 1.49 |
| HAMMY | 12.83 | 1133.5 | 88.34 | 0.02 | 0.1 | 515.64 | 685.31 | 157.93 | 0.23 |
| HNTAI | 0.0 | 3373.22 |  | 0.0 | 0.06 |  | 0.0 | 166.4 |  |
| HUNT | 160.85 | 16337.91 | 101.57 | 47.77 | 1.31 | -97.26 | 11.88 | 33.75 | 2.84 |
| ILV | 2.81 | 879.97 | 313.31 | 23.28 | 95.57 | 310.55 | 0.04 | 0.15 | 3.48 |
| ILV | 9.61 | 208.33 | 21.68 | 22.88 | 57.32 | 150.5 | 0.14 | 0.14 | 1.0 |
| IMGNAI | 1098.19 | 3631.05 | 3.31 | 0.03 | 0.08 | 142.39 | 3580.91 | 209.57 | 0.06 |
| IO | 1.16 | 2684.52 | 2318.66 | 0.0 | 0.0 | 687.52 | 9062.49 | 58027.56 | 6.4 |

| Coin Name | Avg Volume | Total Volume | Volume | Avg Price | Avg Price | Price | Avg Order Size | Avg Order Size | Order Size |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
|  | 7 Days | Pump Day | Increase % | 7 Days | Pump Day | Increase % | 7 Days | Pump Day | Increase % |
| KING | 6.71 | 817.63 | 121.86 | 0.0 | 0.0 | 241.3 | 106659.19 | 218601.67 | 2.05 |
| KING | 67.84 | 1019.11 | 15.02 | 0.0 | 0.0 | 59.85 | 339047.28 | 448642.86 | 1.32 |
| KP3R | 27.17 | 7822.04 | 287.88 | 42.06 | 434.08 | 932.01 | 0.25 | 0.13 | 0.51 |
| LAZIO | 1.31 | 1278.62 | 972.37 | 1.21 | 4.97 | 311.05 | 0.36 | 5.02 | 14.05 |
| LBR | 40.79 | 3755.86 | 92.08 | 2.19 | 7.12 | 224.99 | 3.84 | 2.73 | 0.71 |
| LBR | 27.06 | 4714.56 | 174.2 | 0.98 | 5.23 | 434.8 | 8.13 | 4.16 | 0.51 |
| LBR | 10.56 | 2738.87 | 259.39 | 0.11 | 0.16 | 38.65 | 38.97 | 95.94 | 2.46 |
| LL | 57.4 | 1840.68 | 32.07 | 0.0 | 0.0 | 250.0 | 7408374458.44 | 1485728813.41 | 0.2 |
| LMI | 12.23 | 5681.65 | 464.68 | 0.0 | 0.0 | 685.16 | 30451.7 | 25066.56 | 0.82 |
| LOOT | 62.7 | 17741.44 | 282.96 | 0.37 | 1.03 | 179.77 | 19.28 | 62.9 | 3.26 |
| LOVESNOOPY | 72.44 | 3998.51 | 55.2 | 0.0 | 0.0 | 124.53 | 689762024.85 | 272300258.87 | 0.39 |
| LOVESNOOPY | 37.81 | 1450.6 | 38.36 | 0.0 | 0.0 | 9.94 | 2250158081.0 | 15070674127.5 | 6.7 |
| LVL | 29.1 | 9067.3 | 311.61 | 0.5 | 2.42 | 388.69 | 7.46 | 16.5 | 2.21 |
| LVL | 3.66 | 808.78 | 221.0 | 0.12 | 0.33 | 165.25 | 9.93 | 31.04 | 3.12 |
| LVL | 13.77 | 1377.15 | 100.01 | 0.12 | 0.19 | 55.13 | 20.54 | 66.97 | 3.26 |
| MESSI | 51.51 | 9985.71 | 193.87 | 0.0 | 0.0 | 69.12 | 4769.0 | 11662.66 | 2.45 |
| MMT | 183.66 | 3970.58 | 21.62 | 0.29 | 0.58 | 97.06 | 29.71 | 36.26 | 1.22 |
| MMT | 513.1 | 2.17 | 0.0 | 0.42 | 0.09 | -78.5 | 38.94 | 23.86 | 0.61 |
| MMT | 249.58 | 1.29 | 0.01 | 0.27 | 0.15 | -45.1 | 48.03 | 8.62 | 0.18 |
| MOTH | 327.58 | 5.86 | 0.02 | 0.0 | 0.0 | -86.86 | 13543.53 | 6422.09 | 0.47 |
| MSN | 10.17 | 1305.62 | 128.38 | 0.05 | 0.16 | 220.52 | 99.61 | 146.9 | 1.47 |
| NCT | 0.0 | 48248.54 |  | 0.0 | 0.36 |  | 0.0 | 1666.51 |  |
| NCT | 23.3 | 428.77 | 18.41 | 0.01 | 0.02 | 257.67 | 1044.75 | 357.11 | 0.34 |
| NEBL | 14.1 | 19497.66 | 1383.1 | 0.04 | 0.23 | 493.21 | 132.31 | 140.25 | 1.06 |
| NVIR | 506.59 | 1303.71 | 2.57 | 0.1 | 0.09 | -8.62 | 280.17 | 133.69 | 0.48 |
| NYM | 3.61 | 3249.71 | 900.81 | 0.06 | 0.27 | 369.68 | 17.55 | 87.69 | 5.0 |
| NYM | 2.03 | 2526.22 | 1244.54 | 0.01 | 0.17 | 1065.1 | 20.1 | 120.2 | 5.98 |
| NYM | 0.0 | 2574.46 |  | 0.0 | 0.15 |  | 0.0 | 100.79 |  |
| NYM | 33.78 | 1082.71 | 32.05 | 0.06 | 0.13 | 100.26 | 184.76 | 63.57 | 0.34 |
| OOKI | 21.23 | 1112.43 | 52.39 | 0.0 | 0.0 | 53.73 | 7087.11 | 9317.89 | 1.31 |
| OX | 1.73 | 759.57 | 438.49 | 0.0 | 0.01 | 9052.58 | 1732.26 | 1016.2 | 0.59 |
| PAW | 153.73 | 3843.26 | 25.0 | 0.0 | 0.0 | 66.52 | 1113428.66 | 421564.3 | 0.38 |
| PLA | 13.14 | 10164.84 | 773.68 | 0.07 | 0.26 | 278.29 | 82.99 | 111.35 | 1.34 |
| PNDC | 45.77 | 6820.13 | 149.01 | 0.0 | 0.0 | 960.0 | 21270123.0 | 4703073.93 | 0.22 |
| POLIS | 0.4 | 426.23 | 1074.89 | 0.02 | 0.31 | 1813.17 | 3.46 | 20.73 | 6.0 |
| POLS | 23.96 | 1727.88 | 72.11 | 0.31 | 0.45 | 45.56 | 22.99 | 28.16 | 1.22 |
| PSG | 0.0 | 1883.2 |  | 0.0 | 10.94 |  | 0.0 | 1.78 |  |
| PSP | 1.75 | 7676.85 | 4396.93 | 0.01 | 0.25 | 2863.87 | 56.26 | 109.99 | 1.96 |
| PSP | 4.83 | 7239.31 | 1499.76 | 0.01 | 0.12 | 1510.11 | 138.92 | 126.76 | 0.91 |
| QI | 5.02 | 1844.61 | 367.74 | 0.0 | 0.01 | 95.43 | 371.4 | 1741.72 | 4.6 |
| QUICK | 17.6 | 4462.96 | 253.55 | 0.05 | 0.07 | 23.75 | 94.27 | 270.63 | 2.8 |
| QUICK | 6.99 | 958.18 | 137.02 | 0.02 | 0.07 | 216.74 | 110.35 | 203.07 | 1.8 |
| RCKT | 8.83 | 372.03 | 42.13 | 0.09 | 0.33 | 251.61 | 42.38 | 17.64 | 0.4 |
| RD | 1.23 | 10575.46 | 8597.72 | 1.94 | 115.92 | 5861.53 | 0.16 | 0.26 | 1.5 |
| REQ | 23.26 | 288.95 | 12.42 | 0.07 | 0.33 | 389.48 | 93.37 | 18.45 | 0. |
| RFD | 14.31 | 6598.62 | 461.2 | 0.0 | 0.0 | 410.55 | 1321736.0 | 1851439.76 | 1. |
| RIF | 29.77 | 2241.33 | 75.28 | 0.22 | 0.47 | 117.84 | 85.45 | 19.0 | 0.2 |
| RIF | 163.07 | 1929.9 | 11.83 | 0.1 | 0.12 | 18.84 | 331.08 | 120.01 | 0.3 |
| ROOK | 70.55 | 3340.81 | 47.35 | 0.5 | 0.63 | 27.37 | 26.16 | 41.34 | 1.5 |
| RUNE | 98.73 | 24442.09 | 247.56 | 0.95 | 3.24 | 242.11 | 33.68 | 10.55 | 0.3 |
| SANTOS | 33.63 | 7211.19 | 214.4 | 2.99 | 6.95 | 132.63 | 2.19 | 4.2 | 1.9 |
| SDAO | 22.65 | 1352.51 | 59.71 | 0.28 | 1.14 | 309.0 | 29.49 | 12.68 | 0.43 |
| SG | 127.35 | 3018.1 | 23.7 | 0.04 | 0.08 | 90.12 | 304.76 | 213.37 | 0.7 |
| SOS | 102.63 | 2482.34 | 24.19 | 0.0 | 0.0 | 93.67 | 430644828.18 | 187282370.34 | 0.43 |
| STMX | 0.0 | 904.06 |  | 0.0 | 0.01 |  | 0.0 | 2489.95 |  |
| STMX | 30.82 | 1585.6 | 51.44 | 0.01 | 0.02 | 245.63 | 1375.05 | 715.09 | 0.52 |
| SUDO | 2.25 | 6821.71 | 3025.2 | 0.21 | 0.51 | 145.15 | 4.43 | 53.14 | 12.0 |
| SUDO | 94.23 | 1182.52 | 12.55 | 0.17 | 0.25 | 43.1 | 47.42 | 41.67 | 0.88 |
| SUKU | 1.15 | 11551.54 | 10035.81 | 0.01 | 0.49 | 5666.3 | 19.18 | 79.13 | 4.13 |
| SWINGBY | 17.37 | 4351.56 | 250.5 | 0.0 | 0.0 | 1003.59 | 16000.1 | 7805.31 | 0.49 |
| TIP | 286.81 | 8083.37 | 28.18 | 0.0 | 0.0 | 112.51 | 38156.35 | 35786.16 | 0.94 |
| TIP | 127.22 | 3723.72 | 29.27 | 0.0 | 0.0 | 181.45 | 57578.57 | 53942.14 | 0.94 |
| TITAN | 1.88 | 2303.59 | 1225.26 | 0.03 | 0.07 | 141.47 | 27.12 | 244.45 | 9.01 |
| TITAN | 7.82 | 5470.46 | 699.25 | 0.0 | 0.02 | 406.68 | 608.11 | 1670.03 | 2.75 |
| TOKE | 16.19 | 8890.78 | 549.11 | 0.82 | 5.98 | 630.19 | 5.21 | 5.71 | 1.1 |
| TOKE | 0.0 | 5845.15 |  | 0.0 | 2.84 |  | 0.0 | 9.69 |  |
| TROVE | 0.28 | 15951.14 | 57627.45 | 0.0 | 0.04 | 1371.76 | 22.66 | 469.66 | 20.73 |
| UMEE | 1.91 | 8290.86 | 4350.85 | 0.0 | 0.41 | 10352.88 | 123.85 | 699.89 | 5.65 |
| USH | 1.38 | 7745.9 | 5633.01 | 0.07 | 0.37 | 442.62 | 7.19 | 53.07 | 7.38 |
| VOXEL | 2.12 | 25289.27 | 11902.45 | 0.11 | 0.81 | 602.08 | 6.63 | 53.33 | 8.04 |
| VOXEL | 0.34 | 1171.39 | 3464.32 | 0.02 | 0.31 | 1348.26 | 2.25 | 51.32 | 22.84 |
| VOXEL | 0.21 | 412.21 | 1931.2 | 0.04 | 0.29 | 565.86 | 1.49 | 22.55 | 15.15 |
| WFAI | 34.34 | 4772.56 | 138.99 | 0.0 | 0.0 | 103.44 | 428088949.41 | 480788437.25 | 1.12 |
| WIFI | 4.31 | 23947.22 | 5561.61 | 0.01 | 0.13 | 961.02 | 117.11 | 334.76 | 2.86 |
| WIFI | 3.49 | 358.76 | 102.66 | 0.03 | 0.11 | 297.87 | 38.47 | 68.96 | 1.79 |
| WIFI | 0.0 | 153.2 |  | 0.0 | 0.12 |  | 0.0 | 103.06 |  |
| WLKN | 3.93 | 14408.87 | 3669.82 | 0.01 | 0.03 | 372.03 | 188.65 | 1113.88 | 5.9 |
| WLKN | 0.0 | 394.83 |  | 0.0 | 0.01 |  | 0.0 | 1328.55 |  |
| WLKN | 7.91 | 1578.96 | 199.6 | 0.0 | 0.01 | 561.43 | 3701.47 | 5293.93 | 1.43 |
| WNCG | 3.29 | 13979.9 | 4248.17 | 0.03 | 0.29 | 994.03 | 47.89 | 131.73 | 2.75 |
| WNCG | 45.91 | 5152.96 | 112.23 | 0.08 | 0.47 | 527.98 | 91.63 | 38.36 | 0.42 |
| WPEPE | 96.55 | 1138.16 | 11.79 | 0.0 | 0.0 | 185.14 | 43234.42 | 8623.23 | 0.2 |
| ZKF | 29.1 | 970.52 | 33.36 | 0.0 | 0.0 | 67.48 | 9912.82 | 8061.38 | 0.81 |

## Appendix E Appendix: Further Suggestions for Future Work

### E-A Lag-Llama

A recent advancement in time series forecasting is the development of the Lag LLAMA model [[35](https://arxiv.org/html/2412.18848v1#bib.bib35)], which is based on the transformer architecture. This framework underlies sophisticated large language models such as ChatGPT and Claude. Transformer models excel at capturing long-range dependencies in sequential data, making them particularly suitable for a variety of predictive tasks.

Lag LLAMA has demonstrated promising results in predicting financial data [[44](https://arxiv.org/html/2412.18848v1#bib.bib44)]. However, its current application is restricted to univariate data, which limits its utility for studies such as ours that involve multivariate datasets. Future extensions of the Lag LLAMA model to support multivariate data would open the door to new opportunities. Exploring its performance in these more complex, noisy, and interdependent settings could yield valuable insights and further refine predictive capabilities.

![Mascot Sammy](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAsAAAAOCAYAAAD5YeaVAAAAAXNSR0IArs4c6QAAAAZiS0dEAP8A/wD/oL2nkwAAAAlwSFlzAAALEwAACxMBAJqcGAAAAAd0SU1FB9wKExQZLWTEaOUAAAAddEVYdENvbW1lbnQAQ3JlYXRlZCB3aXRoIFRoZSBHSU1Q72QlbgAAAdpJREFUKM9tkL+L2nAARz9fPZNCKFapUn8kyI0e4iRHSR1Kb8ng0lJw6FYHFwv2LwhOpcWxTjeUunYqOmqd6hEoRDhtDWdA8ApRYsSUCDHNt5ul13vz4w0vWCgUnnEc975arX6ORqN3VqtVZbfbTQC4uEHANM3jSqXymFI6yWazP2KxWAXAL9zCUa1Wy2tXVxheKA9YNoR8Pt+aTqe4FVVVvz05O6MBhqUIBGk8Hn8HAOVy+T+XLJfLS4ZhTiRJgqIoVBRFIoric47jPnmeB1mW/9rr9ZpSSn3Lsmir1fJZlqWlUonKsvwWwD8ymc/nXwVBeLjf7xEKhdBut9Hr9WgmkyGEkJwsy5eHG5vN5g0AKIoCAEgkEkin0wQAfN9/cXPdheu6P33fBwB4ngcAcByHJpPJl+fn54mD3Gg0NrquXxeLRQAAwzAYj8cwTZPwPH9/sVg8PXweDAauqqr2cDjEer1GJBLBZDJBs9mE4zjwfZ85lAGg2+06hmGgXq+j3+/DsixYlgVN03a9Xu8jgCNCyIegIAgx13Vfd7vdu+FweG8YRkjXdWy329+dTgeSJD3ieZ7RNO0VAXAPwDEAO5VKndi2fWrb9jWl9Esul6PZbDY9Go1OZ7PZ9z/lyuD3OozU2wAAAABJRU5ErkJggg==)
