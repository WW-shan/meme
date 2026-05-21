# Detecting Rug Pulls in Decentralized Exchanges: Machine Learning Evidence from the TON Blockchain

###### Abstract

This paper presents a machine learning framework for the early detection of rug pull scams on decentralized exchanges (DEXs) within The Open Network (TON) blockchain. TON’s unique architecture, characterized by asynchronous execution and a massive web2 user base from Telegram, presents a novel and critical environment for fraud analysis. We conduct a comprehensive study on the two largest TON DEXs, Ston.Fi and DeDust, fusing data from both platforms to train our models. A key contribution is the implementation and comparative analysis of two distinct rug pull definitions–TVL-based (a catastrophic liquidity withdrawal) and idle-based (a sudden cessation of all trading activity)–within a single, unified study. We demonstrate that Gradient Boosting models can effectively identify rug pulls within the first five minutes of trading, with the TVL-based method achieving superior AUC (up to 0.891) while the idle-based method excels at recall. Our analysis reveals that while feature sets are consistent across exchanges, their underlying distributions differ significantly, challenging straightforward data fusion and highlighting the need for robust, platform-aware models. This work provides a crucial early-warning mechanism for investors and enhances the security infrastructure of the rapidly growing TON DeFi ecosystem.

###### keywords:

[MIPT]organization=Moscow Institute of Physics and Technology,
city=Moscow 141701,
country=Russia

[HSE]organization=Faculty of Computer Science, HSE University,
city=Moscow 109028,
country=Russia

[MSU]organization=Moscow State University,
city=Moscow 119991,
country=Russia

[Sk]organization=Skolkovo Institute of Science and Technology,
city=Moscow 121205,
country=Russia

[IR]organization=Independent Researcher,
city=Barcelona 08001,
country=Spain

## 1 Introduction

The Open Network [[1](https://arxiv.org/html/2509.01168v1#bib.bib1)] was originally conceived and developed by Telegram, and is now independently operated by the TON Foundation. It is a high-performance decentralized platform designed to support large-scale decentralized applications (DApps) [[2](https://arxiv.org/html/2509.01168v1#bib.bib2)] and smart contracts [[3](https://arxiv.org/html/2509.01168v1#bib.bib3)]. The number of users in the TON ecosystem has increased dramatically, with monthly active users increasing to 4.64 million. However, some users are unaware of blockchain risks and are easy targets for fraud and hacker attacks [[4](https://arxiv.org/html/2509.01168v1#bib.bib4)]. This research focuses on smart contracts related to decentralized exchanges (DEXs) platforms [[5](https://arxiv.org/html/2509.01168v1#bib.bib5)], such as Ston.Fi [[6](https://arxiv.org/html/2509.01168v1#bib.bib6)] and DeDust [[7](https://arxiv.org/html/2509.01168v1#bib.bib7)]. In DEXs, tokens quickly lose value due to vulnerabilities in smart contract code, defects in liquidity mechanisms [[8](https://arxiv.org/html/2509.01168v1#bib.bib8), [9](https://arxiv.org/html/2509.01168v1#bib.bib9), [10](https://arxiv.org/html/2509.01168v1#bib.bib10)], lack of regulation, and anonymity. A common scam encountered by users is rug pull, in which the project party suddenly withdraws funds and runs away after attracting sufficient liquidity. Mantra (OM) is considered the biggest rug pull of the year, with losses amounting to $5.52 billion [[11](https://arxiv.org/html/2509.01168v1#bib.bib11)]. This study applies machine learning to DEXs in TON for early rug pull detection, which is capable of achieving efficient early warnings solely based on minute-level data from the initial stages of token transactions.

The high failure rate of the cryptocurrency market shows that the early window period is the stage of highest risk [[12](https://arxiv.org/html/2509.01168v1#bib.bib12)]. The early window detection of tokens is conducive to protecting user assets and provides a means of prevention [[13](https://arxiv.org/html/2509.01168v1#bib.bib13)]. Although the machine learning method cannot capture the new type of rug pull with 100% accuracy, it has played an important reference role for traders in the early stages. This study aims to use machine learning to discover and detect the early behavior patterns of rug pull on different DEXs data. It will also develop the early window size of the rug pull token, and analyze the data of all available tokens to find appropriate strategies. The results are helpful in understanding different early window strategies and collecting data from different sources to improve the machine learning model.

This study makes the following key contributions to the field of on-chain security and rug pull detection:

Rug Pull Analysis for the TON Blockchain Ecosystem: We present an extensive analysis of rug pull scams on the TON blockchain, addressing its unique ecosystem defined by asynchronous transaction execution and a large, less crypto-native audience migrating from Web2 via Telegram. Our work provides a foundational dataset and benchmark for security research in this emerging environment.

Unified Evaluation of TVL and Idle-Based Rug Pull Definitions: We implement, validate, and directly compare the two primary rug pull detection methodologies from the literature – TVL-based and idle-based – within a single framework. This comparative analysis provides a comprehensive view of scam dynamics, showing that the TVL method achieves superior AUC while the idle method is optimal for maximizing recall.

Analysis of Cross-DEX Data Fusion Viability: We investigate the viability of data fusion techniques for combining data from two major TON DEXs (Ston.Fi and DeDust). A critical finding is that while a consistent feature set can be engineered across platforms, their underlying statistical distributions differ significantly. This insight is vital for future multi-platform studies, indicating that models must account for such domain shifts.

The rest of the paper is organized as follows. Section [2](https://arxiv.org/html/2509.01168v1#S2 "2 Related Work ‣ Detecting Rug Pulls in Decentralized Exchanges: Machine Learning Evidence from the TON Blockchain") provides an overview of the related work. Section [3](https://arxiv.org/html/2509.01168v1#S3 "3 Research Workflow ‣ Detecting Rug Pulls in Decentralized Exchanges: Machine Learning Evidence from the TON Blockchain") formalizes the methodology, defines target variables using the Idle and TVL approaches in [3.1](https://arxiv.org/html/2509.01168v1#S3.SS1 "3.1 Target Variable Definition: Idle vs TVL ‣ 3 Research Workflow ‣ Detecting Rug Pulls in Decentralized Exchanges: Machine Learning Evidence from the TON Blockchain"), establishes evaluation criteria in [3.2](https://arxiv.org/html/2509.01168v1#S3.SS2 "3.2 Criteria for Model Evaluation ‣ 3 Research Workflow ‣ Detecting Rug Pulls in Decentralized Exchanges: Machine Learning Evidence from the TON Blockchain"), and shows details of cross-platform data fusion techniques in [3.3](https://arxiv.org/html/2509.01168v1#S3.SS3 "3.3 Data Fusion ‣ 3 Research Workflow ‣ Detecting Rug Pulls in Decentralized Exchanges: Machine Learning Evidence from the TON Blockchain"). Section [4](https://arxiv.org/html/2509.01168v1#S4 "4 Data Mining ‣ Detecting Rug Pulls in Decentralized Exchanges: Machine Learning Evidence from the TON Blockchain") covers the data mining in this study, including the collection of data from Ston.Fi and DeDust in [4.1](https://arxiv.org/html/2509.01168v1#S4.SS1 "4.1 Data Collection ‣ 4 Data Mining ‣ Detecting Rug Pulls in Decentralized Exchanges: Machine Learning Evidence from the TON Blockchain"), discusses the characterization of the data set in [4.2](https://arxiv.org/html/2509.01168v1#S4.SS2 "4.2 Dataset Description ‣ 4 Data Mining ‣ Detecting Rug Pulls in Decentralized Exchanges: Machine Learning Evidence from the TON Blockchain"), shows the details of feature engineering in [4.3](https://arxiv.org/html/2509.01168v1#S4.SS3 "4.3 Feature Engineering ‣ 4 Data Mining ‣ Detecting Rug Pulls in Decentralized Exchanges: Machine Learning Evidence from the TON Blockchain") , data labeling in [4.4](https://arxiv.org/html/2509.01168v1#S4.SS4 "4.4 Data Labeling ‣ 4 Data Mining ‣ Detecting Rug Pulls in Decentralized Exchanges: Machine Learning Evidence from the TON Blockchain") and preprocessing pipelines in [4.5](https://arxiv.org/html/2509.01168v1#S4.SS5 "4.5 Data Preprocessing Techniques ‣ 4 Data Mining ‣ Detecting Rug Pulls in Decentralized Exchanges: Machine Learning Evidence from the TON Blockchain"). Section [5](https://arxiv.org/html/2509.01168v1#S5 "5 Detection Model ‣ Detecting Rug Pulls in Decentralized Exchanges: Machine Learning Evidence from the TON Blockchain") detection model describes each sample preprocessing step in [5.1](https://arxiv.org/html/2509.01168v1#S5.SS1 "5.1 Data Preprocessing and Feature Engineering ‣ 5 Detection Model ‣ Detecting Rug Pulls in Decentralized Exchanges: Machine Learning Evidence from the TON Blockchain") and explains which machine learning model will be used and how to do tuning in [5.2](https://arxiv.org/html/2509.01168v1#S5.SS2 "5.2 Model and Hyperparameter Tuning ‣ 5 Detection Model ‣ Detecting Rug Pulls in Decentralized Exchanges: Machine Learning Evidence from the TON Blockchain"). Section [6](https://arxiv.org/html/2509.01168v1#S6 "6 Numerical Results ‣ Detecting Rug Pulls in Decentralized Exchanges: Machine Learning Evidence from the TON Blockchain") presents performance benchmarks (AUC/Class 0 accuracy) and a comparative analysis of the efficacy of Idle and TVL. Section [7](https://arxiv.org/html/2509.01168v1#S7 "7 Discussions and Conclusions ‣ Detecting Rug Pulls in Decentralized Exchanges: Machine Learning Evidence from the TON Blockchain") provides the concluding remarks of the paper.

## 2 Related Work

The evolution of blockchain and cryptocurrency has been accompanied by a constant struggle between innovation and new threats. In 2017-2018, there was an explosive growth in ICO (Initial Coin Offering), which led to the emergence of many scam projects and rug pull [[14](https://arxiv.org/html/2509.01168v1#bib.bib14)]. In 2020-2024, DeFi and DEX came to the fore, as well as the creation of memecoins [[15](https://arxiv.org/html/2509.01168v1#bib.bib15)], which increased trading volumes and attracted the attention of investors and scammers [[16](https://arxiv.org/html/2509.01168v1#bib.bib16)].

Memcoins such as Notcoin, DOGS, DUREV on TON are becoming popular due to integration with messengers and social networks, which expands the audience, but also increases the risks for inexperienced users. Memcoins repeat the scenario of classic financial bubbles: rapid capitalization growth. In 2024, the memcoin market increased by 330%, reaching $140 billion.

Modern research offers comprehensive approaches to fraud detection that combine machine learning methods with blockchain features. Key areas include:

Ensemble classification methods: The works [[17](https://arxiv.org/html/2509.01168v1#bib.bib17), [18](https://arxiv.org/html/2509.01168v1#bib.bib18)] demonstrate the effectiveness of a combination of algorithms (logistic regression, Isolation Forest) or XGBoost combined with SMOTE to detect suspicious transactions in Ethereum with an accuracy of up to 99%.

Graph analysis of transactions: The study [[19](https://arxiv.org/html/2509.01168v1#bib.bib19)] proposes using node2vec to analyze Ethereum transactions, achieving an F1 score of 0.846 to detect phishing attacks.

Real-time anomaly detection: The framework combines clustering (k-means) and deep learning techniques to analyze blockchain streaming data [[20](https://arxiv.org/html/2509.01168v1#bib.bib20)].

A significant amount of research has been devoted to blockchain fraud, particularly schemes that are common in token trading. Several studies have looked at fraudulent schemes associated with ICO [[21](https://arxiv.org/html/2509.01168v1#bib.bib21), [22](https://arxiv.org/html/2509.01168v1#bib.bib22), [23](https://arxiv.org/html/2509.01168v1#bib.bib23)], for example, regression analysis showed that tokens that were listed on exchanges (previously considered a sign of a successful ICO) were more likely to be the target of fraud, in approximately 10.1% [[24](https://arxiv.org/html/2509.01168v1#bib.bib24)].

Exchanges and the tokens traded on them are also considered by researchers as a key source of vulnerability. Tokens with potential ”backdoors” in their code are considered especially dangerous. Currently, various analysis tools are available that can be applied to centralized exchanges (CEX) and decentralized exchanges (DEX) [[25](https://arxiv.org/html/2509.01168v1#bib.bib25), [26](https://arxiv.org/html/2509.01168v1#bib.bib26)].

The cryptocurrency market is vulnerable to external manipulation, which is one of the main principles of market vulnerability [[27](https://arxiv.org/html/2509.01168v1#bib.bib27)]. The authors highlight factors such as imperfect regulation, relative anonymity, low barriers to entry, and the lack of strict procedures to create exchanges. Exchange vulnerabilities account for a significant portion of cryptocurrency fraud cases. Between 2011 and 2017, 18 token exchanges were closed due to fraud [[28](https://arxiv.org/html/2509.01168v1#bib.bib28)].

The rug pull scheme was studied by Bruno Mazorra [[29](https://arxiv.org/html/2509.01168v1#bib.bib29)], who analyzed 28,000 tokens in Uniswap V2, of which 98% were flagged as fraudulent in the data. His methodology is based on time series analysis using machine learning, estimating the price drop of a token.

An alternative method to detect token scams is the approach implemented in the TokenScout tool, which uses temporal graph neural networks to detect scams on the Ethereum blockchain [[30](https://arxiv.org/html/2509.01168v1#bib.bib30)]. In another study, the authors used temporal characteristics and automated mechanisms to detect suspicious assets. The researchers developed scam recognition models adapted to work with different time intervals. Although large time windows can improve the accuracy of the models, it is essential to consider short periods to minimize delays in detecting rug pulls after they have occurred [[31](https://arxiv.org/html/2509.01168v1#bib.bib31)].

In the context of the analysis of rug pulls in TON, it is also worth mentioning the study [[32](https://arxiv.org/html/2509.01168v1#bib.bib32)], which looked at token activity on the Ethereum and Binance Smart Chain (BSC) blockchains until 2022. According to the results, about 70% of the addresses created only one token, while only 1% of the addresses issued more than 18 tokens each. The token life cycle has become even shorter: almost half (49.7%) of the assets disappear from the exchange within the first 4 hours after launch.

Memecoins, due to their high virality and low entry barrier, are attractive targets for attackers [[18](https://arxiv.org/html/2509.01168v1#bib.bib18)]. This article focuses on the characteristics of memecoins, which have short life cycles and rapidly fluctuating activity. This research needs to explore machine learning methods for analyzing smart contract and transaction information and proposes the development of effective tools to protect users and strengthen the DeFi ecosystem’s resilience to fraudulent schemes.

These findings confirm the relevance of this study. The more deeply the behavior of tokens on exchanges is studied and predicted, the more opportunities there are for safe and informed investments.

## 3 Research Workflow

The goal of this research is to develop an automated solution for the early lifetime detection of fraudulent tokens (rug pulls) on decentralized blockchain exchanges (DEXs of TON) – S​t​o​n.F​iSton.Fi and D​e​D​u​s​tDeDust. It protects investors’ interests and enhances trust in the TON DeFi ecosystem by timely detecting rug pulls based on data from the first few minutes of trading. Specifically, it is necessary to predict whether a rug pull (fraudulent liquidity loss or cessation of activity) will occur within the next hour after the start of trading, based on data collected within 5 minutes of the start of DEX token trading. The solution should be implemented using machine learning methods and provide investors with recommendations on how to participate in new token trading.
The processing to detect rug pull on the TON blockchain includes the following steps:

Data Collection: Obtaining information on transactions and liquidity pools for tokens on the S​t​o​n.F​iSton.Fi and D​e​D​u​s​tDeDust DEXs through indexed data from the TON Foundation and the Dune.com service.

Data Preprocessing: Cleaning of gaps and zero values, scaling, and generating features.

Feature Generation: Formation of transaction, price, liquidity, time, and meta-features for each token.

Data Labeling: Defining the target variable (rug pull) using two approaches: Idle (no transactions for an hour) and TVL (a drop in TVL by more than 99% from the maximum in the first hour).

Training the models: Applying machine learning algorithms to predict rug pulls.

Validation and Evaluation: Using cross-validation and test sets to evaluate the quality of the models.

Analysis of Results: Comparing the performance of models and approaches, analyzing the importance of features.

### 3.1 Target Variable Definition: Idle vs TVL

The study will use Idle and TVL approaches [[18](https://arxiv.org/html/2509.01168v1#bib.bib18), [29](https://arxiv.org/html/2509.01168v1#bib.bib29)] to define rug pull, each corresponding to its target variable.

#### 3.1.1 Idle Approach

Rug pull is defined as a token that has no trades (buys/sells) within one hour of starting the trading. Figure [1](https://arxiv.org/html/2509.01168v1#S3.F1 "Figure 1 ‣ 3.1.1 Idle Approach ‣ 3.1 Target Variable Definition: Idle vs TVL ‣ 3 Research Workflow ‣ Detecting Rug Pulls in Decentralized Exchanges: Machine Learning Evidence from the TON Blockchain") shows this method. It is recommended by decentralized exchange trading enthusiasts because it has good practical value, if there are no trades within an hour, the previously purchased tokens will not be able to be sold. Figure [2](https://arxiv.org/html/2509.01168v1#S3.F2 "Figure 2 ‣ 3.1.1 Idle Approach ‣ 3.1 Target Variable Definition: Idle vs TVL ‣ 3 Research Workflow ‣ Detecting Rug Pulls in Decentralized Exchanges: Machine Learning Evidence from the TON Blockchain") shows the $NOOB token – 3 trades within 30 minutes of the start of the trade, then the activity stops for a full hour.

![Refer to caption](images/buy_sell.png)
![Refer to caption](images/noob.png)

#### 3.1.2 TVL (Total Value Locked) Approach

A rug pull is defined as a drop in TVL of more than pp% from its peak value within the first hour of trading.

Figure [3](https://arxiv.org/html/2509.01168v1#S3.F3 "Figure 3 ‣ 3.1.2 TVL (Total Value Locked) Approach ‣ 3.1 Target Variable Definition: Idle vs TVL ‣ 3 Research Workflow ‣ Detecting Rug Pulls in Decentralized Exchanges: Machine Learning Evidence from the TON Blockchain") shows an example: $UKWNPTHS token – after reaching TVL peak, liquidity drops drastically, resulting in a loss of more than 99% of its maximum value. TVL drops from $300k to $1 in a short period of time and activity ends. Formally, the method is defined by the “Maximum Drop in TVL”, the rug pull token ⇔M​D≤p\Leftrightarrow MD\leq p.

This approach mirrors the definition of a rug pull in that it relies directly on locked liquidity.

|  |  |  |  |
| --- | --- | --- | --- |
|  | t0=arg⁡maxt∈[0,60]​T​V​L​(t)t\_{0}=\underset{t\in[0,60]}{\arg\max}\ TVL(t) |  | (1) |

|  |  |  |  |
| --- | --- | --- | --- |
|  | τ=arg⁡mint∈[t0,60]​T​V​L​(t)\tau=\underset{t\in[t\_{0},60]}{\arg\min}\ TVL(t) |  | (2) |

|  |  |  |  |
| --- | --- | --- | --- |
|  | M​D=|T​V​L​(t0)−T​V​L​(τ)|T​V​L​(t0)MD=\dfrac{|TVL(t\_{0})-TVL(\tau)|}{TVL(t\_{0})} |  | (3) |

![Refer to caption](images/UKWNPTHS.png)

### 3.2 Criteria for Model Evaluation

The following metrics are used to objectively evaluate the quality of the model:

AUC (area under the ROC curve):
This metric mainly reflects the model’s ability to distinguish between rug pulls and normal tokens.

Accuracy:
The proportion of correctly predicted rug pulls among all positive predictions. This is critical to minimizing false positives.

Recall:
The proportion of correctly predicted rug pulls among all true rug pulls. This is critical to minimize missing values (false negatives).

F1 score:
The harmonic mean of precision and recall, used to balance precision and recall.

Accuracy:
The overall proportion of correct predictions. However, due to class imbalance (which is common in rug pull tasks), this metric has less information.

This study will use the AUC metric to train the model and will use AUC, precision, and recall to analyze the results. The study will also consider the accuracy of Class 0 separately as it is crucial in the task of ensuring investor safety.

### 3.3 Data Fusion

Model training and validation were performed not only on two samples (data sources), but also on various Data Fusion methods. Figure [4](https://arxiv.org/html/2509.01168v1#S3.F4 "Figure 4 ‣ 3.3 Data Fusion ‣ 3 Research Workflow ‣ Detecting Rug Pulls in Decentralized Exchanges: Machine Learning Evidence from the TON Blockchain") we can see five different approaches to model training:

Training on the S​t​o​n.F​iSton.Fi sample, quality measurement on the same S​t​o​n.F​iSton.Fi sample

Training on the D​e​D​u​s​tDeDust sample, quality measurement on the same D​e​D​u​s​tDeDust sample

Training on the combined D​e​D​u​s​t​s​a​m​p​l​e∪S​t​o​n.F​iDeDustsample\;\cup\;Ston.Fi, quality measurement on S​t​o​n.F​iSton.Fi, or on D​e​D​u​s​tDeDust

Training on S​t​o​n.F​iSton.Fi sample, saving model weights, then retraining on D​e​D​u​s​tDeDust sample, quality measurement on D​e​D​u​s​tDeDust

Training on D​e​D​u​s​tDeDust sample, saving model weights, then retraining on S​t​o​n.F​iSton.Fi sample, quality measurement on S​t​o​n.F​iSton.Fi

The paper compares all methods to achieve a higher AUC.

![Refer to caption](images/exps.png)

## 4 Data Mining

### 4.1 Data Collection

To collect and analyze information on transactions, liquidity pools and trading history, this study used the dune.com service [[33](https://arxiv.org/html/2509.01168v1#bib.bib33)], which provides access to indexed blockchain data.

The TON Foundation, the organization responsible for developing and supporting the TON ecosystem, has played a special role in providing access to structured data. All transactions and events on the TON blockchain are indexed and aggregated in an open-source database that can be queried through dune.com. This allows researchers and developers to obtain up-to-date details on token transactions, the formation of liquidity pools, and other key events in the ecosystem.

To collect data, this study developed specialized SQL queries for ton.dex-trades, ton.dex-pools, and other tables in d​u​n​e.c​o​mdune.com to ensure maximum detail and relevance of the collected information.

Figure [5](https://arxiv.org/html/2509.01168v1#S4.F5 "Figure 5 ‣ 4.1 Data Collection ‣ 4 Data Mining ‣ Detecting Rug Pulls in Decentralized Exchanges: Machine Learning Evidence from the TON Blockchain") shows that S​t​o​n.F​iSton.Fi and D​e​D​u​s​tDeDust were taken for the study as the most representative and popular DEXs in TON.

![Refer to caption](images/dex_volume.png)

Several DEXs were represented in the data.

S​t​o​n.F​iSton.Fi and D​e​D​u​s​tDeDust are top 1 and top 2 DEX in TON by volume of trading and popularity.

gaspump is a launchpad where tokens are sold via the Bonding Curve algorithm, and a pool is created automatically on D​e​D​u​s​tDeDust when liquidity reaches 1000 TON. No liquidity data, TVL approach cannot be used.

ton.fun is a pump.fun analogue on TON. No liquidity data, TVL approach cannot be used.

tonco has data on only 80 tokens.

megaton has data on only 38 tokens.

memeslab had no data at the time of model training and data collection.

Figure [6](https://arxiv.org/html/2509.01168v1#S4.F6 "Figure 6 ‣ 4.1 Data Collection ‣ 4 Data Mining ‣ Detecting Rug Pulls in Decentralized Exchanges: Machine Learning Evidence from the TON Blockchain") shows that the lower time limit of Jan 1, 2024 was also chosen as tokens with a trading start date no earlier than Jan 1, 2024 and no later than Apr 1, 2025 account for 99.4% of all tokens (for S​t​o​n.F​iSton.Fi – 99.4%, for D​e​D​u​s​tDeDust – 99.1%). Information on the token ratio was collected in May 2025.

![Refer to caption](images/dex_tokens.png)

### 4.2 Dataset Description

The samples contain information on each token, a detailed description of the features can be found in the Table [1](https://arxiv.org/html/2509.01168v1#S4.T1 "Table 1 ‣ 4.2 Dataset Description ‣ 4 Data Mining ‣ Detecting Rug Pulls in Decentralized Exchanges: Machine Learning Evidence from the TON Blockchain").

The samples included only tokens with pool information (there was at least one record about the pool and its liquidity), only transactions with a non-zero value of v​o​l​u​m​e​\_​u​s​dvolume\\_usd, since we are only interested in token purchases and sales, and only pools from the TON blockchain.

As a result, the sample sizes were: 30,097 tokens on D​e​D​u​s​tDeDust and 18,283 tokens for S​t​o​n.F​iSton.Fi.

| Feature | Description |
| --- | --- |
| buy\_sell\_ratio | Ratio of token purchases and sales |
| price\_range | Difference between maximum and minimum prices |
| buys | Number of purchases in 5 minutes |
| sells | Number of sales in 5 minutes |
| buy\_perc | Percentage of purchases from all transactions |
| sell\_perc | Percentage of sales from all transactions |
| unique\_buyers | Number of unique buyers |
| unique\_sellers | Number of unique sellers |
| total\_usd\_volume | Total transaction volume in dollars |
| total\_usd\_buy\_volume | Purchase volume in dollars |
| total\_usd\_sell\_volume | Sales volume in dollars |
| decimals | Technical field for token (precision) |
| avg\_lp\_fee | Average LP fee |
| avg\_protocol\_fee | Average protocol fee |
| jetton\_creation\_trade\_delta | Difference between token sale start and token creation (in seconds) |
| pool\_creation\_trade\_delta | Difference between token sale start and pool creation (in seconds) |
| is\_pool\_creator | Token creator is the same as pool creator |
| initial\_tvl\_usd | Initial TVL in pool |
| initial\_price | Token price in first transaction |
| initial\_buy\_price | Token price in first purchase |
| max\_tvl | Maximum TVL in 5 minutes |
| min\_tvl | Minimum TVL in 5 minutes |
| buy\_price\_std | Standard deviation of purchase price |
| initial\_sell\_price | Price token in first sale |
| sell\_price\_std | Standard deviation of sale price |
| price\_max | Maximum price in 5 minutes |
| price\_min | Minimum price in 5 minutes |
| price\_delta | Difference between last and starting price |
| price\_std | Standard deviation of price in transactions |
| first\_buy\_time\_ts | Time of first purchase |
| first\_sell\_time\_ts | Time of first sale |
| pool\_deployment\_at\_ts | Pool deployment time |
| jetton\_deployment\_at\_ts | Token deployment time |

### 4.3 Feature Engineering

Distribution histograms were constructed for all numerical features. Most features have a right-skewed distribution, which is typical for financial data: most tokens have low activity, and a small number demonstrate high values in terms of volume, number of transactions, and TVL.

### 4.4 Data Labeling

In the definition of TVL rug pull there is a variable pp  —  acceptable percentage of TVL drop.

In Figure [8](https://arxiv.org/html/2509.01168v1#S4.F8 "Figure 8 ‣ 4.4 Data Labeling ‣ 4 Data Mining ‣ Detecting Rug Pulls in Decentralized Exchanges: Machine Learning Evidence from the TON Blockchain") and Figure [8](https://arxiv.org/html/2509.01168v1#S4.F8 "Figure 8 ‣ 4.4 Data Labeling ‣ 4 Data Mining ‣ Detecting Rug Pulls in Decentralized Exchanges: Machine Learning Evidence from the TON Blockchain"), it can see graphs of the dependence of the rug pull percentage for the TVL approach on the acceptable percentage of M​DMD  —  pp drop, for S​t​o​n.F​iSton.Fi and D​e​D​u​s​tDeDust respectively [[29](https://arxiv.org/html/2509.01168v1#bib.bib29)].

![Refer to caption](images/md_rug_stonfi.png)
![Refer to caption](images/md_rug_dedust.png)

It is also necessary to determine how much time ahead this study will predict rug pull, similar to how the distribution of the ratio of classes 0 and 1 was constructed depending on how long it predicted rug pull [[18](https://arxiv.org/html/2509.01168v1#bib.bib18)]. It is clear that the classes in both the TVL and Idle approaches are not balanced. This is important to consider when training models to avoid overfitting to the majority class. For this work, a time of 60 minutes was chosen.

![Refer to caption](images/when_sell.png)

### 4.5 Data Preprocessing Techniques

During the preliminary data analysis, problems related to the quality of the datasets were identified: the presence of zero values, NULL, and noise in the form of outliers. These features are typical for data collected from decentralized exchanges and require special processing.

NULLs: Some features, especially metadata and timestamps, contain missing values. To eliminate them, they were filled with median values for numeric features.

Null values: Often found in features related to transaction volume (often token sales). Such values may indicate low token activity.

Noise: The data contain outliers in volume and numbers of transactions. To reduce the impact of noise, scaling and algorithmization methods were used.

![Refer to caption](images/zeros_stonfi.png)
![Refer to caption](images/nulls_stonfi.png)
![Refer to caption](images/zeros_dedust.png)
![Refer to caption](images/nulls_dedust.png)

Figure [10](https://arxiv.org/html/2509.01168v1#S4.F10 "Figure 10 ‣ 4.5 Data Preprocessing Techniques ‣ 4 Data Mining ‣ Detecting Rug Pulls in Decentralized Exchanges: Machine Learning Evidence from the TON Blockchain") shows the visualization of the distribution of zero and NULL features. NULLs and zeros are mostly due to missing token sales, which are about 80% in both samples, and also due to missing metadata such as the token creator’s address or d​e​c​i​m​a​l​sdecimals.

## 5 Detection Model

### 5.1 Data Preprocessing and Feature Engineering

For each sample (S​t​o​n.F​iSton.Fi and D​e​D​u​s​tDeDust), the following steps were performed:

Gap removal: Rows with missing values in key features (e.g. timestamps, TVL) were excluded from the sample.

Zero filling: For numeric features with zero values, median filling or row removal were used.

Scaling: Numeric features were scaled using StandardScaler (or left unscaled depending on the results of cross-validation).

Feature generation: Additional features were created, such as the buy/sell ratio, price range, standard price deviation, time deltas between token creation and the first transaction, etc.

Time feature processing: Timestamps were converted to numeric deltas (e.g., the difference between token creation and start of trading in seconds). t​i​m​e​s​t​a​m​ptimestamp time features were also used as features.

### 5.2 Model and Hyperparameter Tuning

#### 5.2.1 Machine Learning Model

The following models were used to solve the rug pull binary classification problem:

GradientBoosting – boosting algorithm with sequential tree construction.

RandomForest – ensemble of decision trees with bagging.

DecisionTree – basic decision tree algorithm.

ExtremeGradientBoosting – gradient boosting of trees with regularization, effective for problems with class imbalance.

The choice of models is due to their high efficiency in solving class imbalance problems and the ability to interpret the importance of features.

#### 5.2.2 Hyperparameter tuning

For each model, hyperparameters were selected using GridSearchCV:

XGBoost: learning\_rate, max\_depth, n\_estimators, subsample, colsample\_bytree, gamma, reg\_alpha, reg\_lambda.

GradientBoosting: learning\_rate, max\_depth, n\_estimators, subsample, loss, min\_samples\_split, max\_features.

RandomForest: n\_estimators, max\_depth, min\_samples\_split, max\_features, class\_weight.

DecisionTree: max\_depth, min\_samples\_split, max\_features.

The selection was carried out on cross-validation with splitting into 3 folds to minimize overfitting and maximize the quality of the models. Also, for each model, the data preprocessing method was tried, either StandardScaler or leave as is, and this was done separately for numerical and temporal features.

#### 5.2.3 Cross-validation

To assess the quality of the models, a division into training and test samples was used in a ratio of 8:2, while maintaining the proportions of classes. At the same time, when training on a combined data set (D​e​D​u​s​t∪S​t​o​n.F​iDeDust\;\cup\;Ston.Fi), stratification was performed not only by class but also by data source.
Training sample for 3 folds, maintaining the balance of classes in each fold.

## 6 Numerical Results

### 6.1 Comparison of Model Performance

#### 6.1.1 AUC Analysis

During the experiments, the following results were obtained for the AUC metric for the best models in each dataset and approache: Idle in Table [2](https://arxiv.org/html/2509.01168v1#S6.T2 "Table 2 ‣ 6.1.1 AUC Analysis ‣ 6.1 Comparison of Model Performance ‣ 6 Numerical Results ‣ Detecting Rug Pulls in Decentralized Exchanges: Machine Learning Evidence from the TON Blockchain") and Table [3](https://arxiv.org/html/2509.01168v1#S6.T3 "Table 3 ‣ 6.1.1 AUC Analysis ‣ 6.1 Comparison of Model Performance ‣ 6 Numerical Results ‣ Detecting Rug Pulls in Decentralized Exchanges: Machine Learning Evidence from the TON Blockchain"), TVL in Table [4](https://arxiv.org/html/2509.01168v1#S6.T4 "Table 4 ‣ 6.1.1 AUC Analysis ‣ 6.1 Comparison of Model Performance ‣ 6 Numerical Results ‣ Detecting Rug Pulls in Decentralized Exchanges: Machine Learning Evidence from the TON Blockchain") and Table [5](https://arxiv.org/html/2509.01168v1#S6.T5 "Table 5 ‣ 6.1.1 AUC Analysis ‣ 6.1 Comparison of Model Performance ‣ 6 Numerical Results ‣ Detecting Rug Pulls in Decentralized Exchanges: Machine Learning Evidence from the TON Blockchain").
The notation D​e​D​u​s​t∪S​t​o​n.F​iDeDust\;\cup\;Ston.Fi means training in the combined sample, and measuring the quality only in D​e​D​u​s​tDeDust or S​t​o​n.F​iSton.Fi, and S​t​o​n.F​i→D​e​D​u​s​tSton.Fi\rightarrow DeDust means training and measuring in the data D​e​D​u​s​tDeDust, but for a model whose weights are preserved after training in the sample S​t​o​n.F​iSton.Fi.

| Metrics / Experiment | D​e​D​u​s​tDeDust | D​e​D​u​s​t∪S​t​o​n.F​iDeDust\;\cup\;Ston.Fi | S​t​o​n.F​i→D​e​D​u​s​tSton.Fi\rightarrow DeDust |
| --- | --- | --- | --- |
| Best Model | ExtremeGradientBoosting | ExtremeGradientBoosting | ExtremeGradientBoosting |
| Precision (1) | 0.86 | 0.86 | 0.90 |
| Recall (1) | 0.96 | 0.97 | 0.82 |
| F1 (1) | 0.91 | 0.91 | 0.86 |
| Precision (0) | 0.70 | 0.78 | 0.46 |
| Recall (0) | 0.35 | 0.36 | 0.64 |
| F1 (0) | 0.46 | 0.49 | 0.54 |
| AUC | 0.820 | 0.820 | 0.820 |

| Metrics / Experiment | S​t​o​n.F​iSton.Fi | D​e​D​u​s​t∪S​t​o​n.F​iDeDust\;\cup\;Ston.Fi | D​e​D​u​s​t→S​t​o​n.F​iDeDust\rightarrow Ston.Fi |
| --- | --- | --- | --- |
| Best Model | ExtremeGradientBoosting | RandomForest | ExtremeGradientBoosting |
| Precision (1) | 0.87 | 0.87 | 0.85 |
| Recall (1) | 0.97 | 0.96 | 0.99 |
| F1 (1) | 0.92 | 0.91 | 0.92 |
| Precision (0) | 0.79 | 0.72 | 0.90 |
| Recall (0) | 0.47 | 0.41 | 0.37 |
| F1 (0) | 0.58 | 0.52 | 0.52 |
| AUC | 0.840 | 0.838 | 0.840 |

| Metrics / Experiment | S​t​o​n.F​iSton.Fi | D​e​D​u​s​t∪S​t​o​n.F​iDeDust\;\cup\;Ston.Fi | D​e​D​u​s​t→S​t​o​n.F​iDeDust\rightarrow Ston.Fi |
| --- | --- | --- | --- |
| Best Model | GradientBoosting | ExtremeGradientBoosting | ExtremeGradientBoosting |
| Precision (1) | 0.76 | 0.74 | 0.74 |
| Recall (1) | 0.64 | 0.81 | 0.65 |
| F1 (1) | 0.69 | 0.78 | 0.69 |
| Precision (0) | 0.87 | 0.83 | 0.87 |
| Recall (0) | 0.92 | 0.76 | 0.91 |
| F1 (0) | 0.89 | 0.79 | 0.89 |
| AUC | 0.885 | 0.891 | 0.885 |

| Metrics / Experiment | D​e​D​u​s​tDeDust | D​e​D​u​s​t∪S​t​o​n.F​iDeDust\;\cup\;Ston.Fi | S​t​o​n.F​i→D​e​D​u​s​tSton.Fi\rightarrow DeDust |
| --- | --- | --- | --- |
| Best Model | GradientBoosting | GradientBoosting | ExtremeGradientBoosting |
| Precision (1) | 0.76 | 0.77 | 0.76 |
| Recall (1) | 0.82 | 0.78 | 0.81 |
| F1 (1) | 0.79 | 0.77 | 0.78 |
| Precision (0) | 0.73 | 0.81 | 0.72 |
| Recall (0) | 0.67 | 0.80 | 0.67 |
| F1 (0) | 0.70 | 0.80 | 0.69 |
| AUC | 0.829 | 0.831 | 0.826 |

For clarity, a comparison chart of AUC for different datasets and approaches is provided below Figure [11](https://arxiv.org/html/2509.01168v1#S6.F11 "Figure 11 ‣ 6.1.1 AUC Analysis ‣ 6.1 Comparison of Model Performance ‣ 6 Numerical Results ‣ Detecting Rug Pulls in Decentralized Exchanges: Machine Learning Evidence from the TON Blockchain").

![Refer to caption](images/idle_vs_tvl_auc_new.png)

The analysis of the results shows that the TVL approach shows a higher average AUC value (0.8600.860) compared to the Idle approach (0.8290.829), with a difference of 0.0310.031.

Mixed learning on combined data (D​e​D​u​s​t∪S​t​o​n.F​iDeDust\;\cup\;Ston.Fi) does not improve the AUC metric for D​e​D​u​s​tDeDust, but positively affects S​t​o​n.F​iSton.Fi TVL approach (+0.007+0.007)

Also, for the TVL approach, testing in S​t​o​n.F​iSton.Fi data shows significantly better results with an average AUC of 0.8870.887, versus 0.8290.829 on D​e​D​u​s​tDeDust data. This may indicate better data quality and clearer rug pull patterns on the S​t​o​n.F​iSton.Fi platform.

Applying Recursive Feature Elimination (RFE) resulted in a slight improvement in the metrics, achieving an accuracy of 87.89%. This algorithm uses a recursive iterative process, each time training on a subset of features, selecting the least important ones for the model, and eliminating them. In this case, the algorithm identified the following features for elimination: creation\_month\_cos, is\_pool\_creator, and std\_rsi.

#### 6.1.2 Comparison of Accuracy Class 0

For clarity, a Precision (0) comparison chart for different datasets and approaches is provided in Figure [12](https://arxiv.org/html/2509.01168v1#S6.F12 "Figure 12 ‣ 6.1.2 Comparison of Accuracy Class 0 ‣ 6.1 Comparison of Model Performance ‣ 6 Numerical Results ‣ Detecting Rug Pulls in Decentralized Exchanges: Machine Learning Evidence from the TON Blockchain").

![Refer to caption](images/idle_vs_tvl_prec_0_new.png)

The accuracy of detecting non-rug pull tokens (class 0) is a critical metric, as false positives reduce user confidence in the warning system.

The best Precision(0) is achieved using the Idle approach with transfer learning from D​e​D​u​s​tDeDust to S​t​o​n.F​iSton.Fi (0.90)

With the idle approach, transferring weights from D​e​D​u​s​tDeDust to S​t​o​n.F​iSton.Fi improves precision (0) to 0.90, while transferring from S​t​o​n.F​iSton.Fi to D​e​D​u​s​tDeDust reduces it to 0.46. For the TVL approach, transfer learning shows stable results in both directions.

### 6.2 Feature Importance Analysis

Feature importance analysis was performed for the best models in each sample. In the Idle approach, the most significant features were those related to transaction volume and number of purchases (e.g. total\_usd\_volume\_5min, buys\_5min, is\_pool\_creator for S​t​o​n.F​iSton.Fi and D​e​D​u​s​tDeDust). In the TVL approach, the key features are related to liquidity and time deltas (e.g. max\_tvl\_5min, jetton\_creation\_trade\_delta, first\_buy\_time\_ts for S​t​o​n.F​iSton.Fi).

For clarity, visualizations of feature importance for each approach (Idle, TVL) and each data source (D​e​D​u​s​tDeDust, S​t​o​n.F​iSton.Fi) are presented below Figure [13](https://arxiv.org/html/2509.01168v1#S6.F13 "Figure 13 ‣ 6.2 Feature Importance Analysis ‣ 6 Numerical Results ‣ Detecting Rug Pulls in Decentralized Exchanges: Machine Learning Evidence from the TON Blockchain") [14](https://arxiv.org/html/2509.01168v1#S6.F14 "Figure 14 ‣ 6.2 Feature Importance Analysis ‣ 6 Numerical Results ‣ Detecting Rug Pulls in Decentralized Exchanges: Machine Learning Evidence from the TON Blockchain") [15](https://arxiv.org/html/2509.01168v1#S6.F15 "Figure 15 ‣ 6.2 Feature Importance Analysis ‣ 6 Numerical Results ‣ Detecting Rug Pulls in Decentralized Exchanges: Machine Learning Evidence from the TON Blockchain") [16](https://arxiv.org/html/2509.01168v1#S6.F16 "Figure 16 ‣ 6.2 Feature Importance Analysis ‣ 6 Numerical Results ‣ Detecting Rug Pulls in Decentralized Exchanges: Machine Learning Evidence from the TON Blockchain").

![Refer to caption](images/dedust_best_idle.png)
![Refer to caption](images/dedust_best_tvl.png)
![Refer to caption](images/stonfi_best_idle.png)
![Refer to caption](images/stonfi_best_tvl.png)

### 6.3 Comparison of Idle and TVL approaches

Comparison of the Idle and TVL approaches showed that the TVL approach demonstrates higher and more stable performance on both samples by AUC metric. This is due to the fact that TVL is a more objective and informative indicator of rug pull compared to no transactions (Idle), especially for tokens with low activity. However, the best Precision(0) indicator is achieved using the Idle approach with transfer learning from D​e​D​u​s​tDeDust to S​t​o​n.F​iSton.Fi (0.90), making the Idle approach more applicable to real life.

The Idle approach better identifies class 1 (rug pull), and the TVL approach better identifies class 0 (not rug pull); this is clearly seen in the table with precision and recall by classes. This is natural because these approaches had a corresponding skew in the ratio of classes.

### Experimental Summary

The experiments confirmed the high efficiency of the proposed approach in detecting rug pull in DEX S​t​o​n.F​iSton.Fi and D​e​D​u​s​tDeDust. The best results were shown by the GradientBoosting and ExtremeGradientBoosting models, especially when using the TVL approach. Combining data from different exchanges (data fusion) allows to increase the stability and quality of the models. The key features for predicting rug pull are the volume of transactions, the number of purchases, and the liquidity of the token. The TVL approach is recommended as the main one for the practical implementation of the rug pull monitoring system on the TON blockchain.

## 7 Discussions and Conclusions

### Comparative analysis of results by datasets and approaches

![Refer to caption](images/matrix_tvl_dedust.png)
![Refer to caption](images/matrix_tvl_stonfi.png)
![Refer to caption](images/matrix_idle_dedust.png)
![Refer to caption](images/matrix_idle_stonfi.png)

The experiments yielded results that allow this study to evaluate the effectiveness of various machine learning models to detect rug pull on the S​t​o​n.F​iSton.Fi and D​e​D​u​s​tDeDust DEX platforms, as well as on the combined dataset (data fusion). The main conclusions for each approach and dataset are presented in the following.

Idle approach (rug pull - no transactions within an hour after the start of trading):

On the S​t​o​n.F​iSton.Fi dataset, the best results were shown by the

ExtremeGradientBoosting model: AUC = 0.8397, precision (1) = 0.87, recall (1) = 0.97, which indicates a high ability of the model to detect rug pull at the early stages of trading.

On the D​e​D​u​s​tDeDust dataset, ExtremeGradientBoosting also leads: AUC = 0.8203, precision (1) = 0.86, recall (1) = 0.96.

On the combined dataset (S​t​o​n.F​i∪D​e​D​u​s​tSton.Fi\;\cup\;DeDust), the best model is

RandomForest: AUC = 0.8265, precision (1) = 0.87, recall (1) = 0.96.

Models trained on the combined dataset and tested on another demonstrate comparable quality, which confirms the robustness of the approaches to differences in data distributions between exchanges.

TVL approach (rug pull - TVL drop by more than 99% from the maximum in the first hour of trading):

In S​t​o​n.F​iSton.Fi, the best model is GradientBoosting: AUC = 0.8853, precision (1) = 0.76, recall (1) = 0.64.

On D​e​D​u​s​tDeDust, GradientBoosting is also in the lead: AUC = 0.8293, precision (1) = 0.76, recall (1) = 0.82.

On the combined dataset, the best model is GradientBoosting: AUC = 0.8713, precision (1) = 0.77, recall (1) = 0.78.

Models trained on the combined dataset and tested on individual exchanges show high generalizability and stability of results.

A comparative analysis of the approaches showed that the TVL approach demonstrates higher AUC values in S​t​o​n.F​iSton.Fi, and the Idle approach shows higher recall values in both data sets. This is due to the specifics of rug pull detection: the TVL approach is more sensitive to a sharp drain on liquidity, and the Idle approach to the cessation of activity.

### Practical Application Suggestions

Based on the results obtained, the following practical recommendations can be formulated:

Use a combined dataset (data fusion) to train models: This allows for increased stability and quality of predictions on different DEXs.

Choose an approach depending on the task:

For early detection of rug pull (cessation of activity) for the purpose of buying and selling tokens, use the Idle approach.

For detection of fraud with a sharp drain of liquidity, use the TVL approach.

Use GradientBoosting and ExtremeGradientBoosting models as the most effective for tasks with class imbalance and high feature dimensionality.

Regularly update the dataset and train the models to adapt to changing market conditions and new fraud schemes.

Implement automatic monitoring of new tokens based on proposed models to protect investors and increase trust in the TON DeFi ecosystem.

### Limitations

The study identified key limitations that affect the quality and sustainability of the proposed solution. Class imbalance is one of the main problems: the number of tokens with rug pull is significantly smaller than normal tokens, which reduces the recall for the non-rug pull class and can lead to a bias in models towards the majority class. Noise and outliers in the data associated with zero values, gaps, and anomalies in transaction and price features also have a negative impact on the quality of the models, which require additional preprocessing and data filtering.

The specifics of determining rug pull depending on the chosen approach (Idle or TVL) lead to the fact that the model can miss individual cases of fraud or give false positives. Using only the first 5 minutes of trading to predict rug pull over the next hour limits the capabilities of the model on tokens with non-standard dynamics, when fraud occurs later or is of a different nature. In addition, the quality of the data received through the API or the dune.com service may be incomplete or contain errors, which also reduces the accuracy of the models and requires additional verification and validation of the information sources.

### Future Research

A promising direction for further research is to expand the set of features using additional metrics, such as the social activity of token creators, data from external sources, and blockchain analytics. This will increase the informativeness of the models and improve the quality of rug pull detection.

Conducting a backtest on historical data to assess the economic effect of using models in real conditions will allow a better understanding of the practical value of the proposed solution and its impact on investment returns. The use of deep learning methods that take into account time dependencies and complex patterns in data can provide an additional boost to the quality of models, especially when working with large volumes of information. Adaptation of the proposed approach to detect rug pull in other decentralized exchanges and blockchain ecosystems will expand the scope of application of research results and will help identify universal patterns of fraud in DeFi.

## References

![Mascot Sammy](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAsAAAAOCAYAAAD5YeaVAAAAAXNSR0IArs4c6QAAAAZiS0dEAP8A/wD/oL2nkwAAAAlwSFlzAAALEwAACxMBAJqcGAAAAAd0SU1FB9wKExQZLWTEaOUAAAAddEVYdENvbW1lbnQAQ3JlYXRlZCB3aXRoIFRoZSBHSU1Q72QlbgAAAdpJREFUKM9tkL+L2nAARz9fPZNCKFapUn8kyI0e4iRHSR1Kb8ng0lJw6FYHFwv2LwhOpcWxTjeUunYqOmqd6hEoRDhtDWdA8ApRYsSUCDHNt5ul13vz4w0vWCgUnnEc975arX6ORqN3VqtVZbfbTQC4uEHANM3jSqXymFI6yWazP2KxWAXAL9zCUa1Wy2tXVxheKA9YNoR8Pt+aTqe4FVVVvz05O6MBhqUIBGk8Hn8HAOVy+T+XLJfLS4ZhTiRJgqIoVBRFIoric47jPnmeB1mW/9rr9ZpSSn3Lsmir1fJZlqWlUonKsvwWwD8ymc/nXwVBeLjf7xEKhdBut9Hr9WgmkyGEkJwsy5eHG5vN5g0AKIoCAEgkEkin0wQAfN9/cXPdheu6P33fBwB4ngcAcByHJpPJl+fn54mD3Gg0NrquXxeLRQAAwzAYj8cwTZPwPH9/sVg8PXweDAauqqr2cDjEer1GJBLBZDJBs9mE4zjwfZ85lAGg2+06hmGgXq+j3+/DsixYlgVN03a9Xu8jgCNCyIegIAgx13Vfd7vdu+FweG8YRkjXdWy329+dTgeSJD3ieZ7RNO0VAXAPwDEAO5VKndi2fWrb9jWl9Esul6PZbDY9Go1OZ7PZ9z/lyuD3OozU2wAAAABJRU5ErkJggg==)
