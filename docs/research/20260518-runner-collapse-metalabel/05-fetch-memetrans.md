# MemeTrans: A Dataset for Detecting High-Risk Memecoin Launches on Solana

###### Abstract.

Launchpads have become the dominant mechanism for issuing memecoins on blockchains due to their fully automated, no-code creation process. This new issuance paradigm has led to a surge in high-risk token launches, causing substantial financial losses for unsuspecting buyers. In this paper, we introduce MemeTrans, the first dataset for studying and detecting high-risk memecoin launches on Solana. MemeTrans covers over 40k memecoin launches that successfully migrated to the public Decentralized Exchange (DEX), with over 30 million transactions during the initial sale on launchpad and 180 million transactions after migration. To precisely capture launch patterns, we design 122 features spanning dimensions such as context, trading activity, holding concentration, and time-series dynamics, supplemented with bundle-level data that reveals multiple accounts controlled by the same entity. Finally, we introduce an annotation approach to label the risk level of memecoin launches, which combines statistical indicators with a manipulation-pattern detector. Experiments on the introduced high-risk launch detection task suggest that designed features are informative for capturing high-risk patterns and ML models trained on MemeTrans can effectively reduce financial loss by 56.1%. Our dataset, experimental code, and pipeline are publicly available at: <https://github.com/git-disl/MemeTrans>.

## 1. Introduction

In internet culture, a meme refers to a humorous or imitative piece of content, such as an image, phrase, or symbol that spreads rapidly across online communities (Davison, [2012](https://arxiv.org/html/2602.13480v1#bib.bib39 "The language of internet memes")). In the field of cryptocurrency and blockchain, a memecoin is a digital token that embodies an Internet meme that lacks intrinsic value or technical utility (Investopedia, [2024](https://arxiv.org/html/2602.13480v1#bib.bib18 "The hidden dangers of buying meme coins"); Xiang et al., [2025](https://arxiv.org/html/2602.13480v1#bib.bib41 "Measuring memecoin fragility")). Due to minimal intrinsic utility, emotion-driven trading, and low entry barrier, the memecoin market exhibits extreme price volatility and very short life cycles, often rising and collapsing within hours (Conlon and Corbet, [2025](https://arxiv.org/html/2602.13480v1#bib.bib40 "Memecoin contagion: irrationality, illicit behaviour, and cryptocurrency risk"); Cernera et al., [2023](https://arxiv.org/html/2602.13480v1#bib.bib22 "Token spammers, rug pulls, and sniper bots: an analysis of the ecosystem of tokens in ethereum and in the binance smart chain ({{{{{bnb}}}}})")). Such conditions create fertile ground for increasing fraudulent activities ([M. La Morgia, A. Mei, F. Sassi, and J. Stefa (2021b)](https://arxiv.org/html/2602.13480v1#bib.bib15 "The doge of wall street: analysis and detection of pump and dump cryptocurrency manipulations"); [28](https://arxiv.org/html/2602.13480v1#bib.bib19 "Memecoin contagion: irrationality, illicit behaviour, and market manipulation")). In 2024 alone, investors lost more than $500 million to memecoin-related scams (CoinDesk, [2024](https://arxiv.org/html/2602.13480v1#bib.bib17 "Crypto investors lost over $500m in memecoin rug pulls and scams in 2024")).

Since early 2024, the emergence of launchpads has substantially accelerated the growth of the memecoin ecosystem. By October 2025, the largest launchpad Pump.fun had launched 12.8 million memecoins on Solana, accounting for about 50% of all tokens created on Solana since its appearance. It also captured around 85% of the total market value of launchpad-issued tokens (Research, [2025](https://arxiv.org/html/2602.13480v1#bib.bib34 "The state of memecoins")). A launchpad provides a web interface where anyone can create and sell a token without writing code or managing liquidity. When a user creates a new coin, the launchpad automatically initializes a bonding-curve sale, allowing users to buy tokens at gradually increasing prices as shown in Figure [1](https://arxiv.org/html/2602.13480v1#S1.F1 "Figure 1 ‣ 1. Introduction ‣ MemeTrans: A Dataset for Detecting High-Risk Memecoin Launches on Solana")(a). Once the sale reaches a certain threshold, liquidity is automatically migrated to decentralized exchanges (DEX), where the token becomes publicly tradable. This automated pipeline removes nearly all technical barriers to launching a token, lowering the threshold for fraudulent activities (CoinDesk, [2025](https://arxiv.org/html/2602.13480v1#bib.bib35 "Pump.fun hits back at report that claimed 98% of memecoins on the platform are fraudulent")).

![Refer to caption](Figure/toy_example.png)

Related Work: Previous studies on memecoins primarily focus on DEX-based rug pulls (Cernera et al., [2023](https://arxiv.org/html/2602.13480v1#bib.bib22 "Token spammers, rug pulls, and sniper bots: an analysis of the ecosystem of tokens in ethereum and in the binance smart chain ({{{{{bnb}}}}})"); Mazorra et al., [2022](https://arxiv.org/html/2602.13480v1#bib.bib25 "Do not rug on me: zero-dimensional scam detection")), where creators withdraw liquidity from DEX liquidity pools after attracting buyers. These approaches rely on detecting anomaly operations in liquidity pool-level controls, such as sudden removals or LP token burns to identify high-risk exits (Yaremus et al., [2025](https://arxiv.org/html/2602.13480v1#bib.bib27 "Detecting rug pulls in decentralized exchanges: machine learning evidence from the ton blockchain")). However, token liquidity is now held and managed entirely by the launchpad during the launchpad sale, and creators thus no longer possess direct authority over the liquidity pool, rendering existing studies ineffective.

Moreover, the launchpads give rise to a new form of threat. As shown in Figure [1](https://arxiv.org/html/2602.13480v1#S1.F1 "Figure 1 ‣ 1. Introduction ‣ MemeTrans: A Dataset for Detecting High-Risk Memecoin Launches on Solana"), early buyers accumulate tokens at the lowest tiers of the bonding curve. After migrating to a DEX and gaining broader exposure, they begin selling their low-cost holdings, leaving normal buyers with devalued tokens. As a result, indicators of high-risk memecoins now manifest primarily during the initial launchpad sale, including highly concentrated holding distributions, multi-address coordination, and suspicious wash-trading behaviors. However, these patterns are largely absent from existing literature due to the recent emergence of launchpads. Only a limited number of studies (Voinea, [2025](https://arxiv.org/html/2602.13480v1#bib.bib32 "Pump. fun and meme-coins: a case study in the legal commodification of ponzi-like tokenomics"); Li et al., [2025](https://arxiv.org/html/2602.13480v1#bib.bib24 "Trust dynamics and bot-driven responses: an approach to rug pulls in solana meme coin markets")) provide economic or sociological analyses, without a systematic investigation or detection of this new class of threats.

Scope and Contributions: We present MemeTrans, the first dataset tailored to study emerging high-risk memecoin launches on Solana. The construction of MemeTrans consists of five components:
(1) Memecoins. We collect 41,470 memecoins that completed their launchpad sales and were successfully migrated to DEXs between Dec. 2024, and Mar. 2025. (2) Transactions: we collect and parse over 200 million transactions from the launchpad sale and subsequent DEX trading. (3) Bundle traces: we aggregate bundle-trace data from multiple sources to reveal relationships among accounts controlled by the same entities. (4) Features: we design 122 features to capture characteristics and trading patterns of memecoin launches across five feature groups. (5) Labels: we introduce a hybrid annotation approach that combines statistical indicators with an ML-based manipulation detector to assign each token launch a risk level.

Based on MemeTrans, several interesting observations are made: high-risk memecoin launches tend to exhibit a shorter duration of the launchpad sale, with fewer transactions and buyers but larger per-buyer token accumulations, compared to lower-risk memecoin launches. The holding concentrations of high-risk memecoins are more skewed, as the earliest buyers acquire a substantial portion of the supply and more likely use bundled accounts to conceal the true holding distribution. These observations suggest that the launchpad sale provides meaningful signal for predicting whether a token will cause losses for normal buyers after being listed on DEXs, i.e., the high-risk memecoin detection.

Finally, we benchmark two families of ML models on the introduced high-risk memecoin detection task: tabular feature–based classifiers and time-series models. To assess the contribution of feature design, we conduct feature ablation studies and observe consistent performance degradation when any group is removed, indicating that the designed features provide informative signals. We further evaluate a practical application in which model predictions are translated into simple memecoin-selection strategies. Using a trained MLP as an example, integrating its risk scores into trading decisions can reduce investment losses by up to 56%, demonstrating that MemeTrans offers practical value for real-world risk mitigation.

This paper makes the following contributions:

Dataset. We introduce MemeTrans, the first large-scale dataset for studying high-risk memecoin launches on Solana, covering over 41k launches and 200M+ transactions, with bundled account traces that reveal hidden multi-account coordination.

Features and Labels. We design 122 features capturing launchpad trading behavior, holding concentration, and bundle statistics, and propose a hybrid annotation scheme that assigns risk levels to memecoin launches.

Benchmark and Impact. We benchmark representative ML models on the high-risk memecoin detection task and show that models trained on MemeTrans can reduce investment losses by up to 56%, demonstrating practical risk-mitigation value.

## 2. Terminology

Account and Transaction. On Solana, an *account* is the basic container for on-chain state and balances ([Solana Documentation,](https://arxiv.org/html/2602.13480v1#bib.bib53 "Accounts — solana core concepts") ). We distinguish between *user accounts*, which are externally controlled and hold SOL and tokens, and *program accounts*, which store on-chain executable logic.
A *transaction* is executed atomically and invokes one or more program accounts to read and modify a set of explicitly listed accounts ([Solana Documentation,](https://arxiv.org/html/2602.13480v1#bib.bib52 "Transactions — solana core concepts") ). In our dataset, transactions primarily include user-to-user transfers of SOL or SPL tokens, as well as interactions with on-chain programs such as token buys and sells via the bonding-curve program during the launchpad sale, and via the DEX AMM program (e.g., Raydium) after migration.

Token and Mint Address.
On Solana, memecoins follow the SPL Token standard and are represented as fungible on-chain assets.
Each memecoin is uniquely identified by a mint address, which serves as its global identifier.
User accounts maintain separate token balances for each mint they hold, with each balance recorded in a distinct token account.
Throughout this paper, a *memecoin* denotes a specific token type defined by a mint address, whereas *token(s)* refer to the corresponding token balances or instances held by user accounts.

Bonding Curve. During the launchpad sale, users trade directly with the launchpad’s bonding-curve program rather than through an order book. A bonding curve sets the posted price as a deterministic, monotonically non-decreasing function of the cumulative quantity sold, P=P​(q)P=P(q), so the price depends only on the remaining inventory (dYdX Foundation, [2024](https://arxiv.org/html/2602.13480v1#bib.bib42 "What are bonding curves, and how do they work?")).
In Pump.fun, the curve is discretized into stepwise tiers P0<P1<⋯P\_{0}<P\_{1}<\cdots with a fixed token allocation per tier.
Each purchase consumes inventory at the current tier; once that tier is exhausted, the sale advances to the next, higher-priced tier.
As a result, early-tier buyers pay substantially lower unit prices than later participants, which strongly amplifies the advantage of insiders and sniper bots.

Automated Market Maker (AMM). After migration to a DEX, memecoin trading is maintained by an AMM program instead of a bonding-curve program. Specifically, a constant-product AMM such as Uniswap or Raydium maintains reserves (x,y)(x,y) of two assets (here, memecoin and SOL) and enforces the invariant x⋅y=kx\cdot y=k (Uniswap Labs, [2018](https://arxiv.org/html/2602.13480v1#bib.bib43 "Uniswap v1 protocol overview")).
The spot price (SOL per token) is p=y/xp=y/x, and a trade that adds Δ​x\Delta x tokens and removes Δ​y\Delta y SOL must satisfy (x+Δ​x)​(y−Δ​y)=k(x+\Delta x)(y-\Delta y)=k.
This pricing rule makes the execution price an explicit function of trade size and current pool depth: large, well-funded pools exhibit smaller price impact per trade, whereas shallow pools experience large price swings for the same order size.

## 3. The Lifetime of a High-Risk Memecoin

Figure [2](https://arxiv.org/html/2602.13480v1#S3.F2 "Figure 2 ‣ 3. The Lifetime of a High-Risk Memecoin ‣ MemeTrans: A Dataset for Detecting High-Risk Memecoin Launches on Solana") summarizes the typical lifecycle of a memecoin launched through Pump.fun and explains why early trading behaviors during the launchpad sale can strongly influence post-migration trading outcomes.

Stage 1: Creation. A developer creates a new memecoin on the launchpad. The launchpad program holds the token supply and exposes buy/sell functions through a bonding-curve mechanism.

Stage 2: Launchpad (bonding-curve) sale. Users buy tokens directly from the bonding-curve program, where the price increases deterministically as more tokens are sold. The bonding-curve mechanism gives a significant first-mover advantage to the earliest buyers: insiders (i.e., developer or developer-affiliated accounts) or automated “sniper” bots can enter within seconds and accumulate a large inventory at the lowest price tiers. As the sale progresses, later participants pay higher prices and often face an already concentrated holding distribution.

Stage 3: Migration. Once the sale reaches a predefined threshold (80% tokens are sold), the launchpad migrates liquidity to a DEX AMM pool by transferring the remaining tokens and the collected base asset (e.g., SOL). After migration, the memecoin becomes visible to broader market participants through DEX interfaces and aggregators, which typically increases attention and trading activity.

Stage 4: DEX Trading. Once migration completes, the price and trading volume typically rises to a peak during this stage due to heightened market hype and speculative demand. At the same time, early buyers can sell their low-cost inventory to the liquidity pool. Such sell pressure can rapidly drain the pool’s base asset and cause large drawdowns for later buyers (Figure [2](https://arxiv.org/html/2602.13480v1#S3.F2 "Figure 2 ‣ 3. The Lifetime of a High-Risk Memecoin ‣ MemeTrans: A Dataset for Detecting High-Risk Memecoin Launches on Solana")). In practice, high-risk launches often exhibit either abrupt collapses, or slower “distribution” patterns that maintain non-trivial activity while gradually moving price downward.

![Refer to caption](x1.png)
![[Uncaptioned image]](x2.png)

## 4. Dataset Construction

Because the bonding-curve sale largely determines who acquires inventory cheaply and how concentrated holdings become, many risk signals (e.g., early-buyer accumulation, short sale duration, coordinated multi-account buying) are already observable before the migration. This motivates our dataset design, which focuses on extracting launchpad-sale behaviors to predict whether a newly migrated memecoin is likely to incur post-migration losses for normal buyers.

MemeTrans tracks the complete lifecycle of memecoins issued through Pump.fun from December 1, 2024 to March 1, 2025. The dataset construction pipeline consists of five stages: (1) Memecoin Collection: we collect tokens that completed migration from the launchpad to DEX, along with their on-chain metadata. (2) Transaction Collection: For each token, we collect and parse on-chain transactions during the launchpad sale and after migration. (3) Bundle Data Collection: we reveal bundled account pairs that used to conceal multi-account holdings with three heuristics. (4) Feature Engineering: we design five categories of feature to capture the pattern of memecoin launches. (5) Annotation: we introduce a hybrid annotation method to assign each token a risk-level label, which includes a statistical indicator and a ML-based score model.

### 4.1. Memecoin Collection

We first collect the transactions that trigger the launchpad (Pump.fun) to the DEX (Raydium) within the time window. Specifically, we identify transactions initiated by the official Pump.fun creator account11139azUYFWPz3VHgKCf3VChUwbpURdCHRxjWVowf5jUJjg that transfer SOL to the Raydium fee account2227YttLkHDoNj9wyDur5pM1ejNaAvT9X4eqaYcHQqtj2G5, indicating the creation of a new liquidity pool on Raydium. From execution logs recorded within the migration transaction, we then get the mint address of token, and the address of the DEX AMM that receives both SOL and the token.

For every token’s mint address, we locate the token’s associated metadata account using Solana’s deterministic address-derivation rule ([29](https://arxiv.org/html/2602.13480v1#bib.bib37 "Program derived addresses")), which is a program-derived address (PDA) derived from the mint address under the Metaplex Token Metadata program. This metadata account stores demographic information such as the token name, symbol, and the Uniform Resource Identifier (URI) that points to the off-chain JSON metadata file. The URI typically resolves to additional descriptive fields, including the token’s description, image link, and social handles (e.g., website, Twitter, or Telegram). The token launch data are summarized as token\_launch.csv in Table [1](https://arxiv.org/html/2602.13480v1#S3.T1 "Table 1 ‣ 3. The Lifetime of a High-Risk Memecoin ‣ MemeTrans: A Dataset for Detecting High-Risk Memecoin Launches on Solana"). We report the statistics of the token data in Table [2](https://arxiv.org/html/2602.13480v1#S4.T2 "Table 2 ‣ 4.2. Transaction Collection ‣ 4. Dataset Construction ‣ MemeTrans: A Dataset for Detecting High-Risk Memecoin Launches on Solana").

### 4.2. Transaction Collection

For each token mint, we collect on-chain transactions involving the memecoin. Pre-migration transactions are those occurring from the creation time up to the migration time, while post-migration transactions are those occurring from the migration time to one hour afterwards. The transactions are collected using the Google BigQuery public dataset for Solana333<https://console.cloud.google.com/marketplace/product/solana-public/crypto-solana-mainnet>.

Transaction Parsing: Raw transactions are heterogeneous and unstructured at the function level, with different purposes such as token creation, buying or selling tokens through programs, or token transfers between user accounts. Even token purchases can be executed through different ways, including bonding-curve programs, DEX AMM programs, or aggregators that route across multiple liquidity sources.

To maintain analytical simplicity, we introduce a transaction parser based on balance changes rather than on complex transaction logs. The key idea is to compute the net balance changes of all accounts to determine whether the token flow occurs between user accounts (transfer), between a user and a liquidity pool (swap), involves buy and sell swaps within the single transaction (wash trade), or is newly created from scratch (mint).
In our dataset, premigration transactions are used for feature engineering, therefore we retain all the types of transactions and report the breakdown of pre-migration transactions in Table [3](https://arxiv.org/html/2602.13480v1#S4.T3 "Table 3 ‣ 4.2. Transaction Collection ‣ 4. Dataset Construction ‣ MemeTrans: A Dataset for Detecting High-Risk Memecoin Launches on Solana"), where ”create & buy” indicates that creation and buy appear in the same transaction. As we can observe, the majority of transactions are normal swaps and 21.4% of transactions are wash trades. While among all ”mint” transactions, ”create & buy” accounts for 98.7%, suggesting that almost all the developers initiate token purchases within the same transaction as minting, indicating that they tend to pre-acquire inventory at the earliest price tiers.

|  |  |
| --- | --- |
| Descriptions | Statistics |
| Start date (yyyy/mm/dd, UTC) | 2024/12/01 |
| End date (yyyy/mm/dd, UTC) | 2025/03/01 |
| # of memecoins | 41,470 |
| Overall Transactions |  |
| Total | 218,530,716 |
| Average per memecoin | 4,841 |
| Pre-migration Transactions |  |
| Total | 30,833,503 |
| Average per memecoin | 743 |
| Post-migration Transactions |  |
| Total | 187,697,213 |
| Average per memecoin | 4,098 |
| Unique Accounts |  |
| Pre-migration | 1,916,363 |
| Post-migration | 6,538,577 |

| Type | Count | Percentage (%) |
| --- | --- | --- |
| Create | 543 | 0.00 |
| Create & Buy | 40,927 | 0.13 |
| Swap (buy/sell) | 22,668,222 | 73.52 |
| Wash trade | 6,599,095 | 21.40 |
| Transfer | 1,524,716 | 4.94 |

| Data Type | Bundle Holder Ratio | Bundle Holding Pct |
| --- | --- | --- |
| In-transaction | 6.46% | 9.16% |
| Fund-flow | 22.57% | 28.22% |
| Jito Bundle | 10.39% | 15.96% |
| All | 28.13% | 36.50% |

| Feature Group | Description | Representative Features |
| --- | --- | --- |
| Contextual information | Launch-time context of the token (e.g., SOL price and calendar time). | SOL\_price, migrate\_weekday, migrate\_hour, migrate\_month, etc. |
| Holding concentration | Concentration of token distribution and early-trader behavior (developers, sniper bots). | dev\_hold\_pct, sniper\_hold\_pct, top10\_hold\_pct, early\_top10\_hold\_pct, etc. |
| Market activity | Pre-migration trading activity, including trader participation, volume, and wash trading signals. | tx\_num, time\_span, trader\_num, holder\_num, buy\_num, sell\_num, etc. |
| Bundle statistics | Holding and trading statistics after clustering addresses into bundles. | bundle\_hold\_pct, bundle\_num, bundle\_account\_num, top10\_hold\_pct, early\_top10\_hold\_pct, etc. |
| Time-series | Price and volume time-series before migration. | open\_price, end\_price, avg\_price, volume, etc. |

### 4.3. Bundle Data Collection

Insiders often hold tokens across multiple accounts to mask the true holding concentration and avoid deterring later buyers. Identifying these bundled accounts controlled by the same users allows us to reveal the actual holding concentration. We collect the bundled account dataset from three sources:

(1) In-transaction Multi-account Purchase: As blockchain transactions are executed atomically, some insiders use multiple addresses within the same transaction to purchase tokens in order to secure a low price. Multi-accounts within the same swap transaction can be considered as bundled accounts.

(2) Fund-flow Relationship: On Solana, creating a new user account requires an initial balance to cover rent, so accounts funded by the same funder often suggest common ownership. A notable exception arises when the funder is a centralized exchange, which typically reflects a user withdrawing funds to a newly created wallet. Such cases are therefore excluded.

(3) Jito Bundle ID: Jito is a widely used block relay on Solana that enables bundled execution of transactions within a block (Jito Foundation, [2024](https://arxiv.org/html/2602.13480v1#bib.bib44 "Jito mev documentation")). As a result, transactions sharing the same Jito bundle ID are strongly indicative of being submitted by the same entity. In practice, for each pre-migration swap transaction, we retrieve its bundle ID from the Jito Explorer via a web crawler.444<https://explorer.jito.wtf/>

Bundle data are organized as (user account, identifier) tuples, where the identifier can be a transaction ID, a funder address, or a Jito bundle ID. For each memecoin launch, we cluster user accounts involved in the launchpad sale into bundles by matching identifier values and merge overlapping bundles. Table [4](https://arxiv.org/html/2602.13480v1#S4.T4 "Table 4 ‣ 4.2. Transaction Collection ‣ 4. Dataset Construction ‣ MemeTrans: A Dataset for Detecting High-Risk Memecoin Launches on Solana") reports the ratio of bundled accounts in holders and the holding percentage of bundled accounts. As we can observe, a considerable portion (36.5%) of the total token supply is held by the bundled accounts.

### 4.4. Feature Engineering

All features are computed strictly using data (transactions, bundle data) before migration, with post-migration data used only for annotation. Specifically, we construct 122 features grouped into five categories to characterize launchpad-sale behaviors. As shown in Table [5](https://arxiv.org/html/2602.13480v1#S4.T5 "Table 5 ‣ 4.2. Transaction Collection ‣ 4. Dataset Construction ‣ MemeTrans: A Dataset for Detecting High-Risk Memecoin Launches on Solana"), the feature groups are summarized as follows:
(1) The contextual information feature group captures launch-time context for each memecoin, including the SOL price and migration time.
(2) The holding concentration feature group characterizes the degree of concentration in token distribution among holders and early traders, including the creator and snipers.
(3) The market activity feature group summarizes trading statistics of the launchpad sale, such as the sale duration and the numbers of transactions, holders, and traders.
(4) The bundle statistics feature group captures true holding concentration after revealing bundled account relationships.
(5) The time-series feature group captures temporal price and trading-volume dynamics before migration.

### 4.5. Risk Level Annotation

We annotate each memecoin with a risk-level label based on its performance during DEX trading. The annotation method combines a statistical indicator and an ML-based model.

Statistical Indicator: Price movements of memecoins are inherently noisy, as they are influenced not only by insiders’ sell-offs but also by post-migration buying activity from external traders. However, when a substantial price drop occurs shortly after migration, it is more likely to be driven by insiders unwinding their low-cost inventory rather than by longer-term market dynamics. Therefore, we define the min\_price\_ratio as the minimum token price observed within yy minutes after migration, normalized by the migration price. The choice of the time window yy reflects a trade-off. If yy is too small, insiders may not yet have completed their sell-offs. If yy is too large, price declines may increasingly reflect the natural decay of speculative attention and trading interest in memecoins, making it difficult to isolate insider-driven effects. Through empirical analysis on real-world data, we find that y=20y=20 minutes provides a reasonable balance between these two effects. As shown in Table [6](https://arxiv.org/html/2602.13480v1#S4.T6 "Table 6 ‣ 4.5. Risk Level Annotation ‣ 4. Dataset Construction ‣ MemeTrans: A Dataset for Detecting High-Risk Memecoin Launches on Solana"), more than 73% of memecoins experience a price drop to below 40% of their migration price within the window.

| Value Range | Memecoin # | Percentage |
| --- | --- | --- |
| [0.0,0.2)[0.0,0.2) | 24988 | 60.26% |
| [0.2,0.4)[0.2,0.4) | 5265 | 12.70% |
| [0.4,0.6)[0.4,0.6) | 3315 | 7.99% |
| [0.6,0.8)[0.6,0.8) | 2991 | 7.21% |
| [0.8,1.0)[0.8,1.0) | 2756 | 6.65% |
| [1.0,1.0][1.0,1.0] | 2155 | 5.20% |

![Refer to caption](x3.png)

ML-based Manipulation Detector: The statistical indicator fails to capture a common class of manipulative schemes in which a manipulator holds a large fraction of the supply and actively manages the price so that m​i​n​\_​p​r​i​c​e​\_​r​a​t​i​omin\\_price\\_ratio remains high. Specifically, a memecoin is labeled as manipulated if its post-migration price-volume trajectory exhibits recurring, structured sell-buy cycles. Figure [3](https://arxiv.org/html/2602.13480v1#S4.F3 "Figure 3 ‣ 4.5. Risk Level Annotation ‣ 4. Dataset Construction ‣ MemeTrans: A Dataset for Detecting High-Risk Memecoin Launches on Solana")(b) illustrates a typical pattern: when normal buyers purchase tokens, the manipulator sells tokens to push the price downward. Then, once those buyers begin selling at a loss, the manipulator buys tokens to drive the price back up. Figure [3](https://arxiv.org/html/2602.13480v1#S4.F3 "Figure 3 ‣ 4.5. Risk Level Annotation ‣ 4. Dataset Construction ‣ MemeTrans: A Dataset for Detecting High-Risk Memecoin Launches on Solana")(c) further shows that such manipulation can remain for a long period. In contrast, normal market activity is usually driven by diverse participants and exhibits less synchronized price reversals, as shown in Figure [3](https://arxiv.org/html/2602.13480v1#S4.F3 "Figure 3 ‣ 4.5. Risk Level Annotation ‣ 4. Dataset Construction ‣ MemeTrans: A Dataset for Detecting High-Risk Memecoin Launches on Solana")(a).

Fortunately, this type of manipulation is identifiable by humans, as it is typically carried out by bots with pre-programmed trading patterns. We adopt an ML model for manipulation detection: First, based on the above trajectory-level evidence, we manually annotate 1,555 memecoins, including 599 manipulated and 956 non-manipulated cases. We release the labeled manipulation dataset to facilitate future research. Second, we split the dataset with 70% training set and 30% testing set, and train a Temporal Convolutional Network (TCN) for binary classification555The hyper-parameters of TCN model can be found at Appendix A (Table LABEL:tab:tcn\_parameter). After training, the model outputs a prediction score s∈[0,1]s\in[0,1] for each time-series input as the probability of manipulative schemes. We report the evaluation results on the testing set in Table [7](https://arxiv.org/html/2602.13480v1#S4.T7 "Table 7 ‣ 4.5. Risk Level Annotation ‣ 4. Dataset Construction ‣ MemeTrans: A Dataset for Detecting High-Risk Memecoin Launches on Solana"). The model reaches a strong performance, reaching approximately 90% accuracy with a prediction threshold of 0.5, suggesting that it provides a reliable signal for real-world applications.

|  |  |  |  |  |  |
| --- | --- | --- | --- | --- | --- |
| Metric | Accuracy | Precision | Recall | F1 | AUC |
| Value | 0.8785 | 0.8764 | 0.8537 | 0.8649 | 0.9320 |

Annotation Rule. We introduce a default annotation rule, which can be easily configured depending on what level of risks that researchers aim to detect. In our case, the rule is defined as follows:

High-risk: A memecoin’s risk level is marked as high if it triggers any of the following conditions:

min\_price\_ratio<0.3\texttt{min\\_price\\_ratio}<0.3 (severe liquidity collapse)

pred\_score≥0.7\texttt{pred\\_score}\geq 0.7 (very likely manipulated)

Low-risk:
A memecoin’s risk level is marked as low only if it satisfies all of the following stability conditions:

min\_price\_ratio≥0.7\texttt{min\\_price\\_ratio}\geq 0.7

pred\_score<0.3\texttt{pred\\_score}<0.3

Medium-risk: Memecoins that do not meet the low-risk criteria and do not trigger any high-risk condition
are classified as medium-risk.

Table [8](https://arxiv.org/html/2602.13480v1#S4.T8 "Table 8 ‣ 4.5. Risk Level Annotation ‣ 4. Dataset Construction ‣ MemeTrans: A Dataset for Detecting High-Risk Memecoin Launches on Solana") reports the distribution of token launches under this rule. We observe that the majority of tokens (82.44%) fall into the high-risk region, indicating that most memecoins are likely to cause financial losses for normal buyers.

| Risk Level | Count | Percentage |
| --- | --- | --- |
| High | 34,890 | 84.13% |
| Medium | 4,702 | 11.34% |
| Low | 1,878 | 4.53% |

![Refer to caption](x4.png)

### 4.6. Observations

Based on the collected dataset, we observe that high-risk memecoins exhibit distinct patterns during the launchpad sale. First, as shown in Figure [4](https://arxiv.org/html/2602.13480v1#S4.F4 "Figure 4 ‣ 4.5. Risk Level Annotation ‣ 4. Dataset Construction ‣ MemeTrans: A Dataset for Detecting High-Risk Memecoin Launches on Solana")(e) and (f), the first buyers of high-risk tokens accumulated a much larger share of the supply than medium- and low-risk memecoins. According to statistics, the first 10 and 20 buyers of high-risk tokens hold 17 and 19 percentage points more of the supply than those of low-risk tokens. Consequently, when they reach the migration point, high-risk tokens tend to exhibit more concentrated holding distributions, as shown in Figure [4](https://arxiv.org/html/2602.13480v1#S4.F4 "Figure 4 ‣ 4.5. Risk Level Annotation ‣ 4. Dataset Construction ‣ MemeTrans: A Dataset for Detecting High-Risk Memecoin Launches on Solana")(g).

Second, since a substantial portion of the high-risk token supply has already been acquired by early buyers, it is easier and faster for high-risk tokens to reach the migration requirement. As a result, high-risk memecoin launches tend to have shorter time spans, as shown in Figure [4](https://arxiv.org/html/2602.13480v1#S4.F4 "Figure 4 ‣ 4.5. Risk Level Annotation ‣ 4. Dataset Construction ‣ MemeTrans: A Dataset for Detecting High-Risk Memecoin Launches on Solana")(a), and fewer buy transactions as shown in Figure [4](https://arxiv.org/html/2602.13480v1#S4.F4 "Figure 4 ‣ 4.5. Risk Level Annotation ‣ 4. Dataset Construction ‣ MemeTrans: A Dataset for Detecting High-Risk Memecoin Launches on Solana"). Meanwhile, the average buy volume of high-risk memecoins is much larger than that of low-risk memecoins, shown in Figure [4](https://arxiv.org/html/2602.13480v1#S4.F4 "Figure 4 ‣ 4.5. Risk Level Annotation ‣ 4. Dataset Construction ‣ MemeTrans: A Dataset for Detecting High-Risk Memecoin Launches on Solana")(d), and the number of holders at the migration point is smaller, as shown in Figure [4](https://arxiv.org/html/2602.13480v1#S4.F4 "Figure 4 ‣ 4.5. Risk Level Annotation ‣ 4. Dataset Construction ‣ MemeTrans: A Dataset for Detecting High-Risk Memecoin Launches on Solana")(b).

Finally, in Figure [4](https://arxiv.org/html/2602.13480v1#S4.F4 "Figure 4 ‣ 4.5. Risk Level Annotation ‣ 4. Dataset Construction ‣ MemeTrans: A Dataset for Detecting High-Risk Memecoin Launches on Solana")(h), we re-calculate the top-10 holding percentage after grouping shares into bundled accounts controlled by same users. Comparing Figure [4](https://arxiv.org/html/2602.13480v1#S4.F4 "Figure 4 ‣ 4.5. Risk Level Annotation ‣ 4. Dataset Construction ‣ MemeTrans: A Dataset for Detecting High-Risk Memecoin Launches on Solana")(g) and (h), we observe that the median holding percentages increase by 24%, 9%, and 6% for high-, medium-, and low-risk tokens, respectively. This suggests that insiders of high-risk tokens are more likely to use bundled accounts to conceal their true holding concentration.

To summarize, high-risk tokens display launch patterns that differ markedly from those of medium- and low-risk tokens, which demonstrates the feasibility of detecting high-risk token launches to mitigate financial loss.

|  |  |  |  |  |  |  |  |  |  |  |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Model | AUPRC | Label=0 (normal) | | | Label=1 (high-risk) | | | Macro | | |
| Precision | Recall | F1 | Precision | Recall | F1 | Precision | Recall | F1 |
| Random | 0.2589 | 0.2589 | 0.2589 | 0.2589 | 0.7411 | 0.7411 | 0.7411 | 0.5000 | 0.5000 | 0.5000 |
| LR | 0.5338 | 0.5122 | 0.5441 | 0.5277 | 0.8358 | 0.8175 | 0.8265 | 0.6740 | 0.6808 | 0.6771 |
| RF | 0.5688 | 0.5444 | 0.5766 | 0.5600 | 0.8477 | 0.8300 | 0.8387 | 0.6960 | 0.7033 | 0.6994 |
| XGBoost | 0.5636 | 0.5264 | 0.5482 | 0.5371 | 0.8385 | 0.8263 | 0.8323 | 0.6824 | 0.6872 | 0.6847 |
| LightGBM | 0.5642 | 0.5360 | 0.5452 | 0.5406 | 0.8388 | 0.8337 | 0.8363 | 0.6874 | 0.6895 | 0.6884 |
| MLP | 0.5729 | 0.5450 | 0.5695 | 0.5570 | 0.8459 | 0.8325 | 0.8391 | 0.6954 | 0.7010 | 0.6981 |
| GRU | 0.4972 | 0.4913 | 0.5186 | 0.5046 | 0.8270 | 0.8108 | 0.8189 | 0.6567 | 0.6680 | 0.6613 |
| LSTM | 0.5023 | 0.4895 | 0.5393 | 0.5132 | 0.8317 | 0.8019 | 0.8165 | 0.6606 | 0.6706 | 0.6649 |
| TCN | 0.4844 | 0.4847 | 0.5074 | 0.4958 | 0.8236 | 0.8100 | 0.8167 | 0.6542 | 0.6587 | 0.6563 |
| Transformer | 0.4841 | 0.4658 | 0.4920 | 0.4786 | 0.8174 | 0.8013 | 0.8093 | 0.6416 | 0.6466 | 0.6439 |
| MLP+RF | 0.5804 | 0.5572 | 0.5701 | 0.5636 | 0.8473 | 0.8404 | 0.8438 | 0.7023 | 0.7052 | 0.7037 |
| MLP+LightGBM | 0.5821 | 0.5561 | 0.5683 | 0.5622 | 0.8467 | 0.8402 | 0.8435 | 0.7014 | 0.7043 | 0.7028 |
| MLP+LSTM | 0.5827 | 0.5490 | 0.5730 | 0.5607 | 0.8466 | 0.8427 | 0.8446 | 0.6958 | 0.7079 | 0.7027 |

## 5. High-Risk Memecoin Detection

To test the utility of MemeTrans, we introduce a new detection task that predicts whether a newly migrated memecoin is high risk after migration. For this task, we label high-risk memecoins as category 1, and medium- and low-risk memecoins as category 0 for training and testing. In our experiments, we exclude memecoins with a launchpad sale duration shorter than one minute or fewer than 100 holders, since 94.9% of these cases fall into the high-risk category. This filtering mirrors simple screening rules commonly used by traders to discard low-quality memecoins and, in practice, also helps mitigate class imbalance.
Table [10](https://arxiv.org/html/2602.13480v1#S5.T10 "Table 10 ‣ 5. High-Risk Memecoin Detection ‣ MemeTrans: A Dataset for Detecting High-Risk Memecoin Launches on Solana") summarizes the statistics of the resulting dataset used in our task.

Objective Function:
Because the classes are highly imbalanced, we use a class-weighted binary cross-entropy loss:

|  |  |  |
| --- | --- | --- |
|  | ℒ​(θ)=−∑i=1N[w1​yi​log⁡pθ​(xi)+w0​(1−yi)​log⁡(1−pθ​(xi))],\mathcal{L}(\theta)=-\sum\_{i=1}^{N}\big[w\_{1}\,y\_{i}\log p\_{\theta}(x\_{i})+w\_{0}\,(1-y\_{i})\log(1-p\_{\theta}(x\_{i}))\big], |  |

where w1w\_{1} and w0w\_{0} are class weights chosen to be inversely proportional to the number of samples in each class. This ensures that the minority class receives proportionally more weight during training, preventing the model from being dominated by the majority class.

| Risk Level | Memecoin # | Percentage | Label |
| --- | --- | --- | --- |
| High | 16,048 | 74.18% | 1 |
| Normal | 5,587 | 25.82% | 0 |

### 5.1. Experimental Setup

We randomly split the dataset into training and testing sets using a 7:3 ratio. For all approaches, we tune hyperparameters using five-fold cross-validation on the training set, and we report the average test performance over five independent runs.

Metrics: We adopt precision, recall, and F1 scores for both classes and macro averaging to provide an overall view of model performance. Since accuracy is unreliable under class imbalance, we employ the Area Under the Precision-Recall Curve (AUPRC) to evaluate the model’s ability to distinguish high-risk from non-high-risk tokens under class imbalance. A higher AUPRC indicates that the model maintains high precision and recall simultaneously under skewed class distributions.

| Removed Feature | AUPRC | Label=0 | | | Label=1 | | | Macro | | |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Precision | Recall | F1 | Precision | Recall | F1 | Precision | Recall | F1 |
| Full Feature | 0.5729 | 0.5450 | 0.5695 | 0.5570 | 0.8459 | 0.8325 | 0.8391 | 0.6954 | 0.7010 | 0.6981 |
| – Group 1 | 0.5567 | 0.5216 | 0.5565 | 0.5385 | 0.8400 | 0.8202 | 0.8300 | 0.6808 | 0.6883 | 0.6842 |
| – Group 2 | 0.5693 | 0.5358 | 0.5582 | 0.5468 | 0.8420 | 0.8296 | 0.8358 | 0.6889 | 0.6939 | 0.6913 |
| – Group 3 | 0.5369 | 0.5165 | 0.5452 | 0.5305 | 0.8366 | 0.8202 | 0.8283 | 0.6766 | 0.6827 | 0.6794 |
| – Group 4 | 0.5451 | 0.5251 | 0.5492 | 0.5369 | 0.8349 | 0.8287 | 0.8318 | 0.6800 | 0.6890 | 0.6844 |
| – Group 2&4 | 0.5268 | 0.5048 | 0.5257 | 0.5151 | 0.8304 | 0.8183 | 0.8243 | 0.6676 | 0.6720 | 0.6697 |

Baselines: We evaluate two families of models: tabular feature-based models and time-series encoders. Specifically, (i) Tabular feature-based models consume tabular features ranging from group 1 to 4, including Logistic Regression (LR), Random Forest (RF) (Breiman, [2001](https://arxiv.org/html/2602.13480v1#bib.bib49 "Random forests")) , LightGBM (Ke et al., [2017](https://arxiv.org/html/2602.13480v1#bib.bib51 "Lightgbm: a highly efficient gradient boosting decision tree")), XGBoost (Chen, [2016](https://arxiv.org/html/2602.13480v1#bib.bib50 "XGBoost: a scalable tree boosting system")), and Multi-Layer Perceptron (MLP); (ii) Time-series encoders take time-series as input, including TCN (Bai, [2018](https://arxiv.org/html/2602.13480v1#bib.bib45 "An empirical evaluation of generic convolutional and recurrent networks for sequence modeling")), LSTM (Hochreiter and Schmidhuber, [1997](https://arxiv.org/html/2602.13480v1#bib.bib48 "Long short-term memory")), GRU (Cho et al., [2014](https://arxiv.org/html/2602.13480v1#bib.bib47 "Learning phrase representations using rnn encoder-decoder for statistical machine translation")) and Transformer Encoder (Vaswani et al., [2017](https://arxiv.org/html/2602.13480v1#bib.bib46 "Attention is all you need")). Due to the space constraint, we put the hyper-parameter settings in Appendix [A](https://arxiv.org/html/2602.13480v1#A1 "Appendix A Hyper-parameter Settings ‣ MemeTrans: A Dataset for Detecting High-Risk Memecoin Launches on Solana").

### 5.2. Performance Comparison

We evaluate existing approaches and report their performance in Table LABEL:tab:comparison, where we can make several observations: (i) Tabular feature-based models achieve better performance compared with time-series models, suggesting that designed features are more informative for detecting high-risk memecoins than models based merely on time-series of price and trading volumes; (ii) Among the tabular models, MLP achieves the best performance, likely due to its ability to implicitly combine multiple features and capture higher-order interactions beyond the original feature set; (iii) Among time-series models, more complex architectures such as Transformers do not achieve the best performance, whereas LSTM performs the best. We conjecture that this is because the short and noisy trading sequences lack the long-range dependencies that Transformers are designed to exploit.

### 5.3. Feature Ablation Study

To measure the contribution of features, we iteratively remove each feature group and report the results in Table [11](https://arxiv.org/html/2602.13480v1#S5.T11 "Table 11 ‣ 5.1. Experimental Setup ‣ 5. High-Risk Memecoin Detection ‣ MemeTrans: A Dataset for Detecting High-Risk Memecoin Launches on Solana"). We first observe that removing any feature group results in a performance drop, indicating that the designed features provide complementary information. Second, removing Group 3 (market activity) leads to the largest performance degradation. This observation is consistent with the feature importance scores obtained from the random forest (RF) model (see Figure [5](https://arxiv.org/html/2602.13480v1#A0.F5 "Figure 5 ‣ 8. Conclusion ‣ MemeTrans: A Dataset for Detecting High-Risk Memecoin Launches on Solana") in the appendix), where features in the market activity group receive the highest importance values. Moreover, groups 2 and 4 both capture holding concentration, but Group 4 is computed after leveraging bundle traces to reveal true ownership concentration. Consequently, removing Group 4 results in a larger performance drop than removing Group 2. Since these groups capture complementary aspects of holding concentration, removing both leads to a substantial performance degradation.

|  |  |  |  |  |
| --- | --- | --- | --- | --- |
| Model | Top-100 | | Top-200 | |
| Precision | Loss (%) | Precision | Loss (%) |
| w.o. model | 0.2540 | 60.71 | 0.2650 | 64.84 |
| LR | 0.7000 | 34.06 | 0.6200 | 36.50 |
| RF | 0.7600 | 30.34 | 0.7300 | 33.72 |
| XGBoost | 0.7500 | 31.45 | 0.7400 | 33.15 |
| LightGBM | 0.7400 | 31.99 | 0.7250 | 34.15 |
| MLP | 0.8000 | 26.64 | 0.7550 | 31.47 |

### 5.4. Application: Memecoin Selection

To assess whether risk detection models can reduce financial loss in practice, we simulate a simple memecoin selection strategy by ranking tokens based on predicted risk scores in descending order and selecting the top-kk candidates. For each selected memecoin, we use the price at migration as the purchase price and compute the average loss by randomly sampling 100 selling timestamps within the following hour. We evaluate this strategy on the test set and report the results in Table LABEL:tab:token\_selection. Precision measures the proportion of non-high-risk memecoins among the selected tokens, while loss denotes the percentage loss incurred when investing one unit of capital. As shown, random selection leads to losses exceeding 60%, whereas model-guided selection reduces losses to around 30%, despite the models not being optimized for loss minimization. Among all approaches, MLP achieves the best performance, reducing financial loss by 56.1%. These results demonstrate that MemeTrans provides practical value for real-world loss mitigation.

## 6. Related Work

### 6.1. Rug Pull Schemes

Rug pull refers to an exit scam pattern on blockchain, where token creators initially provide liquidity to a token pair on a DEX, attract investor trading activity, and later abruptly remove the liquidity, draining the pool of valuable assets and rendering the token worthless. The attack is achieved via the creator’s full control over liquidity pool tokens. Rug pulls have been the subject of extensive analysis in the blockchain security community. Cernera et al. (Cernera et al., [2023](https://arxiv.org/html/2602.13480v1#bib.bib22 "Token spammers, rug pulls, and sniper bots: an analysis of the ecosystem of tokens in ethereum and in the binance smart chain ({{{{{bnb}}}}})")) conduct a longitudinal analysis of over 1.3 million tokens on Ethereum and BNB Smart Chain, introducing the notion of 1-day rug pulls, where a token is listed and drained within 24 hours. Their methodology relies on liquidity pool event patterns and identifies sniper bots that assist in early exploitation. Mazorra et al. (Mazorra et al., [2022](https://arxiv.org/html/2602.13480v1#bib.bib25 "Do not rug on me: zero-dimensional scam detection")) build a supervised classifier using blockchain and social features, showing that most rug pulls are initiated by wallets with prior history of creating disposable tokens. Yaremus et al. (Yaremus et al., [2025](https://arxiv.org/html/2602.13480v1#bib.bib27 "Detecting rug pulls in decentralized exchanges: machine learning evidence from the ton blockchain")) construct a taxonomy of exit scams and propose an automated labeling pipeline based on on-chain liquidity events. Other datasets like SolRPDS (Alhaidari et al., [2024](https://arxiv.org/html/2602.13480v1#bib.bib26 "SolRPDS: a dataset for analyzing rug pulls in solana decentralized finance")) provide curated rug pull samples on Solana to facilitate model training.

### 6.2. Pump-and-dump Schemes

Pump-and-dump campaigns coordinate buying to create a short-lived price spike that enables early insiders to sell at inflated prices (Hu et al., [2023b](https://arxiv.org/html/2602.13480v1#bib.bib38 "Sequence-based target coin prediction for cryptocurrency pump-and-dump"); Li et al., [2021](https://arxiv.org/html/2602.13480v1#bib.bib54 "Cryptocurrency pump-and-dump schemes"); Xu and Livshits, [2019](https://arxiv.org/html/2602.13480v1#bib.bib28 "The anatomy of a cryptocurrency {pump-and-dump} scheme"); La Morgia et al., [2021a](https://arxiv.org/html/2602.13480v1#bib.bib55 "The doge of wall street: analysis and detection of pump and dump cryptocurrency manipulations")). Prior work has mainly studied such behavior in centralized exchanges (CEXs) or order-book markets, where transaction-level traces are not publicly accessible and holdings are custodial rather than address-based, making it difficult to reconstruct fine-grained trading traces or analyze multi-account behaviors (Kamps and Kleinberg, [2018](https://arxiv.org/html/2602.13480v1#bib.bib58 "To the moon: defining and detecting cryptocurrency pump-and-dumps"); Hu et al., [2023b](https://arxiv.org/html/2602.13480v1#bib.bib38 "Sequence-based target coin prediction for cryptocurrency pump-and-dump")). Moreover, order-book price dynamics are driven by buy orders lifting the ask side and subsequent sell orders consuming liquidity. In contrast, launchpad-based memecoin markets sell tokens via a bonding-curve program and then migrate liquidity to an AMM pool, which confers a much stronger first-mover advantage to early buyers and can amplify post-migration losses when these low-cost positions unwind.

## 7. Utility Outlook

Beyond studying risk detection, MemeTrans offers broader utility in the crypto ecosystem. First, it can support the development of memecoin trading strategies for industrial practitioners, as exemplified in our application study, which incorporates the predicted risk scores into memecoin selection. Second, the bundle trace data enables research on matching accounts belonging to the same entities, revealing hidden coordination behaviors on-chain such as money laundering or Sybil detection (Hu et al., [2025](https://arxiv.org/html/2602.13480v1#bib.bib62 "Matching accounts on blockchain via pseudo fine-tuning of language models"), [2023c](https://arxiv.org/html/2602.13480v1#bib.bib64 "Bert4eth: a pre-trained transformer for ethereum fraud detection"); Béres et al., [2021](https://arxiv.org/html/2602.13480v1#bib.bib63 "Blockchain is watching you: profiling and deanonymizing ethereum users")). Both the dataset and the released data science pipeline can be extended to continuously collect newly launched memecoins, perform large-scale transaction collection and parsing, and identify bundled or coordinated accounts. While existing studies have largely focused on fraudulent activities in Bitcoin and Ethereum (Weber et al., [2019](https://arxiv.org/html/2602.13480v1#bib.bib66 "Anti-money laundering in bitcoin: experimenting with graph convolutional networks for financial forensics"); Hu et al., [2024](https://arxiv.org/html/2602.13480v1#bib.bib65 "Zipzap: efficient training of language models for large-scale fraud detection on blockchain"), [2023a](https://arxiv.org/html/2602.13480v1#bib.bib68 "Large language model-powered smart contract vulnerability detection: new perspectives")), the rapid rise of the Solana ecosystem introduces new research challenges in large-scale and high-frequency token markets, making MemeTrans a timely resource for future research and the crypto community.

## 8. Conclusion

MemeTrans provides the first large-scale view of memecoin launchpad trading on Solana, covering over 40k+ launches and 200M+ on-chain transactions. By incorporating bundle traces, MemeTrans reveals coordinated multi-account behaviors that are hidden in raw on-chain data. The dataset includes 122 features of the launchpad sale, capturing contextual information, holding concentration, market activity, and bundle statistics, along with hybrid risk annotations that combine a statistical indicator and an ML-based detector. Experiments on high-risk memecoin detection show that models trained on MemeTrans can effectively reduce financial losses, suggesting that the dataset not only provides a research foundation but also offers practical value for real-world risk mitigation.

![Refer to caption](x5.png)

## Appendix A Hyper-parameter Settings

Table LABEL:tab:tcn\_parameter reports the hyper-parameter setting of TCN used for manipulation detection. For high-risk memecoin detection task, competitors are configured as follows: LR serves as a linear baseline with L2 regularization and a fixed regularization strength of 1.0. For tree-based models, RF is implemented with 800 trees and a maximum depth of 16, while other parameters follow standard practice. XGBoost uses 800 trees with a maximum depth of 6 and a learning rate of 0.05. LightGBM is trained with 2000 boosting iterations and a learning rate of 0.02, with the maximum number of leaves set to 64 and subsampling applied to control model complexity. MLP consists of two fully connected hidden layers with 512 and 256 units, respectively. Each layer is followed by batch normalization, ReLU activation, and dropout with a rate of 0.2, and the model outputs a single logit for binary classification. For time-series models, both GRU, LSTM and Transformer classifiers are configured with two stacked layers and a hidden dimension of 256. A dropout rate of 0.2 is applied between layers. TCN shares the same hyper-parameter settings as those reported in Table LABEL:tab:tcn\_parameter.

| Component | Parameter / Setting |
| --- | --- |
| Input shape | [Batch, Time = 3600, Channels = 5] |
| Kernel size | 9 |
| Dilations | [1, 2, 4, 8, 16, 32, 64, 128] |
| Output channels | 32 |
| Convolution layers | 8 blocks ×\times 2 Conv1d = 16 layers |
| Receptive field | ≈\approx 4,081 seconds |
| Activation | ReLU |
| Normalization | BatchNorm1d |
| Padding | Symmetric (non-causal) |
| Classifier head | AdaptiveAvgPool1d (1) →\rightarrow Flatten →\rightarrow Linear (32→\rightarrow32) →\rightarrow ReLU →\rightarrow Dropout (0.5) →\rightarrow Linear (32→\rightarrow2) |
| Output dimension | [Batch, 2] |

## Appendix B Feature Importance Study

In Figure [5](https://arxiv.org/html/2602.13480v1#A0.F5 "Figure 5 ‣ 8. Conclusion ‣ MemeTrans: A Dataset for Detecting High-Risk Memecoin Launches on Solana"), we report the importance scores of the 122 features produced by the RF model. As shown, features from Group 3 (market activity) and Group 4 (bundle statistics), highlighted in green and red, account for the highest importance, which is consistent with the feature ablation results in Table [11](https://arxiv.org/html/2602.13480v1#S5.T11 "Table 11 ‣ 5.1. Experimental Setup ‣ 5. High-Risk Memecoin Detection ‣ MemeTrans: A Dataset for Detecting High-Risk Memecoin Launches on Solana").

## References

![Mascot Sammy](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAsAAAAOCAYAAAD5YeaVAAAAAXNSR0IArs4c6QAAAAZiS0dEAP8A/wD/oL2nkwAAAAlwSFlzAAALEwAACxMBAJqcGAAAAAd0SU1FB9wKExQZLWTEaOUAAAAddEVYdENvbW1lbnQAQ3JlYXRlZCB3aXRoIFRoZSBHSU1Q72QlbgAAAdpJREFUKM9tkL+L2nAARz9fPZNCKFapUn8kyI0e4iRHSR1Kb8ng0lJw6FYHFwv2LwhOpcWxTjeUunYqOmqd6hEoRDhtDWdA8ApRYsSUCDHNt5ul13vz4w0vWCgUnnEc975arX6ORqN3VqtVZbfbTQC4uEHANM3jSqXymFI6yWazP2KxWAXAL9zCUa1Wy2tXVxheKA9YNoR8Pt+aTqe4FVVVvz05O6MBhqUIBGk8Hn8HAOVy+T+XLJfLS4ZhTiRJgqIoVBRFIoric47jPnmeB1mW/9rr9ZpSSn3Lsmir1fJZlqWlUonKsvwWwD8ymc/nXwVBeLjf7xEKhdBut9Hr9WgmkyGEkJwsy5eHG5vN5g0AKIoCAEgkEkin0wQAfN9/cXPdheu6P33fBwB4ngcAcByHJpPJl+fn54mD3Gg0NrquXxeLRQAAwzAYj8cwTZPwPH9/sVg8PXweDAauqqr2cDjEer1GJBLBZDJBs9mE4zjwfZ85lAGg2+06hmGgXq+j3+/DsixYlgVN03a9Xu8jgCNCyIegIAgx13Vfd7vdu+FweG8YRkjXdWy329+dTgeSJD3ieZ7RNO0VAXAPwDEAO5VKndi2fWrb9jWl9Esul6PZbDY9Go1OZ7PZ9z/lyuD3OozU2wAAAABJRU5ErkJggg==)
