# An Exploration of Meta-Labeling for Trade Selection in High-Frequency Data | by Danieldaolin | Apr, 2026 | Medium

[Sitemap](https://medium.com/sitemap/sitemap.xml)

[Open in app](https://play.google.com/store/apps/details?id=com.medium.reader&referrer=utm_source%3DmobileNavBar&source=post_page---top_nav_layout_nav-----------------------------------------)

Sign up

[Sign in](https://medium.com/m/signin?operation=login&redirect=https%3A%2F%2Fmedium.com%2F%40danieldaolin%2Fan-exploration-of-meta-labeling-for-trade-selection-in-high-frequency-data-5160c028ed19&source=post_page---top_nav_layout_nav-----------------------global_nav------------------)

[](https://medium.com/?source=post_page---top_nav_layout_nav-----------------------------------------)

Get app

[Write](https://medium.com/m/signin?operation=register&redirect=https%3A%2F%2Fmedium.com%2Fnew-story&source=---top_nav_layout_nav-----------------------new_post_topnav------------------)

[Search](https://medium.com/search?source=post_page---top_nav_layout_nav-----------------------------------------)

Sign up

[Sign in](https://medium.com/m/signin?operation=login&redirect=https%3A%2F%2Fmedium.com%2F%40danieldaolin%2Fan-exploration-of-meta-labeling-for-trade-selection-in-high-frequency-data-5160c028ed19&source=post_page---top_nav_layout_nav-----------------------global_nav------------------)

![Image 1: Unknown user](https://miro.medium.com/v2/resize:fill:32:32/1*dmbNkD5D-u45r44go_cf0g.png)

# An Exploration of Meta-Labeling for Trade Selection in High-Frequency Data

[![Image 2: Danieldaolin](https://miro.medium.com/v2/resize:fill:32:32/0*E59-OzOi7TlpdNQl.jpg)](https://medium.com/@danieldaolin?source=post_page---byline--5160c028ed19---------------------------------------)

[Danieldaolin](https://medium.com/@danieldaolin?source=post_page---byline--5160c028ed19---------------------------------------)

Follow

12 min read

·

Apr 16, 2026

[](https://medium.com/m/signin?actionUrl=https%3A%2F%2Fmedium.com%2F_%2Fvote%2Fp%2F5160c028ed19&operation=register&redirect=https%3A%2F%2Fmedium.com%2F%40danieldaolin%2Fan-exploration-of-meta-labeling-for-trade-selection-in-high-frequency-data-5160c028ed19&user=Danieldaolin&userId=dd4e1eff867c&source=---header_actions--5160c028ed19---------------------clap_footer------------------)

4

[](https://medium.com/m/signin?actionUrl=https%3A%2F%2Fmedium.com%2F_%2Fbookmark%2Fp%2F5160c028ed19&operation=register&redirect=https%3A%2F%2Fmedium.com%2F%40danieldaolin%2Fan-exploration-of-meta-labeling-for-trade-selection-in-high-frequency-data-5160c028ed19&source=---header_actions--5160c028ed19---------------------bookmark_footer------------------)

[Listen](https://medium.com/m/signin?actionUrl=https%3A%2F%2Fmedium.com%2Fplans%3Fdimension%3Dpost_audio_button%26postId%3D5160c028ed19&operation=register&redirect=https%3A%2F%2Fmedium.com%2F%40danieldaolin%2Fan-exploration-of-meta-labeling-for-trade-selection-in-high-frequency-data-5160c028ed19&source=---header_actions--5160c028ed19---------------------post_audio_button------------------)

Share

Code: [https://github.com/DaDanielL/HFT-Metalabeling](https://github.com/DaDanielL/HFT-Metalabeling)

Using machine learning to predict trade signals sounds intuitive, but it often fails in practice. Financial markets are:

*   noisy (low signal-to-noise)
*   adaptive (competition erodes edge)
*   non-stationary (regime shifts)

This leads to overfitting, crowding, and **alpha decay**. Even when a model predicts direction correctly, it doesn’t necessarily result in a profitable trade.

Instead of predicting direction, this project focuses on **decision quality**.

*   A base model generates trade signals
*   A second model (meta-labeler) predicts whether a signal is **profitable**

This project will build an end-to-end pipeline for high-frequency trading signals, inspired by techniques from **_Advances in Financial Machine Learning_(Lopez de Prado).** Raw tick data is first transformed using event-based sampling (volume bars), followed by feature engineering that captures price behavior, volatility, and order flow dynamics. A primary model is then used to generate directional trade signals, which are evaluated using the triple barrier method to determine whether each trade is profitable. Finally, a meta-labeling model — implemented using a Random Forest — learns to predict the probability that a given signal will succeed, allowing the system to filter trades and improve overall decision quality.

## Data & Infrastructure

The dataset used for this project consists of ~7GB of nanosecond-resolution CME market-by-order data from 11/15/2025–1/15/2026, focusing on:

*   **Crude Oil Futures (CL)**

To handle the scale:

*   data is stored in **Amazon S3**
*   processed using **Apache Spark**
*   distributed pipeline for cleaning, aggregation, and feature engineering

## Data Pipeline

## Step 1: Volume Bar Aggregation

Raw high-frequency data arrives as irregular, noisy tick events. Modeling directly on this data is difficult because activity is uneven — some periods are extremely active, while others are quiet.

To address this, we use **volume bars**.

Instead of sampling data at fixed time intervals, we aggregate trades until a fixed **volume threshold** is reached. Each bar therefore represents a similar amount of trading activity, making the data more stable and comparable across time.

We target **~100 bars per day**, and dynamically estimate the threshold using recent history:

threshold_t = median(daily_volume_{t-5:t-1}) / 100
This means each bar contains roughly 1% of recent daily volume.

Two key design choices matter here. First, we use a **rolling median** rather than a mean, which makes the threshold robust to sudden volume spikes. Second, the threshold is computed using only **past data**, avoiding lookahead bias. If future volume were used, the model would indirectly gain information it wouldn’t have in real trading.

Overall, volume bars help:

*   normalize information flow
*   reduce noise from uneven activity
*   create more consistent modeling inputs

These bars become the foundation for all downstream features.

## Step 2: Feature Engineering

Financial markets are noisy, and price alone is not enough to explain short-term behavior. To give the model more context, we construct features that capture different aspects of market dynamics.

The feature set includes:

*   **price & momentum features** to capture short-term direction
*   **volatility & rolling statistics** to describe local market regimes
*   **volume & activity features** to measure trading intensity
*   **microstructure & order flow features** to capture supply and demand
*   **interaction and lag features** to model nonlinear effects and short-term memory

In total, ~15 features is used for the **primary signal model**, focusing on direction and immediate market conditions. The **meta-labeling model** uses the full feature set, along with the base model’s predictions, to better understand when a signal is likely to succeed.

Press enter or click to view image in full size

![Image 3](https://miro.medium.com/v2/resize:fit:700/1*tPiIEImPOH4p00vhKUfgOw.png)

## Step 3: Label Construction

Before training any model, we first define what a “correct” signal looks like. This is done through **side labeling**, which assigns a direction based on future returns.

For each bar ( t ), we compute a forward return over a fixed **10-bar horizon**:

r _{t,10} = \frac{P_ {t+10} - P _t}{P_ t}
We then assign labels based on a return threshold of **0.1%**:

*   **1** → upward move (above threshold)
*   **-1** → downward move (below threshold)
*   **0** → no significant movement

The 10-bar horizon captures short-term price movement without being overly noisy, while the threshold filters out insignificant fluctuations. Together, they provide a simple and stable baseline for directional signals.

However, this approach has clear limitations. The threshold is fixed and does not adapt to changing volatility, the 10-bar horizon may not align with the true duration of a signal, and the method ignores the price path—only comparing start and end points.

As an example, below we can see the rolling volatility throughout the dataset. There appears to be regime shifts near the middle and at the end. This is marked by the increase in rolling volatility for a noticeable period. This further suggests that methods like side labeling using fixed thresholds and return horizon may not work well, as the same parameters can behave very differently across low- and high-volatility regimes, leading to inconsistent and noisy labels.

More advanced approaches, such as volatility-scaled or adaptive thresholds, can address these issues. In this project, we keep the setup simple to establish a clear baseline.

Press enter or click to view image in full size

![Image 4](https://miro.medium.com/v2/resize:fit:700/1*tPiIEImPOH4p00vhKUfgOw.png)

Press enter or click to view image in full size

![Image 5](https://miro.medium.com/v2/resize:fit:700/1*880FdtC1FsHf8TNmBw4DjQ.png)

Side labels matches price movements.

> _With labels defined, we can now move into the_**_model pipeline_**_, where signals are generated and evaluated for profitability._

## Model Pipeline

With features and side labels in place, the next step is to generate trade signals and then evaluate whether those signals are actually worth taking.

## Step 1: Train/Test Split

The dataset is first divided into a **training set** and a completely untouched **test set**. The training set is used to build both the base model and the meta-labeler, while the test set is reserved for final evaluation. This keeps the final results closer to a real out-of-sample trading setting.

## Step 2: CPCV for Base Signal Generation

The base model is a **multi-class****logistic regression classifier** trained on a smaller subset of directional features. Its job is not to be a perfect trading model, but to act as a **signal generator**.

The goal is not to build the most accurate predictive model, but to create a consistent and unbiased stream of trade signals that can be evaluated by the meta-labeler. By using a simple linear model, we ensure that the base signals act as a lightweight event filter — capturing basic directional structure without embedding too much complexity — so that the meta-labeler can focus on learning when those signals are actually reliable.

## Get Danieldaolin’s stories in your inbox

Join Medium for free to get updates from this writer.

Subscribe

Subscribe

- [x]

Remember me for faster sign in



For each bar, the model outputs:

*   predicted side/direction label (short -1, no trade 0, long 1)
*   prediction probabilities

### **Combinatorial Purged Cross-Validation**

To train an effective meta-labeler, we need **out-of-sample predictions from the base model**. The meta-labeler’s goal is to learn when a trading signal is likely to be correct, which means its inputs (the base model’s predictions and probabilities) must reflect **realistic, unseen performance**. If we instead use in-sample predictions, the base model would appear artificially accurate, and the meta-labeler would simply learn patterns driven by overfitting rather than true signal quality.

Generating these out-of-sample predictions requires a careful validation strategy. K-fold cross-validation is not suitable for financial time series as randomly splitting temporal data causes **look-ahead bias**, where information from the future leaks into the training set. Sequential splits improve on this by preserving order, but they still fail to fully eliminate leakage when labels or features span time windows (e.g., rolling features or forward returns), causing overlap between training and validation samples.

To address these issues, we use **Combinatorial Purged Cross-Validation (CPCV)**. CPCV divides the dataset into ordered time blocks and systematically selects combinations of these blocks as validation sets. For each validation block, preceding training observations are **purged** and an **embargo** window is applied after the test block to prevent leakage. The remaining observations form a clean training set for that fold. This process ensures that every prediction is generated in a truly out-of-sample setting with no contamination from future information.

After running CPCV across all folds, we **aggregate the out-of-sample predictions** so that each observation in the dataset is assigned:

*   a predicted signal from the base model
*   a corresponding prediction probability

Importantly, these predictions are constructed entirely from models that did not see the corresponding observations during training. This produces a leakage-free dataset that accurately reflects how the base model would perform in live trading.

Finally, this dataset becomes the foundation for the meta-labeling stage. Observations with a neutral signal (side label = 0) are filtered out, allowing the meta-labeler to focus only on meaningful trade opportunities and learn to distinguish between high-quality and low-quality signals.

## Step 5: Construct Meta Labels

Once the base model produces signals, those signals must be evaluated. This is done using **triple barrier labeling**, which checks what happens after entering a trade.

A signal is labeled:

*   **1** if the profit threshold is hit first
*   **0** if the loss threshold is hit first, or if the trade times out

This turns into another classification problem: was the signal actually profitable or not?

## Step 6: Train the Meta-Labeler

The **meta-labeler** is the main model in the project. It is trained using:

*   select engineered features (~40)
*   the base model’s predicted side
*   the base model’s prediction probability
*   Output: probability that a given signal is worth taking.

A **Random Forest** is used because it captures nonlinear relationships and feature interactions that linear models cannot. As an ensemble method, it reduces overfitting by averaging across many trees, making it more robust to noisy financial data.

In addition, Random Forest provides **feature importance scores**, which are useful for both interpretation and feature selection — helping identify which signals (e.g., volatility, volume, order flow) actually drive trade success and potentially refining the model further.

Most importantly, tree-based models are highly robust to multicollinearity, which is common in financial data — especially given the large number of engineered features, many of which are highly correlated.

## Step 7: Final Test-Time Pipeline

After CPCV is complete, the base model is retrained on the full training set and used to generate signals on the held-out test set. Signals with predicted side = 0 are removed, and the trained meta-labeler is then applied to the remaining trades.

This creates two strategies for comparison:

*   **Baseline strategy:** take all base-model signals
*   **Meta-filtered strategy:** take only signals above a probability threshold (0.6)

These two approaches are then evaluated side by side. The comparison focuses on whether filtering improves **trade quality**, not just prediction accuracy. Key metrics include cumulative returns, return distribution, and precision, along with the trade-off between the number of trades and signal reliability.

## **Evaluation & Comparison**

Press enter or click to view image in full size

![Image 6](https://miro.medium.com/v2/resize:fit:700/1*c20rNykAG-qvqSZnQaP5ug.png)

Cumulative Return Comparison

The meta-filtered strategy struggled to consistently capture signals with positive returns, indicating that the meta-labeler was not effectively distinguishing high-quality trades from noise. This suggests that the model’s predictive signal is still weak, and that many profitable opportunities were either missed or not confidently identified.

However, the meta-labeler did provide some downside protection. Near the end of the period, where the base model generated poor signals, the meta-filtered strategy avoided a significant drawdown. This indicates that, even with limited precision, the model is able to identify certain unfavorable conditions and suppress low-quality trades.

Press enter or click to view image in full size

![Image 7](https://miro.medium.com/v2/resize:fit:700/1*66VNaGENz8vUOubi6blq8w.png)

Volume Over Time

Also, notice in the middle of the cumulative return plot, the meta-labeler filtered out nearly all signals. This aligns with the significant drop in trade volume shown above. In low-activity environments, features become less informative and more unstable, leading the model to assign low confidence across the board. As a result, the meta-labeler becomes overly conservative and avoids taking trades altogether.

Overall, this behavior suggests that the meta-labeler is highly sensitive to market regime and data quality. It tends to become risk-averse in uncertain or low-information environments, which can reduce losses but also limit upside. This highlights a key limitation: without stronger features or better calibration, the model may default to avoiding trades rather than selectively improving them.

Press enter or click to view image in full size

![Image 8](https://miro.medium.com/v2/resize:fit:700/1*UQSdQ6EtYg7jbRaVO_omCg.png)

Return Distributions

Moreover, the baseline return distribution being slightly skewed negative suggests that, on average, the strategy takes more losing trades than winning ones, likely due to noise and poor signal quality.

In contrast, the meta-filtered distribution being tightly centered around zero with a very slight positive skew indicates that the meta-labeler is aggressively filtering trades, removing many extreme outcomes — both losses and gains. This is also partly due to the high filter threshold required to talk a trade for the meta-filtered strategy.

The meta-labeler is acting conservatively. It successfully reduces downside risk by filtering out many losing trades However, it also removes a large portion of profitable trades, leading to muted overall returns. Overall, this suggests the model is prioritizing risk reduction over return generation, which can improve stability but may limit profitability if it becomes too restrictive.

Press enter or click to view image in full size

![Image 9](https://miro.medium.com/v2/resize:fit:700/1*SReYPj6QtRZiIY4RV8ZAbg.png)

Feature Importance

Taking advantage of Random Forest, we can se the top features driving predictions in the meta-labeling model. By analyzing these features, we can better understand which market conditions (e.g., order flow, volatility, or momentum) are most relevant for filtering high-quality trading signals.

The results show that rolling_std_20, volume, and realized_vol_10 are the most influential, indicating that the meta-labeler is relying heavily on volatility and market activity rather than pure directional signals.

This suggests that:

*   Volatility features (rolling_std_20, realized_vol_10) help the model identify when the market is unstable or noisy, which often corresponds to lower signal reliability
*   Volume acts as a proxy for market participation and liquidity, helping distinguish between high-information and low-information environments

Press enter or click to view image in full size

![Image 10](https://miro.medium.com/v2/resize:fit:700/1*2wP4vzcUzxxitPjZzTVSZA.png)

Threshold Tradeoffs

Finally, the precision vs. threshold curve highlights a clear tradeoff: as the threshold increases, precision improves while the number of trades drops sharply. We focus on precision because in trading, false positives are costly — taking a bad trade directly leads to losses — so it is more important that selected trades are high-quality rather than frequent. A higher threshold (e.g., 0.6) ensures stronger signal reliability but reduces opportunities, while a lower threshold increases trade count at the expense of noisier, less profitable signals.

Here’s a **clean, concise conclusion** that matches your tone:

## Conclusion

This project explores meta-labeling as a way to improve trading decisions by filtering signals rather than predicting them directly. While the framework is sound, its effectiveness ultimately depends on the quality of the underlying signals.

A key limitation is that the **base model does not have a strong edge** for the meta-labeler to amplify. In highly competitive markets, pure machine learning models often struggle to discover persistent alpha. Financial data is noisy, signals are quickly arbitraged away, and any detectable patterns tend to decay over time. As a result, the meta-labeler is often left filtering weak or unstable signals rather than enhancing a meaningful edge.

This suggests a more practical direction: using meta-labeling on top of **discretionary or domain-driven signals**. Instead of relying purely on ML-generated predictions, the base signals could come from trader intuition, fundamental views, well-tested strategies, or just personal trade history. The meta-labeler can then act as a layer that evaluates when those signals are most likely to succeed under current market conditions.

There are also several methodological limitations. The use of fixed thresholds and horizons in labeling may not adapt well to changing volatility regimes.

The triple barrier method also introduces limitations through its use of **fixed profit-taking, stop-loss, and maximum holding parameters**. These thresholds do not adapt to changing market conditions, particularly shifts in volatility and liquidity. A profit target that is reasonable in a low-volatility regime may be too small in a high-volatility environment, and vice versa.

Future improvements could include:

*   **volatility-scaled barriers:** Replace fixed profit-taking and stop-loss thresholds with volatility-adjusted levels to better adapt to changing market conditions
*   **stronger base signals:** Incorporate discretionary, fundamental, or strategy-driven signals to provide a real edge for the meta-labeler to amplify
*   **adaptive holding periods:** Use dynamic horizons based on market conditions instead of a fixed max holding window
*   **richer feature set:** Add macro, sentiment, or cross-asset features to better capture broader market context and improve signal evaluation

[Machine Learning](https://medium.com/tag/machine-learning?source=post_page-----5160c028ed19---------------------------------------)

[Random Forest](https://medium.com/tag/random-forest?source=post_page-----5160c028ed19---------------------------------------)

[Meta Labeling](https://medium.com/tag/meta-labeling?source=post_page-----5160c028ed19---------------------------------------)

[Ml Finance](https://medium.com/tag/finance-ml?source=post_page-----5160c028ed19---------------------------------------)

[](https://medium.com/m/signin?actionUrl=https%3A%2F%2Fmedium.com%2F_%2Fvote%2Fp%2F5160c028ed19&operation=register&redirect=https%3A%2F%2Fmedium.com%2F%40danieldaolin%2Fan-exploration-of-meta-labeling-for-trade-selection-in-high-frequency-data-5160c028ed19&user=Danieldaolin&userId=dd4e1eff867c&source=---footer_actions--5160c028ed19---------------------clap_footer------------------)

4

[](https://medium.com/m/signin?actionUrl=https%3A%2F%2Fmedium.com%2F_%2Fvote%2Fp%2F5160c028ed19&operation=register&redirect=https%3A%2F%2Fmedium.com%2F%40danieldaolin%2Fan-exploration-of-meta-labeling-for-trade-selection-in-high-frequency-data-5160c028ed19&user=Danieldaolin&userId=dd4e1eff867c&source=---footer_actions--5160c028ed19---------------------clap_footer------------------)

4

[](https://medium.com/m/signin?actionUrl=https%3A%2F%2Fmedium.com%2F_%2Fbookmark%2Fp%2F5160c028ed19&operation=register&redirect=https%3A%2F%2Fmedium.com%2F%40danieldaolin%2Fan-exploration-of-meta-labeling-for-trade-selection-in-high-frequency-data-5160c028ed19&source=---footer_actions--5160c028ed19---------------------bookmark_footer------------------)

[![Image 11: Danieldaolin](https://miro.medium.com/v2/resize:fill:48:48/0*E59-OzOi7TlpdNQl.jpg)](https://medium.com/@danieldaolin?source=post_page---post_author_info--5160c028ed19---------------------------------------)

[![Image 12: Danieldaolin](https://miro.medium.com/v2/resize:fill:64:64/0*E59-OzOi7TlpdNQl.jpg)](https://medium.com/@danieldaolin?source=post_page---post_author_info--5160c028ed19---------------------------------------)

Follow

## [Written by Danieldaolin](https://medium.com/@danieldaolin?source=post_page---post_author_info--5160c028ed19---------------------------------------)

0 followers

·[2 following](https://medium.com/@danieldaolin/following?source=post_page---post_author_info--5160c028ed19---------------------------------------)

Follow

## No responses yet

[](https://policy.medium.com/medium-rules-30e5502c4eb4?source=post_page---post_responses--5160c028ed19---------------------------------------)

![Image 13: Unknown user](https://miro.medium.com/v2/resize:fill:32:32/1*dmbNkD5D-u45r44go_cf0g.png)

Write a response

[What are your thoughts?](https://medium.com/m/signin?operation=register&redirect=https%3A%2F%2Fmedium.com%2F%40danieldaolin%2Fan-exploration-of-meta-labeling-for-trade-selection-in-high-frequency-data-5160c028ed19&source=---post_responses--5160c028ed19---------------------respond_sidebar------------------)

Cancel

Respond

## Recommended from Medium

![Image 14: Software Engineer (named Vasilios Syrakis) at Atlassian was laid off on March 12 after 8 years.](https://miro.medium.com/v2/resize:fit:679/format:webp/0*sqdK4ZeCBWyreVGC)

[![Image 15: Techx_official](https://miro.medium.com/v2/resize:fill:20:20/1*6LbwfqS-HKP99Ip23ohyoQ.png)](https://medium.com/techx-official?source=post_page---read_next_recirc--5160c028ed19----0---------------------9875e335_8667_4c4c_b44d_6195bd88142b--------------)

In

[Techx_official](https://medium.com/techx-official?source=post_page---read_next_recirc--5160c028ed19----0---------------------9875e335_8667_4c4c_b44d_6195bd88142b--------------)

by

[Ship X/ TechX](https://medium.com/@shipx?source=post_page---read_next_recirc--5160c028ed19----0---------------------9875e335_8667_4c4c_b44d_6195bd88142b--------------)

·

5d ago

## [Software Engineer (named Vasilios Syrakis) at Atlassian was laid off on March 12 after 8 years. ### Vasilios responded with a 40-minute YouTube video showing how the company’s entire tech works, free for anyone to copy.](https://medium.com/techx-official/software-engineer-named-vasilios-syrakis-at-atlassian-was-laid-off-on-march-12-after-8-years-04147075ad6d?source=post_page---read_next_recirc--5160c028ed19----0---------------------9875e335_8667_4c4c_b44d_6195bd88142b--------------)

[47](https://medium.com/techx-official/software-engineer-named-vasilios-syrakis-at-atlassian-was-laid-off-on-march-12-after-8-years-04147075ad6d?source=post_page---read_next_recirc--5160c028ed19----0---------------------9875e335_8667_4c4c_b44d_6195bd88142b--------------)

[](https://medium.com/m/signin?operation=register&redirect=https%3A%2F%2Fmedium.com%2F%40danieldaolin%2Fan-exploration-of-meta-labeling-for-trade-selection-in-high-frequency-data-5160c028ed19&source=---read_next_recirc--5160c028ed19----0-----------------explicit_signal----9875e335_8667_4c4c_b44d_6195bd88142b--------------)

[](https://medium.com/m/signin?actionUrl=https%3A%2F%2Fmedium.com%2F_%2Fbookmark%2Fp%2F04147075ad6d&operation=register&redirect=https%3A%2F%2Fmedium.com%2Ftechx-official%2Fsoftware-engineer-named-vasilios-syrakis-at-atlassian-was-laid-off-on-march-12-after-8-years-04147075ad6d&source=---read_next_recirc--5160c028ed19----0-----------------bookmark_preview----9875e335_8667_4c4c_b44d_6195bd88142b--------------)

![Image 16: Understanding XGBoost: A Deep Dive into the Algorithm](https://miro.medium.com/v2/resize:fit:679/format:webp/1*qAAAbZBPcqINya7HhZbCiA.png)

[![Image 17: Towards AI](https://miro.medium.com/v2/resize:fill:20:20/1*JyIThO-cLjlChQLb6kSlVQ.png)](https://medium.com/towards-artificial-intelligence?source=post_page---read_next_recirc--5160c028ed19----1---------------------9875e335_8667_4c4c_b44d_6195bd88142b--------------)

In

[Towards AI](https://medium.com/towards-artificial-intelligence?source=post_page---read_next_recirc--5160c028ed19----1---------------------9875e335_8667_4c4c_b44d_6195bd88142b--------------)

by

[Utkarsh Mittal](https://medium.com/@mittalutkarsh?source=post_page---read_next_recirc--5160c028ed19----1---------------------9875e335_8667_4c4c_b44d_6195bd88142b--------------)

·

Dec 9, 2025

## [Understanding XGBoost: A Deep Dive into the Algorithm ### Introduction](https://medium.com/towards-artificial-intelligence/understanding-xgboost-a-deep-dive-into-the-algorithm-94e8a28957ee?source=post_page---read_next_recirc--5160c028ed19----1---------------------9875e335_8667_4c4c_b44d_6195bd88142b--------------)

[](https://medium.com/towards-artificial-intelligence/understanding-xgboost-a-deep-dive-into-the-algorithm-94e8a28957ee?source=post_page---read_next_recirc--5160c028ed19----1---------------------9875e335_8667_4c4c_b44d_6195bd88142b--------------)

[](https://medium.com/m/signin?operation=register&redirect=https%3A%2F%2Fmedium.com%2F%40danieldaolin%2Fan-exploration-of-meta-labeling-for-trade-selection-in-high-frequency-data-5160c028ed19&source=---read_next_recirc--5160c028ed19----1-----------------explicit_signal----9875e335_8667_4c4c_b44d_6195bd88142b--------------)

[](https://medium.com/m/signin?actionUrl=https%3A%2F%2Fmedium.com%2F_%2Fbookmark%2Fp%2F94e8a28957ee&operation=register&redirect=https%3A%2F%2Fpub.towardsai.net%2Funderstanding-xgboost-a-deep-dive-into-the-algorithm-94e8a28957ee&source=---read_next_recirc--5160c028ed19----1-----------------bookmark_preview----9875e335_8667_4c4c_b44d_6195bd88142b--------------)

![Image 18: A high-contrast digital graphic with a dark, ethereal blue and purple background. Large, glowing cyan text in the center reads “USING LLMs IS A SKILL.” Below the text are three minimalist neon icons: a stack of books with a quill, a castle tower, and a human brain merged with mechanical gears. Small text at the bottom reads “Based on ‘Learning the Art’ concept.”](https://miro.medium.com/v2/resize:fit:679/format:webp/1*BYQlT0GI6CTqJwwk1bXQkg.png)

[![Image 19: Leo Godin](https://miro.medium.com/v2/resize:fill:20:20/0*kkwZ8D_UzFGPeDg_.png)](https://medium.com/@leo-godin?source=post_page---read_next_recirc--5160c028ed19----0---------------------9875e335_8667_4c4c_b44d_6195bd88142b--------------)

[Leo Godin](https://medium.com/@leo-godin?source=post_page---read_next_recirc--5160c028ed19----0---------------------9875e335_8667_4c4c_b44d_6195bd88142b--------------)

·

Mar 2

## [Claude Code is Great ### You Just Need to Learn How to Use It](https://medium.com/@leo-godin/claude-code-is-great-6db35d8685f0?source=post_page---read_next_recirc--5160c028ed19----0---------------------9875e335_8667_4c4c_b44d_6195bd88142b--------------)

[125](https://medium.com/@leo-godin/claude-code-is-great-6db35d8685f0?source=post_page---read_next_recirc--5160c028ed19----0---------------------9875e335_8667_4c4c_b44d_6195bd88142b--------------)

[](https://medium.com/m/signin?operation=register&redirect=https%3A%2F%2Fmedium.com%2F%40danieldaolin%2Fan-exploration-of-meta-labeling-for-trade-selection-in-high-frequency-data-5160c028ed19&source=---read_next_recirc--5160c028ed19----0-----------------explicit_signal----9875e335_8667_4c4c_b44d_6195bd88142b--------------)

[](https://medium.com/m/signin?actionUrl=https%3A%2F%2Fmedium.com%2F_%2Fbookmark%2Fp%2F6db35d8685f0&operation=register&redirect=https%3A%2F%2Fleo-godin.medium.com%2Fclaude-code-is-great-6db35d8685f0&source=---read_next_recirc--5160c028ed19----0-----------------bookmark_preview----9875e335_8667_4c4c_b44d_6195bd88142b--------------)

![Image 20: MCP is Dead](https://miro.medium.com/v2/resize:fit:679/format:webp/1*Oj5PiyfEi8DadSC8Jy374w.png)

[![Image 21: UX Planet](https://miro.medium.com/v2/resize:fill:20:20/1*A0FnBy5FBoVQC02SZXLXPg.png)](https://medium.com/ux-planet?source=post_page---read_next_recirc--5160c028ed19----1---------------------9875e335_8667_4c4c_b44d_6195bd88142b--------------)

In

[UX Planet](https://medium.com/ux-planet?source=post_page---read_next_recirc--5160c028ed19----1---------------------9875e335_8667_4c4c_b44d_6195bd88142b--------------)

by

[Nick Babich](https://medium.com/@101?source=post_page---read_next_recirc--5160c028ed19----1---------------------9875e335_8667_4c4c_b44d_6195bd88142b--------------)

·

Apr 6

## [MCP is Dead ### Why you should avoid using MCP in Claude Code and what to use instead](https://medium.com/ux-planet/mcp-is-dead-cf16b667ba6d?source=post_page---read_next_recirc--5160c028ed19----1---------------------9875e335_8667_4c4c_b44d_6195bd88142b--------------)

[161](https://medium.com/ux-planet/mcp-is-dead-cf16b667ba6d?source=post_page---read_next_recirc--5160c028ed19----1---------------------9875e335_8667_4c4c_b44d_6195bd88142b--------------)

[](https://medium.com/m/signin?operation=register&redirect=https%3A%2F%2Fmedium.com%2F%40danieldaolin%2Fan-exploration-of-meta-labeling-for-trade-selection-in-high-frequency-data-5160c028ed19&source=---read_next_recirc--5160c028ed19----1-----------------explicit_signal----9875e335_8667_4c4c_b44d_6195bd88142b--------------)

[](https://medium.com/m/signin?actionUrl=https%3A%2F%2Fmedium.com%2F_%2Fbookmark%2Fp%2Fcf16b667ba6d&operation=register&redirect=https%3A%2F%2Fuxplanet.org%2Fmcp-is-dead-cf16b667ba6d&source=---read_next_recirc--5160c028ed19----1-----------------bookmark_preview----9875e335_8667_4c4c_b44d_6195bd88142b--------------)

![Image 22: Anthropic’s Engineer Said Kill Markdown. Here’s What He Actually Meant.](https://miro.medium.com/v2/resize:fit:679/format:webp/0*ITstR02aTfQsF2bV)

[![Image 23: Generative AI](https://miro.medium.com/v2/resize:fill:20:20/1*M4RBhIRaSSZB7lXfrGlatA.png)](https://medium.com/generative-ai?source=post_page---read_next_recirc--5160c028ed19----2---------------------9875e335_8667_4c4c_b44d_6195bd88142b--------------)

In

[Generative AI](https://medium.com/generative-ai?source=post_page---read_next_recirc--5160c028ed19----2---------------------9875e335_8667_4c4c_b44d_6195bd88142b--------------)

by

[Yanli Liu](https://medium.com/@yanli.liu?source=post_page---read_next_recirc--5160c028ed19----2---------------------9875e335_8667_4c4c_b44d_6195bd88142b--------------)

·

6d ago

## [Anthropic’s Engineer Said Kill Markdown. Here’s What He Actually Meant. ### HTML vs Markdown ： Here’s the Decision Tree Both Sides Needed.](https://medium.com/generative-ai/anthropics-engineer-said-kill-markdown-here-s-what-he-actually-meant-36bee00c0ca2?source=post_page---read_next_recirc--5160c028ed19----2---------------------9875e335_8667_4c4c_b44d_6195bd88142b--------------)

[75](https://medium.com/generative-ai/anthropics-engineer-said-kill-markdown-here-s-what-he-actually-meant-36bee00c0ca2?source=post_page---read_next_recirc--5160c028ed19----2---------------------9875e335_8667_4c4c_b44d_6195bd88142b--------------)

[](https://medium.com/m/signin?operation=register&redirect=https%3A%2F%2Fmedium.com%2F%40danieldaolin%2Fan-exploration-of-meta-labeling-for-trade-selection-in-high-frequency-data-5160c028ed19&source=---read_next_recirc--5160c028ed19----2-----------------explicit_signal----9875e335_8667_4c4c_b44d_6195bd88142b--------------)

[](https://medium.com/m/signin?actionUrl=https%3A%2F%2Fmedium.com%2F_%2Fbookmark%2Fp%2F36bee00c0ca2&operation=register&redirect=https%3A%2F%2Fgenerativeai.pub%2Fanthropics-engineer-said-kill-markdown-here-s-what-he-actually-meant-36bee00c0ca2&source=---read_next_recirc--5160c028ed19----2-----------------bookmark_preview----9875e335_8667_4c4c_b44d_6195bd88142b--------------)

![Image 24: AI Agents: Complete Course](https://miro.medium.com/v2/resize:fit:679/format:webp/1*PvPPSGJ9779FTWmtK_Yeyw.png)

[![Image 25: Data Science Collective](https://miro.medium.com/v2/resize:fill:20:20/1*0nV0Q-FBHj94Kggq00pG2Q.jpeg)](https://medium.com/data-science-collective?source=post_page---read_next_recirc--5160c028ed19----3---------------------9875e335_8667_4c4c_b44d_6195bd88142b--------------)

In

[Data Science Collective](https://medium.com/data-science-collective?source=post_page---read_next_recirc--5160c028ed19----3---------------------9875e335_8667_4c4c_b44d_6195bd88142b--------------)

by

[Marina Wyss](https://medium.com/@gratitudedriven?source=post_page---read_next_recirc--5160c028ed19----3---------------------9875e335_8667_4c4c_b44d_6195bd88142b--------------)

·

Dec 6, 2025

## [AI Agents: Complete Course ### From beginner to intermediate to production.](https://medium.com/data-science-collective/ai-agents-complete-course-f226aa4550a1?source=post_page---read_next_recirc--5160c028ed19----3---------------------9875e335_8667_4c4c_b44d_6195bd88142b--------------)

[278](https://medium.com/data-science-collective/ai-agents-complete-course-f226aa4550a1?source=post_page---read_next_recirc--5160c028ed19----3---------------------9875e335_8667_4c4c_b44d_6195bd88142b--------------)

[](https://medium.com/m/signin?operation=register&redirect=https%3A%2F%2Fmedium.com%2F%40danieldaolin%2Fan-exploration-of-meta-labeling-for-trade-selection-in-high-frequency-data-5160c028ed19&source=---read_next_recirc--5160c028ed19----3-----------------explicit_signal----9875e335_8667_4c4c_b44d_6195bd88142b--------------)

[](https://medium.com/m/signin?actionUrl=https%3A%2F%2Fmedium.com%2F_%2Fbookmark%2Fp%2Ff226aa4550a1&operation=register&redirect=https%3A%2F%2Fmedium.com%2Fdata-science-collective%2Fai-agents-complete-course-f226aa4550a1&source=---read_next_recirc--5160c028ed19----3-----------------bookmark_preview----9875e335_8667_4c4c_b44d_6195bd88142b--------------)

[See more recommendations](https://medium.com/?source=post_page---read_next_recirc--5160c028ed19---------------------------------------)

[Help](https://help.medium.com/hc/en-us?source=post_page-----5160c028ed19---------------------------------------)

[Status](https://status.medium.com/?source=post_page-----5160c028ed19---------------------------------------)

[About](https://medium.com/about?autoplay=1&source=post_page-----5160c028ed19---------------------------------------)

[Careers](https://medium.com/jobs-at-medium/work-at-medium-959d1a85284e?source=post_page-----5160c028ed19---------------------------------------)

[Press](mailto:pressinquiries@medium.com)

[Blog](https://blog.medium.com/?source=post_page-----5160c028ed19---------------------------------------)

[Privacy](https://policy.medium.com/medium-privacy-policy-f03bf92035c9?source=post_page-----5160c028ed19---------------------------------------)

[Rules](https://policy.medium.com/medium-rules-30e5502c4eb4?source=post_page-----5160c028ed19---------------------------------------)

[Terms](https://policy.medium.com/medium-terms-of-service-9db0094a1e0f?source=post_page-----5160c028ed19---------------------------------------)

[Text to speech](https://speechify.com/medium?source=post_page-----5160c028ed19---------------------------------------)
