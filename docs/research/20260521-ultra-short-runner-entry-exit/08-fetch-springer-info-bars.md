Advertisement

![Advertisement](//pubads.g.doubleclick.net/gampad/ad?iu=/270604982/springerlink/40854/article&sz=728x90&pos=top&articleid=s40854-025-00866-w)
![Springer Nature Link](/oscar-static/images/darwin/header/img/logo-springer-nature-link-05805fde18.svg)

# Algorithmic crypto trading using information-driven bars, triple barrier labeling and deep learning

You have full access to this [open access](https://www.springernature.com/gp/open-science/about/the-fundamentals-of-open-access-and-open-research) article

![](https://media.springernature.com/w72/springer-static/cover-hires/journal/40854?as=webp)

8400 Accesses

1
Altmetric

[Explore all metrics](/article/10.1186/s40854-025-00866-w/metrics)

## Abstract

This paper investigates the optimization of data sampling and target labeling techniques to enhance algorithmic trading strategies in cryptocurrency markets, focusing on Bitcoin (BTC) and Ethereum (ETH). Traditional data sampling methods, such as time bars, often fail to capture the nuances of the continuously active and highly volatile cryptocurrency market and force traders to wait for arbitrary points in time. To address this, we propose an alternative approach using information-driven sampling methods, including the CUSUM filter, range bars, volume bars, and dollar bars, and evaluate their performance using tick-level data from January 2018 to June 2023. Additionally, we introduce the Triple Barrier method for target labeling, which offers a solution tailored for algorithmic trading as opposed to the widely used next-bar prediction. We empirically assess the effectiveness of these data sampling and labeling methods to craft profitable trading strategies. The results demonstrate that the innovative combination of CUSUM-filtered data with Triple Barrier labeling outperforms traditional time bars and next-bar prediction, achieving consistently positive trading performance even after accounting for transaction costs. Moreover, our system enables making trading decisions at any point in time on the basis of market conditions, providing an advantage over traditional methods that rely on fixed time intervals. Furthermore, the paper contributes to the ongoing debate on the applicability of Transformer models to time series classification in the context of algorithmic trading by evaluating various Transformer architectures—including the vanilla Transformer encoder, FEDformer, and Autoformer—alongside other deep learning architectures and classical machine learning models, revealing insights into their relative performance.

### Similar content being viewed by others

![](https://media.springernature.com/w92h120/springer-static/cover-hires/book/978-3-031-97825-8?as=webp)

### [Multi-timeframe Assessment of Triple Barrier Labelization Method for Cryptocurrency Returns Classification](https://link.springer.com/10.1007/978-3-031-97825-8_102?fromPaywallRec=false)

![](https://media.springernature.com/w92h120/springer-static/cover-hires/book/978-3-031-88304-0?as=webp)

### [Towards an Architecture for an Automated Cryptocurrency Algorithmic Trading System](https://link.springer.com/10.1007/978-3-031-88304-0_94?fromPaywallRec=false)

![](https://media.springernature.com/w215h120/springer-static/image/art%3A10.1007%2Fs10489-024-05407-z/MediaObjects/10489_2024_5407_Fig1_HTML.png)

### [UNSURE - A machine learning approach to cryptocurrency trading](https://link.springer.com/10.1007/s10489-024-05407-z?fromPaywallRec=false)

### Explore related subjects

## Introduction

Cryptocurrencies, introduced in Nakamoto’s seminal white paper ([2008](/article/10.1186/s40854-025-00866-w#ref-CR51 "Nakamoto S (2008) Bitcoin: a peer-to-peer electronic cash system.
                  https://bitcoin.org/bitcoin.pdf

                ")), are blockchain-based assets that enable peer-to-peer transactions without the need for third-party validation (Giudici et al. [2020](/article/10.1186/s40854-025-00866-w#ref-CR21 "Giudici G, Milne A, Vinogradov D (2020) Cryptocurrencies: market analysis and perspectives. J Ind Bus Econ 47(1):1–18.
                  https://doi.org/10.1007/s40812-019-00138-6

                ")). Proponents highlight their decentralized and deregulated nature, whereas critics argue that they are fraudulent or akin to Ponzi schemes (Aliber et al. [2023](/article/10.1186/s40854-025-00866-w#ref-CR1 "Aliber RZ, Kindleberger CP, McCauley RN (2023) Bitcoin: worse than a ponzi. In: Aliber RZ, Kindleberger CP, McCauley RN (eds) Manias, panics, and crashes: a history of financial crises. Springer, Berlin, pp 349–371.
                  https://doi.org/10.1007/978-3-031-16008-0_14

                ")). From a trading perspective, cryptocurrencies offer high volatility, continuous market availability—unrestricted by traditional opening and closing hours—anonymity, and the ability to facilitate peer-to-peer transactions (Fang et al. [2022](/article/10.1186/s40854-025-00866-w#ref-CR18 "Fang F, Ventre C, Basios M, Kanthan L, Martinez-Rego D, Wu F, Li L (2022) Cryptocurrency trading: a comprehensive survey. Financ Innov 8(1):13.
                  https://doi.org/10.1186/s40854-021-00321-6

                ")). However, they also face significant challenges, including scalability limitations, where transaction speed and capacity can become bottlenecks, cybersecurity risks, regulatory uncertainties, and susceptibility to market manipulation (Fratrič et al. [2022](/article/10.1186/s40854-025-00866-w#ref-CR19 "Fratrič P, Sileno G, Klous S, van Engers T (2022) Manipulation of the Bitcoin market: an agent-based study. Financ Innov 8(1):60.
                  https://doi.org/10.1186/s40854-022-00364-3

                ")). Despite these risks, the growing adoption of cryptocurrencies by both retail and institutional investors, increasing liquidity in major trading pairs, and expanding market depth have strengthened their viability for systematic trading strategies. These developments, combined with the data-rich and highly volatile nature of crypto markets, make the case even stronger.

Systematic trading models typically leverage statistical methods, classical machine learning, deep learning, or reinforcement learning to predict price movements and generate trading signals. However, traditional statistical methods (e.g., ARIMA and GARCH) often fail to capture complex nonlinear dependencies in crypto markets (Bouteska et al. [2024](/article/10.1186/s40854-025-00866-w#ref-CR9 "Bouteska A, Abedin MZ, Hajek P, Yuan K (2024) Cryptocurrency price forecasting: a comparative analysis of ensemble learning and deep learning methods. Int Rev Financ Anal 92:103055.
                  https://doi.org/10.1016/j.irfa.2023.103055

                "); Ibrahim et al. [2021](/article/10.1186/s40854-025-00866-w#ref-CR31 "Ibrahim A, Kashef R, Corrigan L (2021) Predicting market movement direction for bitcoin: a comparison of time series modeling methods. Comput Electr Eng 89:106905.
                  https://doi.org/10.1016/j.compeleceng.2020.106905

                ")). Classical machine learning techniques, such as gradient boosting, random forest and support vector machines (SVMs), have demonstrated some predictive success (Khedr et al. [2021](/article/10.1186/s40854-025-00866-w#ref-CR37 "Khedr AM, Arif I, P V PR, El-Bannany M, Alhashmi SM, Sreedharan M (2021) Cryptocurrency price prediction using traditional statistical and machine-learning techniques: a survey. Intell Syst Account Financ Manag 28(1):3–34.
                  https://doi.org/10.1002/isaf.1488

                ")) but lack the ability to model long-term temporal dependencies. Deep learning models—particularly recurrent architectures such as LSTMs and CNN-based approaches—have been extensively tested in recent years (Zhang et al. [2024](/article/10.1186/s40854-025-00866-w#ref-CR73 "Zhang J, Cai K, Wen J (2024) A survey of deep learning applications in cryptocurrency. iScience 27(1):108509.
                  https://doi.org/10.1016/j.isci.2023.108509

                ")) because of their natural suitability for time series data. While comparing the performance of ensemble methods and deep learning, Bouteska ([2024](/article/10.1186/s40854-025-00866-w#ref-CR9 "Bouteska A, Abedin MZ, Hajek P, Yuan K (2024) Cryptocurrency price forecasting: a comparative analysis of ensemble learning and deep learning methods. Int Rev Financ Anal 92:103055.
                  https://doi.org/10.1016/j.irfa.2023.103055

                ")) reported that the most effective model varied by cryptocurrency, highlighting the importance of asset-specific approaches.

While prior studies have often focused on improving predictive models, some research has explored alternative data preprocessing techniques, which are more akin to our work. For example, approaches rooted in signal processing, such as wavelet transformations, have been applied to cryptocurrency forecasting. Altan et al. ([2019](/article/10.1186/s40854-025-00866-w#ref-CR3 "Altan A, Karasu S, Bekiros S (2019) Digital currency forecasting with chaotic meta-heuristic bio-inspired signal processing techniques. Chaos Solitons Fractals 126:325–336.
                  https://doi.org/10.1016/j.chaos.2019.07.011

                ")) proposed a hybrid forecasting model that combines empirical wavelet transform (EWT) decomposition with an LSTM network optimized by a metaheuristic cuckoo search algorithm. Their findings suggest that wavelet-based decomposition can enhance predictive performance by isolating key frequency components within financial time series. Parvini et al. ([2022](/article/10.1186/s40854-025-00866-w#ref-CR54 "Parvini N, Abdollahi M, Seifollahi S, Ahmadian D (2022) Forecasting Bitcoin returns with long short-term memory networks and wavelet decomposition: a comparison of several market determinants. Appl Soft Comput 121:108707.
                  https://doi.org/10.1016/j.asoc.2022.108707

                ")) introduced a two-stage forecasting framework that combines discrete wavelet transform (DWT) decomposition with LSTM-based price prediction for Bitcoin. Their study also explored the impact of external predictors from different asset classes, such as gold, oil, the S&P 500, and the VIX, demonstrating that macrofinancial indicators can enhance cryptocurrency price forecasting. More recently, Jirou et al. ([2025](/article/10.1186/s40854-025-00866-w#ref-CR34 "Jirou I, Jebabli I, Lahiani A (2025) A hybrid deep learning model for cryptocurrency returns forecasting: comparison of the performance of financial markets and impact of external variables. Res Int Bus Financ 73:102575.
                  https://doi.org/10.1016/j.ribaf.2024.102575

                ")) expanded upon this work by further fine-tuning the LSTM hyperparameters at each level of DWT decomposition and incorporating additional sentiment and blockchain-based variables into the forecasting process. Their results indicate that the additional layer of DWT enhances feature extraction, ultimately leading to more accurate price forecasts. While these studies demonstrate the effectiveness of advanced feature extraction techniques, they all rely on daily sampled data as a starting point. In contrast, our work challenges the sampling paradigm itself rather than applying transformations to an already aggregated time series. A vast majority of studies, as documented by Amirzadeh ([2022](/article/10.1186/s40854-025-00866-w#ref-CR4 "Amirzadeh R, Nazari A, Thiruvady D (2022) Applying artificial intelligence in cryptocurrency markets: a survey. Algorithms 15(11):11.
                  https://doi.org/10.3390/a15110428

                ")), employ systematic time-based sampling (e.g., hourly or daily bars), which may not accurately reflect real trading conditions. Instead, we investigate information-driven sampling techniques—volume bars, dollar bars, range bars, and the CUSUM filter—which dynamically adjust data granularity on the basis of market activity. This shift allows trading models to respond to market dynamics in real time rather than being constrained by arbitrarily fixed time intervals.

In addition to data sampling, we reexamine the conventional approach to target labeling. Many studies rely on next-bar price movement as the target variable, a choice that may not fully capture the complexities of real trading conditions. Alternative approaches, such as adaptive target labeling and the Triple Barrier Method (Lopez de Prado [2018](/article/10.1186/s40854-025-00866-w#ref-CR16 "de Lopez Prado M (2018) Advances in financial machine learning. Wiley")), have been proposed to better reflect actual trading decisions, yet their empirical effectiveness in cryptocurrency markets remains largely unexplored. Our study addresses this gap by systematically evaluating both alternative data sampling techniques and adaptive target labeling, demonstrating their impact on systematic trading strategies. Specifically, we:

*Evaluate the Effectiveness of Information-Driven Data Sampling:* In financial markets, transactions can occur in rapid succession, sometimes within milliseconds, creating a continuous flow of data. For convenience in data analysis and algorithmic system development, it has become a convention to sample open, high, low, and close (OHLC) data at regular intervals, such as hourly or daily. We test a novel approach to data curation by exploring alternative data sampling methods beyond the widely used systematic time sampling. Our focus on information-driven bars, such as volume and dollar bars, CUSUM filters, and range bars, represents a departure from the traditional time bars used in most academic discussions. The motivation behind our study lies in the advantages of information-driven sampling, which is based on current market activity and volatility, allowing trading decisions to occur at any time and adapt to ongoing market dynamics. While this dynamic responsiveness can benefit any market, it can be particularly useful in the highly volatile cryptocurrency market, where rapid and substantial price movements are frequent. In such an environment, the static nature of time-sampled bars significantly delays the capture of critical market shifts, leading to suboptimal trading outcomes and increased risk. Moreover, this approach aligns with the nature of automated trading, which is now the predominant mode of trading and operates continuously. In contrast, if time-based sampling was applied in practice, we would expect to observe volume spikes at regular intervals—a notion that is not supported by empirical data. Additionally, in traditional financial market studies, trading at the closing price—which is an example of daily time sampling—is very common, but in reality, this is not feasible, as the closing price is reported after the session closes. For example, on the NYSE, Market-on-Close (MOC) orders must be submitted by 3:50 p.m., at which point the final price is still unknown. Consequently, backtests that assume trade execution at the close knowing the actual closing price suffer from look-ahead bias. Waiting instead for the next day’s opening can significantly degrade performance. As demonstrated by Luo et al. ([2014](/article/10.1186/s40854-025-00866-w#ref-CR47 "Luo Y, Alvarez M, Wang S, Jussa J, Wang A, and Rohal G (2014) Seven sins of quantitative investing. Deutsche Bank Markets Research, White paper")), a one-day reversal strategy that required the closing price achieved a theoretical Sharpe ratio of 1.4 when using that price but dropped to just 0.3 when trades were executed at the next day’s feasible opening. Moreover, closing prices are known to be susceptible to market manipulation, particularly around significant calendar events, as shown by Ma ([2022](/article/10.1186/s40854-025-00866-w#ref-CR48 "Ma A (2022) Profitability of technical trading strategies under market manipulation. Financ Innov 8(1):5.
                  https://doi.org/10.1186/s40854-021-00304-7

                ")). The study further revealed that substituting the official closing price with the last tick price, the final traded price during continuous trading, can significantly improve the profitability of technical trading strategies. However, relying on the last tick price introduces its own challenges, including potential liquidity constraints and the need for low-latency infrastructure to capture the exact final trade. Given these limitations, our framework offers a more practical and robust approach for algorithmic trading across asset classes, not just cryptocurrencies. Therefore, our framework has practical implications beyond cryptocurrencies, offering a more realistic approach for algorithmic trading in general.

*Compare Next-Bar and Triple Barrier Target Labeling:* We contrast the conventional next-bar prediction method with the Triple Barrier method. The Triple Barrier method offers a more practical approach, as it can take advantage of price swings regardless of when they occur. Moreover, it closely aligns with the common trading practice of incorporating take-profit and stop-loss orders, making it a more realistic representation of actual trading strategies.

*Evaluate Deep Learning Architectures for Time Series Classification:* Our investigation extends into the effectiveness of various Transformer-based network architectures in time series classification—a less explored domain than forecasting—providing valuable insights into the applicability of cutting-edge models in financial contexts. While there is no doubt that Transformers have sparked the current AI revolution, their dominance in the time series domain is less established, with recent studies offering differing perspectives. Interestingly, the feature that makes Transformers so powerful—the ability to process inputs in parallel rather than sequentially—can also be a limitation in time series applications, as the temporal order of data is critical, and positional encoding may not always effectively capture sequential dependencies.

Cryptocurrency markets provide a highly suitable environment for testing our framework because of their continuous trading cycle (24/7 availability), high volatility, and increasing liquidity. Unlike traditional asset classes, cryptocurrencies do not experience overnight gaps, market closing effects, or liquidity shifts due to opening auctions, which allows for a cleaner application of information-driven sampling techniques. However, while our methodology is tested in crypto markets, its underlying principles are not inherently crypto-specific and can be adapted to other markets.

The subsequent section begins with an overview of research focused on the application of deep learning for predicting the price movements of financial assets, with a particular emphasis on cryptocurrencies. Section “[Machine learning and deep learning models](/article/10.1186/s40854-025-00866-w#Sec3)” introduces the machine learning and deep learning models utilized in our study. Section "[Data](/article/10.1186/s40854-025-00866-w#Sec11)" details various data sampling and target labeling techniques, in addition to other data transformations. Section "[Empirical results](/article/10.1186/s40854-025-00866-w#Sec18)" outlines the experimental setup and performance metrics before presenting the empirical results. Section "[Sensitivity analysis](/article/10.1186/s40854-025-00866-w#Sec23)" examines the sensitivity of certain parameters and assumptions discussed in the preceding section. Finally, Section "[Discussion](/article/10.1186/s40854-025-00866-w#Sec28)" offers a discussion of the key results, and Section "[Conclusions](/article/10.1186/s40854-025-00866-w#Sec29)" provides a conclusion to our research.

## Literature review

In navigating the extensive field of cryptocurrency market forecasting, our literature review focuses on studies employing machine learning (ML) and deep learning (DL) techniques. This focus stems from the transformative potential of ML/DL in enhancing predictive accuracy in this volatile market. Our selection criteria were twofold: relevance to our study’s objectives—particularly in price movement prediction and trading strategy development—and the studies’ prominence, as evidenced by publication in leading journals or inclusion in meta-analyses. This approach streamlined our review to include only the most impactful and innovative research.

The majority of studies rely on systematic time-based sampling techniques and conventional target labeling methods, which may not fully exploit financial market dynamics from a trading perspective. Our study aims to address these limitations by exploring alternative data sampling techniques—such as information-driven bars—and employing more realistic target labeling approaches, such as the Triple Barrier method, to improve the predictive accuracy and applicability of trading strategies.

To illustrate the dominance of systematic time sampling, particularly its most common variant—daily bars—we begin our literature review with meta-studies. A comprehensive review by Jiang ([2021](/article/10.1186/s40854-025-00866-w#ref-CR33 "Jiang W (2021) Applications of deep learning in stock market prediction: recent progress. Expert Syst Appl 184:115537.
                  https://doi.org/10.1016/j.eswa.2021.115537

                ")) of 124 papers applying deep learning to stock market predictions revealed that 52 focused on daily classification (predicting the direction of price movement) and 54 on daily regression (predicting both direction and magnitude), whereas only 19 articles analyzed intraday movements. Most of these studies concentrated on short-term predictions, typically next-day predictions using daily data. This strong preference for daily data is consistent with findings from another meta-study (Thakkar and Chaudhari [2021](/article/10.1186/s40854-025-00866-w#ref-CR64 "Thakkar A, Chaudhari K (2021) A comprehensive survey on deep neural networks for stock market: The need, challenges, and future directions. Expert Syst Appl 177:114800.
                  https://doi.org/10.1016/j.eswa.2021.114800

                ")), where even the empirical part involved deep learning models using daily data. The literature shows a bias toward daily data, largely due to the unavailability or high cost of intraday data, which limits the exploration of more granular trading strategies. Fortunately, this limitation is not present for cryptocurrencies. For example, Alonso-Monsalve et al. ([2020](/article/10.1186/s40854-025-00866-w#ref-CR2 "Alonso-Monsalve S, Suárez-Cetrulo AL, Cervantes A, Quintana D (2020) Convolution on neural networks for high-frequency trend prediction of cryptocurrency exchange rates using technical indicators. Expert Syst Appl 149:113250.
                  https://doi.org/10.1016/j.eswa.2020.113250

                ")) investigated the predictability of six popular cryptocurrencies by applying a set of deep learning methods to high-frequency time sampling—1-min interval data. This study exemplifies the most common next-bar prediction approach, which, for short-term movements, poses challenges in overcoming transaction costs. However, Alonso-Monsalve et al. ([2020](/article/10.1186/s40854-025-00866-w#ref-CR2 "Alonso-Monsalve S, Suárez-Cetrulo AL, Cervantes A, Quintana D (2020) Convolution on neural networks for high-frequency trend prediction of cryptocurrency exchange rates using technical indicators. Expert Syst Appl 149:113250.
                  https://doi.org/10.1016/j.eswa.2020.113250

                ")) did not include an assessment of financial performance. Our study aims to demonstrate that this setup, even when applied over longer durations such as 60-min sampling intervals, is impractical for most investors. Such frequent trading on relatively small movements, especially when compounded with transaction costs, can lead to significant financial losses.

With respect to target labeling options, the literature offers greater variability. For example, (Thakkar and Chaudhari [2021](/article/10.1186/s40854-025-00866-w#ref-CR64 "Thakkar A, Chaudhari K (2021) A comprehensive survey on deep neural networks for stock market: The need, challenges, and future directions. Expert Syst Appl 177:114800.
                  https://doi.org/10.1016/j.eswa.2021.114800

                ")) predicted the adjusted closing price five days ahead. While predicting over a longer horizon can help detect more pronounced trends, it disregards what happens within those intervals, which could significantly impact automated systems and investor decision-making processes. Our study aims to address this shortcoming by allowing the target variable to be determined on the basis of varying interval lengths, contingent on market volatility. The use of market volatility to determine target definitions provides a more dynamic and adaptable model, addressing a critical gap in the literature. For example, Wang et al. ([2018](/article/10.1186/s40854-025-00866-w#ref-CR69 "Wang J, Sun T, Liu B, Cao Y, Wang D (2018) Financial markets prediction with deep learning. In: 2018 17th IEEE international conference on machine learning and applications (ICMLA), 97–104.
                  https://doi.org/10.1109/ICMLA.2018.00022

                ")) incorporated volatility directly into their target variable definition. In their study, a target was classified as up or down only if the subsequent closing price was significantly higher or lower than the previous price, adjusted for current asset volatility. Their data encompassed 5-min intervals for four commodity futures and two equity indices. Another interesting innovation in target definition was introduced by Gurgul et al. ([2025](/article/10.1186/s40854-025-00866-w#ref-CR25 "Gurgul V, Lessmann S, Härdle WK (2025) Deep learning and NLP in cryptocurrency forecasting: integrating financial, blockchain, and social media data. Int J Forecast 41(4):1666–1695.
                  https://doi.org/10.1016/j.ijforecast.2025.02.007

                ")). They labeled observations as local extrema within various time horizons (7, 14, and 21 days) to facilitate strategies for buying at troughs and selling at peaks. Although this target labeling method yielded lower profits than did classification on the basis of next-day labeling, it remained profitable and resulted in fewer trades. Sun et al. ([2020](/article/10.1186/s40854-025-00866-w#ref-CR63 "Sun X, Liu M, Sima Z (2020) A novel cryptocurrency price trend forecasting model based on LightGBM. Fin Res Lett 32:101084.
                  https://doi.org/10.1016/j.frl.2018.12.032

                ")) explored the predictability of cryptocurrencies with different lags between target and input data using daily data. They predicted the direction of movement for intervals of 2 days, 2 weeks, and 2 months. This study demonstrates an interesting variation in target definition by focusing on different prediction intervals, offering practical insights for medium- and long-term traders. These studies highlight the potential of more sophisticated target labeling methods, which we aim to build upon by employing the Triple Barrier method—a technique that aligns closely with practical trading strategies involving stop-loss and take-profit orders.

A significant limitation in existing studies, which impedes practical conclusions, is the lack of financial performance analysis. For example, Oyedele et al. ([2023](/article/10.1186/s40854-025-00866-w#ref-CR52 "Oyedele AA, Ajayi AO, Oyedele LO, Bello SA, Jimoh KO (2023) Performance evaluation of deep learning and boosted trees for cryptocurrency closing price prediction. Expert Syst Appl 213:119233.
                  https://doi.org/10.1016/j.eswa.2022.119233

                ")) predicted next-day closing prices for cryptocurrencies using daily data and evaluated model robustness across datasets from various origins, ultimately concluding that deep learning models outperform boosting tree techniques. However, financial performance metrics were not considered. Similarly, Murray et al. ([2023](/article/10.1186/s40854-025-00866-w#ref-CR50 "Murray K, Rossi A, Carraro D, Visentin A (2023) On forecasting cryptocurrency prices: a comparison of machine learning, deep learning, and ensembles. Forecasting.
                  https://doi.org/10.3390/forecast5010010

                ")) used daily data to forecast one step ahead based on the previous 30 days and explored both deep learning and ML techniques. Notably, their study included an instance of the Transformer network, the Temporal Fusion Transformer (Lim et al. [2021](/article/10.1186/s40854-025-00866-w#ref-CR45 "Lim B, Arık SÖ, Loeff N, Pfister T (2021) Temporal fusion transformers for interpretable multi-horizon time series forecasting. Int J Forecast 37(4):1748–1764.
                  https://doi.org/10.1016/j.ijforecast.2021.03.012

                ")), which underperformed compared with other algorithms. The authors speculated that the lack of additional covariates in the univariate time series models might explain this outcome. Once again, the absence of financial performance analysis limits the real-world applicability of these findings. Zoumpekas et al. ([2020](/article/10.1186/s40854-025-00866-w#ref-CR76 "Zoumpekas T, Houstis E, Vavalis M (2020) ETH analysis and predictions utilizing deep learning. Expert Syst Appl 162:113866.
                  https://doi.org/10.1016/j.eswa.2020.113866

                ")) employed deep learning models with high-frequency data, using 5-min intervals, to develop a trading strategy for ETH. Their profitability analysis suggested that strategies based on LSTM model predictions could outperform the traditional buy-and-hold strategy. However, the analysis did not account for transaction costs, which can significantly diminish gains in high-frequency trading. Zhang et al. ([2021](/article/10.1186/s40854-025-00866-w#ref-CR72 "Zhang Z, Dai H-N, Zhou J, Mondal SK, García MM, Wang H (2021) Forecasting cryptocurrency price using convolutional neural networks with weighted and attentive memory channels. Expert Syst Appl 183:115378.
                  https://doi.org/10.1016/j.eswa.2021.115378

                ")) analyzed daily data for four major cryptocurrencies, introducing the Weighted and Attentive Memory Channels model to exploit correlations among different cryptocurrencies. Their assessment of trading effectiveness did not include transaction costs either. Existing studies often focus solely on metrics such as the RMSE to gauge model performance, neglecting the real-world applicability of these models and the feasibility of their trading scenarios. Addressing this gap is crucial for our study, as comparing different datasets and targets can be reliably performed only from this perspective. Through this approach, we intend to provide a more actionable assessment of our research outcomes. Moreover, not reflecting transaction costs might lead to false conclusions with respect to the Efficient Market Hypothesis (EMH). The weak form of the EMH, introduced by Fama ([1970](/article/10.1186/s40854-025-00866-w#ref-CR17 "Fama EF (1970) Efficient capital markets: a review of theory and empirical work. J Finance 25(2):383–417")), suggests that it is impossible to consistently achieve abnormal returns using historical price data because such opportunities are quickly arbitraged away. However, if transaction costs are not accounted for, it may give the false impression that inefficiencies exist when, in reality, they are neutralized by the costs of executing trades.

Returning to data sampling techniques, the study by Borges and Neves ([2020](/article/10.1186/s40854-025-00866-w#ref-CR7 "Borges TA, Neves RF (2020) Ensemble of machine learning algorithms for cryptocurrency investment with different data resampling methods. Appl Soft Comput 90:106187.
                  https://doi.org/10.1016/j.asoc.2020.106187

                ")) is particularly notable, as it is the only one we are aware of that employed alternative data sampling techniques. It utilized classical, non-deep learning machine learning methods. They employed an ensemble voting system to predict the direction of the next bar, adjusted for transaction fees. The target variable was defined as the classification of the next bar’s movement (up or down). Their primary conclusion was that these alternative methods led to higher returns than did systematic time sampling. The authors analyzed the one hundred most popular cryptocurrencies from July 2017 to October 2018. However, their results were aggregated for most cryptocurrencies, leaving it unclear whether the findings are applicable to the most popular cryptocurrencies—these being our focus. Smaller cryptocurrencies, while potentially offering more opportunities due to their inefficiency, also pose risks such as low liquidity and a higher likelihood of fraud, potentially leading to total capital loss. Nevertheless, these findings are encouraging, suggesting that by combining alternative sampling methods with more sophisticated machine learning techniques, innovative target labeling, and extensive data, we might achieve higher-than-usual returns in our study. On the other hand, the more widespread adoption of cryptocurrencies and the resulting increase in market efficiency during the period we analyzed might impede the success of trading strategies. As concluded by more recent work (Kakinaka and Umeno [2022](/article/10.1186/s40854-025-00866-w#ref-CR35 "Kakinaka S, Umeno K (2022) Cryptocurrency market efficiency in short- and long-term horizons during COVID-19: an asymmetric multifractal analysis approach. Fin Res Lett 46:102319.
                  https://doi.org/10.1016/j.frl.2021.102319

                ")), Bitcoin and Ethereum still exhibit inefficiency in the short term. Notably, this study was also conducted using systematic time sampling relying on hourly data from the Poloniex crypto exchange.

Using a different machine learning paradigm, Vergara and Kristjanpoller ([2024](/article/10.1186/s40854-025-00866-w#ref-CR68 "Vergara G, Kristjanpoller W (2024) Deep reinforcement learning applied to statistical arbitrage investment strategy on cryptomarket. Appl Soft Comput 153:111255.
                  https://doi.org/10.1016/j.asoc.2024.111255

                ")) demonstrate that short-term inefficiencies between cryptocurrencies can be systematically exploited by employing a deep reinforcement learning-based statistical arbitrage framework. Their approach constructs cointegrated long–short portfolios and trains agents to detect and act on temporary price divergences. Evaluated on 30-min interval data and tested across multiple DRL algorithms, their framework, particularly the Deep Q-Network variant, consistently outperforms classical cointegration-based and SVM baselines, even after incorporating transaction costs. These findings further support the view that microstructure-level inefficiencies persist in crypto markets and highlight the potential of deep learning agents to exploit them effectively.

In summary, while the body of research on applying deep learning to cryptocurrency forecasting is extensive, gaps remain, particularly regarding data curation methods for maximizing the performance of algorithmic trading systems and the lack of financial performance evaluations. Our study addresses these gaps by exploring information-driven bars as an alternative to the prevalent time-based sampling method, alongside the Triple Barrier method—an approach not yet explored in the literature, to our knowledge. This in-depth analysis of data sampling and target labeling methods is conducted with a robust financial performance evaluation. Additionally, our research contributes to the study of Transformers’ efficacy for time series problems, which is scarcely researched in the finance domain. We state the following research hypotheses:

The cryptocurrency market is not informationally efficient; that is, it is possible to predict future prices on the basis of their history and create a profitable trading strategy.

Automated trading based on information-driven bars outperforms trading that uses systematic time-based sampling.

Triple Barrier labeling allows obtaining better performance (profitability) than the next bar labeling.

Deep learning algorithms outperform the classical machine learning model in algorithmic trading.

Transformer DL architectures outperform other approaches.

## Machine learning and deep learning models

The primary objective of this study is to measure the impact of different data sampling and target labeling strategies on trading performance while also addressing a secondary research question: the viability of Transformers and related architectures in cryptocurrency time series classification. Given the inherent difficulty of predicting financial assets, we adopt a broad selection of models to mitigate the risk of overlooking a profitable strategy by relying on an inadequate modeling approach. Our selection includes both incumbent methods—proven architectures frequently used in financial applications—and novel approaches that have recently shown promise in time series modeling.

Incumbent approaches:

*ResNet-LSTM*: This hybrid model combines CNNs for feature extraction with LSTMs for capturing long-term dependencies, a widely adopted approach in financial time series forecasting (Alonso-Monsalve et al. [2020](/article/10.1186/s40854-025-00866-w#ref-CR2 "Alonso-Monsalve S, Suárez-Cetrulo AL, Cervantes A, Quintana D (2020) Convolution on neural networks for high-frequency trend prediction of cryptocurrency exchange rates using technical indicators. Expert Syst Appl 149:113250.
                  https://doi.org/10.1016/j.eswa.2020.113250

                "); Gudelek et al. [2017](/article/10.1186/s40854-025-00866-w#ref-CR24 "Gudelek MU, Boluk SA, Ozbayoglu AM (2017) A deep learning based stock trading model with 2-D CNN trend detection.
                  https://ieeexplore.ieee.org/document/8285188

                "); Tsantekidis et al. [2020](/article/10.1186/s40854-025-00866-w#ref-CR66 "Tsantekidis A, Passalis N, Tefas A, Kanniainen J, Gabbouj M, Iosifidis A (2020) Using deep learning for price prediction by exploiting stationary limit order book features. Appl Soft Comput 93:106401.
                  https://doi.org/10.1016/j.asoc.2020.106401

                ")). The residual connections in ResNet-LSTM help mitigate vanishing gradient issues, whereas the CNN component improves local pattern recognition.

*Attention-LSTM*: This extends LSTMs by incorporating an attention mechanism, allowing the model to dynamically focus on the most relevant time steps. Studies in the stock and cryptocurrency markets (S. Chen and Ge [2019](/article/10.1186/s40854-025-00866-w#ref-CR12 "Chen S, Ge L (2019) Exploring the attention mechanism in LSTM-based Hong Kong stock price movement prediction. Quant Finance 19(9):1507–1515.
                  https://doi.org/10.1080/14697688.2019.1622287

                "); Hollis et al. [2018](/article/10.1186/s40854-025-00866-w#ref-CR28 "Hollis T, Viscardi A, Yi SE (2018) A comparison of LSTMs and attention mechanisms for forecasting financial time series.
                  https://doi.org/10.48550/arXiv.1812.07699

                ")) demonstrate its effectiveness in improving predictive accuracy.

*XGBoost*: A strong baseline for financial forecasting, frequently outperforming deep learning models on structured datasets. It has been widely used in cryptocurrency prediction tasks (Oyedele et al. [2023](/article/10.1186/s40854-025-00866-w#ref-CR52 "Oyedele AA, Ajayi AO, Oyedele LO, Bello SA, Jimoh KO (2023) Performance evaluation of deep learning and boosted trees for cryptocurrency closing price prediction. Expert Syst Appl 213:119233.
                  https://doi.org/10.1016/j.eswa.2022.119233

                "); Sun et al. [2020](/article/10.1186/s40854-025-00866-w#ref-CR63 "Sun X, Liu M, Sima Z (2020) A novel cryptocurrency price trend forecasting model based on LightGBM. Fin Res Lett 32:101084.
                  https://doi.org/10.1016/j.frl.2018.12.032

                ")).

Novel approaches:

*Transformers*: The objective of our study is to evaluate Transformer architectures (vanilla Transformer encoder, FEDformer, and Autoformer) in time series classification, which contributes to the debate on their effectiveness in time series forecasting (Zeng et al. [2022](/article/10.1186/s40854-025-00866-w#ref-CR71 "Zeng A, Chen M, Zhang L, Xu Q (2022) Are transformers effective for time series forecasting?
                  https://doi.org/10.48550/arXiv.2205.13504

                ")), (Huggingface [2023](/article/10.1186/s40854-025-00866-w#ref-CR30 "Huggingface (2023) Yes, transformers are effective for time series forecasting (+ Autoformer).
                  https://huggingface.co/blog/autoformer

                ")).

*TSMixer*: A recent MLP-based approach that challenges Transformer dominance in time series forecasting. It sequentially applies time-mixing and feature-mixing operations, offering a structured alternative to recurrent and attention-based models (S.-A. Chen et al. [2023](/article/10.1186/s40854-025-00866-w#ref-CR11 "Chen SA, Li CL, Yoder N, Arik SO, Pfister T (2023) TSMixer: an all-MLP architecture for time series forecasting.
                  https://doi.org/10.48550/arXiv.2303.06053

                "))

### Incumbent methods

#### eXtreme gradient boosting

As a representative of classical machine learning, we selected XGBoost (T. Chen and Guestrin [2016](/article/10.1186/s40854-025-00866-w#ref-CR10 "Chen T, Guestrin C (2016) XGBoost: a scalable tree boosting system. In: Proceedings of the 22nd ACM SIGKDD international conference on knowledge discovery and data mining. 785–794.
                  https://doi.org/10.1145/2939672.2939785

                ")). Compared with deep learning methods, it is known for its high performance on tabular data (Shwartz-Ziv and Armon [2021](/article/10.1186/s40854-025-00866-w#ref-CR61 "Shwartz-Ziv R, Armon A (2021) Tabular data: deep learning is not all you need.
                  https://doi.org/10.48550/arXiv.2106.03253

                ")). Moreover, it has been a frequent choice in cryptocurrency forecasting in recent years (Sun et al. [2020](/article/10.1186/s40854-025-00866-w#ref-CR63 "Sun X, Liu M, Sima Z (2020) A novel cryptocurrency price trend forecasting model based on LightGBM. Fin Res Lett 32:101084.
                  https://doi.org/10.1016/j.frl.2018.12.032

                ")), (Oyedele et al. [2023](/article/10.1186/s40854-025-00866-w#ref-CR52 "Oyedele AA, Ajayi AO, Oyedele LO, Bello SA, Jimoh KO (2023) Performance evaluation of deep learning and boosted trees for cryptocurrency closing price prediction. Expert Syst Appl 213:119233.
                  https://doi.org/10.1016/j.eswa.2022.119233

                ")), and (Borges and Neves [2020](/article/10.1186/s40854-025-00866-w#ref-CR7 "Borges TA, Neves RF (2020) Ensemble of machine learning algorithms for cryptocurrency investment with different data resampling methods. Appl Soft Comput 90:106187.
                  https://doi.org/10.1016/j.asoc.2020.106187

                ")). For example, (Sun et al. [2020](/article/10.1186/s40854-025-00866-w#ref-CR63 "Sun X, Liu M, Sima Z (2020) A novel cryptocurrency price trend forecasting model based on LightGBM. Fin Res Lett 32:101084.
                  https://doi.org/10.1016/j.frl.2018.12.032

                ")) tested classical machine learning approaches, including LightGBM, SVM, and Random Forest. LightGBM, which is a gradient boosting framework, has emerged as the most effective method.

Boosting is an ensemble method that combines many instances of weak learning algorithm into a single model. This happens sequentially to minimize the loss function *l* together with the regularization term Ω, as shown in Eq. ([1](/article/10.1186/s40854-025-00866-w#Equ1)).

In our case, *l* is a log loss function. *T* is the number of leaves in the tree, and γ is the parameter that controls its regularization. The second part of the regularization term is L2 regularization, where w represents the vector of weights (scores), which are pushed toward zero.

Equation ([3](/article/10.1186/s40854-025-00866-w#Equ3)) illustrates the sequential and additive way in which XGBoost is trained on an example of its *t*-th iteration and *i*-th observation.

#### CNN-LSTM

An expanding body of literature demonstrates the efficacy of Convolutional Neural Networks (CNNs) in time series forecasting and classification tasks, particularly in the context of finance applications (Gudelek et al. [2017](/article/10.1186/s40854-025-00866-w#ref-CR24 "Gudelek MU, Boluk SA, Ozbayoglu AM (2017) A deep learning based stock trading model with 2-D CNN trend detection.
                  https://ieeexplore.ieee.org/document/8285188

                "); Chen and He [2018](/article/10.1186/s40854-025-00866-w#ref-CR13 "Chen S, He H (2018) Stock prediction using convolutional neural network. IOP Conf Ser Mater Sci Eng 435(1):012026.
                  https://doi.org/10.1088/1757-899X/435/1/012026

                "); Sezer and Ozbayoglu [2018](/article/10.1186/s40854-025-00866-w#ref-CR58 "Sezer OB, Ozbayoglu AM (2018) Algorithmic financial trading with deep convolutional neural networks: time series to image conversion approach. Appl Soft Comput 70:525–538.
                  https://doi.org/10.1016/j.asoc.2018.04.024

                ")). This body of research motivates our choice to incorporate the ResNet-LSTM architecture as one of our benchmark models. As demonstrated by Fawaz et al. ([2019](/article/10.1186/s40854-025-00866-w#ref-CR32 "Ismail Fawaz H, Forestier G, Weber J, Idoumghar L, Muller P-A (2019) Deep learning for time series classification: a review. Data Min Knowl Discov 33(4):917–963.
                  https://doi.org/10.1007/s10618-019-00619-1

                ")), the Residual Neural Network (ResNet) variant of CNNs has consistently exhibited superior performance in the classification of diverse univariate and multivariate time series compared to other deep learning architectures. Further research (Tsantekidis et al. [2020](/article/10.1186/s40854-025-00866-w#ref-CR66 "Tsantekidis A, Passalis N, Tefas A, Kanniainen J, Gabbouj M, Iosifidis A (2020) Using deep learning for price prediction by exploiting stationary limit order book features. Appl Soft Comput 93:106401.
                  https://doi.org/10.1016/j.asoc.2020.106401

                "); Alonso-Monsalve et al. [2020](/article/10.1186/s40854-025-00866-w#ref-CR2 "Alonso-Monsalve S, Suárez-Cetrulo AL, Cervantes A, Quintana D (2020) Convolution on neural networks for high-frequency trend prediction of cryptocurrency exchange rates using technical indicators. Expert Syst Appl 149:113250.
                  https://doi.org/10.1016/j.eswa.2020.113250

                ")) reported that the combined use of CNNs and Long Short-Term Memory (LSTM) networks leads to increased predictive performance. This finding is consistent with the study of Grądzki and Wójcik ([2023](/article/10.1186/s40854-025-00866-w#ref-CR23 "Grądzki P, Wójcik P (2023) Is attention all you need for intraday Forex trading? Expert Syst n/a(n/a):e13317.
                  https://doi.org/10.1111/exsy.13317

                ")), who reported notable enhancements when incorporating LSTM layers after ResNet blocks. Hence, we selected the ResNet-LSTM model among the deep learning architectures considered in our study. The use of this architecture is still a common practice, as evidenced by Song and Choi ([2023](/article/10.1186/s40854-025-00866-w#ref-CR62 "Song H, Choi H (2023) Forecasting stock market indices using the recurrent neural network based hybrid models: CNN-LSTM, GRU-CNN, and ensemble models. Appl Sci.
                  https://doi.org/10.3390/app13074644

                ")). Interestingly, in their study, the CNN and RNN layers were tested in two orders, CNN-LSTM and GRU-CNN, both of which performed better than standalone LSTM and GRU.

The combination of CNN and LSTM works seamlessly with 1-D convolutions, which move only across time. In this setup, the CNN works as a feature extractor, whereas the LSTM can capture long-term dependencies between features. The architecture used in our study is depicted in Fig. [1](/article/10.1186/s40854-025-00866-w#Fig1). We use three convolution layers with a ReLU activation function preceded by batch normalization. The number of feature maps and the size of the kernel within each layer are hyperparameters, which are optimized. To improve generalization and reduce overfitting, dropout is applied after the CNN layers, randomly deactivating neurons during training. We utilize a skip connection, introduced by He et al. ([2016](/article/10.1186/s40854-025-00866-w#ref-CR26 "He K, Zhang X, Ren S, Sun J (2016) Deep residual learning for image recognition. IEEE Conf Comput vis Pattern Recogn 2016:770–778.
                  https://doi.org/10.1109/CVPR.2016.90

                ")), between the input and output of the last convolution layer, which has the same shape ensured by appropriate padding and stride.

![Fig. 1](//media.springernature.com/lw685/springer-static/image/art%3A10.1186%2Fs40854-025-00866-w/MediaObjects/40854_2025_866_Fig1_HTML.png)

ResNet-LSTM architecture used in our study

The LSTM network was introduced by Hochreiter and Schmidhuber ([1997](/article/10.1186/s40854-025-00866-w#ref-CR27 "Hochreiter S, Schmidhuber J (1997) Long short-term memory. Neural Comput 9(8):1735–1780.
                  https://doi.org/10.1162/neco.1997.9.8.1735

                ")). It aims to overcome the limitations of classical RNNs in the form of vanishing and exploding gradients. They mitigated those problems by introducing a set of gates: forget gate (*f**t*), update gate (*i**t*), and output gate (*o**t*). The forget gate (4) is responsible for discarding dispensable information from the cell state (*c**t*). It receives the current input *x**t* and the previous hidden state *h**t*−*1* and by applying a sigmoid function, outputs a value between 0 and 1. Values close to 0 indicate ‘forget’, and values close to 1 indicate ‘retain this information’. The input gate decides which value of the cell state should be updated (5) and adds it to the cell state (7) after passing through the hyperbolic tangent function (6). The output gate (8) determines the output of the hidden state (7).

LSTM models in recent years (2015–2020) were the most popular architecture for financial time series forecasting according to the meta-study by Hu et al. ([2021](/article/10.1186/s40854-025-00866-w#ref-CR29 "Hu Z, Zhao Y, Khushi M (2021) A survey of Forex and stock price prediction using deep learning. Appl Syst Innov 4(1):1.
                  https://doi.org/10.3390/asi4010009

                ")). However, owing to the studies quoted above, we decided to consider a combination of CNN and LSTM rather than opting for LSTM alone.

where *W* ∈ ℝhxd and *U* ∈ ℝhxh are weight matrices, *h* is the number of hidden units, *d* is the number of input features and b ∈ ℝh is the bias vector.

#### Attention-LSTM

Following our discussion of LSTM networks in Section "[CNN-LSTM](/article/10.1186/s40854-025-00866-w#Sec6)"—which highlighted their strength in capturing long-term dependencies—this subsection introduces attention-enhanced LSTMs. By allowing the model to focus selectively on the most critical time steps, the attention mechanism can mitigate the shortcomings of plain LSTMs in highly volatile financial settings, such as cryptocurrency markets. Recent studies illustrate the benefits of integrating attention into LSTMs across both traditional equities and cryptocurrencies. Hollis et al. ([2018](/article/10.1186/s40854-025-00866-w#ref-CR28 "Hollis T, Viscardi A, Yi SE (2018) A comparison of LSTMs and attention mechanisms for forecasting financial time series.
                  https://doi.org/10.48550/arXiv.1812.07699

                ")) reported that attention, when added to a vanilla LSTM, helps alleviate long-term dependency issues and modestly improves accuracy in stock forecasting. Chen and Ge ([2019](/article/10.1186/s40854-025-00866-w#ref-CR12 "Chen S, Ge L (2019) Exploring the attention mechanism in LSTM-based Hong Kong stock price movement prediction. Quant Finance 19(9):1507–1515.
                  https://doi.org/10.1080/14697688.2019.1622287

                ")) proposed an AttLSTM for Hong Kong stock movement prediction, which demonstrated statistically significant improvements over standard LSTM. Kim and Kang ([2019](/article/10.1186/s40854-025-00866-w#ref-CR39 "Kim S, Kang M (2019) Financial series prediction using attention LSTM.
                  https://doi.org/10.48550/arXiv.1902.10877

                ")) used an Attention LSTM for the KOSPI 200, showing not only gains in predictive performance but also enhanced interpretability via attention-weight visualization. Peng et al. ([2024](/article/10.1186/s40854-025-00866-w#ref-CR55 "Peng P, Chen Y, Lin W, Wang JZ (2024) Attention-based CNN–LSTM for high-frequency multiple cryptocurrency trend prediction. Expert Syst Appl 237:121520.
                  https://doi.org/10.1016/j.eswa.2023.121520

                ")) combined attention with CNN–LSTM for high-frequency crypto data, emphasizing short-term volatility cues that standard RNNs might overlook. Lee ([2024](/article/10.1186/s40854-025-00866-w#ref-CR42 "Lee M-C (2024) Bitcoin trend prediction with attention-based deep learning models and technical indicators. Systems.
                  https://doi.org/10.3390/systems12110498

                ")) leveraged attention-based LSTM for Bitcoin trend prediction, reporting better stability against sudden price swings—an outcome attributed to the attention layer’s adaptive weighting. Kim et al. ([2022](/article/10.1186/s40854-025-00866-w#ref-CR38 "Kim G, Shin D-H, Choi JG, Lim S (2022) A deep learning-based cryptocurrency price prediction model that uses on-chain data. IEEE Access 10:56232–56248.
                  https://doi.org/10.1109/ACCESS.2022.3177888

                ")) integrated self-attention with multiple LSTM modules using on-chain variables, underscoring that distinct attention heads focusing on different feature subsets can further improve forecast accuracy. Pardeshi et al. ([2024](/article/10.1186/s40854-025-00866-w#ref-CR53 "Pardeshi K, Gill SS, Abdelmoniem AM (2024) Stock market price prediction: a hybrid LSTM and sequential self-attention based approach. pp. 122–140.
                  https://doi.org/10.1201/9781003467199-11

                ")) applied a self-attention mechanism after an LSTM layer, outperforming alternative LSTM- and CNN-based models for financial stock price forecasting. In a similar vein, we employ Multi-Head Attention (MHA) following LSTM encoder output H ∈ ℝ*Txd*, where *T* is the sequence length and *d* is the hidden dimension of the LSTM. Compared with single-head self-attention, MHA divides H into multiple parallel heads, each learning a distinct representation. Specifically, for each head *h* ∈ {1,…,*H*}, we define *Q*h = *H* \(W\_{h}^{Q}\), *K*h = *H* \(W\_{h}^{K}\), *V*h = *H* \(W\_{h}^{V}\), where W matrices are learnable projections. The attention score (*E*h) is computed as a scaled dot product \(\frac{{Q\_{h} K\_{h}^{T} }}{{\sqrt {d\_{H} } }}\) where Eh ∈ ℝ*TxT*. A row-wise softmax transforms those scores into weights (αh), which are finally used to compute the attention output αhVh. The outputs of all the heads are then concatenated and projected by dimension d. The final MHA output is pooled across time via a global average pooling layer and passed to a linear layer.

### Novel methods

#### Transformer

The introduction of the Transformer network by Vaswani et al. ([2017](/article/10.1186/s40854-025-00866-w#ref-CR67 "Vaswani A, Shazeer N, Parmar N, Uszkoreit J, Jones L, Gomez AN, Kaiser Ł, Polosukhin I (2017) Attention is all you need. Advances in neural information processing systems. 30.
                  https://proceedings.neurips.cc/paper_files/paper/2017/hash/3f5ee243547dee91fbd053c1c4a845aa-Abstract.html

                ")) marked a significant milestone in the field of Artificial Intelligence. Notably, one of its most renowned applications, ChatGPT, achieved unprecedented growth, attracting 100 million users within a mere two months of its launch. Given the Transformer’s exceptional performance in handling sequential data, extending its application to time series problems is a natural progression. In recent years, several studies have been published (Zhou et al. [2022](/article/10.1186/s40854-025-00866-w#ref-CR75 "Zhou T, Ma Z, Wen Q, Wang X, Sun L, Jin R (2022) FEDformer: frequency enhanced decomposed transformer for long-term series forecasting.
                  https://doi.org/10.48550/arXiv.2201.12740

                "), [2021](/article/10.1186/s40854-025-00866-w#ref-CR74 "Zhou H, Zhang S, Peng J, Zhang S, Li J, Xiong H, Zhang W (2021) Informer: beyond efficient transformer for long sequence time-series forecasting.
                  https://doi.org/10.48550/arXiv.2012.07436

                "); Wu et al. [2022](/article/10.1186/s40854-025-00866-w#ref-CR70 "Wu H, Xu J, Wang J, Long M (2022) Autoformer: decomposition transformers with auto-correlation for long-term series forecasting.
                  https://doi.org/10.48550/arXiv.2106.13008

                ")), claiming the superiority of Transformer architectures in long-term time series forecasting over other deep learning and classical methods. First, in this series, Informer, proposes two improvements in the typical encoder-decoder Transformer architecture. First, it introduces the ProbSparse self-attention mechanism leveraging the fact because, in the canonical self-attention mechanism, usually, only a few dot product pairs have significant attention scores, whereas the majority of them are negligible. On the basis of this observation, ProbSparse self-attention attends only to a predefined number of dominant queries, which are selected on the basis of their dissimilarity to other queries, as such queries are more likely to contain useful information. Owing to this innovation, the Informer achieves O(LlogL) in time complexity and memory usage, which is an improvement over the O(L2) of canonical self-attention. The second innovation lies in switching from autoregressive predictions, which are known to compound errors over time, to predicting the whole forecasting horizon in one forward pass.

Shortly thereafter Autoformer was introduced by Wu et al. ([2022](/article/10.1186/s40854-025-00866-w#ref-CR70 "Wu H, Xu J, Wang J, Long M (2022) Autoformer: decomposition transformers with auto-correlation for long-term series forecasting.
                  https://doi.org/10.48550/arXiv.2106.13008

                ")), which was built on the same encoder-decoder architecture of the Transformer as Informer depicted in Fig. [2](/article/10.1186/s40854-025-00866-w#Fig2). Its distinctive feature is the replacement of the standard attention block with an autocorrelation mechanism combined with decomposition blocks. Owing to the autocorrelation block, it discovers similarity within subseries on the basis of their periodicity while still having O(LlogL) complexity. The decomposition block separates series into trend and seasonal parts. It is applied to the intermediate predictions within the Autoformer block working interchangeably with the autocorrelation block. The autocorrelation block conforms to self-attention convention hence, it was possible to replace it seamlessly. Keys and queries are used to compute autocorrelation with a fast Fourier transform. Next, the top autocorrelation delays are selected according to the predefined hyperparameter and passed through the softmax function. The value matrix is rolled according to the top delays and multiplied through the output of the aforementioned softmax step.

![Fig. 2](//media.springernature.com/lw685/springer-static/image/art%3A10.1186%2Fs40854-025-00866-w/MediaObjects/40854_2025_866_Fig2_HTML.png)

Autoformer encoder-decoder architecture

The FEDformer is another variation of the same architecture as the Autoformer and Informer. It also achieves computational efficiency by leveraging sparse representation in the self-attention block, this time by leveraging series representation in the frequency domain by applying a Fourier transform, instead of a canonical dot product. Inside Frequency Enhanced Block, series in the time domain *X**1*(*t*),…., *X**m*(*t*) is converted to the frequency domain *A* = (*a**1**, a*2,…, *a**m*) ⊤ ∈ ℝmxd by Fourier transform, where *m* is the number of input features and *d* is the number of Fourier components. Next, a predefined number of Fourier (*s*) components is selected at random (*s* < *d*). This operation is applied to keys, queries, and values, which are used to perform standard attention computation and then transformed back to the time domain with an inverse Fourier transform.

Each of these subsequent architectures shows improved forecasting ability on the same set of time series benchmarks. However, not all researchers were convinced that these increasingly sophisticated changes to the self-attention mechanism drive performance gains. Zeng et al. ([2022](/article/10.1186/s40854-025-00866-w#ref-CR71 "Zeng A, Chen M, Zhang L, Xu Q (2022) Are transformers effective for time series forecasting?
                  https://doi.org/10.48550/arXiv.2205.13504

                ")) hypothesized that the main source of improvement was direct multistep forecasting and not alterations in the self-attention module. To validate their hypothesis, they trained a simple linear neural network, which makes predictions in a direct multistep fashion. Surprisingly, “embarrassingly simple linear models” outperformed the above-mentioned Transformer models on all long time series benchmarks. The last word in this discussion thus far belongs to Huggingface ([2023](/article/10.1186/s40854-025-00866-w#ref-CR30 "Huggingface (2023) Yes, transformers are effective for time series forecasting (+ Autoformer).
                  https://huggingface.co/blog/autoformer

                ")). In their blogpost, they claim that Transformers are effective for time series forecasting, as in their benchmarking, Autoformer outperformed the same simple linear model (Zeng et al. [2022](/article/10.1186/s40854-025-00866-w#ref-CR71 "Zeng A, Chen M, Zhang L, Xu Q (2022) Are transformers effective for time series forecasting?
                  https://doi.org/10.48550/arXiv.2205.13504

                ")). This conclusion is attributed to making models more comparable: both are trained as univariate models and have similar numbers of parameters. Interestingly, the best performance in this study was offered by the vanilla Transformer. In our study, in addition to those complex Transformers, we also included the simple Transformer encoder network, which yielded the best results in a study focused on the Forex market (Grądzki and Wójcik [2023](/article/10.1186/s40854-025-00866-w#ref-CR23 "Grądzki P, Wójcik P (2023) Is attention all you need for intraday Forex trading? Expert Syst n/a(n/a):e13317.
                  https://doi.org/10.1111/exsy.13317

                ")). On the basis of this work, we anticipate that Transformers will similarly demonstrate strong performance when applied to cryptocurrency data.

Since our study is about time series classification, a few modifications were needed in the encoder-decoder architecture used in Autoformer and FEDformer. We applied those only when necessary, leaving most of the architecture and parameters unchanged. As per the original setup, the input to the encoder part is the whole training sequence—in our case, 96-time steps across 33 variables. The encoder is the output of the decomposition function applied to the subset of the training sequence; in our case, the decomposition of the last 48 steps from training sequences is padded with one additional step for the prediction. In the original implementation, this padding is equal to the prediction horizon, and it is computed jointly, not in an autoregressive manner. Autoformer makes a prediction for the whole multivariate series, thus at the output it produces a vector with 33 values, in our case, corresponding to one-step prediction for all variables. We pass those 33 variables through softmax layer while also switching from mean squared error loss to binary cross-entropy loss to obtain classification predictions for next-bar labeling. For the Triple Barrier labeling, explained in chapter 4.5, we make predictions for the full prediction horizon, up to the vertical barrier. For the trading and accuracy metrics, we classify the predictions according to the first barrier they breach.

#### TSMixer

Time Series Mixer (TSMixer) was introduced by Google Cloud AI Research (Chen et al. [2023](/article/10.1186/s40854-025-00866-w#ref-CR11 "Chen SA, Li CL, Yoder N, Arik SO, Pfister T (2023) TSMixer: an all-MLP architecture for time series forecasting.
                  https://doi.org/10.48550/arXiv.2303.06053

                ")) to offer an effective multilayer perceptron (MLP)-based model for long-term multivariate forecasting. While its design is inspired by MLP-Mixer architectures from computer vision (Tolstikhin et al. [2021](/article/10.1186/s40854-025-00866-w#ref-CR65 "Tolstikhin I, Houlsby N, Kolesnikov A, Beyer L, Zhai X, Unterthiner T, Yung J, Steiner A, Keysers D, Uszkoreit J, Lucic M, and Dosovitskiy A, (2021). MLP-mixer: an all-MLP architecture for vision.
                  https://doi.org/10.48550/arXiv.2105.01601

                ")), it builds directly on findings from Zeng et al. ([2022](/article/10.1186/s40854-025-00866-w#ref-CR71 "Zeng A, Chen M, Zhang L, Xu Q (2022) Are transformers effective for time series forecasting?
                  https://doi.org/10.48550/arXiv.2205.13504

                ")), who challenged the effectiveness of Transformer-based models for time series forecasting. One of the hypotheses behind this phenomenon is that the presence of uninformative covariates can lead to a deterioration in model performance. The authors demonstrated that this model performs significantly better than the FEDformer, Autoformer, and Informer models even in the presence of uninformative auxiliary covariates and achieves performance similar to that of state-of-the-art univariate models. The TSMixer proposes the use of an MLP applied sequentially to time (time-mixing) and feature (feature-mixing) dimensions, as illustrated in Fig. [3](/article/10.1186/s40854-025-00866-w#Fig3). In this case, the MLP is applied directly to a 2D matrix. Hence, in time mixing, weights and biases are fixed for each feature, whereas in feature mixing, weights and biases are fixed for each time step. The purpose of time mixing MLPs is to capture temporal dependencies or patterns that are consistent across all features, whereas feature mixing aggregates information from different features at a given time step. Notably, despite the authors’ inspiration of linear models, the TSMixer is nonlinear because of the rectified linear unit (ReLU) activation function applied in each MLP. Since our task is time series classification, we flatten the output of the TSMixer, pass it through a dense layer with a ReLU or Gaussian error linear unit (GeLU) activation function, and apply a softmax layer at the end. The number of mixing blocks, size of feed-forward layers, activation function, normalization type (batch or layer), and dropout value are hyperparameters optimized during training. Given the unique characteristics of financial time series, such as high volatility and a low signal-to-noise ratio, our empirical analysis aims to assess whether the findings of Zeng et al. ([2022](/article/10.1186/s40854-025-00866-w#ref-CR71 "Zeng A, Chen M, Zhang L, Xu Q (2022) Are transformers effective for time series forecasting?
                  https://doi.org/10.48550/arXiv.2205.13504

                ")) and Chen et al. ([2023](/article/10.1186/s40854-025-00866-w#ref-CR11 "Chen SA, Li CL, Yoder N, Arik SO, Pfister T (2023) TSMixer: an all-MLP architecture for time series forecasting.
                  https://doi.org/10.48550/arXiv.2303.06053

                ")) hold in the context of cryptocurrency markets.

![Fig. 3](//media.springernature.com/lw685/springer-static/image/art%3A10.1186%2Fs40854-025-00866-w/MediaObjects/40854_2025_866_Fig3_HTML.png)

TSMixer building block composed of time and feature mixing

## Data

### Time split

The data on the quotations of cryptocurrencies covering the period from January 1, 2018, to June 30, 2023 used in our study come from Binance. Binance offers free access to complete tick-level data, which is required for our study. We use data starting at the beginning of 2018 and utilize a quarterly expanding window, as presented in Fig. [4](/article/10.1186/s40854-025-00866-w#Fig4). The first test quarter is Q2 2022, and the last one is Q2 2023, which gives us five quarters to test the predictive capabilities of the tested models. The length of the test period for our study was dictated by data availability from Binance. Given that deep learning models require substantial amounts of training data, we were constrained in how much historical data could be allocated to the test set without compromising model training robustness. Test sets are used for backtest analysis. Given the various shortcomings of a backtest (Luo et al. [2014](/article/10.1186/s40854-025-00866-w#ref-CR47 "Luo Y, Alvarez M, Wang S, Jussa J, Wang A, and Rohal G (2014) Seven sins of quantitative investing. Deutsche Bank Markets Research, White paper")), we performed it as reliably as possible—testing for two currencies and over many out-of-sample periods—ensuring that none of the observations from the training and validation sets were used in the test set, reporting all the experiments, including unsuccessful ones, keeping data sampling and target labeling parameters fixed, and not overoptimizing them. While our test period does not include the peak of the 2021 bull market, it spans both bullish and bearish phases, ensuring that our findings are not biased toward a single regime. Extreme market events, such as the rapid surge in cryptocurrency prices during the 2021 rally, pose unique challenges for predictive modeling, as they are often characterized by high speculative activity and reduced forecastability. Although evaluating model performance under such conditions is valuable, it also carries the risk of overfitting to atypical trends that may not generalize across different market states. Instead, our test period includes volatile yet more structurally diverse market conditions, making it a practical benchmark for real-world algorithmic trading strategies. Future research could explore the effectiveness of different sampling and modeling approaches in extreme boom‒and‒bust cycles to assess whether the methodologies proposed in this study maintain their robustness under highly speculative conditions.

![Fig. 4](//media.springernature.com/lw685/springer-static/image/art%3A10.1186%2Fs40854-025-00866-w/MediaObjects/40854_2025_866_Fig4_HTML.png)

Expanding time window used in our study

While Binance is the largest cryptocurrency exchange by trading volume, it faces fierce competition from many other centralized exchanges as well as decentralized ones. This raises the question of whether using Binance data introduces sample bias. Research on arbitrage opportunities across exchanges (Crépellière et al. [2023](/article/10.1186/s40854-025-00866-w#ref-CR15 "Crépellière T, Pelster M, Zeisberger S (2023) Arbitrage in the market for cryptocurrencies. J Financ Mark 64:100817.
                  https://doi.org/10.1016/j.finmar.2023.100817

                ")) suggests that while price differences exist, they tend to be short-lived and arbitrageable, indicating a high degree of price synchronization across major platforms. At the same time, studies such as Shu et al. ([2023](/article/10.1186/s40854-025-00866-w#ref-CR60 "Shu A, Cheng F, Han J, Liang Z, Pan Z (2023) Arbitrage across different Bitcoin exchange venues: perspectives from investor base and market related events. Account Financ 63(5):5183–5210.
                  https://doi.org/10.1111/acfi.13102

                ")) demonstrate that profitable arbitrage strategies can still be found, suggesting that exchange-specific frictions remain. Further insights into the emergence and feasibility of arbitrage are provided by Kristoufek and Bouri ([2023](/article/10.1186/s40854-025-00866-w#ref-CR40 "Kristoufek L, Bouri E (2023) Exploring sources of statistical arbitrage opportunities among Bitcoin exchanges. Fin Res Lett 51:103332.
                  https://doi.org/10.1016/j.frl.2022.103332

                ")), who show that statistical arbitrage opportunities across major Bitcoin exchanges are more likely during periods of high volatility and network congestion, whereas elevated trading volume and on-chain transfer activity tend to reduce such opportunities. Crucially, they noted that operational frictions, such as delayed transaction confirmations and exchange-specific policies, often prevent traders from fully exploiting these price discrepancies. This finding reinforces the view that while price deviations exist, they are not always practically exploitable, further justifying our focus on Binance as a representative and liquid venue for modeling market dynamics. Future research could incorporate data from multiple exchanges to further validate our findings and account for potential exchange-specific effects.

Additionally, our selection of Bitcoin and Ethereum was driven primarily by their deep liquidity, which minimizes execution frictions such as slippage and order book constraints. High-liquidity assets ensure more reliable execution of trading signals, making our findings applicable to real-world trading conditions. Including lower-liquidity cryptocurrencies would require explicitly modeling these factors or making simplifying assumptions that could reduce the practical applicability of our results. Moreover, our study prioritizes depth over breadth and rigorously evaluates different sampling, labeling, and modeling techniques for these two major cryptocurrencies. Additionally, survivorship bias can be quite acute in the cryptocurrency space, where many projects go bankrupt or are outright fraud. Therefore, we focused on popular and highly traded currencies. An additional caveat concerns market regimes: although there are rallies and sharp declines in our test set, they were not as prominent as those experienced in the past. Oyedele et al. ([2023](/article/10.1186/s40854-025-00866-w#ref-CR52 "Oyedele AA, Ajayi AO, Oyedele LO, Bello SA, Jimoh KO (2023) Performance evaluation of deep learning and boosted trees for cryptocurrency closing price prediction. Expert Syst Appl 213:119233.
                  https://doi.org/10.1016/j.eswa.2022.119233

                ")) analyzed the impact of testing data for cryptocurrencies coming from outside of the training distribution. With the deep learning models, the results were still satisfactory, although, as expected, the errors were greater for a scenario in which the peak in the test data was greater than that in the training data. Importantly, when analyzing the results in our study, the model was not tested on data falling outside of the training values.

### Systematic time sampling

The financial markets, particularly cryptocurrencies—which are unique owing to their 24/7 trading capability—offer data with millisecond precision and detailed price information down to individual ticks. Given the size of this data, aggregation methods are essential for managing the information volume. The algorithmic trading literature relies predominantly on data aggregation based on regular time intervals, leading to the use of uniformly spaced data for training machine learning models. The target variable is typically based on the next candlestick, with predictions aimed at forecasting the direction (classification) or both magnitude and direction (regression) of the upcoming candle. For example, Fig. [5](/article/10.1186/s40854-025-00866-w#Fig5) illustrates BTCUSDT data sampled hourly, yet this representation falls short of accurately reflecting market dynamics. Trades can occur every millisecond, and there is no inherent significance in round-hour intervals, as demonstrated by Fig. [6](/article/10.1186/s40854-025-00866-w#Fig6). This figure displays the volume distribution from January 2018 to June 2023, which is aggregated into minute-wise buckets. This visualization reveals that if automated trading systems predominantly relied on systematically sampled data, significant volume spikes at the beginning or end of each hour would be expected. However, this is not observed in the data. This insight underscores the inadequacy of round-hour intervals in capturing the true dynamics and fluidity of cryptocurrency markets. Furthermore, financial markets are known for their volatility clustering (Cont [2007](/article/10.1186/s40854-025-00866-w#ref-CR14 "Cont R (2007) Volatility clustering in financial markets: empirical facts and agent-based models. In: Teyssière G, Kirman AP (eds) Long memory in economics. Springer, Berlin, pp 289–309.
                  https://doi.org/10.1007/978-3-540-34625-8_10

                ")), with volatility often correlating with volume. Even in the brief period shown in Fig. [5](/article/10.1186/s40854-025-00866-w#Fig5), this pattern is evident: a rapid price decline coupled with increased volume on April 11–12, following a period of minimal price movement and low volume on April 9–10. Ideally, an algorithmic investment strategy should quickly adapt to dynamic changes and filter out periods of low activity. However, systematic time sampling lacks this responsiveness. Researchers frequently depend on daily closing prices (Jiang [2021](/article/10.1186/s40854-025-00866-w#ref-CR33 "Jiang W (2021) Applications of deep learning in stock market prediction: recent progress. Expert Syst Appl 184:115537.
                  https://doi.org/10.1016/j.eswa.2021.115537

                ")), which is an important limitation. Closing prices are known only after the market closes, whereas the next day’s opening price can differ significantly. This issue is somewhat mitigated in the cryptocurrency market, which operates nonstop. Consequently, our study includes a 24-h interval corresponding to daily prices, along with one- and twelve-hour intervals, potentially benefiting from training with a higher data volume. Intervals shorter than this value are unlikely to offset transaction costs effectively.

![Fig. 5](//media.springernature.com/lw685/springer-static/image/art%3A10.1186%2Fs40854-025-00866-w/MediaObjects/40854_2025_866_Fig5_HTML.png)

BTCUSDT candlestick chart sampled every hour

![Fig. 6](//media.springernature.com/lw685/springer-static/image/art%3A10.1186%2Fs40854-025-00866-w/MediaObjects/40854_2025_866_Fig6_HTML.png)

Volume distribution for BTCUSDT from January 2018 to June 2023 aggregated into minute-wise buckets

### Dollar and volume bars

The first type of information-driven bar, addressing the limitations identified previously, includes dollar and volume bars. This approach samples data points upon reaching preset monetary thresholds (for dollar bars) or specific trading volumes (for volume bars). This configuration ensures more frequent bar generation during active market periods and less so during quieter periods. Figure [7](/article/10.1186/s40854-025-00866-w#Fig7) shows how volume bars record more frequent data points during the active period of April 11–12 and fewer during the quieter phase of April 9–10.

![Fig. 7](//media.springernature.com/lw685/springer-static/image/art%3A10.1186%2Fs40854-025-00866-w/MediaObjects/40854_2025_866_Fig7_HTML.png)

BTCUSDT sampled every 5000 BTCs exchanged on the market

Given the high volatility and swift value changes characteristic of the cryptocurrency market, dollar bars may be more effective than volume bars. This effectiveness is based on the premise that dollar bars, representing capital in terms of fiat currency, align more closely with investor concerns. For example, 5,000 BTCs were valued at approximately 67 million dollars at the start of our dataset but reached 334 million dollars on November 8, 2021. Utilizing dollar bars helps to stabilize these substantial value fluctuations. However, applying volume and dollar bars to cryptocurrencies is not without challenges. A significant concern is the prevalence of wash trading, where crypto exchanges artificially inflate their trading volumes to project an illusion of high liquidity, as noted by Pennec et al. ([2021](/article/10.1186/s40854-025-00866-w#ref-CR56 "Pennec GL, Fiedler I, Ante L (2021) Wash trading at cryptocurrency exchanges. Fin Res Lett 43:101982.
                  https://doi.org/10.1016/j.frl.2021.101982

                ")). Despite this, in the absence of a more reliable volume metric, this study relies on data reported by Binance. Threshold selection for dollar and volume bars is inherently asset specific, as different cryptocurrencies exhibit varying levels of trading activity and liquidity. The chosen thresholds for dollar and volume bars were selected to balance feasibility for trading strategies and computational constraints. Bars need to be frequent enough to provide actionable signals but not excessively frequent, which increases transaction costs and reduces practical applicability. For ETHUSDT, the thresholds for volume bars were set at 30 K, 50 K, and 100 K ETH, and those for dollar bars were set at $50 M, $100 M, and $150 M. For BTCUSDT, the thresholds were 5 K, 10 K, and 20 K BTC for volume bars and $100 M, $200 M, and $300 M for dollar bars. We examined the resulting number of bars over the dataset's 2,007-day period. For the ETH volume bars, the thresholds yielded 40,557, 24,338, and 12,171 bars, whereas the ETH dollar bars resulted in 31,042, 15,523, and 10,350 bars. These values translate to an average of 20 to 5 observations per day, which is sufficient for model training while maintaining a realistic trading frequency. Similarly, for BTC, dollar bars resulted in 36,039, 18,021, and 12,014 observations, whereas volume bars produced 32,940, 16,472, and 8,236 observations. Additionally, deep learning models require a minimum number of training samples to learn meaningful patterns. If thresholds were set too high, the bar frequency would drop excessively, resulting in too few observations for model training. Conversely, thresholds that are too low could lead to excessively frequent bars, introducing high transaction costs and making real-world execution less feasible. Thus, our threshold selection was guided by a trade-off between maintaining realistic execution constraints and ensuring adequate training data for deep learning models.

### CUSUM filter and range bars

The CUSUM filter, as delineated by Eq. ([12](/article/10.1186/s40854-025-00866-w#Equ12)), is implemented to identify sequences of upward or downward price movements that surpass a predetermined threshold, denoted as *h*. A new bar is sampled when either of the running sums, \(S\_{t}^{ + }\) or \(S\_{t}^{ - }\), exceeds this threshold. The design of this filter, which is maintained by the min and max operators, ensures that a positive sum does not become negative and vice versa. For example, with a threshold of 2%, if there is an initial 1% upward movement followed by a 2% downward shift, both in a straight line, the CUSUM filter triggers the sampling of the next bar, as the sequence of movements surpasses our threshold. However, the relative price difference between the closing price of the preceding bar and the new bar will be less than 2%.

where *r**t* is the return between periods *t* and *t-1* and the initial values for \(S\_{0}^{ + }\) and \(S\_{0}^{ - }\) are set to 0.

An alternative to this approach is that of range bars, another sampling technique evaluated in our study. Range bars are sampled only when the price difference between successive bars exceeds a set threshold, as defined in Eq. ([13](/article/10.1186/s40854-025-00866-w#Equ13)).

where *P**t* is the price at time *t*, *P**t*−*1* is the price of the last sampled bar and *R* is a fixed percentage threshold. Once this condition is met, a new bar is created, recording the open, high, low, and close prices within the interval. Range bars tend to sample less frequently than the CUSUM filter for the same threshold level, as illustrated in Fig. [10](/article/10.1186/s40854-025-00866-w#Fig10). In our initial experimental setup, we consider thresholds of 1%, 2%, and 3% for both the CUSUM filter and range bars, following the same guideline to strike the balance between intraday sampling and excessive trading, as explained in Section "[Dollar and volume bars](/article/10.1186/s40854-025-00866-w#Sec14)". To increase the computational efficiency of these sampling algorithms, we follow Borges and Neves ([2020](/article/10.1186/s40854-025-00866-w#ref-CR7 "Borges TA, Neves RF (2020) Ensemble of machine learning algorithms for cryptocurrency investment with different data resampling methods. Appl Soft Comput 90:106187.
                  https://doi.org/10.1016/j.asoc.2020.106187

                ")), who also utilized 1-min Binance data for their sampling techniques. While applying the CUSUM filter and range bars to tick-level data could theoretically capture even finer price movements, our chosen thresholds result in a moderate sampling frequency, generating only a few bars per day on average. Given this, we assume that operating at the highest frequency is not critical for our study, as our focus is on capturing meaningful market structure rather than microsecond-level fluctuations.

An example illustrating the differences between the CUSUM filter, range bars, and time sampling is depicted in Fig. [8](/article/10.1186/s40854-025-00866-w#Fig8). In this example, the CUSUM filter was triggered twice, resulting in two samples. The range bar was sampled once in the middle of the dataset, and the 15-min time bar was sampled once at the end of the dataset. Figure [9](/article/10.1186/s40854-025-00866-w#Fig9) illustrates the differences between CUSUM filter sampling, range bars, and traditional time bars using Bitcoin price data. This visual comparison helps clarify how each method samples data differently on the basis of price movements and thresholds. Importantly, the sampled points signify the moment when a new bar is created; it is still a typical OHLC bar, but the period is not fixed—it is instead driven by price action rather than regular intervals of time.

![Fig. 8](//media.springernature.com/lw685/springer-static/image/art%3A10.1186%2Fs40854-025-00866-w/MediaObjects/40854_2025_866_Fig8_HTML.png)

Examples of data sampling via the CUSUM filter (2%), range bars (2%), and 15-min time bars

![Fig. 9](//media.springernature.com/lw685/springer-static/image/art%3A10.1186%2Fs40854-025-00866-w/MediaObjects/40854_2025_866_Fig9_HTML.png)

BTCUSDT sampled according to the 2% CUSUM filter (left) and 2% range bar (right)

Given the practical importance of our work, we also tested the implementation of these sampling techniques on an actual data stream from the Binance API and encountered no difficulties.

### Target labeling

The Triple Barrier method, introduced by Lopez de Prado (2018), represents an important innovation in label generation for algorithmic trading. This method involves establishing three distinct barriers to classify the potential outcome of a trade. These barriers include an upper profit-taking level, a lower stop-loss level, and a temporal barrier, which defines the trade’s time horizon. The three barriers are set at a predefined distance above and below the entry price, as depicted in Fig. [10](/article/10.1186/s40854-025-00866-w#Fig10). This approach provides a more nuanced and realistic representation of market scenarios, aiding in the development of more accurate trading algorithms. Unlike the alternative and dominant target labeling method, which is based on the next bar and tends to learn from many noisy observations, the Triple Barrier method offers a more authentic reflection of the trading reality. Next-bar labeling is a convenient and intuitive method; however, it often leads to excessive trading, as consecutive returns are not correlated. The machine learning model will frequently switch between long and short positions and incur a lot of costs. In the case of intraday trading, those transaction costs can quickly erode any potential gains. For example, in the scenario presented in Fig. [10](/article/10.1186/s40854-025-00866-w#Fig10), the initial price movement is downward. However, predicting such small movements is not only impractical but also often infeasible. Under the Triple Barrier method, this observation would be classified as an upward movement, since the magnitude of the movement that is meaningful for a trader is up. This difference in labeling between Next-bar and the Triple Barrier is presented for more time steps in Table [1](/article/10.1186/s40854-025-00866-w#Tab1). Trading based on the Triple Barrier method also offers protection in the case of a significant price swing in an unfavorable direction. Here, stop-loss is triggered, whereas in typical next-bar labeling, the authors often wait for the bar to close before deciding whether to keep the transaction open or not. In our experiment, we benchmark the Triple Barrier method with labeling on the basis of the next bar movement. Our hypothesis is that models trained on the Triple Barrier labeling outperform those trained on next-bar labeling in terms of trading profit. In the initial setup of our experiment, we assumed 24 periods for vertical barriers and symmetric upper and lower barriers of 2.5% for the most frequent input intervals and 5% for the other intervals. Barriers can be dynamic and linked with asset volatility. However, since we did not find similar studies that would advise on the optimal thresholds and for convenience of analysis, we decided to make them static over the entire period. In practice, the specific values used in the definition of the Triple Barrier should be determined by the investor, as they often define these parameters when engaging in a trade.

![Fig. 10](//media.springernature.com/lw685/springer-static/image/art%3A10.1186%2Fs40854-025-00866-w/MediaObjects/40854_2025_866_Fig10_HTML.png)

Example of the Triple Barrier method applied to BTCUSDT 1-h data

The labels for 2022-04-13 correspond to Fig. [10](/article/10.1186/s40854-025-00866-w#Fig10) and assume the same parameters. Next-bar labeling frequently flips between labels, forcing the model to learn even very small price movements. In contrast, Triple Barrier labeling focuses on more substantial movements, which are better aligned with a realistic trading strategy (Table [1](/article/10.1186/s40854-025-00866-w#Tab1)).

### Feature engineering

To enhance our dataset, in addition to OHLC and volume, we considered a set of commonly used technical indicators (Alonso-Monsalve et al. [2020](/article/10.1186/s40854-025-00866-w#ref-CR2 "Alonso-Monsalve S, Suárez-Cetrulo AL, Cervantes A, Quintana D (2020) Convolution on neural networks for high-frequency trend prediction of cryptocurrency exchange rates using technical indicators. Expert Syst Appl 149:113250.
                  https://doi.org/10.1016/j.eswa.2020.113250

                "); Borges and Neves [2020](/article/10.1186/s40854-025-00866-w#ref-CR7 "Borges TA, Neves RF (2020) Ensemble of machine learning algorithms for cryptocurrency investment with different data resampling methods. Appl Soft Comput 90:106187.
                  https://doi.org/10.1016/j.asoc.2020.106187

                "); Gudelek et al. [2017](/article/10.1186/s40854-025-00866-w#ref-CR24 "Gudelek MU, Boluk SA, Ozbayoglu AM (2017) A deep learning based stock trading model with 2-D CNN trend detection.
                  https://ieeexplore.ieee.org/document/8285188

                "); Li and Tam [2017](/article/10.1186/s40854-025-00866-w#ref-CR43 "Li Z, Tam V (2017) A comparative study of a recurrent neural network and support vector machine for predicting price movements of stocks of different volatilites. IEEE Symp Ser Comput Intell 2017:1–8.
                  https://doi.org/10.1109/SSCI.2017.8285319

                "); Ibrahim et al. [2021](/article/10.1186/s40854-025-00866-w#ref-CR31 "Ibrahim A, Kashef R, Corrigan L (2021) Predicting market movement direction for bitcoin: a comparison of time series modeling methods. Comput Electr Eng 89:106905.
                  https://doi.org/10.1016/j.compeleceng.2020.106905

                "); Gradojevic et al. [2023](/article/10.1186/s40854-025-00866-w#ref-CR22 "Gradojevic N, Kukolj D, Adcock R, Djakovic V (2023) Forecasting Bitcoin with technical analysis: a not-so-random forest? Int J Forecast 39(1):1–17.
                  https://doi.org/10.1016/j.ijforecast.2021.08.001

                ")) listed below. The chosen features capture trend-following signals (moving averages, MACD), momentum conditions (RSI, Stochastic Oscillator, Williams %R), volatility patterns (Bollinger Bands, historical returns), and market strength (CMF, MFI), all of which are widely used to assess market dynamics and identify potential trading opportunities. The utility of technical analysis and its associated indicators has long been debated. Gerritsen et al. ([2020](/article/10.1186/s40854-025-00866-w#ref-CR20 "Gerritsen DF, Bouri E, Ramezanifar E, Roubaud D (2020) The profitability of technical trading rules in the Bitcoin market. Financ Res Lett 34:101263.
                  https://doi.org/10.1016/j.frl.2019.08.011

                ")) provide important empirical evidence on their performance in the Bitcoin market, showing that among several classical trading rules, only the trading range breakout rule consistently outperformed a buy-and-hold benchmark. Other commonly used indicators, such as on-balance volume, did not achieve statistical significance, whereas some, including the Relative Strength Index (RSI) and Bollinger Bands, underperformed the benchmark. Importantly, the findings suggest that the Bitcoin market is not fully efficient, thereby justifying further exploration of methods to uncover and exploit potential inefficiencies. In our approach, we include a broad set of technical indicators as input features to deep learning models, allowing the algorithm to assess their joint informational content. Additionally, time-based features (sine and cosine transformations of hour and weekday) were included to encode seasonality effects, which are relevant for intraday trading strategies. All of these features were computed for all the data sampling techniques after the sampling procedure. All features were scaled before entering the training process by subtracting the mean and dividing by the standard deviation. The utility of this feature engineering approach is discussed in Section "[Sensitivity analysis](/article/10.1186/s40854-025-00866-w#Sec23)". Technical indicators were computed using the pandas-ta Python package.

Exponential moving averages and standard deviations of close prices of different periods: 5, 10, 15, 20 and 50.

Moving Average Convergence/Divergence (MACD) with exponential moving averages of the last 12 and 26 bars.

Relative Strength Index (RSI) for periods of 6, 10, and 14 bars.

Stochastic Oscillator (%K and %D) with a lookback period of 14 bars.

Williams %R with lookback period equal to the 14 last periods.

Bollinger bands for 2 standard deviations and a period length of 5.

Historical returns between consecutive periods.

Chaikin Money Flow (CMF) for 21 periods.

Money Flow Index for the last 14 periods.

Sine and cosine of the hour and weekday. These four features were not used for FEDformer and Autoformer, as they have their own time encodings.

## Empirical results

### Experiment setup and evaluation metrics

In the domain of neural networks, researchers face the challenge of making optimal architectural decisions with respect to many hyperparameters, which results in countless possible networks. To address this variability, we initiate our training process by conducting hyperparameter optimization. The optimal model configuration is determined through evaluation of the initial validation dataset, and this chosen configuration remains consistent throughout the subsequent training phases. To prevent overfitting further, we implement early stopping, ensuring that training halts once validation performance ceases to improve. Additionally, to increase the robustness of the selected configuration, we identify the three most effective model variants within the same network type for each cryptocurrency on the basis of their validation performance. When making predictions on the test dataset, we employ an ensemble consisting of equitable voting among these three models. To identify these optimal configurations, we leverage the Hyperband implementation from the Keras Tuner package. The Hyperband tuner (Li et al. [2017](/article/10.1186/s40854-025-00866-w#ref-CR44 "Li L, Jamieson K, DeSalvo G, Rostamizadeh A, Talwalkar A (2017) Hyperband: a novel bandit-based approach to hyperparameter optimization. J Mach Learn Res 18(1):6765–6816")) functions by efficiently exploring the spectrum of hyperparameter settings. Instead of exhaustively testing every conceivable combination, it employs a resource-efficient strategy that assigns different budgets to swiftly identify promising configurations and allocate additional resources to them. This approach enhances the efficiency of identifying the most suitable model settings in an automated manner. Hyperband was applied to ResNet-LSTM, TSMixer, and Vanilla Transformer encoder. For Autoformer and FEDformer, which were developed in a different framework (PyTorch), we relied on the hyperparameters provided by the original authors in their code repository. This was partially motivated by the substantial size of those models, making it computationally expensive to tune their hyperparameters from scratch.

XGBoost was fine-tuned via a randomized cross-validation search from the scikit-learn package, ensuring that the temporal split of the data was maintained. To increase the reliability of our results and mitigate the risk of chance findings, each model for each period was trained three times with different seeds, and the results were averaged.

The design of our experiment led to the training of a substantial number of models for a single cryptocurrency—2700 in total. This figure arises from the combination of five distinct bars, three values per bar definition, two target labels, and six models, each estimated three times over five periods. The application of this complex framework requires considerable computational resources. Therefore, we decided to limit our study to the two most popular cryptocurrencies – Bitcoin and Ethereum. To expedite the training of the models, we provisioned a ml.g4dn.xlarge virtual machine from Amazon Web Services, which is equipped with an NVIDIA T4 GPU.

For trading evaluation, we assume that the system can take both long and short positions, a functionality provided by Binance in margin trading. We account for 0.1% of the transaction cost for opening and closing trades. These are Binance fees for a regular user irrespective of being a market maker or taker. It is possible to lower those fees provided a high enough trading value; however, we want our findings to be relevant even from a small retail investor perspective. Slippage, while an important consideration in live trading, is rarely considered in research because of the complexities involved in modeling execution costs dynamically. Given that Binance provides deep liquidity for Bitcoin and Ethereum, slippage is expected to be minimal for the typical order sizes considered in systematic trading strategies. Furthermore, modeling slippage requires detailed order book simulations, which are beyond the scope of this study. For the Barrier method, which can generate multiple concurrent signals, we simplify by assuming only one open transaction at a time and investing the full portfolio value each time. To increase the likelihood of successful trades, we filter out predictions near 50%, taking a long position only if the probability of a price increase exceeds 60%, and a short position when it falls below 40%. This influential parameter was fixed prior to starting the experiment to prevent overfitting and to avoid presenting unrealistically optimistic results. This rule applies to all predictions, except those from Autoformer and FEDformer, which use the Triple Barrier method. As detailed in Section "[Novel methods](/article/10.1186/s40854-025-00866-w#Sec8)", these models do not yield probabilities because of the incompatibility of combining an encoder-decoder network with the Triple Barrier method.

Our evaluation employs the standard metrics listed below, which are reported for the test set. Together, they provide a holistic overview from the perspective of profitability, risk, and model accuracy.

Annual Net Profit/Loss (%) from the trading strategy

where *P**0* is the initial value of the portfolio and *P**N* is the final value of the portfolio expressed as

here *R**t* is the trading return on day *t*, and *C**entry* = *C**exit* is the transaction cost incurred whenever opening a new position or closing an existing position. *N* is the length of the trading period, which in our case was 456 days. The 365 days in the numerator reflect the 24/7 nature of the cryptocurrency market.

The share of profitable transactions (%), which is calculated on the basis of only the signals that were acted upon.

where Nprofit is the number of transactions that resulted in profit and Ntotal is the total number of transactions.

Accuracy of all the predictions.

where *TP* is the number of instances when the price appreciates and the model recommends "go long," *TN* is the number of instances when the price depreciates and the model recommends "go short," *FP* is the number of instances when the price depreciates and the model recommends "go long," and *FN* is the number of instances when the price appreciates and the model recommends "go short."

Annualized Sharpe ratio (Sharpe [1994](/article/10.1186/s40854-025-00866-w#ref-CR59 "Sharpe WF (1994) The sharpe ratio. J Portfolio Manag 21(1):49–58.
                  https://doi.org/10.3905/jpm.1994.409501

                "))

where *R*p is the return of the portfolio; *R*f is the risk-free rate, which we assume to be 3.14% on the basis of overnight rates from the U.S. Department of Treasury corresponding to the test period; and *σ**p* is the standard deviation of the portfolio’s return. Given the significant changes in interest rates during the testing period, we empirically determined that this average rate produces results nearly identical to those of a methodology that incorporates daily fluctuations in interest rates. Daily returns were used by computing returns at the end of each day irrespective of whether the position was opened.

Maximum drawdown, which represents the worst investment outcome from peak to trough

where *P*peak*,t* is the peak portfolio value up to time and *P**t* is the portfolio value at time *t.*

### Results

#### Comparison of transformer, conventional deep learning and machine learning models

We begin our analysis of the results by examining the accuracy and profitability of various algorithms on the full test set from the perspective of the target labeling method. Given that our experimental framework for each model encompasses five distinct data sampling methods, each with three varied values, and is applied to two cryptocurrencies, this equates to 30 unique experiments per model. To facilitate an orderly comparison, we initially present the distributions of the key metrics. Each point in the distribution corresponds to the average value of three experiments over the entire test set. We subsequently provide a detailed analysis of the best-performing model. As depicted in Fig. [11](/article/10.1186/s40854-025-00866-w#Fig11), the accuracy of all the models for the next-bar labeling oscillates at approximately 50%, indicating that no single model is the clear best performer. Notably, TSMixer, FEDformer, Transformer-Encoder and Attention-LSTM underperform compared with ResNet-LSTM, Autoformer, and XGBoost. Interestingly, the highest accuracy was achieved by the nondeep learning model XGBoost, which scored 54.94% for BTCUSDT 60 min and 54.53% for ETHUSDT 60 min. However, this does not correspond to a favorable trading outcome, as illustrated in the right panel of Fig. [11](/article/10.1186/s40854-025-00866-w#Fig11). The most significant annual net profit was realized by Autoformer for ETHUSDT 12 h (75.1%) and ETHUSDT CUSUM 3% (44.8%). Overall, the results from next-bar labeling are not particularly impressive, with only 29 out of 210 experiments showing a positive trading outcome. In our experimental setup, we aimed to ensure that these results were not statistically significant anomalies by incorporating a substantial out-of-sample period and averaging the results from three different runs.

![Fig. 11](//media.springernature.com/lw685/springer-static/image/art%3A10.1186%2Fs40854-025-00866-w/MediaObjects/40854_2025_866_Fig11_HTML.png)

Distribution of accuracy (left) and annual net profit/loss (%) (right) for next-bar labeling on the full test set. This figure aggregates all the experiments on all the types of bars for BTC and ETH for a given model

For the Triple Barrier labeling, the situation is clearer in terms of which model performs best, as illustrated in Fig. [12](/article/10.1186/s40854-025-00866-w#Fig12). ResNet-LSTM leads in terms of the mean, median, and third quartile accuracy, as well as in the highest annual return and its third quartile. Notably, this labeling method can yield higher profits in certain configurations than the next-bar labeling. However, the underperformance of the Transformer network merits further examination. We attribute the disappointing results of the Autoformer and FEDformer primarily to the challenges encountered in adapting the encoder-decoder architecture to the Triple Barrier method, as detailed in Section "[Novel methods](/article/10.1186/s40854-025-00866-w#Sec8)". In the absence of those challenges, as was the case for the Autoformer in next-bar labeling, the results were comparable to those of the other models. Further experimentation with the Triple Barrier method, Autoformer, and FEDformer explored transactions on the basis of the direction of maximum change rather than on the first breached barrier. This was based on the hypothesis that barriers set too close could be easily breached due to model errors. Unfortunately, this adjustment failed to improve performance. Our findings suggest that these models are not well suited for trading across the diverse configurations tested. Another Transformer model, the Transformer-Encoder, struggled with learning from the data, which was evidenced by a stagnating error rate during training. This is reflected in an accuracy hovering of approximately 50% and a lower variance in trading performance, given the model’s infrequent generation of trading signals. On the basis of cryptocurrency results, some criticism of Transformers applied to the time series domain seems warranted. As noted by critics, Transformers inherently lose temporal information due to parallel processing within their attention mechanism, which, ironically, also contributes to their success in other applications. Additionally, Transformers can struggle when presented with additional covariates, of which the number in our study was substantially greater than in typical benchmarking datasets.

![Fig. 12](//media.springernature.com/lw685/springer-static/image/art%3A10.1186%2Fs40854-025-00866-w/MediaObjects/40854_2025_866_Fig12_HTML.png)

Distribution of accuracy (left) and annual net profit/loss (right) for Triple Barrier labeling on the full test set. This figure aggregates all the experiments on all the types of bars for BTC and ETH for a given model

The Attention-LSTM model, despite its theoretical potential to capture temporal dependencies effectively through a combination of LSTM and an attention mechanism, also struggled significantly. This outcome, alongside the poor performance of XGBoost, highlights the critical importance of selecting appropriate incumbent methods. These results underscore the complexities involved in modeling financial time series and further support the effectiveness of CNN-LSTM architectures in extracting relevant spatial and temporal features.

#### Detailed results of the best-performing model

Given that ResNet-LSTM consistently shows good performance in both target labeling techniques, we present detailed results for it in Tables [2](/article/10.1186/s40854-025-00866-w#Tab2), [3](/article/10.1186/s40854-025-00866-w#Tab3), [4](/article/10.1186/s40854-025-00866-w#Tab4), [5](/article/10.1186/s40854-025-00866-w#Tab5). These results reveal an interesting pattern. Sampling according to a 2% CUSUM filter yielded positive results in all four configurations, whereas a 3% CUSUM filter resulted in three profitable experiments out of four. Range bars, a method similar to CUSUM, produced positive results in three and one configurations, respectively, but with lower returns. Other methods occasionally led to high returns, such as the 50 K volume bar for the ETHUSDT Triple Barrier and the daily bars for the BTCUSDT Triple Barrier. However, these methods lack consistency in the CUSUM filter. The dominant methods in academic discourse—systematic sampling and next-bar labeling—have yielded negative results in all experiments. Despite achieving high accuracy in certain instances—for example, BTCUSDT predictions for the next hour, which were traded with a 58.8% success rate—these did not lead to profitable outcomes due to transaction costs. This conclusion relates to the shortcomings of some of the studies discussed in Section "[Literature review](/article/10.1186/s40854-025-00866-w#Sec2)"; reporting good model fit or trading outcomes without transaction costs for high-frequency data can be misleading. Nevertheless, when combined with the Triple Barrier method, this sampling method demonstrated profitability, as evidenced by the BTCUSDT daily data. When detailed results across the target labeling methods are compared, it becomes clear that the Triple Barrier labeling yields much better results in absolute terms as well as on a risk-adjusted basis. Intriguingly, the least effective sampling method proved to be dollar bars, which led to highly negative outcomes across all configurations. The volume bars yielded positive results in only two configurations, and the range bars yielded positive results in five configurations, suggesting that sampling according to market movements is indeed the most effective method among those considered.

Overall, the results underscore the difficulty of trading two major cryptocurrencies, with most outcomes leaning toward negative profitability, even when leveraging state-of-the-art deep learning models. It is important to contextualize these findings against a buy-and-hold strategy, which, throughout the entire test period, would have resulted in losses of 34% for BTC and 44% for ETH. Our research highlights the significance of alternative data processing techniques in providing an edge to investors, emphasizing that the selection of an appropriate technique is crucial. Although information-driven bars such as dollar and volume bars appear promising in theory, they fail to produce positive outcomes. Moreover, the results for ETH were notably more positive than those for BTC, which might be attributed to BTC’s higher market efficiency and larger market capitalization. This suggests that the methods presented in our study could be more applicable to less popular cryptocurrencies, although they come with higher risks of a different nature. For the reasons outlined above, our further investigations will focus on the CUSUM, Triple Barrier, and ResNet-LSTM in the following section.

Additionally, Fig. [13](/article/10.1186/s40854-025-00866-w#Fig13) presents the equity curve of one of the experiments alongside the ETH closing price from April 2022 to June 2023. The results indicate that the strategy performs best during periods of heightened market volatility, particularly in mid-to-late 2022, capturing strong returns during both sharp declines and subsequent recoveries. The LUNA collapse in May 2022 triggered a significant sell-off, leading to extreme volatility, during which the strategy generated consistent gains. Similarly, the July–August 2022 recovery provided opportunities for continued profitability, suggesting that the strategy is not inherently biased toward bullish or bearish conditions but rather thrives in high-volatility environments. One plausible explanation for the strategy’s effectiveness during these episodes is the emergence of herding behavior, where traders mimic prevailing market sentiment in response to shocks, producing temporarily aligned and directional flows, which could be exploited by the algorithm. Such behavior has been shown to intensify during periods of economic policy uncertainty and structural market stress, as it overrides individual decision-making in favor of group dynamics (Bouri et al. [2019](/article/10.1186/s40854-025-00866-w#ref-CR8 "Bouri E, Gupta R, Roubaud D (2019) Herding behaviour in cryptocurrencies. Fin Res Lett 29:216–221.
                  https://doi.org/10.1016/j.frl.2018.07.008

                ")). However, a dip in performance occurs in November 2022, coinciding with the collapse of the FTX. This suggests that while the strategy capitalizes on volatility, it is still vulnerable to abrupt liquidity crises or extreme market dislocations. From early 2023 onward, as market conditions stabilized and volatility declined, performance growth slowed, indicating reduced effectiveness in more range-bound environments. Additional experiments confirm this overall pattern, although in some cases, the stagnation in 2023 is less pronounced, suggesting that parameter choices or execution variations may influence the results. Future research could explore whether explicit herding proxies, such as cross-sectional return dispersion or volume clustering, can be added to the feature set to improve the model’s adaptability across market regimes. These findings reinforce the critical role of volatility in driving strategy effectiveness and suggest further exploration into how external factors, such as macroeconomic announcements, impact performance. We also investigated whether the effectiveness of our strategy varies across different trading sessions by segmenting transactions into Asian, European, and U.S. trading hours. While there were slight variations—such as a greater proportion of positive trades during the Asian session—the differences were not statistically significant (χ2 = 0.40, *p* = 0.82). This suggests that our approach does not exhibit a clear preference for specific trading hours, reinforcing its adaptability across different market conditions rather than being dependent on region-specific trading activity.

![Fig. 13](//media.springernature.com/lw685/springer-static/image/art%3A10.1186%2Fs40854-025-00866-w/MediaObjects/40854_2025_866_Fig13_HTML.png)

Equity curve for ETH CUSUM 2% with triple barrier 5%

From our analysis, we conclude the following:

The CUSUM (information-driven bar) approach outperformed systematic time sampling.

Triple Barrier labeling was more effective than next-bar labeling.

Deep learning models outperform classical machine learning models in terms of the most critical metrics.

Contrary to our expectations, the performance of the Transformers did not surpass that of the incumbent method represented by ResNet-LSTM.

The strategy benefits significantly from market volatility

## Sensitivity analysis

### Dynamic triple barrier labeling

In this section, we investigate whether the poor performance of alternative sampling methods, as well as the strong performance of CUSUM sampling, can be influenced by applying a dynamic Triple Barrier approach. While fixed barrier values are intuitive for traders, they do not adapt to changing market conditions and may be suboptimal in volatile or low-volatility regimes. To address this, we conducted experiments where the barrier distances were dynamically adjusted on the basis of the exponentially weighted moving average of the standard deviation of the corresponding time series, following the methodology proposed by Lopez de Prado ([2018](/article/10.1186/s40854-025-00866-w#ref-CR16 "de Lopez Prado M (2018) Advances in financial machine learning. Wiley")).

Figure [14](/article/10.1186/s40854-025-00866-w#Fig14) illustrates the distribution of these volatility-adjusted barriers for two of the weakest-performing sampling methods—dollar and volume bars. Notably, the computed volatilities were often lower than our static barrier values, prompting us to evaluate two configurations: one where stop-loss and take-profit levels were set at one standard deviation from the entry price and another at two standard deviations. Despite its theoretical appeal, this adjustment did not improve trading outcomes. In fact, the results deteriorated for CUSUM sampling and failed to salvage the performance of the alternative sampling methods.

![Fig. 14](//media.springernature.com/lw685/springer-static/image/art%3A10.1186%2Fs40854-025-00866-w/MediaObjects/40854_2025_866_Fig14_HTML.png)

Distribution of volatility for Bitcoin (left) and Ethereum (right) for dollar and volume bars

These findings suggest that incorporating volatility directly into the training data, rather than embedding it into the labeling process, may be a more effective approach for model learning. The detailed results are presented in the Appendix for brevity. Future research could explore whether different volatility estimation techniques or alternative adaptive barrier formulations provide greater improvements, but our results indicate that volatility-aware sampling, such as the CUSUM filter, remains a superior approach.

### CUSUM and triple barrier sensitivity

In this section, we present a sensitivity analysis for the CUSUM filter with the Triple Barrier method for ETHUSDT. This configuration demonstrated robust performance for 2% and 3% sampling, paired with a symmetric Triple Barrier of 5%. Selecting these values poses a cold start problem, as we cannot depend on existing studies related to these methods. Consequently, it is reasonable to assume that these values were not the optimal parameters. In this section, we conduct a grid search of the CUSUM filter and the horizontal barriers of the Triple Barrier method.

The heatmaps, as illustrated in Figs. [15](/article/10.1186/s40854-025-00866-w#Fig15), [16](/article/10.1186/s40854-025-00866-w#Fig16), [17](/article/10.1186/s40854-025-00866-w#Fig17), indicate that our initial parameter estimates were close to optimal, as defined by the highest Sharpe ratio. The two highest Sharpe ratios achieved, 2.0 and 1.9, were observed for the CUSUM and Triple Barrier pairings of (2.5%, 5%), (2.5%, 6%), and (2%, 6%). High accuracy and profit are also achieved with the Triple Barrier method above 7% and for sampling between 1.5% and 2.5%. However, the Sharpe ratio indicates that the risk profile of these combinations is inferior to those mentioned earlier. Generally, a CUSUM filter set too high (above 3%) or too low (1%) proved to be suboptimal, and a similar pattern was noted for excessively low barrier values. In a few cases, in the upper left corner of the heatmaps, when the barrier values were lower than the CUSUM filter, the Triple Barrier method either collapsed or nearly collapsed to the next-bar labeling.

![Fig. 15](//media.springernature.com/lw685/springer-static/image/art%3A10.1186%2Fs40854-025-00866-w/MediaObjects/40854_2025_866_Fig15_HTML.png)

Sensitivity of accuracy to different CUSUM and Triple Barrier values for ETHUSDT and ResNet-LSTM

![Fig. 16](//media.springernature.com/lw685/springer-static/image/art%3A10.1186%2Fs40854-025-00866-w/MediaObjects/40854_2025_866_Fig16_HTML.png)

Sensitivity of annual net profit/loss to different CUSUM and Triple Barrier values for ETHUSDT and ResNet-LSTM

![Fig. 17](//media.springernature.com/lw685/springer-static/image/art%3A10.1186%2Fs40854-025-00866-w/MediaObjects/40854_2025_866_Fig17_HTML.png)

Sensitivity of the annualized Sharpe ratio to different CUSUM and Triple Barrier values for ETHUSDT and ResNet-LSTM

The consistency of many profitable experiments confirms that the positive results reported in the previous chapter were not mere coincidences. Employing the CUSUM filter in tandem with the Triple Barrier method has consistently led to profitable trading for ETHUSDT. Further sensitivity studies could explore the impact of dynamic horizontal barriers driven, for example, by recent market volatility and the impact of different values of the vertical barrier.

### Importance of feature engineering

In this section, we also assess the utility of the feature engineering module by comparing a subset of experiments with and without it presented in Table [6](/article/10.1186/s40854-025-00866-w#Tab6). For ETHUSDT, we observe a minor decrease in performance, which could be attributed to the inherent randomness associated with training deep learning models. However, for the BTCUSDT model, there is a clearly visible advantage in enriching the dataset with additional features, as the performance shifts from positive to negative.

On the basis of these findings, we conclude that our initial assumption regarding the inclusion of additional features was correct. As discussed in Section "[Feature engineering](/article/10.1186/s40854-025-00866-w#Sec17)", while it is a common practice, its utility has not been thoroughly examined. A detailed study of feature importance could offer further insights and lead to additional performance gains; however, such an investigation falls outside the scope of this research.

### Extensibility to other cryptocurrencies

Finally, we illustrate that the method we propose can be successfully extended to a wider range of cryptocurrencies, as exemplified by two well-known altcoins. Nevertheless, determining the optimal parameters for each is critical. This necessity arises from the fact that the volatility and extraordinary growth of many altcoins often eclipse those of ETH and BTC in the past few years, thereby necessitating specifically tailored parameters. For example, the optimal parameters for ETHUSDT are directly transferable to the Polygon (MATICUSDT). Conversely, Chainlink (LINKUSDT) demands significantly increased sampling and Triple Barrier thresholds to realize profitable outcomes, as shown in Table [7](/article/10.1186/s40854-025-00866-w#Tab7).

These findings reinforce the robustness of the method we introduced in our research. They indicate that the capacity to achieve profitable outcomes does not rely solely on the initial selection of cryptocurrencies, suggesting that our method has the potential to produce profitable signals across a broad spectrum of cryptocurrencies, provided that a thorough search for the most suitable parameters is undertaken.

## Discussion

Our results highlight the critical role of data sampling and target labeling methods in algorithmic trading. The CUSUM filter consistently outperforms other approaches, demonstrating that volatility-sensitive sampling provides a more accurate representation of market dynamics. In contrast, volume and dollar bars—despite their theoretical appeal—failed to improve trading outcomes. Their reliance on transaction activity makes them susceptible to distortions such as wash trading, which is inherently complex to correct for. Moreover, they do not inherently account for volatility, a critical factor in financial time series analysis. This suggests that activity-driven sampling alone is insufficient for predictive modeling. Notably, the dominant approach in financial research—systematic time-based sampling—lacks both volatility and activity awareness, further underscoring the advantages of information-driven methods.

The Triple Barrier method was significantly more effective than next-bar labeling, reinforcing the importance of structured entry and exit conditions. While next-bar prediction remains a widely used benchmark, it oversimplifies real trading dynamics and does not incorporate risk management. Our experiments with volatility-based target adjustments did not enhance performance, suggesting that models may be better suited to infer volatility patterns implicitly rather than having them explicitly imposed.

Our findings also contribute to the debate on deep learning for financial time series. Despite their dominance in other fields, Transformer-based models did not outperform the ResNet-LSTM architecture in our experiments, likely because of their loss of sequential dependencies. Similarly, classical machine learning techniques such as XGBoost did not offer meaningful predictive improvements, indicating that capturing intricate, noise-heavy time series requires architectures designed to handle sequential information effectively.

The difficulty of training consistently profitable models for BTC and ETH highlights the relative efficiency of these assets. Recent studies by Polyzos et al. ([2024](/article/10.1186/s40854-025-00866-w#ref-CR57 "Polyzos E, Rubbaniy G, Mazur M (2024) Efficient market hypothesis on the blockchain: a social-media-based index for cryptocurrency efficiency. Financ Rev 59(3):807–829.
                  https://doi.org/10.1111/fire.12387

                ")) have used a social-media-based efficiency index and shown that cryptocurrency market efficiency is time-varying and context dependent, often increasing during exogenous crises such as the COVID-19 pandemic and the Russia–Ukraine war, whereas it deteriorated during the 2018 crypto bust. Mokni et al. ([2024](/article/10.1186/s40854-025-00866-w#ref-CR49 "Mokni K, El Montasser G, Ajmi AN, Bouri E (2024) On the efficiency and its drivers in the cryptocurrency market: the case of Bitcoin and Ethereum. Financ Innov 10(1):39.
                  https://doi.org/10.1186/s40854-023-00566-3

                ")) provide further insight by quantifying inefficiency in BTC and ETH with the Adjusted Market Inefficiency Magnitude (AMIM), revealing that efficiency is significantly influenced by liquidity, volatility, global financial stress, and the COVID-19 pandemic. Notably, they find BTC to be more efficient than ETH, consistent with our observation that profitable strategies are more difficult to develop for BTC. Complementing these results, Aslam et al. ([2023](/article/10.1186/s40854-025-00866-w#ref-CR5 "Aslam F, Memon BA, Hunjra AI, Bouri E (2023) The dynamics of market efficiency of major cryptocurrencies. Glob Financ J 58:100899.
                  https://doi.org/10.1016/j.gfj.2023.100899

                ")) employ a multifractal detrended fluctuation analysis and report that cryptocurrency markets exhibit persistent multifractality, with BTC displaying the highest degree and therefore the lowest efficiency among the assets analyzed. Their use of a dynamic Hurst exponent confirms that efficiency degrades during market crises. While these studies differ in methodology and some conclusions, they converge in challenging the notion of persistent informational efficiency in crypto markets. Collectively, they support the presence of exploitable patterns and underscore the need for context-aware approaches to market modeling—findings that align with our results.

While our approach generalizes beyond these two cryptocurrencies, future research should examine its applicability to a broader range of cryptocurrencies, including lower-liquidity markets where inefficiencies may be more exploitable, as well as classical markets such as equities, forex, and commodities. Our equity curve analysis further confirms the importance of volatility for trading success—our strategy performed well during periods of market turbulence but struggled in more stable conditions. This suggests that future refinements could incorporate adaptive mechanisms such as volatility-targeting position sizing, regime-switching models, or dynamic leverage adjustments to optimize risk exposure in varying market environments.

Additionally, while our study did not directly analyze macroeconomic drivers, a growing body of research indicates that such events do influence cryptocurrency dynamics. Karau ([2023](/article/10.1186/s40854-025-00866-w#ref-CR36 "Karau S (2023) Monetary policy and Bitcoin. J Int Money Financ 137:102880.
                  https://doi.org/10.1016/j.jimonfin.2023.102880

                ")) shows that Bitcoin volatility increases significantly around FOMC announcements, especially post-COVID-19, reflecting heightened sensitivity to monetary policy news. Kyriazis et al. ([2023](/article/10.1186/s40854-025-00866-w#ref-CR41 "Kyriazis A, Ofeidis I, Palaiokrassas G, and Tassiulas L (2023) Monetary policy, digital assets, and DeFi activity.
                  https://doi.org/10.48550/arXiv.2302.10252

                ")) find that unexpected changes in the federal funds rate lead to significant negative returns for BTC and ETH, with volatility responses comparable to those observed for the NASDAQ. Benigno and Rosa ([2023](/article/10.1186/s40854-025-00866-w#ref-CR6 "Benigno G, Rosa C (2023) The Bitcoin-macro disconnect (Working Paper No. 1052). Staff Reports.
                  https://www.econstor.eu/handle/10419/272865

                ")) find that Bitcoin is largely orthogonal to most macroeconomic surprises but reacts significantly to U.S. CPI releases. They also detect a weak response to the forward-guidance component of monetary policy, whereas the current-rate surprises have no measurable effect. Lin et al. ([2025](/article/10.1186/s40854-025-00866-w#ref-CR46 "Lin M, Liu Y, Sheng VNK (2025) Analysis of the impact of macroeconomic factors on cryptocurrency returns—based on quantile regression study. Int Rev Econ Finance 97:103757.
                  https://doi.org/10.1016/j.iref.2024.103757

                ")) show, in a quantile-regression framework covering 2018–2024, that the USD exchange rate, PPI, and 10-year Treasury yields have asymmetric, tail-dependent effects on Bitcoin returns, with the impact intensifying under extreme market conditions. Therefore, future research could examine how incorporating macroeconomic signals into the modeling framework we propose may improve predictive performance and risk control.

Overall, our study demonstrates that thoughtful data preprocessing choices can significantly impact trading performance. To expand on this foundation, future research should explore dynamic threshold selection, alternative labeling methods, and cross-asset validation to further refine these methodologies and assess their robustness across different market conditions.

## Conclusions

This study critically evaluates alternative data sampling and target labeling methods for algorithmic trading strategies in Bitcoin and Ethereum. By comparing information-driven bars—including dollar and volume bars, the CUSUM filter, and range bars—with traditional time bars and contrasting the Triple Barrier method with conventional next-bar prediction, we aimed to identify approaches that better capture market dynamics.

Our results demonstrate that systematic time sampling inadequately reflects the nuances of the volatile and increasingly efficient cryptocurrency market. The CUSUM filter outperforms other sampling techniques by more accurately representing true market movements, thereby enhancing the predictive capabilities of trading models. Equally important, the Triple Barrier method, which was previously unexplored in the academic literature, has been shown to be superior to next-bar prediction. By incorporating realistic trading scenarios with profit-taking, stop-loss, and time-based exits, the Triple Barrier method significantly improves model accuracy and profitability. When combined with the CUSUM filter, it consistently yielded profitable trades, whereas other methods often resulted in losses.

These findings have practical and policy implications. For traders and quantitative asset managers they offer a concrete framework for achieving a competitive advantage by employing advanced data curation techniques that more accurately capture true market dynamics, moving beyond the limitations of time-based sampling. For policymakers, however, our results reveal potential market vulnerabilities. First, the dependence of certain analytical methods on trading volume underscores the risk posed by practices such as wash trading, which can distort price discovery and mislead algorithmic models. This highlights the need for regulatory measures to ensure data integrity through standardized reporting requirements and enhanced market surveillance. Second, the strategy’s potential to profit from herding behavior raises additional concerns. The widespread adoption of similar algorithmic approaches could create self-reinforcing feedback loops, exacerbating price swings and amplifying market volatility, thus increasing systemic risk. These insights emphasize the importance of proactive monitoring and careful consideration of algorithm-driven dynamics in the design of regulatory frameworks.

Additionally, these findings have significant implications for the understanding of market efficiency in cryptocurrency markets. The ability to achieve higher profits via the CUSUM filter and Triple Barrier method suggests that standard time-based sampling and conventional target labeling may overestimate market efficiency by failing to capture exploitable patterns. Our results indicate that cryptocurrency markets may be less efficient than previously thought when analyzed with more sophisticated methods. Consequently, researchers aiming to test market efficiency should consider adopting advanced sampling and labeling techniques, as they provide a more accurate assessment of true market dynamics.

Our analysis also highlights the critical role of parameter selection. The optimal configurations for the CUSUM filter and Triple Barrier method are essential; well-chosen parameters can mean the difference between profit and loss. Our strategy achieved appealing risk-adjusted returns, with a Sharpe ratio of 2 even amid high risk-free rates. Sensitivity analyses confirmed the robustness of our findings, and while our method is applicable to other cryptocurrencies, parameter optimization remains crucial.

In exploring deep learning architectures for complex time series classification, we found that the state-of-the-art Transformer and MLP models did not outperform the established ResNet-LSTM architecture in the cryptocurrency trading context. ResNet-LSTM consistently delivered strong performance across cryptocurrencies and sampling methods, reinforcing its reliability. While Transformers hold promise in time series applications, our findings suggest a cautious approach and highlight the need for further research. Moreover, we confirm that deep learning models outperform classical machine learning methods in this domain.

Our study has certain limitations that open avenues for future research**.** Our analysis was confined to Bitcoin and Ethereum; although we demonstrated extensibility to two additional altcoins, the findings may not fully generalize to the broader cryptoasset universe, particularly less liquid markets that exhibit distinct volatility patterns and risk profiles. A natural direction for future research is to extend this framework to traditional asset classes such as equities, commodities, and forex markets, where different microstructural characteristics and regulatory environments may affect model performance. The study parameters for the CUSUM filter and Triple Barrier method were kept static. Future work could explore dynamic parameter optimization, allowing these thresholds to adapt in real time to changing market volatility and regimes, which could enhance strategy robustness. Furthermore, while our model implicitly captures market dynamics through advanced sampling and labeling, it does not explicitly incorporate external data sources. Integrating macroeconomic indicators, on-chain metrics, or sentiment signals derived from social media and news flows could enhance predictive power and improve robustness, particularly around major economic releases or market-moving events.

In conclusion, our research provides compelling evidence that adopting information-driven sampling via the CUSUM filter and employing the Triple Barrier method for labeling significantly enhances algorithmic trading performance in cryptocurrency markets. These methods offer practical benefits for traders and investors seeking a competitive advantage.

## Availability of data and materials

The datasets analysed during the current study are available at the: <https://data.binance.vision/>.

## Abbreviations

Bitcoin

Ethereum

Bitcoin pair with Tether

Ethereum pair with Tether

Polygon pair with Tether

Chainlink pair with Tether

Open, high, low, close price data

Efficient market hypothesis

Machine learning

Deep learning

Convolutional neural network

Residual neural network

Long short-term memory

Time series mixer

Rectified linear unit

Gaussian error linear unit

## References

Aliber RZ, Kindleberger CP, McCauley RN (2023) Bitcoin: worse than a ponzi. In: Aliber RZ, Kindleberger CP, McCauley RN (eds) Manias, panics, and crashes: a history of financial crises. Springer, Berlin, pp 349–371. <https://doi.org/10.1007/978-3-031-16008-0_14>

[Chapter](https://link.springer.com/doi/10.1007/978-3-031-16008-0_14) 
[Google Scholar](http://scholar.google.com/scholar_lookup?&title=Bitcoin%3A%20worse%20than%20a%20ponzi&doi=10.1007%2F978-3-031-16008-0_14&pages=349-371&publication_year=2023&author=Aliber%2CRZ&author=Kindleberger%2CCP&author=McCauley%2CRN)

Alonso-Monsalve S, Suárez-Cetrulo AL, Cervantes A, Quintana D (2020) Convolution on neural networks for high-frequency trend prediction of cryptocurrency exchange rates using technical indicators. Expert Syst Appl 149:113250. <https://doi.org/10.1016/j.eswa.2020.113250>

[Article](https://doi.org/10.1016%2Fj.eswa.2020.113250) 
[Google Scholar](http://scholar.google.com/scholar_lookup?&title=Convolution%20on%20neural%20networks%20for%20high-frequency%20trend%20prediction%20of%20cryptocurrency%20exchange%20rates%20using%20technical%20indicators&journal=Expert%20Syst%20Appl&doi=10.1016%2Fj.eswa.2020.113250&volume=149&publication_year=2020&author=Alonso-Monsalve%2CS&author=Su%C3%A1rez-Cetrulo%2CAL&author=Cervantes%2CA&author=Quintana%2CD)

Altan A, Karasu S, Bekiros S (2019) Digital currency forecasting with chaotic meta-heuristic bio-inspired signal processing techniques. Chaos Solitons Fractals 126:325–336. <https://doi.org/10.1016/j.chaos.2019.07.011>

[Article](https://doi.org/10.1016%2Fj.chaos.2019.07.011) 
[Google Scholar](http://scholar.google.com/scholar_lookup?&title=Digital%20currency%20forecasting%20with%20chaotic%20meta-heuristic%20bio-inspired%20signal%20processing%20techniques&journal=Chaos%20Solitons%20Fractals&doi=10.1016%2Fj.chaos.2019.07.011&volume=126&pages=325-336&publication_year=2019&author=Altan%2CA&author=Karasu%2CS&author=Bekiros%2CS)

Amirzadeh R, Nazari A, Thiruvady D (2022) Applying artificial intelligence in cryptocurrency markets: a survey. Algorithms 15(11):11. <https://doi.org/10.3390/a15110428>

[Article](https://doi.org/10.3390%2Fa15110428) 
[Google Scholar](http://scholar.google.com/scholar_lookup?&title=Applying%20artificial%20intelligence%20in%20cryptocurrency%20markets%3A%20a%20survey&journal=Algorithms&doi=10.3390%2Fa15110428&volume=15&issue=11&publication_year=2022&author=Amirzadeh%2CR&author=Nazari%2CA&author=Thiruvady%2CD)

Aslam F, Memon BA, Hunjra AI, Bouri E (2023) The dynamics of market efficiency of major cryptocurrencies. Glob Financ J 58:100899. <https://doi.org/10.1016/j.gfj.2023.100899>

[Article](https://doi.org/10.1016%2Fj.gfj.2023.100899) 
[Google Scholar](http://scholar.google.com/scholar_lookup?&title=The%20dynamics%20of%20market%20efficiency%20of%20major%20cryptocurrencies&journal=Glob%20Financ%20J&doi=10.1016%2Fj.gfj.2023.100899&volume=58&publication_year=2023&author=Aslam%2CF&author=Memon%2CBA&author=Hunjra%2CAI&author=Bouri%2CE)

Benigno G, Rosa C (2023) The Bitcoin-macro disconnect (Working Paper No. 1052). Staff Reports. <https://www.econstor.eu/handle/10419/272865>

Borges TA, Neves RF (2020) Ensemble of machine learning algorithms for cryptocurrency investment with different data resampling methods. Appl Soft Comput 90:106187. <https://doi.org/10.1016/j.asoc.2020.106187>

[Article](https://doi.org/10.1016%2Fj.asoc.2020.106187) 
[Google Scholar](http://scholar.google.com/scholar_lookup?&title=Ensemble%20of%20machine%20learning%20algorithms%20for%20cryptocurrency%20investment%20with%20different%20data%20resampling%20methods&journal=Appl%20Soft%20Comput&doi=10.1016%2Fj.asoc.2020.106187&volume=90&publication_year=2020&author=Borges%2CTA&author=Neves%2CRF)

Bouri E, Gupta R, Roubaud D (2019) Herding behaviour in cryptocurrencies. Fin Res Lett 29:216–221. <https://doi.org/10.1016/j.frl.2018.07.008>

[Article](https://doi.org/10.1016%2Fj.frl.2018.07.008) 
[Google Scholar](http://scholar.google.com/scholar_lookup?&title=Herding%20behaviour%20in%20cryptocurrencies&journal=Fin%20Res%20Lett&doi=10.1016%2Fj.frl.2018.07.008&volume=29&pages=216-221&publication_year=2019&author=Bouri%2CE&author=Gupta%2CR&author=Roubaud%2CD)

Bouteska A, Abedin MZ, Hajek P, Yuan K (2024) Cryptocurrency price forecasting: a comparative analysis of ensemble learning and deep learning methods. Int Rev Financ Anal 92:103055. <https://doi.org/10.1016/j.irfa.2023.103055>

[Article](https://doi.org/10.1016%2Fj.irfa.2023.103055) 
[Google Scholar](http://scholar.google.com/scholar_lookup?&title=Cryptocurrency%20price%20forecasting%3A%20a%20comparative%20analysis%20of%20ensemble%20learning%20and%20deep%20learning%20methods&journal=Int%20Rev%20Financ%20Anal&doi=10.1016%2Fj.irfa.2023.103055&volume=92&publication_year=2024&author=Bouteska%2CA&author=Abedin%2CMZ&author=Hajek%2CP&author=Yuan%2CK)

Chen T, Guestrin C (2016) XGBoost: a scalable tree boosting system. In: Proceedings of the 22nd ACM SIGKDD international conference on knowledge discovery and data mining. 785–794. <https://doi.org/10.1145/2939672.2939785>

Chen SA, Li CL, Yoder N, Arik SO, Pfister T (2023) TSMixer: an all-MLP architecture for time series forecasting. <https://doi.org/10.48550/arXiv.2303.06053>

Chen S, Ge L (2019) Exploring the attention mechanism in LSTM-based Hong Kong stock price movement prediction. Quant Finance 19(9):1507–1515. <https://doi.org/10.1080/14697688.2019.1622287>

[Article](https://doi.org/10.1080%2F14697688.2019.1622287) 
[Google Scholar](http://scholar.google.com/scholar_lookup?&title=Exploring%20the%20attention%20mechanism%20in%20LSTM-based%20Hong%20Kong%20stock%20price%20movement%20prediction&journal=Quant%20Finance&doi=10.1080%2F14697688.2019.1622287&volume=19&issue=9&pages=1507-1515&publication_year=2019&author=Chen%2CS&author=Ge%2CL)

Chen S, He H (2018) Stock prediction using convolutional neural network. IOP Conf Ser Mater Sci Eng 435(1):012026. <https://doi.org/10.1088/1757-899X/435/1/012026>

[Article](https://doi.org/10.1088%2F1757-899X%2F435%2F1%2F012026) 
[Google Scholar](http://scholar.google.com/scholar_lookup?&title=Stock%20prediction%20using%20convolutional%20neural%20network&journal=IOP%20Conf%20Ser%20Mater%20Sci%20Eng&doi=10.1088%2F1757-899X%2F435%2F1%2F012026&volume=435&issue=1&publication_year=2018&author=Chen%2CS&author=He%2CH)

Cont R (2007) Volatility clustering in financial markets: empirical facts and agent-based models. In: Teyssière G, Kirman AP (eds) Long memory in economics. Springer, Berlin, pp 289–309. <https://doi.org/10.1007/978-3-540-34625-8_10>

[Chapter](https://link.springer.com/doi/10.1007/978-3-540-34625-8_10) 
[Google Scholar](http://scholar.google.com/scholar_lookup?&title=Volatility%20clustering%20in%20financial%20markets%3A%20empirical%20facts%20and%20agent-based%20models&doi=10.1007%2F978-3-540-34625-8_10&pages=289-309&publication_year=2007&author=Cont%2CR)

Crépellière T, Pelster M, Zeisberger S (2023) Arbitrage in the market for cryptocurrencies. J Financ Mark 64:100817. <https://doi.org/10.1016/j.finmar.2023.100817>

[Article](https://doi.org/10.1016%2Fj.finmar.2023.100817) 
[Google Scholar](http://scholar.google.com/scholar_lookup?&title=Arbitrage%20in%20the%20market%20for%20cryptocurrencies&journal=J%20Financ%20Mark&doi=10.1016%2Fj.finmar.2023.100817&volume=64&publication_year=2023&author=Cr%C3%A9pelli%C3%A8re%2CT&author=Pelster%2CM&author=Zeisberger%2CS)

de Lopez Prado M (2018) Advances in financial machine learning. Wiley

[Google Scholar](http://scholar.google.com/scholar_lookup?&title=Advances%20in%20financial%20machine%20learning&publication_year=2018&author=Lopez%20Prado%2CM)

Fama EF (1970) Efficient capital markets: a review of theory and empirical work. J Finance 25(2):383–417

[Article](https://doi.org/10.2307%2F2325486) 
[Google Scholar](http://scholar.google.com/scholar_lookup?&title=Efficient%20capital%20markets%3A%20a%20review%20of%20theory%20and%20empirical%20work&journal=J%20Finance&doi=10.2307%2F2325486&volume=25&issue=2&pages=383-417&publication_year=1970&author=Fama%2CEF)

Fang F, Ventre C, Basios M, Kanthan L, Martinez-Rego D, Wu F, Li L (2022) Cryptocurrency trading: a comprehensive survey. Financ Innov 8(1):13. <https://doi.org/10.1186/s40854-021-00321-6>

[Article](https://link.springer.com/doi/10.1186/s40854-021-00321-6) 
[Google Scholar](http://scholar.google.com/scholar_lookup?&title=Cryptocurrency%20trading%3A%20a%20comprehensive%20survey&journal=Financ%20Innov&doi=10.1186%2Fs40854-021-00321-6&volume=8&issue=1&publication_year=2022&author=Fang%2CF&author=Ventre%2CC&author=Basios%2CM&author=Kanthan%2CL&author=Martinez-Rego%2CD&author=Wu%2CF&author=Li%2CL)

Fratrič P, Sileno G, Klous S, van Engers T (2022) Manipulation of the Bitcoin market: an agent-based study. Financ Innov 8(1):60. <https://doi.org/10.1186/s40854-022-00364-3>

[Article](https://link.springer.com/doi/10.1186/s40854-022-00364-3) 
[Google Scholar](http://scholar.google.com/scholar_lookup?&title=Manipulation%20of%20the%20Bitcoin%20market%3A%20an%20agent-based%20study&journal=Financ%20Innov&doi=10.1186%2Fs40854-022-00364-3&volume=8&issue=1&publication_year=2022&author=Fratri%C4%8D%2CP&author=Sileno%2CG&author=Klous%2CS&author=Engers%2CT)

Gerritsen DF, Bouri E, Ramezanifar E, Roubaud D (2020) The profitability of technical trading rules in the Bitcoin market. Financ Res Lett 34:101263. <https://doi.org/10.1016/j.frl.2019.08.011>

[Article](https://doi.org/10.1016%2Fj.frl.2019.08.011) 
[Google Scholar](http://scholar.google.com/scholar_lookup?&title=The%20profitability%20of%20technical%20trading%20rules%20in%20the%20Bitcoin%20market&journal=Financ%20Res%20Lett&doi=10.1016%2Fj.frl.2019.08.011&volume=34&publication_year=2020&author=Gerritsen%2CDF&author=Bouri%2CE&author=Ramezanifar%2CE&author=Roubaud%2CD)

Giudici G, Milne A, Vinogradov D (2020) Cryptocurrencies: market analysis and perspectives. J Ind Bus Econ 47(1):1–18. <https://doi.org/10.1007/s40812-019-00138-6>

[Article](https://link.springer.com/doi/10.1007/s40812-019-00138-6) 
[Google Scholar](http://scholar.google.com/scholar_lookup?&title=Cryptocurrencies%3A%20market%20analysis%20and%20perspectives&journal=J%20Ind%20Bus%20Econ&doi=10.1007%2Fs40812-019-00138-6&volume=47&issue=1&pages=1-18&publication_year=2020&author=Giudici%2CG&author=Milne%2CA&author=Vinogradov%2CD)

Gradojevic N, Kukolj D, Adcock R, Djakovic V (2023) Forecasting Bitcoin with technical analysis: a not-so-random forest? Int J Forecast 39(1):1–17. <https://doi.org/10.1016/j.ijforecast.2021.08.001>

[Article](https://doi.org/10.1016%2Fj.ijforecast.2021.08.001) 
[Google Scholar](http://scholar.google.com/scholar_lookup?&title=Forecasting%20Bitcoin%20with%20technical%20analysis%3A%20a%20not-so-random%20forest%3F&journal=Int%20J%20Forecast&doi=10.1016%2Fj.ijforecast.2021.08.001&volume=39&issue=1&pages=1-17&publication_year=2023&author=Gradojevic%2CN&author=Kukolj%2CD&author=Adcock%2CR&author=Djakovic%2CV)

Grądzki P, Wójcik P (2023) Is attention all you need for intraday Forex trading? Expert Syst n/a(n/a):e13317. <https://doi.org/10.1111/exsy.13317>

[Article](https://doi.org/10.1111%2Fexsy.13317) 
[Google Scholar](http://scholar.google.com/scholar_lookup?&title=Is%20attention%20all%20you%20need%20for%20intraday%20Forex%20trading%3F&journal=Expert%20Syst&doi=10.1111%2Fexsy.13317&volume=n%2Fa&issue=n%2Fa&publication_year=2023&author=Gr%C4%85dzki%2CP&author=W%C3%B3jcik%2CP)

Gudelek MU, Boluk SA, Ozbayoglu AM (2017) A deep learning based stock trading model with 2-D CNN trend detection. <https://ieeexplore.ieee.org/document/8285188>

Gurgul V, Lessmann S, Härdle WK (2025) Deep learning and NLP in cryptocurrency forecasting: integrating financial, blockchain, and social media data. Int J Forecast 41(4):1666–1695. <https://doi.org/10.1016/j.ijforecast.2025.02.007>

[Article](https://doi.org/10.1016%2Fj.ijforecast.2025.02.007) 
[Google Scholar](http://scholar.google.com/scholar_lookup?&title=Deep%20learning%20and%20NLP%20in%20cryptocurrency%20forecasting%3A%20integrating%20financial%2C%20blockchain%2C%20and%20social%20media%20data&journal=Int%20J%20Forecast&doi=10.1016%2Fj.ijforecast.2025.02.007&volume=41&issue=4&pages=1666-1695&publication_year=2025&author=Gurgul%2CV&author=Lessmann%2CS&author=H%C3%A4rdle%2CWK)

He K, Zhang X, Ren S, Sun J (2016) Deep residual learning for image recognition. IEEE Conf Comput vis Pattern Recogn 2016:770–778. <https://doi.org/10.1109/CVPR.2016.90>

[Article](https://doi.org/10.1109%2FCVPR.2016.90) 
[Google Scholar](http://scholar.google.com/scholar_lookup?&title=Deep%20residual%20learning%20for%20image%20recognition&journal=IEEE%20Conf%20Comput%20vis%20Pattern%20Recogn&doi=10.1109%2FCVPR.2016.90&volume=2016&pages=770-778&publication_year=2016&author=He%2CK&author=Zhang%2CX&author=Ren%2CS&author=Sun%2CJ)

Hochreiter S, Schmidhuber J (1997) Long short-term memory. Neural Comput 9(8):1735–1780. <https://doi.org/10.1162/neco.1997.9.8.1735>

[Article](https://doi.org/10.1162%2Fneco.1997.9.8.1735) 
[Google Scholar](http://scholar.google.com/scholar_lookup?&title=Long%20short-term%20memory&journal=Neural%20Comput&doi=10.1162%2Fneco.1997.9.8.1735&volume=9&issue=8&pages=1735-1780&publication_year=1997&author=Hochreiter%2CS&author=Schmidhuber%2CJ)

Hollis T, Viscardi A, Yi SE (2018) A comparison of LSTMs and attention mechanisms for forecasting financial time series. <https://doi.org/10.48550/arXiv.1812.07699>

Hu Z, Zhao Y, Khushi M (2021) A survey of Forex and stock price prediction using deep learning. Appl Syst Innov 4(1):1. <https://doi.org/10.3390/asi4010009>

[Article](https://doi.org/10.3390%2Fasi4010009) 
[Google Scholar](http://scholar.google.com/scholar_lookup?&title=A%20survey%20of%20Forex%20and%20stock%20price%20prediction%20using%20deep%20learning&journal=Appl%20Syst%20Innov&doi=10.3390%2Fasi4010009&volume=4&issue=1&publication_year=2021&author=Hu%2CZ&author=Zhao%2CY&author=Khushi%2CM)

Huggingface (2023) Yes, transformers are effective for time series forecasting (+ Autoformer). <https://huggingface.co/blog/autoformer>

Ibrahim A, Kashef R, Corrigan L (2021) Predicting market movement direction for bitcoin: a comparison of time series modeling methods. Comput Electr Eng 89:106905. <https://doi.org/10.1016/j.compeleceng.2020.106905>

[Article](https://doi.org/10.1016%2Fj.compeleceng.2020.106905) 
[Google Scholar](http://scholar.google.com/scholar_lookup?&title=Predicting%20market%20movement%20direction%20for%20bitcoin%3A%20a%20comparison%20of%20time%20series%20modeling%20methods&journal=Comput%20Electr%20Eng&doi=10.1016%2Fj.compeleceng.2020.106905&volume=89&publication_year=2021&author=Ibrahim%2CA&author=Kashef%2CR&author=Corrigan%2CL)

Ismail Fawaz H, Forestier G, Weber J, Idoumghar L, Muller P-A (2019) Deep learning for time series classification: a review. Data Min Knowl Discov 33(4):917–963. <https://doi.org/10.1007/s10618-019-00619-1>

[Article](https://link.springer.com/doi/10.1007/s10618-019-00619-1) 
[Google Scholar](http://scholar.google.com/scholar_lookup?&title=Deep%20learning%20for%20time%20series%20classification%3A%20a%20review&journal=Data%20Min%20Knowl%20Discov&doi=10.1007%2Fs10618-019-00619-1&volume=33&issue=4&pages=917-963&publication_year=2019&author=Ismail%20Fawaz%2CH&author=Forestier%2CG&author=Weber%2CJ&author=Idoumghar%2CL&author=Muller%2CP-A)

Jiang W (2021) Applications of deep learning in stock market prediction: recent progress. Expert Syst Appl 184:115537. <https://doi.org/10.1016/j.eswa.2021.115537>

[Article](https://doi.org/10.1016%2Fj.eswa.2021.115537) 
[Google Scholar](http://scholar.google.com/scholar_lookup?&title=Applications%20of%20deep%20learning%20in%20stock%20market%20prediction%3A%20recent%20progress&journal=Expert%20Syst%20Appl&doi=10.1016%2Fj.eswa.2021.115537&volume=184&publication_year=2021&author=Jiang%2CW)

Jirou I, Jebabli I, Lahiani A (2025) A hybrid deep learning model for cryptocurrency returns forecasting: comparison of the performance of financial markets and impact of external variables. Res Int Bus Financ 73:102575. <https://doi.org/10.1016/j.ribaf.2024.102575>

[Article](https://doi.org/10.1016%2Fj.ribaf.2024.102575) 
[Google Scholar](http://scholar.google.com/scholar_lookup?&title=A%20hybrid%20deep%20learning%20model%20for%20cryptocurrency%20returns%20forecasting%3A%20comparison%20of%20the%20performance%20of%20financial%20markets%20and%20impact%20of%20external%20variables&journal=Res%20Int%20Bus%20Financ&doi=10.1016%2Fj.ribaf.2024.102575&volume=73&publication_year=2025&author=Jirou%2CI&author=Jebabli%2CI&author=Lahiani%2CA)

Kakinaka S, Umeno K (2022) Cryptocurrency market efficiency in short- and long-term horizons during COVID-19: an asymmetric multifractal analysis approach. Fin Res Lett 46:102319. <https://doi.org/10.1016/j.frl.2021.102319>

[Article](https://doi.org/10.1016%2Fj.frl.2021.102319) 
[Google Scholar](http://scholar.google.com/scholar_lookup?&title=Cryptocurrency%20market%20efficiency%20in%20short-%20and%20long-term%20horizons%20during%20COVID-19%3A%20an%20asymmetric%20multifractal%20analysis%20approach&journal=Fin%20Res%20Lett&doi=10.1016%2Fj.frl.2021.102319&volume=46&publication_year=2022&author=Kakinaka%2CS&author=Umeno%2CK)

Karau S (2023) Monetary policy and Bitcoin. J Int Money Financ 137:102880. <https://doi.org/10.1016/j.jimonfin.2023.102880>

[Article](https://doi.org/10.1016%2Fj.jimonfin.2023.102880) 
[Google Scholar](http://scholar.google.com/scholar_lookup?&title=Monetary%20policy%20and%20Bitcoin&journal=J%20Int%20Money%20Financ&doi=10.1016%2Fj.jimonfin.2023.102880&volume=137&publication_year=2023&author=Karau%2CS)

Khedr AM, Arif I, P V PR, El-Bannany M, Alhashmi SM, Sreedharan M (2021) Cryptocurrency price prediction using traditional statistical and machine-learning techniques: a survey. Intell Syst Account Financ Manag 28(1):3–34. <https://doi.org/10.1002/isaf.1488>

[Article](https://doi.org/10.1002%2Fisaf.1488) 
[Google Scholar](http://scholar.google.com/scholar_lookup?&title=Cryptocurrency%20price%20prediction%20using%20traditional%20statistical%20and%20machine-learning%20techniques%3A%20a%20survey&journal=Intell%20Syst%20Account%20Financ%20Manag&doi=10.1002%2Fisaf.1488&volume=28&issue=1&pages=3-34&publication_year=2021&author=Khedr%2CAM&author=Arif%2CI&author=P%20V%2CPR&author=El-Bannany%2CM&author=Alhashmi%2CSM&author=Sreedharan%2CM)

Kim G, Shin D-H, Choi JG, Lim S (2022) A deep learning-based cryptocurrency price prediction model that uses on-chain data. IEEE Access 10:56232–56248. <https://doi.org/10.1109/ACCESS.2022.3177888>

[Article](https://doi.org/10.1109%2FACCESS.2022.3177888) 
[Google Scholar](http://scholar.google.com/scholar_lookup?&title=A%20deep%20learning-based%20cryptocurrency%20price%20prediction%20model%20that%20uses%20on-chain%20data&journal=IEEE%20Access&doi=10.1109%2FACCESS.2022.3177888&volume=10&pages=56232-56248&publication_year=2022&author=Kim%2CG&author=Shin%2CD-H&author=Choi%2CJG&author=Lim%2CS)

Kim S, Kang M (2019) Financial series prediction using attention LSTM. <https://doi.org/10.48550/arXiv.1902.10877>

Kristoufek L, Bouri E (2023) Exploring sources of statistical arbitrage opportunities among Bitcoin exchanges. Fin Res Lett 51:103332. <https://doi.org/10.1016/j.frl.2022.103332>

[Article](https://doi.org/10.1016%2Fj.frl.2022.103332) 
[Google Scholar](http://scholar.google.com/scholar_lookup?&title=Exploring%20sources%20of%20statistical%20arbitrage%20opportunities%20among%20Bitcoin%20exchanges&journal=Fin%20Res%20Lett&doi=10.1016%2Fj.frl.2022.103332&volume=51&publication_year=2023&author=Kristoufek%2CL&author=Bouri%2CE)

Kyriazis A, Ofeidis I, Palaiokrassas G, and Tassiulas L (2023) Monetary policy, digital assets, and DeFi activity. <https://doi.org/10.48550/arXiv.2302.10252>

Lee M-C (2024) Bitcoin trend prediction with attention-based deep learning models and technical indicators. Systems. <https://doi.org/10.3390/systems12110498>

[Article](https://doi.org/10.3390%2Fsystems12110498) 
[Google Scholar](http://scholar.google.com/scholar_lookup?&title=Bitcoin%20trend%20prediction%20with%20attention-based%20deep%20learning%20models%20and%20technical%20indicators&journal=Systems&doi=10.3390%2Fsystems12110498&publication_year=2024&author=Lee%2CM-C)

Li Z, Tam V (2017) A comparative study of a recurrent neural network and support vector machine for predicting price movements of stocks of different volatilites. IEEE Symp Ser Comput Intell 2017:1–8. <https://doi.org/10.1109/SSCI.2017.8285319>

[Article](https://doi.org/10.1109%2FSSCI.2017.8285319) 
[Google Scholar](http://scholar.google.com/scholar_lookup?&title=A%20comparative%20study%20of%20a%20recurrent%20neural%20network%20and%20support%20vector%20machine%20for%20predicting%20price%20movements%20of%20stocks%20of%20different%20volatilites&journal=IEEE%20Symp%20Ser%20Comput%20Intell&doi=10.1109%2FSSCI.2017.8285319&volume=2017&pages=1-8&publication_year=2017&author=Li%2CZ&author=Tam%2CV)

Li L, Jamieson K, DeSalvo G, Rostamizadeh A, Talwalkar A (2017) Hyperband: a novel bandit-based approach to hyperparameter optimization. J Mach Learn Res 18(1):6765–6816

[Google Scholar](http://scholar.google.com/scholar_lookup?&title=Hyperband%3A%20a%20novel%20bandit-based%20approach%20to%20hyperparameter%20optimization&journal=J%20Mach%20Learn%20Res&volume=18&issue=1&pages=6765-6816&publication_year=2017&author=Li%2CL&author=Jamieson%2CK&author=DeSalvo%2CG&author=Rostamizadeh%2CA&author=Talwalkar%2CA)

Lim B, Arık SÖ, Loeff N, Pfister T (2021) Temporal fusion transformers for interpretable multi-horizon time series forecasting. Int J Forecast 37(4):1748–1764. <https://doi.org/10.1016/j.ijforecast.2021.03.012>

[Article](https://doi.org/10.1016%2Fj.ijforecast.2021.03.012) 
[Google Scholar](http://scholar.google.com/scholar_lookup?&title=Temporal%20fusion%20transformers%20for%20interpretable%20multi-horizon%20time%20series%20forecasting&journal=Int%20J%20Forecast&doi=10.1016%2Fj.ijforecast.2021.03.012&volume=37&issue=4&pages=1748-1764&publication_year=2021&author=Lim%2CB&author=Ar%C4%B1k%2CS%C3%96&author=Loeff%2CN&author=Pfister%2CT)

Lin M, Liu Y, Sheng VNK (2025) Analysis of the impact of macroeconomic factors on cryptocurrency returns—based on quantile regression study. Int Rev Econ Finance 97:103757. <https://doi.org/10.1016/j.iref.2024.103757>

[Article](https://doi.org/10.1016%2Fj.iref.2024.103757) 
[Google Scholar](http://scholar.google.com/scholar_lookup?&title=Analysis%20of%20the%20impact%20of%20macroeconomic%20factors%20on%20cryptocurrency%20returns%E2%80%94based%20on%20quantile%20regression%20study&journal=Int%20Rev%20Econ%20Finance&doi=10.1016%2Fj.iref.2024.103757&volume=97&publication_year=2025&author=Lin%2CM&author=Liu%2CY&author=Sheng%2CVNK)

Luo Y, Alvarez M, Wang S, Jussa J, Wang A, and Rohal G (2014) Seven sins of quantitative investing. Deutsche Bank Markets Research, White paper

Ma A (2022) Profitability of technical trading strategies under market manipulation. Financ Innov 8(1):5. <https://doi.org/10.1186/s40854-021-00304-7>

[Article](https://link.springer.com/doi/10.1186/s40854-021-00304-7) 
[Google Scholar](http://scholar.google.com/scholar_lookup?&title=Profitability%20of%20technical%20trading%20strategies%20under%20market%20manipulation&journal=Financ%20Innov&doi=10.1186%2Fs40854-021-00304-7&volume=8&issue=1&publication_year=2022&author=Ma%2CA)

Mokni K, El Montasser G, Ajmi AN, Bouri E (2024) On the efficiency and its drivers in the cryptocurrency market: the case of Bitcoin and Ethereum. Financ Innov 10(1):39. <https://doi.org/10.1186/s40854-023-00566-3>

[Article](https://link.springer.com/doi/10.1186/s40854-023-00566-3) 
[Google Scholar](http://scholar.google.com/scholar_lookup?&title=On%20the%20efficiency%20and%20its%20drivers%20in%20the%20cryptocurrency%20market%3A%20the%20case%20of%20Bitcoin%20and%20Ethereum&journal=Financ%20Innov&doi=10.1186%2Fs40854-023-00566-3&volume=10&issue=1&publication_year=2024&author=Mokni%2CK&author=Montasser%2CG&author=Ajmi%2CAN&author=Bouri%2CE)

Murray K, Rossi A, Carraro D, Visentin A (2023) On forecasting cryptocurrency prices: a comparison of machine learning, deep learning, and ensembles. Forecasting. <https://doi.org/10.3390/forecast5010010>

[Article](https://doi.org/10.3390%2Fforecast5010010) 
[Google Scholar](http://scholar.google.com/scholar_lookup?&title=On%20forecasting%20cryptocurrency%20prices%3A%20a%20comparison%20of%20machine%20learning%2C%20deep%20learning%2C%20and%20ensembles&journal=Forecasting&doi=10.3390%2Fforecast5010010&publication_year=2023&author=Murray%2CK&author=Rossi%2CA&author=Carraro%2CD&author=Visentin%2CA)

Nakamoto S (2008) Bitcoin: a peer-to-peer electronic cash system. <https://bitcoin.org/bitcoin.pdf>

Oyedele AA, Ajayi AO, Oyedele LO, Bello SA, Jimoh KO (2023) Performance evaluation of deep learning and boosted trees for cryptocurrency closing price prediction. Expert Syst Appl 213:119233. <https://doi.org/10.1016/j.eswa.2022.119233>

[Article](https://doi.org/10.1016%2Fj.eswa.2022.119233) 
[Google Scholar](http://scholar.google.com/scholar_lookup?&title=Performance%20evaluation%20of%20deep%20learning%20and%20boosted%20trees%20for%20cryptocurrency%20closing%20price%20prediction&journal=Expert%20Syst%20Appl&doi=10.1016%2Fj.eswa.2022.119233&volume=213&publication_year=2023&author=Oyedele%2CAA&author=Ajayi%2CAO&author=Oyedele%2CLO&author=Bello%2CSA&author=Jimoh%2CKO)

Pardeshi K, Gill SS, Abdelmoniem AM (2024) Stock market price prediction: a hybrid LSTM and sequential self-attention based approach. pp. 122–140. <https://doi.org/10.1201/9781003467199-11>

Parvini N, Abdollahi M, Seifollahi S, Ahmadian D (2022) Forecasting Bitcoin returns with long short-term memory networks and wavelet decomposition: a comparison of several market determinants. Appl Soft Comput 121:108707. <https://doi.org/10.1016/j.asoc.2022.108707>

[Article](https://doi.org/10.1016%2Fj.asoc.2022.108707) 
[Google Scholar](http://scholar.google.com/scholar_lookup?&title=Forecasting%20Bitcoin%20returns%20with%20long%20short-term%20memory%20networks%20and%20wavelet%20decomposition%3A%20a%20comparison%20of%20several%20market%20determinants&journal=Appl%20Soft%20Comput&doi=10.1016%2Fj.asoc.2022.108707&volume=121&publication_year=2022&author=Parvini%2CN&author=Abdollahi%2CM&author=Seifollahi%2CS&author=Ahmadian%2CD)

Peng P, Chen Y, Lin W, Wang JZ (2024) Attention-based CNN–LSTM for high-frequency multiple cryptocurrency trend prediction. Expert Syst Appl 237:121520. <https://doi.org/10.1016/j.eswa.2023.121520>

[Article](https://doi.org/10.1016%2Fj.eswa.2023.121520) 
[Google Scholar](http://scholar.google.com/scholar_lookup?&title=Attention-based%20CNN%E2%80%93LSTM%20for%20high-frequency%20multiple%20cryptocurrency%20trend%20prediction&journal=Expert%20Syst%20Appl&doi=10.1016%2Fj.eswa.2023.121520&volume=237&publication_year=2024&author=Peng%2CP&author=Chen%2CY&author=Lin%2CW&author=Wang%2CJZ)

Pennec GL, Fiedler I, Ante L (2021) Wash trading at cryptocurrency exchanges. Fin Res Lett 43:101982. <https://doi.org/10.1016/j.frl.2021.101982>

[Article](https://doi.org/10.1016%2Fj.frl.2021.101982) 
[Google Scholar](http://scholar.google.com/scholar_lookup?&title=Wash%20trading%20at%20cryptocurrency%20exchanges&journal=Fin%20Res%20Lett&doi=10.1016%2Fj.frl.2021.101982&volume=43&publication_year=2021&author=Pennec%2CGL&author=Fiedler%2CI&author=Ante%2CL)

Polyzos E, Rubbaniy G, Mazur M (2024) Efficient market hypothesis on the blockchain: a social-media-based index for cryptocurrency efficiency. Financ Rev 59(3):807–829. <https://doi.org/10.1111/fire.12387>

[Article](https://doi.org/10.1111%2Ffire.12387) 
[Google Scholar](http://scholar.google.com/scholar_lookup?&title=Efficient%20market%20hypothesis%20on%20the%20blockchain%3A%20a%20social-media-based%20index%20for%20cryptocurrency%20efficiency&journal=Financ%20Rev&doi=10.1111%2Ffire.12387&volume=59&issue=3&pages=807-829&publication_year=2024&author=Polyzos%2CE&author=Rubbaniy%2CG&author=Mazur%2CM)

Sezer OB, Ozbayoglu AM (2018) Algorithmic financial trading with deep convolutional neural networks: time series to image conversion approach. Appl Soft Comput 70:525–538. <https://doi.org/10.1016/j.asoc.2018.04.024>

[Article](https://doi.org/10.1016%2Fj.asoc.2018.04.024) 
[Google Scholar](http://scholar.google.com/scholar_lookup?&title=Algorithmic%20financial%20trading%20with%20deep%20convolutional%20neural%20networks%3A%20time%20series%20to%20image%20conversion%20approach&journal=Appl%20Soft%20Comput&doi=10.1016%2Fj.asoc.2018.04.024&volume=70&pages=525-538&publication_year=2018&author=Sezer%2COB&author=Ozbayoglu%2CAM)

Sharpe WF (1994) The sharpe ratio. J Portfolio Manag 21(1):49–58. <https://doi.org/10.3905/jpm.1994.409501>

[Article](https://doi.org/10.3905%2Fjpm.1994.409501) 
[Google Scholar](http://scholar.google.com/scholar_lookup?&title=The%20sharpe%20ratio&journal=J%20Portfolio%20Manag&doi=10.3905%2Fjpm.1994.409501&volume=21&issue=1&pages=49-58&publication_year=1994&author=Sharpe%2CWF)

Shu A, Cheng F, Han J, Liang Z, Pan Z (2023) Arbitrage across different Bitcoin exchange venues: perspectives from investor base and market related events. Account Financ 63(5):5183–5210. <https://doi.org/10.1111/acfi.13102>

[Article](https://doi.org/10.1111%2Facfi.13102) 
[Google Scholar](http://scholar.google.com/scholar_lookup?&title=Arbitrage%20across%20different%20Bitcoin%20exchange%20venues%3A%20perspectives%20from%20investor%20base%20and%20market%20related%20events&journal=Account%20Financ&doi=10.1111%2Facfi.13102&volume=63&issue=5&pages=5183-5210&publication_year=2023&author=Shu%2CA&author=Cheng%2CF&author=Han%2CJ&author=Liang%2CZ&author=Pan%2CZ)

Shwartz-Ziv R, Armon A (2021) Tabular data: deep learning is not all you need. <https://doi.org/10.48550/arXiv.2106.03253>

Song H, Choi H (2023) Forecasting stock market indices using the recurrent neural network based hybrid models: CNN-LSTM, GRU-CNN, and ensemble models. Appl Sci. <https://doi.org/10.3390/app13074644>

[Article](https://doi.org/10.3390%2Fapp13074644) 
[Google Scholar](http://scholar.google.com/scholar_lookup?&title=Forecasting%20stock%20market%20indices%20using%20the%20recurrent%20neural%20network%20based%20hybrid%20models%3A%20CNN-LSTM%2C%20GRU-CNN%2C%20and%20ensemble%20models&journal=Appl%20Sci&doi=10.3390%2Fapp13074644&publication_year=2023&author=Song%2CH&author=Choi%2CH)

Sun X, Liu M, Sima Z (2020) A novel cryptocurrency price trend forecasting model based on LightGBM. Fin Res Lett 32:101084. <https://doi.org/10.1016/j.frl.2018.12.032>

[Article](https://doi.org/10.1016%2Fj.frl.2018.12.032) 
[Google Scholar](http://scholar.google.com/scholar_lookup?&title=A%20novel%20cryptocurrency%20price%20trend%20forecasting%20model%20based%20on%20LightGBM&journal=Fin%20Res%20Lett&doi=10.1016%2Fj.frl.2018.12.032&volume=32&publication_year=2020&author=Sun%2CX&author=Liu%2CM&author=Sima%2CZ)

Thakkar A, Chaudhari K (2021) A comprehensive survey on deep neural networks for stock market: The need, challenges, and future directions. Expert Syst Appl 177:114800. <https://doi.org/10.1016/j.eswa.2021.114800>

[Article](https://doi.org/10.1016%2Fj.eswa.2021.114800) 
[Google Scholar](http://scholar.google.com/scholar_lookup?&title=A%20comprehensive%20survey%20on%20deep%20neural%20networks%20for%20stock%20market%3A%20The%20need%2C%20challenges%2C%20and%20future%20directions&journal=Expert%20Syst%20Appl&doi=10.1016%2Fj.eswa.2021.114800&volume=177&publication_year=2021&author=Thakkar%2CA&author=Chaudhari%2CK)

Tolstikhin I, Houlsby N, Kolesnikov A, Beyer L, Zhai X, Unterthiner T, Yung J, Steiner A, Keysers D, Uszkoreit J, Lucic M, and Dosovitskiy A, (2021). MLP-mixer: an all-MLP architecture for vision. <https://doi.org/10.48550/arXiv.2105.01601>

Tsantekidis A, Passalis N, Tefas A, Kanniainen J, Gabbouj M, Iosifidis A (2020) Using deep learning for price prediction by exploiting stationary limit order book features. Appl Soft Comput 93:106401. <https://doi.org/10.1016/j.asoc.2020.106401>

[Article](https://doi.org/10.1016%2Fj.asoc.2020.106401) 
[Google Scholar](http://scholar.google.com/scholar_lookup?&title=Using%20deep%20learning%20for%20price%20prediction%20by%20exploiting%20stationary%20limit%20order%20book%20features&journal=Appl%20Soft%20Comput&doi=10.1016%2Fj.asoc.2020.106401&volume=93&publication_year=2020&author=Tsantekidis%2CA&author=Passalis%2CN&author=Tefas%2CA&author=Kanniainen%2CJ&author=Gabbouj%2CM&author=Iosifidis%2CA)

Vaswani A, Shazeer N, Parmar N, Uszkoreit J, Jones L, Gomez AN, Kaiser Ł, Polosukhin I (2017) Attention is all you need. Advances in neural information processing systems. 30. <https://proceedings.neurips.cc/paper_files/paper/2017/hash/3f5ee243547dee91fbd053c1c4a845aa-Abstract.html>

Vergara G, Kristjanpoller W (2024) Deep reinforcement learning applied to statistical arbitrage investment strategy on cryptomarket. Appl Soft Comput 153:111255. <https://doi.org/10.1016/j.asoc.2024.111255>

[Article](https://doi.org/10.1016%2Fj.asoc.2024.111255) 
[Google Scholar](http://scholar.google.com/scholar_lookup?&title=Deep%20reinforcement%20learning%20applied%20to%20statistical%20arbitrage%20investment%20strategy%20on%20cryptomarket&journal=Appl%20Soft%20Comput&doi=10.1016%2Fj.asoc.2024.111255&volume=153&publication_year=2024&author=Vergara%2CG&author=Kristjanpoller%2CW)

Wang J, Sun T, Liu B, Cao Y, Wang D (2018) Financial markets prediction with deep learning. In: 2018 17th IEEE international conference on machine learning and applications (ICMLA), 97–104. <https://doi.org/10.1109/ICMLA.2018.00022>

Wu H, Xu J, Wang J, Long M (2022) Autoformer: decomposition transformers with auto-correlation for long-term series forecasting. <https://doi.org/10.48550/arXiv.2106.13008>

Zeng A, Chen M, Zhang L, Xu Q (2022) Are transformers effective for time series forecasting? <https://doi.org/10.48550/arXiv.2205.13504>

Zhang Z, Dai H-N, Zhou J, Mondal SK, García MM, Wang H (2021) Forecasting cryptocurrency price using convolutional neural networks with weighted and attentive memory channels. Expert Syst Appl 183:115378. <https://doi.org/10.1016/j.eswa.2021.115378>

[Article](https://doi.org/10.1016%2Fj.eswa.2021.115378) 
[Google Scholar](http://scholar.google.com/scholar_lookup?&title=Forecasting%20cryptocurrency%20price%20using%20convolutional%20neural%20networks%20with%20weighted%20and%20attentive%20memory%20channels&journal=Expert%20Syst%20Appl&doi=10.1016%2Fj.eswa.2021.115378&volume=183&publication_year=2021&author=Zhang%2CZ&author=Dai%2CH-N&author=Zhou%2CJ&author=Mondal%2CSK&author=Garc%C3%ADa%2CMM&author=Wang%2CH)

Zhang J, Cai K, Wen J (2024) A survey of deep learning applications in cryptocurrency. iScience 27(1):108509. <https://doi.org/10.1016/j.isci.2023.108509>

[Article](https://doi.org/10.1016%2Fj.isci.2023.108509) 
[Google Scholar](http://scholar.google.com/scholar_lookup?&title=A%20survey%20of%20deep%20learning%20applications%20in%20cryptocurrency&journal=iScience&doi=10.1016%2Fj.isci.2023.108509&volume=27&issue=1&publication_year=2024&author=Zhang%2CJ&author=Cai%2CK&author=Wen%2CJ)

Zhou H, Zhang S, Peng J, Zhang S, Li J, Xiong H, Zhang W (2021) Informer: beyond efficient transformer for long sequence time-series forecasting. <https://doi.org/10.48550/arXiv.2012.07436>

Zhou T, Ma Z, Wen Q, Wang X, Sun L, Jin R (2022) FEDformer: frequency enhanced decomposed transformer for long-term series forecasting. <https://doi.org/10.48550/arXiv.2201.12740>

Zoumpekas T, Houstis E, Vavalis M (2020) ETH analysis and predictions utilizing deep learning. Expert Syst Appl 162:113866. <https://doi.org/10.1016/j.eswa.2020.113866>

[Article](https://doi.org/10.1016%2Fj.eswa.2020.113866) 
[Google Scholar](http://scholar.google.com/scholar_lookup?&title=ETH%20analysis%20and%20predictions%20utilizing%20deep%20learning&journal=Expert%20Syst%20Appl&doi=10.1016%2Fj.eswa.2020.113866&volume=162&publication_year=2020&author=Zoumpekas%2CT&author=Houstis%2CE&author=Vavalis%2CM)

[Download references](https://citation-needed.springer.com/v2/references/10.1186/s40854-025-00866-w?format=refman&flavour=references)

## Acknowledgements

Not applicable.

## Funding

Research carried out thanks to the support of the University of Warsaw under 'New Ideas 3B' competition in POB III implemented under the 'Excellence Initiative—Research University' Programme.

## Author information

### Authors and Affiliations

Department of Data Science, Faculty of Economic Sciences, University of Warsaw, Ul. Dluga 44/50, 00-241, Warsaw, Poland

Przemysław Grądzki & Piotr Wójcik

School of Business and Economics, Humboldt-Universität zu Berlin, Unter den Linden 6, 10099, Berlin, Germany

Stefan Lessmann

Bucharest University of Economic Studies, Piata Romana, No. 8, Bucharest, Romania

Stefan Lessmann

Search author on:[PubMed](https://www.ncbi.nlm.nih.gov/entrez/query.fcgi?cmd=search&term=Przemys%C5%82aw%20Gr%C4%85dzki) [Google Scholar](https://scholar.google.co.uk/scholar?as_q=&num=10&btnG=Search+Scholar&as_epq=&as_oq=&as_eq=&as_occt=any&as_sauthors=%22Przemys%C5%82aw%20Gr%C4%85dzki%22&as_publication=&as_ylo=&as_yhi=&as_allsubj=all&hl=en)

Search author on:[PubMed](https://www.ncbi.nlm.nih.gov/entrez/query.fcgi?cmd=search&term=Piotr%20W%C3%B3jcik) [Google Scholar](https://scholar.google.co.uk/scholar?as_q=&num=10&btnG=Search+Scholar&as_epq=&as_oq=&as_eq=&as_occt=any&as_sauthors=%22Piotr%20W%C3%B3jcik%22&as_publication=&as_ylo=&as_yhi=&as_allsubj=all&hl=en)

Search author on:[PubMed](https://www.ncbi.nlm.nih.gov/entrez/query.fcgi?cmd=search&term=Stefan%20Lessmann) [Google Scholar](https://scholar.google.co.uk/scholar?as_q=&num=10&btnG=Search+Scholar&as_epq=&as_oq=&as_eq=&as_occt=any&as_sauthors=%22Stefan%20Lessmann%22&as_publication=&as_ylo=&as_yhi=&as_allsubj=all&hl=en)

### Contributions

PG: Project proposal, data curation, model development and coding, writing—original draft. PW: Project proposal, project management, writing—review and editing. SL: Writing—review and editing. All authors read and approved the final manuscript.

### Corresponding author

Correspondence to
[Przemysław Grądzki](mailto:p.gradzki@uw.edu.pl).

## Ethics declarations

### Ethics approval and consent to participate

Not applicable.

### Consent for publication

Not applicable.

### Competing interests

The authors declare that they have no competing interests.

## Additional information

### Publisher's Note

Springer Nature remains neutral with regard to jurisdictional claims in published maps and institutional affiliations.

## Supplementary Information

### [Additional file 1. (download DOCX )](https://static-content.springer.com/esm/art%3A10.1186%2Fs40854-025-00866-w/MediaObjects/40854_2025_866_MOESM1_ESM.docx)

## Rights and permissions

**Open Access** This article is licensed under a Creative Commons Attribution 4.0 International License, which permits use, sharing, adaptation, distribution and reproduction in any medium or format, as long as you give appropriate credit to the original author(s) and the source, provide a link to the Creative Commons licence, and indicate if changes were made. The images or other third party material in this article are included in the article's Creative Commons licence, unless indicated otherwise in a credit line to the material. If material is not included in the article's Creative Commons licence and your intended use is not permitted by statutory regulation or exceeds the permitted use, you will need to obtain permission directly from the copyright holder. To view a copy of this licence, visit <http://creativecommons.org/licenses/by/4.0/>.

[Reprints and permissions](https://s100.copyright.com/AppDispatchServlet?title=Algorithmic%20crypto%20trading%20using%20information-driven%20bars%2C%20triple%20barrier%20labeling%20and%20deep%20learning&author=Przemys%C5%82aw%20Gr%C4%85dzki%20et%20al&contentID=10.1186%2Fs40854-025-00866-w&copyright=The%20Author%28s%29&publication=2199-4730&publicationDate=2025-12-15&publisherName=SpringerNature&orderBeanReset=true&oa=CC%20BY)

## About this article

![Check for updates. Verify currency and authenticity via CrossMark](data:image/svg+xml;base64,PHN2ZyBoZWlnaHQ9IjgxIiB3aWR0aD0iNTciIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGcgZmlsbD0ibm9uZSIgZmlsbC1ydWxlPSJldmVub2RkIj48cGF0aCBkPSJtMTcuMzUgMzUuNDUgMjEuMy0xNC4ydi0xNy4wM2gtMjEuMyIgZmlsbD0iIzk4OTg5OCIvPjxwYXRoIGQ9Im0zOC42NSAzNS40NS0yMS4zLTE0LjJ2LTE3LjAzaDIxLjMiIGZpbGw9IiM3NDc0NzQiLz48cGF0aCBkPSJtMjggLjVjLTEyLjk4IDAtMjMuNSAxMC41Mi0yMy41IDIzLjVzMTAuNTIgMjMuNSAyMy41IDIzLjUgMjMuNS0xMC41MiAyMy41LTIzLjVjMC02LjIzLTIuNDgtMTIuMjEtNi44OC0xNi42Mi00LjQxLTQuNC0xMC4zOS02Ljg4LTE2LjYyLTYuODh6bTAgNDEuMjVjLTkuOCAwLTE3Ljc1LTcuOTUtMTcuNzUtMTcuNzVzNy45NS0xNy43NSAxNy43NS0xNy43NSAxNy43NSA3Ljk1IDE3Ljc1IDE3Ljc1YzAgNC43MS0xLjg3IDkuMjItNS4yIDEyLjU1cy03Ljg0IDUuMi0xMi41NSA1LjJ6IiBmaWxsPSIjNTM1MzUzIi8+PHBhdGggZD0ibTQxIDM2Yy01LjgxIDYuMjMtMTUuMjMgNy40NS0yMi40MyAyLjktNy4yMS00LjU1LTEwLjE2LTEzLjU3LTcuMDMtMjEuNWwtNC45Mi0zLjExYy00Ljk1IDEwLjctMS4xOSAyMy40MiA4Ljc4IDI5LjcxIDkuOTcgNi4zIDIzLjA3IDQuMjIgMzAuNi00Ljg2eiIgZmlsbD0iIzljOWM5YyIvPjxwYXRoIGQ9Im0uMiA1OC40NWMwLS43NS4xMS0xLjQyLjMzLTIuMDFzLjUyLTEuMDkuOTEtMS41Yy4zOC0uNDEuODMtLjczIDEuMzQtLjk0LjUxLS4yMiAxLjA2LS4zMiAxLjY1LS4zMi41NiAwIDEuMDYuMTEgMS41MS4zNS40NC4yMy44MS41IDEuMS44MWwtLjkxIDEuMDFjLS4yNC0uMjQtLjQ5LS40Mi0uNzUtLjU2LS4yNy0uMTMtLjU4LS4yLS45My0uMi0uMzkgMC0uNzMuMDgtMS4wNS4yMy0uMzEuMTYtLjU4LjM3LS44MS42Ni0uMjMuMjgtLjQxLjYzLS41MyAxLjA0LS4xMy40MS0uMTkuODgtLjE5IDEuMzkgMCAxLjA0LjIzIDEuODYuNjggMi40Ni40NS41OSAxLjA2Ljg4IDEuODQuODguNDEgMCAuNzctLjA3IDEuMDctLjIzcy41OS0uMzkuODUtLjY4bC45MSAxYy0uMzguNDMtLjguNzYtMS4yOC45OS0uNDcuMjItMSAuMzQtMS41OC4zNC0uNTkgMC0xLjEzLS4xLTEuNjQtLjMxLS41LS4yLS45NC0uNTEtMS4zMS0uOTEtLjM4LS40LS42Ny0uOS0uODgtMS40OC0uMjItLjU5LS4zMy0xLjI2LS4zMy0yLjAyem04LjQtNS4zM2gxLjYxdjIuNTRsLS4wNSAxLjMzYy4yOS0uMjcuNjEtLjUxLjk2LS43MnMuNzYtLjMxIDEuMjQtLjMxYy43MyAwIDEuMjcuMjMgMS42MS43MS4zMy40Ny41IDEuMTQuNSAyLjAydjQuMzFoLTEuNjF2LTQuMWMwLS41Ny0uMDgtLjk3LS4yNS0xLjIxLS4xNy0uMjMtLjQ1LS4zNS0uODMtLjM1LS4zIDAtLjU2LjA4LS43OS4yMi0uMjMuMTUtLjQ5LjM2LS43OC42NHY0LjhoLTEuNjF6bTcuMzcgNi40NWMwLS41Ni4wOS0xLjA2LjI2LTEuNTEuMTgtLjQ1LjQyLS44My43MS0xLjE0LjI5LS4zLjYzLS41NCAxLjAxLS43MS4zOS0uMTcuNzgtLjI1IDEuMTgtLjI1LjQ3IDAgLjg4LjA4IDEuMjMuMjQuMzYuMTYuNjUuMzguODkuNjdzLjQyLjYzLjU0IDEuMDNjLjEyLjQxLjE4Ljg0LjE4IDEuMzIgMCAuMzItLjAyLjU3LS4wNy43NmgtNC4zNmMuMDcuNjIuMjkgMS4xLjY1IDEuNDQuMzYuMzMuODIuNSAxLjM4LjUuMjkgMCAuNTctLjA0LjgzLS4xM3MuNTEtLjIxLjc2LS4zN2wuNTUgMS4wMWMtLjMzLjIxLS42OS4zOS0xLjA5LjUzLS40MS4xNC0uODMuMjEtMS4yNi4yMS0uNDggMC0uOTItLjA4LTEuMzQtLjI1LS40MS0uMTYtLjc2LS40LTEuMDctLjctLjMxLS4zMS0uNTUtLjY5LS43Mi0xLjEzLS4xOC0uNDQtLjI2LS45NS0uMjYtMS41MnptNC42LS42MmMwLS41NS0uMTEtLjk4LS4zNC0xLjI4LS4yMy0uMzEtLjU4LS40Ny0xLjA2LS40Ny0uNDEgMC0uNzcuMTUtMS4wNy40NS0uMzEuMjktLjUuNzMtLjU4IDEuM3ptMi41LjYyYzAtLjU3LjA5LTEuMDguMjgtMS41My4xOC0uNDQuNDMtLjgyLjc1LTEuMTNzLjY5LS41NCAxLjEtLjcxYy40Mi0uMTYuODUtLjI0IDEuMzEtLjI0LjQ1IDAgLjg0LjA4IDEuMTcuMjNzLjYxLjM0Ljg1LjU3bC0uNzcgMS4wMmMtLjE5LS4xNi0uMzgtLjI4LS41Ni0uMzctLjE5LS4wOS0uMzktLjE0LS42MS0uMTQtLjU2IDAtMS4wMS4yMS0xLjM1LjYzLS4zNS40MS0uNTIuOTctLjUyIDEuNjcgMCAuNjkuMTcgMS4yNC41MSAxLjY2LjM0LjQxLjc4LjYyIDEuMzIuNjIuMjggMCAuNTQtLjA2Ljc4LS4xNy4yNC0uMTIuNDUtLjI2LjY0LS40MmwuNjcgMS4wM2MtLjMzLjI5LS42OS41MS0xLjA4LjY1LS4zOS4xNS0uNzguMjMtMS4xOC4yMy0uNDYgMC0uOS0uMDgtMS4zMS0uMjQtLjQtLjE2LS43NS0uMzktMS4wNS0uN3MtLjUzLS42OS0uNy0xLjEzYy0uMTctLjQ1LS4yNS0uOTYtLjI1LTEuNTN6bTYuOTEtNi40NWgxLjU4djYuMTdoLjA1bDIuNTQtMy4xNmgxLjc3bC0yLjM1IDIuOCAyLjU5IDQuMDdoLTEuNzVsLTEuNzctMi45OC0xLjA4IDEuMjN2MS43NWgtMS41OHptMTMuNjkgMS4yN2MtLjI1LS4xMS0uNS0uMTctLjc1LS4xNy0uNTggMC0uODcuMzktLjg3IDEuMTZ2Ljc1aDEuMzR2MS4yN2gtMS4zNHY1LjZoLTEuNjF2LTUuNmgtLjkydi0xLjJsLjkyLS4wN3YtLjcyYzAtLjM1LjA0LS42OC4xMy0uOTguMDgtLjMxLjIxLS41Ny40LS43OXMuNDItLjM5LjcxLS41MWMuMjgtLjEyLjYzLS4xOCAxLjA0LS4xOC4yNCAwIC40OC4wMi42OS4wNy4yMi4wNS40MS4xLjU3LjE3em0uNDggNS4xOGMwLS41Ny4wOS0xLjA4LjI3LTEuNTMuMTctLjQ0LjQxLS44Mi43Mi0xLjEzLjMtLjMxLjY1LS41NCAxLjA0LS43MS4zOS0uMTYuOC0uMjQgMS4yMy0uMjRzLjg0LjA4IDEuMjQuMjRjLjQuMTcuNzQuNCAxLjA0Ljcxcy41NC42OS43MiAxLjEzYy4xOS40NS4yOC45Ni4yOCAxLjUzcy0uMDkgMS4wOC0uMjggMS41M2MtLjE4LjQ0LS40Mi44Mi0uNzIgMS4xM3MtLjY0LjU0LTEuMDQuNy0uODEuMjQtMS4yNC4yNC0uODQtLjA4LTEuMjMtLjI0LS43NC0uMzktMS4wNC0uN2MtLjMxLS4zMS0uNTUtLjY5LS43Mi0xLjEzLS4xOC0uNDUtLjI3LS45Ni0uMjctMS41M3ptMS42NSAwYzAgLjY5LjE0IDEuMjQuNDMgMS42Ni4yOC40MS42OC42MiAxLjE4LjYyLjUxIDAgLjktLjIxIDEuMTktLjYyLjI5LS40Mi40NC0uOTcuNDQtMS42NiAwLS43LS4xNS0xLjI2LS40NC0xLjY3LS4yOS0uNDItLjY4LS42My0xLjE5LS42My0uNSAwLS45LjIxLTEuMTguNjMtLjI5LjQxLS40My45Ny0uNDMgMS42N3ptNi40OC0zLjQ0aDEuMzNsLjEyIDEuMjFoLjA1Yy4yNC0uNDQuNTQtLjc5Ljg4LTEuMDIuMzUtLjI0LjctLjM2IDEuMDctLjM2LjMyIDAgLjU5LjA1Ljc4LjE0bC0uMjggMS40LS4zMy0uMDljLS4xMS0uMDEtLjIzLS4wMi0uMzgtLjAyLS4yNyAwLS41Ni4xLS44Ni4zMXMtLjU1LjU4LS43NyAxLjF2NC4yaC0xLjYxem0tNDcuODcgMTVoMS42MXY0LjFjMCAuNTcuMDguOTcuMjUgMS4yLjE3LjI0LjQ0LjM1LjgxLjM1LjMgMCAuNTctLjA3LjgtLjIyLjIyLS4xNS40Ny0uMzkuNzMtLjczdi00LjdoMS42MXY2Ljg3aC0xLjMybC0uMTItMS4wMWgtLjA0Yy0uMy4zNi0uNjMuNjQtLjk4Ljg2LS4zNS4yMS0uNzYuMzItMS4yNC4zMi0uNzMgMC0xLjI3LS4yNC0xLjYxLS43MS0uMzMtLjQ3LS41LTEuMTQtLjUtMi4wMnptOS40NiA3LjQzdjIuMTZoLTEuNjF2LTkuNTloMS4zM2wuMTIuNzJoLjA1Yy4yOS0uMjQuNjEtLjQ1Ljk3LS42My4zNS0uMTcuNzItLjI2IDEuMS0uMjYuNDMgMCAuODEuMDggMS4xNS4yNC4zMy4xNy42MS40Ljg0LjcxLjI0LjMxLjQxLjY4LjUzIDEuMTEuMTMuNDIuMTkuOTEuMTkgMS40NCAwIC41OS0uMDkgMS4xMS0uMjUgMS41Ny0uMTYuNDctLjM4Ljg1LS42NSAxLjE2LS4yNy4zMi0uNTguNTYtLjk0LjczLS4zNS4xNi0uNzIuMjUtMS4xLjI1LS4zIDAtLjYtLjA3LS45LS4ycy0uNTktLjMxLS44Ny0uNTZ6bTAtMi4zYy4yNi4yMi41LjM3LjczLjQ1LjI0LjA5LjQ2LjEzLjY2LjEzLjQ2IDAgLjg0LS4yIDEuMTUtLjYuMzEtLjM5LjQ2LS45OC40Ni0xLjc3IDAtLjY5LS4xMi0xLjIyLS4zNS0xLjYxLS4yMy0uMzgtLjYxLS41Ny0xLjEzLS41Ny0uNDkgMC0uOTkuMjYtMS41Mi43N3ptNS44Ny0xLjY5YzAtLjU2LjA4LTEuMDYuMjUtMS41MS4xNi0uNDUuMzctLjgzLjY1LTEuMTQuMjctLjMuNTgtLjU0LjkzLS43MXMuNzEtLjI1IDEuMDgtLjI1Yy4zOSAwIC43My4wNyAxIC4yLjI3LjE0LjU0LjMyLjgxLjU1bC0uMDYtMS4xdi0yLjQ5aDEuNjF2OS44OGgtMS4zM2wtLjExLS43NGgtLjA2Yy0uMjUuMjUtLjU0LjQ2LS44OC42NC0uMzMuMTgtLjY5LjI3LTEuMDYuMjctLjg3IDAtMS41Ni0uMzItMi4wNy0uOTVzLS43Ni0xLjUxLS43Ni0yLjY1em0xLjY3LS4wMWMwIC43NC4xMyAxLjMxLjQgMS43LjI2LjM4LjY1LjU4IDEuMTUuNTguNTEgMCAuOTktLjI2IDEuNDQtLjc3di0zLjIxYy0uMjQtLjIxLS40OC0uMzYtLjctLjQ1LS4yMy0uMDgtLjQ2LS4xMi0uNy0uMTItLjQ1IDAtLjgyLjE5LTEuMTMuNTktLjMxLjM5LS40Ni45NS0uNDYgMS42OHptNi4zNSAxLjU5YzAtLjczLjMyLTEuMy45Ny0xLjcxLjY0LS40IDEuNjctLjY4IDMuMDgtLjg0IDAtLjE3LS4wMi0uMzQtLjA3LS41MS0uMDUtLjE2LS4xMi0uMy0uMjItLjQzcy0uMjItLjIyLS4zOC0uM2MtLjE1LS4wNi0uMzQtLjEtLjU4LS4xLS4zNCAwLS42OC4wNy0xIC4ycy0uNjMuMjktLjkzLjQ3bC0uNTktMS4wOGMuMzktLjI0LjgxLS40NSAxLjI4LS42My40Ny0uMTcuOTktLjI2IDEuNTQtLjI2Ljg2IDAgMS41MS4yNSAxLjkzLjc2cy42MyAxLjI1LjYzIDIuMjF2NC4wN2gtMS4zMmwtLjEyLS43NmgtLjA1Yy0uMy4yNy0uNjMuNDgtLjk4LjY2cy0uNzMuMjctMS4xNC4yN2MtLjYxIDAtMS4xLS4xOS0xLjQ4LS41Ni0uMzgtLjM2LS41Ny0uODUtLjU3LTEuNDZ6bTEuNTctLjEyYzAgLjMuMDkuNTMuMjcuNjcuMTkuMTQuNDIuMjEuNzEuMjEuMjggMCAuNTQtLjA3Ljc3LS4ycy40OC0uMzEuNzMtLjU2di0xLjU0Yy0uNDcuMDYtLjg2LjEzLTEuMTguMjMtLjMxLjA5LS41Ny4xOS0uNzYuMzFzLS4zMy4yNS0uNDEuNGMtLjA5LjE1LS4xMy4zMS0uMTMuNDh6bTYuMjktMy42M2gtLjk4di0xLjJsMS4wNi0uMDcuMi0xLjg4aDEuMzR2MS44OGgxLjc1djEuMjdoLTEuNzV2My4yOGMwIC44LjMyIDEuMi45NyAxLjIuMTIgMCAuMjQtLjAxLjM3LS4wNC4xMi0uMDMuMjQtLjA3LjM0LS4xMWwuMjggMS4xOWMtLjE5LjA2LS40LjEyLS42NC4xNy0uMjMuMDUtLjQ5LjA4LS43Ni4wOC0uNCAwLS43NC0uMDYtMS4wMi0uMTgtLjI3LS4xMy0uNDktLjMtLjY3LS41Mi0uMTctLjIxLS4zLS40OC0uMzctLjc4LS4wOC0uMy0uMTItLjY0LS4xMi0xLjAxem00LjM2IDIuMTdjMC0uNTYuMDktMS4wNi4yNy0xLjUxcy40MS0uODMuNzEtMS4xNGMuMjktLjMuNjMtLjU0IDEuMDEtLjcxLjM5LS4xNy43OC0uMjUgMS4xOC0uMjUuNDcgMCAuODguMDggMS4yMy4yNC4zNi4xNi42NS4zOC44OS42N3MuNDIuNjMuNTQgMS4wM2MuMTIuNDEuMTguODQuMTggMS4zMiAwIC4zMi0uMDIuNTctLjA3Ljc2aC00LjM3Yy4wOC42Mi4yOSAxLjEuNjUgMS40NC4zNi4zMy44Mi41IDEuMzguNS4zIDAgLjU4LS4wNC44NC0uMTMuMjUtLjA5LjUxLS4yMS43Ni0uMzdsLjU0IDEuMDFjLS4zMi4yMS0uNjkuMzktMS4wOS41M3MtLjgyLjIxLTEuMjYuMjFjLS40NyAwLS45Mi0uMDgtMS4zMy0uMjUtLjQxLS4xNi0uNzctLjQtMS4wOC0uNy0uMy0uMzEtLjU0LS42OS0uNzItMS4xMy0uMTctLjQ0LS4yNi0uOTUtLjI2LTEuNTJ6bTQuNjEtLjYyYzAtLjU1LS4xMS0uOTgtLjM0LTEuMjgtLjIzLS4zMS0uNTgtLjQ3LTEuMDYtLjQ3LS40MSAwLS43Ny4xNS0xLjA4LjQ1LS4zMS4yOS0uNS43My0uNTcgMS4zem0zLjAxIDIuMjNjLjMxLjI0LjYxLjQzLjkyLjU3LjMuMTMuNjMuMi45OC4yLjM4IDAgLjY1LS4wOC44My0uMjNzLjI3LS4zNS4yNy0uNmMwLS4xNC0uMDUtLjI2LS4xMy0uMzctLjA4LS4xLS4yLS4yLS4zNC0uMjgtLjE0LS4wOS0uMjktLjE2LS40Ny0uMjNsLS41My0uMjJjLS4yMy0uMDktLjQ2LS4xOC0uNjktLjMtLjIzLS4xMS0uNDQtLjI0LS42Mi0uNHMtLjMzLS4zNS0uNDUtLjU1Yy0uMTItLjIxLS4xOC0uNDYtLjE4LS43NSAwLS42MS4yMy0xLjEuNjgtMS40OS40NC0uMzggMS4wNi0uNTcgMS44My0uNTcuNDggMCAuOTEuMDggMS4yOS4yNXMuNzEuMzYuOTkuNTdsLS43NC45OGMtLjI0LS4xNy0uNDktLjMyLS43My0uNDItLjI1LS4xMS0uNTEtLjE2LS43OC0uMTYtLjM1IDAtLjYuMDctLjc2LjIxLS4xNy4xNS0uMjUuMzMtLjI1LjU0IDAgLjE0LjA0LjI2LjEyLjM2cy4xOC4xOC4zMS4yNmMuMTQuMDcuMjkuMTQuNDYuMjFsLjU0LjE5Yy4yMy4wOS40Ny4xOC43LjI5cy40NC4yNC42NC40Yy4xOS4xNi4zNC4zNS40Ni41OC4xMS4yMy4xNy41LjE3LjgyIDAgLjMtLjA2LjU4LS4xNy44My0uMTIuMjYtLjI5LjQ4LS41MS42OC0uMjMuMTktLjUxLjM0LS44NC40NS0uMzQuMTEtLjcyLjE3LTEuMTUuMTctLjQ4IDAtLjk1LS4wOS0xLjQxLS4yNy0uNDYtLjE5LS44Ni0uNDEtMS4yLS42OHoiIGZpbGw9IiM1MzUzNTMiLz48L2c+PC9zdmc+)

### Cite this article

Grądzki, P., Wójcik, P. & Lessmann, S. Algorithmic crypto trading using information-driven bars, triple barrier labeling and deep learning.
*Financ Innov* **11**, 136 (2025). https://doi.org/10.1186/s40854-025-00866-w

[Download citation](https://citation-needed.springer.com/v2/references/10.1186/s40854-025-00866-w?format=refman&flavour=citation)

Received: 13 November 2024

Accepted: 06 November 2025

Published: 15 December 2025

Version of record: 15 December 2025

DOI: https://doi.org/10.1186/s40854-025-00866-w

### Share this article

Anyone you share the following link with will be able to read this content:

Sorry, a shareable link is not currently available for this article.

Provided by the Springer Nature SharedIt content-sharing initiative

### Keywords

### Profiles

Advertisement

## Search

## Navigation

## Footer Navigation

### Discover content

### Publish with us

### Products and services

### Our brands

### Corporate Navigation

188.48.189.150

Not affiliated

![Springer Nature](/oscar-static/images/logo-springernature-white-0689727e50.svg)

© 2026 Springer Nature
